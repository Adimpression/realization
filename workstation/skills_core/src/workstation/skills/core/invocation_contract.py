# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_skill_semantics.invocation import (
    SkillInvocationBinding,
    SkillInvocationRequest,
    SkillInvocationResult,
    required_skill_input_names,
    skill_invocation_result_from_mapping,
)
from realized_core_runtime.capabilities import runtime_skill_declaration_for_artifact
from realized_skill_semantics.execution import ability_executor_framework
from realized_core_semantics.semantic_text import collapse_ws
from realized_skill_application.projection import skill_kind_from_artifact


__all__ = [
    "SkillInvocationBinding",
    "SkillInvocationRequest",
    "SkillInvocationResult",
    "skill_invocation_request_from_artifact",
    "skill_invocation_result_from_mapping",
]


_required_input_names = required_skill_input_names


def skill_invocation_request_from_artifact(
    artifact: Any,
    *,
    semantic_unit: str,
    payload: Any,
    missing_required_inputs: list[str],
    invocation_mode: str,
) -> SkillInvocationRequest:
    """
    High Level Purpose:
        In circumstances like workstation and future runtime skill invocation, helps with projecting one canonical invocation request record from the current artifact declaration and bound payload.

    Reference to Theory:
        Supports the unified invocation contract by making direct named and conversationally bound invocation share one normalized request shape.

    Example Input Output:
        Input: `skill_invocation_request_from_artifact(artifact, semantic_unit='Find BSSCController', payload={'symbol': 'BSSCController'}, missing_required_inputs=[], invocation_mode='llm_routed')`
        Output: SkillInvocationRequest(skill_title='Symbol Search', ...)

    Args:
        artifact: Value for `artifact` used by `skill_invocation_request_from_artifact`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `semantic_unit`. Expected type: `str`.
        payload: Value for `payload` used by `payload`. Expected type: `Any`.
        missing_required_inputs: Value for `missing_required_inputs` used by `missing_required_inputs`. Expected type: `list[str]`.
        invocation_mode: Value for `invocation_mode` used by `invocation_mode`. Expected type: `str`.

    Returns:
        SkillInvocationRequest: Result produced by `skill_invocation_request_from_artifact`.
    """
    declaration = runtime_skill_declaration_for_artifact(artifact)
    inputs = dict(declaration.get("inputs", {})) if isinstance(declaration.get("inputs", {}), Mapping) else {}
    outputs = dict(declaration.get("outputs", {})) if isinstance(declaration.get("outputs", {}), Mapping) else {}
    required_inputs = required_skill_input_names(inputs)
    payload_mapping = dict(payload) if isinstance(payload, Mapping) else {}
    bindings = [
        SkillInvocationBinding(
            name=name,
            contract_description=collapse_ws(str(description)),
            status="provided" if name in payload_mapping and payload_mapping.get(name) is not None else "missing",
            value=payload_mapping.get(name),
        )
        for name, description in inputs.items()
        if collapse_ws(str(name))
    ]
    content = dict(getattr(artifact, "content", {}) or {})
    executor_framework = ability_executor_framework(
        representation=str(getattr(getattr(artifact, "representation", None), "value", getattr(artifact, "representation", ""))),
        content=content,
    )
    return SkillInvocationRequest(
        skill_title=collapse_ws(str(getattr(artifact, "title", ""))),
        skill_kind=skill_kind_from_artifact(artifact),
        executor_framework=collapse_ws(str(executor_framework)),
        invocation_mode=collapse_ws(str(invocation_mode)),
        semantic_unit=collapse_ws(str(semantic_unit)),
        payload=payload,
        declared_inputs=inputs,
        declared_outputs=outputs,
        required_inputs=required_inputs,
        missing_required_inputs=[collapse_ws(str(item)) for item in missing_required_inputs if collapse_ws(str(item))],
        bindings=bindings,
    )
