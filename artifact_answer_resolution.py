# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from applied_theory_types import Artifact, BoundaryShapeTerm
from prompt_directives import semantic_prompt_directive_profile


def _formula_like_executable_answer_text(
    self,
    artifact: Artifact,
    *,
    semantic_unit: str,
    content: Mapping[str, Any],
) -> str:
    semantic_text = str(semantic_unit or "").strip()
    if not semantic_text or not self.prompt_prefers_direct_knowledge_answer(semantic_text):
        return ""
    directive = semantic_prompt_directive_profile(semantic_text)
    directive_kind = str(directive.get("kind", "")).strip()
    requires_formula = bool(directive.get("requires_formula", False))
    if directive_kind not in {"state", "derive", "identify_reusable_substrate"} and not requires_formula:
        return ""
    expression = str(content.get("compute_expression", "")).strip()
    output_field = str(content.get("output_field", "")).strip()
    python_script = str(content.get("python_script", "")).strip()
    if python_script:
        script_expression, script_output = self.expression_ability_script_constants(python_script)
        if not expression:
            expression = script_expression
        if not output_field:
            output_field = script_output
    if not expression:
        return ""
    output_contract = content.get("output_contract", {})
    if not output_field and isinstance(output_contract, Mapping):
        output_field = next(
            (
                str(key).strip()
                for key in output_contract.keys()
                if str(key).strip()
            ),
            "",
        )
    input_contract = content.get("input_contract", {})
    input_keys = (
        [str(key).strip() for key in input_contract.keys() if str(key).strip()]
        if isinstance(input_contract, Mapping)
        else []
    )
    formula_text = f"{output_field} = {expression}" if output_field else expression
    question = str(content.get("question", "")).strip()
    pieces: list[str] = []
    if question:
        pieces.append(question)
    pieces.append(formula_text)
    if input_keys:
        pieces.append(f"inputs: {', '.join(input_keys)}")
    if output_field:
        pieces.append(f"output: {output_field}")
    return ". ".join(piece for piece in pieces if piece)


def artifact_answer_text(
    self,
    artifact: Artifact,
    *,
    semantic_unit: str = "",
    explicit_payload: Any = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like reuse closure, executable invocation, and structural answer recovery from a selected artifact, helps with turning one chosen artifact into the best available answer surface.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_answer_text(self=controller, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'), semantic_unit='Calculate force from mass=3 and acceleration=4.', explicit_payload={'mass': 3, 'acceleration': 4})`
        Output: '12'

    Args:
        self: Bound controller instance that owns runtime state, execution, and Prolog resolution.
        artifact: Value for `artifact` used by `artifact_answer_text`. Expected type: `Artifact`.
        semantic_unit: Value for `semantic_unit` used by `artifact_answer_text`. Expected type: `str`. Defaults to `''`.
        explicit_payload: Value for `explicit_payload` used by `artifact_answer_text`. Expected type: `Any`. Defaults to `None`.

    Returns:
        str: Result produced by `artifact_answer_text`.
    """
    content = self.artifact_runtime_content(artifact)
    effective_semantic_unit = self.artifact_query_semantic_unit(
        artifact,
        semantic_unit=semantic_unit,
        explicit_payload=explicit_payload,
    )
    if self.artifact_is_executable_function(artifact):
        formula_like_answer = _formula_like_executable_answer_text(
            self,
            artifact,
            semantic_unit=effective_semantic_unit or semantic_unit,
            content=content,
        )
        if formula_like_answer and explicit_payload in (None, "", [], {}):
            return formula_like_answer
        execution = self.execute_function_artifact(
            artifact,
            semantic_unit=semantic_unit,
            explicit_payload=explicit_payload,
        )
        if execution.ok:
            execution_answer = str(execution.answer or "").strip()
            if execution_answer:
                return execution_answer
        if formula_like_answer:
            return formula_like_answer
    prolog_answer = self.artifact_prolog_clause_answer(
        artifact,
        semantic_unit=effective_semantic_unit,
    )
    if prolog_answer:
        return prolog_answer
    answer = str(content.get("answer", "")).strip()
    if answer:
        return answer
    latent_answer = self.artifact_latent_knowledge_answer_text(
        artifact,
        semantic_unit=effective_semantic_unit or semantic_unit,
    )
    if latent_answer:
        return latent_answer
    if not self.artifact_is_executable_function(artifact):
        return ""
    return ""


def derive_related_solution_support(
    self,
    structured: Mapping[str, Any],
    related_artifact_ids: Iterable[str],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like closing a prompt from previously related artifacts, helps with choosing the strongest related reusable answer and exposing the capability support that came with it.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `derive_related_solution_support(self=controller, structured={'goal': 'Calculate force from mass and acceleration.', 'boundary_shape': ('a*', 'd*')}, related_artifact_ids=['artifact-force-law', 'artifact-multiplication'])`
        Output: {'answer': '12', 'source_artifact_id': 'artifact-force-law', 'source_artifact_title': 'Physics / Force From Mass And Acceleration', 'answer_preference': 'lookup_overlap', 'capability_artifact_ids': ['artifact-force-law']}

    Args:
        self: Bound controller instance that owns runtime state and related-artifact lookup.
        structured: Value for `structured` used by `derive_related_solution_support`. Expected type: `Mapping[str, Any]`.
        related_artifact_ids: Value for `related_artifact_ids` used by `derive_related_solution_support`. Expected type: `Iterable[str]`.

    Returns:
        dict[str, Any]: Result produced by `derive_related_solution_support`.
    """
    candidates: dict[str, list[Artifact]] = {
        "same_not": [],
        "same_key": [],
        "same_composed_family": [],
        "covers_components": [],
        "lookup_overlap": [],
    }
    capability_artifact_ids = self.supporting_capability_artifact_ids(related_artifact_ids)

    for artifact_id in related_artifact_ids:
        normalized_id = str(artifact_id).strip()
        if not normalized_id:
            continue
        artifact = self.state.artifacts.get(normalized_id) or self.state.learned_artifacts.get(normalized_id)
        if artifact is None:
            continue
        prior = self.artifact_structured_learning_view(artifact)
        preference = self.answer_reuse_preference(structured, prior, artifact)
        if preference is None:
            continue
        candidates[preference].append(artifact)

    for preference in ("same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap"):
        if not candidates[preference]:
            continue
        ranked_candidates = sorted(
            candidates[preference],
            key=lambda artifact: self.answer_candidate_rank(
                artifact,
                semantic_unit=str(structured.get("goal", "")).strip() or str(structured.get("encountered_not", "")).strip(),
                current_boundary_shape=structured.get("boundary_shape", ()),
            ),
        )
        for artifact in ranked_candidates:
            answer = self.artifact_answer_text(
                artifact,
                semantic_unit=str(structured.get("goal", "")).strip() or str(structured.get("encountered_not", "")).strip(),
            )
            if not answer:
                continue
            return {
                "answer": answer,
                "source_artifact_id": artifact.id,
                "source_artifact_title": artifact.title,
                "answer_preference": preference,
                "capability_artifact_ids": capability_artifact_ids,
            }

    return {
        "answer": "",
        "source_artifact_id": "",
        "source_artifact_title": "",
        "answer_preference": "",
        "capability_artifact_ids": capability_artifact_ids,
    }


def fallback_executable_answer_candidate(
    self,
    *,
    current: Mapping[str, Any],
    semantic_unit: str,
) -> tuple[Artifact | None, str, str]:
    """
    High Level Purpose:
        In circumstances like compute-oriented closure where no direct answer has been selected yet, helps with finding an invokable executable artifact that already matches the current semantic shape closely enough to reuse.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `fallback_executable_answer_candidate(self=controller, current={'goal': 'Calculate current from voltage and resistance.'}, semantic_unit='Calculate I from V=12 and R=4.')`
        Output: (Artifact(id='artifact-ohm', title='Physics / Current From Voltage And Resistance', artifact_type='ability', representation='python_script'), 'lookup_overlap', 'lookup_overlap')

    Args:
        self: Bound controller instance that owns reusable-artifact access and invocation-payload derivation.
        current: Value for `current` used by `fallback_executable_answer_candidate`. Expected type: `Mapping[str, Any]`.
        semantic_unit: Value for `semantic_unit` used by `fallback_executable_answer_candidate`. Expected type: `str`.

    Returns:
        tuple[Artifact | None, str, str]: Result produced by `fallback_executable_answer_candidate`.
    """
    for preference in ("same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap"):
        for artifact in self.reusable_artifact_candidates():
            if not self.artifact_is_executable_function(artifact):
                continue
            prior = self.artifact_structured_learning_view(artifact)
            candidate_preference = self.answer_reuse_preference(current, prior, artifact)
            if candidate_preference != preference:
                continue
            invocation_payload = self.derive_artifact_invocation_payload(
                artifact,
                semantic_unit=semantic_unit,
            )
            payload_ok, _, _ = self.artifact_invocation_payload_coverage(
                artifact,
                invocation_payload=invocation_payload,
            )
            if not payload_ok:
                continue
            match_kind = self.classify_structured_learning_match(current, prior) or candidate_preference
            return artifact, match_kind, candidate_preference
    return None, "none", ""


def best_invokable_artifact_candidate(
    self,
    *,
    semantic_unit: str,
    current_boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like numeric or template-style prompts that already expose usable inputs, helps with selecting the strongest invokable executable artifact from the reusable pool without requiring exact prior-encounter classification.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `best_invokable_artifact_candidate(self=controller, semantic_unit='Calculate I from V=12 and R=4.', current_boundary_shape=('a*', 'd*'))`
        Output: Artifact(id='artifact-ohm', title='Physics / Current From Voltage And Resistance', artifact_type='ability', representation='python_script')

    Args:
        self: Bound controller instance that owns reusable-artifact access and answer ranking.
        semantic_unit: Value for `semantic_unit` used by `best_invokable_artifact_candidate`. Expected type: `str`.
        current_boundary_shape: Value for `current_boundary_shape` used by `best_invokable_artifact_candidate`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.

    Returns:
        Artifact | None: Result produced by `best_invokable_artifact_candidate`.
    """
    candidates: list[Artifact] = []
    for artifact in self.reusable_artifact_candidates():
        if not self.artifact_is_executable_function(artifact):
            continue
        invocation_payload = self.derive_artifact_invocation_payload(
            artifact,
            semantic_unit=semantic_unit,
        )
        payload_ok, _, _ = self.artifact_invocation_payload_coverage(
            artifact,
            invocation_payload=invocation_payload,
        )
        if not payload_ok:
            continue
        candidates.append(artifact)
    if not candidates:
        return None
    candidates.sort(
        key=lambda artifact: self.answer_candidate_rank(
            artifact,
            semantic_unit=semantic_unit,
            current_boundary_shape=current_boundary_shape,
        )
    )
    return candidates[0]
