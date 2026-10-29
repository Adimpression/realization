"""Canonical transformation-construct candidate persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workstation.subject.core.learning_context import canonical_learning_subject_id, learning_context_home
from realized_core_semantics.semantic_text import collapse_ws
from realized_core_semantics.transformation_constructs import (
    DECISION_REVIEW_CONSTRUCT_SCHEMA_VERSION,
    TRANSFORMATION_CONSTRUCT_SORT_ORDER,
    VALID_TRANSFORMATION_CONSTRUCT_SORT_KINDS,
    VALID_TRANSFORMATION_CONSTRUCT_STATUSES,
    TransformationConstructCandidate,
    deterministic_transformation_construct_candidates_from_itemized_item,
    next_transformation_construct_sort_kind,
    normalize_transformation_construct_sort_kind,
    stable_transformation_construct_candidate_id,
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
