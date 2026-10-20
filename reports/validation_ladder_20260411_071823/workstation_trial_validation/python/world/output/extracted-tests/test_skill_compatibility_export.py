# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from skill_compatibility_export import (
    instruction_skill_bundle_from_artifact,
    mcp_tool_definition_from_skill_artifact,
    openai_tool_definition_from_skill_artifact,
)
from skill_schema_io import artifact_from_skill_document


class SkillCompatibilityExportTests(unittest.TestCase):
    def test_openai_tool_export_projects_inputs_from_canonical_skill(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Repo Search",
                "description": ["Search the repository for a symbol."],
                "inputs": {
                    "symbol": "required symbol to find",
                    "root": "workspace root",
                },
                "compatibility": {
                    "adapters": [
                        {"direction": "import", "format": "openai_tool", "name": "repo_search"}
                    ]
                },
            }
        )

        exported = openai_tool_definition_from_skill_artifact(artifact)

        self.assertEqual(exported["type"], "function")
        self.assertEqual(exported["function"]["name"], "repo_search")
        self.assertEqual(exported["function"]["parameters"]["required"], ["symbol"])
        self.assertIn("root", exported["function"]["parameters"]["properties"])

    def test_mcp_tool_export_projects_input_schema_from_canonical_skill(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "ability",
                "title": "Read File",
                "description": ["Read a file from the workspace."],
                "inputs": {
                    "path": "required relative file path",
                },
                "compatibility": {
                    "adapters": [
                        {"direction": "import", "format": "mcp_tool", "name": "read_file"}
                    ]
                },
            }
        )

        exported = mcp_tool_definition_from_skill_artifact(artifact)

        self.assertEqual(exported["name"], "read_file")
        self.assertEqual(exported["inputSchema"]["required"], ["path"])
        self.assertEqual(
            exported["inputSchema"]["properties"]["path"]["description"],
            "required relative file path",
        )

    def test_instruction_skill_export_uses_answer_when_present(self) -> None:
        artifact = artifact_from_skill_document(
            {
                "schema": "bssc_skill.v1",
                "kind": "knowledge",
                "title": "Repo Checks",
                "answer": "Run the narrow test slice before widening validation.",
            }
        )

        exported = instruction_skill_bundle_from_artifact(artifact)

        self.assertEqual(exported["format"], "instruction_skill_bundle")
        self.assertEqual(exported["title"], "Repo Checks")
        self.assertEqual(
            exported["instructions"],
            "Run the narrow test slice before widening validation.",
        )


if __name__ == "__main__":
    unittest.main()
