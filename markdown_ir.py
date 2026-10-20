# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections.abc import Mapping, Sequence


MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
MARKDOWN_BULLET_RE = re.compile(r"^\s*[-*+]\s+(.*\S)\s*$")
MARKDOWN_FENCE_RE = re.compile(r"^\s*```")

MATH_IDENTIFIER_STOP_WORDS = {
    "sqrt",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "log",
    "log10",
    "ln",
    "exp",
    "abs",
    "min",
    "max",
    "pow",
    "math",
    "pi",
    "e",
}

CONTRACT_IDENTIFIER_STOP_WORDS = {
    "and",
    "or",
    "the",
    "an",
    "to",
    "from",
    "given",
    "return",
    "returns",
    "input",
    "inputs",
    "output",
    "outputs",
}


def is_contract_identifier_candidate(value: str) -> bool:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with deciding whether contract identifier candidate.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `is_contract_identifier_candidate(value='force')`
        Output: True

    Args:
        value: Value for `value` used by `is_contract_identifier_candidate`. Expected type: `str`.

    Returns:
        bool: Result produced by `is_contract_identifier_candidate`.
    """
    normalized = str(value or "").strip()
    if not normalized:
        return False
    if len(normalized) == 1:
        return True
    return normalized.lower() not in CONTRACT_IDENTIFIER_STOP_WORDS

GENERIC_SYNTHESIS_FIELD_NAMES = {
    "input",
    "input1",
    "input2",
    "input_1",
    "input_2",
    "output",
    "derived_output",
    "result",
    "value",
}


def collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with collapsing ws.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `collapse_ws(text='Compute force from mass and acceleration.')`
        Output: 'F = m * a'

    Args:
        text: Value for `text` used by `collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text)).strip()


def ordered_unique(values: Sequence[str] | list[str] | tuple[str, ...]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling ordered unique.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `ordered_unique(values=[3, 4, 12])`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        values: Value for `values` used by `ordered_unique`. Expected type: `Sequence[str] | list[str] | tuple[str, ...]`.

    Returns:
        list[str]: Result produced by `ordered_unique`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def titleize_semantic_unit(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling titleize semantic unit.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `titleize_semantic_unit(text='Compute force from mass and acceleration.')`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        text: Value for `text` used by `titleize_semantic_unit`. Expected type: `str`.

    Returns:
        str: Result produced by `titleize_semantic_unit`.
    """
    words = [part for part in re.findall(r"[A-Za-z0-9]+", text) if part]
    return " ".join(word.capitalize() for word in words)


@dataclass
class MarkdownSectionIR:
    heading: str
    level: int
    path: list[str]
    paragraphs: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    equations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "heading": self.heading,
            "level": self.level,
            "path": list(self.path),
            "paragraphs": list(self.paragraphs),
            "bullets": list(self.bullets),
            "code_blocks": list(self.code_blocks),
            "equations": list(self.equations),
        }


@dataclass
class MarkdownDocumentIR:
    title: str
    source_path: str
    intro_paragraphs: list[str] = field(default_factory=list)
    intro_bullets: list[str] = field(default_factory=list)
    sections: list[MarkdownSectionIR] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "title": self.title,
            "source_path": self.source_path,
            "intro_paragraphs": list(self.intro_paragraphs),
            "intro_bullets": list(self.intro_bullets),
            "sections": [section.to_dict() for section in self.sections],
        }

    def prompt_view(self, *, max_sections: int = 12) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with building a view of prompt.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `prompt_view(max_sections=3)`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.
            max_sections: Value for `max_sections` used by `prompt_view`. Expected type: `int`. Defaults to `12`.

        Returns:
            dict[str, Any]: Result produced by `prompt_view`.
        """
        clusters = markdown_document_clusters(self)
        return {
            "title": self.title,
            "source_path": self.source_path,
            "intro_paragraphs": self.intro_paragraphs[:3],
            "intro_bullets": self.intro_bullets[:6],
            "section_count": len(self.sections),
            "clusters": clusters[:max_sections],
        }


def markdown_prompt_fragment(text: str, *, max_chars: int) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown prompt fragment.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_prompt_fragment(text='Compute force from mass and acceleration.', max_chars=3)`
        Output: 'F = m * a'

    Args:
        text: Value for `text` used by `markdown_prompt_fragment`. Expected type: `str`.
        max_chars: Value for `max_chars` used by `markdown_prompt_fragment`. Expected type: `int`.

    Returns:
        str: Result produced by `markdown_prompt_fragment`.
    """
    cleaned = collapse_ws(str(text or "").strip())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def markdown_line_is_equation(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown line is equation.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_line_is_equation(text='Compute force from mass and acceleration.')`
        Output: True

    Args:
        text: Value for `text` used by `markdown_line_is_equation`. Expected type: `str`.

    Returns:
        bool: Result produced by `markdown_line_is_equation`.
    """
    stripped = collapse_ws(text)
    if not stripped:
        return False
    return any(marker in stripped for marker in ("=", "=>", "->", "⇒", "∝"))


def parse_markdown_document_ir(markdown_text: str, *, source_path: str = "") -> MarkdownDocumentIR:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with parsing markdown document ir.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `parse_markdown_document_ir(markdown_text='Compute force from mass and acceleration.', source_path='/tmp/physics_force.md')`
        Output: MarkdownDocumentIR(title='Physics Force Lesson')

    Args:
        markdown_text: Value for `markdown_text` used by `parse_markdown_document_ir`. Expected type: `str`.
        source_path: Value for `source_path` used by `parse_markdown_document_ir`. Expected type: `str`. Defaults to `''`.

    Returns:
        MarkdownDocumentIR: Result produced by `parse_markdown_document_ir`.
    """
    lines = markdown_text.splitlines()
    title = ""
    intro_paragraphs: list[str] = []
    intro_bullets: list[str] = []
    sections: list[MarkdownSectionIR] = []
    heading_stack: list[str] = []
    current_section: MarkdownSectionIR | None = None
    paragraph_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code_block = False

    def add_paragraph(text: str) -> None:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling add paragraph.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `add_paragraph(text='Compute force from mass and acceleration.')`
            Output: None

        Args:
            text: Value for `text` used by `add_paragraph`. Expected type: `str`.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        target = intro_paragraphs if current_section is None else current_section.paragraphs
        target.append(text)
        if current_section is not None and markdown_line_is_equation(text):
            current_section.equations.append(text)

    def flush_paragraph() -> None:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling flush paragraph.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `flush_paragraph()`
            Output: None

        Args:
            None.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        nonlocal paragraph_buffer
        if not paragraph_buffer:
            return
        text = collapse_ws(" ".join(paragraph_buffer))
        paragraph_buffer = []
        if text:
            add_paragraph(text)

    def flush_code() -> None:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling flush code.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `flush_code()`
            Output: None

        Args:
            None.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        nonlocal code_buffer
        if not code_buffer:
            return
        text = "\n".join(code_buffer).strip()
        code_buffer = []
        if text and current_section is not None:
            current_section.code_blocks.append(text)

    for raw_line in lines:
        if MARKDOWN_FENCE_RE.match(raw_line):
            flush_paragraph()
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue
        if in_code_block:
            code_buffer.append(raw_line.rstrip("\n"))
            continue

        heading_match = MARKDOWN_HEADING_RE.match(raw_line)
        if heading_match:
            flush_paragraph()
            heading_level = len(heading_match.group(1))
            heading_text = collapse_ws(heading_match.group(2).strip().strip("#").strip())
            if not heading_text:
                continue
            if heading_level == 1 and not title:
                title = heading_text
                heading_stack = [heading_text]
                current_section = None
                continue
            while len(heading_stack) >= heading_level:
                heading_stack.pop()
            heading_stack.append(heading_text)
            current_section = MarkdownSectionIR(
                heading=heading_text,
                level=heading_level,
                path=list(heading_stack),
            )
            sections.append(current_section)
            continue

        bullet_match = MARKDOWN_BULLET_RE.match(raw_line)
        if bullet_match:
            flush_paragraph()
            text = collapse_ws(bullet_match.group(1))
            if not text:
                continue
            target = intro_bullets if current_section is None else current_section.bullets
            target.append(text)
            if current_section is not None and markdown_line_is_equation(text):
                current_section.equations.append(text)
            continue

        stripped = raw_line.strip()
        if not stripped:
            flush_paragraph()
            continue
        paragraph_buffer.append(stripped)

    flush_paragraph()
    flush_code()

    if not title:
        title = titleize_semantic_unit(Path(source_path).stem) or "Markdown Source"

    return MarkdownDocumentIR(
        title=title,
        source_path=source_path,
        intro_paragraphs=intro_paragraphs,
        intro_bullets=intro_bullets,
        sections=sections,
    )


def markdown_document_clusters(document: MarkdownDocumentIR) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown document clusters.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_document_clusters(document=MarkdownDocumentIR(title='Physics Force Lesson'))`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `markdown_document_clusters`. Expected type: `MarkdownDocumentIR`.

    Returns:
        list[dict[str, Any]]: Result produced by `markdown_document_clusters`.
    """
    clusters: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def ensure_cluster(section: MarkdownSectionIR) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling ensure cluster.

        Reference to Theory:
            Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

        Example Input Output:
            Input: `ensure_cluster(section=MarkdownSectionIR(title='Force From Mass And Acceleration'))`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            section: Value for `section` used by `ensure_cluster`. Expected type: `MarkdownSectionIR`.

        Returns:
            dict[str, Any]: Result produced by `ensure_cluster`.
        """
        nonlocal current
        if current is None or section.level <= 2:
            current = {
                "heading": section.heading,
                "path": list(section.path),
                "sections": [],
                "paragraphs": [],
                "bullets": [],
                "equations": [],
                "code_blocks": [],
            }
            clusters.append(current)
        return current

    for section in document.sections:
        cluster = ensure_cluster(section)
        cluster["sections"].append(section.heading)
        cluster["paragraphs"].extend(section.paragraphs)
        cluster["bullets"].extend(section.bullets)
        cluster["equations"].extend(section.equations)
        cluster["code_blocks"].extend(section.code_blocks)

    normalized: list[dict[str, Any]] = []
    for cluster in clusters:
        normalized.append(
            {
                "heading": cluster["heading"],
                "path": cluster["path"],
                "sections": ordered_unique(cluster["sections"]),
                "paragraphs": cluster["paragraphs"][:3],
                "bullets": cluster["bullets"][:6],
                "equations": ordered_unique(cluster["equations"])[:4],
                "code_blocks": [str(item).strip() for item in cluster["code_blocks"][:2] if str(item).strip()],
            }
        )
    return normalized


def compact_markdown_cluster_for_prompt(
    cluster: Mapping[str, Any],
    *,
    paragraph_limit: int = 1,
    bullet_limit: int = 3,
    equation_limit: int = 2,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling compact markdown cluster for prompt.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `compact_markdown_cluster_for_prompt(cluster={'title': 'Physics / Force / Force From Mass And Acceleration'}, paragraph_limit=3, bullet_limit=3, equation_limit=3)`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        cluster: Value for `cluster` used by `compact_markdown_cluster_for_prompt`. Expected type: `Mapping[str, Any]`.
        paragraph_limit: Value for `paragraph_limit` used by `compact_markdown_cluster_for_prompt`. Expected type: `int`. Defaults to `1`.
        bullet_limit: Value for `bullet_limit` used by `compact_markdown_cluster_for_prompt`. Expected type: `int`. Defaults to `3`.
        equation_limit: Value for `equation_limit` used by `compact_markdown_cluster_for_prompt`. Expected type: `int`. Defaults to `2`.

    Returns:
        dict[str, Any]: Result produced by `compact_markdown_cluster_for_prompt`.
    """
    paragraphs = [
        markdown_prompt_fragment(str(item).strip(), max_chars=220)
        for item in cluster.get("paragraphs", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("paragraphs", []), list) else []
    bullets = [
        markdown_prompt_fragment(str(item).strip(), max_chars=140)
        for item in cluster.get("bullets", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("bullets", []), list) else []
    equations = [
        markdown_prompt_fragment(str(item).strip(), max_chars=120)
        for item in cluster.get("equations", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("equations", []), list) else []
    code_blocks = [
        markdown_prompt_fragment(str(item).strip(), max_chars=280)
        for item in cluster.get("code_blocks", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("code_blocks", []), list) else []
    sections = [
        collapse_ws(str(item).strip())
        for item in cluster.get("sections", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("sections", []), list) else []
    path = [
        collapse_ws(str(item).strip())
        for item in cluster.get("path", [])
        if collapse_ws(str(item).strip())
    ] if isinstance(cluster.get("path", []), list) else []
    return {
        "heading": collapse_ws(str(cluster.get("heading", "")).strip()),
        "path": path[-3:],
        "sections": sections[:3],
        "candidate_kinds": markdown_cluster_candidate_kinds(cluster),
        "equation_bearing": bool(equations),
        "code_bearing": bool(code_blocks),
        "paragraph_fragments": paragraphs[:paragraph_limit],
        "bullet_fragments": bullets[:bullet_limit],
        "equation_fragments": equations[:equation_limit],
        "code_block_fragments": code_blocks[:1],
        "omitted": {
            "paragraphs": max(0, len(paragraphs) - paragraph_limit),
            "bullets": max(0, len(bullets) - bullet_limit),
            "equations": max(0, len(equations) - equation_limit),
            "code_blocks": max(0, len(code_blocks) - 1),
        },
    }


def bounded_markdown_learning_prompt_view(
    document: MarkdownDocumentIR,
    *,
    max_clusters: int = 6,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with building a view of bounded markdown learning prompt.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `bounded_markdown_learning_prompt_view(document=MarkdownDocumentIR(title='Physics Force Lesson'), max_clusters=3)`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `bounded_markdown_learning_prompt_view`. Expected type: `MarkdownDocumentIR`.
        max_clusters: Value for `max_clusters` used by `bounded_markdown_learning_prompt_view`. Expected type: `int`. Defaults to `6`.

    Returns:
        dict[str, Any]: Result produced by `bounded_markdown_learning_prompt_view`.
    """
    clusters = markdown_document_clusters(document)
    intro_paragraphs = [
        markdown_prompt_fragment(item, max_chars=220)
        for item in document.intro_paragraphs[:1]
        if collapse_ws(item)
    ]
    intro_bullets = [
        markdown_prompt_fragment(item, max_chars=140)
        for item in document.intro_bullets[:4]
        if collapse_ws(item)
    ]
    return {
        "title": document.title,
        "source_path": document.source_path,
        "section_count": len(document.sections),
        "cluster_count": len(clusters),
        "clusters_omitted": max(0, len(clusters) - max_clusters),
        "intro_paragraph_fragments": intro_paragraphs,
        "intro_bullet_fragments": intro_bullets,
        "clusters": [
            compact_markdown_cluster_for_prompt(cluster)
            for cluster in clusters[:max_clusters]
        ],
    }


def markdown_cluster_candidate_kinds(cluster: Mapping[str, Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown cluster candidate kinds.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_cluster_candidate_kinds(cluster={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        cluster: Value for `cluster` used by `markdown_cluster_candidate_kinds`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[str]: Result produced by `markdown_cluster_candidate_kinds`.
    """
    candidates: list[str] = []
    heading = str(cluster.get("heading", "")).strip().lower()
    sections = [str(item).strip().lower() for item in cluster.get("sections", []) if str(item).strip()]
    paragraphs = [str(item).strip() for item in cluster.get("paragraphs", []) if str(item).strip()]
    bullets = [str(item).strip() for item in cluster.get("bullets", []) if str(item).strip()]
    equations = [str(item).strip() for item in cluster.get("equations", []) if str(item).strip()]

    if equations:
        candidates.append("equation")
    lowered_text = " ".join([heading, *sections, *paragraphs, *bullets]).lower()
    if any(token in lowered_text for token in ("law", "if", "unless", "therefore", "equal", "opposite")):
        candidates.append("logic")
    if any(token in lowered_text for token in ("how to", "step", "procedure", "calculate", "compute")) or equations:
        candidates.append("template")
    if any(token in lowered_text for token in (" is ", " are ", "describe", "means", "form the foundation")):
        candidates.append("definition")
    if bullets or "summary" in heading:
        candidates.append("summary")
    if any(token in lowered_text for token in ("example", "for example", "if a force")):
        candidates.append("example")
    candidates.append("other")
    return ordered_unique(candidates)


def markdown_learning_encounter_view(document: MarkdownDocumentIR) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with building a view of markdown learning encounter.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_learning_encounter_view(document=MarkdownDocumentIR(title='Physics Force Lesson'))`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `markdown_learning_encounter_view`. Expected type: `MarkdownDocumentIR`.

    Returns:
        list[dict[str, Any]]: Result produced by `markdown_learning_encounter_view`.
    """
    encounters: list[dict[str, Any]] = []
    for index, cluster in enumerate(markdown_document_clusters(document), start=1):
        encounters.append(
            {
                "encounter_id": f"cluster_{index}",
                "heading": str(cluster.get("heading", "")).strip(),
                "path": list(cluster.get("path", [])),
                "sections": list(cluster.get("sections", [])),
                "candidate_kinds": markdown_cluster_candidate_kinds(cluster),
                "equation_bearing": bool(cluster.get("equations")),
                "code_bearing": bool(cluster.get("code_blocks")),
                "paragraphs": list(cluster.get("paragraphs", [])),
                "bullets": list(cluster.get("bullets", [])),
                "equations": list(cluster.get("equations", [])),
                "code_blocks": list(cluster.get("code_blocks", [])),
            }
        )
    return encounters


def compact_markdown_encounter_records(
    encounters: Sequence[Mapping[str, Any]],
    *,
    max_encounters: int = 8,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling compact markdown encounter records.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `compact_markdown_encounter_records(encounters={'title': 'Physics / Force / Force From Mass And Acceleration'}, max_encounters=3)`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'lookup_keys': ['force', 'mass', 'acceleration']}

    Args:
        encounters: Value for `encounters` used by `compact_markdown_encounter_records`. Expected type: `Sequence[Mapping[str, Any]]`.
        max_encounters: Value for `max_encounters` used by `compact_markdown_encounter_records`. Expected type: `int`. Defaults to `8`.

    Returns:
        dict[str, Any]: Result produced by `compact_markdown_encounter_records`.
    """
    encounter_items = list(encounters)
    compacted: list[dict[str, Any]] = []
    for encounter in encounter_items[:max_encounters]:
        compacted.append(
            {
                "encounter_id": str(encounter.get("encounter_id", "")).strip(),
                "heading": collapse_ws(str(encounter.get("heading", "")).strip()),
                "path": [
                    collapse_ws(str(item).strip())
                    for item in encounter.get("path", [])
                    if collapse_ws(str(item).strip())
                ][-3:] if isinstance(encounter.get("path", []), list) else [],
                "sections": [
                    collapse_ws(str(item).strip())
                    for item in encounter.get("sections", [])
                    if collapse_ws(str(item).strip())
                ][:3] if isinstance(encounter.get("sections", []), list) else [],
                "candidate_kinds": [
                    collapse_ws(str(item).strip())
                    for item in encounter.get("candidate_kinds", [])
                    if collapse_ws(str(item).strip())
                ] if isinstance(encounter.get("candidate_kinds", []), list) else [],
                "encounter_kind": collapse_ws(str(encounter.get("encounter_kind", "")).strip()),
                "equation_bearing": bool(encounter.get("equation_bearing", False)),
                "code_bearing": bool(encounter.get("code_bearing", False)),
                "parameterized": bool(encounter.get("parameterized", False)),
                "reusable": bool(encounter.get("reusable", False)),
                "extracted_form": markdown_prompt_fragment(
                    str(encounter.get("extracted_form", "")).strip(),
                    max_chars=140,
                ) if str(encounter.get("extracted_form", "")).strip() else "",
                "paragraph_fragments": [
                    markdown_prompt_fragment(str(item).strip(), max_chars=220)
                    for item in encounter.get("paragraphs", [])
                    if collapse_ws(str(item).strip())
                ][:1] if isinstance(encounter.get("paragraphs", []), list) else [],
                "bullet_fragments": [
                    markdown_prompt_fragment(str(item).strip(), max_chars=140)
                    for item in encounter.get("bullets", [])
                    if collapse_ws(str(item).strip())
                ][:3] if isinstance(encounter.get("bullets", []), list) else [],
                "equation_fragments": [
                    markdown_prompt_fragment(str(item).strip(), max_chars=120)
                    for item in encounter.get("equations", [])
                    if collapse_ws(str(item).strip())
                ][:2] if isinstance(encounter.get("equations", []), list) else [],
                "code_block_fragments": [
                    markdown_prompt_fragment(str(item).strip(), max_chars=280)
                    for item in encounter.get("code_blocks", [])
                    if collapse_ws(str(item).strip())
                ][:1] if isinstance(encounter.get("code_blocks", []), list) else [],
            }
        )
    return {
        "encounter_count": len(encounter_items),
        "encounters_omitted": max(0, len(encounter_items) - max_encounters),
        "encounters": compacted,
    }


def bounded_markdown_encounter_prompt_view(
    document: MarkdownDocumentIR,
    *,
    max_encounters: int = 8,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with building a view of bounded markdown encounter prompt.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `bounded_markdown_encounter_prompt_view(document=MarkdownDocumentIR(title='Physics Force Lesson'), max_encounters=3)`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `bounded_markdown_encounter_prompt_view`. Expected type: `MarkdownDocumentIR`.
        max_encounters: Value for `max_encounters` used by `bounded_markdown_encounter_prompt_view`. Expected type: `int`. Defaults to `8`.

    Returns:
        dict[str, Any]: Result produced by `bounded_markdown_encounter_prompt_view`.
    """
    return compact_markdown_encounter_records(
        markdown_learning_encounter_view(document),
        max_encounters=max_encounters,
    )


def markdown_clean_learning_text(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown clean learning text.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_clean_learning_text(text='Compute force from mass and acceleration.')`
        Output: 'F = m * a'

    Args:
        text: Value for `text` used by `markdown_clean_learning_text`. Expected type: `str`.

    Returns:
        str: Result produced by `markdown_clean_learning_text`.
    """
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    cleaned = cleaned.replace("$$", " ").replace("$", " ")
    cleaned = cleaned.replace("`", "")
    cleaned = cleaned.replace("**", "")
    cleaned = cleaned.replace("__", "")
    cleaned = re.sub(r"\\([A-Za-z]+)", r"\1", cleaned)
    cleaned = cleaned.replace("{", " ").replace("}", " ")
    return collapse_ws(cleaned)


def markdown_symbol_identifier(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like parsing equation symbols, chemistry notation, and contract bullets from markdown lessons, helps with converting one symbolic surface into a stable identifier that can be reused in contracts and executable expressions.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_symbol_identifier(text='[H^+]')`
        Output: 'H_plus'

    Args:
        text: Value for `text` used by `markdown_symbol_identifier`. Expected type: `str`.

    Returns:
        str: Result produced by `markdown_symbol_identifier`.
    """
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    while True:
        replaced = re.sub(r"\\(?:mathrm|text)\s*\{([^{}]+)\}", r"\1", normalized)
        if replaced == normalized:
            break
        normalized = replaced
    normalized = normalized.replace("$$", " ").replace("$", " ").replace("`", "")
    normalized = re.sub(r"\\([A-Za-z]+)", r"\1", normalized)
    normalized = normalized.strip()
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1].strip()
    normalized = normalized.replace("{", "").replace("}", "")
    normalized = normalized.replace("^+", "_plus")
    normalized = normalized.replace("^-", "_minus")
    normalized = normalized.replace("+", "_plus")
    normalized = normalized.replace("-", "_minus")
    normalized = normalized.replace("/", "_per_")
    normalized = normalized.replace("*", "_times_")
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def markdown_contract_field_candidates(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like reading declared inputs and outputs from markdown bullets, helps with preserving whole symbolic or phrase-level contract fields instead of breaking them into accidental word fragments.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_contract_field_candidates(text='product concentrations')`
        Output: ['product_concentrations']

    Args:
        text: Value for `text` used by `markdown_contract_field_candidates`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `markdown_contract_field_candidates`.
    """
    cleaned = str(text or "").strip()
    if not cleaned:
        return []
    candidates: list[str] = []
    for chunk in re.split(r"\s*(?:,|;|\band\b)\s*", cleaned):
        normalized = markdown_symbol_identifier(chunk)
        if normalized and is_contract_identifier_candidate(normalized):
            candidates.append(normalized)
    if candidates:
        return ordered_unique(candidates)
    fallback = markdown_symbol_identifier(cleaned)
    if fallback and is_contract_identifier_candidate(fallback):
        return [fallback]
    return []


def markdown_split_identifier_by_known_symbols(token: str, known_symbols: Sequence[str]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like decoding compact mathematical notation such as `nRT` against a declared contract, helps with splitting a fused identifier into the known semantic symbols it actually contains.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_split_identifier_by_known_symbols(token='nRT', known_symbols=['n', 'R', 'T', 'V'])`
        Output: ['n', 'R', 'T']

    Args:
        token: Value for `token` used by `markdown_split_identifier_by_known_symbols`. Expected type: `str`.
        known_symbols: Value for `known_symbols` used by `markdown_split_identifier_by_known_symbols`. Expected type: `Sequence[str]`.

    Returns:
        list[str]: Result produced by `markdown_split_identifier_by_known_symbols`.
    """
    raw_token = str(token or "").strip()
    symbols = ordered_unique(str(symbol).strip() for symbol in known_symbols if str(symbol).strip())
    if not raw_token or not symbols or raw_token in symbols:
        return [raw_token] if raw_token else []
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", raw_token):
        return [raw_token]
    ordered_symbols = sorted(symbols, key=len, reverse=True)

    def split_from(index: int) -> list[str] | None:
        if index >= len(raw_token):
            return []
        for symbol in ordered_symbols:
            if not raw_token.startswith(symbol, index):
                continue
            remainder = split_from(index + len(symbol))
            if remainder is not None:
                return [symbol, *remainder]
        return None

    split = split_from(0)
    if split and len(split) >= 2:
        return split
    return [raw_token]


def markdown_normalize_math_expression(
    text: str,
    *,
    known_symbols: Sequence[str] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like turning markdown equations into executable or structurally matchable forms, helps with normalizing TeX-style math surfaces into a stable expression text that preserves the intended inputs and outputs.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_normalize_math_expression(text='$$ P = \\\\frac{nRT}{V} $$', known_symbols=['P', 'n', 'R', 'T', 'V'])`
        Output: 'P = ((n * R * T) / (V))'

    Args:
        text: Value for `text` used by `markdown_normalize_math_expression`. Expected type: `str`.
        known_symbols: Value for `known_symbols` used by `markdown_normalize_math_expression`. Expected type: `Sequence[str] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `markdown_normalize_math_expression`.
    """
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    normalized = normalized.replace("$$", " ").replace("$", " ").replace("`", "")
    while True:
        replaced = re.sub(r"\\(?:mathrm|text)\s*\{([^{}]+)\}", r"\1", normalized)
        if replaced == normalized:
            break
        normalized = replaced
    while True:
        replaced = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"((\1) / (\2))", normalized)
        if replaced == normalized:
            break
        normalized = replaced
    normalized = re.sub(r"\\log_\s*\{?\s*10\s*\}?", "log10", normalized)
    normalized = re.sub(r"\\prod(?:_[A-Za-z0-9]+)?", "prod", normalized)
    normalized = re.sub(r"\\rightleftharpoons", " equilibrium ", normalized)
    normalized = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", normalized)
    normalized = re.sub(r"sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", normalized)
    normalized = re.sub(
        r"\[([^\[\]]+)\]",
        lambda match: markdown_symbol_identifier(match.group(1)),
        normalized,
    )
    normalized = re.sub(r"\\([A-Za-z]+)", r"\1", normalized)
    normalized = normalized.replace("{", "(").replace("}", ")")
    normalized = re.sub(r"([A-Za-z0-9_)\]])\s*\^\s*\(([^()]+)\)", r"\1**(\2)", normalized)
    normalized = re.sub(r"([A-Za-z0-9_\)\]])\s*\^\s*([A-Za-z0-9_+\-]+)", r"\1**\2", normalized)
    normalized = normalized.replace("^", "**")
    normalized = re.sub(r"\blog10([A-Za-z_][A-Za-z0-9_]*)\b", r"log10(\1)", normalized)
    while True:
        replaced = re.sub(r"sqrt\(([^()]+)\)", r"(\1) ** 0.5", normalized)
        if replaced == normalized:
            break
        normalized = replaced
    normalized = collapse_ws(normalized)
    tokens = re.findall(r"\*\*|[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|[^\s]", normalized)
    symbol_pool = ordered_unique(str(symbol).strip() for symbol in (known_symbols or []) if str(symbol).strip())
    rebuilt: list[str] = []
    previous = ""
    for token in tokens:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            split_tokens = markdown_split_identifier_by_known_symbols(token, symbol_pool)
        else:
            split_tokens = [token]
        for piece in split_tokens:
            if (
                rebuilt
                and (
                    (
                        re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?", previous)
                        and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*|\(", piece)
                        and previous.lower() not in MATH_IDENTIFIER_STOP_WORDS
                    )
                    or (previous == ")" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|\(", piece))
                )
            ):
                rebuilt.append("*")
            rebuilt.append(piece)
            previous = piece
    return collapse_ws(" ".join(rebuilt))


def is_generic_synthesis_field_name(value: str) -> bool:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with deciding whether generic synthesis field name.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `is_generic_synthesis_field_name(value='force')`
        Output: True

    Args:
        value: Value for `value` used by `is_generic_synthesis_field_name`. Expected type: `str`.

    Returns:
        bool: Result produced by `is_generic_synthesis_field_name`.
    """
    normalized = str(value or "").strip().lower()
    if not normalized:
        return True
    return normalized in GENERIC_SYNTHESIS_FIELD_NAMES


def is_generic_synthesis_question(value: str) -> bool:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with deciding whether generic synthesis question.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `is_generic_synthesis_question(value='force')`
        Output: True

    Args:
        value: Value for `value` used by `is_generic_synthesis_question`. Expected type: `str`.

    Returns:
        bool: Result produced by `is_generic_synthesis_question`.
    """
    normalized = collapse_ws(str(value or "").strip()).lower()
    if not normalized:
        return True
    generic_markers = (
        "document's derived output",
        "document s derived output",
        "named inputs",
        "derived output",
    )
    return any(marker in normalized for marker in generic_markers)


def markdown_symbolic_mapping_from_encounter(encounter: Mapping[str, Any]) -> tuple[str, list[str]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown symbolic mapping from encounter.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_symbolic_mapping_from_encounter(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        encounter: Value for `encounter` used by `markdown_symbolic_mapping_from_encounter`. Expected type: `Mapping[str, Any]`.

    Returns:
        tuple[str, list[str]]: Result produced by `markdown_symbolic_mapping_from_encounter`.
    """
    declared_output, declared_inputs = markdown_declared_contract_from_encounter(encounter)
    for output_field, input_fields, _expression in markdown_candidate_expression_mappings(encounter):
        if declared_output and output_field.lower() != declared_output.lower():
            continue
        if declared_inputs and set(map(str.lower, input_fields)) != set(map(str.lower, declared_inputs)):
            continue
        return output_field, input_fields
    for output_field, input_fields, _expression in markdown_candidate_expression_mappings(encounter):
        return output_field, input_fields
    return "", []


def markdown_direct_expression_mapping(encounter: Mapping[str, Any]) -> tuple[str, list[str], str]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown direct expression mapping.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_direct_expression_mapping(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        encounter: Value for `encounter` used by `markdown_direct_expression_mapping`. Expected type: `Mapping[str, Any]`.

    Returns:
        tuple[str, list[str], str]: Result produced by `markdown_direct_expression_mapping`.
    """
    declared_output, declared_inputs = markdown_declared_contract_from_encounter(encounter)
    best_match: tuple[str, list[str], str] = ("", [], "")
    best_score = -1
    for output_field, input_fields, expression in markdown_candidate_expression_mappings(encounter):
        score = 0
        if declared_output and output_field.lower() == declared_output.lower():
            score += 4
        if declared_inputs:
            current = set(map(str.lower, input_fields))
            expected = set(map(str.lower, declared_inputs))
            if current == expected:
                score += 4
            elif expected and current.issuperset(expected):
                score += 2
        if score > best_score:
            best_match = (output_field, input_fields, expression)
            best_score = score
        if declared_output and declared_inputs and score >= 8:
            return output_field, input_fields, expression
    if best_score >= 0:
        return best_match
    return "", [], ""


def markdown_candidate_expression_mappings(encounter: Mapping[str, Any]) -> list[tuple[str, list[str], str]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown candidate expression mappings.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_candidate_expression_mappings(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        encounter: Value for `encounter` used by `markdown_candidate_expression_mappings`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[tuple[str, list[str], str]]: Result produced by `markdown_candidate_expression_mappings`.
    """
    declared_output, declared_inputs = markdown_declared_contract_from_encounter(encounter)
    known_symbols = ordered_unique([declared_output, *declared_inputs])
    candidates: list[str] = []
    extracted_form = str(encounter.get("extracted_form", "")).strip()
    if extracted_form:
        candidates.append(extracted_form)
    equations = encounter.get("equations", [])
    if isinstance(equations, list):
        candidates.extend(str(item).strip() for item in equations if str(item).strip())

    mappings: list[tuple[str, list[str], str]] = []
    for candidate in candidates:
        raw = str(candidate).strip()
        if "=" not in raw:
            continue
        normalized = markdown_normalize_math_expression(raw, known_symbols=known_symbols)
        if "=" not in normalized:
            continue
        left, right = normalized.split("=", 1)
        output_field = markdown_simple_equation_lhs_symbol(left)
        if not output_field:
            continue
        rhs_segment = right.split("=", 1)[0].strip()
        if not rhs_segment:
            continue
        rhs_segment = collapse_ws(rhs_segment)
        input_fields = []
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", rhs_segment):
            lowered = token.lower()
            if token == output_field:
                continue
            if lowered in MATH_IDENTIFIER_STOP_WORDS:
                continue
            input_fields.append(token)
        input_fields = ordered_unique(input_fields)
        if declared_inputs and declared_output and output_field.lower() == declared_output.lower():
            extracted_keys = {field.casefold() for field in input_fields}
            declared_keys = {field.casefold() for field in declared_inputs}
            if extracted_keys != declared_keys:
                input_fields = list(declared_inputs)
        if input_fields and rhs_segment:
            mappings.append((output_field, input_fields, rhs_segment))
    return mappings


def markdown_simple_equation_lhs_symbol(lhs_text: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown simple equation lhs symbol.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_simple_equation_lhs_symbol(lhs_text='Compute force from mass and acceleration.')`
        Output: 'F = m * a'

    Args:
        lhs_text: Value for `lhs_text` used by `markdown_simple_equation_lhs_symbol`. Expected type: `str`.

    Returns:
        str: Result produced by `markdown_simple_equation_lhs_symbol`.
    """
    cleaned = markdown_symbol_identifier(markdown_normalize_math_expression(lhs_text))
    if not cleaned:
        return ""
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)", cleaned)
    return match.group(1) if match else ""


def markdown_declared_contract_from_encounter(encounter: Mapping[str, Any]) -> tuple[str, list[str]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown declared contract from encounter.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_declared_contract_from_encounter(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        encounter: Value for `encounter` used by `markdown_declared_contract_from_encounter`. Expected type: `Mapping[str, Any]`.

    Returns:
        tuple[str, list[str]]: Result produced by `markdown_declared_contract_from_encounter`.
    """
    inputs: list[str] = []
    output_field = ""
    bullets = encounter.get("bullets", [])
    if not isinstance(bullets, list):
        bullets = []
    for raw_item in bullets:
        item = markdown_clean_learning_text(str(raw_item).strip())
        lowered = item.lower()
        if lowered.startswith("inputs:") or lowered.startswith("input:"):
            fields = markdown_contract_field_candidates(item.split(":", 1)[1])
            inputs.extend(fields)
            continue
        if lowered.startswith("output:") or lowered.startswith("outputs:"):
            fields = markdown_contract_field_candidates(item.split(":", 1)[1])
            if fields:
                output_field = fields[0]
            continue
        if lowered.startswith("given "):
            fields = markdown_contract_field_candidates(item[6:])
            inputs.extend(fields)
            continue
        if lowered.startswith("return ") or lowered.startswith("returns "):
            fields = markdown_contract_field_candidates(item.split(" ", 1)[1])
            if fields:
                output_field = fields[0]
            continue
    return output_field, ordered_unique(inputs)


def markdown_encounter_aliases(encounter: Mapping[str, Any], *, limit: int = 8) -> list[str]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown encounter aliases.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_encounter_aliases(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, limit=3)`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        encounter: Value for `encounter` used by `markdown_encounter_aliases`. Expected type: `Mapping[str, Any]`.
        limit: Value for `limit` used by `markdown_encounter_aliases`. Expected type: `int`. Defaults to `8`.

    Returns:
        list[str]: Result produced by `markdown_encounter_aliases`.
    """
    aliases: list[str] = []
    heading = markdown_clean_learning_text(str(encounter.get("heading", "")).strip())
    if heading:
        aliases.append(heading)
    for key in ("bullets", "paragraphs", "equations"):
        values = encounter.get(key, [])
        if not isinstance(values, list):
            continue
        for raw in values:
            cleaned = markdown_clean_learning_text(str(raw).strip())
            if not cleaned:
                continue
            if len(cleaned) > 140:
                continue
            aliases.append(cleaned)
    return ordered_unique(aliases)[:limit]


def markdown_encounter_question(encounter: Mapping[str, Any], *, output_field: str, input_fields: Sequence[str]) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown encounter question.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_encounter_question(encounter={'title': 'Physics / Force / Force From Mass And Acceleration'}, output_field='force', input_fields=['mass', 'acceleration', 'force'])`
        Output: 'F = m * a'

    Args:
        encounter: Value for `encounter` used by `markdown_encounter_question`. Expected type: `Mapping[str, Any]`.
        output_field: Value for `output_field` used by `markdown_encounter_question`. Expected type: `str`.
        input_fields: Value for `input_fields` used by `markdown_encounter_question`. Expected type: `Sequence[str]`.

    Returns:
        str: Result produced by `markdown_encounter_question`.
    """
    preferred_prefixes = ("calculate", "find", "compute", "what", "how")
    for candidate in markdown_encounter_aliases(encounter, limit=10):
        lowered = candidate.lower()
        if lowered.startswith(preferred_prefixes):
            return candidate.rstrip(".") + ("?" if not candidate.rstrip().endswith("?") else "")
    if output_field and input_fields:
        joined_inputs = ", ".join(input_fields)
        return f"How do you calculate {output_field} from {joined_inputs}?"
    heading = markdown_clean_learning_text(str(encounter.get("heading", "")).strip())
    if heading:
        return f"What is {heading}?"
    return ""


def markdown_document_symbol_aliases(document: MarkdownDocumentIR, symbols: Sequence[str]) -> dict[str, list[str]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown document symbol aliases.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_document_symbol_aliases(document=MarkdownDocumentIR(title='Physics Force Lesson'), symbols=['m', 'a', 'F'])`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `markdown_document_symbol_aliases`. Expected type: `MarkdownDocumentIR`.
        symbols: Value for `symbols` used by `markdown_document_symbol_aliases`. Expected type: `Sequence[str]`.

    Returns:
        dict[str, list[str]]: Result produced by `markdown_document_symbol_aliases`.
    """
    normalized_symbols = [str(symbol).strip() for symbol in symbols if str(symbol).strip()]
    alias_map: dict[str, list[str]] = {symbol: [symbol] for symbol in normalized_symbols}
    if not normalized_symbols:
        return alias_map

    all_texts: list[str] = []
    for encounter in markdown_learning_encounter_view(document):
        for key in ("bullets", "paragraphs", "equations"):
            values = encounter.get(key, [])
            if isinstance(values, list):
                all_texts.extend(markdown_clean_learning_text(str(item)) for item in values if markdown_clean_learning_text(str(item)))

    for symbol in normalized_symbols:
        pattern = re.compile(rf"^\s*{re.escape(symbol)}\s*=\s*(.+)$", flags=re.IGNORECASE)
        for text in all_texts:
            match = pattern.match(text)
            if match is None:
                continue
            rhs = collapse_ws(match.group(1))
            if not rhs:
                continue
            alias_map[symbol].append(rhs)
            for part in re.split(r",|;|also called|also known as", rhs, flags=re.IGNORECASE):
                cleaned = collapse_ws(part)
                if cleaned:
                    alias_map[symbol].append(cleaned)

    vocabulary = ordered_unique(
        [
            word.lower()
            for text in all_texts
            for word in re.findall(r"[A-Za-z][A-Za-z-]+", text)
            if len(word) > 2
        ]
    )
    for symbol in normalized_symbols:
        if len(symbol) != 1:
            continue
        for word in vocabulary:
            if word[0].lower() == symbol.lower():
                alias_map[symbol].append(word)

    return {symbol: ordered_unique(values)[:8] for symbol, values in alias_map.items()}


def merge_markdown_encounter_details(
    document: MarkdownDocumentIR,
    classified_encounters: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with merging markdown encounter details.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `merge_markdown_encounter_details(document=MarkdownDocumentIR(title='Physics Force Lesson'), classified_encounters={'cluster-1': ['force formula', 'mass', 'acceleration']})`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `merge_markdown_encounter_details`. Expected type: `MarkdownDocumentIR`.
        classified_encounters: Value for `classified_encounters` used by `merge_markdown_encounter_details`. Expected type: `Sequence[Mapping[str, Any]]`.

    Returns:
        list[dict[str, Any]]: Result produced by `merge_markdown_encounter_details`.
    """
    raw_by_id = {
        str(encounter.get("encounter_id", "")).strip(): dict(encounter)
        for encounter in markdown_learning_encounter_view(document)
        if str(encounter.get("encounter_id", "")).strip()
    }
    merged: list[dict[str, Any]] = []
    if not classified_encounters:
        return list(raw_by_id.values())
    for encounter in classified_encounters:
        encounter_id = str(encounter.get("encounter_id", "")).strip()
        if not encounter_id or encounter_id not in raw_by_id:
            continue
        base = dict(raw_by_id[encounter_id])
        base.update(dict(encounter))
        merged.append(base)
    return merged or list(raw_by_id.values())


def markdown_cluster_answer(cluster: Mapping[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown cluster answer.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_cluster_answer(cluster={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: 'F = m * a'

    Args:
        cluster: Value for `cluster` used by `markdown_cluster_answer`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `markdown_cluster_answer`.
    """
    paragraphs = [str(item).strip() for item in cluster.get("paragraphs", []) if str(item).strip()]
    bullets = [str(item).strip() for item in cluster.get("bullets", []) if str(item).strip()]
    equations = [str(item).strip() for item in cluster.get("equations", []) if str(item).strip()]
    parts: list[str] = []
    parts.extend(paragraphs[:3])
    if equations:
        parts.append("Equation: " + "; ".join(equations[:3]))
    if bullets:
        parts.append("Key points: " + "; ".join(bullets[:5]))
    return collapse_ws(" ".join(parts))


def markdown_canonical_question(document_title: str, heading: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown canonical question.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_canonical_question(document_title='Physics / Force / Force From Mass And Acceleration', heading='force')`
        Output: 'F = m * a'

    Args:
        document_title: Value for `document_title` used by `markdown_canonical_question`. Expected type: `str`.
        heading: Value for `heading` used by `markdown_canonical_question`. Expected type: `str`.

    Returns:
        str: Result produced by `markdown_canonical_question`.
    """
    lowered_title = collapse_ws(document_title).lower()
    lowered_heading = collapse_ws(heading).lower()
    if "newton" in lowered_title and "first law" in lowered_heading:
        return "What is Newton's first law of motion?"
    if "newton" in lowered_title and "second law" in lowered_heading:
        return "What is Newton's second law of motion?"
    if "newton" in lowered_title and "third law" in lowered_heading:
        return "What is Newton's third law of motion?"
    if lowered_heading:
        return f"What is {collapse_ws(heading)}?"
    return f"What is {collapse_ws(document_title)}?"


def markdown_caller_facing_question(document_title: str, heading: str) -> str:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling markdown caller facing question.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `markdown_caller_facing_question(document_title='Physics / Force / Force From Mass And Acceleration', heading='force')`
        Output: 'F = m * a'

    Args:
        document_title: Value for `document_title` used by `markdown_caller_facing_question`. Expected type: `str`.
        heading: Value for `heading` used by `markdown_caller_facing_question`. Expected type: `str`.

    Returns:
        str: Result produced by `markdown_caller_facing_question`.
    """
    normalized_title = collapse_ws(document_title)
    normalized_heading = collapse_ws(heading)
    if not normalized_heading:
        return markdown_canonical_question(document_title, heading)
    if normalized_heading.lower() == "summary" and normalized_title:
        return f"What is the summary of {normalized_title}?"
    if ":" in normalized_heading and normalized_title:
        lead = collapse_ws(normalized_heading.split(":", 1)[0])
        if lead:
            article = "the " if re.match(r"^(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b", lead.lower()) else ""
            return f"What is {article}{lead.lower()} in {normalized_title}?"
    return markdown_canonical_question(document_title, heading)


def looks_like_placeholder_python_script(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like markdown ingestion, IR clustering, and learning-ready fragment extraction, helps with handling looks like placeholder python script.

    Reference to Theory:
        Transforms markdown into IR segments that the controller can decompose and learn from under the title-depth and decomposition law.

    Example Input Output:
        Input: `looks_like_placeholder_python_script(text='Compute force from mass and acceleration.')`
        Output: True

    Args:
        text: Value for `text` used by `looks_like_placeholder_python_script`. Expected type: `str`.

    Returns:
        bool: Result produced by `looks_like_placeholder_python_script`.
    """
    candidate = str(text or "").strip()
    if not candidate:
        return True
    lowered = candidate.lower()
    if candidate.count("\n") < 2 and "python script" in lowered:
        return True
    if "<python_script>" in lowered or "placeholder" in lowered:
        return True
    if lowered.startswith("# python script with inline metadata"):
        return True
    return False
