"""Repository-location support for source-tree validation tools."""

from __future__ import annotations

import os
from pathlib import Path


REPOSITORY_ROOT_ENV = "REALIZED_VALIDATION_REPOSITORY_ROOT"


def validation_repository_root() -> Path:
    """Locate the repository whose trial and validation entrypoints are audited."""

    override = str(os.getenv(REPOSITORY_ROOT_ENV, "")).strip()
    if override:
        return Path(override).expanduser().resolve()

    source_candidate = Path(__file__).resolve().parents[3]
    if (source_candidate / "pyproject.toml").is_file() and (
        source_candidate / "trials"
    ).is_dir():
        return source_candidate

    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "trials"
        ).is_dir():
            return candidate
    return source_candidate


__all__ = ["REPOSITORY_ROOT_ENV", "validation_repository_root"]
