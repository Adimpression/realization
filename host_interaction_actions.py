"""Compatibility facade for shared attachment-scoped host actions."""

from realized_host_interaction.actions import (
    host_interaction_fs_read,
    host_interaction_net_http,
    host_interaction_process_run,
    host_interaction_repo_search,
    host_interaction_repo_tree,
)


__all__ = [
    "host_interaction_fs_read",
    "host_interaction_net_http",
    "host_interaction_process_run",
    "host_interaction_repo_search",
    "host_interaction_repo_tree",
]
