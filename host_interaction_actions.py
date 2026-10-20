# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from host_interaction_models import HostInteractionAttachment
from host_interaction_resolution import safe_join_within_attachment_root


_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def host_interaction_repo_tree(
    attachment: HostInteractionAttachment,
    *,
    relative_path: str = "",
    max_depth: int = 2,
    max_entries: int = 200,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed attachment inspection, helps with returning one bounded directory tree rooted inside a declared attachment.

    Reference to Theory:
        Supports the shared host-interaction substrate by making attachment-scoped tree inspection reusable across workstation-backed and host-native execution.

    Example Input Output:
        Input: `host_interaction_repo_tree(attachment=HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), relative_path='src')`
        Output: {'status': 'ok', 'capability': 'ws.repo.tree', 'target': 'main', 'path': 'src', 'tree': ['app.py', 'lib/']}

    Args:
        attachment: Value for `attachment` used by `host_interaction_repo_tree`. Expected type: `HostInteractionAttachment`.
        relative_path: Value for `relative_path` used by `host_interaction_repo_tree`. Expected type: `str`. Defaults to `''`.
        max_depth: Value for `max_depth` used by `host_interaction_repo_tree`. Expected type: `int`. Defaults to `2`.
        max_entries: Value for `max_entries` used by `host_interaction_repo_tree`. Expected type: `int`. Defaults to `200`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_repo_tree`.
    """
    requested_path = str(relative_path or "").strip()
    root = (
        safe_join_within_attachment_root(Path(attachment.source), requested_path)
        if requested_path
        else Path(attachment.source)
    )
    bounded_max_depth = max(1, int(max_depth))
    bounded_max_entries = max(1, int(max_entries))
    tree: list[str] = []

    def walk(directory: Path, depth: int) -> None:
        if depth > bounded_max_depth or len(tree) >= bounded_max_entries:
            return
        for child in sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold())):
            relative = child.relative_to(root)
            suffix = "/" if child.is_dir() else ""
            tree.append(f"{relative}{suffix}")
            if len(tree) >= bounded_max_entries:
                return
            if child.is_dir():
                walk(child, depth + 1)

    walk(root, 1)
    return {
        "status": "ok",
        "capability": "ws.repo.tree",
        "target": attachment.name,
        "path": requested_path,
        "tree": tree,
    }


def host_interaction_repo_search(
    attachment: HostInteractionAttachment,
    *,
    pattern: str,
    relative_path: str = "",
    glob: str = "",
    max_matches: int = 100,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed repository inspection, helps with running one bounded ripgrep search rooted inside a declared attachment.

    Reference to Theory:
        Supports the shared host-interaction substrate by making attachment-scoped search reusable across workstation-backed and host-native execution.

    Example Input Output:
        Input: `host_interaction_repo_search(attachment=HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), pattern='main\\(')`
        Output: {'status': 'ok', 'capability': 'ws.repo.search', 'target': 'main', 'matches': ['src/app.py:12:def main():']}

    Args:
        attachment: Value for `attachment` used by `host_interaction_repo_search`. Expected type: `HostInteractionAttachment`.
        pattern: Value for `pattern` used by `host_interaction_repo_search`. Expected type: `str`.
        relative_path: Value for `relative_path` used by `host_interaction_repo_search`. Expected type: `str`. Defaults to `''`.
        glob: Value for `glob` used by `host_interaction_repo_search`. Expected type: `str`. Defaults to `''`.
        max_matches: Value for `max_matches` used by `host_interaction_repo_search`. Expected type: `int`. Defaults to `100`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_repo_search`.
    """
    requested_pattern = str(pattern)
    requested_relative_path = str(relative_path or "").strip()
    bounded_max_matches = max(1, int(max_matches))
    command = ["rg", "-n", "--no-heading", "--color", "never", requested_pattern, "."]
    if str(glob or "").strip():
        command[1:1] = ["-g", str(glob)]
    completed = subprocess.run(
        command,
        cwd=str(safe_join_within_attachment_root(Path(attachment.source), requested_relative_path or ".")),
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()][:bounded_max_matches]
    return {
        "status": "ok",
        "capability": "ws.repo.search",
        "target": attachment.name,
        "relative_path": requested_relative_path,
        "returncode": completed.returncode,
        "matches": lines,
    }


def host_interaction_fs_read(
    attachment: HostInteractionAttachment,
    *,
    requested_path: str,
    resolved_path: Path | None = None,
    max_chars: int = 12000,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed file reads, helps with returning one bounded text read result for a declared attachment path.

    Reference to Theory:
        Supports the shared host-interaction substrate by making attachment-scoped file reads reusable while allowing callers to inject an already-resolved bounded path when extra shell-specific resolution is needed.

    Example Input Output:
        Input: `host_interaction_fs_read(attachment=HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), requested_path='README.md')`
        Output: {'status': 'ok', 'capability': 'ws.fs.read', 'target': 'main', 'path': 'README.md', 'content': '# Project', 'truncated': False}

    Args:
        attachment: Value for `attachment` used by `host_interaction_fs_read`. Expected type: `HostInteractionAttachment`.
        requested_path: Value for `requested_path` used by `host_interaction_fs_read`. Expected type: `str`.
        resolved_path: Value for `resolved_path` used by `host_interaction_fs_read`. Expected type: `Path | None`. Defaults to `None`.
        max_chars: Value for `max_chars` used by `host_interaction_fs_read`. Expected type: `int`. Defaults to `12000`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_fs_read`.
    """
    bounded_max_chars = max(1, int(max_chars))
    path = resolved_path or safe_join_within_attachment_root(Path(attachment.source), str(requested_path))
    content = path.read_text()
    return {
        "status": "ok",
        "capability": "ws.fs.read",
        "target": attachment.name,
        "path": str(requested_path),
        "content": content[:bounded_max_chars],
        "truncated": len(content) > bounded_max_chars,
    }


def host_interaction_process_run(
    attachment: HostInteractionAttachment,
    *,
    argv: list[str],
    cwd_relative_path: str = ".",
    timeout_seconds: float = 20.0,
    max_output_chars: int = 12000,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed bounded command execution, helps with running one subprocess inside a declared attachment root without ambient shell access.

    Reference to Theory:
        Supports the shared host-interaction substrate by making attachment-scoped process execution reusable across workstation-backed and host-native backends.

    Example Input Output:
        Input: `host_interaction_process_run(attachment=HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), argv=['python3', '--version'])`
        Output: {'status': 'ok', 'capability': 'ws.process.run', 'target': 'main', 'returncode': 0, 'stdout': 'Python 3.11.0', 'stderr': ''}

    Args:
        attachment: Value for `attachment` used by `host_interaction_process_run`. Expected type: `HostInteractionAttachment`.
        argv: Value for `argv` used by `host_interaction_process_run`. Expected type: `list[str]`.
        cwd_relative_path: Value for `cwd_relative_path` used by `host_interaction_process_run`. Expected type: `str`. Defaults to `'.'`.
        timeout_seconds: Value for `timeout_seconds` used by `host_interaction_process_run`. Expected type: `float`. Defaults to `20.0`.
        max_output_chars: Value for `max_output_chars` used by `host_interaction_process_run`. Expected type: `int`. Defaults to `12000`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_process_run`.
    """
    if not argv:
        raise ValueError("host_interaction_process_run requires a non-empty argv.")
    cwd = safe_join_within_attachment_root(Path(attachment.source), str(cwd_relative_path or "."))
    bounded_max_output_chars = max(1, int(max_output_chars))
    completed = subprocess.run(
        [str(item) for item in argv],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=float(timeout_seconds),
        check=False,
    )
    return {
        "status": "ok",
        "capability": "ws.process.run",
        "target": attachment.name,
        "argv": [str(item) for item in argv],
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout[:bounded_max_output_chars],
        "stderr": completed.stderr[:bounded_max_output_chars],
        "stdout_truncated": len(completed.stdout) > bounded_max_output_chars,
        "stderr_truncated": len(completed.stderr) > bounded_max_output_chars,
    }


def host_interaction_net_http(
    *,
    method: str = "GET",
    url: str,
    headers: dict[str, Any] | None = None,
    body: str = "",
    json_body: Any = None,
    timeout_seconds: float = 20.0,
    max_response_chars: int = 12000,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed bounded network access, helps with issuing one explicit HTTP request through the shared host-interaction substrate instead of ambient network I/O.

    Reference to Theory:
        Supports the shared host-interaction substrate by making network communication one explicit named host action that can be granted or withheld by the outer shell.

    Example Input Output:
        Input: `host_interaction_net_http(method='GET', url='data:text/plain,hello')`
        Output: {'status': 'ok', 'capability': 'ws.net.http', 'method': 'GET', 'url': 'data:text/plain,hello', 'http_status': 200, 'text': 'hello'}

    Args:
        method: Value for `method` used by `host_interaction_net_http`. Expected type: `str`. Defaults to `'GET'`.
        url: Value for `url` used by `host_interaction_net_http`. Expected type: `str`.
        headers: Value for `headers` used by `host_interaction_net_http`. Expected type: `dict[str, Any] | None`. Defaults to `None`.
        body: Value for `body` used by `host_interaction_net_http`. Expected type: `str`. Defaults to `''`.
        json_body: Value for `json_body` used by `json_body`. Expected type: `Any`. Defaults to `None`.
        timeout_seconds: Value for `timeout_seconds` used by `timeout_seconds`. Expected type: `float`. Defaults to `20.0`.
        max_response_chars: Value for `max_response_chars` used by `max_response_chars`. Expected type: `int`. Defaults to `12000`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_net_http`.
    """
    normalized_method = str(method or "GET").strip().upper()
    if normalized_method not in _HTTP_METHODS:
        raise ValueError(f"Unsupported HTTP method: {normalized_method}")
    normalized_headers = {
        str(key): str(value)
        for key, value in dict(headers or {}).items()
        if str(key).strip()
    }
    request_body_bytes: bytes | None = None
    if json_body is not None:
        request_body_bytes = json.dumps(json_body, sort_keys=True).encode("utf-8")
        normalized_headers.setdefault("Content-Type", "application/json")
    elif str(body or ""):
        request_body_bytes = str(body).encode("utf-8")
    bounded_max_response_chars = max(1, int(max_response_chars))
    request = urllib.request.Request(
        str(url),
        headers=normalized_headers,
        data=request_body_bytes,
        method=normalized_method,
    )
    try:
        with urllib.request.urlopen(request, timeout=float(timeout_seconds)) as response:
            raw_bytes = response.read()
            body_text = raw_bytes.decode("utf-8", errors="replace")
            status = getattr(response, "status", 200)
            response_headers = dict(response.headers.items()) if getattr(response, "headers", None) is not None else {}
            result: dict[str, Any] = {
                "status": "ok",
                "capability": "ws.net.http",
                "method": normalized_method,
                "url": str(url),
                "http_status": int(200 if status in (None, "") else status),
                "headers": response_headers,
                "text": body_text[:bounded_max_response_chars],
                "text_truncated": len(body_text) > bounded_max_response_chars,
            }
            try:
                result["json"] = json.loads(body_text)
            except Exception:
                pass
            return result
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return {
            "status": "error",
            "capability": "ws.net.http",
            "method": normalized_method,
            "url": str(url),
            "http_status": int(exc.code),
            "error": str(exc),
            "text": error_body[:bounded_max_response_chars],
            "text_truncated": len(error_body) > bounded_max_response_chars,
        }
