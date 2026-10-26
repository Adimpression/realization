from __future__ import annotations

from collections import UserDict
import unittest

from realized_skill_semantics import declaration


class SkillDeclarationSemanticsTests(unittest.TestCase):
    def test_schema_constants_are_stable(self) -> None:
        self.assertEqual("bssc_skill.v1", declaration.SKILL_SCHEMA_VERSION_V1)
        self.assertEqual("bssc_skill.v2", declaration.SKILL_SCHEMA_VERSION_V2)
        self.assertEqual(
            {"bssc_skill.v1", "bssc_skill.v2"},
            declaration.SKILL_SCHEMA_VERSIONS,
        )

    def test_schema_normalization_preserves_defaults_and_text_cleanup(self) -> None:
        for value in (None, "", False, 0, " \n\t "):
            with self.subTest(value=value):
                self.assertEqual(
                    declaration.SKILL_SCHEMA_VERSION_V1,
                    declaration.normalize_skill_schema_version(value),
                )

        self.assertEqual(
            declaration.SKILL_SCHEMA_VERSION_V2,
            declaration.normalize_skill_schema_version(" bssc_skill.v2\n"),
        )
        self.assertEqual(
            declaration.SKILL_SCHEMA_VERSION_V1,
            declaration.normalize_skill_schema_version("bssc_skill.v1\x14"),
        )

    def test_unknown_schema_version_keeps_the_exact_error(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"^Unsupported skill schema version: bssc_skill\.v3$",
        ):
            declaration.normalize_skill_schema_version(" bssc_skill.v3 ")

    def test_non_mapping_declarations_have_no_composition_targets(self) -> None:
        for value in (None, "", [], ("skill:One",), object()):
            with self.subTest(value=value):
                self.assertEqual([], declaration.composition_binding_targets(value))

    def test_composition_targets_preserve_prefix_order_and_deduplication(self) -> None:
        value = UserDict(
            {
                "composition_rights": [
                    " skill:Reader ",
                    "INVOKE: Writer\n",
                    "title:Reader",
                    "Direct Target",
                    "unsupported:Ignored",
                    "skill: ",
                ]
            }
        )

        self.assertEqual(
            ["Reader", "Writer", "Direct Target"],
            declaration.composition_binding_targets(value),
        )

    def test_scalar_right_and_case_sensitive_targets_are_preserved(self) -> None:
        self.assertEqual(
            ["One"],
            declaration.composition_binding_targets(
                {"composition_rights": " skill:One "}
            ),
        )
        self.assertEqual(
            ["One", "one"],
            declaration.composition_binding_targets(
                {"composition_rights": ["One", "one", "One"]}
            ),
        )

    def test_wildcard_short_circuits_prior_and_later_targets(self) -> None:
        self.assertEqual(
            ["*"],
            declaration.composition_binding_targets(
                {"composition_rights": ["skill:Before", " * ", "skill:After"]}
            ),
        )


if __name__ == "__main__":
    unittest.main()
