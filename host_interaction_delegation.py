"""Compatibility facade for shared host-interaction delegation."""

from realized_host_interaction.delegation import (
    artifact_with_delegated_virtual_mounts,
    build_host_interaction_delegated_mounts,
    host_interaction_delegation_requires_escalation,
    normalized_requested_delegation,
)


__all__ = [
    "artifact_with_delegated_virtual_mounts",
    "build_host_interaction_delegated_mounts",
    "host_interaction_delegation_requires_escalation",
    "normalized_requested_delegation",
]
