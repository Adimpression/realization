from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "core_governance"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_core_governance"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class CoreGovernanceDistributionTests(unittest.TestCase):
    def test_project_declares_only_lower_semantic_dependencies(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]

        self.assertEqual("realized-core-governance", project["name"])
        self.assertEqual(
            [
                "realized-core-semantics==0.1.0",
                "realized-skill-semantics==0.1.0",
            ],
            project["dependencies"],
        )

    def test_package_has_no_repository_root_or_upper_layer_imports(self) -> None:
        imported = {
            root for path in PACKAGE_ROOT.glob("*.py") for root in _import_roots(path)
        }
        unexpected = imported - sys.stdlib_module_names - {
            "realized_core_governance",
            "realized_core_semantics",
            "realized_skill_semantics",
        }

        self.assertEqual(set(), unexpected)

    def test_typed_package_files_are_present(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "_normalization.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "admission.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "approval.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "data.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "declarations.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "inventory.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "lifecycle.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "records.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "safety.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "vocabulary.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "py.typed").is_file())

    def test_workspace_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn(
            "core_governance", workspace["tool"]["uv"]["workspace"]["members"]
        )
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-governance"],
        )
        self.assertIn("uv build core_governance", cloud_build)
        self.assertIn("core_governance.tests.test_admission", cloud_build)
        self.assertIn("core_governance.tests.test_api", cloud_build)
        self.assertIn("core_governance.tests.test_approval", cloud_build)
        self.assertIn("core_governance.tests.test_data", cloud_build)
        self.assertIn("core_governance.tests.test_declarations", cloud_build)
        self.assertIn("core_governance.tests.test_distribution", cloud_build)
        self.assertIn("core_governance.tests.test_inventory", cloud_build)
        self.assertIn("core_governance.tests.test_lifecycle", cloud_build)
        self.assertIn("core_governance.tests.test_records", cloud_build)
        self.assertIn("core_governance.tests.test_safety", cloud_build)
        self.assertIn("core_governance.tests.test_vocabulary", cloud_build)
        self.assertIn("--governance-wheel", cloud_build)
        self.assertIn("--governance-sdist", cloud_build)


if __name__ == "__main__":
    unittest.main()
