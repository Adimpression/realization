from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import unittest
from unittest.mock import patch

from realized_core_governance import lifecycle


@dataclass
class _ArtifactView:
    content: Any


class GovernanceLifecycleTests(unittest.TestCase):
    def test_status_vocabularies_preserve_exact_order(self) -> None:
        self.assertEqual(
            ("pending_review", "reviewed", "review_rejected"),
            lifecycle.SKILL_REVIEW_STATUSES,
        )
        self.assertEqual(
            ("installed", "blocked"), lifecycle.SKILL_INSTALLATION_STATUSES
        )
        self.assertEqual(
            ("active", "inactive"), lifecycle.SKILL_ACTIVATION_STATUSES
        )
        self.assertEqual(
            ("trusted", "restricted", "suspended", "revoked"),
            lifecycle.SKILL_TRUST_STATUSES,
        )
        self.assertEqual(
            ("clear", "quarantined"), lifecycle.SKILL_QUARANTINE_STATUSES
        )

    def test_status_normalizers_preserve_defaults_controls_and_case(self) -> None:
        cases = (
            (lifecycle.normalize_skill_review_status, " REVIEWED\n", {}, "reviewed"),
            (
                lifecycle.normalize_skill_review_status,
                "unknown",
                {"default": "CUSTOM"},
                "CUSTOM",
            ),
            (
                lifecycle.normalize_skill_installation_status,
                "\x00BLOCKED\x7f",
                {},
                "blocked",
            ),
            (
                lifecycle.normalize_skill_activation_status,
                0,
                {"default": "inactive"},
                "inactive",
            ),
            (lifecycle.normalize_skill_trust_status, "SUSPENDED", {}, "suspended"),
            (
                lifecycle.normalize_skill_quarantine_status,
                [],
                {"default": "quarantined"},
                "quarantined",
            ),
        )
        for function, value, kwargs, expected in cases:
            with self.subTest(function=function.__name__, value=value, kwargs=kwargs):
                self.assertEqual(expected, function(value, **kwargs))

    def test_synthesis_preserves_every_admission_branch(self) -> None:
        expected = {
            "admitted": (
                "installed",
                "active",
                "trusted",
                "Skill is installed, active, and trusted for invocation.",
            ),
            "held": (
                "installed",
                "inactive",
                "restricted",
                "Skill remains installed but inactive while admission is held.",
            ),
            "rejected": (
                "blocked",
                "inactive",
                "restricted",
                "Skill is blocked because admission was rejected.",
            ),
            "": (
                "installed",
                "inactive",
                "restricted",
                "Skill lifecycle was synthesized without a current admitted invocation state.",
            ),
        }
        for admission, values in expected.items():
            with self.subTest(admission=admission):
                result = lifecycle.synthesized_skill_lifecycle(
                    admission_status=admission,
                    default_updated_at=" 2026-03-31T12:00:00+00:00 ",
                )
                self.assertEqual(admission, result["admission_status"])
                self.assertEqual(values[0], result["installation_status"])
                self.assertEqual(values[1], result["activation_status"])
                self.assertEqual(values[2], result["trust_status"])
                self.assertEqual(values[3], result["status_reason"])
                self.assertEqual("pending_review", result["review_status"])
                self.assertEqual("clear", result["quarantine_status"])
                self.assertEqual(
                    "2026-03-31T12:00:00+00:00", result["updated_at"]
                )

    def test_synthesis_policy_and_clock_precedence_is_stable(self) -> None:
        with patch.object(
            lifecycle, "utc_now", return_value="2026-04-01T00:00:00+00:00"
        ):
            result = lifecycle.synthesized_skill_lifecycle(policy_record=True)
        self.assertEqual("admitted", result["admission_status"])
        self.assertEqual("active", result["activation_status"])
        self.assertEqual("2026-04-01T00:00:00+00:00", result["updated_at"])

    def test_payload_normalization_preserves_nested_and_explicit_precedence(self) -> None:
        result = lifecycle.skill_lifecycle_from_payload(
            {
                "lifecycle": {
                    "review_status": " REVIEWED ",
                    "admission_status": "held",
                    "installation_status": "installed",
                    "activation_status": "inactive",
                    "trust_status": "restricted",
                    "quarantine_status": "clear",
                    "status_reason": "  waiting\nfor approval  ",
                    "updated_at": "payload-time",
                }
            },
            admission_status="admitted",
            default_updated_at="default-time",
        )
        self.assertEqual(
            {
                "review_status": "reviewed",
                "admission_status": "admitted",
                "installation_status": "installed",
                "activation_status": "inactive",
                "trust_status": "restricted",
                "quarantine_status": "clear",
                "status_reason": "waiting for approval",
                "updated_at": "payload-time",
            },
            result,
        )
        self.assertEqual(
            lifecycle.skill_lifecycle_from_payload(None, default_updated_at="fixed"),
            lifecycle.skill_lifecycle_from_payload("not-a-mapping", default_updated_at="fixed"),
        )

    def test_artifact_projection_uses_only_read_only_content(self) -> None:
        self.assertEqual({}, lifecycle.artifact_skill_lifecycle(_ArtifactView({})))
        self.assertEqual(
            {}, lifecycle.artifact_skill_lifecycle(_ArtifactView("not-a-mapping"))
        )
        result = lifecycle.artifact_skill_lifecycle(
            _ArtifactView(
                {
                    "skill_admission": {
                        "status": "held",
                        "evaluated_at": "admission-time",
                    },
                    "created_at": "created-time",
                }
            )
        )
        self.assertEqual("held", result["admission_status"])
        self.assertEqual("inactive", result["activation_status"])
        self.assertEqual("admission-time", result["updated_at"])

    def test_effective_projection_preserves_explicit_lifecycle_and_current_admission_rules(self) -> None:
        explicit = _ArtifactView(
            {
                "skill_lifecycle": {
                    "admission_status": "held",
                    "activation_status": "inactive",
                    "updated_at": "explicit-time",
                },
                "skill_admission": {"status": "admitted"},
            }
        )
        result = lifecycle.artifact_effective_skill_lifecycle(
            explicit, current_admission_status="rejected"
        )
        self.assertEqual("admitted", result["admission_status"])
        self.assertEqual("inactive", result["activation_status"])
        self.assertEqual("explicit-time", result["updated_at"])

        synthesized = lifecycle.artifact_effective_skill_lifecycle(
            _ArtifactView(
                {
                    "skill_admission": {
                        "status": "rejected",
                        "evaluated_at": "admission-time",
                    }
                }
            ),
            current_admission_status="admitted",
        )
        self.assertEqual("admitted", synthesized["admission_status"])
        self.assertEqual("active", synthesized["activation_status"])
        self.assertEqual("admission-time", synthesized["updated_at"])
        self.assertEqual(
            {},
            lifecycle.artifact_effective_skill_lifecycle(_ArtifactView({})),
        )

    def test_invocation_gate_order_and_messages_are_exact(self) -> None:
        cases = (
            (
                {
                    "quarantine_status": "quarantined",
                    "trust_status": "revoked",
                    "installation_status": "blocked",
                    "activation_status": "inactive",
                },
                (False, "Governed skill is quarantined and cannot be invoked."),
            ),
            (
                {"trust_status": "restricted"},
                (False, "Governed skill trust status is restricted."),
            ),
            (
                {"trust_status": "suspended"},
                (False, "Governed skill trust status is suspended."),
            ),
            (
                {"trust_status": "revoked"},
                (False, "Governed skill trust status is revoked."),
            ),
            (
                {"installation_status": "blocked"},
                (False, "Governed skill installation status is blocked."),
            ),
            (
                {"activation_status": "inactive"},
                (False, "Governed skill activation status is inactive."),
            ),
            ({}, (True, "")),
            (None, (True, "")),
            ({"trust_status": "unknown"}, (True, "")),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    expected, lifecycle.skill_lifecycle_allows_invocation(value)
                )


if __name__ == "__main__":
    unittest.main()
