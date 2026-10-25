"""Compatibility facade for the shared host-interaction context."""

from realized_host_interaction.context import (
    HostInteractionContext,
    StaticHostInteractionContext,
    host_interaction_attachments,
    host_interaction_descriptor_payload,
    host_interaction_virtual_mounts,
    host_interaction_workspace_root,
    host_native_interaction_context,
    normalize_host_interaction_attachment_path,
    primary_host_interaction_workspace,
    resolve_host_interaction_attachment,
)


__all__ = [
    "HostInteractionContext",
    "StaticHostInteractionContext",
    "host_interaction_attachments",
    "host_interaction_descriptor_payload",
    "host_interaction_virtual_mounts",
    "host_interaction_workspace_root",
    "host_native_interaction_context",
    "normalize_host_interaction_attachment_path",
    "primary_host_interaction_workspace",
    "resolve_host_interaction_attachment",
]
