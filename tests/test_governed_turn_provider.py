from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from realized_core_engine import EngineResult
from workstation.app.cli.composition import (
    ApplicationControllerRuntimeProvider as _ApplicationControllerRuntimeProvider,
)
from workstation.contracts.runtime import GovernedTurnRequest


def _summary(run_id: str, outcome: str, answer: str | None = None) -> dict[str, object]:
    return {
        "run_id": run_id,
        "run_outcome": outcome,
        "final_answer": answer,
        "root": {"status": "closed" if outcome == "completed" else outcome},
    }


class ApplicationGovernedTurnProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.root = Path(self.temporary_dir.name)
        self.parent_checkpoint = self.root / "parent.json"
        self.parent_checkpoint.write_text("{}", encoding="utf-8")
        self.provider = _ApplicationControllerRuntimeProvider()

    def request(self, treatment: str, *, parent_run_id: str = "") -> GovernedTurnRequest:
        return GovernedTurnRequest(
            session_id="session-1",
            turn_id="turn-2",
            user_message_id="message-3",
            prompt="Current selected user contribution",
            treatment=treatment,
            checkpoint_path=(
                self.parent_checkpoint
                if treatment == "human_contribution"
                else self.root / f"{treatment}.json"
            ),
            sqlite_path=self.root / "artifacts.sqlite3",
            parent_run_id=parent_run_id,
            parent_checkpoint_path=(
                self.parent_checkpoint if treatment != "independent" else None
            ),
            llm_policy="off",
            max_steps=0,
        )

    def test_independent_request_starts_without_inlets(self) -> None:
        with patch(
            "workstation.app.cli.composition.start_core_run",
            return_value=EngineResult(
                summary=_summary("run-independent", "completed", "answer")
            ),
        ) as start_mock:
            result = self.provider.perform_governed_turn(self.request("independent"))

        configuration = start_mock.call_args.kwargs["configuration"]
        self.assertEqual((), configuration.inlets)
        self.assertEqual("run-independent", result.run_id)

    def test_human_contribution_is_provenance_bearing_and_resumes_same_run(self) -> None:
        with (
            patch(
                "workstation.app.cli.composition.inspect_core_state",
                return_value=EngineResult(summary=_summary("run-paused", "paused")),
            ),
            patch(
                "workstation.app.cli.composition.resume_core_run",
                return_value=EngineResult(
                    summary=_summary("run-paused", "completed", "continued")
                ),
            ) as resume_mock,
        ):
            result = self.provider.perform_governed_turn(
                self.request("human_contribution", parent_run_id="run-paused")
            )

        inlet = resume_mock.call_args.kwargs["configuration"].inlets[0]
        self.assertEqual("human_contribution", inlet.kind)
        self.assertEqual("message-3", inlet.source_ref)
        self.assertIn("turn-2", inlet.provenance)
        self.assertEqual("run-paused", result.run_id)

    def test_closed_run_rejects_ordinary_resume(self) -> None:
        with patch(
            "workstation.app.cli.composition.inspect_core_state",
            return_value=EngineResult(
                summary=_summary("run-closed", "completed", "closed answer")
            ),
        ):
            with self.assertRaisesRegex(ValueError, "paused or incomplete"):
                self.provider.perform_governed_turn(
                    self.request("human_contribution", parent_run_id="run-closed")
                )

    def test_follow_up_starts_new_run_with_only_committed_parent_answer(self) -> None:
        with (
            patch(
                "workstation.app.cli.composition.inspect_core_state",
                return_value=EngineResult(
                    summary=_summary("run-parent", "completed", "committed answer")
                ),
            ),
            patch(
                "workstation.app.cli.composition.start_core_run",
                return_value=EngineResult(
                    summary=_summary("run-child", "completed", "child answer")
                ),
            ) as start_mock,
        ):
            result = self.provider.perform_governed_turn(
                self.request("follow_up", parent_run_id="run-parent")
            )

        inlet = start_mock.call_args.kwargs["configuration"].inlets[0]
        self.assertEqual("prior_result", inlet.kind)
        self.assertEqual("committed answer", inlet.content)
        self.assertEqual("run-parent", inlet.source_ref)
        self.assertEqual("run-parent", result.parent_run_id)

    def test_correction_of_closed_run_starts_new_run_instead_of_resuming(self) -> None:
        with (
            patch(
                "workstation.app.cli.composition.inspect_core_state",
                return_value=EngineResult(
                    summary=_summary("run-parent", "completed", "committed answer")
                ),
            ),
            patch(
                "workstation.app.cli.composition.start_core_run",
                return_value=EngineResult(
                    summary=_summary("run-correction", "completed", "corrected")
                ),
            ) as start_mock,
            patch("workstation.app.cli.composition.resume_core_run") as resume_mock,
        ):
            result = self.provider.perform_governed_turn(
                self.request("correction", parent_run_id="run-parent")
            )

        start_mock.assert_called_once()
        resume_mock.assert_not_called()
        self.assertEqual("run-correction", result.run_id)


if __name__ == "__main__":
    unittest.main()
