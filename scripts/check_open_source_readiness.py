#!/usr/bin/env python3
"""Audit a staged source tree for obvious open-source release blockers.

The audit is intentionally read-only and dependency-free. It is a hygiene
check, not a substitute for license review, provenance review, or a dedicated
secret scanner.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCUMENTS = (
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "RELEASE_CONTENT.md",
    "THIRD_PARTY_NOTICES.md",
)
REQUIRED_RELEASE_FILES = (
    "release/release-content.toml",
    "release/tooling.toml",
    "scripts/build_release_export.py",
    "scripts/check_release_provenance.py",
    "scripts/scan_release_secrets.py",
)
ENVIRONMENT_EXAMPLES = (
    "local.env.example",
    "offline.env.example",
)
LOCAL_CONFIGURATION = (
    "local.env",
    "offline.env",
)
LOCAL_DIRECTORIES = (
    ".idea",
    ".runtime_models",
    ".tmp_pdf_review",
    ".uv-cache",
    ".venv",
    "build",
    "dist",
    "ram",
    "state",
    "tmp",
    "venv",
)
GENERATED_DIRECTORY_NAMES = (
    ".dart_tool",
    ".gradle",
    ".mypy_cache",
    ".pycache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
)
CAPTURED_EVIDENCE_PATHS = (
    "reports/",
)
ARCHITECTURE_ESSENTIAL_FILES = frozenset(
    {
        "DEPENDENCY_REPORT.md",
        "README.md",
        "boundaries.toml",
        "dependency-baseline.json",
        "qualification-baseline.json",
        "qualification-gates.toml",
    }
)
FORBIDDEN_RELEASE_PATHS = (
    "CHAT_HISTORY.md",
)
FORBIDDEN_TEMPORARY_DOCUMENTS = (
    "TMP.md",
)
MARKDOWN_PROSE_PREFIX = re.compile(
    r"^\s*(?:(?:#{1,6}|>|[-+*]|\d+[.)])\s+)+"
)
AI_RESPONSE_RESIDUE = (
    re.compile(r"^\s*yes\.\s+(?:with|that|now)\b", re.IGNORECASE),
    re.compile(r"^\s*so yes\b", re.IGNORECASE),
    re.compile(r"^\s*so your intuition is right\b", re.IGNORECASE),
    re.compile(r"^\s*from (?:that|your) list\b", re.IGNORECASE),
    re.compile(r"^\s*so the honest answer is\b", re.IGNORECASE),
    re.compile(r"^\s*here is the clean mental model\b", re.IGNORECASE),
    re.compile(r"^\s*since you also asked\b", re.IGNORECASE),
    re.compile(r"^\s*implemented(?:\.|\s+the\b)", re.IGNORECASE),
    re.compile(r"^\s*you can summarize it internally as\b", re.IGNORECASE),
    re.compile(r"^\s*i (?:also )?(?:added|fixed|implemented|ran|verified)\b", re.IGNORECASE),
    re.compile(r"^\s*so i implemented\b", re.IGNORECASE),
    re.compile(r"^\s*one remaining limitation:\s*i would\b", re.IGNORECASE),
    re.compile(r"^\s*if you want the next step\b", re.IGNORECASE),
    re.compile(r"^\s*(?:clean )?next extension, if you want it\b", re.IGNORECASE),
    re.compile(r"\bif you want to keep pushing this\b", re.IGNORECASE),
    re.compile(r"^\s*below is an ebnf\b", re.IGNORECASE),
    re.compile(r"\bif you want,\s*(?:next\s+)?i can\b", re.IGNORECASE),
    re.compile(r"\bi can .+ next:\s*", re.IGNORECASE),
    re.compile(r"\bwould you like me to\b", re.IGNORECASE),
    re.compile(r"\byour final answer should\b", re.IGNORECASE),
    re.compile(
        r"^\s*phase\s+\d+\s+is now complete in the intended shape\b",
        re.IGNORECASE,
    ),
)
LICENSE_PATTERNS = (
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "COPYING",
    "COPYING.md",
    "COPYING.txt",
)
SECRET_NAME = re.compile(
    r"(?:^|_)(?:API_KEY|PASSWORD|PRIVATE_KEY|SECRET|TOKEN|CREDENTIALS?)(?:$|_)",
    re.IGNORECASE,
)
ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
QUOTE_PAIRS = {("'", "'"), ('"', '"')}


@dataclass(frozen=True, order=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def _display_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _license_files(root: Path) -> list[Path]:
    return sorted(
        {
            path
            for pattern in LICENSE_PATTERNS
            for path in root.glob(pattern)
            if path.is_file()
        }
    )


def _unquoted(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and (value[0], value[-1]) in QUOTE_PAIRS:
        return value[1:-1].strip()
    return value


def _environment_example_findings(path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = ASSIGNMENT.match(line.strip())
        if match is None:
            continue
        name, value = match.groups()
        if SECRET_NAME.search(name) and _unquoted(value):
            findings.append(
                Finding(
                    "blocker",
                    "nonempty-example-secret",
                    f"{_display_path(path, root)}:{line_number}",
                    f"{name} must be empty in a distributed environment example",
                )
            )
    return findings


def _artifact_findings(root: Path) -> Iterable[Finding]:
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        retained_directories: list[str] = []
        for name in directories:
            path = current_path / name
            if name == ".git":
                continue
            if current_path == root and name in LOCAL_DIRECTORIES:
                continue
            if name in GENERATED_DIRECTORY_NAMES:
                yield Finding(
                    "blocker",
                    "generated-cache",
                    _display_path(path, root),
                    "generated cache directory must not be distributed",
                )
                continue
            retained_directories.append(name)
        directories[:] = retained_directories
        for name in filenames:
            path = current_path / name
            if name == ".DS_Store":
                yield Finding(
                    "blocker",
                    "os-metadata",
                    _display_path(path, root),
                    "operating-system metadata must not be distributed",
                )
            elif ".sync-conflict-" in name:
                yield Finding(
                    "blocker",
                    "sync-conflict",
                    _display_path(path, root),
                    "synchronization-conflict file requires review and exclusion",
                )
            elif name.endswith((".pyc", ".pyo")):
                yield Finding(
                    "blocker",
                    "generated-bytecode",
                    _display_path(path, root),
                    "generated Python bytecode must not be distributed",
                )
            elif ".sqlite" in name.lower():
                yield Finding(
                    "blocker",
                    "local-database",
                    _display_path(path, root),
                    "local SQLite data must not be distributed without explicit review",
                )


def _is_captured_evidence(path: Path, root: Path) -> bool:
    relative_path = path.relative_to(root).as_posix()
    return any(
        relative_path == candidate.rstrip("/")
        or relative_path.startswith(candidate)
        for candidate in CAPTURED_EVIDENCE_PATHS
    )


def _authored_markdown_findings(root: Path) -> Iterable[Finding]:
    for path in sorted(root.rglob("*.md")):
        if not path.is_file() or _is_captured_evidence(path, root):
            continue
        relative_path = _display_path(path, root)
        if path.stat().st_size == 0:
            yield Finding(
                "blocker",
                "empty-document",
                relative_path,
                "empty authored Markdown must be removed or populated",
            )
            continue
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                prose_line = MARKDOWN_PROSE_PREFIX.sub("", line, count=1).lstrip("*_`")
                if "utm_source=chatgpt.com" in line.lower():
                    yield Finding(
                        "blocker",
                        "ai-copy-tracking-parameter",
                        f"{relative_path}:{line_number}",
                        "remove ChatGPT copy-tracking parameters from authored documentation",
                    )
                if any(pattern.search(prose_line) for pattern in AI_RESPONSE_RESIDUE):
                    yield Finding(
                        "blocker",
                        "ai-response-residue",
                        f"{relative_path}:{line_number}",
                        "rewrite conversational response residue as maintained documentation",
                    )


def _architecture_findings(root: Path) -> Iterable[Finding]:
    architecture_root = root / "architecture"
    if not architecture_root.is_dir():
        return
    for path in sorted(architecture_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(architecture_root).as_posix()
        if relative_path not in ARCHITECTURE_ESSENTIAL_FILES:
            yield Finding(
                "blocker",
                "nonessential-architecture-artifact",
                _display_path(path, root),
                "architecture contains only live boundary controls and current baselines",
            )


def audit(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []

    if not root.is_dir():
        return [
            Finding(
                "blocker",
                "missing-root",
                root.as_posix(),
                "release candidate root does not exist or is not a directory",
            )
        ]

    for document in REQUIRED_DOCUMENTS:
        if not (root / document).is_file():
            findings.append(
                Finding(
                    "blocker",
                    "missing-document",
                    document,
                    "required public project document is missing",
                )
            )

    for relative_path in REQUIRED_RELEASE_FILES:
        if not (root / relative_path).is_file():
            findings.append(
                Finding(
                    "blocker",
                    "missing-release-control",
                    relative_path,
                    "required release classification or verification control is missing",
                )
            )

    if not _license_files(root):
        findings.append(
            Finding(
                "blocker",
                "missing-license",
                "LICENSE",
                "an explicit license is required before public distribution",
            )
        )

    security_path = root / "SECURITY.md"
    if security_path.is_file() and "PUBLIC-SECURITY-CONTACT-REQUIRED" in security_path.read_text(
        encoding="utf-8"
    ):
        findings.append(
            Finding(
                "blocker",
                "missing-security-contact",
                "SECURITY.md",
                "replace the private-reporting placeholder before publication",
            )
        )

    for example in ENVIRONMENT_EXAMPLES:
        path = root / example
        if not path.is_file():
            findings.append(
                Finding(
                    "blocker",
                    "missing-environment-example",
                    example,
                    "credential-free environment example is missing",
                )
            )
            continue
        findings.extend(_environment_example_findings(path, root))

    for relative_path in LOCAL_CONFIGURATION:
        path = root / relative_path
        if path.exists():
            findings.append(
                Finding(
                    "blocker",
                    "local-configuration",
                    relative_path,
                    "local operational configuration must be excluded from the release",
                )
            )

    for relative_path in FORBIDDEN_RELEASE_PATHS:
        path = root / relative_path
        if path.exists():
            findings.append(
                Finding(
                    "blocker",
                    "private-transcript",
                    relative_path,
                    "raw private conversation history must not be distributed",
                )
            )

    for relative_path in FORBIDDEN_TEMPORARY_DOCUMENTS:
        path = root / relative_path
        if path.exists():
            findings.append(
                Finding(
                    "blocker",
                    "temporary-document",
                    relative_path,
                    "temporary working documentation must be removed or incorporated",
                )
            )

    for relative_path in LOCAL_DIRECTORIES:
        path = root / relative_path
        if path.exists():
            findings.append(
                Finding(
                    "blocker",
                    "local-directory",
                    relative_path,
                    "local runtime/build directory must be excluded from the release",
                )
            )

    findings.extend(_architecture_findings(root))
    findings.extend(_artifact_findings(root))
    findings.extend(_authored_markdown_findings(root))
    return sorted(set(findings))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=REPO_ROOT,
        help="staged release directory to audit (default: repository root)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=40,
        help="maximum detailed findings in text output; 0 prints all (default: 40)",
    )
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    findings = audit(arguments.root)
    if arguments.json:
        print(
            json.dumps(
                {
                    "ready": not findings,
                    "root": arguments.root.resolve().as_posix(),
                    "findings": [asdict(finding) for finding in findings],
                },
                indent=2,
                sort_keys=True,
            )
        )
    elif findings:
        print(f"NOT READY: {len(findings)} release blocker(s)")
        counts = Counter(finding.code for finding in findings)
        print("Summary:")
        for code, count in sorted(counts.items()):
            print(f"- {code}: {count}")
        visible_findings = (
            findings
            if arguments.max_findings == 0
            else findings[: max(arguments.max_findings, 0)]
        )
        print("Details:")
        for finding in visible_findings:
            print(
                f"- [{finding.code}] {finding.path}: {finding.message}"
            )
        hidden_count = len(findings) - len(visible_findings)
        if hidden_count:
            print(
                f"- ... {hidden_count} additional finding(s); use --json or "
                "--max-findings 0 for the complete list"
            )
    else:
        print("READY: no release-hygiene blockers detected")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
