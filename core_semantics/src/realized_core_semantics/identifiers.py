# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
import uuid

from .semantic_text import collapse_ws


def slugify(text: str, *, limit: int = 48) -> str:
    """
    High Level Purpose:
        In circumstances like runtime/controller identifier shaping, helps with reducing one text surface to a compact slug segment suitable for stable identifier construction.

    Reference to Theory:
        Supports lower-layer identifier generation without requiring callers to depend on controller composition in `main.py`.

    Example Input Output:
        Input: `slugify(text='Compute force from mass and acceleration.', limit=16)`
        Output: 'compute-force-fr'

    Args:
        text: Value for `text` used by `slugify`. Expected type: `str`.
        limit: Value for `limit` used by `slugify`. Expected type: `int`. Defaults to `48`.

    Returns:
        str: Result produced by `slugify`.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit] or "item"


def make_id(prefix: str, text: str = "") -> str:
    """
    High Level Purpose:
        In circumstances like runtime graph construction and controller-side artifact/evidence creation, helps with constructing a stable identifier from semantic text without depending on `main.py`.

    Reference to Theory:
        Supports six-layer extraction by moving generic identifier construction below controller/runtime composition.

    Example Input Output:
        Input: `make_id(prefix='artifact', text='force-from-mass-and-acceleration')`
        Output: 'artifact_force-from-mass-and-acceleration_a1b2c3'

    Args:
        prefix: Value for `prefix` used by `make_id`. Expected type: `str`.
        text: Value for `text` used by `make_id`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `make_id`.
    """
    suffix = slugify(text) if text else uuid.uuid4().hex[:8]
    return f"{prefix}_{suffix}_{uuid.uuid4().hex[:6]}"


def canonical_learning_subject_id(text: str) -> str:
    """Return the stable subject identifier used by the subject lifecycle."""
    normalized = slugify(collapse_ws(text), limit=64)
    return normalized or "subject"


__all__ = ["canonical_learning_subject_id", "make_id", "slugify"]
