#!/usr/bin/env python3
"""Build and import every UV workspace distribution outside the repository."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from typing import Any
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "architecture" / "boundaries.toml"
BOUNDARY_SCRIPT = REPO_ROOT / "scripts" / "check_architecture_boundaries.py"


def _load_boundary_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_realized_workspace_distribution_boundaries",
        BOUNDARY_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load architecture checker: {BOUNDARY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BOUNDARIES = _load_boundary_module()


def _module_references(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module)
            continue
        if not isinstance(node, ast.Call) or not node.args:
            continue
        argument = node.args[0]
        if not isinstance(argument, ast.Constant) or not isinstance(
            argument.value, str
        ):
            continue
        function = node.func
        is_dynamic = isinstance(function, ast.Name) and function.id == "__import__"
        is_dynamic = is_dynamic or (
            isinstance(function, ast.Attribute)
            and function.attr == "import_module"
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
        )
        if is_dynamic:
            modules.add(argument.value)
    return modules


def _facade_names(analysis: dict[str, Any]) -> set[str]:
    return {
        row["module"]
        for row in analysis["baseline"]["root_module_ownership"]
        if "compatibility_facade" in row["statuses"]
    }


def _wheel_facade_imports(
    wheel: Path,
    facade_names: set[str],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    with zipfile.ZipFile(wheel) as archive:
        for entry in sorted(archive.namelist()):
            if not entry.endswith(".py") or ".dist-info/" in entry:
                continue
            source = archive.read(entry).decode("utf-8")
            tree = ast.parse(source, filename=f"{wheel.name}:{entry}")
            for module in sorted(_module_references(tree)):
                facade = module.partition(".")[0]
                if facade in facade_names:
                    findings.append(
                        {
                            "facade": facade,
                            "module": module,
                            "path": entry,
                            "wheel": wheel.name,
                        }
                    )
    return findings


def _build_project(project_path: Path, output: Path) -> tuple[Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "uv",
            "build",
            "--no-build-isolation",
            str(project_path),
            "--out-dir",
            str(output),
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"distribution build failed for {project_path}:\n{completed.stdout}"
        )
    wheels = sorted(output.glob("*.whl"))
    sdists = sorted(output.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"expected one wheel and one sdist for {project_path}; "
            f"found {len(wheels)} wheels and {len(sdists)} sdists"
        )
    with tarfile.open(sdists[0], mode="r:gz") as archive:
        if not archive.getmembers():
            raise RuntimeError(f"empty source distribution: {sdists[0]}")
    return wheels[0], sdists[0]


def _install_wheels(wheels: list[Path], site_root: Path) -> None:
    seen: dict[str, tuple[str, bytes]] = {}
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            for entry in sorted(archive.namelist()):
                if entry.endswith("/"):
                    continue
                content = archive.read(entry)
                prior = seen.get(entry)
                if prior is not None and prior[1] != content:
                    raise RuntimeError(
                        f"wheels contain conflicting {entry}: "
                        f"{prior[0]} and {wheel.name}"
                    )
                seen[entry] = (wheel.name, content)
                target = site_root / entry
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)


def _import_public_modules(site_root: Path, module_names: list[str]) -> None:
    program = """
import importlib
import json
from pathlib import Path
import sys

site_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()
modules = json.loads(sys.argv[3])
sys.path.insert(0, str(site_root))
for value in sys.path:
    if not value:
        continue
    if Path(value).resolve() == repo_root:
        raise RuntimeError(f"repository leaked onto sys.path: {value}")
for module in modules:
    importlib.import_module(module)
print(json.dumps({"imported": modules}, sort_keys=True))
"""
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            program,
            str(site_root),
            str(REPO_ROOT),
            json.dumps(module_names),
        ],
        cwd=site_root.parent,
        env={**os.environ, "PYTHONPATH": ""},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            "isolated workspace-distribution import failed:\n" + completed.stdout
        )


def verify_workspace_distributions(
    root: Path,
    manifest_path: Path,
    dist_root: Path,
) -> dict[str, Any]:
    manifest = BOUNDARIES.load_manifest(manifest_path)
    analysis = BOUNDARIES.analyze(root, manifest)
    facade_names = _facade_names(analysis)
    projects = analysis["components"]
    wheels: list[Path] = []
    sdists: list[Path] = []
    forbidden_imports: list[dict[str, str]] = []
    built: list[dict[str, str]] = []
    for component, project in sorted(projects.items()):
        project_path = root / project["project_dir"]
        wheel, sdist = _build_project(project_path, dist_root / component)
        wheels.append(wheel)
        sdists.append(sdist)
        forbidden_imports.extend(_wheel_facade_imports(wheel, facade_names))
        built.append(
            {
                "component": component,
                "module": project["module_prefix"],
                "sdist": sdist.name,
                "wheel": wheel.name,
            }
        )
    if forbidden_imports:
        rendered = "\n".join(
            f"{row['wheel']}:{row['path']} imports {row['module']}"
            for row in forbidden_imports
        )
        raise RuntimeError("built wheels import root compatibility facades:\n" + rendered)
    site_root = dist_root / "isolated-site"
    site_root.mkdir(parents=True, exist_ok=True)
    _install_wheels(wheels, site_root)
    modules = sorted(
        {
            module
            for project in projects.values()
            for module in (
                project["module_prefix"],
                *project.get("distribution_import_modules", []),
            )
        }
    )
    _import_public_modules(site_root, modules)
    return {
        "components": built,
        "facade_imports": forbidden_imports,
        "imported_modules": modules,
        "schema_version": 1,
        "sdist_count": len(sdists),
        "wheel_count": len(wheels),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dist-root", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    root = REPO_ROOT if manifest_path == DEFAULT_MANIFEST else manifest_path.parent.parent
    try:
        if args.dist_root is None:
            with tempfile.TemporaryDirectory(
                prefix="realized-workspace-distributions-"
            ) as temporary:
                result = verify_workspace_distributions(
                    root,
                    manifest_path,
                    Path(temporary),
                )
        else:
            dist_root = args.dist_root.resolve()
            if dist_root.exists() and any(dist_root.iterdir()):
                raise RuntimeError(f"distribution output is not empty: {dist_root}")
            dist_root.mkdir(parents=True, exist_ok=True)
            result = verify_workspace_distributions(root, manifest_path, dist_root)
    except (OSError, RuntimeError, SyntaxError, ValueError) as exc:
        print(f"workspace distribution verification failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "workspace distribution verification passed: "
            f"{result['wheel_count']} wheels, {result['sdist_count']} sdists, "
            f"{len(result['imported_modules'])} isolated public-module imports"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
