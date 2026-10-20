# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from applied_theory_types import (
    BOUNDARY_OUTPUT_TERMS,
    BOUNDARY_WRITE_TERMS,
    PYTHON_ARTIFACT_REPRESENTATIONS,
    TEMPLATE_BEARING_ARTIFACT_TYPES,
    ArtifactRepresentation,
    ArtifactType,
    BoundaryShapeTerm,
)
from normalization_primitives import (
    boundary_shape_values,
    normalize_artifact_representation,
    normalize_artifact_type,
    normalize_boundary_shape,
    normalize_function_bit,
)


def _collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like boundary-shape inference from freeform semantic text, helps with collapsing repeated whitespace so text heuristics behave deterministically.

    Reference to Theory:
        Supports the artifact/boundary rules that keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `_collapse_ws(text='Compute   force\\nfrom mass.')`
        Output: 'Compute force from mass.'

    Args:
        text: Value for `text` used by `_collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `_collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text or "")).strip()


BOUNDARY_REFERENCE_HINTS = (
    "path",
    "file",
    "filepath",
    "uri",
    "url",
    "ref",
    "reference",
    "handle",
    "pointer",
    "record_id",
    "resource_id",
)

BOUNDARY_READ_HINTS = (
    "read",
    "load",
    "fetch",
    "query",
    "lookup",
    "look up",
    "retrieve",
    "inspect",
    "open",
    "search",
)

BOUNDARY_WRITE_HINTS = (
    "write",
    "save",
    "store",
    "persist",
    "send",
    "email",
    "post",
    "upload",
    "update",
    "delete",
    "create",
    "notify",
)


def is_template_bearing_artifact_type(artifact_type: ArtifactType | str) -> bool:
    """
    High Level Purpose:
        In circumstances like artifact import, persistence, and reuse scoring, helps with deciding whether an artifact type should be treated as template-bearing.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `is_template_bearing_artifact_type(artifact_type='ability')`
        Output: True

    Args:
        artifact_type: Value for `artifact_type` used by `is_template_bearing_artifact_type`. Expected type: `ArtifactType | str`.

    Returns:
        bool: Result produced by `is_template_bearing_artifact_type`.
    """
    return normalize_artifact_type(artifact_type, default="knowledge") in TEMPLATE_BEARING_ARTIFACT_TYPES


def is_python_artifact_representation(representation: ArtifactRepresentation | str) -> bool:
    """
    High Level Purpose:
        In circumstances like ability import, execution routing, and function-bit inference, helps with deciding whether an artifact representation is Python-backed.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `is_python_artifact_representation(representation='python_script')`
        Output: True

    Args:
        representation: Value for `representation` used by `is_python_artifact_representation`. Expected type: `ArtifactRepresentation | str`.

    Returns:
        bool: Result produced by `is_python_artifact_representation`.
    """
    return normalize_artifact_representation(representation) in PYTHON_ARTIFACT_REPRESENTATIONS


def _boundary_shape_contract_has_reference(contract: Mapping[str, Any]) -> bool:
    """
    High Level Purpose:
        In circumstances like inferring whether an artifact reads or writes by reference, helps with checking contract fields for reference-bearing hints.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `_boundary_shape_contract_has_reference(contract={'input_path': 'dataset.csv'})`
        Output: True

    Args:
        contract: Value for `contract` used by `_boundary_shape_contract_has_reference`. Expected type: `Mapping[str, Any]`.

    Returns:
        bool: Result produced by `_boundary_shape_contract_has_reference`.
    """
    for key, value in contract.items():
        combined = f"{key} {value}".casefold()
        if any(hint in combined for hint in BOUNDARY_REFERENCE_HINTS):
            return True
    return False


def _boundary_shape_text_has_reference(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like freeform prompt or title analysis for boundary-shape inference, helps with deciding whether the text points to references rather than inline values.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `_boundary_shape_text_has_reference(text='Read the file path and compute the checksum.')`
        Output: True

    Args:
        text: Value for `text` used by `_boundary_shape_text_has_reference`. Expected type: `str`.

    Returns:
        bool: Result produced by `_boundary_shape_text_has_reference`.
    """
    lowered = str(text).casefold()
    return any(hint in lowered for hint in BOUNDARY_REFERENCE_HINTS)


def _boundary_shape_text_has_any(text: str, hints: Iterable[str]) -> bool:
    """
    High Level Purpose:
        In circumstances like boundary-shape inference from descriptive text, helps with checking whether any operational hint is present in the text.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `_boundary_shape_text_has_any(text='Fetch the record and update the output.', hints=['fetch', 'update'])`
        Output: True

    Args:
        text: Value for `text` used by `_boundary_shape_text_has_any`. Expected type: `str`.
        hints: Value for `hints` used by `_boundary_shape_text_has_any`. Expected type: `Iterable[str]`.

    Returns:
        bool: Result produced by `_boundary_shape_text_has_any`.
    """
    lowered = str(text).casefold()
    return any(hint in lowered for hint in hints)


def infer_not_boundary_shape_from_semantic_text(semantic_unit: str) -> tuple[BoundaryShapeTerm, ...]:
    """
    High Level Purpose:
        In circumstances like bootstrapping a new `Not` node from a natural-language prompt, helps with inferring the node's default boundary shape from the semantic text alone.

    Reference to Theory:
        Supports title-depth and decomposition by giving each semantic unit a body-side boundary contract coherent with what the text appears to require.

    Example Input Output:
        Input: `infer_not_boundary_shape_from_semantic_text(semantic_unit='Read the referenced dataset and return the average value.')`
        Output: (BoundaryShapeTerm.READ_REFERENCE, BoundaryShapeTerm.OUTPUT_VALUE)

    Args:
        semantic_unit: Value for `semantic_unit` used by `infer_not_boundary_shape_from_semantic_text`. Expected type: `str`.

    Returns:
        tuple[BoundaryShapeTerm, ...]: Result produced by `infer_not_boundary_shape_from_semantic_text`.
    """
    semantic_text = _collapse_ws(str(semantic_unit or "").strip())
    if not semantic_text:
        return normalize_boundary_shape(
            (BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE)
        )

    assignment_matches = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", semantic_text)
    has_reference_assignment = any(
        _boundary_shape_text_has_reference(match) for match in assignment_matches
    )
    has_value_assignment = bool(assignment_matches)
    terms: list[BoundaryShapeTerm] = []

    def add(term: BoundaryShapeTerm) -> None:
        """
        High Level Purpose:
            In circumstances like accumulating inferred boundary atoms, helps with appending a boundary term once without duplication.

        Reference to Theory:
            Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

        Example Input Output:
            Input: `add(term=BoundaryShapeTerm.OUTPUT_VALUE)`
            Output: None

        Args:
            term: Value for `term` used by `add`. Expected type: `BoundaryShapeTerm`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if term not in terms:
            terms.append(term)

    if has_reference_assignment:
        add(BoundaryShapeTerm.INPUT_REFERENCE)
    elif has_value_assignment:
        add(BoundaryShapeTerm.INPUT_VALUE)

    if _boundary_shape_text_has_any(semantic_text, BOUNDARY_READ_HINTS):
        add(
            BoundaryShapeTerm.READ_REFERENCE
            if _boundary_shape_text_has_reference(semantic_text)
            else BoundaryShapeTerm.READ_VALUE
        )
        if not has_value_assignment and not has_reference_assignment:
            add(
                BoundaryShapeTerm.INPUT_REFERENCE
                if _boundary_shape_text_has_reference(semantic_text)
                else BoundaryShapeTerm.INPUT_VALUE
            )

    if _boundary_shape_text_has_any(semantic_text, BOUNDARY_WRITE_HINTS):
        add(
            BoundaryShapeTerm.WRITE_REFERENCE
            if _boundary_shape_text_has_reference(semantic_text)
            else BoundaryShapeTerm.WRITE_VALUE
        )
        if not has_value_assignment and not has_reference_assignment:
            add(
                BoundaryShapeTerm.INPUT_REFERENCE
                if _boundary_shape_text_has_reference(semantic_text)
                else BoundaryShapeTerm.INPUT_VALUE
            )

    if "?" in semantic_text or not any(term in BOUNDARY_OUTPUT_TERMS for term in terms):
        add(BoundaryShapeTerm.OUTPUT_VALUE)

    if not terms:
        terms = [BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE]

    return tuple(terms)


def infer_artifact_boundary_shape(
    *,
    artifact_type: Any,
    representation: Any,
    content: Mapping[str, Any] | None,
    explicit: Any = None,
    title: str = "",
    scope: str = "",
    function_bit: Any = None,
) -> tuple[BoundaryShapeTerm, ...]:
    """
    High Level Purpose:
        In circumstances like artifact import, normalization, and persistence, helps with inferring the artifact's boundary shape from its contracts, representation, and descriptive text.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `infer_artifact_boundary_shape(artifact_type='ability', representation='python_script', content={'input_contract': {'mass': 'number', 'acceleration': 'number'}, 'output_contract': {'force': 'number'}}, title='Force from mass and acceleration')`
        Output: (BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE)

    Args:
        artifact_type: Value for `artifact_type` used by `infer_artifact_boundary_shape`. Expected type: `Any`.
        representation: Value for `representation` used by `infer_artifact_boundary_shape`. Expected type: `Any`.
        content: Value for `content` used by `infer_artifact_boundary_shape`. Expected type: `Mapping[str, Any] | None`.
        explicit: Value for `explicit` used by `infer_artifact_boundary_shape`. Expected type: `Any`. Defaults to `None`.
        title: Value for `title` used by `infer_artifact_boundary_shape`. Expected type: `str`. Defaults to `''`.
        scope: Value for `scope` used by `infer_artifact_boundary_shape`. Expected type: `str`. Defaults to `''`.
        function_bit: Value for `function_bit` used by `infer_artifact_boundary_shape`. Expected type: `Any`. Defaults to `None`.

    Returns:
        tuple[BoundaryShapeTerm, ...]: Result produced by `infer_artifact_boundary_shape`.
    """
    explicit_shape = normalize_boundary_shape(explicit, default=())
    if explicit_shape:
        return explicit_shape

    normalized_artifact_type = normalize_artifact_type(artifact_type, default="knowledge")
    normalized_representation = normalize_artifact_representation(
        representation,
        artifact_type=normalized_artifact_type,
        default="json",
    )
    runtime_function_bit = normalize_function_bit(
        function_bit
        if function_bit not in (None, "")
        else infer_function_bit(
            artifact_type=normalized_artifact_type,
            representation=normalized_representation,
            content=content or {},
        )
    )
    artifact_content = dict(content or {})
    descriptive_text = _collapse_ws(
        " ".join(
            [
                str(title or "").strip(),
                str(scope or "").strip(),
                str(artifact_content.get("question", "")).strip(),
                str(artifact_content.get("answer", "")).strip(),
                str(artifact_content.get("affordance", "")).strip(),
                str(artifact_content.get("input_form", "")).strip(),
                str(artifact_content.get("output_form", "")).strip(),
                " ".join(str(item).strip() for item in artifact_content.get("aliases", []) if str(item).strip())
                if isinstance(artifact_content.get("aliases", []), list)
                else "",
            ]
        )
    )
    operational_text = _collapse_ws(
        " ".join(
            [
                str(title or "").strip(),
                str(scope or "").strip(),
                str(artifact_content.get("affordance", "")).strip(),
                str(artifact_content.get("input_form", "")).strip(),
                str(artifact_content.get("output_form", "")).strip(),
                str(artifact_content.get("entrypoint", "")).strip(),
                str(artifact_content.get("script_language", "")).strip(),
                " ".join(str(item).strip() for item in artifact_content.get("aliases", []) if str(item).strip())
                if isinstance(artifact_content.get("aliases", []), list)
                else "",
            ]
        )
    )
    input_contract = artifact_content.get("input_contract", {})
    output_contract = artifact_content.get("output_contract", {})
    terms: list[BoundaryShapeTerm] = []

    def add(term: BoundaryShapeTerm) -> None:
        """
        High Level Purpose:
            In circumstances like accumulating an inferred artifact boundary, helps with appending a term once without duplication.

        Reference to Theory:
            Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

        Example Input Output:
            Input: `add(term=BoundaryShapeTerm.INPUT_VALUE)`
            Output: None

        Args:
            term: Value for `term` used by `add`. Expected type: `BoundaryShapeTerm`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if term not in terms:
            terms.append(term)

    if isinstance(input_contract, Mapping) and input_contract:
        add(
            BoundaryShapeTerm.INPUT_REFERENCE
            if _boundary_shape_contract_has_reference(input_contract)
            else BoundaryShapeTerm.INPUT_VALUE
        )
    elif normalized_artifact_type == ArtifactType.CAPABILITY.value and str(artifact_content.get("input_form", "")).strip():
        add(
            BoundaryShapeTerm.INPUT_REFERENCE
            if _boundary_shape_text_has_reference(str(artifact_content.get("input_form", "")))
            else BoundaryShapeTerm.INPUT_VALUE
        )

    if normalized_artifact_type in {ArtifactType.ABILITY.value, ArtifactType.CAPABILITY.value} or runtime_function_bit == 1:
        if _boundary_shape_text_has_any(operational_text or descriptive_text, BOUNDARY_READ_HINTS):
            add(
                BoundaryShapeTerm.READ_REFERENCE
                if _boundary_shape_text_has_reference(operational_text or descriptive_text)
                else BoundaryShapeTerm.READ_VALUE
            )

        if _boundary_shape_text_has_any(operational_text or descriptive_text, BOUNDARY_WRITE_HINTS):
            add(
                BoundaryShapeTerm.WRITE_REFERENCE
                if _boundary_shape_text_has_reference(operational_text or descriptive_text)
                else BoundaryShapeTerm.WRITE_VALUE
            )

    if isinstance(output_contract, Mapping) and output_contract:
        add(
            BoundaryShapeTerm.OUTPUT_REFERENCE
            if _boundary_shape_contract_has_reference(output_contract)
            else BoundaryShapeTerm.OUTPUT_VALUE
        )
    elif normalized_artifact_type == ArtifactType.CAPABILITY.value and str(artifact_content.get("output_form", "")).strip():
        add(
            BoundaryShapeTerm.OUTPUT_REFERENCE
            if _boundary_shape_text_has_reference(str(artifact_content.get("output_form", "")))
            else BoundaryShapeTerm.OUTPUT_VALUE
        )
    elif normalized_artifact_type == ArtifactType.KNOWLEDGE.value or str(artifact_content.get("answer", "")).strip():
        add(BoundaryShapeTerm.OUTPUT_VALUE)
    elif runtime_function_bit == 1 and not any(term in BOUNDARY_WRITE_TERMS for term in terms):
        add(BoundaryShapeTerm.OUTPUT_VALUE)

    if not terms:
        terms = [BoundaryShapeTerm.OUTPUT_VALUE]

    return tuple(terms)


def boundary_shape_term_rows(
    artifact_id: str,
    boundary_shape: Iterable[BoundaryShapeTerm | str],
) -> list[tuple[str, int, str]]:
    """
    High Level Purpose:
        In circumstances like persisting boundary-shape atoms into SQLite, helps with turning one normalized boundary shape into indexed storage rows.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `boundary_shape_term_rows(artifact_id='artifact-force', boundary_shape=['a*', 'd*'])`
        Output: [('artifact-force', 0, 'a*'), ('artifact-force', 1, 'd*')]

    Args:
        artifact_id: Value for `artifact_id` used by `boundary_shape_term_rows`. Expected type: `str`.
        boundary_shape: Value for `boundary_shape` used by `boundary_shape_term_rows`. Expected type: `Iterable[BoundaryShapeTerm | str]`.

    Returns:
        list[tuple[str, int, str]]: Result produced by `boundary_shape_term_rows`.
    """
    rows: list[tuple[str, int, str]] = []
    for index, term in enumerate(boundary_shape_values(boundary_shape, default=())):
        rows.append((artifact_id, index, term))
    return rows


def boundary_shape_rank(
    current_boundary_shape: Iterable[BoundaryShapeTerm | str] | None,
    artifact_boundary_shape: Iterable[BoundaryShapeTerm | str] | None,
) -> tuple[int, int, int]:
    """
    High Level Purpose:
        In circumstances like ranking reusable artifacts against the current request boundary, helps with penalizing extra or missing boundary terms.

    Reference to Theory:
        Supports the artifact/boundary rules used to keep body constitution coherent with semantic identity under the applied theory.

    Example Input Output:
        Input: `boundary_shape_rank(current_boundary_shape=['a*', 'd*'], artifact_boundary_shape=['a*', 'c*', 'd*'])`
        Output: (0, 1, 0)

    Args:
        current_boundary_shape: Value for `current_boundary_shape` used by `boundary_shape_rank`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`.
        artifact_boundary_shape: Value for `artifact_boundary_shape` used by `boundary_shape_rank`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`.

    Returns:
        tuple[int, int, int]: Result produced by `boundary_shape_rank`.
    """
    current_terms = set(boundary_shape_values(current_boundary_shape, default=()))
    artifact_terms = set(boundary_shape_values(artifact_boundary_shape, default=()))
    if not current_terms or not artifact_terms:
        return (0, 0, 0)
    extra_terms = artifact_terms - current_terms
    missing_terms = current_terms - artifact_terms
    write_mismatch = 1 if extra_terms.intersection({term.value for term in BOUNDARY_WRITE_TERMS}) else 0
    return (write_mismatch, len(extra_terms), len(missing_terms))


def default_boundary_shape_for_node(
    *,
    semantic_unit: str = "",
    parent_boundary_shape: Iterable[BoundaryShapeTerm | str] | None = None,
) -> tuple[BoundaryShapeTerm, ...]:
    """
    High Level Purpose:
        In circumstances like creating a new semantic node, helps with choosing the node's default boundary shape from either the parent contract or the semantic text.

    Reference to Theory:
        Supports title-depth and decomposition by keeping the node's body-side boundary consistent with its semantic role.

    Example Input Output:
        Input: `default_boundary_shape_for_node(semantic_unit='Read the referenced dataset and summarize it.', parent_boundary_shape=None)`
        Output: (BoundaryShapeTerm.READ_REFERENCE, BoundaryShapeTerm.OUTPUT_VALUE)

    Args:
        semantic_unit: Value for `semantic_unit` used by `default_boundary_shape_for_node`. Expected type: `str`. Defaults to `''`.
        parent_boundary_shape: Value for `parent_boundary_shape` used by `default_boundary_shape_for_node`. Expected type: `Iterable[BoundaryShapeTerm | str] | None`. Defaults to `None`.

    Returns:
        tuple[BoundaryShapeTerm, ...]: Result produced by `default_boundary_shape_for_node`.
    """
    if parent_boundary_shape:
        return normalize_boundary_shape(parent_boundary_shape)
    return infer_not_boundary_shape_from_semantic_text(semantic_unit)


def infer_function_bit(
    *,
    artifact_type: str,
    representation: str,
    content: Mapping[str, Any] | None = None,
    explicit: Any = None,
) -> int:
    """
    High Level Purpose:
        In circumstances like artifact import, normalization, and persistence, helps with deciding whether an artifact should be treated as function-bearing.

    Reference to Theory:
        Supports semantic reuse and composition by distinguishing executable or callable artifacts from passive knowledge artifacts under the applied theory.

    Example Input Output:
        Input: `infer_function_bit(artifact_type='ability', representation='python_script', content={'entrypoint': 'run'})`
        Output: 1

    Args:
        artifact_type: Value for `artifact_type` used by `infer_function_bit`. Expected type: `str`.
        representation: Value for `representation` used by `infer_function_bit`. Expected type: `str`.
        content: Value for `content` used by `infer_function_bit`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        explicit: Value for `explicit` used by `infer_function_bit`. Expected type: `Any`. Defaults to `None`.

    Returns:
        int: Result produced by `infer_function_bit`.
    """
    if explicit is not None and str(explicit).strip() != "":
        return normalize_function_bit(explicit)
    normalized_type = normalize_artifact_type(artifact_type, default="knowledge")
    normalized_representation = normalize_artifact_representation(representation, artifact_type=normalized_type)
    payload = content if isinstance(content, Mapping) else {}
    if normalized_type == "ability" or is_python_artifact_representation(normalized_representation):
        return 1
    for key in (
        "requires_external_function",
        "requires_function_call",
        "callable_name",
        "tool_name",
        "command",
        "entrypoint",
        "python_script",
        "function_name",
        "module_name",
    ):
        value = payload.get(key)
        if value not in (None, "", [], {}, False):
            return 1
    return 0
