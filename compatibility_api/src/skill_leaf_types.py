# See MODULES.md for the repository module map before editing.
"""Compatibility facade for canonical portable skill leaf semantics."""

from realized_skill_semantics.leaves import (
    BoundaryShapeTerm,
    REGION_SYMBOL_BY_TERM,
    REGION_TERM_BY_SYMBOL,
    SKILL_LEAF_NON_PRIMITIVE_TYPE_ALIASES,
    STATE_INTERFACE_PRIMITIVE_KIND_ALIASES,
    STATE_INTERFACE_REPEATED_PRIMITIVE_KIND_ALIASES,
    SkillLeaf,
    SkillLeafCarrierKind,
    SkillLeafClass,
    normalize_skill_boundary_region,
    normalize_skill_leaf_data_type,
    skill_boundary_region_symbol,
    skill_leaf_carrier_kind_for_region,
)

__all__ = [
    "BoundaryShapeTerm",
    "REGION_SYMBOL_BY_TERM",
    "REGION_TERM_BY_SYMBOL",
    "SKILL_LEAF_NON_PRIMITIVE_TYPE_ALIASES",
    "STATE_INTERFACE_PRIMITIVE_KIND_ALIASES",
    "STATE_INTERFACE_REPEATED_PRIMITIVE_KIND_ALIASES",
    "SkillLeaf",
    "SkillLeafCarrierKind",
    "SkillLeafClass",
    "normalize_skill_boundary_region",
    "normalize_skill_leaf_data_type",
    "skill_boundary_region_symbol",
    "skill_leaf_carrier_kind_for_region",
]
