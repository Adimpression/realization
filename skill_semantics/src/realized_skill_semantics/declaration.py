"""Portable skill declaration schema and composition-right semantics."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


SKILL_SCHEMA_VERSION_V1 = "bssc_skill.v1"
SKILL_SCHEMA_VERSION_V2 = "bssc_skill.v2"
SKILL_SCHEMA_VERSIONS = {SKILL_SCHEMA_VERSION_V1, SKILL_SCHEMA_VERSION_V2}

__all__ = [
    "SKILL_SCHEMA_VERSION_V1",
    "SKILL_SCHEMA_VERSION_V2",
    "SKILL_SCHEMA_VERSIONS",
    "composition_binding_targets",
    "normalize_skill_schema_version",
]


def _collapse_ws(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [_collapse_ws(item) for item in value if _collapse_ws(item)]
    return [_collapse_ws(value)] if _collapse_ws(value) else []


def normalize_skill_schema_version(value: Any) -> str:
    """Normalize one explicit portable skill schema version."""
    normalized = _collapse_ws(value or SKILL_SCHEMA_VERSION_V1)
    if not normalized:
        return SKILL_SCHEMA_VERSION_V1
    if normalized not in SKILL_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported skill schema version: {normalized}")
    return normalized


def composition_binding_targets(
    declaration: Mapping[str, Any] | None,
) -> list[str]:
    """Project explicit composition rights into ordered target titles."""
    if not isinstance(declaration, Mapping):
        return []
    targets: list[str] = []
    for item in _string_list(declaration.get("composition_rights", [])):
        raw = _collapse_ws(item)
        if not raw:
            continue
        if raw == "*":
            return ["*"]
        if ":" in raw:
            prefix, target = raw.split(":", 1)
            if _collapse_ws(prefix).lower() not in {"skill", "invoke", "title"}:
                continue
            raw = _collapse_ws(target)
        if raw and raw not in targets:
            targets.append(raw)
    return targets
