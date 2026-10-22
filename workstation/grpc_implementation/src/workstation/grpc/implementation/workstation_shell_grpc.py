# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from concurrent import futures
from pathlib import Path
from typing import Callable

import grpc

from workstation.contracts.shell import (
    WorkstationChatSnapshotView,
    WorkstationShellTextView,
    WorkstationShellWatchEventView,
)
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.grpc.definitions import workstation_shell_pb2, workstation_shell_pb2_grpc
from workstation.shell.core.workstation_shell_api import WorkstationShellApiService


def _message_message_from_view(view) -> workstation_shell_pb2.WorkstationChatMessage:
    return workstation_shell_pb2.WorkstationChatMessage(
        role=view.role,
        content=view.content,
        timestamp_epoch_ms=int(getattr(view, "timestamp_epoch_ms", 0) or 0),
        message_id=str(getattr(view, "message_id", "") or ""),
        turn_id=str(getattr(view, "turn_id", "") or ""),
        sequence=int(getattr(view, "sequence", 0) or 0),
    )


def _chat_snapshot_message_from_view(view: WorkstationChatSnapshotView) -> workstation_shell_pb2.ChatSnapshotResponse:
    return workstation_shell_pb2.ChatSnapshotResponse(
        messages=[_message_message_from_view(item) for item in view.messages],
        session_status=view.session_status,
        snapshot_version=view.snapshot_version,
        progress_fingerprint=view.progress_fingerprint,
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _text_view_message_from_view(view: WorkstationShellTextView) -> workstation_shell_pb2.ShellTextView:
    return workstation_shell_pb2.ShellTextView(
        text=view.text,
        snapshot_version=view.snapshot_version,
        progress_fingerprint=view.progress_fingerprint,
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _watch_event_message_from_view(view: WorkstationShellWatchEventView) -> workstation_shell_pb2.WorkstationShellWatchEvent:
    message = workstation_shell_pb2.WorkstationShellWatchEvent(
        event_kind=view.event_kind,
        channel_key=view.channel_key,
        sequence=int(view.sequence or 0),
        snapshot_version=view.snapshot_version,
        progress_fingerprint=view.progress_fingerprint,
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )
    if view.chat_snapshot is not None:
        message.chat_snapshot.CopyFrom(_chat_snapshot_message_from_view(view.chat_snapshot))
    elif view.activity_view is not None:
        message.activity_view.CopyFrom(_text_view_message_from_view(view.activity_view))
    elif view.permissions_view is not None:
        message.permissions_view.CopyFrom(_text_view_message_from_view(view.permissions_view))
    elif view.skills_view is not None:
        message.skills_view.CopyFrom(_text_view_message_from_view(view.skills_view))
    elif view.status_view is not None:
        message.status_view.CopyFrom(_text_view_message_from_view(view.status_view))
    return message


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


class WorkstationShellGrpcService(workstation_shell_pb2_grpc.WorkstationShellServiceServicer):
    def __init__(
        self,
        service: WorkstationShellApiService | None = None,
        *,
        root_initializer: Callable[[Path], Path] | None = None,
    ) -> None:
        self._service = service or WorkstationShellApiService()
        self._root_initializer = root_initializer

    def _ready_root_path(self, root_path: str | Path) -> Path:
        resolved = Path(root_path).expanduser().resolve()
        if self._root_initializer is not None:
            return self._root_initializer(resolved)
        return resolved

    def OpenClientSession(self, request, context):
        client_session_id = self._service.open_client_session(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
        )
        parent_id = new_trace_id("shell-open-session-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="OpenClientSessionResponse",
            prefix="shell-session-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, client_session_id, "open"),
        )
        return workstation_shell_pb2.ClientSessionResponse(
            client_session_id=client_session_id,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def CloseClientSession(self, request, context):
        client_session_id = self._service.close_client_session(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
        )
        parent_id = new_trace_id("shell-close-session-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="CloseClientSessionResponse",
            prefix="shell-session-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, client_session_id, "close"),
        )
        return workstation_shell_pb2.ClientSessionResponse(
            client_session_id=client_session_id,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def GetChatSnapshot(self, request, context):
        return _chat_snapshot_message_from_view(
            self._service.get_chat_snapshot(
                root_path=self._ready_root_path(request.root_path),
                client_session_id=request.client_session_id,
                limit=int(request.limit or 0),
            )
        )

    def PrepareChatPromptTarget(self, request, context):
        view = self._service.prepare_chat_prompt_target(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
            prompt_text=request.prompt_text,
        )
        return workstation_shell_pb2.PrepareChatPromptTargetResponse(
            kind=view.kind,
            prepared_prompt=view.prepared_prompt,
            shell_text=view.shell_text,
            target_kind=view.target_kind,
            routing_metadata_json=view.routing_metadata_json,
            trace_id=view.trace_id,
            parent_id=view.parent_id,
        )

    def SubmitChatInput(self, request, context):
        view = self._service.submit_chat_input(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
            prompt_text=request.prompt_text,
            model=request.model or None,
            max_tool_rounds=int(request.max_tool_rounds or 0),
            force_llm_only=bool(request.force_llm_only),
            interaction_mode=request.interaction_mode or "normal",
            governed_treatment=request.governed_treatment or "independent",
            governed_parent_run_id=request.governed_parent_run_id,
            governed_llm_policy=request.governed_llm_policy or "auto",
            governed_max_steps=(
                int(request.governed_max_steps)
                if request.HasField("governed_max_steps")
                else 256
            ),
        )
        return workstation_shell_pb2.SubmitChatInputResponse(
            assistant_text=view.assistant_text,
            messages=[_message_message_from_view(item) for item in view.messages],
            fulfilled_by=view.fulfilled_by,
            rounds=int(view.rounds or 0),
            tool_receipts_json=view.tool_receipts_json,
            status_text=view.status_text,
            snapshot_version=view.snapshot_version,
            progress_fingerprint=view.progress_fingerprint,
            trace_id=view.trace_id,
            parent_id=view.parent_id,
            turn_id=view.turn_id,
            run_id=view.run_id,
            run_outcome=view.run_outcome,
            checkpoint_path=view.checkpoint_path,
        )

    def AppendShellTurn(self, request, context):
        snapshot = self._service.append_shell_turn(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
            prompt_text=request.prompt_text,
            assistant_text=request.assistant_text,
            assistant_role=request.assistant_role or "shell",
        )
        parent_id = new_trace_id("shell-append-turn-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="AppendShellTurnResponse",
            prefix="shell-append-turn-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, request.prompt_text, request.assistant_text, snapshot.snapshot_version),
        )
        return workstation_shell_pb2.AppendShellTurnResponse(
            snapshot=_chat_snapshot_message_from_view(snapshot),
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def GetActivityView(self, request, context):
        return _text_view_message_from_view(
            self._service.get_activity_view(
                root_path=self._ready_root_path(request.root_path),
                client_session_id=request.client_session_id,
                limit=int(request.limit or 0),
            )
        )

    def GetPermissionsView(self, request, context):
        return _text_view_message_from_view(
            self._service.get_permissions_view(
                root_path=self._ready_root_path(request.root_path),
                client_session_id=request.client_session_id,
            )
        )

    def GetSkillsView(self, request, context):
        return _text_view_message_from_view(
            self._service.get_skills_view(
                root_path=self._ready_root_path(request.root_path),
                client_session_id=request.client_session_id,
                query=request.query,
            )
        )

    def WatchWorkstationShell(self, request, context):
        iterator = self._service.watch_workstation_shell(
            root_path=self._ready_root_path(request.root_path),
            client_session_id=request.client_session_id,
            last_seen_version=request.last_seen_version,
        )
        for event in iterator:
            if context.is_active():
                yield _watch_event_message_from_view(event)
            else:
                break


def build_workstation_shell_grpc_server(
    *,
    service: WorkstationShellApiService | None = None,
    max_workers: int = 8,
) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    workstation_shell_pb2_grpc.add_WorkstationShellServiceServicer_to_server(
        WorkstationShellGrpcService(service=service),
        server,
    )
    return server


def bind_workstation_shell_grpc_server_unix_socket(
    server: grpc.Server,
    *,
    socket_path: Path,
) -> int:
    resolved = Path(socket_path).expanduser().resolve()
    if resolved.exists():
        resolved.unlink()
    return server.add_insecure_port(f"unix://{resolved}")
