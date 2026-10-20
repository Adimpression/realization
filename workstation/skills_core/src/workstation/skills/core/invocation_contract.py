# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from applied_theory_types import json_safe
from capability_runtime import runtime_skill_declaration_for_artifact
from execution_frameworks import ability_executor_framework
from semantic_text import collapse_ws
from skill_export_projection import skill_kind_from_artifact


__all__ = [
    "SkillInvocationBinding",
    "SkillInvocationRequest",
    "SkillInvocationResult",
    "skill_invocation_request_from_artifact",
    "skill_invocation_result_from_mapping",
]


def _required_input_names(inputs: Mapping[str, Any]) -> list[str]:
    required: list[str] = []
    for raw_name, raw_description in dict(inputs).items():
        name = collapse_ws(str(raw_name))
        description = collapse_ws(str(raw_description))
        if not name:
            continue
        if not description or "required" in description.casefold():
            required.append(name)
    return required


@dataclass(frozen=True)
class SkillInvocationBinding:
    name: str
    contract_description: str
    status: str
    value: Any = None


@dataclass(frozen=True)
class SkillInvocationRequest:
    skill_title: str
    skill_kind: str
    executor_framework: str
    invocation_mode: str
    semantic_unit: str
    payload: Any
    declared_inputs: dict[str, Any]
    declared_outputs: dict[str, Any]
    required_inputs: list[str]
    missing_required_inputs: list[str]
    bindings: list[SkillInvocationBinding]

    def to_dict(self) -> dict[str, Any]:
        return json_safe(self)


@dataclass(frozen=True)
class SkillInvocationResult:
    skill_title: str
    status: str
    answer: str
    error: str
    output_payload: Any
    nested_run_outcome: str

    def to_dict(self) -> dict[str, Any]:
        return json_safe(self)


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
    required_inputs = _required_input_names(inputs)
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


def skill_invocation_result_from_mapping(result: Mapping[str, Any]) -> SkillInvocationResult:
    """
    High Level Purpose:
        In circumstances like workstation result projection and future runtime unification, helps with normalizing one invocation terminal payload into a canonical result record.

    Reference to Theory:
        Supports the unified invocation contract by keeping success, approval, unsupported, and error outcomes on one stable result surface.

    Example Input Output:
        Input: `skill_invocation_result_from_mapping({'status': 'ok', 'skill_title': 'Repo Search', 'answer': 'src/app.py'})`
        Output: SkillInvocationResult(skill_title='Repo Search', status='ok', answer='src/app.py', ...)

    Args:
        result: Value for `result` used by `skill_invocation_result_from_mapping`. Expected type: `Mapping[str, Any]`.

    Returns:
        SkillInvocationResult: Result produced by `skill_invocation_result_from_mapping`.
    """
    output_payload = result.get("result_payload")
    if output_payload is None:
        output_payload = result.get("parsed_output")
    if output_payload is None:
        output_payload = result.get("result")
    return SkillInvocationResult(
        skill_title=collapse_ws(str(result.get("skill_title", ""))),
        status=collapse_ws(str(result.get("status", ""))),
        answer=str(result.get("answer", "") or ""),
        error=str(result.get("error", "") or ""),
        output_payload=output_payload,
        nested_run_outcome=collapse_ws(str(result.get("nested_run_outcome", ""))),
    )
