# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from realized_core_semantics.applied_primitives import (
    BoundaryShapeTerm,
    NotDegreeKind,
    NotMisalignmentKind,
    NotOriginKind,
    NotRemainderShapeKind,
)
from realized_core_semantics.boundary import default_boundary_shape_for_node
from realized_core_semantics.normalization import (
    boundary_shape_values,
    normalize_not_degree,
    normalize_not_misalignment_list,
    normalize_not_origin_list,
    normalize_remainder_shape_list,
)
from realized_core_engine.prompt_directives import (
    prompt_has_absence_signal,
    prompt_has_confirmation_signal,
    prompt_has_unresolved_uncertainty,
    semantic_prompt_directive_profile,
)
from realized_core_semantics.prolog import looks_like_prolog_title_identity, prolog_title_view
from realized_core_engine.semantic_prompt_posture import semantic_prompt_action_posture
from realized_core_semantics.semantic_text import (
    collapse_ws,
    learning_component_units,
    learning_core_tokens,
    learning_lookup_keys,
    ordered_unique,
    semantic_named_input_keys,
    structured_text_list,
    titleize_semantic_unit,
)
from realized_core_engine.structured_learning import render_structured_learning_yaml
from realized_core_semantics.title_semantics import (
    TITLE_REPRESENTATION_MODE_PROLOG,
    TITLE_REPRESENTATION_MODE_SLASH,
    derive_semantic_title_depth_view,
    normalize_semantic_title_identity,
)

def fallback_not_elaboration_for_text(
    semantic_unit: str,
    *,
    boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
    title_identity: str | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like synthesizing a governed fallback remainder for a prompt that has not yet been reduced by an LLM proposal, helps with building the full non-achievedness record the runtime can rank, normalize, and reuse.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `fallback_not_elaboration_for_text(semantic_unit='Physics / Force / Force From Mass And Acceleration', boundary_shape=['a*', 'a*', 'd*'], title_identity='Physics / Force / Force From Mass And Acceleration')`
        Output: {'title_identity': 'Physics / Force / Force From Mass And Acceleration', 'encountered_not': 'Physics Force Force From Mass And Acceleration', 'action_posture': 'direct_resolution'}

    Args:
        semantic_unit: Value for `semantic_unit` used by `fallback_not_elaboration_for_text`. Expected type: `str`.
        boundary_shape: Value for `boundary_shape` used by `fallback_not_elaboration_for_text`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.
        title_identity: Value for `title_identity` used by `fallback_not_elaboration_for_text`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `fallback_not_elaboration_for_text`.
    """
    semantic_text = collapse_ws(str(semantic_unit or "").strip())
    prompt_directive = semantic_prompt_directive_profile(semantic_text)
    directive_kind = collapse_ws(str(prompt_directive.get("kind", "")).strip())
    directive_focus = collapse_ws(str(prompt_directive.get("focus_text", "")).strip())
    directive_compared_terms = structured_text_list(prompt_directive.get("compared_terms", []))
    directive_expectations = structured_text_list(prompt_directive.get("expectations", []))
    directive_requires_formula = bool(prompt_directive.get("requires_formula", False))
    directive_requires_contrast = bool(prompt_directive.get("requires_contrast", False))
    directive_requires_chain = bool(prompt_directive.get("requires_chain", False))
    directive_requires_substrate = bool(prompt_directive.get("requires_substrate", False))
    normalized_title_identity = normalize_semantic_title_identity(title_identity or semantic_text)
    title_depth_view = derive_semantic_title_depth_view(normalized_title_identity)
    prolog_view = prolog_title_view(normalized_title_identity) if looks_like_prolog_title_identity(normalized_title_identity) else {}
    normalized_boundary_shape = list(
        boundary_shape_values(
            boundary_shape,
            default=default_boundary_shape_for_node(semantic_unit=semantic_text),
        )
    )
    encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(semantic_text))) or titleize_semantic_unit(semantic_text) or "Active Non Achievedness"
    component_nots = learning_component_units(semantic_text)
    composed_not = encountered_not if len(component_nots) > 1 else ""

    clauses = [
        collapse_ws(part)
        for part in re.split(r"[,.!?;]\s*", semantic_text)
        if collapse_ws(part)
    ]
    givens = [
        clause
        for clause in clauses
        if re.search(r"\b(i have|we have|there is|there are|given|with|holding|contains?|includes?|already)\b", clause, flags=re.IGNORECASE)
        or re.search(r"\b[A-Za-z_][A-Za-z0-9_]*\s*(?:=|:)\s*[^ ,;]+", clause)
        or re.search(r"\b\d+(?:\.\d+)?\b", clause)
    ][:4]

    unknowns: list[str] = []
    differentiators: list[str] = []
    contrastive_cases: list[str] = []
    disallowed_assumptions: list[str] = []
    risk_of_wrong_closure: list[str] = []

    if prompt_has_unresolved_uncertainty(semantic_text):
        unknowns.append("one or more decisive facts remain unconfirmed")
        differentiators.append("different explicit alternatives may lead to different next actions")
        disallowed_assumptions.append("do not treat an unresolved alternative as confirmed")
        risk_of_wrong_closure.append("acting on the wrong alternative could produce the wrong result")
        alternatives = re.findall(r"(\b[^.?!,;]{0,40}\bor\b[^.?!,;]{0,40}\b)", semantic_text, flags=re.IGNORECASE)
        if alternatives:
            differentiators.extend(collapse_ws(item) for item in alternatives[:2])
        contrastive_cases.append("confirmed case versus unresolved case")

    if re.search(r"\bwhat should\b|\bwhat do i do\b|\bnext step\b|\bshould i\b", semantic_text, flags=re.IGNORECASE):
        unknowns.append("the admissible next step is not yet determined")

    if prompt_has_confirmation_signal(semantic_text):
        differentiators.append("explicit confirmation or verified-match language is present")
        contrastive_cases.append("confirmed match versus unresolved mismatch")

    if prompt_has_absence_signal(semantic_text):
        differentiators.append("explicit absence is stated and should not be collapsed into presence")
        contrastive_cases.append("relevant item present versus explicitly absent")
        disallowed_assumptions.append("do not infer the presence of an item when the prompt states absence")

    if semantic_named_input_keys(semantic_text):
        differentiators.extend(f"named inputs supplied: {', '.join(semantic_named_input_keys(semantic_text))}" for _ in [0])

    if re.search(r"\bif\b", semantic_text, flags=re.IGNORECASE):
        contrastive_cases.append("condition holds versus condition does not hold")

    if directive_kind == "state":
        differentiators.append("the requested governing law or relation must be stated faithfully")
        if directive_requires_formula:
            differentiators.append("formula-level fidelity is explicitly required")

    if directive_kind == "distinguish":
        differentiators.append("the answer must preserve the requested contrast between the compared cases")
        contrastive_cases.extend(
            directive_compared_terms or ["the first contrasted case versus the second contrasted case"]
        )

    if directive_kind == "derive":
        differentiators.append("the intermediate derivation chain must remain visible")
        if directive_requires_formula:
            differentiators.append("the final derived relation must remain explicit")

    if directive_kind == "construct":
        differentiators.append("the ordered composition path must remain explicit")

    if directive_kind == "identify_reusable_substrate":
        differentiators.append("the broader reusable substrate must stay distinct from the narrower determinate case")
        if directive_requires_substrate:
            differentiators.append("the prompt explicitly asks for the reusable family or broader ground")

    action_posture = semantic_prompt_action_posture(semantic_text)

    lookup_keys = ordered_unique(
        learning_lookup_keys(semantic_text)
        + [key for item in differentiators for key in learning_lookup_keys(item)]
        + [key for item in unknowns for key in learning_lookup_keys(item)]
        + learning_lookup_keys(directive_focus)
        + [key for item in directive_compared_terms for key in learning_lookup_keys(item)]
        + [key for item in directive_expectations for key in learning_lookup_keys(item)]
    )[:24]

    givens = structured_text_list(givens)
    unknowns = structured_text_list(unknowns)
    differentiators = structured_text_list(differentiators)
    contrastive_cases = structured_text_list(contrastive_cases)
    disallowed_assumptions = structured_text_list(disallowed_assumptions)
    risk_of_wrong_closure = structured_text_list(risk_of_wrong_closure)

    intended_object = directive_focus or semantic_text or encountered_not
    success_criteria: list[str] = []
    missing_components: list[str] = list(unknowns)
    distorted_components: list[str] = []
    misalignment_types: list[str] = []
    origin_layers: list[str] = []
    remainder_shapes: list[str] = []
    why_it_matters: list[str] = []
    minimal_repair: list[str] = []

    if prompt_has_unresolved_uncertainty(semantic_text):
        success_criteria.append("the decisive unresolved alternative is explicitly resolved before closure")
        success_criteria.append("the next step or answer is conditioned only on confirmed facts")
        distorted_components.append("confirmed and unconfirmed cases must not be collapsed together")
        misalignment_types.extend(
            [
                NotMisalignmentKind.SPECIFICATION.value,
                NotMisalignmentKind.EPISTEMIC.value,
                NotMisalignmentKind.FIDELITY.value,
            ]
        )
        origin_layers.extend([NotOriginKind.PROMPT.value, NotOriginKind.KNOWLEDGE.value])
        remainder_shapes.extend(
            [
                NotRemainderShapeKind.UNDERDETERMINED.value,
                NotRemainderShapeKind.BLOCKED.value,
            ]
        )
        why_it_matters.append("different unresolved alternatives could require materially different actions or answers")
        minimal_repair.append("confirm the decisive unresolved fact before acting or closing")

    if directive_kind == "state":
        success_criteria.extend(
            [
                "the requested law, relation, formula, or governing statement is stated faithfully",
                "the answer preserves the requested variable roles or relation surface rather than drifting to a nearby family",
            ]
        )
        misalignment_types.extend([NotMisalignmentKind.FIDELITY.value, NotMisalignmentKind.COMPLETION.value])
        origin_layers.append(NotOriginKind.PROMPT.value)
        remainder_shapes.append(NotRemainderShapeKind.MISSING.value)
        minimal_repair.append("recover and state the requested governing relation or law faithfully")

    if directive_kind == "distinguish":
        success_criteria.extend(
            [
                "both contrasted cases remain explicit",
                "the discriminating difference between the contrasted cases is stated clearly",
            ]
        )
        distorted_components.append("the contrasted cases would be flattened together if the difference is omitted")
        misalignment_types.extend([NotMisalignmentKind.SEMANTIC.value, NotMisalignmentKind.FIDELITY.value])
        origin_layers.append(NotOriginKind.PROMPT.value)
        remainder_shapes.append(NotRemainderShapeKind.UNDERDETERMINED.value)
        minimal_repair.append("name both contrasted cases and state the specific difference between them")

    if directive_kind == "derive":
        success_criteria.extend(
            [
                "the intermediate relation chain required for the target result is preserved",
                "the derivation reaches the requested relation without skipping the governing intermediate steps",
            ]
        )
        misalignment_types.extend([NotMisalignmentKind.SEMANTIC.value, NotMisalignmentKind.COMPLETION.value])
        origin_layers.append(NotOriginKind.PROMPT.value)
        remainder_shapes.append(NotRemainderShapeKind.UNDERDETERMINED.value)
        minimal_repair.append("recover the intermediate relations and present the derivation chain to the requested result")

    if directive_kind == "construct":
        success_criteria.extend(
            [
                "the ordered construction or staged composition is explicit",
                "the answer names the intermediate dependencies instead of jumping directly to the end state",
            ]
        )
        misalignment_types.extend([NotMisalignmentKind.STRUCTURAL.value, NotMisalignmentKind.COMPLETION.value])
        origin_layers.append(NotOriginKind.PROMPT.value)
        remainder_shapes.append(NotRemainderShapeKind.UNDERDETERMINED.value)
        minimal_repair.append("name the ordered stages or dependencies that compose into the requested result")

    if directive_kind == "identify_reusable_substrate":
        success_criteria.extend(
            [
                "the broader reusable substrate is identified explicitly",
                "the narrower determinate law or application remains distinct from that broader substrate",
            ]
        )
        misalignment_types.extend([NotMisalignmentKind.SEMANTIC.value, NotMisalignmentKind.STRUCTURAL.value])
        origin_layers.append(NotOriginKind.PROMPT.value)
        remainder_shapes.append(NotRemainderShapeKind.UNDERDETERMINED.value)
        minimal_repair.append("identify the broader reusable family and map the requested case onto it")

    if semantic_named_input_keys(semantic_text) or re.search(r"\bcalculate\b|\bcompute\b|\bfind\b|\bsolve\b", semantic_text, flags=re.IGNORECASE):
        success_criteria.append("all required inputs are explicit and the bounded computation or template is applied faithfully")
        success_criteria.append("the result is returned in the requested usable form")
        misalignment_types.extend([NotMisalignmentKind.FUNCTIONAL.value, NotMisalignmentKind.COMPLETION.value])
        if semantic_named_input_keys(semantic_text):
            origin_layers.append(NotOriginKind.MODEL.value)
            remainder_shapes.append(NotRemainderShapeKind.MISSING.value)
            minimal_repair.append("perform the bounded computation or invoke the matching executable template")
        else:
            origin_layers.append(NotOriginKind.PROMPT.value)
            missing_components.append("the full set of required inputs or executable relation is not yet explicit")
            remainder_shapes.append(NotRemainderShapeKind.UNDERDETERMINED.value)
            minimal_repair.append("supply or recover the missing inputs and then perform the bounded computation")

    if re.search(r"\bwhat should\b|\bwhat do i do\b|\bshould i\b|\bnext step\b", semantic_text, flags=re.IGNORECASE):
        success_criteria.append("the next step is specific, actionable, and faithful to the stated facts")
        misalignment_types.extend([NotMisalignmentKind.FUNCTIONAL.value, NotMisalignmentKind.FIDELITY.value])
        minimal_repair.append("derive the next admissible step from the confirmed facts and explicit uncertainties")

    if not success_criteria:
        success_criteria.append("the response directly resolves the stated ask without erasing material distinctions")
    if not missing_components and semantic_text:
        missing_components.append("a justified final realization has not yet been produced")
    if not why_it_matters:
        why_it_matters.append("without reducing the remainder, the item cannot be closed with governed confidence")
    if not misalignment_types:
        misalignment_types = [NotMisalignmentKind.COMPLETION.value]
    if not origin_layers:
        origin_layers = [NotOriginKind.MODEL.value if semantic_text else NotOriginKind.PROMPT.value]
    if not remainder_shapes:
        remainder_shapes = [NotRemainderShapeKind.MISSING.value]

    actual_realization_parts = ["the prompt surface is present"]
    if givens:
        actual_realization_parts.append(f"explicit givens are present: {', '.join(givens[:3])}")
    if unknowns:
        actual_realization_parts.append(f"unresolved points remain: {', '.join(unknowns[:3])}")
    actual_realization_parts.append("no justified final closure has been admitted yet")
    actual_realization = "; ".join(actual_realization_parts)

    degree = NotDegreeKind.PARTIAL.value
    if not semantic_text:
        degree = NotDegreeKind.TOTAL.value
    elif prompt_has_unresolved_uncertainty(semantic_text):
        degree = NotDegreeKind.DOMINANT.value

    success_criteria = structured_text_list(success_criteria)
    missing_components = structured_text_list(missing_components)
    distorted_components = structured_text_list(distorted_components)
    why_it_matters = structured_text_list(why_it_matters)
    minimal_repair = structured_text_list(minimal_repair)
    full_repair = structured_text_list(
        minimal_repair
        + [f"satisfy success condition: {item}" for item in success_criteria]
    )
    misalignment_types = normalize_not_misalignment_list(misalignment_types)
    origin_layers = normalize_not_origin_list(origin_layers)
    remainder_shapes = normalize_remainder_shape_list(remainder_shapes)
    degree = normalize_not_degree(degree, default=NotDegreeKind.PARTIAL)
    lookup_keys = ordered_unique(
        learning_lookup_keys(semantic_text)
        + [key for item in component_nots for key in learning_lookup_keys(item)]
        + ([key for key in learning_lookup_keys(composed_not)] if composed_not else [])
        + [key for item in givens for key in learning_lookup_keys(item)]
        + [key for item in differentiators for key in learning_lookup_keys(item)]
        + [key for item in unknowns for key in learning_lookup_keys(item)]
        + [key for item in contrastive_cases for key in learning_lookup_keys(item)]
        + learning_lookup_keys(directive_focus)
        + [key for item in directive_compared_terms for key in learning_lookup_keys(item)]
        + [key for item in directive_expectations for key in learning_lookup_keys(item)]
        + learning_lookup_keys(str(prolog_view.get("head_text", "")).strip())
        + learning_lookup_keys(str(prolog_view.get("predicate", "")).strip())
        + lookup_keys
    )[:24]

    notation_yaml = render_structured_learning_yaml(
        semantic_unit=semantic_text,
        encountered_not=encountered_not,
        component_nots=component_nots,
        composed_not=composed_not,
        related_artifact_titles=[],
        title_identity=normalized_title_identity,
        title_depth_segments=list(title_depth_view["segments"]),
        title_depth_prefixes=list(title_depth_view["prefixes"]),
        title_depth_exposed_depth=int(title_depth_view["exposed_depth"]),
        title_depth_minimal_sufficient_depth=int(title_depth_view["minimal_sufficient_depth"]),
        title_depth_assessment=str(title_depth_view["assessment"]),
        title_depth_hidden_depth_note="title-depth is inferred from context rather than explicitly specified",
        title_depth_body_split_needed=False,
        title_depth_body_split_reason="",
        title_depth_reuse_bias="determinate_reuse" if int(title_depth_view["exposed_depth"]) > 1 else "ground_reuse",
        title_similar_identities=[],
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
        "goal": semantic_text,
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
        "prompt_directive_kind": directive_kind or "none",
        "prompt_directive_focus": directive_focus,
        "prompt_directive_compared_terms": directive_compared_terms,
        "prompt_directive_expectations": directive_expectations,
        "prompt_directive_requires_formula": directive_requires_formula,
        "prompt_directive_requires_contrast": directive_requires_contrast,
        "prompt_directive_requires_chain": directive_requires_chain,
        "prompt_directive_requires_substrate": directive_requires_substrate,
        "title_depth_segments": list(title_depth_view["segments"]),
        "title_depth_prefixes": list(title_depth_view["prefixes"]),
        "title_depth_exposed_depth": int(title_depth_view["exposed_depth"]),
        "title_depth_minimal_sufficient_depth": int(title_depth_view["minimal_sufficient_depth"]),
        "title_depth_assessment": str(title_depth_view["assessment"]),
        "title_depth_hidden_depth_note": "title-depth is inferred from context rather than explicitly specified",
        "title_depth_body_split_needed": False,
        "title_depth_body_split_reason": "",
        "title_depth_reuse_bias": "determinate_reuse" if int(title_depth_view["exposed_depth"]) > 1 else "ground_reuse",
        "title_similar_identities": [],
        "title_representation_mode": (
            TITLE_REPRESENTATION_MODE_PROLOG
            if looks_like_prolog_title_identity(normalized_title_identity)
            else TITLE_REPRESENTATION_MODE_SLASH
        ),
        "title_prolog_head": str(prolog_view.get("head_text", "")).strip(),
        "title_prolog_body": str(prolog_view.get("body_text", "")).strip(),
        "title_prolog_predicate": str(prolog_view.get("predicate", "")).strip(),
        "title_prolog_arity": int(prolog_view.get("arity", 0) or 0),
        "title_prolog_head_canonical": str(prolog_view.get("head_canonical", "")).strip(),
        "component_nots": component_nots,
        "composed_not": composed_not,
        "lookup_keys": lookup_keys,
        "notation_yaml": notation_yaml,
    }
