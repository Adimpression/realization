# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

TRIALS_ROOT = Path(__file__).resolve().parent
ROOT = TRIALS_ROOT.parent if (TRIALS_ROOT.parent / "main.py").exists() else TRIALS_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from store import SQLiteVectorArtifactStore
from validation_sqlite import archive_validation_sqlite, validation_sqlite_paths

MAIN = ROOT / "main.py"
LOCAL_ENV = ROOT / "local.env"
REPORT_ROOT = ROOT / "reports"


def resolve_trial_markdown_path(name: str) -> Path:
    """
    High Level Purpose:
        In circumstances like cumulative relation validation after markdown files have moved between the repo root and the trials folder, helps with resolving the active curriculum path.

    Reference to Theory:
        Ensures the probability/information ladder is evaluated against the intended source documents so relation formation can be assessed correctly.

    Example Input Output:
        Input: `resolve_trial_markdown_path(name='01_LEARN_PROBABILITY_RELATIONS_FOUNDATIONS.md')`
        Output: Path('/Users/ravindranathakila/service/realized/trials/01_LEARN_PROBABILITY_RELATIONS_FOUNDATIONS.md')

    Args:
        name: Value for `name` used by `resolve_trial_markdown_path`. Expected type: `str`.

    Returns:
        Path: Result produced by `resolve_trial_markdown_path`.
    """
    trial_path = TRIALS_ROOT / name
    if trial_path.exists():
        return trial_path
    return ROOT / name


@dataclass(frozen=True)
class RelationGroup:
    label: str
    needles: tuple[str, ...]


@dataclass(frozen=True)
class CurriculumCase:
    order: int
    markdown_file: Path
    substrate_needles: tuple[str, ...]
    determinate_needles: tuple[str, ...]
    prior_relation_groups: tuple[RelationGroup, ...] = ()


CASES: tuple[CurriculumCase, ...] = (
    CurriculumCase(
        order=1,
        markdown_file=resolve_trial_markdown_path("01_LEARN_PROBABILITY_RELATIONS_FOUNDATIONS.md"),
        substrate_needles=("additive combination",),
        determinate_needles=("event count", "disjoint parts"),
    ),
    CurriculumCase(
        order=2,
        markdown_file=resolve_trial_markdown_path("02_LEARN_PROBABILITY_RELATIONS_RATIO.md"),
        substrate_needles=("ratio formation",),
        determinate_needles=("probability from favorable count", "probability"),
        prior_relation_groups=(
            RelationGroup("depends on additive combination", ("additive combination",)),
        ),
    ),
    CurriculumCase(
        order=3,
        markdown_file=resolve_trial_markdown_path("03_LEARN_PROBABILITY_RELATIONS_COMPLEMENT.md"),
        substrate_needles=("complement subtraction",),
        determinate_needles=("complement probability",),
        prior_relation_groups=(
            RelationGroup("depends on ratio formation", ("ratio formation",)),
        ),
    ),
    CurriculumCase(
        order=4,
        markdown_file=resolve_trial_markdown_path("04_LEARN_PROBABILITY_RELATIONS_CONDITIONAL.md"),
        substrate_needles=("conditional restriction",),
        determinate_needles=("conditional probability",),
        prior_relation_groups=(
            RelationGroup("depends on ratio formation", ("ratio formation",)),
        ),
    ),
    CurriculumCase(
        order=5,
        markdown_file=resolve_trial_markdown_path("05_LEARN_PROBABILITY_RELATIONS_BAYES.md"),
        substrate_needles=("inverse conditional update",),
        determinate_needles=("bayes",),
        prior_relation_groups=(
            RelationGroup("depends on conditional restriction", ("conditional restriction", "conditional probability")),
            RelationGroup("depends on ratio formation", ("ratio formation",)),
        ),
    ),
    CurriculumCase(
        order=6,
        markdown_file=resolve_trial_markdown_path("06_LEARN_PROBABILITY_RELATIONS_EXPECTATION.md"),
        substrate_needles=("weighted aggregation",),
        determinate_needles=("expected value",),
    ),
    CurriculumCase(
        order=7,
        markdown_file=resolve_trial_markdown_path("07_LEARN_PROBABILITY_RELATIONS_VARIANCE.md"),
        substrate_needles=("transformed deviation aggregation",),
        determinate_needles=("variance",),
        prior_relation_groups=(
            RelationGroup("depends on expectation", ("expected value", "expectation", "weighted aggregation")),
        ),
    ),
    CurriculumCase(
        order=8,
        markdown_file=resolve_trial_markdown_path("08_LEARN_PROBABILITY_RELATIONS_COVARIANCE.md"),
        substrate_needles=("co-deviation aggregation",),
        determinate_needles=("covariance",),
        prior_relation_groups=(
            RelationGroup("depends on expectation", ("expected value", "expectation", "weighted aggregation")),
        ),
    ),
    CurriculumCase(
        order=9,
        markdown_file=resolve_trial_markdown_path("09_LEARN_INFORMATION_RELATIONS_ENTROPY.md"),
        substrate_needles=("transformed probability expectation",),
        determinate_needles=("entropy",),
        prior_relation_groups=(
            RelationGroup("depends on weighted aggregation family", ("weighted aggregation", "expected value", "expectation")),
        ),
    ),
    CurriculumCase(
        order=10,
        markdown_file=resolve_trial_markdown_path("10_LEARN_INFORMATION_RELATIONS_KL_DIVERGENCE.md"),
        substrate_needles=("weighted relative transform",),
        determinate_needles=("kl divergence", "relative information mismatch"),
        prior_relation_groups=(
            RelationGroup("depends on ratio formation", ("ratio formation",)),
            RelationGroup("depends on weighted aggregation family", ("weighted aggregation", "expected value", "expectation", "entropy")),
        ),
    ),
)


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


def semantic_contains(text: str, needle: str) -> bool:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling semantic contains.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `semantic_contains(text='Compute force from mass and acceleration.', needle='external force')`
        Output: True

    Args:
        text: Value for `text` used by `semantic_contains`. Expected type: `str`.
        needle: Value for `needle` used by `semantic_contains`. Expected type: `str`.

    Returns:
        bool: Result produced by `semantic_contains`.
    """
    def _normalized(value: str) -> str:
        return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in str(value or "")).split())

    needle_text = str(needle or "")
    haystack_text = str(text or "")
    if needle_text.casefold() in haystack_text.casefold():
        return True
    normalized_needle = _normalized(needle_text)
    normalized_haystack = _normalized(haystack_text)
    return bool(normalized_needle) and normalized_needle in normalized_haystack


def ordered_unique(items: Iterable[str]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling ordered unique.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end.

    Example Input Output:
        Input: `ordered_unique(items=['mass', 'acceleration', 'force'])`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        items: Value for `items` used by `ordered_unique`. Expected type: `Iterable[str]`.

    Returns:
        list[str]: Result produced by `ordered_unique`.
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def artifact_source_document(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact source document.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_source_document(artifact=3)`
        Output: 'F = m * a'

    Args:
        artifact: Value for `artifact` used by `artifact_source_document`. Expected type: `Any`.

    Returns:
        str: Result produced by `artifact_source_document`.
    """
    content = artifact.content if isinstance(artifact.content, dict) else {}
    return str(content.get("source_document", "")).strip()


def artifact_output_field(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact output field.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

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
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact title current identity.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

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


def artifact_question(artifact: Any) -> str:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact question.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_question(artifact=3)`
        Output: 'F = m * a'

    Args:
        artifact: Value for `artifact` used by `artifact_question`. Expected type: `Any`.

    Returns:
        str: Result produced by `artifact_question`.
    """
    content = artifact.content if isinstance(artifact.content, dict) else {}
    return str(content.get("question", "")).strip()


def is_ability_artifact(artifact: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with deciding whether ability artifact.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `is_ability_artifact(artifact=3)`
        Output: True

    Args:
        artifact: Value for `artifact` used by `is_ability_artifact`. Expected type: `Any`.

    Returns:
        bool: Result produced by `is_ability_artifact`.
    """
    return "ABILITY" in str(getattr(artifact, "artifact_type", "")).upper()


def is_generic_executor_wrapper_artifact(artifact: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with excluding generic executor-wrapper artifacts from semantic-pair selection when a more semantic sibling is available.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `is_generic_executor_wrapper_artifact(artifact=3)`
        Output: True

    Args:
        artifact: Value for `artifact` used by `is_generic_executor_wrapper_artifact`. Expected type: `Any`.

    Returns:
        bool: Result produced by `is_generic_executor_wrapper_artifact`.
    """
    title = str(getattr(artifact, "title", "") or "").casefold()
    current_identity = artifact_title_current_identity(artifact).casefold()
    question = artifact_question(artifact).casefold()
    generic_markers = (
        "python ability",
        "bash ability",
        "ansible ability",
        "wasm ability",
    )
    return any(marker in title or marker in current_identity or marker in question for marker in generic_markers)


def artifact_identity_surfaces(artifact: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact identity surfaces.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_identity_surfaces(artifact=3)`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        artifact: Value for `artifact` used by `artifact_identity_surfaces`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `artifact_identity_surfaces`.
    """
    content = artifact.content if isinstance(artifact.content, dict) else {}
    aliases = content.get("aliases", []) if isinstance(content.get("aliases", []), list) else []
    title_similies = content.get("title_similies", []) if isinstance(content.get("title_similies", []), list) else []
    surfaces = [
        str(getattr(artifact, "title", "")).strip(),
        artifact_title_current_identity(artifact),
        artifact_question(artifact),
        str(content.get("semantic_unit", "")).strip(),
        *[str(item).strip() for item in aliases if str(item).strip()],
        *[str(item).strip() for item in title_similies if str(item).strip()],
    ]
    return ordered_unique(surface for surface in surfaces if surface)


def artifact_matches_any(artifact: Any, needles: Iterable[str]) -> bool:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling artifact matches any.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_matches_any(artifact=3, needles=['mass', 'acceleration', 'force'])`
        Output: True

    Args:
        artifact: Value for `artifact` used by `artifact_matches_any`. Expected type: `Any`.
        needles: Value for `needles` used by `artifact_matches_any`. Expected type: `Iterable[str]`.

    Returns:
        bool: Result produced by `artifact_matches_any`.
    """
    surfaces = artifact_identity_surfaces(artifact)
    for needle in needles:
        if any(semantic_contains(surface, needle) for surface in surfaces):
            return True
    return False


def find_artifacts(
    artifacts: list[Any],
    *,
    needles: Iterable[str],
    prefer_ability: bool = False,
) -> list[Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with finding artifacts.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `find_artifacts(artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], needles=['mass', 'acceleration', 'force'], prefer_ability=True)`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        artifacts: Value for `artifacts` used by `find_artifacts`. Expected type: `list[Any]`.
        needles: Value for `needles` used by `find_artifacts`. Expected type: `Iterable[str]`.
        prefer_ability: Value for `prefer_ability` used by `find_artifacts`. Expected type: `bool`. Defaults to `False`.

    Returns:
        list[Any]: Result produced by `find_artifacts`.
    """
    candidates = artifacts
    if prefer_ability:
        preferred = [
            artifact
            for artifact in artifacts
            if is_ability_artifact(artifact) and not is_generic_executor_wrapper_artifact(artifact)
        ]
        if not preferred:
            preferred = [artifact for artifact in artifacts if is_ability_artifact(artifact)]
        if preferred:
            candidates = preferred
    return [artifact for artifact in candidates if artifact_matches_any(artifact, needles)]


def choose_relation_pair(
    current_doc_artifacts: list[Any],
    *,
    substrate_needles: tuple[str, ...],
    determinate_needles: tuple[str, ...],
) -> tuple[Any | None, Any | None]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling choose relation pair.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `choose_relation_pair(current_doc_artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}], substrate_needles=('Physics', 'Force'), determinate_needles=('Physics', 'Force'))`
        Output: ('Physics', 'Force')

    Args:
        current_doc_artifacts: Value for `current_doc_artifacts` used by `choose_relation_pair`. Expected type: `list[Any]`.
        substrate_needles: Value for `substrate_needles` used by `choose_relation_pair`. Expected type: `tuple[str, ...]`.
        determinate_needles: Value for `determinate_needles` used by `choose_relation_pair`. Expected type: `tuple[str, ...]`.

    Returns:
        tuple[Any | None, Any | None]: Result produced by `choose_relation_pair`.
    """
    substrate_candidates = find_artifacts(current_doc_artifacts, needles=substrate_needles, prefer_ability=False)
    determinate_candidates = find_artifacts(current_doc_artifacts, needles=determinate_needles, prefer_ability=False)
    current_doc_by_id = {
        str(getattr(artifact, "id", "")).strip(): artifact
        for artifact in current_doc_artifacts
        if str(getattr(artifact, "id", "")).strip()
    }
    linked_substrate_candidates: list[Any] = []
    linked_seen: set[str] = set()
    for determinate in determinate_candidates:
        for artifact_id in getattr(determinate, "related_artifact_ids", []):
            if artifact_id not in current_doc_by_id or artifact_id in linked_seen:
                continue
            linked_seen.add(artifact_id)
            linked_substrate_candidates.append(current_doc_by_id[artifact_id])
    if linked_substrate_candidates:
        substrate_candidates = linked_substrate_candidates + [
            artifact
            for artifact in substrate_candidates
            if str(getattr(artifact, "id", "")).strip() not in linked_seen
        ]
    if not substrate_candidates or not determinate_candidates:
        return (
            substrate_candidates[0] if substrate_candidates else None,
            determinate_candidates[0] if determinate_candidates else None,
        )
    best_score = -1
    best_pair = (substrate_candidates[0], determinate_candidates[0])
    for substrate in substrate_candidates:
        for determinate in determinate_candidates:
            score = 0
            if substrate.id == determinate.id:
                score -= 200
            if substrate.id in determinate.related_artifact_ids:
                score += 200
            if determinate.id in substrate.related_artifact_ids:
                score += 40
            if not is_ability_artifact(substrate):
                score += 8
            if is_ability_artifact(determinate):
                score += 6
            if not artifact_output_field(substrate):
                score += 4
            if artifact_output_field(determinate):
                score += 4
            if artifact_matches_any(determinate, determinate_needles):
                score += 8
            if artifact_matches_any(substrate, substrate_needles):
                score += 8
            if artifact_matches_any(substrate, determinate_needles) and artifact_output_field(substrate):
                score -= 8
            if title_looks_organizational(substrate.title):
                score -= 6
            if title_looks_organizational(determinate.title):
                score -= 6
            if semantic_contains(substrate.title, "reusing earlier lessons"):
                score -= 10
            if semantic_contains(determinate.title, "reusing earlier lessons"):
                score -= 8
            if is_generic_executor_wrapper_artifact(substrate):
                score -= 12
            if is_generic_executor_wrapper_artifact(determinate):
                score -= 12
            if score > best_score:
                best_score = score
                best_pair = (substrate, determinate)
    return best_pair


def artifact_summary(artifact: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with summarizing artifact.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_summary(artifact=3)`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_summary`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `artifact_summary`.
    """
    return {
        "artifact_id": artifact.id,
        "artifact_type": str(artifact.artifact_type),
        "title": artifact.title,
        "title_current_identity": artifact_title_current_identity(artifact),
        "output_field": artifact_output_field(artifact),
        "question": artifact_question(artifact),
        "source_document": artifact_source_document(artifact),
        "related_artifact_ids": list(artifact.related_artifact_ids),
    }


def title_looks_organizational(title: str) -> bool:
    """
    High Level Purpose:
        In circumstances like trial-driven end-to-end checks over decomposition, reuse, and composition, helps with handling title looks organizational.

    Reference to Theory:
        Exercises the real controller/validation flow against trial corpora so the applied title-depth, decomposition, reuse, and composition rules can be assessed end to end. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `title_looks_organizational(title='Physics / Force / Force From Mass And Acceleration')`
        Output: True

    Args:
        title: Value for `title` used by `title_looks_organizational`. Expected type: `str`.

    Returns:
        bool: Result produced by `title_looks_organizational`.
    """
    lowered = str(title or "").casefold()
    return any(
        needle in lowered
        for needle in (
            "reusable substrate",
            "one-sentence summary",
            "one sentence summary",
            "distinguishing the relation",
            "named quantities",
            "notes",
            "example",
        )
    )


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
    env = os.environ.copy()
    env.update(load_local_env())
    if not env.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not configured in the environment or local.env.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = REPORT_ROOT / f"probability_information_relation_validation_{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    runtime_sqlite_path, sqlite_path = validation_sqlite_paths(
        report_dir=report_dir,
        basename="probability_information_relation_validation.sqlite3",
    )
    report_path = report_dir / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "status": "running",
                "stage": "learning",
                "sqlite_path": str(sqlite_path),
                "sqlite_runtime_path": str(runtime_sqlite_path),
                "case_reports": [],
                "failures": [],
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

    os.environ["STATE_SQLITE_PATH"] = str(runtime_sqlite_path)
    store = SQLiteVectorArtifactStore()

    all_failures: list[str] = []
    case_reports: list[dict[str, Any]] = []

    for case in CASES:
        learn_report_path = report_dir / f"{case.order:02d}_{case.markdown_file.stem}_learn_report.json"
        learn_result = run_cli(
            [
                "markdown-learn",
                "--markdown-file",
                str(case.markdown_file),
                "--llm",
                "required",
                "--max-artifacts",
                "12",
                "--report-out",
                str(learn_report_path),
            ],
            env=env,
        )

        artifacts = store.load_recent_artifacts(limit=512)
        artifacts_by_id = {artifact.id: artifact for artifact in artifacts}
        current_doc_artifacts = [
            artifact
            for artifact in artifacts
            if artifact_source_document(artifact) == case.markdown_file.name
        ]
        substrate, determinate = choose_relation_pair(
            current_doc_artifacts,
            substrate_needles=case.substrate_needles,
            determinate_needles=case.determinate_needles,
        )

        failures: list[str] = []
        if learn_result.get("run_outcome") != "completed":
            failures.append(f"learn outcome was {learn_result.get('run_outcome')!r}")
        if not current_doc_artifacts:
            failures.append("no artifacts were persisted for the current document")
        if substrate is None:
            failures.append(
                f"missing substrate artifact for needles {case.substrate_needles!r}"
            )
        if determinate is None:
            failures.append(
                f"missing determinate artifact for needles {case.determinate_needles!r}"
            )

        internal_relation_ok = False
        if substrate is not None and determinate is not None:
            internal_relation_ok = substrate.id in determinate.related_artifact_ids
            if not internal_relation_ok:
                failures.append(
                    f"determinate artifact does not point to current substrate: determinate={determinate.title!r}, substrate={substrate.title!r}, related={determinate.related_artifact_ids!r}"
                )
            if title_looks_organizational(substrate.title):
                failures.append(f"substrate title still looks organizational: {substrate.title!r}")
            if title_looks_organizational(determinate.title):
                failures.append(f"determinate title still looks organizational: {determinate.title!r}")

        relation_carriers = [artifact for artifact in (substrate, determinate) if artifact is not None]
        prior_group_reports: list[dict[str, Any]] = []
        for group in case.prior_relation_groups:
            matched_related: list[Any] = []
            for carrier in relation_carriers:
                for artifact_id in carrier.related_artifact_ids:
                    related = artifacts_by_id.get(artifact_id)
                    if related is None:
                        continue
                    if artifact_source_document(related) == case.markdown_file.name:
                        continue
                    if artifact_matches_any(related, group.needles):
                        matched_related.append(related)
            matched_related = ordered_unique([artifact.id for artifact in matched_related])
            matched_artifacts = [artifacts_by_id[artifact_id] for artifact_id in matched_related if artifact_id in artifacts_by_id]
            if not matched_artifacts:
                failures.append(
                    f"missing prior relation group {group.label!r} from carriers {[artifact.title for artifact in relation_carriers]!r}"
                )
            prior_group_reports.append(
                {
                    "label": group.label,
                    "needles": list(group.needles),
                    "matched": [artifact_summary(artifact) for artifact in matched_artifacts],
                    "ok": bool(matched_artifacts),
                }
            )

        case_report = {
            "order": case.order,
            "markdown_file": str(case.markdown_file),
            "learn_result": learn_result,
            "learn_report_path": str(learn_report_path),
            "artifact_count_total": len(artifacts),
            "artifact_count_current_document": len(current_doc_artifacts),
            "substrate": artifact_summary(substrate) if substrate is not None else None,
            "determinate": artifact_summary(determinate) if determinate is not None else None,
            "internal_relation_ok": internal_relation_ok,
            "prior_relation_groups": prior_group_reports,
            "current_document_artifacts": [artifact_summary(artifact) for artifact in current_doc_artifacts],
            "failures": failures,
        }
        case_reports.append(case_report)
        all_failures.extend(
            f"{case.order:02d} {case.markdown_file.name}: {failure}"
            for failure in failures
        )

    archived_sqlite_path = archive_validation_sqlite(runtime_sqlite_path, sqlite_path)
    report = {
        "status": "ok" if not all_failures else "failed",
        "sqlite_path": str(archived_sqlite_path),
        "sqlite_runtime_path": str(runtime_sqlite_path),
        "case_reports": case_reports,
        "failures": all_failures,
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not all_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
