"""Canonical normalization for portable skill boundary bodies."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from realized_skill_semantics.leaves import (
    BoundaryShapeTerm,
    REGION_SYMBOL_BY_TERM,
    SkillLeaf,
    SkillLeafCarrierKind,
    SkillLeafClass,
    normalize_skill_boundary_region,
    normalize_skill_leaf_data_type,
    skill_leaf_carrier_kind_for_region,
)
from realized_skill_semantics.paths import (
    SKILL_PATH_NOTATION_VERSION,
    canonical_skill_path,
    parse_canonical_skill_path,
)


SKILL_NORMALIZATION_VERSION = "bssc.skill.normalization.v1"

__all__ = [
    "SKILL_NORMALIZATION_VERSION",
    "normalize_skill_region_body",
    "normalized_skill_normalization_payload",
    "reconstruct_skill_region_body",
    "synthesized_skill_normalization",
]


def _collapse_ws(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()


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
    """Flatten one boundary-region body into a deterministic typed leaf ledger."""
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
        semantic_label = (
            _collapse_ws(segments[-1])
            if segments
            else REGION_SYMBOL_BY_TERM[normalized_region]
        )
        leaves.append(
            SkillLeaf(
                region=normalized_region,
                path=path,
                carrier_kind=carrier_kind,
                data_type=_skill_leaf_data_type(value),
                semantic_label=semantic_label,
                value=_json_safe_leaf_value(value),
                leaf_class=_skill_leaf_class(
                    value=value,
                    carrier_kind=carrier_kind,
                ),
            )
        )

    visit(body, [])
    return leaves


def reconstruct_skill_region_body(
    region: BoundaryShapeTerm | str,
    leaves: Sequence[SkillLeaf | Mapping[str, Any]],
) -> Any:
    """Rebuild one structured region body from its canonical leaf ledger."""
    normalized_region = normalize_skill_boundary_region(region)
    normalized_leaves = [
        item if isinstance(item, SkillLeaf) else SkillLeaf.from_dict(dict(item))
        for item in leaves
    ]
    for leaf in normalized_leaves:
        if leaf.region != normalized_region:
            raise ValueError(
                "Cannot reconstruct a region body from leaves belonging to a different region."
            )

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
            next_is_index = bool(
                next_segment is not None and str(next_segment).isdigit()
            )
            if segment_is_index:
                if not root_initialized:
                    root = []
                    current = root
                    root_initialized = True
                if not isinstance(current, list):
                    raise ValueError(
                        "Canonical skill leaves mix mapping and list structures incompatibly."
                    )
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
                raise ValueError(
                    "Canonical skill leaves mix mapping and list structures incompatibly."
                )
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
    reconstructible = all(
        leaf.leaf_class != SkillLeafClass.OPAQUE for leaf in leaves
    )
    return {
        "boundary_term": region.value,
        "carrier_kind": skill_leaf_carrier_kind_for_region(region).value,
        "reconstructible": reconstructible,
        "leaves": [leaf.to_dict() for leaf in leaves],
    }


def normalized_skill_normalization_payload(value: Any) -> dict[str, Any]:
    """Validate and canonicalize imported skill-normalization metadata."""
    if not isinstance(value, Mapping):
        return {}
    raw_regions = (
        dict(value.get("regions", {}))
        if isinstance(value.get("regions", {}), Mapping)
        else {}
    )
    regions: dict[str, Any] = {}
    for key, payload in raw_regions.items():
        if not isinstance(payload, Mapping):
            continue
        region = normalize_skill_boundary_region(payload.get("boundary_term", key))
        raw_leaves = payload.get("leaves", [])
        leaves = (
            [
                item.to_dict()
                if isinstance(item, SkillLeaf)
                else SkillLeaf.from_dict(dict(item)).to_dict()
                for item in raw_leaves
                if isinstance(item, (SkillLeaf, Mapping))
            ]
            if isinstance(raw_leaves, Sequence)
            and not isinstance(raw_leaves, (str, bytes, bytearray))
            else []
        )
        regions[REGION_SYMBOL_BY_TERM[region]] = {
            "boundary_term": region.value,
            "carrier_kind": skill_leaf_carrier_kind_for_region(region).value,
            "reconstructible": bool(
                payload.get(
                    "reconstructible",
                    all(
                        item.get("leaf_class") != SkillLeafClass.OPAQUE.value
                        for item in leaves
                    ),
                )
            ),
            "leaves": leaves,
        }
    if not regions:
        return {}
    return {
        "normalization_version": str(
            value.get("normalization_version", SKILL_NORMALIZATION_VERSION)
        ).strip()
        or SKILL_NORMALIZATION_VERSION,
        "path_notation_version": str(
            value.get("path_notation_version", SKILL_PATH_NOTATION_VERSION)
        ).strip()
        or SKILL_PATH_NOTATION_VERSION,
        "regions": regions,
    }


def synthesized_skill_normalization(
    *,
    input_values: Any,
    output_values: Any,
) -> dict[str, Any]:
    """Build a complete eight-region normalization document from explicit values."""
    regions: dict[str, Any] = {}
    for region in BoundaryShapeTerm:
        body: Any = {}
        if region == BoundaryShapeTerm.INPUT_VALUE:
            body = input_values
        elif region == BoundaryShapeTerm.OUTPUT_VALUE:
            body = output_values
        regions[REGION_SYMBOL_BY_TERM[region]] = _normalization_region_document(
            region,
            body,
        )
    return {
        "normalization_version": SKILL_NORMALIZATION_VERSION,
        "path_notation_version": SKILL_PATH_NOTATION_VERSION,
        "regions": regions,
    }
