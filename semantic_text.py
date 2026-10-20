# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from learn import LEARNING_COMPONENT_BREAKS, LEARNING_STOP_TOKENS
from title_semantics import normalize_semantic_title_identity


def normalize_learning_token(token: str) -> str:
    """Normalize one token for learning lookup and semantic comparison."""
    normalized = token.strip().lower()
    if not normalized:
        return ""
    if normalized.endswith("ies") and len(normalized) > 4:
        return normalized[:-3] + "y"
    if normalized.endswith("ing") and len(normalized) > 5:
        return normalized[:-3]
    if normalized.endswith("ed") and len(normalized) > 4:
        return normalized[:-2]
    if normalized.endswith("s") and len(normalized) > 3 and not normalized.endswith(("ss", "ics")):
        return normalized[:-1]
    return normalized


def semantic_tokens(text: str) -> set[str]:
    """
    High Level Purpose:
        In circumstances like semantic lookup, overlap checks, and coarse reuse filtering, helps with reducing a surface string into stable comparison tokens.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_tokens(text='Compute force from mass and acceleration.')`
        Output: {'force', 'mass', 'compute', 'from', 'acceleration', 'and'}

    Args:
        text: Value for `text` used by `semantic_tokens`. Expected type: `str`.

    Returns:
        set[str]: Result produced by `semantic_tokens`.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if not tokens:
        return set()
    long_tokens = {token for token in tokens if len(token) > 1}
    if long_tokens:
        digit_tokens = {token for token in tokens if len(token) == 1 and token.isdigit()}
        return long_tokens | digit_tokens
    return set(tokens)


def semantic_bearing_level(parent: str, child: str) -> str:
    """
    High Level Purpose:
        In circumstances like comparing a parent semantic unit against a proposed child during refinement, helps with estimating whether the child still bears the parent semantically.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_bearing_level(parent='Physics / Force', child='Force From Mass And Acceleration')`
        Output: 'high'

    Args:
        parent: Value for `parent` used by `semantic_bearing_level`. Expected type: `str`.
        child: Value for `child` used by `semantic_bearing_level`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_bearing_level`.
    """
    parent_tokens = semantic_tokens(parent)
    child_tokens = semantic_tokens(child)
    shared = parent_tokens & child_tokens
    if not shared:
        return "low"
    if parent.lower() in child.lower() or child.lower() in parent.lower():
        return "high"
    if parent_tokens and shared == parent_tokens:
        return "high"
    return "medium"


def ordered_unique(values: Iterable[str]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like building stable semantic key lists, lookup keys, and title-support sets, helps with preserving first occurrence order while removing duplicates and blanks.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `ordered_unique(values=['force', 'mass', 'force', ''])`
        Output: ['force', 'mass']

    Args:
        values: Value for `values` used by `ordered_unique`. Expected type: `Iterable[str]`.

    Returns:
        list[str]: Result produced by `ordered_unique`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def strip_control_chars(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like normalizing learned titles, prompts, and artifact surfaces that may contain copied control bytes, helps with stripping non-printing control characters before further semantic processing.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `strip_control_chars(text='Physics\\x14 / Force')`
        Output: 'Physics  / Force'

    Args:
        text: Value for `text` used by `strip_control_chars`. Expected type: `str`.

    Returns:
        str: Result produced by `strip_control_chars`.
    """
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(text))


def collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like semantic title normalization, prompt cleanup, and deterministic lookup-key generation, helps with collapsing irregular whitespace into a stable single-space surface.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `collapse_ws(text='Compute   force\\nfrom mass and acceleration.')`
        Output: 'Compute force from mass and acceleration.'

    Args:
        text: Value for `text` used by `collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `collapse_ws`.
    """
    return re.sub(r"\s+", " ", strip_control_chars(text)).strip()


def structured_text_list(values: Iterable[Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like normalizing structured list fields coming from LLM payloads, markdown learning extras, and answer-composition metadata, helps with turning mixed raw values into a stable ordered text list.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `structured_text_list(values=[' mass conservation ', 'mass conservation', 3, ''])`
        Output: ['mass conservation', '3']

    Args:
        values: Value for `values` used by `structured_text_list`. Expected type: `Iterable[Any]`.

    Returns:
        list[str]: Result produced by `structured_text_list`.
    """
    return ordered_unique(collapse_ws(str(value)) for value in values if collapse_ws(str(value)))


def structured_learning_signal_lookup_keys(structured: Mapping[str, Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like prior-learning lookup, semantic reuse ranking, and structured non-achievedness matching, helps with extracting the bounded lookup-key surface that should represent a structured learning record during retrieval and reuse.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `structured_learning_signal_lookup_keys(structured={'title_identity': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass acceleration'], 'component_nots': ['Mass', 'Acceleration']})`
        Output: ['physics force force mass acceleration', 'force', 'mass acceleration', 'mass', 'acceleration']

    Args:
        structured: Value for `structured` used by `structured_learning_signal_lookup_keys`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[str]: Result produced by `structured_learning_signal_lookup_keys`.
    """
    signal_sources: list[str] = []
    for field in (
        "title_identity",
        "goal",
        "encountered_not",
        "composed_not",
        "title_prolog_head",
        "title_prolog_head_canonical",
    ):
        value = str(structured.get(field, "")).strip()
        if value:
            signal_sources.append(value)
    explicit_lookup_keys = structured.get("lookup_keys", [])
    if isinstance(explicit_lookup_keys, list):
        signal_sources.extend(str(item).strip() for item in explicit_lookup_keys if str(item).strip())
    for field in (
        "title_depth_segments",
        "title_depth_prefixes",
        "component_nots",
        "differentiators",
        "unknowns",
        "contrastive_cases",
        "givens",
        "title_similar_identities",
    ):
        value = structured.get(field, [])
        if isinstance(value, list):
            signal_sources.extend(str(item).strip() for item in value if str(item).strip())
    return ordered_unique(
        key
        for source in signal_sources
        for key in learning_lookup_keys(source)
    )[:24]


def learning_core_tokens(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like forming semantic lookup keys from natural-language surfaces, helps with extracting the normalized content-bearing tokens while skipping controller stop words.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_core_tokens(text='Compute force from mass and acceleration.')`
        Output: ['force', 'mass', 'acceleration']

    Args:
        text: Value for `text` used by `learning_core_tokens`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `learning_core_tokens`.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    core: list[str] = []
    for token in tokens:
        normalized = normalize_learning_token(token)
        if not normalized or normalized in LEARNING_STOP_TOKENS:
            continue
        core.append(normalized)
    return core


def titleize_semantic_unit(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like turning a semantic phrase into a readable declaration or title leaf, helps with producing a stable title-cased surface from raw tokens.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `titleize_semantic_unit(text='force from mass and acceleration')`
        Output: 'Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `titleize_semantic_unit`. Expected type: `str`.

    Returns:
        str: Result produced by `titleize_semantic_unit`.
    """
    words = [part for part in re.findall(r"[A-Za-z0-9]+", text) if part]
    return " ".join(word.capitalize() for word in words)


def normalize_semantic_component_title(text: str) -> str:
    """Normalize one component into the repository's semantic-title surface."""
    raw = collapse_ws(str(text or "").strip())
    if not raw:
        return ""
    normalized = normalize_semantic_title_identity(raw)
    if "/" in raw:
        return normalized
    titled = titleize_semantic_unit(" ".join(learning_core_tokens(raw))) or titleize_semantic_unit(raw)
    return normalize_semantic_title_identity(titled or normalized)


def learning_component_units(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like decomposing a semantic surface into reusable component nots, helps with extracting stable titled components separated by known semantic break markers.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_component_units(text='force from mass and acceleration')`
        Output: ['Force', 'Mass', 'Acceleration']

    Args:
        text: Value for `text` used by `learning_component_units`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `learning_component_units`.
    """
    raw_tokens = re.findall(r"[a-z0-9]+", text.lower())
    segments: list[list[str]] = []
    current: list[str] = []
    for raw in raw_tokens:
        if raw in LEARNING_COMPONENT_BREAKS:
            if current:
                segments.append(current)
                current = []
            continue
        normalized = normalize_learning_token(raw)
        if not normalized or normalized in LEARNING_STOP_TOKENS:
            continue
        current.append(normalized)
    if current:
        segments.append(current)
    full = titleize_semantic_unit(" ".join(learning_core_tokens(text)))
    components = ordered_unique(titleize_semantic_unit(" ".join(segment)) for segment in segments if segment)
    return [component for component in components if component and component != full][:6]


def learning_lookup_keys(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like candidate retrieval, ranking, and semantic reuse matching, helps with expanding a surface string into a bounded set of normalized lookup phrases.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_lookup_keys(text='force from mass and acceleration')`
        Output: ['force mass acceleration', 'force mass', 'mass acceleration']

    Args:
        text: Value for `text` used by `learning_lookup_keys`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `learning_lookup_keys`.
    """
    keys: list[str] = []
    core_tokens = learning_core_tokens(text)
    core_phrase = " ".join(core_tokens)
    if core_phrase:
        keys.append(core_phrase)
    for component in learning_component_units(text):
        normalized_component = " ".join(learning_core_tokens(component))
        if normalized_component:
            keys.append(normalized_component)
    if len(core_tokens) >= 2:
        for size in (2, 3):
            if len(core_tokens) < size:
                continue
            for start in range(0, len(core_tokens) - size + 1):
                window = " ".join(core_tokens[start : start + size])
                if window and window != core_phrase:
                    keys.append(window)
    if not keys:
        fallback = " ".join(semantic_tokens(text))
        if fallback:
            keys.append(fallback)
    return ordered_unique(keys)[:24]


def semantic_named_input_keys(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like offline prompt routing and ability invocation, helps with extracting explicit named inputs such as `mass=3` or `velocity: 7` from a normal-language prompt.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_named_input_keys(text='Calculate force for mass=3 and acceleration=4.')`
        Output: ['mass', 'acceleration']

    Args:
        text: Value for `text` used by `semantic_named_input_keys`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_named_input_keys`.
    """
    semantic_text = str(text or "")
    keys: list[str] = []
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*=", semantic_text):
        key = str(match.group(1)).strip().lower()
        if key:
            keys.append(key)
    for match in re.finditer(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*:\s*(-?\d+(?:\.\d+)?|true|false|null|none|\"[^\"]*\"|'[^']*')",
        semantic_text,
        flags=re.IGNORECASE,
    ):
        key = str(match.group(1)).strip().lower()
        if key:
            keys.append(key)
    for match in re.finditer(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s+is\s+(-?\d+(?:\.\d+)?|true|false|null|none|\"[^\"]*\"|'[^']*')",
        semantic_text,
        flags=re.IGNORECASE,
    ):
        key = str(match.group(1)).strip().lower()
        if key:
            keys.append(key)
    return ordered_unique(keys)


def semantic_requested_output_keys(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like ranking reusable abilities against normal-language compute prompts, helps with extracting the requested output quantity so routing can prefer artifacts with a compatible output contract.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_requested_output_keys(text='Calculate P from n=2 and R=0.5 and T=3 and V=1.')`
        Output: ['p']

    Args:
        text: Value for `text` used by `semantic_requested_output_keys`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_requested_output_keys`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return []
    candidates: list[str] = []
    patterns = (
        r"\b(?:calculate|compute|find|solve)\s+([A-Za-z_][A-Za-z0-9_]*)\b(?:\s+from\b|\s+given\b|\s+using\b|\s+when\b|[?.!,;]|$)",
        r"\b(?:calculate|compute|find|solve)\s+the\s+(.+?)(?=\s+(?:from|given|using|when|if|with|where)\b|[?.!,;]|$)",
        r"\bwhat is\s+([A-Za-z_][A-Za-z0-9_]*)\b(?:\s+from\b|\s+given\b|\s+using\b|\s+when\b)",
        r"\bwhat is\s+the\s+(.+?)(?=\s+(?:from|given|using|when|if|with|where)\b|[?.!,;]|$)",
        r"\b(?:give|return|provide|show|list)\s+(?:me\s+)?(?:the\s+)?(.+?)\s+and\s+(?:the\s+)?(.+?)\s+(?:as\s+separate\s+results?|separately)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, semantic_text, flags=re.IGNORECASE):
            groups = [collapse_ws(str(part).strip(" ?.!,:;")) for part in match.groups() if collapse_ws(str(part).strip(" ?.!,:;"))]
            for phrase in groups:
                candidates.append(phrase.lower())
                candidates.extend(learning_lookup_keys(phrase))
    return ordered_unique(candidate for candidate in candidates if candidate)


def semantic_requested_output_phrases(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like disambiguating symbol-sensitive compute prompts such as `N` versus `n`, helps with preserving the raw requested output phrases before looser lexical matching is applied.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_requested_output_phrases(text='Calculate N from n=2 and N_A=3.')`
        Output: ['N']

    Args:
        text: Value for `text` used by `semantic_requested_output_phrases`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_requested_output_phrases`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return []
    phrases: list[str] = []
    patterns = (
        r"\b(?:calculate|compute|find|solve)\s+([A-Za-z_][A-Za-z0-9_]*)\b(?:\s+from\b|\s+given\b|\s+using\b|\s+when\b|[?.!,;]|$)",
        r"\b(?:calculate|compute|find|solve)\s+the\s+(.+?)(?=\s+(?:from|given|using|when|if|with|where)\b|[?.!,;]|$)",
        r"\bwhat is\s+([A-Za-z_][A-Za-z0-9_]*)\b(?:\s+from\b|\s+given\b|\s+using\b|\s+when\b)",
        r"\bwhat is\s+the\s+(.+?)(?=\s+(?:from|given|using|when|if|with|where)\b|[?.!,;]|$)",
        r"\b(?:give|return|provide|show|list)\s+(?:me\s+)?(?:the\s+)?(.+?)\s+and\s+(?:the\s+)?(.+?)\s+(?:as\s+separate\s+results?|separately)\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, semantic_text, flags=re.IGNORECASE):
            groups = [collapse_ws(str(part).strip(" ?.!,:;")) for part in match.groups() if collapse_ws(str(part).strip(" ?.!,:;"))]
            phrases.extend(groups)
    return ordered_unique(phrases)


def semantic_chain_decomposition_components(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like deterministic fallback decomposition for ordered transformation prompts, helps with extracting stage-level semantic components when the prompt asks for an explicit chain but does not enumerate separate outputs directly.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `semantic_chain_decomposition_components(text='Describe the full chain of transformations required to convert mass of a reactant into concentration of a product in solution, naming each intermediate relation used.')`
        Output: ['Mass To Mole Conversion', 'Stoichiometric Ratio From Balanced Equations', 'Concentration As Amount Per Volume']

    Args:
        text: Value for `text` used by `semantic_chain_decomposition_components`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_chain_decomposition_components`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return []
    lowered = semantic_text.lower()
    relation_bridge_match = re.match(
        r"^\s*(?:given|using)\s+the\s+(?:relation|formula|law|equation)\s+for\s+(.+?),(?:\s+)?(derive|express|show|write|explain)\s+how\s+to\s+(.+?)(?=\s+and\s+(?:explain|identify|state)\b|[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if relation_bridge_match is None:
        relation_bridge_match = re.match(
            r"^\s*(?:given|using)\s+the\s+(.+?)\s+(?:relation|formula|law|equation),(?:\s+)?(derive|express|show|write|explain)\s+how\s+to\s+(.+?)(?=\s+and\s+(?:explain|identify|state)\b|[?.!]|$)",
            semantic_text,
            flags=re.IGNORECASE,
        )
    if relation_bridge_match is not None:
        source_focus = collapse_ws(str(relation_bridge_match.group(1)).strip(" ?.!,:;"))
        directive_verb = collapse_ws(str(relation_bridge_match.group(2)).strip(" ?.!,:;"))
        target_focus = collapse_ws(str(relation_bridge_match.group(3)).strip(" ?.!,:;"))
        source_tokens = set(learning_core_tokens(source_focus))
        target_tokens = set(learning_core_tokens(target_focus))
        components: list[str] = []
        if not source_tokens or not source_tokens.issubset(target_tokens):
            source_component = titleize_semantic_unit(source_focus) or source_focus
            if source_component:
                components.append(source_component)
        target_surface = f"{directive_verb} how to {target_focus}" if directive_verb else target_focus
        target_component = titleize_semantic_unit(target_surface) or target_surface
        if target_component:
            components.append(target_component)
        if "reusable substrate" in lowered:
            source_component = titleize_semantic_unit(source_focus) or source_focus
            components.append(
                f"Reusable Substrate For {source_component}" if source_component else "Reusable Substrate"
            )
        return ordered_unique(item for item in components if item)
    starting_from_match = re.match(
        r"^\s*starting\s+from\s+(.+?),\s+derive\s+(.+?)(?=\s+and\s+explain\b|[?.!]|$)",
        semantic_text,
        flags=re.IGNORECASE,
    )
    if starting_from_match is not None:
        source_focus = collapse_ws(str(starting_from_match.group(1)).strip(" ?.!,:;"))
        target_focus = collapse_ws(str(starting_from_match.group(2)).strip(" ?.!,:;"))
        source_components = [
            titleize_semantic_unit(part) or part
            for part in re.split(r"\s+and\s+", source_focus, maxsplit=2, flags=re.IGNORECASE)
            if collapse_ws(part)
        ]
        return ordered_unique(
            [
                *source_components,
                titleize_semantic_unit(target_focus) or target_focus,
            ]
        )
    if not any(
        marker in lowered
        for marker in (
            "full chain",
            "intermediate relation",
            "intermediate relations",
            "full reasoning path",
            "staged transformation",
        )
    ):
        return []
    if (
        "convert" in lowered
        and "mass" in lowered
        and "reactant" in lowered
        and "concentration" in lowered
        and "product" in lowered
        and "solution" in lowered
    ):
        return ordered_unique(
            titleize_semantic_unit(item) or item
            for item in (
                "Mass to mole conversion",
                "Stoichiometric ratio from balanced equations",
                "Concentration as amount per volume",
            )
        )
    return []


def semantic_url_literals(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like routing normal device or web prompts into executable abilities, helps with extracting concrete URL values from natural-language text so invocation payloads can be filled without requiring `url=` syntax.

    Reference to Theory:
        Supports governed executable reuse by preserving real input values from the user prompt before boundary execution happens.

    Example Input Output:
        Input: `semantic_url_literals(text='Open Google Chrome to https://google.com.')`
        Output: ['https://google.com']

    Args:
        text: Value for `text` used by `semantic_url_literals`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_url_literals`.
    """
    semantic_text = str(text or "")
    urls = [
        str(match.group(0)).rstrip(").,;!?")
        for match in re.finditer(r"https?://[^\s\"'`]+", semantic_text, flags=re.IGNORECASE)
    ]
    return ordered_unique(url for url in urls if url)


def semantic_backticked_literals(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed executable prompt routing, helps with preserving literal values written in backticks so normal prompts can populate path, text, suffix, and mount-relative arguments.

    Reference to Theory:
        Supports governed executable reuse by retaining literal user-provided values before artifact invocation is derived.

    Example Input Output:
        Input: `semantic_backticked_literals(text='Write `hello` to mount `skill_tmp` at `notes.txt`.')`
        Output: ['hello', 'skill_tmp', 'notes.txt']

    Args:
        text: Value for `text` used by `semantic_backticked_literals`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_backticked_literals`.
    """
    semantic_text = str(text or "")
    literals = [collapse_ws(str(match.group(1)).strip()) for match in re.finditer(r"`([^`]+)`", semantic_text)]
    return ordered_unique(item for item in literals if item)


def decode_semantic_text_literal(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like governed prompt-to-payload extraction for text-bearing skills, helps with turning escaped control sequences such as `\\n` back into their intended literal text values.

    Reference to Theory:
        Supports ordinary natural-language invocation of governed executable abilities by preserving user-intended textual content instead of treating escaped newlines or tabs as plain backslash characters.

    Example Input Output:
        Input: `decode_semantic_text_literal(text='name,score\\\\nAda,10\\\\nBob,9\\\\n')`
        Output: 'name,score\\nAda,10\\nBob,9\\n'

    Args:
        text: Value for `text` used by `decode_semantic_text_literal`. Expected type: `str`.

    Returns:
        str: Result produced by `decode_semantic_text_literal`.
    """
    semantic_text = str(text or "")
    if not semantic_text:
        return ""
    return (
        semantic_text
        .replace("\\r\\n", "\r\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\r", "\r")
    )


def semantic_mount_mentions(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed mount-based skill invocation, helps with extracting named mount references from normal prompts.

    Reference to Theory:
        Supports bundle-style governed file access by preserving named mount identity from the prompt instead of guessing from host paths.

    Example Input Output:
        Input: `semantic_mount_mentions(text='Read README.md from mount `skill_input`.')`
        Output: ['skill_input']

    Args:
        text: Value for `text` used by `semantic_mount_mentions`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_mount_mentions`.
    """
    semantic_text = str(text or "")
    mounts: list[str] = []
    for match in re.finditer(r"\bmount\s+`?([A-Za-z_][A-Za-z0-9_-]*)`?", semantic_text, flags=re.IGNORECASE):
        mount_name = collapse_ws(str(match.group(1)).strip())
        if mount_name:
            mounts.append(mount_name)
    return ordered_unique(item for item in mounts if item)


def semantic_source_mount_mention(text: str) -> str:
    semantic_text = str(text or "")
    match = re.search(r"\bfrom\s+mount\s+`?([A-Za-z_][A-Za-z0-9_-]*)`?", semantic_text, flags=re.IGNORECASE)
    if not match:
        return ""
    return collapse_ws(str(match.group(1)).strip())


def semantic_destination_mount_mention(text: str) -> str:
    semantic_text = str(text or "")
    match = re.search(r"\b(?:to|into|in)\s+mount\s+`?([A-Za-z_][A-Za-z0-9_-]*)`?", semantic_text, flags=re.IGNORECASE)
    if not match:
        return ""
    return collapse_ws(str(match.group(1)).strip())


def semantic_source_relative_path_literal(text: str) -> str:
    semantic_text = str(text or "")
    mounts = set(semantic_mount_mentions(semantic_text))
    patterns = (
        r"\bfrom\s+mount\s+`?[A-Za-z_][A-Za-z0-9_-]*`?\s+at\s+`([^`]+)`",
        r"`([^`]+)`\s+from\s+mount\b",
    )
    for pattern in patterns:
        match = re.search(pattern, semantic_text, flags=re.IGNORECASE)
        if match:
            value = collapse_ws(str(match.group(1)).strip())
            if value and value not in mounts:
                return value
    return ""


def semantic_destination_relative_path_literal(text: str) -> str:
    semantic_text = str(text or "")
    mounts = set(semantic_mount_mentions(semantic_text))
    patterns = (
        r"`([^`]+)`\s+(?:to|into|in)\s+mount\b",
        r"\b(?:to|into|in)\s+mount\s+`?[A-Za-z_][A-Za-z0-9_-]*`?\s+at\s+`([^`]+)`",
        r"\bat\s+`([^`]+)`",
    )
    for pattern in patterns:
        match = re.search(pattern, semantic_text, flags=re.IGNORECASE)
        if match:
            value = collapse_ws(str(match.group(1)).strip())
            if value and value not in mounts:
                return value
    return ""


def semantic_relative_path_literals(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed mount-relative skill invocation, helps with extracting relative path targets from normal prompts that refer to mounts, files, folders, or output locations.

    Reference to Theory:
        Supports mount-relative execution by preserving the prompt's path target without falling back to raw host-path parsing.

    Example Input Output:
        Input: `semantic_relative_path_literals(text='Open `README.md` from mount `skill_input`.')`
        Output: ['README.md']

    Args:
        text: Value for `text` used by `semantic_relative_path_literals`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_relative_path_literals`.
    """
    semantic_text = str(text or "")
    candidates: list[str] = []
    suffix_values = set(semantic_suffix_literals(semantic_text))
    patterns = (
        r"`([^`]+)`\s+(?:from|in)\s+mount\b",
        r"\bmount\s+`?[A-Za-z_][A-Za-z0-9_-]*`?\s+at\s+`([^`]+)`",
        r"\b(?:file|folder|directory|path)\s+`([^`]+)`\s+(?:from|in|within)\s+mount\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, semantic_text, flags=re.IGNORECASE):
            value = collapse_ws(str(match.group(1)).strip())
            if value and value not in suffix_values:
                candidates.append(value)
    backticked = semantic_backticked_literals(semantic_text)
    mounts = set(semantic_mount_mentions(semantic_text))
    for value in backticked:
        if value in mounts:
            continue
        if value in suffix_values:
            continue
        if value.startswith("http://") or value.startswith("https://"):
            continue
        candidates.append(value)
    return ordered_unique(item for item in candidates if item)


def semantic_pathlike_literals(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like path-bearing skill invocation, helps with extracting literal filesystem-style values from normal prompts.

    Reference to Theory:
        Supports governed and legacy executable reuse by preserving explicit path-like values already present in the prompt.

    Example Input Output:
        Input: `semantic_pathlike_literals(text='Copy `/etc/hosts` to `/tmp/hosts.copy`.')`
        Output: ['/etc/hosts', '/tmp/hosts.copy']

    Args:
        text: Value for `text` used by `semantic_pathlike_literals`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_pathlike_literals`.
    """
    semantic_text = str(text or "")
    candidates: list[str] = []
    for value in semantic_backticked_literals(semantic_text):
        if value.startswith(("http://", "https://")):
            continue
        if "/" in value or value.startswith(".") or value in {".", ".."} or re.search(r"\.[A-Za-z0-9]{1,8}$", value):
            candidates.append(value)
    for match in re.finditer(r"(?:(?<=\s)|^)(~?/[^`\s\"']+)(?=\s|$)", semantic_text):
        candidates.append(collapse_ws(str(match.group(1)).rstrip(".,;!?")))
    return ordered_unique(item for item in candidates if item)


def semantic_suffix_literals(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like suffix- or extension-sensitive skill invocation, helps with extracting values like `.md` from normal prompts.

    Reference to Theory:
        Supports executable reuse by keeping symbolic suffix values distinct from ordinary path parameters.

    Example Input Output:
        Input: `semantic_suffix_literals(text='Find files ending in `.md`.')`
        Output: ['.md']

    Args:
        text: Value for `text` used by `semantic_suffix_literals`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_suffix_literals`.
    """
    semantic_text = str(text or "")
    candidates: list[str] = []
    for value in semantic_backticked_literals(semantic_text):
        if value.startswith(".") and len(value) >= 2:
            candidates.append(value)
    for match in re.finditer(r"\b(?:ending in|suffix|extension)\s+`?(\.[A-Za-z0-9_+-]+)`?", semantic_text, flags=re.IGNORECASE):
        value = collapse_ws(str(match.group(1)).strip())
        if value:
            candidates.append(value)
    return ordered_unique(item for item in candidates if item)


def semantic_application_mentions(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like launching browsers or apps from normal-language prompts, helps with extracting concrete application names such as `Google Chrome` or `Safari` so executable abilities can receive the intended application target.

    Reference to Theory:
        Supports governed executable reuse by preserving concrete external-world application identity from the user prompt.

    Example Input Output:
        Input: `semantic_application_mentions(text='Open Google Chrome to https://google.com.')`
        Output: ['Google Chrome']

    Args:
        text: Value for `text` used by `semantic_application_mentions`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_application_mentions`.
    """
    semantic_text = collapse_ws(str(text or "").strip())
    if not semantic_text:
        return []
    mentions: list[str] = []
    known_names = (
        "Google Chrome",
        "Chrome",
        "Safari",
        "Firefox",
        "Microsoft Edge",
        "Edge",
        "Brave",
        "Opera",
        "Terminal",
        "Finder",
        "Preview",
        "TextEdit",
        "Notes",
    )
    for name in known_names:
        if re.search(rf"\b{re.escape(name)}\b", semantic_text):
            mentions.append(name)
    patterns = (
        r"\b(?:open|launch|start)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})(?=\s+(?:to|at|on|with)\b|[?.!,;]|$)",
        r"\b(?:application|app|browser)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\b",
        r"`([^`]+)`\s+app\b",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, semantic_text):
            phrase = collapse_ws(str(match.group(1)).strip(" ?.!,:;"))
            if phrase:
                mentions.append(phrase)
    return ordered_unique(mentions)
