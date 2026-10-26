from __future__ import annotations

import unittest

from realized_core_semantics.theory import BoundaryShapeTermKind
from realized_skill_semantics.leaves import (
    REGION_SYMBOL_BY_TERM,
    SkillLeafCarrierKind,
    SkillLeafClass,
)
from realized_skill_semantics.normalization import (
    SKILL_NORMALIZATION_VERSION,
    normalize_skill_region_body,
    normalized_skill_normalization_payload,
    reconstruct_skill_region_body,
    synthesized_skill_normalization,
)
from realized_skill_semantics.paths import SKILL_PATH_NOTATION_VERSION


class SkillNormalizationTests(unittest.TestCase):
    def test_synthesis_emits_all_regions_with_stable_shape(self) -> None:
        document = synthesized_skill_normalization(
            input_values={"query": "force"},
            output_values={"answer": "F = m * a"},
        )

        self.assertEqual(SKILL_NORMALIZATION_VERSION, document["normalization_version"])
        self.assertEqual(SKILL_PATH_NOTATION_VERSION, document["path_notation_version"])
        self.assertEqual(
            [REGION_SYMBOL_BY_TERM[term] for term in BoundaryShapeTermKind],
            list(document["regions"]),
        )
        for term in BoundaryShapeTermKind:
            symbol = REGION_SYMBOL_BY_TERM[term]
            region = document["regions"][symbol]
            expected_carrier = (
                "reference" if "'" in symbol else "value"
            )
            with self.subTest(region=symbol):
                self.assertEqual(term.value, region["boundary_term"])
                self.assertEqual(expected_carrier, region["carrier_kind"])
                self.assertTrue(region["reconstructible"])

        self.assertEqual(
            ["/a/query"],
            [leaf["path"] for leaf in document["regions"]["a"]["leaves"]],
        )
        self.assertEqual(
            ["/d/answer"],
            [leaf["path"] for leaf in document["regions"]["d"]["leaves"]],
        )

    def test_nested_body_round_trips_in_deterministic_path_order(self) -> None:
        body = {
            "query": "find class Foo",
            "options": {
                "roots": ["src", "lib"],
                "case_sensitive": False,
            },
        }

        leaves = normalize_skill_region_body(BoundaryShapeTermKind.INPUT_VALUE, body)

        self.assertEqual(
            [
                "/a/options/case_sensitive",
                "/a/options/roots/0",
                "/a/options/roots/1",
                "/a/query",
            ],
            [leaf.path for leaf in leaves],
        )
        self.assertEqual(
            body,
            reconstruct_skill_region_body(BoundaryShapeTermKind.INPUT_VALUE, leaves),
        )

    def test_root_scalar_round_trips(self) -> None:
        leaves = normalize_skill_region_body(
            BoundaryShapeTermKind.OUTPUT_VALUE,
            "complete",
        )

        self.assertEqual(["/d"], [leaf.path for leaf in leaves])
        self.assertEqual(
            "complete",
            reconstruct_skill_region_body(BoundaryShapeTermKind.OUTPUT_VALUE, leaves),
        )

    def test_reference_region_preserves_reference_polarity(self) -> None:
        leaves = normalize_skill_region_body(
            BoundaryShapeTermKind.OUTPUT_REFERENCE,
            {"artifact": "file://report.txt"},
        )

        self.assertEqual(1, len(leaves))
        self.assertIs(SkillLeafCarrierKind.REFERENCE, leaves[0].carrier_kind)
        self.assertIs(SkillLeafClass.REFERENCE, leaves[0].leaf_class)

    def test_opaque_value_marks_region_non_reconstructible(self) -> None:
        document = synthesized_skill_normalization(
            input_values={"opaque": b"payload"},
            output_values={},
        )

        region = document["regions"]["a"]
        self.assertFalse(region["reconstructible"])
        self.assertEqual("opaque", region["leaves"][0]["leaf_class"])
        self.assertEqual("bytes", region["leaves"][0]["value"]["opaque_type"])

    def test_imported_payload_is_canonicalized(self) -> None:
        normalized = normalized_skill_normalization_payload(
            {
                "regions": {
                    "a": {
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/query",
                                "carrier_kind": "value",
                                "data_type": "string",
                                "semantic_label": "query",
                                "value": "force",
                                "leaf_class": "scalar",
                            }
                        ]
                    }
                }
            }
        )

        self.assertEqual(SKILL_NORMALIZATION_VERSION, normalized["normalization_version"])
        self.assertEqual(SKILL_PATH_NOTATION_VERSION, normalized["path_notation_version"])
        self.assertEqual("String", normalized["regions"]["a"]["leaves"][0]["data_type"])

    def test_invalid_region_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalized_skill_normalization_payload(
                {"regions": {"unsupported": {"leaves": []}}}
            )

    def test_reconstruction_rejects_leaves_from_another_region(self) -> None:
        output_leaves = normalize_skill_region_body(
            BoundaryShapeTermKind.OUTPUT_VALUE,
            {"answer": "complete"},
        )

        with self.assertRaises(ValueError):
            reconstruct_skill_region_body(
                BoundaryShapeTermKind.INPUT_VALUE,
                output_leaves,
            )


if __name__ == "__main__":
    unittest.main()
