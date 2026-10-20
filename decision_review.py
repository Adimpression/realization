# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from decision_review_models import (
    DECISION_FRAME_STATUSES,
    DECISION_REVIEW_DECISION_ROLE_ORDER,
    DECISION_REVIEW_ITEM_STATUSES,
    DECISION_REVIEW_SCHEMA_VERSION,
    VALID_DECISION_REVIEW_DECISION_ROLES,
    DecisionFrame,
    DecisionReviewItem,
    _normalized_choice,
    _ordered_unique_texts,
    _stable_json_hash,
    _stable_record_id,
    normalize_decision_review_role,
    stable_decision_frame_id,
    stable_decision_review_item_id,
)
from id_generation import slugify
from learning_context import canonical_learning_subject_id
from learning_context_paths import decision_review_paths
from review_composition import ReviewItem
from semantic_text import collapse_ws


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_decision_review_home(root_path: Path, subject_id: str) -> dict[str, Path]:
    paths = decision_review_paths(root_path, subject_id)
    for key in ("root", "items"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def persist_decision_review(
    root_path: Path,
    frame: DecisionFrame,
    items: tuple[DecisionReviewItem, ...],
) -> Path:
    normalized_frame = DecisionFrame.from_dict(frame.to_dict())
    paths = ensure_decision_review_home(root_path, normalized_frame.subject_id)
    active_item_ids: set[str] = set()
    for item in items:
        normalized_item = DecisionReviewItem.from_dict(item.to_dict())
        active_item_ids.add(normalized_item.decision_review_item_id)
        _write_json(paths["items"] / f"{normalized_item.decision_review_item_id}.json", normalized_item.to_dict())
    for path in paths["items"].glob("*.json"):
        if path.stem not in active_item_ids:
            try:
                path.unlink()
            except FileNotFoundError:
                continue
    _write_json(paths["frame"], normalized_frame.to_dict())
    return paths["frame"]


def load_decision_frame(root_path: Path, subject_id: str) -> DecisionFrame:
    return DecisionFrame.from_dict(_read_json(decision_review_paths(root_path, subject_id)["frame"]))


def list_decision_review_items(root_path: Path, subject_id: str) -> tuple[DecisionReviewItem, ...]:
    items_root = decision_review_paths(root_path, subject_id)["items"]
    if not items_root.exists():
        return ()
    items: list[DecisionReviewItem] = []
    for path in sorted(items_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        item = DecisionReviewItem.from_dict(payload)
        if item.decision_review_item_id:
            items.append(item)
    return tuple(sorted(items, key=lambda item: (int(item.ordering or 0), item.decision_review_item_id)))


def decision_review_item_from_review_item(
    review_item: ReviewItem,
    *,
    decision_frame_id: str,
    decision_role: str = "",
    ordering: int = 0,
    build_epoch_ms: int = 0,
    existing: DecisionReviewItem | None = None,
) -> DecisionReviewItem:
    normalized_role = normalize_decision_review_role(
        decision_role
        or review_item.metadata.get("decision_role", "")
        or (existing.decision_role if existing is not None else "")
        or "supporting_evidence"
    )
    canonical_label = collapse_ws(str(review_item.metadata.get("canonical_label", ""))) or review_item.review_item_id
    metadata = dict(existing.metadata) if existing is not None else {}
    metadata.update(
        {
            "canonical_label": canonical_label,
            "semantic_kind": review_item.semantic_kind,
            "render_kind": review_item.render_kind,
            "source_unit_id": review_item.source_unit_id,
            "source_itemized_item_id": review_item.source_itemized_item_id,
        }
    )
    return DecisionReviewItem(
        decision_review_item_id=(
            existing.decision_review_item_id
            if existing is not None and collapse_ws(existing.decision_review_item_id)
            else stable_decision_review_item_id(
                decision_frame_id=decision_frame_id,
                review_item_id=review_item.review_item_id,
                decision_role=normalized_role,
            )
        ),
        review_item_id=review_item.review_item_id,
        decision_frame_id=decision_frame_id,
        decision_role=normalized_role,
        included=bool(review_item.included if existing is None else existing.included),
        ordering=max(0, int(ordering or (existing.ordering if existing is not None else 0))),
        child_decision_review_item_ids=existing.child_decision_review_item_ids if existing is not None else (),
        source_refs=_ordered_unique_texts((*review_item.source_refs, *(existing.source_refs if existing is not None else ()))),
        confidence=float(existing.confidence if existing is not None else 1.0),
        notes=existing.notes if existing is not None else "",
        status="active",
        created_at_epoch_ms=(existing.created_at_epoch_ms if existing is not None else max(0, int(build_epoch_ms or 0))),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata=metadata,
    )
