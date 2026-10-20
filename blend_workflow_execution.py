# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applied_theory_types import json_safe
from blend_context import BlendContext
from blend_operator import (
    BlendOperator,
    BlendOperatorInvocation,
    blend_operator_applicability,
    new_blend_operator_invocation,
    resolve_blend_operator_target,
)
from blend_operator_store import BlendOperatorProvider, resolve_blend_operator_record_for_workflow_step
from blend_workflow import BlendWorkflowPlan, BlendWorkflowStep, blend_workflow_run_from_skill_compose_result
from blend_workflow_store import persist_blend_workflow_objects
from host_interaction_delegation import normalized_requested_delegation
from semantic_text import collapse_ws
from skill_composition import SkillCompositionExecutionEvent, execute_skill_composition_plan


@dataclass(frozen=True)
class BlendResolvedWorkflowStep:
    workflow_step: BlendWorkflowStep
    operator: Any
    operator_descriptor: BlendOperator
    operator_source: dict[str, Any] = field(default_factory=dict)
    context_applicability: dict[str, Any] = field(default_factory=dict)
    resolved_target: str = ""

    @property
    def step_id(self) -> str:
        return self.workflow_step.step_id

    @property
    def operator_name(self) -> str:
        return self.workflow_step.operator_name

    @property
    def semantic_unit(self) -> str:
        return self.workflow_step.semantic_unit

    @property
    def requested_delegation(self) -> tuple[dict[str, Any], ...]:
        return self.workflow_step.requested_delegation

    @property
    def rationale(self) -> str:
        return self.workflow_step.rationale

    def to_skill_composition_step(self) -> dict[str, Any]:
        return {
            "step_id": self.workflow_step.step_id,
            "skill": self.operator,
            "bindings": [item.to_dict() for item in self.workflow_step.bindings],
            "run_if": [item.to_dict() for item in self.workflow_step.run_if],
            "iterate_until": [item.to_dict() for item in self.workflow_step.iterate_until],
            "branch_label": self.workflow_step.branch_label,
        }


class BlendWorkflowExecutionHalt(RuntimeError):
    def __init__(self, *, step_id: str, operator_name: str, result: dict[str, Any]) -> None:
        self.step_id = step_id
        self.operator_name = operator_name
        self.result = dict(result)
        super().__init__(f"Blend workflow halted at step {step_id!r} for {operator_name!r}.")


def _blend_workflow_execution_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BlendWorkflowExecutionEvent:
    kind: str
    workflow_execution_id: str
    workflow_id: str
    session_id: str
    capability_name: str
    target_name: str
    timestamp: str
    workflow_run_id: str = ""
    step_id: str = ""
    operator_name: str = ""
    operator_kind: str = ""
    iteration: int = 0
    branch_label: str = ""
    status: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "kind": self.kind,
                "workflow_execution_id": self.workflow_execution_id,
                "workflow_id": self.workflow_id,
                "workflow_run_id": self.workflow_run_id,
                "session_id": self.session_id,
                "capability_name": self.capability_name,
                "target_name": self.target_name,
                "timestamp": self.timestamp,
                "step_id": self.step_id,
                "operator_name": self.operator_name,
                "operator_kind": self.operator_kind,
                "iteration": self.iteration,
                "branch_label": self.branch_label,
                "status": self.status,
                "payload": self.payload,
            }
        )


def _emit_blend_workflow_execution_event(
    execution_observer: Callable[[BlendWorkflowExecutionEvent], None] | None,
    event: BlendWorkflowExecutionEvent,
) -> None:
    if execution_observer is None:
        return
    try:
        execution_observer(event)
    except Exception:
        return


def resolve_blend_workflow_steps(
    workflow_plan: BlendWorkflowPlan,
    *,
    context: BlendContext,
    resolve_operator: Callable[[BlendWorkflowStep, BlendContext], tuple[Any, dict[str, Any], BlendOperator] | None],
) -> tuple[list[BlendResolvedWorkflowStep], list[str]]:
    resolved_steps: list[BlendResolvedWorkflowStep] = []
    ordered_operator_names: list[str] = []
    seen_step_ids: set[str] = set()
    for workflow_step in workflow_plan.steps:
        step_id = collapse_ws(workflow_step.step_id)
        operator_name = collapse_ws(workflow_step.operator_name)
        if not step_id:
            raise ValueError("Each Blend workflow step requires a non-empty step_id.")
        if step_id in seen_step_ids:
            raise ValueError(f"Duplicate Blend workflow step_id {step_id!r}.")
        if not operator_name:
            raise ValueError(f"Blend workflow step {step_id!r} requires a non-empty operator_name.")
        seen_step_ids.add(step_id)
        resolved = resolve_operator(workflow_step, context)
        if resolved is None:
            raise ValueError(f"No workflow operator matches {operator_name!r}.")
        operator, operator_source, operator_descriptor = resolved
        applicability = blend_operator_applicability(operator_descriptor, context)
        if applicability.get("status") != "applicable":
            raise ValueError(
                f"Blend workflow step {step_id!r} is not applicable under the current context: {json.dumps(json_safe(applicability), sort_keys=True)}"
            )
        requested_target = collapse_ws(str(workflow_step.metadata.get("target", "")))
        resolved_target = resolve_blend_operator_target(
            operator_descriptor,
            context,
            requested_target=requested_target,
        )
        if not resolved_target and (
            requested_target
            or operator_descriptor.target_resolution.get("default_target")
            or operator_descriptor.target_resolution.get("allowed_targets")
        ):
            raise ValueError(
                f"Blend workflow step {step_id!r} could not resolve a valid target under the current context."
            )
        resolved_steps.append(
            BlendResolvedWorkflowStep(
                workflow_step=workflow_step,
                operator=operator,
                operator_descriptor=operator_descriptor,
                operator_source=dict(operator_source),
                context_applicability=applicability,
                resolved_target=resolved_target,
            )
        )
        ordered_operator_names.append(operator_name)
    if not resolved_steps:
        raise ValueError("Blend workflow execution requires at least one step.")
    return resolved_steps, ordered_operator_names


def resolve_blend_skill_workflow_steps(
    workflow_plan: BlendWorkflowPlan,
    *,
    context: BlendContext,
    resolve_operator: Callable[[BlendWorkflowStep, BlendContext], tuple[Any, dict[str, Any], BlendOperator] | None],
) -> tuple[list[BlendResolvedWorkflowStep], list[str]]:
    return resolve_blend_workflow_steps(
        workflow_plan,
        context=context,
        resolve_operator=resolve_operator,
    )


def resolve_blend_workflow_steps_from_providers(
    workflow_plan: BlendWorkflowPlan,
    *,
    context: BlendContext,
    providers: Sequence[BlendOperatorProvider],
) -> tuple[list[BlendResolvedWorkflowStep], list[str]]:
    return resolve_blend_workflow_steps(
        workflow_plan,
        context=context,
        resolve_operator=lambda workflow_step, _context: (
            (
                record.operator,
                dict(record.operator_source),
                record.operator_descriptor,
            )
            if (
                record := resolve_blend_operator_record_for_workflow_step(
                    workflow_step,
                    context=_context,
                    providers=providers,
                )
            )
            is not None
            else None
        ),
    )


def execute_blend_workflow(
    *,
    root_path: Path,
    session_id: str,
    context: BlendContext,
    workflow_plan: BlendWorkflowPlan,
    resolved_steps: Sequence[BlendResolvedWorkflowStep],
    capability_name: str,
    target_name: str,
    invoke_step: Callable[[BlendResolvedWorkflowStep, BlendOperatorInvocation], dict[str, Any]],
    execution_observer: Callable[[BlendWorkflowExecutionEvent], None] | None = None,
) -> dict[str, Any]:
    workflow_execution_id = f"bwf_exec_{uuid.uuid4().hex[:12]}"
    started_at = _blend_workflow_execution_timestamp()
    step_results: dict[str, dict[str, Any]] = {}
    steps_by_id = {item.step_id: item for item in resolved_steps}
    ordered_operator_names = [item.operator_name for item in resolved_steps]
    requested_skill_titles = [
        item.operator_name
        for item in resolved_steps
        if collapse_ws(item.workflow_step.operator_kind or "skill") == "skill"
    ]
    composition_steps = [item.to_skill_composition_step() for item in resolved_steps]
    _emit_blend_workflow_execution_event(
        execution_observer,
        BlendWorkflowExecutionEvent(
            kind="blend_workflow_started",
            workflow_execution_id=workflow_execution_id,
            workflow_id=workflow_plan.workflow_id,
            session_id=session_id,
            capability_name=capability_name,
            target_name=target_name,
            timestamp=started_at,
            payload={
                "workflow_kind": workflow_plan.workflow_kind,
                "step_count": len(resolved_steps),
                "requested_operator_names": list(ordered_operator_names),
                "requested_skill_titles": list(requested_skill_titles),
            },
        ),
    )

    def _observe_skill_composition_event(event: SkillCompositionExecutionEvent) -> None:
        resolved_step = steps_by_id.get(event.step_id)
        _emit_blend_workflow_execution_event(
            execution_observer,
            BlendWorkflowExecutionEvent(
                kind=f"blend_{event.kind}",
                workflow_execution_id=workflow_execution_id,
                workflow_id=workflow_plan.workflow_id,
                session_id=session_id,
                capability_name=capability_name,
                target_name=target_name,
                timestamp=_blend_workflow_execution_timestamp(),
                step_id=event.step_id,
                operator_name=resolved_step.operator_name if resolved_step is not None else event.title,
                operator_kind=(
                    collapse_ws(str(resolved_step.workflow_step.operator_kind or "skill"))
                    if resolved_step is not None
                    else "skill"
                ),
                iteration=event.iteration,
                branch_label=event.branch_label,
                status=event.status,
                payload=event.to_dict(),
            ),
        )

    def invoker(step_id: str, _skill_ir: dict[str, Any], payload: dict[str, Any]) -> Any:
        resolved_step = steps_by_id[step_id]
        invocation = new_blend_operator_invocation(
            operator=resolved_step.operator_descriptor,
            session_id=session_id,
            workflow_id=workflow_plan.workflow_id,
            step_id=resolved_step.step_id,
            context=context,
            inputs=payload,
            resolved_target=resolved_step.resolved_target or target_name,
            policy_state={
                "policy_requirements": list(resolved_step.operator_descriptor.policy_requirements),
                "requested_delegation": [dict(item) for item in resolved_step.requested_delegation],
            },
            metadata={
                "semantic_unit": resolved_step.semantic_unit,
                "operator_source": dict(resolved_step.operator_source),
            },
        )
        step_result = invoke_step(resolved_step, invocation)
        step_results[step_id] = dict(step_result)
        if collapse_ws(str(step_result.get("status", ""))).casefold() != "ok":
            raise BlendWorkflowExecutionHalt(
                step_id=resolved_step.step_id,
                operator_name=resolved_step.operator_name,
                result=step_result,
            )
        output_value = _skill_composition_output_value(step_result)
        if output_value is None:
            return str(step_result.get("answer", "") or "")
        return output_value

    try:
        execution = execute_skill_composition_plan(
            composition_steps,
            invoker=invoker,
            root_inputs=workflow_plan.root_inputs,
            root_references=workflow_plan.root_references,
            execution_observer=_observe_skill_composition_event,
        )
    except BlendWorkflowExecutionHalt as exc:
        halted_result = dict(exc.result)
        all_step_results = [*step_results.values(), halted_result]
        finished_at = _blend_workflow_execution_timestamp()
        response = {
            "status": collapse_ws(str(halted_result.get("status", ""))) or "error",
            "capability": capability_name,
            "target": target_name,
            "workflow_execution_id": workflow_execution_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "blocked_step_id": exc.step_id,
            "blocked_operator_name": exc.operator_name,
            "blocked_skill_title": exc.operator_name,
            "requested_operator_names": ordered_operator_names,
            "requested_skill_titles": requested_skill_titles,
            "requested_delegation": _aggregated_composition_delegation(all_step_results, "requested_delegation"),
            "approved_delegation": _aggregated_composition_delegation(all_step_results, "approved_delegation"),
            "escalated_delegation": _aggregated_composition_delegation(all_step_results, "escalated_delegation"),
            "granted_delegation": _aggregated_composition_delegation(all_step_results, "granted_delegation"),
            "missing_delegation": _aggregated_composition_delegation(all_step_results, "missing_delegation"),
            "unsupported_delegation": _aggregated_composition_delegation(all_step_results, "unsupported_delegation"),
            "step_result": halted_result,
            "answer": collapse_ws(str(halted_result.get("answer", ""))) or f"Workflow halted at {exc.operator_name}.",
            "steps": [
                {
                    "step_id": item.step_id,
                    "operator_kind": item.workflow_step.operator_kind,
                    "operator_name": item.operator_name,
                    "skill_title": item.operator_name,
                    "status": collapse_ws(str(step_results.get(item.step_id, {}).get("status", "ok"))) or "ok",
                }
                for item in resolved_steps
            ],
        }
        return _with_persisted_blend_workflow_objects(
            root_path=root_path,
            session_id=session_id,
            workflow_plan=workflow_plan,
            response=response,
            execution_observer=execution_observer,
            workflow_execution_id=workflow_execution_id,
        )
    except Exception as exc:
        finished_at = _blend_workflow_execution_timestamp()
        response = {
            "status": "error",
            "capability": capability_name,
            "target": target_name,
            "workflow_execution_id": workflow_execution_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "requested_operator_names": ordered_operator_names,
            "requested_skill_titles": requested_skill_titles,
            "error": str(exc),
            "steps": [
                {
                    "step_id": item.step_id,
                    "operator_kind": item.workflow_step.operator_kind,
                    "operator_name": item.operator_name,
                    "skill_title": item.operator_name,
                    "status": collapse_ws(str(step_results.get(item.step_id, {}).get("status", ""))),
                }
                for item in resolved_steps
            ],
        }
        return _with_persisted_blend_workflow_objects(
            root_path=root_path,
            session_id=session_id,
            workflow_plan=workflow_plan,
            response=response,
            execution_observer=execution_observer,
            workflow_execution_id=workflow_execution_id,
        )

    requested_final_output_step = workflow_plan.final_output_step or resolved_steps[-1].step_id
    final_output_step = requested_final_output_step
    final_output = execution.final_outputs_by_step.get(final_output_step)
    if final_output_step not in execution.final_outputs_by_step:
        for item in reversed(execution.steps):
            candidate_step_id = collapse_ws(str(item.get("step_id", "")))
            candidate_status = collapse_ws(str(item.get("status", ""))).casefold()
            if candidate_status == "ok" and candidate_step_id in execution.final_outputs_by_step:
                final_output_step = candidate_step_id
                final_output = execution.final_outputs_by_step.get(candidate_step_id)
                break
    final_step_result = step_results.get(final_output_step, {})
    answer = collapse_ws(str(final_step_result.get("answer", ""))) or _skill_composition_render_answer(final_output)

    enriched_steps: list[dict[str, Any]] = []
    for item in execution.steps:
        step_id = collapse_ws(str(item.get("step_id", "")))
        resolved_step = steps_by_id.get(step_id)
        step_result = step_results.get(step_id, {})
        enriched_steps.append(
            json_safe(
                {
                    **dict(item),
                    "operator_kind": resolved_step.workflow_step.operator_kind if resolved_step is not None else "",
                    "operator_name": resolved_step.operator_name if resolved_step is not None else "",
                    "skill_title": resolved_step.operator_name if resolved_step is not None else "",
                    "operator": (
                        resolved_step.operator_descriptor.to_dict()
                        if resolved_step is not None
                        else {}
                    ),
                    "skill_source": dict(resolved_step.operator_source) if resolved_step is not None else {},
                    "resolved_target": resolved_step.resolved_target if resolved_step is not None else "",
                    "context_applicability": (
                        dict(resolved_step.context_applicability)
                        if resolved_step is not None
                        else {}
                    ),
                    "executor_framework": step_result.get("executor_framework", ""),
                    "answer": step_result.get("answer", ""),
                    "parsed_output": step_result.get("parsed_output"),
                    "result_payload": step_result.get("result_payload"),
                }
            )
        )

    all_step_results = list(step_results.values())
    finished_at = _blend_workflow_execution_timestamp()
    response = {
        "status": "ok",
        "capability": capability_name,
        "target": target_name,
        "workflow_execution_id": workflow_execution_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "requested_operator_names": ordered_operator_names,
        "requested_skill_titles": requested_skill_titles,
        "plan_authorities": execution.plan_authorities,
        "final_output_step": final_output_step,
        "final_output": json_safe(final_output),
        "final_outputs_by_step": execution.final_outputs_by_step,
        "steps": enriched_steps,
        "requested_delegation": _aggregated_composition_delegation(all_step_results, "requested_delegation"),
        "approved_delegation": _aggregated_composition_delegation(all_step_results, "approved_delegation"),
        "escalated_delegation": _aggregated_composition_delegation(all_step_results, "escalated_delegation"),
        "granted_delegation": _aggregated_composition_delegation(all_step_results, "granted_delegation"),
        "missing_delegation": _aggregated_composition_delegation(all_step_results, "missing_delegation"),
        "unsupported_delegation": _aggregated_composition_delegation(all_step_results, "unsupported_delegation"),
        "answer": answer,
    }
    return _with_persisted_blend_workflow_objects(
        root_path=root_path,
        session_id=session_id,
        workflow_plan=workflow_plan,
        response=response,
        execution_observer=execution_observer,
        workflow_execution_id=workflow_execution_id,
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
    invoke_step: Callable[[BlendResolvedWorkflowStep, BlendOperatorInvocation], dict[str, Any]],
    execution_observer: Callable[[BlendWorkflowExecutionEvent], None] | None = None,
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
    )


def _with_persisted_blend_workflow_objects(
    *,
    root_path: Path,
    session_id: str,
    workflow_plan: BlendWorkflowPlan,
    response: dict[str, Any],
    execution_observer: Callable[[BlendWorkflowExecutionEvent], None] | None = None,
    workflow_execution_id: str = "",
) -> dict[str, Any]:
    finished_event_kind = (
        "blend_workflow_completed"
        if collapse_ws(str(response.get("status", ""))).casefold() == "ok"
        else "blend_workflow_failed"
    )
    _emit_blend_workflow_execution_event(
        execution_observer,
        BlendWorkflowExecutionEvent(
            kind=finished_event_kind,
            workflow_execution_id=collapse_ws(workflow_execution_id),
            workflow_id=workflow_plan.workflow_id,
            session_id=session_id,
            capability_name=collapse_ws(str(response.get("capability", ""))),
            target_name=collapse_ws(str(response.get("target", ""))),
            timestamp=collapse_ws(str(response.get("finished_at", ""))) or _blend_workflow_execution_timestamp(),
            status=collapse_ws(str(response.get("status", ""))),
            payload={
                "final_output_step": collapse_ws(str(response.get("final_output_step", ""))),
                "blocked_step_id": collapse_ws(str(response.get("blocked_step_id", ""))),
                "blocked_operator_name": collapse_ws(str(response.get("blocked_operator_name", ""))),
                "error": collapse_ws(str(response.get("error", ""))),
            },
        ),
    )
    workflow_run = blend_workflow_run_from_skill_compose_result(plan=workflow_plan, result=response)
    persisted_plan, persisted_run, workflow_store = persist_blend_workflow_objects(
        root_path=root_path,
        plan=workflow_plan,
        run=workflow_run,
        session_id=session_id,
    )
    enriched_response = dict(response)
    enriched_response["workflow_id"] = persisted_plan.workflow_id
    enriched_response["workflow_run_id"] = persisted_run.workflow_run_id
    enriched_response["session_id"] = persisted_run.session_id
    enriched_response["started_at"] = persisted_run.started_at
    enriched_response["finished_at"] = persisted_run.finished_at
    enriched_response["workflow_plan"] = persisted_plan.to_dict()
    enriched_response["workflow_run"] = persisted_run.to_dict()
    enriched_response["workflow_store"] = workflow_store
    _emit_blend_workflow_execution_event(
        execution_observer,
        BlendWorkflowExecutionEvent(
            kind="blend_workflow_persisted",
            workflow_execution_id=collapse_ws(workflow_execution_id),
            workflow_id=persisted_plan.workflow_id,
            workflow_run_id=persisted_run.workflow_run_id,
            session_id=persisted_run.session_id,
            capability_name=collapse_ws(str(response.get("capability", ""))),
            target_name=collapse_ws(str(response.get("target", ""))),
            timestamp=persisted_run.finished_at or _blend_workflow_execution_timestamp(),
            status=persisted_run.status,
            payload={
                "workflow_store": dict(workflow_store),
                "workflow_kind": persisted_plan.workflow_kind,
            },
        ),
    )
    return enriched_response


def _aggregated_composition_delegation(
    step_results: list[dict[str, Any]],
    key: str,
) -> list[dict[str, Any]]:
    aggregated: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for result in step_results:
        for item in normalized_requested_delegation(result.get(key)):
            signature = (
                collapse_ws(str(item.get("capability", ""))),
                collapse_ws(str(item.get("target", ""))),
                collapse_ws(str(item.get("rationale", ""))),
            )
            if signature in seen:
                continue
            seen.add(signature)
            aggregated.append(item)
    return aggregated


def _skill_composition_output_value(step_result: dict[str, Any]) -> Any:
    result_payload = step_result.get("result_payload")
    if result_payload is not None:
        if isinstance(result_payload, Mapping) and len(result_payload) == 1:
            for generic_key in ("result", "value", "output", "answer", "data", "item"):
                if generic_key in result_payload:
                    return result_payload[generic_key]
        return result_payload
    parsed_output = step_result.get("parsed_output")
    if parsed_output is not None:
        if isinstance(parsed_output, Mapping) and len(parsed_output) == 1:
            for generic_key in ("result", "value", "output", "answer", "data", "item"):
                if generic_key in parsed_output:
                    return parsed_output[generic_key]
        return parsed_output
    answer = str(step_result.get("answer", "") or "").strip()
    if answer:
        return answer
    return None


def _skill_composition_render_answer(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping) or isinstance(value, list):
        return json.dumps(json_safe(value), indent=2, sort_keys=True)
    return str(value)
