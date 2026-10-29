# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from realized_core_engine.learning import (
    DECISION_ACT_MARKERS,
    DECISION_CONDITIONAL_MARKERS,
    DECISION_HOLD_MARKERS,
    SELECTION_SIGNAL_STOP_TOKENS,
)
from realized_core_semantics.prolog import prolog_title_match_score, prolog_title_view
from realized_core_engine.prompt_directives import prompt_has_unresolved_uncertainty
from realized_core_semantics.semantic_text import (
    collapse_ws,
    learning_core_tokens,
    learning_lookup_keys,
    ordered_unique,
    semantic_requested_output_keys,
)
from realized_core_semantics.title_semantics import display_title_leaf_text

ACTION_SURFACE_MARKERS: dict[str, tuple[str, ...]] = {
    "list": ("list", "entries", "directory", "folder contents"),
    "read": ("read", "load", "show file", "display file"),
    "write": ("write", "save", "store"),
    "append": ("append", "add line", "add text"),
    "copy": ("copy", "duplicate"),
    "move": ("move", "rename"),
    "delete": ("delete", "remove"),
    "open": ("open", "launch"),
    "reveal": ("reveal", "show in finder"),
    "search": ("search", "look up"),
    "download": ("download", "fetch"),
    "extract": ("extract", "unpack"),
    "create": ("create", "make"),
    "capture": ("capture", "screenshot"),
    "hash": ("sha256", "checksum", "hash"),
    "find": ("find", "locate"),
}

URGENT_SYMPTOM_MARKERS: tuple[str, ...] = (
    "trouble breathing",
    "cannot breathe",
    "can't breathe",
    "not breathing",
    "collapse",
    "collapsed",
    "seizure",
    "passed out",
    "unresponsive",
    "cannot be awakened",
    "can't be awakened",
)

EMERGENCY_ACTION_MARKERS: tuple[str, ...] = (
    "call emergency services",
    "call 911",
    "emergency care now",
    "go to the emergency room",
    "go to the er",
    "seek emergency care",
    "call emergency",
)


def primary_action_surface_marker(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like command-style prompt routing where filenames or paths may contain action words such as `copy`, helps with recovering the leading requested action from the prompt instead of treating every later lexical occurrence as equally important.

    Reference to Theory:
        Supports governed executable reuse by preserving the caller's primary requested action even when later literals or path names contain overlapping verbs.

    Example Input Output:
        Input: `primary_action_surface_marker(text='Move python-readme.copy from mount skill_tmp to mount skill_output.')`
        Output: 'move'

    Args:
        text: Value for `text` used by `primary_action_surface_marker`. Expected type: `str`.

    Returns:
        str: Result produced by `primary_action_surface_marker`.
    """
    normalized = collapse_ws(str(text or "").strip()).lower()
    if not normalized:
        return ""
    prefix_patterns = (
        "",
        r"(?:please|kindly)\s+",
        r"(?:(?:can|could|would|will)\s+you\s+)",
        r"(?:please\s+)?(?:show\s+me\s+how\s+to|tell\s+me\s+how\s+to|how\s+to|how\s+do\s+you\s+)",
    )
    for canonical, markers in ACTION_SURFACE_MARKERS.items():
        for marker in markers:
            for prefix in prefix_patterns:
                if re.search(
                    rf"^\s*(?:{prefix}){re.escape(marker)}\b",
                    normalized,
                ):
                    return canonical
    return ""


def learning_overlap(left: str, right: str) -> bool:
    """
    High Level Purpose:
        In circumstances like comparing candidate lookup keys during retrieval and reuse ranking, helps with treating narrow lexical containment as a weak semantic overlap signal.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `learning_overlap(left='force', right='force from mass and acceleration')`
        Output: True

    Args:
        left: Value for `left` used by `learning_overlap`. Expected type: `str`.
        right: Value for `right` used by `learning_overlap`. Expected type: `str`.

    Returns:
        bool: Result produced by `learning_overlap`.
    """
    left_normalized = left.strip().lower()
    right_normalized = right.strip().lower()
    if not left_normalized or not right_normalized:
        return False
    if left_normalized == right_normalized:
        return True
    return left_normalized in right_normalized or right_normalized in left_normalized


def output_lookup_compatible(requested_key: str, artifact_key: str) -> bool:
    """
    High Level Purpose:
        In circumstances like compute-prompt routing where output quantities may be one-letter symbols or longer semantic phrases, helps with requiring stronger compatibility than raw substring overlap so symbols like `a` do not spuriously match arbitrary phrases.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `output_lookup_compatible(requested_key='slant side', artifact_key='a')`
        Output: False

    Args:
        requested_key: Value for `requested_key` used by `output_lookup_compatible`. Expected type: `str`.
        artifact_key: Value for `artifact_key` used by `output_lookup_compatible`. Expected type: `str`.

    Returns:
        bool: Result produced by `output_lookup_compatible`.
    """
    requested_normalized = collapse_ws(str(requested_key or "").strip()).lower()
    artifact_normalized = collapse_ws(str(artifact_key or "").strip()).lower()
    if not requested_normalized or not artifact_normalized:
        return False
    if requested_normalized == artifact_normalized:
        return True
    if len(requested_normalized) <= 1 or len(artifact_normalized) <= 1:
        return False
    requested_tokens = requested_normalized.split()
    artifact_tokens = artifact_normalized.split()
    if len(requested_tokens) == 1 and len(artifact_tokens) > 1:
        return artifact_tokens[0] == requested_tokens[0]
    if len(artifact_tokens) == 1 and len(requested_tokens) > 1:
        return requested_tokens[0] == artifact_tokens[0]
    return learning_overlap(requested_normalized, artifact_normalized)


def action_surface_markers(text: str) -> set[str]:
    """
    High Level Purpose:
        In circumstances like separating executable command families that share mount or path arguments, helps with extracting the primary action verbs implied by a prompt or artifact surface.

    Reference to Theory:
        Supports governed executable reuse by keeping action-family routing aligned with what the prompt is actually asking the skill to do.

    Example Input Output:
        Input: `action_surface_markers(text='List the entries in mount skill_input at trials.')`
        Output: {'list'}

    Args:
        text: Value for `text` used by `action_surface_markers`. Expected type: `str`.

    Returns:
        set[str]: Result produced by `action_surface_markers`.
    """
    normalized = collapse_ws(str(text or "").strip()).lower()
    if not normalized:
        return set()
    found: set[str] = set()
    for canonical, markers in ACTION_SURFACE_MARKERS.items():
        if any(re.search(rf"\b{re.escape(marker)}\b", normalized) for marker in markers):
            found.add(canonical)
    return found


def artifact_action_alignment_penalty(artifact: Any, semantic_unit: str) -> int:
    """
    High Level Purpose:
        In circumstances like routing prompt-executable matches between similar mount- or path-shaped skills, helps with penalizing artifacts whose main action family conflicts with the prompt action.

    Reference to Theory:
        Supports executable selection by preventing payload completeness alone from outranking the requested action semantics.

    Example Input Output:
        Input: `artifact_action_alignment_penalty(artifact=Artifact(id='artifact-append', title='Append Text File', content={'question': 'How do you append text to a file?'}), semantic_unit='List the entries in mount skill_input at trials.')`
        Output: 6

    Args:
        artifact: Value for `artifact` used by `artifact_action_alignment_penalty`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `semantic_unit`. Expected type: `str`.

    Returns:
        int: Result produced by `artifact_action_alignment_penalty`.
    """
    prompt_primary_action = primary_action_surface_marker(semantic_unit)
    prompt_actions = {prompt_primary_action} if prompt_primary_action else action_surface_markers(semantic_unit)
    if not prompt_actions:
        return 0
    artifact_actions = action_surface_markers(artifact_selection_text(artifact))
    if not artifact_actions:
        return 0
    if prompt_actions & artifact_actions:
        return 0
    return 12


def selection_signal_tokens(text: str) -> set[str]:
    """
    High Level Purpose:
        In circumstances like ranking artifacts against a prompt, helps with extracting the small set of lexical signal tokens that should drive lightweight alignment checks.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `selection_signal_tokens(text='Compute force from mass and acceleration.')`
        Output: {'compute', 'force', 'mass', 'acceleration'}

    Args:
        text: Value for `text` used by `selection_signal_tokens`. Expected type: `str`.

    Returns:
        set[str]: Result produced by `selection_signal_tokens`.
    """
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if token and token not in SELECTION_SIGNAL_STOP_TOKENS
    }
    return tokens


def selection_signal_phrases(text: str, *, size: int = 2) -> set[str]:
    """
    High Level Purpose:
        In circumstances like tie-breaking between closely related artifacts, helps with extracting short contiguous lexical phrases that capture more structure than individual tokens.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `selection_signal_phrases(text='Compute force from mass and acceleration.', size=2)`
        Output: {'compute force', 'force mass', 'mass acceleration'}

    Args:
        text: Value for `text` used by `selection_signal_phrases`. Expected type: `str`.
        size: Value for `size` used by `selection_signal_phrases`. Expected type: `int`. Defaults to `2`.

    Returns:
        set[str]: Result produced by `selection_signal_phrases`.
    """
    tokens = [token for token in re.findall(r"[a-z0-9]+", str(text or "").lower()) if token and token not in SELECTION_SIGNAL_STOP_TOKENS]
    if len(tokens) < size:
        return set()
    return {" ".join(tokens[index : index + size]) for index in range(0, len(tokens) - size + 1)}


def ordinal_focus_markers(text: str) -> set[str]:
    """
    High Level Purpose:
        In circumstances like ranking members of a titled family such as first, second, or third law prompts, helps with detecting which ordinal member the caller or artifact surface singles out.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `ordinal_focus_markers(text=\"What is Newton's first law of motion?\")`
        Output: {'first'}

    Args:
        text: Value for `text` used by `ordinal_focus_markers`. Expected type: `str`.

    Returns:
        set[str]: Result produced by `ordinal_focus_markers`.
    """
    normalized = collapse_ws(str(text or "")).lower()
    markers: dict[str, tuple[str, ...]] = {
        "first": ("first", "1st"),
        "second": ("second", "2nd"),
        "third": ("third", "3rd"),
        "fourth": ("fourth", "4th"),
        "fifth": ("fifth", "5th"),
        "sixth": ("sixth", "6th"),
        "seventh": ("seventh", "7th"),
        "eighth": ("eighth", "8th"),
        "ninth": ("ninth", "9th"),
        "tenth": ("tenth", "10th"),
    }
    found: set[str] = set()
    for canonical, variants in markers.items():
        if any(re.search(rf"\b{re.escape(variant)}\b", normalized) for variant in variants):
            found.add(canonical)
    return found


def artifact_selection_text(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like ranking an artifact against a prompt, helps with assembling the compact surface text that best represents what the artifact says and claims.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_selection_text(artifact=Artifact(id='artifact-force', title='Physics / Force From Mass And Acceleration', scope='closed-form arithmetic', justification='reusable ability', constraints=['requires mass and acceleration'], content={'question': 'Calculate force from mass and acceleration.', 'answer': 'F = m * a', 'aliases': ['force law']}))`
        Output: 'Physics / Force From Mass And Acceleration Calculate force from mass and acceleration. F = m * a closed-form arithmetic reusable ability force law requires mass and acceleration'

    Args:
        artifact: Value for `artifact` used by `artifact_selection_text`. Expected type: `Any`.

    Returns:
        str: Result produced by `artifact_selection_text`.
    """
    title = str(getattr(artifact, "title", "")).strip()
    scope = str(getattr(artifact, "scope", "")).strip()
    justification = str(getattr(artifact, "justification", "")).strip()
    constraints = list(getattr(artifact, "constraints", [])) if isinstance(getattr(artifact, "constraints", []), list) else []
    content = getattr(artifact, "content", {})
    if not isinstance(content, Mapping):
        content = {}
    aliases = content.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    parts = [
        title,
        str(content.get("question", "")).strip(),
        str(content.get("answer", "")).strip(),
        scope,
        justification,
        *[str(item).strip() for item in aliases if str(item).strip()],
        *[str(item).strip() for item in constraints if str(item).strip()],
    ]
    return collapse_ws(" ".join(part for part in parts if part))


def artifact_is_structured_learning_record(artifact: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like ranking real knowledge or ability artifacts against generated residue, helps with recognizing structured-learning records so they can be demoted when stronger artifacts exist.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `artifact_is_structured_learning_record(artifact=Artifact(id='artifact-structured-record', title='Structured learning record for Mass Conservation Reaction', artifact_type='knowledge', representation='yaml'))`
        Output: True

    Args:
        artifact: Value for `artifact` used by `artifact_is_structured_learning_record`. Expected type: `Any`.

    Returns:
        bool: Result produced by `artifact_is_structured_learning_record`.
    """
    title = collapse_ws(str(getattr(artifact, "title", "")).strip()).lower()
    return title.startswith("structured learning record for")


def artifact_output_lookup_keys(artifact: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like routing a compute prompt toward the correct reusable ability, helps with collecting the output-side semantic keys that describe what quantity the artifact returns.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `artifact_output_lookup_keys(artifact=Artifact(id='artifact-pressure', title='Chemistry / Pressure From Amount Temperature And Volume', artifact_type='ability', representation='python_script', content={'output_field': 'P', 'output_contract': {'pressure': 'number'}, 'question': 'Calculate pressure from amount, temperature, and volume.'}))`
        Output: ['p', 'pressure', 'pressure amount temperature volume']

    Args:
        artifact: Value for `artifact` used by `artifact_output_lookup_keys`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `artifact_output_lookup_keys`.
    """
    content = getattr(artifact, "content", {})
    if not isinstance(content, Mapping):
        content = {}
    output_keys: list[str] = []
    output_field = collapse_ws(str(content.get("output_field", "")).strip())
    if output_field:
        output_keys.append(output_field.lower())
        output_keys.extend(learning_lookup_keys(output_field))
    output_contract = content.get("output_contract", {})
    if isinstance(output_contract, Mapping):
        for key in output_contract.keys():
            key_text = collapse_ws(str(key).strip())
            if not key_text:
                continue
            output_keys.append(key_text.lower())
            output_keys.extend(learning_lookup_keys(key_text))
    question = collapse_ws(str(content.get("question", "")).strip())
    if question:
        output_keys.extend(semantic_requested_output_keys(question))
    title_text = collapse_ws(str(getattr(artifact, "title", "")).strip())
    if title_text:
        output_keys.extend(semantic_requested_output_keys(title_text))
        title_leaf = display_title_leaf_text(title_text)
        if title_leaf:
            output_keys.extend(learning_lookup_keys(title_leaf))
            head_match = re.match(
                r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:\s+[A-Za-z_][A-Za-z0-9_]*){0,5})\s+from\b",
                title_leaf,
                flags=re.IGNORECASE,
            )
            if head_match:
                head_phrase = collapse_ws(str(head_match.group(1)).strip(" ?.!,:;"))
                if head_phrase:
                    output_keys.append(head_phrase.lower())
                    output_keys.extend(learning_lookup_keys(head_phrase))
            pair_match = re.match(
                r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+and\s+([A-Za-z_][A-Za-z0-9_]*)\s*$",
                title_leaf,
                flags=re.IGNORECASE,
            )
            if pair_match:
                for group_index in (1, 2):
                    phrase = collapse_ws(str(pair_match.group(group_index)).strip())
                    if phrase:
                        output_keys.append(phrase.lower())
                        output_keys.extend(learning_lookup_keys(phrase))
    return ordered_unique(key for key in output_keys if key)


def artifact_focus_alignment_score(artifact: Any, focus_text: str) -> int:
    """
    High Level Purpose:
        In circumstances like selecting a direct explanatory artifact for a focused concept prompt, helps with scoring whether an artifact is actually about the requested focus rather than merely lexically adjacent.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `artifact_focus_alignment_score(artifact=Artifact(id='artifact-conservation', title='Chemistry / Mass Conservation Preserves Total Mass', artifact_type='knowledge', representation='yaml'), focus_text='mass conservation in a reaction')`
        Output: 2

    Args:
        artifact: Value for `artifact` used by `artifact_focus_alignment_score`. Expected type: `Any`.
        focus_text: Value for `focus_text` used by `artifact_focus_alignment_score`. Expected type: `str`.

    Returns:
        int: Result produced by `artifact_focus_alignment_score`.
    """
    normalized_focus = collapse_ws(str(focus_text or "").strip()).lower()
    if not normalized_focus:
        return 0
    artifact_text = artifact_selection_text(artifact).lower()
    if normalized_focus in artifact_text:
        return 2
    focus_keys = learning_lookup_keys(normalized_focus)
    if not focus_keys:
        focus_tokens = set(learning_core_tokens(normalized_focus))
        artifact_tokens = set(learning_core_tokens(artifact_text))
        shared_tokens = focus_tokens & artifact_tokens
        if len(shared_tokens) >= 2:
            return 2
        if shared_tokens:
            return 1
        return 0
    artifact_keys = learning_lookup_keys(artifact_text)
    hits = sum(
        1
        for key in focus_keys
        if any(learning_overlap(key, candidate) for candidate in artifact_keys)
    )
    if hits >= max(1, len(focus_keys) - 1):
        return 2
    if hits:
        return 1
    focus_tokens = set(learning_core_tokens(normalized_focus))
    artifact_tokens = set(learning_core_tokens(artifact_text))
    shared_tokens = focus_tokens & artifact_tokens
    if len(shared_tokens) >= 2:
        return 2
    if shared_tokens:
        return 1
    return 0


def artifact_prompt_decision_mismatch_penalty(artifact: Any, semantic_unit: str) -> int:
    """
    High Level Purpose:
        In circumstances like answering prompts that contain uncertainty or guarded decision logic, helps with penalizing artifacts whose advice is too decisive for the prompt conditions.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_prompt_decision_mismatch_penalty(artifact=Artifact(id='artifact-force', title='Physics / Force From Mass And Acceleration', content={'answer': 'Proceed immediately.'}), semantic_unit='If the reading is uncertain, should I proceed or wait?')`
        Output: 6

    Args:
        artifact: Value for `artifact` used by `artifact_prompt_decision_mismatch_penalty`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `artifact_prompt_decision_mismatch_penalty`. Expected type: `str`.

    Returns:
        int: Result produced by `artifact_prompt_decision_mismatch_penalty`.
    """
    prompt_text = str(semantic_unit or "").lower()
    artifact_text = artifact_selection_text(artifact).lower()
    penalty = 0

    has_hold_guidance = any(marker in artifact_text for marker in DECISION_HOLD_MARKERS)
    has_affirmative_action = any(marker in artifact_text for marker in DECISION_ACT_MARKERS)
    has_conditional_guard = any(marker in artifact_text for marker in DECISION_CONDITIONAL_MARKERS)
    prompt_requires_emergency_action = any(marker in prompt_text for marker in URGENT_SYMPTOM_MARKERS)
    has_emergency_action = any(marker in artifact_text for marker in EMERGENCY_ACTION_MARKERS)

    if prompt_requires_emergency_action:
        if not has_emergency_action:
            penalty += 5
        else:
            return penalty

    if prompt_has_unresolved_uncertainty(prompt_text):
        if not has_hold_guidance:
            penalty += 2
        if has_affirmative_action and has_conditional_guard and not has_hold_guidance:
            penalty += 1
        if has_affirmative_action and not has_conditional_guard and not has_hold_guidance:
            penalty += 4

    return penalty


def text_alignment_rank(prompt_text: str, candidate_text: str) -> tuple[int, int, int, int]:
    """
    High Level Purpose:
        In circumstances like sorting multiple candidate artifacts by lexical fit, helps with turning token and phrase overlap into a stable sortable rank tuple.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `text_alignment_rank(prompt_text='Compute force from mass and acceleration.', candidate_text='Calculate force from mass and acceleration.')`
        Output: (-2, -4, 0, 1)

    Args:
        prompt_text: Value for `prompt_text` used by `text_alignment_rank`. Expected type: `str`.
        candidate_text: Value for `candidate_text` used by `text_alignment_rank`. Expected type: `str`.

    Returns:
        tuple[int, int, int, int]: Result produced by `text_alignment_rank`.
    """
    prompt_tokens = selection_signal_tokens(prompt_text)
    artifact_tokens = selection_signal_tokens(candidate_text)
    shared_tokens = prompt_tokens & artifact_tokens
    prompt_phrases = selection_signal_phrases(prompt_text, size=2)
    artifact_phrases = selection_signal_phrases(candidate_text, size=2)
    shared_phrases = prompt_phrases & artifact_phrases
    missing_prompt_tokens = len(prompt_tokens - artifact_tokens)
    extra_artifact_tokens = len(artifact_tokens - prompt_tokens)
    return (-len(shared_phrases), -len(shared_tokens), missing_prompt_tokens, extra_artifact_tokens)


def prolog_surface_alignment_rank(prompt_text: str, candidate_text: str) -> tuple[int, int, int, int] | None:
    """
    High Level Purpose:
        In circumstances like ranking symbolic artifacts against Prolog-shaped queries, helps with converting head compatibility into a sortable alignment rank.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules.

    Example Input Output:
        Input: `prolog_surface_alignment_rank(prompt_text='physics:force:add(2, Y, Z)', candidate_text='physics:force:add(A, B, C) :- C is A + B')`
        Output: (-100, -2, 0, 0)

    Args:
        prompt_text: Value for `prompt_text` used by `prolog_surface_alignment_rank`. Expected type: `str`.
        candidate_text: Value for `candidate_text` used by `candidate_text`. Expected type: `str`.

    Returns:
        tuple[int, int, int, int] | None: Result produced by `prolog_surface_alignment_rank`.
    """
    match_score = prolog_title_match_score(prompt_text, candidate_text)
    if match_score <= 0:
        return None
    query_view = prolog_title_view(prompt_text)
    candidate_view = prolog_title_view(candidate_text)
    shared_namespace_depth = 0
    query_namespace = [str(item).strip().casefold() for item in query_view.get("segments", [])[:-1] if str(item).strip()]
    candidate_namespace = [str(item).strip().casefold() for item in candidate_view.get("segments", [])[:-1] if str(item).strip()]
    for query_part, candidate_part in zip(query_namespace, candidate_namespace):
        if query_part != candidate_part:
            break
        shared_namespace_depth += 1
    arity_gap = abs(int(query_view.get("arity", 0)) - int(candidate_view.get("arity", 0)))
    return (-match_score, -shared_namespace_depth, arity_gap, 0)


def artifact_surface_alignment_rank(artifact: Any, semantic_unit: str) -> tuple[int, int, int, int]:
    """
    High Level Purpose:
        In circumstances like comparing a prompt against visible artifact surfaces, helps with choosing the best title, question, or alias match while allowing symbolic Prolog surfaces to participate.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_surface_alignment_rank(artifact=Artifact(id='artifact-force', title='Physics / Force From Mass And Acceleration', content={'question': 'Calculate force from mass and acceleration.', 'aliases': ['force law']}), semantic_unit='Calculate force from mass and acceleration.')`
        Output: (-2, -4, 0, 1)

    Args:
        artifact: Value for `artifact` used by `artifact_surface_alignment_rank`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `artifact_surface_alignment_rank`. Expected type: `str`.

    Returns:
        tuple[int, int, int, int]: Result produced by `artifact_surface_alignment_rank`.
    """
    content = getattr(artifact, "content", {})
    if not isinstance(content, Mapping):
        content = {}
    aliases = content.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    candidates = [
        str(getattr(artifact, "title", "")).strip(),
        str(content.get("question", "")).strip(),
        *[str(item).strip() for item in aliases if str(item).strip()],
    ]
    prolog_ranks = [
        rank
        for candidate in candidates
        for rank in [prolog_surface_alignment_rank(str(semantic_unit or ""), candidate)]
        if rank is not None
    ]
    if prolog_ranks:
        return min(prolog_ranks)
    ranks = [text_alignment_rank(str(semantic_unit or ""), candidate) for candidate in candidates if candidate]
    if not ranks:
        return (0, 0, 0, 0)
    return min(ranks)


def artifact_text_alignment_rank(artifact: Any, semantic_unit: str) -> tuple[int, int, int, int]:
    """
    High Level Purpose:
        In circumstances like whole-artifact ranking, helps with comparing the prompt against the artifact's combined selection surface rather than only its title or aliases.

    Reference to Theory:
        Implements the applied controller semantics around semantic units, title-depth, decomposition, refinement, reuse, and composition, especially THEORY.md section 8.8 and the surrounding boundary rules. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_text_alignment_rank(artifact=Artifact(id='artifact-force', title='Physics / Force From Mass And Acceleration', content={'question': 'Calculate force from mass and acceleration.', 'answer': 'F = m * a'}), semantic_unit='Calculate force from mass and acceleration.')`
        Output: (-2, -4, 0, 2)

    Args:
        artifact: Value for `artifact` used by `artifact_text_alignment_rank`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `semantic_unit`. Expected type: `str`.

    Returns:
        tuple[int, int, int, int]: Result produced by `artifact_text_alignment_rank`.
    """
    prompt_text = str(semantic_unit or "")
    artifact_text = artifact_selection_text(artifact)
    return text_alignment_rank(prompt_text, artifact_text)
