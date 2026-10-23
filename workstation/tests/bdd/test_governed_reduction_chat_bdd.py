from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workstation.contracts.runtime import (
    ControllerRuntimeProvider,
    GovernedTurnResult,
)
from workstation.runtime.core.session import (
    launch_workstation_session,
    prompt_workstation_session,
)
from workstation.shell.core.workstation_shell_api import WorkstationShellApiService


class _RecordingProvider:
    def __init__(self, results: list[dict[str, str]]) -> None:
        self.requests = []
        self.results = list(results)

    def perform_governed_turn(self, request):
        self.requests.append(request)
        selected = self.results.pop(0)
        return GovernedTurnResult(
            assistant_text=selected.get("assistant_text", "answer"),
            run_id=selected["run_id"],
            parent_run_id=request.parent_run_id,
            run_outcome=selected.get("run_outcome", "completed"),
            root_status=selected.get("root_status", "closed"),
            checkpoint_path=request.checkpoint_path,
            sqlite_path=request.sqlite_path,
            summary={
                "run_id": selected["run_id"],
                "run_outcome": selected.get("run_outcome", "completed"),
                "final_answer": selected.get("assistant_text", "answer"),
                "root": {"status": selected.get("root_status", "closed")},
            },
        )


class GovernedReductionChatBDD(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.root = Path(self.temporary_dir.name) / "workstation"
        self.workspace = Path(self.temporary_dir.name) / "workspace"
        self.workspace.mkdir()
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            attach_default_skill_home=False,
            allowed_capabilities=(),
        )

    def test_independent_governed_turn_persists_distinct_identity_domains(self) -> None:
        provider = _RecordingProvider(
            [{"run_id": "run-independent", "assistant_text": "governed answer"}]
        )

        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=provider,
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="Answer through governed reduction.",
                interaction_mode="governed_reduction",
                governed_llm_policy="off",
                governed_max_steps=0,
            )

        messages = [
            json.loads(line)
            for line in (self.root / "MESSAGES.jsonl").read_text().splitlines()
        ]
        binding = json.loads((self.root / "GOVERNED_TURNS.jsonl").read_text().strip())
        self.assertEqual([1, 2], [message["sequence"] for message in messages])
        self.assertEqual(messages[0]["turn_id"], messages[1]["turn_id"])
        self.assertEqual(messages[0]["turn_id"], binding["turn_id"])
        self.assertEqual(messages[0]["message_id"], binding["user_message_id"])
        self.assertEqual(messages[1]["message_id"], binding["assistant_message_id"])
        self.assertEqual("run-independent", binding["run_id"])
        self.assertNotEqual(Path(binding["checkpoint_path"]), Path(binding["sqlite_path"]))
        self.assertEqual("governed_reduction", report["fulfilled_by"])

    def test_explicit_human_contribution_reuses_selected_checkpoint_after_restart(self) -> None:
        first_provider = _RecordingProvider(
            [
                {
                    "run_id": "run-paused",
                    "run_outcome": "paused",
                    "root_status": "paused",
                    "assistant_text": "need contribution",
                }
            ]
        )
        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=first_provider,
        ):
            initial = prompt_workstation_session(
                root_path=self.root,
                prompt="Pause for an answer.",
                interaction_mode="governed_reduction",
                governed_llm_policy="off",
                governed_max_steps=0,
            )

        restarted_provider = _RecordingProvider(
            [
                {
                    "run_id": "run-paused",
                    "run_outcome": "completed",
                    "assistant_text": "continued answer",
                }
            ]
        )
        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=restarted_provider,
        ):
            continued = prompt_workstation_session(
                root_path=self.root,
                prompt="The selected answer is 42.",
                interaction_mode="governed_reduction",
                governed_treatment="human_contribution",
                governed_parent_run_id="run-paused",
                governed_llm_policy="off",
                governed_max_steps=0,
            )

        continuation_request = restarted_provider.requests[0]
        self.assertEqual("human_contribution", continuation_request.treatment)
        self.assertEqual("run-paused", continuation_request.parent_run_id)
        self.assertEqual(
            Path(initial["checkpoint_path"]),
            Path(continued["checkpoint_path"]),
        )
        self.assertTrue(continuation_request.user_message_id.startswith("msg_"))

    def test_follow_up_creates_linked_checkpoint_without_forwarding_transcript(self) -> None:
        provider = _RecordingProvider(
            [
                {"run_id": "run-parent", "assistant_text": "parent answer"},
                {"run_id": "run-child", "assistant_text": "child answer"},
            ]
        )
        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=provider,
        ):
            parent = prompt_workstation_session(
                root_path=self.root,
                prompt="Parent request with transcript-only wording.",
                interaction_mode="governed_reduction",
                governed_llm_policy="off",
                governed_max_steps=0,
            )
            child = prompt_workstation_session(
                root_path=self.root,
                prompt="A related follow-up.",
                interaction_mode="governed_reduction",
                governed_treatment="follow_up",
                governed_parent_run_id="run-parent",
                governed_llm_policy="off",
                governed_max_steps=0,
            )

        follow_up_request = provider.requests[1]
        self.assertEqual("A related follow-up.", follow_up_request.prompt)
        self.assertFalse(hasattr(follow_up_request, "message_history"))
        self.assertNotEqual(parent["checkpoint_path"], child["checkpoint_path"])
        self.assertEqual("run-parent", child["parent_run_id"])

    def test_llm_only_turn_does_not_enter_controller_provider(self) -> None:
        with (
            patch(
                "workstation.runtime.core.session.controller_runtime_provider",
                side_effect=AssertionError("normal chat must not enter governed reduction"),
            ),
            patch(
                "workstation.runtime.core.session.run_workstation_openai_turn",
                return_value={
                    "assistant_text": "ordinary answer",
                    "tool_receipts": [],
                    "model": "test-model",
                    "rounds": 1,
                    "fulfilled_by": "llm",
                    "fallback_used": False,
                },
            ),
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="Ordinary chat.",
                interaction_mode="llm_only",
            )

        self.assertEqual("ordinary answer", report["assistant_text"])
        self.assertEqual("", (self.root / "GOVERNED_TURNS.jsonl").read_text())

    def test_normal_shell_chat_does_not_enter_controller_provider(self) -> None:
        with (
            patch(
                "workstation.runtime.core.session.controller_runtime_provider",
                side_effect=AssertionError("normal chat must not enter governed reduction"),
            ),
            patch(
                "workstation.runtime.core.session.run_workstation_natural_language_shell_command",
                return_value=(
                    True,
                    {
                        "assistant_text": "ordinary shell answer",
                        "fulfilled_by": "workstation.shell",
                    },
                ),
            ),
        ):
            report = prompt_workstation_session(
                root_path=self.root,
                prompt="Handle this through the ordinary shell.",
            )

        self.assertEqual("ordinary shell answer", report["assistant_text"])
        self.assertEqual("normal", report["interaction_mode"])
        self.assertTrue(report["turn_id"].startswith("turn_"))
        self.assertEqual("", (self.root / "GOVERNED_TURNS.jsonl").read_text())

    def test_shell_contract_exposes_explicit_governed_turn_without_ui_coupling(self) -> None:
        provider = _RecordingProvider(
            [{"run_id": "run-shell", "assistant_text": "shell governed answer"}]
        )
        service = WorkstationShellApiService()

        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=provider,
        ):
            result = service.submit_chat_input(
                root_path=self.root,
                client_session_id="client-1",
                prompt_text="Use governed reduction explicitly.",
                interaction_mode="governed_reduction",
                governed_treatment="independent",
                governed_llm_policy="off",
                governed_max_steps=0,
            )

        self.assertEqual("governed_reduction", result.fulfilled_by)
        self.assertEqual("run-shell", result.run_id)
        self.assertTrue(result.turn_id.startswith("turn_"))
        self.assertTrue(result.checkpoint_path.endswith(".json"))

    def test_missing_controller_provider_fails_explicitly(self) -> None:
        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            side_effect=RuntimeError("controller provider is unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "provider is unavailable"):
                prompt_workstation_session(
                    root_path=self.root,
                    prompt="Use governed reduction.",
                    interaction_mode="governed_reduction",
                    governed_llm_policy="off",
                    governed_max_steps=0,
                )

    def test_existing_provider_without_governed_extension_still_registers(self) -> None:
        class _ExistingProvider:
            def bootstrap_controller(self, semantic_unit, llm_policy):
                return object(), object()

            def learn_markdown_bundle(
                self,
                *,
                markdown_file,
                title,
                state_out,
                sqlite_path,
                llm_policy,
            ):
                return {}

        provider = _ExistingProvider()
        self.assertIsInstance(provider, ControllerRuntimeProvider)

        with patch(
            "workstation.runtime.core.session.controller_runtime_provider",
            return_value=provider,
        ):
            with self.assertRaisesRegex(RuntimeError, "does not support governed turns"):
                prompt_workstation_session(
                    root_path=self.root,
                    prompt="Use governed reduction.",
                    interaction_mode="governed_reduction",
                    governed_llm_policy="off",
                    governed_max_steps=0,
                )


if __name__ == "__main__":
    unittest.main()
