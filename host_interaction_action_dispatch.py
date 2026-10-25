"""Compatibility facade for shared host-action dispatch."""

from realized_host_interaction.action_dispatch import (
    SHARED_HOST_INTERACTION_ACTION_CAPABILITIES,
    execute_shared_host_interaction_action,
    is_shared_host_interaction_action_capability,
)


__all__ = [
    "SHARED_HOST_INTERACTION_ACTION_CAPABILITIES",
    "execute_shared_host_interaction_action",
    "is_shared_host_interaction_action_capability",
]
