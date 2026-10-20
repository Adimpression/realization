# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from typing import Any


LEARNING_MATCH_KINDS = (
    "encountered_before",
    "decomposition_related",
    "composition_related",
)

LEARNING_STOP_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "convert",
    "create",
    "define",
    "did",
    "do",
    "does",
    "explain",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "make",
    "name",
    "of",
    "on",
    "put",
    "sort",
    "that",
    "the",
    "to",
    "turn",
    "use",
    "using",
    "via",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "write",
    "you",
}

LEARNING_COMPONENT_BREAKS = {"and", "for", "then", "using", "via", "with"}

LEARNING_DISCRIMINATOR_TOKENS = {
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
}

SELECTION_SIGNAL_STOP_TOKENS = LEARNING_STOP_TOKENS | {
    "now",
    "next",
    "step",
    "should",
}

DECISION_UNCERTAINTY_MARKERS = (
    "unknown",
    "not sure",
    "unsure",
    "cannot tell",
    "can't tell",
    "cannot identify",
    "can't identify",
    "could be",
    "might be",
    "may be",
    "one of",
    "either",
    "unidentified",
    "unclear",
    "uncertain",
    "ambiguous",
    "which is which",
    "mixed",
    "not clearly",
    "not clearly identified",
    "not confidently",
    "not confidently identified",
    "not identified",
    "not confirmed",
)

DECISION_CONFIRMATION_MARKERS = (
    "confirmed",
    "clear",
    "clearly",
    "verified",
    "match",
    "matches",
    "matching",
    "sealed",
    "labeled",
    "labelled",
    "as prescribed",
)

DECISION_ABSENCE_MARKERS = (
    "no ",
    "none",
    "without ",
    "not holding",
    "not currently",
    "absent",
)

DECISION_HOLD_MARKERS = (
    "do not take",
    "don't take",
    "do not",
    "don't",
    "wait",
    "do not guess",
    "don't guess",
    "identify",
    "confirm",
    "verify",
    "check first",
)

DECISION_ACT_MARKERS = (
    "take",
    "proceed",
    "follow directions",
    "follow the directions",
    "do it now",
)

DECISION_CONDITIONAL_MARKERS = (
    "if confirmed",
    "if you have confirmed",
    "if verified",
    "if they match",
    "if it matches",
    "if the directions match",
    "if verified",
)

STABLE_WORLD_FACTS = {
    "france": {"capital": "Paris"},
    "germany": {"capital": "Berlin"},
    "italy": {"capital": "Rome"},
    "spain": {"capital": "Madrid"},
    "portugal": {"capital": "Lisbon"},
    "japan": {"capital": "Tokyo"},
    "india": {"capital": "New Delhi"},
    "singapore": {"capital": "Singapore"},
}


def normalize_entity_text(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like learning lookup, stable fact reuse, and canonical learning support, helps with normalizing entity text.

    Reference to Theory:
        Supports stable learning and canonical fact lookup rules used by the applied controller and artifact reuse logic.

    Example Input Output:
        Input: `normalize_entity_text(text='Compute force from mass and acceleration.')`
        Output: 'F = m * a'

    Args:
        text: Value for `text` used by `normalize_entity_text`. Expected type: `str`.

    Returns:
        str: Result produced by `normalize_entity_text`.
    """
    return re.sub(r"[^a-z ]+", " ", str(text or "").lower()).strip()


def canonical_stable_fact_lookup(text: str) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like learning lookup, stable fact reuse, and canonical learning support, helps with handling canonical stable fact lookup.

    Reference to Theory:
        Supports stable learning and canonical fact lookup rules used by the applied controller and artifact reuse logic.

    Example Input Output:
        Input: `canonical_stable_fact_lookup(text='Compute force from mass and acceleration.')`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        text: Value for `text` used by `canonical_stable_fact_lookup`. Expected type: `str`.

    Returns:
        dict[str, Any] | None: Result produced by `canonical_stable_fact_lookup`.
    """
    lowered = str(text or "").lower().strip()
    country = None
    match = re.search(r"capital of\s+([a-zA-Z ]+?)[?.! ]*$", lowered)
    if match:
        country = normalize_entity_text(match.group(1))
    if country is None:
        match = re.search(r"name\s+([a-zA-Z ]+?)'s\s+capital\s+city[?.! ]*$", lowered)
        if match:
            country = normalize_entity_text(match.group(1))
    if country is None:
        match = re.search(r"([a-zA-Z ]+?)'s\s+capital\s+city[?.! ]*$", lowered)
        if match:
            country = normalize_entity_text(match.group(1))
    if country and country in STABLE_WORLD_FACTS and "capital" in STABLE_WORLD_FACTS[country]:
        answer = STABLE_WORLD_FACTS[country]["capital"]
        return {
            "answer": answer,
            "justification": f"Canonical bounded fact lookup matched the stable fact capital({country}) = {answer}.",
            "answer_kind": "direct_fact",
        }
    return None
