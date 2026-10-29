"""Outbound runtime operations required by the subject workflow domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SubjectHostActionResult:
    """Runtime-neutral result returned to subject workflow orchestration."""

    status: str
    message: str = ""
    details: tuple[str, ...] = ()
    payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SubjectItemizationProposal:
    """Controller-neutral proposal returned to itemization semantics."""

    proposal_id: str
    source: str
    payload: dict[str, object] = field(default_factory=dict)


class SubjectWorkflowPolicyPort(Protocol):
    """Read runtime policy needed to select a subject-domain path."""

    def allows_direct_llm_decomposition(self, *, root_path: Path) -> bool: ...


class SubjectWorkflowItemizationPort(Protocol):
    """Request optional advisory decomposition without exposing a controller."""

    def request_itemization_proposal(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        target_scope: str,
        instructions: str,
        fallback_payload: dict[str, object],
        schema_hint: dict[str, object],
    ) -> SubjectItemizationProposal: ...


class SubjectWorkflowSourcePort(Protocol):
    """Perform source-ingress effects selected by the subject workflow."""

    def stage_markdown_source(
        self,
        *,
        root_path: Path,
        markdown_path: Path,
        subject_id: str,
        subject_title: str,
    ) -> SubjectHostActionResult: ...

    def learn_url(
        self,
        *,
        root_path: Path,
        source_url: str,
        subject_id: str,
        subject_title: str,
    ) -> SubjectHostActionResult: ...

    def import_staged_source(
        self,
        *,
        root_path: Path,
        subject_id: str,
        staged_source_id: str,
    ) -> SubjectHostActionResult: ...

    def refresh_staged_source(
        self,
        *,
        root_path: Path,
        subject_id: str,
        staged_source_id: str,
    ) -> SubjectHostActionResult: ...

    def sync_source_collection(
        self,
        *,
        root_path: Path,
        subject_id: str,
        collection_id: str,
    ) -> SubjectHostActionResult: ...


class SubjectWorkflowCapturePort(Protocol):
    """Preview and persist explicitly confirmed assistant-source capture."""

    def preview_assistant_markdown(
        self,
        *,
        root_path: Path,
        markdown_text: str,
        command_text: str,
        subject_title_override: str,
    ) -> dict[str, object]: ...


class SubjectWorkflowDecisionSupportPort(Protocol):
    """Realize the controller bootstrap required by live decision support."""

    def bootstrap_decision_support_controller(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        subject_scope: Any | None,
        subject_scope_root_path: Path | None,
    ) -> tuple[Any, Any]: ...

    def capture_assistant_markdown(
        self,
        *,
        root_path: Path,
        markdown_text: str,
        command_text: str,
        subject_title_override: str,
    ) -> dict[str, object]: ...


class SubjectWorkflowHostActions(
    SubjectWorkflowPolicyPort,
    SubjectWorkflowItemizationPort,
    SubjectWorkflowSourcePort,
    SubjectWorkflowCapturePort,
    SubjectWorkflowDecisionSupportPort,
    Protocol,
):
    """Complete outbound port consumed by subject workflow orchestration."""


class SubjectWorkflowHostActionUnavailable(RuntimeError):
    """Raised when an uncomposed service attempts a host-only operation."""


@dataclass(frozen=True)
class UnavailableSubjectWorkflowHostActions:
    """Fail-closed default for read-only or incompletely composed services."""

    @staticmethod
    def _result(action: str) -> SubjectHostActionResult:
        return SubjectHostActionResult(
            status="unavailable",
            message=f"Subject workflow host action is unavailable: {action}.",
        )

    def allows_direct_llm_decomposition(self, *, root_path: Path) -> bool:
        del root_path
        return False

    def request_itemization_proposal(self, **kwargs: object) -> SubjectItemizationProposal:
        del kwargs
        raise SubjectWorkflowHostActionUnavailable(
            "Subject workflow host action is unavailable: request_itemization_proposal."
        )

    def stage_markdown_source(self, **kwargs: object) -> SubjectHostActionResult:
        del kwargs
        return self._result("stage_markdown_source")

    def learn_url(self, **kwargs: object) -> SubjectHostActionResult:
        del kwargs
        return self._result("learn_url")

    def import_staged_source(self, **kwargs: object) -> SubjectHostActionResult:
        del kwargs
        return self._result("import_staged_source")

    def refresh_staged_source(self, **kwargs: object) -> SubjectHostActionResult:
        del kwargs
        return self._result("refresh_staged_source")

    def sync_source_collection(self, **kwargs: object) -> SubjectHostActionResult:
        del kwargs
        return self._result("sync_source_collection")

    def preview_assistant_markdown(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        raise SubjectWorkflowHostActionUnavailable(
            "Subject workflow host action is unavailable: preview_assistant_markdown."
        )

    def capture_assistant_markdown(self, **kwargs: object) -> dict[str, object]:
        del kwargs
        raise SubjectWorkflowHostActionUnavailable(
            "Subject workflow host action is unavailable: capture_assistant_markdown."
        )

    def bootstrap_decision_support_controller(
        self,
        **kwargs: object,
    ) -> tuple[Any, Any]:
        del kwargs
        raise SubjectWorkflowHostActionUnavailable(
            "Subject workflow host action is unavailable: bootstrap_decision_support_controller."
        )


__all__ = [
    "SubjectHostActionResult",
    "SubjectItemizationProposal",
    "SubjectWorkflowCapturePort",
    "SubjectWorkflowDecisionSupportPort",
    "SubjectWorkflowHostActionUnavailable",
    "SubjectWorkflowHostActions",
    "SubjectWorkflowItemizationPort",
    "SubjectWorkflowPolicyPort",
    "SubjectWorkflowSourcePort",
    "UnavailableSubjectWorkflowHostActions",
]
