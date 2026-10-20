# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from blend_workflow import (
    BlendWorkflowBinding,
    BlendWorkflowPlan,
    BlendWorkflowRun,
    BlendWorkflowStep,
)
from workstation.models import WorkstationSession
from workstation.projection_models import (
    render_workstation_permission_panel,
    split_rendered_workstation_activity_line,
    workstation_permission_panel_view,
    workstation_workflow_graph_view,
)


class WorkstationProjectionModelTests(unittest.TestCase):
    def test_permission_panel_view_projects_session_grants_and_usage(self) -> None:
        session = WorkstationSession(
            session_id="ws-1",
            root_path="/tmp/ws",
            created_at="2026-04-06T00:00:00+00:00",
            attachments=(),
            allowed_capabilities=("ws.skill.catalog", "ws.repo.tree"),
            openai_profile=None,
            openai_env_var=None,
            initial_task="",
        )
        view = workstation_permission_panel_view(
            session=session,
            available_capabilities=("ws.skill.catalog", "ws.repo.tree", "ws.repo.search", "ws.net.http"),
            protected_capabilities=("ws.skill.catalog",),
        )
        rendered = render_workstation_permission_panel(view)
        self.assertEqual(view.granted_capabilities, ("ws.skill.catalog", "ws.repo.tree"))
        self.assertEqual(view.ungranted_capabilities, ("ws.repo.search", "ws.net.http"))
        self.assertEqual(view.revocable_capabilities, ("ws.repo.tree",))
        self.assertIn("Granted session capabilities:", rendered)
        self.assertIn("ws.net.http", rendered)
        self.assertIn("/grant-permission <capability>", rendered)

    def test_workflow_graph_view_projects_root_step_and_binding_edges(self) -> None:
        workflow_plan = BlendWorkflowPlan(
            workflow_id="wf-1",
            workflow_kind="skill_compose",
            session_id="ws-1",
            created_at="2026-04-06T00:00:00+00:00",
            root_inputs={"text": "hello"},
            final_output_step="consume",
            steps=(
                BlendWorkflowStep(
                    step_id="emit",
                    operator_kind="skill",
                    operator_name="Emit Text",
                    bindings=(
                        BlendWorkflowBinding(
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_path": "/root/text",
                                "mapper": {"kind": "identity"},
                            }
                        ),
                    ),
                ),
                BlendWorkflowStep(
                    step_id="consume",
                    operator_kind="skill",
                    operator_name="Consume Text",
                    bindings=(
                        BlendWorkflowBinding(
                            {
                                "target_region": "a",
                                "target_path": "/a/text",
                                "source_step_id": "emit",
                                "source_region": "d",
                                "source_path": "/d/text",
                                "mapper": {"kind": "project_field"},
                            }
                        ),
                    ),
                ),
            ),
        )
        workflow_run = BlendWorkflowRun(
            workflow_run_id="run-1",
            workflow_id="wf-1",
            plan=workflow_plan,
            status="ok",
            session_id="ws-1",
            started_at="2026-04-06T00:00:01+00:00",
            finished_at="2026-04-06T00:00:02+00:00",
            final_output_step="consume",
            final_output="done",
            final_outputs_by_step={"emit": "hello", "consume": "done"},
            steps=[
                {"step_id": "emit", "status": "ok"},
                {"step_id": "consume", "status": "ok"},
            ],
            plan_authorities=["read", "write"],
        )
        view = workstation_workflow_graph_view(
            workflow_plan=workflow_plan,
            workflow_run=workflow_run,
        )
        payload = view.to_dict()
        self.assertEqual(view.workflow_id, "wf-1")
        self.assertEqual(view.workflow_run_id, "run-1")
        self.assertEqual(view.status, "ok")
        self.assertEqual(view.final_output_step, "consume")
        self.assertTrue(any(item["node_id"] == "__root__" for item in payload["nodes"]))
        self.assertTrue(any(item["is_final_output"] for item in payload["nodes"]))
        self.assertTrue(
            any(
                item["source_node_id"] == "emit"
                and item["target_node_id"] == "consume"
                and item["mapper_kind"] == "project_field"
                for item in payload["edges"]
            )
        )

    def test_split_rendered_workstation_activity_line_preserves_sections(self) -> None:
        prefix, main, sections, timing = split_rendered_workstation_activity_line(
            "├─ Step completed: Demo Skill [out: ok] [review] (t+1.2s, op ~0.4s)"
        )
        self.assertEqual(prefix, "├─ ")
        self.assertEqual(main, "Step completed: Demo Skill")
        self.assertEqual(sections, ("[out: ok]", "[review]"))
        self.assertEqual(timing, "(t+1.2s, op ~0.4s)")
