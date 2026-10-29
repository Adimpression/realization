from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "coordinated_transformation"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "coordinated_transformation"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class CoordinatedTransformationDistributionTests(unittest.TestCase):
    def test_project_is_dependency_free_and_uses_src_layout(self) -> None:
        metadata = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual("coordinated-transformation", metadata["project"]["name"])
        self.assertEqual([], metadata["project"]["dependencies"])
        self.assertEqual(
            {"": "src"}, metadata["tool"]["setuptools"]["package-dir"]
        )
        self.assertEqual(
            ["coordinated_transformation"],
            metadata["tool"]["setuptools"]["packages"]["find"]["include"],
        )

    def test_package_has_no_repository_root_or_upper_layer_imports(self) -> None:
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        unexpected = imported - sys.stdlib_module_names

        self.assertEqual(set(), unexpected)

    def test_package_and_theory_sources_are_present(self) -> None:
        self.assertTrue((PROJECT_ROOT / "README.md").is_file())
        self.assertEqual(
            "include *.md\n",
            (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8"),
        )
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "core.py").is_file())
        self.assertTrue(
            (
                PROJECT_ROOT
                / "COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY.md"
            ).is_file()
        )
        self.assertTrue(
            (
                PROJECT_ROOT
                / "COORDINATED_TRANSFORMATION_IN_FEDERATED_SYSTEMS_THEORY_IMLEMENTATION.md"
            ).is_file()
        )

    def test_workspace_architecture_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        architecture = tomllib.loads(
            (REPO_ROOT / "architecture" / "boundaries.toml").read_text(
                encoding="utf-8"
            )
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "coordinated_transformation",
            workspace["tool"]["uv"]["workspace"]["members"],
        )
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["coordinated-transformation"],
        )
        self.assertEqual(
            {
                "project_dir": "coordinated_transformation",
                "distribution": "coordinated-transformation",
                "module_prefix": "coordinated_transformation",
                "layer": "subject_domain",
                "allowed_dependencies": [],
            },
            architecture["components"]["coordinated_transformation"],
        )
        self.assertNotIn(
            "coordinated_transformation",
            architecture["root_package_ownership"].get("subject_domain", []),
        )
        self.assertIn("uv build coordinated_transformation", cloud_build)
        self.assertIn("unittest discover", cloud_build)
        self.assertIn("-s coordinated_transformation/tests", cloud_build)


if __name__ == "__main__":
    unittest.main()
