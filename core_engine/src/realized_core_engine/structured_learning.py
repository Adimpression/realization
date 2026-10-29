# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json

from realized_core_semantics.semantic_text import collapse_ws, titleize_semantic_unit
from realized_core_semantics.title_semantics import derive_semantic_title_depth_view


def yaml_quoted_scalar(value: str) -> str:
    """
    High Level Purpose:
        In circumstances like serializing structured-learning declarations into a YAML-like notation block, helps with emitting a safely quoted scalar surface for description and contract lines.

    Reference to Theory:
        Supports the applied decomposition and reuse flow by rendering the controller's structured-learning declaration into a stable portable surface.

    Example Input Output:
        Input: `yaml_quoted_scalar(value='Encountered non-achievedness: Force From Mass And Acceleration')`
        Output: '\"Encountered non-achievedness: Force From Mass And Acceleration\"'

    Args:
        value: Value for `value` used by `yaml_quoted_scalar`. Expected type: `str`.

    Returns:
        str: Result produced by `yaml_quoted_scalar`.
    """
    return json.dumps(value)


def render_structured_learning_yaml(
    semantic_unit: str,
    *,
    encountered_not: str,
    component_nots: list[str],
    composed_not: str,
    related_artifact_titles: list[str],
    title_identity: str = "",
    title_depth_segments: list[str] | None = None,
    title_depth_prefixes: list[str] | None = None,
    title_depth_exposed_depth: int | None = None,
    title_depth_minimal_sufficient_depth: int | None = None,
    title_depth_assessment: str = "",
    title_depth_hidden_depth_note: str = "",
    title_depth_body_split_needed: bool | None = None,
    title_depth_body_split_reason: str = "",
    title_depth_reuse_bias: str = "",
    title_similar_identities: list[str] | None = None,
    intended_object: str = "",
    success_criteria: list[str] | None = None,
    actual_realization: str = "",
    givens: list[str] | None = None,
    unknowns: list[str] | None = None,
    missing_components: list[str] | None = None,
    distorted_components: list[str] | None = None,
    differentiators: list[str] | None = None,
    contrastive_cases: list[str] | None = None,
    risk_of_wrong_closure: list[str] | None = None,
    disallowed_assumptions: list[str] | None = None,
    misalignment_types: list[str] | None = None,
    origin_layers: list[str] | None = None,
    degree: str = "",
    remainder_shapes: list[str] | None = None,
    why_it_matters: list[str] | None = None,
    minimal_repair: list[str] | None = None,
    full_repair: list[str] | None = None,
    action_posture: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like persisting a fallback non-achievedness declaration or exporting normalized structured-learning state, helps with rendering the semantic declaration into a stable YAML-like text block.

    Reference to Theory:
        Supports the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8, by serializing the inferred semantic structure into a portable declaration surface.

    Example Input Output:
        Input: `render_structured_learning_yaml(semantic_unit='Physics / Force / Force From Mass And Acceleration', encountered_not='Force From Mass And Acceleration', component_nots=['Force', 'Mass', 'Acceleration'], composed_not='Force From Mass And Acceleration', related_artifact_titles=['Physics / Multiplicative Combination'], title_identity='Physics / Force / Force From Mass And Acceleration', intended_object='force', success_criteria=['state the governing law faithfully'], actual_realization='the prompt surface is present', action_posture='direct_resolution')`
        Output: '\"Physics Force Force From Mass And Acceleration\":\\n  Description:\\n    - \"Structured learning declaration for the active non-achievedness.\"\\n    - \"Encountered non-achievedness: Force From Mass And Acceleration\"\\n    - \"Components: Force, Mass, Acceleration\"\\n    - \"Composition: Force From Mass And Acceleration\"\\n    - \"Title identity: Physics / Force / Force From Mass And Acceleration\"\\n    - \"Intended object: force\"\\n    - \"Success criteria: state the governing law faithfully\"\\n    - \"Actual realization: the prompt surface is present\"\\n    - \"Action posture: direct_resolution\"\\n    - \"Related artifacts: Physics / Multiplicative Combination\"\\n  In:\\n    - \"Prompt Surface String\"\\n    - \"Encountered Non Achievedness String\"\\n    - \"Lookup Keys Strings\"\\n    - \"[ Component Non Achievedness ]\"\\n    - \"Composed Non Achievedness\"\\n    - \"[ Related Artifact ]\"\\n  Out:\\n    - \"Prior Encounter\"\\n    - \"[ Reusable Artifact ]\"\\n    - \"[ Reused Non Achievedness ]\"\\n    - \"[ Composed Reuse ]\"'

    Args:
        semantic_unit: Value for `semantic_unit` used by `render_structured_learning_yaml`. Expected type: `str`.
        encountered_not: Value for `encountered_not` used by `render_structured_learning_yaml`. Expected type: `str`.
        component_nots: Value for `component_nots` used by `render_structured_learning_yaml`. Expected type: `list[str]`.
        composed_not: Value for `composed_not` used by `render_structured_learning_yaml`. Expected type: `str`.
        related_artifact_titles: Value for `related_artifact_titles` used by `render_structured_learning_yaml`. Expected type: `list[str]`.
        title_identity: Value for `title_identity` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        title_depth_segments: Value for `title_depth_segments` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        title_depth_prefixes: Value for `title_depth_prefixes` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        title_depth_exposed_depth: Value for `title_depth_exposed_depth` used by `render_structured_learning_yaml`. Expected type: `int | None`. Defaults to `None`.
        title_depth_minimal_sufficient_depth: Value for `title_depth_minimal_sufficient_depth` used by `render_structured_learning_yaml`. Expected type: `int | None`. Defaults to `None`.
        title_depth_assessment: Value for `title_depth_assessment` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        title_depth_hidden_depth_note: Value for `title_depth_hidden_depth_note` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        title_depth_body_split_needed: Value for `title_depth_body_split_needed` used by `render_structured_learning_yaml`. Expected type: `bool | None`. Defaults to `None`.
        title_depth_body_split_reason: Value for `title_depth_body_split_reason` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        title_depth_reuse_bias: Value for `title_depth_reuse_bias` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        title_similar_identities: Value for `title_similar_identities` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        intended_object: Value for `intended_object` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        success_criteria: Value for `success_criteria` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        actual_realization: Value for `actual_realization` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        givens: Value for `givens` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        unknowns: Value for `unknowns` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        missing_components: Value for `missing_components` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        distorted_components: Value for `distorted_components` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        differentiators: Value for `differentiators` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        contrastive_cases: Value for `contrastive_cases` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        risk_of_wrong_closure: Value for `risk_of_wrong_closure` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        disallowed_assumptions: Value for `disallowed_assumptions` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        misalignment_types: Value for `misalignment_types` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        origin_layers: Value for `origin_layers` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        degree: Value for `degree` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.
        remainder_shapes: Value for `remainder_shapes` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        why_it_matters: Value for `why_it_matters` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        minimal_repair: Value for `minimal_repair` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        full_repair: Value for `full_repair` used by `render_structured_learning_yaml`. Expected type: `list[str] | None`. Defaults to `None`.
        action_posture: Value for `action_posture` used by `render_structured_learning_yaml`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `render_structured_learning_yaml`.
    """
    key = titleize_semantic_unit(semantic_unit) or "Active Non Achievedness"
    title_depth_view = derive_semantic_title_depth_view(
        title_identity or semantic_unit,
        minimal_sufficient_depth=title_depth_minimal_sufficient_depth,
        assessment=title_depth_assessment,
    )
    description_items = [
        "Structured learning declaration for the active non-achievedness.",
        f"Encountered non-achievedness: {encountered_not or 'Unknown'}",
        "Components: " + (", ".join(component_nots) if component_nots else "none"),
        "Composition: " + (composed_not if composed_not else "atomic"),
    ]
    normalized_title_identity = str(title_depth_view.get("title_identity", "")).strip()
    normalized_title_segments = list(title_depth_segments or title_depth_view.get("segments", []))
    normalized_title_prefixes = list(title_depth_prefixes or title_depth_view.get("prefixes", []))
    normalized_title_exposed_depth = int(
        title_depth_exposed_depth if title_depth_exposed_depth not in (None, "") else title_depth_view.get("exposed_depth", 0)
    )
    normalized_title_minimal_depth = int(title_depth_view.get("minimal_sufficient_depth", 0))
    normalized_title_assessment = str(title_depth_view.get("assessment", "")).strip()
    if normalized_title_identity:
        description_items.append("Title identity: " + normalized_title_identity)
    if normalized_title_segments:
        description_items.append("Title depth segments: " + " -> ".join(normalized_title_segments))
    if normalized_title_prefixes:
        description_items.append("Title depth prefixes: " + " ; ".join(normalized_title_prefixes))
    if normalized_title_exposed_depth:
        description_items.append(
            "Title depth exposed/minimal sufficient: "
            + f"{normalized_title_exposed_depth}/{normalized_title_minimal_depth}"
        )
    if normalized_title_assessment:
        description_items.append("Title depth assessment: " + normalized_title_assessment)
    if collapse_ws(title_depth_hidden_depth_note):
        description_items.append("Title depth hidden-order note: " + collapse_ws(title_depth_hidden_depth_note))
    if title_depth_body_split_needed is not None:
        description_items.append("Title depth body split needed: " + ("true" if bool(title_depth_body_split_needed) else "false"))
    if collapse_ws(title_depth_body_split_reason):
        description_items.append("Title depth body split reason: " + collapse_ws(title_depth_body_split_reason))
    if collapse_ws(title_depth_reuse_bias):
        description_items.append("Title depth reuse bias: " + collapse_ws(title_depth_reuse_bias))
    if title_similar_identities:
        description_items.append("Title similar identities: " + " ; ".join(title_similar_identities[:6]))
    if intended_object:
        description_items.append("Intended object: " + intended_object)
    if success_criteria:
        description_items.append("Success criteria: " + ", ".join(success_criteria))
    if actual_realization:
        description_items.append("Actual realization: " + actual_realization)
    if givens:
        description_items.append("Givens: " + ", ".join(givens))
    if unknowns:
        description_items.append("Unknowns: " + ", ".join(unknowns))
    if missing_components:
        description_items.append("Missing components: " + ", ".join(missing_components))
    if distorted_components:
        description_items.append("Distorted components: " + ", ".join(distorted_components))
    if differentiators:
        description_items.append("Differentiators: " + ", ".join(differentiators))
    if contrastive_cases:
        description_items.append("Contrastive cases: " + ", ".join(contrastive_cases))
    if risk_of_wrong_closure:
        description_items.append("Risk of wrong closure: " + ", ".join(risk_of_wrong_closure))
    if disallowed_assumptions:
        description_items.append("Disallowed assumptions: " + ", ".join(disallowed_assumptions))
    if misalignment_types:
        description_items.append("Misalignment types: " + ", ".join(misalignment_types))
    if origin_layers:
        description_items.append("Origin layers: " + ", ".join(origin_layers))
    if degree:
        description_items.append("Degree: " + degree)
    if remainder_shapes:
        description_items.append("Remainder shapes: " + ", ".join(remainder_shapes))
    if why_it_matters:
        description_items.append("Why it matters: " + ", ".join(why_it_matters))
    if minimal_repair:
        description_items.append("Minimal repair: " + ", ".join(minimal_repair))
    if full_repair:
        description_items.append("Full repair: " + ", ".join(full_repair))
    if action_posture:
        description_items.append("Action posture: " + action_posture)
    if related_artifact_titles:
        description_items.append("Related artifacts: " + ", ".join(related_artifact_titles[:4]))
    in_entries = [
        "Prompt Surface String",
        "Encountered Non Achievedness String",
        "Lookup Keys Strings",
        "[ Component Non Achievedness ]",
    ]
    if composed_not:
        in_entries.append("Composed Non Achievedness")
    if related_artifact_titles:
        in_entries.append("[ Related Artifact ]")
    out_entries = [
        "Prior Encounter",
        "[ Reusable Artifact ]",
        "[ Reused Non Achievedness ]",
    ]
    if composed_not:
        out_entries.append("[ Composed Reuse ]")

    lines = [f"{yaml_quoted_scalar(key)}:"]
    lines.append("  Description:")
    for item in description_items:
        lines.append(f"    - {yaml_quoted_scalar(item)}")
    lines.append("  In:")
    for entry in in_entries:
        lines.append(f"    - {yaml_quoted_scalar(entry)}")
    lines.append("  Out:")
    for entry in out_entries:
        lines.append(f"    - {yaml_quoted_scalar(entry)}")
    return "\n".join(lines)
