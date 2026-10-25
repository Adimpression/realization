#!/usr/bin/env python3
"""Remove generated workspace artifacts without touching operational state."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]

PROTECTED_TOP_LEVEL_DIRECTORIES = frozenset(
    {
        ".git",
        "corpus",
        "ram",
        "reports",
        "state",
        "tmp",
    }
)
ENVIRONMENT_DIRECTORY_NAMES = frozenset({".uv-cache", ".venv", "venv"})
GENERATED_DIRECTORY_NAMES = frozenset(
    {
        ".build",
        ".dart_tool",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "ephemeral",
    }
)
GENERATED_FILE_NAMES = frozenset({".DS_Store"})
GENERATED_FILE_SUFFIXES = (".pyc", ".pyo")


def _git_output(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(root), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def _tracked_paths(root: Path) -> frozenset[str]:
    return frozenset(
        item.decode("utf-8", errors="surrogateescape")
        for item in _git_output(root, "ls-files", "-z").split(b"\0")
        if item
    )


def _contains_tracked_content(
    path: Path,
    *,
    root: Path,
    tracked_paths: frozenset[str],
) -> bool:
    relative = path.relative_to(root).as_posix()
    prefix = f"{relative}/"
    return relative in tracked_paths or any(
        tracked.startswith(prefix) for tracked in tracked_paths
    )


def _is_git_ignored(path: Path, *, root: Path) -> bool:
    relative = path.relative_to(root).as_posix()
    completed = subprocess.run(
        ("git", "-C", str(root), "check-ignore", "--quiet", "--", relative),
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _is_generated_directory(path: Path) -> bool:
    return path.name in GENERATED_DIRECTORY_NAMES or path.name.endswith(".egg-info")


def _is_generated_file(path: Path) -> bool:
    return path.name in GENERATED_FILE_NAMES or path.name.endswith(
        GENERATED_FILE_SUFFIXES
    )


def cleanup_targets(
    root: Path = REPO_ROOT,
    *,
    include_environments: bool = False,
) -> tuple[Path, ...]:
    """Return ignored generated paths that are safe to remove."""

    root = root.resolve()
    tracked_paths = _tracked_paths(root)
    candidates: list[Path] = []

    for current, directories, filenames in os.walk(root, topdown=True):
        current_path = Path(current)
        if current_path != root and (current_path / ".git").exists():
            directories[:] = []
            continue
        retained_directories: list[str] = []

        for name in directories:
            path = current_path / name
            if name == ".git":
                continue
            if current_path == root and name in PROTECTED_TOP_LEVEL_DIRECTORIES:
                continue
            if name in ENVIRONMENT_DIRECTORY_NAMES:
                if (
                    include_environments
                    and _is_git_ignored(path, root=root)
                    and not _contains_tracked_content(
                        path,
                        root=root,
                        tracked_paths=tracked_paths,
                    )
                ):
                    candidates.append(path)
                continue
            if _is_generated_directory(path):
                if (
                    _is_git_ignored(path, root=root)
                    and not _contains_tracked_content(
                        path,
                        root=root,
                        tracked_paths=tracked_paths,
                    )
                ):
                    candidates.append(path)
                continue
            retained_directories.append(name)

        directories[:] = retained_directories

        for name in filenames:
            path = current_path / name
            if not _is_generated_file(path):
                continue
            if (
                _is_git_ignored(path, root=root)
                and not _contains_tracked_content(
                    path,
                    root=root,
                    tracked_paths=tracked_paths,
                )
            ):
                candidates.append(path)

    return tuple(sorted(candidates, key=lambda path: path.relative_to(root).as_posix()))


def remove_targets(targets: Iterable[Path]) -> None:
    for path in targets:
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Git worktree to inspect (defaults to this repository).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Remove listed paths. Without this flag the command is read-only.",
    )
    parser.add_argument(
        "--include-environments",
        action="store_true",
        help="Also include .venv, venv, and .uv-cache directories.",
    )
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    root = arguments.root.resolve()
    targets = cleanup_targets(
        root,
        include_environments=arguments.include_environments,
    )
    action = "remove" if arguments.apply else "would remove"
    for path in targets:
        print(f"{action}: {path.relative_to(root).as_posix()}")
    if arguments.apply:
        remove_targets(targets)
    outcome = "removed" if arguments.apply else "listed"
    print(f"{len(targets)} generated path(s) {outcome}")
    if not arguments.apply:
        print("dry run only; pass --apply to remove the listed paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
