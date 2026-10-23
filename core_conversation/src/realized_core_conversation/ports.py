"""Dependency-facing ports for governed conversation orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from realized_core_engine import (
    InspectionRequest,
    InspectionResult,
    InterruptionRequest,
    InterruptionResult,
    ResumptionRequest,
    ResumptionResult,
    StartRequest,
)

from realized_core_conversation.schemas import (
    ConversationActivityRecord,
    ConversationRecordKind,
    ContributionRecord,
    NormalizedRequestRecord,
    StructuredResultRecord,
)


@runtime_checkable
class SemanticResumptionPort(Protocol):
    """Narrow semantic engine surface consumed by conversation orchestration."""

    def start(
        self,
        request: StartRequest,
        *,
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> ResumptionResult: ...

    def resume(
        self,
        request: ResumptionRequest,
        *,
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> ResumptionResult: ...

    def interrupt(self, request: InterruptionRequest) -> InterruptionResult: ...

    def inspect(self, request: InspectionRequest) -> InspectionResult: ...

    def lookup_normalized_request(
        self,
        normalized_request_id: str,
    ) -> ResumptionResult | None: ...


@runtime_checkable
class ConversationActivityJournal(Protocol):
    """Persistence port for non-semantic conversational activity records."""

    def put(
        self,
        record: ConversationActivityRecord,
    ) -> ConversationActivityRecord: ...

    def get(
        self,
        record_kind: ConversationRecordKind,
        record_id: str,
    ) -> ConversationActivityRecord | None: ...

    def find_contribution(
        self,
        *,
        idempotency_key: str,
    ) -> ContributionRecord | None: ...

    def find_normalized_request(
        self,
        normalized_request_id: str,
    ) -> NormalizedRequestRecord | None: ...

    def find_result(
        self,
        normalized_request_id: str,
    ) -> StructuredResultRecord | None: ...

    def list_for_contribution(
        self,
        contribution_id: str,
    ) -> tuple[ConversationActivityRecord, ...]: ...


__all__ = ["ConversationActivityJournal", "SemanticResumptionPort"]
