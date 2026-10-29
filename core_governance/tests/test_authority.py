from __future__ import annotations

import unittest

from realized_core_governance.authority import (
    AuthorityEvaluation,
    evaluate_authority_grants,
)


class AuthorityEvaluationTests(unittest.TestCase):
    def test_non_admitted_state_denies_before_authority_or_grant_checks(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind="unknown.effect",
            required_authority="",
            admitted=False,
            admission_reason="  held   for review ",
            grants=[object()],  # type: ignore[list-item]
        )

        self.assertEqual(
            AuthorityEvaluation(False, "held for review"),
            decision,
        )

    def test_non_admitted_state_uses_stable_fallback_reason(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind="execute.python3",
            required_authority="execute",
            admitted=False,
            admission_reason="",
            grants=[],
        )

        self.assertEqual(
            AuthorityEvaluation(
                False,
                "Governed skill is not admitted for this effect.",
                "execute",
            ),
            decision,
        )

    def test_missing_effect_mapping_is_denied_before_grant_inspection(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind="unknown.effect",
            required_authority="",
            admitted=True,
            admission_reason="",
            grants=[object()],  # type: ignore[list-item]
        )

        self.assertEqual(
            AuthorityEvaluation(
                False,
                "No governed authority mapping is registered for effect kind unknown.effect.",
            ),
            decision,
        )

    def test_missing_matching_grant_is_denied(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind="net.http",
            required_authority="communicate",
            admitted=True,
            admission_reason="",
            grants=[{"id": "grant-read", "authority": "read"}],
        )

        self.assertEqual(
            AuthorityEvaluation(
                False,
                "Runtime grants do not cover required authority communicate for net.http.",
                "communicate",
            ),
            decision,
        )

    def test_matching_grants_preserve_normalized_ids_order_and_duplicates(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind=" execute.python3 ",
            required_authority=" execute ",
            admitted=True,
            admission_reason="",
            grants=[
                {"id": " grant-b ", "authority": " execute "},
                {"id": "", "authority": "execute"},
                {"id": "grant-a", "authority": "read"},
                {"id": "grant-b", "authority": "execute"},
            ],
        )

        self.assertEqual(
            AuthorityEvaluation(
                True,
                "Effect request is covered by issued runtime grants.",
                "execute",
                ("grant-b", "grant-b"),
            ),
            decision,
        )

    def test_authority_matching_remains_case_sensitive(self) -> None:
        decision = evaluate_authority_grants(
            effect_kind="execute.python3",
            required_authority="execute",
            admitted=True,
            admission_reason="",
            grants=[{"id": "grant-execute", "authority": "Execute"}],
        )

        self.assertFalse(decision.allowed)
        self.assertEqual((), decision.grant_ids)

    def test_malformed_grant_retains_attribute_failure(self) -> None:
        with self.assertRaises(AttributeError):
            evaluate_authority_grants(
                effect_kind="execute.python3",
                required_authority="execute",
                admitted=True,
                admission_reason="",
                grants=[object()],  # type: ignore[list-item]
            )


if __name__ == "__main__":
    unittest.main()
