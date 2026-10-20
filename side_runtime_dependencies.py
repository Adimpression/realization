# See MODULES.md for the repository module map before editing.
"""Explicit dependencies for artifact side-channel import and export."""
from __future__ import annotations

from applied_theory_primitives import ABILITY_SCRIPT_DEPENDENCIES, utc_now
from applied_theory_types import enum_text
from artifact import (
    STRUCTURED_LEARNING_EXTRA_FIELDS,
    artifact_structured_learning_from_content,
    contract_mapping_from_entries,
    yaml_dump_human,
    yaml_string_list,
)
from fallback_not_generation import fallback_not_elaboration_for_text
from id_generation import make_id
from normalize import (
    normalize_artifact_admission,
    normalize_artifact_representation,
    normalize_artifact_reuse,
    normalize_artifact_type,
    normalize_boundary_shape,
    normalize_function_bit,
    normalize_learning_relation,
    normalize_not_elaboration_payload,
)
from semantic_text import learning_lookup_keys, ordered_unique, titleize_semantic_unit
from store import build_artifact_store
from structured_learning_yaml import render_structured_learning_yaml

__all__ = [
    "ABILITY_SCRIPT_DEPENDENCIES",
    "STRUCTURED_LEARNING_EXTRA_FIELDS",
    "artifact_structured_learning_from_content",
    "build_artifact_store",
    "contract_mapping_from_entries",
    "enum_text",
    "fallback_not_elaboration_for_text",
    "learning_lookup_keys",
    "make_id",
    "normalize_artifact_admission",
    "normalize_artifact_representation",
    "normalize_artifact_reuse",
    "normalize_artifact_type",
    "normalize_boundary_shape",
    "normalize_function_bit",
    "normalize_learning_relation",
    "normalize_not_elaboration_payload",
    "ordered_unique",
    "render_structured_learning_yaml",
    "titleize_semantic_unit",
    "utc_now",
    "yaml_dump_human",
    "yaml_string_list",
]
