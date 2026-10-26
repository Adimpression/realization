# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from applied_theory_types import Artifact, BoundaryShapeTerm
from realized_skill_semantics.leaves import SkillLeaf, SkillLeafCarrierKind
from realized_skill_semantics.normalization import (
    normalize_skill_region_body,
    reconstruct_skill_region_body,
)
from skill_boundary_normalization import synthesized_skill_normalization_for_artifact


def _artifact(*, name: str, content: dict[str, object], kind: str = "ability") -> Artifact:
    return Artifact.from_dict(
        {
            "id": f"artifact-{name}",
            "title": name.replace("_", " ").title(),
            "artifact_type": kind,
            "representation": "yaml",
            "content": content,
        }
    )


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

    def test_artifact_adapter_preserves_explicit_contract_precedence(self) -> None:
        artifact = _artifact(
            name="explicit_contracts",
            content={
                "input_contract": {"explicit_in": "E"},
                "output_contract": {"explicit_out": "O"},
                "skill_declaration": {
                    "inputs": {"declared_in": "D"},
                    "outputs": {"declared_out": "D"},
                },
                "answer": "fallback",
            },
        )

        document = synthesized_skill_normalization_for_artifact(artifact)

        self.assertEqual(
            {
                "normalization_version": "bssc.skill.normalization.v1",
                "path_notation_version": "bssc.skill.path.v1",
                "regions": {
                    "a": {
                        "boundary_term": "a*",
                        "carrier_kind": "value",
                        "reconstructible": True,
                        "leaves": [
                            {
                                "region": "a*",
                                "path": "/a/explicit_in",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "explicit_in",
                                "value": "E",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "a'": {
                        "boundary_term": "a'*",
                        "carrier_kind": "reference",
                        "reconstructible": True,
                        "leaves": [],
                    },
                    "b": {
                        "boundary_term": "b*",
                        "carrier_kind": "value",
                        "reconstructible": True,
                        "leaves": [],
                    },
                    "b'": {
                        "boundary_term": "b'*",
                        "carrier_kind": "reference",
                        "reconstructible": True,
                        "leaves": [],
                    },
                    "c": {
                        "boundary_term": "c*",
                        "carrier_kind": "value",
                        "reconstructible": True,
                        "leaves": [],
                    },
                    "c'": {
                        "boundary_term": "c'*",
                        "carrier_kind": "reference",
                        "reconstructible": True,
                        "leaves": [],
                    },
                    "d": {
                        "boundary_term": "d*",
                        "carrier_kind": "value",
                        "reconstructible": True,
                        "leaves": [
                            {
                                "region": "d*",
                                "path": "/d/explicit_out",
                                "carrier_kind": "value",
                                "data_type": "String",
                                "semantic_label": "explicit_out",
                                "value": "O",
                                "leaf_class": "scalar",
                            }
                        ],
                    },
                    "d'": {
                        "boundary_term": "d'*",
                        "carrier_kind": "reference",
                        "reconstructible": True,
                        "leaves": [],
                    },
                },
            },
            document,
        )

    def test_artifact_adapter_preserves_declaration_fallback(self) -> None:
        artifact = _artifact(
            name="declaration_fallback",
            content={
                "skill_declaration": {
                    "inputs": {"declared_in": "D"},
                    "outputs": {"declared_out": "D"},
                }
            },
        )

        document = synthesized_skill_normalization_for_artifact(artifact)

        self.assertEqual(
            ("/a/declared_in", "D"),
            (
                document["regions"]["a"]["leaves"][0]["path"],
                document["regions"]["a"]["leaves"][0]["value"],
            ),
        )
        self.assertEqual(
            ("/d/declared_out", "D"),
            (
                document["regions"]["d"]["leaves"][0]["path"],
                document["regions"]["d"]["leaves"][0]["value"],
            ),
        )

    def test_artifact_adapter_preserves_answer_fallback(self) -> None:
        artifact = _artifact(
            name="answer_fallback",
            kind="knowledge",
            content={
                "answer": "F = m * a",
                "skill_declaration": {
                    "intent": "Answer",
                    "inputs": {},
                    "outputs": {},
                },
            },
        )

        document = synthesized_skill_normalization_for_artifact(artifact)

        self.assertEqual([], document["regions"]["a"]["leaves"])
        self.assertEqual(
            [
                {
                    "region": "d*",
                    "path": "/d/answer",
                    "carrier_kind": "value",
                    "data_type": "String",
                    "semantic_label": "answer",
                    "value": "F = m * a",
                    "leaf_class": "scalar",
                }
            ],
            document["regions"]["d"]["leaves"],
        )

    def test_artifact_adapter_preserves_legacy_default_declaration(self) -> None:
        artifact = _artifact(name="empty", content={})

        document = synthesized_skill_normalization_for_artifact(artifact)

        self.assertEqual(
            ("/a/payload", "execution input"),
            (
                document["regions"]["a"]["leaves"][0]["path"],
                document["regions"]["a"]["leaves"][0]["value"],
            ),
        )
        self.assertEqual(
            ("/d/result", "execution result"),
            (
                document["regions"]["d"]["leaves"][0]["path"],
                document["regions"]["d"]["leaves"][0]["value"],
            ),
        )


if __name__ == "__main__":
    unittest.main()
