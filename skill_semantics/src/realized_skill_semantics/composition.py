"""Portable skill-composition plan and static-analysis values."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from realized_core_semantics.values import json_safe
from realized_skill_semantics.ir import CanonicalSkillIR


__all__ = [
    "SkillBindingDiagnostic",
    "SkillCompositionBinding",
    "SkillCompositionCandidate",
    "SkillCompositionCondition",
    "SkillCompositionMapper",
    "SkillCompositionPlanAnalysis",
    "SkillCompositionStep",
    "SkillConditionDiagnostic",
]


def _collapse_ws(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class SkillCompositionMapper:
    """Declarative mapper applied between one source and target leaf."""

    kind: str = "identity"
    field: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionMapper":
        """Construct a mapper from its portable mapping representation."""
        if not isinstance(payload, Mapping):
            raise TypeError(
                "SkillCompositionMapper.from_dict requires a mapping payload."
            )
        return cls(
            kind=_collapse_ws(payload.get("kind", "identity")) or "identity",
            field=_collapse_ws(payload.get("field", payload.get("source_key", ""))),
        )


@dataclass(frozen=True)
class SkillCompositionBinding:
    """Declarative binding for one target leaf in a composition step."""

    target_region: str
    target_path: str
    source_step_id: str = ""
    source_region: str = ""
    source_path: str = ""
    source_root_name: str = ""
    source_root_region: str = ""
    constant_value: Any = None
    mapper: SkillCompositionMapper | None = None
    mapper_kind: str = "identity"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionBinding":
        """Construct a binding from its portable mapping representation."""
        if not isinstance(payload, Mapping):
            raise TypeError(
                "SkillCompositionBinding.from_dict requires a mapping payload."
            )
        mapper_payload = payload.get("mapper")
        mapper = (
            SkillCompositionMapper.from_dict(mapper_payload)
            if isinstance(mapper_payload, Mapping)
            else None
        )
        return cls(
            target_region=_collapse_ws(payload.get("target_region", "")),
            target_path=_collapse_ws(payload.get("target_path", "")),
            source_step_id=_collapse_ws(payload.get("source_step_id", "")),
            source_region=_collapse_ws(payload.get("source_region", "")),
            source_path=_collapse_ws(payload.get("source_path", "")),
            source_root_name=_collapse_ws(payload.get("source_root_name", "")),
            source_root_region=_collapse_ws(payload.get("source_root_region", "")),
            constant_value=payload.get("constant_value"),
            mapper=mapper,
            mapper_kind=_collapse_ws(payload.get("mapper_kind", "identity"))
            or "identity",
        )


@dataclass(frozen=True)
class SkillCompositionCondition:
    """Declarative condition over one prior or current step output leaf."""

    source_step_id: str
    source_region: str
    source_path: str
    operator: str = "equals"
    expected_value: Any = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionCondition":
        """Construct a condition from its portable mapping representation."""
        if not isinstance(payload, Mapping):
            raise TypeError(
                "SkillCompositionCondition.from_dict requires a mapping payload."
            )
        return cls(
            source_step_id=_collapse_ws(payload.get("source_step_id", "")),
            source_region=_collapse_ws(payload.get("source_region", "")),
            source_path=_collapse_ws(payload.get("source_path", "")),
            operator=_collapse_ws(payload.get("operator", "equals")) or "equals",
            expected_value=payload.get("expected_value"),
        )


@dataclass(frozen=True)
class SkillCompositionStep:
    """One declarative step in a portable skill-composition plan."""

    step_id: str
    skill: CanonicalSkillIR | Mapping[str, Any]
    bindings: tuple[SkillCompositionBinding, ...] = ()
    run_if: tuple[SkillCompositionCondition, ...] = ()
    iterate_until: tuple[SkillCompositionCondition, ...] = ()
    branch_label: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionStep":
        """Construct a step from its portable mapping representation."""
        if not isinstance(payload, Mapping):
            raise TypeError(
                "SkillCompositionStep.from_dict requires a mapping payload."
            )
        bindings = tuple(
            item
            if isinstance(item, SkillCompositionBinding)
            else SkillCompositionBinding.from_dict(item)
            for item in payload.get("bindings", ())
        )
        run_if = tuple(
            item
            if isinstance(item, SkillCompositionCondition)
            else SkillCompositionCondition.from_dict(item)
            for item in payload.get("run_if", ())
        )
        iterate_until = tuple(
            item
            if isinstance(item, SkillCompositionCondition)
            else SkillCompositionCondition.from_dict(item)
            for item in payload.get("iterate_until", ())
        )
        return cls(
            step_id=_collapse_ws(payload.get("step_id", "")),
            skill=payload.get("skill", {}),
            bindings=bindings,
            run_if=run_if,
            iterate_until=iterate_until,
            branch_label=_collapse_ws(payload.get("branch_label", "")),
        )


@dataclass(frozen=True)
class SkillBindingDiagnostic:
    """Static-analysis result for one composition binding."""

    step_id: str
    target_region: str
    target_path: str
    status: str
    source_kind: str
    source_step_id: str = ""
    source_region: str = ""
    source_path: str = ""
    source_root_name: str = ""
    source_root_region: str = ""
    mapper_kind: str = "identity"
    reason: str = ""


@dataclass(frozen=True)
class SkillConditionDiagnostic:
    """Static-analysis result for one composition condition."""

    step_id: str
    status: str
    source_step_id: str
    source_region: str
    source_path: str
    operator: str
    reason: str = ""


@dataclass(frozen=True)
class SkillCompositionCandidate:
    """One possible source-to-target leaf binding."""

    source_region: str
    source_path: str
    target_region: str
    target_path: str
    status: str
    reason: str
    mapper_kind: str = "identity"


@dataclass(frozen=True)
class SkillCompositionPlanAnalysis:
    """Portable static-analysis result for a composition plan."""

    steps: list[dict[str, Any]]
    plan_authorities: list[str]
    blocked: bool
    unresolved_targets: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Project this immutable analysis into a JSON-compatible dictionary."""
        return json_safe(
            {
                "steps": self.steps,
                "plan_authorities": self.plan_authorities,
                "blocked": self.blocked,
                "unresolved_targets": self.unresolved_targets,
            }
        )
