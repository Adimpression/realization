# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from blend_context import BlendContext
from semantic_text import collapse_ws


def _stable_unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = collapse_ws(str(value))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


@dataclass(frozen=True)
class BlendOperator:
    operator_id: str
    operator_kind: str
    display_name: str
    execution_adapter: str
    semantic_description: str = ""
    input_shape: dict[str, Any] = field(default_factory=dict)
    output_shape: dict[str, Any] = field(default_factory=dict)
    policy_requirements: tuple[str, ...] = ()
    actor_visibility: tuple[str, ...] = ()
    context_requirements: dict[str, Any] = field(default_factory=dict)
    target_resolution: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "operator_kind": self.operator_kind,
            "display_name": self.display_name,
            "execution_adapter": self.execution_adapter,
            "semantic_description": self.semantic_description,
            "input_shape": dict(self.input_shape),
            "output_shape": dict(self.output_shape),
            "policy_requirements": list(self.policy_requirements),
            "actor_visibility": list(self.actor_visibility),
            "context_requirements": dict(self.context_requirements),
            "target_resolution": dict(self.target_resolution),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendOperator":
        return cls(
            operator_id=collapse_ws(str(payload.get("operator_id", ""))),
            operator_kind=collapse_ws(str(payload.get("operator_kind", ""))),
            display_name=collapse_ws(str(payload.get("display_name", ""))),
            execution_adapter=collapse_ws(str(payload.get("execution_adapter", ""))),
            semantic_description=str(payload.get("semantic_description", "")),
            input_shape=dict(payload.get("input_shape", {})),
            output_shape=dict(payload.get("output_shape", {})),
            policy_requirements=_stable_unique([str(item) for item in payload.get("policy_requirements", [])]),
            actor_visibility=_stable_unique([str(item) for item in payload.get("actor_visibility", [])]),
            context_requirements=dict(payload.get("context_requirements", {})),
            target_resolution=dict(payload.get("target_resolution", {})),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class BlendOperatorInvocation:
    invocation_id: str
    operator: BlendOperator
    session_id: str
    workflow_id: str
    step_id: str
    context: BlendContext
    inputs: dict[str, Any]
    resolved_target: str = ""
    policy_state: dict[str, Any] = field(default_factory=dict)
    status: str = ""
    outputs: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "operator": self.operator.to_dict(),
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "context": self.context.to_dict(),
            "inputs": dict(self.inputs),
            "resolved_target": self.resolved_target,
            "policy_state": dict(self.policy_state),
            "status": self.status,
            "outputs": self.outputs,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendOperatorInvocation":
        return cls(
            invocation_id=collapse_ws(str(payload.get("invocation_id", ""))),
            operator=BlendOperator.from_dict(dict(payload.get("operator", {}))),
            session_id=collapse_ws(str(payload.get("session_id", ""))),
            workflow_id=collapse_ws(str(payload.get("workflow_id", ""))),
            step_id=collapse_ws(str(payload.get("step_id", ""))),
            context=BlendContext.from_dict(dict(payload.get("context", {}))),
            inputs=dict(payload.get("inputs", {})),
            resolved_target=collapse_ws(str(payload.get("resolved_target", ""))),
            policy_state=dict(payload.get("policy_state", {})),
            status=collapse_ws(str(payload.get("status", ""))),
            outputs=payload.get("outputs"),
            metadata=dict(payload.get("metadata", {})),
        )


def blend_operator_applicability(
    operator: BlendOperator,
    context: BlendContext,
) -> dict[str, Any]:
    requirements = dict(operator.context_requirements)
    required_capabilities = _stable_unique(
        [str(item) for item in requirements.get("required_capabilities", [])]
    )
    required_visible_mounts = _stable_unique(
        [str(item) for item in requirements.get("required_visible_mounts", [])]
    )
    required_writable_mounts = _stable_unique(
        [str(item) for item in requirements.get("required_writable_mounts", [])]
    )
    required_world_mounts = _stable_unique(
        [str(item) for item in requirements.get("required_world_mounts", [])]
    )
    require_shared_world = bool(requirements.get("require_shared_world", False))
    missing_capabilities = [
        capability
        for capability in required_capabilities
        if capability not in context.granted_capabilities
    ]
    missing_visible_mounts = [
        mount
        for mount in required_visible_mounts
        if mount not in context.visible_mounts
    ]
    missing_writable_mounts = [
        mount
        for mount in required_writable_mounts
        if mount not in context.writable_mounts
    ]
    missing_world_mounts = [
        mount
        for mount in required_world_mounts
        if mount not in context.world_mounts
    ]
    missing_shared_world = require_shared_world and not context.world_id
    status = "applicable"
    if (
        missing_capabilities
        or missing_visible_mounts
        or missing_writable_mounts
        or missing_world_mounts
        or missing_shared_world
    ):
        status = "blocked"
    return {
        "status": status,
        "missing_capabilities": missing_capabilities,
        "missing_visible_mounts": missing_visible_mounts,
        "missing_writable_mounts": missing_writable_mounts,
        "missing_world_mounts": missing_world_mounts,
        "missing_shared_world": missing_shared_world,
        "required_capabilities": list(required_capabilities),
        "required_visible_mounts": list(required_visible_mounts),
        "required_writable_mounts": list(required_writable_mounts),
        "required_world_mounts": list(required_world_mounts),
        "require_shared_world": require_shared_world,
    }


def resolve_blend_operator_target(
    operator: BlendOperator,
    context: BlendContext,
    *,
    requested_target: str = "",
) -> str:
    target_rules = dict(operator.target_resolution)
    candidate = collapse_ws(requested_target) or collapse_ws(str(target_rules.get("default_target", "")))
    allowed_targets = _stable_unique([str(item) for item in target_rules.get("allowed_targets", [])])
    require_visible = bool(target_rules.get("require_visible", False))
    require_writable = bool(target_rules.get("require_writable", False))
    if not candidate and allowed_targets:
        for item in allowed_targets:
            if require_visible and item not in context.visible_mounts:
                continue
            if require_writable and item not in context.writable_mounts:
                continue
            candidate = item
            break
    if allowed_targets and candidate and candidate not in allowed_targets:
        return ""
    if require_visible and candidate and candidate not in context.visible_mounts:
        return ""
    if require_writable and candidate and candidate not in context.writable_mounts:
        return ""
    return candidate


def new_blend_operator_invocation(
    *,
    operator: BlendOperator,
    session_id: str,
    workflow_id: str,
    step_id: str,
    context: BlendContext,
    inputs: dict[str, Any],
    resolved_target: str = "",
    policy_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> BlendOperatorInvocation:
    return BlendOperatorInvocation(
        invocation_id=f"bop_inv_{uuid.uuid4().hex[:12]}",
        operator=operator,
        session_id=collapse_ws(session_id),
        workflow_id=collapse_ws(workflow_id),
        step_id=collapse_ws(step_id),
        context=context,
        inputs=dict(inputs),
        resolved_target=collapse_ws(resolved_target),
        policy_state=dict(policy_state or {}),
        metadata=dict(metadata or {}),
    )
