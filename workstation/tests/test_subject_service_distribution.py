from __future__ import annotations

import ast
from pathlib import Path
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "workstation" / "subject_service"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "workstation" / "subject" / "service"


def _absolute_imports(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imported.add(node.module)
    return imported


class SubjectServiceDistributionTests(unittest.TestCase):
    def test_project_owns_url_capture_and_declares_runtime_dependencies(self) -> None:
        metadata = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertTrue((PACKAGE_ROOT / "url_learning_capture.py").is_file())
        self.assertTrue(
            (PACKAGE_ROOT / "learning_context_persistence.py").is_file()
        )
        self.assertTrue((PACKAGE_ROOT / "learning_context_skills.py").is_file())
        self.assertEqual(
            ["workstation.subject.service"],
            metadata["tool"]["setuptools"]["packages"]["find"]["include"],
        )
        self.assertTrue(
            {"playwright==1.58.0", "trafilatura==2.0.0"}.issubset(
                set(metadata["project"]["dependencies"])
            )
        )

    def test_canonical_url_capture_does_not_import_the_root_facade(self) -> None:
        self.assertNotIn(
            "url_learning_capture",
            _absolute_imports(PACKAGE_ROOT / "url_learning_capture.py"),
        )

    def test_cloud_build_runs_the_subject_service_distribution_guard(self) -> None:
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "workstation.tests.test_subject_service_distribution",
            cloud_build,
        )


if __name__ == "__main__":
    unittest.main()
