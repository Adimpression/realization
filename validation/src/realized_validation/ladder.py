"""Repository acceptance-ladder orchestration for Realization validation."""

# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from realized_validation.paths import validation_repository_root


REPO_ROOT = validation_repository_root()
REPORTS_ROOT = REPO_ROOT / "reports"


def iso_now() -> str:
    """
    High Level Purpose:
        In circumstances like staged validation reporting, helps with emitting one stable UTC timestamp for report metadata.

    Reference to Theory:
        Supports disciplined validation observability without changing controller or workstation semantics.

    Example Input Output:
        Input: `iso_now()`
        Output: '2026-04-08T00:30:00+00:00'

    Args:
        None.

    Returns:
        str: Result produced by `iso_now`.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_running_report(report_root: Path) -> None:
    """
    High Level Purpose:
        In circumstances like long-running multi-stage acceptance execution, helps with writing an initial observable report before the first stage starts.

    Reference to Theory:
        Supports the validation doctrine requirement that long-running gates expose live state instead of looking hung.

    Example Input Output:
        Input: `write_running_report(report_root=Path('/tmp/validation_ladder'))`
        Output: None

    Args:
        report_root: Value for `report_root` used by `write_running_report`. Expected type: `Path`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    report = {
        "started_at": iso_now(),
        "finished_at": "",
        "status": "running",
        "stage": "unit_tests",
        "report_root": str(report_root),
        "stages": [],
    }
    (report_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")


def run_stage_command(
    *,
    name: str,
    cmd: list[str],
    cwd: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like running one layer in the staged validation ladder, helps with executing the command and returning a compact structured result.

    Reference to Theory:
        Supports layered acceptance by keeping each stage explicit, bounded, and reportable.

    Example Input Output:
        Input: `run_stage_command(name='unit_tests', cmd=['python3', '-m', 'unittest'], cwd=Path('/repo'), env={})`
        Output: {'name': 'unit_tests', 'status': 'ok', 'returncode': 0}

    Args:
        name: Value for `name` used by `run_stage_command`. Expected type: `str`.
        cmd: Value for `cmd` used by `run_stage_command`. Expected type: `list[str]`.
        cwd: Value for `cwd` used by `run_stage_command`. Expected type: `Path`.
        env: Value for `env` used by `run_stage_command`. Expected type: `dict[str, str]`.

    Returns:
        dict[str, Any]: Result produced by `run_stage_command`.
    """
    started = time.perf_counter()
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
    )
    elapsed_seconds = round(time.perf_counter() - started, 6)
    return {
        "name": name,
        "cmd": cmd,
        "cwd": str(cwd),
        "status": "ok" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "elapsed_seconds": elapsed_seconds,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def load_json_if_exists(path: Path) -> Any:
    """
    High Level Purpose:
        In circumstances like layered validation report aggregation, helps with loading nested stage reports only when they exist.

    Reference to Theory:
        Supports explicit observability for staged validation without fabricating nested results.

    Example Input Output:
        Input: `load_json_if_exists(Path('/tmp/report.json'))`
        Output: {'status': 'ok'}

    Args:
        path: Value for `path` used by `load_json_if_exists`. Expected type: `Path`.

    Returns:
        Any: Result produced by `load_json_if_exists`.
    """
    if not path.exists():
        return None
    return json.loads(path.read_text())


def write_report(report_root: Path, report: dict[str, Any]) -> None:
    """
    High Level Purpose:
        In circumstances like staged validation ladder execution, helps with persisting the current top-level report after each stage transition.

    Reference to Theory:
        Supports validation observability and post-run diagnosis for layered acceptance.

    Example Input Output:
        Input: `write_report(Path('/tmp/validation_ladder'), {'status': 'running'})`
        Output: None

    Args:
        report_root: Value for `report_root` used by `write_report`. Expected type: `Path`.
        report: Value for `report` used by `write_report`. Expected type: `dict[str, Any]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    (report_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")


def run_validation_ladder(
    *,
    workspace: Path,
    report_root: Path,
    model: str = "",
    runner: Callable[..., dict[str, Any]] = run_stage_command,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like stabilization gating, helps with running the layered acceptance ladder in order: unit suite, workstation trial sweep, then chemistry milestone validation.

    Reference to Theory:
        Supports the validation doctrine by treating acceptance as layered and repeatable instead of one monolithic opaque pass/fail.

    Example Input Output:
        Input: `run_validation_ladder(workspace=Path('/repo'), report_root=Path('/tmp/validation_ladder'))`
        Output: {'status': 'ok', 'stages': [{'name': 'unit_tests', 'status': 'ok'}]}`

    Args:
        workspace: Value for `workspace` used by `run_validation_ladder`. Expected type: `Path`.
        report_root: Value for `report_root` used by `run_validation_ladder`. Expected type: `Path`.
        model: Value for `model` used by `run_validation_ladder`. Expected type: `str`. Defaults to `''`.
        runner: Value for `runner` used by `run_validation_ladder`. Expected type: `Callable[..., dict[str, Any]]`. Defaults to `run_stage_command`.

    Returns:
        dict[str, Any]: Result produced by `run_validation_ladder`.
    """
    report_root.mkdir(parents=True, exist_ok=True)
    write_running_report(report_root)

    env = os.environ.copy()
    env["STATE_VECTOR_MODE"] = env.get("STATE_VECTOR_MODE", "off")
    report = {
        "started_at": iso_now(),
        "finished_at": "",
        "status": "running",
        "stage": "unit_tests",
        "report_root": str(report_root),
        "stages": [],
    }
    write_report(report_root, report)

    stages: list[dict[str, Any]] = []

    unit_stage = runner(
        name="unit_tests",
        cmd=[sys.executable, "-m", "unittest", "discover", "-s", str(REPO_ROOT / "tests")],
        cwd=REPO_ROOT,
        env=env,
    )
    stages.append(unit_stage)
    report["stages"] = stages
    report["stage"] = "workstation_trials" if unit_stage["status"] == "ok" else "unit_tests"
    report["status"] = "running" if unit_stage["status"] == "ok" else "failed"
    write_report(report_root, report)
    if unit_stage["status"] != "ok":
        report["finished_at"] = iso_now()
        write_report(report_root, report)
        return report

    workstation_report_root = report_root / "workstation_trial_validation"
    workstation_report_out = report_root / "workstation_trial_validation_report.json"
    workstation_cmd = [
        sys.executable,
        str(REPO_ROOT / "main.py"),
        "workstation-trial-validate",
        "--workspace",
        str(workspace),
        "--report-root",
        str(workstation_report_root),
        "--report-out",
        str(workstation_report_out),
    ]
    if str(model).strip():
        workstation_cmd.extend(["--model", str(model).strip()])
    workstation_stage = runner(
        name="workstation_trials",
        cmd=workstation_cmd,
        cwd=REPO_ROOT,
        env=env,
    )
    workstation_stage["nested_report"] = load_json_if_exists(workstation_report_out)
    stages.append(workstation_stage)
    report["stages"] = stages
    report["stage"] = "chemistry_domain" if workstation_stage["status"] == "ok" else "workstation_trials"
    report["status"] = "running" if workstation_stage["status"] == "ok" else "failed"
    write_report(report_root, report)
    if workstation_stage["status"] != "ok":
        report["finished_at"] = iso_now()
        write_report(report_root, report)
        return report

    chemistry_report_root = report_root / "chemistry_domain_validation"
    chemistry_env = dict(env)
    chemistry_env["TRIAL_DOMAIN_VALIDATION_REPORT_ROOT"] = str(chemistry_report_root)
    chemistry_stage = runner(
        name="chemistry_domain",
        cmd=[sys.executable, str(REPO_ROOT / "TRIAL_DOMAIN_VALIDATION.py"), "--domains", "chemistry"],
        cwd=REPO_ROOT,
        env=chemistry_env,
    )
    chemistry_stage["nested_report"] = load_json_if_exists(chemistry_report_root / "report.json")
    stages.append(chemistry_stage)
    report["stages"] = stages
    report["stage"] = "finished"
    report["status"] = "ok" if chemistry_stage["status"] == "ok" else "failed"
    report["finished_at"] = iso_now()
    write_report(report_root, report)
    return report


def handle_validation_ladder_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like CLI-driven stabilization gating, helps with running the layered validation ladder and printing one compact JSON report.

    Reference to Theory:
        Supports the repository validation doctrine by making the layered acceptance path a first-class repeatable command.

    Example Input Output:
        Input: `handle_validation_ladder_command(args=Namespace(workspace=Path('/repo'), report_root=Path('/tmp/validation_ladder')))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `validation-ladder`.

    Returns:
        int: Process-style exit status.
    """
    report_root = Path(args.report_root) if getattr(args, "report_root", None) else REPORTS_ROOT / f"validation_ladder_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    report = run_validation_ladder(
        workspace=Path(args.workspace) if getattr(args, "workspace", None) else REPO_ROOT,
        report_root=report_root,
        model=str(getattr(args, "model", "") or ""),
    )
    if getattr(args, "report_out", None):
        Path(args.report_out).write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(json.dumps(report, indent=2, sort_keys=False))
    return 0 if report["status"] == "ok" else 1
