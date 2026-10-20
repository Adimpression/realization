# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from concurrent import futures
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.request import urlopen

import grpc

from learning_context import new_learning_context, persist_learning_context
from workstation.foundation.host.client_sessions import WorkstationClientSessionRegistry
from workstation.grpc.definitions import (
    subject_workflow_pb2,
    subject_workflow_pb2_grpc,
    workstation_assets_pb2,
    workstation_assets_pb2_grpc,
    workstation_bootstrap_pb2,
    workstation_bootstrap_pb2_grpc,
)
from workstation.grpc.implementation.subject_workflow_grpc import SubjectWorkflowGrpcService
from workstation.grpc.implementation.workstation_artifact_http import start_workstation_artifact_http_server
from workstation.grpc.implementation.workstation_assets_grpc import resolve_artifact_ref_views
from workstation.grpc.implementation.workstation_bootstrap_grpc import WorkstationRootRegistry
from workstation.grpc.implementation.workstation_grpc_host import (
    bind_workstation_grpc_server_tcp,
    build_workstation_grpc_server,
)
from workstation.runtime.core.session import launch_workstation_session
from workstation.shell.core.workstation_shell_client import GrpcWorkstationShellClient
from workstation.subject.service.subject_workflow_api import (
    SubjectWorkflowActionOutcomeView,
    SubjectWorkflowApiService,
)


class WorkstationBootstrapAndAssetServiceTests(unittest.TestCase):
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
            initial_task="Serve workstation gRPC APIs.",
        )
        context = new_learning_context(canonical_title="Transit Modernization")
        persist_learning_context(self.root, context)
        self.subject_id = context.subject_id

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_combined_tcp_host_lists_roots_stages_markdown_and_serves_artifacts(self) -> None:
        artifact_http = start_workstation_artifact_http_server(host="127.0.0.1", port=0)
        served_roots = WorkstationRootRegistry.from_paths([self.root]).descriptors()
        server = build_workstation_grpc_server(
            client_sessions=WorkstationClientSessionRegistry(),
            served_roots=served_roots,
            artifact_download_base_url=artifact_http.base_url,
            artifact_download_registry=artifact_http.registry,
        )
        port = bind_workstation_grpc_server_tcp(server, host="127.0.0.1", port=0)
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        shell_client = GrpcWorkstationShellClient(channel, client_session_id="grpc-host-a")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            bootstrap_stub = workstation_bootstrap_pb2_grpc.WorkstationBootstrapServiceStub(channel)
            asset_stub = workstation_assets_pb2_grpc.WorkstationAssetServiceStub(channel)

            roots_response = bootstrap_stub.ListWorkstationRoots(
                workstation_bootstrap_pb2.ListWorkstationRootsRequest()
            )
            self.assertEqual(len(roots_response.roots), 1)
            self.assertEqual(Path(roots_response.roots[0].root_path), self.root.resolve())

            upload_response = asset_stub.StageMarkdownUpload(
                workstation_assets_pb2.StageMarkdownUploadRequest(
                    root_path=str(self.root),
                    client_session_id="grpc-host-a",
                    filename="city-bus.md",
                    content=b"# Smart City Travel\n",
                )
            )
            staged_path = Path(upload_response.staged_path)
            self.assertTrue(staged_path.is_file())
            self.assertEqual(staged_path.read_bytes(), b"# Smart City Travel\n")

            report_path = self.root / "build" / "report.pdf"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_bytes(b"%PDF-1.4\nworkstation-test\n")
            resolve_response = asset_stub.ResolveArtifacts(
                workstation_assets_pb2.ResolveArtifactsRequest(
                    root_path=str(self.root),
                    client_session_id="grpc-host-a",
                    server_paths=[str(report_path)],
                )
            )
            self.assertEqual(len(resolve_response.artifacts), 1)
            artifact = resolve_response.artifacts[0]
            self.assertEqual(artifact.server_path, str(report_path.resolve()))
            self.assertTrue(artifact.download_url)
            self.assertEqual(urlopen(artifact.download_url, timeout=5).read(), b"%PDF-1.4\nworkstation-test\n")

            snapshot = shell_client.get_chat_snapshot(root_path=self.root)
            self.assertEqual(snapshot.session_status, "ready")
        finally:
            shell_client.close()
            server.stop(grace=None).wait()
            artifact_http.close()

    def test_combined_tcp_host_auto_initializes_advertised_root_without_session_files(self) -> None:
        blank_root = Path(self.tempdir.name) / "blank-root"
        artifact_http = start_workstation_artifact_http_server(host="127.0.0.1", port=0)
        served_roots = WorkstationRootRegistry.from_paths([blank_root]).descriptors()
        server = build_workstation_grpc_server(
            client_sessions=WorkstationClientSessionRegistry(),
            served_roots=served_roots,
            artifact_download_base_url=artifact_http.base_url,
            artifact_download_registry=artifact_http.registry,
        )
        port = bind_workstation_grpc_server_tcp(server, host="127.0.0.1", port=0)
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        shell_client = GrpcWorkstationShellClient(channel, client_session_id="grpc-host-b")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            subject_stub = subject_workflow_pb2_grpc.SubjectWorkflowServiceStub(channel)
            placeholder = subject_stub.ListSubjects(
                subject_workflow_pb2.ListSubjectsRequest(root_path=str(blank_root))
            ).subjects[0]
            self.assertTrue(placeholder.is_placeholder)
            opened_session_id = shell_client.open_client_session(root_path=blank_root)
            self.assertTrue(opened_session_id)
            self.assertTrue((blank_root / "SESSION.json").is_file())
            snapshot = shell_client.get_chat_snapshot(root_path=blank_root)
            self.assertEqual(snapshot.session_status, "ready")
            self.assertFalse((blank_root / "mounts" / blank_root.name).is_symlink())

            asset_stub = workstation_assets_pb2_grpc.WorkstationAssetServiceStub(channel)
            staged = asset_stub.StageMarkdownUpload(
                workstation_assets_pb2.StageMarkdownUploadRequest(
                    root_path=str(blank_root),
                    client_session_id="grpc-host-b",
                    filename="city-bus.md",
                    content=b"# Smart City Travel\n\nTransit modernization.\n",
                )
            )
            self.assertTrue(Path(staged.staged_path).is_file())

            canonical_outcome = subject_stub.ApplySubjectAction(
                subject_workflow_pb2.ApplySubjectActionRequest(
                    root_path=str(blank_root),
                    subject_id=placeholder.key,
                    phase="research",
                    action_key="use_markdown_ingress",
                    client_session_id="grpc-host-b",
                    projection_context=subject_workflow_pb2.SubjectPhaseProjectionContext(
                        markdown_selected_path=staged.staged_path,
                        markdown_status_text="Markdown upload staged.",
                        markdown_busy=True,
                    ),
                )
            )
            self.assertTrue(canonical_outcome.result.reload_subjects)
            self.assertTrue(canonical_outcome.result.preferred_subject_key)
            self.assertEqual(
                canonical_outcome.view.scenario.subject_id,
                canonical_outcome.result.preferred_subject_key,
            )
        finally:
            shell_client.close()
            server.stop(grace=None).wait()
            artifact_http.close()

    def test_subject_action_response_populates_open_artifacts(self) -> None:
        artifact_http = start_workstation_artifact_http_server(host="127.0.0.1", port=0)
        root_registry = WorkstationRootRegistry.from_paths([self.root])
        report_path = self.root / "build" / "artifact.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("artifact payload\n", encoding="utf-8")

        phase_view = SubjectWorkflowApiService().get_phase_view(
            root_path=self.root,
            subject_id=self.subject_id,
            phase="research",
        )
        mock_service = mock.Mock(spec=SubjectWorkflowApiService)
        mock_service.apply_action.return_value = SubjectWorkflowActionOutcomeView(
            status_text="Artifact opened.",
            timeline_text="Opened a generated artifact.",
            next_phase="research",
            next_tab="research",
            reload_subjects=False,
            open_paths=(str(report_path),),
            preferred_subject_key=self.subject_id,
            phase_view=phase_view,
        )

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
        subject_workflow_pb2_grpc.add_SubjectWorkflowServiceServicer_to_server(
            SubjectWorkflowGrpcService(
                service=mock_service,
                artifact_ref_resolver=lambda root_path, client_session_id, server_paths: resolve_artifact_ref_views(
                    root_path,
                    client_session_id,
                    server_paths,
                    root_registry=root_registry,
                    artifact_download_registry=artifact_http.registry,
                    download_base_url=artifact_http.base_url,
                ),
            ),
            server,
        )
        port = server.add_insecure_port("127.0.0.1:0")
        self.assertGreater(port, 0)
        server.start()
        channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            stub = subject_workflow_pb2_grpc.SubjectWorkflowServiceStub(channel)
            response = stub.ApplySubjectAction(
                subject_workflow_pb2.ApplySubjectActionRequest(
                    root_path=str(self.root),
                    subject_id=self.subject_id,
                    phase="research",
                    action_key="open_generated_artifact",
                    client_session_id="grpc-host-a",
                )
            )
            self.assertEqual(len(response.result.open_artifacts), 1)
            artifact = response.result.open_artifacts[0]
            self.assertEqual(artifact.server_path, str(report_path.resolve()))
            self.assertTrue(artifact.download_url)
            self.assertEqual(urlopen(artifact.download_url, timeout=5).read(), b"artifact payload\n")
        finally:
            channel.close()
            server.stop(grace=None).wait()
            artifact_http.close()
