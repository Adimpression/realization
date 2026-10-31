#!/usr/bin/env python3
"""Inventory and enforce repository-root compatibility-facade use."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import subprocess
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
TEXT_REFERENCE_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".jsonl",
    ".md",
    ".rst",
    ".sh",
    ".spec",
    ".toml",
    ".yaml",
    ".yml",
}
REFERENCE_SCAN_EXCLUDES = {
    "COMPATIBILITY_FACADE_RETIREMENT_IMPLEMENTATION.md",
    "architecture/DEPENDENCY_REPORT.md",
    "architecture/compatibility-facade-contracts.json",
    "architecture/compatibility-facade-policy.json",
    "architecture/compatibility-facades.json",
}
RETIREMENT_STATES = {
    "candidate",
    "consumers_migrated",
    "deprecated",
    "held",
    "qualified",
    "retained",
}
SUPPORT_STATUSES = {
    "repository_internal",
    "retained_aggregate_api",
    "supported_executable_path",
    "supported_historical_import",
}
DURABLE_QUALIFIED_NAME_STATUSES = {
    "clear",
    "migration_required",
    "retained",
    "unreviewed",
}
IMPORT_OBLIGATIONS = {"none", "repository_only", "supported"}
EXECUTABLE_OBLIGATIONS = {"none", "repository_only", "supported"}
FACADE_SHAPES = {
    "aggregate_reexport",
    "behavior_adapter",
    "exact_module_alias",
    "symbol_reexport",
}
REFERENCE_DISPOSITIONS = {
    "architecture_evidence",
    "compatibility_evidence",
    "durable_provenance_evidence",
    "durable_runtime_reference",
    "historical_narrative",
    "runnable_guidance",
    "runtime_reference",
}
BLOCKING_REFERENCE_DISPOSITIONS = {
    "durable_runtime_reference",
    "runnable_guidance",
    "runtime_reference",
}
DURABLE_REFERENCE_SUFFIXES = {
    ".db",
    ".jsonl",
    ".pickle",
    ".pkl",
    ".sqlite",
    ".sqlite3",
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


def _counts_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _relative(path: Path, root: Path) -> str:
    return path.absolute().relative_to(root.absolute()).as_posix()


def _is_skipped(path: Path, root: Path) -> bool:
    relative = path.absolute().relative_to(root.absolute())
    return any(part in SKIPPED_PARTS for part in relative.parts)


def _python_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.py")):
        if path.is_file() and not _is_skipped(path, root):
            yield path


def _call_name(function: ast.expr) -> str:
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        prefix = _call_name(function.value)
        return f"{prefix}.{function.attr}" if prefix else function.attr
    return ""


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.partition(".")[0]
                aliases[local_name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _resolved_call_name(function: ast.expr, aliases: dict[str, str]) -> str:
    name = _call_name(function)
    head, separator, tail = name.partition(".")
    resolved_head = aliases.get(head, head)
    return f"{resolved_head}.{tail}" if separator else resolved_head


def _python_import_package(path: Path) -> str:
    parts: list[str] = []
    current = path.parent
    while (current / "__init__.py").is_file():
        parts.append(current.name)
        current = current.parent
    return ".".join(reversed(parts))


def _module_references(
    tree: ast.AST,
    *,
    import_package: str = "",
) -> list[tuple[str, int, str]]:
    references: set[tuple[str, int, str]] = set()
    aliases = _import_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            references.update(
                (alias.name, node.lineno, "import") for alias in node.names
            )
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                references.add((node.module, node.lineno, "from_import"))
            elif node.level and import_package:
                relative_name = "." * node.level + (node.module or "")
                try:
                    resolved = importlib.util.resolve_name(
                        relative_name,
                        import_package,
                    )
                except (ImportError, ValueError):
                    continue
                references.add((resolved, node.lineno, "relative_from_import"))
            continue
        if not isinstance(node, ast.Call) or not node.args:
            continue
        first_argument = node.args[0]
        if not isinstance(first_argument, ast.Constant) or not isinstance(
            first_argument.value, str
        ):
            continue
        function = node.func
        function_name = _resolved_call_name(function, aliases)
        is_dynamic_import = function_name in {"__import__", "importlib.import_module"}
        if is_dynamic_import:
            references.add(
                (first_argument.value, node.lineno, "dynamic_import")
            )
        elif function_name == "patch" or function_name.endswith(".patch"):
            references.add((first_argument.value, node.lineno, "patch_target"))
    return sorted(references, key=lambda row: (row[1], row[0], row[2]))


def _parsed_references(path: Path) -> list[tuple[str, int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return _module_references(
        tree,
        import_package=_python_import_package(path),
    )


def _is_sys_modules_alias(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if not isinstance(target, ast.Subscript):
            continue
        value = target.value
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "modules"
            and isinstance(value.value, ast.Name)
            and value.value.id == "sys"
        ):
            return True
    return False


def _sys_modules_alias_binding(node: ast.AST) -> str:
    if not _is_sys_modules_alias(node):
        return ""
    value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
    return value.id if isinstance(value, ast.Name) else ""


def _is_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    comparison = node.test
    if len(comparison.ops) != 1 or not isinstance(comparison.ops[0], ast.Eq):
        return False
    values = [comparison.left, *comparison.comparators]
    return any(
        isinstance(value, ast.Name) and value.id == "__name__" for value in values
    ) and any(
        isinstance(value, ast.Constant) and value.value == "__main__"
        for value in values
    )


def _synthesizes_export_surface(node: ast.AST) -> bool:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return False
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if not any(
        isinstance(target, ast.Name) and target.id == "__all__"
        for target in targets
    ):
        return False
    value = node.value
    return value is not None and any(
        isinstance(child, (ast.ListComp, ast.SetComp))
        or (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "globals"
        )
        for child in ast.walk(value)
    )


def _canonical_target(
    module: str,
    module_prefixes: list[tuple[str, str]],
) -> tuple[str, str] | None:
    for prefix, component in module_prefixes:
        if module == prefix or module.startswith(prefix + "."):
            return component, module
    return None


def _facade_source_observations(
    path: Path,
    module_prefixes: list[tuple[str, str]],
) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    has_definition = any(
        isinstance(node, (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef))
        for node in tree.body
    )
    has_module_alias = any(_is_sys_modules_alias(node) for node in tree.body)
    imported_module_bindings: dict[str, str] = {}
    canonical_targets: set[tuple[str, str]] = set()
    canonical_exports: set[tuple[str, str, str, str]] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_module_bindings[alias.asname or alias.name.partition(".")[0]] = (
                    alias.name
                )
                target = _canonical_target(alias.name, module_prefixes)
                if target is not None:
                    canonical_targets.add(target)
            continue
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or not node.module:
            continue
        target = _canonical_target(node.module, module_prefixes)
        for alias in node.names:
            if alias.name != "*":
                imported_module_bindings[alias.asname or alias.name] = (
                    f"{node.module}.{alias.name}"
                )
        if target is None:
            continue
        canonical_targets.add(target)
        component, module = target
        for alias in node.names:
            if alias.name == "*":
                continue
            canonical_exports.add(
                (component, module, alias.name, alias.asname or alias.name)
            )
    if has_definition:
        shape = "behavior_adapter"
    elif has_module_alias:
        shape = "exact_module_alias"
    elif any(_synthesizes_export_surface(node) for node in tree.body):
        shape = "aggregate_reexport"
    else:
        shape = "symbol_reexport"
    alias_binding = next(
        (
            binding
            for node in tree.body
            if (binding := _sys_modules_alias_binding(node))
        ),
        "",
    )
    return {
        "canonical_module_identity": imported_module_bindings.get(alias_binding, ""),
        "canonical_exports": [
            {
                "component": component,
                "exported_name": exported_name,
                "module": module,
                "source_name": source_name,
            }
            for component, module, source_name, exported_name in sorted(
                canonical_exports
            )
        ],
        "canonical_targets": canonical_targets,
        "executable_surface": any(_is_main_guard(node) for node in tree.body),
        "shape": shape,
    }


def _load_retirement_policy(
    root: Path,
    manifest: dict[str, Any],
    facade_names: set[str],
) -> dict[str, Any]:
    configured_path = manifest.get("compatibility_policy_path")
    if not configured_path:
        raise ValueError("compatibility_policy_path is missing from the manifest")
    policy_path = root / str(configured_path)
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse compatibility policy: {exc}") from exc
    if policy.get("schema_version") != 2:
        raise ValueError("unsupported compatibility policy schema version")
    defaults = policy.get("defaults")
    overrides = policy.get("facades")
    tombstones = policy.get("tombstones")
    designated_tests = policy.get("designated_contract_tests")
    durable_pickle_facades = policy.get("durable_pickle_facades")
    if not isinstance(defaults, dict):
        raise ValueError("compatibility policy defaults must be an object")
    if not isinstance(overrides, dict):
        raise ValueError("compatibility policy facades must be an object")
    if not isinstance(tombstones, dict):
        raise ValueError("compatibility policy tombstones must be an object")
    if not isinstance(designated_tests, list) or not all(
        isinstance(path, str) for path in designated_tests
    ):
        raise ValueError("designated contract tests must be a list of paths")
    if not isinstance(durable_pickle_facades, list) or not all(
        isinstance(module, str) for module in durable_pickle_facades
    ):
        raise ValueError("durable pickle facades must be a list of module names")
    unknown_durable_pickle_facades = sorted(
        set(durable_pickle_facades) - facade_names
    )
    if unknown_durable_pickle_facades:
        raise ValueError(
            "compatibility policy contains unknown durable pickle facades: "
            + ", ".join(unknown_durable_pickle_facades)
        )
    unknown_overrides = sorted(set(overrides) - facade_names)
    if unknown_overrides:
        raise ValueError(
            "compatibility policy contains unknown active facades: "
            + ", ".join(unknown_overrides)
        )
    reintroduced = sorted(
        module
        for module in tombstones
        if module in facade_names or (root / f"{module}.py").exists()
    )
    if reintroduced:
        raise ValueError(
            "removed compatibility facades were reintroduced: "
            + ", ".join(reintroduced)
        )
    required_tombstone_fields = {
        "removal_change_reference",
        "removed_at",
        "replacement",
    }
    for module, tombstone in tombstones.items():
        if not isinstance(tombstone, dict):
            raise ValueError(f"tombstone for {module} must be an object")
        missing = sorted(required_tombstone_fields - set(tombstone))
        if missing:
            raise ValueError(
                f"tombstone for {module} is missing: " + ", ".join(missing)
            )
    for module, override in overrides.items():
        if not isinstance(override, dict):
            raise ValueError(f"policy for {module} must be an object")
    return policy


def _effective_facade_policy(
    policy: dict[str, Any],
    facade: str,
) -> dict[str, Any]:
    effective = dict(policy["defaults"])
    durable_pickle_contract = facade in policy["durable_pickle_facades"]
    if durable_pickle_contract:
        effective.update(
            {
                "durable_qualified_name_status": "retained",
                "hold_reason": (
                    "Executable compatibility evidence proves historical "
                    "protocol-zero pickle globals for this facade."
                ),
                "retirement_state": "held",
                "review_condition": (
                    "Advance only after old pickle material is migrated or "
                    "the qualified-name compatibility obligation is explicitly "
                    "retired with migration guidance and qualification."
                ),
            }
        )
    override = policy["facades"].get(facade, {})
    effective.update(override)
    state = effective.get("retirement_state")
    support = effective.get("support_status")
    durable_status = effective.get("durable_qualified_name_status")
    import_obligation = effective.get("import_obligation")
    executable_obligation = effective.get("executable_obligation")
    if state not in RETIREMENT_STATES:
        raise ValueError(f"invalid retirement state for {facade}: {state!r}")
    if support not in SUPPORT_STATUSES:
        raise ValueError(f"invalid support status for {facade}: {support!r}")
    if durable_status not in DURABLE_QUALIFIED_NAME_STATUSES:
        raise ValueError(
            f"invalid durable-qualified-name status for {facade}: "
            f"{durable_status!r}"
        )
    if import_obligation not in IMPORT_OBLIGATIONS:
        raise ValueError(
            f"invalid import obligation for {facade}: {import_obligation!r}"
        )
    if executable_obligation not in EXECUTABLE_OBLIGATIONS:
        raise ValueError(
            f"invalid executable obligation for {facade}: "
            f"{executable_obligation!r}"
        )
    hold_reason = effective.get("hold_reason")
    if not isinstance(hold_reason, str) or not hold_reason.strip():
        raise ValueError(f"compatibility policy requires a hold reason for {facade}")
    review_condition = effective.get("review_condition")
    if not isinstance(review_condition, str) or not review_condition.strip():
        raise ValueError(
            f"compatibility policy requires a review condition for {facade}"
        )
    effective["policy_source"] = (
        "override"
        if override
        else "durable_pickle_contract"
        if durable_pickle_contract
        else "default"
    )
    return effective


def _reference_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_skipped(path, root):
            continue
        relative = _relative(path, root)
        if relative in REFERENCE_SCAN_EXCLUDES:
            continue
        if path.suffix == ".py" or path.suffix in TEXT_REFERENCE_SUFFIXES:
            yield path


def _text_reference_scope(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve())
    if path.suffix in DURABLE_REFERENCE_SUFFIXES:
        return "durable_material"
    if "tests" in relative.parts or path.name.startswith("test_"):
        return "test"
    if relative.parts[0] == "trials":
        return "trial"
    if relative.parts[0] == "scripts":
        return "tooling"
    if relative.parts[0] == "architecture":
        return "architecture_documentation"
    if path.suffix == ".md":
        return "documentation"
    if path.suffix in {".json", ".spec", ".toml", ".yaml", ".yml"}:
        return "configuration_or_fixture"
    return "other_repository_reference"


def _reference_disposition(
    *,
    path: Path,
    root: Path,
    reference_kind: str,
    inside_code_fence: bool,
    inside_documentation_text: bool = False,
) -> str:
    scope = _text_reference_scope(path, root)
    if reference_kind == "pickle_global":
        return "durable_runtime_reference"
    if inside_documentation_text:
        return "historical_narrative"
    if scope == "architecture_documentation":
        return "architecture_evidence"
    if scope == "test":
        return "compatibility_evidence"
    if scope == "documentation":
        if inside_code_fence or reference_kind in {
            "entrypoint_reference",
            "module_invocation",
            "python_file_invocation",
            "textual_import",
        }:
            return "runnable_guidance"
        return "historical_narrative"
    if scope == "trial":
        if path.suffix in {".json", ".jsonl", ".yaml", ".yml"} and reference_kind in {
            "entrypoint_reference",
            "textual_import",
        }:
            return "durable_runtime_reference"
        if path.suffix in {".md", ".rst"}:
            if inside_code_fence or reference_kind in {
                "entrypoint_reference",
                "module_invocation",
                "python_file_invocation",
                "textual_import",
            }:
                return "runnable_guidance"
            return "historical_narrative"
        return "runtime_reference"
    if scope == "durable_material":
        if (
            path.suffix == ".jsonl"
            and "reports" in path.absolute().relative_to(root.absolute()).parts
            and reference_kind != "pickle_global"
        ):
            # Checked-in receipts preserve what a historical run observed. Their
            # escaped paths and tracebacks are evidence, not replayed imports.
            return "durable_provenance_evidence"
        return "durable_runtime_reference"
    if scope == "configuration_or_fixture" and reference_kind in {
        "entrypoint_reference",
        "textual_import",
    }:
        return "durable_runtime_reference"
    return "runtime_reference"


def _python_docstring_lines(path: Path) -> set[int]:
    if path.suffix != ".py":
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return set()
    lines: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        expression = body[0]
        if not (
            isinstance(expression, ast.Expr)
            and isinstance(expression.value, ast.Constant)
            and isinstance(expression.value.value, str)
        ):
            continue
        lines.update(
            range(expression.lineno, (expression.end_lineno or expression.lineno) + 1)
        )
    return lines


def _textual_references(
    path: Path,
    root: Path,
    facade_names: set[str],
) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeError:
        return []
    alternatives = "|".join(
        re.escape(name) for name in sorted(facade_names, key=lambda name: (-len(name), name))
    )
    patterns = [
        (
            "module_file_path",
            re.compile(
                rf"(?<![A-Za-z0-9_/])(?P<facade>{alternatives})\.py"
                rf"(?![A-Za-z0-9_])"
            ),
        ),
        (
            "python_file_invocation",
            re.compile(
                rf"\bpython(?:3(?:\.\d+)*)?\s+(?:-[^\s]+\s+)*"
                rf"(?:[^\s'\"]+/)?(?P<facade>{alternatives})\.py"
                rf"(?![A-Za-z0-9_])"
            ),
        ),
        (
            "module_invocation",
            re.compile(
                rf"\bpython(?:3(?:\.\d+)*)?\s+(?:-[^\s]+\s+)*-m\s+"
                rf"(?P<facade>{alternatives})(?![A-Za-z0-9_.])"
            ),
        ),
    ]
    if path.suffix != ".py":
        patterns.extend(
            [
                (
                    "textual_import",
                    re.compile(
                        rf"(?:^|\\n)\s*(?:from|import)\s+"
                        rf"(?P<facade>{alternatives})"
                        rf"(?![A-Za-z0-9_])"
                    ),
                ),
                (
                    "entrypoint_reference",
                    re.compile(
                        rf"(?<![A-Za-z0-9_.])(?P<facade>{alternatives}):"
                        rf"[A-Za-z_][A-Za-z0-9_]*"
                    ),
                ),
                (
                    "pickle_global",
                    re.compile(
                        rf"(?:^|[^A-Za-z0-9_])c(?P<facade>{alternatives})"
                        rf"(?:\\n|\n)[A-Za-z_][A-Za-z0-9_]*"
                    ),
                ),
            ]
        )
    findings: set[tuple[str, int, str, bool]] = set()
    docstring_lines = _python_docstring_lines(path)
    inside_code_fence = False
    fence_marker = ""
    for line_number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if path.suffix in {".md", ".rst"} and stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not inside_code_fence:
                inside_code_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                inside_code_fence = False
                fence_marker = ""
            continue
        for reference_kind, pattern in patterns:
            for match in pattern.finditer(line):
                findings.add(
                    (
                        match.group("facade"),
                        line_number,
                        reference_kind,
                        inside_code_fence,
                    )
                )
    python_invocations = {
        (facade, line)
        for facade, line, reference_kind, _inside_code_fence in findings
        if reference_kind == "python_file_invocation"
    }
    findings = {
        finding
        for finding in findings
        if not (
            finding[2] == "module_file_path"
            and (finding[0], finding[1]) in python_invocations
        )
    }
    scope = _text_reference_scope(path, root)
    relative = _relative(path, root)
    return [
        {
            "disposition": _reference_disposition(
                path=path,
                root=root,
                reference_kind=reference_kind,
                inside_code_fence=inside_code_fence,
                inside_documentation_text=(
                    line in docstring_lines or lines[line - 1].lstrip().startswith("#")
                ),
            ),
            "facade": facade,
            "inside_code_fence": inside_code_fence,
            "line": line,
            "path": relative,
            "reference_kind": reference_kind,
            "scope": scope,
        }
        for facade, line, reference_kind, inside_code_fence in sorted(
            findings,
            key=lambda row: (row[1], row[0], row[2], row[3]),
        )
    ]


def _repository_text_references(
    root: Path,
    facade_names: set[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in _reference_paths(root):
        findings.extend(_textual_references(path, root, facade_names))
    findings.extend(_tracked_durable_references(root, facade_names))
    unique = {
        (
            row["facade"],
            row["line"],
            row["path"],
            row["reference_kind"],
        ): row
        for row in findings
    }
    return sorted(
        unique.values(),
        key=lambda row: (
            row["path"],
            row["line"],
            row["facade"],
            row["reference_kind"],
        ),
    )


def _tracked_durable_references(
    root: Path,
    facade_names: set[str],
) -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    paths = [
        root / raw_path.decode("utf-8")
        for raw_path in completed.stdout.split(b"\0")
        if raw_path
    ]
    findings: list[dict[str, Any]] = []
    alternatives = "|".join(
        re.escape(name)
        for name in sorted(facade_names, key=lambda name: (-len(name), name))
    )
    binary_patterns = (
        (
            "pickle_global",
            re.compile(
                rb"(?:^|[^A-Za-z0-9_])c(?P<facade>"
                + alternatives.encode("ascii")
                + rb")\n[A-Za-z_][A-Za-z0-9_]*"
            ),
        ),
        (
            "textual_import",
            re.compile(
                rb"(?:^|\\n|\n)\s*(?:from|import)\s+(?P<facade>"
                + alternatives.encode("ascii")
                + rb")(?![A-Za-z0-9_])"
            ),
        ),
        (
            "entrypoint_reference",
            re.compile(
                rb"(?<![A-Za-z0-9_.])(?P<facade>"
                + alternatives.encode("ascii")
                + rb"):[A-Za-z_][A-Za-z0-9_]*"
            ),
        ),
    )
    for path in sorted(paths):
        if not path.is_file() or path.suffix not in DURABLE_REFERENCE_SUFFIXES:
            continue
        if path.suffix == ".jsonl":
            findings.extend(_textual_references(path, root, facade_names))
            continue
        try:
            content = path.read_bytes()
        except OSError:
            continue
        for reference_kind, pattern in binary_patterns:
            for match in pattern.finditer(content):
                findings.append(
                    {
                        "disposition": "durable_runtime_reference",
                        "facade": match.group("facade").decode("ascii"),
                        "inside_code_fence": False,
                        "line": 0,
                        "path": _relative(path, root),
                        "reference_kind": reference_kind,
                        "scope": "durable_material",
                    }
                )
    return findings


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


def _retirement_assessment(
    *,
    facade: str,
    facade_policy: dict[str, Any],
    executable_surface: bool,
    shape: str,
    static_consumers: list[dict[str, Any]],
    text_references: list[dict[str, Any]],
    designated_contract_tests: set[str],
    qualification: dict[str, Any],
) -> dict[str, Any]:
    non_contract_consumers = [
        consumer
        for consumer in static_consumers
        if consumer["path"] not in designated_contract_tests
    ]
    blocking_text_references = [
        reference
        for reference in text_references
        if reference["disposition"] in BLOCKING_REFERENCE_DISPOSITIONS
        and reference["path"] not in designated_contract_tests
    ]
    hold_reasons: list[str] = []
    state = facade_policy["retirement_state"]
    if state != "qualified":
        hold_reasons.append(f"retirement state is {state}, not qualified")
    if facade_policy["durable_qualified_name_status"] != "clear":
        hold_reasons.append(
            "durable qualified-name review is "
            + facade_policy["durable_qualified_name_status"]
        )
    if non_contract_consumers:
        hold_reasons.append(
            f"{len(non_contract_consumers)} repository consumers remain"
        )
    if blocking_text_references:
        hold_reasons.append(
            f"{len(blocking_text_references)} active non-import references remain"
        )
    if (
        executable_surface
        and facade_policy["executable_obligation"] == "none"
    ):
        hold_reasons.append(
            "executable surface has no explicit compatibility obligation"
        )
    if (
        facade_policy["support_status"].startswith("supported_")
        and not facade_policy.get("notice_reference")
    ):
        hold_reasons.append("supported surface has no documented removal notice")
    if qualification["retirement_hold"]:
        hold_reasons.append("minimum stable qualification cycles are incomplete")
    if shape in {"aggregate_reexport", "behavior_adapter"}:
        hold_reasons.append(f"{shape} requires an explicit replacement proof")
    if hold_reasons:
        hold_reasons.insert(0, facade_policy["hold_reason"])
    return {
        "blocking_text_reference_count": len(blocking_text_references),
        "eligible_for_deletion": not hold_reasons,
        "hold_reasons": hold_reasons,
        "non_contract_consumer_count": len(non_contract_consumers),
        "text_reference_count": len(text_references),
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
    retirement_policy = _load_retirement_policy(root, manifest, facade_names)
    designated_contract_tests = set(
        retirement_policy["designated_contract_tests"]
    )
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
    qualification = _qualification_cycle_status(root, manifest)

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

    repository_text_references = _repository_text_references(root, facade_names)
    text_references_by_facade: dict[str, list[dict[str, Any]]] = {
        facade: [] for facade in facade_names
    }
    for reference in repository_text_references:
        text_references_by_facade[reference["facade"]].append(
            {
                key: value
                for key, value in reference.items()
                if key != "facade"
            }
        )

    facades: list[dict[str, Any]] = []
    for facade in sorted(facade_names):
        path = root / f"{facade}.py"
        source_observations = _facade_source_observations(path, module_prefixes)
        canonical_targets: set[tuple[str, str]] = set(
            source_observations["canonical_targets"]
        )
        root_dependencies: set[str] = set()
        for module, _line, _kind in _parsed_references(path):
            imported_root = module.partition(".")[0]
            if imported_root in root_metadata and imported_root != facade:
                root_dependencies.add(imported_root)
            target = _canonical_target(module, module_prefixes)
            if target is not None:
                canonical_targets.add(target)
        static_consumers = sorted(
            consumers[facade],
            key=lambda row: (
                row["path"],
                row["line"],
                row["import_kind"],
            ),
        )
        facade_policy = _effective_facade_policy(retirement_policy, facade)
        text_references = text_references_by_facade[facade]
        retirement_assessment = _retirement_assessment(
            facade=facade,
            facade_policy=facade_policy,
            executable_surface=source_observations["executable_surface"],
            shape=source_observations["shape"],
            static_consumers=static_consumers,
            text_references=text_references,
            designated_contract_tests=designated_contract_tests,
            qualification=qualification,
        )
        facades.append(
            {
                "canonical_exports": source_observations["canonical_exports"],
                "canonical_module_identity": source_observations[
                    "canonical_module_identity"
                ],
                "canonical_targets": [
                    {"component": component, "module": module}
                    for component, module in sorted(canonical_targets)
                ],
                "durable_qualified_name_status": facade_policy[
                    "durable_qualified_name_status"
                ],
                "earliest_removal_condition": facade_policy[
                    "earliest_removal_condition"
                ],
                "executable_surface": source_observations["executable_surface"],
                "hold_reason": facade_policy["hold_reason"],
                "import_obligation": facade_policy["import_obligation"],
                "last_consumer_scan_evidence": facade_policy[
                    "last_consumer_scan_evidence"
                ],
                "last_qualification_evidence": facade_policy[
                    "last_qualification_evidence"
                ],
                "module": facade,
                "notice_reference": facade_policy["notice_reference"],
                "owner": root_metadata[facade]["owner"],
                "path": f"{facade}.py",
                "policy_source": facade_policy["policy_source"],
                "replacement_commands": facade_policy.get(
                    "replacement_commands", []
                ),
                "review_condition": facade_policy["review_condition"],
                "retirement_assessment": retirement_assessment,
                "retirement_state": facade_policy["retirement_state"],
                "root_dependencies": sorted(root_dependencies),
                "shape": source_observations["shape"],
                "static_consumers": static_consumers,
                "support_status": facade_policy["support_status"],
                "executable_obligation": facade_policy[
                    "executable_obligation"
                ],
                "text_references": text_references,
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
    shape_counts = {
        shape: sum(facade["shape"] == shape for facade in facades)
        for shape in sorted(FACADE_SHAPES)
    }
    retirement_candidates = [
        facade["module"]
        for facade in facades
        if facade["retirement_assessment"]["eligible_for_deletion"]
    ]
    retirement_holds = [
        {
            "hold_reasons": facade["retirement_assessment"]["hold_reasons"],
            "module": facade["module"],
        }
        for facade in facades
        if not facade["retirement_assessment"]["eligible_for_deletion"]
    ]
    all_static_consumers = [
        consumer
        for facade in facades
        for consumer in facade["static_consumers"]
    ]
    all_text_references = [
        reference
        for facade in facades
        for reference in facade["text_references"]
    ]
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
        "retirement_candidates": retirement_candidates,
        "retirement_holds": retirement_holds,
        "retirement_policy": {
            "designated_contract_tests": sorted(designated_contract_tests),
            "path": str(manifest["compatibility_policy_path"]),
            "tombstone_count": len(retirement_policy["tombstones"]),
            "tombstones": retirement_policy["tombstones"],
        },
        "schema_version": 2,
        "summary": {
            "canonical_package_consumer_count": len(canonical_consumers),
            "eligible_retirement_candidate_count": len(retirement_candidates),
            "facade_count": len(facades),
            "facade_contract_consumer_count": sum(
                consumer["path"] in designated_contract_tests
                for consumer in all_static_consumers
            ),
            "public_documentation_reference_count": len(public_references),
            "public_example_consumer_count": len(example_consumers),
            "shape_counts": shape_counts,
            "static_consumer_count": len(all_static_consumers),
            "static_consumer_kind_counts": _counts_by(
                all_static_consumers, "import_kind"
            ),
            "static_consumer_scope_counts": _counts_by(
                all_static_consumers, "scope"
            ),
            "text_reference_count": len(repository_text_references),
            "text_reference_kind_counts": _counts_by(
                all_text_references, "reference_kind"
            ),
            "text_reference_disposition_counts": _counts_by(
                all_text_references, "disposition"
            ),
            "text_reference_scope_counts": _counts_by(
                all_text_references, "scope"
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
    invalid_qualified = [
        facade["module"]
        for facade in current["facades"]
        if facade["retirement_state"] == "qualified"
        and not facade["retirement_assessment"]["eligible_for_deletion"]
    ]
    if invalid_qualified:
        errors.append(
            "facades are marked qualified while deletion holds remain: "
            + ", ".join(invalid_qualified)
        )
    return errors


def _consumer_observation_keys(inventory: dict[str, Any]) -> set[tuple[str, ...]]:
    keys: set[tuple[str, ...]] = set()
    for facade in inventory.get("facades", []):
        module = str(facade["module"])
        for consumer in facade.get("static_consumers", []):
            keys.add(
                (
                    "consumer",
                    module,
                    str(consumer["path"]),
                    str(consumer["scope"]),
                    str(consumer["import_kind"]),
                )
            )
        for reference in facade.get("text_references", []):
            keys.add(
                (
                    "text_reference",
                    module,
                    str(reference["path"]),
                    str(reference["scope"]),
                    str(reference["reference_kind"]),
                )
            )
    return keys


def _new_observation_errors(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> list[str]:
    if int(previous.get("schema_version", 0)) < 2:
        return []
    designated_tests = set(
        current["retirement_policy"]["designated_contract_tests"]
    )
    previous_keys = _consumer_observation_keys(previous)
    additions = sorted(
        key
        for key in _consumer_observation_keys(current) - previous_keys
        if key[2] not in designated_tests
    )
    return [
        "new facade observation is not allowed: " + " | ".join(key)
        for key in additions
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the checked-in inventory with the current measured state",
    )
    parser.add_argument(
        "--accept-observation-expansion",
        action="store_true",
        help=(
            "with --update, accept reviewed observations introduced by a "
            "deliberate scanner expansion; ordinary updates remain shrink-only"
        ),
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
    if args.json:
        print(_canonical_json(inventory), end="")
    expected: dict[str, Any] | None = None
    if inventory_path.is_file():
        try:
            expected = json.loads(inventory_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"cannot read compatibility inventory: {exc}", file=sys.stderr)
            return 2
    if args.update:
        if expected is not None:
            expansion_errors = _new_observation_errors(inventory, expected)
            if expansion_errors and not args.accept_observation_expansion:
                print(
                    "compatibility facade observation expansion detected:",
                    file=sys.stderr,
                )
                for error in expansion_errors:
                    print(f"- {error}", file=sys.stderr)
                return 1
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(_canonical_json(inventory), encoding="utf-8")
        expected = inventory
    elif args.accept_observation_expansion:
        print(
            "--accept-observation-expansion requires --update",
            file=sys.stderr,
        )
        return 2
    if expected is None:
        print(
            f"compatibility inventory is missing: {_relative(inventory_path, root)}; "
            "run with --update",
            file=sys.stderr,
        )
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
            f"{summary['text_reference_count']} text references, "
            f"{summary['canonical_package_consumer_count']} canonical package consumers, "
            f"{summary['public_documentation_reference_count']} public README references, "
            f"{summary['public_example_consumer_count']} public example consumers"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
