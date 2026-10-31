# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import textwrap
from collections import deque
from pathlib import Path
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws
from workstation.contracts.shell import WorkstationChatContext, WorkstationChatPromptTargetPlan
from workstation.runtime.core.chat_commands import (
    canonical_workstation_chat_slash_command_text,
    workstation_chat_slash_commands,
)
from workstation.runtime.core.session import load_workstation_session
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService


_WORKSPACE_PATH_SCAN_LIMIT = 160

_CHAT_SLASH_COMMANDS = workstation_chat_slash_commands()
_CHAT_SLASH_COMMAND_HELP_LINES = {
    "/help": "/help  Show workstation chat and CLI usage.",
    "/apply-source-export": (
        "/apply-source-export  Apply the selected staged Gather source export preview back into staged source history."
    ),
    "/apply-source-set-export": (
        "/apply-source-set-export  Apply the selected Gather source set export preview back into staged source history."
    ),
    "/create-source-set": (
        "/create-source-set  Create a focused Gather source set from the selected staged source."
    ),
    "/create-source-set-from-query": (
        "/create-source-set-from-query <title> | <query> | [description]  Create an empty Gather source set from a topic/query."
    ),
    "/edit-source": "/edit-source  Open the manual edit file for the selected staged Gather source.",
    "/edit-source-set": "/edit-source-set  Open the manual edit file for the selected Gather source set.",
    "/curate-source": "/curate-source  Open a Chat curation turn for the selected staged Gather source.",
    "/merge-source": "/merge-source  Open a Chat merge-back turn for the selected staged Gather source.",
    "/curate-source-set": "/curate-source-set  Open a Chat curation turn for the selected Gather source set.",
    "/find-sources": "/find-sources  Open a Chat discovery turn for the selected Gather source set using its saved query.",
    "/merge-source-set": "/merge-source-set  Open a Chat merge-back turn for the selected Gather source set.",
    "/merge-set-sources": (
        "/merge-set-sources  Open a Chat merge-back turn for the staged sources inside the selected Gather source set."
    ),
    "/synthesize-source-set": (
        "/synthesize-source-set  Open a Chat synthesis turn for the selected Gather source set to summarize coverage and open questions."
    ),
    "/prepare-markdown": (
        "/prepare-markdown <text>  Ask the assistant to turn raw source text into research-ready markdown; "
        "use /prepare-last-assistant-markdown when the source is the most recent assistant reply, then use /start-research."
    ),
    "/prepare-last-assistant-markdown": (
        "/prepare-last-assistant-markdown  Ask the assistant to turn the most recent assistant reply into research-ready markdown; "
        "then use /start-research."
    ),
    "/start-research": (
        "/start-research  Preview staging of the last assistant markdown reply as a Gather source, then confirm before writing."
    ),
    "/start-research-into": (
        "/start-research-into <subject title>  Preview staging into one chosen subject as a Gather source, then confirm before writing."
    ),
    "/refresh-source": "/refresh-source  Refresh the selected URL-backed staged Gather source into a new staged revision.",
    "/resume-research-with-llm": (
        "/resume-research-with-llm <subject title>  Ask the assistant to continue research on one maintained subject."
    ),
    "/research": "/research  Move focus to Gather.",
    "/sync-source-set": "/sync-source-set  Refresh all refreshable URL-backed sources in the selected Gather source set.",
    "/describe-skill": "/describe-skill <skill title>  Show the detailed descriptor for one available skill.",
    "/export-skill": "/export-skill <skill title> [destination_path]  Export one available skill as a portable bundle.",
    "/grant-permission": "/grant-permission <capability>  Add one workstation capability to the current session grant.",
    "/import-skill": "/import-skill <skill_path>  Import one skill bundle into the current workstation.",
    "/list-skills": "/list-skills [query]  Show the visible workstation skill catalog.",
    "/permissions": "/permissions [skill title]  Show session capabilities or inspect one skill's requested permissions.",
    "/workstation-root": "/workstation-root  Print the current workstation root path.",
    "/revoke-permission": "/revoke-permission <capability>  Remove one revocable workstation capability from the current session grant.",
    "/quit": "/quit  Exit the interactive chat UI.",
    "/exit": "/exit  Exit the interactive chat UI.",
}

_RESEARCH_CHAT_ACTION_TARGET_SPECS: dict[str, dict[str, str]] = {
    "/apply-source-export": {
        "action_key": "apply_selected_staged_source_export_preview",
        "missing_text": "/apply-source-export requires a selected staged source in Gather with governed additions ready to stage.",
    },
    "/apply-source-set-export": {
        "action_key": "apply_selected_source_collection_export_preview",
        "missing_text": "/apply-source-set-export requires a selected focused source set in Gather with governed additions ready to stage.",
    },
    "/create-source-set": {
        "action_key": "create_source_collection_from_selected_staged_source",
        "missing_text": "/create-source-set requires a selected staged source in Gather.",
    },
    "/create-source-set-from-query": {
        "action_key": "create_source_collection_from_query",
        "missing_text": (
            "/create-source-set-from-query requires: <title> | <query> | [description]. "
            "It creates an empty Gather source set from a topic/query."
        ),
    },
    "/edit-source": {
        "action_key": "start_research_source_manual_curation",
        "missing_text": "/edit-source requires a selected staged source in Gather.",
    },
    "/edit-source-set": {
        "action_key": "start_research_source_collection_manual_curation",
        "missing_text": "/edit-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
    "/refresh-source": {
        "action_key": "refresh_selected_staged_source",
        "missing_text": "/refresh-source requires a selected URL-backed staged source in Gather.",
    },
    "/sync-source-set": {
        "action_key": "sync_selected_source_collection",
        "missing_text": "/sync-source-set requires a selected source set in Gather with refreshable URL-backed sources.",
    },
}

_RESEARCH_CHAT_PROMPT_TARGET_SPECS: dict[str, dict[str, str]] = {
    "/curate-source": {
        "action_key": "start_research_source_llm_curation",
        "progress_field": "research_source_llm_curation_staged_source_id",
        "started_text": "Started a Gather source curation in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
        "missing_text": "/curate-source requires a selected staged source in Gather.",
    },
    "/merge-source": {
        "action_key": "start_research_source_merge_back",
        "progress_field": "research_source_merge_back_staged_source_id",
        "started_text": "Started a Gather source merge-back in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
        "missing_text": "/merge-source requires a selected staged source in Gather and current learned subject state.",
    },
    "/curate-source-set": {
        "action_key": "start_research_source_collection_llm_curation",
        "progress_field": "research_source_collection_llm_curation_collection_id",
        "started_text": "Started a Gather source-set curation in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
        "missing_text": "/curate-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
    "/find-sources": {
        "action_key": "start_research_source_collection_discovery",
        "progress_field": "research_source_collection_discovery_collection_id",
        "started_text": "Started a Gather source-discovery turn in Chat. Reply with repeated [source] blocks using [label], [url], and [notes] only, and keep the result at the source layer.",
        "missing_text": "/find-sources requires a selected source set in Gather with a saved query.",
    },
    "/merge-source-set": {
        "action_key": "start_research_source_collection_merge_back",
        "progress_field": "research_source_collection_merge_back_collection_id",
        "started_text": "Started a Gather source-set merge-back in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
        "missing_text": "/merge-source-set requires a selected source set in Gather plus current learned subject state.",
    },
    "/merge-set-sources": {
        "action_key": "start_research_source_collection_source_merge_back",
        "progress_field": "research_source_collection_source_merge_back_collection_id",
        "started_text": "Started a Gather set-source merge-back in Chat. Reply with repeated [source] blocks using [url], [label], and [text] only, and keep the result at the source layer.",
        "missing_text": "/merge-set-sources requires a selected source set in Gather plus current learned subject state.",
    },
    "/synthesize-source-set": {
        "action_key": "start_research_source_collection_synthesis",
        "progress_field": "research_source_collection_synthesis_collection_id",
        "started_text": (
            "Started a Gather source-set synthesis in Chat. Reply with [summary], [questions], and [query] sections only, "
            "and keep the result at the source layer."
        ),
        "missing_text": "/synthesize-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
}


def _ordered_unique_non_empty_strings(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = collapse_ws(str(value or ""))
        if not normalized or normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _read_workstation_skill_catalog(root: Path) -> dict[str, Any]:
    skills_path = Path(root) / "SKILLS.json"
    if not skills_path.exists():
        return {}
    try:
        parsed = json.loads(skills_path.read_text())
    except Exception:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _workspace_relative_paths(workspace_root: Path | None) -> list[str]:
    if workspace_root is None or not workspace_root.exists():
        return []
    collected: list[str] = []
    root = Path(workspace_root).expanduser().resolve()
    pending: deque[Path] = deque([root])
    while pending and len(collected) < _WORKSPACE_PATH_SCAN_LIMIT:
        current_path = pending.popleft()
        try:
            relative_root = current_path.relative_to(root)
        except ValueError:
            continue
        relative_root_text = relative_root.as_posix()
        is_root_directory = relative_root_text in {"", "."}
        if not is_root_directory:
            collected.append(relative_root.as_posix() + "/")
            if len(collected) >= _WORKSPACE_PATH_SCAN_LIMIT:
                break
        try:
            with os.scandir(current_path) as iterator:
                for entry in iterator:
                    name = str(getattr(entry, "name", "") or "")
                    if not name or name.startswith("."):
                        continue
                    relative_entry = (relative_root / name) if str(relative_root) else Path(name)
                    try:
                        is_directory = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_directory:
                        pending.append(Path(entry.path))
                        collected.append(relative_entry.as_posix() + "/")
                    else:
                        collected.append(relative_entry.as_posix())
                    if len(collected) >= _WORKSPACE_PATH_SCAN_LIMIT:
                        break
        except OSError:
            continue
    return sorted(_ordered_unique_non_empty_strings(collected))


def _subject_titles(root: Path) -> tuple[str, ...]:
    scenarios = SubjectWorkflowApiService().list_subjects(root_path=Path(root).expanduser().resolve())
    return tuple(
        sorted(
            {
                collapse_ws(str(item.title))
                for item in scenarios
                if not getattr(item, "is_placeholder", False) and collapse_ws(str(getattr(item, "title", "")))
            },
            key=str.casefold,
        )
    )


def workstation_chat_context(root: Path) -> WorkstationChatContext:
    session = load_workstation_session(Path(root).expanduser().resolve())
    workspace_root: Path | None = None
    for attachment in session.attachments:
        if collapse_ws(str(getattr(attachment, "kind", ""))) == "workspace":
            workspace_root = Path(str(getattr(attachment, "source", ""))).expanduser().resolve()
            break
    skills_payload = _read_workstation_skill_catalog(Path(root))
    skill_entries = skills_payload.get("skills", []) if isinstance(skills_payload.get("skills", []), list) else []
    skill_titles = tuple(
        collapse_ws(str(item.get("title", "")))
        for item in skill_entries
        if isinstance(item, dict) and collapse_ws(str(item.get("title", "")))
    )
    builtin_skill_titles = tuple(
        collapse_ws(str(item.get("title", "")))
        for item in skill_entries
        if isinstance(item, dict)
        and collapse_ws(str(item.get("title", "")))
        and collapse_ws(str(item.get("source_kind", ""))) == "builtin_workstation"
    )
    imported_skill_titles = tuple(
        collapse_ws(str(item.get("title", "")))
        for item in skill_entries
        if isinstance(item, dict)
        and collapse_ws(str(item.get("title", "")))
        and collapse_ws(str(item.get("source_kind", ""))) != "builtin_workstation"
    )
    return WorkstationChatContext(
        root=Path(root).expanduser().resolve(),
        workspace_root=workspace_root,
        skill_titles=skill_titles,
        builtin_skill_titles=builtin_skill_titles,
        imported_skill_titles=imported_skill_titles,
        subject_titles=_subject_titles(Path(root)),
        workspace_paths=tuple(_workspace_relative_paths(workspace_root)),
        allowed_capabilities=tuple(str(item) for item in session.allowed_capabilities),
    )


def workstation_chat_help_text(context: WorkstationChatContext) -> str:
    root_text = str(context.root)
    workspace_text = str(context.workspace_root) if context.workspace_root is not None else "<workspace>"
    return "\n".join(
        [
            "Workstation chat commands",
            "",
            "Slash commands",
            *(_CHAT_SLASH_COMMAND_HELP_LINES[command] for command in _CHAT_SLASH_COMMANDS),
            "",
            "Use in chat",
            "Ask normal questions about the attached workspace.",
            "List skills: What skills are available right now?",
            "Import a skill: Import the skill file at trials/python.skill.yaml into this workstation.",
            "Use a skill family: Use the symbol search skill to find the Python class definition for BSSCController under src.",
            "Use an exact skill: Use the skill titled \"Python Commands 02 — Read Text File / Python Commands 02 Read Text File\".",
            "Export a skill: Export the skill titled \"Python Commands 02 — Read Text File / Python Commands 02 Read Text File\" to exports/python-read-text-file.yaml.",
            "Save learnings: Save these learnings as a new markdown at notes/chat-learnings.md.",
            "Append learnings: Add these learnings to the existing markdown at notes/chat-learnings.md.",
            "Grant a capability: /grant-permission ws.repo.search",
            "Revoke a capability: /revoke-permission ws.repo.search",
            "Approve rights when prompted: yes",
            "",
            "CLI commands",
            f"realized-workstation launch --root {root_text} --workspace {workspace_text} --task \"Use installed skills when appropriate.\"",
            f"realized-workstation chat --root {root_text}",
            f"realized-workstation prompt --root {root_text} --prompt \"What skills are available right now?\"",
            f"realized-workstation skill-catalog --root {root_text}",
            f"realized-workstation skill-import --root {root_text} --skill-file /absolute/path/to/skill.yaml",
            f"realized-workstation skill-export --root {root_text} --skill-title \"Skill Title\" --out /absolute/path/to/skill.yaml",
            f"realized-workstation trial-validate --workspace {workspace_text} --domains symbolsearch",
            "",
            "Permission model",
            "The shell prefers skills when a suitable skill exists.",
            "Read skills may run directly when the current session grant covers them.",
            "Write or broader delegated rights may return approval_required; approve with yes to continue one invocation.",
        ]
    )


def workstation_chat_prepare_markdown_prompt(example_text: str) -> str:
    normalized = str(example_text or "").strip()
    return "\n".join(
        [
            "Prepare research-ingress markdown for the 'Source material' mentioned below.",
            "Return markdown only. Do not wrap the answer in code fences.",
            "Requirements:",
            "- start with one H1 title naming the subject clearly",
            "- follow with one short summary paragraph",
            "- use short sections when relevant: Definitions, Governing Relations, Executable Abilities, Examples, Misconceptions, Open Questions, Provenance",
            "- use short bullets or short paragraphs",
            "- keep uncertainty explicit instead of inventing facts",
            "- make the result directly suitable for research ingestion",
            "",
            "Source material:",
            normalized,
        ]
    )


def workstation_chat_prepare_last_assistant_routed_text(assistant_text: str) -> str:
    preview = textwrap.shorten(collapse_ws(str(assistant_text or "")), width=220, placeholder="...")
    return "\n".join(
        [
            "[routed-to-llm]",
            "Prepare research-ingress markdown from the last assistant reply.",
            f"Source preview: {preview or '<empty>'}",
        ]
    ).rstrip()


def workstation_chat_prepare_last_assistant_resolution(assistant_text: str) -> tuple[str, str]:
    normalized = str(assistant_text or "").strip()
    if not normalized:
        return (
            "",
            "No assistant reply is available yet. Ask the assistant for source material first, or use /prepare-markdown <text>.",
        )
    return (
        workstation_chat_prepare_markdown_prompt(normalized),
        workstation_chat_prepare_last_assistant_routed_text(normalized),
    )


def workstation_chat_resume_research_prompt(subject_title: str) -> str:
    normalized_title = collapse_ws(subject_title)
    return "\n".join(
        [
            f'Study this maintained subject: "{normalized_title}".',
            "Use the current maintained subject and its projections as grounding.",
            "Respond in three parts:",
            "1. What the subject already appears to contain.",
            "2. What remains incomplete, ambiguous, or worth checking next.",
            "3. A concise research continuation plan.",
        ]
    )


def _strip_wrapping_quotes(text: str) -> str:
    rendered = str(text or "").strip()
    if len(rendered) >= 2 and rendered[0] == rendered[-1] and rendered[0] in {"'", '"'}:
        return rendered[1:-1].strip()
    return rendered


def _resolved_subject_title_for_resume(*, context: WorkstationChatContext, raw_subject_text: str) -> str:
    normalized = _strip_wrapping_quotes(raw_subject_text)
    if not collapse_ws(normalized):
        return ""
    for title in context.subject_titles:
        if title.casefold() == normalized.casefold():
            return title
    return ""


def workstation_chat_prompt_target_plan(
    *,
    context: WorkstationChatContext,
    prompt_text: str,
) -> WorkstationChatPromptTargetPlan | None:
    normalized_prompt = canonical_workstation_chat_slash_command_text(prompt_text)
    if not normalized_prompt.startswith("/"):
        return None
    command_name, _, raw_args = normalized_prompt.partition(" ")
    arguments_text = raw_args.strip()
    if command_name in _RESEARCH_CHAT_ACTION_TARGET_SPECS:
        if not context.subject_titles:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="No subjects are available yet. Import or stage source material in Gather first.",
            )
        return WorkstationChatPromptTargetPlan(
            kind="research_action",
            command_name=command_name,
            command_arguments=arguments_text,
        )
    if command_name in _RESEARCH_CHAT_PROMPT_TARGET_SPECS:
        if not context.subject_titles:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="No subjects are available yet. Import or stage source material in Gather first.",
            )
        return WorkstationChatPromptTargetPlan(
            kind="research_follow_up",
            command_name=command_name,
            command_arguments=arguments_text,
        )
    if command_name == "/research":
        return WorkstationChatPromptTargetPlan(
            kind="switch_research",
            shell_text="Moved to Gather.",
            move_to_research=True,
        )
    if command_name == "/prepare-markdown":
        if not arguments_text:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text=(
                    "Usage: /prepare-markdown <raw notes or source text>\n"
                    "Use /prepare-last-assistant-markdown when the source is the most recent assistant reply."
                ),
            )
        return WorkstationChatPromptTargetPlan(
            kind="llm_prompt",
            llm_prompt=workstation_chat_prepare_markdown_prompt(arguments_text),
            move_to_research=False,
        )
    if command_name == "/prepare-last-assistant-markdown":
        return WorkstationChatPromptTargetPlan(
            kind="prepare_last_assistant_markdown",
            move_to_research=False,
        )
    if command_name == "/start-research":
        return WorkstationChatPromptTargetPlan(
            kind="start_research",
            move_to_research=False,
        )
    if command_name == "/start-research-into":
        if not arguments_text:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="Usage: /start-research-into <subject title>",
            )
        return WorkstationChatPromptTargetPlan(
            kind="start_research",
            move_to_research=False,
            subject_title=arguments_text,
        )
    if command_name == "/resume-research-with-llm":
        if not context.subject_titles:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="No subjects are available yet. Use /prepare-markdown <text> and then /start-research first.",
            )
        if not arguments_text:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="Available subjects:\n- " + "\n- ".join(context.subject_titles),
            )
        subject_title = _resolved_subject_title_for_resume(context=context, raw_subject_text=arguments_text)
        if not subject_title:
            return WorkstationChatPromptTargetPlan(
                kind="shell",
                shell_text="Unknown subject for /resume-research-with-llm.\nAvailable subjects:\n- " + "\n- ".join(context.subject_titles),
            )
        return WorkstationChatPromptTargetPlan(
            kind="llm_prompt",
            llm_prompt=workstation_chat_resume_research_prompt(subject_title),
            move_to_research=False,
            subject_title=subject_title,
        )
    return None


def workstation_chat_routed_llm_prompt_text(llm_prompt: str) -> str:
    return "\n".join(
        [
            "[routed-to-llm]",
            str(llm_prompt or "").strip(),
        ]
    ).rstrip()
