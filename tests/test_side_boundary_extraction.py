# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest
from unittest.mock import patch

import side
from applied_theory_types import Artifact
from semantic_text import ordered_unique


class SideBoundaryExtractionTests(unittest.TestCase):
    def test_local_ordered_unique_helper_matches_existing_semantics(self) -> None:
        values = [" force ", "mass", "force", "", "  ", "mass", "acceleration"]

        self.assertEqual(ordered_unique(values), side._ordered_unique_text(values))

    def test_export_description_no_longer_loads_the_main_runtime(self) -> None:
        artifact = Artifact.from_dict(
            {
                "id": "artifact-force",
                "artifact_type": "knowledge",
                "title": "Force",
                "representation": "text",
                "function_bit": 0,
                "scope": "local",
                "provenance": [],
                "reusability": "local_reuse",
                "admissibility": "admitted",
                "template_schema": {},
                "learning_relation": "new_family",
                "related_artifact_ids": [],
                "content": {"question": "What is force?"},
                "justification": " What is force? ",
            }
        )

        with patch.object(side, "_runtime", side_effect=AssertionError("main loaded")):
            self.assertEqual(
                ["What is force?", "Knowledge artifact for: What is force?"],
                side.artifact_export_description(artifact),
            )


if __name__ == "__main__":
    unittest.main()
