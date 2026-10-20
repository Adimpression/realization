# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from capability_runtime import runtime_skill_declaration_for_artifact
from semantic_text import collapse_ws
from skill_composition import analyze_skill_composition_plan, propose_skill_leaf_bindings
from skill_ir import canonical_skill_ir_from_artifact
from skill_leaf_types import SkillLeaf
from skill_path_notation import parse_canonical_skill_path
from workstation.skills.core.direct_composition import (
    _skill_action_bonus,
    derive_workstation_invocation_payload_from_prompt,
    derive_workstation_partial_invocation_payload_from_prompt,
)
from workstation.foundation.models import WorkstationSession
from workstation.contracts.shell_prompt_routing import match_workstation_shell_utility_prompt
from workstation.skills.core.skill_invocation import resolve_workstation_skill
from workstation.skills.core.skill_management import workstation_prompt_skill_shortlist_payload


_PIPELINE_PATTERN = re.compile(
    r"\b(?:and then|then|after that|using the output|using the result|feed(?: it)? into|pipe(?: it)? into)\b",
    flags=re.IGNORECASE,
)
_PIPELINE_SPLIT_PATTERN = re.compile(
    r"\b(?:and then|then|after that|using the output|using the result|feed(?: it)? into|pipe(?: it)? into)\b",
    flags=re.IGNORECASE,
)
_PIPELINE_ACTIONS = {"read", "write", "append", "find", "load", "render", "extract", "search", "download", "poll"}
_GENERIC_LEAF_NAMES = {"result", "value", "output", "answer", "input", "item", "items", "data"}
_DISALLOWED_AUTO_MAPPED_INPUT_NAMES = {
    "mount",
    "relative_path",
    "path",
    "source_mount",
    "source_relative_path",
    "destination_mount",
    "destination_relative_path",
    "destination_path",
    "output_path",
    "output_mount",
    "url",
    "bucket",
    "key",
    "blob_name",
    "channel",
    "repo_name",
    "token",
    "api_key",
}
_MAX_AUTO_COMPOSE_STEPS = 4
_MAX_CANDIDATES_PER_CLAUSE = 3
_PLANNER_ACTION_SYNONYMS: dict[str, set[str]] = {
    "append": {"append"},
    "checksum": {"checksum"},
    "copy": {"copy"},
    "delete": {"delete", "remove"},
    "download": {"download", "fetch"},
    "extract": {"extract"},
    "find": {"find", "search"},
    "list": {"list"},
    "move": {"move"},
    "poll": {"poll"},
    "read": {"read"},
    "render": {"render"},
    "search": {"search", "find"},
    "write": {"write"},
}


def _prompt_implies_skill_pipeline(prompt: str) -> bool:
    normalized = collapse_ws(str(prompt))
    if not normalized:
        return False
    if _PIPELINE_PATTERN.search(normalized):
        return True
    prompt_tokens = set(re.findall(r"[a-z0-9_]+", normalized.casefold()))
    if "and" not in prompt_tokens:
        return False
    return len(_PIPELINE_ACTIONS.intersection(prompt_tokens)) >= 2


def _planner_primary_action(prompt: str) -> str:
    for token in re.findall(r"[a-z0-9_]+", collapse_ws(str(prompt)).casefold()):
        if token in _PLANNER_ACTION_SYNONYMS:
            return token
    return ""


def _planner_clause_skill_bonus(*, clause: str, skill_title: str) -> int:
    bonus = _skill_action_bonus(prompt=clause, skill_title=skill_title)
    primary_action = _planner_primary_action(clause)
    if not primary_action:
        return bonus
    title_tokens = set(re.findall(r"[a-z0-9_]+", collapse_ws(str(skill_title)).casefold()))
    matching_tokens = _PLANNER_ACTION_SYNONYMS.get(primary_action, {primary_action})
    strong_title_actions = set(_PLANNER_ACTION_SYNONYMS).intersection(title_tokens)
    if strong_title_actions.intersection(matching_tokens):
        bonus += 8
    elif strong_title_actions:
        bonus -= 8
    return bonus


def _scored_shortlist_for_prompt(*, session: WorkstationSession, prompt: str, limit: int) -> list[dict[str, Any]]:
    shortlist = workstation_prompt_skill_shortlist_payload(session=session, prompt=prompt, limit=limit)
    raw_skills = list(shortlist.get("skills", []))
    scored_skills: list[dict[str, Any]] = []
    for raw_skill in raw_skills:
        if not isinstance(raw_skill, Mapping):
            continue
        item = dict(raw_skill)
        title = collapse_ws(str(item.get("title", "")))
        if not title:
            continue
        item["_effective_score"] = int(item.get("score", 0) or 0) + _skill_action_bonus(prompt=prompt, skill_title=title)
        scored_skills.append(item)
    scored_skills.sort(key=lambda item: int(item.get("_effective_score", 0) or 0), reverse=True)
    return scored_skills


def _split_prompt_pipeline_clauses(prompt: str) -> list[str] | None:
    normalized = collapse_ws(str(prompt))
    if not normalized:
        return None
    if _PIPELINE_SPLIT_PATTERN.search(normalized):
        parts = [
            collapse_ws(part)
            for part in _PIPELINE_SPLIT_PATTERN.split(normalized)
            if collapse_ws(part)
        ]
        if len(parts) >= 2:
            return parts[:_MAX_AUTO_COMPOSE_STEPS]
    and_parts = re.split(r"\band\b", normalized, maxsplit=1, flags=re.IGNORECASE)
    if len(and_parts) != 2:
        return None
    left = collapse_ws(and_parts[0])
    right = collapse_ws(and_parts[1])
    if not left or not right:
        return None
    left_tokens = set(re.findall(r"[a-z0-9_]+", left.casefold()))
    right_tokens = set(re.findall(r"[a-z0-9_]+", right.casefold()))
    if not _PIPELINE_ACTIONS.intersection(left_tokens):
        return None
    if not _PIPELINE_ACTIONS.intersection(right_tokens):
        return None
    return [left, right]


@dataclass(frozen=True)
class _ResolvedPlannerSkillCandidate:
    title: str
    skill: Any
    effective_score: int
    clause_bonus: int
    inputs: dict[str, str]
    input_targets: dict[str, dict[str, str]]
    required_inputs: set[str]


@dataclass(frozen=True)
class _BuiltPlannerStep:
    step_payload: dict[str, Any]
    analysis_payload: dict[str, Any]
    root_inputs: dict[str, Any]
    root_references: dict[str, Any]
    exact_count: int
    mapper_count: int
    skill_title: str
    skill: Any


@dataclass(frozen=True)
class _PlannerConditionSpec:
    field_name: str
    operator: str
    expected_value: Any = None


@dataclass(frozen=True)
class _PlannerIterationSpec:
    field_name: str
    operator: str
    expected_value: Any = None


def _invert_condition_spec(condition_spec: _PlannerConditionSpec) -> _PlannerConditionSpec | None:
    inverse_operator = {
        "equals": "not_equals",
        "not_equals": "equals",
        "exists": "missing",
        "missing": "exists",
    }.get(collapse_ws(str(condition_spec.operator or "")))
    if not inverse_operator:
        return None
    return _PlannerConditionSpec(
        field_name=condition_spec.field_name,
        operator=inverse_operator,
        expected_value=condition_spec.expected_value,
    )


def _skill_ir_dict(skill: Any) -> dict[str, Any]:
    if isinstance(skill, Mapping):
        payload = dict(skill)
        if {"artifact_id", "title", "schema", "kind", "normalization"}.issubset(payload.keys()):
            return payload
    return canonical_skill_ir_from_artifact(skill).to_dict()


def _normalized_name(value: str) -> str:
    return collapse_ws(str(value)).casefold()


def _leaf_terminal_segment(path: str) -> str:
    _region, segments = parse_canonical_skill_path(path)
    if not segments:
        return ""
    return collapse_ws(str(segments[-1]))


def _skill_input_mapping(skill: Any) -> dict[str, str]:
    declaration = runtime_skill_declaration_for_artifact(skill)
    raw_inputs = declaration.get("inputs", {})
    if not isinstance(raw_inputs, Mapping):
        return {}
    return {
        collapse_ws(str(name)): collapse_ws(str(description))
        for name, description in dict(raw_inputs).items()
        if collapse_ws(str(name))
    }


def _required_input_names(skill: Any) -> list[str]:
    required: list[str] = []
    for name, description in _skill_input_mapping(skill).items():
        if not description or "required" in description.casefold():
            required.append(name)
    return required


def _input_leaf_targets(skill: Any) -> dict[str, dict[str, str]]:
    ir = _skill_ir_dict(skill)
    normalization = dict(ir.get("normalization", {})) if isinstance(ir.get("normalization", {}), Mapping) else {}
    regions = dict(normalization.get("regions", {})) if isinstance(normalization.get("regions", {}), Mapping) else {}
    declared_inputs = _skill_input_mapping(skill)
    candidate_leaves: list[tuple[str, SkillLeaf]] = []
    for region_name, payload in regions.items():
        normalized_region = collapse_ws(str(region_name))
        if normalized_region not in {"a", "a'", "b", "b'"}:
            continue
        raw_leaves = payload.get("leaves", []) if isinstance(payload, Mapping) else []
        if not isinstance(raw_leaves, list):
            continue
        for item in raw_leaves:
            if isinstance(item, Mapping):
                candidate_leaves.append((normalized_region, SkillLeaf.from_dict(dict(item))))
    targets: dict[str, dict[str, str]] = {}
    for input_name in declared_inputs:
        normalized_input = _normalized_name(input_name)
        matches = [
            (region_name, leaf.path)
            for region_name, leaf in candidate_leaves
            if normalized_input
            and normalized_input in {
                _normalized_name(_leaf_terminal_segment(leaf.path)),
                _normalized_name(leaf.semantic_label),
            }
        ]
        if len(matches) == 1:
            region_name, path = matches[0]
            targets[input_name] = {
                "target_region": region_name,
                "target_path": path,
            }
    return targets


def _default_mapper_payload(
    *,
    candidate_status: str,
    candidate_reason: str,
    source_path: str,
    target_path: str,
) -> dict[str, Any] | None:
    normalized_status = collapse_ws(str(candidate_status)).casefold()
    if normalized_status == "exact":
        return {"kind": "identity"}
    if normalized_status != "mapper_required":
        return None
    source_segment = _normalized_name(_leaf_terminal_segment(source_path))
    target_segment = _normalized_name(_leaf_terminal_segment(target_path))
    if source_segment in _GENERIC_LEAF_NAMES and target_segment and target_segment not in _GENERIC_LEAF_NAMES:
        return {"kind": "project_field", "field": target_segment}
    if "differ in multiplicity" in candidate_reason.casefold() or "primitive family" in candidate_reason.casefold():
        return {"kind": "first_item"}
    return {"kind": "rename"}


def _root_binding_payload(
    *,
    step_id: str,
    payload: Mapping[str, Any],
    input_targets: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]] | None:
    root_inputs: dict[str, Any] = {}
    root_references: dict[str, Any] = {}
    bindings: list[dict[str, Any]] = []
    for input_name, value in payload.items():
        target = input_targets.get(collapse_ws(str(input_name)))
        if target is None:
            return None
        root_name = f"{step_id}_{collapse_ws(str(input_name))}"
        target_region = collapse_ws(str(target.get("target_region", "")))
        source_root_region = "a'" if target_region.endswith("'") else "a"
        if source_root_region.endswith("'"):
            root_references[root_name] = value
        else:
            root_inputs[root_name] = value
        bindings.append(
            {
                "target_region": target_region,
                "target_path": collapse_ws(str(target.get("target_path", ""))),
                "source_root_name": root_name,
                "source_root_region": source_root_region,
            }
        )
    return root_inputs, root_references, bindings


def _parse_condition_literal(value: str) -> Any:
    normalized = collapse_ws(str(value)).rstrip(".,;:")
    if not normalized:
        return ""
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"`", "'", '"'}:
        normalized = normalized[1:-1]
    normalized = collapse_ws(str(normalized)).rstrip(".,;:")
    lowered = normalized.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    if re.fullmatch(r"-?[0-9]+", normalized):
        return int(normalized)
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", normalized):
        return float(normalized)
    return normalized


def _split_clause_condition(clause: str) -> tuple[_PlannerConditionSpec | None, str]:
    normalized = collapse_ws(str(clause))
    if not normalized:
        return None, ""
    exists_match = re.match(
        r"^if\s+([A-Za-z_][A-Za-z0-9_\- ]*?)\s+(exists|is present)\s*,\s*(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if exists_match:
        return (
            _PlannerConditionSpec(
                field_name=collapse_ws(str(exists_match.group(1))),
                operator="exists",
                expected_value=None,
            ),
            collapse_ws(str(exists_match.group(3))),
        )
    equals_match = re.match(
        r"^if\s+([A-Za-z_][A-Za-z0-9_\- ]*?)\s+(?:is|equals)\s+(.+?)\s*,\s*(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if equals_match:
        return (
            _PlannerConditionSpec(
                field_name=collapse_ws(str(equals_match.group(1))),
                operator="equals",
                expected_value=_parse_condition_literal(str(equals_match.group(2))),
            ),
            collapse_ws(str(equals_match.group(3))),
        )
    return None, normalized


def _split_clause_iteration(clause: str) -> tuple[_PlannerIterationSpec | None, str]:
    normalized = collapse_ws(str(clause))
    if not normalized:
        return None, ""
    exists_match = re.match(
        r"^(repeat\s+|keep\s+|continue\s+)?(.+?)\s+until\s+([A-Za-z_][A-Za-z0-9_\- ]*?)\s+(exists|is present)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if exists_match:
        return (
            _PlannerIterationSpec(
                field_name=collapse_ws(str(exists_match.group(3))),
                operator="exists",
                expected_value=None,
            ),
            collapse_ws(str(exists_match.group(2))),
        )
    equals_match = re.match(
        r"^(repeat\s+|keep\s+|continue\s+)?(.+?)\s+until\s+([A-Za-z_][A-Za-z0-9_\- ]*?)\s+(?:is|equals)\s+(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if equals_match:
        return (
            _PlannerIterationSpec(
                field_name=collapse_ws(str(equals_match.group(3))),
                operator="equals",
                expected_value=_parse_condition_literal(str(equals_match.group(4))),
            ),
            collapse_ws(str(equals_match.group(2))),
        )
    return None, normalized


def _split_clause_else_branch(clause: str) -> tuple[str, str]:
    normalized = collapse_ws(str(clause))
    if not normalized:
        return "", ""
    else_match = re.match(
        r"^(.+?)(?:,\s*|\s+)(?:otherwise|else)\s+(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if not else_match:
        return normalized, ""
    primary_clause = collapse_ws(str(else_match.group(1)))
    else_clause = collapse_ws(str(else_match.group(2)))
    return primary_clause, else_clause


def _type_hint_for_value(value: Any) -> str:
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "Int"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, (bytes, bytearray)):
        return "Bytes"
    if isinstance(value, list):
        if not value:
            return "Strings"
        first = _type_hint_for_value(value[0])
        repeated = {
            "String": "Strings",
            "Bytes": "Bytess",
            "Int": "Ints",
            "Boolean": "Bools",
            "Float": "Floats",
        }
        return repeated.get(first, "Strings")
    return "String"


def _resolved_candidates_for_clause(
    *,
    scored_skills: list[dict[str, Any]],
    clause: str,
    skill_store_path: str,
) -> list[_ResolvedPlannerSkillCandidate]:
    candidates: list[_ResolvedPlannerSkillCandidate] = []
    for item in scored_skills:
        title = collapse_ws(str(item.get("title", "")))
        if not title:
            continue
        clause_bonus = _planner_clause_skill_bonus(clause=clause, skill_title=title)
        if clause_bonus <= 0:
            continue
        resolved = resolve_workstation_skill(skill_title=title, skill_store_path=skill_store_path)
        if resolved is None:
            continue
        skill, _metadata = resolved
        inputs = _skill_input_mapping(skill)
        input_targets = _input_leaf_targets(skill)
        if inputs and not input_targets:
            continue
        candidates.append(
            _ResolvedPlannerSkillCandidate(
                title=title,
                skill=skill,
                effective_score=int(item.get("_effective_score", 0) or 0),
                clause_bonus=clause_bonus,
                inputs=inputs,
                input_targets=input_targets,
                required_inputs={
                    collapse_ws(str(name))
                    for name in _required_input_names(skill)
                    if collapse_ws(str(name))
                },
            )
        )
    candidates.sort(
        key=lambda item: (item.clause_bonus, item.effective_score),
        reverse=True,
    )
    return candidates[:_MAX_CANDIDATES_PER_CLAUSE]


def _candidate_mappings_from_prior_steps(
    *,
    prior_steps: list[_BuiltPlannerStep],
    target_step_id: str,
    target_skill: Any,
    target_input_targets: Mapping[str, Mapping[str, str]],
    root_bound_names: set[str],
) -> tuple[list[dict[str, Any]], int, int] | None:
    reverse_target_lookup = {
        (collapse_ws(str(target.get("target_region", ""))), collapse_ws(str(target.get("target_path", "")))): input_name
        for input_name, target in target_input_targets.items()
    }
    all_candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for reverse_index, prior_step in enumerate(reversed(prior_steps)):
        source_step_id = collapse_ws(str(prior_step.step_payload.get("step_id", "")))
        if not source_step_id:
            continue
        for candidate in propose_skill_leaf_bindings(prior_step.skill, target_skill):
            target_name = reverse_target_lookup.get((candidate.target_region, candidate.target_path), "")
            normalized_target_name = collapse_ws(str(target_name))
            if not normalized_target_name:
                continue
            if normalized_target_name in root_bound_names:
                continue
            if normalized_target_name.casefold() in _DISALLOWED_AUTO_MAPPED_INPUT_NAMES:
                continue
            mapper_payload = _default_mapper_payload(
                candidate_status=candidate.status,
                candidate_reason=candidate.reason,
                source_path=candidate.source_path,
                target_path=candidate.target_path,
            )
            if mapper_payload is None:
                continue
            status_rank = 0 if candidate.status == "exact" else 1
            mapping_payload = {
                "target_region": candidate.target_region,
                "target_path": candidate.target_path,
                "source_step_id": source_step_id,
                "source_region": candidate.source_region,
                "source_path": candidate.source_path,
                "mapper": mapper_payload,
            }
            all_candidates.append((status_rank, reverse_index, normalized_target_name, mapping_payload))
    if not all_candidates:
        return None
    all_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    chosen_names: set[str] = set()
    chosen_mappings: list[dict[str, Any]] = []
    exact_count = 0
    mapper_count = 0
    for status_rank, _reverse_index, normalized_target_name, mapping_payload in all_candidates:
        if normalized_target_name in chosen_names:
            continue
        chosen_names.add(normalized_target_name)
        chosen_mappings.append(mapping_payload)
        if status_rank == 0:
            exact_count += 1
        else:
            mapper_count += 1
    return chosen_mappings, exact_count, mapper_count


def _build_root_bound_step(
    *,
    step_id: str,
    skill_title: str,
    skill: Any,
    payload: Mapping[str, Any],
    input_targets: Mapping[str, Mapping[str, str]],
    normalized_prompt: str,
    branch_label: str = "",
) -> _BuiltPlannerStep | None:
    root_payload = _root_binding_payload(
        step_id=step_id,
        payload=payload,
        input_targets=input_targets,
    )
    if root_payload is None:
        return None
    root_inputs, root_references, bindings = root_payload
    step_payload = {
        "step_id": step_id,
        "skill_title": skill_title,
        "semantic_unit": normalized_prompt,
        "bindings": bindings,
    }
    if branch_label:
        step_payload["branch_label"] = branch_label
    analysis_payload = {
        "step_id": step_id,
        "skill": _skill_ir_dict(skill),
        "bindings": bindings,
    }
    if branch_label:
        analysis_payload["branch_label"] = branch_label
    return _BuiltPlannerStep(
        step_payload=step_payload,
        analysis_payload=analysis_payload,
        root_inputs=root_inputs,
        root_references=root_references,
        exact_count=0,
        mapper_count=0,
        skill_title=skill_title,
        skill=skill,
    )


def _condition_binding_from_prior_steps(
    *,
    prior_steps: list[_BuiltPlannerStep],
    condition_spec: _PlannerConditionSpec,
) -> dict[str, Any] | None:
    normalized_field = _normalized_name(condition_spec.field_name)
    if not normalized_field:
        return None
    for prior_step in reversed(prior_steps):
        candidate_matches: list[tuple[int, SkillLeaf]] = []
        for (region_name, _path), leaf in _canonical_skill_output_leaves(prior_step.skill).items():
            terminal_name = _normalized_name(_leaf_terminal_segment(leaf.path))
            semantic_name = _normalized_name(leaf.semantic_label)
            if terminal_name == normalized_field:
                candidate_matches.append((0, leaf))
            elif semantic_name == normalized_field:
                candidate_matches.append((1, leaf))
            elif normalized_field in {terminal_name, semantic_name}:
                candidate_matches.append((2, leaf))
            else:
                continue
        if not candidate_matches:
            continue
        candidate_matches.sort(key=lambda item: (item[0], item[1].path))
        matched_leaf = candidate_matches[0][1]
        payload = {
            "source_step_id": collapse_ws(str(prior_step.step_payload.get("step_id", ""))),
            "source_region": "d" if not matched_leaf.path.startswith("/d'/") else "d'",
            "source_path": matched_leaf.path,
            "operator": condition_spec.operator,
        }
        if condition_spec.operator in {"equals", "not_equals"}:
            payload["expected_value"] = condition_spec.expected_value
        return payload
    return None


def _canonical_skill_output_leaves(skill: Any) -> dict[tuple[str, str], SkillLeaf]:
    ir = _skill_ir_dict(skill)
    normalization = dict(ir.get("normalization", {})) if isinstance(ir.get("normalization", {}), Mapping) else {}
    regions = dict(normalization.get("regions", {})) if isinstance(normalization.get("regions", {}), Mapping) else {}
    leaves: dict[tuple[str, str], SkillLeaf] = {}
    for region_name, payload in regions.items():
        normalized_region = collapse_ws(str(region_name))
        if normalized_region not in {"d", "d'"}:
            continue
        raw_leaves = payload.get("leaves", []) if isinstance(payload, Mapping) else []
        if not isinstance(raw_leaves, list):
            continue
        for item in raw_leaves:
            if not isinstance(item, Mapping):
                continue
            leaf = SkillLeaf.from_dict(dict(item))
            leaves[(normalized_region, leaf.path)] = leaf
    return leaves


def _iteration_binding_for_current_step(
    *,
    step_id: str,
    skill: Any,
    iteration_spec: _PlannerIterationSpec,
) -> dict[str, Any] | None:
    normalized_field = _normalized_name(iteration_spec.field_name)
    if not normalized_field:
        return None
    candidate_matches: list[tuple[int, SkillLeaf]] = []
    for (_region_name, _path), leaf in _canonical_skill_output_leaves(skill).items():
        terminal_name = _normalized_name(_leaf_terminal_segment(leaf.path))
        semantic_name = _normalized_name(leaf.semantic_label)
        if terminal_name == normalized_field:
            candidate_matches.append((0, leaf))
        elif semantic_name == normalized_field:
            candidate_matches.append((1, leaf))
        else:
            continue
    if not candidate_matches:
        return None
    candidate_matches.sort(key=lambda item: (item[0], item[1].path))
    matched_leaf = candidate_matches[0][1]
    payload = {
        "source_step_id": step_id,
        "source_region": "d" if not matched_leaf.path.startswith("/d'/") else "d'",
        "source_path": matched_leaf.path,
        "operator": iteration_spec.operator,
    }
    if iteration_spec.operator in {"equals", "not_equals"}:
        payload["expected_value"] = iteration_spec.expected_value
    return payload


def _build_pipeline_step(
    *,
    step_id: str,
    clause: str,
    candidate: _ResolvedPlannerSkillCandidate,
    prior_steps: list[_BuiltPlannerStep],
    normalized_prompt: str,
    condition_spec: _PlannerConditionSpec | None = None,
    iteration_spec: _PlannerIterationSpec | None = None,
    branch_label: str = "",
) -> _BuiltPlannerStep | None:
    if not prior_steps:
        if condition_spec is not None:
            return None
        full_payload = derive_workstation_invocation_payload_from_prompt(
            inputs=candidate.inputs,
            prompt=clause,
            skill_title=candidate.title,
        )
        if full_payload is None or not isinstance(full_payload, Mapping):
            return None
        built = _build_root_bound_step(
            step_id=step_id,
            skill_title=candidate.title,
            skill=candidate.skill,
            payload=full_payload,
            input_targets=candidate.input_targets,
            normalized_prompt=normalized_prompt,
            branch_label=branch_label,
        )
        if built is None:
            return None
        bound_names = {
            collapse_ws(str(name))
            for name in full_payload.keys()
            if collapse_ws(str(name))
        }
        if candidate.required_inputs - bound_names:
            return None
        return built

    partial_payload = derive_workstation_partial_invocation_payload_from_prompt(
        inputs=candidate.inputs,
        prompt=clause,
        skill_title=candidate.title,
    )
    if partial_payload is None:
        partial_payload = {}
    if not isinstance(partial_payload, Mapping):
        return None
    built = _build_root_bound_step(
        step_id=step_id,
        skill_title=candidate.title,
        skill=candidate.skill,
        payload=partial_payload,
        input_targets=candidate.input_targets,
        normalized_prompt=normalized_prompt,
        branch_label=branch_label,
    )
    if built is None:
        return None
    root_bound_names = {
        collapse_ws(str(name))
        for name in partial_payload.keys()
        if collapse_ws(str(name))
    }
    candidate_mappings = _candidate_mappings_from_prior_steps(
        prior_steps=prior_steps,
        target_step_id=step_id,
        target_skill=candidate.skill,
        target_input_targets=candidate.input_targets,
        root_bound_names=root_bound_names,
    )
    chosen_mappings: list[dict[str, Any]] = []
    exact_count = 0
    mapper_count = 0
    if candidate_mappings is not None:
        chosen_mappings, exact_count, mapper_count = candidate_mappings
    chosen_target_names = {
        collapse_ws(str(name))
        for name, target in candidate.input_targets.items()
        if any(
            collapse_ws(str(target.get("target_region", ""))) == collapse_ws(str(binding.get("target_region", "")))
            and collapse_ws(str(target.get("target_path", ""))) == collapse_ws(str(binding.get("target_path", "")))
            for binding in chosen_mappings
        )
    }
    if candidate.required_inputs - root_bound_names - chosen_target_names:
        return None
    step_payload = dict(built.step_payload)
    step_payload["bindings"] = [*built.step_payload["bindings"], *chosen_mappings]
    analysis_payload = dict(built.analysis_payload)
    analysis_payload["bindings"] = [*built.analysis_payload["bindings"], *chosen_mappings]
    if condition_spec is not None:
        condition_payload = _condition_binding_from_prior_steps(
            prior_steps=prior_steps,
            condition_spec=condition_spec,
        )
        if condition_payload is None:
            return None
        step_payload["run_if"] = [condition_payload]
        analysis_payload["run_if"] = [condition_payload]
    if iteration_spec is not None:
        iteration_payload = _iteration_binding_for_current_step(
            step_id=step_id,
            skill=candidate.skill,
            iteration_spec=iteration_spec,
        )
        if iteration_payload is None:
            return None
        step_payload["iterate_until"] = [iteration_payload]
        analysis_payload["iterate_until"] = [iteration_payload]
    return _BuiltPlannerStep(
        step_payload=step_payload,
        analysis_payload=analysis_payload,
        root_inputs=built.root_inputs,
        root_references=built.root_references,
        exact_count=exact_count,
        mapper_count=mapper_count,
        skill_title=candidate.title,
        skill=candidate.skill,
    )


def _workstation_skill_store_path(session: WorkstationSession) -> str | None:
    for attachment in session.attachments:
        if collapse_ws(str(getattr(attachment, "name", ""))) == "skills":
            source = collapse_ws(str(getattr(attachment, "source", "")))
            if source:
                return source
    return None


def preferred_workstation_skill_composition_plan(
    *,
    session: WorkstationSession,
    prompt: str,
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation prompts that obviously require more than one installed skill, helps with synthesizing one bounded `ws.skill.compose` plan before the shell falls back to broader LLM planning.

    Reference to Theory:
        Supports the first workstation-facing composition-planning cut by turning prompt-local multi-step intent into explicit validated leaf bindings over the canonical skill ledger.

    Example Input Output:
        Input: `preferred_workstation_skill_composition_plan(session=3, prompt='Read `src/demo.py` from mount `main` and write it to mount `skill_tmp` at `demo.copy`.')`
        Output: {'steps': [...], 'root_inputs': {...}, 'final_output_step': 'step_2'}

    Args:
        session: Value for `session` used by `preferred_workstation_skill_composition_plan`. Expected type: `WorkstationSession`.
        prompt: Value for `prompt` used by `preferred_workstation_skill_composition_plan`. Expected type: `str`.

    Returns:
        dict[str, Any] | None: Result produced by `preferred_workstation_skill_composition_plan`.
    """
    if "ws.skill.compose" not in session.allowed_capabilities:
        return None
    if match_workstation_shell_utility_prompt(prompt) is not None:
        return None
    if not _prompt_implies_skill_pipeline(prompt):
        return None
    scored_skills = _scored_shortlist_for_prompt(session=session, prompt=prompt, limit=6)
    if len(scored_skills) < 2:
        return None

    best_plan: dict[str, Any] | None = None
    best_score = -1
    normalized_prompt = collapse_ws(str(prompt))
    skill_store_path = _workstation_skill_store_path(session)
    if not skill_store_path:
        return None
    pipeline_clauses = _split_prompt_pipeline_clauses(prompt)
    if pipeline_clauses is None:
        return None
    parsed_clauses = []
    for clause in pipeline_clauses:
        condition_spec, conditioned_clause = _split_clause_condition(clause)
        primary_clause = conditioned_clause
        else_clause = ""
        if isinstance(condition_spec, _PlannerConditionSpec):
            primary_clause, else_clause = _split_clause_else_branch(conditioned_clause)
        iteration_spec, action_clause = _split_clause_iteration(primary_clause)
        parsed_clauses.append(
            {
                "original_clause": clause,
                "condition": condition_spec,
                "iteration": iteration_spec,
                "action_clause": action_clause,
                "branch_label": "if" if isinstance(condition_spec, _PlannerConditionSpec) else "",
            }
        )
        if else_clause:
            inverse_condition = _invert_condition_spec(condition_spec) if isinstance(condition_spec, _PlannerConditionSpec) else None
            if inverse_condition is None:
                return None
            else_iteration_spec, else_action_clause = _split_clause_iteration(else_clause)
            parsed_clauses.append(
                {
                    "original_clause": clause,
                    "condition": inverse_condition,
                    "iteration": else_iteration_spec,
                    "action_clause": else_action_clause,
                    "branch_label": "else",
                }
            )
    if any(not collapse_ws(str(item.get("action_clause", ""))) for item in parsed_clauses):
        return None
    clause_candidates: list[list[_ResolvedPlannerSkillCandidate]] = []
    shortlist_limit = max(6, min(12, len(parsed_clauses) * 3))
    for clause_item in parsed_clauses:
        clause_text = collapse_ws(str(clause_item.get("action_clause", "")))
        candidates = _resolved_candidates_for_clause(
            scored_skills=scored_skills[:shortlist_limit],
            clause=clause_text,
            skill_store_path=skill_store_path,
        )
        if not candidates:
            clause_scored_skills = _scored_shortlist_for_prompt(
                session=session,
                prompt=clause_text,
                limit=max(shortlist_limit, 8),
            )
            candidates = _resolved_candidates_for_clause(
                scored_skills=clause_scored_skills,
                clause=clause_text,
                skill_store_path=skill_store_path,
            )
        if not candidates:
            return None
        clause_candidates.append(candidates)

    def _search(
        *,
        clause_index: int,
        prior_steps: list[_BuiltPlannerStep],
        root_inputs: dict[str, Any],
        root_references: dict[str, Any],
        total_score: int,
    ) -> None:
        nonlocal best_plan, best_score
        if clause_index >= len(parsed_clauses):
            analysis = analyze_skill_composition_plan(
                [step.analysis_payload for step in prior_steps],
                root_inputs={name: _type_hint_for_value(value) for name, value in root_inputs.items()},
                root_references={name: _type_hint_for_value(value) for name, value in root_references.items()},
            )
            if analysis.blocked:
                return
            plan: dict[str, Any] = {
                "steps": [step.step_payload for step in prior_steps],
                "root_inputs": root_inputs,
                "final_output_step": collapse_ws(str(prior_steps[-1].step_payload.get("step_id", ""))),
            }
            if root_references:
                plan["root_references"] = root_references
            if total_score > best_score:
                best_score = total_score
                best_plan = plan
            return

        step_id = f"step_{clause_index + 1}"
        clause = collapse_ws(str(parsed_clauses[clause_index].get("action_clause", "")))
        condition_spec = parsed_clauses[clause_index].get("condition")
        iteration_spec = parsed_clauses[clause_index].get("iteration")
        branch_label = collapse_ws(str(parsed_clauses[clause_index].get("branch_label", "")))
        for candidate in clause_candidates[clause_index]:
            built_step = _build_pipeline_step(
                step_id=step_id,
                clause=clause,
                candidate=candidate,
                prior_steps=prior_steps,
                normalized_prompt=normalized_prompt,
                condition_spec=condition_spec if isinstance(condition_spec, _PlannerConditionSpec) else None,
                iteration_spec=iteration_spec if isinstance(iteration_spec, _PlannerIterationSpec) else None,
                branch_label=branch_label,
            )
            if built_step is None:
                continue
            merged_root_inputs = {
                **root_inputs,
                **built_step.root_inputs,
            }
            merged_root_references = {
                **root_references,
                **built_step.root_references,
            }
            prefix_analysis = analyze_skill_composition_plan(
                [* [step.analysis_payload for step in prior_steps], built_step.analysis_payload],
                root_inputs={name: _type_hint_for_value(value) for name, value in merged_root_inputs.items()},
                root_references={name: _type_hint_for_value(value) for name, value in merged_root_references.items()},
            )
            if prefix_analysis.blocked:
                continue
            step_score = (
                candidate.effective_score
                + (candidate.clause_bonus * 5)
                + built_step.exact_count
                + built_step.mapper_count
            )
            _search(
                clause_index=clause_index + 1,
                prior_steps=[*prior_steps, built_step],
                root_inputs=merged_root_inputs,
                root_references=merged_root_references,
                total_score=total_score + step_score,
            )

    _search(
        clause_index=0,
        prior_steps=[],
        root_inputs={},
        root_references={},
        total_score=0,
    )

    return best_plan
