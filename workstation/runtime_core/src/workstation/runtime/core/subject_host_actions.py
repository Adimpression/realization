"""Runtime adapter for subject workflow outbound operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from realized_core_semantics.proposals import ProposalType, SupplementMode
from workstation.foundation.host.controller_runtime import controller_runtime_provider
from workstation.foundation.host.skill_exchange import skill_exchange_provider
from workstation.subject.service.learning_capture import (
    capture_workstation_assistant_markdown_for_research,
    preview_workstation_assistant_markdown_for_research,
)
from workstation.foundation.projections import WorkstationActionResultView
from workstation.runtime.core.session import load_workstation_session
from workstation.runtime.core.workstation_core import (
    workstation_import_staged_source_action,
    workstation_learn_url_action,
    workstation_refresh_staged_source_action,
    workstation_stage_markdown_source_action,
    workstation_sync_source_collection_action,
)
from workstation.subject.core.host_actions import (
    SubjectHostActionResult,
    SubjectItemizationProposal,
)


def _subject_result(result: WorkstationActionResultView) -> SubjectHostActionResult:
    payload = getattr(result, "payload", {})
    return SubjectHostActionResult(
        status=str(getattr(result, "status", "error")),
        message=str(getattr(result, "message", "")),
        details=tuple(str(item) for item in getattr(result, "details", ())),
        payload=dict(payload) if isinstance(payload, Mapping) else {},
    )


@dataclass(frozen=True)
class RuntimeSubjectWorkflowHostActions:
    """Realize subject effects through the existing workstation runtime."""

    def allows_direct_llm_decomposition(self, *, root_path: Path) -> bool:
        try:
            return bool(load_workstation_session(root_path).allow_direct_llm_decomposition)
        except Exception:
            return False

    def request_itemization_proposal(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        target_scope: str,
        instructions: str,
        fallback_payload: dict[str, object],
        schema_hint: dict[str, object],
    ) -> SubjectItemizationProposal:
        _state, controller = controller_runtime_provider().bootstrap_controller(
            semantic_unit=semantic_unit,
            llm_policy=llm_policy,
        )
        proposal = controller.request_proposal(
            proposal_type=ProposalType.NOT_DECOMPOSITION,
            node=None,
            target_scope=target_scope,
            instructions=instructions,
            fallback_payload=fallback_payload,
            mode=SupplementMode.DEEP,
            schema_hint=schema_hint,
        )
        return SubjectItemizationProposal(
            proposal_id=str(proposal.id),
            source=str(proposal.source),
            payload=dict(proposal.payload or {}),
        )

    def bootstrap_decision_support_controller(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
        subject_scope: Any | None,
        subject_scope_root_path: Path | None,
    ) -> tuple[Any, Any]:
        return controller_runtime_provider().bootstrap_controller(
            semantic_unit=semantic_unit,
            llm_policy=llm_policy,
            subject_scope=subject_scope,
            subject_scope_root_path=subject_scope_root_path,
        )

    def stage_markdown_source(
        self,
        *,
        root_path: Path,
        markdown_path: Path,
        subject_id: str,
        subject_title: str,
    ) -> SubjectHostActionResult:
        return _subject_result(
            workstation_stage_markdown_source_action(
                root_path=root_path,
                markdown_path=markdown_path,
                subject_id=subject_id,
                subject_title=subject_title,
            )
        )

    def learn_url(
        self,
        *,
        root_path: Path,
        source_url: str,
        subject_id: str,
        subject_title: str,
    ) -> SubjectHostActionResult:
        return _subject_result(
            workstation_learn_url_action(
                root_path=root_path,
                source_url=source_url,
                subject_id=subject_id,
                subject_title=subject_title,
            )
        )

    def import_staged_source(
        self,
        *,
        root_path: Path,
        subject_id: str,
        staged_source_id: str,
    ) -> SubjectHostActionResult:
        return _subject_result(
            workstation_import_staged_source_action(
                root_path=root_path,
                subject_id=subject_id,
                staged_source_id=staged_source_id,
            )
        )

    def refresh_staged_source(
        self,
        *,
        root_path: Path,
        subject_id: str,
        staged_source_id: str,
    ) -> SubjectHostActionResult:
        return _subject_result(
            workstation_refresh_staged_source_action(
                root_path=root_path,
                subject_id=subject_id,
                staged_source_id=staged_source_id,
            )
        )

    def sync_source_collection(
        self,
        *,
        root_path: Path,
        subject_id: str,
        collection_id: str,
    ) -> SubjectHostActionResult:
        return _subject_result(
            workstation_sync_source_collection_action(
                root_path=root_path,
                subject_id=subject_id,
                collection_id=collection_id,
            )
        )

    def preview_assistant_markdown(
        self,
        *,
        root_path: Path,
        markdown_text: str,
        command_text: str,
        subject_title_override: str,
    ) -> dict[str, object]:
        return dict(
            preview_workstation_assistant_markdown_for_research(
                root_path=root_path,
                markdown_text=markdown_text,
                command_text=command_text,
                subject_title_override=subject_title_override,
            )
        )

    def capture_assistant_markdown(
        self,
        *,
        root_path: Path,
        markdown_text: str,
        command_text: str,
        subject_title_override: str,
    ) -> dict[str, object]:
        return dict(
            capture_workstation_assistant_markdown_for_research(
                root_path=root_path,
                markdown_text=markdown_text,
                command_text=command_text,
                subject_title_override=subject_title_override,
                skill_materializer=skill_exchange_provider().materialize_learning_context_skills,
            )
        )


__all__ = ["RuntimeSubjectWorkflowHostActions"]
