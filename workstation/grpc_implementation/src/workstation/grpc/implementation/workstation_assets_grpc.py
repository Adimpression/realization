# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import mimetypes
from urllib.parse import quote

import grpc

from realized_core_semantics.semantic_text import collapse_ws
from workstation.contracts.subject import WorkstationArtifactRefView
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.grpc.definitions import workstation_assets_pb2, workstation_assets_pb2_grpc
from workstation.grpc.implementation.workstation_artifact_http import WorkstationArtifactDownloadRegistry
from workstation.grpc.implementation.workstation_bootstrap_grpc import WorkstationRootRegistry


def _registered_trace_fields(
    *,
    message_kind: str,
    prefix: str,
    parent_id: str = "",
    components: tuple[object, ...] = (),
) -> tuple[str, str]:
    trace_id = (
        derived_trace_id(prefix, *(components or (parent_id or new_trace_id(prefix),)))
        if components
        else new_trace_id(prefix)
    )
    return register_message_trace(
        trace_id=trace_id,
        parent_id=parent_id,
        message_kind=message_kind,
    )


def _sanitize_session_fragment(value: str, *, fallback: str) -> str:
    normalized = collapse_ws(value)
    slug = "".join(character if character.isalnum() else "-" for character in normalized).strip("-").casefold()
    return slug or fallback


def _safe_filename(value: str, *, fallback: str = "upload.md") -> str:
    candidate = Path(str(value or "")).name
    normalized = collapse_ws(candidate)
    if not normalized:
        return fallback
    return normalized


def _path_is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_artifact_ref_views(
    root_path: Path,
    client_session_id: str,
    server_paths: tuple[str, ...] | list[str],
    *,
    root_registry: WorkstationRootRegistry,
    artifact_download_registry: WorkstationArtifactDownloadRegistry | None = None,
    download_base_url: str = "",
    allow_local_path_open: bool = True,
) -> tuple[WorkstationArtifactRefView, ...]:
    del client_session_id
    resolved_root = root_registry.resolve_root_path(root_path)
    normalized_base_url = str(download_base_url or "").rstrip("/")
    items: list[WorkstationArtifactRefView] = []
    for server_path in server_paths:
        raw_path = Path(str(server_path or "")).expanduser()
        candidate_path = raw_path if raw_path.is_absolute() else resolved_root / raw_path
        resolved_path = candidate_path.resolve()
        mime_type, _ = mimetypes.guess_type(str(resolved_path))
        is_directory = resolved_path.exists() and resolved_path.is_dir()
        label = resolved_path.name or resolved_path.as_posix() or "artifact"
        download_url = ""
        if (
            artifact_download_registry is not None
            and normalized_base_url
            and resolved_path.exists()
            and _path_is_within_root(resolved_path, resolved_root)
        ):
            token = artifact_download_registry.register(resolved_path)
            download_name = f"{label}.zip" if is_directory else label
            download_url = f"{normalized_base_url}/artifacts/{token}/{quote(download_name)}"
        items.append(
            WorkstationArtifactRefView(
                label=label,
                server_path=str(resolved_path),
                mime_type=mime_type or ("inode/directory" if is_directory else "application/octet-stream"),
                download_url=download_url,
                can_open_locally=bool(allow_local_path_open and resolved_path.exists()),
            )
        )
    return tuple(items)


def _artifact_ref_message(view: WorkstationArtifactRefView) -> workstation_assets_pb2.ArtifactRef:
    return workstation_assets_pb2.ArtifactRef(
        label=view.label,
        server_path=view.server_path,
        mime_type=view.mime_type,
        download_url=view.download_url,
        can_open_locally=bool(view.can_open_locally),
    )


class WorkstationAssetGrpcService(workstation_assets_pb2_grpc.WorkstationAssetServiceServicer):
    def __init__(
        self,
        *,
        root_registry: WorkstationRootRegistry | None = None,
        artifact_download_registry: WorkstationArtifactDownloadRegistry | None = None,
        download_base_url: str = "",
        allow_local_path_open: bool = True,
    ) -> None:
        self._root_registry = root_registry or WorkstationRootRegistry()
        self._artifact_download_registry = artifact_download_registry
        self._download_base_url = str(download_base_url or "")
        self._allow_local_path_open = bool(allow_local_path_open)

    def StageMarkdownUpload(
        self,
        request: workstation_assets_pb2.StageMarkdownUploadRequest,
        context: grpc.ServicerContext,
    ) -> workstation_assets_pb2.StageMarkdownUploadResponse:
        del context
        resolved_root = self._root_registry.resolve_root_path(request.root_path)
        session_fragment = _sanitize_session_fragment(request.client_session_id, fallback="client")
        filename = _safe_filename(request.filename, fallback="upload.md")
        destination = resolved_root / "uploads" / session_fragment / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = bytes(request.content or b"")
        destination.write_bytes(payload)
        digest = sha256(payload).hexdigest()
        parent_id = new_trace_id("asset-stage-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="StageMarkdownUploadResponse",
            prefix="asset-stage-response",
            parent_id=parent_id,
            components=(parent_id, resolved_root, request.client_session_id, filename, digest),
        )
        return workstation_assets_pb2.StageMarkdownUploadResponse(
            staged_path=str(destination),
            display_name=filename,
            sha256=digest,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def ResolveArtifacts(
        self,
        request: workstation_assets_pb2.ResolveArtifactsRequest,
        context: grpc.ServicerContext,
    ) -> workstation_assets_pb2.ResolveArtifactsResponse:
        del context
        artifacts = resolve_artifact_ref_views(
            Path(request.root_path),
            request.client_session_id,
            tuple(request.server_paths),
            root_registry=self._root_registry,
            artifact_download_registry=self._artifact_download_registry,
            download_base_url=self._download_base_url,
            allow_local_path_open=self._allow_local_path_open,
        )
        parent_id = new_trace_id("asset-resolve-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="ResolveArtifactsResponse",
            prefix="asset-resolve-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, request.client_session_id, *(item.server_path for item in artifacts)),
        )
        return workstation_assets_pb2.ResolveArtifactsResponse(
            artifacts=[_artifact_ref_message(item) for item in artifacts],
            trace_id=trace_id,
            parent_id=parent_id,
        )
