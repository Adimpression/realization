"""Trace and causality types for typed design mediation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReferenceKind(StrEnum):
    OBJECTIVE = "objective"
    INTENT = "intent"
    OBLIGATION = "obligation"
    EMBODIMENT = "embodiment"
    ENCODING = "encoding"
    OBSERVATION = "observation"
    REVISION = "revision"


@dataclass(frozen=True, slots=True)
class DesignRef:
    ref_id: str
    target_id: str
    kind: ReferenceKind
    note: str = ""


@dataclass(frozen=True, slots=True)
class ObjectiveRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.OBJECTIVE


@dataclass(frozen=True, slots=True)
class IntentRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.INTENT


@dataclass(frozen=True, slots=True)
class ObligationRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.OBLIGATION


@dataclass(frozen=True, slots=True)
class EmbodimentRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.EMBODIMENT


@dataclass(frozen=True, slots=True)
class EncodingRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.ENCODING


@dataclass(frozen=True, slots=True)
class ObservationRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.OBSERVATION


@dataclass(frozen=True, slots=True)
class RevisionRef(DesignRef):
    kind: ReferenceKind = ReferenceKind.REVISION


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    link_id: str
    observation_ref: str
    supports: bool
    obligation_ref: str | None = None
    encoding_ref: str | None = None
    rationale: str = ""

