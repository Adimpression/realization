# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from realized_core_semantics.applied_primitives import BoundaryShapeTerm
from realized_core_semantics.normalization import (
    extract_boundary_shape_term_values,
    normalize_non_achievedness_degree_value,
    normalize_non_achievedness_misalignment_kind_list,
    normalize_non_achievedness_origin_kind_list,
    normalize_non_achievedness_remainder_shape_kind_list,
)

def _default_boundary_shape_for_goal(*, semantic_unit: str) -> tuple[BoundaryShapeTerm, ...]:
    """
    High Level Purpose:
        In circumstances like normalizing learned semantic payloads into stable runtime fields, helps with deriving a default boundary shape without creating a top-level import cycle.

    Reference to Theory:
        Preserves the artifact/boundary side of title-depth and decomposition while normalization stabilizes semantic units under the applied theory.

    Example Input Output:
        Input: `_default_boundary_shape_for_goal(semantic_unit='Read the referenced dataset and summarize it.')`
        Output: (BoundaryShapeTerm.READ_REFERENCE, BoundaryShapeTerm.OUTPUT_VALUE)

    Args:
        semantic_unit: Value for `semantic_unit` used by `_default_boundary_shape_for_goal`. Expected type: `str`.

    Returns:
        tuple[BoundaryShapeTerm, ...]: Result produced by `_default_boundary_shape_for_goal`.
    """
    from realized_core_semantics.boundary import default_boundary_shape_for_node

    return default_boundary_shape_for_node(semantic_unit=semantic_unit)

def normalize_structured_non_achievedness_payload(
    semantic_unit: str,
    payload: Mapping[str, Any] | None,
    *,
    boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
    related_artifact_titles: Iterable[str] | None = None,
    title_identity: str | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like semantic normalization, title cleanup, and identity stabilization, helps with building payload data for normalize structured non achievedness.

    Reference to Theory:
        Normalizes theory-bearing data so semantic identity, title-depth, and body constitution stay coherent with THEORY.md section 8.8.

    Example Input Output:
        Input: `normalize_structured_non_achievedness_payload(semantic_unit='Physics / Force / Force From Mass And Acceleration', payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, boundary_shape=['input', 'input', 'output'], related_artifact_titles=['Physics', 'Force', 'Force From Mass And Acceleration'])`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

    Args:
        semantic_unit: Value for `semantic_unit` used by `normalize_structured_non_achievedness_payload`. Expected type: `str`.
        payload: Value for `payload` used by `normalize_structured_non_achievedness_payload`. Expected type: `Mapping[str, Any] | None`.
        boundary_shape: Value for `boundary_shape` used by `normalize_structured_non_achievedness_payload`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.
        related_artifact_titles: Value for `related_artifact_titles` used by `normalize_structured_non_achievedness_payload`. Expected type: `Iterable[str] | None`. Defaults to `None`.
        title_identity: Value for `title_identity` used by `normalize_structured_non_achievedness_payload`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `normalize_structured_non_achievedness_payload`.
    """
    from realized_core_engine import normalization_runtime_dependencies as runtime

    normalized_title_identity = runtime.normalize_semantic_title_identity(title_identity or semantic_unit)
    fallback = runtime.fallback_not_elaboration_for_text(
        semantic_unit,
        boundary_shape=boundary_shape,
        title_identity=normalized_title_identity,
    )
    if not isinstance(payload, Mapping):
        return fallback

    normalized_title_identity = runtime.normalize_semantic_title_identity(
        payload.get("title_identity", "")
    ) or normalized_title_identity or str(fallback.get("title_identity", "")).strip()
    title_depth_view = runtime.derive_semantic_title_depth_view(
        normalized_title_identity,
        minimal_sufficient_depth=payload.get(
            "title_depth_minimal_sufficient_depth",
            fallback.get("title_depth_minimal_sufficient_depth"),
        ),
        assessment=payload.get("title_depth_assessment", fallback.get("title_depth_assessment", "")),
    )
    title_is_prolog = runtime.looks_like_prolog_title_identity(normalized_title_identity)
    prolog_view = runtime.prolog_title_view(normalized_title_identity) if title_is_prolog else {}
    encountered_not = runtime.titleize_semantic_unit(str(payload.get("encountered_not", "")).strip()) or fallback["encountered_not"]
    goal = runtime.collapse_ws(str(payload.get("goal", "")).strip()) or fallback["goal"]
    intended_object = runtime.collapse_ws(str(payload.get("intended_object", "")).strip()) or fallback["intended_object"]
    success_criteria = runtime.structured_text_list(payload.get("success_criteria", [])) if "success_criteria" in payload and isinstance(payload.get("success_criteria"), list) else fallback["success_criteria"]
    actual_realization = runtime.collapse_ws(str(payload.get("actual_realization", "")).strip()) or fallback["actual_realization"]
    givens = runtime.structured_text_list(payload.get("givens", [])) if "givens" in payload and isinstance(payload.get("givens"), list) else fallback["givens"]
    unknowns = runtime.structured_text_list(payload.get("unknowns", [])) if "unknowns" in payload and isinstance(payload.get("unknowns"), list) else fallback["unknowns"]
    missing_components = runtime.structured_text_list(payload.get("missing_components", [])) if "missing_components" in payload and isinstance(payload.get("missing_components"), list) else fallback["missing_components"]
    distorted_components = runtime.structured_text_list(payload.get("distorted_components", [])) if "distorted_components" in payload and isinstance(payload.get("distorted_components"), list) else fallback["distorted_components"]
    differentiators = runtime.structured_text_list(payload.get("differentiators", [])) if "differentiators" in payload and isinstance(payload.get("differentiators"), list) else fallback["differentiators"]
    contrastive_cases = runtime.structured_text_list(payload.get("contrastive_cases", [])) if "contrastive_cases" in payload and isinstance(payload.get("contrastive_cases"), list) else fallback["contrastive_cases"]
    risk_of_wrong_closure = runtime.structured_text_list(payload.get("risk_of_wrong_closure", [])) if "risk_of_wrong_closure" in payload and isinstance(payload.get("risk_of_wrong_closure"), list) else fallback["risk_of_wrong_closure"]
    disallowed_assumptions = runtime.structured_text_list(payload.get("disallowed_assumptions", [])) if "disallowed_assumptions" in payload and isinstance(payload.get("disallowed_assumptions"), list) else fallback["disallowed_assumptions"]
    misalignment_types = normalize_non_achievedness_misalignment_kind_list(payload.get("misalignment_types")) if "misalignment_types" in payload else list(fallback["misalignment_types"])
    origin_layers = normalize_non_achievedness_origin_kind_list(payload.get("origin_layers")) if "origin_layers" in payload else list(fallback["origin_layers"])
    degree = normalize_non_achievedness_degree_value(payload.get("degree"), default=fallback["degree"])
    remainder_shapes = normalize_non_achievedness_remainder_shape_kind_list(payload.get("remainder_shapes")) if "remainder_shapes" in payload else list(fallback["remainder_shapes"])
    why_it_matters = runtime.structured_text_list(payload.get("why_it_matters", [])) if "why_it_matters" in payload and isinstance(payload.get("why_it_matters"), list) else fallback["why_it_matters"]
    minimal_repair = runtime.structured_text_list(payload.get("minimal_repair", [])) if "minimal_repair" in payload and isinstance(payload.get("minimal_repair"), list) else fallback["minimal_repair"]
    full_repair = runtime.structured_text_list(payload.get("full_repair", [])) if "full_repair" in payload and isinstance(payload.get("full_repair"), list) else fallback["full_repair"]
    action_posture = runtime.collapse_ws(str(payload.get("action_posture", "")).strip()) or str(fallback.get("action_posture", "")).strip()
    title_depth_hidden_depth_note = runtime.collapse_ws(str(payload.get("title_depth_hidden_depth_note", "")).strip()) or str(
        fallback.get("title_depth_hidden_depth_note", "")
    ).strip()
    if "title_depth_body_split_needed" in payload:
        title_depth_body_split_needed = bool(payload.get("title_depth_body_split_needed"))
    else:
        title_depth_body_split_needed = bool(fallback.get("title_depth_body_split_needed", False))
    title_depth_body_split_reason = runtime.collapse_ws(str(payload.get("title_depth_body_split_reason", "")).strip()) or str(
        fallback.get("title_depth_body_split_reason", "")
    ).strip()
    title_depth_reuse_bias = runtime.collapse_ws(str(payload.get("title_depth_reuse_bias", "")).strip()) or str(
        fallback.get("title_depth_reuse_bias", "")
    ).strip()
    prompt_directive_kind = runtime.collapse_ws(str(payload.get("prompt_directive_kind", "")).strip()) or str(
        fallback.get("prompt_directive_kind", "")
    ).strip() or "none"
    prompt_directive_focus = runtime.collapse_ws(str(payload.get("prompt_directive_focus", "")).strip()) or str(
        fallback.get("prompt_directive_focus", "")
    ).strip()
    prompt_directive_compared_terms = runtime.structured_text_list(
        payload.get("prompt_directive_compared_terms", [])
    ) if "prompt_directive_compared_terms" in payload and isinstance(payload.get("prompt_directive_compared_terms"), list) else list(
        fallback.get("prompt_directive_compared_terms", [])
    )
    prompt_directive_expectations = runtime.structured_text_list(
        payload.get("prompt_directive_expectations", [])
    ) if "prompt_directive_expectations" in payload and isinstance(payload.get("prompt_directive_expectations"), list) else list(
        fallback.get("prompt_directive_expectations", [])
    )
    prompt_directive_requires_formula = bool(
        payload.get("prompt_directive_requires_formula", fallback.get("prompt_directive_requires_formula", False))
    )
    prompt_directive_requires_contrast = bool(
        payload.get("prompt_directive_requires_contrast", fallback.get("prompt_directive_requires_contrast", False))
    )
    prompt_directive_requires_chain = bool(
        payload.get("prompt_directive_requires_chain", fallback.get("prompt_directive_requires_chain", False))
    )
    prompt_directive_requires_substrate = bool(
        payload.get("prompt_directive_requires_substrate", fallback.get("prompt_directive_requires_substrate", False))
    )
    title_similar_identities = runtime.ordered_unique(
        runtime.normalize_semantic_title_identity(str(item).strip()) or runtime.collapse_ws(str(item).strip())
        for item in payload.get("title_similar_identities", fallback.get("title_similar_identities", []))
        if str(item).strip()
    )[:8]
    component_nots = runtime.ordered_unique(
        runtime.normalize_semantic_component_title(str(item).strip()) or str(item).strip()
        for item in payload.get("component_nots", [])
        if str(item).strip()
    ) if "component_nots" in payload and isinstance(payload.get("component_nots"), list) else list(fallback["component_nots"])
    composed_not = runtime.normalize_semantic_component_title(str(payload.get("composed_not", "")).strip()) or fallback["composed_not"]
    lookup_keys = runtime.ordered_unique(
        [str(item).strip().lower() for item in payload.get("lookup_keys", []) if str(item).strip()]
        + runtime.learning_lookup_keys(normalized_title_identity)
        + [key for item in title_depth_view["segments"] for key in runtime.learning_lookup_keys(item)]
        + [key for item in title_depth_view["prefixes"] for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(goal)
        + [key for item in minimal_repair for key in runtime.learning_lookup_keys(item)]
        + [key for item in why_it_matters for key in runtime.learning_lookup_keys(item)]
        + [key for item in missing_components for key in runtime.learning_lookup_keys(item)]
        + [key for item in givens for key in runtime.learning_lookup_keys(item)]
        + [key for item in unknowns for key in runtime.learning_lookup_keys(item)]
        + [key for item in differentiators for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(prompt_directive_focus)
        + [key for item in prompt_directive_compared_terms for key in runtime.learning_lookup_keys(item)]
        + [key for item in prompt_directive_expectations for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(str(prolog_view.get("head_text", "")).strip())
        + runtime.learning_lookup_keys(str(prolog_view.get("predicate", "")).strip())
    ) if "lookup_keys" in payload and isinstance(payload.get("lookup_keys"), list) else runtime.ordered_unique(
        runtime.learning_lookup_keys(normalized_title_identity)
        + [key for item in title_depth_view["segments"] for key in runtime.learning_lookup_keys(item)]
        + [key for item in title_depth_view["prefixes"] for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(goal)
        + [key for item in minimal_repair for key in runtime.learning_lookup_keys(item)]
        + [key for item in why_it_matters for key in runtime.learning_lookup_keys(item)]
        + [key for item in missing_components for key in runtime.learning_lookup_keys(item)]
        + [key for item in givens for key in runtime.learning_lookup_keys(item)]
        + [key for item in unknowns for key in runtime.learning_lookup_keys(item)]
        + [key for item in differentiators for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(prompt_directive_focus)
        + [key for item in prompt_directive_compared_terms for key in runtime.learning_lookup_keys(item)]
        + [key for item in prompt_directive_expectations for key in runtime.learning_lookup_keys(item)]
        + runtime.learning_lookup_keys(str(prolog_view.get("head_text", "")).strip())
        + runtime.learning_lookup_keys(str(prolog_view.get("predicate", "")).strip())
        + fallback["lookup_keys"]
    )
    normalized_boundary_shape = list(
        extract_boundary_shape_term_values(
            payload.get("boundary_shape"),
            default=extract_boundary_shape_term_values(
                boundary_shape,
                default=_default_boundary_shape_for_goal(semantic_unit=goal or semantic_unit),
            ),
        )
    )
    notation_yaml = runtime.render_structured_learning_yaml(
        semantic_unit=goal or semantic_unit,
        encountered_not=encountered_not,
        component_nots=component_nots,
        composed_not=composed_not,
        related_artifact_titles=related_artifact_titles or [],
        title_identity=normalized_title_identity,
        title_depth_segments=list(title_depth_view["segments"]),
        title_depth_prefixes=list(title_depth_view["prefixes"]),
        title_depth_exposed_depth=int(title_depth_view["exposed_depth"]),
        title_depth_minimal_sufficient_depth=int(title_depth_view["minimal_sufficient_depth"]),
        title_depth_assessment=str(title_depth_view["assessment"]),
        title_depth_hidden_depth_note=title_depth_hidden_depth_note,
        title_depth_body_split_needed=title_depth_body_split_needed,
        title_depth_body_split_reason=title_depth_body_split_reason,
        title_depth_reuse_bias=title_depth_reuse_bias,
        title_similar_identities=title_similar_identities,
        intended_object=intended_object,
        success_criteria=success_criteria,
        actual_realization=actual_realization,
        givens=givens,
        unknowns=unknowns,
        missing_components=missing_components,
        distorted_components=distorted_components,
        differentiators=differentiators,
        contrastive_cases=contrastive_cases,
        risk_of_wrong_closure=risk_of_wrong_closure,
        disallowed_assumptions=disallowed_assumptions,
        misalignment_types=misalignment_types,
        origin_layers=origin_layers,
        degree=degree,
        remainder_shapes=remainder_shapes,
        why_it_matters=why_it_matters,
        minimal_repair=minimal_repair,
        full_repair=full_repair,
        action_posture=action_posture,
    )
    return {
        "title_identity": normalized_title_identity,
        "encountered_not": encountered_not,
        "goal": goal,
        "intended_object": intended_object,
        "success_criteria": success_criteria,
        "actual_realization": actual_realization,
        "givens": givens,
        "unknowns": unknowns,
        "missing_components": missing_components,
        "distorted_components": distorted_components,
        "differentiators": differentiators,
        "contrastive_cases": contrastive_cases,
        "risk_of_wrong_closure": risk_of_wrong_closure,
        "disallowed_assumptions": disallowed_assumptions,
        "misalignment_types": misalignment_types,
        "origin_layers": origin_layers,
        "degree": degree,
        "remainder_shapes": remainder_shapes,
        "why_it_matters": why_it_matters,
        "minimal_repair": minimal_repair,
        "full_repair": full_repair,
        "boundary_shape": normalized_boundary_shape,
        "action_posture": action_posture,
        "prompt_directive_kind": prompt_directive_kind,
        "prompt_directive_focus": prompt_directive_focus,
        "prompt_directive_compared_terms": prompt_directive_compared_terms,
        "prompt_directive_expectations": prompt_directive_expectations,
        "prompt_directive_requires_formula": prompt_directive_requires_formula,
        "prompt_directive_requires_contrast": prompt_directive_requires_contrast,
        "prompt_directive_requires_chain": prompt_directive_requires_chain,
        "prompt_directive_requires_substrate": prompt_directive_requires_substrate,
        "title_depth_segments": list(title_depth_view["segments"]),
        "title_depth_prefixes": list(title_depth_view["prefixes"]),
        "title_depth_exposed_depth": int(title_depth_view["exposed_depth"]),
        "title_depth_minimal_sufficient_depth": int(title_depth_view["minimal_sufficient_depth"]),
        "title_depth_assessment": str(title_depth_view["assessment"]),
        "title_depth_hidden_depth_note": title_depth_hidden_depth_note,
        "title_depth_body_split_needed": title_depth_body_split_needed,
        "title_depth_body_split_reason": title_depth_body_split_reason,
        "title_depth_reuse_bias": title_depth_reuse_bias,
        "title_similar_identities": title_similar_identities,
        "title_representation_mode": runtime.TITLE_REPRESENTATION_MODE_PROLOG if title_is_prolog else runtime.TITLE_REPRESENTATION_MODE_SLASH,
        "title_prolog_head": str(prolog_view.get("head_text", "")).strip(),
        "title_prolog_body": str(prolog_view.get("body_text", "")).strip(),
        "title_prolog_predicate": str(prolog_view.get("predicate", "")).strip(),
        "title_prolog_arity": int(prolog_view.get("arity", 0) or 0),
        "title_prolog_head_canonical": str(prolog_view.get("head_canonical", "")).strip(),
        "component_nots": component_nots,
        "composed_not": composed_not,
        "lookup_keys": lookup_keys[:24],
        "notation_yaml": notation_yaml,
    }

normalize_not_elaboration_payload = normalize_structured_non_achievedness_payload
