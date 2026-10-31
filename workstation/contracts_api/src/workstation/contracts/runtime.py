"""Controller-runtime ports supplied by the application composition root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable
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
        subject_scope: Any | None = None,
        subject_scope_root_path: Path | None = None,
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
        llm_policy: str,
        vector_mode: str | None,
    ) -> dict[str, Any]: ...


@runtime_checkable
class GovernedTurnRuntimeProvider(Protocol):
    """Optional controller-provider extension for explicit governed turns."""

    def perform_governed_turn(
        self,
        request: GovernedTurnRequest,
    ) -> GovernedTurnResult: ...


@runtime_checkable
class HostAwareControllerRuntimeProvider(Protocol):
    """Optional extension for host-context injection at controller bootstrap."""

    def bootstrap_controller_with_host_interaction(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        host_interaction_context: Any,
    ) -> tuple[Any, Any]: ...


@runtime_checkable
class ArtifactRepository(Protocol):
    """Persistence behavior required by workstation skill operations."""

    def describe(self) -> dict[str, Any]: ...

    def persist(self, state: Any) -> dict[str, Any]: ...

    def persist_artifact(
        self,
        artifact: Any,
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]: ...

    def persist_artifacts(
        self,
        artifacts: Any,
        *,
        run_id: str = "artifact_import",
    ) -> dict[str, Any]: ...

    def load_all_artifacts(self) -> list[Any]: ...

    def load_relevant_artifacts(
        self,
        query_text: str,
        *,
        limit: int = 8,
    ) -> list[Any]: ...

    def load_recent_artifacts(self, *, limit: int = 512) -> list[Any]: ...


@runtime_checkable
class ArtifactRepositoryProvider(Protocol):
    """Application-supplied constructor for an explicitly addressed store."""

    def open_artifact_repository(
        self,
        *,
        sqlite_path: Path,
        vector_mode: str | None = None,
    ) -> ArtifactRepository: ...


@runtime_checkable
class SkillExchangeProvider(Protocol):
    """Representation translation supplied by the entry/exchange layer."""

    def artifact_from_skill_document(self, document: Any) -> Any: ...

    def load_import_payload_documents(
        self,
        source_file: Path,
    ) -> list[dict[str, Any]]: ...

    def export_skill_bundle_text(self, artifacts: Iterable[Any]) -> str: ...

    def normalized_skill_bundle_filename_for_source(self, path: Path) -> str: ...

    def batch_skill_export_filename(self, artifact: Any) -> str: ...

    def materialize_learning_context_skills(
        self,
        root_path: Path,
        context: Any,
    ) -> tuple[dict[str, Any], ...]: ...


__all__ = [
    "ArtifactRepository",
    "ArtifactRepositoryProvider",
    "ControllerRuntimeProvider",
    "GovernedTurnRuntimeProvider",
    "HostAwareControllerRuntimeProvider",
    "SkillExchangeProvider",
    "GovernedTurnLlmPolicy",
    "GovernedTurnRequest",
    "GovernedTurnResult",
    "GovernedTurnTreatment",
]
