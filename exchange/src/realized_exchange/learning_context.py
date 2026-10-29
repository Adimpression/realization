"""Compatibility-complete outer persistence adapter for learning contexts."""

from __future__ import annotations

from pathlib import Path

from workstation.subject.core import learning_context as _canonical
from workstation.subject.service.learning_context_persistence import (
    persist_learning_context as _persist_learning_context,
)

from realized_exchange.learning_context_skills import (
    materialize_learning_context_skill_projections,
)


for _name in _canonical.__all__:
    globals()[_name] = getattr(_canonical, _name)


def persist_learning_context(
    root_path: Path,
    context: _canonical.LearningContext,
) -> Path:
    """Persist canonical state and all historical exchange projections."""
    return _persist_learning_context(
        root_path,
        context,
        skill_materializer=materialize_learning_context_skill_projections,
    )


__all__ = list(_canonical.__all__)
