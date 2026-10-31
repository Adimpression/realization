# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from realized_core_semantics.identifiers import slugify
from realized_exchange.learning_context import (
    LearningContext,
    LearningDelta,
    LearningDeltaOperation,
    LearningSource,
    LearningUnit,
    apply_learning_delta,
    canonical_learning_subject_id,
    new_learning_context,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from realized_core_semantics.markdown import MarkdownDocumentIR, MarkdownSectionIR, parse_markdown_document_ir
from realized_core_semantics.semantic_text import collapse_ws


@dataclass(frozen=True)
class FixtureSectionHandle:
    section_id: str
    heading: str
    path: tuple[str, ...]
    paragraphs: tuple[str, ...]
    bullets: tuple[str, ...]


@dataclass(frozen=True)
class FixtureXrefCandidate:
    source_section_id: str
    xref_type: str
    target_label: str
    raw_bullet: str


@dataclass(frozen=True)
class LearningFixture:
    root: Path
    markdown_path: Path
    markdown_text: str
    document: MarkdownDocumentIR
    subject_id: str
    canonical_title: str
    subject_family: str
    summary: str
    source: LearningSource
    delta: LearningDelta
    context: LearningContext
    sections: tuple[FixtureSectionHandle, ...]
    xref_candidates: tuple[FixtureXrefCandidate, ...]


def generated_large_markdown(
    *,
    document_title: str,
    subject_title: str,
    subject_family: str,
    section_prefix: str,
    start_index: int,
    section_count: int,
    include_explicit_xrefs: bool = False,
) -> str:
    sections: list[str] = []
    for index in range(start_index, start_index + section_count):
        body_lines = [
            (
                f"{section_prefix} principle {index:02d} states that quantity_{index} "
                f"varies with driver_{index}."
            ),
            (
                f"The reusable relation for {section_prefix.lower()} principle {index:02d} "
                "should remain distinct and stable."
            ),
        ]
        if include_explicit_xrefs and index > start_index:
            body_lines.append(f"- Xref depends_on: {section_prefix} Principle {index - 1:02d}")
        sections.append(
            "\n".join(
                [
                    f"## {section_prefix} Principle {index:02d}",
                    "",
                    *body_lines,
                    "",
                ]
            )
        )
    return "\n".join(
        [
            f"# {document_title}",
            "",
            f"- Subject: {subject_title}",
            f"- Subject Family: {subject_family}",
            f"- Summary: Generated large markdown lesson for {subject_title}.",
            "",
            *sections,
        ]
    )


def _stable_fixture_section_id(subject_id: str, path: tuple[str, ...]) -> str:
    rendered = "::".join([canonical_learning_subject_id(subject_id), *path])
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10]
    return f"section_{slugify(path[-1] if path else subject_id, limit=40)}_{digest}"


def fixture_section_handles(document: MarkdownDocumentIR, *, subject_id: str) -> tuple[FixtureSectionHandle, ...]:
    return tuple(
        FixtureSectionHandle(
            section_id=_stable_fixture_section_id(subject_id, tuple(section.path)),
            heading=section.heading,
            path=tuple(section.path),
            paragraphs=tuple(section.paragraphs),
            bullets=tuple(section.bullets),
        )
        for section in document.sections
    )


def explicit_xref_candidates_from_sections(
    sections: tuple[FixtureSectionHandle, ...],
) -> tuple[FixtureXrefCandidate, ...]:
    candidates: list[FixtureXrefCandidate] = []
    for section in sections:
        for bullet in section.bullets:
            normalized = collapse_ws(bullet)
            lowered = normalized.lower()
            if not lowered.startswith("xref "):
                continue
            remainder = normalized[5:]
            if ":" not in remainder:
                continue
            xref_type, target_label = remainder.split(":", 1)
            xref_type = collapse_ws(xref_type).lower().replace(" ", "_")
            target_label = collapse_ws(target_label)
            if not xref_type or not target_label:
                continue
            candidates.append(
                FixtureXrefCandidate(
                    source_section_id=section.section_id,
                    xref_type=xref_type,
                    target_label=target_label,
                    raw_bullet=normalized,
                )
            )
    return tuple(candidates)


def _learning_unit_from_fixture_section(
    section: MarkdownSectionIR,
    *,
    subject_id: str,
    source_id: str,
    section_id: str,
) -> LearningUnit:
    canonical_title = " / ".join(section.path) if section.path else section.heading
    body_lines = list(section.paragraphs) + [
        item
        for item in section.bullets
        if not collapse_ws(item).lower().startswith("xref ")
    ]
    statement = " ".join(item.strip() for item in body_lines if collapse_ws(item)) or canonical_title
    return LearningUnit(
        unit_id=stable_learning_unit_id(
            subject_id=subject_id,
            unit_kind="source_note",
            canonical_title=canonical_title,
        ),
        subject_id=subject_id,
        unit_kind="source_note",
        canonical_title=canonical_title,
        statement=statement,
        provenance_refs=(source_id,),
        status="admitted",
        linked_section_ids=(section_id,),
        metadata={"fixture_origin": "learning_xref_test_support"},
    )


def materialize_learning_fixture(
    root: Path,
    *,
    filename: str,
    markdown_text: str,
    canonical_title: str,
    subject_family: str,
    summary: str,
    source_kind: str = "markdown",
) -> LearningFixture:
    root = Path(root)
    markdown_path = root / filename
    markdown_path.write_text(markdown_text, encoding="utf-8")
    document = parse_markdown_document_ir(markdown_text, source_path=str(markdown_path))
    subject_id = canonical_learning_subject_id(canonical_title)
    sections = fixture_section_handles(document, subject_id=subject_id)
    xref_candidates = explicit_xref_candidates_from_sections(sections)

    source = new_learning_source(
        subject_id=subject_id,
        title=document.title or canonical_title,
        source_ref=str(markdown_path.resolve()),
        source_kind=source_kind,
        media_type="text/markdown",
        section_count=len(document.sections),
        metadata={"fixture_origin": "learning_xref_test_support"},
    )
    persist_learning_source(root, source, source_text=markdown_text)

    section_id_by_path = {section.path: section.section_id for section in sections}
    proposed_units = tuple(
        _learning_unit_from_fixture_section(
            section,
            subject_id=subject_id,
            source_id=source.source_id,
            section_id=section_id_by_path[tuple(section.path)],
        )
        for section in document.sections
    )
    delta_seed = new_learning_delta(
        subject_id=subject_id,
        source_kind=source_kind,
        rationale=f"Fixture-learned units from {filename}.",
    )
    delta = LearningDelta(
        delta_id=delta_seed.delta_id,
        subject_id=delta_seed.subject_id,
        source_kind=delta_seed.source_kind,
        rationale=delta_seed.rationale,
        evidence_refs=(source.source_id,),
        proposed_units=proposed_units,
        operations=tuple(
            LearningDeltaOperation(
                operation_id=f"op_initiate_{unit.unit_id}",
                operation_kind="initiate",
                proposed_unit_ids=(unit.unit_id,),
                evidence_refs=(source.source_id,),
                rationale=f"Admit fixture unit {unit.canonical_title}.",
            )
            for unit in proposed_units
        ),
        status="applied",
        metadata={"fixture_origin": "learning_xref_test_support"},
    )
    persist_learning_delta(root, delta)

    context = apply_learning_delta(
        new_learning_context(
            canonical_title=canonical_title,
            subject_id=subject_id,
            subject_family=subject_family,
        ),
        delta,
    )
    context = LearningContext(
        subject_id=context.subject_id,
        canonical_title=canonical_title,
        aliases=context.aliases,
        subject_family=subject_family,
        summary=summary,
        units=context.units,
        linked_source_ids=context.linked_source_ids,
        linked_skill_ids=context.linked_skill_ids,
        linked_document_section_ids=context.linked_document_section_ids,
        applied_delta_ids=context.applied_delta_ids,
        governance_status=context.governance_status,
        metadata=context.metadata,
    )
    persist_learning_context(root, context)

    return LearningFixture(
        root=root,
        markdown_path=markdown_path,
        markdown_text=markdown_text,
        document=document,
        subject_id=subject_id,
        canonical_title=canonical_title,
        subject_family=subject_family,
        summary=summary,
        source=source,
        delta=delta,
        context=context,
        sections=sections,
        xref_candidates=xref_candidates,
    )
