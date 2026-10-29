# See MODULES.md for the repository module map before editing.
"""Explicit dependencies for artifact side-channel import and export."""
from __future__ import annotations

from realized_core_semantics.applied_primitives import ABILITY_SCRIPT_DEPENDENCIES, utc_now
from realized_core_semantics.applied_model import enum_text
from realized_core_engine.artifact_semantics import (
    STRUCTURED_LEARNING_EXTRA_FIELDS,
    artifact_structured_learning_from_content,
    contract_mapping_from_entries,
    yaml_dump_human,
    yaml_string_list,
)
from realized_core_engine.fallback_not_generation import fallback_not_elaboration_for_text
from realized_core_semantics.identifiers import make_id
from realized_core_engine.non_achievedness_normalization import normalize_not_elaboration_payload
from realized_core_semantics.normalization import (
    normalize_artifact_admission,
    normalize_artifact_representation,
    normalize_artifact_reuse,
    normalize_artifact_type,
    normalize_boundary_shape,
    normalize_function_bit,
    normalize_learning_relation,
)
from realized_core_semantics.semantic_text import learning_lookup_keys, ordered_unique, titleize_semantic_unit
from realized_core_engine.persistence import build_artifact_store
from realized_core_engine.structured_learning import render_structured_learning_yaml

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
