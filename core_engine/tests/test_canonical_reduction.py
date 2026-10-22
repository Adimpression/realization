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
    IdentityDisposition,
    IdentityDispositionKind,
    InletRelationship,
    OperationKind,
    Realignment,
    ResumptionRequest,
    SemanticDelta,
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
    delta: SemanticDelta = SemanticDelta(),
    realignment: Realignment | None = None,
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
        delta=delta,
        realignment=realignment,
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
        artifact_id = result.transition_artifact_reference.rsplit("/", 1)[-1]
        artifact = self.repository.load_transition_artifact(artifact_id)
        self.assertEqual(
            result.execution_attempt_id,
            artifact["execution_attempt_id"],
        )
        self.assertEqual("commit", artifact["commit_decision"]["disposition"])
        self.assertTrue(artifact["reduction_trace"])
        attempt = self.repository.load_attempt(result.execution_attempt_id)
        for measurement in (
            "attempt_preparation_latency_ns",
            "revision_load_latency_ns",
            "verification_and_admission_latency_ns",
            "reduction_latency_ns",
            "atomic_commit_latency_ns",
        ):
            self.assertGreater(
                attempt.performance_measurements[measurement],
                0,
            )
        self.assertNotIn(
            "performance_measurements",
            revision.state.to_dict(),
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
            started_artifact = self.repository.load_transition_artifact(
                started.transition_artifact_reference.rsplit("/", 1)[-1]
            )

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
        continued_artifact = self.repository.load_transition_artifact(
            continued.transition_artifact_reference.rsplit("/", 1)[-1]
        )
        prior_sequences = {
            item["sequence"] for item in started_artifact["reduction_trace"]
        }
        current_sequences = {
            item["sequence"] for item in continued_artifact["reduction_trace"]
        }
        self.assertTrue(current_sequences)
        self.assertTrue(prior_sequences.isdisjoint(current_sequences))
        continued_attempt = self.repository.load_attempt(
            continued.execution_attempt_id
        )
        self.assertGreater(
            continued_attempt.performance_measurements[
                "projection_construction_latency_ns"
            ],
            0,
        )
        self.assertGreater(
            continued_attempt.performance_measurements[
                "projection_size_bytes"
            ],
            0,
        )

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

    def test_redirection_never_runs_the_frontier_from_the_prior_direction(
        self,
    ) -> None:
        prior_state = SystemState.bootstrap("Continue the prior direction.")
        prior_root_id = prior_state.root_id
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            started = self.service.start(
                StartRequest(
                    scope_id="scope-1",
                    objective_id="objective-1",
                    branch_id="main",
                    initial_inlet=_inlet(
                        "start-prior",
                        payload={
                            "prompt": prior_state.root().semantic_unit,
                            "engine_state": prior_state.to_dict(),
                        },
                    ),
                    governing_direction=GoverningDirection(
                        objective=prior_state.root().semantic_unit,
                        scope="scope-1",
                    ),
                    execution_policy=self.policy,
                )
            )
            source = self.repository.require_revision(
                started.resulting_revision_identity
            )
            affected = tuple(
                item.item_id
                for item in (
                    *source.state.achieved,
                    *source.state.non_achievedness,
                )
            )
            direction = GoverningDirection(
                objective="Advance only the redirected objective.",
                scope="scope-1",
            )
            realignment = Realignment(
                source_revision_id=source.identity.revision_id,
                redirection_inlet_id="redirect-new",
                affected_item_ids=affected,
                identity_disposition=IdentityDisposition(
                    kind=IdentityDispositionKind.SAME_OBJECTIVE,
                    target_scope_id="scope-1",
                    target_objective_id="objective-1",
                    target_branch_id="main",
                    rationale="The same objective now has an explicit new direction.",
                ),
                retained_item_ids=(),
                superseded_item_ids=affected,
                introduced_items=(),
                unresolved_applicability_item_ids=(),
                resulting_non_achievedness=(),
                evidence_references=("direction:redirect-new",),
                governance_references=("policy:realignment",),
                completeness_statement="All prior frontier material is superseded.",
            )
            redirected = self.service.resume(
                ResumptionRequest(
                    anchor=source.identity,
                    operation=OperationKind.REDIRECT_AND_REALIGN,
                    expected_branch_head_revision_id=(
                        source.identity.revision_id
                    ),
                    inlet=_inlet(
                        "redirect-new",
                        relationship=InletRelationship.REDIRECTION,
                        payload={"prompt": direction.objective},
                        delta=SemanticDelta(governing_direction=direction),
                        realignment=realignment,
                    ),
                    execution_policy=self.policy,
                )
            )

        revision = self.repository.require_revision(
            redirected.resulting_revision_identity
        )
        reconstructed = SystemState.from_dict(revision.state.engine_state)
        attempt = self.repository.load_attempt(
            redirected.execution_attempt_id
        )
        artifact = self.repository.load_transition_artifact(
            attempt.transition_artifact_references[-1]
        )
        prepared_frontier = artifact["reconciliation"]["reduction"][
            "prepared_frontier"
        ]

        self.assertEqual(direction.objective, reconstructed.root().semantic_unit)
        self.assertNotIn(prior_root_id, reconstructed.graph.nodes)
        self.assertNotIn(prior_root_id, prepared_frontier)
        self.assertEqual([reconstructed.root_id], prepared_frontier)


if __name__ == "__main__":
    unittest.main()
