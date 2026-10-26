# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from textwrap import dedent
from typing import Any

from applied_theory_types import (
    Artifact,
    ArtifactType,
    ArtifactRepresentation,
    BoundaryShapeTerm,
    ProposalObject,
    ProposalType,
    SemanticNode,
    SupplementMode,
)
from execution_frameworks import (
    executor_framework_representation,
    supported_executor_framework_prompt_block,
)
from markdown_ir import (
    MarkdownDocumentIR,
    bounded_markdown_encounter_prompt_view,
    bounded_markdown_learning_prompt_view,
    compact_markdown_encounter_records,
    is_generic_synthesis_field_name,
    looks_like_placeholder_python_script,
    markdown_caller_facing_question,
    markdown_direct_expression_mapping,
    markdown_document_symbol_aliases,
    markdown_encounter_aliases,
    markdown_encounter_question,
    markdown_learning_encounter_view,
)
from non_achievedness_normalization import normalize_not_elaboration_payload
from normalization_primitives import (
    normalize_artifact_admission,
    normalize_artifact_representation,
    normalize_artifact_reuse,
    normalize_artifact_type,
    normalize_learning_relation,
)
from realized_skill_semantics.execution import (
    ability_executor_framework,
    executor_framework_content_key,
)
from prolog import (
    looks_like_prolog_title_identity,
    synthesize_prolog_formal_title_identity,
)
from retrieval_ranking import learning_overlap
from semantic_text import collapse_ws, learning_lookup_keys, ordered_unique, titleize_semantic_unit
from structured_learning_yaml import render_structured_learning_yaml
from title_semantics import (
    compose_display_title_identity,
    normalize_markdown_title_identity,
    normalize_semantic_title_identity,
    semantic_namespace_key,
    semantic_title_display_text,
    title_depth_theory_prompt_block,
    title_representation_is_prolog,
)


def propose_markdown_learning(self, node: SemanticNode, document: MarkdownDocumentIR, *, max_artifacts: int) -> ProposalObject:
    """
    High Level Purpose:
        In circumstances like turning one parsed markdown document into a small reusable knowledge-and-ability harvest, helps with asking the LLM for the bounded artifact-learning proposal that follows title-depth and decomposition rules.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `propose_markdown_learning(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), max_artifacts=3)`
        Output: ProposalObject(proposal_type=ProposalType.MARKDOWN_LEARNING, rationale='Markdown learning proposals are bounded ingestion plans for external-source harvest and remain governed before artifact admission.')

    Args:
        self: Bound controller instance that owns proposal requests and markdown fallback behavior.
        node: Value for `node` used by `propose_markdown_learning`. Expected type: `SemanticNode`.
        document: Value for `document` used by `propose_markdown_learning`. Expected type: `MarkdownDocumentIR`.
        max_artifacts: Value for `max_artifacts` used by `propose_markdown_learning`. Expected type: `int`.

    Returns:
        ProposalObject: Result produced by `propose_markdown_learning`.
    """
    fallback = self.fallback_markdown_learning(document, max_artifacts=max_artifacts)
    ir_view = bounded_markdown_learning_prompt_view(
        document,
        max_clusters=min(max(max_artifacts, 1) + 2, 6),
    )
    proposal = self.request_proposal(
        proposal_type=ProposalType.MARKDOWN_LEARNING,
        node=node,
        target_scope=document.title,
        instructions=dedent(
            f"""
            Learn reusable artifacts from a markdown document.
            The markdown has already been parsed into a structural ir. Work from that ir, not from raw markdown.

            Goal:
            - extract a small set of reusable artifacts that will help later questions close from prior learning
            - improve future Not-generation by turning the document into answer-bearing, lookup-friendly learning units

            Guidelines for applying title-depth theory to an IR segment:
            {title_depth_theory_prompt_block()}

            Rules:
            - stay faithful to the supplied markdown ir only
            - do not invent facts, equations, examples, or code that are not grounded in the document
            - prefer stable, reusable units such as definitions, laws, equations, and short explanatory notes
            - if the document contains decision, safety, or triage guidance, prefer scenario-bearing question/answer artifacts that state the next step clearly and preserve the main no-go condition when ambiguity is unresolved
            - do not use a raw section heading or a generic "What is section X?" prompt as the learned question
            - semantic_unit and question should express the reusable case, distinction, rule, or task that a later caller would actually ask about
            - if the ir exposes a parameterized equation or bounded procedure that should be reusable later, emit an ability artifact instead of only a prose note
            - do not ask the controller to hand-compile equations itself; if you emit an ability, you must provide the actual Python script artifact
            - if a section has nested equation/explanation/example parts, combine them into one answer-bearing artifact for that section
            - prefer broad reuse when the material is stable and introductory
            - keep each answer self-contained enough to answer a later user prompt without rereading the source
            - use plain language
            - return at most {max_artifacts} artifacts

            Return JSON with:
            - document_summary: one short summary of the document
            - artifacts: a list of artifact objects
            - rationale: one short reason for the extraction choices

            Each artifact object must include:
            - title
            - title_broader_category
            - title_current_identity
            - title_downward_decomposition
            - title_construction_rationale
            - title_collision_rationale
            - title_similies
            - semantic_unit
            - question
            - question_title_separation
            - related_titles
            - relation_rationale
            - aliases
            - component_nots
            - composed_not
            - sections
            - why_reusable
            - if artifact_type is knowledge, include answer
            - if artifact_type is ability, include the framework-matching executable body field plus content.input_contract and content.output_contract

            Question/semantic_unit guidance:
            - title is the final formal semantic identity of the artifact.
            - first infer title_current_identity as the minimally sufficient current identity.
            - if possible, infer exactly one title_broader_category above the current identity when that broader category genuinely grounds it.
            - if narrower ordered determination is genuinely needed below the current identity, place those later segments in title_downward_decomposition.
            - if no narrower title decomposition is needed, leave title_downward_decomposition empty; the broader category still may be useful.
            - final title should follow the decomposition law: title_broader_category / title_current_identity / title_downward_decomposition...
            - each later segment must depend on the earlier chain for intelligibility.
            - stop at minimal sufficient determination; do not over-segment for style.
            - prefer titles that would still make sense if exported alone without the source markdown beside them.
            - avoid raw outline residue such as section numbers or bare heading copies unless that residue is semantically constitutive.
            - if a heading is only organizational or meta (for example summary, named quantities, notes, distinctions, examples, reusable substrate), ignore that heading as the current identity and reconstruct the actual reusable semantic identity from the encounter content.
            - title_similies should list nearby phrasings or sibling-safe alternates that remain close in meaning without becoming the same identity.
            - use a reusable caller-facing form such as a concrete scenario, a direct task, or a bounded explanatory question
            - preserve the crucial differentiators from the document instead of collapsing nearby cases together
            - if the document distinguishes ambiguity from confirmation, the learned question should preserve that distinction
            - question must not merely restate the chosen title; explain the separation briefly in question_title_separation
            - if this artifact depends on a broader reusable substrate, a prior operation, or another semantic unit taught in the same document, list that dependency in related_titles
            - related_titles should point to reusable semantic dependencies, not to every nearby heading

            Optional:
            - artifact_type: knowledge or ability
            - representation: yaml, python_script, shell_script, or ansible_playbook
            - constraints

            Ability artifact rules:
            {supported_executor_framework_prompt_block(self.supported_executor_frameworks())}
            - for python3 artifacts, the script must include inline dependency metadata
            - for python3 artifacts, prefer stdin JSON as the input path, while keeping argparse available
            - for python3 artifacts, use msgspec and orjson in the script
            - every executable artifact should write structured JSON to stdout with status, answer, result, and notes when the underlying framework allows that directly

            Document title:
            {document.title}

            Bounded structural ir fragments:
            {json.dumps(ir_view, indent=2, sort_keys=True)}
            """
        ).strip(),
        fallback_payload=fallback,
        mode=SupplementMode.DEEP,
    )
    node.metadata["markdown_learning_proposal_id"] = proposal.id
    self.admit_proposal(
        proposal,
        rationale="Markdown learning proposals are bounded ingestion plans for external-source harvest and remain governed before artifact admission.",
    )
    return proposal


def propose_markdown_ability_learning(self, node: SemanticNode, document: MarkdownDocumentIR, *, max_artifacts: int) -> ProposalObject:
    """
    High Level Purpose:
        In circumstances like classifying reusable equation-bearing or template-bearing encounters inside one markdown lesson, helps with asking the LLM for the encounter-level ability-learning proposal before executable synthesis begins.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `propose_markdown_ability_learning(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), max_artifacts=3)`
        Output: ProposalObject(proposal_type=ProposalType.MARKDOWN_ABILITY_LEARNING, rationale='Markdown ability learning proposals are bounded executable-harvest plans grounded in the structural ir.')

    Args:
        self: Bound controller instance that owns proposal requests and markdown fallback behavior.
        node: Value for `node` used by `propose_markdown_ability_learning`. Expected type: `SemanticNode`.
        document: Value for `document` used by `propose_markdown_ability_learning`. Expected type: `MarkdownDocumentIR`.
        max_artifacts: Value for `max_artifacts` used by `propose_markdown_ability_learning`. Expected type: `int`.

    Returns:
        ProposalObject: Result produced by `propose_markdown_ability_learning`.
    """
    encounters = bounded_markdown_encounter_prompt_view(
        document,
        max_encounters=min(max(max_artifacts, 1) + 3, 8),
    )
    fallback = self.fallback_markdown_ability_learning(document, max_artifacts=max_artifacts)
    proposal = self.request_proposal(
        proposal_type=ProposalType.MARKDOWN_ABILITY_LEARNING,
        node=node,
        target_scope=document.title,
        instructions=dedent(
            f"""
            Learn reusable encounter artifacts from a markdown document after structural ir compilation.
            Work only from the supplied structural ir encounters. Do not invent equations, rules, procedures, or examples.

            Goal:
            - identify which encounters are equation-bearing, logic-bearing, template-bearing, definition-bearing, summary-bearing, or other
            - for each encounter, extract the reusable form it contributes

            Rules:
            - stay faithful to the supplied ir only
            - classify encounters from the ir itself; do not assume every cluster is equation-bearing
            - return one encounter record per reusable encounter you identify
            - use encounter_kind from: equation, logic, template, definition, summary, example, other
            - set parameterized=true only when the encounter defines a reusable mapping from named inputs to named outputs
            - preserve the document's own nouns, symbols, and quantities; do not substitute unrelated domains or laws
            - do not emit artifacts in this pass; use artifacts: []
            - do not emit prose-only knowledge artifacts here; those belong to the broader markdown learning pass

            Return JSON with:
            - encounters: a list of encounter objects
            - artifacts: always an empty list in this pass
            - rationale: one short reason for the extraction choices

            Each encounter object must include:
            - encounter_id
            - cluster_heading
            - encounter_kind
            - equation_bearing
            - parameterized
            - reusable
            - extracted_form
            - why_reusable
            - artifact_title_hint
            - artifact_title_hint may use / when it expresses minimally sufficient broader-to-narrower determination without namespace collision

            Document title:
            {document.title}

            Bounded structural ir encounters:
            {json.dumps(encounters, indent=2, sort_keys=True)}
            """
        ).strip(),
        fallback_payload=fallback,
        mode=SupplementMode.DEEP,
    )
    node.metadata["markdown_ability_learning_proposal_id"] = proposal.id
    self.admit_proposal(
        proposal,
        rationale="Markdown ability learning proposals are bounded executable-harvest plans grounded in the structural ir.",
    )
    return proposal


def propose_markdown_functionalization(
    self,
    node: SemanticNode,
    document: MarkdownDocumentIR,
    *,
    encounters: Sequence[Mapping[str, Any]],
    max_artifacts: int,
) -> ProposalObject:
    """
    High Level Purpose:
        In circumstances like converting already classified markdown encounters into reusable callable artifacts, helps with asking the LLM for the executable functionalization proposal bounded to those encounter records.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `propose_markdown_functionalization(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), encounters=[{'encounter_id': 'force-equation'}], max_artifacts=3)`
        Output: ProposalObject(proposal_type=ProposalType.MARKDOWN_FUNCTIONALIZATION, rationale='Markdown functionalization proposals are bounded executable extractions from already classified encounters.')

    Args:
        self: Bound controller instance that owns proposal requests and markdown fallback behavior.
        node: Value for `node` used by `propose_markdown_functionalization`. Expected type: `SemanticNode`.
        document: Value for `document` used by `propose_markdown_functionalization`. Expected type: `MarkdownDocumentIR`.
        encounters: Value for `encounters` used by `propose_markdown_functionalization`. Expected type: `Sequence[Mapping[str, Any]]`.
        max_artifacts: Value for `max_artifacts` used by `propose_markdown_functionalization`. Expected type: `int`.

    Returns:
        ProposalObject: Result produced by `propose_markdown_functionalization`.
    """
    fallback = self.fallback_markdown_functionalization(encounters, max_artifacts=max_artifacts)
    encounter_prompt_view = compact_markdown_encounter_records(
        encounters,
        max_encounters=min(max(max_artifacts, 1) + 3, 8),
    )
    proposal = self.request_proposal(
        proposal_type=ProposalType.MARKDOWN_FUNCTIONALIZATION,
        node=node,
        target_scope=document.title,
        instructions=dedent(
            f"""
            Convert already classified markdown encounters into executable reusable ability artifacts.
            Work only from the supplied encounter records. They may already be classified, or they may only contain candidate kinds from the structural ir.
            Do not invent new equations, rules, symbols, or examples.

            Goal:
            - find encounters that define a parameterized mapping or executable template
            - emit executor-backed ability artifacts only for encounters that directly match one of the supported executor frameworks

            Guidelines for applying title-depth theory to an IR segment:
            {title_depth_theory_prompt_block()}

            Parameterization rule:
            - if an encounter states a reusable relation over named quantities or placeholders, it is parameterized
            - a symbolic relation like output = input1 * input2 is parameterized when later runs can supply values for the named inputs
            - if an equation-bearing encounter contains named symbolic quantities and describes how one quantity depends on others, presume it is executable unless there is a concrete reason it is not
            - if an encounter includes an equation plus explanatory text or an example evaluation, that is enough to emit a callable function when the relation is computational
            - if the encounter is only explanatory prose with no executable mapping, do not emit an artifact

            Rules:
            - stay faithful to the encounter records only
            - if an encounter has only candidate_kinds, infer the actual reusable encounter kind from its text before deciding whether it is executable
            - prefer one ability artifact per reusable mapping family
            - do not emit knowledge artifacts here
            - every emitted artifact must include the actual framework-matching executable body, not only a description of one
            - do not copy placeholder values from the schema hint; fill the fields with real content from the encounter
            - if emitting a full python_script would be too verbose, you may leave content.python_script empty and instead provide:
              content.compute_expression as a Python expression over the named inputs,
              and content.output_field as the primary output key
            - when you use compute_expression, it must be directly grounded in the encounter and executable with the supplied input names
            - when executor_framework is python3, the script must include inline dependency metadata
            - when executor_framework is python3, the script must prefer stdin JSON, keep argparse available, use msgspec and orjson, and write JSON to stdout
            - if the encounter already presents a supported fenced executable form, prefer that direct framework match over reconstructing it into a different framework
            - return at most {max_artifacts} ability artifacts

            Return JSON with:
            - artifacts: a list of ability artifact objects
            - rationale: one short reason for the extraction choices

            Each artifact object must include:
            - artifact_type: ability
            - title
            - title_broader_category
            - title_current_identity
            - title_downward_decomposition
            - title_construction_rationale
            - title_collision_rationale
            - title_similies
            - semantic_unit
            - question
            - question_title_separation
            - related_titles
            - relation_rationale
            - aliases
            - component_nots
            - composed_not
            - sections
            - why_reusable
            - encounter_id
            - encounter_kind
            - equation_bearing
            - parameterized
            - representation
            - scope
            - reusability
            - admissibility
            - learning_relation
            - constraints
            - content.executor_framework
            - content.entrypoint
            - content.script_language
            - content.dependencies
            - content.input_contract
            - content.output_contract
            - the matching executable body field:
              python3 -> content.python_script
              bash -> content.shell_script
              ansible -> content.ansible_playbook

            Title guidance:
            - title is the final formal semantic identity of the emitted ability artifact
            - first infer title_current_identity as the minimally sufficient current identity
            - if possible, infer exactly one title_broader_category above it when that broader category genuinely grounds the ability
            - if narrower ordered determination is genuinely needed below the current identity, place those later segments in title_downward_decomposition
            - if no narrower title decomposition is needed, leave title_downward_decomposition empty; the broader category still may be useful
            - final title should follow the decomposition law: title_broader_category / title_current_identity / title_downward_decomposition...
            - do not segment decoratively or merely repeat the document heading
            - prefer titles that survive export outside the source document
            - avoid raw section numbering or bare heading-copy titles unless that residue is semantically constitutive
            - if the encounter heading is only organizational or meta, ignore it and reconstruct the actual executable identity from the relation, declared quantities, or distinction stated in the encounter
            - title_similies should contain nearby alternative phrasings that help retrieval without collapsing the chosen identity
            - question must reflect likely caller invocation and must not just restate the chosen title
            - if the ability reuses a previously taught substrate operation or broader reusable family from the same document, list that dependency in related_titles

            Document title:
            {document.title}

            Bounded encounter records:
            {json.dumps(encounter_prompt_view, indent=2, sort_keys=True)}
            """
        ).strip(),
        fallback_payload=fallback,
        mode=SupplementMode.DEEP,
    )
    node.metadata["markdown_functionalization_proposal_id"] = proposal.id
    self.admit_proposal(
        proposal,
        rationale="Markdown functionalization proposals are bounded executable extractions from already classified encounters.",
    )
    return proposal


def propose_markdown_expression_synthesis(
    self,
    node: SemanticNode,
    document: MarkdownDocumentIR,
    *,
    encounter: Mapping[str, Any],
) -> ProposalObject:
    """
    High Level Purpose:
        In circumstances like extracting one direct executable relation from a single markdown encounter, helps with asking the LLM for the smallest parameter-mapping synthesis proposal grounded only in that encounter.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `propose_markdown_expression_synthesis(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), encounter={'encounter_id': 'force-equation'})`
        Output: ProposalObject(proposal_type=ProposalType.MARKDOWN_EXPRESSION_SYNTHESIS, rationale='Markdown expression synthesis proposals extract executable parameter mappings from a single encounter.')

    Args:
        self: Bound controller instance that owns proposal requests and markdown fallback behavior.
        node: Value for `node` used by `propose_markdown_expression_synthesis`. Expected type: `SemanticNode`.
        document: Value for `document` used by `propose_markdown_expression_synthesis`. Expected type: `MarkdownDocumentIR`.
        encounter: Value for `encounter` used by `propose_markdown_expression_synthesis`. Expected type: `Mapping[str, Any]`.

    Returns:
        ProposalObject: Result produced by `propose_markdown_expression_synthesis`.
    """
    fallback = self.fallback_markdown_expression_synthesis()
    proposal = self.request_proposal(
        proposal_type=ProposalType.MARKDOWN_EXPRESSION_SYNTHESIS,
        node=node,
        target_scope=document.title,
        instructions=dedent(
            f"""
            Extract the executable parameter mapping from one markdown encounter.
            Work only from this encounter. Do not invent laws, symbols, or examples outside it.

            Rules:
            - if the encounter defines a computational mapping, set parameterized=true
            - input_fields must be the concrete input names a later caller should provide
            - output_field must be the main computed quantity
            - compute_expression must be a Python expression using only the named input_fields
            - preserve the encounter's own symbols and quantity names; do not substitute unrelated domains
            - question should be a concise later-user question this mapping answers
            - aliases should include the compact symbolic form when appropriate
            - if the encounter is not executable, set parameterized=false and leave the other fields empty

            Document title:
            {document.title}

            Encounter:
            {json.dumps(compact_markdown_encounter_records([encounter], max_encounters=1), indent=2, sort_keys=True)}
            """
        ).strip(),
        fallback_payload=fallback,
        mode=SupplementMode.DEEP,
    )
    node.metadata.setdefault("markdown_expression_synthesis_proposal_ids", []).append(proposal.id)
    self.admit_proposal(
        proposal,
        rationale="Markdown expression synthesis proposals extract executable parameter mappings from a single encounter.",
    )
    return proposal


def propose_markdown_title_repair(
    self,
    node: SemanticNode,
    document: MarkdownDocumentIR,
    *,
    encounter: Mapping[str, Any] | None,
    proposed_title: str,
    proposed_question: str,
    source_sections: Sequence[str],
    existing_titles: Sequence[str],
) -> ProposalObject:
    """
    High Level Purpose:
        In circumstances like repairing a heading-shaped markdown artifact identity before it is stored, helps with asking the LLM for a bounded title-and-question repair proposal tied to one encounter and one current title.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `propose_markdown_title_repair(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), encounter={'encounter_id': 'force-equation'}, proposed_title='1. Named quantities', proposed_question='What is 1. Named quantities?', source_sections=['Force'], existing_titles=['Physics / Force'])`
        Output: ProposalObject(proposal_type=ProposalType.MARKDOWN_TITLE_REPAIR, rationale='Markdown title repair proposals are bounded identity repairs for weak heading-shaped markdown artifacts.')

    Args:
        self: Bound controller instance that owns proposal requests and markdown fallback behavior.
        node: Value for `node` used by `propose_markdown_title_repair`. Expected type: `SemanticNode`.
        document: Value for `document` used by `propose_markdown_title_repair`. Expected type: `MarkdownDocumentIR`.
        encounter: Value for `encounter` used by `propose_markdown_title_repair`. Expected type: `Mapping[str, Any] | None`.
        proposed_title: Value for `proposed_title` used by `propose_markdown_title_repair`. Expected type: `str`.
        proposed_question: Value for `proposed_question` used by `propose_markdown_title_repair`. Expected type: `str`.
        source_sections: Value for `source_sections` used by `propose_markdown_title_repair`. Expected type: `Sequence[str]`.
        existing_titles: Value for `existing_titles` used by `propose_markdown_title_repair`. Expected type: `Sequence[str]`.

    Returns:
        ProposalObject: Result produced by `propose_markdown_title_repair`.
    """
    fallback = self.fallback_markdown_title_question_repair(
        document=document,
        encounter=encounter,
        proposed_title=proposed_title,
        proposed_question=proposed_question,
    )
    encounter_view = compact_markdown_encounter_records(
        [encounter] if isinstance(encounter, Mapping) else [],
        max_encounters=1,
    )
    semantic_hints = self.markdown_title_repair_semantic_hints(
        encounter=encounter,
        proposed_title=proposed_title,
    )
    proposal = self.request_proposal(
        proposal_type=ProposalType.MARKDOWN_TITLE_REPAIR,
        node=node,
        target_scope=document.title,
        instructions=dedent(
            f"""
            Repair one markdown-derived artifact title and question.
            Work only from the bounded encounter record and the current proposed title/question.

            Title-depth law (infer from the formal title and context; it is never explicitly specified):
            {title_depth_theory_prompt_block()}

            Goal:
            - repair weak section-heading or outline-shaped titles
            - if the current identity is only organizational or meta, reconstruct the actual reusable semantic identity from the encounter content
            - choose one broader grounding category above the title_current_identity if a real grounding category is available
            - decompose downward from the current identity only if narrower title determination is semantically necessary
            - keep the question caller-facing rather than identical to the title

            Return JSON with:
            - title_broader_category
            - title_current_identity
            - title_downward_decomposition
            - title_construction_rationale
            - title_collision_rationale
            - title_similies
            - question
            - question_title_separation

            Rules:
            - title_current_identity is the minimally sufficient current identity and must not be a raw outline label
            - if the heading is only a meta label such as summary, named quantities, notes, distinctions, or example, do not return that label as title_current_identity
            - rebuild the identity from formulas, declared quantities, stable distinctions, or reusable procedural content found in the encounter
            - choose at most one title_broader_category
            - title_downward_decomposition should be empty unless narrower title determination is genuinely needed
            - the final title will be assembled externally as title_broader_category / title_current_identity / title_downward_decomposition...
            - avoid raw section numbering or bare heading-copy identities unless they are semantically constitutive
            - avoid collision with existing titles and nearby artifact identities
            - keep the repaired question distinct from the repaired title

            Document title:
            {document.title}

            Current proposed title:
            {proposed_title}

            Current proposed question:
            {proposed_question}

            Source sections:
            {json.dumps(list(source_sections), indent=2, sort_keys=True)}

            Existing selected titles:
            {json.dumps(list(existing_titles)[:8], indent=2, sort_keys=True)}

            Derived semantic hints:
            {json.dumps(semantic_hints, indent=2, sort_keys=True)}

            Encounter:
            {json.dumps(encounter_view, indent=2, sort_keys=True)}
            """
        ).strip(),
        fallback_payload=fallback,
        mode=SupplementMode.FAST,
    )
    node.metadata.setdefault("markdown_title_repair_proposal_ids", []).append(proposal.id)
    self.admit_proposal(
        proposal,
        rationale="Markdown title repair proposals are bounded identity repairs for weak heading-shaped markdown artifacts.",
    )
    return proposal


def select_markdown_learning_encounter(
    self,
    *,
    document: MarkdownDocumentIR,
    encounter_id: str,
    title: str,
    semantic_unit: str,
    question: str,
    sections: Sequence[str],
    aliases: Sequence[str],
) -> Mapping[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like grounding one learned markdown artifact back to the best matching encounter record, helps with selecting the strongest encounter anchor from headings, sections, paragraphs, bullets, and lookup-key overlap.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `select_markdown_learning_encounter(self=controller, document=MarkdownDocumentIR(title='Physics Force Lesson'), encounter_id='force-equation', title='Physics / Force / Force From Mass And Acceleration', semantic_unit='Physics / Force / Force From Mass And Acceleration', question='How do you calculate force?', sections=['Force'], aliases=['F = m * a'])`
        Output: {'encounter_id': 'force-equation', 'heading': 'Force from mass and acceleration'}

    Args:
        self: Bound controller instance that owns markdown lookup helpers.
        document: Value for `document` used by `select_markdown_learning_encounter`. Expected type: `MarkdownDocumentIR`.
        encounter_id: Value for `encounter_id` used by `select_markdown_learning_encounter`. Expected type: `str`.
        title: Value for `title` used by `select_markdown_learning_encounter`. Expected type: `str`.
        semantic_unit: Value for `semantic_unit` used by `select_markdown_learning_encounter`. Expected type: `str`.
        question: Value for `question` used by `select_markdown_learning_encounter`. Expected type: `str`.
        sections: Value for `sections` used by `select_markdown_learning_encounter`. Expected type: `Sequence[str]`.
        aliases: Value for `aliases` used by `select_markdown_learning_encounter`. Expected type: `Sequence[str]`.

    Returns:
        Mapping[str, Any] | None: Result produced by `select_markdown_learning_encounter`.
    """
    encounters = markdown_learning_encounter_view(document)
    if encounter_id:
        exact = next(
            (
                encounter
                for encounter in encounters
                if str(encounter.get("encounter_id", "")).strip() == encounter_id
            ),
            None,
        )
        if exact is not None:
            return exact

    reference_parts = ordered_unique(
        collapse_ws(str(item).strip())
        for item in (title, semantic_unit, question, *sections, *aliases)
        if collapse_ws(str(item).strip())
    )
    if not reference_parts:
        return None
    reference_keys = {
        key
        for part in reference_parts
        for key in learning_lookup_keys(part)
    }
    best_encounter: Mapping[str, Any] | None = None
    best_score = (0, 0, 0, 0)
    for encounter in encounters:
        encounter_parts = ordered_unique(
            collapse_ws(str(item).strip())
            for item in (
                str(encounter.get("heading", "")).strip(),
                *(encounter.get("path", []) if isinstance(encounter.get("path", []), list) else []),
                *(encounter.get("sections", []) if isinstance(encounter.get("sections", []), list) else []),
                *(encounter.get("paragraphs", []) if isinstance(encounter.get("paragraphs", []), list) else []),
                *(encounter.get("bullets", []) if isinstance(encounter.get("bullets", []), list) else []),
            )
            if collapse_ws(str(item).strip())
        )
        if not encounter_parts:
            continue
        encounter_keys = {
            key
            for part in encounter_parts
            for key in learning_lookup_keys(part)
        }
        shared_key_count = len(reference_keys.intersection(encounter_keys))
        overlap_count = sum(
            1
            for part in reference_parts
            if any(learning_overlap(part, encounter_part) for encounter_part in encounter_parts)
        )
        question_bullet_count = sum(
            1
            for bullet in encounter.get("bullets", [])
            if "?" in collapse_ws(str(bullet).strip())
        ) if isinstance(encounter.get("bullets", []), list) else 0
        score = (
            shared_key_count,
            overlap_count,
            question_bullet_count,
            len(encounter_parts),
        )
        if score > best_score:
            best_score = score
            best_encounter = encounter
    if best_score[0] == 0 and best_score[1] == 0:
        return None
    return best_encounter


def build_markdown_knowledge_answer_from_encounter(
    self,
    encounter: Mapping[str, Any],
    *,
    fallback_answer: str,
) -> str:
    """
    High Level Purpose:
        In circumstances like turning one selected markdown encounter into a cleaner stored knowledge answer, helps with assembling paragraph and bullet evidence while stripping prompt-format residue from the encounter text.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `build_markdown_knowledge_answer_from_encounter(self=controller, encounter={'paragraphs': ['Force equals mass times acceleration.'], 'bullets': ['What is force?', 'Force depends on mass and acceleration.']}, fallback_answer='force')`
        Output: 'Force equals mass times acceleration. Force depends on mass and acceleration.'

    Args:
        self: Bound controller instance that owns answer sanitization.
        encounter: Value for `encounter` used by `build_markdown_knowledge_answer_from_encounter`. Expected type: `Mapping[str, Any]`.
        fallback_answer: Value for `fallback_answer` used by `build_markdown_knowledge_answer_from_encounter`. Expected type: `str`.

    Returns:
        str: Result produced by `build_markdown_knowledge_answer_from_encounter`.
    """
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
    question_like_bullets = [item for item in bullets if "?" in item]
    answer_bullets = [item for item in bullets if item not in question_like_bullets]

    parts: list[str] = []
    for paragraph in paragraphs:
        lowered = paragraph.lower()
        if lowered in {
            "canonical prompt forms:",
            "reusable answer pattern:",
            "source basis for these patterns:",
        }:
            continue
        parts.append(paragraph)
    parts.extend(answer_bullets[:6])

    answer = self.sanitize_markdown_learned_answer(" ".join(ordered_unique(parts)))
    if answer:
        return answer
    return self.sanitize_markdown_learned_answer(fallback_answer)


def markdown_ability_collision_identity(
    *,
    content: Mapping[str, Any],
    encounter_heading: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like markdown-learned executable abilities collapsing onto the same broader document title, helps with supplying a stable narrower identity so executable artifacts do not overwrite each other in storage.

    Reference to Theory:
        Supports governed artifact admission by keeping executable ability titles distinct while still anchored beneath the document-level semantic family.

    Example Input Output:
        Input: `markdown_ability_collision_identity(content={'executor_framework': 'python3'}, encounter_heading='Executable Python relation')`
        Output: 'Python Function'

    Args:
        content: Value for `content` used by `markdown_ability_collision_identity`. Expected type: `Mapping[str, Any]`.
        encounter_heading: Value for `encounter_heading` used by `markdown_ability_collision_identity`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `markdown_ability_collision_identity`.
    """
    framework = ability_executor_framework(
        representation=str(content.get("representation", "")).strip(),
        content=content,
    )
    normalized_heading = collapse_ws(str(encounter_heading or "").strip()).lower()
    if framework == "bash":
        return "Bash Command"
    if framework == "ansible":
        return "Ansible Playbook"
    if framework == "python3":
        if "signature" in normalized_heading or "function" in normalized_heading or "python" in normalized_heading:
            return "Python Function"
        return "Python Ability"
    return "Executable Ability"


def usable_markdown_symbolic_fields(output_field: str, input_fields: Sequence[str]) -> bool:
    """
    High Level Purpose:
        In circumstances like deriving executable identities and questions from markdown encounters, helps with rejecting malformed symbolic field guesses before they can pollute learned titles or questions.

    Reference to Theory:
        Supports governed markdown learning by keeping learned executable identities grounded in compact semantic fields rather than noisy sentence fragments.

    Example Input Output:
        Input: `usable_markdown_symbolic_fields(output_field='force', input_fields=['mass', 'acceleration'])`
        Output: True

    Args:
        output_field: Value for `output_field` used by `usable_markdown_symbolic_fields`. Expected type: `str`.
        input_fields: Value for `input_fields` used by `usable_markdown_symbolic_fields`. Expected type: `Sequence[str]`.

    Returns:
        bool: Result produced by `usable_markdown_symbolic_fields`.
    """
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


def build_markdown_learning_artifact(
    self,
    *,
    node: SemanticNode,
    document: MarkdownDocumentIR,
    source_path: Path,
    payload: Mapping[str, Any],
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like turning one markdown-learning payload into a persisted reusable artifact, helps with repairing title depth, grounding the payload to a source encounter, deriving structured-learning metadata, and producing the final governed artifact payload.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `build_markdown_learning_artifact(self=controller, node=SemanticNode(id='not-force', semantic_unit='Physics / Force'), document=MarkdownDocumentIR(title='Physics Force Lesson'), source_path=Path('/tmp/physics_force.md'), payload={'artifact_type': 'ability', 'title': 'Force From Mass And Acceleration', 'semantic_unit': 'Force From Mass And Acceleration', 'question': 'How do you calculate force?', 'content': {'compute_expression': 'm * a', 'output_field': 'F', 'input_contract': {'m': 'number', 'a': 'number'}, 'output_contract': {'F': 'number'}}})`
        Output: Artifact(id='artifact-force', title='Physics Force Lesson / Force From Mass And Acceleration', artifact_type='ability', representation='python_script')

    Args:
        self: Bound controller instance that owns markdown repair, title, and artifact-building helpers.
        node: Value for `node` used by `build_markdown_learning_artifact`. Expected type: `SemanticNode`.
        document: Value for `document` used by `build_markdown_learning_artifact`. Expected type: `MarkdownDocumentIR`.
        source_path: Value for `source_path` used by `build_markdown_learning_artifact`. Expected type: `Path`.
        payload: Value for `payload` used by `build_markdown_learning_artifact`. Expected type: `Mapping[str, Any]`.

    Returns:
        Artifact | None: Result produced by `build_markdown_learning_artifact`.
    """
    artifact_type = normalize_artifact_type(payload.get("artifact_type", "knowledge"))
    raw_title = collapse_ws(str(payload.get("title", "")).strip())
    raw_formal_title_identity = str(payload.get("title_identity", "")).strip() or raw_title
    if looks_like_prolog_title_identity(raw_formal_title_identity):
        formal_title_identity = normalize_semantic_title_identity(raw_formal_title_identity)
    else:
        formal_title_identity = normalize_markdown_title_identity(raw_formal_title_identity)
    title = normalize_markdown_title_identity(raw_title) or raw_title
    title_broader_category = normalize_markdown_title_identity(
        collapse_ws(str(payload.get("title_broader_category", "")).strip())
    )
    title_broader_category = self.repair_markdown_broader_category_against_document(
        title_broader_category,
        document_title=document.title,
    )
    title_current_identity = normalize_markdown_title_identity(
        collapse_ws(str(payload.get("title_current_identity", "")).strip())
    )
    title_downward_decomposition = ordered_unique(
        normalize_markdown_title_identity(str(item).strip())
        for item in payload.get("title_downward_decomposition", [])
        if normalize_markdown_title_identity(str(item).strip())
    ) if isinstance(payload.get("title_downward_decomposition", []), list) else []
    composed_title = compose_display_title_identity(
        broader_category=title_broader_category,
        current_identity=title_current_identity,
        downward_decomposition=title_downward_decomposition,
        fallback_title=title,
    )
    if composed_title:
        title = composed_title
    if formal_title_identity and looks_like_prolog_title_identity(formal_title_identity):
        title = title or semantic_title_display_text(formal_title_identity)
    if (
        document.title
        and "/" not in title
        and semantic_namespace_key(title) != semantic_namespace_key(document.title)
        and not title_broader_category
    ):
        title_broader_category = document.title
        if not title_current_identity:
            title_current_identity = normalize_markdown_title_identity(title) or title
        title = compose_display_title_identity(
            broader_category=title_broader_category,
            current_identity=title_current_identity,
            downward_decomposition=title_downward_decomposition,
            fallback_title=title,
        ) or title
    semantic_unit = collapse_ws(str(payload.get("semantic_unit", "")).strip()) or title
    question = collapse_ws(str(payload.get("question", "")).strip()) or markdown_caller_facing_question(document.title, semantic_unit or title)
    answer = collapse_ws(str(payload.get("answer", "")).strip())
    if not title or not semantic_unit:
        return None
    title_similies = ordered_unique(
        collapse_ws(str(item).strip())
        for item in payload.get("title_similies", [])
        if collapse_ws(str(item).strip())
    ) if isinstance(payload.get("title_similies", []), list) else []
    related_titles = ordered_unique(
        collapse_ws(str(item).strip())
        for item in payload.get("related_titles", [])
        if collapse_ws(str(item).strip())
    ) if isinstance(payload.get("related_titles", []), list) else []
    relation_rationale = collapse_ws(str(payload.get("relation_rationale", "")).strip())
    title_construction_rationale = collapse_ws(str(payload.get("title_construction_rationale", "")).strip())
    title_collision_rationale = collapse_ws(str(payload.get("title_collision_rationale", "")).strip())
    question_title_separation = collapse_ws(str(payload.get("question_title_separation", "")).strip())
    aliases = ordered_unique(str(item).strip() for item in payload.get("aliases", []) if str(item).strip()) if isinstance(payload.get("aliases", []), list) else []
    component_nots = ordered_unique(str(item).strip() for item in payload.get("component_nots", []) if str(item).strip()) if isinstance(payload.get("component_nots", []), list) else []
    composed_not = collapse_ws(str(payload.get("composed_not", "")).strip())
    sections = ordered_unique(str(item).strip() for item in payload.get("sections", []) if str(item).strip()) if isinstance(payload.get("sections", []), list) else []
    raw_content = dict(payload.get("content", {})) if isinstance(payload.get("content", {}), Mapping) else {}
    encounter_id = str(payload.get("encounter_id", "")).strip()
    raw_encounter = self.select_markdown_learning_encounter(
        document=document,
        encounter_id=encounter_id,
        title=title,
        semantic_unit=semantic_unit,
        question=question,
        sections=sections,
        aliases=aliases,
    )
    encounter_heading = collapse_ws(str(raw_encounter.get("heading", "")).strip()) if isinstance(raw_encounter, Mapping) else ""
    if artifact_type == ArtifactType.ABILITY and title_broader_category:
        current_identity_key = semantic_namespace_key(title_current_identity or title)
        broader_identity_key = semantic_namespace_key(title_broader_category)
        if current_identity_key == broader_identity_key or self.looks_like_generic_markdown_current_identity(
            title_current_identity or title,
            encounter_heading=encounter_heading,
        ):
            title_current_identity = markdown_ability_collision_identity(
                content=raw_content,
                encounter_heading=encounter_heading,
            )
            title = compose_display_title_identity(
                broader_category=title_broader_category,
                current_identity=title_current_identity,
                downward_decomposition=title_downward_decomposition,
                fallback_title=title,
            ) or title
    encounter_relation_hints = [
        hint
        for hint in self.markdown_encounter_relation_hints(raw_encounter)
        if not self.looks_like_generic_markdown_current_identity(
            hint,
            encounter_heading=encounter_heading,
        )
    ]
    document_relation_hints = [
        hint
        for hint in self.markdown_document_relation_hints(
            document,
            exclude_encounter_id=encounter_id,
        )
        if not self.looks_like_generic_markdown_current_identity(hint)
    ]
    relation_hint_texts = self.markdown_relation_hint_texts(
        document,
        encounter=raw_encounter,
        exclude_encounter_id=encounter_id,
    )
    encounter_is_reusable_substrate = self.markdown_heading_is_reusable_substrate(encounter_heading)
    generic_executor_wrapper_identity = False
    if artifact_type == ArtifactType.ABILITY:
        identity_key = semantic_namespace_key(title_current_identity or title)
        generic_executor_wrapper_identity = identity_key in {
            semantic_namespace_key("Python Ability"),
            semantic_namespace_key("Bash Ability"),
            semantic_namespace_key("Ansible Ability"),
            semantic_namespace_key("Wasm Ability"),
        }
    if encounter_relation_hints:
        if not generic_executor_wrapper_identity:
            title_similies = ordered_unique(title_similies + encounter_relation_hints)
            aliases = ordered_unique(aliases + encounter_relation_hints)
    if not encounter_is_reusable_substrate:
        related_titles = ordered_unique(related_titles + encounter_relation_hints + document_relation_hints)
    if artifact_type == ArtifactType.KNOWLEDGE and raw_encounter is not None:
        encounter_bullets = [
            collapse_ws(str(item).strip())
            for item in raw_encounter.get("bullets", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(raw_encounter.get("bullets", []), list) else []
        encounter_heading = collapse_ws(str(raw_encounter.get("heading", "")).strip())
        encounter_path = [
            collapse_ws(str(item).strip())
            for item in raw_encounter.get("path", [])
            if collapse_ws(str(item).strip())
        ] if isinstance(raw_encounter.get("path", []), list) else []
        question_like_bullets = [item for item in encounter_bullets if "?" in item]
        if self.looks_like_generic_markdown_question(
            question,
            semantic_unit=semantic_unit,
            title=title,
            document_title=document.title,
        ) and question_like_bullets:
            question = question_like_bullets[0]
        elif self.looks_like_generic_markdown_question(
            question,
            semantic_unit=semantic_unit,
            title=title,
            document_title=document.title,
        ) and encounter_heading:
            question = markdown_caller_facing_question(document.title, encounter_heading)
        aliases = ordered_unique(aliases + question_like_bullets[:4] + encounter_bullets[:6])
        heading_aliases = ordered_unique(
            [
                encounter_heading,
                *encounter_path,
                f"{document.title} {encounter_heading}".strip() if encounter_heading else "",
                f"{document.title} {encounter_heading.split(':', 1)[0].strip()}".strip()
                if encounter_heading and ":" in encounter_heading
                else "",
            ]
        )
        aliases = ordered_unique(aliases + [alias for alias in heading_aliases if alias])
        encounter_answer = self.build_markdown_knowledge_answer_from_encounter(
            raw_encounter,
            fallback_answer=answer,
        )
        if encounter_answer and (
            not answer
            or self.markdown_answer_has_prompt_noise(answer)
            or self.looks_like_generic_markdown_question(
                question,
                semantic_unit=semantic_unit,
                title=title,
                document_title=document.title,
            )
        ):
            answer = encounter_answer
    elif artifact_type == ArtifactType.KNOWLEDGE:
        answer = self.sanitize_markdown_learned_answer(answer)
    if raw_encounter is not None:
        weak_title = self.looks_like_heading_markdown_title(
            title,
            encounter_heading=encounter_heading,
            document_title=document.title,
        )
        weak_current_identity = self.looks_like_generic_markdown_current_identity(
            title_current_identity or title,
            encounter_heading=encounter_heading,
        )
        weak_question = self.looks_like_generic_markdown_question(
            question,
            semantic_unit=semantic_unit,
            title=title,
            document_title=document.title,
        )
        needs_title_repair = weak_title or weak_current_identity
        needs_question_repair = weak_question
        if needs_title_repair or needs_question_repair:
            repair = self.propose_markdown_title_repair(
                node,
                document,
                encounter=raw_encounter,
                proposed_title=title,
                proposed_question=question,
                source_sections=sections,
                existing_titles=[artifact.title for artifact in self.reusable_artifact_candidates()],
            )
            repair_payload = repair.payload if isinstance(repair.payload, Mapping) else {}
            if needs_title_repair:
                title_broader_category = collapse_ws(
                    str(repair_payload.get("title_broader_category", title_broader_category)).strip()
                )
                title_broader_category = normalize_markdown_title_identity(title_broader_category)
                title_broader_category = self.repair_markdown_broader_category_against_document(
                    title_broader_category,
                    document_title=document.title,
                )
                title_current_identity = collapse_ws(
                    str(repair_payload.get("title_current_identity", title_current_identity)).strip()
                )
                title_current_identity = normalize_markdown_title_identity(title_current_identity)
                title_downward_decomposition = ordered_unique(
                    normalize_markdown_title_identity(str(item).strip())
                    for item in repair_payload.get("title_downward_decomposition", title_downward_decomposition)
                    if normalize_markdown_title_identity(str(item).strip())
                ) if isinstance(
                    repair_payload.get("title_downward_decomposition", title_downward_decomposition),
                    list,
                ) else list(title_downward_decomposition)
                title_similies = ordered_unique(
                    title_similies
                    + [
                        collapse_ws(str(item).strip())
                        for item in repair_payload.get("title_similies", [])
                        if collapse_ws(str(item).strip())
                    ]
                ) if isinstance(repair_payload.get("title_similies", []), list) else title_similies
                title_construction_rationale = collapse_ws(
                    str(repair_payload.get("title_construction_rationale", title_construction_rationale)).strip()
                )
                title_collision_rationale = collapse_ws(
                    str(repair_payload.get("title_collision_rationale", title_collision_rationale)).strip()
                )
            repaired_question = collapse_ws(str(repair_payload.get("question", question)).strip())
            if needs_question_repair and repaired_question:
                question = repaired_question
            if needs_title_repair or not question_title_separation:
                question_title_separation = collapse_ws(
                    str(repair_payload.get("question_title_separation", question_title_separation)).strip()
                )
            if needs_title_repair:
                title = normalize_markdown_title_identity(title) or title
                title = compose_display_title_identity(
                    broader_category=title_broader_category,
                    current_identity=title_current_identity,
                    downward_decomposition=title_downward_decomposition,
                    fallback_title=title,
                ) or title
                if self.looks_like_generic_markdown_current_identity(
                    title_current_identity or title,
                    encounter_heading=encounter_heading,
                ):
                    title_current_identity = self.derive_markdown_current_identity_from_encounter(
                        encounter=raw_encounter,
                        proposed_title=title_current_identity or title,
                    )
                    title_downward_decomposition = []
                    title = compose_display_title_identity(
                        broader_category=title_broader_category,
                        current_identity=title_current_identity,
                        downward_decomposition=title_downward_decomposition,
                        fallback_title=title,
                    ) or title
    if (
        document.title
        and "/" not in title
        and semantic_namespace_key(title) != semantic_namespace_key(document.title)
        and not title_broader_category
    ):
        title_broader_category = document.title
        if not title_current_identity:
            title_current_identity = normalize_markdown_title_identity(title) or title
        title = compose_display_title_identity(
            broader_category=title_broader_category,
            current_identity=title_current_identity,
            downward_decomposition=title_downward_decomposition,
            fallback_title=title,
        ) or title
    if artifact_type == ArtifactType.ABILITY and raw_encounter is not None:
        direct_output_field, direct_input_fields, direct_expression = markdown_direct_expression_mapping(raw_encounter)
        raw_input_contract = raw_content.get("input_contract", {})
        raw_output_contract = raw_content.get("output_contract", {})
        current_input_fields = list(raw_input_contract.keys()) if isinstance(raw_input_contract, Mapping) else []
        current_output_field = str(raw_content.get("output_field", "")).strip()
        current_expression = str(raw_content.get("compute_expression", "")).strip()
        if not current_output_field and isinstance(raw_output_contract, Mapping):
            current_output_field = str(next(iter(raw_output_contract.keys()), "")).strip()
        if usable_markdown_symbolic_fields(direct_output_field, direct_input_fields) and direct_expression:
            normalized_current_expression, normalized_current_output = self.normalize_expression_ability_fields(
                compute_expression=current_expression,
                output_field=current_output_field,
            )
            normalized_direct_expression, normalized_direct_output = self.normalize_expression_ability_fields(
                compute_expression=direct_expression,
                output_field=direct_output_field,
            )
            if (
                current_output_field.lower() != direct_output_field.lower()
                or set(map(str.lower, current_input_fields)) != set(map(str.lower, direct_input_fields))
                or normalized_current_output != normalized_direct_output
                or normalized_current_expression != normalized_direct_expression
            ):
                raw_content["compute_expression"] = normalized_direct_expression or direct_expression
                raw_content["output_field"] = normalized_direct_output or direct_output_field
                raw_content["input_contract"] = {field: "number" for field in direct_input_fields}
                raw_content["output_contract"] = {direct_output_field: "number"}
                raw_content["python_script"] = ""
            better_question = markdown_encounter_question(
                raw_encounter,
                output_field=direct_output_field,
                input_fields=direct_input_fields,
            )
            if better_question:
                question = better_question
            aliases = ordered_unique(aliases + markdown_encounter_aliases(raw_encounter))
            component_nots = ordered_unique(
                titleize_semantic_unit(field)
                for field in [*direct_input_fields, direct_output_field]
                if titleize_semantic_unit(field)
            )
            raw_content["parameter_aliases"] = markdown_document_symbol_aliases(
                document,
                [*direct_input_fields, direct_output_field],
            )
    if title_representation_is_prolog():
        input_contract = raw_content.get("input_contract", {})
        output_contract = raw_content.get("output_contract", {})
        synthesized_formal_title = synthesize_prolog_formal_title_identity(
            display_title=title,
            input_keys=list(input_contract.keys()) if isinstance(input_contract, Mapping) else [],
            output_keys=list(output_contract.keys()) if isinstance(output_contract, Mapping) else [],
            compute_expression=str(raw_content.get("compute_expression", "")).strip(),
            output_field=str(raw_content.get("output_field", "")).strip(),
            parameter_aliases=raw_content.get("parameter_aliases", {}) if isinstance(raw_content.get("parameter_aliases", {}), Mapping) else {},
        )
        if synthesized_formal_title:
            formal_title_identity = normalize_semantic_title_identity(synthesized_formal_title)
    aliases = ordered_unique(
        aliases
        + title_similies
        + ([title_broader_category] if title_broader_category else [])
        + ([title_current_identity] if title_current_identity else [])
        + list(title_downward_decomposition)
    )
    semantic_basis_parts = [
        document.title,
        title,
        formal_title_identity,
        title_broader_category,
        title_current_identity,
        *title_downward_decomposition,
        *related_titles,
        question,
        semantic_unit,
        *aliases,
        *sections,
    ]
    if raw_encounter is not None:
        if isinstance(raw_encounter.get("bullets", []), list):
            semantic_basis_parts.extend(
                collapse_ws(str(item).strip())
                for item in raw_encounter.get("bullets", [])
                if collapse_ws(str(item).strip())
            )
        if isinstance(raw_encounter.get("paragraphs", []), list):
            semantic_basis_parts.extend(
                collapse_ws(str(item).strip())
                for item in raw_encounter.get("paragraphs", [])[:3]
                if collapse_ws(str(item).strip())
            )
    if answer:
        semantic_basis_parts.append(answer[:400])
    structured = normalize_not_elaboration_payload(
        " ".join(item for item in ordered_unique(semantic_basis_parts) if item).strip() or question or semantic_unit or title,
        {
            "title_identity": formal_title_identity or title,
            "encountered_not": semantic_unit,
            "goal": question,
            "component_nots": component_nots,
            "composed_not": composed_not,
        },
        boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
        related_artifact_titles=aliases[:4],
        title_identity=formal_title_identity or title,
    )
    if artifact_type == ArtifactType.KNOWLEDGE:
        knowledge_posture = "next_step_guidance" if re.search(
            r"\bwhat should\b|\bwhat do i do\b|\bshould i\b|\bnext step\b",
            question,
            flags=re.IGNORECASE,
        ) else "direct_resolution"
        structured["action_posture"] = knowledge_posture
        structured["notation_yaml"] = render_structured_learning_yaml(
            semantic_unit=question or semantic_unit or title,
            encountered_not=structured.get("encountered_not", semantic_unit),
            component_nots=list(structured.get("component_nots", [])),
            composed_not=str(structured.get("composed_not", "")).strip(),
            related_artifact_titles=aliases[:4],
            intended_object=str(structured.get("intended_object", "")),
            success_criteria=list(structured.get("success_criteria", [])),
            actual_realization=str(structured.get("actual_realization", "")),
            givens=list(structured.get("givens", [])),
            unknowns=list(structured.get("unknowns", [])),
            missing_components=list(structured.get("missing_components", [])),
            distorted_components=list(structured.get("distorted_components", [])),
            differentiators=list(structured.get("differentiators", [])),
            contrastive_cases=list(structured.get("contrastive_cases", [])),
            risk_of_wrong_closure=list(structured.get("risk_of_wrong_closure", [])),
            disallowed_assumptions=list(structured.get("disallowed_assumptions", [])),
            misalignment_types=list(structured.get("misalignment_types", [])),
            origin_layers=list(structured.get("origin_layers", [])),
            degree=str(structured.get("degree", "")),
            remainder_shapes=list(structured.get("remainder_shapes", [])),
            why_it_matters=list(structured.get("why_it_matters", [])),
            minimal_repair=list(structured.get("minimal_repair", [])),
            full_repair=list(structured.get("full_repair", [])),
            action_posture=knowledge_posture,
        )
    structured["lookup_keys"] = ordered_unique(
        list(structured.get("lookup_keys", []))
        + learning_lookup_keys(question)
        + learning_lookup_keys(semantic_unit)
        + [key for related in related_titles for key in learning_lookup_keys(related)]
        + [key for alias in aliases for key in learning_lookup_keys(alias)]
    )[:24]
    content = {
        "question": question,
        "aliases": aliases,
        "formal_title_identity": formal_title_identity or title,
        "title_broader_category": title_broader_category,
        "title_current_identity": title_current_identity,
        "title_downward_decomposition": title_downward_decomposition,
        "title_similies": title_similies,
        "related_titles": related_titles,
        "relation_rationale": relation_rationale,
        "relation_family_hints": ordered_unique(encounter_relation_hints + document_relation_hints),
        "relation_hint_texts": relation_hint_texts,
        "title_construction_rationale": title_construction_rationale,
        "title_collision_rationale": title_collision_rationale,
        "question_title_separation": question_title_separation,
        "source_kind": "markdown",
        "source_path": str(source_path),
        "source_document": source_path.name,
        "source_title": document.title,
        "source_sections": sections,
        "encounter_id": encounter_id,
        "encounter_kind": str(payload.get("encounter_kind", "")).strip().lower(),
        "equation_bearing": bool(payload.get("equation_bearing", False)),
        "parameterized": bool(payload.get("parameterized", False)),
        "structured_learning": structured,
        **raw_content,
    }
    function_bit = 0
    if artifact_type == ArtifactType.KNOWLEDGE:
        if not answer:
            return None
        content["answer"] = answer
    elif artifact_type == ArtifactType.ABILITY:
        input_contract = content.get("input_contract", {})
        output_contract = content.get("output_contract", {})
        content["input_contract"] = dict(input_contract) if isinstance(input_contract, Mapping) else {}
        content["output_contract"] = dict(output_contract) if isinstance(output_contract, Mapping) else {}
        executor_framework = ability_executor_framework(
            representation=str(payload.get("representation", "")).strip(),
            content=content,
        ) or "python3"
        content["executor_framework"] = executor_framework
        if executor_framework == "python3":
            python_script = str(content.get("python_script", "")).strip()
            if looks_like_placeholder_python_script(python_script):
                compute_expression = str(content.get("compute_expression", "")).strip()
                output_field = str(content.get("output_field", "")).strip()
                if not output_field and isinstance(content.get("output_contract", {}), Mapping):
                    output_field = next(iter(content["output_contract"].keys()), "")
                if not compute_expression or not output_field or not content["input_contract"]:
                    return None
                if not content["output_contract"]:
                    content["output_contract"] = {output_field: "number"}
                python_script = self.expression_ability_script(
                    title=title,
                    scope=collapse_ws(str(payload.get("scope", "")).strip())
                    or f"reuse when the user asks about {semantic_unit} from {document.title} under ordinary stable reading",
                    input_contract=content["input_contract"],
                    output_contract=content["output_contract"],
                    expression=compute_expression,
                    output_field=output_field,
                )
                content["python_script"] = python_script
            content["entrypoint"] = str(content.get("entrypoint", "main")).strip() or "main"
            content["script_language"] = "python"
            content["dependencies"] = self.ability_script_dependencies(content)
        elif executor_framework == "bash":
            shell_script = str(content.get("shell_script", "")).strip()
            if not shell_script:
                return None
            content["entrypoint"] = str(content.get("entrypoint", "main")).strip() or "main"
            content["script_language"] = "bash"
            content["dependencies"] = ordered_unique(
                str(item).strip() for item in content.get("dependencies", []) if str(item).strip()
            ) if isinstance(content.get("dependencies", []), list) else []
        elif executor_framework == "ansible":
            ansible_playbook = str(content.get("ansible_playbook", "")).strip()
            if not ansible_playbook:
                return None
            content["entrypoint"] = str(content.get("entrypoint", "playbook")).strip() or "playbook"
            content["script_language"] = "ansible"
            content["dependencies"] = ordered_unique(
                str(item).strip() for item in content.get("dependencies", []) if str(item).strip()
            ) if isinstance(content.get("dependencies", []), list) else []
        else:
            return None
        payload_representation = str(payload.get("representation", "")).strip()
        if not payload_representation:
            payload["representation"] = executor_framework_representation(executor_framework)
        function_bit = 1
    else:
        if answer:
            content["answer"] = answer
    artifact_payload = {
        "artifact_type": artifact_type,
        "title": title,
        "representation": normalize_artifact_representation(
            payload.get(
                "representation",
                "yaml"
                if artifact_type != ArtifactType.ABILITY
                else executor_framework_representation(str(content.get("executor_framework", "")) or "python3"),
            ),
            artifact_type=artifact_type,
            default="yaml",
        ),
        "scope": collapse_ws(str(payload.get("scope", "")).strip())
        or f"reuse when the user asks about {semantic_unit} from {document.title} under ordinary stable reading",
        "reusability": normalize_artifact_reuse(payload.get("reusability", "broad_reuse")),
        "admissibility": normalize_artifact_admission(payload.get("admissibility", "admitted")),
        "learning_relation": normalize_learning_relation(payload.get("learning_relation", "new_family")),
        "related_artifact_ids": [
            str(item).strip()
            for item in payload.get("related_artifact_ids", [])
            if str(item).strip()
        ] if isinstance(payload.get("related_artifact_ids", []), list) else [],
        "justification": collapse_ws(str(payload.get("justification", "")).strip())
        or collapse_ws(str(payload.get("why_reusable", "")).strip())
        or "Compiled from the supplied markdown document through bounded structural extraction.",
        "constraints": [str(item).strip() for item in payload.get("constraints", []) if str(item).strip()] if isinstance(payload.get("constraints", []), list) else ["derived only from the supplied markdown source"],
        "content": content,
        "function_bit": function_bit,
    }
    return self.build_artifact_from_payload(node=node, payload=artifact_payload, provenance=[node.id, str(source_path)])
