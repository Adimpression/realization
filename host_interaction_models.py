# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HostInteractionAttachment:
    name: str
    kind: str
    source: str
    access_mode: str
    mount_path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like shared host-interaction substrate description, helps with turning one attachment declaration into a stable JSON-friendly mapping.

        Reference to Theory:
            Supports the shared host-interaction contract by keeping host-visible resources explicit rather than ambient, regardless of whether the backend is host-native or workstation-backed.

        Example Input Output:
            Input: `HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main').to_dict()`
            Output: {'name': 'main', 'kind': 'workspace', 'source': '/tmp/project', 'access_mode': 'read_write', 'mount_path': '/workstation/mounts/main', 'metadata': {}}

        Args:
            self: Bound host-interaction attachment instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "name": self.name,
            "kind": self.kind,
            "source": self.source,
            "access_mode": self.access_mode,
            "mount_path": self.mount_path,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class HostInteractionDescriptor:
    backend_kind: str
    attachments: tuple[HostInteractionAttachment, ...] = ()
    allowed_capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller/runtime and workstation convergence on one shared substrate, helps with serializing the active host-interaction backend into a stable payload.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by making backend kind, attachment scope, and allowed capabilities explicit instead of encoding them in layer-specific assumptions.

        Example Input Output:
            Input: `HostInteractionDescriptor(backend_kind='workstation', attachments=(HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), allowed_capabilities=('ws.fs.read',), metadata={'session_id': 'ws_123'}).to_dict()`
            Output: {'backend_kind': 'workstation', 'attachments': [{'name': 'main', 'kind': 'workspace', 'source': '/tmp/project', 'access_mode': 'read_write', 'mount_path': '/workstation/mounts/main', 'metadata': {}}], 'allowed_capabilities': ['ws.fs.read'], 'metadata': {'session_id': 'ws_123'}}

        Args:
            self: Bound host-interaction descriptor instance.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "backend_kind": self.backend_kind,
            "attachments": [attachment.to_dict() for attachment in self.attachments],
            "allowed_capabilities": list(self.allowed_capabilities),
            "metadata": dict(self.metadata),
        }
