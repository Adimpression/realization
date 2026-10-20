import tempfile
import unittest
from pathlib import Path

from blend_workflow import (
    blend_workflow_plan_from_skill_compose_arguments,
    blend_workflow_run_from_skill_compose_result,
)
from blend_workflow_store import (
    ensure_blend_workflow_store,
    list_blend_workflow_runs_for_plan,
    list_blend_workflow_summaries,
    load_blend_workflow_index,
    persist_blend_workflow_objects,
)


class BlendWorkflowStoreTests(unittest.TestCase):
    def test_ensure_blend_workflow_store_bootstraps_empty_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            refs = ensure_blend_workflow_store(root)
            self.assertTrue(refs["plans"].exists())
            self.assertTrue(refs["runs"].exists())
            self.assertTrue(refs["index"].exists())
            self.assertEqual(
                load_blend_workflow_index(root),
                {
                    "latest_plan_id": "",
                    "latest_run_id": "",
                    "plans": [],
                    "runs": [],
                },
            )

    def test_shared_store_lists_and_filters_persisted_workflow_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan = blend_workflow_plan_from_skill_compose_arguments(
                {
                    "steps": [
                        {"step_id": "emit", "skill_title": "Emit Text"},
                        {"step_id": "consume", "skill_title": "Consume Text"},
                    ],
                    "root_inputs": {"text": "hello"},
                    "final_output_step": "consume",
                }
            )
            ok_run = blend_workflow_run_from_skill_compose_result(
                plan=plan,
                result={
                    "status": "ok",
                    "capability": "ws.workflow.run",
                    "target": "skills",
                    "requested_skill_titles": ["Emit Text", "Consume Text"],
                    "plan_authorities": ["execute"],
                    "final_output_step": "consume",
                    "final_output": {"result": "done"},
                    "final_outputs_by_step": {"consume": {"result": "done"}},
                    "steps": [{"step_id": "emit", "status": "ok"}, {"step_id": "consume", "status": "ok"}],
                    "started_at": "2026-04-05T10:00:00+00:00",
                    "finished_at": "2026-04-05T10:00:01+00:00",
                },
            )
            persisted_plan, first_run, _ = persist_blend_workflow_objects(
                root_path=root,
                plan=plan,
                run=ok_run,
                session_id="ws_demo",
            )
            failed_run = blend_workflow_run_from_skill_compose_result(
                plan=persisted_plan,
                result={
                    "workflow_id": persisted_plan.workflow_id,
                    "status": "error",
                    "capability": "ws.workflow.run",
                    "target": "skills",
                    "requested_skill_titles": ["Emit Text", "Consume Text"],
                    "plan_authorities": ["execute"],
                    "final_output_step": "consume",
                    "final_output": None,
                    "final_outputs_by_step": {},
                    "steps": [{"step_id": "emit", "status": "ok"}, {"step_id": "consume", "status": "error"}],
                    "started_at": "2026-04-05T10:00:02+00:00",
                    "finished_at": "2026-04-05T10:00:03+00:00",
                },
            )
            _, second_run, _ = persist_blend_workflow_objects(
                root_path=root,
                plan=persisted_plan,
                run=failed_run,
                session_id="ws_demo",
            )

            run_summaries = list_blend_workflow_summaries(root, kind="runs", limit=10)
            self.assertEqual([item["workflow_run_id"] for item in run_summaries], [second_run.workflow_run_id, first_run.workflow_run_id])
            ok_summaries = list_blend_workflow_summaries(root, kind="runs", status="ok", limit=10)
            self.assertEqual([item["workflow_run_id"] for item in ok_summaries], [first_run.workflow_run_id])
            related_runs = list_blend_workflow_runs_for_plan(root, persisted_plan.workflow_id, limit=10)
            self.assertEqual([item["workflow_run_id"] for item in related_runs], [second_run.workflow_run_id, first_run.workflow_run_id])
            index_payload = load_blend_workflow_index(root)
            self.assertEqual(index_payload["latest_plan_id"], persisted_plan.workflow_id)
            self.assertEqual(index_payload["latest_run_id"], second_run.workflow_run_id)


if __name__ == "__main__":
    unittest.main()
