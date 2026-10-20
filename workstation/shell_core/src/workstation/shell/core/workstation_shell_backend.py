# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workstation.runtime.core.capabilities import AVAILABLE_WORKSTATION_CAPABILITIES
from workstation.foundation.projections import (
    WorkstationActivityEventView,
    render_workstation_activity_feed,
    render_workstation_permission_panel,
    render_workstation_skill_catalog,
)
from workstation.runtime.core.session import load_workstation_session
from workstation.runtime.core.workstation_core import (
    workstation_permission_panel_for_session,
    workstation_recent_activity_feed,
    workstation_skill_catalog_for_session,
)


@dataclass(frozen=True)
class WorkstationShellProjectionBackend:
    protected_capabilities: tuple[str, ...] = (
        "ws.skill.catalog",
        "ws.skill.import",
        "ws.skill.export",
    )

    def activity_text(
        self,
        *,
        root_path: Path,
        limit: int,
        supplemental_events: tuple[WorkstationActivityEventView, ...] = (),
        fallback_lines: tuple[str, ...] = (),
    ) -> str:
        feed = workstation_recent_activity_feed(
            root_path=Path(root_path).expanduser().resolve(),
            limit=limit,
            supplemental_events=supplemental_events,
        )
        if feed.events:
            return render_workstation_activity_feed(feed)
        if not fallback_lines:
            return "No activity yet."
        return "\n".join(f"activity {line}" for line in fallback_lines)

    def permissions_text(self, *, root_path: Path) -> str:
        session = load_workstation_session(Path(root_path).expanduser().resolve())
        return render_workstation_permission_panel(
            workstation_permission_panel_for_session(
                session=session,
                available_capabilities=AVAILABLE_WORKSTATION_CAPABILITIES,
                protected_capabilities=self.protected_capabilities,
            )
        )

    def skills_text(self, *, root_path: Path) -> str:
        session = load_workstation_session(Path(root_path).expanduser().resolve())
        return render_workstation_skill_catalog(
            workstation_skill_catalog_for_session(
                session=session,
            )
        )
