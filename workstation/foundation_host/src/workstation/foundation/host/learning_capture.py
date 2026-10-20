# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from learning_context import (
    LearningContext,
    LearningDelta,
    LearningDeltaOperation,
    LearningUnit,
    apply_learning_delta,
    canonical_learning_subject_id,
    find_learning_context_by_lookup,
    load_learning_context,
    new_learning_context,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from gather_sources import (
    new_source_revision,
    new_staged_source,
    persist_source_revision,
    persist_staged_source,
    staged_source_bundle_root,
)
from markdown_ir import parse_markdown_document_ir
from semantic_text import collapse_ws, ordered_unique, titleize_semantic_unit
from workstation.foundation.models import WorkstationAttachment, WorkstationSession


_LEARNING_MARKDOWN_CAPABILITIES = {"ws.markdown.create", "ws.markdown.append"}
_GENERIC_LEARNING_TITLES = {"learnings", "saved learnings", "chat learnings", "learning notes"}


def _attachment_by_name(session: WorkstationSession, name: str) -> WorkstationAttachment | None:
    normalized = collapse_ws(name)
    for attachment in session.attachments:
        if attachment.name == normalized:
            return attachment
    return None


def _prompt_requests_learning_capture(prompt: str) -> bool:
    normalized = collapse_ws(prompt).lower()
    return ("learning" in normalized or "learnings" in normalized) and any(
        marker in normalized
        for marker in ("save", "capture", "record", "write", "markdown", ".md")
    )


def _chat_subject_hint_from_prompt(prompt: str) -> str:
    normalized = collapse_ws(prompt)
    patterns = (
        r"\b(?:from|of|about|for)\s+(?:this|our)\s+(.+?)\s+(?:discussion|conversation|chat)\b",
        r"\bthis\s+(.+?)\s+(?:discussion|conversation|chat)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match is None:
            continue
        value = collapse_ws(str(match.group(1)).strip(" `\"'.,;:!?"))
        if value:
            return titleize_semantic_unit(value)
    return ""


def _latest_successful_markdown_learning_receipt(tool_receipts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for receipt in reversed(tool_receipts):
        if not isinstance(receipt, dict):
            continue
        if collapse_ws(str(receipt.get("name", ""))) not in _LEARNING_MARKDOWN_CAPABILITIES:
            continue
        result = receipt.get("result", {})
        if not isinstance(result, dict) or collapse_ws(str(result.get("status", ""))) != "ok":
            continue
        return receipt
    return None


def _chat_learning_markdown_text(receipt: dict[str, Any]) -> str:
    result = receipt.get("result", {})
    arguments = receipt.get("arguments", {})
    absolute_path = Path(str(result.get("absolute_path", ""))).expanduser()
    if absolute_path.is_file():
        return absolute_path.read_text(encoding="utf-8")
    return str(arguments.get("markdown_text", ""))


def _chat_learning_document_title(document_title: str, fallback_name: str) -> str:
    title = collapse_ws(str(document_title))
    if title:
        return title
    fallback_title = titleize_semantic_unit(Path(fallback_name).stem)
    return fallback_title or Path(fallback_name).stem or "Chat Learnings"


def _absolute_markdown_path(
    *,
    target_attachment: WorkstationAttachment,
    receipt: dict[str, Any],
) -> Path | None:
    result = receipt.get("result", {})
    arguments = receipt.get("arguments", {})
    absolute_text = collapse_ws(str(result.get("absolute_path", "")))
    if absolute_text:
        return Path(absolute_text).expanduser().resolve()
    relative_text = collapse_ws(str(result.get("path", "") or arguments.get("path", "")))
    if not relative_text:
        return None
    return (Path(target_attachment.source).expanduser().resolve() / relative_text).resolve()


def _chat_learning_document(markdown_text: str, *, source_path: Path) -> tuple[Any, str]:
    document = parse_markdown_document_ir(markdown_text, source_path=str(source_path))
    title = collapse_ws(str(document.title))
    return document, _chat_learning_document_title(title, source_path.name)


def _chat_learning_subject_resolution(
    *,
    prompt: str,
    document: Any,
    source_path: Path,
    corpus_root: Path,
    subject_title_override: str = "",
) -> dict[str, Any]:
    override_title = collapse_ws(subject_title_override)
    if override_title:
        existing_context = find_learning_context_by_lookup(corpus_root, override_title)
        subject_id = (
            existing_context.subject_id
            if existing_context is not None
            else canonical_learning_subject_id(override_title)
        )
        canonical_title = (
            existing_context.canonical_title
            if existing_context is not None
            else override_title
        )
        aliases = ordered_unique(
            item
            for item in (
                canonical_title,
                *(getattr(existing_context, "aliases", ())),
                override_title,
                _chat_learning_document_title(getattr(document, "title", ""), source_path.name),
                titleize_semantic_unit(source_path.stem),
            )
            if collapse_ws(str(item))
        )
        return {
            "subject_id": subject_id,
            "canonical_title": canonical_title,
            "aliases": tuple(aliases),
            "subject_family": collapse_ws(str(getattr(existing_context, "subject_family", ""))),
            "summary": str(getattr(existing_context, "summary", "")),
            "prompt_subject_hint": override_title,
            "matched_existing_subject_id": getattr(existing_context, "subject_id", ""),
        }
    prompt_subject_hint = _chat_subject_hint_from_prompt(prompt)
    document_title = _chat_learning_document_title(getattr(document, "title", ""), source_path.name)
    document_lookup_title = "" if collapse_ws(document_title).lower() in _GENERIC_LEARNING_TITLES else document_title
    existing_context = find_learning_context_by_lookup(
        corpus_root,
        prompt_subject_hint,
        document_lookup_title,
        titleize_semantic_unit(source_path.stem),
    )
    subject_id = (
        existing_context.subject_id
        if existing_context is not None
        else canonical_learning_subject_id(prompt_subject_hint or document_lookup_title or source_path.stem)
    )
    canonical_title = (
        existing_context.canonical_title
        if existing_context is not None
        else prompt_subject_hint or document_lookup_title or titleize_semantic_unit(source_path.stem) or source_path.stem
    )
    aliases = ordered_unique(
        item
        for item in (
            canonical_title,
            *(getattr(existing_context, "aliases", ())),
            prompt_subject_hint,
            document_lookup_title,
            titleize_semantic_unit(source_path.stem),
        )
        if collapse_ws(str(item))
    )
    return {
        "subject_id": subject_id,
        "canonical_title": canonical_title,
        "aliases": tuple(aliases),
        "subject_family": collapse_ws(str(getattr(existing_context, "subject_family", ""))),
        "summary": str(getattr(existing_context, "summary", "")),
        "prompt_subject_hint": prompt_subject_hint,
        "matched_existing_subject_id": getattr(existing_context, "subject_id", ""),
    }


def _chat_learning_unit_title(statement: str, *, index: int) -> str:
    base = titleize_semantic_unit(statement.strip(" ."))
    base = collapse_ws(base)
    if len(base) > 96:
        base = collapse_ws(base[:96]).rstrip()
    return base or f"Chat Note {index}"


def _source_note_units_from_chat_markdown(
    *,
    subject_id: str,
    source_id: str,
    markdown_text: str,
    source_path: Path,
) -> tuple[LearningUnit, ...]:
    document = parse_markdown_document_ir(markdown_text, source_path=str(source_path))
    candidates: list[tuple[str, dict[str, Any]]] = []
    for item in document.intro_bullets:
        text = collapse_ws(str(item))
        if text and ":" not in text.split(" ", 1)[0]:
            candidates.append((text, {"capture_kind": "intro_bullet", "source_heading": document.title}))
    for section in document.sections:
        for paragraph in section.paragraphs:
            text = collapse_ws(str(paragraph))
            if text:
                candidates.append((text, {"capture_kind": "section_paragraph", "source_heading": section.heading}))
        for bullet in section.bullets:
            text = collapse_ws(str(bullet))
            if text:
                candidates.append((text, {"capture_kind": "section_bullet", "source_heading": section.heading}))
    units: list[LearningUnit] = []
    for index, (statement, metadata) in enumerate(candidates, start=1):
        canonical_title = _chat_learning_unit_title(statement, index=index)
        units.append(
            LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind="source_note",
                    canonical_title=f"{index}:{canonical_title}",
                ),
                subject_id=subject_id,
                unit_kind="source_note",
                canonical_title=canonical_title,
                aliases=(),
                statement=statement,
                structured_fields={
                    "source_path": str(source_path),
                    "capture_kind": metadata.get("capture_kind", ""),
                    "source_heading": metadata.get("source_heading", ""),
                },
                provenance_refs=(source_id,),
                status="proposed",
                metadata={
                    "origin": "workstation_chat_learning",
                    "note_index": index,
                },
            )
        )
    return tuple(units)


def _normalized_assistant_markdown_text(markdown_text: str) -> str:
    rendered = str(markdown_text or "").strip()
    fenced_match = re.fullmatch(r"```(?:markdown|md)?\s*\n(.*?)\n?```", rendered, flags=re.IGNORECASE | re.DOTALL)
    if fenced_match is not None:
        return str(fenced_match.group(1) or "").strip()
    return rendered


def _prepared_assistant_markdown_research_capture(
    *,
    root_path: Path,
    markdown_text: str,
    command_text: str,
    subject_title_override: str = "",
) -> dict[str, Any]:
    normalized_root = Path(root_path).expanduser().resolve()
    normalized_markdown = _normalized_assistant_markdown_text(markdown_text)
    if not collapse_ws(normalized_markdown):
        raise ValueError("No assistant message is available to start research.")
    if not normalized_markdown.lstrip().startswith("#"):
        raise ValueError(
            "The last assistant message is not research-ready markdown yet. "
            "Use /prepare-markdown <text> first so the assistant returns a titled markdown document."
        )
    source_path = Path("assistant-prepared-markdown.md")
    document, document_title = _chat_learning_document(normalized_markdown, source_path=source_path)
    explicit_document_title = collapse_ws(str(getattr(document, "title", "")))
    if not explicit_document_title:
        raise ValueError(
            "The last assistant message is not research-ready markdown yet. "
            "Use /prepare-markdown <text> first so the assistant returns a titled markdown document."
        )
    subject_resolution = _chat_learning_subject_resolution(
        prompt=f"Start research for {explicit_document_title}.",
        document=document,
        source_path=source_path,
        corpus_root=normalized_root,
        subject_title_override=subject_title_override,
    )
    subject_id = str(subject_resolution.get("subject_id", ""))
    normalized_override = collapse_ws(subject_title_override)
    proposed_units = _source_note_units_from_chat_markdown(
        subject_id=subject_id,
        source_id="preview_source",
        markdown_text=normalized_markdown,
        source_path=source_path,
    )
    if not proposed_units:
        raise ValueError(
            "The last assistant message did not yield any research units. "
            "Ask the assistant for structured markdown with headings, bullets, or short paragraphs first."
        )
    return {
        "root_path": str(normalized_root),
        "normalized_markdown": normalized_markdown,
        "source_path": source_path,
        "document": document,
        "document_title": document_title,
        "explicit_document_title": explicit_document_title,
        "subject_resolution": subject_resolution,
        "subject_id": subject_id,
        "canonical_title": str(subject_resolution.get("canonical_title", "")),
        "matched_existing_subject_id": str(subject_resolution.get("matched_existing_subject_id", "")),
        "subject_family": str(subject_resolution.get("subject_family", "")),
        "summary": str(subject_resolution.get("summary", "")),
        "prompt_subject_hint": str(subject_resolution.get("prompt_subject_hint", "")),
        "subject_title_override": normalized_override,
        "proposed_units": proposed_units,
        "proposed_unit_count": len(proposed_units),
        "admitted_unit_count": len(proposed_units),
    }


def _ensure_gather_subject_workspace(
    *,
    root_path: Path,
    subject_id: str,
    canonical_title: str,
    subject_family: str = "",
) -> tuple[LearningContext, Path]:
    normalized_root = Path(root_path).expanduser().resolve()
    normalized_subject_id = collapse_ws(subject_id)
    normalized_title = collapse_ws(canonical_title) or normalized_subject_id or "Gather Source"
    try:
        context = load_learning_context(normalized_root, normalized_subject_id)
    except FileNotFoundError:
        context = new_learning_context(
            canonical_title=normalized_title,
            subject_id=normalized_subject_id or canonical_learning_subject_id(normalized_title),
            subject_family=collapse_ws(subject_family),
        )
        context_path = persist_learning_context(normalized_root, context)
        return context, Path(context_path)
    return context, (normalized_root / "corpus" / context.subject_id / "context.json").resolve()


def preview_workstation_assistant_markdown_for_research(
    *,
    root_path: Path,
    markdown_text: str,
    command_text: str = "/start-research",
    subject_title_override: str = "",
) -> dict[str, Any]:
    prepared = _prepared_assistant_markdown_research_capture(
        root_path=root_path,
        markdown_text=markdown_text,
        command_text=command_text,
        subject_title_override=subject_title_override,
    )
    return {
        "canonical_title": str(prepared.get("canonical_title", "")),
        "subject_id": str(prepared.get("subject_id", "")),
        "document_title": str(prepared.get("document_title", "")),
        "matched_existing_subject_id": str(prepared.get("matched_existing_subject_id", "")),
        "subject_family": str(prepared.get("subject_family", "")),
        "summary": str(prepared.get("summary", "")),
        "subject_title_override": str(prepared.get("subject_title_override", "")),
        "proposed_unit_count": int(prepared.get("proposed_unit_count", 0) or 0),
        "admitted_unit_count": int(prepared.get("admitted_unit_count", 0) or 0),
    }


def capture_workstation_assistant_markdown_for_research(
    *,
    root_path: Path,
    markdown_text: str,
    command_text: str = "/start-research",
    subject_title_override: str = "",
) -> dict[str, Any]:
    prepared = _prepared_assistant_markdown_research_capture(
        root_path=root_path,
        markdown_text=markdown_text,
        command_text=command_text,
        subject_title_override=subject_title_override,
    )
    normalized_root = Path(str(prepared.get("root_path", root_path))).expanduser().resolve()
    normalized_markdown = str(prepared.get("normalized_markdown", ""))
    document_title = str(prepared.get("document_title", ""))
    subject_resolution = dict(prepared.get("subject_resolution", {}))
    subject_id = str(prepared.get("subject_id", ""))
    canonical_title = str(prepared.get("canonical_title", ""))
    matched_existing_subject_id = str(subject_resolution.get("matched_existing_subject_id", ""))
    context, context_path = _ensure_gather_subject_workspace(
        root_path=normalized_root,
        subject_id=subject_id,
        canonical_title=canonical_title,
        subject_family=str(subject_resolution.get("subject_family", "")),
    )
    staged_source = new_staged_source(
        subject_id=context.subject_id,
        title=document_title,
        source_ref=f"chat://assistant/start-research/{int(time.time() * 1000)}",
        source_kind="chat",
        media_type="text/markdown",
        metadata={
            "command_text": command_text,
            "capture_origin": "assistant_markdown_research",
            "resolved_subject_id": context.subject_id,
            "resolved_canonical_title": context.canonical_title or canonical_title,
            "matched_existing_subject_id": matched_existing_subject_id,
            "subject_title_override": collapse_ws(subject_title_override),
            "proposed_unit_count": int(prepared.get("proposed_unit_count", 0) or 0),
        },
    )
    revision = new_source_revision(
        staged_source_id=staged_source.staged_source_id,
        subject_id=context.subject_id,
        source_ref=staged_source.source_ref,
        revision_kind="capture",
        metadata={
            "capture_origin": "assistant_markdown_research",
            "command_text": command_text,
            "document_title": document_title,
            "resolved_subject_id": context.subject_id,
            "resolved_canonical_title": context.canonical_title or canonical_title,
            "matched_existing_subject_id": matched_existing_subject_id,
            "subject_title_override": collapse_ws(subject_title_override),
            "proposed_unit_count": int(prepared.get("proposed_unit_count", 0) or 0),
        },
    )
    revision_path, revision_markdown_path, persisted_bundle_paths = persist_source_revision(
        normalized_root,
        revision,
        markdown_text=normalized_markdown,
    )
    staged_source_path = persist_staged_source(
        normalized_root,
        staged_source.__class__(
            staged_source_id=staged_source.staged_source_id,
            subject_id=staged_source.subject_id,
            title=staged_source.title,
            source_ref=staged_source.source_ref,
            source_kind=staged_source.source_kind,
            media_type=staged_source.media_type,
            status="staged",
            latest_revision_id=revision.revision_id,
            revision_count=1,
            created_at_epoch_ms=staged_source.created_at_epoch_ms,
            updated_at_epoch_ms=revision.created_at_epoch_ms,
            metadata=dict(staged_source.metadata),
        ),
    )
    return {
        "corpus_root": str((normalized_root / "corpus").resolve()),
        "subject_id": context.subject_id,
        "canonical_title": context.canonical_title,
        "subject_family": context.subject_family,
        "context_path": str(context_path),
        "staged_source_id": staged_source.staged_source_id,
        "source_id": staged_source.staged_source_id,
        "staged_source_path": str(staged_source_path),
        "revision_id": revision.revision_id,
        "source_record_path": str(staged_source_path),
        "revision_path": str(revision_path),
        "revision_markdown_path": str(revision_markdown_path),
        "revision_bundle_root": str(staged_source_bundle_root(normalized_root, context.subject_id, revision.revision_id)),
        "bundle_file_count": len(persisted_bundle_paths),
        "unit_count": len(context.units),
        "proposed_unit_count": int(prepared.get("proposed_unit_count", 0) or 0),
        "admitted_unit_count": sum(1 for unit in context.units if unit.status == "admitted"),
        "applied_delta_count": len(context.applied_delta_ids),
        "matched_existing_subject_id": matched_existing_subject_id,
        "capture_origin": "assistant_markdown_research",
    }


def capture_workstation_chat_learning_from_tool_receipts(
    *,
    session: WorkstationSession,
    prompt: str,
    tool_receipts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not _prompt_requests_learning_capture(prompt):
        return None
    receipt = _latest_successful_markdown_learning_receipt(tool_receipts)
    if receipt is None:
        return None
    result = receipt.get("result", {})
    arguments = receipt.get("arguments", {})
    target_name = collapse_ws(str(result.get("target", "") or arguments.get("target", "main")))
    target_attachment = _attachment_by_name(session, target_name)
    if target_attachment is None:
        return None
    absolute_path = _absolute_markdown_path(target_attachment=target_attachment, receipt=receipt)
    if absolute_path is None:
        return None
    markdown_text = _chat_learning_markdown_text(receipt)
    if not collapse_ws(markdown_text):
        return None
    corpus_root = Path(target_attachment.source).expanduser().resolve()
    document, document_title = _chat_learning_document(markdown_text, source_path=absolute_path)
    subject_resolution = _chat_learning_subject_resolution(
        prompt=prompt,
        document=document,
        source_path=absolute_path,
        corpus_root=corpus_root,
    )
    subject_id = str(subject_resolution.get("subject_id", ""))
    canonical_title = str(subject_resolution.get("canonical_title", ""))
    source_record = new_learning_source(
        subject_id=subject_id,
        title=document_title,
        source_ref=str(absolute_path),
        source_kind="chat",
        media_type="text/markdown",
        section_count=len(document.sections),
        metadata={
            "session_id": session.session_id,
            "prompt": prompt,
            "target_attachment": target_attachment.name,
            "workspace_markdown_path": str(result.get("path", "")),
            "prompt_subject_hint": str(subject_resolution.get("prompt_subject_hint", "")),
            "matched_existing_subject_id": str(subject_resolution.get("matched_existing_subject_id", "")),
            "resolved_subject_id": subject_id,
            "resolved_canonical_title": canonical_title,
        },
    )
    source_record_path = persist_learning_source(corpus_root, source_record, source_text=markdown_text)
    proposed_units = _source_note_units_from_chat_markdown(
        subject_id=subject_id,
        source_id=source_record.source_id,
        markdown_text=markdown_text,
        source_path=absolute_path,
    )
    delta_seed = new_learning_delta(
        subject_id=subject_id,
        source_kind="chat",
        rationale=f"Captured chat learnings from {absolute_path.name}.",
    )
    delta = LearningDelta(
        delta_id=delta_seed.delta_id,
        subject_id=delta_seed.subject_id,
        source_kind=delta_seed.source_kind,
        rationale=delta_seed.rationale,
        evidence_refs=(source_record.source_id,),
        proposed_units=proposed_units,
        deprecated_unit_ids=(),
        operations=tuple(
            LearningDeltaOperation(
                operation_id=f"op_initiate_{unit.unit_id}",
                operation_kind="initiate",
                proposed_unit_ids=(unit.unit_id,),
                evidence_refs=(source_record.source_id,),
                rationale=f"Admit captured chat learning unit {unit.canonical_title or unit.unit_id}.",
            )
            for unit in proposed_units
        ),
        derived_skill_ids=(),
        document_section_ids=(),
        status="applied" if proposed_units else "proposed",
        metadata={
            "session_id": session.session_id,
            "prompt": prompt,
            "workspace_markdown_path": str(result.get("path", "")),
            "target_attachment": target_attachment.name,
        },
    )
    delta_path = persist_learning_delta(corpus_root, delta)
    try:
        existing_context = load_learning_context(corpus_root, subject_id)
    except FileNotFoundError:
        existing_context = new_learning_context(
            canonical_title=canonical_title,
            subject_id=subject_id,
            subject_family=str(subject_resolution.get("subject_family", "")),
        )
    merged_context = apply_learning_delta(existing_context, delta)
    merged_context = LearningContext(
        subject_id=merged_context.subject_id,
        canonical_title=canonical_title or merged_context.canonical_title,
        aliases=tuple(subject_resolution.get("aliases", merged_context.aliases)),
        subject_family=str(subject_resolution.get("subject_family", "") or merged_context.subject_family),
        summary=str(subject_resolution.get("summary", "") or merged_context.summary),
        units=merged_context.units,
        linked_source_ids=merged_context.linked_source_ids,
        linked_skill_ids=merged_context.linked_skill_ids,
        linked_document_section_ids=merged_context.linked_document_section_ids,
        applied_delta_ids=merged_context.applied_delta_ids,
        governance_status=merged_context.governance_status,
        metadata=merged_context.metadata,
    )
    context_path = persist_learning_context(corpus_root, merged_context)
    return {
        "corpus_root": str(corpus_root),
        "subject_id": merged_context.subject_id,
        "canonical_title": merged_context.canonical_title,
        "subject_family": merged_context.subject_family,
        "context_path": str(context_path),
        "source_id": source_record.source_id,
        "source_record_path": str(source_record_path),
        "delta_id": delta.delta_id,
        "delta_path": str(delta_path),
        "unit_count": len(merged_context.units),
        "applied_delta_count": len(merged_context.applied_delta_ids),
        "matched_existing_subject_id": str(subject_resolution.get("matched_existing_subject_id", "")),
        "capture_origin": "workstation_chat_markdown",
        "target_attachment": target_attachment.name,
        "workspace_markdown_path": str(result.get("path", "")),
    }
