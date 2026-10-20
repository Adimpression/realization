# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


TRIALS_ROOT = Path(__file__).resolve().parent
ROOT = TRIALS_ROOT.parent if (TRIALS_ROOT.parent / "main.py").exists() else TRIALS_ROOT
MAIN = ROOT / "main.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "boundary_shape_artifacts"
REPORT_ROOT = ROOT / "reports"


@dataclass(frozen=True)
class ValidationCase:
    slug: str
    prompt: str
    expected_answer: str
    expected_title: str
    expected_boundary_terms: tuple[str, ...]


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
    completed = subprocess.run(
        [sys.executable, str(MAIN), *args],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = completed.stdout.strip()
    return json.loads(stdout) if stdout else {}


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
        title_row = connection.execute(
            "SELECT title FROM bssc_artifacts WHERE artifact_id = ? LIMIT 1",
            (artifact_id,),
        ).fetchone()
        term_rows = connection.execute(
            """
            SELECT boundary_term
            FROM bssc_artifact_boundary_shape_terms
            WHERE artifact_id = ?
            ORDER BY term_index ASC
            """,
            (artifact_id,),
        ).fetchall()
    finally:
        connection.close()
    return {
        "title": title_row[0] if title_row else "",
        "boundary_terms": [row[0] for row in term_rows],
    }


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


def build_cases(greeting_path: Path) -> list[ValidationCase]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with building cases.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `build_cases(greeting_path=Path('/tmp/physics_force.md'))`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        greeting_path: Value for `greeting_path` used by `build_cases`. Expected type: `Path`.

    Returns:
        list[ValidationCase]: Result produced by `build_cases`.
    """
    return [
        ValidationCase(
            slug="output_only_hi",
            prompt="Say hi.",
            expected_answer="hi",
            expected_title="Hi Responder",
            expected_boundary_terms=("d*",),
        ),
        ValidationCase(
            slug="personalized_greeting",
            prompt="Say hi to name='Ada'.",
            expected_answer="hi, Ada",
            expected_title="Personalized Greeter",
            expected_boundary_terms=("a*", "d*"),
        ),
        ValidationCase(
            slug="file_read_greeting",
            prompt=f"Read the greeting from path='{greeting_path}'.",
            expected_answer="hi from file",
            expected_title="File Greeting Reader",
            expected_boundary_terms=("a'*", "b'*", "d*"),
        ),
        ValidationCase(
            slug="email_send_greeting",
            prompt="Send an email to recipient='alice@example.com' message='hi'.",
            expected_answer="simulated send to alice@example.com: hi",
            expected_title="Hi Email Sender",
            expected_boundary_terms=("a*", "c*"),
        ),
    ]


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
    parser = argparse.ArgumentParser(description="Run the boundary-shape prompt validation suite.")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        help="Optional explicit SQLite path. Defaults to reports/<timestamp>/boundary_shape_validation.sqlite3.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        help="Optional explicit report directory. Defaults to reports/boundary_shape_validation_<timestamp>.",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = args.report_dir or (REPORT_ROOT / f"boundary_shape_validation_{timestamp}")
    report_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = (args.sqlite_path or (report_dir / "boundary_shape_validation.sqlite3")).resolve()

    env = os.environ.copy()
    env["STATE_SQLITE_PATH"] = str(sqlite_path)
    for key in ("STATE_DB_URL", "STATE_DB_HOST", "STATE_DB_PORT", "STATE_DB_USER", "STATE_DB_PASSWORD", "STATE_DB_NAME"):
        env.pop(key, None)

    greeting_path = report_dir / "greeting.txt"
    greeting_path.write_text("hi from file\n")

    import_result = run_cli(
        [
            "artifact-import",
            "--artifact-dir",
            str(FIXTURE_DIR),
            "--normalized-out-dir",
            str(report_dir / "normalized"),
        ],
        env=env,
    )

    cases = build_cases(greeting_path)
    results: list[dict[str, Any]] = []
    failures: list[str] = []

    for case in cases:
        state_out = report_dir / f"{case.slug}.json"
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
        context = find_artifact_context(state_out)
        details = artifact_details(sqlite_path, str(context.get("artifact_id", "")))

        case_result = {
            "slug": case.slug,
            "prompt": case.prompt,
            "final_answer": run_result.get("final_answer", ""),
            "run_outcome": run_result.get("run_outcome", ""),
            "artifact_id": context.get("artifact_id", ""),
            "artifact_title": details["title"],
            "artifact_boundary_terms": details["boundary_terms"],
            "cross_boundary_execution": bool(context.get("cross_boundary_execution")),
            "state_path": str(state_out),
        }
        results.append(case_result)

        if run_result.get("run_outcome") != "completed":
            failures.append(f"{case.slug}: expected completed, got {run_result.get('run_outcome')!r}")
        if str(run_result.get("final_answer", "")).strip() != case.expected_answer:
            failures.append(
                f"{case.slug}: expected answer {case.expected_answer!r}, got {run_result.get('final_answer', '')!r}"
            )
        if details["title"] != case.expected_title:
            failures.append(f"{case.slug}: expected artifact {case.expected_title!r}, got {details['title']!r}")
        if tuple(details["boundary_terms"]) != case.expected_boundary_terms:
            failures.append(
                f"{case.slug}: expected boundary terms {case.expected_boundary_terms!r}, got {tuple(details['boundary_terms'])!r}"
            )
        if not context.get("cross_boundary_execution"):
            failures.append(f"{case.slug}: expected cross_boundary execution to be true")

    report = {
        "sqlite_path": str(sqlite_path),
        "fixture_dir": str(FIXTURE_DIR),
        "import_result": import_result,
        "cases": results,
        "status": "ok" if not failures else "failed",
        "failures": failures,
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
