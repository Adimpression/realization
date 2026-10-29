# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Iterator

from realized_core_semantics.semantic_text import collapse_ws
from workstation.contracts.shell import (
    WorkstationChatContext,
    WorkstationChatMessageView,
    WorkstationChatPromptTargetPlan,
    WorkstationChatSnapshotView,
    WorkstationPreparedChatPromptTargetView,
    WorkstationShellTextView,
    WorkstationShellWatchEventView,
    WorkstationSubmitChatInputResultView,
)
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.runtime.core.chat_commands import (
    canonical_workstation_chat_slash_command_text,
    run_workstation_chat_slash_command,
)
from workstation.shell.core.chat_shell import (
    workstation_chat_context,
    workstation_chat_help_text,
    workstation_chat_prepare_last_assistant_resolution,
    workstation_chat_prompt_target_plan,
)
from workstation.shell.core.governed_conversation import (
    submit_governed_conversation_turn,
)
from workstation.foundation.events.event_bus import publish_workstation_event, workstation_event_bus
from workstation.runtime.core.session import _append_message, prompt_workstation_session
from workstation.runtime.core.workstation_core import workstation_chat_transcript_view
from workstation.shell.core.workstation_shell_backend import WorkstationShellProjectionBackend
from workstation.subject.service.client_sessions import WorkstationClientSessionRegistry


def _registered_trace(
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


def _path_stat_key(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return "0:0"
    return f"{int(stat.st_mtime_ns)}:{int(stat.st_size)}"


def _shell_progress_fingerprint(*, root_path: Path) -> str:
    resolved_root = Path(root_path).expanduser().resolve()
    activity_path = resolved_root / "activity.log"
    session_path = resolved_root / "SESSION.json"
    skills_path = resolved_root / "SKILLS.json"
    messages_path = resolved_root / "MESSAGES.jsonl"
    return "|".join(
        (
            f"messages={_path_stat_key(messages_path)}",
            f"session={_path_stat_key(session_path)}",
            f"skills={_path_stat_key(skills_path)}",
            f"activity={_path_stat_key(activity_path)}",
        )
    )


def _snapshot_version(*, root_path: Path, channel_key: str) -> str:
    return f"{collapse_ws(channel_key)}::{_shell_progress_fingerprint(root_path=root_path)}"


def _routing_metadata_json(plan: WorkstationChatPromptTargetPlan) -> str:
    return json.dumps(
        {
            "command_name": plan.command_name,
            "command_arguments": plan.command_arguments,
            "move_to_research": bool(plan.move_to_research),
            "subject_title": plan.subject_title,
        },
        sort_keys=True,
    )


def _latest_assistant_transcript_text(messages: tuple[WorkstationChatMessageView, ...]) -> str:
    for message in reversed(messages):
        if collapse_ws(str(getattr(message, "role", ""))).casefold() == "assistant":
            return str(getattr(message, "content", "") or "").strip()
    return ""


@dataclass
class WorkstationShellApiService:
    client_sessions: WorkstationClientSessionRegistry = field(default_factory=WorkstationClientSessionRegistry)
    shell_projection_backend: WorkstationShellProjectionBackend = field(default_factory=WorkstationShellProjectionBackend)
    governed_conversation_submitter: Callable[..., dict[str, Any]] = (
        submit_governed_conversation_turn
    )

    def open_client_session(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
    ) -> str:
        return self.client_sessions.open_client_session(
            root_path=Path(root_path).expanduser().resolve(),
            client_session_id=client_session_id,
        )

    def close_client_session(
        self,
        *,
        root_path: Path,
        client_session_id: str,
    ) -> str:
        self.client_sessions.close_client_session(
            root_path=Path(root_path).expanduser().resolve(),
            client_session_id=client_session_id,
        )
        return collapse_ws(client_session_id)

    def get_chat_snapshot(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        limit: int = 120,
    ) -> WorkstationChatSnapshotView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-chat-snapshot-request")
        normalized_session_id = self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        transcript = workstation_chat_transcript_view(root_path=resolved_root, limit=max(int(limit or 0), 1))
        snapshot_version = _snapshot_version(root_path=resolved_root, channel_key="shell/transcript")
        progress_fingerprint = _shell_progress_fingerprint(root_path=resolved_root)
        trace_id, parent_id = _registered_trace(
            message_kind="GetChatSnapshot",
            prefix="shell-chat-snapshot",
            parent_id=parent_trace_id,
            components=(
                parent_trace_id,
                resolved_root,
                normalized_session_id,
                snapshot_version,
            ),
        )
        return WorkstationChatSnapshotView(
            context=workstation_chat_context(resolved_root),
            messages=tuple(transcript.messages),
            session_status="ready",
            snapshot_version=snapshot_version,
            progress_fingerprint=progress_fingerprint,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def prepare_chat_prompt_target(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        prompt_text: str,
    ) -> WorkstationPreparedChatPromptTargetView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-prompt-target-request")
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        plan = workstation_chat_prompt_target_plan(
            context=workstation_chat_context(resolved_root),
            prompt_text=prompt_text,
        )
        if plan is None:
            return WorkstationPreparedChatPromptTargetView(
                kind="none",
                prepared_prompt="",
                shell_text="",
                target_kind="none",
                routing_metadata_json="{}",
                trace_id=_registered_trace(
                    message_kind="PrepareChatPromptTarget.none",
                    prefix="shell-prompt-target",
                    parent_id=parent_trace_id,
                    components=(parent_trace_id, resolved_root, prompt_text, "none"),
                )[0],
                parent_id=parent_trace_id,
            )
        if plan.kind == "prepare_last_assistant_markdown":
            snapshot = self.get_chat_snapshot(
                root_path=resolved_root,
                client_session_id=client_session_id,
            )
            prepared_prompt, shell_text = workstation_chat_prepare_last_assistant_resolution(
                _latest_assistant_transcript_text(snapshot.messages)
            )
            if not collapse_ws(prepared_prompt):
                return WorkstationPreparedChatPromptTargetView(
                    kind="shell",
                    prepared_prompt="",
                    shell_text=shell_text,
                    target_kind="shell",
                    routing_metadata_json=_routing_metadata_json(plan),
                    trace_id=_registered_trace(
                        message_kind="PrepareChatPromptTarget.shell",
                        prefix="shell-prompt-target",
                        parent_id=parent_trace_id,
                        components=(parent_trace_id, resolved_root, plan.kind, shell_text),
                    )[0],
                    parent_id=parent_trace_id,
                )
            return WorkstationPreparedChatPromptTargetView(
                kind="llm_prompt",
                prepared_prompt=prepared_prompt,
                shell_text=shell_text,
                target_kind="llm_prompt",
                routing_metadata_json=_routing_metadata_json(plan),
                trace_id=_registered_trace(
                    message_kind="PrepareChatPromptTarget.llm",
                    prefix="shell-prompt-target",
                    parent_id=parent_trace_id,
                    components=(parent_trace_id, resolved_root, plan.kind, prepared_prompt),
                )[0],
                parent_id=parent_trace_id,
            )
        trace_id, parent_id = _registered_trace(
            message_kind="PrepareChatPromptTarget",
            prefix="shell-prompt-target",
            parent_id=parent_trace_id,
            components=(parent_trace_id, resolved_root, plan.kind, plan.shell_text, plan.llm_prompt),
        )
        prepared_prompt = plan.llm_prompt if plan.kind == "llm_prompt" else ""
        return WorkstationPreparedChatPromptTargetView(
            kind=plan.kind,
            prepared_prompt=prepared_prompt,
            shell_text=plan.shell_text,
            target_kind=plan.kind,
            routing_metadata_json=_routing_metadata_json(plan),
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def append_shell_turn(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        prompt_text: str = "",
        assistant_text: str = "",
        assistant_role: str = "shell",
    ) -> WorkstationChatSnapshotView:
        resolved_root = Path(root_path).expanduser().resolve()
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        normalized_prompt = str(prompt_text or "").strip()
        normalized_assistant = str(assistant_text or "").strip()
        normalized_role = collapse_ws(assistant_role) or "shell"
        turn_id = new_trace_id("shell-turn")
        if normalized_prompt:
            _append_message(
                resolved_root,
                {"role": "user", "content": normalized_prompt, "turn_id": turn_id},
            )
        if normalized_assistant:
            _append_message(
                resolved_root,
                {
                    "role": normalized_role,
                    "content": normalized_assistant,
                    "turn_id": turn_id,
                },
            )
        if normalized_prompt or normalized_assistant:
            publish_workstation_event(
                root_path=resolved_root,
                session_id=collapse_ws(client_session_id) or "shell_api",
                event_kind="shell_transcript_changed",
                payload={
                    "has_prompt": bool(normalized_prompt),
                    "has_assistant": bool(normalized_assistant),
                    "assistant_role": normalized_role,
                },
            )
        return self.get_chat_snapshot(root_path=resolved_root, client_session_id=client_session_id)

    def submit_chat_input(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
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
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-submit-request")
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        normalized_prompt = str(prompt_text or "").strip()
        if not normalized_prompt:
            snapshot = self.get_chat_snapshot(root_path=resolved_root, client_session_id=client_session_id)
            return WorkstationSubmitChatInputResultView(
                assistant_text="",
                messages=snapshot.messages,
                fulfilled_by="",
                rounds=0,
                tool_receipts_json="[]",
                status_text="Prompt is required.",
                snapshot_version=snapshot.snapshot_version,
                progress_fingerprint=snapshot.progress_fingerprint,
                trace_id=_registered_trace(
                    message_kind="SubmitChatInput.empty",
                    prefix="shell-submit-response",
                    parent_id=parent_trace_id,
                    components=(parent_trace_id, resolved_root, "empty"),
                )[0],
                parent_id=parent_trace_id,
            )
        canonical_prompt = canonical_workstation_chat_slash_command_text(normalized_prompt)
        if canonical_prompt == "/help":
            snapshot = self.append_shell_turn(
                root_path=resolved_root,
                client_session_id=client_session_id,
                prompt_text=normalized_prompt,
                assistant_text=workstation_chat_help_text(workstation_chat_context(resolved_root)),
            )
            return WorkstationSubmitChatInputResultView(
                assistant_text=snapshot.messages[-1].content if snapshot.messages else "",
                messages=snapshot.messages,
                fulfilled_by="shell.help",
                rounds=0,
                tool_receipts_json="[]",
                status_text="ok",
                snapshot_version=snapshot.snapshot_version,
                progress_fingerprint=snapshot.progress_fingerprint,
                trace_id=_registered_trace(
                    message_kind="SubmitChatInput.help",
                    prefix="shell-submit-response",
                    parent_id=parent_trace_id,
                    components=(parent_trace_id, resolved_root, canonical_prompt, snapshot.snapshot_version),
                )[0],
                parent_id=parent_trace_id,
            )
        if canonical_prompt.startswith("/"):
            handled, output_text = run_workstation_chat_slash_command(root=resolved_root, command_text=normalized_prompt)
            if handled:
                snapshot = self.append_shell_turn(
                    root_path=resolved_root,
                    client_session_id=client_session_id,
                    prompt_text=normalized_prompt,
                    assistant_text=output_text,
                )
                return WorkstationSubmitChatInputResultView(
                    assistant_text=output_text,
                    messages=snapshot.messages,
                    fulfilled_by="shell.command",
                    rounds=0,
                    tool_receipts_json="[]",
                    status_text="ok",
                    snapshot_version=snapshot.snapshot_version,
                    progress_fingerprint=snapshot.progress_fingerprint,
                    trace_id=_registered_trace(
                        message_kind="SubmitChatInput.command",
                        prefix="shell-submit-response",
                        parent_id=parent_trace_id,
                        components=(parent_trace_id, resolved_root, canonical_prompt, snapshot.snapshot_version),
                    )[0],
                    parent_id=parent_trace_id,
                )
        normalized_interaction_mode = collapse_ws(interaction_mode).casefold() or "normal"
        if normalized_interaction_mode == "governed_conversation":
            if force_llm_only:
                raise ValueError(
                    "LLM-only and governed-conversation modes are mutually exclusive."
                )
            report = self.governed_conversation_submitter(
                root_path=resolved_root,
                prompt_text=normalized_prompt,
                model=model,
                max_steps=governed_max_steps,
                llm_policy=governed_llm_policy,
                parent_run_id=governed_parent_run_id,
            )
            assistant_text = str(report.get("assistant_text", "") or "")
            snapshot = self.append_shell_turn(
                root_path=resolved_root,
                client_session_id=client_session_id,
                prompt_text=normalized_prompt,
                assistant_text=assistant_text,
                assistant_role="assistant",
            )
            trace_id, parent_id = _registered_trace(
                message_kind="SubmitChatInput.governed_conversation",
                prefix="shell-submit-response",
                parent_id=parent_trace_id,
                components=(
                    parent_trace_id,
                    resolved_root,
                    normalized_prompt,
                    snapshot.snapshot_version,
                ),
            )
            return WorkstationSubmitChatInputResultView(
                assistant_text=assistant_text,
                messages=snapshot.messages,
                fulfilled_by="governed_conversation",
                rounds=0,
                tool_receipts_json="[]",
                status_text="ok",
                snapshot_version=snapshot.snapshot_version,
                progress_fingerprint=snapshot.progress_fingerprint,
                trace_id=trace_id,
                parent_id=parent_id,
                turn_id=collapse_ws(str(report.get("turn_id", ""))),
                run_id=collapse_ws(str(report.get("run_id", ""))),
                run_outcome=collapse_ws(str(report.get("run_outcome", ""))),
                checkpoint_path="",
            )
        report = prompt_workstation_session(
            root_path=resolved_root,
            prompt=normalized_prompt,
            model=model,
            max_tool_rounds=max_tool_rounds,
            force_llm_only=force_llm_only,
            interaction_mode=interaction_mode,
            governed_treatment=governed_treatment,
            governed_parent_run_id=governed_parent_run_id,
            governed_llm_policy=governed_llm_policy,
            governed_max_steps=governed_max_steps,
        )
        snapshot = self.get_chat_snapshot(root_path=resolved_root, client_session_id=client_session_id)
        trace_id, parent_id = _registered_trace(
            message_kind="SubmitChatInput.llm",
            prefix="shell-submit-response",
            parent_id=parent_trace_id,
            components=(parent_trace_id, resolved_root, normalized_prompt, snapshot.snapshot_version),
        )
        return WorkstationSubmitChatInputResultView(
            assistant_text=str(report.get("assistant_text", "") or ""),
            messages=snapshot.messages,
            fulfilled_by=collapse_ws(str(report.get("fulfilled_by", ""))),
            rounds=int(report.get("rounds", 0) or 0),
            tool_receipts_json=json.dumps(report.get("tool_receipts", []), sort_keys=True),
            status_text="ok",
            snapshot_version=snapshot.snapshot_version,
            progress_fingerprint=snapshot.progress_fingerprint,
            trace_id=trace_id,
            parent_id=parent_id,
            turn_id=collapse_ws(str(report.get("turn_id", ""))),
            run_id=collapse_ws(str(report.get("run_id", ""))),
            run_outcome=collapse_ws(str(report.get("run_outcome", ""))),
            checkpoint_path=str(report.get("checkpoint_path", "") or ""),
        )

    def get_activity_view(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        limit: int = 120,
    ) -> WorkstationShellTextView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-activity-request")
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        channel_key = "shell/activity"
        text = self.shell_projection_backend.activity_text(root_path=resolved_root, limit=max(int(limit or 0), 1))
        snapshot_version = _snapshot_version(root_path=resolved_root, channel_key=channel_key)
        progress_fingerprint = _shell_progress_fingerprint(root_path=resolved_root)
        trace_id, parent_id = _registered_trace(
            message_kind="GetActivityView",
            prefix="shell-text-view",
            parent_id=parent_trace_id,
            components=(parent_trace_id, resolved_root, channel_key, snapshot_version),
        )
        return WorkstationShellTextView(
            text=text,
            snapshot_version=snapshot_version,
            progress_fingerprint=progress_fingerprint,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def get_permissions_view(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
    ) -> WorkstationShellTextView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-permissions-request")
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        channel_key = "shell/permissions"
        text = self.shell_projection_backend.permissions_text(root_path=resolved_root)
        snapshot_version = _snapshot_version(root_path=resolved_root, channel_key=channel_key)
        progress_fingerprint = _shell_progress_fingerprint(root_path=resolved_root)
        trace_id, parent_id = _registered_trace(
            message_kind="GetPermissionsView",
            prefix="shell-text-view",
            parent_id=parent_trace_id,
            components=(parent_trace_id, resolved_root, channel_key, snapshot_version),
        )
        return WorkstationShellTextView(
            text=text,
            snapshot_version=snapshot_version,
            progress_fingerprint=progress_fingerprint,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def get_skills_view(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        query: str = "",
    ) -> WorkstationShellTextView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("shell-skills-request")
        self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        # Query is reserved for future filtering. Keep API stable now.
        _ = query
        channel_key = "shell/skills"
        text = self.shell_projection_backend.skills_text(root_path=resolved_root)
        snapshot_version = _snapshot_version(root_path=resolved_root, channel_key=channel_key)
        progress_fingerprint = _shell_progress_fingerprint(root_path=resolved_root)
        trace_id, parent_id = _registered_trace(
            message_kind="GetSkillsView",
            prefix="shell-text-view",
            parent_id=parent_trace_id,
            components=(parent_trace_id, resolved_root, channel_key, snapshot_version),
        )
        return WorkstationShellTextView(
            text=text,
            snapshot_version=snapshot_version,
            progress_fingerprint=progress_fingerprint,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def watch_workstation_shell(
        self,
        *,
        root_path: Path,
        client_session_id: str = "",
        last_seen_version: str = "",
        poll_interval_seconds: float = 0.25,
        stop_when: Callable[[], bool] | None = None,
    ) -> Iterator[WorkstationShellWatchEventView]:
        resolved_root = Path(root_path).expanduser().resolve()
        normalized_session_id = self.open_client_session(root_path=resolved_root, client_session_id=client_session_id)
        stream_trace_id = new_trace_id("shell-watch-stream")
        sequence = 0
        last_versions: dict[str, str] = {}
        if collapse_ws(last_seen_version):
            last_versions["shell/transcript"] = collapse_ws(last_seen_version)
        payload_cache: dict[str, Any] = {}
        event_queue: Queue[Any] = Queue()

        def _handle_event(event: Any) -> None:
            try:
                event_queue.put_nowait(event)
            except Exception:
                return

        def _candidates() -> tuple[tuple[str, str, Callable[[], Any], str], ...]:
            transcript_version = _snapshot_version(root_path=resolved_root, channel_key="shell/transcript")
            activity_version = _snapshot_version(root_path=resolved_root, channel_key="shell/activity")
            permissions_version = _snapshot_version(root_path=resolved_root, channel_key="shell/permissions")
            skills_version = _snapshot_version(root_path=resolved_root, channel_key="shell/skills")
            return (
                (
                    "shell/transcript",
                    transcript_version,
                    lambda: self.get_chat_snapshot(
                        root_path=resolved_root,
                        client_session_id=normalized_session_id,
                    ),
                    "WatchWorkstationShell.chat",
                ),
                (
                    "shell/activity",
                    activity_version,
                    lambda: self.get_activity_view(
                        root_path=resolved_root,
                        client_session_id=normalized_session_id,
                    ),
                    "WatchWorkstationShell.activity",
                ),
                (
                    "shell/permissions",
                    permissions_version,
                    lambda: self.get_permissions_view(
                        root_path=resolved_root,
                        client_session_id=normalized_session_id,
                    ),
                    "WatchWorkstationShell.permissions",
                ),
                (
                    "shell/skills",
                    skills_version,
                    lambda: self.get_skills_view(
                        root_path=resolved_root,
                        client_session_id=normalized_session_id,
                    ),
                    "WatchWorkstationShell.skills",
                ),
            )

        def _emit_available_snapshots(*, parent_trace_id: str) -> Iterator[WorkstationShellWatchEventView]:
            nonlocal sequence
            for channel_key, snapshot_version, payload_loader, message_kind in _candidates():
                if last_versions.get(channel_key) == snapshot_version:
                    continue
                last_versions[channel_key] = snapshot_version
                payload = payload_cache.get(channel_key)
                if payload is None or collapse_ws(str(getattr(payload, "snapshot_version", "") or "")) != snapshot_version:
                    payload = payload_loader()
                    payload_cache[channel_key] = payload
                trace_id, parent_id = _registered_trace(
                    message_kind=message_kind,
                    prefix="shell-watch-event",
                    parent_id=parent_trace_id,
                    components=(stream_trace_id, parent_trace_id, channel_key, snapshot_version, sequence),
                )
                if channel_key == "shell/transcript":
                    chat_snapshot = payload
                    yield WorkstationShellWatchEventView(
                        event_kind="initial" if sequence == 0 else "chat_snapshot_changed",
                        channel_key=channel_key,
                        sequence=sequence,
                        snapshot_version=snapshot_version,
                        progress_fingerprint=chat_snapshot.progress_fingerprint,
                        chat_snapshot=chat_snapshot,
                        trace_id=trace_id,
                        parent_id=parent_id,
                    )
                elif channel_key == "shell/activity":
                    activity_view = payload
                    yield WorkstationShellWatchEventView(
                        event_kind="initial" if sequence == 0 else "activity_changed",
                        channel_key=channel_key,
                        sequence=sequence,
                        snapshot_version=snapshot_version,
                        progress_fingerprint=activity_view.progress_fingerprint,
                        activity_view=activity_view,
                        trace_id=trace_id,
                        parent_id=parent_id,
                    )
                elif channel_key == "shell/permissions":
                    permissions_view = payload
                    yield WorkstationShellWatchEventView(
                        event_kind="initial" if sequence == 0 else "permissions_changed",
                        channel_key=channel_key,
                        sequence=sequence,
                        snapshot_version=snapshot_version,
                        progress_fingerprint=permissions_view.progress_fingerprint,
                        permissions_view=permissions_view,
                        trace_id=trace_id,
                        parent_id=parent_id,
                    )
                else:
                    skills_view = payload
                    yield WorkstationShellWatchEventView(
                        event_kind="initial" if sequence == 0 else "skills_changed",
                        channel_key=channel_key,
                        sequence=sequence,
                        snapshot_version=snapshot_version,
                        progress_fingerprint=skills_view.progress_fingerprint,
                        skills_view=skills_view,
                        trace_id=trace_id,
                        parent_id=parent_id,
                    )
                sequence += 1

        unsubscribe = workstation_event_bus(resolved_root).subscribe("*", _handle_event)
        try:
            yield from _emit_available_snapshots(parent_trace_id=stream_trace_id)
            wait_timeout = max(0.05, float(poll_interval_seconds or 0.25))
            while True:
                if stop_when is not None and stop_when():
                    break
                try:
                    event = event_queue.get(timeout=wait_timeout)
                except Empty:
                    continue
                if stop_when is not None and stop_when():
                    break
                event_trace_id = collapse_ws(str(getattr(event, "trace_id", "") or "")) or stream_trace_id
                yield from _emit_available_snapshots(parent_trace_id=event_trace_id)
        finally:
            try:
                unsubscribe()
            except Exception:
                pass
