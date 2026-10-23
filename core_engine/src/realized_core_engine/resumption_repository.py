"""Plain-SQLite persistence for governed resumption.

Immutable revisions and transition artifacts are canonical.  Branch heads are
updated with compare-and-swap, while execution attempts live in a separate
journal so operational interruption cannot mutate semantic state.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_core_runtime import (
    AttemptLifecycleRecord,
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptUpdate,
    merge_performance_measurements,
)

from realized_core_engine.resumption_contracts import (
    ResumptionIdentity,
    ResumptionProjection,
    ResumptionResult,
    Revision,
    SemanticState,
    TransitionArtifact,
    canonical_json,
    content_digest,
)


class ResumptionRepositoryError(RuntimeError):
    """Base class for authoritative resumption persistence failures."""


class StaleAnchorError(ResumptionRepositoryError):
    """Raised when a branch head no longer equals the caller's exact anchor."""

    def __init__(self, expected: str | None, actual: str | None) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"stale branch anchor: expected {expected!r}, actual {actual!r}"
        )


class AttemptNotRunningError(ResumptionRepositoryError):
    """Raised when interrupted or terminal work tries to commit semantic state."""


class RepositoryIntegrityError(ResumptionRepositoryError):
    """Raised when persisted canonical data fails digest or identity checks."""


@dataclass(frozen=True, slots=True)
class NormalizedRequestBinding:
    """Durable idempotency binding from one request to one attempt/result."""

    normalized_request_id: str
    request_digest: str
    operation: str
    request_payload: dict[str, Any]
    attempt_id: str
    result: ResumptionResult | None
    created_at: str
    updated_at: str


class SQLiteResumptionRepository:
    """Authoritative SQLite repository and execution-attempt journal."""

    def __init__(
        self,
        path: Path,
        *,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self.path = path.expanduser().resolve()
        self._clock = clock or _utc_now
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS resumption_transition_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    decision_flow_signature TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resumption_revisions (
                    revision_id TEXT PRIMARY KEY,
                    scope_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    state_digest TEXT NOT NULL,
                    revision_digest TEXT NOT NULL UNIQUE,
                    state_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    governance_json TEXT NOT NULL,
                    transition_artifact_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (transition_artifact_id)
                        REFERENCES resumption_transition_artifacts(artifact_id)
                );

                CREATE TABLE IF NOT EXISTS resumption_revision_parents (
                    revision_id TEXT NOT NULL,
                    parent_revision_id TEXT NOT NULL,
                    parent_order INTEGER NOT NULL,
                    PRIMARY KEY (revision_id, parent_order),
                    UNIQUE (revision_id, parent_revision_id),
                    FOREIGN KEY (revision_id)
                        REFERENCES resumption_revisions(revision_id),
                    FOREIGN KEY (parent_revision_id)
                        REFERENCES resumption_revisions(revision_id)
                );

                CREATE TABLE IF NOT EXISTS resumption_branch_heads (
                    scope_id TEXT NOT NULL,
                    objective_id TEXT NOT NULL,
                    branch_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    revision_digest TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (scope_id, objective_id, branch_id),
                    FOREIGN KEY (revision_id)
                        REFERENCES resumption_revisions(revision_id)
                );

                CREATE TABLE IF NOT EXISTS resumption_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    causal_anchor TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    initial_branch_head_revision_id TEXT,
                    initial_branch_head_digest TEXT,
                    execution_policy_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latest_admitted_revision_id TEXT,
                    proposal_references_json TEXT NOT NULL,
                    receipt_references_json TEXT NOT NULL,
                    transition_artifact_references_json TEXT NOT NULL,
                    interruption_cause TEXT,
                    interruption_correlation_json TEXT NOT NULL,
                    operational_error TEXT,
                    lifecycle_records_json TEXT NOT NULL,
                    performance_measurements_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resumption_normalized_requests (
                    normalized_request_id TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    attempt_id TEXT NOT NULL UNIQUE,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resumption_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_kind TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    revision_id TEXT,
                    attempt_id TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_resumption_revisions_identity
                    ON resumption_revisions(scope_id, objective_id, branch_id);
                CREATE INDEX IF NOT EXISTS idx_resumption_parents_parent
                    ON resumption_revision_parents(parent_revision_id);
                CREATE INDEX IF NOT EXISTS idx_resumption_attempts_status
                    ON resumption_attempts(status);
                """
            )
            self._add_column_if_missing(
                connection,
                table="resumption_attempts",
                column="initial_branch_head_revision_id",
                definition="TEXT",
            )
            self._add_column_if_missing(
                connection,
                table="resumption_attempts",
                column="initial_branch_head_digest",
                definition="TEXT",
            )
            self._add_column_if_missing(
                connection,
                table="resumption_attempts",
                column="lifecycle_records_json",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            self._add_column_if_missing(
                connection,
                table="resumption_attempts",
                column="performance_measurements_json",
                definition="TEXT NOT NULL DEFAULT '{}'",
            )

    # Normalized request idempotency -----------------------------------------

    def claim_normalized_request(
        self,
        *,
        normalized_request_id: str,
        request_digest: str,
        operation: str,
        request_payload: Mapping[str, Any],
        proposed_attempt_id: str,
    ) -> tuple[NormalizedRequestBinding, bool]:
        """Bind one canonical request identity to exactly one attempt."""

        request_id = str(normalized_request_id).strip()
        if not request_id:
            raise ValueError("normalized_request_id is required")
        digest = str(request_digest).strip()
        if not digest:
            raise ValueError("request_digest is required")
        encoded_request = canonical_json(dict(request_payload))
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO resumption_normalized_requests (
                    normalized_request_id, request_digest, operation,
                    request_json, attempt_id, result_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    request_id,
                    digest,
                    str(operation),
                    encoded_request,
                    str(proposed_attempt_id),
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM resumption_normalized_requests
                WHERE normalized_request_id = ?
                """,
                (request_id,),
            ).fetchone()
            if row is None:
                raise RepositoryIntegrityError(
                    "normalized request claim disappeared"
                )
            binding = _normalized_request_from_row(row)
            if (
                binding.request_digest != digest
                or binding.operation != str(operation)
                or canonical_json(binding.request_payload) != encoded_request
            ):
                raise RepositoryIntegrityError(
                    "normalized request identity names different content: "
                    f"{request_id}"
                )
            if cursor.rowcount == 1:
                self._append_event(
                    connection,
                    event_kind="normalized_request_claimed",
                    aggregate_id=request_id,
                    attempt_id=binding.attempt_id,
                    payload={
                        "operation": binding.operation,
                        "request_digest": binding.request_digest,
                    },
                    created_at=now,
                )
            return binding, cursor.rowcount == 1

    def load_normalized_request(
        self,
        normalized_request_id: str,
    ) -> NormalizedRequestBinding | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM resumption_normalized_requests
                WHERE normalized_request_id = ?
                """,
                (str(normalized_request_id),),
            ).fetchone()
        return _normalized_request_from_row(row) if row is not None else None

    def record_normalized_request_result(
        self,
        normalized_request_id: str,
        *,
        attempt_id: str,
        result: ResumptionResult,
    ) -> NormalizedRequestBinding:
        """Record the immutable public result for an idempotent request."""

        encoded_result = canonical_json(result.to_dict())
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT * FROM resumption_normalized_requests
                WHERE normalized_request_id = ?
                """,
                (str(normalized_request_id),),
            ).fetchone()
            if row is None:
                raise KeyError(
                    f"unknown normalized request: {normalized_request_id}"
                )
            current = _normalized_request_from_row(row)
            if current.attempt_id != str(attempt_id):
                raise RepositoryIntegrityError(
                    "normalized request result points at another attempt"
                )
            if current.result is not None:
                if canonical_json(current.result.to_dict()) != encoded_result:
                    raise RepositoryIntegrityError(
                        "normalized request already has a different result"
                    )
                return current
            connection.execute(
                """
                UPDATE resumption_normalized_requests
                SET result_json = ?, updated_at = ?
                WHERE normalized_request_id = ? AND result_json IS NULL
                """,
                (encoded_result, now, str(normalized_request_id)),
            )
            self._append_event(
                connection,
                event_kind="normalized_request_completed",
                aggregate_id=str(normalized_request_id),
                attempt_id=str(attempt_id),
                revision_id=(
                    result.resulting_revision_identity.revision_id
                    if result.resulting_revision_identity is not None
                    else None
                ),
                payload={
                    "execution_outcome": result.execution_outcome.value,
                    "semantic_outcome": (
                        result.semantic_outcome.value
                        if result.semantic_outcome is not None
                        else None
                    ),
                },
                created_at=now,
            )
        restored = self.load_normalized_request(normalized_request_id)
        if restored is None:
            raise RepositoryIntegrityError(
                "normalized request result disappeared"
            )
        return restored

    def rebuild_derived_indexes(self) -> tuple[str, ...]:
        """Recreate non-authoritative indexes without touching canonical rows."""

        definitions = {
            "idx_resumption_revisions_identity": (
                "CREATE INDEX idx_resumption_revisions_identity "
                "ON resumption_revisions(scope_id, objective_id, branch_id)"
            ),
            "idx_resumption_parents_parent": (
                "CREATE INDEX idx_resumption_parents_parent "
                "ON resumption_revision_parents(parent_revision_id)"
            ),
            "idx_resumption_attempts_status": (
                "CREATE INDEX idx_resumption_attempts_status "
                "ON resumption_attempts(status)"
            ),
        }
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for name in definitions:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            for statement in definitions.values():
                connection.execute(statement)
            connection.commit()
        return tuple(definitions)

    # Execution-attempt journal -------------------------------------------------

    def prepare_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        if attempt.status is not AttemptLifecycleStatus.PREPARED:
            raise ValueError("only prepared attempts can be appended")
        now = self._clock()
        durable = replace(
            attempt,
            lifecycle_records=(
                *attempt.lifecycle_records,
                AttemptLifecycleRecord(
                    status=AttemptLifecycleStatus.PREPARED,
                    recorded_at=attempt.created_at or now,
                ),
            ),
            created_at=attempt.created_at or now,
            updated_at=now,
        )
        try:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO resumption_attempts (
                        attempt_id, causal_anchor, operation,
                        initial_branch_head_revision_id,
                        initial_branch_head_digest,
                        execution_policy_json, status,
                        latest_admitted_revision_id,
                        proposal_references_json, receipt_references_json,
                        transition_artifact_references_json,
                        interruption_cause, interruption_correlation_json,
                        operational_error, lifecycle_records_json,
                        performance_measurements_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _attempt_values(durable),
                )
                self._append_event(
                    connection,
                    event_kind="attempt_prepared",
                    aggregate_id=durable.attempt_id,
                    attempt_id=durable.attempt_id,
                    payload={"status": durable.status.value},
                    created_at=now,
                )
        except sqlite3.IntegrityError as exc:
            existing = self.load_attempt(attempt.attempt_id)
            if (
                existing is not None
                and existing.status is AttemptLifecycleStatus.PREPARED
                and _same_attempt_intent(existing, durable)
            ):
                return existing
            raise ResumptionRepositoryError(
                f"execution attempt already exists: {attempt.attempt_id}"
            ) from exc
        return durable

    def load_attempt(self, attempt_id: str) -> AttemptRecord | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM resumption_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
        return _attempt_from_row(row) if row is not None else None

    def transition_attempt(
        self,
        attempt_id: str,
        *,
        expected_statuses: tuple[AttemptLifecycleStatus, ...],
        update: AttemptUpdate,
    ) -> AttemptRecord | None:
        if not expected_statuses:
            raise ValueError("attempt transition requires an expected status")
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM resumption_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return None
            current = _attempt_from_row(row)
            if current.status not in expected_statuses:
                connection.rollback()
                return None
            replacement = _apply_attempt_update(current, update, now=now)
            placeholders = ", ".join("?" for _ in expected_statuses)
            cursor = connection.execute(
                f"""
                UPDATE resumption_attempts SET
                    status = ?, latest_admitted_revision_id = ?,
                    proposal_references_json = ?, receipt_references_json = ?,
                    transition_artifact_references_json = ?,
                    interruption_cause = ?, interruption_correlation_json = ?,
                    operational_error = ?, lifecycle_records_json = ?,
                    performance_measurements_json = ?, updated_at = ?
                WHERE attempt_id = ? AND status IN ({placeholders})
                """,
                (
                    replacement.status.value,
                    replacement.latest_admitted_revision_id,
                    canonical_json(list(replacement.proposal_references)),
                    canonical_json(list(replacement.receipt_references)),
                    canonical_json(
                        list(replacement.transition_artifact_references)
                    ),
                    replacement.interruption_cause,
                    canonical_json(dict(replacement.interruption_correlation)),
                    replacement.operational_error,
                    canonical_json(
                        [
                            record.to_dict()
                            for record in replacement.lifecycle_records
                        ]
                    ),
                    canonical_json(
                        dict(replacement.performance_measurements)
                    ),
                    replacement.updated_at,
                    attempt_id,
                    *(status.value for status in expected_statuses),
                ),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                return None
            self._append_event(
                connection,
                event_kind=f"attempt_{replacement.status.value}",
                aggregate_id=attempt_id,
                attempt_id=attempt_id,
                revision_id=replacement.latest_admitted_revision_id,
                payload={
                    "prior_status": current.status.value,
                    "status": replacement.status.value,
                },
                created_at=now,
            )
            connection.commit()
        return replacement

    def attempt_artifact_reference(self, attempt_id: str) -> str:
        return f"sqlite-resumption://attempt/{attempt_id}"

    def record_attempt_performance(
        self,
        attempt_id: str,
        measurements: Mapping[str, int],
    ) -> AttemptRecord | None:
        """Merge non-semantic measurements into the operational artifact."""

        if not measurements:
            return self.load_attempt(attempt_id)
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM resumption_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                connection.rollback()
                return None
            current = _attempt_from_row(row)
            merged = merge_performance_measurements(
                current.performance_measurements,
                measurements,
            )
            connection.execute(
                """
                UPDATE resumption_attempts
                SET performance_measurements_json = ?, updated_at = ?
                WHERE attempt_id = ?
                """,
                (canonical_json(merged), now, attempt_id),
            )
            connection.commit()
        return replace(
            current,
            performance_measurements=merged,
            updated_at=now,
        )

    def recover_running_attempts(self, *, reason: str) -> tuple[AttemptRecord, ...]:
        """Close abandoned operational episodes without changing semantic state."""

        with self._connection() as connection:
            rows = connection.execute(
                "SELECT attempt_id FROM resumption_attempts WHERE status = ?",
                (AttemptLifecycleStatus.RUNNING.value,),
            ).fetchall()
        recovered: list[AttemptRecord] = []
        for row in rows:
            result = self.transition_attempt(
                str(row["attempt_id"]),
                expected_statuses=(AttemptLifecycleStatus.RUNNING,),
                update=AttemptUpdate(
                    status=AttemptLifecycleStatus.OPERATIONALLY_FAILED,
                    operational_error=reason,
                ),
            )
            if result is not None:
                recovered.append(result)
        return tuple(recovered)

    # Semantic revisions -------------------------------------------------------

    def load_revision(self, revision_id: str) -> Revision | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM resumption_revisions WHERE revision_id = ?",
                (revision_id,),
            ).fetchone()
            if row is None:
                return None
            parent_rows = connection.execute(
                """
                SELECT parent_revision_id
                FROM resumption_revision_parents
                WHERE revision_id = ?
                ORDER BY parent_order
                """,
                (revision_id,),
            ).fetchall()
        revision = _revision_from_rows(row, parent_rows)
        if not revision.verify():
            raise RepositoryIntegrityError(
                f"revision digest verification failed: {revision_id}"
            )
        return revision

    def require_revision(self, identity: ResumptionIdentity) -> Revision:
        revision = self.load_revision(identity.revision_id)
        if revision is None:
            raise KeyError(f"unknown semantic revision: {identity.revision_id}")
        if revision.identity != identity:
            raise RepositoryIntegrityError(
                "complete resumption identity does not match the stored revision"
            )
        return revision

    def load_branch_head(
        self,
        scope_id: str,
        objective_id: str,
        branch_id: str,
    ) -> Revision | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT revision_id FROM resumption_branch_heads
                WHERE scope_id = ? AND objective_id = ? AND branch_id = ?
                """,
                (scope_id, objective_id, branch_id),
            ).fetchone()
        return self.load_revision(str(row["revision_id"])) if row else None

    def commit_revision(
        self,
        revision: Revision,
        artifact: TransitionArtifact,
        *,
        expected_head_revision_id: str | None,
        attempt_id: str,
    ) -> Revision:
        """Atomically append artifact/revision and compare-and-swap branch head."""

        if not revision.verify():
            raise RepositoryIntegrityError("candidate revision digest is invalid")
        if artifact.artifact_id != revision.transition_artifact_id:
            raise RepositoryIntegrityError(
                "revision and transition artifact identities do not match"
            )
        if artifact.resulting_revision_id != revision.identity.revision_id:
            raise RepositoryIntegrityError(
                "transition artifact points at a different revision"
            )
        if artifact.resulting_revision_digest != revision.revision_digest:
            raise RepositoryIntegrityError(
                "transition artifact carries the wrong revision digest"
            )
        if artifact.execution_attempt_id != attempt_id:
            raise RepositoryIntegrityError(
                "transition artifact points at a different execution attempt"
            )
        if artifact.commit_decision.get("disposition") != "commit":
            raise RepositoryIntegrityError(
                "committed transition artifact lacks a commit decision"
            )
        if (
            artifact.commit_decision.get(
                "expected_branch_head_revision_id"
            )
            != expected_head_revision_id
        ):
            raise RepositoryIntegrityError(
                "transition commit decision carries the wrong expected head"
            )

        now = self._clock()
        identity = revision.identity
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            attempt_row = connection.execute(
                "SELECT status FROM resumption_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if (
                attempt_row is None
                or str(attempt_row["status"])
                != AttemptLifecycleStatus.RUNNING.value
            ):
                connection.rollback()
                raise AttemptNotRunningError(
                    f"attempt cannot commit semantic state: {attempt_id}"
                )

            head_row = connection.execute(
                """
                SELECT revision_id FROM resumption_branch_heads
                WHERE scope_id = ? AND objective_id = ? AND branch_id = ?
                """,
                (
                    identity.scope_id,
                    identity.objective_id,
                    identity.branch_id,
                ),
            ).fetchone()
            actual_head = str(head_row["revision_id"]) if head_row else None
            if actual_head != expected_head_revision_id:
                connection.rollback()
                raise StaleAnchorError(expected_head_revision_id, actual_head)

            for parent_id in revision.parent_revision_ids:
                parent = connection.execute(
                    "SELECT 1 FROM resumption_revisions WHERE revision_id = ?",
                    (parent_id,),
                ).fetchone()
                if parent is None:
                    connection.rollback()
                    raise RepositoryIntegrityError(
                        f"missing parent revision: {parent_id}"
                    )

            connection.execute(
                """
                INSERT INTO resumption_transition_artifacts (
                    artifact_id, payload_json, decision_flow_signature, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    artifact.artifact_id,
                    canonical_json(artifact.to_dict()),
                    artifact.decision_flow_signature,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO resumption_revisions (
                    revision_id, scope_id, objective_id, branch_id,
                    state_digest, revision_digest, state_json,
                    provenance_json, governance_json,
                    transition_artifact_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity.revision_id,
                    identity.scope_id,
                    identity.objective_id,
                    identity.branch_id,
                    identity.state_digest,
                    revision.revision_digest,
                    canonical_json(revision.state.to_dict()),
                    canonical_json(list(revision.provenance_references)),
                    canonical_json(list(revision.governance_references)),
                    revision.transition_artifact_id,
                    revision.created_at,
                ),
            )
            connection.executemany(
                """
                INSERT INTO resumption_revision_parents (
                    revision_id, parent_revision_id, parent_order
                ) VALUES (?, ?, ?)
                """,
                (
                    (identity.revision_id, parent_id, index)
                    for index, parent_id in enumerate(
                        revision.parent_revision_ids
                    )
                ),
            )
            if head_row is None:
                connection.execute(
                    """
                    INSERT INTO resumption_branch_heads (
                        scope_id, objective_id, branch_id,
                        revision_id, revision_digest, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        identity.scope_id,
                        identity.objective_id,
                        identity.branch_id,
                        identity.revision_id,
                        revision.revision_digest,
                        now,
                    ),
                )
            else:
                cursor = connection.execute(
                    """
                    UPDATE resumption_branch_heads
                    SET revision_id = ?, revision_digest = ?, updated_at = ?
                    WHERE scope_id = ? AND objective_id = ? AND branch_id = ?
                      AND revision_id = ?
                    """,
                    (
                        identity.revision_id,
                        revision.revision_digest,
                        now,
                        identity.scope_id,
                        identity.objective_id,
                        identity.branch_id,
                        expected_head_revision_id,
                    ),
                )
                if cursor.rowcount != 1:
                    connection.rollback()
                    refreshed = self._branch_head_id(
                        connection,
                        identity.scope_id,
                        identity.objective_id,
                        identity.branch_id,
                    )
                    raise StaleAnchorError(expected_head_revision_id, refreshed)

            attempt = _attempt_from_row(
                connection.execute(
                    "SELECT * FROM resumption_attempts WHERE attempt_id = ?",
                    (attempt_id,),
                ).fetchone()
            )
            transition_refs = tuple(
                dict.fromkeys(
                    (*attempt.transition_artifact_references, artifact.artifact_id)
                )
            )
            connection.execute(
                """
                UPDATE resumption_attempts
                SET latest_admitted_revision_id = ?,
                    transition_artifact_references_json = ?, updated_at = ?
                WHERE attempt_id = ? AND status = ?
                """,
                (
                    identity.revision_id,
                    canonical_json(list(transition_refs)),
                    now,
                    attempt_id,
                    AttemptLifecycleStatus.RUNNING.value,
                ),
            )
            self._append_event(
                connection,
                event_kind="semantic_revision_committed",
                aggregate_id=(
                    f"{identity.scope_id}/{identity.objective_id}/"
                    f"{identity.branch_id}"
                ),
                revision_id=identity.revision_id,
                attempt_id=attempt_id,
                payload={
                    "revision_digest": revision.revision_digest,
                    "transition_artifact_id": artifact.artifact_id,
                },
                created_at=now,
            )
            connection.commit()
        return revision

    def append_uncommitted_transition_artifact(
        self,
        artifact: TransitionArtifact,
        *,
        attempt_id: str,
    ) -> str:
        """Persist a rejected/stale/ambiguous transition without a revision."""

        if artifact.execution_attempt_id != attempt_id:
            raise RepositoryIntegrityError(
                "transition artifact points at a different execution attempt"
            )
        if artifact.commit_decision.get("disposition") == "commit":
            raise RepositoryIntegrityError(
                "uncommitted transition artifact claims a commit decision"
            )
        now = self._clock()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO resumption_transition_artifacts (
                    artifact_id, payload_json, decision_flow_signature, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    artifact.artifact_id,
                    canonical_json(artifact.to_dict()),
                    artifact.decision_flow_signature,
                    now,
                ),
            )
            row = connection.execute(
                "SELECT * FROM resumption_attempts WHERE attempt_id = ?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise KeyError(f"unknown execution attempt: {attempt_id}")
            attempt = _attempt_from_row(row)
            references = tuple(
                dict.fromkeys(
                    (*attempt.transition_artifact_references, artifact.artifact_id)
                )
            )
            connection.execute(
                """
                UPDATE resumption_attempts
                SET transition_artifact_references_json = ?, updated_at = ?
                WHERE attempt_id = ?
                """,
                (canonical_json(list(references)), now, attempt_id),
            )
            self._append_event(
                connection,
                event_kind="semantic_transition_not_committed",
                aggregate_id=artifact.artifact_id,
                attempt_id=attempt_id,
                payload={
                    "semantic_outcome": artifact.semantic_outcome.value,
                    "decision_flow_signature": artifact.decision_flow_signature,
                },
                created_at=now,
            )
            connection.commit()
        return self.transition_artifact_reference(artifact.artifact_id)

    def load_transition_artifact(self, artifact_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT payload_json FROM resumption_transition_artifacts
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            ).fetchone()
        return json.loads(str(row["payload_json"])) if row else None

    def load_transition_artifact_record(
        self,
        artifact_id: str,
    ) -> TransitionArtifact | None:
        payload = self.load_transition_artifact(artifact_id)
        if payload is None:
            return None
        artifact = TransitionArtifact.from_dict(payload)
        if artifact.artifact_id != artifact_id:
            raise RepositoryIntegrityError(
                f"transition artifact identity mismatch: {artifact_id}"
            )
        return artifact

    def verify_transition_replay(self, artifact_id: str) -> dict[str, Any]:
        """Reproduce and verify an externalized transition decision flow."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT payload_json, decision_flow_signature
                FROM resumption_transition_artifacts
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown transition artifact: {artifact_id}")

        artifact = TransitionArtifact.from_dict(
            json.loads(str(row["payload_json"]))
        )
        failures: list[str] = []
        if artifact.artifact_id != artifact_id:
            failures.append("artifact identity does not match its repository key")
        stored_signature = str(row["decision_flow_signature"])
        if stored_signature != artifact.decision_flow_signature:
            failures.append("artifact payload and signature column disagree")
        reproduced_signature = artifact.expected_decision_flow_signature
        if not artifact.verify_decision_flow_signature():
            failures.append("decision-flow signature could not be reproduced")

        if artifact.projection_artifact is not None:
            try:
                projection = ResumptionProjection.from_dict(
                    artifact.projection_artifact
                )
            except (KeyError, TypeError, ValueError) as exc:
                failures.append(f"projection artifact is invalid: {exc}")
            else:
                if not projection.verify():
                    failures.append("projection digest could not be reproduced")
                if projection.projection_digest != artifact.projection_digest:
                    failures.append(
                        "projection artifact and transition digest disagree"
                    )
        elif artifact.projection_digest is not None:
            failures.append("projection artifact required for replay is missing")

        if artifact.inlet_artifact is not None:
            if content_digest(artifact.inlet_artifact) != artifact.inlet_digest:
                failures.append("inlet digest could not be reproduced")
            if (
                artifact.inlet_artifact.get("inlet_id")
                != artifact.inlet_id
            ):
                failures.append(
                    "inlet artifact and transition identity disagree"
                )
        elif artifact.inlet_digest is not None:
            failures.append("inlet artifact required for replay is missing")

        if artifact.source_identity is not None:
            source = self.load_revision(
                artifact.source_identity.revision_id
            )
            if source is None:
                failures.append("source revision is missing")
            elif source.identity != artifact.source_identity:
                failures.append("source identity does not match its revision")
            elif source.revision_digest != artifact.source_revision_digest:
                failures.append("source revision digest does not match")

        resulting_revision = None
        if artifact.resulting_revision_id is not None:
            resulting_revision = self.load_revision(
                artifact.resulting_revision_id
            )
            if resulting_revision is None:
                failures.append("resulting revision is missing")
            elif (
                resulting_revision.revision_digest
                != artifact.resulting_revision_digest
            ):
                failures.append("resulting revision digest does not match")
            elif resulting_revision.transition_artifact_id != artifact_id:
                failures.append(
                    "resulting revision points at a different transition"
                )
        else:
            with self._connection() as connection:
                committed = connection.execute(
                    """
                    SELECT revision_id FROM resumption_revisions
                    WHERE transition_artifact_id = ?
                    """,
                    (artifact_id,),
                ).fetchone()
            if committed is not None:
                failures.append(
                    "non-committing artifact is referenced by a revision"
                )

        attempt = None
        if artifact.execution_attempt_id is not None:
            attempt = self.load_attempt(artifact.execution_attempt_id)
            if attempt is None:
                failures.append("execution attempt is missing")
            else:
                if artifact_id not in attempt.transition_artifact_references:
                    failures.append(
                        "execution attempt does not reference the transition"
                    )
                failures.extend(_attempt_lifecycle_failures(attempt))

        if artifact.commit_decision:
            disposition = artifact.commit_decision.get("disposition")
            if disposition == "commit":
                if artifact.resulting_revision_id is None:
                    failures.append(
                        "commit decision has no resulting revision"
                    )
                if (
                    artifact.commit_decision.get("resulting_revision_id")
                    != artifact.resulting_revision_id
                ):
                    failures.append(
                        "commit decision and resulting revision disagree"
                    )
                if (
                    artifact.commit_decision.get(
                        "resulting_revision_digest"
                    )
                    != artifact.resulting_revision_digest
                ):
                    failures.append(
                        "commit decision and resulting digest disagree"
                    )
            elif artifact.resulting_revision_id is not None:
                failures.append(
                    "non-commit decision carries a resulting revision"
                )

        if artifact.reduction_trace:
            replayed_frontier = _frontier_selections_from_trace(
                artifact.reduction_trace
            )
            if replayed_frontier != artifact.frontier_selections:
                failures.append(
                    "frontier selections do not match the reduction trace"
                )
            replayed_retrieval = _retrievals_from_trace(
                artifact.reduction_trace
            )
            if replayed_retrieval != artifact.retrieved_candidate_sets:
                failures.append(
                    "retrieved candidate ordering does not match the reduction trace"
                )

        proposal_ids = tuple(
            str(proposal.get("id"))
            for interaction in artifact.proposal_interactions
            for proposal in interaction.get("proposals", ())
            if isinstance(proposal, dict) and proposal.get("id") is not None
        )
        if proposal_ids and proposal_ids != artifact.proposal_references:
            failures.append(
                "proposal references do not match recorded interactions"
            )

        if artifact.execution_decisions and not any(
            item.get("kind") == "semantic_outcome"
            and item.get("outcome") == artifact.semantic_outcome.value
            for item in artifact.execution_decisions
        ):
            failures.append(
                "execution decisions do not record the semantic outcome"
            )

        has_llm_receipts = any(
            bool(item.get("llm_receipts"))
            for item in artifact.proposal_interactions
        )
        replay_mode = (
            "recorded_proposal_interactions"
            if has_llm_receipts
            else "deterministic_externalized_flow"
        )
        return {
            "artifact_id": artifact_id,
            "verified": not failures,
            "failures": failures,
            "stored_decision_flow_signature": stored_signature,
            "reproduced_decision_flow_signature": reproduced_signature,
            "replay_mode": replay_mode,
            "proposal_interaction_references": list(
                artifact.proposal_references
            ),
            "recorded_proposal_interaction_count": len(
                artifact.proposal_interactions
            ),
            "execution_attempt_id": artifact.execution_attempt_id,
            "attempt_lifecycle_records": (
                [record.to_dict() for record in attempt.lifecycle_records]
                if attempt is not None
                else []
            ),
            "frontier_selection_count": len(
                artifact.frontier_selections
            ),
            "retrieved_candidate_set_count": len(
                artifact.retrieved_candidate_sets
            ),
            "source_revision_id": (
                artifact.source_identity.revision_id
                if artifact.source_identity is not None
                else None
            ),
            "resulting_revision_id": (
                resulting_revision.identity.revision_id
                if resulting_revision is not None
                else artifact.resulting_revision_id
            ),
        }

    def transition_artifact_reference(self, artifact_id: str) -> str:
        return f"sqlite-resumption://transition/{artifact_id}"

    def revision_reference(self, revision_id: str) -> str:
        return f"sqlite-resumption://revision/{revision_id}"

    def parent_revision_ids(self, revision_id: str) -> tuple[str, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT parent_revision_id
                FROM resumption_revision_parents
                WHERE revision_id = ? ORDER BY parent_order
                """,
                (revision_id,),
            ).fetchall()
        return tuple(str(row["parent_revision_id"]) for row in rows)

    def child_revision_ids(self, revision_id: str) -> tuple[str, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT revision_id FROM resumption_revision_parents
                WHERE parent_revision_id = ? ORDER BY revision_id
                """,
                (revision_id,),
            ).fetchall()
        return tuple(str(row["revision_id"]) for row in rows)

    def path_to_roots(self, revision_id: str) -> tuple[str, ...]:
        """Return deterministic ancestor traversal including the target."""

        pending = [revision_id]
        visited: set[str] = set()
        ordered: list[str] = []
        while pending:
            current = pending.pop(0)
            if current in visited:
                continue
            visited.add(current)
            ordered.append(current)
            pending.extend(
                parent
                for parent in self.parent_revision_ids(current)
                if parent not in visited
            )
        return tuple(ordered)

    def branch_graph(self, scope_id: str, objective_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            revisions = connection.execute(
                """
                SELECT revision_id, scope_id, branch_id, revision_digest
                FROM resumption_revisions
                WHERE scope_id = ? AND objective_id = ?
                ORDER BY created_at, revision_id
                """,
                (scope_id, objective_id),
            ).fetchall()
            heads = connection.execute(
                """
                SELECT scope_id, branch_id, revision_id
                FROM resumption_branch_heads
                WHERE scope_id = ? AND objective_id = ?
                ORDER BY branch_id
                """,
                (scope_id, objective_id),
            ).fetchall()
        return {
            "scope_id": scope_id,
            "objective_id": objective_id,
            "revisions": [
                {
                    "revision_id": str(row["revision_id"]),
                    "scope_id": str(row["scope_id"]),
                    "branch_id": str(row["branch_id"]),
                    "revision_digest": str(row["revision_digest"]),
                    "parent_revision_ids": list(
                        self.parent_revision_ids(str(row["revision_id"]))
                    ),
                }
                for row in revisions
            ],
            "heads": [dict(row) for row in heads],
        }

    def list_events(self) -> tuple[dict[str, Any], ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM resumption_events ORDER BY event_id"
            ).fetchall()
        return tuple(
            {
                "event_id": int(row["event_id"]),
                "event_kind": str(row["event_kind"]),
                "aggregate_id": str(row["aggregate_id"]),
                "revision_id": row["revision_id"],
                "attempt_id": row["attempt_id"],
                "payload": json.loads(str(row["payload_json"])),
                "created_at": str(row["created_at"]),
            }
            for row in rows
        )

    def verify_integrity(self) -> tuple[str, ...]:
        failures: list[str] = []
        with self._connection() as connection:
            revision_ids = [
                str(row["revision_id"])
                for row in connection.execute(
                    "SELECT revision_id FROM resumption_revisions"
                ).fetchall()
            ]
            head_rows = connection.execute(
                "SELECT * FROM resumption_branch_heads"
            ).fetchall()
            artifact_ids = [
                str(row["artifact_id"])
                for row in connection.execute(
                    "SELECT artifact_id FROM resumption_transition_artifacts"
                ).fetchall()
            ]
            normalized_rows = connection.execute(
                "SELECT * FROM resumption_normalized_requests"
            ).fetchall()
        for revision_id in revision_ids:
            try:
                self.load_revision(revision_id)
            except RepositoryIntegrityError as exc:
                failures.append(str(exc))
        for row in head_rows:
            revision = self.load_revision(str(row["revision_id"]))
            if revision is None:
                failures.append(f"branch head has missing revision: {dict(row)}")
                continue
            if revision.revision_digest != str(row["revision_digest"]):
                failures.append(
                    f"branch head digest mismatch: {revision.identity.revision_id}"
                )
        for artifact_id in artifact_ids:
            try:
                replay = self.verify_transition_replay(artifact_id)
            except (KeyError, RepositoryIntegrityError, ValueError) as exc:
                failures.append(str(exc))
                continue
            failures.extend(
                f"transition {artifact_id}: {failure}"
                for failure in replay["failures"]
            )
        for row in normalized_rows:
            try:
                binding = _normalized_request_from_row(row)
            except (KeyError, TypeError, ValueError) as exc:
                failures.append(f"invalid normalized request binding: {exc}")
                continue
            expected_digest = content_digest(
                {
                    "operation": binding.operation,
                    "request": binding.request_payload,
                }
            )
            if binding.request_digest != expected_digest:
                failures.append(
                    "normalized request digest mismatch: "
                    f"{binding.normalized_request_id}"
                )
            attempt = self.load_attempt(binding.attempt_id)
            if binding.result is not None:
                if attempt is None:
                    failures.append(
                        "normalized request result has no attempt: "
                        f"{binding.normalized_request_id}"
                    )
                elif (
                    binding.result.execution_attempt_id
                    != binding.attempt_id
                ):
                    failures.append(
                        "normalized request result attempt mismatch: "
                        f"{binding.normalized_request_id}"
                    )
        return tuple(failures)

    @staticmethod
    def _add_column_if_missing(
        connection: sqlite3.Connection,
        *,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            )

    @staticmethod
    def _branch_head_id(
        connection: sqlite3.Connection,
        scope_id: str,
        objective_id: str,
        branch_id: str,
    ) -> str | None:
        row = connection.execute(
            """
            SELECT revision_id FROM resumption_branch_heads
            WHERE scope_id = ? AND objective_id = ? AND branch_id = ?
            """,
            (scope_id, objective_id, branch_id),
        ).fetchone()
        return str(row["revision_id"]) if row else None

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        *,
        event_kind: str,
        aggregate_id: str,
        payload: dict[str, Any],
        created_at: str,
        revision_id: str | None = None,
        attempt_id: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO resumption_events (
                event_kind, aggregate_id, revision_id,
                attempt_id, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_kind,
                aggregate_id,
                revision_id,
                attempt_id,
                canonical_json(payload),
                created_at,
            ),
        )


def _attempt_values(attempt: AttemptRecord) -> tuple[Any, ...]:
    return (
        attempt.attempt_id,
        attempt.causal_anchor,
        attempt.operation,
        attempt.initial_branch_head_revision_id,
        attempt.initial_branch_head_digest,
        canonical_json(dict(attempt.execution_policy)),
        attempt.status.value,
        attempt.latest_admitted_revision_id,
        canonical_json(list(attempt.proposal_references)),
        canonical_json(list(attempt.receipt_references)),
        canonical_json(list(attempt.transition_artifact_references)),
        attempt.interruption_cause,
        canonical_json(dict(attempt.interruption_correlation)),
        attempt.operational_error,
        canonical_json(
            [record.to_dict() for record in attempt.lifecycle_records]
        ),
        canonical_json(dict(attempt.performance_measurements)),
        attempt.created_at,
        attempt.updated_at,
    )


def _same_attempt_intent(left: AttemptRecord, right: AttemptRecord) -> bool:
    return (
        left.attempt_id == right.attempt_id
        and left.causal_anchor == right.causal_anchor
        and left.operation == right.operation
        and left.initial_branch_head_revision_id
        == right.initial_branch_head_revision_id
        and left.initial_branch_head_digest == right.initial_branch_head_digest
        and dict(left.execution_policy) == dict(right.execution_policy)
        and left.latest_admitted_revision_id
        == right.latest_admitted_revision_id
    )


def _normalized_request_from_row(
    row: sqlite3.Row,
) -> NormalizedRequestBinding:
    raw_result = row["result_json"]
    return NormalizedRequestBinding(
        normalized_request_id=str(row["normalized_request_id"]),
        request_digest=str(row["request_digest"]),
        operation=str(row["operation"]),
        request_payload=json.loads(str(row["request_json"])),
        attempt_id=str(row["attempt_id"]),
        result=(
            ResumptionResult.from_dict(json.loads(str(raw_result)))
            if raw_result is not None
            else None
        ),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _attempt_from_row(row: sqlite3.Row) -> AttemptRecord:
    return AttemptRecord(
        attempt_id=str(row["attempt_id"]),
        causal_anchor=str(row["causal_anchor"]),
        operation=str(row["operation"]),
        initial_branch_head_revision_id=row[
            "initial_branch_head_revision_id"
        ],
        initial_branch_head_digest=row["initial_branch_head_digest"],
        execution_policy=json.loads(str(row["execution_policy_json"])),
        status=AttemptLifecycleStatus(str(row["status"])),
        latest_admitted_revision_id=row["latest_admitted_revision_id"],
        proposal_references=tuple(
            json.loads(str(row["proposal_references_json"]))
        ),
        receipt_references=tuple(
            json.loads(str(row["receipt_references_json"]))
        ),
        transition_artifact_references=tuple(
            json.loads(str(row["transition_artifact_references_json"]))
        ),
        interruption_cause=row["interruption_cause"],
        interruption_correlation=json.loads(
            str(row["interruption_correlation_json"])
        ),
        operational_error=row["operational_error"],
        lifecycle_records=tuple(
            AttemptLifecycleRecord.from_dict(dict(item))
            for item in json.loads(str(row["lifecycle_records_json"]))
        ),
        performance_measurements=json.loads(
            str(row["performance_measurements_json"])
        ),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _apply_attempt_update(
    current: AttemptRecord,
    update: AttemptUpdate,
    *,
    now: str,
) -> AttemptRecord:
    return replace(
        current,
        status=update.status,
        latest_admitted_revision_id=(
            update.latest_admitted_revision_id
            if update.latest_admitted_revision_id is not None
            else current.latest_admitted_revision_id
        ),
        proposal_references=(
            update.proposal_references
            if update.proposal_references
            else current.proposal_references
        ),
        receipt_references=(
            update.receipt_references
            if update.receipt_references
            else current.receipt_references
        ),
        transition_artifact_references=(
            update.transition_artifact_references
            if update.transition_artifact_references
            else current.transition_artifact_references
        ),
        interruption_cause=(
            update.interruption_cause
            if update.interruption_cause is not None
            else current.interruption_cause
        ),
        interruption_correlation=(
            dict(update.interruption_correlation)
            if update.interruption_correlation
            else current.interruption_correlation
        ),
        operational_error=(
            update.operational_error
            if update.operational_error is not None
            else current.operational_error
        ),
        lifecycle_records=(
            *current.lifecycle_records,
            AttemptLifecycleRecord(
                status=update.status,
                prior_status=current.status,
                recorded_at=now,
                cause=(
                    update.interruption_cause
                    if update.interruption_cause is not None
                    else update.operational_error
                ),
                correlation=dict(update.interruption_correlation),
            ),
        ),
        performance_measurements=merge_performance_measurements(
            current.performance_measurements,
            update.performance_measurements,
        ),
        updated_at=now,
    )


def _revision_from_rows(
    row: sqlite3.Row,
    parent_rows: Iterable[sqlite3.Row],
) -> Revision:
    state = SemanticState.from_dict(json.loads(str(row["state_json"])))
    identity = ResumptionIdentity(
        scope_id=str(row["scope_id"]),
        objective_id=str(row["objective_id"]),
        branch_id=str(row["branch_id"]),
        revision_id=str(row["revision_id"]),
        state_digest=str(row["state_digest"]),
    )
    return Revision(
        identity=identity,
        parent_revision_ids=tuple(
            str(parent["parent_revision_id"]) for parent in parent_rows
        ),
        state=state,
        provenance_references=tuple(
            json.loads(str(row["provenance_json"]))
        ),
        governance_references=tuple(
            json.loads(str(row["governance_json"]))
        ),
        transition_artifact_id=str(row["transition_artifact_id"]),
        revision_digest=str(row["revision_digest"]),
        created_at=str(row["created_at"]),
    )


def _attempt_lifecycle_failures(attempt: AttemptRecord) -> list[str]:
    records = attempt.lifecycle_records
    if not records:
        return ["execution attempt lifecycle records are missing"]
    failures: list[str] = []
    if (
        records[0].status is not AttemptLifecycleStatus.PREPARED
        or records[0].prior_status is not None
    ):
        failures.append("execution attempt lifecycle does not begin prepared")
    for prior, current in zip(records, records[1:], strict=False):
        if current.prior_status is not prior.status:
            failures.append(
                "execution attempt lifecycle has a discontinuous transition"
            )
            break
    if records[-1].status is not attempt.status:
        failures.append(
            "execution attempt lifecycle does not end at its current status"
        )
    if attempt.status is AttemptLifecycleStatus.INTERRUPTED:
        final = records[-1]
        if final.cause != attempt.interruption_cause:
            failures.append(
                "interruption lifecycle cause disagrees with the attempt"
            )
        if dict(final.correlation) != dict(
            attempt.interruption_correlation
        ):
            failures.append(
                "interruption lifecycle correlation disagrees with the attempt"
            )
    return failures


def _frontier_selections_from_trace(
    trace: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "sequence": record["sequence"],
            "selected_node_id": record.get("node_id"),
            "proposal_id": record.get("payload", {}).get("proposal_id", ""),
            "candidate_order": list(
                record.get("payload", {}).get("candidate_order", ())
            ),
        }
        for record in trace
        if record.get("kind") == "frontier_selection"
    )


def _retrievals_from_trace(
    trace: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    for record in trace:
        kind = str(record.get("kind", ""))
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if kind != "learning_context" and "retriev" not in kind:
            continue
        ordered = next(
            (
                payload[key]
                for key in (
                    "artifact_ids",
                    "ordered_candidate_ids",
                    "candidate_ids",
                    "candidate_order",
                )
                if isinstance(payload.get(key), (list, tuple))
            ),
            (),
        )
        records.append(
            {
                "sequence": record["sequence"],
                "kind": kind,
                "ordered_candidate_ids": [str(item) for item in ordered],
            }
        )
    return tuple(records)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "AttemptNotRunningError",
    "RepositoryIntegrityError",
    "ResumptionRepositoryError",
    "SQLiteResumptionRepository",
    "StaleAnchorError",
]
