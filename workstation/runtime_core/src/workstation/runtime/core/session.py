# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import shutil
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applied_theory_types import json_safe
from blend_context import blend_context_from_workstation_session
from blend_session import blend_session_from_workstation_session
from blend_world import BlendWorld
from blend_world_store import blend_world_mount_source, ensure_persisted_blend_workstation_world, load_blend_world
from blend_workflow import blend_workflow_plan_from_skill_compose_arguments, ensure_blend_workflow_store
from realized_host_interaction.receipts import (
    host_interaction_assistant_response_receipt,
    host_interaction_capability_call_receipt,
    host_interaction_delegation_approval_decision_receipt,
    host_interaction_delegation_approval_requested_receipt,
    host_interaction_user_prompt_receipt,
)
from realized_host_interaction.delegation import normalized_requested_delegation
from semantic_text import collapse_ws
from workstation.runtime.core.capabilities import (
    DEFAULT_WORKSTATION_CAPABILITIES,
    execute_workstation_capability,
    list_workstation_tool_definitions,
)
from workstation.runtime.core.chat_commands import run_workstation_natural_language_shell_command
from workstation.skills.core.direct_composition import preferred_workstation_skill_invocation_plan
from workstation.foundation.events.event_bus import append_workstation_receipt_and_publish, publish_workstation_event
from workstation.foundation.host.learning_capture import capture_workstation_chat_learning_from_tool_receipts
from workstation.foundation.host.controller_runtime import controller_runtime_provider
from workstation.foundation.models import (
    WorkstationAttachment,
    WorkstationDelegationEscalationDecision,
    WorkstationDelegationEscalationRequest,
    WorkstationSession,
)
from workstation.contracts.runtime import (
    GovernedTurnRequest,
    GovernedTurnRuntimeProvider,
)
from workstation.skills.planning.skill_composition_planning import preferred_workstation_skill_composition_plan
from workstation.skills.planning.skill_home import resolve_workstation_skill_home, workstation_skill_home_metadata
from workstation.skills.core.skill_invocation import workstation_skill_invocation_status_answer
from workstation.skills.core.skill_management import (
    write_workstation_prompt_skill_shortlist,
    write_workstation_skill_catalog,
)
from workstation.foundation.host.task_contract import normalize_prompt_to_task_boundary_contract
from workstation.runtime.core.llm_driver import run_workstation_openai_turn


def launch_workstation_session(
    *,
    root_path: Path,
    workspace_path: Path,
    blend_world_path: Path | None = None,
    skills_sqlite_path: Path | None = None,
    attach_default_skill_home: bool = True,
    initial_task: str = "",
    workspace_name: str = "main",
    allowed_capabilities: tuple[str, ...] | None = None,
    openai_env_var: str = "OPENAI_API_KEY",
    openai_profile: str = "openai_default",
    allow_direct_llm_decomposition: bool = True,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like creating one governed workstation session, helps with materializing the workstation root, attachments, discovery files, and session metadata.

    Reference to Theory:
        Supports the workstation session model by making attachments, capabilities, and discovery surfaces explicit under a host-owned launcher.

    Example Input Output:
        Input: `launch_workstation_session(root_path=Path('/tmp/ws'), workspace_path=Path('/tmp/project'), blend_world_path=Path('/tmp/ws-world'), skills_sqlite_path=Path('/tmp/skills.sqlite3'), attach_default_skill_home=True, initial_task='Inspect the project.')`
        Output: {'session_id': 'ws_123', 'root_path': '/tmp/ws', 'attachments': [{'name': 'main', 'kind': 'workspace'}], 'allowed_capabilities': ['ws.repo.tree']}

    Args:
        root_path: Value for `root_path` used by `launch_workstation_session`. Expected type: `Path`.
        workspace_path: Value for `workspace_path` used by `workspace_path`. Expected type: `Path`.
        blend_world_path: Value for `blend_world_path` used by `blend_world_path`. Expected type: `Path | None`. Defaults to `None`.
        skills_sqlite_path: Value for `skills_sqlite_path` used by `launch_workstation_session`. Expected type: `Path | None`. Defaults to `None`.
        attach_default_skill_home: Value for `attach_default_skill_home` used by `attach_default_skill_home`. Expected type: `bool`. Defaults to `True`.
        initial_task: Value for `initial_task` used by `initial_task`. Expected type: `str`. Defaults to `''`.
        workspace_name: Value for `workspace_name` used by `workspace_name`. Expected type: `str`. Defaults to `'main'`.
        allowed_capabilities: Value for `allowed_capabilities` used by `allowed_capabilities`. Expected type: `tuple[str, ...]`. Defaults to `DEFAULT_WORKSTATION_CAPABILITIES`.
        openai_env_var: Value for `openai_env_var` used by `openai_env_var`. Expected type: `str`. Defaults to `'OPENAI_API_KEY'`.
        openai_profile: Value for `openai_profile` used by `openai_profile`. Expected type: `str`. Defaults to `'openai_default'`.
        allow_direct_llm_decomposition: Value for `allow_direct_llm_decomposition` used by `allow_direct_llm_decomposition`. Expected type: `bool`. Defaults to `True`.

    Returns:
        dict[str, Any]: Result produced by `launch_workstation_session`.
    """
    if allowed_capabilities is None:
        allowed_capabilities = DEFAULT_WORKSTATION_CAPABILITIES
    root = Path(root_path).expanduser().resolve()
    workspace = Path(workspace_path).expanduser().resolve()
    blend_world = (
        ensure_persisted_blend_workstation_world(
            root_path=blend_world_path,
            workspace_path=workspace,
            workspace_name=workspace_name,
        )
        if blend_world_path is not None
        else None
    )
    skill_home = (
        resolve_workstation_skill_home(skills_sqlite_path=skills_sqlite_path, ensure_exists=True)
        if (skills_sqlite_path is not None or attach_default_skill_home)
        else {}
    )
    skills_path = Path(skill_home["store_path"]).resolve() if skill_home else None
    root.mkdir(parents=True, exist_ok=True)
    (root / "mounts").mkdir(parents=True, exist_ok=True)
    (root / "scratch").mkdir(parents=True, exist_ok=True)
    (root / "output").mkdir(parents=True, exist_ok=True)
    (root / "receipts").mkdir(parents=True, exist_ok=True)
    ensure_blend_workflow_store(root)
    workspace_source = blend_world_mount_source(blend_world, workspace_name) or workspace
    scratch_source = blend_world_mount_source(blend_world, "scratch") or (root / "scratch").resolve()
    output_source = blend_world_mount_source(blend_world, "output") or (root / "output").resolve()
    symlink_path = root / "mounts" / workspace_name
    if symlink_path.exists() or symlink_path.is_symlink():
        if symlink_path.is_dir() and not symlink_path.is_symlink():
            shutil.rmtree(symlink_path)
        else:
            symlink_path.unlink()
    if workspace_source == root:
        # When the workstation root doubles as the attached workspace, a
        # self-referential symlink would create an unusable recursive mount.
        symlink_path.mkdir(parents=True, exist_ok=True)
    else:
        symlink_path.symlink_to(workspace_source, target_is_directory=True)

    attachments = (
        WorkstationAttachment(
            name="session",
            kind="session_root",
            source=str(root),
            access_mode="read_write",
            mount_path="/workstation/session",
        ),
        WorkstationAttachment(
            name=workspace_name,
            kind="workspace",
            source=str(workspace_source),
            access_mode="read_write",
            mount_path=f"/workstation/mounts/{workspace_name}",
            metadata=_blend_world_attachment_metadata(blend_world, workspace_name),
        ),
        WorkstationAttachment(
            name="scratch",
            kind="scratch",
            source=str(scratch_source),
            access_mode="read_write",
            mount_path="/workstation/scratch",
            metadata=_blend_world_attachment_metadata(blend_world, "scratch"),
        ),
        WorkstationAttachment(
            name="output",
            kind="output",
            source=str(output_source),
            access_mode="write",
            mount_path="/workstation/output",
            metadata=_blend_world_attachment_metadata(blend_world, "output"),
        ),
        WorkstationAttachment(
            name="openai",
            kind="secret_ref",
            source=f"host:{openai_env_var}",
            access_mode="indirect",
            mount_path="/workstation/secrets/openai",
            metadata={"profile": openai_profile},
        ),
    )
    attachments = _with_default_workstation_attachment_aliases(attachments, workspace_name=workspace_name)
    if skills_path is not None:
        skill_home_metadata = workstation_skill_home_metadata(skill_home)
        attachments = attachments + (
            WorkstationAttachment(
                name="skills",
                kind="skill_store",
                source=str(skills_path),
                access_mode="read_write",
                mount_path="/workstation/skills/store.sqlite3",
                metadata=skill_home_metadata,
            ),
            WorkstationAttachment(
                name="skills_exports",
                kind="skill_exports",
                source=str(skill_home["exports_path"]),
                access_mode="read_write",
                mount_path="/workstation/skills/exports",
                metadata=skill_home_metadata,
            ),
            WorkstationAttachment(
                name="skills_imports",
                kind="skill_imports",
                source=str(skill_home["imports_path"]),
                access_mode="read_write",
                mount_path="/workstation/skills/imports",
                metadata=skill_home_metadata,
            ),
        )
        adjusted_capabilities = list(allowed_capabilities)
        for required_capability in ("ws.skill.invoke", "ws.skill.compose"):
            if required_capability not in adjusted_capabilities:
                adjusted_capabilities.append(required_capability)
        for required_capability in ("ws.skill.catalog", "ws.skill.import", "ws.skill.export"):
            if required_capability not in adjusted_capabilities:
                adjusted_capabilities.append(required_capability)
        allowed_capabilities = tuple(adjusted_capabilities)
    session = WorkstationSession(
        session_id=f"ws_{uuid.uuid4().hex[:12]}",
        root_path=str(root),
        created_at=datetime.now(timezone.utc).isoformat(),
        attachments=attachments,
        allowed_capabilities=tuple(allowed_capabilities),
        openai_profile=openai_profile,
        openai_env_var=openai_env_var,
        initial_task=str(initial_task or ""),
        allow_direct_llm_decomposition=bool(allow_direct_llm_decomposition),
    )
    _write_json(root / "SESSION.json", session.to_dict())
    _write_json(root / "ATTACHMENTS.json", {"attachments": [item.to_dict() for item in attachments]})
    _write_json(root / "TOOLS.json", {"tools": list_workstation_tool_definitions(session)})
    _write_blend_discovery_files(root, session, blend_world=blend_world)
    ensure_blend_workflow_store(root)
    if skills_path is not None:
        write_workstation_skill_catalog(root, session)
        write_workstation_prompt_skill_shortlist(root, session=session, prompt=initial_task or "")
    (root / "MESSAGES.jsonl").write_text("")
    (root / "GOVERNED_TURNS.jsonl").write_text("")
    (root / "receipts" / "events.jsonl").write_text("")
    (root / "TASK.md").write_text(initial_task.strip() or "No active task yet.\n")
    (root / "README.md").write_text(_render_readme(session))
    (root / "WORKSTATION.toml").write_text(_render_workstation_toml(session))
    return session.to_dict()


def load_workstation_session(root_path: Path) -> WorkstationSession:
    """
    High Level Purpose:
        In circumstances like prompt handling for an existing workstation session, helps with loading the persisted workstation metadata from the session root.

    Reference to Theory:
        Supports the workstation session model by letting the host-owned session driver resume against explicit session state.

    Example Input Output:
        Input: `load_workstation_session(root_path=Path('/tmp/ws'))`
        Output: WorkstationSession(session_id='ws_123', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=(), openai_profile='openai_default', openai_env_var='OPENAI_API_KEY', initial_task='')

    Args:
        root_path: Value for `root_path` used by `load_workstation_session`. Expected type: `Path`.

    Returns:
        WorkstationSession: Result produced by `load_workstation_session`.
    """
    root = Path(root_path).expanduser().resolve()
    payload = json.loads((root / "SESSION.json").read_text())
    session = WorkstationSession.from_dict(payload)
    attachments = list(session.attachments)
    if not any(attachment.kind == "session_root" for attachment in attachments):
        attachments.insert(
            0,
            WorkstationAttachment(
                name="session",
                kind="session_root",
                source=str(root),
                access_mode="read_write",
                mount_path="/workstation/session",
            ),
        )
    if not any(attachment.kind == "skill_store" for attachment in attachments):
        skill_home = resolve_workstation_skill_home(ensure_exists=True)
        skill_home_metadata = workstation_skill_home_metadata(skill_home)
        attachments.extend(
            [
                WorkstationAttachment(
                    name="skills",
                    kind="skill_store",
                    source=str(skill_home["store_path"]),
                    access_mode="read_write",
                    mount_path="/workstation/skills/store.sqlite3",
                    metadata=skill_home_metadata,
                ),
                WorkstationAttachment(
                    name="skills_exports",
                    kind="skill_exports",
                    source=str(skill_home["exports_path"]),
                    access_mode="read_write",
                    mount_path="/workstation/skills/exports",
                    metadata=skill_home_metadata,
                ),
                WorkstationAttachment(
                    name="skills_imports",
                    kind="skill_imports",
                    source=str(skill_home["imports_path"]),
                    access_mode="read_write",
                    mount_path="/workstation/skills/imports",
                    metadata=skill_home_metadata,
                ),
            ]
        )
    attachments = list(
        _with_default_workstation_attachment_aliases(
            tuple(attachments),
            workspace_name=next(
                (
                    attachment.name
                    for attachment in attachments
                    if attachment.kind == "workspace" and str(attachment.metadata.get("alias_of", "")) == ""
                ),
                "main",
            ),
        )
    )
    upgraded = WorkstationSession(
        session_id=session.session_id,
        root_path=session.root_path,
        created_at=session.created_at,
        attachments=tuple(attachments),
        allowed_capabilities=tuple(session.allowed_capabilities),
        openai_profile=session.openai_profile,
        openai_env_var=session.openai_env_var,
        initial_task=session.initial_task,
        allow_direct_llm_decomposition=bool(session.allow_direct_llm_decomposition),
    )
    if upgraded.to_dict() != payload:
        persist_workstation_session(root, upgraded)
    return upgraded


def persist_workstation_session(root_path: Path, session: WorkstationSession) -> None:
    """
    High Level Purpose:
        In circumstances like workstation session mutation after launch, helps with rewriting the canonical session and discovery files so capability changes remain durable and visible to later turns.

    Reference to Theory:
        Supports the workstation shell by keeping session mutation explicit and synchronized across `SESSION.json`, tool discovery, attachments, and human-readable workstation metadata.

    Example Input Output:
        Input: `persist_workstation_session(root_path=Path('/tmp/ws'), session=3)`
        Output: None

    Args:
        root_path: Value for `root_path` used by `root_path`. Expected type: `Path`.
        session: Value for `session` used by `session`. Expected type: `WorkstationSession`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    root = Path(root_path).expanduser().resolve()
    _write_json(root / "SESSION.json", session.to_dict())
    _write_json(root / "ATTACHMENTS.json", {"attachments": [item.to_dict() for item in session.attachments]})
    _write_json(root / "TOOLS.json", {"tools": list_workstation_tool_definitions(session)})
    _write_blend_discovery_files(root, session, blend_world=_blend_world_from_session(session))
    if any(attachment.kind == "skill_store" for attachment in session.attachments):
        write_workstation_skill_catalog(root, session)
    (root / "README.md").write_text(_render_readme(session))
    (root / "WORKSTATION.toml").write_text(_render_workstation_toml(session))


def _with_default_workstation_attachment_aliases(
    attachments: tuple[WorkstationAttachment, ...],
    *,
    workspace_name: str,
) -> tuple[WorkstationAttachment, ...]:
    """
    High Level Purpose:
        In circumstances like workstation launch and legacy-session upgrade, helps with adding the conventional trial-compatible attachment aliases that map the workstation shell onto the broader trial worker corpus.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by keeping the shell attachment vocabulary compatible with imported workers without rewriting worker bundles.

    Example Input Output:
        Input: `_with_default_workstation_attachment_aliases(attachments=(WorkstationAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), workspace_name='main')`
        Output: (WorkstationAttachment(name='main', ...), WorkstationAttachment(name='skill_input', ...))

    Args:
        attachments: Value for `attachments` used by `_with_default_workstation_attachment_aliases`. Expected type: `tuple[WorkstationAttachment, ...]`.
        workspace_name: Value for `workspace_name` used by `_with_default_workstation_attachment_aliases`. Expected type: `str`.

    Returns:
        tuple[WorkstationAttachment, ...]: Result produced by `_with_default_workstation_attachment_aliases`.
    """
    by_name = {attachment.name: attachment for attachment in attachments}
    workspace_attachment = by_name.get(workspace_name)
    scratch_attachment = by_name.get("scratch")
    output_attachment = by_name.get("output")
    augmented = list(attachments)

    def ensure_alias(alias_name: str, source_attachment: WorkstationAttachment | None, *, access_mode: str | None = None) -> None:
        if alias_name in by_name or source_attachment is None:
            return
        augmented.append(
            WorkstationAttachment(
                name=alias_name,
                kind=source_attachment.kind,
                source=source_attachment.source,
                access_mode=access_mode or source_attachment.access_mode,
                mount_path=f"/workstation/mounts/{alias_name}",
                metadata={**dict(source_attachment.metadata), "alias_of": source_attachment.name},
            )
        )

    ensure_alias("skill_input", workspace_attachment, access_mode="read")
    ensure_alias("skill_tmp", scratch_attachment)
    ensure_alias("skill_output", output_attachment)
    return tuple(augmented)

def prompt_workstation_session(
    *,
    root_path: Path,
    prompt: str,
    model: str | None = None,
    client: Any | None = None,
    max_tool_rounds: int = 8,
    force_llm_only: bool = False,
    interaction_mode: str = "normal",
    governed_treatment: str = "independent",
    governed_parent_run_id: str = "",
    governed_llm_policy: str = "auto",
    governed_max_steps: int = 256,
    delegation_approval_callback: Callable[[WorkstationDelegationEscalationRequest], WorkstationDelegationEscalationDecision | bool | None] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like one end-to-end workstation turn, helps with normalizing the user prompt, updating session files, running the host-owned LLM/tool loop, and recording receipts.

    Reference to Theory:
        Supports the workstation prompt model by combining boundary-complete task normalization with host-owned capability mediation and receipt emission.

    Example Input Output:
        Input: `prompt_workstation_session(root_path=Path('/tmp/ws'), prompt='Inspect the project.')`
        Output: {'assistant_text': 'I inspected the project.', 'task_contract': {'semantic_unit': 'Inspect the project.'}, 'tool_receipts': []}

    Args:
        root_path: Value for `root_path` used by `root_path`. Expected type: `Path`.
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.
        model: Value for `model` used by `model`. Expected type: `str | None`. Defaults to `None`.
        client: Value for `client` used by `client`. Expected type: `Any | None`. Defaults to `None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`. Defaults to `8`.
        delegation_approval_callback: Value for `delegation_approval_callback` used by `delegation_approval_callback`. Expected type: `Callable[[WorkstationDelegationEscalationRequest], WorkstationDelegationEscalationDecision | bool | None] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `prompt_workstation_session`.
    """
    root = Path(root_path).expanduser().resolve()
    session = load_workstation_session(root)
    normalized_interaction_mode = collapse_ws(interaction_mode).casefold() or "normal"
    if force_llm_only:
        if normalized_interaction_mode == "governed_reduction":
            raise ValueError("LLM-only and governed-reduction modes are mutually exclusive.")
        normalized_interaction_mode = "llm_only"
    if normalized_interaction_mode not in {"normal", "llm_only", "governed_reduction"}:
        raise ValueError(f"Unsupported workstation interaction mode: {interaction_mode}")
    normalized_governed_treatment = collapse_ws(governed_treatment).casefold() or "independent"
    if normalized_governed_treatment not in {
        "independent",
        "human_contribution",
        "follow_up",
        "correction",
    }:
        raise ValueError(f"Unsupported governed turn treatment: {governed_treatment}")
    if normalized_interaction_mode != "governed_reduction" and normalized_governed_treatment != "independent":
        raise ValueError("Governed turn treatment requires governed-reduction mode.")
    normalized_governed_llm_policy = collapse_ws(governed_llm_policy).casefold() or "auto"
    if normalized_governed_llm_policy not in {"off", "auto", "required"}:
        raise ValueError(f"Unsupported governed LLM policy: {governed_llm_policy}")
    task_contract = normalize_prompt_to_task_boundary_contract(prompt)
    _write_json(root / "TASK_CONTRACT.json", task_contract.to_dict())
    (root / "TASK.md").write_text(prompt.strip() + "\n")
    if any(attachment.kind == "skill_store" for attachment in session.attachments):
        write_workstation_prompt_skill_shortlist(root, session=session, prompt=prompt)
    turn_id = f"turn_{uuid.uuid4().hex}"
    user_message = _append_message(
        root,
        {
            "role": "user",
            "content": prompt,
            "turn_id": turn_id,
            "interaction_mode": normalized_interaction_mode,
        },
    )
    publish_workstation_event(
        root_path=root,
        session_id=session.session_id,
        event_kind="turn_started",
        payload={
            "prompt": prompt,
            "task_contract": task_contract.to_dict(),
            "model": str(model or ""),
            "max_tool_rounds": int(max_tool_rounds),
            "turn_id": turn_id,
            "message_id": user_message["message_id"],
            "interaction_mode": normalized_interaction_mode,
            "governed_treatment": normalized_governed_treatment,
        },
    )
    append_workstation_receipt_and_publish(
        root_path=root,
        session_id=session.session_id,
        receipt=host_interaction_user_prompt_receipt(
            prompt=prompt,
            task_contract=task_contract.to_dict(),
        ),
    )
    message_history = _load_message_history(root)

    if normalized_interaction_mode == "governed_reduction":
        parent_binding = (
            _resolve_governed_turn_binding(
                root,
                run_id=collapse_ws(governed_parent_run_id),
            )
            if normalized_governed_treatment != "independent"
            else None
        )
        governed_root = root / "governed_reduction"
        states_root = governed_root / "states"
        states_root.mkdir(parents=True, exist_ok=True)
        sqlite_path = governed_root / "artifacts.sqlite3"
        checkpoint_path = (
            Path(str(parent_binding["checkpoint_path"])).expanduser().resolve()
            if normalized_governed_treatment == "human_contribution" and parent_binding is not None
            else states_root / f"{turn_id}.json"
        )
        runtime_provider = controller_runtime_provider()
        if not isinstance(runtime_provider, GovernedTurnRuntimeProvider):
            raise RuntimeError(
                "The configured controller provider does not support governed turns."
            )
        governed_result = runtime_provider.perform_governed_turn(
            GovernedTurnRequest(
                session_id=session.session_id,
                turn_id=turn_id,
                user_message_id=str(user_message["message_id"]),
                prompt=prompt,
                treatment=normalized_governed_treatment,
                checkpoint_path=checkpoint_path,
                sqlite_path=sqlite_path,
                parent_run_id=(
                    str(parent_binding.get("run_id", ""))
                    if parent_binding is not None
                    else ""
                ),
                parent_checkpoint_path=(
                    Path(str(parent_binding["checkpoint_path"]))
                    if parent_binding is not None
                    else None
                ),
                llm_policy=normalized_governed_llm_policy,
                max_steps=max(0, int(governed_max_steps)),
            )
        )
        assistant_message = _append_message(
            root,
            {
                "role": "assistant",
                "content": governed_result.assistant_text,
                "turn_id": turn_id,
                "interaction_mode": normalized_interaction_mode,
                "governed_run_id": governed_result.run_id,
            },
        )
        binding = {
            "binding_id": f"binding_{uuid.uuid4().hex}",
            "session_id": session.session_id,
            "turn_id": turn_id,
            "user_message_id": user_message["message_id"],
            "assistant_message_id": assistant_message["message_id"],
            "treatment": normalized_governed_treatment,
            "run_id": governed_result.run_id,
            "parent_run_id": governed_result.parent_run_id,
            "checkpoint_path": str(governed_result.checkpoint_path),
            "sqlite_path": str(governed_result.sqlite_path),
            "run_outcome": governed_result.run_outcome,
            "root_status": governed_result.root_status,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(root / "GOVERNED_TURNS.jsonl", binding)
        turn_report = {
            "assistant_text": governed_result.assistant_text,
            "tool_receipts": [],
            "model": "realized-core",
            "rounds": 0,
            "fulfilled_by": "governed_reduction",
            "fallback_used": False,
            "interaction_mode": normalized_interaction_mode,
            "governed_treatment": normalized_governed_treatment,
            "turn_id": turn_id,
            "run_id": governed_result.run_id,
            "parent_run_id": governed_result.parent_run_id,
            "run_outcome": governed_result.run_outcome,
            "checkpoint_path": str(governed_result.checkpoint_path),
            "binding": binding,
        }
        _write_json(root / "LAST_RESPONSE.json", turn_report)
        append_workstation_receipt_and_publish(
            root_path=root,
            session_id=session.session_id,
            receipt=host_interaction_assistant_response_receipt(
                assistant_text=governed_result.assistant_text,
                model="realized-core",
                rounds=0,
                tool_calls=0,
                fulfilled_by="governed_reduction",
                fallback_used=False,
            ),
        )
        _publish_turn_finished_event(
            root=root,
            session=session,
            assistant_text=governed_result.assistant_text,
            fulfilled_by="governed_reduction",
            tool_calls=0,
            model="realized-core",
        )
        return {
            "session_id": session.session_id,
            "root_path": str(root),
            "task_contract": task_contract.to_dict(),
            **turn_report,
        }

    if normalized_interaction_mode == "llm_only":
        turn_report = run_workstation_openai_turn(
            session=session,
            task_contract=task_contract,
            prompt=prompt,
            message_history=message_history,
            tool_definitions=[],
            tool_executor=lambda _capability_name, _arguments: {
                "status": "unsupported",
                "answer": "This prompt was run in LLM-only mode and cannot invoke workstation tools.",
            },
            model=model,
            client=client,
            max_tool_rounds=1,
        )
        turn_report["turn_id"] = turn_id
        turn_report["interaction_mode"] = normalized_interaction_mode
        _append_message(
            root,
            {
                "role": "assistant",
                "content": turn_report["assistant_text"],
                "turn_id": turn_id,
                "interaction_mode": normalized_interaction_mode,
            },
        )
        _write_json(root / "LAST_RESPONSE.json", turn_report)
        append_workstation_receipt_and_publish(
            root_path=root,
            session_id=session.session_id,
            receipt=host_interaction_assistant_response_receipt(
                assistant_text=turn_report["assistant_text"],
                model=turn_report["model"],
                rounds=turn_report["rounds"],
                tool_calls=len(turn_report["tool_receipts"]),
                requested_skill="",
                fulfilled_by=collapse_ws(str(turn_report.get("fulfilled_by", ""))),
                fallback_used=turn_report.get("fallback_used"),
            ),
        )
        _publish_turn_finished_event(
            root=root,
            session=session,
            assistant_text=turn_report["assistant_text"],
            fulfilled_by=collapse_ws(str(turn_report.get("fulfilled_by", ""))),
            requested_skill="",
            tool_calls=len(turn_report["tool_receipts"]),
            model=turn_report["model"],
        )
        return {
            "session_id": session.session_id,
            "root_path": str(root),
            "task_contract": task_contract.to_dict(),
            "assistant_text": turn_report["assistant_text"],
            "tool_receipts": turn_report["tool_receipts"],
            "model": turn_report["model"],
            "rounds": turn_report["rounds"],
            "learning_context_updates": [],
            "turn_id": turn_id,
            "interaction_mode": normalized_interaction_mode,
        }

    handled_shell_utility, shell_utility_report = run_workstation_natural_language_shell_command(
        root=root,
        prompt=prompt,
    )
    if handled_shell_utility:
        turn_report = {
            "assistant_text": str(shell_utility_report.get("assistant_text", "")).strip(),
            "tool_receipts": [],
            "model": "workstation-shell-command",
            "rounds": 0,
            "fulfilled_by": collapse_ws(str(shell_utility_report.get("fulfilled_by", ""))),
            "fallback_used": False,
            "turn_id": turn_id,
            "interaction_mode": normalized_interaction_mode,
        }
        _append_message(
            root,
            {
                "role": "assistant",
                "content": turn_report["assistant_text"],
                "turn_id": turn_id,
                "interaction_mode": normalized_interaction_mode,
            },
        )
        _write_json(root / "LAST_RESPONSE.json", turn_report)
        append_workstation_receipt_and_publish(
            root_path=root,
            session_id=session.session_id,
            receipt=host_interaction_assistant_response_receipt(
                assistant_text=turn_report["assistant_text"],
                model=turn_report["model"],
                rounds=turn_report["rounds"],
                tool_calls=len(turn_report["tool_receipts"]),
                fulfilled_by=turn_report["fulfilled_by"],
                fallback_used=False,
            ),
        )
        _publish_turn_finished_event(
            root=root,
            session=session,
            assistant_text=turn_report["assistant_text"],
            fulfilled_by=turn_report["fulfilled_by"],
            tool_calls=len(turn_report["tool_receipts"]),
            model=turn_report["model"],
        )
        return {
            "session_id": session.session_id,
            "root_path": str(root),
            "task_contract": task_contract.to_dict(),
            **turn_report,
        }

    def tool_executor(capability_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        append_workstation_receipt_and_publish(
            root_path=root,
            session_id=session.session_id,
            receipt=host_interaction_capability_call_receipt(
                capability=capability_name,
                arguments=arguments,
                result={"status": "started"},
                phase="started",
            ),
        )
        try:
            result = execute_workstation_capability(session, capability_name, arguments)
        except Exception as exc:
            result = {
                "status": "error",
                "capability": capability_name,
                "arguments": dict(arguments),
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        append_workstation_receipt_and_publish(
            root_path=root,
            session_id=session.session_id,
            receipt=host_interaction_capability_call_receipt(
                capability=capability_name,
                arguments=arguments,
                result=result,
                phase="approval_required" if result.get("status") == "approval_required" else "",
            ),
        )
        if result.get("status") == "approval_required" and delegation_approval_callback is not None:
            result = _resolve_workstation_escalation_if_requested(
                root=root,
                session=session,
                capability_name=capability_name,
                arguments=arguments,
                initial_result=result,
                delegation_approval_callback=delegation_approval_callback,
            )
            append_workstation_receipt_and_publish(
                root_path=root,
                session_id=session.session_id,
                receipt=host_interaction_capability_call_receipt(
                    capability=capability_name,
                    arguments=arguments,
                    result=result,
                    phase="completed",
                ),
            )
        return result

    if "ws.workflow.run" in session.allowed_capabilities or "ws.skill.compose" in session.allowed_capabilities:
        composition_plan = preferred_workstation_skill_composition_plan(session=session, prompt=prompt)
        if composition_plan is not None:
            workflow_capability = "ws.workflow.run" if "ws.workflow.run" in session.allowed_capabilities else "ws.skill.compose"
            workflow_arguments = (
                {"workflow_plan": blend_workflow_plan_from_skill_compose_arguments(composition_plan).to_dict()}
                if workflow_capability == "ws.workflow.run"
                else composition_plan
            )
            composition_result = tool_executor(workflow_capability, workflow_arguments)
            composition_answer = str(composition_result.get("answer", "") or "").strip()
            if composition_answer:
                requested_skill_titles = [
                    collapse_ws(str(item))
                    for item in composition_result.get("requested_skill_titles", [])
                    if collapse_ws(str(item))
                ]
                turn_report = {
                    "assistant_text": composition_answer,
                    "tool_receipts": [
                        {
                            "name": workflow_capability,
                            "arguments": workflow_arguments,
                            "result": composition_result,
                        }
                    ],
                    "model": "workstation-direct-composition",
                    "rounds": 0,
                    "direct_result_status": collapse_ws(str(composition_result.get("status", ""))).casefold(),
                    "turn_id": turn_id,
                    "interaction_mode": normalized_interaction_mode,
                }
                _append_message(
                    root,
                    {
                        "role": "assistant",
                        "content": turn_report["assistant_text"],
                        "turn_id": turn_id,
                        "interaction_mode": normalized_interaction_mode,
                    },
                )
                _write_json(root / "LAST_RESPONSE.json", turn_report)
                append_workstation_receipt_and_publish(
                    root_path=root,
                    session_id=session.session_id,
                    receipt=host_interaction_assistant_response_receipt(
                        assistant_text=turn_report["assistant_text"],
                        model=turn_report["model"],
                        rounds=turn_report["rounds"],
                        tool_calls=len(turn_report["tool_receipts"]),
                        requested_skill=" -> ".join(requested_skill_titles),
                        fulfilled_by=workflow_capability,
                        fallback_used=False,
                    ),
                )
                _publish_turn_finished_event(
                    root=root,
                    session=session,
                    assistant_text=turn_report["assistant_text"],
                    fulfilled_by=workflow_capability,
                    requested_skill=" -> ".join(requested_skill_titles),
                    tool_calls=len(turn_report["tool_receipts"]),
                    model=turn_report["model"],
                )
                return {
                    "session_id": session.session_id,
                    "root_path": str(root),
                    **turn_report,
                    "task_contract": task_contract.to_dict(),
                }

    if "ws.skill.invoke" in session.allowed_capabilities:
        direct_plan = preferred_workstation_skill_invocation_plan(session=session, prompt=prompt)
        if direct_plan is not None:
            direct_result = tool_executor("ws.skill.invoke", direct_plan)
            direct_status = collapse_ws(str(direct_result.get("status", ""))).casefold()
            direct_answer = workstation_skill_invocation_status_answer(direct_result)
            if direct_answer:
                turn_report = {
                    "assistant_text": str(direct_answer).strip(),
                    "tool_receipts": [
                        {
                            "name": "ws.skill.invoke",
                            "arguments": direct_plan,
                            "result": direct_result,
                        }
                    ],
                    "model": "workstation-direct-composition",
                    "rounds": 0,
                    "direct_result_status": direct_status,
                    "turn_id": turn_id,
                    "interaction_mode": normalized_interaction_mode,
                }
                _append_message(
                    root,
                    {
                        "role": "assistant",
                        "content": turn_report["assistant_text"],
                        "turn_id": turn_id,
                        "interaction_mode": normalized_interaction_mode,
                    },
                )
                _write_json(root / "LAST_RESPONSE.json", turn_report)
                append_workstation_receipt_and_publish(
                    root_path=root,
                    session_id=session.session_id,
                    receipt=host_interaction_assistant_response_receipt(
                        assistant_text=turn_report["assistant_text"],
                        model=turn_report["model"],
                        rounds=turn_report["rounds"],
                        tool_calls=len(turn_report["tool_receipts"]),
                        requested_skill=collapse_ws(str(direct_plan.get("skill_title", ""))),
                        fulfilled_by="ws.skill.invoke",
                        fallback_used=False,
                    ),
                )
                _publish_turn_finished_event(
                    root=root,
                    session=session,
                    assistant_text=turn_report["assistant_text"],
                    fulfilled_by="ws.skill.invoke",
                    requested_skill=collapse_ws(str(direct_plan.get("skill_title", ""))),
                    tool_calls=len(turn_report["tool_receipts"]),
                    model=turn_report["model"],
                )
                return {
                    "session_id": session.session_id,
                    "root_path": str(root),
                    **turn_report,
                    "task_contract": task_contract.to_dict(),
                }

    turn_report = run_workstation_openai_turn(
        session=session,
        task_contract=task_contract,
        prompt=prompt,
        message_history=message_history,
        tool_definitions=list_workstation_tool_definitions(session),
        tool_executor=tool_executor,
        model=model,
        client=client,
        max_tool_rounds=max_tool_rounds,
    )
    turn_report["turn_id"] = turn_id
    turn_report["interaction_mode"] = normalized_interaction_mode
    learning_context_update = capture_workstation_chat_learning_from_tool_receipts(
        session=session,
        prompt=prompt,
        tool_receipts=list(turn_report.get("tool_receipts", [])),
    )
    if learning_context_update is not None:
        turn_report["learning_context_updates"] = [learning_context_update]
    _append_message(
        root,
        {
            "role": "assistant",
            "content": turn_report["assistant_text"],
            "turn_id": turn_id,
            "interaction_mode": normalized_interaction_mode,
        },
    )
    _write_json(root / "LAST_RESPONSE.json", turn_report)
    append_workstation_receipt_and_publish(
        root_path=root,
        session_id=session.session_id,
        receipt=host_interaction_assistant_response_receipt(
            assistant_text=turn_report["assistant_text"],
            model=turn_report["model"],
            rounds=turn_report["rounds"],
            tool_calls=len(turn_report["tool_receipts"]),
            requested_skill=collapse_ws(str(turn_report.get("requested_skill", ""))),
            fulfilled_by=collapse_ws(str(turn_report.get("fulfilled_by", ""))),
            fallback_used=turn_report.get("fallback_used"),
        ),
    )
    _publish_turn_finished_event(
        root=root,
        session=session,
        assistant_text=turn_report["assistant_text"],
        fulfilled_by=collapse_ws(str(turn_report.get("fulfilled_by", ""))),
        requested_skill=collapse_ws(str(turn_report.get("requested_skill", ""))),
        tool_calls=len(turn_report["tool_receipts"]),
        model=turn_report["model"],
    )
    return {
        "session_id": session.session_id,
        "root_path": str(root),
        "task_contract": task_contract.to_dict(),
        "assistant_text": turn_report["assistant_text"],
        "tool_receipts": turn_report["tool_receipts"],
        "model": turn_report["model"],
        "rounds": turn_report["rounds"],
        "learning_context_updates": list(turn_report.get("learning_context_updates", [])),
        "turn_id": turn_id,
        "interaction_mode": normalized_interaction_mode,
    }


def _resolve_workstation_escalation_if_requested(
    *,
    root: Path,
    session: WorkstationSession,
    capability_name: str,
    arguments: dict[str, Any],
    initial_result: dict[str, Any],
    delegation_approval_callback: Callable[[WorkstationDelegationEscalationRequest], WorkstationDelegationEscalationDecision | bool | None],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation that exceeds the current session grant, helps with prompting the host-owned escalation callback, recording the decision, and replaying the capability call with one-invocation approved delegation when allowed.

    Reference to Theory:
        Supports the workstation escalation model by keeping approval at the host boundary, not inside the invoked skill.

    Example Input Output:
        Input: `_resolve_workstation_escalation_if_requested(root=Path('/tmp/ws'), session=3, capability_name='ws.skill.invoke', arguments={'skill_title': 'Workstation Greeting'}, initial_result={'status': 'approval_required', 'missing_delegation': [{'capability': 'ws.fs.write', 'target': 'scratch'}]}, delegation_approval_callback=lambda request: True)`
        Output: {'status': 'ok', 'capability': 'ws.skill.invoke', 'skill_title': 'Workstation Greeting'}

    Args:
        root: Value for `root` used by `_resolve_workstation_escalation_if_requested`. Expected type: `Path`.
        session: Value for `session` used by `_resolve_workstation_escalation_if_requested`. Expected type: `WorkstationSession`.
        capability_name: Value for `capability_name` used by `_resolve_workstation_escalation_if_requested`. Expected type: `str`.
        arguments: Value for `arguments` used by `_resolve_workstation_escalation_if_requested`. Expected type: `dict[str, Any]`.
        initial_result: Value for `initial_result` used by `_resolve_workstation_escalation_if_requested`. Expected type: `dict[str, Any]`.
        delegation_approval_callback: Value for `delegation_approval_callback` used by `_resolve_workstation_escalation_if_requested`. Expected type: `Callable[[WorkstationDelegationEscalationRequest], WorkstationDelegationEscalationDecision | bool | None]`.

    Returns:
        dict[str, Any]: Result produced by `_resolve_workstation_escalation_if_requested`.
    """
    missing_delegation = normalized_requested_delegation(initial_result.get("missing_delegation"))
    escalation_request = WorkstationDelegationEscalationRequest(
        capability=capability_name,
        target=str(initial_result.get("target", "")),
        skill_title=str(initial_result.get("skill_title", "")),
        requested_delegation=tuple(missing_delegation),
        rationale=str(arguments.get("rationale", "")),
        scope="one_invocation",
    )
    append_workstation_receipt_and_publish(
        root_path=root,
        session_id=session.session_id,
        receipt=host_interaction_delegation_approval_requested_receipt(
            request=escalation_request.to_dict(),
        ),
    )
    decision = _normalize_workstation_escalation_decision(
        delegation_approval_callback(escalation_request)
    )
    append_workstation_receipt_and_publish(
        root_path=root,
        session_id=session.session_id,
        receipt=host_interaction_delegation_approval_decision_receipt(
            request=escalation_request.to_dict(),
            decision=decision.to_dict(),
        ),
    )
    if not decision.approved:
        denied_result = dict(initial_result)
        denied_result["escalation"] = decision.to_dict()
        return denied_result
    approved_delegation = normalized_requested_delegation(
        [*arguments.get("approved_delegation", []), *missing_delegation]
    )
    retry_arguments = dict(arguments)
    retry_arguments["approved_delegation"] = approved_delegation
    retry_arguments["approved_delegation_scope"] = decision.scope
    retried_result = execute_workstation_capability(session, capability_name, retry_arguments)
    retried_result["escalation"] = {
        **decision.to_dict(),
        "requested_delegation": [dict(item) for item in missing_delegation],
    }
    append_workstation_receipt_and_publish(
        root_path=root,
        session_id=session.session_id,
        receipt=host_interaction_capability_call_receipt(
            capability=capability_name,
            arguments=retry_arguments,
            result=retried_result,
            phase="after_escalation",
        ),
    )
    return retried_result


def _publish_turn_finished_event(
    *,
    root: Path,
    session: WorkstationSession,
    assistant_text: str,
    fulfilled_by: str,
    tool_calls: int,
    model: str,
    requested_skill: str = "",
) -> None:
    publish_workstation_event(
        root_path=root,
        session_id=session.session_id,
        event_kind="turn_finished",
        payload={
            "assistant_text": collapse_ws(str(assistant_text)),
            "fulfilled_by": collapse_ws(str(fulfilled_by)),
            "requested_skill": collapse_ws(str(requested_skill)),
            "tool_calls": int(tool_calls),
            "model": collapse_ws(str(model)),
        },
    )


def _normalize_workstation_escalation_decision(
    decision: WorkstationDelegationEscalationDecision | bool | None,
) -> WorkstationDelegationEscalationDecision:
    """
    High Level Purpose:
        In circumstances like host-owned workstation escalation prompting, helps with normalizing callback return values into one stable escalation-decision object.

    Reference to Theory:
        Supports the workstation escalation model by keeping host approval decisions explicit and uniform for receipts and replay.

    Example Input Output:
        Input: `_normalize_workstation_escalation_decision(True)`
        Output: WorkstationDelegationEscalationDecision(approved=True, scope='one_invocation', rationale='')

    Args:
        decision: Value for `decision` used by `_normalize_workstation_escalation_decision`. Expected type: `WorkstationDelegationEscalationDecision | bool | None`.

    Returns:
        WorkstationDelegationEscalationDecision: Result produced by `_normalize_workstation_escalation_decision`.
    """
    if isinstance(decision, WorkstationDelegationEscalationDecision):
        return decision
    return WorkstationDelegationEscalationDecision(
        approved=bool(decision),
        scope="one_invocation",
        rationale="",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """
    High Level Purpose:
        In circumstances like workstation file materialization and turn recording, helps with writing stable pretty-printed JSON files into the workstation root.

    Reference to Theory:
        Supports the workstation discovery and receipt surfaces by keeping machine-readable files explicit and inspectable.

    Example Input Output:
        Input: `_write_json(path=Path('/tmp/ws/SESSION.json'), payload={'session_id': 'ws_1'})`
        Output: None

    Args:
        path: Value for `path` used by `_write_json`. Expected type: `Path`.
        payload: Value for `payload` used by `_write_json`. Expected type: `dict[str, Any]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(json_safe(payload), indent=2, sort_keys=True) + "\n"
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp_path.write_text(rendered)
    temp_path.replace(path)


def _write_blend_discovery_files(root: Path, session: WorkstationSession, *, blend_world: BlendWorld | None = None) -> None:
    _write_json(root / "BLEND_CONTEXT.json", blend_context_from_workstation_session(session).to_dict())
    _write_json(root / "BLEND_SESSION.json", blend_session_from_workstation_session(session).to_dict())
    if blend_world is not None:
        _write_json(root / "BLEND_WORLD.json", blend_world.to_dict())


def _blend_world_attachment_metadata(blend_world: BlendWorld | None, mount_name: str) -> dict[str, Any]:
    if blend_world is None:
        return {}
    for mount in blend_world.mounts:
        if str(mount.name) != str(mount_name):
            continue
        return {
            "blend_world_id": blend_world.world_id,
            "blend_world_root": blend_world.root_path,
            "blend_world_mount": mount.name,
        }
    return {}


def _blend_world_from_session(session: WorkstationSession) -> BlendWorld | None:
    world_id = ""
    world_root = ""
    mounts: list[dict[str, Any]] = []
    for attachment in session.attachments:
        metadata = dict(attachment.metadata)
        if str(metadata.get("alias_of", "")).strip():
            continue
        attachment_world_id = str(metadata.get("blend_world_id", "")).strip()
        attachment_world_root = str(metadata.get("blend_world_root", "")).strip()
        mount_name = str(metadata.get("blend_world_mount", "")).strip()
        if not attachment_world_id or not attachment_world_root or not mount_name:
            continue
        if not world_id:
            world_id = attachment_world_id
        if not world_root:
            world_root = attachment_world_root
        mounts.append(
            {
                "name": mount_name,
                "kind": attachment.kind,
                "source": attachment.source,
                "access_mode": attachment.access_mode,
                "mount_path": attachment.mount_path,
                "metadata": {
                    key: value
                    for key, value in metadata.items()
                    if key not in {"blend_world_id", "blend_world_root", "blend_world_mount"}
                },
            }
        )
    if not world_id or not world_root:
        return None
    try:
        return load_blend_world(Path(world_root))
    except Exception:
        pass
    return BlendWorld.from_dict(
        {
            "world_id": world_id,
            "root_path": world_root,
            "created_at": session.created_at,
            "mounts": mounts,
            "metadata": {"source_kind": "workstation_session_projection"},
        }
    )


def _append_message(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation turn recording, helps with appending one conversational message to the session-visible message log.

    Reference to Theory:
        Supports the host-owned session model by making user and assistant turns explicit and replayable.

    Example Input Output:
        Input: `_append_message(root=Path('/tmp/ws'), payload={'role': 'user', 'content': 'Inspect the project.'})`
        Output: None

    Args:
        root: Value for `root` used by `_append_message`. Expected type: `Path`.
        payload: Value for `payload` used by `_append_message`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: The normalized, durably appended message record.
    """
    normalized_payload = dict(payload)
    raw_epoch_ms = normalized_payload.get("timestamp_epoch_ms", 0)
    try:
        epoch_ms = int(raw_epoch_ms or 0)
    except Exception:
        epoch_ms = 0
    if epoch_ms <= 0:
        epoch_ms = int(time.time() * 1000)
    normalized_payload["timestamp_epoch_ms"] = epoch_ms
    normalized_payload["message_id"] = collapse_ws(str(normalized_payload.get("message_id", ""))) or f"msg_{uuid.uuid4().hex}"
    normalized_payload["turn_id"] = collapse_ws(str(normalized_payload.get("turn_id", ""))) or f"turn_{uuid.uuid4().hex}"
    try:
        sequence = int(normalized_payload.get("sequence", 0) or 0)
    except Exception:
        sequence = 0
    if sequence <= 0:
        sequence = _next_message_sequence(root)
    normalized_payload["sequence"] = sequence
    _append_jsonl(root / "MESSAGES.jsonl", normalized_payload)
    return normalized_payload


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(json_safe(payload), sort_keys=True) + "\n")


def _next_message_sequence(root: Path) -> int:
    message_path = root / "MESSAGES.jsonl"
    if not message_path.exists():
        return 1
    maximum = 0
    count = 0
    for line in message_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        count += 1
        try:
            maximum = max(maximum, int(json.loads(stripped).get("sequence", 0) or 0))
        except Exception:
            continue
    return max(maximum, count) + 1


def _load_governed_turn_bindings(root: Path) -> list[dict[str, Any]]:
    binding_path = root / "GOVERNED_TURNS.jsonl"
    if not binding_path.exists():
        return []
    bindings: list[dict[str, Any]] = []
    for line in binding_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except Exception:
            continue
        if isinstance(payload, dict) and collapse_ws(str(payload.get("run_id", ""))):
            bindings.append(dict(payload))
    return bindings


def _resolve_governed_turn_binding(root: Path, *, run_id: str = "") -> dict[str, Any]:
    bindings = _load_governed_turn_bindings(root)
    normalized_run_id = collapse_ws(run_id)
    if normalized_run_id:
        bindings = [
            binding
            for binding in bindings
            if collapse_ws(str(binding.get("run_id", ""))) == normalized_run_id
        ]
    if not bindings:
        qualifier = f" for run {normalized_run_id}" if normalized_run_id else ""
        raise ValueError(f"No governed turn binding is available{qualifier}.")
    return bindings[-1]


def _load_message_history(root: Path) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like running another host-owned workstation turn, helps with reloading prior user and assistant messages from the session log.

    Reference to Theory:
        Supports the workstation session model by keeping prompt history explicit and resumable.

    Example Input Output:
        Input: `_load_message_history(root=Path('/tmp/ws'))`
        Output: [{'role': 'user', 'content': 'Inspect the project.'}]

    Args:
        root: Value for `root` used by `_load_message_history`. Expected type: `Path`.

    Returns:
        list[dict[str, Any]]: Result produced by `_load_message_history`.
    """
    messages: list[dict[str, Any]] = []
    for line in (root / "MESSAGES.jsonl").read_text().splitlines():
        stripped = line.strip()
        if stripped:
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                continue
            role = collapse_ws(str(payload.get("role", "")))
            content = str(payload.get("content", "") or "")
            if role and content:
                messages.append({"role": role, "content": content})
    return messages


def _render_readme(session: WorkstationSession) -> str:
    """
    High Level Purpose:
        In circumstances like workstation root materialization, helps with writing the short human-readable instructions that orient the LLM and the user inside the session root.

    Reference to Theory:
        Supports the workstation discovery surface by providing a concise human-readable summary alongside machine-readable files.

    Example Input Output:
        Input: `_render_readme(session=3)`
        Output: '# Workstation\\n\\nRead TASK.md and WORKSTATION.toml first.'

    Args:
        session: Value for `session` used by `_render_readme`. Expected type: `WorkstationSession`.

    Returns:
        str: Result produced by `_render_readme`.
    """
    attachment_lines = "\n".join(
        f"- {attachment.name}: {attachment.kind} at {attachment.mount_path}"
        for attachment in session.attachments
    )
    capability_lines = "\n".join(f"- {name}" for name in session.allowed_capabilities)
    return (
        "# Workstation\n\n"
        "Read `TASK.md`, `WORKSTATION.toml`, `ATTACHMENTS.json`, `TOOLS.json`, and `SKILLS.json` when present before acting.\n\n"
        "Available attachments:\n"
        f"{attachment_lines}\n\n"
        "Allowed capabilities:\n"
        f"{capability_lines}\n"
    )


def _render_workstation_toml(session: WorkstationSession) -> str:
    """
    High Level Purpose:
        In circumstances like workstation root materialization, helps with producing the authoritative machine-readable workstation contract in TOML form.

    Reference to Theory:
        Supports the workstation discovery model by making session identity, attachments, and capabilities explicit in one canonical contract file.

    Example Input Output:
        Input: `_render_workstation_toml(session=3)`
        Output: '[session]\\nsession_id = \"ws_1\"'

    Args:
        session: Value for `session` used by `_render_workstation_toml`. Expected type: `WorkstationSession`.

    Returns:
        str: Result produced by `_render_workstation_toml`.
    """
    lines = [
        "[session]",
        f'session_id = "{session.session_id}"',
        f'created_at = "{session.created_at}"',
        f'root_path = "{session.root_path}"',
        f'openai_profile = "{session.openai_profile or ""}"',
        f'openai_env_var = "{session.openai_env_var or ""}"',
        f"allow_direct_llm_decomposition = {'true' if session.allow_direct_llm_decomposition else 'false'}",
        "",
    ]
    for attachment in session.attachments:
        lines.extend(
            [
                f"[attachments.{attachment.name}]",
                f'kind = "{attachment.kind}"',
                f'source = "{attachment.source}"',
                f'access_mode = "{attachment.access_mode}"',
                f'mount_path = "{attachment.mount_path}"',
            ]
        )
        for key, value in sorted(attachment.metadata.items()):
            lines.append(f'metadata_{key} = "{value}"')
        lines.append("")
    lines.extend(["[capabilities]"])
    for index, capability in enumerate(session.allowed_capabilities):
        lines.append(f'capability_{index} = "{capability}"')
    lines.append("")
    return "\n".join(lines) + "\n"
