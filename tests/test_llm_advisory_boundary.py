from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from tempfile import TemporaryDirectory

from workstation.foundation.models import TaskBoundaryContract, WorkstationSession
from workstation.runtime.core.llm_driver import run_workstation_openai_turn


class _ProposingCompletions:
    def __init__(self, sentinel: Path) -> None:
        self.sentinel = sentinel
        self.requests: list[dict[str, object]] = []

    def create(self, **request: object) -> dict[str, object]:
        self.requests.append(dict(request))
        if len(self.requests) == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {
                                        "name": "ws__process__run",
                                        "arguments": json.dumps(
                                            {
                                                "command": [
                                                    "touch",
                                                    str(self.sentinel),
                                                ]
                                            }
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        return {
            "choices": [
                {
                    "message": {
                        "content": "The operation was denied by the host.",
                        "tool_calls": [],
                    }
                }
            ]
        }


class LlmAdvisoryBoundaryTests(TestCase):
    def test_provider_tool_call_cannot_bypass_injected_host_mediator(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "must-not-exist"
            completions = _ProposingCompletions(sentinel)
            client = SimpleNamespace(
                chat=SimpleNamespace(completions=completions)
            )
            mediated_calls: list[tuple[str, dict[str, object]]] = []

            def deny(
                capability_name: str,
                arguments: dict[str, object],
            ) -> dict[str, object]:
                mediated_calls.append((capability_name, arguments))
                return {"status": "denied", "reason": "not authorized"}

            report = run_workstation_openai_turn(
                session=WorkstationSession(
                    session_id="boundary-test",
                    root_path=str(root),
                    created_at="2026-10-27T00:00:00+00:00",
                    attachments=(),
                    allowed_capabilities=("ws.process.run",),
                    openai_profile=None,
                    openai_env_var=None,
                    initial_task="Create a sentinel file.",
                ),
                task_contract=TaskBoundaryContract(
                    semantic_unit="Create a sentinel file.",
                    boundary_shape=(),
                    input_values={},
                    read_references=(),
                    write_targets=(str(sentinel),),
                    output_values=(),
                    side_effects=("create file",),
                    completion_conditions=("sentinel exists",),
                    assumptions=(),
                    missing_requirements=(),
                ),
                prompt="Create the sentinel file.",
                message_history=[],
                tool_definitions=[
                    {
                        "type": "function",
                        "function": {
                            "name": "ws.process.run",
                            "description": "Run an authorized process.",
                            "parameters": {"type": "object"},
                        },
                    }
                ],
                tool_executor=deny,
                model="boundary-test-model",
                client=client,
            )

            self.assertFalse(sentinel.exists())
            self.assertEqual("ws.process.run", mediated_calls[0][0])
            self.assertEqual(
                ["touch", str(sentinel)],
                mediated_calls[0][1]["command"],
            )
            self.assertEqual("denied", report["tool_receipts"][0]["result"]["status"])
            tool_messages = [
                item
                for item in completions.requests[1]["messages"]
                if item.get("role") == "tool"
            ]
            self.assertEqual(1, len(tool_messages))
            self.assertIn('"status": "denied"', tool_messages[0]["content"])


if __name__ == "__main__":
    import unittest

    unittest.main()
