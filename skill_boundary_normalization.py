# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from applied_theory_types import Artifact, BoundaryShapeTerm
from semantic_text import collapse_ws
from skill_governance import artifact_skill_declaration, synthesized_skill_declaration_for_artifact
from skill_leaf_types import (
    REGION_SYMBOL_BY_TERM,
    SkillLeaf,
    SkillLeafCarrierKind,
    SkillLeafClass,
    normalize_skill_leaf_data_type,
    normalize_skill_boundary_region,
    skill_leaf_carrier_kind_for_region,
)
from skill_path_notation import SKILL_PATH_NOTATION_VERSION, canonical_skill_path, parse_canonical_skill_path


SKILL_NORMALIZATION_VERSION = "bssc.skill.normalization.v1"


def _skill_leaf_data_type(value: Any) -> str:
    if value is None:
        return "Null"
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "Int"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, str):
        return "String"
    if isinstance(value, (bytes, bytearray)):
        return "Bytes"
    return normalize_skill_leaf_data_type(type(value).__name__ or "Opaque")


def _skill_leaf_class(
    *,
    value: Any,
    carrier_kind: SkillLeafCarrierKind,
) -> SkillLeafClass:
    if carrier_kind == SkillLeafCarrierKind.REFERENCE:
        return SkillLeafClass.REFERENCE
    if value is None:
        return SkillLeafClass.NULL
    if isinstance(value, (str, bool, int, float)):
        return SkillLeafClass.SCALAR
    if isinstance(value, (bytes, bytearray, set, frozenset)):
        return SkillLeafClass.OPAQUE
    return SkillLeafClass.SCALAR


def _json_safe_leaf_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
    except TypeError:
        return {
            "opaque_type": type(value).__name__,
            "repr": repr(value),
        }
    return value


def normalize_skill_region_body(
    region: BoundaryShapeTerm | str,
    body: Any,
) -> list[SkillLeaf]:
    """
    High Level Purpose:
        In circumstances like canonical skill normalization, helps with flattening one structured boundary-region body into a deterministic region-aware leaf ledger.

    Reference to Theory:
        Implements section-4.6 `Φ_r(x)` by converting one region body into canonical leaf records over canonical path notation.

    Example Input Output:
        Input: `normalize_skill_region_body(BoundaryShapeTerm.INPUT_VALUE, {'query': 'find class Foo', 'options': {'roots': ['src', 'lib']}})`
        Output: [SkillLeaf(region=BoundaryShapeTerm.INPUT_VALUE, path='/a/query', carrier_kind=SkillLeafCarrierKind.VALUE, data_type='String', semantic_label='query', value='find class Foo', leaf_class=SkillLeafClass.SCALAR), ...]

    Args:
        region: Value for `region` used by `normalize_skill_region_body`. Expected type: `BoundaryShapeTerm | str`.
        body: Value for `body` used by `normalize_skill_region_body`. Expected type: `Any`.

    Returns:
        list[SkillLeaf]: Result produced by `normalize_skill_region_body`.
    """
    normalized_region = normalize_skill_boundary_region(region)
    carrier_kind = skill_leaf_carrier_kind_for_region(normalized_region)
    leaves: list[SkillLeaf] = []

    def visit(value: Any, segments: list[Any]) -> None:
        if isinstance(value, Mapping):
            for key in sorted((str(item) for item in value.keys()), key=str.casefold):
                visit(value.get(key), [*segments, key])
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for index, item in enumerate(value):
                visit(item, [*segments, index])
            return
        path = canonical_skill_path(normalized_region, segments)
        semantic_label = collapse_ws(str(segments[-1])) if segments else REGION_SYMBOL_BY_TERM[normalized_region]
        leaf = SkillLeaf(
            region=normalized_region,
            path=path,
            carrier_kind=carrier_kind,
            data_type=_skill_leaf_data_type(value),
            semantic_label=semantic_label,
            value=_json_safe_leaf_value(value),
            leaf_class=_skill_leaf_class(value=value, carrier_kind=carrier_kind),
        )
        leaves.append(leaf)

    visit(body, [])
    return leaves


def reconstruct_skill_region_body(
    region: BoundaryShapeTerm | str,
    leaves: Sequence[SkillLeaf | Mapping[str, Any]],
) -> Any:
    """
    High Level Purpose:
        In circumstances like canonical skill normalization validation, helps with rebuilding one structured region body from a deterministic region-aware leaf ledger.

    Reference to Theory:
        Implements the section-4.6 reconstructibility requirement for `Φ_r(x)`.

    Example Input Output:
        Input: `reconstruct_skill_region_body(BoundaryShapeTerm.INPUT_VALUE, [SkillLeaf(region=BoundaryShapeTerm.INPUT_VALUE, path='/a/query', carrier_kind=SkillLeafCarrierKind.VALUE, data_type='String', semantic_label='query', value='foo', leaf_class=SkillLeafClass.SCALAR)])`
        Output: {'query': 'foo'}

    Args:
        region: Value for `region` used by `reconstruct_skill_region_body`. Expected type: `BoundaryShapeTerm | str`.
        leaves: Value for `leaves` used by `reconstruct_skill_region_body`. Expected type: `Sequence[SkillLeaf | Mapping[str, Any]]`.

    Returns:
        Any: Result produced by `reconstruct_skill_region_body`.
    """
    normalized_region = normalize_skill_boundary_region(region)
    normalized_leaves = [
        item if isinstance(item, SkillLeaf) else SkillLeaf.from_dict(dict(item))
        for item in leaves
    ]
    for leaf in normalized_leaves:
        if leaf.region != normalized_region:
            raise ValueError("Cannot reconstruct a region body from leaves belonging to a different region.")

    if not normalized_leaves:
        return {}

    root: Any = {}
    root_initialized = False
    for leaf in normalized_leaves:
        _region, segments = parse_canonical_skill_path(leaf.path)
        if not segments:
            return leaf.value
        current = root
        for position, raw_segment in enumerate(segments):
            is_last = position == len(segments) - 1
            segment_is_index = raw_segment.isdigit()
            segment: str | int = int(raw_segment) if segment_is_index else raw_segment
            next_segment = None if is_last else segments[position + 1]
            next_is_index = bool(next_segment is not None and str(next_segment).isdigit())
            if segment_is_index:
                if not root_initialized:
                    root = []
                    current = root
                    root_initialized = True
                if not isinstance(current, list):
                    raise ValueError("Canonical skill leaves mix mapping and list structures incompatibly.")
                while len(current) <= segment:
                    current.append(None)
                if is_last:
                    current[segment] = leaf.value
                else:
                    existing = current[segment]
                    if existing is None:
                        existing = [] if next_is_index else {}
                        current[segment] = existing
                    current = existing
                continue
            if not root_initialized:
                root = {}
                current = root
                root_initialized = True
            if not isinstance(current, dict):
                raise ValueError("Canonical skill leaves mix mapping and list structures incompatibly.")
            if is_last:
                current[segment] = leaf.value
            else:
                existing = current.get(segment)
                if existing is None:
                    existing = [] if next_is_index else {}
                    current[segment] = existing
                current = existing
    return root


def _normalization_region_document(
    region: BoundaryShapeTerm,
    body: Any,
) -> dict[str, Any]:
    leaves = normalize_skill_region_body(region, body)
    reconstructible = all(leaf.leaf_class != SkillLeafClass.OPAQUE for leaf in leaves)
    return {
        "boundary_term": region.value,
        "carrier_kind": skill_leaf_carrier_kind_for_region(region).value,
        "reconstructible": reconstructible,
        "leaves": [leaf.to_dict() for leaf in leaves],
    }


def normalized_skill_normalization_payload(value: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing portable skill documents that already carry normalization metadata, helps with canonicalizing that metadata into a stable repository-local shape.

    Reference to Theory:
        Preserves section-4.6 path-ledger imports by validating regions, leaves, and reconstructibility hints instead of treating normalization as an opaque blob.

    Example Input Output:
        Input: `normalized_skill_normalization_payload({'normalization_version': 'bssc.skill.normalization.v1', 'path_notation_version': 'bssc.skill.path.v1', 'regions': {'a': {'boundary_term': 'a*', 'carrier_kind': 'value', 'reconstructible': True, 'leaves': [{'region': 'a*', 'path': '/a/query', 'carrier_kind': 'value', 'data_type': 'String', 'semantic_label': 'query', 'value': 'foo', 'leaf_class': 'scalar'}]}}})`
        Output: {'normalization_version': 'bssc.skill.normalization.v1', 'path_notation_version': 'bssc.skill.path.v1', 'regions': {'a': {'boundary_term': 'a*', 'carrier_kind': 'value', 'reconstructible': True, 'leaves': [{'region': 'a*', 'path': '/a/query', 'carrier_kind': 'value', 'data_type': 'String', 'semantic_label': 'query', 'value': 'foo', 'leaf_class': 'scalar'}]}}}

    Args:
        value: Value for `value` used by `normalized_skill_normalization_payload`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `normalized_skill_normalization_payload`.
    """
    if not isinstance(value, Mapping):
        return {}
    raw_regions = dict(value.get("regions", {})) if isinstance(value.get("regions", {}), Mapping) else {}
    regions: dict[str, Any] = {}
    for key, payload in raw_regions.items():
        if not isinstance(payload, Mapping):
            continue
        region = normalize_skill_boundary_region(payload.get("boundary_term", key))
        leaves = [
            item.to_dict() if isinstance(item, SkillLeaf) else SkillLeaf.from_dict(dict(item)).to_dict()
            for item in payload.get("leaves", [])
            if isinstance(item, (SkillLeaf, Mapping))
        ] if isinstance(payload.get("leaves", []), Sequence) and not isinstance(payload.get("leaves", []), (str, bytes, bytearray)) else []
        regions[REGION_SYMBOL_BY_TERM[region]] = {
            "boundary_term": region.value,
            "carrier_kind": skill_leaf_carrier_kind_for_region(region).value,
            "reconstructible": bool(payload.get("reconstructible", all(item.get("leaf_class") != SkillLeafClass.OPAQUE.value for item in leaves))),
            "leaves": leaves,
        }
    if not regions:
        return {}
    return {
        "normalization_version": str(value.get("normalization_version", SKILL_NORMALIZATION_VERSION)).strip() or SKILL_NORMALIZATION_VERSION,
        "path_notation_version": str(value.get("path_notation_version", SKILL_PATH_NOTATION_VERSION)).strip() or SKILL_PATH_NOTATION_VERSION,
        "regions": regions,
    }


def synthesized_skill_normalization_for_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing or exporting legacy governed skills, helps with synthesizing one conservative canonical boundary-normalization document from the current artifact fields.

    Reference to Theory:
        Implements the section-4.6 path-ledger substrate additively for existing skills so composition and invocation can evolve without breaking current persistence or runtime behavior.

    Example Input Output:
        Input: `synthesized_skill_normalization_for_artifact(Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml', function_bit=0, scope='', provenance=[], reusability='local_reuse', admissibility='candidate', template_schema={}, learning_relation='new_family', related_artifact_ids=[], content={'answer': 'F = m * a'}, justification=''))`
        Output: {'normalization_version': 'bssc.skill.normalization.v1', 'path_notation_version': 'bssc.skill.path.v1', 'regions': {'d': {'boundary_term': 'd*', 'carrier_kind': 'value', 'reconstructible': True, 'leaves': [...]}, ...}}

    Args:
        artifact: Value for `artifact` used by `synthesized_skill_normalization_for_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `synthesized_skill_normalization_for_artifact`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    declaration = artifact_skill_declaration(artifact) or synthesized_skill_declaration_for_artifact(artifact)
    input_contract = dict(content.get("input_contract", {})) if isinstance(content.get("input_contract", {}), Mapping) else {}
    output_contract = dict(content.get("output_contract", {})) if isinstance(content.get("output_contract", {}), Mapping) else {}
    input_values = input_contract or (dict(declaration.get("inputs", {})) if isinstance(declaration.get("inputs", {}), Mapping) else {})
    output_values = output_contract or (dict(declaration.get("outputs", {})) if isinstance(declaration.get("outputs", {}), Mapping) else {})
    if not output_values and str(content.get("answer", "")).strip():
        output_values = {"answer": str(content.get("answer", "")).strip()}

    regions: dict[str, Any] = {}
    for region in BoundaryShapeTerm:
        body: Any = {}
        if region == BoundaryShapeTerm.INPUT_VALUE:
            body = input_values
        elif region == BoundaryShapeTerm.OUTPUT_VALUE:
            body = output_values
        regions[REGION_SYMBOL_BY_TERM[region]] = _normalization_region_document(region, body)
    return {
        "normalization_version": SKILL_NORMALIZATION_VERSION,
        "path_notation_version": SKILL_PATH_NOTATION_VERSION,
        "regions": regions,
    }
