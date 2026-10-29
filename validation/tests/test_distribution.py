from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "validation"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_validation"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class ValidationDistributionTests(unittest.TestCase):
    def test_package_is_dependency_free_and_complete(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }

        self.assertEqual("realized-validation", project["name"])
        self.assertEqual([], project["dependencies"])
        self.assertEqual(
            set(), imported - sys.stdlib_module_names - {"realized_validation"}
        )
        self.assertEqual(
            {"__init__.py", "ladder.py", "paths.py", "py.typed", "sqlite_runtime.py"},
            {path.name for path in PACKAGE_ROOT.iterdir() if path.is_file()},
        )

    def test_workspace_and_cloud_build_qualify_validation_support(self) -> None:
        workspace = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("validation", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("uv build validation", cloud_build)
        self.assertIn("validation.tests.test_distribution", cloud_build)


if __name__ == "__main__":
    unittest.main()
