# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from applied_theory_types import Artifact, json_safe, utc_now
from approval_governance import artifact_is_approval_record
from artifact import yaml_dump_human
from constitutional_trace import constitutional_trace_snapshot
from host_abi import host_abi_version
from skill_registry import skill_registry_document
from skill_export_projection import skill_export_document
from skill_schema_io import artifact_from_skill_document
from skill_governance import (
    SKILL_SCHEMA_VERSION_V2,
    SKILL_RISK_TIERS,
    artifact_is_policy_record,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)
from skill_safety_governance import artifact_is_incident_record, artifact_is_revocation_record
from system_state import SystemState, load_state

RUN_BUNDLE_SCHEMA_VERSION = "bssc_run_bundle.v1"
RUN_GOVERNANCE_SNAPSHOT_SCHEMA_VERSION = "bssc_run_governance_snapshot.v1"


def _canonical_receipt_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            key_text = str(key).strip()
            if key_text in {"captured_at", "generated_at", "exported_at"}:
                continue
            normalized[key_text] = _canonical_receipt_payload(value.get(key))
        return normalized
    if isinstance(value, list):
        return [_canonical_receipt_payload(item) for item in value]
    return json_safe(value)


def _receipt_digest(payload: Any) -> str:
    return yaml.safe_dump(_canonical_receipt_payload(payload), sort_keys=True)


def governance_snapshot_for_artifacts(artifacts: list[Artifact]) -> dict[str, Any]:
    registry = skill_registry_document(artifacts)
    registry_identity = sorted(
        [
        {
            "artifact_id": str(entry.get("artifact_id", "")).strip(),
            "title": str(entry.get("title", "")).strip(),
            "kind": str(entry.get("kind", "")).strip(),
            "schema": str(entry.get("schema", "")).strip(),
            "representation": str(entry.get("representation", "")).strip(),
            "executor": str(entry.get("executor", "")).strip(),
            "entrypoint": str(entry.get("entrypoint", "")).strip(),
        }
        for entry in registry.get("entries", [])
        if isinstance(entry, Mapping)
        ],
        key=lambda item: (
            str(item.get("title", "")).lower(),
            str(item.get("kind", "")).lower(),
            str(item.get("artifact_id", "")).lower(),
        ),
    )
    policy_titles = sorted(
        artifact.title for artifact in artifacts if artifact_is_policy_record(artifact)
    )
    approval_titles = sorted(
        artifact.title for artifact in artifacts if artifact_is_approval_record(artifact)
    )
    revocation_titles = sorted(
        artifact.title for artifact in artifacts if artifact_is_revocation_record(artifact)
    )
    incident_titles = sorted(
        artifact.title for artifact in artifacts if artifact_is_incident_record(artifact)
    )
    return {
        "schema": RUN_GOVERNANCE_SNAPSHOT_SCHEMA_VERSION,
        "captured_at": utc_now(),
        "policy_titles": policy_titles,
        "approval_titles": approval_titles,
        "revocation_titles": revocation_titles,
        "incident_titles": incident_titles,
        "registry": registry,
        "receipts": {
            "policy_titles": _receipt_digest(policy_titles),
            "approval_titles": _receipt_digest(approval_titles),
            "revocation_titles": _receipt_digest(revocation_titles),
            "incident_titles": _receipt_digest(incident_titles),
            "registry": _receipt_digest(registry_identity),
        },
    }


def _state_artifacts_by_id(state: SystemState) -> dict[str, Artifact]:
    artifacts: dict[str, Artifact] = {}
    for collection in (state.artifacts, state.learned_artifacts):
        for artifact_id, artifact in collection.items():
            if artifact_id and isinstance(artifact, Artifact):
                artifacts[str(artifact_id)] = artifact
    return artifacts


def referenced_run_bundle_artifacts(
    state: SystemState,
    artifact_store: Any,
) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like governed run bundle export, helps with collecting the skill, policy, and approval artifacts that are materially referenced by the recorded effect traces.

    Reference to Theory:
        Supports self-contained replay bundles by exporting the executed skill surface together with the governance records that justified the observed effects.

    Example Input Output:
        Input: `referenced_run_bundle_artifacts(state=state, artifact_store=store)`
        Output: [Artifact(id='artifact-skill-abc', title='Say Hi', artifact_type='ability', representation='python_script')]

    Args:
        state: Value for `state` used by `referenced_run_bundle_artifacts`. Expected type: `SystemState`.
        artifact_store: Value for `artifact_store` used by `referenced_run_bundle_artifacts`. Expected type: `Any`.

    Returns:
        list[Artifact]: Result produced by `referenced_run_bundle_artifacts`.
    """
    state_by_id = _state_artifacts_by_id(state)
    installed = [
        artifact
        for artifact in (artifact_store.load_all_artifacts() if artifact_store is not None else [])
        if isinstance(artifact, Artifact)
    ]
    installed_by_id = {str(artifact.id): artifact for artifact in installed if str(artifact.id).strip()}
    installed_by_title = {str(artifact.title).strip(): artifact for artifact in installed if str(artifact.title).strip()}
    selected: dict[str, Artifact] = {}
    if not state.effect_traces:
        selected = {
            str(artifact.title).strip(): artifact
            for artifact in state_by_id.values()
            if isinstance(artifact, Artifact) and str(artifact.title).strip()
        }
    policy_titles: set[str] = set()
    approval_titles: set[str] = set()
    for trace in state.effect_traces:
        if not isinstance(trace, Mapping):
            continue
        artifact_id = str(trace.get("artifact_id", "")).strip()
        artifact_title = str(trace.get("artifact_title", "")).strip()
        admission = dict(trace.get("admission", {})) if isinstance(trace.get("admission", {}), Mapping) else {}
        policy_titles.update(str(item).strip() for item in admission.get("policy_titles", []) if str(item).strip())
        approval_titles.update(str(item).strip() for item in admission.get("approval_titles", []) if str(item).strip())
        artifact = (
            installed_by_id.get(artifact_id)
            or state_by_id.get(artifact_id)
            or installed_by_title.get(artifact_title)
        )
        if artifact is not None:
            selected[str(artifact.title).strip()] = artifact
    for title in sorted(policy_titles | approval_titles):
        artifact = installed_by_title.get(title)
        if artifact is not None:
            selected[str(artifact.title).strip()] = artifact
    for artifact in installed:
        if artifact_is_policy_record(artifact) or artifact_is_approval_record(artifact) or artifact_is_revocation_record(artifact) or artifact_is_incident_record(artifact):
            selected[str(artifact.title).strip()] = artifact
    return [selected[key] for key in sorted(selected)]


def _synthetic_replay_policy_document(
    skill_documents: list[dict[str, Any]],
    *,
    run_id: str,
) -> dict[str, Any] | None:
    governed_skills = [
        document
        for document in skill_documents
        if normalize_skill_kind(document.get("kind", "knowledge")) not in {"policy", "approval"}
    ]
    if not governed_skills:
        return None
    if any(normalize_skill_kind(document.get("kind", "knowledge")) == "policy" for document in skill_documents):
        return None
    risk_index = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}
    max_risk_tier = "tier0_passive"
    target_kinds: list[str] = []
    allowed_authorities: list[str] = []
    allowed_executors: list[str] = []
    allowed_data_classes: list[str] = []
    for document in governed_skills:
        kind = normalize_skill_kind(document.get("kind", "knowledge"))
        if kind not in target_kinds:
            target_kinds.append(kind)
        declaration = dict(document.get("declaration", {})) if isinstance(document.get("declaration", {}), Mapping) else {}
        declared_risk = normalize_skill_risk_tier(declaration.get("risk_tier", "tier0_passive"), default="tier0_passive")
        if risk_index[declared_risk] > risk_index[max_risk_tier]:
            max_risk_tier = declared_risk
        for authority in normalize_skill_authorities(declaration.get("authorities_requested", [])):
            if authority not in allowed_authorities:
                allowed_authorities.append(authority)
        executor = str(document.get("executor", "")).strip()
        if executor and executor not in allowed_executors:
            allowed_executors.append(executor)
        for data_class in declaration.get("data_classes_touched", []):
            normalized = str(data_class).strip()
            if normalized and normalized not in allowed_data_classes:
                allowed_data_classes.append(normalized)
    return {
        "schema": SKILL_SCHEMA_VERSION_V2,
        "kind": "policy",
        "title": f"Replay Policy Snapshot / {run_id}",
        "policy": {
            "intent": "Admit the bundled replay skills exactly as exported for governed replay verification.",
            "target_kinds": target_kinds or ["knowledge", "ability"],
            "max_risk_tier": max_risk_tier,
            "allowed_authorities": allowed_authorities,
            "denied_authorities": [],
            "allowed_executors": allowed_executors,
            "allowed_data_classes": allowed_data_classes,
            "denied_side_effects": [],
            "required_approval_for_risk_tiers": {},
        },
    }


def run_bundle_document(
    state: SystemState,
    artifact_store: Any,
    *,
    llm_policy: str = "off",
    max_steps: int = 256,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting a governed execution for later review or replay, helps with building one self-contained run bundle that carries the prompt, governed trace, and referenced skills.

    Reference to Theory:
        Supports OPEN_GOVERNANCE and BUNDLE replay requirements by packaging the constitutional trace and the referenced portable skills together.

    Example Input Output:
        Input: `run_bundle_document(state=state, artifact_store=store, llm_policy='off', max_steps=64)`
        Output: {'schema': 'bssc_run_bundle.v1', 'run': {...}, 'skills': [...]}

    Args:
        state: Value for `state` used by `run_bundle_document`. Expected type: `SystemState`.
        artifact_store: Value for `artifact_store` used by `run_bundle_document`. Expected type: `Any`.
        llm_policy: Value for `llm_policy` used by `run_bundle_document`. Expected type: `str`. Defaults to `'off'`.
        max_steps: Value for `max_steps` used by `run_bundle_document`. Expected type: `int`. Defaults to `256`.

    Returns:
        dict[str, Any]: Result produced by `run_bundle_document`.
    """
    root = state.root()
    artifacts = referenced_run_bundle_artifacts(state, artifact_store)
    exported_skills: list[dict[str, Any]] = []
    bundle_artifacts: list[Artifact] = []
    for artifact in artifacts:
        document = skill_export_document(artifact)
        try:
            bundle_artifact = artifact_from_skill_document(document)
        except Exception:
            continue
        exported_skills.append(document)
        bundle_artifacts.append(bundle_artifact)
    synthetic_policy = _synthetic_replay_policy_document(exported_skills, run_id=state.run_id)
    if synthetic_policy is not None:
        exported_skills.insert(0, synthetic_policy)
        bundle_artifacts.insert(0, artifact_from_skill_document(synthetic_policy))
    governance_snapshot = governance_snapshot_for_artifacts(bundle_artifacts)
    return {
        "schema": RUN_BUNDLE_SCHEMA_VERSION,
        "kind": "governed_run_bundle",
        "exported_at": utc_now(),
        "host_abi_version": host_abi_version(),
        "run": {
            "run_id": state.run_id,
            "root_id": state.root_id,
            "prompt": root.semantic_unit,
            "run_outcome": state.run_outcome.value,
            "final_answer": state.root_final_answer(),
            "governance": state.governance.to_dict(),
            "controller_features": state.controller_features.to_dict(),
            "theory_version": state.theory_version,
            "llm_policy": str(llm_policy or "off"),
            "determinism_policy": getattr(state, "determinism_policy", None).to_dict()
            if getattr(state, "determinism_policy", None) is not None
            else {},
            "max_steps": int(max_steps),
            "llm_transcript": json_safe(getattr(state, "llm_transcript", [])),
        },
        "constitutional_trace": constitutional_trace_snapshot(state),
        "governance_snapshot": governance_snapshot,
        "skills": exported_skills,
    }


def export_run_bundle_text(
    state: SystemState,
    artifact_store: Any,
    *,
    llm_policy: str = "off",
    max_steps: int = 256,
) -> str:
    """
    High Level Purpose:
        In circumstances like CLI export of a governed run bundle, helps with rendering the bundle as human-readable YAML.

    Reference to Theory:
        Supports replayable bundle exchange by making the full governed run surface portable as one YAML document.

    Example Input Output:
        Input: `export_run_bundle_text(state=state, artifact_store=store, llm_policy='off', max_steps=64)`
        Output: 'schema: bssc_run_bundle.v1\nkind: governed_run_bundle\n...'

    Args:
        state: Value for `state` used by `export_run_bundle_text`. Expected type: `SystemState`.
        artifact_store: Value for `artifact_store` used by `export_run_bundle_text`. Expected type: `Any`.
        llm_policy: Value for `llm_policy` used by `export_run_bundle_text`. Expected type: `str`. Defaults to `'off'`.
        max_steps: Value for `max_steps` used by `export_run_bundle_text`. Expected type: `int`. Defaults to `256`.

    Returns:
        str: Result produced by `export_run_bundle_text`.
    """
    return yaml_dump_human(
        run_bundle_document(
            state,
            artifact_store,
            llm_policy=llm_policy,
            max_steps=max_steps,
        )
    ) + "\n"


def load_run_bundle_document(path: Path) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like governed replay of a previously exported run, helps with loading one run bundle document and validating its schema at the boundary.

    Reference to Theory:
        Supports replay bundles by treating the exported governed run as a first-class transport document rather than ad hoc local state.

    Example Input Output:
        Input: `load_run_bundle_document(path=Path('/tmp/run-bundle.yaml'))`
        Output: {'schema': 'bssc_run_bundle.v1', 'run': {...}, 'skills': [...]}

    Args:
        path: Value for `path` used by `load_run_bundle_document`. Expected type: `Path`.

    Returns:
        dict[str, Any]: Result produced by `load_run_bundle_document`.
    """
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, Mapping):
        raise ValueError("Run bundle YAML must be a non-empty mapping.")
    document = {str(key): value for key, value in payload.items()}
    if str(document.get("schema", "")).strip() != RUN_BUNDLE_SCHEMA_VERSION:
        raise ValueError(f"Run bundle requires schema {RUN_BUNDLE_SCHEMA_VERSION}.")
    return document


def load_run_bundle_from_state_file(
    state_path: Path,
    artifact_store: Any,
    *,
    llm_policy: str = "off",
    max_steps: int = 256,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting a run bundle from a previously saved state JSON, helps with loading the state and materializing the governed bundle document in one step.

    Reference to Theory:
        Supports replay export from durable controller state without requiring the original process to still be live.

    Example Input Output:
        Input: `load_run_bundle_from_state_file(state_path=Path('/tmp/state.json'), artifact_store=store, llm_policy='off', max_steps=64)`
        Output: {'schema': 'bssc_run_bundle.v1', 'run': {...}, 'skills': [...]}

    Args:
        state_path: Value for `state_path` used by `load_run_bundle_from_state_file`. Expected type: `Path`.
        artifact_store: Value for `artifact_store` used by `load_run_bundle_from_state_file`. Expected type: `Any`.
        llm_policy: Value for `llm_policy` used by `load_run_bundle_from_state_file`. Expected type: `str`. Defaults to `'off'`.
        max_steps: Value for `max_steps` used by `load_run_bundle_from_state_file`. Expected type: `int`. Defaults to `256`.

    Returns:
        dict[str, Any]: Result produced by `load_run_bundle_from_state_file`.
    """
    state = load_state(state_path)
    return run_bundle_document(state, artifact_store, llm_policy=llm_policy, max_steps=max_steps)
