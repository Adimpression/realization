"""Derived-skill YAML materialization for subject learning contexts."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws, ordered_unique
from realized_exchange.compiler import compile_skill_document
from realized_exchange.skill_export import export_skill_text
from workstation.subject.core.learning_context import (
    learning_context_projected_skill_ids,
)
from workstation.subject.core.learning_context_paths import learning_context_paths
from workstation.subject.service.learning_context_skills import (
    projected_skill_document_from_learning_unit,
)


def projected_skill_filename(skill_id: str) -> str:
    """Return the stable YAML filename for one projected skill identity."""
    normalized = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        collapse_ws(skill_id),
    ).strip("-._")
    return f"{normalized or 'skill'}.yaml"


def materialize_learning_context_skill_projections(
    root_path: Path,
    context: Any,
) -> tuple[dict[str, Any], ...]:
    """Compile and write every admitted derived skill for a learning context."""
    paths = learning_context_paths(root_path, context.subject_id)
    paths["derived_skills"].mkdir(parents=True, exist_ok=True)
    for existing in paths["derived_skills"].glob("*.yaml"):
        existing.unlink()
    reports: list[dict[str, Any]] = []
    for unit in sorted(
        context.units,
        key=lambda item: (item.canonical_title, item.unit_id),
    ):
        for skill_id in ordered_unique(unit.linked_skill_ids):
            payload = projected_skill_document_from_learning_unit(
                context=context,
                unit=unit,
                skill_id=skill_id,
            )
            if payload is None:
                continue
            compiled = compile_skill_document(
                payload,
                source_kind="learning_context_projection",
            )
            output_path = paths["derived_skills"] / projected_skill_filename(
                skill_id
            )
            output_path.write_text(
                export_skill_text(compiled.artifact),
                encoding="utf-8",
            )
            reports.append(
                {
                    "skill_id": skill_id,
                    "unit_id": unit.unit_id,
                    "path": str(output_path),
                    "title": str(payload.get("title", "")),
                    "kind": str(payload.get("kind", "")),
                    "compiler_summary": compiled.summary(),
                }
            )
    return tuple(reports)


__all__ = [
    "learning_context_projected_skill_ids",
    "materialize_learning_context_skill_projections",
    "projected_skill_document_from_learning_unit",
    "projected_skill_filename",
]
