from __future__ import annotations

import unittest

from realized_core_conversation import (
    CONVERSATION_RECORD_SCHEMA_VERSION,
    ConversationActivityStatus,
    ConversationReceipt,
    ConversationRecordKind,
    ConversationSchemaError,
    ContributionRecord,
    NormalizedRequestRecord,
    PlanningProposalRecord,
    RecoveryDecisionRecord,
    RenderingRecord,
    StructuredResultRecord,
    conversation_record_from_dict,
)


class ConversationSchemaTests(unittest.TestCase):
    def test_every_activity_record_round_trips_with_discriminator(self) -> None:
        records = (
            ContributionRecord(
                contribution_id="contribution-1",
                session_id="session-1",
                idempotency_key="delivery-1",
                text="Continue the plan.",
                scope_id="scope-1",
                received_at="2026-10-23T00:00:00+00:00",
                selected_binding={"revision_id": "revision-1"},
                provenance={"transport": "test"},
                correlation={"message_id": "message-1"},
            ),
            PlanningProposalRecord(
                planning_attempt_id="planning-1",
                contribution_id="contribution-1",
                status=ConversationActivityStatus.SUCCEEDED,
                planning_context_digest="context-digest",
                proposal={"schema_version": "1", "operation": "continue"},
                created_at="2026-10-23T00:00:01+00:00",
                proposal_schema_version="1",
                prompt_version="1",
                provider_receipt={"response_id": "provider-1"},
            ),
            NormalizedRequestRecord(
                normalized_request_id="request-1",
                contribution_id="contribution-1",
                planning_attempt_id="planning-1",
                operation="continue",
                request_payload={"operation": "continue"},
                request_digest="request-digest",
                causal_anchor={"revision_id": "revision-1"},
                created_at="2026-10-23T00:00:02+00:00",
            ),
            StructuredResultRecord(
                result_id="result-1",
                normalized_request_id="request-1",
                contribution_id="contribution-1",
                execution_attempt_id="attempt-1",
                result_payload={"semantic_outcome": "completed"},
                recorded_at="2026-10-23T00:00:03+00:00",
                resulting_binding={"revision_id": "revision-2"},
            ),
            RenderingRecord(
                rendering_attempt_id="rendering-1",
                contribution_id="contribution-1",
                result_id="result-1",
                status=ConversationActivityStatus.SUCCEEDED,
                rendering_request={"result_id": "result-1"},
                started_at="2026-10-23T00:00:04+00:00",
                rendering_schema_version="1",
                prompt_version="1",
                presentation="The plan is complete.",
                completed_at="2026-10-23T00:00:05+00:00",
                delivery_status=ConversationActivityStatus.DELIVERED,
            ),
            ConversationReceipt(
                receipt_id="receipt-1",
                stage="engine_submission",
                status=ConversationActivityStatus.SUBMITTED,
                correlation_ids={
                    "contribution_id": "contribution-1",
                    "normalized_request_id": "request-1",
                },
                payload={"execution_attempt_id": "attempt-1"},
                recorded_at="2026-10-23T00:00:06+00:00",
            ),
            RecoveryDecisionRecord(
                recovery_decision_id="recovery-1",
                contribution_id="contribution-1",
                stage="submitted",
                action="recover_result",
                reason="The semantic result already exists.",
                linked_record_ids={
                    "normalized_request_id": "request-1",
                    "result_id": "result-1",
                },
                recorded_at="2026-10-23T00:00:07+00:00",
            ),
        )

        for record in records:
            with self.subTest(record_kind=record.KIND.value):
                payload = record.to_dict()
                self.assertEqual(
                    CONVERSATION_RECORD_SCHEMA_VERSION,
                    payload["schema_version"],
                )
                self.assertEqual(record.KIND.value, payload["record_kind"])
                self.assertEqual(record.record_id, payload["record_id"])
                self.assertEqual(record, conversation_record_from_dict(payload))

    def test_future_schema_version_is_not_silently_accepted(self) -> None:
        payload = ContributionRecord(
            contribution_id="contribution-1",
            session_id="session-1",
            idempotency_key="delivery-1",
            text="Continue.",
            scope_id="scope-1",
            received_at="2026-10-23T00:00:00+00:00",
        ).to_dict()
        payload["schema_version"] = CONVERSATION_RECORD_SCHEMA_VERSION + 1

        with self.assertRaisesRegex(
            ConversationSchemaError,
            "Unsupported conversation record schema version",
        ):
            conversation_record_from_dict(payload)

    def test_unknown_record_kind_is_not_guessed(self) -> None:
        with self.assertRaisesRegex(
            ConversationSchemaError,
            "Unsupported conversation record kind",
        ):
            conversation_record_from_dict(
                {
                    "schema_version": CONVERSATION_RECORD_SCHEMA_VERSION,
                    "record_kind": "unknown",
                }
            )

    def test_record_kind_vocabulary_is_complete(self) -> None:
        self.assertEqual(
            {
                "contribution",
                "proposal",
                "normalized_request",
                "structured_result",
                "rendering",
                "receipt",
                "recovery_decision",
            },
            {item.value for item in ConversationRecordKind},
        )


if __name__ == "__main__":
    unittest.main()
