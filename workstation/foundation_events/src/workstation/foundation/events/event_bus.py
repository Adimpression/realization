# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from host_interaction_receipts import append_host_interaction_receipt
from semantic_text import collapse_ws
from workstation.contracts.events import WorkstationEvent
from workstation.foundation.events.message_tracing import event_trace_id

try:
    from blinker import Namespace as _BlinkerNamespace
except Exception:  # pragma: no cover - optional dependency
    _BlinkerNamespace = None


def _workstation_event_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkstationEventBus:
    def __init__(self, root_path: Path) -> None:
        self.root_path = str(Path(root_path).expanduser().resolve())
        self._namespace = _BlinkerNamespace() if _BlinkerNamespace is not None else None
        self._fallback_handlers: dict[str, list[Callable[[WorkstationEvent], None]]] = {}

    def subscribe(
        self,
        event_kind: str,
        handler: Callable[[WorkstationEvent], None],
    ) -> Callable[[], None]:
        normalized_kind = collapse_ws(str(event_kind)) or "*"
        if self._namespace is not None:
            signal = self._namespace.signal(normalized_kind)

            def _receiver(_sender: Any, *, event: WorkstationEvent) -> None:
                handler(event)

            signal.connect(_receiver, sender=self.root_path, weak=False)

            def _unsubscribe() -> None:
                signal.disconnect(_receiver, sender=self.root_path)

            return _unsubscribe
        handlers = self._fallback_handlers.setdefault(normalized_kind, [])
        handlers.append(handler)

        def _unsubscribe() -> None:
            current = self._fallback_handlers.get(normalized_kind, [])
            if handler in current:
                current.remove(handler)
            if not current:
                self._fallback_handlers.pop(normalized_kind, None)

        return _unsubscribe

    def publish(self, event: WorkstationEvent) -> None:
        if not collapse_ws(event.trace_id):
            event = replace(
                event,
                trace_id=event_trace_id(
                    kind=event.kind,
                    session_id=event.session_id,
                    root_path=event.root_path,
                    payload=event.payload,
                ),
            )
        for event_kind in (collapse_ws(event.kind), "*"):
            if not event_kind:
                continue
            if self._namespace is not None:
                signal = self._namespace.signal(event_kind)
                for receiver in list(signal.receivers_for(self.root_path)):
                    try:
                        receiver(self.root_path, event=event)
                    except Exception:
                        continue
                continue
            for handler in list(self._fallback_handlers.get(event_kind, [])):
                try:
                    handler(event)
                except Exception:
                    continue


_WORKSTATION_EVENT_BUSES: dict[str, WorkstationEventBus] = {}


def workstation_event_bus(root_path: Path) -> WorkstationEventBus:
    root = str(Path(root_path).expanduser().resolve())
    bus = _WORKSTATION_EVENT_BUSES.get(root)
    if bus is None:
        bus = WorkstationEventBus(Path(root))
        _WORKSTATION_EVENT_BUSES[root] = bus
    return bus


def publish_workstation_event(
    *,
    root_path: Path,
    session_id: str,
    event_kind: str,
    payload: dict[str, Any] | None = None,
    timestamp: str = "",
    trace_id: str = "",
    parent_id: str = "",
) -> WorkstationEvent:
    event = WorkstationEvent(
        kind=collapse_ws(str(event_kind)),
        session_id=collapse_ws(str(session_id)),
        root_path=str(Path(root_path).expanduser().resolve()),
        timestamp=collapse_ws(str(timestamp)) or _workstation_event_timestamp(),
        payload=dict(payload or {}),
        trace_id=collapse_ws(trace_id),
        parent_id=collapse_ws(parent_id),
    )
    workstation_event_bus(root_path).publish(event)
    return event


def append_workstation_receipt_and_publish(
    *,
    root_path: Path,
    session_id: str,
    receipt: dict[str, Any],
) -> None:
    root = Path(root_path).expanduser().resolve()
    append_host_interaction_receipt(root, receipt)
    for event in _workstation_events_from_receipt(
        root_path=root,
        session_id=session_id,
        receipt=receipt,
    ):
        workstation_event_bus(root).publish(event)


def _workstation_events_from_receipt(
    *,
    root_path: Path,
    session_id: str,
    receipt: dict[str, Any],
) -> tuple[WorkstationEvent, ...]:
    receipt_kind = collapse_ws(str(receipt.get("kind", "")))
    timestamp = collapse_ws(str(receipt.get("timestamp", ""))) or _workstation_event_timestamp()
    activity_payload = _activity_event_payload(receipt_kind=receipt_kind, receipt=receipt)
    events: list[WorkstationEvent] = []
    if activity_payload is not None:
        events.append(
            WorkstationEvent(
                kind="activity_event",
                session_id=collapse_ws(str(session_id)),
                root_path=str(root_path),
                timestamp=timestamp,
                payload=activity_payload,
            )
        )
    if receipt_kind == "assistant_response":
        events.append(
            WorkstationEvent(
                kind="assistant_response_changed",
                session_id=collapse_ws(str(session_id)),
                root_path=str(root_path),
                timestamp=timestamp,
                payload={
                    "model": collapse_ws(str(receipt.get("model", ""))),
                    "rounds": int(receipt.get("rounds", 0) or 0),
                    "tool_calls": int(receipt.get("tool_calls", 0) or 0),
                    "requested_skill": collapse_ws(str(receipt.get("requested_skill", ""))),
                    "fulfilled_by": collapse_ws(str(receipt.get("fulfilled_by", ""))),
                    "fallback_used": bool(receipt.get("fallback_used")) if "fallback_used" in receipt else None,
                },
            )
        )
    if receipt_kind == "delegation_approval_requested":
        events.append(
            WorkstationEvent(
                kind="approval_requested",
                session_id=collapse_ws(str(session_id)),
                root_path=str(root_path),
                timestamp=timestamp,
                payload={"request": dict(receipt.get("request", {})) if isinstance(receipt.get("request", {}), dict) else {}},
            )
        )
    if receipt_kind == "delegation_approval_decision":
        payload: dict[str, Any] = {}
        if isinstance(receipt.get("request", {}), dict):
            payload["request"] = dict(receipt.get("request", {}))
        if isinstance(receipt.get("decision", {}), dict):
            payload["decision"] = dict(receipt.get("decision", {}))
        events.append(
            WorkstationEvent(
                kind="approval_decided",
                session_id=collapse_ws(str(session_id)),
                root_path=str(root_path),
                timestamp=timestamp,
                payload=payload,
            )
        )
    return tuple(events)


def _activity_event_payload(*, receipt_kind: str, receipt: dict[str, Any]) -> dict[str, Any] | None:
    if receipt_kind == "user_prompt":
        return {
            "receipt_kind": receipt_kind,
            "prompt": collapse_ws(str(receipt.get("prompt", ""))),
        }
    if receipt_kind == "capability_call":
        result = receipt.get("result", {})
        if not isinstance(result, dict):
            result = {}
        return {
            "receipt_kind": receipt_kind,
            "capability": collapse_ws(str(receipt.get("capability", ""))),
            "phase": collapse_ws(str(receipt.get("phase", ""))),
            "status": collapse_ws(str(result.get("status", ""))),
        }
    if receipt_kind == "assistant_response":
        return {
            "receipt_kind": receipt_kind,
            "model": collapse_ws(str(receipt.get("model", ""))),
            "fulfilled_by": collapse_ws(str(receipt.get("fulfilled_by", ""))),
        }
    if receipt_kind == "delegation_approval_requested":
        request = receipt.get("request", {})
        if not isinstance(request, dict):
            request = {}
        return {
            "receipt_kind": receipt_kind,
            "capability": collapse_ws(str(request.get("capability", ""))),
            "skill_title": collapse_ws(str(request.get("skill_title", ""))),
        }
    if receipt_kind == "delegation_approval_decision":
        decision = receipt.get("decision", {})
        if not isinstance(decision, dict):
            decision = {}
        return {
            "receipt_kind": receipt_kind,
            "approved": bool(decision.get("approved")),
        }
    return None


def _reset_workstation_event_bus_registry_for_tests() -> None:
    _WORKSTATION_EVENT_BUSES.clear()
