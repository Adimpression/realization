"""Portable skill invocation records and deterministic normalization."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from realized_core_semantics.values import json_safe


__all__ = [
    "SkillInvocationBinding",
    "SkillInvocationRequest",
    "SkillInvocationResult",
    "required_skill_input_names",
    "skill_invocation_result_from_mapping",
]


def _collapse_ws(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def required_skill_input_names(inputs: Mapping[str, Any]) -> list[str]:
    """Return declared input names whose descriptions mark them as required."""
    required: list[str] = []
    for raw_name, raw_description in dict(inputs).items():
        name = _collapse_ws(raw_name)
        description = _collapse_ws(raw_description)
        if not name:
            continue
        if not description or "required" in description.casefold():
            required.append(name)
    return required


@dataclass(frozen=True)
class SkillInvocationBinding:
    """One declared invocation input and its current binding state."""

    name: str
    contract_description: str
    status: str
    value: Any = None


@dataclass(frozen=True)
class SkillInvocationRequest:
    """Portable normalized request for invoking one selected skill."""

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
        """Project this immutable request into a JSON-compatible dictionary."""
        return json_safe(self)


@dataclass(frozen=True)
class SkillInvocationResult:
    """Portable normalized terminal result of one skill invocation."""

    skill_title: str
    status: str
    answer: str
    error: str
    output_payload: Any
    nested_run_outcome: str

    def to_dict(self) -> dict[str, Any]:
        """Project this immutable result into a JSON-compatible dictionary."""
        return json_safe(self)


def skill_invocation_result_from_mapping(
    result: Mapping[str, Any],
) -> SkillInvocationResult:
    """Normalize one invocation terminal mapping into the portable result."""
    output_payload = result.get("result_payload")
    if output_payload is None:
        output_payload = result.get("parsed_output")
    if output_payload is None:
        output_payload = result.get("result")
    return SkillInvocationResult(
        skill_title=_collapse_ws(result.get("skill_title", "")),
        status=_collapse_ws(result.get("status", "")),
        answer=str(result.get("answer", "") or ""),
        error=str(result.get("error", "") or ""),
        output_payload=output_payload,
        nested_run_outcome=_collapse_ws(result.get("nested_run_outcome", "")),
    )
