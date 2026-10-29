# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


__all__ = [
    "split_prolog_clause",
    "split_prolog_namespace",
    "looks_like_prolog_title_identity",
    "prolog_title_atom",
    "prolog_title_segment_display_text",
    "parse_prolog_term",
    "prolog_term_text",
    "prolog_terms_unify",
    "prolog_unify_bindings",
    "instantiate_prolog_body_text",
    "normalize_prolog_title_identity",
    "prolog_title_view",
    "prolog_title_display_segments",
    "prolog_title_display_text",
    "prolog_contract_argument_roles",
    "prolog_contract_alias_map",
    "synthesize_prolog_query_title_identity",
    "derive_prolog_query_invocation_payload",
    "prolog_title_match_score",
    "prolog_title_query_variants",
    "compose_prolog_semantic_title_identity",
    "synthesize_prolog_formal_title_identity",
]


def _collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like symbolic title parsing, clause normalization, and structural matching, helps with collapsing repeated whitespace without disturbing logical structure.

    Reference to Theory:
        Supports the applied title-depth and decomposition rules by keeping symbolic title surfaces stable enough for matching and reuse.

    Example Input Output:
        Input: `_collapse_ws(text='math:add:add( A ,  B , C )  :-   C is A + B')`
        Output: 'math:add:add( A , B , C ) :- C is A + B'

    Args:
        text: Value for `text` used by `_collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `_collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _ordered_unique(values: Sequence[str] | list[str]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like symbolic query expansion and namespace normalization, helps with preserving first-seen order while removing duplicates.

    Reference to Theory:
        Supports stable reuse and comparison by preventing repeated symbolic surfaces from distorting the retrieval set.

    Example Input Output:
        Input: `_ordered_unique(values=['add', 'add', 'sum', 'add'])`
        Output: ['add', 'sum']

    Args:
        values: Value for `values` used by `_ordered_unique`. Expected type: `Sequence[str] | list[str]`.

    Returns:
        list[str]: Result produced by `_ordered_unique`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _normalize_learning_lookup_token(token: str) -> str:
    """
    High Level Purpose:
        In circumstances like converting natural-language title fragments into symbolic atoms, helps with normalizing lookup tokens into stable stem-like forms.

    Reference to Theory:
        Supports stable semantic naming by reducing incidental inflection before symbolic title construction.

    Example Input Output:
        Input: `_normalize_learning_lookup_token(token='accelerations')`
        Output: 'acceleration'

    Args:
        token: Value for `token` used by `_normalize_learning_lookup_token`. Expected type: `str`.

    Returns:
        str: Result produced by `_normalize_learning_lookup_token`.
    """
    normalized = str(token or "").strip().lower()
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


def _learning_core_tokens(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like mapping descriptive title fragments into Prolog-safe atoms, helps with extracting normalized semantic tokens from ordinary text.

    Reference to Theory:
        Supports semantic singularity and title-depth stability by stripping surface noise before symbolic representation.

    Example Input Output:
        Input: `_learning_core_tokens(text='Force From Mass And Acceleration')`
        Output: ['force', 'from', 'mass', 'and', 'acceleration']

    Args:
        text: Value for `text` used by `_learning_core_tokens`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_learning_core_tokens`.
    """
    raw_tokens = re.findall(r"[a-z0-9]+", str(text or "").lower())
    return [_normalize_learning_lookup_token(token) for token in raw_tokens if _normalize_learning_lookup_token(token)]


def _split_title_segments(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like anchoring symbolic identities under broader slash-path categories, helps with extracting non-empty semantic title segments from a slash title.

    Reference to Theory:
        Supports ordered determination by preserving broad-to-narrow title segments before symbolic translation.

    Example Input Output:
        Input: `_split_title_segments(text='Physics / Force / Force From Mass And Acceleration')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        text: Value for `text` used by `_split_title_segments`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_split_title_segments`.
    """
    return [segment for segment in (_collapse_ws(part) for part in re.split(r"\s*/\s*", str(text or ""))) if segment]


def _split_top_level_text(text: str, delimiter: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like parsing qualified semantic heads, clause bodies, or nested term arguments, helps with splitting text only at top-level separators.

    Reference to Theory:
        Supports the applied title-depth and decomposition rules by keeping symbolic structure intact while separating only the intended logical boundaries.

    Example Input Output:
        Input: `_split_top_level_text(text='physics:force:add(A, B, C)', delimiter=':')`
        Output: ['physics', 'force', 'add(A, B, C)']

    Args:
        text: Value for `text` used by `_split_top_level_text`. Expected type: `str`.
        delimiter: Value for `delimiter` used by `_split_top_level_text`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_split_top_level_text`.
    """
    normalized_text = str(text or "")
    if not delimiter:
        return [normalized_text]
    parts: list[str] = []
    start = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    quote: str | None = None
    index = 0
    while index < len(normalized_text):
        char = normalized_text[index]
        if quote:
            if char == quote and (index == 0 or normalized_text[index - 1] != "\\"):
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(0, brace_depth - 1)
        if (
            paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
            and normalized_text.startswith(delimiter, index)
        ):
            parts.append(normalized_text[start:index].strip())
            index += len(delimiter)
            start = index
            continue
        index += 1
    parts.append(normalized_text[start:].strip())
    return parts


def split_prolog_clause(text: str) -> tuple[str, str]:
    """
    High Level Purpose:
        In circumstances like separating symbolic identity from a clause body, helps with splitting a Prolog-form title into head and body parts.

    Reference to Theory:
        Supports the distinction between title-level identity and body-level realization in the applied decomposition law.

    Example Input Output:
        Input: `split_prolog_clause(text='add(A, B, C) :- C is A + B')`
        Output: ('add(A, B, C)', 'C is A + B')

    Args:
        text: Value for `text` used by `split_prolog_clause`. Expected type: `str`.

    Returns:
        tuple[str, str]: Result produced by `split_prolog_clause`.
    """
    parts = _split_top_level_text(_collapse_ws(str(text or "").strip()), ":-")
    if len(parts) <= 1:
        return (_collapse_ws(str(text or "").strip()), "")
    head_text = parts[0]
    body_text = " :- ".join(part for part in parts[1:] if part)
    return (head_text, body_text)


def split_prolog_namespace(head_text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like representing broader-to-narrower semantic grounding as qualified symbolic heads, helps with separating a Prolog head into namespace-qualified segments.

    Reference to Theory:
        Supports ordered determination by preserving the broad-to-narrow chain encoded in symbolic qualification.

    Example Input Output:
        Input: `split_prolog_namespace(head_text='physics:force:add(A, B, C)')`
        Output: ['physics', 'force', 'add(A, B, C)']

    Args:
        head_text: Value for `head_text` used by `split_prolog_namespace`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `split_prolog_namespace`.
    """
    parts = [_collapse_ws(part) for part in _split_top_level_text(head_text, ":")]
    return [part for part in parts if part]


def looks_like_prolog_title_identity(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether a returned semantic title should be treated as a symbolic head rather than a slash path, helps with recognizing Prolog-shaped title syntax.

    Reference to Theory:
        Supports the swappable title-representation experiment while preserving the same semantic identity rules.

    Example Input Output:
        Input: `looks_like_prolog_title_identity(text='physics:force:add(A, B, C) :- C is A + B')`
        Output: True

    Args:
        text: Value for `text` used by `looks_like_prolog_title_identity`. Expected type: `str`.

    Returns:
        bool: Result produced by `looks_like_prolog_title_identity`.
    """
    raw = _collapse_ws(str(text or "").strip())
    if not raw:
        return False
    head_text, body_text = split_prolog_clause(raw)
    if body_text:
        return True
    namespace_parts = split_prolog_namespace(head_text)
    if len(namespace_parts) > 1:
        return all(
            bool(re.fullmatch(r"[a-z][a-z0-9_]*", part))
            or (
                "(" in part
                and part.endswith(")")
                and bool(re.fullmatch(r"[a-z][a-z0-9_]*", part.split("(", 1)[0].strip()))
            )
            for part in namespace_parts
        )
    candidate = namespace_parts[0] if namespace_parts else head_text
    if "(" in candidate and candidate.endswith(")"):
        functor = candidate.split("(", 1)[0].strip()
        return bool(re.fullmatch(r"[a-z][a-z0-9_]*", functor))
    if " " in candidate:
        return False
    return bool(re.fullmatch(r"[a-z][a-z0-9_]*", candidate))


def prolog_title_atom(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like coercing natural-language fragments into symbolic title atoms, helps with deriving a Prolog-safe atom from semantic text.

    Reference to Theory:
        Supports stable identity naming by converting incidental wording into a reusable symbolic surface.

    Example Input Output:
        Input: `prolog_title_atom(text='Force From Mass And Acceleration')`
        Output: 'force_from_mass_and_acceleration'

    Args:
        text: Value for `text` used by `prolog_title_atom`. Expected type: `str`.

    Returns:
        str: Result produced by `prolog_title_atom`.
    """
    token_stream = _learning_core_tokens(text)
    if token_stream:
        return "_".join(token_stream)
    fallback_tokens = re.findall(r"[a-z0-9]+", str(text or "").lower())
    if fallback_tokens:
        return "_".join(fallback_tokens)
    return "semantic_unit"


def prolog_title_segment_display_text(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like preserving a readable semantic title surface while still storing a symbolic Prolog identity, helps with rendering one Prolog namespace segment as human-readable display text.

    Reference to Theory:
        Supports the separation between structural identity and visible semantic descent while preserving ordered determination for human inspection.

    Example Input Output:
        Input: `prolog_title_segment_display_text(text='force_from_mass_and_acceleration(Mass, Acceleration, Force)')`
        Output: 'Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `prolog_title_segment_display_text`. Expected type: `str`.

    Returns:
        str: Result produced by `prolog_title_segment_display_text`.
    """
    normalized = _collapse_ws(str(text or "").strip())
    if not normalized:
        return ""
    if looks_like_prolog_title_identity(normalized):
        head_text, _body_text = split_prolog_clause(normalized)
        namespace_parts = split_prolog_namespace(head_text)
        if namespace_parts:
            normalized = namespace_parts[-1]
    if "(" in normalized and normalized.endswith(")"):
        normalized = normalized.split("(", 1)[0].strip()
    tokens = [part for part in normalized.replace("_", " ").split() if part]
    if not tokens:
        return ""
    return " ".join(token.capitalize() for token in tokens)


def parse_prolog_term(term_text: str, *, variable_prefix: str = "") -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like symbolic head matching and variable-safe clause comparison, helps with converting a Prolog term surface into a structured term tree.

    Reference to Theory:
        Supports the symbolic retrieval layer by turning title surfaces into terms that can actually unify.

    Example Input Output:
        Input: `parse_prolog_term(term_text='add(A, B, C)', variable_prefix='q:')`
        Output: {'kind': 'compound', 'functor': 'add', 'args': [{'kind': 'var', 'text': 'A'}, {'kind': 'var', 'text': 'B'}, {'kind': 'var', 'text': 'C'}]}

    Args:
        term_text: Value for `term_text` used by `parse_prolog_term`. Expected type: `str`.
        variable_prefix: Value for `variable_prefix` used by `parse_prolog_term`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `parse_prolog_term`.
    """
    normalized = _collapse_ws(str(term_text or "").strip())
    if not normalized:
        return {"kind": "atom", "text": ""}
    if re.fullmatch(r"[_A-Z][_A-Za-z0-9]*", normalized):
        return {"kind": "var", "id": f"{variable_prefix}{normalized}", "text": normalized}
    if re.fullmatch(r"-?\d+(?:\.\d+)?", normalized):
        return {"kind": "number", "text": normalized}
    if "(" in normalized and normalized.endswith(")"):
        functor, remainder = normalized.split("(", 1)
        functor = functor.strip()
        if re.fullmatch(r"[a-z][a-z0-9_]*", functor):
            inner = remainder[:-1]
            arguments = [
                parse_prolog_term(argument, variable_prefix=variable_prefix)
                for argument in _split_top_level_text(inner, ",")
                if _collapse_ws(argument)
            ]
            return {"kind": "compound", "functor": functor, "args": arguments, "text": normalized}
    return {"kind": "atom", "text": normalized}


def prolog_term_text(
    term: Mapping[str, Any],
    *,
    canonical_variables: bool = False,
    variable_order: dict[str, str] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like canonicalizing symbolic heads for storage and matching, helps with rendering a parsed Prolog term back into normalized text.

    Reference to Theory:
        Supports reusable identity comparison by making equivalent heads render identically even when variable names differ.

    Example Input Output:
        Input: `prolog_term_text(term={'kind': 'compound', 'functor': 'add', 'args': [{'kind': 'var', 'id': 'q:A', 'text': 'A'}, {'kind': 'var', 'id': 'q:B', 'text': 'B'}, {'kind': 'var', 'id': 'q:C', 'text': 'C'}]}, canonical_variables=True)`
        Output: 'add(V1, V2, V3)'

    Args:
        term: Value for `term` used by `prolog_term_text`. Expected type: `Mapping[str, Any]`.
        canonical_variables: Value for `canonical_variables` used by `prolog_term_text`. Expected type: `bool`. Defaults to `False`.
        variable_order: Value for `variable_order` used by `prolog_term_text`. Expected type: `dict[str, str] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `prolog_term_text`.
    """
    kind = str(term.get("kind", "")).strip()
    if kind == "var":
        if canonical_variables:
            variable_key = str(term.get("id", "")).strip() or str(term.get("text", "")).strip()
            mapping = variable_order if variable_order is not None else {}
            if variable_key not in mapping:
                mapping[variable_key] = f"V{len(mapping) + 1}"
            return mapping[variable_key]
        return str(term.get("text", "")).strip()
    if kind == "compound":
        rendered_args = [
            prolog_term_text(argument, canonical_variables=canonical_variables, variable_order=variable_order)
            for argument in term.get("args", [])
            if isinstance(argument, Mapping)
        ]
        return f"{str(term.get('functor', '')).strip()}({', '.join(rendered_args)})"
    return str(term.get("text", "")).strip()


def prolog_terms_unify(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether a query head can reuse a stored symbolic clause head, helps with checking whether two parsed Prolog terms unify.

    Reference to Theory:
        Supports the symbolic retrieval layer by turning title similarity into actual term-compatibility.

    Example Input Output:
        Input: `prolog_terms_unify(left=parse_prolog_term(term_text='add(2, Y, Z)', variable_prefix='q:'), right=parse_prolog_term(term_text='add(A, B, C)', variable_prefix='c:'))`
        Output: True

    Args:
        left: Value for `left` used by `prolog_terms_unify`. Expected type: `Mapping[str, Any]`.
        right: Value for `right` used by `prolog_terms_unify`. Expected type: `Mapping[str, Any]`.

    Returns:
        bool: Result produced by `prolog_terms_unify`.
    """
    bindings: dict[str, Mapping[str, Any]] = {}

    def resolve(term: Mapping[str, Any]) -> Mapping[str, Any]:
        current = term
        while str(current.get("kind", "")).strip() == "var" and str(current.get("id", "")).strip() in bindings:
            current = bindings[str(current.get("id", "")).strip()]
        return current

    def unify(left_term: Mapping[str, Any], right_term: Mapping[str, Any]) -> bool:
        resolved_left = resolve(left_term)
        resolved_right = resolve(right_term)
        left_kind = str(resolved_left.get("kind", "")).strip()
        right_kind = str(resolved_right.get("kind", "")).strip()
        if left_kind == "var":
            bindings[str(resolved_left.get("id", "")).strip()] = resolved_right
            return True
        if right_kind == "var":
            bindings[str(resolved_right.get("id", "")).strip()] = resolved_left
            return True
        if left_kind != right_kind:
            return False
        if left_kind == "compound":
            if str(resolved_left.get("functor", "")).strip() != str(resolved_right.get("functor", "")).strip():
                return False
            left_args = [item for item in resolved_left.get("args", []) if isinstance(item, Mapping)]
            right_args = [item for item in resolved_right.get("args", []) if isinstance(item, Mapping)]
            if len(left_args) != len(right_args):
                return False
            return all(unify(left_arg, right_arg) for left_arg, right_arg in zip(left_args, right_args))
        return str(resolved_left.get("text", "")).strip() == str(resolved_right.get("text", "")).strip()

    return unify(left, right)


def _collect_prolog_variables(term: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """
    High Level Purpose:
        In circumstances like symbolic clause instantiation and variable-safe substitution, helps with collecting the variable terms that occur inside a parsed Prolog term.

    Reference to Theory:
        Supports clause-body instantiation by identifying which symbolic variables need substitution.

    Example Input Output:
        Input: `_collect_prolog_variables(term=parse_prolog_term(term_text='add(A, B, C)', variable_prefix='s:'))`
        Output: [{'kind': 'var', 'id': 's:A', 'text': 'A'}, {'kind': 'var', 'id': 's:B', 'text': 'B'}, {'kind': 'var', 'id': 's:C', 'text': 'C'}]

    Args:
        term: Value for `term` used by `_collect_prolog_variables`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[Mapping[str, Any]]: Result produced by `_collect_prolog_variables`.
    """
    kind = str(term.get("kind", "")).strip()
    if kind == "var":
        return [term]
    if kind != "compound":
        return []
    variables: list[Mapping[str, Any]] = []
    for argument in term.get("args", []):
        if isinstance(argument, Mapping):
            variables.extend(_collect_prolog_variables(argument))
    return variables


def prolog_unify_bindings(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Mapping[str, Any]] | None:
    """
    High Level Purpose:
        In circumstances like retrieving reusable symbolic clauses by head pattern and carrying substitutions into the body, helps with computing the variable bindings induced by Prolog-style unification.

    Reference to Theory:
        Supports the clause retrieval law by preserving the substitution that makes the query head and stored head compatible.

    Example Input Output:
        Input: `prolog_unify_bindings(left=parse_prolog_term(term_text='add(A, B, C)', variable_prefix='s:'), right=parse_prolog_term(term_text='add(2, X, Y)', variable_prefix='q:'))`
        Output: {'s:A': {'kind': 'number', 'text': '2'}, 's:B': {'kind': 'var', 'id': 'q:X', 'text': 'X'}, 's:C': {'kind': 'var', 'id': 'q:Y', 'text': 'Y'}}

    Args:
        left: Value for `left` used by `prolog_unify_bindings`. Expected type: `Mapping[str, Any]`.
        right: Value for `right` used by `prolog_unify_bindings`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Mapping[str, Any]] | None: Result produced by `prolog_unify_bindings`.
    """
    bindings: dict[str, Mapping[str, Any]] = {}

    def resolve(term: Mapping[str, Any]) -> Mapping[str, Any]:
        current = term
        seen: set[str] = set()
        while str(current.get("kind", "")).strip() == "var":
            variable_id = str(current.get("id", "")).strip()
            if not variable_id or variable_id in seen or variable_id not in bindings:
                break
            seen.add(variable_id)
            current = bindings[variable_id]
        return current

    def unify(left_term: Mapping[str, Any], right_term: Mapping[str, Any]) -> bool:
        resolved_left = resolve(left_term)
        resolved_right = resolve(right_term)
        left_kind = str(resolved_left.get("kind", "")).strip()
        right_kind = str(resolved_right.get("kind", "")).strip()
        if left_kind == "var":
            bindings[str(resolved_left.get("id", "")).strip()] = resolved_right
            return True
        if right_kind == "var":
            bindings[str(resolved_right.get("id", "")).strip()] = resolved_left
            return True
        if left_kind != right_kind:
            return False
        if left_kind == "compound":
            if str(resolved_left.get("functor", "")).strip() != str(resolved_right.get("functor", "")).strip():
                return False
            left_args = [item for item in resolved_left.get("args", []) if isinstance(item, Mapping)]
            right_args = [item for item in resolved_right.get("args", []) if isinstance(item, Mapping)]
            if len(left_args) != len(right_args):
                return False
            return all(unify(left_arg, right_arg) for left_arg, right_arg in zip(left_args, right_args))
        return str(resolved_left.get("text", "")).strip() == str(resolved_right.get("text", "")).strip()

    if not unify(left, right):
        return None
    return bindings


def instantiate_prolog_body_text(
    body_text: str,
    *,
    source_term: Mapping[str, Any],
    query_term: Mapping[str, Any],
) -> str:
    """
    High Level Purpose:
        In circumstances like clause-head retrieval where a matched symbolic head should return an instantiated body, helps with applying the head unifier to a stored Prolog body text.

    Reference to Theory:
        Supports the head-to-body retrieval rule by carrying the same substitution from the symbolic identity into the realization text.

    Example Input Output:
        Input: `instantiate_prolog_body_text(body_text='C is A + B', source_term=parse_prolog_term(term_text='add(A, B, C)', variable_prefix='s:'), query_term=parse_prolog_term(term_text='add(2, X, Y)', variable_prefix='q:'))`
        Output: 'Y is 2 + X'

    Args:
        body_text: Value for `body_text` used by `instantiate_prolog_body_text`. Expected type: `str`.
        source_term: Value for `source_term` used by `instantiate_prolog_body_text`. Expected type: `Mapping[str, Any]`.
        query_term: Value for `query_term` used by `instantiate_prolog_body_text`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `instantiate_prolog_body_text`.
    """
    bindings = prolog_unify_bindings(source_term, query_term)
    if bindings is None:
        return ""

    def resolve(term: Mapping[str, Any]) -> Mapping[str, Any]:
        current = term
        seen: set[str] = set()
        while str(current.get("kind", "")).strip() == "var":
            variable_id = str(current.get("id", "")).strip()
            if not variable_id or variable_id in seen or variable_id not in bindings:
                break
            seen.add(variable_id)
            current = bindings[variable_id]
        return current

    replacements: dict[str, str] = {}
    for variable in _collect_prolog_variables(source_term):
        variable_name = str(variable.get("text", "")).strip()
        if not variable_name:
            continue
        replacements[variable_name] = prolog_term_text(resolve(variable))

    instantiated = str(body_text or "")
    for variable_name, rendered in sorted(replacements.items(), key=lambda item: (-len(item[0]), item[0])):
        instantiated = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(variable_name)}(?![A-Za-z0-9_])",
            rendered,
            instantiated,
        )
    return _collapse_ws(instantiated.strip())


def normalize_prolog_title_identity(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like storing symbolic semantic titles and querying them by structural head shape, helps with normalizing a Prolog-form title identity without changing its logical structure.

    Reference to Theory:
        Supports reusable identity matching by keeping clause-shaped titles canonical but semantically unchanged.

    Example Input Output:
        Input: `normalize_prolog_title_identity(text=' physics : force : add( A , B , C )  :-   C is A + B ')`
        Output: 'physics:force:add(A, B, C) :- C is A + B'

    Args:
        text: Value for `text` used by `normalize_prolog_title_identity`. Expected type: `str`.

    Returns:
        str: Result produced by `normalize_prolog_title_identity`.
    """
    raw = _collapse_ws(str(text or "").strip())
    if not raw:
        return ""
    head_text, body_text = split_prolog_clause(raw)
    namespace_parts = split_prolog_namespace(head_text)
    if not namespace_parts:
        namespace_parts = [head_text]
    normalized_parts = [
        prolog_term_text(parse_prolog_term(part))
        if looks_like_prolog_title_identity(part)
        else _collapse_ws(part)
        for part in namespace_parts
        if _collapse_ws(part)
    ]
    normalized_head = ":".join(normalized_parts)
    normalized_body = _collapse_ws(body_text)
    if normalized_body:
        return f"{normalized_head} :- {normalized_body}"
    return normalized_head


def prolog_title_view(title_identity: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like deriving title-depth structure, canonical keys, and symbolic query signatures from a stored clause-shaped title, helps with building a normalized Prolog title view.

    Reference to Theory:
        Supports ordered determination and reusable identity by exposing namespace segments, canonical heads, and body structure from the symbolic title surface.

    Example Input Output:
        Input: `prolog_title_view(title_identity='physics:force:add(A, B, C) :- C is A + B')`
        Output: {'title_identity': 'physics:force:add(A, B, C) :- C is A + B', 'predicate': 'add', 'arity': 3}

    Args:
        title_identity: Value for `title_identity` used by `prolog_title_view`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `prolog_title_view`.
    """
    normalized_title = normalize_prolog_title_identity(title_identity)
    head_text, body_text = split_prolog_clause(normalized_title)
    namespace_parts = split_prolog_namespace(head_text)
    leaf_text = namespace_parts[-1] if namespace_parts else head_text
    leaf_term = parse_prolog_term(leaf_text)
    variable_order: dict[str, str] = {}
    leaf_canonical = prolog_term_text(
        leaf_term,
        canonical_variables=True,
        variable_order=variable_order,
    )
    qualified_parts = list(namespace_parts[:-1]) + ([leaf_canonical] if leaf_canonical else [])
    prefixes: list[str] = []
    running: list[str] = []
    for part in namespace_parts:
        running.append(part)
        prefixes.append(":".join(running))
    predicate = ""
    arity = 0
    if str(leaf_term.get("kind", "")).strip() == "compound":
        predicate = str(leaf_term.get("functor", "")).strip()
        arity = len([item for item in leaf_term.get("args", []) if isinstance(item, Mapping)])
    elif str(leaf_term.get("kind", "")).strip() == "atom" and re.fullmatch(r"[a-z][a-z0-9_]*", str(leaf_term.get("text", "")).strip()):
        predicate = str(leaf_term.get("text", "")).strip()
        arity = 0
    display_segments = [prolog_title_segment_display_text(part) for part in namespace_parts if prolog_title_segment_display_text(part)]
    display_prefixes: list[str] = []
    running_display: list[str] = []
    for part in display_segments:
        running_display.append(part)
        display_prefixes.append(" / ".join(running_display))
    return {
        "title_identity": normalized_title,
        "head_text": ":".join(namespace_parts) if namespace_parts else head_text,
        "body_text": body_text,
        "segments": namespace_parts or ([head_text] if head_text else []),
        "prefixes": prefixes or ([head_text] if head_text else []),
        "display_segments": display_segments,
        "display_prefixes": display_prefixes,
        "predicate": predicate,
        "arity": arity,
        "leaf_head_text": leaf_text,
        "head_canonical": leaf_canonical,
        "qualified_head_canonical": ":".join(qualified_parts) if qualified_parts else leaf_canonical,
    }


def prolog_title_display_segments(title_identity: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like showing a human-readable semantic path for a stored Prolog identity, helps with deriving readable title-depth segments from a symbolic clause title.

    Reference to Theory:
        Preserves the visible descent of ordered determination while allowing the stored formal identity to remain symbolic.

    Example Input Output:
        Input: `prolog_title_display_segments(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        title_identity: Value for `title_identity` used by `prolog_title_display_segments`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `prolog_title_display_segments`.
    """
    if not looks_like_prolog_title_identity(title_identity):
        return []
    return [str(item).strip() for item in prolog_title_view(title_identity).get("display_segments", []) if str(item).strip()]


def prolog_title_display_text(title_identity: str) -> str:
    """
    High Level Purpose:
        In circumstances like keeping artifact titles readable while still storing a symbolic Prolog identity, helps with rendering a full Prolog-form title as a slash-based display path.

    Reference to Theory:
        Supports a split between formal structural identity and exposed human semantic order without changing the underlying title-depth law.

    Example Input Output:
        Input: `prolog_title_display_text(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration')`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        title_identity: Value for `title_identity` used by `prolog_title_display_text`. Expected type: `str`.

    Returns:
        str: Result produced by `prolog_title_display_text`.
    """
    return " / ".join(prolog_title_display_segments(title_identity))


def _prolog_literal_text(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like synthesizing a structural query head from prompt-supplied values, helps with rendering Python scalars as Prolog-safe literal text.

    Reference to Theory:
        Supports structural retrieval by letting ordinary prompt values be injected into symbolic heads without changing the underlying predicate identity.

    Example Input Output:
        Input: `_prolog_literal_text(value=3)`
        Output: '3'

    Args:
        value: Value for `value` used by `_prolog_literal_text`. Expected type: `Any`.

    Returns:
        str: Result produced by `_prolog_literal_text`.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = _collapse_ws(str(value or "").strip())
    if not text:
        return "null"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return text
    if re.fullmatch(r"[a-z][a-z0-9_]*", text):
        return text
    if re.fullmatch(r"[_A-Z][_A-Za-z0-9]*", text):
        return text
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _prolog_term_scalar_value(term: Mapping[str, Any]) -> Any:
    """
    High Level Purpose:
        In circumstances like turning a matched symbolic query argument into an invocation payload value, helps with converting a parsed Prolog term into a simple Python scalar when possible.

    Reference to Theory:
        Supports the structural retrieval bridge by letting bound query arguments feed downstream execution or clause instantiation.

    Example Input Output:
        Input: `_prolog_term_scalar_value(term=parse_prolog_term(term_text='3'))`
        Output: 3

    Args:
        term: Value for `term` used by `_prolog_term_scalar_value`. Expected type: `Mapping[str, Any]`.

    Returns:
        Any: Result produced by `_prolog_term_scalar_value`.
    """
    kind = str(term.get("kind", "")).strip()
    text = str(term.get("text", "")).strip()
    if kind == "number":
        if "." in text:
            try:
                return float(text)
            except ValueError:
                return text
        try:
            return int(text)
        except ValueError:
            return text
    if kind == "atom":
        lowered = text.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered in {"null", "none"}:
            return None
        if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
            return text[1:-1]
        return text
    return text


def prolog_contract_argument_roles(
    title_identity: str,
    *,
    input_keys: Sequence[str] | None = None,
    output_keys: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like binding natural-language prompt inputs to a stored symbolic head, helps with aligning contract keys to head argument positions.

    Reference to Theory:
        Supports structural reuse by keeping the predicate/head fixed while identifying which argument slots correspond to inputs and outputs.

    Example Input Output:
        Input: `prolog_contract_argument_roles(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)', input_keys=['m', 'a'], output_keys=['F'])`
        Output: [{'index': 0, 'role': 'input', 'contract_key': 'm', 'term_text': 'Mass'}, {'index': 1, 'role': 'input', 'contract_key': 'a', 'term_text': 'Acceleration'}, {'index': 2, 'role': 'output', 'contract_key': 'F', 'term_text': 'Force'}]

    Args:
        title_identity: Value for `title_identity` used by `prolog_contract_argument_roles`. Expected type: `str`.
        input_keys: Value for `input_keys` used by `prolog_contract_argument_roles`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        output_keys: Value for `output_keys` used by `prolog_contract_argument_roles`. Expected type: `Sequence[str] | None`. Defaults to `None`.

    Returns:
        list[dict[str, Any]]: Result produced by `prolog_contract_argument_roles`.
    """
    normalized_title = normalize_prolog_title_identity(title_identity)
    if not looks_like_prolog_title_identity(normalized_title):
        return []
    view = prolog_title_view(normalized_title)
    leaf_term = parse_prolog_term(str(view.get("leaf_head_text", "")).strip(), variable_prefix="h:")
    if str(leaf_term.get("kind", "")).strip() != "compound":
        return []
    args = [item for item in leaf_term.get("args", []) if isinstance(item, Mapping)]
    if not args:
        return []

    normalized_input_keys = [str(item).strip() for item in (input_keys or []) if str(item).strip()]
    normalized_output_keys = [str(item).strip() for item in (output_keys or []) if str(item).strip()]
    arity = len(args)
    roles: list[dict[str, Any]] = []

    def add_role(index: int, role: str, contract_key: str) -> None:
        if index < 0 or index >= arity:
            return
        roles.append(
            {
                "index": index,
                "role": role,
                "contract_key": contract_key,
                "term_text": prolog_term_text(args[index]),
            }
        )

    if normalized_input_keys and normalized_output_keys and len(normalized_input_keys) + len(normalized_output_keys) == arity:
        for index, key in enumerate(normalized_input_keys):
            add_role(index, "input", key)
        output_start = arity - len(normalized_output_keys)
        for offset, key in enumerate(normalized_output_keys):
            add_role(output_start + offset, "output", key)
        return roles

    if normalized_input_keys and len(normalized_input_keys) == arity:
        for index, key in enumerate(normalized_input_keys):
            add_role(index, "input", key)
        return roles

    if normalized_input_keys:
        for index, key in enumerate(normalized_input_keys[:arity]):
            add_role(index, "input", key)
        if normalized_output_keys:
            output_slots = min(len(normalized_output_keys), max(0, arity - len(normalized_input_keys)))
            output_start = arity - output_slots
            for offset, key in enumerate(normalized_output_keys[:output_slots]):
                add_role(output_start + offset, "output", key)
        return roles

    if normalized_output_keys:
        output_slots = min(len(normalized_output_keys), arity)
        output_start = arity - output_slots
        for offset, key in enumerate(normalized_output_keys[:output_slots]):
            add_role(output_start + offset, "output", key)
    return roles


def prolog_contract_alias_map(
    title_identity: str,
    *,
    input_keys: Sequence[str] | None = None,
    output_keys: Sequence[str] | None = None,
) -> dict[str, list[str]]:
    """
    High Level Purpose:
        In circumstances like extracting named values from a normal-text prompt for a symbolic artifact, helps with deriving prompt-side alias candidates from the stored Prolog head.

    Reference to Theory:
        Supports the bridge from ordinary language into structural retrieval by reusing the artifact's own symbolic argument names as natural alias hints.

    Example Input Output:
        Input: `prolog_contract_alias_map(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)', input_keys=['m', 'a'], output_keys=['F'])`
        Output: {'m': ['m', 'Mass', 'mass'], 'a': ['a', 'Acceleration', 'acceleration']}

    Args:
        title_identity: Value for `title_identity` used by `prolog_contract_alias_map`. Expected type: `str`.
        input_keys: Value for `input_keys` used by `prolog_contract_alias_map`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        output_keys: Value for `output_keys` used by `prolog_contract_alias_map`. Expected type: `Sequence[str] | None`. Defaults to `None`.

    Returns:
        dict[str, list[str]]: Result produced by `prolog_contract_alias_map`.
    """
    alias_map: dict[str, list[str]] = {}
    for role in prolog_contract_argument_roles(
        title_identity,
        input_keys=input_keys,
        output_keys=output_keys,
    ):
        if str(role.get("role", "")).strip() != "input":
            continue
        contract_key = str(role.get("contract_key", "")).strip()
        term_text = str(role.get("term_text", "")).strip()
        display_text = prolog_title_segment_display_text(term_text)
        aliases = [
            contract_key,
            contract_key.lower(),
            term_text,
            term_text.lower(),
            display_text,
            display_text.lower(),
            prolog_title_atom(term_text),
            prolog_title_atom(display_text),
            *[token for token in display_text.split() if token],
            *[token.lower() for token in display_text.split() if token],
        ]
        alias_map[contract_key] = _ordered_unique([item for item in aliases if str(item).strip()])
    return alias_map


def synthesize_prolog_query_title_identity(
    title_identity: str,
    *,
    invocation_payload: Mapping[str, Any] | None,
    input_keys: Sequence[str] | None = None,
    output_keys: Sequence[str] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like querying a stored symbolic artifact from a normal-text prompt, helps with synthesizing a concrete Prolog head by injecting prompt values into the artifact's own head shape.

    Reference to Theory:
        Supports structural reuse by treating the stored formal identity as authoritative and only instantiating the argument positions that the prompt actually supplies.

    Example Input Output:
        Input: `synthesize_prolog_query_title_identity(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)', invocation_payload={'m': 3, 'a': 4}, input_keys=['m', 'a'], output_keys=['F'])`
        Output: 'physics:force:force_from_mass_and_acceleration(3, 4, Force)'

    Args:
        title_identity: Value for `title_identity` used by `synthesize_prolog_query_title_identity`. Expected type: `str`.
        invocation_payload: Value for `invocation_payload` used by `synthesize_prolog_query_title_identity`. Expected type: `Mapping[str, Any] | None`.
        input_keys: Value for `input_keys` used by `synthesize_prolog_query_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        output_keys: Value for `output_keys` used by `output_keys`. Expected type: `Sequence[str] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `synthesize_prolog_query_title_identity`.
    """
    if not isinstance(invocation_payload, Mapping) or not invocation_payload:
        return ""
    normalized_title = normalize_prolog_title_identity(title_identity)
    if not looks_like_prolog_title_identity(normalized_title):
        return ""
    view = prolog_title_view(normalized_title)
    leaf_term = parse_prolog_term(str(view.get("leaf_head_text", "")).strip(), variable_prefix="q:")
    if str(leaf_term.get("kind", "")).strip() != "compound":
        return ""

    roles = prolog_contract_argument_roles(
        normalized_title,
        input_keys=input_keys,
        output_keys=output_keys,
    )
    if not roles:
        return ""

    args = [item for item in leaf_term.get("args", []) if isinstance(item, Mapping)]
    bound_by_index: dict[int, str] = {}
    for role in roles:
        if str(role.get("role", "")).strip() != "input":
            continue
        contract_key = str(role.get("contract_key", "")).strip()
        if contract_key not in invocation_payload or invocation_payload.get(contract_key) in (None, "", [], {}):
            continue
        bound_by_index[int(role.get("index", -1))] = _prolog_literal_text(invocation_payload.get(contract_key))
    if not bound_by_index:
        return ""

    rendered_args = [
        bound_by_index.get(index, prolog_term_text(argument))
        for index, argument in enumerate(args)
    ]
    rendered_leaf = f"{str(leaf_term.get('functor', '')).strip()}({', '.join(rendered_args)})"
    namespace_parts = [str(item).strip() for item in view.get("segments", [])[:-1] if str(item).strip()]
    return ":".join([*namespace_parts, rendered_leaf]) if namespace_parts else rendered_leaf


def derive_prolog_query_invocation_payload(
    title_identity: str,
    query_title_identity: str,
    *,
    input_keys: Sequence[str] | None = None,
    output_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like executing a Prolog-backed artifact from an already symbolic query head, helps with deriving the input payload directly from the query head arguments.

    Reference to Theory:
        Supports structural reuse by reusing the same argument positions that define the stored formal identity instead of reparsing the query as ordinary text.

    Example Input Output:
        Input: `derive_prolog_query_invocation_payload(title_identity='physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)', query_title_identity='physics:force:force_from_mass_and_acceleration(3, 4, Force)', input_keys=['m', 'a'], output_keys=['F'])`
        Output: {'m': 3, 'a': 4}

    Args:
        title_identity: Value for `title_identity` used by `derive_prolog_query_invocation_payload`. Expected type: `str`.
        query_title_identity: Value for `query_title_identity` used by `derive_prolog_query_invocation_payload`. Expected type: `str`.
        input_keys: Value for `input_keys` used by `input_keys`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        output_keys: Value for `output_keys` used by `output_keys`. Expected type: `Sequence[str] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `derive_prolog_query_invocation_payload`.
    """
    normalized_title = normalize_prolog_title_identity(title_identity)
    normalized_query = normalize_prolog_title_identity(query_title_identity)
    if not looks_like_prolog_title_identity(normalized_title) or not looks_like_prolog_title_identity(normalized_query):
        return {}
    if prolog_title_match_score(normalized_query, normalized_title) < 95:
        return {}

    title_view = prolog_title_view(normalized_title)
    query_view = prolog_title_view(normalized_query)
    title_leaf = parse_prolog_term(str(title_view.get("leaf_head_text", "")).strip(), variable_prefix="s:")
    query_leaf = parse_prolog_term(str(query_view.get("leaf_head_text", "")).strip(), variable_prefix="q:")
    if not prolog_terms_unify(title_leaf, query_leaf):
        return {}
    query_args = [item for item in query_leaf.get("args", []) if isinstance(item, Mapping)]
    payload: dict[str, Any] = {}
    for role in prolog_contract_argument_roles(
        normalized_title,
        input_keys=input_keys,
        output_keys=output_keys,
    ):
        if str(role.get("role", "")).strip() != "input":
            continue
        index = int(role.get("index", -1))
        contract_key = str(role.get("contract_key", "")).strip()
        if index < 0 or index >= len(query_args) or not contract_key:
            continue
        query_arg = query_args[index]
        if str(query_arg.get("kind", "")).strip() == "var":
            continue
        payload[contract_key] = _prolog_term_scalar_value(query_arg)
    return payload


def prolog_title_match_score(query_title: str, candidate_title: str) -> int:
    """
    High Level Purpose:
        In circumstances like querying stored artifacts by symbolic semantic head rather than loose lexical overlap, helps with assigning a structural match score between two Prolog-form titles.

    Reference to Theory:
        Supports head-pattern retrieval by preferring exact canonical head matches, then unifiable heads, then weaker predicate-family compatibility.

    Example Input Output:
        Input: `prolog_title_match_score(query_title='physics:force:add(2, Y, Z)', candidate_title='physics:force:add(A, B, C) :- C is A + B')`
        Output: 98

    Args:
        query_title: Value for `query_title` used by `prolog_title_match_score`. Expected type: `str`.
        candidate_title: Value for `candidate_title` used by `prolog_title_match_score`. Expected type: `str`.

    Returns:
        int: Result produced by `prolog_title_match_score`.
    """
    if not looks_like_prolog_title_identity(query_title) or not looks_like_prolog_title_identity(candidate_title):
        return 0
    query_view = prolog_title_view(query_title)
    candidate_view = prolog_title_view(candidate_title)
    query_key = str(query_view.get("qualified_head_canonical", "")).strip().casefold()
    candidate_key = str(candidate_view.get("qualified_head_canonical", "")).strip().casefold()
    if query_key and query_key == candidate_key:
        return 100
    query_leaf = parse_prolog_term(str(query_view.get("leaf_head_text", "")).strip(), variable_prefix="q:")
    candidate_leaf = parse_prolog_term(str(candidate_view.get("leaf_head_text", "")).strip(), variable_prefix="c:")
    query_namespace = [str(item).strip().casefold() for item in query_view.get("segments", [])[:-1] if str(item).strip()]
    candidate_namespace = [str(item).strip().casefold() for item in candidate_view.get("segments", [])[:-1] if str(item).strip()]
    shared_namespace_depth = 0
    for query_part, candidate_part in zip(query_namespace, candidate_namespace):
        if query_part != candidate_part:
            break
        shared_namespace_depth += 1
    if prolog_terms_unify(query_leaf, candidate_leaf):
        if query_namespace and query_namespace == candidate_namespace:
            return 99
        if shared_namespace_depth > 0:
            return 96 + min(shared_namespace_depth, 2)
        return 95
    if (
        str(query_view.get("predicate", "")).strip()
        and str(query_view.get("predicate", "")).strip() == str(candidate_view.get("predicate", "")).strip()
        and int(query_view.get("arity", 0)) == int(candidate_view.get("arity", 0))
    ):
        if shared_namespace_depth > 0:
            return 92 + min(shared_namespace_depth, 2)
        return 90
    return 0


def prolog_title_query_variants(title_identity: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like candidate retrieval for symbolic clause reuse, helps with expanding one Prolog-form semantic title into the concrete query variants most likely to retrieve structurally compatible stored artifacts.

    Reference to Theory:
        Supports the two-stage retrieval design by giving the store several index-friendly symbolic surfaces before symbolic verification happens in memory.

    Example Input Output:
        Input: `prolog_title_query_variants(title_identity='math:add:add(2, X, Y)')`
        Output: ['math:add:add(2, X, Y)', 'math:add:add(V1, V2, V3)', 'add(V1, V2, V3)', 'add']

    Args:
        title_identity: Value for `title_identity` used by `prolog_title_query_variants`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `prolog_title_query_variants`.
    """
    normalized_title = normalize_prolog_title_identity(title_identity)
    if not looks_like_prolog_title_identity(normalized_title):
        return [normalized_title] if normalized_title else []
    view = prolog_title_view(normalized_title)
    query_variants = [
        normalized_title,
        str(view.get("head_text", "")).strip(),
        str(view.get("qualified_head_canonical", "")).strip(),
        str(view.get("head_canonical", "")).strip(),
        str(view.get("predicate", "")).strip(),
    ]
    return _ordered_unique([item for item in query_variants if str(item).strip()])


def compose_prolog_semantic_title_identity(
    *,
    broader_category: str = "",
    current_identity: str = "",
    downward_decomposition: Sequence[str] | None = None,
    fallback_title: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like anchoring a newly inferred symbolic head under its broader semantic ground, helps with composing a Prolog-form title identity from broader qualifiers and a determinate head.

    Reference to Theory:
        Supports ordered determination by preserving broad qualifiers before the resolved symbolic head and optional clause body.

    Example Input Output:
        Input: `compose_prolog_semantic_title_identity(broader_category='physics:force', current_identity='add(Mass, Acceleration, Force) :- Force is Mass * Acceleration', downward_decomposition=['mass_input(Mass)'], fallback_title='force')`
        Output: 'physics:force:add(Mass, Acceleration, Force) :- Force is Mass * Acceleration'

    Args:
        broader_category: Value for `broader_category` used by `compose_prolog_semantic_title_identity`. Expected type: `str`. Defaults to `''`.
        current_identity: Value for `current_identity` used by `compose_prolog_semantic_title_identity`. Expected type: `str`. Defaults to `''`.
        downward_decomposition: Value for `downward_decomposition` used by `compose_prolog_semantic_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        fallback_title: Value for `fallback_title` used by `compose_prolog_semantic_title_identity`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `compose_prolog_semantic_title_identity`.
    """
    base_sources = [str(item).strip() for item in (current_identity, fallback_title) if str(item).strip()]
    if not base_sources:
        return ""
    base_title = normalize_prolog_title_identity(base_sources[0]) if looks_like_prolog_title_identity(base_sources[0]) else _collapse_ws(base_sources[0])
    current_head, current_body = split_prolog_clause(base_title)

    def namespace_parts_for_title(value: str) -> list[str]:
        normalized_value = _collapse_ws(str(value or "").strip())
        if not normalized_value:
            return []
        if looks_like_prolog_title_identity(normalized_value):
            head_text, _ = split_prolog_clause(normalized_value)
            return split_prolog_namespace(normalize_prolog_title_identity(head_text))
        if "/" in normalized_value:
            return [prolog_title_atom(part) for part in _split_title_segments(normalized_value) if part]
        return [prolog_title_atom(normalized_value)]

    broader_parts = namespace_parts_for_title(broader_category)
    current_parts = namespace_parts_for_title(current_head or base_title)
    if downward_decomposition:
        current_parts.extend(
            namespace_parts_for_title(str(item).strip())[0]
            for item in downward_decomposition
            if str(item).strip() and namespace_parts_for_title(str(item).strip())
        )
    if broader_parts and current_parts[: len(broader_parts)] == broader_parts:
        composed_parts = current_parts
    else:
        composed_parts = broader_parts + current_parts
    composed_head = ":".join(part for part in composed_parts if part)
    if current_body:
        return f"{composed_head} :- {current_body}"
    return composed_head


def synthesize_prolog_formal_title_identity(
    *,
    display_title: str,
    input_keys: Sequence[str] | None = None,
    output_keys: Sequence[str] | None = None,
    compute_expression: str = "",
    output_field: str = "",
    parameter_aliases: Mapping[str, Sequence[str]] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like Prolog-mode artifact learning where the visible title stays readable but the stored structural identity should still be symbolic, helps with deriving a deterministic Prolog-form formal title identity from the display title and contract shape.

    Reference to Theory:
        Supports the split between visible title-depth and structural identity by turning the learned semantic path and body contract into a reusable symbolic head, with a clause body when an executable expression is known.

    Example Input Output:
        Input: `synthesize_prolog_formal_title_identity(display_title=\"Newton's Laws of Motion / Force From Mass And Acceleration\", input_keys=['m', 'a'], output_keys=['F'], compute_expression='m * a', output_field='F', parameter_aliases={'m': ['mass'], 'a': ['acceleration'], 'F': ['force']})`
        Output: 'newton_s_laws_of_motion:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration'

    Args:
        display_title: Value for `display_title` used by `synthesize_prolog_formal_title_identity`. Expected type: `str`.
        input_keys: Value for `input_keys` used by `synthesize_prolog_formal_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        output_keys: Value for `output_keys` used by `synthesize_prolog_formal_title_identity`. Expected type: `Sequence[str] | None`. Defaults to `None`.
        compute_expression: Value for `compute_expression` used by `synthesize_prolog_formal_title_identity`. Expected type: `str`. Defaults to `''`.
        output_field: Value for `output_field` used by `synthesize_prolog_formal_title_identity`. Expected type: `str`. Defaults to `''`.
        parameter_aliases: Value for `parameter_aliases` used by `synthesize_prolog_formal_title_identity`. Expected type: `Mapping[str, Sequence[str]] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `synthesize_prolog_formal_title_identity`.
    """
    segments = _split_title_segments(display_title)
    if not segments:
        return ""

    namespace_atoms = [prolog_title_atom(segment) for segment in segments if prolog_title_atom(segment)]
    if not namespace_atoms:
        return ""

    functor = namespace_atoms[-1]
    qualifier_atoms = namespace_atoms[:-1]
    normalized_input_keys = [str(item).strip() for item in (input_keys or []) if str(item).strip()]
    normalized_output_keys = [str(item).strip() for item in (output_keys or []) if str(item).strip()]
    if output_field and output_field not in normalized_output_keys:
        normalized_output_keys = [*normalized_output_keys, output_field]

    used_names: set[str] = set()

    def choose_variable_name(contract_key: str, role: str) -> str:
        candidates: list[str] = []
        if isinstance(parameter_aliases, Mapping):
            aliases = parameter_aliases.get(contract_key, [])
            if isinstance(aliases, Sequence) and not isinstance(aliases, (str, bytes)):
                candidates.extend(str(alias).strip() for alias in aliases if str(alias).strip())
        candidates.extend([contract_key, prolog_title_segment_display_text(contract_key)])
        for candidate in candidates:
            tokens = [token for token in re.findall(r"[A-Za-z0-9]+", candidate) if token]
            if not tokens:
                continue
            if len(tokens) == 1 and len(tokens[0]) == 1:
                base_name = f"{'Result' if role == 'output' else 'Input'}{tokens[0].upper()}"
            else:
                base_name = "".join(token.capitalize() for token in tokens)
            if not base_name:
                continue
            if not base_name[0].isalpha():
                base_name = f"{'Result' if role == 'output' else 'Value'}{base_name}"
            if not base_name[0].isupper():
                base_name = base_name[0].upper() + base_name[1:]
            final_name = base_name
            suffix = 2
            while final_name in used_names:
                final_name = f"{base_name}{suffix}"
                suffix += 1
            used_names.add(final_name)
            return final_name
        fallback = f"{'Result' if role == 'output' else 'Value'}{len(used_names) + 1}"
        used_names.add(fallback)
        return fallback

    input_variables = [choose_variable_name(key, "input") for key in normalized_input_keys]
    output_variables = [choose_variable_name(key, "output") for key in normalized_output_keys[:1]]
    if input_variables or output_variables:
        head_text = f"{functor}({', '.join([*input_variables, *output_variables])})"
    else:
        head_text = functor

    qualified_head = ":".join([*qualifier_atoms, head_text]) if qualifier_atoms else head_text
    body_text = _collapse_ws(str(compute_expression or "").strip())
    if body_text and output_variables:
        rendered_expression = body_text
        replacement_pairs = [
            (str(key).strip(), variable)
            for key, variable in zip(normalized_input_keys, input_variables)
            if str(key).strip()
        ]
        replacement_pairs.extend(
            (str(key).strip(), variable)
            for key, variable in zip(normalized_output_keys[:1], output_variables)
            if str(key).strip()
        )
        for key, variable in sorted(replacement_pairs, key=lambda item: (-len(item[0]), item[0])):
            rendered_expression = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(key)}(?![A-Za-z0-9_])",
                variable,
                rendered_expression,
            )
        return normalize_prolog_title_identity(f"{qualified_head} :- {output_variables[0]} is {rendered_expression}")
    return normalize_prolog_title_identity(qualified_head)
