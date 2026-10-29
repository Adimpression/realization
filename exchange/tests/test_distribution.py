from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "exchange"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "realized_exchange"


def _import_roots(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


class ExchangeDistributionTests(unittest.TestCase):
    def test_package_imports_only_declared_dependencies(self) -> None:
        project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["project"]
        declared = {
            "yaml",
            "realized_core_engine",
            "realized_core_governance",
            "realized_core_runtime",
            "realized_core_semantics",
            "realized_exchange",
            "realized_skill_application",
            "realized_skill_semantics",
            "workstation",
        }
        imported = {
            root
            for path in PACKAGE_ROOT.glob("*.py")
            for root in _import_roots(path)
        }
        self.assertEqual(set(), imported - sys.stdlib_module_names - declared)
        self.assertEqual("realized-exchange", project["name"])

    def test_package_contains_all_exchange_modules(self) -> None:
        expected = {
            "__init__.py",
            "artifact_yaml.py",
            "compatibility_export.py",
            "compatibility_import.py",
            "compiler.py",
            "dependencies.py",
            "learning_context.py",
            "learning_context_skills.py",
            "markdown_learning_pipeline.py",
            "py.typed",
            "registry.py",
            "run_bundle.py",
            "skill_export.py",
            "skill_schema.py",
            "workstation.py",
        }
        self.assertEqual(expected, {path.name for path in PACKAGE_ROOT.iterdir() if path.is_file()})


if __name__ == "__main__":
    unittest.main()
