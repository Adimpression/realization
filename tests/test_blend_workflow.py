import json
import tempfile
import unittest
from pathlib import Path

from realized_blend_application.workflows import (
    BlendWorkflowPlan,
    blend_workflow_plan_from_skill_compose_arguments,
    blend_workflow_run_from_skill_compose_result,
    load_blend_workflow_plan,
    load_blend_workflow_run,
    persist_blend_workflow_objects,
    skill_compose_arguments_from_blend_workflow_plan,
)


class BlendWorkflowTests(unittest.TestCase):
    def test_blend_workflow_plan_round_trips_from_skill_compose_arguments(self) -> None:
        arguments = {
            "target": "skills",
            "steps": [
                {
                    "step_id": "step_1",
                    "skill_title": "Emit Text",
                    "semantic_unit": "Emit text",
                    "bindings": [
                        {
                            "target_region": "a",
                            "target_path": "/a/text",
                            "source_root_name": "step_1_text",
                            "source_root_region": "a",
                        }
                    ],
                },
                {
                    "step_id": "step_2",
                    "skill_title": "Consume Text",
                    "bindings": [
                        {
                            "target_region": "a",
                            "target_path": "/a/text",
                            "source_step_id": "step_1",
                            "source_region": "d",
                            "source_path": "/d/text",
                            "mapper": {"kind": "identity"},
                        }
                    ],
                    "run_if": [
                        {
                            "source_step_id": "step_1",
                            "source_region": "d",
                            "source_path": "/d/status",
                            "operator": "equals",
                            "expected_value": "ok",
                        }
                    ],
                    "branch_label": "if",
                },
            ],
            "root_inputs": {"step_1_text": "hello"},
            "final_output_step": "step_2",
        }
        plan = blend_workflow_plan_from_skill_compose_arguments(arguments)
        self.assertEqual(plan.workflow_kind, "skill_compose")
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].operator_name, "Emit Text")
        self.assertEqual(plan.steps[1].branch_label, "if")
        self.assertEqual(skill_compose_arguments_from_blend_workflow_plan(plan), arguments)
        self.assertEqual(BlendWorkflowPlan.from_dict(plan.to_dict()), plan)

    def test_blend_workflow_run_projection_wraps_skill_compose_result(self) -> None:
        plan = blend_workflow_plan_from_skill_compose_arguments(
            {
                "steps": [{"step_id": "step_1", "skill_title": "Emit Text"}],
                "final_output_step": "step_1",
            }
        )
        result = {
            "status": "ok",
            "capability": "ws.skill.compose",
            "target": "skills",
            "requested_skill_titles": ["Emit Text"],
            "plan_authorities": ["execute"],
            "final_output_step": "step_1",
            "final_output": {"text": "hello"},
            "final_outputs_by_step": {"step_1": {"text": "hello"}},
            "steps": [{"step_id": "step_1", "status": "ok"}],
        }
        run = blend_workflow_run_from_skill_compose_result(plan=plan, result=result)
        self.assertEqual(run.status, "ok")
        self.assertEqual(run.final_output_step, "step_1")
        self.assertEqual(run.final_output, {"text": "hello"})
        self.assertEqual(run.metadata["capability"], "ws.skill.compose")
        self.assertEqual(run.metadata["requested_skill_titles"], ["Emit Text"])

    def test_persist_blend_workflow_objects_writes_plan_run_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws-root"
            root.mkdir(parents=True, exist_ok=True)
            plan = blend_workflow_plan_from_skill_compose_arguments(
                {
                    "steps": [
                        {"step_id": "emit", "skill_title": "Emit Text"},
                        {"step_id": "consume", "skill_title": "Consume Text"},
                    ],
                    "final_output_step": "consume",
                }
            )
            run = blend_workflow_run_from_skill_compose_result(
                plan=plan,
                result={
                    "status": "ok",
                    "capability": "ws.skill.compose",
                    "target": "skills",
                    "requested_skill_titles": ["Emit Text", "Consume Text"],
                    "plan_authorities": ["execute"],
                    "final_output_step": "consume",
                    "final_output": {"result": "done"},
                    "final_outputs_by_step": {"consume": {"result": "done"}},
                    "steps": [{"step_id": "emit", "status": "ok"}, {"step_id": "consume", "status": "ok"}],
                },
            )
            persisted_plan, persisted_run, refs = persist_blend_workflow_objects(
                root_path=root,
                plan=plan,
                run=run,
                session_id="ws_demo",
            )
            self.assertTrue(refs["workflow_id"].startswith("bwf_plan_"))
            self.assertTrue(refs["workflow_run_id"].startswith("bwf_run_"))
            self.assertTrue(Path(refs["plan_path"]).exists())
            self.assertTrue(Path(refs["run_path"]).exists())
            self.assertTrue(Path(refs["index_path"]).exists())
            self.assertEqual(load_blend_workflow_plan(root, persisted_plan.workflow_id), persisted_plan)
            self.assertEqual(load_blend_workflow_run(root, persisted_run.workflow_run_id), persisted_run)
            index_payload = json.loads(Path(refs["index_path"]).read_text())
            self.assertEqual(index_payload["latest_plan_id"], persisted_plan.workflow_id)
            self.assertEqual(index_payload["latest_run_id"], persisted_run.workflow_run_id)
            self.assertEqual(index_payload["plans"][0]["workflow_id"], persisted_plan.workflow_id)
            self.assertEqual(index_payload["runs"][0]["workflow_run_id"], persisted_run.workflow_run_id)


if __name__ == "__main__":
    unittest.main()
