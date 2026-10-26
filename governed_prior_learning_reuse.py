# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from applied_theory_types import Artifact, Evidence, SemanticNode, ThreeLevel, json_safe
from learn import LEARNING_MATCH_KINDS
from normalization_primitives import (
    normalize_artifact_representation,
    normalize_artifact_type,
    normalize_learning_relation,
)
from prompt_directives import semantic_prompt_directive_profile, semantic_question_focus_text
from retrieval_ranking import artifact_is_structured_learning_record, learning_overlap
from semantic_prompt_posture import semantic_prompt_action_posture
from semantic_text import (
    collapse_ws,
    learning_lookup_keys,
    ordered_unique,
    semantic_named_input_keys,
    semantic_requested_output_keys,
    structured_learning_signal_lookup_keys,
    structured_text_list,
    titleize_semantic_unit,
)
from title_semantics import semantic_namespace_key


def _formula_role_answer_excerpt(semantic_unit: str, answer: str) -> str:
    normalized_unit = collapse_ws(str(semantic_unit or "").strip()).lower()
    normalized_answer = collapse_ws(str(answer or "").strip())
    if not normalized_unit or not normalized_answer:
        return ""
    directive = semantic_prompt_directive_profile(normalized_unit)
    if bool(directive.get("requires_formula", False)) and any(
        marker in normalized_answer for marker in ("$$", " = ", "formula is", "law is", "relation is", "equation is")
    ):
        return ""
    wants_input = "input" in normalized_unit
    wants_output = "output" in normalized_unit or "represent" in normalized_unit
    if not wants_input and not wants_output:
        return ""
    excerpts: list[str] = []
    def clean_role_value(value: str) -> str:
        normalized_value = collapse_ws(str(value).strip().strip(","))
        normalized_value = re.split(
            r"\s+(?=(?:If|When|Then|Where|Because|Since|After|Before)\b)",
            normalized_value,
            maxsplit=1,
        )[0]
        return collapse_ws(normalized_value.strip().strip(","))
    if wants_input:
        match = re.search(
            r"\binputs?\s*:\s*([^.;]+?)(?=\s+\boutputs?\s*:|[.;]|$)",
            normalized_answer,
            flags=re.IGNORECASE,
        )
        if match:
            cleaned = clean_role_value(str(match.group(1)))
            if cleaned:
                excerpts.append(f"input: {cleaned}")
    if wants_output:
        match = re.search(
            r"\boutputs?\s*:\s*([^.;]+?)(?=\s+\binputs?\s*:|[.;]|$)",
            normalized_answer,
            flags=re.IGNORECASE,
        )
        if match:
            cleaned = clean_role_value(str(match.group(1)))
            if cleaned:
                excerpts.append(f"output: {cleaned}")
    return " ".join(item for item in excerpts if item).strip()


def _component_fallback_reuse_semantic_unit(
    node: SemanticNode,
    current: Mapping[str, Any],
) -> str:
    semantic_text = collapse_ws(str(node.semantic_unit or "").strip())
    if not semantic_text:
        return semantic_text
    if node.role != "generic" or not bool(node.metadata.get("component_fallback")):
        return semantic_text
    directive_kind = collapse_ws(str(current.get("prompt_directive_kind", "")).strip()).lower()
    focus_text = collapse_ws(str(current.get("prompt_directive_focus", "")).strip())
    substrate_match = re.match(
        r"^\s*reusable\s+substrate\s+for\s+(.+?)\s*$",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if substrate_match is not None:
        substrate_focus = collapse_ws(str(substrate_match.group(1)).strip(" ?.!,:;"))
        if substrate_focus:
            return f"Identify the reusable substrate for {substrate_focus}."
    if re.match(
        r"^\s*(?:express|derive|show|write)\s+how\s+to\b",
        semantic_text,
        flags=re.IGNORECASE,
    ):
        compute_tail = re.sub(
            r"^\s*(?:express|derive|show|write)\s+",
            "",
            semantic_text,
            count=1,
            flags=re.IGNORECASE,
        ).strip(" ?.!,:;")
        if compute_tail:
            lead = "Derive" if directive_kind in {"derive", "construct"} else "Explain"
            return f"{lead} {compute_tail}."
    return f"What is {semantic_text}?"


def lookup_prior_non_achievedness(self, node: SemanticNode) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like deciding whether a current non-achievedness can close from prior learned residue instead of being reduced again from scratch, helps with assembling the governed reuse picture for the active node.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `lookup_prior_non_achievedness(self=controller, node=SemanticNode(id='not-force', semantic_unit='Calculate force from mass=3 and acceleration=4.'))`
        Output: {'match_kind': 'same_key', 'answer_match_kind': 'same_key', 'answer_preference': 'same_key', 'matched_lookup_keys': ['force from mass acceleration'], 'matched_artifacts': [Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script')], 'answer_artifact': Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'), 'focus_candidates': [], 'current': {'goal': 'Calculate force from mass=3 and acceleration=4.'}}

    Args:
        self: Bound controller instance that owns runtime state, reusable artifacts, and ranking helpers.
        node: Value for `node` used by `lookup_prior_non_achievedness`. Expected type: `SemanticNode`.

    Returns:
        dict[str, Any]: Result produced by `lookup_prior_non_achievedness`.
    """
    current = self.ensure_not_elaboration(node)
    matches: dict[str, list[Artifact]] = {kind: [] for kind in LEARNING_MATCH_KINDS}
    answer_candidates: dict[str, list[Artifact]] = {
        "same_not": [],
        "same_key": [],
        "same_composed_family": [],
        "covers_components": [],
        "lookup_overlap": [],
    }
    answer_candidate_kinds: dict[str, str] = {}
    matched_lookup_keys: list[str] = []

    for artifact in self.reusable_artifact_candidates():
        prior = self.artifact_structured_learning_view(artifact)
        match_kind = self.classify_structured_learning_match(current, prior)
        if match_kind is not None:
            matches[match_kind].append(artifact)
        preference = self.answer_reuse_preference(current, prior, artifact)
        if preference is not None:
            answer_candidates[preference].append(artifact)
            answer_candidate_kinds[artifact.id] = match_kind or "lookup_overlap"
            if not matched_lookup_keys:
                matched_lookup_keys = [
                    key
                    for key in structured_learning_signal_lookup_keys(current)
                    if any(
                        learning_overlap(key, prior_key)
                        for prior_key in structured_learning_signal_lookup_keys(prior)
                    )
                ]

    match_kind = "none"
    matched_artifacts: list[Artifact] = []
    for candidate_kind in LEARNING_MATCH_KINDS:
        if matches[candidate_kind]:
            match_kind = candidate_kind
            matched_artifacts = matches[candidate_kind]
            break

    answer_artifact: Artifact | None = None
    answer_match_kind = "none"
    answer_preference = ""
    focused_knowledge_artifacts: list[Artifact] = []
    preference_order = ("same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap")
    current_posture = str(current.get("action_posture", "")).strip()
    reuse_semantic_unit = _component_fallback_reuse_semantic_unit(node, current)
    direct_knowledge_prompt = self.prompt_prefers_direct_knowledge_answer(reuse_semantic_unit)
    if direct_knowledge_prompt:
        focused_knowledge_candidates = self.focused_direct_knowledge_candidates(
            semantic_unit=reuse_semantic_unit,
            current_boundary_shape=node.boundary_shape,
            candidate_pairs=[
                (preference, candidate)
                for preference in preference_order
                for candidate in answer_candidates[preference]
            ],
            include_unmatched_pool=True,
        )
        if focused_knowledge_candidates:
            focused_knowledge_artifacts = [candidate for _, candidate in focused_knowledge_candidates[:6]]
            answer_preference, answer_artifact = focused_knowledge_candidates[0]
            answer_match_kind = answer_candidate_kinds.get(answer_artifact.id, "focus_alignment")

    split_child_leaf_candidate = _preferred_split_child_leaf_artifact(
        self,
        node=node,
        current=current,
        matched_artifacts=matched_artifacts,
    )
    if split_child_leaf_candidate is not None and (
        answer_artifact is None
        or answer_preference in {"focus_alignment", "focus_alignment_store"}
        or artifact_is_structured_learning_record(answer_artifact)
        or semantic_namespace_key(str(answer_artifact.title).rsplit("/", 1)[-1].strip()) != semantic_namespace_key(
            str(split_child_leaf_candidate.title).rsplit("/", 1)[-1].strip()
        )
    ):
        answer_artifact = split_child_leaf_candidate
        answer_match_kind = self.classify_structured_learning_match(
            current,
            self.artifact_structured_learning_view(split_child_leaf_candidate),
        ) or match_kind or "lookup_overlap"
        answer_preference = self.answer_match_preference(
            current,
            self.artifact_structured_learning_view(split_child_leaf_candidate),
        )

    executable_candidates: list[tuple[str, Artifact]] = []
    if answer_artifact is None:
        for preference in preference_order:
            for candidate in answer_candidates[preference]:
                if not self.artifact_is_executable_function(candidate):
                    continue
                invocation_payload = self.derive_artifact_invocation_payload(
                    candidate,
                    semantic_unit=reuse_semantic_unit,
                )
                payload_ok, _, _ = self.artifact_invocation_payload_coverage(
                    candidate,
                    invocation_payload=invocation_payload,
                )
                if not payload_ok and not self.artifact_answer_text(candidate, semantic_unit=reuse_semantic_unit):
                    continue
                executable_candidates.append((preference, candidate))
    if answer_artifact is None and executable_candidates:
        executable_candidates.sort(
            key=lambda item: (
                preference_order.index(item[0]),
                self.answer_candidate_rank(
                    item[1],
                    semantic_unit=node.semantic_unit,
                    current_boundary_shape=node.boundary_shape,
                ),
            ),
        )
        answer_preference, answer_artifact = executable_candidates[0]
        answer_match_kind = answer_candidate_kinds.get(answer_artifact.id, "none")
    elif answer_artifact is None:
        for preference in preference_order:
            if not answer_candidates[preference]:
                continue
            ranked_candidates = sorted(
                answer_candidates[preference],
                key=lambda artifact: self.answer_candidate_rank(
                    artifact,
                    semantic_unit=reuse_semantic_unit,
                    current_boundary_shape=node.boundary_shape,
                ),
            )
            for candidate in ranked_candidates:
                if current_posture != "compute_or_template" and direct_knowledge_prompt:
                    if artifact_is_structured_learning_record(candidate):
                        continue
                if self.artifact_is_executable_function(candidate):
                    invocation_payload = self.derive_artifact_invocation_payload(
                        candidate,
                        semantic_unit=reuse_semantic_unit,
                    )
                    payload_ok, _, _ = self.artifact_invocation_payload_coverage(
                        candidate,
                        invocation_payload=invocation_payload,
                    )
                    if not payload_ok and not self.artifact_answer_text(candidate, semantic_unit=reuse_semantic_unit):
                        continue
                elif not self.artifact_answer_text(candidate, semantic_unit=reuse_semantic_unit):
                    continue
                answer_artifact = candidate
                answer_match_kind = answer_candidate_kinds.get(answer_artifact.id, "none")
                answer_preference = preference
                break
            if answer_artifact is not None:
                break
    if current_posture == "compute_or_template" or (
        not direct_knowledge_prompt
        and (
            answer_artifact is None
            or artifact_is_structured_learning_record(answer_artifact)
            or not self.artifact_is_executable_function(answer_artifact)
        )
    ):
        best_invokable = self.best_invokable_artifact_candidate(
            semantic_unit=reuse_semantic_unit,
            current_boundary_shape=node.boundary_shape,
        )
        if best_invokable is not None and (
            answer_artifact is None
            or artifact_is_structured_learning_record(answer_artifact)
            or not self.artifact_is_executable_function(answer_artifact)
            or self.answer_candidate_rank(
                best_invokable,
                semantic_unit=node.semantic_unit,
                current_boundary_shape=node.boundary_shape,
            ) < self.answer_candidate_rank(
                answer_artifact,
                semantic_unit=node.semantic_unit,
                current_boundary_shape=node.boundary_shape,
            )
        ):
            answer_artifact = best_invokable
            answer_match_kind = answer_candidate_kinds.get(answer_artifact.id, "lookup_overlap")
            answer_preference = "lookup_overlap"
        fallback_artifact, fallback_match_kind, fallback_preference = self.fallback_executable_answer_candidate(
            current=current,
            semantic_unit=reuse_semantic_unit,
        )
        if fallback_artifact is not None and (
            answer_artifact is None
            or artifact_is_structured_learning_record(answer_artifact)
            or not self.artifact_is_executable_function(answer_artifact)
        ):
            answer_artifact = fallback_artifact
            answer_match_kind = fallback_match_kind
            answer_preference = fallback_preference
    if answer_artifact is None:
        answer_artifact, answer_match_kind, answer_preference = self.fallback_executable_answer_candidate(
            current=current,
            semantic_unit=reuse_semantic_unit,
        )
    if answer_artifact is None and match_kind != "none" and matched_artifacts:
        ranked_matched_candidates = sorted(
            [
                artifact
                for artifact in matched_artifacts
                if not artifact_is_structured_learning_record(artifact)
                and (
                    self.artifact_is_executable_function(artifact)
                    or self.artifact_has_answer_capability(artifact, semantic_unit=reuse_semantic_unit)
                )
            ],
            key=lambda artifact: self.answer_candidate_rank(
                artifact,
                semantic_unit=reuse_semantic_unit,
                current_boundary_shape=node.boundary_shape,
            ),
        )
        if ranked_matched_candidates:
            answer_artifact = ranked_matched_candidates[0]
            answer_match_kind = match_kind
            answer_preference = self.answer_match_preference(
                current,
                self.artifact_structured_learning_view(answer_artifact),
            )

    return {
        "current": current,
        "reuse_semantic_unit": reuse_semantic_unit,
        "match_kind": match_kind,
        "matched_artifacts": matched_artifacts[:6],
        "answer_artifact": answer_artifact,
        "answer_match_kind": answer_match_kind,
        "answer_preference": answer_preference,
        "matched_lookup_keys": matched_lookup_keys[:4],
        "focus_candidates": focused_knowledge_artifacts[:6],
    }


def _preferred_split_child_leaf_artifact(
    self,
    *,
    node: SemanticNode,
    current: Mapping[str, Any],
    matched_artifacts: list[Artifact],
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like prompt-local split children under a broader shared family, helps with preferring the exact determinate child artifact over a broader family answer when both are present.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `_preferred_split_child_leaf_artifact(self=controller, node=SemanticNode(id='child-volume', semantic_unit='Prompt / Volume Of A Cylinder'), current={'title_depth_body_split_needed': True}, matched_artifacts=[Artifact(id='artifact-family', title='Cylinder Measures'), Artifact(id='artifact-volume', title='Cylinder Measures / Volume Of A Cylinder')])`
        Output: Artifact(id='artifact-volume', title='Cylinder Measures / Volume Of A Cylinder', artifact_type='knowledge', representation='yaml')

    Args:
        self: Bound controller instance that owns reusable-artifact ranking helpers.
        node: Value for `node` used by `_preferred_split_child_leaf_artifact`. Expected type: `SemanticNode`.
        current: Value for `current` used by `_preferred_split_child_leaf_artifact`. Expected type: `Mapping[str, Any]`.
        matched_artifacts: Value for `matched_artifacts` used by `_preferred_split_child_leaf_artifact`. Expected type: `list[Artifact]`.

    Returns:
        Artifact | None: Result produced by `_preferred_split_child_leaf_artifact`.
    """
    semantic_text = collapse_ws(str(node.semantic_unit or "").strip())
    if node.role != "generic" or "/" not in semantic_text:
        return None
    parent = self.state.graph.get_node(node.parent_id) if node.parent_id and node.parent_id in self.state.graph.nodes else None
    parent_structured = parent.metadata.get("structured_learning", {}) if parent is not None else {}
    parent_not = parent.metadata.get("not_elaboration", {}) if parent is not None else {}
    split_needed = bool(current.get("title_depth_body_split_needed", False)) or bool(
        isinstance(parent_structured, Mapping) and parent_structured.get("title_depth_body_split_needed", False)
    ) or bool(
        isinstance(parent_not, Mapping) and parent_not.get("title_depth_body_split_needed", False)
    )
    if not split_needed:
        return None
    leaf_text = collapse_ws(semantic_text.rsplit("/", 1)[-1].strip())
    leaf_key = semantic_namespace_key(leaf_text)
    if not leaf_key:
        return None
    candidates: list[Artifact] = []
    for artifact in matched_artifacts:
        identity_surfaces = self.artifact_identity_surfaces(artifact)
        if any(
            semantic_namespace_key(collapse_ws(str(surface).rsplit("/", 1)[-1].strip())) == leaf_key
            or semantic_namespace_key(surface) == leaf_key
            for surface in identity_surfaces
        ):
            candidates.append(artifact)
    if not candidates:
        return None
    candidates.sort(
        key=lambda artifact: self.answer_candidate_rank(
            artifact,
            semantic_unit=node.semantic_unit,
            current_boundary_shape=node.boundary_shape,
        ),
    )
    return candidates[0]


def learning_context_query_variants(self, semantic_unit: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like loading prior reusable artifacts before reduction begins, helps with generating a bounded query set that covers both broad families and narrower directive-shaped focus.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_context_query_variants(self=controller, semantic_unit='Derive current from voltage and resistance.')`
        Output: ['Derive current from voltage and resistance.', 'current', 'Current', 'current derivation', 'current relation chain', 'current from voltage resistance', 'calculate current from voltage resistance']

    Args:
        self: Bound controller instance that owns directive and lookup helpers.
        semantic_unit: Value for `semantic_unit` used by `learning_context_query_variants`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `learning_context_query_variants`.
    """
    semantic_text = collapse_ws(str(semantic_unit or "").strip())
    if not semantic_text:
        return []
    variants: list[str] = [semantic_text]
    directive = semantic_prompt_directive_profile(semantic_text)
    directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
    focus_text = semantic_question_focus_text(semantic_text)
    if focus_text:
        variants.append(focus_text)
        titleized_focus = titleize_semantic_unit(focus_text)
        if titleized_focus:
            variants.append(titleized_focus)
        variants.append(f"{focus_text} definition")
        variants.append(f"{focus_text} meaning")
        if directive_kind == "state" and bool(directive.get("requires_formula", False)):
            variants.extend(
                [
                    f"{focus_text} formula",
                    f"{focus_text} relation",
                    f"{focus_text} law",
                ]
            )
        if directive_kind == "derive":
            variants.extend(
                [
                    f"{focus_text} derivation",
                    f"{focus_text} relation chain",
                ]
            )
        if directive_kind == "construct":
            variants.extend(
                [
                    f"{focus_text} composition",
                    f"{focus_text} chain",
                ]
            )
        if directive_kind == "identify_reusable_substrate":
            variants.extend(
                [
                    f"{focus_text} reusable substrate",
                    f"{focus_text} broader substrate",
                    f"{focus_text} underlying family",
                ]
            )
    compared_terms = structured_text_list(directive.get("compared_terms", []))
    for compared_term in compared_terms:
        variants.append(compared_term)
        titleized_term = titleize_semantic_unit(compared_term)
        if titleized_term:
            variants.append(titleized_term)
    if directive_kind == "distinguish" and len(compared_terms) == 2:
        variants.append(f"{compared_terms[0]} versus {compared_terms[1]}")
        variants.append(f"difference between {compared_terms[0]} and {compared_terms[1]}")
    requested_outputs = semantic_requested_output_keys(semantic_text)
    named_inputs = semantic_named_input_keys(semantic_text)
    relation_match = re.search(
        r"\b(?:formula|relation|equation|law)\s+that\s+relates?\s+(.+?)\s+to\s+(.+?)(?:[?.!,;]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if relation_match:
        related_output = collapse_ws(str(relation_match.group(1)).strip(" ?.!,:;"))
        related_inputs = collapse_ws(str(relation_match.group(2)).strip(" ?.!,:;"))
        if related_output and related_inputs:
            variants.extend(
                [
                    f"{related_output} from {related_inputs}",
                    f"calculate {related_output} from {related_inputs}",
                    f"{related_output} relation",
                    f"formula relating {related_output} and {related_inputs}",
                ]
            )
    compute_shape_match = re.search(
        r"\b(?:derive|express|show|write|explain)\s+how\s+to\s+compute\s+(.+?)\s+from\s+(.+?)(?:\s+(?:and|which|that)\b|[?.!,;]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if compute_shape_match:
        derived_output = collapse_ws(str(compute_shape_match.group(1)).strip(" ?.!,:;"))
        derived_inputs = collapse_ws(str(compute_shape_match.group(2)).strip(" ?.!,:;"))
        if derived_output and derived_inputs:
            variants.extend(
                [
                    f"compute {derived_output} from {derived_inputs}",
                    f"calculate {derived_output} from {derived_inputs}",
                    f"{derived_output} from {derived_inputs}",
                ]
            )
    if requested_outputs and named_inputs:
        for output in requested_outputs[:2]:
            variants.append(f"{output} from {' '.join(named_inputs[:6])}")
            variants.append(f"calculate {output} from {' '.join(named_inputs[:6])}")
    elif requested_outputs:
        variants.extend(output for output in requested_outputs[:2] if len(output) >= 3)
    focus_basis = focus_text or semantic_text
    variants.extend(
        key
        for key in learning_lookup_keys(focus_basis)
        if len(key) >= 8
    )
    return ordered_unique(collapse_ws(item) for item in variants if collapse_ws(item))[:16]


def build_structured_learning_artifact(
    self,
    *,
    node: SemanticNode,
    related_artifact_ids: list[str],
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like persisting a reuse-ready summary of the current non-achievedness after closure or support formation, helps with materializing a structured learning artifact that can be matched later.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_structured_learning_artifact(self=controller, node=SemanticNode(id='not-force', semantic_unit='Calculate force from mass=3 and acceleration=4.'), related_artifact_ids=['artifact-force'])`
        Output: Artifact(id='artifact-structured-force', title='Structured learning record for Calculate force from mass=3 and acceleration=4.', artifact_type='knowledge', representation='yaml')

    Args:
        self: Bound controller instance that owns artifact-building and support-derivation helpers.
        node: Value for `node` used by `build_structured_learning_artifact`. Expected type: `SemanticNode`.
        related_artifact_ids: Value for `related_artifact_ids` used by `build_structured_learning_artifact`. Expected type: `list[str]`.

    Returns:
        Artifact | None: Result produced by `build_structured_learning_artifact`.
    """
    structured = self.structured_learning_view(node)
    derived_support = self.derive_related_solution_support(structured, related_artifact_ids)
    direct_answer = str(node.metadata.get("direct_resolution_answer", "")).strip()
    stored_answer = direct_answer
    title = f"Structured learning record for {structured['encountered_not']}"
    scope = "reuse when the same non-achievedness, a paraphrase of it, or a compatible decomposition reappears"
    constraints = [
        "reuse the record only when the active non-achievedness is semantically aligned under ordinary reading",
        "treat structure alone as support only after governance checks for scope, conflict, and stability",
    ]
    payload = {
        "artifact_type": "knowledge",
        "title": title,
        "representation": "yaml",
        "scope": scope,
        "reusability": "broad_reuse" if structured["lookup_keys"] else "local_reuse",
        "admissibility": "admitted" if structured["lookup_keys"] else "candidate",
        "learning_relation": "new_family",
        "related_artifact_ids": related_artifact_ids[:6],
        "template_schema": {},
        "justification": "the run produced a structured non-achievedness view that can be reused for prior-encounter lookup, decomposition-aware reuse, and composition-aware reuse",
        "constraints": constraints,
        "content": {
            "node_id": node.id,
            "question": node.semantic_unit,
            "answer": stored_answer,
            "answer_source": "direct_resolution" if direct_answer else "none",
            "answer_source_artifact_id": str(derived_support.get("source_artifact_id", "")).strip(),
            "answer_source_artifact_title": str(derived_support.get("source_artifact_title", "")).strip(),
            "answer_reuse_preference": str(derived_support.get("answer_preference", "")).strip(),
            "supporting_capability_artifact_ids": list(derived_support.get("capability_artifact_ids", [])),
            "structured_learning": structured,
        },
    }
    return self.build_artifact_from_payload(node=node, payload=payload, provenance=[node.id, *related_artifact_ids[:4]])


def build_immediate_learning_artifact(
    self,
    *,
    node: SemanticNode,
    payload: Mapping[str, Any],
    related_artifact_ids: list[str],
    provenance: list[str],
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like harvesting a nearby bounded lesson while the current encounter is still active, helps with turning that immediate learning note into a reusable artifact.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_immediate_learning_artifact(self=controller, node=SemanticNode(id='not-force', semantic_unit='What is force?'), payload={'question': 'What is force?', 'answer': 'Force is mass times acceleration.', 'encountered_not': 'Force', 'component_nots': ['Mass', 'Acceleration']}, related_artifact_ids=['artifact-force'], provenance=['not-force', 'artifact-force'])`
        Output: Artifact(id='artifact-immediate-force', title='Immediate learning note for Force', artifact_type='knowledge', representation='yaml')

    Args:
        self: Bound controller instance that owns structured-learning and artifact-building helpers.
        node: Value for `node` used by `build_immediate_learning_artifact`. Expected type: `SemanticNode`.
        payload: Value for `payload` used by `build_immediate_learning_artifact`. Expected type: `Mapping[str, Any]`.
        related_artifact_ids: Value for `related_artifact_ids` used by `build_immediate_learning_artifact`. Expected type: `list[str]`.
        provenance: Value for `provenance` used by `build_immediate_learning_artifact`. Expected type: `list[str]`.

    Returns:
        Artifact | None: Result produced by `build_immediate_learning_artifact`.
    """
    semantic_unit = str(payload.get("semantic_unit") or payload.get("question") or "").strip()
    answer = str(payload.get("answer", "")).strip()
    if not semantic_unit or not answer:
        return None

    raw_encountered_not = str(payload.get("encountered_not", "")).strip()
    raw_composed_not = str(payload.get("composed_not", "")).strip()
    component_nots = [
        str(item).strip()
        for item in payload.get("component_nots", [])
        if str(item).strip()
    ] if isinstance(payload.get("component_nots", []), list) else []
    if raw_composed_not:
        component_basis = [raw_encountered_not, *component_nots]
        component_nots = ordered_unique(
            titleize_semantic_unit(item) or item
            for item in component_basis
            if str(item).strip()
        )
        raw_encountered_not = raw_composed_not
    structured = self.structured_learning_view_for_text(
        semantic_unit,
        encountered_not=raw_encountered_not,
        component_nots=component_nots or None,
        composed_not=raw_composed_not,
        related_artifact_titles=[
            self.state.artifacts[artifact_id].title
            for artifact_id in related_artifact_ids
            if artifact_id in self.state.artifacts
        ][:4],
    )
    encountered_not = structured["encountered_not"]
    title = str(payload.get("title", "")).strip() or f"Immediate learning note for {encountered_not}"
    scope = (
        str(payload.get("scope", "")).strip()
        or f"reuse when the same nearby non-achievedness around {titleize_semantic_unit(node.semantic_unit) or node.semantic_unit} reappears under an ordinary stable reading"
    )
    why_now = str(payload.get("why_now") or payload.get("justification") or "").strip()
    constraints = [
        str(item).strip()
        for item in payload.get("constraints", [])
        if str(item).strip()
    ] if isinstance(payload.get("constraints", []), list) else []
    if not constraints:
        constraints = [
            "reuse only when the adjacent question remains within the same ordinary scope",
            "treat the stored answer as bounded introductory support rather than as universal doctrine",
        ]

    learning_relation = normalize_learning_relation(
        payload.get("learning_relation", "extends_parameters" if related_artifact_ids else "new_family"),
        default="extends_parameters" if related_artifact_ids else "new_family",
    )
    artifact_payload = {
        "artifact_type": normalize_artifact_type(payload.get("artifact_type", "knowledge")),
        "title": title,
        "representation": normalize_artifact_representation(payload.get("representation", "yaml")),
        "scope": scope,
        "reusability": payload.get("reusability", "broad_reuse" if structured["lookup_keys"] else "local_reuse"),
        "admissibility": payload.get("admissibility", "admitted"),
        "learning_relation": learning_relation,
        "related_artifact_ids": ordered_unique(list(related_artifact_ids) + self.related_learned_artifact_ids("knowledge", title, scope))[:8],
        "template_schema": {},
        "justification": why_now or "discovery widened future governability by harvesting a nearby bounded learning unit while the source encounter was still semantically active",
        "constraints": constraints,
        "content": {
            "node_id": node.id,
            "question": semantic_unit,
            "answer": answer,
            "source_node_id": node.id,
            "source_semantic_unit": node.semantic_unit,
            "source_encountered_not": str(payload.get("encountered_not", "")).strip(),
            "immediate_learning_reason": why_now,
            "structured_learning": structured,
        },
    }
    return self.build_artifact_from_payload(
        node=node,
        payload=artifact_payload,
        provenance=list(dict.fromkeys([node.id, *provenance, *related_artifact_ids[:4]])),
    )


def load_learning_context(self, node: SemanticNode) -> None:
    """
    High Level Purpose:
        In circumstances like opening a fresh prompt against a learned corpus, helps with loading a small reusable artifact context before deeper reduction begins.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `load_learning_context(self=controller, node=SemanticNode(id='not-mass-conservation', semantic_unit='What is mass conservation in a reaction?'))`
        Output: None

    Args:
        self: Bound controller instance that owns runtime state, retrieval, and step recording.
        node: Value for `node` used by `load_learning_context`. Expected type: `SemanticNode`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    node.metadata["structured_learning"] = self.ensure_not_elaboration(node)
    global_retrieval_enabled = bool(getattr(self, "subject_scope_global_retrieval_enabled", lambda: False)())
    if self.state.learned_artifacts and not global_retrieval_enabled:
        return
    if not global_retrieval_enabled and getattr(self.state, "subject_reasoning_scope", {}):
        return
    self.use_capability(
        "structured_learning",
        node=node,
        contribution="represent the active item as a structured non-achievedness before prior-encounter lookup",
    )
    direct_knowledge_prompt = self.prompt_prefers_direct_knowledge_answer(node.semantic_unit)
    per_query_limit = 16 if direct_knowledge_prompt else 10
    max_loaded = 64 if direct_knowledge_prompt else 12
    learned_by_id: dict[str, Artifact] = dict(self.state.learned_artifacts)
    for query_text in self.learning_context_query_variants(node.semantic_unit):
        for artifact in self.store_relevant_artifacts(query_text, limit=per_query_limit):
            learned_by_id.setdefault(artifact.id, artifact)
        if not direct_knowledge_prompt and len(learned_by_id) >= max_loaded:
            break
    learned = list(learned_by_id.values())[:max_loaded]
    if not learned:
        return
    for artifact in learned:
        self.state.learned_artifacts[artifact.id] = artifact
    node.metadata["structured_learning"] = self.ensure_not_elaboration(node)
    loaded_origin_report = self.learned_artifact_origin_report([artifact.id for artifact in learned])
    structured_lookup = node.metadata.get("structured_learning_lookup", {})
    if isinstance(structured_lookup, Mapping):
        node.metadata["structured_learning_lookup"] = {
            **structured_lookup,
            "loaded_artifact_origin_report": loaded_origin_report,
        }
    self.state.record_step(
        kind="learning_context",
        node_id=node.id,
        intent="Load relevant prior reusable artifacts so later reduction can benefit from prior templating and harvest.",
        action="retrieve learned artifacts from the configured store",
        result="learning context loaded",
        evaluation="prior admitted residue became available for governed reuse rather than remaining inert storage",
        payload={
            "structured_learning": node.metadata.get("structured_learning", {}),
            "artifact_ids": [artifact.id for artifact in learned],
            "artifact_types": sorted({artifact.artifact_type for artifact in learned}),
            "subject_reasoning_scope": dict(getattr(self.state, "subject_reasoning_scope", {}) or {}),
            "learned_artifact_origins": {
                artifact.id: self.learned_artifact_origin_payload(artifact.id)
                for artifact in learned
            },
            "artifact_origin_report": loaded_origin_report,
        },
    )


def immediate_learning_context_artifacts(
    self,
    node: SemanticNode,
    *,
    limit: int = 10,
) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like discovery harvest or nearby-lesson generation, helps with assembling the bounded artifact context most relevant to the active encounter.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `immediate_learning_context_artifacts(self=controller, node=SemanticNode(id='not-force', semantic_unit='What is force?'), limit=3)`
        Output: [Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script')]

    Args:
        self: Bound controller instance that owns reusable-artifact access and store history access.
        node: Value for `node` used by `immediate_learning_context_artifacts`. Expected type: `SemanticNode`.
        limit: Value for `limit` used by `immediate_learning_context_artifacts`. Expected type: `int`. Defaults to `10`.

    Returns:
        list[Artifact]: Result produced by `immediate_learning_context_artifacts`.
    """
    ordered: dict[str, Artifact] = {}
    lookup = node.metadata.get("structured_learning_lookup", {})
    lookup_ids = [
        str(item).strip()
        for item in lookup.get("artifact_ids", [])
        if str(item).strip()
    ] if isinstance(lookup, Mapping) else []
    reusable = {artifact.id: artifact for artifact in self.reusable_artifact_candidates()}
    for artifact_id in lookup_ids:
        artifact = reusable.get(artifact_id)
        if artifact is not None and artifact.admissibility != "rejected":
            ordered.setdefault(artifact.id, artifact)
    for artifact in self.reusable_artifact_candidates():
        if artifact.admissibility == "rejected":
            continue
        ordered.setdefault(artifact.id, artifact)
    for artifact in self.artifact_store.load_recent_artifacts(limit=limit):
        if artifact.admissibility == "rejected":
            continue
        ordered.setdefault(artifact.id, artifact)
    return list(ordered.values())[:limit]


def instantiate_reusable_artifact_support(self, node: SemanticNode) -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether the current encounter can close or at least gain support from prior learned residue, helps with instantiating the governed reusable support now instead of forcing fresh reduction.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `instantiate_reusable_artifact_support(self=controller, node=SemanticNode(id='not-current', semantic_unit='Calculate current from voltage=12 and resistance=4.'))`
        Output: True

    Args:
        self: Bound controller instance that owns evidence attachment, reuse lookup, and direct-answer composition.
        node: Value for `node` used by `instantiate_reusable_artifact_support`. Expected type: `SemanticNode`.

    Returns:
        bool: Result produced by `instantiate_reusable_artifact_support`.
    """
    if self.direct_support_items(node):
        return False
    lookup = self.lookup_prior_non_achievedness(node)
    answer_artifact = lookup["answer_artifact"]
    reuse_semantic_unit = str(lookup.get("reuse_semantic_unit", "")).strip() or node.semantic_unit
    answer_match_kind = str(lookup.get("answer_match_kind", "")).strip() or lookup["match_kind"]
    answer_preference = str(lookup.get("answer_preference", "")).strip()
    matched_artifacts: list[Artifact] = list(lookup["matched_artifacts"])
    if answer_artifact is not None and all(artifact.id != answer_artifact.id for artifact in matched_artifacts):
        matched_artifacts = [*matched_artifacts, answer_artifact]

    effective_match_kind = lookup["match_kind"]
    if effective_match_kind == "none" and answer_artifact is not None:
        effective_match_kind = answer_match_kind or "lookup_overlap"

    directive = semantic_prompt_directive_profile(node.semantic_unit)
    component_count = len(
        [item for item in lookup["current"].get("component_nots", []) if str(item).strip()]
    ) if isinstance(lookup.get("current"), Mapping) else 0
    prompt_requires_body_split = node.role == "root" and (
        bool(
            re.search(
                r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
                str(node.semantic_unit or ""),
                flags=re.IGNORECASE,
            )
        )
        or bool(lookup["current"].get("title_depth_body_split_needed", False))
        or (
            collapse_ws(str(directive.get("kind", "")).strip()) in {"construct", "derive", "distinguish"}
            and component_count >= 2
        )
    )

    node.metadata["structured_learning"] = lookup["current"]
    node.metadata["structured_learning_lookup"] = {
        "match_kind": effective_match_kind,
        "artifact_ids": [artifact.id for artifact in matched_artifacts],
        "matched_lookup_keys": lookup["matched_lookup_keys"],
        "artifact_origin_report": self.learned_artifact_origin_report([artifact.id for artifact in matched_artifacts]),
    }
    if effective_match_kind == "none" and answer_artifact is None:
        return False

    provenance: list[str] = []
    for artifact in matched_artifacts:
        provenance.append(artifact.id)
        provenance.extend(artifact.related_artifact_ids)
    provenance = ordered_unique(provenance)

    self.use_capability(
        "structured_learning",
        node=node,
        contribution="lookup whether the active non-achievedness, its parts, or a compatible composition has been encountered before",
    )

    if answer_artifact is not None:
        executable_answer = self.artifact_is_executable_function(answer_artifact)
        prompt_posture = semantic_prompt_action_posture(node.semantic_unit)
        invocation_payload = self.derive_artifact_invocation_payload(
            answer_artifact,
            semantic_unit=reuse_semantic_unit,
        ) if executable_answer else None
        execution = None
        split_child_leaf_reuse = False
        semantic_text = collapse_ws(str(node.semantic_unit or "").strip())
        if (
            node.role == "generic"
            and bool(lookup["current"].get("title_depth_body_split_needed", False))
            and "/" in semantic_text
        ):
            leaf_key = semantic_namespace_key(semantic_text.rsplit("/", 1)[-1].strip())
            split_child_leaf_reuse = bool(leaf_key) and any(
                semantic_namespace_key(collapse_ws(str(surface).rsplit("/", 1)[-1].strip())) == leaf_key
                or semantic_namespace_key(surface) == leaf_key
                for surface in self.artifact_identity_surfaces(answer_artifact)
            )
        answer = ""
        if executable_answer and invocation_payload not in (None, "", [], {}) and (
            prompt_posture == "compute_or_template" or split_child_leaf_reuse
        ):
            execution = self.execute_function_artifact(
                answer_artifact,
                semantic_unit=node.semantic_unit,
                explicit_payload=invocation_payload,
            )
            if execution.ok and str(execution.answer or "").strip():
                answer = str(execution.answer).strip()
        if not answer:
            answer = self.artifact_answer_text(
                answer_artifact,
                semantic_unit=reuse_semantic_unit,
            )
        direct_knowledge_prompt = self.prompt_prefers_direct_knowledge_answer(reuse_semantic_unit)
        if answer and direct_knowledge_prompt and not split_child_leaf_reuse:
            answer = self.compose_direct_knowledge_answer(
                semantic_unit=reuse_semantic_unit,
                primary_artifact=answer_artifact,
                primary_answer=answer,
                focus_candidates=lookup.get("focus_candidates", []),
            )
        if not answer and executable_answer and invocation_payload not in (None, "", [], {}):
            execution = self.execute_function_artifact(
                answer_artifact,
                semantic_unit=reuse_semantic_unit,
                explicit_payload=invocation_payload,
            )
            if execution.ok and str(execution.answer or "").strip():
                answer = str(execution.answer).strip()
        if not answer:
            return False
        self.use_capability(
            "artifact_instantiation",
            node=node,
            contribution="instantiate prior encountered non-achievedness as present support before requesting fresh semantic adjudication",
        )
        prompt_posture = semantic_prompt_action_posture(node.semantic_unit)
        direct_knowledge_reuse = (
            direct_knowledge_prompt
            and prompt_posture != "next_step_guidance"
            and answer_preference in {"focus_alignment", "focus_alignment_store"}
        )
        grounded_direct_knowledge_reuse = (
            prompt_posture == "direct_resolution"
            and effective_match_kind in {"encountered_before", "same_not", "same_key", "same_composed_family", "covers_components"}
            and answer_preference in {"covers_components", "lookup_overlap", "focus_alignment", "focus_alignment_store"}
            and answer_artifact is not None
            and not artifact_is_structured_learning_record(answer_artifact)
            and bool(answer.strip())
        )
        grounded_same_family_direct_resolution_reuse = (
            prompt_posture == "direct_resolution"
            and answer_match_kind in {"composition_related", "decomposition_related"}
            and answer_preference == "same_composed_family"
            and answer_artifact is not None
            and not artifact_is_structured_learning_record(answer_artifact)
            and bool(answer.strip())
        )
        grounded_component_chain_direct_resolution_reuse = (
            prompt_posture == "direct_resolution"
            and answer_match_kind in {"composition_related", "decomposition_related"}
            and answer_preference == "covers_components"
            and answer_artifact is not None
            and not artifact_is_structured_learning_record(answer_artifact)
            and bool(answer.strip())
        )
        formula_role_answer = _formula_role_answer_excerpt(node.semantic_unit, answer)
        grounded_formula_role_direct_resolution_reuse = (
            prompt_posture == "direct_resolution"
            and answer_artifact is not None
            and not artifact_is_structured_learning_record(answer_artifact)
            and bool(formula_role_answer)
        )
        executable_reuse_ready = executable_answer and invocation_payload not in (None, "", [], {})
        strong_grounded_guidance_reuse = (
            prompt_posture == "next_step_guidance"
            and effective_match_kind in {"encountered_before", "same_not", "same_key", "same_composed_family", "covers_components"}
            and answer_artifact is not None
            and any(artifact.id == answer_artifact.id for artifact in matched_artifacts)
        )
        grounded_guidance_reuse = (
            prompt_posture == "next_step_guidance"
            and answer_artifact is not None
            and effective_match_kind in {
                "encountered_before",
                "same_not",
                "same_key",
                "same_composed_family",
                "covers_components",
                "composition_related",
                "decomposition_related",
            }
            and not artifact_is_structured_learning_record(answer_artifact)
            and bool(answer.strip())
        )
        weak_guidance_reuse = (
            prompt_posture == "next_step_guidance"
            and not grounded_guidance_reuse
            and not strong_grounded_guidance_reuse
            and answer_match_kind not in {"encountered_before", "same_not", "same_key", "same_composed_family", "covers_components"}
            and answer_preference not in {"same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap"}
            and not executable_reuse_ready
        )
        support_only_reuse = weak_guidance_reuse or (
            answer_match_kind in {"composition_related", "decomposition_related"}
            and not executable_reuse_ready
            and not grounded_guidance_reuse
            and not grounded_direct_knowledge_reuse
            and not grounded_same_family_direct_resolution_reuse
            and not grounded_component_chain_direct_resolution_reuse
            and not grounded_formula_role_direct_resolution_reuse
        )
        closure_ready = (not support_only_reuse) and (
            answer_match_kind == "encountered_before"
            or answer_preference in {"same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap"}
            or direct_knowledge_reuse
            or grounded_direct_knowledge_reuse
            or grounded_same_family_direct_resolution_reuse
            or grounded_component_chain_direct_resolution_reuse
            or grounded_formula_role_direct_resolution_reuse
            or executable_reuse_ready
            or strong_grounded_guidance_reuse
            or grounded_guidance_reuse
        )
        if prompt_requires_body_split:
            closure_ready = False
        reusable_answer = formula_role_answer or answer
        if closure_ready and split_child_leaf_reuse:
            artifact_structured = self.artifact_structured_learning_view(answer_artifact)
            artifact_title_identity = collapse_ws(str(artifact_structured.get("title_identity", "")).strip())
            if "/" in artifact_title_identity:
                updated_current = dict(lookup["current"])
                updated_current["title_identity"] = artifact_title_identity
                updated_current["title_depth_segments"] = list(artifact_structured.get("title_depth_segments", []))
                updated_current["title_depth_prefixes"] = list(artifact_structured.get("title_depth_prefixes", []))
                updated_current["title_depth_exposed_depth"] = int(artifact_structured.get("title_depth_exposed_depth", 0) or 0)
                updated_current["title_depth_minimal_sufficient_depth"] = int(
                    artifact_structured.get("title_depth_minimal_sufficient_depth", 0) or 0
                )
                updated_current["title_depth_assessment"] = str(artifact_structured.get("title_depth_assessment", "")).strip()
                updated_current["title_depth_reuse_bias"] = (
                    str(updated_current.get("title_depth_reuse_bias", "")).strip() or "determinate_reuse"
                )
                lookup["current"] = updated_current
                node.metadata["structured_learning"] = updated_current
                not_elaboration = node.metadata.get("not_elaboration")
                if isinstance(not_elaboration, Mapping):
                    node.metadata["not_elaboration"] = {**not_elaboration, **updated_current}
        support_effect = "high" if closure_ready else "medium"
        confidence = "high" if closure_ready else "medium"
        evidence = Evidence(
            id=self.runtime_make_id("evidence", node.semantic_unit),
            node_id=node.id,
            observation=f"Reused prior {answer_match_kind.replace('_', ' ')} residue for '{node.semantic_unit}': {reusable_answer}.",
            source="committed_state",
            context={
                "generated_by": "artifact_instantiation",
                "artifact_id": answer_artifact.id,
                "reuse_mode": answer_match_kind,
                "answer_reuse_preference": answer_preference,
                "matched_lookup_keys": lookup["matched_lookup_keys"],
                "question": answer_artifact.content.get("question", ""),
                "answer": reusable_answer,
                "artifact_answer": answer,
                "function_bit": answer_artifact.function_bit,
                "cross_boundary_execution": executable_answer,
                "execution_result": execution.to_dict() if execution is not None else {},
                "invocation_payload": json_safe(invocation_payload),
                "structured_learning": lookup["current"],
            },
            support_effect=support_effect,
            confidence=confidence,
            provenance=provenance,
        )
        self.state.attach_evidence(evidence)
        if closure_ready:
            node.metadata["direct_resolution_ready_for_commitment"] = True
            node.metadata["direct_resolution_answer"] = reusable_answer
            node.metadata["direct_resolution_confidence"] = confidence
            node.metadata["direct_resolution_answer_kind"] = "learned_reuse"
            node.metadata["direct_resolution_closure_status"] = "ready"
        else:
            node.metadata["related_support_only"] = True
        self.state.record_step(
            kind="artifact_instantiation",
            node_id=node.id,
            intent="Instantiate admitted reusable residue when the active item has been encountered before under a compatible non-achievedness form.",
            action="reuse prior encountered or bridge non-achievedness as current support",
            result="support-bearing witness instantiated from prior residue",
            evaluation="the controller reused a previously encountered non-achievedness rather than re-litigating it from scratch",
            payload={
                "artifact_id": answer_artifact.id,
                "answer": reusable_answer,
                "match_kind": answer_match_kind,
                "answer_reuse_preference": answer_preference,
                "matched_lookup_keys": lookup["matched_lookup_keys"],
            },
        )
        return True

    summary = ", ".join(artifact.title for artifact in matched_artifacts[:3])
    support_effect = ThreeLevel.MEDIUM if effective_match_kind == "composition_related" else ThreeLevel.LOW
    evidence = Evidence(
        id=self.runtime_make_id("evidence", node.semantic_unit),
        node_id=node.id,
        observation=f"Prior {effective_match_kind.replace('_', ' ')} support is available for '{node.semantic_unit}': {summary}.",
        source="committed_state",
        context={
            "generated_by": "structured_learning_lookup",
            "artifact_ids": [artifact.id for artifact in matched_artifacts[:6]],
            "reuse_mode": effective_match_kind,
            "structured_learning": lookup["current"],
        },
        support_effect=support_effect,
        confidence=ThreeLevel.MEDIUM,
        provenance=provenance,
    )
    self.state.attach_evidence(evidence)
    self.state.record_step(
        kind="artifact_instantiation",
        node_id=node.id,
        intent="Use prior decomposition-related or composition-related non-achievedness structure as present support when exact reuse is unavailable.",
        action="attach structured learning support from prior related non-achievedness",
        result="related prior residue became current support",
        evaluation="the controller reused decomposition/composition structure from earlier encounters without pretending that structure alone is a final answer",
        payload={
            "match_kind": effective_match_kind,
            "artifact_ids": [artifact.id for artifact in matched_artifacts[:6]],
            "artifact_origin_report": self.learned_artifact_origin_report([artifact.id for artifact in matched_artifacts[:6]]),
        },
    )
    return True
