from __future__ import annotations

import ast
from pathlib import Path
import tomllib
import unittest

import dst
from dst import core, discovery, normalization, orchestration, projection, revision


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = REPO_ROOT / "dst"
PACKAGE_ROOT = PROJECT_ROOT / "src" / "dst"


class DstDistributionTests(unittest.TestCase):
    def test_project_uses_src_layout_and_declares_workspace_dependencies(self) -> None:
        metadata = tomllib.loads(
            (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual("dst", metadata["project"]["name"])
        self.assertEqual(
            [
                "coordinated-transformation==0.1.0",
                "realized-core-semantics==0.1.0",
            ],
            metadata["project"]["dependencies"],
        )
        self.assertEqual(
            {"": "src"}, metadata["tool"]["setuptools"]["package-dir"]
        )
        self.assertEqual(
            ["dst"],
            metadata["tool"]["setuptools"]["packages"]["find"]["include"],
        )

    def test_package_root_has_an_explicit_unique_public_api(self) -> None:
        modules = (core, discovery, normalization, orchestration, projection, revision)
        expected = tuple(name for module in modules for name in module.__all__)

        self.assertEqual(94, len(expected))
        self.assertEqual(94, len(set(expected)))
        self.assertEqual(expected, dst.__all__)
        for module in modules:
            for name in module.__all__:
                with self.subTest(module=module.__name__, name=name):
                    self.assertIs(getattr(dst, name), getattr(module, name))

        syntax = ast.parse(
            (PACKAGE_ROOT / "__init__.py").read_text(encoding="utf-8")
        )
        self.assertFalse(
            any(
                isinstance(node, ast.ImportFrom)
                and any(alias.name == "*" for alias in node.names)
                for node in ast.walk(syntax)
            )
        )

        orchestration_syntax = ast.parse(
            (PACKAGE_ROOT / "orchestration.py").read_text(encoding="utf-8")
        )
        imported_modules = {
            node.module
            for node in ast.walk(orchestration_syntax)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(orchestration_syntax)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        self.assertNotIn("runtime_controller_api", imported_modules)

    def test_distribution_owns_the_runtime_prompt_and_fixture_substrate(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "DST_PROMPT.md").is_file())
        self.assertEqual(PACKAGE_ROOT / "DST_PROMPT.md", normalization.DST_PROMPT_PATH)
        self.assertTrue(normalization.load_dst_prompt_template())
        self.assertEqual(7, len(core.load_dst_use_cases()))
        self.assertTrue(discovery.load_dst_discovery_results())
        self.assertTrue(normalization.load_dst_normalized_cases())

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

        self.assertIn("dst", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertEqual(
            {"workspace": True}, workspace["tool"]["uv"]["sources"]["dst"]
        )
        self.assertEqual(
            {
                "project_dir": "dst",
                "distribution": "dst",
                "module_prefix": "dst",
                "layer": "subject_domain",
                "allowed_dependencies": [
                    "coordinated_transformation",
                    "core_semantics",
                ],
            },
            architecture["components"]["dst"],
        )
        self.assertNotIn(
            "dst",
            architecture.get("root_package_ownership", {}).get(
                "subject_domain", []
            ),
        )
        self.assertIn("uv build dst", cloud_build)
        self.assertIn("-s dst/tests", cloud_build)


if __name__ == "__main__":
    unittest.main()
