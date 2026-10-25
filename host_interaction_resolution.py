"""Compatibility facade for shared host-interaction resolution."""

from realized_host_interaction.resolution import (
    DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS,
    DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS,
    normalize_host_interaction_attachment_relative_path,
    normalize_host_interaction_delegation_targets,
    primary_workspace_attachment,
    resolve_host_interaction_attachment_reference,
    safe_join_within_attachment_root,
)


__all__ = [
    "DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS",
    "DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS",
    "normalize_host_interaction_attachment_relative_path",
    "normalize_host_interaction_delegation_targets",
    "primary_workspace_attachment",
    "resolve_host_interaction_attachment_reference",
    "safe_join_within_attachment_root",
]
