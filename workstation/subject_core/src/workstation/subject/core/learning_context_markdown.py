# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from workstation.subject.core.learning_context import (
    LearningUnit,
    canonical_learning_subject_id,
    find_learning_context_by_lookup,
    load_learning_context,
    stable_learning_unit_id,
)
from realized_core_semantics.markdown import MarkdownDocumentIR
from realized_core_semantics.semantic_text import collapse_ws, ordered_unique, titleize_semantic_unit


def markdown_learning_subject_metadata(document: MarkdownDocumentIR) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "subject_id": "",
        "canonical_title": "",
        "aliases": (),
        "subject_family": "",
        "summary": "",
    }
    candidate_lines = [
        collapse_ws(str(item))
        for item in [*document.intro_bullets, *document.intro_paragraphs]
        if collapse_ws(str(item))
    ]
    for line in candidate_lines:
        if ":" not in line:
            continue
        raw_key, raw_value = line.split(":", 1)
        key = collapse_ws(raw_key).lower().replace("_", " ")
        value = collapse_ws(raw_value)
        if not value:
            continue
        if key in {"subject", "subject title", "canonical subject", "canonical title"}:
            metadata["canonical_title"] = value
        elif key in {"subject id", "subject identifier"}:
            metadata["subject_id"] = canonical_learning_subject_id(value)
        elif key in {"aliases", "alias"}:
            separator = ";" if ";" in value else ","
            metadata["aliases"] = ordered_unique(item.strip() for item in value.split(separator) if item.strip())
        elif key in {"subject family", "family", "category"}:
            metadata["subject_family"] = value
        elif key == "summary":
            metadata["summary"] = value
    return metadata


def markdown_learning_subject_title(
    document: MarkdownDocumentIR,
    source_path: Path,
    *,
    preferred_subject_title: str = "",
    generic_document_titles: Sequence[str] = (),
) -> str:
    title = collapse_ws(str(document.title or ""))
    preferred = collapse_ws(str(preferred_subject_title or ""))
    generic_titles = {
        collapse_ws(str(item)).casefold()
        for item in generic_document_titles
        if collapse_ws(str(item))
    }
    if preferred and (not title or title.casefold() in generic_titles):
        return preferred
    if title:
        return title
    if preferred:
        return preferred
    return titleize_semantic_unit(source_path.stem) or source_path.stem


def resolve_markdown_learning_subject(
    document: MarkdownDocumentIR,
    source_path: Path,
    *,
    corpus_root: Path,
    preferred_subject_title: str = "",
    generic_document_titles: Sequence[str] = (),
) -> dict[str, Any]:
    metadata = markdown_learning_subject_metadata(document)
    inferred_title = markdown_learning_subject_title(
        document,
        source_path,
        preferred_subject_title=preferred_subject_title,
        generic_document_titles=generic_document_titles,
    )
    source_title = titleize_semantic_unit(source_path.stem) or source_path.stem
    explicit_subject_id = collapse_ws(str(metadata.get("subject_id", "")))
    explicit_title = collapse_ws(str(metadata.get("canonical_title", "")))
    explicit_aliases = ordered_unique(metadata.get("aliases", ()))
    preferred = collapse_ws(str(preferred_subject_title or ""))
    existing_context = None
    if explicit_subject_id:
        try:
            existing_context = load_learning_context(corpus_root, explicit_subject_id)
        except FileNotFoundError:
            existing_context = None
    if existing_context is None:
        existing_context = find_learning_context_by_lookup(
            corpus_root,
            explicit_title,
            preferred,
            document.title,
            source_title,
            *explicit_aliases,
        )
    subject_id = (
        existing_context.subject_id
        if existing_context is not None
        else explicit_subject_id or canonical_learning_subject_id(explicit_title or inferred_title)
    )
    canonical_title = (
        existing_context.canonical_title
        if existing_context is not None
        else explicit_title or inferred_title
    )
    return {
        "subject_id": subject_id,
        "canonical_title": canonical_title,
        "aliases": ordered_unique(
            [canonical_title]
            + list(getattr(existing_context, "aliases", ()))
            + ([document.title] if collapse_ws(str(document.title)) else [])
            + ([source_title] if source_title else [])
            + ([preferred] if preferred else [])
            + list(explicit_aliases)
            + ([explicit_title] if explicit_title else [])
        ),
        "subject_family": collapse_ws(
            str(
                getattr(existing_context, "subject_family", "")
                or metadata.get("subject_family", "")
            )
        ),
        "summary": str(getattr(existing_context, "summary", "") or metadata.get("summary", "")),
        "declared_subject_id": explicit_subject_id,
        "declared_subject_title": explicit_title,
        "matched_existing_subject_id": getattr(existing_context, "subject_id", ""),
    }


def learning_source_note_units_from_markdown_document(
    document: MarkdownDocumentIR,
    *,
    subject_id: str,
    source_id: str,
    base_title: str = "",
    unit_status: str = "proposed",
    source_kind: str = "chat",
) -> tuple[LearningUnit, ...]:
    normalized_base_title = collapse_ws(base_title or document.title or "Source Notes") or "Source Notes"

    def _joined_statement(*parts: Sequence[str]) -> str:
        rendered: list[str] = []
        for group in parts:
            for item in group:
                text = str(item or "").strip()
                if not text:
                    continue
                rendered.append(text if text.startswith("- ") else text)
        return "\n".join(rendered).strip()

    units: list[LearningUnit] = []
    for section in document.sections:
        statement = _joined_statement(section.paragraphs, [f"- {item}" for item in section.bullets], section.equations)
        if not statement:
            continue
        canonical_title = collapse_ws(f"{normalized_base_title} / {section.heading}") if collapse_ws(str(section.heading)) else normalized_base_title
        units.append(
            LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind="source_note",
                    canonical_title=canonical_title,
                ),
                subject_id=subject_id,
                unit_kind="source_note",
                canonical_title=canonical_title,
                aliases=ordered_unique([section.heading, *section.path]),
                statement=statement,
                provenance_refs=(source_id,),
                status=unit_status,
                linked_section_ids=ordered_unique(section.path),
                metadata={
                    "source_kind": source_kind,
                    "capture_kind": "markdown_note_capture",
                },
            )
        )
    if units:
        return tuple(units)
    intro_statement = _joined_statement(document.intro_paragraphs, [f"- {item}" for item in document.intro_bullets])
    if not intro_statement:
        return ()
    return (
        LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="source_note",
                canonical_title=normalized_base_title,
            ),
            subject_id=subject_id,
            unit_kind="source_note",
            canonical_title=normalized_base_title,
            aliases=(normalized_base_title,),
            statement=intro_statement,
            provenance_refs=(source_id,),
            status=unit_status,
            metadata={
                "source_kind": source_kind,
                "capture_kind": "markdown_note_capture",
            },
        ),
    )


__all__ = [
    "learning_source_note_units_from_markdown_document",
    "markdown_learning_subject_metadata",
    "markdown_learning_subject_title",
    "resolve_markdown_learning_subject",
]
