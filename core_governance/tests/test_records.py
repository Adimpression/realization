from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass
from typing import Any
import unittest

from realized_core_governance import records


@dataclass
class _ArtifactView:
    content: Any


class GovernanceRecordProjectionTests(unittest.TestCase):
    def test_invalid_artifact_content_projects_empty_records(self) -> None:
        artifact = _ArtifactView(content="invalid")

        self.assertEqual({}, records.artifact_skill_declaration(artifact))
        self.assertEqual({}, records.artifact_skill_policy(artifact))
        self.assertEqual({}, records.artifact_skill_admission(artifact))
        self.assertFalse(records.artifact_is_policy_record(artifact))

    def test_absent_falsey_and_non_mapping_values_project_empty_records(self) -> None:
        for value in (None, "", False, 0, [], ()):
            with self.subTest(value=value):
                artifact = _ArtifactView(
                    content={
                        "skill_declaration": value,
                        "skill_policy": value,
                        "skill_admission": value,
                    }
                )
                self.assertEqual({}, records.artifact_skill_declaration(artifact))
                self.assertEqual({}, records.artifact_skill_policy(artifact))
                self.assertEqual({}, records.artifact_skill_admission(artifact))
                self.assertFalse(records.artifact_is_policy_record(artifact))

    def test_mapping_values_are_copied_without_normalization(self) -> None:
        declaration = UserDict({"intent": " raw ", "nested": {"value": 1}})
        policy = UserDict({"max_risk_tier": "tier2_connected"})
        admission = UserDict({"status": "admitted", "admitted": True})
        artifact = _ArtifactView(
            content=UserDict(
                {
                    "skill_declaration": declaration,
                    "skill_policy": policy,
                    "skill_admission": admission,
                }
            )
        )

        projected_declaration = records.artifact_skill_declaration(artifact)
        projected_policy = records.artifact_skill_policy(artifact)
        projected_admission = records.artifact_skill_admission(artifact)

        self.assertEqual(dict(declaration), projected_declaration)
        self.assertEqual(dict(policy), projected_policy)
        self.assertEqual(dict(admission), projected_admission)
        self.assertIsNot(declaration, projected_declaration)
        self.assertIsNot(policy, projected_policy)
        self.assertIsNot(admission, projected_admission)
        projected_declaration["intent"] = "changed"
        projected_policy["max_risk_tier"] = "changed"
        projected_admission["status"] = "changed"
        self.assertEqual(" raw ", declaration["intent"])
        self.assertEqual("tier2_connected", policy["max_risk_tier"])
        self.assertEqual("admitted", admission["status"])

    def test_policy_classification_depends_only_on_non_empty_projection(self) -> None:
        self.assertFalse(
            records.artifact_is_policy_record(
                _ArtifactView(content={"skill_policy": {}})
            )
        )
        self.assertTrue(
            records.artifact_is_policy_record(
                _ArtifactView(content={"skill_policy": {"intent": ""}})
            )
        )


if __name__ == "__main__":
    unittest.main()
