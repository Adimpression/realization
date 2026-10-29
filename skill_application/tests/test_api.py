from __future__ import annotations

import unittest

import realized_skill_application
from realized_skill_application import composition, ir, normalization, projection


class SkillApplicationApiTests(unittest.TestCase):
    def test_public_surface_is_explicit(self) -> None:
        self.assertEqual(
            ["composition", "ir", "normalization", "projection"],
            realized_skill_application.__all__,
        )

    def test_public_modules_expose_application_operations(self) -> None:
        self.assertTrue(callable(normalization.synthesized_skill_normalization_for_artifact))
        self.assertTrue(callable(ir.canonical_skill_ir_from_artifact))
        self.assertTrue(callable(composition.analyze_skill_composition_plan))
        self.assertTrue(callable(composition.execute_skill_composition_plan))
        self.assertTrue(callable(projection.skill_kind_from_artifact))


if __name__ == "__main__":
    unittest.main()
