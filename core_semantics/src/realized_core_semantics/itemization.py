"""Dependency-light values for subject itemization."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Mapping

from .identifiers import canonical_learning_subject_id
from .semantic_text import collapse_ws


ITEMIZATION_SCHEMA_VERSION = "itemization.v1"
VALID_ITEMIZED_ITEM_KINDS = {
    "glossary_term",
    "keyword",
    "entity",
    "claim",
    "assumption",
    "equation",
    "variable",
    "metric",
    "table_candidate",
    "figure_candidate",
    "diagram_candidate",
    "citation_anchor",
    "xref_candidate",
    "decision_role_candidate",
}
VALID_ITEMIZED_ITEM_STATUSES = {"candidate", "promoted", "rejected", "merged", "split"}
VALID_ITEMIZATION_SESSION_STATUSES = {"draft", "active", "archived"}
VALID_ITEMIZED_DECISION_ROLES: tuple[str, ...] = (
    "",
    "actor",
    "objective",
    "capability",
    "dependency",
    "constraint",
    "boundary",
    "state",
    "transition",
    "decision",
)
_VALID_ITEMIZED_DECISION_ROLE_SET = set(VALID_ITEMIZED_DECISION_ROLES)


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


def _normalized_choice(value: Any, *, allowed: set[str], default: str) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    return text if text in allowed else default


def normalize_itemized_decision_role(value: Any) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    return text if text in _VALID_ITEMIZED_DECISION_ROLE_SET else ""


def _normalized_itemized_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = dict(metadata or {})
    decision_role = normalize_itemized_decision_role(normalized.get("decision_role", ""))
    if decision_role:
        normalized["decision_role"] = decision_role
    else:
        normalized.pop("decision_role", None)
    return normalized


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ItemizedSubjectItem:
    itemized_item_id: str
    subject_id: str
    item_kind: str
    canonical_label: str
    source_unit_id: str = ""
    aliases: tuple[str, ...] = ()
    summary: str = ""
    source_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    status: str = "candidate"
    linked_item_ids: tuple[str, ...] = ()
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    schema_version: str = ITEMIZATION_SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "itemized_item_id": self.itemized_item_id,
            "subject_id": self.subject_id,
            "item_kind": self.item_kind,
            "canonical_label": self.canonical_label,
            "source_unit_id": self.source_unit_id,
            "aliases": list(self.aliases),
            "summary": self.summary,
            "source_refs": list(self.source_refs),
            "confidence": float(self.confidence),
            "status": self.status,
            "linked_item_ids": list(self.linked_item_ids),
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
    def from_dict(cls, payload: dict[str, Any]) -> "ItemizedSubjectItem":
        try:
            confidence = float(payload.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        confidence = min(1.0, max(0.0, confidence))
        try:
            created_at_epoch_ms = max(0, int(payload.get("created_at_epoch_ms", 0) or 0))
        except Exception:
            created_at_epoch_ms = 0
        try:
            updated_at_epoch_ms = max(0, int(payload.get("updated_at_epoch_ms", 0) or 0))
        except Exception:
            updated_at_epoch_ms = 0
        return cls(
            itemized_item_id=collapse_ws(str(payload.get("itemized_item_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            item_kind=_normalized_choice(
                payload.get("item_kind", "entity"),
                allowed=VALID_ITEMIZED_ITEM_KINDS,
                default="entity",
            ),
            canonical_label=collapse_ws(str(payload.get("canonical_label", ""))),
            source_unit_id=collapse_ws(str(payload.get("source_unit_id", ""))),
            aliases=_ordered_unique_texts(payload.get("aliases", [])),
            summary=str(payload.get("summary", "")),
            source_refs=_ordered_unique_texts(payload.get("source_refs", [])),
            confidence=confidence,
            status=_normalized_choice(
                payload.get("status", "candidate"),
                allowed=VALID_ITEMIZED_ITEM_STATUSES,
                default="candidate",
            ),
            linked_item_ids=_ordered_unique_texts(payload.get("linked_item_ids", [])),
            created_at_epoch_ms=created_at_epoch_ms,
            updated_at_epoch_ms=updated_at_epoch_ms,
            schema_version=collapse_ws(str(payload.get("schema_version", ITEMIZATION_SCHEMA_VERSION))) or ITEMIZATION_SCHEMA_VERSION,
            metadata=_normalized_itemized_metadata(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class ItemizationSession:
    itemization_session_id: str
    subject_id: str
    learning_context_snapshot_hash: str
    item_ids: tuple[str, ...] = ()
    status: str = "active"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": ITEMIZATION_SCHEMA_VERSION,
            "itemization_session_id": self.itemization_session_id,
            "subject_id": self.subject_id,
            "learning_context_snapshot_hash": self.learning_context_snapshot_hash,
            "item_ids": list(self.item_ids),
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
    def from_dict(cls, payload: dict[str, Any]) -> "ItemizationSession":
        try:
            created_at_epoch_ms = max(0, int(payload.get("created_at_epoch_ms", 0) or 0))
        except Exception:
            created_at_epoch_ms = 0
        try:
            updated_at_epoch_ms = max(0, int(payload.get("updated_at_epoch_ms", 0) or 0))
        except Exception:
            updated_at_epoch_ms = 0
        return cls(
            itemization_session_id=collapse_ws(str(payload.get("itemization_session_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            learning_context_snapshot_hash=collapse_ws(str(payload.get("learning_context_snapshot_hash", ""))),
            item_ids=_ordered_unique_texts(payload.get("item_ids", [])),
            status=_normalized_choice(
                payload.get("status", "active"),
                allowed=VALID_ITEMIZATION_SESSION_STATUSES,
                default="active",
            ),
            created_at_epoch_ms=created_at_epoch_ms,
            updated_at_epoch_ms=updated_at_epoch_ms,
            metadata=dict(payload.get("metadata", {})),
        )


__all__ = [
    "ITEMIZATION_SCHEMA_VERSION",
    "ItemizationSession",
    "ItemizedSubjectItem",
    "VALID_ITEMIZATION_SESSION_STATUSES",
    "VALID_ITEMIZED_DECISION_ROLES",
    "VALID_ITEMIZED_ITEM_KINDS",
    "VALID_ITEMIZED_ITEM_STATUSES",
    "normalize_itemized_decision_role",
]
