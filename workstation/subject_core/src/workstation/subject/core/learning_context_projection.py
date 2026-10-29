# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws
from workstation.subject.core.learning_context import (
    learning_context_projected_skill_ids,
)

LearningContext = Any
LearningUnit = Any


_SECTION_ORDER: tuple[tuple[str, str], ...] = (
    ("subject", "Subject"),
    ("definitions", "Definitions"),
    ("governing-relations", "Governing Relations"),
    ("executable-abilities", "Executable Abilities"),
    ("examples", "Examples"),
    ("counterexamples", "Counterexamples"),
    ("boundaries", "Boundaries"),
    ("misconceptions", "Misconceptions"),
    ("open-questions", "Open Questions"),
    ("provenance", "Provenance"),
    ("derived-skills", "Derived Skills"),
    ("update-log", "Update Log"),
)

_SECTION_TITLES = {section_id: title for section_id, title in _SECTION_ORDER}
_UNIT_KIND_TO_SECTION = {
    "definition": "definitions",
    "relation": "governing-relations",
    "ability": "executable-abilities",
    "example": "examples",
    "counterexample": "counterexamples",
    "boundary": "boundaries",
    "misconception": "misconceptions",
    "open_question": "open-questions",
    "source_note": "provenance",
}

_TYPST_ESCAPE_REPLACEMENTS = {
    "\\": "\\\\",
    "#": "\\#",
    "$": "\\$",
    "[": "\\[",
    "]": "\\]",
    "{": "\\{",
    "}": "\\}",
    "<": "\\<",
    ">": "\\>",
    "_": "\\_",
    "*": "\\*",
}


def _ordered_units(units: tuple["LearningUnit", ...]) -> list["LearningUnit"]:
    return sorted(
        list(units),
        key=lambda item: (
            _SECTION_ORDER_INDEX.get(_UNIT_KIND_TO_SECTION.get(item.unit_kind, "definitions"), 99),
            item.canonical_title,
            item.unit_id,
        ),
    )


_SECTION_ORDER_INDEX = {section_id: index for index, (section_id, _title) in enumerate(_SECTION_ORDER)}


def _grouped_units(context: "LearningContext") -> dict[str, list["LearningUnit"]]:
    grouped: dict[str, list["LearningUnit"]] = defaultdict(list)
    for unit in _ordered_units(context.units):
        grouped[_UNIT_KIND_TO_SECTION.get(unit.unit_kind, "definitions")].append(unit)
    return grouped


def _render_value_list(items: tuple[str, ...] | list[str]) -> str:
    ordered = [collapse_ws(str(item)) for item in items if collapse_ws(str(item))]
    return ", ".join(ordered)


def _render_json_inline(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))


def _typst_escape_text(text: str) -> str:
    rendered = str(text or "")
    for needle, replacement in _TYPST_ESCAPE_REPLACEMENTS.items():
        rendered = rendered.replace(needle, replacement)
    return rendered


def _markdown_unit_block(unit: "LearningUnit") -> list[str]:
    lines = [
        f"<!-- unit-id: {unit.unit_id} -->",
        f"### {unit.canonical_title or unit.unit_id}",
        "",
        f"- Unit ID: `{unit.unit_id}`",
        f"- Status: `{unit.status}`",
        f"- Statement: {unit.statement or '_No statement._'}",
    ]
    if unit.aliases:
        lines.append(f"- Aliases: {_render_value_list(unit.aliases)}")
    if unit.provenance_refs:
        lines.append(f"- Provenance: {_render_value_list(unit.provenance_refs)}")
    if unit.linked_skill_ids:
        lines.append(f"- Linked Skills: {_render_value_list(unit.linked_skill_ids)}")
    if unit.linked_artifact_ids:
        lines.append(f"- Linked Artifacts: {_render_value_list(unit.linked_artifact_ids)}")
    if unit.structured_fields:
        lines.append(f"- Structured Fields: `{_render_json_inline(unit.structured_fields)}`")
    lines.append("")
    return lines


def _typst_unit_block(unit: "LearningUnit") -> list[str]:
    lines = [
        f"=== {_typst_escape_text(unit.canonical_title or unit.unit_id)} <unit-{unit.unit_id}>",
        "",
        f"- Unit ID: {_typst_escape_text(unit.unit_id)}",
        f"- Status: {_typst_escape_text(unit.status)}",
        f"- Statement: {_typst_escape_text(unit.statement or 'No statement.')}",
    ]
    if unit.aliases:
        lines.append(f"- Aliases: {_typst_escape_text(_render_value_list(unit.aliases))}")
    if unit.provenance_refs:
        lines.append(f"- Provenance: {_typst_escape_text(_render_value_list(unit.provenance_refs))}")
    if unit.linked_skill_ids:
        lines.append(f"- Linked Skills: {_typst_escape_text(_render_value_list(unit.linked_skill_ids))}")
    if unit.linked_artifact_ids:
        lines.append(f"- Linked Artifacts: {_typst_escape_text(_render_value_list(unit.linked_artifact_ids))}")
    if unit.structured_fields:
        lines.append(f"- Structured Fields: {_typst_escape_text(_render_json_inline(unit.structured_fields))}")
    lines.append("")
    return lines


def render_learning_context_subject_markdown(context: "LearningContext") -> str:
    grouped = _grouped_units(context)
    projected_skill_ids = learning_context_projected_skill_ids(context)
    lines = [f"# {context.canonical_title or context.subject_id}", ""]
    for section_id, section_title in _SECTION_ORDER:
        lines.extend([f"<!-- section-id: {section_id} -->", f"## {section_title}", ""])
        if section_id == "subject":
            lines.append(f"- Subject ID: `{context.subject_id}`")
            lines.append(f"- Governance Status: `{context.governance_status}`")
            if context.subject_family:
                lines.append(f"- Subject Family: {context.subject_family}")
            if context.aliases:
                lines.append(f"- Aliases: {_render_value_list(context.aliases)}")
            if context.summary:
                lines.append(f"- Summary: {context.summary}")
            lines.append("")
            continue
        if section_id == "derived-skills":
            if projected_skill_ids:
                for skill_id in projected_skill_ids:
                    lines.append(f"- `{skill_id}`")
            else:
                lines.append("_No linked skills yet._")
            lines.append("")
            continue
        if section_id == "update-log":
            if context.applied_delta_ids:
                for delta_id in context.applied_delta_ids:
                    lines.append(f"- `{delta_id}`")
            else:
                lines.append("_No applied deltas yet._")
            lines.append("")
            continue
        if section_id == "provenance":
            lines.append("### Sources")
            lines.append("")
            if context.linked_source_ids:
                for source_id in context.linked_source_ids:
                    lines.append(f"- `{source_id}`")
            else:
                lines.append("_No linked sources yet._")
            lines.append("")
        units = grouped.get(section_id, [])
        if units:
            for unit in units:
                lines.extend(_markdown_unit_block(unit))
        elif section_id != "provenance":
            lines.append("_No entries yet._")
            lines.append("")
        elif not context.linked_source_ids:
            lines.append("_No provenance notes yet._")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_learning_context_subject_typ(context: "LearningContext") -> str:
    grouped = _grouped_units(context)
    projected_skill_ids = learning_context_projected_skill_ids(context)
    lines = [
        "// Generated from LearningContext. Edit through governed deltas, not direct free-form drift.",
        "#set heading(numbering: none)",
        "",
        f"= {_typst_escape_text(context.canonical_title or context.subject_id)}",
        "",
    ]
    for section_id, section_title in _SECTION_ORDER:
        lines.extend([f"== {section_title} <{section_id}>", ""])
        if section_id == "subject":
            lines.append(f"- Subject ID: {_typst_escape_text(context.subject_id)}")
            lines.append(f"- Governance Status: {_typst_escape_text(context.governance_status)}")
            if context.subject_family:
                lines.append(f"- Subject Family: {_typst_escape_text(context.subject_family)}")
            if context.aliases:
                lines.append(f"- Aliases: {_typst_escape_text(_render_value_list(context.aliases))}")
            if context.summary:
                lines.append(f"- Summary: {_typst_escape_text(context.summary)}")
            lines.append("")
            continue
        if section_id == "derived-skills":
            if projected_skill_ids:
                for skill_id in projected_skill_ids:
                    lines.append(f"- {_typst_escape_text(skill_id)}")
            else:
                lines.append("- No linked skills yet.")
            lines.append("")
            continue
        if section_id == "update-log":
            if context.applied_delta_ids:
                for delta_id in context.applied_delta_ids:
                    lines.append(f"- {_typst_escape_text(delta_id)}")
            else:
                lines.append("- No applied deltas yet.")
            lines.append("")
            continue
        if section_id == "provenance":
            lines.extend(["=== Sources <provenance-sources>", ""])
            if context.linked_source_ids:
                for source_id in context.linked_source_ids:
                    lines.append(f"- {_typst_escape_text(source_id)}")
            else:
                lines.append("- No linked sources yet.")
            lines.append("")
        units = grouped.get(section_id, [])
        if units:
            for unit in units:
                lines.extend(_typst_unit_block(unit))
        elif section_id != "provenance":
            lines.append("- No entries yet.")
            lines.append("")
        elif not context.linked_source_ids:
            lines.extend(["=== Notes <provenance-notes>", "", "- No provenance notes yet.", ""])
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "render_learning_context_subject_markdown",
    "render_learning_context_subject_typ",
]
