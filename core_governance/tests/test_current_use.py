from __future__ import annotations

import unittest
from unittest.mock import patch

from realized_core_governance import current_use


class GovernanceCurrentUseTests(unittest.TestCase):
    def test_legacy_schema_bypasses_governed_admission_and_lifecycle(self) -> None:
        with patch.object(
            current_use,
            "skill_lifecycle_allows_invocation",
            side_effect=AssertionError("legacy lifecycle must not be evaluated"),
        ):
            self.assertEqual(
                (True, ""),
                current_use.skill_current_use_allows_invocation(
                    schema_version="bssc_skill.v1",
                    admission={"status": "rejected"},
                    lifecycle={"quarantine_status": "quarantined"},
                ),
            )

    def test_governed_schema_denies_missing_admission(self) -> None:
        for admission in (None, {}):
            with self.subTest(admission=admission):
                self.assertEqual(
                    (False, "Governed skill has no admission record."),
                    current_use.skill_admission_allows_current_use(
                        schema_version="bssc_skill.v2",
                        admission=admission,
                    ),
                )

    def test_non_admitted_status_uses_collapsed_rationale_or_fallback(self) -> None:
        cases = (
            (
                {"status": " HELD ", "rationale": "  waiting\nfor\x00approval  "},
                "waiting for approval",
            ),
            (
                {"status": "rejected", "rationale": "\n\x00\t"},
                "Governed skill is not admitted for use.",
            ),
            (
                {"admitted": True},
                "Governed skill is not admitted for use.",
            ),
        )
        for admission, expected_reason in cases:
            with self.subTest(admission=admission):
                self.assertEqual(
                    (False, expected_reason),
                    current_use.skill_admission_allows_current_use(
                        schema_version="bssc_skill.v2",
                        admission=admission,
                    ),
                )

    def test_admitted_status_is_case_and_whitespace_insensitive(self) -> None:
        self.assertEqual(
            (True, ""),
            current_use.skill_admission_allows_current_use(
                schema_version="bssc_skill.v2",
                admission={"status": "  ADMITTED\n"},
            ),
        )

    def test_admission_denial_short_circuits_lifecycle(self) -> None:
        with patch.object(
            current_use,
            "skill_lifecycle_allows_invocation",
            side_effect=AssertionError("denied admission must short-circuit"),
        ):
            self.assertEqual(
                (False, "policy denied current use"),
                current_use.skill_current_use_allows_invocation(
                    schema_version="bssc_skill.v2",
                    admission={
                        "status": "rejected",
                        "rationale": "policy denied current use",
                    },
                    lifecycle={"activation_status": "active"},
                ),
            )

    def test_admitted_skill_applies_exact_lifecycle_precedence(self) -> None:
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
                {"trust_status": "suspended", "activation_status": "inactive"},
                (False, "Governed skill trust status is suspended."),
            ),
            (
                {"installation_status": "blocked", "activation_status": "inactive"},
                (False, "Governed skill installation status is blocked."),
            ),
            (
                {"activation_status": "inactive"},
                (False, "Governed skill activation status is inactive."),
            ),
            ({}, (True, "")),
            (None, (True, "")),
        )
        for lifecycle, expected in cases:
            with self.subTest(lifecycle=lifecycle):
                self.assertEqual(
                    expected,
                    current_use.skill_current_use_allows_invocation(
                        schema_version="bssc_skill.v2",
                        admission={"status": "admitted"},
                        lifecycle=lifecycle,
                    ),
                )

    def test_unsupported_schema_and_malformed_admission_fail_exactly(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported skill schema version: future.skill.v9",
        ):
            current_use.skill_admission_allows_current_use(
                schema_version="future.skill.v9",
                admission=None,
            )
        with self.assertRaises(AttributeError):
            current_use.skill_admission_allows_current_use(
                schema_version="bssc_skill.v2",
                admission=["not", "a", "mapping"],  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
