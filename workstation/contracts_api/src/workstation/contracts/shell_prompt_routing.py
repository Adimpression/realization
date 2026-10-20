"""Deterministic shell utility routing shared below runtime and skill layers."""

from __future__ import annotations

import re
from typing import Any


def _collapse_ws(text: str) -> str:
    without_controls = re.sub(r"[\x00-\x1f\x7f]", " ", str(text))
    return re.sub(r"\s+", " ", without_controls).strip()


def match_workstation_shell_utility_prompt(prompt: str) -> dict[str, Any] | None:
    normalized = _collapse_ws(str(prompt))
    if not normalized:
        return None
    trimmed = normalized.rstrip(" \t\r\n.,;:!?")
    lowered = trimmed.casefold()

    import_prefix = "import the skill file at "
    import_suffixes = (
        " into this workstation",
        " into the workstation",
    )
    if lowered.startswith(import_prefix):
        for suffix in import_suffixes:
            if lowered.endswith(suffix):
                path_text = trimmed[len(import_prefix) : len(trimmed) - len(suffix)].strip().rstrip(".,;:!?")
                if path_text:
                    return {
                        "command_text": f"/import-skill {path_text}",
                        "capability": "ws.skill.import",
                    }

    export_prefix = "export the skill titled "
    export_marker = " to "
    if lowered.startswith(export_prefix) and export_marker in lowered:
        marker_index = lowered.rfind(export_marker)
        title_text = trimmed[len(export_prefix) : marker_index].strip().strip("\"' ")
        destination_text = trimmed[marker_index + len(export_marker) :].strip().rstrip(".,;:!?")
        if title_text and destination_text:
            return {
                "command_text": f'/export-skill "{title_text}" {destination_text}',
                "capability": "ws.skill.export",
            }

    return None


match_workstation_shell_utility_prompt.__module__ = "workstation.shell.core.shell_prompt_routing"

__all__ = ["match_workstation_shell_utility_prompt"]
