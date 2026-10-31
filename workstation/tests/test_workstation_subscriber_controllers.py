# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from workstation.app.cli.composition import ensure_workstation_application_composition
from workstation.foundation.events.event_bus import _reset_workstation_event_bus_registry_for_tests, publish_workstation_event
from workstation.foundation.projections import WorkstationActivityEventView
from workstation.runtime.core.projection_subscriber_controller import WorkstationProjectionSubscriberController
from workstation.runtime.core.session import launch_workstation_session


class WorkstationSubscriberControllersTests(unittest.TestCase):
    def setUp(self) -> None:
        ensure_workstation_application_composition()
        _reset_workstation_event_bus_registry_for_tests()
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Test workstation subscriber controllers.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_projection_controller_captures_live_blend_activity_and_invalidation(self) -> None:
        controller = WorkstationProjectionSubscriberController(root_path=self.root, activity_limit=5)
        activity_lines: list[str] = []
        context_invalidations: list[str] = []
        projection_invalidations: list[str] = []
        controller.start(
            on_activity_line=lambda line: activity_lines.append(line),
            on_context_invalidated=lambda: context_invalidations.append("context"),
            on_projection_invalidated=lambda: projection_invalidations.append("projection"),
        )
        publish_workstation_event(
            root_path=self.root,
            session_id="ws_demo",
            event_kind="blend_step_started",
            payload={
                "workflow_execution_id": "bwf_exec_demo",
                "step_id": "emit",
                "operator_name": "Emit Text",
                "status": "started",
                "payload": {"input_payload": {"text": "hello"}},
            },
        )
        publish_workstation_event(
            root_path=self.root,
            session_id="ws_demo",
            event_kind="permissions_changed",
            payload={"added_capabilities": ["ws.net.http"], "removed_capabilities": []},
        )
        controller.stop()
        self.assertTrue(any("Step started: Emit Text" in line for line in activity_lines))
        self.assertEqual(len(controller.supplemental_activity_events()), 1)
        self.assertIsInstance(controller.supplemental_activity_events()[0], WorkstationActivityEventView)
        self.assertEqual(context_invalidations, ["context"])
        self.assertGreaterEqual(len(projection_invalidations), 2)


if __name__ == "__main__":
    unittest.main()
