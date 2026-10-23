"""SQLite adapter for non-semantic conversation activity records."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from collections.abc import Iterator
from typing import Any

from realized_core_conversation.schemas import (
    ConversationActivityRecord,
    ConversationReceipt,
    ConversationRecordKind,
    ContributionRecord,
    NormalizedRequestRecord,
    StructuredResultRecord,
    conversation_record_from_dict,
)


class ConversationJournalConflict(ValueError):
    """Raised when one stable activity identity is reused for other content."""


class SQLiteConversationActivityJournal:
    """Durable, idempotent journal distinct from semantic revision tables."""

    def __init__(self, sqlite_path: Path) -> None:
        self.sqlite_path = Path(sqlite_path).expanduser().resolve()
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def put(
        self,
        record: ConversationActivityRecord,
    ) -> ConversationActivityRecord:
        payload = record.to_dict()
        encoded = _canonical_json(payload)
        contribution_id = _contribution_id(record)
        idempotency_key = (
            record.idempotency_key
            if isinstance(record, ContributionRecord)
            else ""
        )
        normalized_request_id = _normalized_request_id(record)
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversation_activity_records (
                        record_kind,
                        record_id,
                        contribution_id,
                        idempotency_key,
                        normalized_request_id,
                        payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.KIND.value,
                        record.record_id,
                        contribution_id,
                        idempotency_key,
                        normalized_request_id,
                        encoded,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            existing = self._conflicting_record(record)
            if existing is not None and _canonical_json(existing.to_dict()) == encoded:
                return existing
            raise ConversationJournalConflict(
                "Conversation activity identity already names different content: "
                f"{record.KIND.value}/{record.record_id}"
            ) from exc
        return record

    def get(
        self,
        record_kind: ConversationRecordKind,
        record_id: str,
    ) -> ConversationActivityRecord | None:
        row = self._one(
            """
            SELECT payload_json
            FROM conversation_activity_records
            WHERE record_kind = ? AND record_id = ?
            """,
            (record_kind.value, str(record_id)),
        )
        return _restore(row)

    def find_contribution(
        self,
        *,
        idempotency_key: str,
    ) -> ContributionRecord | None:
        row = self._one(
            """
            SELECT payload_json
            FROM conversation_activity_records
            WHERE record_kind = ? AND idempotency_key = ?
            """,
            (
                ConversationRecordKind.CONTRIBUTION.value,
                str(idempotency_key),
            ),
        )
        restored = _restore(row)
        return restored if isinstance(restored, ContributionRecord) else None

    def find_normalized_request(
        self,
        normalized_request_id: str,
    ) -> NormalizedRequestRecord | None:
        restored = self.get(
            ConversationRecordKind.NORMALIZED_REQUEST,
            normalized_request_id,
        )
        return (
            restored
            if isinstance(restored, NormalizedRequestRecord)
            else None
        )

    def find_result(
        self,
        normalized_request_id: str,
    ) -> StructuredResultRecord | None:
        row = self._one(
            """
            SELECT payload_json
            FROM conversation_activity_records
            WHERE record_kind = ? AND normalized_request_id = ?
            """,
            (
                ConversationRecordKind.STRUCTURED_RESULT.value,
                str(normalized_request_id),
            ),
        )
        restored = _restore(row)
        return (
            restored
            if isinstance(restored, StructuredResultRecord)
            else None
        )

    def list_for_contribution(
        self,
        contribution_id: str,
    ) -> tuple[ConversationActivityRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM conversation_activity_records
                WHERE contribution_id = ?
                ORDER BY sequence_id
                """,
                (str(contribution_id),),
            ).fetchall()
        return tuple(
            record
            for row in rows
            if (record := _restore(row)) is not None
        )

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversation_activity_records (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_kind TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    contribution_id TEXT NOT NULL DEFAULT '',
                    idempotency_key TEXT NOT NULL DEFAULT '',
                    normalized_request_id TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL,
                    UNIQUE (record_kind, record_id)
                );

                CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_conversation_contribution_idempotency
                ON conversation_activity_records (idempotency_key)
                WHERE record_kind = 'contribution';

                CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_conversation_normalized_request
                ON conversation_activity_records (normalized_request_id)
                WHERE record_kind = 'normalized_request';

                CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_conversation_result_request
                ON conversation_activity_records (normalized_request_id)
                WHERE record_kind = 'structured_result';

                CREATE INDEX IF NOT EXISTS
                    ix_conversation_activity_contribution
                ON conversation_activity_records (
                    contribution_id,
                    sequence_id
                );
                """
            )

    def _conflicting_record(
        self,
        record: ConversationActivityRecord,
    ) -> ConversationActivityRecord | None:
        existing = self.get(record.KIND, record.record_id)
        if existing is not None:
            return existing
        if isinstance(record, ContributionRecord):
            return self.find_contribution(
                idempotency_key=record.idempotency_key
            )
        if isinstance(record, NormalizedRequestRecord):
            return self.find_normalized_request(record.normalized_request_id)
        if isinstance(record, StructuredResultRecord):
            return self.find_result(record.normalized_request_id)
        return None

    def _one(
        self,
        sql: str,
        parameters: tuple[str, ...],
    ) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(sql, parameters).fetchone()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.sqlite_path)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection
        finally:
            connection.close()


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _restore(row: sqlite3.Row | None) -> ConversationActivityRecord | None:
    if row is None:
        return None
    return conversation_record_from_dict(json.loads(str(row["payload_json"])))


def _contribution_id(record: ConversationActivityRecord) -> str:
    if isinstance(record, ConversationReceipt):
        return str(record.correlation_ids.get("contribution_id", ""))
    return str(getattr(record, "contribution_id", ""))


def _normalized_request_id(record: ConversationActivityRecord) -> str:
    return str(getattr(record, "normalized_request_id", ""))


__all__ = [
    "ConversationJournalConflict",
    "SQLiteConversationActivityJournal",
]
