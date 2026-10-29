"""Structural records for multi-actor Blend coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BlendCoordinationRecord:
    coordination_id: str
    coordination_kind: str
    status: str
    subject_kind: str
    subject_id: str
    created_at: str
    updated_at: str = ""
    participant_actor_ids: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "coordination_id": self.coordination_id,
            "coordination_kind": self.coordination_kind,
            "status": self.status,
            "subject_kind": self.subject_kind,
            "subject_id": self.subject_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "participant_actor_ids": list(self.participant_actor_ids),
            "authority_refs": list(self.authority_refs),
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendCoordinationRecord":
        return cls(
            coordination_id=str(payload.get("coordination_id", "")),
            coordination_kind=str(payload.get("coordination_kind", "")),
            status=str(payload.get("status", "")),
            subject_kind=str(payload.get("subject_kind", "")),
            subject_id=str(payload.get("subject_id", "")),
            created_at=str(payload.get("created_at", "")),
            updated_at=str(payload.get("updated_at", "")),
            participant_actor_ids=tuple(str(item) for item in payload.get("participant_actor_ids", [])),
            authority_refs=tuple(str(item) for item in payload.get("authority_refs", [])),
            payload=dict(payload.get("payload", {})),
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = ["BlendCoordinationRecord"]
