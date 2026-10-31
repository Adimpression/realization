# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_validation.sqlite_runtime import (
    archive_validation_sqlite,
    validation_sqlite_paths,
)

REPO_ROOT = Path(__file__).resolve().parent
TRIALS_ROOT = REPO_ROOT / "trials"
REPORTS_ROOT = REPO_ROOT / "reports"
LOCAL_ENV = REPO_ROOT / "local.env"
DEFAULT_PROBE_TIMEOUT_SECONDS = 60


def write_running_report(report_root: Path, *, started_at: str) -> None:
    """
    High Level Purpose:
        In circumstances like long-running domain learning sweeps, helps with writing an initial observable report before domain learning starts.

    Reference to Theory:
        Supports disciplined validation observability for cross-domain semantic reuse and composition checks without changing the trial semantics themselves.

    Example Input Output:
        Input: `write_running_report(report_root=Path('/tmp/report'), started_at='2026-04-07T21:00:00Z')`
        Output: None

    Args:
        report_root: Value for `report_root` used by `write_running_report`. Expected type: `Path`.
        started_at: Value for `started_at` used by `write_running_report`. Expected type: `str`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    report = {
        "started_at": started_at,
        "finished_at": "",
        "status": "running",
        "stage": "learning",
        "report_root": str(report_root),
        "domains": [],
    }
    (report_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
DEFAULT_PROBE_TIMEOUT_MAX_SECONDS = 180


def _elapsed_seconds(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)


def _json_stdout(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


@dataclass(frozen=True)
class ProbeSpec:
    """
    High Level Purpose:
        In circumstances like validating a learned domain corpus after markdown learning, helps with defining one offline reuse probe together with the success condition that should hold for its final answer.

    Reference to Theory:
        Supports applied validation of semantic reuse, decomposition, and composition by checking whether previously learned artifacts can resolve later prompts without fresh LLM intervention.

    Example Input Output:
        Input: `ProbeSpec(name='ideal_gas_pressure', prompt='Calculate P from n=2 and R=0.5 and T=3 and V=1.', expected_mode='numeric', expected_value=3.0, expected_substrings=())`
        Output: `ProbeSpec(name='ideal_gas_pressure', prompt='Calculate P from n=2 and R=0.5 and T=3 and V=1.', expected_mode='numeric', expected_value=3.0, expected_substrings=())`

    Args:
        name: Value for `name` used by `ProbeSpec`. Expected type: `str`.
        prompt: Value for `prompt` used by `ProbeSpec`. Expected type: `str`.
        expected_mode: Value for `expected_mode` used by `ProbeSpec`. Expected type: `str`.
        expected_value: Value for `expected_value` used by `ProbeSpec`. Expected type: `float | None`.
        expected_substrings: Value for `expected_substrings` used by `ProbeSpec`. Expected type: `tuple[str, ...]`.

    Returns:
        ProbeSpec: Dataclass instance representing one validation probe.
    """

    name: str
    prompt: str
    expected_mode: str
    expected_value: float | None = None
    expected_substrings: tuple[str, ...] = ()


STOPWORD_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "do",
    "does",
    "each",
    "explain",
    "for",
    "form",
    "from",
    "full",
    "general",
    "give",
    "how",
    "identify",
    "in",
    "is",
    "it",
    "its",
    "main",
    "of",
    "on",
    "one",
    "out",
    "provide",
    "relation",
    "role",
    "state",
    "structure",
    "terms",
    "that",
    "the",
    "their",
    "them",
    "this",
    "through",
    "to",
    "use",
    "using",
    "what",
    "why",
    "with",
    "write",
}


def slugify_prompt(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like converting human-written prompt bullets into stable report filenames, helps with collapsing one prompt surface into a short deterministic identifier.

    Reference to Theory:
        None.

    Example Input Output:
        Input: `slugify_prompt(text='What is gene expression?')`
        Output: 'what_is_gene_expression'

    Args:
        text: Value for `text` used by `slugify_prompt`. Expected type: `str`.

    Returns:
        str: Result produced by `slugify_prompt`.
    """

    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    if not tokens:
        return "prompt"
    return "_".join(tokens[:8]).strip("_") or "prompt"


def parse_prompts_markdown(path: Path) -> tuple[ProbeSpec, ...]:
    """
    High Level Purpose:
        In circumstances like keeping trial prompts in one editable markdown file per domain, helps with turning `PROMPTS.md` bullet lines into executable validation probes.

    Reference to Theory:
        Supports practical validation of semantic reuse and composition by letting domain prompt corpora live alongside the domain lessons they exercise.

    Example Input Output:
        Input: `parse_prompts_markdown(path=Path('/workspace/realized/trials/biology/PROMPTS.md'))`
        Output: (ProbeSpec(name='what_is_gene_expression', prompt='What is gene expression?', expected_mode='freeform', expected_value=None, expected_substrings=()),)

    Args:
        path: Value for `path` used by `parse_prompts_markdown`. Expected type: `Path`.

    Returns:
        tuple[ProbeSpec, ...]: Result produced by `parse_prompts_markdown`.
    """

    probes: list[ProbeSpec] = []
    if not path.exists():
        return ()
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        prompt = line[2:].strip()
        if not prompt:
            continue
        probes.append(
            ProbeSpec(
                name=slugify_prompt(prompt),
                prompt=prompt,
                expected_mode="freeform",
            )
        )
    return tuple(probes)


def freeform_probe_signal_tokens(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like evaluating whether a freeform answer is at least about the asked scientific prompt, helps with extracting the higher-information prompt terms that should plausibly reappear in the response.

    Reference to Theory:
        Supports practical validation of reuse and composition by checking that a closed answer still stays semantically tied to the asked unit instead of drifting into generic residue.

    Example Input Output:
        Input: `freeform_probe_signal_tokens(text='Explain how genotype, regulation, and environment together determine phenotype.')`
        Output: ['genotype', 'regulation', 'environment', 'determine', 'phenotype']

    Args:
        text: Value for `text` used by `freeform_probe_signal_tokens`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `freeform_probe_signal_tokens`.
    """

    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", str(text).lower())
        if len(token) >= 3 and token not in STOPWORD_TOKENS
    ]
    return tokens


def freeform_probe_passed(state_payload: dict[str, Any], probe: ProbeSpec) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like validating open-ended domain prompts without exact gold text, helps with applying bounded answer-quality checks so the harness can still reject obviously empty, generic, or drifted answers.

    Reference to Theory:
        Supports practical validation of semantic reuse and composition by requiring that a freeform answer both closes and remains anchored to the asked semantic focus.

    Example Input Output:
        Input: `freeform_probe_passed(state_payload={'run_outcome': 'completed', 'final_answer': 'Gene expression is the process by which information in DNA contributes to functional products.'}, probe=ProbeSpec(name='what_is_gene_expression', prompt='What is gene expression?', expected_mode='freeform'))`
        Output: (True, 'freeform_overlap:3')

    Args:
        state_payload: Value for `state_payload` used by `freeform_probe_passed`. Expected type: `dict[str, Any]`.
        probe: Value for `probe` used by `freeform_probe_passed`. Expected type: `ProbeSpec`.

    Returns:
        tuple[bool, str]: Result produced by `freeform_probe_passed`.
    """

    if str(state_payload.get("run_outcome", "")).strip() != "completed":
        return (False, "run_incomplete")
    answer = str(state_payload.get("final_answer", "")).strip()
    if not answer:
        return (False, "missing_final_answer")
    lowered = answer.lower()
    if "committed_state supports reduction" in lowered:
        return (False, "generic_placeholder_answer")
    if len(answer) < 32:
        return (False, "answer_too_short")
    prompt_tokens = freeform_probe_signal_tokens(probe.prompt)
    answer_tokens = set(freeform_probe_signal_tokens(answer))
    overlap = [token for token in prompt_tokens if token in answer_tokens]
    required_overlap = 1 if len(prompt_tokens) <= 3 else 2
    if len(overlap) < required_overlap:
        return (False, "freeform_low_overlap:" + ",".join(prompt_tokens[:6]))
    return (True, f"freeform_overlap:{len(overlap)}")


@dataclass(frozen=True)
class DomainSpec:
    """
    High Level Purpose:
        In circumstances like running a full-folder trial over one scientific domain, helps with bundling the markdown lesson folder and representative reuse probes into a single reusable execution plan.

    Reference to Theory:
        Supports validation of domain-level semantic reuse by keeping together the learning corpus, probe prompts, and expected reuse behavior for one semantic neighborhood.

    Example Input Output:
        Input: `DomainSpec(name='chemistry', folder=Path('/workspace/realized/trials/chemistry'), probes=(ProbeSpec(name='ideal_gas_pressure', prompt='Calculate P from n=2 and R=0.5 and T=3 and V=1.', expected_mode='numeric', expected_value=3.0),))`
        Output: `DomainSpec(name='chemistry', folder=Path('/workspace/realized/trials/chemistry'), probes=(ProbeSpec(name='ideal_gas_pressure', prompt='Calculate P from n=2 and R=0.5 and T=3 and V=1.', expected_mode='numeric', expected_value=3.0),))`

    Args:
        name: Value for `name` used by `DomainSpec`. Expected type: `str`.
        folder: Value for `folder` used by `DomainSpec`. Expected type: `Path`.
        probes: Value for `probes` used by `DomainSpec`. Expected type: `tuple[ProbeSpec, ...]`.

    Returns:
        DomainSpec: Dataclass instance representing one domain trial plan.
    """

    name: str
    folder: Path
    probes: tuple[ProbeSpec, ...]


def _int_env(name: str, default: int) -> int:
    """
    High Level Purpose:
        In circumstances like configuring bounded trial harness budgets from environment variables, helps with reading one integer-valued environment setting while preserving a safe default when the environment is empty or malformed.

    Reference to Theory:
        Supports practical validation by letting trial execution budgets vary without changing the trial semantics or the probe specification surface.

    Example Input Output:
        Input: `_int_env(name='TRIAL_PROBE_TIMEOUT_SECONDS', default=60)`
        Output: 60

    Args:
        name: Value for `name` used by `_int_env`. Expected type: `str`.
        default: Value for `default` used by `_int_env`. Expected type: `int`.

    Returns:
        int: Result produced by `_int_env`.
    """
    raw_value = str(os.getenv(name, str(default))).strip()
    try:
        return int(raw_value or str(default))
    except ValueError:
        return int(default)


def probe_timeout_seconds_for(probe: ProbeSpec, *, default_seconds: int) -> int:
    """
    High Level Purpose:
        In circumstances like running one domain probe sweep with both short direct prompts and long derivational freeform prompts, helps with assigning a bounded timeout budget that scales with prompt complexity rather than forcing every probe through one brittle global cap.

    Reference to Theory:
        Supports practical validation of reuse and composition by letting longer reconstruction or derivation prompts complete under the same harness instead of being misclassified as failures solely because their requested explanation surface is larger.

    Example Input Output:
        Input: `probe_timeout_seconds_for(probe=ProbeSpec(name='derive_mass', prompt='Given the relation for molar mass, express how to compute mass from moles and molar mass, and explain how this relates to the reusable substrate.', expected_mode='freeform'), default_seconds=60)`
        Output: 150

    Args:
        probe: Value for `probe` used by `probe_timeout_seconds_for`. Expected type: `ProbeSpec`.
        default_seconds: Value for `default_seconds` used by `probe_timeout_seconds_for`. Expected type: `int`.

    Returns:
        int: Result produced by `probe_timeout_seconds_for`.
    """
    timeout_seconds = int(default_seconds)
    if str(probe.expected_mode).strip().lower() != "freeform":
        return timeout_seconds

    lowered_prompt = str(probe.prompt or "").strip().lower()
    prompt_tokens = re.findall(r"[a-z0-9_]+", lowered_prompt)
    prompt_length = len(lowered_prompt)

    if len(prompt_tokens) >= 16:
        timeout_seconds += min(30, (len(prompt_tokens) - 15) * 2)
    if prompt_length >= 120:
        timeout_seconds += min(30, max(0, (prompt_length - 120) // 6))
    if any(
        marker in lowered_prompt
        for marker in (
            "derive",
            "reconstruct",
            "full chain",
            "full reasoning path",
            "starting from",
            "given the relation",
            "given the formula",
            "using the relation",
            "using the formula",
            "composes multiple earlier semantic substrates",
            "reusable substrate",
        )
    ):
        timeout_seconds += 75
    if any(
        marker in lowered_prompt
        for marker in (
            "write the formula",
            "state the formula",
            "identify the role of each variable",
            "identify the role of each term",
            "what the inputs and outputs represent",
        )
    ):
        timeout_seconds += 30

    max_seconds = _int_env("TRIAL_PROBE_TIMEOUT_MAX_SECONDS", DEFAULT_PROBE_TIMEOUT_MAX_SECONDS)
    return max(timeout_seconds, int(default_seconds)) if timeout_seconds <= max_seconds else max_seconds


def resolve_domain_skill_bundle(folder: Path) -> Path | None:
    """
    High Level Purpose:
        In circumstances like rerunning domain trials under the current governed import/export posture, helps with locating a domain-level `skill.yaml` bundle that can seed a fresh DB without repeating markdown learning.

    Reference to Theory:
        Keeps domain validation aligned with the current governance posture by preferring installed governed skills when the corpus has already been exported that way, while still allowing an explicit markdown-learning fallback when needed.

    Example Input Output:
        Input: `resolve_domain_skill_bundle(folder=Path('/workspace/realized/trials/chemistry'))`
        Output: Path('/workspace/realized/trials/chemistry/skill.yaml')

    Args:
        folder: Value for `folder` used by `resolve_domain_skill_bundle`. Expected type: `Path`.

    Returns:
        Path | None: Result produced by `resolve_domain_skill_bundle`.
    """

    candidate = folder / "skill.yaml"
    if not candidate.exists():
        return None
    use_bundle = str(os.getenv("TRIAL_DOMAIN_VALIDATION_USE_BUNDLE", "")).strip().lower()
    if use_bundle in {"0", "false", "no", "off"}:
        return None
    if use_bundle in {"", "1", "true", "yes", "on"}:
        return candidate
    return None


def iso_now() -> str:
    """
    High Level Purpose:
        In circumstances like naming report directories and stamping domain validation outputs, helps with producing one UTC timestamp string that is stable enough for filenames and reports.

    Reference to Theory:
        None.

    Example Input Output:
        Input: `iso_now()`
        Output: '2026-03-29T02:15:30+00:00'

    Args:
        None.

    Returns:
        str: Result produced by `iso_now`.
    """

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_local_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like running domain validation from a clean shell, helps with loading API keys and related local configuration from `local.env` so the harness behaves like the other trial scripts.

    Reference to Theory:
        Supports reproducible domain validation by keeping the learning-time environment explicit instead of depending on ambient shell state.

    Example Input Output:
        Input: `load_local_env()`
        Output: {'OPENAI_API_KEY': 'test-key'}

    Args:
        None.

    Returns:
        dict[str, str]: Result produced by `load_local_env`.
    """

    values: dict[str, str] = {}
    if not LOCAL_ENV.exists():
        return values
    for raw_line in LOCAL_ENV.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key_text = key.strip()
        if not key_text:
            continue
        values[key_text] = raw_value.strip().strip('"').strip("'")
    return values


def base_env() -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like running OpenAI-backed markdown learning and offline probe reuse in a reproducible trial harness, helps with constructing the shared environment variables required by every subprocess.

    Reference to Theory:
        Supports practical validation of learning, reuse, and composition by keeping representation and query-priming settings stable across the whole run.

    Example Input Output:
        Input: `base_env()`
        Output: {'BSSC_TITLE_REPRESENTATION': 'prolog', 'BSSC_PROLOG_QUERY_PRIMING': 'fallback'}

    Args:
        None.

    Returns:
        dict[str, str]: Result produced by `base_env`.
    """

    env = dict(os.environ)
    env.update(load_local_env())
    env["BSSC_TITLE_REPRESENTATION"] = "prolog"
    env["BSSC_PROLOG_QUERY_PRIMING"] = "fallback"
    env["TRIAL_LEARN_TIMEOUT_SECONDS"] = env.get("TRIAL_LEARN_TIMEOUT_SECONDS", "300")
    env["STATE_VECTOR_MODE"] = env.get("STATE_VECTOR_MODE", "off")
    return env


def run_command(
    *,
    cmd: list[str],
    env: dict[str, str],
    cwd: Path,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    High Level Purpose:
        In circumstances like learning a markdown lesson or probing an already learned domain DB, helps with executing one child command and capturing stdout and stderr for later report writing.

    Reference to Theory:
        None.

    Example Input Output:
        Input: `run_command(cmd=['realized-compatibility', 'run', '--prompt', 'Calculate F from m=3 and a=4.', '--llm', 'off'], env={'BSSC_TITLE_REPRESENTATION': 'prolog'}, cwd=Path('/workspace/realized'), timeout_seconds=120)`
        Output: `CompletedProcess(args=['realized-compatibility', 'run', '--prompt', 'Calculate F from m=3 and a=4.', '--llm', 'off'], returncode=0, stdout='...', stderr='')`

    Args:
        cmd: Value for `cmd` used by `run_command`. Expected type: `list[str]`.
        env: Value for `env` used by `run_command`. Expected type: `dict[str, str]`.
        cwd: Value for `cwd` used by `run_command`. Expected type: `Path`.
        timeout_seconds: Value for `timeout_seconds` used by `run_command`. Expected type: `int | None`. Defaults to `None`.

    Returns:
        subprocess.CompletedProcess[str]: Result produced by `run_command`.
    """

    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )


def learn_retry_count() -> int:
    """
    High Level Purpose:
        In circumstances like provider-backed markdown learning during domain validation, helps with deciding how many retry attempts are allowed after the first failed learn attempt.

    Reference to Theory:
        Supports validation stability without changing the underlying controller semantics being validated.

    Example Input Output:
        Input: `learn_retry_count()`
        Output: 4

    Args:
        None.

    Returns:
        int: Result produced by `learn_retry_count`.
    """
    raw = str(os.getenv("TRIAL_LEARN_RETRIES", "4")).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 4


def learn_retry_delay_seconds_for_attempt(attempt_index: int) -> int:
    """
    High Level Purpose:
        In circumstances like repeated transient provider failures during long markdown learning, helps with inserting a short bounded backoff before the next retry so immediate reconnect churn does not consume the full retry budget too aggressively.

    Reference to Theory:
        Supports validator stability by treating provider transport instability as harness noise rather than semantic failure.

    Example Input Output:
        Input: `learn_retry_delay_seconds_for_attempt(attempt_index=2)`
        Output: 6

    Args:
        attempt_index: Value for `attempt_index` used by `learn_retry_delay_seconds_for_attempt`. Expected type: `int`.

    Returns:
        int: Result produced by `learn_retry_delay_seconds_for_attempt`.
    """
    if attempt_index <= 0:
        return 0
    return min(15, int(attempt_index) * 3)


def probe_retry_count() -> int:
    """
    High Level Purpose:
        In circumstances like long freeform probe execution during domain validation, helps with deciding how many retry attempts are allowed after the first timed-out probe attempt.

    Reference to Theory:
        Supports validation stability without changing the underlying controller semantics being validated.

    Example Input Output:
        Input: `probe_retry_count()`
        Output: 1

    Args:
        None.

    Returns:
        int: Result produced by `probe_retry_count`.
    """
    raw = str(os.getenv("TRIAL_PROBE_RETRIES", "1")).strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 1


def learn_timeout_seconds_for_attempt(base_seconds: int, attempt_index: int) -> int:
    """
    High Level Purpose:
        In circumstances like retrying a long-running markdown learn after a timeout or transient provider failure, helps with increasing the timeout budget on later attempts.

    Reference to Theory:
        Supports validator stability by distinguishing long-running learning work from true theory/runtime failure.

    Example Input Output:
        Input: `learn_timeout_seconds_for_attempt(base_seconds=300, attempt_index=1)`
        Output: 600

    Args:
        base_seconds: Value for `base_seconds` used by `learn_timeout_seconds_for_attempt`. Expected type: `int`.
        attempt_index: Value for `attempt_index` used by `learn_timeout_seconds_for_attempt`. Expected type: `int`.

    Returns:
        int: Result produced by `learn_timeout_seconds_for_attempt`.
    """
    if attempt_index <= 0:
        return max(1, int(base_seconds))
    return max(1, int(base_seconds) * (attempt_index + 1))


def probe_timeout_seconds_for_attempt(base_seconds: int, attempt_index: int) -> int:
    """
    High Level Purpose:
        In circumstances like retrying timed-out validation probes, helps with increasing the timeout budget on later attempts without flattening all probes into one large default timeout.

    Reference to Theory:
        Supports validation stability by distinguishing long-running probe execution from a true semantic failure.

    Example Input Output:
        Input: `probe_timeout_seconds_for_attempt(base_seconds=60, attempt_index=1)`
        Output: 120

    Args:
        base_seconds: Value for `base_seconds` used by `probe_timeout_seconds_for_attempt`. Expected type: `int`.
        attempt_index: Value for `attempt_index` used by `probe_timeout_seconds_for_attempt`. Expected type: `int`.

    Returns:
        int: Result produced by `probe_timeout_seconds_for_attempt`.
    """
    if attempt_index <= 0:
        return max(1, int(base_seconds))
    return max(1, int(base_seconds) * (attempt_index + 1))


def is_transient_markdown_learn_failure(*, stdout_tail: str, stderr_tail: str) -> bool:
    """
    High Level Purpose:
        In circumstances like deciding whether a failed markdown learn should be retried, helps with detecting known transient provider and transport failures rather than treating them as stable controller regressions.

    Reference to Theory:
        Supports the validation doctrine rule that harness/provider instability must be separated from theory/runtime failure.

    Example Input Output:
        Input: `is_transient_markdown_learn_failure(stdout_tail='', stderr_tail='openai.InternalServerError: upstream connect error')`
        Output: True

    Args:
        stdout_tail: Value for `stdout_tail` used by `is_transient_markdown_learn_failure`. Expected type: `str`.
        stderr_tail: Value for `stderr_tail` used by `is_transient_markdown_learn_failure`. Expected type: `str`.

    Returns:
        bool: Result produced by `is_transient_markdown_learn_failure`.
    """
    combined = f"{stdout_tail}\n{stderr_tail}".lower()
    transient_markers = (
        "internalservererror",
        "upstream connect error",
        "connection termination",
        "connection reset",
        "apiconnectionerror",
        "rate limit",
        "temporarily unavailable",
        "server_error",
        "could not parse the json body of your request",
    )
    return any(marker in combined for marker in transient_markers)


def run_probe_with_retries(
    *,
    probe: ProbeSpec,
    state_path: Path,
    env: dict[str, str],
    timeout_seconds: int,
    runner=run_command,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like running one offline reuse probe after domain learning, helps with retrying timed-out probe attempts with a larger timeout budget while preserving attempt history in the result.

    Reference to Theory:
        Supports validation stability by separating harness timeout pressure from actual semantic reuse failure.

    Example Input Output:
        Input: `run_probe_with_retries(probe=ProbeSpec(name='force', prompt='Calculate F from m=3 and a=4.', expected_mode='numeric', expected_value=12.0), state_path=Path('/tmp/probe.json'), env={}, timeout_seconds=60)`
        Output: {'name': 'force', 'returncode': 0, 'attempt_count': 1}

    Args:
        probe: Value for `probe` used by `run_probe_with_retries`. Expected type: `ProbeSpec`.
        state_path: Value for `state_path` used by `run_probe_with_retries`. Expected type: `Path`.
        env: Value for `env` used by `run_probe_with_retries`. Expected type: `dict[str, str]`.
        timeout_seconds: Value for `timeout_seconds` used by `run_probe_with_retries`. Expected type: `int`.
        runner: Value for `runner` used by `run_probe_with_retries`. Expected type: `Any`. Defaults to `run_command`.

    Returns:
        dict[str, Any]: Result produced by `run_probe_with_retries`.
    """
    attempts: list[dict[str, Any]] = []
    for attempt_index in range(probe_retry_count() + 1):
        effective_timeout_seconds = probe_timeout_seconds_for_attempt(timeout_seconds, attempt_index)
        try:
            probe_started = time.perf_counter()
            completed = runner(
                cmd=[
                    str(Path(sys.executable).with_name("realized-compatibility")),
                    "run",
                    "--prompt",
                    probe.prompt,
                    "--llm",
                    "off",
                    "--state-out",
                    str(state_path),
                ],
                env=env,
                cwd=REPO_ROOT,
                timeout_seconds=effective_timeout_seconds,
            )
            probe_elapsed_seconds = _elapsed_seconds(probe_started)
        except subprocess.TimeoutExpired as exc:
            attempt = {
                "attempt": attempt_index + 1,
                "timeout_seconds": effective_timeout_seconds,
                "returncode": -1,
                "stdout_tail": str(exc.stdout or "")[-2000:],
                "stderr_tail": str(exc.stderr or "")[-2000:],
                "elapsed_seconds": effective_timeout_seconds,
                "timed_out": True,
            }
            attempts.append(attempt)
            if attempt_index < probe_retry_count():
                continue
            return {
                "name": probe.name,
                "prompt": probe.prompt,
                "returncode": -1,
                "stdout_tail": attempt["stdout_tail"],
                "stderr_tail": attempt["stderr_tail"],
                "state": str(state_path),
                "resumed": False,
                "passed": False,
                "reason": "timeout",
                "run_outcome": "timeout",
                "final_answer": "",
                "elapsed_seconds": effective_timeout_seconds,
                "timeout_seconds": effective_timeout_seconds,
                "attempt_count": len(attempts),
                "attempts": attempts,
            }

        attempt = {
            "attempt": attempt_index + 1,
            "timeout_seconds": effective_timeout_seconds,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
            "elapsed_seconds": probe_elapsed_seconds,
            "timed_out": False,
            "command_timings": _json_stdout(completed.stdout).get("timings", {}),
        }
        attempts.append(attempt)
        return {
            "name": probe.name,
            "prompt": probe.prompt,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
            "state": str(state_path),
            "resumed": False,
            "elapsed_seconds": probe_elapsed_seconds,
            "timeout_seconds": effective_timeout_seconds,
            "command_timings": attempt["command_timings"],
            "attempt_count": len(attempts),
            "attempts": attempts,
        }
    raise AssertionError("probe retry loop terminated unexpectedly")


def run_markdown_learn_with_retries(
    *,
    markdown_path: Path,
    report_path: Path,
    state_path: Path,
    env: dict[str, str],
    timeout_seconds: int,
    runner=run_command,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like domain validation over long provider-backed learning lessons, helps with retrying markdown-learn after a timeout or transient provider failure while preserving one compact report entry.

    Reference to Theory:
        Supports validation stability by keeping learn-stage transport/provider noise separate from actual semantic/controller regressions.

    Example Input Output:
        Input: `run_markdown_learn_with_retries(markdown_path=Path('/tmp/lesson.md'), report_path=Path('/tmp/report.json'), state_path=Path('/tmp/state.json'), env={}, timeout_seconds=300)`
        Output: {'file': '/tmp/lesson.md', 'returncode': 0, 'attempt_count': 2}

    Args:
        markdown_path: Value for `markdown_path` used by `run_markdown_learn_with_retries`. Expected type: `Path`.
        report_path: Value for `report_path` used by `run_markdown_learn_with_retries`. Expected type: `Path`.
        state_path: Value for `state_path` used by `run_markdown_learn_with_retries`. Expected type: `Path`.
        env: Value for `env` used by `run_markdown_learn_with_retries`. Expected type: `dict[str, str]`.
        timeout_seconds: Value for `timeout_seconds` used by `run_markdown_learn_with_retries`. Expected type: `int`.
        runner: Value for `runner` used by `run_markdown_learn_with_retries`. Expected type: `Any`. Defaults to `run_command`.

    Returns:
        dict[str, Any]: Result produced by `run_markdown_learn_with_retries`.
    """
    attempts: list[dict[str, Any]] = []
    markdown_learn_llm_policy = str(env.get("TRIAL_MARKDOWN_LEARN_LLM_POLICY", "required")).strip() or "required"
    for attempt_index in range(learn_retry_count() + 1):
        effective_timeout_seconds = learn_timeout_seconds_for_attempt(timeout_seconds, attempt_index)
        try:
            learn_started = time.perf_counter()
            completed = runner(
                cmd=[
                    str(Path(sys.executable).with_name("realized-compatibility")),
                    "markdown-learn",
                    "--markdown-file",
                    str(markdown_path),
                    "--llm",
                    markdown_learn_llm_policy,
                    "--report-out",
                    str(report_path),
                    "--state-out",
                    str(state_path),
                ],
                env=env,
                cwd=REPO_ROOT,
                timeout_seconds=effective_timeout_seconds,
            )
            learn_elapsed_seconds = _elapsed_seconds(learn_started)
        except subprocess.TimeoutExpired as exc:
            attempt = {
                "attempt": attempt_index + 1,
                "timeout_seconds": effective_timeout_seconds,
                "returncode": -1,
                "stdout_tail": str(exc.stdout or "")[-2000:],
                "stderr_tail": str(exc.stderr or "")[-2000:],
                "elapsed_seconds": effective_timeout_seconds,
                "timed_out": True,
            }
            attempts.append(attempt)
            if attempt_index < learn_retry_count():
                continue
            return {
                "file": str(markdown_path),
                "returncode": -1,
                "stdout_tail": attempt["stdout_tail"],
                "stderr_tail": attempt["stderr_tail"],
                "report": str(report_path),
                "state": str(state_path),
                "resumed": False,
                "learn_mode": "markdown_learn",
                "elapsed_seconds": effective_timeout_seconds,
                "attempt_count": len(attempts),
                "attempts": attempts,
            }

        attempt = {
            "attempt": attempt_index + 1,
            "timeout_seconds": effective_timeout_seconds,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
            "elapsed_seconds": learn_elapsed_seconds,
            "timed_out": False,
            "command_timings": _json_stdout(completed.stdout).get("timings", {}),
        }
        attempts.append(attempt)
        if completed.returncode == 0:
            return {
                "file": str(markdown_path),
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
                "report": str(report_path),
                "state": str(state_path),
                "resumed": False,
                "learn_mode": "markdown_learn",
                "elapsed_seconds": learn_elapsed_seconds,
                "command_timings": attempt["command_timings"],
                "attempt_count": len(attempts),
                "attempts": attempts,
            }
        if attempt_index < learn_retry_count() and is_transient_markdown_learn_failure(
            stdout_tail=attempt["stdout_tail"],
            stderr_tail=attempt["stderr_tail"],
        ):
            delay_seconds = learn_retry_delay_seconds_for_attempt(attempt_index + 1)
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            continue
        return {
            "file": str(markdown_path),
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
            "report": str(report_path),
            "state": str(state_path),
            "resumed": False,
            "learn_mode": "markdown_learn",
            "elapsed_seconds": learn_elapsed_seconds,
            "command_timings": attempt["command_timings"],
            "attempt_count": len(attempts),
            "attempts": attempts,
        }
    raise AssertionError("markdown-learn retry loop terminated unexpectedly")


def sqlite_metrics(sqlite_path: Path) -> dict[str, int]:
    """
    High Level Purpose:
        In circumstances like assessing whether a learned domain corpus actually persisted reusable structure, helps with reading a few stable SQLite counts that summarize artifacts, abilities, relations, and stored Prolog heads.

    Reference to Theory:
        Supports validation of semantic reuse and decomposition by measuring how much reusable residue and relation structure survived persistence.

    Example Input Output:
        Input: `sqlite_metrics(sqlite_path=Path('/workspace/realized/reports/sample/domain.sqlite3'))`
        Output: {'artifacts': 57, 'abilities': 20, 'knowledge': 37, 'related_items': 48, 'prolog_heads': 57}

    Args:
        sqlite_path: Value for `sqlite_path` used by `sqlite_metrics`. Expected type: `Path`.

    Returns:
        dict[str, int]: Result produced by `sqlite_metrics`.
    """

    counts = {
        "artifacts": 0,
        "abilities": 0,
        "knowledge": 0,
        "related_items": 0,
        "prolog_heads": 0,
    }
    if not sqlite_path.exists():
        return counts
    conn = sqlite3.connect(str(sqlite_path))
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('bssc_artifact', 'bssc_artifacts') ORDER BY name DESC LIMIT 1")
        row = cur.fetchone()
        artifact_table = str(row[0]) if row else ""
        if artifact_table:
            cur.execute(f"SELECT COUNT(*) FROM {artifact_table}")
            counts["artifacts"] = int(cur.fetchone()[0] or 0)
            cur.execute(f"SELECT COUNT(*) FROM {artifact_table} WHERE artifact_type = 'ability'")
            counts["abilities"] = int(cur.fetchone()[0] or 0)
            cur.execute(f"SELECT COUNT(*) FROM {artifact_table} WHERE artifact_type = 'knowledge'")
            counts["knowledge"] = int(cur.fetchone()[0] or 0)
        cur.execute("SELECT COUNT(*) FROM bssc_artifact_related_items")
        counts["related_items"] = int(cur.fetchone()[0] or 0)
        cur.execute(
            """
            SELECT COUNT(*)
            FROM bssc_artifact_detail
            WHERE COALESCE(extra_content_yaml, '') LIKE '%title_prolog_head:%'
            """
        )
        counts["prolog_heads"] = int(cur.fetchone()[0] or 0)
    except sqlite3.OperationalError:
        return counts
    finally:
        conn.close()
    return counts


def probe_passed(state_payload: dict[str, Any], probe: ProbeSpec) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like checking whether one offline prompt was resolved correctly from a learned corpus, helps with applying either a numeric expectation or a keyword expectation to the saved run state.

    Reference to Theory:
        Supports validation of semantic reuse and composition by testing whether learned artifacts can answer later prompts without fresh LLM intervention.

    Example Input Output:
        Input: `probe_passed(state_payload={'run_outcome': 'completed', 'final_answer': '3'}, probe=ProbeSpec(name='ideal_gas_pressure', prompt='Calculate P from n=2 and R=0.5 and T=3 and V=1.', expected_mode='numeric', expected_value=3.0))`
        Output: (True, 'numeric_match')

    Args:
        state_payload: Value for `state_payload` used by `probe_passed`. Expected type: `dict[str, Any]`.
        probe: Value for `probe` used by `probe_passed`. Expected type: `ProbeSpec`.

    Returns:
        tuple[bool, str]: Result produced by `probe_passed`.
    """

    if probe.expected_mode == "freeform":
        return freeform_probe_passed(state_payload, probe)
    if str(state_payload.get("run_outcome", "")).strip() != "completed":
        return (False, "run_incomplete")
    answer = str(state_payload.get("final_answer", "")).strip()
    if not answer:
        return (False, "missing_final_answer")
    if probe.expected_mode == "numeric":
        try:
            numeric_answer = float(answer)
        except ValueError:
            return (False, "not_numeric")
        if probe.expected_value is None:
            return (True, "numeric_present")
        if abs(numeric_answer - probe.expected_value) <= 1e-9:
            return (True, "numeric_match")
        return (False, f"numeric_mismatch:{numeric_answer}")
    normalized = answer.lower()
    missing = [token for token in probe.expected_substrings if token.lower() not in normalized]
    if missing:
        return (False, "missing_substrings:" + ",".join(missing))
    return (True, "substring_match")


def run_domain(spec: DomainSpec, *, report_root: Path, env: dict[str, str]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like trialing a whole scientific domain folder after controller changes, helps with learning the folder into one SQLite DB, probing representative offline prompts, and collecting a compact domain report.

    Reference to Theory:
        Supports applied validation of title-depth, semantic reuse, and composition by checking whether one coherent domain corpus can both persist reusable structure and answer later prompts from that structure.

    Example Input Output:
        Input: `run_domain(spec=DomainSpec(name='physics', folder=Path('/workspace/realized/trials/physics'), probes=(ProbeSpec(name='force', prompt='Calculate F from m=3 and a=4.', expected_mode='numeric', expected_value=12.0),)), report_root=Path('/workspace/realized/reports/demo'), env={'BSSC_TITLE_REPRESENTATION': 'prolog'})`
        Output: {'domain': 'physics', 'status': 'ok', 'learned_files': 10, 'probe_summary': {'passed': 1, 'total': 1}}

    Args:
        spec: Value for `spec` used by `run_domain`. Expected type: `DomainSpec`.
        report_root: Value for `report_root` used by `run_domain`. Expected type: `Path`.
        env: Value for `env` used by `run_domain`. Expected type: `dict[str, str]`.

    Returns:
        dict[str, Any]: Result produced by `run_domain`.
    """

    domain_dir = report_root / spec.name
    domain_dir.mkdir(parents=True, exist_ok=True)
    runtime_sqlite_path, sqlite_path = validation_sqlite_paths(
        report_dir=domain_dir,
        basename=f"{spec.name}.sqlite3",
    )
    domain_env = dict(env)
    domain_env["STATE_SQLITE_PATH"] = str(runtime_sqlite_path)
    probe_timeout_seconds = _int_env("TRIAL_PROBE_TIMEOUT_SECONDS", DEFAULT_PROBE_TIMEOUT_SECONDS)
    learn_timeout_seconds = int(str(domain_env.get("TRIAL_LEARN_TIMEOUT_SECONDS", "300")).strip() or "300")

    def _finalize(result: dict[str, Any]) -> dict[str, Any]:
        archived = archive_validation_sqlite(runtime_sqlite_path, sqlite_path)
        result["sqlite"] = str(archived)
        result["sqlite_runtime"] = str(runtime_sqlite_path)
        result["metrics"] = sqlite_metrics(archived if archived.exists() else runtime_sqlite_path)
        return result

    learn_results: list[dict[str, Any]] = []
    markdown_files = [
        path
        for path in sorted(spec.folder.glob("*.md"))
        if path.name != "PROMPTS.md"
    ]
    bundle_path = resolve_domain_skill_bundle(spec.folder)
    if bundle_path is not None:
        try:
            import_started = time.perf_counter()
            completed = run_command(
                cmd=[
                    str(Path(sys.executable).with_name("realized-compatibility")),
                    "import-skill",
                    "--skill-file",
                    str(bundle_path),
                ],
                env=domain_env,
                cwd=REPO_ROOT,
                timeout_seconds=learn_timeout_seconds,
            )
            import_elapsed_seconds = _elapsed_seconds(import_started)
        except subprocess.TimeoutExpired as exc:
            learn_results.append(
                {
                    "file": str(bundle_path),
                    "returncode": -1,
                    "stdout_tail": str(exc.stdout or "")[-2000:],
                    "stderr_tail": str(exc.stderr or "")[-2000:],
                    "report": "",
                    "state": "",
                    "resumed": False,
                    "learn_mode": "import_skill_bundle",
                    "elapsed_seconds": learn_timeout_seconds,
                }
            )
            return _finalize({
                "domain": spec.name,
                "status": "failed",
                "stage": "learn",
                "failed_file": str(bundle_path),
                "learn_results": learn_results,
            })
        learn_results.append(
            {
                "file": str(bundle_path),
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
                "report": "",
                "state": "",
                "resumed": False,
                "learn_mode": "import_skill_bundle",
                "elapsed_seconds": import_elapsed_seconds,
                "command_timings": _json_stdout(completed.stdout).get("timings", {}),
            }
        )
        if completed.returncode != 0:
            return _finalize({
                "domain": spec.name,
                "status": "failed",
                "stage": "learn",
                "failed_file": str(bundle_path),
                "learn_results": learn_results,
            })
    else:
        for markdown_path in markdown_files:
            report_path = domain_dir / f"{markdown_path.stem}_learn_report.json"
            state_path = domain_dir / f"{markdown_path.stem}_learn_state.json"
            if report_path.exists() and state_path.exists():
                learn_results.append(
                    {
                        "file": str(markdown_path),
                        "returncode": 0,
                        "stdout_tail": "",
                        "stderr_tail": "",
                        "report": str(report_path),
                        "state": str(state_path),
                        "resumed": True,
                        "learn_mode": "markdown_learn",
                    }
                )
                continue
            learn_result = run_markdown_learn_with_retries(
                markdown_path=markdown_path,
                report_path=report_path,
                state_path=state_path,
                env=domain_env,
                timeout_seconds=learn_timeout_seconds,
            )
            learn_results.append(learn_result)
            if learn_result["returncode"] != 0:
                return _finalize({
                    "domain": spec.name,
                    "status": "failed",
                    "stage": "learn",
                    "failed_file": str(markdown_path),
                    "learn_results": learn_results,
                })

    probe_results: list[dict[str, Any]] = []
    for probe in spec.probes:
        probe_budget_seconds = probe_timeout_seconds_for(
            probe,
            default_seconds=probe_timeout_seconds,
        )
        state_path = domain_dir / f"probe_{probe.name}.json"
        if state_path.exists():
            result: dict[str, Any] = {
                "name": probe.name,
                "prompt": probe.prompt,
                "returncode": 0,
                "stdout_tail": "",
                "stderr_tail": "",
                "state": str(state_path),
                "resumed": True,
            }
        else:
            result = run_probe_with_retries(
                probe=probe,
                state_path=state_path,
                env=domain_env,
                timeout_seconds=probe_budget_seconds,
            )
        if result["returncode"] == 0 and state_path.exists():
            payload = json.loads(state_path.read_text())
            passed, reason = probe_passed(payload, probe)
            result.update(
                {
                    "run_outcome": payload.get("run_outcome", ""),
                    "final_answer": payload.get("final_answer", ""),
                    "passed": passed,
                    "reason": reason,
                }
            )
        else:
            result.update({"passed": False, "reason": "run_failed"})
        probe_results.append(result)

    passed = sum(1 for item in probe_results if item.get("passed"))
    total = len(probe_results)
    status = "ok" if total and passed == total else "failed"
    return _finalize({
        "domain": spec.name,
        "status": status,
        "learn_mode": "import_skill_bundle" if bundle_path is not None else "markdown_learn",
        "bundle_file": str(bundle_path) if bundle_path is not None else "",
        "learned_files": len(markdown_files),
        "learn_results": learn_results,
        "probe_results": probe_results,
        "probe_summary": {"passed": passed, "total": total},
    })


def domain_specs() -> tuple[DomainSpec, ...]:
    """
    High Level Purpose:
        In circumstances like validating several trial folders with one generic harness, helps with defining the concrete domain folders and representative prompts that exercise decomposition, reuse, and composition in each domain.

    Reference to Theory:
        Supports cross-domain validation of semantic reuse by keeping the probe design explicit and stable across chemistry, biology, and physics.

    Example Input Output:
        Input: `domain_specs()`
        Output: (DomainSpec(name='chemistry', folder=Path('/workspace/realized/trials/chemistry'), probes=(...)), DomainSpec(name='biology', folder=Path('/workspace/realized/trials/biology'), probes=(...)), DomainSpec(name='physics', folder=Path('/workspace/realized/trials/physics'), probes=(...)))

    Args:
        None.

    Returns:
        tuple[DomainSpec, ...]: Result produced by `domain_specs`.
    """

    domains: list[DomainSpec] = []
    for name in ("chemistry", "biology", "physics"):
        folder = TRIALS_ROOT / name
        prompts_path = folder / "PROMPTS.md"
        probes = parse_prompts_markdown(prompts_path)
        domains.append(
            DomainSpec(
                name=name,
                folder=folder,
                probes=probes,
            )
        )
    return tuple(domains)


def main() -> int:
    """
    High Level Purpose:
        In circumstances like running one cross-domain validation sweep after controller or retrieval changes, helps with executing the generic chemistry, biology, and physics trial plan and writing one timestamped summary report.

    Reference to Theory:
        Supports practical validation of semantic reuse and composition by applying one uniform harness across several domain corpora.

    Example Input Output:
        Input: `main()`
        Output: 0

    Args:
        None.

    Returns:
        int: Result produced by `main`.
    """

    parser = argparse.ArgumentParser(description="Run fresh-db domain validation across chemistry, biology, and physics curricula.")
    parser.add_argument(
        "--domains",
        nargs="+",
        help="Optional domain names to run, such as chemistry biology physics.",
    )
    args = parser.parse_args()

    started = iso_now()
    report_root_override = str(os.getenv("TRIAL_DOMAIN_VALIDATION_REPORT_ROOT", "")).strip()
    report_root = Path(report_root_override) if report_root_override else REPORTS_ROOT / f"trial_domain_validation_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    report_root.mkdir(parents=True, exist_ok=True)
    write_running_report(report_root, started_at=started)
    env = base_env()
    specs = list(domain_specs())
    if args.domains:
        wanted = {str(item).strip() for item in args.domains if str(item).strip()}
        specs = [spec for spec in specs if spec.name in wanted]
        missing = sorted(wanted - {spec.name for spec in specs})
        if missing:
            raise SystemExit(f"Unknown domain names: {', '.join(missing)}")
    domains = [run_domain(spec, report_root=report_root, env=env) for spec in specs]
    overall_status = "ok" if all(item.get("status") == "ok" for item in domains) else "failed"
    report = {
        "started_at": started,
        "finished_at": iso_now(),
        "status": overall_status,
        "report_root": str(report_root),
        "domains": domains,
    }
    report_path = report_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n")
    print(json.dumps(report, indent=2, sort_keys=False))
    return 0 if overall_status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
