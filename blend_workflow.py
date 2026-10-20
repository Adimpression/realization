# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from pathlib import Path
from typing import Any

from blend_workflow_models import (
    BlendWorkflowBinding,
    BlendWorkflowCondition,
    BlendWorkflowPlan,
    BlendWorkflowRun,
    BlendWorkflowStep,
)
from semantic_text import collapse_ws


def blend_workflow_plan_from_skill_compose_arguments(arguments: dict[str, Any]) -> BlendWorkflowPlan:
    workflow_payload = arguments.get("workflow_plan")
    if isinstance(workflow_payload, dict):
        return BlendWorkflowPlan.from_dict(dict(workflow_payload))
    steps = []
    for raw_step in arguments.get("steps", []):
        if not isinstance(raw_step, dict):
            continue
        steps.append(
            BlendWorkflowStep(
                step_id=collapse_ws(str(raw_step.get("step_id", ""))),
                operator_kind="skill",
                operator_name=collapse_ws(str(raw_step.get("skill_title", ""))),
                semantic_unit=collapse_ws(str(raw_step.get("semantic_unit", ""))),
                bindings=tuple(
                    BlendWorkflowBinding.from_dict(dict(item))
                    for item in raw_step.get("bindings", [])
                    if isinstance(item, dict)
                ),
                run_if=tuple(
                    BlendWorkflowCondition.from_dict(dict(item))
                    for item in raw_step.get("run_if", [])
                    if isinstance(item, dict)
                ),
                iterate_until=tuple(
                    BlendWorkflowCondition.from_dict(dict(item))
                    for item in raw_step.get("iterate_until", [])
                    if isinstance(item, dict)
                ),
                branch_label=collapse_ws(str(raw_step.get("branch_label", ""))),
                requested_delegation=tuple(
                    dict(item) for item in raw_step.get("requested_delegation", []) if isinstance(item, dict)
                ),
                rationale=str(raw_step.get("rationale", "")),
                metadata={"target": collapse_ws(str(raw_step.get("target", "")))},
            )
        )
    return BlendWorkflowPlan(
        workflow_id="",
        workflow_kind="skill_compose",
        steps=tuple(steps),
        session_id=collapse_ws(str(arguments.get("session_id", ""))),
        created_at=collapse_ws(str(arguments.get("created_at", ""))),
        root_inputs=dict(arguments.get("root_inputs", {})),
        root_references=dict(arguments.get("root_references", {})),
        final_output_step=collapse_ws(str(arguments.get("final_output_step", ""))),
        metadata={"target": collapse_ws(str(arguments.get("target", ""))) or "skills"},
    )


def skill_compose_arguments_from_blend_workflow_plan(plan: BlendWorkflowPlan) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "steps": [],
        "root_inputs": dict(plan.root_inputs),
    }
    if plan.root_references:
        payload["root_references"] = dict(plan.root_references)
    if plan.final_output_step:
        payload["final_output_step"] = plan.final_output_step
    target = collapse_ws(str(plan.metadata.get("target", ""))) or "skills"
    payload["target"] = target
    for step in plan.steps:
        if collapse_ws(str(step.operator_kind or "skill")) != "skill":
            raise ValueError(f"Unsupported Blend workflow operator_kind {step.operator_kind!r}; only 'skill' is supported.")
        step_payload: dict[str, Any] = {
            "step_id": step.step_id,
            "skill_title": step.operator_name,
        }
        if step.semantic_unit:
            step_payload["semantic_unit"] = step.semantic_unit
        bindings = [item.to_dict() for item in step.bindings]
        if bindings:
            step_payload["bindings"] = bindings
        run_if = [item.to_dict() for item in step.run_if]
        if run_if:
            step_payload["run_if"] = run_if
        iterate_until = [item.to_dict() for item in step.iterate_until]
        if iterate_until:
            step_payload["iterate_until"] = iterate_until
        if step.branch_label:
            step_payload["branch_label"] = step.branch_label
        requested_delegation = [dict(item) for item in step.requested_delegation]
        if requested_delegation:
            step_payload["requested_delegation"] = requested_delegation
        if step.rationale:
            step_payload["rationale"] = step.rationale
        step_target = collapse_ws(str(step.metadata.get("target", "")))
        if step_target and step_target != target:
            step_payload["target"] = step_target
        payload["steps"].append(step_payload)
    return payload


def blend_workflow_run_from_skill_compose_result(
    *,
    plan: BlendWorkflowPlan,
    result: dict[str, Any],
) -> BlendWorkflowRun:
    return BlendWorkflowRun(
        workflow_run_id=collapse_ws(str(result.get("workflow_run_id", ""))),
        workflow_id=collapse_ws(str(result.get("workflow_id", ""))) or plan.workflow_id,
        plan=plan,
        status=collapse_ws(str(result.get("status", ""))),
        session_id=collapse_ws(str(result.get("session_id", ""))) or plan.session_id,
        started_at=collapse_ws(str(result.get("started_at", ""))),
        finished_at=collapse_ws(str(result.get("finished_at", ""))),
        final_output_step=collapse_ws(str(result.get("final_output_step", ""))),
        final_output=result.get("final_output"),
        final_outputs_by_step=dict(result.get("final_outputs_by_step", {})),
        steps=[dict(item) for item in result.get("steps", []) if isinstance(item, dict)],
        plan_authorities=[str(item) for item in result.get("plan_authorities", [])],
        metadata={
            "capability": collapse_ws(str(result.get("capability", ""))),
            "target": collapse_ws(str(result.get("target", ""))),
            "requested_skill_titles": [str(item) for item in result.get("requested_skill_titles", [])],
        },
    )


def load_blend_workflow_plan(root_path: Path, workflow_id: str) -> BlendWorkflowPlan:
    from blend_workflow_store import load_blend_workflow_plan as _impl

    return _impl(root_path, workflow_id)


def load_blend_workflow_run(root_path: Path, workflow_run_id: str) -> BlendWorkflowRun:
    from blend_workflow_store import load_blend_workflow_run as _impl

    return _impl(root_path, workflow_run_id)


def load_blend_workflow_index(root_path: Path) -> dict[str, Any]:
    from blend_workflow_store import load_blend_workflow_index as _impl

    return _impl(root_path)


def list_blend_workflow_summaries(
    root_path: Path,
    *,
    kind: str = "runs",
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    from blend_workflow_store import list_blend_workflow_summaries as _impl

    return _impl(root_path, kind=kind, status=status, limit=limit)


def persist_blend_workflow_objects(
    *,
    root_path: Path,
    plan: BlendWorkflowPlan,
    run: BlendWorkflowRun,
    session_id: str = "",
) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
    from blend_workflow_store import persist_blend_workflow_objects as _impl

    return _impl(root_path=root_path, plan=plan, run=run, session_id=session_id)


def ensure_blend_workflow_store(root_path: Path) -> dict[str, Path]:
    from blend_workflow_store import ensure_blend_workflow_store as _impl

    return _impl(root_path)
