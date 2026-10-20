"""Revision and alignment types for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from .core import InteractionObligation, Objective
from .embodiment import DesignEmbodiment
from .framework.base import FrameworkEncoding
from .reality import RealityEvidence


class AlignmentStatus(StrEnum):
    ALIGNED = "aligned"
    DRIFTED = "drifted"
    INVALIDATED = "invalidated"


@dataclass(frozen=True, slots=True)
class DesignSnapshot:
    snapshot_id: str
    objectives: tuple[Objective, ...] = ()
    obligations: tuple[InteractionObligation, ...] = ()
    embodiments: tuple[DesignEmbodiment, ...] = ()
    encodings: tuple[FrameworkEncoding, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RealitySnapshot:
    snapshot_id: str
    evidence: tuple[RealityEvidence, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AlignmentCheck:
    encoding_ref: str
    status: AlignmentStatus
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    obligation_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class InvalidatedEncoding:
    encoding_ref: str
    reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    obligation_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecompilationRequired:
    required: bool
    affected_encoding_refs: tuple[str, ...] = ()
    affected_obligation_refs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DriftReport:
    report_id: str
    alignment_checks: tuple[AlignmentCheck, ...] = ()
    invalidated_encodings: tuple[InvalidatedEncoding, ...] = ()
    recompilation: RecompilationRequired = field(
        default_factory=lambda: RecompilationRequired(required=False)
    )
    metadata: dict[str, object] = field(default_factory=dict)

