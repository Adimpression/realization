"""Canonical Blend operator values and context interpretation rules."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws

from .context import BlendContext


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


@dataclass(frozen=True)
class BlendOperatorRecord:
    """A descriptor paired with the adapter's opaque invocation handle."""

    operator: Any
    operator_source: dict[str, Any]
    operator_descriptor: BlendOperator

    @property
    def invocation_handle(self) -> Any:
        return self.operator

    def to_summary(self) -> dict[str, Any]:
        descriptor = self.operator_descriptor
        source = dict(self.operator_source)
        return {
            "operator_id": descriptor.operator_id,
            "operator_kind": descriptor.operator_kind,
            "operator_name": descriptor.display_name,
            "display_name": descriptor.display_name,
            "execution_adapter": descriptor.execution_adapter,
            "semantic_description": descriptor.semantic_description,
            "policy_requirements": list(descriptor.policy_requirements),
            "actor_visibility": list(descriptor.actor_visibility),
            "context_requirements": dict(descriptor.context_requirements),
            "target_resolution": dict(descriptor.target_resolution),
            "source_kind": collapse_ws(str(source.get("source_kind", ""))),
            "source_target": collapse_ws(str(source.get("source_target", ""))),
            "metadata": dict(descriptor.metadata),
        }


@dataclass(frozen=True)
class BlendOperatorProvider:
    """Supply canonical descriptors and opaque handles for one operator source."""

    provider_id: str
    list_operators: Callable[[BlendContext], Sequence[BlendOperatorRecord]]
    resolve_operator: Callable[[str, str, BlendContext], BlendOperatorRecord | None]
    resolve_workflow_step: Callable[[Any, BlendContext], BlendOperatorRecord | None] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def new_blend_capability_operator_provider(
    *,
    provider_id: str,
    list_capability_names: Callable[[BlendContext], Sequence[str]],
    resolve_capability_record: Callable[[str, BlendContext], BlendOperatorRecord | None],
    resolve_workflow_step_record: Callable[[Any, BlendContext], BlendOperatorRecord | None] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BlendOperatorProvider:
    """Adapt a named capability source to the neutral provider contract."""

    return BlendOperatorProvider(
        provider_id=provider_id,
        list_operators=lambda context: [
            record
            for capability_name in list_capability_names(context)
            if (record := resolve_capability_record(capability_name, context)) is not None
        ],
        resolve_operator=lambda operator_name, operator_kind, context: (
            resolve_capability_record(operator_name, context)
            if collapse_ws(operator_kind or "capability") in {"capability", "host_action"}
            else None
        ),
        resolve_workflow_step=resolve_workflow_step_record,
        metadata=dict(metadata or {}),
    )


def list_blend_operator_summaries(
    *,
    context: BlendContext,
    providers: Sequence[BlendOperatorProvider],
    operator_kind: str = "",
    query: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    normalized_kind = collapse_ws(operator_kind).casefold()
    normalized_query = _operator_text_key(query)
    by_operator_id: dict[str, dict[str, Any]] = {}
    for provider in providers:
        for record in provider.list_operators(context):
            summary = record.to_summary()
            summary["provider_id"] = provider.provider_id
            if normalized_kind and collapse_ws(str(summary.get("operator_kind", ""))).casefold() != normalized_kind:
                continue
            if normalized_query:
                haystack = _operator_text_key(
                    " ".join(
                        [
                            str(summary.get("operator_name", "")),
                            str(summary.get("semantic_description", "")),
                            str(summary.get("source_kind", "")),
                        ]
                    )
                )
                if normalized_query not in haystack:
                    continue
            operator_id = collapse_ws(str(summary.get("operator_id", "")))
            if operator_id and operator_id not in by_operator_id:
                by_operator_id[operator_id] = summary
    items = list(by_operator_id.values())
    items.sort(
        key=lambda item: (
            collapse_ws(str(item.get("operator_kind", ""))).casefold(),
            collapse_ws(str(item.get("operator_name", ""))).casefold(),
        )
    )
    bounded_limit = max(1, min(int(limit or 20), 200))
    return items[:bounded_limit]


def get_blend_operator_summary(
    *,
    context: BlendContext,
    providers: Sequence[BlendOperatorProvider],
    operator_name: str,
    operator_kind: str = "",
) -> dict[str, Any] | None:
    record = resolve_blend_operator_record(
        operator_name=operator_name,
        operator_kind=operator_kind,
        context=context,
        providers=providers,
    )
    if record is None:
        return None
    return record.to_summary()


def resolve_blend_operator_record(
    *,
    operator_name: str,
    operator_kind: str,
    context: BlendContext,
    providers: Sequence[BlendOperatorProvider],
) -> BlendOperatorRecord | None:
    normalized_name = collapse_ws(operator_name)
    normalized_kind = collapse_ws(operator_kind or "skill") or "skill"
    if not normalized_name:
        return None
    for provider in providers:
        resolved = provider.resolve_operator(normalized_name, normalized_kind, context)
        if resolved is not None:
            return resolved
    return None


def resolve_blend_operator_record_for_workflow_step(
    workflow_step: Any,
    *,
    context: BlendContext,
    providers: Sequence[BlendOperatorProvider],
) -> BlendOperatorRecord | None:
    for provider in providers:
        if provider.resolve_workflow_step is None:
            continue
        resolved = provider.resolve_workflow_step(workflow_step, context)
        if resolved is not None:
            return resolved
    return resolve_blend_operator_record(
        operator_name=collapse_ws(str(getattr(workflow_step, "operator_name", ""))),
        operator_kind=collapse_ws(str(getattr(workflow_step, "operator_kind", "skill") or "skill")) or "skill",
        context=context,
        providers=providers,
    )


def _operator_text_key(value: str) -> str:
    normalized = collapse_ws(str(value)).casefold()
    normalized = "".join(character if character.isalnum() else " " for character in normalized)
    return collapse_ws(normalized)


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
        mount for mount in required_visible_mounts if mount not in context.visible_mounts
    ]
    missing_writable_mounts = [
        mount for mount in required_writable_mounts if mount not in context.writable_mounts
    ]
    missing_world_mounts = [
        mount for mount in required_world_mounts if mount not in context.world_mounts
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
    invocation_id: str = "",
) -> BlendOperatorInvocation:
    return BlendOperatorInvocation(
        invocation_id=collapse_ws(invocation_id) or f"bop_inv_{uuid.uuid4().hex[:12]}",
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


__all__ = [
    "BlendOperator",
    "BlendOperatorInvocation",
    "BlendOperatorProvider",
    "BlendOperatorRecord",
    "blend_operator_applicability",
    "get_blend_operator_summary",
    "list_blend_operator_summaries",
    "new_blend_operator_invocation",
    "new_blend_capability_operator_provider",
    "resolve_blend_operator_record",
    "resolve_blend_operator_record_for_workflow_step",
    "resolve_blend_operator_target",
]
