from __future__ import annotations

import argparse
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import statistics
import time
from typing import Any, Callable

from realized_core_conversation import CoreConversationHost
from realized_core_llm import (
    ConversationPlanner,
    ConversationPlanningError,
    ConversationRenderer,
    build_environment_conversation_advisors,
)
from realized_core_engine import (
    EngineConfiguration,
    InspectionView,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIO = (
    Path(__file__).resolve().parent
    / "governed_chat"
    / "RESUMPTION_JOURNEY.json"
)
LEGACY_FIVE_TURN_SCENARIO = (
    Path(__file__).resolve().parent
    / "governed_chat"
    / "FIVE_TURN_HERB_GARDEN.json"
)
DEFAULT_REPORT_ROOT = ROOT / "reports" / "governed_chat"
LOCAL_ENV = ROOT / "local.env"

_CEDAR_SUPPORTED_OPERATIONS = {
    "attempt_prose_only_handoff",
    "attempt_similarity_only_continuation",
    "augment",
    "branch",
    "continue_from_stale_head",
    "continue_realignment",
    "correct",
    "explain",
    "inspect_current",
    "interrupt",
    "merge",
    "reconstruct",
    "redirect_and_realign",
    "replace_provider_and_resume",
    "rerender_then_resume",
    "restart_host_and_resume",
    "resume_after_interruption",
    "reverse",
    "start",
    "verify",
}


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
    flows = payload.get("flows")
    if isinstance(flows, list):
        if not flows:
            raise ValueError(
                "The resumption conversation scenario must contain flows."
            )
        seen_steps: set[str] = set()
        for flow_index, flow in enumerate(flows, start=1):
            if not isinstance(flow, dict):
                raise ValueError(
                    f"Resumption flow {flow_index} must be an object."
                )
            steps = flow.get("steps")
            if not isinstance(steps, list) or not steps:
                raise ValueError(
                    f"Resumption flow {flow_index} must contain steps."
                )
            for step_index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    raise ValueError(
                        f"Resumption step {flow_index}.{step_index} must be an object."
                    )
                step_id = str(step.get("step_id", "")).strip()
                operation = str(step.get("operation", "")).strip()
                if not step_id or not operation:
                    raise ValueError(
                        f"Resumption step {flow_index}.{step_index} requires "
                        "step_id and operation."
                    )
                if operation not in _CEDAR_SUPPORTED_OPERATIONS:
                    raise ValueError(
                        f"Unsupported Cedar harness operation: {operation}"
                    )
                if step_id in seen_steps:
                    raise ValueError(
                        f"Duplicate resumption step id: {step_id}"
                    )
                seen_steps.add(step_id)
        coverage = payload.get("principle_coverage")
        if not isinstance(coverage, dict) or not coverage:
            raise ValueError(
                "The resumption scenario requires principle coverage."
            )
        unknown = {
            str(step_id)
            for step_ids in coverage.values()
            for step_id in step_ids
            if str(step_id) not in seen_steps
        }
        if unknown:
            raise ValueError(
                "Principle coverage references unknown steps: "
                + ", ".join(sorted(unknown))
            )
        return payload
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
    """Collect provider timing and provenance from product-owned receipts."""

    def __init__(self, record_path: Path | None = None) -> None:
        self.records: list[dict[str, Any]] = []
        self.record_path = record_path

    def __enter__(self) -> TimedLlmRequests:
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        return None

    def capture_result(
        self,
        result: dict[str, Any],
        *,
        action: str,
    ) -> None:
        for stage in ("planning", "rendering"):
            stage_record = result.get(stage)
            if not isinstance(stage_record, dict):
                continue
            receipt = stage_record.get("provider_receipt")
            if isinstance(receipt, dict) and receipt:
                self.capture_receipt(stage, receipt, action=action)

    def capture_receipt(
        self,
        stage: str,
        receipt: dict[str, Any],
        *,
        action: str,
    ) -> None:
        record = {
            "request_index": len(self.records) + 1,
            "action": action,
            "stage": str(stage),
            "status": "completed",
            "provider": str(receipt.get("provider") or ""),
            "response_model": str(receipt.get("model") or ""),
            "response_id": str(receipt.get("response_id") or ""),
            "request_digest": str(receipt.get("request_digest") or ""),
            "response_digest": str(receipt.get("response_digest") or ""),
            "elapsed_seconds": float(receipt.get("elapsed_seconds") or 0.0),
        }
        self.records.append(record)
        if self.record_path is not None:
            self.record_path.parent.mkdir(parents=True, exist_ok=True)
            with self.record_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")


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


_CEDAR_PLANNER_OPERATIONS: dict[str, set[str]] = {
    "start": {"start"},
    "correct": {"correct"},
    "restart_host_and_resume": {"continue", "explain"},
    "replace_provider_and_resume": {"continue", "explain"},
    "rerender_then_resume": {"continue", "explain"},
    "interrupt": {"correct"},
    "resume_after_interruption": {"resume_after_interruption"},
    "augment": {"augment"},
    "redirect_and_realign": {"redirect_and_realign"},
    "continue_realignment": {"correct"},
    "explain": {"explain"},
    "verify": {"verify"},
    "reconstruct": {"reconstruct"},
    "reverse": {"reverse"},
    "branch": {"branch"},
    "merge": {"merge"},
    "continue_from_stale_head": {"augment", "continue", "correct"},
    "start_independent": {"start"},
}


def _is_explicit_noncommit_outcome(result: dict[str, Any]) -> bool:
    return str(result.get("run_outcome", "")) in {
        "stale",
        "rejected",
        "ambiguous",
    }


def _require_advanced_setup_result(
    result: dict[str, Any],
    parent_run_id: str,
) -> str:
    run_id = str(result.get("run_id", ""))
    if (
        _is_explicit_noncommit_outcome(result)
        or not run_id
        or run_id == parent_run_id
    ):
        raise RuntimeError(
            "stale-anchor setup did not advance the bound branch"
        )
    return run_id


@dataclass
class CedarTrialRunner:
    """Execute the full Cedar conversation through the real application path."""

    scenario: dict[str, Any]
    host: CoreConversationHost
    host_factory: Callable[[], CoreConversationHost]
    advisor_factory: Callable[
        [], tuple[ConversationPlanner, ConversationRenderer]
    ]
    llm_requests: TimedLlmRequests

    def __post_init__(self) -> None:
        self.planner, self.renderer = self.advisor_factory()
        self.trial_root = self.host.root.parent
        self.checkpoint_root = self.trial_root / ".cedar-flow-checkpoints"
        self.step_runs: dict[str, str] = {}
        self.step_checkpoints: dict[str, Path] = {}
        self.run_results: dict[str, dict[str, Any]] = {}
        self.branch_aliases: dict[str, str] = {}
        self.attempt_ids: dict[str, str] = {}
        self.interruptions: dict[str, dict[str, Any]] = {}

    def execute(
        self,
        *,
        report_path: Path,
        base_report: dict[str, Any],
        max_median_turn_seconds: float | None,
        max_single_turn_seconds: float | None,
    ) -> TrialOutcome:
        step_reports: list[dict[str, Any]] = []
        for flow in self.scenario["flows"]:
            flow_id = str(flow["flow_id"])
            starts_from = str(flow.get("starts_from", ""))
            flow_start_run = self.step_runs.get(starts_from, "")
            if starts_from and not flow_start_run:
                return self._operational_failure(
                    report_path,
                    base_report,
                    step_reports,
                    starts_from,
                    RuntimeError(
                        f"Flow {flow_id} has no completed baseline {starts_from}."
                    ),
                )
            if starts_from:
                self._activate_flow_checkpoint(flow_id, starts_from)
                self.branch_aliases = {}
                self.attempt_ids = {}
                self.interruptions = {}
            current_run = flow_start_run
            for step in flow["steps"]:
                request_start = len(self.llm_requests.records)
                started_at = time.perf_counter()
                try:
                    step_report, next_run = self._execute_step(
                        flow_id=flow_id,
                        step=dict(step),
                        current_run=current_run,
                        flow_start_run=flow_start_run,
                    )
                except Exception as exc:
                    if isinstance(exc, ConversationPlanningError):
                        provider_receipt = exc.provider_receipt
                        if provider_receipt:
                            self.llm_requests.capture_receipt(
                                "planning",
                                provider_receipt,
                                action="semantic_turn",
                            )
                    return self._operational_failure(
                        report_path,
                        base_report,
                        step_reports,
                        str(step.get("step_id", "unknown")),
                        exc,
                        elapsed_seconds=_elapsed_seconds(started_at),
                        llm_requests=self.llm_requests.records[request_start:],
                    )
                step_report.update(
                    {
                        "flow_id": flow_id,
                        "elapsed_seconds": _elapsed_seconds(started_at),
                        "llm_requests": self.llm_requests.records[
                            request_start:
                        ],
                    }
                )
                step_reports.append(step_report)
                current_run = next_run
                self._capture_step_checkpoint(str(step["step_id"]))
                running_report = {
                    **base_report,
                    "status": "running",
                    "steps_completed": len(step_reports),
                    "steps": step_reports,
                }
                _write_report(report_path, running_report)

        structural_passed = all(
            bool(step.get("structural_passed")) for step in step_reports
        )
        structural_checks = [
            check
            for step in step_reports
            for check in step.get("checks", [])
            if check.get("category") == "structure"
        ]
        interpretation_checks = [
            check
            for step in step_reports
            for check in step.get("checks", [])
            if check.get("category") == "interpretation"
        ]
        interpretation_passed = all(
            check["passed"] for check in interpretation_checks
        )
        rendering_checks = [
            check
            for step in step_reports
            for check in step.get("checks", [])
            if check.get("category") == "rendering"
        ]
        rendering_passed = all(check["passed"] for check in rendering_checks)
        performance = summarize_performance(step_reports)
        timing_checks: dict[str, bool] = {}
        if max_median_turn_seconds is not None:
            timing_checks["median_turn_within_limit"] = (
                performance["median_turn_seconds"]
                <= max_median_turn_seconds
            )
        if max_single_turn_seconds is not None:
            timing_checks["slowest_turn_within_limit"] = (
                performance["slowest_turn_seconds"]
                <= max_single_turn_seconds
            )
        timing_passed = all(timing_checks.values()) if timing_checks else None
        passed = (
            structural_passed
            and interpretation_passed
            and rendering_passed
            and timing_passed is not False
        )
        report = {
            **base_report,
            "status": "passed" if passed else "failed",
            "completed_at": _utc_now(),
            "structural_passed": structural_passed,
            "structural": {
                "passed": structural_passed,
                "checks_passed": sum(
                    1 for check in structural_checks if check["passed"]
                ),
                "checks_total": len(structural_checks),
            },
            "interpretation": {
                "passed": interpretation_passed,
                "checks_passed": sum(
                    1 for check in interpretation_checks if check["passed"]
                ),
                "checks_total": len(interpretation_checks),
            },
            "rendering": {
                "passed": rendering_passed,
                "checks_passed": sum(
                    1 for check in rendering_checks if check["passed"]
                ),
                "checks_total": len(rendering_checks),
            },
            "principle_coverage": dict(
                self.scenario.get("principle_coverage", {})
            ),
            "timing": {
                "passed": timing_passed,
                "checks": timing_checks,
                "max_median_turn_seconds": max_median_turn_seconds,
                "max_single_turn_seconds": max_single_turn_seconds,
            },
            "performance": performance,
            "semantic_turn_count": sum(
                1 for step in step_reports if step.get("semantic_turn")
            ),
            "operational_action_count": sum(
                len(step.get("harness_actions", ()))
                for step in step_reports
            ),
            "steps": step_reports,
        }
        _write_report(report_path, report)
        return TrialOutcome(report=report, exit_code=0 if passed else 1)

    def _capture_step_checkpoint(self, step_id: str) -> None:
        checkpoint = self.checkpoint_root / step_id
        if checkpoint.exists():
            raise RuntimeError(f"Duplicate Cedar checkpoint: {step_id}")
        source_database = self.host.sqlite_path
        ignored = shutil.ignore_patterns(
            source_database.name,
            f"{source_database.name}-shm",
            f"{source_database.name}-wal",
        )
        shutil.copytree(self.host.root, checkpoint, ignore=ignored)
        checkpoint_database = checkpoint / "artifacts.sqlite3"
        with (
            closing(sqlite3.connect(source_database)) as source,
            closing(sqlite3.connect(checkpoint_database)) as destination,
        ):
            source.backup(destination)
        self.step_checkpoints[step_id] = checkpoint

    def _activate_flow_checkpoint(self, flow_id: str, step_id: str) -> None:
        checkpoint = self.step_checkpoints.get(step_id)
        if checkpoint is None:
            raise RuntimeError(f"No durable Cedar checkpoint exists for {step_id}.")
        flow_root = self.trial_root / "flow-sessions" / flow_id
        if flow_root.exists():
            raise RuntimeError(f"Duplicate Cedar flow session: {flow_id}")
        shutil.copytree(checkpoint, flow_root)
        flow_database = flow_root / "artifacts.sqlite3"
        self.host = CoreConversationHost(
            root=flow_root,
            configuration=replace(
                self.host.configuration,
                sqlite_path=flow_database,
            ),
        )

    def _execute_step(
        self,
        *,
        flow_id: str,
        step: dict[str, Any],
        current_run: str,
        flow_start_run: str,
    ) -> tuple[dict[str, Any], str]:
        step_id = str(step["step_id"])
        harness_operation = str(step["operation"])
        prompt = str(step.get("prompt", "")).strip()
        parent_run = current_run
        if step_id in {"branch_executive", "branch_technical"}:
            parent_run = flow_start_run
        elif step_id == "merge_branches":
            parent_run = self.branch_aliases["executive"]
        elif step_id == "stale_continuation_rejected":
            parent_run = self.branch_aliases["technical"]

        pre = self._snapshot(parent_run) if parent_run else None
        result: dict[str, Any] | None = None
        metadata: dict[str, Any] = {}
        harness_actions: list[str] = []

        if harness_operation == "inspect_current":
            metadata["inspection_only"] = True
            harness_actions.append("inspect_current_state")
        elif harness_operation == "restart_host_and_resume":
            metadata.update(self.host.discard_transcript())
            harness_actions.extend(("discard_transcript", "restart_host"))
            self.host = self.host_factory()
            result = self._submit(prompt, parent_run)
            metadata["transcript_required"] = False
        elif harness_operation == "replace_provider_and_resume":
            harness_actions.extend(("replace_provider", "restart_host"))
            self.planner, self.renderer = self.advisor_factory()
            self.host = self.host_factory()
            result = self._submit(prompt, parent_run)
            metadata["provider_state_required"] = False
        elif harness_operation == "rerender_then_resume":
            harness_actions.append("rerender_durable_result")
            before_digest = str((pre or {}).get("digest", ""))
            source_result = self.run_results.get(parent_run)
            if source_result is None:
                raise RuntimeError(
                    f"No durable conversation result is known for {parent_run}."
                )
            rerendered = self.host.rerender_result(
                str(source_result["result_id"]),
                renderer=self.renderer,
                rendering_attempt_key=f"cedar-{step_id}",
            )
            provider_receipt = rerendered.get("provider_receipt")
            if isinstance(provider_receipt, dict) and provider_receipt:
                self.llm_requests.capture_receipt(
                    "rerendering",
                    provider_receipt,
                    action=step_id,
                )
            after_rerender_digest = str(
                self._snapshot(parent_run).get("digest", "")
            )
            result = self._submit(prompt, parent_run)
            metadata["digest_before_rerender"] = before_digest
            metadata["digest_after_rerender"] = after_rerender_digest
            metadata["rerendering"] = rerendered
            metadata["presentation_reparsed"] = False
        elif harness_operation == "interrupt":
            harness_actions.append("interrupt_running_attempt")
            observed: dict[str, Any] = {}

            def interrupt_running(attempt_id: str) -> None:
                observed["attempt_id"] = attempt_id
                observed["interruption"] = self.host.interrupt(
                    attempt_id,
                    reason="Cedar trial interruption boundary.",
                )

            result = self._submit(
                prompt,
                parent_run,
                on_attempt_running=interrupt_running,
            )
            attempt_id = str(observed.get("attempt_id", ""))
            if not attempt_id:
                raise RuntimeError("The running attempt was not observed.")
            self.attempt_ids[step_id] = attempt_id
            self.interruptions[step_id] = dict(
                observed.get("interruption", {})
            )
            metadata.update(observed)
        elif harness_operation == "resume_after_interruption":
            source_attempt = self.attempt_ids["interrupt_candidate"]
            result = self._submit(
                prompt,
                parent_run,
                source_attempt_id=source_attempt,
            )
            metadata["source_attempt_id"] = source_attempt
        elif harness_operation == "attempt_similarity_only_continuation" or harness_operation == "attempt_prose_only_handoff":
            harness_actions.append("isolate_unbound_host")
            unbound_root = self.host.root.parent / f"unbound-{step_id}"
            unbound = CoreConversationHost(
                root=unbound_root,
                configuration=replace(
                    self.host.configuration,
                    sqlite_path=self.host.sqlite_path,
                ),
            )
            try:
                unbound.submit_text(
                    prompt,
                    planner=self.planner,
                    renderer=self.renderer,
                    require_existing_binding=True,
                )
            except ConversationPlanningError as exc:
                metadata.update(
                    {
                        "expected_rejection": True,
                        "error": str(exc),
                        "causal_binding_created": False,
                        "state_reconstructed_from_presentation": False,
                    }
                )
            else:
                metadata["expected_rejection"] = False
        elif step_id == "ambiguous_reversal":
            try:
                result = self._submit(prompt, parent_run)
            except ConversationPlanningError as exc:
                metadata.update(
                    {
                        "expected_rejection": True,
                        "error": str(exc),
                        "guessed_target": False,
                    }
                )
            else:
                metadata["expected_rejection"] = False
        elif harness_operation == "continue_from_stale_head":
            harness_actions.append("arrange_stale_anchor_race")
            setup = self._submit(
                str(step["setup_prompt"]),
                parent_run,
            )
            metadata["advanced_run_id"] = _require_advanced_setup_result(
                setup,
                parent_run,
            )
            result = self._submit(prompt, parent_run)
            metadata["silent_overwrite"] = not _is_explicit_noncommit_outcome(
                result
            )
        else:
            result = self._submit(prompt, parent_run)

        if result is not None and step_id == "redirect_checklist":
            try:
                stale_old_frontier = self._submit(
                    "Continue the superseded Cedar brief direction.",
                    parent_run,
                )
            except (ConversationPlanningError, ValueError) as exc:
                metadata["old_frontier_executable"] = None
                metadata["old_frontier_probe_error"] = str(exc)
            else:
                metadata["old_frontier_executable"] = (
                    stale_old_frontier.get("run_outcome") != "stale"
                )

        next_run = current_run
        if result is not None:
            next_run = str(result.get("run_id", current_run))
            self.step_runs[step_id] = next_run
            self.run_results[next_run] = dict(result)
            if step.get("branch_alias"):
                self.branch_aliases[str(step["branch_alias"])] = next_run
        elif step_id == "stale_continuation_rejected":
            next_run = str(metadata.get("advanced_run_id", current_run))
            self.step_runs[step_id] = next_run
        else:
            self.step_runs[step_id] = current_run

        post_run = next_run or parent_run
        post = self._snapshot(post_run) if post_run else None
        checks = self._evaluate_step(
            step=step,
            result=result,
            metadata=metadata,
            parent_run=parent_run,
            pre=pre,
            post=post,
        )
        report = {
            "step_id": step_id,
            "harness_operation": harness_operation,
            "harness_actions": harness_actions,
            "semantic_turn": bool(prompt),
            "prompt": prompt,
            "parent_run_id": parent_run,
            "run_id": post_run,
            "answer": str((result or {}).get("assistant_text", "")),
            "run_outcome": str((result or {}).get("run_outcome", "")),
            "planning": dict((result or {}).get("planning", {})),
            "rendering": dict((result or {}).get("rendering", {})),
            "metadata": metadata,
            "checks": checks,
            "structural_passed": all(check["passed"] for check in checks),
            "status": "completed",
        }
        return report, next_run

    def _submit(
        self,
        prompt: str,
        parent_run_id: str,
        *,
        source_attempt_id: str = "",
        on_attempt_running: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        result = self.host.submit_text(
            prompt,
            planner=self.planner,
            renderer=self.renderer,
            parent_run_id=parent_run_id,
            binding_aliases=self.branch_aliases,
            source_attempt_id=source_attempt_id,
            on_attempt_running=on_attempt_running,
        )
        self.llm_requests.capture_result(result, action="semantic_turn")
        return result

    def _snapshot(self, run_id: str) -> dict[str, Any]:
        state = self.host.inspect_binding(run_id)
        reconstruction = self.host.inspect_binding(
            run_id,
            view=InspectionView.RECONSTRUCTION,
        )
        identity = reconstruction["revision"]["identity"]
        return {
            "state": state,
            "digest": str(identity["state_digest"]),
            "objective_id": str(identity["objective_id"]),
            "branch_id": str(identity["branch_id"]),
            "revision_id": str(identity["revision_id"]),
            "parents": tuple(
                reconstruction["revision"].get("parent_revision_ids", ())
            ),
        }

    def _evaluate_step(
        self,
        *,
        step: dict[str, Any],
        result: dict[str, Any] | None,
        metadata: dict[str, Any],
        parent_run: str,
        pre: dict[str, Any] | None,
        post: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []

        def add(
            label: str,
            passed: bool,
            *,
            category: str = "structure",
            actual: Any = None,
            expected: Any = None,
        ) -> None:
            checks.append(
                {
                    "label": label,
                    "passed": bool(passed),
                    "category": category,
                    "actual": actual,
                    "expected": expected,
                }
            )

        harness_operation = str(step["operation"])
        if result is not None and result.get("planning"):
            planned_operation = str(
                result["planning"].get("proposal", {}).get("operation", "")
            )
            expected_operations = _CEDAR_PLANNER_OPERATIONS.get(
                harness_operation,
                _CEDAR_PLANNER_OPERATIONS.get(
                    "start_independent" if step["step_id"] == "independent_request" else harness_operation,
                    set(),
                ),
            )
            if expected_operations:
                add(
                    "natural language selected the intended operation family",
                    planned_operation in expected_operations,
                    category="interpretation",
                    actual=planned_operation,
                    expected=sorted(expected_operations),
                )
            if result["binding"]["execution_outcome"] != "interrupted":
                add(
                    "admitted result was rendered through the provider port",
                    result.get("rendering", {}).get("status") == "rendered",
                    category="rendering",
                    actual=result.get("rendering", {}).get("status"),
                    expected="rendered",
                )

        expected = dict(step.get("expect", {}))
        post_state = dict((post or {}).get("state", {}))
        pre_state = dict((pre or {}).get("state", {}))
        achieved = _semantic_values(post_state, "achieved")
        non_achieved = _semantic_values(post_state, "non_achievedness")
        all_terms = {
            *achieved.keys(),
            *achieved.values(),
            *non_achieved.keys(),
            *non_achieved.values(),
        }
        normalized_terms = {_normalized_text(term) for term in all_terms}

        if "achieved" in expected:
            for key, value in expected["achieved"].items():
                actual = achieved.get(_semantic_label(key), "")
                add(
                    f"achieved {key}",
                    _normalized_text(actual) == _normalized_text(value),
                    actual=actual,
                    expected=value,
                )
        if "non_achieved" in expected:
            for item in expected["non_achieved"]:
                wanted = _semantic_label(item)
                matched = wanted in non_achieved or any(
                    wanted in _semantic_label(value)
                    for value in non_achieved.values()
                )
                add(
                    f"non-achievedness retains {item}",
                    matched,
                    actual=non_achieved,
                    expected=item,
                )
        for field, should_exist in (
            ("current_values_include", True),
            ("inherits_current_values", True),
            ("current_values_exclude", False),
            ("forbidden_inherited_values", False),
        ):
            for item in expected.get(field, []):
                normalized = _normalized_text(item)
                present = any(
                    normalized in term or term in normalized
                    for term in normalized_terms
                    if term
                )
                add(
                    f"{field}: {item}",
                    present is should_exist,
                    actual=present,
                    expected=should_exist,
                )
        if expected.get("inherited_values") == []:
            add(
                "independent objective inherited no Cedar state",
                not any(
                    term in normalized_terms
                    for term in {"cedar", "green", "monday", "audience"}
                ),
            )
        if "objective_complete" in expected:
            actual = str((result or {}).get("run_outcome", "")) == "completed"
            add(
                "turn completion is separate from objective completion",
                actual is bool(expected["objective_complete"]),
                actual=actual,
                expected=expected["objective_complete"],
            )
        if expected.get("turn_complete"):
            add(
                "turn produced a response",
                bool(str((result or {}).get("assistant_text", "")).strip()),
                category="rendering",
            )
        if expected.get("transcript_required") is False:
            add("restart did not require transcript", metadata.get("transcript_required") is False)
        if expected.get("provider_state_required") is False:
            add("replacement provider retained continuity", metadata.get("provider_state_required") is False)
        if expected.get("state_digest_unchanged_by_rerender"):
            add(
                "presentation change did not change source state",
                metadata.get("digest_before_rerender")
                == metadata.get("digest_after_rerender"),
                actual=metadata.get("digest_after_rerender"),
                expected=metadata.get("digest_before_rerender"),
            )
        if expected.get("presentation_reparsed") is False:
            add("presentation was not reparsed", metadata.get("presentation_reparsed") is False)
        if expected.get("attempt_status") == "interrupted":
            add(
                "attempt was interrupted",
                str((result or {}).get("binding", {}).get("execution_outcome", "")) == "interrupted",
            )
        if expected.get("semantic_revision_created_by_interruption") is False:
            interruption = metadata.get("interruption", {})
            add(
                "interruption created no semantic revision",
                interruption.get("semantic_revision_created") is False,
            )
        if "candidate_not_admitted" in expected:
            candidate = _normalized_text(expected["candidate_not_admitted"])
            add(
                "interrupted candidate was not admitted",
                all(candidate not in term for term in normalized_terms),
            )
        if expected.get("source_is_latest_admitted_revision"):
            add(
                "resume used latest admitted revision",
                str((result or {}).get("parent_run_id", "")) == parent_run,
            )
        if expected.get("unfinished_candidate_is_current") is False:
            add(
                "unfinished candidate is absent",
                all("city officials" not in term for term in normalized_terms),
            )
        if expected.get("superseded_by_augmentation") == []:
            add(
                "augmentation added no supersession",
                len(post_state.get("supersession_edges", ()))
                == len(pre_state.get("supersession_edges", ())),
            )
        if "governing_direction" in expected:
            objective = _normalized_text(
                post_state.get("governing_direction", {}).get("objective", "")
            )
            add(
                "governing direction changed",
                _normalized_text(expected["governing_direction"]) in objective,
                actual=objective,
                expected=expected["governing_direction"],
            )
        if "retained" in expected:
            for selector in expected["retained"]:
                add(
                    f"realignment retained {selector}",
                    _semantic_label(selector) in achieved
                    or _semantic_label(selector) in non_achieved,
                )
        superseded = expected.get("superseded")
        if isinstance(superseded, dict):
            pre_items = {
                str(item.get("item_id", "")): item
                for collection in ("achieved", "non_achievedness")
                for item in pre_state.get(collection, ())
                if isinstance(item, dict)
            }
            post_items = {
                str(item.get("item_id", "")): item
                for collection in ("achieved", "non_achievedness")
                for item in post_state.get(collection, ())
                if isinstance(item, dict)
            }
            edges = tuple(
                edge
                for edge in post_state.get("supersession_edges", ())
                if isinstance(edge, dict)
            )
            for selector, prior_values in superseded.items():
                wanted_selector = _semantic_label(selector)
                wanted_values = {
                    _normalized_text(value) for value in prior_values
                }
                prior_ids = {
                    item_id
                    for item_id, item in pre_items.items()
                    if _semantic_label(
                        item.get("payload", {}).get("semantic_key", "")
                    )
                    == wanted_selector
                    and _normalized_text(
                        item.get("payload", {}).get("value")
                        or item.get("payload", {}).get("text", "")
                    )
                    in wanted_values
                }
                replacement_ids = {
                    item_id
                    for item_id, item in post_items.items()
                    if _semantic_label(
                        item.get("payload", {}).get("semantic_key", "")
                    )
                    == wanted_selector
                }
                passed = any(
                    str(edge.get("prior_item_id", "")) in prior_ids
                    and str(edge.get("replacement_item_id", ""))
                    in replacement_ids
                    for edge in edges
                )
                add(
                    f"correction superseded {selector}",
                    passed,
                    actual=list(edges),
                    expected=sorted(wanted_values),
                )
        elif isinstance(superseded, list):
            for selector in superseded:
                if _semantic_label(selector) == "brief direction":
                    prior = _normalized_text(
                        pre_state.get("governing_direction", {}).get(
                            "objective", ""
                        )
                    )
                    current = _normalized_text(
                        post_state.get("governing_direction", {}).get(
                            "objective", ""
                        )
                    )
                    passed = prior != current and "brief" not in current
                else:
                    passed = (
                        _semantic_label(selector) not in achieved
                        and _semantic_label(selector) not in non_achieved
                    )
                add(f"realignment superseded {selector}", passed)
        if "unresolved_applicability" in expected:
            unresolved = _unresolved_selectors(post_state)
            wanted = {_semantic_label(item) for item in expected["unresolved_applicability"]}
            add(
                "unresolved applicability matches",
                unresolved == wanted,
                actual=sorted(unresolved),
                expected=sorted(wanted),
            )
        if expected.get("old_frontier_executable") is False:
            add(
                "old frontier was stale after redirection",
                metadata.get("old_frontier_executable") is False,
            )
        if expected.get("current_state_changed") is False:
            add("read-only operation left state unchanged", (pre or {}).get("digest") == (post or {}).get("digest"))
        if "path_values_include" in expected:
            path_values = self._path_values(post_run_id=str((post or {}).get("revision_id", "")))
            for value in expected["path_values_include"]:
                add(f"path retains {value}", _normalized_text(value) in path_values)
        operation_result = dict((result or {}).get("summary", {}).get("operation_result", {}))
        if expected.get("path_verified"):
            add("path verification passed", operation_result.get("verified") is True)
        if expected.get("revision_digest_verified"):
            add("reconstruction verified", operation_result.get("verified") is True)
        if expected.get("history_erased") is False:
            add("reversal retained history", len(self._path_revision_ids(str((post or {}).get("revision_id", "")))) > 1)
        if expected.get("new_transition_created"):
            add("reversal created a new transition", str((post or {}).get("revision_id", "")) != parent_run)
        if expected.get("request_rejected_before_mutation"):
            add("ambiguous request rejected", metadata.get("expected_rejection") is True)
        if expected.get("guessed_target") is False:
            add("ambiguous target was not guessed", metadata.get("guessed_target") is False)
        if expected.get("state_changed") is False:
            add("rejected request did not change state", (pre or {}).get("digest") == (post or {}).get("digest"))
        if "inherits_non_achieved" in expected:
            for selector in expected["inherits_non_achieved"]:
                add(f"branch inherited {selector}", _semantic_label(selector) in non_achieved)
        if "branch_distinct_from" in expected:
            other = self.branch_aliases.get(str(expected["branch_distinct_from"]), "")
            add("branches are distinct", bool(other and other != str((post or {}).get("revision_id", ""))))
        if expected.get("parents_preserved"):
            expected_parents = {self.branch_aliases[alias] for alias in expected.get("parent_branches", [])}
            add("merge preserved both parents", set((post or {}).get("parents", ())) == expected_parents)
        if expected.get("silent_overwrite") is False:
            add("stale continuation did not overwrite", metadata.get("silent_overwrite") is False)
        if expected.get("outcome") == "rejected_or_reconciled":
            add("stale result was explicit", str((result or {}).get("run_outcome", "")) in {"stale", "rejected", "ambiguous"})
        if expected.get("new_objective_identity"):
            add("independent request has a new objective", (pre or {}).get("objective_id") != (post or {}).get("objective_id"))
        if expected.get("causal_binding_created") is False:
            add("similarity created no binding", metadata.get("causal_binding_created") is False)
        if expected.get("state_reconstructed_from_presentation") is False:
            add("prose did not reconstruct state", metadata.get("state_reconstructed_from_presentation") is False)
        return checks

    def _path_revision_ids(self, post_run_id: str) -> tuple[str, ...]:
        if not post_run_id:
            return ()
        payload = self.host.inspect_binding(
            post_run_id,
            view=InspectionView.PATH,
        )
        return tuple(str(item) for item in payload.get("revision_ids", ()))

    def _path_values(self, *, post_run_id: str) -> set[str]:
        values: set[str] = set()
        for revision_id in self._path_revision_ids(post_run_id):
            state = self.host.inspect_binding(revision_id)
            for collection in ("achieved", "non_achievedness"):
                values.update(
                    _normalized_text(value)
                    for value in _semantic_values(state, collection).values()
                )
        return values

    @staticmethod
    def _operational_failure(
        report_path: Path,
        base_report: dict[str, Any],
        step_reports: list[dict[str, Any]],
        failure_stage: str,
        error: Exception,
        *,
        elapsed_seconds: float = 0.0,
        llm_requests: list[dict[str, Any]] | None = None,
    ) -> TrialOutcome:
        failed_step = {
            "step_id": failure_stage,
            "status": "operational_error",
            "elapsed_seconds": elapsed_seconds,
            "error_type": type(error).__name__,
            "error": str(error)[:1000],
            "llm_requests": list(llm_requests or ()),
        }
        reports = [*step_reports, failed_step]
        report = {
            **base_report,
            "status": "operational_error",
            "completed_at": _utc_now(),
            "failure_stage": failure_stage,
            "steps": reports,
            "performance": summarize_performance(reports),
        }
        _write_report(report_path, report)
        return TrialOutcome(report=report, exit_code=2)


def _semantic_label(value: Any) -> str:
    return _normalized_text(str(value)).replace("_", " ")


def _semantic_values(state: dict[str, Any], collection: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in state.get(collection, ()):
        payload = item.get("payload", {})
        if not isinstance(payload, dict):
            continue
        key = _semantic_label(payload.get("semantic_key", ""))
        if not key:
            continue
        values[key] = str(payload.get("value") or payload.get("text") or "")
    return values


def _unresolved_selectors(state: dict[str, Any]) -> set[str]:
    unresolved_ids = {
        str(item)
        for item in state.get("unresolved_applicability_item_ids", ())
    }
    return {
        key
        for collection in ("achieved", "non_achievedness")
        for item in state.get(collection, ())
        if str(item.get("item_id", "")) in unresolved_ids
        if (key := _semantic_label(item.get("payload", {}).get("semantic_key", "")))
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full Cedar resumption conversation or a legacy five-turn "
            "governed-chat characterization."
        ),
    )
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--provider", choices=["openai", "llamacpp"])
    parser.add_argument("--model")
    parser.add_argument("--provider-timeout-seconds", type=float, default=60.0)
    parser.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high"],
        default="minimal",
    )
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
            "reasoning_effort": args.reasoning_effort,
            "max_steps": args.max_steps,
            "discovery": args.discovery,
            "reflection": args.reflection,
            "contemplation": args.contemplation,
            "llm_policy": args.llm_policy,
        },
        "resumption_policy": (
            "explicit_causal_binding"
            if "flows" in scenario
            else "immediate_prior_committed_result_only"
        ),
        "conversation_root": str(output_dir / "conversation"),
        "report_path": str(report_path),
        "turns": [],
    }
    _write_report(report_path, base_report)
    conversation_root = output_dir / "conversation"
    configuration = EngineConfiguration(
        max_steps=args.max_steps,
        llm_policy=args.llm_policy,
        discovery=args.discovery,
        reflection=args.reflection,
        contemplation=args.contemplation,
    )
    host = CoreConversationHost(
        root=conversation_root,
        configuration=configuration,
    )

    def host_factory() -> CoreConversationHost:
        return CoreConversationHost(
            root=conversation_root,
            configuration=replace(
                configuration,
                sqlite_path=host.sqlite_path,
            ),
        )

    def advisor_factory() -> tuple[
        ConversationPlanner,
        ConversationRenderer,
    ]:
        return build_environment_conversation_advisors(
            provider=environment["provider"],
            model=environment["model"],
            timeout_seconds=args.provider_timeout_seconds,
            reasoning_effort=args.reasoning_effort,
        )

    requests = TimedLlmRequests(output_dir / "llm_requests.jsonl")
    try:
        with requests:
            if "flows" in scenario:
                outcome = CedarTrialRunner(
                    scenario=scenario,
                    host=host,
                    host_factory=host_factory,
                    advisor_factory=advisor_factory,
                    llm_requests=requests,
                ).execute(
                    report_path=report_path,
                    base_report=base_report,
                    max_median_turn_seconds=args.max_median_turn_seconds,
                    max_single_turn_seconds=args.max_single_turn_seconds,
                )
            else:
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
        "interpretation": outcome.report.get("interpretation"),
        "rendering": outcome.report.get("rendering"),
        "performance": outcome.report.get("performance"),
        "failure_stage": outcome.report.get("failure_stage"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
