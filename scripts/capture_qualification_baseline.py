#!/usr/bin/env python3
"""Run declared qualification gates and persist a reviewable baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "architecture" / "qualification-gates.toml"
DEFAULT_OUTPUT = REPO_ROOT / "architecture" / "qualification-baseline.json"
DEFAULT_LOG_ROOT = REPO_ROOT / "reports" / "architecture_qualification" / "logs"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _normalize_log(path: Path) -> None:
    """Remove terminal progress padding while preserving exact line endings."""
    content = path.read_bytes()
    normalized = re.sub(rb"[ \t]+(?=\r?$)", b"", content, flags=re.MULTILINE)
    if normalized != content:
        path.write_bytes(normalized)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return ordered[index]


def _runtime_command(configured_command: list[str]) -> list[str]:
    if configured_command and configured_command[0] in {"python", "python3"}:
        return [sys.executable, *configured_command[1:]]
    return configured_command


def _source_roots(repo_root: Path) -> list[Path]:
    """Return deterministic import roots for every in-repository UV project."""
    package_roots = {
        *repo_root.glob("*/src"),
        *repo_root.glob("workstation/*/src"),
    }
    return [repo_root, *sorted(package_roots)]


def _artifact_records(repo_root: Path, patterns: list[str]) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for pattern in patterns:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            artifacts.append(
                {
                    "path": path.relative_to(repo_root).as_posix(),
                    "sha256": _sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    unique = {artifact["path"]: artifact for artifact in artifacts}
    return [unique[path] for path in sorted(unique)]


def _result_json_evidence(
    gate: dict[str, Any], repo_root: Path
) -> dict[str, Any] | None:
    configured_path = gate.get("result_json")
    if configured_path is None:
        return None
    relative_path = Path(str(configured_path))
    path = repo_root / relative_path
    accepted_statuses = [
        str(value) for value in gate.get("accepted_result_statuses", ["ok"])
    ]
    evidence: dict[str, Any] = {
        "accepted_statuses": accepted_statuses,
        "path": relative_path.as_posix(),
    }
    if not path.is_file():
        return {
            **evidence,
            "accepted": False,
            "observed_status": "missing",
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            **evidence,
            "accepted": False,
            "error": type(exc).__name__,
            "observed_status": "invalid",
        }
    observed_status = str(payload.get("status", "missing"))
    return {
        **evidence,
        "accepted": observed_status in accepted_statuses,
        "observed_status": observed_status,
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _unittest_summary(log_path: Path) -> dict[str, Any] | None:
    text = log_path.read_text(encoding="utf-8")
    ran_matches = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", text, re.MULTILINE)
    outcomes = re.findall(r"^(FAIL|ERROR): (.+)$", text, re.MULTILINE)
    if not ran_matches and not outcomes:
        return None
    tests_run = int(ran_matches[-1][0]) if ran_matches else 0
    return {
        "errors": sorted(name for outcome, name in outcomes if outcome == "ERROR"),
        "failures": sorted(name for outcome, name in outcomes if outcome == "FAIL"),
        "tests_run": tests_run,
    }


def _run_once(
    *,
    gate: dict[str, Any],
    repo_root: Path,
    log_root: Path,
    run_number: int,
) -> dict[str, Any]:
    gate_id = str(gate["id"])
    cwd = repo_root / str(gate.get("cwd", "."))
    command = _runtime_command([str(value) for value in gate["command"]])
    env = os.environ.copy()
    env.update({str(key): str(value) for key, value in gate.get("env", {}).items()})
    source_roots = _source_roots(repo_root)
    existing_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_parts = [str(path) for path in source_roots]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"{gate_id}-run-{run_number}.log"
    started = time.perf_counter()
    try:
        with log_path.open("w", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
            try:
                returncode = process.wait(
                    timeout=int(gate.get("timeout_seconds", 1800))
                )
                failure = ""
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                returncode = None
                failure = "timeout"
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                raise
        _normalize_log(log_path)
        duration = round(time.perf_counter() - started, 3)
        status = "passed" if returncode == 0 else "failed"
    except FileNotFoundError as exc:
        duration = round(time.perf_counter() - started, 3)
        log_path.write_text(str(exc) + "\n", encoding="utf-8")
        status = "blocked"
        returncode = None
        failure = "command_not_found"
    return {
        "duration_seconds": duration,
        "failure": failure,
        "log_path": log_path.relative_to(repo_root).as_posix(),
        "output_sha256": _sha256(log_path),
        "returncode": returncode,
        "status": status,
    }


def run_gate(
    *,
    gate: dict[str, Any],
    repo_root: Path,
    log_root: Path,
    repeat: int,
) -> dict[str, Any]:
    runs = [
        _run_once(
            gate=gate,
            repo_root=repo_root,
            log_root=log_root,
            run_number=index + 1,
        )
        for index in range(repeat)
    ]
    statuses = {run["status"] for run in runs}
    if statuses == {"passed"}:
        status = "passed"
    elif "failed" in statuses:
        status = "failed"
    else:
        status = "blocked"
    durations = [float(run["duration_seconds"]) for run in runs]
    result = {
        "artifacts": _artifact_records(
            repo_root, [str(value) for value in gate.get("artifacts", [])]
        ),
        "category": str(gate["category"]),
        "command": [str(value) for value in gate["command"]],
        "cwd": str(gate.get("cwd", ".")),
        "environment_overrides": {
            str(key): (
                "<cleared>"
                if str(value) == ""
                else "<configured>"
                if any(marker in str(key).upper() for marker in ("KEY", "TOKEN", "SECRET"))
                else str(value)
            )
            for key, value in sorted(gate.get("env", {}).items())
        },
        "id": str(gate["id"]),
        "performance": {
            "median_seconds": round(statistics.median(durations), 3),
            "p95_seconds": round(_percentile_95(durations), 3),
            "runs": len(runs),
        },
        "required": bool(gate.get("required", True)),
        "runs": runs,
        "status": status,
    }
    result_evidence = _result_json_evidence(gate, repo_root)
    if result_evidence is not None:
        result["result_evidence"] = result_evidence
        if status == "passed" and not result_evidence["accepted"]:
            result["status"] = "failed"
            runs[-1]["failure"] = (
                "result_status_not_accepted:"
                f"{result_evidence['observed_status']}"
            )
    unittest_summary = _unittest_summary(repo_root / runs[-1]["log_path"])
    if unittest_summary is not None:
        result["unittest"] = unittest_summary
    return result


def not_run_gate(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifacts": [],
        "category": str(gate["category"]),
        "command": [str(value) for value in gate["command"]],
        "cwd": str(gate.get("cwd", ".")),
        "environment_overrides": {
            str(key): (
                "<cleared>"
                if str(value) == ""
                else "<configured>"
                if any(marker in str(key).upper() for marker in ("KEY", "TOKEN", "SECRET"))
                else str(value)
            )
            for key, value in sorted(gate.get("env", {}).items())
        },
        "id": str(gate["id"]),
        "performance": {"median_seconds": 0.0, "p95_seconds": 0.0, "runs": 0},
        "reason": str(
            gate.get("reason_not_default", "not selected for this qualification run")
        ),
        "required": bool(gate.get("required", True)),
        "runs": [],
        "status": "not_run",
    }


def _hydrate_unittest_summary(
    gate: dict[str, Any], repo_root: Path
) -> dict[str, Any]:
    if gate.get("unittest") or not gate.get("runs"):
        return gate
    log_path = repo_root / str(gate["runs"][-1].get("log_path", ""))
    if not log_path.is_file():
        return gate
    summary = _unittest_summary(log_path)
    if summary is not None:
        gate = {**gate, "unittest": summary}
    return gate


def compare_baselines(
    current: dict[str, Any], baseline: dict[str, Any]
) -> list[str]:
    regressions: list[str] = []
    policy = baseline.get("policy", {})
    median_limit = 1.0 + float(policy.get("max_median_regression_percent", 10.0)) / 100.0
    p95_limit = 1.0 + float(policy.get("max_p95_regression_percent", 10.0)) / 100.0
    prior_by_id = {gate["id"]: gate for gate in baseline.get("gates", [])}
    current_by_id = {gate["id"]: gate for gate in current.get("gates", [])}
    for gate_id, prior in sorted(prior_by_id.items()):
        gate = current_by_id.get(gate_id)
        if gate is None:
            regressions.append(f"missing gate: {gate_id}")
            continue
        if prior.get("status") == "passed" and gate.get("status") != "passed":
            regressions.append(
                f"gate no longer passes: {gate_id} ({gate.get('status', 'missing')})"
            )
        elif prior.get("status") == "failed":
            if gate.get("status") in {"blocked", "not_run"}:
                regressions.append(
                    f"failed gate is no longer observable: {gate_id} "
                    f"({gate.get('status')})"
                )
                continue
            prior_unittest = prior.get("unittest", {})
            current_unittest = gate.get("unittest", {})
            if (
                gate.get("status") == "failed"
                and prior_unittest
                and not current_unittest
            ):
                regressions.append(f"unittest result missing: {gate_id}")
            for outcome in ("errors", "failures"):
                new_outcomes = set(current_unittest.get(outcome, [])) - set(
                    prior_unittest.get(outcome, [])
                )
                regressions.extend(
                    f"new unittest {outcome[:-1]}: {gate_id}: {name}"
                    for name in sorted(new_outcomes)
                )
        prior_result = prior.get("result_evidence")
        current_result = gate.get("result_evidence")
        if prior_result and not current_result:
            regressions.append(f"nested result evidence missing: {gate_id}")
        elif prior_result and current_result:
            prior_status = prior_result.get("observed_status")
            current_status = current_result.get("observed_status")
            if current_status in {"invalid", "missing"}:
                regressions.append(
                    f"nested result is not observable: {gate_id} ({current_status})"
                )
            elif prior_status == "ok" and current_status != "ok":
                regressions.append(
                    f"nested result no longer ok: {gate_id} ({current_status})"
                )
        prior_artifacts = {
            item["path"]: item["sha256"] for item in prior.get("artifacts", [])
        }
        current_artifacts = {
            item["path"]: item["sha256"] for item in gate.get("artifacts", [])
        }
        for path, digest in prior_artifacts.items():
            if current_artifacts.get(path) != digest:
                regressions.append(f"artifact changed: {gate_id}: {path}")
        prior_performance = prior.get("performance", {})
        current_performance = gate.get("performance", {})
        if min(
            int(prior_performance.get("runs", 0)),
            int(current_performance.get("runs", 0)),
        ) >= 3:
            prior_median = float(prior_performance.get("median_seconds", 0.0))
            current_median = float(current_performance.get("median_seconds", 0.0))
            prior_p95 = float(prior_performance.get("p95_seconds", 0.0))
            current_p95 = float(current_performance.get("p95_seconds", 0.0))
            if prior_median > 0 and current_median > prior_median * median_limit:
                regressions.append(f"median performance regression: {gate_id}")
            if prior_p95 > 0 and current_p95 > prior_p95 * p95_limit:
                regressions.append(f"p95 performance regression: {gate_id}")
    return regressions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gate", action="append", dest="gate_ids")
    parser.add_argument("--include-manual", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--compare-to", type=Path)
    parser.add_argument("--merge-from", action="append", type=Path, default=[])
    parser.add_argument(
        "--assemble-only",
        action="store_true",
        help="run no gates; assemble the output from --merge-from baselines",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repeat < 1:
        print("--repeat must be at least 1", file=sys.stderr)
        return 2
    with args.config.open("rb") as handle:
        config = tomllib.load(handle)
    if config.get("schema_version") != 1:
        print("unsupported qualification gate schema", file=sys.stderr)
        return 2
    selected = set(args.gate_ids or [])
    configured_ids = {str(gate["id"]) for gate in config.get("gates", [])}
    unknown = selected - configured_ids
    if unknown:
        print("unknown gates: " + ", ".join(sorted(unknown)), file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    for gate in config.get("gates", []):
        gate_id = str(gate["id"])
        should_run = False if args.assemble_only else (
            gate_id in selected
            if selected
            else bool(gate.get("run_by_default", True)) or args.include_manual
        )
        if should_run:
            print(f"running qualification gate: {gate_id}", flush=True)
            results.append(
                run_gate(
                    gate=gate,
                    repo_root=REPO_ROOT,
                    log_root=DEFAULT_LOG_ROOT,
                    repeat=args.repeat,
                )
            )
        else:
            results.append(not_run_gate(gate))

    results_by_id = {result["id"]: result for result in results}
    for merge_path in args.merge_from:
        merged = json.loads(merge_path.read_text(encoding="utf-8"))
        for result in merged.get("gates", []):
            gate_id = result.get("id")
            if gate_id not in results_by_id:
                continue
            if (
                results_by_id[gate_id]["status"] == "not_run"
                and result.get("status") != "not_run"
            ):
                results_by_id[gate_id] = result
    results = [
        _hydrate_unittest_summary(results_by_id[str(gate["id"])], REPO_ROOT)
        for gate in config.get("gates", [])
    ]

    baseline = {
        "schema_version": 1,
        "policy": config.get("policy", {}),
        "gates": results,
        "summary": {
            status: sum(1 for result in results if result["status"] == status)
            for status in ("passed", "failed", "blocked", "not_run")
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_canonical_json(baseline), encoding="utf-8")

    regressions: list[str] = []
    if args.compare_to:
        prior = json.loads(args.compare_to.read_text(encoding="utf-8"))
        regressions = compare_baselines(baseline, prior)
        for regression in regressions:
            print(f"qualification regression: {regression}", file=sys.stderr)
    print(_canonical_json(baseline["summary"]), end="")
    required_failures = [
        result
        for result in results
        if result["required"] and result["status"] in {"failed", "blocked"}
    ]
    return 1 if required_failures or regressions else 0


if __name__ == "__main__":
    raise SystemExit(main())
