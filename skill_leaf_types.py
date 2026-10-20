# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from applied_theory_primitives import BoundaryShapeTerm, json_safe


class SkillLeafCarrierKind(str, Enum):
    VALUE = "value"
    REFERENCE = "reference"


class SkillLeafClass(str, Enum):
    SCALAR = "scalar"
    REFERENCE = "reference"
    COLLECTION = "collection"
    NULL = "null"
    OPAQUE = "opaque"


STATE_INTERFACE_PRIMITIVE_KIND_ALIASES: dict[str, str] = {
    "string": "String",
    "str": "String",
    "bytes": "Bytes",
    "byte": "Bytes",
    "int": "Int",
    "integer": "Int",
    "bool": "Boolean",
    "boolean": "Boolean",
    "float": "Float",
    "number": "Float",
}

STATE_INTERFACE_REPEATED_PRIMITIVE_KIND_ALIASES: dict[str, str] = {
    "strings": "Strings",
    "strs": "Strings",
    "bytes[]": "Bytess",
    "list[bytes]": "Bytess",
    "sequence[bytes]": "Bytess",
    "array[bytes]": "Bytess",
    "tuple[bytes]": "Bytess",
    "bytess": "Bytess",
    "ints": "Ints",
    "integers": "Ints",
    "ints[]": "Ints",
    "list[int]": "Ints",
    "sequence[int]": "Ints",
    "array[int]": "Ints",
    "tuple[int]": "Ints",
    "bools": "Bools",
    "booleans": "Bools",
    "bools[]": "Bools",
    "list[bool]": "Bools",
    "sequence[bool]": "Bools",
    "array[bool]": "Bools",
    "tuple[bool]": "Bools",
    "floats": "Floats",
    "numbers": "Floats",
    "floats[]": "Floats",
    "list[float]": "Floats",
    "sequence[float]": "Floats",
    "array[float]": "Floats",
    "tuple[float]": "Floats",
    "string[]": "Strings",
    "list[string]": "Strings",
    "sequence[string]": "Strings",
    "array[string]": "Strings",
    "tuple[string]": "Strings",
    "list[str]": "Strings",
    "sequence[str]": "Strings",
    "array[str]": "Strings",
    "tuple[str]": "Strings",
}

SKILL_LEAF_NON_PRIMITIVE_TYPE_ALIASES: dict[str, str] = {
    "null": "Null",
    "none": "Null",
    "opaque": "Opaque",
    "object": "Opaque",
    "array": "Opaque",
    "unknown": "Opaque",
}


def normalize_skill_leaf_data_type(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like canonical skill normalization and import of legacy normalization payloads, helps with collapsing raw type names into one stable `SkillLeaf.data_type` vocabulary aligned with the service-interface notation primitive kinds.

    Reference to Theory:
        Preserves the section-4.6 leaf object `ℓ = <r, π, κ, τ, σ, ν>` by giving `τ` a stable canonical type vocabulary rather than ad hoc lowercase Python type names.

    Example Input Output:
        Input: `normalize_skill_leaf_data_type('string')`
        Output: 'String'

    Args:
        value: Value for `value` used by `normalize_skill_leaf_data_type`. Expected type: `Any`.

    Returns:
        str: Result produced by `normalize_skill_leaf_data_type`.
    """
    raw_text = str(getattr(value, "value", value) or "").strip()
    if not raw_text:
        return "Opaque"
    normalized_key = raw_text.casefold()
    if normalized_key in STATE_INTERFACE_REPEATED_PRIMITIVE_KIND_ALIASES:
        return STATE_INTERFACE_REPEATED_PRIMITIVE_KIND_ALIASES[normalized_key]
    if normalized_key in STATE_INTERFACE_PRIMITIVE_KIND_ALIASES:
        return STATE_INTERFACE_PRIMITIVE_KIND_ALIASES[normalized_key]
    if normalized_key in SKILL_LEAF_NON_PRIMITIVE_TYPE_ALIASES:
        return SKILL_LEAF_NON_PRIMITIVE_TYPE_ALIASES[normalized_key]
    return raw_text


REGION_SYMBOL_BY_TERM: dict[BoundaryShapeTerm, str] = {
    BoundaryShapeTerm.INPUT_VALUE: "a",
    BoundaryShapeTerm.INPUT_REFERENCE: "a'",
    BoundaryShapeTerm.READ_VALUE: "b",
    BoundaryShapeTerm.READ_REFERENCE: "b'",
    BoundaryShapeTerm.WRITE_VALUE: "c",
    BoundaryShapeTerm.WRITE_REFERENCE: "c'",
    BoundaryShapeTerm.OUTPUT_VALUE: "d",
    BoundaryShapeTerm.OUTPUT_REFERENCE: "d'",
}

REGION_TERM_BY_SYMBOL: dict[str, BoundaryShapeTerm] = {
    symbol: term
    for term, symbol in REGION_SYMBOL_BY_TERM.items()
}


def normalize_skill_boundary_region(value: Any) -> BoundaryShapeTerm:
    """
    High Level Purpose:
        In circumstances like canonical skill normalization, helps with reducing raw region labels into the shared boundary-shape terms already used by the theory and artifact layers.

    Reference to Theory:
        Preserves the section-4.6 region-aware path ledger by reusing the existing `a, a', b, b', c, c', d, d'` boundary doctrine instead of inventing a parallel region algebra.

    Example Input Output:
        Input: `normalize_skill_boundary_region("a'*")`
        Output: BoundaryShapeTerm.INPUT_REFERENCE

    Args:
        value: Value for `value` used by `normalize_skill_boundary_region`. Expected type: `Any`.

    Returns:
        BoundaryShapeTerm: Result produced by `normalize_skill_boundary_region`.
    """
    raw = getattr(value, "value", value)
    text = str(raw or "").strip()
    for term in BoundaryShapeTerm:
        if text == term.value:
            return term
    if text in REGION_TERM_BY_SYMBOL:
        return REGION_TERM_BY_SYMBOL[text]
    raise ValueError(f"Unsupported skill boundary region: {value}")


def skill_boundary_region_symbol(region: BoundaryShapeTerm | str) -> str:
    """
    High Level Purpose:
        In circumstances like canonical path notation, helps with rendering one boundary region into the compact region-prefix symbol used in normalized skill ledgers.

    Reference to Theory:
        Preserves section-4.6 region-aware flattening by making path namespaces explicitly encode the boundary region.

    Example Input Output:
        Input: `skill_boundary_region_symbol(BoundaryShapeTerm.OUTPUT_REFERENCE)`
        Output: "d'"

    Args:
        region: Value for `region` used by `skill_boundary_region_symbol`. Expected type: `BoundaryShapeTerm | str`.

    Returns:
        str: Result produced by `skill_boundary_region_symbol`.
    """
    normalized = normalize_skill_boundary_region(region)
    return REGION_SYMBOL_BY_TERM[normalized]


def skill_leaf_carrier_kind_for_region(region: BoundaryShapeTerm | str) -> SkillLeafCarrierKind:
    """
    High Level Purpose:
        In circumstances like path-ledger synthesis, helps with deriving whether a boundary region carries values or references.

    Reference to Theory:
        Preserves section-4.6 polarity-aware flattening by keeping value vs reference first-class in the normalized leaf model.

    Example Input Output:
        Input: `skill_leaf_carrier_kind_for_region(BoundaryShapeTerm.READ_REFERENCE)`
        Output: SkillLeafCarrierKind.REFERENCE

    Args:
        region: Value for `region` used by `skill_leaf_carrier_kind_for_region`. Expected type: `BoundaryShapeTerm | str`.

    Returns:
        SkillLeafCarrierKind: Result produced by `skill_leaf_carrier_kind_for_region`.
    """
    normalized = normalize_skill_boundary_region(region)
    if normalized in {
        BoundaryShapeTerm.INPUT_REFERENCE,
        BoundaryShapeTerm.READ_REFERENCE,
        BoundaryShapeTerm.WRITE_REFERENCE,
        BoundaryShapeTerm.OUTPUT_REFERENCE,
    }:
        return SkillLeafCarrierKind.REFERENCE
    return SkillLeafCarrierKind.VALUE


@dataclass(frozen=True)
class SkillLeaf:
    region: BoundaryShapeTerm
    path: str
    carrier_kind: SkillLeafCarrierKind
    data_type: str
    semantic_label: str
    value: Any
    leaf_class: SkillLeafClass = SkillLeafClass.SCALAR

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like exporting canonical normalization metadata into portable skill documents, helps with rendering one in-memory leaf into a JSON/YAML-safe record.

        Reference to Theory:
            Preserves the section-4.6 leaf object `ℓ = <r, π, κ, τ, σ, ν>` as a serializable record for canonical path ledgers.

        Example Input Output:
            Input: `SkillLeaf(region=BoundaryShapeTerm.INPUT_VALUE, path='/a/query', carrier_kind=SkillLeafCarrierKind.VALUE, data_type='String', semantic_label='query', value='force').to_dict()`
            Output: {'region': 'a*', 'path': '/a/query', 'carrier_kind': 'value', 'data_type': 'String', 'semantic_label': 'query', 'value': 'force', 'leaf_class': 'scalar'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "region": self.region.value,
            "path": self.path,
            "carrier_kind": self.carrier_kind.value,
            "data_type": self.data_type,
            "semantic_label": self.semantic_label,
            "value": json_safe(self.value),
            "leaf_class": self.leaf_class.value,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillLeaf":
        """
        High Level Purpose:
            In circumstances like importing canonical normalization metadata from portable skill documents, helps with reconstructing one in-memory leaf from a serialized record.

        Reference to Theory:
            Preserves the section-4.6 canonical leaf object while allowing portable import/export survival.

        Example Input Output:
            Input: `SkillLeaf.from_dict({'region': 'd*', 'path': '/d/answer', 'carrier_kind': 'value', 'data_type': 'String', 'semantic_label': 'answer', 'value': 'F = m * a', 'leaf_class': 'scalar'})`
            Output: SkillLeaf(region=BoundaryShapeTerm.OUTPUT_VALUE, path='/d/answer', carrier_kind=SkillLeafCarrierKind.VALUE, data_type='String', semantic_label='answer', value='F = m * a', leaf_class=SkillLeafClass.SCALAR)

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            payload: Value for `payload` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            SkillLeaf: Result produced by `from_dict`.
        """
        return cls(
            region=normalize_skill_boundary_region(payload.get("region", "")),
            path=str(payload.get("path", "")).strip(),
            carrier_kind=SkillLeafCarrierKind(str(payload.get("carrier_kind", SkillLeafCarrierKind.VALUE.value)).strip() or SkillLeafCarrierKind.VALUE.value),
            data_type=normalize_skill_leaf_data_type(payload.get("data_type", "")),
            semantic_label=str(payload.get("semantic_label", "")).strip(),
            value=payload.get("value"),
            leaf_class=SkillLeafClass(str(payload.get("leaf_class", SkillLeafClass.SCALAR.value)).strip() or SkillLeafClass.SCALAR.value),
        )
