# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from semantic_text import collapse_ws

DATA_CLASS_CHOICES = (
    "public",
    "internal",
    "sensitive",
    "regulated",
    "secret",
    "audit_only",
    "derived",
)


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [collapse_ws(str(item)) for item in value if collapse_ws(str(item))]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def normalize_data_class(value: Any, *, default: str = "public") -> str:
    """
    High Level Purpose:
        In circumstances like governed broker access to files and stores, helps with normalizing one declared or requested data class into the runtime governance ladder.

    Reference to Theory:
        Supports bundle-style data governance by making data boundaries explicit and machine-checkable before a broker touches the host.

    Example Input Output:
        Input: `normalize_data_class(value='audit-only')`
        Output: 'audit_only'

    Args:
        value: Value for `value` used by `normalize_data_class`. Expected type: `Any`.
        default: Value for `default` used by `normalize_data_class`. Expected type: `str`. Defaults to `'public'`.

    Returns:
        str: Result produced by `normalize_data_class`.
    """
    normalized = collapse_ws(str(value or default)).lower().replace("-", "_").replace(" ", "_")
    if normalized in DATA_CLASS_CHOICES:
        return normalized
    return default


def normalize_data_class_list(value: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like runtime broker mediation and declaration parsing, helps with turning raw declared data classes into one normalized deduplicated list.

    Reference to Theory:
        Supports open governance and bundle-style data mediation by making touched data classes stable across admission, grant issuance, and effect checks.

    Example Input Output:
        Input: `normalize_data_class_list(value=['public', 'derived', 'public'])`
        Output: ['public', 'derived']

    Args:
        value: Value for `value` used by `normalize_data_class_list`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `normalize_data_class_list`.
    """
    normalized: list[str] = []
    for item in _string_list(value):
        data_class = normalize_data_class(item)
        if data_class not in normalized:
            normalized.append(data_class)
    return normalized


def allowed_data_classes_from_governance_context(
    governance_context: Mapping[str, Any] | None,
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like broker-time data-boundary checks, helps with recovering the currently granted or declared data classes that may be touched by the effect.

    Reference to Theory:
        Supports the governed host model by making data access derive from current declaration and grants rather than ambient path freedom.

    Example Input Output:
        Input: `allowed_data_classes_from_governance_context(governance_context={'declaration': {'data_classes_touched': ['public']}, 'grants': [{'data_classes_touched': ['derived']} ]})`
        Output: ['derived', 'public']

    Args:
        governance_context: Value for `governance_context` used by `allowed_data_classes_from_governance_context`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        list[str]: Result produced by `allowed_data_classes_from_governance_context`.
    """
    if not isinstance(governance_context, Mapping):
        return []
    normalized: list[str] = []
    grants = governance_context.get("grants", [])
    if isinstance(grants, list):
        for item in grants:
            if not isinstance(item, Mapping):
                continue
            for data_class in normalize_data_class_list(item.get("data_classes_touched", [])):
                if data_class not in normalized:
                    normalized.append(data_class)
    declaration = governance_context.get("declaration", {})
    if isinstance(declaration, Mapping):
        for data_class in normalize_data_class_list(declaration.get("data_classes_touched", [])):
            if data_class not in normalized:
                normalized.append(data_class)
    return normalized


def ensure_governed_data_access(
    governance_context: Mapping[str, Any] | None,
    *,
    requested_data_classes: list[str] | None,
    operation: str,
) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like mounted filesystem or named-store access, helps with deciding whether the runtime declaration and grants cover the requested data classes.

    Reference to Theory:
        Supports bundle-style data governance by requiring the effect surface to stay within declared data boundaries instead of relying only on path strings.

    Example Input Output:
        Input: `ensure_governed_data_access(governance_context={'declaration': {'data_classes_touched': ['public']}}, requested_data_classes=['secret'], operation='fs.read_mount')`
        Output: (False, 'Governed data access for fs.read_mount requires data classes secret, but runtime grants allow public.')

    Args:
        governance_context: Value for `governance_context` used by `ensure_governed_data_access`. Expected type: `Mapping[str, Any] | None`.
        requested_data_classes: Value for `requested_data_classes` used by `ensure_governed_data_access`. Expected type: `list[str] | None`.
        operation: Value for `operation` used by `ensure_governed_data_access`. Expected type: `str`.

    Returns:
        tuple[bool, str]: Result produced by `ensure_governed_data_access`.
    """
    requested = normalize_data_class_list(requested_data_classes or [])
    if not requested:
        return True, ""
    allowed = allowed_data_classes_from_governance_context(governance_context)
    if not allowed:
        return (
            False,
            f"Governed data access for {collapse_ws(operation)} requires declared data classes "
            f"{', '.join(requested)}, but runtime grants declare none.",
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
    """
    High Level Purpose:
        In circumstances like named store-query brokerage, helps with normalizing the declared query registry into one machine-checkable map.

    Reference to Theory:
        Supports bundle-style host governance by replacing arbitrary SQL with explicit named governed query handles.

    Example Input Output:
        Input: `normalize_named_query_registry(value={'artifact_count': {'sql': 'SELECT COUNT(*) AS artifact_count FROM artifacts', 'data_class': 'internal'}})`
        Output: {'artifact_count': {'sql': 'SELECT COUNT(*) AS artifact_count FROM artifacts', 'parameter_order': [], 'data_class': 'internal'}}

    Args:
        value: Value for `value` used by `normalize_named_query_registry`. Expected type: `Any`.

    Returns:
        dict[str, dict[str, Any]]: Result produced by `normalize_named_query_registry`.
    """
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
        parameter_order = [
            collapse_ws(str(item))
            for item in raw_spec.get("parameter_order", [])
            if collapse_ws(str(item))
        ] if isinstance(raw_spec.get("parameter_order", []), list) else []
        normalized[name] = {
            "sql": sql,
            "parameter_order": parameter_order,
            "data_class": normalize_data_class(raw_spec.get("data_class", "internal"), default="internal"),
        }
    return normalized


def query_is_read_only(sql: str) -> bool:
    """
    High Level Purpose:
        In circumstances like named governed SQLite reads, helps with rejecting mutation-shaped SQL from the named-query broker.

    Reference to Theory:
        Supports host-owned persistence by keeping named queries bounded and read-only rather than allowing arbitrary schema or data mutation.

    Example Input Output:
        Input: `query_is_read_only(sql='SELECT 1')`
        Output: True

    Args:
        sql: Value for `sql` used by `query_is_read_only`. Expected type: `str`.

    Returns:
        bool: Result produced by `query_is_read_only`.
    """
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
        return not any(fragment in f" {normalized} " for fragment in forbidden_fragments)
    return False
