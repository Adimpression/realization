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
from realized_core_engine import (
    EngineConfiguration,
    InspectionResult,
    InspectionTargetKind,
    InspectionView,
    OperationKind,
    ResumptionIdentity,
    ResumptionResult,
    SemanticOutcome,
)
from realized_core_runtime import AttemptExecutionOutcome


def _identity(
    revision_id: str,
    *,
    objective_id: str = "objective-1",
) -> ResumptionIdentity:
    return ResumptionIdentity(
        scope_id="scope-1",
        objective_id=objective_id,
        branch_id="main",
        revision_id=revision_id,
        state_digest=f"digest:{revision_id}",
    )


def _result(
    revision_id: str,
    *,
    outcome: SemanticOutcome,
    source: ResumptionIdentity | None = None,
    objective_id: str = "objective-1",
    presentation: dict[str, object] | None = None,
) -> ResumptionResult:
    identity = _identity(revision_id, objective_id=objective_id)
    return ResumptionResult(
        source_revision_identity=source,
        execution_attempt_id=f"attempt:{revision_id}",
        execution_outcome=AttemptExecutionOutcome.TERMINATED,
        semantic_outcome=outcome,
        resulting_revision_identity=identity,
        transition_artifact_reference=f"transition:{revision_id}",
        attempt_artifact_reference=f"attempt-ref:{revision_id}",
        realignment_summary=None,
        identity_disposition=None,
        achieved_state_summary=(),
        non_achievedness_summary=(),
        active_hold_summary=(),
        diagnostics={},
        presentation=dict(presentation or {}),
    )


class StubEngine:
    def __init__(self) -> None:
        self.start_result = _result(
            "revision-1",
            outcome=SemanticOutcome.INCOMPLETE,
        )
        self.resume_result = _result(
            "revision-2",
            outcome=SemanticOutcome.INCOMPLETE,
            source=self.start_result.resulting_revision_identity,
        )
        self.states: dict[str, dict[str, object]] = {}
        self.start_requests = []
        self.resume_requests = []
        self.inspect_requests = []

    def start(self, request):
        self.start_requests.append(request)
        return self.start_result

    def resume(self, request):
        self.resume_requests.append(request)
        return self.resume_result

    def inspect(self, request):
        self.inspect_requests.append(request)
        return InspectionResult(
            target_kind=InspectionTargetKind.REVISION,
            target_id=request.target_id,
            view=InspectionView.CURRENT_STATE,
            payload=dict(self.states[request.target_id]),
        )


class CoreConversationHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_dir.cleanup)
        self.root = Path(self.temporary_dir.name)
        self.engine = StubEngine()
        self.host = CoreConversationHost(
            root=self.root,
            configuration=EngineConfiguration(max_steps=0, llm_policy="off"),
            engine=self.engine,
        )

    def test_independent_turn_uses_typed_start_and_no_transcript_state(self) -> None:
        report = self.host.submit("First request")

        request = self.engine.start_requests[0]
        messages = [
            json.loads(line)
            for line in (self.root / "MESSAGES.jsonl").read_text().splitlines()
        ]
        self.assertEqual([1, 2], [item["sequence"] for item in messages])
        self.assertEqual(messages[0]["turn_id"], messages[1]["turn_id"])
        self.assertEqual("First request", request.governing_direction.objective)
        self.assertEqual("First request", request.initial_inlet.payload["prompt"])
        self.assertNotIn("transcript", request.initial_inlet.payload)
        self.assertEqual("revision-1", report["run_id"])
        self.assertNotIn("checkpoint_path", report)
        self.assertEqual(
            "revision-1",
            report["binding"]["resumption_identity"]["revision_id"],
        )

    def test_human_contribution_addresses_one_exact_hold(self) -> None:
        self.engine.start_result = _result(
            "revision-paused",
            outcome=SemanticOutcome.PAUSED,
        )
        parent = self.host.submit("Ask me for the missing value")
        self.engine.states["revision-paused"] = {
            "achieved": [],
            "non_achievedness": [
                {"item_id": "not-1", "kind": "not", "payload": {}}
            ],
            "holds": [
                {
                    "hold_id": "hold-1",
                    "disposition": "remain_held",
                    "correlation": {"token": "correlation-1"},
                }
            ],
        }
        self.engine.resume_result = _result(
            "revision-resumed",
            outcome=SemanticOutcome.COMPLETED,
            source=_identity("revision-paused"),
            presentation={"final_answer": "42"},
        )

        resumed = self.host.submit(
            "42",
            treatment="human_contribution",
            parent_run_id=parent["run_id"],
        )

        request = self.engine.resume_requests[-1]
        self.assertEqual(OperationKind.RESUME_SUSPENDED, request.operation)
        self.assertEqual("revision-paused", request.anchor.revision_id)
        self.assertEqual("hold-1", request.inlet.target)
        self.assertEqual({"token": "correlation-1"}, request.inlet.correlation)
        self.assertEqual("42", request.inlet.payload["content"])
        self.assertTrue(request.inlet.inlet_id.startswith("msg_"))
        self.assertEqual("revision-resumed", resumed["run_id"])

    def test_multiple_holds_require_explicit_selection(self) -> None:
        parent = self.host.submit("Wait")
        self.engine.states["revision-1"] = {
            "achieved": [],
            "non_achievedness": [],
            "holds": [
                {"hold_id": "hold-1", "correlation": {}},
                {"hold_id": "hold-2", "correlation": {}},
            ],
        }

        with self.assertRaisesRegex(ValueError, "select one explicitly"):
            self.host.submit(
                "Signal",
                treatment="human_contribution",
                parent_run_id=parent["run_id"],
            )

    def test_follow_up_derives_from_explicit_admitted_parent_material(self) -> None:
        self.engine.start_result = _result(
            "revision-parent",
            outcome=SemanticOutcome.COMPLETED,
            presentation={"final_answer": "Committed answer"},
        )
        parent = self.host.submit("Parent request")
        self.engine.states["revision-parent"] = {
            "achieved": [
                {"item_id": "fact-parent", "kind": "fact", "payload": {}}
            ],
            "non_achievedness": [],
            "holds": [],
        }
        self.engine.resume_result = _result(
            "revision-child",
            objective_id="objective-child",
            outcome=SemanticOutcome.INCOMPLETE,
            source=_identity("revision-parent"),
        )

        child = self.host.submit(
            "Follow-up request",
            treatment="follow_up",
            parent_run_id=parent["run_id"],
        )

        request = self.engine.resume_requests[-1]
        self.assertEqual(OperationKind.DERIVE, request.operation)
        self.assertEqual(["fact-parent"], request.inlet.payload["selected_item_ids"])
        self.assertEqual("Follow-up request", request.inlet.payload["content"])
        self.assertNotIn("Parent request", request.inlet.payload["content"])
        self.assertNotEqual(
            request.anchor.objective_id,
            request.inlet.payload["target_objective_id"],
        )
        self.assertEqual("revision-parent", child["parent_run_id"])

    def test_correction_requires_and_supersedes_one_explicit_current_item(self) -> None:
        self.engine.start_result = _result(
            "revision-original",
            outcome=SemanticOutcome.COMPLETED,
        )
        parent = self.host.submit("Original request")
        self.engine.states["revision-original"] = {
            "achieved": [
                {"item_id": "fact-original", "kind": "fact", "payload": {}}
            ],
            "non_achievedness": [],
            "holds": [],
        }

        with self.assertRaisesRegex(ValueError, "explicit current semantic item"):
            self.host.submit(
                "Corrected value",
                treatment="correction",
                parent_run_id=parent["run_id"],
            )

        self.engine.resume_result = _result(
            "revision-corrected",
            outcome=SemanticOutcome.COMPLETED,
            source=_identity("revision-original"),
        )
        correction = self.host.submit(
            "Corrected value",
            treatment="correction",
            parent_run_id=parent["run_id"],
            correction_target_item_id="fact-original",
        )

        request = self.engine.resume_requests[-1]
        supersession = request.inlet.delta.supersessions[0]
        self.assertEqual(OperationKind.CORRECT, request.operation)
        self.assertEqual("fact-original", supersession.target_item_id)
        self.assertEqual("Corrected value", supersession.replacement.payload["text"])
        self.assertEqual("revision-corrected", correction["run_id"])

    def test_cli_composes_chat_host_with_typed_engine_configuration(self) -> None:
        chat_root = self.root / "cli-chat"

        with (
            patch(
                "realized_core.chat.open_resumption_engine",
                return_value=self.engine,
            ),
            patch("realized_core.cli.run_core_chat_loop", return_value=0) as loop,
        ):
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
        self.assertIs(self.engine, host.engine)

    def test_real_host_continues_from_exact_sqlite_revision_without_checkpoint(
        self,
    ) -> None:
        real_root = self.root / "real-host"
        host = CoreConversationHost(
            root=real_root,
            configuration=EngineConfiguration(
                max_steps=0,
                llm_policy="off",
            ),
        )

        parent = host.submit("Wait for one explicit value.")
        continued = host.submit(
            "The value is 42.",
            treatment="human_contribution",
            parent_run_id=parent["run_id"],
        )

        self.assertEqual(parent["run_id"], continued["parent_run_id"])
        self.assertNotEqual(parent["run_id"], continued["run_id"])
        self.assertFalse((real_root / "states").exists())
        self.assertTrue((real_root / "artifacts.sqlite3").exists())
        bindings = [
            json.loads(line)
            for line in (real_root / "RUN_BINDINGS.jsonl")
            .read_text()
            .splitlines()
        ]
        self.assertEqual(2, len(bindings))
        self.assertEqual(
            parent["run_id"],
            bindings[1]["parent_run_id"],
        )


if __name__ == "__main__":
    unittest.main()
