# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from applied_theory_types import BoundaryShapeTerm
from skill_boundary_normalization import normalize_skill_region_body, reconstruct_skill_region_body
from skill_leaf_types import SkillLeaf, SkillLeafCarrierKind


class SkillBoundaryNormalizationTests(unittest.TestCase):
    def test_normalize_skill_region_body_flattens_nested_mapping_and_list(self) -> None:
        leaves = normalize_skill_region_body(
            BoundaryShapeTerm.INPUT_VALUE,
            {
                "query": "find class Foo",
                "options": {
                    "roots": ["src", "lib"],
                    "case_sensitive": False,
                },
            },
        )

        self.assertEqual(
            [leaf.path for leaf in leaves],
            [
                "/a/options/case_sensitive",
                "/a/options/roots/0",
                "/a/options/roots/1",
                "/a/query",
            ],
        )
        self.assertTrue(all(leaf.carrier_kind == SkillLeafCarrierKind.VALUE for leaf in leaves))
        self.assertEqual(
            [leaf.data_type for leaf in leaves],
            ["Boolean", "String", "String", "String"],
        )

    def test_reconstruct_skill_region_body_round_trips_flattened_mapping(self) -> None:
        original = {
            "query": "find class Foo",
            "options": {
                "roots": ["src", "lib"],
                "case_sensitive": False,
            },
        }
        leaves = normalize_skill_region_body(BoundaryShapeTerm.INPUT_VALUE, original)

        reconstructed = reconstruct_skill_region_body(BoundaryShapeTerm.INPUT_VALUE, leaves)

        self.assertEqual(reconstructed, original)

    def test_reference_region_preserves_reference_carrier_kind(self) -> None:
        leaves = normalize_skill_region_body(
            BoundaryShapeTerm.OUTPUT_REFERENCE,
            {"artifact": "file://report.txt"},
        )

        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0].path, "/d'/artifact")
        self.assertEqual(leaves[0].carrier_kind, SkillLeafCarrierKind.REFERENCE)
        self.assertEqual(leaves[0].data_type, "String")

    def test_skill_leaf_from_dict_normalizes_legacy_lowercase_data_type(self) -> None:
        leaf = SkillLeaf.from_dict(
            {
                "region": "d*",
                "path": "/d/answer",
                "carrier_kind": "value",
                "data_type": "string",
                "semantic_label": "answer",
                "value": "F = m * a",
                "leaf_class": "scalar",
            }
        )

        self.assertEqual(leaf.data_type, "String")

    def test_skill_leaf_from_dict_normalizes_repeated_primitive_kinds(self) -> None:
        strings_leaf = SkillLeaf.from_dict(
            {
                "region": "a*",
                "path": "/a/items",
                "carrier_kind": "value",
                "data_type": "strings",
                "semantic_label": "items",
                "value": ["a", "b"],
                "leaf_class": "collection",
            }
        )
        bools_leaf = SkillLeaf.from_dict(
            {
                "region": "a*",
                "path": "/a/flags",
                "carrier_kind": "value",
                "data_type": "list[bool]",
                "semantic_label": "flags",
                "value": [True, False],
                "leaf_class": "collection",
            }
        )
        bytess_leaf = SkillLeaf.from_dict(
            {
                "region": "a*",
                "path": "/a/chunks",
                "carrier_kind": "value",
                "data_type": "bytes[]",
                "semantic_label": "chunks",
                "value": ["AA==", "BB=="],
                "leaf_class": "collection",
            }
        )

        self.assertEqual(strings_leaf.data_type, "Strings")
        self.assertEqual(bools_leaf.data_type, "Bools")
        self.assertEqual(bytess_leaf.data_type, "Bytess")


if __name__ == "__main__":
    unittest.main()
