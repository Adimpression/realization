"""Transport-neutral workstation shell request and response contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Protocol, runtime_checkable


@dataclass(frozen=True)
class WorkstationChatContext:
    root: Path
    workspace_root: Path | None
    skill_titles: tuple[str, ...]
    builtin_skill_titles: tuple[str, ...]
    imported_skill_titles: tuple[str, ...]
    subject_titles: tuple[str, ...]
    workspace_paths: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class WorkstationChatPromptTargetPlan:
    kind: str
    command_name: str = ""
    command_arguments: str = ""
    llm_prompt: str = ""
    shell_text: str = ""
    move_to_research: bool = False
    subject_title: str = ""


@dataclass(frozen=True)
class WorkstationChatMessageView:
    role: str
    content: str
    timestamp_epoch_ms: int = 0
    message_id: str = ""
    turn_id: str = ""
    sequence: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp_epoch_ms": int(self.timestamp_epoch_ms or 0),
            "message_id": self.message_id,
            "turn_id": self.turn_id,
            "sequence": int(self.sequence or 0),
        }


@dataclass(frozen=True)
class WorkstationShellTextView:
    text: str
    snapshot_version: str
    progress_fingerprint: str
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class WorkstationChatSnapshotView:
    context: WorkstationChatContext
    messages: tuple[WorkstationChatMessageView, ...]
    session_status: str
    snapshot_version: str
    progress_fingerprint: str
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class WorkstationPreparedChatPromptTargetView:
    kind: str
    prepared_prompt: str
    shell_text: str
    target_kind: str
    routing_metadata_json: str
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class WorkstationSubmitChatInputResultView:
    assistant_text: str
    messages: tuple[WorkstationChatMessageView, ...]
    fulfilled_by: str
    rounds: int
    tool_receipts_json: str
    status_text: str
    snapshot_version: str
    progress_fingerprint: str
    trace_id: str = ""
    parent_id: str = ""
    turn_id: str = ""
    run_id: str = ""
    run_outcome: str = ""
    checkpoint_path: str = ""


@dataclass(frozen=True)
class WorkstationShellWatchEventView:
    event_kind: str
    channel_key: str
    sequence: int
    snapshot_version: str
    progress_fingerprint: str
    chat_snapshot: WorkstationChatSnapshotView | None = None
    activity_view: WorkstationShellTextView | None = None
    permissions_view: WorkstationShellTextView | None = None
    skills_view: WorkstationShellTextView | None = None
    status_view: WorkstationShellTextView | None = None
    trace_id: str = ""
    parent_id: str = ""


@runtime_checkable
class WorkstationShellClient(Protocol):
    @property
    def client_session_id(self) -> str: ...

    def open_client_session(self, *, root_path: Path) -> str: ...

    def close_client_session(self, *, root_path: Path) -> str: ...

    def get_chat_snapshot(
        self, *, root_path: Path, limit: int = 120
    ) -> WorkstationChatSnapshotView: ...

    def prepare_chat_prompt_target(
        self, *, root_path: Path, prompt_text: str
    ) -> WorkstationPreparedChatPromptTargetView: ...

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
    ) -> WorkstationSubmitChatInputResultView: ...

    def append_shell_turn(
        self,
        *,
        root_path: Path,
        prompt_text: str = "",
        assistant_text: str = "",
        assistant_role: str = "shell",
    ) -> WorkstationChatSnapshotView: ...

    def get_activity_view(
        self, *, root_path: Path, limit: int = 120
    ) -> WorkstationShellTextView: ...

    def get_permissions_view(self, *, root_path: Path) -> WorkstationShellTextView: ...

    def get_skills_view(
        self, *, root_path: Path, query: str = ""
    ) -> WorkstationShellTextView: ...

    def watch_workstation_shell(
        self,
        *,
        root_path: Path,
        last_seen_version: str = "",
        stop_when: Callable[[], bool] | None = None,
    ) -> Iterator[WorkstationShellWatchEventView]: ...


WorkstationChatContext.__module__ = "workstation.shell.core.chat_shell"
WorkstationChatPromptTargetPlan.__module__ = "workstation.shell.core.chat_shell"
WorkstationChatMessageView.__module__ = (
    "workstation.foundation.projections.projection_models"
)
for _view_type in (
    WorkstationShellTextView,
    WorkstationChatSnapshotView,
    WorkstationPreparedChatPromptTargetView,
    WorkstationSubmitChatInputResultView,
    WorkstationShellWatchEventView,
):
    _view_type.__module__ = "workstation.shell.core.workstation_shell_api"
WorkstationShellClient.__module__ = "workstation.shell.core.workstation_shell_client"
del _view_type

__all__ = [
    "WorkstationChatContext",
    "WorkstationChatMessageView",
    "WorkstationChatPromptTargetPlan",
    "WorkstationChatSnapshotView",
    "WorkstationPreparedChatPromptTargetView",
    "WorkstationShellClient",
    "WorkstationShellTextView",
    "WorkstationShellWatchEventView",
    "WorkstationSubmitChatInputResultView",
]
