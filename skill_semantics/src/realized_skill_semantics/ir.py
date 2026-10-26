"""Portable canonical skill IR values and identity metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from realized_core_semantics.values import json_safe


__all__ = [
    "CanonicalSkillIR",
    "derived_skill_family_metadata_from_title",
    "normalized_skill_aliases",
    "normalized_skill_family_metadata",
]


def _collapse_ws(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


def _normalize_notation_key(value: Any) -> str:
    return " ".join(str(value).strip().split()).casefold()


def _normalized_string_list(values: Any) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    if not isinstance(values, list):
        return normalized
    for item in values:
        text = _collapse_ws(item)
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _derived_title_aliases(title: str) -> list[str]:
    parts = [
        _collapse_ws(part)
        for part in str(title).split(" / ")
        if _collapse_ws(part)
    ]
    if len(parts) <= 1:
        return []
    return parts[1:]


def normalized_skill_aliases(value: Any, *, title: str = "") -> list[str]:
    """Return stable explicit and title-derived aliases for one skill."""
    aliases: list[str] = []
    seen: set[str] = set()
    for candidate in _normalized_string_list(value) + _derived_title_aliases(title):
        if candidate == _collapse_ws(title) or candidate in seen:
            continue
        seen.add(candidate)
        aliases.append(candidate)
    return aliases


def derived_skill_family_metadata_from_title(title: str) -> dict[str, str]:
    """Derive conservative family metadata from a numbered skill title."""
    canonical_title = _collapse_ws(str(title).split(" / ", 1)[0])
    match = re.match(
        r"^(?P<label>.+?)\s+(?P<ordinal>\d{1,3})\s+[—-]\s+(?P<variant>.+)$",
        canonical_title,
    )
    if not match:
        return {}
    label = _collapse_ws(match.group("label"))
    ordinal = _collapse_ws(match.group("ordinal"))
    variant = _collapse_ws(match.group("variant"))
    if not label:
        return {}
    return {
        "label": label,
        "key": _normalize_notation_key(label),
        "ordinal": ordinal,
        "variant": variant,
    }


def normalized_skill_family_metadata(
    value: Any,
    *,
    title: str = "",
) -> dict[str, str]:
    """Return explicit or conservatively title-derived skill-family metadata."""
    metadata = dict(value) if isinstance(value, Mapping) else {}
    label = _collapse_ws(metadata.get("label", metadata.get("family", "")))
    key = _collapse_ws(metadata.get("key", ""))
    ordinal = _collapse_ws(metadata.get("ordinal", ""))
    variant = _collapse_ws(metadata.get("variant", ""))
    if not label and isinstance(value, str):
        label = _collapse_ws(value)
    if not label:
        return derived_skill_family_metadata_from_title(title)
    normalized = {"label": label, "key": key or _normalize_notation_key(label)}
    if ordinal:
        normalized["ordinal"] = ordinal
    if variant:
        normalized["variant"] = variant
    return normalized


@dataclass(frozen=True)
class CanonicalSkillIR:
    """Portable canonical projection of one skill's semantic surfaces."""

    artifact_id: str
    title: str
    schema: str
    kind: str
    declaration: dict[str, Any]
    lifecycle: dict[str, Any]
    runtime_package_reference: dict[str, Any]
    normalization: dict[str, Any]
    aliases: list[str]
    family: dict[str, str]
    compatibility: dict[str, Any]
    hosting_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Project this immutable IR value into a JSON-compatible dictionary."""
        return json_safe(self)
