from __future__ import annotations

import ast
from collections import deque
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ENGINE_ROOT = REPO_ROOT / "core_engine"


def _manifest_modules() -> list[str]:
    return [
        line
        for raw_line in (CORE_ENGINE_ROOT / "module_manifest.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    ]


def _root_imports(path: Path) -> set[str]:
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(syntax):
        if isinstance(node, ast.Import):
            imports.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.partition(".")[0])
    return imports


def _canonical_engine_closure() -> set[str]:
    local_modules = {
        path.stem: path
        for path in REPO_ROOT.glob("*.py")
        if path.name != "__init__.py"
    }
    pending = deque(["controller_runtime", "system_state", "args"])
    closure: set[str] = set()
    while pending:
        module_name = pending.popleft()
        if module_name in closure or module_name not in local_modules:
            continue
        closure.add(module_name)
        for imported in sorted(_root_imports(local_modules[module_name])):
            if imported in local_modules and imported not in closure:
                pending.append(imported)
    return closure


class CoreEngineDistributionTests(unittest.TestCase):
    def test_manifest_is_sorted_unique_and_matches_engine_closure(self) -> None:
        modules = _manifest_modules()

        self.assertEqual(sorted(set(modules)), modules)
        self.assertEqual(_canonical_engine_closure(), set(modules))

    def test_manifest_excludes_outer_application_surfaces(self) -> None:
        modules = set(_manifest_modules())

        self.assertNotIn("main", modules)
        self.assertNotIn("controller_entrypoints", modules)
        self.assertFalse(any(module.startswith("workstation") for module in modules))
        self.assertFalse(any("publication" in module for module in modules))

    def test_manifest_imports_only_declared_or_supported_dependencies(self) -> None:
        modules = set(_manifest_modules())
        allowed_external = {
            "openai",
            "pydantic",
            "realized_core_runtime",
            "wasmtime",
            "yaml",
        }
        imported = {
            imported
            for module in modules
            for imported in _root_imports(REPO_ROOT / f"{module}.py")
        }
        unexpected = imported - modules - sys.stdlib_module_names - allowed_external

        self.assertEqual(set(), unexpected)
        self.assertNotIn("workstation", imported)

    def test_project_declares_engine_dependencies_without_an_executable(self) -> None:
        project = tomllib.loads(
            (CORE_ENGINE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        metadata = project["project"]

        self.assertNotIn("scripts", metadata)
        self.assertEqual(
            {
                "openai==2.29.0",
                "pydantic==2.12.5",
                "pyyaml==6.0.3",
                "realized-core-runtime==0.1.0",
            },
            set(metadata["dependencies"]),
        )
        self.assertEqual(
            ["wasmtime==43.0.0"],
            metadata["optional-dependencies"]["wasm"],
        )

    def test_public_abi_is_owned_by_the_engine_package(self) -> None:
        package_root = CORE_ENGINE_ROOT / "src" / "realized_core_engine"
        setup_source = (CORE_ENGINE_ROOT / "setup.py").read_text(encoding="utf-8")

        self.assertTrue((package_root / "__init__.py").is_file())
        self.assertTrue((package_root / "api.py").is_file())
        self.assertTrue((package_root / "contracts.py").is_file())
        self.assertTrue((package_root / "cli_support.py").is_file())
        self.assertIn('packages=["realized_core_engine"]', setup_source)

    def test_build_py_removes_stale_modules_before_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            build_lib = Path(temporary_directory) / "lib"
            build_lib.mkdir()
            stale_module = build_lib / "removed_manifest_module.py"
            stale_module.write_text("SHOULD_NOT_SHIP = True\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "setup.py",
                    "build_py",
                    "--build-lib",
                    str(build_lib),
                ],
                cwd=CORE_ENGINE_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertFalse(stale_module.exists())
            self.assertTrue((build_lib / "controller_runtime.py").is_file())
            self.assertTrue(
                (build_lib / "realized_core_engine" / "api.py").is_file()
            )

    def test_source_distribution_is_self_contained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            subprocess.run(
                [
                    sys.executable,
                    "setup.py",
                    "sdist",
                    "--formats=gztar",
                    "--dist-dir",
                    temporary_directory,
                ],
                cwd=CORE_ENGINE_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            archives = list(Path(temporary_directory).glob("*.tar.gz"))
            self.assertEqual(1, len(archives))
            with tarfile.open(archives[0], mode="r:gz") as archive:
                names = set(archive.getnames())

            prefix = "realized_core_engine-0.1.0"
            self.assertIn(f"{prefix}/module_manifest.txt", names)
            for module in _manifest_modules():
                self.assertIn(
                    f"{prefix}/_canonical_modules/{module}.py",
                    names,
                )

    def test_workspace_and_cloud_build_qualify_the_engine_distribution(self) -> None:
        workspace = tomllib.loads(
            (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        cloud_build = (REPO_ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")

        self.assertIn("core_engine", workspace["tool"]["uv"]["workspace"]["members"])
        self.assertEqual(
            {"workspace": True},
            workspace["tool"]["uv"]["sources"]["realized-core-engine"],
        )
        self.assertIn("uv build --wheel core_engine", cloud_build)
        self.assertIn("core_engine.tests.test_api", cloud_build)
        self.assertIn("core_engine.tests.test_distribution", cloud_build)
        self.assertIn("--engine-wheel", cloud_build)


if __name__ == "__main__":
    unittest.main()
