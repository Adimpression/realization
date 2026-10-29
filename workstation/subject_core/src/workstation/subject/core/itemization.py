"""Subject itemization extraction, continuity, and persistence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping, Protocol

from realized_core_semantics.identifiers import slugify
from realized_core_semantics.itemization import (
    ITEMIZATION_SCHEMA_VERSION,
    VALID_ITEMIZATION_SESSION_STATUSES,
    VALID_ITEMIZED_DECISION_ROLES,
    VALID_ITEMIZED_ITEM_KINDS,
    VALID_ITEMIZED_ITEM_STATUSES,
    ItemizationSession,
    ItemizedSubjectItem,
    _normalized_choice,
    _normalized_itemized_metadata,
    _ordered_unique_texts,
    _stable_json_hash,
    normalize_itemized_decision_role,
)
from workstation.subject.core.learning_context import (
    LearningContext,
    LearningSource,
    LearningUnit,
    canonical_learning_subject_id,
    learning_context_home,
    learning_context_paths,
    learning_source_bundle_root,
    load_learning_context,
    load_learning_source,
)
from realized_core_semantics.markdown import (
    MarkdownDocumentIR,
    bounded_markdown_learning_prompt_view,
    markdown_candidate_expression_mappings,
    markdown_document_symbol_aliases,
    markdown_encounter_aliases,
    markdown_learning_encounter_view,
    markdown_clean_learning_text,
    parse_markdown_document_ir,
)
from realized_core_semantics.semantic_text import collapse_ws, semantic_chain_decomposition_components
from realized_core_semantics.title_semantics import normalize_markdown_title_identity, normalize_semantic_title_identity


class ItemizationProposalResult(Protocol):
    """Minimal advisory proposal shape consumed by itemization."""

    proposal_id: str
    source: str
    payload: dict[str, object]


class ItemizationProposalPort(Protocol):
    """Outbound itemization effect expressed without a runtime dependency."""

    def request_itemization_proposal(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        target_scope: str,
        instructions: str,
        fallback_payload: dict[str, object],
        schema_hint: dict[str, object],
    ) -> ItemizationProposalResult: ...


def _itemized_intermediate_was_rephrased(item: "ItemizedSubjectItem") -> bool:
    metadata = dict(item.metadata or {})
    return collapse_ws(str(metadata.get("last_rephrase_phase", ""))).lower() == "itemize"


def _itemized_continuity_source_refs(source_refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        ref
        for ref in _ordered_unique_texts(source_refs)
        if not ref.startswith("encounter:")
    )


def _itemized_continuity_key(item: "ItemizedSubjectItem") -> tuple[str, ...]:
    metadata = dict(item.metadata or {})
    source_unit_id = collapse_ws(item.source_unit_id) or collapse_ws(str(metadata.get("unit_id", "")))
    source_refs = _itemized_continuity_source_refs(item.source_refs)
    origin = collapse_ws(str(metadata.get("origin", ""))).lower()
    role = normalize_itemized_decision_role(metadata.get("decision_role", ""))
    key_parts: list[str] = [f"kind:{collapse_ws(item.item_kind).lower()}"]
    if role:
        key_parts.append(f"role:{role}")
    if source_unit_id:
        key_parts.append(f"unit:{source_unit_id}")
    for ref in source_refs:
        key_parts.append(f"ref:{ref}")
    if origin:
        key_parts.append(f"origin:{origin}")
    for field in (
        "unit_kind",
        "encounter_heading",
        "xref_type",
        "target_label",
        "output_field",
        "asset_src",
        "alt",
    ):
        value = collapse_ws(str(metadata.get(field, "")))
        if value:
            key_parts.append(f"{field}:{value}")
    if len(key_parts) <= 1:
        return ()
    return tuple(key_parts)


def _itemized_continuity_match_score(
    generated: "ItemizedSubjectItem",
    existing: "ItemizedSubjectItem",
) -> tuple[int, int, int]:
    generated_label = collapse_ws(generated.canonical_label).casefold()
    existing_label = collapse_ws(existing.canonical_label).casefold()
    existing_aliases = {
        collapse_ws(alias).casefold()
        for alias in existing.aliases
        if collapse_ws(alias)
    }
    score = 0
    if generated_label and generated_label == existing_label:
        score += 6
    elif generated_label and generated_label in existing_aliases:
        score += 4
    elif generated_label and existing_label and (
        generated_label in existing_label or existing_label in generated_label
    ):
        score += 2
    if collapse_ws(generated.source_unit_id) and collapse_ws(generated.source_unit_id) == collapse_ws(existing.source_unit_id):
        score += 3
    if _itemized_continuity_source_refs(generated.source_refs) == _itemized_continuity_source_refs(existing.source_refs):
        score += 2
    elif set(_itemized_continuity_source_refs(generated.source_refs)) & set(_itemized_continuity_source_refs(existing.source_refs)):
        score += 1
    generated_summary = collapse_ws(generated.summary)
    existing_summary = collapse_ws(existing.summary)
    if generated_summary and existing_summary and generated_summary == existing_summary:
        score += 1
    return (
        score,
        int(existing.updated_at_epoch_ms or 0),
        int(existing.created_at_epoch_ms or 0),
    )


def _stable_itemization_record_id(prefix: str, *parts: Any) -> str:
    normalized_parts = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized_parts)
    slug = slugify(normalized_parts[-1] if normalized_parts else prefix, limit=48)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10] if rendered else "0" * 10
    return f"{prefix}_{slug}_{digest}"


def stable_itemized_item_id(
    *,
    subject_id: str,
    item_kind: str,
    canonical_label: str,
    source_refs: tuple[str, ...] = (),
    role: str = "",
    disambiguator: str = "",
) -> str:
    return _stable_itemization_record_id(
        "itm",
        canonical_learning_subject_id(subject_id),
        collapse_ws(item_kind),
        collapse_ws(role),
        collapse_ws(canonical_label),
        *source_refs,
        collapse_ws(disambiguator),
    )


def stable_itemization_session_id(*, subject_id: str, learning_context_snapshot_hash: str) -> str:
    return _stable_itemization_record_id(
        "itemization",
        canonical_learning_subject_id(subject_id),
        learning_context_snapshot_hash,
    )


def itemization_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    home = learning_context_home(root_path, subject_id) / "itemization"
    return {
        "root": home,
        "session": home / "session.json",
        "items": home / "items",
        "receipts": home / "receipts",
    }


def ensure_itemization_home(root_path: Path, subject_id: str) -> dict[str, Path]:
    paths = itemization_paths(root_path, subject_id)
    for key in ("root", "items", "receipts"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def persist_itemization_session(
    root_path: Path,
    session: ItemizationSession,
    items: tuple[ItemizedSubjectItem, ...],
) -> Path:
    normalized_session = ItemizationSession.from_dict(session.to_dict())
    paths = ensure_itemization_home(root_path, normalized_session.subject_id)
    persisted_item_ids: set[str] = set()
    for item in items:
        normalized_item = ItemizedSubjectItem.from_dict(item.to_dict())
        persisted_item_ids.add(normalized_item.itemized_item_id)
        _write_json(paths["items"] / f"{normalized_item.itemized_item_id}.json", normalized_item.to_dict())
    # The session inventory is authoritative after a refresh. Remove stale item files
    # so validation and subsequent loads don't keep seeing orphaned candidates.
    for path in paths["items"].glob("*.json"):
        if path.stem not in persisted_item_ids:
            try:
                path.unlink()
            except FileNotFoundError:
                continue
    _write_json(paths["session"], normalized_session.to_dict())
    return paths["session"]


def load_itemized_subject_item(root_path: Path, subject_id: str, itemized_item_id: str) -> ItemizedSubjectItem:
    path = itemization_paths(root_path, subject_id)["items"] / f"{collapse_ws(itemized_item_id)}.json"
    return ItemizedSubjectItem.from_dict(_read_json(path))


def load_itemization_session(root_path: Path, subject_id: str) -> ItemizationSession:
    path = itemization_paths(root_path, subject_id)["session"]
    return ItemizationSession.from_dict(_read_json(path))


def list_itemized_subject_items(root_path: Path, subject_id: str) -> tuple[ItemizedSubjectItem, ...]:
    items_root = itemization_paths(root_path, subject_id)["items"]
    if not items_root.exists():
        return ()
    items: list[ItemizedSubjectItem] = []
    for path in sorted(items_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        item = ItemizedSubjectItem.from_dict(payload)
        if item.itemized_item_id:
            items.append(item)
    return tuple(
        sorted(
            items,
            key=lambda item: (
                item.item_kind,
                item.canonical_label.casefold(),
                item.itemized_item_id,
            ),
        )
    )


def _canonical_label(text: str, *, markdown_title: bool = False) -> str:
    raw = collapse_ws(str(text))
    if not raw:
        return ""
    if markdown_title:
        normalized = normalize_markdown_title_identity(raw)
        return normalized or raw
    normalized = normalize_semantic_title_identity(raw)
    return normalized or raw


def _mergeable_item_key(item_kind: str, canonical_label: str, metadata: Mapping[str, Any]) -> tuple[str, ...]:
    role = collapse_ws(str(metadata.get("decision_role", ""))).lower()
    return (item_kind, canonical_label.casefold(), role)


def _append_or_merge_item(
    built: dict[tuple[str, ...], ItemizedSubjectItem],
    *,
    subject_id: str,
    item_kind: str,
    canonical_label: str,
    source_unit_id: str = "",
    aliases: tuple[str, ...] = (),
    summary: str = "",
    source_refs: tuple[str, ...] = (),
    confidence: float = 0.5,
    linked_item_ids: tuple[str, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> None:
    normalized_kind = _normalized_choice(item_kind, allowed=VALID_ITEMIZED_ITEM_KINDS, default="entity")
    normalized_label = collapse_ws(canonical_label)
    if not normalized_label:
        return
    normalized_aliases = _ordered_unique_texts((normalized_label, *aliases))
    normalized_sources = _ordered_unique_texts(source_refs)
    normalized_metadata = _normalized_itemized_metadata(metadata or {})
    key = _mergeable_item_key(normalized_kind, normalized_label, normalized_metadata)
    existing = built.get(key)
    if existing is None:
        built[key] = ItemizedSubjectItem(
            itemized_item_id=stable_itemized_item_id(
                subject_id=subject_id,
                item_kind=normalized_kind,
                canonical_label=normalized_label,
                role=collapse_ws(str(normalized_metadata.get("decision_role", ""))),
            ),
            subject_id=canonical_learning_subject_id(subject_id),
            item_kind=normalized_kind,
            canonical_label=normalized_label,
            source_unit_id=collapse_ws(source_unit_id),
            aliases=normalized_aliases,
            summary=str(summary or ""),
            source_refs=normalized_sources,
            confidence=min(1.0, max(0.0, float(confidence))),
            status="candidate",
            linked_item_ids=_ordered_unique_texts(linked_item_ids),
            metadata=normalized_metadata,
        )
        return
    built[key] = ItemizedSubjectItem(
        itemized_item_id=existing.itemized_item_id,
        subject_id=existing.subject_id,
        item_kind=existing.item_kind,
        canonical_label=existing.canonical_label,
        source_unit_id=existing.source_unit_id or collapse_ws(source_unit_id),
        aliases=_ordered_unique_texts((*existing.aliases, *normalized_aliases)),
        summary=existing.summary or str(summary or ""),
        source_refs=_ordered_unique_texts((*existing.source_refs, *normalized_sources)),
        confidence=max(existing.confidence, min(1.0, max(0.0, float(confidence)))),
        status=existing.status,
        linked_item_ids=_ordered_unique_texts((*existing.linked_item_ids, *linked_item_ids)),
        created_at_epoch_ms=existing.created_at_epoch_ms,
        updated_at_epoch_ms=existing.updated_at_epoch_ms,
        schema_version=existing.schema_version,
        metadata=_normalized_itemized_metadata(
            {
                **existing.metadata,
                **normalized_metadata,
                "origins": _ordered_unique_texts(
                    (
                        *existing.metadata.get("origins", ()),
                        collapse_ws(str(existing.metadata.get("origin", ""))),
                        *normalized_metadata.get("origins", ()),
                        collapse_ws(str(normalized_metadata.get("origin", ""))),
                    )
                ),
            }
        ),
    )


def _resolve_itemized_source_unit_id(
    context: LearningContext,
    item: ItemizedSubjectItem,
) -> str:
    existing_source_unit_id = collapse_ws(item.source_unit_id)
    if existing_source_unit_id:
        return existing_source_unit_id
    metadata_unit_id = collapse_ws(str(item.metadata.get("unit_id", "")))
    if metadata_unit_id:
        return metadata_unit_id
    admitted_units = tuple(
        unit
        for unit in context.units
        if collapse_ws(unit.unit_id) and collapse_ws(unit.status) == "admitted"
    )
    if not admitted_units:
        return ""
    source_refs = {
        collapse_ws(ref)
        for ref in item.source_refs
        if collapse_ws(ref)
    }
    if source_refs:
        matched_units = tuple(
            unit
            for unit in admitted_units
            if source_refs & {collapse_ws(ref) for ref in unit.provenance_refs if collapse_ws(ref)}
        )
        if len(matched_units) == 1:
            return matched_units[0].unit_id
    if len(admitted_units) == 1:
        return admitted_units[0].unit_id
    return ""


def _stable_section_marker(subject_id: str, path: tuple[str, ...]) -> str:
    return _stable_itemization_record_id("section", canonical_learning_subject_id(subject_id), *path)


def _explicit_xref_candidates(document: MarkdownDocumentIR, *, subject_id: str, source_id: str) -> tuple[dict[str, Any], ...]:
    candidates: list[dict[str, Any]] = []
    for section in document.sections:
        section_marker = _stable_section_marker(subject_id, tuple(section.path))
        for bullet in section.bullets:
            normalized = collapse_ws(bullet)
            lowered = normalized.lower()
            if not lowered.startswith("xref "):
                continue
            remainder = normalized[5:]
            if ":" not in remainder:
                continue
            xref_type, target_label = remainder.split(":", 1)
            normalized_type = collapse_ws(xref_type).lower().replace(" ", "_")
            normalized_target = _canonical_label(target_label, markdown_title=True)
            if not normalized_type or not normalized_target:
                continue
            candidates.append(
                {
                    "canonical_label": normalized_target,
                    "summary": normalized,
                    "source_refs": (source_id, f"section:{section_marker}"),
                    "aliases": (normalized,),
                    "metadata": {
                        "xref_type": normalized_type,
                        "source_section_id": section_marker,
                        "source_section_path": list(section.path),
                        "target_label": normalized_target,
                    },
                }
            )
    return tuple(candidates)


def _decision_role_candidates_from_unit(unit: LearningUnit) -> tuple[dict[str, Any], ...]:
    text = " ".join(
        part for part in (
            unit.canonical_title,
            unit.statement,
            " ".join(unit.aliases),
        ) if collapse_ws(part)
    )
    lowered = text.lower()
    candidates: list[dict[str, Any]] = []
    base_source_refs = (*unit.provenance_refs, f"unit:{unit.unit_id}")
    if unit.unit_kind == "ability":
        candidates.append(
            {
                "canonical_label": _canonical_label(unit.canonical_title or unit.unit_id),
                "summary": unit.statement,
                "source_refs": base_source_refs,
                "aliases": unit.aliases,
                "metadata": {"decision_role": "capability"},
                "confidence": 0.85,
            }
        )
    if unit.unit_kind == "boundary":
        candidates.append(
            {
                "canonical_label": _canonical_label(unit.canonical_title or unit.unit_id),
                "summary": unit.statement,
                "source_refs": base_source_refs,
                "aliases": unit.aliases,
                "metadata": {"decision_role": "boundary"},
                "confidence": 0.9,
            }
        )
    if any(marker in lowered for marker in ("requires ", "depends on", "prerequisite", "dependency")):
        candidates.append(
            {
                "canonical_label": _canonical_label(unit.canonical_title or unit.unit_id),
                "summary": unit.statement,
                "source_refs": base_source_refs,
                "aliases": unit.aliases,
                "metadata": {"decision_role": "dependency"},
                "confidence": 0.7,
            }
        )
    if any(marker in lowered for marker in ("must ", "cannot ", "unless ", "constraint", "prohibited")):
        candidates.append(
            {
                "canonical_label": _canonical_label(unit.canonical_title or unit.unit_id),
                "summary": unit.statement,
                "source_refs": base_source_refs,
                "aliases": unit.aliases,
                "metadata": {"decision_role": "constraint"},
                "confidence": 0.65,
            }
        )
    for component in semantic_chain_decomposition_components(text):
        component_label = _canonical_label(component, markdown_title=True)
        if not component_label:
            continue
        candidates.append(
            {
                "canonical_label": component_label,
                "summary": unit.statement,
                "source_refs": base_source_refs,
                "aliases": (component_label,),
                "metadata": {"decision_role": "transition"},
                "confidence": 0.75,
            }
        )
    return tuple(candidates)


def _extract_itemized_candidates_from_learning_units(context: LearningContext) -> tuple[ItemizedSubjectItem, ...]:
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    for unit in context.units:
        if unit.status != "admitted":
            continue
        canonical_title = _canonical_label(unit.canonical_title or unit.unit_id)
        source_refs = (*unit.provenance_refs, f"unit:{unit.unit_id}")
        if canonical_title:
            _append_or_merge_item(
                built,
                subject_id=context.subject_id,
                item_kind="entity",
                canonical_label=canonical_title,
                source_unit_id=unit.unit_id,
                aliases=unit.aliases,
                summary=unit.statement,
                source_refs=source_refs,
                confidence=0.8,
                metadata={"origin": "learning_unit", "unit_kind": unit.unit_kind, "unit_id": unit.unit_id},
            )
        if unit.statement:
            _append_or_merge_item(
                built,
                subject_id=context.subject_id,
                item_kind="claim",
                canonical_label=canonical_title or _canonical_label(unit.statement),
                source_unit_id=unit.unit_id,
                aliases=unit.aliases,
                summary=unit.statement,
                source_refs=source_refs,
                confidence=0.75,
                metadata={"origin": "learning_unit", "unit_kind": unit.unit_kind, "unit_id": unit.unit_id},
            )
        if unit.unit_kind == "definition" and canonical_title:
            _append_or_merge_item(
                built,
                subject_id=context.subject_id,
                item_kind="glossary_term",
                canonical_label=canonical_title,
                source_unit_id=unit.unit_id,
                aliases=unit.aliases,
                summary=unit.statement,
                source_refs=source_refs,
                confidence=0.85,
                metadata={"origin": "learning_unit", "unit_kind": unit.unit_kind, "unit_id": unit.unit_id},
            )
        for candidate in _decision_role_candidates_from_unit(unit):
            _append_or_merge_item(
                built,
                subject_id=context.subject_id,
                item_kind="decision_role_candidate",
                canonical_label=candidate["canonical_label"],
                source_unit_id=unit.unit_id,
                aliases=_ordered_unique_texts(candidate.get("aliases", ())),
                summary=str(candidate.get("summary", "")),
                source_refs=_ordered_unique_texts(candidate.get("source_refs", ())),
                confidence=float(candidate.get("confidence", 0.6)),
                metadata=dict(candidate.get("metadata", {})),
            )
    return tuple(built.values())


def extract_itemized_candidates_from_markdown_document(
    document: MarkdownDocumentIR,
    *,
    subject_id: str,
    source_id: str,
) -> tuple[ItemizedSubjectItem, ...]:
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    encounters = markdown_learning_encounter_view(document)
    known_symbols: set[str] = set()
    symbol_aliases: dict[str, list[str]] = {}
    xref_candidates = _explicit_xref_candidates(document, subject_id=subject_id, source_id=source_id)

    for encounter in encounters:
        heading = _canonical_label(str(encounter.get("heading", "")).strip(), markdown_title=True)
        aliases = _ordered_unique_texts(markdown_encounter_aliases(encounter))
        source_refs = (source_id, f"encounter:{collapse_ws(str(encounter.get('encounter_id', '')))}")
        candidate_kinds = {
            collapse_ws(str(item)).lower()
            for item in encounter.get("candidate_kinds", [])
            if collapse_ws(str(item))
        }
        if heading:
            _append_or_merge_item(
                built,
                subject_id=subject_id,
                item_kind="entity",
                canonical_label=heading,
                aliases=aliases,
                summary="; ".join(str(item).strip() for item in encounter.get("paragraphs", [])[:1] if collapse_ws(str(item)))[:280],
                source_refs=source_refs,
                confidence=0.7,
                metadata={"origin": "markdown_heading", "sections": list(encounter.get("sections", []))},
            )
        if heading and "definition" in candidate_kinds:
            _append_or_merge_item(
                built,
                subject_id=subject_id,
                item_kind="glossary_term",
                canonical_label=heading,
                aliases=aliases,
                summary="; ".join(str(item).strip() for item in encounter.get("paragraphs", [])[:1] if collapse_ws(str(item)))[:280],
                source_refs=source_refs,
                confidence=0.8,
                metadata={"origin": "markdown_definition_candidate"},
            )
        for output_field, input_fields, expression in markdown_candidate_expression_mappings(encounter):
            normalized_expression = collapse_ws(f"{output_field} = {expression}")
            if normalized_expression:
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="equation",
                    canonical_label=normalized_expression,
                    aliases=aliases,
                    summary=heading or normalized_expression,
                    source_refs=source_refs,
                    confidence=0.92,
                    metadata={
                        "origin": "markdown_equation",
                        "encounter_heading": heading,
                        "output_field": output_field,
                        "input_fields": list(input_fields),
                    },
                )
            for symbol in [output_field, *input_fields]:
                normalized_symbol = collapse_ws(symbol)
                if not normalized_symbol:
                    continue
                known_symbols.add(normalized_symbol)
        for paragraph in encounter.get("paragraphs", [])[:2]:
            cleaned = markdown_clean_learning_text(str(paragraph).strip())
            if not cleaned:
                continue
            _append_or_merge_item(
                built,
                subject_id=subject_id,
                item_kind="claim",
                canonical_label=heading or _canonical_label(cleaned[:120]),
                aliases=aliases,
                summary=cleaned,
                source_refs=source_refs,
                confidence=0.65,
                metadata={"origin": "markdown_paragraph", "encounter_heading": heading},
            )

    for xref_candidate in xref_candidates:
        _append_or_merge_item(
            built,
            subject_id=subject_id,
            item_kind="xref_candidate",
            canonical_label=str(xref_candidate["canonical_label"]),
            aliases=_ordered_unique_texts(xref_candidate.get("aliases", ())),
            summary=str(xref_candidate["summary"]),
            source_refs=_ordered_unique_texts(xref_candidate["source_refs"]),
            confidence=0.95,
            metadata=dict(xref_candidate["metadata"]),
        )

    if known_symbols:
        symbol_aliases = markdown_document_symbol_aliases(document, sorted(known_symbols))
    for symbol in sorted(known_symbols):
        _append_or_merge_item(
            built,
            subject_id=subject_id,
            item_kind="variable",
            canonical_label=collapse_ws(symbol),
            aliases=_ordered_unique_texts(symbol_aliases.get(symbol, [])),
            summary=f"Symbol candidate extracted from markdown equations for {document.title}.",
            source_refs=(source_id,),
            confidence=0.88,
            metadata={"origin": "markdown_equation_symbols"},
        )

    return tuple(built.values())


def _direct_llm_markdown_itemization_schema_hint() -> dict[str, Any]:
    return {
        "decompose_now": True,
        "preserve_parent": False,
        "preserve_reason": "",
        "rationale": "Return candidate itemization output only.",
        "candidates": [
            {
                "canonical_label": "Introduce contactless bank-card payment",
                "item_kind": "decision_role_candidate",
                "decision_role": "transition",
                "summary": "Target arrangement introduces contactless bank-card payment.",
                "aliases": ["contactless bank-card payment"],
                "confidence": 0.8,
            },
            {
                "canonical_label": "Fare payment supports contactless bank-card payment",
                "item_kind": "decision_role_candidate",
                "decision_role": "state",
                "summary": "The achieved fare-payment arrangement supports contactless bank-card payment.",
                "aliases": ["contactless bank-card payment available"],
                "confidence": 0.8,
            }
        ],
    }


def _direct_llm_markdown_itemization_fallback_payload() -> dict[str, Any]:
    return {
        "decompose_now": False,
        "preserve_parent": True,
        "preserve_reason": "No additional candidate decomposition is available beyond deterministic itemization.",
        "rationale": "Fallback leaves source-side decomposition empty and lets deterministic itemization proceed.",
        "candidates": [],
    }


_WEAKLY_STRUCTURED_SHARED_HEAD_WORDS = {
    "payment",
    "payments",
    "service",
    "services",
    "system",
    "systems",
    "tool",
    "tools",
    "mode",
    "modes",
}
_INTRODUCE_VERB_PREFIXES = (
    "introduce",
    "adopt",
    "enable",
    "add",
    "move to",
    "shift to",
    "switch to",
)
_TEMPORAL_ACTOR_NOISE_PATTERNS = (
    r"\bat present\b",
    r"\bcurrently\b",
    r"\btoday\b",
    r"\bnow\b",
)
_WEAKLY_STRUCTURED_PARTY_LIST_PATTERNS = (
    r"^(?:the\s+)?(?:main|key)?\s*part(?:y|ies)\s+(?:involved|responsible|participating)\s+(?:is|are)\s+(?P<actors>.+?)\.?$",
    r"^(?:the\s+)?stakeholders?\s+(?:include|are)\s+(?P<actors>.+?)\.?$",
)
_WEAKLY_STRUCTURED_ACTOR_MODAL_PATTERNS = (
    r"^(?P<actor>(?:a|an|the)\s+.+?|[A-Z][^.]+?)\s+wants?\s+to\s+(?P<objective>.+?)\.?$",
    r"^(?P<actor>(?:a|an|the)\s+.+?|[A-Z][^.]+?)\s+needs?\s+(?P<objective>.+?)\.?$",
    r"^(?P<actor>(?:a|an|the)\s+.+?|[A-Z][^.]+?)\s+must\s+(?P<objective>.+?)\.?$",
)
_OBJECTIVE_DOMAIN_VERB_PREFIXES = (
    "modernize",
    "upgrade",
    "improve",
    "digitize",
    "transform",
    "replace",
    "simplify",
    "streamline",
    "strengthen",
    "expand",
    "extend",
    "coordinate",
)
_LEGACY_STATE_OBJECTIVE_VERB_PREFIXES = (
    "modernize",
    "upgrade",
    "digitize",
    "replace",
    "transform",
    "shift",
    "switch",
    "migrate",
)


def _is_weakly_structured_markdown_document(document: MarkdownDocumentIR) -> bool:
    return not bool(document.sections) and bool(document.intro_bullets or document.intro_paragraphs)


def _weakly_structured_markdown_fragments(document: MarkdownDocumentIR) -> tuple[str, ...]:
    fragments: list[str] = []
    for bullet in document.intro_bullets:
        cleaned = markdown_clean_learning_text(collapse_ws(bullet).strip())
        if cleaned:
            fragments.append(cleaned)
    for paragraph in document.intro_paragraphs:
        cleaned = markdown_clean_learning_text(collapse_ws(paragraph).strip())
        if not cleaned:
            continue
        sentence_parts = [
            markdown_clean_learning_text(collapse_ws(part).strip())
            for part in re.split(r"(?<=[.!?])\s+", cleaned)
            if markdown_clean_learning_text(collapse_ws(part).strip())
        ]
        if sentence_parts:
            fragments.extend(sentence_parts)
    return _ordered_unique_texts(fragments)


def _strip_leading_article(text: str) -> str:
    return re.sub(r"^(?:a|an|the)\s+", "", collapse_ws(text), flags=re.IGNORECASE)


def _normalized_actor_candidate_label(text: str) -> str:
    normalized = _strip_leading_article(text)
    normalized = re.sub(r"^(?:and|or)\s+", "", normalized, flags=re.IGNORECASE)
    for pattern in _TEMPORAL_ACTOR_NOISE_PATTERNS:
        normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)
    normalized = collapse_ws(normalized.strip(" .,:;"))
    return normalized


def _actor_label_tokens(text: str) -> tuple[str, ...]:
    return tuple(
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9-]*", collapse_ws(text))
        if collapse_ws(token)
    )


def _token_sequence_is_contiguous_subsequence(shorter: tuple[str, ...], longer: tuple[str, ...]) -> bool:
    if not shorter or len(shorter) >= len(longer):
        return False
    for index in range(0, len(longer) - len(shorter) + 1):
        if longer[index : index + len(shorter)] == shorter:
            return True
    return False


def _split_target_transition_clause(objects_text: str) -> tuple[str, tuple[str, ...]]:
    normalized = markdown_clean_learning_text(collapse_ws(objects_text).strip(" .,:;"))
    if not normalized:
        return "", ()
    parts = re.split(
        r"\s*,?\s+(?:while|without)\s+",
        normalized,
        maxsplit=1,
        flags=re.IGNORECASE,
    )
    primary = markdown_clean_learning_text(collapse_ws(parts[0]).strip(" .,:;"))
    constraints: list[str] = []
    if len(parts) > 1:
        trailing = markdown_clean_learning_text(collapse_ws(parts[1]).strip(" .,:;"))
        keep_match = re.match(
            r"^(?:keeping|maintaining)\s+(?P<object>.+?)\s+(?P<descriptors>reliable|accessible|secure|dependable|available|fair|inclusive)(?:\s+and\s+(?P<descriptor_two>reliable|accessible|secure|dependable|available|fair|inclusive))*\.?$",
            trailing,
            flags=re.IGNORECASE,
        )
        if keep_match:
            object_text = _strip_leading_article(
                markdown_clean_learning_text(collapse_ws(keep_match.group("object")).strip(" .,:;"))
            )
            descriptor_values = [
                keep_match.group("descriptors"),
                keep_match.group("descriptor_two"),
            ]
            for descriptor in descriptor_values:
                descriptor_text = markdown_clean_learning_text(collapse_ws(str(descriptor or "")).strip(" .,:;"))
                if object_text and descriptor_text:
                    constraints.append(f"keep {object_text} {descriptor_text}")
    return primary, _ordered_unique_texts(constraints)


def _postprocess_markdown_role_candidates(
    items: tuple[ItemizedSubjectItem, ...],
) -> tuple[ItemizedSubjectItem, ...]:
    rebuilt: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    for item in items:
        metadata = dict(item.metadata)
        decision_role = collapse_ws(str(metadata.get("decision_role", ""))).casefold()
        canonical_label = item.canonical_label
        aliases = item.aliases
        if decision_role == "actor":
            normalized_actor_label = _normalized_actor_candidate_label(item.canonical_label)
            if not normalized_actor_label:
                continue
            if collapse_ws(normalized_actor_label).casefold() != collapse_ws(item.canonical_label).casefold():
                aliases = _ordered_unique_texts((*item.aliases, item.canonical_label))
                canonical_label = normalized_actor_label
        _append_or_merge_item(
            rebuilt,
            subject_id=item.subject_id,
            item_kind=item.item_kind,
            canonical_label=canonical_label,
            source_unit_id=item.source_unit_id,
            aliases=aliases,
            summary=item.summary,
            source_refs=item.source_refs,
            confidence=item.confidence,
            linked_item_ids=item.linked_item_ids,
            metadata=metadata,
        )
    actor_labels_to_drop: set[str] = set()
    actor_items = [
        item
        for item in rebuilt.values()
        if collapse_ws(str(item.metadata.get("decision_role", ""))).casefold() == "actor"
    ]
    for candidate in actor_items:
        candidate_tokens = _actor_label_tokens(candidate.canonical_label)
        if not candidate_tokens:
            actor_labels_to_drop.add(candidate.canonical_label.casefold())
            continue
        for other in actor_items:
            if other.itemized_item_id == candidate.itemized_item_id:
                continue
            other_tokens = _actor_label_tokens(other.canonical_label)
            if _token_sequence_is_contiguous_subsequence(candidate_tokens, other_tokens):
                actor_labels_to_drop.add(candidate.canonical_label.casefold())
                break
    if not actor_labels_to_drop:
        return tuple(rebuilt.values())
    return tuple(
        item
        for item in rebuilt.values()
        if not (
            collapse_ws(str(item.metadata.get("decision_role", ""))).casefold() == "actor"
            and item.canonical_label.casefold() in actor_labels_to_drop
        )
    )


def _objective_domain_phrase(objective_text: str) -> str:
    normalized = markdown_clean_learning_text(collapse_ws(objective_text).strip(" .,:;"))
    if not normalized:
        return ""
    lowered = normalized.casefold()
    for prefix in _OBJECTIVE_DOMAIN_VERB_PREFIXES:
        prefix_text = f"{prefix} "
        if lowered.startswith(prefix_text):
            remainder = markdown_clean_learning_text(normalized[len(prefix_text):].strip(" .,:;"))
            return remainder or normalized
    return normalized


def _state_prefix_for_objective(objective_text: str) -> str:
    lowered = collapse_ws(objective_text).casefold()
    for prefix in _LEGACY_STATE_OBJECTIVE_VERB_PREFIXES:
        if lowered.startswith(f"{prefix} "):
            return "legacy"
    return "current"


def _normalized_state_candidate_label(*, mode_text: str, objective_text: str) -> str:
    normalized_mode = markdown_clean_learning_text(collapse_ws(mode_text).strip(" .,:;"))
    if not normalized_mode:
        return ""
    domain_phrase = _objective_domain_phrase(objective_text)
    if not domain_phrase:
        return normalized_mode
    return f"{_state_prefix_for_objective(objective_text)} {domain_phrase} via {normalized_mode}"


def _normalized_transition_candidate_label(*, verb_text: str, mode_text: str) -> str:
    normalized_mode = markdown_clean_learning_text(collapse_ws(mode_text).strip(" .,:;"))
    normalized_verb = markdown_clean_learning_text(collapse_ws(verb_text).strip(" .,:;"))
    if not normalized_mode:
        return ""
    if not normalized_verb:
        return normalized_mode
    return f"{normalized_verb} {normalized_mode}"


def _normalized_target_state_candidate_label(*, mode_text: str, objective_text: str) -> str:
    normalized_mode = markdown_clean_learning_text(collapse_ws(mode_text).strip(" .,:;"))
    if not normalized_mode:
        return ""
    domain_phrase = _objective_domain_phrase(objective_text)
    if domain_phrase:
        return f"{domain_phrase} supports {normalized_mode}"
    return f"{normalized_mode} available"


def _shared_head_suffix_for_phrase(fragment: str, reference: str) -> tuple[str, ...]:
    fragment_tokens = [token for token in collapse_ws(fragment).split() if token]
    reference_tokens = [token for token in collapse_ws(reference).split() if token]
    if not fragment_tokens or len(fragment_tokens) > 2 or not reference_tokens:
        return ()
    if fragment_tokens[-1].lower() in _WEAKLY_STRUCTURED_SHARED_HEAD_WORDS:
        return ()
    if "-" not in fragment_tokens[-1] and not fragment_tokens[-1].lower().endswith(("based", "less")):
        return ()
    last_reference = reference_tokens[-1].lower()
    if last_reference not in _WEAKLY_STRUCTURED_SHARED_HEAD_WORDS:
        return ()
    return (reference_tokens[-1],)


def _split_weakly_structured_phrase(phrase: str) -> tuple[str, ...]:
    normalized = markdown_clean_learning_text(collapse_ws(phrase).strip(" .,:;"))
    if not normalized:
        return ()
    comma_segments = [segment.strip() for segment in re.split(r"\s*,\s*", normalized) if collapse_ws(segment)]
    if not comma_segments:
        return ()
    built: list[str] = []
    for segment in comma_segments:
        parts = [collapse_ws(part) for part in re.split(r"\s+(?:and|or)\s+", segment) if collapse_ws(part)]
        if len(parts) >= 2:
            normalized_parts: list[str] = []
            for index, part in enumerate(parts):
                if index < len(parts) - 1:
                    suffix = _shared_head_suffix_for_phrase(part, parts[index + 1])
                    if suffix:
                        part = f"{part} {' '.join(suffix)}"
                normalized_parts.append(part)
            built.extend(normalized_parts)
        else:
            built.append(segment)
    return _ordered_unique_texts(
        markdown_clean_learning_text(collapse_ws(item).strip(" .,:;"))
        for item in built
        if markdown_clean_learning_text(collapse_ws(item).strip(" .,:;"))
    )


def _extract_weakly_structured_itemized_candidates_from_markdown_document(
    document: MarkdownDocumentIR,
    *,
    subject_id: str,
    source_id: str,
) -> tuple[ItemizedSubjectItem, ...]:
    if not _is_weakly_structured_markdown_document(document):
        return ()
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    source_refs = (source_id, "chunk:source")
    current_objective_text = ""
    for fragment in _weakly_structured_markdown_fragments(document):
        lowered = collapse_ws(fragment).lower().rstrip(".")
        for party_list_pattern in _WEAKLY_STRUCTURED_PARTY_LIST_PATTERNS:
            party_list_match = re.match(party_list_pattern, fragment, flags=re.IGNORECASE)
            if not party_list_match:
                continue
            for actor_text in _split_weakly_structured_phrase(party_list_match.group("actors")):
                normalized_actor_text = _normalized_actor_candidate_label(actor_text)
                if not normalized_actor_text:
                    continue
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(normalized_actor_text, markdown_title=True),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.79,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "actor",
                    },
                )
            break
        actor_match: re.Match[str] | None = None
        for actor_pattern in _WEAKLY_STRUCTURED_ACTOR_MODAL_PATTERNS:
            actor_match = re.match(actor_pattern, fragment, flags=re.IGNORECASE)
            if actor_match:
                break
        if actor_match:
            actor_text = _normalized_actor_candidate_label(actor_match.group("actor"))
            objective_text = markdown_clean_learning_text(collapse_ws(actor_match.group("objective")).strip(" ."))
            if actor_text and len(actor_text.split()) >= 1:
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(actor_text, markdown_title=True),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.78,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "actor",
                    },
                )
            if objective_text and not any(
                objective_text.lower().startswith(prefix) for prefix in _INTRODUCE_VERB_PREFIXES
            ) and re.match(r"^(?:to\s+)?(?:keep|maintain|support|ensure|be)\b", objective_text, flags=re.IGNORECASE) is None:
                current_objective_text = objective_text
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(objective_text, markdown_title=True),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.76,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "objective",
                    },
                )
        current_state_match = re.match(
            r"^(?:today|currently|at present|now)\s*,?\s+.+?\s+(?:mostly\s+|primarily\s+)?(?:use|uses|rely on|depends on|pay with|pay using)\s+(?P<objects>.+?)\.?$",
            lowered,
            flags=re.IGNORECASE,
        )
        if current_state_match:
            for state_text in _split_weakly_structured_phrase(current_state_match.group("objects")):
                normalized_state_label = _normalized_state_candidate_label(
                    mode_text=state_text,
                    objective_text=current_objective_text,
                )
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(normalized_state_label or state_text, markdown_title=True),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.74,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "state",
                    },
                )
        target_match = re.match(
            r"^(?:.+?)\s+wants?\s+to\s+(?P<verb>introduce|adopt|enable|add|move to|shift to|switch to)\s+(?P<objects>.+?)\.?$",
            lowered,
            flags=re.IGNORECASE,
        )
        if target_match:
            verb_text = markdown_clean_learning_text(collapse_ws(target_match.group("verb")).strip(" ."))
            transition_objects_text, constraint_labels = _split_target_transition_clause(target_match.group("objects"))
            for constraint_label in constraint_labels:
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(constraint_label, markdown_title=True),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.72,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "constraint",
                    },
                )
            for transition_text in _split_weakly_structured_phrase(transition_objects_text or target_match.group("objects")):
                normalized_transition_label = _normalized_transition_candidate_label(
                    verb_text=verb_text,
                    mode_text=transition_text,
                )
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(
                        normalized_transition_label or transition_text,
                        markdown_title=True,
                    ),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.74,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "transition",
                    },
                )
                normalized_target_state_label = _normalized_target_state_candidate_label(
                    mode_text=transition_text,
                    objective_text=current_objective_text,
                )
                _append_or_merge_item(
                    built,
                    subject_id=subject_id,
                    item_kind="decision_role_candidate",
                    canonical_label=_canonical_label(
                        normalized_target_state_label or transition_text,
                        markdown_title=True,
                    ),
                    aliases=(),
                    summary=fragment,
                    source_refs=source_refs,
                    confidence=0.72,
                    metadata={
                        "origin": "markdown_weakly_structured_source_decomposition",
                        "decision_role": "state",
                    },
                )
    return _postprocess_markdown_role_candidates(tuple(built.values()))


def _extract_direct_llm_itemized_candidates_from_markdown_document(
    document: MarkdownDocumentIR,
    *,
    subject_id: str,
    source_id: str,
    llm_policy: str = "auto",
    proposal_port: ItemizationProposalPort | None = None,
) -> tuple[ItemizedSubjectItem, ...]:
    prompt_view = bounded_markdown_learning_prompt_view(document, max_clusters=6)
    if proposal_port is None:
        return ()
    try:
        proposal = proposal_port.request_itemization_proposal(
            semantic_unit=f"Itemize source prose for {collapse_ws(document.title) or subject_id}",
            llm_policy=llm_policy,
            target_scope=f"itemize:{subject_id}:{source_id}",
            instructions=(
                "Decompose the bounded source prose into candidate itemization output for the workstation.\n\n"
                "Rules:\n"
                "- This is Itemize-time candidate decomposition only.\n"
                "- Do not rewrite the source into publication prose.\n"
                "- Do not claim final truth or approval.\n"
                "- Return at most 12 candidates.\n"
                "- Prefer concrete actors, objectives, capabilities, dependencies, constraints, boundaries, states, transitions, and decisions when present.\n"
                "- If a candidate clearly fits one of those roles, use item_kind `decision_role_candidate` and set `decision_role`.\n"
                "- Otherwise use a simple item kind such as `claim`, `entity`, `keyword`, or `assumption`.\n"
                "- Verification rule: only emit a candidate if the bounded source snapshot directly supports it.\n"
                "- Verification rule: if you cannot point to a concrete source phrase that grounds the candidate, omit it.\n"
                "- Use concise canonical labels, but normalize them to the candidate role rather than copying raw nouns.\n"
                "- For actor/objective prose like '<actor> wants to <objective>', emit both the actor and the objective when directly supported.\n"
                "- For stakeholder-list prose like 'the main parties involved are A, B, C', emit each party as its own verified actor candidate.\n"
                "- For actor clauses like 'X needs ...' or 'X must ...', keep X as the actor and derive additional role-shaped candidates only when the prose directly supports them.\n"
                "- Do not keep temporal adverbs like 'now', 'today', 'currently', or 'at present' inside actor labels.\n"
                "- Do not emit generic actor placeholders like 'city' when the same source gives a more specific party such as 'city regulator' or 'city transit authority'.\n"
                "- For current-state prose like 'today/currently ... use/pay with X', do not emit bare nouns like 'Cash'; emit role-shaped state labels like 'legacy fare payment via cash' or 'current payment flow via cash' when the domain is supported.\n"
                "- For target-change prose like 'introduce/adopt/enable/add/move to/shift to X', emit role-shaped transition labels like 'introduce app-based payment' rather than bare target-mode nouns.\n"
                "- For target-change prose, when the achieved arrangement is directly inferable, emit both the transition and the resulting target state or capability.\n"
                "- Example: from 'introduce contactless bank-card payment', emit transition 'introduce contactless bank-card payment' and a paired target state/capability such as 'fare payment supports contactless bank-card payment'.\n"
                "- Verification rule: only emit the paired target state/capability when the bounded source snapshot makes that achieved arrangement a clear intended outcome.\n"
                "- Trailing clauses like 'while keeping the bus network reliable and accessible' are constraints/objectives about what must be preserved; do not treat 'reliable' or 'accessible' as standalone payment modes.\n"
                "- Keep current-state and target-state labels parallel when the same domain is being modernized.\n"
                "- If one sentence enumerates multiple current modes or multiple target modes, split them into separate verified candidates.\n"
                "- Summary should stay short, factual, and grounded in the supporting phrase.\n"
                "- Avoid decorative restatement of the title.\n\n"
                "Bounded source snapshot:\n"
                f"{json.dumps(prompt_view, indent=2, sort_keys=True)}"
            ),
            fallback_payload=_direct_llm_markdown_itemization_fallback_payload(),
            schema_hint=_direct_llm_markdown_itemization_schema_hint(),
        )
    except Exception:
        return ()
    payload = dict(proposal.payload or {})
    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return ()
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    for ordinal, candidate in enumerate(raw_candidates[:12], start=1):
        if not isinstance(candidate, Mapping):
            continue
        canonical_label = _canonical_label(
            collapse_ws(
                str(
                    candidate.get("canonical_label")
                    or candidate.get("label")
                    or candidate.get("title")
                    or ""
                )
            ),
            markdown_title=True,
        )
        if not canonical_label:
            continue
        decision_role = normalize_itemized_decision_role(candidate.get("decision_role", ""))
        requested_kind = collapse_ws(str(candidate.get("item_kind", ""))).lower()
        if requested_kind not in VALID_ITEMIZED_ITEM_KINDS:
            requested_kind = "decision_role_candidate" if decision_role else "claim"
        item_kind = "decision_role_candidate" if decision_role else requested_kind
        aliases = _ordered_unique_texts(candidate.get("aliases", ()))
        summary = markdown_clean_learning_text(
            collapse_ws(str(candidate.get("summary", ""))) or canonical_label
        )
        confidence = float(candidate.get("confidence", 0.82) or 0.82)
        source_refs = (source_id, "chunk:source")
        metadata = {
            "origin": "markdown_direct_llm_decomposition",
            "source_chunk_kind": "source_snapshot",
            "decomposition_proposal_id": str(proposal.proposal_id),
            "llm_source": str(proposal.source),
            "decomposition_ordinal": ordinal,
        }
        if decision_role:
            metadata["decision_role"] = decision_role
        _append_or_merge_item(
            built,
            subject_id=subject_id,
            item_kind=item_kind,
            canonical_label=canonical_label,
            aliases=aliases,
            summary=summary,
            source_refs=source_refs,
            confidence=max(0.45, min(0.95, confidence)),
            metadata=metadata,
        )
    return _postprocess_markdown_role_candidates(tuple(built.values()))


def _load_source_body_text(root_path: Path, source: LearningSource) -> str:
    body_relpath = str(source.body_relpath or "").strip()
    if not body_relpath:
        return ""
    body_path = learning_context_paths(root_path, source.subject_id)["sources"] / body_relpath
    try:
        return body_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_url_elements(root_path: Path, source: LearningSource) -> tuple[dict[str, Any], ...]:
    bundle_root = learning_source_bundle_root(root_path, source.subject_id, source.source_id)
    elements_path = bundle_root / "elements.json"
    try:
        payload = json.loads(elements_path.read_text(encoding="utf-8"))
    except Exception:
        return ()
    if not isinstance(payload, list):
        return ()
    return tuple(item for item in payload if isinstance(item, dict))


def _extract_itemized_candidates_from_url_source(
    root_path: Path,
    source: LearningSource,
) -> tuple[ItemizedSubjectItem, ...]:
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    elements = _load_url_elements(root_path, source)
    if not elements:
        return ()
    headings = [
        _canonical_label(str(item.get("text", "")).strip(), markdown_title=True)
        for item in elements
        if collapse_ws(str(item.get("kind", ""))).lower() == "heading" and collapse_ws(str(item.get("text", "")))
    ]
    paragraphs = [
        markdown_clean_learning_text(str(item.get("text", "")).strip())
        for item in elements
        if collapse_ws(str(item.get("kind", ""))).lower() in {"paragraph", "list_item", "blockquote"}
        and collapse_ws(str(item.get("text", "")))
    ]
    for heading in headings[:8]:
        _append_or_merge_item(
            built,
            subject_id=source.subject_id,
            item_kind="entity",
            canonical_label=heading,
            aliases=(heading,),
            summary=f"Heading extracted from {source.title or source.source_ref}.",
            source_refs=(source.source_id,),
            confidence=0.72,
            metadata={"origin": "url_heading", "source_kind": source.source_kind},
        )
        _append_or_merge_item(
            built,
            subject_id=source.subject_id,
            item_kind="glossary_term",
            canonical_label=heading,
            aliases=(heading,),
            summary=f"Heading candidate extracted from {source.title or source.source_ref}.",
            source_refs=(source.source_id,),
            confidence=0.68,
            metadata={"origin": "url_heading", "source_kind": source.source_kind},
        )
    for paragraph in paragraphs[:6]:
        _append_or_merge_item(
            built,
            subject_id=source.subject_id,
            item_kind="claim",
            canonical_label=_canonical_label(paragraph[:120]),
            aliases=(),
            summary=paragraph,
            source_refs=(source.source_id,),
            confidence=0.6,
            metadata={"origin": "url_text_element", "source_kind": source.source_kind},
        )
    for item in elements:
        if collapse_ws(str(item.get("kind", ""))).lower() != "image":
            continue
        src = collapse_ws(str(item.get("src", "")))
        alt = markdown_clean_learning_text(str(item.get("alt", "")).strip())
        label = _canonical_label(alt or src, markdown_title=True)
        if not label:
            continue
        _append_or_merge_item(
            built,
            subject_id=source.subject_id,
            item_kind="figure_candidate",
            canonical_label=label,
            aliases=(alt,) if alt else (),
            summary=f"Image candidate from {src}.",
            source_refs=(source.source_id,),
            confidence=0.9,
            metadata={"origin": "url_image", "asset_src": src, "alt": alt},
        )
    return tuple(built.values())


def _list_learning_sources(root_path: Path, subject_id: str) -> tuple[LearningSource, ...]:
    sources_root = learning_context_paths(root_path, subject_id)["sources"]
    if not sources_root.exists():
        return ()
    sources: list[LearningSource] = []
    for path in sorted(sources_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        source = LearningSource.from_dict(payload)
        if source.source_id:
            sources.append(source)
    return tuple(
        sorted(
            sources,
            key=lambda source: (
                source.title.casefold(),
                source.source_id,
            ),
        )
    )


def extract_itemized_candidates_from_learning_context(
    root_path: Path,
    context: LearningContext,
    *,
    allow_direct_llm_decomposition: bool = False,
    proposal_port: ItemizationProposalPort | None = None,
) -> tuple[ItemizedSubjectItem, ...]:
    built: dict[tuple[str, ...], ItemizedSubjectItem] = {}
    for item in _extract_itemized_candidates_from_learning_units(context):
        built[_mergeable_item_key(item.item_kind, item.canonical_label, item.metadata)] = item
    discovered_sources = {source.source_id: source for source in _list_learning_sources(root_path, context.subject_id)}
    for source_id in context.linked_source_ids:
        if source_id in discovered_sources:
            continue
        try:
            discovered_sources[source_id] = load_learning_source(root_path, context.subject_id, source_id)
        except Exception:
            continue
    for source in tuple(discovered_sources.values()):
        markdown_text = _load_source_body_text(root_path, source)
        if markdown_text and (
            "markdown" in source.media_type.lower()
            or str(source.body_relpath).lower().endswith(".md")
        ):
            document = parse_markdown_document_ir(markdown_text, source_path=source.source_ref or source.body_relpath)
            if allow_direct_llm_decomposition:
                direct_items = _extract_direct_llm_itemized_candidates_from_markdown_document(
                    document,
                    subject_id=context.subject_id,
                    source_id=source.source_id,
                    proposal_port=proposal_port,
                )
                for item in direct_items:
                    _append_or_merge_item(
                        built,
                        subject_id=item.subject_id,
                        item_kind=item.item_kind,
                        canonical_label=item.canonical_label,
                        aliases=item.aliases,
                        summary=item.summary,
                        source_refs=item.source_refs,
                            confidence=item.confidence,
                            metadata=item.metadata,
                        )
                for item in _extract_weakly_structured_itemized_candidates_from_markdown_document(
                    document,
                    subject_id=context.subject_id,
                    source_id=source.source_id,
                ):
                    _append_or_merge_item(
                        built,
                        subject_id=item.subject_id,
                        item_kind=item.item_kind,
                        canonical_label=item.canonical_label,
                        aliases=item.aliases,
                        summary=item.summary,
                        source_refs=item.source_refs,
                        confidence=item.confidence,
                        metadata=item.metadata,
                    )
            for item in extract_itemized_candidates_from_markdown_document(
                document,
                subject_id=context.subject_id,
                source_id=source.source_id,
            ):
                _append_or_merge_item(
                    built,
                    subject_id=item.subject_id,
                    item_kind=item.item_kind,
                    canonical_label=item.canonical_label,
                    aliases=item.aliases,
                    summary=item.summary,
                    source_refs=item.source_refs,
                    confidence=item.confidence,
                    metadata=item.metadata,
                )
        if source.source_kind == "url":
            for item in _extract_itemized_candidates_from_url_source(root_path, source):
                _append_or_merge_item(
                    built,
                    subject_id=item.subject_id,
                    item_kind=item.item_kind,
                    canonical_label=item.canonical_label,
                    aliases=item.aliases,
                    summary=item.summary,
                    source_refs=item.source_refs,
                    confidence=item.confidence,
                    metadata=item.metadata,
                )
    postprocessed_items = _postprocess_markdown_role_candidates(tuple(built.values()))
    return tuple(
        sorted(
            postprocessed_items,
            key=lambda item: (
                item.item_kind,
                item.canonical_label.casefold(),
                item.itemized_item_id,
            ),
        )
    )


def materialize_itemization_session(
    root_path: Path,
    subject_id: str,
    *,
    allow_direct_llm_decomposition: bool = False,
    proposal_port: ItemizationProposalPort | None = None,
) -> tuple[ItemizationSession, tuple[ItemizedSubjectItem, ...]]:
    context = load_learning_context(root_path, subject_id)
    existing_by_id = {
        item.itemized_item_id: item
        for item in list_itemized_subject_items(root_path, subject_id)
    }
    existing_by_continuity_key: dict[tuple[str, ...], list[ItemizedSubjectItem]] = {}
    for item in existing_by_id.values():
        continuity_key = _itemized_continuity_key(item)
        if not continuity_key:
            continue
        existing_by_continuity_key.setdefault(continuity_key, []).append(item)
    generated_items = extract_itemized_candidates_from_learning_context(
        root_path,
        context,
        allow_direct_llm_decomposition=allow_direct_llm_decomposition,
        proposal_port=proposal_port,
    )
    direct_llm_candidate_count = sum(
        1
        for item in generated_items
        if (
            collapse_ws(str(item.metadata.get("origin", ""))) == "markdown_direct_llm_decomposition"
            or "markdown_direct_llm_decomposition"
            in {
                collapse_ws(str(value))
                for value in item.metadata.get("origins", ())
                if collapse_ws(str(value))
            }
        )
    )
    fallback_candidate_count = sum(
        1
        for item in generated_items
        if (
            collapse_ws(str(item.metadata.get("origin", ""))) == "markdown_weakly_structured_source_decomposition"
            or "markdown_weakly_structured_source_decomposition"
            in {
                collapse_ws(str(value))
                for value in item.metadata.get("origins", ())
                if collapse_ws(str(value))
            }
        )
    )
    now_epoch_ms = int(time.time() * 1000)
    items: list[ItemizedSubjectItem] = []
    persisted_item_ids: set[str] = set()
    matched_existing_item_ids: set[str] = set()
    for item in generated_items:
        existing_item = existing_by_id.get(item.itemized_item_id)
        if existing_item is None:
            continuity_key = _itemized_continuity_key(item)
            continuity_candidates = [
                candidate
                for candidate in existing_by_continuity_key.get(continuity_key, ())
                if candidate.itemized_item_id not in matched_existing_item_ids
            ]
            if continuity_candidates:
                existing_item = max(
                    continuity_candidates,
                    key=lambda candidate: _itemized_continuity_match_score(item, candidate),
                )
        preserved_rephrase = existing_item is not None and _itemized_intermediate_was_rephrased(existing_item)
        merged_metadata = _normalized_itemized_metadata(
            {
                **dict(item.metadata),
                **(dict(existing_item.metadata) if existing_item is not None else {}),
            }
        )
        resolved_itemized_item_id = (
            existing_item.itemized_item_id
            if existing_item is not None and collapse_ws(existing_item.itemized_item_id)
            else item.itemized_item_id
        )
        resolved_label = existing_item.canonical_label if preserved_rephrase else item.canonical_label
        resolved_summary = existing_item.summary if preserved_rephrase else item.summary
        resolved_source_unit_id = _resolve_itemized_source_unit_id(context, item)
        merged_aliases = _ordered_unique_texts(
            (
                *item.aliases,
                *(existing_item.aliases if existing_item is not None else ()),
                *((item.canonical_label,) if preserved_rephrase else ()),
            )
        )
        if preserved_rephrase:
            if collapse_ws(item.canonical_label):
                merged_metadata["latest_generated_canonical_label"] = item.canonical_label
            if collapse_ws(item.summary):
                merged_metadata["latest_generated_summary"] = item.summary
        items.append(
            ItemizedSubjectItem(
                itemized_item_id=resolved_itemized_item_id,
                subject_id=item.subject_id,
                item_kind=item.item_kind,
                canonical_label=resolved_label,
                source_unit_id=resolved_source_unit_id,
                aliases=merged_aliases,
                summary=resolved_summary,
                source_refs=_ordered_unique_texts(
                    (
                        *item.source_refs,
                        *(existing_item.source_refs if existing_item is not None else ()),
                    )
                ),
                confidence=item.confidence,
                status=existing_item.status if existing_item is not None else item.status,
                linked_item_ids=(
                    existing_item.linked_item_ids
                    if existing_item is not None and existing_item.linked_item_ids
                    else item.linked_item_ids
                ),
                created_at_epoch_ms=(
                    existing_item.created_at_epoch_ms
                    if existing_item is not None and existing_item.created_at_epoch_ms > 0
                    else now_epoch_ms
                ),
                updated_at_epoch_ms=now_epoch_ms,
                schema_version=item.schema_version,
                metadata=merged_metadata,
            )
        )
        persisted_item_ids.add(resolved_itemized_item_id)
        if existing_item is not None and collapse_ws(existing_item.itemized_item_id):
            matched_existing_item_ids.add(existing_item.itemized_item_id)
    for existing_item in existing_by_id.values():
        if existing_item.itemized_item_id in persisted_item_ids:
            continue
        origin = collapse_ws(str(existing_item.metadata.get("origin", ""))).casefold()
        if origin not in {"itemize_merge", "itemize_split"}:
            continue
        items.append(
            ItemizedSubjectItem(
                itemized_item_id=existing_item.itemized_item_id,
                subject_id=existing_item.subject_id,
                item_kind=existing_item.item_kind,
                canonical_label=existing_item.canonical_label,
                source_unit_id=existing_item.source_unit_id,
                aliases=existing_item.aliases,
                summary=existing_item.summary,
                source_refs=existing_item.source_refs,
                confidence=existing_item.confidence,
                status=existing_item.status,
                linked_item_ids=existing_item.linked_item_ids,
                created_at_epoch_ms=existing_item.created_at_epoch_ms or now_epoch_ms,
                updated_at_epoch_ms=existing_item.updated_at_epoch_ms or now_epoch_ms,
                schema_version=existing_item.schema_version,
                metadata=_normalized_itemized_metadata(existing_item.metadata),
            )
        )
    items_tuple = tuple(items)
    session_id = stable_itemization_session_id(
        subject_id=context.subject_id,
        learning_context_snapshot_hash=context.content_hash(),
    )
    existing = _read_json(itemization_paths(root_path, context.subject_id)["session"])
    existing_session = ItemizationSession.from_dict(existing) if existing else None
    created_at_epoch_ms = now_epoch_ms
    if existing_session and existing_session.itemization_session_id == session_id:
        created_at_epoch_ms = existing_session.created_at_epoch_ms or now_epoch_ms
    session = ItemizationSession(
        itemization_session_id=session_id,
        subject_id=context.subject_id,
        learning_context_snapshot_hash=context.content_hash(),
        item_ids=tuple(item.itemized_item_id for item in items_tuple),
        status="active",
        created_at_epoch_ms=created_at_epoch_ms,
        updated_at_epoch_ms=now_epoch_ms,
        metadata={
            "subject_title": context.canonical_title,
            "item_count": len(items_tuple),
            "linked_source_count": len(context.linked_source_ids),
            "direct_llm_decomposition_status": (
                "disabled"
                if not allow_direct_llm_decomposition
                else "used"
                if direct_llm_candidate_count > 0
                else "fallback"
                if fallback_candidate_count > 0
                else "empty"
            ),
            "direct_llm_candidate_count": direct_llm_candidate_count,
            "fallback_candidate_count": fallback_candidate_count,
        },
    )
    persist_itemization_session(root_path, session, items_tuple)
    return session, items_tuple


__all__ = [
    "ITEMIZATION_SCHEMA_VERSION",
    "ItemizationProposalPort",
    "ItemizationProposalResult",
    "ItemizationSession",
    "ItemizedSubjectItem",
    "VALID_ITEMIZATION_SESSION_STATUSES",
    "VALID_ITEMIZED_DECISION_ROLES",
    "VALID_ITEMIZED_ITEM_KINDS",
    "VALID_ITEMIZED_ITEM_STATUSES",
    "canonical_learning_subject_id",
    "ensure_itemization_home",
    "extract_itemized_candidates_from_learning_context",
    "extract_itemized_candidates_from_markdown_document",
    "itemization_paths",
    "list_itemized_subject_items",
    "load_itemization_session",
    "load_itemized_subject_item",
    "materialize_itemization_session",
    "normalize_itemized_decision_role",
    "persist_itemization_session",
    "stable_itemization_session_id",
    "stable_itemized_item_id",
]
