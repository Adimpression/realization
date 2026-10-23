from __future__ import annotations

from dataclasses import dataclass
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from realized_core_llm import (
    ConversationOperation,
    ConversationPlanningContext,
    ConversationProviderConfigurationError,
    ConversationProviderResponseError,
    ConversationRenderContext,
    OpenAICompatibleJsonProvider,
    build_environment_conversation_advisors,
)


@dataclass
class _QueuedOutcome:
    content: str = ""
    error: Exception | None = None


class _FakeCompletions:
    def __init__(self, *outcomes: _QueuedOutcome) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(dict(kwargs))
        if not self.outcomes:
            raise AssertionError("Unexpected provider call")
        outcome = self.outcomes.pop(0)
        if outcome.error is not None:
            raise outcome.error
        return SimpleNamespace(
            id=f"response-{len(self.calls)}",
            model="returned-model",
            system_fingerprint="fingerprint-1",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=outcome.content)
                )
            ],
        )


def _client(*outcomes: _QueuedOutcome):
    completions = _FakeCompletions(*outcomes)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    ), completions


def _schema() -> dict[str, object]:
    return {
        "title": "TestPlanningResult",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "operation": {"type": "string", "enum": ["start"]},
        },
        "required": ["operation"],
    }


class OpenAICompatibleJsonProviderTests(unittest.TestCase):
    def test_returns_strict_json_with_a_provenance_receipt(self) -> None:
        client, completions = _client(
            _QueuedOutcome(content='{"operation":"start"}')
        )
        provider = OpenAICompatibleJsonProvider(
            client=client,
            provider="openai",
            model="test-model",
        )

        first = provider("Interpret this.", _schema())
        second_client, _ = _client(
            _QueuedOutcome(content='{"operation":"start"}')
        )
        second = OpenAICompatibleJsonProvider(
            client=second_client,
            provider="openai",
            model="test-model",
        )("Interpret this.", _schema())

        self.assertEqual({"operation": "start"}, first.payload)
        self.assertEqual("llm", first.receipt["source"])
        self.assertEqual("openai", first.receipt["provider"])
        self.assertEqual("returned-model", first.receipt["model"])
        self.assertEqual("response-1", first.receipt["response_id"])
        self.assertEqual(
            first.receipt["request_digest"],
            second.receipt["request_digest"],
        )
        self.assertEqual(
            first.receipt["response_digest"],
            second.receipt["response_digest"],
        )
        self.assertGreaterEqual(first.receipt["elapsed_seconds"], 0.0)
        call = completions.calls[0]
        self.assertEqual("test-model", call["model"])
        self.assertEqual("json_schema", call["response_format"]["type"])
        self.assertEqual(
            "TestPlanningResult",
            call["response_format"]["json_schema"]["name"],
        )
        self.assertTrue(call["response_format"]["json_schema"]["strict"])
        self.assertEqual("minimal", call["reasoning_effort"])
        messages = call["messages"]
        assert isinstance(messages, list)
        developer_message = messages[0]["content"]
        self.assertIn(
            "validation and semantic contract",
            developer_message,
        )
        self.assertIn(
            "Populate every required field from the task",
            developer_message,
        )
        self.assertIn("genuinely inapplicable", developer_message)
        self.assertIn(
            "Application-owned instructions and bounded context:\nInterpret this.",
            developer_message,
        )
        user_message = messages[1]["content"]
        self.assertIn("Required output JSON Schema:", user_message)
        self.assertNotIn("Interpret this.", user_message)
        self.assertIn("return a populated instance", user_message)

    def test_rejects_malformed_or_non_object_json_without_guessing(self) -> None:
        for raw in (
            "not json",
            '{"schema_version":"1","operation":',
            json.dumps(["not", "an", "object"]),
        ):
            with self.subTest(raw=raw):
                client, _ = _client(_QueuedOutcome(content=raw))
                provider = OpenAICompatibleJsonProvider(
                    client=client,
                    provider="openai",
                    model="test-model",
                )
                with self.assertRaises(ConversationProviderResponseError):
                    provider("Interpret this.", _schema())

    def test_retries_only_explicitly_unsupported_compatibility_parameters(self) -> None:
        client, completions = _client(
            _QueuedOutcome(
                error=TypeError(
                    "max_tokens is unsupported; use max_completion_tokens"
                )
            ),
            _QueuedOutcome(
                error=TypeError("temperature is not supported")
            ),
            _QueuedOutcome(content='{"operation":"start"}'),
        )
        provider = OpenAICompatibleJsonProvider(
            client=client,
            provider="openai",
            model="test-model",
        )

        result = provider("Interpret this.", _schema())

        self.assertEqual("start", result.payload["operation"])
        self.assertIn("max_tokens", completions.calls[0])
        self.assertNotIn("max_tokens", completions.calls[1])
        self.assertIn("max_completion_tokens", completions.calls[1])
        self.assertIn("temperature", completions.calls[1])
        self.assertNotIn("temperature", completions.calls[2])

    def test_does_not_reclassify_an_ordinary_provider_failure(self) -> None:
        client, completions = _client(
            _QueuedOutcome(error=RuntimeError("provider unavailable"))
        )
        provider = OpenAICompatibleJsonProvider(
            client=client,
            provider="openai",
            model="test-model",
        )

        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            provider("Interpret this.", _schema())
        self.assertEqual(1, len(completions.calls))

    def test_invalid_json_schema_is_not_silently_disabled(self) -> None:
        client, completions = _client(
            _QueuedOutcome(
                error=ValueError("response_format has an invalid schema")
            )
        )
        provider = OpenAICompatibleJsonProvider(
            client=client,
            provider="openai",
            model="test-model",
        )

        with self.assertRaisesRegex(ValueError, "invalid schema"):
            provider("Interpret this.", _schema())
        self.assertEqual(1, len(completions.calls))

    def test_unsupported_structured_output_can_fall_back_to_plain_json(self) -> None:
        client, completions = _client(
            _QueuedOutcome(
                error=TypeError("response_format is unsupported")
            ),
            _QueuedOutcome(content='{"operation":"start"}'),
        )
        provider = OpenAICompatibleJsonProvider(
            client=client,
            provider="llamacpp",
            model="test-model",
        )

        result = provider("Interpret this.", _schema())

        self.assertEqual("start", result.payload["operation"])
        self.assertIn("response_format", completions.calls[0])
        self.assertNotIn("response_format", completions.calls[1])


class EnvironmentAdvisorCompositionTests(unittest.TestCase):
    def test_injected_client_builds_both_product_advisors(self) -> None:
        client, completions = _client(
            _QueuedOutcome(
                content=json.dumps(
                    {
                        "schema_version": "1",
                        "operation": "start",
                        "objective": "Choose a colour.",
                        "required_outcome": "A colour is chosen.",
                    }
                )
            ),
            _QueuedOutcome(content='{"answer":"Blue is selected."}'),
        )

        planner, renderer = build_environment_conversation_advisors(
            provider="openai",
            model="test-model",
            client=client,
            reasoning_effort="low",
        )
        planned = planner.propose(
            ConversationPlanningContext(
                prompt="Choose blue.",
                scope_id="scope-1",
            )
        )
        rendered = renderer.render(
            ConversationRenderContext(
                prompt="What did we choose?",
                operation=ConversationOperation.START,
                current_state={},
                path=(),
                structured_result={},
                default_text="fallback",
            )
        )

        self.assertEqual(ConversationOperation.START, planned.proposal.operation)
        self.assertEqual("Blue is selected.", rendered.text)
        self.assertEqual("openai", planned.receipt["provider"])
        self.assertEqual("openai", rendered.receipt["provider"])
        self.assertEqual(2, len(completions.calls))
        self.assertEqual(
            ["low", "low"],
            [call["reasoning_effort"] for call in completions.calls],
        )

    def test_configuration_requires_supported_provider_and_model(self) -> None:
        client, _ = _client()
        with self.assertRaisesRegex(
            ConversationProviderConfigurationError,
            "Unsupported LLM_PROVIDER",
        ):
            build_environment_conversation_advisors(
                provider="unknown",
                model="test-model",
                client=client,
            )

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(
                ConversationProviderConfigurationError,
                "No conversation model",
            ):
                build_environment_conversation_advisors(client=client)


if __name__ == "__main__":
    unittest.main()
