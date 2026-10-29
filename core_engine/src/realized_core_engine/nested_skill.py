"""Controller-owned realization of nested governed skill invocation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from realized_core_runtime.host_abi import validate_host_broker_invocation
from realized_core_semantics.semantic_text import collapse_ws
from realized_host_interaction.context import (
    HostInteractionContext,
    host_native_interaction_context,
)
from realized_host_interaction.realizers import (
    HostBrokerBinding,
    HostBrokerCallback,
    HostBrokerInvocation,
    HostRealizerDescriptor,
    HostRealizerProvider,
    StaticHostRealizerProvider,
)
from realized_skill_semantics.declaration import composition_binding_targets

from realized_core_engine.state import SystemState


class ArtifactRepository(Protocol):
    """Minimal persistence port required to resolve an installed skill."""

    def load_all_artifacts(self) -> list[Any]: ...


type NestedControllerFactory = Callable[
    [SystemState, HostInteractionContext],
    Any,
]


def with_nested_skill_realizer(
    provider: HostRealizerProvider,
    callback: HostBrokerCallback,
) -> StaticHostRealizerProvider:
    """Replace only the abstract ``skill.invoke`` binding at composition."""

    existing_binding = next(
        (
            binding
            for binding in provider.broker_bindings()
            if binding.descriptor.identity == "skill.invoke"
        ),
        None,
    )
    descriptor = (
        existing_binding.descriptor
        if existing_binding is not None
        else HostRealizerDescriptor(kind="broker", identity="skill.invoke")
    )
    brokers = tuple(
        binding
        for binding in provider.broker_bindings()
        if binding.descriptor.identity != "skill.invoke"
    ) + (
        HostBrokerBinding(
            descriptor=descriptor,
            callback=callback,
            inspector=(
                existing_binding.inspector
                if existing_binding is not None
                else None
            ),
        ),
    )
    return StaticHostRealizerProvider(
        executors=provider.executor_bindings(),
        brokers=brokers,
    )


def invoke_nested_skill(
    invocation: HostBrokerInvocation,
    provider: HostRealizerProvider,
    *,
    artifact_repository: ArtifactRepository,
    controller_factory: NestedControllerFactory,
) -> dict[str, Any]:
    """Resolve and execute a nested skill through controller-owned semantics."""

    arguments, abi_error = validate_host_broker_invocation(
        invocation.identity,
        invocation.arguments,
    )
    if arguments is None:
        return {
            "status": "error",
            "broker": invocation.identity,
            "error": abi_error,
        }

    title_text = collapse_ws(str(arguments.get("skill_title", "")))
    if not title_text:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "error": "A non-empty skill_title is required.",
        }
    installed = [
        artifact
        for artifact in artifact_repository.load_all_artifacts()
        if collapse_ws(str(getattr(artifact, "title", ""))) == title_text
    ]
    if not installed:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "error": f"No installed skill artifact matches title {title_text!r}.",
        }

    governance_context = invocation.governance_context
    declaration = (
        dict(governance_context.get("declaration", {}))
        if isinstance(governance_context, Mapping)
        and isinstance(governance_context.get("declaration", {}), Mapping)
        else {}
    )
    allowed_bindings = composition_binding_targets(declaration)
    if (
        allowed_bindings
        and "*" not in allowed_bindings
        and title_text not in allowed_bindings
    ):
        return {
            "status": "error",
            "broker": "skill.invoke",
            "error": (
                f"Governed composition rights do not bind this skill to {title_text!r}. "
                f"Allowed targets: {', '.join(allowed_bindings)}."
            ),
        }

    artifact = installed[0]
    nested_semantic_unit = (
        collapse_ws(str(arguments.get("semantic_unit", ""))) or title_text
    )
    host_context = host_native_interaction_context(
        metadata={"owner": "nested_skill"},
        realizer_provider=provider,
    )
    nested_state = SystemState.bootstrap(nested_semantic_unit)
    nested_controller = controller_factory(nested_state, host_context)
    nested_state.learned_artifacts[str(artifact.id)] = artifact

    content = dict(getattr(artifact, "content", {}) or {})
    input_contract = dict(content.get("input_contract", {}) or {})
    nested_payload = arguments.get("invocation_payload")
    if nested_payload is None and not input_contract:
        nested_payload = {}
    elif nested_payload is None and sorted(input_contract) == ["payload"]:
        nested_payload = {"payload": {}}
    max_steps = int(arguments.get("max_steps", 64))
    artifact_type_value = str(
        getattr(
            getattr(artifact, "artifact_type", ""),
            "value",
            getattr(artifact, "artifact_type", ""),
        )
    ).strip().lower()
    if artifact_type_value == "ability":
        result = nested_controller.execute_function_artifact(
            artifact,
            semantic_unit=nested_semantic_unit,
            explicit_payload=nested_payload,
        )
        return {
            "status": "ok" if result.ok else "error",
            "broker": "skill.invoke",
            "skill_title": title_text,
            "answer": result.answer,
            "stderr": result.stderr,
            "notes": list(result.notes),
            "nested_effect_traces": list(nested_state.effect_traces),
            "nested_capability_grants": list(nested_state.capability_grants),
            "nested_run_outcome": nested_state.run_outcome.value,
            "max_steps": max_steps,
        }

    answer = nested_controller.artifact_answer_text(
        artifact,
        semantic_unit=nested_semantic_unit,
        explicit_payload=nested_payload,
    )
    if not answer:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "skill_title": title_text,
            "error": (
                "Target skill did not expose an invokable ability or "
                "answer-bearing knowledge surface."
            ),
        }
    return {
        "status": "ok",
        "broker": "skill.invoke",
        "skill_title": title_text,
        "answer": answer,
        "nested_effect_traces": list(nested_state.effect_traces),
        "nested_capability_grants": list(nested_state.capability_grants),
        "nested_run_outcome": nested_state.run_outcome.value,
        "max_steps": max_steps,
    }


__all__ = [
    "ArtifactRepository",
    "NestedControllerFactory",
    "invoke_nested_skill",
    "with_nested_skill_realizer",
]
