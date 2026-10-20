# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from id_generation import slugify
from itemize import ItemizationSession, ItemizedSubjectItem
from learning_context import LearningContext, canonical_learning_subject_id, learning_context_home
from semantic_text import collapse_ws, semantic_chain_decomposition_components


REVIEW_COMPOSITION_SCHEMA_VERSION = "review_composition.v1"
REVIEW_ITEM_SEMANTIC_KIND_ORDER = (
    "equation",
    "claim",
    "multi_claim_paragraph",
    "table_like",
    "process",
    "decision_rule",
    "definition",
    "metric",
    "timeline",
    "risk_control",
    "figure_asset",
)
VALID_REVIEW_ITEM_SEMANTIC_KINDS = frozenset(REVIEW_ITEM_SEMANTIC_KIND_ORDER)
REVIEW_ITEM_RENDER_KIND_ORDER = (
    "paragraph",
    "equation_block",
    "claim_panel",
    "citation_callout",
    "typst_table",
    "decision_table",
    "flow_diagram",
    "dependency_diagram",
    "metric_card",
    "figure_with_caption",
    "appendix_note",
)
VALID_REVIEW_ITEM_RENDER_KINDS = frozenset(REVIEW_ITEM_RENDER_KIND_ORDER)
REVIEW_ITEM_EVIDENCE_MODE_ORDER = (
    "inline_handles",
    "source_basis_panel",
    "citation_box",
    "footnote_handles",
    "appendix_only",
)
VALID_REVIEW_ITEM_EVIDENCE_MODES = frozenset(REVIEW_ITEM_EVIDENCE_MODE_ORDER)
REVIEW_ITEM_TRANSFORM_MODE_ORDER = (
    "keep",
    "split",
    "merge",
    "rewrite_manual",
    "rewrite_llm_proposal",
    "convert_to_table",
    "convert_to_diagram",
    "convert_to_equation_legend",
)
VALID_REVIEW_ITEM_TRANSFORM_MODES = frozenset(REVIEW_ITEM_TRANSFORM_MODE_ORDER)
VALID_REVIEW_ITEM_STATUSES = frozenset({"active", "rejected"})
VALID_REVIEW_COMPOSITION_STATUSES = frozenset({"draft", "active", "approved", "archived"})
VALID_REVIEW_TRANSFORM_KINDS = frozenset({"split", "merge", "promote", "convert", "rewrite"})


def _ordered_unique_texts(items: list[Any] | tuple[Any, ...] | set[Any] | None) -> tuple[str, ...]:
    if not items:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _normalized_choice(value: Any, *, allowed: frozenset[str], default: str) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    return text if text in allowed else default


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _stable_review_record_id(prefix: str, *parts: Any) -> str:
    normalized_parts = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized_parts)
    slug = slugify(normalized_parts[-1] if normalized_parts else prefix, limit=48)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10] if rendered else "0" * 10
    return f"{prefix}_{slug}_{digest}"


def stable_review_item_id(*, subject_id: str, source_itemized_item_id: str, canonical_label: str) -> str:
    return _stable_review_record_id(
        "rvwitm",
        canonical_learning_subject_id(subject_id),
        source_itemized_item_id,
        canonical_label,
    )


def stable_child_review_item_id(*, parent_review_item_id: str, canonical_label: str) -> str:
    return _stable_review_record_id(
        "rvwchd",
        parent_review_item_id,
        canonical_label,
    )


def stable_review_composition_id(
    *,
    subject_id: str,
    learning_context_snapshot_hash: str,
    itemization_session_id: str,
) -> str:
    return _stable_review_record_id(
        "rvwcomp",
        canonical_learning_subject_id(subject_id),
        learning_context_snapshot_hash,
        itemization_session_id,
    )


def stable_review_transform_receipt_id(
    *,
    review_item_id: str,
    transform_kind: str,
    output_snapshot_hash: str,
) -> str:
    return _stable_review_record_id(
        "rvwrct",
        review_item_id,
        transform_kind,
        output_snapshot_hash,
    )


def _default_semantic_kind(item: ItemizedSubjectItem) -> str:
    kind = collapse_ws(item.item_kind)
    if kind == "equation":
        return "equation"
    if kind == "table_candidate":
        return "table_like"
    if kind == "metric":
        return "metric"
    if kind in {"figure_candidate", "diagram_candidate"}:
        return "figure_asset"
    if kind in {"glossary_term", "entity", "keyword", "variable"}:
        return "definition"
    return "claim"


def _default_render_kind(item: ItemizedSubjectItem, *, semantic_kind: str) -> str:
    kind = collapse_ws(item.item_kind)
    if semantic_kind == "equation":
        return "equation_block"
    if semantic_kind == "table_like":
        return "typst_table"
    if semantic_kind == "metric":
        return "metric_card"
    if kind == "diagram_candidate":
        return "flow_diagram"
    if semantic_kind == "figure_asset":
        return "figure_with_caption"
    if kind == "decision_role_candidate":
        return "citation_callout"
    return "paragraph"


def _default_evidence_mode(item: ItemizedSubjectItem) -> str:
    if item.item_kind in {"claim", "assumption", "decision_role_candidate", "xref_candidate", "citation_anchor"}:
        return "source_basis_panel"
    if item.item_kind in {"figure_candidate", "diagram_candidate", "table_candidate"}:
        return "citation_box"
    return "inline_handles"


def _default_transform_mode(item: ItemizedSubjectItem) -> str:
    if item.item_kind == "table_candidate":
        return "convert_to_table"
    if item.item_kind == "diagram_candidate":
        return "convert_to_diagram"
    if item.item_kind == "equation":
        return "convert_to_equation_legend"
    return "keep"


def review_item_split_labels(item: ReviewItem) -> tuple[str, ...]:
    metadata = dict(item.metadata or {})
    canonical_label = collapse_ws(str(metadata.get("canonical_label", ""))) or collapse_ws(item.notes)
    alias_values = metadata.get("aliases", ())
    aliases: tuple[str, ...]
    if isinstance(alias_values, (list, tuple, set)):
        aliases = _ordered_unique_texts(alias_values)
    else:
        aliases = ()
    alias_parts = tuple(
        alias
        for alias in aliases
        if alias
        and alias != canonical_label
        and alias != collapse_ws(item.notes)
        and not alias.endswith((".", "!", "?"))
    )
    if alias_parts:
        return alias_parts
    for candidate_text in (item.notes, canonical_label):
        candidates = semantic_chain_decomposition_components(candidate_text)
        if len(candidates) > 1:
            return tuple(
                label
                for label in (
                    collapse_ws(candidate)
                    for candidate in candidates
                )
                if label and label != canonical_label
            )
    for delimiter in (" / ", ";", " and "):
        if delimiter in canonical_label:
            parts = tuple(
                part
                for part in (collapse_ws(piece) for piece in canonical_label.split(delimiter))
                if part and part != canonical_label
            )
            if len(parts) > 1:
                return parts
    return ()


@dataclass(frozen=True)
class ReviewItem:
    review_item_id: str
    subject_id: str
    source_itemized_item_id: str
    source_unit_id: str = ""
    parent_review_item_id: str = ""
    semantic_kind: str = "claim"
    render_kind: str = "paragraph"
    evidence_mode: str = "inline_handles"
    transform_mode: str = "keep"
    included: bool = False
    ordering: int = 0
    child_review_item_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    notes: str = ""
    status: str = "active"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = REVIEW_COMPOSITION_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "review_item_id": self.review_item_id,
            "subject_id": self.subject_id,
            "source_itemized_item_id": self.source_itemized_item_id,
            "source_unit_id": self.source_unit_id,
            "parent_review_item_id": self.parent_review_item_id,
            "semantic_kind": self.semantic_kind,
            "render_kind": self.render_kind,
            "evidence_mode": self.evidence_mode,
            "transform_mode": self.transform_mode,
            "included": bool(self.included),
            "ordering": int(self.ordering),
            "child_review_item_ids": list(self.child_review_item_ids),
            "source_refs": list(self.source_refs),
            "notes": self.notes,
            "status": self.status,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReviewItem":
        return cls(
            review_item_id=collapse_ws(str(payload.get("review_item_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            source_itemized_item_id=collapse_ws(str(payload.get("source_itemized_item_id", ""))),
            source_unit_id=collapse_ws(str(payload.get("source_unit_id", ""))),
            parent_review_item_id=collapse_ws(str(payload.get("parent_review_item_id", ""))),
            semantic_kind=_normalized_choice(
                payload.get("semantic_kind", "claim"),
                allowed=VALID_REVIEW_ITEM_SEMANTIC_KINDS,
                default="claim",
            ),
            render_kind=_normalized_choice(
                payload.get("render_kind", "paragraph"),
                allowed=VALID_REVIEW_ITEM_RENDER_KINDS,
                default="paragraph",
            ),
            evidence_mode=_normalized_choice(
                payload.get("evidence_mode", "inline_handles"),
                allowed=VALID_REVIEW_ITEM_EVIDENCE_MODES,
                default="inline_handles",
            ),
            transform_mode=_normalized_choice(
                payload.get("transform_mode", "keep"),
                allowed=VALID_REVIEW_ITEM_TRANSFORM_MODES,
                default="keep",
            ),
            included=bool(payload.get("included", False)),
            ordering=max(0, int(payload.get("ordering", 0) or 0)),
            child_review_item_ids=_ordered_unique_texts(payload.get("child_review_item_ids", [])),
            source_refs=_ordered_unique_texts(payload.get("source_refs", [])),
            notes=str(payload.get("notes", "")),
            status=_normalized_choice(
                payload.get("status", "active"),
                allowed=VALID_REVIEW_ITEM_STATUSES,
                default="active",
            ),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
            schema_version=collapse_ws(str(payload.get("schema_version", REVIEW_COMPOSITION_SCHEMA_VERSION))) or REVIEW_COMPOSITION_SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class ReviewComposition:
    review_composition_id: str
    subject_id: str
    itemization_session_id: str
    learning_context_snapshot_hash: str
    root_review_item_ids: tuple[str, ...] = ()
    included_review_item_ids: tuple[str, ...] = ()
    excluded_review_item_ids: tuple[str, ...] = ()
    status: str = "draft"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = REVIEW_COMPOSITION_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "review_composition_id": self.review_composition_id,
            "subject_id": self.subject_id,
            "itemization_session_id": self.itemization_session_id,
            "learning_context_snapshot_hash": self.learning_context_snapshot_hash,
            "root_review_item_ids": list(self.root_review_item_ids),
            "included_review_item_ids": list(self.included_review_item_ids),
            "excluded_review_item_ids": list(self.excluded_review_item_ids),
            "status": self.status,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReviewComposition":
        return cls(
            review_composition_id=collapse_ws(str(payload.get("review_composition_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            itemization_session_id=collapse_ws(str(payload.get("itemization_session_id", ""))),
            learning_context_snapshot_hash=collapse_ws(str(payload.get("learning_context_snapshot_hash", ""))),
            root_review_item_ids=_ordered_unique_texts(payload.get("root_review_item_ids", [])),
            included_review_item_ids=_ordered_unique_texts(payload.get("included_review_item_ids", [])),
            excluded_review_item_ids=_ordered_unique_texts(payload.get("excluded_review_item_ids", [])),
            status=_normalized_choice(
                payload.get("status", "draft"),
                allowed=VALID_REVIEW_COMPOSITION_STATUSES,
                default="draft",
            ),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
            schema_version=collapse_ws(str(payload.get("schema_version", REVIEW_COMPOSITION_SCHEMA_VERSION))) or REVIEW_COMPOSITION_SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class ReviewTransformReceipt:
    receipt_id: str
    review_item_id: str
    review_composition_id: str
    transform_kind: str
    input_snapshot_hash: str
    output_snapshot_hash: str
    operator: str
    notes: str = ""
    created_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = REVIEW_COMPOSITION_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "review_item_id": self.review_item_id,
            "review_composition_id": self.review_composition_id,
            "transform_kind": self.transform_kind,
            "input_snapshot_hash": self.input_snapshot_hash,
            "output_snapshot_hash": self.output_snapshot_hash,
            "operator": self.operator,
            "notes": self.notes,
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReviewTransformReceipt":
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            receipt_id=collapse_ws(str(payload.get("receipt_id", ""))),
            review_item_id=collapse_ws(str(payload.get("review_item_id", ""))),
            review_composition_id=collapse_ws(str(payload.get("review_composition_id", ""))),
            transform_kind=_normalized_choice(
                payload.get("transform_kind", "split"),
                allowed=VALID_REVIEW_TRANSFORM_KINDS,
                default="split",
            ),
            input_snapshot_hash=collapse_ws(str(payload.get("input_snapshot_hash", ""))),
            output_snapshot_hash=collapse_ws(str(payload.get("output_snapshot_hash", ""))),
            operator=collapse_ws(str(payload.get("operator", ""))),
            notes=str(payload.get("notes", "")),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            metadata={str(key): value for key, value in metadata.items()},
            schema_version=collapse_ws(str(payload.get("schema_version", REVIEW_COMPOSITION_SCHEMA_VERSION))) or REVIEW_COMPOSITION_SCHEMA_VERSION,
        )


def review_composition_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    home = learning_context_home(root_path, subject_id) / "review_composition"
    return {
        "root": home,
        "composition": home / "composition.json",
        "items": home / "items",
        "receipts": home / "receipts",
    }


def ensure_review_composition_home(root_path: Path, subject_id: str) -> dict[str, Path]:
    paths = review_composition_paths(root_path, subject_id)
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


def persist_review_composition(
    root_path: Path,
    composition: ReviewComposition,
    items: tuple[ReviewItem, ...],
) -> Path:
    normalized_composition = ReviewComposition.from_dict(composition.to_dict())
    paths = ensure_review_composition_home(root_path, normalized_composition.subject_id)
    active_item_ids: set[str] = set()
    for item in items:
        normalized_item = ReviewItem.from_dict(item.to_dict())
        active_item_ids.add(normalized_item.review_item_id)
        _write_json(paths["items"] / f"{normalized_item.review_item_id}.json", normalized_item.to_dict())
    for path in paths["items"].glob("*.json"):
        if path.stem not in active_item_ids:
            try:
                path.unlink()
            except FileNotFoundError:
                continue
    _write_json(paths["composition"], normalized_composition.to_dict())
    return paths["composition"]


def load_review_composition(root_path: Path, subject_id: str) -> ReviewComposition:
    return ReviewComposition.from_dict(_read_json(review_composition_paths(root_path, subject_id)["composition"]))


def list_review_items(root_path: Path, subject_id: str) -> tuple[ReviewItem, ...]:
    items_root = review_composition_paths(root_path, subject_id)["items"]
    if not items_root.exists():
        return ()
    items: list[ReviewItem] = []
    for path in sorted(items_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        item = ReviewItem.from_dict(payload)
        if item.review_item_id:
            items.append(item)
    return tuple(
        sorted(
            items,
            key=lambda item: (
                collapse_ws(item.parent_review_item_id),
                int(item.ordering or 0),
                item.review_item_id,
            ),
        )
    )


def persist_review_transform_receipt(
    root_path: Path,
    subject_id: str,
    receipt: ReviewTransformReceipt,
) -> Path:
    paths = ensure_review_composition_home(root_path, subject_id)
    normalized = ReviewTransformReceipt.from_dict(receipt.to_dict())
    target = paths["receipts"] / f"{normalized.receipt_id}.json"
    _write_json(target, normalized.to_dict())
    return target


def list_review_transform_receipts(root_path: Path, subject_id: str) -> tuple[ReviewTransformReceipt, ...]:
    receipts_root = review_composition_paths(root_path, subject_id)["receipts"]
    if not receipts_root.exists():
        return ()
    receipts: list[ReviewTransformReceipt] = []
    for path in sorted(receipts_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        receipt = ReviewTransformReceipt.from_dict(payload)
        if receipt.receipt_id:
            receipts.append(receipt)
    return tuple(
        sorted(
            receipts,
            key=lambda item: (
                int(item.created_at_epoch_ms or 0),
                item.receipt_id,
            ),
        )
    )


def review_item_from_itemized_item(
    item: ItemizedSubjectItem,
    *,
    ordering: int,
    included: bool,
    build_epoch_ms: int = 0,
    existing: ReviewItem | None = None,
) -> ReviewItem:
    semantic_kind = _default_semantic_kind(item)
    render_kind = _default_render_kind(item, semantic_kind=semantic_kind)
    evidence_mode = _default_evidence_mode(item)
    transform_mode = _default_transform_mode(item)
    if existing is not None:
        semantic_kind = existing.semantic_kind or semantic_kind
        render_kind = existing.render_kind or render_kind
        evidence_mode = existing.evidence_mode or evidence_mode
        transform_mode = existing.transform_mode or transform_mode
    metadata = dict(existing.metadata) if existing is not None else {}
    if item.metadata:
        metadata.update(item.metadata)
    metadata.setdefault("canonical_label", item.canonical_label)
    if item.aliases:
        metadata.setdefault("aliases", list(item.aliases))
    status = "rejected" if collapse_ws(item.status) == "rejected" else "active"
    return ReviewItem(
        review_item_id=(
            existing.review_item_id
            if existing is not None and collapse_ws(existing.review_item_id)
            else stable_review_item_id(
                subject_id=item.subject_id,
                source_itemized_item_id=item.itemized_item_id,
                canonical_label=item.canonical_label,
            )
        ),
        subject_id=canonical_learning_subject_id(item.subject_id),
        source_itemized_item_id=item.itemized_item_id,
        source_unit_id=collapse_ws(item.source_unit_id),
        parent_review_item_id=existing.parent_review_item_id if existing is not None else "",
        semantic_kind=semantic_kind,
        render_kind=render_kind,
        evidence_mode=evidence_mode,
        transform_mode=transform_mode,
        included=bool(included and status != "rejected"),
        ordering=max(0, int(ordering)),
        child_review_item_ids=existing.child_review_item_ids if existing is not None else (),
        source_refs=_ordered_unique_texts((*item.source_refs, *(existing.source_refs if existing is not None else ()))),
        notes=existing.notes if existing is not None else "",
        status=status,
        created_at_epoch_ms=(existing.created_at_epoch_ms if existing is not None else max(0, int(build_epoch_ms or 0))),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata=metadata,
    )


def review_composition_from_itemization(
    context: LearningContext,
    session: ItemizationSession,
    items: tuple[ItemizedSubjectItem, ...],
    *,
    existing: ReviewComposition | None = None,
    existing_items: tuple[ReviewItem, ...] = (),
    build_epoch_ms: int = 0,
    status: str = "draft",
) -> tuple[ReviewComposition, tuple[ReviewItem, ...]]:
    active_items = tuple(item for item in items if collapse_ws(item.itemized_item_id))
    active_items_by_source_id = {
        collapse_ws(item.itemized_item_id): item
        for item in active_items
        if collapse_ws(item.itemized_item_id)
    }
    existing_by_source_id = {
        collapse_ws(item.source_itemized_item_id): item
        for item in existing_items
        if collapse_ws(item.source_itemized_item_id) and not collapse_ws(item.parent_review_item_id)
    }
    ordered_source_item_ids: list[str] = []
    seen_source_item_ids: set[str] = set()
    for existing_item in sorted(existing_items, key=lambda item: (item.ordering, item.review_item_id)):
        source_item_id = collapse_ws(existing_item.source_itemized_item_id)
        if not source_item_id or source_item_id not in active_items_by_source_id or source_item_id in seen_source_item_ids:
            continue
        ordered_source_item_ids.append(source_item_id)
        seen_source_item_ids.add(source_item_id)
    for item in active_items:
        source_item_id = collapse_ws(item.itemized_item_id)
        if not source_item_id or source_item_id in seen_source_item_ids:
            continue
        ordered_source_item_ids.append(source_item_id)
        seen_source_item_ids.add(source_item_id)
    built_items: list[ReviewItem] = []
    for ordering, source_item_id in enumerate(ordered_source_item_ids, start=1):
        item = active_items_by_source_id[source_item_id]
        include_default = collapse_ws(item.status) != "rejected"
        existing_item = existing_by_source_id.get(source_item_id)
        built_items.append(
            review_item_from_itemized_item(
                item,
                ordering=ordering,
                included=(existing_item.included if existing_item is not None else include_default),
                build_epoch_ms=build_epoch_ms,
                existing=existing_item,
            )
        )
    preserved_child_items = tuple(
        item
        for item in existing_items
        if collapse_ws(item.parent_review_item_id)
        and collapse_ws(item.status) != "rejected"
    )
    built_items_tuple = tuple(
        sorted(
            (*built_items, *preserved_child_items),
            key=lambda item: (
                collapse_ws(item.parent_review_item_id),
                int(item.ordering or 0),
                item.review_item_id,
            ),
        )
    )
    active_items = tuple(item for item in built_items_tuple if collapse_ws(item.status) != "rejected")
    root_review_item_ids = tuple(
        item.review_item_id
        for item in active_items
        if not collapse_ws(item.parent_review_item_id)
    )
    included_review_item_ids = tuple(item.review_item_id for item in active_items if item.included)
    excluded_review_item_ids = tuple(item.review_item_id for item in active_items if not item.included)
    metadata = dict(existing.metadata) if existing is not None else {}
    metadata.update(
        {
            "seed_mode": "all_non_rejected_items",
            "itemization_session_id": session.itemization_session_id,
            "item_count": len(built_items_tuple),
            "included_item_count": len(included_review_item_ids),
        }
    )
    composition = ReviewComposition(
        review_composition_id=(
            existing.review_composition_id
            if existing is not None and collapse_ws(existing.review_composition_id)
            else stable_review_composition_id(
                subject_id=context.subject_id,
                learning_context_snapshot_hash=context.content_hash(),
                itemization_session_id=session.itemization_session_id,
            )
        ),
        subject_id=context.subject_id,
        itemization_session_id=session.itemization_session_id,
        learning_context_snapshot_hash=context.content_hash(),
        root_review_item_ids=root_review_item_ids,
        included_review_item_ids=included_review_item_ids,
        excluded_review_item_ids=excluded_review_item_ids,
        status=_normalized_choice(status, allowed=VALID_REVIEW_COMPOSITION_STATUSES, default="draft"),
        created_at_epoch_ms=(
            existing.created_at_epoch_ms
            if existing is not None and int(existing.created_at_epoch_ms or 0) > 0
            else max(0, int(build_epoch_ms or 0))
        ),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata=metadata,
    )
    return composition, built_items_tuple


def included_review_composition_unit_ids(items: tuple[ReviewItem, ...]) -> tuple[str, ...]:
    return _ordered_unique_texts(
        item.source_unit_id
        for item in included_leaf_review_items(items)
        if collapse_ws(item.source_unit_id)
    )


def review_composition_with_items(
    composition: ReviewComposition,
    items: tuple[ReviewItem, ...],
    *,
    build_epoch_ms: int = 0,
    status: str | None = None,
) -> ReviewComposition:
    normalized_items = tuple(
        sorted(
            items,
            key=lambda item: (
                collapse_ws(item.parent_review_item_id),
                int(item.ordering or 0),
                item.review_item_id,
            ),
        )
    )
    active_items = tuple(item for item in normalized_items if collapse_ws(item.status) != "rejected")
    metadata = dict(composition.metadata)
    metadata.update(
        {
            "itemization_session_id": composition.itemization_session_id,
            "item_count": len(active_items),
            "included_item_count": sum(1 for item in active_items if item.included),
        }
    )
    return ReviewComposition(
        review_composition_id=composition.review_composition_id,
        subject_id=composition.subject_id,
        itemization_session_id=composition.itemization_session_id,
        learning_context_snapshot_hash=composition.learning_context_snapshot_hash,
        root_review_item_ids=tuple(
            item.review_item_id
            for item in active_items
            if not collapse_ws(item.parent_review_item_id)
        ),
        included_review_item_ids=tuple(item.review_item_id for item in active_items if item.included),
        excluded_review_item_ids=tuple(item.review_item_id for item in active_items if not item.included),
        status=_normalized_choice(
            status if status is not None else composition.status,
            allowed=VALID_REVIEW_COMPOSITION_STATUSES,
            default="draft",
        ),
        created_at_epoch_ms=composition.created_at_epoch_ms,
        updated_at_epoch_ms=max(0, int(build_epoch_ms or composition.updated_at_epoch_ms or 0)),
        metadata=metadata,
        schema_version=composition.schema_version or REVIEW_COMPOSITION_SCHEMA_VERSION,
    )


def active_review_items(items: tuple[ReviewItem, ...]) -> tuple[ReviewItem, ...]:
    return tuple(item for item in items if collapse_ws(item.status) != "rejected")


def review_item_by_id(items: tuple[ReviewItem, ...], review_item_id: str) -> ReviewItem | None:
    normalized_id = collapse_ws(review_item_id)
    if not normalized_id:
        return None
    for item in items:
        if collapse_ws(item.review_item_id) == normalized_id:
            return item
    return None


def review_item_children(items: tuple[ReviewItem, ...], parent_review_item_id: str) -> tuple[ReviewItem, ...]:
    normalized_parent_id = collapse_ws(parent_review_item_id)
    return tuple(
        sorted(
            (
                item
                for item in active_review_items(items)
                if collapse_ws(item.parent_review_item_id) == normalized_parent_id
            ),
            key=lambda item: (int(item.ordering or 0), item.review_item_id),
        )
    )


def flatten_review_item_tree(items: tuple[ReviewItem, ...]) -> tuple[tuple[ReviewItem, int], ...]:
    rows: list[tuple[ReviewItem, int]] = []
    active_items = active_review_items(items)
    children_by_parent: dict[str, list[ReviewItem]] = {}
    for item in active_items:
        parent_id = collapse_ws(item.parent_review_item_id)
        children_by_parent.setdefault(parent_id, []).append(item)
    for siblings in children_by_parent.values():
        siblings.sort(key=lambda item: (int(item.ordering or 0), item.review_item_id))

    def _walk(parent_id: str, depth: int) -> None:
        for child in children_by_parent.get(parent_id, ()):
            rows.append((child, depth))
            _walk(child.review_item_id, depth + 1)

    _walk("", 0)
    return tuple(rows)


def included_leaf_review_items(items: tuple[ReviewItem, ...]) -> tuple[ReviewItem, ...]:
    active_item_ids = {
        collapse_ws(item.review_item_id)
        for item in active_review_items(items)
        if collapse_ws(item.review_item_id)
    }
    return tuple(
        item
        for item in active_review_items(items)
        if item.included
        and not any(
            collapse_ws(child_id) in active_item_ids
            for child_id in item.child_review_item_ids
        )
    )


def split_review_item_into_children(
    composition: ReviewComposition,
    items: tuple[ReviewItem, ...],
    *,
    review_item_id: str,
    build_epoch_ms: int = 0,
) -> tuple[ReviewComposition, tuple[ReviewItem, ...], ReviewItem, tuple[ReviewItem, ...]] | None:
    selected = review_item_by_id(items, review_item_id)
    if selected is None or collapse_ws(selected.status) == "rejected":
        return None
    if any(collapse_ws(child_id) for child_id in selected.child_review_item_ids):
        return None
    split_labels = review_item_split_labels(selected)
    if len(split_labels) < 2:
        return None
    now_epoch_ms = max(0, int(build_epoch_ms or 0))
    selected_label = collapse_ws(str(selected.metadata.get("canonical_label", ""))) or selected.review_item_id
    child_items: list[ReviewItem] = []
    for ordering, label in enumerate(split_labels, start=1):
        child_item_id = stable_child_review_item_id(
            parent_review_item_id=selected.review_item_id,
            canonical_label=label,
        )
        child_items.append(
            ReviewItem(
                review_item_id=child_item_id,
                subject_id=selected.subject_id,
                source_itemized_item_id=selected.source_itemized_item_id,
                source_unit_id=selected.source_unit_id,
                parent_review_item_id=selected.review_item_id,
                semantic_kind=selected.semantic_kind,
                render_kind=selected.render_kind,
                evidence_mode=selected.evidence_mode,
                transform_mode="keep",
                included=bool(selected.included),
                ordering=ordering,
                child_review_item_ids=(),
                source_refs=selected.source_refs,
                notes=selected.notes,
                status="active",
                created_at_epoch_ms=now_epoch_ms,
                updated_at_epoch_ms=now_epoch_ms,
                metadata={
                    **dict(selected.metadata),
                    "canonical_label": label,
                    "origin": "review_split",
                    "split_from_review_item_id": selected.review_item_id,
                    "split_from_label": selected_label,
                },
            )
        )
    updated_items: list[ReviewItem] = []
    for item in items:
        if collapse_ws(item.review_item_id) != collapse_ws(selected.review_item_id):
            updated_items.append(item)
            continue
        metadata = dict(item.metadata)
        metadata["split_into_review_item_ids"] = tuple(child.review_item_id for child in child_items)
        updated_items.append(
            replace(
                item,
                included=False,
                transform_mode="split",
                child_review_item_ids=tuple(child.review_item_id for child in child_items),
                updated_at_epoch_ms=now_epoch_ms,
                metadata=metadata,
            )
        )
    updated_items.extend(child_items)
    updated_items_tuple = tuple(updated_items)
    updated_composition = review_composition_with_items(
        composition,
        updated_items_tuple,
        build_epoch_ms=now_epoch_ms,
    )
    updated_parent = review_item_by_id(updated_items_tuple, selected.review_item_id)
    if updated_parent is None:
        return None
    return updated_composition, updated_items_tuple, updated_parent, tuple(child_items)


def merge_review_item_with_next_sibling(
    composition: ReviewComposition,
    items: tuple[ReviewItem, ...],
    *,
    review_item_id: str,
    build_epoch_ms: int = 0,
) -> tuple[ReviewComposition, tuple[ReviewItem, ...], ReviewItem, tuple[ReviewItem, ...]] | None:
    selected = review_item_by_id(items, review_item_id)
    if selected is None or collapse_ws(selected.status) == "rejected":
        return None
    siblings = review_item_children(items, selected.parent_review_item_id)
    try:
        current_index = next(
            index
            for index, item in enumerate(siblings)
            if collapse_ws(item.review_item_id) == collapse_ws(selected.review_item_id)
        )
    except StopIteration:
        return None
    if current_index >= len(siblings) - 1:
        return None
    sibling = siblings[current_index + 1]
    now_epoch_ms = max(0, int(build_epoch_ms or 0))
    selected_label = collapse_ws(str(selected.metadata.get("canonical_label", ""))) or selected.review_item_id
    sibling_label = collapse_ws(str(sibling.metadata.get("canonical_label", ""))) or sibling.review_item_id
    merged_label = f"{selected_label} / {sibling_label}"
    merged_review_item = ReviewItem(
        review_item_id=stable_child_review_item_id(
            parent_review_item_id=selected.parent_review_item_id or "root",
            canonical_label=merged_label,
        ),
        subject_id=selected.subject_id,
        source_itemized_item_id=(
            selected.source_itemized_item_id
            if collapse_ws(selected.source_itemized_item_id) == collapse_ws(sibling.source_itemized_item_id)
            else ""
        ),
        source_unit_id=(
            selected.source_unit_id
            if collapse_ws(selected.source_unit_id) == collapse_ws(sibling.source_unit_id)
            else ""
        ),
        parent_review_item_id=selected.parent_review_item_id,
        semantic_kind=selected.semantic_kind,
        render_kind=selected.render_kind,
        evidence_mode=selected.evidence_mode,
        transform_mode="merge",
        included=bool(selected.included or sibling.included),
        ordering=int(selected.ordering or 0),
        child_review_item_ids=(),
        source_refs=_ordered_unique_texts((*selected.source_refs, *sibling.source_refs)),
        notes=collapse_ws("\n".join(part for part in (selected.notes, sibling.notes) if collapse_ws(part))),
        status="active",
        created_at_epoch_ms=now_epoch_ms,
        updated_at_epoch_ms=now_epoch_ms,
        metadata={
            **dict(selected.metadata),
            "canonical_label": merged_label,
            "origin": "review_merge",
            "merged_review_item_ids": (
                selected.review_item_id,
                sibling.review_item_id,
            ),
        },
    )
    merged_source_ids = {
        collapse_ws(selected.review_item_id),
        collapse_ws(sibling.review_item_id),
    }
    updated_items: list[ReviewItem] = []
    for item in items:
        item_id = collapse_ws(item.review_item_id)
        if item_id in merged_source_ids:
            metadata = dict(item.metadata)
            metadata["merged_into_review_item_id"] = merged_review_item.review_item_id
            updated_items.append(
                replace(
                    item,
                    included=False,
                    status="rejected",
                    updated_at_epoch_ms=now_epoch_ms,
                    metadata=metadata,
                )
            )
            continue
        updated_items.append(item)
    updated_items.append(merged_review_item)
    active_siblings = tuple(
        item
        for item in updated_items
        if collapse_ws(item.parent_review_item_id) == collapse_ws(selected.parent_review_item_id)
        and collapse_ws(item.status) != "rejected"
    )
    resequenced_items: list[ReviewItem] = []
    sibling_order_by_id = {
        collapse_ws(item.review_item_id): index
        for index, item in enumerate(sorted(active_siblings, key=lambda item: (int(item.ordering or 0), item.review_item_id)), start=1)
    }
    for item in updated_items:
        item_id = collapse_ws(item.review_item_id)
        if item_id in sibling_order_by_id and int(item.ordering or 0) != sibling_order_by_id[item_id]:
            resequenced_items.append(replace(item, ordering=sibling_order_by_id[item_id], updated_at_epoch_ms=now_epoch_ms))
        else:
            resequenced_items.append(item)
    updated_items_tuple = tuple(resequenced_items)
    updated_composition = review_composition_with_items(
        composition,
        updated_items_tuple,
        build_epoch_ms=now_epoch_ms,
    )
    updated_merged_item = review_item_by_id(updated_items_tuple, merged_review_item.review_item_id)
    if updated_merged_item is None:
        return None
    return updated_composition, updated_items_tuple, updated_merged_item, (selected, sibling)


def promote_review_item_to_root(
    composition: ReviewComposition,
    items: tuple[ReviewItem, ...],
    *,
    review_item_id: str,
    build_epoch_ms: int = 0,
) -> tuple[ReviewComposition, tuple[ReviewItem, ...], ReviewItem] | None:
    selected = review_item_by_id(items, review_item_id)
    if selected is None or not collapse_ws(selected.parent_review_item_id):
        return None
    now_epoch_ms = max(0, int(build_epoch_ms or 0))
    parent = review_item_by_id(items, selected.parent_review_item_id)
    remaining_child_ids = tuple(
        child_id
        for child_id in ((parent.child_review_item_ids if parent is not None else ()))
        if collapse_ws(child_id) and collapse_ws(child_id) != collapse_ws(selected.review_item_id)
    )
    max_root_ordering = max(
        (int(item.ordering or 0) for item in active_review_items(items) if not collapse_ws(item.parent_review_item_id)),
        default=0,
    )
    updated_items: list[ReviewItem] = []
    for item in items:
        item_id = collapse_ws(item.review_item_id)
        if item_id == collapse_ws(selected.review_item_id):
            updated_items.append(
                replace(
                    item,
                    parent_review_item_id="",
                    ordering=max_root_ordering + 1,
                    updated_at_epoch_ms=now_epoch_ms,
                )
            )
            continue
        if parent is not None and item_id == collapse_ws(parent.review_item_id):
            metadata = dict(item.metadata)
            metadata["promoted_child_review_item_id"] = selected.review_item_id
            parent_status = item.status if remaining_child_ids else "rejected"
            updated_items.append(
                replace(
                    item,
                    child_review_item_ids=remaining_child_ids,
                    status=parent_status,
                    included=(item.included if remaining_child_ids else False),
                    updated_at_epoch_ms=now_epoch_ms,
                    metadata=metadata,
                )
            )
            continue
        updated_items.append(item)
    updated_items_tuple = tuple(updated_items)
    updated_composition = review_composition_with_items(
        composition,
        updated_items_tuple,
        build_epoch_ms=now_epoch_ms,
    )
    updated_selected = review_item_by_id(updated_items_tuple, selected.review_item_id)
    if updated_selected is None:
        return None
    return updated_composition, updated_items_tuple, updated_selected
