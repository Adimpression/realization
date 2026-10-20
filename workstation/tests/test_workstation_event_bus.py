# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from host_interaction_receipts import (
    host_interaction_assistant_response_receipt,
    host_interaction_delegation_approval_decision_receipt,
    host_interaction_user_prompt_receipt,
)
from workstation.runtime.core.capabilities import execute_workstation_capability
from workstation.foundation.events.event_bus import (
    _reset_workstation_event_bus_registry_for_tests,
    append_workstation_receipt_and_publish,
    publish_workstation_event,
    workstation_event_bus,
)
from workstation.runtime.core.session import launch_workstation_session, load_workstation_session, prompt_workstation_session
from workstation.runtime.core.workstation_core import workstation_change_session_capabilities


class WorkstationEventBusTests(unittest.TestCase):
    def setUp(self) -> None:
        _reset_workstation_event_bus_registry_for_tests()
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.other_root = Path(self.tempdir.name) / "other-root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        self.skills_sqlite = Path(self.tempdir.name) / "skills.sqlite3"
        (self.workspace / "trials").mkdir(parents=True, exist_ok=True)
        (self.workspace / "trials" / "demo.skill.yaml").write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Demo Imported Skill",
                    "answer: hello from imported skill",
                ]
            )
            + "\n"
        )
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Test workstation event bus.",
        )
        launch_workstation_session(
            root_path=self.other_root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Other workstation.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_event_bus_is_session_scoped_and_subscriber_isolated(self) -> None:
        received: list[str] = []
        other_received: list[str] = []
        bus = workstation_event_bus(self.root)
        other_bus = workstation_event_bus(self.other_root)
        bus.subscribe("activity_event", lambda event: received.append(event.kind))

        def _boom(_event) -> None:
            raise RuntimeError("ignore me")

        bus.subscribe("activity_event", _boom)
        other_bus.subscribe("activity_event", lambda event: other_received.append(event.kind))

        publish_workstation_event(
            root_path=self.root,
            session_id="ws_1",
            event_kind="activity_event",
            payload={"receipt_kind": "user_prompt"},
        )
        self.assertEqual(received, ["activity_event"])
        self.assertEqual(other_received, [])

    def test_append_receipt_and_publish_derives_activity_and_response_events(self) -> None:
        session = load_workstation_session(self.root)
        seen: list[str] = []
        bus = workstation_event_bus(self.root)
        bus.subscribe("*", lambda event: seen.append(event.kind))

        append_workstation_receipt_and_publish(
            root_path=self.root,
            session_id=session.session_id,
            receipt=host_interaction_user_prompt_receipt(
                prompt="List skills.",
                task_contract={"semantic_unit": "List skills."},
            ),
        )
        append_workstation_receipt_and_publish(
            root_path=self.root,
            session_id=session.session_id,
            receipt=host_interaction_assistant_response_receipt(
                assistant_text="Done.",
                model="workstation-shell-command",
                rounds=0,
                tool_calls=0,
                fulfilled_by="ws.skill.catalog",
                fallback_used=False,
            ),
        )
        append_workstation_receipt_and_publish(
            root_path=self.root,
            session_id=session.session_id,
            receipt=host_interaction_delegation_approval_decision_receipt(
                request={"capability": "ws.skill.invoke"},
                decision={"approved": True, "scope": "one_invocation"},
            ),
        )
        self.assertEqual(
            seen,
            [
                "activity_event",
                "activity_event",
                "assistant_response_changed",
                "activity_event",
                "approval_decided",
            ],
        )

    def test_permission_mutation_publishes_session_and_permission_events(self) -> None:
        session = load_workstation_session(self.root)
        seen: list[tuple[str, dict]] = []
        bus = workstation_event_bus(self.root)
        bus.subscribe("*", lambda event: seen.append((event.kind, dict(event.payload))))
        workstation_change_session_capabilities(
            root=self.root,
            session=session,
            added_capabilities=["ws.net.http"],
            removed_capabilities=["ws.process.run"],
        )
        kinds = [kind for kind, _payload in seen]
        self.assertIn("session_changed", kinds)
        self.assertIn("permissions_changed", kinds)
        permissions_payload = next(payload for kind, payload in seen if kind == "permissions_changed")
        self.assertIn("ws.net.http", permissions_payload["added_capabilities"])
        self.assertIn("ws.process.run", permissions_payload["removed_capabilities"])

    def test_skill_import_and_export_publish_catalog_events(self) -> None:
        session = load_workstation_session(self.root)
        seen: list[tuple[str, dict]] = []
        bus = workstation_event_bus(self.root)
        bus.subscribe("*", lambda event: seen.append((event.kind, dict(event.payload))))
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {"target": "skills", "source_target": "main", "path": "trials/demo.skill.yaml"},
        )
        self.assertEqual(import_result["status"], "ok")
        export_result = execute_workstation_capability(
            session,
            "ws.skill.export",
            {"target": "skills", "skill_title": "Demo Imported Skill"},
        )
        self.assertEqual(export_result["status"], "ok")
        kinds = [kind for kind, _payload in seen]
        self.assertIn("skill_import_completed", kinds)
        self.assertIn("skill_export_completed", kinds)
        self.assertGreaterEqual(kinds.count("skill_catalog_changed"), 2)

    def test_prompt_session_publishes_turn_lifecycle_events(self) -> None:
        seen: list[tuple[str, dict]] = []
        bus = workstation_event_bus(self.root)
        bus.subscribe("*", lambda event: seen.append((event.kind, dict(event.payload))))
        report = prompt_workstation_session(
            root_path=self.root,
            prompt="Import the skill file at trials/demo.skill.yaml into this workstation.",
            model=None,
            max_tool_rounds=4,
        )
        self.assertIn("Import status: ok", report["assistant_text"])
        kinds = [kind for kind, _payload in seen]
        self.assertIn("turn_started", kinds)
        self.assertIn("turn_finished", kinds)
        finished_payload = next(payload for kind, payload in seen if kind == "turn_finished")
        self.assertEqual(finished_payload["fulfilled_by"], "ws.skill.import")

    def test_workflow_run_publishes_blend_step_lifecycle_events(self) -> None:
        seen: list[tuple[str, dict]] = []
        bus = workstation_event_bus(self.root)
        bus.subscribe("*", lambda event: seen.append((event.kind, dict(event.payload))))
        session = workstation_change_session_capabilities(
            root=self.root,
            session=load_workstation_session(self.root),
            added_capabilities=["ws.workflow.run"],
            removed_capabilities=[],
        )
        workflow_plan = {
            "workflow_kind": "workflow",
            "steps": [
                {
                    "step_id": "read_file",
                    "operator_kind": "capability",
                    "operator_name": "ws.fs.read",
                    "bindings": [
                        {
                            "target_region": "a",
                            "target_path": "/a/path",
                            "source_root_name": "path",
                            "source_root_region": "a",
                        }
                    ],
                    "metadata": {"target": "main"},
                }
            ],
            "root_inputs": {"path": "trials/demo.skill.yaml"},
            "final_output_step": "read_file",
            "metadata": {"target": "skills"},
        }
        result = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {"workflow_plan": workflow_plan},
        )
        self.assertEqual(result["status"], "ok")
        kinds = [kind for kind, _payload in seen]
        lifecycle_kinds = [
            kind
            for kind in kinds
            if kind
            in {
                "blend_workflow_started",
                "blend_step_started",
                "blend_step_completed",
                "blend_workflow_completed",
                "blend_workflow_persisted",
            }
        ]
        self.assertEqual(
            lifecycle_kinds,
            [
                "blend_workflow_started",
                "blend_step_started",
                "blend_step_completed",
                "blend_workflow_completed",
                "blend_workflow_persisted",
            ],
        )
        execution_ids = {
            payload.get("workflow_execution_id")
            for kind, payload in seen
            if kind.startswith("blend_")
        }
        self.assertEqual(len(execution_ids), 1)
        persisted_payload = next(payload for kind, payload in seen if kind == "blend_workflow_persisted")
        self.assertEqual(persisted_payload["workflow_run_id"], result["workflow_run_id"])


if __name__ == "__main__":
    unittest.main()
