"""Situated state used to interpret Blend operators and projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BlendContextAttachment:
    name: str
    kind: str
    source: str
    access_mode: str
    mount_path: str
    alias_of: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "source": self.source,
            "access_mode": self.access_mode,
            "mount_path": self.mount_path,
            "alias_of": self.alias_of,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendContextAttachment":
        return cls(
            name=str(payload.get("name", "")),
            kind=str(payload.get("kind", "")),
            source=str(payload.get("source", "")),
            access_mode=str(payload.get("access_mode", "")),
            mount_path=str(payload.get("mount_path", "")),
            alias_of=str(payload.get("alias_of", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class BlendContext:
    attachments: tuple[BlendContextAttachment, ...]
    visible_mounts: tuple[str, ...]
    writable_mounts: tuple[str, ...]
    granted_capabilities: tuple[str, ...]
    task_focus: str = ""
    world_id: str = ""
    world_root: str = ""
    world_mounts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "visible_mounts": list(self.visible_mounts),
            "writable_mounts": list(self.writable_mounts),
            "granted_capabilities": list(self.granted_capabilities),
            "task_focus": self.task_focus,
            "world_id": self.world_id,
            "world_root": self.world_root,
            "world_mounts": list(self.world_mounts),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BlendContext":
        return cls(
            attachments=tuple(
                BlendContextAttachment.from_dict(dict(item))
                for item in payload.get("attachments", [])
                if isinstance(item, dict)
            ),
            visible_mounts=tuple(str(item) for item in payload.get("visible_mounts", [])),
            writable_mounts=tuple(str(item) for item in payload.get("writable_mounts", [])),
            granted_capabilities=tuple(str(item) for item in payload.get("granted_capabilities", [])),
            task_focus=str(payload.get("task_focus", "")),
            world_id=str(payload.get("world_id", "")),
            world_root=str(payload.get("world_root", "")),
            world_mounts=tuple(str(item) for item in payload.get("world_mounts", [])),
        )


__all__ = ["BlendContext", "BlendContextAttachment"]
