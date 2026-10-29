"""Mechanical host-runtime compatibility evidence for governed skills."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_governance.vocabulary import SKILL_RISK_TIERS, normalize_skill_kind, normalize_skill_risk_tier
from realized_skill_semantics.execution import normalize_executor_framework_name

from .host_abi import host_broker_stability
from .python_brokerization import python_skill_data_surface_assessment
from .skill_declarations import _governed_broker_hints_from_content


_RISK_INDEX = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}


def runtime_skill_compatibility_issue(
    *,
    kind: Any,
    executor_framework: Any,
    risk_tier: Any,
    skill_content: Mapping[str, Any] | None,
) -> str:
    """Return a mechanical runtime-compatibility issue, or an empty string."""
    normalized_kind = normalize_skill_kind(kind)
    normalized_executor = normalize_executor_framework_name(executor_framework)
    normalized_risk = normalize_skill_risk_tier(risk_tier)
    if normalized_kind != "ability" or _RISK_INDEX[normalized_risk] < _RISK_INDEX["tier3_sensitive"]:
        return ""

    content = dict(skill_content) if isinstance(skill_content, Mapping) else {}
    governed_brokers = _governed_broker_hints_from_content(content)
    transitional_brokers = sorted(
        broker_name
        for broker_name in governed_brokers
        if host_broker_stability(broker_name) == "transitional"
    )
    if transitional_brokers:
        runtime_kind = "Python skills" if normalized_executor == "python3" else "governed skills"
        return (
            f"Higher-risk {runtime_kind} must depend only on stable governed host ABI brokers. "
            "Detected transitional brokers: " + ", ".join(transitional_brokers) + "."
        )

    if normalized_executor != "python3":
        return ""
    python_code = str(content.get("python_script", "")).strip()
    if not python_code:
        return ""
    assessment = python_skill_data_surface_assessment(python_code)
    surface_issues: list[str] = []
    if assessment["uses_raw_sqlite"]:
        surface_issues.append("raw sqlite access")
    if assessment["uses_raw_network_io"]:
        surface_issues.append("raw network access")
    if assessment["uses_raw_tool_invocation"]:
        surface_issues.append("raw tool or process invocation")
    if assessment["uses_raw_path_io"]:
        surface_issues.append("raw path-based filesystem access")
    if assessment["uses_legacy_data_brokers"]:
        surface_issues.append("legacy path/sqlite broker surfaces")
    if not surface_issues:
        return ""
    return (
        "Higher-risk Python skills must use governed host ABI surfaces such as "
        "fs.read_mount, fs.write_mount, fs.list_mount, fs.find_mount, "
        "store.named_query, store.skill_state, net.http_get_json, net.http_get_text, "
        "or named macOS brokers. Detected: " + ", ".join(surface_issues) + "."
    )


__all__ = ["runtime_skill_compatibility_issue"]
