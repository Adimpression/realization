"""Private normalization helpers that keep the substrate dependency-free."""

from __future__ import annotations

from dataclasses import is_dataclass
from enum import Enum
import re
from typing import Any


_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def collapse_ws(value: Any) -> str:
    """Match the repository's established control-character and whitespace normalization."""
    without_controls = _CONTROL_CHARACTERS.sub(" ", str(value))
    return _WHITESPACE.sub(" ", without_controls).strip()


def json_safe(value: Any) -> Any:
    """Match the repository's established recursively JSON-safe projection."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", errors="replace")
    if is_dataclass(value):
        return {key: json_safe(item) for key, item in value.__dict__.items()}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    return value
