# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from semantic_text import collapse_ws


@dataclass(frozen=True)
class BlendWorkflowBinding:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorkflowBinding":
        return cls(payload=dict(payload))


@dataclass(frozen=True)
class BlendWorkflowCondition:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorkflowCondition":
        return cls(payload=dict(payload))


@dataclass(frozen=True)
class BlendWorkflowStep:
    step_id: str
    operator_kind: str
    operator_name: str
    semantic_unit: str = ""
    bindings: tuple[BlendWorkflowBinding, ...] = ()
    run_if: tuple[BlendWorkflowCondition, ...] = ()
    iterate_until: tuple[BlendWorkflowCondition, ...] = ()
    branch_label: str = ""
    requested_delegation: tuple[dict[str, Any], ...] = ()
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "operator_kind": self.operator_kind,
            "operator_name": self.operator_name,
            "semantic_unit": self.semantic_unit,
            "bindings": [item.to_dict() for item in self.bindings],
            "run_if": [item.to_dict() for item in self.run_if],
            "iterate_until": [item.to_dict() for item in self.iterate_until],
            "branch_label": self.branch_label,
            "requested_delegation": [dict(item) for item in self.requested_delegation],
            "rationale": self.rationale,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorkflowStep":
        return cls(
            step_id=collapse_ws(str(payload.get("step_id", ""))),
            operator_kind=collapse_ws(str(payload.get("operator_kind", ""))) or "skill",
            operator_name=collapse_ws(str(payload.get("operator_name", ""))),
            semantic_unit=collapse_ws(str(payload.get("semantic_unit", ""))),
            bindings=tuple(
                BlendWorkflowBinding.from_dict(dict(item))
                for item in payload.get("bindings", [])
                if isinstance(item, dict)
            ),
            run_if=tuple(
                BlendWorkflowCondition.from_dict(dict(item))
                for item in payload.get("run_if", [])
                if isinstance(item, dict)
            ),
            iterate_until=tuple(
                BlendWorkflowCondition.from_dict(dict(item))
                for item in payload.get("iterate_until", [])
                if isinstance(item, dict)
            ),
            branch_label=collapse_ws(str(payload.get("branch_label", ""))),
            requested_delegation=tuple(
                dict(item) for item in payload.get("requested_delegation", []) if isinstance(item, dict)
            ),
            rationale=str(payload.get("rationale", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class BlendWorkflowPlan:
    workflow_id: str
    workflow_kind: str
    steps: tuple[BlendWorkflowStep, ...]
    session_id: str = ""
    created_at: str = ""
    root_inputs: dict[str, Any] = field(default_factory=dict)
    root_references: dict[str, Any] = field(default_factory=dict)
    final_output_step: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_kind": self.workflow_kind,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "steps": [step.to_dict() for step in self.steps],
            "root_inputs": dict(self.root_inputs),
            "root_references": dict(self.root_references),
            "final_output_step": self.final_output_step,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorkflowPlan":
        return cls(
            workflow_id=collapse_ws(str(payload.get("workflow_id", ""))),
            workflow_kind=collapse_ws(str(payload.get("workflow_kind", ""))) or "skill_compose",
            steps=tuple(
                BlendWorkflowStep.from_dict(dict(item))
                for item in payload.get("steps", [])
                if isinstance(item, dict)
            ),
            session_id=collapse_ws(str(payload.get("session_id", ""))),
            created_at=collapse_ws(str(payload.get("created_at", ""))),
            root_inputs=dict(payload.get("root_inputs", {})),
            root_references=dict(payload.get("root_references", {})),
            final_output_step=collapse_ws(str(payload.get("final_output_step", ""))),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class BlendWorkflowRun:
    workflow_run_id: str
    workflow_id: str
    plan: BlendWorkflowPlan
    status: str
    final_output_step: str
    final_output: Any
    final_outputs_by_step: dict[str, Any]
    steps: list[dict[str, Any]]
    plan_authorities: list[str]
    session_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_run_id": self.workflow_run_id,
            "workflow_id": self.workflow_id,
            "plan": self.plan.to_dict(),
            "status": self.status,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "final_output_step": self.final_output_step,
            "final_output": self.final_output,
            "final_outputs_by_step": dict(self.final_outputs_by_step),
            "steps": [dict(item) for item in self.steps],
            "plan_authorities": list(self.plan_authorities),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorkflowRun":
        return cls(
            workflow_run_id=collapse_ws(str(payload.get("workflow_run_id", ""))),
            workflow_id=collapse_ws(str(payload.get("workflow_id", ""))),
            plan=BlendWorkflowPlan.from_dict(dict(payload.get("plan", {}))),
            status=collapse_ws(str(payload.get("status", ""))),
            session_id=collapse_ws(str(payload.get("session_id", ""))),
            started_at=collapse_ws(str(payload.get("started_at", ""))),
            finished_at=collapse_ws(str(payload.get("finished_at", ""))),
            final_output_step=collapse_ws(str(payload.get("final_output_step", ""))),
            final_output=payload.get("final_output"),
            final_outputs_by_step=dict(payload.get("final_outputs_by_step", {})),
            steps=[dict(item) for item in payload.get("steps", []) if isinstance(item, dict)],
            plan_authorities=[str(item) for item in payload.get("plan_authorities", [])],
            metadata=dict(payload.get("metadata", {})),
        )
