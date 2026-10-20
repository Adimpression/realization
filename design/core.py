"""Core semantic types for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Intent(StrEnum):
    DETECT = "detect"
    LOCATE = "locate"
    DISTINGUISH = "distinguish"
    INSPECT = "inspect"
    COMPARE = "compare"
    SELECT = "select"
    ENTER = "enter"
    MODIFY = "modify"
    TRIGGER = "trigger"
    NAVIGATE = "navigate"
    MONITOR = "monitor"
    VERIFY = "verify"
    CONFIRM = "confirm"
    INTERRUPT = "interrupt"
    RECOVER = "recover"
    COORDINATE = "coordinate"
    LEARN = "learn"


class TaskMorphology(StrEnum):
    ONE_SHOT = "one_shot"
    SEQUENTIAL = "sequential"
    BRANCHING = "branching"
    ITERATIVE = "iterative"
    CYCLICAL = "cyclical"
    CONTINUOUS = "continuous"
    INTERRUPT_DRIVEN = "interrupt_driven"
    SUPERVISORY = "supervisory"
    COLLABORATIVE = "collaborative"
    EMERGENCY = "emergency"


class InteractionInvariant(StrEnum):
    VISIBILITY = "visibility"
    SALIENCE = "salience"
    LEGIBILITY = "legibility"
    MAPPING = "mapping"
    FEEDBACK = "feedback"
    CONSTRAINT = "constraint"
    CONSISTENCY = "consistency"
    RECOVERABILITY = "recoverability"
    STATE_AWARENESS = "state_awareness"
    PRIORITIZATION = "prioritization"
    LEARNABILITY = "learnability"
    ACCESSIBILITY = "accessibility"
    REDUNDANCY = "redundancy"
    RESPONSIVENESS = "responsiveness"
    MODE_CLARITY = "mode_clarity"
    TRUSTWORTHINESS = "trustworthiness"


class RiskClass(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class FeedbackRequirement(StrEnum):
    OPTIONAL = "optional"
    IMPLIED = "implied"
    IMMEDIATE = "immediate"
    AUDITABLE = "auditable"


class RecoverabilityRequirement(StrEnum):
    NONE = "none"
    BASIC = "basic"
    STRONG = "strong"
    REVERSIBLE = "reversible"


class CoordinationRequirement(StrEnum):
    NONE = "none"
    HANDOFF = "handoff"
    MULTI_ACTOR = "multi_actor"
    GOVERNANCE = "governance"


@dataclass(frozen=True, slots=True)
class SemanticDesignObject:
    id: str
    name: str
    description: str = ""
    source_refs: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Objective(SemanticDesignObject):
    intent_types: tuple[Intent, ...] = ()
    success_metrics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Constraint(SemanticDesignObject):
    active: bool = True


@dataclass(frozen=True, slots=True)
class InteractionObligation(SemanticDesignObject):
    intent_types: tuple[Intent, ...] = ()
    task_morphologies: tuple[TaskMorphology, ...] = ()
    invariants: tuple[InteractionInvariant, ...] = ()
    constraint_refs: tuple[str, ...] = ()
    risk_class: RiskClass = RiskClass.NORMAL
    feedback_requirement: FeedbackRequirement = FeedbackRequirement.IMMEDIATE
    recoverability_requirement: RecoverabilityRequirement = (
        RecoverabilityRequirement.BASIC
    )
    coordination_requirement: CoordinationRequirement = (
        CoordinationRequirement.NONE
    )

