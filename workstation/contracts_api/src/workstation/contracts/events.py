"""Transport-neutral event envelopes shared by workstation layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkstationEvent:
    kind: str
    session_id: str
    root_path: str
    timestamp: str
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    parent_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "session_id": self.session_id,
            "root_path": self.root_path,
            "timestamp": self.timestamp,
            "payload": dict(self.payload),
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
        }


# Preserve the historical public ABI while the old module re-exports this class.
WorkstationEvent.__module__ = "workstation.foundation.events.event_bus"

__all__ = ["WorkstationEvent"]
