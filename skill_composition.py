# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from applied_theory_types import Artifact, BoundaryShapeTerm, json_safe
from semantic_text import collapse_ws
from skill_boundary_normalization import normalize_skill_region_body, reconstruct_skill_region_body
from skill_ir import CanonicalSkillIR, canonical_skill_ir_from_artifact
from skill_leaf_types import (
    SkillLeaf,
    SkillLeafCarrierKind,
    SkillLeafClass,
    normalize_skill_leaf_data_type,
)
from skill_path_notation import parse_canonical_skill_path


_SOURCE_TARGET_REGION_COMPATIBILITY: dict[str, set[str]] = {
    "a": {"a", "b"},
    "a'": {"a'", "b'"},
    "c": {"a", "b"},
    "c'": {"a'", "b'"},
    "d": {"a", "b"},
    "d'": {"a'", "b'"},
}

_REPEATED_TO_SINGULAR: dict[str, str] = {
    "Strings": "String",
    "Bytess": "Bytes",
    "Ints": "Int",
    "Bools": "Boolean",
    "Floats": "Float",
}
_SINGULAR_TO_REPEATED = {value: key for key, value in _REPEATED_TO_SINGULAR.items()}
_CANONICAL_PRIMITIVE_TYPES = set(_REPEATED_TO_SINGULAR.values()) | set(_REPEATED_TO_SINGULAR.keys())


@dataclass(frozen=True)
class SkillCompositionMapper:
    kind: str = "identity"
    field: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionMapper":
        if not isinstance(payload, Mapping):
            raise TypeError("SkillCompositionMapper.from_dict requires a mapping payload.")
        return cls(
            kind=collapse_ws(str(payload.get("kind", "identity"))) or "identity",
            field=collapse_ws(str(payload.get("field", payload.get("source_key", "")))),
        )


@dataclass(frozen=True)
class SkillCompositionBinding:
    target_region: str
    target_path: str
    source_step_id: str = ""
    source_region: str = ""
    source_path: str = ""
    source_root_name: str = ""
    source_root_region: str = ""
    constant_value: Any = None
    mapper: SkillCompositionMapper | None = None
    mapper_kind: str = "identity"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionBinding":
        if not isinstance(payload, Mapping):
            raise TypeError("SkillCompositionBinding.from_dict requires a mapping payload.")
        mapper_payload = payload.get("mapper")
        mapper = (
            SkillCompositionMapper.from_dict(mapper_payload)
            if isinstance(mapper_payload, Mapping)
            else None
        )
        return cls(
            target_region=collapse_ws(str(payload.get("target_region", ""))),
            target_path=collapse_ws(str(payload.get("target_path", ""))),
            source_step_id=collapse_ws(str(payload.get("source_step_id", ""))),
            source_region=collapse_ws(str(payload.get("source_region", ""))),
            source_path=collapse_ws(str(payload.get("source_path", ""))),
            source_root_name=collapse_ws(str(payload.get("source_root_name", ""))),
            source_root_region=collapse_ws(str(payload.get("source_root_region", ""))),
            constant_value=payload.get("constant_value"),
            mapper=mapper,
            mapper_kind=collapse_ws(str(payload.get("mapper_kind", "identity"))) or "identity",
        )


@dataclass(frozen=True)
class SkillCompositionCondition:
    source_step_id: str
    source_region: str
    source_path: str
    operator: str = "equals"
    expected_value: Any = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionCondition":
        if not isinstance(payload, Mapping):
            raise TypeError("SkillCompositionCondition.from_dict requires a mapping payload.")
        return cls(
            source_step_id=collapse_ws(str(payload.get("source_step_id", ""))),
            source_region=collapse_ws(str(payload.get("source_region", ""))),
            source_path=collapse_ws(str(payload.get("source_path", ""))),
            operator=collapse_ws(str(payload.get("operator", "equals"))) or "equals",
            expected_value=payload.get("expected_value"),
        )


@dataclass(frozen=True)
class SkillCompositionStep:
    step_id: str
    skill: CanonicalSkillIR | Artifact | Mapping[str, Any]
    bindings: tuple[SkillCompositionBinding, ...] = ()
    run_if: tuple[SkillCompositionCondition, ...] = ()
    iterate_until: tuple[SkillCompositionCondition, ...] = ()
    branch_label: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SkillCompositionStep":
        if not isinstance(payload, Mapping):
            raise TypeError("SkillCompositionStep.from_dict requires a mapping payload.")
        bindings = tuple(
            item if isinstance(item, SkillCompositionBinding) else SkillCompositionBinding.from_dict(item)
            for item in payload.get("bindings", ())
        )
        run_if = tuple(
            item if isinstance(item, SkillCompositionCondition) else SkillCompositionCondition.from_dict(item)
            for item in payload.get("run_if", ())
        )
        iterate_until = tuple(
            item if isinstance(item, SkillCompositionCondition) else SkillCompositionCondition.from_dict(item)
            for item in payload.get("iterate_until", ())
        )
        return cls(
            step_id=collapse_ws(str(payload.get("step_id", ""))),
            skill=payload.get("skill", {}),
            bindings=bindings,
            run_if=run_if,
            iterate_until=iterate_until,
            branch_label=collapse_ws(str(payload.get("branch_label", ""))),
        )


@dataclass(frozen=True)
class SkillBindingDiagnostic:
    step_id: str
    target_region: str
    target_path: str
    status: str
    source_kind: str
    source_step_id: str = ""
    source_region: str = ""
    source_path: str = ""
    source_root_name: str = ""
    source_root_region: str = ""
    mapper_kind: str = "identity"
    reason: str = ""


@dataclass(frozen=True)
class SkillConditionDiagnostic:
    step_id: str
    status: str
    source_step_id: str
    source_region: str
    source_path: str
    operator: str
    reason: str = ""


@dataclass(frozen=True)
class SkillCompositionCandidate:
    source_region: str
    source_path: str
    target_region: str
    target_path: str
    status: str
    reason: str
    mapper_kind: str = "identity"


@dataclass(frozen=True)
class SkillCompositionPlanAnalysis:
    steps: list[dict[str, Any]]
    plan_authorities: list[str]
    blocked: bool
    unresolved_targets: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "steps": self.steps,
                "plan_authorities": self.plan_authorities,
                "blocked": self.blocked,
                "unresolved_targets": self.unresolved_targets,
            }
        )


@dataclass(frozen=True)
class SkillCompositionStepExecutionRecord:
    step_id: str
    title: str
    status: str
    iteration: int
    branch_label: str = ""
    input_payload: dict[str, Any] | None = None
    output_payload: Any = None
    binding_receipts: list[dict[str, Any]] | None = None
    condition_receipts: list[dict[str, Any]] | None = None
    skipped_reason: str = ""


@dataclass(frozen=True)
class SkillCompositionExecutionResult:
    steps: list[dict[str, Any]]
    plan_authorities: list[str]
    final_outputs_by_step: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "steps": self.steps,
                "plan_authorities": self.plan_authorities,
                "final_outputs_by_step": self.final_outputs_by_step,
            }
        )


@dataclass(frozen=True)
class SkillCompositionExecutionEvent:
    kind: str
    step_id: str
    title: str
    iteration: int
    branch_label: str = ""
    status: str = ""
    input_payload: dict[str, Any] | None = None
    output_payload: Any = None
    binding_receipts: list[dict[str, Any]] | None = None
    condition_receipts: list[dict[str, Any]] | None = None
    skipped_reason: str = ""
    error: str = ""
    result_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "kind": self.kind,
                "step_id": self.step_id,
                "title": self.title,
                "iteration": self.iteration,
                "branch_label": self.branch_label,
                "status": self.status,
                "input_payload": self.input_payload,
                "output_payload": self.output_payload,
                "binding_receipts": self.binding_receipts,
                "condition_receipts": self.condition_receipts,
                "skipped_reason": self.skipped_reason,
                "error": self.error,
                "result_payload": self.result_payload,
            }
        )


def _normalize_mapper_kind(binding: SkillCompositionBinding) -> str:
    if binding.mapper is not None:
        return collapse_ws(str(binding.mapper.kind or "identity")) or "identity"
    return collapse_ws(str(binding.mapper_kind or "identity")) or "identity"


def _mapper_field_name(binding: SkillCompositionBinding) -> str:
    if binding.mapper is not None:
        return collapse_ws(str(binding.mapper.field or ""))
    return ""


def _normalize_composition_step(
    step: SkillCompositionStep | Mapping[str, Any],
) -> SkillCompositionStep:
    if isinstance(step, SkillCompositionStep):
        return step
    if isinstance(step, Mapping):
        return SkillCompositionStep.from_dict(step)
    raise TypeError("Skill composition planning requires SkillCompositionStep or mapping payloads.")


def _normalize_composition_steps(
    steps: Sequence[SkillCompositionStep | Mapping[str, Any]],
) -> list[SkillCompositionStep]:
    return [_normalize_composition_step(step) for step in steps]


def _emit_skill_composition_execution_event(
    execution_observer: Callable[[SkillCompositionExecutionEvent], None] | None,
    event: SkillCompositionExecutionEvent,
) -> None:
    if execution_observer is None:
        return
    try:
        execution_observer(event)
    except Exception:
        return


def _skill_ir_dict(skill: CanonicalSkillIR | Artifact | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(skill, CanonicalSkillIR):
        return skill.to_dict()
    if isinstance(skill, Artifact):
        return canonical_skill_ir_from_artifact(skill).to_dict()
    if isinstance(skill, Mapping):
        payload = dict(skill)
        if {"artifact_id", "title", "schema", "kind", "normalization"}.issubset(payload.keys()):
            return payload
    raise TypeError("Skill composition analysis requires CanonicalSkillIR, Artifact, or canonical skill IR mapping.")


def _canonical_skill_leaves(
    skill: CanonicalSkillIR | Artifact | Mapping[str, Any],
    *,
    regions: set[str] | None = None,
) -> dict[tuple[str, str], SkillLeaf]:
    ir = _skill_ir_dict(skill)
    normalization = dict(ir.get("normalization", {})) if isinstance(ir.get("normalization", {}), Mapping) else {}
    normalized_regions = dict(normalization.get("regions", {})) if isinstance(normalization.get("regions", {}), Mapping) else {}
    leaves: dict[tuple[str, str], SkillLeaf] = {}
    for region_name, payload in normalized_regions.items():
        region_symbol = collapse_ws(str(region_name))
        if regions is not None and region_symbol not in regions:
            continue
        if not isinstance(payload, Mapping):
            continue
        raw_leaves = payload.get("leaves", [])
        if not isinstance(raw_leaves, Sequence) or isinstance(raw_leaves, (str, bytes, bytearray)):
            continue
        for item in raw_leaves:
            if not isinstance(item, (SkillLeaf, Mapping)):
                continue
            leaf = item if isinstance(item, SkillLeaf) else SkillLeaf.from_dict(dict(item))
            leaves[(region_symbol, leaf.path)] = leaf
    return leaves


def _leaf_terminal_segment(leaf: SkillLeaf) -> str:
    _region, segments = parse_canonical_skill_path(leaf.path)
    if not segments:
        return ""
    return collapse_ws(str(segments[-1]))


def _normalized_semantic_key(value: Any) -> str:
    return collapse_ws(str(value)).replace("_", " ").replace("-", " ").casefold()


def _primitive_family(value: str) -> str:
    text = collapse_ws(str(value))
    if text in _REPEATED_TO_SINGULAR:
        return _REPEATED_TO_SINGULAR[text]
    return text


def _leaf_data_type_for_constant(value: Any) -> str:
    if value is None:
        return ""
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
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        items = list(value)
        if not items:
            return ""
        kinds = {_leaf_data_type_for_constant(item) for item in items}
        kinds.discard("")
        if len(kinds) != 1:
            return ""
        singular = next(iter(kinds))
        return _SINGULAR_TO_REPEATED.get(singular, "")
    return normalize_skill_leaf_data_type(type(value).__name__)


def _region_pair_allowed(source_region: str, target_region: str) -> bool:
    return target_region in _SOURCE_TARGET_REGION_COMPATIBILITY.get(source_region, set())


def _leaf_type_compatibility(source_leaf: SkillLeaf, target_leaf: SkillLeaf) -> tuple[str, str]:
    source_type = collapse_ws(str(source_leaf.data_type))
    target_type = collapse_ws(str(target_leaf.data_type))
    if source_leaf.leaf_class == SkillLeafClass.OPAQUE:
        return "mapper_required", "source leaf is opaque and requires an explicit mapper."
    if target_leaf.leaf_class == SkillLeafClass.OPAQUE:
        return "mapper_required", "target leaf is opaque and requires an explicit mapper."
    if source_leaf.leaf_class == SkillLeafClass.NULL:
        return "blocked", "null source leaves cannot satisfy required target leaves without an explicit optionality rule."
    if source_type and target_type and source_type == target_type:
        return "exact", "leaf data types are identical."
    if source_type in _CANONICAL_PRIMITIVE_TYPES and target_type in _CANONICAL_PRIMITIVE_TYPES:
        if _primitive_family(source_type) == _primitive_family(target_type):
            return "mapper_required", "leaf data types share the same primitive family but differ in multiplicity."
        return "blocked", "leaf data types belong to different primitive families."
    if not source_type or not target_type:
        return "mapper_required", "one or both leaf data types are underspecified."
    return ("exact", "leaf data types match by explicit declaration.") if source_type == target_type else ("mapper_required", "leaf data types require explicit mapper treatment.")


def _leaf_semantic_compatibility(source_leaf: SkillLeaf, target_leaf: SkillLeaf) -> tuple[str, str]:
    source_label = _normalized_semantic_key(source_leaf.semantic_label)
    target_label = _normalized_semantic_key(target_leaf.semantic_label)
    source_segment = _normalized_semantic_key(_leaf_terminal_segment(source_leaf))
    target_segment = _normalized_semantic_key(_leaf_terminal_segment(target_leaf))
    if source_label and source_label == target_label:
        return "exact", "semantic labels match exactly."
    if source_segment and source_segment == target_segment:
        return "exact", "terminal canonical path segments match."
    if source_label and target_label and (source_label in target_label or target_label in source_label):
        return "mapper_required", "semantic labels are related but not identical."
    if source_segment and target_segment and (source_segment in target_segment or target_segment in source_segment):
        return "mapper_required", "canonical path segments are related but not identical."
    generic_names = {"result", "value", "output", "answer", "input", "item", "items", "data"}
    if source_segment in generic_names or target_segment in generic_names:
        return "mapper_required", "one side uses a generic semantic label and needs an explicit mapper."
    return "blocked", "semantic labels do not line up."


def _binding_status_from_leaves(source_leaf: SkillLeaf, target_leaf: SkillLeaf, *, source_region: str, target_region: str) -> tuple[str, str]:
    if not _region_pair_allowed(source_region, target_region):
        return "blocked", f"region {source_region} cannot satisfy target region {target_region}."
    if source_leaf.carrier_kind != target_leaf.carrier_kind:
        return "blocked", "carrier kinds differ."
    type_status, type_reason = _leaf_type_compatibility(source_leaf, target_leaf)
    if type_status == "blocked":
        return type_status, type_reason
    semantic_status, semantic_reason = _leaf_semantic_compatibility(source_leaf, target_leaf)
    if semantic_status == "blocked":
        return semantic_status, semantic_reason
    if type_status == "exact" and semantic_status == "exact":
        return "exact", f"{type_reason} {semantic_reason}"
    return "mapper_required", f"{type_reason} {semantic_reason}"


def _allowed_mapper_kinds(source_leaf: SkillLeaf, target_leaf: SkillLeaf) -> set[str]:
    source_type = collapse_ws(str(source_leaf.data_type))
    target_type = collapse_ws(str(target_leaf.data_type))
    if source_leaf.carrier_kind != target_leaf.carrier_kind:
        return set()
    allowed: set[str] = set()
    if source_type == target_type:
        allowed.update({"identity", "rename"})
    if source_type in _REPEATED_TO_SINGULAR and _REPEATED_TO_SINGULAR[source_type] == target_type:
        allowed.add("first_item")
    elif source_type in _CANONICAL_PRIMITIVE_TYPES and target_type in _CANONICAL_PRIMITIVE_TYPES:
        if _primitive_family(source_type) == _primitive_family(target_type):
            allowed.add("first_item")
    if source_leaf.leaf_class == SkillLeafClass.OPAQUE or target_leaf.leaf_class == SkillLeafClass.OPAQUE:
        return set()
    allowed.update({"rename", "project_field"})
    return allowed


def _apply_mapper_kind(value: Any, mapper_kind: str, *, field_name: str = "") -> Any:
    normalized = collapse_ws(str(mapper_kind or "identity")) or "identity"
    if normalized in {"identity", "rename"}:
        return value
    if normalized == "first_item":
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            items = list(value)
            if not items:
                raise ValueError("Mapper first_item cannot project from an empty sequence.")
            return items[0]
        raise ValueError("Mapper first_item requires a sequence source value.")
    if normalized == "project_field":
        if not isinstance(value, Mapping):
            raise ValueError("Mapper project_field requires a mapping source value.")
        normalized_field = collapse_ws(str(field_name))
        if not normalized_field:
            raise ValueError("Mapper project_field requires a non-empty field name.")
        if normalized_field in value:
            return value[normalized_field]
        normalized_lookup = {
            _normalized_semantic_key(key): item
            for key, item in dict(value).items()
        }
        normalized_key = _normalized_semantic_key(normalized_field)
        if normalized_key in normalized_lookup:
            return normalized_lookup[normalized_key]
        raise ValueError(f"Mapper project_field could not find field {normalized_field!r} in the source mapping.")
    raise ValueError(f"Unsupported mapper kind: {mapper_kind}")


def _build_skill_leaf_with_value(template: SkillLeaf, value: Any) -> SkillLeaf:
    if value is None:
        leaf_class = SkillLeafClass.NULL
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        leaf_class = SkillLeafClass.COLLECTION
    else:
        leaf_class = SkillLeafClass.REFERENCE if template.carrier_kind == SkillLeafCarrierKind.REFERENCE else SkillLeafClass.SCALAR
    return SkillLeaf(
        region=template.region,
        path=template.path,
        carrier_kind=template.carrier_kind,
        data_type=_leaf_data_type_for_constant(value) or template.data_type,
        semantic_label=template.semantic_label,
        value=value,
        leaf_class=leaf_class,
    )


def _single_region_payload_from_leaves(leaves: list[SkillLeaf], region: str) -> Any:
    if not leaves:
        return {}
    boundary_term = {
        "a": BoundaryShapeTerm.INPUT_VALUE,
        "a'": BoundaryShapeTerm.INPUT_REFERENCE,
        "b": BoundaryShapeTerm.READ_VALUE,
        "b'": BoundaryShapeTerm.READ_REFERENCE,
        "c": BoundaryShapeTerm.WRITE_VALUE,
        "c'": BoundaryShapeTerm.WRITE_REFERENCE,
        "d": BoundaryShapeTerm.OUTPUT_VALUE,
        "d'": BoundaryShapeTerm.OUTPUT_REFERENCE,
    }[region]
    return reconstruct_skill_region_body(boundary_term, leaves)


def _output_payload_for_skill_result(skill_ir: Mapping[str, Any], result: Any) -> Any:
    declared_output_leaves = [
        leaf
        for (region, _path), leaf in _canonical_skill_leaves(skill_ir, regions={"d"}).items()
        if region == "d"
    ]
    if isinstance(result, Mapping):
        return dict(result)
    if len(declared_output_leaves) == 1:
        key = _leaf_terminal_segment(declared_output_leaves[0]) or "result"
        return {key: result}
    return {"result": result}


def _runtime_output_leaves_for_step(skill_ir: Mapping[str, Any], result: Any) -> dict[tuple[str, str], SkillLeaf]:
    declared_output_leaves = {
        leaf.path: leaf
        for (region, _path), leaf in _canonical_skill_leaves(skill_ir, regions={"d"}).items()
        if region == "d"
    }
    runtime_leaves: dict[tuple[str, str], SkillLeaf] = {}
    if len(declared_output_leaves) == 1 and not isinstance(result, Mapping):
        template = next(iter(declared_output_leaves.values()))
        runtime_leaves[("d", template.path)] = _build_skill_leaf_with_value(template, result)
        return runtime_leaves

    if len(declared_output_leaves) == 1 and isinstance(result, Mapping):
        template = next(iter(declared_output_leaves.values()))
        template_segment = _normalized_semantic_key(_leaf_terminal_segment(template))
        if template_segment in {"result", "value", "output", "answer", "data", "item", "items"}:
            runtime_leaves[("d", template.path)] = _build_skill_leaf_with_value(template, result)

    if isinstance(result, Mapping):
        for key, value in dict(result).items():
            normalized_key = _normalized_semantic_key(key)
            matches = [
                leaf
                for leaf in declared_output_leaves.values()
                if _normalized_semantic_key(_leaf_terminal_segment(leaf)) == normalized_key
                or _normalized_semantic_key(leaf.semantic_label) == normalized_key
            ]
            if len(matches) == 1:
                template = matches[0]
                runtime_leaves[("d", template.path)] = _build_skill_leaf_with_value(template, value)

    body = _output_payload_for_skill_result(skill_ir, result)
    generic_leaves = normalize_skill_region_body(BoundaryShapeTerm.OUTPUT_VALUE, body)
    for leaf in generic_leaves:
        runtime_leaves.setdefault(("d", leaf.path), leaf)
    return runtime_leaves


def _condition_value(
    emitted_leaves_by_step: Mapping[str, dict[tuple[str, str], SkillLeaf]],
    condition: SkillCompositionCondition,
) -> Any:
    leaf = emitted_leaves_by_step.get(condition.source_step_id, {}).get(
        (collapse_ws(condition.source_region), collapse_ws(condition.source_path))
    )
    if leaf is None:
        raise ValueError("Condition references a missing emitted leaf.")
    return leaf.value


def _evaluate_condition_value(actual_value: Any, condition: SkillCompositionCondition) -> bool:
    operator = collapse_ws(condition.operator or "equals")
    if operator == "equals":
        return actual_value == condition.expected_value
    if operator == "not_equals":
        return actual_value != condition.expected_value
    if operator == "exists":
        return actual_value is not None
    if operator == "missing":
        return actual_value is None
    raise ValueError(f"Unsupported condition operator: {condition.operator}")


def propose_skill_leaf_bindings(
    source_skill: CanonicalSkillIR | Artifact | Mapping[str, Any],
    target_skill: CanonicalSkillIR | Artifact | Mapping[str, Any],
) -> list[SkillCompositionCandidate]:
    """
    High Level Purpose:
        In circumstances like planning skill composition, helps with enumerating candidate leaf-to-leaf bindings between one producer skill and one consumer skill.

    Reference to Theory:
        Supports the section-4.6 compatibility layer by making leaf-level composition explicit over canonical path ledgers instead of relying on prompt heuristics alone.

    Example Input Output:
        Input: `propose_skill_leaf_bindings(source_skill, target_skill)`
        Output: [SkillCompositionCandidate(source_region='d', source_path='/d/result', target_region='a', target_path='/a/text', status='mapper_required', reason='...')]

    Args:
        source_skill: Source skill or canonical IR.
        target_skill: Target skill or canonical IR.

    Returns:
        list[SkillCompositionCandidate]: Result produced by `propose_skill_leaf_bindings`.
    """
    source_leaves = _canonical_skill_leaves(source_skill, regions={"c", "c'", "d", "d'"})
    target_leaves = _canonical_skill_leaves(target_skill, regions={"a", "a'", "b", "b'"})
    candidates: list[SkillCompositionCandidate] = []
    for (source_region, source_path), source_leaf in source_leaves.items():
        for (target_region, target_path), target_leaf in target_leaves.items():
            status, reason = _binding_status_from_leaves(
                source_leaf,
                target_leaf,
                source_region=source_region,
                target_region=target_region,
            )
            candidates.append(
                SkillCompositionCandidate(
                    source_region=source_region,
                    source_path=source_path,
                    target_region=target_region,
                    target_path=target_path,
                    status=status,
                    reason=reason,
                )
            )
    status_order = {"exact": 0, "mapper_required": 1, "blocked": 2}
    return sorted(
        candidates,
        key=lambda item: (
            status_order.get(item.status, 99),
            item.target_region,
            item.target_path,
            item.source_region,
            item.source_path,
        ),
    )


def _constant_leaf_for_target(target_leaf: SkillLeaf, value: Any) -> SkillLeaf:
    return SkillLeaf(
        region=target_leaf.region,
        path=target_leaf.path,
        carrier_kind=target_leaf.carrier_kind,
        data_type=_leaf_data_type_for_constant(value),
        semantic_label=target_leaf.semantic_label,
        value=value,
        leaf_class=(
            SkillLeafClass.NULL
            if value is None
            else SkillLeafClass.COLLECTION
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
            else SkillLeafClass.SCALAR
        ),
    )


def analyze_skill_composition_plan(
    steps: Sequence[SkillCompositionStep | Mapping[str, Any]],
    *,
    root_inputs: Mapping[str, str] | None = None,
    root_references: Mapping[str, str] | None = None,
) -> SkillCompositionPlanAnalysis:
    """
    High Level Purpose:
        In circumstances like validating step-wise or branching skill plans, helps with checking explicit bindings, conditions, and permission envelopes over a skill sequence.

    Reference to Theory:
        Supports the staged composition layer by validating leaf-level bindings and permission envelopes directly against the canonical path ledger.

    Example Input Output:
        Input: `analyze_skill_composition_plan([SkillCompositionStep(step_id='read', skill=read_ir)])`
        Output: SkillCompositionPlanAnalysis(steps=[...], plan_authorities=['read'], blocked=True, unresolved_targets=[...])

    Args:
        steps: Planned skill steps.
        root_inputs: Named root value inputs available to the plan.
        root_references: Named root reference inputs available to the plan.

    Returns:
        SkillCompositionPlanAnalysis: Result produced by `analyze_skill_composition_plan`.
    """
    normalized_steps = _normalize_composition_steps(steps)
    root_input_types = {collapse_ws(str(key)): collapse_ws(str(value)) for key, value in dict(root_inputs or {}).items() if collapse_ws(str(key))}
    root_reference_types = {collapse_ws(str(key)): collapse_ws(str(value)) for key, value in dict(root_references or {}).items() if collapse_ws(str(key))}
    ir_by_step: dict[str, dict[str, Any]] = {}
    leaves_by_step: dict[str, dict[tuple[str, str], SkillLeaf]] = {}
    for step in normalized_steps:
        ir = _skill_ir_dict(step.skill)
        ir_by_step[step.step_id] = ir
        leaves_by_step[step.step_id] = _canonical_skill_leaves(step.skill)

    plan_authorities: set[str] = set()
    step_reports: list[dict[str, Any]] = []
    unresolved_targets: list[dict[str, Any]] = []
    blocked = False

    for step in normalized_steps:
        ir = ir_by_step[step.step_id]
        declaration = dict(ir.get("declaration", {})) if isinstance(ir.get("declaration", {}), Mapping) else {}
        plan_authorities.update(
            collapse_ws(str(item))
            for item in declaration.get("authorities_requested", [])
            if collapse_ws(str(item))
        )
        target_leaves = leaves_by_step[step.step_id]
        input_targets = {
            (region, path): leaf
            for (region, path), leaf in target_leaves.items()
            if region in {"a", "a'", "b", "b'"}
        }
        diagnostics: list[SkillBindingDiagnostic] = []
        bound_targets: set[tuple[str, str]] = set()
        for binding in step.bindings:
            target_key = (collapse_ws(binding.target_region), collapse_ws(binding.target_path))
            target_leaf = input_targets.get(target_key)
            if target_leaf is None:
                diagnostics.append(
                    SkillBindingDiagnostic(
                        step_id=step.step_id,
                        target_region=target_key[0],
                        target_path=target_key[1],
                        status="blocked",
                        source_kind="missing_target",
                        mapper_kind=_normalize_mapper_kind(binding),
                        reason="target leaf is not present in the step normalization ledger.",
                    )
                )
                blocked = True
                continue
            bound_targets.add(target_key)

            if binding.source_root_name:
                root_name = collapse_ws(binding.source_root_name)
                root_region = collapse_ws(binding.source_root_region or ("a'" if target_key[0].endswith("'") else "a"))
                root_type = root_reference_types.get(root_name, "") if root_region.endswith("'") else root_input_types.get(root_name, "")
                if not root_type:
                    diagnostics.append(
                        SkillBindingDiagnostic(
                            step_id=step.step_id,
                            target_region=target_key[0],
                            target_path=target_key[1],
                            status="blocked",
                            source_kind="root_input",
                            source_root_name=root_name,
                            source_root_region=root_region,
                            mapper_kind=_normalize_mapper_kind(binding),
                            reason="referenced root input is not declared for the plan.",
                        )
                    )
                    blocked = True
                    continue
                synthetic_source = SkillLeaf(
                    region=target_leaf.region,
                    path=f"/{root_region}/root/{root_name}",
                    carrier_kind=target_leaf.carrier_kind,
                    data_type=normalize_skill_leaf_data_type(root_type),
                    semantic_label=root_name,
                    value=root_name,
                    leaf_class=SkillLeafClass.REFERENCE if root_region.endswith("'") else SkillLeafClass.SCALAR,
                )
                status, reason = _binding_status_from_leaves(
                    synthetic_source,
                    target_leaf,
                    source_region=root_region,
                    target_region=target_key[0],
                )
                diagnostics.append(
                    SkillBindingDiagnostic(
                        step_id=step.step_id,
                        target_region=target_key[0],
                        target_path=target_key[1],
                        status=status,
                        source_kind="root_input",
                        source_root_name=root_name,
                        source_root_region=root_region,
                        mapper_kind=_normalize_mapper_kind(binding),
                        reason=reason,
                    )
                )
                blocked = blocked or status == "blocked"
                continue

            if binding.constant_value is not None:
                synthetic_source = _constant_leaf_for_target(target_leaf, binding.constant_value)
                source_region = collapse_ws(binding.source_region or ("a'" if target_key[0].endswith("'") else "a"))
                status, reason = _binding_status_from_leaves(
                    synthetic_source,
                    target_leaf,
                    source_region=source_region,
                    target_region=target_key[0],
                )
                diagnostics.append(
                    SkillBindingDiagnostic(
                        step_id=step.step_id,
                        target_region=target_key[0],
                        target_path=target_key[1],
                        status=status,
                        source_kind="constant",
                        source_region=source_region,
                        mapper_kind=_normalize_mapper_kind(binding),
                        reason=reason,
                    )
                )
                blocked = blocked or status == "blocked"
                continue

            source_step_id = collapse_ws(binding.source_step_id)
            source_region = collapse_ws(binding.source_region)
            source_path = collapse_ws(binding.source_path)
            source_leaf = leaves_by_step.get(source_step_id, {}).get((source_region, source_path))
            if source_leaf is None:
                diagnostics.append(
                    SkillBindingDiagnostic(
                        step_id=step.step_id,
                        target_region=target_key[0],
                        target_path=target_key[1],
                        status="blocked",
                        source_kind="step_output",
                        source_step_id=source_step_id,
                        source_region=source_region,
                        source_path=source_path,
                        mapper_kind=_normalize_mapper_kind(binding),
                        reason="source leaf is not present in the referenced step normalization ledger.",
                    )
                )
                blocked = True
                continue
            status, reason = _binding_status_from_leaves(
                source_leaf,
                target_leaf,
                source_region=source_region,
                target_region=target_key[0],
            )
            diagnostics.append(
                SkillBindingDiagnostic(
                    step_id=step.step_id,
                    target_region=target_key[0],
                    target_path=target_key[1],
                    status=status,
                    source_kind="step_output",
                    source_step_id=source_step_id,
                    source_region=source_region,
                    source_path=source_path,
                    mapper_kind=_normalize_mapper_kind(binding),
                    reason=reason,
                )
            )
            blocked = blocked or status == "blocked"

        for target_key, target_leaf in sorted(input_targets.items()):
            if target_key in bound_targets:
                continue
            unresolved = {
                "step_id": step.step_id,
                "target_region": target_key[0],
                "target_path": target_key[1],
                "semantic_label": target_leaf.semantic_label,
                "status": "unbound",
            }
            unresolved_targets.append(unresolved)
            diagnostics.append(
                SkillBindingDiagnostic(
                    step_id=step.step_id,
                    target_region=target_key[0],
                    target_path=target_key[1],
                    status="unbound",
                    source_kind="unbound",
                    reason="target leaf has no explicit binding in the plan.",
                )
            )

        condition_diagnostics: list[SkillConditionDiagnostic] = []
        for condition in list(step.run_if) + list(step.iterate_until):
            source_leaf = leaves_by_step.get(condition.source_step_id, {}).get(
                (collapse_ws(condition.source_region), collapse_ws(condition.source_path))
            )
            if source_leaf is None:
                blocked = True
                condition_diagnostics.append(
                    SkillConditionDiagnostic(
                        step_id=step.step_id,
                        status="blocked",
                        source_step_id=condition.source_step_id,
                        source_region=collapse_ws(condition.source_region),
                        source_path=collapse_ws(condition.source_path),
                        operator=collapse_ws(condition.operator or "equals"),
                        reason="condition references a missing source leaf.",
                    )
                )
                continue
            operator = collapse_ws(condition.operator or "equals")
            status = "exact" if operator in {"equals", "not_equals", "exists", "missing"} else "blocked"
            if status == "blocked":
                blocked = True
            condition_diagnostics.append(
                SkillConditionDiagnostic(
                    step_id=step.step_id,
                    status=status,
                    source_step_id=condition.source_step_id,
                    source_region=collapse_ws(condition.source_region),
                    source_path=collapse_ws(condition.source_path),
                    operator=operator,
                    reason="condition operator is supported." if status == "exact" else "condition operator is unsupported.",
                )
            )

        step_reports.append(
            {
                "step_id": step.step_id,
                "title": ir.get("title", ""),
                "branch_label": step.branch_label,
                "authorities_requested": sorted(
                    collapse_ws(str(item))
                    for item in declaration.get("authorities_requested", [])
                    if collapse_ws(str(item))
                ),
                "bindings": [json_safe(item) for item in diagnostics],
                "conditions": [json_safe(item) for item in condition_diagnostics],
            }
        )

    return SkillCompositionPlanAnalysis(
        steps=step_reports,
        plan_authorities=sorted(plan_authorities),
        blocked=blocked or bool(unresolved_targets),
        unresolved_targets=unresolved_targets,
    )


def execute_skill_composition_plan(
    steps: Sequence[SkillCompositionStep | Mapping[str, Any]],
    *,
    invoker: Callable[[str, dict[str, Any], dict[str, Any]], Any],
    root_inputs: Mapping[str, Any] | None = None,
    root_references: Mapping[str, Any] | None = None,
    max_iterations_per_step: int = 8,
    execution_observer: Callable[[SkillCompositionExecutionEvent], None] | None = None,
) -> SkillCompositionExecutionResult:
    """
    High Level Purpose:
        In circumstances like explicit skill-to-skill composition execution, helps with validating a composition plan, building mapped invocation payloads, and executing each step through one caller-supplied invoker.

    Reference to Theory:
        Supports the section-4.6 composition path by making mapper-backed leaf bindings executable and inspectable instead of leaving them as prompt-only intent.

    Example Input Output:
        Input: `execute_skill_composition_plan(steps=plan, invoker=invoke_skill, root_inputs={'mount': 'skill_input'})`
        Output: SkillCompositionExecutionResult(steps=[...], final_outputs_by_step={'read': {'result': 'hello'}})

    Args:
        steps: Planned composition steps.
        invoker: Callback invoked as `(step_id, canonical_skill_ir_dict, payload)`.
        root_inputs: Named root value inputs available to the plan.
        root_references: Named root reference inputs available to the plan.
        max_iterations_per_step: Maximum iterations for one iterative step.

    Returns:
        SkillCompositionExecutionResult: Result produced by `execute_skill_composition_plan`.
    """
    normalized_steps = _normalize_composition_steps(steps)
    input_type_hints = {
        collapse_ws(str(key)): _leaf_data_type_for_constant(value) or "String"
        for key, value in dict(root_inputs or {}).items()
        if collapse_ws(str(key))
    }
    reference_type_hints = {
        collapse_ws(str(key)): _leaf_data_type_for_constant(value) or "String"
        for key, value in dict(root_references or {}).items()
        if collapse_ws(str(key))
    }
    analysis = analyze_skill_composition_plan(
        normalized_steps,
        root_inputs=input_type_hints,
        root_references=reference_type_hints,
    )
    if analysis.blocked:
        raise ValueError(f"Skill composition plan is not executable: {json_safe(analysis.to_dict())}")

    root_input_values = {collapse_ws(str(key)): value for key, value in dict(root_inputs or {}).items() if collapse_ws(str(key))}
    root_reference_values = {collapse_ws(str(key)): value for key, value in dict(root_references or {}).items() if collapse_ws(str(key))}
    emitted_leaves_by_step: dict[str, dict[tuple[str, str], SkillLeaf]] = {}
    final_outputs_by_step: dict[str, Any] = {}
    execution_steps: list[dict[str, Any]] = []
    ir_by_step = {step.step_id: _skill_ir_dict(step.skill) for step in normalized_steps}
    target_leaves_by_step = {
        step.step_id: {
            key: leaf
            for key, leaf in _canonical_skill_leaves(step.skill).items()
            if key[0] in {"a", "a'", "b", "b'"}
        }
        for step in normalized_steps
    }

    for step in normalized_steps:
        ir = ir_by_step[step.step_id]
        iteration = 0
        while True:
            iteration += 1
            if iteration > max_iterations_per_step:
                raise ValueError(f"Skill composition step {step.step_id!r} exceeded max_iterations_per_step={max_iterations_per_step}.")

            condition_receipts: list[dict[str, Any]] = []
            should_run = True
            for condition in step.run_if:
                actual_value = _condition_value(emitted_leaves_by_step, condition)
                matched = _evaluate_condition_value(actual_value, condition)
                condition_receipts.append(
                    {
                        "kind": "run_if",
                        "source_step_id": condition.source_step_id,
                        "source_region": collapse_ws(condition.source_region),
                        "source_path": collapse_ws(condition.source_path),
                        "operator": collapse_ws(condition.operator or "equals"),
                        "expected_value": condition.expected_value,
                        "actual_value": actual_value,
                        "matched": matched,
                    }
                )
                if not matched:
                    should_run = False
            if not should_run:
                _emit_skill_composition_execution_event(
                    execution_observer,
                    SkillCompositionExecutionEvent(
                        kind="step_skipped",
                        step_id=step.step_id,
                        title=collapse_ws(str(ir.get("title", ""))),
                        status="skipped",
                        iteration=iteration,
                        branch_label=step.branch_label,
                        condition_receipts=json_safe(condition_receipts),
                        skipped_reason="run_if conditions were not satisfied.",
                    ),
                )
                execution_steps.append(
                    json_safe(
                        SkillCompositionStepExecutionRecord(
                            step_id=step.step_id,
                            title=collapse_ws(str(ir.get("title", ""))),
                            status="skipped",
                            iteration=iteration,
                            branch_label=step.branch_label,
                            condition_receipts=condition_receipts,
                            skipped_reason="run_if conditions were not satisfied.",
                        )
                    )
                )
                break

            bound_target_leaves: dict[str, list[SkillLeaf]] = {"a": [], "a'": [], "b": [], "b'": []}
            binding_receipts: list[dict[str, Any]] = []
            for binding in step.bindings:
                target_key = (collapse_ws(binding.target_region), collapse_ws(binding.target_path))
                target_leaf = target_leaves_by_step[step.step_id][target_key]
                source_kind = ""
                source_value: Any = None
                source_leaf = None
                source_region = ""
                if binding.source_root_name:
                    source_kind = "root_input"
                    root_name = collapse_ws(binding.source_root_name)
                    source_region = collapse_ws(binding.source_root_region or ("a'" if target_key[0].endswith("'") else "a"))
                    source_value = (
                        root_reference_values.get(root_name)
                        if source_region.endswith("'")
                        else root_input_values.get(root_name)
                    )
                    source_leaf = SkillLeaf(
                        region=target_leaf.region,
                        path=f"/{source_region}/root/{root_name}",
                        carrier_kind=target_leaf.carrier_kind,
                        data_type=normalize_skill_leaf_data_type(
                            (
                                reference_type_hints.get(root_name, "")
                                if source_region.endswith("'")
                                else input_type_hints.get(root_name, "")
                            )
                        ),
                        semantic_label=root_name,
                        value=source_value,
                        leaf_class=SkillLeafClass.REFERENCE if source_region.endswith("'") else SkillLeafClass.SCALAR,
                    )
                elif binding.constant_value is not None:
                    source_kind = "constant"
                    source_region = collapse_ws(binding.source_region or ("a'" if target_key[0].endswith("'") else "a"))
                    source_value = binding.constant_value
                    source_leaf = _constant_leaf_for_target(target_leaf, source_value)
                else:
                    source_kind = "step_output"
                    source_region = collapse_ws(binding.source_region)
                    source_key = (source_region, collapse_ws(binding.source_path))
                    source_leaf = emitted_leaves_by_step.get(collapse_ws(binding.source_step_id), {}).get(source_key)
                    if source_leaf is None:
                        raise ValueError(
                            f"Step {step.step_id!r} references unavailable source leaf {source_key!r} from {binding.source_step_id!r}."
                        )
                    source_value = source_leaf.value

                allowed_mappers = _allowed_mapper_kinds(source_leaf, target_leaf)
                mapper_kind = _normalize_mapper_kind(binding)
                if mapper_kind not in allowed_mappers:
                    raise ValueError(
                        f"Mapper {mapper_kind!r} is not valid for binding {binding.source_step_id or binding.source_root_name or 'constant'} -> {binding.target_path}; allowed={sorted(allowed_mappers)}"
                    )
                mapped_value = _apply_mapper_kind(
                    source_value,
                    mapper_kind,
                    field_name=_mapper_field_name(binding),
                )
                mapped_leaf = _build_skill_leaf_with_value(target_leaf, mapped_value)
                bound_target_leaves[target_key[0]].append(mapped_leaf)
                binding_receipts.append(
                    {
                        "target_region": target_key[0],
                        "target_path": target_key[1],
                        "source_kind": source_kind,
                        "source_step_id": collapse_ws(binding.source_step_id),
                        "source_region": source_region,
                        "source_path": collapse_ws(binding.source_path),
                        "source_root_name": collapse_ws(binding.source_root_name),
                        "mapper_kind": mapper_kind,
                        "mapper_field": _mapper_field_name(binding),
                        "source_value": json_safe(source_value),
                        "mapped_value": json_safe(mapped_value),
                    }
                )

            payload: dict[str, Any] = {}
            for region_name in ("a", "a'", "b", "b'"):
                if not bound_target_leaves[region_name]:
                    continue
                body = _single_region_payload_from_leaves(bound_target_leaves[region_name], region_name)
                if isinstance(body, Mapping):
                    payload.update(dict(body))
            _emit_skill_composition_execution_event(
                execution_observer,
                SkillCompositionExecutionEvent(
                    kind="step_started",
                    step_id=step.step_id,
                    title=collapse_ws(str(ir.get("title", ""))),
                    status="started",
                    iteration=iteration,
                    branch_label=step.branch_label,
                    input_payload=json_safe(payload),
                    binding_receipts=json_safe(binding_receipts),
                    condition_receipts=json_safe(condition_receipts),
                ),
            )
            try:
                result = invoker(step.step_id, ir, payload)
            except Exception as exc:
                result_payload = getattr(exc, "result", None)
                normalized_result_payload = (
                    json_safe(dict(result_payload))
                    if isinstance(result_payload, Mapping)
                    else None
                )
                failure_status = (
                    collapse_ws(str(result_payload.get("status", "")))
                    if isinstance(result_payload, Mapping)
                    else ""
                )
                failure_kind = (
                    "step_blocked"
                    if failure_status.casefold() in {"approval_required", "blocked"}
                    else "step_failed"
                )
                _emit_skill_composition_execution_event(
                    execution_observer,
                    SkillCompositionExecutionEvent(
                        kind=failure_kind,
                        step_id=step.step_id,
                        title=collapse_ws(str(ir.get("title", ""))),
                        status=failure_status or "error",
                        iteration=iteration,
                        branch_label=step.branch_label,
                        input_payload=json_safe(payload),
                        binding_receipts=json_safe(binding_receipts),
                        condition_receipts=json_safe(condition_receipts),
                        error=str(exc),
                        result_payload=normalized_result_payload,
                    ),
                )
                raise
            normalized_output = _output_payload_for_skill_result(ir, result)
            final_outputs_by_step[step.step_id] = normalized_output
            emitted_leaves_by_step[step.step_id] = _runtime_output_leaves_for_step(ir, result)

            iterate_receipts: list[dict[str, Any]] = []
            continue_iteration = False
            for condition in step.iterate_until:
                actual_value = _condition_value(emitted_leaves_by_step, condition)
                matched = _evaluate_condition_value(actual_value, condition)
                iterate_receipts.append(
                    {
                        "kind": "iterate_until",
                        "source_step_id": condition.source_step_id,
                        "source_region": collapse_ws(condition.source_region),
                        "source_path": collapse_ws(condition.source_path),
                        "operator": collapse_ws(condition.operator or "equals"),
                        "expected_value": condition.expected_value,
                        "actual_value": actual_value,
                        "matched": matched,
                    }
                )
                if not matched:
                    continue_iteration = True

            _emit_skill_composition_execution_event(
                execution_observer,
                SkillCompositionExecutionEvent(
                    kind="step_completed",
                    step_id=step.step_id,
                    title=collapse_ws(str(ir.get("title", ""))),
                    status="ok",
                    iteration=iteration,
                    branch_label=step.branch_label,
                    input_payload=json_safe(payload),
                    output_payload=json_safe(normalized_output),
                    binding_receipts=json_safe(binding_receipts),
                    condition_receipts=json_safe(condition_receipts + iterate_receipts),
                ),
            )
            execution_steps.append(
                json_safe(
                    SkillCompositionStepExecutionRecord(
                        step_id=step.step_id,
                        title=collapse_ws(str(ir.get("title", ""))),
                        status="ok",
                        iteration=iteration,
                        branch_label=step.branch_label,
                        input_payload=json_safe(payload),
                        output_payload=json_safe(normalized_output),
                        binding_receipts=binding_receipts,
                        condition_receipts=condition_receipts + iterate_receipts,
                    )
                )
            )
            if not continue_iteration:
                break

    return SkillCompositionExecutionResult(
        steps=execution_steps,
        plan_authorities=analysis.plan_authorities,
        final_outputs_by_step=json_safe(final_outputs_by_step),
    )
