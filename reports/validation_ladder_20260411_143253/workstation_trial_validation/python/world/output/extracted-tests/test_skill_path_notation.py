# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from applied_theory_types import BoundaryShapeTerm
from skill_path_notation import canonical_skill_path, parse_canonical_skill_path


class SkillPathNotationTests(unittest.TestCase):
    def test_canonical_skill_path_round_trips_nested_segments(self) -> None:
        path = canonical_skill_path(
            BoundaryShapeTerm.INPUT_VALUE,
            ["options", "roots", 0],
        )

        self.assertEqual(path, "/a/options/roots/0")
        region, segments = parse_canonical_skill_path(path)
        self.assertEqual(region, BoundaryShapeTerm.INPUT_VALUE)
        self.assertEqual(segments, ["options", "roots", "0"])

    def test_canonical_skill_path_escapes_slashes_and_tildes(self) -> None:
        path = canonical_skill_path(
            BoundaryShapeTerm.OUTPUT_REFERENCE,
            ["artifact/main", "v~1"],
        )

        self.assertEqual(path, "/d'/artifact~1main/v~01")
        region, segments = parse_canonical_skill_path(path)
        self.assertEqual(region, BoundaryShapeTerm.OUTPUT_REFERENCE)
        self.assertEqual(segments, ["artifact/main", "v~1"])


if __name__ == "__main__":
    unittest.main()
