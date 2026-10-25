#!/usr/bin/env python3
"""Verify release hashes, classifications, notices, and public package metadata."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import stat
import tomllib

from release_content import POLICY_PATH, iter_files, load_policy, sha256_path


MANIFEST_NAME = "release-manifest.json"
PUBLIC_PACKAGES = {
    "core_app": "realized-core",
    "core_engine": "realized-core-engine",
    "core_runtime": "realized-core-runtime",
    "host_interaction": "realized-host-interaction",
}
REQUIRED_CLASSIFIERS = {
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.14",
}
SUPERSEDED_LICENSE_CLASSIFIER = "License :: OSI Approved :: Apache Software License"
REQUIRED_URLS = {"Homepage", "Repository", "Issues"}


def _package_errors(root: Path) -> list[str]:
    errors: list[str] = []
    for directory, expected_name in PUBLIC_PACKAGES.items():
        package_root = root / directory
        metadata_path = package_root / "pyproject.toml"
        if not metadata_path.is_file():
            errors.append(f"missing public package metadata: {metadata_path}")
            continue
        payload = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
        project = payload.get("project", {})
        if project.get("name") != expected_name:
            errors.append(f"{metadata_path}: unexpected project name")
        if project.get("license") != "Apache-2.0":
            errors.append(f"{metadata_path}: license must be Apache-2.0")
        if not project.get("authors"):
            errors.append(f"{metadata_path}: authors are required")
        if not project.get("maintainers"):
            errors.append(f"{metadata_path}: maintainers are required")
        classifiers = set(project.get("classifiers", []))
        missing_classifiers = REQUIRED_CLASSIFIERS - classifiers
        if missing_classifiers:
            errors.append(
                f"{metadata_path}: missing classifiers {sorted(missing_classifiers)}"
            )
        if SUPERSEDED_LICENSE_CLASSIFIER in classifiers:
            errors.append(
                f"{metadata_path}: use the PEP 639 license expression, not its superseded classifier"
            )
        urls = project.get("urls", {})
        if not REQUIRED_URLS.issubset(urls):
            errors.append(f"{metadata_path}: missing required project URLs")
        if project.get("license-files") != ["LICENSE"]:
            errors.append(f"{metadata_path}: license-files must contain LICENSE")
        package_license = package_root / "LICENSE"
        if not package_license.is_file():
            errors.append(f"missing packaged license: {package_license}")
        elif package_license.read_bytes() != (root / "LICENSE").read_bytes():
            errors.append(f"packaged license differs from root LICENSE: {package_license}")
    return errors


def verify_stage(root: Path, *, allow_dirty: bool = False) -> dict[str, object]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        raise ValueError(f"missing {MANIFEST_NAME} in {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        errors.append("unsupported release manifest schema")
    source = manifest.get("source", {})
    if source.get("dirty") and not allow_dirty:
        errors.append("release manifest was built from a dirty worktree")

    policy = load_policy(root)
    policy_digest = sha256_path(root / POLICY_PATH)
    if source.get("classification_policy_sha256") != policy_digest:
        errors.append("classification policy digest does not match the manifest")

    expected_paths: set[str] = set()
    category_counts: Counter[str] = Counter()
    for entry in manifest.get("files", []):
        relative = str(entry.get("path", ""))
        if not relative or relative in expected_paths:
            errors.append(f"invalid or duplicate manifest path: {relative!r}")
            continue
        expected_paths.add(relative)
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing or non-regular staged file: {relative}")
            continue
        classification = policy.classify(relative)
        if not classification.include:
            errors.append(f"excluded path is present in the stage: {relative}")
        expected_values = {
            "category": classification.category,
            "provenance": classification.provenance.identifier,
            "license": classification.provenance.license,
            "classification_rule": classification.pattern,
        }
        for key, expected in expected_values.items():
            if entry.get(key) != expected:
                errors.append(f"{relative}: manifest {key} does not match policy")
        if entry.get("sha256") != sha256_path(path):
            errors.append(f"{relative}: SHA-256 mismatch")
        if entry.get("size") != path.stat().st_size:
            errors.append(f"{relative}: size mismatch")
        actual_mode = "755" if path.stat().st_mode & stat.S_IXUSR else "644"
        if entry.get("mode") != actual_mode:
            errors.append(f"{relative}: normalized mode mismatch")
        category_counts[classification.category] += 1

    actual_paths = {
        path.relative_to(root).as_posix()
        for path in iter_files(root)
        if path.name != MANIFEST_NAME
    }
    for relative in sorted(expected_paths - actual_paths):
        errors.append(f"manifest path absent from stage: {relative}")
    for relative in sorted(actual_paths - expected_paths):
        errors.append(f"unmanifested file in stage: {relative}")

    notices_path = root / "THIRD_PARTY_NOTICES.md"
    notices = notices_path.read_text(encoding="utf-8") if notices_path.is_file() else ""
    for item in policy.provenance.values():
        if item.third_party and item.notice_key not in notices:
            errors.append(f"missing third-party notice: {item.notice_key}")

    errors.extend(_package_errors(root))
    summary = {
        "status": "ok" if not errors else "failed",
        "file_count": len(expected_paths),
        "category_counts": dict(sorted(category_counts.items())),
        "errors": errors,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    arguments = parser.parse_args()
    summary = verify_stage(arguments.root, allow_dirty=arguments.allow_dirty)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
