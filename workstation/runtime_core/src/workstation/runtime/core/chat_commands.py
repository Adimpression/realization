# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import shlex
import shutil
from pathlib import Path
from typing import Any

from realized_core_runtime.capabilities import runtime_skill_declaration_for_artifact
from realized_host_interaction.receipts import (
    host_interaction_capability_call_receipt,
)
from realized_core_semantics.semantic_text import collapse_ws
from realized_skill_application.projection import skill_kind_from_artifact
from workstation.runtime.core.capabilities import AVAILABLE_WORKSTATION_CAPABILITIES, execute_workstation_capability
from workstation.foundation.events.event_bus import append_workstation_receipt_and_publish
from workstation.foundation.models import WorkstationSession
from workstation.foundation.projections import (
    render_workstation_permission_panel,
    render_workstation_skill_catalog,
    render_workstation_skill_descriptor,
)
from workstation.contracts.shell_prompt_routing import match_workstation_shell_utility_prompt
from workstation.skills.core.skill_invocation import list_available_workstation_skills, resolve_workstation_skill
from workstation.runtime.core.workstation_core import (
    workstation_change_session_capabilities,
    workstation_permission_panel_for_session,
    workstation_skill_catalog_for_session,
    workstation_skill_descriptor_for_query,
)


_CHAT_UTILITY_SLASH_COMMANDS = (
    "/apply-source-export",
    "/apply-source-set-export",
    "/create-source-set",
    "/create-source-set-from-query",
    "/curate-source",
    "/curate-source-set",
    "/edit-source",
    "/edit-source-set",
    "/find-sources",
    "/merge-set-sources",
    "/merge-source",
    "/merge-source-set",
    "/prepare-markdown",
    "/prepare-last-assistant-markdown",
    "/refresh-source",
    "/research",
    "/resume-research-with-llm",
    "/synthesize-source-set",
    "/sync-source-set",
    "/start-research",
    "/start-research-into",
    "/describe-skill",
    "/export-skill",
    "/grant-permission",
    "/help",
    "/import-skill",
    "/list-skills",
    "/permissions",
    "/workstation-root",
    "/quit",
    "/revoke-permission",
    "/exit",
)
_CHAT_PROMPT_TARGET_SLASH_COMMANDS = (
    "/apply-source-export",
    "/apply-source-set-export",
    "/create-source-set",
    "/create-source-set-from-query",
    "/curate-source",
    "/curate-source-set",
    "/edit-source",
    "/edit-source-set",
    "/find-sources",
    "/merge-set-sources",
    "/merge-source",
    "/merge-source-set",
    "/prepare-markdown",
    "/prepare-last-assistant-markdown",
    "/refresh-source",
    "/research",
    "/resume-research-with-llm",
    "/synthesize-source-set",
    "/sync-source-set",
    "/start-research",
    "/start-research-into",
)
_CHAT_UTILITY_SLASH_COMMAND_ALIASES = {
    "/h": "/help",
    "/s": "/list-skills",
    "/p": "/permissions",
    "/q": "/quit",
}
_PROTECTED_SHELL_CAPABILITIES = (
    "ws.skill.catalog",
    "ws.skill.import",
    "ws.skill.export",
)


def workstation_chat_slash_commands() -> tuple[str, ...]:
    """
    High Level Purpose:
        In circumstances like workstation chat command completion and help rendering, helps with exposing the stable slash-command vocabulary supported directly by the shell.

    Reference to Theory:
        Supports separation of concerns by keeping chat-native command discovery explicit and reusable instead of scattering command names across UI code paths.

    Example Input Output:
        Input: `workstation_chat_slash_commands()`
        Output: ('/describe-skill', '/export-skill', '/grant-permission', '/help', '/import-skill', '/list-skills', '/permissions', '/workstation-root', '/quit', '/revoke-permission', '/exit')

    Returns:
        tuple[str, ...]: Result produced by `workstation_chat_slash_commands`.
    """
    return _CHAT_UTILITY_SLASH_COMMANDS


def workstation_chat_prompt_target_slash_commands() -> tuple[str, ...]:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat prompt routing, helps with exposing the slash-command targets that are interpreted by the host UI as prompt macros or local workflow actions instead of direct deterministic shell commands.

    Reference to Theory:
        Supports the host-owned chat boundary by separating direct shell utilities from richer prompt-target routing while still keeping both vocabularies explicit and discoverable.

    Example Input Output:
        Input: `workstation_chat_prompt_target_slash_commands()`
        Output: ('/prepare-markdown', '/research', '/resume-research-with-llm', '/start-research', '/start-research-into')

    Returns:
        tuple[str, ...]: Result produced by `workstation_chat_prompt_target_slash_commands`.
    """
    return _CHAT_PROMPT_TARGET_SLASH_COMMANDS


def canonical_workstation_chat_slash_command_text(command_text: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation chat shell alias handling, helps with normalizing short slash aliases onto the canonical workstation command vocabulary before dispatch.

    Reference to Theory:
        Supports the host-owned shell boundary by keeping command aliasing deterministic and centralized instead of repeating it in each UI surface.

    Example Input Output:
        Input: `canonical_workstation_chat_slash_command_text('/s demo')`
        Output: '/list-skills demo'

    Args:
        command_text: Value for `command_text` used by `command_text`. Expected type: `str`.

    Returns:
        str: Result produced by `canonical_workstation_chat_slash_command_text`.
    """
    normalized = str(command_text or "").strip()
    if not normalized.startswith("/"):
        return normalized
    command_name, separator, raw_args = normalized.partition(" ")
    canonical_name = _CHAT_UTILITY_SLASH_COMMAND_ALIASES.get(command_name, command_name)
    if not separator:
        return canonical_name
    arguments_text = raw_args.lstrip()
    if not arguments_text:
        return canonical_name
    return f"{canonical_name} {arguments_text}"


def run_workstation_chat_slash_command(*, root: Path, command_text: str) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat usage, helps with executing one direct slash command against the current workstation session without routing through the LLM.

    Reference to Theory:
        Supports the host-owned shell by keeping direct lifecycle and inspection commands explicit, deterministic, and separate from natural-language worker planning.

    Example Input Output:
        Input: `run_workstation_chat_slash_command(root=Path('/tmp/ws'), command_text='/list-skills')`
        Output: (True, 'Built-in skills\\n- Workstation Repo Search [python3]')

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.
        command_text: Value for `command_text` used by `command_text`. Expected type: `str`.

    Returns:
        tuple[bool, str]: Result produced by `run_workstation_chat_slash_command`.
    """
    normalized = canonical_workstation_chat_slash_command_text(command_text)
    if not normalized.startswith("/"):
        return False, ""
    command_name, _, raw_args = normalized.partition(" ")
    arguments_text = raw_args.strip()
    root_path = Path(root).expanduser().resolve()
    from workstation.runtime.core.session import load_workstation_session

    session = load_workstation_session(root_path)

    try:
        if command_name in _CHAT_PROMPT_TARGET_SLASH_COMMANDS:
            return True, (
                f"{command_name} is an interactive workstation chat target.\n"
                "Run it inside workstation chat so the host can route the prompt or research handoff."
            )
        if command_name == "/list-skills":
            return True, _run_list_skills_command(root=root_path, session=session, query=arguments_text)
        if command_name == "/describe-skill":
            return True, _run_describe_skill_command(root=root_path, session=session, skill_query=arguments_text)
        if command_name == "/permissions":
            return True, _run_permissions_command(root=root_path, session=session, skill_query=arguments_text)
        if command_name == "/workstation-root":
            return True, _run_workstation_root_command(root=root_path)
        if command_name == "/grant-permission":
            return True, _run_grant_permission_command(root=root_path, session=session, capability_text=arguments_text)
        if command_name == "/import-skill":
            return True, _run_import_skill_command(root=root_path, session=session, path_text=arguments_text)
        if command_name == "/export-skill":
            return True, _run_export_skill_command(root=root_path, session=session, arguments_text=arguments_text)
        if command_name == "/revoke-permission":
            return True, _run_revoke_permission_command(root=root_path, session=session, capability_text=arguments_text)
        return True, f"Unknown slash command: {command_name}\nUse /help to see supported chat commands."
    except Exception as exc:
        return True, f"{command_name} failed: {exc}"


def run_workstation_natural_language_shell_command(*, root: Path, prompt: str) -> tuple[bool, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation prompt handling before LLM planning, helps with routing obvious shell-lifecycle requests such as skill import/export onto the deterministic shell command path.

    Reference to Theory:
        Supports the workstation shell / worker split by keeping lifecycle operations out of worker composition and generic tool selection.

    Example Input Output:
        Input: `run_workstation_natural_language_shell_command(root=Path('/tmp/ws'), prompt='Import the skill file at trials/python.skill.yaml into this workstation.')`
        Output: (True, {'assistant_text': 'Import status: ok', 'fulfilled_by': 'ws.skill.import', 'command_text': '/import-skill trials/python.skill.yaml'})

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.

    Returns:
        tuple[bool, dict[str, Any]]: Result produced by `run_workstation_natural_language_shell_command`.
    """
    matched = match_workstation_shell_utility_prompt(prompt)
    if matched is None:
        return False, {}
    handled, rendered = run_workstation_chat_slash_command(
        root=root,
        command_text=str(matched.get("command_text", "")),
    )
    if not handled:
        return False, {}
    return True, {
        "assistant_text": rendered,
        "fulfilled_by": collapse_ws(str(matched.get("capability", ""))),
        "command_text": collapse_ws(str(matched.get("command_text", ""))),
    }


def _run_list_skills_command(*, root: Path, session: Any, query: str) -> str:
    normalized_query = collapse_ws(str(query))
    view = workstation_skill_catalog_for_session(
        session=session,
        query=normalized_query,
    )
    payload = {
        "status": "ok",
        "skill_catalog": view.to_dict(),
        "returned_skill_count": view.total_visible,
    }
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.catalog",
        arguments={"target": "skills", **({"query": normalized_query} if normalized_query else {})},
        result=payload,
        phase="started",
    )
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.catalog",
        arguments={"target": "skills", **({"query": normalized_query} if normalized_query else {})},
        result=payload,
    )
    return render_workstation_skill_catalog(view)


def _run_describe_skill_command(*, root: Path, session: Any, skill_query: str) -> str:
    normalized_query = collapse_ws(str(skill_query))
    if not normalized_query:
        return "Usage: /describe-skill <skill title>"
    descriptor = workstation_skill_descriptor_for_query(
        session=session,
        skill_query=normalized_query,
    )
    payload = {
        "status": "ok",
        "skill_descriptor": descriptor.to_dict(),
        "skill_title": descriptor.skill_title,
        "source_kind": descriptor.source_kind,
        "executor_framework": descriptor.executor_framework,
        "authorities_requested": list(descriptor.authorities_requested),
    }
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.describe",
        arguments={"skill_title": normalized_query},
        result=payload,
        phase="started",
    )
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.describe",
        arguments={"skill_title": normalized_query},
        result=payload,
    )
    return render_workstation_skill_descriptor(descriptor)


def _run_permissions_command(*, root: Path, session: Any, skill_query: str) -> str:
    normalized_query = collapse_ws(str(skill_query))
    if not normalized_query:
        view = workstation_permission_panel_for_session(
            session=session,
            available_capabilities=list(_all_known_workstation_capabilities()),
            protected_capabilities=list(_PROTECTED_SHELL_CAPABILITIES),
        )
        payload = {
            "status": "ok",
            "permission_panel": view.to_dict(),
            "granted_capabilities": list(view.granted_capabilities),
            "available_capabilities": list(view.available_capabilities),
            "protected_capabilities": list(view.protected_capabilities),
        }
        _append_chat_command_receipt(
            root=root,
            capability="ws.permissions.list",
            arguments={},
            result=payload,
            phase="started",
        )
        _append_chat_command_receipt(
            root=root,
            capability="ws.permissions.list",
            arguments={},
            result=payload,
        )
        return render_workstation_permission_panel(view)
    descriptor = workstation_skill_descriptor_for_query(
        session=session,
        skill_query=normalized_query,
    )
    requested = list(descriptor.authorities_requested)
    payload = {
        "status": "ok",
        "skill_title": descriptor.skill_title,
        "authorities_requested": requested,
    }
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.permissions",
        arguments={"skill_title": normalized_query},
        result=payload,
        phase="started",
    )
    _append_chat_command_receipt(
        root=root,
        capability="ws.skill.permissions",
        arguments={"skill_title": normalized_query},
        result=payload,
    )
    lines = [
        f"Skill: {descriptor.skill_title}",
        "Declared permissions: " + _render_string_list(requested, empty="<none>"),
        "Session capabilities: " + _render_string_list(list(session.allowed_capabilities), empty="<none>"),
        "Invocation note: actual delegated rights are narrowed per call and may still require approval.",
    ]
    return "\n".join(lines)


def _run_workstation_root_command(*, root: Path) -> str:
    return f"Workstation root: {Path(root).expanduser().resolve()}"


def _run_grant_permission_command(*, root: Path, session: WorkstationSession, capability_text: str) -> str:
    capability = collapse_ws(str(capability_text))
    if not capability:
        return "Usage: /grant-permission <capability>"
    if capability not in _all_known_workstation_capabilities():
        return (
            f"Unknown capability: {capability}\n"
            "Use /permissions to see all available workstation capabilities."
        )
    if capability in session.allowed_capabilities:
        return (
            f"Capability already granted: {capability}\n"
            "Use /permissions to inspect the current session grant."
        )
    updated_session = workstation_change_session_capabilities(
        root=root,
        session=session,
        added_capabilities=[capability],
        removed_capabilities=[],
    )
    payload = {
        "status": "ok",
        "capability": capability,
        "granted_capabilities": list(updated_session.allowed_capabilities),
    }
    _append_chat_command_receipt(
        root=root,
        capability="ws.permissions.grant",
        arguments={"capability": capability},
        result=payload,
        phase="started",
    )
    _append_chat_command_receipt(
        root=root,
        capability="ws.permissions.grant",
        arguments={"capability": capability},
        result=payload,
    )
    return "\n".join(
        [
            f"Granted capability: {capability}",
            "Current session capabilities:",
            *[f"- {item}" for item in updated_session.allowed_capabilities],
        ]
    )


def _run_revoke_permission_command(*, root: Path, session: WorkstationSession, capability_text: str) -> str:
    capability = collapse_ws(str(capability_text))
    if not capability:
        return "Usage: /revoke-permission <capability>"
    if capability not in _all_known_workstation_capabilities():
        return (
            f"Unknown capability: {capability}\n"
            "Use /permissions to see all available workstation capabilities."
        )
    if capability in _PROTECTED_SHELL_CAPABILITIES:
        return (
            f"Cannot revoke protected shell capability: {capability}\n"
            "Protected capabilities keep in-chat skill management available."
        )
    if capability not in session.allowed_capabilities:
        return (
            f"Capability not currently granted: {capability}\n"
            "Use /permissions to inspect the current session grant."
        )
    updated_session = workstation_change_session_capabilities(
        root=root,
        session=session,
        added_capabilities=[],
        removed_capabilities=[capability],
    )
    payload = {
        "status": "ok",
        "capability": capability,
        "granted_capabilities": list(updated_session.allowed_capabilities),
    }
    _append_chat_command_receipt(
        root=root,
        capability="ws.permissions.revoke",
        arguments={"capability": capability},
        result=payload,
        phase="started",
    )
    _append_chat_command_receipt(
        root=root,
        capability="ws.permissions.revoke",
        arguments={"capability": capability},
        result=payload,
    )
    return "\n".join(
        [
            f"Revoked capability: {capability}",
            "Current session capabilities:",
            *[f"- {item}" for item in updated_session.allowed_capabilities],
        ]
    )


def _run_import_skill_command(*, root: Path, session: Any, path_text: str) -> str:
    normalized_path = collapse_ws(str(path_text))
    if not normalized_path:
        return "Usage: /import-skill <skill_path>"
    capability_arguments = _chat_import_capability_arguments(session=session, path_text=normalized_path)
    result = _execute_chat_command_capability(
        root=root,
        session=session,
        capability="ws.skill.import",
        arguments=capability_arguments,
    )
    imported = result.get("imported", []) if isinstance(result.get("imported", []), list) else []
    titles = [
        collapse_ws(str(item.get("title", "")))
        for item in imported
        if isinstance(item, dict) and collapse_ws(str(item.get("title", "")))
    ]
    lines = [
        f"Import status: {collapse_ws(str(result.get('status', ''))) or '<unknown>'}",
        f"Imported count: {int(result.get('imported_count', 0) or 0)}",
    ]
    if titles:
        lines.append("Imported skills:")
        lines.extend(f"- {title}" for title in titles)
    return "\n".join(lines)


def _run_export_skill_command(*, root: Path, session: Any, arguments_text: str) -> str:
    normalized_arguments = collapse_ws(str(arguments_text))
    if not normalized_arguments:
        return "Usage: /export-skill <skill title> [destination_path]"
    skill_query, out_path = _split_skill_query_and_optional_path(normalized_arguments)
    if not skill_query:
        return "Usage: /export-skill <skill title> [destination_path]"
    capability_arguments = {"target": "skills", "skill_title": skill_query}
    copied_to = ""
    if out_path:
        destination_path = Path(out_path).expanduser()
        if destination_path.is_absolute():
            capability_arguments["destination_target"] = "skills_exports"
            capability_arguments["destination_path"] = destination_path.name
            copied_to = str(destination_path.resolve())
        else:
            capability_arguments["destination_target"] = "main"
            capability_arguments["destination_path"] = out_path
    result = _execute_chat_command_capability(
        root=root,
        session=session,
        capability="ws.skill.export",
        arguments=capability_arguments,
    )
    if copied_to:
        host_output_path = Path(copied_to)
        host_output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(result["destination_path"]), host_output_path)
        result = dict(result)
        result["copied_to"] = str(host_output_path)
    lines = [
        f"Export status: {collapse_ws(str(result.get('status', ''))) or '<unknown>'}",
        f"Skill: {collapse_ws(str(result.get('skill_title', skill_query))) or skill_query}",
        f"Destination: {collapse_ws(str(result.get('copied_to', result.get('destination_path', ''))))}",
    ]
    return "\n".join(lines)


def _execute_chat_command_capability(
    *,
    root: Path,
    session: Any,
    capability: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    _append_chat_command_receipt(
        root=root,
        capability=capability,
        arguments=arguments,
        result={"status": "started"},
        phase="started",
    )
    result = execute_workstation_capability(session, capability, arguments)
    _append_chat_command_receipt(
        root=root,
        capability=capability,
        arguments=arguments,
        result=result,
    )
    return result


def _append_chat_command_receipt(
    *,
    root: Path,
    capability: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    phase: str = "",
) -> None:
    from workstation.runtime.core.session import load_workstation_session

    session = load_workstation_session(Path(root))
    append_workstation_receipt_and_publish(
        root_path=Path(root),
        session_id=session.session_id,
        receipt=host_interaction_capability_call_receipt(
            capability=capability,
            arguments=arguments,
            result=result,
            source="chat_slash_command",
            phase=phase,
        ),
    )


def _all_known_workstation_capabilities() -> tuple[str, ...]:
    return tuple(collapse_ws(str(item)) for item in AVAILABLE_WORKSTATION_CAPABILITIES if collapse_ws(str(item)))


def _chat_import_capability_arguments(*, session: Any, path_text: str) -> dict[str, Any]:
    source_path = Path(path_text).expanduser()
    if source_path.is_absolute():
        imports_attachment = _require_attachment_source(session, "skills_imports")
        staged_source_path = imports_attachment / source_path.name
        staged_source_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path.resolve(), staged_source_path)
        return {
            "target": "skills",
            "source_target": "skills_imports",
            "path": source_path.name,
        }
    return {
        "target": "skills",
        "source_target": "main",
        "path": path_text,
    }


def _require_attachment_source(session: Any, name: str) -> Path:
    for attachment in session.attachments:
        if attachment.name == name:
            return Path(str(attachment.source)).expanduser().resolve()
    raise ValueError(f"Required workstation attachment {name!r} is not available in this session.")


def _require_resolved_skill(*, session: Any, skill_query: str) -> tuple[Any, dict[str, str]]:
    skill_store_path = _require_attachment_source(session, "skills")
    resolved = resolve_workstation_skill(skill_title=skill_query, skill_store_path=skill_store_path)
    if resolved is None:
        available = list_available_workstation_skills(skill_store_path)
        candidates = [str(item.get("title", "")) for item in available if isinstance(item, dict)]
        hint = ""
        if candidates:
            hint = "\nAvailable skills:\n" + "\n".join(f"- {title}" for title in candidates[:12])
        raise ValueError(f"No workstation skill matches title {skill_query!r}.{hint}")
    return resolved


def _skill_group_lines(header: str, skills: list[dict[str, Any]]) -> list[str]:
    lines = [header]
    if not skills:
        lines.append("- <none>")
        return lines
    for item in skills:
        title = collapse_ws(str(item.get("title", "")))
        executor = collapse_ws(str(item.get("executor_framework", "")))
        source = collapse_ws(str(item.get("source_kind", "")))
        lines.append(f"- {title} [{executor or source or 'unknown'}]")
    return lines


def _render_mapping_lines(mapping: Any, *, empty: str) -> list[str]:
    if not isinstance(mapping, dict) or not mapping:
        return [f"- {empty}"]
    lines: list[str] = []
    for key, value in mapping.items():
        lines.append(f"- {collapse_ws(str(key))}: {collapse_ws(str(value))}")
    return lines


def _render_string_list(values: list[str], *, empty: str) -> str:
    rendered = [collapse_ws(str(item)) for item in values if collapse_ws(str(item))]
    if not rendered:
        return empty
    return ", ".join(rendered)


def _split_skill_query_and_optional_path(argument_text: str) -> tuple[str, str]:
    try:
        parts = shlex.split(argument_text)
    except Exception:
        parts = [argument_text]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return collapse_ws(parts[0]), ""
    last = collapse_ws(parts[-1])
    if "/" in last or last.endswith((".yaml", ".yml")):
        return collapse_ws(" ".join(parts[:-1])), last
    return collapse_ws(argument_text), ""
