#!/usr/bin/env python3
"""Shared release-content classification and manifest helpers."""

from __future__ import annotations

from dataclasses import dataclass
import fnmatch
import hashlib
from pathlib import Path
import subprocess
import tomllib
from typing import Any, Iterable


POLICY_PATH = Path("release/release-content.toml")


@dataclass(frozen=True)
class Provenance:
    identifier: str
    origin: str
    license: str
    redistribution: str
    third_party: bool = False
    notice_key: str = ""


@dataclass(frozen=True)
class Rule:
    pattern: str
    include: bool
    category: str
    provenance: str
    reason: str


@dataclass(frozen=True)
class Classification:
    include: bool
    category: str
    provenance: Provenance
    reason: str
    pattern: str


@dataclass(frozen=True)
class Policy:
    default_include: bool
    default_category: str
    default_provenance: str
    provenance: dict[str, Provenance]
    rules: tuple[Rule, ...]

    def classify(self, path: str) -> Classification:
        normalized = path.replace("\\", "/").lstrip("./")
        for rule in self.rules:
            if fnmatch.fnmatchcase(normalized, rule.pattern):
                return Classification(
                    include=rule.include,
                    category=rule.category,
                    provenance=self.provenance[rule.provenance],
                    reason=rule.reason,
                    pattern=rule.pattern,
                )
        return Classification(
            include=self.default_include,
            category=self.default_category,
            provenance=self.provenance[self.default_provenance],
            reason="Default classification for maintained project material.",
            pattern="<default>",
        )


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def load_policy(root: Path) -> Policy:
    path = root / POLICY_PATH
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"unsupported release policy schema in {path}")

    provenance: dict[str, Provenance] = {}
    for identifier, item in payload.get("provenance", {}).items():
        provenance[identifier] = Provenance(
            identifier=identifier,
            origin=_required_text(item.get("origin"), f"provenance.{identifier}.origin"),
            license=_required_text(
                item.get("license"), f"provenance.{identifier}.license"
            ),
            redistribution=_required_text(
                item.get("redistribution"),
                f"provenance.{identifier}.redistribution",
            ),
            third_party=bool(item.get("third_party", False)),
            notice_key=str(item.get("notice_key", "")).strip(),
        )

    default_provenance = _required_text(
        payload.get("default_provenance"), "default_provenance"
    )
    if default_provenance not in provenance:
        raise ValueError(f"unknown default provenance: {default_provenance}")

    rules: list[Rule] = []
    for index, item in enumerate(payload.get("rules", [])):
        provenance_id = _required_text(
            item.get("provenance"), f"rules[{index}].provenance"
        )
        if provenance_id not in provenance:
            raise ValueError(
                f"rules[{index}] references unknown provenance {provenance_id}"
            )
        rules.append(
            Rule(
                pattern=_required_text(item.get("pattern"), f"rules[{index}].pattern"),
                include=bool(item.get("include", False)),
                category=_required_text(
                    item.get("category"), f"rules[{index}].category"
                ),
                provenance=provenance_id,
                reason=_required_text(item.get("reason"), f"rules[{index}].reason"),
            )
        )

    return Policy(
        default_include=bool(payload.get("default_include", False)),
        default_category=_required_text(
            payload.get("default_category"), "default_category"
        ),
        default_provenance=default_provenance,
        provenance=provenance,
        rules=tuple(rules),
    )


def run_git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=check,
        capture_output=True,
    )


def git_paths(root: Path, *, include_untracked: bool = False) -> list[str]:
    arguments = ["ls-files", "--cached"]
    if include_untracked:
        arguments.extend(["--others", "--exclude-standard"])
    arguments.append("-z")
    output = run_git(root, *arguments).stdout
    return sorted(
        {
            item.decode("utf-8", errors="strict")
            for item in output.split(b"\0")
            if item
        }
    )


def git_modes(root: Path) -> dict[str, str]:
    output = run_git(root, "ls-files", "--stage", "-z").stdout
    modes: dict[str, str] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        modes[raw_path.decode("utf-8", errors="strict")] = mode
    return modes


def git_dirty(root: Path) -> bool:
    return bool(run_git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout)


def git_commit(root: Path) -> str:
    return run_git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()


def git_remote(root: Path) -> str:
    result = run_git(root, "config", "--get", "remote.origin.url", check=False)
    return result.stdout.decode("utf-8", errors="replace").strip()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() or path.is_symlink():
            yield path
