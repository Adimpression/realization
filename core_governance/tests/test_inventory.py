from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import unittest

from realized_core_governance.inventory import (
    GovernanceInventoryReader,
    load_governance_inventory,
)


@dataclass
class _Artifact:
    title: str
    content: Any


class _Reader:
    def __init__(self, artifacts: list[_Artifact]) -> None:
        self.artifacts = artifacts
        self.calls = 0

    def load_all_artifacts(self) -> list[_Artifact]:
        self.calls += 1
        return self.artifacts


class GovernanceInventoryTests(unittest.TestCase):
    def test_reader_protocol_is_structural(self) -> None:
        self.assertIsInstance(_Reader([]), GovernanceInventoryReader)

    def test_empty_inventory_is_loaded_once_and_retained(self) -> None:
        artifacts: list[_Artifact] = []
        reader = _Reader(artifacts)

        inventory = load_governance_inventory(reader)

        self.assertEqual(1, reader.calls)
        self.assertIs(artifacts, inventory["artifacts"])
        self.assertEqual([], inventory["policies"])
        self.assertEqual([], inventory["approvals"])
        self.assertEqual([], inventory["revocations"])
        self.assertEqual([], inventory["incidents"])
        self.assertGreaterEqual(inventory["timings"]["load_seconds"], 0.0)
        self.assertEqual(
            inventory["timings"]["load_seconds"],
            round(inventory["timings"]["load_seconds"], 6),
        )

    def test_records_are_classified_independently_in_source_order(self) -> None:
        policy = _Artifact("Policy", {"skill_policy": {"name": "policy"}})
        approval = _Artifact("Approval", {"skill_approval": {"status": "approved"}})
        overlapping = _Artifact(
            "Overlapping",
            {
                "skill_policy": {"name": "overlap"},
                "skill_approval": {"status": "approved"},
                "skill_revocation": {"status": "active"},
                "skill_incident": {"status": "open"},
            },
        )
        revocation = _Artifact(
            "Revocation", {"skill_revocation": {"status": "active"}}
        )
        incident = _Artifact("Incident", {"skill_incident": {"status": "open"}})
        ordinary = _Artifact("Ordinary", {"answer": "not governance"})
        artifacts = [policy, approval, overlapping, revocation, incident, ordinary]
        reader = _Reader(artifacts)

        inventory = load_governance_inventory(reader)

        self.assertEqual(1, reader.calls)
        self.assertIs(artifacts, inventory["artifacts"])
        self.assertEqual([policy, overlapping], inventory["policies"])
        self.assertEqual([approval, overlapping], inventory["approvals"])
        self.assertEqual([overlapping, revocation], inventory["revocations"])
        self.assertEqual([overlapping, incident], inventory["incidents"])


if __name__ == "__main__":
    unittest.main()
