"""Compatibility facade for the shared host-interaction data contracts."""

from realized_host_interaction.models import (
    HostInteractionAttachment,
    HostInteractionDescriptor,
)


__all__ = [
    "HostInteractionAttachment",
    "HostInteractionDescriptor",
]
