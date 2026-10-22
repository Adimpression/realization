"""Dependency-inverted execution-attempt lifecycle.

An attempt is an operational episode.  It deliberately carries an opaque
causal anchor so this package can enforce lifecycle rules without owning the
engine's semantic identity model.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable


class AttemptLifecycleStatus(StrEnum):
    """Durable lifecycle states for one execution attempt."""

    PREPARED = "prepared"
    RUNNING = "running"
    INTERRUPTED = "interrupted"
    TERMINATED = "terminated"
    OPERATIONALLY_FAILED = "operationally_failed"


class AttemptExecutionOutcome(StrEnum):
    """Operational outcome, kept separate from any semantic disposition."""

    TERMINATED = "terminated"
    INTERRUPTED = "interrupted"
    OPERATIONALLY_FAILED = "operationally_failed"


class InterruptionDisposition(StrEnum):
    """Result of an interruption request against an attempt."""

    ACCEPTED = "accepted"
    ALREADY_COMPLETE = "already_complete"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    """Durable operational record; none of its fields constitute semantic state."""

    attempt_id: str
    causal_anchor: str
    operation: str
    execution_policy: Mapping[str, Any] = field(default_factory=dict)
    status: AttemptLifecycleStatus = AttemptLifecycleStatus.PREPARED
    latest_admitted_revision_id: str | None = None
    proposal_references: tuple[str, ...] = ()
    receipt_references: tuple[str, ...] = ()
    transition_artifact_references: tuple[str, ...] = ()
    interruption_cause: str | None = None
    interruption_correlation: Mapping[str, Any] = field(default_factory=dict)
    operational_error: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True, slots=True)
class AttemptUpdate:
    """Fields written by a conditional lifecycle transition."""

    status: AttemptLifecycleStatus
    latest_admitted_revision_id: str | None = None
    proposal_references: tuple[str, ...] = ()
    receipt_references: tuple[str, ...] = ()
    transition_artifact_references: tuple[str, ...] = ()
    interruption_cause: str | None = None
    interruption_correlation: Mapping[str, Any] = field(default_factory=dict)
    operational_error: str | None = None


@dataclass(frozen=True, slots=True)
class AttemptWorkResult:
    """Externalized result returned by prepared work before lifecycle admission."""

    semantic_outcome: str | None = None
    latest_admitted_revision_id: str | None = None
    proposal_references: tuple[str, ...] = ()
    receipt_references: tuple[str, ...] = ()
    transition_artifact_references: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AttemptRunResult:
    """Observed operational result and the durable attempt record proving it."""

    outcome: AttemptExecutionOutcome
    attempt: AttemptRecord
    work_result: AttemptWorkResult | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class InterruptionRequest:
    """Operational stop request addressed to one exact attempt."""

    attempt_id: str
    requesting_principal: str
    authority_context: Mapping[str, Any] = field(default_factory=dict)
    reason: str | None = None
    correlation: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InterruptionResult:
    """Result of stopping execution, with an explicit no-semantic-change claim."""

    attempt_id: str
    prior_status: AttemptLifecycleStatus
    resulting_status: AttemptLifecycleStatus
    disposition: InterruptionDisposition
    latest_admitted_revision_id: str | None
    attempt_artifact_reference: str
    semantic_revision_created: bool = False


@runtime_checkable
class AttemptJournal(Protocol):
    """Persistence port required by the generic attempt lifecycle."""

    def prepare_attempt(self, attempt: AttemptRecord) -> AttemptRecord: ...

    def load_attempt(self, attempt_id: str) -> AttemptRecord | None: ...

    def transition_attempt(
        self,
        attempt_id: str,
        *,
        expected_statuses: tuple[AttemptLifecycleStatus, ...],
        update: AttemptUpdate,
    ) -> AttemptRecord | None: ...

    def attempt_artifact_reference(self, attempt_id: str) -> str: ...


@runtime_checkable
class PreparedAttemptWork(Protocol):
    """Prepared work advanced by the runtime under an observable stop signal."""

    def execute(
        self,
        *,
        should_stop: Callable[[], bool],
    ) -> AttemptWorkResult: ...


class AttemptInterrupted(RuntimeError):
    """Raised by prepared work after observing an accepted stop request."""


def attempt_stop_requested(journal: AttemptJournal, attempt_id: str) -> bool:
    """Return whether the durable attempt lifecycle records interruption."""

    attempt = journal.load_attempt(attempt_id)
    return (
        attempt is not None
        and attempt.status is AttemptLifecycleStatus.INTERRUPTED
    )


def run_execution_attempt(
    journal: AttemptJournal,
    attempt: AttemptRecord,
    work: PreparedAttemptWork,
) -> AttemptRunResult:
    """Durably run prepared work without assigning semantic meaning to stopping."""

    if attempt.status is not AttemptLifecycleStatus.PREPARED:
        raise ValueError("an execution attempt must begin in prepared status")

    prepared = journal.prepare_attempt(attempt)
    running = journal.transition_attempt(
        prepared.attempt_id,
        expected_statuses=(AttemptLifecycleStatus.PREPARED,),
        update=AttemptUpdate(
            status=AttemptLifecycleStatus.RUNNING,
            latest_admitted_revision_id=prepared.latest_admitted_revision_id,
        ),
    )
    if running is None:
        current = journal.load_attempt(prepared.attempt_id)
        if current is None:
            raise RuntimeError("prepared execution attempt disappeared")
        return AttemptRunResult(
            outcome=_execution_outcome(current.status),
            attempt=current,
        )

    try:
        result = work.execute(
            should_stop=lambda: attempt_stop_requested(journal, running.attempt_id)
        )
    except AttemptInterrupted:
        current = journal.load_attempt(running.attempt_id)
        if current is None:
            raise RuntimeError("interrupted execution attempt disappeared")
        if current.status is not AttemptLifecycleStatus.INTERRUPTED:
            current = journal.transition_attempt(
                running.attempt_id,
                expected_statuses=(AttemptLifecycleStatus.RUNNING,),
                update=AttemptUpdate(
                    status=AttemptLifecycleStatus.INTERRUPTED,
                    latest_admitted_revision_id=(
                        running.latest_admitted_revision_id
                    ),
                    interruption_cause="stop signal observed",
                ),
            ) or journal.load_attempt(running.attempt_id)
        if current is None:
            raise RuntimeError("interrupted execution attempt disappeared")
        return AttemptRunResult(
            outcome=AttemptExecutionOutcome.INTERRUPTED,
            attempt=current,
        )
    except Exception as exc:
        failed = journal.transition_attempt(
            running.attempt_id,
            expected_statuses=(AttemptLifecycleStatus.RUNNING,),
            update=AttemptUpdate(
                status=AttemptLifecycleStatus.OPERATIONALLY_FAILED,
                latest_admitted_revision_id=running.latest_admitted_revision_id,
                operational_error=f"{type(exc).__name__}: {exc}",
            ),
        )
        current = failed or journal.load_attempt(running.attempt_id)
        if current is None:
            raise RuntimeError("failed execution attempt disappeared") from exc
        return AttemptRunResult(
            outcome=_execution_outcome(current.status),
            attempt=current,
            error=current.operational_error,
        )

    terminated = journal.transition_attempt(
        running.attempt_id,
        expected_statuses=(AttemptLifecycleStatus.RUNNING,),
        update=AttemptUpdate(
            status=AttemptLifecycleStatus.TERMINATED,
            latest_admitted_revision_id=result.latest_admitted_revision_id,
            proposal_references=result.proposal_references,
            receipt_references=result.receipt_references,
            transition_artifact_references=(
                result.transition_artifact_references
            ),
        ),
    )
    if terminated is None:
        current = journal.load_attempt(running.attempt_id)
        if current is None:
            raise RuntimeError("completed execution attempt disappeared")
        return AttemptRunResult(
            outcome=_execution_outcome(current.status),
            attempt=current,
            work_result=None,
        )
    return AttemptRunResult(
        outcome=AttemptExecutionOutcome.TERMINATED,
        attempt=terminated,
        work_result=result,
    )


def request_attempt_interruption(
    journal: AttemptJournal,
    request: InterruptionRequest,
) -> InterruptionResult:
    """Stop an operational attempt without creating a semantic transition."""

    current = journal.load_attempt(request.attempt_id)
    if current is None:
        raise KeyError(f"unknown execution attempt: {request.attempt_id}")

    if current.status in {
        AttemptLifecycleStatus.TERMINATED,
        AttemptLifecycleStatus.OPERATIONALLY_FAILED,
    }:
        disposition = InterruptionDisposition.ALREADY_COMPLETE
        result = current
    elif current.status is AttemptLifecycleStatus.INTERRUPTED:
        disposition = InterruptionDisposition.NOT_APPLICABLE
        result = current
    else:
        result = journal.transition_attempt(
            request.attempt_id,
            expected_statuses=(
                AttemptLifecycleStatus.PREPARED,
                AttemptLifecycleStatus.RUNNING,
            ),
            update=AttemptUpdate(
                status=AttemptLifecycleStatus.INTERRUPTED,
                latest_admitted_revision_id=(
                    current.latest_admitted_revision_id
                ),
                interruption_cause=request.reason,
                interruption_correlation=dict(request.correlation),
            ),
        )
        if result is None:
            result = journal.load_attempt(request.attempt_id)
            if result is None:
                raise RuntimeError("execution attempt disappeared during interruption")
            disposition = (
                InterruptionDisposition.ALREADY_COMPLETE
                if result.status
                in {
                    AttemptLifecycleStatus.TERMINATED,
                    AttemptLifecycleStatus.OPERATIONALLY_FAILED,
                }
                else InterruptionDisposition.NOT_APPLICABLE
            )
        else:
            disposition = InterruptionDisposition.ACCEPTED

    return InterruptionResult(
        attempt_id=result.attempt_id,
        prior_status=current.status,
        resulting_status=result.status,
        disposition=disposition,
        latest_admitted_revision_id=result.latest_admitted_revision_id,
        attempt_artifact_reference=journal.attempt_artifact_reference(
            result.attempt_id
        ),
    )


def _execution_outcome(status: AttemptLifecycleStatus) -> AttemptExecutionOutcome:
    if status is AttemptLifecycleStatus.INTERRUPTED:
        return AttemptExecutionOutcome.INTERRUPTED
    if status is AttemptLifecycleStatus.TERMINATED:
        return AttemptExecutionOutcome.TERMINATED
    return AttemptExecutionOutcome.OPERATIONALLY_FAILED


__all__ = [
    "AttemptExecutionOutcome",
    "AttemptInterrupted",
    "AttemptJournal",
    "AttemptLifecycleStatus",
    "AttemptRecord",
    "AttemptRunResult",
    "AttemptUpdate",
    "AttemptWorkResult",
    "InterruptionDisposition",
    "InterruptionRequest",
    "InterruptionResult",
    "PreparedAttemptWork",
    "attempt_stop_requested",
    "request_attempt_interruption",
    "run_execution_attempt",
]
