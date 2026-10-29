from __future__ import annotations

import unittest

from realized_core_semantics.theory import BoundaryShapeTermKind
from realized_skill_semantics import (
    composition,
    compatibility,
    declaration,
    execution,
    invocation,
    ir,
    leaves,
    normalization,
    paths,
)


class SkillSemanticsApiTests(unittest.TestCase):
    def test_package_exports_only_the_cohesive_semantic_modules(self) -> None:
        import realized_skill_semantics

        self.assertEqual(
            [
                "composition",
                "compatibility",
                "declaration",
                "execution",
                "invocation",
                "ir",
                "leaves",
                "normalization",
                "paths",
            ],
            realized_skill_semantics.__all__,
        )
        self.assertIs(realized_skill_semantics.composition, composition)
        self.assertIs(realized_skill_semantics.compatibility, compatibility)
        self.assertIs(realized_skill_semantics.declaration, declaration)
        self.assertIs(realized_skill_semantics.execution, execution)
        self.assertIs(realized_skill_semantics.invocation, invocation)
        self.assertIs(realized_skill_semantics.ir, ir)
        self.assertIs(realized_skill_semantics.leaves, leaves)
        self.assertIs(realized_skill_semantics.normalization, normalization)
        self.assertIs(realized_skill_semantics.paths, paths)

    def test_module_exports_are_explicit_unique_and_resolvable(self) -> None:
        for module in (
            composition,
            compatibility,
            declaration,
            execution,
            invocation,
            ir,
            leaves,
            normalization,
            paths,
        ):
            with self.subTest(module=module.__name__):
                self.assertEqual(len(module.__all__), len(set(module.__all__)))
                for name in module.__all__:
                    self.assertTrue(hasattr(module, name), name)

    def test_boundary_term_is_the_canonical_theory_enum(self) -> None:
        self.assertIs(BoundaryShapeTermKind, leaves.BoundaryShapeTerm)
        self.assertIs(BoundaryShapeTermKind, paths.BoundaryShapeTerm)

    def test_compatibility_envelope_normalization_is_deterministic(self) -> None:
        self.assertEqual(
            {
                "adapters": [
                    {
                        "format": "mcp_tool",
                        "direction": "import",
                        "name": "repo_search",
                    }
                ]
            },
            compatibility.normalized_skill_compatibility_payload(
                {
                    "format": " mcp_tool ",
                    "direction": " import ",
                    "name": " repo_search ",
                }
            ),
        )

    def test_region_normalization_preserves_value_reference_polarity(self) -> None:
        expected = {
            "a": (BoundaryShapeTermKind.INPUT_VALUE, leaves.SkillLeafCarrierKind.VALUE),
            "a'": (BoundaryShapeTermKind.INPUT_REFERENCE, leaves.SkillLeafCarrierKind.REFERENCE),
            "b": (BoundaryShapeTermKind.READ_VALUE, leaves.SkillLeafCarrierKind.VALUE),
            "b'": (BoundaryShapeTermKind.READ_REFERENCE, leaves.SkillLeafCarrierKind.REFERENCE),
            "c": (BoundaryShapeTermKind.WRITE_VALUE, leaves.SkillLeafCarrierKind.VALUE),
            "c'": (BoundaryShapeTermKind.WRITE_REFERENCE, leaves.SkillLeafCarrierKind.REFERENCE),
            "d": (BoundaryShapeTermKind.OUTPUT_VALUE, leaves.SkillLeafCarrierKind.VALUE),
            "d'": (BoundaryShapeTermKind.OUTPUT_REFERENCE, leaves.SkillLeafCarrierKind.REFERENCE),
        }

        for symbol, (term, carrier) in expected.items():
            with self.subTest(symbol=symbol):
                self.assertIs(term, leaves.normalize_skill_boundary_region(symbol))
                self.assertIs(
                    term,
                    leaves.normalize_skill_boundary_region(term.value),
                )
                self.assertEqual(symbol, leaves.skill_boundary_region_symbol(term))
                self.assertIs(carrier, leaves.skill_leaf_carrier_kind_for_region(term))

    def test_leaf_round_trip_has_stable_json_shape(self) -> None:
        leaf = leaves.SkillLeaf(
            region=BoundaryShapeTermKind.OUTPUT_REFERENCE,
            path="/d'/artifact/main",
            carrier_kind=leaves.SkillLeafCarrierKind.REFERENCE,
            data_type="String",
            semantic_label="artifact",
            value={"id": "artifact-1", "rank": (1, 2)},
            leaf_class=leaves.SkillLeafClass.REFERENCE,
        )
        expected = {
            "region": "d'*",
            "path": "/d'/artifact/main",
            "carrier_kind": "reference",
            "data_type": "String",
            "semantic_label": "artifact",
            "value": {"id": "artifact-1", "rank": [1, 2]},
            "leaf_class": "reference",
        }

        self.assertEqual(expected, leaf.to_dict())
        self.assertEqual(
            leaf,
            leaves.SkillLeaf.from_dict(expected | {"value": leaf.value}),
        )

    def test_leaf_type_normalization_retains_the_existing_vocabulary(self) -> None:
        expected = {
            "string": "String",
            "list[int]": "Ints",
            "bytes[]": "Bytess",
            "none": "Null",
            "object": "Opaque",
            "DomainValue": "DomainValue",
            "": "Opaque",
        }

        for raw, normalized in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(
                    normalized,
                    leaves.normalize_skill_leaf_data_type(raw),
                )

    def test_canonical_paths_round_trip_every_region_and_escape_segments(self) -> None:
        for term in BoundaryShapeTermKind:
            path = paths.canonical_skill_path(
                term,
                ["source/file~1", 0, ""],
            )
            parsed_term, parsed_segments = paths.parse_canonical_skill_path(path)

            with self.subTest(term=term):
                self.assertIs(term, parsed_term)
                self.assertEqual(["source/file~1", "0", ""], parsed_segments)

    def test_malformed_canonical_paths_are_rejected(self) -> None:
        for malformed in ("a/query", "/", "/unsupported/query"):
            with self.subTest(path=malformed):
                with self.assertRaises(ValueError):
                    paths.parse_canonical_skill_path(malformed)


if __name__ == "__main__":
    unittest.main()
