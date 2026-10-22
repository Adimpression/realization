from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from applied_theory_types import (
    NodeStatus,
    PauseBoundary,
    PausePoint,
    SemanticNode,
)
from system_state import SystemState

from realized_core_engine.canonical_reduction import CanonicalReductionAdapter
from realized_core_engine.resumption_contracts import (
    ContinuationInlet,
    GoverningDirection,
    InletRelationship,
    OperationKind,
    ResumptionRequest,
    StartRequest,
)
from realized_core_engine.resumption_repository import SQLiteResumptionRepository
from realized_core_engine.resumption_service import ResumptionService


def _inlet(
    inlet_id: str,
    *,
    relationship: InletRelationship = InletRelationship.CONTINUATION,
    payload: dict[str, object] | None = None,
    target: str = "root",
    correlation: dict[str, object] | None = None,
) -> ContinuationInlet:
    return ContinuationInlet(
        inlet_id=inlet_id,
        kind="human_contribution",
        payload=payload or {},
        target=target,
        relationship=relationship,
        source="human",
        provenance=(f"message:{inlet_id}",),
        correlation=correlation or {},
        authority_context={"principal": "tester"},
    )


class CanonicalReductionAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "resumption.sqlite3"
        self.repository = SQLiteResumptionRepository(self.database)
        self.service = ResumptionService(
            self.repository,
            reduction_controller=CanonicalReductionAdapter(),
        )
        self.policy = {
            "llm_policy": "off",
            "max_steps": 0,
            "sqlite_path": str(self.database),
            "discovery": "off",
            "reflection": "off",
            "contemplation": "off",
        }

    def test_start_runs_the_canonical_reducer_and_persists_reconstructable_state(
        self,
    ) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            result = self.service.start(
                StartRequest(
                    scope_id="scope-1",
                    objective_id="objective-1",
                    branch_id="main",
                    initial_inlet=_inlet(
                        "start-1",
                        payload={"prompt": "Produce a governed answer."},
                    ),
                    governing_direction=GoverningDirection(
                        objective="Produce a governed answer.",
                        scope="scope-1",
                    ),
                    execution_policy=self.policy,
                )
            )

        revision = self.repository.require_revision(
            result.resulting_revision_identity
        )
        reconstructed = SystemState.from_dict(revision.state.engine_state)

        self.assertEqual(
            "Produce a governed answer.",
            reconstructed.root().semantic_unit,
        )
        self.assertEqual(
            reconstructed.root_id,
            revision.state.refinement_graph["nodes"][0]["id"],
        )
        self.assertEqual(
            result.non_achievedness_summary[0],
            reconstructed.root().metadata["resumption_item_id"],
        )
        self.assertEqual(
            reconstructed.summary()["run_id"],
            result.presentation["run_id"],
        )

    def test_continuation_reconstructs_without_process_or_provider_state(self) -> None:
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            started = self.service.start(
                StartRequest(
                    scope_id="scope-1",
                    objective_id="objective-1",
                    branch_id="main",
                    initial_inlet=_inlet(
                        "start-1",
                        payload={"prompt": "Wait for a value."},
                    ),
                    governing_direction=GoverningDirection(
                        objective="Wait for a value.",
                        scope="scope-1",
                    ),
                    execution_policy=self.policy,
                )
            )
            source = self.repository.require_revision(
                started.resulting_revision_identity
            )
            first_run_id = source.state.engine_state["run_id"]

            replacement_service = ResumptionService(
                SQLiteResumptionRepository(self.database),
                reduction_controller=CanonicalReductionAdapter(),
            )
            continued = replacement_service.resume(
                ResumptionRequest(
                    anchor=source.identity,
                    operation=OperationKind.CONTINUE,
                    expected_branch_head_revision_id=source.identity.revision_id,
                    inlet=_inlet(
                        "continue-1",
                        payload={"content": "The value is 42."},
                        target=source.state.non_achievedness[0].item_id,
                    ),
                    execution_policy=self.policy,
                )
            )

        revision = self.repository.require_revision(
            continued.resulting_revision_identity
        )
        reconstructed = SystemState.from_dict(revision.state.engine_state)

        self.assertEqual(first_run_id, reconstructed.run_id)
        self.assertEqual(1, len(reconstructed.human_contributions))
        contribution = next(iter(reconstructed.human_contributions.values()))
        self.assertEqual("The value is 42.", contribution.content)
        self.assertIn("message:continue-1", contribution.provenance)

    def test_hold_satisfaction_reopens_only_its_continuation_carrier(self) -> None:
        state = SystemState.bootstrap("Wait for two independent answers.")
        child = SemanticNode(
            id="second-node",
            semantic_unit="Wait for the second answer.",
            parent_id=state.root_id,
        )
        state.register_node(child, parent_id=state.root_id)
        for node_id in (state.root_id, child.id):
            state.frontier.discard(node_id)
            state.paused.add(node_id)
            state.status[node_id] = NodeStatus.PAUSED
        state.pause_points = {
            "pause-one": PausePoint(
                id="pause-one",
                node_id=state.root_id,
                reason="first answer required",
                required_boundary=PauseBoundary.HUMAN_CONTRIBUTION,
            ),
            "pause-two": PausePoint(
                id="pause-two",
                node_id=child.id,
                reason="second answer required",
                required_boundary=PauseBoundary.HUMAN_CONTRIBUTION,
            ),
        }

        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            started = self.service.start(
                StartRequest(
                    scope_id="scope-1",
                    objective_id="objective-1",
                    branch_id="main",
                    initial_inlet=_inlet(
                        "start-paused",
                        payload={
                            "prompt": state.root().semantic_unit,
                            "engine_state": state.to_dict(),
                        },
                    ),
                    governing_direction=GoverningDirection(
                        objective=state.root().semantic_unit,
                        scope="scope-1",
                    ),
                    execution_policy=self.policy,
                )
            )
            source = self.repository.require_revision(
                started.resulting_revision_identity
            )
            hold = next(
                item
                for item in source.state.holds
                if item.hold_id == "engine:hold:pause-one"
            )
            resumed = self.service.resume(
                ResumptionRequest(
                    anchor=source.identity,
                    operation=OperationKind.RESUME_SUSPENDED,
                    expected_branch_head_revision_id=source.identity.revision_id,
                    inlet=_inlet(
                        "resume-one",
                        relationship=InletRelationship.HOLD_SATISFACTION,
                        payload={"hold_id": hold.hold_id},
                        target=hold.hold_id,
                        correlation=dict(hold.correlation),
                    ),
                    execution_policy=self.policy,
                )
            )

        revision = self.repository.require_revision(
            resumed.resulting_revision_identity
        )
        reconstructed = SystemState.from_dict(revision.state.engine_state)

        self.assertNotIn(state.root_id, reconstructed.paused)
        self.assertIn(child.id, reconstructed.paused)
        self.assertNotIn("pause-one", reconstructed.pause_points)
        self.assertIn("pause-two", reconstructed.pause_points)
        self.assertEqual(
            ("engine:hold:pause-two",),
            resumed.active_hold_summary,
        )


if __name__ == "__main__":
    unittest.main()
