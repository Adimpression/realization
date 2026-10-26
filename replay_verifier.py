# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from applied_theory_types import (
    ControllerFeatureToggles,
    RuntimeDeterminismPolicy,
    enum_text,
    json_safe,
)
from constitutional_trace import canonical_trace_answer, compare_bundle_trace_to_state
from realized_core_governance.inventory import load_governance_inventory
from realized_core_governance.lifecycle import skill_lifecycle_from_payload
from realized_core_governance.records import artifact_skill_declaration
from runtime_temp import runtime_mkdtemp
from runtime_controller_api import new_runtime_controller
from run_bundle_io import (
    RUN_BUNDLE_SCHEMA_VERSION,
    governance_snapshot_for_artifacts,
)
from skill_schema_io import artifact_from_skill_document
from skill_governance import (
    evaluate_skill_admission,
    normalize_skill_kind,
)
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V2,
    normalize_skill_schema_version,
)
from realized_skill_semantics.execution import ability_executor_framework
from store import build_artifact_store
from system_state import SystemState, save_state

STATE_SQLITE_PATH_ENV = "STATE_SQLITE_PATH"


def _persist_bundle_skill_payloads(
    store: Any,
    payloads: list[dict[str, Any]],
    *,
    source_label: str = "run_bundle_replay",
) -> list[Any]:
    imported_artifacts: list[Any] = []
    policy_payloads = [payload for payload in payloads if normalize_skill_kind(payload.get("kind", "knowledge")) == "policy"]
    approval_payloads = [payload for payload in payloads if normalize_skill_kind(payload.get("kind", "knowledge")) == "approval"]
    revocation_payloads = [payload for payload in payloads if normalize_skill_kind(payload.get("kind", "knowledge")) == "revocation"]
    incident_payloads = [payload for payload in payloads if normalize_skill_kind(payload.get("kind", "knowledge")) == "incident"]
    skill_payloads = [
        payload
        for payload in payloads
        if normalize_skill_kind(payload.get("kind", "knowledge")) not in {"policy", "approval", "revocation", "incident"}
    ]
    for payload in policy_payloads:
        artifact = artifact_from_skill_document(payload)
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Policy artifacts are admitted governance records.",
            "policy_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        }
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status="admitted",
            policy_record=True,
            default_updated_at=str(content["skill_admission"].get("evaluated_at", "")),
        )
        artifact.content = content
        store.persist_artifact(artifact, run_id=f"{source_label}:{artifact.id}")
        imported_artifacts.append(artifact)
    for payload in approval_payloads:
        artifact = artifact_from_skill_document(payload)
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Approval artifacts are admitted governance records.",
            "policy_titles": [],
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        }
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status="admitted",
            policy_record=False,
            default_updated_at=str(content["skill_admission"].get("evaluated_at", "")),
        )
        artifact.content = content
        store.persist_artifact(artifact, run_id=f"{source_label}:{artifact.id}")
        imported_artifacts.append(artifact)
    for payload in [*revocation_payloads, *incident_payloads]:
        artifact = artifact_from_skill_document(payload)
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        content["skill_admission"] = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Safety governance artifacts are admitted governance records.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        }
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status="admitted",
            policy_record=False,
            default_updated_at=str(content["skill_admission"].get("evaluated_at", "")),
        )
        artifact.content = content
        store.persist_artifact(artifact, run_id=f"{source_label}:{artifact.id}")
        imported_artifacts.append(artifact)
    governance_snapshot = load_governance_inventory(store)
    installed_policies = list(governance_snapshot["policies"])
    installed_approvals = list(governance_snapshot["approvals"])
    for payload in skill_payloads:
        artifact = artifact_from_skill_document(payload)
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        if normalize_skill_schema_version(content.get("skill_schema", "")) == SKILL_SCHEMA_VERSION_V2:
            admission = evaluate_skill_admission(
                artifact_skill_declaration(artifact),
                skill_title=artifact.title,
                kind=normalize_skill_kind(content.get("skill_kind", "")),
                executor_framework=ability_executor_framework(
                    representation=enum_text(artifact.representation),
                    content=content,
                ),
                skill_content=content,
                policy_artifacts=installed_policies,
                approval_artifacts=installed_approvals,
            )
            content["skill_admission"] = admission
            content["skill_lifecycle"] = skill_lifecycle_from_payload(
                payload,
                admission_status=str(admission.get("status", "")),
                policy_record=False,
                default_updated_at=str(admission.get("evaluated_at", "")),
            )
            artifact.content = content
        store.persist_artifact(artifact, run_id=f"{source_label}:{artifact.id}")
        imported_artifacts.append(artifact)
    return imported_artifacts


def replay_run_bundle_document(
    bundle: Mapping[str, Any],
    *,
    sqlite_path: Path | None = None,
    llm_policy: str | None = None,
    max_steps: int | None = None,
    state_out: Path | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like replay verification of a previously exported governed run, helps with importing the bundled skills into a fresh store, rerunning the prompt, and reporting whether the replay remained constitutionally aligned.

    Reference to Theory:
        Supports OPEN_GOVERNANCE and BUNDLE replay requirements by making a governed run transportable and re-checkable under a fresh runtime boundary.

    Example Input Output:
        Input: `replay_run_bundle_document(bundle={'schema': 'bssc_run_bundle.v1', 'run': {'prompt': 'Say hi.'}, 'skills': []}, sqlite_path=Path('/tmp/replay.sqlite3'))`
        Output: {'replay_ok': True, 'comparison': {'matched': True, 'differences': []}}

    Args:
        bundle: Value for `bundle` used by `replay_run_bundle_document`. Expected type: `Mapping[str, Any]`.
        sqlite_path: Value for `sqlite_path` used by `replay_run_bundle_document`. Expected type: `Path | None`. Defaults to `None`.
        llm_policy: Value for `llm_policy` used by `replay_run_bundle_document`. Expected type: `str | None`. Defaults to `None`.
        max_steps: Value for `max_steps` used by `replay_run_bundle_document`. Expected type: `int | None`. Defaults to `None`.
        state_out: Value for `state_out` used by `replay_run_bundle_document`. Expected type: `Path | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `replay_run_bundle_document`.
    """
    payload = dict(bundle)
    if str(payload.get("schema", "")).strip() != RUN_BUNDLE_SCHEMA_VERSION:
        raise ValueError(f"Replay requires schema {RUN_BUNDLE_SCHEMA_VERSION}.")
    run = dict(payload.get("run", {})) if isinstance(payload.get("run", {}), Mapping) else {}
    if not str(run.get("prompt", "")).strip():
        raise ValueError("Run bundle replay requires a non-empty run.prompt.")
    replay_sqlite = Path(sqlite_path) if sqlite_path is not None else Path(runtime_mkdtemp(prefix="bssc_run_bundle_replay_")) / "state.sqlite3"
    replay_sqlite.parent.mkdir(parents=True, exist_ok=True)
    previous_sqlite = os.environ.get(STATE_SQLITE_PATH_ENV)
    try:
        os.environ[STATE_SQLITE_PATH_ENV] = str(replay_sqlite)
        store = build_artifact_store()
        skill_payloads = [
            dict(item)
            for item in payload.get("skills", [])
            if isinstance(item, Mapping)
        ]
        imported = _persist_bundle_skill_payloads(store, skill_payloads)
        state = SystemState.bootstrap(str(run.get("prompt", "")).strip())
        state.controller_features = ControllerFeatureToggles.from_dict(run.get("controller_features", {}))
        state.determinism_policy = RuntimeDeterminismPolicy.from_dict(run.get("determinism_policy"))
        state.llm_transcript = [
            dict(item)
            for item in run.get("llm_transcript", [])
            if isinstance(item, Mapping)
        ]
        determinism_mode = str(getattr(state.determinism_policy, "mode", "governed") or "governed").strip().lower() or "governed"
        llm_strategy = str(getattr(state.determinism_policy, "llm_strategy", "live") or "live").strip().lower() or "live"
        # Deterministic runs are captured under `record` but verified under `replay`.
        if determinism_mode in {"deterministic", "replay"} and state.llm_transcript and llm_strategy in {"record", "live"}:
            state.determinism_policy.llm_strategy = "replay"
        controller = new_runtime_controller(
            state,
            llm_policy=str(llm_policy or run.get("llm_policy", "off") or "off"),
        )
        controller.run(max_steps=int(max_steps if max_steps is not None else run.get("max_steps", 256) or 256))
        if state_out is not None:
            save_state(state, state_out)
        comparison = compare_bundle_trace_to_state(
            payload.get("constitutional_trace", {}),
            state,
            strict=determinism_mode in {"deterministic", "replay"},
        )
        bundle_governance = dict(payload.get("governance_snapshot", {})) if isinstance(payload.get("governance_snapshot", {}), Mapping) else {}
        replay_governance = governance_snapshot_for_artifacts(imported)
        original_receipts = dict(bundle_governance.get("receipts", {})) if isinstance(bundle_governance.get("receipts", {}), Mapping) else {}
        replay_receipts = dict(replay_governance.get("receipts", {})) if isinstance(replay_governance.get("receipts", {}), Mapping) else {}
        governance_differences: list[str] = []
        for key in ("policy_titles", "approval_titles", "revocation_titles", "incident_titles", "registry"):
            if str(original_receipts.get(key, "")) != str(replay_receipts.get(key, "")):
                governance_differences.append(f"governance receipt differs: {key}")
        if governance_differences:
            comparison["matched"] = False
            comparison.setdefault("differences", []).extend(governance_differences)
        comparison["original_governance_receipts"] = original_receipts
        comparison["replay_governance_receipts"] = replay_receipts
        original_answer = canonical_trace_answer(run.get("final_answer", ""))
        replay_answer = canonical_trace_answer(state.root_final_answer())
        if original_answer != replay_answer:
            comparison["matched"] = False
            comparison.setdefault("differences", []).append("final answer differs")
        if str(run.get("run_outcome", "")).strip() != state.run_outcome.value:
            comparison["matched"] = False
            comparison.setdefault("differences", []).append("run outcome differs")
        return {
            "schema": "bssc_run_replay_report.v1",
            "bundle_schema": RUN_BUNDLE_SCHEMA_VERSION,
            "replay_ok": bool(comparison.get("matched", False)),
            "sqlite_path": str(replay_sqlite),
            "original_run": {
                "prompt": str(run.get("prompt", "")).strip(),
                "run_outcome": str(run.get("run_outcome", "")).strip(),
                "final_answer": run.get("final_answer"),
            },
            "replay_run": {
                "run_id": state.run_id,
                "run_outcome": state.run_outcome.value,
                "final_answer": state.root_final_answer(),
            },
            "comparison": json_safe(comparison),
            "imported_skill_count": len(imported),
        }
    finally:
        if previous_sqlite is None:
            os.environ.pop(STATE_SQLITE_PATH_ENV, None)
        else:
            os.environ[STATE_SQLITE_PATH_ENV] = previous_sqlite
