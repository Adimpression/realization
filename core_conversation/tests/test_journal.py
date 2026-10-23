from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from realized_core_conversation import (
    ConversationActivityStatus,
    ConversationJournalConflict,
    ConversationRecordKind,
    ContributionRecord,
    NormalizedRequestRecord,
    SQLiteConversationActivityJournal,
    StructuredResultRecord,
    canonical_payload_digest,
    stable_contribution_id,
    stable_normalized_request_id,
    stable_planning_attempt_id,
    stable_rendering_attempt_id,
    stable_result_id,
)


class ConversationIdentityTests(unittest.TestCase):
    def test_canonical_request_identity_ignores_object_key_order(self) -> None:
        first = {
            "operation": "continue",
            "anchor": {"revision_id": "revision-1", "branch_id": "main"},
        }
        second = {
            "anchor": {"branch_id": "main", "revision_id": "revision-1"},
            "operation": "continue",
        }

        self.assertEqual(
            canonical_payload_digest(first),
            canonical_payload_digest(second),
        )
        self.assertEqual(
            stable_normalized_request_id(first),
            stable_normalized_request_id(second),
        )

    def test_each_stage_identity_is_stable_and_names_its_stage(self) -> None:
        contribution_id = stable_contribution_id("session-1", "delivery-1")
        planning_id = stable_planning_attempt_id(
            contribution_id,
            "planning-attempt-1",
        )
        request_id = stable_normalized_request_id(
            {"operation": "start", "contribution_id": contribution_id}
        )
        result_id = stable_result_id(request_id, "attempt-1")
        rendering_id = stable_rendering_attempt_id(
            result_id,
            "rendering-attempt-1",
        )

        self.assertTrue(contribution_id.startswith("contribution_"))
        self.assertTrue(planning_id.startswith("planning_"))
        self.assertTrue(request_id.startswith("request_"))
        self.assertTrue(result_id.startswith("result_"))
        self.assertTrue(rendering_id.startswith("rendering_"))
        self.assertEqual(
            contribution_id,
            stable_contribution_id("session-1", "delivery-1"),
        )


class SQLiteConversationActivityJournalTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.sqlite_path = Path(temporary.name) / "conversation.sqlite3"
        self.journal = SQLiteConversationActivityJournal(self.sqlite_path)
        self.contribution = ContributionRecord(
            contribution_id=stable_contribution_id(
                "session-1",
                "delivery-1",
            ),
            session_id="session-1",
            idempotency_key="delivery-1",
            text="Continue the plan.",
            scope_id="scope-1",
            received_at="2026-10-23T00:00:00+00:00",
        )

    def test_records_survive_reopen_and_retain_stage_order(self) -> None:
        request = self._request()
        result = self._result(request)
        for record in (self.contribution, request, result):
            self.assertEqual(record, self.journal.put(record))

        reopened = SQLiteConversationActivityJournal(self.sqlite_path)

        self.assertEqual(
            self.contribution,
            reopened.find_contribution(idempotency_key="delivery-1"),
        )
        self.assertEqual(request, reopened.find_normalized_request(request.record_id))
        self.assertEqual(result, reopened.find_result(request.record_id))
        self.assertEqual(
            (self.contribution, request, result),
            reopened.list_for_contribution(self.contribution.record_id),
        )

    def test_repeating_identical_record_is_idempotent(self) -> None:
        self.journal.put(self.contribution)

        self.assertEqual(
            self.contribution,
            self.journal.put(self.contribution),
        )

    def test_stable_identity_cannot_be_reused_for_other_content(self) -> None:
        self.journal.put(self.contribution)
        changed = ContributionRecord(
            contribution_id=self.contribution.contribution_id,
            session_id=self.contribution.session_id,
            idempotency_key=self.contribution.idempotency_key,
            text="Different content.",
            scope_id=self.contribution.scope_id,
            received_at=self.contribution.received_at,
        )

        with self.assertRaisesRegex(
            ConversationJournalConflict,
            "already names different content",
        ):
            self.journal.put(changed)

    def test_idempotency_key_cannot_name_two_contributions(self) -> None:
        self.journal.put(self.contribution)
        duplicate_delivery = ContributionRecord(
            contribution_id="contribution-other",
            session_id="session-1",
            idempotency_key=self.contribution.idempotency_key,
            text=self.contribution.text,
            scope_id=self.contribution.scope_id,
            received_at=self.contribution.received_at,
        )

        with self.assertRaises(ConversationJournalConflict):
            self.journal.put(duplicate_delivery)

    def test_journal_table_is_namespaced_from_semantic_tables(self) -> None:
        self.journal.put(self.contribution)
        with closing(sqlite3.connect(self.sqlite_path)) as connection:
            tables = {
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }

        self.assertIn("conversation_activity_records", tables)
        self.assertNotIn("resumption_revisions", tables)

    def test_get_uses_record_kind_and_identity(self) -> None:
        self.journal.put(self.contribution)

        self.assertEqual(
            self.contribution,
            self.journal.get(
                ConversationRecordKind.CONTRIBUTION,
                self.contribution.record_id,
            ),
        )
        self.assertIsNone(
            self.journal.get(
                ConversationRecordKind.RENDERING,
                self.contribution.record_id,
            )
        )

    def _request(self) -> NormalizedRequestRecord:
        payload = {
            "operation": "continue",
            "causal_anchor": {"revision_id": "revision-1"},
        }
        request_id = stable_normalized_request_id(payload)
        return NormalizedRequestRecord(
            normalized_request_id=request_id,
            contribution_id=self.contribution.record_id,
            planning_attempt_id=stable_planning_attempt_id(
                self.contribution.record_id,
                "planning-1",
            ),
            operation="continue",
            request_payload=payload,
            request_digest=canonical_payload_digest(payload),
            causal_anchor={"revision_id": "revision-1"},
            created_at="2026-10-23T00:00:01+00:00",
            submission_status=ConversationActivityStatus.SUBMITTED,
        )

    def _result(
        self,
        request: NormalizedRequestRecord,
    ) -> StructuredResultRecord:
        return StructuredResultRecord(
            result_id=stable_result_id(request.record_id, "attempt-1"),
            normalized_request_id=request.record_id,
            contribution_id=self.contribution.record_id,
            execution_attempt_id="attempt-1",
            result_payload={"semantic_outcome": "completed"},
            recorded_at="2026-10-23T00:00:02+00:00",
            resulting_binding={"revision_id": "revision-2"},
        )


if __name__ == "__main__":
    unittest.main()
