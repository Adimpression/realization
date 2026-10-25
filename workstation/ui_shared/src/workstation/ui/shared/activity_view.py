# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from realized_host_interaction.receipts import host_interaction_receipts_path
from semantic_text import collapse_ws
from workstation.foundation.projections import render_workstation_activity_line


_TAIL_POLL_INTERVAL_SECONDS = 0.10


def workstation_activity_log_offset(root: Path) -> int:
    """
    High Level Purpose:
        In circumstances like workstation chat activity streaming, helps with capturing the current receipt-log byte offset so one turn can tail only the new events it produces.

    Reference to Theory:
        Supports the receipt-driven activity view by keeping the shell presentation layer anchored to the durable receipt stream instead of inventing a parallel progress channel.

    Example Input Output:
        Input: `workstation_activity_log_offset(Path('/tmp/ws'))`
        Output: 128

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.

    Returns:
        int: Result produced by `workstation_activity_log_offset`.
    """
    path = host_interaction_receipts_path(Path(root))
    if not path.exists():
        return 0
    try:
        return int(path.stat().st_size)
    except Exception:
        return 0


def start_workstation_activity_tail(
    *,
    root: Path,
    start_offset: int,
    emit: Callable[[str], None],
) -> Callable[[], None]:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat turns, helps with tailing newly appended receipt events in the background and emitting formatted activity lines as they arrive.

    Reference to Theory:
        Supports the shell / receipt separation by deriving live progress from the durable event log instead of coupling UI updates directly into capability execution internals.

    Example Input Output:
        Input: `start_workstation_activity_tail(root=Path('/tmp/ws'), start_offset=0, emit=print)`
        Output: stopper callback

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.
        start_offset: Value for `start_offset` used by `start_offset`. Expected type: `int`.
        emit: Value for `emit` used by `emit`. Expected type: `Callable[[str], None]`.

    Returns:
        Callable[[], None]: Result produced by `start_workstation_activity_tail`.
    """
    stop_event = threading.Event()
    worker = threading.Thread(
        target=_tail_workstation_activity,
        kwargs={
            "root": Path(root),
            "start_offset": int(start_offset),
            "emit": emit,
            "stop_event": stop_event,
        },
        daemon=True,
    )
    worker.start()

    def stop() -> None:
        stop_event.set()
        worker.join(timeout=1.0)

    return stop


def workstation_activity_line(
    receipt: dict[str, Any],
    *,
    elapsed_seconds: float | None = None,
    prompt_elapsed_seconds: float | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like workstation shell activity presentation, helps with turning one structured receipt event into one concise human-facing progress line.

    Reference to Theory:
        Supports the workstation activity pane by formatting receipts for readability while keeping the raw receipt log unchanged for audit and debugging.

    Example Input Output:
        Input: `workstation_activity_line({'kind': 'user_prompt', 'prompt': 'Inspect the repo.'})`
        Output: 'Prompt received'

    Args:
        receipt: Value for `receipt` used by `receipt`. Expected type: `dict[str, Any]`.

    Returns:
        str: Result produced by `workstation_activity_line`.
    """
    return render_workstation_activity_line(
        receipt,
        elapsed_seconds=elapsed_seconds,
        prompt_elapsed_seconds=prompt_elapsed_seconds,
    )


def _tail_workstation_activity(
    *,
    root: Path,
    start_offset: int,
    emit: Callable[[str], None],
    stop_event: threading.Event,
) -> None:
    path = host_interaction_receipts_path(Path(root))
    offset = max(0, int(start_offset))
    started_timestamps_by_signature: dict[str, list[float]] = {}
    current_prompt_started_at: float | None = None
    while True:
        if not path.exists():
            if stop_event.wait(_TAIL_POLL_INTERVAL_SECONDS):
                break
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                handle.seek(offset)
                chunk = handle.read()
                offset = handle.tell()
        except Exception:
            if stop_event.wait(_TAIL_POLL_INTERVAL_SECONDS):
                break
            continue
        if not chunk:
            if stop_event.is_set():
                break
            stop_event.wait(_TAIL_POLL_INTERVAL_SECONDS)
            continue
        for line in chunk.splitlines():
            if not line.strip():
                continue
            try:
                receipt = json.loads(line)
            except Exception:
                continue
            normalized_receipt = dict(receipt) if isinstance(receipt, dict) else {}
            elapsed_seconds: float | None = None
            timestamp_seconds = _receipt_timestamp_seconds(normalized_receipt)
            if collapse_ws(str(normalized_receipt.get("kind", ""))) == "user_prompt":
                current_prompt_started_at = timestamp_seconds
            if collapse_ws(str(normalized_receipt.get("kind", ""))) == "capability_call":
                signature = _capability_receipt_signature(normalized_receipt)
                phase = collapse_ws(str(normalized_receipt.get("phase", ""))).casefold()
                if signature:
                    if phase == "started":
                        started_timestamps_by_signature.setdefault(signature, []).append(timestamp_seconds)
                    else:
                        started_candidates = started_timestamps_by_signature.get(signature, [])
                        if started_candidates:
                            started_at = started_candidates.pop(0)
                            elapsed_seconds = max(0.0, timestamp_seconds - started_at)
                            if not started_candidates:
                                started_timestamps_by_signature.pop(signature, None)
            prompt_elapsed_seconds: float | None = None
            if current_prompt_started_at is not None:
                prompt_elapsed_seconds = max(0.0, timestamp_seconds - current_prompt_started_at)
            rendered = workstation_activity_line(
                normalized_receipt,
                elapsed_seconds=elapsed_seconds,
                prompt_elapsed_seconds=prompt_elapsed_seconds,
            )
            if rendered:
                emit(rendered)
        if stop_event.wait(_TAIL_POLL_INTERVAL_SECONDS):
            continue


def _capability_started_activity_line(*, capability: str, arguments: dict[str, Any]) -> str:
    if capability == "ws.permissions.list":
        return "Listing session permissions"
    if capability == "ws.permissions.grant":
        capability_name = collapse_ws(str(arguments.get("capability", "")))
        return f"Granting permission: {capability_name}" if capability_name else "Granting permission"
    if capability == "ws.permissions.revoke":
        capability_name = collapse_ws(str(arguments.get("capability", "")))
        return f"Revoking permission: {capability_name}" if capability_name else "Revoking permission"
    if capability == "ws.net.http":
        method = collapse_ws(str(arguments.get("method", "GET"))).upper() or "GET"
        url = _short_preview(str(arguments.get("url", "")), limit=72)
        return _with_preview(f"HTTP {method}", url, label="in")
    if capability == "ws.markdown.create":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Saving learnings to {target_path}" if target_path else "Saving learnings to markdown"
    if capability == "ws.markdown.append":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Appending learnings to {target_path}" if target_path else "Appending learnings to markdown"
    if capability == "ws.skill.import":
        return f"Importing skill from {_display_path(str(arguments.get('path', '')))}"
    if capability == "ws.skill.catalog":
        return "Listing available skills"
    if capability == "ws.skill.describe":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        return f"Describing skill: {title or 'requested skill'}"
    if capability == "ws.skill.export":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        target_path = _display_path(str(arguments.get("out", arguments.get("path", ""))))
        if title and target_path:
            return f"Exporting {title} to {target_path}"
        if title:
            return f"Exporting {title}"
        return "Exporting skill"
    if capability == "ws.skill.permissions":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        return f"Inspecting permissions: {title or 'requested skill'}"
    if capability == "ws.skill.invoke":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        input_preview = _skill_input_preview(arguments)
        return _with_preview(
            f"Invoking skill: {title or 'requested skill'}",
            input_preview,
            label="in",
        )
    if capability == "ws.skill.compose":
        input_preview = _skill_compose_input_preview(arguments)
        return _with_preview(
            "Composing skills",
            input_preview,
            label="in",
        )
    if capability == "ws.repo.search":
        pattern = collapse_ws(str(arguments.get("pattern", "")))
        relative_path = _display_path(str(arguments.get("path", arguments.get("relative_path", ""))))
        if pattern and relative_path:
            return f"Searching {relative_path} for {pattern}"
        if pattern:
            return f"Searching for {pattern}"
        return "Searching workspace"
    if capability == "ws.repo.tree":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Listing {target_path}" if target_path else "Listing workspace"
    if capability == "ws.fs.read":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Reading {target_path}" if target_path else "Reading file"
    if capability == "ws.process.run":
        argv = arguments.get("argv", [])
        command_text = " ".join(str(item) for item in argv[:4]) if isinstance(argv, list) else ""
        return f"Running command: {command_text}" if command_text else "Running command"
    if capability:
        return f"Running {capability}"
    return ""


def _capability_finished_activity_line(
    *,
    capability: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    phase: str,
    elapsed_seconds: float | None,
    prompt_elapsed_seconds: float | None,
) -> str:
    status = collapse_ws(str(result.get("status", ""))).casefold()
    if capability == "ws.permissions.list":
        granted = result.get("granted_capabilities", [])
        count = len(granted) if isinstance(granted, list) else 0
        if status == "ok":
            return _with_timing(
                f"Permissions ready: {count} granted",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Permission listing failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.permissions.grant":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        if status == "ok":
            return _with_timing(
                f"Granted permission: {capability_name or 'capability'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Grant failed: {capability_name or 'capability'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.permissions.revoke":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        if status == "ok":
            return _with_timing(
                f"Revoked permission: {capability_name or 'capability'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Revoke failed: {capability_name or 'capability'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.net.http":
        method = collapse_ws(str(result.get("method", arguments.get("method", "GET")))).upper() or "GET"
        url = _short_preview(str(result.get("url", arguments.get("url", ""))), limit=72)
        if status == "ok":
            return _with_timing(
                _with_preview(
                    f"HTTP {method} ok",
                    _net_http_output_preview(result, fallback=url),
                    label="out",
                ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            _with_preview(
                f"HTTP {method} failed",
                _net_http_output_preview(result, fallback=url),
                label="out",
            ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
    if capability == "ws.markdown.create":
        target_path = _display_path(str(result.get("path", arguments.get("path", ""))))
        if status == "ok":
            return _with_timing(
                f"Saved learnings to {target_path or 'markdown file'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Save learnings failed for {target_path or 'markdown file'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.markdown.append":
        target_path = _display_path(str(result.get("path", arguments.get("path", ""))))
        if status == "ok":
            return _with_timing(
                f"Appended learnings to {target_path or 'markdown file'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Append learnings failed for {target_path or 'markdown file'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.import":
        imported_count = int(result.get("imported_count", 0) or 0)
        if status == "ok":
            imported_preview = _imported_skills_preview(result)
            return _with_timing(
                _with_preview(
                    f"Imported {imported_count} skill{'s' if imported_count != 1 else ''}",
                    imported_preview,
                    label="out",
                ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Skill import failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.catalog":
        returned = int(result.get("returned_skill_count", 0) or 0)
        if status == "ok":
            return _with_timing(
                f"Listed {returned} skill{'s' if returned != 1 else ''}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Skill listing failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.describe":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "ok":
            return _with_timing(
                f"Described skill: {title or 'skill'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Describe failed for {title or 'skill'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.export":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "ok":
            output_preview = _display_path(str(result.get("destination_path", "")))
            return _with_timing(
                _with_preview(f"Exported {title or 'skill'}", output_preview, label="out"),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Export failed for {title or 'skill'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.permissions":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "ok":
            return _with_timing(
                f"Permissions ready: {title or 'skill'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            f"Permissions failed for {title or 'skill'}",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.invoke":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "approval_required":
            return _with_timing(
                f"Waiting for approval: {title or 'skill'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        output_preview = _skill_output_preview(result)
        if phase == "after_escalation" and status == "ok":
            return _with_timing(
                _with_preview(f"Skill completed after approval: {title or 'skill'}", output_preview, label="out"),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        if status == "ok":
            return _with_timing(
                _with_preview(f"Skill completed: {title or 'skill'}", output_preview, label="out"),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            _with_preview(f"Skill failed: {title or 'skill'}", _skill_error_preview(result), label="out"),
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.skill.compose":
        if status == "approval_required":
            title = _short_skill_title(str(result.get("blocked_skill_title", "")))
            return _with_timing(
                f"Waiting for approval: {title or 'skill composition'}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        output_preview = _skill_compose_output_preview(result)
        if status == "ok":
            return _with_timing(
                _with_preview("Skill composition completed", output_preview, label="out"),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            _with_preview("Skill composition failed", output_preview or _skill_error_preview(result), label="out"),
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.repo.search":
        match_count = int(result.get("match_count", 0) or 0)
        if status == "ok":
            return _with_timing(
                _with_preview(
                    f"Search completed: {match_count} match{'es' if match_count != 1 else ''}",
                    _search_output_preview(result),
                    label="out",
                ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Search failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.repo.tree":
        if status == "ok":
            tree = result.get("tree", [])
            count = len(tree) if isinstance(tree, list) else 0
            return _with_timing(
                _with_preview(
                    f"Listed {count} entr{'ies' if count != 1 else 'y'}",
                    _first_list_item_preview(tree),
                    label="out",
                ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Listing failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.fs.read":
        if status == "ok":
            return _with_timing(
                _with_preview(
                    f"Read {_display_path(str(result.get('path', arguments.get('path', ''))))}",
                    _content_preview(str(result.get("content", ""))),
                    label="out",
                ),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            "Read failed",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability == "ws.process.run":
        exit_code = result.get("exit_code")
        if exit_code in {0, "0"}:
            return _with_timing(
                _with_preview("Command completed", _process_output_preview(result), label="out"),
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return _with_timing(
            _with_preview("Command failed", _process_output_preview(result), label="out"),
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if capability:
        if status == "ok":
            return _with_timing(
                f"Completed {capability}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        if status:
            return _with_timing(
                f"{capability} {status}",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
    return ""


def _short_skill_title(text: str) -> str:
    raw = collapse_ws(str(text))
    if " / " in raw:
        return raw.split(" / ", 1)[0].strip()
    return raw


def _display_path(text: str) -> str:
    value = collapse_ws(str(text))
    if not value:
        return ""
    return value.rstrip("/")


def _capability_receipt_signature(receipt: dict[str, Any]) -> str:
    capability = collapse_ws(str(receipt.get("capability", "")))
    arguments = receipt.get("arguments", {})
    if not capability or not isinstance(arguments, dict):
        return ""
    try:
        return capability + "|" + json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    except Exception:
        return capability + "|" + repr(arguments)


def _receipt_timestamp_seconds(receipt: dict[str, Any]) -> float:
    raw = collapse_ws(str(receipt.get("timestamp", "")))
    if not raw:
        return time.time()
    try:
        return datetime.fromisoformat(raw).timestamp()
    except Exception:
        return time.time()


def _with_preview(text: str, preview: str, *, label: str) -> str:
    if not preview:
        return text
    return f"{text} [{label}: {preview}]"


def _with_timing(
    text: str,
    *,
    prompt_elapsed_seconds: float | None = None,
    elapsed_seconds: float | None = None,
) -> str:
    parts: list[str] = []
    if prompt_elapsed_seconds is not None:
        parts.append(f"t+{_elapsed_preview(prompt_elapsed_seconds).lstrip('~')}")
    if elapsed_seconds is not None:
        parts.append(f"op {_elapsed_preview(elapsed_seconds)}")
    if not parts:
        return text
    return f"{text} ({', '.join(parts)})"


def _elapsed_preview(elapsed_seconds: float) -> str:
    seconds = max(0.0, float(elapsed_seconds))
    if seconds < 0.1:
        return "~0.0s"
    if seconds < 1.0:
        return f"~{seconds:.1f}s"
    if seconds < 10.0:
        return f"~{seconds:.1f}s"
    return f"~{seconds:.0f}s"


def _skill_input_preview(arguments: dict[str, Any]) -> str:
    payload = arguments.get("invocation_payload")
    if not isinstance(payload, dict):
        payload = {}
    items: list[str] = []
    for key, value in payload.items():
        preview = _value_preview(value)
        if preview:
            items.append(f"{key}={preview}")
        if len(items) >= 2:
            break
    if items:
        return ", ".join(items)
    semantic_unit = _short_preview(collapse_ws(str(arguments.get("semantic_unit", ""))), limit=64)
    return semantic_unit


def _skill_output_preview(result: dict[str, Any]) -> str:
    answer = _short_preview(str(result.get("answer", "")), limit=72)
    if answer:
        return answer
    parsed_output = result.get("parsed_output")
    if isinstance(parsed_output, dict):
        preview = _first_list_item_preview(parsed_output.get("matches", []))
        if preview:
            return preview
        preview = _short_preview(json.dumps(parsed_output, sort_keys=True), limit=72)
        if preview:
            return preview
    stdout = _short_preview(str(result.get("stdout", "")), limit=72)
    if stdout:
        return stdout
    return _first_list_item_preview(result.get("matches", []))


def _skill_compose_input_preview(arguments: dict[str, Any]) -> str:
    steps = arguments.get("steps", [])
    if not isinstance(steps, list):
        return ""
    titles = [
        _short_skill_title(str(item.get("skill_title", "")))
        for item in steps
        if isinstance(item, dict) and _short_skill_title(str(item.get("skill_title", "")))
    ]
    if not titles:
        return ""
    return " -> ".join(titles[:3]) + (" -> ..." if len(titles) > 3 else "")


def _skill_compose_output_preview(result: dict[str, Any]) -> str:
    final_output = result.get("final_output")
    if isinstance(final_output, dict):
        preview = _short_preview(json.dumps(final_output, sort_keys=True), limit=72)
        if preview:
            return preview
    answer = _short_preview(str(result.get("answer", "")), limit=72)
    if answer:
        return answer
    blocked = _short_skill_title(str(result.get("blocked_skill_title", "")))
    if blocked:
        return blocked
    return ""


def _skill_error_preview(result: dict[str, Any]) -> str:
    for key in ("stderr", "error", "answer"):
        preview = _short_preview(str(result.get(key, "")), limit=72)
        if preview:
            return preview
    return ""


def _search_output_preview(result: dict[str, Any]) -> str:
    matches = result.get("matches", [])
    return _first_list_item_preview(matches)


def _process_output_preview(result: dict[str, Any]) -> str:
    stdout = _short_preview(str(result.get("stdout", "")), limit=72)
    if stdout:
        return stdout
    stderr = _short_preview(str(result.get("stderr", "")), limit=72)
    return stderr


def _net_http_output_preview(result: dict[str, Any], *, fallback: str) -> str:
    http_status = collapse_ws(str(result.get("http_status", "")))
    text_preview = _short_preview(str(result.get("text", "")), limit=72)
    if http_status and text_preview:
        return f"{http_status} {text_preview}"
    if http_status:
        return http_status
    return text_preview or fallback


def _imported_skills_preview(result: dict[str, Any]) -> str:
    imported = result.get("imported", [])
    if not isinstance(imported, list):
        return ""
    for item in imported:
        if isinstance(item, dict):
            title = _short_skill_title(str(item.get("title", "")))
            if title:
                return title
    return ""


def _content_preview(text: str) -> str:
    for line in str(text or "").splitlines():
        preview = _short_preview(line, limit=72)
        if preview:
            return preview
    return ""


def _first_list_item_preview(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    for item in values:
        if isinstance(item, dict):
            for key in ("path", "file", "match", "text", "line"):
                preview = _short_preview(str(item.get(key, "")), limit=72)
                if preview:
                    return preview
            preview = _short_preview(json.dumps(item, sort_keys=True), limit=72)
            if preview:
                return preview
        else:
            preview = _short_preview(str(item), limit=72)
            if preview:
                return preview
    return ""


def _value_preview(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)):
        return _short_preview(str(value), limit=36)
    if isinstance(value, list):
        parts = [_short_preview(str(item), limit=16) for item in value[:2] if _short_preview(str(item), limit=16)]
        return "[" + ", ".join(parts) + (", ..." if len(value) > 2 else "") + "]" if parts else ""
    if isinstance(value, dict):
        parts: list[str] = []
        for key, child in list(value.items())[:2]:
            child_preview = _value_preview(child)
            if child_preview:
                parts.append(f"{key}={child_preview}")
        return "{" + ", ".join(parts) + (" ..." if len(value) > 2 else "") + "}" if parts else ""
    return ""


def _short_preview(text: str, *, limit: int) -> str:
    normalized = collapse_ws(str(text))
    if not normalized:
        return ""
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)].rstrip() + "…"
