"""Controller-runtime ports supplied by the application composition root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable


type GovernedTurnTreatment = Literal[
    "independent",
    "human_contribution",
    "follow_up",
    "correction",
]
type GovernedTurnLlmPolicy = Literal["off", "auto", "required"]


@dataclass(frozen=True, slots=True)
class GovernedTurnRequest:
    """One explicit conversation-host request to the governed controller."""

    session_id: str
    turn_id: str
    user_message_id: str
    prompt: str
    treatment: GovernedTurnTreatment
    checkpoint_path: Path
    sqlite_path: Path
    parent_run_id: str = ""
    parent_checkpoint_path: Path | None = None
    llm_policy: GovernedTurnLlmPolicy = "auto"
    max_steps: int = 256


@dataclass(frozen=True, slots=True)
class GovernedTurnResult:
    """Stable governed result projection returned to a conversation host."""

    assistant_text: str
    run_id: str
    parent_run_id: str
    run_outcome: str
    root_status: str
    checkpoint_path: Path
    sqlite_path: Path
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "assistant_text": self.assistant_text,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "run_outcome": self.run_outcome,
            "root_status": self.root_status,
            "checkpoint_path": str(self.checkpoint_path),
            "sqlite_path": str(self.sqlite_path),
            "summary": dict(self.summary),
        }


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


@runtime_checkable
class GovernedTurnRuntimeProvider(Protocol):
    """Optional controller-provider extension for explicit governed turns."""

    def perform_governed_turn(
        self,
        request: GovernedTurnRequest,
    ) -> GovernedTurnResult: ...


__all__ = [
    "ControllerRuntimeProvider",
    "GovernedTurnRuntimeProvider",
    "GovernedTurnLlmPolicy",
    "GovernedTurnRequest",
    "GovernedTurnResult",
    "GovernedTurnTreatment",
]
