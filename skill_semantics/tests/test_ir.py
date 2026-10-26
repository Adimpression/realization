from __future__ import annotations

import unittest

from realized_skill_semantics.ir import (
    CanonicalSkillIR,
    derived_skill_family_metadata_from_title,
    normalized_skill_aliases,
    normalized_skill_family_metadata,
)


class SkillIrTests(unittest.TestCase):
    def test_canonical_ir_has_stable_json_safe_shape(self) -> None:
        value = CanonicalSkillIR(
            artifact_id="artifact-1",
            title="Read Text File",
            schema="bssc_skill.v1",
            kind="ability",
            declaration={"inputs": {"path": "required"}},
            lifecycle={"activation_status": "active"},
            runtime_package_reference={"digest": b"digest"},
            normalization={"regions": {"d": {"rank": (1, 2)}}},
            aliases=["Read File"],
            family={"label": "Python Commands", "key": "python commands"},
            compatibility={"adapters": []},
            hosting_metadata={"virtual_mounts": ["main"]},
        )

        self.assertEqual(
            {
                "artifact_id": "artifact-1",
                "title": "Read Text File",
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "declaration": {"inputs": {"path": "required"}},
                "lifecycle": {"activation_status": "active"},
                "runtime_package_reference": {"digest": "digest"},
                "normalization": {"regions": {"d": {"rank": [1, 2]}}},
                "aliases": ["Read File"],
                "family": {"label": "Python Commands", "key": "python commands"},
                "compatibility": {"adapters": []},
                "hosting_metadata": {"virtual_mounts": ["main"]},
            },
            value.to_dict(),
        )

    def test_aliases_preserve_order_deduplicate_and_include_title_variants(self) -> None:
        self.assertEqual(
            [
                "Read Text File",
                "Python Commands 02 — Read Text File",
                "Python Commands 02 Read Text File",
            ],
            normalized_skill_aliases(
                [
                    " Read\tText\nFile ",
                    "Read Text File",
                    "Python Commands 02 — Read Text File",
                ],
                title=(
                    "Python Commands 02 — Read Text File / "
                    "Python Commands 02 Read Text File"
                ),
            ),
        )
        self.assertEqual([], normalized_skill_aliases(("not", "a", "list")))

    def test_aliases_normalize_control_characters_without_case_folding(self) -> None:
        self.assertEqual(
            ["Mixed Case Alias", "Second Alias"],
            normalized_skill_aliases(
                ["Mixed\x00Case\tAlias"],
                title="Canonical / Second\nAlias",
            ),
        )

    def test_numbered_family_is_derived_from_em_dash_or_hyphen_title(self) -> None:
        expected = {
            "label": "Python Commands",
            "key": "python commands",
            "ordinal": "02",
            "variant": "Read Text File",
        }
        self.assertEqual(
            expected,
            derived_skill_family_metadata_from_title(
                "Python Commands 02 — Read Text File / alternate"
            ),
        )
        self.assertEqual(
            expected,
            derived_skill_family_metadata_from_title(
                "Python Commands 02 - Read Text File"
            ),
        )
        self.assertEqual(
            {},
            derived_skill_family_metadata_from_title("Read Text File"),
        )

    def test_explicit_family_metadata_precedes_title_derivation(self) -> None:
        self.assertEqual(
            {
                "label": "Explicit Family",
                "key": "explicit-key",
                "ordinal": "7",
                "variant": "Variant",
            },
            normalized_skill_family_metadata(
                {
                    "label": " Explicit\nFamily ",
                    "key": " explicit-key ",
                    "ordinal": 7,
                    "variant": " Variant ",
                },
                title="Ignored 02 — Title Family",
            ),
        )

    def test_family_accepts_legacy_family_key_and_scalar_value(self) -> None:
        self.assertEqual(
            {"label": "Legacy Family", "key": "legacy family"},
            normalized_skill_family_metadata({"family": "Legacy Family"}),
        )
        self.assertEqual(
            {"label": "Scalar Family", "key": "scalar family"},
            normalized_skill_family_metadata("Scalar Family"),
        )
        self.assertEqual({}, normalized_skill_family_metadata(None))


if __name__ == "__main__":
    unittest.main()
