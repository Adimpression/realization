"""Controller-runtime ports supplied by the application composition root."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ControllerRuntimeProvider(Protocol):
    """Behavior the workstation may request from the outer controller runtime."""

    def bootstrap_controller(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
    ) -> tuple[Any, Any]: ...

    def learn_markdown_bundle(
        self,
        *,
        root_path: Path,
        markdown_path: Path,
        source_label: str,
        bundle_output_path: Path,
        max_artifacts: int,
        source_bundle_override: dict[str, Any] | None,
    ) -> dict[str, Any]: ...


__all__ = ["ControllerRuntimeProvider"]
