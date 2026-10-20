"""Framework-agnostic embodiment types for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .core import RecoverabilityRequirement, RiskClass


class EmbodimentKind(StrEnum):
    ACTION = "action"
    NAVIGATION = "navigation"
    CONTAINMENT = "containment"
    STATUS = "status"
    SELECTION = "selection"
    INPUT = "input"
    QUEUE = "queue"
    HANDOFF = "handoff"
    INTERLOCK = "interlock"
    AUDIT = "audit"


@dataclass(frozen=True, slots=True)
class DesignEmbodiment:
    embodiment_id: str
    name: str
    kind: EmbodimentKind
    obligation_refs: tuple[str, ...] = ()
    invariant_refs: tuple[str, ...] = ()
    risk_class: RiskClass = RiskClass.NORMAL
    recoverability_posture: RecoverabilityRequirement = (
        RecoverabilityRequirement.BASIC
    )
    constraints: tuple[str, ...] = ()
    implementation_notes: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ActionEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.ACTION, init=False)


@dataclass(frozen=True, slots=True)
class NavigationEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.NAVIGATION, init=False)


@dataclass(frozen=True, slots=True)
class ContainmentEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.CONTAINMENT, init=False)


@dataclass(frozen=True, slots=True)
class StatusEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.STATUS, init=False)


@dataclass(frozen=True, slots=True)
class SelectionEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.SELECTION, init=False)


@dataclass(frozen=True, slots=True)
class InputEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.INPUT, init=False)


@dataclass(frozen=True, slots=True)
class QueueEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.QUEUE, init=False)


@dataclass(frozen=True, slots=True)
class HandoffEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.HANDOFF, init=False)


@dataclass(frozen=True, slots=True)
class InterlockEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.INTERLOCK, init=False)


@dataclass(frozen=True, slots=True)
class AuditEmbodiment(DesignEmbodiment):
    kind: EmbodimentKind = field(default=EmbodimentKind.AUDIT, init=False)

