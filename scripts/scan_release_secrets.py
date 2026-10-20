#!/usr/bin/env python3
"""Run the pinned Gitleaks scanner over Git history and an exact release stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLING_PATH = REPO_ROOT / "release" / "tooling.toml"


def _scanner_version(binary: Path) -> str:
    direct = subprocess.run(
        [str(binary), "version"], check=False, capture_output=True, text=True
    )
    output = f"{direct.stdout}\n{direct.stderr}"
    go = shutil.which("go")
    if go:
        module = subprocess.run(
            [go, "version", "-m", str(binary)],
            check=False,
            capture_output=True,
            text=True,
        )
        output += f"\n{module.stdout}\n{module.stderr}"
    return output


def _run_scan(binary: Path, command: str, target: Path, report: Path) -> int:
    result = subprocess.run(
        [
            str(binary),
            command,
            "--no-banner",
            "--redact=100",
            "--report-format",
            "json",
            "--report-path",
            str(report),
            str(target),
        ],
        check=False,
        text=True,
    )
    return result.returncode


def main() -> int:
    tooling = tomllib.loads(TOOLING_PATH.read_text(encoding="utf-8"))
    expected_version = str(tooling["secret_scanner"]["version"])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("--repository", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--gitleaks",
        type=Path,
        default=Path(shutil.which("gitleaks") or "gitleaks"),
    )
    parser.add_argument("--skip-history", action="store_true")
    arguments = parser.parse_args()

    if not arguments.stage.is_dir():
        parser.error(f"stage does not exist: {arguments.stage}")
    if not arguments.gitleaks.is_file():
        parser.error(f"gitleaks binary does not exist: {arguments.gitleaks}")
    if expected_version not in _scanner_version(arguments.gitleaks):
        parser.error(
            f"gitleaks {expected_version} is required; use the install command in release/tooling.toml"
        )

    results: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="realization-secret-scan-") as directory:
        report_root = Path(directory)
        targets = [("stage", "dir", arguments.stage)]
        if not arguments.skip_history:
            targets.insert(0, ("history", "git", arguments.repository))
        for label, command, target in targets:
            report = report_root / f"{label}.json"
            status = _run_scan(arguments.gitleaks, command, target, report)
            findings = json.loads(report.read_text(encoding="utf-8")) if report.exists() else []
            results[label] = {
                "status": "ok" if status == 0 and not findings else "findings",
                "finding_count": len(findings),
            }

    summary = {
        "scanner": "gitleaks",
        "version": expected_version,
        "results": results,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(item["status"] == "ok" for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
