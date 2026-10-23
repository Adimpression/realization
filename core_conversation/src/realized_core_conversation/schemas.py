"""Versioned, transport-neutral records for conversation activity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar


CONVERSATION_RECORD_SCHEMA_VERSION = 1


class ConversationSchemaError(ValueError):
    """Raised when a durable conversation record is not well formed."""


class ConversationRecordKind(StrEnum):
    CONTRIBUTION = "contribution"
    PROPOSAL = "proposal"
    NORMALIZED_REQUEST = "normalized_request"
    STRUCTURED_RESULT = "structured_result"
    RENDERING = "rendering"
    RECEIPT = "receipt"
    RECOVERY_DECISION = "recovery_decision"


class ConversationActivityStatus(StrEnum):
    RECEIVED = "received"
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"
    PREPARED = "prepared"
    SUBMITTED = "submitted"
    RECOVERED = "recovered"
    SKIPPED = "skipped"
    DELIVERED = "delivered"


@dataclass(frozen=True, slots=True)
class ContributionRecord:
    """Original user contribution before semantic interpretation."""

    KIND: ClassVar[ConversationRecordKind] = ConversationRecordKind.CONTRIBUTION

    contribution_id: str
    session_id: str
    idempotency_key: str
    text: str
    scope_id: str
    received_at: str
    selected_binding: dict[str, Any] | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    correlation: dict[str, Any] = field(default_factory=dict)
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.contribution_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "contribution_id": self.contribution_id,
            "session_id": self.session_id,
            "idempotency_key": self.idempotency_key,
            "text": self.text,
            "scope_id": self.scope_id,
            "received_at": self.received_at,
            "selected_binding": _optional_object(self.selected_binding),
            "provenance": dict(self.provenance),
            "correlation": dict(self.correlation),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ContributionRecord:
        _validate_header(value, cls.KIND)
        return cls(
            contribution_id=_required(value, "contribution_id"),
            session_id=_required(value, "session_id"),
            idempotency_key=_required(value, "idempotency_key"),
            text=_required(value, "text"),
            scope_id=_required(value, "scope_id"),
            received_at=_required(value, "received_at"),
            selected_binding=_optional_object(value.get("selected_binding")),
            provenance=_object(value.get("provenance")),
            correlation=_object(value.get("correlation")),
        )


@dataclass(frozen=True, slots=True)
class PlanningProposalRecord:
    """One externalized advisory proposal and its interpretation status."""

    KIND: ClassVar[ConversationRecordKind] = ConversationRecordKind.PROPOSAL

    planning_attempt_id: str
    contribution_id: str
    status: ConversationActivityStatus
    planning_context_digest: str
    proposal: dict[str, Any]
    created_at: str
    proposal_schema_version: str
    prompt_version: str
    normalized_plan: dict[str, Any] = field(default_factory=dict)
    provider_receipt: dict[str, Any] = field(default_factory=dict)
    unresolved_interpretation: tuple[str, ...] = ()
    error: dict[str, Any] = field(default_factory=dict)
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.planning_attempt_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "planning_attempt_id": self.planning_attempt_id,
            "contribution_id": self.contribution_id,
            "status": self.status.value,
            "planning_context_digest": self.planning_context_digest,
            "proposal": dict(self.proposal),
            "created_at": self.created_at,
            "proposal_schema_version": self.proposal_schema_version,
            "prompt_version": self.prompt_version,
            "normalized_plan": dict(self.normalized_plan),
            "provider_receipt": dict(self.provider_receipt),
            "unresolved_interpretation": list(self.unresolved_interpretation),
            "error": dict(self.error),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> PlanningProposalRecord:
        _validate_header(value, cls.KIND)
        return cls(
            planning_attempt_id=_required(value, "planning_attempt_id"),
            contribution_id=_required(value, "contribution_id"),
            status=_status(value.get("status")),
            planning_context_digest=_required(value, "planning_context_digest"),
            proposal=_object(value.get("proposal")),
            created_at=_required(value, "created_at"),
            proposal_schema_version=_required(
                value, "proposal_schema_version"
            ),
            prompt_version=_required(value, "prompt_version"),
            normalized_plan=_object(value.get("normalized_plan")),
            provider_receipt=_object(value.get("provider_receipt")),
            unresolved_interpretation=_strings(
                value.get("unresolved_interpretation")
            ),
            error=_object(value.get("error")),
        )


@dataclass(frozen=True, slots=True)
class NormalizedRequestRecord:
    """Canonical semantic request prepared for idempotent submission."""

    KIND: ClassVar[ConversationRecordKind] = (
        ConversationRecordKind.NORMALIZED_REQUEST
    )

    normalized_request_id: str
    contribution_id: str
    planning_attempt_id: str
    operation: str
    request_payload: dict[str, Any]
    request_digest: str
    causal_anchor: dict[str, Any]
    created_at: str
    submission_status: ConversationActivityStatus = (
        ConversationActivityStatus.PREPARED
    )
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.normalized_request_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "normalized_request_id": self.normalized_request_id,
            "contribution_id": self.contribution_id,
            "planning_attempt_id": self.planning_attempt_id,
            "operation": self.operation,
            "request_payload": dict(self.request_payload),
            "request_digest": self.request_digest,
            "causal_anchor": dict(self.causal_anchor),
            "created_at": self.created_at,
            "submission_status": self.submission_status.value,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> NormalizedRequestRecord:
        _validate_header(value, cls.KIND)
        return cls(
            normalized_request_id=_required(value, "normalized_request_id"),
            contribution_id=_required(value, "contribution_id"),
            planning_attempt_id=_required(value, "planning_attempt_id"),
            operation=_required(value, "operation"),
            request_payload=_object(value.get("request_payload")),
            request_digest=_required(value, "request_digest"),
            causal_anchor=_object(value.get("causal_anchor")),
            created_at=_required(value, "created_at"),
            submission_status=_status(value.get("submission_status")),
        )


@dataclass(frozen=True, slots=True)
class StructuredResultRecord:
    """Durable engine result captured before rendering begins."""

    KIND: ClassVar[ConversationRecordKind] = (
        ConversationRecordKind.STRUCTURED_RESULT
    )

    result_id: str
    normalized_request_id: str
    contribution_id: str
    execution_attempt_id: str
    result_payload: dict[str, Any]
    recorded_at: str
    resulting_binding: dict[str, Any] | None = None
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.result_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "result_id": self.result_id,
            "normalized_request_id": self.normalized_request_id,
            "contribution_id": self.contribution_id,
            "execution_attempt_id": self.execution_attempt_id,
            "result_payload": dict(self.result_payload),
            "recorded_at": self.recorded_at,
            "resulting_binding": _optional_object(self.resulting_binding),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> StructuredResultRecord:
        _validate_header(value, cls.KIND)
        return cls(
            result_id=_required(value, "result_id"),
            normalized_request_id=_required(value, "normalized_request_id"),
            contribution_id=_required(value, "contribution_id"),
            execution_attempt_id=_required(value, "execution_attempt_id"),
            result_payload=_object(value.get("result_payload")),
            recorded_at=_required(value, "recorded_at"),
            resulting_binding=_optional_object(value.get("resulting_binding")),
        )


@dataclass(frozen=True, slots=True)
class RenderingRecord:
    """One presentation attempt over an already durable structured result."""

    KIND: ClassVar[ConversationRecordKind] = ConversationRecordKind.RENDERING

    rendering_attempt_id: str
    contribution_id: str
    result_id: str
    status: ConversationActivityStatus
    rendering_request: dict[str, Any]
    started_at: str
    rendering_schema_version: str
    prompt_version: str
    presentation: str = ""
    provider_receipt: dict[str, Any] = field(default_factory=dict)
    completed_at: str = ""
    delivery_status: ConversationActivityStatus = (
        ConversationActivityStatus.PENDING
    )
    error: dict[str, Any] = field(default_factory=dict)
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.rendering_attempt_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "rendering_attempt_id": self.rendering_attempt_id,
            "contribution_id": self.contribution_id,
            "result_id": self.result_id,
            "status": self.status.value,
            "rendering_request": dict(self.rendering_request),
            "started_at": self.started_at,
            "rendering_schema_version": self.rendering_schema_version,
            "prompt_version": self.prompt_version,
            "presentation": self.presentation,
            "provider_receipt": dict(self.provider_receipt),
            "completed_at": self.completed_at,
            "delivery_status": self.delivery_status.value,
            "error": dict(self.error),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RenderingRecord:
        _validate_header(value, cls.KIND)
        return cls(
            rendering_attempt_id=_required(value, "rendering_attempt_id"),
            contribution_id=_required(value, "contribution_id"),
            result_id=_required(value, "result_id"),
            status=_status(value.get("status")),
            rendering_request=_object(value.get("rendering_request")),
            started_at=_required(value, "started_at"),
            rendering_schema_version=_required(
                value, "rendering_schema_version"
            ),
            prompt_version=_required(value, "prompt_version"),
            presentation=str(value.get("presentation", "")),
            provider_receipt=_object(value.get("provider_receipt")),
            completed_at=str(value.get("completed_at", "")),
            delivery_status=_status(value.get("delivery_status")),
            error=_object(value.get("error")),
        )


@dataclass(frozen=True, slots=True)
class ConversationReceipt:
    """Inspectable application provenance for one conversation stage."""

    KIND: ClassVar[ConversationRecordKind] = ConversationRecordKind.RECEIPT

    receipt_id: str
    stage: str
    status: ConversationActivityStatus
    correlation_ids: dict[str, str]
    payload: dict[str, Any]
    recorded_at: str
    complete: bool = True
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.receipt_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "receipt_id": self.receipt_id,
            "stage": self.stage,
            "status": self.status.value,
            "correlation_ids": dict(self.correlation_ids),
            "payload": dict(self.payload),
            "recorded_at": self.recorded_at,
            "complete": self.complete,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ConversationReceipt:
        _validate_header(value, cls.KIND)
        return cls(
            receipt_id=_required(value, "receipt_id"),
            stage=_required(value, "stage"),
            status=_status(value.get("status")),
            correlation_ids={
                str(key): str(item)
                for key, item in _object(
                    value.get("correlation_ids")
                ).items()
            },
            payload=_object(value.get("payload")),
            recorded_at=_required(value, "recorded_at"),
            complete=bool(value.get("complete", True)),
        )


@dataclass(frozen=True, slots=True)
class RecoveryDecisionRecord:
    """Durable explanation of how a retry resumed from a prior stage."""

    KIND: ClassVar[ConversationRecordKind] = (
        ConversationRecordKind.RECOVERY_DECISION
    )

    recovery_decision_id: str
    contribution_id: str
    stage: str
    action: str
    reason: str
    linked_record_ids: dict[str, str]
    recorded_at: str
    schema_version: int = CONVERSATION_RECORD_SCHEMA_VERSION

    @property
    def record_id(self) -> str:
        return self.recovery_decision_id

    def to_dict(self) -> dict[str, Any]:
        return {
            **_record_header(self),
            "recovery_decision_id": self.recovery_decision_id,
            "contribution_id": self.contribution_id,
            "stage": self.stage,
            "action": self.action,
            "reason": self.reason,
            "linked_record_ids": dict(self.linked_record_ids),
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RecoveryDecisionRecord:
        _validate_header(value, cls.KIND)
        return cls(
            recovery_decision_id=_required(value, "recovery_decision_id"),
            contribution_id=_required(value, "contribution_id"),
            stage=_required(value, "stage"),
            action=_required(value, "action"),
            reason=_required(value, "reason"),
            linked_record_ids={
                str(key): str(item)
                for key, item in _object(
                    value.get("linked_record_ids")
                ).items()
            },
            recorded_at=_required(value, "recorded_at"),
        )


type ConversationActivityRecord = (
    ContributionRecord
    | PlanningProposalRecord
    | NormalizedRequestRecord
    | StructuredResultRecord
    | RenderingRecord
    | ConversationReceipt
    | RecoveryDecisionRecord
)


_RECORD_TYPES = {
    record_type.KIND: record_type
    for record_type in (
        ContributionRecord,
        PlanningProposalRecord,
        NormalizedRequestRecord,
        StructuredResultRecord,
        RenderingRecord,
        ConversationReceipt,
        RecoveryDecisionRecord,
    )
}


def conversation_record_from_dict(
    value: Mapping[str, Any],
) -> ConversationActivityRecord:
    """Restore a versioned record using its explicit discriminator."""

    try:
        kind = ConversationRecordKind(str(value.get("record_kind", "")))
    except ValueError as exc:
        raise ConversationSchemaError("Unsupported conversation record kind.") from exc
    return _RECORD_TYPES[kind].from_dict(value)


def _record_header(value: ConversationActivityRecord) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "record_kind": value.KIND.value,
        "record_id": value.record_id,
    }


def _validate_header(
    value: Mapping[str, Any],
    expected_kind: ConversationRecordKind,
) -> None:
    try:
        version = int(value.get("schema_version", 0))
    except (TypeError, ValueError) as exc:
        raise ConversationSchemaError(
            "Conversation record schema_version must be an integer."
        ) from exc
    if version != CONVERSATION_RECORD_SCHEMA_VERSION:
        raise ConversationSchemaError(
            f"Unsupported conversation record schema version: {version}"
        )
    if str(value.get("record_kind", "")) != expected_kind.value:
        raise ConversationSchemaError(
            f"Expected {expected_kind.value} conversation record."
        )


def _required(value: Mapping[str, Any], key: str) -> str:
    result = str(value.get(key, "")).strip()
    if not result:
        raise ConversationSchemaError(f"{key} is required.")
    return result


def _object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConversationSchemaError("Expected a JSON object.")
    return {str(key): item for key, item in value.items()}


def _optional_object(value: Any) -> dict[str, Any] | None:
    return None if value is None else _object(value)


def _strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ConversationSchemaError("Expected a JSON string array.")
    return tuple(str(item) for item in value if str(item).strip())


def _status(value: Any) -> ConversationActivityStatus:
    try:
        return ConversationActivityStatus(str(value))
    except ValueError as exc:
        raise ConversationSchemaError(
            f"Unsupported conversation activity status: {value}"
        ) from exc


__all__ = [
    "CONVERSATION_RECORD_SCHEMA_VERSION",
    "ConversationActivityRecord",
    "ConversationActivityStatus",
    "ConversationReceipt",
    "ConversationRecordKind",
    "ConversationSchemaError",
    "ContributionRecord",
    "NormalizedRequestRecord",
    "PlanningProposalRecord",
    "RecoveryDecisionRecord",
    "RenderingRecord",
    "StructuredResultRecord",
    "conversation_record_from_dict",
]
