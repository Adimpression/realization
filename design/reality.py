"""Reality-facing evidence types for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class EvidenceSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RealityEvidenceKind(StrEnum):
    OBSERVED_SIGNAL = "observed_signal"
    ACTION_EVENT = "action_event"
    FEEDBACK_EVENT = "feedback_event"
    CONSTRAINT_ACTIVATION = "constraint_activation"
    BOUNDARY_FRICTION = "boundary_friction"
    QUEUE_CONGESTION = "queue_congestion"
    HANDOFF_FAILURE = "handoff_failure"
    OVERRIDE_EVENT = "override_event"
    TRUST_FAILURE = "trust_failure"
    ADOPTION_DRIFT = "adoption_drift"


@dataclass(frozen=True, slots=True)
class RealityEvidence:
    evidence_id: str
    kind: RealityEvidenceKind
    actor_or_system_source: str
    observed_fact: str
    affected_encoding_refs: tuple[str, ...] = ()
    affected_obligation_refs: tuple[str, ...] = ()
    severity: EvidenceSeverity = EvidenceSeverity.MEDIUM
    time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ObservedSignal(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.OBSERVED_SIGNAL, init=False
    )


@dataclass(frozen=True, slots=True)
class ActionEvent(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.ACTION_EVENT, init=False
    )


@dataclass(frozen=True, slots=True)
class FeedbackEvent(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.FEEDBACK_EVENT, init=False
    )


@dataclass(frozen=True, slots=True)
class ConstraintActivation(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.CONSTRAINT_ACTIVATION, init=False
    )


@dataclass(frozen=True, slots=True)
class BoundaryFriction(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.BOUNDARY_FRICTION, init=False
    )


@dataclass(frozen=True, slots=True)
class QueueCongestion(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.QUEUE_CONGESTION, init=False
    )


@dataclass(frozen=True, slots=True)
class HandoffFailure(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.HANDOFF_FAILURE, init=False
    )


@dataclass(frozen=True, slots=True)
class OverrideEvent(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.OVERRIDE_EVENT, init=False
    )


@dataclass(frozen=True, slots=True)
class TrustFailure(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.TRUST_FAILURE, init=False
    )


@dataclass(frozen=True, slots=True)
class AdoptionDrift(RealityEvidence):
    kind: RealityEvidenceKind = field(
        default=RealityEvidenceKind.ADOPTION_DRIFT, init=False
    )

