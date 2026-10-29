"""Application coordination for authoritative learning-context persistence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from workstation.subject.core.learning_context import (
    LearningContext,
    learning_context_paths,
    learning_context_projected_skill_ids,
    load_learning_context,
)
from workstation.subject.core.learning_context import (
    persist_learning_context as persist_authoritative_learning_context,
)
from workstation.subject.core.learning_context_projection import (
    render_learning_context_subject_markdown,
    render_learning_context_subject_typ,
)


LearningContextSkillMaterializer = Callable[
    [Path, LearningContext],
    tuple[dict[str, Any], ...],
]


def persist_learning_context(
    root_path: Path,
    context: LearningContext,
    *,
    skill_materializer: LearningContextSkillMaterializer | None = None,
) -> Path:
    """Persist authoritative state, then regenerate deterministic projections."""
    projected_skill_ids = learning_context_projected_skill_ids(context)
    if projected_skill_ids and skill_materializer is None:
        raise RuntimeError(
            "Learning-context skill projection requires an entry-composed "
            "skill materializer."
        )
    context_path = persist_authoritative_learning_context(root_path, context)
    normalized = load_learning_context(root_path, context.subject_id)
    paths = learning_context_paths(root_path, normalized.subject_id)
    paths["subject_typ"].write_text(
        render_learning_context_subject_typ(normalized),
        encoding="utf-8",
    )
    paths["subject_md"].write_text(
        render_learning_context_subject_markdown(normalized),
        encoding="utf-8",
    )
    if skill_materializer is not None:
        skill_materializer(Path(root_path), normalized)
    return context_path


__all__ = [
    "LearningContextSkillMaterializer",
    "persist_learning_context",
]
