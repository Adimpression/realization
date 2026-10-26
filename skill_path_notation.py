# See MODULES.md for the repository module map before editing.
"""Compatibility facade for canonical portable skill path notation."""

from realized_skill_semantics.paths import (
    BoundaryShapeTerm,
    SKILL_PATH_NOTATION_VERSION,
    canonical_skill_path,
    escape_skill_path_segment,
    parse_canonical_skill_path,
    unescape_skill_path_segment,
)

__all__ = [
    "BoundaryShapeTerm",
    "SKILL_PATH_NOTATION_VERSION",
    "canonical_skill_path",
    "escape_skill_path_segment",
    "parse_canonical_skill_path",
    "unescape_skill_path_segment",
]
