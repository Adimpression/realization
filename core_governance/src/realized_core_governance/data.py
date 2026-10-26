"""Data classification and supplied-context access rules."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._normalization import collapse_ws


DATA_CLASS_CHOICES = (
    "public",
    "internal",
    "sensitive",
    "regulated",
    "secret",
    "audit_only",
    "derived",
)

__all__ = [
    "DATA_CLASS_CHOICES",
    "allowed_data_classes_from_governance_context",
    "ensure_governed_data_access",
    "normalize_data_class",
    "normalize_data_class_list",
    "normalize_named_query_registry",
    "query_is_read_only",
]


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [
            collapse_ws(str(item))
            for item in value
            if collapse_ws(str(item))
        ]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def normalize_data_class(value: Any, *, default: str = "public") -> str:
    """Normalize one data-class label into the governed vocabulary."""
    normalized = (
        collapse_ws(str(value or default))
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )
    if normalized in DATA_CLASS_CHOICES:
        return normalized
    return default


def normalize_data_class_list(value: Any) -> list[str]:
    """Normalize and stably deduplicate data-class labels."""
    normalized: list[str] = []
    for item in _string_list(value):
        data_class = normalize_data_class(item)
        if data_class not in normalized:
            normalized.append(data_class)
    return normalized


def allowed_data_classes_from_governance_context(
    governance_context: Mapping[str, Any] | None,
) -> list[str]:
    """Project allowed data classes from an already supplied runtime context."""
    if not isinstance(governance_context, Mapping):
        return []
    normalized: list[str] = []
    grants = governance_context.get("grants", [])
    if isinstance(grants, list):
        for item in grants:
            if not isinstance(item, Mapping):
                continue
            for data_class in normalize_data_class_list(
                item.get("data_classes_touched", [])
            ):
                if data_class not in normalized:
                    normalized.append(data_class)
    declaration = governance_context.get("declaration", {})
    if isinstance(declaration, Mapping):
        for data_class in normalize_data_class_list(
            declaration.get("data_classes_touched", [])
        ):
            if data_class not in normalized:
                normalized.append(data_class)
    return normalized


def ensure_governed_data_access(
    governance_context: Mapping[str, Any] | None,
    *,
    requested_data_classes: list[str] | None,
    operation: str,
) -> tuple[bool, str]:
    """Check requested classes against the supplied declaration and grants."""
    requested = normalize_data_class_list(requested_data_classes or [])
    if not requested:
        return True, ""
    allowed = allowed_data_classes_from_governance_context(governance_context)
    if not allowed:
        return (
            False,
            f"Governed data access for {collapse_ws(operation)} requires declared "
            f"data classes {', '.join(requested)}, but runtime grants declare none.",
        )
    missing = [item for item in requested if item not in allowed]
    if not missing:
        return True, ""
    return (
        False,
        f"Governed data access for {collapse_ws(operation)} requires data classes "
        f"{', '.join(missing)}, but runtime grants allow {', '.join(allowed)}.",
    )


def normalize_named_query_registry(value: Any) -> dict[str, dict[str, Any]]:
    """Normalize declared named queries without executing or discovering them."""
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for raw_name, raw_spec in value.items():
        name = collapse_ws(str(raw_name))
        if not name or not isinstance(raw_spec, Mapping):
            continue
        sql = collapse_ws(str(raw_spec.get("sql", "")))
        if not sql:
            continue
        parameter_order = (
            [
                collapse_ws(str(item))
                for item in raw_spec.get("parameter_order", [])
                if collapse_ws(str(item))
            ]
            if isinstance(raw_spec.get("parameter_order", []), list)
            else []
        )
        normalized[name] = {
            "sql": sql,
            "parameter_order": parameter_order,
            "data_class": normalize_data_class(
                raw_spec.get("data_class", "internal"),
                default="internal",
            ),
        }
    return normalized


def query_is_read_only(sql: str) -> bool:
    """Apply the historical lexical read-only predicate to one query."""
    normalized = collapse_ws(sql).lower()
    if not normalized:
        return False
    if normalized.startswith("select ") or normalized.startswith("with "):
        forbidden_fragments = (
            " insert ",
            " update ",
            " delete ",
            " alter ",
            " drop ",
            " create ",
            " replace ",
            " pragma ",
            " attach ",
            " detach ",
        )
        return not any(
            fragment in f" {normalized} " for fragment in forbidden_fragments
        )
    return False
