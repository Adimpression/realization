from __future__ import annotations

from collections import UserDict
import unittest

from realized_core_governance.declarations import (
    SKILL_AUTHORITY_BOUND_FIELDS,
    SKILL_DECLARATION_REQUIRED_FIELDS,
    policy_answer_summary,
    skill_declaration_from_payload,
    skill_policy_from_payload,
)


def _valid_declaration() -> dict[str, object]:
    return {
        "intent": " Open   a browser URL. ",
        "inputs": {" url ": " target\nURL "},
        "outputs": {" status ": " open status "},
        "authorities_requested": ["EXECUTE", "execute"],
        "authority_bounds": {
            " Execute ": {
                "scope": " local_desktop ",
                "target": " browser_application ",
                "context": " explicit_user_prompt ",
                "duration": " single_invocation ",
                "triggering_conditions": [" user invokes\nskill "],
                "approval_class": "automatic",
            }
        },
        "data_classes_touched": [" public "],
        "side_effects": [" launch\tbrowser "],
        "persistence_behavior": " none ",
        "invocation_rights": [" direct_user_invocation "],
        "composition_rights": [],
        "escalation_rights": [],
        "approval_requirements": ["AUTOMATIC"],
        "risk_tier": "tier1_bounded_transform",
    }


class GovernanceDeclarationTests(unittest.TestCase):
    def test_public_field_contracts_remain_ordered(self) -> None:
        self.assertEqual(
            (
                "intent",
                "inputs",
                "outputs",
                "authorities_requested",
                "data_classes_touched",
                "side_effects",
                "persistence_behavior",
                "invocation_rights",
                "composition_rights",
                "escalation_rights",
                "approval_requirements",
                "risk_tier",
            ),
            SKILL_DECLARATION_REQUIRED_FIELDS,
        )
        self.assertEqual(
            (
                "scope",
                "target",
                "context",
                "duration",
                "triggering_conditions",
                "approval_class",
            ),
            SKILL_AUTHORITY_BOUND_FIELDS,
        )

    def test_v2_declaration_normalizes_contract_and_authority_bounds(self) -> None:
        normalized = skill_declaration_from_payload(
            UserDict(
                {
                    "schema": "bssc_skill.v2",
                    "declaration": UserDict(_valid_declaration()),
                }
            ),
            kind="ability",
            executor_framework="python",
        )

        self.assertEqual("Open a browser URL.", normalized["intent"])
        self.assertEqual({"url": "target URL"}, normalized["inputs"])
        self.assertEqual({"status": "open status"}, normalized["outputs"])
        self.assertEqual(["execute"], normalized["authorities_requested"])
        self.assertEqual(
            {
                "execute": {
                    "scope": "local_desktop",
                    "target": "browser_application",
                    "context": "explicit_user_prompt",
                    "duration": "single_invocation",
                    "triggering_conditions": ["user invokes skill"],
                    "approval_class": "automatic",
                }
            },
            normalized["authority_bounds"],
        )
        self.assertEqual(["public"], normalized["data_classes_touched"])
        self.assertEqual(["launch browser"], normalized["side_effects"])
        self.assertEqual("none", normalized["persistence_behavior"])
        self.assertEqual(["direct_user_invocation"], normalized["invocation_rights"])
        self.assertEqual([], normalized["composition_rights"])
        self.assertEqual([], normalized["escalation_rights"])
        self.assertEqual(["automatic"], normalized["approval_requirements"])
        self.assertEqual("tier1_bounded_transform", normalized["risk_tier"])
        self.assertEqual("python3", normalized["executor_framework"])

    def test_legacy_and_governance_record_payloads_have_no_skill_declaration(self) -> None:
        for payload, kind in (
            ({"schema": "bssc_skill.v1"}, "ability"),
            ({"schema": "bssc_skill.v2"}, "policy"),
            ({"schema": "bssc_skill.v2"}, "approval"),
            ({"schema": "bssc_skill.v2"}, "revocation"),
            ({"schema": "bssc_skill.v2"}, "incident"),
        ):
            with self.subTest(payload=payload, kind=kind):
                self.assertEqual(
                    {},
                    skill_declaration_from_payload(payload, kind=kind),
                )

    def test_collection_fields_must_be_explicit_even_with_fallback_values(self) -> None:
        declaration = _valid_declaration()
        declaration.pop("inputs")
        declaration.pop("outputs")

        with self.assertRaisesRegex(
            ValueError,
            r"requires declared fields: inputs, outputs$",
        ):
            skill_declaration_from_payload(
                {"schema": "bssc_skill.v2", "declaration": declaration},
                kind="ability",
                fallback_inputs={"url": "target URL"},
                fallback_outputs={"status": "open status"},
            )

    def test_every_requested_authority_requires_bounds(self) -> None:
        declaration = _valid_declaration()
        declaration["authorities_requested"] = ["execute", "read"]

        with self.assertRaisesRegex(
            ValueError,
            r"requires authority_bounds for every requested authority: read$",
        ):
            skill_declaration_from_payload(
                {"schema": "bssc_skill.v2", "declaration": declaration},
                kind="ability",
            )

    def test_every_authority_bound_requires_all_bound_fields(self) -> None:
        declaration = _valid_declaration()
        execute_bounds = dict(declaration["authority_bounds"][" Execute "])
        execute_bounds["target"] = ""
        execute_bounds["triggering_conditions"] = []
        declaration["authority_bounds"] = {"execute": execute_bounds}

        with self.assertRaisesRegex(
            ValueError,
            r"authority 'execute' is missing bounds: target, triggering_conditions$",
        ):
            skill_declaration_from_payload(
                {"schema": "bssc_skill.v2", "declaration": declaration},
                kind="ability",
            )

    def test_v2_policy_normalizes_governance_constraints(self) -> None:
        normalized = skill_policy_from_payload(
            UserDict(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "POLICY",
                    "policy": UserDict(
                        {
                            "intent": " Admit   bounded skills. ",
                            "target_kinds": ["ABILITY", "knowledge"],
                            "max_risk_tier": "tier2_connected",
                            "allowed_authorities": ["READ", "execute", "READ"],
                            "denied_authorities": ["approve"],
                            "allowed_executors": ["python", "sh", ""],
                            "allowed_data_classes": [" public ", " internal "],
                            "denied_side_effects": [" raw\tnetwork "],
                            "required_approval_for_risk_tiers": UserDict(
                                {"tier2_connected": "OPERATOR_APPROVED"}
                            ),
                        }
                    ),
                }
            )
        )

        self.assertEqual(
            {
                "intent": "Admit bounded skills.",
                "target_kinds": ["ability", "knowledge"],
                "max_risk_tier": "tier2_connected",
                "allowed_authorities": ["read", "execute"],
                "denied_authorities": ["approve"],
                "allowed_executors": ["python3", "bash"],
                "allowed_data_classes": ["public", "internal"],
                "denied_side_effects": ["raw network"],
                "required_approval_for_risk_tiers": {
                    "tier2_connected": "operator_approved"
                },
            },
            normalized,
        )

    def test_non_policy_and_legacy_payloads_have_no_policy(self) -> None:
        self.assertEqual(
            {},
            skill_policy_from_payload(
                {"schema": "bssc_skill.v1", "kind": "policy"}
            ),
        )
        self.assertEqual(
            {},
            skill_policy_from_payload(
                {"schema": "bssc_skill.v2", "kind": "ability"}
            ),
        )

    def test_policy_requires_nonempty_intent_targets_and_risk(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"requires non-empty fields: intent, target_kinds$",
        ):
            skill_policy_from_payload(
                {
                    "schema": "bssc_skill.v2",
                    "kind": "policy",
                    "policy": {
                        "intent": "",
                        "target_kinds": [],
                        "max_risk_tier": "tier1_bounded_transform",
                    },
                }
            )

    def test_policy_summary_is_stable_and_reviewable(self) -> None:
        self.assertEqual(
            "Policy intent: Admit bounded skills.. Targets: ability. "
            "Max risk tier: tier2_connected. Allowed authorities: read, execute. "
            "Denied authorities: approve.",
            policy_answer_summary(
                {
                    "intent": " Admit   bounded skills. ",
                    "target_kinds": ["ability"],
                    "max_risk_tier": "tier2_connected",
                    "allowed_authorities": ["read", "execute"],
                    "denied_authorities": ["approve"],
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
