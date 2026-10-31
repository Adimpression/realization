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

from realized_core_engine import open_sqlite_artifact_repository


ROOT = Path(__file__).resolve().parent
COMPATIBILITY_CLI = Path(sys.executable).with_name("realized-compatibility")
LOCAL_ENV = ROOT / "local.env"
REPORT_ROOT = ROOT / "reports"
MARKDOWN_FILE = ROOT / "LEARN_PHYSICS_MATH_RELATIONS.md"
if not MARKDOWN_FILE.exists():
    MARKDOWN_FILE = ROOT / "trials" / "LEARN_PHYSICS_MATH_RELATIONS.md"


def load_local_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with loading local environment variables from disk.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law.

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
        In circumstances like end-to-end semantic relation validation, helps with handling run cli.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law.

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
        [str(COMPATIBILITY_CLI), *args],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    stdout = completed.stdout.strip()
    return json.loads(stdout) if stdout else {}


def parse_number(text: str) -> float | None:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with parsing number.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law.

    Example Input Output:
        Input: `parse_number(text='Compute force from mass and acceleration.')`
        Output: 0.75

    Args:
        text: Value for `text` used by `parse_number`. Expected type: `str`.

    Returns:
        float | None: Result produced by `parse_number`.
    """
    match = re.search(r"-?\d+(?:\.\d+)?", str(text or ""))
    if not match:
        return None
    return float(match.group(0))


def semantic_contains(text: str, needle: str) -> bool:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with handling semantic contains.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_contains(text='Compute force from mass and acceleration.', needle='external force')`
        Output: True

    Args:
        text: Value for `text` used by `semantic_contains`. Expected type: `str`.
        needle: Value for `needle` used by `semantic_contains`. Expected type: `str`.

    Returns:
        bool: Result produced by `semantic_contains`.
    """
    return needle.casefold() in str(text or "").casefold()


def artifact_output_field(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with handling artifact output field.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_output_field(artifact=3)`
        Output: 'F = m * a'

    Args:
        artifact: Value for `artifact` used by `artifact_output_field`. Expected type: `Any`.

    Returns:
        str: Result produced by `artifact_output_field`.
    """
    content = artifact.content if isinstance(artifact.content, dict) else {}
    return str(content.get("output_field", "")).strip()


def artifact_title_current_identity(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with handling artifact title current identity.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `artifact_title_current_identity(artifact=3)`
        Output: 'Physics / Force / Force From Mass And Acceleration'

    Args:
        artifact: Value for `artifact` used by `artifact_title_current_identity`. Expected type: `Any`.

    Returns:
        str: Result produced by `artifact_title_current_identity`.
    """
    content = artifact.content if isinstance(artifact.content, dict) else {}
    return str(content.get("title_current_identity", "")).strip()


def is_ability_artifact(artifact: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with deciding whether ability artifact.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `is_ability_artifact(artifact=3)`
        Output: True

    Args:
        artifact: Value for `artifact` used by `is_ability_artifact`. Expected type: `Any`.

    Returns:
        bool: Result produced by `is_ability_artifact`.
    """
    return "ABILITY" in str(getattr(artifact, "artifact_type", "")).upper()


def find_artifact(
    artifacts: list[Any],
    *,
    output_field: str = "",
    contains: str = "",
    prefer_ability: bool = False,
) -> Any | None:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with finding artifact.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `find_artifact(artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], output_field='force', contains='external force', prefer_ability=True)`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifacts: Value for `artifacts` used by `find_artifact`. Expected type: `list[Any]`.
        output_field: Value for `output_field` used by `find_artifact`. Expected type: `str`. Defaults to `''`.
        contains: Value for `contains` used by `find_artifact`. Expected type: `str`. Defaults to `''`.
        prefer_ability: Value for `prefer_ability` used by `find_artifact`. Expected type: `bool`. Defaults to `False`.

    Returns:
        Any | None: Result produced by `find_artifact`.
    """
    candidates = artifacts
    if prefer_ability:
        preferred = [artifact for artifact in artifacts if is_ability_artifact(artifact)]
        if preferred:
            candidates = preferred
    for artifact in candidates:
        if output_field and artifact_output_field(artifact) == output_field:
            return artifact
        if contains and (
            semantic_contains(artifact.title, contains)
            or semantic_contains(artifact_title_current_identity(artifact), contains)
            or semantic_contains((artifact.content if isinstance(artifact.content, dict) else {}).get("question", ""), contains)
        ):
            return artifact
    return None


def find_artifacts(
    artifacts: list[Any],
    *,
    output_field: str = "",
    contains: str = "",
    prefer_ability: bool = False,
) -> list[Any]:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with finding artifacts.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `find_artifacts(artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], output_field='force', contains='external force', prefer_ability=True)`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        artifacts: Value for `artifacts` used by `find_artifacts`. Expected type: `list[Any]`.
        output_field: Value for `output_field` used by `find_artifacts`. Expected type: `str`. Defaults to `''`.
        contains: Value for `contains` used by `find_artifacts`. Expected type: `str`. Defaults to `''`.
        prefer_ability: Value for `prefer_ability` used by `find_artifacts`. Expected type: `bool`. Defaults to `False`.

    Returns:
        list[Any]: Result produced by `find_artifacts`.
    """
    candidates = artifacts
    if prefer_ability:
        preferred = [artifact for artifact in artifacts if is_ability_artifact(artifact)]
        if preferred:
            candidates = preferred
    matches: list[Any] = []
    for artifact in candidates:
        if output_field and artifact_output_field(artifact) == output_field:
            matches.append(artifact)
            continue
        if contains and (
            semantic_contains(artifact.title, contains)
            or semantic_contains(artifact_title_current_identity(artifact), contains)
            or semantic_contains((artifact.content if isinstance(artifact.content, dict) else {}).get("question", ""), contains)
        ):
            matches.append(artifact)
    return matches


@dataclass(frozen=True)
class PromptCase:
    slug: str
    prompt: str
    expected: float


def main() -> int:
    """
    High Level Purpose:
        In circumstances like end-to-end semantic relation validation, helps with handling main.

    Reference to Theory:
        Validates semantic relation formation, decomposition, and composition against the applied theory and title-depth law.

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
    report_dir = REPORT_ROOT / f"semantic_relation_validation_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = report_dir / "semantic_relation_validation.sqlite3"
    learn_report_path = report_dir / "learn_report.json"

    for key in ("STATE_DB_URL", "STATE_DB_HOST", "STATE_DB_PORT", "STATE_DB_USER", "STATE_DB_PASSWORD", "STATE_DB_NAME"):
        env.pop(key, None)
    env["STATE_SQLITE_PATH"] = str(sqlite_path)
    env["LLM_PROVIDER"] = env.get("LLM_PROVIDER", "openai")
    env["LLM_TIMEOUT_SECONDS"] = env.get("LLM_TIMEOUT_SECONDS", "180")

    learn_result = run_cli(
        [
            "markdown-learn",
            "--markdown-file",
            str(MARKDOWN_FILE),
            "--llm",
            "required",
            "--max-artifacts",
            "12",
            "--report-out",
            str(learn_report_path),
        ],
        env=env,
    )

    os.environ["STATE_SQLITE_PATH"] = str(sqlite_path)
    store = open_sqlite_artifact_repository()
    artifacts = store.load_recent_artifacts(limit=64)

    force = find_artifact(artifacts, contains="force", prefer_ability=True)
    if force is None:
        force = find_artifact(artifacts, output_field="F", prefer_ability=True)
    momentum = find_artifact(artifacts, contains="momentum", prefer_ability=True)
    if momentum is None:
        momentum = find_artifact(artifacts, output_field="p", prefer_ability=True)
    substrate = find_artifact(artifacts, contains="product", prefer_ability=True)
    substrate_candidates = find_artifacts(artifacts, output_field="P", prefer_ability=True)
    if substrate is None and substrate_candidates:
        downstream_related = set()
        if force is not None:
            downstream_related.update(force.related_artifact_ids)
        if momentum is not None:
            downstream_related.update(momentum.related_artifact_ids)
        substrate = next(
            (artifact for artifact in substrate_candidates if artifact.id in downstream_related),
            substrate_candidates[0],
        )

    failures: list[str] = []

    if substrate is None:
        failures.append("missing substrate artifact for multiplicative/product family")
    if force is None:
        failures.append("missing force artifact")
    if momentum is None:
        failures.append("missing momentum artifact")

    if substrate is not None:
        substrate_title = str(substrate.title)
        if semantic_contains(substrate_title, "reusable substrate"):
            failures.append(f"substrate title still looks organizational: {substrate_title!r}")
    if force is not None and not semantic_contains(force.title, "force"):
        failures.append(f"force title does not carry force identity: {force.title!r}")
    if momentum is not None and not semantic_contains(momentum.title, "momentum"):
        failures.append(f"momentum title does not carry momentum identity: {momentum.title!r}")

    if substrate is not None and force is not None and substrate.id not in force.related_artifact_ids:
        failures.append(
            f"force artifact does not point to substrate artifact: force={force.id!r}, substrate={substrate.id!r}, related={force.related_artifact_ids!r}"
        )
    if substrate is not None and momentum is not None and substrate.id not in momentum.related_artifact_ids:
        failures.append(
            f"momentum artifact does not point to substrate artifact: momentum={momentum.id!r}, substrate={substrate.id!r}, related={momentum.related_artifact_ids!r}"
        )

    prompt_cases = [
        PromptCase(
            slug="substrate_product",
            prompt="Calculate P from x=2 and y=6.",
            expected=12.0,
        ),
        PromptCase(
            slug="force_from_mass_acceleration",
            prompt="Calculate F from m=3 and a=4.",
            expected=12.0,
        ),
        PromptCase(
            slug="momentum_from_mass_velocity",
            prompt="Calculate p from m=5 and v=7.",
            expected=35.0,
        ),
    ]
    prompt_reports: list[dict[str, Any]] = []
    for case in prompt_cases:
        state_path = report_dir / f"{case.slug}_state.json"
        result = run_cli(
            [
                "run",
                "--prompt",
                case.prompt,
                "--llm",
                "off",
                "--max-steps",
                "24",
                "--state-out",
                str(state_path),
            ],
            env=env,
        )
        parsed = parse_number(str(result.get("final_answer", "")))
        if result.get("run_outcome") != "completed":
            failures.append(f"{case.slug}: expected completed, got {result.get('run_outcome')!r}")
        elif parsed is None or not math.isclose(parsed, case.expected, rel_tol=1e-9, abs_tol=1e-9):
            failures.append(f"{case.slug}: expected {case.expected!r}, got {result.get('final_answer')!r}")
        prompt_reports.append(
            {
                "slug": case.slug,
                "prompt": case.prompt,
                "expected": case.expected,
                "run_outcome": result.get("run_outcome", ""),
                "final_answer": result.get("final_answer", ""),
                "state_path": str(state_path),
            }
        )

    artifact_reports = []
    for artifact in artifacts:
        artifact_reports.append(
            {
                "artifact_id": artifact.id,
                "artifact_type": str(artifact.artifact_type),
                "title": artifact.title,
                "title_current_identity": artifact_title_current_identity(artifact),
                "output_field": artifact_output_field(artifact),
                "related_artifact_ids": list(artifact.related_artifact_ids),
                "question": str((artifact.content if isinstance(artifact.content, dict) else {}).get("question", "")).strip(),
            }
        )

    report = {
        "status": "ok" if not failures else "failed",
        "markdown_file": str(MARKDOWN_FILE),
        "sqlite_path": str(sqlite_path),
        "learn_result": learn_result,
        "artifacts": artifact_reports,
        "prompt_reports": prompt_reports,
        "failures": failures,
    }
    report_path = report_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
