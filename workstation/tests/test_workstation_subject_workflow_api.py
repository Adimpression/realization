# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import grpc

from controller_entrypoints import ensure_application_controller_runtime
from gather_sources import new_source_collection, persist_source_collection
from learning_context import new_learning_context, persist_learning_context
from workstation.grpc.definitions import subject_workflow_pb2, subject_workflow_pb2_grpc
from workstation.runtime.core.session import launch_workstation_session
from workstation.subject.core.subject_workflow import (
    SubjectActionResult,
    new_subject_progress,
    persist_subject_progress,
    subject_progress_path,
)
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService
from workstation.subject.service.subject_workflow_client import (
    GrpcSubjectWorkflowClient,
    InProcessSubjectWorkflowClient,
    new_grpc_subject_workflow_client_for_unix_socket,
)
from workstation.grpc.implementation.subject_workflow_grpc import (
    bind_subject_workflow_grpc_server_unix_socket,
    build_subject_workflow_grpc_server,
)


class WorkstationSubjectWorkflowApiTests(unittest.TestCase):
    def setUp(self) -> None:
        ensure_application_controller_runtime()
        self.tempdir = tempfile.TemporaryDirectory()
        self.enterContext(
            mock.patch.dict(
                "os.environ",
                {"WORKSTATION_HOME": str(Path(self.tempdir.name) / "workstation-home")},
                clear=False,
            )
        )
        self.root = Path(self.tempdir.name) / "root"
        self.root.mkdir(parents=True, exist_ok=True)
        context = new_learning_context(canonical_title="Transit Modernization")
        persist_learning_context(self.root, context)
        self.subject_id = context.subject_id

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_subject_workflow_api_lists_subjects_and_projects_phase_view(self) -> None:
        service = SubjectWorkflowApiService()

        subjects = service.list_subjects(root_path=self.root)

        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0].subject_id, self.subject_id)
        self.assertEqual(subjects[0].title, "Transit Modernization")

        view = service.get_phase_view(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )

        self.assertEqual(view.phase, "research")
        self.assertEqual(view.phase_title, "Gather")
        self.assertEqual(view.status_view.title, "Gather Status")
        status_rows = {row.label: row.value for row in view.status_view.rows}
        self.assertEqual(status_rows["Mode"], "Live subject workflow")
        self.assertEqual(status_rows["Phase"], "Gather")
        self.assertIn("Gather Intake", status_rows)
        self.assertTrue(view.current_step.title)
        self.assertTrue(view.current_step.actions)
        self.assertEqual(view.workspace_view.title, "Gather Journal")

    def test_subject_workflow_api_can_apply_current_step_action_and_refresh_view(self) -> None:
        service = SubjectWorkflowApiService()
        initial_view = service.get_phase_view(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )

        outcome = service.apply_action(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
            action_key=initial_view.current_step.actions[0].key,
        )

        self.assertTrue(outcome.status_text)
        self.assertIn(outcome.phase_view.phase, {"research", "itemize", "draft", "review", "publication"})
        self.assertTrue(outcome.phase_view.current_step.title)

    def test_subject_workflow_api_projects_control_bundle(self) -> None:
        service = SubjectWorkflowApiService()

        bundle = service.get_control_bundle(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )

        self.assertEqual(bundle.phase, "research")
        self.assertTrue(any(spec.key == "research_source_collection" for spec in bundle.selects))
        self.assertTrue(any(spec.key == "research_source_revision_history" for spec in bundle.tables))

    def test_subject_workflow_api_projects_pane_bundle(self) -> None:
        service = SubjectWorkflowApiService()

        bundle = service.get_pane_bundle(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )

        self.assertEqual(bundle.phase, "research")
        self.assertTrue(any(pane.key == "research_sources" for pane in bundle.panes))
        self.assertTrue(any(pane.key == "research_target" for pane in bundle.panes))
        learned_snapshot = next(pane for pane in bundle.panes if pane.key == "research_observation")
        self.assertTrue(learned_snapshot.is_structured_table)
        self.assertTrue(any(row.label == "Subject summary" for row in learned_snapshot.rows))
        source_detail = next(pane for pane in bundle.panes if pane.key == "research_target")
        self.assertFalse(source_detail.is_structured_table)
        self.assertTrue(source_detail.lines)
        self.assertFalse(source_detail.rows)

        itemize_bundle = service.get_pane_bundle(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="itemize",
        )
        itemize_target = next(pane for pane in itemize_bundle.panes if pane.key == "itemize_target")
        self.assertEqual(itemize_target.rows[0].label, "Itemize Target")
        self.assertEqual(itemize_target.rows[0].value, "Draft Handoff")

    def test_subject_workflow_api_projects_typed_rows_for_every_structured_pane(self) -> None:
        service = SubjectWorkflowApiService()

        for phase in ("research", "itemize", "draft", "review", "publication"):
            with self.subTest(phase=phase):
                bundle = service.get_pane_bundle(
                    root_path=self.root,
                    subject_id=self.subject_id,
                    phase=phase,
                )
                structured_panes = tuple(pane for pane in bundle.panes if pane.is_structured_table)
                self.assertTrue(structured_panes)
                self.assertTrue(
                    all(pane.rows for pane in structured_panes),
                    msg=f"{phase} contains a structured pane without producer-supplied rows",
                )

    def test_subject_workflow_api_projects_typed_pane_items_without_decoding_rendered_lines(self) -> None:
        collection = new_source_collection(
            subject_id=self.subject_id,
            title="Transit Sources",
            description="Typed source inventory fixture.",
        )
        persist_source_collection(self.root, collection)
        progress = new_subject_progress()
        progress.research_selected_source_collection_id = collection.collection_id
        persist_subject_progress(self.root, self.subject_id, progress)
        service = SubjectWorkflowApiService()

        bundle = service.get_pane_bundle(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )

        sources = next(pane for pane in bundle.panes if pane.key == "research_sources")
        projected = next(item for item in sources.items if item.entry_id == collection.collection_id)
        self.assertEqual(projected.entry_kind, "source_collection")
        self.assertEqual(projected.label, "Transit Sources [0 sources, no saved query]")
        self.assertTrue(projected.selected)

    def test_subject_workflow_api_projects_snapshot_and_watch_updates(self) -> None:
        service = SubjectWorkflowApiService()
        client = InProcessSubjectWorkflowClient(service=service)

        snapshot = client.get_snapshot(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )
        self.assertEqual(snapshot.phase_view.phase, "research")
        self.assertEqual(snapshot.control_bundle.phase, "research")
        self.assertEqual(snapshot.pane_bundle.phase, "research")

        watch = client.watch_subject_workflow(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )
        initial_event = next(watch)
        self.assertEqual(initial_event.event_kind, "initial")
        self.assertEqual(initial_event.channel_key, f"subject/{self.subject_id}/research")
        self.assertEqual(initial_event.sequence, 0)
        self.assertTrue(initial_event.snapshot_version)
        self.assertTrue(initial_event.progress_fingerprint)
        self.assertEqual(initial_event.snapshot.phase_view.phase, "research")

        first_action_key = initial_event.snapshot.phase_view.current_step.actions[0].key
        outcome = client.apply_action(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
            action_key=first_action_key,
        )
        self.assertTrue(outcome.status_text)

        changed_event = next(watch)
        self.assertEqual(changed_event.event_kind, "subject_workflow_changed")
        self.assertEqual(changed_event.channel_key, f"subject/{self.subject_id}/research")
        self.assertEqual(changed_event.sequence, 1)
        self.assertTrue(changed_event.snapshot_version)
        self.assertTrue(changed_event.progress_fingerprint)
        self.assertTrue(changed_event.snapshot.phase_view.current_step.title)
        watch.close()

    def test_subject_workflow_api_projects_placeholder_snapshot_for_empty_root(self) -> None:
        service = SubjectWorkflowApiService()
        empty_root = Path(self.tempdir.name) / "empty-root"
        empty_workspace = Path(self.tempdir.name) / "empty-workspace"
        launch_workstation_session(
            root_path=empty_root,
            workspace_path=empty_workspace,
            attach_default_skill_home=False,
            initial_task="Project the placeholder subject workflow.",
        )

        subjects = service.list_subjects(root_path=empty_root)

        self.assertEqual(len(subjects), 1)
        self.assertTrue(subjects[0].is_placeholder)
        self.assertTrue(subjects[0].key)
        snapshot = service.get_snapshot(
            root_path=empty_root,
            subject_id=subjects[0].key,
            phase="research",
        )

        self.assertEqual(snapshot.phase_view.phase, "research")
        self.assertTrue(snapshot.phase_view.scenario.is_placeholder)
        self.assertEqual(snapshot.phase_view.current_step.title, "Create the first subject")
        self.assertTrue(any(action.key == "use_markdown_ingress" for action in snapshot.phase_view.current_step.actions))

    def test_subject_workflow_api_apply_markdown_ingress_uses_staged_path_and_selects_created_subject(self) -> None:
        service = SubjectWorkflowApiService()
        empty_root = Path(self.tempdir.name) / "markdown-root"
        empty_workspace = Path(self.tempdir.name) / "markdown-workspace"
        launch_workstation_session(
            root_path=empty_root,
            workspace_path=empty_workspace,
            attach_default_skill_home=False,
            initial_task="Run canonical markdown ingress through the workflow service.",
        )
        markdown_path = Path(self.tempdir.name) / "city-bus.md"
        markdown_path.write_text(
            "# Smart City Travel\n\nA city transit authority wants to modernize fare payment.\n",
            encoding="utf-8",
        )
        placeholder = service.list_subjects(root_path=empty_root)[0]

        outcome = service.apply_action(
            root_path=empty_root,
            subject_id=placeholder.key,
            phase="research",
            action_key="use_markdown_ingress",
            markdown_selected_path=str(markdown_path),
            markdown_status_text="Markdown upload staged.",
            markdown_busy=True,
        )

        self.assertTrue(outcome.reload_subjects)
        self.assertTrue(outcome.preferred_subject_key)
        self.assertEqual(outcome.phase_view.phase, "research")
        self.assertFalse(outcome.phase_view.scenario.is_placeholder)
        self.assertEqual(outcome.phase_view.scenario.subject_id, outcome.preferred_subject_key)
        self.assertIn("Imported 1 skill", outcome.status_text)
        subjects = service.list_subjects(root_path=empty_root)
        self.assertTrue(any(subject.subject_id == outcome.preferred_subject_key for subject in subjects))

    def test_subject_workflow_api_uploaded_dst_markdown_keeps_the_build_report_path_visible(self) -> None:
        service = SubjectWorkflowApiService()
        root = Path(self.tempdir.name) / "uploaded-dst-root"
        workspace = Path(__file__).resolve().parents[2]
        launch_workstation_session(
            root_path=root,
            workspace_path=workspace,
            attach_default_skill_home=False,
            initial_task="Exercise uploaded markdown ingress through the DST publication path.",
            allow_direct_llm_decomposition=True,
        )
        staged_upload = root / "uploads" / "flutter-shell-a" / "City bus prose v10.md"
        staged_upload.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(workspace / "dst" / "City bus prose v10.md", staged_upload)
        placeholder = service.list_subjects(root_path=root)[0]

        ingress = service.apply_action(
            root_path=root,
            subject_id=placeholder.key,
            phase="research",
            action_key="use_markdown_ingress",
            markdown_selected_path=str(staged_upload),
            markdown_status_text="Markdown upload staged.",
            markdown_busy=True,
        )

        subject_id = ingress.preferred_subject_key
        self.assertTrue(subject_id)
        self.assertEqual(ingress.phase_view.scenario.subject_id, subject_id)

        phase = ingress.phase_view.phase
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "suggest_transformation_constructs",
            "refresh_review_composition",
        ):
            outcome = service.apply_action(
                root_path=root,
                subject_id=subject_id,
                phase=phase,
                action_key=action_key,
            )
            phase = outcome.phase_view.phase

        draft_view = service.get_phase_view(
            root_path=root,
            subject_id=subject_id,
            phase="draft",
        )
        self.assertEqual(draft_view.current_step.actions[0].label, "Start Decision Analysis")

        start = service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="draft",
            action_key="create_decision_frame_from_selected_draft_item",
        )
        self.assertEqual(start.phase_view.current_step.actions[0].label, "Run Decision Analysis")

        service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="draft",
            action_key="open_draft_model_view",
        )
        draft_panes = service.get_pane_bundle(
            root_path=root,
            subject_id=subject_id,
            phase="draft",
        )
        draft_model = next(pane for pane in draft_panes.panes if pane.key == "draft_scope_tree")
        self.assertTrue(draft_model.items)
        self.assertTrue(
            any(
                any(attribute.label == "lane" and attribute.value for attribute in item.attributes)
                for item in draft_model.items
            )
        )

        review = service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="draft",
            action_key="analyze_decision_frame",
        )
        self.assertEqual(review.phase_view.phase, "review")
        self.assertEqual(review.phase_view.current_step.actions[0].label, "Approve For Report")
        review_panes = service.get_pane_bundle(
            root_path=root,
            subject_id=subject_id,
            phase="review",
        )
        review_detail = next(pane for pane in review_panes.panes if pane.key == "review_scope_detail")
        self.assertEqual(review_detail.rows[0].label, "Selection")

        publication_ready = service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="review",
            action_key="approve_review",
        )
        self.assertEqual(
            publication_ready.phase_view.current_step.actions[0].label,
            "Publication: Lock Report Inputs",
        )
        publication_view = service.get_phase_view(
            root_path=root,
            subject_id=subject_id,
            phase="publication",
        )
        self.assertEqual(publication_view.current_step.actions[0].label, "Lock Report Inputs")

        build_ready = service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="publication",
            action_key="lock_publication",
        )
        self.assertEqual(build_ready.phase_view.phase, "publication")
        self.assertEqual(build_ready.phase_view.current_step.actions[0].label, "Build Report")

        built = service.apply_action(
            root_path=root,
            subject_id=subject_id,
            phase="publication",
            action_key="build_report",
        )
        self.assertIn("Report build completed", built.status_text)
        publication_built_view = service.get_phase_view(
            root_path=root,
            subject_id=subject_id,
            phase="publication",
        )
        self.assertEqual(publication_built_view.current_step.actions[0].label, "Open Release Folder")
        self.assertEqual(publication_built_view.current_step.actions[1].label, "Preview report.pdf")

    def test_subject_workflow_api_keeps_empty_optional_routing_fields_empty(self) -> None:
        service = SubjectWorkflowApiService()
        with mock.patch(
            "workstation.subject.service.subject_workflow_api.apply_subject_action",
            return_value=SubjectActionResult(
                status_text="No explicit routing returned.",
                timeline_text="Stayed on the current phase.",
                next_phase=None,
                next_tab=None,
            ),
        ):
            outcome = service.apply_action(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
                action_key="goto_chat",
            )

        self.assertEqual(outcome.next_phase, "")
        self.assertEqual(outcome.next_tab, "")

    def test_subject_workflow_api_streams_client_view_changes_back_to_the_same_session(self) -> None:
        service = SubjectWorkflowApiService()
        client = InProcessSubjectWorkflowClient(service=service, client_session_id="watch-client-a")

        watch = client.watch_subject_workflow(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )
        initial_event = next(watch)
        self.assertEqual(initial_event.event_kind, "initial")

        payload = json.loads(
            client.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
        )
        payload["research_source_cursor"] = 4
        client.put_client_progress_json(
            root_path=self.root,
            subject_id=self.subject_id,
            progress_json=json.dumps(payload),
        )

        changed_event = next(watch)
        self.assertEqual(changed_event.event_kind, "subject_workflow_client_view_changed")
        self.assertEqual(changed_event.channel_key, f"subject/{self.subject_id}/research")
        self.assertEqual(changed_event.sequence, 1)
        self.assertNotEqual(changed_event.progress_fingerprint, initial_event.progress_fingerprint)
        watch.close()

    def test_subject_workflow_api_keeps_client_progress_view_state_isolated_by_session(self) -> None:
        service = SubjectWorkflowApiService()
        client_a = InProcessSubjectWorkflowClient(service=service, client_session_id="client-a")
        client_b = InProcessSubjectWorkflowClient(service=service, client_session_id="client-b")

        progress_a = json.loads(
            client_a.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
        )
        self.assertEqual(progress_a.get("itemize_cursor"), 0)
        progress_a["itemize_cursor"] = 9
        progress_a["draft_selected_review_item_id"] = "review-item-a"
        client_a.put_client_progress_json(
            root_path=self.root,
            subject_id=self.subject_id,
            progress_json=json.dumps(progress_a),
        )

        reloaded_a = json.loads(
            client_a.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
        )
        reloaded_b = json.loads(
            client_b.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
        )

        self.assertEqual(reloaded_a.get("itemize_cursor"), 9)
        self.assertEqual(reloaded_a.get("draft_selected_review_item_id"), "review-item-a")
        self.assertEqual(reloaded_b.get("itemize_cursor"), 0)
        self.assertEqual(reloaded_b.get("draft_selected_review_item_id"), "")

    def test_subject_workflow_api_does_not_persist_pure_client_view_changes(self) -> None:
        service = SubjectWorkflowApiService()
        client = InProcessSubjectWorkflowClient(service=service, client_session_id="client-a")

        progress = new_subject_progress()
        progress.context_opened = True
        persist_subject_progress(self.root, self.subject_id, progress)
        progress_path = subject_progress_path(self.root, self.subject_id)
        original_text = progress_path.read_text(encoding="utf-8")

        payload = json.loads(
            client.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
        )
        payload["itemize_cursor"] = 7
        payload["draft_selected_review_item_id"] = "review-item-a"
        client.put_client_progress_json(
            root_path=self.root,
            subject_id=self.subject_id,
            progress_json=json.dumps(payload),
        )

        self.assertEqual(progress_path.read_text(encoding="utf-8"), original_text)

    def test_subject_workflow_grpc_service_round_trips_subject_queries_and_actions(self) -> None:
        collection = new_source_collection(
            subject_id=self.subject_id,
            title="Transport Contract Sources",
            description="Proves typed pane items cross the transport boundary.",
        )
        persist_source_collection(self.root, collection)
        progress = new_subject_progress()
        progress.research_selected_source_collection_id = collection.collection_id
        persist_subject_progress(self.root, self.subject_id, progress)
        server = build_subject_workflow_grpc_server(service=SubjectWorkflowApiService())
        port = server.add_insecure_port("127.0.0.1:0")
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            stub = subject_workflow_pb2_grpc.SubjectWorkflowServiceStub(channel)

            list_response = stub.ListSubjects(
                subject_workflow_pb2.ListSubjectsRequest(root_path=str(self.root))
            )
            self.assertEqual(len(list_response.subjects), 1)
            self.assertEqual(list_response.subjects[0].subject_id, self.subject_id)

            view_response = stub.GetSubjectPhaseView(
                subject_workflow_pb2.GetSubjectPhaseViewRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                )
            )
            self.assertEqual(view_response.view.phase_title, "Gather")
            self.assertGreater(len(view_response.view.current_step.actions), 0)

            bundle_response = stub.GetSubjectControlBundle(
                subject_workflow_pb2.GetSubjectControlBundleRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                )
            )
            self.assertEqual(bundle_response.bundle.phase, "research")
            self.assertTrue(
                any(spec.key == "research_source_collection" for spec in bundle_response.bundle.selects)
            )
            self.assertTrue(
                any(spec.key == "research_source_revision_history" for spec in bundle_response.bundle.tables)
            )

            pane_bundle_response = stub.GetSubjectPaneBundle(
                subject_workflow_pb2.GetSubjectPaneBundleRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                )
            )
            self.assertEqual(pane_bundle_response.bundle.phase, "research")
            self.assertTrue(
                any(pane.key == "research_sources" for pane in pane_bundle_response.bundle.panes)
            )
            self.assertTrue(
                any(pane.key == "research_target" for pane in pane_bundle_response.bundle.panes)
            )
            self.assertTrue(
                any(pane.key == "research_observation" and pane.is_structured_table for pane in pane_bundle_response.bundle.panes)
            )
            research_target = next(
                pane for pane in pane_bundle_response.bundle.panes if pane.key == "research_target"
            )
            self.assertFalse(research_target.is_structured_table)
            self.assertTrue(research_target.lines)
            self.assertFalse(research_target.rows)
            source_pane = next(
                pane for pane in pane_bundle_response.bundle.panes if pane.key == "research_sources"
            )
            source_item = next(
                item for item in source_pane.items if item.entry_id == collection.collection_id
            )
            self.assertEqual(source_item.entry_kind, "source_collection")
            self.assertEqual(source_item.label, "Transport Contract Sources [0 sources, no saved query]")
            self.assertTrue(source_item.selected)

            snapshot_response = stub.GetSubjectWorkflowSnapshot(
                subject_workflow_pb2.GetSubjectWorkflowSnapshotRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                )
            )
            self.assertTrue(snapshot_response.trace_id)
            self.assertTrue(snapshot_response.parent_id)
            self.assertEqual(snapshot_response.snapshot.phase_view.phase, "research")
            self.assertEqual(snapshot_response.snapshot.control_bundle.phase, "research")
            self.assertEqual(snapshot_response.snapshot.pane_bundle.phase, "research")

            watch_stream = stub.WatchSubjectWorkflow(
                subject_workflow_pb2.WatchSubjectWorkflowRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                )
            )
            initial_update = next(watch_stream)
            self.assertEqual(initial_update.event_kind, "initial")
            self.assertEqual(initial_update.channel_key, f"subject/{self.subject_id}/research")
            self.assertEqual(int(initial_update.sequence), 0)
            self.assertTrue(initial_update.snapshot_version)
            self.assertTrue(initial_update.progress_fingerprint)
            self.assertTrue(initial_update.trace_id)
            self.assertTrue(initial_update.parent_id)

            action_response = stub.ApplySubjectAction(
                subject_workflow_pb2.ApplySubjectActionRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                    action_key=view_response.view.current_step.actions[0].key,
                )
            )
            self.assertTrue(action_response.result.status_text)
            self.assertTrue(action_response.view.current_step.title)
            self.assertTrue(action_response.trace_id)
            self.assertTrue(action_response.parent_id)

            changed_update = next(watch_stream)
            self.assertEqual(changed_update.event_kind, "subject_workflow_changed")
            self.assertEqual(changed_update.channel_key, f"subject/{self.subject_id}/research")
            self.assertEqual(int(changed_update.sequence), 1)
            self.assertTrue(changed_update.snapshot_version)
            self.assertTrue(changed_update.progress_fingerprint)
            self.assertTrue(changed_update.trace_id)
            self.assertTrue(changed_update.parent_id)
            self.assertTrue(changed_update.snapshot.phase_view.current_step.title)

            client = GrpcSubjectWorkflowClient(channel)
            grpc_snapshot = client.get_snapshot(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
            )
            self.assertEqual(grpc_snapshot.phase_view.phase, "research")
            grpc_watch = client.watch_subject_workflow(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
            )
            grpc_initial = next(grpc_watch)
            self.assertEqual(grpc_initial.event_kind, "initial")
            self.assertEqual(grpc_initial.channel_key, f"subject/{self.subject_id}/research")
            self.assertEqual(grpc_initial.sequence, 0)
            self.assertTrue(grpc_initial.snapshot_version)
            self.assertTrue(grpc_initial.progress_fingerprint)
            client.apply_action(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
                action_key=grpc_snapshot.phase_view.current_step.actions[0].key,
            )
            grpc_changed = next(grpc_watch)
            self.assertEqual(grpc_changed.event_kind, "subject_workflow_changed")
            self.assertEqual(grpc_changed.channel_key, f"subject/{self.subject_id}/research")
            self.assertEqual(grpc_changed.sequence, 1)
            self.assertTrue(grpc_changed.snapshot_version)
            self.assertTrue(grpc_changed.progress_fingerprint)
            watch_stream.cancel()
        finally:
            channel.close()
            server.stop(grace=None).wait()

    def test_subject_workflow_grpc_service_keeps_client_progress_view_state_isolated_by_session(self) -> None:
        server = build_subject_workflow_grpc_server(service=SubjectWorkflowApiService())
        port = server.add_insecure_port("127.0.0.1:0")
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            client_a = GrpcSubjectWorkflowClient(channel, client_session_id="grpc-client-a")
            client_b = GrpcSubjectWorkflowClient(channel, client_session_id="grpc-client-b")

            progress_a = json.loads(
                client_a.get_client_progress_json(
                    root_path=self.root,
                    subject_id=self.subject_id,
                )
            )
            progress_a["research_source_cursor"] = 3
            progress_a["research_selected_staged_source_id"] = "source-a"
            client_a.put_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
                progress_json=json.dumps(progress_a),
            )

            reloaded_a = json.loads(
                client_a.get_client_progress_json(
                    root_path=self.root,
                    subject_id=self.subject_id,
                )
            )
            reloaded_b = json.loads(
                client_b.get_client_progress_json(
                    root_path=self.root,
                    subject_id=self.subject_id,
                )
            )

            self.assertEqual(reloaded_a.get("research_source_cursor"), 3)
            self.assertEqual(reloaded_a.get("research_selected_staged_source_id"), "source-a")
            self.assertEqual(reloaded_b.get("research_source_cursor"), 0)
            self.assertEqual(reloaded_b.get("research_selected_staged_source_id"), "")
        finally:
            channel.close()
            server.stop(grace=None).wait()

    def test_subject_workflow_grpc_service_supports_unix_socket_clients(self) -> None:
        server = build_subject_workflow_grpc_server(service=SubjectWorkflowApiService())
        socket_path = self.root / "subject-workflow.sock"
        bound = bind_subject_workflow_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        client = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="unix-client-a",
        )
        try:
            snapshot = client.get_snapshot(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
            )
            self.assertEqual(snapshot.phase_view.phase, "research")

            progress_json = client.get_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
            )
            payload = json.loads(progress_json)
            payload["research_source_cursor"] = 2
            updated_json = client.put_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
                progress_json=json.dumps(payload),
            )
            updated_payload = json.loads(updated_json)
            self.assertEqual(updated_payload.get("research_source_cursor"), 2)
        finally:
            client.close()
            server.stop(grace=None).wait()
