import json
import tempfile
import unittest
from pathlib import Path

from realized_blend.ports import BlendWorkflowRepository
from realized_blend.workflows import (
    BlendWorkflowPlan,
    BlendWorkflowRun,
    BlendWorkflowStep,
)
from realized_blend_application.workflows import (
    blend_workflow_plan_from_skill_compose_arguments,
    blend_workflow_run_from_skill_compose_result,
)
from realized_blend_application.workflow_store import (
    JsonBlendWorkflowRepository,
    ensure_blend_workflow_store,
    list_blend_workflow_runs_for_plan,
    list_blend_workflow_summaries,
    load_blend_workflow_index,
    persist_blend_workflow_objects,
)


class BlendWorkflowStoreTests(unittest.TestCase):
    @staticmethod
    def _tree(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    @staticmethod
    def _fixed_objects() -> tuple[BlendWorkflowPlan, BlendWorkflowRun]:
        plan = BlendWorkflowPlan(
            workflow_id="workflow-fixed",
            workflow_kind="workflow",
            steps=(
                BlendWorkflowStep(
                    step_id="emit",
                    operator_kind="skill",
                    operator_name="Emit Text",
                ),
            ),
            session_id="session-fixed",
            created_at="2026-10-27T00:00:00+00:00",
            root_inputs={"text": "stable"},
            final_output_step="emit",
        )
        run = BlendWorkflowRun(
            workflow_run_id="run-fixed",
            workflow_id=plan.workflow_id,
            plan=plan,
            status="ok",
            final_output_step="emit",
            final_output={"text": "stable"},
            final_outputs_by_step={"emit": {"text": "stable"}},
            steps=[{"step_id": "emit", "status": "ok"}],
            plan_authorities=["invoke"],
            session_id=plan.session_id,
            started_at="2026-10-27T00:00:00+00:00",
            finished_at="2026-10-27T00:00:01+00:00",
        )
        return plan, run

    def test_json_repository_satisfies_neutral_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertIsInstance(
                JsonBlendWorkflowRepository(Path(tmpdir)),
                BlendWorkflowRepository,
            )

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

    def test_compatibility_functions_and_repository_preserve_bytes_and_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            plan, run = self._fixed_objects()
            wrapper_result = persist_blend_workflow_objects(
                root_path=root,
                plan=plan,
                run=run,
                session_id=plan.session_id,
            )
            wrapper_tree = self._tree(root)
            wrapper_index = load_blend_workflow_index(root)
            wrapper_summaries = list_blend_workflow_summaries(root)
            wrapper_related = list_blend_workflow_runs_for_plan(root, plan.workflow_id)

            repository = JsonBlendWorkflowRepository(root)
            repository_result = repository.persist(
                plan=plan,
                run=run,
                session_id=plan.session_id,
            )

            self.assertEqual(wrapper_result, repository_result)
            self.assertEqual(wrapper_tree, self._tree(root))
            self.assertEqual(wrapper_index, repository.load_index())
            self.assertEqual(wrapper_summaries, repository.list_summaries())
            self.assertEqual(
                wrapper_related,
                repository.list_runs_for_plan(plan.workflow_id),
            )
            self.assertEqual(
                wrapper_result[0],
                repository.load_plan(plan.workflow_id),
            )
            self.assertEqual(
                wrapper_result[1],
                repository.load_run(run.workflow_run_id),
            )

    def test_missing_and_malformed_files_preserve_historical_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "blend-root"
            repository = JsonBlendWorkflowRepository(root)

            with self.assertRaises(FileNotFoundError):
                repository.load_plan("missing-plan")
            with self.assertRaises(FileNotFoundError):
                repository.load_run("missing-run")

            paths = repository.ensure()
            paths["index"].write_text("{not-json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                repository.load_index()
            with self.assertRaises(json.JSONDecodeError):
                repository.list_summaries()

            paths["plans"].joinpath("bad-plan.json").write_text(
                "{not-json",
                encoding="utf-8",
            )
            paths["runs"].joinpath("bad-run.json").write_text(
                "{not-json",
                encoding="utf-8",
            )
            with self.assertRaises(json.JSONDecodeError):
                repository.load_plan("bad-plan")
            with self.assertRaises(json.JSONDecodeError):
                repository.load_run("bad-run")


if __name__ == "__main__":
    unittest.main()
