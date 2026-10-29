# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re

from realized_core_engine.prompt_directives import (
    prompt_has_unresolved_uncertainty,
    semantic_prompt_directive_profile,
    semantic_question_focus_text,
)
from realized_core_semantics.semantic_text import collapse_ws, semantic_named_input_keys


def semantic_prompt_action_posture(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like routing a prompt toward direct explanation, bounded computation, clarification, or next-step guidance, helps with classifying the governing action posture without constructing a full fallback non-achievedness payload.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_prompt_action_posture(text='Calculate force from mass=3 and acceleration=4.')`
        Output: 'compute_or_template'

    Args:
        text: Value for `text` used by `semantic_prompt_action_posture`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_prompt_action_posture`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return "direct_resolution"
    directive = semantic_prompt_directive_profile(semantic_text)
    directive_kind = str(directive.get("kind", "")).strip()
    if directive_kind in {
        "state",
        "distinguish",
        "derive",
        "construct",
        "identify_reusable_substrate",
    }:
        return "direct_resolution"
    if re.search(
        r"^\s*(?:write|append|copy|move|delete|open|launch|reveal|download|extract|create|list|read|load|search|lookup|hash|checksum|capture)\b",
        semantic_text,
        flags=re.IGNORECASE,
    ):
        return "compute_or_template"
    if semantic_named_input_keys(semantic_text) or re.search(r"\bcalculate\b|\bcompute\b|\bfind\b", semantic_text, flags=re.IGNORECASE):
        return "compute_or_template"
    if re.search(r"\bwhat should\b|\bwhat do i do\b|\bshould i\b|\bwhat next\b|\bwhat now\b", semantic_text, flags=re.IGNORECASE):
        return "next_step_guidance"
    if prompt_has_unresolved_uncertainty(semantic_text):
        return "clarify_before_acting"
    return "direct_resolution"


def semantic_prompt_prefers_direct_knowledge_answer(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like offline reuse of prior knowledge artifacts, helps with detecting when a prompt is asking for a direct explanatory answer rather than a compute execution.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_prompt_prefers_direct_knowledge_answer(text='What is mass conservation in a reaction?')`
        Output: True

    Args:
        text: Value for `text` used by `semantic_prompt_prefers_direct_knowledge_answer`. Expected type: `str`.

    Returns:
        bool: Result produced by `semantic_prompt_prefers_direct_knowledge_answer`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return False
    directive = semantic_prompt_directive_profile(semantic_text)
    directive_kind = str(directive.get("kind", "")).strip()
    if directive_kind in {
        "state",
        "distinguish",
        "derive",
        "construct",
        "identify_reusable_substrate",
    }:
        return True
    if semantic_named_input_keys(semantic_text):
        return False
    posture = semantic_prompt_action_posture(semantic_text)
    if posture == "compute_or_template":
        return False
    if posture == "next_step_guidance":
        return True
    if bool(semantic_question_focus_text(semantic_text)):
        return True
    return False


def semantic_unit_allows_default_invocation_payload(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like routing a prompt toward reusable executable artifacts, helps with deciding whether default invocation payloads should be considered admissible for the semantic unit.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `semantic_unit_allows_default_invocation_payload(text='Compute force from mass and acceleration.')`
        Output: True

    Args:
        text: Value for `text` used by `semantic_unit_allows_default_invocation_payload`. Expected type: `str`.

    Returns:
        bool: Result produced by `semantic_unit_allows_default_invocation_payload`.
    """
    semantic_text = str(text or "")
    lowered = semantic_text.lower().strip()
    if semantic_named_input_keys(semantic_text):
        return True
    if re.search(r"-?\d+(?:\.\d+)?", semantic_text) and re.search(r"\b(calculate|compute|find|solve|derive|use)\b", lowered):
        return True
    if re.search(r"\b(calculate|compute|find|solve|derive)\b", lowered):
        return True
    if re.search(r"\bwhat\b.*\bget\b", lowered):
        return True
    if lowered.startswith(("what is ", "what are ", "explain ", "define ", "describe ", "summarize ")):
        return False
    return semantic_prompt_action_posture(semantic_text) == "compute_or_template"
