# See MODULES.md for the repository module map before editing.
"""Compatibility and runtime adapters for canonical Blend workflow execution."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_blend_application.workflow_store import JsonBlendWorkflowRepository
from realized_blend.context import BlendContext
from realized_blend.execution import (
    BlendResolvedWorkflowStep,
    BlendWorkflowExecutionHalt,
    execute_blend_workflow as _execute_canonical_blend_workflow,
    resolve_blend_skill_workflow_steps,
    resolve_blend_workflow_steps,
    resolve_blend_workflow_steps_from_providers,
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
from realized_blend.workflows import BlendWorkflowPlan
from realized_skill_application.composition import (
    SkillCompositionExecutionEvent,
    execute_skill_composition_plan,
)


class SkillCompositionBlendPort:
    """Adapt the existing composition engine to Blend's neutral composition port."""

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
        result = execute_skill_composition_plan(
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


class UtcBlendClock:
    """Supply the historical UTC ISO timestamp representation."""

    def now(self) -> str:
        return _blend_workflow_execution_timestamp()


class UuidBlendIdentifierFactory:
    """Supply the historical prefixed, twelve-hex-character identifier shape."""

    def new_identifier(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CallbackBlendOperatorInvocationPort:
    """Adapt the historical resolved-step callback to the neutral invocation port."""

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


def _blend_composition_event_from_skill_event(
    event: SkillCompositionExecutionEvent,
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


def _blend_workflow_execution_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_blend_workflow(
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
    return _execute_canonical_blend_workflow(
        session_id=session_id,
        context=context,
        workflow_plan=workflow_plan,
        resolved_steps=resolved_steps,
        capability_name=capability_name,
        target_name=target_name,
        composition_port=SkillCompositionBlendPort(),
        operator_invocation_port=CallbackBlendOperatorInvocationPort(
            resolved_steps=resolved_steps,
            invoke_step=invoke_step,
        ),
        workflow_repository=(
            workflow_repository or JsonBlendWorkflowRepository(root_path)
        ),
        clock=UtcBlendClock(),
        identifier_factory=UuidBlendIdentifierFactory(),
        execution_observer=execution_observer,
    )


def execute_blend_skill_workflow(
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
    return execute_blend_workflow(
        root_path=root_path,
        session_id=session_id,
        context=context,
        workflow_plan=workflow_plan,
        resolved_steps=resolved_steps,
        capability_name=capability_name,
        target_name=target_name,
        invoke_step=invoke_step,
        execution_observer=execution_observer,
        workflow_repository=workflow_repository,
    )


__all__ = [
    "BlendResolvedWorkflowStep",
    "BlendWorkflowExecutionEvent",
    "BlendWorkflowExecutionHalt",
    "CallbackBlendOperatorInvocationPort",
    "SkillCompositionBlendPort",
    "UtcBlendClock",
    "UuidBlendIdentifierFactory",
    "execute_blend_skill_workflow",
    "execute_blend_workflow",
    "resolve_blend_skill_workflow_steps",
    "resolve_blend_workflow_steps",
    "resolve_blend_workflow_steps_from_providers",
]
