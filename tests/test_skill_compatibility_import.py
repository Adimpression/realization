# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_exchange.compatibility_import import (
    canonical_skill_document_from_instruction_skill_bundle,
    canonical_skill_document_from_mcp_tool,
    canonical_skill_document_from_openai_tool,
)
from realized_exchange.skill_schema import artifact_from_skill_document


class SkillCompatibilityImportTests(unittest.TestCase):
    def test_openai_tool_import_builds_declaration_only_ability(self) -> None:
        payload = canonical_skill_document_from_openai_tool(
            {
                "type": "function",
                "function": {
                    "name": "repo_search",
                    "description": "Search the repository for a symbol.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "symbol to find"},
                            "root": {"type": "string", "description": "workspace root"},
                        },
                        "required": ["symbol"],
                    },
                },
            }
        )

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.title, "repo_search")
        self.assertEqual(str(artifact.artifact_type.value), "ability")
        self.assertNotIn("python_script", artifact.content)
        self.assertEqual(
            artifact.content.get("input_contract", {}),
            {
                "symbol": "required symbol to find",
                "root": "workspace root",
            },
        )
        self.assertEqual(
            artifact.content.get("skill_compatibility", {}),
            {
                "adapters": [
                    {
                        "direction": "import",
                        "format": "openai_tool",
                        "surface": "function",
                        "name": "repo_search",
                    }
                ]
            },
        )

    def test_mcp_tool_import_builds_declaration_only_ability(self) -> None:
        payload = canonical_skill_document_from_mcp_tool(
            {
                "name": "read_file",
                "description": "Read a file from the workspace.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "relative file path"},
                    },
                    "required": ["path"],
                },
            }
        )

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(artifact.title, "read_file")
        self.assertEqual(str(artifact.artifact_type.value), "ability")
        self.assertEqual(artifact.content.get("input_contract", {}), {"path": "required relative file path"})
        self.assertEqual(
            artifact.content.get("skill_compatibility", {}),
            {
                "adapters": [
                    {
                        "direction": "import",
                        "format": "mcp_tool",
                        "name": "read_file",
                    }
                ]
            },
        )

    def test_instruction_skill_bundle_import_builds_knowledge_skill(self) -> None:
        payload = canonical_skill_document_from_instruction_skill_bundle(
            {
                "format": "codex_instruction_skill",
                "title": "Repo Checks",
                "description": "Repository hygiene instructions.",
                "instructions": "Run the narrow test slice before widening validation.",
            }
        )

        artifact = artifact_from_skill_document(payload)

        self.assertEqual(str(artifact.artifact_type.value), "knowledge")
        self.assertEqual(
            artifact.content.get("answer"),
            "Run the narrow test slice before widening validation.",
        )
        self.assertEqual(
            artifact.content.get("skill_compatibility", {}),
            {
                "adapters": [
                    {
                        "direction": "import",
                        "format": "codex_instruction_skill",
                        "title": "Repo Checks",
                    }
                ]
            },
        )


if __name__ == "__main__":
    unittest.main()
