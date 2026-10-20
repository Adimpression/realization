# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from data_governance import normalize_data_class
from runtime_temp import preferred_runtime_temp_root
from semantic_text import collapse_ws

MOUNT_PERMISSION_CHOICES = ("read", "write", "list")


def normalize_mount_permissions(value: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed virtual mount resolution, helps with normalizing mount permissions into the bounded read/write/list vocabulary.

    Reference to Theory:
        Supports bundle-style virtual mounts by making mount access capabilities explicit instead of implicit in a filesystem path.

    Example Input Output:
        Input: `normalize_mount_permissions(value=['read', 'list', 'read'])`
        Output: ['read', 'list']

    Args:
        value: Value for `value` used by `normalize_mount_permissions`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `normalize_mount_permissions`.
    """
    if value in (None, "", [], {}):
        return []
    raw_items = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for item in raw_items:
        permission = collapse_ws(str(item)).lower()
        if permission in MOUNT_PERMISSION_CHOICES and permission not in normalized:
            normalized.append(permission)
    return normalized


def default_virtual_mount_table(
    *,
    artifact_id: str = "",
    workspace_root: str = "",
    sqlite_path: str = "",
) -> dict[str, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like governed file brokerage without explicit mount overrides, helps with providing a conservative default virtual mount table for the Python-first host.

    Reference to Theory:
        Supports bundle-style filesystem mediation by giving skills named mounts instead of raw path freedom.

    Example Input Output:
        Input: `default_virtual_mount_table(artifact_id='artifact-demo', workspace_root='/repo', sqlite_path='/repo/state/common.sqlite3')`
        Output: {'skill_tmp': {'root': '/var/.../artifact-demo', 'permissions': ['read', 'write', 'list'], 'data_class': 'derived'}}

    Args:
        artifact_id: Value for `artifact_id` used by `default_virtual_mount_table`. Expected type: `str`. Defaults to `''`.
        workspace_root: Value for `workspace_root` used by `default_virtual_mount_table`. Expected type: `str`. Defaults to `''`.
        sqlite_path: Value for `sqlite_path` used by `default_virtual_mount_table`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, dict[str, Any]]: Result produced by `default_virtual_mount_table`.
    """
    workspace = Path(workspace_root or os.getcwd()).expanduser().resolve()
    sqlite_parent = Path(sqlite_path).expanduser().resolve().parent if collapse_ws(sqlite_path) else workspace
    namespace_seed = collapse_ws(sqlite_path) or str(workspace) or (collapse_ws(artifact_id) or "default")
    namespace = hashlib.sha256(namespace_seed.encode("utf-8")).hexdigest()[:16]
    temp_root = (
        preferred_runtime_temp_root() / "bssc_virtual_mounts" / namespace
    ).resolve()
    return {
        "skill_tmp": {
            "root": str(temp_root),
            "permissions": ["read", "write", "list"],
            "data_class": "derived",
        },
        "skill_input": {
            "root": str(workspace),
            "permissions": ["read", "list"],
            "data_class": "public",
        },
        "skill_output": {
            "root": str(workspace),
            "permissions": ["read", "write", "list"],
            "data_class": "public",
        },
        "shared_readonly": {
            "root": str(workspace),
            "permissions": ["read", "list"],
            "data_class": "internal",
        },
        "state_root": {
            "root": str(sqlite_parent),
            "permissions": ["read", "list"],
            "data_class": "internal",
        },
    }


def normalize_virtual_mount_table(
    value: Any,
    *,
    artifact_id: str = "",
    workspace_root: str = "",
    sqlite_path: str = "",
) -> dict[str, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like governed filesystem brokerage, helps with normalizing the active virtual mount table including explicit overrides and default mounts.

    Reference to Theory:
        Supports bundle-style host mediation by replacing raw path access with named mounts carrying permissions and data classes.

    Example Input Output:
        Input: `normalize_virtual_mount_table(value={'user_selected': {'root': '/tmp/docs', 'permissions': ['read']}}, artifact_id='artifact-demo', workspace_root='/repo', sqlite_path='/repo/state/common.sqlite3')`
        Output: {'skill_tmp': {...}, 'user_selected': {'root': '/tmp/docs', 'permissions': ['read'], 'data_class': 'public'}}

    Args:
        value: Value for `value` used by `normalize_virtual_mount_table`. Expected type: `Any`.
        artifact_id: Value for `artifact_id` used by `normalize_virtual_mount_table`. Expected type: `str`. Defaults to `''`.
        workspace_root: Value for `workspace_root` used by `normalize_virtual_mount_table`. Expected type: `str`. Defaults to `''`.
        sqlite_path: Value for `sqlite_path` used by `normalize_virtual_mount_table`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, dict[str, Any]]: Result produced by `normalize_virtual_mount_table`.
    """
    mounts = default_virtual_mount_table(
        artifact_id=artifact_id,
        workspace_root=workspace_root,
        sqlite_path=sqlite_path,
    )
    if not isinstance(value, Mapping):
        return mounts
    for raw_name, raw_mount in value.items():
        name = collapse_ws(str(raw_name))
        if not name or not isinstance(raw_mount, Mapping):
            continue
        root = collapse_ws(str(raw_mount.get("root", mounts.get(name, {}).get("root", ""))))
        if not root:
            continue
        mounts[name] = {
            "root": str(Path(root).expanduser().resolve()),
            "permissions": normalize_mount_permissions(
                raw_mount.get("permissions", mounts.get(name, {}).get("permissions", []))
            ) or list(mounts.get(name, {}).get("permissions", [])),
            "data_class": normalize_data_class(
                raw_mount.get("data_class", mounts.get(name, {}).get("data_class", "public"))
            ),
        }
    return mounts


def resolve_virtual_mount_path(
    mount_table: Mapping[str, Any],
    *,
    mount_name: str,
    relative_path: str = "",
    operation: str,
) -> tuple[dict[str, Any], Path]:
    """
    High Level Purpose:
        In circumstances like governed mounted file reads and writes, helps with resolving one mount-relative path while preventing escape beyond the declared mount root.

    Reference to Theory:
        Supports virtual mounts by making mount name plus relative path the effective capability boundary rather than a raw absolute host path.

    Example Input Output:
        Input: `resolve_virtual_mount_path(mount_table={'skill_tmp': {'root': '/tmp/demo', 'permissions': ['read', 'write'], 'data_class': 'derived'}}, mount_name='skill_tmp', relative_path='notes/out.txt', operation='write')`
        Output: ({'root': '/tmp/demo', 'permissions': ['read', 'write'], 'data_class': 'derived'}, PosixPath('/tmp/demo/notes/out.txt'))

    Args:
        mount_table: Value for `mount_table` used by `resolve_virtual_mount_path`. Expected type: `Mapping[str, Any]`.
        mount_name: Value for `mount_name` used by `resolve_virtual_mount_path`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `resolve_virtual_mount_path`. Expected type: `str`. Defaults to `''`.
        operation: Value for `operation` used by `resolve_virtual_mount_path`. Expected type: `str`.

    Returns:
        tuple[dict[str, Any], Path]: Result produced by `resolve_virtual_mount_path`.
    """
    normalized_mount_name = collapse_ws(str(mount_name))
    raw_spec = dict(mount_table.get(normalized_mount_name, {})) if isinstance(mount_table.get(normalized_mount_name, {}), Mapping) else {}
    if not raw_spec:
        raise ValueError(f"No virtual mount is configured for {normalized_mount_name}.")
    permissions = normalize_mount_permissions(raw_spec.get("permissions", []))
    if collapse_ws(operation) not in permissions:
        raise ValueError(
            f"Virtual mount {normalized_mount_name} does not allow {collapse_ws(operation)} operations."
        )
    root = Path(str(raw_spec.get("root", ""))).expanduser().resolve()
    if not str(root):
        raise ValueError(f"Virtual mount {normalized_mount_name} has no root.")
    relative = collapse_ws(str(relative_path))
    target = (root / relative).resolve() if relative else root
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Relative path {relative!r} escapes virtual mount {normalized_mount_name}."
        ) from exc
    return (
        {
            "root": str(root),
            "permissions": permissions,
            "data_class": normalize_data_class(raw_spec.get("data_class", "public")),
        },
        target,
    )
