# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_exchange.compiler import compile_skill_document, compiled_skill_summary_from_artifact


class SkillCompilerTests(unittest.TestCase):
    def test_compile_skill_document_emits_canonical_analysis_for_python_ability(self) -> None:
        compiled = compile_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                "aliases": ["Read Text File"],
                "executor": "python3",
                "inputs": {
                    "mount": "required input value",
                    "relative_path": "required input value",
                },
                "outputs": {"result": "execution result"},
                "python": (
                    "def main(mount: str, relative_path: str, __dependencies__: tuple[str, ...] = ()):\n"
                    "    return {'status': 'read', 'mount': mount, 'relative_path': relative_path}\n"
                ),
            }
        )

        self.assertEqual(compiled.analysis["executor_framework"], "python3")
        self.assertEqual(compiled.analysis["representation"], "python_script")
        self.assertIn("a", compiled.analysis["normalized_regions"])
        self.assertIn("d", compiled.analysis["normalized_regions"])
        self.assertGreater(compiled.analysis["normalization_leaf_counts"]["a"], 0)
        self.assertTrue(compiled.warnings)

    def test_compiled_skill_summary_from_artifact_includes_family_and_alias_count(self) -> None:
        compiled = compile_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Symbol Search Commands 03 — Find Python Class Definition / Symbol Search Commands 03 Find Python Class Definition",
                "aliases": ["Find Python Class Definition"],
                "executor": "bash",
                "inputs": {"root": "required input value", "symbol": "required input value"},
                "outputs": {"result": "execution result"},
                "shell": "printf '%s\\n' \"$symbol\"",
            }
        )

        summary = compiled_skill_summary_from_artifact(compiled.artifact)

        self.assertEqual(summary["schema"], "bssc_skill.v1")
        self.assertEqual(summary["kind"], "ability")
        self.assertEqual(summary["alias_count"], 2)
        self.assertEqual(
            summary["family"],
            {
                "label": "Symbol Search Commands",
                "key": "symbol search commands",
                "ordinal": "03",
                "variant": "Find Python Class Definition",
            },
        )
        self.assertIn("a", summary["normalized_regions"])
