# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    LearningRelation,
    artifact_export_bundle_text,
    normalize_boundary_shape,
)
from blend_workflow import BlendWorkflowBinding, BlendWorkflowPlan, BlendWorkflowRun, BlendWorkflowStep
from blend_workflow_store import persist_blend_workflow_objects
from gather_sources import latest_source_revision, list_staged_sources, new_source_collection, persist_source_collection
from host_interaction_receipts import append_host_interaction_receipt
from learning_context import load_learning_context
from applied_theory_types import BoundaryShapeTerm
from workstation.foundation.projections import WorkstationActivityEventView, render_workstation_activity_event
from workstation.runtime.core.session import launch_workstation_session, load_workstation_session
from workstation.runtime.core.workstation_core import (
    workstation_activity_event_view,
    workstation_chat_transcript_view,
    workstation_recent_activity_feed,
    workstation_change_session_capabilities,
    workstation_export_learned_skill_bundle_action,
    workstation_import_staged_source_action,
    workstation_invoke_skill_action,
    workstation_learn_markdown_action,
    workstation_learn_url_action,
    workstation_refresh_staged_source_action,
    workstation_sync_source_collection_action,
    workstation_prompt_action,
    workstation_run_workflow_action,
    workstation_skill_catalog_for_session,
    workstation_skill_descriptor_for_query,
    workstation_workflow_summary_list_view,
    workstation_workflow_query_view,
)
from url_learning_capture import CapturedUrlLearningBundle


class WorkstationCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        self.skills_sqlite = Path(self.tempdir.name) / "skills.sqlite3"
        self.workspace.mkdir(parents=True, exist_ok=True)
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Test workstation core.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_workstation_skill_descriptor_for_query_builds_form_view(self) -> None:
        session = load_workstation_session(self.root)
        descriptor = workstation_skill_descriptor_for_query(
            session=session,
            skill_query="Workstation Repo Search",
        )
        self.assertEqual(descriptor.skill_title, "Workstation Repo Search")
        self.assertEqual(descriptor.source_kind, "builtin_workstation")
        self.assertEqual(descriptor.executor_framework, "python3")
        self.assertGreaterEqual(len(descriptor.input_form.fields), 1)
        mount_fields = [field for field in descriptor.input_form.fields if field.field_name == "mount"]
        self.assertTrue(mount_fields)
        relative_path_fields = [field for field in descriptor.input_form.fields if field.field_name == "relative_path"]
        self.assertTrue(relative_path_fields)
        self.assertIn("main", mount_fields[0].options)
        self.assertTrue(mount_fields[0].constraints.get("attachment_backed"))
        self.assertIn("main", mount_fields[0].constraints.get("allowed_values", []))
        self.assertEqual(mount_fields[0].section, "Location")
        self.assertEqual(mount_fields[0].placeholder, "main")
        self.assertTrue(relative_path_fields[0].constraints.get("path_like"))
        self.assertEqual(relative_path_fields[0].constraints.get("path_scope"), "workspace_relative")
        self.assertEqual(relative_path_fields[0].section, "Location")
        self.assertEqual(relative_path_fields[0].placeholder, "src/example.txt")
        self.assertTrue(descriptor.input_form.sections)
        self.assertEqual(descriptor.input_form.sections[0].title, "Location")

    def test_workstation_skill_catalog_for_session_projects_builtin_and_imported(self) -> None:
        session = load_workstation_session(self.root)
        catalog = workstation_skill_catalog_for_session(
            session=session,
            query="workstation",
        )
        self.assertGreaterEqual(catalog.total_visible, 1)
        self.assertTrue(any(item.skill_title == "Workstation Repo Search" for item in catalog.builtin))

    def test_workstation_change_session_capabilities_persists_session(self) -> None:
        session = load_workstation_session(self.root)
        updated = workstation_change_session_capabilities(
            root=self.root,
            session=session,
            added_capabilities=["ws.net.http"],
            removed_capabilities=["ws.process.run"],
        )
        self.assertIn("ws.net.http", updated.allowed_capabilities)
        self.assertNotIn("ws.process.run", updated.allowed_capabilities)
        reloaded = load_workstation_session(self.root)
        self.assertIn("ws.net.http", reloaded.allowed_capabilities)
        self.assertNotIn("ws.process.run", reloaded.allowed_capabilities)

    def test_workstation_invoke_skill_action_runs_skill_through_capability_surface(self) -> None:
        result = workstation_invoke_skill_action(
            root_path=self.root,
            skill_query="Workstation Greeting From Wasm",
            raw_inputs={"payload": "hello"},
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "skill_invoke")
        self.assertIn("Workstation Greeting From Wasm", result.title)
        self.assertIn("hello from workstation wasm", result.message)
        self.assertEqual(result.payload.get("capability"), "ws.skill.invoke")

    def test_execute_workstation_capability_can_create_and_append_learning_markdown(self) -> None:
        from workstation.runtime.core.capabilities import execute_workstation_capability

        session = load_workstation_session(self.root)
        created = execute_workstation_capability(
            session,
            "ws.markdown.create",
            {
                "path": "notes/chemistry_learnings.md",
                "markdown_text": "# Chemistry Learnings\n\n- Conservation of amount is invariant.",
            },
        )
        appended = execute_workstation_capability(
            session,
            "ws.markdown.append",
            {
                "path": "notes/chemistry_learnings.md",
                "markdown_text": "## More\n\n- Balance atoms before balancing charge.",
            },
        )
        destination = self.workspace / "notes" / "chemistry_learnings.md"
        self.assertTrue(destination.exists())
        self.assertEqual(created["status"], "ok")
        self.assertEqual(created["target"], "main")
        self.assertEqual(appended["status"], "ok")
        self.assertEqual(appended["target"], "main")
        rendered = destination.read_text()
        self.assertIn("# Chemistry Learnings", rendered)
        self.assertIn("## More", rendered)
        self.assertIn("Balance atoms before balancing charge.", rendered)

    def test_workstation_chat_transcript_view_and_prompt_action_use_session_prompt_path(self) -> None:
        (self.root / "MESSAGES.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"role": "user", "content": "hello", "timestamp_epoch_ms": 1712577600000}),
                    json.dumps({"role": "assistant", "content": "hi", "timestamp_epoch_ms": 1712577601250}),
                ]
            )
            + "\n"
        )
        with patch(
            "workstation.runtime.core.session.prompt_workstation_session",
            return_value={
                "assistant_text": "Handled prompt.",
                "fulfilled_by": "ws.skill.catalog",
                "rounds": 0,
                "tool_receipts": [],
            },
        ):
            result = workstation_prompt_action(
                root_path=self.root,
                prompt="What skills are available right now?",
            )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "chat_prompt")
        transcript = workstation_chat_transcript_view(root_path=self.root)
        self.assertEqual(len(transcript.messages), 2)
        self.assertEqual(transcript.messages[-2].role, "user")
        self.assertEqual(transcript.messages[-2].timestamp_epoch_ms, 1712577600000)
        self.assertEqual(transcript.messages[-1].role, "assistant")
        self.assertEqual(transcript.messages[-1].timestamp_epoch_ms, 1712577601250)

    def test_workstation_workflow_query_view_returns_graph_projection(self) -> None:
        workflow_plan = BlendWorkflowPlan(
            workflow_id="",
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
                ),
                BlendWorkflowStep(
                    step_id="consume",
                    operator_kind="skill",
                    operator_name="Consume Text",
                    bindings=(
                        BlendWorkflowBinding(
                            {
                                "source_step_id": "emit",
                                "source_path": "/d/text",
                                "target_path": "/a/text",
                                "mapper": {"kind": "identity"},
                            }
                        ),
                    ),
                ),
            ),
            metadata={"target": "skills"},
        )
        workflow_run = BlendWorkflowRun(
            workflow_run_id="",
            workflow_id="",
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
            plan_authorities=["read"],
        )
        persisted_plan, persisted_run, _store = persist_blend_workflow_objects(
            root_path=self.root,
            plan=workflow_plan,
            run=workflow_run,
            session_id="ws-1",
        )
        result = workstation_workflow_query_view(
            root_path=self.root,
            workflow_run_id=persisted_run.workflow_run_id,
        )
        summary_list = workstation_workflow_summary_list_view(
            root_path=self.root,
            kind="runs",
            limit=10,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["workflow_id"], persisted_plan.workflow_id)
        self.assertEqual(result["workflow_graph"]["workflow_run_id"], persisted_run.workflow_run_id)
        self.assertEqual(result["workflow_timeline"]["workflow_run_id"], persisted_run.workflow_run_id)
        self.assertEqual(len(result["workflow_timeline"]["entries"]), 2)
        self.assertEqual(result["workflow_timeline"]["entries"][1]["step_id"], "consume")
        self.assertTrue(any(item["node_id"] == "consume" for item in result["workflow_graph"]["nodes"]))
        self.assertTrue(any(item["source_node_id"] == "emit" for item in result["workflow_graph"]["edges"]))
        self.assertEqual(summary_list.kind, "runs")
        self.assertTrue(any(item.workflow_run_id == persisted_run.workflow_run_id for item in summary_list.items))
        plan_result = workstation_workflow_query_view(
            root_path=self.root,
            workflow_id=persisted_plan.workflow_id,
        )
        self.assertEqual(plan_result["workflow_run_history"]["kind"], "runs")
        self.assertEqual(plan_result["workflow_run_history"]["returned_count"], 1)

    def test_workstation_run_workflow_action_reruns_persisted_workflow(self) -> None:
        session = load_workstation_session(self.root)
        first_run = workstation_run_workflow_action(
            root_path=self.root,
            workflow_id=self._persist_greeting_workflow_and_run_once(session=session),
        )
        self.assertEqual(first_run.status, "ok")
        second_run = workstation_run_workflow_action(
            root_path=self.root,
            workflow_id=first_run.workflow_id,
        )
        self.assertEqual(second_run.status, "ok")
        self.assertEqual(second_run.action_kind, "workflow_run")
        self.assertEqual(second_run.workflow_id, first_run.workflow_id)
        self.assertNotEqual(second_run.workflow_run_id, first_run.workflow_run_id)
        self.assertEqual(second_run.payload.get("capability"), "ws.workflow.run")

    def test_workstation_learn_markdown_action_converts_and_imports_bundle(self) -> None:
        markdown_path = self.workspace / "lesson.md"
        markdown_path.write_text("# Demo Lesson\n\n```python\nprint('hello')\n```")
        progress_messages: list[str] = []

        def _fake_convert(command: list[str], **kwargs) -> object:
            out_path = Path(command[command.index("--out") + 1])
            report_path = Path(command[command.index("--report-out") + 1])
            out_path.write_text("schema: bssc_skill.v2\nkind: ability\ntitle: Learned Demo Skill\n")
            report_path.write_text(json.dumps({"learned_count": 1}))
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with (
            patch("workstation.runtime.core.workstation_core.subprocess.run", side_effect=_fake_convert),
            patch(
                "workstation.runtime.core.capabilities.execute_workstation_capability",
                return_value={
                    "status": "ok",
                    "capability": "ws.skill.import",
                    "imported_count": 1,
                    "imported": [{"title": "Learned Demo Skill"}],
                    "canonical_export_path": str(self.root / "skills" / "exports" / "lesson.skill.yaml"),
                },
            ),
        ):
            result = workstation_learn_markdown_action(
                root_path=self.root,
                markdown_path=markdown_path,
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "learn_markdown")
        self.assertIn("Imported 1 skill", result.message)
        self.assertEqual(result.payload["report"]["learned_count"], 1)
        self.assertEqual(result.payload["import_result"]["status"], "ok")
        self.assertTrue(str(result.payload["canonical_export_path"]).endswith("lesson.skill.yaml"))
        self.assertEqual(
            progress_messages,
            [
                "Preparing markdown learning for: lesson.md",
                "Converting markdown to a portable skill bundle...",
                "Staging learned bundle for workstation import...",
                "Importing learned bundle into the workstation skill store...",
                "Imported 1 skill from markdown.",
            ],
        )

    def test_workstation_learn_markdown_action_imports_artifact_bundle_output(self) -> None:
        markdown_path = self.workspace / "lesson.md"
        markdown_path.write_text("# Demo Lesson\n\nportable learning")
        progress_messages: list[str] = []

        def _fake_convert(command: list[str], **kwargs) -> object:
            out_path = Path(command[command.index("--out") + 1])
            report_path = Path(command[command.index("--report-out") + 1])
            artifact = Artifact(
                id="artifact-demo-knowledge",
                artifact_type=ArtifactType.KNOWLEDGE,
                title="Learned Demo Skill",
                representation=ArtifactRepresentation.YAML,
                function_bit=0,
                scope="reuse for workstation markdown learning",
                provenance=["test"],
                reusability=ArtifactReuse.BROAD_REUSE,
                admissibility=ArtifactAdmission.ADMITTED,
                template_schema={},
                learning_relation=LearningRelation.NEW_FAMILY,
                related_artifact_ids=[],
                content={
                    "question": "What did the markdown teach?",
                    "answer": "The markdown taught one portable knowledge skill.",
                    "structured_learning": {
                        "encountered_not": "Learned Demo Skill",
                        "lookup_keys": ["learned demo skill"],
                        "component_nots": [],
                        "composed_not": "",
                        "notation_yaml": "",
                    },
                },
                justification="Generated by markdown learning test.",
                boundary_shape=normalize_boundary_shape((BoundaryShapeTerm.OUTPUT_VALUE.value,), default=()),
            )
            out_path.write_text(artifact_export_bundle_text([artifact]))
            report_path.write_text(json.dumps({"learned_count": 1}))
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with patch("workstation.runtime.core.workstation_core.subprocess.run", side_effect=_fake_convert):
            result = workstation_learn_markdown_action(
                root_path=self.root,
                markdown_path=markdown_path,
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "learn_markdown")
        self.assertGreaterEqual(int(result.payload["import_result"]["imported_count"]), 1)
        self.assertIn("Learned Demo Skill", result.payload.get("imported_titles", []))
        canonical_export_path = Path(str(result.payload["canonical_export_path"]))
        self.assertTrue(canonical_export_path.exists())
        canonical_export_text = canonical_export_path.read_text()
        self.assertIn("title: Learned Demo Skill", canonical_export_text)
        self.assertIn("schema: bssc_skill.v2", canonical_export_text)
        self.assertEqual(
            progress_messages[:4],
            [
                "Preparing markdown learning for: lesson.md",
                "Converting markdown to a portable skill bundle...",
                "Staging learned bundle for workstation import...",
                "Importing learned bundle into the workstation skill store...",
            ],
        )

    def test_workstation_learn_markdown_action_lightweight_testing_disables_llm_and_vectors_for_convert(self) -> None:
        markdown_path = self.workspace / "lesson.md"
        markdown_path.write_text("# Demo Lesson\n\nportable learning")
        captured: dict[str, object] = {}

        def _fake_convert(command: list[str], **kwargs) -> object:
            captured["command"] = list(command)
            captured["env"] = dict(kwargs.get("env", {}))
            out_path = Path(command[command.index("--out") + 1])
            report_path = Path(command[command.index("--report-out") + 1])
            out_path.write_text("schema: bssc_skill.v2\nkind: knowledge\ntitle: Lightweight Demo Skill\n")
            report_path.write_text(json.dumps({"learned_count": 1}))
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with (
            patch("workstation.runtime.core.workstation_core.subprocess.run", side_effect=_fake_convert),
            patch(
                "workstation.runtime.core.capabilities.execute_workstation_capability",
                return_value={
                    "status": "ok",
                    "capability": "ws.skill.import",
                    "imported_count": 1,
                    "imported": [{"title": "Lightweight Demo Skill"}],
                    "canonical_export_path": str(self.root / "skills" / "exports" / "lesson.skill.yaml"),
                },
            ),
        ):
            result = workstation_learn_markdown_action(
                root_path=self.root,
                markdown_path=markdown_path,
                testing_lightweight=True,
            )

        self.assertEqual(result.status, "ok")
        command = captured.get("command")
        env = captured.get("env")
        self.assertIsInstance(command, list)
        self.assertIsInstance(env, dict)
        self.assertIn("--llm", command)
        self.assertEqual(command[command.index("--llm") + 1], "off")
        self.assertEqual(env.get("STATE_VECTOR_MODE"), "off")
        self.assertEqual(env.get("LLM_SUPPLEMENT_POLICY"), "off")

    def test_workstation_learn_url_action_stages_captured_source_in_gather_workspace(self) -> None:
        progress_messages: list[str] = []
        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )

        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/article",
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "learn_url")
        self.assertIn("Staged URL source", result.message)
        self.assertEqual(result.payload["subject_id"], "example-article")
        self.assertEqual(result.payload["capture_report"]["title"], "Example Article")
        context = load_learning_context(self.root, "example-article")
        self.assertEqual(context.canonical_title, "Example Article")
        staged_sources = list_staged_sources(self.root, "example-article")
        self.assertEqual(len(staged_sources), 1)
        self.assertEqual(staged_sources[0].source_ref, "https://example.test/article")
        self.assertEqual(
            progress_messages,
            [
                "Preparing URL capture for: https://example.test/article",
                "Fetching URL and extracting canonical markdown...",
                "Creating Gather source workspace...",
                "Saving captured source into Gather...",
                "Staged URL source in Gather.",
            ],
        )

    def test_workstation_import_staged_source_action_explicitly_imports_gather_source(self) -> None:
        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        progress_messages: list[str] = []
        with (
            patch(
                "workstation.runtime.core.workstation_core._learn_markdown_bundle_in_process",
                return_value={
                    "subject_id": "example-article",
                    "context_path": str(self.root / "corpus" / "example-article" / "context.json"),
                    "learned_count": 1,
                    "learning_context": {
                        "subject_id": "example-article",
                        "context_path": str(self.root / "corpus" / "example-article" / "context.json"),
                    },
                },
            ) as learn_mock,
            patch(
                "workstation.runtime.core.capabilities.execute_workstation_capability",
                return_value={
                    "status": "ok",
                    "capability": "ws.skill.import",
                    "imported_count": 1,
                    "imported": [{"title": "Example Article"}],
                    "canonical_export_path": str(self.root / "skills" / "exports" / "example-article.skill.yaml"),
                },
            ),
        ):
            result = workstation_import_staged_source_action(
                root_path=self.root,
                subject_id="example-article",
                staged_source_id=str(staged.payload["staged_source_id"]),
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertIn("Imported 1 skill", result.message)
        learn_kwargs = learn_mock.call_args.kwargs
        self.assertEqual(learn_kwargs["source_bundle_override"]["source_kind"], "url")
        self.assertEqual(learn_kwargs["source_bundle_override"]["source_ref"], "https://example.test/article")
        self.assertEqual(
            progress_messages,
            [
                "Importing staged source: Example Article",
                "Learning reusable artifacts from staged source markdown...",
                "Importing learned bundle into the workstation skill store...",
                "Imported 1 skill from staged source.",
            ],
        )

    def test_workstation_refresh_staged_source_action_writes_new_refresh_revision(self) -> None:
        initial_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nInitial source notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Initial</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577700000,
            markdown_text="# Example Article\n\nRefreshed source notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=initial_capture):
            staged = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        progress_messages: list[str] = []
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=refreshed_capture):
            result = workstation_refresh_staged_source_action(
                root_path=self.root,
                subject_id="example-article",
                staged_source_id=str(staged.payload["staged_source_id"]),
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "refresh_staged_source")
        staged_source = list_staged_sources(self.root, "example-article")[0]
        latest_revision = latest_source_revision(self.root, staged_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        self.assertEqual(staged_source.revision_count, 2)
        self.assertEqual(latest_revision.revision_kind, "refresh")
        self.assertEqual(latest_revision.metadata.get("refresh_mode"), "url_capture")
        self.assertIn("Refreshed source notes.", body_path.read_text(encoding="utf-8"))
        self.assertEqual(
            progress_messages,
            [
                "Refreshing staged source: Example Article",
                "Fetching URL and extracting canonical markdown...",
                "Saving refreshed source revision into Gather...",
                "Refreshed staged source in Gather.",
            ],
        )

    def test_workstation_sync_source_collection_action_refreshes_all_url_sources_in_set(self) -> None:
        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-one",
            final_url="https://example.test/article-one",
            title="Article One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Article One\n\nInitial one.\n",
            bundle_files={
                "rendered.html": "<html><body>Article One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-two",
            final_url="https://example.test/article-two",
            title="Article Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Article Two\n\nInitial two.\n",
            bundle_files={
                "rendered.html": "<html><body>Article Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-two"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-one",
            final_url="https://example.test/article-one?fresh=1",
            title="Article One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577700000,
            markdown_text="# Article One\n\nRefreshed one.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-one"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-two",
            final_url="https://example.test/article-two?fresh=1",
            title="Article Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577701000,
            markdown_text="# Article Two\n\nRefreshed two.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-two"},
            elements=(),
            asset_manifest=(),
        )

        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            staged_one = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/article-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            staged_two = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/article-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Tracked sources for energy export topics.",
            staged_source_ids=(
                str(staged_one.payload["staged_source_id"]),
                str(staged_two.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)

        progress_messages: list[str] = []
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[refreshed_one, refreshed_two]):
            result = workstation_sync_source_collection_action(
                root_path=self.root,
                subject_id="energy-exports",
                collection_id=collection.collection_id,
                progress_callback=progress_messages.append,
            )

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action_kind, "sync_source_collection")
        payload = dict(result.payload or {})
        self.assertEqual(payload.get("collection_id"), collection.collection_id)
        self.assertEqual(payload.get("refreshed_count"), 2)
        self.assertEqual(payload.get("failed_count"), 0)
        self.assertEqual(payload.get("skipped_count"), 0)

        staged_sources = list_staged_sources(self.root, "energy-exports")
        latest_bodies = []
        for staged_source in staged_sources:
            latest_revision = latest_source_revision(self.root, staged_source)
            self.assertIsNotNone(latest_revision)
            self.assertEqual(latest_revision.revision_kind, "refresh")
            body_path = self.root / "corpus" / "energy-exports" / "gather" / "revisions" / latest_revision.markdown_relpath
            latest_bodies.append(body_path.read_text(encoding="utf-8"))
            self.assertEqual(staged_source.revision_count, 2)
        self.assertTrue(any("Refreshed one." in body for body in latest_bodies))
        self.assertTrue(any("Refreshed two." in body for body in latest_bodies))
        self.assertIn("Syncing source set: Energy Export Sources", progress_messages)
        self.assertIn("Refreshing 1/2: Article One", progress_messages)
        self.assertIn("Refreshing 2/2: Article Two", progress_messages)

    def test_workstation_export_learned_skill_bundle_action_copies_bundle(self) -> None:
        source_bundle = self.root / "skills" / "exports" / "learned.skill.yaml"
        source_bundle.parent.mkdir(parents=True, exist_ok=True)
        source_bundle.write_text("schema: bssc_skill.v2\nkind: ability\ntitle: Learned Demo Skill\n")
        destination = self.workspace / "exports" / "learned.skill.yaml"
        result = workstation_export_learned_skill_bundle_action(
            root_path=self.root,
            source_bundle_path=source_bundle,
            destination_path=destination,
        )
        self.assertEqual(result.status, "ok")
        self.assertTrue(destination.exists())
        self.assertEqual(destination.read_text(), source_bundle.read_text())

    def test_workstation_activity_views_project_and_render_receipts(self) -> None:
        append_host_interaction_receipt(
            self.root,
            {
                "kind": "user_prompt",
                "prompt": "List skills.",
                "timestamp": "2026-04-06T12:00:00+00:00",
            },
        )
        append_host_interaction_receipt(
            self.root,
            {
                "kind": "capability_call",
                "timestamp": "2026-04-06T12:00:00.200000+00:00",
                "capability": "ws.skill.catalog",
                "arguments": {},
                "result": {"status": "started"},
                "phase": "started",
            },
        )
        append_host_interaction_receipt(
            self.root,
            {
                "kind": "capability_call",
                "timestamp": "2026-04-06T12:00:00.800000+00:00",
                "capability": "ws.skill.catalog",
                "arguments": {},
                "result": {"status": "ok", "returned_skill_count": 14},
            },
        )
        feed = workstation_recent_activity_feed(root_path=self.root, limit=10)
        self.assertEqual(len(feed.events), 3)
        self.assertEqual(render_workstation_activity_event(feed.events[0]), "Prompt received (t+0.0s)")
        self.assertEqual(render_workstation_activity_event(feed.events[1]), "Listing available skills (t+0.2s)")
        self.assertEqual(render_workstation_activity_event(feed.events[2]), "Listed 14 skills (t+0.8s, op ~0.6s)")
        started = workstation_activity_event_view(
            {
                "kind": "capability_call",
                "capability": "ws.permissions.grant",
                "arguments": {"capability": "ws.repo.search"},
                "result": {"status": "started"},
                "phase": "started",
            },
            prompt_elapsed_seconds=0.3,
        )
        self.assertIsNotNone(started)
        assert started is not None
        self.assertEqual(render_workstation_activity_event(started), "Granting permission: ws.repo.search (t+0.3s)")

    def test_recent_activity_feed_renders_blend_workflow_as_tree(self) -> None:
        feed = workstation_recent_activity_feed(
            root_path=self.root,
            limit=10,
            supplemental_events=(
                WorkstationActivityEventView(
                    event_kind="blend_workflow_started",
                    message="Workflow started (2 steps)",
                    status="started",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                ),
                WorkstationActivityEventView(
                    event_kind="blend_step_started",
                    message="Step started: Emit Text",
                    status="started",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                    step_id="emit",
                    branch_label="if",
                ),
                WorkstationActivityEventView(
                    event_kind="blend_step_completed",
                    message="Step completed: Emit Text",
                    status="ok",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                    step_id="emit",
                    branch_label="if",
                    iteration=1,
                ),
                WorkstationActivityEventView(
                    event_kind="blend_workflow_completed",
                    message="Workflow completed: emit",
                    status="ok",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                ),
            ),
        )
        rendered = [render_workstation_activity_event(item) for item in feed.events]
        self.assertEqual(rendered[0], "Workflow started (2 steps)")
        self.assertIn("├─ Step started: Emit Text [if]", rendered[1])
        self.assertIn("├─ Step completed: Emit Text [if | iter 2]", rendered[2])
        self.assertEqual(rendered[3], "Workflow completed: emit")

    def _persist_greeting_workflow_and_run_once(self, *, session) -> str:
        from workstation.runtime.core.capabilities import execute_workstation_capability

        session = workstation_change_session_capabilities(
            root=self.root,
            session=session,
            added_capabilities=["ws.workflow.run"],
            removed_capabilities=[],
        )
        run_result = execute_workstation_capability(
            session,
            "ws.workflow.run",
            {
                "workflow_plan": {
                    "workflow_kind": "skill_compose",
                    "steps": [
                        {
                            "step_id": "greet",
                            "operator_kind": "skill",
                            "operator_name": "Workstation Greeting From Wasm",
                            "bindings": [
                                {
                                    "target_region": "a",
                                    "target_path": "/a/payload",
                                    "source_root_name": "payload",
                                    "source_root_region": "a",
                                }
                            ],
                        }
                    ],
                    "root_inputs": {"payload": "hello"},
                    "final_output_step": "greet",
                    "metadata": {"target": "skills"},
                }
            },
        )
        self.assertEqual(run_result["status"], "ok")
        return str(run_result["workflow_id"])
