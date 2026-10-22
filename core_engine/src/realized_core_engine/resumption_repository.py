"""Plain-SQLite persistence for governed resumption.

Immutable revisions and transition artifacts are canonical.  Branch heads are
updated with compare-and-swap, while execution attempts live in a separate
journal so operational interruption cannot mutate semantic state.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_core_runtime import (
    AttemptLifecycleStatus,
    AttemptRecord,
    AttemptUpdate,
)

from realized_core_engine.resumption_contracts import (
    ResumptionIdentity,
    Revision,
    SemanticState,
    TransitionArtifact,
    canonical_json,
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
    def _connection(self) -> Iterable[sqlite3.Connection]:
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
                    execution_policy_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latest_admitted_revision_id TEXT,
                    proposal_references_json TEXT NOT NULL,
                    receipt_references_json TEXT NOT NULL,
                    transition_artifact_references_json TEXT NOT NULL,
                    interruption_cause TEXT,
                    interruption_correlation_json TEXT NOT NULL,
                    operational_error TEXT,
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

    # Execution-attempt journal -------------------------------------------------

    def prepare_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        if attempt.status is not AttemptLifecycleStatus.PREPARED:
            raise ValueError("only prepared attempts can be appended")
        now = self._clock()
        durable = replace(
            attempt,
            created_at=attempt.created_at or now,
            updated_at=now,
        )
        try:
            with self._connection() as connection:
                connection.execute(
                    """
                    INSERT INTO resumption_attempts (
                        attempt_id, causal_anchor, operation,
                        execution_policy_json, status,
                        latest_admitted_revision_id,
                        proposal_references_json, receipt_references_json,
                        transition_artifact_references_json,
                        interruption_cause, interruption_correlation_json,
                        operational_error, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    operational_error = ?, updated_at = ?
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

    def branch_graph(self, objective_id: str) -> dict[str, Any]:
        with self._connection() as connection:
            revisions = connection.execute(
                """
                SELECT revision_id, scope_id, branch_id, revision_digest
                FROM resumption_revisions
                WHERE objective_id = ? ORDER BY created_at, revision_id
                """,
                (objective_id,),
            ).fetchall()
            heads = connection.execute(
                """
                SELECT scope_id, branch_id, revision_id
                FROM resumption_branch_heads
                WHERE objective_id = ? ORDER BY scope_id, branch_id
                """,
                (objective_id,),
            ).fetchall()
        return {
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
        return tuple(failures)

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
        canonical_json(dict(attempt.execution_policy)),
        attempt.status.value,
        attempt.latest_admitted_revision_id,
        canonical_json(list(attempt.proposal_references)),
        canonical_json(list(attempt.receipt_references)),
        canonical_json(list(attempt.transition_artifact_references)),
        attempt.interruption_cause,
        canonical_json(dict(attempt.interruption_correlation)),
        attempt.operational_error,
        attempt.created_at,
        attempt.updated_at,
    )


def _attempt_from_row(row: sqlite3.Row) -> AttemptRecord:
    return AttemptRecord(
        attempt_id=str(row["attempt_id"]),
        causal_anchor=str(row["causal_anchor"]),
        operation=str(row["operation"]),
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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "AttemptNotRunningError",
    "RepositoryIntegrityError",
    "ResumptionRepositoryError",
    "SQLiteResumptionRepository",
    "StaleAnchorError",
]
