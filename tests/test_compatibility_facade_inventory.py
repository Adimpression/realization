from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_compatibility_facades.py"
SPEC = importlib.util.spec_from_file_location(
    "check_compatibility_facades",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
inventory_checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_checker)


class CompatibilityFacadeInventoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = inventory_checker.build_inventory(
            REPO_ROOT,
            REPO_ROOT / "architecture" / "boundaries.toml",
        )

    def test_checked_in_inventory_matches_repository(self) -> None:
        checked_in = json.loads(
            (REPO_ROOT / "architecture" / "compatibility-facades.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(checked_in, self.inventory)

    def test_every_facade_is_inventoried_once(self) -> None:
        modules = [row["module"] for row in self.inventory["facades"]]
        self.assertEqual(len(modules), len(set(modules)))
        self.assertEqual(
            self.inventory["summary"]["facade_count"],
            len(modules),
        )

    def test_canonical_packages_do_not_consume_root_facades(self) -> None:
        self.assertEqual(
            0,
            self.inventory["summary"]["canonical_package_consumer_count"],
        )

    def test_public_documentation_and_examples_use_canonical_apis(self) -> None:
        self.assertEqual(
            [],
            self.inventory["public_documentation_facade_references"],
        )
        self.assertEqual([], self.inventory["public_example_facade_consumers"])

    def test_retirement_policy_keeps_facades_until_qualification(self) -> None:
        qualification = self.inventory["qualification"]
        self.assertGreaterEqual(qualification["minimum_stable_cycles"], 1)
        if qualification["completed_stable_cycles"] < qualification["minimum_stable_cycles"]:
            self.assertTrue(qualification["retirement_hold"])
        self.assertTrue(
            all(row["removal_state"] == "retained" for row in self.inventory["facades"])
        )


if __name__ == "__main__":
    unittest.main()
