# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from typing import Any

from learn import (
    DECISION_ABSENCE_MARKERS,
    DECISION_CONFIRMATION_MARKERS,
    DECISION_UNCERTAINTY_MARKERS,
)


def _collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like interpreting prompt form and extracting directive focus, helps with normalizing whitespace so prompt-shape detection stays deterministic.

    Reference to Theory:
        Supports the applied decomposition and reuse rules by stabilizing the prompt surface before directive interpretation.

    Example Input Output:
        Input: `_collapse_ws(text='State   Newton\\'s\\nsecond law')`
        Output: 'State Newton's second law'

    Args:
        text: Value for `text` used by `_collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `_collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _normalize_directive_focus(value: str) -> str:
    """
    High Level Purpose:
        In circumstances like state, construct, and relation-bridge prompts whose literal surface contains scaffolding such as `the relation that describes` or `the full ... pathway from`, helps with reducing that surface to the semantic nucleus that retrieval and reuse should rank against.

    Reference to Theory:
        Supports the applied decomposition, title-depth, and reuse rules by keeping prompt focus aligned to the actual governing object instead of the surrounding prompt scaffolding.

    Example Input Output:
        Input: `_normalize_directive_focus(value='the relation that describes diffusion')`
        Output: 'diffusion'

    Args:
        value: Value for `value` used by `_normalize_directive_focus`. Expected type: `str`.

    Returns:
        str: Result produced by `_normalize_directive_focus`.
    """
    focus = _collapse_ws(str(value or "").strip(" \t\r\n?.!,:;()"))
    if not focus:
        return ""
    focused_patterns = (
        r"^(?:the\s+)?relation\s+that\s+describes?\s+(.+)$",
        r"^(?:the\s+)?relation\s+for\s+(.+)$",
        r"^(?:the\s+)?formula\s+for\s+(.+)$",
        r"^(?:the\s+)?law\s+for\s+(.+)$",
        r"^(?:the\s+)?equation\s+that\s+updates?\s+(.+?)\s+from\s+.+$",
    )
    for pattern in focused_patterns:
        match = re.match(pattern, focus, flags=re.IGNORECASE)
        if match is None:
            continue
        focus = _collapse_ws(str(match.group(1)).strip(" \t\r\n?.!,:;()"))
        break
    pathway_match = re.match(
        r"^(?:the\s+)?full\s+(.+?\bpathway)\b(?:\s+from\b.*)?$",
        focus,
        flags=re.IGNORECASE,
    )
    if pathway_match is not None:
        focus = _collapse_ws(str(pathway_match.group(1)).strip(" \t\r\n?.!,:;()"))
    focus = re.sub(r"^(?:the|a|an)\s+", "", focus, flags=re.IGNORECASE)
    return _collapse_ws(focus)


def semantic_prompt_directive_profile(text: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like long explanatory prompts that ask to state a law, distinguish two families, derive a relation, construct a chain, or identify a reusable substrate, helps with extracting the governing request form so reduction and reuse stay aligned with what the caller is actually asking for.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_prompt_directive_profile(text='State Newton\\'s second law and explain how it fits the multiplicative-combination substrate.')`
        Output: {'kind': 'state', 'focus_text': \"Newton's second law\", 'compared_terms': [], 'expectations': ['state the governing relation or law faithfully', 'preserve the requested variable roles, relation form, or law surface when they are asked for'], 'requires_formula': True, 'requires_contrast': False, 'requires_chain': False, 'requires_substrate': False}

    Args:
        text: Value for `text` used by `semantic_prompt_directive_profile`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `semantic_prompt_directive_profile`.
    """
    semantic_text = _collapse_ws(str(text or "").strip())
    lowered = semantic_text.lower()
    profile = {
        "kind": "none",
        "focus_text": "",
        "compared_terms": [],
        "expectations": [],
        "requires_formula": False,
        "requires_contrast": False,
        "requires_chain": False,
        "requires_substrate": False,
    }
    if not semantic_text:
        return profile

    def _clean(value: str) -> str:
        return _collapse_ws(str(value).strip(" \t\r\n?.!,:;()"))

    compare_match = re.match(
        r"^\s*(?:what\s+)?distinguishes?\s+(.+?)\s+from\s+(.+?)(?:,|\s+and\s+|\s+in\s+terms\b|[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if compare_match is None:
        compare_match = re.match(
            r"^\s*distinguish\s+between\s+(.+?)\s+and\s+(.+?)(?:,|\s+in\s+terms\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
    if compare_match is None:
        compare_match = re.match(
            r"^\s*explain\s+the\s+difference\s+between\s+(.+?)\s+and\s+(.+?)(?:,|\s+in\s+terms\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
    if compare_match is not None:
        left = _clean(str(compare_match.group(1)))
        right = _clean(str(compare_match.group(2)))
        if left and right:
            profile["kind"] = "distinguish"
            profile["focus_text"] = f"difference between {left} and {right}"
            profile["compared_terms"] = [left, right]
            profile["expectations"] = [
                "keep both contrasted cases explicit rather than answering with only one side",
                "state the discriminating difference, not just the surrounding topic",
            ]
            profile["requires_contrast"] = True
            return profile

    substrate_patterns = (
        r"^\s*identify\s+the\s+reusable\s+substrate\s+underlying\s+(.+?)(?:,|\s+and\s+|[?.!]|$)",
        r"^\s*identify\s+the\s+reusable\s+substrate\s+for\s+(.+?)(?:,|\s+and\s+|[?.!]|$)",
        r"^\s*identify\s+the\s+reusable\s+substrate\b(?:\s+of\s+(.+?))?(?:,|\s+and\s+|[?.!]|$)",
    )
    for pattern in substrate_patterns:
        match = re.match(pattern, semantic_text, flags=re.IGNORECASE)
        if match is None:
            continue
        focus = _clean(str(match.group(1) or ""))
        profile["kind"] = "identify_reusable_substrate"
        profile["focus_text"] = focus
        profile["expectations"] = [
            "separate the broader reusable substrate from the narrower determinate law or relation",
            "map the requested variables, terms, or roles onto that broader substrate when the prompt asks for it",
        ]
        profile["requires_substrate"] = True
        return profile

    if lowered.startswith("state "):
        match = re.match(
            r"^\s*state\s+(.+?)(?:,|\s+and\s+|\s+while\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
        focus = _normalize_directive_focus(_clean(str(match.group(1)))) if match is not None else ""
        profile["kind"] = "state"
        profile["focus_text"] = focus
        profile["expectations"] = [
            "state the governing relation or law faithfully",
            "preserve the requested variable roles, relation form, or law surface when they are asked for",
        ]
        profile["requires_formula"] = bool(
            re.search(r"\b(formula|relation|law|equation|variable|variables|role|roles)\b", lowered)
        )
        return profile

    if lowered.startswith("write ") and re.search(
        r"\b(formula|relation|law|equation|expression|summary|definition)\b",
        lowered,
    ):
        match = re.match(
            r"^\s*write\s+(.+?)(?:,|\s+and\s+|\s+while\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
        focus = _normalize_directive_focus(_clean(str(match.group(1)))) if match is not None else ""
        profile["kind"] = "state"
        profile["focus_text"] = focus
        profile["expectations"] = [
            "state the governing relation or law faithfully",
            "preserve the requested variable roles, relation form, or law surface when they are asked for",
        ]
        profile["requires_formula"] = True
        return profile

    if lowered.startswith("construct "):
        match = re.match(
            r"^\s*construct\s+(.+?)(?:,|\s+and\s+|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
        focus = _normalize_directive_focus(_clean(str(match.group(1)))) if match is not None else ""
        profile["kind"] = "construct"
        profile["focus_text"] = focus
        profile["expectations"] = [
            "build the ordered chain from earlier stages to the requested end state",
            "name the intermediate stages, relations, or dependencies instead of jumping straight to the final line",
        ]
        profile["requires_chain"] = True
        return profile

    split_results_match = re.search(
        r"\b(?:give|return|provide|show|list)\s+(?:me\s+)?(?:the\s+)?(.+?)\s+and\s+(?:the\s+)?(.+?)\s+(?:as\s+separate\s+results?|separately)\b",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if split_results_match is not None and re.search(
        r"\bbreak this down\b|\bseparate results?\b|\bseparately\b|\bas separate\b",
        lowered,
    ):
        left = _normalize_directive_focus(_clean(str(split_results_match.group(1))))
        right = _normalize_directive_focus(_clean(str(split_results_match.group(2))))
        profile["kind"] = "construct"
        profile["focus_text"] = _collapse_ws(" / ".join(part for part in (left, right) if part)) or semantic_text
        profile["expectations"] = [
            "separate the requested results into distinct body-level work rather than collapsing them into one surface answer",
            "preserve the shared semantic family while keeping each requested result explicit",
        ]
        profile["requires_chain"] = True
        return profile

    relation_bridge_match = re.match(
        r"^\s*(?:given|using)\s+the\s+(?:relation|formula|law|equation)\s+for\s+(.+?),(?:\s+)?(?:derive|express|show|write|explain)\s+how\s+to\s+(.+?)(?=\s+and\s+(?:explain|identify|state)\b|[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if relation_bridge_match is None:
        relation_bridge_match = re.match(
            r"^\s*(?:given|using)\s+the\s+(.+?)\s+(?:relation|formula|law|equation),(?:\s+)?(?:derive|express|show|write|explain)\s+how\s+to\s+(.+?)(?=\s+and\s+(?:explain|identify|state)\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
    if relation_bridge_match is not None:
        source_focus = _clean(str(relation_bridge_match.group(1)))
        target_focus = _clean(str(relation_bridge_match.group(2)))
        combined_focus = _collapse_ws(" / ".join(part for part in (source_focus, target_focus) if part))
        profile["kind"] = "derive"
        profile["focus_text"] = combined_focus or semantic_text
        profile["expectations"] = [
            "preserve the governing relation and the transformed target relation together",
            "show how the requested computed form follows from the given relation instead of treating it as an unrelated standalone calculation",
        ]
        profile["requires_chain"] = True
        profile["requires_formula"] = True
        profile["requires_substrate"] = "reusable substrate" in lowered
        return profile

    starting_from_match = re.match(
        r"^\s*starting\s+from\s+(.+?),\s+derive\s+(.+?)(?=\s+and\s+explain\b|[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if starting_from_match is not None:
        source_focus = _clean(str(starting_from_match.group(1)))
        target_focus = _clean(str(starting_from_match.group(2)))
        combined_focus = _collapse_ws(" / ".join(part for part in (source_focus, target_focus) if part))
        profile["kind"] = "derive"
        profile["focus_text"] = combined_focus or semantic_text
        profile["expectations"] = [
            "preserve the starting relations together with the derived target relation",
            "show the substitution chain explicitly instead of collapsing directly to the final expression",
        ]
        profile["requires_chain"] = True
        profile["requires_formula"] = True
        return profile

    if re.search(r"\bderive\b", lowered):
        derive_match = re.search(
            r"\bderive\s+(.+?)(?:,|\s+and\s+|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
        focus = _normalize_directive_focus(_clean(str(derive_match.group(1)))) if derive_match is not None else ""
        profile["kind"] = "derive"
        profile["focus_text"] = focus
        profile["expectations"] = [
            "preserve the intermediate relation chain required for the target result",
            "do not skip straight from the starting point to the final expression when the prompt asks for derivation",
        ]
        profile["requires_chain"] = True
        profile["requires_formula"] = True
        return profile

    relation_write_match = re.match(
        r"^\s*(?:given|using)\s+the\s+(.+?)\s+(?:relation|formula|law|equation),(?:\s+)?(?:write|state|give|show|derive|express|identify)\s+(.+?)(?:[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if relation_write_match is not None:
        source_focus = _normalize_directive_focus(_clean(str(relation_write_match.group(1))))
        target_focus = _normalize_directive_focus(_clean(str(relation_write_match.group(2))))
        combined_focus = _collapse_ws(" ".join(part for part in (source_focus, target_focus) if part))
        profile["kind"] = "state" if re.search(r"\b(write|state|give)\b", lowered) else "derive"
        profile["focus_text"] = combined_focus or semantic_text
        profile["expectations"] = [
            "preserve the governing relation and the requested updated relation together",
            "keep the requested variable roles or state-change structure explicit rather than collapsing to a generic family answer",
        ]
        profile["requires_formula"] = True
        profile["requires_substrate"] = "reusable substrate" in lowered or "state-plus-change" in lowered
        return profile

    if lowered.startswith(("explain ", "describe ")):
        same_family_match = re.match(
            r"^\s*explain\s+why\s+(.+?)\s+and\s+(.+?)\s+belong\s+to\s+the\s+same\s+family\b.*$",
            semantic_text,
            flags=re.IGNORECASE,
        )
        if same_family_match is not None:
            left = _clean(str(same_family_match.group(1)))
            right = _clean(str(same_family_match.group(2)))
            if left and right:
                profile["kind"] = "distinguish"
                profile["focus_text"] = f"difference between {left} and {right}"
                profile["compared_terms"] = [left, right]
                profile["expectations"] = [
                    "keep both compared laws explicit and non-collapsed",
                    "state why the laws share a family and why they still differ",
                ]
                profile["requires_contrast"] = True
                return profile
        if "reusable substrate" in lowered:
            focus = ""
            match = re.search(
                r"\breusable\s+substrate\b(?:\s+underlying\s+(.+?))?(?:,|\s+and\s+|[?.!]|$)",
                semantic_text,
                flags=re.IGNORECASE,
            )
            if match is not None:
                focus = _clean(str(match.group(1) or ""))
            profile["kind"] = "identify_reusable_substrate"
            profile["focus_text"] = focus
            profile["expectations"] = [
                "identify the broader reusable substrate explicitly",
                "separate that broader substrate from the narrower law, case, or determinate application",
            ]
            profile["requires_substrate"] = True
            return profile
        if any(
            marker in lowered
            for marker in (
                "full chain",
                "full staged transformation",
                "full reasoning path",
                "composition of earlier relations",
                "composes multiple earlier semantic substrates",
                "through composition",
                "constructed by combining earlier relations",
                "constructed by combining",
                "built by combining earlier relations",
            )
        ):
            focus = semantic_text
            construct_focus_match = re.match(
                r"^\s*(?:explain|describe)\s+how\s+(.+?)\s+(?:is|are)\s+(?:constructed|built|derived|formed)\s+(?:by|through)\s+.+$",
                semantic_text,
                flags=re.IGNORECASE,
            )
            if construct_focus_match is not None:
                focus = _normalize_directive_focus(_clean(str(construct_focus_match.group(1))))
            profile["kind"] = "construct"
            profile["focus_text"] = focus
            profile["expectations"] = [
                "preserve the ordered composition chain from earlier relations to the requested result",
                "name the intermediate dependencies or stages that make the final result intelligible",
            ]
            profile["requires_chain"] = True
            return profile
        if any(
            marker in lowered
            for marker in (
                "same family but",
                "must not be treated as the same",
                "difference between",
                "versus",
            )
        ):
            profile["kind"] = "distinguish"
            profile["focus_text"] = semantic_text
            profile["expectations"] = [
                "keep the compared cases explicit and non-collapsed",
                "state why the cases belong together and why they still differ",
            ]
            profile["requires_contrast"] = True
            return profile

    return profile


def semantic_question_focus_text(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like choosing between a real reusable knowledge artifact and a generic structured-learning record, helps with extracting the semantic focus phrase from a direct knowledge question.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_question_focus_text(text='What is mass conservation in a reaction?')`
        Output: 'mass conservation in a reaction'

    Args:
        text: Value for `text` used by `semantic_question_focus_text`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_question_focus_text`.
    """
    semantic_text = _collapse_ws(str(text or "").strip())
    if not semantic_text:
        return ""
    directive = semantic_prompt_directive_profile(semantic_text)
    directive_focus = _collapse_ws(str(directive.get("focus_text", "")).strip())
    if directive_focus:
        return directive_focus
    patterns = (
        r"^\s*(?:what is|what are|define|explain|describe|summarize)\s+(.+?)\s*[?.!]*\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, semantic_text, flags=re.IGNORECASE)
        if match:
            return _collapse_ws(str(match.group(1)).strip(" ?.!,:;"))
    return ""


def prompt_has_unresolved_uncertainty(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like direct-answer safety checks and prompt-shape routing, helps with detecting when the prompt still carries unresolved alternatives or explicit uncertainty.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prompt_has_unresolved_uncertainty(text='It could be 5 or 7 depending on the missing label.')`
        Output: True

    Args:
        text: Value for `text` used by `prompt_has_unresolved_uncertainty`. Expected type: `str`.

    Returns:
        bool: Result produced by `prompt_has_unresolved_uncertainty`.
    """
    normalized = str(text or "").lower()
    if re.search(r"\b\d+(?:\.\d+)?\b[^\n]{0,40}\bor\b[^\n]{0,40}\b\d+(?:\.\d+)?\b", normalized):
        return True
    return any(marker in normalized for marker in DECISION_UNCERTAINTY_MARKERS)


def prompt_has_confirmation_signal(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like direct-answer safety checks and action routing, helps with detecting explicit confirmation language in the prompt surface.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prompt_has_confirmation_signal(text='The match was confirmed and verified.')`
        Output: True

    Args:
        text: Value for `text` used by `prompt_has_confirmation_signal`. Expected type: `str`.

    Returns:
        bool: Result produced by `prompt_has_confirmation_signal`.
    """
    normalized = str(text or "").lower()
    return any(marker in normalized for marker in DECISION_CONFIRMATION_MARKERS)


def prompt_has_absence_signal(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like direct-answer safety checks and fact-surface preservation, helps with detecting explicit absence language so the runtime does not collapse absence into presence.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prompt_has_absence_signal(text='There is no reagent present in the sample.')`
        Output: True

    Args:
        text: Value for `text` used by `prompt_has_absence_signal`. Expected type: `str`.

    Returns:
        bool: Result produced by `prompt_has_absence_signal`.
    """
    normalized = str(text or "").lower()
    return any(marker in normalized for marker in DECISION_ABSENCE_MARKERS)


def prompt_directive_support_markers(kind: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """
    High Level Purpose:
        In circumstances like ranking reusable artifacts for long explanatory prompts, helps with defining the broad semantic markers that indicate whether an answer actually supports the requested prompt form.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prompt_directive_support_markers(kind='distinguish')`
        Output: (('difference', 'distinct', 'whereas', 'versus'), ('contrast', 'same family', 'different'))

    Args:
        kind: Value for `kind` used by `prompt_directive_support_markers`. Expected type: `str`.

    Returns:
        tuple[tuple[str, ...], tuple[str, ...]]: Result produced by `prompt_directive_support_markers`.
    """
    normalized_kind = _collapse_ws(str(kind or "").strip())
    if normalized_kind == "distinguish":
        return (
            ("difference", "distinct", "whereas", "versus", "unlike", "rather than", "but not"),
            ("contrast", "same family", "different"),
        )
    if normalized_kind == "derive":
        return (
            ("derive", "derived", "using", "from", "combine", "substitute", "therefore", "so", "step"),
            ("chain", "intermediate", "relation"),
        )
    if normalized_kind == "construct":
        return (
            ("construct", "composition", "compose", "stage", "staged", "pathway", "chain", "sequence"),
            ("intermediate", "dependency", "ordered"),
        )
    if normalized_kind == "identify_reusable_substrate":
        return (
            ("substrate", "broader", "underlying", "reusable", "family", "ground", "base"),
            ("determinate", "narrower", "application"),
        )
    if normalized_kind == "state":
        return (
            ("law", "relation", "equation", "formula", "="),
            ("governing", "states"),
        )
    return ((), ())
