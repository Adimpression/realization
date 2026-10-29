"""Public persistence port and plain-SQLite adapter factory for the engine."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from realized_core_semantics.applied_model import Artifact

from realized_core_engine.store import (
    ArtifactStore,
    SQLiteVectorArtifactStore,
)


@runtime_checkable
class ArtifactRepository(Protocol):
    """Persistence behavior consumed by controllers and outer compositions."""

    def describe(self) -> dict[str, Any]: ...

    def persist(self, state: Any) -> dict[str, Any]: ...

    def persist_artifact(
        self,
        artifact: Artifact,
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]: ...

    def persist_artifacts(
        self,
        artifacts: Iterable[Artifact],
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]: ...

    def load_artifact_by_id(self, artifact_id: str) -> Artifact | None: ...

    def load_all_artifacts(self) -> list[Artifact]: ...

    def load_relevant_artifacts(
        self,
        semantic_unit: str,
        *,
        limit: int = 8,
    ) -> list[Artifact]: ...

    def load_recent_artifacts(self, *, limit: int = 12) -> list[Artifact]: ...


def open_sqlite_artifact_repository(
    sqlite_path: Path | None = None,
    *,
    vector_mode: str | None = None,
    fallback_repository: ArtifactStore | None = None,
) -> ArtifactRepository:
    """Open the engine's schema-compatible SQLite artifact repository."""

    repository = SQLiteVectorArtifactStore(fallback_store=fallback_repository)
    if sqlite_path is not None:
        repository.sqlite_path = Path(sqlite_path).expanduser().resolve()
    if vector_mode is not None:
        repository.vector_mode_override = str(vector_mode).strip().lower()
    return repository


def build_artifact_store() -> ArtifactRepository:
    """Build the default repository selected by engine configuration."""

    return open_sqlite_artifact_repository(fallback_repository=ArtifactStore())


__all__ = [
    "ArtifactRepository",
    "build_artifact_store",
    "open_sqlite_artifact_repository",
]
