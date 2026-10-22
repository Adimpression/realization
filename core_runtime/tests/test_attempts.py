from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from realized_core_runtime import (
    AttemptExecutionOutcome,
    AttemptInterrupted,
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptUpdate,
    AttemptWorkResult,
    InterruptionDisposition,
    InterruptionRequest,
    request_attempt_interruption,
    run_execution_attempt,
)


class MemoryAttemptJournal:
    def __init__(self) -> None:
        self.records: dict[str, AttemptRecord] = {}
        self.events: list[str] = []

    def prepare_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        if attempt.attempt_id in self.records:
            raise ValueError("duplicate attempt")
        self.events.append(f"prepare:{attempt.attempt_id}")
        self.records[attempt.attempt_id] = attempt
        return attempt

    def load_attempt(self, attempt_id: str) -> AttemptRecord | None:
        return self.records.get(attempt_id)

    def transition_attempt(
        self,
        attempt_id: str,
        *,
        expected_statuses: tuple[AttemptLifecycleStatus, ...],
        update: AttemptUpdate,
    ) -> AttemptRecord | None:
        current = self.records.get(attempt_id)
        if current is None or current.status not in expected_statuses:
            return None
        self.events.append(f"{current.status}->{update.status}")
        replacement = replace(
            current,
            status=update.status,
            latest_admitted_revision_id=update.latest_admitted_revision_id,
            proposal_references=update.proposal_references,
            receipt_references=update.receipt_references,
            transition_artifact_references=(
                update.transition_artifact_references
            ),
            interruption_cause=update.interruption_cause,
            interruption_correlation=dict(update.interruption_correlation),
            operational_error=update.operational_error,
            performance_measurements={
                **current.performance_measurements,
                **update.performance_measurements,
            },
        )
        self.records[attempt_id] = replacement
        return replacement

    def attempt_artifact_reference(self, attempt_id: str) -> str:
        return f"attempt:{attempt_id}"

    def record_attempt_performance(
        self,
        attempt_id: str,
        measurements: dict[str, int],
    ) -> AttemptRecord | None:
        current = self.records.get(attempt_id)
        if current is None:
            return None
        merged = dict(current.performance_measurements)
        for key, value in measurements.items():
            merged[key] = merged.get(key, 0) + value
        replacement = replace(
            current,
            performance_measurements=merged,
        )
        self.records[attempt_id] = replacement
        return replacement


class ReturningWork:
    def __init__(self, journal: MemoryAttemptJournal | None = None) -> None:
        self.journal = journal
        self.saw_running = False

    def execute(self, *, should_stop: Any) -> AttemptWorkResult:
        if self.journal is not None:
            current = self.journal.load_attempt("attempt-1")
            self.saw_running = (
                current is not None
                and current.status is AttemptLifecycleStatus.RUNNING
            )
        return AttemptWorkResult(
            semantic_outcome="completed",
            latest_admitted_revision_id="revision-2",
            proposal_references=("proposal-1",),
            receipt_references=("receipt-1",),
            transition_artifact_references=("transition-1",),
            payload={"answer": 42},
        )


class InterruptingWork:
    def __init__(self, journal: MemoryAttemptJournal, *, raise_after: bool) -> None:
        self.journal = journal
        self.raise_after = raise_after

    def execute(self, *, should_stop: Any) -> AttemptWorkResult:
        request_attempt_interruption(
            self.journal,
            InterruptionRequest(
                attempt_id="attempt-1",
                requesting_principal="operator",
                reason="user stop",
                correlation={"request_id": "stop-1"},
            ),
        )
        self.assert_stop(should_stop())
        if self.raise_after:
            raise AttemptInterrupted()
        return AttemptWorkResult(
            semantic_outcome="completed",
            latest_admitted_revision_id="late-revision",
            transition_artifact_references=("late-transition",),
        )

    @staticmethod
    def assert_stop(value: bool) -> None:
        if not value:
            raise AssertionError("accepted interruption was not observable")


class FailingWork:
    def execute(self, *, should_stop: Any) -> AttemptWorkResult:
        raise OSError("host disappeared")


def prepared_attempt() -> AttemptRecord:
    return AttemptRecord(
        attempt_id="attempt-1",
        causal_anchor="scope/objective/branch/revision-1",
        operation="continue",
        latest_admitted_revision_id="revision-1",
    )


class AttemptLifecycleTests(unittest.TestCase):
    def test_attempt_is_durable_and_running_before_work_executes(self) -> None:
        journal = MemoryAttemptJournal()
        work = ReturningWork(journal)

        result = run_execution_attempt(journal, prepared_attempt(), work)

        self.assertTrue(work.saw_running)
        self.assertEqual(
            [
                "prepare:attempt-1",
                "prepared->running",
                "running->terminated",
            ],
            journal.events,
        )
        self.assertEqual(AttemptExecutionOutcome.TERMINATED, result.outcome)
        self.assertEqual("revision-2", result.attempt.latest_admitted_revision_id)
        self.assertEqual(("transition-1",), result.attempt.transition_artifact_references)
        self.assertGreater(
            result.attempt.performance_measurements[
                "attempt_preparation_latency_ns"
            ],
            0,
        )

    def test_interruption_is_operational_and_carries_no_semantic_revision(self) -> None:
        journal = MemoryAttemptJournal()
        journal.prepare_attempt(prepared_attempt())

        result = request_attempt_interruption(
            journal,
            InterruptionRequest(
                attempt_id="attempt-1",
                requesting_principal="operator",
                reason="cancelled",
            ),
        )

        self.assertEqual(InterruptionDisposition.ACCEPTED, result.disposition)
        self.assertEqual(AttemptLifecycleStatus.INTERRUPTED, result.resulting_status)
        self.assertFalse(result.semantic_revision_created)
        self.assertEqual("revision-1", result.latest_admitted_revision_id)

    def test_late_result_cannot_terminate_an_interrupted_attempt(self) -> None:
        journal = MemoryAttemptJournal()

        result = run_execution_attempt(
            journal,
            prepared_attempt(),
            InterruptingWork(journal, raise_after=False),
        )

        self.assertEqual(AttemptExecutionOutcome.INTERRUPTED, result.outcome)
        self.assertIsNone(result.work_result)
        self.assertEqual("revision-1", result.attempt.latest_admitted_revision_id)
        self.assertEqual((), result.attempt.transition_artifact_references)

    def test_cooperative_interruption_preserves_interrupted_status(self) -> None:
        journal = MemoryAttemptJournal()

        result = run_execution_attempt(
            journal,
            prepared_attempt(),
            InterruptingWork(journal, raise_after=True),
        )

        self.assertEqual(AttemptExecutionOutcome.INTERRUPTED, result.outcome)
        self.assertEqual("user stop", result.attempt.interruption_cause)
        self.assertEqual(
            {"request_id": "stop-1"},
            result.attempt.interruption_correlation,
        )

    def test_operational_exception_is_not_a_semantic_failure(self) -> None:
        journal = MemoryAttemptJournal()

        result = run_execution_attempt(journal, prepared_attempt(), FailingWork())

        self.assertEqual(
            AttemptExecutionOutcome.OPERATIONALLY_FAILED,
            result.outcome,
        )
        self.assertEqual(
            AttemptLifecycleStatus.OPERATIONALLY_FAILED,
            result.attempt.status,
        )
        self.assertIn("host disappeared", result.error or "")

    def test_interrupting_a_terminal_attempt_is_idempotently_complete(self) -> None:
        journal = MemoryAttemptJournal()
        run_execution_attempt(journal, prepared_attempt(), ReturningWork())

        result = request_attempt_interruption(
            journal,
            InterruptionRequest(
                attempt_id="attempt-1",
                requesting_principal="operator",
            ),
        )

        self.assertEqual(
            InterruptionDisposition.ALREADY_COMPLETE,
            result.disposition,
        )
        self.assertEqual(AttemptLifecycleStatus.TERMINATED, result.resulting_status)


if __name__ == "__main__":
    unittest.main()
