"""Dependency-light semantic value projection helpers."""

from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    """Return the current UTC time in the repository's canonical format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_safe(value: Any) -> Any:
    """Return a recursively JSON-compatible projection of a runtime value."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if is_dataclass(value):
        return {key: json_safe(val) for key, val in value.__dict__.items()}
    if isinstance(value, dict):
        return {str(key): json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return value


__all__ = ["json_safe", "utc_now"]
