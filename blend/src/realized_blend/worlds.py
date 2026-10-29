"""Canonical persisted-world and mount values for Blend."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BlendWorldMount:
    name: str
    kind: str
    source: str
    access_mode: str
    mount_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "source": self.source,
            "access_mode": self.access_mode,
            "mount_path": self.mount_path,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorldMount":
        return cls(
            name=str(payload.get("name", "")),
            kind=str(payload.get("kind", "")),
            source=str(payload.get("source", "")),
            access_mode=str(payload.get("access_mode", "")),
            mount_path=str(payload.get("mount_path", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class BlendWorld:
    world_id: str
    root_path: str
    created_at: str
    mounts: tuple[BlendWorldMount, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def root(self) -> Path:
        return Path(self.root_path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "root_path": self.root_path,
            "created_at": self.created_at,
            "mounts": [item.to_dict() for item in self.mounts],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendWorld":
        return cls(
            world_id=str(payload.get("world_id", "")),
            root_path=str(payload.get("root_path", "")),
            created_at=str(payload.get("created_at", "")),
            mounts=tuple(
                BlendWorldMount.from_dict(dict(item))
                for item in payload.get("mounts", [])
                if isinstance(item, dict)
            ),
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = ["BlendWorld", "BlendWorldMount"]
