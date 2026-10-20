# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from id_generation import slugify
from itemize import ItemizedSubjectItem, normalize_itemized_decision_role
from learning_context import canonical_learning_subject_id, learning_context_home
from semantic_text import collapse_ws


DECISION_REVIEW_CONSTRUCT_SCHEMA_VERSION = "decision_review_constructs.v1"
TRANSFORMATION_CONSTRUCT_SORT_ORDER: tuple[str, ...] = (
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
VALID_TRANSFORMATION_CONSTRUCT_SORT_KINDS = frozenset(TRANSFORMATION_CONSTRUCT_SORT_ORDER)
VALID_TRANSFORMATION_CONSTRUCT_STATUSES = frozenset({"candidate", "accepted", "rejected"})

_EXPLICIT_ROLE_TO_SORT_KIND: dict[str, str] = {
    "actor": "actor",
    "objective": "objective",
    "capability": "capability",
    "dependency": "dependency",
    "constraint": "constraint",
    "boundary": "boundary",
    "state": "state",
    "transition": "transition",
    "decision": "decision",
}
_SORT_KIND_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("actor", ("actor", "user", "citizen", "passenger", "commuter", "student", "teacher", "operator", "staff", "vendor", "agency", "department", "hospital", "school", "ministry", "authority")),
    ("objective", ("objective", "goal", "outcome", "target", "improve", "reduce", "increase", "ensure", "achieve", "modernize", "digitize", "rollout")),
    ("capability", ("capability", "enable", "support", "ability", "automate", "automation", "ticketing", "alerting", "dispense", "synchronize", "audit", "monitor")),
    ("dependency", ("dependency", "depends on", "requires", "prerequisite", "upstream", "downstream", "integration", "network", "identity", "approval")),
    ("constraint", ("constraint", "must", "cannot", "prohibited", "only", "within", "threshold", "compliance", "regulation", "budget", "deadline")),
    ("boundary", ("boundary", "across", "cross", "between", "regional", "district", "national", "channel", "provider", "interface")),
    ("state", ("state", "current", "target", "as-is", "to-be", "existing", "future", "manual", "digital", "ready")),
    ("transition", ("transition", "route", "path", "move from", "start with", "then", "phase", "migrate", "upgrade", "sequence")),
    ("decision", ("decision", "choose", "option", "alternative", "recommend", "strategy", "plan")),
)


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


def normalize_transformation_construct_sort_kind(value: Any) -> str:
    return _normalized_choice(
        value,
        allowed=VALID_TRANSFORMATION_CONSTRUCT_SORT_KINDS,
        default="actor",
    )


def next_transformation_construct_sort_kind(current: str) -> str:
    normalized_current = normalize_transformation_construct_sort_kind(current)
    try:
        current_index = TRANSFORMATION_CONSTRUCT_SORT_ORDER.index(normalized_current)
    except ValueError:
        return TRANSFORMATION_CONSTRUCT_SORT_ORDER[0]
    return TRANSFORMATION_CONSTRUCT_SORT_ORDER[(current_index + 1) % len(TRANSFORMATION_CONSTRUCT_SORT_ORDER)]


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _stable_record_id(prefix: str, *parts: Any) -> str:
    normalized_parts = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized_parts)
    slug = slugify(normalized_parts[-1] if normalized_parts else prefix, limit=48)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10] if rendered else "0" * 10
    return f"{prefix}_{slug}_{digest}"


def stable_transformation_construct_candidate_id(
    *,
    subject_id: str,
    itemized_item_id: str,
    sort_kind: str,
    canonical_label: str,
    disambiguator: str = "",
) -> str:
    return _stable_record_id(
        "trcnd",
        canonical_learning_subject_id(subject_id),
        collapse_ws(itemized_item_id),
        normalize_transformation_construct_sort_kind(sort_kind),
        collapse_ws(canonical_label),
        collapse_ws(disambiguator),
    )


@dataclass(frozen=True)
class TransformationConstructCandidate:
    construct_candidate_id: str
    subject_id: str
    itemized_item_id: str
    review_item_id: str = ""
    sort_kind: str = "actor"
    canonical_label: str = ""
    summary: str = ""
    source_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    status: str = "candidate"
    notes: str = ""
    relation_hints: dict[str, Any] = field(default_factory=dict)
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    schema_version: str = DECISION_REVIEW_CONSTRUCT_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "construct_candidate_id": self.construct_candidate_id,
            "subject_id": self.subject_id,
            "itemized_item_id": self.itemized_item_id,
            "review_item_id": self.review_item_id,
            "sort_kind": self.sort_kind,
            "canonical_label": self.canonical_label,
            "summary": self.summary,
            "source_refs": list(self.source_refs),
            "confidence": float(self.confidence),
            "status": self.status,
            "notes": self.notes,
            "relation_hints": dict(self.relation_hints),
            "created_at_epoch_ms": int(self.created_at_epoch_ms or 0),
            "updated_at_epoch_ms": int(self.updated_at_epoch_ms or 0),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransformationConstructCandidate":
        try:
            confidence = float(payload.get("confidence", 0.0))
        except Exception:
            confidence = 0.0
        confidence = min(1.0, max(0.0, confidence))
        return cls(
            construct_candidate_id=collapse_ws(str(payload.get("construct_candidate_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            itemized_item_id=collapse_ws(str(payload.get("itemized_item_id", ""))),
            review_item_id=collapse_ws(str(payload.get("review_item_id", ""))),
            sort_kind=normalize_transformation_construct_sort_kind(payload.get("sort_kind", "actor")),
            canonical_label=collapse_ws(str(payload.get("canonical_label", ""))),
            summary=str(payload.get("summary", "")),
            source_refs=_ordered_unique_texts(payload.get("source_refs", [])),
            confidence=confidence,
            status=_normalized_choice(
                payload.get("status", "candidate"),
                allowed=VALID_TRANSFORMATION_CONSTRUCT_STATUSES,
                default="candidate",
            ),
            notes=str(payload.get("notes", "")),
            relation_hints=dict(payload.get("relation_hints", {})),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            schema_version=collapse_ws(str(payload.get("schema_version", DECISION_REVIEW_CONSTRUCT_SCHEMA_VERSION)))
            or DECISION_REVIEW_CONSTRUCT_SCHEMA_VERSION,
        )


def transformation_construct_candidate_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    home = learning_context_home(root_path, subject_id) / "decision_review_constructs"
    return {
        "root": home,
        "candidates": home / "candidates",
    }


def ensure_transformation_construct_candidate_home(root_path: Path, subject_id: str) -> dict[str, Path]:
    paths = transformation_construct_candidate_paths(root_path, subject_id)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["candidates"].mkdir(parents=True, exist_ok=True)
    return paths


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def persist_transformation_construct_candidates(
    root_path: Path,
    subject_id: str,
    candidates: tuple[TransformationConstructCandidate, ...],
) -> Path:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    paths = ensure_transformation_construct_candidate_home(root_path, normalized_subject_id)
    persisted_ids: set[str] = set()
    for candidate in candidates:
        normalized = TransformationConstructCandidate.from_dict(candidate.to_dict())
        persisted_ids.add(normalized.construct_candidate_id)
        _write_json(paths["candidates"] / f"{normalized.construct_candidate_id}.json", normalized.to_dict())
    for path in paths["candidates"].glob("*.json"):
        if path.stem not in persisted_ids:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    return paths["candidates"]


def load_transformation_construct_candidate(
    root_path: Path,
    subject_id: str,
    construct_candidate_id: str,
) -> TransformationConstructCandidate:
    path = transformation_construct_candidate_paths(root_path, subject_id)["candidates"] / f"{collapse_ws(construct_candidate_id)}.json"
    return TransformationConstructCandidate.from_dict(_read_json(path))


def list_transformation_construct_candidates(root_path: Path, subject_id: str) -> tuple[TransformationConstructCandidate, ...]:
    candidates_root = transformation_construct_candidate_paths(root_path, subject_id)["candidates"]
    if not candidates_root.exists():
        return ()
    candidates: list[TransformationConstructCandidate] = []
    for path in sorted(candidates_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        candidate = TransformationConstructCandidate.from_dict(payload)
        if candidate.construct_candidate_id:
            candidates.append(candidate)
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.sort_kind,
                candidate.canonical_label.casefold(),
                candidate.construct_candidate_id,
            ),
        )
    )


def _search_text(item: ItemizedSubjectItem) -> str:
    return " ".join(
        part
        for part in (
            item.canonical_label,
            item.summary,
            " ".join(item.aliases),
            " ".join(f"{collapse_ws(str(key))} {collapse_ws(str(value))}" for key, value in sorted(item.metadata.items())),
        )
        if collapse_ws(part)
    ).casefold()


def _state_polarity(item: ItemizedSubjectItem, text: str) -> str:
    if any(marker in text for marker in ("target", "future", "desired", "to-be", "goal state")):
        return "target"
    if any(marker in text for marker in ("current", "existing", "today", "as-is")):
        return "current"
    if collapse_ws(item.item_kind) == "assumption":
        return "current"
    return ""


def deterministic_transformation_construct_candidates_from_itemized_item(
    item: ItemizedSubjectItem,
    *,
    build_epoch_ms: int = 0,
    review_item_id: str = "",
) -> tuple[TransformationConstructCandidate, ...]:
    now_epoch_ms = max(0, int(build_epoch_ms or 0))
    search_text = _search_text(item)
    sort_kinds: list[str] = []
    relation_hints_by_sort: dict[str, dict[str, Any]] = {}

    explicit_role = _EXPLICIT_ROLE_TO_SORT_KIND.get(
        normalize_itemized_decision_role(item.metadata.get("decision_role", "")),
        "",
    )
    if collapse_ws(item.item_kind) == "decision_role_candidate" and explicit_role:
        # Itemize already classified the candidate. Respect that role as the
        # primary deterministic DST projection instead of cloning the same
        # label across generic marker-matched construct kinds.
        sort_kinds.append(explicit_role)
    else:
        if explicit_role:
            sort_kinds.append(explicit_role)
        for sort_kind, markers in _SORT_KIND_MARKERS:
            if any(marker in search_text for marker in markers):
                sort_kinds.append(sort_kind)
    if "state" in sort_kinds:
        polarity = _state_polarity(item, search_text)
        if polarity:
            relation_hints_by_sort["state"] = {"state_polarity": polarity}

    ordered_unique_sorts = tuple(
        dict.fromkeys(
            normalize_transformation_construct_sort_kind(sort_kind)
            for sort_kind in sort_kinds
            if collapse_ws(sort_kind)
        )
    )
    if not ordered_unique_sorts:
        return ()

    candidates: list[TransformationConstructCandidate] = []
    explicit_confidence = 0.92 if explicit_role else 0.0
    for sort_kind in ordered_unique_sorts:
        confidence = max(
            explicit_confidence if sort_kind == explicit_role and explicit_role else 0.0,
            min(0.9, max(0.45, float(item.confidence or 0.0))),
        )
        candidates.append(
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=item.subject_id,
                    itemized_item_id=item.itemized_item_id,
                    sort_kind=sort_kind,
                    canonical_label=item.canonical_label,
                ),
                subject_id=item.subject_id,
                itemized_item_id=item.itemized_item_id,
                review_item_id=collapse_ws(review_item_id),
                sort_kind=sort_kind,
                canonical_label=item.canonical_label,
                summary=item.summary,
                source_refs=item.source_refs,
                confidence=confidence,
                status="candidate",
                notes="",
                relation_hints=relation_hints_by_sort.get(sort_kind, {}),
                created_at_epoch_ms=now_epoch_ms,
                updated_at_epoch_ms=now_epoch_ms,
            )
        )
    return tuple(candidates)
