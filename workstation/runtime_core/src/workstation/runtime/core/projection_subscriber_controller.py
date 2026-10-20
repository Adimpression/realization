# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from semantic_text import collapse_ws
from workstation.contracts.events import WorkstationEvent
from workstation.foundation.events.event_bus import workstation_event_bus
from workstation.foundation.projections import WorkstationActivityEventView, render_workstation_activity_event
from workstation.runtime.core.workstation_core import workstation_activity_event_view_from_event


_CONTEXT_INVALIDATION_EVENT_KINDS = {
    "assistant_response_changed",
    "permissions_changed",
    "session_changed",
    "skill_catalog_changed",
}

_LIVE_ACTIVITY_EVENT_KINDS = {
    "blend_workflow_started",
    "blend_step_started",
    "blend_step_skipped",
    "blend_step_blocked",
    "blend_step_completed",
    "blend_step_failed",
    "blend_workflow_completed",
    "blend_workflow_failed",
    "blend_workflow_persisted",
}

_DASHBOARD_REBUILD_EVENT_KINDS = _CONTEXT_INVALIDATION_EVENT_KINDS | _LIVE_ACTIVITY_EVENT_KINDS | {
    "approval_requested",
    "approval_decided",
    "turn_finished",
}


@dataclass
class WorkstationProjectionSubscriberController:
    root_path: Path
    activity_limit: int = 30
    _unsubscribe: Callable[[], None] | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _live_activity_events: list[WorkstationActivityEventView] = field(default_factory=list)

    def start(
        self,
        *,
        on_activity_line: Callable[[str], None] | None = None,
        on_context_invalidated: Callable[[], None] | None = None,
        on_projection_invalidated: Callable[[], None] | None = None,
    ) -> None:
        self.stop()

        def _handle(event: WorkstationEvent) -> None:
            normalized_kind = collapse_ws(str(event.kind))
            if normalized_kind in _LIVE_ACTIVITY_EVENT_KINDS:
                self._handle_live_activity_event(event, on_activity_line=on_activity_line)
            if normalized_kind in _CONTEXT_INVALIDATION_EVENT_KINDS and on_context_invalidated is not None:
                try:
                    on_context_invalidated()
                except Exception:
                    pass
            if normalized_kind in _DASHBOARD_REBUILD_EVENT_KINDS and on_projection_invalidated is not None:
                try:
                    on_projection_invalidated()
                except Exception:
                    pass

        self._unsubscribe = workstation_event_bus(Path(self.root_path)).subscribe("*", _handle)

    def stop(self) -> None:
        unsubscribe = self._unsubscribe
        self._unsubscribe = None
        if unsubscribe is not None:
            try:
                unsubscribe()
            except Exception:
                pass

    def supplemental_activity_events(self) -> tuple[WorkstationActivityEventView, ...]:
        with self._lock:
            return tuple(self._live_activity_events)

    def _handle_live_activity_event(
        self,
        event: WorkstationEvent,
        *,
        on_activity_line: Callable[[str], None] | None,
    ) -> None:
        event_view = workstation_activity_event_view_from_event(
            event_kind=event.kind,
            payload=event.payload,
        )
        if event_view is None:
            return
        with self._lock:
            self._live_activity_events.append(event_view)
            self._live_activity_events = self._live_activity_events[-max(1, int(self.activity_limit)) :]
        if on_activity_line is not None:
            rendered = render_workstation_activity_event(event_view)
            if rendered:
                try:
                    on_activity_line(rendered)
                except Exception:
                    pass


WorkstationProjectionSubscriberController.__module__ = (
    "workstation.foundation.events.subscriber_controllers"
)

__all__ = ["WorkstationProjectionSubscriberController"]
