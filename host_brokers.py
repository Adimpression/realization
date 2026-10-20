# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import urllib.error
import urllib.request
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from applied_theory_types import utc_now
from data_governance import (
    ensure_governed_data_access,
    normalize_data_class,
    normalize_named_query_registry,
    query_is_read_only,
)
from host_abi import validate_host_broker_invocation
from macos_host_brokers import (
    capture_screenshot,
    copy_to_clipboard,
    open_app,
    open_browser,
    open_file,
    open_folder,
    open_location,
    reveal_in_finder,
)
from semantic_text import collapse_ws
from skill_governance import composition_binding_targets
from virtual_mounts import normalize_virtual_mount_table, resolve_virtual_mount_path


_NAMED_TOOL_TARGETS = {
    "open_browser": "macos.open_browser",
    "open_app": "macos.open_app",
    "open_file": "macos.open_file",
    "open_folder": "macos.open_folder",
    "open_location": "macos.open_location",
    "reveal_in_finder": "macos.reveal_in_finder",
    "capture_screenshot": "macos.capture_screenshot",
    "copy_to_clipboard": "macos.copy_to_clipboard",
}


def _mapping_arguments(arguments: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like invoking named host brokers from a mediated controller path, helps with normalizing raw broker arguments into one mutable mapping.

    Reference to Theory:
        Supports host mediation by keeping broker invocation shapes uniform before dispatch.

    Example Input Output:
        Input: `_mapping_arguments(arguments={'path': '/tmp/demo.txt'})`
        Output: {'path': '/tmp/demo.txt'}

    Args:
        arguments: Value for `arguments` used by `_mapping_arguments`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        dict[str, Any]: Result produced by `_mapping_arguments`.
    """
    return dict(arguments) if isinstance(arguments, Mapping) else {}


def _governance_context(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _governed_sqlite_path(governance_context: Mapping[str, Any] | None) -> str:
    context = _governance_context(governance_context)
    selected = collapse_ws(str(context.get("sqlite_path", "")))
    if selected:
        return selected
    return collapse_ws(os.getenv("STATE_SQLITE_PATH", ""))


def _virtual_mount_table(governance_context: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    context = _governance_context(governance_context)
    return normalize_virtual_mount_table(
        context.get("virtual_mounts", {}),
        artifact_id=collapse_ws(str(context.get("artifact_id", ""))),
        workspace_root=collapse_ws(str(context.get("workspace_root", ""))),
        sqlite_path=_governed_sqlite_path(context),
    )


def _builtin_named_queries() -> dict[str, dict[str, Any]]:
    return {
        "artifact_count": {
            "sql": "SELECT COUNT(*) AS artifact_count FROM artifacts",
            "parameter_order": [],
            "data_class": "internal",
        },
        "artifact_titles_by_prefix": {
            "sql": (
                "SELECT title FROM artifacts "
                "WHERE title LIKE ? ORDER BY title LIMIT ?"
            ),
            "parameter_order": ["prefix", "limit"],
            "data_class": "internal",
        },
    }


def _named_query_registry(governance_context: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    context = _governance_context(governance_context)
    registry = _builtin_named_queries()
    registry.update(normalize_named_query_registry(context.get("named_queries", {})))
    return registry


def _skill_state_namespace(governance_context: Mapping[str, Any] | None) -> str:
    context = _governance_context(governance_context)
    explicit = collapse_ws(str(context.get("skill_state_namespace", "")))
    if explicit:
        return explicit
    artifact_id = collapse_ws(str(context.get("artifact_id", "")))
    if artifact_id:
        return artifact_id
    return "default"


def _decode_state_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return raw


def _ensure_skill_state_table(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS governed_skill_state (
            namespace TEXT NOT NULL,
            key TEXT NOT NULL,
            value_json TEXT NOT NULL,
            data_class TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(namespace, key)
        )
        """
    )
    connection.commit()


def fs_read_text(*, path: str, governance_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed filesystem reads through the host broker layer, helps with reading one text file and returning its contents in a structured broker result.

    Reference to Theory:
        Supports bundle-style host ownership of filesystem effects by turning file reads into named mediated requests.

    Example Input Output:
        Input: `fs_read_text(path='/tmp/demo.txt')`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'text': 'hello'}

    Args:
        path: Value for `path` used by `fs_read_text`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `fs_read_text`.
    """
    target = Path(path)
    return {"status": "ok", "path": str(target), "text": target.read_text()}


def fs_write_text(
    *,
    path: str,
    text: str,
    append: bool = False,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed filesystem writes through the host broker layer, helps with writing text to one file while returning a structured broker result.

    Reference to Theory:
        Supports host-owned filesystem effects by replacing direct script writes with explicit brokered write requests.

    Example Input Output:
        Input: `fs_write_text(path='/tmp/demo.txt', text='hello', append=False)`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'bytes_written': 5, 'append': False}

    Args:
        path: Value for `path` used by `fs_write_text`. Expected type: `str`.
        text: Value for `text` used by `fs_write_text`. Expected type: `str`.
        append: Value for `append` used by `fs_write_text`. Expected type: `bool`. Defaults to `False`.

    Returns:
        dict[str, Any]: Result produced by `fs_write_text`.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = str(text)
    if append:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
    else:
        target.write_text(content)
    return {
        "status": "ok",
        "path": str(target),
        "bytes_written": len(content.encode("utf-8")),
        "append": bool(append),
    }


def fs_list_directory(*, path: str, governance_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed directory inspection through the host broker layer, helps with listing the immediate entry names under one directory path in a structured result.

    Reference to Theory:
        Supports host-owned filesystem reads by making directory listing a named mediated read rather than a raw library call inside skills.

    Example Input Output:
        Input: `fs_list_directory(path='/tmp')`
        Output: {'status': 'ok', 'path': '/tmp', 'entries': ['a.txt', 'b.txt']}

    Args:
        path: Value for `path` used by `fs_list_directory`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `fs_list_directory`.
    """
    target = Path(path)
    entries = sorted(item.name for item in target.iterdir())
    return {"status": "ok", "path": str(target), "entries": entries}


def store_sqlite_query(
    *,
    sqlite_path: str,
    query: str,
    parameters: list[Any] | None = None,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed store reads through the host broker layer, helps with executing one bounded SQLite query and returning rows in JSON-safe form.

    Reference to Theory:
        Supports host-owned persistence effects by making store access a named brokered operation rather than an implicit library call.

    Example Input Output:
        Input: `store_sqlite_query(sqlite_path='/tmp/demo.sqlite3', query='SELECT 1 AS value', parameters=[])`
        Output: {'status': 'ok', 'rows': [{'value': 1}], 'row_count': 1}

    Args:
        sqlite_path: Value for `sqlite_path` used by `store_sqlite_query`. Expected type: `str`.
        query: Value for `query` used by `store_sqlite_query`. Expected type: `str`.
        parameters: Value for `parameters` used by `store_sqlite_query`. Expected type: `list[Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `store_sqlite_query`.
    """
    connection = sqlite3.connect(str(sqlite_path))
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(str(query), list(parameters or []))
        rows = [dict(row) for row in cursor.fetchall()]
        return {"status": "ok", "rows": rows, "row_count": len(rows)}
    finally:
        connection.close()


def net_http_get_json(
    *,
    url: str,
    headers: Mapping[str, Any] | None = None,
    timeout_seconds: float = 10.0,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed network reads through the host broker layer, helps with issuing one HTTP GET and decoding a JSON response in a bounded broker result.

    Reference to Theory:
        Supports host-owned communication effects by making HTTP access an explicit named broker request.

    Example Input Output:
        Input: `net_http_get_json(url='https://example.com/data.json', headers={'Accept': 'application/json'}, timeout_seconds=5.0)`
        Output: {'status': 'ok', 'url': 'https://example.com/data.json', 'json': {'ok': True}}

    Args:
        url: Value for `url` used by `net_http_get_json`. Expected type: `str`.
        headers: Value for `headers` used by `net_http_get_json`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        timeout_seconds: Value for `timeout_seconds` used by `net_http_get_json`. Expected type: `float`. Defaults to `10.0`.

    Returns:
        dict[str, Any]: Result produced by `net_http_get_json`.
    """
    request = urllib.request.Request(
        str(url),
        headers={str(key): str(value) for key, value in dict(headers or {}).items()},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds)) as response:
            body = response.read().decode("utf-8")
            status = getattr(response, "status", 200)
            return {
                "status": "ok",
                "url": str(url),
                "http_status": int(200 if status in (None, "") else status),
                "json": json.loads(body),
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": "error",
            "url": str(url),
            "http_status": int(exc.code),
            "error": str(exc),
        }


def net_http_get_text(
    *,
    url: str,
    headers: Mapping[str, Any] | None = None,
    timeout_seconds: float = 10.0,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed network reads through the host broker layer, helps with issuing one HTTP GET and decoding a text response in a bounded broker result.

    Reference to Theory:
        Supports host-owned communication effects by making text HTTP access an explicit named broker request instead of raw network calls inside skills.

    Example Input Output:
        Input: `net_http_get_text(url='https://example.com', headers={'Accept': 'text/html'}, timeout_seconds=5.0)`
        Output: {'status': 'ok', 'url': 'https://example.com', 'text': '<html>...</html>'}

    Args:
        url: Value for `url` used by `net_http_get_text`. Expected type: `str`.
        headers: Value for `headers` used by `net_http_get_text`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        timeout_seconds: Value for `timeout_seconds` used by `net_http_get_text`. Expected type: `float`. Defaults to `10.0`.

    Returns:
        dict[str, Any]: Result produced by `net_http_get_text`.
    """
    request = urllib.request.Request(
        str(url),
        headers={str(key): str(value) for key, value in dict(headers or {}).items()},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds)) as response:
            body = response.read().decode("utf-8")
            status = getattr(response, "status", 200)
            return {
                "status": "ok",
                "url": str(url),
                "http_status": int(200 if status in (None, "") else status),
                "text": body,
            }
    except urllib.error.HTTPError as exc:
        return {
            "status": "error",
            "url": str(url),
            "http_status": int(exc.code),
            "error": str(exc),
        }


def fs_read_mount(
    *,
    mount: str,
    relative_path: str = "",
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed mounted filesystem access, helps with reading one file through a named virtual mount instead of a raw host path.

    Reference to Theory:
        Supports bundle-style virtual mounts by making file access depend on named mounts, mount permissions, and declared data classes.

    Example Input Output:
        Input: `fs_read_mount(mount='skill_input', relative_path='docs/readme.txt', governance_context={'virtual_mounts': {'skill_input': {'root': '/tmp/docs', 'permissions': ['read'], 'data_class': 'public'}}})`
        Output: {'status': 'ok', 'mount': 'skill_input', 'path': '/tmp/docs/readme.txt', 'text': 'hello'}

    Args:
        mount: Value for `mount` used by `fs_read_mount`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `fs_read_mount`. Expected type: `str`. Defaults to `''`.
        governance_context: Value for `governance_context` used by `fs_read_mount`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `fs_read_mount`.
    """
    try:
        mount_spec, target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=mount,
            relative_path=relative_path,
            operation="read",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.read_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[mount_spec.get("data_class", "public")],
        operation="fs.read_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.read_mount", "error": rationale}
    return {
        "status": "ok",
        "mount": collapse_ws(str(mount)),
        "path": str(target),
        "data_class": normalize_data_class(mount_spec.get("data_class", "public")),
        "text": target.read_text(),
    }


def fs_write_mount(
    *,
    mount: str,
    relative_path: str,
    text: str,
    append: bool = False,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed mounted filesystem writes, helps with writing one file through a named virtual mount instead of a raw host path.

    Reference to Theory:
        Supports bundle-style virtual mounts by constraining writes to named mounts whose permissions and data classes are governed.

    Example Input Output:
        Input: `fs_write_mount(mount='skill_output', relative_path='results/out.txt', text='hello', append=False, governance_context={'virtual_mounts': {'skill_output': {'root': '/tmp/out', 'permissions': ['write'], 'data_class': 'derived'}}})`
        Output: {'status': 'ok', 'mount': 'skill_output', 'path': '/tmp/out/results/out.txt', 'bytes_written': 5}

    Args:
        mount: Value for `mount` used by `fs_write_mount`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `fs_write_mount`. Expected type: `str`.
        text: Value for `text` used by `fs_write_mount`. Expected type: `str`.
        append: Value for `append` used by `fs_write_mount`. Expected type: `bool`. Defaults to `False`.
        governance_context: Value for `governance_context` used by `fs_write_mount`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `fs_write_mount`.
    """
    try:
        mount_spec, target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=mount,
            relative_path=relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.write_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[mount_spec.get("data_class", "public")],
        operation="fs.write_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.write_mount", "error": rationale}
    target.parent.mkdir(parents=True, exist_ok=True)
    content = str(text)
    if append:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
    else:
        target.write_text(content)
    return {
        "status": "ok",
        "mount": collapse_ws(str(mount)),
        "path": str(target),
        "data_class": normalize_data_class(mount_spec.get("data_class", "public")),
        "bytes_written": len(content.encode("utf-8")),
        "append": bool(append),
    }


def fs_list_mount(
    *,
    mount: str,
    relative_path: str = "",
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed directory inspection through virtual mounts, helps with listing one mounted directory by mount name plus relative path instead of a raw host path.

    Reference to Theory:
        Supports bundle-style data surfaces by keeping directory traversal inside a named mount boundary with explicit permissions and data classes.

    Example Input Output:
        Input: `fs_list_mount(mount='skill_input', relative_path='trials', governance_context={'virtual_mounts': {'skill_input': {'root': '/repo', 'permissions': ['read', 'list'], 'data_class': 'public'}}})`
        Output: {'status': 'ok', 'mount': 'skill_input', 'path': '/repo/trials', 'entries': ['chemistry', 'physics']}

    Args:
        mount: Value for `mount` used by `fs_list_mount`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `fs_list_mount`. Expected type: `str`. Defaults to `''`.
        governance_context: Value for `governance_context` used by `fs_list_mount`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `fs_list_mount`.
    """
    try:
        mount_spec, target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=mount,
            relative_path=relative_path,
            operation="list",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.list_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[mount_spec.get("data_class", "public")],
        operation="fs.list_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.list_mount", "error": rationale}
    entries = sorted(item.name for item in target.iterdir())
    return {
        "status": "ok",
        "mount": collapse_ws(str(mount)),
        "path": str(target),
        "data_class": normalize_data_class(mount_spec.get("data_class", "public")),
        "entries": entries,
    }


def fs_find_mount(
    *,
    mount: str,
    suffix: str,
    relative_path: str = "",
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed recursive file search through virtual mounts, helps with finding files beneath one mounted root by suffix without exposing raw host paths as the caller contract.

    Reference to Theory:
        Supports bundle-style data surfaces by keeping recursive file discovery inside a named mount boundary with explicit permissions and data classes.

    Example Input Output:
        Input: `fs_find_mount(mount='skill_input', relative_path='trials', suffix='.md', governance_context={'virtual_mounts': {'skill_input': {'root': '/repo', 'permissions': ['read', 'list'], 'data_class': 'public'}}})`
        Output: {'status': 'ok', 'mount': 'skill_input', 'path': '/repo/trials', 'suffix': '.md', 'matches': ['python/README.md']}

    Args:
        mount: Value for `mount` used by `fs_find_mount`. Expected type: `str`.
        suffix: Value for `suffix` used by `fs_find_mount`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `fs_find_mount`. Expected type: `str`. Defaults to `''`.
        governance_context: Value for `governance_context` used by `fs_find_mount`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `fs_find_mount`.
    """
    try:
        mount_spec, target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=mount,
            relative_path=relative_path,
            operation="list",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.find_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[mount_spec.get("data_class", "public")],
        operation="fs.find_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.find_mount", "error": rationale}
    normalized_suffix = collapse_ws(str(suffix))
    if not normalized_suffix:
        return {"status": "error", "broker": "fs.find_mount", "error": "A non-empty suffix is required."}
    matches = sorted(
        str(child.relative_to(target))
        for child in target.rglob(f"*{normalized_suffix}")
        if child.is_file()
    )
    return {
        "status": "ok",
        "mount": collapse_ws(str(mount)),
        "path": str(target),
        "suffix": normalized_suffix,
        "data_class": normalize_data_class(mount_spec.get("data_class", "public")),
        "matches": matches,
    }


def fs_copy_mount(
    *,
    source_mount: str,
    source_relative_path: str,
    destination_mount: str,
    destination_relative_path: str,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        source_spec, source_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=source_mount,
            relative_path=source_relative_path,
            operation="read",
        )
        destination_spec, destination_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=destination_mount,
            relative_path=destination_relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.copy_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[
            source_spec.get("data_class", "public"),
            destination_spec.get("data_class", "public"),
        ],
        operation="fs.copy_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.copy_mount", "error": rationale}
    destination_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_target, destination_target)
    return {
        "status": "ok",
        "source_mount": collapse_ws(str(source_mount)),
        "source_path": str(source_target),
        "destination_mount": collapse_ws(str(destination_mount)),
        "destination_path": str(destination_target),
        "data_classes": [
            normalize_data_class(source_spec.get("data_class", "public")),
            normalize_data_class(destination_spec.get("data_class", "public")),
        ],
    }


def fs_move_mount(
    *,
    source_mount: str,
    source_relative_path: str,
    destination_mount: str,
    destination_relative_path: str,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        source_spec, source_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=source_mount,
            relative_path=source_relative_path,
            operation="write",
        )
        destination_spec, destination_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=destination_mount,
            relative_path=destination_relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.move_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[
            source_spec.get("data_class", "public"),
            destination_spec.get("data_class", "public"),
        ],
        operation="fs.move_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.move_mount", "error": rationale}
    destination_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_target), str(destination_target))
    return {
        "status": "ok",
        "source_mount": collapse_ws(str(source_mount)),
        "source_path": str(source_target),
        "destination_mount": collapse_ws(str(destination_mount)),
        "destination_path": str(destination_target),
        "data_classes": [
            normalize_data_class(source_spec.get("data_class", "public")),
            normalize_data_class(destination_spec.get("data_class", "public")),
        ],
    }


def fs_delete_mount(
    *,
    mount: str,
    relative_path: str,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        mount_spec, target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=mount,
            relative_path=relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.delete_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[mount_spec.get("data_class", "public")],
        operation="fs.delete_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.delete_mount", "error": rationale}
    deleted = False
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        deleted = True
    return {
        "status": "ok",
        "mount": collapse_ws(str(mount)),
        "path": str(target),
        "data_class": normalize_data_class(mount_spec.get("data_class", "public")),
        "deleted": deleted,
    }


def fs_create_zip_mount(
    *,
    source_mount: str,
    source_relative_path: str,
    destination_mount: str,
    destination_relative_path: str,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        source_spec, source_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=source_mount,
            relative_path=source_relative_path,
            operation="read",
        )
        destination_spec, destination_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=destination_mount,
            relative_path=destination_relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.create_zip_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[
            source_spec.get("data_class", "public"),
            destination_spec.get("data_class", "public"),
        ],
        operation="fs.create_zip_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.create_zip_mount", "error": rationale}
    if not source_target.exists():
        return {"status": "error", "broker": "fs.create_zip_mount", "error": f"Source path {source_relative_path!r} does not exist in mount {source_mount}."}
    destination_target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination_target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if source_target.is_dir():
            for child in sorted(source_target.rglob("*")):
                if child.is_dir():
                    continue
                archive.write(child, arcname=str(child.relative_to(source_target)))
        else:
            archive.write(source_target, arcname=source_target.name)
    return {
        "status": "ok",
        "source_mount": collapse_ws(str(source_mount)),
        "source_path": str(source_target),
        "destination_mount": collapse_ws(str(destination_mount)),
        "destination_path": str(destination_target),
        "data_classes": [
            normalize_data_class(source_spec.get("data_class", "public")),
            normalize_data_class(destination_spec.get("data_class", "public")),
        ],
    }


def fs_extract_zip_mount(
    *,
    source_mount: str,
    source_relative_path: str,
    destination_mount: str,
    destination_relative_path: str,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        source_spec, source_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=source_mount,
            relative_path=source_relative_path,
            operation="read",
        )
        destination_spec, destination_target = resolve_virtual_mount_path(
            _virtual_mount_table(governance_context),
            mount_name=destination_mount,
            relative_path=destination_relative_path,
            operation="write",
        )
    except ValueError as exc:
        return {"status": "error", "broker": "fs.extract_zip_mount", "error": str(exc)}
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[
            source_spec.get("data_class", "public"),
            destination_spec.get("data_class", "public"),
        ],
        operation="fs.extract_zip_mount",
    )
    if not allowed:
        return {"status": "error", "broker": "fs.extract_zip_mount", "error": rationale}
    destination_target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_target, "r") as archive:
        archive.extractall(destination_target)
    return {
        "status": "ok",
        "source_mount": collapse_ws(str(source_mount)),
        "source_path": str(source_target),
        "destination_mount": collapse_ws(str(destination_mount)),
        "destination_path": str(destination_target),
        "data_classes": [
            normalize_data_class(source_spec.get("data_class", "public")),
            normalize_data_class(destination_spec.get("data_class", "public")),
        ],
    }


def store_named_query(
    *,
    query_name: str,
    parameters: Mapping[str, Any] | list[Any] | None = None,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed store access, helps with executing one pre-registered named SQLite query instead of arbitrary SQL.

    Reference to Theory:
        Supports bundle-style host ownership of persistence by replacing free-form database access with named governed query handles.

    Example Input Output:
        Input: `store_named_query(query_name='artifact_count', parameters={}, governance_context={'sqlite_path': '/tmp/state.sqlite3'})`
        Output: {'status': 'ok', 'query_name': 'artifact_count', 'rows': [{'artifact_count': 3}], 'row_count': 1}

    Args:
        query_name: Value for `query_name` used by `store_named_query`. Expected type: `str`.
        parameters: Value for `parameters` used by `store_named_query`. Expected type: `Mapping[str, Any] | list[Any] | None`. Defaults to `None`.
        governance_context: Value for `governance_context` used by `store_named_query`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `store_named_query`.
    """
    registry = _named_query_registry(governance_context)
    query_key = collapse_ws(str(query_name))
    spec = dict(registry.get(query_key, {}))
    if not spec:
        return {"status": "error", "broker": "store.named_query", "error": f"No named query is registered for {query_key}."}
    sql = collapse_ws(str(spec.get("sql", "")))
    if not query_is_read_only(sql):
        return {"status": "error", "broker": "store.named_query", "error": f"Named query {query_key} is not read-only."}
    data_class = normalize_data_class(spec.get("data_class", "internal"), default="internal")
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[data_class],
        operation="store.named_query",
    )
    if not allowed:
        return {"status": "error", "broker": "store.named_query", "error": rationale}
    sqlite_path = _governed_sqlite_path(governance_context)
    if not sqlite_path:
        return {"status": "error", "broker": "store.named_query", "error": "No governed SQLite path is available for named queries."}
    bound_parameters: list[Any]
    if isinstance(parameters, list):
        bound_parameters = list(parameters)
    elif isinstance(parameters, Mapping):
        order = list(spec.get("parameter_order", [])) if isinstance(spec.get("parameter_order", []), list) else []
        bound_parameters = [parameters.get(name) for name in order]
    else:
        bound_parameters = []
    connection = sqlite3.connect(str(sqlite_path))
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(sql, bound_parameters)
        rows = [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()
    return {
        "status": "ok",
        "query_name": query_key,
        "data_class": data_class,
        "rows": rows,
        "row_count": len(rows),
    }


def store_skill_state(
    *,
    operation: str,
    key: str = "",
    value: Any = None,
    namespace: str = "",
    data_class: str = "derived",
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed per-skill persistence, helps with reading and writing namespaced skill state in host-owned SQLite rather than exposing arbitrary database handles.

    Reference to Theory:
        Supports the bundle target by making skill-local persistence a named broker surface with explicit namespace and data-class mediation.

    Example Input Output:
        Input: `store_skill_state(operation='put', key='last_result', value={'answer': 12}, governance_context={'artifact_id': 'artifact-force'})`
        Output: {'status': 'ok', 'operation': 'put', 'namespace': 'artifact-force', 'key': 'last_result'}

    Args:
        operation: Value for `operation` used by `store_skill_state`. Expected type: `str`.
        key: Value for `key` used by `store_skill_state`. Expected type: `str`. Defaults to `''`.
        value: Value for `value` used by `store_skill_state`. Expected type: `Any`. Defaults to `None`.
        namespace: Value for `namespace` used by `store_skill_state`. Expected type: `str`. Defaults to `''`.
        data_class: Value for `data_class` used by `store_skill_state`. Expected type: `str`. Defaults to `'derived'`.
        governance_context: Value for `governance_context` used by `store_skill_state`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `store_skill_state`.
    """
    normalized_operation = collapse_ws(str(operation)).lower()
    normalized_key = collapse_ws(str(key))
    normalized_namespace = collapse_ws(str(namespace)) or _skill_state_namespace(governance_context)
    normalized_data_class = normalize_data_class(data_class, default="derived")
    allowed, rationale = ensure_governed_data_access(
        governance_context,
        requested_data_classes=[normalized_data_class],
        operation="store.skill_state",
    )
    if not allowed:
        return {"status": "error", "broker": "store.skill_state", "error": rationale}
    sqlite_path = _governed_sqlite_path(governance_context)
    if not sqlite_path:
        return {"status": "error", "broker": "store.skill_state", "error": "No governed SQLite path is available for skill state."}
    connection = sqlite3.connect(str(sqlite_path))
    connection.row_factory = sqlite3.Row
    try:
        _ensure_skill_state_table(connection)
        cursor = connection.cursor()
        if normalized_operation == "put":
            cursor.execute(
                """
                INSERT INTO governed_skill_state(namespace, key, value_json, data_class, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value_json=excluded.value_json,
                    data_class=excluded.data_class,
                    updated_at=excluded.updated_at
                """,
                (
                    normalized_namespace,
                    normalized_key,
                    json.dumps(value),
                    normalized_data_class,
                    utc_now(),
                ),
            )
            connection.commit()
            return {
                "status": "ok",
                "operation": "put",
                "namespace": normalized_namespace,
                "key": normalized_key,
                "data_class": normalized_data_class,
            }
        if normalized_operation == "get":
            cursor.execute(
                "SELECT value_json, data_class, updated_at FROM governed_skill_state WHERE namespace = ? AND key = ?",
                (normalized_namespace, normalized_key),
            )
            row = cursor.fetchone()
            if row is None:
                return {
                    "status": "ok",
                    "operation": "get",
                    "namespace": normalized_namespace,
                    "key": normalized_key,
                    "found": False,
                }
            return {
                "status": "ok",
                "operation": "get",
                "namespace": normalized_namespace,
                "key": normalized_key,
                "found": True,
                "data_class": normalize_data_class(row["data_class"], default=normalized_data_class),
                "updated_at": str(row["updated_at"]),
                "value": _decode_state_value(str(row["value_json"])),
            }
        if normalized_operation == "delete":
            cursor.execute(
                "DELETE FROM governed_skill_state WHERE namespace = ? AND key = ?",
                (normalized_namespace, normalized_key),
            )
            connection.commit()
            return {
                "status": "ok",
                "operation": "delete",
                "namespace": normalized_namespace,
                "key": normalized_key,
                "deleted": cursor.rowcount > 0,
            }
        if normalized_operation == "list_keys":
            cursor.execute(
                "SELECT key FROM governed_skill_state WHERE namespace = ? ORDER BY key",
                (normalized_namespace,),
            )
            return {
                "status": "ok",
                "operation": "list_keys",
                "namespace": normalized_namespace,
                "keys": [str(row["key"]) for row in cursor.fetchall()],
            }
        return {
            "status": "error",
            "broker": "store.skill_state",
            "error": f"Unsupported skill state operation {normalized_operation}.",
        }
    finally:
        connection.close()


def macos_open_browser(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return open_browser(**kwargs)


def macos_open_app(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return open_app(**kwargs)


def macos_open_file(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return open_file(**kwargs)


def macos_open_folder(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return open_folder(**kwargs)


def macos_open_location(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return open_location(**kwargs)


def macos_reveal_in_finder(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return reveal_in_finder(**kwargs)


def macos_capture_screenshot(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return capture_screenshot(**kwargs)


def macos_copy_to_clipboard(*, governance_context: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    return copy_to_clipboard(**kwargs)


def tool_invoke(
    *,
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_tool = collapse_ws(str(tool_name)).lower()
    target_broker = _NAMED_TOOL_TARGETS.get(normalized_tool)
    if not target_broker:
        return {
            "status": "error",
            "broker": "tool.invoke",
            "error": f"No named tool is registered for {normalized_tool}.",
        }
    result = invoke_host_broker(
        target_broker,
        arguments=dict(arguments) if isinstance(arguments, Mapping) else {},
        governance_context=governance_context,
    )
    return {
        **result,
        "tool_name": normalized_tool,
        "broker": target_broker,
    }


def skill_invoke(
    *,
    skill_title: str,
    semantic_unit: str = "",
    invocation_payload: Any = None,
    max_steps: int = 64,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from store import build_artifact_store

    title_text = collapse_ws(str(skill_title))
    if not title_text:
        return {"status": "error", "broker": "skill.invoke", "error": "A non-empty skill_title is required."}
    store = build_artifact_store()
    installed = [
        artifact
        for artifact in store.load_all_artifacts()
        if collapse_ws(str(getattr(artifact, "title", ""))) == title_text
    ]
    if not installed:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "error": f"No installed skill artifact matches title {title_text!r}.",
        }
    declaration = dict(governance_context.get("declaration", {})) if isinstance(governance_context, Mapping) and isinstance(governance_context.get("declaration", {}), Mapping) else {}
    allowed_bindings = composition_binding_targets(declaration)
    if allowed_bindings and "*" not in allowed_bindings and title_text not in allowed_bindings:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "error": (
                f"Governed composition rights do not bind this skill to {title_text!r}. "
                f"Allowed targets: {', '.join(allowed_bindings)}."
            ),
        }
    artifact = installed[0]
    nested_semantic_unit = collapse_ws(str(semantic_unit)) or title_text
    from controller_runtime_binding import bootstrap_registered_controller

    nested_state, nested_controller = bootstrap_registered_controller(
        semantic_unit=nested_semantic_unit,
        llm_policy="off",
    )
    nested_state.learned_artifacts[str(artifact.id)] = artifact
    content = dict(getattr(artifact, "content", {}) or {})
    input_contract = dict(content.get("input_contract", {}) or {})
    nested_payload = invocation_payload
    if nested_payload is None and not input_contract:
        nested_payload = {}
    elif nested_payload is None and sorted(input_contract) == ["payload"]:
        nested_payload = {"payload": {}}
    artifact_type_value = str(
        getattr(getattr(artifact, "artifact_type", ""), "value", getattr(artifact, "artifact_type", ""))
    ).strip().lower()
    if artifact_type_value == "ability":
        result = nested_controller.execute_function_artifact(
            artifact,
            semantic_unit=nested_semantic_unit,
            explicit_payload=nested_payload,
        )
        return {
            "status": "ok" if result.ok else "error",
            "broker": "skill.invoke",
            "skill_title": title_text,
            "answer": result.answer,
            "stderr": result.stderr,
            "notes": list(result.notes),
            "nested_effect_traces": list(nested_state.effect_traces),
            "nested_capability_grants": list(nested_state.capability_grants),
            "nested_run_outcome": nested_state.run_outcome.value,
            "max_steps": int(max_steps),
        }
    answer = nested_controller.artifact_answer_text(
        artifact,
        semantic_unit=nested_semantic_unit,
        explicit_payload=nested_payload,
    )
    if not answer:
        return {
            "status": "error",
            "broker": "skill.invoke",
            "skill_title": title_text,
            "error": "Target skill did not expose an invokable ability or answer-bearing knowledge surface.",
        }
    return {
        "status": "ok",
        "broker": "skill.invoke",
        "skill_title": title_text,
        "answer": answer,
        "nested_effect_traces": list(nested_state.effect_traces),
        "nested_capability_grants": list(nested_state.capability_grants),
        "nested_run_outcome": nested_state.run_outcome.value,
        "max_steps": int(max_steps),
    }


HOST_BROKER_REGISTRY = {
    "fs.read_text": fs_read_text,
    "fs.write_text": fs_write_text,
    "fs.list_directory": fs_list_directory,
    "fs.read_mount": fs_read_mount,
    "fs.write_mount": fs_write_mount,
    "fs.list_mount": fs_list_mount,
    "fs.find_mount": fs_find_mount,
    "fs.copy_mount": fs_copy_mount,
    "fs.move_mount": fs_move_mount,
    "fs.delete_mount": fs_delete_mount,
    "fs.create_zip_mount": fs_create_zip_mount,
    "fs.extract_zip_mount": fs_extract_zip_mount,
    "store.sqlite_query": store_sqlite_query,
    "store.named_query": store_named_query,
    "store.skill_state": store_skill_state,
    "net.http_get_json": net_http_get_json,
    "net.http_get_text": net_http_get_text,
    "tool.invoke": tool_invoke,
    "skill.invoke": skill_invoke,
    "macos.open_browser": macos_open_browser,
    "macos.open_app": macos_open_app,
    "macos.open_file": macos_open_file,
    "macos.open_folder": macos_open_folder,
    "macos.open_location": macos_open_location,
    "macos.reveal_in_finder": macos_reveal_in_finder,
    "macos.capture_screenshot": macos_capture_screenshot,
    "macos.copy_to_clipboard": macos_copy_to_clipboard,
}


def invoke_host_broker(
    name: str,
    *,
    arguments: Mapping[str, Any] | None = None,
    governance_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated host-effect execution under the controller, helps with dispatching one named broker request to the registered broker implementation.

    Reference to Theory:
        Supports the bundle target by giving the host one explicit broker registry for effectful operations instead of leaving effect routing implicit.

    Example Input Output:
        Input: `invoke_host_broker(name='fs.read_text', arguments={'path': '/tmp/demo.txt'})`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'text': 'hello'}

    Args:
        name: Value for `name` used by `invoke_host_broker`. Expected type: `str`.
        arguments: Value for `arguments` used by `invoke_host_broker`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        governance_context: Value for `governance_context` used by `invoke_host_broker`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `invoke_host_broker`.
    """
    broker_name = collapse_ws(str(name))
    normalized_arguments, abi_error = validate_host_broker_invocation(
        broker_name,
        _mapping_arguments(arguments),
    )
    if normalized_arguments is None:
        return {
            "status": "error",
            "broker": broker_name,
            "error": abi_error,
        }
    handler = HOST_BROKER_REGISTRY.get(broker_name)
    if handler is None:
        return {
            "status": "error",
            "broker": broker_name,
            "error": f"No host broker is registered for {broker_name}.",
        }
    return handler(**normalized_arguments, governance_context=_governance_context(governance_context))
