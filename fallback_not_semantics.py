# See MODULES.md for the repository module map before editing.
"""Compatibility facade for fallback generation and reuse ranking."""
from __future__ import annotations

from fallback_not_generation import fallback_not_elaboration_for_text
from not_elaboration_ranking import not_elaboration_alignment_rank

__all__ = [
    "fallback_not_elaboration_for_text",
    "not_elaboration_alignment_rank",
]
