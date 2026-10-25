# See MODULES.md for the repository module map before editing.
# Canonical implementation of the governed controller runtime.
from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request as urllib_request
from collections.abc import Mapping
from dataclasses import dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any, Iterable

from realized_core_runtime import measured_performance

from args import add_controller_feature_toggle_arguments, parse_args
from boundary import (
    boundary_shape_rank,
    boundary_shape_term_rows,
    default_boundary_shape_for_node,
    infer_artifact_boundary_shape,
    infer_function_bit,
    infer_not_boundary_shape_from_semantic_text,
    is_python_artifact_representation,
    is_template_bearing_artifact_type,
)
from artifact_answer_resolution import (
    artifact_answer_text as resolve_artifact_answer_text,
    best_invokable_artifact_candidate as resolve_best_invokable_artifact_candidate,
    derive_related_solution_support as resolve_related_solution_support,
    fallback_executable_answer_candidate as resolve_fallback_executable_answer_candidate,
)
from direct_knowledge_reuse import (
    compose_direct_knowledge_answer as compose_direct_knowledge_reuse_answer,
    focused_direct_knowledge_candidates as focused_direct_knowledge_reuse_candidates,
    persisted_direct_knowledge_candidates as persisted_direct_knowledge_reuse_candidates,
)
from external_markdown_learning_pipeline import (
    apply_markdown_batch_relations as apply_external_markdown_batch_relations,
    learn_from_markdown_document as learn_from_external_markdown_document,
    markdown_expression_artifact_payload as build_markdown_expression_artifact_payload,
)
from execution_frameworks import (
    ability_executable_text,
    ability_executor_framework,
    brokerize_python_main_for_host_brokers,
    executor_framework_representation,
    execute_cross_boundary,
    normalize_supported_executor_frameworks,
)
from fallback_not_semantics import (
    fallback_not_elaboration_for_text,
    not_elaboration_alignment_rank,
)
from host_mediation import (
    execute_mediated_artifact_effect as execute_governed_mediated_artifact_effect,
    execute_mediated_host_broker_request as execute_governed_mediated_host_broker_request,
    record_effect_trace as record_governed_effect_trace,
)
from realized_host_interaction.context import (
    HostInteractionContext,
    host_interaction_descriptor_payload,
    host_interaction_attachments,
    host_native_interaction_context,
    normalize_host_interaction_attachment_path,
    primary_host_interaction_workspace,
    resolve_host_interaction_attachment,
)
from id_generation import make_id, slugify
from markdown_learning_artifact_semantics import (
    build_markdown_knowledge_answer_from_encounter as build_markdown_knowledge_answer_from_selected_encounter,
    build_markdown_learning_artifact as build_semantic_markdown_learning_artifact,
    markdown_ability_collision_identity,
    propose_markdown_ability_learning as propose_semantic_markdown_ability_learning,
    propose_markdown_expression_synthesis as propose_semantic_markdown_expression_synthesis,
    propose_markdown_functionalization as propose_semantic_markdown_functionalization,
    propose_markdown_learning as propose_semantic_markdown_learning,
    propose_markdown_title_repair as propose_semantic_markdown_title_repair,
    select_markdown_learning_encounter as select_semantic_markdown_learning_encounter,
)
from governed_prior_learning_reuse import (
    build_immediate_learning_artifact as build_governed_immediate_learning_artifact,
    build_structured_learning_artifact as build_governed_structured_learning_artifact,
    immediate_learning_context_artifacts as governed_immediate_learning_context_artifacts,
    instantiate_reusable_artifact_support as instantiate_governed_reusable_artifact_support,
    learning_context_query_variants as governed_learning_context_query_variants,
    load_learning_context as governed_load_learning_context,
    lookup_prior_non_achievedness as lookup_governed_prior_non_achievedness,
)
from governed_closure_and_commitment import (
    commit_closure as commit_governed_closure,
    commit_incompletion as commit_governed_incompletion,
    commit_pause as commit_governed_pause,
    is_committable as is_governed_committable,
    materialize_root_product as materialize_governed_root_product,
    needs_reframing as needs_governed_reframing,
    pause_boundary_for as resolve_governed_pause_boundary,
    pause_reason as describe_governed_pause_reason,
    should_pause as should_governed_pause,
)
from governed_semantic_reduction_runtime import (
    decompose_or_refine as decompose_or_refine_governed_semantic_runtime,
    filter_by_faithfulness as filter_children_by_runtime_faithfulness,
    order_children as order_runtime_children,
    pop_best_frontier as pop_runtime_frontier_candidate,
    reduce_not as reduce_governed_not,
    refresh_frontier as refresh_governed_frontier,
    resume as resume_governed_semantic_runtime,
    runtime_host_interaction_context_payload,
    run as run_governed_semantic_runtime,
)
from artifact import (
    STRUCTURED_LEARNING_EXTRA_FIELDS,
    artifact_boundary_shape_projection,
    artifact_build_from_normalized,
    artifact_compatibility_payload,
    artifact_contract_rows,
    artifact_list_item_rows,
    artifact_normalized_projection,
    artifact_notation_projection,
    artifact_structured_learning_from_content,
    artifact_structured_learning_projection,
    artifact_template_schema_projection,
    artifact_with_id,
    build_pure_theory_artifact_projection,
    contract_mapping_from_entries,
    normalized_text_items,
    notation_item_rows,
    pure_theory_template_schema_from_runtime,
    yaml_dump_human,
    yaml_dump_storage,
    yaml_load_storage,
    yaml_string_list,
)
from applied_theory_types import (
    ABILITY_SCRIPT_DEPENDENCIES,
    ARTIFACT_TYPES,
    ARTIFACT_ADMISSION_LEVELS,
    ARTIFACT_REPRESENTATION_LEVELS,
    ARTIFACT_REUSE_LEVELS,
    BOUNDARY_OUTPUT_TERMS,
    BOUNDARY_SHAPE_TERMS,
    BOUNDARY_WRITE_TERMS,
    CLOSURE_RULE_LEVELS,
    GAIN_CLASSES,
    LEARNING_RELATIONS,
    NOT_DEGREE_VALUES,
    NOT_MISALIGNMENT_VALUES,
    NOT_ORIGIN_VALUES,
    NOT_REMAINDER_SHAPE_VALUES,
    PAIN_CLASSES,
    PRIORITY_LEVELS,
    SUPPORT_SCORE_LEVELS,
    THEORY_VERSION,
    THREE_LEVELS,
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BSSCCarrier,
    BoundaryShapeTerm,
    Capability,
    Claim,
    ClaimStance,
    ClosureRule,
    Commitment,
    ControllerFeatureToggles,
    CrossBoundaryResult,
    DecompositionMode,
    DiscoveryAudit,
    EdgeType,
    Evidence,
    EvidencePolarity,
    GainClass,
    GovernanceRules,
    GraphEdge,
    HumanContribution,
    LearningRelation,
    LLMSupplementResult,
    NodeOrigin,
    NodeStatus,
    NotDegreeKind,
    NotMisalignmentKind,
    NotOriginKind,
    NotRemainderShapeKind,
    OntologyEntry,
    PainClass,
    PauseBoundary,
    PausePoint,
    PriorityLevel,
    Product,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposedCommitment,
    ProposalType,
    PureTheoryAbilityArtifact,
    PureTheoryBSSCAwareness,
    PureTheoryCapabilityArtifact,
    PureTheoryClosurePatternArtifact,
    PureTheoryCompositionArtifact,
    PureTheoryDutyTemplateArtifact,
    PureTheoryEvaluationArtifact,
    PureTheoryGainKind,
    PureTheoryHoldOnAwareness,
    PureTheoryKnowledgeArtifact,
    PureTheoryPainKind,
    PureTheoryRejectionPatternArtifact,
    PureTheoryUncertaintyPatternArtifact,
    Result,
    RunOutcome,
    RuntimeStrEnum,
    SemanticNode,
    StepRecord,
    SupplementMode,
    SupportScore,
    SupportView,
    ThreeLevel,
    enum_text,
    json_safe,
    utc_now,
)
from normalize import (
    boundary_shape_values,
    normalize_artifact_admission,
    normalize_artifact_representation,
    normalize_artifact_reuse,
    normalize_artifact_type,
    normalize_boundary_shape,
    normalize_boundary_shape_term,
    normalize_claim_stance,
    normalize_closure_rule,
    normalize_decomposition_mode,
    normalize_evidence_polarity,
    normalize_function_bit,
    normalize_gain_class,
    normalize_learning_relation,
    normalize_node_origin,
    normalize_not_degree,
    normalize_not_elaboration_payload,
    normalize_not_misalignment_kind,
    normalize_not_misalignment_list,
    normalize_not_origin_kind,
    normalize_not_origin_list,
    normalize_notation_entries,
    normalize_notation_key,
    normalize_notation_text,
    normalize_pain_class,
    normalize_pause_boundary,
    normalize_priority,
    normalize_remainder_shape_kind,
    normalize_remainder_shape_list,
    normalize_run_outcome,
    normalize_support_score,
    normalize_three_level,
)
from markdown_ir import (
    MarkdownDocumentIR,
    MarkdownSectionIR,
    bounded_markdown_encounter_prompt_view,
    bounded_markdown_learning_prompt_view,
    compact_markdown_encounter_records,
    is_generic_synthesis_field_name,
    is_generic_synthesis_question,
    looks_like_placeholder_python_script,
    markdown_caller_facing_question,
    markdown_canonical_question,
    markdown_clean_learning_text,
    markdown_cluster_answer,
    markdown_direct_expression_mapping,
    markdown_document_clusters,
    markdown_document_symbol_aliases,
    markdown_encounter_aliases,
    markdown_encounter_question,
    markdown_learning_encounter_view,
    markdown_symbolic_mapping_from_encounter,
    merge_markdown_encounter_details,
    parse_markdown_document_ir,
)
from learn import (
    DECISION_ABSENCE_MARKERS,
    DECISION_CONFIRMATION_MARKERS,
    DECISION_UNCERTAINTY_MARKERS,
    LEARNING_DISCRIMINATOR_TOKENS,
    LEARNING_MATCH_KINDS,
    canonical_stable_fact_lookup,
)
from prolog import (
    compose_prolog_semantic_title_identity,
    derive_prolog_query_invocation_payload,
    instantiate_prolog_body_text,
    looks_like_prolog_title_identity,
    normalize_prolog_title_identity,
    parse_prolog_term,
    prolog_contract_alias_map,
    prolog_term_text,
    prolog_terms_unify,
    prolog_title_atom,
    prolog_title_display_segments,
    prolog_title_display_text,
    prolog_title_match_score,
    prolog_title_query_variants,
    prolog_title_view,
    prolog_unify_bindings,
    synthesize_prolog_formal_title_identity,
    synthesize_prolog_query_title_identity,
    split_prolog_clause,
    split_prolog_namespace,
)
from prompt_directives import (
    prompt_directive_support_markers,
    prompt_has_absence_signal,
    prompt_has_confirmation_signal,
    prompt_has_unresolved_uncertainty,
    semantic_prompt_directive_profile,
    semantic_question_focus_text,
)
from retrieval_ranking import (
    artifact_action_alignment_penalty,
    artifact_focus_alignment_score,
    artifact_is_structured_learning_record,
    artifact_output_lookup_keys,
    artifact_prompt_decision_mismatch_penalty,
    artifact_selection_text,
    artifact_surface_alignment_rank,
    artifact_text_alignment_rank,
    learning_overlap,
    output_lookup_compatible,
    ordinal_focus_markers,
    prolog_surface_alignment_rank,
    selection_signal_phrases,
    selection_signal_tokens,
    text_alignment_rank,
)
from run_outcome_harvest_and_reporting import (
    emit_trace_report as emit_run_trace_report,
    finalize_run as finalize_governed_run,
    perform_discovery_harvest as perform_run_discovery_harvest,
    persist_artifacts as persist_governed_artifacts,
)
from semantic_prompt_posture import (
    semantic_prompt_action_posture,
    semantic_prompt_prefers_direct_knowledge_answer,
    semantic_unit_allows_default_invocation_payload,
)
from semantic_text import (
    collapse_ws,
    decode_semantic_text_literal,
    learning_component_units,
    learning_core_tokens,
    learning_lookup_keys,
    normalize_semantic_component_title,
    ordered_unique,
    semantic_application_mentions,
    semantic_backticked_literals,
    semantic_bearing_level,
    semantic_chain_decomposition_components,
    semantic_destination_mount_mention,
    semantic_destination_relative_path_literal,
    semantic_mount_mentions,
    semantic_named_input_keys,
    semantic_pathlike_literals,
    semantic_relative_path_literals,
    semantic_source_mount_mention,
    semantic_source_relative_path_literal,
    semantic_requested_output_keys,
    semantic_requested_output_phrases,
    semantic_suffix_literals,
    semantic_url_literals,
    semantic_tokens,
    strip_control_chars,
    structured_learning_signal_lookup_keys,
    structured_text_list,
    titleize_semantic_unit,
)
from structured_learning_yaml import render_structured_learning_yaml, yaml_quoted_scalar
from controller_governance_bridge import (
    artifact_has_answer_capability as controller_artifact_has_answer_capability,
    artifact_is_executable_function as controller_artifact_is_executable_function,
    current_skill_governance_artifacts as controller_current_skill_governance_artifacts,
    current_skill_governance_snapshot as controller_current_skill_governance_snapshot,
    invalidate_current_skill_governance_snapshot as controller_invalidate_current_skill_governance_snapshot,
)
from side import (
    artifact_export_bundle_text,
    artifact_export_description,
    artifact_export_document,
    artifact_export_in_entries,
    artifact_export_metadata,
    artifact_export_out_entries,
    artifact_export_yaml,
    artifact_from_yaml_document,
    artifact_structured_learning_from_import,
    batch_artifact_export_filename,
    export_artifact_text,
    load_artifact_yaml,
    load_artifact_yaml_documents,
    load_batch_list,
    normalized_bundle_filename_for_source,
    resolve_export_artifact_ids,
    resolve_import_artifact_files,
    yaml_top_level_declaration,
)
from store import (
    ArtifactStore,
    EmbeddingGemmaEncoder,
    SQLiteVectorArtifactStore,
    build_artifact_store as _build_artifact_store,
)
from supplement import (
    LLMSupplement,
    llm_supplement_request_digest,
    llm_supplement_system_message,
)
from system_state import (
    RefinementGraph,
    SystemState,
)
from title_semantics import (
    PROLOG_QUERY_PRIMING_MODE_ENV,
    PROLOG_QUERY_PRIMING_MODE_FALLBACK,
    PROLOG_QUERY_PRIMING_MODE_FORCE,
    PROLOG_QUERY_PRIMING_MODE_OFF,
    TITLE_REPRESENTATION_MODE_ENV,
    TITLE_REPRESENTATION_MODE_PROLOG,
    TITLE_REPRESENTATION_MODE_SLASH,
    classify_title_depth_relation,
    compose_display_title_identity,
    compose_semantic_title_identity,
    derive_semantic_title_depth_prefix_chain,
    derive_semantic_title_depth_segments,
    derive_semantic_title_depth_view,
    display_title_leaf_text,
    normalize_markdown_title_identity,
    normalize_semantic_title_identity,
    prolog_query_priming_mode,
    semantic_namespace_key,
    semantic_title_depth_prefix_chain,
    semantic_title_display_segments,
    semantic_title_display_text,
    strip_markdown_outline_prefix,
    structured_title_identity_text,
    title_depth_theory_prompt_block,
    title_inputs_prefer_prolog_surface,
    title_representation_is_prolog,
    title_representation_mode,
)

def clamp(value: float, low: float, high: float) -> float:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with keeping a numeric value within lower and upper bounds.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `clamp(value=1.5, low=0.0, high=1.0)`
        Output: 1.0

    Args:
        value: Value for `value` used by `clamp`. Expected type: `float`.
        low: Value for `low` used by `clamp`. Expected type: `float`.
        high: Value for `high` used by `clamp`. Expected type: `float`.

    Returns:
        float: Result produced by `clamp`.
    """
    return max(low, min(high, value))


def level_rank(value: str, levels: tuple[str, str, str] = THREE_LEVELS) -> int:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling level rank.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `level_rank(value='force', levels=('Physics', 'Force'))`
        Output: 3

    Args:
        value: Value for `value` used by `level_rank`. Expected type: `str`.
        levels: Value for `levels` used by `level_rank`. Expected type: `tuple[str, str, str]`. Defaults to `THREE_LEVELS`.

    Returns:
        int: Result produced by `level_rank`.
    """
    normalized = value if value in levels else levels[0]
    return levels.index(normalized)


def max_level(values: Iterable[str], *, levels: tuple[str, str, str] = THREE_LEVELS, default: str = "low") -> str:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling max level.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `max_level(values=[3, 4, 12], levels=('Physics', 'Force'), default='force')`
        Output: 'F = m * a'

    Args:
        values: Value for `values` used by `max_level`. Expected type: `Iterable[str]`.
        levels: Value for `levels` used by `max_level`. Expected type: `tuple[str, str, str]`. Defaults to `THREE_LEVELS`.
        default: Value for `default` used by `max_level`. Expected type: `str`. Defaults to `'low'`.

    Returns:
        str: Result produced by `max_level`.
    """
    chosen = default
    for value in values:
        normalized = value if value in levels else default
        if level_rank(normalized, levels) > level_rank(chosen, levels):
            chosen = normalized
    return chosen


def min_level(values: Iterable[str], *, levels: tuple[str, str, str] = THREE_LEVELS, default: str = "high") -> str:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling min level.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `min_level(values=[3, 4, 12], levels=('Physics', 'Force'), default='force')`
        Output: 'F = m * a'

    Args:
        values: Value for `values` used by `min_level`. Expected type: `Iterable[str]`.
        levels: Value for `levels` used by `min_level`. Expected type: `tuple[str, str, str]`. Defaults to `THREE_LEVELS`.
        default: Value for `default` used by `min_level`. Expected type: `str`. Defaults to `'high'`.

    Returns:
        str: Result produced by `min_level`.
    """
    chosen = default
    for value in values:
        normalized = value if value in levels else default
        if level_rank(normalized, levels) < level_rank(chosen, levels):
            chosen = normalized
    return chosen


def level_at_least(value: str, minimum: str, *, levels: tuple[str, str, str] = THREE_LEVELS) -> bool:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling level at least.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `level_at_least(value='force', minimum='force', levels=('Physics', 'Force'))`
        Output: True

    Args:
        value: Value for `value` used by `level_at_least`. Expected type: `str`.
        minimum: Value for `minimum` used by `level_at_least`. Expected type: `str`.
        levels: Value for `levels` used by `level_at_least`. Expected type: `tuple[str, str, str]`. Defaults to `THREE_LEVELS`.

    Returns:
        bool: Result produced by `level_at_least`.
    """
    return level_rank(value, levels) >= level_rank(minimum, levels)


def semantic_phrase_surface(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like turning stored symbolic identifiers or title leaves into readable semantic phrases, helps with producing a human-readable phrase surface that can be reused inside direct explanatory answers.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_phrase_surface(text='stored_chemical_energy')`
        Output: 'Stored Chemical Energy'

    Args:
        text: Value for `text` used by `semantic_phrase_surface`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_phrase_surface`.
    """
    raw = display_title_leaf_text(collapse_ws(str(text or "").strip()))
    if not raw:
        return ""
    normalized = collapse_ws(raw.replace("_", " ").replace("-", " "))
    words = [part for part in re.findall(r"[A-Za-z0-9]+", normalized) if part]
    if not words:
        return ""
    return " ".join(word.capitalize() for word in words)


def arrow_relation_sentence(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like recovering latent knowledge from stored givens or relation hints, helps with turning compact arrow notation into a readable sentence that can supplement a direct answer.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `arrow_relation_sentence(text='So: light energy -> stored chemical energy')`
        Output: 'Light Energy becomes Stored Chemical Energy.'

    Args:
        text: Value for `text` used by `arrow_relation_sentence`. Expected type: `str`.

    Returns:
        str: Result produced by `arrow_relation_sentence`.
    """
    raw = collapse_ws(str(text or "").strip())
    if not raw:
        return ""
    cleaned = raw.replace("**", "").replace("`", "")
    if "->" in cleaned:
        left, right = cleaned.split("->", 1)
    elif "→" in cleaned:
        left, right = cleaned.split("→", 1)
    else:
        return ""
    left_phrase = semantic_phrase_surface(left)
    right_phrase = semantic_phrase_surface(right)
    if not left_phrase or not right_phrase:
        return ""
    return f"{left_phrase} becomes {right_phrase}."


def markdown_title_tokens(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown title tokens.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `markdown_title_tokens(text='Compute force from mass and acceleration.')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        text: Value for `text` used by `markdown_title_tokens`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `markdown_title_tokens`.
    """
    return [token for token in re.findall(r"[A-Za-z0-9]+", collapse_ws(text)) if token]


def extract_parenthesized_prefix(text: str) -> tuple[str, str]:
    """
    High Level Purpose:
        In circumstances like repairing malformed symbolic ratio expressions, helps with extracting the next balanced parenthesized segment from the front of a candidate expression.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `extract_parenthesized_prefix(text='( V ) * ( R )')`
        Output: (' V ', ' * ( R )')

    Args:
        text: Value for `text` used by `extract_parenthesized_prefix`. Expected type: `str`.

    Returns:
        tuple[str, str]: Result produced by `extract_parenthesized_prefix`.
    """
    source = str(text or "").lstrip()
    if not source.startswith("("):
        return "", source
    depth = 0
    for index, char in enumerate(source):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[1:index], source[index + 1 :]
    return "", source


def repair_fraction_like_expression_surface(expression: str) -> str:
    """
    High Level Purpose:
        In circumstances like execution repair for markdown-derived arithmetic laws, helps with converting malformed `frac/rac` division surfaces into executable division expressions before the controller regenerates a Python ability script.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `repair_fraction_like_expression_surface(expression='rac * ( V ) * ( R )')`
        Output: '((V) / (R))'

    Args:
        expression: Value for `expression` used by `repair_fraction_like_expression_surface`. Expected type: `str`.

    Returns:
        str: Result produced by `repair_fraction_like_expression_surface`.
    """
    normalized = collapse_ws(str(expression or "").strip())
    if not normalized:
        return ""
    normalized = re.sub(r"\\?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1) / (\2)", normalized)
    normalized = re.sub(r"(?<![A-Za-z])rac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1) / (\2)", normalized)
    normalized = re.sub(r"\\?frac\s+([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)", r"(\1) / (\2)", normalized)
    normalized = re.sub(r"(?<![A-Za-z])rac\s+([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)", r"(\1) / (\2)", normalized)
    for marker in ("frac", "rac"):
        prefix = f"{marker} * "
        if not normalized.startswith(prefix):
            continue
        left, remainder = extract_parenthesized_prefix(normalized[len(prefix):])
        if not left:
            continue
        remainder = remainder.strip()
        if not remainder.startswith("*"):
            continue
        right, tail = extract_parenthesized_prefix(remainder[1:].strip())
        if not right or tail.strip():
            continue
        return f"(({collapse_ws(left)}) / ({collapse_ws(right)}))"
    return normalized


def learning_discriminator_tokens(*texts: str) -> set[str]:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling learning discriminator tokens.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_discriminator_tokens()`
        Output: {'Physics', 'Force'}

    Args:
        *texts: Additional positional arguments forwarded by the caller. Expected type: `str`.

    Returns:
        set[str]: Result produced by `learning_discriminator_tokens`.
    """
    discriminators: set[str] = set()
    for text in texts:
        for token in learning_core_tokens(text):
            if token in LEARNING_DISCRIMINATOR_TOKENS:
                discriminators.add(token)
    return discriminators


def plain_prompt(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling plain prompt.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `plain_prompt(text='Compute force from mass and acceleration.')`
        Output: 'F = m * a'

    Args:
        text: Value for `text` used by `plain_prompt`. Expected type: `str`.

    Returns:
        str: Result produced by `plain_prompt`.
    """
    return dedent(text).strip()


def cross_boundary(
    python_script: str,
    stdin_payload: Any,
    *,
    timeout_seconds: float | None = None,
) -> CrossBoundaryResult:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling cross boundary.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `cross_boundary(python_script='Compute force from mass and acceleration.', stdin_payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, timeout_seconds=3)`
        Output: 'F = m * a'

    Args:
        python_script: Value for `python_script` used by `cross_boundary`. Expected type: `str`.
        stdin_payload: Value for `stdin_payload` used by `cross_boundary`. Expected type: `Any`.
        timeout_seconds: Value for `timeout_seconds` used by `cross_boundary`. Expected type: `float | None`. Defaults to `None`.

    Returns:
        CrossBoundaryResult: Result produced by `cross_boundary`.
    """
    return execute_cross_boundary(
        framework="python3",
        executable_text=str(python_script or ""),
        stdin_payload=json_safe(stdin_payload),
        timeout_seconds=timeout_seconds,
    )


class BSSCController:
    SOURCE_RELIABILITY = {
        "human": ThreeLevel.HIGH,
        "tool": ThreeLevel.HIGH,
        "committed_state": ThreeLevel.HIGH,
        "governance": ThreeLevel.MEDIUM,
        "internal_reflection": ThreeLevel.MEDIUM,
        "prompt": ThreeLevel.LOW,
    }
    PRIOR_LEARNING_FAST_PATH_PROPOSALS = {
        ProposalType.SEMANTIC_TARGET,
        ProposalType.CONTROL_DECISION,
        ProposalType.NODE_ASSESSMENT,
        ProposalType.NEXT_ACTION,
        ProposalType.DIRECT_RESOLUTION,
        ProposalType.REALIZATION_WITNESS,
        ProposalType.REFLECTION,
        ProposalType.CONTEMPLATION,
        ProposalType.NOT_DECOMPOSITION,
        ProposalType.CANDIDATE_SELECTION,
        ProposalType.REFRAME,
        ProposalType.UNCERTAINTY_ASSESSMENT,
        ProposalType.RETRIEVAL_PLAN,
        ProposalType.DISCOVERY_AUDIT,
        ProposalType.IMMEDIATE_LEARNING,
        ProposalType.EXPLANATION_DRAFT,
    }

    def __init__(
        self,
        state: SystemState,
        *,
        llm_policy: str = "auto",
        host_interaction_context: HostInteractionContext | None = None,
    ) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with initializing the surrounding object with a usable starting state.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `__init__(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'), llm_policy='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            state: Value for `state` used by `__init__`. Expected type: `SystemState`.
            llm_policy: Value for `llm_policy` used by `__init__`. Expected type: `str`. Defaults to `'auto'`.
            host_interaction_context: Value for `host_interaction_context` used by `__init__`. Expected type: `HostInteractionContext | None`. Defaults to `None`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.state = state
        self.state.initialize_builtin_capabilities()
        self.llm = LLMSupplement(llm_policy)
        bound_store = getattr(state, "store", None)
        if bound_store is not None:
            self.artifact_store = bound_store
        else:
            self.artifact_store = SQLiteVectorArtifactStore(fallback_store=ArtifactStore())
        self.host_interaction_context = host_interaction_context or host_native_interaction_context(
            metadata={"owner": "controller"}
        )
        self._current_skill_governance_snapshot_cache: dict[str, Any] | None = None
        self.state.supplement_profile = self.llm.describe()
        self.state.supplement_profile["artifact_store"] = self.artifact_store.describe()
        self.state.supplement_profile["host_interaction"] = self.describe_host_interaction_context()
        self.ensure_llm_capabilities()
        if self.should_load_initial_learning_context(self.state.root()):
            self.load_learning_context(self.state.root())

    def describe_host_interaction_context(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller/runtime execution over different host backends, helps with exposing the active host-interaction descriptor as one stable JSON-friendly payload.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by letting the controller surface host-native and workstation-backed execution through one contract.

        Example Input Output:
            Input: `describe_host_interaction_context()`
            Output: {'backend_kind': 'host', 'attachments': [], 'allowed_capabilities': [], 'metadata': {'owner': 'controller'}}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `describe_host_interaction_context`.
        """
        return host_interaction_descriptor_payload(self.host_interaction_context)

    def host_interaction_backend_kind(self) -> str:
        """
        High Level Purpose:
            In circumstances like selecting or auditing the active host-interaction backend, helps with returning the normalized backend kind for the current controller runtime.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by making host-native versus workstation-backed execution explicit at the controller boundary.

        Example Input Output:
            Input: `host_interaction_backend_kind()`
            Output: 'host'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            str: Result produced by `host_interaction_backend_kind`.
        """
        return str(self.describe_host_interaction_context().get("backend_kind", "host"))

    def host_interaction_attachments(self) -> tuple[Any, ...]:
        """
        High Level Purpose:
            In circumstances like governed runtime execution over a pluggable host backend, helps with exposing the active attachment scope through the shared host-interaction contract.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by letting the controller/runtime observe attachment scope without importing workstation session code.

        Example Input Output:
            Input: `host_interaction_attachments()`
            Output: ()

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            tuple[Any, ...]: Result produced by `host_interaction_attachments`.
        """
        return host_interaction_attachments(self.host_interaction_context)

    def resolve_host_interaction_attachment_reference(self, name: str) -> tuple[Any, str]:
        """
        High Level Purpose:
            In circumstances like governed runtime use of the shared host-interaction seam, helps with resolving one attachment reference through the injected backend contract.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by letting host-native and workstation-backed execution share the same attachment-addressing behavior.

        Example Input Output:
            Input: `resolve_host_interaction_attachment_reference(name='main')`
            Output: (HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), '')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            name: Value for `name` used by `resolve_host_interaction_attachment_reference`. Expected type: `str`.

        Returns:
            tuple[Any, str]: Result produced by `resolve_host_interaction_attachment_reference`.
        """
        return resolve_host_interaction_attachment(self.host_interaction_context, name)

    def normalize_host_interaction_attachment_path(
        self,
        *,
        raw_target: str,
        explicit_relative_path: str,
    ) -> tuple[Any, str]:
        """
        High Level Purpose:
            In circumstances like governed runtime capability planning over a pluggable host backend, helps with canonicalizing one attachment target plus bounded relative path through the shared substrate.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by giving the controller/runtime the same attachment-path normalization behavior that workstation-backed execution uses.

        Example Input Output:
            Input: `normalize_host_interaction_attachment_path(raw_target='/workstation/mounts/main/src', explicit_relative_path='')`
            Output: (HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), 'src')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            raw_target: Value for `raw_target` used by `normalize_host_interaction_attachment_path`. Expected type: `str`.
            explicit_relative_path: Value for `explicit_relative_path` used by `normalize_host_interaction_attachment_path`. Expected type: `str`.

        Returns:
            tuple[Any, str]: Result produced by `normalize_host_interaction_attachment_path`.
        """
        return normalize_host_interaction_attachment_path(
            self.host_interaction_context,
            raw_target=raw_target,
            explicit_relative_path=explicit_relative_path,
        )

    def primary_host_interaction_workspace(self) -> Any | None:
        """
        High Level Purpose:
            In circumstances like governed runtime execution over a pluggable host backend, helps with recovering the single primary workspace attachment when the backend exposes exactly one.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by letting host-native and workstation-backed backends agree on the same bounded workspace default.

        Example Input Output:
            Input: `primary_host_interaction_workspace()`
            Output: HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            Any | None: Result produced by `primary_host_interaction_workspace`.
        """
        return primary_host_interaction_workspace(self.host_interaction_context)

    def should_load_initial_learning_context(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building context for should load initial learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `should_load_initial_learning_context(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `should_load_initial_learning_context`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `should_load_initial_learning_context`.
        """
        bootstrap_mode = collapse_ws(str(node.metadata.get("bootstrap_mode", "")).strip()).lower()
        if node.id == self.state.root_id and bootstrap_mode == "markdown_ingestion":
            return False
        return True

    def discovery_enabled(self) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling discovery enabled.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `discovery_enabled()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `discovery_enabled`.
        """
        return bool(self.state.controller_features.discovery_enabled)

    def reflection_enabled(self) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling reflection enabled.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `reflection_enabled()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `reflection_enabled`.
        """
        return bool(self.state.controller_features.reflection_enabled)

    def contemplation_enabled(self) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling contemplation enabled.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `contemplation_enabled()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `contemplation_enabled`.
        """
        return bool(self.state.controller_features.contemplation_enabled)

    def supported_executor_frameworks(self) -> list[str]:
        """
        High Level Purpose:
            In circumstances like markdown learning, artifact import, and runtime invocation across external executors, helps with exposing the ordered executor frameworks this controller instance is currently allowed to rely on.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially the governed external-boundary rules.

        Example Input Output:
            Input: `supported_executor_frameworks()`
            Output: ['python3', 'bash']

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            list[str]: Result produced by `supported_executor_frameworks`.
        """
        return normalize_supported_executor_frameworks(
            self.state.controller_features.supported_executors,
            default=("python3",),
        )

    def annotate_artifact_content_with_controller_features(
        self,
        content: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling annotate artifact content with controller features.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `annotate_artifact_content_with_controller_features(content={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            content: Value for `content` used by `annotate_artifact_content_with_controller_features`. Expected type: `Mapping[str, Any] | None`.

        Returns:
            dict[str, Any]: Result produced by `annotate_artifact_content_with_controller_features`.
        """
        enriched = dict(content) if isinstance(content, Mapping) else {}
        enriched["controller_features"] = self.state.controller_features.to_dict()
        return enriched

    def structural_governance_violation(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with checking structural governance violation.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `structural_governance_violation(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `structural_governance_violation`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `structural_governance_violation`.
        """
        if node.depth > self.state.governance.max_depth:
            return True
        if len(self.state.graph.nodes) > self.state.governance.max_nodes:
            return True
        return False

    def prior_learning_fast_path_ready(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether prior learning fast path is ready.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `prior_learning_fast_path_ready(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `prior_learning_fast_path_ready`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `prior_learning_fast_path_ready`.
        """
        if node.role != "root" or node.parent_id is not None:
            return False
        directive = semantic_prompt_directive_profile(node.semantic_unit)
        if collapse_ws(str(directive.get("kind", "")).strip()) in {"construct", "derive", "distinguish"}:
            return False
        if re.search(
            r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
            str(node.semantic_unit or ""),
            flags=re.IGNORECASE,
        ):
            return False
        if str(node.metadata.get("direct_resolution_answer_kind", "")).strip() != "learned_reuse":
            return False
        if not node.metadata.get("direct_resolution_ready_for_commitment"):
            return False
        if not self.direct_support_items(node):
            return False
        if self.structural_governance_violation(node):
            return False
        return True

    def seed_root_semantics_from_prior_learning(self, root: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with seeding root semantics from prior learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `seed_root_semantics_from_prior_learning(root=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            root: Value for `root` used by `seed_root_semantics_from_prior_learning`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        root.metadata["semantic_target"] = {
            "target_kind": self.infer_target_kind(root.semantic_unit),
            "goal_statement": root.semantic_unit,
            "scope_candidates": [root.semantic_unit],
            "exclusions": [],
            "ambiguity_notes": [],
            "alternate_semantic_framings": [],
            "boundary_shape": list(root.boundary_shape),
            "source": "prior_learning",
        }
        root.metadata["semantic_target_initialized"] = True
        root.description = root.semantic_unit
        self.state.sync_not_ontology_entry(root)

    def prepare_root_prior_learning_fast_path(self) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling prepare root prior learning fast path.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `prepare_root_prior_learning_fast_path()`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            bool: Result produced by `prepare_root_prior_learning_fast_path`.
        """
        root = self.state.root()
        self.load_learning_context(root)
        learned_signature = json.dumps(sorted(self.state.learned_artifacts), sort_keys=True)
        if (
            root.metadata.get("prior_learning_fast_path_prepared")
            and root.metadata.get("prior_learning_fast_path_signature") == learned_signature
        ):
            return bool(root.metadata.get("prior_learning_fast_path_ready"))

        self.instantiate_reusable_artifact_support(root)
        structured_learning = self.ensure_not_elaboration(root)
        directive = semantic_prompt_directive_profile(root.semantic_unit)
        explicit_split_request = bool(
            re.search(
                r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
                str(root.semantic_unit or ""),
                flags=re.IGNORECASE,
            )
        )
        component_count = len(
            [item for item in structured_learning.get("component_nots", []) if str(item).strip()]
        ) if isinstance(structured_learning, Mapping) else 0
        if (
            explicit_split_request
            or bool(structured_learning.get("title_depth_body_split_needed", False))
            or (
                collapse_ws(str(directive.get("kind", "")).strip()) in {"construct", "derive", "distinguish"}
                and component_count >= 2
            )
        ):
            root.metadata["prior_learning_fast_path_prepared"] = True
            root.metadata["prior_learning_fast_path_ready"] = False
            root.metadata["prior_learning_fast_path_signature"] = learned_signature
            return False
        ready = self.prior_learning_fast_path_ready(root)
        root.metadata["prior_learning_fast_path_prepared"] = True
        root.metadata["prior_learning_fast_path_ready"] = ready
        root.metadata["prior_learning_fast_path_signature"] = learned_signature

        if not ready:
            return False

        self.seed_root_semantics_from_prior_learning(root)
        direct = self.direct_support_items(root)
        upstream = self.upstream_support_items(root)
        self.state.support[root.id] = SupportView(direct=direct, upstream=upstream, score=SupportScore.OK)
        self.state.certainty[root.id] = ThreeLevel.HIGH
        self.state.blockers[root.id] = []
        self.state.conflicts[root.id] = []
        self.state.status[root.id] = NodeStatus.CLOSABLE
        root.metadata["llm_bypass_from_prior_learning"] = True
        self.state.record_step(
            kind="prior_learning_fast_path",
            node_id=root.id,
            intent="Let consecutive runs close from answer-bearing prior learning before fresh semantic supplementation is requested.",
            action="prime root from learned reusable residue",
            result="root prepared for direct closure from prior learning",
            evaluation="semantic target, support, and certainty were seeded from committed reusable artifacts rather than new LLM mediation",
            payload={
                "learned_artifact_ids": list(root.metadata.get("structured_learning_lookup", {}).get("artifact_ids", [])),
                "match_kind": root.metadata.get("structured_learning_lookup", {}).get("match_kind", "none"),
                "artifact_origin_report": root.metadata.get("structured_learning_lookup", {}).get("artifact_origin_report", {}),
                "answer_kind": root.metadata.get("direct_resolution_answer_kind", ""),
            },
        )
        return True

    def should_skip_related_proposal_from_prior_learning(
        self,
        proposal_type: ProposalType,
        node: SemanticNode | None,
    ) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether skip related proposal from prior learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `should_skip_related_proposal_from_prior_learning(proposal_type=ProposalType.NOT_ELABORATION, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal_type: Value for `proposal_type` used by `should_skip_related_proposal_from_prior_learning`. Expected type: `ProposalType`.
            node: Value for `node` used by `should_skip_related_proposal_from_prior_learning`. Expected type: `SemanticNode | None`.

        Returns:
            bool: Result produced by `should_skip_related_proposal_from_prior_learning`.
        """
        if node is None:
            return False
        return self.prior_learning_fast_path_ready(node) and proposal_type in self.PRIOR_LEARNING_FAST_PATH_PROPOSALS

    def ensure_llm_capabilities(self) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ensure llm capabilities.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ensure_llm_capabilities()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if not self.llm.enabled:
            return
        for mode in SupplementMode:
            semantic_role = f"llm_{mode.value}_supplement"
            if self.capabilities_for_role(semantic_role):
                continue
            model = self.llm.model_for_mode(mode) or "unconfigured"
            self.state.register_capability(
                affordance=f"{mode.value} llm semantic proposal",
                input_form="governed state slice",
                output_form="typed proposal object",
                semantic_role=semantic_role,
                limits={"mode": mode.value},
                validated=True,
                provenance=[],
                service_axis="semantic_proposal",
                realizer=f"{self.llm.provider}:{model}",
            )

    def capabilities_for_role(self, semantic_role: str) -> list[Capability]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling capabilities for role.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `capabilities_for_role(semantic_role='Physics / Force / Force From Mass And Acceleration')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_role: Value for `semantic_role` used by `capabilities_for_role`. Expected type: `str`.

        Returns:
            list[Capability]: Result produced by `capabilities_for_role`.
        """
        return [capability for capability in self.state.capabilities.values() if capability.semantic_role == semantic_role]

    def use_capability(self, semantic_role: str, *, node: SemanticNode | None, contribution: str) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with using capability.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `use_capability(semantic_role='Physics / Force / Force From Mass And Acceleration', node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), contribution='force')`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_role: Value for `semantic_role` used by `use_capability`. Expected type: `str`.
            node: Value for `node` used by `use_capability`. Expected type: `SemanticNode | None`.
            contribution: Value for `contribution` used by `use_capability`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        capabilities = self.capabilities_for_role(semantic_role)
        if not capabilities:
            return
        capability = capabilities[0]
        node_id = node.id if node is not None else None
        if node is not None:
            self.state.provenance_links.setdefault(node.id, []).append(capability.id)
        self.state.record_step(
            kind="capability_use",
            node_id=node_id,
            intent="Use capabilities only where their contribution bears on relevant non-achievedness reduction.",
            action=f"use capability {capability.affordance}",
            result="capability applied under controlled use",
            evaluation="tooling remained demoted beneath Not-centric control",
            payload={"capability_id": capability.id, "semantic_role": semantic_role, "contribution": contribution},
        )

    def template_schema_summary(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with summarizing template schema.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `template_schema_summary(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `template_schema_summary`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `template_schema_summary`.
        """
        if not artifact.template_schema:
            return {}
        return {
            "preconditions": artifact.template_schema.get("preconditions", []),
            "governed_function": artifact.template_schema.get("governed_function", ""),
            "completion_conditions": artifact.template_schema.get("completion_conditions", []),
            "failure_conditions": artifact.template_schema.get("failure_conditions", []),
            "scope_of_reuse": artifact.template_schema.get("scope_of_reuse", ""),
            "bssc_awareness": artifact.template_schema.get("bssc_awareness", {}),
            "holdon_awareness": artifact.template_schema.get("holdon_awareness", {}),
        }

    def ability_script_dependencies(self, content: Mapping[str, Any]) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ability script dependencies.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ability_script_dependencies(content={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            content: Value for `content` used by `ability_script_dependencies`. Expected type: `Mapping[str, Any]`.

        Returns:
            list[str]: Result produced by `ability_script_dependencies`.
        """
        raw = content.get("dependencies", [])
        if isinstance(raw, list):
            dependencies = [str(item).strip() for item in raw if str(item).strip()]
        else:
            dependencies = []
        for dependency in ABILITY_SCRIPT_DEPENDENCIES:
            if dependency not in dependencies:
                dependencies.append(dependency)
        return dependencies

    def default_ability_script(
        self,
        *,
        title: str,
        scope: str,
        justification: str,
        input_contract: Mapping[str, Any] | None = None,
        output_contract: Mapping[str, Any] | None = None,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with supplying default ability script.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `default_ability_script(title='Physics / Force / Force From Mass And Acceleration', scope='force', justification='force', input_contract={'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `default_ability_script`. Expected type: `str`.
            scope: Value for `scope` used by `default_ability_script`. Expected type: `str`.
            justification: Value for `justification` used by `default_ability_script`. Expected type: `str`.
            input_contract: Value for `input_contract` used by `default_ability_script`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
            output_contract: Value for `output_contract` used by `default_ability_script`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

        Returns:
            str: Result produced by `default_ability_script`.
        """
        input_contract = dict(input_contract or {"payload": "JSON object from stdin"})
        output_contract = dict(output_contract or {"result": "JSON object written to stdout"})
        dependencies = ", ".join(f'"{item}"' for item in ABILITY_SCRIPT_DEPENDENCIES)
        return dedent(
            f"""
            # /// script
            # requires-python = ">=3.11"
            # dependencies = [{dependencies}]
            # ///

            from __future__ import annotations

            import argparse
import ast
            import sys

            import msgspec
            import orjson


            class InputPayload(msgspec.Struct, kw_only=True):
                payload: dict[str, object] = {{}}


            class OutputPayload(msgspec.Struct, kw_only=True):
                status: str
                answer: str = ""
                result: dict[str, object]
                notes: list[str] = []


            def run(payload: InputPayload) -> OutputPayload:
                \"\"\"{title}: {scope}\"\"\"
                return OutputPayload(
                    status="not_implemented",
                    answer="",
                    result={{
                        "title": {title!r},
                        "scope": {scope!r},
                        "justification": {justification!r},
                        "received": payload.payload,
                    }},
                    notes=["Fill in the governed ability body for this artifact."],
                )


            def main() -> None:
                parser = argparse.ArgumentParser(description={title!r})
                parser.add_argument("--input-json", help="Optional JSON payload. Prefer stdin when omitted.")
                args = parser.parse_args()
                raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
                payload = orjson.loads(raw) if raw else {{}}
                typed_input = msgspec.convert({{"payload": payload}}, type=InputPayload)
                result = run(typed_input)
                sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result), option=orjson.OPT_INDENT_2))
                sys.stdout.buffer.write(b"\\n")


            if __name__ == "__main__":
                main()
            """
        ).strip()

    def expression_ability_script(
        self,
        *,
        title: str,
        scope: str,
        input_contract: Mapping[str, Any],
        output_contract: Mapping[str, Any],
        expression: str,
        output_field: str,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling expression ability script.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `expression_ability_script(title='Physics / Force / Force From Mass And Acceleration', scope='force', input_contract={'inputs': ['mass', 'acceleration'], 'output': 'force'}, output_contract={'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `expression_ability_script`. Expected type: `str`.
            scope: Value for `scope` used by `expression_ability_script`. Expected type: `str`.
            input_contract: Value for `input_contract` used by `expression_ability_script`. Expected type: `Mapping[str, Any]`.
            output_contract: Value for `output_contract` used by `expression_ability_script`. Expected type: `Mapping[str, Any]`.
            expression: Value for `expression` used by `expression_ability_script`. Expected type: `str`.
            output_field: Value for `output_field` used by `expression_ability_script`. Expected type: `str`.

        Returns:
            str: Result produced by `expression_ability_script`.
        """
        input_fields = [str(key).strip() for key in input_contract.keys() if str(key).strip()]
        field_block = "\n".join(f'                "{field}": _coerce_number(payload.payload.get("{field}")),' for field in input_fields)
        dependencies = ", ".join(f'"{item}"' for item in ABILITY_SCRIPT_DEPENDENCIES)
        return dedent(
            f"""
            # /// script
            # requires-python = ">=3.11"
            # dependencies = [{dependencies}]
            # ///

            from __future__ import annotations

            import argparse
            import ast
            import math
            import sys

            import msgspec
            import orjson


            EXPRESSION = {expression!r}
            OUTPUT_FIELD = {output_field!r}
            ALLOWED_NAMES = {input_fields!r}
            ALLOWED_NODE_TYPES = (
                ast.Expression,
                ast.BinOp,
                ast.UnaryOp,
                ast.Attribute,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.Pow,
                ast.Mod,
                ast.FloorDiv,
                ast.USub,
                ast.UAdd,
                ast.Load,
                ast.Name,
                ast.Constant,
            )


            class InputPayload(msgspec.Struct, kw_only=True):
                payload: dict[str, object] = {{}}


            class OutputPayload(msgspec.Struct, kw_only=True):
                status: str
                answer: str = ""
                result: dict[str, object]
                notes: list[str] = []


            def _validate_expression() -> ast.AST:
                tree = ast.parse(EXPRESSION, mode="eval")
                for node in ast.walk(tree):
                    if not isinstance(node, ALLOWED_NODE_TYPES):
                        raise ValueError(f"disallowed expression node: {{type(node).__name__}}")
                    if isinstance(node, ast.Attribute):
                        if not (
                            isinstance(node.value, ast.Name)
                            and node.value.id == "math"
                            and node.attr in {"pi", "e"}
                        ):
                            raise ValueError(f"disallowed attribute access: {{ast.unparse(node)}}")
                    if isinstance(node, ast.Name) and node.id not in ALLOWED_NAMES:
                        if node.id == "math":
                            continue
                        raise ValueError(f"disallowed symbol: {{node.id}}")
                return tree


            COMPILED = compile(_validate_expression(), "<expression>", "eval")


            def _coerce_number(value: object) -> float:
                if value is None:
                    raise ValueError("missing numeric input")
                if isinstance(value, bool):
                    raise ValueError("boolean inputs are not numeric")
                if isinstance(value, (int, float)):
                    return float(value)
                text = str(value).strip()
                if not text:
                    raise ValueError("empty numeric input")
                return float(text)


            def run(payload: InputPayload) -> OutputPayload:
                values = {{
{field_block}
                }}
                result = eval(COMPILED, {{"__builtins__": {{}}, "math": math}}, values)
                normalized = int(result) if isinstance(result, float) and result.is_integer() else result
                return OutputPayload(
                    status="ok",
                    answer=str(normalized),
                    result={{OUTPUT_FIELD: normalized}},
                    notes=[],
                )


            def main() -> None:
                parser = argparse.ArgumentParser(description={title!r})
                parser.add_argument("--input-json", help="Optional JSON payload. Prefer stdin when omitted.")
                args = parser.parse_args()
                raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
                payload = orjson.loads(raw) if raw else {{}}
                typed_input = msgspec.convert({{"payload": payload}}, type=InputPayload)
                result = run(typed_input)
                sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result), option=orjson.OPT_INDENT_2))
                sys.stdout.buffer.write(b"\\n")


            if __name__ == "__main__":
                main()
            """
        ).strip()

    def normalize_expression_ability_fields(
        self,
        *,
        compute_expression: str,
        output_field: str,
    ) -> tuple[str, str]:
        """
        High Level Purpose:
            In circumstances like ability-artifact learning, import, and execution repair, helps with converting equation-shaped formula text into an executable expression while preserving the semantic output field.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `normalize_expression_ability_fields(compute_expression='F = m * a', output_field='')`
            Output: ('m * a', 'F')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            compute_expression: Value for `compute_expression` used by `normalize_expression_ability_fields`. Expected type: `str`.
            output_field: Value for `output_field` used by `normalize_expression_ability_fields`. Expected type: `str`.

        Returns:
            tuple[str, str]: Result produced by `normalize_expression_ability_fields`.
        """
        raw_expression = str(compute_expression or "").strip()
        normalized_output = str(output_field or "").strip()
        if not raw_expression:
            return "", normalized_output
        if (
            "=" not in raw_expression
            and not re.search(r"[`$^π]|\\sqrt|sqrt\s*\{|rac\b", raw_expression)
        ):
            try:
                ast.parse(raw_expression, mode="eval")
                return raw_expression, normalized_output
            except Exception:
                pass

        power_marker = "BSSCPOWPLACEHOLDER"
        normalized = raw_expression.replace("$$", " ").replace("$", " ").replace("`", "")
        normalized = normalized.replace("π", " pi ")
        normalized = normalized.replace("**", power_marker)
        normalized = repair_fraction_like_expression_surface(normalized)
        normalized = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", normalized)
        normalized = re.sub(r"sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", normalized)
        normalized = markdown_clean_learning_text(normalized)
        normalized = normalized.replace(power_marker, "**")
        if "=" in normalized:
            left, right = normalized.split("=", 1)
            lhs_cleaned = markdown_clean_learning_text(left).replace(" ", "")
            lhs_match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)", lhs_cleaned)
            if lhs_match and not normalized_output:
                normalized_output = lhs_match.group(1)
            normalized = right.split("=", 1)[0].strip()
        normalized = repair_fraction_like_expression_surface(normalized)
        normalized = normalized.replace("^", "**")
        # Repair markdown/LLM formulas that flatten superscripts into adjacency, such as
        # `a 2`, `b 2`, or `( a ** 2 + b ** 2 ) 0.5`.
        normalized = re.sub(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s+(-?\d+(?:\.\d+)?)\b",
            r"\1 ** \2",
            normalized,
        )
        normalized = re.sub(
            r"(\))\s+(-?\d+(?:\.\d+)?)\b",
            r"\1 ** \2",
            normalized,
        )
        normalized = re.sub(
            r"\b([A-Za-z])([23])\b",
            r"\1 ** \2",
            normalized,
        )
        normalized = re.sub(
            r"(\))([23])\b",
            r"\1 ** \2",
            normalized,
        )
        while True:
            replaced = re.sub(r"sqrt\(([^()]+)\)", r"(\1) ** 0.5", normalized)
            if replaced == normalized:
                break
            normalized = replaced
        normalized = re.sub(r"(\d)([A-Za-z(])", r"\1*\2", normalized)
        normalized = re.sub(r"([A-Za-z\)])\(", r"\1*(", normalized)
        normalized = re.sub(r"\)([A-Za-z0-9])", r")*\1", normalized)
        normalized = self.repair_implicit_multiplication_surface(normalized)
        normalized = collapse_ws(normalized)
        normalized = repair_fraction_like_expression_surface(normalized)
        normalized = re.sub(
            r"\(\s*\(\s*([^()]+?)\s*\)\s*/\s*\(\s*([^()]+?)\s*\)\s*\)",
            lambda match: f"(({collapse_ws(match.group(1))}) / ({collapse_ws(match.group(2))}))",
            normalized,
        )
        return normalized, normalized_output

    def repair_implicit_multiplication_surface(self, expression: str) -> str:
        """
        High Level Purpose:
            In circumstances like markdown-learned formula repair and execution-time normalization, helps with restoring missing multiplication operators between adjacent multiplicative tokens without disturbing function-call syntax.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function keeps executable body constitution structurally coherent instead of relying on prompt-surface guesswork.

        Example Input Output:
            Input: `repair_implicit_multiplication_surface(expression='2 pi r ( r + h )')`
            Output: '2 * pi * r * ( r + h )'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            expression: Value for `expression` used by `repair_implicit_multiplication_surface`. Expected type: `str`.

        Returns:
            str: Result produced by `repair_implicit_multiplication_surface`.
        """
        normalized = collapse_ws(str(expression or "").strip())
        if not normalized:
            return ""
        tokens = re.findall(
            r"\*\*|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|\d+(?:\.\d+)?|[^\s]",
            normalized,
        )
        if not tokens:
            return normalized
        callable_leaf_names = {
            "sqrt",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "log",
            "log10",
            "ln",
            "exp",
            "abs",
            "min",
            "max",
            "pow",
        }
        rebuilt: list[str] = []
        previous = ""
        for token in tokens:
            current = str(token)
            if rebuilt:
                previous_is_value = bool(
                    re.fullmatch(
                        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|\d+(?:\.\d+)?|\)",
                        previous,
                    )
                )
                current_is_value = bool(
                    re.fullmatch(
                        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|\d+(?:\.\d+)?|\(",
                        current,
                    )
                )
                previous_leaf = previous.rsplit(".", 1)[-1].lower()
                previous_is_callable = current == "(" and previous_leaf in callable_leaf_names
                if previous_is_value and current_is_value and not previous_is_callable:
                    rebuilt.append("*")
            rebuilt.append(current)
            previous = current
        return collapse_ws(" ".join(rebuilt))

    def expression_ability_script_constants(self, python_script: str) -> tuple[str, str]:
        """
        High Level Purpose:
            In circumstances like execution-time repair of persisted expression abilities, helps with recovering the stored expression and output-field constants from a generated expression script.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `expression_ability_script_constants(python_script=\"EXPRESSION = 'F = m * a'\\nOUTPUT_FIELD = 'F'\")`
            Output: ('F = m * a', 'F')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            python_script: Value for `python_script` used by `expression_ability_script_constants`. Expected type: `str`.

        Returns:
            tuple[str, str]: Result produced by `expression_ability_script_constants`.
        """
        script_text = str(python_script or "")
        expression_match = re.search(r"^\s*EXPRESSION\s*=\s*(.+)$", script_text, flags=re.MULTILINE)
        output_match = re.search(r"^\s*OUTPUT_FIELD\s*=\s*(.+)$", script_text, flags=re.MULTILINE)
        expression_value = ""
        output_value = ""
        if expression_match:
            try:
                parsed = ast.literal_eval(expression_match.group(1).strip())
                expression_value = str(parsed).strip()
            except Exception:
                expression_value = ""
        if output_match:
            try:
                parsed = ast.literal_eval(output_match.group(1).strip())
                output_value = str(parsed).strip()
            except Exception:
                output_value = ""
        return expression_value, output_value

    def refresh_expression_ability_content(
        self,
        *,
        title: str,
        scope: str,
        content: Mapping[str, Any],
        force_regenerate: bool = False,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like ability-artifact construction, import hydration, and execution repair, helps with normalizing equation-backed content and regenerating the governed expression script when the stored script is stale or unsafe.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `refresh_expression_ability_content(title='Newton\\'s Laws of Motion / Force-Mass-Acceleration Relationship', scope='reuse when force should be computed from mass and acceleration', content={'compute_expression': 'F = m * a', 'output_field': 'F', 'input_contract': {'m': 'number', 'a': 'number'}, 'output_contract': {'F': 'number'}, 'python_script': ''})`
            Output: {'compute_expression': 'm * a', 'output_field': 'F', 'python_script': '# /// script ...'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `refresh_expression_ability_content`. Expected type: `str`.
            scope: Value for `scope` used by `refresh_expression_ability_content`. Expected type: `str`.
            content: Value for `content` used by `refresh_expression_ability_content`. Expected type: `Mapping[str, Any]`.
            force_regenerate: Value for `force_regenerate` used by `refresh_expression_ability_content`. Expected type: `bool`. Defaults to `False`.

        Returns:
            dict[str, Any]: Result produced by `refresh_expression_ability_content`.
        """
        updated = dict(content) if isinstance(content, Mapping) else {}
        input_contract = updated.get("input_contract", {})
        output_contract = updated.get("output_contract", {})
        updated["input_contract"] = dict(input_contract) if isinstance(input_contract, Mapping) else {}
        updated["output_contract"] = dict(output_contract) if isinstance(output_contract, Mapping) else {}

        normalized_expression, normalized_output = self.normalize_expression_ability_fields(
            compute_expression=str(updated.get("compute_expression", "")).strip(),
            output_field=str(updated.get("output_field", "")).strip(),
        )
        input_keys = [str(key).strip() for key in updated["input_contract"].keys() if str(key).strip()]
        input_key_set = {key.casefold() for key in input_keys}
        if normalized_expression and "pi" not in input_key_set:
            normalized_expression = re.sub(r"(?<![A-Za-z0-9_\.])pi(?![A-Za-z0-9_])", "math.pi", normalized_expression)
        if normalized_expression:
            updated["compute_expression"] = normalized_expression
        if normalized_output:
            updated["output_field"] = normalized_output

        if normalized_expression and updated["input_contract"]:
            expression_names = {
                token
                for token in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", normalized_expression)
                if token not in {"math", "sqrt"}
            }
            used_input_keys = [key for key in input_keys if key in expression_names]
            if used_input_keys and len(used_input_keys) < len(input_keys):
                updated["input_contract"] = {
                    key: updated["input_contract"][key]
                    for key in input_keys
                    if key in used_input_keys
                }
                parameter_aliases = updated.get("parameter_aliases", {})
                if isinstance(parameter_aliases, Mapping):
                    updated["parameter_aliases"] = {
                        key: parameter_aliases.get(key, [])
                        for key in used_input_keys
                    }

        if normalized_output:
            current_output_contract = dict(updated.get("output_contract", {}))
            if not current_output_contract:
                updated["output_contract"] = {normalized_output: "number"}
            elif normalized_output not in current_output_contract:
                first_value = next(iter(current_output_contract.values()), "number")
                updated["output_contract"] = {normalized_output: first_value}

        python_script = str(updated.get("python_script", "")).strip()
        if not normalized_expression or not normalized_output or not updated["input_contract"]:
            return updated
        stored_expression, stored_output = self.expression_ability_script_constants(python_script)
        should_regenerate = force_regenerate or not python_script
        if stored_expression or stored_output:
            should_regenerate = should_regenerate or stored_expression != normalized_expression or stored_output != normalized_output
        if should_regenerate:
            updated["python_script"] = self.expression_ability_script(
                title=title,
                scope=scope,
                input_contract=updated["input_contract"],
                output_contract=updated["output_contract"],
                expression=normalized_expression,
                output_field=normalized_output,
            )
        return updated

    def prompt_requests_python_executable(self, semantic_unit: str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling prompt requests python executable.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `prompt_requests_python_executable(semantic_unit='Physics / Force / Force From Mass And Acceleration')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `prompt_requests_python_executable`. Expected type: `str`.

        Returns:
            bool: Result produced by `prompt_requests_python_executable`.
        """
        text = collapse_ws(str(semantic_unit or "").strip().lower())
        if not text:
            return False
        return bool(
            re.search(
                r"\b(write|create|generate|build)\b.*\bpython\b.*\b(script|function|program)\b"
                r"|\bpython\b.*\b(script|function|program)\b"
                r"|\binline-metadata\b.*\bpython\b.*\bscript\b",
                text,
            )
        )

    def extract_python_code_answer(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling extract python code answer.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `extract_python_code_answer(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `extract_python_code_answer`. Expected type: `str`.

        Returns:
            str: Result produced by `extract_python_code_answer`.
        """
        raw = str(text or "").strip()
        if not raw:
            return ""
        fenced = re.search(r"```(?:python)?\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return str(fenced.group(1)).strip()
        return raw

    def callable_python_signature(self, python_code: str) -> tuple[str, list[str]] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling callable python signature.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `callable_python_signature(python_code='Compute force from mass and acceleration.')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            python_code: Value for `python_code` used by `callable_python_signature`. Expected type: `str`.

        Returns:
            tuple[str, list[str]] | None: Result produced by `callable_python_signature`.
        """
        code = self.extract_python_code_answer(python_code)
        if not code:
            return None
        try:
            module = ast.parse(code)
        except Exception:
            return None
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.args.vararg or node.args.kwarg or node.decorator_list:
                    return None
                arg_names = [
                    str(arg.arg).strip()
                    for arg in [*node.args.args, *node.args.kwonlyargs]
                    if str(arg.arg).strip() and str(arg.arg).strip() != "__dependencies__"
                ]
                if not arg_names:
                    return None
                return str(node.name).strip(), arg_names
        return None

    def callable_snippet_ability_script(
        self,
        *,
        title: str,
        scope: str,
        justification: str,
        python_code: str,
        function_name: str,
        argument_names: list[str],
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling callable snippet ability script.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `callable_snippet_ability_script(title='Physics / Force / Force From Mass And Acceleration', scope='force', justification='force', python_code='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `callable_snippet_ability_script`. Expected type: `str`.
            scope: Value for `scope` used by `callable_snippet_ability_script`. Expected type: `str`.
            justification: Value for `justification` used by `callable_snippet_ability_script`. Expected type: `str`.
            python_code: Value for `python_code` used by `callable_snippet_ability_script`. Expected type: `str`.
            function_name: Value for `function_name` used by `callable_snippet_ability_script`. Expected type: `str`.
            argument_names: Value for `argument_names` used by `callable_snippet_ability_script`. Expected type: `list[str]`.

        Returns:
            str: Result produced by `callable_snippet_ability_script`.
        """
        dependencies = ", ".join(f'"{item}"' for item in ABILITY_SCRIPT_DEPENDENCIES)
        argument_unpack = ", ".join(f"{name}=payload.payload.get({name!r})" for name in argument_names)
        source_code = self.extract_python_code_answer(python_code)
        cli_entrypoint_name = "__bssc_cli_main__"
        runtime_prefix = dedent(
            f"""
            # /// script
            # requires-python = ">=3.11"
            # dependencies = [{dependencies}]
            # ///

            from __future__ import annotations

            import argparse
            import sys

            import msgspec
            import orjson


            class InputPayload(msgspec.Struct, kw_only=True):
                payload: dict[str, object] = {{}}


            class OutputPayload(msgspec.Struct, kw_only=True):
                status: str
                answer: str = ""
                result: dict[str, object]
                notes: list[str] = []


            def _normalize_result(value: object) -> object:
                if isinstance(value, float) and value.is_integer():
                    return int(value)
                return value
            """
        ).strip()
        runtime_suffix = dedent(
            f"""
            def run(payload: InputPayload) -> OutputPayload:
                \"\"\"{title}: {scope}\"\"\"
                result_value = {function_name}({argument_unpack})
                normalized = _normalize_result(result_value)
                return OutputPayload(
                    status="ok",
                    answer=str(normalized),
                    result={{"result": normalized}},
                    notes=[],
                )


            def {cli_entrypoint_name}() -> None:
                parser = argparse.ArgumentParser(description={title!r})
                parser.add_argument("--input-json", help="Optional JSON payload. Prefer stdin when omitted.")
                args = parser.parse_args()
                raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
                payload = orjson.loads(raw) if raw else {{}}
                typed_input = msgspec.convert({{"payload": payload}}, type=InputPayload)
                result = run(typed_input)
                sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result), option=orjson.OPT_INDENT_2))
                sys.stdout.buffer.write(b"\\n")


            if __name__ == "__main__":
                {cli_entrypoint_name}()
            """
        ).strip()
        return "\n\n".join(
            [
                runtime_prefix,
                source_code.strip(),
                runtime_suffix,
            ]
        ).strip()

    def ability_payload_from_python_answer(
        self,
        *,
        node: SemanticNode,
        answer: str,
        answer_kind: str,
    ) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ability payload from python answer.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ability_payload_from_python_answer(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), answer='F = m * a', answer_kind='force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `ability_payload_from_python_answer`. Expected type: `SemanticNode`.
            answer: Value for `answer` used by `ability_payload_from_python_answer`. Expected type: `str`.
            answer_kind: Value for `answer_kind` used by `ability_payload_from_python_answer`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `ability_payload_from_python_answer`.
        """
        if not self.prompt_requests_python_executable(node.semantic_unit):
            return None
        signature = self.callable_python_signature(answer)
        if signature is None:
            return None
        function_name, argument_names = signature
        family_label = titleize_semantic_unit(function_name.replace("_", " ")) or "Python Ability"
        title = f"Python {family_label} Ability"
        scope = f"reuse when the user asks to compute or script {family_label.lower()} in Python under compatible named inputs"
        structured_learning = {
            "encountered_not": f"Python {family_label}",
            "lookup_keys": ordered_unique(
                [
                    f"python {function_name.replace('_', ' ')}",
                    f"{function_name.replace('_', ' ')} function",
                    f"{function_name.replace('_', ' ')} script",
                    f"{family_label.lower()} python",
                    f"{family_label.lower()} function",
                    f"{family_label.lower()} script",
                    *[f"{family_label.lower()} {name}" for name in argument_names],
                ]
            )[:24],
            "component_nots": [family_label, f"Inputs {' '.join(argument_names)}"],
            "composed_not": f"Python {family_label} Function",
            "goal": f"Compute {family_label.lower()} in Python from named inputs.",
            "intended_object": f"A reusable Python executable for {family_label.lower()} with named inputs {', '.join(argument_names)}.",
            "success_criteria": [
                "all required named inputs are supplied",
                "the executable returns the computed result in structured form",
            ],
            "boundary_shape": ["a*", "c*", "d*"],
            "action_posture": "compute_or_template",
            "notation_yaml": "",
        }
        python_script = self.callable_snippet_ability_script(
            title=title,
            scope=scope,
            justification="Derived from a closed Python code answer so later runs can reuse it as an executable ability.",
            python_code=answer,
            function_name=function_name,
            argument_names=argument_names,
        )
        return {
            "artifact_type": "ability",
            "title": title,
            "representation": "python_script",
            "scope": scope,
            "reusability": "broad_reuse",
            "admissibility": "admitted",
            "learning_relation": "new_family",
            "justification": "the run produced executable Python code that can be reused as a governed ability rather than only as inert text",
            "constraints": [
                "reuse only when the prompt asks for the same executable Python task family",
                "invoke only with the required named inputs",
            ],
            "content": {
                "question": f"How do you compute {family_label.lower()} in Python?",
                "aliases": [
                    node.semantic_unit,
                    f"Write a Python script for {family_label.lower()}",
                    f"Write a Python function for {family_label.lower()}",
                ],
                "answer_kind": answer_kind or "function_execution",
                "python_script": python_script,
                "entrypoint": "main",
                "script_language": "python",
                "input_contract": {name: "required input value" for name in argument_names},
                "output_contract": {"result": "computed result"},
                "dependencies": list(ABILITY_SCRIPT_DEPENDENCIES),
                "structured_learning": structured_learning,
            },
            "function_bit": 1,
            "boundary_shape": ["a*", "c*", "d*"],
        }

    def ability_artifact_summary(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with summarizing ability artifact.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `ability_artifact_summary(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `ability_artifact_summary`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `ability_artifact_summary`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        return {
            "entrypoint": str(content.get("entrypoint", "")),
            "script_language": str(content.get("script_language", "")),
            "dependencies": [str(item) for item in content.get("dependencies", []) if str(item).strip()]
            if isinstance(content.get("dependencies", []), list)
            else [],
            "input_contract": dict(content.get("input_contract", {}))
            if isinstance(content.get("input_contract", {}), Mapping)
            else {},
            "output_contract": dict(content.get("output_contract", {}))
            if isinstance(content.get("output_contract", {}), Mapping)
            else {},
        }

    def artifact_runtime_content(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like ranking, payload derivation, and execution of persisted ability artifacts, helps with normalizing expression-backed content before the controller makes routing or invocation decisions.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_runtime_content(artifact=Artifact(id='artifact-speed', title='Physics / Speed From Distance And Time', artifact_type='ability', representation='python_script'))`
            Output: {'compute_expression': '((d) / (t))', 'input_contract': {'d': 'number', 't': 'number'}}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_runtime_content`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `artifact_runtime_content`.
        """
        raw_content = artifact.content if isinstance(artifact.content, Mapping) else {}
        if int(getattr(artifact, "function_bit", 0) or 0) != 1:
            return dict(raw_content) if isinstance(raw_content, Mapping) else {}
        refreshed = self.refresh_expression_ability_content(
            title=artifact.title,
            scope=artifact.scope,
            content=raw_content,
        )
        if refreshed != raw_content:
            artifact.content = refreshed
        return refreshed

    def extract_inline_invocation_payload(self, text: str) -> Any | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for extract inline invocation.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `extract_inline_invocation_payload(text='Compute force from mass and acceleration.')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `extract_inline_invocation_payload`. Expected type: `str`.

        Returns:
            Any | None: Result produced by `extract_inline_invocation_payload`.
        """
        candidate = str(text or "").strip()
        if not candidate:
            return None
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", candidate, flags=re.DOTALL)
        if fenced_match:
            candidate = fenced_match.group(1).strip()
        direct_json_match = re.search(r"(\{.*\}|\[.*\])", candidate, flags=re.DOTALL)
        if direct_json_match:
            raw = direct_json_match.group(1).strip()
            try:
                return json.loads(raw)
            except Exception:
                pass
        return None

    def coerce_invocation_scalar(self, raw: str) -> Any:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling coerce invocation scalar.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `coerce_invocation_scalar(raw='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            raw: Value for `raw` used by `coerce_invocation_scalar`. Expected type: `str`.

        Returns:
            Any: Result produced by `coerce_invocation_scalar`.
        """
        text = str(raw or "").strip().rstrip(".,;")
        if not text:
            return ""
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none"}:
            return None
        try:
            if re.fullmatch(r"-?\d+", text):
                return int(text)
            if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
                return float(text)
        except Exception:
            pass
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                return json.loads(text)
            except Exception:
                return text
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            return text[1:-1]
        return text

    def derive_artifact_invocation_payload(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
        explicit_payload: Any = None,
    ) -> Any | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for derive artifact invocation.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `derive_artifact_invocation_payload(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), semantic_unit='Physics / Force / Force From Mass And Acceleration', explicit_payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `derive_artifact_invocation_payload`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `derive_artifact_invocation_payload`. Expected type: `str`. Defaults to `''`.
            explicit_payload: Value for `explicit_payload` used by `derive_artifact_invocation_payload`. Expected type: `Any`. Defaults to `None`.

        Returns:
            Any | None: Result produced by `derive_artifact_invocation_payload`.
        """
        if explicit_payload not in (None, "", [], {}):
            return json_safe(explicit_payload)

        content = self.artifact_runtime_content(artifact)
        formal_title_identity = self.artifact_formal_title_identity(artifact)
        input_contract = content.get("input_contract", {})
        output_contract = content.get("output_contract", {})
        if (
            looks_like_prolog_title_identity(formal_title_identity)
            and looks_like_prolog_title_identity(str(semantic_unit or "").strip())
            and isinstance(input_contract, Mapping)
        ):
            prolog_payload = derive_prolog_query_invocation_payload(
                formal_title_identity,
                str(semantic_unit or "").strip(),
                input_keys=[str(key).strip() for key in input_contract.keys() if str(key).strip()],
                output_keys=[str(key).strip() for key in output_contract.keys() if str(key).strip()] if isinstance(output_contract, Mapping) else [],
            )
            if prolog_payload:
                return json_safe(prolog_payload)

        parsed_inline = self.extract_inline_invocation_payload(semantic_unit)
        if not isinstance(input_contract, Mapping):
            if parsed_inline not in (None, "", [], {}):
                return json_safe(parsed_inline)
            return None
        if not input_contract:
            if parsed_inline not in (None, "", [], {}):
                return json_safe(parsed_inline)
            return {}
        contract_keys = {
            str(key).strip()
            for key in input_contract.keys()
            if str(key).strip()
        }
        inline_contract_values: dict[str, Any] = {}
        if isinstance(parsed_inline, Mapping):
            for raw_key, raw_value in parsed_inline.items():
                key_text = str(raw_key).strip()
                if key_text and key_text in contract_keys:
                    inline_contract_values[key_text] = raw_value
            if contract_keys and contract_keys.issubset(set(inline_contract_values.keys())):
                return json_safe(inline_contract_values)

        semantic_text = str(semantic_unit or "")
        named_values: dict[str, Any] = {}
        parameter_aliases = content.get("parameter_aliases", {})
        prolog_aliases: dict[str, list[str]] = {}
        prompt_named_keys = semantic_named_input_keys(semantic_text)
        backticked_literals = semantic_backticked_literals(semantic_text)
        url_literals = semantic_url_literals(semantic_text)
        application_mentions = semantic_application_mentions(semantic_text)
        mount_mentions = semantic_mount_mentions(semantic_text)
        source_mount_mention = semantic_source_mount_mention(semantic_text)
        destination_mount_mention = semantic_destination_mount_mention(semantic_text)
        relative_path_literals = semantic_relative_path_literals(semantic_text)
        source_relative_path_literal = semantic_source_relative_path_literal(semantic_text)
        destination_relative_path_literal = semantic_destination_relative_path_literal(semantic_text)
        pathlike_literals = semantic_pathlike_literals(semantic_text)
        suffix_literals = semantic_suffix_literals(semantic_text)
        absolute_path_literals = [
            value for value in pathlike_literals if value == "." or value.startswith("~") or "/" in value
        ]
        generic_literal_values = [
            value
            for value in backticked_literals
            if value not in mount_mentions and value not in url_literals and value not in pathlike_literals
        ]
        prompt_initial_aliases: dict[str, list[str]] = {}
        for key in input_contract.keys():
            key_text = str(key).strip()
            lowered_key = key_text.lower()
            if not lowered_key or len(lowered_key) != 1 or not lowered_key.isalpha():
                continue
            prompt_initial_aliases[key_text] = [
                candidate
                for candidate in prompt_named_keys
                if candidate and candidate.startswith(lowered_key) and candidate != lowered_key
            ]
        if looks_like_prolog_title_identity(formal_title_identity):
            prolog_aliases = prolog_contract_alias_map(
                formal_title_identity,
                input_keys=[str(key).strip() for key in input_contract.keys() if str(key).strip()],
                output_keys=[str(key).strip() for key in output_contract.keys() if str(key).strip()] if isinstance(output_contract, Mapping) else [],
            )
        for key in input_contract.keys():
            key_text = str(key).strip()
            if not key_text:
                continue
            candidates = [key_text]
            if isinstance(parameter_aliases, Mapping):
                aliases = parameter_aliases.get(key_text, [])
                if isinstance(aliases, list):
                    candidates.extend(str(alias).strip() for alias in aliases if str(alias).strip())
            candidates.extend(prolog_aliases.get(key_text, []))
            candidates.extend(prompt_initial_aliases.get(key_text, []))
            for candidate_name in ordered_unique(candidates):
                pattern = re.compile(
                    rf"\b{re.escape(candidate_name)}\b\s*(?:(?:=|:)|\bis\b)?\s*"
                    r"("
                    r"-?\d+(?:\.\d+)?"
                    r"|true|false|null|none"
                    r"|\"[^\"]*\""
                    r"|'[^']*'"
                    r")",
                    flags=re.IGNORECASE,
                )
                match = pattern.search(semantic_text)
                if match:
                    named_values[key_text] = self.coerce_invocation_scalar(match.group(1))
                    break
        for key in input_contract.keys():
            key_text = str(key).strip()
            lowered_key = key_text.lower()
            if not lowered_key or key_text in named_values:
                continue
            if any(marker in lowered_key for marker in ("source_mount", "from_mount", "input_mount")) and mount_mentions:
                if source_mount_mention:
                    named_values[key_text] = source_mount_mention
                    continue
                named_values[key_text] = mount_mentions[0]
                continue
            if any(marker in lowered_key for marker in ("destination_mount", "dest_mount", "target_mount", "output_mount", "to_mount")):
                if destination_mount_mention:
                    named_values[key_text] = destination_mount_mention
                    continue
                if len(mount_mentions) >= 2:
                    named_values[key_text] = mount_mentions[1]
                    continue
                if mount_mentions:
                    named_values[key_text] = mount_mentions[0]
                    continue
            if "mount" in lowered_key and mount_mentions:
                named_values[key_text] = mount_mentions[0]
                continue
            if any(marker in lowered_key for marker in ("source_relative_path", "from_relative_path", "input_relative_path")) and relative_path_literals:
                if source_relative_path_literal:
                    named_values[key_text] = source_relative_path_literal
                    continue
                named_values[key_text] = relative_path_literals[0]
                continue
            if any(marker in lowered_key for marker in ("destination_relative_path", "dest_relative_path", "target_relative_path", "output_relative_path", "to_relative_path")):
                if destination_relative_path_literal:
                    named_values[key_text] = destination_relative_path_literal
                    continue
                if len(relative_path_literals) >= 2:
                    named_values[key_text] = relative_path_literals[1]
                    continue
                if relative_path_literals:
                    named_values[key_text] = relative_path_literals[0]
                    continue
            if "relative_path" in lowered_key and relative_path_literals:
                named_values[key_text] = relative_path_literals[0]
                continue
            if lowered_key in {"path", "file_path", "folder_path", "directory_path"} and pathlike_literals:
                named_values[key_text] = pathlike_literals[0]
                continue
            if any(marker in lowered_key for marker in ("source_path", "src_path", "input_path", "from_path")) and pathlike_literals:
                named_values[key_text] = pathlike_literals[0]
                continue
            if any(marker in lowered_key for marker in ("destination_path", "dest_path", "target_path", "output_path", "to_path")):
                if len(pathlike_literals) >= 2:
                    named_values[key_text] = pathlike_literals[1]
                    continue
                if pathlike_literals:
                    named_values[key_text] = pathlike_literals[0]
                    continue
            if lowered_key in {"root", "directory", "folder"} and absolute_path_literals:
                named_values[key_text] = absolute_path_literals[-1]
                continue
            if "suffix" in lowered_key or "extension" in lowered_key:
                if suffix_literals:
                    named_values[key_text] = suffix_literals[0]
                    continue
            if any(marker in lowered_key for marker in ("text", "content", "message", "query", "search", "term")) and generic_literal_values:
                named_values[key_text] = decode_semantic_text_literal(generic_literal_values[0])
                continue
            if any(marker in lowered_key for marker in ("url", "uri", "link", "website", "address")) and url_literals:
                named_values[key_text] = url_literals[0]
                continue
            if any(marker in lowered_key for marker in ("browser", "app", "application")) and application_mentions:
                named_values[key_text] = application_mentions[0]
        if named_values:
            if inline_contract_values:
                merged_named_values = dict(inline_contract_values)
                merged_named_values.update(named_values)
                return json_safe(merged_named_values)
            return named_values

        contract_keys = [key for key in contract_keys if key]
        numeric_literals = [
            self.coerce_invocation_scalar(match)
            for match in re.findall(r"-?\d+(?:\.\d+)?", semantic_text)
        ]
        repeated_input_markers = (
            " each",
            "same length",
            "same value",
            "both ",
            "both of",
            "the other two",
            "all equal",
        )
        if len(contract_keys) >= 2 and len(numeric_literals) == 1:
            lowered_semantic_text = semantic_text.lower()
            if any(marker in lowered_semantic_text for marker in repeated_input_markers):
                return {key: numeric_literals[0] for key in contract_keys}
        if len(contract_keys) == 1 and len(numeric_literals) == 1:
            return {contract_keys[0]: numeric_literals[0]}
        if semantic_unit_allows_default_invocation_payload(semantic_unit):
            for key in ("default_invocation_payload", "invocation_payload"):
                stored = content.get(key)
                if stored not in (None, "", [], {}):
                    return json_safe(stored)
        return None

    def execute_function_artifact(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
        explicit_payload: Any = None,
    ) -> CrossBoundaryResult:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with executing function artifact.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `execute_function_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), semantic_unit='Physics / Force / Force From Mass And Acceleration', explicit_payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `execute_function_artifact`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `execute_function_artifact`. Expected type: `str`. Defaults to `''`.
            explicit_payload: Value for `explicit_payload` used by `execute_function_artifact`. Expected type: `Any`. Defaults to `None`.

        Returns:
            CrossBoundaryResult: Result produced by `execute_function_artifact`.
        """
        raw_content = artifact.content if isinstance(artifact.content, Mapping) else {}
        content = self.refresh_expression_ability_content(
            title=artifact.title,
            scope=artifact.scope,
            content=raw_content,
        )
        if content != raw_content:
            artifact.content = content
        executor_framework = ability_executor_framework(
            representation=str(artifact.representation),
            content=content,
        )
        executable_text = ability_executable_text(
            representation=str(artifact.representation),
            content=content,
        )
        invocation_payload = self.derive_artifact_invocation_payload(
            artifact,
            semantic_unit=semantic_unit,
            explicit_payload=explicit_payload,
        )
        if not executable_text:
            return CrossBoundaryResult(
                ok=False,
                command=[],
                exit_code=1,
                stdout="",
                stderr="Ability artifact had no executable body content.",
                notes=["Stored ability artifact could not cross the execution boundary."],
            )
        if executor_framework and executor_framework not in self.supported_executor_frameworks():
            return CrossBoundaryResult(
                ok=False,
                command=[],
                exit_code=1,
                stdout="",
                stderr=f"Executor framework {executor_framework} is not enabled for this controller run.",
                notes=["The artifact requires an executor framework that is not currently supported."],
            )
        if invocation_payload is None:
            return CrossBoundaryResult(
                ok=False,
                command=[],
                exit_code=1,
                stdout="",
                stderr="No invocation payload could be derived for the executable artifact.",
                notes=["The active item did not provide structured inputs matching the artifact input contract."],
            )
        self.use_capability(
            "cross_boundary",
            node=None,
            contribution=f"execute function-bearing artifact {artifact.title} with governed structured input",
        )
        result = self.execute_mediated_artifact_effect(
            artifact,
            semantic_unit=semantic_unit,
            executor_framework=executor_framework or "python3",
            executable_text=executable_text,
            invocation_payload=invocation_payload,
        )
        if not result.ok and executor_framework == "python3" and str(content.get("compute_expression", "")).strip():
            repaired_content = self.refresh_expression_ability_content(
                title=artifact.title,
                scope=artifact.scope,
                content={**content, "python_script": ""},
                force_regenerate=True,
            )
            repaired_script = str(repaired_content.get("python_script", "")).strip()
            if repaired_script and repaired_script != executable_text:
                artifact.content = repaired_content
                result = self.execute_mediated_artifact_effect(
                    artifact,
                    semantic_unit=semantic_unit,
                    executor_framework="python3",
                    executable_text=repaired_script,
                    invocation_payload=invocation_payload,
                )
        if isinstance(result.parsed_output, Mapping):
            status = str(result.parsed_output.get("status", "")).strip().lower()
            if status == "not_implemented":
                result.ok = False
                result.notes.append("Executable artifact returned not_implemented and cannot count as closure support.")
        return result

    def persist_generated_artifact(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with persisting generated artifact.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `persist_generated_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `persist_generated_artifact`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `persist_generated_artifact`.
        """
        self.use_capability(
            "artifact_persistence",
            node=self.state.root(),
            contribution=f"persist generated artifact {artifact.title} for later reuse",
        )
        report = self.artifact_store.persist_artifact(artifact, run_id=self.state.run_id)
        self.invalidate_current_skill_governance_snapshot()
        self.state.artifact_persistence.append(json_safe(report))
        self.state.record_step(
            kind="artifact_persistence",
            node_id=self.state.root_id,
            intent="Persist newly generated artifacts immediately when they are admitted and operationally relevant.",
            action="persist generated artifact",
            result=report.get("status", "persisted"),
            evaluation="generated residue was made available for future runs without waiting for end-of-run harvest only",
            payload=report,
        )
        return report

    def structured_learning_view(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building a view of structured learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `structured_learning_view(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `structured_learning_view`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `structured_learning_view`.
        """
        semantic_basis = self.component_fallback_lookup_basis(node)
        stored = node.metadata.get("not_elaboration", {})
        if isinstance(stored, Mapping):
            normalized = normalize_not_elaboration_payload(
                semantic_basis,
                stored,
                boundary_shape=node.boundary_shape,
                related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                title_identity=node.semantic_unit,
            )
            return normalized | {"boundary_shape": list(normalized.get("boundary_shape", [term.value for term in node.boundary_shape]))}

        encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(node.semantic_unit)))
        if not encountered_not:
            semantic_target = node.metadata.get("semantic_target", {})
            semantic_basis = str(semantic_target.get("goal_statement", "")).strip()
            encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(semantic_basis)))
        component_nots = list(learning_component_units(node.semantic_unit))
        for child in self.refinement_children(node):
            normalized_child = titleize_semantic_unit(" ".join(learning_core_tokens(child.semantic_unit))) or titleize_semantic_unit(child.semantic_unit)
            if normalized_child and normalized_child != encountered_not:
                component_nots.append(normalized_child)

        related_titles = [artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]]
        return self.structured_learning_view_for_text(
            semantic_basis,
            title_identity=node.semantic_unit,
            encountered_not=encountered_not,
            component_nots=component_nots or None,
            related_artifact_titles=related_titles,
        ) | {"boundary_shape": [term.value for term in node.boundary_shape]}

    def component_fallback_lookup_basis(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like fallback decomposition children that must stay determinate leaves, helps with preserving the governing parent prompt as lookup context without changing the child semantic identity.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `component_fallback_lookup_basis(node=SemanticNode(id='child', semantic_unit='Reusable Substrate For Molar Mass'))`
            Output: 'Given the relation for molar mass, express how to compute mass from moles and molar mass, and explain how this relates to the reusable substrate. / Reusable Substrate For Molar Mass'

        Args:
            self: Bound instance that owns runtime state and graph access.
            node: Value for `node` used by `component_fallback_lookup_basis`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `component_fallback_lookup_basis`.
        """
        semantic_text = collapse_ws(str(node.semantic_unit or "").strip())
        if node.role != "generic" or not bool(node.metadata.get("component_fallback")):
            return semantic_text
        parent = self.state.graph.get_node(node.parent_id) if node.parent_id and node.parent_id in self.state.graph.nodes else None
        parent_semantic = collapse_ws(str(parent.semantic_unit or "").strip()) if parent is not None else ""
        anchor_prefix = collapse_ws(str(node.metadata.get("title_depth_anchor_prefix", "")).strip())
        contextual_parts: list[str] = []
        if parent_semantic and parent_semantic != semantic_text:
            contextual_parts.append(parent_semantic)
        elif anchor_prefix and anchor_prefix != semantic_text:
            contextual_parts.append(anchor_prefix)
        if semantic_text:
            contextual_parts.append(semantic_text)
        contextualized = " / ".join(part for part in contextual_parts if part)
        return contextualized or semantic_text

    def ensure_not_elaboration(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ensure not elaboration.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ensure_not_elaboration(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `ensure_not_elaboration`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `ensure_not_elaboration`.
        """
        existing = node.metadata.get("not_elaboration", {})
        semantic_basis = self.component_fallback_lookup_basis(node)
        if isinstance(existing, Mapping) and str(existing.get("encountered_not", "")).strip():
            normalized = normalize_not_elaboration_payload(
                semantic_basis,
                existing,
                boundary_shape=node.boundary_shape,
                related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                title_identity=node.semantic_unit,
            )
            if node.role == "generic" and bool(node.metadata.get("component_fallback")):
                leaf_title_identity = normalize_semantic_title_identity(node.semantic_unit) or node.semantic_unit
                contextualized_fallback = fallback_not_elaboration_for_text(
                    semantic_basis,
                    boundary_shape=node.boundary_shape,
                    title_identity=leaf_title_identity,
                )
                normalized = normalize_not_elaboration_payload(
                    semantic_basis,
                    normalized,
                    boundary_shape=node.boundary_shape,
                    related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                    title_identity=leaf_title_identity,
                )
                normalized.update(
                    {
                        "prompt_directive_kind": str(contextualized_fallback.get("prompt_directive_kind", "")).strip(),
                        "prompt_directive_focus": str(contextualized_fallback.get("prompt_directive_focus", "")).strip(),
                        "prompt_directive_compared_terms": list(contextualized_fallback.get("prompt_directive_compared_terms", [])),
                        "prompt_directive_expectations": list(contextualized_fallback.get("prompt_directive_expectations", [])),
                        "prompt_directive_requires_formula": bool(contextualized_fallback.get("prompt_directive_requires_formula", False)),
                        "prompt_directive_requires_contrast": bool(contextualized_fallback.get("prompt_directive_requires_contrast", False)),
                        "prompt_directive_requires_chain": bool(contextualized_fallback.get("prompt_directive_requires_chain", False)),
                        "prompt_directive_requires_substrate": bool(contextualized_fallback.get("prompt_directive_requires_substrate", False)),
                        "action_posture": str(contextualized_fallback.get("action_posture", "")).strip(),
                        "lookup_keys": ordered_unique(
                            list(contextualized_fallback.get("lookup_keys", []))
                            + list(normalized.get("lookup_keys", []))
                        )[:24],
                        "title_depth_body_split_reason": (
                            collapse_ws(str(normalized.get("title_depth_body_split_reason", "")).strip())
                            or "Fallback relation components should remain determinate leaves instead of re-splitting under the parent prompt surface."
                        ),
                        "title_depth_reuse_bias": str(normalized.get("title_depth_reuse_bias", "")).strip() or "determinate_reuse",
                    }
                )
                normalized["title_identity"] = leaf_title_identity
                normalized["component_nots"] = []
                normalized["title_depth_body_split_needed"] = False
                normalized["title_depth_segments"] = [leaf_title_identity]
                normalized["title_depth_prefixes"] = [leaf_title_identity]
                normalized["title_depth_exposed_depth"] = 1
                normalized["title_depth_minimal_sufficient_depth"] = 1
            existing_assessment = collapse_ws(str(normalized.get("title_depth_assessment", "")).strip())
            has_contextual_title_inference = existing_assessment not in {"", "surface_unsegmented", "surface_segmented"}
            if has_contextual_title_inference:
                node.metadata["not_elaboration"] = normalized
                node.metadata["structured_learning"] = normalized
                return normalized

        fallback = fallback_not_elaboration_for_text(
            node.semantic_unit,
            boundary_shape=node.boundary_shape,
            title_identity=node.semantic_unit,
        )
        prompt_directive = semantic_prompt_directive_profile(node.semantic_unit)
        title_depth_prior = derive_semantic_title_depth_view(node.semantic_unit)
        root_local_namespace = self.root_local_title_namespace_payload(node)
        parent_context = self.decomposition_parent_context_payload(node)
        certain_sibling_context = self.decomposition_certain_sibling_context_payload(node)
        proposal = self.request_proposal(
            proposal_type=ProposalType.NOT_ELABORATION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Represent the active item as a still-unachieved task.
                Represent the non-achievedness, not the answer.

                Title-depth law (infer from the formal title and context; it is never explicitly specified):
                {title_depth_theory_prompt_block()}

                If correctness mattered critically:
                - what exactly is being asked?
                - what intended object would count as realized?
                - what success conditions would make closure justified?
                - what is already present as the current actual realization?
                - what is already given?
                - what is still unknown?
                - what remains missing?
                - what is present but would become distorted if the wrong case were assumed?
                - what distinctions matter for the next step?
                - which nearby cases must not be collapsed together?
                - what assumptions would be unsafe?
                - what would make closure wrong if guessed too early?
                - where does the remainder mainly originate?
                - how severe is the remaining non-achievedness?
                - what is the smallest governed repair, and what would fully dissolve the remainder?

                Return JSON with these fields:
                - title_identity
                - encountered_not
                - goal
                - intended_object
                - success_criteria
                - actual_realization
                - givens
                - unknowns
                - missing_components
                - distorted_components
                - differentiators
                - contrastive_cases
                - risk_of_wrong_closure
                - disallowed_assumptions
                - misalignment_types
                - origin_layers
                - degree
                - remainder_shapes
                - why_it_matters
                - minimal_repair
                - full_repair
                - boundary_shape
                - action_posture
                - title_depth_minimal_sufficient_depth
                - title_depth_assessment
                - title_depth_hidden_depth_note
                - title_depth_body_split_needed
                - title_depth_body_split_reason
                - title_depth_reuse_bias
                - title_similar_identities
                - component_nots
                - composed_not
                - prompt_directive_kind
                - prompt_directive_focus
                - prompt_directive_compared_terms
                - prompt_directive_expectations
                - prompt_directive_requires_formula
                - prompt_directive_requires_contrast
                - prompt_directive_requires_chain
                - prompt_directive_requires_substrate
                - lookup_keys

                Rules:
                - use only a*, a'*, b*, b'*, c*, c'*, d*, d'* in boundary_shape
                - use only specification, semantic, structural, functional, epistemic, contextual, completion, precision, fidelity, modal in misalignment_types
                - use only prompt, model, tool, knowledge, constraint, ontological in origin_layers
                - use only null, residual, partial, dominant, total, category_error in degree
                - use only missing, distorted, misweighted, misplaced, prematurely_closed, overgenerated, underdetermined, self_contradictory, externally_inconsistent, blocked in remainder_shapes
                - * means one or more occurrences of the lane kind
                - preserve caller perspective when describing the boundary
                - infer title_identity so it is minimally sufficient, stable, and non-colliding in the root-local semantic namespace below
                - infer title-depth adequacy from context; do not pretend the title author explicitly specified it
                - use title-depth to decide whether body decomposition is really needed
                - preserve the prompt directive below as part of the non-achievedness itself
                - if the directive is state, keep the requested law or relation surface explicit
                - if the directive is distinguish, keep both contrasted cases explicit
                - if the directive is derive or construct, preserve the ordered intermediate chain rather than jumping straight to the end
                - if the directive is identify_reusable_substrate, separate the broader reusable substrate from the narrower determinate case
                - use only the provided root-local titles as reusable namespace material; do not assume any external corpus
                - you may reuse any provided root-local title if it is already the correct semantic identity
                - parent overview and prior certain siblings are background only
                - do not solve the task here
                - do not collapse unresolved alternatives into a confirmed case
                - omit decorative paraphrase

                Active item:
                {node.semantic_unit}

                Parent overview:
                {json.dumps(parent_context, indent=2, sort_keys=True)}

                Prior certain siblings:
                {json.dumps(certain_sibling_context, indent=2, sort_keys=True)}

                Derived title-depth context:
                {json.dumps(title_depth_prior, indent=2, sort_keys=True)}

                Prompt directive:
                {json.dumps(prompt_directive, indent=2, sort_keys=True)}

                Root-local title namespace:
                {json.dumps(root_local_namespace, indent=2, sort_keys=True)}
                """
            ),
            fallback_payload=fallback,
            mode=self.select_supplement_mode("not_elaboration", node),
        )
        normalized = normalize_not_elaboration_payload(
            semantic_basis,
            proposal.payload,
            boundary_shape=node.boundary_shape,
            related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
            title_identity=node.semantic_unit,
        )
        normalized["title_identity"] = self.resolve_root_local_title_identity(
            node=node,
            proposed_title=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
        )
        normalized_directive_kind = collapse_ws(str(normalized.get("prompt_directive_kind", "")).strip())
        if node.role == "generic" and bool(node.metadata.get("component_fallback")):
            normalized["title_identity"] = normalize_semantic_title_identity(node.semantic_unit) or node.semantic_unit
            normalized["component_nots"] = []
            normalized["title_depth_body_split_needed"] = False
            if not collapse_ws(str(normalized.get("title_depth_body_split_reason", "")).strip()):
                normalized["title_depth_body_split_reason"] = (
                    "Fallback relation components should remain determinate leaves instead of re-splitting under the parent prompt surface."
                )
        normalized_compared_terms = [
            str(item).strip()
            for item in normalized.get("prompt_directive_compared_terms", [])
            if str(item).strip()
        ] if isinstance(normalized.get("prompt_directive_compared_terms", []), list) else []
        inferred_chain_components: list[str] = []
        if (
            node.role == "root"
            and normalized_directive_kind in {"construct", "derive"}
            and bool(normalized.get("prompt_directive_requires_chain", False))
        ):
            inferred_chain_components = semantic_chain_decomposition_components(node.semantic_unit)
            if len(inferred_chain_components) >= 2:
                normalized["component_nots"] = inferred_chain_components
                normalized["title_depth_body_split_needed"] = True
                if not collapse_ws(str(normalized.get("title_depth_body_split_reason", "")).strip()):
                    normalized["title_depth_body_split_reason"] = (
                        "The prompt requests an ordered transformation chain whose intermediate relations must remain explicit."
                    )
        preserve_parent_prompt_surface = (
            node.role == "root"
            and not bool(normalized.get("title_depth_body_split_needed", False))
            and (
                (
                    normalized_directive_kind == "construct"
                    and bool(normalized.get("prompt_directive_requires_chain", False))
                    and not inferred_chain_components
                    and self.should_preserve_construct_chain_prompt_surface(node.semantic_unit)
                )
                or (normalized_directive_kind == "distinguish" and len(normalized_compared_terms) >= 2)
                or (
                    normalized_directive_kind == "identify_reusable_substrate"
                    and bool(normalized.get("prompt_directive_requires_substrate", False))
                )
            )
        )
        component_nots = normalized.get("component_nots", [])
        if isinstance(component_nots, list) and component_nots and not preserve_parent_prompt_surface:
            normalized["component_nots"] = self.canonicalize_semantic_io_titles(
                anchor_title=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
                item_names=[str(item).strip() for item in component_nots if str(item).strip()],
                exclude_titles=[str(normalized.get("title_identity", "")).strip() or node.semantic_unit],
            )
        renormalized = normalize_not_elaboration_payload(
            node.semantic_unit,
            normalized,
            boundary_shape=node.boundary_shape,
            related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
            title_identity=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
        )
        normalized = self.refine_structured_learning_from_reuse(node, renormalized)
        normalized["title_identity"] = self.resolve_root_local_title_identity(
            node=node,
            proposed_title=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
        )
        refined_component_nots = normalized.get("component_nots", [])
        if isinstance(refined_component_nots, list) and refined_component_nots and not preserve_parent_prompt_surface:
            contextualized = self.structured_learning_view_for_text(
                node.semantic_unit,
                title_identity=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
                encountered_not=str(normalized.get("encountered_not", "")).strip(),
                component_nots=[
                    derive_semantic_title_depth_segments(str(item).strip())[-1]
                    if derive_semantic_title_depth_segments(str(item).strip())
                    else str(item).strip()
                    for item in refined_component_nots
                    if str(item).strip()
                ],
                composed_not=str(normalized.get("composed_not", "")).strip(),
                related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                intended_object=str(normalized.get("intended_object", "")).strip(),
                success_criteria=normalized.get("success_criteria", []),
                actual_realization=str(normalized.get("actual_realization", "")).strip(),
                givens=normalized.get("givens", []),
                unknowns=normalized.get("unknowns", []),
                missing_components=normalized.get("missing_components", []),
                distorted_components=normalized.get("distorted_components", []),
                differentiators=normalized.get("differentiators", []),
                contrastive_cases=normalized.get("contrastive_cases", []),
                risk_of_wrong_closure=normalized.get("risk_of_wrong_closure", []),
                disallowed_assumptions=normalized.get("disallowed_assumptions", []),
                misalignment_types=normalized.get("misalignment_types", []),
                origin_layers=normalized.get("origin_layers", []),
                degree=str(normalized.get("degree", "")).strip(),
                remainder_shapes=normalized.get("remainder_shapes", []),
                why_it_matters=normalized.get("why_it_matters", []),
                minimal_repair=normalized.get("minimal_repair", []),
                full_repair=normalized.get("full_repair", []),
                action_posture=str(normalized.get("action_posture", "")).strip(),
                boundary_shape=node.boundary_shape,
                title_similar_identities=normalized.get("title_similar_identities", []),
                title_depth_body_split_needed=bool(normalized.get("title_depth_body_split_needed", False)),
                title_depth_body_split_reason=str(normalized.get("title_depth_body_split_reason", "")).strip(),
                title_depth_reuse_bias=str(normalized.get("title_depth_reuse_bias", "")).strip(),
            )
            normalized["component_nots"] = list(contextualized.get("component_nots", refined_component_nots))
            if (
                bool(normalized.get("title_depth_body_split_needed", False))
                and not [str(item).strip() for item in normalized.get("component_nots", []) if str(item).strip()]
                and refined_component_nots
            ):
                normalized["component_nots"] = [
                    str(item).strip()
                    for item in refined_component_nots
                    if str(item).strip()
                ]
        refined_component_nots = normalized.get("component_nots", [])
        if (
            isinstance(refined_component_nots, list)
            and refined_component_nots
            and not bool(normalized.get("title_depth_body_split_needed", False))
            and not preserve_parent_prompt_surface
        ):
            normalized["component_nots"] = self.canonicalize_semantic_io_titles(
                anchor_title=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
                item_names=[str(item).strip() for item in refined_component_nots if str(item).strip()],
                exclude_titles=[str(normalized.get("title_identity", "")).strip() or node.semantic_unit],
            )
        if preserve_parent_prompt_surface:
            normalized = self.structured_learning_view_for_text(
                node.semantic_unit,
                title_identity=str(normalized.get("title_identity", "")).strip() or node.semantic_unit,
                encountered_not=str(normalized.get("encountered_not", "")).strip(),
                component_nots=[],
                composed_not=str(normalized.get("encountered_not", "")).strip() or str(normalized.get("composed_not", "")).strip(),
                related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                intended_object=str(normalized.get("intended_object", "")).strip(),
                success_criteria=normalized.get("success_criteria", []),
                actual_realization=str(normalized.get("actual_realization", "")).strip(),
                givens=normalized.get("givens", []),
                unknowns=normalized.get("unknowns", []),
                missing_components=normalized.get("missing_components", []),
                distorted_components=normalized.get("distorted_components", []),
                differentiators=normalized.get("differentiators", []),
                contrastive_cases=normalized.get("contrastive_cases", []),
                risk_of_wrong_closure=normalized.get("risk_of_wrong_closure", []),
                disallowed_assumptions=normalized.get("disallowed_assumptions", []),
                misalignment_types=normalized.get("misalignment_types", []),
                origin_layers=normalized.get("origin_layers", []),
                degree=str(normalized.get("degree", "")).strip(),
                remainder_shapes=normalized.get("remainder_shapes", []),
                why_it_matters=normalized.get("why_it_matters", []),
                minimal_repair=normalized.get("minimal_repair", []),
                full_repair=normalized.get("full_repair", []),
                action_posture=str(normalized.get("action_posture", "")).strip(),
                boundary_shape=node.boundary_shape,
                title_similar_identities=normalized.get("title_similar_identities", []),
                title_depth_body_split_needed=bool(normalized.get("title_depth_body_split_needed", False)),
                title_depth_body_split_reason=str(normalized.get("title_depth_body_split_reason", "")).strip(),
                title_depth_reuse_bias=str(normalized.get("title_depth_reuse_bias", "")).strip(),
            )
        if (
            bool(normalized.get("title_depth_body_split_needed", False))
            and not [str(item).strip() for item in normalized.get("component_nots", []) if str(item).strip()]
        ):
            requested_phrases = semantic_requested_output_phrases(node.semantic_unit)
            semantic_context = " ".join(
                part
                for part in [
                    node.semantic_unit,
                    str(normalized.get("title_identity", "")).strip(),
                    str(normalized.get("encountered_not", "")).strip(),
                    str(normalized.get("intended_object", "")).strip(),
                ]
                if collapse_ws(part)
            )
            recovered_components: list[str] = []
            for phrase in requested_phrases:
                matched_title = (
                    self.best_reusable_title_for_phrase(phrase, semantic_context=semantic_context)
                    or self.reusable_semantic_title_match(hint=phrase)
                )
                recovered_component = (
                    display_title_leaf_text(matched_title)
                    if matched_title
                    else (titleize_semantic_unit(phrase) or collapse_ws(phrase))
                )
                if recovered_component:
                    recovered_components.append(recovered_component)
            if recovered_components:
                normalized["component_nots"] = ordered_unique(recovered_components)
        if node.role == "generic" and bool(node.metadata.get("component_fallback")):
            leaf_title_identity = normalize_semantic_title_identity(node.semantic_unit) or node.semantic_unit
            contextualized_fallback = fallback_not_elaboration_for_text(
                semantic_basis,
                boundary_shape=node.boundary_shape,
                title_identity=leaf_title_identity,
            )
            normalized = normalize_not_elaboration_payload(
                semantic_basis,
                normalized,
                boundary_shape=node.boundary_shape,
                related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
                title_identity=leaf_title_identity,
            )
            normalized["title_identity"] = leaf_title_identity
            normalized["component_nots"] = []
            normalized["title_depth_body_split_needed"] = False
            normalized["prompt_directive_kind"] = str(contextualized_fallback.get("prompt_directive_kind", "")).strip()
            normalized["prompt_directive_focus"] = str(contextualized_fallback.get("prompt_directive_focus", "")).strip()
            normalized["prompt_directive_compared_terms"] = list(contextualized_fallback.get("prompt_directive_compared_terms", []))
            normalized["prompt_directive_expectations"] = list(contextualized_fallback.get("prompt_directive_expectations", []))
            normalized["prompt_directive_requires_formula"] = bool(contextualized_fallback.get("prompt_directive_requires_formula", False))
            normalized["prompt_directive_requires_contrast"] = bool(contextualized_fallback.get("prompt_directive_requires_contrast", False))
            normalized["prompt_directive_requires_chain"] = bool(contextualized_fallback.get("prompt_directive_requires_chain", False))
            normalized["prompt_directive_requires_substrate"] = bool(contextualized_fallback.get("prompt_directive_requires_substrate", False))
            normalized["action_posture"] = str(contextualized_fallback.get("action_posture", "")).strip()
            normalized["lookup_keys"] = ordered_unique(
                list(contextualized_fallback.get("lookup_keys", []))
                + list(normalized.get("lookup_keys", []))
            )[:24]
            normalized["title_depth_body_split_reason"] = (
                collapse_ws(str(normalized.get("title_depth_body_split_reason", "")).strip())
                or "Fallback relation components should remain determinate leaves instead of re-splitting under the parent prompt surface."
            )
            normalized["title_depth_reuse_bias"] = str(normalized.get("title_depth_reuse_bias", "")).strip() or "determinate_reuse"
            normalized["title_depth_segments"] = [leaf_title_identity]
            normalized["title_depth_prefixes"] = [leaf_title_identity]
            normalized["title_depth_exposed_depth"] = 1
            normalized["title_depth_minimal_sufficient_depth"] = 1
        node.metadata["not_elaboration_proposal_id"] = proposal.id
        node.metadata["not_elaboration"] = normalized
        node.metadata["structured_learning"] = normalized
        self.admit_proposal(
            proposal,
            rationale="Non-achievedness elaboration proposals are admissible working representations of what remains unsettled and why.",
        )
        return normalized

    def learned_component_hints(self, semantic_unit: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling learned component hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `learned_component_hints(semantic_unit='Physics / Force / Force From Mass And Acceleration')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `learned_component_hints`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `learned_component_hints`.
        """
        semantic_text = str(semantic_unit).strip()
        core_tokens = learning_core_tokens(semantic_text)
        if len(core_tokens) < 2:
            return []
        full_key = " ".join(core_tokens)
        token_set = set(core_tokens)
        hints: list[str] = []
        for artifact in self.reusable_artifact_candidates():
            prior = self.artifact_structured_learning_view(artifact)
            prior_not = str(prior.get("encountered_not", "")).strip()
            if not prior_not:
                continue
            prior_tokens = learning_core_tokens(prior_not)
            if not prior_tokens:
                continue
            prior_key = " ".join(prior_tokens)
            if prior_key == full_key or len(prior_tokens) >= len(core_tokens):
                continue
            if set(prior_tokens).issubset(token_set):
                hints.append(titleize_semantic_unit(prior_not) or prior_not)
        return ordered_unique(hints)[:4]

    def similar_title_identities(
        self,
        title_identity: str,
        *,
        exclude_titles: Iterable[str] | None = None,
        limit: int = 6,
    ) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling similar title identities.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `similar_title_identities(title_identity='Physics / Force / Force From Mass And Acceleration', exclude_titles=['Physics', 'Force', 'Force From Mass And Acceleration'], limit=3)`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title_identity: Value for `title_identity` used by `similar_title_identities`. Expected type: `str`.
            exclude_titles: Value for `exclude_titles` used by `similar_title_identities`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            limit: Value for `limit` used by `similar_title_identities`. Expected type: `int`. Defaults to `6`.

        Returns:
            list[str]: Result produced by `similar_title_identities`.
        """
        normalized_title_identity = normalize_semantic_title_identity(title_identity)
        if not normalized_title_identity:
            return []
        excluded_keys = {
            semantic_namespace_key(item)
            for item in ([normalized_title_identity, *(exclude_titles or [])])
            if str(item).strip()
        }
        query_variants = ordered_unique(
            (
                prolog_title_query_variants(normalized_title_identity)
                if looks_like_prolog_title_identity(normalized_title_identity)
                else [normalized_title_identity] + list(semantic_title_depth_prefix_chain(normalized_title_identity))
            )
        )
        matches: list[str] = []
        for query_text in reversed(query_variants):
            try:
                artifacts = self.store_relevant_artifacts(query_text, limit=max(limit * 2, 8))
            except Exception:
                break
            for artifact in artifacts:
                artifact_title = normalize_semantic_title_identity(getattr(artifact, "title", ""))
                if not artifact_title:
                    continue
                artifact_key = semantic_namespace_key(artifact_title)
                if artifact_key in excluded_keys:
                    continue
                excluded_keys.add(artifact_key)
                matches.append(artifact_title)
                if len(matches) >= limit:
                    return ordered_unique(matches)[:limit]
        return ordered_unique(matches)[:limit]

    def node_title_identity(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling node title identity.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `node_title_identity(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `node_title_identity`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `node_title_identity`.
        """
        stored = node.metadata.get("not_elaboration", {})
        if isinstance(stored, Mapping):
            title_identity = structured_title_identity_text(stored)
            if title_identity:
                return title_identity
        semantic_title = normalize_semantic_title_identity(node.semantic_unit)
        if semantic_title:
            return semantic_title
        return ""

    def node_root_local_title_identity(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling node root local title identity.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `node_root_local_title_identity(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `node_root_local_title_identity`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `node_root_local_title_identity`.
        """
        semantic_title = normalize_semantic_title_identity(node.semantic_unit)
        if semantic_title:
            return semantic_title
        return self.node_title_identity(node)

    def shared_reusable_family_title(self, titles: Iterable[str]) -> str:
        """
        High Level Purpose:
            In circumstances like title-depth grounding from multiple reusable determinate artifacts, helps with recovering a shared slash-bearing family title instead of leaving the current item at the raw prompt surface.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `shared_reusable_family_title(titles=['Cylinder Measures / Total Surface Area Of A Cylinder', 'Cylinder Measures / Volume Of A Cylinder'])`
            Output: 'Geometry / Cylinder Measures'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            titles: Value for `titles` used by `shared_reusable_family_title`. Expected type: `Iterable[str]`.

        Returns:
            str: Result produced by `shared_reusable_family_title`.
        """
        normalized_titles = [
            normalize_semantic_title_identity(str(title).strip())
            for title in titles
            if normalize_semantic_title_identity(str(title).strip())
        ]
        if not normalized_titles:
            return ""
        segment_sets = [derive_semantic_title_depth_segments(title) for title in normalized_titles]
        if not segment_sets:
            return ""
        common_segments: list[str] = []
        for parts in zip(*segment_sets):
            if len({semantic_namespace_key(str(part).strip()) for part in parts if str(part).strip()}) != 1:
                break
            common_segments.append(str(parts[0]).strip())
        if not common_segments:
            return ""
        if len(common_segments) == 1:
            resolved_titles: list[str] = []
            for normalized_title in normalized_titles:
                title_segments = derive_semantic_title_depth_segments(normalized_title)
                extension_candidates = sorted(
                    {
                        candidate_title
                        for artifact in self.reusable_artifact_candidates()
                        for candidate_title in [normalize_semantic_title_identity(str(artifact.title).strip())]
                        if candidate_title
                        and len(derive_semantic_title_depth_segments(candidate_title)) > len(title_segments)
                        and [
                            semantic_namespace_key(segment)
                            for segment in derive_semantic_title_depth_segments(candidate_title)[-len(title_segments):]
                        ] == [semantic_namespace_key(segment) for segment in title_segments]
                    },
                    key=lambda item: (len(derive_semantic_title_depth_segments(item)), len(item), item.casefold()),
                )
                if len(extension_candidates) > 1:
                    return ""
                if len(extension_candidates) == 1:
                    resolved_titles.append(extension_candidates[0])
            if len(resolved_titles) == len(normalized_titles):
                resolved_segment_sets = [derive_semantic_title_depth_segments(title) for title in resolved_titles]
                resolved_common_segments: list[str] = []
                for parts in zip(*resolved_segment_sets):
                    if len({semantic_namespace_key(str(part).strip()) for part in parts if str(part).strip()}) != 1:
                        break
                    resolved_common_segments.append(str(parts[0]).strip())
                common_title = " / ".join(resolved_common_segments)
                if len(resolved_common_segments) >= 2 and "/" in common_title:
                    return common_title
            return ""
        common_title = " / ".join(common_segments)
        return common_title if len(common_segments) >= 2 and "/" in common_title else ""

    def best_reusable_title_for_phrase(self, phrase: str, *, semantic_context: str = "") -> str:
        """
        High Level Purpose:
            In circumstances like grounding a prompt-local requested output phrase in an already learned reusable family, helps with selecting the best matching reusable title even when vector retrieval is too loose or too sparse.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `best_reusable_title_for_phrase(phrase='total surface area')`
            Output: 'Cylinder Measures / Total Surface Area Of A Cylinder'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            phrase: Value for `phrase` used by `best_reusable_title_for_phrase`. Expected type: `str`.

        Returns:
            str: Result produced by `best_reusable_title_for_phrase`.
        """
        normalized_phrase = collapse_ws(str(phrase or "").strip())
        normalized_context = collapse_ws(str(semantic_context or "").strip())
        phrase_tokens = set(learning_core_tokens(normalized_phrase))
        if not phrase_tokens:
            return ""
        context_tokens = set(learning_core_tokens(normalized_context)) - phrase_tokens
        best_title = ""
        best_score = -1
        for artifact in self.reusable_artifact_candidates():
            candidate_title = normalize_semantic_title_identity(str(artifact.title).strip())
            if not candidate_title:
                continue
            if candidate_title.casefold().startswith("structured learning record for ".casefold()):
                continue
            if "/" not in candidate_title:
                continue
            candidate_tokens = set(learning_core_tokens(candidate_title))
            overlap = len(phrase_tokens & candidate_tokens)
            if overlap <= 0:
                continue
            score = overlap * 10
            if phrase_tokens.issubset(candidate_tokens):
                score += 20
            context_overlap = len(context_tokens & candidate_tokens)
            if context_tokens:
                score += context_overlap * 6
                if context_overlap == 0:
                    score -= 8
            score += max(artifact_focus_alignment_score(artifact, normalized_phrase), 0) * 5
            if "/" in candidate_title:
                score += 2
            if len(derive_semantic_title_depth_segments(candidate_title)) >= 2:
                score += 2
            if score > best_score:
                best_score = score
                best_title = candidate_title
        return best_title

    def refine_structured_learning_from_reuse(self, node: SemanticNode, structured: Mapping[str, Any]) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like title-depth grounding for reusable compute families, helps with promoting a raw prompt-surface structured-learning payload into a stable slash-bearing title identity and body-level split when reusable artifacts already supply that family.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `refine_structured_learning_from_reuse(node=SemanticNode(id='not-cylinder', semantic_unit='Break this down carefully...'), structured={'title_identity': 'Break this down carefully...'})`
            Output: {'title_identity': 'Geometry / Cylinder Measures', 'component_nots': ['Total Surface Area Of A Cylinder', 'Volume Of A Cylinder']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `refine_structured_learning_from_reuse`. Expected type: `SemanticNode`.
            structured: Value for `structured` used by `refine_structured_learning_from_reuse`. Expected type: `Mapping[str, Any]`.

        Returns:
            dict[str, Any]: Result produced by `refine_structured_learning_from_reuse`.
        """
        semantic_unit = str(node.semantic_unit or "").strip()
        if not semantic_unit:
            return dict(structured)
        refined = dict(structured)
        current_title = normalize_semantic_title_identity(str(refined.get("title_identity", "")).strip())
        requested_phrases = semantic_requested_output_phrases(semantic_unit)
        semantic_context = " ".join(
            part
            for part in [
                semantic_unit,
                current_title,
                collapse_ws(str(refined.get("intended_object", "")).strip()),
                " ".join(
                    str(item).strip()
                    for item in refined.get("givens", [])
                    if str(item).strip()
                ) if isinstance(refined.get("givens", []), list) else "",
            ]
            if collapse_ws(part)
        )
        matched_titles: list[str] = []
        component_titles: list[str] = []
        requested_component_titles = ordered_unique(
            titleize_semantic_unit(phrase) or phrase
            for phrase in requested_phrases
            if titleize_semantic_unit(phrase) or phrase
        )
        title_changed = False
        for phrase in requested_phrases:
            matched_title = (
                self.best_reusable_title_for_phrase(phrase, semantic_context=semantic_context)
                or self.reusable_semantic_title_match(hint=phrase)
            )
            if matched_title:
                matched_titles.append(matched_title)
                component_titles.append(display_title_leaf_text(matched_title) or matched_title)
            else:
                titled_phrase = titleize_semantic_unit(phrase)
                if titled_phrase:
                    component_titles.append(titled_phrase)
        explicit_split_request = bool(
            re.search(
                r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
                semantic_unit,
                flags=re.IGNORECASE,
            )
        )
        effective_component_titles = component_titles if len(component_titles) >= 2 else requested_component_titles
        if explicit_split_request and len(effective_component_titles) >= 2:
            family_title = self.shared_reusable_family_title(matched_titles)
            if family_title:
                refined["title_identity"] = family_title
                title_changed = True
            refined["component_nots"] = ordered_unique(
                item
                for item in effective_component_titles
                if item and semantic_namespace_key(item) != semantic_namespace_key(str(refined.get("title_identity", "")).strip())
            )
            refined["title_depth_body_split_needed"] = True
            if not str(refined.get("title_depth_body_split_reason", "")).strip():
                refined["title_depth_body_split_reason"] = "the prompt explicitly requests separate results under a shared semantic family"
        elif "/" not in current_title:
            for matched_title in matched_titles:
                normalized_match = normalize_semantic_title_identity(matched_title)
                if normalized_match and "/" in normalized_match:
                    refined["title_identity"] = normalized_match
                    title_changed = True
                    break
        refined_title = normalize_semantic_title_identity(str(refined.get("title_identity", "")).strip())
        if refined_title and title_changed:
            refined["title_identity"] = self.resolve_root_local_title_identity(
                node=node,
                proposed_title=refined_title,
            )
        normalized_refined = normalize_not_elaboration_payload(
            node.semantic_unit,
            refined,
            boundary_shape=node.boundary_shape,
            related_artifact_titles=[artifact.title for artifact in list(self.state.learned_artifacts.values())[:4]],
            title_identity=str(refined.get("title_identity", "")).strip() or node.semantic_unit,
        )
        if explicit_split_request and len(effective_component_titles) >= 2:
            normalized_refined["component_nots"] = ordered_unique(
                item
                for item in effective_component_titles
                if item and semantic_namespace_key(item) != semantic_namespace_key(str(normalized_refined.get("title_identity", "")).strip())
            )
            normalized_refined["title_depth_body_split_needed"] = True
        return normalized_refined

    def root_local_title_namespace_payload(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for root local title namespace.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `root_local_title_namespace_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `root_local_title_namespace_payload`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `root_local_title_namespace_payload`.
        """
        root = self.state.root()
        current_parent = (
            self.state.graph.get_node(node.parent_id)
            if node.parent_id and node.parent_id in self.state.graph.nodes
            else None
        )
        parent_title = self.node_title_identity(current_parent) if current_parent is not None else ""
        entries: list[dict[str, Any]] = []
        for candidate in sorted(self.state.graph.nodes.values(), key=lambda item: (item.depth, item.semantic_unit.casefold())):
            title_identity = self.node_title_identity(candidate)
            if not title_identity:
                continue
            entries.append(
                {
                    "node_id": candidate.id,
                    "title_identity": title_identity,
                    "role": candidate.role,
                    "depth": candidate.depth,
                    "parent_id": candidate.parent_id or "",
                }
            )
        return {
            "root_node_id": root.id,
            "root_title_identity": self.node_title_identity(root),
            "current_node_id": node.id,
            "parent_node_id": current_parent.id if current_parent is not None else "",
            "parent_title_identity": parent_title,
            "current_insertion_handle": (
                f"{parent_title}:<current>"
                if parent_title and looks_like_prolog_title_identity(parent_title)
                else (f"{parent_title} / <current>" if parent_title else "<current>")
            ),
            "titles": entries,
        }

    def resolve_root_local_title_identity(
        self,
        *,
        node: SemanticNode,
        proposed_title: str,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with resolving root local title identity.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `resolve_root_local_title_identity(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), proposed_title='Physics / Force / Force From Mass And Acceleration')`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `resolve_root_local_title_identity`. Expected type: `SemanticNode`.
            proposed_title: Value for `proposed_title` used by `resolve_root_local_title_identity`. Expected type: `str`.

        Returns:
            str: Result produced by `resolve_root_local_title_identity`.
        """
        normalized_title = normalize_semantic_title_identity(proposed_title)
        if not normalized_title:
            return ""
        namespace_payload = self.root_local_title_namespace_payload(node)
        parent_title = str(namespace_payload.get("parent_title_identity", "")).strip()
        current_node_id = str(namespace_payload.get("current_node_id", "")).strip()
        current_node_local_title = ""
        for item in namespace_payload.get("titles", []):
            title_identity = str(item.get("title_identity", "")).strip()
            if not title_identity:
                continue
            if semantic_namespace_key(title_identity) != semantic_namespace_key(normalized_title):
                continue
            if str(item.get("node_id", "")).strip() == current_node_id:
                current_node_local_title = title_identity
                continue
            return title_identity
        if not parent_title:
            return current_node_local_title or normalized_title
        title_relation, _ = classify_title_depth_relation(parent_title, normalized_title)
        if title_relation in {"same_identity", "prior_is_ground_prefix", "prior_is_overdetermined_extension"}:
            return normalized_title
        return compose_semantic_title_identity(
            broader_category=parent_title,
            current_identity=normalized_title,
            fallback_title=normalized_title,
        )

    def semantic_title_match_score(
        self,
        *,
        hint: str,
        anchor_title: str,
        candidate_title: str,
    ) -> int:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling semantic title match score.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `semantic_title_match_score(hint='force', anchor_title='Physics / Force / Force From Mass And Acceleration', candidate_title='Physics / Force / Force From Mass And Acceleration')`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            hint: Value for `hint` used by `semantic_title_match_score`. Expected type: `str`.
            anchor_title: Value for `anchor_title` used by `semantic_title_match_score`. Expected type: `str`.
            candidate_title: Value for `candidate_title` used by `semantic_title_match_score`. Expected type: `str`.

        Returns:
            int: Result produced by `semantic_title_match_score`.
        """
        normalized_hint = normalize_semantic_title_identity(hint)
        normalized_candidate = normalize_semantic_title_identity(candidate_title)
        normalized_anchor = normalize_semantic_title_identity(anchor_title)
        if not normalized_hint or not normalized_candidate:
            return 0
        hinted_full = compose_semantic_title_identity(
            broader_category=normalized_anchor,
            current_identity=normalized_hint,
            fallback_title=normalized_hint,
        ) if normalized_anchor else normalized_hint
        hint_key = semantic_namespace_key(normalized_hint)
        hinted_full_key = semantic_namespace_key(hinted_full)
        candidate_key = semantic_namespace_key(normalized_candidate)
        if candidate_key == hinted_full_key:
            return 100
        if candidate_key == hint_key:
            return 99
        prolog_score = prolog_title_match_score(hinted_full, normalized_candidate)
        if prolog_score:
            return prolog_score
        relation_to_full, shared_depth = classify_title_depth_relation(hinted_full, normalized_candidate)
        if relation_to_full == "prior_is_ground_prefix":
            return 97
        if relation_to_full == "shared_ground_prefix" and shared_depth >= 1:
            return 88 + min(shared_depth, 4)
        hint_leaf = derive_semantic_title_depth_segments(normalized_hint)[-1]
        candidate_leaf = derive_semantic_title_depth_segments(normalized_candidate)[-1]
        if semantic_namespace_key(hint_leaf) == semantic_namespace_key(candidate_leaf):
            return 94
        overlap = len(set(learning_lookup_keys(normalized_hint)).intersection(set(learning_lookup_keys(normalized_candidate))))
        if overlap >= 2:
            return 70 + min(overlap, 8)
        return 0

    def reusable_semantic_title_match(
        self,
        *,
        hint: str,
        anchor_title: str = "",
        exclude_titles: Iterable[str] | None = None,
        limit: int = 8,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling reusable semantic title match.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `reusable_semantic_title_match(hint='force', anchor_title='Physics / Force / Force From Mass And Acceleration', exclude_titles=['Physics', 'Force', 'Force From Mass And Acceleration'], limit=3)`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            hint: Value for `hint` used by `reusable_semantic_title_match`. Expected type: `str`.
            anchor_title: Value for `anchor_title` used by `reusable_semantic_title_match`. Expected type: `str`. Defaults to `''`.
            exclude_titles: Value for `exclude_titles` used by `reusable_semantic_title_match`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            limit: Value for `limit` used by `reusable_semantic_title_match`. Expected type: `int`. Defaults to `8`.

        Returns:
            str: Result produced by `reusable_semantic_title_match`.
        """
        normalized_hint = normalize_semantic_title_identity(hint)
        if not normalized_hint:
            return ""
        excluded = {
            semantic_namespace_key(item)
            for item in (exclude_titles or [])
            if str(item).strip()
        }
        queries = ordered_unique(
            (
                prolog_title_query_variants(normalized_hint)
                + (
                    prolog_title_query_variants(
                        compose_semantic_title_identity(
                            broader_category=anchor_title,
                            current_identity=normalized_hint,
                            fallback_title=normalized_hint,
                        )
                    )
                    if str(anchor_title).strip()
                    else []
                )
                if looks_like_prolog_title_identity(normalized_hint)
                else [
                    normalized_hint,
                    compose_semantic_title_identity(
                        broader_category=anchor_title,
                        current_identity=normalized_hint,
                        fallback_title=normalized_hint,
                    ) if str(anchor_title).strip() else "",
                ]
            )
        )
        pool: list[Artifact] = []
        seen_ids: set[str] = set()
        for artifact in self.reusable_artifact_candidates():
            if artifact.id in seen_ids:
                continue
            seen_ids.add(artifact.id)
            pool.append(artifact)
        for query_text in queries:
            if not query_text:
                continue
            try:
                artifacts = self.store_relevant_artifacts(query_text, limit=max(limit * 2, 8))
            except Exception:
                continue
            for artifact in artifacts:
                if artifact.id in seen_ids:
                    continue
                seen_ids.add(artifact.id)
                pool.append(artifact)
        best_title = ""
        best_score = 0
        for artifact in pool:
            for surface in self.artifact_identity_surfaces(artifact):
                candidate_title = normalize_semantic_title_identity(surface)
                if not candidate_title:
                    continue
                if semantic_namespace_key(candidate_title) in excluded:
                    continue
                score = self.semantic_title_match_score(
                    hint=normalized_hint,
                    anchor_title=anchor_title,
                    candidate_title=candidate_title,
                )
                if score > best_score:
                    best_score = score
                    best_title = candidate_title
        return best_title if best_score >= 95 else ""

    def canonicalize_child_semantic_title(
        self,
        *,
        parent_title: str,
        proposed_title: str,
        prefer_store_reuse: bool,
        exclude_titles: Iterable[str] | None = None,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with canonicalizing child semantic title.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `canonicalize_child_semantic_title(parent_title='Physics / Force / Force From Mass And Acceleration', proposed_title='Physics / Force / Force From Mass And Acceleration', prefer_store_reuse=True, exclude_titles=['Physics', 'Force', 'Force From Mass And Acceleration'])`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            parent_title: Value for `parent_title` used by `canonicalize_child_semantic_title`. Expected type: `str`.
            proposed_title: Value for `proposed_title` used by `canonicalize_child_semantic_title`. Expected type: `str`.
            prefer_store_reuse: Value for `prefer_store_reuse` used by `canonicalize_child_semantic_title`. Expected type: `bool`.
            exclude_titles: Value for `exclude_titles` used by `canonicalize_child_semantic_title`. Expected type: `Iterable[str] | None`. Defaults to `None`.

        Returns:
            str: Result produced by `canonicalize_child_semantic_title`.
        """
        normalized_title = normalize_semantic_title_identity(proposed_title)
        if not normalized_title:
            return ""
        if prefer_store_reuse:
            reused = self.reusable_semantic_title_match(
                hint=normalized_title,
                anchor_title=parent_title,
                exclude_titles=exclude_titles,
            )
            if reused:
                relation_to_parent, _ = classify_title_depth_relation(parent_title, reused)
                if relation_to_parent not in {"same_identity", "prior_is_ground_prefix"}:
                    raw_lower = collapse_ws(normalized_title).lower()
                    reused_lower = collapse_ws(reused).lower()
                    leading_directive_match = re.match(
                        r"^\s*(derive|express|show|write|explain|identify|state|compare|distinguish)\b",
                        raw_lower,
                    )
                    reused_directive_match = re.match(
                        r"^\s*(derive|express|show|write|explain|identify|state|compare|distinguish)\b",
                        reused_lower,
                    )
                    directive_shift = bool(leading_directive_match) and (
                        leading_directive_match.group(1)
                        != (reused_directive_match.group(1) if reused_directive_match else "")
                    )
                    raw_tokens = set(selection_signal_tokens(raw_lower))
                    reused_tokens = set(selection_signal_tokens(reused))
                    stripped_focus_tokens = {
                        token
                        for token in raw_tokens - reused_tokens
                        if token
                        and token not in {
                            "a",
                            "an",
                            "and",
                            "example",
                            "for",
                            "formula",
                            "general",
                            "give",
                            "law",
                            "one",
                            "relation",
                            "state",
                            "the",
                            "using",
                        }
                    }
                    if directive_shift or (
                        stripped_focus_tokens
                        and (
                            re.search(r"\b(?:using|for)\b", raw_lower)
                            or len(stripped_focus_tokens) >= 2
                        )
                    ):
                        relation, _ = classify_title_depth_relation(parent_title, normalized_title)
                        if relation in {"same_identity", "prior_is_ground_prefix", "prior_is_overdetermined_extension"}:
                            return normalized_title
                        return compose_semantic_title_identity(
                            broader_category=parent_title,
                            current_identity=normalized_title,
                            fallback_title=normalized_title,
                        )
                    return reused
        if not parent_title:
            return normalized_title
        relation, _ = classify_title_depth_relation(parent_title, normalized_title)
        if relation in {"same_identity", "prior_is_ground_prefix", "prior_is_overdetermined_extension"}:
            return normalized_title
        return compose_semantic_title_identity(
            broader_category=parent_title,
            current_identity=normalized_title,
            fallback_title=normalized_title,
        )

    def canonicalize_semantic_io_titles(
        self,
        *,
        anchor_title: str,
        item_names: Iterable[str],
        exclude_titles: Iterable[str] | None = None,
    ) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with canonicalizing semantic io titles.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `canonicalize_semantic_io_titles(anchor_title='Physics / Force / Force From Mass And Acceleration', item_names=['mass', 'acceleration', 'force'], exclude_titles=['Physics', 'Force', 'Force From Mass And Acceleration'])`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            anchor_title: Value for `anchor_title` used by `canonicalize_semantic_io_titles`. Expected type: `str`.
            item_names: Value for `item_names` used by `canonicalize_semantic_io_titles`. Expected type: `Iterable[str]`.
            exclude_titles: Value for `exclude_titles` used by `canonicalize_semantic_io_titles`. Expected type: `Iterable[str] | None`. Defaults to `None`.

        Returns:
            list[str]: Result produced by `canonicalize_semantic_io_titles`.
        """
        resolved: list[str] = []
        for item_name in item_names:
            raw_name = collapse_ws(str(item_name).strip())
            if not raw_name:
                continue
            if re.fullmatch(r"[a-z0-9_]+", raw_name):
                raw_name = raw_name.replace("_", " ")
                raw_name = " ".join(part.capitalize() if part else "" for part in raw_name.split())
            normalized_name = normalize_semantic_title_identity(raw_name)
            if not normalized_name:
                continue
            resolved.append(
                self.canonicalize_child_semantic_title(
                    parent_title=anchor_title,
                    proposed_title=normalized_name,
                    prefer_store_reuse=True,
                    exclude_titles=[anchor_title, *list(exclude_titles or []), *resolved],
                )
            )
        return ordered_unique(resolved)

    def title_depth_namespace_guardrails_payload(
        self,
        title_identity: str,
        *,
        reserved_semantic_units: Iterable[str] | None = None,
        limit: int = 6,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for title depth namespace guardrails.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `title_depth_namespace_guardrails_payload(title_identity='Physics / Force / Force From Mass And Acceleration', reserved_semantic_units=['mass', 'acceleration', 'force'], limit=3)`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title_identity: Value for `title_identity` used by `title_depth_namespace_guardrails_payload`. Expected type: `str`.
            reserved_semantic_units: Value for `reserved_semantic_units` used by `title_depth_namespace_guardrails_payload`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            limit: Value for `limit` used by `title_depth_namespace_guardrails_payload`. Expected type: `int`. Defaults to `6`.

        Returns:
            dict[str, Any]: Result produced by `title_depth_namespace_guardrails_payload`.
        """
        normalized_title_identity = normalize_semantic_title_identity(title_identity)
        title_depth_view = derive_semantic_title_depth_view(normalized_title_identity)
        reserved_units = ordered_unique(
            normalize_semantic_title_identity(str(item).strip()) or collapse_ws(str(item).strip())
            for item in (reserved_semantic_units or [])
            if str(item).strip()
        )
        nearby_titles = self.similar_title_identities(
            normalized_title_identity,
            exclude_titles=[normalized_title_identity, *reserved_units],
            limit=limit,
        )
        return {
            "title_identity": normalized_title_identity,
            "title_depth_segments": list(title_depth_view["segments"]),
            "title_depth_prefixes": list(title_depth_view["prefixes"]),
            "ground_reuse_prefixes": list(title_depth_view["prefixes"][:-1]),
            "determinate_reuse_identity": normalized_title_identity,
            "reserved_semantic_units": reserved_units,
            "nearby_artifact_titles": nearby_titles,
            "collision_rules": [
                "Do not duplicate the active title identity.",
                "Do not restate a title prefix as if it were a distinct sibling identity.",
                "Do not collide with already-settled nearby semantic units or nearby artifact titles.",
                "If the full title is already minimally sufficient, preserve the parent instead of emitting decorative children.",
            ],
        }

    def structured_learning_view_for_text(
        self,
        semantic_unit: str,
        *,
        title_identity: str = "",
        encountered_not: str = "",
        component_nots: Iterable[str] | None = None,
        composed_not: str = "",
        related_artifact_titles: list[str] | None = None,
        intended_object: str = "",
        success_criteria: Iterable[str] | None = None,
        actual_realization: str = "",
        givens: Iterable[str] | None = None,
        unknowns: Iterable[str] | None = None,
        missing_components: Iterable[str] | None = None,
        distorted_components: Iterable[str] | None = None,
        differentiators: Iterable[str] | None = None,
        contrastive_cases: Iterable[str] | None = None,
        risk_of_wrong_closure: Iterable[str] | None = None,
        disallowed_assumptions: Iterable[str] | None = None,
        misalignment_types: Iterable[str] | None = None,
        origin_layers: Iterable[str] | None = None,
        degree: str = "",
        remainder_shapes: Iterable[str] | None = None,
        why_it_matters: Iterable[str] | None = None,
        minimal_repair: Iterable[str] | None = None,
        full_repair: Iterable[str] | None = None,
        action_posture: str = "",
        boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
        title_similar_identities: Iterable[str] | None = None,
        title_depth_body_split_needed: bool = False,
        title_depth_body_split_reason: str = "",
        title_depth_reuse_bias: str = "",
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling structured learning view for text.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `structured_learning_view_for_text(semantic_unit='Physics / Force / Force From Mass And Acceleration', title_identity='Physics / Force / Force From Mass And Acceleration', encountered_not='force', component_nots=['mass', 'acceleration', 'force'])`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            semantic_unit: Value for `semantic_unit` used by `structured_learning_view_for_text`. Expected type: `str`.
            title_identity: Value for `title_identity` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            encountered_not: Value for `encountered_not` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            component_nots: Value for `component_nots` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            composed_not: Value for `composed_not` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            related_artifact_titles: Value for `related_artifact_titles` used by `structured_learning_view_for_text`. Expected type: `list[str] | None`. Defaults to `None`.
            intended_object: Value for `intended_object` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            success_criteria: Value for `success_criteria` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            actual_realization: Value for `actual_realization` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            givens: Value for `givens` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            unknowns: Value for `unknowns` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            missing_components: Value for `missing_components` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            distorted_components: Value for `distorted_components` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            differentiators: Value for `differentiators` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            contrastive_cases: Value for `contrastive_cases` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            risk_of_wrong_closure: Value for `risk_of_wrong_closure` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            disallowed_assumptions: Value for `disallowed_assumptions` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            misalignment_types: Value for `misalignment_types` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            origin_layers: Value for `origin_layers` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            degree: Value for `degree` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            remainder_shapes: Value for `remainder_shapes` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            why_it_matters: Value for `why_it_matters` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            minimal_repair: Value for `minimal_repair` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            full_repair: Value for `full_repair` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.
            action_posture: Value for `action_posture` used by `structured_learning_view_for_text`. Expected type: `str`. Defaults to `''`.
            boundary_shape: Value for `boundary_shape` used by `structured_learning_view_for_text`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.
            title_similar_identities: Value for `title_similar_identities` used by `structured_learning_view_for_text`. Expected type: `Iterable[str] | None`. Defaults to `None`.

        Returns:
            dict[str, Any]: Result produced by `structured_learning_view_for_text`.
        """
        semantic_text = str(semantic_unit).strip()
        normalized_title_identity = normalize_semantic_title_identity(title_identity or semantic_text)
        fallback = fallback_not_elaboration_for_text(
            semantic_text,
            boundary_shape=boundary_shape,
            title_identity=normalized_title_identity,
        )
        normalized_body_split_needed = bool(title_depth_body_split_needed) or bool(
            fallback.get("title_depth_body_split_needed", False)
        )
        normalized_body_split_reason = (
            collapse_ws(str(title_depth_body_split_reason).strip())
            or str(fallback.get("title_depth_body_split_reason", "")).strip()
        )
        normalized_title_depth_reuse_bias = (
            collapse_ws(str(title_depth_reuse_bias).strip())
            or str(fallback.get("title_depth_reuse_bias", "")).strip()
        )
        encountered_not = titleize_semantic_unit(str(encountered_not).strip())
        if not encountered_not:
            encountered_not = titleize_semantic_unit(" ".join(learning_core_tokens(semantic_text)))
        if not encountered_not:
            encountered_not = titleize_semantic_unit(semantic_text) or "Active Non Achievedness"

        lookup_keys = ordered_unique(learning_lookup_keys(semantic_text))
        normalized_components: list[str] = []
        if component_nots is None:
            normalized_components.extend(learning_component_units(semantic_text))
            learned_hints = self.learned_component_hints(semantic_text)
            normalized_components.extend(learned_hints)
            if learned_hints:
                used_tokens: set[str] = set()
                for hint in learned_hints:
                    used_tokens.update(learning_core_tokens(hint))
                leftover_tokens = [token for token in learning_core_tokens(semantic_text) if token not in used_tokens]
                leftover_component = titleize_semantic_unit(" ".join(leftover_tokens))
                if leftover_component:
                    normalized_components.append(leftover_component)
        else:
            for item in component_nots:
                if normalized_body_split_needed:
                    normalized_component = (
                        display_title_leaf_text(normalize_semantic_title_identity(str(item).strip()))
                        or titleize_semantic_unit(str(item).strip())
                        or collapse_ws(str(item).strip())
                    )
                else:
                    normalized_component = normalize_semantic_component_title(str(item))
                if normalized_component and normalized_component != encountered_not:
                    normalized_components.append(normalized_component)
        normalized_components = ordered_unique(normalized_components)[:6]
        normalized_composed_not = normalize_semantic_component_title(str(composed_not).strip())
        if not normalized_composed_not and len(normalized_components) > 1:
            normalized_composed_not = encountered_not
        normalized_intended_object = collapse_ws(str(intended_object).strip()) or str(fallback.get("intended_object", "")).strip()
        component_focus_text = collapse_ws(str(fallback.get("prompt_directive_focus", "")).strip()) or normalized_intended_object
        if component_focus_text and not normalized_body_split_needed:
            normalized_focus_component = normalize_semantic_component_title(component_focus_text) or titleize_semantic_unit(component_focus_text)
            if normalized_focus_component:
                normalized_focus_key = semantic_namespace_key(normalized_focus_component)
                directive_kind = collapse_ws(str(fallback.get("prompt_directive_kind", "")).strip()).lower()
                compared_components = ordered_unique(
                    normalize_semantic_component_title(str(item).strip()) or titleize_semantic_unit(str(item).strip())
                    for item in fallback.get("prompt_directive_compared_terms", [])
                    if str(item).strip()
                )
                contrast_focus_component = normalize_semantic_component_title(" And ".join(compared_components)) if compared_components else ""
                requires_formula = bool(fallback.get("prompt_directive_requires_formula", False))
                contextualized_components: list[str] = []
                for component in normalized_components:
                    normalized_component = normalize_semantic_component_title(component)
                    if not normalized_component:
                        continue
                    component_lower = collapse_ws(normalized_component).lower()
                    component_key = semantic_namespace_key(normalized_component)
                    if normalized_focus_key and normalized_focus_key in component_key:
                        contextualized_components.append(normalized_component)
                        continue
                    enriched_component = normalized_component
                    if (
                        directive_kind == "state"
                        and requires_formula
                        and any(marker in component_lower for marker in ("input", "output", "variable", "role", "represent"))
                    ):
                        enriched_component = (
                            normalize_semantic_component_title(f"{normalized_focus_component} {normalized_component}")
                            or normalized_component
                        )
                    elif re.search(r"\bgive\b.*\bexample\b", component_lower):
                        enriched_component = (
                            normalize_semantic_component_title(f"{normalized_component} Using {normalized_focus_component}")
                            or normalized_component
                        )
                    elif re.search(r"\bidentify\b", component_lower) and any(
                        marker in collapse_ws(semantic_text).lower()
                        for marker in ("state-plus-change", "state plus change")
                    ):
                        enriched_component = (
                            normalize_semantic_component_title(f"{normalized_component} For {normalized_focus_component}")
                            or normalized_component
                        )
                    elif (
                        directive_kind == "distinguish"
                        and contrast_focus_component
                        and any(marker in component_lower for marker in ("represent", "relation", "substrate"))
                    ):
                        enriched_component = (
                            normalize_semantic_component_title(f"{normalized_component} For {contrast_focus_component}")
                            or normalized_component
                        )
                    contextualized_components.append(enriched_component)
                normalized_components = ordered_unique(contextualized_components)[:6]
        normalized_success_criteria = structured_text_list(success_criteria or fallback.get("success_criteria", []))
        normalized_actual_realization = collapse_ws(str(actual_realization).strip()) or str(fallback.get("actual_realization", "")).strip()
        normalized_givens = structured_text_list(givens or fallback.get("givens", []))
        normalized_unknowns = structured_text_list(unknowns or fallback.get("unknowns", []))
        normalized_missing_components = structured_text_list(missing_components or fallback.get("missing_components", []))
        normalized_distorted_components = structured_text_list(distorted_components or fallback.get("distorted_components", []))
        normalized_differentiators = structured_text_list(differentiators or fallback.get("differentiators", []))
        normalized_contrastive_cases = structured_text_list(contrastive_cases or fallback.get("contrastive_cases", []))
        normalized_risk = structured_text_list(risk_of_wrong_closure or fallback.get("risk_of_wrong_closure", []))
        normalized_disallowed_assumptions = structured_text_list(disallowed_assumptions or fallback.get("disallowed_assumptions", []))
        normalized_misalignment_types = normalize_not_misalignment_list(misalignment_types or fallback.get("misalignment_types", []))
        normalized_origin_layers = normalize_not_origin_list(origin_layers or fallback.get("origin_layers", []))
        normalized_degree = normalize_not_degree(degree or fallback.get("degree"), default=fallback.get("degree", NotDegreeKind.PARTIAL.value))
        normalized_remainder_shapes = normalize_remainder_shape_list(remainder_shapes or fallback.get("remainder_shapes", []))
        normalized_why_it_matters = structured_text_list(why_it_matters or fallback.get("why_it_matters", []))
        normalized_minimal_repair = structured_text_list(minimal_repair or fallback.get("minimal_repair", []))
        normalized_full_repair = structured_text_list(full_repair or fallback.get("full_repair", []))
        normalized_action_posture = collapse_ws(str(action_posture).strip()) or str(fallback.get("action_posture", "")).strip()
        title_depth_view = derive_semantic_title_depth_view(
            normalized_title_identity,
            minimal_sufficient_depth=fallback.get("title_depth_minimal_sufficient_depth"),
            assessment=fallback.get("title_depth_assessment", ""),
        )
        normalized_title_similar_identities = ordered_unique(
            normalize_semantic_title_identity(str(item).strip()) or collapse_ws(str(item).strip())
            for item in (title_similar_identities or fallback.get("title_similar_identities", []))
            if str(item).strip()
        )[:8]
        lookup_keys = ordered_unique(
            learning_lookup_keys(normalized_title_identity)
            + [key for item in title_depth_view["segments"] for key in learning_lookup_keys(item)]
            + [key for item in title_depth_view["prefixes"] for key in learning_lookup_keys(item)]
            + learning_lookup_keys(semantic_text)
            + [key for item in normalized_components for key in learning_lookup_keys(item)]
            + ([key for key in learning_lookup_keys(normalized_composed_not)] if normalized_composed_not else [])
            + [key for item in normalized_givens for key in learning_lookup_keys(item)]
            + [key for item in normalized_unknowns for key in learning_lookup_keys(item)]
            + [key for item in normalized_differentiators for key in learning_lookup_keys(item)]
            + [key for item in normalized_contrastive_cases for key in learning_lookup_keys(item)]
            + [key for item in normalized_title_similar_identities for key in learning_lookup_keys(item)]
            + lookup_keys
        )[:24]
        notation_yaml = render_structured_learning_yaml(
            semantic_unit=semantic_text,
            encountered_not=encountered_not,
            component_nots=normalized_components,
            composed_not=normalized_composed_not,
            related_artifact_titles=related_artifact_titles or [],
            title_identity=normalized_title_identity,
            title_depth_segments=list(title_depth_view["segments"]),
            title_depth_prefixes=list(title_depth_view["prefixes"]),
            title_depth_exposed_depth=int(title_depth_view["exposed_depth"]),
            title_depth_minimal_sufficient_depth=int(title_depth_view["minimal_sufficient_depth"]),
            title_depth_assessment=str(title_depth_view["assessment"]),
            title_depth_hidden_depth_note=str(fallback.get("title_depth_hidden_depth_note", "")).strip(),
            title_depth_body_split_needed=normalized_body_split_needed,
            title_depth_body_split_reason=normalized_body_split_reason,
            title_depth_reuse_bias=normalized_title_depth_reuse_bias,
            title_similar_identities=normalized_title_similar_identities,
            intended_object=normalized_intended_object,
            success_criteria=normalized_success_criteria,
            actual_realization=normalized_actual_realization,
            givens=normalized_givens,
            unknowns=normalized_unknowns,
            missing_components=normalized_missing_components,
            distorted_components=normalized_distorted_components,
            differentiators=normalized_differentiators,
            contrastive_cases=normalized_contrastive_cases,
            risk_of_wrong_closure=normalized_risk,
            disallowed_assumptions=normalized_disallowed_assumptions,
            misalignment_types=normalized_misalignment_types,
            origin_layers=normalized_origin_layers,
            degree=normalized_degree,
            remainder_shapes=normalized_remainder_shapes,
            why_it_matters=normalized_why_it_matters,
            minimal_repair=normalized_minimal_repair,
            full_repair=normalized_full_repair,
            action_posture=normalized_action_posture,
        )
        return {
            "title_identity": normalized_title_identity,
            "encountered_not": encountered_not,
            "goal": semantic_text,
            "intended_object": normalized_intended_object,
            "success_criteria": normalized_success_criteria,
            "actual_realization": normalized_actual_realization,
            "givens": normalized_givens,
            "unknowns": normalized_unknowns,
            "missing_components": normalized_missing_components,
            "distorted_components": normalized_distorted_components,
            "differentiators": normalized_differentiators,
            "contrastive_cases": normalized_contrastive_cases,
            "risk_of_wrong_closure": normalized_risk,
            "disallowed_assumptions": normalized_disallowed_assumptions,
            "misalignment_types": normalized_misalignment_types,
            "origin_layers": normalized_origin_layers,
            "degree": normalized_degree,
            "remainder_shapes": normalized_remainder_shapes,
            "why_it_matters": normalized_why_it_matters,
            "minimal_repair": normalized_minimal_repair,
            "full_repair": normalized_full_repair,
            "boundary_shape": list(boundary_shape_values(boundary_shape, default=default_boundary_shape_for_node(semantic_unit=semantic_text))),
            "action_posture": normalized_action_posture,
            "title_depth_segments": list(title_depth_view["segments"]),
            "title_depth_prefixes": list(title_depth_view["prefixes"]),
            "title_depth_exposed_depth": int(title_depth_view["exposed_depth"]),
            "title_depth_minimal_sufficient_depth": int(title_depth_view["minimal_sufficient_depth"]),
            "title_depth_assessment": str(title_depth_view["assessment"]),
            "title_depth_hidden_depth_note": str(fallback.get("title_depth_hidden_depth_note", "")).strip(),
            "title_depth_body_split_needed": normalized_body_split_needed,
            "title_depth_body_split_reason": normalized_body_split_reason,
            "title_depth_reuse_bias": normalized_title_depth_reuse_bias,
            "title_similar_identities": normalized_title_similar_identities,
            "lookup_keys": lookup_keys,
            "component_nots": normalized_components,
            "composed_not": normalized_composed_not,
            "notation_yaml": notation_yaml,
        }

    def artifact_structured_learning_view(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building a view of artifact structured learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `artifact_structured_learning_view(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_structured_learning_view`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `artifact_structured_learning_view`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = artifact_structured_learning_from_content(artifact)
        structured_title_identity = structured_title_identity_text(structured)
        artifact_title_identity = normalize_semantic_title_identity(str(artifact.title or "").strip())
        structured_segments = derive_semantic_title_depth_segments(structured_title_identity)
        artifact_segments = derive_semantic_title_depth_segments(artifact_title_identity)
        if artifact_title_identity and len(artifact_segments) > len(structured_segments):
            structured_suffix_matches_artifact = (
                not structured_segments
                or len(structured_segments) <= 1
                or [
                    semantic_namespace_key(segment)
                    for segment in artifact_segments[-len(structured_segments):]
                ]
                == [semantic_namespace_key(segment) for segment in structured_segments]
            )
            if structured_suffix_matches_artifact:
                artifact_title_view = derive_semantic_title_depth_view(artifact_title_identity)
                structured = {
                    **structured,
                    "title_identity": artifact_title_identity,
                    "title_depth_segments": list(artifact_title_view["segments"]),
                    "title_depth_prefixes": list(artifact_title_view["prefixes"]),
                    "title_depth_exposed_depth": int(artifact_title_view["exposed_depth"]),
                }
        alias_keys: list[str] = []
        aliases = content.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                alias_keys.extend(learning_lookup_keys(str(alias)))
        input_contract = content.get("input_contract", {})
        if isinstance(input_contract, Mapping):
            for key in input_contract.keys():
                alias_keys.extend(learning_lookup_keys(str(key)))
        output_contract = content.get("output_contract", {})
        if isinstance(output_contract, Mapping):
            for key in output_contract.keys():
                alias_keys.extend(learning_lookup_keys(str(key)))
        formal_title_identity = self.artifact_formal_title_identity(artifact)
        if looks_like_prolog_title_identity(formal_title_identity):
            alias_map = prolog_contract_alias_map(
                formal_title_identity,
                input_keys=[str(key).strip() for key in input_contract.keys()] if isinstance(input_contract, Mapping) else [],
                output_keys=[str(key).strip() for key in output_contract.keys()] if isinstance(output_contract, Mapping) else [],
            )
            for aliases in alias_map.values():
                for alias in aliases:
                    alias_keys.extend(learning_lookup_keys(alias))
        return {
            **structured,
            "lookup_keys": ordered_unique(
                list(structured.get("lookup_keys", []))
                + learning_lookup_keys(artifact.title)
                + learning_lookup_keys(str(content.get("question", "")).strip())
                + alias_keys
            ),
            "boundary_shape": [term.value for term in artifact.boundary_shape],
        }

    def classify_structured_learning_match(
        self,
        current: Mapping[str, Any],
        prior: Mapping[str, Any],
    ) -> str | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling classify structured learning match.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `classify_structured_learning_match(current={'title': 'Physics / Force / Force From Mass And Acceleration'}, prior={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            current: Value for `current` used by `classify_structured_learning_match`. Expected type: `Mapping[str, Any]`.
            prior: Value for `prior` used by `classify_structured_learning_match`. Expected type: `Mapping[str, Any]`.

        Returns:
            str | None: Result produced by `classify_structured_learning_match`.
        """
        current_not = str(current.get("encountered_not", "")).strip()
        prior_not = str(prior.get("encountered_not", "")).strip()
        current_title_identity = structured_title_identity_text(current)
        prior_title_identity = structured_title_identity_text(prior)
        current_title_segments = derive_semantic_title_depth_segments(current_title_identity)
        prior_title_segments = derive_semantic_title_depth_segments(prior_title_identity)
        title_relation, _ = classify_title_depth_relation(
            current_title_identity,
            prior_title_identity,
        )
        prolog_match_score = prolog_title_match_score(current_title_identity, prior_title_identity)
        current_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(current)]
        prior_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(prior)]
        current_keys = set(current_key_list)
        prior_keys = set(prior_key_list)
        current_components = [str(item).strip() for item in current.get("component_nots", []) if str(item).strip()]
        prior_components = [str(item).strip() for item in prior.get("component_nots", []) if str(item).strip()]
        current_primary_key = current_key_list[0] if current_key_list else ""
        prior_primary_key = prior_key_list[0] if prior_key_list else ""
        current_discriminators = learning_discriminator_tokens(
            current_not,
            current_primary_key,
            *current_key_list,
            *current_components,
        )
        prior_discriminators = learning_discriminator_tokens(
            prior_not,
            prior_primary_key,
            *prior_key_list,
            *prior_components,
        )

        if current_discriminators and prior_discriminators and current_discriminators.isdisjoint(prior_discriminators):
            return None

        if prolog_match_score >= 95:
            return "encountered_before"
        if prolog_match_score >= 90:
            return "decomposition_related"
        if title_relation == "same_identity":
            return "encountered_before"
        if (
            str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(prior_title_segments) >= 2
            and len(current_title_segments) > len(prior_title_segments)
            and [
                semantic_namespace_key(segment)
                for segment in current_title_segments[-len(prior_title_segments):]
            ]
            == [semantic_namespace_key(segment) for segment in prior_title_segments]
        ):
            return "encountered_before"
        if (
            str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(current_title_segments) >= 2
            and len(prior_title_segments) >= 2
            and semantic_namespace_key(current_title_segments[-1]) == semantic_namespace_key(prior_title_segments[-1])
            and (
                bool(current.get("title_depth_body_split_needed", False))
                or bool(prior.get("title_depth_body_split_needed", False))
            )
        ):
            return "encountered_before"
        if current_not and prior_not and current_not.lower() == prior_not.lower():
            return "encountered_before"
        if current_primary_key and prior_primary_key and current_primary_key == prior_primary_key:
            return "encountered_before"

        current_surface_tokens = set(learning_core_tokens(str(current.get("goal", "")).strip() or current_not))
        prior_surface_tokens = set(learning_core_tokens(str(prior.get("goal", "")).strip() or prior_not))
        current_extra_surface_tokens = current_surface_tokens - prior_surface_tokens if current_surface_tokens and prior_surface_tokens else set()
        shared_lookup_keys = [
            key
            for key in current_key_list
            if any(learning_overlap(key, prior_key) for prior_key in prior_key_list)
        ]
        if len(shared_lookup_keys) >= 3 and not current_extra_surface_tokens:
            return "encountered_before"

        matched_components: set[str] = set()
        prior_terms = [prior_not, *prior_components, *sorted(prior_keys)]
        for component in current_components:
            if any(learning_overlap(component, term) for term in prior_terms if term):
                matched_components.add(component)
        if len(matched_components) >= 2:
            return "composition_related"
        if matched_components:
            return "decomposition_related"
        if title_relation in {"prior_is_ground_prefix", "shared_ground_prefix"}:
            return "decomposition_related"
        if shared_lookup_keys:
            return "decomposition_related"

        return None

    def answer_match_preference(
        self,
        current: Mapping[str, Any],
        prior: Mapping[str, Any],
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with answering match preference.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `answer_match_preference(current={'title': 'Physics / Force / Force From Mass And Acceleration'}, prior={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            current: Value for `current` used by `answer_match_preference`. Expected type: `Mapping[str, Any]`.
            prior: Value for `prior` used by `answer_match_preference`. Expected type: `Mapping[str, Any]`.

        Returns:
            str: Result produced by `answer_match_preference`.
        """
        current_not = str(current.get("encountered_not", "")).strip().lower()
        prior_not = str(prior.get("encountered_not", "")).strip().lower()
        current_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(current)]
        prior_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(prior)]
        current_title_identity = structured_title_identity_text(current)
        prior_title_identity = structured_title_identity_text(prior)
        current_title_segments = derive_semantic_title_depth_segments(current_title_identity)
        prior_title_segments = derive_semantic_title_depth_segments(prior_title_identity)
        if current_not and prior_not and current_not == prior_not:
            return "same_not"
        if (
            str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(current_title_segments) >= 2
            and len(prior_title_segments) >= 2
            and semantic_namespace_key(current_title_segments[-1]) == semantic_namespace_key(prior_title_segments[-1])
            and (
                bool(current.get("title_depth_body_split_needed", False))
                or bool(prior.get("title_depth_body_split_needed", False))
            )
        ):
            return "same_key"
        if current_key_list and prior_key_list and current_key_list[0] == prior_key_list[0]:
            return "same_key"
        return "related_key"

    def artifact_formal_title_identity(self, artifact: Artifact) -> str:
        """
        High Level Purpose:
            In circumstances like candidate-specific structural retrieval and title-backed reuse, helps with recovering the authoritative formal title identity stored on an artifact.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_formal_title_identity(artifact=Artifact(id='artifact-force', title=\"Newton's Laws of Motion / Force-Mass-Acceleration Relationship\", artifact_type='ability', representation='python'))`
            Output: 'newtons_laws_of_motion:force_mass_acceleration_relationship(Mass, Acceleration, Force) :- Force is Mass * Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_formal_title_identity`. Expected type: `Artifact`.

        Returns:
            str: Result produced by `artifact_formal_title_identity`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = artifact_structured_learning_from_content(artifact)
        candidates = [
            str(content.get("formal_title_identity", "")).strip(),
            str(structured.get("title_identity", "")).strip(),
            str(artifact.title or "").strip(),
        ]
        for candidate in candidates:
            normalized = normalize_semantic_title_identity(candidate)
            if normalized:
                return normalized
        return ""

    def llm_prime_prolog_query_title_identity(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
        explicit_payload: Any = None,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like using an available LLM to bridge a normal-language prompt into a stored Prolog identity, helps with asking for a candidate query head anchored to one specific artifact.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `llm_prime_prolog_query_title_identity(artifact=Artifact(id='artifact-force', title=\"Newton's Laws of Motion / Force-Mass-Acceleration Relationship\", artifact_type='ability', representation='python'), semantic_unit='Calculate force for mass=3 and acceleration=4.')`
            Output: 'newtons_laws_of_motion:force_mass_acceleration_relationship(3, 4, Force)'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `llm_prime_prolog_query_title_identity`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `llm_prime_prolog_query_title_identity`. Expected type: `str`. Defaults to `''`.
            explicit_payload: Value for `explicit_payload` used by `llm_prime_prolog_query_title_identity`. Expected type: `Any`. Defaults to `None`.

        Returns:
            str: Result produced by `llm_prime_prolog_query_title_identity`.
        """
        if not self.llm.enabled or prolog_query_priming_mode() == PROLOG_QUERY_PRIMING_MODE_OFF:
            return ""
        prompt_text = collapse_ws(str(semantic_unit or "").strip())
        formal_title_identity = self.artifact_formal_title_identity(artifact)
        if not prompt_text or not looks_like_prolog_title_identity(formal_title_identity):
            return ""
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        input_contract = content.get("input_contract", {})
        output_contract = content.get("output_contract", {})
        deterministic_payload = self.derive_artifact_invocation_payload(
            artifact,
            semantic_unit=prompt_text,
            explicit_payload=explicit_payload,
        )
        try:
            result = self.llm.propose_json(
                proposal_type=ProposalType.RETRIEVAL_PLAN,
                mode=SupplementMode.FAST,
                prompt=plain_prompt(
                    f"""
                    The user prompt is ordinary text, not Prolog.
                    You are given one stored artifact with a formal Prolog title identity.

                    Return JSON with:
                    - query_title_identity: either one Prolog head only (no body) or an empty string
                    - rationale: one short sentence

                    Rules:
                    - Use only the provided artifact predicate family and namespace.
                    - If the prompt clearly targets this artifact, fill concrete literal inputs from the prompt where explicit.
                    - Leave unresolved positions as the variable names already present in the stored head.
                    - Do not invent a new predicate, namespace, or body.
                    - If the prompt does not fit this artifact, return an empty query_title_identity.

                    User prompt:
                    {prompt_text}

                    Artifact display title:
                    {artifact.title}

                    Artifact formal title identity:
                    {formal_title_identity}

                    Artifact question:
                    {str(content.get('question', '')).strip()}

                    Artifact input contract:
                    {json.dumps(json_safe(input_contract), sort_keys=True)}

                    Artifact output contract:
                    {json.dumps(json_safe(output_contract), sort_keys=True)}

                    Deterministic payload already recovered from the prompt:
                    {json.dumps(json_safe(deterministic_payload), sort_keys=True)}
                    """
                ),
                schema_hint={
                    "query_title_identity": "",
                    "rationale": "",
                },
            )
        except Exception:
            return ""

        payload = result.payload if isinstance(result.payload, Mapping) else {}
        candidate_query = normalize_semantic_title_identity(str(payload.get("query_title_identity", "")).strip())
        if not candidate_query or not looks_like_prolog_title_identity(candidate_query):
            return ""
        if prolog_title_match_score(candidate_query, formal_title_identity) < 95:
            return ""
        self.state.record_step(
            kind="prolog_query_priming",
            node_id=self.state.root_id,
            intent="Bridge a normal-language prompt into a stored structural identity when Prolog-backed retrieval is enabled and deterministic synthesis is insufficient.",
            action="prime candidate-specific Prolog query head",
            result="primed structural query recovered",
            evaluation="the controller preserved artifact authority by asking only for an instantiated head over an existing predicate family",
            payload={
                "artifact_id": artifact.id,
                "artifact_title": artifact.title,
                "semantic_unit": prompt_text,
                "query_title_identity": candidate_query,
                "provider": result.provider,
                "model": result.model,
            },
        )
        return candidate_query

    def artifact_query_semantic_unit(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
        explicit_payload: Any = None,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like making a normal-language prompt benefit from a stored Prolog identity, helps with deriving the best artifact-specific semantic query text for matching, instantiation, and ranking.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_query_semantic_unit(artifact=Artifact(id='artifact-force', title=\"Newton's Laws of Motion / Force-Mass-Acceleration Relationship\", artifact_type='ability', representation='python'), semantic_unit='Calculate force for mass=3 and acceleration=4.')`
            Output: 'newtons_laws_of_motion:force_mass_acceleration_relationship(3, 4, Force)'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_query_semantic_unit`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_query_semantic_unit`. Expected type: `str`. Defaults to `''`.
            explicit_payload: Value for `explicit_payload` used by `artifact_query_semantic_unit`. Expected type: `Any`. Defaults to `None`.

        Returns:
            str: Result produced by `artifact_query_semantic_unit`.
        """
        base_query = normalize_semantic_title_identity(str(semantic_unit or "").strip())
        formal_title_identity = self.artifact_formal_title_identity(artifact)
        if not looks_like_prolog_title_identity(formal_title_identity):
            return base_query
        if looks_like_prolog_title_identity(base_query) and prolog_title_match_score(base_query, formal_title_identity) >= 95:
            return base_query

        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        input_contract = content.get("input_contract", {})
        output_contract = content.get("output_contract", {})
        input_keys = list(input_contract.keys()) if isinstance(input_contract, Mapping) else []
        output_keys = list(output_contract.keys()) if isinstance(output_contract, Mapping) else []
        priming_mode = prolog_query_priming_mode()

        if priming_mode == PROLOG_QUERY_PRIMING_MODE_FORCE:
            llm_query = self.llm_prime_prolog_query_title_identity(
                artifact,
                semantic_unit=base_query,
                explicit_payload=explicit_payload,
            )
            if llm_query:
                return llm_query

        invocation_payload = self.derive_artifact_invocation_payload(
            artifact,
            semantic_unit=base_query,
            explicit_payload=explicit_payload,
        )
        deterministic_query = synthesize_prolog_query_title_identity(
            formal_title_identity,
            invocation_payload=invocation_payload if isinstance(invocation_payload, Mapping) else None,
            input_keys=input_keys,
            output_keys=output_keys,
        )
        if deterministic_query:
            return deterministic_query

        if priming_mode in {PROLOG_QUERY_PRIMING_MODE_FALLBACK, PROLOG_QUERY_PRIMING_MODE_FORCE}:
            llm_query = self.llm_prime_prolog_query_title_identity(
                artifact,
                semantic_unit=base_query,
                explicit_payload=explicit_payload,
            )
            if llm_query:
                return llm_query
        return base_query

    def artifact_prolog_clause_answer(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
    ) -> str:
        """
        High Level Purpose:
            In circumstances like symbolic head-pattern retrieval where a stored clause title should answer a new clause head query, helps with instantiating the stored body under the query unifier.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_prolog_clause_answer(artifact=Artifact(id='artifact-add', title='math:add:add(A, B, C) :- C is A + B', artifact_type='knowledge', representation='yaml'), semantic_unit='math:add:add(2, X, Y)')`
            Output: 'Y is 2 + X'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_prolog_clause_answer`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_prolog_clause_answer`. Expected type: `str`. Defaults to `''`.

        Returns:
            str: Result produced by `artifact_prolog_clause_answer`.
        """
        normalized_query = normalize_semantic_title_identity(str(semantic_unit or "").strip())
        if not looks_like_prolog_title_identity(normalized_query):
            return ""

        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = content.get("structured_learning", {}) if isinstance(content.get("structured_learning", {}), Mapping) else {}
        candidate_title = (
            str(structured.get("title_identity", "")).strip()
            or str(artifact.title or "").strip()
        )
        candidate_title = normalize_semantic_title_identity(candidate_title)
        if not looks_like_prolog_title_identity(candidate_title):
            return ""
        if prolog_title_match_score(normalized_query, candidate_title) <= 0:
            return ""

        query_view = prolog_title_view(normalized_query)
        candidate_view = prolog_title_view(candidate_title)
        source_term = parse_prolog_term(str(candidate_view.get("leaf_head_text", "")).strip(), variable_prefix="s:")
        query_term = parse_prolog_term(str(query_view.get("leaf_head_text", "")).strip(), variable_prefix="q:")

        candidate_body = (
            str(structured.get("title_prolog_body", "")).strip()
            or str(candidate_view.get("body_text", "")).strip()
        )
        if candidate_body:
            instantiated_body = instantiate_prolog_body_text(
                candidate_body,
                source_term=source_term,
                query_term=query_term,
            )
            if instantiated_body:
                return instantiated_body

        stored_answer = str(content.get("answer", "")).strip()
        if stored_answer:
            instantiated_answer = instantiate_prolog_body_text(
                stored_answer,
                source_term=source_term,
                query_term=query_term,
            )
            return instantiated_answer or stored_answer
        return ""

    def artifact_latent_knowledge_answer_text(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str = "",
    ) -> str:
        """
        High Level Purpose:
            In circumstances like direct explanatory prompts where a learned knowledge artifact has no explicit answer field but does carry semantic givens, relation hints, or typed input-output traces, helps with recovering a bounded readable answer surface from that stored structure.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_latent_knowledge_answer_text(artifact=Artifact(id='artifact-photo-energy', title='Biology / Biological Energy Can Also Be Stored', artifact_type='knowledge', representation='yaml'), semantic_unit='What is photosynthesis?')`
            Output: 'Light Energy becomes Stored Chemical Energy.'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_latent_knowledge_answer_text`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_latent_knowledge_answer_text`. Expected type: `str`. Defaults to `''`.

        Returns:
            str: Result produced by `artifact_latent_knowledge_answer_text`.
        """
        if not semantic_prompt_prefers_direct_knowledge_answer(semantic_unit):
            return ""
        content = self.artifact_runtime_content(artifact)
        structured = content.get("structured_learning", {})
        if not isinstance(structured, Mapping):
            structured = {}

        arrow_sources: list[str] = []
        relation_hints = content.get("relation_hint_texts", [])
        if isinstance(relation_hints, list):
            arrow_sources.extend(str(item).strip() for item in relation_hints if str(item).strip())
        givens = structured.get("givens", [])
        if isinstance(givens, list):
            arrow_sources.extend(str(item).strip() for item in givens if str(item).strip())
        for source_text in arrow_sources:
            sentence = arrow_relation_sentence(source_text)
            if sentence:
                return sentence

        input_titles = content.get("input_titles", {})
        output_titles = content.get("output_titles", {})
        if isinstance(input_titles, Mapping) and isinstance(output_titles, Mapping) and output_titles:
            input_phrases = [
                semantic_phrase_surface(key)
                for key in input_titles.keys()
                if semantic_phrase_surface(key)
            ]
            output_phrases: list[str] = []
            for key, value in output_titles.items():
                phrase = semantic_phrase_surface(value) or semantic_phrase_surface(key)
                if phrase:
                    output_phrases.append(phrase)
            if len(input_phrases) == 1 and len(output_phrases) == 1:
                return f"{input_phrases[0]} becomes {output_phrases[0]}."
            if len(output_phrases) == 1:
                title_identity = semantic_phrase_surface(content.get("title_current_identity", ""))
                if title_identity:
                    return f"{title_identity}. {output_phrases[0]}."

        return ""

    artifact_answer_text = resolve_artifact_answer_text

    def answer_reuse_preference(
        self,
        current: Mapping[str, Any],
        prior: Mapping[str, Any],
        artifact: Artifact,
    ) -> str | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with answering reuse preference.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `answer_reuse_preference(current={'title': 'Physics / Force / Force From Mass And Acceleration'}, prior={'title': 'Physics / Force / Force From Mass And Acceleration'}, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            current: Value for `current` used by `answer_reuse_preference`. Expected type: `Mapping[str, Any]`.
            prior: Value for `prior` used by `answer_reuse_preference`. Expected type: `Mapping[str, Any]`.
            artifact: Value for `artifact` used by `answer_reuse_preference`. Expected type: `Artifact`.

        Returns:
            str | None: Result produced by `answer_reuse_preference`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        current_semantic_text = (
            structured_title_identity_text(current)
            or str(current.get("goal", "")).strip()
            or str(current.get("encountered_not", "")).strip()
            or str(current.get("composed_not", "")).strip()
        )
        current_query_text = self.artifact_query_semantic_unit(
            artifact,
            semantic_unit=current_semantic_text,
        ) or current_semantic_text
        prior_query_text = structured_title_identity_text(prior)
        has_stored_answer = self.artifact_has_answer_capability(
            artifact,
            semantic_unit=current_query_text,
        )
        executable_artifact = self.artifact_is_executable_function(artifact)
        if not has_stored_answer and not executable_artifact:
            return None

        current_boundary_shape = normalize_boundary_shape(current.get("boundary_shape"), default=())
        artifact_boundary = normalize_boundary_shape(artifact.boundary_shape, default=())
        current_posture = collapse_ws(str(current.get("action_posture", "")).strip())
        prior_posture = collapse_ws(str(prior.get("action_posture", "")).strip())
        current_title_identity = structured_title_identity_text(current)
        prior_title_identity = structured_title_identity_text(prior)
        current_title_segments = derive_semantic_title_depth_segments(current_title_identity)
        prior_title_segments = derive_semantic_title_depth_segments(prior_title_identity)
        title_relation, _ = classify_title_depth_relation(
            current_title_identity,
            prior_title_identity,
        )
        prolog_match_score = prolog_title_match_score(current_query_text, prior_query_text)
        current_write_terms = set(boundary_shape_values(current_boundary_shape, default=())).intersection(
            {term.value for term in BOUNDARY_WRITE_TERMS}
        )
        artifact_write_terms = set(boundary_shape_values(artifact_boundary, default=())).intersection(
            {term.value for term in BOUNDARY_WRITE_TERMS}
        )
        if artifact_write_terms and not current_write_terms:
            if not (executable_artifact and current_posture == "compute_or_template"):
                return None

        if current_posture and prior_posture and current_posture != prior_posture:
            if "compute_or_template" in {current_posture, prior_posture}:
                if not executable_artifact:
                    return None
        if (
            title_relation == "prior_is_ground_prefix"
            and str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(current_title_segments) > len(prior_title_segments)
            and not current.get("component_nots")
            and not executable_artifact
        ):
            return None
        if title_relation == "prior_is_overdetermined_extension":
            return None
        if prolog_match_score >= 95:
            return "same_key"
        if prolog_match_score >= 90:
            return "lookup_overlap"
        if (
            str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(prior_title_segments) >= 2
            and len(current_title_segments) > len(prior_title_segments)
            and [
                semantic_namespace_key(segment)
                for segment in current_title_segments[-len(prior_title_segments):]
            ]
            == [semantic_namespace_key(segment) for segment in prior_title_segments]
        ):
            return "same_key"
        if (
            str(current.get("title_depth_reuse_bias", "")).strip() == "determinate_reuse"
            and len(current_title_segments) >= 2
            and len(prior_title_segments) >= 2
            and semantic_namespace_key(current_title_segments[-1]) == semantic_namespace_key(prior_title_segments[-1])
            and (
                bool(current.get("title_depth_body_split_needed", False))
                or bool(prior.get("title_depth_body_split_needed", False))
            )
        ):
            return "same_key"

        current_not = str(current.get("encountered_not", "")).strip().lower()
        current_composed = str(current.get("composed_not", "")).strip().lower()
        current_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(current)]
        current_components = [str(item).strip() for item in current.get("component_nots", []) if str(item).strip()]

        prior_not = str(prior.get("encountered_not", "")).strip().lower()
        prior_composed = str(prior.get("composed_not", "")).strip().lower()
        prior_key_list = [item.lower() for item in structured_learning_signal_lookup_keys(prior)]
        prior_components = [str(item).strip() for item in prior.get("component_nots", []) if str(item).strip()]
        input_contract = content.get("input_contract", {})
        if executable_artifact and isinstance(input_contract, Mapping):
            prior_key_list.extend(
                str(key).strip().lower()
                for key in input_contract.keys()
                if str(key).strip()
            )
        prior_terms = [prior_not, prior_composed, *prior_components, *prior_key_list]
        current_discriminators = learning_discriminator_tokens(
            current_not,
            current_composed,
            *current_key_list,
            *current_components,
        )
        prior_discriminators = learning_discriminator_tokens(
            prior_not,
            prior_composed,
            *prior_key_list,
            *prior_components,
        )
        shared_lookup_keys = [
            key
            for key in current_key_list
            if any(learning_overlap(key, prior_key) for prior_key in prior_key_list)
        ]
        executable_compute_ready = False
        if executable_artifact and current_posture == "compute_or_template":
            semantic_text = (
                str(current.get("goal", "")).strip()
                or str(current.get("intended_object", "")).strip()
                or current_not
                or current_composed
            )
            invocation_payload = self.derive_artifact_invocation_payload(
                artifact,
                semantic_unit=semantic_text,
            )
            payload_ok, _, _ = self.artifact_invocation_payload_coverage(
                artifact,
                invocation_payload=invocation_payload,
            )
            operation_overlap = bool(shared_lookup_keys) or (
                current_not
                and prior_not
                and learning_overlap(current_not, prior_not)
            ) or (
                current_not
                and prior_composed
                and learning_overlap(current_not, prior_composed)
            ) or (
                current_composed
                and prior_composed
                and learning_overlap(current_composed, prior_composed)
            )
            executable_compute_ready = payload_ok and operation_overlap
            if executable_compute_ready:
                return "lookup_overlap"

        if current_discriminators and not executable_compute_ready:
            if not prior_discriminators:
                return None
            else:
                missing_discriminators = set(current_discriminators) - set(prior_discriminators)
                if missing_discriminators:
                    return None
            if prior_discriminators - current_discriminators:
                return None

        if current_not and prior_not and current_not == prior_not:
            return "same_not"
        if current_key_list and prior_key_list and current_key_list[0] == prior_key_list[0]:
            return "same_key"
        if current_composed and prior_composed and learning_overlap(current_composed, prior_composed):
            return "same_composed_family"
        if current_not and prior_composed and learning_overlap(current_not, prior_composed):
            return "same_composed_family"
        if current_components and all(
            any(learning_overlap(component, term) for term in prior_terms if term)
            for component in current_components
        ):
            return "covers_components"

        current_surface_tokens = set(learning_core_tokens(str(current.get("goal", "")).strip() or current_not))
        prior_surface_tokens = set(learning_core_tokens(str(prior.get("goal", "")).strip() or prior_not))
        current_extra_surface_tokens = current_surface_tokens - prior_surface_tokens if current_surface_tokens and prior_surface_tokens else set()
        if len(shared_lookup_keys) >= 2:
            if current_extra_surface_tokens:
                return None
            return "lookup_overlap"
        return None

    def supporting_capability_artifact_ids(self, artifact_ids: Iterable[str]) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling supporting capability artifact ids.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `supporting_capability_artifact_ids(artifact_ids=[{'title': 'Physics / Force / Force From Mass And Acceleration'}])`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_ids: Value for `artifact_ids` used by `supporting_capability_artifact_ids`. Expected type: `Iterable[str]`.

        Returns:
            list[str]: Result produced by `supporting_capability_artifact_ids`.
        """
        capability_ids: list[str] = []
        for artifact_id in artifact_ids:
            normalized_id = str(artifact_id).strip()
            if not normalized_id:
                continue
            artifact = self.state.artifacts.get(normalized_id) or self.state.learned_artifacts.get(normalized_id)
            if artifact is None:
                continue
            if artifact.artifact_type in {"ability", "capability"}:
                capability_ids.append(artifact.id)
        return ordered_unique(capability_ids)[:6]

    derive_related_solution_support = resolve_related_solution_support
    fallback_executable_answer_candidate = resolve_fallback_executable_answer_candidate
    best_invokable_artifact_candidate = resolve_best_invokable_artifact_candidate

    def artifact_scope_breadth_penalty(self, artifact: Artifact, *, semantic_unit: str) -> int:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with penalizing artifacts whose stored scope or answer breadth is broader than a specific prompt is asking for.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_scope_breadth_penalty(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), semantic_unit=\"What is Newton's first law of motion?\")`
            Output: 0

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_scope_breadth_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_scope_breadth_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_scope_breadth_penalty`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        prompt_text = collapse_ws(str(semantic_unit or "")).strip()
        prompt_lower = prompt_text.lower()
        penalty = 0

        source_sections = [
            str(item).strip()
            for item in content.get("source_sections", [])
            if str(item).strip()
        ] if isinstance(content.get("source_sections", []), list) else []
        prompt_requests_meta_view = bool(
            prompt_lower
            and (
                self.looks_like_generic_markdown_current_identity(prompt_text, encounter_heading=prompt_text)
                or any(marker in prompt_lower for marker in ("summary", "overview", "introduction", "key points", "takeaways"))
            )
        )
        if source_sections and not prompt_requests_meta_view:
            if all(self.looks_like_generic_markdown_current_identity(item, encounter_heading=item) for item in source_sections):
                penalty += 1

        prompt_ordinals = ordinal_focus_markers(prompt_text)
        if len(prompt_ordinals) == 1:
            candidate_ordinals = ordinal_focus_markers(artifact_selection_text(artifact))
            extra_ordinals = candidate_ordinals - prompt_ordinals
            if extra_ordinals:
                penalty += min(len(extra_ordinals), 3) + 1

        if str(artifact.title or "").strip().lower().startswith("structured learning record for"):
            if prompt_lower and "structured learning record" not in prompt_lower:
                penalty += 4

        return penalty

    def artifact_exact_output_symbol_penalty(self, artifact: Artifact, *, semantic_unit: str) -> int:
        """
        High Level Purpose:
            In circumstances like symbolic compute prompts where one-letter outputs such as `N`, `n`, `I`, or `P` must not be conflated, helps with penalizing artifacts whose primary output symbol conflicts with the exact requested symbol even when lowercased lexical overlap would otherwise match.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_exact_output_symbol_penalty(artifact=Artifact(id='artifact-moles', title='Chemistry / Moles From Particles', artifact_type='ability', representation='python_script'), semantic_unit='Calculate N from n=2 and N_A=3.')`
            Output: 7

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_exact_output_symbol_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_exact_output_symbol_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_exact_output_symbol_penalty`.
        """
        requested_phrases = semantic_requested_output_phrases(semantic_unit)
        if len(requested_phrases) != 1:
            return 0
        requested = collapse_ws(str(requested_phrases[0]).strip())
        if len(requested) != 1 or not requested.isalpha():
            return 0
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        artifact_output = collapse_ws(str(content.get("output_field", "")).strip())
        if len(artifact_output) != 1 or not artifact_output.isalpha():
            return 0
        if artifact_output == requested:
            return 0
        return 7

    def artifact_direct_definition_penalty(self, artifact: Artifact, *, semantic_unit: str) -> int:
        """
        High Level Purpose:
            In circumstances like bare `What is X?` prompts, helps with demoting section-local, example-local, or relation-local artifacts when they do not behave like a clean definition of the requested concept.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_direct_definition_penalty(artifact=Artifact(id='artifact-displacement-relation', title='Physics / Velocity-displacement relation', artifact_type='knowledge', representation='yaml'), semantic_unit='What is displacement?')`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_direct_definition_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_direct_definition_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_direct_definition_penalty`.
        """
        if not semantic_prompt_prefers_direct_knowledge_answer(semantic_unit):
            return 0
        focus_text = semantic_question_focus_text(semantic_unit)
        if not focus_text:
            return 0
        focus_lower = collapse_ws(focus_text).lower()
        selection_text = artifact_selection_text(artifact).lower()
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        answer_text = collapse_ws(str(content.get("answer", "")).strip()).lower()
        question_text = collapse_ws(str(content.get("question", "")).strip()).lower()
        leaf_text = display_title_leaf_text(str(getattr(artifact, "title", "")).strip()).lower()
        directive_kind = collapse_ws(
            str(semantic_prompt_directive_profile(semantic_unit).get("kind", "")).strip()
        )
        penalty = 0

        if directive_kind == "identify_reusable_substrate":
            substrate_markers = (
                "reusable substrate",
                "reuses",
                "broader substrate",
                "broader family",
                "inverse-square",
                "inverse square",
                "multiplicative combination",
                "special case",
            )
            if any(marker in answer_text for marker in substrate_markers):
                return 0

        if self.looks_like_generic_markdown_current_identity(leaf_text, encounter_heading=leaf_text):
            penalty += 2
        if any(marker in leaf_text for marker in ("example", "summary", "reusable knowledge", "connection", "integration", "previous lesson", "complement", "complementarity")):
            penalty += 2
        if question_text.startswith("how do you calculate"):
            penalty += 2
        if "relation" in leaf_text and "relation" not in focus_lower:
            penalty += 2
        from_focus_pattern = rf"\bfrom\s+{re.escape(focus_lower)}\b"
        if re.search(from_focus_pattern, leaf_text) or re.search(from_focus_pattern, question_text):
            penalty += 2
        bridge_pattern = rf"\bfrom\s+{re.escape(focus_lower)}\b[\w\W]{0,80}\bto\b"
        if re.search(bridge_pattern, leaf_text) or re.search(bridge_pattern, question_text):
            penalty += 2
        pair_focus_pattern = rf"(?:\b{re.escape(focus_lower)}\b[\w\W]{0,30}\band\b)|(?:\band\b[\w\W]{0,30}\b{re.escape(focus_lower)}\b)"
        if re.search(pair_focus_pattern, leaf_text):
            penalty += 1
        if focus_lower not in selection_text:
            penalty += 2
        if answer_text and focus_lower not in answer_text:
            penalty += 1
        return penalty

    def prompt_prefers_direct_knowledge_answer(self, text: str) -> bool:
        """
        High Level Purpose:
            In circumstances like direct explanatory prompts that need to be routed toward prior learned knowledge instead of compute execution, helps with exposing the prompt-preference decision as an explicit controller seam for knowledge-reuse helpers.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `prompt_prefers_direct_knowledge_answer(text='What is mass conservation in a reaction?')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `prompt_prefers_direct_knowledge_answer`. Expected type: `str`.

        Returns:
            bool: Result produced by `prompt_prefers_direct_knowledge_answer`.
        """
        return semantic_prompt_prefers_direct_knowledge_answer(text)

    persisted_direct_knowledge_candidates = persisted_direct_knowledge_reuse_candidates
    compose_direct_knowledge_answer = compose_direct_knowledge_reuse_answer

    def artifact_compute_prompt_penalty(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str,
        current_posture: str,
    ) -> int:
        """
        High Level Purpose:
            In circumstances like normal-language compute prompts that must select the right reusable ability, helps with penalizing artifacts whose output shape does not match the quantity being requested.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_compute_prompt_penalty(artifact=Artifact(id='artifact-pressure', title='Chemistry / Pressure From Amount Temperature And Volume', artifact_type='ability', representation='python_script'), semantic_unit='Calculate P from n=2 and R=0.5 and T=3 and V=1.', current_posture='compute_or_template')`
            Output: 0

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_compute_prompt_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_compute_prompt_penalty`. Expected type: `str`.
            current_posture: Value for `current_posture` used by `artifact_compute_prompt_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_compute_prompt_penalty`.
        """
        directive_kind = collapse_ws(str(semantic_prompt_directive_profile(semantic_unit).get("kind", "")).strip())
        if directive_kind in {"state", "distinguish", "derive", "construct", "identify_reusable_substrate"}:
            return 0
        if current_posture != "compute_or_template":
            return 0
        requested_output_keys = semantic_requested_output_keys(semantic_unit)
        artifact_output_keys = artifact_output_lookup_keys(artifact)
        executable = self.artifact_is_executable_function(artifact)
        has_answer_capability = self.artifact_has_answer_capability(
            artifact,
            semantic_unit=semantic_unit,
        )
        if requested_output_keys:
            if artifact_output_keys and any(
                output_lookup_compatible(requested_key, artifact_key)
                for requested_key in requested_output_keys
                for artifact_key in artifact_output_keys
            ):
                return 0
            if artifact_is_structured_learning_record(artifact):
                return 6
            if artifact_output_keys:
                return 4
            if executable or has_answer_capability:
                return 3
            return 5
        if artifact_is_structured_learning_record(artifact) and not executable:
            return 4
        return 0

    def artifact_direct_knowledge_prompt_penalty(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str,
        current_posture: str,
    ) -> int:
        """
        High Level Purpose:
            In circumstances like direct explanatory questions, helps with preferring reusable knowledge artifacts whose semantic focus matches the asked concept instead of generic structured-learning residue.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_direct_knowledge_prompt_penalty(artifact=Artifact(id='artifact-conservation', title='Chemistry / Mass Conservation Preserves Total Mass', artifact_type='knowledge', representation='yaml'), semantic_unit='What is mass conservation in a reaction?', current_posture='direct_resolution')`
            Output: 0

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_direct_knowledge_prompt_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_direct_knowledge_prompt_penalty`. Expected type: `str`.
            current_posture: Value for `current_posture` used by `artifact_direct_knowledge_prompt_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_direct_knowledge_prompt_penalty`.
        """
        if current_posture == "compute_or_template":
            return 0
        if not semantic_prompt_prefers_direct_knowledge_answer(semantic_unit):
            return 0
        focus_text = semantic_question_focus_text(semantic_unit)
        if not focus_text:
            return 0
        directive_kind = collapse_ws(
            str(semantic_prompt_directive_profile(semantic_unit).get("kind", "")).strip()
        )
        focus_alignment = artifact_focus_alignment_score(artifact, focus_text)
        if artifact_is_structured_learning_record(artifact):
            return 6 if focus_alignment >= 1 else 8
        content = self.artifact_runtime_content(artifact)
        explicit_answer_available = bool(str(content.get("answer", "")).strip()) if isinstance(content, Mapping) else False
        latent_answer_available = bool(
            self.artifact_latent_knowledge_answer_text(
                artifact,
                semantic_unit=semantic_unit,
            )
        )
        candidate_tokens = selection_signal_tokens(
            collapse_ws(
                " ".join(
                    part
                    for part in (
                        artifact_selection_text(artifact),
                        self.artifact_answer_text(artifact, semantic_unit=semantic_unit),
                    )
                    if collapse_ws(part)
                )
            )
        )
        combined_candidate_text = collapse_ws(
            " ".join(
                part
                for part in (
                    artifact_selection_text(artifact),
                    self.artifact_answer_text(artifact, semantic_unit=semantic_unit),
                )
                if collapse_ws(part)
            )
        ).lower()
        if directive_kind == "identify_reusable_substrate":
            substrate_markers = (
                "reusable substrate",
                "reuses",
                "broader substrate",
                "broader family",
                "inverse-square",
                "inverse square",
                "multiplicative combination",
                "special case",
            )
            has_substrate_markers = any(marker in combined_candidate_text for marker in substrate_markers)
            formula_only_law = (
                any(marker in combined_candidate_text for marker in ("$$", " = ", "formula is", "law is"))
            ) and not has_substrate_markers
            if has_substrate_markers:
                return 0 if explicit_answer_available or latent_answer_available else 2
            if formula_only_law:
                return 4
        distinctive_focus_tokens = {
            token
            for token in learning_core_tokens(focus_text)
            if token
            and token
            not in {
                "general",
                "formula",
                "equation",
                "relation",
                "law",
                "example",
                "using",
                "state",
                "identify",
                "quantity",
                "reusable",
                "represent",
                "represented",
                "representation",
                "change",
                "connect",
                "structure",
                "underneath",
                "theorem",
                "term",
                "terms",
                "explain",
                "describe",
                "relate",
                "relates",
                "related",
            }
        }
        example_child_match = re.search(
            r"/\s*give\b.*\bexample\b(?P<tail>.*)$",
            semantic_unit,
            flags=re.IGNORECASE,
        )
        if example_child_match:
            example_tail = str(example_child_match.group("tail") or "")
            domain_fragment = re.split(r"\busing\b", example_tail, maxsplit=1, flags=re.IGNORECASE)[0]
            domain_tokens = set(selection_signal_tokens(domain_fragment))
            combined_tokens = selection_signal_tokens(
                collapse_ws(
                    " ".join(
                        part
                        for part in (
                            artifact_selection_text(artifact),
                            self.artifact_answer_text(artifact, semantic_unit=semantic_unit),
                        )
                        if collapse_ws(part)
                    )
                ).lower()
            )
            if domain_tokens and (domain_tokens & combined_tokens):
                example_leaf_text = display_title_leaf_text(str(getattr(artifact, "title", "")).strip()).lower()
                if focus_alignment >= 1 and not any(
                    marker in example_leaf_text for marker in (" from ", " using ", " example", " case", " application")
                ):
                    return 2
                return 0 if explicit_answer_available or latent_answer_available else 2
            return 2 if focus_alignment >= 1 else 3
        if self.artifact_is_executable_function(artifact):
            if explicit_answer_available:
                return 0
            if latent_answer_available:
                return 3
            return 4
        if not explicit_answer_available and latent_answer_available:
            return 2 if focus_alignment >= 1 else 4
        if distinctive_focus_tokens:
            distinctive_hits = len(distinctive_focus_tokens & candidate_tokens)
            required_distinctive_hits = 1 if len(distinctive_focus_tokens) == 1 else 2
            if distinctive_hits < min(required_distinctive_hits, len(distinctive_focus_tokens)):
                return 3
            if len(distinctive_focus_tokens) >= 4 and distinctive_hits < 3:
                return 2
        if focus_alignment >= 2:
            return 0
        if focus_alignment == 1:
            return 1
        return 3

    def artifact_derivation_prompt_penalty(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str,
        current_posture: str,
    ) -> int:
        """
        High Level Purpose:
            In circumstances like long explanatory prompts that ask to state, distinguish, derive, construct, or identify a reusable substrate, helps with demoting artifacts whose answer shape does not satisfy the requested prompt form even when they overlap lexically.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `artifact_derivation_prompt_penalty(artifact=Artifact(id='artifact-rate', title='Physics / General Ratio Of Change', artifact_type='knowledge', representation='yaml'), semantic_unit='State the general ratio-of-change formula and give one example from motion that uses it.', current_posture='direct_resolution')`
            Output: 0

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_derivation_prompt_penalty`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `artifact_derivation_prompt_penalty`. Expected type: `str`.
            current_posture: Value for `current_posture` used by `artifact_derivation_prompt_penalty`. Expected type: `str`.

        Returns:
            int: Result produced by `artifact_derivation_prompt_penalty`.
        """
        if current_posture == "compute_or_template":
            return 0
        directive = semantic_prompt_directive_profile(semantic_unit)
        directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
        if directive_kind in {"", "none"}:
            return 0
        focus_text = collapse_ws(str(directive.get("focus_text", "")).strip())
        compared_terms = structured_text_list(directive.get("compared_terms", []))
        combined_text = collapse_ws(
            " ".join(
                part
                for part in (
                    artifact_selection_text(artifact),
                    self.artifact_answer_text(artifact, semantic_unit=semantic_unit),
                )
                if collapse_ws(part)
            )
        ).lower()
        combined_tokens = selection_signal_tokens(combined_text)
        leaf_text = display_title_leaf_text(str(getattr(artifact, "title", "")).strip()).lower()
        substrate_markers = (
            "reusable substrate",
            "reuses",
            "broader substrate",
            "broader family",
            "inverse-square",
            "inverse square",
            "multiplicative combination",
            "special case",
        )
        has_substrate_markers = (
            directive_kind == "identify_reusable_substrate"
            and any(marker in combined_text for marker in substrate_markers)
        )
        example_child_match = re.search(
            r"/\s*give\b.*\bexample\b(?P<tail>.*)$",
            semantic_unit,
            flags=re.IGNORECASE,
        )
        example_child = example_child_match is not None
        penalty = 0
        if artifact_is_structured_learning_record(artifact):
            penalty += 4
        if (
            focus_text
            and not example_child
            and artifact_focus_alignment_score(artifact, focus_text) <= 0
            and not has_substrate_markers
        ):
            penalty += 4
        focus_tokens = set(learning_core_tokens(focus_text))
        if focus_tokens and not example_child and not has_substrate_markers:
            focus_hits = len(focus_tokens & combined_tokens)
            if focus_hits == 0:
                penalty += 4
            elif focus_hits < min(2, len(focus_tokens)):
                penalty += 2
            if len(focus_tokens) >= 3 and focus_hits * 2 < len(focus_tokens):
                penalty += 2
            distinctive_focus_tokens = {
                token
                for token in focus_tokens
                if token not in {"general", "formula", "equation", "relation", "law", "example", "using", "state", "identify"}
            }
            if distinctive_focus_tokens:
                distinctive_hits = len(distinctive_focus_tokens & combined_tokens)
                required_distinctive_hits = 1 if len(distinctive_focus_tokens) == 1 else 2
                if distinctive_hits < min(required_distinctive_hits, len(distinctive_focus_tokens)):
                    penalty += 3
        if directive_kind == "distinguish" and compared_terms:
            missing_compared_terms = 0
            for term in compared_terms:
                term_lower = collapse_ws(str(term).strip()).lower()
                term_tokens = {
                    token
                    for token in learning_core_tokens(term_lower)
                    if token not in {"a", "an", "the", "quantity"}
                }
                if term_lower and term_lower in combined_text:
                    continue
                if term_tokens and (
                    term_tokens & combined_tokens
                    or any(
                        combined_token.startswith(term_token) or term_token.startswith(combined_token)
                        for term_token in term_tokens
                        for combined_token in combined_tokens
                    )
                ):
                    continue
                missing_compared_terms += 1
            if missing_compared_terms:
                penalty += min(4, missing_compared_terms * 2)
        if example_child_match:
            example_tail = str(example_child_match.group("tail") or "")
            domain_fragment = re.split(r"\busing\b", example_tail, maxsplit=1, flags=re.IGNORECASE)[0]
            domain_tokens = set(selection_signal_tokens(domain_fragment))
            missing_example_domain = bool(domain_tokens) and not (domain_tokens & combined_tokens)
            if missing_example_domain:
                penalty += 5
            if (
                missing_example_domain
                and focus_text
                and artifact_focus_alignment_score(artifact, focus_text) >= 1
                and collapse_ws(str(getattr(artifact, "content", {}).get("question", "")).strip()).lower().startswith("what is ")
            ):
                penalty += 4
            if any(marker in leaf_text for marker in ("general", "summary", "reusable substrate", "reusable knowledge")):
                penalty += 2
        primary_markers, secondary_markers = prompt_directive_support_markers(directive_kind)
        if not example_child:
            if primary_markers and not any(marker in combined_text for marker in primary_markers):
                penalty += 3
            elif secondary_markers and not any(marker in combined_text for marker in secondary_markers):
                penalty += 1
        if directive_kind in {"derive", "construct"}:
            if self.artifact_is_executable_function(artifact) and not str(self.artifact_runtime_content(artifact).get("answer", "")).strip():
                penalty += 2
            if len(combined_text) < 72:
                penalty += 1
            if any(
                marker in leaf_text
                for marker in ("reusable knowledge", "general", "proportional mapping", "connection to earlier lessons")
            ) and not any(marker in combined_text for marker in ("therefore", "then", "using", "from", "substitute", "=")):
                penalty += 3
        if directive_kind == "identify_reusable_substrate":
            if self.looks_like_generic_markdown_current_identity(leaf_text, encounter_heading=leaf_text):
                penalty += 2
            if not has_substrate_markers:
                penalty += 4
            if any(marker in combined_text for marker in ("$$", " = ", "formula is", "law is")) and not any(
                marker in combined_text for marker in ("reuses", "reusable substrate", "broader", "special case")
            ):
                penalty += 3
        if directive_kind == "state" and bool(directive.get("requires_formula", False)) and not example_child:
            if not any(marker in combined_text for marker in ("=", "formula", "equation", "law", "relation")):
                penalty += 2
            if focus_tokens and len(focus_tokens & combined_tokens) < min(2, len(focus_tokens)):
                penalty += 2
        if directive_kind == "state" and "state-plus-change" in collapse_ws(str(semantic_unit or "")).lower():
            if focus_tokens and len(focus_tokens & combined_tokens) < min(3, len(focus_tokens)):
                penalty += 4
            if not any(
                marker in combined_text
                for marker in (
                    "state-plus-change",
                    "state plus change",
                    "initial velocity",
                    "final velocity",
                    "velocity changes",
                    "velocity update",
                    "update",
                    "change",
                )
            ):
                penalty += 3
        return penalty

    def answer_candidate_rank(
        self,
        artifact: Artifact,
        *,
        semantic_unit: str,
        current_boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
    ) -> tuple[Any, ...]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with answering candidate rank.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `answer_candidate_rank(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), semantic_unit='Physics / Force / Force From Mass And Acceleration', current_boundary_shape=['input', 'input', 'output'])`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `answer_candidate_rank`. Expected type: `Artifact`.
            semantic_unit: Value for `semantic_unit` used by `answer_candidate_rank`. Expected type: `str`.
            current_boundary_shape: Value for `current_boundary_shape` used by `answer_candidate_rank`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.

        Returns:
            tuple[Any, ...]: Result produced by `answer_candidate_rank`.
        """
        effective_semantic_unit = self.artifact_query_semantic_unit(
            artifact,
            semantic_unit=semantic_unit,
        )
        formal_title_identity = self.artifact_formal_title_identity(artifact)
        structural_match_penalty = 1
        if (
            effective_semantic_unit
            and looks_like_prolog_title_identity(effective_semantic_unit)
            and looks_like_prolog_title_identity(formal_title_identity)
            and prolog_title_match_score(effective_semantic_unit, formal_title_identity) >= 95
        ):
            structural_match_penalty = 0
        executable = self.artifact_is_executable_function(artifact)
        invocation_payload = self.derive_artifact_invocation_payload(
            artifact,
            semantic_unit=semantic_unit,
        ) if executable else None
        has_invokable_payload, satisfied_inputs, total_inputs = self.artifact_invocation_payload_coverage(
            artifact,
            invocation_payload=invocation_payload,
        ) if executable else (False, 0, 0)
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        has_stored_answer = self.artifact_has_answer_capability(
            artifact,
            semantic_unit=effective_semantic_unit or semantic_unit,
        )
        has_output_contract = isinstance(content.get("output_contract", {}), Mapping) and bool(content.get("output_contract", {}))
        shape_rank = boundary_shape_rank(current_boundary_shape, artifact.boundary_shape)
        surface_rank = artifact_surface_alignment_rank(artifact, effective_semantic_unit or semantic_unit)
        text_rank = artifact_text_alignment_rank(artifact, semantic_unit)
        elaboration_rank = not_elaboration_alignment_rank(
            artifact,
            effective_semantic_unit or semantic_unit,
            current_boundary_shape=current_boundary_shape,
        )
        current_posture = semantic_prompt_action_posture(semantic_unit)
        safety_penalty = artifact_prompt_decision_mismatch_penalty(artifact, semantic_unit)
        compute_prompt_penalty = self.artifact_compute_prompt_penalty(
            artifact,
            semantic_unit=semantic_unit,
            current_posture=current_posture,
        )
        exact_output_symbol_penalty = self.artifact_exact_output_symbol_penalty(
            artifact,
            semantic_unit=semantic_unit,
        )
        direct_knowledge_penalty = self.artifact_direct_knowledge_prompt_penalty(
            artifact,
            semantic_unit=semantic_unit,
            current_posture=current_posture,
        )
        direct_definition_penalty = self.artifact_direct_definition_penalty(
            artifact,
            semantic_unit=semantic_unit,
        )
        directive = semantic_prompt_directive_profile(semantic_unit)
        directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
        explanatory_prompt = (
            directive_kind in {"construct", "derive", "distinguish", "identify_reusable_substrate"}
            or bool(directive.get("requires_chain", False))
            or bool(directive.get("requires_contrast", False))
            or bool(directive.get("requires_substrate", False))
        )
        derivation_prompt_penalty = self.artifact_derivation_prompt_penalty(
            artifact,
            semantic_unit=semantic_unit,
            current_posture=current_posture,
        )
        action_alignment_penalty = artifact_action_alignment_penalty(
            artifact,
            semantic_unit,
        )
        breadth_penalty = self.artifact_scope_breadth_penalty(artifact, semantic_unit=semantic_unit)
        posture_execution_penalty = 0
        if current_posture == "compute_or_template":
            if executable and has_invokable_payload:
                posture_execution_penalty = 0
            elif executable:
                posture_execution_penalty = 1
            elif has_stored_answer:
                posture_execution_penalty = 3
            else:
                posture_execution_penalty = 4
        elif current_posture in {"direct_resolution", "next_step_guidance", "clarify_before_acting"}:
            if executable and not has_stored_answer:
                posture_execution_penalty = 2 if has_invokable_payload else 4
                if explanatory_prompt and not has_invokable_payload:
                    posture_execution_penalty += 4
        return (
            structural_match_penalty,
            safety_penalty,
            compute_prompt_penalty,
            exact_output_symbol_penalty,
            direct_knowledge_penalty,
            direct_definition_penalty,
            derivation_prompt_penalty,
            action_alignment_penalty,
            posture_execution_penalty,
            breadth_penalty,
            elaboration_rank[0],
            elaboration_rank[1],
            elaboration_rank[2],
            elaboration_rank[3],
            elaboration_rank[4],
            elaboration_rank[5],
            elaboration_rank[6],
            shape_rank[0],
            shape_rank[1],
            shape_rank[2],
            0 if executable and has_invokable_payload else 1,
            -satisfied_inputs,
            total_inputs,
            0 if has_stored_answer else 1,
            0 if has_output_contract else 1,
            surface_rank[0],
            surface_rank[1],
            surface_rank[2],
            surface_rank[3],
            text_rank[0],
            text_rank[1],
            text_rank[2],
            text_rank[3],
            str(artifact.title).lower(),
        )

    focused_direct_knowledge_candidates = focused_direct_knowledge_reuse_candidates

    def artifact_invocation_payload_coverage(
        self,
        artifact: Artifact,
        *,
        invocation_payload: Any,
    ) -> tuple[bool, int, int]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling artifact invocation payload coverage.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `artifact_invocation_payload_coverage(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'), invocation_payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_invocation_payload_coverage`. Expected type: `Artifact`.
            invocation_payload: Value for `invocation_payload` used by `artifact_invocation_payload_coverage`. Expected type: `Any`.

        Returns:
            tuple[bool, int, int]: Result produced by `artifact_invocation_payload_coverage`.
        """
        content = self.artifact_runtime_content(artifact)
        input_contract = content.get("input_contract", {})
        if not isinstance(input_contract, Mapping):
            return (invocation_payload not in (None, "", [], {}), 0, 0)
        if not input_contract:
            return (True, 0, 0)
        required_keys = [str(key).strip() for key in input_contract.keys() if str(key).strip()]
        if not required_keys:
            return (invocation_payload not in (None, "", [], {}), 0, 0)
        if not isinstance(invocation_payload, Mapping):
            return (False, 0, len(required_keys))
        satisfied = 0
        for key in required_keys:
            if key in invocation_payload and invocation_payload.get(key) not in (None, "", [], {}):
                satisfied += 1
        return (satisfied == len(required_keys), satisfied, len(required_keys))

    runtime_make_id = staticmethod(make_id)
    runtime_plain_prompt = staticmethod(plain_prompt)
    level_at_least_runtime = staticmethod(level_at_least)
    execute_mediated_artifact_effect = execute_governed_mediated_artifact_effect
    execute_mediated_host_broker_request = execute_governed_mediated_host_broker_request
    record_effect_trace = record_governed_effect_trace
    lookup_prior_non_achievedness = lookup_governed_prior_non_achievedness
    learning_context_query_variants = governed_learning_context_query_variants
    build_structured_learning_artifact = build_governed_structured_learning_artifact
    build_immediate_learning_artifact = build_governed_immediate_learning_artifact
    load_learning_context = governed_load_learning_context

    def subject_reasoning_scope_payload(self) -> dict[str, Any]:
        payload = getattr(self.state, "subject_reasoning_scope", {})
        return dict(payload) if isinstance(payload, Mapping) else {}

    def subject_scope_global_retrieval_enabled(self) -> bool:
        policy = collapse_ws(str(self.subject_reasoning_scope_payload().get("global_retrieval_policy", ""))).casefold()
        return policy in {"enabled", "enable", "global", "allow", "on", "true", "yes"}

    def learned_artifact_origin_payload(self, artifact_id: str) -> dict[str, Any]:
        payload = getattr(self.state, "learned_artifact_origins", {})
        if not isinstance(payload, Mapping):
            return {}
        item = payload.get(str(artifact_id).strip(), {})
        return dict(item) if isinstance(item, Mapping) else {}

    def learned_artifact_origin_kind(self, artifact_id: str) -> str:
        return collapse_ws(str(self.learned_artifact_origin_payload(artifact_id).get("origin_kind", ""))).casefold() or "global"

    def register_learned_artifact_origin(
        self,
        artifact: Artifact,
        *,
        origin_kind: str = "global",
        origin_payload: Mapping[str, Any] | None = None,
    ) -> None:
        artifact_id = str(getattr(artifact, "id", "")).strip()
        if not artifact_id:
            return
        current = self.learned_artifact_origin_payload(artifact_id)
        normalized_origin_kind = collapse_ws(origin_kind).casefold() or "global"
        if current and current.get("origin_kind") in {"primary", "borrowed"} and normalized_origin_kind == "global":
            return
        payload = {"origin_kind": normalized_origin_kind}
        if isinstance(origin_payload, Mapping):
            payload.update({str(key): value for key, value in origin_payload.items()})
        if not isinstance(getattr(self.state, "learned_artifact_origins", None), dict):
            self.state.learned_artifact_origins = {}
        self.state.learned_artifact_origins[artifact_id] = payload

    def learned_artifact_origin_report(self, artifact_ids: Iterable[str]) -> dict[str, Any]:
        seen_ids: set[str] = set()
        counts: dict[str, int] = {}
        items: list[dict[str, Any]] = []
        for raw_artifact_id in artifact_ids:
            artifact_id = collapse_ws(str(raw_artifact_id))
            if not artifact_id or artifact_id in seen_ids:
                continue
            seen_ids.add(artifact_id)
            origin = self.learned_artifact_origin_payload(artifact_id)
            origin_kind = collapse_ws(str(origin.get("origin_kind", ""))).casefold() or "global"
            counts[origin_kind] = counts.get(origin_kind, 0) + 1
            artifact = self.state.learned_artifacts.get(artifact_id) or self.state.artifacts.get(artifact_id)
            item = {
                "artifact_id": artifact_id,
                "title": collapse_ws(str(getattr(artifact, "title", ""))),
                "artifact_type": collapse_ws(str(getattr(artifact, "artifact_type", ""))),
                "origin_kind": origin_kind,
            }
            for key in (
                "source_subject_id",
                "source_subject_version_id",
                "source_import_id",
                "import_kind",
            ):
                value = collapse_ws(str(origin.get(key, "")))
                if value:
                    item[key] = value
            items.append(item)
        return {
            "counts": counts,
            "items": items,
        }

    def subject_scope_relevant_artifacts(self, semantic_unit: str, *, limit: int = 8) -> list[Artifact]:
        if not self.subject_reasoning_scope_payload():
            return []
        ranked: list[tuple[Any, ...]] = []
        seen_ids: set[str] = set()
        origin_priority = {"primary": 0, "borrowed": 1, "global": 2}
        for artifact in self.state.learned_artifacts.values():
            artifact_id = str(getattr(artifact, "id", "")).strip()
            if not artifact_id or artifact_id in seen_ids or artifact.admissibility == "rejected":
                continue
            seen_ids.add(artifact_id)
            ranked.append(
                (
                    origin_priority.get(self.learned_artifact_origin_kind(artifact_id), 3),
                    *self.answer_candidate_rank(
                        artifact,
                        semantic_unit=semantic_unit,
                    ),
                    artifact,
                )
            )
        ranked.sort()
        return [artifact for *_, artifact in ranked[:limit]]

    @measured_performance("candidate_retrieval_latency_ns")
    def store_relevant_artifacts(self, semantic_unit: str, *, limit: int = 8) -> list[Artifact]:
        local_artifacts = self.subject_scope_relevant_artifacts(semantic_unit, limit=limit)
        if self.subject_reasoning_scope_payload() and not self.subject_scope_global_retrieval_enabled():
            return local_artifacts
        if self.subject_reasoning_scope_payload() and len(local_artifacts) >= limit:
            return local_artifacts[:limit]
        artifacts = self.artifact_store.load_relevant_artifacts(semantic_unit, limit=limit)
        ordered: dict[str, Artifact] = {
            str(getattr(artifact, "id", "")).strip(): artifact
            for artifact in local_artifacts
            if str(getattr(artifact, "id", "")).strip()
        }
        for artifact in artifacts:
            artifact_id = str(getattr(artifact, "id", "")).strip()
            if not artifact_id:
                continue
            self.state.learned_artifacts.setdefault(artifact_id, artifact)
            self.register_learned_artifact_origin(artifact, origin_kind="global")
            ordered.setdefault(artifact_id, artifact)
        return list(ordered.values())[:limit]

    def reusable_artifact_candidates(self) -> list[Artifact]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling reusable artifact candidates.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `reusable_artifact_candidates()`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            list[Artifact]: Result produced by `reusable_artifact_candidates`.
        """
        ordered: dict[str, Artifact] = {}
        learned_values = list(self.state.learned_artifacts.values())
        for origin_kind in ("primary", "borrowed", "global"):
            for artifact in learned_values:
                if artifact.admissibility == "rejected":
                    continue
                if self.learned_artifact_origin_kind(artifact.id) != origin_kind:
                    continue
                ordered.setdefault(artifact.id, artifact)
        for artifact in learned_values:
            if artifact.admissibility == "rejected":
                continue
            ordered.setdefault(artifact.id, artifact)
        for artifact in self.state.artifacts.values():
            if artifact.admissibility == "rejected":
                continue
            ordered.setdefault(artifact.id, artifact)
        return list(ordered.values())

    def artifact_learning_summary(self, artifact: Artifact) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with summarizing artifact learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `artifact_learning_summary(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_learning_summary`. Expected type: `Artifact`.

        Returns:
            dict[str, Any]: Result produced by `artifact_learning_summary`.
        """
        structured = self.artifact_structured_learning_view(artifact)
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        answer = str(content.get("answer", "")).strip()
        question = str(content.get("question", "")).strip()
        return {
            "id": artifact.id,
            "title": artifact.title,
            "artifact_type": artifact.artifact_type,
            "scope": artifact.scope,
            "reusability": artifact.reusability,
            "learning_relation": artifact.learning_relation,
            "encountered_not": structured.get("encountered_not", ""),
            "component_nots": structured.get("component_nots", []),
            "composed_not": structured.get("composed_not", ""),
            "question": question,
            "answer_excerpt": answer[:280],
        }

    immediate_learning_context_artifacts = governed_immediate_learning_context_artifacts

    def immediate_learning_bridge_opportunities(
        self,
        node: SemanticNode,
        nearby_artifacts: list[Artifact],
        *,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling immediate learning bridge opportunities.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `immediate_learning_bridge_opportunities(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), nearby_artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], limit=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `immediate_learning_bridge_opportunities`. Expected type: `SemanticNode`.
            nearby_artifacts: Value for `nearby_artifacts` used by `immediate_learning_bridge_opportunities`. Expected type: `list[Artifact]`.
            limit: Value for `limit` used by `immediate_learning_bridge_opportunities`. Expected type: `int`. Defaults to `6`.

        Returns:
            list[dict[str, Any]]: Result produced by `immediate_learning_bridge_opportunities`.
        """
        current = node.metadata.get("structured_learning", self.structured_learning_view(node))
        current_family = titleize_semantic_unit(str(current.get("encountered_not", "")).strip())
        current_components = [
            titleize_semantic_unit(str(item).strip())
            for item in current.get("component_nots", [])
            if titleize_semantic_unit(str(item).strip())
        ] if isinstance(current.get("component_nots", []), list) else []
        if not current_family:
            return []

        opportunities: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for artifact in nearby_artifacts:
            prior = self.artifact_structured_learning_view(artifact)
            prior_family = titleize_semantic_unit(str(prior.get("encountered_not", "")).strip())
            prior_components = [
                titleize_semantic_unit(str(item).strip())
                for item in prior.get("component_nots", [])
                if titleize_semantic_unit(str(item).strip())
            ] if isinstance(prior.get("component_nots", []), list) else []
            candidate_terms = prior_components or ([prior_family] if prior_family else [])
            for candidate in candidate_terms:
                if not candidate:
                    continue
                if candidate.lower() == current_family.lower():
                    continue
                if any(candidate.lower() == component.lower() for component in current_components):
                    continue
                key = (current_family.lower(), candidate.lower())
                if key in seen:
                    continue
                composed_family = titleize_semantic_unit(" ".join([current_family, candidate]))
                opportunities.append(
                    {
                        "current_family": current_family,
                        "other_family": candidate,
                        "source_artifact_id": artifact.id,
                        "source_artifact_title": artifact.title,
                        "source_encountered_not": prior_family,
                        "suggested_bridge_encountered_not": composed_family,
                        "suggested_bridge_semantic_unit": f"How does {candidate} relate to {current_family}?",
                    }
                )
                seen.add(key)
                if len(opportunities) >= limit:
                    return opportunities
        return opportunities

    instantiate_reusable_artifact_support = instantiate_governed_reusable_artifact_support

    def proposal_state_slice(self, node: SemanticNode | None) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling proposal state slice.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `proposal_state_slice(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `proposal_state_slice`. Expected type: `SemanticNode | None`.

        Returns:
            dict[str, Any]: Result produced by `proposal_state_slice`.
        """
        root = self.state.root()
        root_structured = root.metadata.get("structured_learning", {})
        node_slice: dict[str, Any] = {
            "overall_task": {
                "id": root.id,
                "focus": root.semantic_unit,
                "status": self.state.node_status(root.id).value,
                "certainty": self.state.certainty.get(root.id, ThreeLevel.LOW),
                "structured_learning": {
                    "encountered_not": root_structured.get("encountered_not", ""),
                    "goal": root_structured.get("goal", ""),
                    "givens": root_structured.get("givens", []),
                    "unknowns": root_structured.get("unknowns", []),
                    "differentiators": root_structured.get("differentiators", []),
                    "contrastive_cases": root_structured.get("contrastive_cases", []),
                    "risk_of_wrong_closure": root_structured.get("risk_of_wrong_closure", []),
                    "disallowed_assumptions": root_structured.get("disallowed_assumptions", []),
                    "action_posture": root_structured.get("action_posture", ""),
                    "boundary_shape": root_structured.get("boundary_shape", []),
                },
            },
            "learned_artifacts": [
                {
                    "id": artifact.id,
                    "artifact_type": artifact.artifact_type,
                    "title": artifact.title,
                    "scope": artifact.scope,
                    "reusability": artifact.reusability,
                    "admissibility": artifact.admissibility,
                    "learning_relation": artifact.learning_relation,
                    "related_artifact_ids": artifact.related_artifact_ids,
                    "template_bearing": is_template_bearing_artifact_type(artifact.artifact_type),
                    "template_schema": self.template_schema_summary(artifact),
                    "ability_summary": self.ability_artifact_summary(artifact) if artifact.artifact_type == "ability" else {},
                }
                for artifact in list(self.state.learned_artifacts.values())[:6]
            ],
            "frontier_size": len(self.state.frontier),
            "recent_steps": [
                {
                    "seq": record.seq,
                    "kind": record.kind,
                    "node_id": record.node_id,
                    "result": record.result,
                }
                for record in self.state.ledger[-6:]
            ],
        }
        if node is not None:
            support = self.state.support.get(node.id, SupportView([], [], SupportScore.VERY_BAD))
            structured_learning = node.metadata.get("structured_learning", {})
            structured_lookup = node.metadata.get("structured_learning_lookup", {})
            relevant_evidence = []
            for evidence_id in list(dict.fromkeys(support.direct + support.upstream)):
                evidence = self.state.evidence.get(evidence_id)
                if evidence is None:
                    continue
                relevant_evidence.append(
                    {
                        "id": evidence.id,
                        "source": evidence.source,
                        "polarity": evidence.polarity,
                        "confidence": evidence.confidence,
                        "support_strength": evidence.support_effect,
                    }
                )
            relevant_pauses = [
                {
                    "id": pause.id,
                    "required_boundary": pause.required_boundary,
                    "reason": pause.reason,
                }
                for pause in self.state.pause_points.values()
                if pause.node_id == node.id
            ]
            node_slice["active_item"] = {
                "id": node.id,
                "focus": node.semantic_unit,
                "role": node.role,
                "status": self.state.node_status(node.id).value,
                "depth": node.depth,
                "parent_id": node.parent_id,
                "boundary_shape": list(node.boundary_shape),
                "required": node.required,
                "evidence_required": node.evidence_required,
                "decomposition_mode": node.decomposition_mode,
                "priority": node.priority_bias,
                "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
                "faithfulness": str(node.metadata.get("faithfulness", "low")),
                "open_issues": list(self.state.blockers.get(node.id, [])),
                "conflicts": list(self.state.conflicts.get(node.id, [])),
                "support": {
                    "direct_evidence_ids": list(support.direct),
                    "upstream_evidence_ids": list(support.upstream),
                    "support_score": support.score,
                },
                "structured_learning": {
                    "encountered_not": structured_learning.get("encountered_not", ""),
                    "goal": structured_learning.get("goal", ""),
                    "givens": structured_learning.get("givens", []),
                    "unknowns": structured_learning.get("unknowns", []),
                    "differentiators": structured_learning.get("differentiators", []),
                    "contrastive_cases": structured_learning.get("contrastive_cases", []),
                    "risk_of_wrong_closure": structured_learning.get("risk_of_wrong_closure", []),
                    "disallowed_assumptions": structured_learning.get("disallowed_assumptions", []),
                    "action_posture": structured_learning.get("action_posture", ""),
                    "lookup_keys": structured_learning.get("lookup_keys", []),
                    "component_nots": structured_learning.get("component_nots", []),
                    "composed_not": structured_learning.get("composed_not", ""),
                    "match_kind": structured_lookup.get("match_kind", "none"),
                    "matched_artifact_ids": structured_lookup.get("artifact_ids", []),
                    "matched_artifact_origin_report": structured_lookup.get("artifact_origin_report", {}),
                    "loaded_artifact_origin_report": structured_lookup.get("loaded_artifact_origin_report", {}),
                },
                "evidence": relevant_evidence,
                "pause_points": relevant_pauses,
                "children": self.child_context_payload(node),
            }
        return node_slice

    def proposal_state_slice_for_deterministic_replay(self, node: SemanticNode | None) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like deterministic recording and replay of LLM supplements, helps with providing a stable state slice that can be hashed into request digests across runs.

        Reference to Theory:
            Supports the governed runtime determinism and replay contract by ensuring that volatile, run-specific identifiers (run ids, ledger sequence numbers, evidence ids, etc.) do not prevent replay.

        Notes:
            This slice is intentionally smaller than `proposal_state_slice(...)` and omits volatile identifiers and recent-step traces. It is only used when the runtime determinism policy requests deterministic recording or replay.
        """

        def stable_structured_learning(payload: Any) -> dict[str, Any]:
            data = dict(payload) if isinstance(payload, Mapping) else {}
            return {
                "encountered_not": data.get("encountered_not", ""),
                "goal": data.get("goal", ""),
                "givens": data.get("givens", []),
                "unknowns": data.get("unknowns", []),
                "differentiators": data.get("differentiators", []),
                "contrastive_cases": data.get("contrastive_cases", []),
                "risk_of_wrong_closure": data.get("risk_of_wrong_closure", []),
                "disallowed_assumptions": data.get("disallowed_assumptions", []),
                "action_posture": data.get("action_posture", ""),
                "boundary_shape": data.get("boundary_shape", []),
                "lookup_keys": data.get("lookup_keys", []),
                "component_nots": data.get("component_nots", []),
                "composed_not": data.get("composed_not", ""),
            }

        root = self.state.root()
        root_structured = stable_structured_learning(root.metadata.get("structured_learning", {}))

        snapshot: dict[str, Any] = {
            "overall_task": {
                "focus": root.semantic_unit,
                "status": self.state.node_status(root.id).value,
                "certainty": self.state.certainty.get(root.id, ThreeLevel.LOW),
                "structured_learning": root_structured,
            },
            "learned_artifacts": [
                {
                    "artifact_type": artifact.artifact_type,
                    "title": artifact.title,
                    "scope": artifact.scope,
                    "reusability": artifact.reusability,
                    "admissibility": artifact.admissibility,
                    "learning_relation": artifact.learning_relation,
                    "template_bearing": is_template_bearing_artifact_type(artifact.artifact_type),
                }
                for artifact in sorted(
                    list(self.state.learned_artifacts.values())[:12],
                    key=lambda item: (str(getattr(item, "artifact_type", "")), str(getattr(item, "title", ""))),
                )[:6]
            ],
        }

        if node is None:
            return snapshot

        structured_learning = stable_structured_learning(node.metadata.get("structured_learning", {}))
        snapshot["active_item"] = {
            "focus": node.semantic_unit,
            "role": node.role,
            "status": self.state.node_status(node.id).value,
            "depth": node.depth,
            "boundary_shape": list(node.boundary_shape),
            "required": node.required,
            "evidence_required": node.evidence_required,
            "decomposition_mode": node.decomposition_mode,
            "priority": node.priority_bias,
            "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
            "faithfulness": str(node.metadata.get("faithfulness", "low")),
            "open_issues": list(self.state.blockers.get(node.id, [])),
            "conflicts": list(self.state.conflicts.get(node.id, [])),
            "structured_learning": structured_learning,
            "children": [
                {
                    "focus": child.semantic_unit,
                    "role": child.role,
                    "status": self.state.node_status(child.id).value,
                    "required": child.required,
                    "depth": child.depth,
                    "boundary_shape": list(child.boundary_shape),
                    "certainty": self.state.certainty.get(child.id, ThreeLevel.LOW),
                }
                for child in self.refinement_children(node)
            ],
        }
        return snapshot

    def child_context_payload(self, node: SemanticNode) -> list[dict[str, Any]]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for child context.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `child_context_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `child_context_payload`. Expected type: `SemanticNode`.

        Returns:
            list[dict[str, Any]]: Result produced by `child_context_payload`.
        """
        children_payload: list[dict[str, Any]] = []
        for child in self.refinement_children(node):
            support = self.state.support.get(child.id, SupportView([], [], SupportScore.VERY_BAD))
            children_payload.append(
                {
                    "id": child.id,
                    "focus": child.semantic_unit,
                    "role": child.role,
                    "status": self.state.node_status(child.id).value,
                    "required": child.required,
                    "depth": child.depth,
                    "boundary_shape": list(child.boundary_shape),
                    "certainty": self.state.certainty.get(child.id, ThreeLevel.LOW),
                    "faithfulness": str(child.metadata.get("faithfulness", "low")),
                    "open_issues": list(self.state.blockers.get(child.id, [])),
                    "conflicts": list(self.state.conflicts.get(child.id, [])),
                    "support": {
                        "support_score": support.score,
                    },
                }
            )
        return children_payload

    def decomposition_parent_context_payload(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for decomposition parent context.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `decomposition_parent_context_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `decomposition_parent_context_payload`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `decomposition_parent_context_payload`.
        """
        if not node.parent_id or node.parent_id not in self.state.graph.nodes:
            return {}
        parent = self.state.graph.get_node(node.parent_id)
        parent_structured = self.structured_learning_view(parent)
        support = self.state.support.get(parent.id, SupportView([], [], SupportScore.VERY_BAD))
        return {
            "id": parent.id,
            "focus": parent.semantic_unit,
            "role": parent.role,
            "status": self.state.node_status(parent.id).value,
            "description": parent.description,
            "boundary_shape": list(parent.boundary_shape),
            "certainty": self.state.certainty.get(parent.id, ThreeLevel.LOW),
            "open_issues": list(self.state.blockers.get(parent.id, [])),
            "conflicts": list(self.state.conflicts.get(parent.id, [])),
            "support": {
                "support_score": support.score,
                "direct_evidence_ids": list(support.direct),
                "upstream_evidence_ids": list(support.upstream),
            },
            "structured_learning": parent_structured,
        }

    def decomposition_certain_sibling_context_payload(self, node: SemanticNode) -> list[dict[str, Any]]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for decomposition certain sibling context.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `decomposition_certain_sibling_context_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `decomposition_certain_sibling_context_payload`. Expected type: `SemanticNode`.

        Returns:
            list[dict[str, Any]]: Result produced by `decomposition_certain_sibling_context_payload`.
        """
        if not node.parent_id or node.parent_id not in self.state.graph.nodes:
            return []
        parent = self.state.graph.get_node(node.parent_id)
        siblings: list[dict[str, Any]] = []
        for sibling in self.refinement_children(parent):
            if sibling.id == node.id:
                break
            sibling_status = self.state.node_status(sibling.id)
            sibling_certainty = normalize_three_level(
                self.state.certainty.get(sibling.id, ThreeLevel.LOW),
                default=ThreeLevel.LOW,
            )
            if sibling_certainty == ThreeLevel.LOW and sibling_status not in {NodeStatus.CLOSED, NodeStatus.CLOSABLE}:
                continue
            support = self.state.support.get(sibling.id, SupportView([], [], SupportScore.VERY_BAD))
            sibling_structured = self.structured_learning_view(sibling)
            siblings.append(
                {
                    "id": sibling.id,
                    "focus": sibling.semantic_unit,
                    "role": sibling.role,
                    "status": sibling_status.value,
                    "required": sibling.required,
                    "description": sibling.description,
                    "boundary_shape": list(sibling.boundary_shape),
                    "certainty": sibling_certainty,
                    "support": {
                        "support_score": support.score,
                        "direct_evidence_ids": list(support.direct),
                        "upstream_evidence_ids": list(support.upstream),
                    },
                    "structured_learning": sibling_structured,
                    "direct_resolution_answer_kind": str(sibling.metadata.get("direct_resolution_answer_kind", "")).strip(),
                }
            )
        return siblings

    def select_supplement_mode(self, locus: str, node: SemanticNode | None) -> SupplementMode:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with selecting supplement mode.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `select_supplement_mode(locus='force', node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: SupplementMode.REQUIRED

        Args:
            self: Bound instance that owns the runtime state used by this method.
            locus: Value for `locus` used by `select_supplement_mode`. Expected type: `str`.
            node: Value for `node` used by `select_supplement_mode`. Expected type: `SemanticNode | None`.

        Returns:
            SupplementMode: Result produced by `select_supplement_mode`.
        """
        if locus in {"control_decision", "node_assessment"}:
            return SupplementMode.FAST
        if locus in {"contemplation", "reframe", "template", "retrieval", "uncertainty", "discovery", "not_elaboration"}:
            return SupplementMode.DEEP
        if node is None:
            return SupplementMode.FAST
        if node.depth == 0 or self.state.visit_counts.get(node.id, 0) > 1:
            return SupplementMode.DEEP
        if len(self.state.blockers.get(node.id, [])) > 1:
            return SupplementMode.DEEP
        return SupplementMode.FAST

    def build_prompt_state_reference(self, node: SemanticNode | None) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building prompt state reference.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `build_prompt_state_reference(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `build_prompt_state_reference`. Expected type: `SemanticNode | None`.

        Returns:
            str: Result produced by `build_prompt_state_reference`.
        """
        node_part = node.id if node is not None else "state"
        return f"run:{self.state.run_id}:seq:{self.state.sequence_counter}:node:{node_part}"

    def should_preserve_construct_chain_prompt_surface(self, semantic_unit: str) -> bool:
        directive = semantic_prompt_directive_profile(semantic_unit)
        if collapse_ws(str(directive.get("kind", "")).strip()) != "construct":
            return False
        if not bool(directive.get("requires_chain", False)):
            return False
        if semantic_requested_output_phrases(semantic_unit):
            return False
        normalized_text = collapse_ws(str(semantic_unit or "")).lower()
        if not normalized_text:
            return False
        if re.search(r"\bpathway\b|\bworkflow\b|\bpipeline\b|\bsequence\b|\bstages?\b|\bsteps?\b", normalized_text):
            return False
        has_formula_surface = bool(re.search(r"\([^)]*=[^)]*\)", str(semantic_unit or "")))
        has_derivation_surface = bool(
            re.search(
                r"\bexpressions?\b|\bequations?\b|\bformula(?:e|s)?\b|\bderive(?:d|s|ing)?\b|\bderivation\b|\bcomposes?\b|\bcomposition\b|\bfinal form\b",
                normalized_text,
            )
        )
        return has_formula_surface or has_derivation_surface

    def fallback_construct_chain_components(self, semantic_unit: str) -> list[str]:
        directive = semantic_prompt_directive_profile(semantic_unit)
        directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
        if directive_kind not in {"construct", "derive"}:
            return []
        if not bool(directive.get("requires_chain", False)):
            return []
        if self.should_preserve_construct_chain_prompt_surface(semantic_unit):
            return []
        components: list[str] = []
        focus_text = collapse_ws(str(directive.get("focus_text", "")).strip())
        focus_component = normalize_semantic_component_title(focus_text) or titleize_semantic_unit(focus_text)
        if focus_component:
            components.append(focus_component)
        normalized_text = collapse_ws(str(semantic_unit or "")).strip()
        for pattern in (
            r"\band explain why (?P<clause>.+)$",
            r"\band explain how (?P<clause>.+)$",
            r"\band show how (?P<clause>.+)$",
            r"\band identify (?P<clause>.+)$",
            r"\band describe (?P<clause>.+)$",
            r"\band reconstruct (?P<clause>.+)$",
        ):
            match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
            if not match:
                continue
            clause_text = re.sub(r"[.?!]+$", "", collapse_ws(str(match.group("clause")).strip()))
            clause_component = (
                normalize_semantic_component_title(clause_text)
                or titleize_semantic_unit(clause_text)
                or clause_text
            )
            if clause_component:
                components.append(clause_component)
            break
        return ordered_unique(component for component in components if collapse_ws(component))[:4]

    @measured_performance("proposal_latency_ns")
    def request_proposal(
        self,
        *,
        proposal_type: ProposalType,
        node: SemanticNode | None,
        target_scope: str,
        instructions: str,
        fallback_payload: dict[str, Any],
        mode: SupplementMode | None = None,
        schema_hint: dict[str, Any] | None = None,
    ) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling request proposal.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `request_proposal(proposal_type=ProposalType.NOT_ELABORATION, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), target_scope='force', instructions='Compute force from mass and acceleration.')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal_type: Value for `proposal_type` used by `request_proposal`. Expected type: `ProposalType`.
            node: Value for `node` used by `request_proposal`. Expected type: `SemanticNode | None`.
            target_scope: Value for `target_scope` used by `request_proposal`. Expected type: `str`.
            instructions: Value for `instructions` used by `request_proposal`. Expected type: `str`.
            fallback_payload: Value for `fallback_payload` used by `request_proposal`. Expected type: `dict[str, Any]`.
            mode: Value for `mode` used by `request_proposal`. Expected type: `SupplementMode | None`. Defaults to `None`.
            schema_hint: Value for `schema_hint` used by `request_proposal`. Expected type: `dict[str, Any] | None`. Defaults to `None`.

        Returns:
            ProposalObject: Result produced by `request_proposal`.
        """
        selected_mode = mode or self.select_supplement_mode(proposal_type.value, node)
        semantic_role = f"llm_{selected_mode.value}_supplement"
        determinism_policy = getattr(self.state, "determinism_policy", None)
        determinism_mode = str(getattr(determinism_policy, "mode", "governed") or "governed").strip().lower() or "governed"
        llm_strategy = str(getattr(determinism_policy, "llm_strategy", "live") or "live").strip() or "live"
        llm_seed = getattr(determinism_policy, "llm_seed", None)
        if self.should_skip_related_proposal_from_prior_learning(proposal_type, node):
            result = LLMSupplementResult(
                payload=dict(json_safe(fallback_payload)),
                source="prior_learning_bypass",
                provider=self.llm.provider,
                model=None,
            )
        else:
            if self.llm.enabled:
                self.use_capability(
                    semantic_role,
                    node=node,
                    contribution=f"produce {proposal_type.value}",
                )

            prompt = (
                f"{instructions}\n\n"
                "Current state snapshot:\n"
                f"{json.dumps(self.proposal_state_slice_for_deterministic_replay(node) if determinism_mode in {'deterministic', 'replay'} else self.proposal_state_slice(node), indent=2, sort_keys=True)}"
            )
            try:
                if llm_strategy == "replay":
                    system_msg = llm_supplement_system_message()
                    request_digest = llm_supplement_request_digest(
                        proposal_type=proposal_type,
                        mode=selected_mode,
                        prompt=prompt,
                        schema_hint=schema_hint or fallback_payload,
                        max_tokens=self.llm.max_tokens_for_mode(selected_mode),
                        reasoning_effort="minimal" if selected_mode == SupplementMode.FAST else "medium",
                        response_format={"type": "json_object"},
                        temperature=0.0,
                        system_msg=system_msg,
                        seed=llm_seed,
                    )
                    transcript = list(getattr(self.state, "llm_transcript", []) or [])
                    matching = next(
                        (
                            dict(item)
                            for item in transcript
                            if isinstance(item, Mapping)
                            and str(item.get("proposal_type", "")).strip() == proposal_type.value
                            and str(item.get("mode", "")).strip() == selected_mode.value
                            and str(item.get("request_digest", "")).strip() == request_digest
                        ),
                        None,
                    )
                    if matching is None:
                        raise RuntimeError(
                            f"LLM replay receipt not found for {proposal_type.value}/{selected_mode.value} ({request_digest})."
                        )
                    replay_payload = matching.get("payload")
                    result = LLMSupplementResult(
                        payload=dict(replay_payload) if isinstance(replay_payload, Mapping) else None,
                        source="replay",
                        provider=str(matching.get("provider") or self.llm.provider),
                        model=str(matching.get("model") or self.llm.model_for_mode(selected_mode) or ""),
                        raw_text=str(matching.get("raw_text") or ""),
                        receipt=matching,
                    )
                elif llm_strategy == "off":
                    result = LLMSupplementResult(
                        payload=None,
                        source="disabled",
                        provider=self.llm.provider,
                        model=self.llm.model_for_mode(selected_mode),
                    )
                else:
                    result = self.llm.propose_json(
                        proposal_type=proposal_type,
                        mode=selected_mode,
                        prompt=prompt,
                        schema_hint=schema_hint or fallback_payload,
                        seed=llm_seed,
                    )
                    if llm_strategy == "record" and result.receipt and isinstance(getattr(self.state, "llm_transcript", None), list):
                        self.state.llm_transcript.append(dict(result.receipt))
            except Exception as exc:
                if self.llm.policy == "required":
                    raise
                result = LLMSupplementResult(
                    payload=None,
                    source="heuristic",
                    provider=self.llm.provider,
                    model=self.llm.model_for_mode(selected_mode),
                    error=str(exc),
                )
        payload = dict(result.payload) if isinstance(result.payload, dict) else json_safe(fallback_payload)
        proposal = ProposalObject(
            id=make_id("proposal", proposal_type.value),
            proposal_type=proposal_type,
            target_scope=target_scope,
            originating_not_id=node.id if node is not None else None,
            mode=selected_mode,
            prompt_state_reference=self.build_prompt_state_reference(node),
            revision_count=self.state.next_proposal_revision(proposal_type, node.id if node is not None else None),
            governance_status=ProposalGovernanceStatus.SUGGESTED,
            payload=payload,
            source=result.source,
            provider=result.provider,
            model=result.model,
            rationale=payload.get("rationale", ""),
            raw_text=result.raw_text,
        )
        self.state.register_proposal(proposal)
        if result.error:
            self.state.record_step(
                kind="llm_fallback",
                node_id=node.id if node is not None else None,
                intent="Fall back cleanly when supplementation is unavailable or malformed.",
                action=f"fallback for {proposal_type.value}",
                result="heuristic proposal used",
                evaluation="governed continuation proceeded without giving authority to the supplement",
                payload={"proposal_id": proposal.id, "error": result.error},
            )
        return proposal

    def admit_proposal(self, proposal: ProposalObject, *, rationale: str) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with admitting proposal.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `admit_proposal(proposal=ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.'), rationale='The title is already minimally sufficient.')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal: Value for `proposal` used by `admit_proposal`. Expected type: `ProposalObject`.
            rationale: Value for `rationale` used by `admit_proposal`. Expected type: `str`.

        Returns:
            ProposalObject: Result produced by `admit_proposal`.
        """
        updated = self.state.set_proposal_status(
            proposal.id,
            ProposalGovernanceStatus.ADMITTED,
            rationale=rationale,
        )
        return updated or proposal

    def revise_proposal(self, proposal: ProposalObject, *, rationale: str) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with revising proposal.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `revise_proposal(proposal=ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.'), rationale='The title is already minimally sufficient.')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal: Value for `proposal` used by `revise_proposal`. Expected type: `ProposalObject`.
            rationale: Value for `rationale` used by `revise_proposal`. Expected type: `str`.

        Returns:
            ProposalObject: Result produced by `revise_proposal`.
        """
        updated = self.state.set_proposal_status(
            proposal.id,
            ProposalGovernanceStatus.REVISED,
            rationale=rationale,
        )
        return updated or proposal

    def reject_proposal(self, proposal: ProposalObject, *, rationale: str) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with rejecting proposal.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `reject_proposal(proposal=ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.'), rationale='The title is already minimally sufficient.')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposal: Value for `proposal` used by `reject_proposal`. Expected type: `ProposalObject`.
            rationale: Value for `rationale` used by `reject_proposal`. Expected type: `str`.

        Returns:
            ProposalObject: Result produced by `reject_proposal`.
        """
        updated = self.state.set_proposal_status(
            proposal.id,
            ProposalGovernanceStatus.REJECTED,
            rationale=rationale,
        )
        return updated or proposal

    def proposal_flag(self, payload: Mapping[str, Any], key: str, *, default: bool = False) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling proposal flag.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `proposal_flag(payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, key='force', default=True)`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            payload: Value for `payload` used by `proposal_flag`. Expected type: `Mapping[str, Any]`.
            key: Value for `key` used by `proposal_flag`. Expected type: `str`.
            default: Value for `default` used by `proposal_flag`. Expected type: `bool`. Defaults to `False`.

        Returns:
            bool: Result produced by `proposal_flag`.
        """
        value = payload.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "yes", "1"}:
                return True
            if lowered in {"false", "no", "0", ""}:
                return False
        return bool(value)

    def proposal_text(self, payload: Mapping[str, Any], key: str, *, default: str = "") -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling proposal text.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `proposal_text(payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, key='force', default='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            payload: Value for `payload` used by `proposal_text`. Expected type: `Mapping[str, Any]`.
            key: Value for `key` used by `proposal_text`. Expected type: `str`.
            default: Value for `default` used by `proposal_text`. Expected type: `str`. Defaults to `''`.

        Returns:
            str: Result produced by `proposal_text`.
        """
        value = payload.get(key, default)
        if value is None:
            return default
        return str(value).strip()

    def proposal_list(self, payload: Mapping[str, Any], key: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling proposal list.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `proposal_list(payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, key='force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            payload: Value for `payload` used by `proposal_list`. Expected type: `Mapping[str, Any]`.
            key: Value for `key` used by `proposal_list`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `proposal_list`.
        """
        value = payload.get(key, [])
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return []

    def proposal_mapping_list(self, payload: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling proposal mapping list.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `proposal_mapping_list(payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, key='force')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            payload: Value for `payload` used by `proposal_mapping_list`. Expected type: `Mapping[str, Any]`.
            key: Value for `key` used by `proposal_mapping_list`. Expected type: `str`.

        Returns:
            list[dict[str, Any]]: Result produced by `proposal_mapping_list`.
        """
        value = payload.get(key, [])
        if not isinstance(value, list):
            return []
        return [dict(item) for item in value if isinstance(item, Mapping)]

    def can_reframe_within_decomposition(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether reframe within decomposition.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `can_reframe_within_decomposition(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `can_reframe_within_decomposition`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `can_reframe_within_decomposition`.
        """
        return bool(node.parent_id and node.parent_id in self.state.graph.nodes)

    def structural_can_decompose(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with checking structural can decompose.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `structural_can_decompose(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `structural_can_decompose`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `structural_can_decompose`.
        """
        if node.depth >= self.state.governance.max_depth:
            return False
        if len(self.state.graph.nodes) >= self.state.governance.max_nodes:
            return False
        if node.role in {"framing", "governance", "closure", "direct_support", "upstream_support"}:
            return False
        return True

    def structural_direct_refinement_supported(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether direct refinement is structurally supported.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `structural_direct_refinement_supported(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `structural_direct_refinement_supported`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `structural_direct_refinement_supported`.
        """
        if node.role in {"root", "framing", "governance", "closure"}:
            return True
        if node.role == "direct_support":
            return bool(self.direct_support_items(node))
        if node.role == "upstream_support":
            return bool(self.upstream_support_items(node))
        if node.role == "generic":
            return bool(self.direct_support_items(node) or self.upstream_support_items(node))
        return False

    def fallback_pause_reason(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with describing the reason for fallback pause.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_pause_reason(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_pause_reason`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `fallback_pause_reason`.
        """
        blockers = self.state.blockers.get(node.id, [])
        if any(blocker.startswith("missing_evidence:") for blocker in blockers):
            return "wait for missing evidence or outside input before continuing"
        if any(blocker.startswith("governance_violation:") for blocker in blockers):
            return "wait until the blocking governance issue is resolved"
        if any(self.state.node_status(child.id) == NodeStatus.PAUSED for child in self.refinement_children(node)):
            return "wait for a paused subtask to resolve first"
        return "wait until the current blockers are resolved"

    def fallback_pause_boundary(self, node: SemanticNode) -> tuple[PauseBoundary, bool]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback pause boundary.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `fallback_pause_boundary(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_pause_boundary`. Expected type: `SemanticNode`.

        Returns:
            tuple[PauseBoundary, bool]: Result produced by `fallback_pause_boundary`.
        """
        existing_pause = next((pause for pause in self.state.pause_points.values() if pause.node_id == node.id), None)
        if existing_pause is not None:
            return (
                existing_pause.required_boundary,
                existing_pause.required_boundary == PauseBoundary.EVIDENCE_ATTACHMENT,
            )

        blockers = self.state.blockers.get(node.id, [])
        if any(blocker.startswith("missing_evidence:") for blocker in blockers):
            return PauseBoundary.EVIDENCE_ATTACHMENT, True
        return PauseBoundary.RESUME_SIGNAL, False

    def fallback_control_decision(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback control decision.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_control_decision(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_control_decision`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_control_decision`.
        """
        children = self.refinement_children(node)
        open_children = [child for child in children if self.state.node_status(child.id) == NodeStatus.OPEN]
        paused_children = [child for child in children if self.state.node_status(child.id) == NodeStatus.PAUSED]
        blockers = list(self.state.blockers.get(node.id, []))
        structural_decompose = self.structural_can_decompose(node)
        direct_supported = self.structural_direct_refinement_supported(node)
        structured_learning = node.metadata.get("structured_learning", {})
        if not isinstance(structured_learning, Mapping):
            structured_learning = self.ensure_not_elaboration(node)
        directive = semantic_prompt_directive_profile(node.semantic_unit)
        directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
        requires_chain = bool(directive.get("requires_chain", False))
        inferred_chain_components = (
            semantic_chain_decomposition_components(node.semantic_unit)
            if node.role == "root" and directive_kind in {"construct", "derive"} and requires_chain
            else []
        )
        fallback_chain_components = (
            self.fallback_construct_chain_components(node.semantic_unit)
            if node.role == "root" and directive_kind in {"construct", "derive"} and requires_chain
            else []
        )
        preserve_construct_chain_prompt_surface = (
            node.role == "root"
            and directive_kind == "construct"
            and requires_chain
            and self.should_preserve_construct_chain_prompt_surface(node.semantic_unit)
        )
        explicit_split_request = bool(
            re.search(
                r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
                str(node.semantic_unit or ""),
                flags=re.IGNORECASE,
            )
        )
        component_count = len(
            [item for item in structured_learning.get("component_nots", []) if str(item).strip()]
        )
        component_count = max(component_count, len(fallback_chain_components))
        requested_output_count = len(semantic_requested_output_phrases(node.semantic_unit))
        body_split_needed = bool(structured_learning.get("title_depth_body_split_needed", False))
        example_component_requested = any(
            re.search(r"\bgive\b.*\bexample\b", str(item), flags=re.IGNORECASE)
            for item in structured_learning.get("component_nots", [])
            if str(item).strip()
        ) if isinstance(structured_learning.get("component_nots", []), list) else False
        structured_lookup = node.metadata.get("structured_learning_lookup", {})
        lookup_match_kind = (
            collapse_ws(str(structured_lookup.get("match_kind", "")).strip())
            if isinstance(structured_lookup, Mapping)
            else ""
        )
        should_pause = False
        pause_reason = ""
        required_boundary = PauseBoundary.RESUME_SIGNAL
        needs_retrieval = False

        if node.id in self.state.paused:
            should_pause = True
            pause_reason = "work on this item is already paused"
            required_boundary, needs_retrieval = self.fallback_pause_boundary(node)
        elif self.is_closed(node) or self.is_committable(node):
            should_pause = False
        elif structural_decompose and not children:
            should_pause = False
        elif open_children:
            should_pause = False
        elif node.decomposition_mode == "OR" and any(self.child_is_satisfied(child) for child in children):
            should_pause = False
        elif paused_children or blockers:
            should_pause = True
            pause_reason = self.fallback_pause_reason(node)
            required_boundary, needs_retrieval = self.fallback_pause_boundary(node)

        needs_reframe = bool(node.metadata.get("force_reframe")) and self.can_reframe_within_decomposition(node)
        root_requires_decomposition = (
            node.role == "root"
            and structural_decompose
            and not children
            and not preserve_construct_chain_prompt_surface
            and (component_count >= 2 or requested_output_count >= 2 or body_split_needed)
            and not node.metadata.get("direct_resolution_ready_for_commitment")
            and (
                body_split_needed
                or (requires_chain and len(inferred_chain_components) >= 2)
                or (directive_kind == "state" and component_count >= 2 and example_component_requested)
                or (
                    directive_kind in {"derive", "distinguish"}
                    or (
                        directive_kind == "construct"
                        and (
                            body_split_needed
                            or len(inferred_chain_components) >= 2
                            or len(fallback_chain_components) >= 2
                        )
                    )
                )
                or explicit_split_request
                or lookup_match_kind in {"composition_related", "decomposition_related"}
            )
        )
        should_decompose = structural_decompose and not children and (
            node.role == "support" or root_requires_decomposition
        )
        can_refine_directly = direct_supported and not should_decompose

        return {
            "should_pause": should_pause,
            "pause_reason": pause_reason if should_pause else "",
            "required_boundary": required_boundary if should_pause else PauseBoundary.RESUME_SIGNAL,
            "needs_retrieval": needs_retrieval if should_pause else False,
            "needs_reframe": needs_reframe,
            "reframe_reason": "the current wording has already been marked for reframing" if needs_reframe else "",
            "should_decompose": should_decompose,
            "can_refine_directly": can_refine_directly,
            "suggested_focus": blockers[0] if blockers else node.semantic_unit,
            "rationale": "Fallback control decision mirrors the current structural state conservatively.",
        }

    def control_decision_cache_key(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling control decision cache key.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `control_decision_cache_key(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `control_decision_cache_key`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `control_decision_cache_key`.
        """
        snapshot = {
            "visit_count": self.state.visit_counts.get(node.id, 0),
            "status": self.state.node_status(node.id).value,
            "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
            "blockers": sorted(self.state.blockers.get(node.id, [])),
            "children": [
                {
                    "id": child.id,
                    "status": self.state.node_status(child.id).value,
                    "role": child.role,
                }
                for child in self.refinement_children(node)
            ],
            "direct_support_count": len(self.direct_support_items(node)),
            "upstream_support_count": len(self.upstream_support_items(node)),
        }
        return json.dumps(snapshot, sort_keys=True)

    def propose_control_decision(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing control decision.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_control_decision(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_control_decision`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_control_decision`.
        """
        cache_key = self.control_decision_cache_key(node)
        cached_id = node.metadata.get("control_decision_proposal_id")
        if (
            isinstance(cached_id, str)
            and cached_id in self.state.proposals
            and node.metadata.get("control_decision_cache_key") == cache_key
        ):
            return self.state.proposals[cached_id]

        proposal = self.request_proposal(
            proposal_type=ProposalType.CONTROL_DECISION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Make a quick judgment for the active item.
                Do not solve the task itself. Decide how we should proceed next.

                Field guidance:
                - should_pause: true only if work should stop for now instead of continuing immediately.
                - pause_reason: a short reason for pausing. Leave empty if should_pause is false.
                - required_boundary: one of resume_signal, evidence_attachment, human_contribution, or capability_emergence.
                - needs_retrieval: true only if continuation depends on outside supporting material being gathered.
                - needs_reframe: true only if the current wording or scope is poor enough that it should be rewritten before more work.
                - reframe_reason: a short reason for reframing. Leave empty if needs_reframe is false.
                - should_decompose: true only if breaking the item into smaller parts is still useful right now.
                - can_refine_directly: true only if the item can be worked on directly with the information already available and the current workflow has a direct path for that.
                - suggested_focus: name the most important part to focus on next.

                Guidance for trivial or clear tasks:
                - If the item is already clear, do not ask for reframing.
                - If the item is small and self-contained, prefer direct work over decomposition when the current workflow supports it.
                - Only pause when there is a real dependency, missing support, or a reason not to continue safely.
                - If should_pause is true, choose the required boundary explicitly instead of describing it indirectly.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload=self.fallback_control_decision(node),
            mode=SupplementMode.FAST,
        )
        node.metadata["control_decision_proposal_id"] = proposal.id
        node.metadata["control_decision_cache_key"] = cache_key
        node.metadata["control_decision"] = json_safe(proposal.payload)
        self.admit_proposal(
            proposal,
            rationale="Control decisions are advisory workflow judgments and may guide fast local control without becoming commitments.",
        )
        return proposal

    def control_decision_payload(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for control decision.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `control_decision_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `control_decision_payload`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `control_decision_payload`.
        """
        return dict(self.propose_control_decision(node).payload)

    def evidence_effectiveness_level(self, evidence: Evidence) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling evidence effectiveness level.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `evidence_effectiveness_level(evidence=Evidence(statement='F = m * a'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence: Value for `evidence` used by `evidence_effectiveness_level`. Expected type: `Evidence`.

        Returns:
            ThreeLevel: Result produced by `evidence_effectiveness_level`.
        """
        return min_level(
            [
                normalize_three_level(evidence.support_effect, default=ThreeLevel.MEDIUM),
                normalize_three_level(evidence.confidence, default=ThreeLevel.MEDIUM),
                self.SOURCE_RELIABILITY.get(evidence.source, ThreeLevel.MEDIUM),
            ],
            default=ThreeLevel.MEDIUM,
        )

    def strongest_support_level_from_items(self, evidence_ids: Iterable[str]) -> tuple[ThreeLevel, bool]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling strongest support level from items.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `strongest_support_level_from_items(evidence_ids=['mass', 'acceleration', 'force'])`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence_ids: Value for `evidence_ids` used by `strongest_support_level_from_items`. Expected type: `Iterable[str]`.

        Returns:
            tuple[ThreeLevel, bool]: Result produced by `strongest_support_level_from_items`.
        """
        levels: list[ThreeLevel] = []
        any_support = False
        for evidence_id in evidence_ids:
            evidence = self.state.evidence.get(evidence_id)
            if evidence is None or evidence.polarity != EvidencePolarity.SUPPORT:
                continue
            any_support = True
            levels.append(self.evidence_effectiveness_level(evidence))
        return max_level(levels, default=ThreeLevel.LOW), any_support

    def strongest_counter_level_from_items(self, evidence_ids: Iterable[str]) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling strongest counter level from items.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `strongest_counter_level_from_items(evidence_ids=['mass', 'acceleration', 'force'])`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence_ids: Value for `evidence_ids` used by `strongest_counter_level_from_items`. Expected type: `Iterable[str]`.

        Returns:
            ThreeLevel: Result produced by `strongest_counter_level_from_items`.
        """
        levels: list[ThreeLevel] = []
        for evidence_id in evidence_ids:
            evidence = self.state.evidence.get(evidence_id)
            if evidence is None or evidence.polarity != EvidencePolarity.COUNTER:
                continue
            levels.append(self.evidence_effectiveness_level(evidence))
        return max_level(levels, default=ThreeLevel.LOW)

    def support_score_label(self, strength: ThreeLevel | str, *, has_any_support: bool) -> SupportScore:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling support score label.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `support_score_label(strength='force', has_any_support=True)`
            Output: 0.75

        Args:
            self: Bound instance that owns the runtime state used by this method.
            strength: Value for `strength` used by `support_score_label`. Expected type: `ThreeLevel | str`.
            has_any_support: Value for `has_any_support` used by `support_score_label`. Expected type: `bool`.

        Returns:
            SupportScore: Result produced by `support_score_label`.
        """
        normalized = normalize_three_level(strength, default=ThreeLevel.LOW)
        if normalized == ThreeLevel.HIGH:
            return SupportScore.OK
        if has_any_support:
            return SupportScore.BAD
        return SupportScore.VERY_BAD

    def support_score_is_sufficient(self, score: SupportScore | str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling support score is sufficient.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `support_score_is_sufficient(score='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            score: Value for `score` used by `support_score_is_sufficient`. Expected type: `SupportScore | str`.

        Returns:
            bool: Result produced by `support_score_is_sufficient`.
        """
        return normalize_support_score(score) == SupportScore.OK

    def heuristic_support_view(self, node: SemanticNode) -> SupportScore:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building a view of heuristic support.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_support_view(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_support_view`. Expected type: `SemanticNode`.

        Returns:
            SupportScore: Result produced by `heuristic_support_view`.
        """
        if node.metadata.get("direct_resolution_ready_for_commitment") and self.direct_support_items(node):
            return SupportScore.OK
        children = self.refinement_children(node)
        if children:
            if node.decomposition_mode == "AND":
                child_condition = all(self.child_is_satisfied(child) for child in children if child.required)
            elif node.decomposition_mode == "OR":
                child_condition = any(self.child_is_satisfied(child) for child in children)
            else:
                child_condition = any(self.child_is_satisfied(child) for child in children)
        else:
            child_condition = False

        if child_condition:
            return SupportScore.OK
        direct_level, has_direct = self.strongest_support_level_from_items(self.direct_support_items(node))
        upstream_level, has_upstream = self.strongest_support_level_from_items(self.upstream_support_items(node))
        strongest = max_level([direct_level, upstream_level], default=ThreeLevel.LOW)
        return self.support_score_label(strongest, has_any_support=has_direct or has_upstream)

    def counter_evidence_level(self, node: SemanticNode) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling counter evidence level.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `counter_evidence_level(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `counter_evidence_level`. Expected type: `SemanticNode`.

        Returns:
            ThreeLevel: Result produced by `counter_evidence_level`.
        """
        relevant_ids = self.direct_support_items(node) + self.upstream_support_items(node)
        return self.strongest_counter_level_from_items(relevant_ids)

    def certainty_satisfies_rule(self, certainty: ThreeLevel | str, closure_rule: ClosureRule | str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling certainty satisfies rule.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `certainty_satisfies_rule(certainty='force', closure_rule='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            certainty: Value for `certainty` used by `certainty_satisfies_rule`. Expected type: `ThreeLevel | str`.
            closure_rule: Value for `closure_rule` used by `certainty_satisfies_rule`. Expected type: `ClosureRule | str`.

        Returns:
            bool: Result produced by `certainty_satisfies_rule`.
        """
        normalized_rule = normalize_closure_rule(closure_rule, default=ClosureRule.NORMAL)
        normalized_certainty = normalize_three_level(certainty, default=ThreeLevel.LOW)
        if normalized_rule == ClosureRule.LIGHT:
            return level_at_least(normalized_certainty, ThreeLevel.MEDIUM)
        return normalized_certainty == ThreeLevel.HIGH

    def heuristic_certainty(self, node: SemanticNode) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling heuristic certainty.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_certainty(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_certainty`. Expected type: `SemanticNode`.

        Returns:
            ThreeLevel: Result produced by `heuristic_certainty`.
        """
        support_score = self.heuristic_support_view(node)
        children = self.refinement_children(node)
        blockers = self.state.blockers.get(node.id, [])
        conflicts = self.state.conflicts.get(node.id, [])

        if conflicts:
            return ThreeLevel.LOW
        if node.metadata.get("direct_resolution_ready_for_commitment") and self.support_score_is_sufficient(support_score):
            return ThreeLevel.HIGH
        if children:
            required_children = [child for child in children if child.required]
            satisfied_required = all(self.child_is_satisfied(child) for child in required_children) if required_children else False
            any_satisfied = any(self.child_is_satisfied(child) for child in children)
            if node.decomposition_mode == DecompositionMode.AND and satisfied_required and support_score != SupportScore.VERY_BAD and not blockers:
                return ThreeLevel.HIGH
            if node.decomposition_mode == DecompositionMode.OR and any_satisfied and support_score != SupportScore.VERY_BAD and not blockers:
                return ThreeLevel.HIGH
            if any_satisfied or support_score in {SupportScore.BAD, SupportScore.OK}:
                return ThreeLevel.MEDIUM
            return ThreeLevel.LOW
        if blockers:
            return ThreeLevel.MEDIUM if support_score == SupportScore.OK else ThreeLevel.LOW
        if support_score == SupportScore.OK:
            return ThreeLevel.HIGH
        if support_score == SupportScore.BAD:
            return ThreeLevel.MEDIUM
        return ThreeLevel.LOW

    def heuristic_should_reflect(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling heuristic should reflect.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_should_reflect(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_should_reflect`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `heuristic_should_reflect`.
        """
        if node.role == "root":
            return True
        children = self.refinement_children(node)
        if not children:
            return bool(self.state.blockers.get(node.id) or self.state.conflicts.get(node.id))
        child_statuses = {self.state.node_status(child.id).value for child in children}
        return len(child_statuses) > 1 or bool(self.state.blockers.get(node.id))

    def heuristic_governance_violation(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling heuristic governance violation.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_governance_violation(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_governance_violation`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `heuristic_governance_violation`.
        """
        if node.depth > self.state.governance.max_depth:
            return True
        if len(self.state.graph.nodes) > self.state.governance.max_nodes:
            return True
        faithfulness = normalize_three_level(node.metadata.get("faithfulness", ThreeLevel.HIGH), default=ThreeLevel.HIGH)
        if not level_at_least(faithfulness, self.state.governance.faithfulness_requirement) and node.role != "root":
            return True
        return False

    def heuristic_conflict_descriptions(self, node: SemanticNode) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling heuristic conflict descriptions.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_conflict_descriptions(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_conflict_descriptions`. Expected type: `SemanticNode`.

        Returns:
            list[str]: Result produced by `heuristic_conflict_descriptions`.
        """
        conflicts = []
        for other in self.incompatible_neighbors(node):
            if self.simultaneously_asserted(node, other):
                conflicts.append(f"{node.id}:{other.id}")
        certainty = self.heuristic_certainty(node)
        support_score = self.heuristic_support_view(node)
        counter_level = self.counter_evidence_level(node)
        if certainty == ThreeLevel.HIGH and (
            (support_score != SupportScore.OK and level_at_least(counter_level, ThreeLevel.MEDIUM))
            or counter_level == ThreeLevel.HIGH
        ):
            conflicts.append(f"{node.id}:evidence_conflict")
        return sorted(set(conflicts))

    def heuristic_ready_for_commitment(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling heuristic ready for commitment.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `heuristic_ready_for_commitment(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `heuristic_ready_for_commitment`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `heuristic_ready_for_commitment`.
        """
        if self.heuristic_governance_violation(node):
            return False
        if self.state.conflicts.get(node.id):
            return False
        if self.state.blockers.get(node.id):
            return False
        if not self.certainty_satisfies_rule(self.heuristic_certainty(node), node.closure_threshold):
            return False
        children = self.refinement_children(node)
        if not children:
            return self.support_score_is_sufficient(self.heuristic_support_view(node))
        if node.decomposition_mode == "AND":
            if not all(self.child_is_satisfied(child) for child in children if child.required):
                return False
        elif node.decomposition_mode == "OR":
            if not any(self.child_is_satisfied(child) for child in children):
                return False
        return self.support_score_is_sufficient(self.heuristic_support_view(node))

    def fallback_node_assessment(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback node assessment.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_node_assessment(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_node_assessment`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_node_assessment`.
        """
        support_score = self.heuristic_support_view(node)
        governance_violation = self.heuristic_governance_violation(node)
        conflicts = self.heuristic_conflict_descriptions(node)
        direct_resolution_ready = bool(node.metadata.get("direct_resolution_ready_for_commitment")) and self.support_score_is_sufficient(support_score)
        return {
            "support_score": support_score,
            "certainty": self.heuristic_certainty(node),
            "ready_for_commitment": direct_resolution_ready or self.heuristic_ready_for_commitment(node),
            "should_reflect": self.heuristic_should_reflect(node),
            "governance_violation": governance_violation,
            "governance_concerns": ["local governance heuristics marked a violation"] if governance_violation else [],
            "conflict_descriptions": conflicts,
            "rationale": "Fallback node assessment mirrors the controller's current heuristic view.",
        }

    def node_assessment_cache_key(self, node: SemanticNode) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling node assessment cache key.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `node_assessment_cache_key(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `node_assessment_cache_key`. Expected type: `SemanticNode`.

        Returns:
            str: Result produced by `node_assessment_cache_key`.
        """
        support = self.state.support.get(node.id, SupportView([], [], SupportScore.VERY_BAD))
        evidence_summary = []
        for evidence_id in sorted(self.direct_support_items(node) + self.upstream_support_items(node)):
            evidence = self.state.evidence.get(evidence_id)
            if evidence is None:
                continue
            evidence_summary.append(
                {
                    "id": evidence.id,
                    "source": evidence.source,
                    "polarity": evidence.polarity,
                    "confidence": evidence.confidence,
                    "support_strength": evidence.support_effect,
                }
            )
        snapshot = {
            "node_id": node.id,
            "role": node.role,
            "depth": node.depth,
            "status": self.state.node_status(node.id).value,
            "decomposition_mode": node.decomposition_mode,
            "required": node.required,
            "evidence_required": node.evidence_required,
            "priority": node.priority_bias,
            "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
            "faithfulness": str(node.metadata.get("faithfulness", "low")),
            "blockers": sorted(self.state.blockers.get(node.id, [])),
            "conflicts": sorted(self.state.conflicts.get(node.id, [])),
            "support": {
                "support_score": support.score,
            },
            "pause_boundaries": sorted(
                pause.required_boundary
                for pause in self.state.pause_points.values()
                if pause.node_id == node.id
            ),
            "visit_count": self.state.visit_counts.get(node.id, 0),
            "children": self.child_context_payload(node),
            "evidence": evidence_summary,
        }
        return json.dumps(snapshot, sort_keys=True)

    def propose_node_assessment(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing node assessment.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_node_assessment(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_node_assessment`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_node_assessment`.
        """
        cache_key = self.node_assessment_cache_key(node)
        cached_id = node.metadata.get("node_assessment_proposal_id")
        if (
            isinstance(cached_id, str)
            and cached_id in self.state.proposals
            and node.metadata.get("node_assessment_cache_key") == cache_key
        ):
            return self.state.proposals[cached_id]

        proposal = self.request_proposal(
            proposal_type=ProposalType.NODE_ASSESSMENT,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Assess the active item. Do not solve the task.

                Field guidance:
                - support_score: one of very_bad, bad, or ok.
                - certainty: one of low, medium, or high.
                - ready_for_commitment: true only if the item is ready to be closed under current support and structure.
                - should_reflect: true only if this item now needs an explicit progress review.
                - governance_violation: true only if the current state should be treated as governance-breaking.
                - governance_concerns: list concrete governance concerns.
                - conflict_descriptions: list contradictions, incompatibilities, or support conflicts that matter now.

                Rules:
                - Base the assessment on the current structure, support, conflicts, and blockers.
                - Use ordinary judgment rather than fixed numeric formulas.
                - Use very_bad when support is weak or missing, bad when it exists but is not enough, and ok when it is in good shape.
                - Do not invent support or conflicts that are not grounded in the state snapshot.
                - Decide should_reflect by explicitly examining the current children, especially drift, disagreement, stalled progress, or uneven child status.
                - If there are no children, do not recommend reflection unless the node itself is materially unstable.

                Active item:
                {node.semantic_unit}

                Current children:
                {json.dumps(self.child_context_payload(node), indent=2, sort_keys=True)}
                """
            ),
            fallback_payload=self.fallback_node_assessment(node),
            mode=SupplementMode.FAST,
        )
        node.metadata["node_assessment_proposal_id"] = proposal.id
        node.metadata["node_assessment_cache_key"] = cache_key
        self.admit_proposal(
            proposal,
            rationale="Node assessments may guide support assessment and judgment while closure authority remains separate.",
        )
        return proposal

    def node_assessment_payload(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for node assessment.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `node_assessment_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `node_assessment_payload`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `node_assessment_payload`.
        """
        return dict(self.propose_node_assessment(node).payload)

    def candidate_brief(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling candidate brief.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `candidate_brief(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `candidate_brief`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `candidate_brief`.
        """
        return {
            "id": node.id,
            "semantic_unit": node.semantic_unit,
            "role": node.role,
            "status": self.state.node_status(node.id).value,
            "depth": node.depth,
            "required": node.required,
            "blockers": list(self.state.blockers.get(node.id, [])),
            "conflicts": list(self.state.conflicts.get(node.id, [])),
            "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
        }

    def normalize_candidate_order(
        self,
        candidates: list[SemanticNode],
        ordered_ids: Iterable[str] | None = None,
    ) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with normalizing candidate order.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `normalize_candidate_order(candidates=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], ordered_ids=['mass', 'acceleration', 'force'])`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            candidates: Value for `candidates` used by `normalize_candidate_order`. Expected type: `list[SemanticNode]`.
            ordered_ids: Value for `ordered_ids` used by `normalize_candidate_order`. Expected type: `Iterable[str] | None`. Defaults to `None`.

        Returns:
            list[SemanticNode]: Result produced by `normalize_candidate_order`.
        """
        lookup = {candidate.id: candidate for candidate in candidates}
        ordered: list[SemanticNode] = []
        seen: set[str] = set()
        for candidate_id in ordered_ids or []:
            if candidate_id in lookup and candidate_id not in seen:
                ordered.append(lookup[candidate_id])
                seen.add(candidate_id)
        for candidate in candidates:
            if candidate.id not in seen:
                ordered.append(candidate)
        return ordered

    def propose_candidate_selection(
        self,
        *,
        context_node: SemanticNode,
        candidates: list[SemanticNode],
        selection_kind: str,
    ) -> ProposalObject | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing candidate selection.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_candidate_selection(context_node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), candidates=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], selection_kind='force')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            context_node: Value for `context_node` used by `propose_candidate_selection`. Expected type: `SemanticNode`.
            candidates: Value for `candidates` used by `propose_candidate_selection`. Expected type: `list[SemanticNode]`.
            selection_kind: Value for `selection_kind` used by `propose_candidate_selection`. Expected type: `str`.

        Returns:
            ProposalObject | None: Result produced by `propose_candidate_selection`.
        """
        if not candidates:
            return None

        candidate_payload = [self.candidate_brief(candidate) for candidate in candidates]
        fallback_payload = {
            "selected_candidate_id": candidates[0].id,
            "ordered_candidate_ids": [candidate.id for candidate in candidates],
            "rationale": "Fallback candidate choice preserves the current candidate order.",
        }
        proposal = self.request_proposal(
            proposal_type=ProposalType.CANDIDATE_SELECTION,
            node=context_node,
            target_scope=selection_kind,
            instructions=plain_prompt(
                f"""
                Choose which candidate should be worked first in this {selection_kind}.
                Use only the candidates provided. Do not invent new ids.

                Field guidance:
                - selected_candidate_id: the single best candidate to work first.
                - ordered_candidate_ids: the candidate ids in the preferred working order.
                - rationale: short explanation tied to the parent context and candidate differences.

                Rules:
                - Every id in ordered_candidate_ids must come from the provided candidate list.
                - Preserve the parent context; do not choose based on unrelated considerations.
                - Prefer the candidate that most directly advances the current parent context.

                Parent context:
                {context_node.semantic_unit}

                Candidates:
                {json.dumps(candidate_payload, indent=2, sort_keys=True)}
                """
            ),
            fallback_payload=fallback_payload,
            mode=SupplementMode.FAST,
        )
        context_node.metadata.setdefault("candidate_selection_proposal_ids", []).append(proposal.id)
        self.admit_proposal(
            proposal,
            rationale="Candidate-choice proposals may guide work ordering without becoming commitments.",
        )
        return proposal

    def infer_target_kind(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with inferring target kind.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `infer_target_kind(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `infer_target_kind`. Expected type: `str`.

        Returns:
            str: Result produced by `infer_target_kind`.
        """
        lowered = text.lower()
        if self._canonical_direct_resolution(text) is not None:
            return "bounded"
        if any(token in lowered for token in {"explain", "analyze", "summarize"}):
            return "analytic"
        if any(token in lowered for token in {"build", "create", "design", "implement"}):
            return "constructive"
        if any(token in lowered for token in {"find", "verify", "lookup", "retrieve"}):
            return "factual"
        return "general"

    def initialize_root_semantics(self) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling initialize root semantics.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `initialize_root_semantics()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        root = self.state.root()
        if root.metadata.get("semantic_target_initialized"):
            self.ensure_not_elaboration(root)
            return
        if self.prepare_root_prior_learning_fast_path():
            self.ensure_not_elaboration(root)
            return

        semantic_target = self.request_proposal(
            proposal_type=ProposalType.SEMANTIC_TARGET,
            node=root,
            target_scope=root.semantic_unit,
            instructions=plain_prompt(
                f"""
                Clarify what the user is actually asking for. Do not solve the task; unless it's trivial question.
                Fill the JSON fields with concrete, plain-language content.

                Field guidance:
                - target_kind: choose the best fit such as analytic, constructive, factual, or general.
                - goal_statement: one clear sentence stating the desired outcome.
                - scope_candidates: 2 to 5 concrete things that should be considered part of the task.
                - exclusions: things that should not be treated as part of the task.
                - ambiguity_notes: missing details, alternate readings, or assumptions that may matter.
                - alternate_semantic_framings: alternate but still plausible ways to phrase the same request.
                - boundary_shape: a list using only a*, a'*, b*, b'*, c*, c'*, d*, d'* to describe the current boundary shape of this Not.
                - In that notation, * means one or more occurrences of the lane kind, not zero-or-more.

                Additional guidance:
                - If the request is a trivial self-contained question, do not invent ambiguity just to avoid a direct answer.
                - In that case, make the goal_statement describe answering it directly and briefly.

                Focus on this task:
                {root.semantic_unit}
                """
            ),
            fallback_payload={
                "target_kind": self.infer_target_kind(root.semantic_unit),
                "goal_statement": root.semantic_unit,
                "scope_candidates": [root.semantic_unit],
                "exclusions": [],
                "ambiguity_notes": [],
                "alternate_semantic_framings": [],
                "boundary_shape": list(root.boundary_shape),
                "rationale": "Fallback task clarification keeps the original request as the working goal.",
            },
            mode=self.select_supplement_mode("semantic_target", root),
        )
        root.metadata["semantic_target_proposal_id"] = semantic_target.id
        root.metadata["semantic_target"] = semantic_target.payload
        root.description = str(semantic_target.payload.get("goal_statement") or root.description)
        root.boundary_shape = normalize_boundary_shape(
            semantic_target.payload.get("boundary_shape"),
            default=root.boundary_shape,
        )
        self.state.sync_not_ontology_entry(root)
        self.admit_proposal(
            semantic_target,
            rationale="Semantic target proposals may be admitted as working framing artifacts without affecting certainty.",
        )

        root.metadata["semantic_target_initialized"] = True
        self.ensure_not_elaboration(root)

    def propose_next_action(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing next action.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_next_action(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_next_action`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_next_action`.
        """
        control = self.control_decision_payload(node)
        fallback_action = "commit_closure" if self.is_committable(node) else "decompose"
        if self.proposal_flag(control, "should_pause"):
            fallback_action = "holdon"
        elif self.proposal_flag(control, "needs_reframe"):
            fallback_action = "reframe"
        elif self.proposal_flag(control, "can_refine_directly") and self.structural_direct_refinement_supported(node):
            fallback_action = "refine_directly"
        elif not self.proposal_flag(control, "should_decompose", default=self.structural_can_decompose(node)):
            fallback_action = "contemplate"

        proposal = self.request_proposal(
            proposal_type=ProposalType.NEXT_ACTION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Choose the single best next step for the active item.
                Use the exact token for action_kind.

                Allowed action_kind values:
                - decompose: split the work into smaller parts
                - retrieve: gather missing evidence, source material, or outside input
                - refine_directly: work directly on the item using what is already available
                - contemplate: compare plausible paths before acting
                - reframe: rewrite the problem statement because the current framing is poor
                - holdon: pause and wait because progress would be premature
                - escalate: push the issue upward for a broader decision

                Field guidance:
                - reason: tie the choice to the current status, blockers, and confidence.
                - focus: name the exact part that should be worked on next.
                - needs: list missing inputs, evidence, or dependencies.
                - stop_conditions: say when the system should reassess.
                - alternates: include 1 to 3 backup actions.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "action_kind": fallback_action,
                "reason": "Fallback next step follows the current controller heuristics.",
                "focus": node.semantic_unit,
                "needs": list(self.state.blockers.get(node.id, [])),
                "stop_conditions": ["reassess after propagation"],
                "alternates": ["mark_incomplete"],
                "rationale": "Fallback next-step guidance stays conservative and reversible.",
            },
            mode=self.select_supplement_mode("next_action", node),
        )
        node.metadata["next_action_proposal_id"] = proposal.id
        return proposal

    def _normalize_entity_text(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with normalizing entity text.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_normalize_entity_text(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_normalize_entity_text`. Expected type: `str`.

        Returns:
            str: Result produced by `_normalize_entity_text`.
        """
        return re.sub(r"[^a-z ]+", " ", text.lower()).strip()

    def _canonical_arithmetic(self, text: str) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling canonical arithmetic.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_canonical_arithmetic(text='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_canonical_arithmetic`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `_canonical_arithmetic`.
        """
        compact = text.strip()
        expr_match = re.search(r"(?<![A-Za-z0-9_])(-?\d+)\s*([+\-*/])\s*(-?\d+)(?![A-Za-z0-9_])", compact)
        if expr_match:
            left = int(expr_match.group(1))
            op = expr_match.group(2)
            right = int(expr_match.group(3))
            if op == '+':
                value = left + right
            elif op == '-':
                value = left - right
            elif op == '*':
                value = left * right
            else:
                if right == 0:
                    return None
                value = left / right
            return {
                "answer": str(int(value) if isinstance(value, float) and value.is_integer() else value),
                "justification": f"Canonical arithmetic form evaluated exactly: {left} {op} {right}.",
                "answer_kind": "arithmetic",
            }
        lowered = compact.lower()
        verbal = re.search(r"\badd\s+(-?\d+)\s+(?:and|to)\s+(-?\d+)\b", lowered)
        if verbal:
            left, right = int(verbal.group(1)), int(verbal.group(2))
            return {
                "answer": str(left + right),
                "justification": f"Canonical arithmetic form extracted from verbal addition: {left} + {right}.",
                "answer_kind": "arithmetic",
            }
        return None

    def _canonical_syllogism(self, text: str) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling canonical syllogism.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_canonical_syllogism(text='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_canonical_syllogism`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `_canonical_syllogism`.
        """
        premises = re.findall(r"all\s+([a-zA-Z ]+?)\s+are\s+([a-zA-Z ]+?)[.?!]", text, flags=re.IGNORECASE)
        question = re.search(r"are\s+([a-zA-Z ]+?)\s+([a-zA-Z ]+?)\?", text, flags=re.IGNORECASE)
        if len(premises) < 2 or not question:
            return None
        relations = [(self._normalize_entity_text(a), self._normalize_entity_text(b)) for a,b in premises]
        subj = self._normalize_entity_text(question.group(1))
        pred = self._normalize_entity_text(question.group(2))
        reachable = {subj}
        changed = True
        while changed:
            changed = False
            for a,b in relations:
                if a in reachable and b not in reachable:
                    reachable.add(b)
                    changed = True
        if pred in reachable:
            subject_phrase = question.group(1).strip()
            predicate_phrase = question.group(2).strip()
            return {
                "answer": f"Yes, {subject_phrase} are {predicate_phrase}.",
                "justification": "Canonical syllogism closure by transitive subset relation over universal premises.",
                "answer_kind": "logical_entailment",
            }
        return None

    def _canonical_passive_rewrite(self, text: str) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling canonical passive rewrite.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_canonical_passive_rewrite(text='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_canonical_passive_rewrite`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `_canonical_passive_rewrite`.
        """
        m = re.search(r'(?:rewrite|turn)\s+"([^"]+)"\s+(?:in|into)\s+passive voice', text, flags=re.IGNORECASE)
        if not m:
            return None
        sentence = m.group(1).strip().rstrip('.!?')
        m2 = re.match(r'(?i)the\s+([a-z]+)\s+([a-z]+)\s+on\s+the\s+([a-z]+)$', sentence)
        if m2:
            subj, verb, obj = m2.groups()
            return {
                "answer": f"The {obj} was {verb} on by the {subj}.",
                "justification": "Canonical passive rewrite matched bounded prepositional pattern.",
                "answer_kind": "rewrite",
            }
        m3 = re.match(r'(?i)the\s+([a-z]+)\s+([a-z]+)\s+the\s+([a-z]+)$', sentence)
        if m3:
            subj, verb, obj = m3.groups()
            return {
                "answer": f"The {obj} was {verb} by the {subj}.",
                "justification": "Canonical passive rewrite matched bounded transitive pattern.",
                "answer_kind": "rewrite",
            }
        return None

    def _canonical_sort(self, text: str) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling canonical sort.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_canonical_sort(text='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_canonical_sort`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `_canonical_sort`.
        """
        if not re.search(r"\b(sort|ascending|descending|order)\b", text, flags=re.IGNORECASE):
            return None
        m = re.search(r"(\[[^\]]+\])", text)
        if not m:
            return None
        try:
            value = ast.literal_eval(m.group(1))
        except Exception:
            return None
        if not isinstance(value, list):
            return None
        reverse = bool(re.search(r"\bdescending\b", text, flags=re.IGNORECASE))
        try:
            sorted_value = sorted(value, reverse=reverse)
        except Exception:
            return None
        return {
            "answer": json.dumps(sorted_value),
            "justification": "Canonical finite ordering over the literal list succeeded.",
            "answer_kind": "finite_construction",
        }

    def _canonical_direct_resolution(self, text: str) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling canonical direct resolution.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `_canonical_direct_resolution(text='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `_canonical_direct_resolution`. Expected type: `str`.

        Returns:
            dict[str, Any] | None: Result produced by `_canonical_direct_resolution`.
        """
        for resolver in (
            self._canonical_arithmetic,
            canonical_stable_fact_lookup,
            self._canonical_syllogism,
            self._canonical_passive_rewrite,
            self._canonical_sort,
        ):
            result = resolver(text)
            if result is not None:
                return {
                    "resolved": True,
                    "answer": result["answer"],
                    "justification": result["justification"],
                    "confidence": "high",
                    "closure_status": "ready",
                    "answer_kind": result["answer_kind"],
                    "rationale": "Deterministic canonicalization recognized a bounded operator form before escalation or decomposition.",
                }
        return None

    def fallback_direct_resolution(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback direct resolution.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_direct_resolution(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_direct_resolution`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_direct_resolution`.
        """
        canonical = self._canonical_direct_resolution(node.semantic_unit)
        if canonical is not None:
            canonical.setdefault("function_artifact", {})
            canonical.setdefault("invocation_payload", {})
            return canonical
        return {
            "resolved": False,
            "answer": "",
            "justification": "Fallback direct resolution found no bounded canonical operator form and therefore does not infer world-facing or semantic assumptions without an LLM judgment.",
            "confidence": "low",
            "closure_status": "not_ready",
            "answer_kind": "none",
            "function_artifact": {},
            "invocation_payload": {},
            "rationale": "Fallback direct resolution stays conservative after deterministic canonicalization fails.",
        }

    def fallback_realization_witness(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback realization witness.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_realization_witness(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_realization_witness`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_realization_witness`.
        """
        canonical = self._canonical_direct_resolution(node.semantic_unit)
        if canonical is not None:
            answer_kind = str(canonical.get("answer_kind", "direct_answer"))
            witness_kind = {
                "arithmetic": "symbolic_compute",
                "direct_fact": "bounded_fact",
                "logical_entailment": "logical_chain",
                "rewrite": "exact_rewrite",
                "finite_construction": "finite_construction",
            }.get(answer_kind, "finite_construction")
            return {
                "realizable_now": True,
                "answer": canonical["answer"],
                "answer_kind": answer_kind,
                "witness_kind": witness_kind,
                "witness_steps": [canonical["justification"]],
                "validation_check": "Canonical bounded operator produced a stable result under deterministic realization.",
                "confidence": canonical["confidence"],
                "closure_status": canonical["closure_status"],
                "function_artifact": {},
                "invocation_payload": {},
                "rationale": "Fallback present-witness generation used deterministic canonicalization before any nonlocal reasoning.",
            }
        return {
            "realizable_now": False,
            "answer": "",
            "answer_kind": "none",
            "witness_kind": "none",
            "witness_steps": [],
            "validation_check": "",
            "confidence": "low",
            "closure_status": "not_ready",
            "function_artifact": {},
            "invocation_payload": {},
            "rationale": "Fallback present-witness generation stays conservative when no governed realization witness is available.",
        }

    def materialize_function_artifact_from_payload(
        self,
        *,
        node: SemanticNode,
        payload: Mapping[str, Any],
        invocation_payload: Any,
        provenance: list[str],
        answer_kind: str,
        justification: str,
        validation_check: str = "",
    ) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for materialize function artifact from.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `materialize_function_artifact_from_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, invocation_payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, provenance=['mass', 'acceleration', 'force'])`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `materialize_function_artifact_from_payload`. Expected type: `SemanticNode`.
            payload: Value for `payload` used by `materialize_function_artifact_from_payload`. Expected type: `Mapping[str, Any]`.
            invocation_payload: Value for `invocation_payload` used by `materialize_function_artifact_from_payload`. Expected type: `Any`.
            provenance: Value for `provenance` used by `materialize_function_artifact_from_payload`. Expected type: `list[str]`.
            answer_kind: Value for `answer_kind` used by `materialize_function_artifact_from_payload`. Expected type: `str`.
            justification: Value for `justification` used by `materialize_function_artifact_from_payload`. Expected type: `str`.
            validation_check: Value for `validation_check` used by `materialize_function_artifact_from_payload`. Expected type: `str`. Defaults to `''`.

        Returns:
            Artifact | None: Result produced by `materialize_function_artifact_from_payload`.
        """
        raw_function_artifact = payload.get("function_artifact", {})
        if not isinstance(raw_function_artifact, Mapping) or not raw_function_artifact:
            return None

        artifact_payload = dict(raw_function_artifact)
        artifact_payload["artifact_type"] = "ability"
        artifact_payload["representation"] = "python_script"
        artifact_payload["function_bit"] = 1
        artifact_payload.setdefault("title", f"Parameterized resolver for {titleize_semantic_unit(node.semantic_unit) or node.semantic_unit}")
        artifact_payload.setdefault(
            "scope",
            f"reuse when the same parameterized calculation or template family as '{node.semantic_unit}' reappears under compatible inputs",
        )
        artifact_payload.setdefault("reusability", "broad_reuse")
        artifact_payload.setdefault("admissibility", "admitted")
        artifact_payload.setdefault("learning_relation", "extends_parameters")
        artifact_payload.setdefault("justification", justification)

        content = dict(artifact_payload.get("content", {})) if isinstance(artifact_payload.get("content", {}), Mapping) else {}
        if not str(content.get("python_script", "")).strip():
            return None
        content.setdefault("question", node.semantic_unit)
        content.setdefault("answer_kind", answer_kind or "function_execution")
        content.setdefault("default_invocation_payload", json_safe(invocation_payload))
        if validation_check:
            content.setdefault("validation_check", validation_check)
        content.setdefault("structured_learning", self.structured_learning_view(node))
        artifact_payload["content"] = content

        artifact = self.build_artifact_from_payload(
            node=node,
            payload=artifact_payload,
            provenance=provenance,
        )
        if artifact is None:
            return None
        artifact.function_bit = 1
        self.state.learned_artifacts[artifact.id] = artifact
        return artifact

    def resolve_function_execution_payload(
        self,
        *,
        node: SemanticNode,
        payload: Mapping[str, Any],
        provenance: list[str],
        answer_kind: str,
        justification: str,
        validation_check: str = "",
    ) -> tuple[str, Artifact | None, CrossBoundaryResult | None]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for resolve function execution.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `resolve_function_execution_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, provenance=['mass', 'acceleration', 'force'], answer_kind='force')`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `resolve_function_execution_payload`. Expected type: `SemanticNode`.
            payload: Value for `payload` used by `resolve_function_execution_payload`. Expected type: `Mapping[str, Any]`.
            provenance: Value for `provenance` used by `resolve_function_execution_payload`. Expected type: `list[str]`.
            answer_kind: Value for `answer_kind` used by `resolve_function_execution_payload`. Expected type: `str`.
            justification: Value for `justification` used by `resolve_function_execution_payload`. Expected type: `str`.
            validation_check: Value for `validation_check` used by `resolve_function_execution_payload`. Expected type: `str`. Defaults to `''`.

        Returns:
            tuple[str, Artifact | None, CrossBoundaryResult | None]: Result produced by `resolve_function_execution_payload`.
        """
        invocation_payload = payload.get("invocation_payload", {})
        artifact = self.materialize_function_artifact_from_payload(
            node=node,
            payload=payload,
            invocation_payload=invocation_payload,
            provenance=provenance,
            answer_kind=answer_kind,
            justification=justification,
            validation_check=validation_check,
        )
        if artifact is None:
            return "", None, None
        execution = self.execute_function_artifact(
            artifact,
            semantic_unit=node.semantic_unit,
            explicit_payload=invocation_payload,
        )
        if not execution.ok:
            artifact.admissibility = ArtifactAdmission.CANDIDATE
            return "", artifact, execution
        artifact.admissibility = ArtifactAdmission.ADMITTED
        try:
            self.persist_generated_artifact(artifact)
        except Exception as exc:
            self.state.record_step(
                kind="artifact_persistence_failure",
                node_id=node.id,
                intent="Persist function-bearing artifacts generated during direct resolution when possible.",
                action="persist generated function artifact",
                result="persistence failed",
                evaluation="execution can still continue because the current run keeps the artifact in memory",
                payload={"artifact_id": artifact.id, "error": str(exc)},
            )
        answer = str(execution.answer).strip()
        return answer, artifact, execution

    def propose_direct_resolution(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing direct resolution.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_direct_resolution(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_direct_resolution`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_direct_resolution`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.DIRECT_RESOLUTION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Decide whether the active item is a trivial, self-contained question that should be answered directly right now.
                Do not broaden the task and do not invent missing complexity.

                Field guidance:
                - resolved: true only if a concise direct answer is warranted right now.
                - answer: the direct answer. Leave empty if resolved is false.
                - justification: short reason why the answer is directly warranted, or why it is not.
                - confidence: one of low, medium, or high.
                - closure_status: one of ready, needs_support, or not_ready.
                - answer_kind: short label such as arithmetic, direct_fact, concise_definition, or none.
                - function_artifact: empty object unless the best direct answer is a reusable parameterized Python function.
                - invocation_payload: empty object unless function_artifact is present. This should be the concrete JSON payload to pass now.

                Rules:
                - If the question is trivial and self-contained, prefer a direct answer over decomposition.
                - If the task is best handled as a reusable parameterized calculation or template, return function_artifact plus invocation_payload instead of a static answer.
                - Any function_artifact must be an ability artifact stored as python_script with inline dependency metadata.
                - Function artifacts must read JSON from stdin, keep argparse support, use msgspec and orjson, and write JSON to stdout with status, answer, result, and notes.
                - If the question is not trivial or support is missing, set resolved to false.
                - Consider ordinary real-world assumptions and context, and only answer directly when the usual interpretation is stable enough.
                - Do not refuse a direct answer merely because a bizarre alternate interpretation is imaginable.
                - If related prior residue is present in the state, you may use it as partial support and then answer directly if the whole item is now straightforward.
                - Use closure_status=ready when the answer can close the present task now under its ordinary interpretation.
                - If closure_status=ready, use confidence=high unless there is a concrete reason not to.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload=self.fallback_direct_resolution(node),
            mode=SupplementMode.FAST,
        )
        node.metadata["direct_resolution_proposal_id"] = proposal.id
        return proposal

    def propose_realization_witness(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing realization witness.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_realization_witness(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_realization_witness`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_realization_witness`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.REALIZATION_WITNESS,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Produce a present realization witness for the active item if it is bounded and self-contained.
                This is not a meta-judgment about whether answering would be nice. Actually solve or realize the item now if it is safely doable.

                Field guidance:
                - realizable_now: true only if the item can be realized now without outside lookup or unresolved ambiguity.
                - answer: the realized answer or output. Leave empty if realizable_now is false.
                - answer_kind: short label such as arithmetic, direct_fact, logical_entailment, rewrite, finite_constructive, or none.
                - witness_kind: one of symbolic_compute, logical_chain, bounded_fact, exact_rewrite, finite_construction, or none.
                - witness_steps: 1 to 4 short steps showing why the answer follows.
                - validation_check: one short invariant check, consistency check, or equivalent verification.
                - confidence: one of low, medium, or high.
                - closure_status: one of ready, needs_support, or not_ready.
                - function_artifact: empty object unless a parameterized Python function is the right realization vehicle.
                - invocation_payload: empty object unless function_artifact is present. This should be the concrete JSON payload to execute now.

                Rules:
                - Use this only for bounded self-contained items.
                - For arithmetic or finite constructive tasks, actually carry out the computation.
                - If the bounded task is parameterized and reusable, prefer a function_artifact plus invocation_payload over a one-off handwritten answer.
                - Any function_artifact must be an ability artifact stored as python_script with inline dependency metadata.
                - Function artifacts must read JSON from stdin, keep argparse support, use msgspec and orjson, and write JSON to stdout with status, answer, result, and notes.
                - For logical tasks, state the entailment chain briefly.
                - For rewrite tasks, preserve the requested meaning and transformation.
                - For factual tasks, answer directly only if the ordinary fact is stable enough that no fresh lookup is needed.
                - If partial prior residue is available from related non-achievedness, integrate it and still attempt a fresh present witness for the whole item.
                - If realizable_now is true, witness_steps and validation_check must both be non-empty.
                - If the answer is not safe to realize now, set realizable_now to false.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload=self.fallback_realization_witness(node),
            mode=self.select_supplement_mode("realization", node),
        )
        node.metadata["realization_witness_proposal_id"] = proposal.id
        return proposal

    def propose_uncertainty_assessment(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing uncertainty assessment.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_uncertainty_assessment(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_uncertainty_assessment`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_uncertainty_assessment`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.UNCERTAINTY_ASSESSMENT,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Review what is still unclear about the active item and why a final answer may be premature.

                Field guidance:
                - uncertainty_loci: name the parts of the task that are still unclear.
                - insufficiency_classes: describe what is missing, such as evidence, detail, or decomposition.
                - ambiguity_classes: list competing interpretations or unresolved wording.
                - conflict_descriptions: describe contradictions or incompatible signals.
                - tests: propose checks, evidence, or actions that would reduce uncertainty.
                - reasons_to_refrain_from_closure: state why the system should avoid calling the item complete.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "uncertainty_loci": [node.semantic_unit],
                "insufficiency_classes": list(self.state.blockers.get(node.id, [])) or ["insufficient_support"],
                "ambiguity_classes": [],
                "conflict_descriptions": list(self.state.conflicts.get(node.id, [])),
                "tests": ["collect stronger support", "reassess after propagation"],
                "reasons_to_refrain_from_closure": ["certainty is not yet high enough for closure"],
            "rationale": "Fallback uncertainty summary mirrors the current blockers and certainty state.",
            },
            mode=self.select_supplement_mode("uncertainty", node),
        )
        node.metadata["uncertainty_assessment_id"] = proposal.id
        node.metadata["uncertainty_assessment"] = proposal.payload
        self.admit_proposal(
            proposal,
            rationale="Uncertainty assessments may be admitted as advisory structure without authorizing certainty transitions.",
        )
        return proposal

    def propose_retrieval_plan(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing retrieval plan.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_retrieval_plan(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_retrieval_plan`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_retrieval_plan`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.RETRIEVAL_PLAN,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Build a focused research plan for the active item.
                The goal is to identify what to look up, where to look, and what would count as useful support.

                Field guidance:
                - retrieval_queries: write concrete search or lookup queries.
                - source_classes: name the kinds of sources to consult.
                - retrieval_plan: list the steps in order.
                - evidence_expectations: describe what useful material should look like.
                - triangulation_plan: explain how to cross-check the result.
                - stop_conditions: say when enough support has been gathered.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "retrieval_queries": [f"What evidence would justify a confident answer for {node.semantic_unit}?"],
                "source_classes": ["human_input", "tool_result", "retrieved_material"],
                "retrieval_plan": [
                    "Clarify what is missing",
                    "Collect relevant supporting material",
                    "Reassess certainty after the new material is attached",
                ],
                "evidence_expectations": ["traceable support that is directly relevant to the active item"],
                "triangulation_plan": ["prefer at least one independent support source when possible"],
                "stop_conditions": ["stop when the support score reaches ok"],
                "rationale": "Fallback research planning targets the support that is currently missing.",
            },
            mode=self.select_supplement_mode("retrieval", node),
        )
        node.metadata["retrieval_plan_id"] = proposal.id
        node.metadata["retrieval_plan"] = proposal.payload
        self.admit_proposal(
            proposal,
            rationale="Retrieval plans may be admitted as action guidance while retrieved material remains separately governed.",
        )
        return proposal

    def propose_capability_draft(self, node: SemanticNode, *, semantic_role: str, affordance: str) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing capability draft.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_capability_draft(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), semantic_role='Physics / Force / Force From Mass And Acceleration', affordance='force')`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_capability_draft`. Expected type: `SemanticNode`.
            semantic_role: Value for `semantic_role` used by `propose_capability_draft`. Expected type: `str`.
            affordance: Value for `affordance` used by `propose_capability_draft`. Expected type: `str`.

        Returns:
            ProposalObject: Result produced by `propose_capability_draft`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.CAPABILITY_DRAFT,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Describe the missing ability or tool support that would help move this item forward.
                Treat this as a design draft for a capability, not as proof that the capability exists.

                Field guidance:
                - capability_kind: short category name for the missing ability.
                - semantic_role: keep the provided role unless there is a strong reason to refine it.
                - affordance: one sentence describing what the capability would do.
                - input_form: what it would consume.
                - output_form: what it would produce.
                - limits: operating limits, scope, and safety boundaries.
                - sub_capabilities: smaller abilities that would support it.
                - recommended_tooling_family: broad implementation family, such as search, human input, parser, or analyzer.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "capability_kind": "support_acquisition",
                "semantic_role": semantic_role,
                "affordance": affordance,
                "input_form": node.semantic_unit,
                "output_form": "usable evidence or tool output",
                "limits": {"for_node": node.id, "generated": True},
                "sub_capabilities": [],
                "recommended_tooling_family": "human_input_or_tool_result",
                "rationale": "Fallback capability drafting preserves the current support-gathering path.",
            },
            mode=self.select_supplement_mode("capability", node),
        )
        node.metadata.setdefault("capability_draft_ids", []).append(proposal.id)
        return proposal

    def propose_reframe(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing reframe.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_reframe(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_reframe`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_reframe`.
        """
        proposal = self.request_proposal(
            proposal_type=ProposalType.REFRAME,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Suggest a better way to state this subtask if the current version is too broad, misleading, or poorly shaped.
                Do not solve the task. Keep the replacement compatible with the current parent task and nearby siblings.

                Field guidance:
                - candidate_reframed_not: keep the fixed field name, but put a better problem statement in the value.
                - reframing_reason: explain why the new wording is better.
                - semantic_loss_gain_notes: list what becomes clearer, broader, narrower, or less explicit.
                - preservation_obligations: list the important parts of the original request that must not be lost.

                Current wording:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "candidate_reframed_not": f"better framing for {node.semantic_unit}",
                "reframing_reason": "Fallback reframing broadens or sharpens the problem statement when the current wording is weak.",
                "semantic_loss_gain_notes": ["gain: clearer framing", "loss: some local specificity"],
                "preservation_obligations": [node.semantic_unit],
                "rationale": "Fallback reframing is only a draft and does not change the task by itself.",
            },
            mode=SupplementMode.DEEP,
        )
        node.metadata["reframe_proposal_id"] = proposal.id
        return proposal

    def propose_explanation_draft(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing explanation draft.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_explanation_draft(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_explanation_draft`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_explanation_draft`.
        """
        outcome = self.state.run_outcome.value
        proposal = self.request_proposal(
            proposal_type=ProposalType.EXPLANATION_DRAFT,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Write a short status update for a human reader.
                Explain where the work stands, what progress has been made, and what would help next.

                Field guidance:
                - summary: plain-language snapshot of the current state.
                - progress_note: what has already been accomplished.
                - continuation_note: what should happen next or what input is needed.
                - clarification_prompts: useful follow-up questions for a human.

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload={
                "summary": f"The run for '{node.semantic_unit}' is currently {outcome}.",
                "progress_note": "Steps, evidence, and decisions are recorded and can be resumed.",
                "continuation_note": "Resume by supplying the missing evidence or signal when continuation should be retried.",
                "clarification_prompts": ["What evidence or information is still missing?"],
                "rationale": "Fallback explanation mirrors the current state without changing it.",
            },
            mode=self.select_supplement_mode("explanation", node),
        )
        node.metadata["explanation_draft_id"] = proposal.id
        self.admit_proposal(
            proposal,
            rationale="Explanation drafts may be admitted as communicative artifacts without changing formal commitment state.",
        )
        return proposal

    def default_template_schema(
        self,
        *,
        artifact_type: str,
        node: SemanticNode,
        scope: str,
        governed_function: str,
        completion_conditions: list[str],
        failure_conditions: list[str],
        harvest_conditions: list[str],
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with supplying default template schema.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `default_template_schema(artifact_type='ability', node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), scope='force', governed_function='force')`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_type: Value for `artifact_type` used by `default_template_schema`. Expected type: `str`.
            node: Value for `node` used by `default_template_schema`. Expected type: `SemanticNode`.
            scope: Value for `scope` used by `default_template_schema`. Expected type: `str`.
            governed_function: Value for `governed_function` used by `default_template_schema`. Expected type: `str`.
            completion_conditions: Value for `completion_conditions` used by `default_template_schema`. Expected type: `list[str]`.
            failure_conditions: Value for `failure_conditions` used by `default_template_schema`. Expected type: `list[str]`.
            harvest_conditions: Value for `harvest_conditions` used by `default_template_schema`. Expected type: `list[str]`.

        Returns:
            dict[str, Any]: Result produced by `default_template_schema`.
        """
        return {
            "preconditions": ["the active item matches the artifact scope", "the current state is admissible for governed reuse"],
            "invariant_core": governed_function,
            "variation_parameters": ["semantic_unit", "support context"],
            "governed_function": governed_function,
            "bssc_awareness": {
                "admissible_place_in_realization": "governed realization state",
                "required_governed_state": "active represented non-achievedness with durable state",
                "permitted_governed_effect": f"support {enum_text(artifact_type)} reuse without self-justifying closure",
                "may_not_by_itself_justify": ["closure"],
            },
            "holdon_awareness": {
                "relevant_holdon_blocks_instantiation": artifact_type not in {"uncertainty_pattern", "rejection_pattern"},
                "diagnostic_use_allowed": True,
                "relevant_holdon_conditions": ["missing evidence", "pause boundary", "governance block"],
                "resumption_condition": "resume ordinary use only when the blocking condition is cleared",
            },
            "completion_conditions": completion_conditions,
            "failure_conditions": failure_conditions,
            "harvest_conditions": harvest_conditions,
            "scope_of_reuse": scope,
            "source_node_id": node.id,
        }

    def template_schema_complete(self, schema: Mapping[str, Any]) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling template schema complete.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `template_schema_complete(schema={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'})`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            schema: Value for `schema` used by `template_schema_complete`. Expected type: `Mapping[str, Any]`.

        Returns:
            bool: Result produced by `template_schema_complete`.
        """
        if pure_theory_template_schema_from_runtime(schema) is not None:
            return True
        required = {
            "preconditions",
            "invariant_core",
            "variation_parameters",
            "governed_function",
            "bssc_awareness",
            "holdon_awareness",
            "completion_conditions",
            "failure_conditions",
            "harvest_conditions",
            "scope_of_reuse",
        }
        if not required.issubset(schema.keys()):
            return False
        bssc = schema.get("bssc_awareness", {})
        holdon = schema.get("holdon_awareness", {})
        return isinstance(bssc, Mapping) and isinstance(holdon, Mapping) and bool(bssc) and bool(holdon)

    def related_learned_artifact_ids(self, artifact_type: str, title: str, scope: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling related learned artifact ids.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `related_learned_artifact_ids(artifact_type='ability', title='Physics / Force / Force From Mass And Acceleration', scope='force')`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_type: Value for `artifact_type` used by `related_learned_artifact_ids`. Expected type: `str`.
            title: Value for `title` used by `related_learned_artifact_ids`. Expected type: `str`.
            scope: Value for `scope` used by `related_learned_artifact_ids`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `related_learned_artifact_ids`.
        """
        related: list[str] = []
        for artifact in list(self.state.learned_artifacts.values()) + list(self.state.artifacts.values()):
            if artifact.artifact_type != artifact_type:
                continue
            if artifact.id in related:
                continue
            if semantic_tokens(title) & semantic_tokens(artifact.title):
                related.append(artifact.id)
                continue
            if semantic_tokens(scope) & semantic_tokens(artifact.scope):
                related.append(artifact.id)
        return related[:4]

    def derived_discovery_artifact_payloads(self, node: SemanticNode) -> list[dict[str, Any]]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling derived discovery artifact payloads.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `derived_discovery_artifact_payloads(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `derived_discovery_artifact_payloads`. Expected type: `SemanticNode`.

        Returns:
            list[dict[str, Any]]: Result produced by `derived_discovery_artifact_payloads`.
        """
        answer = str(node.metadata.get("direct_resolution_answer", "")).strip()
        answer_kind = str(node.metadata.get("direct_resolution_answer_kind", "direct_answer")).strip() or "direct_answer"
        if not answer:
            return []
        derived: list[dict[str, Any]] = []
        ability_payload = self.ability_payload_from_python_answer(
            node=node,
            answer=answer,
            answer_kind=answer_kind,
        )
        if ability_payload is not None:
            ability_scope = str(ability_payload.get("scope", "")).strip()
            ability_payload["related_artifact_ids"] = self.related_learned_artifact_ids(
                "ability",
                str(ability_payload.get("title", "")).strip(),
                ability_scope,
            )
            derived.append(ability_payload)
        return derived

    def fallback_discovery_audit(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback discovery audit.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_discovery_audit(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_discovery_audit`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_discovery_audit`.
        """
        outcome = self.state.run_outcome.value
        pain_class = "no_pain"
        if outcome != RunOutcome.COMPLETED.value:
            pain_class = "pain"
        elif self.state.pause_points or any(capability.realizer == "generated_capability" for capability in self.state.capabilities.values()):
            pain_class = "pain"
        elif any(item.kind in {"reflection", "contemplation"} for item in self.state.ledger):
            pain_class = "pain" if self.refinement_children(node) else "no_pain"

        enablers: list[str] = []
        diagnostics: list[str] = []
        artifacts: list[dict[str, Any]] = []
        immediate_learning: list[dict[str, Any]] = []

        answer = str(node.metadata.get("direct_resolution_answer", "")).strip()
        answer_kind = str(node.metadata.get("direct_resolution_answer_kind", "direct_answer")).strip() or "direct_answer"
        if answer:
            enablers.append("the item was narrow enough for direct resolution under the ordinary reading")
            closure_scope = f"bounded {answer_kind} prompts that are self-contained and conventionally interpreted"
            artifacts.extend(self.derived_discovery_artifact_payloads(node))
            artifacts.append(
                {
                    "artifact_type": "closure_pattern",
                    "title": f"Direct closure pattern for {answer_kind}",
                    "representation": "json",
                    "scope": closure_scope,
                    "reusability": "broad_reuse",
                    "admissibility": "admitted",
                    "learning_relation": "new_family",
                    "related_artifact_ids": self.related_learned_artifact_ids("closure_pattern", f"Direct closure pattern for {answer_kind}", closure_scope),
                    "justification": "the run closed through direct resolution without requiring subordinate achievement decomposition",
                    "constraints": ["use only when the question is self-contained and the ordinary interpretation is stable"],
                    "template_schema": self.default_template_schema(
                        artifact_type="closure_pattern",
                        node=node,
                        scope=closure_scope,
                        governed_function="keep the item whole and close directly when a stable ordinary reading yields a ready direct answer",
                        completion_conditions=["direct resolution is ready", "support-bearing answer evidence is attached"],
                        failure_conditions=["ordinary interpretation is unstable", "external evidence is required"],
                        harvest_conditions=["the closure path is reusable beyond this exact phrasing"],
                    ),
                    "content": {
                        "node_id": node.id,
                        "answer_kind": answer_kind,
                        "closure_rule": "if direct resolution is ready, keep the item whole and close it after support-bearing evidence is attached",
                    },
                }
            )
            if answer_kind in {"direct_fact", "concise_definition"}:
                artifacts.append(
                    {
                        "artifact_type": "knowledge",
                        "title": f"Knowledge note from {node.semantic_unit}",
                        "representation": "json",
                        "scope": "reuse when the same stable fact is asked again under the same ordinary reading",
                        "reusability": "local_reuse",
                        "admissibility": "candidate",
                        "learning_relation": "new_family",
                        "related_artifact_ids": self.related_learned_artifact_ids("knowledge", f"Knowledge note from {node.semantic_unit}", "reuse when the same stable fact is asked again under the same ordinary reading"),
                        "template_schema": {},
                        "justification": "the run produced a bounded answer that may be reusable beyond the exact originating phrasing",
                        "constraints": ["reuse only when the fact remains stable and no fresher evidence is required"],
                        "content": {
                            "node_id": node.id,
                            "question": node.semantic_unit,
                            "answer": answer,
                        },
                    }
                )
        if outcome in {RunOutcome.PAUSED.value, RunOutcome.INCOMPLETE.value}:
            blockers = list(self.state.blockers.get(node.id, []))
            if blockers:
                diagnostics.extend(blockers)
                artifacts.append(
                    {
                        "artifact_type": "uncertainty_pattern",
                        "title": f"Uncertainty boundary for {node.semantic_unit}",
                        "representation": "json",
                        "scope": "reuse when a later run shows the same blocker shape",
                        "reusability": "local_reuse",
                        "admissibility": "candidate",
                        "learning_relation": "new_family",
                        "related_artifact_ids": self.related_learned_artifact_ids("uncertainty_pattern", f"Uncertainty boundary for {node.semantic_unit}", "reuse when a later run shows the same blocker shape"),
                        "justification": "the run exposed a reusable insufficiency signature rather than silently stalling",
                        "constraints": ["treat as a pattern, not as closure support by itself"],
                        "template_schema": self.default_template_schema(
                            artifact_type="uncertainty_pattern",
                            node=node,
                            scope="reuse when a later run shows the same blocker shape",
                            governed_function="identify when similar insufficiency or blocker structure is recurring",
                            completion_conditions=["the same blocker shape is recognized in a later run"],
                            failure_conditions=["the later blocker is semantically different", "the pattern is treated as closure support by itself"],
                            harvest_conditions=["the blocker shape is specific enough to be reusable"],
                        ),
                        "content": {
                            "node_id": node.id,
                            "run_outcome": outcome,
                            "blockers": blockers,
                        },
                    }
                )
        for capability in self.state.capabilities.values():
            if capability.realizer != "generated_capability":
                continue
            artifacts.append(
                {
                    "artifact_type": "capability",
                    "title": capability.affordance,
                    "representation": "json",
                    "scope": f"reuse when the same missing ability appears around {capability.semantic_role}",
                    "reusability": "local_reuse",
                    "admissibility": "candidate",
                    "learning_relation": "new_family",
                    "related_artifact_ids": self.related_learned_artifact_ids("capability", capability.affordance, f"reuse when the same missing ability appears around {capability.semantic_role}"),
                    "justification": "the run had to surface a missing governed capability",
                    "constraints": ["requires separate operational realization before trusted reuse"],
                    "template_schema": self.default_template_schema(
                        artifact_type="capability",
                        node=node,
                        scope=f"reuse when the same missing ability appears around {capability.semantic_role}",
                        governed_function="specify what may be done under what conditions when this capability gap reappears",
                        completion_conditions=["the capability gap is explicitly recognized", "admissible use conditions are clear"],
                        failure_conditions=["the capability is treated as if already operational", "failure modes are omitted"],
                        harvest_conditions=["the missing capability pattern recurs beyond this single instance"],
                    ),
                    "content": capability.to_dict(),
                }
            )
            ability_scope = f"executable governed helper for {capability.semantic_role} when the same gap recurs"
            artifacts.append(
                {
                    "artifact_type": "ability",
                    "title": f"{capability.affordance} script",
                    "representation": "python_script",
                    "scope": ability_scope,
                    "reusability": "local_reuse",
                    "admissibility": "candidate",
                    "learning_relation": "new_family",
                    "related_artifact_ids": self.related_learned_artifact_ids("ability", f"{capability.affordance} script", ability_scope),
                    "justification": "the run identified a reusable executable ability shape that should live as a stored Python script artifact",
                    "constraints": [
                        "validate the script before operational reuse",
                        "do not treat the script artifact as closure support by itself",
                    ],
                    "template_schema": self.default_template_schema(
                        artifact_type="ability",
                        node=node,
                        scope=ability_scope,
                        governed_function="provide an executable helper that realizes the governed ability under explicit limits",
                        completion_conditions=["the script accepts governed input and produces the expected structured output"],
                        failure_conditions=["input contract is violated", "the script is used outside its scope or limits"],
                        harvest_conditions=["later runs can reuse or refine the same executable ability family"],
                    ),
                    "content": {
                        "entrypoint": "main",
                        "script_language": "python",
                        "dependencies": list(ABILITY_SCRIPT_DEPENDENCIES),
                        "input_contract": {"payload": "JSON object from stdin or --input-json"},
                        "output_contract": {"result": "JSON object to stdout"},
                    },
                }
            )
        gain_candidates = [item for item in artifacts if normalize_artifact_admission(item.get("admissibility", "candidate")) != "rejected"]
        gain_types = sorted({normalize_artifact_type(item.get("artifact_type", "knowledge")) for item in gain_candidates})
        return {
            "pain_class": pain_class,
            "gain_class": "gain" if gain_candidates else "no_gain",
            "gain_types": gain_types,
            "enablers": enablers or ["the run preserved its current boundary conditions faithfully"],
            "diagnostics": diagnostics,
            "artifacts": artifacts[:3],
            "immediate_learning": immediate_learning[:3],
            "rationale": "Fallback discovery audit extracts bounded reusable residue from the run outcome.",
        }

    def propose_discovery_audit(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing discovery audit.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_discovery_audit(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_discovery_audit`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_discovery_audit`.
        """
        outcome = self.state.run_outcome.value
        fallback = self.fallback_discovery_audit(node)
        proposal = self.request_proposal(
            proposal_type=ProposalType.DISCOVERY_AUDIT,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Run a bounded development audit for the finished encounter.
                Do not reopen the task and do not ask for more decomposition of the present task.
                The goal is to determine whether this encounter produced reusable residue for future runs.

                Required questions:
                1. What made this outcome possible?
                2. Is any reusable residue present?
                3. If yes, what kind of artifact is it?
                4. How should it be represented?
                5. What scope and constraints govern reuse?
                6. Should it be admitted now, kept as a candidate, or rejected?
                7. What immediate further learning would most help nearby future runs, and can it be learned now in a bounded way?

                Field guidance:
                - pain_class: one of no_pain or pain.
                - gain_class: one of no_gain or gain.
                - gain_types: zero or more artifact types from this list:
                  knowledge, ability, capability, duty_template, closure_pattern,
                  rejection_pattern, uncertainty_pattern, composition, evaluation.
                - enablers: concrete things that made the outcome possible.
                - diagnostics: concrete notes about friction, missing structure, or missed harvest.
                - artifacts: up to 3 artifact candidates.
                - immediate_learning: up to 3 nearby follow-on learning units that should be harvested now for future reuse.

                Artifact field guidance:
                - artifact_type: choose one allowed artifact type.
                - title: the formal semantic identity of the artifact.
                - title may use ordered segmentation with / when broader-to-narrower determination is semantically necessary for stable reuse.
                - if segmented, use / only for real ordered depth; do not segment decoratively.
                - choose the minimally sufficient non-colliding title, not the longest descriptive label.
                - representation: how it should be stored, such as json, text, schema, or python_script.
                - scope: where it is admissibly reusable.
                - reusability: one of instance_only, local_reuse, or broad_reuse.
                - admissibility: one of admitted, candidate, or rejected.
                - learning_relation: one of new_family, instance_of_existing, refines_existing, or extends_parameters.
                - related_artifact_ids: ids of any prior artifacts this candidate instantiates, refines, or extends.
                - justification: why this artifact is warranted by the run.
                - constraints: reuse limits or failure conditions.
                - if artifact_type is ability, use representation python_script and put a Python script in content.python_script.
                - ability scripts must use inline dependency metadata, prefer stdin for input, keep argparse for CLI arguments,
                  and use msgspec and orjson inside the stored script.
                - for ability artifacts also include content.entrypoint, content.dependencies, content.input_contract, and content.output_contract.
                - template_schema: empty for knowledge artifacts. For every other artifact, include:
                  preconditions, invariant_core, variation_parameters, governed_function,
                  bssc_awareness, holdon_awareness, completion_conditions,
                  failure_conditions, harvest_conditions, and scope_of_reuse.
                - content: compact structured payload.

                Immediate learning field guidance:
                - Only include an item if it is an immediate neighbor of the finished encounter and you can answer it now without research.
                - Do not emit a broad curriculum tree.
                - Each item must be bounded and shallow.
                - Each item should include:
                  semantic_unit, encountered_not, component_nots, composed_not,
                  why_now, answer, scope, constraints.
                - Prefer adjacent concepts whose later reuse would help composition, paraphrase transfer, or nearby follow-on questions.
                - Do not reopen the present task. This is for future-governability harvest only.

                Current run outcome:
                {outcome}

                Active item:
                {node.semantic_unit}
                """
            ),
            fallback_payload=fallback,
            mode=SupplementMode.DEEP,
        )
        node.metadata["discovery_audit_proposal_id"] = proposal.id
        self.admit_proposal(
            proposal,
            rationale="Discovery audits are bounded harvest artifacts that may be admitted without reopening achievedness reduction.",
        )
        return proposal

    def fallback_immediate_learning(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback immediate learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_immediate_learning(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `fallback_immediate_learning`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `fallback_immediate_learning`.
        """
        return {
            "immediate_learning": [],
            "rationale": "Fallback adjacent-learning expansion stays empty unless the supplement path can justify bounded nearby learning with actual reusable answers.",
        }

    def propose_immediate_learning(self, node: SemanticNode) -> ProposalObject:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing immediate learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_immediate_learning(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_immediate_learning`. Expected type: `SemanticNode`.

        Returns:
            ProposalObject: Result produced by `propose_immediate_learning`.
        """
        fallback = self.fallback_immediate_learning(node)
        answer = str(node.metadata.get("direct_resolution_answer", "")).strip()
        structured_learning = node.metadata.get("structured_learning", self.structured_learning_view(node))
        component_nots = [
            str(item).strip()
            for item in structured_learning.get("component_nots", [])
            if str(item).strip()
        ] if isinstance(structured_learning.get("component_nots", []), list) else []
        current_artifacts = [
            self.artifact_learning_summary(artifact)
            for artifact in list(self.state.artifacts.values())[-6:]
        ]
        nearby_artifact_objects = self.immediate_learning_context_artifacts(node, limit=10)
        nearby_artifacts = [
            self.artifact_learning_summary(artifact)
            for artifact in nearby_artifact_objects
        ]
        bridge_opportunities = self.immediate_learning_bridge_opportunities(
            node,
            nearby_artifact_objects,
            limit=6,
        )
        proposal = self.request_proposal(
            proposal_type=ProposalType.IMMEDIATE_LEARNING,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                The finished question is done. Do a very small adjacent-learning pass.
                Do not reopen the finished question.
                Do not propose a broad curriculum.

                Your job is to identify up to 3 immediate nearby questions that should be learned now so that the next closely related questions are more likely to reuse stored knowledge instead of starting cold.

                Rules:
                - Each item must be a nearby follow-on question, not a distant topic jump.
                - Each item must be shallow, bounded, and answerable now under ordinary stable reading.
                - Prefer items that help paraphrase transfer, composition, or the next likely student-style follow-up questions.
                - Decompose each item into parts when that helps later lookup.
                - Avoid generic side detours when a more direct bridge question exists.
                - Use nearby learned artifacts from earlier runs when they reveal the next missing bridge.
                - Assume the learner starts with only plain English, basic logic, and basic math.
                - If the finished question has multiple components, prefer:
                  1. one missing single-component prerequisite, and
                  2. one bridge question that explicitly connects the components.
                - Even if the finished question is atomic, inspect the nearby learned artifacts. If they expose a closely adjacent family that should be connected next, you may propose one bridge question between the finished item and that nearby family.
                - If explicit bridge opportunities are listed below, prefer at least one of them unless it is clearly irrelevant.
                - A bridge question should name both sides of the composition and explain how they work together in practice.
                - If nearby learned artifacts already expose one component or family, use that to infer the missing bridge instead of repeating the same component definition.
                - When proposing a bridge, set encountered_not and composed_not to the composed reusable family itself, not to a diagnostic sentence about what is missing.
                - If no such item is worth storing, return an empty list.

                Return JSON with:
                - immediate_learning: up to 3 objects.
                - rationale: one short reason for the chosen expansion.

                Each immediate_learning object must include:
                - semantic_unit
                - encountered_not
                - component_nots
                - composed_not
                - why_now
                - answer
                - scope
                - constraints

                Finished question:
                {node.semantic_unit}

                Finished answer:
                {answer or "(none)"}

                Structured learning view:
                {json.dumps(structured_learning, indent=2, sort_keys=True)}

                Named components:
                {json.dumps(component_nots, indent=2)}

                Artifacts already harvested in this run:
                {json.dumps(current_artifacts, indent=2, sort_keys=True)}

                Nearby learned artifacts from current and prior runs:
                {json.dumps(nearby_artifacts, indent=2, sort_keys=True)}

                Explicit bridge opportunities derived from the current structured Not and nearby learned artifacts:
                {json.dumps(bridge_opportunities, indent=2, sort_keys=True)}
                """
            ),
            fallback_payload=fallback,
            mode=SupplementMode.DEEP,
        )
        node.metadata["immediate_learning_proposal_id"] = proposal.id
        self.admit_proposal(
            proposal,
            rationale="Adjacent-learning expansion is advisory harvest for future runs and does not reopen present achievedness.",
        )
        return proposal

    def fallback_markdown_learning(self, document: MarkdownDocumentIR, *, max_artifacts: int) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback markdown learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_markdown_learning(document=MarkdownDocumentIR(title='Physics Force Lesson'), max_artifacts=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            document: Value for `document` used by `fallback_markdown_learning`. Expected type: `MarkdownDocumentIR`.
            max_artifacts: Value for `max_artifacts` used by `fallback_markdown_learning`. Expected type: `int`.

        Returns:
            dict[str, Any]: Result produced by `fallback_markdown_learning`.
        """
        artifacts: list[dict[str, Any]] = []
        document_summary_parts = list(document.intro_paragraphs)
        if document.intro_bullets:
            document_summary_parts.append("Key points: " + "; ".join(document.intro_bullets[:5]))
        document_summary = collapse_ws(" ".join(document_summary_parts))
        if document_summary:
            artifacts.append(
                {
                    "title": document.title,
                    "semantic_unit": document.title,
                    "question": markdown_caller_facing_question(document.title, document.title),
                    "answer": document_summary,
                    "related_titles": [],
                    "relation_rationale": "",
                    "aliases": [],
                    "component_nots": [],
                    "composed_not": "",
                    "sections": [],
                    "why_reusable": "The markdown document states the overall topic directly in its introduction.",
                }
            )
        for cluster in markdown_document_clusters(document):
            heading = collapse_ws(str(cluster.get("heading", "")))
            if not heading:
                continue
            answer = markdown_cluster_answer(cluster)
            if not answer:
                continue
            artifacts.append(
                {
                    "title": heading,
                    "semantic_unit": heading,
                    "question": markdown_caller_facing_question(document.title, heading),
                    "answer": answer,
                    "related_titles": [],
                    "relation_rationale": "",
                    "aliases": [item for item in cluster.get("sections", []) if str(item).strip() and str(item).strip() != heading][:4],
                    "component_nots": [document.title] if heading != document.title else [],
                    "composed_not": document.title if heading != document.title else "",
                    "sections": list(cluster.get("sections", []))[:6],
                    "why_reusable": "The markdown document contains a bounded section that directly states this knowledge unit.",
                }
            )
        deduped: list[dict[str, Any]] = []
        seen_titles: set[str] = set()
        for candidate in artifacts:
            title_key = collapse_ws(str(candidate.get("title", ""))).lower()
            if not title_key or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            deduped.append(candidate)
            if len(deduped) >= max_artifacts:
                break
        return {
            "document_summary": document_summary,
            "artifacts": deduped,
            "rationale": "Fallback markdown learning extracts reusable knowledge units from the structural markdown ir without semantic supplementation.",
        }

    propose_markdown_learning = propose_semantic_markdown_learning

    def fallback_markdown_ability_learning(self, document: MarkdownDocumentIR, *, max_artifacts: int) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback markdown ability learning.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_markdown_ability_learning(document=MarkdownDocumentIR(title='Physics Force Lesson'), max_artifacts=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            document: Value for `document` used by `fallback_markdown_ability_learning`. Expected type: `MarkdownDocumentIR`.
            max_artifacts: Value for `max_artifacts` used by `fallback_markdown_ability_learning`. Expected type: `int`.

        Returns:
            dict[str, Any]: Result produced by `fallback_markdown_ability_learning`.
        """
        return {
            "encounters": [],
            "artifacts": [],
            "rationale": "Fallback markdown encounter learning does not classify reusable executable encounters without LLM mediation from the structural ir.",
        }

    propose_markdown_ability_learning = propose_semantic_markdown_ability_learning

    def fallback_markdown_functionalization(
        self,
        encounters: Sequence[Mapping[str, Any]],
        *,
        max_artifacts: int,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback markdown functionalization.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_markdown_functionalization(encounters={'title': 'Physics / Force / Force From Mass And Acceleration'}, max_artifacts=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            encounters: Value for `encounters` used by `fallback_markdown_functionalization`. Expected type: `Sequence[Mapping[str, Any]]`.
            max_artifacts: Value for `max_artifacts` used by `fallback_markdown_functionalization`. Expected type: `int`.

        Returns:
            dict[str, Any]: Result produced by `fallback_markdown_functionalization`.
        """
        artifacts: list[dict[str, Any]] = []
        if "python3" in self.supported_executor_frameworks():
            for encounter in encounters:
                payload = self.fallback_markdown_prose_python_ability_payload(encounter)
                if payload is None:
                    continue
                artifacts.append(payload)
                if len(artifacts) >= max_artifacts:
                    break
        return {
            "artifacts": artifacts,
            "rationale": (
                "Fallback markdown functionalization deterministically recovers only explicit prose-defined "
                "executor relations; it does not invent executable artifacts beyond those bounded patterns."
            ),
        }

    propose_markdown_functionalization = propose_semantic_markdown_functionalization

    def fallback_markdown_prose_python_ability_payload(
        self,
        encounter: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        """
        High Level Purpose:
            In circumstances like LLM-off markdown learning over prose that explicitly describes a reusable Python `main(...)` relation, helps with deterministically recovering an ability payload without requiring fenced code or model synthesis.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_markdown_prose_python_ability_payload(encounter={'heading': 'Executable Python relation', 'paragraphs': ['The reusable function signature is `main(url: str) -> dict[str, str]`.'], 'bullets': ['import `subprocess`', 'return `{\"status\": \"opened\", \"url\": url}`']})`
            Output: {'artifact_type': 'ability', 'title': 'Python Function', 'content': {'executor_framework': 'python3', 'python_script': 'def main(url: str) -> dict[str, str]:\\n    import subprocess\\n    return {\"status\": \"opened\", \"url\": url}'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            encounter: Value for `encounter` used by `fallback_markdown_prose_python_ability_payload`. Expected type: `Mapping[str, Any]`.

        Returns:
            dict[str, Any] | None: Result produced by `fallback_markdown_prose_python_ability_payload`.
        """
        heading = collapse_ws(str(encounter.get("heading", "")).strip())
        paragraphs = [
            collapse_ws(str(item).strip())
            for item in encounter.get("paragraphs", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(encounter.get("paragraphs", []), list) else []
        bullets = [
            collapse_ws(str(item).strip())
            for item in encounter.get("bullets", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(encounter.get("bullets", []), list) else []
        heading_lower = heading.lower()
        joined_text = " ".join([heading, *paragraphs, *bullets]).lower()
        if "python" not in heading_lower and "python" not in joined_text:
            return None

        signature_text = ""
        for part in [heading, *paragraphs, *bullets]:
            for candidate in re.findall(r"`([^`]+)`", part):
                normalized_candidate = collapse_ws(candidate.strip())
                if normalized_candidate.startswith("main("):
                    signature_text = normalized_candidate
                    break
            if signature_text:
                break
        if not signature_text:
            return None

        body_lines: list[str] = []
        for bullet in bullets:
            code_segments = [collapse_ws(item.strip()) for item in re.findall(r"`([^`]+)`", bullet) if collapse_ws(item.strip())]
            lowered_bullet = bullet.lower()
            if lowered_bullet.startswith("import ") and code_segments:
                snippet = code_segments[0]
                body_lines.append(snippet if snippet.startswith("import ") else f"import {snippet}")
                continue
            if lowered_bullet.startswith("return ") and code_segments:
                snippet = code_segments[0]
                body_lines.append(snippet if snippet.startswith("return ") else f"return {snippet}")
                continue
            if (lowered_bullet.startswith("run ") or lowered_bullet.startswith("execute ")) and code_segments:
                body_lines.append(code_segments[0])
                continue
        if not body_lines:
            return None

        python_code = "\n".join(
            [f"def {signature_text}:", *[f"    {line}" for line in body_lines]]
        )
        brokerized = brokerize_python_main_for_host_brokers(python_code)
        if brokerized is not None:
            python_code = brokerized.python_code
        signature = self.callable_python_signature(python_code)
        if signature is None:
            return None
        function_name, argument_names = signature
        if function_name != "main":
            return None

        return_lines = [line for line in body_lines if line.startswith("return ")]
        output_keys = ordered_unique(
            match
            for line in return_lines
            for match in re.findall(r"[\"']([A-Za-z_][A-Za-z0-9_]*)[\"']\s*:", line)
        )
        ability_title = markdown_ability_collision_identity(
            content={"executor_framework": "python3", "representation": "python_script"},
            encounter_heading=heading,
        )
        encounter_id = collapse_ws(str(encounter.get("encounter_id", "")).strip())
        sections = [
            collapse_ws(str(item).strip())
            for item in encounter.get("sections", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(encounter.get("sections", []), list) else []
        content: dict[str, Any] = {
            "executor_framework": "python3",
            "python_script": python_code,
            "entrypoint": "main",
            "script_language": "python",
            "input_contract": {
                name: "required input value"
                for name in argument_names
            },
            "output_contract": (
                {name: "result field" for name in output_keys}
                if output_keys
                else {"result": "execution result"}
            ),
        }
        if brokerized is not None:
            content["governed_host_brokers"] = list(brokerized.broker_names)
            content["governed_authorities"] = list(brokerized.authorities)
        return {
            "artifact_type": "ability",
            "title": ability_title,
            "title_current_identity": ability_title,
            "semantic_unit": heading or ability_title,
            "question": "",
            "encounter_id": encounter_id,
            "sections": sections,
            "content": content,
        }

    def fallback_markdown_expression_synthesis(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback markdown expression synthesis.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `fallback_markdown_expression_synthesis()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `fallback_markdown_expression_synthesis`.
        """
        return {
            "parameterized": False,
            "input_fields": [],
            "output_field": "",
            "compute_expression": "",
            "question": "",
            "aliases": [],
            "why_reusable": "",
            "rationale": "Fallback expression synthesis does not invent parameterized equations without LLM mediation.",
        }

    propose_markdown_expression_synthesis = propose_semantic_markdown_expression_synthesis

    markdown_expression_artifact_payload = build_markdown_expression_artifact_payload

    def markdown_answer_has_prompt_noise(self, text: str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown answer has prompt noise.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `markdown_answer_has_prompt_noise(text='Compute force from mass and acceleration.')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `markdown_answer_has_prompt_noise`. Expected type: `str`.

        Returns:
            bool: Result produced by `markdown_answer_has_prompt_noise`.
        """
        lowered = collapse_ws(text).lower()
        if not lowered:
            return False
        return any(
            marker in lowered
            for marker in (
                "canonical prompt forms:",
                "reusable answer pattern:",
                "source basis for these patterns:",
            )
        )

    def sanitize_markdown_learned_answer(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling sanitize markdown learned answer.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `sanitize_markdown_learned_answer(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `sanitize_markdown_learned_answer`. Expected type: `str`.

        Returns:
            str: Result produced by `sanitize_markdown_learned_answer`.
        """
        cleaned = collapse_ws(text)
        lowered = cleaned.lower()
        for marker in (
            "canonical prompt forms:",
            "reusable answer pattern:",
            "source basis for these patterns:",
        ):
            idx = lowered.find(marker)
            if idx >= 0:
                cleaned = cleaned[:idx].strip()
                lowered = cleaned.lower()
        cleaned = re.sub(r"(?i)\bkey points:\s*", "", cleaned).strip()
        cleaned = re.sub(r"[*_`]+", "", cleaned).strip()
        return collapse_ws(cleaned)

    def looks_like_generic_markdown_question(
        self,
        question: str,
        *,
        semantic_unit: str,
        title: str,
        document_title: str,
    ) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling looks like generic markdown question.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `looks_like_generic_markdown_question(question='Compute force from mass and acceleration.', semantic_unit='Physics / Force / Force From Mass And Acceleration', title='Physics / Force / Force From Mass And Acceleration', document_title='Physics / Force / Force From Mass And Acceleration')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            question: Value for `question` used by `looks_like_generic_markdown_question`. Expected type: `str`.
            semantic_unit: Value for `semantic_unit` used by `looks_like_generic_markdown_question`. Expected type: `str`.
            title: Value for `title` used by `looks_like_generic_markdown_question`. Expected type: `str`.
            document_title: Value for `document_title` used by `looks_like_generic_markdown_question`. Expected type: `str`.

        Returns:
            bool: Result produced by `looks_like_generic_markdown_question`.
        """
        normalized_question = collapse_ws(question).strip().lower()
        if not normalized_question:
            return True
        canonical = markdown_canonical_question(document_title, semantic_unit or title).strip().lower()
        if normalized_question == canonical:
            return True
        if normalized_question == collapse_ws(semantic_unit).strip().lower():
            return True
        if normalized_question == collapse_ws(title).strip().lower():
            return True
        if normalized_question.startswith("what is "):
            return True
        return bool(re.match(r"^what is\s+\d+[\.\s]", normalized_question))

    def looks_like_heading_markdown_title(
        self,
        title: str,
        *,
        encounter_heading: str = "",
        document_title: str = "",
    ) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling looks like heading markdown title.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `looks_like_heading_markdown_title(title='Physics / Force / Force From Mass And Acceleration', encounter_heading='force', document_title='Physics / Force / Force From Mass And Acceleration')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            title: Value for `title` used by `looks_like_heading_markdown_title`. Expected type: `str`.
            encounter_heading: Value for `encounter_heading` used by `looks_like_heading_markdown_title`. Expected type: `str`. Defaults to `''`.
            document_title: Value for `document_title` used by `looks_like_heading_markdown_title`. Expected type: `str`. Defaults to `''`.

        Returns:
            bool: Result produced by `looks_like_heading_markdown_title`.
        """
        normalized_title = collapse_ws(title).strip().lower()
        if not normalized_title:
            return True
        normalized_heading = collapse_ws(encounter_heading).strip().lower()
        stripped_heading = strip_markdown_outline_prefix(encounter_heading).lower()
        normalized_document_title = collapse_ws(document_title).strip().lower()
        if normalized_heading and normalized_title == normalized_heading:
            return True
        if stripped_heading and normalized_title == stripped_heading:
            return True
        if re.match(r"^\d+(?:\.\d+)*[\.\s:]", normalized_title):
            return True
        if normalized_title in {"summary", "one-sentence summary", "named quantities"}:
            return True
        if normalized_document_title and normalized_title == normalized_document_title and normalized_heading:
            return True
        return False

    def looks_like_generic_markdown_current_identity(
        self,
        current_identity: str,
        *,
        encounter_heading: str = "",
    ) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling looks like generic markdown current identity.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `looks_like_generic_markdown_current_identity(current_identity='Force From Mass And Acceleration', encounter_heading='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            current_identity: Value for `current_identity` used by `looks_like_generic_markdown_current_identity`. Expected type: `str`.
            encounter_heading: Value for `encounter_heading` used by `looks_like_generic_markdown_current_identity`. Expected type: `str`. Defaults to `''`.

        Returns:
            bool: Result produced by `looks_like_generic_markdown_current_identity`.
        """
        normalized_identity = strip_markdown_outline_prefix(current_identity).strip().lower()
        if not normalized_identity:
            return True
        generic_phrases = {
            "capability",
            "core capability",
            "executable relation",
            "executable python relation",
            "executable bash relation",
            "executable shell relation",
            "executable ansible relation",
            "inputs and outputs",
            "input and output",
            "natural language paraphrases",
            "natural-language paraphrases",
            "summary",
            "one-sentence summary",
            "overview",
            "introduction",
            "notes",
            "key points",
            "takeaways",
            "named quantities",
            "notation",
            "variables",
            "definitions",
            "worked example",
            "example",
            "examples",
            "comparison",
            "comparisons",
            "distinction",
            "distinctions",
            "distinguishing the measures",
            "distinguishing the laws",
            "reusable substrate",
            "reusable family",
            "broader reusable substrate",
            "broader reusable family",
            "narrower determinate chemistry",
            "narrower determinate chemistry law",
            "narrower determinate law",
            "determinate chemistry law",
        }
        if normalized_identity in generic_phrases:
            return True
        if normalized_identity.startswith(
            (
                "summary of ",
                "overview of ",
                "introduction to ",
                "named ",
                "core ",
                "executable ",
                "inputs ",
                "natural language ",
                "natural-language ",
                "notation ",
                "variables ",
                "distinguishing ",
                "comparison ",
                "examples ",
                "worked example ",
                "notes ",
            )
        ):
            return True

        identity_tokens = {
            token
            for token in re.findall(r"[a-z][a-z-]+", normalized_identity)
            if len(token) > 2
        }
        generic_tokens = {
            "summary",
            "sentence",
            "core",
            "capability",
            "executable",
            "python",
            "bash",
            "shell",
            "ansible",
            "inputs",
            "outputs",
            "input",
            "output",
            "natural",
            "language",
            "paraphrases",
            "overview",
            "introduction",
            "notes",
            "named",
            "quantities",
            "notation",
            "variables",
            "definitions",
            "worked",
            "example",
            "examples",
            "comparison",
            "comparisons",
            "distinction",
            "distinguishing",
            "measures",
            "laws",
            "reusable",
            "substrate",
            "family",
            "broader",
            "narrower",
            "determinate",
            "chemistry",
            "key",
            "points",
            "takeaways",
        }
        if identity_tokens and identity_tokens.issubset(generic_tokens):
            return True

        normalized_heading = strip_markdown_outline_prefix(encounter_heading).strip().lower()
        if normalized_heading and normalized_identity == normalized_heading and (
            normalized_heading in generic_phrases
            or identity_tokens.issubset(generic_tokens)
        ):
            return True
        return False

    def markdown_heading_is_reusable_substrate(self, heading: str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown heading is reusable substrate.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `markdown_heading_is_reusable_substrate(heading='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            heading: Value for `heading` used by `markdown_heading_is_reusable_substrate`. Expected type: `str`.

        Returns:
            bool: Result produced by `markdown_heading_is_reusable_substrate`.
        """
        normalized_heading = strip_markdown_outline_prefix(heading).strip().lower()
        if not normalized_heading:
            return False
        return normalized_heading in {
            "reusable substrate",
            "reusable family",
        }

    def markdown_heading_supports_relation_hints(self, heading: str) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown heading supports relation hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_heading_supports_relation_hints(heading='force')`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            heading: Value for `heading` used by `markdown_heading_supports_relation_hints`. Expected type: `str`.

        Returns:
            bool: Result produced by `markdown_heading_supports_relation_hints`.
        """
        normalized_heading = strip_markdown_outline_prefix(heading).strip().lower()
        if not normalized_heading:
            return False
        return normalized_heading in {
            "reusing earlier lesson",
            "reusing earlier lessons",
            "one-sentence summary",
            "one sentence summary",
        }

    def repair_markdown_broader_category_against_document(
        self,
        proposed_broader_category: str,
        *,
        document_title: str,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with repairing markdown broader category against document.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `repair_markdown_broader_category_against_document(proposed_broader_category='force', document_title='Physics / Force / Force From Mass And Acceleration')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            proposed_broader_category: Value for `proposed_broader_category` used by `repair_markdown_broader_category_against_document`. Expected type: `str`.
            document_title: Value for `document_title` used by `repair_markdown_broader_category_against_document`. Expected type: `str`.

        Returns:
            str: Result produced by `repair_markdown_broader_category_against_document`.
        """
        normalized_proposed = normalize_markdown_title_identity(proposed_broader_category)
        normalized_document = normalize_markdown_title_identity(document_title)
        if not normalized_document:
            return normalized_proposed
        if not normalized_proposed:
            return normalized_proposed
        if semantic_namespace_key(normalized_proposed) == semantic_namespace_key(normalized_document):
            return normalized_document
        doc_tokens = markdown_title_tokens(normalized_document)
        proposed_tokens = markdown_title_tokens(normalized_proposed)
        if not doc_tokens or not proposed_tokens:
            return normalized_proposed
        shared_prefix = 0
        for left, right in zip(doc_tokens, proposed_tokens):
            if left.lower() != right.lower():
                break
            shared_prefix += 1
        if shared_prefix < 2:
            return normalized_proposed
        doc_single_digits = sum(1 for token in doc_tokens if re.fullmatch(r"\d", token))
        proposed_single_digits = sum(1 for token in proposed_tokens if re.fullmatch(r"\d", token))
        doc_single_letters = sum(1 for token in doc_tokens if re.fullmatch(r"[A-Za-z]", token))
        proposed_single_letters = sum(1 for token in proposed_tokens if re.fullmatch(r"[A-Za-z]", token))
        proposed_digit_letter_noise = any(
            re.fullmatch(r"\d+[A-Za-z]+", token) or re.fullmatch(r"[A-Za-z]+\d+", token)
            for token in proposed_tokens
        )
        doc_alpha_tokens = {token.lower() for token in doc_tokens if re.search(r"[A-Za-z]", token)}
        proposed_alpha_tokens = {token.lower() for token in proposed_tokens if re.search(r"[A-Za-z]", token)}
        alpha_loss = len(doc_alpha_tokens.difference(proposed_alpha_tokens))
        suspicious = (
            proposed_digit_letter_noise
            or proposed_single_digits > doc_single_digits
            or proposed_single_letters > doc_single_letters
            or (shared_prefix >= 3 and alpha_loss >= 1 and len(proposed_tokens) >= len(doc_tokens))
        )
        return normalized_document if suspicious else normalized_proposed

    def normalize_markdown_relation_hint(self, text: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with normalizing markdown relation hint.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `normalize_markdown_relation_hint(text='Compute force from mass and acceleration.')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `normalize_markdown_relation_hint`. Expected type: `str`.

        Returns:
            str: Result produced by `normalize_markdown_relation_hint`.
        """
        cleaned = collapse_ws(str(text).strip())
        if not cleaned:
            return ""
        cleaned = strip_markdown_outline_prefix(cleaned)
        cleaned = cleaned.replace("`", " ")
        cleaned = cleaned.replace("_", " ")
        cleaned = cleaned.replace("/", " ")
        cleaned = re.sub(r"\\[A-Za-z]+", " ", cleaned)
        cleaned = re.sub(r"\$+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:;!-")
        lowered = cleaned.casefold()
        direct_normalizations = {
            "weighted sum": "Weighted Aggregation",
            "weighted average": "Weighted Aggregation",
            "expectation-like": "Expectation",
            "expectation like": "Expectation",
        }
        if lowered in direct_normalizations:
            return normalize_markdown_title_identity(direct_normalizations[lowered])
        lowered = cleaned.casefold()
        for suffix in (
            " in physics",
            " in probability",
            " in information theory",
            " in information measurement",
            " family",
            " families",
            " relation",
            " relations",
            " law",
            " laws",
            " structure",
            " structures",
            " form",
            " forms",
        ):
            if lowered.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip(" .,:;!-")
                lowered = cleaned.casefold()
        connector_patterns = (
            r"\b(?:formed|built|computed|obtained|derived|produced|defined|constructed|expressed|normalized|carried|reused?)\s+by\s+(.+)$",
            r"\b(?:formed|built|computed|obtained|derived|produced|defined|constructed|expressed|normalized|carried|reused?)\s+through\s+(.+)$",
            r"\b(?:depends|dependent)\s+on\s+(.+)$",
            r"\b(?:uses|using|reuse|reuses|reused)\s+(.+)$",
        )
        for pattern in connector_patterns:
            match = re.search(pattern, cleaned, flags=re.IGNORECASE)
            if not match:
                continue
            narrowed = collapse_ws(match.group(1)).strip(" .,:;!-")
            if narrowed and semantic_namespace_key(narrowed) != semantic_namespace_key(cleaned):
                cleaned = narrowed
                lowered = cleaned.casefold()
                break
        normalized = titleize_semantic_unit(cleaned) or cleaned
        return normalize_markdown_title_identity(normalized)

    def expand_markdown_relation_hint_variants(self, hint: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling expand markdown relation hint variants.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `expand_markdown_relation_hint_variants(hint='force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            hint: Value for `hint` used by `expand_markdown_relation_hint_variants`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `expand_markdown_relation_hint_variants`.
        """
        normalized_hint = self.normalize_markdown_relation_hint(hint)
        if not normalized_hint:
            return []
        variants = [normalized_hint]
        tokens = normalized_hint.split()
        lowered = normalized_hint.casefold()
        if lowered.endswith(" relation"):
            variants.append(normalized_hint[: -len(" Relation")].strip())
        if lowered.endswith(" relations"):
            variants.append(normalized_hint[: -len(" Relations")].strip())
        if lowered.endswith(" relation") or lowered.endswith(" relations") or len(tokens) == 1:
            root = re.sub(r"\s+Relations?$", "", normalized_hint).strip()
            if root:
                variants.append(f"{root} Formation")
        for connector in (" By ", " Through ", " Via ", " Using "):
            if connector in normalized_hint:
                tail = normalized_hint.split(connector, 1)[1].strip()
                if tail:
                    variants.append(tail)
        return ordered_unique(
            variant
            for variant in variants
            if normalize_markdown_title_identity(variant)
        )

    def markdown_text_relation_hints(self, text: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown text relation hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_text_relation_hints(text='Compute force from mass and acceleration.')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            text: Value for `text` used by `markdown_text_relation_hints`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `markdown_text_relation_hints`.
        """
        raw_text = collapse_ws(str(text).strip())
        if not raw_text:
            return []
        lowered = raw_text.casefold()
        patterns = (
            r"\bthe reusable (?:family|substrate) is ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\b([a-z0-9][a-z0-9\-\s]+?) is the broader reusable substrate\b",
            r"\bis (?:itself\s+|also\s+)?(?:an?|the)\s+([a-z0-9][a-z0-9\-\s]+?)\s+(?:relation|law)\b",
            r"\breuses? (?:the earlier )?([a-z0-9][a-z0-9\-\s]+?)\s+family\b",
            r"\breuses? ([a-z0-9][a-z0-9\-\s]+?)(?: while| through| and|,|;|\\.|$)",
            r"\bmay(?: itself)? come from ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bmay(?: itself)? be derived from ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bmay(?: also)? be formed through ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bdepends on ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bdownstream of ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bbuilt on ([a-z0-9][a-z0-9\-\s]+?)(?:[.;,:]|$)",
            r"\bformed through ([a-z0-9][a-z0-9\-\s]+?)\s+relations?\b",
            r"\b([a-z0-9][a-z0-9\-\s]+?) appears inside\b",
            r"\b([a-z0-9][a-z0-9\-\s]+?) for both centers\b",
            r"\b([a-z0-9][a-z0-9\-\s]+?) over probability\b",
            r"\b([a-z0-9][a-z0-9\-\s]+?)-like structure\b",
        )
        hints: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, lowered, flags=re.IGNORECASE):
                captured = raw_text[match.start(1) : match.end(1)]
                hints.extend(self.expand_markdown_relation_hint_variants(captured))
        return ordered_unique(hints)

    def markdown_encounter_relation_hints(self, encounter: Mapping[str, Any] | None) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown encounter relation hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_encounter_relation_hints(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            encounter: Value for `encounter` used by `markdown_encounter_relation_hints`. Expected type: `Mapping[str, Any] | None`.

        Returns:
            list[str]: Result produced by `markdown_encounter_relation_hints`.
        """
        if not isinstance(encounter, Mapping):
            return []
        texts: list[str] = []
        heading = collapse_ws(str(encounter.get("heading", "")).strip())
        if heading:
            texts.append(heading)
        for key in ("paragraphs", "bullets"):
            values = encounter.get(key, [])
            if isinstance(values, list):
                texts.extend(collapse_ws(str(item).strip()) for item in values if collapse_ws(str(item).strip()))
        hints: list[str] = []
        for text in texts:
            hints.extend(self.markdown_text_relation_hints(text))
        return ordered_unique(hints)

    def markdown_document_relation_hints(
        self,
        document: MarkdownDocumentIR,
        *,
        exclude_encounter_id: str = "",
    ) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown document relation hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_document_relation_hints(document=MarkdownDocumentIR(title='Physics Force Lesson'), exclude_encounter_id='artifact-force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            document: Value for `document` used by `markdown_document_relation_hints`. Expected type: `MarkdownDocumentIR`.
            exclude_encounter_id: Value for `exclude_encounter_id` used by `markdown_document_relation_hints`. Expected type: `str`. Defaults to `''`.

        Returns:
            list[str]: Result produced by `markdown_document_relation_hints`.
        """
        hints: list[str] = []
        for encounter in markdown_learning_encounter_view(document):
            encounter_id = str(encounter.get("encounter_id", "")).strip()
            if exclude_encounter_id and encounter_id == exclude_encounter_id:
                continue
            heading = collapse_ws(str(encounter.get("heading", "")).strip())
            if not self.markdown_heading_supports_relation_hints(heading):
                continue
            hints.extend(self.markdown_encounter_relation_hints(encounter))
        return ordered_unique(hints)

    def markdown_relation_hint_texts(
        self,
        document: MarkdownDocumentIR,
        *,
        encounter: Mapping[str, Any] | None,
        exclude_encounter_id: str = "",
    ) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown relation hint texts.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_relation_hint_texts(document=MarkdownDocumentIR(title='Physics Force Lesson'), encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, exclude_encounter_id='artifact-force')`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            document: Value for `document` used by `markdown_relation_hint_texts`. Expected type: `MarkdownDocumentIR`.
            encounter: Value for `encounter` used by `markdown_relation_hint_texts`. Expected type: `Mapping[str, Any] | None`.
            exclude_encounter_id: Value for `exclude_encounter_id` used by `markdown_relation_hint_texts`. Expected type: `str`. Defaults to `''`.

        Returns:
            list[str]: Result produced by `markdown_relation_hint_texts`.
        """
        texts: list[str] = []
        if isinstance(encounter, Mapping):
            heading = collapse_ws(str(encounter.get("heading", "")).strip())
            if heading:
                texts.append(heading)
            for key in ("paragraphs", "bullets"):
                values = encounter.get(key, [])
                if isinstance(values, list):
                    texts.extend(collapse_ws(str(item).strip()) for item in values if collapse_ws(str(item).strip()))
        for support in markdown_learning_encounter_view(document):
            encounter_id = str(support.get("encounter_id", "")).strip()
            if exclude_encounter_id and encounter_id == exclude_encounter_id:
                continue
            heading = collapse_ws(str(support.get("heading", "")).strip())
            if not self.markdown_heading_supports_relation_hints(heading):
                continue
            if heading:
                texts.append(heading)
            for key in ("paragraphs", "bullets"):
                values = support.get(key, [])
                if isinstance(values, list):
                    texts.extend(collapse_ws(str(item).strip()) for item in values if collapse_ws(str(item).strip()))
        return ordered_unique(text for text in texts if text)

    def derive_markdown_current_identity_from_encounter(
        self,
        *,
        encounter: Mapping[str, Any] | None,
        proposed_title: str,
    ) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling derive markdown current identity from encounter.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `derive_markdown_current_identity_from_encounter(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, proposed_title='Physics / Force / Force From Mass And Acceleration')`
            Output: 'Physics / Force / Force From Mass And Acceleration'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            encounter: Value for `encounter` used by `derive_markdown_current_identity_from_encounter`. Expected type: `Mapping[str, Any] | None`.
            proposed_title: Value for `proposed_title` used by `derive_markdown_current_identity_from_encounter`. Expected type: `str`.

        Returns:
            str: Result produced by `derive_markdown_current_identity_from_encounter`.
        """
        encounter_heading = collapse_ws(str(encounter.get("heading", "")).strip()) if isinstance(encounter, Mapping) else ""
        stripped_heading = strip_markdown_outline_prefix(encounter_heading)
        def usable_symbolic_identity(output_field: str, input_fields: list[str]) -> bool:
            candidates = [collapse_ws(str(output_field).strip())] + [
                collapse_ws(str(item).strip()) for item in input_fields
            ]
            if not candidates[0] or len(candidates) < 2:
                return False
            for candidate in candidates:
                if not candidate:
                    return False
                if len(candidate) > 24:
                    return False
                if is_generic_synthesis_field_name(candidate):
                    return False
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
                    return False
            return True
        if stripped_heading and not self.looks_like_generic_markdown_current_identity(
            stripped_heading,
            encounter_heading=encounter_heading,
        ):
            return stripped_heading

        if isinstance(encounter, Mapping):
            for hint in self.markdown_encounter_relation_hints(encounter):
                normalized_hint = normalize_markdown_title_identity(hint)
                if not normalized_hint:
                    continue
                if self.looks_like_generic_markdown_current_identity(
                    normalized_hint,
                    encounter_heading=encounter_heading,
                ):
                    continue
                return normalized_hint

            output_field, input_fields, _expression = markdown_direct_expression_mapping(encounter)
            if usable_symbolic_identity(output_field, input_fields):
                return titleize_semantic_unit(
                    f"{output_field} from {' and '.join(input_fields)}"
                ) or f"{output_field} from {' and '.join(input_fields)}"

            output_field, input_fields = markdown_symbolic_mapping_from_encounter(encounter)
            if usable_symbolic_identity(output_field, input_fields):
                return titleize_semantic_unit(
                    f"{output_field} from {' and '.join(input_fields)}"
                ) or f"{output_field} from {' and '.join(input_fields)}"

            encounter_path = [
                collapse_ws(str(item).strip())
                for item in encounter.get("path", [])
                if collapse_ws(str(item).strip())
            ] if isinstance(encounter.get("path", []), list) else []
            for candidate in reversed(encounter_path):
                cleaned_candidate = strip_markdown_outline_prefix(candidate)
                if not cleaned_candidate:
                    continue
                if self.looks_like_generic_markdown_current_identity(
                    cleaned_candidate,
                    encounter_heading=encounter_heading,
                ):
                    continue
                return titleize_semantic_unit(cleaned_candidate) or cleaned_candidate

            for alias in markdown_encounter_aliases(encounter, limit=12):
                cleaned_alias = strip_markdown_outline_prefix(alias)
                if not cleaned_alias:
                    continue
                if "?" in cleaned_alias or "=" in cleaned_alias or len(cleaned_alias) > 96:
                    continue
                if self.looks_like_generic_markdown_current_identity(
                    cleaned_alias,
                    encounter_heading=encounter_heading,
                ):
                    continue
                return titleize_semantic_unit(cleaned_alias) or cleaned_alias

        fallback = strip_markdown_outline_prefix(proposed_title)
        return titleize_semantic_unit(fallback) or fallback

    def markdown_title_repair_semantic_hints(
        self,
        *,
        encounter: Mapping[str, Any] | None,
        proposed_title: str,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling markdown title repair semantic hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `markdown_title_repair_semantic_hints(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, proposed_title='Physics / Force / Force From Mass And Acceleration')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            encounter: Value for `encounter` used by `markdown_title_repair_semantic_hints`. Expected type: `Mapping[str, Any] | None`.
            proposed_title: Value for `proposed_title` used by `markdown_title_repair_semantic_hints`. Expected type: `str`.

        Returns:
            dict[str, Any]: Result produced by `markdown_title_repair_semantic_hints`.
        """
        if not isinstance(encounter, Mapping):
            return {
                "derived_identity_hint": strip_markdown_outline_prefix(proposed_title),
                "direct_expression_output": "",
                "direct_expression_inputs": [],
                "alias_hints": [],
            }
        output_field, input_fields, expression = markdown_direct_expression_mapping(encounter)
        return {
            "derived_identity_hint": self.derive_markdown_current_identity_from_encounter(
                encounter=encounter,
                proposed_title=proposed_title,
            ),
            "direct_expression_output": output_field,
            "direct_expression_inputs": input_fields,
            "direct_expression": expression,
            "alias_hints": markdown_encounter_aliases(encounter, limit=6),
        }

    def artifact_identity_surfaces(self, artifact: Artifact) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling artifact identity surfaces.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `artifact_identity_surfaces(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_identity_surfaces`. Expected type: `Artifact`.

        Returns:
            list[str]: Result produced by `artifact_identity_surfaces`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = content.get("structured_learning", {}) if isinstance(content.get("structured_learning", {}), Mapping) else {}
        candidates = [
            artifact.title,
            str(content.get("formal_title_identity", "")).strip(),
            str(content.get("title_current_identity", "")).strip(),
            str(content.get("semantic_unit", "")).strip(),
            str(content.get("question", "")).strip(),
            str(structured.get("title_identity", "")).strip(),
            str(structured.get("title_prolog_head", "")).strip(),
            str(structured.get("title_prolog_head_canonical", "")).strip(),
        ]
        aliases = content.get("aliases", [])
        if isinstance(aliases, list):
            candidates.extend(str(item).strip() for item in aliases if str(item).strip())
        input_titles = content.get("input_titles", {})
        if isinstance(input_titles, Mapping):
            candidates.extend(str(item).strip() for item in input_titles.values() if str(item).strip())
        output_titles = content.get("output_titles", {})
        if isinstance(output_titles, Mapping):
            candidates.extend(str(item).strip() for item in output_titles.values() if str(item).strip())
        title_similies = content.get("title_similies", [])
        if isinstance(title_similies, list):
            candidates.extend(str(item).strip() for item in title_similies if str(item).strip())
        return ordered_unique(collapse_ws(item) for item in candidates if collapse_ws(item))

    def artifact_relation_surfaces(self, artifact: Artifact) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling artifact relation surfaces.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `artifact_relation_surfaces(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_relation_surfaces`. Expected type: `Artifact`.

        Returns:
            list[str]: Result produced by `artifact_relation_surfaces`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        structured = content.get("structured_learning", {}) if isinstance(content.get("structured_learning", {}), Mapping) else {}
        candidates = list(self.artifact_identity_surfaces(artifact))
        candidates.extend(
            [
                str(content.get("answer", "")).strip(),
                str(content.get("title_broader_category", "")).strip(),
                str(content.get("relation_rationale", "")).strip(),
            ]
        )
        source_sections = content.get("source_sections", [])
        if isinstance(source_sections, list):
            candidates.extend(str(item).strip() for item in source_sections if str(item).strip())
        for key in ("title_identity", "goal", "intended_object", "actual_realization"):
            candidates.append(str(structured.get(key, "")).strip())
        for key in ("givens", "why_it_matters"):
            values = structured.get(key, [])
            if isinstance(values, list):
                candidates.extend(str(item).strip() for item in values if str(item).strip())
        return ordered_unique(collapse_ws(item) for item in candidates if collapse_ws(item))

    def artifact_relation_hint_surfaces(self, artifact: Artifact) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling artifact relation hint surfaces.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `artifact_relation_hint_surfaces(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_relation_hint_surfaces`. Expected type: `Artifact`.

        Returns:
            list[str]: Result produced by `artifact_relation_hint_surfaces`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        candidates: list[str] = []
        relation_family_hints = content.get("relation_family_hints", [])
        if isinstance(relation_family_hints, list):
            candidates.extend(str(item).strip() for item in relation_family_hints if str(item).strip())
        relation_hint_texts = content.get("relation_hint_texts", [])
        if isinstance(relation_hint_texts, list):
            candidates.extend(str(item).strip() for item in relation_hint_texts if str(item).strip())
        relation_rationale = str(content.get("relation_rationale", "")).strip()
        if relation_rationale:
            candidates.append(relation_rationale)
        return ordered_unique(collapse_ws(item) for item in candidates if collapse_ws(item))

    def semantic_relation_match_score(self, hint: str, surface: str) -> int:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling semantic relation match score.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `semantic_relation_match_score(hint='force', surface='force')`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            hint: Value for `hint` used by `semantic_relation_match_score`. Expected type: `str`.
            surface: Value for `surface` used by `semantic_relation_match_score`. Expected type: `str`.

        Returns:
            int: Result produced by `semantic_relation_match_score`.
        """
        normalized_hint = collapse_ws(str(hint).strip())
        normalized_surface = collapse_ws(str(surface).strip())
        if not normalized_hint or not normalized_surface:
            return 0
        prolog_score = prolog_title_match_score(normalized_hint, normalized_surface)
        if prolog_score:
            return prolog_score
        hint_key = semantic_namespace_key(normalized_hint)
        surface_key = semantic_namespace_key(normalized_surface)
        if not hint_key or not surface_key:
            return 0
        hint_prefix_keys = {
            semantic_namespace_key(prefix)
            for prefix in semantic_title_depth_prefix_chain(normalized_hint)
            if semantic_namespace_key(prefix)
        }
        surface_prefix_keys = {
            semantic_namespace_key(prefix)
            for prefix in semantic_title_depth_prefix_chain(normalized_surface)
            if semantic_namespace_key(prefix)
        }
        if surface_key == hint_key:
            return 100
        if surface_key.endswith(hint_key) or hint_key.endswith(surface_key):
            return 92
        if hint_prefix_keys.intersection(surface_prefix_keys):
            return 84
        overlap = len(
            set(learning_lookup_keys(normalized_hint)).intersection(
                set(learning_lookup_keys(normalized_surface))
            )
        )
        if overlap >= 2:
            return 60 + overlap
        return 0

    def artifact_relation_resolution_bias(self, artifact: Artifact) -> int:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling artifact relation resolution bias.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `artifact_relation_resolution_bias(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
            Output: 3

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact: Value for `artifact` used by `artifact_relation_resolution_bias`. Expected type: `Artifact`.

        Returns:
            int: Result produced by `artifact_relation_resolution_bias`.
        """
        content = artifact.content if isinstance(artifact.content, Mapping) else {}
        bias = 0
        source_sections = [
            collapse_ws(str(item).strip())
            for item in content.get("source_sections", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(content.get("source_sections", []), list) else []
        if not source_sections:
            bias -= 6
        if any(self.markdown_heading_is_reusable_substrate(item) for item in source_sections):
            bias += 18
        if any(self.markdown_heading_supports_relation_hints(item) for item in source_sections):
            bias -= 10
        if enum_text(artifact.artifact_type) == "ability":
            bias += 8
        lowered_title = collapse_ws(str(artifact.title).strip()).casefold()
        if lowered_title.endswith("python ability") or lowered_title.endswith("bash ability") or lowered_title.endswith("ansible ability") or lowered_title.endswith("wasm ability"):
            bias -= 32
        encounter_heading = source_sections[0] if source_sections else ""
        current_identity = str(content.get("title_current_identity", "")).strip()
        if self.looks_like_generic_markdown_current_identity(
            current_identity or artifact.title,
            encounter_heading=encounter_heading,
        ):
            bias -= 8
        relation_family_hints = content.get("relation_family_hints", [])
        if isinstance(relation_family_hints, list) and relation_family_hints:
            bias += 4
        return bias

    def resolve_related_artifact_ids_from_title_hints(
        self,
        *,
        related_titles: Sequence[str],
        pool: Sequence[Artifact],
        exclude_artifact_id: str = "",
    ) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with resolving related artifact ids from title hints.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `resolve_related_artifact_ids_from_title_hints(related_titles=['Physics', 'Force', 'Force From Mass And Acceleration'], pool=['mass', 'acceleration', 'force'], exclude_artifact_id='artifact-force')`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            related_titles: Value for `related_titles` used by `resolve_related_artifact_ids_from_title_hints`. Expected type: `Sequence[str]`.
            pool: Value for `pool` used by `resolve_related_artifact_ids_from_title_hints`. Expected type: `Sequence[Artifact]`.
            exclude_artifact_id: Value for `exclude_artifact_id` used by `resolve_related_artifact_ids_from_title_hints`. Expected type: `str`. Defaults to `''`.

        Returns:
            list[str]: Result produced by `resolve_related_artifact_ids_from_title_hints`.
        """
        resolved: list[str] = []
        for hint in related_titles:
            normalized_hint = collapse_ws(str(hint).strip())
            if not normalized_hint:
                continue
            best_score = 0
            best_artifact_id = ""
            for artifact in pool:
                if artifact.id == exclude_artifact_id:
                    continue
                identity_score = max(
                    (self.semantic_relation_match_score(normalized_hint, surface) for surface in self.artifact_identity_surfaces(artifact)),
                    default=0,
                )
                supporting_score = max(
                    (self.semantic_relation_match_score(normalized_hint, surface) for surface in self.artifact_relation_surfaces(artifact)),
                    default=0,
                )
                hint_score = max(
                    (self.semantic_relation_match_score(normalized_hint, surface) for surface in self.artifact_relation_hint_surfaces(artifact)),
                    default=0,
                )
                candidate_score = max(identity_score, supporting_score, min(hint_score, 76))
                candidate_score += self.artifact_relation_resolution_bias(artifact)
                if candidate_score > best_score:
                    best_score = candidate_score
                    best_artifact_id = artifact.id
            if best_artifact_id and best_score >= 84:
                resolved.append(best_artifact_id)
        return ordered_unique(resolved)

    apply_markdown_batch_relations = apply_external_markdown_batch_relations

    def fallback_markdown_title_question_repair(
        self,
        *,
        document: MarkdownDocumentIR,
        encounter: Mapping[str, Any] | None,
        proposed_title: str,
        proposed_question: str,
    ) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling fallback markdown title question repair.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `fallback_markdown_title_question_repair(document=MarkdownDocumentIR(title='Physics Force Lesson'), encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, proposed_title='Physics / Force / Force From Mass And Acceleration', proposed_question='Compute force from mass and acceleration.')`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            document: Value for `document` used by `fallback_markdown_title_question_repair`. Expected type: `MarkdownDocumentIR`.
            encounter: Value for `encounter` used by `fallback_markdown_title_question_repair`. Expected type: `Mapping[str, Any] | None`.
            proposed_title: Value for `proposed_title` used by `fallback_markdown_title_question_repair`. Expected type: `str`.
            proposed_question: Value for `proposed_question` used by `fallback_markdown_title_question_repair`. Expected type: `str`.

        Returns:
            dict[str, Any]: Result produced by `fallback_markdown_title_question_repair`.
        """
        encounter_heading = collapse_ws(str(encounter.get("heading", "")).strip()) if isinstance(encounter, Mapping) else ""
        current_identity = self.derive_markdown_current_identity_from_encounter(
            encounter=encounter,
            proposed_title=proposed_title,
        ) or strip_markdown_outline_prefix(proposed_title) or collapse_ws(proposed_title)
        broader_category = ""
        normalized_document_title = collapse_ws(document.title).strip()
        if normalized_document_title and semantic_namespace_key(normalized_document_title) != semantic_namespace_key(current_identity):
            broader_category = normalized_document_title
        downward_decomposition: list[str] = []
        question = collapse_ws(proposed_question).strip()
        if self.looks_like_generic_markdown_question(
            question,
            semantic_unit=current_identity or proposed_title,
            title=proposed_title,
            document_title=document.title,
        ):
            question = markdown_caller_facing_question(document.title, current_identity or proposed_title)
        return {
            "title_broader_category": broader_category,
            "title_current_identity": current_identity,
            "title_downward_decomposition": downward_decomposition,
            "title_construction_rationale": "Fallback repair grounds the identity in the document family and removes outline residue from the current identity.",
            "title_collision_rationale": "Fallback repair avoids storing the raw section heading as the artifact identity.",
            "title_similies": ordered_unique(
                [
                    current_identity,
                    f"{normalized_document_title} {current_identity}".strip() if normalized_document_title else "",
                ]
            )[:4],
            "question": question,
            "question_title_separation": "The repaired title carries semantic identity while the question remains the likely caller-facing invocation.",
        }

    propose_markdown_title_repair = propose_semantic_markdown_title_repair

    select_markdown_learning_encounter = select_semantic_markdown_learning_encounter
    build_markdown_knowledge_answer_from_encounter = build_markdown_knowledge_answer_from_selected_encounter
    build_markdown_learning_artifact = build_semantic_markdown_learning_artifact
    current_skill_governance_artifacts = controller_current_skill_governance_artifacts
    current_skill_governance_snapshot = controller_current_skill_governance_snapshot
    invalidate_current_skill_governance_snapshot = controller_invalidate_current_skill_governance_snapshot
    artifact_is_executable_function = controller_artifact_is_executable_function
    artifact_has_answer_capability = controller_artifact_has_answer_capability
    learn_from_markdown_document = learn_from_external_markdown_document

    def build_artifact_from_payload(
        self,
        *,
        node: SemanticNode,
        payload: Mapping[str, Any],
        provenance: list[str],
    ) -> Artifact | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building payload data for build artifact from.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `build_artifact_from_payload(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), payload={'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}, provenance=['mass', 'acceleration', 'force'])`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `build_artifact_from_payload`. Expected type: `SemanticNode`.
            payload: Value for `payload` used by `build_artifact_from_payload`. Expected type: `Mapping[str, Any]`.
            provenance: Value for `provenance` used by `build_artifact_from_payload`. Expected type: `list[str]`.

        Returns:
            Artifact | None: Result produced by `build_artifact_from_payload`.
        """
        artifact_type = normalize_artifact_type(payload.get("artifact_type", "knowledge"))
        title = str(payload.get("title", "")).strip()
        representation = normalize_artifact_representation(
            payload.get("representation", "json"),
            artifact_type=artifact_type,
        )
        scope = str(payload.get("scope", "")).strip()
        justification = str(payload.get("justification", "")).strip()
        reusability = normalize_artifact_reuse(payload.get("reusability", "local_reuse"))
        admissibility = normalize_artifact_admission(payload.get("admissibility", "candidate"))
        template_schema = dict(payload.get("template_schema", {})) if isinstance(payload.get("template_schema", {}), Mapping) else {}
        learning_relation = normalize_learning_relation(payload.get("learning_relation", "new_family"))
        explicit_related_artifact_ids = "related_artifact_ids" in payload
        related_artifact_ids = [str(item).strip() for item in payload.get("related_artifact_ids", []) if str(item).strip()] if isinstance(payload.get("related_artifact_ids", []), list) else []
        content = dict(payload.get("content", {})) if isinstance(payload.get("content", {}), Mapping) else {}
        content.setdefault("node_id", node.id)
        content = self.annotate_artifact_content_with_controller_features(content)
        constraints = [str(item).strip() for item in payload.get("constraints", []) if str(item).strip()] if isinstance(payload.get("constraints", []), list) else []
        formal_title_identity = normalize_semantic_title_identity(
            str(content.get("formal_title_identity", "")).strip()
            or str(payload.get("title_identity", "")).strip()
            or title
        )
        if formal_title_identity:
            content.setdefault("formal_title_identity", formal_title_identity)

        if admissibility == "rejected":
            return None
        if not title or not scope or not justification:
            return None
        if is_template_bearing_artifact_type(artifact_type):
            if not self.template_schema_complete(template_schema):
                admissibility = "candidate"
                if not template_schema:
                    template_schema = self.default_template_schema(
                        artifact_type=artifact_type,
                        node=node,
                        scope=scope,
                        governed_function=f"reuse {enum_text(artifact_type)} in a governed way",
                        completion_conditions=["the artifact is instantiated in scope and its use conditions are met"],
                        failure_conditions=["scope or HoldOn conditions are violated"],
                        harvest_conditions=["later runs reuse the same artifact family"],
                    )
            if artifact_type == "duty_template":
                duty_fields = {"preconditions", "completion_conditions", "failure_conditions"}
                if not duty_fields.issubset(template_schema.keys()):
                    admissibility = "candidate"
        else:
            template_schema = {}
        if artifact_type == "ability":
            executor_framework = ability_executor_framework(
                representation=str(representation),
                content=content,
            ) or "python3"
            content["executor_framework"] = executor_framework
            representation = executor_framework_representation(executor_framework)
            if not isinstance(content.get("input_contract", {}), Mapping):
                content["input_contract"] = {"payload": "JSON object read from stdin or --input-json"}
            if not isinstance(content.get("output_contract", {}), Mapping):
                content["output_contract"] = {"result": "JSON object written to stdout"}
            content["input_contract"] = dict(content.get("input_contract", {}))
            content["output_contract"] = dict(content.get("output_contract", {}))
            if executor_framework == "python3":
                content["entrypoint"] = str(content.get("entrypoint", "main")).strip() or "main"
                content["script_language"] = "python"
                content["dependencies"] = self.ability_script_dependencies(content)
                content = self.refresh_expression_ability_content(
                    title=title,
                    scope=scope,
                    content=content,
                )
                python_script = str(content.get("python_script", "")).strip()
                if not python_script:
                    admissibility = "candidate"
                    content["python_script"] = self.default_ability_script(
                        title=title,
                        scope=scope,
                        justification=justification,
                        input_contract=content["input_contract"],
                        output_contract=content["output_contract"],
                    )
                else:
                    if "# /// script" not in python_script or "msgspec" not in python_script or "orjson" not in python_script:
                        signature = self.callable_python_signature(python_script)
                        if signature is not None:
                            function_name, argument_names = signature
                            python_script = self.callable_snippet_ability_script(
                                title=title,
                                scope=scope,
                                justification=justification,
                                python_code=python_script,
                                function_name=function_name,
                                argument_names=argument_names,
                            )
                            if not content["input_contract"]:
                                content["input_contract"] = {name: "required input value" for name in argument_names}
                            if not content["output_contract"]:
                                content["output_contract"] = {"result": "computed result"}
                        else:
                            admissibility = "candidate"
                    content["python_script"] = python_script
            elif executor_framework == "bash":
                content["entrypoint"] = str(content.get("entrypoint", "main")).strip() or "main"
                content["script_language"] = "bash"
                if not isinstance(content.get("dependencies", []), list):
                    content["dependencies"] = []
                if not str(content.get("shell_script", "")).strip():
                    admissibility = "candidate"
            elif executor_framework == "ansible":
                content["entrypoint"] = str(content.get("entrypoint", "playbook")).strip() or "playbook"
                content["script_language"] = "ansible"
                if not isinstance(content.get("dependencies", []), list):
                    content["dependencies"] = []
                if not str(content.get("ansible_playbook", "")).strip():
                    admissibility = "candidate"
            elif executor_framework == "wasm_wasi":
                content["entrypoint"] = str(content.get("entrypoint", "run")).strip() or "run"
                content["script_language"] = "wasm"
                if not isinstance(content.get("dependencies", []), list):
                    content["dependencies"] = []
                if not str(content.get("wasm_abi_version", "")).strip():
                    content["wasm_abi_version"] = "bssc.wasm.v1"
                if not str(content.get("wasm_format", "")).strip():
                    content["wasm_format"] = "wat"
                if not str(content.get("wasm_module", "")).strip():
                    admissibility = "candidate"
            else:
                admissibility = "candidate"
        elif is_python_artifact_representation(representation):
            content["script_language"] = "python"
        if not related_artifact_ids and not explicit_related_artifact_ids:
            related_artifact_ids = self.related_learned_artifact_ids(artifact_type, title, scope)
        if related_artifact_ids and learning_relation == "new_family":
            learning_relation = "instance_of_existing"

        boundary_shape = infer_artifact_boundary_shape(
            artifact_type=artifact_type,
            representation=representation,
            content=content,
            explicit=payload.get("boundary_shape"),
            title=title,
            scope=scope,
            function_bit=payload.get("function_bit"),
        )
        semantic_surface_parts = [
            str(payload.get("semantic_unit", "")).strip(),
            str(content.get("question", "")).strip(),
            title,
        ]
        aliases = content.get("aliases", [])
        if isinstance(aliases, list):
            semantic_surface_parts.extend(str(item).strip() for item in aliases if str(item).strip())
        sections = payload.get("sections", [])
        if isinstance(sections, list):
            semantic_surface_parts.extend(str(item).strip() for item in sections if str(item).strip())
        answer_excerpt = str(content.get("answer", "")).strip()
        if answer_excerpt:
            semantic_surface_parts.append(answer_excerpt[:400])
        semantic_basis = " ".join(item for item in ordered_unique(semantic_surface_parts) if item).strip() or title
        content["structured_learning"] = normalize_not_elaboration_payload(
            semantic_basis,
            content.get("structured_learning") if isinstance(content.get("structured_learning"), Mapping) else payload.get("structured_learning"),
            boundary_shape=boundary_shape,
            title_identity=formal_title_identity or title,
        )
        structured_learning = content.get("structured_learning", {}) if isinstance(content.get("structured_learning", {}), Mapping) else {}
        if artifact_type == "ability":
            input_contract = content.get("input_contract", {})
            output_contract = content.get("output_contract", {})
            if isinstance(input_contract, Mapping) and input_contract:
                content["input_titles"] = {
                    str(key).strip(): canonical_title
                    for key, canonical_title in zip(
                        [str(key).strip() for key in input_contract.keys() if str(key).strip()],
                        self.canonicalize_semantic_io_titles(
                            anchor_title=title,
                            item_names=[str(key).strip() for key in input_contract.keys() if str(key).strip()],
                            exclude_titles=[title],
                        ),
                        strict=False,
                    )
                    if str(key).strip() and canonical_title
                }
            if isinstance(output_contract, Mapping) and output_contract:
                content["output_titles"] = {
                    str(key).strip(): canonical_title
                    for key, canonical_title in zip(
                        [str(key).strip() for key in output_contract.keys() if str(key).strip()],
                        self.canonicalize_semantic_io_titles(
                            anchor_title=title,
                            item_names=[str(key).strip() for key in output_contract.keys() if str(key).strip()],
                            exclude_titles=[title, *list(content.get("input_titles", {}).values())] if isinstance(content.get("input_titles", {}), Mapping) else [title],
                        ),
                        strict=False,
                    )
                    if str(key).strip() and canonical_title
                }
        component_nots = structured_learning.get("component_nots", [])
        if isinstance(component_nots, list) and component_nots:
            structured_learning["component_nots"] = self.canonicalize_semantic_io_titles(
                anchor_title=title,
                item_names=[str(item).strip() for item in component_nots if str(item).strip()],
                exclude_titles=[title],
            )
            content["structured_learning"] = structured_learning
        content = self.annotate_artifact_content_with_controller_features(content)

        artifact = Artifact(
            id=make_id("artifact", f"{enum_text(artifact_type)}-{title}"),
            artifact_type=artifact_type,
            title=title,
            representation=representation,
            function_bit=infer_function_bit(
                artifact_type=artifact_type,
                representation=representation,
                content=content,
                explicit=payload.get("function_bit"),
            ),
            boundary_shape=boundary_shape,
            scope=scope,
            provenance=list(dict.fromkeys(provenance)),
            reusability=reusability,
            admissibility=admissibility,
            template_schema=template_schema,
            learning_relation=learning_relation,
            related_artifact_ids=related_artifact_ids,
            content=content,
            justification=justification,
            constraints=constraints,
        )
        return self.state.register_artifact(artifact)

    perform_discovery_harvest = perform_run_discovery_harvest
    persist_artifacts = persist_governed_artifacts

    def ensure_generated_capability(self, node: SemanticNode, *, semantic_role: str, affordance: str, service_axis: str) -> Capability:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ensure generated capability.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ensure_generated_capability(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), semantic_role='Physics / Force / Force From Mass And Acceleration', affordance='force', service_axis='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `ensure_generated_capability`. Expected type: `SemanticNode`.
            semantic_role: Value for `semantic_role` used by `ensure_generated_capability`. Expected type: `str`.
            affordance: Value for `affordance` used by `ensure_generated_capability`. Expected type: `str`.
            service_axis: Value for `service_axis` used by `ensure_generated_capability`. Expected type: `str`.

        Returns:
            Capability: Result produced by `ensure_generated_capability`.
        """
        for capability in self.state.capabilities.values():
            if capability.semantic_role == semantic_role and capability.limits.get("for_node") == node.id:
                return capability
        draft = self.propose_capability_draft(node, semantic_role=semantic_role, affordance=affordance)
        payload = draft.payload
        admitted_affordance = str(payload.get("affordance") or affordance)
        admitted_role = str(payload.get("semantic_role") or semantic_role)
        admitted_input_form = str(payload.get("input_form") or node.not_label)
        admitted_output_form = str(payload.get("output_form") or "support-bearing boundary return")
        limits = dict(payload.get("limits", {}))
        limits.setdefault("for_node", node.id)
        limits.setdefault("generated", True)
        capability = self.state.register_capability(
            affordance=admitted_affordance,
            input_form=admitted_input_form,
            output_form=admitted_output_form,
            semantic_role=admitted_role,
            limits=limits,
            validated=True,
            provenance=[node.id, draft.id],
            service_axis=service_axis,
            realizer="generated_capability",
        )
        self.admit_proposal(
            draft,
            rationale="The capability draft was admitted into a generated capability for governed continuation.",
        )
        self.state.record_step(
            kind="genesis",
            node_id=node.id,
            intent="Generate missing capability only when governed continuation needs it.",
            action="register generated capability",
            result="missing capability emerged into controlled use",
            evaluation="capability genesis remained subordinate to the main realization path",
            commit_effect=capability.id,
            payload={"capability_id": capability.id, "semantic_role": semantic_role},
        )
        self.state.record_outlet(
            kind="capability_request",
            semantic_identity=node.semantic_unit,
            payload={"node_id": node.id, "capability_id": capability.id, "semantic_role": semantic_role},
            provenance=[capability.id, node.id],
        )
        return capability

    run = run_governed_semantic_runtime
    resume = resume_governed_semantic_runtime
    runtime_host_interaction_context_payload = runtime_host_interaction_context_payload
    pop_best_frontier = pop_runtime_frontier_candidate
    refresh_frontier = refresh_governed_frontier
    reduce_not = reduce_governed_not

    def should_reflect(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether reflect.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `should_reflect(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `should_reflect`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `should_reflect`.
        """
        assessment = self.node_assessment_payload(node)
        return self.proposal_flag(
            assessment,
            "should_reflect",
            default=self.fallback_node_assessment(node)["should_reflect"],
        )

    def reflect(self, node: SemanticNode) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling reflect.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `reflect(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `reflect`. Expected type: `SemanticNode`.

        Returns:
            dict[str, Any]: Result produced by `reflect`.
        """
        self.use_capability("reflection", node=node, contribution="reassess the active composition subset")
        children = self.refinement_children(node)
        faithfulness = "high"
        if children:
            values = [
                normalize_three_level(child.metadata.get("faithfulness", ThreeLevel.HIGH), default=ThreeLevel.HIGH)
                for child in children
            ]
            faithfulness = min_level(values, default="high")
        report = {
            "child_count": len(children),
            "certainty": self.state.certainty.get(node.id, ThreeLevel.LOW),
            "blocked": len(self.state.blockers.get(node.id, [])),
            "faithfulness": faithfulness,
            "still_bears_on_higher_not": level_at_least(faithfulness, self.state.governance.faithfulness_requirement) if children else True,
        }
        self.state.record_step(
                kind="reflection",
                node_id=node.id,
                intent="Retrospectively reassess the current composition subset.",
                action="reflect over active refinement subset",
                result="reflection report recorded",
                evaluation="local drift, sufficiency, and certainty progression were reassessed",
                payload=report,
            )
        proposal = self.request_proposal(
            proposal_type=ProposalType.REFLECTION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Review the current work on this item and judge whether the plan is coherent.

                Field guidance:
                - coherence_assessment: short judgment of how coherent the current breakdown is.
                - overscoping_detected: true if the current plan is too broad or drifting.
                - relevance_judgment: say whether the active work still serves the overall task.
                - holdon_consistency_notes: note reasons the system should pause rather than continue.
                - boundary_assessment: mention any need for outside input, tools, or missing context.
                - recommended_mode: choose fast or deep.
                - issues_list: list concrete issues to watch.

                Rules:
                - Use the current children as primary evidence for coherence, drift, stalling, and relevance.
                - Compare children against each other, not just against the parent in isolation.

                Active item:
                {node.semantic_unit}

                Current children:
                {json.dumps(self.child_context_payload(node), indent=2, sort_keys=True)}
                """
            ),
            fallback_payload={
                "coherence_assessment": "locally coherent" if report["still_bears_on_higher_not"] else "drifting",
                "overscoping_detected": False,
                "relevance_judgment": "still aligned with the overall task" if report["still_bears_on_higher_not"] else "alignment is doubtful",
                "holdon_consistency_notes": [],
                "boundary_assessment": "no external boundary issue detected",
                "recommended_mode": self.select_supplement_mode("reflection", node).value,
                "issues_list": [],
                "rationale": "Fallback review mirrors the current local assessment.",
            },
            mode=self.select_supplement_mode("reflection", node),
        )
        report["reflection_proposal_id"] = proposal.id
        report["advisory"] = proposal.payload
        node.metadata["reflection_proposal_id"] = proposal.id
        self.admit_proposal(
            proposal,
            rationale="Reflection proposals are advisory diagnostics and may be admitted as working reflection state.",
        )
        return report

    def contemplate(self, node: SemanticNode) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling contemplate.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `contemplate(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `contemplate`. Expected type: `SemanticNode`.

        Returns:
            list[str]: Result produced by `contemplate`.
        """
        self.use_capability("contemplation", node=node, contribution="evaluate candidate governed trajectories")
        control = self.control_decision_payload(node)
        trajectories = []
        if self.is_committable(node):
            trajectories.append("commit_closure")
        if self.proposal_flag(control, "should_decompose", default=self.structural_can_decompose(node)) and not self.refinement_children(node):
            trajectories.append("decompose")
        if self.proposal_flag(control, "can_refine_directly") and self.structural_direct_refinement_supported(node):
            trajectories.append("refine_directly")
        if self.proposal_flag(control, "needs_reframe"):
            trajectories.append("reframe_upward")
        if self.proposal_flag(control, "should_pause"):
            trajectories.append("pause")
        if not trajectories:
            trajectories.append("mark_incomplete")
        proposal = self.request_proposal(
            proposal_type=ProposalType.CONTEMPLATION,
            node=node,
            target_scope=node.semantic_unit,
            instructions=plain_prompt(
                f"""
                Step back and compare the most plausible next paths for this item.
                Pick a primary path, but also record reasonable alternatives.

                Field guidance:
                - primary_trajectory: the best next path.
                - alternates: backup paths worth considering.
                - plausibility_ranking: order the candidate paths from most to least plausible.
                - stop_conditions: say when the chosen path should be reconsidered.
                - scope_elevation_rationale: explain whether and why the system should zoom out.

                Rules:
                - Use the current children explicitly when comparing paths.
                - If children already exist, assess whether continuation should proceed through those children, revise them, or pause; do not treat the item as isolated.
                - If there are no children, say so implicitly through the path choice rather than inventing missing child structure.

                Active item:
                {node.semantic_unit}

                Current children:
                {json.dumps(self.child_context_payload(node), indent=2, sort_keys=True)}
                """
            ),
            fallback_payload={
                "primary_trajectory": trajectories[0],
                "alternates": trajectories[1:],
                "plausibility_ranking": trajectories,
                "stop_conditions": ["reassess after local propagation"],
                "scope_elevation_rationale": "Only elevate scope when current framing is insufficient.",
                "rationale": "Fallback path comparison mirrors the controller's current candidate actions.",
            },
            mode=self.select_supplement_mode("contemplation", node),
        )
        advisory_trajectories = [proposal.payload.get("primary_trajectory")] + list(proposal.payload.get("alternates", []))
        for item in advisory_trajectories:
            if isinstance(item, str) and item and item not in trajectories:
                trajectories.append(item)
        self.state.record_step(
            kind="contemplation",
            node_id=node.id,
            intent="Prospectively consider admissible next trajectories.",
            action="generate bounded candidate trajectories",
            result="candidate trajectories identified",
            evaluation="future path selection remained governed by relevance and plausibility",
            payload={"trajectories": trajectories, "proposal_id": proposal.id},
        )
        node.metadata["contemplation_proposal_id"] = proposal.id
        self.admit_proposal(
            proposal,
            rationale="Contemplation proposals may be admitted as advisory path candidates without authorizing them.",
        )
        return trajectories

    decompose_or_refine = decompose_or_refine_governed_semantic_runtime
    filter_by_faithfulness = filter_children_by_runtime_faithfulness
    order_children = order_runtime_children
    should_pause = should_governed_pause
    needs_reframing = needs_governed_reframing
    pause_boundary_for = resolve_governed_pause_boundary
    pause_reason = describe_governed_pause_reason
    commit_closure = commit_governed_closure
    materialize_root_product = materialize_governed_root_product
    commit_pause = commit_governed_pause
    commit_incompletion = commit_governed_incompletion
    is_committable = is_governed_committable

    def should_decompose_further(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether decompose further.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `should_decompose_further(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `should_decompose_further`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `should_decompose_further`.
        """
        if self.refinement_children(node):
            return False
        if not self.structural_can_decompose(node):
            return False
        control = self.control_decision_payload(node)
        return self.proposal_flag(
            control,
            "should_decompose",
            default=self.fallback_control_decision(node)["should_decompose"],
        )

    def can_refine_directly(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether refine directly.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `can_refine_directly(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `can_refine_directly`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `can_refine_directly`.
        """
        if not self.structural_direct_refinement_supported(node):
            return False
        control = self.control_decision_payload(node)
        if self.proposal_flag(
            control,
            "should_decompose",
            default=self.fallback_control_decision(node)["should_decompose"],
        ):
            return False
        if node.metadata.get("decomposition_choice") == "preserve_parent":
            return True
        return self.proposal_flag(
            control,
            "can_refine_directly",
            default=self.fallback_control_decision(node)["can_refine_directly"],
        )

    def default_closure_threshold_for_role(self, role: str) -> str:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with supplying default closure threshold for role.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `default_closure_threshold_for_role(role='force')`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            role: Value for `role` used by `default_closure_threshold_for_role`. Expected type: `str`.

        Returns:
            str: Result produced by `default_closure_threshold_for_role`.
        """
        if role == "support":
            return self.state.governance.support_branch_closure_threshold
        return self.state.governance.closure_threshold_default

    def refine_directly(self, node: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling refine directly.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `refine_directly(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `refine_directly`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if node.metadata.get("direct_refined"):
            return

        evidence: Evidence | None = None
        if node.role == "framing":
            evidence = Evidence(
                id=make_id("evidence", node.semantic_unit),
                node_id=node.id,
                observation=f"Semantic framing derived from the stable prompt-carried unit '{node.semantic_unit}'.",
                source="internal_reflection",
                context={"generated_by": "refine_directly", "role": node.role},
                support_effect=ThreeLevel.HIGH,
                confidence=ThreeLevel.HIGH,
            )
        elif node.role == "governance":
            evidence = Evidence(
                id=make_id("evidence", node.semantic_unit),
                node_id=node.id,
                observation=f"No governance violation is currently represented against '{node.semantic_unit}'.",
                source="governance",
                context={"generated_by": "refine_directly", "role": node.role},
                support_effect=ThreeLevel.HIGH,
                confidence=ThreeLevel.HIGH,
            )
        elif node.role == "closure":
            evidence = Evidence(
                id=make_id("evidence", node.semantic_unit),
                node_id=node.id,
                observation=f"Closure conditions were made explicit for '{node.semantic_unit}'.",
                source="internal_reflection",
                context={"generated_by": "refine_directly", "role": node.role},
                support_effect=ThreeLevel.HIGH,
                confidence=ThreeLevel.HIGH,
            )
        elif node.role == "direct_support" and self.direct_support_items(node):
            evidence = Evidence(
                id=make_id("evidence", node.semantic_unit),
                node_id=node.id,
                observation=f"Direct support was interpreted for '{node.semantic_unit}'.",
                source="internal_reflection",
                context={"generated_by": "refine_directly", "role": node.role},
                support_effect=ThreeLevel.MEDIUM,
                confidence=ThreeLevel.MEDIUM,
                provenance=list(self.direct_support_items(node)),
            )
        elif node.role == "upstream_support" and self.upstream_support_items(node):
            evidence = Evidence(
                id=make_id("evidence", node.semantic_unit),
                node_id=node.id,
                observation=f"Upstream support was carried forward for '{node.semantic_unit}'.",
                source="committed_state",
                context={"generated_by": "refine_directly", "role": node.role},
                support_effect=ThreeLevel.MEDIUM,
                confidence=ThreeLevel.HIGH,
                provenance=list(self.upstream_support_items(node)),
            )
        elif node.role == "generic":
            related_support_attached = self.instantiate_reusable_artifact_support(node)
            if node.metadata.get("direct_resolution_ready_for_commitment"):
                node.metadata["direct_refined"] = True
                return
            if related_support_attached:
                node.metadata["related_support_only"] = True
                return
            signals = self.direct_support_items(node) or self.upstream_support_items(node)
            if signals:
                evidence = Evidence(
                    id=make_id("evidence", node.semantic_unit),
                    node_id=node.id,
                    observation=f"Available support was interpreted directly for '{node.semantic_unit}'.",
                    source="internal_reflection",
                    context={"generated_by": "refine_directly", "role": node.role},
                    support_effect=ThreeLevel.MEDIUM,
                    confidence=ThreeLevel.MEDIUM,
                    provenance=list(signals),
                )
        elif node.role == "root":
            related_support_attached = self.instantiate_reusable_artifact_support(node)
            if node.metadata.get("direct_resolution_ready_for_commitment"):
                node.metadata["direct_refined"] = True
                return
            proposal = self.propose_direct_resolution(node)
            resolved = self.proposal_flag(
                proposal.payload,
                "resolved",
                default=self.fallback_direct_resolution(node)["resolved"],
            )
            answer = str(proposal.payload.get("answer", "")).strip()
            function_answer = ""
            function_artifact: Artifact | None = None
            function_execution: CrossBoundaryResult | None = None
            if resolved:
                function_answer, function_artifact, function_execution = self.resolve_function_execution_payload(
                    node=node,
                    payload=proposal.payload,
                    provenance=[proposal.id, node.id],
                    answer_kind=str(proposal.payload.get("answer_kind", "function_execution")).strip() or "function_execution",
                    justification=str(proposal.payload.get("justification", "")).strip() or "The item was better represented as a reusable parameterized function than as a one-off literal answer.",
                )
                if function_answer:
                    answer = function_answer
            confidence = normalize_three_level(
                proposal.payload.get("confidence", self.fallback_direct_resolution(node)["confidence"]),
                default=ThreeLevel.LOW,
            )
            closure_status = str(proposal.payload.get("closure_status", self.fallback_direct_resolution(node)["closure_status"])).strip().lower()
            if resolved and answer and closure_status == "ready":
                self.admit_proposal(
                    proposal,
                    rationale="The controller admitted a direct-resolution proposal because the item was judged trivial and directly answerable.",
                )
                node.metadata["direct_resolution_ready_for_commitment"] = True
                node.metadata["direct_resolution_answer"] = answer
                node.metadata["direct_resolution_confidence"] = confidence
                node.metadata["direct_resolution_answer_kind"] = str(proposal.payload.get("answer_kind", "direct_answer")).strip() or "direct_answer"
                node.metadata["direct_resolution_closure_status"] = closure_status
                evidence = Evidence(
                    id=make_id("evidence", node.semantic_unit),
                    node_id=node.id,
                    observation=f"Direct answer for '{node.semantic_unit}': {answer}.",
                    source="tool",
                    context={
                        "generated_by": "refine_directly",
                        "role": node.role,
                        "answer_kind": str(proposal.payload.get("answer_kind", "direct_answer")),
                        "justification": str(proposal.payload.get("justification", "")).strip(),
                        "proposal_id": proposal.id,
                        "llm_confidence": confidence,
                        "closure_status": closure_status,
                        "function_artifact_id": function_artifact.id if function_artifact is not None else "",
                        "cross_boundary": function_execution.to_dict() if function_execution is not None else {},
                    },
                    support_effect=ThreeLevel.HIGH,
                    confidence=ThreeLevel.HIGH,
                    provenance=[proposal.id, *( [function_artifact.id] if function_artifact is not None else [] )],
                )
            else:
                node.metadata.pop("direct_resolution_ready_for_commitment", None)
                self.revise_proposal(
                    proposal,
                    rationale="Direct resolution was not admitted because the item was not ready for direct closure under the current judgment.",
                )
                witness = self.propose_realization_witness(node)
                realizable_now = self.proposal_flag(
                    witness.payload,
                    "realizable_now",
                    default=self.fallback_realization_witness(node)["realizable_now"],
                )
                witness_answer = str(witness.payload.get("answer", "")).strip()
                witness_confidence = normalize_three_level(
                    witness.payload.get("confidence", self.fallback_realization_witness(node)["confidence"]),
                    default=ThreeLevel.LOW,
                )
                witness_closure_status = str(
                    witness.payload.get("closure_status", self.fallback_realization_witness(node)["closure_status"])
                ).strip().lower()
                witness_function_answer = ""
                witness_function_artifact: Artifact | None = None
                witness_execution: CrossBoundaryResult | None = None
                witness_steps = [
                    str(item).strip()
                    for item in witness.payload.get("witness_steps", [])
                    if isinstance(item, str) and str(item).strip()
                ] if isinstance(witness.payload.get("witness_steps", []), list) else []
                validation_check = str(witness.payload.get("validation_check", "")).strip()
                if realizable_now:
                    witness_function_answer, witness_function_artifact, witness_execution = self.resolve_function_execution_payload(
                        node=node,
                        payload=witness.payload,
                        provenance=[witness.id, node.id],
                        answer_kind=str(
                            witness.payload.get("answer_kind", witness.payload.get("witness_kind", "function_execution"))
                        ).strip()
                        or "function_execution",
                        justification="The present task was best realized by executing a reusable parameterized function artifact.",
                        validation_check=validation_check,
                    )
                    if witness_function_answer:
                        witness_answer = witness_function_answer
                if realizable_now and witness_answer and witness_closure_status == "ready" and witness_steps and validation_check:
                    self.admit_proposal(
                        witness,
                        rationale="The controller admitted a present realization witness because the bounded item could be solved now and paired with an evaluation check.",
                    )
                    node.metadata["direct_resolution_ready_for_commitment"] = True
                    node.metadata["direct_resolution_answer"] = witness_answer
                    node.metadata["direct_resolution_confidence"] = witness_confidence
                    node.metadata["direct_resolution_answer_kind"] = str(
                        witness.payload.get("answer_kind", witness.payload.get("witness_kind", "direct_answer"))
                    ).strip() or "direct_answer"
                    node.metadata["direct_resolution_closure_status"] = witness_closure_status
                    evidence = Evidence(
                        id=make_id("evidence", node.semantic_unit),
                        node_id=node.id,
                        observation=f"Present realization witness for '{node.semantic_unit}': {witness_answer}.",
                        source="tool",
                        context={
                            "generated_by": "present_realization_witness",
                            "role": node.role,
                            "answer_kind": str(
                                witness.payload.get("answer_kind", witness.payload.get("witness_kind", "direct_answer"))
                            ).strip(),
                            "witness_kind": str(witness.payload.get("witness_kind", "")).strip(),
                            "witness_steps": witness_steps,
                            "validation_check": validation_check,
                            "proposal_id": witness.id,
                            "llm_confidence": witness_confidence,
                            "closure_status": witness_closure_status,
                            "function_artifact_id": witness_function_artifact.id if witness_function_artifact is not None else "",
                            "cross_boundary": witness_execution.to_dict() if witness_execution is not None else {},
                        },
                        support_effect=ThreeLevel.HIGH,
                        confidence=witness_confidence,
                        provenance=[witness.id, *( [witness_function_artifact.id] if witness_function_artifact is not None else [] )],
                    )
                else:
                    self.revise_proposal(
                        witness,
                        rationale="The present realization witness did not provide a bounded answer plus evaluation check strong enough for closure.",
                    )
                    if related_support_attached:
                        node.metadata["related_support_only"] = True

        if evidence is not None:
            self.state.attach_evidence(evidence)
            node.metadata["direct_refined"] = True

    def propagate(self, seeds: Iterable[SemanticNode]) -> SystemState:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling propagate.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propagate(seeds=['mass', 'acceleration', 'force'])`
            Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            seeds: Value for `seeds` used by `propagate`. Expected type: `Iterable[SemanticNode]`.

        Returns:
            SystemState: Result produced by `propagate`.
        """
        seed_nodes = [seed if isinstance(seed, SemanticNode) else self.state.graph.get_node(seed) for seed in seeds]
        if seed_nodes:
            self.use_capability(
                "propagation",
                node=seed_nodes[0],
                contribution="stabilize affected semantic state after local change",
            )
        worklist = list(seed_nodes)
        queued = {node.id for node in seed_nodes}
        changed: set[str] = set()

        while worklist:
            node = worklist.pop()
            queued.discard(node.id)
            old_snapshot = self.snapshot(node)
            self.recompute_node(node)
            new_snapshot = self.snapshot(node)
            if new_snapshot != old_snapshot:
                changed.add(node.id)
                for neighbor in self.affected_neighbors(node):
                    if neighbor.id not in queued:
                        worklist.append(neighbor)
                        queued.add(neighbor.id)

        if changed:
            self.state.record_step(
                kind="propagation",
                node_id=self.state.root_id,
                intent="Propagate local semantic changes until the affected region stabilizes.",
                action="run typed worklist propagation",
                result="affected region recomputed to a local fixpoint",
                evaluation="status, certainty, blockers, and conflicts were updated for impacted nodes",
                payload={"changed_nodes": sorted(changed)},
            )
        return self.state

    def propagate_recursive(self, node: SemanticNode, visiting: set[str] | None = None) -> SystemState:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling propagate recursive.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propagate_recursive(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), visiting={'Physics', 'Force'})`
            Output: SystemState.bootstrap(prompt='Compute force from mass and acceleration.')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propagate_recursive`. Expected type: `SemanticNode`.
            visiting: Value for `visiting` used by `propagate_recursive`. Expected type: `set[str] | None`. Defaults to `None`.

        Returns:
            SystemState: Result produced by `propagate_recursive`.
        """
        if visiting is None:
            visiting = set()
        if node.id in visiting:
            return self.state
        visiting.add(node.id)
        try:
            old_snapshot = self.snapshot(node)
            self.recompute_node(node)
            if self.snapshot(node) != old_snapshot:
                for neighbor in self.affected_neighbors(node):
                    self.propagate_recursive(neighbor, visiting)
            return self.state
        finally:
            visiting.remove(node.id)

    def recompute_node(self, node: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling recompute node.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `recompute_node(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `recompute_node`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.state.blockers[node.id] = sorted(self.infer_blockers(node))
        self.state.support[node.id] = self.infer_support(node)
        self.state.certainty[node.id] = self.infer_certainty(node)
        self.state.conflicts[node.id] = sorted(self.surface_conflicts(node))
        self.state.status[node.id] = self.infer_status(node)
        self.maybe_close(node)

    def snapshot(self, node: SemanticNode) -> tuple[Any, ...]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling snapshot.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `snapshot(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `snapshot`. Expected type: `SemanticNode`.

        Returns:
            tuple[Any, ...]: Result produced by `snapshot`.
        """
        return (
            self.state.node_status(node.id).value,
            self.state.certainty.get(node.id, ThreeLevel.LOW),
            tuple(sorted(self.state.blockers.get(node.id, []))),
            tuple(sorted(self.state.conflicts.get(node.id, []))),
            self.state.support.get(node.id, SupportView([], [], SupportScore.VERY_BAD)).score,
            node.id in self.state.closed,
            node.id in self.state.paused,
            node.id in self.state.incomplete,
        )

    def maybe_close(self, node: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling maybe close.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `maybe_close(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `maybe_close`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if node.id in self.state.closed:
            self.state.status[node.id] = NodeStatus.CLOSED
        elif self.is_committable(node):
            self.state.incomplete.discard(node.id)
            self.state.status[node.id] = NodeStatus.CLOSABLE

    def infer_status(self, node: SemanticNode) -> NodeStatus:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with inferring status.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `infer_status(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `infer_status`. Expected type: `SemanticNode`.

        Returns:
            NodeStatus: Result produced by `infer_status`.
        """
        if node.id in self.state.closed:
            return NodeStatus.CLOSED
        if node.id in self.state.paused:
            return NodeStatus.PAUSED
        if node.id in self.state.incomplete:
            return NodeStatus.INCOMPLETE
        if self.prior_learning_fast_path_ready(node):
            return NodeStatus.CLOSABLE
        if self.is_inadmissible(node):
            return NodeStatus.INADMISSIBLE
        if self.state.conflicts.get(node.id):
            return NodeStatus.BLOCKED
        if self.has_open_blockers(node):
            return NodeStatus.BLOCKED

        assessment = self.node_assessment_payload(node)
        ready_for_commitment = self.proposal_flag(
            assessment,
            "ready_for_commitment",
            default=self.fallback_node_assessment(node)["ready_for_commitment"],
        )
        if node.metadata.get("direct_resolution_ready_for_commitment") and self.support_is_sufficient(node):
            ready_for_commitment = True
        children = self.refinement_children(node)
        if not children:
            if ready_for_commitment and self.support_is_sufficient(node):
                return NodeStatus.CLOSABLE
            return NodeStatus.OPEN

        if node.decomposition_mode == "AND":
            all_satisfied = all(self.child_is_satisfied(child) for child in children if child.required)
            if all_satisfied and ready_for_commitment:
                return NodeStatus.CLOSABLE
            return NodeStatus.OPEN

        if node.decomposition_mode == "OR":
            any_satisfied = any(self.child_is_satisfied(child) for child in children)
            if any_satisfied and ready_for_commitment:
                return NodeStatus.CLOSABLE
            return NodeStatus.OPEN

        return NodeStatus.OPEN

    def infer_support(self, node: SemanticNode) -> SupportView:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with inferring support.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `infer_support(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `infer_support`. Expected type: `SemanticNode`.

        Returns:
            SupportView: Result produced by `infer_support`.
        """
        if self.prior_learning_fast_path_ready(node):
            return SupportView(
                direct=self.direct_support_items(node),
                upstream=self.upstream_support_items(node),
                score=SupportScore.OK,
            )
        direct = self.direct_support_items(node)
        upstream = self.upstream_support_items(node)
        if node.metadata.get("direct_resolution_ready_for_commitment") and direct:
            return SupportView(direct=direct, upstream=upstream, score=SupportScore.OK)
        assessment = self.node_assessment_payload(node)
        score = normalize_support_score(
            self.proposal_text(
                assessment,
                "support_score",
                default=self.fallback_node_assessment(node)["support_score"],
            ),
            default=self.fallback_node_assessment(node)["support_score"],
        )
        return SupportView(direct=direct, upstream=upstream, score=score)

    def infer_certainty(self, node: SemanticNode) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with inferring certainty.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `infer_certainty(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `infer_certainty`. Expected type: `SemanticNode`.

        Returns:
            ThreeLevel: Result produced by `infer_certainty`.
        """
        if self.prior_learning_fast_path_ready(node):
            return ThreeLevel.HIGH
        if node.metadata.get("direct_resolution_ready_for_commitment") and self.direct_support_items(node):
            return ThreeLevel.HIGH
        assessment = self.node_assessment_payload(node)
        return normalize_three_level(
            self.proposal_text(
                assessment,
                "certainty",
                default=self.fallback_node_assessment(node)["certainty"],
            ),
            default=self.fallback_node_assessment(node)["certainty"],
        )

    def infer_blockers(self, node: SemanticNode) -> set[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with inferring blockers.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `infer_blockers(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'Physics', 'Force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `infer_blockers`. Expected type: `SemanticNode`.

        Returns:
            set[str]: Result produced by `infer_blockers`.
        """
        if self.prior_learning_fast_path_ready(node):
            return set()
        blockers: set[str] = set()
        for dependency in self.dependency_children(node):
            status = self.state.node_status(dependency.id)
            if dependency.required and status in {
                NodeStatus.OPEN,
                NodeStatus.BLOCKED,
                NodeStatus.PAUSED,
                NodeStatus.INCOMPLETE,
                NodeStatus.INADMISSIBLE,
            }:
                blockers.add(dependency.id)

        if self.missing_required_evidence(node):
            blockers.add(f"missing_evidence:{node.id}")
        if self.has_governance_violation(node):
            blockers.add(f"governance_violation:{node.id}")
        return blockers

    def surface_conflicts(self, node: SemanticNode) -> set[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling surface conflicts.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `surface_conflicts(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: {'Physics', 'Force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `surface_conflicts`. Expected type: `SemanticNode`.

        Returns:
            set[str]: Result produced by `surface_conflicts`.
        """
        if self.prior_learning_fast_path_ready(node):
            return set()
        assessment = self.node_assessment_payload(node)
        return set(self.proposal_list(assessment, "conflict_descriptions"))

    def affected_neighbors(self, node: SemanticNode) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling affected neighbors.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `affected_neighbors(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `affected_neighbors`. Expected type: `SemanticNode`.

        Returns:
            list[SemanticNode]: Result produced by `affected_neighbors`.
        """
        neighbors: dict[str, SemanticNode] = {}
        relevant = {
            EdgeType.REFINES,
            EdgeType.DEPENDS_ON,
            EdgeType.SUPPORTED_BY,
            EdgeType.BLOCKS,
            EdgeType.ALTERNATIVE_TO,
            EdgeType.REFRAMES_TO,
            EdgeType.CLOSES_TO,
        }
        for edge in self.state.graph.out_edges(node.id):
            if edge.type in relevant:
                neighbors[edge.dst] = self.state.graph.get_node(edge.dst)
        for edge in self.state.graph.in_edges(node.id):
            if edge.type in relevant:
                neighbors[edge.src] = self.state.graph.get_node(edge.src)
        neighbors.pop(node.id, None)
        return list(neighbors.values())

    def reframe_upward(self, node: SemanticNode) -> SemanticNode | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling reframe upward.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `reframe_upward(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `reframe_upward`. Expected type: `SemanticNode`.

        Returns:
            SemanticNode | None: Result produced by `reframe_upward`.
        """
        replacement = self.propose_higher_order_framing(node)
        if replacement is None:
            return None
        self.state.register_node(replacement, parent_id=node.parent_id)
        self.state.graph.add_edge(node.id, replacement.id, EdgeType.REFRAMES_TO)
        self.mark_reframed(node, replacement)
        affected = [node, replacement]
        if node.parent_id and node.parent_id in self.state.graph.nodes:
            affected.append(self.state.graph.get_node(node.parent_id))
        self.propagate(affected)
        return replacement

    def propose_higher_order_framing(self, node: SemanticNode) -> SemanticNode | None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with proposing higher order framing.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `propose_higher_order_framing(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `propose_higher_order_framing`. Expected type: `SemanticNode`.

        Returns:
            SemanticNode | None: Result produced by `propose_higher_order_framing`.
        """
        if node.metadata.get("already_reframed") or not self.can_reframe_within_decomposition(node):
            return None
        proposal = self.propose_reframe(node)
        semantic = str(
            proposal.payload.get("candidate_reframed_not")
            or f"better decomposition-scoped framing for {node.semantic_unit}"
        )
        for existing in self.state.graph.nodes.values():
            if existing.semantic_unit == semantic and existing.parent_id == node.parent_id:
                self.admit_proposal(
                    proposal,
                    rationale="The controller accepted an existing decomposition-scoped reframing suggested by the proposal.",
                )
                return existing
        reframed = SemanticNode(
            id=make_id("not", semantic),
            semantic_unit=semantic,
            role="generic",
            description=str(
                proposal.payload.get("reframing_reason")
                or "Decomposition-scoped reframing introduced because the local framing was insufficient."
            ),
            boundary_shape=node.boundary_shape,
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=self.state.governance.closure_threshold_default,
            evidence_required=False,
            required=node.required,
            depth=node.depth,
            priority_bias=PriorityLevel.HIGH,
            origin=NodeOrigin.REFRAMING,
            parent_id=node.parent_id,
            metadata={
                "reframe_proposal_id": proposal.id,
                "reframes_sibling": node.id,
                "semantic_loss_gain_notes": json_safe(proposal.payload.get("semantic_loss_gain_notes", [])),
                "preservation_obligations": json_safe(proposal.payload.get("preservation_obligations", [])),
            },
        )
        self.admit_proposal(
            proposal,
            rationale="The controller admitted the reframing proposal as a decomposition-scoped replacement candidate.",
        )
        return reframed

    def mark_reframed(self, node: SemanticNode, replacement: SemanticNode) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling mark reframed.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `mark_reframed(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), replacement=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `mark_reframed`. Expected type: `SemanticNode`.
            replacement: Value for `replacement` used by `mark_reframed`. Expected type: `SemanticNode`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        node.metadata["already_reframed"] = True
        node.metadata["reframed_to"] = replacement.id
        node.metadata["superseded_in_parent"] = True
        node.required = False
        self.state.incomplete.add(node.id)
        self.state.paused.discard(node.id)
        self.state.frontier.discard(node.id)
        self.state.status[node.id] = NodeStatus.INCOMPLETE
        self.state.record_step(
            kind="reframing",
            node_id=node.id,
            intent="Replace a poorly framed subordinate item without leaving the current decomposition region.",
            action="introduce decomposition-scoped reframing sibling",
            result="node superseded by a better-framed sibling",
            evaluation="reframing stayed inside the existing parent task rather than creating a new root above it",
            payload={"replacement_id": replacement.id, "parent_id": replacement.parent_id},
        )

    def direct_support_items(self, node: SemanticNode) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling direct support items.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `direct_support_items(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `direct_support_items`. Expected type: `SemanticNode`.

        Returns:
            list[str]: Result produced by `direct_support_items`.
        """
        return list(self.state.evidence_by_node.get(node.id, []))

    def upstream_support_items(self, node: SemanticNode) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling upstream support items.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `upstream_support_items(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `upstream_support_items`. Expected type: `SemanticNode`.

        Returns:
            list[str]: Result produced by `upstream_support_items`.
        """
        if node.role == "direct_support":
            return []
        seen: set[str] = set()
        items: list[str] = []

        def push(evidence_id: str) -> None:
            """
            High Level Purpose:
                In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling push.

            Reference to Theory:
                Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

            Example Input Output:
                Input: `push(evidence_id='artifact-force')`
                Output: None

            Args:
                evidence_id: Value for `evidence_id` used by `push`. Expected type: `str`.

            Returns:
                None: This function mutates state or performs side effects without returning a value.
            """
            if evidence_id not in seen:
                seen.add(evidence_id)
                items.append(evidence_id)

        for ancestor_id in self.ancestor_node_ids(node.id):
            for evidence_id in self.state.evidence_by_node.get(ancestor_id, []):
                push(evidence_id)
        for child in self.refinement_children(node):
            if child.id in self.state.closed:
                for evidence_id in self.state.evidence_by_node.get(child.id, []):
                    push(evidence_id)
        for commitment in self.state.commitments.values():
            if commitment.node_id in self.ancestor_node_ids(node.id):
                for evidence_id in commitment.evidence_ids:
                    push(evidence_id)
        return items

    def support_signal_from_items(self, evidence_ids: Iterable[str]) -> SupportScore:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling support signal from items.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `support_signal_from_items(evidence_ids=['mass', 'acceleration', 'force'])`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            evidence_ids: Value for `evidence_ids` used by `support_signal_from_items`. Expected type: `Iterable[str]`.

        Returns:
            SupportScore: Result produced by `support_signal_from_items`.
        """
        strongest, has_any = self.strongest_support_level_from_items(evidence_ids)
        return self.support_score_label(strongest, has_any_support=has_any)

    def aggregate_child_certainty(self, node: SemanticNode) -> ThreeLevel:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling aggregate child certainty.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `aggregate_child_certainty(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `aggregate_child_certainty`. Expected type: `SemanticNode`.

        Returns:
            ThreeLevel: Result produced by `aggregate_child_certainty`.
        """
        children = self.refinement_children(node)
        if not children:
            return ThreeLevel.LOW
        values = [self.state.certainty.get(child.id, ThreeLevel.LOW) for child in children]
        if node.decomposition_mode == "OR":
            return max_level(values, default=ThreeLevel.LOW)
        return min_level(values, default=ThreeLevel.HIGH)

    def dependency_children(self, node: SemanticNode) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling dependency children.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `dependency_children(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `dependency_children`. Expected type: `SemanticNode`.

        Returns:
            list[SemanticNode]: Result produced by `dependency_children`.
        """
        dependencies = [child for child in self.refinement_children(node) if child.required]
        for edge in self.state.graph.out_edges(node.id):
            if edge.type == EdgeType.DEPENDS_ON:
                dependencies.append(self.state.graph.get_node(edge.dst))
        deduped: dict[str, SemanticNode] = {dep.id: dep for dep in dependencies}
        return list(deduped.values())

    def incompatible_neighbors(self, node: SemanticNode) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling incompatible neighbors.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `incompatible_neighbors(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `incompatible_neighbors`. Expected type: `SemanticNode`.

        Returns:
            list[SemanticNode]: Result produced by `incompatible_neighbors`.
        """
        incompatible: dict[str, SemanticNode] = {}
        for edge in self.state.graph.out_edges(node.id):
            if edge.type == EdgeType.ALTERNATIVE_TO and edge.metadata.get("exclusive", False):
                incompatible[edge.dst] = self.state.graph.get_node(edge.dst)
        for edge in self.state.graph.in_edges(node.id):
            if edge.type == EdgeType.ALTERNATIVE_TO and edge.metadata.get("exclusive", False):
                incompatible[edge.src] = self.state.graph.get_node(edge.src)
        return list(incompatible.values())

    def child_is_satisfied(self, child: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling child is satisfied.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `child_is_satisfied(child=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            child: Value for `child` used by `child_is_satisfied`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `child_is_satisfied`.
        """
        return self.state.node_status(child.id) in {NodeStatus.CLOSED, NodeStatus.CLOSABLE}

    def support_is_sufficient(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling support is sufficient.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `support_is_sufficient(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `support_is_sufficient`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `support_is_sufficient`.
        """
        if self.prior_learning_fast_path_ready(node):
            return True
        if node.metadata.get("direct_resolution_ready_for_commitment") and self.direct_support_items(node):
            return True
        support = self.state.support.get(node.id, SupportView([], [], SupportScore.VERY_BAD))
        return self.support_score_is_sufficient(support.score)

    def missing_required_evidence(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling missing required evidence.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `missing_required_evidence(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `missing_required_evidence`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `missing_required_evidence`.
        """
        if not node.evidence_required:
            return False
        support = self.state.support.get(node.id)
        if support and self.support_score_is_sufficient(support.score):
            return False
        children = self.refinement_children(node)
        if children and any(self.child_is_satisfied(child) for child in children):
            return False
        return True

    def has_governance_violation(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether governance violation.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `has_governance_violation(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `has_governance_violation`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `has_governance_violation`.
        """
        if self.structural_governance_violation(node):
            return True
        if self.prior_learning_fast_path_ready(node):
            return False
        assessment = self.node_assessment_payload(node)
        return self.proposal_flag(
            assessment,
            "governance_violation",
            default=self.fallback_node_assessment(node)["governance_violation"],
        )

    def has_open_blockers(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether open blockers.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `has_open_blockers(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `has_open_blockers`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `has_open_blockers`.
        """
        return bool(self.state.blockers.get(node.id, []))

    def simultaneously_asserted(self, node: SemanticNode, other: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling simultaneously asserted.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `simultaneously_asserted(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), other=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `simultaneously_asserted`. Expected type: `SemanticNode`.
            other: Value for `other` used by `simultaneously_asserted`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `simultaneously_asserted`.
        """
        return self.child_is_satisfied(node) and self.child_is_satisfied(other)

    def certainty_conflicts_with_evidence(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling certainty conflicts with evidence.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `certainty_conflicts_with_evidence(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `certainty_conflicts_with_evidence`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `certainty_conflicts_with_evidence`.
        """
        certainty = self.state.certainty.get(node.id, ThreeLevel.LOW)
        support_signal = self.support_signal_from_items(self.direct_support_items(node) + self.upstream_support_items(node))
        counter_signal = self.counter_evidence_level(node)
        return certainty == ThreeLevel.HIGH and (
            (support_signal != SupportScore.OK and level_at_least(counter_signal, ThreeLevel.MEDIUM))
            or counter_signal == ThreeLevel.HIGH
        )

    def is_closed(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether closed.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `is_closed(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `is_closed`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `is_closed`.
        """
        return node.id in self.state.closed

    def is_inadmissible(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether inadmissible.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `is_inadmissible(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `is_inadmissible`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `is_inadmissible`.
        """
        if node.id in self.state.inadmissible:
            return True
        if self.has_governance_violation(node):
            self.state.inadmissible.add(node.id)
            return True
        return False

    def is_terminal(self, node: SemanticNode) -> bool:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with deciding whether terminal.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `is_terminal(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: True

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `is_terminal`. Expected type: `SemanticNode`.

        Returns:
            bool: Result produced by `is_terminal`.
        """
        return node.id in self.state.closed or node.id in self.state.inadmissible or node.id in self.state.incomplete or node.id in self.state.paused

    def refinement_children(self, node: SemanticNode) -> list[SemanticNode]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling refinement children.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `refinement_children(node=SemanticNode(id='not-force', semantic_unit='Physics / Force'))`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node: Value for `node` used by `refinement_children`. Expected type: `SemanticNode`.

        Returns:
            list[SemanticNode]: Result produced by `refinement_children`.
        """
        return self.state.graph.refinement_children(node.id)

    def ancestor_node_ids(self, node_id: str) -> list[str]:
        """
        High Level Purpose:
            In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling ancestor node ids.

        Reference to Theory:
            Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

        Example Input Output:
            Input: `ancestor_node_ids(node_id='artifact-force')`
            Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `ancestor_node_ids`. Expected type: `str`.

        Returns:
            list[str]: Result produced by `ancestor_node_ids`.
        """
        visited: set[str] = set()
        ordered: list[str] = []
        stack = [node_id]
        while stack:
            current = stack.pop()
            for parent in self.state.graph.refinement_parents(current):
                if parent.id not in visited:
                    visited.add(parent.id)
                    ordered.append(parent.id)
                    stack.append(parent.id)
        return ordered

    emit_trace_report = emit_run_trace_report
    finalize_run = finalize_governed_run


def build_artifact_store() -> SQLiteVectorArtifactStore:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with building artifact store.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_artifact_store()`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        None.

    Returns:
        SQLiteVectorArtifactStore: Result produced by `build_artifact_store`.
    """
    return _build_artifact_store()


def _registered_controller_factory(*, state: SystemState, llm_policy: str = "off") -> BSSCController:
    return BSSCController(state, llm_policy=llm_policy)


from controller_runtime_binding import register_controller_factory as _register_controller_factory

_register_controller_factory(_registered_controller_factory)


def build_controller(*, state: SystemState | None = None, llm_policy: str = "auto") -> BSSCController:
    """Construct the canonical controller implementation for an assembled state."""
    if state is None:
        raise ValueError("state must be provided to build_controller in this implementation.")
    return BSSCController(state, llm_policy=llm_policy)


def main() -> int:
    """Run the executable entrypoint registered by the compatibility facade."""
    from controller_entrypoint_binding import run_registered_controller_entrypoint

    return run_registered_controller_entrypoint()
