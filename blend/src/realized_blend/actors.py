"""Actor references shared by Blend sessions, history, and coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BlendActor:
    actor_id: str
    actor_kind: str
    display_name: str = ""
    capability_envelope: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "actor_kind": self.actor_kind,
            "display_name": self.display_name,
            "capability_envelope": list(self.capability_envelope),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendActor":
        return cls(
            actor_id=str(payload.get("actor_id", "")),
            actor_kind=str(payload.get("actor_kind", "")),
            display_name=str(payload.get("display_name", "")),
            capability_envelope=tuple(str(item) for item in payload.get("capability_envelope", [])),
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = ["BlendActor"]
