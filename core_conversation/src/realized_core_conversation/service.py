"""Transport-neutral conversation application above the governed engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any
import uuid

from realized_core_engine import (
    ContinuationInlet,
    EngineConfiguration,
    GoverningDirection,
    IdentityDisposition,
    IdentityDispositionKind,
    InletRelationship,
    InspectionRequest,
    InspectionTargetKind,
    InspectionView,
    InterruptionRequest,
    OperationKind,
    Realignment,
    Reversal,
    ResumptionEngine,
    ResumptionIdentity,
    ResumptionRequest,
    ResumptionResult,
    SemanticDelta,
    SemanticItem,
    SemanticOutcome,
    StartRequest,
    Supersession,
    open_resumption_engine,
)

from realized_core_conversation.contracts import (
    ConversationTurnPlan,
    CorrectionPlan,
    RealignmentPlan,
    ReversalPlan,
)
from realized_core_conversation.identity import (
    canonical_payload_digest,
    stable_contribution_id,
    stable_normalized_request_id,
    stable_planning_attempt_id,
    stable_receipt_id,
    stable_recovery_decision_id,
    stable_rendering_attempt_id,
    stable_result_id,
)
from realized_core_conversation.journal import (
    SQLiteConversationActivityJournal,
)
from realized_core_conversation.ports import (
    ConversationActivityJournal,
    SemanticResumptionPort,
)
from realized_core_conversation.schemas import (
    ConversationActivityStatus,
    ConversationReceipt,
    ConversationRecordKind,
    ContributionRecord,
    NormalizedRequestRecord,
    PlanningProposalRecord,
    RecoveryDecisionRecord,
    RenderingRecord,
    StructuredResultRecord,
)
from realized_core_llm import (
    ConversationIdentityDisposition,
    ConversationOperation,
    ConversationPlanProposal,
    ConversationPlanner,
    ConversationPlanningContext,
    ConversationPlanningError,
    ConversationPlanningResult,
    ConversationRenderContext,
    ConversationRenderResult,
    ConversationRenderer,
    PLANNING_PROMPT_VERSION,
    PLANNING_SCHEMA_VERSION,
    RENDERING_PROMPT_VERSION,
    RENDERING_SCHEMA_VERSION,
    SemanticItemProposal,
)


_TREATMENTS = {"independent", "human_contribution", "follow_up", "correction"}


def _engine_operation(
    value: ConversationOperation | OperationKind,
) -> OperationKind:
    """Translate the provider-facing operation at the application boundary."""

    return OperationKind(value.value)


def _conversation_operation(
    value: OperationKind,
) -> ConversationOperation:
    """Expose an admitted engine operation to the rendering boundary."""

    return ConversationOperation(value.value)


def _engine_identity_disposition(
    value: ConversationIdentityDisposition | IdentityDispositionKind,
) -> IdentityDispositionKind:
    """Translate an advisory identity proposal to the engine ABI."""

    return IdentityDispositionKind(value.value)


def _ground_redirect_identity_disposition(
    disposition: IdentityDispositionKind,
    prompt: str,
) -> IdentityDispositionKind:
    if disposition is not IdentityDispositionKind.DERIVED_OBJECTIVE:
        return disposition
    normalized = _selector_token(prompt)
    explicitly_new = re.search(
        r"\b(?:new|separate|derived|distinct|independent) "
        r"(?:objective|goal|project|workstream)\b",
        normalized,
    )
    return (
        disposition
        if explicitly_new is not None
        else IdentityDispositionKind.SAME_OBJECTIVE
    )


def _normalize_operation_control_fields(
    proposal: ConversationPlanProposal,
    operation: OperationKind,
) -> tuple[ConversationPlanProposal, tuple[str, ...]]:
    direct_semantic_operations = frozenset(
        {
            OperationKind.START,
            OperationKind.CONTINUE,
            OperationKind.DERIVE,
            OperationKind.RESUME_SUSPENDED,
            OperationKind.AUGMENT,
        }
    )
    exclusive_fields: tuple[
        tuple[str, Any, frozenset[OperationKind]], ...
    ] = (
        (
            "achieved_items",
            proposal.achieved_items,
            direct_semantic_operations,
        ),
        (
            "non_achieved_items",
            proposal.non_achieved_items,
            direct_semantic_operations,
        ),
        (
            "selected_selectors",
            proposal.selected_selectors,
            frozenset({OperationKind.DERIVE}),
        ),
        (
            "promote_selectors",
            proposal.promote_selectors,
            frozenset({OperationKind.CORRECT}),
        ),
        (
            "resolved_selectors",
            proposal.resolved_selectors,
            frozenset(
                {
                    OperationKind.CORRECT,
                    OperationKind.RESUME_SUSPENDED,
                }
            ),
        ),
        (
            "resolved_applicability_selectors",
            proposal.resolved_applicability_selectors,
            frozenset({OperationKind.CORRECT}),
        ),
        (
            "corrections",
            proposal.corrections,
            frozenset({OperationKind.CORRECT}),
        ),
        (
            "affected_selectors",
            proposal.affected_selectors,
            frozenset({OperationKind.REDIRECT_AND_REALIGN}),
        ),
        (
            "retained_selectors",
            proposal.retained_selectors,
            frozenset({OperationKind.REDIRECT_AND_REALIGN}),
        ),
        (
            "superseded_selectors",
            proposal.superseded_selectors,
            frozenset({OperationKind.REDIRECT_AND_REALIGN}),
        ),
        (
            "unresolved_selectors",
            proposal.unresolved_selectors,
            frozenset({OperationKind.REDIRECT_AND_REALIGN}),
        ),
        (
            "introduced_items",
            proposal.introduced_items,
            frozenset({OperationKind.REDIRECT_AND_REALIGN}),
        ),
        (
            "target_branch",
            proposal.target_branch,
            frozenset(
                {OperationKind.BRANCH, OperationKind.REDIRECT_AND_REALIGN}
            ),
        ),
        (
            "merge_branch_aliases",
            proposal.merge_branch_aliases,
            frozenset({OperationKind.MERGE}),
        ),
        (
            "reversal_selector",
            proposal.reversal_selector,
            frozenset({OperationKind.REVERSE}),
        ),
    )
    ignored = tuple(sorted(
        name
        for name, value, allowed_operations in exclusive_fields
        if value and operation not in allowed_operations
    ))
    if not ignored:
        return proposal, ()
    updates = {
        name: "" if isinstance(getattr(proposal, name), str) else ()
        for name in ignored
    }
    return replace(proposal, **updates), ignored


@dataclass
class CoreConversationHost:
    """Own transcript and explicit turn/revision routing above the engine."""

    root: Path
    configuration: EngineConfiguration
    engine: SemanticResumptionPort | None = None
    journal: ConversationActivityJournal | None = None

    @classmethod
    def open(
        cls,
        *,
        root: Path,
        max_steps: int = 256,
        llm_policy: str = "auto",
        sqlite_path: Path | None = None,
    ) -> CoreConversationHost:
        """Open the application service without exposing engine composition."""

        if llm_policy not in {"off", "auto", "required"}:
            raise ValueError(f"Unsupported LLM policy: {llm_policy}")
        return cls(
            root=root,
            configuration=EngineConfiguration(
                sqlite_path=sqlite_path,
                max_steps=max(0, int(max_steps)),
                llm_policy=llm_policy,
            ),
        )

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for name in (
            "MESSAGES.jsonl",
            "PLANNING_RECEIPTS.jsonl",
            "TURN_PLANS.jsonl",
            "ENGINE_REQUESTS.jsonl",
            "RUN_BINDINGS.jsonl",
            "RENDERING_RECEIPTS.jsonl",
        ):
            path = self.root / name
            if not path.exists():
                path.write_text("", encoding="utf-8")
        session_path = self.root / "SESSION.json"
        if not session_path.exists():
            _write_json(
                session_path,
                {
                    "session_id": f"session_{uuid.uuid4().hex}",
                    "scope_id": f"conversation_{uuid.uuid4().hex}",
                },
            )
        if self.engine is None:
            self.engine = open_resumption_engine(
                configuration=replace(
                    self.configuration,
                    sqlite_path=self.sqlite_path,
                    state_output_path=None,
                    inlets=(),
                )
            )
        if self.journal is None:
            self.journal = SQLiteConversationActivityJournal(self.sqlite_path)

    @property
    def sqlite_path(self) -> Path:
        selected = self.configuration.sqlite_path or (self.root / "artifacts.sqlite3")
        return Path(selected).expanduser().resolve()

    @property
    def scope_id(self) -> str:
        return str(_read_json(self.root / "SESSION.json")["scope_id"])

    @property
    def session_id(self) -> str:
        return str(_read_json(self.root / "SESSION.json")["session_id"])

    def submit(
        self,
        prompt: str,
        *,
        treatment: str = "independent",
        parent_run_id: str = "",
        target_hold_id: str = "",
        selected_item_ids: tuple[str, ...] = (),
        correction_target_item_id: str = "",
        inlet_payload: dict[str, Any] | None = None,
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Submit one legacy treatment through the typed turn-plan boundary."""

        normalized_prompt = str(prompt or "").strip()
        normalized_treatment = str(treatment or "independent").strip().casefold()
        if not normalized_prompt:
            raise ValueError("Prompt is required.")
        if normalized_treatment not in _TREATMENTS:
            raise ValueError(f"Unsupported governed turn treatment: {treatment}")

        if normalized_treatment == "independent":
            plan = ConversationTurnPlan(
                operation=OperationKind.START,
                prompt=normalized_prompt,
                treatment_label=normalized_treatment,
                inlet_payload=dict(inlet_payload or {}),
            )
        elif normalized_treatment == "human_contribution":
            binding, _, state = self._parent_context(parent_run_id)
            selected_hold = _select_active_hold(state, target_hold_id)
            plan = ConversationTurnPlan(
                operation=(
                    OperationKind.RESUME_SUSPENDED
                    if selected_hold is not None
                    else OperationKind.CONTINUE
                ),
                prompt=normalized_prompt,
                parent_run_id=str(binding["run_id"]),
                target_hold_id=str((selected_hold or {}).get("hold_id", "")),
                treatment_label=normalized_treatment,
                inlet_kind="human_contribution",
                inlet_payload=dict(inlet_payload or {}),
            )
        elif normalized_treatment == "follow_up":
            binding, _, state = self._parent_context(parent_run_id)
            achieved_ids = {
                str(item["item_id"]) for item in state.get("achieved", ())
            }
            selected = tuple(dict.fromkeys(selected_item_ids))
            if not selected and len(achieved_ids) == 1:
                selected = tuple(achieved_ids)
            if not selected or not set(selected).issubset(achieved_ids):
                raise ValueError(
                    "Select one or more admitted achieved items for the follow-up."
                )
            plan = ConversationTurnPlan(
                operation=OperationKind.DERIVE,
                prompt=normalized_prompt,
                parent_run_id=str(binding["run_id"]),
                selected_item_ids=selected,
                target_scope_id=self.scope_id,
                target_objective_id=f"objective_{uuid.uuid4().hex}",
                target_branch_id="main",
                governing_direction=GoverningDirection(
                    objective=normalized_prompt,
                    scope=self.scope_id,
                    required_outcome="answer the represented follow-up",
                ),
                treatment_label=normalized_treatment,
                inlet_kind="follow_up",
                inlet_payload=dict(inlet_payload or {}),
            )
        else:
            binding, parent_identity, state = self._parent_context(parent_run_id)
            target_item = _resolve_semantic_selector(
                state,
                correction_target_item_id,
            )
            replacement = SemanticItem(
                item_id=f"item_{uuid.uuid4().hex}",
                kind=str(target_item.get("kind", "corrected_item")),
                payload={
                    "text": normalized_prompt,
                    "semantic_key": _semantic_key(target_item),
                },
                provenance_references=(parent_identity.revision_id,),
            )
            plan = ConversationTurnPlan(
                operation=OperationKind.CORRECT,
                prompt=normalized_prompt,
                parent_run_id=str(binding["run_id"]),
                corrections=(
                    CorrectionPlan(
                        target_selector=str(target_item["item_id"]),
                        replacement=replacement,
                        rationale="Explicit user correction.",
                    ),
                ),
                treatment_label=normalized_treatment,
                inlet_kind="correction",
                inlet_payload=dict(inlet_payload or {}),
            )
        return self.submit_plan(
            plan,
            on_attempt_running=on_attempt_running,
        )

    def submit_text(
        self,
        prompt: str,
        *,
        planner: ConversationPlanner,
        parent_run_id: str = "",
        binding_aliases: dict[str, str] | None = None,
        renderer: ConversationRenderer | None = None,
        source_attempt_id: str = "",
        require_existing_binding: bool = False,
        idempotency_key: str = "",
        planning_attempt_key: str = "primary",
        rendering_attempt_key: str = "primary",
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Interpret ordinary language without delegating causal identity."""

        normalized_prompt = str(prompt or "").strip()
        if not normalized_prompt:
            raise ValueError("Prompt is required.")
        contribution = self._accept_contribution(
            normalized_prompt,
            idempotency_key=idempotency_key,
            parent_run_id=parent_run_id,
        )
        turn_id, user_message = self._begin_turn(
            normalized_prompt,
            contribution_id=contribution.contribution_id,
        )
        planning_attempt_id = stable_planning_attempt_id(
            contribution.contribution_id,
            planning_attempt_key,
        )

        parent_binding: dict[str, Any] | None = None
        parent_identity: ResumptionIdentity | None = None
        parent_state: dict[str, Any] | None = None
        if contribution.selected_binding is not None:
            parent_binding = dict(contribution.selected_binding)
            parent_identity = ResumptionIdentity.from_dict(
                dict(parent_binding["resumption_identity"])
            )
            parent_state = self._inspect_state(parent_identity)
        elif parent_run_id:
            raise ValueError(
                f"No governed run binding is available for run {parent_run_id}."
            )

        aliases = dict(binding_aliases or {})
        context = ConversationPlanningContext(
            prompt=normalized_prompt,
            scope_id=self.scope_id,
            parent_run_id=(
                str(parent_binding["run_id"])
                if parent_binding is not None
                else ""
            ),
            parent_identity=(
                parent_identity.to_dict()
                if parent_identity is not None
                else None
            ),
            current_state=(
                dict(parent_state) if parent_state is not None else None
            ),
            binding_aliases=aliases,
            interrupted_attempt_available=bool(source_attempt_id.strip()),
        )
        context_payload = context.public_payload()
        context_digest = canonical_payload_digest(context_payload)
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        existing_proposal = self.journal.get(
            ConversationRecordKind.PROPOSAL,
            planning_attempt_id,
        )
        if existing_proposal is not None:
            if not isinstance(existing_proposal, PlanningProposalRecord):
                raise TypeError("The planning identity names another record type.")
            if (
                existing_proposal.contribution_id
                != contribution.contribution_id
                or existing_proposal.planning_context_digest
                != context_digest
            ):
                raise ValueError(
                    "The planning attempt identity names another context."
                )
            if (
                existing_proposal.status
                is not ConversationActivityStatus.SUCCEEDED
            ):
                message = str(
                    existing_proposal.error.get(
                        "error",
                        "The prior planning attempt did not produce a plan.",
                    )
                )
                raise ConversationPlanningError(message)
            if not existing_proposal.normalized_plan:
                raise ConversationPlanningError(
                    "The prior planning record predates recoverable normalized "
                    "plans; use a new planning attempt key."
                )
            self._record_recovery_decision(
                contribution_id=contribution.contribution_id,
                stage="planning",
                action="reuse_normalized_plan",
                reason=(
                    "The stable planning attempt already has a validated "
                    "normalized plan."
                ),
                linked_record_ids={
                    "planning_attempt_id": planning_attempt_id,
                },
            )
            recovered_plan = ConversationTurnPlan.from_dict(
                existing_proposal.normalized_plan
            )
            report = self._execute_plan(
                recovered_plan,
                turn_id=turn_id,
                user_message=user_message,
                contribution=contribution,
                planning_attempt_id=planning_attempt_id,
                rendering_attempt_key=rendering_attempt_key,
                renderer=renderer,
                on_attempt_running=on_attempt_running,
            )
            report["planning"] = {
                "status": "recovered",
                "planning_attempt_id": planning_attempt_id,
                "normalized_plan": existing_proposal.normalized_plan,
            }
            return report
        self._record_receipt(
            stage="planning_request",
            status=ConversationActivityStatus.RUNNING,
            contribution_id=contribution.contribution_id,
            correlation_ids={
                "planning_attempt_id": planning_attempt_id,
            },
            payload={
                "context": context_payload,
                "planner": type(planner).__name__,
                "planning_schema_version": PLANNING_SCHEMA_VERSION,
                "prompt_version": PLANNING_PROMPT_VERSION,
            },
            receipt_key="request",
        )
        planning_started = time.perf_counter()
        planning_record: dict[str, Any] = {
            "turn_id": turn_id,
            "user_message_id": user_message["message_id"],
            "contribution_id": contribution.contribution_id,
            "planning_attempt_id": planning_attempt_id,
            "context": context_payload,
            "planner": type(planner).__name__,
        }
        if require_existing_binding and parent_identity is None:
            planning_record.update(
                {
                    "status": "unresolved",
                    "error": "An exact causal binding is required.",
                    "elapsed_seconds": round(
                        time.perf_counter() - planning_started,
                        6,
                    ),
                }
            )
            _append_jsonl(
                self.root / "PLANNING_RECEIPTS.jsonl",
                planning_record,
            )
            self._record_proposal(
                planning_attempt_id=planning_attempt_id,
                contribution_id=contribution.contribution_id,
                context_digest=context_digest,
                status=ConversationActivityStatus.UNRESOLVED,
                error={
                    "error_type": "ConversationPlanningError",
                    "error": "An exact causal binding is required.",
                },
            )
            raise ConversationPlanningError(
                "An exact causal binding is required; similarity or prose "
                "cannot select one."
            )

        planned: ConversationPlanningResult | None = None
        proposal: ConversationPlanProposal | None = None
        try:
            planned = planner.propose(context)
            if not isinstance(planned, ConversationPlanningResult):
                raise ConversationPlanningError(
                    "The planner returned no provider-neutral planning result."
                )
            proposal = planned.proposal
            planning_record.update(
                {
                    "proposal": proposal.to_dict(),
                    "provider_receipt": dict(planned.receipt),
                }
            )
            if proposal.unresolved_interpretation:
                raise ConversationPlanningError(
                    "Unresolved conversation interpretation: "
                    + "; ".join(proposal.unresolved_interpretation)
                )
            if proposal.operation is None:
                raise ConversationPlanningError(
                    "The conversation operation is unresolved."
                )
            plan = self._materialize_proposal(
                proposal,
                prompt=normalized_prompt,
                parent_binding=parent_binding,
                parent_identity=parent_identity,
                parent_state=parent_state,
                binding_aliases=aliases,
                source_attempt_id=source_attempt_id,
                turn_id=turn_id,
                message_id=str(user_message["message_id"]),
            )
        except Exception as exc:
            planning_record.update(
                {
                    "status": "unresolved",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "elapsed_seconds": round(
                        time.perf_counter() - planning_started,
                        6,
                    ),
                }
            )
            _append_jsonl(
                self.root / "PLANNING_RECEIPTS.jsonl",
                planning_record,
            )
            self._record_proposal(
                planning_attempt_id=planning_attempt_id,
                contribution_id=contribution.contribution_id,
                context_digest=context_digest,
                status=ConversationActivityStatus.UNRESOLVED,
                proposal=(proposal.to_dict() if proposal is not None else {}),
                provider_receipt=(
                    dict(planned.receipt) if planned is not None else {}
                ),
                unresolved_interpretation=(
                    proposal.unresolved_interpretation
                    if proposal is not None
                    else ()
                ),
                schema_version=(
                    planned.schema_version
                    if planned is not None
                    else PLANNING_SCHEMA_VERSION
                ),
                prompt_version=(
                    planned.prompt_version
                    if planned is not None
                    else PLANNING_PROMPT_VERSION
                ),
                error={"error_type": type(exc).__name__, "error": str(exc)},
            )
            if (
                isinstance(exc, ConversationPlanningError)
                and planned is not None
                and planned.receipt
            ):
                raise ConversationPlanningError(
                    str(exc),
                    provider_receipt=planned.receipt,
                ) from exc
            raise

        planning_record.update(
            {
                "status": "proposed",
                "normalized_plan": plan.to_dict(),
                "elapsed_seconds": round(
                    time.perf_counter() - planning_started,
                    6,
                ),
            }
        )
        _append_jsonl(
            self.root / "PLANNING_RECEIPTS.jsonl",
            planning_record,
        )
        assert planned is not None
        assert proposal is not None
        self._record_proposal(
            planning_attempt_id=planning_attempt_id,
            contribution_id=contribution.contribution_id,
            context_digest=context_digest,
            status=ConversationActivityStatus.SUCCEEDED,
            proposal=proposal.to_dict(),
            normalized_plan=plan.to_dict(),
            provider_receipt=dict(planned.receipt),
            unresolved_interpretation=proposal.unresolved_interpretation,
            schema_version=planned.schema_version,
            prompt_version=planned.prompt_version,
        )
        report = self._execute_plan(
            plan,
            turn_id=turn_id,
            user_message=user_message,
            contribution=contribution,
            planning_attempt_id=planning_attempt_id,
            rendering_attempt_key=rendering_attempt_key,
            renderer=renderer,
            on_attempt_running=on_attempt_running,
        )
        report["planning"] = planning_record
        return report

    def submit_plan(
        self,
        plan: ConversationTurnPlan,
        *,
        renderer: ConversationRenderer | None = None,
        idempotency_key: str = "",
        rendering_attempt_key: str = "primary",
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Execute one typed advisory plan against an exact causal binding."""

        normalized_prompt = str(plan.prompt or "").strip()
        if not normalized_prompt:
            raise ValueError("Prompt is required.")
        contribution = self._accept_contribution(
            normalized_prompt,
            idempotency_key=idempotency_key,
            parent_run_id=plan.parent_run_id,
            provenance={"interpretation": "explicit_turn_plan"},
        )
        turn_id, user_message = self._begin_turn(
            normalized_prompt,
            contribution_id=contribution.contribution_id,
        )
        planning_attempt_id = stable_planning_attempt_id(
            contribution.contribution_id,
            "explicit-control",
        )
        plan_payload = plan.to_dict()
        proposal_record = self._record_proposal(
            planning_attempt_id=planning_attempt_id,
            contribution_id=contribution.contribution_id,
            context_digest=canonical_payload_digest(plan_payload),
            status=ConversationActivityStatus.SUCCEEDED,
            proposal=plan_payload,
            normalized_plan=plan_payload,
            schema_version="explicit-control-v1",
            prompt_version="not-applicable",
        )
        if proposal_record.normalized_plan != plan_payload:
            raise ValueError(
                "The contribution idempotency key already names another "
                "explicit turn plan."
            )
        plan = ConversationTurnPlan.from_dict(
            proposal_record.normalized_plan
        )
        return self._execute_plan(
            plan,
            turn_id=turn_id,
            user_message=user_message,
            contribution=contribution,
            planning_attempt_id=planning_attempt_id,
            rendering_attempt_key=rendering_attempt_key,
            renderer=renderer,
            on_attempt_running=on_attempt_running,
        )

    def _execute_plan(
        self,
        plan: ConversationTurnPlan,
        *,
        turn_id: str,
        user_message: dict[str, Any],
        contribution: ContributionRecord,
        planning_attempt_id: str,
        rendering_attempt_key: str,
        renderer: ConversationRenderer | None,
        on_attempt_running: Callable[[str], None] | None,
    ) -> dict[str, Any]:
        """Execute a normalized plan for an already recorded contribution."""

        _append_jsonl(
            self.root / "TURN_PLANS.jsonl",
            {
                "turn_id": turn_id,
                "user_message_id": user_message["message_id"],
                "plan": plan.to_dict(),
            },
        )

        parent_binding: dict[str, Any] | None = None
        parent_identity: ResumptionIdentity | None = None
        parent_state: dict[str, Any] | None = None
        if plan.operation is not OperationKind.START:
            parent_binding, parent_identity, parent_state = self._parent_context(
                plan.parent_run_id
            )

        request = self._request_for_plan(
            plan,
            turn_id=turn_id,
            message_id=str(user_message["message_id"]),
            parent_identity=parent_identity,
            parent_state=parent_state,
        )
        request_payload = {
            "operation": plan.operation.value,
            "request": request.to_dict(),
        }
        normalized_request_id = stable_normalized_request_id(request_payload)
        request_digest = canonical_payload_digest(request_payload)
        request = replace(
            request,
            normalized_request_id=normalized_request_id,
        )
        causal_anchor = (
            parent_identity.to_dict() if parent_identity is not None else {}
        )
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        normalized_record = self.journal.find_normalized_request(
            normalized_request_id
        )
        if normalized_record is None:
            restored_request = self._journal_put(
                NormalizedRequestRecord(
                    normalized_request_id=normalized_request_id,
                    contribution_id=contribution.contribution_id,
                    planning_attempt_id=planning_attempt_id,
                    operation=plan.operation.value,
                    request_payload=request_payload,
                    request_digest=request_digest,
                    causal_anchor=causal_anchor,
                    created_at=_utc_now(),
                )
            )
            if not isinstance(restored_request, NormalizedRequestRecord):
                raise TypeError(
                    "The activity journal returned another record type."
                )
            normalized_record = restored_request
        else:
            if (
                normalized_record.request_digest != request_digest
                or normalized_record.request_payload != request_payload
            ):
                raise ValueError(
                    "The normalized request identity names another request."
                )
            self._record_recovery_decision(
                contribution_id=contribution.contribution_id,
                stage="engine_submission",
                action="reuse_normalized_request",
                reason=(
                    "The exact canonical engine request is already durable."
                ),
                linked_record_ids={
                    "normalized_request_id": normalized_request_id,
                },
            )
        _append_jsonl(
            self.root / "ENGINE_REQUESTS.jsonl",
            {
                "turn_id": turn_id,
                "normalized_request_id": normalized_request_id,
                "operation": plan.operation.value,
                "request": request.to_dict(),
            },
        )
        self._record_receipt(
            stage="engine_submission",
            status=ConversationActivityStatus.SUBMITTED,
            contribution_id=contribution.contribution_id,
            correlation_ids={
                "planning_attempt_id": planning_attempt_id,
                "normalized_request_id": normalized_request_id,
            },
            payload={"request_digest": request_digest},
            receipt_key="submission",
        )

        assert self.engine is not None
        durable_result = self.journal.find_result(normalized_request_id)
        if durable_result is not None:
            result = ResumptionResult.from_dict(durable_result.result_payload)
            self._record_recovery_decision(
                contribution_id=contribution.contribution_id,
                stage="structured_result",
                action="reuse_conversation_result",
                reason=(
                    "The structured engine result is already present in the "
                    "conversation activity journal."
                ),
                linked_record_ids={
                    "result_id": durable_result.result_id,
                    "normalized_request_id": normalized_request_id,
                },
            )
        else:
            lookup = getattr(
                self.engine,
                "lookup_normalized_request",
                None,
            )
            result = (
                lookup(normalized_request_id)
                if callable(lookup)
                else None
            )
            if result is not None:
                self._record_recovery_decision(
                    contribution_id=contribution.contribution_id,
                    stage="structured_result",
                    action="recover_engine_result",
                    reason=(
                        "The engine already has the authoritative result for "
                        "the normalized request."
                    ),
                    linked_record_ids={
                        "normalized_request_id": normalized_request_id,
                        "execution_attempt_id": result.execution_attempt_id,
                    },
                )
            elif isinstance(request, StartRequest):
                result = (
                    self.engine.start(request)
                    if on_attempt_running is None
                    else self.engine.start(
                        request,
                        on_attempt_running=on_attempt_running,
                    )
                )
            else:
                result = (
                    self.engine.resume(request)
                    if on_attempt_running is None
                    else self.engine.resume(
                        request,
                        on_attempt_running=on_attempt_running,
                    )
                )

        resolved_parent_run_id = (
            parent_identity.revision_id if parent_identity is not None else ""
        )
        identity = result.resulting_revision_identity or result.source_revision_identity
        if identity is None:
            raise ValueError("The governed turn produced no causal revision identity.")
        result_id = stable_result_id(
            normalized_request_id,
            result.execution_attempt_id,
        )
        if durable_result is None:
            restored_result = self._journal_put(
                StructuredResultRecord(
                    result_id=result_id,
                    normalized_request_id=normalized_request_id,
                    contribution_id=contribution.contribution_id,
                    execution_attempt_id=result.execution_attempt_id,
                    result_payload=result.to_dict(),
                    recorded_at=_utc_now(),
                    resulting_binding=identity.to_dict(),
                )
            )
            if not isinstance(restored_result, StructuredResultRecord):
                raise TypeError(
                    "The activity journal returned another record type."
                )
            durable_result = restored_result
        summary = _result_summary(result)
        default_text = _assistant_text(result)
        assistant_text = default_text
        rendering_record: dict[str, Any] = {
            "turn_id": turn_id,
            "result_id": result_id,
            "operation": plan.operation.value,
            "renderer": type(renderer).__name__ if renderer is not None else "",
            "status": "not_requested" if renderer is None else "pending",
        }
        rendering_attempt_id = stable_rendering_attempt_id(
            result_id,
            f"{contribution.contribution_id}:{rendering_attempt_key}",
        )
        durable_rendering = self.journal.get(
            ConversationRecordKind.RENDERING,
            rendering_attempt_id,
        )
        if durable_rendering is not None:
            if not isinstance(durable_rendering, RenderingRecord):
                raise TypeError("The rendering identity names another record type.")
            if (
                durable_rendering.contribution_id
                != contribution.contribution_id
                or durable_rendering.result_id != result_id
            ):
                raise ValueError(
                    "The rendering attempt identity names another result."
                )
            assistant_text = durable_rendering.presentation or default_text
            rendering_record = {
                "turn_id": turn_id,
                "result_id": result_id,
                "operation": plan.operation.value,
                "renderer": type(renderer).__name__ if renderer is not None else "",
                "status": "recovered",
                "rendering_attempt_id": rendering_attempt_id,
            }
            self._record_recovery_decision(
                contribution_id=contribution.contribution_id,
                stage="rendering",
                action="reuse_rendering",
                reason=(
                    "The selected rendering attempt already has a durable "
                    "presentation."
                ),
                linked_record_ids={
                    "rendering_attempt_id": rendering_attempt_id,
                    "result_id": result_id,
                },
            )
        else:
            rendering_started_at = _utc_now()
            self._record_receipt(
                stage="rendering_request",
                status=(
                    ConversationActivityStatus.RUNNING
                    if renderer is not None
                    else ConversationActivityStatus.SUCCEEDED
                ),
                contribution_id=contribution.contribution_id,
                correlation_ids={
                    "normalized_request_id": normalized_request_id,
                    "result_id": result_id,
                    "rendering_attempt_id": rendering_attempt_id,
                },
                payload={
                    "renderer": (
                        type(renderer).__name__ if renderer is not None else ""
                    ),
                    "rendering_schema_version": RENDERING_SCHEMA_VERSION,
                    "prompt_version": RENDERING_PROMPT_VERSION,
                },
                receipt_key="request",
            )
            rendering_status = ConversationActivityStatus.SUCCEEDED
            rendering_schema_version = RENDERING_SCHEMA_VERSION
            rendering_prompt_version = RENDERING_PROMPT_VERSION
            rendering_provider_receipt: dict[str, Any] = {}
            rendering_error: dict[str, Any] = {}
            if (
                renderer is not None
                and result.execution_outcome.value != "interrupted"
            ):
                rendering_started = time.perf_counter()
                try:
                    current_state = self._inspect_state(identity)
                    path_payload = self._inspect_identity(
                        identity,
                        InspectionView.PATH,
                    )
                    rendered = renderer.render(
                        ConversationRenderContext(
                            prompt=plan.prompt,
                            operation=_conversation_operation(plan.operation),
                            current_state=current_state,
                            path=(path_payload,),
                            structured_result=result.to_dict(),
                            default_text=default_text,
                        )
                    )
                    if not isinstance(rendered, ConversationRenderResult):
                        raise ValueError(
                            "The renderer returned no provider-neutral render "
                            "result."
                        )
                    assistant_text = rendered.text.strip() or default_text
                    rendering_provider_receipt = dict(rendered.receipt)
                    rendering_schema_version = rendered.schema_version
                    rendering_prompt_version = rendered.prompt_version
                    rendering_record.update(
                        {
                            "status": "rendered",
                            "provider_receipt": dict(rendered.receipt),
                            "elapsed_seconds": round(
                                time.perf_counter() - rendering_started,
                                6,
                            ),
                        }
                    )
                except Exception as exc:
                    rendering_status = ConversationActivityStatus.FAILED
                    rendering_error = {
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                    rendering_record.update(
                        {
                            "status": "failed",
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "elapsed_seconds": round(
                                time.perf_counter() - rendering_started,
                                6,
                            ),
                        }
                    )
                    assistant_text = default_text
            elif renderer is not None:
                rendering_record["status"] = "skipped_interrupted_attempt"
                rendering_status = ConversationActivityStatus.SKIPPED
            _append_jsonl(
                self.root / "RENDERING_RECEIPTS.jsonl",
                rendering_record,
            )
            restored_rendering = self._journal_put(
                RenderingRecord(
                    rendering_attempt_id=rendering_attempt_id,
                    contribution_id=contribution.contribution_id,
                    result_id=result_id,
                    status=rendering_status,
                    rendering_request={
                        "prompt": plan.prompt,
                        "operation": plan.operation.value,
                        "result_id": result_id,
                    },
                    started_at=rendering_started_at,
                    rendering_schema_version=rendering_schema_version,
                    prompt_version=rendering_prompt_version,
                    presentation=assistant_text,
                    provider_receipt=rendering_provider_receipt,
                    completed_at=_utc_now(),
                    error=rendering_error,
                )
            )
            if not isinstance(restored_rendering, RenderingRecord):
                raise TypeError(
                    "The activity journal returned another record type."
                )
        assistant_message = self._append_message(
            role="assistant",
            content=assistant_text,
            turn_id=turn_id,
            message_id=_stable_local_id(
                "msg",
                rendering_attempt_id,
                "assistant",
            ),
        )
        self._record_receipt(
            stage="presentation_delivery",
            status=ConversationActivityStatus.DELIVERED,
            contribution_id=contribution.contribution_id,
            correlation_ids={
                "result_id": result_id,
                "rendering_attempt_id": rendering_attempt_id,
                "assistant_message_id": str(assistant_message["message_id"]),
            },
            payload={"presentation": assistant_text},
            receipt_key="delivery",
        )
        binding_id = _stable_local_id(
            "binding",
            contribution.contribution_id,
            result_id,
        )
        binding = {
            "binding_id": binding_id,
            "turn_id": turn_id,
            "user_message_id": user_message["message_id"],
            "assistant_message_id": assistant_message["message_id"],
            "treatment": plan.treatment_label or plan.operation.value,
            "operation": plan.operation.value,
            "run_id": identity.revision_id,
            "parent_run_id": resolved_parent_run_id,
            "resumption_identity": identity.to_dict(),
            "execution_attempt_id": result.execution_attempt_id,
            "transition_artifact_reference": (
                result.transition_artifact_reference
            ),
            "sqlite_path": str(self.sqlite_path),
            "semantic_outcome": (
                result.semantic_outcome.value
                if result.semantic_outcome is not None
                else None
            ),
            "execution_outcome": result.execution_outcome.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        prior_binding = next(
            (
                item
                for item in _read_jsonl(self.root / "RUN_BINDINGS.jsonl")
                if str(item.get("binding_id", "")) == binding_id
            ),
            None,
        )
        if prior_binding is None:
            _append_jsonl(self.root / "RUN_BINDINGS.jsonl", binding)
        else:
            binding = prior_binding
            self._record_recovery_decision(
                contribution_id=contribution.contribution_id,
                stage="presentation_delivery",
                action="reuse_binding",
                reason=(
                    "The durable result already has a conversation binding."
                ),
                linked_record_ids={
                    "binding_id": binding_id,
                    "result_id": result_id,
                },
            )
        _write_json(
            self.root / "ACTIVE_BINDING.json",
            {"binding_id": binding["binding_id"]},
        )
        return {
            "assistant_text": assistant_text,
            "turn_id": turn_id,
            "contribution_id": contribution.contribution_id,
            "planning_attempt_id": planning_attempt_id,
            "normalized_request_id": normalized_request_id,
            "result_id": result_id,
            "rendering_attempt_id": rendering_attempt_id,
            "run_id": binding["run_id"],
            "parent_run_id": resolved_parent_run_id,
            "run_outcome": binding["semantic_outcome"],
            "binding": binding,
            "summary": summary,
            "rendering": rendering_record,
        }

    def interrupt(
        self,
        attempt_id: str,
        *,
        reason: str = "",
        requesting_principal: str = "local-user",
        authority_context: dict[str, Any] | None = None,
        correlation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Interrupt one exact execution attempt without semantic mutation."""

        assert self.engine is not None
        result = self.engine.interrupt(
            InterruptionRequest(
                attempt_id=str(attempt_id),
                requesting_principal=requesting_principal,
                authority_context=dict(authority_context or {}),
                reason=reason or None,
                correlation=dict(correlation or {}),
            )
        )
        return result.to_dict()

    def inspect_binding(
        self,
        run_id: str = "",
        *,
        view: InspectionView = InspectionView.CURRENT_STATE,
    ) -> dict[str, Any]:
        """Inspect the exact revision selected by a chat binding."""

        binding = self._resolve_binding(run_id)
        identity = ResumptionIdentity.from_dict(
            dict(binding["resumption_identity"])
        )
        assert self.engine is not None
        return dict(
            self.engine.inspect(
                InspectionRequest(
                    target_kind=InspectionTargetKind.REVISION,
                    target_id=identity.revision_id,
                    view=view,
                    authority_context={"allowed_scope_ids": [identity.scope_id]},
                )
            ).payload
        )

    def discard_transcript(self) -> dict[str, Any]:
        """Discard presentation history without touching semantic state."""

        path = self.root / "MESSAGES.jsonl"
        messages = _read_jsonl(path)
        prior_digest = canonical_payload_digest({"messages": messages})
        path.write_text("", encoding="utf-8")
        return {
            "discarded_message_count": len(messages),
            "discarded_transcript_digest": prior_digest,
        }

    def rerender_result(
        self,
        result_id: str,
        *,
        renderer: ConversationRenderer,
        rendering_attempt_key: str,
    ) -> dict[str, Any]:
        """Render one durable semantic result without resubmitting it."""

        normalized_result_id = str(result_id).strip()
        normalized_attempt_key = str(rendering_attempt_key).strip()
        if not normalized_result_id:
            raise ValueError("A durable result identity is required.")
        if not normalized_attempt_key:
            raise ValueError("A rendering attempt key is required.")
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")

        result_record = self.journal.get(
            ConversationRecordKind.STRUCTURED_RESULT,
            normalized_result_id,
        )
        if not isinstance(result_record, StructuredResultRecord):
            raise ValueError(
                f"No durable structured result exists: {normalized_result_id}"
            )
        request_record = self.journal.get(
            ConversationRecordKind.NORMALIZED_REQUEST,
            result_record.normalized_request_id,
        )
        if not isinstance(request_record, NormalizedRequestRecord):
            raise ValueError(
                "The durable result has no normalized request record."
            )
        contribution = self.journal.get(
            ConversationRecordKind.CONTRIBUTION,
            result_record.contribution_id,
        )
        if not isinstance(contribution, ContributionRecord):
            raise ValueError("The durable result has no contribution record.")
        if result_record.resulting_binding is None:
            raise ValueError("The durable result has no causal binding.")

        rendering_attempt_id = stable_rendering_attempt_id(
            normalized_result_id,
            normalized_attempt_key,
        )
        existing = self.journal.get(
            ConversationRecordKind.RENDERING,
            rendering_attempt_id,
        )
        if existing is not None:
            if not isinstance(existing, RenderingRecord):
                raise TypeError("The rendering identity names another record type.")
            if existing.result_id != normalized_result_id:
                raise ValueError(
                    "The rendering attempt identity names another result."
                )
            return _rendering_report(existing, recovered=True)

        semantic_result = ResumptionResult.from_dict(
            result_record.result_payload
        )
        identity = ResumptionIdentity.from_dict(
            result_record.resulting_binding
        )
        operation = OperationKind(request_record.operation)
        default_text = _assistant_text(semantic_result)
        self._record_receipt(
            stage="rendering_request",
            status=ConversationActivityStatus.RUNNING,
            contribution_id=contribution.contribution_id,
            correlation_ids={
                "normalized_request_id": request_record.normalized_request_id,
                "result_id": normalized_result_id,
                "rendering_attempt_id": rendering_attempt_id,
            },
            payload={
                "renderer": type(renderer).__name__,
                "rendering_schema_version": RENDERING_SCHEMA_VERSION,
                "prompt_version": RENDERING_PROMPT_VERSION,
                "rerender": True,
            },
            receipt_key="rerender_request",
        )
        started_at = _utc_now()
        status = ConversationActivityStatus.SUCCEEDED
        presentation = default_text
        provider_receipt: dict[str, Any] = {}
        error: dict[str, Any] = {}
        schema_version = RENDERING_SCHEMA_VERSION
        prompt_version = RENDERING_PROMPT_VERSION
        try:
            rendered = renderer.render(
                ConversationRenderContext(
                    prompt=contribution.text,
                    operation=_conversation_operation(operation),
                    current_state=self._inspect_state(identity),
                    path=(
                        self._inspect_identity(identity, InspectionView.PATH),
                    ),
                    structured_result=semantic_result.to_dict(),
                    default_text=default_text,
                )
            )
            if not isinstance(rendered, ConversationRenderResult):
                raise ValueError(
                    "The renderer returned no provider-neutral render result."
                )
            presentation = rendered.text.strip() or default_text
            provider_receipt = dict(rendered.receipt)
            schema_version = rendered.schema_version
            prompt_version = rendered.prompt_version
        except Exception as exc:
            status = ConversationActivityStatus.FAILED
            error = {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        restored = self._journal_put(
            RenderingRecord(
                rendering_attempt_id=rendering_attempt_id,
                contribution_id=contribution.contribution_id,
                result_id=normalized_result_id,
                status=status,
                rendering_request={
                    "prompt": contribution.text,
                    "operation": operation.value,
                    "result_id": normalized_result_id,
                    "rerender": True,
                },
                started_at=started_at,
                rendering_schema_version=schema_version,
                prompt_version=prompt_version,
                presentation=presentation,
                provider_receipt=provider_receipt,
                completed_at=_utc_now(),
                error=error,
            )
        )
        if not isinstance(restored, RenderingRecord):
            raise TypeError("The activity journal returned another record type.")
        self._record_receipt(
            stage="presentation_delivery",
            status=ConversationActivityStatus.DELIVERED,
            contribution_id=contribution.contribution_id,
            correlation_ids={
                "result_id": normalized_result_id,
                "rendering_attempt_id": rendering_attempt_id,
            },
            payload={"presentation": presentation, "rerender": True},
            receipt_key="rerender_delivery",
        )
        return _rendering_report(restored, recovered=False)

    def _parent_context(
        self,
        run_id: str,
    ) -> tuple[dict[str, Any], ResumptionIdentity, dict[str, Any]]:
        binding = self._resolve_binding(run_id)
        identity = ResumptionIdentity.from_dict(
            dict(binding["resumption_identity"])
        )
        return binding, identity, self._inspect_state(identity)

    def _accept_contribution(
        self,
        prompt: str,
        *,
        idempotency_key: str,
        parent_run_id: str,
        provenance: dict[str, Any] | None = None,
    ) -> ContributionRecord:
        delivery_key = str(idempotency_key).strip() or f"delivery_{uuid.uuid4().hex}"
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        existing = self.journal.find_contribution(
            idempotency_key=delivery_key
        )
        if existing is not None:
            expected_correlation = (
                {"requested_parent_run_id": str(parent_run_id)}
                if str(parent_run_id).strip()
                else {}
            )
            if (
                existing.session_id != self.session_id
                or existing.scope_id != self.scope_id
                or existing.text != prompt
                or existing.correlation != expected_correlation
            ):
                raise ValueError(
                    "The contribution idempotency key already names a "
                    "different contribution."
                )
            return existing
        selected_binding: dict[str, Any] | None = None
        try:
            selected_binding = dict(self._resolve_binding(parent_run_id))
        except ValueError:
            if str(parent_run_id).strip():
                raise
        record = ContributionRecord(
            contribution_id=stable_contribution_id(
                self.session_id,
                delivery_key,
            ),
            session_id=self.session_id,
            idempotency_key=delivery_key,
            text=prompt,
            scope_id=self.scope_id,
            received_at=_utc_now(),
            selected_binding=selected_binding,
            provenance={
                "source": "conversation_application",
                **dict(provenance or {}),
            },
            correlation=(
                {"requested_parent_run_id": str(parent_run_id)}
                if str(parent_run_id).strip()
                else {}
            ),
        )
        restored = self._journal_put(record)
        if not isinstance(restored, ContributionRecord):
            raise TypeError("The activity journal returned another record type.")
        return restored

    def _record_proposal(
        self,
        *,
        planning_attempt_id: str,
        contribution_id: str,
        context_digest: str,
        status: ConversationActivityStatus,
        proposal: dict[str, Any] | None = None,
        normalized_plan: dict[str, Any] | None = None,
        provider_receipt: dict[str, Any] | None = None,
        unresolved_interpretation: tuple[str, ...] = (),
        schema_version: str = PLANNING_SCHEMA_VERSION,
        prompt_version: str = PLANNING_PROMPT_VERSION,
        error: dict[str, Any] | None = None,
    ) -> PlanningProposalRecord:
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        existing = self.journal.get(
            ConversationRecordKind.PROPOSAL,
            planning_attempt_id,
        )
        if existing is not None:
            if not isinstance(existing, PlanningProposalRecord):
                raise TypeError("The planning identity names another record type.")
            return existing
        record = PlanningProposalRecord(
            planning_attempt_id=planning_attempt_id,
            contribution_id=contribution_id,
            status=status,
            planning_context_digest=context_digest,
            proposal=dict(proposal or {}),
            created_at=_utc_now(),
            proposal_schema_version=schema_version,
            prompt_version=prompt_version,
            normalized_plan=dict(normalized_plan or {}),
            provider_receipt=dict(provider_receipt or {}),
            unresolved_interpretation=tuple(unresolved_interpretation),
            error=dict(error or {}),
        )
        restored = self._journal_put(record)
        if not isinstance(restored, PlanningProposalRecord):
            raise TypeError("The activity journal returned another record type.")
        return restored

    def _record_receipt(
        self,
        *,
        stage: str,
        status: ConversationActivityStatus,
        contribution_id: str,
        correlation_ids: dict[str, str],
        payload: dict[str, Any],
        receipt_key: str,
        complete: bool = True,
    ) -> ConversationReceipt:
        correlations = {
            "contribution_id": contribution_id,
            **{
                str(key): str(value)
                for key, value in correlation_ids.items()
                if str(value)
            },
        }
        receipt_id = stable_receipt_id(
            stage,
            correlations,
            receipt_key,
        )
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        existing = self.journal.get(
            ConversationRecordKind.RECEIPT,
            receipt_id,
        )
        if existing is not None:
            if not isinstance(existing, ConversationReceipt):
                raise TypeError("The receipt identity names another record type.")
            return existing
        record = ConversationReceipt(
            receipt_id=receipt_id,
            stage=stage,
            status=status,
            correlation_ids=correlations,
            payload=dict(payload),
            recorded_at=_utc_now(),
            complete=complete,
        )
        restored = self._journal_put(record)
        if not isinstance(restored, ConversationReceipt):
            raise TypeError("The activity journal returned another record type.")
        return restored

    def _record_recovery_decision(
        self,
        *,
        contribution_id: str,
        stage: str,
        action: str,
        reason: str,
        linked_record_ids: dict[str, str],
    ) -> RecoveryDecisionRecord:
        recovery_id = stable_recovery_decision_id(
            contribution_id,
            stage,
            action,
            canonical_payload_digest(linked_record_ids),
        )
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        existing = self.journal.get(
            ConversationRecordKind.RECOVERY_DECISION,
            recovery_id,
        )
        if existing is not None:
            if not isinstance(existing, RecoveryDecisionRecord):
                raise TypeError("The recovery identity names another record type.")
            return existing
        record = RecoveryDecisionRecord(
            recovery_decision_id=recovery_id,
            contribution_id=contribution_id,
            stage=stage,
            action=action,
            reason=reason,
            linked_record_ids=dict(linked_record_ids),
            recorded_at=_utc_now(),
        )
        restored = self._journal_put(record)
        if not isinstance(restored, RecoveryDecisionRecord):
            raise TypeError("The activity journal returned another record type.")
        return restored

    def _journal_put(self, record):
        if self.journal is None:
            raise RuntimeError("Conversation activity journal is not configured.")
        return self.journal.put(record)

    def _begin_turn(
        self,
        prompt: str,
        *,
        contribution_id: str,
    ) -> tuple[str, dict[str, Any]]:
        turn_id = f"turn_{contribution_id.removeprefix('contribution_')}"
        return turn_id, self._append_message(
            role="user",
            content=prompt,
            turn_id=turn_id,
            message_id=_stable_local_id("msg", turn_id, "user"),
        )

    def _materialize_proposal(
        self,
        proposal: ConversationPlanProposal,
        *,
        prompt: str,
        parent_binding: dict[str, Any] | None,
        parent_identity: ResumptionIdentity | None,
        parent_state: dict[str, Any] | None,
        binding_aliases: dict[str, str],
        source_attempt_id: str,
        turn_id: str,
        message_id: str,
    ) -> ConversationTurnPlan:
        proposed_operation = proposal.operation
        if proposed_operation is None:
            raise ConversationPlanningError(
                "The conversation operation is unresolved."
            )
        operation = _engine_operation(proposed_operation)
        proposal, ignored_control_fields = _normalize_operation_control_fields(
            proposal,
            operation,
        )
        ignored_unsupported_promote_selectors: tuple[str, ...] = ()
        ignored_unsupported_resolved_selectors: tuple[str, ...] = ()
        ignored_unsupported_resolved_applicability_selectors: tuple[
            str, ...
        ] = ()
        ignored_redundant_promote_selectors: tuple[str, ...] = ()
        ignored_redundant_resolved_selectors: tuple[str, ...] = ()
        ignored_redundant_resolved_applicability_selectors: tuple[
            str, ...
        ] = ()
        defaulted_unresolved_realignment_selectors: tuple[str, ...] = ()
        identity_disposition = _engine_identity_disposition(
            proposal.identity_disposition
        )
        if operation is OperationKind.REDIRECT_AND_REALIGN:
            identity_disposition = _ground_redirect_identity_disposition(
                identity_disposition,
                prompt,
            )
        if operation is not OperationKind.START and (
            parent_binding is None
            or parent_identity is None
            or parent_state is None
        ):
            raise ConversationPlanningError(
                f"{operation.value} requires an exact causal binding; "
                "similarity or prose cannot select one."
            )
        if operation is OperationKind.CORRECT and parent_state is not None:
            grounded_selectors = _explicitly_grounded_selectors(
                parent_state,
                prompt,
            )
            ignored_unsupported_promote_selectors = tuple(
                selector
                for selector in proposal.promote_selectors
                if _selector_token(selector) not in grounded_selectors
            )
            ignored_unsupported_resolved_selectors = tuple(
                selector
                for selector in proposal.resolved_selectors
                if _selector_token(selector) not in grounded_selectors
            )
            ignored_unsupported_resolved_applicability_selectors = tuple(
                selector
                for selector in proposal.resolved_applicability_selectors
                if _selector_token(selector) not in grounded_selectors
            )
            correction_selectors = {
                _selector_token(
                    _semantic_key(
                        _resolve_semantic_selector(
                            parent_state,
                            correction.target_selector,
                        )
                    )
                )
                for correction in proposal.corrections
            }
            supported_promote_selectors = tuple(
                selector
                for selector in proposal.promote_selectors
                if _selector_token(selector) in grounded_selectors
            )
            supported_resolved_selectors = tuple(
                selector
                for selector in proposal.resolved_selectors
                if _selector_token(selector) in grounded_selectors
            )
            supported_resolved_applicability_selectors = tuple(
                selector
                for selector in proposal.resolved_applicability_selectors
                if _selector_token(selector) in grounded_selectors
            )
            ignored_redundant_promote_selectors = tuple(
                selector
                for selector in supported_promote_selectors
                if _selector_token(selector) in correction_selectors
            )
            ignored_redundant_resolved_selectors = tuple(
                selector
                for selector in supported_resolved_selectors
                if _selector_token(selector) in correction_selectors
            )
            stronger_resolution_selectors = {
                *correction_selectors,
                *(
                    _selector_token(selector)
                    for selector in supported_promote_selectors
                ),
                *(
                    _selector_token(selector)
                    for selector in supported_resolved_selectors
                ),
            }
            ignored_redundant_resolved_applicability_selectors = tuple(
                selector
                for selector in supported_resolved_applicability_selectors
                if _selector_token(selector) in stronger_resolution_selectors
            )
            proposal = replace(
                proposal,
                promote_selectors=tuple(
                    selector
                    for selector in supported_promote_selectors
                    if _selector_token(selector) not in correction_selectors
                ),
                resolved_selectors=tuple(
                    selector
                    for selector in supported_resolved_selectors
                    if _selector_token(selector) not in correction_selectors
                ),
                resolved_applicability_selectors=tuple(
                    selector
                    for selector in supported_resolved_applicability_selectors
                    if _selector_token(selector)
                    not in stronger_resolution_selectors
                ),
            )

        achieved_proposals, non_achieved_proposals = (
            _normalize_direct_semantic_proposals(
                proposal,
                operation=operation,
                parent_state=parent_state,
            )
        )
        achieved = [
            _materialize_item(
                item,
                message_id=message_id,
                turn_id=turn_id,
                destination="achieved",
            )
            for item in achieved_proposals
        ]
        non_achieved = [
            _materialize_item(
                item,
                message_id=message_id,
                turn_id=turn_id,
                destination="non_achievedness",
            )
            for item in non_achieved_proposals
        ]
        resolved_non_achievedness_ids: list[str] = []
        resolved_applicability_item_ids: list[str] = []
        corrections: list[CorrectionPlan] = []

        if parent_state is not None:
            for selector in proposal.promote_selectors:
                promoted = _resolve_non_achieved_selector(
                    parent_state,
                    selector,
                )
                achieved.append(SemanticItem.from_dict(dict(promoted)))
                resolved_non_achievedness_ids.append(
                    str(promoted["item_id"])
                )
            for selector in proposal.resolved_selectors:
                resolved = _resolve_non_achieved_selector(
                    parent_state,
                    selector,
                )
                resolved_non_achievedness_ids.append(
                    str(resolved["item_id"])
                )
            unresolved_applicability_ids = {
                str(item_id)
                for item_id in parent_state.get(
                    "unresolved_applicability_item_ids",
                    (),
                )
            }
            for selector in proposal.resolved_applicability_selectors:
                resolved = _resolve_non_achieved_selector(
                    parent_state,
                    selector,
                )
                resolved_id = str(resolved["item_id"])
                if resolved_id not in unresolved_applicability_ids:
                    raise ConversationPlanningError(
                        "Applicability can only be resolved for a selector "
                        f"currently unresolved in applicability: {selector}"
                    )
                resolved_applicability_item_ids.append(resolved_id)
            for correction in proposal.corrections:
                target = _resolve_semantic_selector(
                    parent_state,
                    correction.target_selector,
                )
                target_selector = _semantic_key(target)
                replacement = None
                if correction.replacement is not None:
                    replacement_selector = _selector_token(
                        correction.replacement.selector
                    )
                    if replacement_selector not in {
                        _selector_token(target_selector),
                        _selector_token(str(target["item_id"])),
                    }:
                        raise ConversationPlanningError(
                            "A correction replacement must preserve the "
                            f"selected semantic key: {target_selector}"
                        )
                    replacement = _materialize_item(
                        correction.replacement,
                        message_id=message_id,
                        turn_id=turn_id,
                        destination="achieved",
                        semantic_key=target_selector,
                    )
                corrections.append(
                    CorrectionPlan(
                        target_selector=target_selector,
                        replacement=replacement,
                        rationale=(
                            correction.rationale
                            or "The user explicitly requested this correction."
                        ),
                        evidence_references=(message_id,),
                    )
                )

        introduced_achieved: list[SemanticItem] = []
        introduced_non_achieved: list[SemanticItem] = []
        for item in proposal.introduced_items:
            destination = _proposal_destination(item)
            materialized = _materialize_item(
                item,
                message_id=message_id,
                turn_id=turn_id,
                destination=destination,
            )
            if destination == "achieved":
                introduced_achieved.append(materialized)
            else:
                introduced_non_achieved.append(materialized)
        achieved.extend(introduced_achieved)
        non_achieved.extend(introduced_non_achieved)
        _require_unique_semantic_keys((*achieved, *non_achieved))

        semantic_delta = SemanticDelta(
            achieved=tuple(achieved),
            non_achievedness=tuple(non_achieved),
            resolved_non_achievedness_ids=tuple(
                dict.fromkeys(resolved_non_achievedness_ids)
            ),
            resolved_applicability_item_ids=tuple(
                dict.fromkeys(resolved_applicability_item_ids)
            ),
        )
        direction: GoverningDirection | None = None
        if operation in {
            OperationKind.START,
            OperationKind.DERIVE,
            OperationKind.REDIRECT_AND_REALIGN,
        }:
            scope_id = (
                parent_identity.scope_id
                if parent_identity is not None
                else self.scope_id
            )
            direction = GoverningDirection(
                objective=proposal.objective or prompt,
                scope=scope_id,
                required_outcome=(
                    proposal.required_outcome
                    or "Satisfy the represented user objective."
                ),
            )

        realignment: RealignmentPlan | None = None
        if operation is OperationKind.REDIRECT_AND_REALIGN:
            assert parent_state is not None
            assert parent_identity is not None
            all_selectors = _all_public_selectors(parent_state)
            affected = _normalized_selectors(proposal.affected_selectors)
            retained = _normalized_selectors(proposal.retained_selectors)
            superseded = _normalized_selectors(
                proposal.superseded_selectors
            )
            unresolved = _normalized_selectors(
                proposal.unresolved_selectors
            )
            extra = sorted(affected - all_selectors)
            if extra:
                raise ConversationPlanningError(
                    "Realignment cannot classify unknown public selectors: "
                    + ", ".join(extra)
                )
            defaulted_unresolved_realignment_selectors = tuple(
                sorted(all_selectors - affected)
            )
            affected |= set(defaulted_unresolved_realignment_selectors)
            unresolved |= set(defaulted_unresolved_realignment_selectors)
            grounded = _explicitly_grounded_selectors(
                parent_state,
                prompt,
            )
            unsupported_dispositions = (
                retained | superseded
            ) - grounded
            retained -= unsupported_dispositions
            superseded -= unsupported_dispositions
            unresolved |= unsupported_dispositions
            _require_partition(
                affected,
                retained=retained,
                superseded=superseded,
                unresolved=unresolved,
            )
            target_scope_id = parent_identity.scope_id
            target_objective_id = parent_identity.objective_id
            target_branch_id = parent_identity.branch_id
            if (
                identity_disposition
                is not IdentityDispositionKind.SAME_OBJECTIVE
            ):
                target_objective_id = _stable_local_id(
                    "objective",
                    message_id,
                    "realigned",
                )
            if identity_disposition is IdentityDispositionKind.BRANCH:
                target_branch_id = _branch_name(proposal.target_branch)
            realignment = RealignmentPlan(
                affected_selectors=tuple(sorted(affected)),
                retained_selectors=tuple(sorted(retained)),
                superseded_selectors=tuple(sorted(superseded)),
                unresolved_selectors=tuple(sorted(unresolved)),
                introduced_items=tuple(
                    (*introduced_achieved, *introduced_non_achieved)
                ),
                identity_disposition=identity_disposition,
                target_scope_id=target_scope_id,
                target_objective_id=target_objective_id,
                target_branch_id=target_branch_id,
                rationale=(
                    proposal.rationale
                    or "The user explicitly changed the governing direction."
                ),
                evidence_references=(message_id,),
                completeness_statement=(
                    "Every current public semantic selector was classified "
                    "by the conversation host."
                ),
            )

        selected_item_selectors = proposal.selected_selectors
        target_scope_id = ""
        target_objective_id = ""
        target_branch_id = ""
        if operation is OperationKind.START:
            target_scope_id = self.scope_id
            target_objective_id = _stable_local_id(
                "objective",
                message_id,
                "start",
            )
            target_branch_id = "main"
        elif operation is OperationKind.DERIVE:
            if not selected_item_selectors:
                raise ConversationPlanningError(
                    "Derivation requires selected admitted semantic material."
                )
            target_scope_id = self.scope_id
            target_objective_id = _stable_local_id(
                "objective",
                message_id,
                "derived",
            )
            target_branch_id = "main"
        elif operation is OperationKind.BRANCH:
            target_branch_id = _branch_name(proposal.target_branch)

        merge_parent_run_ids: tuple[str, ...] = ()
        if operation is OperationKind.MERGE:
            assert parent_binding is not None
            merge_ids: list[str] = []
            merge_aliases = tuple(dict.fromkeys((
                *proposal.merge_branch_aliases,
                *_explicit_binding_aliases(prompt, binding_aliases),
            )))
            for alias in merge_aliases:
                if alias not in binding_aliases:
                    raise ConversationPlanningError(
                        f"Unknown host-resolved branch alias: {alias}"
                    )
                run_id = str(binding_aliases[alias])
                if run_id != str(parent_binding["run_id"]):
                    merge_ids.append(run_id)
            merge_parent_run_ids = tuple(dict.fromkeys(merge_ids))
            if not merge_parent_run_ids:
                raise ConversationPlanningError(
                    "Merge requires at least one other exact branch binding."
                )

        reversal: ReversalPlan | None = None
        if operation is OperationKind.REVERSE:
            assert parent_identity is not None
            reversal = self._resolve_reversal(
                parent_identity,
                proposal.reversal_selector,
                prompt=prompt,
                rationale=proposal.rationale,
                evidence_reference=message_id,
            )

        if (
            operation is OperationKind.RESUME_AFTER_INTERRUPTION
            and not source_attempt_id.strip()
        ):
            raise ConversationPlanningError(
                "Resume after interruption requires an exact attempt identity."
            )

        return ConversationTurnPlan(
            operation=operation,
            prompt=prompt,
            parent_run_id=(
                ""
                if operation is OperationKind.START
                else str((parent_binding or {})["run_id"])
            ),
            semantic_delta=semantic_delta,
            governing_direction=direction,
            corrections=tuple(corrections),
            realignment=realignment,
            reversal=reversal,
            selected_item_selectors=selected_item_selectors,
            target_scope_id=target_scope_id,
            target_objective_id=target_objective_id,
            target_branch_id=target_branch_id,
            source_attempt_id=source_attempt_id,
            merge_parent_run_ids=merge_parent_run_ids,
            inlet_kind="natural_language_contribution",
            treatment_label=f"planned_{operation.value}",
            inlet_payload={
                "planner_rationale": proposal.rationale,
                "ignored_inapplicable_control_fields": list(
                    ignored_control_fields
                ),
                "ignored_unsupported_promote_selectors": list(
                    ignored_unsupported_promote_selectors
                ),
                "ignored_unsupported_resolved_selectors": list(
                    ignored_unsupported_resolved_selectors
                ),
                "ignored_unsupported_resolved_applicability_selectors": list(
                    ignored_unsupported_resolved_applicability_selectors
                ),
                "ignored_redundant_promote_selectors": list(
                    ignored_redundant_promote_selectors
                ),
                "ignored_redundant_resolved_selectors": list(
                    ignored_redundant_resolved_selectors
                ),
                "ignored_redundant_resolved_applicability_selectors": list(
                    ignored_redundant_resolved_applicability_selectors
                ),
                "defaulted_unresolved_realignment_selectors": list(
                    defaulted_unresolved_realignment_selectors
                ),
            },
        )

    def _resolve_reversal(
        self,
        parent_identity: ResumptionIdentity,
        selector: str,
        *,
        prompt: str,
        rationale: str,
        evidence_reference: str,
    ) -> ReversalPlan:
        normalized = _selector_token(selector)
        if not normalized:
            raise ConversationPlanningError(
                "Reverse requires an unambiguous public reversal selector."
            )
        normalized_prompt = _selector_token(prompt)
        generic_selectors = {
            "last",
            "latest",
            "last correction",
            "latest correction",
        }
        if normalized in generic_selectors:
            if not any(
                candidate in normalized_prompt
                for candidate in generic_selectors
            ):
                raise ConversationPlanningError(
                    "A generic reversal selector must be explicit in the user "
                    "contribution."
                )
        elif normalized not in normalized_prompt:
            raise ConversationPlanningError(
                "The reversal selector must be grounded in the user contribution."
            )
        reconstruction = self._inspect_identity(
            parent_identity,
            InspectionView.RECONSTRUCTION,
        )
        revision = dict(reconstruction.get("revision", {}))
        transition = dict(
            reconstruction.get("transition_artifact", {}) or {}
        )
        parents = tuple(revision.get("parent_revision_ids", ()))
        if transition.get("operation") != OperationKind.CORRECT.value or len(parents) != 1:
            raise ConversationPlanningError(
                "The selected current revision is not one reversible correction."
            )
        aliases = _correction_transition_aliases(revision)
        if normalized not in aliases and normalized not in generic_selectors:
            raise ConversationPlanningError(
                f"The current correction does not match reversal selector: {selector}"
            )
        artifact_id = str(transition.get("artifact_id", ""))
        if not artifact_id:
            raise ConversationPlanningError(
                "The current correction has no inspectable transition artifact."
            )
        return ReversalPlan(
            target_transition_artifact_id=artifact_id,
            restore_parent_revision_id=str(parents[0]),
            rationale=rationale or "The user explicitly selected this correction.",
            evidence_references=(evidence_reference,),
        )

    def _inspect_identity(
        self,
        identity: ResumptionIdentity,
        view: InspectionView,
    ) -> dict[str, Any]:
        assert self.engine is not None
        return dict(
            self.engine.inspect(
                InspectionRequest(
                    target_kind=InspectionTargetKind.REVISION,
                    target_id=identity.revision_id,
                    view=view,
                    authority_context={
                        "allowed_scope_ids": [identity.scope_id]
                    },
                )
            ).payload
        )

    def _request_for_plan(
        self,
        plan: ConversationTurnPlan,
        *,
        turn_id: str,
        message_id: str,
        parent_identity: ResumptionIdentity | None,
        parent_state: dict[str, Any] | None,
    ) -> StartRequest | ResumptionRequest:
        payload = {
            "content": plan.prompt,
            "turn_id": turn_id,
            **dict(plan.inlet_payload),
        }
        if plan.operation is OperationKind.START:
            direction = plan.governing_direction or GoverningDirection(
                objective=plan.prompt,
                scope=self.scope_id,
                required_outcome="answer the represented request",
            )
            initial_delta = replace(
                plan.semantic_delta,
                governing_direction=None,
            )
            return StartRequest(
                scope_id=plan.target_scope_id or self.scope_id,
                objective_id=(
                    plan.target_objective_id
                    or _stable_local_id(
                        "objective",
                        message_id,
                        "start",
                    )
                ),
                branch_id=plan.target_branch_id or "main",
                initial_inlet=ContinuationInlet(
                    inlet_id=message_id,
                    kind=plan.inlet_kind or "user_request",
                    payload={"prompt": plan.prompt, **dict(plan.inlet_payload)},
                    target="root",
                    relationship=InletRelationship.CONTINUATION,
                    source="human",
                    provenance=(turn_id,),
                    correlation={},
                    authority_context=dict(plan.authority_context),
                    delta=initial_delta,
                ),
                governing_direction=direction,
            )

        if parent_identity is None or parent_state is None:
            raise ValueError(
                f"{plan.operation.value} requires an exact causal binding."
            )

        inlet: ContinuationInlet | None = None
        merge_parent_identities: tuple[ResumptionIdentity, ...] = ()
        operation = plan.operation
        current_items = _current_items(parent_state)

        if operation is OperationKind.RESUME_SUSPENDED:
            selected_hold = _select_active_hold(
                parent_state,
                plan.target_hold_id,
            )
            if selected_hold is None:
                raise ValueError("No active HoldOn is available to resume.")
            hold_id = str(selected_hold["hold_id"])
            payload.update({"answer": plan.prompt, "hold_id": hold_id})
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target=hold_id,
                relationship=InletRelationship.HOLD_SATISFACTION,
                correlation=dict(selected_hold.get("correlation", {})),
            )
        elif operation is OperationKind.DERIVE:
            selected = _resolve_selected_items(
                parent_state,
                plan.selected_item_ids,
                plan.selected_item_selectors,
            )
            if not selected:
                raise ValueError(
                    "Derivation requires selected admitted semantic material."
                )
            target_scope = plan.target_scope_id or self.scope_id
            target_objective = (
                plan.target_objective_id
                or _stable_local_id(
                    "objective",
                    message_id,
                    "derived",
                )
            )
            target_branch = plan.target_branch_id or "main"
            direction = plan.governing_direction or GoverningDirection(
                objective=plan.prompt,
                scope=target_scope,
                required_outcome="answer the represented derived objective",
            )
            payload.update(
                {
                    "selected_item_ids": list(selected),
                    "target_scope_id": target_scope,
                    "target_objective_id": target_objective,
                    "target_branch_id": target_branch,
                }
            )
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target="root",
                relationship=InletRelationship.CONTINUATION,
                delta=replace(
                    plan.semantic_delta,
                    governing_direction=direction,
                ),
            )
        elif operation is OperationKind.CORRECT:
            supersessions = list(plan.semantic_delta.supersessions)
            target_ids: list[str] = []
            for correction in plan.corrections:
                target = _resolve_semantic_selector(
                    parent_state,
                    correction.target_selector,
                )
                target_id = str(target["item_id"])
                target_ids.append(target_id)
                replacement_item = correction.replacement
                if replacement_item is not None:
                    replacement_item = _attribute_item(
                        replacement_item,
                        message_id=message_id,
                        parent_revision_id=parent_identity.revision_id,
                        turn_id=turn_id,
                    )
                supersessions.append(
                    Supersession(
                        target_item_id=target_id,
                        replacement=replacement_item,
                        evidence_references=(
                            correction.evidence_references or (message_id,)
                        ),
                        rationale=correction.rationale,
                    )
                )
            if not supersessions and plan.semantic_delta == SemanticDelta():
                raise ValueError(
                    "Correction requires at least one explicit semantic change."
                )
            target = target_ids[0] if len(target_ids) == 1 else "root"
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target=target,
                relationship=InletRelationship.CORRECTION,
                delta=replace(
                    plan.semantic_delta,
                    supersessions=tuple(supersessions),
                ),
            )
        elif operation is OperationKind.REDIRECT_AND_REALIGN:
            proposal = plan.realignment
            if proposal is None:
                raise ValueError(
                    "Redirection requires an explicit realignment proposal."
                )
            direction = (
                plan.governing_direction
                or plan.semantic_delta.governing_direction
            )
            if direction is None:
                raise ValueError(
                    "Redirection requires an explicit governing direction."
                )
            affected = _resolve_selector_ids(
                parent_state,
                proposal.affected_selectors,
            )
            retained = _resolve_selector_ids(
                parent_state,
                proposal.retained_selectors,
            )
            superseded = _resolve_selector_ids(
                parent_state,
                proposal.superseded_selectors,
            )
            unresolved = _resolve_selector_ids(
                parent_state,
                proposal.unresolved_selectors,
            )
            unresolved_items = tuple(
                SemanticItem.from_dict(dict(current_items[item_id]))
                for item_id in unresolved
            )
            target_scope = proposal.target_scope_id or parent_identity.scope_id
            target_objective = (
                proposal.target_objective_id
                or parent_identity.objective_id
            )
            target_branch = (
                proposal.target_branch_id or parent_identity.branch_id
            )
            identity_disposition = IdentityDisposition(
                kind=proposal.identity_disposition,
                target_scope_id=target_scope,
                target_objective_id=target_objective,
                target_branch_id=target_branch,
                rationale=proposal.rationale,
            )
            realignment = Realignment(
                source_revision_id=parent_identity.revision_id,
                redirection_inlet_id=message_id,
                affected_item_ids=affected,
                identity_disposition=identity_disposition,
                retained_item_ids=retained,
                superseded_item_ids=superseded,
                introduced_items=proposal.introduced_items,
                unresolved_applicability_item_ids=unresolved,
                resulting_non_achievedness=unresolved_items,
                evidence_references=(
                    proposal.evidence_references or (message_id,)
                ),
                governance_references=proposal.governance_references,
                completeness_statement=proposal.completeness_statement,
            )
            redirect_delta = replace(
                plan.semantic_delta,
                governing_direction=direction,
            )
            if redirect_delta.supersessions:
                payload["includes_explicit_correction"] = True
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target="root",
                relationship=InletRelationship.REDIRECTION,
                delta=redirect_delta,
                realignment=realignment,
            )
        elif operation is OperationKind.BRANCH:
            target_branch = plan.target_branch_id.strip()
            if not target_branch:
                raise ValueError("Branch requires an explicit target branch.")
            payload["target_branch_id"] = target_branch
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target="root",
                relationship=InletRelationship.CONTINUATION,
            )
        elif operation is OperationKind.MERGE:
            merge_parent_identities = tuple(
                ResumptionIdentity.from_dict(
                    dict(self._resolve_binding(run_id)["resumption_identity"])
                )
                for run_id in plan.merge_parent_run_ids
            )
            if plan.semantic_delta != SemanticDelta():
                relationship = (
                    InletRelationship.CORRECTION
                    if plan.semantic_delta.supersessions
                    else InletRelationship.CONTINUATION
                )
                inlet = self._inlet(
                    plan,
                    turn_id=turn_id,
                    message_id=message_id,
                    parent_identity=parent_identity,
                    payload=payload,
                    target="root",
                    relationship=relationship,
                )
        elif operation is OperationKind.REVERSE:
            proposal = plan.reversal
            if proposal is None:
                raise ValueError("Reverse requires an explicit reversal proposal.")
            reversal = Reversal(
                target_transition_artifact_id=(
                    proposal.target_transition_artifact_id
                ),
                restore_parent_revision_id=(
                    proposal.restore_parent_revision_id
                ),
                evidence_references=(
                    proposal.evidence_references or (message_id,)
                ),
                rationale=proposal.rationale,
            )
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target="root",
                relationship=InletRelationship.REVERSAL,
                delta=SemanticDelta(),
                reversal=reversal,
            )
        elif operation in {
            OperationKind.EXPLAIN,
            OperationKind.VERIFY,
            OperationKind.RECONSTRUCT,
            OperationKind.RESUME_AFTER_INTERRUPTION,
        }:
            inlet = None
        else:
            relationship = {
                OperationKind.AUGMENT: InletRelationship.AUGMENTATION,
                OperationKind.CONTINUE: InletRelationship.CONTINUATION,
            }.get(operation)
            if relationship is None:
                raise ValueError(
                    f"Unsupported conversation operation: {operation.value}"
                )
            inlet = self._inlet(
                plan,
                turn_id=turn_id,
                message_id=message_id,
                parent_identity=parent_identity,
                payload=payload,
                target=_single_non_achieved_target(parent_state),
                relationship=relationship,
            )

        return ResumptionRequest(
            anchor=parent_identity,
            operation=operation,
            expected_branch_head_revision_id=parent_identity.revision_id,
            inlet=inlet,
            source_attempt_id=plan.source_attempt_id or None,
            merge_parent_identities=merge_parent_identities,
        )

    @staticmethod
    def _inlet(
        plan: ConversationTurnPlan,
        *,
        turn_id: str,
        message_id: str,
        parent_identity: ResumptionIdentity,
        payload: dict[str, Any],
        target: str,
        relationship: InletRelationship,
        correlation: dict[str, Any] | None = None,
        delta: SemanticDelta | None = None,
        realignment: Realignment | None = None,
        reversal: Reversal | None = None,
    ) -> ContinuationInlet:
        return ContinuationInlet(
            inlet_id=message_id,
            kind=plan.inlet_kind,
            payload=dict(payload),
            target=target,
            relationship=relationship,
            source="human",
            provenance=(turn_id, parent_identity.revision_id),
            correlation=dict(correlation or {}),
            authority_context=dict(plan.authority_context),
            delta=delta if delta is not None else plan.semantic_delta,
            realignment=realignment,
            reversal=reversal,
        )

    def _inspect_state(self, identity: ResumptionIdentity) -> dict[str, Any]:
        assert self.engine is not None
        return dict(
            self.engine.inspect(
                InspectionRequest(
                    target_kind=InspectionTargetKind.REVISION,
                    target_id=identity.revision_id,
                    view=InspectionView.CURRENT_STATE,
                    authority_context={
                        "allowed_scope_ids": [identity.scope_id]
                    },
                )
            ).payload
        )

    def _append_message(
        self,
        *,
        role: str,
        content: str,
        turn_id: str,
        message_id: str = "",
    ) -> dict[str, Any]:
        records = _read_jsonl(self.root / "MESSAGES.jsonl")
        stable_message_id = str(message_id).strip() or f"msg_{uuid.uuid4().hex}"
        existing = next(
            (
                record
                for record in records
                if str(record.get("message_id", "")) == stable_message_id
            ),
            None,
        )
        if existing is not None:
            if (
                str(existing.get("role", "")) != role
                or str(existing.get("content", "")) != content
                or str(existing.get("turn_id", "")) != turn_id
            ):
                raise ValueError(
                    "The stable message identity names different content."
                )
            return existing
        payload = {
            "message_id": stable_message_id,
            "turn_id": turn_id,
            "sequence": len(records) + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(self.root / "MESSAGES.jsonl", payload)
        return payload

    def _resolve_binding(self, run_id: str) -> dict[str, Any]:
        bindings = _read_jsonl(self.root / "RUN_BINDINGS.jsonl")
        normalized_run_id = str(run_id or "").strip()
        if normalized_run_id:
            bindings = [
                binding
                for binding in bindings
                if normalized_run_id
                in {
                    str(binding.get("run_id", "")),
                    str(binding.get("binding_id", "")),
                }
            ]
        else:
            active = _read_json(self.root / "ACTIVE_BINDING.json", default={})
            active_id = str(active.get("binding_id", ""))
            bindings = [
                binding
                for binding in bindings
                if str(binding.get("binding_id", "")) == active_id
            ]
        if not bindings:
            qualifier = f" for run {normalized_run_id}" if normalized_run_id else ""
            raise ValueError(f"No governed run binding is available{qualifier}.")
        return bindings[-1]

    def select_binding(self, run_id: str) -> dict[str, Any]:
        """Select an explicit causal binding for subsequent related turns."""

        binding = self._resolve_binding(run_id)
        _write_json(
            self.root / "ACTIVE_BINDING.json",
            {"binding_id": binding["binding_id"]},
        )
        return binding


def _current_items(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["item_id"]): dict(item)
        for item in (
            *state.get("achieved", ()),
            *state.get("non_achievedness", ()),
        )
    }


def _materialize_item(
    proposal: SemanticItemProposal,
    *,
    message_id: str,
    turn_id: str,
    destination: str,
    semantic_key: str = "",
) -> SemanticItem:
    key = str(semantic_key or proposal.selector).strip()
    if not key:
        raise ConversationPlanningError(
            "Proposed semantic material requires a public selector."
        )
    value = str(proposal.value).strip()
    text = str(proposal.text).strip()
    if not value and not text:
        if destination == "non_achievedness":
            text = f"{key} is unresolved."
        else:
            raise ConversationPlanningError(
                f"Proposed semantic material has no value or text: {key}"
            )
    kind = str(proposal.kind or "fact").strip()
    if destination == "non_achievedness" and kind.casefold() == "fact":
        kind = "requirement"
    payload: dict[str, Any] = {"semantic_key": key}
    if value:
        payload["value"] = value
    if text:
        payload["text"] = text
    elif value:
        payload["text"] = f"{key}: {value}"
    return SemanticItem(
        item_id=_stable_local_id(
            "item",
            message_id,
            destination,
            key,
        ),
        kind=kind,
        payload=payload,
        evidence_references=(message_id,),
        provenance_references=(turn_id,),
    )


def _proposal_destination(proposal: SemanticItemProposal) -> str:
    normalized = proposal.kind.strip().casefold().replace("-", "_")
    if normalized in {
        "requirement",
        "not",
        "non_achieved",
        "non_achievedness",
        "unknown",
        "obligation",
    }:
        return "non_achievedness"
    return "achieved"


def _normalize_direct_semantic_proposals(
    proposal: ConversationPlanProposal,
    *,
    operation: OperationKind,
    parent_state: dict[str, Any] | None,
) -> tuple[tuple[SemanticItemProposal, ...], tuple[SemanticItemProposal, ...]]:
    non_achieved = list(proposal.non_achieved_items)
    explicit_non_achieved = {
        _selector_token(item.selector)
        for item in non_achieved
        if _selector_token(item.selector)
    }
    achieved: list[SemanticItemProposal] = []
    for item in proposal.achieved_items:
        selector = _selector_token(item.selector)
        misplaced_requirement = (
            not item.value.strip()
            and _proposal_destination(item) == "non_achievedness"
        )
        if not misplaced_requirement:
            achieved.append(item)
            continue
        if selector not in explicit_non_achieved:
            non_achieved.append(item)
            explicit_non_achieved.add(selector)
    if parent_state is None or operation not in {
        OperationKind.AUGMENT,
        OperationKind.CONTINUE,
    }:
        return tuple(achieved), tuple(non_achieved)

    current = {
        _selector_token(_semantic_key(item)): item
        for item in _current_items(parent_state).values()
        if _selector_token(_semantic_key(item))
    }
    current_non_achieved_ids = {
        str(candidate.get("item_id", ""))
        for candidate in parent_state.get("non_achievedness", ())
    }

    def new_items(
        items: list[SemanticItemProposal],
        *,
        destination: str,
    ) -> list[SemanticItemProposal]:
        additions: list[SemanticItemProposal] = []
        for item in items:
            selector = _selector_token(item.selector)
            existing = current.get(selector)
            if existing is None:
                additions.append(item)
                continue
            existing_destination = (
                "non_achievedness"
                if str(existing.get("item_id", ""))
                in current_non_achieved_ids
                else "achieved"
            )
            existing_value = _selector_token(
                str(existing.get("payload", {}).get("value", ""))
            )
            proposed_value = _selector_token(item.value)
            is_restatement = (
                existing_destination == destination
                and existing_value == proposed_value
            )
            if is_restatement:
                continue
            raise ConversationPlanningError(
                f"{operation.value} cannot replace current selector "
                f"{item.selector or selector}; the turn must use correction."
            )
        return additions

    achieved = new_items(achieved, destination="achieved")
    non_achieved = new_items(
        non_achieved,
        destination="non_achievedness",
    )
    if operation is OperationKind.AUGMENT and not achieved and not non_achieved:
        raise ConversationPlanningError(
            "Augmentation requires new semantic material after current-state "
            "restatements are removed."
        )
    return tuple(achieved), tuple(non_achieved)


def _identifier_fragment(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return normalized[:48] or "semantic"


def _require_unique_semantic_keys(items: tuple[SemanticItem, ...]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        key = _selector_token(item.payload.get("semantic_key", ""))
        if not key:
            continue
        if key in seen:
            duplicates.add(key)
        seen.add(key)
    if duplicates:
        raise ConversationPlanningError(
            "A plan cannot introduce the same semantic selector twice: "
            + ", ".join(sorted(duplicates))
        )


def _resolve_non_achieved_selector(
    state: dict[str, Any],
    selector: str,
) -> dict[str, Any]:
    selected = _resolve_semantic_selector(state, selector)
    non_achieved_ids = {
        str(item.get("item_id", ""))
        for item in state.get("non_achievedness", ())
    }
    if str(selected.get("item_id", "")) not in non_achieved_ids:
        raise ConversationPlanningError(
            f"Selector is not current non-achievedness: {selector}"
        )
    return selected


def _all_public_selectors(state: dict[str, Any]) -> set[str]:
    public_items = [
        item
        for item in _current_items(state).values()
        if _semantic_key(item)
    ]
    selectors = {
        _selector_token(_semantic_key(item))
        for item in public_items
    }
    if len(selectors) != len(public_items):
        raise ConversationPlanningError(
            "Realignment requires every public semantic item to have a unique "
            "selector."
        )
    return selectors


def _normalized_selectors(selectors: tuple[str, ...]) -> set[str]:
    return {
        _selector_token(selector)
        for selector in selectors
        if _selector_token(selector)
    }


def _explicitly_grounded_selectors(
    state: dict[str, Any],
    prompt: str,
) -> set[str]:
    normalized_prompt = f" {_selector_token(prompt)} "
    grounded: set[str] = set()
    for item in _current_items(state).values():
        selector = _selector_token(_semantic_key(item))
        if not selector:
            continue
        payload = item.get("payload", {})
        value = (
            _selector_token(payload.get("value", ""))
            if isinstance(payload, dict)
            else ""
        )
        if (
            f" {selector} " in normalized_prompt
            or (value and f" {value} " in normalized_prompt)
        ):
            grounded.add(selector)
    return grounded


def _require_partition(
    affected: set[str],
    *,
    retained: set[str],
    superseded: set[str],
    unresolved: set[str],
) -> None:
    classified = retained | superseded | unresolved
    overlaps = (
        (retained & superseded)
        | (retained & unresolved)
        | (superseded & unresolved)
    )
    if classified != affected or overlaps:
        raise ConversationPlanningError(
            "Realignment dispositions must be mutually exclusive and "
            f"exhaustive; unclassified={sorted(affected - classified)}, "
            f"unknown={sorted(classified - affected)}, "
            f"overlap={sorted(overlaps)}."
        )


def _branch_name(value: str) -> str:
    normalized = _identifier_fragment(value)
    if not value.strip() or normalized == "semantic":
        raise ConversationPlanningError(
            "Branch creation requires an explicit public branch name."
        )
    return normalized


def _correction_transition_aliases(revision: dict[str, Any]) -> set[str]:
    state = revision.get("state", {})
    if not isinstance(state, dict):
        return set()
    aliases: set[str] = set()
    items = {
        str(item.get("item_id", "")): item
        for collection in ("achieved", "non_achievedness")
        for item in state.get(collection, ())
        if isinstance(item, dict)
    }
    edges = state.get("supersession_edges", ())
    if not isinstance(edges, (list, tuple)) or not edges:
        return aliases
    edge = edges[-1]
    if not isinstance(edge, dict):
        return aliases
    for item_id in (
        edge.get("prior_item_id"),
        edge.get("replacement_item_id"),
    ):
        normalized_id = _selector_token(item_id)
        if normalized_id:
            aliases.add(normalized_id)
        item = items.get(str(item_id or ""))
        if item is not None:
            key = _selector_token(_semantic_key(item))
            if key:
                aliases.add(key)
    return aliases


def _semantic_key(item: dict[str, Any]) -> str:
    payload = item.get("payload", {})
    if not isinstance(payload, dict):
        return ""
    for key in ("semantic_key", "field", "key", "name", "label"):
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    return ""


def _selector_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def _explicit_binding_aliases(
    prompt: str,
    binding_aliases: dict[str, str],
) -> tuple[str, ...]:
    normalized_prompt = f" {_selector_token(prompt)} "
    return tuple(
        alias
        for alias in binding_aliases
        if f" {_selector_token(alias)} " in normalized_prompt
    )


def _resolve_semantic_selector(
    state: dict[str, Any],
    selector: str,
) -> dict[str, Any]:
    normalized = _selector_token(selector)
    if not normalized:
        raise ValueError(
            "An explicit current semantic item identity or selector is required."
        )
    matches: list[dict[str, Any]] = []
    for item in _current_items(state).values():
        aliases = {
            _selector_token(item.get("item_id", "")),
            _selector_token(item.get("kind", "")),
            _selector_token(_semantic_key(item)),
        }
        aliases.discard("")
        if normalized in aliases:
            matches.append(item)
    if not matches:
        raise ValueError(f"No current semantic item matches selector: {selector}")
    if len(matches) > 1:
        raise ValueError(f"Semantic selector is ambiguous: {selector}")
    return matches[0]


def _resolve_selector_ids(
    state: dict[str, Any],
    selectors: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            str(_resolve_semantic_selector(state, selector)["item_id"])
            for selector in selectors
        )
    )


def _resolve_selected_items(
    state: dict[str, Any],
    item_ids: tuple[str, ...],
    selectors: tuple[str, ...],
) -> tuple[str, ...]:
    current = _current_items(state)
    selected = list(dict.fromkeys(str(item) for item in item_ids if str(item)))
    missing = [item_id for item_id in selected if item_id not in current]
    if missing:
        raise ValueError(
            "Selected semantic material is not current: " + ", ".join(missing)
        )
    selected.extend(_resolve_selector_ids(state, selectors))
    return tuple(dict.fromkeys(selected))


def _select_active_hold(
    state: dict[str, Any],
    target_hold_id: str,
) -> dict[str, Any] | None:
    active_holds = [
        dict(hold)
        for hold in state.get("holds", ())
        if hold.get("disposition", "remain_held") == "remain_held"
    ]
    normalized_hold_id = str(target_hold_id or "").strip()
    if normalized_hold_id:
        selected = next(
            (
                hold
                for hold in active_holds
                if hold.get("hold_id") == normalized_hold_id
            ),
            None,
        )
        if selected is None:
            raise ValueError(f"Unknown active HoldOn: {normalized_hold_id}")
        return selected
    if len(active_holds) == 1:
        return active_holds[0]
    if len(active_holds) > 1:
        raise ValueError(
            "Multiple HoldOn continuations are active; select one explicitly."
        )
    return None


def _attribute_item(
    item: SemanticItem,
    *,
    message_id: str,
    parent_revision_id: str,
    turn_id: str,
) -> SemanticItem:
    return replace(
        item,
        evidence_references=(
            item.evidence_references or (message_id,)
        ),
        provenance_references=tuple(
            dict.fromkeys(
                (
                    *item.provenance_references,
                    parent_revision_id,
                    turn_id,
                )
            )
        ),
    )


def _assistant_text(result: ResumptionResult) -> str:
    final_answer = str(result.presentation.get("final_answer", "") or "").strip()
    if final_answer:
        return final_answer
    outcome = result.semantic_outcome.value if result.semantic_outcome else "ongoing"
    return {
        "paused": "The governed run paused for an explicit boundary contribution.",
        "incomplete": "The governed run is incomplete and remains available for explicit continuation.",
        "exhausted": "The governed run exhausted its current execution bound and remains available for continuation.",
        "ambiguous": "The governed turn requires an explicit disambiguation before state can change.",
        "rejected": "The governed turn was rejected without changing semantic state.",
    }.get(outcome, "The governed run completed without a projected answer.")


def _rendering_report(
    record: RenderingRecord,
    *,
    recovered: bool,
) -> dict[str, Any]:
    return {
        "rendering_attempt_id": record.rendering_attempt_id,
        "result_id": record.result_id,
        "status": (
            "recovered"
            if recovered
            else (
                "rendered"
                if record.status is ConversationActivityStatus.SUCCEEDED
                else record.status.value
            )
        ),
        "presentation": record.presentation,
        "provider_receipt": dict(record.provider_receipt),
        "error": dict(record.error),
    }


def _result_summary(result: ResumptionResult) -> dict[str, Any]:
    return {
        **dict(result.presentation),
        "semantic_outcome": (
            result.semantic_outcome.value
            if result.semantic_outcome is not None
            else None
        ),
        "execution_outcome": result.execution_outcome.value,
        "achieved_item_ids": list(result.achieved_state_summary),
        "non_achievedness_item_ids": list(
            result.non_achievedness_summary
        ),
        "active_hold_ids": list(result.active_hold_summary),
        "diagnostics": dict(result.diagnostics),
    }


def _single_non_achieved_target(state: dict[str, Any]) -> str:
    items = [
        str(item["item_id"])
        for item in state.get("non_achievedness", ())
    ]
    return items[0] if len(items) == 1 else "root"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(dict(payload))
    return records


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_local_id(prefix: str, *parts: str) -> str:
    digest = canonical_payload_digest(
        {
            "identity_kind": prefix,
            "parts": [str(part) for part in parts],
        }
    )
    return f"{prefix}_{digest}"


def _read_json(
    path: Path,
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not path.exists():
        return dict(default or {})
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return dict(payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


__all__ = ["CoreConversationHost"]
