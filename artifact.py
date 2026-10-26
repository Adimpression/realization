# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

import yaml

from applied_theory_types import (
    PURE_THEORY_TYPES_ENABLED,
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BoundaryShapeTerm,
    ControllerFeatureToggles,
    LearningRelation,
    PureTheoryAbilityArtifact,
    PureTheoryCapabilityArtifact,
    PureTheoryClosurePatternArtifact,
    PureTheoryCompositionArtifact,
    PureTheoryDutyTemplateArtifact,
    PureTheoryEvaluationArtifact,
    PureTheoryKnowledgeArtifact,
    PureTheoryRejectionPatternArtifact,
    PureTheoryTemplateSchema,
    PureTheoryUncertaintyPatternArtifact,
    enum_text,
    json_safe,
    utc_now,
)
from boundary import infer_function_bit
from fallback_not_generation import fallback_not_elaboration_for_text
from non_achievedness_normalization import normalize_not_elaboration_payload
from normalization_primitives import (
    boundary_shape_values,
    normalize_artifact_admission,
    normalize_artifact_representation,
    normalize_artifact_reuse,
    normalize_artifact_type,
    normalize_boundary_shape,
    normalize_learning_relation,
    normalize_notation_entries,
    normalize_notation_key,
    normalize_notation_text,
)
from semantic_text import (
    learning_core_tokens,
    learning_lookup_keys,
    normalize_semantic_component_title,
    ordered_unique,
    titleize_semantic_unit,
)


STRUCTURED_LEARNING_EXTRA_FIELDS = (
    "title_identity",
    "goal",
    "intended_object",
    "success_criteria",
    "actual_realization",
    "givens",
    "unknowns",
    "missing_components",
    "distorted_components",
    "differentiators",
    "contrastive_cases",
    "risk_of_wrong_closure",
    "disallowed_assumptions",
    "misalignment_types",
    "origin_layers",
    "degree",
    "remainder_shapes",
    "why_it_matters",
    "minimal_repair",
    "full_repair",
    "boundary_shape",
    "action_posture",
    "title_depth_segments",
    "title_depth_prefixes",
    "title_depth_exposed_depth",
    "title_depth_minimal_sufficient_depth",
    "title_depth_assessment",
    "title_depth_hidden_depth_note",
    "title_depth_body_split_needed",
    "title_depth_body_split_reason",
    "title_depth_reuse_bias",
    "title_similar_identities",
    "title_representation_mode",
    "title_prolog_head",
    "title_prolog_body",
    "title_prolog_predicate",
    "title_prolog_arity",
    "title_prolog_head_canonical",
)


def pure_theory_template_schema_from_runtime(schema: Mapping[str, Any]) -> Any | None:
    """Validate a runtime mapping as a pure-theory template schema."""
    if not PURE_THEORY_TYPES_ENABLED or PureTheoryTemplateSchema is None:
        return None
    if not isinstance(schema, Mapping) or not schema:
        return None
    payload = dict(schema)
    payload.setdefault("id", str(payload.get("id") or "runtime-template-schema"))
    try:
        return PureTheoryTemplateSchema.model_validate(payload)
    except Exception:
        return None


class _ArtifactYamlDumper(yaml.SafeDumper):
    pass


def _artifact_yaml_str_presenter(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact yaml str presenter.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_ArtifactYamlDumper.add_representer(str, _artifact_yaml_str_presenter)


def yaml_dump_human(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling yaml dump human.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    return yaml.dump(
        value,
        Dumper=_ArtifactYamlDumper,
        sort_keys=False,
        allow_unicode=False,
        default_flow_style=False,
    ).strip()


def yaml_dump_storage(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling yaml dump storage.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    if value in (None, "", [], {}):
        return ""
    return yaml.safe_dump(
        value,
        sort_keys=False,
        allow_unicode=False,
        default_flow_style=False,
    ).strip()


def yaml_load_storage(text: Any, *, default: Any = None) -> Any:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling yaml load storage.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    raw = str(text or "").strip()
    if not raw:
        return default
    try:
        value = yaml.safe_load(raw)
    except Exception:
        return default
    if value is None:
        return default
    return value


def build_pure_theory_artifact_projection(artifact: Artifact) -> Any | None:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with building pure theory artifact projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_pure_theory_artifact_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `build_pure_theory_artifact_projection`. Expected type: `Artifact`.

    Returns:
        Any | None: Result produced by `build_pure_theory_artifact_projection`.
    """
    if not PURE_THEORY_TYPES_ENABLED:
        return None
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    common = {
        "id": artifact.id,
        "representation": artifact.representation,
        "scope": artifact.scope,
        "boundary_shape": [term.value for term in artifact.boundary_shape],
        "provenance_ids": list(artifact.provenance),
        "reusability": artifact.reusability,
        "justification": artifact.justification,
        "admissibility_conditions": list(artifact.constraints),
        "related_artifact_ids": list(artifact.related_artifact_ids),
    }
    try:
        if artifact.artifact_type == ArtifactType.KNOWLEDGE.value and PureTheoryKnowledgeArtifact is not None:
            return PureTheoryKnowledgeArtifact(
                **common,
                domain_content=str(content.get("answer", "")).strip() or artifact.title,
                citations=[str(content.get("source_path", "")).strip()] if str(content.get("source_path", "")).strip() else [],
                index_terms=ordered_unique(
                    [artifact.title, *learning_lookup_keys(str(content.get("question", "")).strip() or artifact.title)]
                )[:16],
            )

        template_schema = pure_theory_template_schema_from_runtime(artifact.template_schema)
        if template_schema is None:
            return None

        if artifact.artifact_type == ArtifactType.ABILITY.value and PureTheoryAbilityArtifact is not None:
            return PureTheoryAbilityArtifact(
                **common,
                artifact_type=ArtifactType.ABILITY.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                executable_form=str(content.get("python_script", "")).strip() or str(content.get("entrypoint", "")).strip() or artifact.title,
                failure_modes=[str(item).strip() for item in content.get("failure_modes", []) if str(item).strip()] if isinstance(content.get("failure_modes", []), list) else [],
                evaluation_artifact_ids=[str(item).strip() for item in content.get("evaluation_artifact_ids", []) if str(item).strip()] if isinstance(content.get("evaluation_artifact_ids", []), list) else [],
            )
        if artifact.artifact_type == ArtifactType.CAPABILITY.value and PureTheoryCapabilityArtifact is not None:
            input_form = json.dumps(content.get("input_contract", {}), sort_keys=True) if isinstance(content.get("input_contract", {}), Mapping) else str(content.get("input_form", "")).strip()
            output_form = json.dumps(content.get("output_contract", {}), sort_keys=True) if isinstance(content.get("output_contract", {}), Mapping) else str(content.get("output_form", "")).strip()
            return PureTheoryCapabilityArtifact(
                **common,
                artifact_type=ArtifactType.CAPABILITY.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                input_form=input_form or artifact.title,
                output_form=output_form or artifact.scope,
                affordance=str(content.get("affordance", "")).strip() or artifact.title,
                limits=dict(content.get("limits", {})) if isinstance(content.get("limits", {}), Mapping) else {},
                relation_to_evidence=str(content.get("relation_to_evidence", "")).strip(),
                implementing_ability_artifact_id=str(content.get("implementing_ability_artifact_id", "")).strip() or None,
            )
        if artifact.artifact_type == ArtifactType.DUTY_TEMPLATE.value and PureTheoryDutyTemplateArtifact is not None:
            return PureTheoryDutyTemplateArtifact(
                **common,
                artifact_type=ArtifactType.DUTY_TEMPLATE.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                applicability_conditions=[str(item).strip() for item in content.get("applicability_conditions", []) if str(item).strip()] if isinstance(content.get("applicability_conditions", []), list) else list(template_schema.preconditions),
                parameter_schema=dict(content.get("parameter_schema", {})) if isinstance(content.get("parameter_schema", {}), Mapping) else {},
                expected_evidence_forms=[str(item).strip() for item in content.get("expected_evidence_forms", []) if str(item).strip()] if isinstance(content.get("expected_evidence_forms", []), list) else [],
                closure_conditions=[str(item).strip() for item in content.get("closure_conditions", []) if str(item).strip()] if isinstance(content.get("closure_conditions", []), list) else list(template_schema.completion_conditions),
                escalation_conditions=[str(item).strip() for item in content.get("escalation_conditions", []) if str(item).strip()] if isinstance(content.get("escalation_conditions", []), list) else [],
                rejection_conditions=[str(item).strip() for item in content.get("rejection_conditions", []) if str(item).strip()] if isinstance(content.get("rejection_conditions", []), list) else [],
            )
        if artifact.artifact_type == ArtifactType.CLOSURE_PATTERN.value and PureTheoryClosurePatternArtifact is not None:
            return PureTheoryClosurePatternArtifact(
                **common,
                artifact_type=ArtifactType.CLOSURE_PATTERN.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                supported_not_classes=[artifact.title],
                closure_structures=[str(content.get("answer", "")).strip() or artifact.justification],
            )
        if artifact.artifact_type == ArtifactType.REJECTION_PATTERN.value and PureTheoryRejectionPatternArtifact is not None:
            return PureTheoryRejectionPatternArtifact(
                **common,
                artifact_type=ArtifactType.REJECTION_PATTERN.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                insufficiency_patterns=list(artifact.constraints),
                rejection_structures=[str(content.get("answer", "")).strip() or artifact.justification],
            )
        if artifact.artifact_type == ArtifactType.UNCERTAINTY_PATTERN.value and PureTheoryUncertaintyPatternArtifact is not None:
            return PureTheoryUncertaintyPatternArtifact(
                **common,
                artifact_type=ArtifactType.UNCERTAINTY_PATTERN.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                ambiguity_signatures=[str(item).strip() for item in content.get("ambiguity_signatures", []) if str(item).strip()] if isinstance(content.get("ambiguity_signatures", []), list) else [],
                evidence_gap_signatures=[str(item).strip() for item in content.get("evidence_gap_signatures", []) if str(item).strip()] if isinstance(content.get("evidence_gap_signatures", []), list) else [],
                blocker_signatures=[str(item).strip() for item in content.get("blocker_signatures", []) if str(item).strip()] if isinstance(content.get("blocker_signatures", []), list) else list(artifact.constraints),
                stale_holdon_signatures=[str(item).strip() for item in content.get("stale_holdon_signatures", []) if str(item).strip()] if isinstance(content.get("stale_holdon_signatures", []), list) else [],
            )
        if artifact.artifact_type == ArtifactType.COMPOSITION.value and PureTheoryCompositionArtifact is not None:
            expected_harvest: list[ArtifactType] = []
            if isinstance(content.get("expected_harvest_artifacts", []), list):
                for item in content.get("expected_harvest_artifacts", []):
                    normalized = normalize_artifact_type(item, default="")
                    if normalized:
                        expected_harvest.append(ArtifactType(normalized))
            return PureTheoryCompositionArtifact(
                **common,
                artifact_type=ArtifactType.COMPOSITION.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                governing_duty_family=str(content.get("governing_duty_family", "")).strip(),
                admissible_duty_templates=[str(item).strip() for item in content.get("admissible_duty_templates", []) if str(item).strip()] if isinstance(content.get("admissible_duty_templates", []), list) else [],
                required_capabilities=[str(item).strip() for item in content.get("required_capabilities", []) if str(item).strip()] if isinstance(content.get("required_capabilities", []), list) else [],
                preferred_closure_patterns=[str(item).strip() for item in content.get("preferred_closure_patterns", []) if str(item).strip()] if isinstance(content.get("preferred_closure_patterns", []), list) else [],
                relevant_rejection_patterns=[str(item).strip() for item in content.get("relevant_rejection_patterns", []) if str(item).strip()] if isinstance(content.get("relevant_rejection_patterns", []), list) else [],
                relevant_uncertainty_patterns=[str(item).strip() for item in content.get("relevant_uncertainty_patterns", []) if str(item).strip()] if isinstance(content.get("relevant_uncertainty_patterns", []), list) else [],
                expected_harvest_artifacts=expected_harvest,
            )
        if artifact.artifact_type == ArtifactType.EVALUATION.value and PureTheoryEvaluationArtifact is not None:
            return PureTheoryEvaluationArtifact(
                **common,
                artifact_type=ArtifactType.EVALUATION.value,
                template_schema=template_schema,
                failure_or_escalation_behavior=list(template_schema.failure_conditions),
                criteria=[str(item).strip() for item in content.get("criteria", []) if str(item).strip()] if isinstance(content.get("criteria", []), list) else list(artifact.constraints),
                test_forms=[str(item).strip() for item in content.get("test_forms", []) if str(item).strip()] if isinstance(content.get("test_forms", []), list) else [],
                score_functions=[str(item).strip() for item in content.get("score_functions", []) if str(item).strip()] if isinstance(content.get("score_functions", []), list) else [],
                reuse_quality_checks=[str(item).strip() for item in content.get("reuse_quality_checks", []) if str(item).strip()] if isinstance(content.get("reuse_quality_checks", []), list) else [],
            )
    except Exception:
        return None
    return None


def yaml_string_list(value: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling yaml string list.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory.

    Example Input Output:
        Input: `yaml_string_list(value=3)`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        value: Value for `value` used by `yaml_string_list`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `yaml_string_list`.
    """
    if isinstance(value, list):
        normalized: list[str] = []
        for item in value:
            if isinstance(item, Mapping) and len(item) == 1:
                key, inner_value = next(iter(item.items()))
                text = f"{key}: {inner_value}"
            else:
                text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    return []


def contract_mapping_from_entries(entries: Iterable[str], *, prefix: str) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling contract mapping from entries.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory.

    Example Input Output:
        Input: `contract_mapping_from_entries(entries=['mass', 'acceleration', 'force'], prefix='Physics / Force / Force From Mass And Acceleration')`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

    Args:
        entries: Value for `entries` used by `contract_mapping_from_entries`. Expected type: `Iterable[str]`.
        prefix: Value for `prefix` used by `contract_mapping_from_entries`. Expected type: `str`.

    Returns:
        dict[str, str]: Result produced by `contract_mapping_from_entries`.
    """
    mapping: dict[str, str] = {}
    fallback_index = 1
    for entry in entries:
        text = str(entry).strip()
        if not text:
            continue
        if ":" in text:
            key, value = text.split(":", 1)
            normalized_key = str(key).strip()
            normalized_value = str(value).strip()
            if normalized_key and normalized_value:
                mapping[normalized_key] = normalized_value
                continue
        mapping[f"{prefix}_{fallback_index}"] = text
        fallback_index += 1
    return mapping


def artifact_structured_learning_from_content(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact structured learning from content.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_structured_learning_from_content(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_structured_learning_from_content`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_structured_learning_from_content`.
    """
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    structured = content.get("structured_learning", {})
    title_source_text = str(content.get("formal_title_identity", "") or artifact.title or "").strip()
    question_source_text = str(content.get("question", "")).strip()
    source_text = title_source_text or question_source_text
    fallback = fallback_not_elaboration_for_text(
        source_text,
        boundary_shape=artifact.boundary_shape,
        title_identity=title_source_text or artifact.title,
    )
    question_lookup_keys = learning_lookup_keys(question_source_text) if question_source_text else []
    if isinstance(structured, Mapping):
        if any(
            structured.get(key) not in (None, "", [], {})
            for key in (
                "encountered_not",
                "title_identity",
                "goal",
                "lookup_keys",
                "component_nots",
                "composed_not",
                *STRUCTURED_LEARNING_EXTRA_FIELDS,
            )
        ):
            normalized = normalize_not_elaboration_payload(
                source_text,
                structured,
                boundary_shape=artifact.boundary_shape,
                related_artifact_titles=[],
                title_identity=title_source_text or artifact.title,
            )
            normalized["lookup_keys"] = ordered_unique(
                list(normalized.get("lookup_keys", []))
                + list(fallback.get("lookup_keys", []))
                + list(question_lookup_keys)
            )[:24]
            normalized["component_nots"] = ordered_unique(
                list(normalized.get("component_nots", [])) + list(fallback.get("component_nots", []))
            )[:6]
            if not str(normalized.get("composed_not", "")).strip():
                normalized["composed_not"] = str(fallback.get("composed_not", "")).strip()
            return normalized
    fallback["lookup_keys"] = ordered_unique(
        list(fallback.get("lookup_keys", [])) + list(question_lookup_keys)
    )[:24]
    return fallback


def artifact_export_in_entries(artifact: Artifact) -> list[str]:
    """Return the artifact inputs used by notation and side-channel exports."""
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    if artifact.artifact_type == "ability":
        input_titles = content.get("input_titles", {})
        if isinstance(input_titles, Mapping) and input_titles:
            return [
                str(value).strip()
                for value in input_titles.values()
                if str(value).strip()
            ]
        input_contract = content.get("input_contract", {})
        if isinstance(input_contract, Mapping) and input_contract:
            lines: list[str] = []
            for key, value in input_contract.items():
                if isinstance(value, list):
                    lines.extend(f"{key}: {item}" for item in value if str(item).strip())
                else:
                    lines.append(f"{key}: {value}")
            return lines
    structured = artifact_structured_learning_from_content(artifact)
    component_nots = yaml_string_list(structured.get("component_nots", []))
    if component_nots:
        return component_nots
    question = str(content.get("question", "")).strip()
    return [question] if question and question != artifact.title else []


def artifact_export_out_entries(artifact: Artifact) -> list[str]:
    """Return the artifact outputs used by notation and side-channel exports."""
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    if artifact.artifact_type == "ability":
        output_titles = content.get("output_titles", {})
        if isinstance(output_titles, Mapping) and output_titles:
            return [
                str(value).strip()
                for value in output_titles.values()
                if str(value).strip()
            ]
        output_contract = content.get("output_contract", {})
        if isinstance(output_contract, Mapping) and output_contract:
            lines: list[str] = []
            for key, value in output_contract.items():
                if isinstance(value, list):
                    lines.extend(f"{key}: {item}" for item in value if str(item).strip())
                else:
                    lines.append(f"{key}: {value}")
            return lines
    answer = str(content.get("answer", "")).strip()
    if answer:
        return [answer]
    return []


def artifact_notation_projection(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact notation projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_notation_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_notation_projection`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_notation_projection`.
    """
    key_text = normalize_notation_text(artifact.title)
    in_entries = normalize_notation_entries(artifact_export_in_entries(artifact))
    out_entries = normalize_notation_entries(artifact_export_out_entries(artifact))
    return {
        "notation_key": key_text,
        "notation_key_normalized": normalize_notation_key(key_text),
        "notation_in_entries": in_entries,
        "notation_in_json": json.dumps(in_entries, sort_keys=True),
        "notation_in_blob": " | ".join(item.casefold() for item in in_entries),
        "notation_out_entries": out_entries,
        "notation_out_json": json.dumps(out_entries, sort_keys=True),
        "notation_out_blob": " | ".join(item.casefold() for item in out_entries),
    }


def artifact_boundary_shape_projection(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact boundary shape projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_boundary_shape_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_boundary_shape_projection`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_boundary_shape_projection`.
    """
    entries = list(boundary_shape_values(artifact.boundary_shape, default=()))
    return {
        "boundary_shape_entries": entries,
        "boundary_shape_blob": " | ".join(entries),
    }


ARTIFACT_DETAIL_SCALAR_FIELDS = (
    "question",
    "answer",
    "source_path",
    "source_document",
    "entrypoint",
    "script_language",
    "python_script",
    "input_form",
    "output_form",
    "affordance",
    "relation_to_evidence",
    "implementing_ability_artifact_id",
    "output_field",
    "compute_expression",
    "validation_check",
)

ARTIFACT_DETAIL_YAML_FIELDS = (
    "limits",
    "parameter_aliases",
    "default_invocation_payload",
)

ARTIFACT_DETAIL_LIST_FIELDS = (
    "aliases",
    "dependencies",
)


def normalized_text_items(entries: Iterable[Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling normalized text items.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory.

    Example Input Output:
        Input: `normalized_text_items(entries=['mass', 'acceleration', 'force'])`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        entries: Value for `entries` used by `normalized_text_items`. Expected type: `Iterable[Any]`.

    Returns:
        list[str]: Result produced by `normalized_text_items`.
    """
    normalized: list[str] = []
    for item in entries:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return ordered_unique(normalized)


def artifact_list_item_rows(entries: Iterable[Any]) -> list[tuple[int, str]]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact list item rows.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_list_item_rows(entries=['mass', 'acceleration', 'force'])`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        entries: Value for `entries` used by `artifact_list_item_rows`. Expected type: `Iterable[Any]`.

    Returns:
        list[tuple[int, str]]: Result produced by `artifact_list_item_rows`.
    """
    rows: list[tuple[int, str]] = []
    for index, item in enumerate(normalized_text_items(entries)):
        rows.append((index, item))
    return rows


def artifact_contract_rows(contract: Mapping[str, Any] | None) -> list[tuple[int, str, str]]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact contract rows.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_contract_rows(contract={'inputs': ['mass', 'acceleration'], 'output': 'force'})`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        contract: Value for `contract` used by `artifact_contract_rows`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        list[tuple[int, str, str]]: Result produced by `artifact_contract_rows`.
    """
    if not isinstance(contract, Mapping):
        return []
    rows: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for key, value in contract.items():
        key_text = str(key).strip()
        if not key_text or key_text in seen:
            continue
        seen.add(key_text)
        rows.append((len(rows), key_text, yaml_dump_storage(value)))
    return rows


def artifact_structured_learning_projection(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact structured learning projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_structured_learning_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_structured_learning_projection`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_structured_learning_projection`.
    """
    structured = artifact_structured_learning_from_content(artifact)
    encountered_not = ""
    lookup_keys: list[str] = []
    component_nots: list[str] = []
    composed_not = ""
    if isinstance(structured, Mapping):
        encountered_not = titleize_semantic_unit(str(structured.get("encountered_not", "")).strip())
        lookup_keys = ordered_unique(
            str(item).strip().lower()
            for item in structured.get("lookup_keys", [])
            if str(item).strip()
        ) if isinstance(structured.get("lookup_keys", []), list) else []
        component_nots = ordered_unique(
            normalize_semantic_component_title(str(item))
            for item in structured.get("component_nots", [])
            if normalize_semantic_component_title(str(item))
        ) if isinstance(structured.get("component_nots", []), list) else []
        composed_not = normalize_semantic_component_title(str(structured.get("composed_not", "")).strip())

    if not encountered_not:
        source_text = str(artifact.content.get("question", "")).strip() if isinstance(artifact.content, Mapping) else ""
        source_text = source_text or artifact.title
        encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(source_text))) or titleize_semantic_unit(source_text)
    if not lookup_keys:
        source_text = str(artifact.content.get("question", "")).strip() if isinstance(artifact.content, Mapping) else ""
        source_text = source_text or artifact.title
        lookup_keys = learning_lookup_keys(source_text)

    return {
        "encountered_not": encountered_not,
        "lookup_keys": lookup_keys,
        "component_nots": component_nots,
        "composed_not": composed_not,
    }


def artifact_template_schema_projection(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact template schema projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_template_schema_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_template_schema_projection`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_template_schema_projection`.
    """
    schema = dict(artifact.template_schema) if isinstance(artifact.template_schema, Mapping) else {}
    return {
        "governed_function": str(schema.get("governed_function", "")).strip(),
        "scope_of_reuse": str(schema.get("scope_of_reuse", "")).strip(),
        "bssc_awareness_yaml": yaml_dump_storage(schema.get("bssc_awareness", {})),
        "holdon_awareness_yaml": yaml_dump_storage(schema.get("holdon_awareness", {})),
        "preconditions": normalized_text_items(schema.get("preconditions", [])),
        "completion_conditions": normalized_text_items(schema.get("completion_conditions", [])),
        "failure_conditions": normalized_text_items(schema.get("failure_conditions", [])),
    }


def artifact_normalized_projection(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact normalized projection.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_normalized_projection(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_normalized_projection`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_normalized_projection`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    structured_projection = artifact_structured_learning_projection(artifact)
    raw_structured = content.get("structured_learning", {})

    scalar_detail: dict[str, str] = {}
    for key in ARTIFACT_DETAIL_SCALAR_FIELDS:
        value = content.pop(key, None)
        text = str(value).strip() if value not in (None, [], {}) else ""
        if text:
            scalar_detail[key] = text

    yaml_detail: dict[str, str] = {}
    for key in ARTIFACT_DETAIL_YAML_FIELDS:
        dumped = yaml_dump_storage(content.pop(key, None))
        if dumped:
            yaml_detail[key] = dumped

    list_detail: dict[str, list[str]] = {}
    for key in ARTIFACT_DETAIL_LIST_FIELDS:
        value = content.pop(key, [])
        if isinstance(value, list):
            normalized = normalized_text_items(value)
            if normalized:
                list_detail[key] = normalized

    input_contract = dict(content.pop("input_contract", {})) if isinstance(content.get("input_contract", {}), Mapping) else {}
    output_contract = dict(content.pop("output_contract", {})) if isinstance(content.get("output_contract", {}), Mapping) else {}

    content.pop("structured_learning", None)

    extra_content: dict[str, Any] = {}
    if isinstance(raw_structured, Mapping):
        structured_extras = {
            key: json_safe(raw_structured.get(key))
            for key in STRUCTURED_LEARNING_EXTRA_FIELDS
            if raw_structured.get(key) not in (None, "", [], {})
        }
        if structured_extras:
            extra_content["structured_learning_extras"] = structured_extras
    for key, value in content.items():
        if value in (None, "", [], {}):
            continue
        extra_content[str(key)] = json_safe(value)

    return {
        "scalar_detail": scalar_detail,
        "yaml_detail": yaml_detail,
        "list_detail": list_detail,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "extra_content_yaml": yaml_dump_storage(extra_content),
        "structured": structured_projection,
        "template": artifact_template_schema_projection(artifact),
    }


def artifact_build_from_normalized(
    *,
    artifact_id: str,
    artifact_type: Any,
    representation: Any,
    function_bit: Any,
    title: str,
    scope: str,
    provenance: list[str],
    reusability: Any,
    admissibility: Any,
    template_schema: Mapping[str, Any],
    learning_relation: Any,
    related_artifact_ids: list[str],
    content: Mapping[str, Any],
    justification: str,
    boundary_shape: Iterable[BoundaryShapeTerm | str],
    constraints: list[str],
    created_at: str,
) -> Artifact:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact build from normalized.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_build_from_normalized(artifact_id='artifact-force', artifact_type=3, representation=3, function_bit=3)`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        artifact_id: Value for `artifact_id` used by `artifact_build_from_normalized`. Expected type: `str`.
        artifact_type: Value for `artifact_type` used by `artifact_build_from_normalized`. Expected type: `Any`.
        representation: Value for `representation` used by `artifact_build_from_normalized`. Expected type: `Any`.
        function_bit: Value for `function_bit` used by `artifact_build_from_normalized`. Expected type: `Any`.
        title: Value for `title` used by `artifact_build_from_normalized`. Expected type: `str`.
        scope: Value for `scope` used by `artifact_build_from_normalized`. Expected type: `str`.
        provenance: Value for `provenance` used by `artifact_build_from_normalized`. Expected type: `list[str]`.
        reusability: Value for `reusability` used by `artifact_build_from_normalized`. Expected type: `Any`.
        admissibility: Value for `admissibility` used by `artifact_build_from_normalized`. Expected type: `Any`.
        template_schema: Value for `template_schema` used by `artifact_build_from_normalized`. Expected type: `Mapping[str, Any]`.
        learning_relation: Value for `learning_relation` used by `artifact_build_from_normalized`. Expected type: `Any`.
        related_artifact_ids: Value for `related_artifact_ids` used by `artifact_build_from_normalized`. Expected type: `list[str]`.
        content: Value for `content` used by `artifact_build_from_normalized`. Expected type: `Mapping[str, Any]`.
        justification: Value for `justification` used by `artifact_build_from_normalized`. Expected type: `str`.
        boundary_shape: Value for `boundary_shape` used by `artifact_build_from_normalized`. Expected type: `Iterable[BoundaryShapeTerm | str]`.
        constraints: Value for `constraints` used by `artifact_build_from_normalized`. Expected type: `list[str]`.
        created_at: Value for `created_at` used by `artifact_build_from_normalized`. Expected type: `str`.

    Returns:
        Artifact: Result produced by `artifact_build_from_normalized`.
    """
    return Artifact(
        id=str(artifact_id).strip(),
        artifact_type=normalize_artifact_type(artifact_type, default=ArtifactType.KNOWLEDGE),
        title=str(title).strip(),
        representation=normalize_artifact_representation(representation, artifact_type=artifact_type),
        function_bit=infer_function_bit(
            artifact_type=artifact_type,
            representation=representation,
            content=content,
            explicit=function_bit,
        ),
        scope=str(scope).strip(),
        provenance=normalized_text_items(provenance),
        reusability=normalize_artifact_reuse(reusability, default=ArtifactReuse.LOCAL_REUSE),
        admissibility=normalize_artifact_admission(admissibility, default=ArtifactAdmission.CANDIDATE),
        template_schema=dict(template_schema or {}),
        learning_relation=normalize_learning_relation(learning_relation, default=LearningRelation.NEW_FAMILY),
        related_artifact_ids=normalized_text_items(related_artifact_ids),
        content=dict(content or {}),
        justification=str(justification).strip(),
        boundary_shape=normalize_boundary_shape(boundary_shape, default=(BoundaryShapeTerm.OUTPUT_VALUE,)),
        constraints=normalized_text_items(constraints),
        created_at=str(created_at).strip() or utc_now(),
    )


def artifact_compatibility_payload(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with building payload data for artifact compatibility.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_compatibility_payload(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_compatibility_payload`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_compatibility_payload`.
    """
    payload = {
        "id": artifact.id,
        "artifact_type": enum_text(artifact.artifact_type),
        "title": artifact.title,
        "representation": enum_text(artifact.representation),
        "function_bit": int(artifact.function_bit or 0),
        "scope": artifact.scope,
        "reusability": enum_text(artifact.reusability),
        "admissibility": enum_text(artifact.admissibility),
        "learning_relation": enum_text(artifact.learning_relation),
        "justification": artifact.justification,
        "boundary_shape": [term.value for term in artifact.boundary_shape],
        "created_at": artifact.created_at,
        "storage_mode": "normalized_tables",
        "normalized_tables": {
            "detail": "bssc_artifact_detail",
            "notation_in": "bssc_artifact_in_items",
            "notation_out": "bssc_artifact_out_items",
            "boundary_shape": "bssc_artifact_boundary_shape_terms",
        },
    }
    controller_features = artifact.content.get("controller_features", {}) if isinstance(artifact.content, Mapping) else {}
    if isinstance(controller_features, Mapping):
        payload["controller_features"] = ControllerFeatureToggles.from_dict(dict(controller_features)).to_dict()
    return payload


def notation_item_rows(entries: Iterable[Any]) -> list[tuple[int, str, str]]:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling notation item rows.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory.

    Example Input Output:
        Input: `notation_item_rows(entries=['mass', 'acceleration', 'force'])`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        entries: Value for `entries` used by `notation_item_rows`. Expected type: `Iterable[Any]`.

    Returns:
        list[tuple[int, str, str]]: Result produced by `notation_item_rows`.
    """
    rows: list[tuple[int, str, str]] = []
    for index, item in enumerate(normalize_notation_entries(entries)):
        rows.append((index, item, normalize_notation_key(item)))
    return rows


def artifact_with_id(artifact: Artifact, artifact_id: str) -> Artifact:
    """
    High Level Purpose:
        In circumstances like artifact shaping, projection, serialization, and boundary interpretation, helps with handling artifact with id.

    Reference to Theory:
        Shapes artifact-level semantic identities, achievedness records, inputs, outputs, and reusable artifact boundaries in line with the applied theory. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_with_id(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), artifact_id='artifact-force')`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        artifact: Value for `artifact` used by `artifact_with_id`. Expected type: `Artifact`.
        artifact_id: Value for `artifact_id` used by `artifact_with_id`. Expected type: `str`.

    Returns:
        Artifact: Result produced by `artifact_with_id`.
    """
    if artifact.id == artifact_id:
        return artifact
    payload = artifact.to_dict()
    payload["id"] = artifact_id
    return Artifact.from_dict(payload)
