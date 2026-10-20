# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from pathlib import Path

from id_generation import slugify
from semantic_text import collapse_ws


def canonical_learning_subject_id(text: str) -> str:
    normalized = slugify(collapse_ws(text), limit=64)
    return normalized or "subject"


def learning_corpus_root(root_path: Path) -> Path:
    return Path(root_path).expanduser().resolve() / "corpus"


def resolve_learning_context_root(
    *,
    source_path: Path | None = None,
    override_root: Path | None = None,
) -> Path:
    if override_root is not None:
        return Path(override_root).expanduser().resolve()
    env_override = collapse_ws(str(os.getenv("LEARNING_CONTEXT_ROOT", "")))
    if env_override:
        return Path(env_override).expanduser().resolve()
    if source_path is not None:
        return Path(source_path).expanduser().resolve().parent
    return Path.cwd().resolve()


def learning_context_home(root_path: Path, subject_id: str) -> Path:
    return learning_corpus_root(root_path) / canonical_learning_subject_id(subject_id)


def decision_review_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    home = learning_context_home(root_path, subject_id) / "decision_review"
    return {
        "root": home,
        "frame": home / "frame.json",
        "items": home / "items",
    }


def learning_source_bundle_root(root_path: Path, subject_id: str, source_id: str) -> Path:
    return learning_context_paths(root_path, subject_id)["sources"] / collapse_ws(source_id)


def learning_context_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    home = learning_context_home(root_path, subject_id)
    return {
        "root": home,
        "context": home / "context.json",
        "subject_typ": home / "subject.typ",
        "subject_md": home / "subject.md",
        "sources": home / "sources",
        "deltas": home / "deltas",
        "imports": home / "imports",
        "derived_root": home / "derived",
        "derived_skills": home / "derived" / "skills",
        "derived_exports": home / "derived" / "exports",
        "receipts": home / "receipts",
        "indexes": home / "indexes",
        "aliases_index": home / "indexes" / "aliases.json",
        "units_index": home / "indexes" / "units.json",
        "imports_index": home / "indexes" / "imports.json",
    }


def ensure_learning_context_home(root_path: Path, subject_id: str) -> dict[str, Path]:
    paths = learning_context_paths(root_path, subject_id)
    for key in (
        "root",
        "sources",
        "deltas",
        "imports",
        "derived_root",
        "derived_skills",
        "derived_exports",
        "receipts",
        "indexes",
    ):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths
