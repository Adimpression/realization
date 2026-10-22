from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_APP_SRC = REPO_ROOT / "core_app" / "src"
if str(CORE_APP_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_APP_SRC))

from realized_core import cli
from realized_core.chat import CoreConversationHost
from realized_core_engine import EngineConfiguration, EngineResult


def _summary(
    run_id: str,
    *,
    outcome: str,
    answer: str | None = None,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "run_outcome": outcome,
        "final_answer": answer,
        "root": {"status": "closed" if outcome == "completed" else outcome},
    }


class CoreConversationHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.root = Path(self.temporary_dir.name)
        self.host = CoreConversationHost(
            root=self.root,
            configuration=EngineConfiguration(max_steps=0, llm_policy="off"),
        )

    def test_independent_turn_has_stable_identity_and_no_transcript_inlet(self) -> None:
        def fake_run(prompt, *, configuration):
            configuration.state_output_path.write_text("{}", encoding="utf-8")
            self.assertEqual((), configuration.inlets)
            return EngineResult(summary=_summary("run-one", outcome="completed", answer="one"))

        with patch("realized_core.chat.run_engine", side_effect=fake_run):
            report = self.host.submit("First request")

        messages = [json.loads(line) for line in (self.root / "MESSAGES.jsonl").read_text().splitlines()]
        self.assertEqual([1, 2], [item["sequence"] for item in messages])
        self.assertEqual(messages[0]["turn_id"], messages[1]["turn_id"])
        self.assertNotEqual(messages[0]["message_id"], messages[1]["message_id"])
        self.assertEqual("run-one", report["run_id"])

    def test_human_contribution_resumes_selected_run_with_message_provenance(self) -> None:
        def fake_run(prompt, *, configuration):
            configuration.state_output_path.write_text("{}", encoding="utf-8")
            return EngineResult(summary=_summary("run-paused", outcome="paused"))

        with patch("realized_core.chat.run_engine", side_effect=fake_run):
            initial = self.host.submit("Ask me for the missing value")

        resumed_configurations = []

        def fake_resume(state_path, *, configuration):
            resumed_configurations.append(configuration)
            return EngineResult(summary=_summary("run-paused", outcome="completed", answer="42"))

        with (
            patch(
                "realized_core.chat.inspect_engine",
                return_value=EngineResult(summary=_summary("run-paused", outcome="paused")),
            ),
            patch("realized_core.chat.resume_engine", side_effect=fake_resume),
        ):
            resumed = self.host.submit(
                "The missing value is 42",
                treatment="human_contribution",
                parent_run_id=initial["run_id"],
            )

        inlet = resumed_configurations[0].inlets[0]
        self.assertEqual("human_contribution", inlet.kind)
        self.assertEqual("The missing value is 42", inlet.content)
        self.assertTrue(inlet.source_ref.startswith("msg_"))
        self.assertEqual(initial["checkpoint_path"], resumed["checkpoint_path"])

    def test_follow_up_starts_linked_run_with_only_committed_parent_result(self) -> None:
        run_calls = []

        def fake_run(prompt, *, configuration):
            run_calls.append((prompt, configuration))
            configuration.state_output_path.write_text("{}", encoding="utf-8")
            if len(run_calls) == 1:
                return EngineResult(
                    summary=_summary("run-parent", outcome="completed", answer="Committed answer")
                )
            return EngineResult(summary=_summary("run-child", outcome="completed", answer="Followed up"))

        with patch("realized_core.chat.run_engine", side_effect=fake_run):
            parent = self.host.submit("Parent request")
            with patch(
                "realized_core.chat.inspect_engine",
                return_value=EngineResult(
                    summary=_summary("run-parent", outcome="completed", answer="Committed answer")
                ),
            ):
                child = self.host.submit(
                    "Follow-up request",
                    treatment="follow_up",
                    parent_run_id=parent["run_id"],
                )

        inlet = run_calls[1][1].inlets[0]
        self.assertEqual("prior_result", inlet.kind)
        self.assertEqual("Committed answer", inlet.content)
        self.assertNotIn("Parent request", inlet.content)
        self.assertEqual("run-parent", child["parent_run_id"])
        self.assertNotEqual(parent["checkpoint_path"], child["checkpoint_path"])

    def test_correction_never_resumes_closed_parent(self) -> None:
        def fake_run(prompt, *, configuration):
            configuration.state_output_path.write_text("{}", encoding="utf-8")
            answer = "Original" if prompt == "Original request" else "Corrected"
            run_id = "run-original" if prompt == "Original request" else "run-correction"
            return EngineResult(summary=_summary(run_id, outcome="completed", answer=answer))

        with patch("realized_core.chat.run_engine", side_effect=fake_run) as run_mock:
            parent = self.host.submit("Original request")
            with (
                patch(
                    "realized_core.chat.inspect_engine",
                    return_value=EngineResult(
                        summary=_summary("run-original", outcome="completed", answer="Original")
                    ),
                ),
                patch("realized_core.chat.resume_engine") as resume_mock,
            ):
                correction = self.host.submit(
                    "Correct the original",
                    treatment="correction",
                    parent_run_id=parent["run_id"],
                )

        self.assertEqual(2, run_mock.call_count)
        resume_mock.assert_not_called()
        self.assertEqual("run-original", correction["parent_run_id"])

    def test_cli_composes_chat_host_with_engine_configuration(self) -> None:
        chat_root = self.root / "cli-chat"

        with patch("realized_core.cli.run_core_chat_loop", return_value=0) as loop:
            status = cli.main(
                [
                    "chat",
                    "--root",
                    str(chat_root),
                    "--llm",
                    "off",
                    "--max-steps",
                    "7",
                ]
            )

        self.assertEqual(0, status)
        host = loop.call_args.args[0]
        self.assertIsInstance(host, CoreConversationHost)
        self.assertEqual(chat_root.resolve(), host.root)
        self.assertEqual("off", host.configuration.llm_policy)
        self.assertEqual(7, host.configuration.max_steps)


if __name__ == "__main__":
    unittest.main()
