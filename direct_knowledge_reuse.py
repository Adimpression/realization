# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from applied_theory_types import Artifact, BoundaryShapeTerm
from prompt_directives import (
    prompt_directive_support_markers,
    semantic_prompt_directive_profile,
    semantic_question_focus_text,
)
from retrieval_ranking import (
    artifact_focus_alignment_score,
    artifact_is_structured_learning_record,
    artifact_selection_text,
    selection_signal_tokens,
    text_alignment_rank,
)
from semantic_text import (
    collapse_ws,
    learning_core_tokens,
    structured_text_list,
    titleize_semantic_unit,
)
from semantic_prompt_posture import semantic_prompt_action_posture
from title_semantics import display_title_leaf_text


def persisted_direct_knowledge_candidates(
    self,
    *,
    semantic_unit: str,
) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like direct explanatory prompts whose best reusable answer was not pulled into the initial in-memory learning context, helps with scanning persisted artifacts for additional answer-bearing candidates aligned to the requested concept.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `persisted_direct_knowledge_candidates(self=controller, semantic_unit='What is gene expression?')`
        Output: [Artifact(id='artifact-gene-expression', title='Biology / Gene Expression', artifact_type='knowledge', representation='yaml')]

    Args:
        self: Bound controller instance that owns runtime state and artifact-store access.
        semantic_unit: Value for `semantic_unit` used by `persisted_direct_knowledge_candidates`. Expected type: `str`.

    Returns:
        list[Artifact]: Result produced by `persisted_direct_knowledge_candidates`.
    """
    if not self.prompt_prefers_direct_knowledge_answer(semantic_unit):
        return []
    prompt_posture = semantic_prompt_action_posture(semantic_unit)
    guidance_prompt = prompt_posture == "next_step_guidance"
    focus_text = semantic_question_focus_text(semantic_unit)
    prompt_tokens = selection_signal_tokens(semantic_unit) if guidance_prompt else set()
    if not focus_text and not guidance_prompt:
        return []
    try:
        persisted = self.artifact_store.load_all_artifacts()
    except Exception:
        return []
    candidates: list[Artifact] = []
    for artifact in persisted:
        if artifact.admissibility == "rejected":
            continue
        if artifact_is_structured_learning_record(artifact):
            continue
        if not self.artifact_answer_text(artifact, semantic_unit=semantic_unit):
            continue
        if guidance_prompt and not focus_text:
            if not (prompt_tokens & selection_signal_tokens(artifact_selection_text(artifact))):
                continue
        elif artifact_focus_alignment_score(artifact, focus_text) <= 0:
            continue
        candidates.append(artifact)
    return candidates


def compose_direct_knowledge_answer(
    self,
    *,
    semantic_unit: str,
    primary_artifact: Artifact,
    primary_answer: str,
    focus_candidates: Iterable[Artifact] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like direct explanatory prompts that need a cleaner reusable concept answer than one narrow section fragment provides, helps with composing a focused answer from the selected artifact plus nearby knowledge from the same learned family.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `compose_direct_knowledge_answer(self=controller, semantic_unit='What is photosynthesis?', primary_artifact=Artifact(id='artifact-photo', title='Biology / Simplified Input Output Relation', artifact_type='knowledge', representation='yaml'), primary_answer='carbon dioxide + water + light -> glucose + oxygen', focus_candidates=[])`
        Output: 'Photosynthesis is a simplified input output relation. carbon dioxide + water + light -> glucose + oxygen'

    Args:
        self: Bound controller instance that owns runtime state and reusable-artifact access.
        semantic_unit: Value for `semantic_unit` used by `compose_direct_knowledge_answer`. Expected type: `str`.
        primary_artifact: Value for `primary_artifact` used by `compose_direct_knowledge_answer`. Expected type: `Artifact`.
        primary_answer: Value for `primary_answer` used by `compose_direct_knowledge_answer`. Expected type: `str`.
        focus_candidates: Value for `focus_candidates` used by `compose_direct_knowledge_answer`. Expected type: `Iterable[Artifact] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `compose_direct_knowledge_answer`.
    """
    answer = collapse_ws(str(primary_answer or "").strip())
    if not self.prompt_prefers_direct_knowledge_answer(semantic_unit):
        return answer
    directive = semantic_prompt_directive_profile(semantic_unit)
    directive_kind = collapse_ws(str(directive.get("kind", "")).strip())
    focus_text = collapse_ws(semantic_question_focus_text(semantic_unit))
    allow_cross_source_support = bool(focus_text) and bool(
        re.match(r"^\s*what\s+is\b", str(semantic_unit or ""), flags=re.IGNORECASE)
    )
    if not focus_text and directive_kind not in {"derive", "construct", "distinguish", "identify_reusable_substrate"}:
        return answer
    focus_lower = focus_text.lower()
    leaf_text = display_title_leaf_text(str(primary_artifact.title or "").strip())
    content = primary_artifact.content if isinstance(primary_artifact.content, Mapping) else {}
    source_title = collapse_ws(str(content.get("source_title", "")).strip())
    compared_terms = structured_text_list(directive.get("compared_terms", []))
    compared_terms_lower = [term.lower() for term in compared_terms]
    compared_term_token_map = {
        term.lower(): set(learning_core_tokens(term))
        for term in compared_terms
        if set(learning_core_tokens(term))
    }
    focus_tokens = set(learning_core_tokens(focus_text))
    primary_markers, secondary_markers = prompt_directive_support_markers(directive_kind)

    candidate_entries: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()
    for candidate in [primary_artifact, *(focus_candidates or [])]:
        candidate_id = str(getattr(candidate, "id", "")).strip()
        if candidate_id and candidate_id in seen_candidate_ids:
            continue
        if candidate_id:
            seen_candidate_ids.add(candidate_id)
        candidate_content = candidate.content if isinstance(candidate.content, Mapping) else {}
        candidate_source_title = collapse_ws(str(candidate_content.get("source_title", "")).strip())
        if source_title and candidate_source_title and source_title.lower() != candidate_source_title.lower():
            continue
        candidate_answer = collapse_ws(self.artifact_answer_text(candidate, semantic_unit=semantic_unit))
        if not candidate_answer:
            continue
        candidate_text = collapse_ws(
            " ".join(
                part
                for part in (
                    str(getattr(candidate, "title", "")).strip(),
                    artifact_selection_text(candidate),
                    candidate_answer,
                )
                if collapse_ws(part)
            )
        )
        candidate_lower = candidate_text.lower()
        candidate_signal_tokens = selection_signal_tokens(candidate_text)
        candidate_entries.append(
            {
                "artifact": candidate,
                "answer": candidate_answer,
                "lower": candidate_lower,
                "signal_tokens": candidate_signal_tokens,
                "focus_alignment": artifact_focus_alignment_score(candidate, focus_text) if focus_text else 0,
                "focus_hits": len(focus_tokens & candidate_signal_tokens),
                "compared_hits": sum(1 for term in compared_terms_lower if term and term in candidate_lower),
                "has_formula": bool(re.search(r"[A-Za-z0-9_]\s*=\s*[A-Za-z0-9_(]", candidate_answer)) or "$$" in candidate_answer,
                "has_primary_marker": any(marker in candidate_lower for marker in primary_markers),
                "has_secondary_marker": any(marker in candidate_lower for marker in secondary_markers),
                "is_primary": candidate.id == primary_artifact.id,
            }
        )

    if not candidate_entries:
        return answer

    candidate_entries.sort(
        key=lambda entry: (
            0 if entry["is_primary"] else 1,
            0 if entry["focus_alignment"] > 0 else 1,
            0 if entry["has_primary_marker"] else 1,
            0 if entry["has_secondary_marker"] else 1,
            -int(entry["compared_hits"]),
            -int(entry["focus_hits"]),
            0 if entry["has_formula"] else 1,
            str(entry["artifact"].title).lower(),
        )
    )

    combined_parts: list[str] = []
    if focus_lower and focus_lower not in answer.lower() and leaf_text and not self.looks_like_generic_markdown_current_identity(leaf_text, encounter_heading=leaf_text):
        combined_parts.append(f"{titleize_semantic_unit(focus_text) or focus_text}: {leaf_text}.")
    if answer:
        combined_parts.append(answer)
    combined_text = collapse_ws(" ".join(part for part in combined_parts if part))
    supplement_count = 0

    candidate_list = [artifact for artifact in (focus_candidates or []) if artifact.id != primary_artifact.id]
    for candidate in candidate_list:
        candidate_content = candidate.content if isinstance(candidate.content, Mapping) else {}
        candidate_source_title = collapse_ws(str(candidate_content.get("source_title", "")).strip())
        if source_title and candidate_source_title and source_title.lower() != candidate_source_title.lower():
            continue
        supplement = collapse_ws(self.artifact_answer_text(candidate, semantic_unit=semantic_unit))
        if not supplement:
            continue
        if supplement.lower() in combined_text.lower():
            continue
        if focus_lower not in supplement.lower() and focus_lower not in artifact_selection_text(candidate).lower():
            continue
        if not (selection_signal_tokens(supplement) - selection_signal_tokens(combined_text)):
            continue
        combined_parts.append(supplement)
        combined_text = collapse_ws(" ".join(part for part in combined_parts if part))
        supplement_count += 1
        if supplement_count >= 2:
            break

    if supplement_count == 0:
        primary_tokens = selection_signal_tokens(f"{focus_text} {answer} {source_title}")
        supplement_candidates: list[tuple[int, tuple[int, int, int, int], str]] = []
        for candidate in self.reusable_artifact_candidates():
            if candidate.id == primary_artifact.id or self.artifact_is_executable_function(candidate):
                continue
            candidate_content = candidate.content if isinstance(candidate.content, Mapping) else {}
            candidate_source_title = collapse_ws(str(candidate_content.get("source_title", "")).strip())
            if (
                source_title
                and candidate_source_title
                and candidate_source_title.lower() != source_title.lower()
                and not allow_cross_source_support
            ):
                continue
            if source_title and not candidate_source_title:
                continue
            supplement = collapse_ws(self.artifact_answer_text(candidate, semantic_unit=semantic_unit))
            if not supplement or supplement.lower() in combined_text.lower():
                continue
            candidate_text = artifact_selection_text(candidate)
            shared_tokens = len(primary_tokens & selection_signal_tokens(f"{candidate_text} {supplement}"))
            if shared_tokens < 1:
                continue
            supplement_candidates.append(
                (
                    -shared_tokens,
                    text_alignment_rank(f"{focus_text} {answer}", f"{candidate_text} {supplement}"),
                    supplement,
                )
            )
        if supplement_candidates:
            supplement_candidates.sort()
            combined_parts.append(supplement_candidates[0][2])

    if directive_kind == "distinguish" and compared_terms:
        best_contrast = next(
            (
                entry
                for entry in candidate_entries
                if all(
                    term in entry["lower"]
                    or (
                        compared_term_token_map.get(term)
                        and len(compared_term_token_map[term] & entry["signal_tokens"]) >= 1
                    )
                    for term in compared_terms_lower
                )
                and (entry["has_primary_marker"] or entry["has_secondary_marker"])
            ),
            None,
        )
        if best_contrast is not None:
            return collapse_ws(best_contrast["answer"])
        contrasted_parts: list[str] = []
        used_artifact_ids: set[str] = set()
        for term in compared_terms:
            term_lower = term.lower()
            term_tokens = compared_term_token_map.get(term_lower, set())
            term_entry = next(
                (
                    entry
                    for entry in candidate_entries
                    if (
                        term_lower in entry["lower"]
                        or (term_tokens and len(term_tokens & entry["signal_tokens"]) >= 1)
                    )
                    and str(entry["artifact"].id).strip() not in used_artifact_ids
                ),
                None,
            )
            if term_entry is None:
                continue
            used_artifact_ids.add(str(term_entry["artifact"].id).strip())
            contrasted_parts.append(f"{titleize_semantic_unit(term) or term}: {term_entry['answer']}")
        if contrasted_parts:
            return collapse_ws(" ".join(contrasted_parts))

    if directive_kind in {"derive", "construct"}:
        chain_entries = sorted(
            candidate_entries,
            key=lambda entry: (
                0 if entry["has_primary_marker"] else 1,
                0 if entry["has_formula"] else 1,
                0 if entry["focus_alignment"] > 0 else 1,
                -int(entry["focus_hits"]),
                str(entry["artifact"].title).lower(),
            ),
        )
        chain_parts: list[str] = []
        seen_chain_snippets: set[str] = set()
        for entry in chain_entries:
            snippet = collapse_ws(str(entry["answer"]).strip())
            snippet_lower = snippet.lower()
            if not snippet or snippet_lower in seen_chain_snippets:
                continue
            if any(existing in snippet_lower for existing in seen_chain_snippets):
                continue
            seen_chain_snippets.add(snippet_lower)
            if not chain_parts:
                chain_parts.append(snippet)
            elif len(chain_parts) >= 2:
                chain_parts.append(snippet if re.match(r"^(therefore|thus|so)\b", snippet, flags=re.IGNORECASE) else f"Therefore, {snippet}")
            else:
                chain_parts.append(snippet if re.match(r"^(then|next|using|from|substitute|rearrange)\b", snippet, flags=re.IGNORECASE) else f"Then, {snippet}")
            if len(chain_parts) >= 3:
                break
        if chain_parts:
            chain_text = collapse_ws(" ".join(chain_parts))
            if focus_text and focus_lower not in chain_text.lower():
                return collapse_ws(f"{titleize_semantic_unit(focus_text) or focus_text}: {chain_text}")
            return chain_text

    if directive_kind == "identify_reusable_substrate":
        substrate_entry = next(
            (
                entry
                for entry in candidate_entries
                if any(
                    marker in entry["lower"]
                    for marker in (
                        "substrate",
                        "broader",
                        "underlying",
                        "reusable substrate",
                        "reuses",
                        "family",
                        "ground",
                        "base",
                        "inverse-square",
                        "inverse square",
                        "multiplicative combination",
                        "special case",
                    )
                )
            ),
            None,
        )
        if substrate_entry is not None:
            return collapse_ws(substrate_entry["answer"])

    if directive_kind == "state" and bool(directive.get("requires_formula", False)):
        if "=" not in combined_text and "$$" not in combined_text:
            formula_entry = next((entry for entry in candidate_entries if entry["has_formula"]), None)
            if formula_entry is not None:
                combined_formula_text = collapse_ws(
                    " ".join(part for part in (combined_text, str(formula_entry["answer"]).strip()) if collapse_ws(part))
                )
                if combined_formula_text:
                    return combined_formula_text

    return collapse_ws(" ".join(part for part in combined_parts if part))


def focused_direct_knowledge_candidates(
    self,
    *,
    semantic_unit: str,
    current_boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
    candidate_pairs: Iterable[tuple[str, Artifact]] | None = None,
    include_unmatched_pool: bool = False,
) -> list[tuple[str, Artifact]]:
    """
    High Level Purpose:
        In circumstances like direct explanatory prompts that should resolve through prior learned knowledge, helps with collecting focus-aligned answer-bearing knowledge artifacts from classified reuse matches and the broader reusable pool.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `focused_direct_knowledge_candidates(self=controller, semantic_unit='What is mass conservation in a reaction?', current_boundary_shape=('d*',), candidate_pairs=[('lookup_overlap', Artifact(id='artifact-conservation', title='Chemistry / Conservation', artifact_type='knowledge', representation='yaml'))], include_unmatched_pool=True)`
        Output: [('lookup_overlap', Artifact(id='artifact-conservation', title='Chemistry / Conservation', artifact_type='knowledge', representation='yaml'))]

    Args:
        self: Bound controller instance that owns runtime state and reusable-artifact access.
        semantic_unit: Value for `semantic_unit` used by `focused_direct_knowledge_candidates`. Expected type: `str`.
        current_boundary_shape: Value for `current_boundary_shape` used by `focused_direct_knowledge_candidates`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.
        candidate_pairs: Value for `candidate_pairs` used by `focused_direct_knowledge_candidates`. Expected type: `Iterable[tuple[str, Artifact]] | None`. Defaults to `None`.
        include_unmatched_pool: Value for `include_unmatched_pool` used by `focused_direct_knowledge_candidates`. Expected type: `bool`. Defaults to `False`.

    Returns:
        list[tuple[str, Artifact]]: Result produced by `focused_direct_knowledge_candidates`.
    """
    if not self.prompt_prefers_direct_knowledge_answer(semantic_unit):
        return []
    prompt_posture = semantic_prompt_action_posture(semantic_unit)
    guidance_prompt = prompt_posture == "next_step_guidance"
    knowledge_focus = semantic_question_focus_text(semantic_unit)
    directive_kind = collapse_ws(str(semantic_prompt_directive_profile(semantic_unit).get("kind", "")).strip())
    prompt_tokens = selection_signal_tokens(semantic_unit) if guidance_prompt else set()
    focus_signal_tokens = selection_signal_tokens(knowledge_focus) if knowledge_focus else set()
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
    distinctive_focus_tokens = {
        token
        for token in learning_core_tokens(knowledge_focus)
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
    substrate_focus_anchor_stop_tokens = {
        "force",
        "law",
        "relation",
        "formula",
        "equation",
        "quantity",
        "field",
        "strength",
        "motion",
        "change",
        "rate",
        "mass",
        "power",
        "energy",
        "general",
        "broader",
        "family",
        "substrate",
        "specialization",
        "special",
        "determinate",
    }
    substrate_focus_anchor_tokens = {
        token
        for token in distinctive_focus_tokens
        if token not in substrate_focus_anchor_stop_tokens
    }
    if not knowledge_focus and not guidance_prompt:
        return []

    prioritized: list[tuple[str, Artifact]] = list(candidate_pairs or [])
    if include_unmatched_pool:
        matched_ids = {artifact.id for _, artifact in prioritized}
        for artifact in self.reusable_artifact_candidates():
            if artifact.id in matched_ids:
                continue
            prioritized.append(("focus_alignment", artifact))
            matched_ids.add(artifact.id)
        for artifact in self.persisted_direct_knowledge_candidates(
            semantic_unit=semantic_unit,
        ):
            if artifact.id in matched_ids:
                continue
            prioritized.append(("focus_alignment_store", artifact))
            matched_ids.add(artifact.id)

    filtered: list[tuple[str, Artifact]] = []
    for preference, candidate in prioritized:
        if artifact_is_structured_learning_record(candidate):
            continue
        answer_text = self.artifact_answer_text(candidate, semantic_unit=semantic_unit)
        if not answer_text:
            continue
        combined_candidate_text = collapse_ws(
            " ".join(
                part
                for part in (
                    artifact_selection_text(candidate),
                    answer_text,
                )
                if collapse_ws(part)
            )
        ).lower()
        candidate_tokens = selection_signal_tokens(
            combined_candidate_text
        )
        has_substrate_markers = (
            directive_kind == "identify_reusable_substrate"
            and any(marker in combined_candidate_text for marker in substrate_markers)
        )
        if guidance_prompt and not knowledge_focus:
            if not (prompt_tokens & selection_signal_tokens(artifact_selection_text(candidate))):
                continue
        else:
            if has_substrate_markers:
                if substrate_focus_anchor_tokens and not any(
                    candidate_token.startswith(anchor_token)
                    or anchor_token.startswith(candidate_token)
                    for anchor_token in substrate_focus_anchor_tokens
                    for candidate_token in candidate_tokens
                ):
                    continue
                filtered.append((preference, candidate))
                continue
            if distinctive_focus_tokens:
                distinctive_hits = len(distinctive_focus_tokens & candidate_tokens)
                required_distinctive_hits = 1 if len(distinctive_focus_tokens) == 1 else 2
                if distinctive_hits < min(required_distinctive_hits, len(distinctive_focus_tokens)):
                    continue
                if (
                    len(distinctive_focus_tokens) >= 4
                    and distinctive_hits * 3 < len(distinctive_focus_tokens)
                ):
                    continue
            elif focus_signal_tokens and not (focus_signal_tokens & candidate_tokens):
                continue
            elif artifact_focus_alignment_score(candidate, knowledge_focus) <= 0:
                continue
        filtered.append((preference, candidate))

    preference_order = ("same_not", "same_key", "same_composed_family", "covers_components", "lookup_overlap", "focus_alignment_store", "focus_alignment")
    filtered.sort(
        key=lambda item: (
            self.answer_candidate_rank(
                item[1],
                semantic_unit=semantic_unit,
                current_boundary_shape=current_boundary_shape,
            ),
            preference_order.index(item[0]) if item[0] in preference_order else len(preference_order),
        ),
    )
    return filtered
