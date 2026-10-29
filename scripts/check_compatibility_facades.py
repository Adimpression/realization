#!/usr/bin/env python3
"""Inventory and enforce repository-root compatibility-facade use."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "architecture" / "boundaries.toml"
BOUNDARY_SCRIPT = REPO_ROOT / "scripts" / "check_architecture_boundaries.py"
SKIPPED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "generated",
    "reconstructed_product_spec",
    "reports",
}


def _load_boundary_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_realized_architecture_boundaries",
        BOUNDARY_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load architecture checker: {BOUNDARY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BOUNDARIES = _load_boundary_module()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_skipped(path: Path, root: Path) -> bool:
    relative = path.resolve().relative_to(root.resolve())
    return any(part in SKIPPED_PARTS for part in relative.parts)


def _python_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.is_file() and not _is_skipped(path, root):
            yield path


def _module_references(tree: ast.AST) -> list[tuple[str, int, str]]:
    references: set[tuple[str, int, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            references.update(
                (alias.name, node.lineno, "import") for alias in node.names
            )
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                references.add((node.module, node.lineno, "from_import"))
            continue
        if not isinstance(node, ast.Call) or not node.args:
            continue
        first_argument = node.args[0]
        if not isinstance(first_argument, ast.Constant) or not isinstance(
            first_argument.value, str
        ):
            continue
        function = node.func
        is_dynamic_import = isinstance(function, ast.Name) and function.id == "__import__"
        is_dynamic_import = is_dynamic_import or (
            isinstance(function, ast.Attribute)
            and function.attr == "import_module"
            and isinstance(function.value, ast.Name)
            and function.value.id == "importlib"
        )
        if is_dynamic_import:
            references.add(
                (first_argument.value, node.lineno, "dynamic_import")
            )
    return sorted(references, key=lambda row: (row[1], row[0], row[2]))


def _parsed_references(path: Path) -> list[tuple[str, int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return _module_references(tree)


def _component_for_path(
    path: Path,
    component_roots: list[tuple[Path, str]],
) -> str | None:
    resolved = path.resolve()
    for source_root, component in component_roots:
        if resolved.is_relative_to(source_root):
            return component
    return None


def _consumer_kind(
    path: Path,
    root: Path,
    component_roots: list[tuple[Path, str]],
    root_statuses: dict[str, tuple[str, ...]],
) -> tuple[str, str | None]:
    component = _component_for_path(path, component_roots)
    if component is not None:
        return "canonical_package", component

    relative = path.resolve().relative_to(root.resolve())
    if len(relative.parts) == 1:
        statuses = set(root_statuses.get(path.stem, ()))
        if "compatibility_facade" in statuses:
            return "compatibility_facade", None
        if "entrypoint" in statuses:
            return "entrypoint", None
        if "validation" in statuses:
            return "validation", None
        return "unclassified_root", None
    if "tests" in relative.parts or path.name.startswith("test_"):
        return "test", None
    if "examples" in relative.parts:
        return "example", None
    if relative.parts[0] == "scripts":
        return "tooling", None
    if relative.parts[0] == "trials":
        return "trial", None
    return "other_repository_code", None


def _public_readme_references(
    root: Path,
    facade_names: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("README.md")):
        if not path.is_file() or _is_skipped(path, root):
            continue
        inside_fence = False
        fence_marker = ""
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.lstrip()
            if stripped.startswith(("```", "~~~")):
                marker = stripped[:3]
                if not inside_fence:
                    inside_fence = True
                    fence_marker = marker
                elif marker == fence_marker:
                    inside_fence = False
                    fence_marker = ""
                continue
            if not inside_fence:
                continue
            candidate = stripped.removeprefix(">>> ")
            try:
                tree = ast.parse(candidate)
            except SyntaxError:
                continue
            for module, _line, import_kind in _module_references(tree):
                facade = module.partition(".")[0]
                if facade in facade_names:
                    findings.append(
                        {
                            "facade": facade,
                            "import_kind": import_kind,
                            "line": line_number,
                            "path": _relative(path, root),
                        }
                    )
    return sorted(
        findings,
        key=lambda row: (row["path"], row["line"], row["facade"]),
    )


def _qualification_cycle_status(
    _root: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    policy = manifest.get("compatibility_retirement", {})
    minimum = int(policy.get("minimum_stable_qualification_cycles", 1))
    completed = int(policy.get("completed_stable_qualification_cycles", 0))
    evidence = str(
        policy.get(
            "qualification_evidence",
            "architecture/qualification-baseline.json",
        )
    )
    return {
        "completed_stable_cycles": completed,
        "evidence": evidence,
        "minimum_stable_cycles": minimum,
        "retirement_hold": completed < minimum,
    }


def build_inventory(root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = BOUNDARIES.load_manifest(manifest_path)
    analysis = BOUNDARIES.analyze(root, manifest)
    baseline = analysis["baseline"]
    root_metadata = {
        row["module"]: row for row in baseline["root_module_ownership"]
    }
    facade_names = {
        module
        for module, row in root_metadata.items()
        if "compatibility_facade" in row["statuses"]
    }
    root_statuses = {
        module: tuple(row["statuses"]) for module, row in root_metadata.items()
    }
    component_roots = sorted(
        (
            (component["source_root"].resolve(), name)
            for name, component in analysis["components"].items()
        ),
        key=lambda row: (-len(row[0].parts), row[1]),
    )
    module_prefixes = sorted(
        (
            (component["module_prefix"], name)
            for name, component in analysis["components"].items()
        ),
        key=lambda row: (-len(row[0]), row[0]),
    )

    consumers: dict[str, list[dict[str, Any]]] = {
        facade: [] for facade in facade_names
    }
    parse_errors: list[dict[str, str]] = []
    for path in _python_paths(root):
        try:
            references = _parsed_references(path)
        except (OSError, SyntaxError, UnicodeError) as exc:
            parse_errors.append({"error": str(exc), "path": _relative(path, root)})
            continue
        kind, component = _consumer_kind(
            path,
            root,
            component_roots,
            root_statuses,
        )
        for module, line, import_kind in references:
            facade = module.partition(".")[0]
            if facade not in facade_names or path == root / f"{facade}.py":
                continue
            consumer = {
                "import_kind": import_kind,
                "line": line,
                "path": _relative(path, root),
                "scope": kind,
            }
            if component is not None:
                consumer["component"] = component
            consumers[facade].append(consumer)

    facades: list[dict[str, Any]] = []
    for facade in sorted(facade_names):
        path = root / f"{facade}.py"
        canonical_targets: set[tuple[str, str]] = set()
        root_dependencies: set[str] = set()
        for module, _line, _kind in _parsed_references(path):
            imported_root = module.partition(".")[0]
            if imported_root in root_metadata and imported_root != facade:
                root_dependencies.add(imported_root)
            for prefix, component in module_prefixes:
                if module == prefix or module.startswith(prefix + "."):
                    canonical_targets.add((component, module))
                    break
        static_consumers = sorted(
            consumers[facade],
            key=lambda row: (
                row["path"],
                row["line"],
                row["import_kind"],
            ),
        )
        facades.append(
            {
                "canonical_targets": [
                    {"component": component, "module": module}
                    for component, module in sorted(canonical_targets)
                ],
                "module": facade,
                "owner": root_metadata[facade]["owner"],
                "path": f"{facade}.py",
                "removal_state": "retained",
                "root_dependencies": sorted(root_dependencies),
                "static_consumers": static_consumers,
                "support_status": "supported_historical_import",
            }
        )

    public_references = _public_readme_references(root, facade_names)
    canonical_consumers = [
        {"facade": facade["module"], **consumer}
        for facade in facades
        for consumer in facade["static_consumers"]
        if consumer["scope"] == "canonical_package"
    ]
    example_consumers = [
        {"facade": facade["module"], **consumer}
        for facade in facades
        for consumer in facade["static_consumers"]
        if consumer["scope"] == "example"
    ]
    qualification = _qualification_cycle_status(root, manifest)
    return {
        "facades": facades,
        "parse_errors": sorted(parse_errors, key=lambda row: row["path"]),
        "policy": {
            "canonical_package_imports_are_forbidden": True,
            "facade_removal_requires_a_separate_change": True,
            "public_examples_must_use_canonical_apis": True,
            "supported_import_removal_requires_documented_notice": True,
        },
        "public_documentation_facade_references": public_references,
        "public_example_facade_consumers": example_consumers,
        "qualification": qualification,
        "schema_version": 1,
        "summary": {
            "canonical_package_consumer_count": len(canonical_consumers),
            "facade_count": len(facades),
            "public_documentation_reference_count": len(public_references),
            "public_example_consumer_count": len(example_consumers),
            "static_consumer_count": sum(
                len(facade["static_consumers"]) for facade in facades
            ),
        },
    }


def compare_inventory(current: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if current != expected:
        errors.append("checked-in compatibility inventory is stale")
    if current["parse_errors"]:
        errors.append("compatibility inventory encountered Python parse errors")
    if current["summary"]["canonical_package_consumer_count"]:
        errors.append("canonical package code imports a root compatibility facade")
    if current["summary"]["public_documentation_reference_count"]:
        errors.append("public README examples import a root compatibility facade")
    if current["summary"]["public_example_consumer_count"]:
        errors.append("repository examples import a root compatibility facade")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the checked-in inventory with the current measured state",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    root = REPO_ROOT if manifest_path == DEFAULT_MANIFEST else manifest_path.parent.parent
    try:
        manifest = BOUNDARIES.load_manifest(manifest_path)
        inventory = build_inventory(root, manifest_path)
    except (OSError, RuntimeError, SyntaxError, ValueError) as exc:
        print(f"compatibility inventory error: {exc}", file=sys.stderr)
        return 2
    inventory_path = args.inventory
    if inventory_path is None:
        inventory_path = root / manifest["compatibility_inventory_path"]
    elif not inventory_path.is_absolute():
        inventory_path = root / inventory_path
    if args.update:
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(_canonical_json(inventory), encoding="utf-8")
    if args.json:
        print(_canonical_json(inventory), end="")
    if not inventory_path.is_file():
        print(
            f"compatibility inventory is missing: {_relative(inventory_path, root)}; "
            "run with --update",
            file=sys.stderr,
        )
        return 2
    try:
        expected = json.loads(inventory_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"cannot read compatibility inventory: {exc}", file=sys.stderr)
        return 2
    errors = compare_inventory(inventory, expected)
    if errors:
        print("compatibility facade regressions detected:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if not args.json:
        summary = inventory["summary"]
        print(
            "compatibility facade inventory passed: "
            f"{summary['facade_count']} facades, "
            f"{summary['static_consumer_count']} static consumers, "
            f"{summary['canonical_package_consumer_count']} canonical package consumers, "
            f"{summary['public_documentation_reference_count']} public README references, "
            f"{summary['public_example_consumer_count']} public example consumers"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
