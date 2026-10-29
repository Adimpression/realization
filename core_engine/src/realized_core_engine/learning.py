"""Controller-owned learning vocabulary and deterministic fact lookup."""

from __future__ import annotations

import re
from typing import Any

from realized_core_semantics.semantic_text import (
    LEARNING_COMPONENT_BREAKS,
    LEARNING_STOP_TOKENS,
)


LEARNING_MATCH_KINDS = (
    "encountered_before",
    "decomposition_related",
    "composition_related",
)

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
    """Normalize a bounded-fact entity for deterministic lookup."""

    return re.sub(r"[^a-z ]+", " ", str(text or "").lower()).strip()


def canonical_stable_fact_lookup(text: str) -> dict[str, Any] | None:
    """Return a bounded stable fact when the request has a known shape."""

    lowered = str(text or "").lower().strip()
    country = None
    match = re.search(r"capital of\s+([a-zA-Z ]+?)[?.! ]*$", lowered)
    if match:
        country = normalize_entity_text(match.group(1))
    if country is None:
        match = re.search(
            r"name\s+([a-zA-Z ]+?)'s\s+capital\s+city[?.! ]*$",
            lowered,
        )
        if match:
            country = normalize_entity_text(match.group(1))
    if country is None:
        match = re.search(
            r"([a-zA-Z ]+?)'s\s+capital\s+city[?.! ]*$",
            lowered,
        )
        if match:
            country = normalize_entity_text(match.group(1))
    if (
        country
        and country in STABLE_WORLD_FACTS
        and "capital" in STABLE_WORLD_FACTS[country]
    ):
        answer = STABLE_WORLD_FACTS[country]["capital"]
        return {
            "answer": answer,
            "justification": (
                "Canonical bounded fact lookup matched the stable fact "
                f"capital({country}) = {answer}."
            ),
            "answer_kind": "direct_fact",
        }
    return None


__all__ = [
    "DECISION_ABSENCE_MARKERS",
    "DECISION_ACT_MARKERS",
    "DECISION_CONDITIONAL_MARKERS",
    "DECISION_CONFIRMATION_MARKERS",
    "DECISION_HOLD_MARKERS",
    "DECISION_UNCERTAINTY_MARKERS",
    "LEARNING_COMPONENT_BREAKS",
    "LEARNING_DISCRIMINATOR_TOKENS",
    "LEARNING_MATCH_KINDS",
    "LEARNING_STOP_TOKENS",
    "SELECTION_SIGNAL_STOP_TOKENS",
    "STABLE_WORLD_FACTS",
    "canonical_stable_fact_lookup",
    "normalize_entity_text",
]
