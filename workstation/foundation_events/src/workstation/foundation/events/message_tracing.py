# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections import deque
from hashlib import sha1
from threading import Lock
import json
import uuid
from typing import Any, Iterable

from semantic_text import collapse_ws


class DuplicateWorkstationMessageError(RuntimeError):
    pass


_TRACE_CACHE_LIMIT = 512
_TRACE_CACHE_LOCK = Lock()
_RECENT_TRACE_IDS: deque[str] = deque()
_RECENT_TRACE_SET: set[str] = set()


def _normalized_trace_components(components: Iterable[object]) -> tuple[str, ...]:
    values: list[str] = []
    for component in components:
        text = collapse_ws(str(component))
        if text:
            values.append(text)
    return tuple(values)


def _stable_trace_payload(payload: Any) -> str:
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
    except Exception:
        return collapse_ws(repr(payload))


def new_trace_id(prefix: str = "msg") -> str:
    normalized_prefix = collapse_ws(prefix) or "msg"
    return f"{normalized_prefix}-{uuid.uuid4().hex}"


def derived_trace_id(prefix: str, *components: object) -> str:
    normalized_prefix = collapse_ws(prefix) or "msg"
    normalized_components = _normalized_trace_components(components)
    digest = sha1("||".join(normalized_components).encode("utf-8")).hexdigest()[:20]
    return f"{normalized_prefix}-{digest}"


def event_trace_id(
    *,
    kind: str,
    session_id: str,
    root_path: str,
    payload: dict[str, Any] | None = None,
) -> str:
    return derived_trace_id(
        "event",
        kind,
        session_id,
        root_path,
        _stable_trace_payload(payload or {}),
    )


def register_message_trace(
    *,
    trace_id: str,
    parent_id: str = "",
    message_kind: str = "",
) -> tuple[str, str]:
    normalized_trace_id = collapse_ws(trace_id)
    normalized_parent_id = collapse_ws(parent_id)
    if not normalized_trace_id:
        raise ValueError("trace_id is required for workstation message tracing.")
    with _TRACE_CACHE_LOCK:
        if normalized_trace_id in _RECENT_TRACE_SET:
            label = collapse_ws(message_kind) or "workstation_message"
            raise DuplicateWorkstationMessageError(
                f"Duplicate workstation message trace detected for {label}: "
                f"trace_id={normalized_trace_id} parent_id={normalized_parent_id}"
            )
        _RECENT_TRACE_SET.add(normalized_trace_id)
        _RECENT_TRACE_IDS.append(normalized_trace_id)
        while len(_RECENT_TRACE_IDS) > _TRACE_CACHE_LIMIT:
            expired = _RECENT_TRACE_IDS.popleft()
            _RECENT_TRACE_SET.discard(expired)
    return normalized_trace_id, normalized_parent_id
