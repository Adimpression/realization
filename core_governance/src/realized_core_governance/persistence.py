"""Dependency-inverted persistence port for governed artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, TypeVar, runtime_checkable


ArtifactT = TypeVar("ArtifactT", contravariant=True)


@runtime_checkable
class GovernanceArtifactWriter(Protocol[ArtifactT]):
    """Port for persisting one already-prepared governed artifact batch."""

    def persist_artifacts(
        self,
        artifacts: Iterable[ArtifactT],
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]: ...


def persist_governed_artifacts(
    writer: GovernanceArtifactWriter[ArtifactT],
    artifacts: Iterable[ArtifactT],
    *,
    run_id: str = "artifact_import",
) -> dict[str, Any]:
    """Forward an already-prepared batch to the injected persistence writer."""
    return writer.persist_artifacts(artifacts, run_id=run_id)


__all__ = ["GovernanceArtifactWriter", "persist_governed_artifacts"]
