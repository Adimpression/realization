from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ENGINE_ROOT = REPO_ROOT / "core_engine"
PACKAGE_ROOT = CORE_ENGINE_ROOT / "src" / "realized_core_engine"


def _root_imports(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.partition(".")[0])
    return imports


class CoreEngineDistributionTests(unittest.TestCase):
    def test_dependency_light_submodule_import_does_not_eagerly_load_api(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import sys; "
                    "import realized_core_engine.learning; "
                    "assert 'realized_core_engine.api' not in sys.modules; "
                    "assert 'controller_runtime' not in sys.modules"
                ),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_source_native_package_imports_only_declared_dependencies(self) -> None:
        allowed_external = {
            "pydantic",
            "realized_core_governance",
            "realized_core_engine",
            "realized_core_llm",
            "realized_core_semantics",
            "realized_core_runtime",
            "realized_skill_semantics",
            "realized_host_interaction",
            "wasmtime",
            "yaml",
        }
        imported = {
            imported
            for path in PACKAGE_ROOT.glob("*.py")
            for imported in _root_imports(path)
        }
        unexpected = imported - sys.stdlib_module_names - allowed_external

        self.assertEqual(set(), unexpected)
        self.assertNotIn("workstation", imported)
        self.assertFalse((CORE_ENGINE_ROOT / "setup.py").exists())
        self.assertFalse((CORE_ENGINE_ROOT / "module_manifest.txt").exists())

    def test_project_declares_engine_dependencies_without_an_executable(self) -> None:
        project = tomllib.loads(
            (CORE_ENGINE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        metadata = project["project"]

        self.assertNotIn("scripts", metadata)
        self.assertEqual(
            {
                "pydantic==2.12.5",
                "pyyaml==6.0.3",
                "realized-core-governance==0.1.0",
                "realized-core-llm==0.1.0",
                "realized-core-semantics==0.1.0",
                "realized-core-runtime==0.1.0",
                "realized-skill-semantics==0.1.0",
                "realized-host-interaction==0.1.0",
            },
            set(metadata["dependencies"]),
        )
        self.assertEqual(
            ["wasmtime==43.0.0"],
            metadata["optional-dependencies"]["wasm"],
        )

    def test_runtime_configuration_does_not_own_entry_parser_vocabulary(self) -> None:
        configuration = (
            PACKAGE_ROOT / "configuration.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("def parse_args", configuration)
        self.assertNotIn("workstation-", configuration)
        self.assertNotIn("artifact-export", configuration)
        self.assertNotIn("run-bundle", configuration)
        self.assertNotIn("validation-ladder", configuration)

    def test_public_abi_is_owned_by_the_engine_package(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "__init__.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "api.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "contracts.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "constitutional_trace.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "controller_runtime.py").is_file())
        self.assertTrue(
            (PACKAGE_ROOT / "markdown_learning_artifact_semantics.py").is_file()
        )
        self.assertTrue((PACKAGE_ROOT / "persistence.py").is_file())
        self.assertTrue((PACKAGE_ROOT / "store.py").is_file())
        project = tomllib.loads(
            (CORE_ENGINE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        self.assertEqual({"": "src"}, project["tool"]["setuptools"]["package-dir"])
        self.assertEqual(
            ["realized_core_engine"],
            project["tool"]["setuptools"]["packages"]["find"]["include"],
        )

    def test_source_distribution_is_self_contained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            environment = dict(os.environ)
            environment["UV_CACHE_DIR"] = "/tmp/realized-uv-cache"
            subprocess.run(
                [
                    "uv",
                    "build",
                    "--no-build-isolation",
                    "--sdist",
                    "--out-dir",
                    temporary_directory,
                    "core_engine",
                ],
                cwd=REPO_ROOT,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )

            archives = list(Path(temporary_directory).glob("*.tar.gz"))
            self.assertEqual(1, len(archives))
            with tarfile.open(archives[0], mode="r:gz") as archive:
                names = set(archive.getnames())

            prefix = "realized_core_engine-0.1.0"
            self.assertIn(
                f"{prefix}/src/realized_core_engine/controller_runtime.py",
                names,
            )
            self.assertIn(
                f"{prefix}/src/realized_core_engine/constitutional_trace.py",
                names,
            )
            self.assertIn(
                f"{prefix}/src/realized_core_engine/markdown_learning_artifact_semantics.py",
                names,
            )
            self.assertIn(f"{prefix}/src/realized_core_engine/store.py", names)
            self.assertIn(f"{prefix}/src/realized_core_engine/persistence.py", names)
            self.assertNotIn(f"{prefix}/module_manifest.txt", names)
            self.assertNotIn(f"{prefix}/setup.py", names)

    def test_workspace_and_cloud_build_qualify_the_engine_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("core_engine", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("core_governance", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("core_llm", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("core_semantics", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("skill_semantics", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertIn("host_interaction", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-engine"],
        )
        self.assertIn("uv build core_engine", cloud_build)
        self.assertIn("uv build core_governance", cloud_build)
        self.assertIn("uv build --wheel core_llm", cloud_build)
        self.assertIn("uv build core_semantics", cloud_build)
        self.assertIn("uv build skill_semantics", cloud_build)
        self.assertIn("uv build --wheel host_interaction", cloud_build)
        self.assertIn("core_engine.tests.test_api", cloud_build)
        self.assertIn("core_engine.tests.test_distribution", cloud_build)
        self.assertIn("--engine-wheel", cloud_build)
        self.assertIn("--engine-sdist", cloud_build)
        self.assertIn("--governance-wheel", cloud_build)
        self.assertIn("--llm-wheel", cloud_build)
        self.assertIn("--governance-sdist", cloud_build)
        self.assertIn("--semantics-wheel", cloud_build)
        self.assertIn("--semantics-sdist", cloud_build)
        self.assertIn("--skill-semantics-wheel", cloud_build)
        self.assertIn("--skill-semantics-sdist", cloud_build)
        self.assertIn("--host-interaction-wheel", cloud_build)


if __name__ == "__main__":
    unittest.main()
