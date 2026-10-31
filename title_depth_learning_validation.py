# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from realized_validation.sqlite_runtime import (
    archive_validation_sqlite,
    validation_sqlite_paths,
)


ROOT = Path(__file__).resolve().parent
COMPATIBILITY_CLI = Path(sys.executable).with_name("realized-compatibility")
LOCAL_ENV = ROOT / "local.env"
REPORT_ROOT = ROOT / "reports"
MARKDOWN_FILE = ROOT / "LEARN_CYLINDER_MEASURES.md"
if not MARKDOWN_FILE.exists():
    MARKDOWN_FILE = ROOT / "trials" / "LEARN_CYLINDER_MEASURES.md"


def load_local_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with loading local environment variables from disk.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

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


def run_cli(
    args: list[str],
    *,
    env: dict[str, str],
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with handling run cli.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `run_cli(args=['mass', 'acceleration', 'force'], env={'OPENAI_API_KEY': 'test-key'})`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        args: Value for `args` used by `run_cli`. Expected type: `list[str]`.
        env: Value for `env` used by `env`. Expected type: `dict[str, str]`.
        timeout_seconds: Value for `timeout_seconds` used by `run_cli`. Expected type: `int | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `run_cli`.
    """
    try:
        completed = subprocess.run(
            [str(COMPATIBILITY_CLI), *args],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "_status": "timeout",
            "args": list(args),
            "timeout_seconds": timeout_seconds,
            "stdout": (exc.stdout or "").strip(),
            "stderr": (exc.stderr or "").strip(),
        }
    except subprocess.CalledProcessError as exc:
        return {
            "_status": "error",
            "args": list(args),
            "returncode": int(exc.returncode),
            "stdout": (exc.stdout or "").strip(),
            "stderr": (exc.stderr or "").strip(),
        }
    stdout = completed.stdout.strip()
    return json.loads(stdout) if stdout else {}


def parse_number(text: str) -> float | None:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with parsing number.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `parse_number(text='Compute force from mass and acceleration.')`
        Output: 0.75

    Args:
        text: Value for `text` used by `parse_number`. Expected type: `str`.

    Returns:
        float | None: Result produced by `parse_number`.
    """
    raw = str(text or "").strip()
    if not raw:
        return None
    pi_match = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:\*?\s*)?(?:π|pi)\b", raw, flags=re.IGNORECASE)
    if pi_match:
        return float(pi_match.group(1)) * math.pi
    bare_pi_match = re.search(r"(?<![A-Za-z0-9_])(?:π|pi)\b", raw, flags=re.IGNORECASE)
    if bare_pi_match:
        return math.pi
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return None
    return float(match.group(0))


def load_state(path: Path) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with loading state.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `load_state(path=Path('/tmp/physics_force.md'))`
        Output: {'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}}

    Args:
        path: Value for `path` used by `load_state`. Expected type: `Path`.

    Returns:
        dict[str, Any]: Result produced by `load_state`.
    """
    return json.loads(path.read_text())


def root_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with handling root node.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `root_node(state={'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}})`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        state: Value for `state` used by `root_node`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `root_node`.
    """
    root_id = str(state.get("root_id", "")).strip()
    for node in state.get("graph", {}).get("nodes", []):
        if str(node.get("id", "")).strip() == root_id:
            return node
    raise AssertionError(f"Could not find root node {root_id!r} in saved state.")


def child_nodes(state: dict[str, Any], parent_id: str) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with handling child nodes.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `child_nodes(state={'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}}, parent_id='artifact-force')`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        state: Value for `state` used by `child_nodes`. Expected type: `dict[str, Any]`.
        parent_id: Value for `parent_id` used by `child_nodes`. Expected type: `str`.

    Returns:
        list[dict[str, Any]]: Result produced by `child_nodes`.
    """
    return [
        node
        for node in state.get("graph", {}).get("nodes", [])
        if str(node.get("parent_id", "")).strip() == parent_id
    ]


def title_prefixes_from_state(root: dict[str, Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with handling title prefixes from state.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `title_prefixes_from_state(root={'title': 'Physics / Force / Force From Mass And Acceleration'})`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        root: Value for `root` used by `title_prefixes_from_state`. Expected type: `dict[str, Any]`.

    Returns:
        list[str]: Result produced by `title_prefixes_from_state`.
    """
    structured = root.get("metadata", {}).get("structured_learning", {})
    prefixes = structured.get("title_depth_prefixes", [])
    return [str(item).strip() for item in prefixes if str(item).strip()] if isinstance(prefixes, list) else []


@dataclass(frozen=True)
class ValidationCase:
    slug: str
    prompt: str
    expected_numbers: tuple[float, ...]
    require_decomposition: bool


def validate_atomic_result(result: dict[str, Any], expected: float, failures: list[str], slug: str) -> None:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with validating atomic result.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `validate_atomic_result(result={'title': 'Physics / Force / Force From Mass And Acceleration'}, expected=3, failures=['mass', 'acceleration', 'force'], slug='force')`
        Output: None

    Args:
        result: Value for `result` used by `validate_atomic_result`. Expected type: `dict[str, Any]`.
        expected: Value for `expected` used by `validate_atomic_result`. Expected type: `float`.
        failures: Value for `failures` used by `validate_atomic_result`. Expected type: `list[str]`.
        slug: Value for `slug` used by `validate_atomic_result`. Expected type: `str`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    if result.get("run_outcome") != "completed":
        failures.append(f"{slug}: expected completed, got {result.get('run_outcome')!r}")
        return
    parsed = parse_number(str(result.get("final_answer", "")))
    if parsed is None or not math.isclose(parsed, expected, rel_tol=1e-9, abs_tol=1e-9):
        failures.append(f"{slug}: expected numeric answer near {expected!r}, got {result.get('final_answer')!r}")


def validate_compound_result(result: dict[str, Any], expected_numbers: tuple[float, ...], failures: list[str], slug: str) -> None:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with validating compound result.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `validate_compound_result(result={'title': 'Physics / Force / Force From Mass And Acceleration'}, expected_numbers=('Physics', 'Force'), failures=['mass', 'acceleration', 'force'], slug='force')`
        Output: None

    Args:
        result: Value for `result` used by `validate_compound_result`. Expected type: `dict[str, Any]`.
        expected_numbers: Value for `expected_numbers` used by `validate_compound_result`. Expected type: `tuple[float, ...]`.
        failures: Value for `failures` used by `validate_compound_result`. Expected type: `list[str]`.
        slug: Value for `slug` used by `validate_compound_result`. Expected type: `str`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    if result.get("run_outcome") != "completed":
        failures.append(f"{slug}: expected completed, got {result.get('run_outcome')!r}")
        return
    lowered = str(result.get("final_answer", "")).lower()
    for number in expected_numbers:
        formatted = f"{number:.6f}"
        if formatted[:6] not in lowered and str(round(number, 3)) not in lowered and str(round(number, 6)) not in lowered:
            failures.append(f"{slug}: expected compound answer to mention {number!r}, got {result.get('final_answer')!r}")


def main() -> int:
    """
    High Level Purpose:
        In circumstances like title-depth learning validation, helps with handling main.

    Reference to Theory:
        Validates title-depth learning, decomposition, and slash-structured identity formation against THEORY.md section 8.8.

    Example Input Output:
        Input: `main()`
        Output: 3

    Args:
        None.

    Returns:
        int: Result produced by `main`.
    """
    env = os.environ.copy()
    env.update(load_local_env())
    if not env.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured in the environment or local.env.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = REPORT_ROOT / f"title_depth_learning_validation_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    runtime_sqlite_path, sqlite_path = validation_sqlite_paths(
        report_dir=report_dir,
        basename="title_depth_learning.sqlite3",
    )
    learn_report_path = report_dir / "learn_report.json"
    bootstrap_report_path = report_dir / "report.json"
    bootstrap_report_path.write_text(
        json.dumps(
            {
                "status": "running",
                "stage": "learning",
                "markdown_file": str(MARKDOWN_FILE),
                "sqlite_path": str(sqlite_path),
                "sqlite_runtime_path": str(runtime_sqlite_path),
                "run_llm_policy": "off",
                "cases": [],
            },
            indent=2,
            sort_keys=True,
        )
    )

    for key in ("STATE_DB_URL", "STATE_DB_HOST", "STATE_DB_PORT", "STATE_DB_USER", "STATE_DB_PASSWORD", "STATE_DB_NAME"):
        env.pop(key, None)
    env["STATE_SQLITE_PATH"] = str(runtime_sqlite_path)
    env["LLM_PROVIDER"] = env.get("LLM_PROVIDER", "openai")
    env["LLM_TIMEOUT_SECONDS"] = env.get("LLM_TIMEOUT_SECONDS", "180")

    learn_timeout_seconds = int(env.get("TITLE_DEPTH_LEARN_TIMEOUT_SECONDS", "600"))
    run_timeout_seconds = int(env.get("TITLE_DEPTH_RUN_TIMEOUT_SECONDS", "300"))
    learn_llm_policy = str(env.get("TITLE_DEPTH_LEARN_LLM_POLICY", "required")).strip() or "required"
    run_llm_policy = str(env.get("TITLE_DEPTH_RUN_LLM_POLICY", "off")).strip() or "off"

    learn_result = run_cli(
        [
            "markdown-learn",
            "--markdown-file",
            str(MARKDOWN_FILE),
            "--llm",
            learn_llm_policy,
            "--max-artifacts",
            "10",
            "--report-out",
            str(learn_report_path),
        ],
        env=env,
        timeout_seconds=learn_timeout_seconds,
    )
    if learn_result.get("_status"):
        archived_sqlite_path = archive_validation_sqlite(runtime_sqlite_path, sqlite_path)
        report = {
            "status": "failed",
            "markdown_file": str(MARKDOWN_FILE),
            "sqlite_path": str(archived_sqlite_path),
            "sqlite_runtime_path": str(runtime_sqlite_path),
            "learn_result": learn_result,
            "cases": [],
            "failures": [
                f"markdown-learn did not complete ({learn_result.get('_status')})",
            ],
        }
        report_path = report_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    cases = [
        ValidationCase(
            slug="atomic_total_surface_area",
            prompt="Calculate the total surface area of a cylinder with radius=3 and height=5.",
            expected_numbers=(48 * math.pi,),
            require_decomposition=False,
        ),
        ValidationCase(
            slug="compound_surface_area_and_volume",
            prompt="Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results.",
            expected_numbers=(48 * math.pi, 45 * math.pi),
            require_decomposition=True,
        ),
    ]

    case_reports: list[dict[str, Any]] = []
    failures: list[str] = []

    for case in cases:
        state_path = report_dir / f"{case.slug}_state.json"
        run_result = run_cli(
            [
                "run",
                "--prompt",
                case.prompt,
                "--llm",
                run_llm_policy,
                "--max-steps",
                "24",
                "--state-out",
                str(state_path),
            ],
            env=env,
            timeout_seconds=run_timeout_seconds,
        )
        if run_result.get("_status"):
            failures.append(f"{case.slug}: run did not complete ({run_result.get('_status')})")
            case_reports.append(
                {
                    "slug": case.slug,
                    "prompt": case.prompt,
                    "run_outcome": run_result.get("_status", ""),
                    "final_answer": "",
                    "title_identity": "",
                    "title_depth_prefixes": [],
                    "title_depth_assessment": "",
                    "title_depth_minimal_sufficient_depth": "",
                    "child_semantic_units": [],
                    "child_title_depth_anchor_prefixes": [],
                    "state_path": str(state_path),
                    "process_result": run_result,
                }
            )
            continue
        state = load_state(state_path)
        root = root_node(state)
        root_metadata = root.get("metadata", {})
        structured = root_metadata.get("structured_learning", {})
        title_identity = str(structured.get("title_identity", "")).strip()
        prefixes = title_prefixes_from_state(root)
        children = child_nodes(state, str(root.get("id", "")).strip())

        if not title_identity:
            failures.append(f"{case.slug}: expected non-empty title_identity")
        allow_minimal_family_root = bool(
            case.require_decomposition
            and title_identity
            and "/" not in title_identity
            and prefixes == [title_identity]
        )
        if "/" not in title_identity and not allow_minimal_family_root:
            failures.append(f"{case.slug}: expected slash-bearing title_identity, got {title_identity!r}")
        if len(prefixes) < 2 and not allow_minimal_family_root:
            failures.append(f"{case.slug}: expected at least 2 title prefixes, got {prefixes!r}")
        if not prefixes or prefixes[-1] != title_identity:
            failures.append(f"{case.slug}: expected final title prefix to equal title_identity, got {prefixes!r} vs {title_identity!r}")

        if case.require_decomposition:
            if len(children) < 2:
                failures.append(f"{case.slug}: expected decomposition children, got {len(children)}")
            reserved = {item.casefold() for item in prefixes}
            for child in children:
                metadata = child.get("metadata", {})
                anchor_prefix = str(metadata.get("title_depth_anchor_prefix", "")).strip()
                namespace_rationale = str(metadata.get("namespace_rationale", "")).strip()
                child_semantic_unit = str(child.get("semantic_unit", "")).strip()
                if not anchor_prefix:
                    failures.append(f"{case.slug}: child {child_semantic_unit!r} missing title_depth_anchor_prefix")
                if not namespace_rationale:
                    failures.append(f"{case.slug}: child {child_semantic_unit!r} missing namespace_rationale")
                if child_semantic_unit.casefold() in reserved:
                    failures.append(f"{case.slug}: child {child_semantic_unit!r} restates a title prefix instead of distinct body-level work")

        if case.require_decomposition:
            validate_compound_result(run_result, case.expected_numbers, failures, case.slug)
        else:
            validate_atomic_result(run_result, case.expected_numbers[0], failures, case.slug)

        case_reports.append(
            {
                "slug": case.slug,
                "prompt": case.prompt,
                "run_outcome": run_result.get("run_outcome", ""),
                "final_answer": run_result.get("final_answer", ""),
                "title_identity": title_identity,
                "title_depth_prefixes": prefixes,
                "title_depth_assessment": structured.get("title_depth_assessment", ""),
                "title_depth_minimal_sufficient_depth": structured.get("title_depth_minimal_sufficient_depth", ""),
                "child_semantic_units": [str(child.get("semantic_unit", "")).strip() for child in children],
                "child_title_depth_anchor_prefixes": [
                    str(child.get("metadata", {}).get("title_depth_anchor_prefix", "")).strip()
                    for child in children
                ],
                "state_path": str(state_path),
            }
        )

    archived_sqlite_path = archive_validation_sqlite(runtime_sqlite_path, sqlite_path)
    report = {
        "status": "ok" if not failures else "failed",
        "markdown_file": str(MARKDOWN_FILE),
        "sqlite_path": str(archived_sqlite_path),
        "sqlite_runtime_path": str(runtime_sqlite_path),
        "learn_llm_policy": learn_llm_policy,
        "run_llm_policy": run_llm_policy,
        "learn_result": learn_result,
        "cases": case_reports,
        "failures": failures,
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
