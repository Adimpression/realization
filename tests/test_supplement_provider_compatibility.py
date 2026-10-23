from __future__ import annotations

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from supplement import ask_llm


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
                "supplement.build_openai_compatible_llm_client",
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
                "supplement.build_openai_compatible_llm_client",
                return_value=client,
            ),
            patch("supplement.time.sleep"),
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

if __name__ == "__main__":
    unittest.main()
