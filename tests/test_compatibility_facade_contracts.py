from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_compatibility_facade_contracts.py"
SPEC = importlib.util.spec_from_file_location(
    "capture_compatibility_facade_contracts",
    SCRIPT_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"unable to load {SCRIPT_PATH}")
contract_capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract_capture)


class CompatibilityFacadeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_path = (
            REPO_ROOT / "architecture" / "compatibility-facade-contracts.json"
        )
        cls.expected = json.loads(cls.contract_path.read_text(encoding="utf-8"))
        cls.current = contract_capture.build_contracts()
        cls.cards = {
            card["module"]: card for card in cls.current["cards"]
        }

    def test_checked_in_contract_ledger_matches_executable_contracts(self) -> None:
        self.assertEqual(self.expected, self.current)

    def test_every_facade_has_one_retirement_card(self) -> None:
        self.assertEqual(88, self.current["summary"]["card_count"])
        self.assertEqual(88, len(self.cards))

    def test_exact_alias_contracts_prove_module_object_identity(self) -> None:
        exact_aliases = [
            card
            for card in self.current["cards"]
            if card["shape"] == "exact_module_alias"
        ]
        self.assertEqual(63, len(exact_aliases))
        self.assertTrue(
            all(card["exact_module_identity_observed"] is True for card in exact_aliases)
        )
        self.assertTrue(
            all(
                card["proof_strategy"] == "exact_module_object_identity"
                for card in exact_aliases
            )
        )

    def test_pickle_compatibility_obligations_are_explicit(self) -> None:
        self.assertEqual(
            35,
            self.current["summary"]["facades_with_durable_pickle_globals"],
        )
        self.assertEqual(133, self.current["summary"]["pickle_global_count"])
        self.assertEqual(
            ["BSSCController"],
            self.cards["main"]["durable_pickle_globals"],
        )
        self.assertIn(
            "LearningContext",
            self.cards["learning_context"]["durable_pickle_globals"],
        )
        policy = json.loads(
            (
                REPO_ROOT / "architecture" / "compatibility-facade-policy.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(
                card["module"]
                for card in self.current["cards"]
                if card["durable_pickle_globals"]
            ),
            policy["durable_pickle_facades"],
        )

    def test_behavior_and_aggregate_facades_require_manual_proof(self) -> None:
        for module in (
            "blend_context",
            "blend_session",
            "controller_runtime",
            "itemize",
            "main",
        ):
            with self.subTest(module=module):
                self.assertEqual(
                    "manual_behavior_equivalence",
                    self.cards[module]["proof_strategy"],
                )
        self.assertEqual(
            "manual_multi_owner_export_mapping",
            self.cards["normalize"]["proof_strategy"],
        )

    def test_every_card_has_a_reviewable_surface_and_rollback(self) -> None:
        self.assertTrue(
            all(
                card["contract_evidence"]
                and card["export_surface"]["public_names"]
                and card["rollback_operation"]
                for card in self.current["cards"]
            )
        )


if __name__ == "__main__":
    unittest.main()
