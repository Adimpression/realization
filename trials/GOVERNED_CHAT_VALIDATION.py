from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import time
from typing import Any, Callable

from realized_core.chat import CoreConversationHost
from realized_core_engine import EngineConfiguration
import supplement


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIO = (
    Path(__file__).resolve().parent
    / "governed_chat"
    / "FIVE_TURN_HERB_GARDEN.json"
)
DEFAULT_REPORT_ROOT = ROOT / "reports" / "governed_chat"
LOCAL_ENV = ROOT / "local.env"


@dataclass(frozen=True, slots=True)
class TrialOutcome:
    report: dict[str, Any]
    exit_code: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _elapsed_seconds(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)


def _normalized_text(value: str) -> str:
    normalized = str(value or "").casefold().replace("×", "x")
    return re.sub(r"\s+", " ", normalized).strip()


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def load_local_env(path: Path = LOCAL_ENV) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_scenario(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("The governed-chat scenario must be a JSON object.")
    turns = payload.get("turns")
    if not isinstance(turns, list) or len(turns) != 5:
        raise ValueError("The governed-chat scenario must contain exactly five turns.")
    if str(turns[0].get("treatment", "")) != "independent":
        raise ValueError("The first governed-chat turn must be independent.")
    for index, turn in enumerate(turns, start=1):
        if not isinstance(turn, dict) or not str(turn.get("prompt", "")).strip():
            raise ValueError(f"Governed-chat turn {index} must contain a prompt.")
        if str(turn.get("treatment", "")) not in {
            "independent",
            "human_contribution",
            "follow_up",
            "correction",
        }:
            raise ValueError(f"Governed-chat turn {index} has an invalid treatment.")
    return payload


def evaluate_answer(answer: str, turn: dict[str, Any]) -> dict[str, Any]:
    normalized_answer = _normalized_text(answer)
    checks: list[dict[str, Any]] = []
    for expectation in turn.get("required_concepts", []):
        alternatives = [
            _normalized_text(candidate)
            for candidate in expectation.get("any_of", [])
            if str(candidate).strip()
        ]
        matched = next(
            (candidate for candidate in alternatives if candidate in normalized_answer),
            "",
        )
        checks.append(
            {
                "label": str(expectation.get("label", "unnamed concept")),
                "passed": bool(matched),
                "matched": matched,
                "alternatives": alternatives,
            }
        )
    for expectation in turn.get("forbidden_concepts", []):
        alternatives = [
            _normalized_text(candidate)
            for candidate in expectation.get("any_of", [])
            if str(candidate).strip()
        ]
        matched = next(
            (candidate for candidate in alternatives if candidate in normalized_answer),
            "",
        )
        checks.append(
            {
                "label": str(expectation.get("label", "forbidden concept")),
                "passed": not bool(matched),
                "matched": matched,
                "alternatives": alternatives,
                "forbidden": True,
            }
        )
    passed = sum(1 for check in checks if check["passed"])
    return {
        "passed": passed == len(checks),
        "checks_passed": passed,
        "checks_total": len(checks),
        "score": round(passed / len(checks), 6) if checks else 1.0,
        "checks": checks,
    }


class TimedLlmRequests:
    """Time logical ``ask_llm`` requests without changing their contract.

    A request can contain provider-internal retries. Those attempts contribute to
    elapsed time but are not counted separately here.
    """

    def __init__(self, record_path: Path | None = None) -> None:
        self.records: list[dict[str, Any]] = []
        self.record_path = record_path
        self._original: Callable[..., Any] | None = None
        self._original_propose_json: Callable[..., Any] | None = None
        self._proposal_context: list[dict[str, str]] = []

    def __enter__(self) -> TimedLlmRequests:
        self._original = supplement.ask_llm
        self._original_propose_json = supplement.LLMSupplement.propose_json

        def timed_propose_json(
            instance: supplement.LLMSupplement,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            proposal_type = kwargs.get("proposal_type")
            mode = kwargs.get("mode")
            self._proposal_context.append(
                {
                    "proposal_type": str(getattr(proposal_type, "value", proposal_type or "")),
                    "supplement_mode": str(getattr(mode, "value", mode or "")),
                }
            )
            try:
                return self._original_propose_json(instance, *args, **kwargs)
            finally:
                self._proposal_context.pop()

        def timed_call(prompt: str, *args: Any, **kwargs: Any) -> Any:
            started_at = time.perf_counter()
            record: dict[str, Any] = {
                "request_index": len(self.records) + 1,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "prompt_characters": len(prompt),
                "requested_model": str(kwargs.get("model") or ""),
                "max_tokens": int(kwargs.get("max_tokens", 2048)),
                "reasoning_effort": str(kwargs.get("reasoning_effort") or ""),
                **(self._proposal_context[-1] if self._proposal_context else {}),
            }
            try:
                result = self._original(prompt, *args, **kwargs)
                record["status"] = "completed"
                if isinstance(result, tuple) and len(result) == 2:
                    metadata = result[1]
                    if isinstance(metadata, dict):
                        record["response_model"] = str(metadata.get("model") or "")
                        record["response_id"] = str(metadata.get("response_id") or "")
                return result
            except Exception as exc:
                record.update(
                    {
                        "status": "failed",
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    }
                )
                raise
            finally:
                record["elapsed_seconds"] = _elapsed_seconds(started_at)
                self.records.append(record)
                if self.record_path is not None:
                    self.record_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.record_path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(record, sort_keys=True) + "\n")

        supplement.ask_llm = timed_call
        supplement.LLMSupplement.propose_json = timed_propose_json
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        if self._original is not None:
            supplement.ask_llm = self._original
        if self._original_propose_json is not None:
            supplement.LLMSupplement.propose_json = self._original_propose_json


def summarize_performance(turns: list[dict[str, Any]]) -> dict[str, Any]:
    durations = [float(turn["elapsed_seconds"]) for turn in turns]
    request_durations = [
        float(request["elapsed_seconds"])
        for turn in turns
        for request in turn.get("llm_requests", [])
    ]
    total_turn_seconds = sum(durations)
    total_request_seconds = sum(request_durations)
    continuation_durations = durations[1:]
    return {
        "turn_count": len(turns),
        "logical_llm_request_count": len(request_durations),
        "total_turn_seconds": round(total_turn_seconds, 6),
        "total_llm_request_seconds": round(total_request_seconds, 6),
        "estimated_non_llm_seconds": round(
            max(0.0, total_turn_seconds - total_request_seconds),
            6,
        ),
        "llm_request_share": round(total_request_seconds / total_turn_seconds, 6)
        if total_turn_seconds
        else 0.0,
        "first_turn_seconds": durations[0] if durations else 0.0,
        "median_turn_seconds": round(statistics.median(durations), 6)
        if durations
        else 0.0,
        "median_continuation_seconds": round(
            statistics.median(continuation_durations),
            6,
        )
        if continuation_durations
        else 0.0,
        "slowest_turn_seconds": max(durations) if durations else 0.0,
        "per_turn_seconds": durations,
        "per_llm_request_seconds": request_durations,
    }


def execute_trial(
    *,
    scenario: dict[str, Any],
    host: CoreConversationHost,
    report_path: Path,
    base_report: dict[str, Any],
    llm_requests: TimedLlmRequests,
    max_median_turn_seconds: float | None = None,
    max_single_turn_seconds: float | None = None,
) -> TrialOutcome:
    turn_reports: list[dict[str, Any]] = []
    previous_run_id = ""
    semantic_checks_passed = 0
    semantic_checks_total = 0

    for index, turn in enumerate(scenario["turns"], start=1):
        request_start_index = len(llm_requests.records)
        started_at = time.perf_counter()
        try:
            result = host.submit(
                str(turn["prompt"]),
                treatment=str(turn["treatment"]),
                parent_run_id=previous_run_id,
            )
        except Exception as exc:
            failed_turn = {
                "index": index,
                "turn_id": str(turn.get("turn_id", f"turn_{index}")),
                "treatment": str(turn["treatment"]),
                "prompt": str(turn["prompt"]),
                "elapsed_seconds": _elapsed_seconds(started_at),
                "status": "operational_error",
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
                "llm_requests": llm_requests.records[request_start_index:],
            }
            turn_reports.append(failed_turn)
            report = {
                **base_report,
                "status": "operational_error",
                "completed_at": _utc_now(),
                "failure_stage": str(turn.get("turn_id", f"turn_{index}")),
                "turns": turn_reports,
                "performance": summarize_performance(turn_reports),
            }
            _write_report(report_path, report)
            return TrialOutcome(report=report, exit_code=2)

        elapsed = _elapsed_seconds(started_at)
        answer = str(result.get("assistant_text", ""))
        semantic = evaluate_answer(answer, turn)
        semantic_checks_passed += int(semantic["checks_passed"])
        semantic_checks_total += int(semantic["checks_total"])
        run_id = str(result.get("run_id", ""))
        parent_run_id = str(result.get("parent_run_id", ""))
        checkpoint_path = Path(str(result.get("checkpoint_path", "")))
        treatment = str(turn["treatment"])
        expected_parent_run_id = "" if treatment == "independent" else previous_run_id
        structure = {
            "completed": str(result.get("run_outcome", "")) == "completed",
            "non_empty_answer": bool(answer.strip()),
            "run_id_present": bool(run_id),
            "parent_run_matches": parent_run_id == expected_parent_run_id,
            "checkpoint_exists": checkpoint_path.is_file(),
            "treatment_matches": str(result.get("binding", {}).get("treatment", ""))
            == treatment,
        }
        turn_report = {
            "index": index,
            "turn_id": str(turn.get("turn_id", f"turn_{index}")),
            "treatment": treatment,
            "prompt": str(turn["prompt"]),
            "answer": answer,
            "elapsed_seconds": elapsed,
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "run_outcome": str(result.get("run_outcome", "")),
            "root_status": str(result.get("summary", {}).get("root_status", "")),
            "checkpoint_path": str(checkpoint_path),
            "structure": structure,
            "structure_passed": all(structure.values()),
            "semantic": semantic,
            "llm_requests": llm_requests.records[request_start_index:],
            "status": "completed",
        }
        turn_reports.append(turn_report)
        previous_run_id = run_id
        running_report = {
            **base_report,
            "status": "running",
            "turns_completed": index,
            "turns": turn_reports,
        }
        _write_report(report_path, running_report)

    semantic_score = (
        semantic_checks_passed / semantic_checks_total
        if semantic_checks_total
        else 1.0
    )
    semantic_threshold = float(scenario.get("minimum_semantic_score", 1.0))
    structural_passed = all(turn["structure_passed"] for turn in turn_reports)
    semantic_passed = semantic_score >= semantic_threshold
    performance = summarize_performance(turn_reports)
    timing_checks: dict[str, bool] = {}
    if max_median_turn_seconds is not None:
        timing_checks["median_turn_within_limit"] = (
            performance["median_turn_seconds"] <= max_median_turn_seconds
        )
    if max_single_turn_seconds is not None:
        timing_checks["slowest_turn_within_limit"] = (
            performance["slowest_turn_seconds"] <= max_single_turn_seconds
        )
    timing_passed = all(timing_checks.values()) if timing_checks else None
    passed = structural_passed and semantic_passed and timing_passed is not False
    report = {
        **base_report,
        "status": "passed" if passed else "failed",
        "completed_at": _utc_now(),
        "structural_passed": structural_passed,
        "semantic": {
            "passed": semantic_passed,
            "score": round(semantic_score, 6),
            "minimum_score": semantic_threshold,
            "checks_passed": semantic_checks_passed,
            "checks_total": semantic_checks_total,
        },
        "timing": {
            "passed": timing_passed,
            "checks": timing_checks,
            "max_median_turn_seconds": max_median_turn_seconds,
            "max_single_turn_seconds": max_single_turn_seconds,
        },
        "performance": performance,
        "turns": turn_reports,
    }
    _write_report(report_path, report)
    return TrialOutcome(report=report, exit_code=0 if passed else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a five-turn meaningfulness and latency trial over governed chat.",
    )
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--provider", choices=["openai", "llamacpp"])
    parser.add_argument("--model")
    parser.add_argument("--provider-timeout-seconds", type=float, default=60.0)
    parser.add_argument("--llm-policy", choices=["off", "auto", "required"], default="required")
    parser.add_argument("--max-steps", type=int, default=24)
    parser.add_argument("--discovery", choices=["on", "off"])
    parser.add_argument("--reflection", choices=["on", "off"])
    parser.add_argument("--contemplation", choices=["on", "off"])
    parser.add_argument("--max-median-turn-seconds", type=float)
    parser.add_argument("--max-single-turn-seconds", type=float)
    return parser


def _configure_environment(args: argparse.Namespace) -> dict[str, str]:
    for key, value in load_local_env().items():
        os.environ.setdefault(key, value)
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
    os.environ["LLM_TIMEOUT_SECONDS"] = str(args.provider_timeout_seconds)
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model
        os.environ["LLAMACPP_MODEL"] = args.model
        os.environ["LLM_FAST_MODEL"] = args.model
        os.environ["LLM_DEEP_MODEL"] = args.model
    provider = os.getenv("LLM_PROVIDER", "openai").strip().casefold()
    if provider == "llamacpp":
        model = os.getenv("LLM_FAST_MODEL") or os.getenv("LLAMACPP_MODEL") or ""
    else:
        model = os.getenv("LLM_FAST_MODEL") or os.getenv("OPENAI_MODEL") or ""
    return {"provider": provider, "model": model}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    environment = _configure_environment(args)
    scenario_path = args.scenario.expanduser().resolve()
    scenario = load_scenario(scenario_path)
    if args.output_dir:
        output_dir = args.output_dir.expanduser().resolve()
        if output_dir.exists() and any(output_dir.iterdir()):
            raise SystemExit(f"Output directory is not empty: {output_dir}")
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = DEFAULT_REPORT_ROOT / stamp
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"
    base_report: dict[str, Any] = {
        "schema_version": 1,
        "trial": "governed_chat_validation",
        "scenario_id": str(scenario.get("scenario_id", "")),
        "scenario_path": str(scenario_path),
        "started_at": _utc_now(),
        "status": "running",
        "configuration": {
            **environment,
            "provider_timeout_seconds": args.provider_timeout_seconds,
            "max_steps": args.max_steps,
            "discovery": args.discovery,
            "reflection": args.reflection,
            "contemplation": args.contemplation,
            "llm_policy": args.llm_policy,
        },
        "resumption_policy": "immediate_prior_committed_result_only",
        "conversation_root": str(output_dir / "conversation"),
        "report_path": str(report_path),
        "turns": [],
    }
    _write_report(report_path, base_report)
    host = CoreConversationHost(
        root=output_dir / "conversation",
        configuration=EngineConfiguration(
            max_steps=args.max_steps,
            llm_policy=args.llm_policy,
            discovery=args.discovery,
            reflection=args.reflection,
            contemplation=args.contemplation,
        ),
    )
    requests = TimedLlmRequests(output_dir / "llm_requests.jsonl")
    try:
        with requests:
            outcome = execute_trial(
                scenario=scenario,
                host=host,
                report_path=report_path,
                base_report=base_report,
                llm_requests=requests,
                max_median_turn_seconds=args.max_median_turn_seconds,
                max_single_turn_seconds=args.max_single_turn_seconds,
            )
    except KeyboardInterrupt:
        interrupted_report = {
            **base_report,
            "status": "interrupted",
            "completed_at": _utc_now(),
            "llm_requests": requests.records,
        }
        _write_report(report_path, interrupted_report)
        print(
            json.dumps(
                {
                    "status": "interrupted",
                    "report_path": str(report_path),
                    "logical_llm_request_count": len(requests.records),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 130
    summary = {
        "status": outcome.report["status"],
        "report_path": str(report_path),
        "semantic": outcome.report.get("semantic"),
        "performance": outcome.report.get("performance"),
        "failure_stage": outcome.report.get("failure_stage"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
