# See MODULES.md for the repository module map before editing.
"""Named dependencies for structured non-achievedness normalization."""
from __future__ import annotations

from fallback_not_generation import fallback_not_elaboration_for_text
from prolog import looks_like_prolog_title_identity, prolog_title_view
from semantic_text import (
    collapse_ws,
    learning_lookup_keys,
    normalize_semantic_component_title,
    ordered_unique,
    structured_text_list,
    titleize_semantic_unit,
)
from structured_learning_yaml import render_structured_learning_yaml
from title_semantics import (
    TITLE_REPRESENTATION_MODE_PROLOG,
    TITLE_REPRESENTATION_MODE_SLASH,
    derive_semantic_title_depth_view,
    normalize_semantic_title_identity,
)

__all__ = [
    "TITLE_REPRESENTATION_MODE_PROLOG",
    "TITLE_REPRESENTATION_MODE_SLASH",
    "collapse_ws",
    "derive_semantic_title_depth_view",
    "fallback_not_elaboration_for_text",
    "learning_lookup_keys",
    "looks_like_prolog_title_identity",
    "normalize_semantic_component_title",
    "normalize_semantic_title_identity",
    "ordered_unique",
    "prolog_title_view",
    "render_structured_learning_yaml",
    "structured_text_list",
    "titleize_semantic_unit",
]
