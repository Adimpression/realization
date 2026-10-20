# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from prolog import (
    compose_prolog_semantic_title_identity,
    looks_like_prolog_title_identity,
    normalize_prolog_title_identity,
    prolog_title_display_segments,
    prolog_title_display_text,
    prolog_title_view,
)

TITLE_REPRESENTATION_MODE_ENV = "BSSC_TITLE_REPRESENTATION"
TITLE_REPRESENTATION_MODE_SLASH = "slash"
TITLE_REPRESENTATION_MODE_PROLOG = "prolog"
PROLOG_QUERY_PRIMING_MODE_ENV = "BSSC_PROLOG_QUERY_PRIMING"
PROLOG_QUERY_PRIMING_MODE_OFF = "off"
PROLOG_QUERY_PRIMING_MODE_FALLBACK = "fallback"
PROLOG_QUERY_PRIMING_MODE_FORCE = "force"


def _collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like semantic title cleanup, title-depth normalization, and stable namespace comparison, helps with collapsing repeated whitespace into a deterministic surface.

    Reference to Theory:
        Supports title-depth and decomposition by keeping surface identity stable enough for ordered determination, reuse, and composition checks.

    Example Input Output:
        Input: `_collapse_ws(text='Physics   /  Force\\n/ Force From Mass')`
        Output: 'Physics / Force / Force From Mass'

    Args:
        text: Value for `text` used by `_collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `_collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text or "")).strip()


def title_representation_mode() -> str:
    """
    High Level Purpose:
        In circumstances like switching semantic-title surface forms between human-readable slash paths and symbolic clause heads, helps with selecting the active title representation policy.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `title_representation_mode()` with `BSSC_TITLE_REPRESENTATION='prolog'`
        Output: 'prolog'

    Args:
        None.

    Returns:
        str: Result produced by `title_representation_mode`.
    """
    raw_mode = _collapse_ws(os.getenv(TITLE_REPRESENTATION_MODE_ENV, TITLE_REPRESENTATION_MODE_SLASH)).lower()
    if raw_mode == TITLE_REPRESENTATION_MODE_PROLOG:
        return TITLE_REPRESENTATION_MODE_PROLOG
    return TITLE_REPRESENTATION_MODE_SLASH


def title_representation_is_prolog() -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether semantic titles should be interpreted as slash paths or symbolic heads, helps with checking whether Prolog title representation is active.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `title_representation_is_prolog()` with `BSSC_TITLE_REPRESENTATION='prolog'`
        Output: True

    Args:
        None.

    Returns:
        bool: Result produced by `title_representation_is_prolog`.
    """
    return title_representation_mode() == TITLE_REPRESENTATION_MODE_PROLOG


def prolog_query_priming_mode() -> str:
    """
    High Level Purpose:
        In circumstances like bridging normal-language prompts into structural Prolog retrieval, helps with selecting whether LLM-based Prolog query priming is disabled, fallback-only, or forced.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prolog_query_priming_mode()` with `BSSC_PROLOG_QUERY_PRIMING='fallback'`
        Output: 'fallback'

    Args:
        None.

    Returns:
        str: Result produced by `prolog_query_priming_mode`.
    """
    raw_mode = _collapse_ws(os.getenv(PROLOG_QUERY_PRIMING_MODE_ENV, PROLOG_QUERY_PRIMING_MODE_FALLBACK)).lower()
    if raw_mode == PROLOG_QUERY_PRIMING_MODE_FORCE:
        return PROLOG_QUERY_PRIMING_MODE_FORCE
    if raw_mode == PROLOG_QUERY_PRIMING_MODE_OFF:
        return PROLOG_QUERY_PRIMING_MODE_OFF
    return PROLOG_QUERY_PRIMING_MODE_FALLBACK


def display_title_leaf_text(title: str) -> str:
    """
    High Level Purpose:
        In circumstances like ranking and repairing human-readable artifact identities, helps with isolating the visible leaf identity from a slash-structured title so routing can reason about the determinate unit rather than the whole namespace prefix.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `display_title_leaf_text(title='Physics / Rate of Change / Speed From Distance And Time')`
        Output: 'Speed From Distance And Time'

    Args:
        title: Value for `title` used by `display_title_leaf_text`. Expected type: `str`.

    Returns:
        str: Result produced by `display_title_leaf_text`.
    """
    return _collapse_ws(str(title or "").strip().split("/")[-1].strip())


def title_inputs_prefer_prolog_surface(*values: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether a composed title should stay human-readable or become a symbolic Prolog identity, helps with checking whether the current inputs explicitly carry Prolog structure.

    Reference to Theory:
        Preserves the same title-depth law while separating representation choice from the semantic content being composed.

    Example Input Output:
        Input: `title_inputs_prefer_prolog_surface('physics:force', 'force_from_mass_and_acceleration(Mass, Acceleration, Force)')`
        Output: True

    Args:
        *values: Additional positional values supplied by the caller when checking representation preference.

    Returns:
        bool: Result produced by `title_inputs_prefer_prolog_surface`.
    """
    if not title_representation_is_prolog():
        return False
    for value in values:
        if isinstance(value, (list, tuple, set)):
            if title_inputs_prefer_prolog_surface(*list(value)):
                return True
            continue
        normalized_value = _collapse_ws(str(value or "").strip())
        if normalized_value and looks_like_prolog_title_identity(normalized_value):
            return True
    return False


def semantic_title_display_segments(title_identity: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like anchoring children, repairing markdown titles, and showing semantic order to a human reader, helps with deriving readable title-depth segments from either slash or Prolog identities.

    Reference to Theory:
        Keeps the exposed semantic order readable while allowing the formal stored identity to remain symbolic when needed.

    Example Input Output:
        Input: `semantic_title_display_segments(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        title_identity: Value for `title_identity` used by `semantic_title_display_segments`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_title_display_segments`.
    """
    normalized_title = normalize_semantic_title_identity(title_identity)
    if not normalized_title:
        return []
    if looks_like_prolog_title_identity(normalized_title):
        return prolog_title_display_segments(normalized_title)
    return derive_semantic_title_depth_segments(normalized_title)


def semantic_title_display_text(title_identity: str) -> str:
    """
    High Level Purpose:
        In circumstances like keeping artifact titles readable while still supporting symbolic structural identity, helps with rendering any semantic title identity into a human-readable slash path.

    Reference to Theory:
        Separates visible title descent from formal identity representation without changing the underlying title-depth semantics.

    Example Input Output:
        Input: `semantic_title_display_text(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration')`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        title_identity: Value for `title_identity` used by `semantic_title_display_text`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_title_display_text`.
    """
    normalized_title = normalize_semantic_title_identity(title_identity)
    if not normalized_title:
        return ""
    if looks_like_prolog_title_identity(normalized_title):
        return prolog_title_display_text(normalized_title)
    return normalized_title


def semantic_title_depth_prefix_chain(title_identity: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like reuse lookup, namespace reasoning, and decomposition guidance, helps with deriving the active prefix chain directly from a normalized semantic title identity.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on ordered determination.

    Example Input Output:
        Input: `semantic_title_depth_prefix_chain(title_identity='physics:force:add(A, B, C) :- C is A + B')`
        Output: ['physics', 'physics:force', 'physics:force:add(A, B, C)']

    Args:
        title_identity: Value for `title_identity` used by `semantic_title_depth_prefix_chain`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `semantic_title_depth_prefix_chain`.
    """
    normalized_title = normalize_semantic_title_identity(title_identity)
    if looks_like_prolog_title_identity(normalized_title):
        return list(prolog_title_view(normalized_title).get("prefixes", []))
    segments = derive_semantic_title_depth_segments(normalized_title)
    return derive_semantic_title_depth_prefix_chain(segments, separator=" / ")


def normalize_semantic_title_identity(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with normalizing semantic title identity.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `normalize_semantic_title_identity(text='Physics  /  Force / Force From Mass And Acceleration')`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `normalize_semantic_title_identity`. Expected type: `str`.

    Returns:
        str: Result produced by `normalize_semantic_title_identity`.
    """
    raw = str(text or "").strip()
    if not raw:
        return ""
    if looks_like_prolog_title_identity(raw):
        return normalize_prolog_title_identity(raw)
    parts = [_collapse_ws(part) for part in re.split(r"\s*/\s*", raw)]
    normalized_parts = [part for part in parts if part]
    if not normalized_parts:
        return _collapse_ws(raw)
    if len(normalized_parts) == 1:
        return normalized_parts[0]
    return " / ".join(normalized_parts)


def derive_semantic_title_depth_segments(title_identity: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling derive semantic title depth segments.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `derive_semantic_title_depth_segments(title_identity='Physics / Force / Force From Mass And Acceleration')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        title_identity: Value for `title_identity` used by `derive_semantic_title_depth_segments`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `derive_semantic_title_depth_segments`.
    """
    normalized_title = normalize_semantic_title_identity(title_identity)
    if not normalized_title:
        return []
    if looks_like_prolog_title_identity(normalized_title):
        return list(prolog_title_view(normalized_title).get("segments", []))
    parts = [_collapse_ws(part) for part in re.split(r"\s*/\s*", normalized_title)]
    segments = [part for part in parts if part]
    return segments or [normalized_title]


def derive_semantic_title_depth_prefix_chain(
    segments: Iterable[str],
    *,
    separator: str = " / ",
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling derive semantic title depth prefix chain.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `derive_semantic_title_depth_prefix_chain(segments=['Physics', 'Force', 'Force From Mass And Acceleration'], separator=' / ')`
        Output: ['Physics', 'Physics / Force', 'Physics / Force / Force From Mass And Acceleration']

    Args:
        segments: Value for `segments` used by `derive_semantic_title_depth_prefix_chain`. Expected type: `Iterable[str]`.
        separator: Value for `separator` used by `derive_semantic_title_depth_prefix_chain`. Expected type: `str`. Defaults to `' / '`.

    Returns:
        list[str]: Result produced by `derive_semantic_title_depth_prefix_chain`.
    """
    normalized_segments = [_collapse_ws(str(item).strip()) for item in segments if _collapse_ws(str(item).strip())]
    prefixes: list[str] = []
    running: list[str] = []
    for segment in normalized_segments:
        running.append(segment)
        prefixes.append(separator.join(running))
    return prefixes


def compose_semantic_title_identity(
    *,
    broader_category: str = "",
    current_identity: str = "",
    downward_decomposition: Sequence[str] | None = None,
    fallback_title: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like controller-side semantic decomposition, refinement, reuse, and answer formation, helps with handling compose semantic title identity.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `compose_semantic_title_identity(broader_category='Physics / Force', current_identity='Force From Mass And Acceleration', downward_decomposition=['Output Force'], fallback_title='Physics / Force / Force From Mass And Acceleration')`
        Output: 'Physics / Force / Force From Mass And Acceleration / Output Force'

    Args:
        broader_category: Value for `broader_category` used by `compose_semantic_title_identity`. Expected type: `str`. Defaults to `''`.
        current_identity: Value for `current_identity` used by `compose_semantic_title_identity`. Expected type: `str`. Defaults to `''`.
        downward_decomposition: Value for `downward_decomposition` used by `compose_semantic_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        fallback_title: Value for `fallback_title` used by `compose_semantic_title_identity`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `compose_semantic_title_identity`.
    """
    if title_inputs_prefer_prolog_surface(
        broader_category,
        current_identity,
        list(downward_decomposition or []),
        fallback_title,
    ):
        return compose_prolog_semantic_title_identity(
            broader_category=broader_category,
            current_identity=current_identity,
            downward_decomposition=downward_decomposition,
            fallback_title=fallback_title,
        )
    segment_sources: list[str] = []
    if broader_category:
        segment_sources.append(str(broader_category))
    if current_identity:
        segment_sources.append(str(current_identity))
    elif fallback_title:
        segment_sources.append(str(fallback_title))
    if downward_decomposition:
        segment_sources.extend(str(item) for item in downward_decomposition if str(item).strip())

    segments: list[str] = []
    for source in segment_sources:
        for segment in derive_semantic_title_depth_segments(source):
            normalized_segment = _collapse_ws(str(segment).strip())
            if not normalized_segment:
                continue
            if segments and semantic_namespace_key(segments[-1]) == semantic_namespace_key(normalized_segment):
                continue
            segments.append(normalized_segment)
    if not segments:
        return normalize_semantic_title_identity(fallback_title)
    return " / ".join(segments)


def compose_display_title_identity(
    *,
    broader_category: str = "",
    current_identity: str = "",
    downward_decomposition: Sequence[str] | None = None,
    fallback_title: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like artifact display, markdown title repair, and readable namespace anchoring, helps with composing a human-readable slash title from broader, current, and downward semantic layers regardless of the formal identity representation.

    Reference to Theory:
        Preserves the visible broad-to-narrow semantic descent while allowing the formal title identity to use a different structural encoding.

    Example Input Output:
        Input: `compose_display_title_identity(broader_category='physics:force', current_identity='force_from_mass_and_acceleration(Mass, Acceleration, Force)', downward_decomposition=[], fallback_title='')`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        broader_category: Value for `broader_category` used by `compose_display_title_identity`. Expected type: `str`. Defaults to `''`.
        current_identity: Value for `current_identity` used by `compose_display_title_identity`. Expected type: `str`. Defaults to `''`.
        downward_decomposition: Value for `downward_decomposition` used by `compose_display_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        fallback_title: Value for `fallback_title` used by `compose_display_title_identity`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `compose_display_title_identity`.
    """
    segment_sources: list[str] = []
    if broader_category:
        segment_sources.append(str(broader_category))
    if current_identity:
        segment_sources.append(str(current_identity))
    elif fallback_title:
        segment_sources.append(str(fallback_title))
    if downward_decomposition:
        segment_sources.extend(str(item) for item in downward_decomposition if str(item).strip())

    segments: list[str] = []
    for source in segment_sources:
        for segment in semantic_title_display_segments(source):
            normalized_segment = _collapse_ws(str(segment).strip())
            if not normalized_segment:
                continue
            if segments and semantic_namespace_key(segments[-1]) == semantic_namespace_key(normalized_segment):
                continue
            segments.append(normalized_segment)
    if not segments:
        return semantic_title_display_text(fallback_title)
    return " / ".join(segments)


def strip_markdown_outline_prefix(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like deriving title identity from markdown headings, helps with removing outline numbering and document-structure residue before title-depth analysis.

    Reference to Theory:
        Supports title-depth by preventing retrieval structure and heading residue from being mistaken for ontological identity.

    Example Input Output:
        Input: `strip_markdown_outline_prefix(text='02. Force From Mass And Acceleration')`
        Output: 'Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `strip_markdown_outline_prefix`. Expected type: `str`.

    Returns:
        str: Result produced by `strip_markdown_outline_prefix`.
    """
    candidate = _collapse_ws(str(text or "").strip())
    if not candidate:
        return ""
    candidate = re.sub(r"^\s*(?:section|part|chapter)\s+", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"^\s*(?:\d+(?:\.\d+)*|[ivxlcdm]+)(?:[\.\):\-]|\s)+", "", candidate, flags=re.IGNORECASE)
    return _collapse_ws(candidate)


def normalize_markdown_title_identity(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like converting markdown headings and repaired title fragments into stable reusable semantic identities, helps with removing outline residue and normalizing the result into the active title representation surface.

    Reference to Theory:
        Supports title-depth and decomposition by preventing heading numbering, organizational residue, and accidental formatting noise from becoming part of the stored semantic identity.

    Example Input Output:
        Input: `normalize_markdown_title_identity(text='02. Force From Mass And Acceleration')`
        Output: 'Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `normalize_markdown_title_identity`. Expected type: `str`.

    Returns:
        str: Result produced by `normalize_markdown_title_identity`.
    """
    raw = _collapse_ws(str(text or "").strip())
    if not raw:
        return ""
    stripped = strip_markdown_outline_prefix(raw)
    if looks_like_prolog_title_identity(stripped or raw):
        return semantic_title_display_text(stripped or raw)
    return normalize_semantic_title_identity(stripped or raw)


def derive_semantic_title_depth_view(
    title_identity: str,
    *,
    minimal_sufficient_depth: Any = None,
    assessment: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like comparing reusable semantic identities or persisting structured learning metadata, helps with materializing the ordered title-depth view for one semantic unit.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `derive_semantic_title_depth_view(title_identity='Physics / Force / Force From Mass And Acceleration', minimal_sufficient_depth=3, assessment='surface_segmented')`
        Output: {'title_identity': 'Physics / Force / Force From Mass And Acceleration', 'segments': ['Physics', 'Force', 'Force From Mass And Acceleration'], 'prefixes': ['Physics', 'Physics / Force', 'Physics / Force / Force From Mass And Acceleration'], 'exposed_depth': 3, 'minimal_sufficient_depth': 3, 'assessment': 'surface_segmented'}`

    Args:
        title_identity: Value for `title_identity` used by `derive_semantic_title_depth_view`. Expected type: `str`.
        minimal_sufficient_depth: Value for `minimal_sufficient_depth` used by `derive_semantic_title_depth_view`. Expected type: `Any`. Defaults to `None`.
        assessment: Value for `assessment` used by `derive_semantic_title_depth_view`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `derive_semantic_title_depth_view`.
    """
    normalized_title = normalize_semantic_title_identity(title_identity)
    segments = derive_semantic_title_depth_segments(normalized_title)
    prefixes = semantic_title_depth_prefix_chain(normalized_title)
    exposed_depth = len(segments) or (1 if normalized_title else 0)
    try:
        minimal_depth = int(minimal_sufficient_depth) if minimal_sufficient_depth not in (None, "") else exposed_depth
    except (TypeError, ValueError):
        minimal_depth = exposed_depth
    minimal_depth = max(1, minimal_depth) if normalized_title else 0
    normalized_assessment = _collapse_ws(str(assessment or "").strip())
    if not normalized_assessment:
        normalized_assessment = "surface_unsegmented" if exposed_depth <= 1 else "surface_segmented"
    return {
        "title_identity": normalized_title or (prefixes[-1] if prefixes else ""),
        "segments": segments or ([normalized_title] if normalized_title else []),
        "prefixes": prefixes or ([normalized_title] if normalized_title else []),
        "exposed_depth": exposed_depth,
        "minimal_sufficient_depth": minimal_depth,
        "assessment": normalized_assessment,
    }


def semantic_namespace_key(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like title collision checks, reuse scoring, and namespace anchoring, helps with reducing one semantic identity surface to a stable comparison key.

    Reference to Theory:
        Supports title-depth reuse and decomposition by comparing semantic identities at the namespace level rather than on unstable surface formatting alone.

    Example Input Output:
        Input: `semantic_namespace_key(text='Physics / Force / Force From Mass And Acceleration')`
        Output: 'physics / force / force from mass and acceleration'

    Args:
        text: Value for `text` used by `semantic_namespace_key`. Expected type: `str`.

    Returns:
        str: Result produced by `semantic_namespace_key`.
    """
    normalized_title = normalize_semantic_title_identity(text)
    if looks_like_prolog_title_identity(normalized_title):
        prolog_view = prolog_title_view(normalized_title)
        qualified_key = str(prolog_view.get("qualified_head_canonical", "")).strip()
        if qualified_key:
            return qualified_key.casefold()
        head_key = str(prolog_view.get("head_canonical", "")).strip() or str(prolog_view.get("head_text", "")).strip()
        if head_key:
            return head_key.casefold()
    if normalized_title:
        return normalized_title.casefold()
    return _collapse_ws(str(text or "").strip()).casefold()


def structured_title_identity_text(structured: Mapping[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like reading back structured learning payloads for reuse or comparison, helps with extracting the best semantic title identity text from the payload.

    Reference to Theory:
        Supports title-depth and reuse by keeping one stable identity source even when the payload carries several related semantic fields.

    Example Input Output:
        Input: `structured_title_identity_text(structured={'title_identity': 'Physics / Force / Force From Mass And Acceleration', 'goal': 'Force From Mass'})`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        structured: Value for `structured` used by `structured_title_identity_text`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `structured_title_identity_text`.
    """
    return (
        normalize_semantic_title_identity(structured.get("title_identity", ""))
        or normalize_semantic_title_identity(structured.get("goal", ""))
        or normalize_semantic_title_identity(structured.get("encountered_not", ""))
    )


def classify_title_depth_relation(
    current_title_identity: str,
    prior_title_identity: str,
) -> tuple[str, int]:
    """
    High Level Purpose:
        In circumstances like reuse ranking and title-collision checks, helps with classifying whether one semantic title is the same identity, a broader ground, an overdetermined extension, or only loosely related.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on ordered determination.

    Example Input Output:
        Input: `classify_title_depth_relation(current_title_identity='Physics / Force / Force From Mass And Acceleration', prior_title_identity='Physics / Force')`
        Output: ('prior_is_ground_prefix', 2)

    Args:
        current_title_identity: Value for `current_title_identity` used by `classify_title_depth_relation`. Expected type: `str`.
        prior_title_identity: Value for `prior_title_identity` used by `classify_title_depth_relation`. Expected type: `str`.

    Returns:
        tuple[str, int]: Result produced by `classify_title_depth_relation`.
    """
    current_view = derive_semantic_title_depth_view(current_title_identity)
    prior_view = derive_semantic_title_depth_view(prior_title_identity)
    current_full = str(current_view.get("title_identity", "")).strip().casefold()
    prior_full = str(prior_view.get("title_identity", "")).strip().casefold()
    if not current_full or not prior_full:
        return ("none", 0)
    if current_full == prior_full:
        return ("same_identity", len(current_view.get("segments", [])))

    current_prefixes = [semantic_namespace_key(str(item).strip()) for item in current_view.get("prefixes", []) if str(item).strip()]
    prior_prefixes = [semantic_namespace_key(str(item).strip()) for item in prior_view.get("prefixes", []) if str(item).strip()]
    if prior_full in current_prefixes[:-1]:
        shared_depth = prior_prefixes.index(prior_full) + 1 if prior_full in prior_prefixes else len(prior_view.get("segments", []))
        return ("prior_is_ground_prefix", shared_depth)
    if current_full in prior_prefixes[:-1]:
        shared_depth = current_prefixes.index(current_full) + 1 if current_full in current_prefixes else len(current_view.get("segments", []))
        return ("prior_is_overdetermined_extension", shared_depth)

    shared_prefix_depth = 0
    for current_segment, prior_segment in zip(current_view.get("segments", []), prior_view.get("segments", [])):
        if str(current_segment).strip().casefold() != str(prior_segment).strip().casefold():
            break
        shared_prefix_depth += 1
    if shared_prefix_depth > 0:
        return ("shared_ground_prefix", shared_prefix_depth)
    return ("none", 0)


def title_depth_theory_prompt_block() -> str:
    """
    High Level Purpose:
        In circumstances like prompting the LLM to propose titles, title decomposition, and semantic children, helps with supplying the operational title-depth law that constrains naming and decomposition.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `title_depth_theory_prompt_block()` with `BSSC_TITLE_REPRESENTATION='slash'`
        Output: 'Title-depth guidelines: ...'

    Args:
        None.

    Returns:
        str: Result produced by `title_depth_theory_prompt_block`.
    """
    if title_representation_is_prolog():
        return """
Title-depth guidelines:
- Assume one primary semantic burden unless clear evidence shows multiple stable top-level units.
- Identify what has become semantically determined before naming anything.
- Treat titles as ontological commitments, not summaries of the passage.
- Strip examples, rhetoric, motivation, and local heading residue before inferring identity.
- Infer the minimal stable semantic unit first, then test whether it is underdetermined or overdetermined.
- Stop at minimal sufficient determination: deep enough for stable reusable identity, not deeper.
- In Prolog mode, represent the title as a single-line symbolic head whenever possible.
- Expose broader-to-narrower title depth with namespace qualification from left to right, for example broad:ground:resolved_head(Arg1, Arg2, Out).
- The rightmost head is the determinate reusable identity; earlier qualifiers are broader grounding context.
- If body-level realization must be surfaced inline, you may use Head :- Body, but keep the title single-line and structurally parsable.
- Never read broad:ground:resolved_head(...) as a bag of labels; it is directional semantic descent.
- Later qualified parts should depend on earlier ones for full intelligibility.
- Separate title-level decomposition from body-level decomposition; the title constrains the body split.
- Apply the same law to semantic In items and Out items: if they are represented symbolically, keep them as semantic heads or atoms rather than loose labels.
- Decompose by dependency of meaning, not by sentence grammar alone.
- Prefer semantic grounds over document-local headings and retrieval convenience.
- Distinguish broader reusable substrate from narrower achieved determination.
- Preserve singularity unless the passage truly contains multiple separate reusable identities.
- Stay inside the root-local semantic namespace that is provided; do not assume any external corpus.
- Final test: at what depth has this segment first become a stable, intelligible, reusable semantic unit?
""".strip()
    return """
Title-depth guidelines:
- Assume one primary semantic burden unless clear evidence shows multiple stable top-level units.
- Identify what has become semantically determined before naming anything.
- Treat titles as ontological commitments, not summaries of the passage.
- Strip examples, rhetoric, motivation, and local heading residue before inferring identity.
- Infer the minimal stable semantic unit first, then test whether it is underdetermined or overdetermined.
- Stop at minimal sufficient determination: deep enough for stable reusable identity, not deeper.
- If segmentation is real, read earlier segments as broader ground and later segments as narrower determination.
- Never read A / B / C as a bag of labels; it is directional semantic descent.
- Later segments should depend on earlier ones for full intelligibility.
- Separate title-level decomposition from body-level decomposition; the title constrains the body split.
- Apply the same law to semantic In items and Out items: they are named semantic units, not loose labels.
- Decompose by dependency of meaning, not by sentence grammar alone.
- Prefer semantic grounds over document-local headings and retrieval convenience.
- Distinguish broader reusable substrate from narrower achieved determination.
- Preserve singularity unless the passage truly contains multiple separate reusable identities.
- Stay inside the root-local semantic namespace that is provided; do not assume any external corpus.
- Final test: at what depth has this segment first become a stable, intelligible, reusable semantic unit?
""".strip()
