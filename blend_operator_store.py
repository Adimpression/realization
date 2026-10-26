# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from capability_runtime import runtime_skill_declaration_for_artifact
from blend_context import BlendContext
from blend_operator import BlendOperator
from realized_skill_semantics.execution import ability_executor_framework
from semantic_text import collapse_ws

DEFAULT_BLEND_OPERATOR_ACTOR_VISIBILITY = (
    "ai_chat",
    "automation_api",
    "hitl_review",
)


@dataclass(frozen=True)
class BlendOperatorRecord:
    operator: Any
    operator_source: dict[str, Any]
    operator_descriptor: BlendOperator

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
    provider_id: str
    list_operators: Callable[[BlendContext], Sequence[BlendOperatorRecord]]
    resolve_operator: Callable[[str, str, BlendContext], BlendOperatorRecord | None]
    resolve_workflow_step: Callable[[Any, BlendContext], BlendOperatorRecord | None] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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
    source = dict(operator_source or {})
    name = collapse_ws(operator_name) or collapse_ws(str(getattr(artifact, "title", "")))
    content = dict(getattr(artifact, "content", {}) or {})
    declaration = runtime_skill_declaration_for_artifact(artifact)
    executor_framework = str(
        declaration.get("executor_framework", "")
        or ability_executor_framework(
            representation=str(
                getattr(getattr(artifact, "representation", ""), "value", getattr(artifact, "representation", ""))
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
        policy_requirements=_stable_unique([str(item) for item in declaration.get("authorities_requested", [])]),
        actor_visibility=_stable_unique([str(item) for item in actor_visibility]),
        context_requirements={
            "required_capabilities": list(_stable_unique([str(item) for item in required_capabilities])),
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
    source = dict(operator_source or {})
    visible_mounts = _stable_unique([str(item) for item in required_visible_mounts])
    writable_mounts = _stable_unique([str(item) for item in required_writable_mounts])
    targets = _stable_unique([str(item) for item in allowed_targets]) or (
        (collapse_ws(default_target),) if collapse_ws(default_target) else ()
    )
    normalized_default_target = collapse_ws(default_target) or (targets[0] if targets else "")
    descriptor = BlendOperator(
        operator_id=f"{collapse_ws(operator_kind) or 'capability'}:{collapse_ws(capability_name)}:{normalized_default_target or 'host'}",
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


def new_blend_capability_operator_provider(
    *,
    provider_id: str,
    list_capability_names: Callable[[BlendContext], Sequence[str]],
    resolve_capability_record: Callable[[str, BlendContext], BlendOperatorRecord | None],
    resolve_workflow_step_record: Callable[[Any, BlendContext], BlendOperatorRecord | None] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BlendOperatorProvider:
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
