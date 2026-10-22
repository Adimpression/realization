from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
import sqlite3

from realized_core_runtime import (
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptUpdate,
    InterruptionRequest,
    request_attempt_interruption,
)

from realized_core_engine.resumption_contracts import (
    AdmissionDecision,
    AdmissionDisposition,
    GoverningDirection,
    OperationKind,
    ProjectionPolicy,
    ResumptionIdentity,
    Revision,
    SemanticItem,
    SemanticOutcome,
    SemanticState,
    TransitionArtifact,
    canonical_json,
    content_digest,
)
from realized_core_engine.resumption_repository import (
    AttemptNotRunningError,
    SQLiteResumptionRepository,
    StaleAnchorError,
)


def _state(label: str) -> SemanticState:
    return SemanticState(
        achieved=(
            SemanticItem(
                item_id=f"fact-{label}",
                kind="fact",
                payload={"text": label},
            ),
        ),
        non_achievedness=(),
        governing_direction=GoverningDirection(
            objective="Prove repository behavior",
            scope="test",
            required_outcome="verified",
        ),
    )


def _revision_and_artifact(
    *,
    revision_id: str,
    artifact_id: str,
    state: SemanticState,
    parents: tuple[str, ...] = (),
) -> tuple[Revision, TransitionArtifact]:
    identity = ResumptionIdentity(
        scope_id="scope-1",
        objective_id="objective-1",
        branch_id="main",
        revision_id=revision_id,
        state_digest=state.digest,
    )
    revision = Revision(
        identity=identity,
        parent_revision_ids=parents,
        state=state,
        provenance_references=("source-1",),
        governance_references=("policy-1",),
        transition_artifact_id=artifact_id,
        revision_digest="",
        created_at="2026-01-01T00:00:00+00:00",
    )
    revision = replace(
        revision,
        revision_digest=content_digest(revision.canonical_content()),
    )
    inlet_artifact = {"inlet_id": "inlet-1", "kind": "repository-test"}
    artifact = TransitionArtifact(
        artifact_id=artifact_id,
        source_identity=None,
        source_revision_digest=None,
        projection_policy=ProjectionPolicy(),
        projection_digest=None,
        projection_completeness_statement="complete",
        inlet_id="inlet-1",
        inlet_digest=content_digest(inlet_artifact),
        operation=OperationKind.START,
        reconciliation={"kind": "test"},
        proposal_references=(),
        admission=AdmissionDecision(
            disposition=AdmissionDisposition.ACCEPTED,
            rationale="test admission",
        ),
        admitted_delta={"state_digest": state.digest},
        rejected_delta={},
        superseded_delta={},
        conflicting_delta={},
        unresolved_delta={},
        hold_evaluation={},
        capability_receipt_references=(),
        effect_receipt_references=(),
        semantic_outcome=SemanticOutcome.COMPLETED,
        resulting_revision_id=revision_id,
        resulting_revision_digest=revision.revision_digest,
        decision_flow_signature="",
        inlet_artifact=inlet_artifact,
    )
    artifact = replace(
        artifact,
        decision_flow_signature=artifact.expected_decision_flow_signature,
    )
    return revision, artifact


class ResumptionRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repository = SQLiteResumptionRepository(
            Path(self.temporary.name) / "resumption.sqlite3",
            clock=lambda: "2026-01-01T00:00:00+00:00",
        )

    def _running_attempt(self, attempt_id: str = "attempt-1") -> None:
        self.repository.prepare_attempt(
            AttemptRecord(
                attempt_id=attempt_id,
                causal_anchor="anchor",
                operation="start",
            )
        )
        updated = self.repository.transition_attempt(
            attempt_id,
            expected_statuses=(AttemptLifecycleStatus.PREPARED,),
            update=AttemptUpdate(status=AttemptLifecycleStatus.RUNNING),
        )
        self.assertIsNotNone(updated)

    def test_atomic_commit_persists_revision_artifact_head_and_event(self) -> None:
        self._running_attempt()
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )

        self.repository.commit_revision(
            revision,
            artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )

        loaded = self.repository.require_revision(revision.identity)
        self.assertTrue(loaded.verify())
        self.assertEqual(
            revision.identity,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity,
        )
        self.assertEqual(
            "revision-1",
            self.repository.load_attempt(
                "attempt-1"
            ).latest_admitted_revision_id,
        )
        self.assertEqual(
            "semantic_revision_committed",
            self.repository.list_events()[-1]["event_kind"],
        )
        self.assertEqual((), self.repository.verify_integrity())

    def test_stale_compare_and_swap_rolls_back_artifact_and_revision(self) -> None:
        self._running_attempt("attempt-1")
        first, first_artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            first,
            first_artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )
        self._running_attempt("attempt-2")
        stale, stale_artifact = _revision_and_artifact(
            revision_id="revision-stale",
            artifact_id="transition-stale",
            state=_state("stale"),
            parents=("revision-1",),
        )

        with self.assertRaises(StaleAnchorError):
            self.repository.commit_revision(
                stale,
                stale_artifact,
                expected_head_revision_id="not-the-head",
                attempt_id="attempt-2",
            )

        self.assertIsNone(self.repository.load_revision("revision-stale"))
        self.assertIsNone(
            self.repository.load_transition_artifact("transition-stale")
        )
        self.assertEqual(
            "revision-1",
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )

    def test_interrupted_attempt_cannot_commit_or_move_branch_head(self) -> None:
        self._running_attempt()
        request_attempt_interruption(
            self.repository,
            InterruptionRequest(
                attempt_id="attempt-1",
                requesting_principal="operator",
                reason="stop",
            ),
        )
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )

        with self.assertRaises(AttemptNotRunningError):
            self.repository.commit_revision(
                revision,
                artifact,
                expected_head_revision_id=None,
                attempt_id="attempt-1",
            )

        self.assertIsNone(
            self.repository.load_branch_head("scope-1", "objective-1", "main")
        )
        self.assertIsNone(self.repository.load_revision("revision-1"))

    def test_attempt_recovery_does_not_create_a_semantic_revision(self) -> None:
        self._running_attempt()

        recovered = self.repository.recover_running_attempts(
            reason="worker disappeared"
        )

        self.assertEqual(1, len(recovered))
        self.assertEqual(
            AttemptLifecycleStatus.OPERATIONALLY_FAILED,
            recovered[0].status,
        )
        self.assertIsNone(
            self.repository.load_branch_head("scope-1", "objective-1", "main")
        )

    def test_parent_and_child_traversal_preserve_branch_history(self) -> None:
        self._running_attempt("attempt-1")
        first, first_artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            first,
            first_artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )
        self._running_attempt("attempt-2")
        second, second_artifact = _revision_and_artifact(
            revision_id="revision-2",
            artifact_id="transition-2",
            state=_state("two"),
            parents=("revision-1",),
        )
        self.repository.commit_revision(
            second,
            second_artifact,
            expected_head_revision_id="revision-1",
            attempt_id="attempt-2",
        )

        self.assertEqual(
            ("revision-1",),
            self.repository.parent_revision_ids("revision-2"),
        )
        self.assertEqual(
            ("revision-2",),
            self.repository.child_revision_ids("revision-1"),
        )
        self.assertEqual(
            ("revision-2", "revision-1"),
            self.repository.path_to_roots("revision-2"),
        )

    def test_complete_event_loss_does_not_lose_authoritative_state(self) -> None:
        self._running_attempt()
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            revision,
            artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )

        with sqlite3.connect(self.repository.path) as connection:
            connection.execute("DELETE FROM resumption_events")
            connection.commit()
        reopened = SQLiteResumptionRepository(self.repository.path)

        self.assertEqual((), reopened.list_events())
        self.assertEqual(
            revision.identity,
            reopened.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity,
        )
        self.assertEqual((), reopened.verify_integrity())

    def test_derived_indexes_rebuild_without_semantic_loss(self) -> None:
        self._running_attempt()
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            revision,
            artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )
        before = self.repository.require_revision(revision.identity)

        rebuilt = self.repository.rebuild_derived_indexes()
        after = self.repository.require_revision(revision.identity)

        self.assertEqual(
            {
                "idx_resumption_revisions_identity",
                "idx_resumption_parents_parent",
                "idx_resumption_attempts_status",
            },
            set(rebuilt),
        )
        self.assertEqual(before, after)
        self.assertEqual((), self.repository.verify_integrity())

    def test_replay_reproduces_the_decision_flow_signature(self) -> None:
        self._running_attempt()
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            revision,
            artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )

        replay = self.repository.verify_transition_replay("transition-1")

        self.assertTrue(replay["verified"])
        self.assertEqual(
            replay["stored_decision_flow_signature"],
            replay["reproduced_decision_flow_signature"],
        )
        self.assertEqual(
            "deterministic_externalized_flow",
            replay["replay_mode"],
        )

    def test_replay_detects_tampered_externalized_flow(self) -> None:
        self._running_attempt()
        revision, artifact = _revision_and_artifact(
            revision_id="revision-1",
            artifact_id="transition-1",
            state=_state("one"),
        )
        self.repository.commit_revision(
            revision,
            artifact,
            expected_head_revision_id=None,
            attempt_id="attempt-1",
        )
        payload = self.repository.load_transition_artifact("transition-1")
        payload["semantic_outcome"] = SemanticOutcome.FAILED.value
        with sqlite3.connect(self.repository.path) as connection:
            connection.execute(
                """
                UPDATE resumption_transition_artifacts
                SET payload_json = ? WHERE artifact_id = ?
                """,
                (canonical_json(payload), "transition-1"),
            )
            connection.commit()

        replay = self.repository.verify_transition_replay("transition-1")

        self.assertFalse(replay["verified"])
        self.assertIn(
            "decision-flow signature could not be reproduced",
            replay["failures"],
        )


if __name__ == "__main__":
    unittest.main()
