# See MODULES.md for the repository module map before editing.
"""Compatibility facade for canonical governance vocabulary."""

from realized_core_governance.vocabulary import (
    SKILL_APPROVAL_CLASSES,
    SKILL_AUTHORITIES,
    SKILL_KIND_CHOICES,
    SKILL_RISK_TIERS,
    _APPROVAL_INDEX,
    _RISK_INDEX,
    _string_list,
    collapse_ws,
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)


__all__ = [
    "SKILL_APPROVAL_CLASSES",
    "SKILL_AUTHORITIES",
    "SKILL_KIND_CHOICES",
    "SKILL_RISK_TIERS",
    "normalize_skill_approval_class",
    "normalize_skill_authorities",
    "normalize_skill_kind",
    "normalize_skill_risk_tier",
]
