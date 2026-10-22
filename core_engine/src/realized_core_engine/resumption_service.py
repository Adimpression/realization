"""Controller-owned governed resumption service."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from realized_core_runtime import (
    AttemptExecutionOutcome,
    AttemptInterrupted,
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptRunResult,
    AttemptWorkResult,
    InterruptionRequest,
    InterruptionResult,
    PreparedAttemptWork,
    request_attempt_interruption,
    run_execution_attempt,
)

from realized_core_engine.resumption_contracts import (
    AdmissionDecision,
    AdmissionDisposition,
    ContinuationInlet,
    GoverningDirection,
    HoldDisposition,
    IdentityDisposition,
    IdentityDispositionKind,
    InletRelationship,
    InspectionRequest,
    InspectionResult,
    InspectionTargetKind,
    InspectionView,
    OperationKind,
    ProjectionPolicy,
    Realignment,
    ReductionContext,
    ReductionController,
    ReductionProposal,
    ResumptionIdentity,
    ResumptionProjection,
    ResumptionRequest,
    ResumptionResult,
    Revision,
    SemanticDelta,
    SemanticItem,
    SemanticOutcome,
    SemanticState,
    StartRequest,
    TransitionArtifact,
    canonical_json,
    content_digest,
)
from realized_core_engine.resumption_repository import (
    AttemptNotRunningError,
    RepositoryIntegrityError,
    SQLiteResumptionRepository,
    StaleAnchorError,
)


AdmissionEvaluator = Callable[
    [
        OperationKind,
        Revision | None,
        ContinuationInlet | None,
        SemanticState,
        dict[str, Any],
        dict[str, Any],
    ],
    AdmissionDecision,
]


class TransitionValidationError(ValueError):
    """A mechanically invalid semantic transition proposal."""

    def __init__(
        self,
        message: str,
        *,
        outcome: SemanticOutcome = SemanticOutcome.REJECTED,
    ) -> None:
        self.outcome = outcome
        super().__init__(message)


class _FunctionWork(PreparedAttemptWork):
    def __init__(
        self,
        callback: Callable[[Callable[[], bool]], AttemptWorkResult],
    ) -> None:
        self._callback = callback

    def execute(
        self,
        *,
        should_stop: Callable[[], bool],
    ) -> AttemptWorkResult:
        return self._callback(should_stop)


class ResumptionService:
    """Canonical semantic implementation over the resumption repository."""

    def __init__(
        self,
        repository: SQLiteResumptionRepository,
        *,
        reduction_controller: ReductionController | None = None,
        admission_evaluator: AdmissionEvaluator | None = None,
        id_factory: Callable[[str], str] | None = None,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository
        self.reduction_controller = reduction_controller
        self.admission_evaluator = (
            admission_evaluator or self._default_admission_evaluator
        )
        self._id_factory = id_factory or (
            lambda prefix: f"{prefix}_{uuid.uuid4().hex}"
        )
        self._clock = clock or (
            lambda: datetime.now(timezone.utc).isoformat()
        )

    def start(self, request: StartRequest) -> ResumptionResult:
        """Start a new objective with no causal parent revision."""

        attempt_id = self._id_factory("attempt")
        attempt = AttemptRecord(
            attempt_id=attempt_id,
            causal_anchor=(
                f"start:{request.scope_id}/{request.objective_id}/"
                f"{request.branch_id}"
            ),
            operation=OperationKind.START.value,
            execution_policy=dict(request.execution_policy),
        )
        run_result = run_execution_attempt(
            self.repository,
            attempt,
            _FunctionWork(
                lambda should_stop: self._start_work(
                    request,
                    attempt_id,
                    should_stop,
                )
            ),
        )
        return self._public_result(run_result, source_revision=None)

    def resume(self, request: ResumptionRequest) -> ResumptionResult:
        """Execute one typed continuation operation from an exact anchor."""

        attempt_id = self._id_factory("attempt")
        attempt = AttemptRecord(
            attempt_id=attempt_id,
            causal_anchor=request.anchor.causal_anchor,
            operation=request.operation.value,
            execution_policy=dict(request.execution_policy),
            latest_admitted_revision_id=request.anchor.revision_id,
        )
        run_result = run_execution_attempt(
            self.repository,
            attempt,
            _FunctionWork(
                lambda should_stop: self._resume_work(
                    request,
                    attempt_id,
                    should_stop,
                )
            ),
        )
        source = self.repository.load_revision(request.anchor.revision_id)
        return self._public_result(run_result, source_revision=source)

    def interrupt(self, request: InterruptionRequest) -> InterruptionResult:
        """Interrupt an attempt without synthesizing a semantic transition."""

        return request_attempt_interruption(self.repository, request)

    def project(
        self,
        revision: Revision,
        policy: ProjectionPolicy,
    ) -> ResumptionProjection:
        """Construct a deterministic, bounded, inspectable state projection."""

        permitted = set(policy.permitted_item_ids)
        all_items = sorted(
            (*revision.state.achieved, *revision.state.non_achievedness),
            key=lambda item: item.item_id,
        )
        eligible = [
            item
            for item in all_items
            if not permitted or item.item_id in permitted
        ]
        inline_ids = {
            item.item_id for item in eligible[: max(policy.max_inline_items, 0)]
        }
        overflow_ids = [
            item.item_id for item in eligible if item.item_id not in inline_ids
        ]
        restricted_count = len(all_items) - len(eligible)
        state = replace(
            revision.state,
            achieved=tuple(
                item
                for item in revision.state.achieved
                if item.item_id in inline_ids
            ),
            non_achievedness=tuple(
                item
                for item in revision.state.non_achievedness
                if item.item_id in inline_ids
            ),
            engine_state={},
        )
        references = [
            f"{self.repository.revision_reference(revision.identity.revision_id)}"
            f"/item/{item_id}"
            for item_id in overflow_ids
        ]
        revision_reference = self.repository.revision_reference(
            revision.identity.revision_id
        )
        if restricted_count:
            references.append(f"{revision_reference}/restricted-items")
        if overflow_ids or restricted_count:
            references.append(f"{revision_reference}/semantic-context")
            state = _redact_non_inline_semantic_context(state, inline_ids)
        if revision.state.engine_state:
            references.append(f"{revision_reference}/engine-state")

        statements = [f"{len(inline_ids)} current semantic items are inline."]
        if overflow_ids:
            statements.append(
                f"{len(overflow_ids)} permitted items are represented by stable references."
            )
        if restricted_count:
            statements.append(
                f"{restricted_count} items are withheld by projection policy."
            )
        if revision.state.engine_state:
            statements.append(
                "Canonical reducer reconstruction data is held behind an authorized reference."
            )
        completeness = " ".join(statements)
        projection = ResumptionProjection(
            identity=revision.identity,
            policy=policy,
            state=state,
            external_references=tuple(references),
            completeness_statement=completeness,
            projection_digest="",
        )
        return replace(
            projection,
            projection_digest=content_digest(projection.canonical_content()),
        )

    def inspect(self, request: InspectionRequest) -> InspectionResult:
        """Inspect typed state without reconstructing it from presentation."""

        if request.target_kind is InspectionTargetKind.ATTEMPT:
            attempt = self.repository.load_attempt(request.target_id)
            if attempt is None:
                raise KeyError(f"unknown execution attempt: {request.target_id}")
            self._authorize_attempt_inspection(request, attempt)
            if request.view is InspectionView.RECONSTRUCTION:
                latest = (
                    self.repository.load_revision(
                        attempt.latest_admitted_revision_id
                    )
                    if attempt.latest_admitted_revision_id is not None
                    else None
                )
                payload = {
                    "attempt": _attempt_payload(attempt),
                    "transitions": [
                        {
                            "transition_artifact": (
                                self.repository.load_transition_artifact(
                                    artifact_id
                                )
                            ),
                            "replay_verification": (
                                self.repository.verify_transition_replay(
                                    artifact_id
                                )
                            ),
                        }
                        for artifact_id in (
                            attempt.transition_artifact_references
                        )
                    ],
                    "latest_admitted_revision": (
                        {
                            **latest.canonical_content(),
                            "revision_digest": latest.revision_digest,
                        }
                        if latest is not None
                        else None
                    ),
                }
            else:
                payload = _attempt_payload(attempt)
        elif request.target_kind is InspectionTargetKind.TRANSITION:
            payload = self.repository.load_transition_artifact(request.target_id)
            if payload is None:
                raise KeyError(
                    f"unknown transition artifact: {request.target_id}"
                )
            self._authorize_transition_inspection(request, payload)
            if request.view is InspectionView.RECONSTRUCTION:
                payload = {
                    "transition_artifact": payload,
                    "replay_verification": (
                        self.repository.verify_transition_replay(
                            request.target_id
                        )
                    ),
                }
        else:
            revision = self._inspection_revision(request)
            self._authorize_inspection(request, revision)
            payload = self._revision_inspection_payload(revision, request.view)
        return InspectionResult(
            target_kind=request.target_kind,
            target_id=request.target_id,
            view=request.view,
            payload=payload,
        )

    def proposal_cache_key(
        self,
        *,
        projection: ResumptionProjection,
        inlet: ContinuationInlet | None,
        operation: OperationKind,
        proposal_schema_version: str,
        prompt_version: str,
        model_identity: str,
        provider_identity: str,
        governance_posture: dict[str, Any],
    ) -> str:
        """Build a cache key that never confuses proposals with admissions."""

        return content_digest(
            {
                "projection_digest": projection.projection_digest,
                "inlet_digest": inlet.digest if inlet is not None else None,
                "operation": operation.value,
                "direction_digest": content_digest(
                    projection.state.governing_direction.to_dict()
                ),
                "realignment_digest": content_digest(
                    [item.to_dict() for item in projection.state.realignments]
                ),
                "proposal_schema_version": proposal_schema_version,
                "prompt_version": prompt_version,
                "model_identity": model_identity,
                "provider_identity": provider_identity,
                "governance_posture": governance_posture,
            }
        )

    # Attempt work -------------------------------------------------------------

    def _start_work(
        self,
        request: StartRequest,
        attempt_id: str,
        should_stop: Callable[[], bool],
    ) -> AttemptWorkResult:
        self._raise_if_stopped(should_stop)
        attempt = self._require_running_attempt(attempt_id)
        existing = self.repository.load_branch_head(
            request.scope_id,
            request.objective_id,
            request.branch_id,
        )
        if existing is not None:
            return self._non_committing_work_result(
                attempt,
                source=None,
                operation=OperationKind.START,
                inlet=request.initial_inlet,
                projection=None,
                outcome=SemanticOutcome.STALE,
                rationale="the requested initial branch already exists",
                diagnostics={
                    "actual_branch_head": existing.identity.revision_id
                },
            )

        empty = SemanticState(
            achieved=(),
            non_achievedness=(),
            governing_direction=request.governing_direction,
            capability_declarations=tuple(
                dict(item)
                for item in request.initial_inlet.payload.get(
                    "capability_declarations", ()
                )
            ),
            scope_imports=tuple(
                dict(item)
                for item in request.initial_inlet.payload.get(
                    "scope_imports", ()
                )
            ),
            engine_state=dict(
                request.initial_inlet.payload.get("engine_state", {})
            ),
        )
        initial_delta = request.initial_inlet.delta
        if _delta_is_empty(initial_delta):
            initial_delta = SemanticDelta(
                non_achievedness=(
                    SemanticItem(
                        item_id=self._stable_item_id(
                            "objective", request.initial_inlet.to_dict()
                        ),
                        kind="objective",
                        payload={
                            "inlet": dict(request.initial_inlet.payload),
                            "target": request.initial_inlet.target,
                        },
                        provenance_references=(
                            request.initial_inlet.inlet_id,
                            *request.initial_inlet.provenance,
                        ),
                    ),
                )
            )
        try:
            candidate, reconciliation = self._apply_delta(
                empty,
                initial_delta,
                allow_supersession=False,
                allow_direction=False,
            )
            candidate = replace(
                candidate,
                provenance_references=tuple(
                    dict.fromkeys(
                        (
                            *candidate.provenance_references,
                            request.initial_inlet.inlet_id,
                            *request.initial_inlet.provenance,
                        )
                    )
                ),
            )
            decision = self.admission_evaluator(
                OperationKind.START,
                None,
                request.initial_inlet,
                candidate,
                dict(request.governance_policy),
                dict(request.execution_policy),
            )
            if decision.disposition is not AdmissionDisposition.ACCEPTED:
                raise TransitionValidationError(decision.rationale)
            proposal = self._reduce_start(
                request,
                candidate,
                should_stop,
            )
            candidate, proposal_reconciliation = (
                self._apply_reduction_proposal(candidate, proposal)
            )
            reconciliation = {
                **reconciliation,
                "inlet_admission": decision.to_dict(),
                "reduction": {
                    **proposal_reconciliation,
                    **dict(proposal.reconciliation),
                },
            }
            decision = self.admission_evaluator(
                OperationKind.START,
                None,
                request.initial_inlet,
                candidate,
                dict(request.governance_policy),
                dict(request.execution_policy),
            )
            if decision.disposition is not AdmissionDisposition.ACCEPTED:
                raise TransitionValidationError(decision.rationale)
        except TransitionValidationError as exc:
            return self._non_committing_work_result(
                attempt,
                source=None,
                operation=OperationKind.START,
                inlet=request.initial_inlet,
                projection=None,
                outcome=exc.outcome,
                rationale=str(exc),
            )

        self._raise_if_stopped(should_stop)
        outcome = proposal.semantic_outcome or _infer_semantic_outcome(candidate)
        revision, artifact = self._revision_and_artifact(
            source=None,
            target_scope_id=request.scope_id,
            target_objective_id=request.objective_id,
            target_branch_id=request.branch_id,
            parent_revision_ids=(),
            state=candidate,
            operation=OperationKind.START,
            inlet=request.initial_inlet,
            projection=None,
            reconciliation=reconciliation,
            admission=decision,
            semantic_outcome=outcome,
            realignment=None,
            proposal=proposal,
        )
        try:
            self.repository.commit_revision(
                revision,
                artifact,
                expected_head_revision_id=None,
                attempt_id=attempt.attempt_id,
            )
        except StaleAnchorError as exc:
            return self._non_committing_work_result(
                attempt,
                source=None,
                operation=OperationKind.START,
                inlet=request.initial_inlet,
                projection=None,
                outcome=SemanticOutcome.STALE,
                rationale=str(exc),
                diagnostics={"actual_branch_head": exc.actual},
            )
        public = self._result_for_revision(
            attempt_id=attempt.attempt_id,
            source=None,
            revision=revision,
            artifact=artifact,
            semantic_outcome=outcome,
            presentation=dict(proposal.presentation),
        )
        return AttemptWorkResult(
            semantic_outcome=outcome.value,
            latest_admitted_revision_id=revision.identity.revision_id,
            transition_artifact_references=(artifact.artifact_id,),
            payload={"resumption_result": public},
        )

    def _resume_work(
        self,
        request: ResumptionRequest,
        attempt_id: str,
        should_stop: Callable[[], bool],
    ) -> AttemptWorkResult:
        self._raise_if_stopped(should_stop)
        attempt = self._require_running_attempt(attempt_id)
        try:
            source = self.repository.require_revision(request.anchor)
        except (KeyError, ValueError, RepositoryIntegrityError) as exc:
            return self._non_committing_work_result(
                attempt,
                source=None,
                operation=request.operation,
                inlet=request.inlet,
                projection=None,
                outcome=SemanticOutcome.REJECTED,
                rationale=str(exc),
            )
        projection = self.project(source, request.projection_policy)

        try:
            self._validate_operation_request(request, source)
            target, parent_ids, expected_head = self._candidate_for_request(
                request,
                source,
            )
            candidate, reconciliation, realignment = self._apply_request(
                request,
                source,
                target,
            )
            inlet_admission = self.admission_evaluator(
                request.operation,
                source,
                request.inlet,
                candidate,
                dict(request.governance_policy),
                dict(request.execution_policy),
            )
            if inlet_admission.disposition is not AdmissionDisposition.ACCEPTED:
                raise TransitionValidationError(inlet_admission.rationale)
            self._raise_if_stopped(should_stop)
            proposal = self._reduce(
                request,
                projection,
                candidate,
                should_stop,
            )
            candidate, proposal_reconciliation = self._apply_reduction_proposal(
                candidate,
                proposal,
            )
            reconciliation = {
                **reconciliation,
                "inlet_admission": inlet_admission.to_dict(),
                "reduction": {
                    **proposal_reconciliation,
                    **dict(proposal.reconciliation),
                },
            }
            admission = self.admission_evaluator(
                request.operation,
                source,
                request.inlet,
                candidate,
                dict(request.governance_policy),
                dict(request.execution_policy),
            )
            if admission.disposition is not AdmissionDisposition.ACCEPTED:
                raise TransitionValidationError(admission.rationale)
        except TransitionValidationError as exc:
            return self._non_committing_work_result(
                attempt,
                source=source,
                operation=request.operation,
                inlet=request.inlet,
                projection=projection,
                outcome=exc.outcome,
                rationale=str(exc),
            )

        state_changed = candidate.digest != source.state.digest
        forced_outcome = reconciliation.get("forced_semantic_outcome")
        outcome = (
            proposal.semantic_outcome
            or (SemanticOutcome(forced_outcome) if forced_outcome else None)
            or _infer_semantic_outcome(candidate)
        )
        if not state_changed:
            public = ResumptionResult(
                source_revision_identity=source.identity,
                execution_attempt_id=attempt.attempt_id,
                execution_outcome=AttemptExecutionOutcome.TERMINATED,
                semantic_outcome=outcome,
                resulting_revision_identity=None,
                transition_artifact_reference=None,
                attempt_artifact_reference=(
                    self.repository.attempt_artifact_reference(attempt.attempt_id)
                ),
                realignment_summary=None,
                identity_disposition=None,
                achieved_state_summary=tuple(
                    item.item_id for item in source.state.achieved
                ),
                non_achievedness_summary=tuple(
                    item.item_id for item in source.state.non_achievedness
                ),
                active_hold_summary=tuple(
                    hold.hold_id for hold in _active_holds(source.state)
                ),
                diagnostics={"semantic_state_changed": False},
                presentation=dict(proposal.presentation),
            )
            return AttemptWorkResult(
                semantic_outcome=outcome.value,
                latest_admitted_revision_id=source.identity.revision_id,
                proposal_references=proposal.proposal_references,
                receipt_references=tuple(
                    dict.fromkeys(
                        (
                            *proposal.capability_receipt_references,
                            *proposal.effect_receipt_references,
                        )
                    )
                ),
                payload={"resumption_result": public},
            )

        self._raise_if_stopped(should_stop)
        revision, artifact = self._revision_and_artifact(
            source=source,
            target_scope_id=target[0],
            target_objective_id=target[1],
            target_branch_id=target[2],
            parent_revision_ids=parent_ids,
            state=candidate,
            operation=request.operation,
            inlet=request.inlet,
            projection=projection,
            reconciliation=reconciliation,
            admission=admission,
            semantic_outcome=outcome,
            realignment=realignment,
            proposal=proposal,
        )
        try:
            self.repository.commit_revision(
                revision,
                artifact,
                expected_head_revision_id=expected_head,
                attempt_id=attempt.attempt_id,
            )
        except (StaleAnchorError, AttemptNotRunningError) as exc:
            actual = exc.actual if isinstance(exc, StaleAnchorError) else None
            return self._non_committing_work_result(
                attempt,
                source=source,
                operation=request.operation,
                inlet=request.inlet,
                projection=projection,
                outcome=SemanticOutcome.STALE,
                rationale=str(exc),
                diagnostics={"actual_branch_head": actual},
            )
        public = self._result_for_revision(
            attempt_id=attempt.attempt_id,
            source=source,
            revision=revision,
            artifact=artifact,
            semantic_outcome=outcome,
            presentation=dict(proposal.presentation),
        )
        return AttemptWorkResult(
            semantic_outcome=outcome.value,
            latest_admitted_revision_id=revision.identity.revision_id,
            proposal_references=proposal.proposal_references,
            receipt_references=tuple(
                dict.fromkeys(
                    (
                        *proposal.capability_receipt_references,
                        *proposal.effect_receipt_references,
                    )
                )
            ),
            transition_artifact_references=(artifact.artifact_id,),
            payload={"resumption_result": public},
        )

    # Reconciliation -----------------------------------------------------------

    def _validate_operation_request(
        self,
        request: ResumptionRequest,
        source: Revision,
    ) -> None:
        if request.expected_branch_head_revision_id != request.anchor.revision_id:
            raise TransitionValidationError(
                "expected branch head must identify the exact causal anchor",
                outcome=SemanticOutcome.STALE,
            )
        current_head = self.repository.load_branch_head(
            source.identity.scope_id,
            source.identity.objective_id,
            source.identity.branch_id,
        )
        if (
            current_head is None
            or current_head.identity.revision_id
            != request.expected_branch_head_revision_id
        ):
            raise TransitionValidationError(
                "causal anchor is not the current source branch head",
                outcome=SemanticOutcome.STALE,
            )

        required_relationships = {
            OperationKind.CONTINUE: InletRelationship.CONTINUATION,
            OperationKind.DERIVE: InletRelationship.CONTINUATION,
            OperationKind.AUGMENT: InletRelationship.AUGMENTATION,
            OperationKind.CORRECT: InletRelationship.CORRECTION,
            OperationKind.REDIRECT_AND_REALIGN: InletRelationship.REDIRECTION,
            OperationKind.RESUME_SUSPENDED: (
                InletRelationship.HOLD_SATISFACTION
            ),
        }
        expected = required_relationships.get(request.operation)
        if expected is not None:
            if request.inlet is None:
                raise TransitionValidationError(
                    f"{request.operation.value} requires an explicit inlet"
                )
            if request.inlet.relationship is not expected:
                raise TransitionValidationError(
                    f"{request.operation.value} requires a "
                    f"{expected.value} inlet"
                )

        if request.operation is OperationKind.RESUME_AFTER_INTERRUPTION:
            if not request.source_attempt_id:
                raise TransitionValidationError(
                    "resume after interruption requires the source attempt identity"
                )
            source_attempt = self.repository.load_attempt(request.source_attempt_id)
            if source_attempt is None:
                raise TransitionValidationError("source attempt does not exist")
            if source_attempt.status is not AttemptLifecycleStatus.INTERRUPTED:
                raise TransitionValidationError(
                    "source attempt is not interrupted"
                )
            if (
                source_attempt.latest_admitted_revision_id
                != source.identity.revision_id
            ):
                raise TransitionValidationError(
                    "resume-after-interruption must use the latest admitted revision"
                )

        if request.operation is OperationKind.REDIRECT_AND_REALIGN:
            if request.inlet is None or request.inlet.realignment is None:
                raise TransitionValidationError(
                    "redirection requires an explicit realignment"
                )
            if request.inlet.delta.governing_direction is None:
                raise TransitionValidationError(
                    "redirection requires an explicit governing direction"
                )

        if request.operation is OperationKind.BRANCH:
            target = str(
                (request.inlet.payload if request.inlet else {}).get(
                    "target_branch_id", ""
                )
            ).strip()
            if not target or target == source.identity.branch_id:
                raise TransitionValidationError(
                    "branch requires a distinct explicit target_branch_id"
                )

        if request.operation is OperationKind.DERIVE:
            assert request.inlet is not None
            payload = request.inlet.payload
            target_scope = str(payload.get("target_scope_id", "")).strip()
            target_objective = str(
                payload.get("target_objective_id", "")
            ).strip()
            target_branch = str(payload.get("target_branch_id", "main")).strip()
            selected = {
                str(item) for item in payload.get("selected_item_ids", ())
            }
            available = {
                item.item_id
                for item in (
                    *source.state.achieved,
                    *source.state.non_achievedness,
                )
            }
            if not target_scope or not target_objective or not target_branch:
                raise TransitionValidationError(
                    "derive requires explicit target scope, objective, and branch"
                )
            if (
                target_scope == source.identity.scope_id
                and target_objective == source.identity.objective_id
            ):
                raise TransitionValidationError(
                    "derive requires a new objective or scope identity"
                )
            if not selected or not selected.issubset(available):
                raise TransitionValidationError(
                    "derive requires explicit admitted source item identities"
                )
            if request.inlet.delta.governing_direction is None:
                raise TransitionValidationError(
                    "derive requires an explicit governing direction"
                )

        if request.operation is OperationKind.MERGE:
            if not request.merge_parent_identities:
                raise TransitionValidationError(
                    "merge requires at least one additional parent"
                )

    def _candidate_for_request(
        self,
        request: ResumptionRequest,
        source: Revision,
    ) -> tuple[tuple[str, str, str], tuple[str, ...], str | None]:
        target = (
            source.identity.scope_id,
            source.identity.objective_id,
            source.identity.branch_id,
        )
        parent_ids = (source.identity.revision_id,)
        expected: str | None = request.expected_branch_head_revision_id

        if request.operation is OperationKind.BRANCH:
            target_branch = str(request.inlet.payload["target_branch_id"])
            target = (target[0], target[1], target_branch)
            expected = None
        elif request.operation is OperationKind.DERIVE:
            assert request.inlet is not None
            target = (
                str(request.inlet.payload["target_scope_id"]),
                str(request.inlet.payload["target_objective_id"]),
                str(request.inlet.payload.get("target_branch_id", "main")),
            )
            expected = None
        elif request.operation is OperationKind.REDIRECT_AND_REALIGN:
            assert request.inlet is not None
            assert request.inlet.realignment is not None
            disposition = request.inlet.realignment.identity_disposition
            target = (
                disposition.target_scope_id,
                disposition.target_objective_id,
                disposition.target_branch_id,
            )
            if disposition.kind is not IdentityDispositionKind.SAME_OBJECTIVE:
                expected = None
        elif request.operation is OperationKind.MERGE:
            parents = [source.identity.revision_id]
            for identity in request.merge_parent_identities:
                self.repository.require_revision(identity)
                if identity.revision_id not in parents:
                    parents.append(identity.revision_id)
            parent_ids = tuple(parents)
        return target, parent_ids, expected

    def _apply_request(
        self,
        request: ResumptionRequest,
        source: Revision,
        target: tuple[str, str, str],
    ) -> tuple[SemanticState, dict[str, Any], Realignment | None]:
        if request.operation is OperationKind.REDIRECT_AND_REALIGN:
            assert request.inlet is not None
            assert request.inlet.realignment is not None
            state, reconciliation = self._apply_realignment(
                source,
                request.inlet,
                target,
            )
            return state, reconciliation, request.inlet.realignment
        if request.operation is OperationKind.DERIVE:
            assert request.inlet is not None
            selected_ids = {
                str(item)
                for item in request.inlet.payload.get("selected_item_ids", ())
            }
            selected_achieved = tuple(
                item
                for item in source.state.achieved
                if item.item_id in selected_ids
            )
            selected_non_achieved = tuple(
                item
                for item in source.state.non_achievedness
                if item.item_id in selected_ids
            )
            direction = request.inlet.delta.governing_direction
            assert direction is not None
            derived = SemanticState(
                achieved=selected_achieved,
                non_achievedness=selected_non_achieved,
                governing_direction=direction,
                provenance_references=(
                    self.repository.revision_reference(
                        source.identity.revision_id
                    ),
                    request.inlet.inlet_id,
                    *request.inlet.provenance,
                ),
                governance_references=source.state.governance_references,
            )
            derived, delta_reconciliation = self._apply_delta(
                derived,
                replace(request.inlet.delta, governing_direction=None),
                allow_supersession=False,
                allow_direction=False,
            )
            return (
                derived,
                {
                    "kind": "derived_objective",
                    "selected_source_item_ids": sorted(selected_ids),
                    "source_revision_id": source.identity.revision_id,
                    "delta": delta_reconciliation,
                },
                None,
            )
        if request.operation is OperationKind.MERGE:
            state, reconciliation = self._merge_states(
                source,
                request.merge_parent_identities,
            )
            if request.inlet is not None:
                state, inlet_reconciliation = self._apply_delta(
                    state,
                    request.inlet.delta,
                    allow_supersession=(
                        request.inlet.relationship is InletRelationship.CORRECTION
                    ),
                    allow_direction=False,
                )
                reconciliation["inlet"] = inlet_reconciliation
            return state, reconciliation, None
        if request.operation is OperationKind.RESUME_SUSPENDED:
            assert request.inlet is not None
            state, hold_reconciliation = self._satisfy_hold(
                source.state,
                request.inlet,
            )
            state, delta_reconciliation = self._apply_delta(
                state,
                request.inlet.delta,
                allow_supersession=False,
                allow_direction=False,
            )
            return (
                state,
                {
                    "hold": hold_reconciliation,
                    "delta": delta_reconciliation,
                    "forced_semantic_outcome": hold_reconciliation.get(
                        "forced_semantic_outcome"
                    ),
                },
                None,
            )
        if request.inlet is None:
            return source.state, {"kind": "no_inlet"}, None
        allow_supersession = request.operation is OperationKind.CORRECT
        state, reconciliation = self._apply_delta(
            source.state,
            request.inlet.delta,
            allow_supersession=allow_supersession,
            allow_direction=False,
        )
        return state, reconciliation, None

    def _apply_delta(
        self,
        state: SemanticState,
        delta: SemanticDelta,
        *,
        allow_supersession: bool,
        allow_direction: bool,
    ) -> tuple[SemanticState, dict[str, Any]]:
        if delta.supersessions and not allow_supersession:
            raise TransitionValidationError(
                "this operation cannot supersede current semantic material"
            )
        if delta.governing_direction is not None and not allow_direction:
            raise TransitionValidationError(
                "this operation cannot change the governing direction"
            )

        achieved = {item.item_id: item for item in state.achieved}
        non_achieved = {
            item.item_id: item for item in state.non_achievedness
        }
        holds = {hold.hold_id: hold for hold in state.holds}
        supersession_edges = list(state.supersession_edges)

        for item in delta.achieved:
            self._add_item(achieved, non_achieved, item, destination="achieved")
        for item in delta.non_achievedness:
            self._add_item(
                achieved,
                non_achieved,
                item,
                destination="non_achievedness",
            )
        for item_id in delta.resolved_non_achievedness_ids:
            non_achieved.pop(item_id, None)
        for hold in delta.holds:
            existing = holds.get(hold.hold_id)
            if existing is not None and existing != hold:
                raise TransitionValidationError(
                    f"ambiguous replacement for HoldOn {hold.hold_id}",
                    outcome=SemanticOutcome.AMBIGUOUS,
                )
            holds[hold.hold_id] = hold
        for hold_id in delta.resolved_hold_ids:
            holds.pop(hold_id, None)

        for supersession in delta.supersessions:
            if not supersession.evidence_references:
                raise TransitionValidationError(
                    f"supersession lacks evidence: {supersession.target_item_id}"
                )
            in_achieved = supersession.target_item_id in achieved
            in_non_achieved = supersession.target_item_id in non_achieved
            if in_achieved == in_non_achieved:
                raise TransitionValidationError(
                    f"supersession target is missing or ambiguous: "
                    f"{supersession.target_item_id}",
                    outcome=SemanticOutcome.AMBIGUOUS,
                )
            achieved.pop(supersession.target_item_id, None)
            non_achieved.pop(supersession.target_item_id, None)
            replacement_id = None
            if supersession.replacement is not None:
                replacement_id = supersession.replacement.item_id
                self._add_item(
                    achieved,
                    non_achieved,
                    supersession.replacement,
                    destination="achieved",
                )
            supersession_edges.append(
                {
                    "prior_item_id": supersession.target_item_id,
                    "replacement_item_id": replacement_id,
                    "evidence_references": list(
                        supersession.evidence_references
                    ),
                    "rationale": supersession.rationale,
                }
            )

        result = replace(
            state,
            achieved=tuple(achieved[key] for key in sorted(achieved)),
            non_achievedness=tuple(
                non_achieved[key] for key in sorted(non_achieved)
            ),
            holds=tuple(holds[key] for key in sorted(holds)),
            supersession_edges=tuple(supersession_edges),
            governing_direction=(
                delta.governing_direction
                if delta.governing_direction is not None
                else state.governing_direction
            ),
        )
        return result, {
            "added_achieved": [item.item_id for item in delta.achieved],
            "added_non_achievedness": [
                item.item_id for item in delta.non_achievedness
            ],
            "resolved_non_achievedness": list(
                delta.resolved_non_achievedness_ids
            ),
            "added_holds": [hold.hold_id for hold in delta.holds],
            "resolved_holds": list(delta.resolved_hold_ids),
            "superseded": [
                item.target_item_id for item in delta.supersessions
            ],
        }

    def _apply_reduction_proposal(
        self,
        candidate: SemanticState,
        proposal: ReductionProposal,
    ) -> tuple[SemanticState, dict[str, Any]]:
        """Apply and verify controller-owned output after inlet admission."""

        proposed, reconciliation = self._apply_delta(
            candidate,
            proposal.delta,
            allow_supersession=False,
            allow_direction=False,
        )
        if proposal.resulting_state is None:
            return proposed, reconciliation

        resulting = proposal.resulting_state
        if resulting.governing_direction != proposed.governing_direction:
            raise TransitionValidationError(
                "a reduction proposal cannot change the governing direction"
            )

        for field_name in (
            "supersession_edges",
            "contradiction_edges",
            "realignments",
            "hold_evaluations",
            "provenance_references",
            "governance_references",
        ):
            admitted = tuple(getattr(proposed, field_name))
            supplied = tuple(getattr(resulting, field_name))
            if supplied[: len(admitted)] != admitted:
                raise TransitionValidationError(
                    f"a reduction proposal cannot rewrite admitted {field_name}"
                )

        proposed_achieved = {item.item_id for item in proposed.achieved}
        resulting_achieved = {item.item_id for item in resulting.achieved}
        if not proposed_achieved.issubset(resulting_achieved):
            raise TransitionValidationError(
                "a reduction proposal cannot silently withdraw achieved state"
            )
        resulting_non_achieved = {
            item.item_id for item in resulting.non_achievedness
        }
        if resulting_achieved & resulting_non_achieved:
            raise TransitionValidationError(
                "a semantic item cannot be both achieved and non-achieved"
            )

        admitted_holds = {hold.hold_id: hold for hold in proposed.holds}
        resulting_holds = {hold.hold_id: hold for hold in resulting.holds}
        missing_holds = set(admitted_holds) - set(resulting_holds)
        if missing_holds:
            raise TransitionValidationError(
                "a reduction proposal cannot silently discharge HoldOn: "
                + ", ".join(sorted(missing_holds))
            )
        if any(
            resulting_holds[hold_id] != admitted
            for hold_id, admitted in admitted_holds.items()
        ):
            raise TransitionValidationError(
                "a reduction proposal cannot rewrite an admitted HoldOn"
            )

        admitted_imports = tuple(proposed.scope_imports)
        if tuple(resulting.scope_imports)[: len(admitted_imports)] != admitted_imports:
            raise TransitionValidationError(
                "a reduction proposal cannot rewrite admitted scope imports"
            )
        return resulting, {
            **reconciliation,
            "resulting_state_digest": resulting.digest,
            "resolved_by_reduction": sorted(
                {item.item_id for item in proposed.non_achievedness}
                - resulting_non_achieved
            ),
        }

    def _apply_realignment(
        self,
        source: Revision,
        inlet: ContinuationInlet,
        target: tuple[str, str, str],
    ) -> tuple[SemanticState, dict[str, Any]]:
        realignment = inlet.realignment
        assert realignment is not None
        if realignment.source_revision_id != source.identity.revision_id:
            raise TransitionValidationError(
                "realignment source revision does not match the causal anchor"
            )
        if realignment.redirection_inlet_id != inlet.inlet_id:
            raise TransitionValidationError(
                "realignment does not identify the redirection inlet"
            )
        self._validate_identity_disposition(
            source.identity,
            realignment.identity_disposition,
            target,
        )

        source_items = {
            item.item_id: item
            for item in (
                *source.state.achieved,
                *source.state.non_achievedness,
            )
        }
        affected = set(realignment.affected_item_ids)
        retained = set(realignment.retained_item_ids)
        superseded = set(realignment.superseded_item_ids)
        unresolved = set(realignment.unresolved_applicability_item_ids)
        if not affected.issubset(source_items):
            raise TransitionValidationError(
                "realignment affected scope contains unknown semantic material"
            )
        if (
            retained & superseded
            or retained & unresolved
            or superseded & unresolved
        ):
            raise TransitionValidationError(
                "realignment carry-forward dispositions overlap"
            )
        if retained | superseded | unresolved != affected:
            raise TransitionValidationError(
                "realignment does not exhaustively classify affected material"
            )
        if not realignment.completeness_statement.strip():
            raise TransitionValidationError(
                "realignment requires a completeness statement"
            )
        if (retained or superseded) and not realignment.evidence_references:
            unsupported = [
                item_id
                for item_id in sorted(retained | superseded)
                if not source_items[item_id].evidence_references
            ]
            if unsupported:
                raise TransitionValidationError(
                    "retained and superseded dispositions require support: "
                    + ", ".join(unsupported)
                )

        unresolved_items = {
            item.item_id: item
            for item in realignment.resulting_non_achievedness
        }
        if set(unresolved_items) != unresolved:
            raise TransitionValidationError(
                "every unresolved applicability item must become non-achievedness"
            )
        introduced = {
            item.item_id: item for item in realignment.introduced_items
        }
        if set(introduced) & set(source_items):
            raise TransitionValidationError(
                "introduced material cannot reuse a source material identity"
            )
        delta_introduced = {
            item.item_id: item
            for item in (
                *inlet.delta.achieved,
                *inlet.delta.non_achievedness,
            )
        }
        if set(introduced) != set(delta_introduced):
            raise TransitionValidationError(
                "introduced realignment material must be explicitly classified "
                "in the semantic delta"
            )
        for item_id, item in introduced.items():
            if item != delta_introduced[item_id]:
                raise TransitionValidationError(
                    f"introduced material differs from its classified delta: {item_id}"
                )

        achieved = {
            item.item_id: item
            for item in source.state.achieved
            if item.item_id not in superseded | unresolved
        }
        non_achieved = {
            item.item_id: item
            for item in source.state.non_achievedness
            if item.item_id not in superseded | unresolved
        }
        non_achieved.update(unresolved_items)
        supersession_edges = [
            *source.state.supersession_edges,
            *(
                {
                    "prior_item_id": item_id,
                    "replacement_item_id": None,
                    "relationship": "directional_supersession",
                    "realignment_source_revision_id": (
                        source.identity.revision_id
                    ),
                }
                for item_id in sorted(superseded)
            ),
        ]
        aligned = replace(
            source.state,
            achieved=tuple(achieved[key] for key in sorted(achieved)),
            non_achievedness=tuple(
                non_achieved[key] for key in sorted(non_achieved)
            ),
            governing_direction=inlet.delta.governing_direction
            or source.state.governing_direction,
            supersession_edges=tuple(supersession_edges),
            realignments=(*source.state.realignments, realignment),
            unresolved_applicability_item_ids=tuple(sorted(unresolved)),
            engine_state={},
        )
        aligned, delta_reconciliation = self._apply_delta(
            aligned,
            replace(inlet.delta, governing_direction=None),
            allow_supersession=bool(
                inlet.payload.get("includes_explicit_correction", False)
            ),
            allow_direction=False,
        )
        return aligned, {
            "kind": "redirection_realignment",
            "affected": sorted(affected),
            "retained": sorted(retained),
            "superseded": sorted(superseded),
            "introduced": sorted(introduced),
            "unresolved": sorted(unresolved),
            "identity_disposition": (
                realignment.identity_disposition.to_dict()
            ),
            "delta": delta_reconciliation,
        }

    def _merge_states(
        self,
        source: Revision,
        parent_identities: tuple[ResumptionIdentity, ...],
    ) -> tuple[SemanticState, dict[str, Any]]:
        achieved = {item.item_id: item for item in source.state.achieved}
        non_achieved = {
            item.item_id: item for item in source.state.non_achievedness
        }
        holds = {item.hold_id: item for item in source.state.holds}
        conflicts = dict(source.state.conflicts)
        conflict_ids: list[str] = []
        provenance = list(source.state.provenance_references)
        governance = list(source.state.governance_references)

        for identity in parent_identities:
            parent = self.repository.require_revision(identity)
            if (
                parent.identity.scope_id != source.identity.scope_id
                or parent.identity.objective_id != source.identity.objective_id
            ):
                raise TransitionValidationError(
                    "merge parents must share scope and objective identity"
                )
            for destination, items in (
                (achieved, parent.state.achieved),
                (non_achieved, parent.state.non_achievedness),
            ):
                for item in items:
                    existing = achieved.get(item.item_id) or non_achieved.get(
                        item.item_id
                    )
                    if existing is not None and existing != item:
                        conflict_id = self._stable_item_id(
                            "merge_conflict",
                            {
                                "item_id": item.item_id,
                                "left": existing.to_dict(),
                                "right": item.to_dict(),
                            },
                        )
                        conflict_item = SemanticItem(
                            item_id=conflict_id,
                            kind="merge_conflict",
                            payload={
                                "item_id": item.item_id,
                                "left": existing.to_dict(),
                                "right": item.to_dict(),
                            },
                            provenance_references=(
                                source.identity.revision_id,
                                parent.identity.revision_id,
                            ),
                        )
                        non_achieved[conflict_id] = conflict_item
                        conflicts[conflict_id] = [
                            source.identity.revision_id,
                            parent.identity.revision_id,
                        ]
                        conflict_ids.append(conflict_id)
                    elif existing is None:
                        destination[item.item_id] = item
            for hold in parent.state.holds:
                existing_hold = holds.get(hold.hold_id)
                if existing_hold is not None and existing_hold != hold:
                    raise TransitionValidationError(
                        f"merge has conflicting HoldOn {hold.hold_id}",
                        outcome=SemanticOutcome.CONFLICTED,
                    )
                holds[hold.hold_id] = hold
            if (
                parent.state.governing_direction
                != source.state.governing_direction
            ):
                direction_conflict_id = self._stable_item_id(
                    "direction_conflict",
                    {
                        "left": source.state.governing_direction.to_dict(),
                        "right": parent.state.governing_direction.to_dict(),
                    },
                )
                non_achieved[direction_conflict_id] = SemanticItem(
                    item_id=direction_conflict_id,
                    kind="direction_conflict",
                    payload={
                        "left": source.state.governing_direction.to_dict(),
                        "right": parent.state.governing_direction.to_dict(),
                    },
                )
                conflict_ids.append(direction_conflict_id)
            provenance.extend(parent.state.provenance_references)
            governance.extend(parent.state.governance_references)

        state = replace(
            source.state,
            achieved=tuple(achieved[key] for key in sorted(achieved)),
            non_achievedness=tuple(
                non_achieved[key] for key in sorted(non_achieved)
            ),
            holds=tuple(holds[key] for key in sorted(holds)),
            conflicts=conflicts,
            provenance_references=tuple(dict.fromkeys(provenance)),
            governance_references=tuple(dict.fromkeys(governance)),
        )
        return state, {
            "kind": "merge",
            "parent_revision_ids": [
                identity.revision_id for identity in parent_identities
            ],
            "conflict_item_ids": sorted(conflict_ids),
        }

    def _satisfy_hold(
        self,
        state: SemanticState,
        inlet: ContinuationInlet,
    ) -> tuple[SemanticState, dict[str, Any]]:
        hold_id = str(inlet.payload.get("hold_id", inlet.target)).strip()
        matches = [hold for hold in state.holds if hold.hold_id == hold_id]
        if len(matches) != 1:
            raise TransitionValidationError(
                "hold satisfaction must address one exact active HoldOn"
            )
        hold = matches[0]
        for key, expected in hold.correlation.items():
            if inlet.correlation.get(key) != expected:
                raise TransitionValidationError(
                    f"inlet correlation does not satisfy HoldOn {hold_id}"
                )
        try:
            disposition = HoldDisposition(
                inlet.payload.get(
                    "hold_disposition",
                    HoldDisposition.RESUME.value,
                )
            )
        except ValueError as exc:
            raise TransitionValidationError(
                f"unknown HoldOn disposition for {hold_id}"
            ) from exc
        evaluated_predicate: dict[str, Any] = {}
        if disposition is HoldDisposition.RESUME:
            evaluated_predicate = dict(hold.resume_predicate)
            self._require_hold_predicate(
                hold_id,
                "resume",
                evaluated_predicate,
                inlet,
            )
        elif disposition in {
            HoldDisposition.EXPIRE,
            HoldDisposition.FAIL,
        }:
            family = hold.failure_or_expiry_predicate
            selected = family.get(disposition.value, family)
            evaluated_predicate = (
                dict(selected) if isinstance(selected, dict) else {}
            )
            self._require_hold_predicate(
                hold_id,
                disposition.value,
                evaluated_predicate,
                inlet,
            )
        outcome = {
            HoldDisposition.RESUME: None,
            HoldDisposition.REMAIN_HELD: SemanticOutcome.PAUSED,
            HoldDisposition.EXPIRE: SemanticOutcome.EXPIRED,
            HoldDisposition.FAIL: SemanticOutcome.FAILED,
            HoldDisposition.ESCALATE: SemanticOutcome.INCOMPLETE,
            HoldDisposition.REFRAME: SemanticOutcome.INCOMPLETE,
        }[disposition]
        remaining_holds = [
            item for item in state.holds if item.hold_id != hold_id
        ]
        if disposition is HoldDisposition.REMAIN_HELD:
            remaining_holds.append(hold)
        evaluation = {
            "hold_id": hold_id,
            "disposition": disposition.value,
            "correlation": dict(inlet.correlation),
            "inlet_id": inlet.inlet_id,
            "evaluated_predicate": evaluated_predicate,
        }
        return (
            replace(
                state,
                holds=tuple(sorted(remaining_holds, key=lambda item: item.hold_id)),
                hold_evaluations=(*state.hold_evaluations, evaluation),
            ),
            {
                "hold_id": hold_id,
                "disposition": disposition.value,
                "correlation": dict(inlet.correlation),
                "forced_semantic_outcome": outcome.value if outcome else None,
            },
        )

    @staticmethod
    def _require_hold_predicate(
        hold_id: str,
        predicate_kind: str,
        predicate: dict[str, Any],
        inlet: ContinuationInlet,
    ) -> None:
        required_payload = predicate.get("required_payload", {})
        if not isinstance(required_payload, dict):
            raise TransitionValidationError(
                f"{predicate_kind} predicate is malformed for {hold_id}"
            )
        for key, expected in required_payload.items():
            if inlet.payload.get(key) != expected:
                raise TransitionValidationError(
                    f"{predicate_kind} predicate does not hold for {hold_id}"
                )

    def _reduce(
        self,
        request: ResumptionRequest,
        projection: ResumptionProjection,
        candidate: SemanticState,
        should_stop: Callable[[], bool],
    ) -> ReductionProposal:
        if self.reduction_controller is None:
            return ReductionProposal()
        context = ReductionContext(
            projection=projection,
            operation=request.operation,
            admitted_inlet=request.inlet,
            candidate_state=candidate,
            execution_policy=dict(request.execution_policy),
        )
        return self.reduction_controller.reduce(context, should_stop=should_stop)

    def _reduce_start(
        self,
        request: StartRequest,
        candidate: SemanticState,
        should_stop: Callable[[], bool],
    ) -> ReductionProposal:
        if self.reduction_controller is None:
            return ReductionProposal()
        context = ReductionContext(
            projection=None,
            operation=OperationKind.START,
            admitted_inlet=request.initial_inlet,
            candidate_state=candidate,
            execution_policy=dict(request.execution_policy),
        )
        return self.reduction_controller.reduce(context, should_stop=should_stop)

    # Artifacts and results ----------------------------------------------------

    def _revision_and_artifact(
        self,
        *,
        source: Revision | None,
        target_scope_id: str,
        target_objective_id: str,
        target_branch_id: str,
        parent_revision_ids: tuple[str, ...],
        state: SemanticState,
        operation: OperationKind,
        inlet: ContinuationInlet | None,
        projection: ResumptionProjection | None,
        reconciliation: dict[str, Any],
        admission: AdmissionDecision,
        semantic_outcome: SemanticOutcome,
        realignment: Realignment | None,
        proposal: ReductionProposal | None = None,
    ) -> tuple[Revision, TransitionArtifact]:
        revision_id = self._id_factory("revision")
        artifact_id = self._id_factory("transition")
        identity = ResumptionIdentity(
            scope_id=target_scope_id,
            objective_id=target_objective_id,
            branch_id=target_branch_id,
            revision_id=revision_id,
            state_digest=state.digest,
        )
        revision = Revision(
            identity=identity,
            parent_revision_ids=parent_revision_ids,
            state=state,
            provenance_references=tuple(
                dict.fromkeys(
                    (
                        *(source.provenance_references if source else ()),
                        *(inlet.provenance if inlet else ()),
                        *((inlet.inlet_id,) if inlet else ()),
                    )
                )
            ),
            governance_references=admission.governance_references,
            transition_artifact_id=artifact_id,
            revision_digest="",
            created_at=self._clock(),
        )
        revision = replace(
            revision,
            revision_digest=content_digest(revision.canonical_content()),
        )
        artifact = TransitionArtifact(
            artifact_id=artifact_id,
            source_identity=source.identity if source else None,
            source_revision_digest=source.revision_digest if source else None,
            projection_policy=(
                projection.policy if projection else ProjectionPolicy()
            ),
            projection_digest=(
                projection.projection_digest if projection else None
            ),
            projection_completeness_statement=(
                projection.completeness_statement
                if projection
                else "Initial objective has no source projection."
            ),
            inlet_id=inlet.inlet_id if inlet else None,
            inlet_digest=inlet.digest if inlet else None,
            operation=operation,
            reconciliation=reconciliation,
            proposal_references=(
                proposal.proposal_references if proposal else ()
            ),
            admission=admission,
            admitted_delta={
                "state_digest": state.digest,
                "achieved_item_ids": [item.item_id for item in state.achieved],
                "non_achievedness_item_ids": [
                    item.item_id for item in state.non_achievedness
                ],
            },
            rejected_delta={},
            superseded_delta={
                "edges": list(state.supersession_edges)
            },
            conflicting_delta={"conflicts": dict(state.conflicts)},
            unresolved_delta={
                "applicability_item_ids": list(
                    state.unresolved_applicability_item_ids
                )
            },
            hold_evaluation={
                "active_hold_ids": [
                    hold.hold_id for hold in _active_holds(state)
                ],
                "evaluations": list(state.hold_evaluations),
            },
            capability_receipt_references=(
                proposal.capability_receipt_references if proposal else ()
            ),
            effect_receipt_references=(
                proposal.effect_receipt_references if proposal else ()
            ),
            semantic_outcome=semantic_outcome,
            resulting_revision_id=revision.identity.revision_id,
            resulting_revision_digest=revision.revision_digest,
            decision_flow_signature="",
            realignment=realignment,
            projection_artifact=(
                {
                    **projection.canonical_content(),
                    "projection_digest": projection.projection_digest,
                }
                if projection is not None
                else None
            ),
            inlet_artifact=inlet.to_dict() if inlet is not None else None,
            proposal_interactions=(
                proposal.proposal_interactions if proposal else ()
            ),
        )
        artifact = replace(
            artifact,
            decision_flow_signature=(
                artifact.expected_decision_flow_signature
            ),
        )
        return revision, artifact

    def _non_committing_work_result(
        self,
        attempt: AttemptRecord,
        *,
        source: Revision | None,
        operation: OperationKind,
        inlet: ContinuationInlet | None,
        projection: ResumptionProjection | None,
        outcome: SemanticOutcome,
        rationale: str,
        diagnostics: dict[str, Any] | None = None,
    ) -> AttemptWorkResult:
        admission = AdmissionDecision(
            disposition=(
                AdmissionDisposition.CLARIFICATION_REQUIRED
                if outcome is SemanticOutcome.AMBIGUOUS
                else AdmissionDisposition.REJECTED
            ),
            rationale=rationale,
            checks={"committed": False},
        )
        artifact_id = self._id_factory("transition")
        artifact = TransitionArtifact(
            artifact_id=artifact_id,
            source_identity=source.identity if source else None,
            source_revision_digest=source.revision_digest if source else None,
            projection_policy=(
                projection.policy if projection else ProjectionPolicy()
            ),
            projection_digest=(
                projection.projection_digest if projection else None
            ),
            projection_completeness_statement=(
                projection.completeness_statement
                if projection
                else "No source projection was available."
            ),
            inlet_id=inlet.inlet_id if inlet else None,
            inlet_digest=inlet.digest if inlet else None,
            operation=operation,
            reconciliation={"rationale": rationale},
            proposal_references=(),
            admission=admission,
            admitted_delta={},
            rejected_delta={"rationale": rationale},
            superseded_delta={},
            conflicting_delta={},
            unresolved_delta={},
            hold_evaluation={},
            capability_receipt_references=(),
            effect_receipt_references=(),
            semantic_outcome=outcome,
            resulting_revision_id=None,
            resulting_revision_digest=None,
            decision_flow_signature="",
            projection_artifact=(
                {
                    **projection.canonical_content(),
                    "projection_digest": projection.projection_digest,
                }
                if projection is not None
                else None
            ),
            inlet_artifact=inlet.to_dict() if inlet is not None else None,
        )
        artifact = replace(
            artifact,
            decision_flow_signature=(
                artifact.expected_decision_flow_signature
            ),
        )
        reference = self.repository.append_uncommitted_transition_artifact(
            artifact,
            attempt_id=attempt.attempt_id,
        )
        state = source.state if source else None
        public = ResumptionResult(
            source_revision_identity=source.identity if source else None,
            execution_attempt_id=attempt.attempt_id,
            execution_outcome=AttemptExecutionOutcome.TERMINATED,
            semantic_outcome=outcome,
            resulting_revision_identity=None,
            transition_artifact_reference=reference,
            attempt_artifact_reference=(
                self.repository.attempt_artifact_reference(attempt.attempt_id)
            ),
            realignment_summary=None,
            identity_disposition=None,
            achieved_state_summary=tuple(
                item.item_id for item in (state.achieved if state else ())
            ),
            non_achievedness_summary=tuple(
                item.item_id
                for item in (state.non_achievedness if state else ())
            ),
            active_hold_summary=tuple(
                hold.hold_id
                for hold in (_active_holds(state) if state else ())
            ),
            diagnostics={"rationale": rationale, **(diagnostics or {})},
        )
        return AttemptWorkResult(
            semantic_outcome=outcome.value,
            latest_admitted_revision_id=(
                source.identity.revision_id if source else None
            ),
            transition_artifact_references=(artifact_id,),
            payload={"resumption_result": public},
        )

    def _result_for_revision(
        self,
        *,
        attempt_id: str,
        source: Revision | None,
        revision: Revision,
        artifact: TransitionArtifact,
        semantic_outcome: SemanticOutcome,
        presentation: dict[str, Any],
    ) -> ResumptionResult:
        realignment = artifact.realignment
        return ResumptionResult(
            source_revision_identity=source.identity if source else None,
            execution_attempt_id=attempt_id,
            execution_outcome=AttemptExecutionOutcome.TERMINATED,
            semantic_outcome=semantic_outcome,
            resulting_revision_identity=revision.identity,
            transition_artifact_reference=(
                self.repository.transition_artifact_reference(
                    artifact.artifact_id
                )
            ),
            attempt_artifact_reference=(
                self.repository.attempt_artifact_reference(attempt_id)
            ),
            realignment_summary=(
                realignment.to_dict() if realignment is not None else None
            ),
            identity_disposition=(
                realignment.identity_disposition
                if realignment is not None
                else None
            ),
            achieved_state_summary=tuple(
                item.item_id for item in revision.state.achieved
            ),
            non_achievedness_summary=tuple(
                item.item_id for item in revision.state.non_achievedness
            ),
            active_hold_summary=tuple(
                hold.hold_id for hold in _active_holds(revision.state)
            ),
            diagnostics={
                "revision_digest": revision.revision_digest,
                "state_digest": revision.identity.state_digest,
            },
            presentation=presentation,
        )

    def _public_result(
        self,
        run_result: AttemptRunResult,
        *,
        source_revision: Revision | None,
    ) -> ResumptionResult:
        if run_result.work_result is not None:
            candidate = run_result.work_result.payload.get("resumption_result")
            if isinstance(candidate, ResumptionResult):
                return replace(
                    candidate,
                    execution_outcome=run_result.outcome,
                )

        latest = (
            self.repository.load_revision(
                run_result.attempt.latest_admitted_revision_id
            )
            if run_result.attempt.latest_admitted_revision_id
            else source_revision
        )
        semantic_outcome: SemanticOutcome | None = None
        transition_reference: str | None = None
        if run_result.attempt.transition_artifact_references:
            artifact_id = run_result.attempt.transition_artifact_references[-1]
            artifact = self.repository.load_transition_artifact(artifact_id)
            transition_reference = self.repository.transition_artifact_reference(
                artifact_id
            )
            if artifact is not None:
                semantic_outcome = SemanticOutcome(artifact["semantic_outcome"])
        return ResumptionResult(
            source_revision_identity=(
                source_revision.identity if source_revision else None
            ),
            execution_attempt_id=run_result.attempt.attempt_id,
            execution_outcome=run_result.outcome,
            semantic_outcome=semantic_outcome,
            resulting_revision_identity=(latest.identity if latest else None),
            transition_artifact_reference=transition_reference,
            attempt_artifact_reference=(
                self.repository.attempt_artifact_reference(
                    run_result.attempt.attempt_id
                )
            ),
            realignment_summary=None,
            identity_disposition=None,
            achieved_state_summary=tuple(
                item.item_id for item in (latest.state.achieved if latest else ())
            ),
            non_achievedness_summary=tuple(
                item.item_id
                for item in (latest.state.non_achievedness if latest else ())
            ),
            active_hold_summary=tuple(
                hold.hold_id
                for hold in (_active_holds(latest.state) if latest else ())
            ),
            diagnostics={
                "operational_error": run_result.error,
                "semantic_state_changed_by_interruption": False,
            },
        )

    # Inspection and governance -----------------------------------------------

    def _inspection_revision(self, request: InspectionRequest) -> Revision:
        if request.target_kind is InspectionTargetKind.REVISION:
            revision = self.repository.load_revision(request.target_id)
        elif request.target_kind is InspectionTargetKind.BRANCH_HEAD:
            if not all(
                (request.scope_id, request.objective_id, request.branch_id)
            ):
                raise ValueError(
                    "branch-head inspection requires scope, objective, and branch"
                )
            revision = self.repository.load_branch_head(
                request.scope_id or "",
                request.objective_id or "",
                request.branch_id or "",
            )
        else:
            raise ValueError(
                f"unsupported revision inspection target: {request.target_kind}"
            )
        if revision is None:
            raise KeyError(f"unknown semantic revision: {request.target_id}")
        return revision

    def _revision_inspection_payload(
        self,
        revision: Revision,
        view: InspectionView,
    ) -> dict[str, Any]:
        if view is InspectionView.CURRENT_STATE:
            return revision.state.to_dict()
        if view is InspectionView.NON_ACHIEVEDNESS:
            return {
                "items": [
                    item.to_dict() for item in revision.state.non_achievedness
                ]
            }
        if view is InspectionView.GOVERNING_DIRECTION:
            return revision.state.governing_direction.to_dict()
        if view is InspectionView.REALIGNMENT:
            return {
                "realignments": [
                    item.to_dict() for item in revision.state.realignments
                ]
            }
        if view is InspectionView.PATH:
            return {
                "revision_ids": list(
                    self.repository.path_to_roots(revision.identity.revision_id)
                )
            }
        if view is InspectionView.PROVENANCE:
            return {
                "provenance_references": list(
                    revision.provenance_references
                ),
                "governance_references": list(
                    revision.governance_references
                ),
                "supersession_edges": list(
                    revision.state.supersession_edges
                ),
            }
        if view is InspectionView.BRANCH_GRAPH:
            return self.repository.branch_graph(revision.identity.objective_id)
        if view is InspectionView.TRANSITION:
            artifact = self.repository.load_transition_artifact(
                revision.transition_artifact_id
            )
            return artifact or {}
        if view is InspectionView.RECONSTRUCTION:
            return {
                "revision": {
                    **revision.canonical_content(),
                    "revision_digest": revision.revision_digest,
                    "created_at": revision.created_at,
                },
                "transition_artifact": (
                    self.repository.load_transition_artifact(
                        revision.transition_artifact_id
                    )
                ),
            }
        raise ValueError(f"view {view.value} does not apply to a revision")

    @staticmethod
    def _authorize_inspection(
        request: InspectionRequest,
        revision: Revision,
    ) -> None:
        ResumptionService._authorize_inspection_scope(
            request,
            revision.identity.scope_id,
        )

    def _authorize_attempt_inspection(
        self,
        request: InspectionRequest,
        attempt: AttemptRecord,
    ) -> None:
        scope_id: str | None = None
        if attempt.latest_admitted_revision_id is not None:
            revision = self.repository.load_revision(
                attempt.latest_admitted_revision_id
            )
            scope_id = revision.identity.scope_id if revision else None
        elif attempt.causal_anchor.startswith("start:"):
            scope_id = attempt.causal_anchor.removeprefix("start:").split(
                "/", 1
            )[0]
        else:
            try:
                scope_id = str(json.loads(attempt.causal_anchor)["scope_id"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                scope_id = None
        self._authorize_inspection_scope(request, scope_id)

    def _authorize_transition_inspection(
        self,
        request: InspectionRequest,
        payload: dict[str, Any],
    ) -> None:
        source_identity = payload.get("source_identity")
        scope_id = (
            str(source_identity.get("scope_id"))
            if isinstance(source_identity, dict)
            and source_identity.get("scope_id") is not None
            else None
        )
        if scope_id is None and payload.get("resulting_revision_id"):
            revision = self.repository.load_revision(
                str(payload["resulting_revision_id"])
            )
            scope_id = revision.identity.scope_id if revision else None
        self._authorize_inspection_scope(request, scope_id)

    @staticmethod
    def _authorize_inspection_scope(
        request: InspectionRequest,
        scope_id: str | None,
    ) -> None:
        allowed = set(
            request.authority_context.get("allowed_scope_ids", ())
        )
        if allowed and scope_id not in allowed:
            raise PermissionError(
                f"principal {request.principal!r} cannot inspect this scope"
            )

    @staticmethod
    def _default_admission_evaluator(
        operation: OperationKind,
        source: Revision | None,
        inlet: ContinuationInlet | None,
        candidate: SemanticState,
        governance_policy: dict[str, Any],
        execution_policy: dict[str, Any],
    ) -> AdmissionDecision:
        if governance_policy.get("revoked"):
            return AdmissionDecision(
                disposition=AdmissionDisposition.REJECTED,
                rationale="governance authority is revoked",
                checks={"authority_current": False},
            )
        if governance_policy.get("expired"):
            return AdmissionDecision(
                disposition=AdmissionDisposition.REJECTED,
                rationale="governance authority is expired",
                checks={"authority_current": False},
            )
        if governance_policy.get("authorized", True) is not True:
            return AdmissionDecision(
                disposition=AdmissionDisposition.REJECTED,
                rationale="the transition is not authorized",
                checks={"authority_current": False},
            )
        required = set(governance_policy.get("required_capabilities", ()))
        available = set(execution_policy.get("available_capabilities", ()))
        if not required.issubset(available):
            return AdmissionDecision(
                disposition=AdmissionDisposition.REJECTED,
                rationale="required current host capabilities are unavailable",
                checks={
                    "missing_capabilities": sorted(required - available)
                },
            )
        return AdmissionDecision(
            disposition=AdmissionDisposition.ACCEPTED,
            rationale="mechanical identity, lifecycle, and authority checks passed",
            governance_references=tuple(
                governance_policy.get("governance_references", ())
            ),
            checks={
                "identity_verified": True,
                "authority_current": True,
                "capabilities_current": True,
                "operation": operation.value,
                "source_revision_id": (
                    source.identity.revision_id if source else None
                ),
                "inlet_id": inlet.inlet_id if inlet else None,
                "candidate_state_digest": candidate.digest,
            },
        )

    # Small helpers ------------------------------------------------------------

    def _require_running_attempt(self, attempt_id: str) -> AttemptRecord:
        attempt = self.repository.load_attempt(attempt_id)
        if attempt is None or attempt.status is not AttemptLifecycleStatus.RUNNING:
            raise RuntimeError(f"prepared work has no running attempt: {attempt_id}")
        return attempt

    @staticmethod
    def _raise_if_stopped(should_stop: Callable[[], bool]) -> None:
        if should_stop():
            raise AttemptInterrupted()

    @staticmethod
    def _add_item(
        achieved: dict[str, SemanticItem],
        non_achieved: dict[str, SemanticItem],
        item: SemanticItem,
        *,
        destination: str,
    ) -> None:
        existing = achieved.get(item.item_id) or non_achieved.get(item.item_id)
        if existing is not None and existing != item:
            raise TransitionValidationError(
                f"semantic identity collision for {item.item_id}",
                outcome=SemanticOutcome.AMBIGUOUS,
            )
        if destination == "achieved":
            non_achieved.pop(item.item_id, None)
            achieved[item.item_id] = item
        else:
            if item.item_id not in achieved:
                non_achieved[item.item_id] = item

    @staticmethod
    def _validate_identity_disposition(
        source: ResumptionIdentity,
        disposition: IdentityDisposition,
        target: tuple[str, str, str],
    ) -> None:
        if target != (
            disposition.target_scope_id,
            disposition.target_objective_id,
            disposition.target_branch_id,
        ):
            raise TransitionValidationError(
                "realignment target does not match identity disposition"
            )
        if disposition.kind is IdentityDispositionKind.SAME_OBJECTIVE:
            if target != (source.scope_id, source.objective_id, source.branch_id):
                raise TransitionValidationError(
                    "same-objective realignment cannot silently change identity"
                )
        elif disposition.kind is IdentityDispositionKind.BRANCH:
            if (
                target[0] != source.scope_id
                or target[1] != source.objective_id
                or target[2] == source.branch_id
            ):
                raise TransitionValidationError(
                    "branch realignment requires a distinct branch of the same objective"
                )
        elif disposition.kind is IdentityDispositionKind.DERIVED_OBJECTIVE:
            if target[1] == source.objective_id:
                raise TransitionValidationError(
                    "derived-objective realignment requires a new objective identity"
                )

    def _stable_item_id(self, prefix: str, value: Any) -> str:
        return f"{prefix}_{content_digest(value)[:24]}"


def _delta_is_empty(delta: SemanticDelta) -> bool:
    return not any(
        (
            delta.achieved,
            delta.non_achievedness,
            delta.resolved_non_achievedness_ids,
            delta.holds,
            delta.resolved_hold_ids,
            delta.supersessions,
            delta.governing_direction is not None,
        )
    )


def _redact_non_inline_semantic_context(
    state: SemanticState,
    inline_item_ids: set[str],
) -> SemanticState:
    """Keep only context mechanically attributable to inline semantic items."""

    inline_items = {
        item.item_id: item
        for item in (*state.achieved, *state.non_achievedness)
        if item.item_id in inline_item_ids
    }
    inline_node_ids = {
        str(node.get("id"))
        for item in inline_items.values()
        if isinstance((node := item.payload.get("node")), dict)
        and node.get("id") is not None
    }
    allowed_ids = inline_item_ids | inline_node_ids

    graph_nodes = [
        dict(node)
        for node in state.refinement_graph.get("nodes", ())
        if str(node.get("id")) in inline_node_ids
    ]
    graph_edges = [
        dict(edge)
        for edge in state.refinement_graph.get("edges", ())
        if str(edge.get("src")) in inline_node_ids
        and str(edge.get("dst")) in inline_node_ids
    ]

    def keyed(values: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value for key, value in values.items() if key in allowed_ids
        }

    def attributable(values: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
        return tuple(
            value
            for value in values
            if str(value.get("item_id") or value.get("node_id") or "")
            in allowed_ids
        )

    holds = tuple(
        hold
        for hold in state.holds
        if str(hold.unresolved_semantic_object.get("item_id", ""))
        in inline_item_ids
    )
    hold_ids = {hold.hold_id for hold in holds}
    return replace(
        state,
        refinement_graph={"nodes": graph_nodes, "edges": graph_edges},
        duties_and_obligations=attributable(state.duties_and_obligations),
        certainty=keyed(state.certainty),
        blockers=keyed(state.blockers),
        conflicts=keyed(state.conflicts),
        evidence_and_support={},
        commitments=attributable(state.commitments),
        supersession_edges=tuple(
            edge
            for edge in state.supersession_edges
            if str(edge.get("prior_item_id", "")) in inline_item_ids
            and (
                edge.get("replacement_item_id") is None
                or str(edge.get("replacement_item_id")) in inline_item_ids
            )
        ),
        contradiction_edges=tuple(
            edge
            for edge in state.contradiction_edges
            if {
                str(edge.get("left_item_id", "")),
                str(edge.get("right_item_id", "")),
            }.issubset(inline_item_ids)
        ),
        realignments=(),
        unresolved_applicability_item_ids=tuple(
            item_id
            for item_id in state.unresolved_applicability_item_ids
            if item_id in inline_item_ids
        ),
        holds=holds,
        hold_evaluations=tuple(
            evaluation
            for evaluation in state.hold_evaluations
            if str(evaluation.get("hold_id", "")) in hold_ids
        ),
        provenance_references=(),
    )


def _infer_semantic_outcome(state: SemanticState) -> SemanticOutcome:
    if _active_holds(state):
        return SemanticOutcome.PAUSED
    if state.conflicts:
        return SemanticOutcome.CONFLICTED
    if state.non_achievedness:
        return SemanticOutcome.INCOMPLETE
    return SemanticOutcome.COMPLETED


def _active_holds(state: SemanticState) -> tuple[Any, ...]:
    return tuple(
        hold
        for hold in state.holds
        if hold.disposition is HoldDisposition.REMAIN_HELD
    )


def _attempt_payload(attempt: AttemptRecord) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "causal_anchor": attempt.causal_anchor,
        "operation": attempt.operation,
        "execution_policy": dict(attempt.execution_policy),
        "status": attempt.status.value,
        "latest_admitted_revision_id": attempt.latest_admitted_revision_id,
        "proposal_references": list(attempt.proposal_references),
        "receipt_references": list(attempt.receipt_references),
        "transition_artifact_references": list(
            attempt.transition_artifact_references
        ),
        "interruption_cause": attempt.interruption_cause,
        "interruption_correlation": dict(attempt.interruption_correlation),
        "operational_error": attempt.operational_error,
        "created_at": attempt.created_at,
        "updated_at": attempt.updated_at,
    }


__all__ = [
    "AdmissionEvaluator",
    "ResumptionService",
    "TransitionValidationError",
]
