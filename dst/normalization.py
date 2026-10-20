from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

from coordinated_transformation.core import (
    Actor,
    Boundary,
    Capability,
    Constraint,
    Decision,
    Dependency,
    Model,
    Objective,
    State,
    TimePoint,
    Transition,
)
from dst.core import DST_TYPED_FIXTURE_ROOT, DstUseCaseFixture, REPO_ROOT
from dst.discovery import DstDiscoveryResult
from semantic_text import collapse_ws


DST_NORMALIZED_SCHEMA_VERSION = "dst_normalized_case.v1"
DST_NORMALIZED_FIXTURE_ROOT = DST_TYPED_FIXTURE_ROOT / "normalized"
DST_PROMPT_PATH = REPO_ROOT / "DST_PROMPT.md"


def _ordered_unique_texts(items: list[object] | tuple[object, ...] | set[object] | None) -> tuple[str, ...]:
    if not items:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _normalized_bool_or_none(value: Any) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    return None


def _text(value: Any) -> str:
    return str(value or "")


def _prefixed_id(raw_code: str, prefix: str, index: int) -> str:
    normalized = collapse_ws(raw_code)
    if normalized:
        lowered = normalized.lower()
        digits = "".join(ch for ch in lowered if ch.isdigit())
        if lowered.startswith(prefix) and digits:
            return f"{prefix}{digits}"
        if lowered == prefix:
            return prefix
        if digits:
            return f"{prefix}{digits}"
    return f"{prefix}{index}"


def _entry_name(entry: Any) -> str:
    text = collapse_ws(str(getattr(entry, "text", "")))
    if text:
        return text
    code = collapse_ws(str(getattr(entry, "code", "")))
    return code


def _route_tokens(route_expression: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in str(route_expression or "").split("->") if token.strip())


def load_dst_prompt_template(path: Path | None = None) -> str:
    prompt_path = Path(path or DST_PROMPT_PATH)
    return prompt_path.read_text(encoding="utf-8").strip()


def build_dst_normalization_prompt(
    prompt_input: str,
    *,
    prompt_template: str | None = None,
) -> str:
    template = (prompt_template or load_dst_prompt_template()).strip()
    return (
        f"{template}\n\n"
        "--------------------------------------------------\n"
        "INPUT TO NORMALIZE\n"
        "--------------------------------------------------\n\n"
        f"{str(prompt_input or '').strip()}\n"
    )


def dst_normalized_schema_hint() -> dict[str, Any]:
    return {
        "schema_version": DST_NORMALIZED_SCHEMA_VERSION,
        "fixture_id": "",
        "source_ref": "",
        "context": {
            "system_name": "",
            "decision_problem": "",
            "evaluation_state_id": "",
            "planning_horizon": "",
            "notes": [],
        },
        "actors": [{"id": "", "name": "", "roles": [], "can_decide": None}],
        "objectives": [{"id": "", "name": "", "shared": None, "mandatory": None, "pursued_by": []}],
        "capabilities": [
            {
                "id": "",
                "name": "",
                "kind": "unknown",
                "advances_objectives": [],
                "controlled_by": [],
                "benefits_to": [],
                "costs_to": [],
                "risks_to": [],
            }
        ],
        "dependencies": [{"id": "", "name": ""}],
        "constraints": [{"id": "", "name": "", "kind": "unknown"}],
        "boundaries": [{"id": "", "name": ""}],
        "states": [
            {
                "id": "",
                "name": "",
                "is_current": None,
                "is_target": None,
                "available_capabilities": [],
                "operational_capabilities": [],
                "satisfied_dependencies": [],
                "active_constraints": [],
                "boundary_friction": [{"boundary_id": "", "present": None}],
            }
        ],
        "capability_requirements": [
            {
                "capability_id": "",
                "required_dependencies": [],
                "limiting_constraints": [],
                "crossed_boundaries": [],
            }
        ],
        "capability_admissibility": [
            {
                "capability_id": "",
                "state_id": "",
                "admissible": None,
                "reasons": [],
            }
        ],
        "transitions": [
            {
                "id": "",
                "name": "",
                "source_state_id": "",
                "target_state_id": "",
                "changes_capabilities": [],
                "required_dependencies": [],
                "constraining_constraints": [],
                "crossed_boundaries": [],
            }
        ],
        "transition_admissibility": [
            {
                "transition_id": "",
                "state_id": "",
                "admissible": None,
                "reasons": [],
            }
        ],
        "decisions": [
            {
                "id": "",
                "name": "",
                "selects_transition_id": "",
                "assignments": [{"actor_id": "", "capability_id": ""}],
                "time_label": "",
            }
        ],
        "decision_status": [
            {
                "decision_id": "",
                "state_id": "",
                "valid": None,
                "executable": None,
                "reasons": [],
            }
        ],
        "coordination_requirements": [
            {
                "type": "",
                "target_id": "",
                "required": None,
                "actors": [],
                "basis": "unknown",
            }
        ],
        "risk_indicators": [{"target_type": "", "target_id": "", "state_id": "", "risks": []}],
        "fallbacks": [{"from_transition_id": "", "fallback_transition_id": "", "explicit": None}],
        "candidate_sets": {
            "candidate_transition_ids_from_current_state": [],
            "candidate_decision_ids_from_current_state": [],
        },
        "assumptions": [],
        "ambiguities": [],
        "missing_information": [],
    }


@dataclass(frozen=True)
class DstNormalizedContext:
    system_name: str = ""
    decision_problem: str = ""
    evaluation_state_id: str = ""
    planning_horizon: str = ""
    notes: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedContext":
        return cls(
            system_name=_text(payload.get("system_name", "")),
            decision_problem=_text(payload.get("decision_problem", "")),
            evaluation_state_id=collapse_ws(str(payload.get("evaluation_state_id", ""))),
            planning_horizon=_text(payload.get("planning_horizon", "")),
            notes=_ordered_unique_texts(payload.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_name": self.system_name,
            "decision_problem": self.decision_problem,
            "evaluation_state_id": self.evaluation_state_id,
            "planning_horizon": self.planning_horizon,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class DstNormalizedActor:
    id: str
    name: str
    roles: tuple[str, ...] = ()
    can_decide: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedActor":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            roles=_ordered_unique_texts(payload.get("roles", [])),
            can_decide=_normalized_bool_or_none(payload.get("can_decide")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "roles": list(self.roles),
            "can_decide": self.can_decide,
        }


@dataclass(frozen=True)
class DstNormalizedObjective:
    id: str
    name: str
    shared: bool | None = None
    mandatory: bool | None = None
    pursued_by: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedObjective":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            shared=_normalized_bool_or_none(payload.get("shared")),
            mandatory=_normalized_bool_or_none(payload.get("mandatory")),
            pursued_by=_ordered_unique_texts(payload.get("pursued_by", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "shared": self.shared,
            "mandatory": self.mandatory,
            "pursued_by": list(self.pursued_by),
        }


@dataclass(frozen=True)
class DstNormalizedCapability:
    id: str
    name: str
    kind: str = "unknown"
    advances_objectives: tuple[str, ...] = ()
    controlled_by: tuple[str, ...] = ()
    benefits_to: tuple[str, ...] = ()
    costs_to: tuple[str, ...] = ()
    risks_to: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedCapability":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            kind=collapse_ws(str(payload.get("kind", ""))) or "unknown",
            advances_objectives=_ordered_unique_texts(payload.get("advances_objectives", [])),
            controlled_by=_ordered_unique_texts(payload.get("controlled_by", [])),
            benefits_to=_ordered_unique_texts(payload.get("benefits_to", [])),
            costs_to=_ordered_unique_texts(payload.get("costs_to", [])),
            risks_to=_ordered_unique_texts(payload.get("risks_to", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "advances_objectives": list(self.advances_objectives),
            "controlled_by": list(self.controlled_by),
            "benefits_to": list(self.benefits_to),
            "costs_to": list(self.costs_to),
            "risks_to": list(self.risks_to),
        }


@dataclass(frozen=True)
class DstNamedIdRecord:
    id: str
    name: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNamedIdRecord":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}


@dataclass(frozen=True)
class DstNormalizedConstraint:
    id: str
    name: str
    kind: str = "unknown"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedConstraint":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            kind=collapse_ws(str(payload.get("kind", ""))) or "unknown",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class DstBoundaryFriction:
    boundary_id: str
    present: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstBoundaryFriction":
        return cls(
            boundary_id=collapse_ws(str(payload.get("boundary_id", ""))),
            present=_normalized_bool_or_none(payload.get("present")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "present": self.present,
        }


@dataclass(frozen=True)
class DstNormalizedState:
    id: str
    name: str
    is_current: bool | None = None
    is_target: bool | None = None
    available_capabilities: tuple[str, ...] = ()
    operational_capabilities: tuple[str, ...] = ()
    satisfied_dependencies: tuple[str, ...] = ()
    active_constraints: tuple[str, ...] = ()
    boundary_friction: tuple[DstBoundaryFriction, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedState":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            is_current=_normalized_bool_or_none(payload.get("is_current")),
            is_target=_normalized_bool_or_none(payload.get("is_target")),
            available_capabilities=_ordered_unique_texts(payload.get("available_capabilities", [])),
            operational_capabilities=_ordered_unique_texts(payload.get("operational_capabilities", [])),
            satisfied_dependencies=_ordered_unique_texts(payload.get("satisfied_dependencies", [])),
            active_constraints=_ordered_unique_texts(payload.get("active_constraints", [])),
            boundary_friction=tuple(
                DstBoundaryFriction.from_dict(item)
                for item in list(payload.get("boundary_friction", []))
                if isinstance(item, dict)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "is_current": self.is_current,
            "is_target": self.is_target,
            "available_capabilities": list(self.available_capabilities),
            "operational_capabilities": list(self.operational_capabilities),
            "satisfied_dependencies": list(self.satisfied_dependencies),
            "active_constraints": list(self.active_constraints),
            "boundary_friction": [item.to_dict() for item in self.boundary_friction],
        }


@dataclass(frozen=True)
class DstCapabilityRequirement:
    capability_id: str
    required_dependencies: tuple[str, ...] = ()
    limiting_constraints: tuple[str, ...] = ()
    crossed_boundaries: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstCapabilityRequirement":
        return cls(
            capability_id=collapse_ws(str(payload.get("capability_id", ""))),
            required_dependencies=_ordered_unique_texts(payload.get("required_dependencies", [])),
            limiting_constraints=_ordered_unique_texts(payload.get("limiting_constraints", [])),
            crossed_boundaries=_ordered_unique_texts(payload.get("crossed_boundaries", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "required_dependencies": list(self.required_dependencies),
            "limiting_constraints": list(self.limiting_constraints),
            "crossed_boundaries": list(self.crossed_boundaries),
        }


@dataclass(frozen=True)
class DstAdmissibilityRecord:
    subject_id: str
    state_id: str
    admissible: bool | None = None
    reasons: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, subject_key: str) -> "DstAdmissibilityRecord":
        return cls(
            subject_id=collapse_ws(str(payload.get(subject_key, ""))),
            state_id=collapse_ws(str(payload.get("state_id", ""))),
            admissible=_normalized_bool_or_none(payload.get("admissible")),
            reasons=_ordered_unique_texts(payload.get("reasons", [])),
        )

    def to_dict(self, *, subject_key: str) -> dict[str, Any]:
        return {
            subject_key: self.subject_id,
            "state_id": self.state_id,
            "admissible": self.admissible,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DstNormalizedTransition:
    id: str
    name: str
    source_state_id: str
    target_state_id: str
    changes_capabilities: tuple[str, ...] = ()
    required_dependencies: tuple[str, ...] = ()
    constraining_constraints: tuple[str, ...] = ()
    crossed_boundaries: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedTransition":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            source_state_id=collapse_ws(str(payload.get("source_state_id", ""))),
            target_state_id=collapse_ws(str(payload.get("target_state_id", ""))),
            changes_capabilities=_ordered_unique_texts(payload.get("changes_capabilities", [])),
            required_dependencies=_ordered_unique_texts(payload.get("required_dependencies", [])),
            constraining_constraints=_ordered_unique_texts(payload.get("constraining_constraints", [])),
            crossed_boundaries=_ordered_unique_texts(payload.get("crossed_boundaries", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_state_id": self.source_state_id,
            "target_state_id": self.target_state_id,
            "changes_capabilities": list(self.changes_capabilities),
            "required_dependencies": list(self.required_dependencies),
            "constraining_constraints": list(self.constraining_constraints),
            "crossed_boundaries": list(self.crossed_boundaries),
        }


@dataclass(frozen=True)
class DstDecisionAssignment:
    actor_id: str
    capability_id: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstDecisionAssignment":
        return cls(
            actor_id=collapse_ws(str(payload.get("actor_id", ""))),
            capability_id=collapse_ws(str(payload.get("capability_id", ""))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "capability_id": self.capability_id,
        }


@dataclass(frozen=True)
class DstNormalizedDecision:
    id: str
    name: str
    selects_transition_id: str
    assignments: tuple[DstDecisionAssignment, ...] = ()
    time_label: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedDecision":
        return cls(
            id=collapse_ws(str(payload.get("id", ""))),
            name=_text(payload.get("name", "")),
            selects_transition_id=collapse_ws(str(payload.get("selects_transition_id", ""))),
            assignments=tuple(
                DstDecisionAssignment.from_dict(item)
                for item in list(payload.get("assignments", []))
                if isinstance(item, dict)
            ),
            time_label=_text(payload.get("time_label", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "selects_transition_id": self.selects_transition_id,
            "assignments": [item.to_dict() for item in self.assignments],
            "time_label": self.time_label,
        }


@dataclass(frozen=True)
class DstDecisionStatus:
    decision_id: str
    state_id: str
    valid: bool | None = None
    executable: bool | None = None
    reasons: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstDecisionStatus":
        return cls(
            decision_id=collapse_ws(str(payload.get("decision_id", ""))),
            state_id=collapse_ws(str(payload.get("state_id", ""))),
            valid=_normalized_bool_or_none(payload.get("valid")),
            executable=_normalized_bool_or_none(payload.get("executable")),
            reasons=_ordered_unique_texts(payload.get("reasons", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "state_id": self.state_id,
            "valid": self.valid,
            "executable": self.executable,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class DstCoordinationRequirement:
    type: str
    target_id: str
    required: bool | None = None
    actors: tuple[str, ...] = ()
    basis: str = "unknown"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstCoordinationRequirement":
        return cls(
            type=collapse_ws(str(payload.get("type", ""))),
            target_id=collapse_ws(str(payload.get("target_id", ""))),
            required=_normalized_bool_or_none(payload.get("required")),
            actors=_ordered_unique_texts(payload.get("actors", [])),
            basis=collapse_ws(str(payload.get("basis", ""))) or "unknown",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "target_id": self.target_id,
            "required": self.required,
            "actors": list(self.actors),
            "basis": self.basis,
        }


@dataclass(frozen=True)
class DstRiskIndicator:
    target_type: str
    target_id: str
    state_id: str
    risks: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstRiskIndicator":
        return cls(
            target_type=collapse_ws(str(payload.get("target_type", ""))),
            target_id=collapse_ws(str(payload.get("target_id", ""))),
            state_id=collapse_ws(str(payload.get("state_id", ""))),
            risks=_ordered_unique_texts(payload.get("risks", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_type": self.target_type,
            "target_id": self.target_id,
            "state_id": self.state_id,
            "risks": list(self.risks),
        }


@dataclass(frozen=True)
class DstFallback:
    from_transition_id: str
    fallback_transition_id: str
    explicit: bool | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstFallback":
        return cls(
            from_transition_id=collapse_ws(str(payload.get("from_transition_id", ""))),
            fallback_transition_id=collapse_ws(str(payload.get("fallback_transition_id", ""))),
            explicit=_normalized_bool_or_none(payload.get("explicit")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_transition_id": self.from_transition_id,
            "fallback_transition_id": self.fallback_transition_id,
            "explicit": self.explicit,
        }


@dataclass(frozen=True)
class DstCandidateSets:
    candidate_transition_ids_from_current_state: tuple[str, ...] = ()
    candidate_decision_ids_from_current_state: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstCandidateSets":
        return cls(
            candidate_transition_ids_from_current_state=_ordered_unique_texts(
                payload.get("candidate_transition_ids_from_current_state", [])
            ),
            candidate_decision_ids_from_current_state=_ordered_unique_texts(
                payload.get("candidate_decision_ids_from_current_state", [])
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_transition_ids_from_current_state": list(self.candidate_transition_ids_from_current_state),
            "candidate_decision_ids_from_current_state": list(self.candidate_decision_ids_from_current_state),
        }


@dataclass(frozen=True)
class DstNormalizedCase:
    fixture_id: str
    source_ref: str
    context: DstNormalizedContext
    actors: tuple[DstNormalizedActor, ...] = ()
    objectives: tuple[DstNormalizedObjective, ...] = ()
    capabilities: tuple[DstNormalizedCapability, ...] = ()
    dependencies: tuple[DstNamedIdRecord, ...] = ()
    constraints: tuple[DstNormalizedConstraint, ...] = ()
    boundaries: tuple[DstNamedIdRecord, ...] = ()
    states: tuple[DstNormalizedState, ...] = ()
    capability_requirements: tuple[DstCapabilityRequirement, ...] = ()
    capability_admissibility: tuple[DstAdmissibilityRecord, ...] = ()
    transitions: tuple[DstNormalizedTransition, ...] = ()
    transition_admissibility: tuple[DstAdmissibilityRecord, ...] = ()
    decisions: tuple[DstNormalizedDecision, ...] = ()
    decision_status: tuple[DstDecisionStatus, ...] = ()
    coordination_requirements: tuple[DstCoordinationRequirement, ...] = ()
    risk_indicators: tuple[DstRiskIndicator, ...] = ()
    fallbacks: tuple[DstFallback, ...] = ()
    candidate_sets: DstCandidateSets = field(default_factory=DstCandidateSets)
    assumptions: tuple[str, ...] = ()
    ambiguities: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    schema_version: str = DST_NORMALIZED_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DstNormalizedCase":
        result = cls(
            fixture_id=collapse_ws(str(payload.get("fixture_id", ""))),
            source_ref=collapse_ws(str(payload.get("source_ref", ""))),
            context=DstNormalizedContext.from_dict(dict(payload.get("context", {}))),
            actors=tuple(DstNormalizedActor.from_dict(item) for item in list(payload.get("actors", [])) if isinstance(item, dict)),
            objectives=tuple(DstNormalizedObjective.from_dict(item) for item in list(payload.get("objectives", [])) if isinstance(item, dict)),
            capabilities=tuple(DstNormalizedCapability.from_dict(item) for item in list(payload.get("capabilities", [])) if isinstance(item, dict)),
            dependencies=tuple(DstNamedIdRecord.from_dict(item) for item in list(payload.get("dependencies", [])) if isinstance(item, dict)),
            constraints=tuple(DstNormalizedConstraint.from_dict(item) for item in list(payload.get("constraints", [])) if isinstance(item, dict)),
            boundaries=tuple(DstNamedIdRecord.from_dict(item) for item in list(payload.get("boundaries", [])) if isinstance(item, dict)),
            states=tuple(DstNormalizedState.from_dict(item) for item in list(payload.get("states", [])) if isinstance(item, dict)),
            capability_requirements=tuple(DstCapabilityRequirement.from_dict(item) for item in list(payload.get("capability_requirements", [])) if isinstance(item, dict)),
            capability_admissibility=tuple(
                DstAdmissibilityRecord.from_dict(item, subject_key="capability_id")
                for item in list(payload.get("capability_admissibility", []))
                if isinstance(item, dict)
            ),
            transitions=tuple(DstNormalizedTransition.from_dict(item) for item in list(payload.get("transitions", [])) if isinstance(item, dict)),
            transition_admissibility=tuple(
                DstAdmissibilityRecord.from_dict(item, subject_key="transition_id")
                for item in list(payload.get("transition_admissibility", []))
                if isinstance(item, dict)
            ),
            decisions=tuple(DstNormalizedDecision.from_dict(item) for item in list(payload.get("decisions", [])) if isinstance(item, dict)),
            decision_status=tuple(DstDecisionStatus.from_dict(item) for item in list(payload.get("decision_status", [])) if isinstance(item, dict)),
            coordination_requirements=tuple(DstCoordinationRequirement.from_dict(item) for item in list(payload.get("coordination_requirements", [])) if isinstance(item, dict)),
            risk_indicators=tuple(DstRiskIndicator.from_dict(item) for item in list(payload.get("risk_indicators", [])) if isinstance(item, dict)),
            fallbacks=tuple(DstFallback.from_dict(item) for item in list(payload.get("fallbacks", [])) if isinstance(item, dict)),
            candidate_sets=DstCandidateSets.from_dict(dict(payload.get("candidate_sets", {}))),
            assumptions=_ordered_unique_texts(payload.get("assumptions", [])),
            ambiguities=_ordered_unique_texts(payload.get("ambiguities", [])),
            missing_information=_ordered_unique_texts(payload.get("missing_information", [])),
            schema_version=collapse_ws(str(payload.get("schema_version", DST_NORMALIZED_SCHEMA_VERSION))) or DST_NORMALIZED_SCHEMA_VERSION,
        )
        result._validate()
        return result

    def _validate(self) -> None:
        actor_ids = {item.id for item in self.actors}
        objective_ids = {item.id for item in self.objectives}
        capability_ids = {item.id for item in self.capabilities}
        dependency_ids = {item.id for item in self.dependencies}
        constraint_ids = {item.id for item in self.constraints}
        boundary_ids = {item.id for item in self.boundaries}
        state_ids = {item.id for item in self.states}
        transition_ids = {item.id for item in self.transitions}
        decision_ids = {item.id for item in self.decisions}

        for label, ids in (
            ("actor", actor_ids),
            ("objective", objective_ids),
            ("capability", capability_ids),
            ("dependency", dependency_ids),
            ("constraint", constraint_ids),
            ("boundary", boundary_ids),
            ("state", state_ids),
            ("transition", transition_ids),
            ("decision", decision_ids),
        ):
            if any(not item for item in ids):
                raise ValueError(f"{label} id missing")

        if self.context.evaluation_state_id and self.context.evaluation_state_id not in state_ids:
            raise ValueError("evaluation_state_id references unknown state")

        current_ids = [item.id for item in self.states if item.is_current is True]
        if len(current_ids) == 1 and self.context.evaluation_state_id and self.context.evaluation_state_id != current_ids[0]:
            raise ValueError("evaluation_state_id does not match current state")

        for item in self.objectives:
            if any(actor_id not in actor_ids for actor_id in item.pursued_by):
                raise ValueError(f"objective {item.id} references unknown pursued_by actor")
        for item in self.capabilities:
            if any(objective_id not in objective_ids for objective_id in item.advances_objectives):
                raise ValueError(f"capability {item.id} references unknown objective")
            if any(actor_id not in actor_ids for actor_id in item.controlled_by + item.benefits_to + item.costs_to + item.risks_to):
                raise ValueError(f"capability {item.id} references unknown actor")
        for item in self.states:
            if any(cap_id not in capability_ids for cap_id in item.available_capabilities + item.operational_capabilities):
                raise ValueError(f"state {item.id} references unknown capability")
            if any(dep_id not in dependency_ids for dep_id in item.satisfied_dependencies):
                raise ValueError(f"state {item.id} references unknown dependency")
            if any(constraint_id not in constraint_ids for constraint_id in item.active_constraints):
                raise ValueError(f"state {item.id} references unknown constraint")
            if any(friction.boundary_id not in boundary_ids for friction in item.boundary_friction):
                raise ValueError(f"state {item.id} references unknown boundary")
        for item in self.capability_requirements:
            if item.capability_id not in capability_ids:
                raise ValueError("capability requirement references unknown capability")
            if any(dep_id not in dependency_ids for dep_id in item.required_dependencies):
                raise ValueError("capability requirement references unknown dependency")
            if any(constraint_id not in constraint_ids for constraint_id in item.limiting_constraints):
                raise ValueError("capability requirement references unknown constraint")
            if any(boundary_id not in boundary_ids for boundary_id in item.crossed_boundaries):
                raise ValueError("capability requirement references unknown boundary")
        for item in self.capability_admissibility:
            if item.subject_id not in capability_ids or item.state_id not in state_ids:
                raise ValueError("capability admissibility references unknown id")
        for item in self.transitions:
            if item.source_state_id not in state_ids or item.target_state_id not in state_ids:
                raise ValueError("transition references unknown state")
            if any(capability_id not in capability_ids for capability_id in item.changes_capabilities):
                raise ValueError("transition references unknown capability")
            if any(dep_id not in dependency_ids for dep_id in item.required_dependencies):
                raise ValueError("transition references unknown dependency")
            if any(constraint_id not in constraint_ids for constraint_id in item.constraining_constraints):
                raise ValueError("transition references unknown constraint")
            if any(boundary_id not in boundary_ids for boundary_id in item.crossed_boundaries):
                raise ValueError("transition references unknown boundary")
        for item in self.transition_admissibility:
            if item.subject_id not in transition_ids or item.state_id not in state_ids:
                raise ValueError("transition admissibility references unknown id")
        for item in self.decisions:
            if item.selects_transition_id not in transition_ids:
                raise ValueError("decision references unknown transition")
            for assignment in item.assignments:
                if assignment.actor_id not in actor_ids or assignment.capability_id not in capability_ids:
                    raise ValueError("decision assignment references unknown actor or capability")
        for item in self.decision_status:
            if item.decision_id not in decision_ids or item.state_id not in state_ids:
                raise ValueError("decision status references unknown id")
        for item in self.coordination_requirements:
            if any(actor_id not in actor_ids for actor_id in item.actors):
                raise ValueError("coordination requirement references unknown actor")
        for item in self.risk_indicators:
            if item.state_id and item.state_id not in state_ids:
                raise ValueError("risk indicator references unknown state")
        for item in self.fallbacks:
            if item.from_transition_id not in transition_ids or item.fallback_transition_id not in transition_ids:
                raise ValueError("fallback references unknown transition")
        if any(item not in transition_ids for item in self.candidate_sets.candidate_transition_ids_from_current_state):
            raise ValueError("candidate transition set references unknown transition")
        if any(item not in decision_ids for item in self.candidate_sets.candidate_decision_ids_from_current_state):
            raise ValueError("candidate decision set references unknown decision")
        if self.context.evaluation_state_id:
            evaluation_state_id = self.context.evaluation_state_id
            transition_lookup = {item.id: item for item in self.transitions}
            decision_lookup = {item.id: item for item in self.decisions}
            for transition_id in self.candidate_sets.candidate_transition_ids_from_current_state:
                if transition_lookup[transition_id].source_state_id != evaluation_state_id:
                    raise ValueError("candidate transition does not originate in evaluation state")
            for decision_id in self.candidate_sets.candidate_decision_ids_from_current_state:
                transition_id = decision_lookup[decision_id].selects_transition_id
                if transition_lookup[transition_id].source_state_id != evaluation_state_id:
                    raise ValueError("candidate decision does not originate in evaluation state")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fixture_id": self.fixture_id,
            "source_ref": self.source_ref,
            "context": self.context.to_dict(),
            "actors": [item.to_dict() for item in self.actors],
            "objectives": [item.to_dict() for item in self.objectives],
            "capabilities": [item.to_dict() for item in self.capabilities],
            "dependencies": [item.to_dict() for item in self.dependencies],
            "constraints": [item.to_dict() for item in self.constraints],
            "boundaries": [item.to_dict() for item in self.boundaries],
            "states": [item.to_dict() for item in self.states],
            "capability_requirements": [item.to_dict() for item in self.capability_requirements],
            "capability_admissibility": [item.to_dict(subject_key="capability_id") for item in self.capability_admissibility],
            "transitions": [item.to_dict() for item in self.transitions],
            "transition_admissibility": [item.to_dict(subject_key="transition_id") for item in self.transition_admissibility],
            "decisions": [item.to_dict() for item in self.decisions],
            "decision_status": [item.to_dict() for item in self.decision_status],
            "coordination_requirements": [item.to_dict() for item in self.coordination_requirements],
            "risk_indicators": [item.to_dict() for item in self.risk_indicators],
            "fallbacks": [item.to_dict() for item in self.fallbacks],
            "candidate_sets": self.candidate_sets.to_dict(),
            "assumptions": list(self.assumptions),
            "ambiguities": list(self.ambiguities),
            "missing_information": list(self.missing_information),
        }


def list_dst_normalized_fixture_paths() -> tuple[Path, ...]:
    if not DST_NORMALIZED_FIXTURE_ROOT.exists():
        return ()
    return tuple(sorted(DST_NORMALIZED_FIXTURE_ROOT.glob("*.json")))


def load_dst_normalized_cases() -> tuple[DstNormalizedCase, ...]:
    cases: list[DstNormalizedCase] = []
    for path in list_dst_normalized_fixture_paths():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"invalid normalized fixture payload: {path}")
        cases.append(DstNormalizedCase.from_dict(payload))
    return tuple(cases)


def load_dst_normalized_case(fixture_id: str) -> DstNormalizedCase | None:
    normalized_fixture_id = collapse_ws(str(fixture_id))
    if not normalized_fixture_id:
        return None
    path = DST_NORMALIZED_FIXTURE_ROOT / f"{normalized_fixture_id}.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid normalized fixture payload: {path}")
    return DstNormalizedCase.from_dict(payload)


def normalized_case_from_fixture(
    fixture: DstUseCaseFixture,
    discovery: DstDiscoveryResult | None = None,
) -> DstNormalizedCase:
    checked_in = load_dst_normalized_case(fixture.fixture_id)
    if checked_in is not None:
        return checked_in

    actors = tuple(
        DstNormalizedActor(
            id=_prefixed_id(entry.code, "a", index),
            name=_entry_name(entry),
        )
        for index, entry in enumerate(fixture.section_entries("actors"), start=1)
    )
    objectives = tuple(
        DstNormalizedObjective(
            id=_prefixed_id(entry.code, "o", index),
            name=_entry_name(entry),
        )
        for index, entry in enumerate(fixture.section_entries("objectives"), start=1)
    )
    capabilities = tuple(
        DstNormalizedCapability(
            id=_prefixed_id(entry.code, "k", index),
            name=_entry_name(entry),
        )
        for index, entry in enumerate(fixture.section_entries("capabilities"), start=1)
    )
    dependencies = tuple(
        DstNamedIdRecord(
            id=_prefixed_id(entry.code, "d", index),
            name=_entry_name(entry),
        )
        for index, entry in enumerate(fixture.section_entries("dependencies"), start=1)
    )
    constraints = tuple(
        DstNormalizedConstraint(
            id=_prefixed_id(entry.code, "q", index),
            name=_entry_name(entry),
            kind="unknown",
        )
        for index, entry in enumerate(fixture.section_entries("constraints"), start=1)
    )
    boundaries = tuple(
        DstNamedIdRecord(
            id=_prefixed_id(entry.code, "b", index),
            name=_entry_name(entry),
        )
        for index, entry in enumerate(fixture.section_entries("boundaries"), start=1)
    )

    state_records: list[DstNormalizedState] = []
    state_order: list[str] = []
    state_names: dict[str, str] = {}
    for index, entry in enumerate(fixture.section_entries("states"), start=0):
        state_id = _prefixed_id(entry.code, "s", index)
        state_name = _entry_name(entry)
        state_order.append(state_id)
        state_names[state_id] = state_name or state_id
        state_records.append(
            DstNormalizedState(
                id=state_id,
                name=state_name or state_id,
            )
        )

    discovery_paths = tuple(discovery.candidate_paths) if discovery is not None else ()
    if not discovery_paths:
        from dst.discovery import discovery_result_from_fixture as _discovery_result_from_fixture

        discovery_paths = _discovery_result_from_fixture(fixture).candidate_paths

    for item in discovery_paths:
        for token in _route_tokens(item.route_expression):
            state_id = _prefixed_id(token, "s", len(state_order))
            if state_id in state_names:
                continue
            state_order.append(state_id)
            state_names[state_id] = token
            state_records.append(
                DstNormalizedState(
                    id=state_id,
                    name=token,
                )
            )

    evaluation_state_id = ""
    if "s0" in state_names:
        evaluation_state_id = "s0"
    else:
        for item in discovery_paths:
            tokens = _route_tokens(item.route_expression)
            if tokens:
                evaluation_state_id = _prefixed_id(tokens[0], "s", 0)
                break
    if not evaluation_state_id and state_records:
        evaluation_state_id = state_records[0].id

    target_state_ids: list[str] = []
    for item in discovery_paths:
        tokens = _route_tokens(item.route_expression)
        if not tokens:
            continue
        target_id = _prefixed_id(tokens[-1], "s", 0)
        if target_id != evaluation_state_id and target_id in state_names and target_id not in target_state_ids:
            target_state_ids.append(target_id)

    states = tuple(
        DstNormalizedState(
            id=item.id,
            name=item.name,
            is_current=True if item.id == evaluation_state_id else None,
            is_target=True if item.id in target_state_ids else None,
            available_capabilities=tuple(capability.id for capability in capabilities),
        )
        for item in state_records
    )

    transition_ids_by_edge: dict[tuple[str, str], str] = {}
    transitions: list[DstNormalizedTransition] = []
    for item in discovery_paths:
        tokens = _route_tokens(item.route_expression)
        for source_token, target_token in zip(tokens, tokens[1:]):
            source_id = _prefixed_id(source_token, "s", 0)
            target_id = _prefixed_id(target_token, "s", 0)
            edge = (source_id, target_id)
            if edge in transition_ids_by_edge:
                continue
            transition_id = f"t{len(transition_ids_by_edge) + 1}"
            transition_ids_by_edge[edge] = transition_id
            transitions.append(
                DstNormalizedTransition(
                    id=transition_id,
                    name=f"{source_id} -> {target_id}",
                    source_state_id=source_id,
                    target_state_id=target_id,
                )
            )

    decisions: list[DstNormalizedDecision] = []
    decision_status: list[DstDecisionStatus] = []
    candidate_decision_ids: list[str] = []
    ambiguities = list(discovery.ambiguities if discovery is not None else ())
    for index, item in enumerate(discovery_paths, start=1):
        tokens = _route_tokens(item.route_expression)
        if len(tokens) < 2:
            continue
        selected_transition_id = transition_ids_by_edge.get(
            (_prefixed_id(tokens[0], "s", 0), _prefixed_id(tokens[1], "s", 0))
        )
        if not selected_transition_id:
            continue
        decision_id = f"x{index}"
        decisions.append(
            DstNormalizedDecision(
                id=decision_id,
                name=item.title,
                selects_transition_id=selected_transition_id,
            )
        )
        if len(tokens) > 2:
            ambiguities.append(
                f"multi_step_path_collapsed_to_first_transition:{item.path_id}"
            )
        if evaluation_state_id and transitions and next(
            (
                transition
                for transition in transitions
                if transition.id == selected_transition_id and transition.source_state_id == evaluation_state_id
            ),
            None,
        ) is not None:
            candidate_decision_ids.append(decision_id)
        if evaluation_state_id:
            decision_status.append(
                DstDecisionStatus(
                    decision_id=decision_id,
                    state_id=evaluation_state_id,
                    valid=None,
                    executable=None,
                    reasons=("insufficient_information",),
                )
            )

    candidate_transition_ids = tuple(
        transition.id
        for transition in transitions
        if transition.source_state_id == evaluation_state_id
    )

    notes = []
    if discovery is not None:
        notes.extend(
            item
            for item in (
                *discovery.shared_blockers,
                *(f"path:{path.title}" for path in discovery.candidate_paths),
            )
            if collapse_ws(item)
        )

    return DstNormalizedCase(
        fixture_id=fixture.fixture_id,
        source_ref=fixture.source_ref,
        context=DstNormalizedContext(
            system_name=(discovery.system_name if discovery is not None else fixture.title) or fixture.title,
            decision_problem=(
                discovery.decision_problem
                if discovery is not None and collapse_ws(discovery.decision_problem)
                else f"Decide how to guide {fixture.title}."
            ),
            evaluation_state_id=evaluation_state_id,
            notes=tuple(_ordered_unique_texts(notes)),
        ),
        actors=actors,
        objectives=objectives,
        capabilities=capabilities,
        dependencies=dependencies,
        constraints=constraints,
        boundaries=boundaries,
        states=states,
        transitions=tuple(transitions),
        decisions=tuple(decisions),
        decision_status=tuple(decision_status),
        candidate_sets=DstCandidateSets(
            candidate_transition_ids_from_current_state=candidate_transition_ids,
            candidate_decision_ids_from_current_state=tuple(candidate_decision_ids),
        ),
        assumptions=tuple(_ordered_unique_texts(discovery.assumptions if discovery is not None else ())),
        ambiguities=tuple(_ordered_unique_texts(ambiguities)),
        missing_information=tuple(
            _ordered_unique_texts(discovery.missing_information if discovery is not None else ())
        ),
    )


def coordinated_model_from_normalized_case(case: DstNormalizedCase) -> Model:
    actors = {item.id: Actor(item.name) for item in case.actors}
    objectives = {item.id: Objective(item.name) for item in case.objectives}
    capabilities = {item.id: Capability(item.name) for item in case.capabilities}
    dependencies = {item.id: Dependency(item.name) for item in case.dependencies}
    constraints = {item.id: Constraint(item.name) for item in case.constraints}
    boundaries = {item.id: Boundary(item.name) for item in case.boundaries}
    states = {item.id: State(item.name) for item in case.states}
    transitions = {item.id: Transition(item.name) for item in case.transitions}
    decisions = {item.id: Decision(item.name) for item in case.decisions}
    times = {
        item.time_label: TimePoint(item.time_label)
        for item in case.decisions
        if collapse_ws(item.time_label)
    }

    capability_requirements = {item.capability_id: item for item in case.capability_requirements}
    transition_lookup = {item.id: item for item in case.transitions}
    decision_lookup = {item.id: item for item in case.decisions}
    state_lookup = {item.id: item for item in case.states}

    pursues = frozenset(
        (actors[actor_id], objectives[item.id])
        for item in case.objectives
        for actor_id in item.pursued_by
        if actor_id in actors
    )
    controls = frozenset(
        (actors[actor_id], capabilities[item.id])
        for item in case.capabilities
        for actor_id in item.controlled_by
        if actor_id in actors
    )
    benefits_from = frozenset(
        (actors[actor_id], capabilities[item.id])
        for item in case.capabilities
        for actor_id in item.benefits_to
        if actor_id in actors
    )
    bears_cost = frozenset(
        (actors[actor_id], capabilities[item.id])
        for item in case.capabilities
        for actor_id in item.costs_to
        if actor_id in actors
    )
    bears_risk = frozenset(
        (actors[actor_id], capabilities[item.id])
        for item in case.capabilities
        for actor_id in item.risks_to
        if actor_id in actors
    )
    can_decide = frozenset(
        (actors[item.id], decisions[decision.id])
        for item in case.actors
        if item.can_decide is True
        for decision in case.decisions
    )
    advances = frozenset(
        (capabilities[item.id], objectives[objective_id])
        for item in case.capabilities
        for objective_id in item.advances_objectives
        if objective_id in objectives
    )
    requires = frozenset(
        (capabilities[item.capability_id], dependencies[dependency_id])
        for item in case.capability_requirements
        for dependency_id in item.required_dependencies
        if item.capability_id in capabilities and dependency_id in dependencies
    )
    limited_by = frozenset(
        (capabilities[item.capability_id], constraints[constraint_id])
        for item in case.capability_requirements
        for constraint_id in item.limiting_constraints
        if item.capability_id in capabilities and constraint_id in constraints
    )
    crosses = frozenset(
        (capabilities[item.capability_id], boundaries[boundary_id])
        for item in case.capability_requirements
        for boundary_id in item.crossed_boundaries
        if item.capability_id in capabilities and boundary_id in boundaries
    )
    available = frozenset(
        (capabilities[capability_id], states[item.id])
        for item in case.states
        for capability_id in item.available_capabilities
        if capability_id in capabilities
    )
    operational = frozenset(
        (capabilities[capability_id], states[item.id])
        for item in case.states
        for capability_id in item.operational_capabilities
        if capability_id in capabilities
    )
    satisfied = frozenset(
        (dependencies[dependency_id], states[item.id])
        for item in case.states
        for dependency_id in item.satisfied_dependencies
        if dependency_id in dependencies
    )
    active = frozenset(
        (constraints[constraint_id], states[item.id])
        for item in case.states
        for constraint_id in item.active_constraints
        if constraint_id in constraints
    )
    friction_at = frozenset(
        (boundaries[item.boundary_id], states[state.id])
        for state in case.states
        for item in state.boundary_friction
        if item.present is True and item.boundary_id in boundaries
    )

    admissible_under_records: set[tuple[Capability, Constraint, State]] = set()
    active_constraints_by_state = {
        item.id: set(item.active_constraints) for item in case.states
    }
    capability_requirement_lookup = {
        item.capability_id: item for item in case.capability_requirements
    }
    for item in case.capability_admissibility:
        if item.admissible is not True:
            continue
        requirement = capability_requirement_lookup.get(item.subject_id)
        if requirement is None:
            continue
        for constraint_id in requirement.limiting_constraints:
            if constraint_id in active_constraints_by_state.get(item.state_id, set()):
                admissible_under_records.add(
                    (capabilities[item.subject_id], constraints[constraint_id], states[item.state_id])
                )

    changes = frozenset(
        (transitions[item.id], capabilities[capability_id])
        for item in case.transitions
        for capability_id in item.changes_capabilities
        if capability_id in capabilities
    )
    requires_for_transition = frozenset(
        (transitions[item.id], dependencies[dependency_id])
        for item in case.transitions
        for dependency_id in item.required_dependencies
        if dependency_id in dependencies
    )
    constrained_by_transition = frozenset(
        (transitions[item.id], constraints[constraint_id])
        for item in case.transitions
        for constraint_id in item.constraining_constraints
        if constraint_id in constraints
    )
    crosses_transition = frozenset(
        (transitions[item.id], boundaries[boundary_id])
        for item in case.transitions
        for boundary_id in item.crossed_boundaries
        if boundary_id in boundaries
    )

    transition_admissible_under_records: set[tuple[Transition, Constraint, State]] = set()
    for item in case.transition_admissibility:
        if item.admissible is not True:
            continue
        transition = transition_lookup.get(item.subject_id)
        if transition is None:
            continue
        for constraint_id in transition.constraining_constraints:
            if constraint_id in active_constraints_by_state.get(item.state_id, set()):
                transition_admissible_under_records.add(
                    (transitions[item.subject_id], constraints[constraint_id], states[item.state_id])
                )

    selects = frozenset(
        (decisions[item.id], transitions[item.selects_transition_id])
        for item in case.decisions
    )
    assigns = frozenset(
        (decisions[item.id], actors[assignment.actor_id], capabilities[assignment.capability_id])
        for item in case.decisions
        for assignment in item.assignments
    )
    at_time = frozenset(
        (decisions[item.id], times[item.time_label])
        for item in case.decisions
        if item.time_label in times
    )
    valid = frozenset(
        (decisions[item.decision_id], states[item.state_id])
        for item in case.decision_status
        if item.valid is True
    )
    executable = frozenset(
        (decisions[item.decision_id], states[item.state_id])
        for item in case.decision_status
        if item.executable is True
    )

    return Model(
        actors=frozenset(actors.values()),
        objectives=frozenset(objectives.values()),
        capabilities=frozenset(capabilities.values()),
        dependencies=frozenset(dependencies.values()),
        constraints=frozenset(constraints.values()),
        boundaries=frozenset(boundaries.values()),
        states=frozenset(states.values()),
        transitions=frozenset(transitions.values()),
        decisions=frozenset(decisions.values()),
        times=frozenset(times.values()),
        pursues=pursues,
        controls=controls,
        benefits_from=benefits_from,
        bears_cost=bears_cost,
        bears_risk=bears_risk,
        can_decide=can_decide,
        advances=advances,
        requires=requires,
        limited_by=limited_by,
        crosses=crosses,
        available=available,
        operational=operational,
        satisfied=satisfied,
        active=active,
        admissible_under=frozenset(admissible_under_records),
        friction_at=friction_at,
        current=frozenset(states[item.id] for item in case.states if item.is_current is True),
        target_state=frozenset(states[item.id] for item in case.states if item.is_target is True),
        changes=changes,
        requires_for_transition=requires_for_transition,
        constrained_by_transition=constrained_by_transition,
        crosses_transition=crosses_transition,
        transition_admissible_under=frozenset(transition_admissible_under_records),
        selects=selects,
        assigns=assigns,
        at_time=at_time,
        valid=valid,
        executable=executable,
        source={transitions[item.id]: states[item.source_state_id] for item in case.transitions},
        target={transitions[item.id]: states[item.target_state_id] for item in case.transitions},
    )


__all__ = [
    "DST_NORMALIZED_FIXTURE_ROOT",
    "DST_PROMPT_PATH",
    "DST_NORMALIZED_SCHEMA_VERSION",
    "DstAdmissibilityRecord",
    "DstBoundaryFriction",
    "DstCandidateSets",
    "DstCapabilityRequirement",
    "DstCoordinationRequirement",
    "DstDecisionAssignment",
    "DstDecisionStatus",
    "DstFallback",
    "DstNamedIdRecord",
    "DstNormalizedActor",
    "DstNormalizedCapability",
    "DstNormalizedCase",
    "DstNormalizedContext",
    "DstNormalizedConstraint",
    "DstNormalizedDecision",
    "DstNormalizedObjective",
    "DstNormalizedState",
    "DstNormalizedTransition",
    "DstRiskIndicator",
    "build_dst_normalization_prompt",
    "coordinated_model_from_normalized_case",
    "dst_normalized_schema_hint",
    "list_dst_normalized_fixture_paths",
    "load_dst_normalized_case",
    "load_dst_normalized_cases",
    "load_dst_prompt_template",
    "normalized_case_from_fixture",
]
