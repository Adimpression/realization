# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from applied_theory_primitives import BoundaryShapeTerm
from artifact import artifact_structured_learning_from_content
from fallback_not_generation import fallback_not_elaboration_for_text
from normalization_primitives import normalize_not_misalignment_list
from retrieval_ranking import artifact_selection_text
from semantic_text import collapse_ws, learning_lookup_keys
from title_semantics import (
    classify_title_depth_relation,
    structured_title_identity_text,
)

def not_elaboration_alignment_rank(
    artifact: Any,
    semantic_unit: str,
    *,
    current_boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
) -> tuple[int, int, int, int, int, int, int]:
    """
    High Level Purpose:
        In circumstances like ranking prior artifacts against a current remainder shape during governed reuse, helps with computing a deterministic alignment order from title-depth, posture, unknowns, differentiators, and repair overlap.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `not_elaboration_alignment_rank(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='knowledge', representation='yaml', boundary_shape=('a*', 'a*', 'd*')), semantic_unit='Physics / Force / Force From Mass And Acceleration', current_boundary_shape=['a*', 'a*', 'd*'])`
        Output: (0, -3, 0, 0, -1, -1, -2)

    Args:
        artifact: Value for `artifact` used by `not_elaboration_alignment_rank`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `not_elaboration_alignment_rank`. Expected type: `str`.
        current_boundary_shape: Value for `current_boundary_shape` used by `not_elaboration_alignment_rank`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.

    Returns:
        tuple[int, int, int, int, int, int, int]: Result produced by `not_elaboration_alignment_rank`.
    """
    artifact_boundary_shape = getattr(artifact, "boundary_shape", ())
    current = fallback_not_elaboration_for_text(
        semantic_unit,
        boundary_shape=current_boundary_shape,
    )
    if hasattr(artifact, "content"):
        prior = artifact_structured_learning_from_content(artifact)
    else:
        prior = fallback_not_elaboration_for_text(
            artifact_selection_text(artifact),
            boundary_shape=artifact_boundary_shape,
        )
    current_title_identity = structured_title_identity_text(current)
    prior_title_identity = structured_title_identity_text(prior)
    title_relation, shared_title_depth = classify_title_depth_relation(current_title_identity, prior_title_identity)
    title_relation_penalty = {
        "same_identity": 0,
        "prior_is_ground_prefix": 1,
        "shared_ground_prefix": 2,
        "prior_is_overdetermined_extension": 3,
        "none": 4,
    }.get(title_relation, 4)
    current_posture = collapse_ws(str(current.get("action_posture", "")).strip())
    prior_posture = collapse_ws(str(prior.get("action_posture", "")).strip())
    posture_penalty = 0 if not current_posture or not prior_posture or current_posture == prior_posture else 1
    current_unknowns = {
        key
        for item in current.get("unknowns", [])
        for key in learning_lookup_keys(str(item))
    }
    prior_unknowns = {
        key
        for item in prior.get("unknowns", [])
        for key in learning_lookup_keys(str(item))
    }
    current_differentiators = {
        key
        for item in current.get("differentiators", [])
        for key in learning_lookup_keys(str(item))
    }
    prior_differentiators = {
        key
        for item in prior.get("differentiators", [])
        for key in learning_lookup_keys(str(item))
    }
    current_risks = {
        key
        for item in current.get("risk_of_wrong_closure", [])
        for key in learning_lookup_keys(str(item))
    }
    prior_risks = {
        key
        for item in prior.get("risk_of_wrong_closure", [])
        for key in learning_lookup_keys(str(item))
    }
    current_missing = {
        key
        for item in current.get("missing_components", [])
        for key in learning_lookup_keys(str(item))
    }
    prior_missing = {
        key
        for item in prior.get("missing_components", [])
        for key in learning_lookup_keys(str(item))
    }
    current_repairs = {
        key
        for item in current.get("minimal_repair", [])
        for key in learning_lookup_keys(str(item))
    }
    prior_repairs = {
        key
        for item in prior.get("minimal_repair", [])
        for key in learning_lookup_keys(str(item))
    }
    current_misalignment = set(normalize_not_misalignment_list(current.get("misalignment_types", [])))
    prior_misalignment = set(normalize_not_misalignment_list(prior.get("misalignment_types", [])))
    missing_unknowns = len(current_unknowns - prior_unknowns) if current_unknowns else 0
    missing_differentiators = len(current_differentiators - prior_differentiators) if current_differentiators else 0
    missing_components = len(current_missing - prior_missing) if current_missing else 0
    shared_unknowns = len(current_unknowns & prior_unknowns)
    shared_differentiators = len(current_differentiators & prior_differentiators)
    shared_risks = len(current_risks & prior_risks)
    shared_repairs = len(current_repairs & prior_repairs)
    misalignment_penalty = len(current_misalignment - prior_misalignment) if current_misalignment else 0
    return (
        title_relation_penalty,
        -shared_title_depth,
        posture_penalty,
        missing_unknowns + missing_differentiators + missing_components + misalignment_penalty,
        -shared_unknowns,
        -shared_differentiators,
        -(shared_risks + shared_repairs),
    )
