# See MODULES.md for the repository module map before editing.
"""Compatibility and runtime adapters for the canonical Blend operator catalog."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from realized_core_runtime.capabilities import runtime_skill_declaration_for_artifact
from realized_blend.context import BlendContext
from realized_blend.operators import (
    BlendOperator,
    BlendOperatorProvider,
    BlendOperatorRecord,
    get_blend_operator_summary,
    list_blend_operator_summaries,
    new_blend_capability_operator_provider,
    resolve_blend_operator_record,
    resolve_blend_operator_record_for_workflow_step,
)
from realized_core_semantics.semantic_text import collapse_ws
from realized_skill_semantics.execution import ability_executor_framework


DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY = (
    "ai_chat",
    "automation_api",
    "hitl_review",
)


def blend_skill_operator_record_from_artifact(
    *,
    artifact: Any,
    operator_name: str = "",
    operator_source: Mapping[str, Any] | None = None,
    visible_targets: Sequence[str] = (),
    required_capabilities: Sequence[str] = ("ws.skill.invoke",),
    execution_adapter: str = "blend.skill_invoke",
    actor_visibility: Sequence[str] = DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY,
    metadata: Mapping[str, Any] | None = None,
) -> BlendOperatorRecord:
    """Project one admitted runtime artifact into a neutral catalog record."""

    source = dict(operator_source or {})
    name = collapse_ws(operator_name) or collapse_ws(str(getattr(artifact, "title", "")))
    content = dict(getattr(artifact, "content", {}) or {})
    declaration = runtime_skill_declaration_for_artifact(artifact)
    executor_framework = str(
        declaration.get("executor_framework", "")
        or ability_executor_framework(
            representation=str(
                getattr(
                    getattr(artifact, "representation", ""),
                    "value",
                    getattr(artifact, "representation", ""),
                )
            ),
            content=content,
        )
        or ""
    )
    targets = _stable_unique([str(item) for item in visible_targets])
    default_target = targets[0] if targets else ""
    descriptor = BlendOperator(
        operator_id=collapse_ws(str(getattr(artifact, "id", ""))) or f"skill:{name}",
        operator_kind="skill",
        display_name=name,
        execution_adapter=collapse_ws(execution_adapter),
        semantic_description=collapse_ws(str(declaration.get("intent", ""))) or name,
        input_shape=dict(content.get("input_contract", {}) or {}),
        output_shape=dict(content.get("output_contract", {}) or {}),
        policy_requirements=_stable_unique(
            [str(item) for item in declaration.get("authorities_requested", [])]
        ),
        actor_visibility=_stable_unique([str(item) for item in actor_visibility]),
        context_requirements={
            "required_capabilities": list(
                _stable_unique([str(item) for item in required_capabilities])
            ),
            "required_visible_mounts": list(targets),
        },
        target_resolution={
            "default_target": default_target,
            "allowed_targets": list(targets),
            "require_visible": bool(targets),
        },
        metadata={
            "artifact_id": collapse_ws(str(getattr(artifact, "id", ""))),
            "executor_framework": executor_framework,
            "source_kind": collapse_ws(str(source.get("source_kind", ""))),
            "source_target": collapse_ws(str(source.get("source_target", ""))),
            **dict(metadata or {}),
        },
    )
    return BlendOperatorRecord(
        operator=artifact,
        operator_source=source,
        operator_descriptor=descriptor,
    )


def blend_capability_operator_record(
    *,
    capability_name: str,
    operator: Any,
    operator_source: Mapping[str, Any] | None = None,
    input_shape: Mapping[str, Any] | None = None,
    output_shape: Mapping[str, Any] | None = None,
    semantic_description: str = "",
    policy_requirements: Sequence[str] = (),
    required_capabilities: Sequence[str] = (),
    required_visible_mounts: Sequence[str] = (),
    required_writable_mounts: Sequence[str] = (),
    default_target: str = "",
    allowed_targets: Sequence[str] = (),
    execution_adapter: str = "blend.capability",
    actor_visibility: Sequence[str] = DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY,
    metadata: Mapping[str, Any] | None = None,
    operator_kind: str = "capability",
) -> BlendOperatorRecord:
    """Project one concrete host capability into a neutral catalog record."""

    source = dict(operator_source or {})
    visible_mounts = _stable_unique([str(item) for item in required_visible_mounts])
    writable_mounts = _stable_unique([str(item) for item in required_writable_mounts])
    targets = _stable_unique([str(item) for item in allowed_targets]) or (
        (collapse_ws(default_target),) if collapse_ws(default_target) else ()
    )
    normalized_default_target = collapse_ws(default_target) or (targets[0] if targets else "")
    descriptor = BlendOperator(
        operator_id=(
            f"{collapse_ws(operator_kind) or 'capability'}:"
            f"{collapse_ws(capability_name)}:{normalized_default_target or 'host'}"
        ),
        operator_kind=collapse_ws(operator_kind) or "capability",
        display_name=collapse_ws(capability_name),
        execution_adapter=collapse_ws(execution_adapter),
        semantic_description=collapse_ws(semantic_description) or collapse_ws(capability_name),
        input_shape=dict(input_shape or {}),
        output_shape=dict(output_shape or {}),
        policy_requirements=_stable_unique([str(item) for item in policy_requirements]),
        actor_visibility=_stable_unique([str(item) for item in actor_visibility]),
        context_requirements={
            "required_capabilities": list(
                _stable_unique(
                    [str(item) for item in (required_capabilities or (capability_name,))]
                )
            ),
            "required_visible_mounts": list(visible_mounts),
            "required_writable_mounts": list(writable_mounts),
        },
        target_resolution={
            "default_target": normalized_default_target,
            "allowed_targets": list(targets),
            "require_visible": bool(visible_mounts),
            "require_writable": bool(writable_mounts),
        },
        metadata={
            "source_kind": collapse_ws(str(source.get("source_kind", ""))),
            "source_target": collapse_ws(str(source.get("source_target", ""))),
            **dict(metadata or {}),
        },
    )
    return BlendOperatorRecord(
        operator=operator,
        operator_source=source,
        operator_descriptor=descriptor,
    )


def new_blend_skill_operator_provider(
    *,
    provider_id: str,
    list_skill_names: Callable[[BlendContext], Sequence[str]],
    resolve_skill: Callable[[str, BlendContext], tuple[Any, Mapping[str, Any]] | None],
    visible_targets: Sequence[str] | Callable[[BlendContext], Sequence[str]],
    required_capabilities: Sequence[str] = ("ws.skill.invoke",),
    execution_adapter: str = "blend.skill_invoke",
    actor_visibility: Sequence[str] = DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY,
    metadata: Mapping[str, Any] | None = None,
) -> BlendOperatorProvider:
    """Adapt the runtime's admitted artifact catalog to a Blend provider."""

    return BlendOperatorProvider(
        provider_id=provider_id,
        list_operators=lambda context: [
            record
            for name in list_skill_names(context)
            if (
                record := _resolve_skill_record(
                    operator_name=name,
                    context=context,
                    resolve_skill=resolve_skill,
                    visible_targets=visible_targets,
                    required_capabilities=required_capabilities,
                    execution_adapter=execution_adapter,
                    actor_visibility=actor_visibility,
                )
            )
            is not None
        ],
        resolve_operator=lambda operator_name, operator_kind, context: (
            _resolve_skill_record(
                operator_name=operator_name,
                context=context,
                resolve_skill=resolve_skill,
                visible_targets=visible_targets,
                required_capabilities=required_capabilities,
                execution_adapter=execution_adapter,
                actor_visibility=actor_visibility,
            )
            if collapse_ws(operator_kind or "skill") == "skill"
            else None
        ),
        resolve_workflow_step=lambda workflow_step, context: _resolve_skill_record(
            operator_name=collapse_ws(str(getattr(workflow_step, "operator_name", ""))),
            context=context,
            resolve_skill=resolve_skill,
            visible_targets=visible_targets,
            required_capabilities=required_capabilities,
            execution_adapter=execution_adapter,
            actor_visibility=actor_visibility,
        ),
        metadata=dict(metadata or {}),
    )


def _stable_unique(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = collapse_ws(str(value))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _contextual_targets(
    value: Sequence[str] | Callable[[BlendContext], Sequence[str]],
    context: BlendContext,
) -> tuple[str, ...]:
    resolved = value(context) if callable(value) else value
    return _stable_unique([str(item) for item in resolved])


def _resolve_skill_record(
    *,
    operator_name: str,
    context: BlendContext,
    resolve_skill: Callable[[str, BlendContext], tuple[Any, Mapping[str, Any]] | None],
    visible_targets: Sequence[str] | Callable[[BlendContext], Sequence[str]],
    required_capabilities: Sequence[str],
    execution_adapter: str,
    actor_visibility: Sequence[str],
) -> BlendOperatorRecord | None:
    normalized_name = collapse_ws(operator_name)
    if not normalized_name:
        return None
    resolved = resolve_skill(normalized_name, context)
    if resolved is None:
        return None
    artifact, operator_source = resolved
    return blend_skill_operator_record_from_artifact(
        artifact=artifact,
        operator_name=normalized_name,
        operator_source=operator_source,
        visible_targets=_contextual_targets(visible_targets, context),
        required_capabilities=required_capabilities,
        execution_adapter=execution_adapter,
        actor_visibility=actor_visibility,
    )


__all__ = [
    "DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY",
    "BlendOperatorProvider",
    "BlendOperatorRecord",
    "blend_capability_operator_record",
    "blend_skill_operator_record_from_artifact",
    "get_blend_operator_summary",
    "list_blend_operator_summaries",
    "new_blend_capability_operator_provider",
    "new_blend_skill_operator_provider",
    "resolve_blend_operator_record",
    "resolve_blend_operator_record_for_workflow_step",
]
