#!/usr/bin/env python3
"""Build a deterministic, classified source-release directory."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import tempfile

from release_content import (
    POLICY_PATH,
    git_commit,
    git_dirty,
    git_modes,
    git_paths,
    git_remote,
    load_policy,
    sha256_path,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "release-manifest.json"


def _inside(path: Path, possible_parent: Path) -> bool:
    try:
        path.relative_to(possible_parent)
        return True
    except ValueError:
        return False


def build_export(
    root: Path,
    output: Path,
    *,
    allow_dirty: bool = False,
    include_untracked: bool = False,
) -> dict[str, object]:
    root = root.resolve()
    output = output.resolve()
    if _inside(output, root):
        raise ValueError("release output must be outside the source repository")
    if output.exists():
        raise FileExistsError(f"release output already exists: {output}")

    dirty = git_dirty(root)
    if dirty and not allow_dirty:
        raise RuntimeError("refusing to build a release from a dirty worktree")
    if include_untracked and not allow_dirty:
        raise ValueError("--include-untracked requires --allow-dirty")

    policy = load_policy(root)
    modes = git_modes(root)
    entries: list[dict[str, object]] = []
    excluded = Counter()
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=str(output.parent))
    )
    try:
        for relative in git_paths(root, include_untracked=include_untracked):
            source = root / relative
            if not source.exists() and not source.is_symlink():
                continue
            classification = policy.classify(relative)
            if not classification.include:
                excluded[classification.category] += 1
                continue
            if source.is_symlink():
                raise RuntimeError(f"included symlink requires explicit handling: {relative}")
            if not source.is_file():
                continue

            git_mode = modes.get(relative)
            if git_mode == "120000":
                raise RuntimeError(f"included Git symlink requires explicit handling: {relative}")
            normalized_mode = 0o755 if git_mode == "100755" else 0o644
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            destination.chmod(normalized_mode)
            os.utime(destination, (0, 0))
            size = destination.stat().st_size
            entries.append(
                {
                    "path": relative,
                    "sha256": sha256_path(destination),
                    "size": size,
                    "mode": f"{normalized_mode:o}",
                    "category": classification.category,
                    "provenance": classification.provenance.identifier,
                    "license": classification.provenance.license,
                    "classification_rule": classification.pattern,
                }
            )

        manifest: dict[str, object] = {
            "schema_version": 1,
            "source": {
                "repository": git_remote(root),
                "commit": git_commit(root),
                "dirty": dirty,
                "included_untracked": include_untracked,
                "classification_policy": POLICY_PATH.as_posix(),
                "classification_policy_sha256": sha256_path(root / POLICY_PATH),
            },
            "summary": {
                "file_count": len(entries),
                "total_bytes": sum(int(entry["size"]) for entry in entries),
                "category_counts": dict(
                    sorted(Counter(str(entry["category"]) for entry in entries).items())
                ),
                "excluded_counts": dict(sorted(excluded.items())),
            },
            "files": entries,
        }
        manifest_path = temporary / MANIFEST_NAME
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest_path.chmod(0o644)
        os.utime(manifest_path, (0, 0))
        for directory in sorted(
            (path for path in temporary.rglob("*") if path.is_dir()), reverse=True
        ):
            directory.chmod(0o755)
            os.utime(directory, (0, 0))
        os.replace(temporary, output)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--include-untracked", action="store_true")
    arguments = parser.parse_args()
    manifest = build_export(
        arguments.root,
        arguments.output,
        allow_dirty=arguments.allow_dirty,
        include_untracked=arguments.include_untracked,
    )
    print(json.dumps(manifest["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
