# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from typing import Iterable

from realized_core_semantics.boundary import infer_not_boundary_shape_from_semantic_text

from workstation.foundation.models import TaskBoundaryContract


_ASSIGNMENT_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(['\"])(.*?)\2")
_URL_PATTERN = re.compile(r"https?://[^\s)>\"]+")

_OUTPUT_HINTS = (
    ("summarize", "summary"),
    ("explain", "explanation"),
    ("describe", "description"),
    ("list", "list"),
    ("show", "result"),
    ("return", "result"),
)

_SIDE_EFFECT_HINTS = (
    ("open browser", "open browser"),
    ("browser", "open browser"),
    ("download", "download file"),
    ("write", "write file"),
    ("save", "write file"),
    ("edit", "write file"),
    ("run", "run command"),
    ("execute", "run command"),
    ("launch", "launch application"),
    ("open app", "launch application"),
)


def _unique(items: Iterable[str]) -> tuple[str, ...]:
    """
    High Level Purpose:
        In circumstances like task-contract normalization from freeform prompts, helps with deduplicating ordered textual boundary items without losing their first-seen order.

    Reference to Theory:
        Supports BSSC boundary completeness by keeping normalized boundary items stable and non-redundant.

    Example Input Output:
        Input: `_unique(items=['summary', 'summary', 'result'])`
        Output: ('summary', 'result')

    Args:
        items: Value for `items` used by `_unique`. Expected type: `Iterable[str]`.

    Returns:
        tuple[str, ...]: Result produced by `_unique`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def normalize_prompt_to_task_boundary_contract(prompt: str) -> TaskBoundaryContract:
    """
    High Level Purpose:
        In circumstances like workstation prompt ingestion, helps with turning freeform user text into a boundary-complete task contract suitable for capability planning and receipts.

    Reference to Theory:
        Reuses BSSC boundary-shape completeness theory by keeping the user prompt natural while normalizing its operational body into explicit reads, writes, outputs, side effects, and missing requirements.

    Example Input Output:
        Input: `normalize_prompt_to_task_boundary_contract(prompt='Open the browser, download the quarterly report, and summarize it.')`
        Output: TaskBoundaryContract(semantic_unit='Open the browser, download the quarterly report, and summarize it.', boundary_shape=('b*', 'c*', 'd*'), input_values={}, read_references=('browser target', 'quarterly report source'), write_targets=('download destination',), output_values=('summary',), side_effects=('open browser', 'download file'), completion_conditions=('quarterly report is available in the workstation', 'summary is returned to the user'), assumptions=(), missing_requirements=('report URL or search target',))

    Args:
        prompt: Value for `prompt` used by `normalize_prompt_to_task_boundary_contract`. Expected type: `str`.

    Returns:
        TaskBoundaryContract: Result produced by `normalize_prompt_to_task_boundary_contract`.
    """
    semantic_unit = str(prompt or "").strip()
    lowered = semantic_unit.casefold()
    boundary_shape = tuple(term.value for term in infer_not_boundary_shape_from_semantic_text(semantic_unit))
    input_values = {
        key: value
        for key, _, value in _ASSIGNMENT_PATTERN.findall(semantic_unit)
    }
    read_references: list[str] = []
    write_targets: list[str] = []
    output_values: list[str] = []
    side_effects: list[str] = []
    completion_conditions: list[str] = []
    assumptions: list[str] = []
    missing_requirements: list[str] = []

    urls = _URL_PATTERN.findall(semantic_unit)
    for url in urls:
        read_references.append(url)

    if "browser" in lowered:
        read_references.append("browser target")
    if "download" in lowered:
        read_references.append("download source")
        write_targets.append("download destination")
        completion_conditions.append("downloaded file is available in the workstation")
        if not urls and "url=" not in lowered and "http://" not in lowered and "https://" not in lowered:
            missing_requirements.append("report URL or search target")
    if "file" in lowered or "path" in lowered:
        read_references.append("file or path reference")
    if "workspace" in lowered or "repo" in lowered or "repository" in lowered:
        read_references.append("workspace attachment")

    for cue, normalized_output in _OUTPUT_HINTS:
        if cue in lowered:
            output_values.append(normalized_output)
    if not output_values:
        output_values.append("result")

    for cue, normalized_effect in _SIDE_EFFECT_HINTS:
        if cue in lowered:
            side_effects.append(normalized_effect)

    if "summarize" in lowered:
        completion_conditions.append("summary is returned to the user")
    elif "explain" in lowered or "describe" in lowered:
        completion_conditions.append("explanation is returned to the user")
    else:
        completion_conditions.append("requested result is returned to the user")

    if not read_references and any(term.startswith("b") for term in boundary_shape):
        read_references.append("external reference")
    if not write_targets and any(term.startswith("c") for term in boundary_shape):
        write_targets.append("external write target")

    return TaskBoundaryContract(
        semantic_unit=semantic_unit,
        boundary_shape=boundary_shape,
        input_values=input_values,
        read_references=_unique(read_references),
        write_targets=_unique(write_targets),
        output_values=_unique(output_values),
        side_effects=_unique(side_effects),
        completion_conditions=_unique(completion_conditions),
        assumptions=_unique(assumptions),
        missing_requirements=_unique(missing_requirements),
    )
