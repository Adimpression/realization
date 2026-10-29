"""Workstation-to-Blend value adapters."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_blend_application.workflow_store import JsonBlendWorkflowRepository
from realized_blend.context import BlendContext, BlendContextAttachment
from realized_blend.execution import (
    BlendResolvedWorkflowStep,
    execute_blend_workflow as execute_canonical_blend_workflow,
)
from realized_blend.observations import BlendWorkflowExecutionEvent
from realized_blend.operators import BlendOperator, BlendOperatorInvocation
from realized_blend.ports import (
    BlendCompositionExecutionEvent,
    BlendCompositionExecutionResult,
    BlendCompositionInvoker,
    BlendCompositionObserver,
    BlendWorkflowRepository,
)
from realized_blend.sessions import BlendSession
from realized_blend.workflows import BlendWorkflowPlan
from workstation.foundation.models import WorkstationSession
from workstation.skills.planning.skill_composition_planning import (
    execute_workstation_skill_composition_plan,
)


def _stable_unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def blend_context_from_workstation_session(session: WorkstationSession) -> BlendContext:
    """Translate workstation-owned active state into a neutral Blend context."""
    attachments = tuple(
        BlendContextAttachment(
            name=str(attachment.name),
            kind=str(attachment.kind),
            source=str(attachment.source),
            access_mode=str(attachment.access_mode),
            mount_path=str(attachment.mount_path),
            alias_of=str(attachment.metadata.get("alias_of", "")),
            metadata=dict(attachment.metadata),
        )
        for attachment in session.attachments
    )
    visible_mounts = _stable_unique(
        [
            attachment.name
            for attachment in attachments
            if attachment.kind != "secret_ref" and attachment.access_mode != "indirect"
        ]
    )
    writable_mounts = _stable_unique(
        [
            attachment.name
            for attachment in attachments
            if "write" in attachment.access_mode
        ]
    )
    granted_capabilities = _stable_unique([str(item) for item in session.allowed_capabilities])
    world_ids = _stable_unique(
        [str(attachment.metadata.get("blend_world_id", "")) for attachment in session.attachments]
    )
    world_roots = _stable_unique(
        [str(attachment.metadata.get("blend_world_root", "")) for attachment in session.attachments]
    )
    world_mounts = _stable_unique(
        [str(attachment.metadata.get("blend_world_mount", "")) for attachment in session.attachments]
    )
    return BlendContext(
        attachments=attachments,
        visible_mounts=visible_mounts,
        writable_mounts=writable_mounts,
        granted_capabilities=granted_capabilities,
        task_focus=str(session.initial_task or ""),
        world_id=world_ids[0] if world_ids else "",
        world_root=world_roots[0] if world_roots else "",
        world_mounts=world_mounts,
    )


def blend_session_from_workstation_session(
    session: WorkstationSession,
    *,
    actor_kind: str = "ai_chat",
    projection_kind: str = "ai_chat",
) -> BlendSession:
    """Translate a workstation session into the neutral Blend session value."""
    return BlendSession(
        session_id=str(session.session_id),
        root_path=str(session.root_path),
        created_at=str(session.created_at),
        actor_kind=actor_kind,
        projection_kind=projection_kind,
        context=blend_context_from_workstation_session(session),
        initial_task=str(session.initial_task or ""),
        metadata={
            "source_kind": "workstation_session",
            "openai_profile": session.openai_profile,
            "openai_env_var": session.openai_env_var,
        },
    )


class WorkstationSkillCompositionBlendPort:
    """Adapt the workstation's existing composition engine to Blend."""

    def execute(
        self,
        *,
        steps: Sequence[dict[str, Any]],
        invoker: BlendCompositionInvoker,
        root_inputs: Mapping[str, Any],
        root_references: Mapping[str, Any],
        execution_observer: BlendCompositionObserver | None = None,
    ) -> BlendCompositionExecutionResult:
        observer = (
            None
            if execution_observer is None
            else lambda event: execution_observer(
                _blend_composition_event_from_skill_event(event)
            )
        )
        result = execute_workstation_skill_composition_plan(
            steps,
            invoker=invoker,
            root_inputs=root_inputs,
            root_references=root_references,
            execution_observer=observer,
        )
        return BlendCompositionExecutionResult(
            steps=[dict(item) for item in result.steps],
            plan_authorities=list(result.plan_authorities),
            final_outputs_by_step=dict(result.final_outputs_by_step),
        )


class WorkstationBlendClock:
    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


class WorkstationBlendIdentifierFactory:
    def new_identifier(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkstationBlendOperatorInvocationPort:
    def __init__(
        self,
        *,
        resolved_steps: Sequence[BlendResolvedWorkflowStep],
        invoke_step: Callable[
            [BlendResolvedWorkflowStep, BlendOperatorInvocation],
            dict[str, Any],
        ],
    ) -> None:
        self._resolved_steps = {item.step_id: item for item in resolved_steps}
        self._invoke_step = invoke_step

    def invoke(
        self,
        *,
        operator: BlendOperator,
        invocation: BlendOperatorInvocation,
        handle: Any,
    ) -> dict[str, Any]:
        del operator, handle
        return self._invoke_step(
            self._resolved_steps[invocation.step_id],
            invocation,
        )


def execute_workstation_blend_workflow(
    *,
    root_path: Path,
    session_id: str,
    context: BlendContext,
    workflow_plan: BlendWorkflowPlan,
    resolved_steps: Sequence[BlendResolvedWorkflowStep],
    capability_name: str,
    target_name: str,
    invoke_step: Callable[
        [BlendResolvedWorkflowStep, BlendOperatorInvocation],
        dict[str, Any],
    ],
    execution_observer: Callable[[BlendWorkflowExecutionEvent], None] | None = None,
    workflow_repository: BlendWorkflowRepository | None = None,
) -> dict[str, Any]:
    return execute_canonical_blend_workflow(
        session_id=session_id,
        context=context,
        workflow_plan=workflow_plan,
        resolved_steps=resolved_steps,
        capability_name=capability_name,
        target_name=target_name,
        composition_port=WorkstationSkillCompositionBlendPort(),
        operator_invocation_port=WorkstationBlendOperatorInvocationPort(
            resolved_steps=resolved_steps,
            invoke_step=invoke_step,
        ),
        workflow_repository=(
            workflow_repository or JsonBlendWorkflowRepository(root_path)
        ),
        clock=WorkstationBlendClock(),
        identifier_factory=WorkstationBlendIdentifierFactory(),
        execution_observer=execution_observer,
    )


def _blend_composition_event_from_skill_event(
    event: Any,
) -> BlendCompositionExecutionEvent:
    return BlendCompositionExecutionEvent(
        kind=event.kind,
        step_id=event.step_id,
        title=event.title,
        iteration=event.iteration,
        branch_label=event.branch_label,
        status=event.status,
        input_payload=event.input_payload,
        output_payload=event.output_payload,
        binding_receipts=event.binding_receipts,
        condition_receipts=event.condition_receipts,
        skipped_reason=event.skipped_reason,
        error=event.error,
        result_payload=event.result_payload,
    )


__all__ = [
    "WorkstationBlendClock",
    "WorkstationBlendIdentifierFactory",
    "WorkstationBlendOperatorInvocationPort",
    "WorkstationSkillCompositionBlendPort",
    "blend_context_from_workstation_session",
    "blend_session_from_workstation_session",
    "execute_workstation_blend_workflow",
]
