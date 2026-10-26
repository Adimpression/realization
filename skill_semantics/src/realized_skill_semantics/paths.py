"""Canonical region-aware path notation for portable skill ledgers."""

from __future__ import annotations

from typing import Any

from realized_core_semantics.theory import (
    BoundaryShapeTermKind as BoundaryShapeTerm,
)
from realized_skill_semantics.leaves import (
    normalize_skill_boundary_region,
    skill_boundary_region_symbol,
)


__all__ = [
    "BoundaryShapeTerm",
    "SKILL_PATH_NOTATION_VERSION",
    "canonical_skill_path",
    "escape_skill_path_segment",
    "parse_canonical_skill_path",
    "unescape_skill_path_segment",
]


SKILL_PATH_NOTATION_VERSION = "bssc.skill.path.v1"


def escape_skill_path_segment(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like canonical skill path formation, helps with escaping one path segment so separators and escape markers remain losslessly reconstructible.

    Reference to Theory:
        Implements section-4.6 canonical path notation with a deterministic, reconstructible escaping rule.

    Example Input Output:
        Input: `escape_skill_path_segment('source/file~1')`
        Output: 'source~1file~01'

    Args:
        value: Value for `value` used by `escape_skill_path_segment`. Expected type: `Any`.

    Returns:
        str: Result produced by `escape_skill_path_segment`.
    """
    text = str(value)
    return text.replace("~", "~0").replace("/", "~1")


def unescape_skill_path_segment(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like canonical skill path parsing, helps with reversing the canonical escaping rule back into the original path segment text.

    Reference to Theory:
        Preserves section-4.6 reconstructibility for canonical path notation.

    Example Input Output:
        Input: `unescape_skill_path_segment('source~1file~01')`
        Output: 'source/file~1'

    Args:
        value: Value for `value` used by `unescape_skill_path_segment`. Expected type: `Any`.

    Returns:
        str: Result produced by `unescape_skill_path_segment`.
    """
    text = str(value)
    return text.replace("~1", "/").replace("~0", "~")


def canonical_skill_path(
    region: BoundaryShapeTerm | str,
    segments: list[Any] | tuple[Any, ...] = (),
) -> str:
    """
    High Level Purpose:
        In circumstances like skill boundary normalization, helps with rendering one boundary-region root plus hierarchical segments into canonical path notation.

    Reference to Theory:
        Implements section-4.6 region-aware canonical path notation such as `/a/query` and `/d'/artifact/main`.

    Example Input Output:
        Input: `canonical_skill_path(BoundaryShapeTerm.INPUT_VALUE, ['options', 'roots', 0])`
        Output: '/a/options/roots/0'

    Args:
        region: Value for `region` used by `canonical_skill_path`. Expected type: `BoundaryShapeTerm | str`.
        segments: Value for `segments` used by `canonical_skill_path`. Expected type: `list[Any] | tuple[Any, ...]`. Defaults to `()`.

    Returns:
        str: Result produced by `canonical_skill_path`.
    """
    normalized = normalize_skill_boundary_region(region)
    root = f"/{skill_boundary_region_symbol(normalized)}"
    if not segments:
        return root
    suffix = "/".join(escape_skill_path_segment(item) for item in segments)
    return f"{root}/{suffix}"


def parse_canonical_skill_path(path: str) -> tuple[BoundaryShapeTerm, list[str]]:
    """
    High Level Purpose:
        In circumstances like reconstructing a normalized skill ledger, helps with parsing canonical path notation back into its boundary-region root and ordered segments.

    Reference to Theory:
        Preserves section-4.6 reconstructibility and region-aware flattening for canonical skill paths.

    Example Input Output:
        Input: `parse_canonical_skill_path('/a/options/roots/0')`
        Output: (BoundaryShapeTerm.INPUT_VALUE, ['options', 'roots', '0'])

    Args:
        path: Value for `path` used by `parse_canonical_skill_path`. Expected type: `str`.

    Returns:
        tuple[BoundaryShapeTerm, list[str]]: Result produced by `parse_canonical_skill_path`.
    """
    normalized = str(path or "").strip()
    if not normalized.startswith("/"):
        raise ValueError(f"Canonical skill path must start with '/': {path}")
    parts = normalized.split("/")[1:]
    if not parts or not parts[0]:
        raise ValueError(f"Canonical skill path requires a region root: {path}")
    region = normalize_skill_boundary_region(parts[0])
    segments = [unescape_skill_path_segment(part) for part in parts[1:]]
    return region, segments
