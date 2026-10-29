from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "skill_semantics"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_skill_semantics"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class SkillSemanticsDistributionTests(unittest.TestCase):
    def test_project_declares_only_the_semantic_contract_dependency(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]

        self.assertEqual("realized-skill-semantics", project["name"])
        self.assertEqual(
            ["realized-core-semantics==0.1.0"],
            project["dependencies"],
        )

    def test_package_has_no_repository_root_or_upper_layer_imports(self) -> None:
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        unexpected = imported - sys.stdlib_module_names - {
            "realized_core_semantics",
            "realized_skill_semantics",
        }

        self.assertEqual(set(), unexpected)

    def test_typed_package_files_are_present(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "composition.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "compatibility.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "declaration.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "execution.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "invocation.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "ir.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "leaves.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "normalization.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "paths.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "py.typed").is_file())

    def test_workspace_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "skill_semantics", workspace["tool"]["uv"]["workspace"]["members"]
        )
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-skill-semantics"],
        )
        self.assertIn("uv build skill_semantics", cloud_build)
        self.assertIn("skill_semantics.tests.test_api", cloud_build)
        self.assertIn("skill_semantics.tests.test_composition", cloud_build)
        self.assertIn("skill_semantics.tests.test_declaration", cloud_build)
        self.assertIn("skill_semantics.tests.test_distribution", cloud_build)
        self.assertIn("skill_semantics.tests.test_execution", cloud_build)
        self.assertIn("skill_semantics.tests.test_invocation", cloud_build)
        self.assertIn("skill_semantics.tests.test_ir", cloud_build)
        self.assertIn("skill_semantics.tests.test_normalization", cloud_build)
        self.assertIn("--skill-semantics-wheel", cloud_build)
        self.assertIn("--skill-semantics-sdist", cloud_build)


if __name__ == "__main__":
    unittest.main()
