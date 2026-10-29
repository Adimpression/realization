"""Authoritative Blend history records, distinct from transport events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BlendHistoryRecord:
    record_id: str
    aggregate_kind: str
    aggregate_id: str
    transition: str
    sequence: int
    recorded_at: str
    actor_id: str = ""
    session_id: str = ""
    workflow_id: str = ""
    workflow_run_id: str = ""
    receipt_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "aggregate_kind": self.aggregate_kind,
            "aggregate_id": self.aggregate_id,
            "transition": self.transition,
            "sequence": self.sequence,
            "recorded_at": self.recorded_at,
            "actor_id": self.actor_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "receipt_refs": list(self.receipt_refs),
            "provenance_refs": list(self.provenance_refs),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendHistoryRecord":
        return cls(
            record_id=str(payload.get("record_id", "")),
            aggregate_kind=str(payload.get("aggregate_kind", "")),
            aggregate_id=str(payload.get("aggregate_id", "")),
            transition=str(payload.get("transition", "")),
            sequence=int(payload.get("sequence", 0) or 0),
            recorded_at=str(payload.get("recorded_at", "")),
            actor_id=str(payload.get("actor_id", "")),
            session_id=str(payload.get("session_id", "")),
            workflow_id=str(payload.get("workflow_id", "")),
            workflow_run_id=str(payload.get("workflow_run_id", "")),
            receipt_refs=tuple(str(item) for item in payload.get("receipt_refs", [])),
            provenance_refs=tuple(str(item) for item in payload.get("provenance_refs", [])),
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = ["BlendHistoryRecord"]
