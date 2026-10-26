#!/usr/bin/env python3
"""Measure and ratchet uv workspace boundaries without importing the app."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
import tomllib
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "architecture" / "boundaries.toml"
DEPENDENCY_NAME = re.compile(r"^[A-Za-z0-9_.-]+")
ROOT_BOUNDARY_CATEGORIES = {
    "pure_helper",
    "dto_constants",
    "persistence",
    "orchestration",
    "compatibility",
}
ROOT_MODULE_OWNERS = {
    "blend",
    "compatibility",
    "controller",
    "entry_exchange",
    "governance",
    "llm",
    "persistence_adapter",
    "portable_skills",
    "runtime_execution",
    "semantic_model",
    "subject_domain",
    "validation_trial",
}
ROOT_MODULE_STATUS_FIELDS = {
    "compatibility_facade_modules": "compatibility_facade",
    "entrypoint_modules": "entrypoint",
    "validation_modules": "validation",
}
ROOT_PACKAGE_STATUS_FIELDS = {
    "validation_packages": "validation",
}


class ArchitectureConfigurationError(RuntimeError):
    """Raised when the manifest or workspace metadata is inconsistent."""


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _normalized_distribution(value: str) -> str:
    match = DEPENDENCY_NAME.match(value.strip())
    if not match:
        return ""
    return re.sub(r"[-_.]+", "-", match.group(0)).lower()


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    candidate = Path(path)
    return any(candidate.match(pattern) for pattern in patterns)


def _workspace_glob_patterns(manifest: dict[str, Any]) -> list[str]:
    patterns = manifest.get("workspace_globs")
    if patterns is None:
        legacy_pattern = manifest.get("workspace_glob")
        patterns = [legacy_pattern] if legacy_pattern is not None else []
    if not isinstance(patterns, list) or not patterns or not all(
        isinstance(pattern, str) and pattern for pattern in patterns
    ):
        raise ArchitectureConfigurationError(
            "boundaries manifest must declare workspace_globs or workspace_glob"
        )
    return patterns


def _root_module_metadata(
    manifest: dict[str, Any], root_modules: set[str] | None = None
) -> tuple[dict[str, str], dict[str, list[str]]]:
    ownership = manifest.get("root_module_ownership")
    if not isinstance(ownership, dict) or not ownership:
        raise ArchitectureConfigurationError(
            "boundaries manifest must declare root_module_ownership"
        )
    unknown_owners = sorted(set(ownership) - ROOT_MODULE_OWNERS)
    if unknown_owners:
        raise ArchitectureConfigurationError(
            "unsupported root-module owners: " + ", ".join(unknown_owners)
        )

    owner_by_module: dict[str, str] = {}
    for owner in sorted(ownership):
        modules = ownership[owner]
        if not isinstance(modules, list) or not all(
            isinstance(module, str) and module for module in modules
        ):
            raise ArchitectureConfigurationError(
                f"root-module owner {owner!r} must contain a list of module names"
            )
        if len(modules) != len(set(modules)):
            raise ArchitectureConfigurationError(
                f"root-module owner {owner!r} contains duplicate module names"
            )
        for module in modules:
            prior_owner = owner_by_module.get(module)
            if prior_owner is not None:
                raise ArchitectureConfigurationError(
                    f"root module {module!r} has multiple owners: "
                    f"{prior_owner!r} and {owner!r}"
                )
            owner_by_module[module] = owner

    status = manifest.get("root_module_status", {})
    if not isinstance(status, dict):
        raise ArchitectureConfigurationError(
            "root_module_status must be a table when declared"
        )
    unknown_status_fields = sorted(set(status) - set(ROOT_MODULE_STATUS_FIELDS))
    if unknown_status_fields:
        raise ArchitectureConfigurationError(
            "unsupported root-module status fields: "
            + ", ".join(unknown_status_fields)
        )
    statuses_by_module: dict[str, list[str]] = defaultdict(list)
    for field, status_name in ROOT_MODULE_STATUS_FIELDS.items():
        modules = status.get(field, [])
        if not isinstance(modules, list) or not all(
            isinstance(module, str) and module for module in modules
        ):
            raise ArchitectureConfigurationError(
                f"root-module status {field!r} must be a list of module names"
            )
        if len(modules) != len(set(modules)):
            raise ArchitectureConfigurationError(
                f"root-module status {field!r} contains duplicate module names"
            )
        for module in modules:
            statuses_by_module[module].append(status_name)

    if root_modules is not None:
        unowned = sorted(root_modules - set(owner_by_module))
        stale_owners = sorted(set(owner_by_module) - root_modules)
        stale_statuses = sorted(set(statuses_by_module) - root_modules)
        if unowned:
            raise ArchitectureConfigurationError(
                "root modules without explicit owners: " + ", ".join(unowned)
            )
        if stale_owners:
            raise ArchitectureConfigurationError(
                "root-module ownership entries do not resolve: "
                + ", ".join(stale_owners)
            )
        if stale_statuses:
            raise ArchitectureConfigurationError(
                "root-module status entries do not resolve: "
                + ", ".join(stale_statuses)
            )

    return owner_by_module, {
        module: sorted(statuses) for module, statuses in statuses_by_module.items()
    }


def _root_owner_policy(
    manifest: dict[str, Any], declared_owners: set[str]
) -> dict[str, set[str]]:
    policy = manifest.get("root_owner_policy")
    if not isinstance(policy, dict):
        raise ArchitectureConfigurationError(
            "boundaries manifest must declare root_owner_policy"
        )
    missing = sorted(declared_owners - set(policy))
    stale = sorted(set(policy) - ROOT_MODULE_OWNERS)
    if missing:
        raise ArchitectureConfigurationError(
            "root owners without dependency policies: " + ", ".join(missing)
        )
    if stale:
        raise ArchitectureConfigurationError(
            "unsupported root-owner policies: " + ", ".join(stale)
        )

    allowed_by_owner: dict[str, set[str]] = {}
    for owner, owner_policy in sorted(policy.items()):
        if not isinstance(owner_policy, dict):
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} must be a table"
            )
        unknown_fields = sorted(set(owner_policy) - {"allowed_dependencies"})
        if unknown_fields:
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} has unsupported fields: "
                + ", ".join(unknown_fields)
            )
        dependencies = owner_policy.get("allowed_dependencies")
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) and dependency
            for dependency in dependencies
        ):
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} must declare allowed_dependencies"
            )
        if len(dependencies) != len(set(dependencies)):
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} contains duplicate dependencies"
            )
        unsupported = sorted(set(dependencies) - ROOT_MODULE_OWNERS)
        if unsupported:
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} has unsupported dependencies: "
                + ", ".join(unsupported)
            )
        if owner in dependencies:
            raise ArchitectureConfigurationError(
                f"root-owner policy {owner!r} cannot depend on itself"
            )
        allowed_by_owner[owner] = set(dependencies)

    policy_edges = {
        (owner, dependency)
        for owner, dependencies in allowed_by_owner.items()
        for dependency in dependencies
    }
    cycles = _strongly_connected_components(ROOT_MODULE_OWNERS, policy_edges)
    if cycles:
        rendered_cycles = "; ".join(" -> ".join(cycle) for cycle in cycles)
        raise ArchitectureConfigurationError(
            "root-owner target policy contains cycles: " + rendered_cycles
        )
    return allowed_by_owner


def _root_package_metadata(
    manifest: dict[str, Any], root_packages: set[str] | None = None
) -> tuple[dict[str, str], dict[str, list[str]]]:
    ownership = manifest.get("root_package_ownership")
    if not isinstance(ownership, dict) or not ownership:
        raise ArchitectureConfigurationError(
            "boundaries manifest must declare root_package_ownership"
        )
    unknown_owners = sorted(set(ownership) - ROOT_MODULE_OWNERS)
    if unknown_owners:
        raise ArchitectureConfigurationError(
            "unsupported root-package owners: " + ", ".join(unknown_owners)
        )

    owner_by_package: dict[str, str] = {}
    for owner in sorted(ownership):
        packages = ownership[owner]
        if not isinstance(packages, list) or not all(
            isinstance(package, str) and package for package in packages
        ):
            raise ArchitectureConfigurationError(
                f"root-package owner {owner!r} must contain a list of package names"
            )
        if len(packages) != len(set(packages)):
            raise ArchitectureConfigurationError(
                f"root-package owner {owner!r} contains duplicate package names"
            )
        for package in packages:
            prior_owner = owner_by_package.get(package)
            if prior_owner is not None:
                raise ArchitectureConfigurationError(
                    f"root package {package!r} has multiple owners: "
                    f"{prior_owner!r} and {owner!r}"
                )
            owner_by_package[package] = owner

    status = manifest.get("root_package_status", {})
    if not isinstance(status, dict):
        raise ArchitectureConfigurationError(
            "root_package_status must be a table when declared"
        )
    unknown_status_fields = sorted(set(status) - set(ROOT_PACKAGE_STATUS_FIELDS))
    if unknown_status_fields:
        raise ArchitectureConfigurationError(
            "unsupported root-package status fields: "
            + ", ".join(unknown_status_fields)
        )
    statuses_by_package: dict[str, list[str]] = defaultdict(list)
    for field, status_name in ROOT_PACKAGE_STATUS_FIELDS.items():
        packages = status.get(field, [])
        if not isinstance(packages, list) or not all(
            isinstance(package, str) and package for package in packages
        ):
            raise ArchitectureConfigurationError(
                f"root-package status {field!r} must be a list of package names"
            )
        if len(packages) != len(set(packages)):
            raise ArchitectureConfigurationError(
                f"root-package status {field!r} contains duplicate package names"
            )
        for package in packages:
            statuses_by_package[package].append(status_name)

    if root_packages is not None:
        unowned = sorted(root_packages - set(owner_by_package))
        stale_owners = sorted(set(owner_by_package) - root_packages)
        stale_statuses = sorted(set(statuses_by_package) - root_packages)
        if unowned:
            raise ArchitectureConfigurationError(
                "root packages without explicit owners: " + ", ".join(unowned)
            )
        if stale_owners:
            raise ArchitectureConfigurationError(
                "root-package ownership entries do not resolve: "
                + ", ".join(stale_owners)
            )
        if stale_statuses:
            raise ArchitectureConfigurationError(
                "root-package status entries do not resolve: "
                + ", ".join(stale_statuses)
            )

    return owner_by_package, {
        package: sorted(statuses)
        for package, statuses in statuses_by_package.items()
    }


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        manifest = tomllib.load(handle)
    if manifest.get("schema_version") != 1:
        raise ArchitectureConfigurationError("unsupported boundaries manifest schema")
    components = manifest.get("components")
    if not isinstance(components, dict) or not components:
        raise ArchitectureConfigurationError("boundaries manifest has no components")
    _workspace_glob_patterns(manifest)
    _root_module_metadata(manifest)
    _root_package_metadata(manifest)
    _root_owner_policy(
        manifest,
        set(manifest["root_module_ownership"])
        | set(manifest["root_package_ownership"]),
    )
    classification = manifest.get("root_boundary_classification", {})
    default_category = classification.get("default", "orchestration")
    if default_category not in ROOT_BOUNDARY_CATEGORIES:
        raise ArchitectureConfigurationError(
            f"unsupported root-boundary default category {default_category!r}"
        )
    category_keys = {
        "pure_helper": "pure_helper_modules",
        "dto_constants": "dto_constant_modules",
        "persistence": "persistence_modules",
        "compatibility": "compatibility_modules",
    }
    assigned: dict[str, str] = {}
    for category, key in category_keys.items():
        modules = classification.get(key, [])
        if not isinstance(modules, list) or not all(
            isinstance(module, str) and module for module in modules
        ):
            raise ArchitectureConfigurationError(
                f"root-boundary classification {key!r} must be a list of module names"
            )
        for module in modules:
            if module in assigned:
                raise ArchitectureConfigurationError(
                    f"root module {module!r} has multiple boundary classifications"
                )
            assigned[module] = category
    return manifest


def _root_boundary_category(manifest: dict[str, Any], root_module: str) -> str:
    classification = manifest.get("root_boundary_classification", {})
    category_keys = (
        ("pure_helper", "pure_helper_modules"),
        ("dto_constants", "dto_constant_modules"),
        ("persistence", "persistence_modules"),
        ("compatibility", "compatibility_modules"),
    )
    for category, key in category_keys:
        if root_module in classification.get(key, []):
            return category
    return classification.get("default", "orchestration")


def _load_project(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _uv_workspace_projects(repo_root: Path) -> dict[str, Path]:
    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return {}
    workspace = (
        _load_project(pyproject_path)
        .get("tool", {})
        .get("uv", {})
        .get("workspace", {})
    )
    members = workspace.get("members", [])
    if not isinstance(members, list):
        raise ArchitectureConfigurationError(
            "tool.uv.workspace.members must be a list"
        )
    projects: dict[str, Path] = {}
    for member in members:
        if not isinstance(member, str) or not member.strip():
            raise ArchitectureConfigurationError(
                "tool.uv.workspace.members must contain non-empty paths"
            )
        matches = sorted(repo_root.glob(member))
        if not matches:
            raise ArchitectureConfigurationError(
                f"uv workspace member {member!r} does not resolve"
            )
        for project_dir in matches:
            project_path = project_dir / "pyproject.toml"
            if project_path.is_file():
                projects[_relative(project_dir, repo_root)] = project_path
    return projects


def _component_inventory(
    repo_root: Path, manifest: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    configured = manifest["components"]
    discovered = {
        _relative(path.parent, repo_root): path
        for workspace_glob in _workspace_glob_patterns(manifest)
        for path in repo_root.glob(workspace_glob)
    }
    discovered.update(_uv_workspace_projects(repo_root))
    configured_dirs = {
        str(component["project_dir"]): name for name, component in configured.items()
    }
    unregistered = sorted(set(discovered) - set(configured_dirs))
    inventory: dict[str, dict[str, Any]] = {}
    distributions: dict[str, str] = {}
    prefixes: dict[str, str] = {}

    for name, configured_component in sorted(configured.items()):
        project_dir = repo_root / configured_component["project_dir"]
        pyproject_path = project_dir / "pyproject.toml"
        if not pyproject_path.is_file():
            raise ArchitectureConfigurationError(
                f"{name}: missing {_relative(pyproject_path, repo_root)}"
            )
        project_data = _load_project(pyproject_path)
        project = project_data.get("project", {})
        actual_distribution = project.get("name")
        expected_distribution = configured_component["distribution"]
        if actual_distribution != expected_distribution:
            raise ArchitectureConfigurationError(
                f"{name}: distribution is {actual_distribution!r}, expected "
                f"{expected_distribution!r}"
            )
        source_root = project_dir / "src"
        if not source_root.is_dir():
            raise ArchitectureConfigurationError(
                f"{name}: missing source root {_relative(source_root, repo_root)}"
            )
        prefix = configured_component["module_prefix"]
        distribution_key = _normalized_distribution(expected_distribution)
        if distribution_key in distributions:
            raise ArchitectureConfigurationError(
                f"duplicate distribution {expected_distribution!r}"
            )
        if prefix in prefixes:
            raise ArchitectureConfigurationError(f"duplicate module prefix {prefix!r}")
        distributions[distribution_key] = name
        prefixes[prefix] = name
        inventory[name] = {
            **configured_component,
            "project": project_data,
            "source_root": source_root,
        }

    return inventory, unregistered


def _module_for_file(path: Path, source_root: Path) -> tuple[str, bool]:
    relative = path.relative_to(source_root)
    parts = list(relative.with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ".".join(parts), is_package


def _resolve_import(
    module: str | None, level: int, current_module: str, is_package: bool
) -> str | None:
    if level == 0:
        return module
    package = current_module if is_package else current_module.rpartition(".")[0]
    if not package:
        return None
    relative_name = "." * level + (module or "")
    try:
        return importlib.util.resolve_name(relative_name, package)
    except (ImportError, ValueError):
        return None


def _owner_for_module(module: str, prefixes: list[tuple[str, str]]) -> str | None:
    for prefix, owner in prefixes:
        if module == prefix or module.startswith(prefix + "."):
            return owner
    return None


def _python_files(
    repo_root: Path, source_root: Path, exclude_globs: list[str]
) -> list[Path]:
    files = []
    for path in source_root.rglob("*.py"):
        relative = _relative(path, repo_root)
        if not _matches_any(relative, exclude_globs):
            files.append(path)
    return sorted(files)


def _strongly_connected_components(
    nodes: Iterable[str], edges: set[tuple[str, str]]
) -> list[list[str]]:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
        adjacency.setdefault(target, [])
    for targets in adjacency.values():
        targets.sort()

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            components.append(sorted(component))

    for node in sorted(adjacency):
        if node not in indices:
            visit(node)
    return sorted(components)


def _combined_graph_metrics(
    nodes: set[str],
    edges: set[tuple[str, str]],
    cycles: list[list[str]],
) -> dict[str, int]:
    cyclic_nodes = {member for cycle in cycles for member in cycle}
    cyclic_internal_edges = {
        (source, target)
        for source, target in edges
        if source in cyclic_nodes and target in cyclic_nodes
    }
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "cyclic_scc_count": len(cycles),
        "cyclic_node_count": len(cyclic_nodes),
        "cyclic_internal_edge_count": len(cyclic_internal_edges),
        "largest_cyclic_scc_node_count": max(
            (len(cycle) for cycle in cycles), default=0
        ),
    }


def _single_edge_cut_impacts(
    nodes: set[str],
    edges: set[tuple[str, str]],
    cycles: list[list[str]],
    metrics: dict[str, int],
) -> list[dict[str, str | int]]:
    cyclic_nodes = {member for cycle in cycles for member in cycle}
    impacts: list[dict[str, str | int]] = []
    for source, target in sorted(edges):
        if source not in cyclic_nodes or target not in cyclic_nodes:
            continue
        candidate_edges = edges - {(source, target)}
        candidate_cycles = _strongly_connected_components(nodes, candidate_edges)
        candidate_metrics = _combined_graph_metrics(
            nodes, candidate_edges, candidate_cycles
        )
        cyclic_node_reduction = (
            metrics["cyclic_node_count"] - candidate_metrics["cyclic_node_count"]
        )
        cyclic_internal_edge_reduction = (
            metrics["cyclic_internal_edge_count"]
            - candidate_metrics["cyclic_internal_edge_count"]
        )
        largest_scc_reduction = (
            metrics["largest_cyclic_scc_node_count"]
            - candidate_metrics["largest_cyclic_scc_node_count"]
        )
        # A reduction of one internal edge merely reflects the simulated removal.
        # Record only cuts that change SCC membership or remove additional cyclic
        # edges by splitting the graph.
        if not (
            cyclic_node_reduction
            or largest_scc_reduction
            or cyclic_internal_edge_reduction > 1
        ):
            continue
        impacts.append(
            {
                "source": source,
                "target": target,
                "cyclic_node_reduction": cyclic_node_reduction,
                "cyclic_internal_edge_reduction": cyclic_internal_edge_reduction,
                "largest_cyclic_scc_node_reduction": largest_scc_reduction,
                "resulting_cyclic_node_count": candidate_metrics[
                    "cyclic_node_count"
                ],
                "resulting_cyclic_internal_edge_count": candidate_metrics[
                    "cyclic_internal_edge_count"
                ],
            }
        )
    return sorted(
        impacts,
        key=lambda row: (
            -int(row["cyclic_node_reduction"]),
            -int(row["largest_cyclic_scc_node_reduction"]),
            -int(row["cyclic_internal_edge_reduction"]),
            str(row["source"]),
            str(row["target"]),
        ),
    )
def analyze(repo_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    inventory, unregistered = _component_inventory(repo_root, manifest)
    prefixes = sorted(
        ((component["module_prefix"], name) for name, component in inventory.items()),
        key=lambda pair: (-len(pair[0]), pair[0]),
    )
    distribution_owners = {
        _normalized_distribution(component["distribution"]): name
        for name, component in inventory.items()
    }
    root_module_paths = {
        path.stem: path
        for path in repo_root.glob(manifest.get("root_module_glob", "*.py"))
        if path.is_file()
    }
    root_modules = set(root_module_paths)
    root_module_owners, root_module_statuses = _root_module_metadata(
        manifest, root_modules
    )
    root_package_excludes = manifest.get("root_package_excludes", [])
    if not isinstance(root_package_excludes, list) or not all(
        isinstance(package, str) and package for package in root_package_excludes
    ):
        raise ArchitectureConfigurationError(
            "root_package_excludes must be a list of package names"
        )
    root_package_paths = {
        path.name: path
        for path in repo_root.iterdir()
        if path.is_dir()
        and (path / "__init__.py").is_file()
        and path.name not in set(root_package_excludes)
    }
    root_packages = set(root_package_paths)
    root_package_owners, root_package_statuses = _root_package_metadata(
        manifest, root_packages
    )
    root_owner_policy = _root_owner_policy(
        manifest,
        set(manifest["root_module_ownership"])
        | set(manifest["root_package_ownership"]),
    )
    excludes = list(manifest.get("exclude_globs", []))
    compatibility_alias_globs = list(
        manifest.get(
            "compatibility_alias_globs",
            manifest.get("compatibility_shim_globs", []),
        )
    )
    actual_edges: set[tuple[str, str]] = set()
    edge_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    compatibility_edges: set[tuple[str, str]] = set()
    compatibility_edge_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    root_dependencies: set[tuple[str, str]] = set()
    root_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    root_to_component_dependencies: set[tuple[str, str]] = set()
    root_to_component_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    root_to_root_dependencies: set[tuple[str, str]] = set()
    root_to_root_evidence: dict[tuple[str, str], set[str]] = defaultdict(set)
    component_to_root_package_dependencies: set[tuple[str, str]] = set()
    component_to_root_package_evidence: dict[
        tuple[str, str], set[str]
    ] = defaultdict(set)
    root_module_to_package_dependencies: set[tuple[str, str]] = set()
    root_module_to_package_evidence: dict[
        tuple[str, str], set[str]
    ] = defaultdict(set)
    root_package_to_component_dependencies: set[tuple[str, str]] = set()
    root_package_to_component_evidence: dict[
        tuple[str, str], set[str]
    ] = defaultdict(set)
    root_package_to_module_dependencies: set[tuple[str, str]] = set()
    root_package_to_module_evidence: dict[
        tuple[str, str], set[str]
    ] = defaultdict(set)
    root_package_to_package_dependencies: set[tuple[str, str]] = set()
    root_package_to_package_evidence: dict[
        tuple[str, str], set[str]
    ] = defaultdict(set)
    wildcard_exports: set[tuple[str, str]] = set()
    wildcard_evidence: dict[tuple[str, str], set[int]] = defaultdict(set)
    parse_errors: list[dict[str, str]] = []

    for component_name, component in sorted(inventory.items()):
        source_root: Path = component["source_root"]
        for path in _python_files(repo_root, source_root, excludes):
            relative_path = _relative(path, repo_root)
            is_compatibility_alias = _matches_any(
                relative_path, compatibility_alias_globs
            )
            current_module, is_package = _module_for_file(path, source_root)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
            except (OSError, SyntaxError, UnicodeError) as exc:
                parse_errors.append({"path": relative_path, "error": str(exc)})
                continue
            imported_modules: list[tuple[str, int, bool]] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.extend(
                        (alias.name, node.lineno, False) for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom):
                    resolved = _resolve_import(
                        node.module, node.level, current_module, is_package
                    )
                    if not resolved:
                        continue
                    imported_modules.append((resolved, node.lineno, False))
                    if any(alias.name == "*" for alias in node.names):
                        wildcard_exports.add((relative_path, resolved))
                        wildcard_evidence[(relative_path, resolved)].add(node.lineno)
            for imported_module, _lineno, _wildcard in imported_modules:
                owner = _owner_for_module(imported_module, prefixes)
                if owner and owner != component_name:
                    edge = (component_name, owner)
                    if is_compatibility_alias:
                        compatibility_edges.add(edge)
                        compatibility_edge_evidence[edge].add(relative_path)
                    else:
                        actual_edges.add(edge)
                        edge_evidence[edge].add(relative_path)
                root_module = imported_module.partition(".")[0]
                if root_module in root_modules:
                    dependency = (component_name, root_module)
                    root_dependencies.add(dependency)
                    root_evidence[dependency].add(relative_path)
                if root_module in root_packages:
                    dependency = (component_name, root_module)
                    component_to_root_package_dependencies.add(dependency)
                    component_to_root_package_evidence[dependency].add(relative_path)

    for root_module, path in sorted(root_module_paths.items()):
        relative_path = _relative(path, repo_root)
        if _matches_any(relative_path, excludes):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative_path)
        except (OSError, SyntaxError, UnicodeError) as exc:
            parse_errors.append({"path": relative_path, "error": str(exc)})
            continue
        imported_modules: list[tuple[str, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend((alias.name, node.lineno) for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                resolved = _resolve_import(node.module, node.level, root_module, False)
                if not resolved:
                    continue
                imported_modules.append((resolved, node.lineno))
                if any(alias.name == "*" for alias in node.names):
                    wildcard_exports.add((relative_path, resolved))
                    wildcard_evidence[(relative_path, resolved)].add(node.lineno)
        for imported_module, _lineno in imported_modules:
            owner = _owner_for_module(imported_module, prefixes)
            if owner:
                dependency = (root_module, owner)
                root_to_component_dependencies.add(dependency)
                root_to_component_evidence[dependency].add(relative_path)
            imported_root = imported_module.partition(".")[0]
            if imported_root in root_modules and imported_root != root_module:
                dependency = (root_module, imported_root)
                root_to_root_dependencies.add(dependency)
                root_to_root_evidence[dependency].add(relative_path)
            if imported_root in root_packages:
                dependency = (root_module, imported_root)
                root_module_to_package_dependencies.add(dependency)
                root_module_to_package_evidence[dependency].add(relative_path)

    for root_package, package_path in sorted(root_package_paths.items()):
        for path in _python_files(repo_root, package_path, excludes):
            relative_path = _relative(path, repo_root)
            current_module, is_package = _module_for_file(path, repo_root)
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"), filename=relative_path
                )
            except (OSError, SyntaxError, UnicodeError) as exc:
                parse_errors.append({"path": relative_path, "error": str(exc)})
                continue
            imported_modules: list[tuple[str, int]] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.extend(
                        (alias.name, node.lineno) for alias in node.names
                    )
                elif isinstance(node, ast.ImportFrom):
                    resolved = _resolve_import(
                        node.module, node.level, current_module, is_package
                    )
                    if not resolved:
                        continue
                    imported_modules.append((resolved, node.lineno))
                    if any(alias.name == "*" for alias in node.names):
                        wildcard_exports.add((relative_path, resolved))
                        wildcard_evidence[(relative_path, resolved)].add(node.lineno)
            for imported_module, _lineno in imported_modules:
                owner = _owner_for_module(imported_module, prefixes)
                if owner:
                    dependency = (root_package, owner)
                    root_package_to_component_dependencies.add(dependency)
                    root_package_to_component_evidence[dependency].add(relative_path)
                imported_root = imported_module.partition(".")[0]
                if imported_root in root_modules:
                    dependency = (root_package, imported_root)
                    root_package_to_module_dependencies.add(dependency)
                    root_package_to_module_evidence[dependency].add(relative_path)
                if imported_root in root_packages and imported_root != root_package:
                    dependency = (root_package, imported_root)
                    root_package_to_package_dependencies.add(dependency)
                    root_package_to_package_evidence[dependency].add(relative_path)

    root_owner_dependencies = {
        (root_module_owners[source], root_module_owners[target])
        for source, target in root_to_root_dependencies
        if root_module_owners[source] != root_module_owners[target]
    }
    root_owner_dependencies.update(
        (root_module_owners[source], root_package_owners[target])
        for source, target in root_module_to_package_dependencies
        if root_module_owners[source] != root_package_owners[target]
    )
    root_owner_dependencies.update(
        (root_package_owners[source], root_module_owners[target])
        for source, target in root_package_to_module_dependencies
        if root_package_owners[source] != root_module_owners[target]
    )
    root_owner_dependencies.update(
        (root_package_owners[source], root_package_owners[target])
        for source, target in root_package_to_package_dependencies
        if root_package_owners[source] != root_package_owners[target]
    )
    forbidden_root_owner_dependencies = {
        edge
        for edge in root_owner_dependencies
        if edge[1] not in root_owner_policy.get(edge[0], set())
    }
    compatibility_facade_modules = {
        module
        for module, statuses in root_module_statuses.items()
        if "compatibility_facade" in statuses
    }
    compatibility_facade_imports = {
        dependency
        for dependency in root_dependencies
        if dependency[1] in compatibility_facade_modules
    }
    canonical_root_facade_imports = {
        dependency
        for dependency in root_to_root_dependencies
        if dependency[1] in compatibility_facade_modules
        and "compatibility_facade"
        not in root_module_statuses.get(dependency[0], [])
    }
    canonical_root_facade_imports.update(
        dependency
        for dependency in root_package_to_module_dependencies
        if dependency[1] in compatibility_facade_modules
    )

    declared_dependencies: dict[str, set[str]] = {}
    for component_name, component in inventory.items():
        dependencies = component["project"].get("project", {}).get("dependencies", [])
        declared_dependencies[component_name] = {
            owner
            for dependency in dependencies
            if (owner := distribution_owners.get(_normalized_distribution(dependency)))
        }

    undeclared = {
        edge for edge in actual_edges if edge[1] not in declared_dependencies[edge[0]]
    }
    forbidden = {
        edge
        for edge in actual_edges
        if edge[1] not in set(inventory[edge[0]].get("allowed_dependencies", []))
    }
    cycles = _strongly_connected_components(inventory, actual_edges)
    combined_nodes = {
        *(f"component:{name}" for name in inventory),
        *(f"root:{name}" for name in root_modules),
        *(f"root-package:{name}" for name in root_packages),
    }
    combined_edges = {
        *((f"component:{source}", f"component:{target}") for source, target in actual_edges),
        *((f"component:{source}", f"root:{target}") for source, target in root_dependencies),
        *((f"root:{source}", f"component:{target}") for source, target in root_to_component_dependencies),
        *((f"root:{source}", f"root:{target}") for source, target in root_to_root_dependencies),
        *((f"component:{source}", f"root-package:{target}") for source, target in component_to_root_package_dependencies),
        *((f"root:{source}", f"root-package:{target}") for source, target in root_module_to_package_dependencies),
        *((f"root-package:{source}", f"component:{target}") for source, target in root_package_to_component_dependencies),
        *((f"root-package:{source}", f"root:{target}") for source, target in root_package_to_module_dependencies),
        *((f"root-package:{source}", f"root-package:{target}") for source, target in root_package_to_package_dependencies),
    }
    combined_cycles = _strongly_connected_components(combined_nodes, combined_edges)
    combined_graph_metrics = _combined_graph_metrics(
        combined_nodes, combined_edges, combined_cycles
    )
    single_edge_cut_impacts = _single_edge_cut_impacts(
        combined_nodes,
        combined_edges,
        combined_cycles,
        combined_graph_metrics,
    )

    root_boundary_classifications = [
        {
            "direction": "component_to_root",
            "source": source,
            "target": module,
            "category": _root_boundary_category(manifest, module),
        }
        for source, module in sorted(root_dependencies)
    ] + [
        {
            "direction": "root_to_component",
            "source": source,
            "target": target,
            "category": _root_boundary_category(manifest, source),
        }
        for source, target in sorted(root_to_component_dependencies)
    ]

    def edge_rows(edges: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
        return [
            {"source": source, "target": target}
            for source, target in sorted(edges)
        ]

    baseline = {
        "schema_version": 1,
        "actual_edges": edge_rows(actual_edges),
        "compatibility_edges": edge_rows(compatibility_edges),
        "combined_cycles": combined_cycles,
        "combined_graph_metrics": combined_graph_metrics,
        "cycles": cycles,
        "forbidden_edges": edge_rows(forbidden),
        "forbidden_root_owner_dependencies": edge_rows(
            forbidden_root_owner_dependencies
        ),
        "root_module_dependencies": [
            {"source": source, "module": module}
            for source, module in sorted(root_dependencies)
        ],
        "root_module_ownership": [
            {
                "module": module,
                "owner": root_module_owners[module],
                "statuses": root_module_statuses.get(module, []),
            }
            for module in sorted(root_modules)
        ],
        "root_package_ownership": [
            {
                "package": package,
                "owner": root_package_owners[package],
                "statuses": root_package_statuses.get(package, []),
            }
            for package in sorted(root_packages)
        ],
        "root_owner_dependencies": edge_rows(root_owner_dependencies),
        "compatibility_facade_imports": [
            {"source": source, "module": module}
            for source, module in sorted(compatibility_facade_imports)
        ],
        "canonical_root_facade_imports": [
            {"source": source, "module": module}
            for source, module in sorted(canonical_root_facade_imports)
        ],
        "component_to_root_package_dependencies": edge_rows(
            component_to_root_package_dependencies
        ),
        "root_module_to_package_dependencies": edge_rows(
            root_module_to_package_dependencies
        ),
        "root_package_to_component_dependencies": edge_rows(
            root_package_to_component_dependencies
        ),
        "root_package_to_module_dependencies": [
            {"source": source, "module": module}
            for source, module in sorted(root_package_to_module_dependencies)
        ],
        "root_package_to_package_dependencies": edge_rows(
            root_package_to_package_dependencies
        ),
        "root_boundary_classifications": root_boundary_classifications,
        "root_to_component_dependencies": edge_rows(root_to_component_dependencies),
        "root_to_root_dependencies": [
            {"source": source, "module": module}
            for source, module in sorted(root_to_root_dependencies)
        ],
        "single_edge_cut_impacts": single_edge_cut_impacts,
        "undeclared_dependencies": edge_rows(undeclared),
        "unregistered_components": unregistered,
        "wildcard_exports": [
            {"path": path, "module": module}
            for path, module in sorted(wildcard_exports)
        ],
    }
    return {
        "baseline": baseline,
        "components": inventory,
        "compatibility_edge_evidence": compatibility_edge_evidence,
        "declared_dependencies": declared_dependencies,
        "edge_evidence": edge_evidence,
        "root_evidence": root_evidence,
        "root_to_component_evidence": root_to_component_evidence,
        "root_to_root_evidence": root_to_root_evidence,
        "component_to_root_package_evidence": component_to_root_package_evidence,
        "root_module_to_package_evidence": root_module_to_package_evidence,
        "root_package_to_component_evidence": root_package_to_component_evidence,
        "root_package_to_module_evidence": root_package_to_module_evidence,
        "root_package_to_package_evidence": root_package_to_package_evidence,
        "wildcard_evidence": wildcard_evidence,
        "parse_errors": parse_errors,
    }


def _edge_set(rows: Iterable[dict[str, str]]) -> set[tuple[str, str]]:
    return {(row["source"], row["target"]) for row in rows}


def _root_boundary_classification_map(
    rows: Iterable[dict[str, str]],
) -> dict[tuple[str, str, str], str]:
    return {
        (row["direction"], row["source"], row["target"]): row["category"]
        for row in rows
    }


def _root_module_ownership_map(
    rows: Iterable[dict[str, Any]],
) -> dict[str, tuple[str, tuple[str, ...]]]:
    return {
        row["module"]: (row["owner"], tuple(row.get("statuses", [])))
        for row in rows
    }


def _root_package_ownership_map(
    rows: Iterable[dict[str, Any]],
) -> dict[str, tuple[str, tuple[str, ...]]]:
    return {
        row["package"]: (row["owner"], tuple(row.get("statuses", [])))
        for row in rows
    }


def compare(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    regressions: list[str] = []
    if baseline.get("schema_version") != 1:
        return ["dependency baseline uses an unsupported schema"]

    for key, label in (
        ("actual_edges", "new dependency edge"),
        ("compatibility_edges", "new compatibility-alias edge"),
        ("forbidden_edges", "new forbidden edge"),
        ("undeclared_dependencies", "new undeclared dependency"),
    ):
        extras = _edge_set(current.get(key, [])) - _edge_set(baseline.get(key, []))
        regressions.extend(
            f"{label}: {source} -> {target}" for source, target in sorted(extras)
        )

    current_roots = {
        (row["source"], row["module"])
        for row in current.get("root_module_dependencies", [])
    }
    baseline_roots = {
        (row["source"], row["module"])
        for row in baseline.get("root_module_dependencies", [])
    }
    regressions.extend(
        f"new root-module dependency: {source} -> {module}"
        for source, module in sorted(current_roots - baseline_roots)
    )

    facade_imports = {
        (row["source"], row["module"])
        for row in current.get("compatibility_facade_imports", [])
    }
    regressions.extend(
        f"package imports root compatibility facade: {source} -> {module}"
        for source, module in sorted(facade_imports)
    )
    canonical_root_facade_imports = {
        (row["source"], row["module"])
        for row in current.get("canonical_root_facade_imports", [])
    }
    regressions.extend(
        f"canonical root module imports compatibility facade: {source} -> {module}"
        for source, module in sorted(canonical_root_facade_imports)
    )

    current_root_components = _edge_set(
        current.get("root_to_component_dependencies", [])
    )
    baseline_root_components = _edge_set(
        baseline.get("root_to_component_dependencies", [])
    )
    regressions.extend(
        f"new root-to-component dependency: {source} -> {target}"
        for source, target in sorted(
            current_root_components - baseline_root_components
        )
    )

    current_root_roots = {
        (row["source"], row["module"])
        for row in current.get("root_to_root_dependencies", [])
    }
    baseline_root_roots = {
        (row["source"], row["module"])
        for row in baseline.get("root_to_root_dependencies", [])
    }
    regressions.extend(
        f"new root-to-root dependency: {source} -> {module}"
        for source, module in sorted(current_root_roots - baseline_root_roots)
    )

    for key, label in (
        (
            "component_to_root_package_dependencies",
            "new component-to-root-package dependency",
        ),
        (
            "root_module_to_package_dependencies",
            "new root-module-to-package dependency",
        ),
        (
            "root_package_to_component_dependencies",
            "new root-package-to-component dependency",
        ),
        (
            "root_package_to_package_dependencies",
            "new root-package-to-package dependency",
        ),
    ):
        extras = _edge_set(current.get(key, [])) - _edge_set(baseline.get(key, []))
        regressions.extend(
            f"{label}: {source} -> {target}"
            for source, target in sorted(extras)
        )

    current_package_modules = {
        (row["source"], row["module"])
        for row in current.get("root_package_to_module_dependencies", [])
    }
    baseline_package_modules = {
        (row["source"], row["module"])
        for row in baseline.get("root_package_to_module_dependencies", [])
    }
    regressions.extend(
        f"new root-package-to-module dependency: {source} -> {module}"
        for source, module in sorted(
            current_package_modules - baseline_package_modules
        )
    )

    for key, label in (
        ("root_owner_dependencies", "new root-owner dependency"),
        (
            "forbidden_root_owner_dependencies",
            "new forbidden root-owner dependency",
        ),
    ):
        extras = _edge_set(current.get(key, [])) - _edge_set(baseline.get(key, []))
        regressions.extend(
            f"{label}: {source} -> {target}"
            for source, target in sorted(extras)
        )

    if "root_module_ownership" in baseline:
        current_ownership = _root_module_ownership_map(
            current.get("root_module_ownership", [])
        )
        baseline_ownership = _root_module_ownership_map(
            baseline["root_module_ownership"]
        )
        for module in sorted(current_ownership.keys() - baseline_ownership.keys()):
            owner, statuses = current_ownership[module]
            status_text = ",".join(statuses) if statuses else "canonical"
            regressions.append(
                f"new owned root module: {module} -> {owner} ({status_text})"
            )
        for module in sorted(current_ownership.keys() & baseline_ownership.keys()):
            current_metadata = current_ownership[module]
            baseline_metadata = baseline_ownership[module]
            if current_metadata != baseline_metadata:
                regressions.append(
                    "root-module ownership changed: "
                    f"{module} ({baseline_metadata[0]} {list(baseline_metadata[1])} -> "
                    f"{current_metadata[0]} {list(current_metadata[1])})"
                )

    if "root_package_ownership" in baseline:
        current_ownership = _root_package_ownership_map(
            current.get("root_package_ownership", [])
        )
        baseline_ownership = _root_package_ownership_map(
            baseline["root_package_ownership"]
        )
        for package in sorted(current_ownership.keys() - baseline_ownership.keys()):
            owner, statuses = current_ownership[package]
            status_text = ",".join(statuses) if statuses else "canonical"
            regressions.append(
                f"new owned root package: {package} -> {owner} ({status_text})"
            )
        for package in sorted(current_ownership.keys() & baseline_ownership.keys()):
            current_metadata = current_ownership[package]
            baseline_metadata = baseline_ownership[package]
            if current_metadata != baseline_metadata:
                regressions.append(
                    "root-package ownership changed: "
                    f"{package} ({baseline_metadata[0]} {list(baseline_metadata[1])} -> "
                    f"{current_metadata[0]} {list(current_metadata[1])})"
                )

    if "root_boundary_classifications" in baseline:
        current_classifications = _root_boundary_classification_map(
            current.get("root_boundary_classifications", [])
        )
        baseline_classifications = _root_boundary_classification_map(
            baseline["root_boundary_classifications"]
        )
        for edge in sorted(current_classifications.keys() & baseline_classifications.keys()):
            current_category = current_classifications[edge]
            baseline_category = baseline_classifications[edge]
            if current_category != baseline_category:
                regressions.append(
                    "root-boundary classification changed: "
                    f"{edge[0]} {edge[1]} -> {edge[2]} "
                    f"({baseline_category} -> {current_category})"
                )

    current_wildcards = {
        (row["path"], row["module"]) for row in current.get("wildcard_exports", [])
    }
    baseline_wildcards = {
        (row["path"], row["module"])
        for row in baseline.get("wildcard_exports", [])
    }
    regressions.extend(
        f"new wildcard export: {path} imports * from {module}"
        for path, module in sorted(current_wildcards - baseline_wildcards)
    )

    new_components = set(current.get("unregistered_components", [])) - set(
        baseline.get("unregistered_components", [])
    )
    regressions.extend(
        f"new unregistered component: {component}" for component in sorted(new_components)
    )

    prior_cycles = [set(cycle) for cycle in baseline.get("cycles", [])]
    for cycle in current.get("cycles", []):
        current_cycle = set(cycle)
        if not any(current_cycle <= prior_cycle for prior_cycle in prior_cycles):
            regressions.append("new or enlarged cycle: " + " -> ".join(cycle))
    prior_combined_cycles = [
        set(cycle) for cycle in baseline.get("combined_cycles", [])
    ]
    for cycle in current.get("combined_cycles", []):
        current_cycle = set(cycle)
        if not any(
            current_cycle <= prior_cycle for prior_cycle in prior_combined_cycles
        ):
            regressions.append(
                "new or enlarged combined cycle: " + " -> ".join(cycle)
            )
    current_metrics = current.get("combined_graph_metrics", {})
    baseline_metrics = baseline.get("combined_graph_metrics", {})
    for key, label in (
        ("cyclic_node_count", "combined cyclic node count"),
        ("cyclic_internal_edge_count", "combined cyclic internal edge count"),
        ("largest_cyclic_scc_node_count", "largest combined cyclic SCC"),
    ):
        if key not in current_metrics or key not in baseline_metrics:
            continue
        if current_metrics[key] > baseline_metrics[key]:
            regressions.append(
                f"{label} increased: {baseline_metrics[key]} -> {current_metrics[key]}"
            )
    return sorted(set(regressions))


def render_report(repo_root: Path, manifest: dict[str, Any], result: dict[str, Any]) -> str:
    baseline = result["baseline"]
    components = result["components"]
    lines = [
        "# Repository Dependency Report",
        "",
        "This report is generated deterministically by "
        "`scripts/check_architecture_boundaries.py`. It records architecture facts; "
        "it does not import or execute production code.",
        "",
        "## Components",
        "",
        "| Component | Layer | Distribution | Public module prefix |",
        "| --- | --- | --- | --- |",
    ]
    for name, component in sorted(components.items()):
        lines.append(
            f"| `{name}` | `{component['layer']}` | `{component['distribution']}` | "
            f"`{component['module_prefix']}` |"
        )

    lines.extend(
        [
            "",
            "## Root Module Ownership",
            "",
            "Every repository-root Python module has one explicit responsibility. "
            "Status is orthogonal: an entrypoint or compatibility facade retains "
            "the owner of the behavior it exposes.",
            "",
            "| Module | Owner | Status |",
            "| --- | --- | --- |",
        ]
    )
    for row in baseline["root_module_ownership"]:
        statuses = row.get("statuses", [])
        status_text = ", ".join(f"`{status}`" for status in statuses) or "canonical"
        lines.append(
            f"| `{row['module']}` | `{row['owner']}` | {status_text} |"
        )

    lines.extend(
        [
            "",
            "## Root Package Family Ownership",
            "",
            "Top-level Python package families that are not UV workspace projects are "
            "measured by the same responsibility policy as root modules.",
            "",
            "| Package family | Owner | Status |",
            "| --- | --- | --- |",
        ]
    )
    for row in baseline["root_package_ownership"]:
        statuses = row.get("statuses", [])
        status_text = ", ".join(f"`{status}`" for status in statuses) or "canonical"
        lines.append(
            f"| `{row['package']}` | `{row['owner']}` | {status_text} |"
        )

    root_owner_policy = _root_owner_policy(
        manifest,
        set(manifest["root_module_ownership"])
        | set(manifest["root_package_ownership"]),
    )
    lines.extend(
        [
            "",
            "## Target Root-Owner Dependency Policy",
            "",
            "This policy describes the intended acyclic responsibility graph. Current "
            "violations are measured separately and may only shrink.",
            "",
            "| Owner | May depend on |",
            "| --- | --- |",
        ]
    )
    for owner, dependencies in sorted(root_owner_policy.items()):
        dependency_text = ", ".join(
            f"`{dependency}`" for dependency in sorted(dependencies)
        ) or "none"
        lines.append(f"| `{owner}` | {dependency_text} |")

    lines.extend(
        [
            "",
            "## Current Root-Owner Dependency Edges",
            "",
            "| Source | Target | Allowed by target policy |",
            "| --- | --- | --- |",
        ]
    )
    forbidden_root_owner_edges = _edge_set(
        baseline["forbidden_root_owner_dependencies"]
    )
    for row in baseline["root_owner_dependencies"]:
        edge = (row["source"], row["target"])
        lines.append(
            f"| `{edge[0]}` | `{edge[1]}` | "
            f"{'no' if edge in forbidden_root_owner_edges else 'yes'} |"
        )

    lines.extend(["", "## Package Imports Of Root Compatibility Facades", ""])
    if baseline["compatibility_facade_imports"]:
        for row in baseline["compatibility_facade_imports"]:
            lines.append(f"- `{row['source']}` -> `{row['module']}`")
    else:
        lines.append("No workspace package imports a root compatibility facade.")

    lines.extend(["", "## Canonical Root Imports Of Compatibility Facades", ""])
    if baseline["canonical_root_facade_imports"]:
        for row in baseline["canonical_root_facade_imports"]:
            lines.append(f"- `{row['source']}` -> `{row['module']}`")
    else:
        lines.append("No canonical root module imports a compatibility facade.")

    lines.extend(
        [
            "",
            "## Dependency Edges",
            "",
            "| Source | Target | Declared | Allowed by target policy | Evidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    forbidden = _edge_set(baseline["forbidden_edges"])
    undeclared = _edge_set(baseline["undeclared_dependencies"])
    for row in baseline["actual_edges"]:
        edge = (row["source"], row["target"])
        evidence = sorted(result["edge_evidence"].get(edge, []))
        display_evidence = ", ".join(f"`{path}`" for path in evidence[:3])
        if len(evidence) > 3:
            display_evidence += f" (+{len(evidence) - 3} more)"
        lines.append(
            f"| `{edge[0]}` | `{edge[1]}` | "
            f"{'no' if edge in undeclared else 'yes'} | "
            f"{'no' if edge in forbidden else 'yes'} | {display_evidence} |"
        )

    lines.extend(["", "## Cycles", ""])
    if baseline["cycles"]:
        for cycle in baseline["cycles"]:
            lines.append("- " + " -> ".join(f"`{member}`" for member in cycle))
    else:
        lines.append("No package cycles were found.")

    lines.extend(["", "## Compatibility Alias Edges", ""])
    if baseline.get("compatibility_edges", []):
        lines.extend(
            [
                "These edges exist only to preserve historical import paths. They are excluded "
                "from the canonical cycle calculation, remain visible here, and are still "
                "ratcheted against expansion.",
                "",
                "| Source | Target | Evidence |",
                "| --- | --- | --- |",
            ]
        )
        for row in baseline["compatibility_edges"]:
            edge = (row["source"], row["target"])
            evidence = sorted(result["compatibility_edge_evidence"].get(edge, []))
            lines.append(
                f"| `{edge[0]}` | `{edge[1]}` | "
                + ", ".join(f"`{path}`" for path in evidence)
                + " |"
            )
    else:
        lines.append("No compatibility-alias dependency edges were found.")

    metrics = baseline["combined_graph_metrics"]
    lines.extend(
        [
            "",
            "## Combined Graph Metrics",
            "",
            "| Metric | Count |",
            "| --- | ---: |",
            f"| Nodes | {metrics['node_count']} |",
            f"| Edges | {metrics['edge_count']} |",
            f"| Cyclic SCCs | {metrics['cyclic_scc_count']} |",
            f"| Nodes in cyclic SCCs | {metrics['cyclic_node_count']} |",
            f"| Edges internal to cyclic SCCs | {metrics['cyclic_internal_edge_count']} |",
            f"| Largest cyclic SCC nodes | {metrics['largest_cyclic_scc_node_count']} |",
        ]
    )

    lines.extend(["", "## Single-Edge SCC Sensitivity", ""])
    lines.append(
        "This is a removal-only topology simulation, not an extraction recommendation. "
        "A candidate is safe only if preserving its behavior does not add replacement "
        "edges that recreate the cycle."
    )
    if baseline["single_edge_cut_impacts"]:
        lines.extend(
            [
                "",
                "| Removed edge | Cyclic nodes removed | Internal cyclic edges removed | Largest SCC reduction | Resulting cyclic nodes | Resulting internal cyclic edges |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in baseline["single_edge_cut_impacts"]:
            lines.append(
                f"| `{row['source']} -> {row['target']}` | "
                f"{row['cyclic_node_reduction']} | "
                f"{row['cyclic_internal_edge_reduction']} | "
                f"{row['largest_cyclic_scc_node_reduction']} | "
                f"{row['resulting_cyclic_node_count']} | "
                f"{row['resulting_cyclic_internal_edge_count']} |"
            )
    else:
        lines.append("No single internal edge has structural SCC impact.")

    lines.extend(["", "## Root-Boundary Classification Ledger", ""])
    lines.extend(
        [
            "Classifications are explicit policy metadata from `architecture/boundaries.toml`. "
            "Unlisted root modules are conservatively classified as `orchestration`.",
            "",
            "| Direction | Source | Target | Category |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in baseline["root_boundary_classifications"]:
        lines.append(
            f"| `{row['direction']}` | `{row['source']}` | `{row['target']}` | "
            f"`{row['category']}` |"
        )

    lines.extend(["", "## Root-Module Dependencies", ""])
    if baseline["root_module_dependencies"]:
        for row in baseline["root_module_dependencies"]:
            key = (row["source"], row["module"])
            evidence = ", ".join(
                f"`{path}`" for path in sorted(result["root_evidence"].get(key, []))
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No workspace package imports a root application module.")

    lines.extend(["", "## Root-to-Component Dependencies", ""])
    if baseline["root_to_component_dependencies"]:
        for row in baseline["root_to_component_dependencies"]:
            key = (row["source"], row["target"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["root_to_component_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No root application module imports a workspace component.")

    lines.extend(["", "## Root-to-Root Dependencies", ""])
    if baseline["root_to_root_dependencies"]:
        for row in baseline["root_to_root_dependencies"]:
            key = (row["source"], row["module"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(result["root_to_root_evidence"].get(key, []))
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No root application module imports another root module.")

    lines.extend(["", "## Component-to-Root-Package Dependencies", ""])
    if baseline["component_to_root_package_dependencies"]:
        for row in baseline["component_to_root_package_dependencies"]:
            key = (row["source"], row["target"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["component_to_root_package_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No workspace component imports a top-level package family.")

    lines.extend(["", "## Root-Module-to-Package Dependencies", ""])
    if baseline["root_module_to_package_dependencies"]:
        for row in baseline["root_module_to_package_dependencies"]:
            key = (row["source"], row["target"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["root_module_to_package_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No root module imports a top-level package family.")

    lines.extend(["", "## Root-Package-to-Component Dependencies", ""])
    if baseline["root_package_to_component_dependencies"]:
        for row in baseline["root_package_to_component_dependencies"]:
            key = (row["source"], row["target"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["root_package_to_component_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No top-level package family imports a workspace component.")

    lines.extend(["", "## Root-Package-to-Module Dependencies", ""])
    if baseline["root_package_to_module_dependencies"]:
        for row in baseline["root_package_to_module_dependencies"]:
            key = (row["source"], row["module"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["root_package_to_module_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No top-level package family imports a root module.")

    lines.extend(["", "## Root-Package-to-Package Dependencies", ""])
    if baseline["root_package_to_package_dependencies"]:
        for row in baseline["root_package_to_package_dependencies"]:
            key = (row["source"], row["target"])
            evidence = ", ".join(
                f"`{path}`"
                for path in sorted(
                    result["root_package_to_package_evidence"].get(key, [])
                )
            )
            lines.append(f"- `{key[0]}` -> `{key[1]}` ({evidence})")
    else:
        lines.append("No top-level package family imports another package family.")

    lines.extend(["", "## Combined Root/Package Cycles", ""])
    if baseline["combined_cycles"]:
        for cycle in baseline["combined_cycles"]:
            lines.append("- " + " -> ".join(f"`{member}`" for member in cycle))
    else:
        lines.append(
            "No cycles span root modules, top-level package families, and workspace packages."
        )

    lines.extend(["", "## Wildcard Exports", ""])
    if baseline["wildcard_exports"]:
        for row in baseline["wildcard_exports"]:
            key = (row["path"], row["module"])
            locations = ", ".join(
                str(line) for line in sorted(result["wildcard_evidence"].get(key, []))
            )
            lines.append(
                f"- `{row['path']}` imports `*` from `{row['module']}` "
                f"(line {locations})"
            )
    else:
        lines.append("No wildcard exports were found in scanned production sources.")

    lines.extend(
        [
            "",
            "## Ratchet Rules",
            "",
            "The checked-in baseline records the facts above. Declared compatibility aliases "
            "preserve historical ABI; every measured category remains closed to expansion. "
            "The checker fails for unowned, multiply owned, or stale root modules or package families; "
            "changed root ownership; package or canonical-root imports of compatibility facades; "
            "new dependency edges; undeclared or forbidden edges; package-to-root, "
            "root-to-package, root-to-root, or top-level package-family dependencies; "
            "new compatibility-alias edges; new wildcard "
            "exports, unregistered packages, and new or enlarged package or combined strongly connected "
            "components. Removing a violation "
            "and refreshing the baseline "
            "makes that improvement permanent.",
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_from_repo(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="replace the baseline with the current measured architecture",
    )
    parser.add_argument(
        "--write-report",
        nargs="?",
        const="",
        metavar="PATH",
        help="write the deterministic Markdown dependency report",
    )
    parser.add_argument("--json", action="store_true", help="print measured JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest.resolve()
    repo_root = REPO_ROOT if manifest_path == DEFAULT_MANIFEST else manifest_path.parent.parent
    try:
        manifest = load_manifest(manifest_path)
        result = analyze(repo_root, manifest)
    except (ArchitectureConfigurationError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"architecture configuration error: {exc}", file=sys.stderr)
        return 2

    if result["parse_errors"]:
        for error in result["parse_errors"]:
            print(f"cannot parse {error['path']}: {error['error']}", file=sys.stderr)
        return 2

    baseline_path = args.baseline or _resolve_from_repo(
        repo_root, manifest["baseline_path"]
    )
    if args.update_baseline:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(_canonical_json(result["baseline"]), encoding="utf-8")

    if args.write_report is not None:
        report_value = args.write_report or manifest["report_path"]
        report_path = _resolve_from_repo(repo_root, report_value)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            render_report(repo_root, manifest, result), encoding="utf-8"
        )

    if args.json:
        print(_canonical_json(result["baseline"]), end="")

    if not baseline_path.is_file():
        print(
            f"dependency baseline is missing: {_relative(baseline_path, repo_root)}; "
            "run with --update-baseline",
            file=sys.stderr,
        )
        return 2
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read dependency baseline: {exc}", file=sys.stderr)
        return 2
    regressions = compare(result["baseline"], baseline)
    if regressions:
        print("architecture boundary regressions detected:", file=sys.stderr)
        for regression in regressions:
            print(f"- {regression}", file=sys.stderr)
        return 1
    if not args.json:
        edge_count = len(result["baseline"]["actual_edges"])
        violation_count = (
            len(result["baseline"].get("compatibility_edges", []))
            +
            len(result["baseline"]["forbidden_edges"])
            + len(result["baseline"]["undeclared_dependencies"])
            + len(result["baseline"]["root_module_dependencies"])
            + len(result["baseline"]["root_to_component_dependencies"])
            + len(result["baseline"]["root_to_root_dependencies"])
            + len(result["baseline"]["component_to_root_package_dependencies"])
            + len(result["baseline"]["root_module_to_package_dependencies"])
            + len(result["baseline"]["root_package_to_component_dependencies"])
            + len(result["baseline"]["root_package_to_module_dependencies"])
            + len(result["baseline"]["root_package_to_package_dependencies"])
            + len(result["baseline"]["wildcard_exports"])
        )
        print(
            f"architecture boundary ratchet passed: {len(result['components'])} components, "
            f"{len(result['baseline']['root_module_ownership'])} owned root modules, "
            f"{len(result['baseline']['root_package_ownership'])} owned root package families, "
            f"{edge_count} edges, {violation_count} grandfathered observations, "
            f"{result['baseline']['combined_graph_metrics']['cyclic_node_count']} cyclic nodes, "
            f"{result['baseline']['combined_graph_metrics']['cyclic_internal_edge_count']} "
            "cyclic internal edges"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
