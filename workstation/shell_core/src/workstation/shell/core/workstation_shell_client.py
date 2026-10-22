# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator
import uuid

import grpc

from semantic_text import collapse_ws
from workstation.contracts.shell import (
    WorkstationChatMessageView,
    WorkstationChatSnapshotView,
    WorkstationPreparedChatPromptTargetView,
    WorkstationShellClient,
    WorkstationShellTextView,
    WorkstationShellWatchEventView,
    WorkstationSubmitChatInputResultView,
)
from workstation.grpc.definitions import workstation_shell_pb2, workstation_shell_pb2_grpc
from workstation.shell.core.workstation_shell_api import WorkstationShellApiService


def _message_view_from_message(message: workstation_shell_pb2.WorkstationChatMessage):
    return WorkstationChatMessageView(
        role=message.role,
        content=message.content,
        timestamp_epoch_ms=int(message.timestamp_epoch_ms or 0),
        message_id=message.message_id,
        turn_id=message.turn_id,
        sequence=int(message.sequence or 0),
    )


def _chat_snapshot_view_from_message(message: workstation_shell_pb2.ChatSnapshotResponse) -> WorkstationChatSnapshotView:
    from workstation.shell.core.chat_shell import workstation_chat_context

    # Context is not serialized yet; rebuild from root on the client side when used in-process.
    return WorkstationChatSnapshotView(
        context=workstation_chat_context(Path(".")),
        messages=tuple(_message_view_from_message(item) for item in message.messages),
        session_status=message.session_status,
        snapshot_version=message.snapshot_version,
        progress_fingerprint=message.progress_fingerprint,
    )


def _text_view_from_message(message: workstation_shell_pb2.ShellTextView) -> WorkstationShellTextView:
    return WorkstationShellTextView(
        text=message.text,
        snapshot_version=message.snapshot_version,
        progress_fingerprint=message.progress_fingerprint,
    )


def _watch_event_view_from_message(
    message: workstation_shell_pb2.WorkstationShellWatchEvent,
) -> WorkstationShellWatchEventView:
    chat_snapshot = _chat_snapshot_view_from_message(message.chat_snapshot) if message.HasField("chat_snapshot") else None
    return WorkstationShellWatchEventView(
        event_kind=message.event_kind,
        channel_key=message.channel_key,
        sequence=int(message.sequence or 0),
        snapshot_version=message.snapshot_version,
        progress_fingerprint=message.progress_fingerprint,
        chat_snapshot=chat_snapshot,
        activity_view=_text_view_from_message(message.activity_view) if message.HasField("activity_view") else None,
        permissions_view=_text_view_from_message(message.permissions_view) if message.HasField("permissions_view") else None,
        skills_view=_text_view_from_message(message.skills_view) if message.HasField("skills_view") else None,
        status_view=_text_view_from_message(message.status_view) if message.HasField("status_view") else None,
    )


@dataclass
class InProcessWorkstationShellClient:
    service: WorkstationShellApiService = field(default_factory=WorkstationShellApiService)
    client_session_id: str = ""

    def __post_init__(self) -> None:
        if not collapse_ws(self.client_session_id):
            self.client_session_id = f"client-{uuid.uuid4().hex}"

    def open_client_session(self, *, root_path: Path) -> str:
        return self.service.open_client_session(root_path=root_path, client_session_id=self.client_session_id)

    def close_client_session(self, *, root_path: Path) -> str:
        return self.service.close_client_session(root_path=root_path, client_session_id=self.client_session_id)

    def get_chat_snapshot(self, *, root_path: Path, limit: int = 120) -> WorkstationChatSnapshotView:
        return self.service.get_chat_snapshot(root_path=root_path, client_session_id=self.client_session_id, limit=limit)

    def prepare_chat_prompt_target(self, *, root_path: Path, prompt_text: str) -> WorkstationPreparedChatPromptTargetView:
        return self.service.prepare_chat_prompt_target(
            root_path=root_path,
            client_session_id=self.client_session_id,
            prompt_text=prompt_text,
        )

    def submit_chat_input(
        self,
        *,
        root_path: Path,
        prompt_text: str,
        model: str | None = None,
        max_tool_rounds: int = 8,
        force_llm_only: bool = False,
        interaction_mode: str = "normal",
        governed_treatment: str = "independent",
        governed_parent_run_id: str = "",
        governed_llm_policy: str = "auto",
        governed_max_steps: int = 256,
    ) -> WorkstationSubmitChatInputResultView:
        return self.service.submit_chat_input(
            root_path=root_path,
            client_session_id=self.client_session_id,
            prompt_text=prompt_text,
            model=model,
            max_tool_rounds=max_tool_rounds,
            force_llm_only=force_llm_only,
            interaction_mode=interaction_mode,
            governed_treatment=governed_treatment,
            governed_parent_run_id=governed_parent_run_id,
            governed_llm_policy=governed_llm_policy,
            governed_max_steps=governed_max_steps,
        )

    def append_shell_turn(
        self,
        *,
        root_path: Path,
        prompt_text: str = "",
        assistant_text: str = "",
        assistant_role: str = "shell",
    ) -> WorkstationChatSnapshotView:
        return self.service.append_shell_turn(
            root_path=root_path,
            client_session_id=self.client_session_id,
            prompt_text=prompt_text,
            assistant_text=assistant_text,
            assistant_role=assistant_role,
        )

    def get_activity_view(self, *, root_path: Path, limit: int = 120) -> WorkstationShellTextView:
        return self.service.get_activity_view(root_path=root_path, client_session_id=self.client_session_id, limit=limit)

    def get_permissions_view(self, *, root_path: Path) -> WorkstationShellTextView:
        return self.service.get_permissions_view(root_path=root_path, client_session_id=self.client_session_id)

    def get_skills_view(self, *, root_path: Path, query: str = "") -> WorkstationShellTextView:
        return self.service.get_skills_view(root_path=root_path, client_session_id=self.client_session_id, query=query)

    def watch_workstation_shell(
        self,
        *,
        root_path: Path,
        last_seen_version: str = "",
        stop_when: Callable[[], bool] | None = None,
    ) -> Iterator[WorkstationShellWatchEventView]:
        iterator = self.service.watch_workstation_shell(
            root_path=root_path,
            client_session_id=self.client_session_id,
            last_seen_version=last_seen_version,
            stop_when=stop_when,
        )
        for event in iterator:
            if stop_when is not None and stop_when():
                break
            yield event


@dataclass
class GrpcWorkstationShellClient:
    channel: grpc.Channel
    client_session_id: str = ""

    def __post_init__(self) -> None:
        if not collapse_ws(self.client_session_id):
            self.client_session_id = f"client-{uuid.uuid4().hex}"
        self._stub = workstation_shell_pb2_grpc.WorkstationShellServiceStub(self.channel)

    def open_client_session(self, *, root_path: Path) -> str:
        response = self._stub.OpenClientSession(
            workstation_shell_pb2.ClientSessionRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
            )
        )
        return response.client_session_id

    def close_client_session(self, *, root_path: Path) -> str:
        response = self._stub.CloseClientSession(
            workstation_shell_pb2.ClientSessionRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
            )
        )
        return response.client_session_id

    def get_chat_snapshot(self, *, root_path: Path, limit: int = 120) -> WorkstationChatSnapshotView:
        response = self._stub.GetChatSnapshot(
            workstation_shell_pb2.ChatSnapshotRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                limit=max(int(limit or 0), 1),
            )
        )
        from workstation.shell.core.chat_shell import workstation_chat_context

        return WorkstationChatSnapshotView(
            context=workstation_chat_context(Path(root_path).expanduser().resolve()),
            messages=tuple(_message_view_from_message(item) for item in response.messages),
            session_status=response.session_status,
            snapshot_version=response.snapshot_version,
            progress_fingerprint=response.progress_fingerprint,
        )

    def prepare_chat_prompt_target(self, *, root_path: Path, prompt_text: str) -> WorkstationPreparedChatPromptTargetView:
        response = self._stub.PrepareChatPromptTarget(
            workstation_shell_pb2.PrepareChatPromptTargetRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                prompt_text=str(prompt_text or ""),
            )
        )
        return WorkstationPreparedChatPromptTargetView(
            kind=response.kind,
            prepared_prompt=response.prepared_prompt,
            shell_text=response.shell_text,
            target_kind=response.target_kind,
            routing_metadata_json=response.routing_metadata_json,
        )

    def submit_chat_input(
        self,
        *,
        root_path: Path,
        prompt_text: str,
        model: str | None = None,
        max_tool_rounds: int = 8,
        force_llm_only: bool = False,
        interaction_mode: str = "normal",
        governed_treatment: str = "independent",
        governed_parent_run_id: str = "",
        governed_llm_policy: str = "auto",
        governed_max_steps: int = 256,
    ) -> WorkstationSubmitChatInputResultView:
        response = self._stub.SubmitChatInput(
            workstation_shell_pb2.SubmitChatInputRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                prompt_text=str(prompt_text or ""),
                model=str(model or ""),
                max_tool_rounds=max(int(max_tool_rounds or 0), 0),
                force_llm_only=bool(force_llm_only),
                interaction_mode=str(interaction_mode or "normal"),
                governed_treatment=str(governed_treatment or "independent"),
                governed_parent_run_id=str(governed_parent_run_id or ""),
                governed_llm_policy=str(governed_llm_policy or "auto"),
                governed_max_steps=max(int(governed_max_steps or 0), 0),
            )
        )
        return WorkstationSubmitChatInputResultView(
            assistant_text=response.assistant_text,
            messages=tuple(_message_view_from_message(item) for item in response.messages),
            fulfilled_by=response.fulfilled_by,
            rounds=int(response.rounds or 0),
            tool_receipts_json=response.tool_receipts_json,
            status_text=response.status_text,
            snapshot_version=response.snapshot_version,
            progress_fingerprint=response.progress_fingerprint,
            turn_id=response.turn_id,
            run_id=response.run_id,
            run_outcome=response.run_outcome,
            checkpoint_path=response.checkpoint_path,
        )

    def append_shell_turn(
        self,
        *,
        root_path: Path,
        prompt_text: str = "",
        assistant_text: str = "",
        assistant_role: str = "shell",
    ) -> WorkstationChatSnapshotView:
        response = self._stub.AppendShellTurn(
            workstation_shell_pb2.AppendShellTurnRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                prompt_text=str(prompt_text or ""),
                assistant_text=str(assistant_text or ""),
                assistant_role=str(assistant_role or "shell"),
            )
        )
        snapshot = response.snapshot
        from workstation.shell.core.chat_shell import workstation_chat_context

        return WorkstationChatSnapshotView(
            context=workstation_chat_context(Path(root_path).expanduser().resolve()),
            messages=tuple(_message_view_from_message(item) for item in snapshot.messages),
            session_status=snapshot.session_status,
            snapshot_version=snapshot.snapshot_version,
            progress_fingerprint=snapshot.progress_fingerprint,
        )

    def get_activity_view(self, *, root_path: Path, limit: int = 120) -> WorkstationShellTextView:
        response = self._stub.GetActivityView(
            workstation_shell_pb2.ActivityViewRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                limit=max(int(limit or 0), 1),
            )
        )
        return _text_view_from_message(response)

    def get_permissions_view(self, *, root_path: Path) -> WorkstationShellTextView:
        response = self._stub.GetPermissionsView(
            workstation_shell_pb2.PermissionsViewRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
            )
        )
        return _text_view_from_message(response)

    def get_skills_view(self, *, root_path: Path, query: str = "") -> WorkstationShellTextView:
        response = self._stub.GetSkillsView(
            workstation_shell_pb2.SkillsViewRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                query=str(query or ""),
            )
        )
        return _text_view_from_message(response)

    def watch_workstation_shell(
        self,
        *,
        root_path: Path,
        last_seen_version: str = "",
        stop_when: Callable[[], bool] | None = None,
    ) -> Iterator[WorkstationShellWatchEventView]:
        stream = self._stub.WatchWorkstationShell(
            workstation_shell_pb2.WatchWorkstationShellRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                client_session_id=self.client_session_id,
                last_seen_version=str(last_seen_version or ""),
            )
        )
        try:
            try:
                for message in stream:
                    if stop_when is not None and stop_when():
                        break
                    yield _watch_event_view_from_message(message)
            except grpc.RpcError as error:
                if error.code() not in (
                    grpc.StatusCode.CANCELLED,
                    grpc.StatusCode.UNAVAILABLE,
                ):
                    raise
        finally:
            try:
                stream.cancel()
            except Exception:
                pass

    def close(self) -> None:
        try:
            self.channel.close()
        except Exception:
            pass


def workstation_shell_grpc_unix_socket_target(socket_path: Path) -> str:
    return f"unix://{Path(socket_path).expanduser().resolve()}"


def open_workstation_shell_grpc_unix_socket_channel(socket_path: Path) -> grpc.Channel:
    return grpc.insecure_channel(workstation_shell_grpc_unix_socket_target(socket_path))


def new_grpc_workstation_shell_client_for_unix_socket(
    socket_path: Path,
    *,
    client_session_id: str = "",
) -> GrpcWorkstationShellClient:
    return GrpcWorkstationShellClient(
        open_workstation_shell_grpc_unix_socket_channel(socket_path),
        client_session_id=client_session_id,
    )
