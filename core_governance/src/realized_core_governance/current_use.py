"""Deterministic current-use eligibility for governed skills."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_governance._normalization import collapse_ws
from realized_core_governance.lifecycle import skill_lifecycle_allows_invocation
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V2,
    normalize_skill_schema_version,
)


def skill_admission_allows_current_use(
    *,
    schema_version: Any,
    admission: Mapping[str, Any] | None,
) -> tuple[bool, str]:
    """Evaluate schema compatibility and admission gates before lifecycle work."""
    schema = normalize_skill_schema_version(schema_version)
    if schema != SKILL_SCHEMA_VERSION_V2:
        return True, ""
    if not admission:
        return False, "Governed skill has no admission record."
    if str(admission.get("status", "")).strip().lower() != "admitted":
        rationale = collapse_ws(str(admission.get("rationale", "")))
        return False, rationale or "Governed skill is not admitted for use."
    return True, ""


def skill_current_use_allows_invocation(
    *,
    schema_version: Any,
    admission: Mapping[str, Any] | None,
    lifecycle: Mapping[str, Any] | None,
) -> tuple[bool, str]:
    """Evaluate final current-use eligibility over already supplied state."""
    schema = normalize_skill_schema_version(schema_version)
    if schema != SKILL_SCHEMA_VERSION_V2:
        return True, ""
    admission_allowed, admission_reason = skill_admission_allows_current_use(
        schema_version=schema,
        admission=admission,
    )
    if not admission_allowed:
        return False, admission_reason
    return skill_lifecycle_allows_invocation(lifecycle)


__all__ = [
    "skill_admission_allows_current_use",
    "skill_current_use_allows_invocation",
]
