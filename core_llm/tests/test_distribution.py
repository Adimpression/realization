from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "core_llm"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_core_llm"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class CoreLLMDistributionTests(unittest.TestCase):
    def test_project_owns_the_only_provider_sdk_dependency(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]

        self.assertEqual("realized-core-llm", project["name"])
        self.assertEqual(["openai==2.29.0"], project["dependencies"])

    def test_package_has_no_governance_controller_or_workstation_imports(self) -> None:
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        unexpected = imported - sys.stdlib_module_names - {
            "openai",
            "realized_core_llm",
        }

        self.assertEqual(set(), unexpected)

    def test_typed_package_files_are_present(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "planning.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "provider.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "transport.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "py.typed").is_file())

    def test_workspace_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("core_llm", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-llm"],
        )
        self.assertIn("uv build --wheel core_llm", cloud_build)
        self.assertIn("core_llm.tests.test_distribution", cloud_build)
        self.assertIn("core_llm.tests.test_planning_contract", cloud_build)
        self.assertIn("core_llm.tests.test_provider", cloud_build)
        self.assertIn("core_llm.tests.test_transport", cloud_build)
        self.assertIn("--llm-wheel", cloud_build)


if __name__ == "__main__":
    unittest.main()
