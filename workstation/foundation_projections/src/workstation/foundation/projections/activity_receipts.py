# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from typing import Any

from semantic_text import collapse_ws

from .projection_models import (
    WorkstationActivityEventView,
)


def workstation_activity_event_view(
    receipt: dict[str, Any],
    *,
    elapsed_seconds: float | None = None,
    prompt_elapsed_seconds: float | None = None,
) -> WorkstationActivityEventView | None:
    kind = collapse_ws(str(receipt.get("kind", "")))
    if kind == "user_prompt":
        return WorkstationActivityEventView(
            event_kind=kind,
            message="Prompt received",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if kind == "delegation_approval_requested":
        request = receipt.get("request", {})
        if not isinstance(request, dict):
            request = {}
        skill_title = _short_skill_title(str(request.get("skill_title", "")))
        delegated_lines = ", ".join(
            f"{item.get('capability', '')}({item.get('target', '')})"
            for item in list(request.get("requested_delegation", []))
            if isinstance(item, dict)
        ) or "additional rights"
        message = (
            f"Approval required for {skill_title}: {delegated_lines}"
            if skill_title
            else f"Approval required: {delegated_lines}"
        )
        return WorkstationActivityEventView(
            event_kind=kind,
            message=message,
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if kind == "delegation_approval_decision":
        decision = receipt.get("decision", {})
        approved = bool(decision.get("approved")) if isinstance(decision, dict) else False
        return WorkstationActivityEventView(
            event_kind=kind,
            message="Approval granted" if approved else "Approval denied",
            status="ok" if approved else "denied",
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if kind == "assistant_response":
        preview = _short_preview(str(receipt.get("assistant_text", "")), limit=72)
        return WorkstationActivityEventView(
            event_kind=kind,
            message=_with_preview("Assistant response ready", preview, label="out"),
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    if kind == "capability_call":
        capability = collapse_ws(str(receipt.get("capability", "")))
        arguments = receipt.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}
        result = receipt.get("result", {})
        if not isinstance(result, dict):
            result = {}
        phase = collapse_ws(str(receipt.get("phase", ""))).casefold()
        if phase == "started":
            return WorkstationActivityEventView(
                event_kind=kind,
                message=_capability_started_activity_message(
                    capability=capability,
                    arguments=arguments,
                ),
                capability=capability,
                status="started",
                prompt_elapsed_seconds=prompt_elapsed_seconds,
                elapsed_seconds=elapsed_seconds,
            )
        return WorkstationActivityEventView(
            event_kind=kind,
            message=_capability_finished_activity_message(
                capability=capability,
                arguments=arguments,
                result=result,
                phase=phase,
            ),
            capability=capability,
            status=collapse_ws(str(result.get("status", ""))),
            prompt_elapsed_seconds=prompt_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )
    return None


def render_workstation_activity_line(
    receipt: dict[str, Any],
    *,
    elapsed_seconds: float | None = None,
    prompt_elapsed_seconds: float | None = None,
) -> str:
    from workstation.foundation.projections import render_workstation_activity_event

    event_view = workstation_activity_event_view(
        receipt,
        elapsed_seconds=elapsed_seconds,
        prompt_elapsed_seconds=prompt_elapsed_seconds,
    )
    if event_view is None:
        return ""
    return render_workstation_activity_event(event_view)


def _capability_started_activity_message(
    *,
    capability: str,
    arguments: dict[str, Any],
) -> str:
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
        return _with_preview(f"Invoking skill: {title or 'requested skill'}", input_preview, label="in")
    if capability == "ws.skill.compose":
        input_preview = _skill_compose_input_preview(arguments)
        return _with_preview("Composing skills", input_preview, label="in")
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
    return f"Running {capability}" if capability else ""


def _capability_finished_activity_message(
    *,
    capability: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    phase: str,
) -> str:
    status = collapse_ws(str(result.get("status", ""))).casefold()
    if capability == "ws.permissions.list":
        granted = result.get("granted_capabilities", [])
        count = len(granted) if isinstance(granted, list) else 0
        return f"Permissions ready: {count} granted" if status == "ok" else "Permission listing failed"
    if capability == "ws.permissions.grant":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        return f"Granted permission: {capability_name or 'capability'}" if status == "ok" else f"Grant failed: {capability_name or 'capability'}"
    if capability == "ws.permissions.revoke":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        return f"Revoked permission: {capability_name or 'capability'}" if status == "ok" else f"Revoke failed: {capability_name or 'capability'}"
    if capability == "ws.net.http":
        method = collapse_ws(str(result.get("method", arguments.get("method", "GET")))).upper() or "GET"
        url = _short_preview(str(result.get("url", arguments.get("url", ""))), limit=72)
        prefix = f"HTTP {method} ok" if status == "ok" else f"HTTP {method} failed"
        return _with_preview(prefix, _net_http_output_preview(result, fallback=url), label="out")
    if capability == "ws.skill.import":
        imported_count = int(result.get("imported_count", 0) or 0)
        if status == "ok":
            return _with_preview(
                f"Imported {imported_count} skill{'s' if imported_count != 1 else ''}",
                _imported_skills_preview(result),
                label="out",
            )
        return "Skill import failed"
    if capability == "ws.skill.catalog":
        returned = int(result.get("returned_skill_count", 0) or 0)
        return f"Listed {returned} skill{'s' if returned != 1 else ''}" if status == "ok" else "Skill listing failed"
    if capability == "ws.skill.describe":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        return f"Described skill: {title or 'skill'}" if status == "ok" else f"Describe failed for {title or 'skill'}"
    if capability == "ws.skill.export":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "ok":
            return _with_preview(
                f"Exported {title or 'skill'}",
                _display_path(str(result.get("destination_path", ""))),
                label="out",
            )
        return f"Export failed for {title or 'skill'}"
    if capability == "ws.skill.permissions":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        return f"Permissions ready: {title or 'skill'}" if status == "ok" else f"Permissions failed for {title or 'skill'}"
    if capability == "ws.skill.invoke":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "approval_required":
            return f"Waiting for approval: {title or 'skill'}"
        if phase == "after_escalation" and status == "ok":
            return _with_preview(f"Skill completed after approval: {title or 'skill'}", _skill_output_preview(result), label="out")
        if status == "ok":
            return _with_preview(f"Skill completed: {title or 'skill'}", _skill_output_preview(result), label="out")
        return _with_preview(f"Skill failed: {title or 'skill'}", _skill_error_preview(result), label="out")
    if capability == "ws.skill.compose":
        if status == "approval_required":
            title = _short_skill_title(str(result.get("blocked_skill_title", "")))
            return f"Waiting for approval: {title or 'skill composition'}"
        output_preview = _skill_compose_output_preview(result)
        if status == "ok":
            return _with_preview("Skill composition completed", output_preview, label="out")
        return _with_preview("Skill composition failed", output_preview or _skill_error_preview(result), label="out")
    if capability == "ws.repo.search":
        match_count = int(result.get("match_count", 0) or 0)
        if status == "ok":
            return _with_preview(
                f"Search completed: {match_count} match{'es' if match_count != 1 else ''}",
                _search_output_preview(result),
                label="out",
            )
        return "Search failed"
    if capability == "ws.repo.tree":
        if status == "ok":
            tree = result.get("tree", [])
            count = len(tree) if isinstance(tree, list) else 0
            return _with_preview(
                f"Listed {count} entr{'ies' if count != 1 else 'y'}",
                _first_list_item_preview(tree),
                label="out",
            )
        return "Listing failed"
    if capability == "ws.fs.read":
        if status == "ok":
            return _with_preview(
                f"Read {_display_path(str(result.get('path', arguments.get('path', ''))))}",
                _content_preview(str(result.get("content", ""))),
                label="out",
            )
        return "Read failed"
    if capability == "ws.process.run":
        exit_code = result.get("exit_code")
        prefix = "Command completed" if exit_code in {0, "0"} else "Command failed"
        return _with_preview(prefix, _process_output_preview(result), label="out")
    if capability:
        if status == "ok":
            return f"Completed {capability}"
        if status:
            return f"{capability} {status}"
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


def _with_preview(text: str, preview: str, *, label: str) -> str:
    if not preview:
        return text
    return f"{text} [{label}: {preview}]"


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
    return _short_preview(collapse_ws(str(arguments.get("semantic_unit", ""))), limit=64)


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
    return blocked or ""


def _skill_error_preview(result: dict[str, Any]) -> str:
    for key in ("stderr", "error", "answer"):
        preview = _short_preview(str(result.get(key, "")), limit=72)
        if preview:
            return preview
    return ""


def _search_output_preview(result: dict[str, Any]) -> str:
    return _first_list_item_preview(result.get("matches", []))


def _process_output_preview(result: dict[str, Any]) -> str:
    stdout = _short_preview(str(result.get("stdout", "")), limit=72)
    if stdout:
        return stdout
    return _short_preview(str(result.get("stderr", "")), limit=72)


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
        parts = [
            _short_preview(str(item), limit=16)
            for item in value[:2]
            if _short_preview(str(item), limit=16)
        ]
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


__all__ = [
    "render_workstation_activity_line",
    "workstation_activity_event_view",
]
