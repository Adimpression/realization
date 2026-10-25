"""Mechanical dispatch for the shared non-skill host-action surface."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .actions import (
    host_interaction_fs_read,
    host_interaction_net_http,
    host_interaction_process_run,
    host_interaction_repo_search,
    host_interaction_repo_tree,
)
from .models import HostInteractionAttachment


SHARED_HOST_INTERACTION_ACTION_CAPABILITIES = (
    "ws.repo.tree",
    "ws.repo.search",
    "ws.fs.read",
    "ws.process.run",
    "ws.net.http",
)


def is_shared_host_interaction_action_capability(capability: str) -> bool:
    """
    High Level Purpose:
        In circumstances like host-backed capability mediation, helps with deciding whether one capability belongs to the shared non-skill host-action substrate.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by keeping the shared non-skill action boundary explicit rather than re-encoding it in shell-local dispatch logic.

    Example Input Output:
        Input: `is_shared_host_interaction_action_capability('ws.fs.read')`
        Output: True

    Args:
        capability: Value for `capability` used by `is_shared_host_interaction_action_capability`. Expected type: `str`.

    Returns:
        bool: Result produced by `is_shared_host_interaction_action_capability`.
    """
    return str(capability) in SHARED_HOST_INTERACTION_ACTION_CAPABILITIES


def execute_shared_host_interaction_action(
    *,
    capability: str,
    attachment: HostInteractionAttachment | None,
    arguments: dict[str, Any],
    resolve_read_path: Callable[[str], Path] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed non-skill capability execution, helps with dispatching one attachment-scoped action through the shared substrate rather than through shell-local branching.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by centralizing the common host-action dispatch and result vocabulary below workstation shell code.

    Example Input Output:
        Input: `execute_shared_host_interaction_action(capability='ws.repo.tree', attachment=HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), arguments={'path': 'src'})`
        Output: {'status': 'ok', 'capability': 'ws.repo.tree', 'target': 'main', 'path': 'src', 'tree': ['app.py']}

    Args:
        capability: Value for `capability` used by `execute_shared_host_interaction_action`. Expected type: `str`.
        attachment: Value for `attachment` used by `execute_shared_host_interaction_action`. Expected type: `HostInteractionAttachment`.
        arguments: Value for `arguments` used by `execute_shared_host_interaction_action`. Expected type: `dict[str, Any]`.
        resolve_read_path: Value for `resolve_read_path` used by `execute_shared_host_interaction_action`. Expected type: `Callable[[str], Path] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `execute_shared_host_interaction_action`.
    """
    normalized_capability = str(capability)
    if normalized_capability == "ws.repo.tree":
        if attachment is None:
            raise ValueError("ws.repo.tree requires an attachment.")
        return host_interaction_repo_tree(
            attachment,
            relative_path=str(arguments.get("path", "")).strip(),
            max_depth=int(arguments.get("max_depth", 2)),
            max_entries=int(arguments.get("max_entries", 200)),
        )
    if normalized_capability == "ws.repo.search":
        if attachment is None:
            raise ValueError("ws.repo.search requires an attachment.")
        return host_interaction_repo_search(
            attachment,
            pattern=str(arguments["pattern"]),
            relative_path=str(arguments.get("relative_path", "")).strip(),
            glob=str(arguments.get("glob", "")).strip(),
            max_matches=int(arguments.get("max_matches", 100)),
        )
    if normalized_capability == "ws.fs.read":
        if attachment is None:
            raise ValueError("ws.fs.read requires an attachment.")
        requested_path = str(arguments["path"])
        resolved_path = resolve_read_path(requested_path) if resolve_read_path is not None else None
        return host_interaction_fs_read(
            attachment,
            requested_path=requested_path,
            resolved_path=resolved_path,
            max_chars=int(arguments.get("max_chars", 12000)),
        )
    if normalized_capability == "ws.process.run":
        if attachment is None:
            raise ValueError("ws.process.run requires an attachment.")
        return host_interaction_process_run(
            attachment,
            argv=[str(item) for item in arguments["argv"]],
            cwd_relative_path=str(arguments.get("cwd", ".")),
            timeout_seconds=float(arguments.get("timeout_seconds", 20.0)),
            max_output_chars=int(arguments.get("max_output_chars", 12000)),
        )
    if normalized_capability == "ws.net.http":
        return host_interaction_net_http(
            method=str(arguments.get("method", "GET")),
            url=str(arguments["url"]),
            headers=dict(arguments.get("headers", {})) if isinstance(arguments.get("headers", {}), dict) else {},
            body=str(arguments.get("body", "")),
            json_body=arguments.get("json_body"),
            timeout_seconds=float(arguments.get("timeout_seconds", 20.0)),
            max_response_chars=int(arguments.get("max_response_chars", 12000)),
        )
    raise ValueError(f"Unsupported shared host interaction capability: {capability}")
