# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from id_generation import slugify
from learning_context_paths import canonical_learning_subject_id
from semantic_text import collapse_ws


DECISION_REVIEW_SCHEMA_VERSION = "decision_review.v1"
DECISION_FRAME_STATUSES = frozenset({"draft", "active", "approved", "archived"})
DECISION_REVIEW_ITEM_STATUSES = frozenset({"active", "rejected"})
DECISION_REVIEW_DECISION_ROLE_ORDER = (
    "actor",
    "objective",
    "capability",
    "dependency",
    "constraint",
    "boundary",
    "current_state",
    "target_state",
    "transition_candidate",
    "decision_candidate",
    "assignment_candidate",
    "risk_statement",
    "supporting_evidence",
)
VALID_DECISION_REVIEW_DECISION_ROLES = frozenset(DECISION_REVIEW_DECISION_ROLE_ORDER)


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


def normalize_decision_review_role(value: Any) -> str:
    return _normalized_choice(
        value,
        allowed=VALID_DECISION_REVIEW_DECISION_ROLES,
        default="supporting_evidence",
    )


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _stable_record_id(prefix: str, *parts: Any) -> str:
    normalized_parts = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized_parts)
    slug = slugify(normalized_parts[-1] if normalized_parts else prefix, limit=48)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10] if rendered else "0" * 10
    return f"{prefix}_{slug}_{digest}"


def stable_decision_frame_id(*, subject_id: str, question: str, publication_id: str = "") -> str:
    return _stable_record_id(
        "decfrm",
        canonical_learning_subject_id(subject_id),
        publication_id,
        question,
    )


def stable_decision_review_item_id(
    *,
    decision_frame_id: str,
    review_item_id: str,
    decision_role: str,
) -> str:
    return _stable_record_id(
        "decitm",
        decision_frame_id,
        review_item_id,
        decision_role,
    )


@dataclass(frozen=True)
class DecisionFrame:
    decision_frame_id: str
    subject_id: str
    publication_id: str = ""
    question: str = ""
    decision_mode: str = "decision_aid"
    current_state_ids: tuple[str, ...] = ()
    target_state_ids: tuple[str, ...] = ()
    primary_objective_ids: tuple[str, ...] = ()
    scope_boundary_ids: tuple[str, ...] = ()
    status: str = "draft"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = DECISION_REVIEW_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_frame_id": self.decision_frame_id,
            "subject_id": self.subject_id,
            "publication_id": self.publication_id,
            "question": self.question,
            "decision_mode": self.decision_mode,
            "current_state_ids": list(self.current_state_ids),
            "target_state_ids": list(self.target_state_ids),
            "primary_objective_ids": list(self.primary_objective_ids),
            "scope_boundary_ids": list(self.scope_boundary_ids),
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
    def from_dict(cls, payload: dict[str, Any]) -> "DecisionFrame":
        return cls(
            decision_frame_id=collapse_ws(str(payload.get("decision_frame_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            publication_id=collapse_ws(str(payload.get("publication_id", ""))),
            question=str(payload.get("question", "")),
            decision_mode=collapse_ws(str(payload.get("decision_mode", ""))) or "decision_aid",
            current_state_ids=_ordered_unique_texts(payload.get("current_state_ids", [])),
            target_state_ids=_ordered_unique_texts(payload.get("target_state_ids", [])),
            primary_objective_ids=_ordered_unique_texts(payload.get("primary_objective_ids", [])),
            scope_boundary_ids=_ordered_unique_texts(payload.get("scope_boundary_ids", [])),
            status=_normalized_choice(
                payload.get("status", "draft"),
                allowed=DECISION_FRAME_STATUSES,
                default="draft",
            ),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
            schema_version=collapse_ws(str(payload.get("schema_version", DECISION_REVIEW_SCHEMA_VERSION))) or DECISION_REVIEW_SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class DecisionReviewItem:
    decision_review_item_id: str
    review_item_id: str
    decision_frame_id: str
    decision_role: str = "supporting_evidence"
    included: bool = True
    ordering: int = 0
    child_decision_review_item_ids: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    notes: str = ""
    status: str = "active"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = DECISION_REVIEW_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision_review_item_id": self.decision_review_item_id,
            "review_item_id": self.review_item_id,
            "decision_frame_id": self.decision_frame_id,
            "decision_role": self.decision_role,
            "included": bool(self.included),
            "ordering": int(self.ordering),
            "child_decision_review_item_ids": list(self.child_decision_review_item_ids),
            "source_refs": list(self.source_refs),
            "confidence": float(self.confidence),
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
    def from_dict(cls, payload: dict[str, Any]) -> "DecisionReviewItem":
        return cls(
            decision_review_item_id=collapse_ws(str(payload.get("decision_review_item_id", ""))),
            review_item_id=collapse_ws(str(payload.get("review_item_id", ""))),
            decision_frame_id=collapse_ws(str(payload.get("decision_frame_id", ""))),
            decision_role=normalize_decision_review_role(payload.get("decision_role", "supporting_evidence")),
            included=bool(payload.get("included", True)),
            ordering=max(0, int(payload.get("ordering", 0) or 0)),
            child_decision_review_item_ids=_ordered_unique_texts(payload.get("child_decision_review_item_ids", [])),
            source_refs=_ordered_unique_texts(payload.get("source_refs", [])),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            notes=str(payload.get("notes", "")),
            status=_normalized_choice(
                payload.get("status", "active"),
                allowed=DECISION_REVIEW_ITEM_STATUSES,
                default="active",
            ),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
            schema_version=collapse_ws(str(payload.get("schema_version", DECISION_REVIEW_SCHEMA_VERSION))) or DECISION_REVIEW_SCHEMA_VERSION,
        )
