from __future__ import annotations

import builtins
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from realized_core_llm import (
    ChatCompletionResponseError,
    ChatContentPolicy,
    ChatProviderDependencyError,
    ChatRequestFallback,
    ChatRetryPolicy,
    OpenAICompatibleChatTransport,
    build_openai_compatible_client,
    discover_openai_compatible_model_id,
    ensure_openai_v1_base_url,
    normalize_openai_compatible_base_url,
    parse_chat_completion_response,
)


class _Completions:
    def __init__(self, *outcomes: object) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        if not self.outcomes:
            raise AssertionError("Unexpected provider call")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _response(
    text: object = "ok",
    *,
    tool_calls: object = None,
    response_id: str = "response-1",
) -> object:
    return SimpleNamespace(
        id=response_id,
        model="returned-model",
        system_fingerprint="fingerprint",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=text,
                    tool_calls=tool_calls,
                )
            )
        ],
    )


def _client(*outcomes: object) -> tuple[object, _Completions]:
    completions = _Completions(*outcomes)
    return (
        SimpleNamespace(chat=SimpleNamespace(completions=completions)),
        completions,
    )


class OpenAICompatibleChatTransportTests(unittest.TestCase):
    def test_constructs_sdk_client_without_sdk_retries(self) -> None:
        expected = object()
        with patch("openai.OpenAI", return_value=expected) as constructor:
            actual = build_openai_compatible_client(
                api_key="secret",
                timeout_seconds=2.5,
                base_url="http://localhost:8080/v1",
            )

        self.assertIs(expected, actual)
        constructor.assert_called_once_with(
            api_key="secret",
            timeout=2.5,
            max_retries=0,
            base_url="http://localhost:8080/v1",
        )

    def test_missing_sdk_has_typed_dependency_error(self) -> None:
        real_import = builtins.__import__

        def import_without_openai(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("missing openai")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_without_openai):
            with self.assertRaises(ChatProviderDependencyError):
                build_openai_compatible_client(
                    api_key="secret",
                    timeout_seconds=2.5,
                )

    def test_compatibility_fallback_does_not_mutate_callers_request(self) -> None:
        client, completions = _client(
            TypeError("max_tokens unsupported; use max_completion_tokens"),
            _response(),
        )
        request = {"model": "m", "max_tokens": 12}

        result = OpenAICompatibleChatTransport(
            client,
            fallbacks=(
                ChatRequestFallback(
                    "max_tokens",
                    required_error_markers=(
                        "max_tokens",
                        "max_completion_tokens",
                    ),
                    replacement_parameter="max_completion_tokens",
                ),
            ),
        ).complete(request)

        self.assertEqual("ok", result.text)
        self.assertEqual({"model": "m", "max_tokens": 12}, request)
        self.assertIn("max_tokens", completions.calls[0])
        self.assertEqual(12, completions.calls[1]["max_completion_tokens"])

    def test_unrelated_error_cannot_trigger_parameter_fallback(self) -> None:
        client, completions = _client(RuntimeError("provider unavailable"))
        subject = OpenAICompatibleChatTransport(
            client,
            fallbacks=(
                ChatRequestFallback(
                    "temperature",
                    required_error_markers=("temperature",),
                    any_error_markers=("unsupported",),
                ),
            ),
        )

        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            subject.complete({"model": "m", "temperature": 0.0})
        self.assertEqual(1, len(completions.calls))

    def test_retry_budget_and_delays_are_explicit(self) -> None:
        client, completions = _client(
            RuntimeError("timed out"),
            RuntimeError("timed out"),
            _response(),
        )
        delays: list[float] = []

        result = OpenAICompatibleChatTransport(
            client,
            retry_policy=ChatRetryPolicy(
                max_transient_retries=2,
                retry_delays_seconds=(1.0, 2.0),
                retry_error_markers=("timed out",),
            ),
            sleep=delays.append,
        ).complete({"model": "m"})

        self.assertEqual("ok", result.text)
        self.assertEqual(3, len(completions.calls))
        self.assertEqual([1.0, 2.0], delays)

    def test_retry_status_can_come_from_provider_response(self) -> None:
        transient = RuntimeError("provider request failed")
        transient.response = SimpleNamespace(status_code=503)
        client, completions = _client(transient, _response())

        result = OpenAICompatibleChatTransport(
            client,
            retry_policy=ChatRetryPolicy(
                max_transient_retries=1,
                retry_server_errors=True,
            ),
            sleep=lambda _delay: None,
        ).complete({"model": "m"})

        self.assertEqual("ok", result.text)
        self.assertEqual(2, len(completions.calls))

    def test_provider_attempt_budget_includes_compatibility_fallbacks(self) -> None:
        client, completions = _client(
            RuntimeError("temperature unsupported"),
            RuntimeError("timed out"),
            RuntimeError("timed out"),
        )
        subject = OpenAICompatibleChatTransport(
            client,
            fallbacks=(
                ChatRequestFallback(
                    "temperature",
                    required_error_markers=("temperature",),
                    any_error_markers=("unsupported",),
                ),
            ),
            retry_policy=ChatRetryPolicy(
                max_transient_retries=2,
                max_provider_attempts=3,
                retry_error_markers=("timed out",),
            ),
            sleep=lambda _delay: None,
        )

        with self.assertRaisesRegex(RuntimeError, "timed out"):
            subject.complete({"model": "m", "temperature": 0.0})
        self.assertEqual(3, len(completions.calls))

    def test_repeated_request_is_never_served_from_transport_state(self) -> None:
        client, completions = _client(
            _response("first", response_id="1"),
            _response("second", response_id="2"),
        )
        subject = OpenAICompatibleChatTransport(client)

        self.assertEqual("first", subject.complete({"model": "m"}).text)
        self.assertEqual("second", subject.complete({"model": "m"}).text)
        self.assertEqual(2, len(completions.calls))

    def test_response_normalizes_text_tools_and_provider_metadata(self) -> None:
        tool_call = SimpleNamespace(
            id="call-1",
            type="function",
            function=SimpleNamespace(
                name="ws__fs__read",
                arguments='{"path":"README.md"}',
            ),
        )
        client, _ = _client(_response("  done  ", tool_calls=[tool_call]))

        result = OpenAICompatibleChatTransport(client).complete({"model": "m"})

        self.assertEqual("done", result.text)
        self.assertEqual("returned-model", result.model)
        self.assertEqual("response-1", result.response_id)
        self.assertEqual("fingerprint", result.system_fingerprint)
        self.assertEqual("ws__fs__read", result.tool_calls[0].name)
        self.assertEqual("call-1", result.tool_calls[0].to_dict()["id"])

    def test_content_policy_preserves_each_callers_existing_semantics(self) -> None:
        message = {
            "content": [
                {"type": "image", "text": "ignored-by-strict-policy"},
                {"type": "text", "text": "included"},
                SimpleNamespace(text="object text"),
            ]
        }
        strict = parse_chat_completion_response(
            {"choices": [{"message": message}]},
            content_policy=ChatContentPolicy(
                mapping_requires_text_type=True,
                include_object_text=False,
            ),
        )
        permissive = parse_chat_completion_response(
            {"choices": [{"message": message}]},
            content_policy=ChatContentPolicy(
                mapping_requires_text_type=False,
                include_object_text=True,
            ),
        )

        self.assertEqual("included", strict.text)
        self.assertEqual(
            "ignored-by-strict-policy\nincluded\nobject text",
            permissive.text,
        )

    def test_invalid_response_is_not_retried(self) -> None:
        client, completions = _client(SimpleNamespace(choices=[]), _response())
        subject = OpenAICompatibleChatTransport(
            client,
            retry_policy=ChatRetryPolicy(
                max_transient_retries=1,
                retry_error_markers=("provider",),
            ),
        )

        with self.assertRaises(ChatCompletionResponseError):
            subject.complete({"model": "m"})
        self.assertEqual(1, len(completions.calls))

    def test_malformed_tool_call_is_rejected_before_application_use(self) -> None:
        with self.assertRaises(ChatCompletionResponseError):
            parse_chat_completion_response(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "",
                                "tool_calls": [{"id": "call-1"}],
                            }
                        }
                    ]
                }
            )

    def test_base_url_normalization_is_provider_neutral(self) -> None:
        self.assertEqual(
            "http://localhost:8080/v1",
            normalize_openai_compatible_base_url(
                "http://localhost:8080/v1/chat/completions"
            ),
        )
        self.assertEqual(
            "http://localhost:8080/v1",
            ensure_openai_v1_base_url("http://localhost:8080"),
        )
        self.assertIsNone(normalize_openai_compatible_base_url(None))

    def test_model_discovery_supports_both_compatible_shapes(self) -> None:
        class _Response:
            def __init__(self, payload: object) -> None:
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self) -> bytes:
                return json.dumps(self.payload).encode()

        self.assertEqual(
            "model-a",
            discover_openai_compatible_model_id(
                "http://localhost/v1",
                open_url=lambda *_args, **_kwargs: _Response(
                    {"data": [{"id": "model-a"}]}
                ),
            ),
        )
        self.assertEqual(
            "model-b",
            discover_openai_compatible_model_id(
                "http://localhost/v1",
                open_url=lambda *_args, **_kwargs: _Response(
                    {"models": [{"name": "model-b"}]}
                ),
            ),
        )

    def test_model_discovery_failure_is_non_authoritative(self) -> None:
        self.assertIsNone(
            discover_openai_compatible_model_id(
                "http://localhost/v1",
                open_url=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    OSError("offline")
                ),
            )
        )


if __name__ == "__main__":
    unittest.main()
