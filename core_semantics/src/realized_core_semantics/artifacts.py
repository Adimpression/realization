from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ArtifactContentView(Protocol):
    """Read-only artifact surface for consumers that inspect only content."""

    @property
    def content(self) -> Mapping[str, Any]: ...


@runtime_checkable
class TitledArtifactContentView(ArtifactContentView, Protocol):
    """Read-only artifact surface for consumers that also display a title."""

    @property
    def title(self) -> str: ...


__all__ = ["ArtifactContentView", "TitledArtifactContentView"]
