from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from realized_core_engine.supplement import ask_llm


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        if "reasoning_effort" in kwargs:
            raise RuntimeError(
                "Unrecognized request argument supplied: reasoning_effort"
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))],
            model="fast-model",
            id="response-1",
            system_fingerprint=None,
        )


class _FailingCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        raise RuntimeError("request with reasoning_effort timed out")


class _AllFallbackCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(dict(kwargs))
        call_number = len(self.calls)
        errors = {
            1: RuntimeError(
                "max_tokens is unsupported; use max_completion_tokens"
            ),
            2: RuntimeError("reasoning_effort is unsupported"),
            3: RuntimeError("temperature supports only the default (1)"),
            4: RuntimeError("response_format is invalid"),
            5: RuntimeError("seed is invalid"),
        }
        if call_number in errors:
            raise errors[call_number]
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=[
                            {"type": "image", "text": "ignored"},
                            {"type": "text", "text": '{"ok": true}'},
                        ]
                    )
                )
            ],
            model="compatible-model",
            id="response-compatible",
            system_fingerprint="fingerprint-compatible",
        )


class SupplementProviderCompatibilityTests(unittest.TestCase):
    def test_unrecognized_reasoning_effort_is_retried_without_parameter(self) -> None:
        completions = _FakeCompletions()
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions),
        )
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "openai",
                    "OPENAI_MODEL": "fast-model",
                },
                clear=False,
            ),
            patch(
                "realized_core_engine.supplement.build_openai_compatible_llm_client",
                return_value=client,
            ),
        ):
            answer = ask_llm(
                "Return JSON.",
                model="fast-model",
                reasoning_effort="medium",
                response_format={"type": "json_object"},
            )

        self.assertEqual('{"ok": true}', answer)
        self.assertEqual(2, len(completions.calls))
        self.assertEqual("medium", completions.calls[0]["reasoning_effort"])
        self.assertNotIn("reasoning_effort", completions.calls[1])

    def test_unrelated_provider_failure_does_not_strip_reasoning_effort(self) -> None:
        completions = _FailingCompletions()
        client = SimpleNamespace(
            chat=SimpleNamespace(completions=completions),
        )
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "openai",
                    "OPENAI_MODEL": "fast-model",
                },
                clear=False,
            ),
            patch(
                "realized_core_engine.supplement.build_openai_compatible_llm_client",
                return_value=client,
            ),
            patch("realized_core_engine.supplement.time.sleep") as sleep_mock,
        ):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                ask_llm(
                    "Return JSON.",
                    model="fast-model",
                    reasoning_effort="medium",
                    response_format={"type": "json_object"},
                )

        self.assertEqual(3, len(completions.calls))
        self.assertTrue(
            all(call.get("reasoning_effort") == "medium" for call in completions.calls)
        )
        self.assertEqual([1.0, 2.0], [call.args[0] for call in sleep_mock.call_args_list])

    def test_all_declared_compatibility_fallbacks_preserve_response_shape(self) -> None:
        completions = _AllFallbackCompletions()
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
        with (
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "openai",
                    "OPENAI_MODEL": "fast-model",
                },
                clear=False,
            ),
            patch(
                "realized_core_engine.supplement.build_openai_compatible_llm_client",
                return_value=client,
            ),
        ):
            answer, metadata = ask_llm(
                "Return JSON.",
                model="fast-model",
                reasoning_effort="medium",
                response_format={"type": "json_object"},
                seed=7,
                return_metadata=True,
            )

        self.assertEqual('{"ok": true}', answer)
        self.assertEqual(
            {
                "system_fingerprint": "fingerprint-compatible",
                "model": "compatible-model",
                "response_id": "response-compatible",
            },
            metadata,
        )
        self.assertEqual(6, len(completions.calls))
        self.assertNotIn("max_tokens", completions.calls[-1])
        self.assertEqual(2048, completions.calls[-1]["max_completion_tokens"])
        for parameter in (
            "reasoning_effort",
            "temperature",
            "response_format",
            "seed",
        ):
            self.assertNotIn(parameter, completions.calls[-1])

if __name__ == "__main__":
    unittest.main()
