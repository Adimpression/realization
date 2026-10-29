# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from concurrent import futures
from pathlib import Path
from typing import Iterable

import grpc

from workstation.grpc.definitions import (
    subject_workflow_pb2_grpc,
    workstation_assets_pb2_grpc,
    workstation_bootstrap_pb2_grpc,
    workstation_shell_pb2_grpc,
)
from workstation.grpc.implementation.subject_workflow_grpc import SubjectWorkflowGrpcService
from workstation.grpc.implementation.workstation_artifact_http import WorkstationArtifactDownloadRegistry
from workstation.grpc.implementation.workstation_assets_grpc import (
    WorkstationAssetGrpcService,
    resolve_artifact_ref_views,
)
from workstation.grpc.implementation.workstation_bootstrap_grpc import (
    ServedWorkstationRoot,
    WorkstationBootstrapGrpcService,
    WorkstationRootRegistry,
)
from workstation.grpc.implementation.workstation_shell_grpc import WorkstationShellGrpcService
from workstation.runtime.core.session import launch_workstation_session
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.shell.core.workstation_shell_api import WorkstationShellApiService
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService
from workstation.subject.service.client_sessions import WorkstationClientSessionRegistry


def _ensure_hosted_workstation_root(
    root_path: Path,
    *,
    root_registry: WorkstationRootRegistry,
) -> Path:
    resolved_root = root_registry.resolve_root_path(root_path)
    served_root = root_registry.descriptor_for_path(resolved_root)
    if served_root is None:
        return resolved_root
    if (resolved_root / "SESSION.json").is_file():
        return resolved_root
    launch_workstation_session(
        root_path=resolved_root,
        workspace_path=resolved_root,
        workspace_name=served_root.workspace_name or resolved_root.name,
        initial_task="",
    )
    return resolved_root


def build_workstation_grpc_server(
    *,
    max_workers: int = 16,
    client_sessions: WorkstationClientSessionRegistry | None = None,
    served_roots: Iterable[ServedWorkstationRoot] = (),
    artifact_download_base_url: str = "",
    artifact_download_registry: WorkstationArtifactDownloadRegistry | None = None,
    allow_local_path_open: bool = True,
) -> grpc.Server:
    shared_sessions = client_sessions or WorkstationClientSessionRegistry()
    root_registry = WorkstationRootRegistry(served_roots)
    download_registry = artifact_download_registry or WorkstationArtifactDownloadRegistry()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    root_initializer = lambda root_path: _ensure_hosted_workstation_root(root_path, root_registry=root_registry)
    subject_workflow_pb2_grpc.add_SubjectWorkflowServiceServicer_to_server(
        SubjectWorkflowGrpcService(
            service=SubjectWorkflowApiService(
                client_sessions=shared_sessions,
                host_actions=RuntimeSubjectWorkflowHostActions(),
            ),
            artifact_ref_resolver=lambda root_path, client_session_id, server_paths: resolve_artifact_ref_views(
                root_path,
                client_session_id,
                server_paths,
                root_registry=root_registry,
                artifact_download_registry=download_registry,
                download_base_url=artifact_download_base_url,
                allow_local_path_open=allow_local_path_open,
            ),
            root_initializer=root_initializer,
        ),
        server,
    )
    workstation_shell_pb2_grpc.add_WorkstationShellServiceServicer_to_server(
        WorkstationShellGrpcService(
            service=WorkstationShellApiService(client_sessions=shared_sessions),
            root_initializer=root_initializer,
        ),
        server,
    )
    workstation_bootstrap_pb2_grpc.add_WorkstationBootstrapServiceServicer_to_server(
        WorkstationBootstrapGrpcService(root_registry=root_registry),
        server,
    )
    workstation_assets_pb2_grpc.add_WorkstationAssetServiceServicer_to_server(
        WorkstationAssetGrpcService(
            root_registry=root_registry,
            artifact_download_registry=download_registry,
            download_base_url=artifact_download_base_url,
            allow_local_path_open=allow_local_path_open,
        ),
        server,
    )
    return server


def bind_workstation_grpc_server_unix_socket(
    server: grpc.Server,
    *,
    socket_path: Path,
) -> int:
    resolved = Path(socket_path).expanduser().resolve()
    if resolved.exists():
        resolved.unlink()
    return server.add_insecure_port(f"unix://{resolved}")


def bind_workstation_grpc_server_tcp(
    server: grpc.Server,
    *,
    host: str,
    port: int,
) -> int:
    return server.add_insecure_port(f"{host}:{int(port)}")
