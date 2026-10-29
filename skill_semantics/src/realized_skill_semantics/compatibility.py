"""Portable compatibility-envelope normalization for skill representations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws


def _normalized_adapter_entry(value: Any) -> dict[str, Any]:
    adapter = dict(value) if isinstance(value, Mapping) else {}
    format_name = collapse_ws(str(adapter.get("format", "")))
    if not format_name:
        return {}
    normalized: dict[str, Any] = {"format": format_name}
    direction = collapse_ws(str(adapter.get("direction", "")))
    if direction:
        normalized["direction"] = direction
    for key in ("name", "surface", "title", "path", "entrypoint"):
        text = collapse_ws(str(adapter.get(key, "")))
        if text:
            normalized[key] = text
    metadata = (
        dict(adapter.get("metadata", {}))
        if isinstance(adapter.get("metadata", {}), Mapping)
        else {}
    )
    if metadata:
        normalized["metadata"] = metadata
    return normalized


def normalized_skill_compatibility_payload(value: Any) -> dict[str, Any]:
    """Normalize an optional compatibility envelope into an adapter list."""
    if not isinstance(value, Mapping):
        return {}
    raw_mapping = dict(value)
    adapters_raw = raw_mapping.get("adapters")
    if isinstance(adapters_raw, list):
        adapters = [
            normalized
            for item in adapters_raw
            if (normalized := _normalized_adapter_entry(item))
        ]
    else:
        single = _normalized_adapter_entry(raw_mapping)
        adapters = [single] if single else []
    if not adapters:
        return {}
    return {"adapters": adapters}


__all__ = ["normalized_skill_compatibility_payload"]
