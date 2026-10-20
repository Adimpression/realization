# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from typing import Any

from semantic_text import collapse_ws


SKILL_KIND_CHOICES = {"knowledge", "ability", "policy", "approval", "revocation", "incident"}
SKILL_RISK_TIERS = (
    "tier0_passive",
    "tier1_bounded_transform",
    "tier2_connected",
    "tier3_sensitive",
    "tier4_agentic",
    "tier5_sovereign",
)
SKILL_APPROVAL_CLASSES = (
    "automatic",
    "operator_approved",
    "multi_party_approved",
    "organization_approved",
    "emergency_approved",
    "prohibited",
)
SKILL_AUTHORITIES = (
    "read",
    "write",
    "execute",
    "communicate",
    "persist",
    "invoke",
    "approve",
    "modify",
    "export",
    "escalate",
)

_RISK_INDEX = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}
_APPROVAL_INDEX = {level: index for index, level in enumerate(SKILL_APPROVAL_CLASSES)}


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [collapse_ws(str(item)) for item in value if collapse_ws(str(item))]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def normalize_skill_kind(value: Any, *, default: str = "knowledge") -> str:
    normalized = collapse_ws(str(value or default)).lower()
    return normalized if normalized in SKILL_KIND_CHOICES else default


def normalize_skill_risk_tier(value: Any, *, default: str = "tier1_bounded_transform") -> str:
    normalized = collapse_ws(str(value or default)).lower()
    return normalized if normalized in _RISK_INDEX else default


def normalize_skill_approval_class(value: Any, *, default: str = "automatic") -> str:
    normalized = collapse_ws(str(value or default)).lower()
    return normalized if normalized in _APPROVAL_INDEX else default


def normalize_skill_authorities(value: Any) -> list[str]:
    normalized: list[str] = []
    for item in _string_list(value):
        authority = item.lower().replace("-", "_").replace(" ", "_")
        if authority in SKILL_AUTHORITIES and authority not in normalized:
            normalized.append(authority)
    return normalized
