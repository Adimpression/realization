from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "core_runtime"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_core_runtime"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class CoreRuntimeDistributionTests(unittest.TestCase):
    def test_project_declares_only_lower_layer_runtime_dependencies(self) -> None:
        project = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual("realized-core-runtime", project["project"]["name"])
        self.assertEqual(
            {
                "realized-core-governance==0.1.0",
                "realized-core-semantics==0.1.0",
                "realized-host-interaction==0.1.0",
                "realized-skill-semantics==0.1.0",
            },
            set(project["project"]["dependencies"]),
        )
        self.assertEqual(
            ["python_skill_host"],
            project["tool"]["setuptools"]["py-modules"],
        )

    def test_package_has_no_controller_entry_or_workstation_imports(self) -> None:
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        allowed = {
            "realized_core_governance",
            "realized_core_runtime",
            "realized_core_semantics",
            "realized_host_interaction",
            "realized_skill_semantics",
            "wasmtime",
        }

        self.assertEqual(set(), imported - sys.stdlib_module_names - allowed)
        self.assertNotIn("controller_runtime", imported)
        self.assertNotIn("store", imported)
        self.assertNotIn("workstation", imported)

    def test_runtime_execution_surface_is_package_owned(self) -> None:
        required = {
            "execution.py",
            "host_abi.py",
            "host_brokers.py",
            "host_realizers.py",
            "python_host.py",
            "python_transport.py",
            "wasm.py",
        }

        self.assertEqual(set(), required - {path.name for path in PACKAGE_ROOT.glob("*.py")})
        self.assertTrue((PROJECT_ROOT / "src" / "python_skill_host.py").is_file())

    def test_workspace_and_cloud_build_qualify_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("core_runtime", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-runtime"],
        )
        self.assertIn("uv build core_runtime", cloud_build)
        self.assertIn("core_runtime.tests.test_distribution", cloud_build)
        self.assertIn("--runtime-wheel", cloud_build)


if __name__ == "__main__":
    unittest.main()
