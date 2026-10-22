from __future__ import annotations

import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from typing import Any

from realized_core_runtime import (
    AttemptExecutionOutcome,
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptUpdate,
    InterruptionDisposition,
    InterruptionRequest,
)

from realized_core_engine.resumption_contracts import (
    AdmissionDecision,
    AdmissionDisposition,
    ContinuationInlet,
    GoverningDirection,
    HoldOn,
    IdentityDisposition,
    IdentityDispositionKind,
    InletRelationship,
    InspectionRequest,
    InspectionTargetKind,
    InspectionView,
    OperationKind,
    Realignment,
    Reversal,
    ReductionContext,
    ReductionProposal,
    ResumptionIdentity,
    ResumptionRequest,
    SemanticDelta,
    SemanticItem,
    SemanticOutcome,
    StartRequest,
    Supersession,
    canonical_json,
)
from realized_core_engine.resumption_repository import SQLiteResumptionRepository
from realized_core_engine.resumption_service import ResumptionService


class SequenceIds:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def __call__(self, prefix: str) -> str:
        self.counts[prefix] = self.counts.get(prefix, 0) + 1
        return f"{prefix}-{self.counts[prefix]}"


class ProposalController:
    def __init__(self, proposal: ReductionProposal) -> None:
        self.proposal = proposal
        self.contexts: list[ReductionContext] = []

    def reduce(self, context: ReductionContext, *, should_stop: Any) -> ReductionProposal:
        self.contexts.append(context)
        return self.proposal


def item(
    item_id: str,
    text: str,
    *,
    kind: str = "fact",
    evidence: tuple[str, ...] = (),
) -> SemanticItem:
    return SemanticItem(
        item_id=item_id,
        kind=kind,
        payload={"text": text},
        evidence_references=evidence,
    )


def inlet(
    inlet_id: str,
    relationship: InletRelationship,
    *,
    delta: SemanticDelta = SemanticDelta(),
    payload: dict[str, Any] | None = None,
    target: str = "root",
    correlation: dict[str, Any] | None = None,
    realignment: Realignment | None = None,
    reversal: Reversal | None = None,
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
        reversal=reversal,
    )


class ResumptionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.database = Path(self.temporary.name) / "resumption.sqlite3"
        self.ids = SequenceIds()
        self.repository = SQLiteResumptionRepository(
            self.database,
            clock=lambda: "2026-01-01T00:00:00+00:00",
        )
        self.service = ResumptionService(
            self.repository,
            id_factory=self.ids,
            clock=lambda: "2026-01-01T00:00:00+00:00",
        )

    def _start(
        self,
        *,
        achieved: tuple[SemanticItem, ...] = (),
        non_achievedness: tuple[SemanticItem, ...] = (),
        holds: tuple[HoldOn, ...] = (),
        payload: dict[str, Any] | None = None,
    ) -> tuple[Any, Any]:
        result = self.service.start(
            StartRequest(
                scope_id="scope-1",
                objective_id="objective-1",
                branch_id="main",
                initial_inlet=inlet(
                    "inlet-start",
                    InletRelationship.CONTINUATION,
                    delta=SemanticDelta(
                        achieved=achieved,
                        non_achievedness=non_achievedness,
                        holds=holds,
                    ),
                    payload=payload,
                ),
                governing_direction=GoverningDirection(
                    objective="Produce a governed result",
                    scope="scope-1",
                    required_outcome="verified result",
                ),
                execution_policy={"llm_policy": "off"},
            )
        )
        self.assertIsNotNone(result.resulting_revision_identity)
        revision = self.repository.require_revision(
            result.resulting_revision_identity
        )
        return result, revision

    def _request(
        self,
        revision: Any,
        operation: OperationKind,
        contribution: ContinuationInlet | None = None,
        **kwargs: Any,
    ) -> ResumptionRequest:
        return ResumptionRequest(
            anchor=revision.identity,
            operation=operation,
            expected_branch_head_revision_id=revision.identity.revision_id,
            inlet=contribution,
            execution_policy={"llm_policy": "off"},
            **kwargs,
        )

    def test_start_is_reconstructable_after_service_and_provider_replacement(self) -> None:
        result, revision = self._start(
            non_achievedness=(item("not-1", "Need an answer", kind="not"),),
            payload={
                "scope_imports": [
                    {"source_id": "subject-7", "version": "sha256:abc"}
                ]
            },
        )

        replacement = ResumptionService(
            SQLiteResumptionRepository(self.database),
        )
        inspected = replacement.inspect(
            InspectionRequest(
                target_kind=InspectionTargetKind.REVISION,
                target_id=revision.identity.revision_id,
                view=InspectionView.RECONSTRUCTION,
            )
        )

        self.assertEqual(AttemptExecutionOutcome.TERMINATED, result.execution_outcome)
        self.assertEqual(SemanticOutcome.INCOMPLETE, result.semantic_outcome)
        self.assertEqual(
            "subject-7",
            inspected.payload["revision"]["state"]["scope_imports"][0][
                "source_id"
            ],
        )
        self.assertTrue(
            self.repository.require_revision(revision.identity).verify()
        )
        continued = replacement.resume(
            ResumptionRequest(
                anchor=revision.identity,
                operation=OperationKind.AUGMENT,
                expected_branch_head_revision_id=revision.identity.revision_id,
                inlet=inlet(
                    "scope-import-continuation",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(
                        achieved=(item("fact-1", "Result"),)
                    ),
                ),
                execution_policy={"llm_policy": "off"},
            )
        )
        continued_revision = self.repository.require_revision(
            continued.resulting_revision_identity
        )
        self.assertEqual(
            ({"source_id": "subject-7", "version": "sha256:abc"},),
            continued_revision.state.scope_imports,
        )

    def test_start_admits_the_inlet_before_invoking_the_controller(self) -> None:
        controller = ProposalController(ReductionProposal())
        rejected_service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            admission_evaluator=lambda *args: AdmissionDecision(
                disposition=AdmissionDisposition.REJECTED,
                rationale="policy rejected the inlet",
            ),
            id_factory=self.ids,
        )

        result = rejected_service.start(
            StartRequest(
                scope_id="scope-1",
                objective_id="objective-1",
                branch_id="main",
                initial_inlet=inlet(
                    "rejected-start",
                    InletRelationship.CONTINUATION,
                ),
                governing_direction=GoverningDirection(
                    objective="Rejected objective",
                    scope="scope-1",
                ),
            )
        )

        self.assertEqual(SemanticOutcome.REJECTED, result.semantic_outcome)
        self.assertEqual([], controller.contexts)

    def test_presentation_and_transcript_wording_do_not_mutate_state(self) -> None:
        _, revision = self._start(
            achieved=(item("fact-1", "Stable fact"),),
        )
        controller = ProposalController(
            ReductionProposal(presentation={"text": "Different wording"})
        )
        service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            id_factory=self.ids,
        )

        result = service.resume(
            self._request(
                revision,
                OperationKind.CONTINUE,
                inlet(
                    "inlet-wording",
                    InletRelationship.CONTINUATION,
                    payload={"transcript_text": "A rephrased conversation turn"},
                ),
            )
        )

        self.assertIsNone(result.resulting_revision_identity)
        self.assertEqual(
            revision.identity.revision_id,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )
        self.assertEqual({"text": "Different wording"}, result.presentation)

    def test_unresolved_state_survives_a_completed_conversation_turn(self) -> None:
        _, revision = self._start(
            non_achievedness=(item("not-1", "Still unresolved", kind="not"),)
        )
        service = ResumptionService(
            self.repository,
            reduction_controller=ProposalController(
                ReductionProposal(presentation={"text": "A useful reply"})
            ),
            id_factory=self.ids,
        )

        result = service.resume(
            self._request(
                revision,
                OperationKind.CONTINUE,
                inlet("turn-2", InletRelationship.CONTINUATION),
            )
        )

        self.assertEqual(SemanticOutcome.INCOMPLETE, result.semantic_outcome)
        self.assertEqual(("not-1",), result.non_achievedness_summary)

    def test_explicit_correction_supersedes_without_erasing_provenance(self) -> None:
        _, revision = self._start(
            achieved=(item("fact-old", "Old value"),)
        )
        correction = Supersession(
            target_item_id="fact-old",
            replacement=item("fact-new", "Corrected value"),
            evidence_references=("evidence-1",),
            rationale="verified correction",
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.CORRECT,
                inlet(
                    "correction-1",
                    InletRelationship.CORRECTION,
                    delta=SemanticDelta(supersessions=(correction,)),
                ),
            )
        )
        updated = self.repository.require_revision(
            result.resulting_revision_identity
        )

        self.assertEqual(("fact-new",), result.achieved_state_summary)
        self.assertEqual(
            "fact-old",
            updated.state.supersession_edges[-1]["prior_item_id"],
        )
        self.assertEqual(
            revision.identity.revision_id,
            updated.parent_revision_ids[0],
        )

    def test_ambiguous_correction_does_not_guess_a_target(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Value"),))

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.CORRECT,
                inlet(
                    "correction-missing",
                    InletRelationship.CORRECTION,
                    delta=SemanticDelta(
                        supersessions=(
                            Supersession(
                                target_item_id="similar-but-not-identical",
                                replacement=item("fact-2", "Replacement"),
                                evidence_references=("evidence-2",),
                                rationale="candidate",
                            ),
                        )
                    ),
                ),
            )
        )

        self.assertEqual(SemanticOutcome.AMBIGUOUS, result.semantic_outcome)
        self.assertIsNone(result.resulting_revision_identity)
        self.assertEqual(
            revision.identity.revision_id,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )

    def test_augmentation_cannot_silently_supersede_existing_state(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Value"),))

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.AUGMENT,
                inlet(
                    "augmentation-1",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(
                        achieved=(item("fact-2", "Additional"),),
                        supersessions=(
                            Supersession(
                                target_item_id="fact-1",
                                replacement=None,
                                evidence_references=("evidence-1",),
                                rationale="withdraw",
                            ),
                        ),
                    ),
                ),
            )
        )

        self.assertEqual(SemanticOutcome.REJECTED, result.semantic_outcome)
        head = self.repository.load_branch_head(
            "scope-1", "objective-1", "main"
        )
        self.assertEqual(("fact-1",), tuple(x.item_id for x in head.state.achieved))

    def test_hold_correlation_reopens_only_the_addressed_continuation(self) -> None:
        hold_1 = self._hold("hold-1", "correlation-1")
        hold_2 = self._hold("hold-2", "correlation-2")
        _, revision = self._start(
            non_achievedness=(item("not-1", "Waiting", kind="not"),),
            holds=(hold_1, hold_2),
        )
        wrong = self.service.resume(
            self._request(
                revision,
                OperationKind.RESUME_SUSPENDED,
                inlet(
                    "wrong-signal",
                    InletRelationship.HOLD_SATISFACTION,
                    target="hold-1",
                    payload={"hold_id": "hold-1", "answer": "ready"},
                    correlation={"token": "wrong"},
                ),
            )
        )
        self.assertEqual(SemanticOutcome.REJECTED, wrong.semantic_outcome)

        correct = self.service.resume(
            self._request(
                revision,
                OperationKind.RESUME_SUSPENDED,
                inlet(
                    "right-signal",
                    InletRelationship.HOLD_SATISFACTION,
                    target="hold-1",
                    payload={"hold_id": "hold-1", "answer": "ready"},
                    correlation={"token": "correlation-1"},
                ),
            )
        )
        updated = self.repository.require_revision(
            correct.resulting_revision_identity
        )

        self.assertEqual(("hold-2",), correct.active_hold_summary)
        self.assertEqual("resume", updated.state.hold_evaluations[-1]["disposition"])

    def test_hold_expiry_is_a_durable_semantic_disposition(self) -> None:
        hold = self._hold("hold-1", "correlation-1")
        _, revision = self._start(
            non_achievedness=(item("not-1", "Waiting", kind="not"),),
            holds=(hold,),
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.RESUME_SUSPENDED,
                inlet(
                    "expiry",
                    InletRelationship.HOLD_SATISFACTION,
                    target="hold-1",
                    payload={
                        "hold_id": "hold-1",
                        "expired": True,
                        "hold_disposition": "expire",
                    },
                    correlation={"token": "correlation-1"},
                ),
            )
        )
        updated = self.repository.require_revision(
            result.resulting_revision_identity
        )

        self.assertEqual(SemanticOutcome.EXPIRED, result.semantic_outcome)
        self.assertEqual((), result.active_hold_summary)
        self.assertEqual("expire", updated.state.hold_evaluations[-1]["disposition"])

    def test_all_non_resume_hold_dispositions_are_durable(self) -> None:
        holds = tuple(
            self._hold(f"hold-{index}", f"correlation-{index}")
            for index in range(1, 5)
        )
        _, current = self._start(
            non_achievedness=(item("not-1", "Waiting", kind="not"),),
            holds=holds,
        )
        cases = (
            ("hold-1", "remain_held", {}, SemanticOutcome.PAUSED, True),
            (
                "hold-2",
                "fail",
                {"failed": True},
                SemanticOutcome.FAILED,
                False,
            ),
            (
                "hold-3",
                "escalate",
                {"escalation_target": "operator"},
                SemanticOutcome.INCOMPLETE,
                False,
            ),
            (
                "hold-4",
                "reframe",
                {"reframe": "await a different signal"},
                SemanticOutcome.INCOMPLETE,
                False,
            ),
        )

        for hold_id, disposition, extra, expected, remains in cases:
            with self.subTest(disposition=disposition):
                result = self.service.resume(
                    self._request(
                        current,
                        OperationKind.RESUME_SUSPENDED,
                        inlet(
                            f"signal-{disposition}",
                            InletRelationship.HOLD_SATISFACTION,
                            target=hold_id,
                            payload={
                                "hold_id": hold_id,
                                "hold_disposition": disposition,
                                **extra,
                            },
                            correlation={
                                "token": hold_id.replace(
                                    "hold", "correlation"
                                )
                            },
                        ),
                    )
                )
                current = self.repository.require_revision(
                    result.resulting_revision_identity
                )
                self.assertEqual(expected, result.semantic_outcome)
                self.assertEqual(
                    remains,
                    hold_id in result.active_hold_summary,
                )
                self.assertEqual(
                    disposition,
                    current.state.hold_evaluations[-1]["disposition"],
                )

    def test_interruption_leaves_branch_state_direction_and_holds_unchanged(self) -> None:
        hold = self._hold("hold-1", "correlation-1")
        _, revision = self._start(
            achieved=(item("fact-1", "Value"),),
            holds=(hold,),
        )
        self.repository.prepare_attempt(
            AttemptRecord(
                attempt_id="external-attempt",
                causal_anchor=revision.identity.causal_anchor,
                operation=OperationKind.CONTINUE.value,
                latest_admitted_revision_id=revision.identity.revision_id,
            )
        )
        self.repository.transition_attempt(
            "external-attempt",
            expected_statuses=(AttemptLifecycleStatus.PREPARED,),
            update=AttemptUpdate(status=AttemptLifecycleStatus.RUNNING),
        )

        interruption = self.service.interrupt(
            InterruptionRequest(
                attempt_id="external-attempt",
                requesting_principal="tester",
                reason="operator stop",
            )
        )
        head = self.repository.load_branch_head(
            "scope-1", "objective-1", "main"
        )

        self.assertFalse(interruption.semantic_revision_created)
        self.assertEqual(revision.identity, head.identity)
        self.assertEqual(revision.state.digest, head.state.digest)
        self.assertEqual(("hold-1",), tuple(x.hold_id for x in head.state.holds))

    def test_resume_after_interruption_uses_latest_admitted_revision(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Value"),))
        self.repository.prepare_attempt(
            AttemptRecord(
                attempt_id="interrupted-attempt",
                causal_anchor=revision.identity.causal_anchor,
                operation=OperationKind.CONTINUE.value,
                latest_admitted_revision_id=revision.identity.revision_id,
            )
        )
        self.repository.transition_attempt(
            "interrupted-attempt",
            expected_statuses=(AttemptLifecycleStatus.PREPARED,),
            update=AttemptUpdate(status=AttemptLifecycleStatus.INTERRUPTED),
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.RESUME_AFTER_INTERRUPTION,
                source_attempt_id="interrupted-attempt",
            )
        )

        self.assertEqual(AttemptExecutionOutcome.TERMINATED, result.execution_outcome)
        self.assertIsNone(result.resulting_revision_identity)
        self.assertEqual(
            revision.identity.revision_id,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )

    def test_interrupted_proposals_are_not_active_resumption_context(self) -> None:
        _, revision = self._start(
            non_achievedness=(item("not-1", "Need answer", kind="not"),)
        )
        self.repository.prepare_attempt(
            AttemptRecord(
                attempt_id="interrupted-with-proposal",
                causal_anchor=revision.identity.causal_anchor,
                operation=OperationKind.CONTINUE.value,
                latest_admitted_revision_id=revision.identity.revision_id,
                proposal_references=("proposal:unfinished",),
            )
        )
        self.repository.transition_attempt(
            "interrupted-with-proposal",
            expected_statuses=(AttemptLifecycleStatus.PREPARED,),
            update=AttemptUpdate(status=AttemptLifecycleStatus.INTERRUPTED),
        )
        controller = ProposalController(ReductionProposal())
        service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            id_factory=self.ids,
        )

        service.resume(
            self._request(
                revision,
                OperationKind.RESUME_AFTER_INTERRUPTION,
                source_attempt_id="interrupted-with-proposal",
            )
        )

        self.assertEqual(1, len(controller.contexts))
        projection = controller.contexts[0].projection
        self.assertIsNotNone(projection)
        self.assertNotIn(
            "proposal:unfinished",
            canonical_json(projection.canonical_content()),
        )

    def test_redirection_realigns_every_affected_item_and_clears_old_frontier(self) -> None:
        retained = item("fact-1", "Still applies", evidence=("evidence-1",))
        unresolved = item("not-1", "Former question", kind="not")
        _, revision = self._start(
            achieved=(retained,),
            non_achievedness=(unresolved,),
            payload={"engine_state": {"frontier": ["old-frontier"]}},
        )
        introduced = item("fact-2", "New direction fact", evidence=("evidence-2",))
        unresolved_after = item(
            "not-1",
            "Applicability under the new direction is unresolved",
            kind="unresolved_applicability",
        )
        direction = GoverningDirection(
            objective="Produce a redirected governed result",
            scope="scope-1",
            constraints=("new-constraint",),
            required_outcome="redirected result",
        )
        realignment = Realignment(
            source_revision_id=revision.identity.revision_id,
            redirection_inlet_id="redirect-1",
            affected_item_ids=("fact-1", "not-1"),
            identity_disposition=IdentityDisposition(
                kind=IdentityDispositionKind.SAME_OBJECTIVE,
                target_scope_id="scope-1",
                target_objective_id="objective-1",
                target_branch_id="main",
                rationale="direction changes without constitutive identity change",
            ),
            retained_item_ids=("fact-1",),
            superseded_item_ids=(),
            introduced_items=(introduced,),
            unresolved_applicability_item_ids=("not-1",),
            resulting_non_achievedness=(unresolved_after,),
            evidence_references=("realignment-evidence",),
            governance_references=("policy-redirect",),
            completeness_statement="Every affected item was classified.",
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.REDIRECT_AND_REALIGN,
                inlet(
                    "redirect-1",
                    InletRelationship.REDIRECTION,
                    delta=SemanticDelta(
                        achieved=(introduced,),
                        governing_direction=direction,
                    ),
                    realignment=realignment,
                ),
            )
        )
        updated = self.repository.require_revision(
            result.resulting_revision_identity
        )

        self.assertEqual(direction, updated.state.governing_direction)
        self.assertEqual({}, updated.state.engine_state)
        self.assertEqual(("not-1",), updated.state.unresolved_applicability_item_ids)
        self.assertEqual(
            {"fact-1", "fact-2"},
            {value.item_id for value in updated.state.achieved},
        )
        self.assertIsNotNone(result.realignment_summary)

    def test_pre_redirection_attempt_cannot_commit_over_realigned_head(self) -> None:
        retained = item("fact-1", "Still applies", evidence=("evidence-1",))
        _, source = self._start(achieved=(retained,))

        class BlockingController:
            def __init__(self) -> None:
                self.entered = threading.Event()
                self.release = threading.Event()

            def reduce(
                self,
                context: ReductionContext,
                *,
                should_stop: Any,
            ) -> ReductionProposal:
                self.entered.set()
                if not self.release.wait(timeout=5):
                    raise TimeoutError("test did not release the old reduction")
                return ReductionProposal()

        controller = BlockingController()
        old_service = ResumptionService(
            self.repository,
            reduction_controller=controller,
        )
        old_results: list[Any] = []
        old_errors: list[BaseException] = []

        def run_old_continuation() -> None:
            try:
                old_results.append(
                    old_service.resume(
                        self._request(
                            source,
                            OperationKind.AUGMENT,
                            inlet(
                                "late-augmentation",
                                InletRelationship.AUGMENTATION,
                                delta=SemanticDelta(
                                    achieved=(item("fact-late", "Late"),)
                                ),
                            ),
                        )
                    )
                )
            except BaseException as exc:
                old_errors.append(exc)

        worker = threading.Thread(target=run_old_continuation)
        worker.start()
        self.assertTrue(controller.entered.wait(timeout=5))

        direction = replace(
            source.state.governing_direction,
            objective="Redirected direction",
        )
        realignment = Realignment(
            source_revision_id=source.identity.revision_id,
            redirection_inlet_id="redirect-during-reduction",
            affected_item_ids=("fact-1",),
            identity_disposition=IdentityDisposition(
                kind=IdentityDispositionKind.SAME_OBJECTIVE,
                target_scope_id="scope-1",
                target_objective_id="objective-1",
                target_branch_id="main",
                rationale="same objective with an explicit new direction",
            ),
            retained_item_ids=("fact-1",),
            superseded_item_ids=(),
            introduced_items=(),
            unresolved_applicability_item_ids=(),
            resulting_non_achievedness=(),
            evidence_references=("evidence:redirection",),
            governance_references=("policy:realignment",),
            completeness_statement="All affected material was classified.",
        )
        redirected_result = self.service.resume(
            self._request(
                source,
                OperationKind.REDIRECT_AND_REALIGN,
                inlet(
                    "redirect-during-reduction",
                    InletRelationship.REDIRECTION,
                    delta=SemanticDelta(governing_direction=direction),
                    realignment=realignment,
                ),
            )
        )
        redirected = self.repository.require_revision(
            redirected_result.resulting_revision_identity
        )
        controller.release.set()
        worker.join(timeout=5)

        self.assertFalse(worker.is_alive())
        self.assertEqual([], old_errors)
        self.assertEqual(1, len(old_results))
        self.assertEqual(SemanticOutcome.STALE, old_results[0].semantic_outcome)
        self.assertIsNone(old_results[0].resulting_revision_identity)
        self.assertEqual(
            redirected.identity,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity,
        )
        self.assertNotIn(
            "fact-late",
            {item.item_id for item in redirected.state.achieved},
        )

    def test_incomplete_realignment_is_rejected_without_moving_head(self) -> None:
        _, revision = self._start(
            achieved=(item("fact-1", "Value", evidence=("evidence-1",)),),
        )
        direction = replace(
            revision.state.governing_direction,
            objective="Changed direction",
        )
        incomplete = Realignment(
            source_revision_id=revision.identity.revision_id,
            redirection_inlet_id="redirect-bad",
            affected_item_ids=("fact-1",),
            identity_disposition=IdentityDisposition(
                kind=IdentityDispositionKind.SAME_OBJECTIVE,
                target_scope_id="scope-1",
                target_objective_id="objective-1",
                target_branch_id="main",
                rationale="same identity",
            ),
            retained_item_ids=(),
            superseded_item_ids=(),
            introduced_items=(),
            unresolved_applicability_item_ids=(),
            resulting_non_achievedness=(),
            evidence_references=(),
            governance_references=(),
            completeness_statement="incomplete",
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.REDIRECT_AND_REALIGN,
                inlet(
                    "redirect-bad",
                    InletRelationship.REDIRECTION,
                    delta=SemanticDelta(governing_direction=direction),
                    realignment=incomplete,
                ),
            )
        )

        self.assertEqual(SemanticOutcome.REJECTED, result.semantic_outcome)
        self.assertEqual(
            revision.identity.revision_id,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )

    def test_retained_and_superseded_realignment_require_support(self) -> None:
        for disposition in ("retained", "superseded"):
            with self.subTest(disposition=disposition):
                database = Path(self.temporary.name) / f"{disposition}.sqlite3"
                repository = SQLiteResumptionRepository(database)
                service = ResumptionService(repository)
                started = service.start(
                    StartRequest(
                        scope_id="scope-1",
                        objective_id="objective-1",
                        branch_id="main",
                        initial_inlet=inlet(
                            f"start-{disposition}",
                            InletRelationship.CONTINUATION,
                            delta=SemanticDelta(
                                achieved=(item("fact-1", "Unsupported"),)
                            ),
                        ),
                        governing_direction=GoverningDirection(
                            objective="Original direction",
                            scope="scope-1",
                        ),
                    )
                )
                source = repository.require_revision(
                    started.resulting_revision_identity
                )
                direction = replace(
                    source.state.governing_direction,
                    objective="Redirected direction",
                )
                realignment = Realignment(
                    source_revision_id=source.identity.revision_id,
                    redirection_inlet_id=f"redirect-{disposition}",
                    affected_item_ids=("fact-1",),
                    identity_disposition=IdentityDisposition(
                        kind=IdentityDispositionKind.SAME_OBJECTIVE,
                        target_scope_id="scope-1",
                        target_objective_id="objective-1",
                        target_branch_id="main",
                        rationale="same identity",
                    ),
                    retained_item_ids=(
                        ("fact-1",) if disposition == "retained" else ()
                    ),
                    superseded_item_ids=(
                        ("fact-1",) if disposition == "superseded" else ()
                    ),
                    introduced_items=(),
                    unresolved_applicability_item_ids=(),
                    resulting_non_achievedness=(),
                    evidence_references=(),
                    governance_references=("policy:realignment",),
                    completeness_statement="The affected item was classified.",
                )

                result = service.resume(
                    ResumptionRequest(
                        anchor=source.identity,
                        operation=OperationKind.REDIRECT_AND_REALIGN,
                        expected_branch_head_revision_id=(
                            source.identity.revision_id
                        ),
                        inlet=inlet(
                            f"redirect-{disposition}",
                            InletRelationship.REDIRECTION,
                            delta=SemanticDelta(governing_direction=direction),
                            realignment=realignment,
                        ),
                    )
                )

                self.assertEqual(
                    SemanticOutcome.REJECTED,
                    result.semantic_outcome,
                )
                self.assertEqual(
                    source.identity,
                    repository.load_branch_head(
                        "scope-1", "objective-1", "main"
                    ).identity,
                )

    def test_constitutive_redirection_uses_a_new_derived_objective_identity(self) -> None:
        _, revision = self._start(
            achieved=(item("fact-1", "Source", evidence=("evidence-1",)),)
        )
        introduced = item("fact-2", "Derived", evidence=("evidence-2",))
        direction = GoverningDirection(
            objective="A different constitutive objective",
            scope="scope-2",
        )
        realignment = Realignment(
            source_revision_id=revision.identity.revision_id,
            redirection_inlet_id="derive-1",
            affected_item_ids=("fact-1",),
            identity_disposition=IdentityDisposition(
                kind=IdentityDispositionKind.DERIVED_OBJECTIVE,
                target_scope_id="scope-2",
                target_objective_id="objective-2",
                target_branch_id="main",
                rationale="constitutive objective and scope changed",
            ),
            retained_item_ids=("fact-1",),
            superseded_item_ids=(),
            introduced_items=(introduced,),
            unresolved_applicability_item_ids=(),
            resulting_non_achievedness=(),
            evidence_references=("realignment-evidence",),
            governance_references=("policy-derive",),
            completeness_statement="All affected source material was classified.",
        )

        result = self.service.resume(
            self._request(
                revision,
                OperationKind.REDIRECT_AND_REALIGN,
                inlet(
                    "derive-1",
                    InletRelationship.REDIRECTION,
                    delta=SemanticDelta(
                        achieved=(introduced,),
                        governing_direction=direction,
                    ),
                    realignment=realignment,
                ),
            )
        )

        self.assertEqual("scope-2", result.resulting_revision_identity.scope_id)
        self.assertEqual(
            "objective-2", result.resulting_revision_identity.objective_id
        )
        derived = self.repository.require_revision(
            result.resulting_revision_identity
        )
        self.assertEqual((revision.identity.revision_id,), derived.parent_revision_ids)

    def test_derive_carries_only_explicitly_selected_admitted_material(self) -> None:
        selected = item("fact-selected", "Selected source fact")
        ambient = item("fact-ambient", "Unselected ambient fact")
        _, source = self._start(achieved=(selected, ambient))
        direction = GoverningDirection(
            objective="Produce a derived result",
            scope="scope-derived",
        )

        result = self.service.resume(
            self._request(
                source,
                OperationKind.DERIVE,
                inlet(
                    "derive-explicit",
                    InletRelationship.CONTINUATION,
                    payload={
                        "target_scope_id": "scope-derived",
                        "target_objective_id": "objective-derived",
                        "target_branch_id": "main",
                        "selected_item_ids": [selected.item_id],
                    },
                    delta=SemanticDelta(governing_direction=direction),
                ),
            )
        )
        derived = self.repository.require_revision(
            result.resulting_revision_identity
        )

        self.assertEqual("scope-derived", derived.identity.scope_id)
        self.assertEqual("objective-derived", derived.identity.objective_id)
        self.assertEqual(
            (selected.item_id,),
            tuple(item.item_id for item in derived.state.achieved),
        )
        self.assertEqual({}, derived.state.engine_state)
        self.assertIn(
            self.repository.revision_reference(source.identity.revision_id),
            derived.state.provenance_references,
        )

    def test_concurrent_children_are_explicit_branches_and_can_merge(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Base"),))
        branch_a = self.service.resume(
            self._request(
                revision,
                OperationKind.BRANCH,
                inlet(
                    "branch-a",
                    InletRelationship.CONTINUATION,
                    payload={"target_branch_id": "branch-a"},
                    delta=SemanticDelta(achieved=(item("fact-a", "A"),)),
                ),
            )
        )
        branch_b = self.service.resume(
            self._request(
                revision,
                OperationKind.BRANCH,
                inlet(
                    "branch-b",
                    InletRelationship.CONTINUATION,
                    payload={"target_branch_id": "branch-b"},
                    delta=SemanticDelta(achieved=(item("fact-b", "B"),)),
                ),
            )
        )
        revision_a = self.repository.require_revision(
            branch_a.resulting_revision_identity
        )

        merged = self.service.resume(
            ResumptionRequest(
                anchor=revision_a.identity,
                operation=OperationKind.MERGE,
                expected_branch_head_revision_id=revision_a.identity.revision_id,
                merge_parent_identities=(branch_b.resulting_revision_identity,),
                execution_policy={"llm_policy": "off"},
            )
        )
        merged_revision = self.repository.require_revision(
            merged.resulting_revision_identity
        )

        self.assertEqual(
            {revision_a.identity.revision_id, branch_b.resulting_revision_identity.revision_id},
            set(merged_revision.parent_revision_ids),
        )
        self.assertEqual(
            {"fact-1", "fact-a", "fact-b"},
            {value.item_id for value in merged_revision.state.achieved},
        )

    def test_merge_preserves_parents_and_represents_conflicts_explicitly(
        self,
    ) -> None:
        _, revision = self._start()
        branch_a = self.service.resume(
            self._request(
                revision,
                OperationKind.BRANCH,
                inlet(
                    "branch-conflict-a",
                    InletRelationship.CONTINUATION,
                    payload={"target_branch_id": "branch-conflict-a"},
                    delta=SemanticDelta(
                        achieved=(item("fact-shared", "Value A"),)
                    ),
                ),
            )
        )
        branch_b = self.service.resume(
            self._request(
                revision,
                OperationKind.BRANCH,
                inlet(
                    "branch-conflict-b",
                    InletRelationship.CONTINUATION,
                    payload={"target_branch_id": "branch-conflict-b"},
                    delta=SemanticDelta(
                        achieved=(item("fact-shared", "Value B"),)
                    ),
                ),
            )
        )
        revision_a = self.repository.require_revision(
            branch_a.resulting_revision_identity
        )

        merged = self.service.resume(
            ResumptionRequest(
                anchor=revision_a.identity,
                operation=OperationKind.MERGE,
                expected_branch_head_revision_id=(
                    revision_a.identity.revision_id
                ),
                merge_parent_identities=(
                    branch_b.resulting_revision_identity,
                ),
                execution_policy={"llm_policy": "off"},
            )
        )
        merged_revision = self.repository.require_revision(
            merged.resulting_revision_identity
        )
        conflict_items = [
            value
            for value in merged_revision.state.non_achievedness
            if value.kind == "merge_conflict"
        ]

        self.assertEqual(
            {
                revision_a.identity.revision_id,
                branch_b.resulting_revision_identity.revision_id,
            },
            set(merged_revision.parent_revision_ids),
        )
        self.assertEqual(1, len(conflict_items))
        self.assertEqual(
            "fact-shared",
            conflict_items[0].payload["item_id"],
        )
        self.assertIn(
            conflict_items[0].item_id,
            merged_revision.state.conflicts,
        )

    def test_llm_off_flow_preserves_identity_augmentation_interruption_and_realignment(
        self,
    ) -> None:
        _, started = self._start(
            achieved=(item("fact-1", "Base", evidence=("evidence-1",)),)
        )
        augmented_result = self.service.resume(
            self._request(
                started,
                OperationKind.AUGMENT,
                inlet(
                    "augment-off",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(
                        achieved=(
                            item(
                                "fact-2",
                                "Additional",
                                evidence=("evidence-2",),
                            ),
                        )
                    ),
                ),
            )
        )
        augmented = self.repository.require_revision(
            augmented_result.resulting_revision_identity
        )
        self.repository.prepare_attempt(
            AttemptRecord(
                attempt_id="attempt-interrupted-off",
                causal_anchor=augmented.identity.causal_anchor,
                operation=OperationKind.CONTINUE.value,
                execution_policy={"llm_policy": "off"},
                latest_admitted_revision_id=augmented.identity.revision_id,
            )
        )
        self.repository.transition_attempt(
            "attempt-interrupted-off",
            expected_statuses=(AttemptLifecycleStatus.PREPARED,),
            update=AttemptUpdate(status=AttemptLifecycleStatus.RUNNING),
        )
        interrupted = self.service.interrupt(
            InterruptionRequest(
                attempt_id="attempt-interrupted-off",
                requesting_principal="tester",
                reason="operator requested stop",
            )
        )
        resumed = self.service.resume(
            self._request(
                augmented,
                OperationKind.RESUME_AFTER_INTERRUPTION,
                source_attempt_id="attempt-interrupted-off",
            )
        )
        direction = GoverningDirection(
            objective="Produce redirected result",
            scope="scope-1",
            required_outcome="redirected result",
        )
        affected = tuple(
            item.item_id for item in augmented.state.achieved
        )
        realignment = Realignment(
            source_revision_id=augmented.identity.revision_id,
            redirection_inlet_id="redirect-off",
            affected_item_ids=affected,
            identity_disposition=IdentityDisposition(
                kind=IdentityDispositionKind.SAME_OBJECTIVE,
                target_scope_id="scope-1",
                target_objective_id="objective-1",
                target_branch_id="main",
                rationale="The governing direction changed within the objective.",
            ),
            retained_item_ids=affected,
            superseded_item_ids=(),
            introduced_items=(),
            unresolved_applicability_item_ids=(),
            resulting_non_achievedness=(),
            evidence_references=("evidence-1", "evidence-2"),
            governance_references=("policy:realignment",),
            completeness_statement="Every admitted item remains applicable.",
        )
        redirected_result = self.service.resume(
            self._request(
                augmented,
                OperationKind.REDIRECT_AND_REALIGN,
                inlet(
                    "redirect-off",
                    InletRelationship.REDIRECTION,
                    delta=SemanticDelta(governing_direction=direction),
                    realignment=realignment,
                ),
            )
        )
        redirected = self.repository.require_revision(
            redirected_result.resulting_revision_identity
        )

        self.assertEqual(
            InterruptionDisposition.ACCEPTED,
            interrupted.disposition,
        )
        self.assertIsNone(resumed.resulting_revision_identity)
        self.assertEqual(
            augmented.identity.revision_id,
            resumed.source_revision_identity.revision_id,
        )
        self.assertEqual(direction, redirected.state.governing_direction)
        self.assertEqual(set(affected), {
            value.item_id for value in redirected.state.achieved
        })
        self.assertEqual(
            {"llm_policy": "off"},
            self.repository.load_attempt(
                redirected_result.execution_attempt_id
            ).execution_policy,
        )

    def test_stale_anchor_and_similarity_cannot_bind_causal_identity(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Base"),))
        first = self.service.resume(
            self._request(
                revision,
                OperationKind.AUGMENT,
                inlet(
                    "augment-first",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(achieved=(item("fact-2", "Next"),)),
                ),
            )
        )
        stale = self.service.resume(
            self._request(
                revision,
                OperationKind.AUGMENT,
                inlet(
                    "augment-stale",
                    InletRelationship.AUGMENTATION,
                    payload={"similarity": 0.999},
                    delta=SemanticDelta(achieved=(item("fact-3", "Late"),)),
                ),
            )
        )
        wrong_identity = replace(
            revision.identity,
            objective_id="similar-objective",
        )
        mismatched = self.service.resume(
            ResumptionRequest(
                anchor=wrong_identity,
                operation=OperationKind.CONTINUE,
                expected_branch_head_revision_id=revision.identity.revision_id,
                inlet=inlet("similar", InletRelationship.CONTINUATION),
            )
        )

        self.assertIsNotNone(first.resulting_revision_identity)
        self.assertEqual(SemanticOutcome.STALE, stale.semantic_outcome)
        self.assertEqual(SemanticOutcome.REJECTED, mismatched.semantic_outcome)

    def test_revoked_or_missing_current_capability_is_not_restored(self) -> None:
        _, revision = self._start(achieved=(item("fact-1", "Base"),))
        revoked_request = replace(
            self._request(
                revision,
                OperationKind.AUGMENT,
                inlet(
                    "revoked",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(achieved=(item("fact-2", "No"),)),
                ),
            ),
            governance_policy={"revoked": True},
        )
        capability_request = replace(
            self._request(
                revision,
                OperationKind.AUGMENT,
                inlet(
                    "missing-capability",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(achieved=(item("fact-3", "No"),)),
                ),
            ),
            governance_policy={"required_capabilities": ["filesystem.read"]},
            execution_policy={"available_capabilities": []},
        )

        revoked = self.service.resume(revoked_request)
        missing = self.service.resume(capability_request)

        self.assertEqual(SemanticOutcome.REJECTED, revoked.semantic_outcome)
        self.assertEqual(SemanticOutcome.REJECTED, missing.semantic_outcome)
        self.assertEqual(
            revision.identity.revision_id,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity.revision_id,
        )

    def test_projection_is_bounded_by_references_without_silent_loss(self) -> None:
        _, revision = self._start(
            achieved=tuple(item(f"fact-{index}", str(index)) for index in range(3)),
            non_achievedness=tuple(
                item(f"not-{index}", str(index), kind="not")
                for index in range(3)
            ),
        )

        projection = self.service.project(
            revision,
            replace(
                self._request(
                    revision,
                    OperationKind.RESUME_AFTER_INTERRUPTION,
                    source_attempt_id="unused",
                ).projection_policy,
                max_inline_items=2,
            ),
        )

        self.assertTrue(projection.verify())
        self.assertEqual(2, len(projection.state.achieved) + len(projection.state.non_achievedness))
        self.assertEqual(5, len(projection.external_references))
        self.assertIn(
            "4 permitted items are represented",
            projection.completeness_statement,
        )

    def test_projection_cannot_bypass_bounds_or_permissions_via_engine_state(self) -> None:
        public = item("fact-public", "Visible")
        secret = item("fact-secret", "Withheld")
        _, revision = self._start(
            achieved=(public, secret),
            payload={"engine_state": {"secret": "must-not-be-inline"}},
        )

        projection = self.service.project(
            revision,
            replace(
                self._request(
                    revision,
                    OperationKind.CONTINUE,
                    inlet("continue", InletRelationship.CONTINUATION),
                ).projection_policy,
                permitted_item_ids=(public.item_id,),
            ),
        )
        serialized = canonical_json(projection.canonical_content())

        self.assertEqual({}, projection.state.engine_state)
        self.assertEqual((public.item_id,), tuple(
            item.item_id for item in projection.state.achieved
        ))
        self.assertNotIn(secret.item_id, serialized)
        self.assertNotIn("must-not-be-inline", serialized)
        self.assertTrue(
            any(
                reference.endswith("/restricted-items")
                for reference in projection.external_references
            )
        )
        self.assertTrue(
            any(
                reference.endswith("/engine-state")
                for reference in projection.external_references
            )
        )

    def test_recorded_proposals_and_decision_signature_support_replay(self) -> None:
        _, revision = self._start(
            non_achievedness=(item("not-1", "Need answer", kind="not"),)
        )
        controller = ProposalController(
            ReductionProposal(
                delta=SemanticDelta(
                    achieved=(item("fact-1", "Answer"),),
                    resolved_non_achievedness_ids=("not-1",),
                ),
                semantic_outcome=SemanticOutcome.COMPLETED,
                proposal_references=("llm-receipt-1",),
                proposal_interactions=(
                    {
                        "proposals": [{"id": "llm-receipt-1"}],
                        "llm_receipts": [
                            {
                                "request_digest": "request-1",
                                "response_digest": "response-1",
                            }
                        ],
                    },
                ),
            )
        )
        service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            id_factory=self.ids,
        )

        result = service.resume(
            self._request(
                revision,
                OperationKind.CONTINUE,
                inlet("continue-1", InletRelationship.CONTINUATION),
            )
        )
        attempt = self.repository.load_attempt(result.execution_attempt_id)
        artifact = self.repository.load_transition_artifact(
            attempt.transition_artifact_references[-1]
        )

        self.assertEqual(["llm-receipt-1"], artifact["proposal_references"])
        self.assertTrue(artifact["decision_flow_signature"])
        self.assertEqual(
            result.resulting_revision_identity.revision_id,
            artifact["resulting_revision_id"],
        )
        replay = self.repository.verify_transition_replay(
            artifact["artifact_id"]
        )
        self.assertTrue(replay["verified"])
        self.assertEqual(
            "recorded_proposal_interactions",
            replay["replay_mode"],
        )
        self.assertEqual(
            ["llm-receipt-1"],
            replay["proposal_interaction_references"],
        )

    def test_capability_and_effect_receipts_link_attempt_and_transition(self) -> None:
        _, revision = self._start(
            non_achievedness=(item("not-1", "Need answer", kind="not"),)
        )
        controller = ProposalController(
            ReductionProposal(
                delta=SemanticDelta(
                    achieved=(item("fact-1", "Answer"),),
                    resolved_non_achievedness_ids=("not-1",),
                ),
                capability_receipt_references=("capability-receipt-1",),
                effect_receipt_references=("effect-receipt-1",),
            )
        )
        service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            id_factory=self.ids,
        )

        result = service.resume(
            self._request(
                revision,
                OperationKind.CONTINUE,
                inlet("continue-with-effects", InletRelationship.CONTINUATION),
            )
        )
        attempt = self.repository.load_attempt(result.execution_attempt_id)
        artifact = self.repository.load_transition_artifact(
            attempt.transition_artifact_references[-1]
        )

        self.assertEqual(
            ("capability-receipt-1", "effect-receipt-1"),
            attempt.receipt_references,
        )
        self.assertEqual(
            ["capability-receipt-1"],
            artifact["capability_receipt_references"],
        )
        self.assertEqual(
            ["effect-receipt-1"],
            artifact["effect_receipt_references"],
        )
        self.assertEqual(
            revision.identity.revision_id,
            attempt.initial_branch_head_revision_id,
        )
        self.assertEqual(
            revision.revision_digest,
            attempt.initial_branch_head_digest,
        )

    def test_attempt_transition_and_revision_remain_distinct_on_reconstruction(
        self,
    ) -> None:
        result, revision = self._start(
            non_achievedness=(item("not-1", "Need answer", kind="not"),)
        )
        attempt = self.service.inspect(
            InspectionRequest(
                target_kind=InspectionTargetKind.ATTEMPT,
                target_id=result.execution_attempt_id,
                view=InspectionView.RECONSTRUCTION,
            )
        ).payload
        transition_id = self.repository.load_attempt(
            result.execution_attempt_id
        ).transition_artifact_references[-1]
        transition = self.service.inspect(
            InspectionRequest(
                target_kind=InspectionTargetKind.TRANSITION,
                target_id=transition_id,
                view=InspectionView.RECONSTRUCTION,
            )
        ).payload
        semantic_revision = self.service.inspect(
            InspectionRequest(
                target_kind=InspectionTargetKind.REVISION,
                target_id=revision.identity.revision_id,
                view=InspectionView.RECONSTRUCTION,
            )
        ).payload

        self.assertEqual(
            result.execution_attempt_id,
            attempt["attempt"]["attempt_id"],
        )
        self.assertEqual(1, len(attempt["transitions"]))
        self.assertEqual(
            transition_id,
            transition["transition_artifact"]["artifact_id"],
        )
        self.assertTrue(transition["replay_verification"]["verified"])
        self.assertEqual(
            revision.identity.revision_id,
            semantic_revision["revision"]["identity"]["revision_id"],
        )
        self.assertNotIn("attempt_id", semantic_revision["revision"])

    def test_reconstruction_inspection_rechecks_scope_authority(self) -> None:
        result, _ = self._start(achieved=(item("fact-1", "Base"),))
        transition_id = self.repository.load_attempt(
            result.execution_attempt_id
        ).transition_artifact_references[-1]

        for target_kind, target_id in (
            (InspectionTargetKind.ATTEMPT, result.execution_attempt_id),
            (InspectionTargetKind.TRANSITION, transition_id),
        ):
            with self.subTest(target_kind=target_kind):
                with self.assertRaises(PermissionError):
                    self.service.inspect(
                        InspectionRequest(
                            target_kind=target_kind,
                            target_id=target_id,
                            view=InspectionView.RECONSTRUCTION,
                            authority_context={
                                "allowed_scope_ids": ["different-scope"]
                            },
                        )
                    )

    def test_historical_operations_are_read_only_and_bypass_reduction(self) -> None:
        _, base = self._start(achieved=(item("fact-1", "Base"),))
        augmented_result = self.service.resume(
            self._request(
                base,
                OperationKind.AUGMENT,
                inlet(
                    "augment-for-history",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(
                        achieved=(item("fact-2", "Additional"),)
                    ),
                ),
            )
        )
        augmented = self.repository.require_revision(
            augmented_result.resulting_revision_identity
        )
        controller = ProposalController(
            ReductionProposal(
                delta=SemanticDelta(
                    achieved=(item("should-not-run", "Wrong"),)
                )
            )
        )
        service = ResumptionService(
            self.repository,
            reduction_controller=controller,
            id_factory=self.ids,
        )

        for operation in (
            OperationKind.EXPLAIN,
            OperationKind.VERIFY,
            OperationKind.RECONSTRUCT,
        ):
            with self.subTest(operation=operation):
                result = service.resume(self._request(augmented, operation))
                operation_result = result.presentation["operation_result"]

                self.assertIsNone(result.resulting_revision_identity)
                self.assertEqual(operation.value, operation_result["operation"])
                self.assertEqual(
                    [
                        augmented.identity.revision_id,
                        base.identity.revision_id,
                    ],
                    operation_result["path_revision_ids"],
                )
                self.assertTrue(operation_result["verified"])

        self.assertEqual([], controller.contexts)
        self.assertEqual(
            augmented.identity,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity,
        )

    def test_reversal_creates_a_new_transition_without_erasing_history(self) -> None:
        _, base = self._start(achieved=(item("fact-1", "Base"),))
        augmented_result = self.service.resume(
            self._request(
                base,
                OperationKind.AUGMENT,
                inlet(
                    "augment-before-reverse",
                    InletRelationship.AUGMENTATION,
                    delta=SemanticDelta(
                        achieved=(item("fact-2", "Additional"),)
                    ),
                ),
            )
        )
        augmented = self.repository.require_revision(
            augmented_result.resulting_revision_identity
        )

        reversed_result = self.service.resume(
            self._request(
                augmented,
                OperationKind.REVERSE,
                inlet(
                    "reverse-1",
                    InletRelationship.REVERSAL,
                    reversal=Reversal(
                        target_transition_artifact_id=(
                            augmented.transition_artifact_id
                        ),
                        restore_parent_revision_id=base.identity.revision_id,
                        evidence_references=("review:approved",),
                        rationale="withdraw the admitted augmentation",
                    ),
                ),
            )
        )
        reversed_revision = self.repository.require_revision(
            reversed_result.resulting_revision_identity
        )
        artifact = self.repository.load_transition_artifact(
            reversed_revision.transition_artifact_id
        )

        self.assertEqual(
            (augmented.identity.revision_id,),
            reversed_revision.parent_revision_ids,
        )
        self.assertEqual(
            ("fact-1",),
            tuple(item.item_id for item in reversed_revision.state.achieved),
        )
        self.assertEqual(OperationKind.REVERSE.value, artifact["operation"])
        self.assertEqual(
            augmented.transition_artifact_id,
            artifact["reconciliation"]["target_transition_artifact_id"],
        )
        self.assertIsNotNone(
            self.repository.load_revision(augmented.identity.revision_id)
        )
        self.assertEqual(
            (
                reversed_revision.identity.revision_id,
                augmented.identity.revision_id,
                base.identity.revision_id,
            ),
            self.repository.path_to_roots(
                reversed_revision.identity.revision_id
            ),
        )

    def test_reversal_cannot_guess_or_target_a_non_current_transition(self) -> None:
        _, base = self._start(achieved=(item("fact-1", "Base"),))

        result = self.service.resume(
            self._request(
                base,
                OperationKind.REVERSE,
                inlet(
                    "reverse-invalid",
                    InletRelationship.REVERSAL,
                    reversal=Reversal(
                        target_transition_artifact_id="different-transition",
                        restore_parent_revision_id="guessed-parent",
                        evidence_references=("review:approved",),
                        rationale="invalid target",
                    ),
                ),
            )
        )

        self.assertEqual(SemanticOutcome.REJECTED, result.semantic_outcome)
        self.assertIsNone(result.resulting_revision_identity)
        self.assertEqual(
            base.identity,
            self.repository.load_branch_head(
                "scope-1", "objective-1", "main"
            ).identity,
        )

    @staticmethod
    def _hold(hold_id: str, token: str) -> HoldOn:
        return HoldOn(
            hold_id=hold_id,
            unresolved_semantic_object={"item_id": "not-1"},
            continuation_carrier={"frontier": ["not-1"]},
            resume_predicate={"required_payload": {"answer": "ready"}},
            failure_or_expiry_predicate={
                "expire": {"required_payload": {"expired": True}},
                "fail": {"required_payload": {"failed": True}},
            },
            temporal_policy={},
            correlation={"token": token},
            multiplicity={"mode": "one"},
            scope={"scope_id": "scope-1"},
            provenance_and_governance={"policy": "test"},
        )


if __name__ == "__main__":
    unittest.main()
