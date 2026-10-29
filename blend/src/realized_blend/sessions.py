"""Bounded Blend working-session values."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .context import BlendContext


@dataclass(frozen=True)
class BlendSession:
    session_id: str
    root_path: str
    created_at: str
    actor_kind: str
    projection_kind: str
    context: BlendContext
    initial_task: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def root(self) -> Path:
        return Path(self.root_path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "root_path": self.root_path,
            "created_at": self.created_at,
            "actor_kind": self.actor_kind,
            "projection_kind": self.projection_kind,
            "context": self.context.to_dict(),
            "initial_task": self.initial_task,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendSession":
        return cls(
            session_id=str(payload.get("session_id", "")),
            root_path=str(payload.get("root_path", "")),
            created_at=str(payload.get("created_at", "")),
            actor_kind=str(payload.get("actor_kind", "")),
            projection_kind=str(payload.get("projection_kind", "")),
            context=BlendContext.from_dict(dict(payload.get("context", {}))),
            initial_task=str(payload.get("initial_task", "")),
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = ["BlendSession"]
