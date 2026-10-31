# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


TRIALS_ROOT = Path(__file__).resolve().parent
ROOT = TRIALS_ROOT.parent
MAIN_COMMAND = (sys.executable, "-m", "main")
REPORT_ROOT = ROOT / "reports"
LOCAL_ENV = ROOT / "local.env"


def _elapsed_seconds(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)


def resolve_trial_markdown_path(name: str) -> Path:
    """
    High Level Purpose:
        In circumstances like running trial curricula after files have moved between the repository root and the trials folder, helps with resolving the current markdown source path.

    Reference to Theory:
        Keeps the trial validation surface pointed at the intended learning corpus so decomposition, reuse, and composition are measured against the right material.

    Example Input Output:
        Input: `resolve_trial_markdown_path(name='LEARN_NEWTOWNS_LAWS.md')`
        Output: Path('/workspace/realized/trials/LEARN_NEWTOWNS_LAWS.md')

    Args:
        name: Value for `name` used by `resolve_trial_markdown_path`. Expected type: `str`.

    Returns:
        Path: Result produced by `resolve_trial_markdown_path`.
    """
    trial_path = TRIALS_ROOT / name
    if trial_path.exists():
        return trial_path
    return ROOT / name


def resolve_trial_bundle_path(markdown_path: Path) -> Path | None:
    """
    High Level Purpose:
        In circumstances like rerunning learned-function trials under the current governed artifact posture, helps with finding the colocated exported/importable YAML bundle that can replace fresh LLM learning.

    Reference to Theory:
        Keeps the validator aligned with the current governance posture by preferring persisted governed artifacts when they already exist.

    Example Input Output:
        Input: `resolve_trial_bundle_path(markdown_path=Path('/workspace/realized/trials/LEARN_MOMENTUM.md'))`
        Output: Path('/workspace/realized/trials/LEARN_MOMENTUM.yaml')

    Args:
        markdown_path: Value for `markdown_path` used by `resolve_trial_bundle_path`. Expected type: `Path`.

    Returns:
        Path | None: Result produced by `resolve_trial_bundle_path`.
    """
    candidate = markdown_path.with_suffix(".yaml")
    if candidate.exists():
        return candidate
    return None


def load_local_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with loading local environment variables from disk.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `load_local_env()`
        Output: {'OPENAI_API_KEY': 'test-key'}

    Args:
        None.

    Returns:
        dict[str, str]: Result produced by `load_local_env`.
    """
    if not LOCAL_ENV.exists():
        return {}
    result: dict[str, str] = {}
    for raw_line in LOCAL_ENV.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def run_cli(args: list[str], *, env: dict[str, str]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling run cli.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `run_cli(args=['mass', 'acceleration', 'force'], env={'OPENAI_API_KEY': 'test-key'})`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        args: Value for `args` used by `run_cli`. Expected type: `list[str]`.
        env: Value for `env` used by `run_cli`. Expected type: `dict[str, str]`.

    Returns:
        dict[str, Any]: Result produced by `run_cli`.
    """
    timeout_seconds = int(str(env.get("TRIAL_TIMEOUT_SECONDS", "180")).strip() or "180")
    started_at = time.perf_counter()
    completed = subprocess.run(
        [*MAIN_COMMAND, *args],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout_seconds,
    )
    stdout = completed.stdout.strip()
    payload = json.loads(stdout) if stdout else {}
    if isinstance(payload, dict):
        payload.setdefault("elapsed_seconds", _elapsed_seconds(started_at))
    return payload if isinstance(payload, dict) else {"elapsed_seconds": _elapsed_seconds(started_at)}


def extract_numeric_answer(value: str) -> float:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling extract numeric answer.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `extract_numeric_answer(value='force')`
        Output: 0.75

    Args:
        value: Value for `value` used by `extract_numeric_answer`. Expected type: `str`.

    Returns:
        float: Result produced by `extract_numeric_answer`.
    """
    text = str(value or "").strip()
    if not text:
        raise AssertionError("Expected a numeric final_answer, got empty text.")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        raise AssertionError(f"Could not parse numeric answer from {text!r}.")
    return float(match.group(0))


def find_artifact_context(state_path: Path) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with building context for find artifact.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `find_artifact_context(state_path=Path('/tmp/physics_force.md'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        state_path: Value for `state_path` used by `find_artifact_context`. Expected type: `Path`.

    Returns:
        dict[str, Any]: Result produced by `find_artifact_context`.
    """
    state = json.loads(state_path.read_text())
    for evidence in state.get("evidence", {}).values():
        context = evidence.get("context", {})
        if context.get("artifact_id"):
            return context
    raise AssertionError(f"No artifact-backed evidence context found in {state_path}")


def artifact_details(sqlite_path: Path, artifact_id: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact details.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_details(sqlite_path=Path('/tmp/physics_force.md'), artifact_id='artifact-force')`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        sqlite_path: Value for `sqlite_path` used by `artifact_details`. Expected type: `Path`.
        artifact_id: Value for `artifact_id` used by `artifact_details`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `artifact_details`.
    """
    connection = sqlite3.connect(str(sqlite_path))
    try:
        row = connection.execute(
            """
            SELECT title, artifact_type, function_bit
            FROM bssc_artifacts
            WHERE artifact_id = ?
            LIMIT 1
            """,
            (artifact_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return {"title": "", "artifact_type": "", "function_bit": 0}
    return {
        "title": str(row[0] or ""),
        "artifact_type": str(row[1] or ""),
        "function_bit": int(row[2] or 0),
    }


def function_artifact_count(sqlite_path: Path) -> int:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling function artifact count.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `function_artifact_count(sqlite_path=Path('/tmp/physics_force.md'))`
        Output: 3

    Args:
        sqlite_path: Value for `sqlite_path` used by `function_artifact_count`. Expected type: `Path`.

    Returns:
        int: Result produced by `function_artifact_count`.
    """
    connection = sqlite3.connect(str(sqlite_path))
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM bssc_artifacts WHERE artifact_type = 'ability' AND function_bit = 1"
        ).fetchone()
    finally:
        connection.close()
    return int(row[0] or 0) if row else 0


@dataclass(frozen=True)
class FunctionCase:
    slug: str
    prompt: str
    expected_value: float
    tolerance: float = 1e-9


@dataclass(frozen=True)
class DomainSpec:
    slug: str
    markdown_file: Path
    learn_max_artifacts: int
    cases: tuple[FunctionCase, ...]


def build_domain_specs(seed: int) -> list[DomainSpec]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with building domain specs.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `build_domain_specs(seed=3)`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        seed: Value for `seed` used by `build_domain_specs`. Expected type: `int`.

    Returns:
        list[DomainSpec]: Result produced by `build_domain_specs`.
    """
    rng = random.Random(seed)

    newton_pairs = [(3, 4), (5, 2), (rng.randint(6, 9), rng.randint(3, 7))]
    momentum_pairs = [(8, 12), (10, 5), (rng.randint(3, 9), rng.randint(4, 9))]
    pythagorean_pairs = [(5, 5), (3, 4), (8, 15)]

    return [
        DomainSpec(
            slug="newton_force",
            markdown_file=resolve_trial_markdown_path("LEARN_NEWTOWNS_LAWS.md"),
            learn_max_artifacts=8,
            cases=(
                FunctionCase(
                    slug="force_3_4",
                    prompt=f"Calculate force for mass={newton_pairs[0][0]} and acceleration={newton_pairs[0][1]}.",
                    expected_value=float(newton_pairs[0][0] * newton_pairs[0][1]),
                ),
                FunctionCase(
                    slug="force_5_2",
                    prompt=f"Use Newton's second law to compute force with mass={newton_pairs[1][0]} and acceleration={newton_pairs[1][1]}.",
                    expected_value=float(newton_pairs[1][0] * newton_pairs[1][1]),
                ),
                FunctionCase(
                    slug="force_random",
                    prompt=f"What force do you get for mass={newton_pairs[2][0]} and acceleration={newton_pairs[2][1]}?",
                    expected_value=float(newton_pairs[2][0] * newton_pairs[2][1]),
                ),
            ),
        ),
        DomainSpec(
            slug="pythagorean_hypotenuse",
            markdown_file=resolve_trial_markdown_path("GAIN_PYTHOGOREAN_THEORM.md"),
            learn_max_artifacts=8,
            cases=(
                FunctionCase(
                    slug="equal_sides",
                    prompt="Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each",
                    expected_value=math.sqrt(5**2 + 5**2),
                ),
                FunctionCase(
                    slug="three_four_five",
                    prompt=f"What is the length of the hypotenuse when a={pythagorean_pairs[1][0]} and b={pythagorean_pairs[1][1]}?",
                    expected_value=math.sqrt(pythagorean_pairs[1][0] ** 2 + pythagorean_pairs[1][1] ** 2),
                ),
                FunctionCase(
                    slug="eight_fifteen_seventeen",
                    prompt=f"Calculate the slanted side if a={pythagorean_pairs[2][0]} and b={pythagorean_pairs[2][1]}.",
                    expected_value=math.sqrt(pythagorean_pairs[2][0] ** 2 + pythagorean_pairs[2][1] ** 2),
                ),
            ),
        ),
        DomainSpec(
            slug="momentum",
            markdown_file=resolve_trial_markdown_path("LEARN_MOMENTUM.md"),
            learn_max_artifacts=10,
            cases=(
                FunctionCase(
                    slug="momentum_8_12",
                    prompt=f"Calculate momentum for mass={momentum_pairs[0][0]} and velocity={momentum_pairs[0][1]}.",
                    expected_value=float(momentum_pairs[0][0] * momentum_pairs[0][1]),
                ),
                FunctionCase(
                    slug="momentum_10_5",
                    prompt=f"Calculate momentum for mass={momentum_pairs[1][0]} and velocity={momentum_pairs[1][1]}.",
                    expected_value=float(momentum_pairs[1][0] * momentum_pairs[1][1]),
                ),
                FunctionCase(
                    slug="momentum_random",
                    prompt=f"What is the momentum when mass is {momentum_pairs[2][0]} and velocity is {momentum_pairs[2][1]}?",
                    expected_value=float(momentum_pairs[2][0] * momentum_pairs[2][1]),
                ),
            ),
        ),
    ]


def run_domain(
    spec: DomainSpec,
    *,
    base_report_dir: Path,
    base_env: dict[str, str],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling run domain.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `run_domain(spec=DomainSpec(name='force', learn_file=Path('/tmp/physics_force.md')), base_report_dir=Path('/tmp/physics_force.md'), base_env={'OPENAI_API_KEY': 'test-key'})`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        spec: Value for `spec` used by `run_domain`. Expected type: `DomainSpec`.
        base_report_dir: Value for `base_report_dir` used by `run_domain`. Expected type: `Path`.
        base_env: Value for `base_env` used by `run_domain`. Expected type: `dict[str, str]`.

    Returns:
        dict[str, Any]: Result produced by `run_domain`.
    """
    domain_dir = base_report_dir / spec.slug
    domain_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = domain_dir / f"{spec.slug}.sqlite3"

    env = base_env.copy()
    env["STATE_SQLITE_PATH"] = str(sqlite_path)
    for key in ("STATE_DB_URL", "STATE_DB_HOST", "STATE_DB_PORT", "STATE_DB_USER", "STATE_DB_PASSWORD", "STATE_DB_NAME"):
        env.pop(key, None)

    learn_state_path = domain_dir / "learn_state.json"
    learn_report_path = domain_dir / "learn_report.json"
    bundle_path = resolve_trial_bundle_path(spec.markdown_file)
    try:
        if bundle_path is not None:
            learn_result = run_cli(
                [
                    "artifact-import",
                    "--artifact-file",
                    str(bundle_path),
                ],
                env=env,
            )
        else:
            learn_result = run_cli(
                [
                    "markdown-learn",
                    "--markdown-file",
                    str(spec.markdown_file),
                    "--llm",
                    "required",
                    "--max-artifacts",
                    str(spec.learn_max_artifacts),
                    "--state-out",
                    str(learn_state_path),
                    "--report-out",
                    str(learn_report_path),
                ],
                env=env,
            )
    except subprocess.TimeoutExpired as exc:
        return {
            "slug": spec.slug,
            "markdown_file": str(spec.markdown_file),
            "bundle_file": str(bundle_path) if bundle_path is not None else "",
            "learn_mode": "artifact_import" if bundle_path is not None else "markdown_learn",
            "sqlite_path": str(sqlite_path),
            "learn_report_path": str(learn_report_path),
            "learn_state_path": str(learn_state_path),
            "learned_count": 0,
            "learn_elapsed_seconds": float(exc.timeout or 0),
            "persisted_function_artifact_count": function_artifact_count(sqlite_path) if sqlite_path.exists() else 0,
            "cases": [],
            "status": "failed",
            "failures": [f"{spec.slug}: learn/import timed out after {exc.timeout} seconds"],
        }

    cases: list[dict[str, Any]] = []
    failures: list[str] = []
    persisted_function_count = function_artifact_count(sqlite_path)
    if persisted_function_count < 1:
        failures.append(f"{spec.slug}: expected at least one persisted function_bit=1 ability artifact after learning.")

    for case in spec.cases:
        state_out = domain_dir / f"{case.slug}.json"
        try:
            run_result = run_cli(
                [
                    "run",
                    "--prompt",
                    case.prompt,
                    "--llm",
                    "off",
                    "--max-steps",
                    "24",
                    "--state-out",
                    str(state_out),
                ],
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            failures.append(f"{spec.slug}/{case.slug}: run timed out after {exc.timeout} seconds")
            cases.append(
                {
                    "slug": case.slug,
                    "prompt": case.prompt,
                    "expected_value": case.expected_value,
                    "observed_value": None,
                    "elapsed_seconds": float(exc.timeout or 0),
                    "run_outcome": "timeout",
                    "final_answer": "",
                    "artifact_id": "",
                    "artifact_title": "",
                    "artifact_type": "",
                    "function_bit": 0,
                    "cross_boundary_execution": False,
                    "state_path": str(state_out),
                }
            )
            continue
        context = find_artifact_context(state_out)
        details = artifact_details(sqlite_path, str(context.get("artifact_id", "")))
        observed_value = extract_numeric_answer(str(run_result.get("final_answer", "")))
        value_ok = math.isclose(observed_value, case.expected_value, rel_tol=case.tolerance, abs_tol=case.tolerance)

        case_result = {
            "slug": case.slug,
            "prompt": case.prompt,
            "expected_value": case.expected_value,
            "observed_value": observed_value,
            "elapsed_seconds": float(run_result.get("elapsed_seconds", 0.0) or 0.0),
            "run_outcome": run_result.get("run_outcome", ""),
            "final_answer": run_result.get("final_answer", ""),
            "artifact_id": context.get("artifact_id", ""),
            "artifact_title": details["title"],
            "artifact_type": details["artifact_type"],
            "function_bit": details["function_bit"],
            "cross_boundary_execution": bool(context.get("cross_boundary_execution")),
            "state_path": str(state_out),
        }
        cases.append(case_result)

        if run_result.get("run_outcome") != "completed":
            failures.append(f"{spec.slug}/{case.slug}: expected completed, got {run_result.get('run_outcome')!r}")
        if not value_ok:
            failures.append(
                f"{spec.slug}/{case.slug}: expected numeric answer {case.expected_value!r}, got {run_result.get('final_answer')!r}"
            )
        if details["artifact_type"] != "ability":
            failures.append(f"{spec.slug}/{case.slug}: expected ability artifact, got {details['artifact_type']!r}")
        if details["function_bit"] != 1:
            failures.append(f"{spec.slug}/{case.slug}: expected function_bit=1, got {details['function_bit']!r}")
        if not context.get("cross_boundary_execution"):
            failures.append(f"{spec.slug}/{case.slug}: expected cross_boundary execution to be true")

    return {
        "slug": spec.slug,
        "markdown_file": str(spec.markdown_file),
        "bundle_file": str(bundle_path) if bundle_path is not None else "",
        "learn_mode": "artifact_import" if bundle_path is not None else "markdown_learn",
        "sqlite_path": str(sqlite_path),
        "learn_report_path": str(learn_report_path),
        "learn_state_path": str(learn_state_path),
        "learned_count": int(learn_result.get("learned_count", 0)),
        "learn_elapsed_seconds": float(learn_result.get("elapsed_seconds", 0.0) or 0.0),
        "persisted_function_artifact_count": persisted_function_count,
        "cases": cases,
        "status": "ok" if not failures else "failed",
        "failures": failures,
    }


def main() -> int:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling main.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `main()`
        Output: 3

    Args:
        None.

    Returns:
        int: Result produced by `main`.
    """
    parser = argparse.ArgumentParser(description="Run fresh-db learned-function validation across markdown curricula.")
    parser.add_argument(
        "--report-dir",
        type=Path,
        help="Optional report directory. Defaults to reports/learned_function_validation_<timestamp>.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic seed for any generated numeric cases.",
    )
    parser.add_argument(
        "--domains",
        nargs="+",
        help="Optional domain slugs to run, such as newton_force pythagorean_hypotenuse momentum.",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    env.update(load_local_env())
    if not env.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured in the environment or local.env.")
    env["LLM_PROVIDER"] = "openai"
    env["LLM_TIMEOUT_SECONDS"] = env.get("LLM_TIMEOUT_SECONDS", "180")
    env["TRIAL_TIMEOUT_SECONDS"] = env.get("TRIAL_TIMEOUT_SECONDS", "180")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = args.report_dir or (REPORT_ROOT / f"learned_function_validation_{timestamp}")
    report_dir.mkdir(parents=True, exist_ok=True)

    all_specs = build_domain_specs(args.seed)
    if args.domains:
        wanted = {item.strip() for item in args.domains if item.strip()}
        specs = [spec for spec in all_specs if spec.slug in wanted]
        missing = sorted(wanted - {spec.slug for spec in specs})
        if missing:
            raise SystemExit(f"Unknown domain slugs: {', '.join(missing)}")
    else:
        specs = all_specs

    domain_reports = [run_domain(spec, base_report_dir=report_dir, base_env=env) for spec in specs]
    failures = [failure for report in domain_reports for failure in report["failures"]]

    report = {
        "domains_requested": [spec.slug for spec in specs],
        "seed": args.seed,
        "report_dir": str(report_dir),
        "status": "ok" if not failures else "failed",
        "domains": domain_reports,
        "failures": failures,
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
