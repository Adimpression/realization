from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import unittest
from unittest.mock import patch

from realized_core_governance import approval


@dataclass
class _ArtifactView:
    content: Any


def _record(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "intent": "Approve governed execution.",
        "approval_class": "operator_approved",
        "subject_titles": ["Governed Skill"],
        "subject_kinds": [],
        "approved_authorities": [],
        "approved_risk_tiers": [],
        "issued_by": "operator://reviewer",
        "rationale": "Reviewed.",
        "status": "approved",
        "valid_from": "",
        "valid_until": "",
    }
    value.update(overrides)
    return value


class _FixedDateTime(datetime):
    @classmethod
    def now(cls, tz: Any = None) -> datetime:
        moment = cls(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)
        return moment if tz is not None else moment.replace(tzinfo=None)


class GovernanceApprovalTests(unittest.TestCase):
    def test_status_vocabulary_and_normalization_are_exact(self) -> None:
        self.assertEqual(
            ("approved", "revoked", "expired"),
            approval.APPROVAL_RECORD_STATUSES,
        )
        cases = (
            (" APPROVED\n", {}, "approved"),
            ("\x00REVOKED\x7f", {}, "revoked"),
            ("expired", {}, "expired"),
            (0, {}, "approved"),
            ("unknown", {"default": "custom"}, "custom"),
        )
        for value, kwargs, expected in cases:
            with self.subTest(value=value, kwargs=kwargs):
                self.assertEqual(
                    expected,
                    approval.normalize_approval_record_status(value, **kwargs),
                )

    def test_payload_normalization_preserves_all_fields_and_ordering(self) -> None:
        result = approval.skill_approval_from_payload(
            {
                "schema": " bssc_skill.v2 ",
                "kind": " APPROVAL ",
                "approval": {
                    "intent": " Approve\nexecution. ",
                    "approval_class": " OPERATOR_APPROVED ",
                    "subject_titles": " Governed\x00Skill ",
                    "subject_kinds": ["ABILITY", "unknown"],
                    "approved_authorities": [
                        "Execute",
                        "read",
                        "execute",
                        "unknown",
                    ],
                    "approved_risk_tiers": [
                        "TIER3_SENSITIVE",
                        "unknown",
                    ],
                    "issued_by": " operator://reviewer ",
                    "rationale": " Reviewed\ncarefully. ",
                    "status": " APPROVED ",
                    "valid_from": " 2026-01-01T00:00:00Z ",
                    "valid_until": " 2027-01-01T00:00:00Z ",
                },
            }
        )
        self.assertEqual(
            {
                "intent": "Approve execution.",
                "approval_class": "operator_approved",
                "subject_titles": ["Governed Skill"],
                "subject_kinds": ["ability", "knowledge"],
                "approved_authorities": ["execute", "read"],
                "approved_risk_tiers": [
                    "tier3_sensitive",
                    "tier1_bounded_transform",
                ],
                "issued_by": "operator://reviewer",
                "rationale": "Reviewed carefully.",
                "status": "approved",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_until": "2027-01-01T00:00:00Z",
            },
            result,
        )

    def test_payload_filtering_and_missing_field_error_are_exact(self) -> None:
        self.assertEqual(
            {},
            approval.skill_approval_from_payload(
                {"schema": "bssc_skill.v1", "kind": "approval"}
            ),
        )
        self.assertEqual(
            {},
            approval.skill_approval_from_payload(
                {"schema": "bssc_skill.v2", "kind": "ability"}
            ),
        )
        with self.assertRaisesRegex(
            ValueError,
            "Approval artifact v2 requires non-empty fields: "
            "intent, subject_titles, issued_by, rationale",
        ):
            approval.skill_approval_from_payload(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "approval",
                    "approval": False,
                }
            )

    def test_summary_preserves_subject_order_and_defaults(self) -> None:
        self.assertEqual(
            "Approval record operator_approved revoked for First, Second.",
            approval.approval_answer_summary(
                {
                    "approval_class": "operator_approved",
                    "subject_titles": ["First", "Second"],
                    "status": "revoked",
                }
            ),
        )
        self.assertEqual(
            "Approval record automatic approved for unspecified skill.",
            approval.approval_answer_summary({}),
        )

    def test_artifact_projection_uses_only_read_only_content(self) -> None:
        expected = _record()
        self.assertEqual(
            expected,
            approval.artifact_skill_approval(
                _ArtifactView({"skill_approval": expected})
            ),
        )
        self.assertTrue(
            approval.artifact_is_approval_record(
                _ArtifactView({"skill_approval": expected})
            )
        )
        self.assertEqual(
            {}, approval.artifact_skill_approval(_ArtifactView("invalid"))
        )
        self.assertFalse(approval.artifact_is_approval_record(_ArtifactView({})))

    def test_temporal_bounds_are_inclusive_and_malformed_bounds_are_open(self) -> None:
        exact = "2026-04-01T12:00:00Z"
        with patch.object(approval, "datetime", _FixedDateTime):
            self.assertTrue(
                approval.approval_matches_skill(
                    _record(valid_from=exact, valid_until=exact),
                    skill_title="Governed Skill",
                    kind="ability",
                    requested_authorities=["execute"],
                    risk_tier="tier3_sensitive",
                    required_approval_class="operator_approved",
                )
            )
            self.assertTrue(
                approval.approval_matches_skill(
                    _record(valid_from="not-a-date", valid_until="also-not-a-date"),
                    skill_title="Governed Skill",
                    kind="ability",
                    requested_authorities=[],
                    risk_tier="tier0_passive",
                    required_approval_class="automatic",
                )
            )

    def test_matching_denies_each_restriction_branch(self) -> None:
        common = {
            "skill_title": "Governed Skill",
            "kind": "ability",
            "requested_authorities": ["execute"],
            "risk_tier": "tier3_sensitive",
            "required_approval_class": "operator_approved",
        }
        denied = (
            _record(status="revoked"),
            _record(status="expired"),
            _record(valid_from="2999-01-01T00:00:00Z"),
            _record(valid_until="2000-01-01T00:00:00Z"),
            _record(subject_titles=["Other Skill"]),
            _record(subject_kinds=["knowledge"]),
            _record(approved_authorities=["read"]),
            _record(approved_risk_tiers=["tier2_connected"]),
            _record(approval_class="automatic"),
        )
        for record in denied:
            with self.subTest(record=record):
                self.assertFalse(
                    approval.approval_matches_skill(record, **common)
                )

    def test_matching_optional_restrictions_and_class_order_are_stable(self) -> None:
        common = {
            "skill_title": "Governed Skill",
            "kind": "ability",
            "requested_authorities": ["execute", "read"],
            "risk_tier": "tier3_sensitive",
            "required_approval_class": "operator_approved",
        }
        self.assertTrue(approval.approval_matches_skill(_record(), **common))
        self.assertTrue(
            approval.approval_matches_skill(
                _record(
                    approval_class="multi_party_approved",
                    subject_kinds=["ability"],
                    approved_authorities=["read", "execute"],
                    approved_risk_tiers=["tier3_sensitive"],
                ),
                **common,
            )
        )

    def test_matching_artifacts_preserves_input_order_and_identity(self) -> None:
        first = _ArtifactView({"skill_approval": _record()})
        ignored = _ArtifactView({})
        denied = _ArtifactView(
            {"skill_approval": _record(subject_titles=["Other Skill"])}
        )
        second = _ArtifactView(
            {"skill_approval": _record(approval_class="organization_approved")}
        )
        result = approval.matching_approval_artifacts(
            [first, ignored, denied, second],
            skill_title="Governed Skill",
            kind="ability",
            requested_authorities=["execute"],
            risk_tier="tier3_sensitive",
            required_approval_class="operator_approved",
        )
        self.assertEqual([first, second], result)
        self.assertIs(first, result[0])
        self.assertEqual(
            [],
            approval.matching_approval_artifacts(
                None,
                skill_title="Governed Skill",
                kind="ability",
                requested_authorities=[],
                risk_tier="tier0_passive",
                required_approval_class="automatic",
            ),
        )


if __name__ == "__main__":
    unittest.main()
