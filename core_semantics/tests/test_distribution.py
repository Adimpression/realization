from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "core_semantics"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_core_semantics"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class CoreSemanticsDistributionTests(unittest.TestCase):
    def test_project_declares_only_the_formal_model_dependency(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]

        self.assertEqual("realized-core-semantics", project["name"])
        self.assertEqual(["pydantic==2.12.5"], project["dependencies"])

    def test_package_has_no_repository_root_or_upper_layer_imports(self) -> None:
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        unexpected = imported - sys.stdlib_module_names - {
            "pydantic",
            "realized_core_semantics",
        }

        self.assertEqual(set(), unexpected)

    def test_typed_package_files_are_present(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "applied_model.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "applied_primitives.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "artifacts.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "boundary.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "decision_review.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "executors.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "identifiers.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "itemization.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "markdown.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "normalization.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "prolog.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "proposals.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "semantic_text.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "theory.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "title_semantics.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "transformation_constructs.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "values.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "py.typed").is_file())

    def test_workspace_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "core_semantics", workspace["tool"]["uv"]["workspace"]["members"]
        )
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-semantics"],
        )
        self.assertIn("uv build core_semantics", cloud_build)
        self.assertIn("core_semantics.tests.test_api", cloud_build)
        self.assertIn("core_semantics.tests.test_distribution", cloud_build)
        self.assertIn("--semantics-wheel", cloud_build)
        self.assertIn("--semantics-sdist", cloud_build)


if __name__ == "__main__":
    unittest.main()
