from __future__ import annotations

from dataclasses import dataclass
import unittest
from typing import Any

from realized_core_governance.admission import evaluate_skill_policy_admission
from realized_core_semantics.artifacts import TitledArtifactContentView


@dataclass(frozen=True)
class _Artifact:
    title: str
    content: dict[str, Any]


def _policy(title: str = "Local policy", **overrides: Any) -> _Artifact:
    policy = {
        "target_kinds": ["ability"],
        "max_risk_tier": "tier2_connected",
        "allowed_authorities": ["execute", "read"],
        "denied_authorities": [],
        "allowed_executors": ["python3"],
        "allowed_data_classes": ["public"],
        "denied_side_effects": [],
        "required_approval_for_risk_tiers": {},
    }
    policy.update(overrides)
    return _Artifact(title=title, content={"skill_policy": policy})


def _approval(title: str = "Operator approval", **overrides: Any) -> _Artifact:
    approval = {
        "approval_class": "operator_approved",
        "subject_titles": ["Example skill"],
        "subject_kinds": ["ability"],
        "approved_authorities": ["execute"],
        "approved_risk_tiers": ["tier1_bounded_transform"],
        "status": "approved",
        "valid_from": "",
        "valid_until": "",
    }
    approval.update(overrides)
    return _Artifact(title=title, content={"skill_approval": approval})


def _declaration(**overrides: Any) -> dict[str, Any]:
    declaration = {
        "authorities_requested": ["execute"],
        "risk_tier": "tier1_bounded_transform",
        "approval_requirements": ["automatic"],
        "data_classes_touched": ["public"],
        "side_effects": ["local executor invocation"],
    }
    declaration.update(overrides)
    return declaration


class PolicyAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock_calls = 0

    def _now(self) -> str:
        self.clock_calls += 1
        return "2026-10-26T12:00:00Z"

    def _evaluate(self, **overrides: Any) -> dict[str, Any]:
        arguments = {
            "declaration": _declaration(),
            "skill_title": "Example skill",
            "kind": "ability",
            "executor_framework": "python",
            "policy_artifacts": [_policy()],
            "approval_artifacts": [],
            "evaluated_at": self._now,
        }
        arguments.update(overrides)
        return evaluate_skill_policy_admission(**arguments)

    def test_artifact_protocol_is_structural(self) -> None:
        self.assertIsInstance(_policy(), TitledArtifactContentView)

    def test_no_policy_holds_before_other_policy_checks(self) -> None:
        result = self._evaluate(
            declaration=_declaration(authorities_requested=[]),
            policy_artifacts=[],
        )
        self.assertEqual(result["status"], "held")
        self.assertEqual(
            result["rationale"],
            "No policy artifact is currently installed for governed v2 skills.",
        )
        self.assertEqual(result["policy_titles"], [])
        self.assertEqual(self.clock_calls, 1)

    def test_executable_skill_requires_execute_authority(self) -> None:
        result = self._evaluate(
            declaration=_declaration(authorities_requested=["read"]),
        )
        self.assertEqual(result["status"], "held")
        self.assertEqual(
            result["rationale"],
            "Executable python3 skills must declare execute authority before they can be admitted.",
        )
        self.assertEqual(result["policy_titles"], [])

    def test_automatic_policy_admits_and_preserves_titles(self) -> None:
        result = self._evaluate(
            policy_artifacts=[_policy("First"), _policy("Second")],
        )
        self.assertEqual(result["status"], "admitted")
        self.assertTrue(result["admitted"])
        self.assertEqual(result["policy_titles"], ["First", "Second"])
        self.assertEqual(result["approval_titles"], [])
        self.assertEqual(result["required_approval_class"], "automatic")
        self.assertEqual(result["evaluated_at"], "2026-10-26T12:00:00Z")
        self.assertEqual(self.clock_calls, 1)

    def test_policy_rejections_preserve_reason_order(self) -> None:
        result = self._evaluate(
            declaration=_declaration(
                authorities_requested=["execute", "write"],
                risk_tier="tier3_sensitive",
                data_classes_touched=["secret"],
                side_effects=["network communication"],
            ),
            policy_artifacts=[
                _policy(
                    max_risk_tier="tier1_bounded_transform",
                    allowed_authorities=["execute"],
                    denied_authorities=["write"],
                    allowed_executors=["bash"],
                    allowed_data_classes=["public"],
                    denied_side_effects=["network communication"],
                )
            ],
        )
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(
            result["rationale"],
            "policy 'Local policy' limits risk to tier1_bounded_transform, but declaration requests tier3_sensitive; "
            "policy 'Local policy' denies authorities: write; "
            "policy 'Local policy' does not allow authorities: write; "
            "policy 'Local policy' does not allow executor python3; "
            "policy 'Local policy' does not allow data classes: secret; "
            "policy 'Local policy' denies side effects: network communication",
        )

    def test_kind_rejection_skips_remaining_checks_for_that_policy(self) -> None:
        result = self._evaluate(
            policy_artifacts=[
                _policy(
                    target_kinds=["knowledge"],
                    allowed_authorities=[],
                )
            ],
        )
        self.assertEqual(
            result["rationale"],
            "policy 'Local policy' does not admit kind 'ability'",
        )

    def test_policy_cannot_require_more_than_declaration_provides(self) -> None:
        result = self._evaluate(
            policy_artifacts=[
                _policy(
                    required_approval_for_risk_tiers={
                        "tier1_bounded_transform": "operator_approved"
                    }
                )
            ]
        )
        self.assertEqual(result["status"], "held")
        self.assertEqual(
            result["rationale"],
            "Policy requires approval class operator_approved, but declaration only provides automatic.",
        )

    def test_explicit_approval_is_held_when_no_record_matches(self) -> None:
        result = self._evaluate(
            declaration=_declaration(
                approval_requirements=["operator_approved"]
            ),
            policy_artifacts=[
                _policy(
                    required_approval_for_risk_tiers={
                        "tier1_bounded_transform": "operator_approved"
                    }
                )
            ],
        )
        self.assertEqual(result["status"], "held")
        self.assertEqual(
            result["rationale"],
            "Policy requires explicit approval class operator_approved before admission.",
        )

    def test_matching_approval_admits_and_preserves_approval_order(self) -> None:
        result = self._evaluate(
            declaration=_declaration(
                approval_requirements=["operator_approved"]
            ),
            policy_artifacts=[
                _policy(
                    required_approval_for_risk_tiers={
                        "tier1_bounded_transform": "operator_approved"
                    }
                )
            ],
            approval_artifacts=[_approval("First"), _approval("Second")],
        )
        self.assertEqual(result["status"], "admitted")
        self.assertEqual(result["approval_titles"], ["First", "Second"])
        self.assertEqual(
            result["rationale"],
            "Declaration satisfied installed policy constraints and matched approval class operator_approved.",
        )

    def test_non_policy_records_are_ignored(self) -> None:
        result = self._evaluate(
            policy_artifacts=[
                _Artifact(title="Not policy", content={}),
                _policy("Effective policy"),
            ]
        )
        self.assertEqual(result["policy_titles"], ["Effective policy"])


if __name__ == "__main__":
    unittest.main()
