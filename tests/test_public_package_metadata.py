from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PACKAGES = {
    "core_app": "realized-core",
    "core_conversation": "realized-core-conversation",
    "core_engine": "realized-core-engine",
    "core_governance": "realized-core-governance",
    "core_llm": "realized-core-llm",
    "core_runtime": "realized-core-runtime",
    "core_semantics": "realized-core-semantics",
    "host_interaction": "realized-host-interaction",
    "skill_semantics": "realized-skill-semantics",
}


class PublicPackageMetadataTests(unittest.TestCase):
    def test_core_distributions_have_consistent_public_metadata(self) -> None:
        canonical_license = (REPO_ROOT / "LICENSE").read_bytes()
        for directory, expected_name in PUBLIC_PACKAGES.items():
            with self.subTest(directory=directory):
                root = REPO_ROOT / directory
                project = tomllib.loads(
                    (root / "pyproject.toml").read_text(encoding="utf-8")
                )["project"]
                self.assertEqual(expected_name, project["name"])
                self.assertEqual("Apache-2.0", project["license"])
                self.assertEqual(["LICENSE"], project["license-files"])
                self.assertTrue(project["authors"])
                self.assertTrue(project["maintainers"])
                self.assertEqual(
                    "https://github.com/Adimpression/realization",
                    project["urls"]["Repository"],
                )
                self.assertIn(
                    "Development Status :: 3 - Alpha", project["classifiers"]
                )
                self.assertNotIn(
                    "License :: OSI Approved :: Apache Software License",
                    project["classifiers"],
                )
                self.assertEqual(canonical_license, (root / "LICENSE").read_bytes())


if __name__ == "__main__":
    unittest.main()
