# See MODULES.md for the repository module map before editing.
"""Compatibility facade for package-owned data-governance rules."""

from __future__ import annotations

from realized_core_governance import data as _data
from realized_core_governance.data import (
    DATA_CLASS_CHOICES,
    allowed_data_classes_from_governance_context,
    ensure_governed_data_access,
    normalize_data_class,
    normalize_data_class_list,
    normalize_named_query_registry,
    query_is_read_only,
)


_string_list = _data._string_list
collapse_ws = _data.collapse_ws

__all__ = [
    "DATA_CLASS_CHOICES",
    "allowed_data_classes_from_governance_context",
    "ensure_governed_data_access",
    "normalize_data_class",
    "normalize_data_class_list",
    "normalize_named_query_registry",
    "query_is_read_only",
]
