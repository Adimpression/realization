# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import asyncio
import json
import tempfile
import threading
import time
import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

import grpc

from learning_context import new_learning_context, persist_learning_context
import workstation.ui.textual.chat_ui as workstation_chat_ui_module
from workstation.ui.textual.chat_ui import _TextualWorkstationChatApp
from workstation.foundation.host.client_sessions import WorkstationClientSessionRegistry
from workstation.contracts.shell import WorkstationSubmitChatInputResultView
from workstation.grpc.definitions import workstation_shell_pb2, workstation_shell_pb2_grpc
from workstation.runtime.core.session import launch_workstation_session
from workstation.subject.service.subject_workflow_client import new_grpc_subject_workflow_client_for_unix_socket
from workstation.grpc.implementation.workstation_grpc_host import (
    bind_workstation_grpc_server_unix_socket,
    build_workstation_grpc_server,
)
from workstation.shell.core.workstation_shell_api import WorkstationShellApiService
from workstation.shell.core.workstation_shell_client import (
    GrpcWorkstationShellClient,
    InProcessWorkstationShellClient,
    new_grpc_workstation_shell_client_for_unix_socket,
)
from workstation.grpc.implementation.workstation_shell_grpc import (
    WorkstationShellGrpcService,
    build_workstation_shell_grpc_server,
)


class WorkstationShellApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        temp_root = Path(self.tempdir.name)
        self.root = temp_root / "root"
        self.workspace = temp_root / "workspace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            attach_default_skill_home=False,
            initial_task="Inspect the workstation boundary.",
        )
        context = new_learning_context(canonical_title="Transit Modernization")
        persist_learning_context(self.root, context)
        self.subject_id = context.subject_id

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_in_process_shell_client_serves_snapshot_views_and_help_prompt(self) -> None:
        service = WorkstationShellApiService()
        client = InProcessWorkstationShellClient(service=service, client_session_id="shell-a")

        snapshot = client.get_chat_snapshot(root_path=self.root)
        self.assertTrue(snapshot.context.workspace_root)
        self.assertEqual(snapshot.session_status, "ready")

        activity_view = client.get_activity_view(root_path=self.root, limit=20)
        permissions_view = client.get_permissions_view(root_path=self.root)
        skills_view = client.get_skills_view(root_path=self.root)
        self.assertTrue(activity_view.snapshot_version)
        self.assertTrue(permissions_view.snapshot_version)
        self.assertTrue(skills_view.snapshot_version)

        result = client.submit_chat_input(root_path=self.root, prompt_text="/help")
        self.assertEqual(result.fulfilled_by, "shell.help")
        self.assertTrue(any(message.role == "shell" for message in result.messages))

    def test_grpc_shell_service_round_trips_snapshot_and_help_prompt(self) -> None:
        server = build_workstation_shell_grpc_server(service=WorkstationShellApiService())
        port = server.add_insecure_port("127.0.0.1:0")
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        client = GrpcWorkstationShellClient(channel, client_session_id="grpc-shell-a")
        stub = workstation_shell_pb2_grpc.WorkstationShellServiceStub(channel)
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            raw_snapshot = stub.GetChatSnapshot(
                workstation_shell_pb2.ChatSnapshotRequest(
                    root_path=str(self.root),
                    client_session_id="grpc-shell-a",
                    limit=120,
                )
            )
            self.assertTrue(raw_snapshot.trace_id)
            self.assertTrue(raw_snapshot.parent_id)
            snapshot = client.get_chat_snapshot(root_path=self.root)
            self.assertEqual(snapshot.session_status, "ready")
            raw_result = stub.SubmitChatInput(
                workstation_shell_pb2.SubmitChatInputRequest(
                    root_path=str(self.root),
                    client_session_id="grpc-shell-a",
                    prompt_text="/help",
                )
            )
            self.assertTrue(raw_result.trace_id)
            self.assertTrue(raw_result.parent_id)
            result = client.submit_chat_input(root_path=self.root, prompt_text="/help")
            self.assertEqual(result.fulfilled_by, "shell.help")
            self.assertGreaterEqual(len(result.messages), len(snapshot.messages))
        finally:
            client.close()
            server.stop(grace=None).wait()

    def test_grpc_governed_step_limit_distinguishes_omitted_from_zero(self) -> None:
        service = mock.create_autospec(WorkstationShellApiService, instance=True)
        service.submit_chat_input.return_value = WorkstationSubmitChatInputResultView(
            assistant_text="",
            messages=(),
            fulfilled_by="governed_reduction",
            rounds=0,
            tool_receipts_json="[]",
            status_text="",
            snapshot_version="",
            progress_fingerprint="",
        )
        grpc_service = WorkstationShellGrpcService(service=service)

        grpc_service.SubmitChatInput(
            workstation_shell_pb2.SubmitChatInputRequest(root_path=str(self.root)),
            None,
        )
        self.assertEqual(
            256,
            service.submit_chat_input.call_args.kwargs["governed_max_steps"],
        )

        explicit_zero = workstation_shell_pb2.SubmitChatInputRequest(
            root_path=str(self.root),
            governed_max_steps=0,
        )
        self.assertTrue(explicit_zero.HasField("governed_max_steps"))
        grpc_service.SubmitChatInput(explicit_zero, None)
        self.assertEqual(
            0,
            service.submit_chat_input.call_args.kwargs["governed_max_steps"],
        )

    def test_combined_workstation_grpc_host_supports_unix_socket_clients(self) -> None:
        shared_sessions = WorkstationClientSessionRegistry()
        server = build_workstation_grpc_server(client_sessions=shared_sessions)
        socket_path = self.root / "workstation.sock"
        bound = bind_workstation_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        shell_client = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="unix-shell-a",
        )
        subject_client = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="unix-shell-a",
        )
        try:
            chat_snapshot = shell_client.get_chat_snapshot(root_path=self.root)
            self.assertEqual(chat_snapshot.session_status, "ready")

            subject_snapshot = subject_client.get_snapshot(
                root_path=self.root,
                subject_id=self.subject_id,
                phase="research",
            )
            self.assertEqual(subject_snapshot.phase_view.phase, "research")
        finally:
            shell_client.close()
            subject_client.close()
            server.stop(grace=None).wait()

    def test_shell_transcript_is_shared_while_subject_view_state_stays_session_scoped(self) -> None:
        shared_sessions = WorkstationClientSessionRegistry()
        server = build_workstation_grpc_server(client_sessions=shared_sessions)
        socket_path = self.root / "workstation-shared.sock"
        bound = bind_workstation_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        shell_client_a = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="client-a",
        )
        shell_client_b = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="client-b",
        )
        subject_client_a = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="client-a",
        )
        subject_client_b = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="client-b",
        )
        try:
            before_messages = shell_client_b.get_chat_snapshot(root_path=self.root).messages
            shell_client_a.submit_chat_input(root_path=self.root, prompt_text="/help")
            after_messages = shell_client_b.get_chat_snapshot(root_path=self.root).messages
            self.assertGreater(len(after_messages), len(before_messages))

            progress_a = json.loads(
                subject_client_a.get_client_progress_json(
                    root_path=self.root,
                    subject_id=self.subject_id,
                )
            )
            progress_a["research_source_cursor"] = 7
            subject_client_a.put_client_progress_json(
                root_path=self.root,
                subject_id=self.subject_id,
                progress_json=json.dumps(progress_a),
            )
            progress_b = json.loads(
                subject_client_b.get_client_progress_json(
                    root_path=self.root,
                    subject_id=self.subject_id,
                )
            )
            self.assertEqual(progress_b.get("research_source_cursor"), 0)
        finally:
            shell_client_a.close()
            shell_client_b.close()
            subject_client_a.close()
            subject_client_b.close()
            server.stop(grace=None).wait()

    def test_textual_app_accepts_grpc_subject_and_shell_clients(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("Textual is not available")
        shared_sessions = WorkstationClientSessionRegistry()
        server = build_workstation_grpc_server(client_sessions=shared_sessions)
        socket_path = self.root / "workstation-textual.sock"
        bound = bind_workstation_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        shell_client = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="textual-client",
        )
        subject_client = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="textual-client",
        )
        try:
            shell_client.append_shell_turn(
                root_path=self.root,
                prompt_text="/help",
                assistant_text="Boundary hello.",
                assistant_role="shell",
            )
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
                subject_workflow_client=subject_client,
                shell_client=shell_client,
            )
            transcript_entries = app._state.transcript_entries_snapshot()
            self.assertTrue(any("Boundary hello." in entry.text for entry in transcript_entries))
            snapshot = shell_client.get_chat_snapshot(root_path=self.root)
            self.assertTrue(any(message.content == "Boundary hello." for message in snapshot.messages))
        finally:
            shell_client.close()
            subject_client.close()
            server.stop(grace=None).wait()

    def test_textual_grpc_markdown_ingress_uses_canonical_subject_workflow(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("Textual is not available")
        markdown_path = self.workspace / "notes" / "grpc-kinematics.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(
            "# gRPC Kinematics\n\nVelocity is displacement per unit time.\n",
            encoding="utf-8",
        )
        created_context = new_learning_context(canonical_title="gRPC Kinematics")
        shared_sessions = WorkstationClientSessionRegistry()
        server = build_workstation_grpc_server(client_sessions=shared_sessions)
        socket_path = Path("/tmp") / f"wt-md-{time.time_ns()}.sock"
        bound = bind_workstation_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        shell_client = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="textual-grpc-ingress",
        )
        subject_client = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="textual-grpc-ingress",
        )

        def _fake_result(*args, **kwargs):
            del args, kwargs
            persist_learning_context(self.root, created_context)
            return SimpleNamespace(
                status="ok",
                message="Staged markdown source for gRPC Kinematics.",
                payload={
                    "subject_id": created_context.subject_id,
                    "subject_title": created_context.canonical_title,
                    "context_path": str(
                        self.root / "corpus" / created_context.subject_id / "context.json"
                    ),
                    "staged_source_id": "staged_source_grpc_kinematics",
                },
            )

        def _fake_import_result(*args, **kwargs):
            del args, kwargs
            return SimpleNamespace(
                status="ok",
                message="Imported 1 skill from gRPC Kinematics.",
                payload={
                    "subject_id": created_context.subject_id,
                    "report": {
                        "subject_id": created_context.subject_id,
                        "context_path": str(
                            self.root / "corpus" / created_context.subject_id / "context.json"
                        ),
                    },
                    "imported_titles": ["Velocity"],
                    "canonical_export_path": "grpc-kinematics.learned.md",
                },
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
                subject_workflow_client=subject_client,
                shell_client=shell_client,
            )
            with mock.patch(
                "workstation.ui.textual.chat_ui.desktop_select_markdown_files",
                return_value=(markdown_path,),
            ), mock.patch(
                "workstation.subject.core.subject_workflow.workstation_stage_markdown_source_action",
                side_effect=_fake_result,
            ) as stage_markdown_mock, mock.patch(
                "workstation.subject.core.subject_workflow.workstation_import_staged_source_action",
                side_effect=_fake_import_result,
            ) as import_markdown_mock:
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app.on_button_pressed(
                        SimpleNamespace(button=app.query_one("#learn_markdown_button"))
                    )
                    await pilot.pause()
                    await pilot.pause()
                    ingress = str(app.query_one("#learn_ingress_panel").render())
                    self.assertIn("Stage: Imported 1 skill from gRPC Kinematics.", ingress)
                    self.assertEqual(stage_markdown_mock.call_count, 1)
                    self.assertEqual(import_markdown_mock.call_count, 1)

        try:
            asyncio.run(_exercise())
        finally:
            shell_client.close()
            subject_client.close()
            server.stop(grace=None).wait()

    def test_textual_grpc_url_ingress_uses_canonical_subject_workflow(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("Textual is not available")
        created_context = new_learning_context(canonical_title="gRPC URL Demo")
        source_url = "https://example.test/grpc-kinematics"
        shared_sessions = WorkstationClientSessionRegistry()
        server = build_workstation_grpc_server(client_sessions=shared_sessions)
        socket_path = Path("/tmp") / f"wt-url-{time.time_ns()}.sock"
        bound = bind_workstation_grpc_server_unix_socket(server, socket_path=socket_path)
        self.assertGreaterEqual(bound, 0)
        server.start()
        shell_client = new_grpc_workstation_shell_client_for_unix_socket(
            socket_path,
            client_session_id="textual-grpc-url",
        )
        subject_client = new_grpc_subject_workflow_client_for_unix_socket(
            socket_path,
            client_session_id="textual-grpc-url",
        )

        def _fake_result(*args, **kwargs):
            del args, kwargs
            persist_learning_context(self.root, created_context)
            return SimpleNamespace(
                status="ok",
                message="Staged URL source for gRPC URL Demo.",
                payload={
                    "subject_id": created_context.subject_id,
                    "subject_title": "gRPC URL Demo",
                    "context_path": str(
                        self.root / "corpus" / created_context.subject_id / "context.json"
                    ),
                    "capture_report": {
                        "requested_url": source_url,
                        "final_url": source_url,
                        "title": "gRPC URL Demo",
                    },
                },
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
                subject_workflow_client=subject_client,
                shell_client=shell_client,
            )
            with mock.patch(
                "workstation.ui.textual.chat_ui.desktop_prompt_url",
                return_value=source_url,
            ), mock.patch(
                "workstation.subject.core.subject_workflow.workstation_learn_url_action",
                side_effect=_fake_result,
            ) as learn_url_mock:
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app.on_button_pressed(
                        SimpleNamespace(button=app.query_one("#learn_url_button"))
                    )
                    await pilot.pause()
                    await pilot.pause()
                    ingress = str(app.query_one("#learn_ingress_panel").render())
                    self.assertIn("Stage: Staged URL source for gRPC URL Demo.", ingress)
                    self.assertEqual(learn_url_mock.call_count, 1)

        try:
            asyncio.run(_exercise())
        finally:
            shell_client.close()
            subject_client.close()
            server.stop(grace=None).wait()

    def test_chat_ui_no_longer_uses_local_shell_session_functions(self) -> None:
        source = Path(workstation_chat_ui_module.__file__).read_text()
        self.assertNotIn("load_workstation_session", source)
        self.assertNotIn("prompt_workstation_session", source)
        self.assertNotIn("run_workstation_chat_slash_command", source)
        self.assertNotIn("workstation_chat_transcript_view", source)
        self.assertNotIn("WorkstationShellProjectionBackend", source)

    def test_shell_watch_waits_for_events_instead_of_polling_versions(self) -> None:
        service = WorkstationShellApiService()
        call_counter = {"count": 0}
        stop_event = threading.Event()
        original_snapshot_version = WorkstationShellApiService.watch_workstation_shell.__globals__["_snapshot_version"]

        def _counting_snapshot_version(*args, **kwargs):
            call_counter["count"] += 1
            return original_snapshot_version(*args, **kwargs)

        with mock.patch(
            "workstation.shell.core.workstation_shell_api._snapshot_version",
            side_effect=_counting_snapshot_version,
        ):
            watch = service.watch_workstation_shell(
                root_path=self.root,
                client_session_id="watch-shell",
                poll_interval_seconds=0.05,
                stop_when=stop_event.is_set,
            )
            try:
                initial_events = [next(watch) for _ in range(4)]
                self.assertEqual(initial_events[0].channel_key, "shell/transcript")
                idle_call_count = call_counter["count"]
                received: list[object] = []
                received_event = threading.Event()

                def _await_next() -> None:
                    try:
                        received.append(next(watch))
                    finally:
                        received_event.set()

                waiter = threading.Thread(target=_await_next, daemon=True)
                waiter.start()
                time.sleep(0.2)
                self.assertFalse(received_event.is_set())
                self.assertEqual(call_counter["count"], idle_call_count)

                service.append_shell_turn(
                    root_path=self.root,
                    client_session_id="watch-shell",
                    prompt_text="/help",
                    assistant_text="Event-driven wakeup.",
                    assistant_role="shell",
                )

                self.assertTrue(received_event.wait(timeout=2.0))
                changed_event = received[0]
                self.assertEqual(getattr(changed_event, "channel_key", ""), "shell/transcript")
                self.assertGreater(call_counter["count"], idle_call_count)
            finally:
                stop_event.set()
                try:
                    watch.close()
                except Exception:
                    pass
