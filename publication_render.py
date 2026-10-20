# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import shutil
import subprocess

from publication import (
    Publication,
    PublicationBlock,
    PublicationBuild,
    PublicationClaim,
    PublicationSection,
    PublicationSource,
    RenderArtifact,
    publication_statement_is_reportable,
    stable_publication_build_id,
)
from runtime_temp import runtime_temporary_directory
from semantic_text import collapse_ws


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

_METADATA_ONLY_BLOCK_KINDS = {
    "section_lead",
    "governed_basis",
    "report_scope",
}

_INLINE_MATH_RE = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.DOTALL)
_TEXT_COMMAND_RE = re.compile(r"\\text\{([^{}]*)\}")
_FRACTION_RE = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
_BRACED_SUFFIX_RE = re.compile(r"\b([A-Za-z])\{([A-Za-z][^{}]*)\}")
_BARE_WORD_TOKEN_RE = re.compile(r'(?<!")\b([A-Za-z][A-Za-z0-9]{1,})\b(?!")')
_TYPST_MATH_IDENTIFIER_ALLOWLIST = {
    "abs",
    "alpha",
    "beta",
    "cos",
    "delta",
    "dot",
    "dots",
    "exp",
    "frac",
    "gamma",
    "ln",
    "log",
    "log10",
    "max",
    "min",
    "pi",
    "prod",
    "sigma",
    "sin",
    "sqrt",
    "sum",
    "tan",
    "theta",
    "times",
}

_EXACT_DRAFT_TABLE_BLOCK_KINDS = {
    "review_typst_table",
    "review_decision_table",
    "decision_matrix",
    "decision_risk_matrix",
}

_DECISION_SECTION_BLOCK_KINDS = {
    "decision_case_frame",
    "decision_summary",
    "decision_matrix",
    "decision_transition_roadmap",
    "decision_simple_diagram",
    "decision_ranking_summary",
    "decision_dependency_checklist",
    "decision_risk_matrix",
    "decision_execution_guidance",
    "decision_recommendation_receipt",
}


def _typst_escape_text(text: str) -> str:
    rendered = str(text or "")
    for needle, replacement in _TYPST_ESCAPE_REPLACEMENTS.items():
        rendered = rendered.replace(needle, replacement)
    return rendered


def _typst_math_expression(expr: str) -> str:
    rendered = collapse_ws(str(expr or "").replace("\n", " "))

    def _normalize_bare_word_token(match: re.Match[str]) -> str:
        token = collapse_ws(match.group(1))
        if token.casefold() in _TYPST_MATH_IDENTIFIER_ALLOWLIST:
            return token
        if len(token) > 1 and token.isupper():
            return " ".join(token)
        suffix = match.string[match.end() :]
        if suffix.lstrip().startswith("("):
            return token
        return f'"{token}"'

    for _iteration in range(16):
        previous = rendered
        rendered = _TEXT_COMMAND_RE.sub(lambda match: f'"{collapse_ws(match.group(1))}"', rendered)
        rendered = _FRACTION_RE.sub(
            lambda match: f"frac({_typst_math_expression(match.group(1))}, {_typst_math_expression(match.group(2))})",
            rendered,
        )
        rendered = re.sub(r"\\min\b", "min", rendered)
        rendered = re.sub(r"\\dots\b", "dots.h", rendered)
        rendered = re.sub(r"\\cdot\b", " dot ", rendered)
        rendered = re.sub(r"\\times\b", " times ", rendered)
        rendered = _BRACED_SUFFIX_RE.sub(
            lambda match: f'{match.group(1)}_"{collapse_ws(match.group(2))}"',
            rendered,
        )
        rendered = re.sub(r"\\([A-Za-z]+)", lambda match: match.group(1), rendered)
        rendered = _BARE_WORD_TOKEN_RE.sub(_normalize_bare_word_token, rendered)
        rendered = collapse_ws(rendered)
        if rendered == previous:
            break
    return rendered


def _typst_inline_content(text: str) -> str:
    rendered = str(text or "")
    if not collapse_ws(rendered):
        return "_No narrative provided._"
    pieces: list[str] = []
    cursor = 0
    for match in _INLINE_MATH_RE.finditer(rendered):
        if match.start() > cursor:
            pieces.append(_typst_escape_text(rendered[cursor:match.start()]))
        expr = match.group(1) if match.group(1) is not None else match.group(2)
        pieces.append(f"${_typst_math_expression(expr)}$")
        cursor = match.end()
    if cursor < len(rendered):
        pieces.append(_typst_escape_text(rendered[cursor:]))
    return "".join(piece for piece in pieces if piece)


def _typst_reader_inline_content(text: str) -> str:
    return _typst_inline_content(str(text or "").replace(" -> ", " → "))


def _render_markdown_block_lines(
    block_id: str,
    *,
    block_by_id: dict[str, PublicationBlock],
    trail: tuple[str, ...] = (),
) -> list[str]:
    if block_id in trail:
        return [f"_Blocked transclusion cycle: {' -> '.join(trail + (block_id,))}_"]
    block = block_by_id.get(block_id)
    if block is None:
        return [f"_Missing block: {block_id}_"]
    lines = [f"<!-- block-id: {block.block_id} -->"]
    if block.title:
        lines.append(f"### {block.title}")
    if block.body:
        lines.extend([block.body, ""])
    for included_block_id in block.included_block_refs:
        lines.extend(_render_markdown_block_lines(included_block_id, block_by_id=block_by_id, trail=trail + (block_id,)))
        lines.append("")
    while lines and not lines[-1]:
        lines.pop()
    return lines


def _render_typst_block_lines(
    block_id: str,
    *,
    block_by_id: dict[str, PublicationBlock],
    trail: tuple[str, ...] = (),
) -> list[str]:
    if block_id in trail:
        return _typst_panel_lines(
            "Transclusion Warning",
            [f"Blocked transclusion cycle: {' -> '.join(trail + (block_id,))}"],
            tint="report_warning",
            kicker="VALIDATION",
        )
    block = block_by_id.get(block_id)
    if block is None:
        return _typst_panel_lines(
            "Missing Block",
            [f"Block {block_id} is referenced by the publication but not available in the block store."],
            tint="report_warning",
            kicker="VALIDATION",
        )
    parsed_table = _parse_pipe_table(block.body)
    if block.block_kind == "decision_matrix" and parsed_table is not None:
        headers, rows = parsed_table
        return _typst_decision_option_matrix_lines(
            block.title or f"Block {block.block_id}",
            headers,
            rows,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_ranking_summary":
        return _typst_decision_ranking_summary_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_summary":
        return _typst_decision_summary_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_transition_roadmap":
        return _typst_decision_transition_roadmap_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_execution_guidance":
        return _typst_decision_execution_guidance_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_simple_diagram":
        return _typst_decision_simple_diagram_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_recommendation_receipt":
        return _typst_decision_recommendation_receipt_lines(
            block.title or f"Block {block.block_id}",
            block.body,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "decision_risk_matrix" and parsed_table is not None:
        headers, rows = parsed_table
        return _typst_decision_risk_matrix_lines(
            block.title or f"Block {block.block_id}",
            headers,
            rows,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind in {
        "review_typst_table",
        "review_decision_table",
    } and parsed_table is not None:
        headers, rows = parsed_table
        return _typst_grid_table_lines(
            block.title or f"Block {block.block_id}",
            headers,
            rows,
            tint="report_panel",
            kicker=block.block_kind.replace("_", " ").upper(),
        )
    if block.block_kind == "review_metric_card":
        metrics = _parse_label_value_metrics(block.body)
        if metrics:
            return _typst_panel_lines(
                block.title or f"Block {block.block_id}",
                _typst_metric_grid_lines(metrics[:4]),
                tint="report_panel_alt",
                kicker=block.block_kind.replace("_", " ").upper(),
            )
    panel_tint = {
        "report_scope": "report_highlight",
        "governed_basis": "report_panel_alt",
        "section_lead": "report_panel",
    }.get(block.block_kind, "report_panel")
    lines = _typst_panel_lines(
        block.title or f"Block {block.block_id}",
        _typst_text_lines(block.body),
        tint=panel_tint,
        kicker=block.block_kind.replace("_", " ").upper(),
    )
    for included_block_id in block.included_block_refs:
        lines.extend([""] + _render_typst_block_lines(included_block_id, block_by_id=block_by_id, trail=trail + (block_id,)))
    return lines


def _typst_text_lines(text: str) -> list[str]:
    rendered = str(text or "").strip()
    if not rendered:
        return ["_No narrative provided._"]
    lines: list[str] = []
    paragraphs = [paragraph.strip() for paragraph in rendered.replace("\r\n", "\n").split("\n\n") if paragraph.strip()]
    for index, paragraph in enumerate(paragraphs):
        if index:
            lines.extend(["", ""])
        paragraph_lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
        if not paragraph_lines:
            continue
        for paragraph_line in paragraph_lines:
            lines.append(_typst_inline_content(paragraph_line))
    return lines


def _typst_panel_lines(
    title: str,
    body_lines: list[str] | tuple[str, ...],
    *,
    tint: str = "report_panel",
    kicker: str = "",
    breakable: bool = True,
) -> list[str]:
    breakable_flag = "true" if breakable else "false"
    lines = [
        f"#block(width: 100%, breakable: {breakable_flag}, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    lines.append("  #v(6pt)")
    for line in body_lines:
        lines.append(f"  {line}" if line else "")
    lines.append("]")
    return lines


def _typst_bullet_lines(items: list[str] | tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if text:
            lines.append(f"- {_typst_inline_content(text)}")
    return lines or ["- _No items recorded._"]


def _typst_metric_grid_lines(
    metrics: list[tuple[str, str]] | tuple[tuple[str, str], ...],
) -> list[str]:
    if not metrics:
        return []
    lines = [
        "#grid(",
        f"  columns: ({', '.join(['1fr'] * len(metrics))}),",
        "  gutter: 8pt,",
    ]
    for label, value in metrics:
        lines.extend(
            [
                "  block(width: 100%, fill: report_panel_alt, inset: 11pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
                '    #set par(justify: false)',
                f'    #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(label)}]',
                "    #v(4pt)",
                f'    #text(size: 10.2pt, weight: "bold", fill: report_accent)[{_typst_escape_text(value)}]',
                "  ],",
            ]
        )
    lines.append(")")
    return lines


def _parse_pipe_table(body: str) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]] | None:
    raw_lines = [line.strip() for line in str(body or "").splitlines() if collapse_ws(line)]
    if len(raw_lines) < 2 or "|" not in raw_lines[0] or "|" not in raw_lines[1]:
        return None
    divider_cells = [collapse_ws(cell) for cell in raw_lines[1].split("|")]
    if not any(set(cell) <= {"-"} for cell in divider_cells if cell):
        return None

    def _cells(line: str) -> tuple[str, ...]:
        values = [cell.strip() for cell in line.split("|")]
        while values and not values[0]:
            values.pop(0)
        while values and not values[-1]:
            values.pop()
        return tuple(values)

    headers = _cells(raw_lines[0])
    if not headers:
        return None
    rows: list[tuple[str, ...]] = []
    for line in raw_lines[2:]:
        cells = _cells(line)
        if any(cells):
            rows.append(cells)
    return headers, tuple(rows)


def _parse_label_value_metrics(body: str) -> tuple[tuple[str, str], ...]:
    metrics: list[tuple[str, str]] = []
    for line in str(body or "").splitlines():
        if ":" not in line:
            continue
        label, value = line.split(":", 1)
        normalized_label = collapse_ws(label)
        normalized_value = collapse_ws(value)
        if normalized_label and normalized_value:
            metrics.append((normalized_label, normalized_value))
    return tuple(metrics)


def _indented_lines(lines: list[str] | tuple[str, ...], *, prefix: str) -> list[str]:
    return [f"{prefix}{line}" if line else "" for line in lines]


def _decision_table_rows(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> tuple[dict[str, str], ...]:
    normalized_headers = [collapse_ws(header).casefold() for header in headers]
    parsed_rows: list[dict[str, str]] = []
    for row in rows:
        padded = tuple(row) + tuple("" for _ in range(max(0, len(headers) - len(row))))
        parsed_rows.append(
            {
                normalized_headers[index] if index < len(normalized_headers) else f"column_{index}": collapse_ws(padded[index])
                for index in range(len(headers))
            }
        )
    return tuple(parsed_rows)


def _parse_decision_summary(
    body: str,
) -> tuple[str, str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    question = ""
    status = ""
    policy_profile = ""
    recommended_options: list[str] = []
    reading_lines: list[str] = []
    blocked_lines: list[str] = []
    for raw_line in str(body or "").splitlines():
        line = collapse_ws(raw_line)
        if not line:
            continue
        if line.startswith("Decision question:"):
            question = collapse_ws(line.split(":", 1)[1])
        elif line.startswith("Recommendation status:"):
            status = collapse_ws(line.split(":", 1)[1])
        elif line.startswith("Policy profile:"):
            policy_profile = collapse_ws(line.split(":", 1)[1])
        elif line.startswith("Recommended options:"):
            recommended_options = [
                collapse_ws(item)
                for item in line.split(":", 1)[1].split(",")
                if collapse_ws(item)
            ]
        elif line.startswith("Recommendation reading:"):
            reading_lines.extend(
                segment
                for segment in re.split(r"(?<=[.!?])\s+", collapse_ws(line.split(":", 1)[1]))
                if collapse_ws(segment)
            )
        elif line.startswith("Blocked options:"):
            blocked_lines = [
                collapse_ws(item)
                for item in line.split(":", 1)[1].split(",")
                if collapse_ws(item)
            ]
        elif line.startswith("Blocking conditions:"):
            blocked_lines.extend(
                collapse_ws(item)
                for item in line.split(":", 1)[1].split(";")
                if collapse_ws(item)
            )
    return (
        question,
        status,
        policy_profile,
        tuple(recommended_options),
        tuple(reading_lines),
        tuple(blocked_lines),
    )


def _typst_reader_bullet_lines(items: list[str] | tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if text:
            lines.append(f"- {_typst_reader_inline_content(text)}")
    return lines or ["- _No items recorded._"]


def _typst_label_value_stack_lines(
    entries: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    *,
    item_prefix: str = "",
) -> list[str]:
    lines: list[str] = []
    for label, value in entries:
        if not collapse_ws(value):
            continue
        lead = f"{item_prefix} " if item_prefix else ""
        lines.append(
            f"{lead}#text(weight: \"bold\", fill: report_accent)[{_typst_escape_text(label)}] {_typst_reader_inline_content(value)}"
        )
    return lines or ["_No detail recorded._"]


def _parse_decision_basis_sections(basis: str) -> tuple[tuple[str, str], ...]:
    sections: list[tuple[str, str]] = []
    for segment in re.split(r"(?<=[.!?])\s+", collapse_ws(basis)):
        normalized = collapse_ws(segment).rstrip(".")
        if not normalized:
            continue
        if ":" in normalized:
            label, value = normalized.split(":", 1)
            sections.append((collapse_ws(label), collapse_ws(value)))
        else:
            sections.append(("Reading", normalized))
    return tuple(sections)


def _reader_facing_policy_rule(rule_id: str) -> str:
    normalized = collapse_ws(rule_id).casefold()
    return {
        "prefer_executable_over_merely_valid": "Prefer executable options over merely valid ones.",
        "reject_unresolved_critical_dependencies": "Reject options with unresolved critical dependencies.",
        "penalize_active_high_friction_boundaries": "Penalize options that activate high-friction boundaries.",
        "penalize_coordination_heavy_transitions": "Penalize coordination-heavy transition paths.",
        "prefer_shorter_reachable_paths": "Prefer shorter reachable paths.",
        "prefer_lower_residual_risk": "Prefer options with lower residual risk.",
        "require_source_support_above_minimum_threshold": "Require minimum source support before recommending an option.",
    }.get(normalized, collapse_ws(rule_id).replace("_", " ").capitalize() + ".")


def _typst_decision_summary_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    question, status, policy_profile, recommended_options, reading_lines, blocked_lines = _parse_decision_summary(body)
    lines = [
        f"#block(width: 100%, breakable: false, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    if question:
        lines.extend(
            [
                "  #v(6pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Decision focus]',
                "  #v(2pt)",
                "  #block(width: 100%, fill: white, inset: 9pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f"    {_typst_reader_inline_content(question)}",
                "  ]",
            ]
        )
    metrics: list[tuple[str, str]] = []
    if status:
        metrics.append(("Status", status))
    if policy_profile:
        metrics.append(("Policy profile", policy_profile))
    if metrics:
        lines.extend(["  #v(8pt)", *_indented_lines(_typst_metric_grid_lines(metrics), prefix="  ")])
    if recommended_options:
        lines.extend(
            [
                "  #v(8pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Decision recommendation]',
                "  #v(2pt)",
                "  #block(width: 100%, fill: report_panel_alt, inset: 10pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                '    #set par(justify: false)',
                f'    #text(size: 11pt, weight: "bold", fill: report_accent)[{_typst_escape_text(", ".join(recommended_options[:2]))}]',
                "  ]",
            ]
        )
    if reading_lines:
        lines.extend(
            [
                "  #v(8pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[What this recommendation means]',
                "  #v(3pt)",
                *_indented_lines(_typst_reader_bullet_lines(list(reading_lines[:4])), prefix="  "),
            ]
        )
    if blocked_lines:
        lines.extend(
            [
                "  #v(8pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Blocked or deferred under current conditions]',
                "  #v(3pt)",
                *_indented_lines(_typst_reader_bullet_lines(list(blocked_lines[:4])), prefix="  "),
            ]
        )
    lines.append("]")
    return lines


def _typst_decision_option_card_lines(
    option_label: str,
    *,
    status: str = "",
    score: str = "",
    actors: str = "",
    transitions: str = "",
    basis: str = "",
    capabilities: str = "",
    dependencies: str = "",
    boundaries: str = "",
    ordinal: str = "",
) -> list[str]:
    heading = collapse_ws(f"{ordinal} {option_label}") if collapse_ws(ordinal) else collapse_ws(option_label)
    basis_items = [
        segment
        for segment in _parse_decision_basis_sections(basis)
        if collapse_ws(segment[1])
    ]
    metric_cards: list[str] = [
        '      block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.5pt))[',
        '        #text(size: 7.2pt, weight: "bold", fill: report_muted)[Status]',
        "        #v(2pt)",
        f'        #text(size: 9pt, weight: "bold", fill: report_accent)[{_typst_escape_text(status or "<none>")}]',
        "      ],",
        '      block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.5pt))[',
        '        #text(size: 7.2pt, weight: "bold", fill: report_muted)[Score]',
        "        #v(2pt)",
        f'        #text(size: 9pt, weight: "bold", fill: report_accent)[{_typst_escape_text(score or "<none>")}]',
        "      ],",
        '      block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.5pt))[',
        '        #text(size: 7.2pt, weight: "bold", fill: report_muted)[Actors]',
        "        #v(2pt)",
        f"        {_typst_inline_content(actors or '<none>')}",
        "      ],",
    ]
    lines = [
        "  #block(width: 100%, breakable: false, fill: white, inset: 10pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
        '    #set par(justify: false)',
        f'    #text(size: 9pt, weight: "bold", fill: report_accent)[{_typst_escape_text(heading or "<option>")}]',
        "    #v(5pt)",
        "    #grid(",
        "      columns: (0.9fr, 0.7fr, 1.7fr),",
        "      gutter: 6pt,",
        *_indented_lines(metric_cards, prefix=""),
        "    )",
    ]
    if collapse_ws(transitions):
        lines.extend(
            [
                "    #v(6pt)",
                '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Transitions]',
                "    #v(2pt)",
                f"    {_typst_reader_inline_content(transitions)}",
            ]
        )
    if basis_items:
        lines.extend(
            [
                "    #v(6pt)",
                '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Assessment summary]',
                "    #v(2pt)",
                *_indented_lines(_typst_label_value_stack_lines(basis_items[:4], item_prefix="-"), prefix="    "),
            ]
        )
    if collapse_ws(capabilities):
        lines.extend(
            [
                "    #v(6pt)",
                '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Capabilities]',
                "    #v(2pt)",
                f"    {_typst_inline_content(capabilities)}",
            ]
        )
    if collapse_ws(dependencies):
        lines.extend(
            [
                "    #v(6pt)",
                '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Dependencies]',
                "    #v(2pt)",
                f"    {_typst_inline_content(dependencies)}",
            ]
        )
    if collapse_ws(boundaries):
        lines.extend(
            [
                "    #v(6pt)",
                '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Boundaries]',
                "    #v(2pt)",
                f"    {_typst_inline_content(boundaries)}",
            ]
        )
    lines.append("  ]")
    return lines


def _typst_decision_option_matrix_lines(
    title: str,
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    lines.append("  #v(6pt)")
    parsed_rows = _decision_table_rows(headers, rows)
    if not parsed_rows:
        lines.append("  _No options recorded._")
    for index, row in enumerate(parsed_rows):
        if index:
            lines.append("  #v(8pt)")
        lines.extend(
            _indented_lines(
                _typst_decision_option_card_lines(
                    row.get("option", "") or row.get("column_0", ""),
                    status=row.get("status", "") or row.get("column_1", ""),
                    score=row.get("score", "") or row.get("column_2", ""),
                    transitions=row.get("transitions", "") or row.get("column_3", ""),
                    actors=row.get("actors", "") or row.get("column_4", ""),
                    basis=row.get("basis", "") or row.get("column_5", ""),
                ),
                prefix="  ",
            )
        )
    lines.append("]")
    return lines


def _parse_labeled_sections(body: str) -> dict[str, object]:
    sections: dict[str, object] = {}
    current_key = ""
    list_heading_values = {
        "actors",
        "objectives",
        "reserve options",
        "blocked options",
        "reserve paths",
        "blocked paths",
        "1. current state",
        "2. transition candidates",
        "3. target state",
        "4. assignment candidates",
    }
    for raw_line in str(body or "").splitlines():
        line = collapse_ws(raw_line)
        if not line:
            continue
        normalized_line = collapse_ws(line).casefold()
        if normalized_line in list_heading_values:
            current_key = normalized_line
            sections[current_key] = []
            continue
        if line.endswith(":") and not line.startswith("- "):
            current_key = collapse_ws(line[:-1]).casefold()
            sections[current_key] = []
            continue
        if current_key and line.startswith("- "):
            values = sections.setdefault(current_key, [])
            if isinstance(values, list):
                values.append(collapse_ws(re.sub(r"^-+\s*", "", line)))
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = collapse_ws(key).casefold()
            sections[current_key] = collapse_ws(value)
        elif current_key:
            values = sections.setdefault(current_key, [])
            if isinstance(values, list):
                values.append(line)
    return sections


def _section_list_value(sections: dict[str, object], key: str) -> tuple[str, ...]:
    value = sections.get(key, ())
    if value is None:
        return ()
    if isinstance(value, str) and not collapse_ws(value):
        return ()
    if isinstance(value, tuple) and not value:
        return ()
    if isinstance(value, list) and not value:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(collapse_ws(str(item)) for item in value if collapse_ws(str(item)))
    if collapse_ws(str(value)) and collapse_ws(str(value)) not in {"()", "[]"}:
        return (collapse_ws(str(value)),)
    return ()


def _typst_decision_transition_roadmap_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    sections = _parse_labeled_sections(body)
    question = collapse_ws(str(sections.get("decision question", "")))
    current_states = _section_list_value(sections, "1. current state")
    transition_candidates = _section_list_value(sections, "2. transition candidates")
    target_states = _section_list_value(sections, "3. target state")
    assignment_candidates = _section_list_value(sections, "4. assignment candidates")
    actors = _section_list_value(sections, "actors")
    objectives = _section_list_value(sections, "objectives")
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    if question:
        lines.extend(
            [
                "  #v(6pt)",
                "  #block(width: 100%, fill: white, inset: 9pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f"    {_typst_reader_inline_content(question)}",
                "  ]",
            ]
        )
    lines.extend(
        [
            "  #v(8pt)",
            "  #grid(",
            "    columns: (0.9fr, 1.15fr, 0.95fr),",
            "    gutter: 7pt,",
        ]
    )
    for heading, items in (
        ("Current state", current_states),
        ("Transition candidates", transition_candidates),
        ("Target state", target_states),
    ):
        lines.extend(
            [
                "    block(width: 100%, fill: white, inset: 8pt, radius: 5pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f'      #text(size: 7.2pt, weight: "bold", fill: report_muted)[{_typst_escape_text(heading)}]',
                "      #v(3pt)",
                *_indented_lines(_typst_reader_bullet_lines(list(items or ("<none>",))), prefix="      "),
                "    ],",
            ]
        )
    lines.append("  )")
    if assignment_candidates:
        lines.extend(
            [
                "  #v(8pt)",
                *_indented_lines(
                    _typst_panel_lines(
                        "Assignment candidates",
                        _typst_reader_bullet_lines(list(assignment_candidates)),
                        tint="white",
                    ),
                    prefix="  ",
                ),
            ]
        )
    ancillary_entries = []
    if actors:
        ancillary_entries.append(("Actors", ", ".join(actors[:6])))
    if objectives:
        ancillary_entries.append(("Objectives", ", ".join(objectives[:6])))
    if ancillary_entries:
        lines.extend(
            [
                "  #v(8pt)",
                "  #grid(",
                f"    columns: ({', '.join(['1fr'] * len(ancillary_entries))}),",
                "    gutter: 6pt,",
            ]
        )
        for label, value in ancillary_entries:
            lines.extend(
                [
                    "    block(width: 100%, fill: report_panel_alt, inset: 8pt, radius: 5pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                    f'      #text(size: 7.2pt, weight: "bold", fill: report_muted)[{_typst_escape_text(label)}]',
                    "      #v(2pt)",
                    f"      {_typst_reader_inline_content(value)}",
                    "    ],",
                ]
            )
        lines.append("  )")
    lines.append("]")
    return lines


def _typst_decision_execution_guidance_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    sections = _parse_labeled_sections(body)
    posture = _section_list_value(sections, "recommended operating posture")
    current_reading = _section_list_value(sections, "why this is the current recommendation")
    actors = _section_list_value(sections, "primary responsible actors")
    capabilities = _section_list_value(sections, "capabilities activated in the recommendation")
    prerequisites = _section_list_value(sections, "implementation prerequisites")
    boundaries = _section_list_value(sections, "coordination boundaries to govern")
    reserve = _section_list_value(sections, "alternatives to keep in reserve")
    constraints = _section_list_value(sections, "conditions that remain binding")
    blockers = _section_list_value(sections, "do not proceed if these blockers remain open")
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    if posture:
        lines.extend(
            [
                "  #v(6pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Recommended operating posture]',
                "  #v(2pt)",
                "  #block(width: 100%, fill: report_panel_alt, inset: 10pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f'    #text(size: 10.6pt, weight: "bold", fill: report_accent)[{_typst_escape_text(", ".join(posture[:2]))}]',
                "  ]",
            ]
        )
    if current_reading:
        lines.extend(
            [
                "  #v(8pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Why this leads under the current policy]',
                "  #v(2pt)",
                *_indented_lines(_typst_reader_bullet_lines(list(current_reading[:4])), prefix="  "),
            ]
        )
    grid_entries = []
    if actors:
        grid_entries.append(("Primary actors", ", ".join(actors[:6])))
    if capabilities:
        grid_entries.append(("Activated capabilities", ", ".join(capabilities[:6])))
    if prerequisites:
        grid_entries.append(("Implementation prerequisites", ", ".join(prerequisites[:6])))
    if boundaries:
        grid_entries.append(("Boundaries to govern", ", ".join(boundaries[:6])))
    if grid_entries:
        lines.extend(
            [
                "  #v(8pt)",
                "  #grid(",
                "    columns: (1fr, 1fr),",
                "    gutter: 6pt,",
            ]
        )
        for label, value in grid_entries:
            lines.extend(
                [
                    "    block(width: 100%, fill: white, inset: 8pt, radius: 5pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                    f'      #text(size: 7.2pt, weight: "bold", fill: report_muted)[{_typst_escape_text(label)}]',
                    "      #v(2pt)",
                    f"      {_typst_reader_inline_content(value)}",
                    "    ],",
                ]
            )
        lines.append("  )")
    if reserve:
        lines.extend(
            [
                "  #v(8pt)",
                *_indented_lines(
                    _typst_panel_lines(
                        "Keep in reserve",
                        _typst_reader_bullet_lines(list(reserve[:4])),
                        tint="white",
                    ),
                    prefix="  ",
                ),
            ]
        )
    controls_entries = []
    if constraints:
        controls_entries.append(("Binding conditions", "; ".join(constraints[:6])))
    if blockers:
        controls_entries.append(("Do not proceed if", "; ".join(blockers[:6])))
    if controls_entries:
        lines.extend(
            [
                "  #v(8pt)",
                *_indented_lines(
                    _typst_panel_lines(
                        "Operating controls",
                        _typst_label_value_stack_lines(controls_entries, item_prefix="-"),
                        tint="white",
                    ),
                    prefix="  ",
                ),
            ]
        )
    lines.append("]")
    return lines


def _parse_decision_ranking_summary(
    body: str,
) -> tuple[
    tuple[tuple[str, str], ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[dict[str, str], ...],
    tuple[str, ...],
]:
    metrics: list[tuple[str, str]] = []
    guidance_lines: list[str] = []
    reserve_readings: list[str] = []
    blocked_readings: list[str] = []
    rules: list[str] = []
    ranked_options: list[dict[str, str]] = []
    paths: list[str] = []
    mode = ""
    current_option: dict[str, str] | None = None
    for raw_line in str(body or "").splitlines():
        line = collapse_ws(raw_line)
        if not line:
            continue
        if line.startswith("Policy profile:"):
            metrics.append(("Policy profile", collapse_ws(line.split(":", 1)[1])))
            mode = ""
            continue
        if line.startswith("Recommendation status:"):
            metrics.append(("Recommendation status", collapse_ws(line.split(":", 1)[1])))
            mode = ""
            continue
        if line.startswith("Candidate path count:"):
            metrics.append(("Candidate paths", collapse_ws(line.split(":", 1)[1])))
            mode = ""
            continue
        if (
            line.startswith("Policy guidance:")
            or line.startswith("Current reading:")
            or line.startswith("Why the recommendation leads:")
            or line.startswith("Reserve options:")
            or line.startswith("Blocked options:")
        ):
            guidance_lines.append(line)
            mode = ""
            continue
        if line == "Reserve option readings:":
            if current_option is not None:
                ranked_options.append(current_option)
                current_option = None
            mode = "reserve"
            continue
        if line == "Blocked option readings:":
            if current_option is not None:
                ranked_options.append(current_option)
                current_option = None
            mode = "blocked"
            continue
        if line == "Ranking rules:":
            if current_option is not None:
                ranked_options.append(current_option)
                current_option = None
            mode = "rules"
            continue
        if line == "Ranked options:":
            if current_option is not None:
                ranked_options.append(current_option)
                current_option = None
            mode = "options"
            continue
        if line == "Reachable path signatures:":
            if current_option is not None:
                ranked_options.append(current_option)
                current_option = None
            mode = "paths"
            continue
        if mode == "rules" and line.startswith("- "):
            rules.append(collapse_ws(line[2:]))
            continue
        if mode == "reserve" and line.startswith("- "):
            reserve_readings.append(collapse_ws(line[2:]))
            continue
        if mode == "blocked" and line.startswith("- "):
            blocked_readings.append(collapse_ws(line[2:]))
            continue
        if mode == "options" and line.startswith("- "):
            if current_option is not None:
                ranked_options.append(current_option)
            option_line = collapse_ws(re.sub(r"^-+\s*", "", line))
            option_line = collapse_ws(re.sub(r"^\d+\.\s*", "", option_line))
            parts = [collapse_ws(part) for part in option_line.split("|")]
            current_option = {
                "label": parts[0] if parts else "<unknown>",
                "status": parts[1] if len(parts) > 1 else "",
                "score": parts[2].removeprefix("score ").strip() if len(parts) > 2 else "",
                "transitions": "",
                "actors": "",
                "basis": "",
                "capabilities": "",
                "dependencies": "",
                "boundaries": "",
            }
            continue
        if mode == "options" and current_option is not None and ":" in line:
            key, value = line.split(":", 1)
            current_option[collapse_ws(key).casefold()] = collapse_ws(value)
            continue
        if mode == "paths" and line.startswith("- "):
            paths.append(collapse_ws(line[2:]))
            continue
    if current_option is not None:
        ranked_options.append(current_option)
    return (
        tuple(metrics),
        tuple(guidance_lines),
        tuple(reserve_readings),
        tuple(blocked_readings),
        tuple(rules),
        tuple(ranked_options),
        tuple(paths),
    )


def _typst_decision_ranking_summary_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    metrics, guidance_lines, reserve_readings, blocked_readings, rules, ranked_options, paths = _parse_decision_ranking_summary(body)
    overview_lines: list[str] = []
    if metrics:
        overview_lines.extend(_typst_metric_grid_lines(list(metrics[:3])))
    if guidance_lines:
        overview_lines.extend(
            [
                "#v(8pt)" if overview_lines else "",
                '#text(size: 7.8pt, weight: "bold", fill: report_muted)[Editorial guidance]',
                "#v(4pt)",
                *_typst_bullet_lines(list(guidance_lines[:4])),
            ]
        )
    lines = _typst_panel_lines(
        title,
        overview_lines or ["_No ranking summary recorded._"],
        tint=tint,
        kicker=kicker,
        breakable=False,
    )
    if reserve_readings:
        lines.extend(
            [
                "",
                *_typst_panel_lines(
                    "Reserve option readings",
                    _typst_bullet_lines(list(reserve_readings[:4])),
                    tint="report_panel_alt",
                ),
            ]
        )
    if blocked_readings:
        lines.extend(
            [
                "",
                *_typst_panel_lines(
                    "Blocked option readings",
                    _typst_bullet_lines(list(blocked_readings[:4])),
                    tint="report_panel_alt",
                ),
            ]
        )
    if rules:
        lines.extend(
            [
                "",
                *_typst_panel_lines(
                    "Ranking rules",
                    _typst_reader_bullet_lines([_reader_facing_policy_rule(rule) for rule in list(rules[:8])]),
                    tint="report_panel_alt",
                ),
            ]
        )
    if ranked_options:
        lines.extend(["", '#text(size: 7.8pt, weight: "bold", fill: report_muted)[Ranked option rationale]'])
        for index, option in enumerate(ranked_options[:6], start=1):
            lines.append("#v(6pt)")
            lines.extend(
                _typst_decision_option_card_lines(
                    option.get("label", "<unknown>"),
                    status=option.get("status", ""),
                    score=option.get("score", ""),
                    actors=option.get("actors", ""),
                    transitions=option.get("transitions", ""),
                    basis=option.get("basis", ""),
                    capabilities=option.get("capabilities", ""),
                    dependencies=option.get("dependencies", ""),
                    boundaries=option.get("boundaries", ""),
                    ordinal=f"{index}.",
                )
            )
    if paths:
        lines.extend(
            [
                "",
                *_typst_panel_lines(
                    "Reachable path signatures",
                    _typst_bullet_lines([item.replace(' -> ', ' → ') for item in list(paths[:6])]),
                    tint="report_panel_alt",
                ),
            ]
        )
    return lines


def _parse_decision_simple_diagram(
    body: str,
) -> tuple[
    str,
    str,
    str,
    str,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    current_text = "<current>"
    recommended_option = "<recommended>"
    transition_text = "<transition>"
    target_text = "<target>"
    recommended_actors: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    boundaries: tuple[str, ...] = ()
    reserve_options: list[dict[str, str]] = []
    blocked_options: list[dict[str, str]] = []
    current_group = ""
    current_option: dict[str, str] | None = None

    def _split_path_segments(path_text: str) -> list[str]:
        return [
            collapse_ws(part)
            for part in re.split(r"\s+(?:->|→)\s+", collapse_ws(path_text))
            if collapse_ws(part)
        ]

    def _flush_current_option() -> None:
        nonlocal current_option
        if current_option is None:
            return
        label = collapse_ws(current_option.get("label", ""))
        if not label:
            current_option = None
            return
        option_payload = {
            "label": label,
            "path": collapse_ws(current_option.get("path", "")),
            "actors": collapse_ws(current_option.get("actors", "")),
            "capabilities": collapse_ws(current_option.get("capabilities", "")),
            "dependencies": collapse_ws(current_option.get("dependencies", "")),
            "boundaries": collapse_ws(current_option.get("boundaries", "")),
        }
        if current_group == "reserve":
            reserve_options.append(option_payload)
        elif current_group == "blocked":
            blocked_options.append(option_payload)
        current_option = None

    for index, raw_line in enumerate(str(body or "").splitlines()):
        line = collapse_ws(raw_line)
        if not line:
            continue
        if index == 0 and (" -> " in line or " → " in line):
            segments = _split_path_segments(line)
            if segments:
                current_text = segments[0]
            if len(segments) >= 2:
                transition_text = segments[1]
            if len(segments) >= 3:
                target_text = " → ".join(segments[2:])
            continue
        if line.startswith("Current states:"):
            _flush_current_option()
            current_text = collapse_ws(line.split(":", 1)[1]) or current_text
        elif line.startswith("Recommended option:"):
            _flush_current_option()
            recommended_option = collapse_ws(line.split(":", 1)[1]) or recommended_option
        elif line.startswith("Recommended path:"):
            _flush_current_option()
            transition_text = collapse_ws(line.split(":", 1)[1]) or transition_text
        elif line.startswith("Target states:"):
            _flush_current_option()
            target_text = collapse_ws(line.split(":", 1)[1]) or target_text
        elif line.startswith("Recommended actors:"):
            _flush_current_option()
            recommended_actors = tuple(collapse_ws(item) for item in line.split(":", 1)[1].split(",") if collapse_ws(item))
        elif line == "Reserve options:" or line == "Reserve paths:":
            _flush_current_option()
            current_group = "reserve"
        elif line == "Blocked options:" or line == "Blocked paths:":
            _flush_current_option()
            current_group = "blocked"
        elif line.startswith("Recommended capabilities:") or line.startswith("Activated capabilities:"):
            _flush_current_option()
            capabilities = tuple(collapse_ws(item) for item in line.split(":", 1)[1].split(",") if collapse_ws(item))
            current_group = ""
        elif line.startswith("Recommended dependencies:") or line.startswith("Dependencies:"):
            _flush_current_option()
            dependencies = tuple(collapse_ws(item) for item in line.split(":", 1)[1].split(",") if collapse_ws(item))
            current_group = ""
        elif line.startswith("Recommended boundaries:") or line.startswith("Boundaries:"):
            _flush_current_option()
            boundaries = tuple(collapse_ws(item) for item in line.split(":", 1)[1].split(",") if collapse_ws(item))
            current_group = ""
        elif line.startswith("- "):
            _flush_current_option()
            if current_group in {"reserve", "blocked"}:
                current_option = {
                    "label": collapse_ws(line[2:]),
                    "path": "",
                    "actors": "",
                    "capabilities": "",
                    "dependencies": "",
                    "boundaries": "",
                }
        elif current_option is not None and ":" in line:
            key, value = line.split(":", 1)
            normalized_key = collapse_ws(key).casefold()
            normalized_value = collapse_ws(value)
            if normalized_key == "path":
                current_option["path"] = normalized_value
            elif normalized_key == "actors":
                current_option["actors"] = normalized_value
            elif normalized_key == "capabilities":
                current_option["capabilities"] = normalized_value
            elif normalized_key == "dependencies":
                current_option["dependencies"] = normalized_value
            elif normalized_key == "boundaries":
                current_option["boundaries"] = normalized_value
    _flush_current_option()
    return (
        current_text,
        recommended_option,
        transition_text,
        target_text,
        recommended_actors,
        capabilities,
        dependencies,
        boundaries,
        tuple(reserve_options),
        tuple(blocked_options),
    )


def _typst_decision_path_detail_card_lines(
    title: str,
    *,
    path: str = "",
    actors: str = "",
    capabilities: str = "",
    dependencies: str = "",
    boundaries: str = "",
    tint: str = "white",
) -> list[str]:
    lines = [
        f"#block(width: 100%, breakable: false, fill: {tint}, inset: 8pt, radius: 5pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
        f'  #text(size: 7.2pt, weight: "bold", fill: report_muted)[{_typst_escape_text(title)}]',
    ]
    sections = (
        ("Path", path),
        ("Actors", actors),
        ("Capabilities", capabilities),
        ("Dependencies", dependencies),
        ("Boundaries", boundaries),
    )
    if any(collapse_ws(value) for _label, value in sections):
        for label, value in sections:
            if not collapse_ws(value):
                continue
            lines.extend(
                [
                    "  #v(3pt)",
                    f'  #text(size: 6.9pt, weight: "bold", fill: report_muted)[{_typst_escape_text(label)}]',
                    "  #v(2pt)",
                    f"  {_typst_inline_content(value)}",
                ]
            )
    else:
        lines.extend(["  #v(3pt)", "  _none_"])
    lines.append("]")
    return lines


def _typst_decision_simple_diagram_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    (
        current_text,
        recommended_option,
        transition_text,
        target_text,
        recommended_actors,
        capabilities,
        dependencies,
        boundaries,
        reserve_options,
        blocked_options,
    ) = _parse_decision_simple_diagram(body)
    lines = [
        f"#block(width: 100%, breakable: false, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    lines.extend(
        [
            "  #v(6pt)",
            "  #grid(",
            "    columns: (1fr, 1.2fr, 1fr),",
            "    gutter: 8pt,",
        ]
    )
    for heading, value in (
        ("Current state(s)", current_text),
        ("Recommended option", collapse_ws(recommended_option) or "<recommended>"),
        ("Target state(s)", target_text),
    ):
        lines.extend(
            [
                "    block(width: 100%, fill: white, inset: 8pt, radius: 5pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f'      #text(size: 7.2pt, weight: "bold", fill: report_muted)[{_typst_escape_text(heading)}]',
                "      #v(3pt)",
                f"      {_typst_inline_content(value)}",
                "    ],",
            ]
        )
    lines.append("  )")
    lines.extend(
        [
            "  #v(8pt)",
            *_indented_lines(
                _typst_decision_path_detail_card_lines(
                    "Recommended path and coordination",
                    path=transition_text,
                    actors=", ".join(recommended_actors[:6]),
                    capabilities=", ".join(capabilities[:6]),
                    dependencies=", ".join(dependencies[:6]),
                    boundaries=", ".join(boundaries[:6]),
                    tint="white",
                ),
                prefix="  ",
            ),
        ]
    )
    lines.append("]")
    def _append_option_group(group_title: str, options: tuple[dict[str, str], ...], *, option_tint: str) -> None:
        if not options:
            return
        lines.extend(
            [
                "",
                f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
                '  #set par(justify: false)',
                f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(group_title.upper())}]',
            ]
        )
        for index, option in enumerate(options[:4], start=1):
            lines.extend(
                [
                    "  #v(4pt)",
                    *_indented_lines(
                        _typst_decision_path_detail_card_lines(
                            f"{index}. {option.get('label', '<option>')}",
                            path=option.get("path", ""),
                            actors=option.get("actors", ""),
                            capabilities=option.get("capabilities", ""),
                            dependencies=option.get("dependencies", ""),
                            boundaries=option.get("boundaries", ""),
                            tint=option_tint,
                        ),
                        prefix="  ",
                    ),
                ]
            )
        lines.append("]")

    _append_option_group("Reserve options", tuple(reserve_options), option_tint="report_panel_alt")
    _append_option_group("Blocked options", tuple(blocked_options), option_tint="report_warning")
    return lines


def _typst_decision_recommendation_receipt_lines(
    title: str,
    body: str,
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    sections = _parse_labeled_sections(body)
    question = collapse_ws(str(sections.get("question", "")))
    status = collapse_ws(str(sections.get("recommendation status", "")))
    profile = collapse_ws(str(sections.get("policy profile", "")))
    admissible = collapse_ws(str(sections.get("admissible transitions", "")))
    valid = collapse_ws(str(sections.get("valid options", "")))
    executable = collapse_ws(str(sections.get("executable options", "")))
    path_count = collapse_ws(str(sections.get("candidate paths", "")))
    top_option = collapse_ws(str(sections.get("top ranked option", "")))
    top_basis = collapse_ws(str(sections.get("top option basis", "")))
    top_transitions = collapse_ws(str(sections.get("top option transitions", "")))
    top_actors = collapse_ws(str(sections.get("top option actors", "")))
    top_capabilities = collapse_ws(str(sections.get("top option capabilities", "")))
    top_dependencies = collapse_ws(str(sections.get("top option dependencies", "")))
    top_boundaries = collapse_ws(str(sections.get("boundary conditions to govern", "")))
    recommended = collapse_ws(str(sections.get("recommended options", "")))
    blocking = collapse_ws(str(sections.get("blocking conditions", "")))
    rules = collapse_ws(str(sections.get("policy rules", "")))
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    if question:
        lines.extend(
            [
                "  #v(6pt)",
                "  #block(width: 100%, fill: white, inset: 9pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f"    {_typst_reader_inline_content(question)}",
                "  ]",
            ]
        )
    metric_entries = [
        ("Status", status),
        ("Policy", profile),
        ("Executable options", executable),
        ("Candidate paths", path_count),
    ]
    metric_entries = [(label, value) for label, value in metric_entries if collapse_ws(value)]
    if metric_entries:
        lines.extend(["  #v(8pt)", *_indented_lines(_typst_metric_grid_lines(metric_entries[:4]), prefix="  ")])
    if top_option or recommended:
        recommendation_label = top_option or recommended
        lines.extend(
            [
                "  #v(8pt)",
                '  #text(size: 7.2pt, weight: "bold", fill: report_muted)[Recommended option]',
                "  #v(2pt)",
                "  #block(width: 100%, fill: report_panel_alt, inset: 10pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                f'    #text(size: 10.6pt, weight: "bold", fill: report_accent)[{_typst_escape_text(recommendation_label)}]',
                "  ]",
            ]
        )
    detail_sections = []
    if top_basis:
        detail_sections.extend(_parse_decision_basis_sections(top_basis))
    if top_transitions:
        detail_sections.append(("Path", top_transitions))
    if top_actors:
        detail_sections.append(("Actors", top_actors))
    if top_capabilities:
        detail_sections.append(("Capabilities", top_capabilities))
    if top_dependencies:
        detail_sections.append(("Dependencies", top_dependencies))
    if top_boundaries:
        detail_sections.append(("Boundaries to govern", top_boundaries))
    if detail_sections:
        lines.extend(
            [
                "  #v(8pt)",
                *_indented_lines(_typst_label_value_stack_lines(detail_sections, item_prefix="-"), prefix="  "),
            ]
        )
    support_notes = []
    if admissible:
        support_notes.append(("Admissible transitions", admissible))
    if valid:
        support_notes.append(("Valid options", valid))
    if blocking:
        support_notes.append(("Blocking conditions", blocking))
    if support_notes or rules:
        support_lines = _typst_label_value_stack_lines(support_notes, item_prefix="-")
        if rules:
            support_lines.extend(
                [
                    "",
                    '#text(size: 7.2pt, weight: "bold", fill: report_muted)[Policy rules in effect]',
                    "#v(2pt)",
                    *_typst_reader_bullet_lines([_reader_facing_policy_rule(rule) for rule in rules.split(",") if collapse_ws(rule)]),
                ]
            )
        lines.extend(
            [
                "  #v(8pt)",
                *_indented_lines(
                    _typst_panel_lines(
                        "Governance and controls",
                        support_lines,
                        tint="white",
                    ),
                    prefix="  ",
                ),
            ]
        )
    lines.append("]")
    return lines


def _typst_grid_table_lines(
    title: str,
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    column_count = max(1, len(headers))
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    lines.append("  #v(6pt)")
    lines.append("  #grid(")
    lines.append(f"    columns: ({', '.join(['1fr'] * column_count)}),")
    lines.append("    gutter: 4pt,")
    for header in headers:
        lines.extend(
            [
                "    block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.6pt))[",
                f'      #text(size: 7.8pt, weight: "bold", fill: report_accent)[{_typst_escape_text(header)}]',
                "    ],",
            ]
        )
    for row in rows:
        padded = tuple(row) + tuple("" for _ in range(max(0, column_count - len(row))))
        for index in range(column_count):
            cell_value = padded[index] if index < len(padded) else ""
            lines.extend(
                [
                    "    block(width: 100%, fill: white, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.4pt))[",
                    f"      {_typst_inline_content(cell_value)}",
                    "    ],",
                ]
            )
    lines.append("  )")
    lines.append("]")
    return lines


def _typst_decision_risk_matrix_lines(
    title: str,
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    *,
    tint: str = "report_panel",
    kicker: str = "",
) -> list[str]:
    parsed_rows = _decision_table_rows(headers, rows)
    lines = [
        f"#block(width: 100%, fill: {tint}, inset: 12pt, radius: 7pt, stroke: (paint: report_rule, thickness: 0.7pt))[",
        '  #set par(justify: false)',
    ]
    if collapse_ws(kicker):
        lines.append(f'  #text(size: 7.8pt, weight: "bold", fill: report_muted)[{_typst_escape_text(kicker)}]')
        lines.append("  #v(3pt)")
    lines.append(f'  #text(size: 8.4pt, weight: "bold", fill: report_accent)[{_typst_escape_text(title)}]')
    lines.append("  #v(6pt)")
    if not parsed_rows:
        lines.append("  _No decision risks were recorded._")
        lines.append("]")
        return lines
    for index, row in enumerate(parsed_rows):
        if index:
            lines.append("  #v(8pt)")
        factor = row.get("factor", "") or row.get("column_0", "")
        category = row.get("category", "") or row.get("column_1", "")
        effect = row.get("effect", "") or row.get("column_2", "")
        basis = row.get("basis", "") or row.get("column_3", "")
        lines.extend(
            [
                "  #block(width: 100%, breakable: false, fill: white, inset: 10pt, radius: 6pt, stroke: (paint: report_rule, thickness: 0.5pt))[",
                '    #set par(justify: false)',
                f'    #text(size: 9pt, weight: "bold", fill: report_accent)[{_typst_escape_text(factor or "<risk>")}]',
                "    #v(5pt)",
                "    #grid(",
                "      columns: (0.75fr, 1.25fr),",
                "      gutter: 6pt,",
                '      block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.5pt))[',
                '        #text(size: 7.2pt, weight: "bold", fill: report_muted)[Category]',
                "        #v(2pt)",
                f"        {_typst_reader_inline_content(category or '<none>')}",
                "      ],",
                '      block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.5pt))[',
                '        #text(size: 7.2pt, weight: "bold", fill: report_muted)[Effect on the decision]',
                "        #v(2pt)",
                f"        {_typst_reader_inline_content(effect or '<none>')}",
                "      ],",
                "    )",
            ]
        )
        if collapse_ws(basis):
            lines.extend(
                [
                    "    #v(6pt)",
                    '    #text(size: 7.2pt, weight: "bold", fill: report_muted)[Why it matters]',
                    "    #v(2pt)",
                    f"    {_typst_reader_inline_content(basis)}",
                ]
            )
        lines.append("  ]")
    lines.append("]")
    return lines


def _typst_grid_table_only_lines(
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
) -> list[str]:
    column_count = max(1, len(headers))
    lines = [
        "#grid(",
        f"  columns: ({', '.join(['1fr'] * column_count)}),",
        "  gutter: 4pt,",
    ]
    for header in headers:
        lines.extend(
            [
                "  block(width: 100%, fill: report_panel_alt, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.6pt))[",
                f'    #text(size: 7.8pt, weight: "bold", fill: report_accent)[{_typst_escape_text(header)}]',
                "  ],",
            ]
        )
    for row in rows:
        padded = tuple(row) + tuple("" for _ in range(max(0, column_count - len(row))))
        for index in range(column_count):
            cell_value = padded[index] if index < len(padded) else ""
            lines.extend(
                [
                    "  block(width: 100%, fill: white, inset: 6pt, radius: 4pt, stroke: (paint: report_rule, thickness: 0.4pt))[",
                    f"    {_typst_inline_content(cell_value)}",
                    "  ],",
                ]
            )
    lines.append(")")
    return lines


def _typst_source_number_map(sources: tuple[PublicationSource, ...]) -> dict[str, int]:
    return {source.source_id: index for index, source in enumerate(sources, start=1)}


def _render_exact_draft_markdown(
    publication: Publication,
    *,
    blocks: tuple[PublicationBlock, ...],
    claims: tuple[PublicationClaim, ...],
) -> str:
    block_by_id = {block.block_id: block for block in blocks}
    lines: list[str] = []
    if publication.block_ids:
        for block_id in publication.block_ids:
            block = block_by_id.get(block_id)
            if block is None or not collapse_ws(block.body):
                continue
            lines.append(block.body.rstrip())
            lines.append("")
    else:
        for claim in claims:
            if not publication_statement_is_reportable(claim.statement):
                continue
            lines.append(claim.statement.rstrip())
            lines.append("")
    while lines and not collapse_ws(lines[-1]):
        lines.pop()
    return ("\n".join(lines).rstrip() + "\n") if lines else ""


def _render_exact_draft_typst(
    publication: Publication,
    *,
    blocks: tuple[PublicationBlock, ...],
    claims: tuple[PublicationClaim, ...],
) -> str:
    block_by_id = {block.block_id: block for block in blocks}
    lines = [
        "// Generated exact draft build. Do not treat as subject truth.",
        '#let report_accent = rgb("#14324A")',
        '#let report_ink = rgb("#172230")',
        '#let report_muted = rgb("#657483")',
        '#let report_rule = rgb("#D6DEE6")',
        '#let report_panel = rgb("#F7F3EE")',
        '#let report_panel_alt = rgb("#F2F6F9")',
        '#let report_highlight = rgb("#EEE2D1")',
        '#let report_warning = rgb("#F7E6E0")',
        '#set page(',
        '  paper: "a4",',
        "  margin: (top: 22mm, bottom: 20mm, left: 22mm, right: 22mm),",
        ")",
        '#set text(size: 10.2pt, fill: report_ink)',
        '#set par(justify: true, leading: 0.7em)',
        "",
    ]
    rendered_any = False
    if publication.block_ids:
        for block_id in publication.block_ids:
            block = block_by_id.get(block_id)
            if block is None:
                continue
            parsed_table = _parse_pipe_table(block.body)
            if collapse_ws(block.block_kind) in _EXACT_DRAFT_TABLE_BLOCK_KINDS and parsed_table is not None:
                headers, rows = parsed_table
                lines.extend(_typst_grid_table_only_lines(headers, rows))
            elif collapse_ws(block.block_kind) == "review_metric_card":
                metrics = _parse_label_value_metrics(block.body)
                if metrics:
                    lines.extend(_typst_metric_grid_lines(metrics[:4]))
                else:
                    lines.extend(_typst_text_lines(block.body))
            else:
                lines.extend(_typst_text_lines(block.body))
            lines.extend(["", ""])
            rendered_any = True
    else:
        for claim in claims:
            if not publication_statement_is_reportable(claim.statement):
                continue
            lines.extend(_typst_text_lines(claim.statement))
            lines.extend(["", ""])
            rendered_any = True
    if not rendered_any:
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _typst_source_handle(source_id: str, *, source_number_by_id: dict[str, int]) -> str:
    return _typst_escape_text(_typst_source_handle_text(source_id, source_number_by_id=source_number_by_id))


def _typst_source_handle_text(source_id: str, *, source_number_by_id: dict[str, int]) -> str:
    number = source_number_by_id.get(source_id)
    if number is None:
        return source_id
    return f"[S{number}]"


def _normalized_claim_key(statement: str) -> str:
    rendered = collapse_ws(statement).casefold()
    for needle in (",", ".", ";", ":", "?", "!", "(", ")", "[", "]", "{", "}"):
        rendered = rendered.replace(needle, " ")
    return collapse_ws(rendered)


def _is_reportable_claim(claim: PublicationClaim) -> bool:
    return publication_statement_is_reportable(claim.statement)


def _reportable_claims(claims: tuple[PublicationClaim, ...]) -> tuple[PublicationClaim, ...]:
    selected: list[PublicationClaim] = []
    seen_keys: set[str] = set()
    for claim in claims:
        if not _is_reportable_claim(claim):
            continue
        claim_key = _normalized_claim_key(claim.statement)
        if not claim_key or claim_key in seen_keys:
            continue
        seen_keys.add(claim_key)
        selected.append(claim)
    return tuple(selected)


def _reportable_sections(
    sections: tuple[PublicationSection, ...],
    *,
    block_by_id: dict[str, PublicationBlock],
    reportable_claim_ids: set[str],
) -> tuple[PublicationSection, ...]:
    ordered = sorted(sections, key=lambda item: item.ordinal)
    return tuple(
        section
        for section in ordered
        if _substantive_block_ids(section, block_by_id=block_by_id)
        or any(claim_id in reportable_claim_ids for claim_id in section.claim_ids)
    )


def _section_children_in_order(
    sections: tuple[PublicationSection, ...],
    *,
    parent_section_id: str,
) -> tuple[PublicationSection, ...]:
    children = [section for section in sections if collapse_ws(section.parent_section_id) == collapse_ws(parent_section_id)]
    if not children:
        return ()
    child_by_id = {section.section_id: section for section in children}
    ordered_by_declared_ids = [
        child_by_id[child_id]
        for child_id in next(
            (section.child_section_ids for section in sections if section.section_id == parent_section_id),
            (),
        )
        if child_id in child_by_id
    ]
    if ordered_by_declared_ids:
        seen_ids = {section.section_id for section in ordered_by_declared_ids}
        ordered_by_declared_ids.extend(
            sorted(
                (section for section in children if section.section_id not in seen_ids),
                key=lambda item: item.ordinal,
            )
        )
        return tuple(ordered_by_declared_ids)
    return tuple(sorted(children, key=lambda item: item.ordinal))


def _reportable_section_entries(
    sections: tuple[PublicationSection, ...],
    *,
    publication: Publication,
    block_by_id: dict[str, PublicationBlock],
    reportable_claim_ids: set[str],
) -> tuple[tuple[PublicationSection, int, tuple[int, ...]], ...]:
    section_by_id = {section.section_id: section for section in sections}
    root_sections = [
        section_by_id[section_id]
        for section_id in publication.root_section_ids
        if section_id in section_by_id
    ]
    if not root_sections:
        root_sections = [
            section
            for section in sorted(sections, key=lambda item: item.ordinal)
            if not collapse_ws(section.parent_section_id)
        ]

    def _is_reportable_subtree(section: PublicationSection) -> bool:
        if _substantive_block_ids(section, block_by_id=block_by_id):
            return True
        if any(claim_id in reportable_claim_ids for claim_id in section.claim_ids):
            return True
        return any(_is_reportable_subtree(child) for child in _section_children_in_order(sections, parent_section_id=section.section_id))

    ordered_entries: list[tuple[PublicationSection, int, tuple[int, ...]]] = []

    def _walk(section: PublicationSection, depth: int, number_path: tuple[int, ...]) -> None:
        if not _is_reportable_subtree(section):
            return
        ordered_entries.append((section, depth, number_path))
        reportable_children = [
            child
            for child in _section_children_in_order(sections, parent_section_id=section.section_id)
            if _is_reportable_subtree(child)
        ]
        for child_index, child in enumerate(reportable_children, start=1):
            _walk(child, depth + 1, number_path + (child_index,))

    reportable_roots = [section for section in root_sections if _is_reportable_subtree(section)]
    for root_index, section in enumerate(reportable_roots, start=1):
        _walk(section, 0, (root_index,))
    return tuple(ordered_entries)


def _reader_facing_scope_summary(publication: Publication, scope_summary: str) -> str:
    rendered = collapse_ws(scope_summary)
    if not rendered or rendered.casefold().startswith("governed report projection"):
        subject_title = collapse_ws(publication.title.replace(" Report", "")) or publication.subject_id
        return f"This report summarizes the currently approved findings for {subject_title}."
    return rendered


def _executive_summary_claims(claims: tuple[PublicationClaim, ...], *, limit: int = 4) -> tuple[PublicationClaim, ...]:
    reportable = _reportable_claims(claims)
    return tuple(reportable[:limit])


def _first_block_by_kind(
    blocks: tuple[PublicationBlock, ...],
    *,
    block_kind: str,
) -> PublicationBlock | None:
    normalized_kind = collapse_ws(block_kind).casefold()
    for block in blocks:
        if collapse_ws(block.block_kind).casefold() == normalized_kind:
            return block
    return None


def _decision_summary_lines(blocks: tuple[PublicationBlock, ...]) -> tuple[str, ...]:
    block = _first_block_by_kind(blocks, block_kind="decision_summary")
    if block is None:
        return ()
    return tuple(
        collapse_ws(line)
        for line in str(block.body or "").splitlines()
        if collapse_ws(line)
    )


def _decision_summary_value(blocks: tuple[PublicationBlock, ...], prefix: str) -> str:
    normalized_prefix = collapse_ws(prefix).casefold()
    for line in _decision_summary_lines(blocks):
        if line.casefold().startswith(normalized_prefix):
            return collapse_ws(line[len(prefix):]).strip()
    return ""


def _decision_matrix_rows(
    blocks: tuple[PublicationBlock, ...],
) -> tuple[tuple[str, str, str, str], ...]:
    block = _first_block_by_kind(blocks, block_kind="decision_matrix")
    if block is None:
        return ()
    parsed = _parse_pipe_table(block.body)
    if parsed is None:
        return ()
    _headers, rows = parsed
    normalized_rows: list[tuple[str, str, str, str]] = []
    for row in rows:
        padded = tuple(row) + ("", "", "", "")
        option = collapse_ws(padded[0])
        status = collapse_ws(padded[1])
        score = collapse_ws(padded[2])
        basis = collapse_ws(padded[3])
        if option:
            normalized_rows.append((option, status, score, basis))
    return tuple(normalized_rows)


def _decision_matrix_findings(blocks: tuple[PublicationBlock, ...], *, limit: int = 4) -> tuple[str, ...]:
    findings: list[str] = []
    for option, raw_status, score, basis in _decision_matrix_rows(blocks):
        status = raw_status.casefold()
        if not option or option == "No options":
            continue
        if status in {"blocked", "pending"}:
            continue
        status_reading = {
            "recommended": "is the lead recommendation",
            "valid_but_not_executable": "remains directionally sound but stays in reserve",
            "executable": "is executable under current conditions",
            "valid": "remains valid under current conditions",
        }.get(status, f"is currently assessed as {raw_status}")
        finding = f"{option} {status_reading}"
        if score:
            finding += f" (score {score})"
        if basis:
            basis_sections = _parse_decision_basis_sections(basis)
            conclusion = next((value for label, value in basis_sections if label.casefold() == "conclusion" and collapse_ws(value)), "")
            context = next((value for label, value in basis_sections if label.casefold() == "context" and collapse_ws(value)), "")
            if conclusion:
                finding += f". {conclusion.rstrip('.')}."
            if context:
                finding += " " + context.rstrip(".") + "."
        findings.append(finding)
        if len(findings) >= limit:
            break
    return tuple(findings)


def _markdown_executive_summary_lines(
    publication: Publication,
    *,
    blocks: tuple[PublicationBlock, ...],
    fallback_scope_summary: str,
) -> tuple[str, ...]:
    summary_lines = _decision_summary_lines(blocks)
    if summary_lines:
        question = _decision_summary_value(blocks, "Decision question:")
        recommendation_status = _decision_summary_value(blocks, "Recommendation status:")
        recommended = _decision_summary_value(blocks, "Recommended options:")
        blockers = _decision_summary_value(blocks, "Blocking conditions:")
        matrix_rows = _decision_matrix_rows(blocks)
        recommended_basis = ""
        valid_reserve: list[str] = []
        blocked_options: list[str] = []
        for option, raw_status, _score, basis in matrix_rows:
            status = raw_status.casefold()
            if status == "recommended" and not recommended_basis:
                recommended_basis = basis
            elif status == "valid_but_not_executable":
                valid_reserve.append(option)
            elif status == "blocked":
                blocked_options.append(option)
        rendered: list[str] = []
        if question:
            rendered.append(f"- Decision focus: {question}")
        if recommended:
            rendered.append(f"- Recommended course: {recommended}")
        if recommendation_status:
            rendered.append(f"- Recommendation status: {recommendation_status}")
        if recommended_basis:
            rendered.append(f"- Current recommendation basis: {recommended_basis}")
        if valid_reserve:
            rendered.append(
                "- Alternatives in reserve under current conditions: "
                + ", ".join(valid_reserve[:3])
            )
        elif blockers:
            rendered.append(f"- Current blockers: {blockers}")
        elif blocked_options:
            rendered.append("- Blocked options: " + ", ".join(blocked_options[:3]))
        return tuple(rendered or summary_lines)
    return (fallback_scope_summary,)


def _markdown_key_finding_lines(
    claims: tuple[PublicationClaim, ...],
    *,
    blocks: tuple[PublicationBlock, ...],
    source_number_by_id: dict[str, int],
) -> tuple[str, ...]:
    decision_findings = _decision_matrix_findings(blocks)
    if decision_findings:
        return decision_findings
    executive_claims = _executive_summary_claims(claims)
    rendered: list[str] = []
    for claim in executive_claims:
        citations = _markdown_source_handles(claim, source_number_by_id=source_number_by_id)
        rendered.append(f"{claim.statement}{f' ({citations})' if citations else ''}")
    return tuple(rendered)


def _typst_key_finding_lines(
    claims: tuple[PublicationClaim, ...],
    *,
    blocks: tuple[PublicationBlock, ...],
) -> tuple[str, ...]:
    decision_findings = _decision_matrix_findings(blocks)
    if decision_findings:
        return decision_findings
    executive_claims = _executive_summary_claims(claims)
    return tuple(claim.statement for claim in executive_claims)


def _substantive_block_ids(
    section: PublicationSection,
    *,
    block_by_id: dict[str, PublicationBlock],
) -> tuple[str, ...]:
    return tuple(
        block_id
        for block_id in section.block_ids
        if collapse_ws(block_by_id.get(block_id).block_kind if block_by_id.get(block_id) is not None else "").casefold()
        not in _METADATA_ONLY_BLOCK_KINDS
    )


def _section_has_decision_blocks(
    section: PublicationSection,
    *,
    block_by_id: dict[str, PublicationBlock],
) -> bool:
    for block_id in _substantive_block_ids(section, block_by_id=block_by_id):
        block = block_by_id.get(block_id)
        if block is None:
            continue
        if collapse_ws(block.block_kind).casefold() in _DECISION_SECTION_BLOCK_KINDS:
            return True
    return False


def _substantive_sections(
    sections: tuple[PublicationSection, ...],
    *,
    block_by_id: dict[str, PublicationBlock],
) -> tuple[PublicationSection, ...]:
    ordered = sorted(sections, key=lambda item: item.ordinal)
    return tuple(
        section
        for section in ordered
        if section.claim_ids or _substantive_block_ids(section, block_by_id=block_by_id)
    )


def _claim_kind_counts(claims: tuple[PublicationClaim, ...]) -> dict[str, int]:
    counts = {
        "descriptive": 0,
        "interpretive": 0,
        "procedural": 0,
    }
    for claim in claims:
        normalized = collapse_ws(claim.claim_kind).casefold()
        if normalized in counts:
            counts[normalized] += 1
    return counts


def _typst_section_divider_lines(section: PublicationSection, *, section_label: str, claim_count: int) -> list[str]:
    claim_suffix = f" | {claim_count} CLAIMS" if claim_count else ""
    return [
        "#pagebreak()",
        "",
        "#block(width: 100%, fill: report_accent, inset: (top: 8pt, right: 12pt, bottom: 8pt, left: 12pt), radius: 8pt)[",
        '  #set par(justify: false)',
        f'  #text(size: 8pt, weight: "bold", fill: white)[SECTION {_typst_escape_text(section_label.zfill(2))} | {_typst_escape_text(section.role.upper())}{_typst_escape_text(claim_suffix)}]',
        "  #v(6pt)",
        f'  #text(size: 20pt, weight: "bold", fill: white)[{_typst_escape_text(section.title)}]',
        "]",
        "",
    ]


def _typst_claim_panel_lines(
    claim: PublicationClaim,
    *,
    source_by_id: dict[str, PublicationSource],
    source_number_by_id: dict[str, int],
) -> list[str]:
    panel_tint = {
        "descriptive": "report_panel_alt",
        "procedural": "report_highlight",
        "interpretive": "report_panel",
    }.get(collapse_ws(claim.claim_kind).casefold(), "report_panel_alt")
    body_lines: list[str] = [
        f'#text(size: 10.4pt, weight: "bold", fill: report_ink)[{_typst_inline_content(claim.statement)}]',
    ]
    if claim.related_unit_ids:
        body_lines.extend(
            [
                "",
                f'#text(size: 8pt, weight: "bold", fill: report_muted)[Traceable units]',
                "- " + ", ".join(_typst_escape_text(unit_id) for unit_id in claim.related_unit_ids),
            ]
        )
    if claim.source_ids:
        citations = [
            f"- {_typst_source_handle(source_id, source_number_by_id=source_number_by_id)} {_typst_escape_text(source_by_id[source_id].title)}"
            for source_id in claim.source_ids
            if source_id in source_by_id
        ]
        if citations:
            body_lines.extend(
                [
                    "",
                    f'#text(size: 8pt, weight: "bold", fill: report_muted)[Source basis]',
                    *citations,
                ]
            )
    return _typst_panel_lines(
        "Finding",
        body_lines,
        tint=panel_tint,
        kicker=claim.claim_kind.upper() or "FINDING",
    )


def _typst_source_panel_lines(source: PublicationSource, *, source_number: int) -> list[str]:
    body_lines: list[str] = [_typst_escape_text(source.source_ref or "<unavailable>")]
    if collapse_ws(source.published_at):
        body_lines.extend(
            [
                "",
                f'#text(size: 8pt, weight: "bold", fill: report_muted)[Published]',
                _typst_escape_text(source.published_at),
            ]
        )
    if collapse_ws(source.excerpt):
        body_lines.extend(
            [
                "",
                f'#text(size: 8pt, weight: "bold", fill: report_muted)[Relevance]',
                *_typst_text_lines(source.excerpt),
            ]
        )
    return _typst_panel_lines(
        source.title or source.source_id,
        body_lines,
        tint="report_panel_alt",
        kicker=f"Source {source_number:02d}",
    )


def _markdown_source_handles(
    claim: PublicationClaim,
    *,
    source_number_by_id: dict[str, int],
) -> str:
    handles = [
        f"[S{source_number_by_id[source_id]}]"
        for source_id in claim.source_ids
        if source_id in source_number_by_id
    ]
    return ", ".join(handles)


def _typst_claim_bullet_lines(
    claim: PublicationClaim,
    *,
    source_number_by_id: dict[str, int],
) -> list[str]:
    citation_text = ", ".join(
        _typst_source_handle_text(source_id, source_number_by_id=source_number_by_id)
        for source_id in claim.source_ids
        if source_id in source_number_by_id
    )
    statement = _typst_inline_content(claim.statement)
    lines = [f"- {statement}"]
    if citation_text:
        lines.append(
            f'  #text(size: 8pt, fill: report_muted)[Sources: {_typst_escape_text(citation_text)}]'
        )
    return lines


def render_publication_markdown(
    publication: Publication,
    *,
    sections: tuple[PublicationSection, ...],
    blocks: tuple[PublicationBlock, ...] = (),
    claims: tuple[PublicationClaim, ...],
    sources: tuple[PublicationSource, ...],
) -> str:
    if collapse_ws(publication.publication_type).casefold() == "exact_draft":
        return _render_exact_draft_markdown(publication, blocks=blocks, claims=claims)
    block_by_id = {block.block_id: block for block in blocks}
    claim_by_id = {claim.claim_id: claim for claim in claims}
    source_by_id = {source.source_id: source for source in sources}
    source_number_by_id = _typst_source_number_map(sources)
    reportable_claims = _reportable_claims(claims)
    reportable_claim_id_set = {claim.claim_id for claim in reportable_claims}
    raw_scope_summary = collapse_ws(publication.scope_summary) or (
        f"Governed report projection derived from the current LearningContext snapshot for {publication.subject_id}."
    )
    scope_summary = _reader_facing_scope_summary(publication, raw_scope_summary)
    executive_summary_lines = _markdown_executive_summary_lines(
        publication,
        blocks=blocks,
        fallback_scope_summary=scope_summary,
    )
    key_finding_lines = _typst_key_finding_lines(
        reportable_claims,
        blocks=blocks,
    )
    lines = [
        f"# {publication.title}",
        "",
        scope_summary,
        "",
        "## Executive Summary",
        "",
        *executive_summary_lines,
        "",
        "## Key Findings",
        "",
    ]
    if key_finding_lines:
        for line in key_finding_lines:
            lines.append(f"- {line}")
    else:
        lines.append("- No substantive findings are available yet.")
    lines.append("")
    for section, depth, number_path in _reportable_section_entries(
        sections,
        publication=publication,
        block_by_id=block_by_id,
        reportable_claim_ids=reportable_claim_id_set,
    ):
        include_section_claims = not _section_has_decision_blocks(section, block_by_id=block_by_id)
        heading_level = min(2 + depth, 6)
        section_label = ".".join(str(part) for part in number_path)
        lines.extend([f"<!-- section-id: {section.section_id} -->", f"{'#' * heading_level} {section_label} {section.title}", ""])
        for block_id in _substantive_block_ids(section, block_by_id=block_by_id):
            lines.extend(_render_markdown_block_lines(block_id, block_by_id=block_by_id))
            lines.append("")
        if include_section_claims:
            for claim_id in section.claim_ids:
                if claim_id not in reportable_claim_id_set:
                    continue
                claim = claim_by_id[claim_id]
                citations = _markdown_source_handles(claim, source_number_by_id=source_number_by_id)
                lines.append(f"- {claim.statement}{f' ({citations})' if citations else ''}")
        lines.append("")
    lines.extend(["## Sources", ""])
    if sources:
        for source in sources:
            handle = f"[S{source_number_by_id[source.source_id]}]" if source.source_id in source_number_by_id else source.source_id
            lines.append(f"- {handle} {source.title} — {source.source_ref}")
    else:
        lines.append("_No sources._")
    lines.extend(
        [
            "",
            "## Build Notes",
            "",
            f"- Built from subject `{publication.subject_id}` at snapshot `{publication.learning_context_snapshot_hash}`.",
            f"- Publication id: `{publication.publication_id}`.",
        ]
    )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_publication_typst(
    publication: Publication,
    *,
    sections: tuple[PublicationSection, ...],
    blocks: tuple[PublicationBlock, ...] = (),
    claims: tuple[PublicationClaim, ...],
    sources: tuple[PublicationSource, ...],
) -> str:
    if collapse_ws(publication.publication_type).casefold() == "exact_draft":
        return _render_exact_draft_typst(publication, blocks=blocks, claims=claims)
    block_by_id = {block.block_id: block for block in blocks}
    claim_by_id = {claim.claim_id: claim for claim in claims}
    source_by_id = {source.source_id: source for source in sources}
    source_number_by_id = _typst_source_number_map(sources)
    reportable_claims = _reportable_claims(claims)
    reportable_claim_id_set = {claim.claim_id for claim in reportable_claims}
    raw_scope_summary = collapse_ws(publication.scope_summary) or (
        f"Governed report projection derived from the current LearningContext snapshot for {publication.subject_id}."
    )
    scope_summary = _reader_facing_scope_summary(publication, raw_scope_summary)
    executive_summary_lines = _markdown_executive_summary_lines(
        publication,
        blocks=blocks,
        fallback_scope_summary=scope_summary,
    )
    key_finding_lines = _typst_key_finding_lines(
        reportable_claims,
        blocks=blocks,
    )
    body_section_entries = _reportable_section_entries(
        sections,
        publication=publication,
        block_by_id=block_by_id,
        reportable_claim_ids=reportable_claim_id_set,
    )
    section_titles = tuple(
        ("  " * depth + ".".join(str(part) for part in number_path) + " " + section.title)
        for section, depth, number_path in body_section_entries
        if depth <= 1
    )
    lines = [
        "// Generated publication build. Do not treat as subject truth.",
        '#let report_accent = rgb("#14324A")',
        '#let report_ink = rgb("#172230")',
        '#let report_muted = rgb("#657483")',
        '#let report_rule = rgb("#D6DEE6")',
        '#let report_panel = rgb("#F7F3EE")',
        '#let report_panel_alt = rgb("#F2F6F9")',
        '#let report_highlight = rgb("#EEE2D1")',
        '#let report_warning = rgb("#F7E6E0")',
        '#set page(',
        '  paper: "a4",',
        "  margin: (top: 22mm, bottom: 20mm, left: 22mm, right: 22mm),",
        '  numbering: "1",',
        "  number-align: right + bottom,",
        f'  header: align(right)[#text(size: 8pt, fill: report_muted)[{_typst_escape_text(publication.title)}]],',
        ")",
        '#set text(size: 10.2pt, fill: report_ink)',
        '#set par(justify: true, leading: 0.7em)',
        '#set heading(numbering: "1.")',
        "",
        "#align(left)[",
        f'  #text(size: 8.5pt, weight: "bold", fill: report_accent)[GOVERNED INSIGHT REPORT]',
        "  #v(9pt)",
        f'  #text(size: 24pt, weight: "bold", fill: report_ink)[{_typst_escape_text(publication.title)}]',
        "  #v(7pt)",
        f'  #text(size: 11pt, fill: report_muted)[{_typst_escape_text(scope_summary)}]',
        "  #v(10pt)",
        f'  #text(size: 8.4pt, fill: report_muted)[Snapshot {_typst_escape_text(publication.learning_context_snapshot_hash[:8] or "<pending>")} | {len(claims)} findings | {len(sources)} sources]',
        "]",
        "",
        "#pagebreak()",
        "",
        "= Executive Summary <executive-summary>",
        "",
        *[
            line
            for line in _typst_panel_lines(
                "What this report covers",
                [line for entry in executive_summary_lines for line in _typst_text_lines(entry)],
                tint="report_highlight",
                kicker="EXECUTIVE SUMMARY",
            )
        ],
        "",
        *[
            line
            for line in _typst_panel_lines(
                "Key Findings",
                (
                    [line for finding in key_finding_lines for line in _typst_bullet_lines((finding,))]
                    or ["- _No substantive findings are available yet._"]
                ),
                tint="report_panel",
                kicker="HEADLINE FINDINGS",
            )
        ],
        "",
        *[
            line
            for line in _typst_panel_lines(
                "What comes next",
                _typst_bullet_lines(section_titles),
                tint="report_panel_alt",
                kicker="READING GUIDE",
            )
        ],
        "",
    ]
    for section, depth, number_path in body_section_entries:
        include_section_claims = not _section_has_decision_blocks(section, block_by_id=block_by_id)
        section_claims = (
            tuple(
                claim_by_id[claim_id]
                for claim_id in section.claim_ids
                if claim_id in reportable_claim_id_set
            )
            if include_section_claims
            else ()
        )
        section_label = ".".join(str(part) for part in number_path)
        if depth == 0:
            lines.extend(_typst_section_divider_lines(section, section_label=section_label, claim_count=len(section_claims)))
        else:
            lines.extend(
                [
                    f'#heading(level: {depth + 1}, numbering: none)[{_typst_escape_text(section_label)}. {_typst_escape_text(section.title)}] <{section.section_id}>',
                    "",
                ]
            )
        for block_id in _substantive_block_ids(section, block_by_id=block_by_id):
            lines.extend(_render_typst_block_lines(block_id, block_by_id=block_by_id))
            lines.append("")
        for claim in section_claims:
            lines.extend(_typst_claim_bullet_lines(claim, source_number_by_id=source_number_by_id))
            lines.append("")
    lines.extend(["#pagebreak()", "", "= Sources <sources>", ""])
    if sources:
        lines.extend(
            _typst_panel_lines(
                "Source Register",
                [
                    "Each source is assigned a numbered handle for compact reference inside the report body.",
                    "",
                    *[
                        f"- {_typst_source_handle(source.source_id, source_number_by_id=source_number_by_id)} {_typst_escape_text(source.title)}"
                        for source in sources[:6]
                    ],
                ],
                tint="report_panel",
                kicker="SOURCE GUIDE",
            )
        )
        lines.append("")
        for source in sources:
            lines.extend(
                _typst_source_panel_lines(
                    source,
                    source_number=source_number_by_id.get(source.source_id, 0),
                )
            )
            lines.append("")
    else:
        lines.extend(
            _typst_panel_lines(
                "No external sources recorded",
                ["The current publication snapshot does not carry source references."],
                tint="report_panel_alt",
                kicker="SOURCE REGISTER",
            )
        )
        lines.append("")
    lines.extend(
        [
            "",
            "= Build Notes <report-controls>",
            "",
            *[
                line
                for line in _typst_panel_lines(
                    "Build Notes",
                    [
                        f"- Built from subject {_typst_escape_text(publication.subject_id)}.",
                        f"- Snapshot {_typst_escape_text(publication.learning_context_snapshot_hash or '<pending>')}.",
                        f"- Publication id {_typst_escape_text(publication.publication_id)}.",
                    ],
                    tint="report_panel",
                    kicker="APPENDIX",
                )
            ],
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def validate_rendered_typst(report_typ: str) -> tuple[dict[str, object], bytes | None]:
    typst_bin = shutil.which("typst")
    if not typst_bin:
        return (
            {
                "status": "unavailable",
                "tool": "typst",
                "reason": "typst_not_installed",
            },
            None,
        )
    with runtime_temporary_directory(prefix="publication-typst-validate-") as tempdir_text:
        tempdir = Path(tempdir_text)
        typ_path = tempdir / "report.typ"
        pdf_path = tempdir / "report.pdf"
        typ_path.write_text(report_typ, encoding="utf-8")
        process = subprocess.run(
            [typst_bin, "compile", str(typ_path), str(pdf_path)],
            capture_output=True,
            text=True,
        )
        if process.returncode == 0 and pdf_path.is_file():
            return (
                {
                    "status": "ok",
                    "tool": "typst",
                    "output_path": str(pdf_path),
                },
                pdf_path.read_bytes(),
            )
        return (
            {
                "status": "error",
                "tool": "typst",
                "returncode": process.returncode,
                "stdout": collapse_ws(process.stdout),
                "stderr": collapse_ws(process.stderr),
            },
            None,
        )


def publication_build_from_rendered_outputs(
    publication: Publication,
    *,
    learning_context_snapshot_hash: str,
    validation_report: dict[str, object],
    report_typ: str,
    report_md: str,
    report_pdf: bytes | None = None,
    renderer_id: str = "publication_render",
    renderer_version: str = "v1",
    template_id: str = "report",
    template_version: str = "v1",
    build_epoch_ms: int = 0,
) -> tuple[PublicationBuild, tuple[RenderArtifact, ...], dict[str, str], dict[str, bytes]]:
    build_id = stable_publication_build_id(
        publication_snapshot_hash=publication.content_hash(),
        learning_context_snapshot_hash=learning_context_snapshot_hash,
        renderer_id=renderer_id,
        template_id=template_id,
    )
    output_texts = {
        "report.typ": report_typ,
        "report.md": report_md,
    }
    output_blobs: dict[str, bytes] = {}
    if report_pdf is not None:
        output_blobs["report.pdf"] = report_pdf
    render_artifacts_list: list[RenderArtifact] = []
    for name, text in output_texts.items():
        render_artifacts_list.append(
            RenderArtifact(
                artifact_id=f"render_{collapse_ws(name).replace('.', '_')}",
                publication_id=publication.publication_id,
                build_id=build_id,
                format=name.rsplit(".", 1)[-1],
                path=f"outputs/{build_id}/{name}",
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
    for name, blob in output_blobs.items():
        render_artifacts_list.append(
            RenderArtifact(
                artifact_id=f"render_{collapse_ws(name).replace('.', '_')}",
                publication_id=publication.publication_id,
                build_id=build_id,
                format=name.rsplit(".", 1)[-1],
                path=f"outputs/{build_id}/{name}",
                content_hash=hashlib.sha256(blob).hexdigest(),
            )
        )
    render_artifacts = tuple(render_artifacts_list)
    build = PublicationBuild(
        build_id=build_id,
        publication_id=publication.publication_id,
        publication_snapshot_hash=publication.content_hash(),
        learning_context_snapshot_hash=learning_context_snapshot_hash,
        renderer_id=renderer_id,
        renderer_version=renderer_version,
        template_id=template_id,
        template_version=template_version,
        build_status="ok" if validation_report.get("status") == "ok" else "error",
        started_at_epoch_ms=build_epoch_ms,
        finished_at_epoch_ms=build_epoch_ms,
        validation_report=validation_report,
        render_artifact_ids=tuple(artifact.artifact_id for artifact in render_artifacts),
    )
    return build, render_artifacts, output_texts, output_blobs
