"""Validation invariants for persisted subject itemization sessions."""

from __future__ import annotations

from collections import Counter

from realized_core_semantics.itemization import (
    ItemizationSession,
    ItemizedSubjectItem,
    VALID_ITEMIZED_ITEM_KINDS,
    VALID_ITEMIZED_ITEM_STATUSES,
    VALID_ITEMIZATION_SESSION_STATUSES,
    normalize_itemized_decision_role,
)
from realized_core_semantics.semantic_text import collapse_ws


def validate_itemization_session(
    session: ItemizationSession,
    *,
    items: tuple[ItemizedSubjectItem, ...],
    learning_context_snapshot_hash: str = "",
) -> dict[str, object]:
    errors: list[str] = []
    item_ids = [collapse_ws(item.itemized_item_id) for item in items if collapse_ws(item.itemized_item_id)]
    if len(item_ids) != len(set(item_ids)):
        errors.append("every ItemizedSubjectItem id must be unique")
    session_item_ids = [collapse_ws(item_id) for item_id in session.item_ids if collapse_ws(item_id)]
    if len(session_item_ids) != len(set(session_item_ids)):
        errors.append("itemization session item_ids must be unique")
    item_by_id = {
        collapse_ws(item.itemized_item_id): item
        for item in items
        if collapse_ws(item.itemized_item_id)
    }
    missing_item_ids = [item_id for item_id in session_item_ids if item_id not in item_by_id]
    if missing_item_ids:
        errors.append(
            "itemization session references missing items: "
            + ", ".join(missing_item_ids[:6])
            + (" ..." if len(missing_item_ids) > 6 else "")
        )
    extra_item_ids = [item_id for item_id in item_by_id if item_id not in set(session_item_ids)]
    if extra_item_ids:
        errors.append(
            "persisted itemization items are missing from the session: "
            + ", ".join(extra_item_ids[:6])
            + (" ..." if len(extra_item_ids) > 6 else "")
        )
    if session.status not in VALID_ITEMIZATION_SESSION_STATUSES:
        errors.append(f"itemization session uses unsupported status {session.status}")

    duplicate_keys: dict[tuple[str, str, str], int] = {}
    item_kind_counts = Counter()
    for item in items:
        if item.subject_id != session.subject_id:
            errors.append(
                f"item {item.itemized_item_id} belongs to {item.subject_id}, expected {session.subject_id}"
            )
        if item.item_kind not in VALID_ITEMIZED_ITEM_KINDS:
            errors.append(f"item {item.itemized_item_id} uses unsupported item_kind {item.item_kind}")
        if item.status not in VALID_ITEMIZED_ITEM_STATUSES:
            errors.append(f"item {item.itemized_item_id} uses unsupported status {item.status}")
        if not collapse_ws(item.canonical_label):
            errors.append(f"item {item.itemized_item_id} must declare canonical_label")
        if not item.source_refs:
            errors.append(f"item {item.itemized_item_id} must declare at least one source_ref")
        if item.status == "merged" and not item.linked_item_ids:
            errors.append(f"merged item {item.itemized_item_id} must retain linked_item_ids provenance")
        decision_role = normalize_itemized_decision_role(item.metadata.get("decision_role", ""))
        if collapse_ws(str(item.metadata.get("decision_role", ""))) and not decision_role:
            errors.append(
                f"item {item.itemized_item_id} uses unsupported decision_role {item.metadata.get('decision_role')}"
            )
        duplicate_key = (
            collapse_ws(item.item_kind).casefold(),
            collapse_ws(item.canonical_label).casefold(),
            decision_role.casefold(),
        )
        duplicate_keys[duplicate_key] = duplicate_keys.get(duplicate_key, 0) + 1
        item_kind_counts[item.item_kind] += 1
    duplicate_labels = [
        key
        for key, count in duplicate_keys.items()
        if key[0] and key[1] and count > 1
    ]
    if duplicate_labels:
        errors.append("itemization contains duplicate item kind/label pairs")

    normalized_snapshot_hash = collapse_ws(learning_context_snapshot_hash)
    if normalized_snapshot_hash:
        snapshot_status = (
            "current"
            if collapse_ws(session.learning_context_snapshot_hash) == normalized_snapshot_hash
            else "stale"
        )
    else:
        snapshot_status = "unknown"

    return {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "snapshot_status": snapshot_status,
        "item_count": len(items),
        "item_kind_counts": dict(sorted(item_kind_counts.items())),
        "subject_id": session.subject_id,
        "itemization_session_id": session.itemization_session_id,
        "learning_context_snapshot_hash": session.learning_context_snapshot_hash,
    }


__all__ = ["validate_itemization_session"]
