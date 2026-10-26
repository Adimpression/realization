from __future__ import annotations

import unittest

from realized_core_governance import vocabulary


class GovernanceVocabularyTests(unittest.TestCase):
    def test_vocabularies_preserve_exact_membership_and_order(self) -> None:
        self.assertEqual(
            {
                "knowledge",
                "ability",
                "policy",
                "approval",
                "revocation",
                "incident",
            },
            vocabulary.SKILL_KIND_CHOICES,
        )
        self.assertEqual(
            (
                "tier0_passive",
                "tier1_bounded_transform",
                "tier2_connected",
                "tier3_sensitive",
                "tier4_agentic",
                "tier5_sovereign",
            ),
            vocabulary.SKILL_RISK_TIERS,
        )
        self.assertEqual(
            (
                "automatic",
                "operator_approved",
                "multi_party_approved",
                "organization_approved",
                "emergency_approved",
                "prohibited",
            ),
            vocabulary.SKILL_APPROVAL_CLASSES,
        )
        self.assertEqual(
            (
                "read",
                "write",
                "execute",
                "communicate",
                "persist",
                "invoke",
                "approve",
                "modify",
                "export",
                "escalate",
            ),
            vocabulary.SKILL_AUTHORITIES,
        )

    def test_scalar_normalizers_preserve_defaults_and_cleanup(self) -> None:
        cases = (
            (vocabulary.normalize_skill_kind, " ABILITY\n", {}, "ability"),
            (vocabulary.normalize_skill_kind, "unknown", {}, "knowledge"),
            (vocabulary.normalize_skill_kind, 0, {"default": "policy"}, "policy"),
            (
                vocabulary.normalize_skill_kind,
                "unknown",
                {"default": "CUSTOM"},
                "CUSTOM",
            ),
            (
                vocabulary.normalize_skill_risk_tier,
                "\x00TIER3_SENSITIVE\x7f",
                {},
                "tier3_sensitive",
            ),
            (
                vocabulary.normalize_skill_risk_tier,
                None,
                {"default": "tier0_passive"},
                "tier0_passive",
            ),
            (
                vocabulary.normalize_skill_approval_class,
                " OPERATOR_APPROVED ",
                {},
                "operator_approved",
            ),
            (
                vocabulary.normalize_skill_approval_class,
                [],
                {"default": "prohibited"},
                "prohibited",
            ),
        )
        for function, value, kwargs, expected in cases:
            with self.subTest(function=function.__name__, value=value, kwargs=kwargs):
                self.assertEqual(expected, function(value, **kwargs))

    def test_authority_normalization_is_ordered_deduplicated_and_list_specific(self) -> None:
        self.assertEqual(
            ["read", "write", "execute"],
            vocabulary.normalize_skill_authorities(
                [" READ ", "write", "READ", "execute\n", "unknown", ""]
            ),
        )
        self.assertEqual(
            ["communicate"],
            vocabulary.normalize_skill_authorities("COMMUNICATE"),
        )
        self.assertEqual([], vocabulary.normalize_skill_authorities(("read", "write")))
        for empty in (None, "", [], {}):
            with self.subTest(empty=empty):
                self.assertEqual([], vocabulary.normalize_skill_authorities(empty))


if __name__ == "__main__":
    unittest.main()
