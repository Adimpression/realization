# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import json
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from realized_core_governance.inventory import load_governance_inventory
from realized_core_governance.lifecycle import skill_lifecycle_from_payload
from realized_core_governance.persistence import persist_governed_artifacts
from realized_core_governance.records import artifact_skill_declaration
from realized_exchange.skill_export import export_skill_bundle_text
from realized_skill_application.projection import skill_kind_from_artifact
from realized_exchange.compiler import (
    compile_skill_document,
    compiled_skill_summary_from_artifact,
)
from realized_core_governance.vocabulary import normalize_skill_kind
from realized_core_engine.skill_governance import evaluate_skill_admission
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V2,
    normalize_skill_schema_version,
)
from realized_skill_semantics.execution import ability_executor_framework
from realized_exchange.skill_schema import (
    _runtime,
    load_skill_yaml_payload_documents,
    normalized_skill_bundle_filename_for_source,
    resolve_import_skill_files,
)


def _elapsed_seconds(start: float) -> float:
    """
    High Level Purpose:
        In circumstances like timing governed skill bundle installation work, helps with converting one monotonic start marker into a compact elapsed-seconds value for CLI reports.

    Reference to Theory:
        Supports open governance import/install reporting by making installation cost visible without changing admission or persistence semantics.

    Example Input Output:
        Input: `_elapsed_seconds(start=123.0)`
        Output: 0.123456

    Args:
        start: Value for `start` used by `_elapsed_seconds`. Expected type: `float`.

    Returns:
        float: Result produced by `_elapsed_seconds`.
    """
    return round(time.perf_counter() - start, 6)


def installed_governance_snapshot(store: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing governed skill bundles, helps with loading the currently installed policy, approval, revocation, and incident records once so admission can evaluate against the actual store state.

    Reference to Theory:
        Supports open governance installation by keeping import-time admission tied to installed governance records rather than to some ad hoc caller-local view.

    Example Input Output:
        Input: `installed_governance_snapshot(store=artifact_store)`
        Output: {'policies': [Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], 'approvals': [], 'revocations': [], 'incidents': []}

    Args:
        store: Value for `store` used by `installed_governance_snapshot`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `installed_governance_snapshot`.
    """
    return load_governance_inventory(store)


def record_import_batch(
    *,
    imported: list[dict[str, Any]],
    imported_artifacts_by_file: dict[Path, list[Any]],
    normalized_out_by_file: dict[Path, Path | None],
    artifacts: list[Any],
    reports: list[dict[str, Any]],
    skill_files_for_artifacts: list[Path],
    admissions: list[dict[str, Any]],
) -> None:
    """
    High Level Purpose:
        In circumstances like batch governed skill installation, helps with projecting persisted artifact reports into one stable user-facing import summary without duplicating that shaping logic for every governance record type.

    Reference to Theory:
        Supports open governance installation by keeping persistence, admission, and lifecycle reporting aligned while still letting installation persist different governed record classes in separate batches.

    Example Input Output:
        Input: `record_import_batch(imported=[], imported_artifacts_by_file={}, normalized_out_by_file={}, artifacts=[artifact], reports=[{'artifact_id': artifact.id}], skill_files_for_artifacts=[Path('/tmp/skill.yaml')], admissions=[{'status': 'admitted'}])`
        Output: None

    Args:
        imported: Value for `imported` used by `record_import_batch`. Expected type: `list[dict[str, Any]]`.
        imported_artifacts_by_file: Value for `imported_artifacts_by_file` used by `record_import_batch`. Expected type: `dict[Path, list[Any]]`.
        normalized_out_by_file: Value for `normalized_out_by_file` used by `record_import_batch`. Expected type: `dict[Path, Path | None]`.
        artifacts: Value for `artifacts` used by `record_import_batch`. Expected type: `list[Any]`.
        reports: Value for `reports` used by `record_import_batch`. Expected type: `list[dict[str, Any]]`.
        skill_files_for_artifacts: Value for `skill_files_for_artifacts` used by `record_import_batch`. Expected type: `list[Path]`.
        admissions: Value for `admissions` used by `record_import_batch`. Expected type: `list[dict[str, Any]]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    runtime = _runtime()
    for artifact, report, skill_file, admission in zip(artifacts, reports, skill_files_for_artifacts, admissions, strict=False):
        imported_artifacts_by_file.setdefault(skill_file, []).append(artifact)
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        lifecycle = dict(content.get("skill_lifecycle", {})) if isinstance(content.get("skill_lifecycle", {}), Mapping) else {}
        imported.append(
            {
                "artifact_id": report.get("artifact_id", artifact.id),
                "title": artifact.title,
                "kind": skill_kind_from_artifact(artifact),
                "representation": runtime.enum_text(artifact.representation),
                "skill_file": str(skill_file),
                "normalized_out": str(normalized_out_by_file.get(skill_file) or ""),
                "admission_status": str(admission.get("status", "")),
                "activation_status": lifecycle.get("activation_status", ""),
                "trust_status": lifecycle.get("trust_status", ""),
                "compiler_summary": compiled_skill_summary_from_artifact(artifact),
                "store_report": report,
            }
        )


def handle_import_skill_command(args: argparse.Namespace) -> int:
    """
    High Level Purpose:
        In circumstances like loading the smaller skill-facing YAML interface into the configured store, helps with importing one or more skills idempotently while optionally emitting normalized skill bundles.

    Reference to Theory:
        Supports open governance installation by accepting the portable skill kernel plus governance envelope, evaluating admission against installed governance state, and persisting the resulting artifacts without forcing callers to know store internals.

    Example Input Output:
        Input: `handle_import_skill_command(args=Namespace(skill_file=[Path('/tmp/skill.yaml')], normalized_out=Path('/tmp/normalized.yaml')))`
        Output: 0

    Args:
        args: Value for `args` used by `handle_import_skill_command`. Expected type: `argparse.Namespace`.

    Returns:
        int: Result produced by `handle_import_skill_command`.
    """
    runtime = _runtime()
    total_started = time.perf_counter()
    store = runtime.build_artifact_store()
    skill_files = resolve_import_skill_files(args)
    if not skill_files:
        raise SystemExit("import-skill requires --skill-file, --skill-files-file, or --skill-dir.")
    if args.normalized_out and args.normalized_out_dir:
        raise SystemExit("Use either --normalized-out or --normalized-out-dir, not both.")

    load_started = time.perf_counter()
    source_payloads: list[tuple[Path, list[dict[str, Any]]]] = []
    for skill_file in skill_files:
        source_payloads.append((skill_file, load_skill_yaml_payload_documents(skill_file)))
    load_seconds = _elapsed_seconds(load_started)

    total_artifacts = sum(len(items) for _, items in source_payloads)
    batch_mode = (
        len(skill_files) > 1
        or total_artifacts > 1
        or args.skill_files_file is not None
        or args.skill_dir is not None
        or args.normalized_out_dir is not None
    )
    if batch_mode and args.normalized_out:
        raise SystemExit("Use --normalized-out only for a single imported skill; use --normalized-out-dir for batch or multi-document import.")
    if batch_mode and args.normalized_out_dir:
        args.normalized_out_dir.mkdir(parents=True, exist_ok=True)

    classify_started = time.perf_counter()
    policy_entries: list[tuple[Path, dict[str, Any]]] = []
    approval_entries: list[tuple[Path, dict[str, Any]]] = []
    revocation_entries: list[tuple[Path, dict[str, Any]]] = []
    incident_entries: list[tuple[Path, dict[str, Any]]] = []
    skill_entries: list[tuple[Path, dict[str, Any]]] = []
    for skill_file, payloads in source_payloads:
        for payload in payloads:
            kind = normalize_skill_kind(payload.get("kind", "knowledge"))
            if kind == "policy":
                policy_entries.append((skill_file, payload))
            elif kind == "approval":
                approval_entries.append((skill_file, payload))
            elif kind == "revocation":
                revocation_entries.append((skill_file, payload))
            elif kind == "incident":
                incident_entries.append((skill_file, payload))
            else:
                skill_entries.append((skill_file, payload))
    classify_seconds = _elapsed_seconds(classify_started)

    imported: list[dict[str, Any]] = []
    normalized_out_by_file: dict[Path, Path | None] = {}
    imported_artifacts_by_file: dict[Path, list[Any]] = {skill_file: [] for skill_file in skill_files}
    persist_summaries: dict[str, dict[str, Any]] = {}

    governance_persist_started = time.perf_counter()

    policy_artifacts: list[Any] = []
    policy_skill_files: list[Path] = []
    policy_admissions: list[dict[str, Any]] = []
    for skill_file, payload in policy_entries:
        artifact = compile_skill_document(payload, source_kind="portable_skill_document").artifact
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        admission = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Policy artifacts are admitted governance records.",
            "policy_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        }
        content["skill_admission"] = admission
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status="admitted",
            policy_record=True,
            default_updated_at=str(admission.get("evaluated_at", "")),
        )
        artifact.content = content
        policy_artifacts.append(artifact)
        policy_skill_files.append(skill_file)
        policy_admissions.append(admission)
    if policy_artifacts:
        summary = persist_governed_artifacts(
            store,
            policy_artifacts,
            run_id="skill_import:policy_batch",
        )
        persist_summaries["policy"] = summary
        record_import_batch(
            imported=imported,
            imported_artifacts_by_file=imported_artifacts_by_file,
            normalized_out_by_file=normalized_out_by_file,
            artifacts=policy_artifacts,
            reports=list(summary.get("reports", [])),
            skill_files_for_artifacts=policy_skill_files,
            admissions=policy_admissions,
        )

    approval_artifacts: list[Any] = []
    approval_skill_files: list[Path] = []
    approval_admissions: list[dict[str, Any]] = []
    for skill_file, payload in approval_entries:
        artifact = compile_skill_document(payload, source_kind="portable_skill_document").artifact
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        admission = {
            "status": "admitted",
            "admitted": True,
            "rationale": "Approval artifacts are admitted governance records.",
            "policy_titles": [],
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": content.get("created_at", ""),
        }
        content["skill_admission"] = admission
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status="admitted",
            policy_record=False,
            default_updated_at=str(admission.get("evaluated_at", "")),
        )
        artifact.content = content
        approval_artifacts.append(artifact)
        approval_skill_files.append(skill_file)
        approval_admissions.append(admission)
    if approval_artifacts:
        summary = persist_governed_artifacts(
            store,
            approval_artifacts,
            run_id="skill_import:approval_batch",
        )
        persist_summaries["approval"] = summary
        record_import_batch(
            imported=imported,
            imported_artifacts_by_file=imported_artifacts_by_file,
            normalized_out_by_file=normalized_out_by_file,
            artifacts=approval_artifacts,
            reports=list(summary.get("reports", [])),
            skill_files_for_artifacts=approval_skill_files,
            admissions=approval_admissions,
        )

    safety_artifacts: list[Any] = []
    safety_skill_files: list[Path] = []
    safety_admissions: list[dict[str, Any]] = []
    for record_entries in (revocation_entries, incident_entries):
        for skill_file, payload in record_entries:
            artifact = compile_skill_document(payload, source_kind="portable_skill_document").artifact
            content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
            admission = {
                "status": "admitted",
                "admitted": True,
                "rationale": "Safety governance artifacts are admitted governance records.",
                "policy_titles": [],
                "approval_titles": [],
                "required_approval_class": "automatic",
                "evaluated_at": content.get("created_at", ""),
            }
            content["skill_admission"] = admission
            content["skill_lifecycle"] = skill_lifecycle_from_payload(
                payload,
                admission_status="admitted",
                policy_record=False,
                default_updated_at=str(admission.get("evaluated_at", "")),
            )
            artifact.content = content
            safety_artifacts.append(artifact)
            safety_skill_files.append(skill_file)
            safety_admissions.append(admission)
    if safety_artifacts:
        summary = persist_governed_artifacts(
            store,
            safety_artifacts,
            run_id="skill_import:safety_batch",
        )
        persist_summaries["safety"] = summary
        record_import_batch(
            imported=imported,
            imported_artifacts_by_file=imported_artifacts_by_file,
            normalized_out_by_file=normalized_out_by_file,
            artifacts=safety_artifacts,
            reports=list(summary.get("reports", [])),
            skill_files_for_artifacts=safety_skill_files,
            admissions=safety_admissions,
        )

    governance_persist_seconds = _elapsed_seconds(governance_persist_started)

    snapshot_started = time.perf_counter()
    governance_snapshot = installed_governance_snapshot(store)
    installed_policies = list(governance_snapshot["policies"])
    installed_approvals = list(governance_snapshot["approvals"])
    governance_snapshot_seconds = _elapsed_seconds(snapshot_started)

    admission_started = time.perf_counter()
    skill_artifacts: list[Any] = []
    skill_skill_files: list[Path] = []
    skill_admissions: list[dict[str, Any]] = []
    for skill_file, payload in skill_entries:
        artifact = compile_skill_document(payload, source_kind="portable_skill_document").artifact
        content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
        schema = normalize_skill_schema_version(content.get("skill_schema", "bssc_skill.v1"))
        admission: dict[str, Any] = {}
        if schema == SKILL_SCHEMA_VERSION_V2:
            admission = evaluate_skill_admission(
                artifact_skill_declaration(artifact),
                skill_title=artifact.title,
                kind=skill_kind_from_artifact(artifact),
                executor_framework=ability_executor_framework(
                    representation=runtime.enum_text(artifact.representation),
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
        skill_artifacts.append(artifact)
        skill_skill_files.append(skill_file)
        skill_admissions.append(admission)
    admission_seconds = _elapsed_seconds(admission_started)

    skill_persist_started = time.perf_counter()
    if skill_artifacts:
        summary = persist_governed_artifacts(
            store,
            skill_artifacts,
            run_id="skill_import:skill_batch",
        )
        persist_summaries["skill"] = summary
        record_import_batch(
            imported=imported,
            imported_artifacts_by_file=imported_artifacts_by_file,
            normalized_out_by_file=normalized_out_by_file,
            artifacts=skill_artifacts,
            reports=list(summary.get("reports", [])),
            skill_files_for_artifacts=skill_skill_files,
            admissions=skill_admissions,
        )
    skill_persist_seconds = _elapsed_seconds(skill_persist_started)

    normalized_export_started = time.perf_counter()
    for skill_file, artifacts in imported_artifacts_by_file.items():
        normalized_out_path = None
        if batch_mode and args.normalized_out_dir:
            normalized_out_path = args.normalized_out_dir / normalized_skill_bundle_filename_for_source(skill_file)
            normalized_out_path.write_text(export_skill_bundle_text(artifacts))
        elif not batch_mode and args.normalized_out:
            args.normalized_out.write_text(export_skill_bundle_text(artifacts))
            normalized_out_path = args.normalized_out
        normalized_out_by_file[skill_file] = normalized_out_path
    for item in imported:
        skill_file_path = Path(item["skill_file"])
        item["normalized_out"] = str(normalized_out_by_file.get(skill_file_path) or "")
    normalized_export_seconds = _elapsed_seconds(normalized_export_started)

    timings = {
        "load_payload_seconds": load_seconds,
        "classify_seconds": classify_seconds,
        "governance_persist_seconds": governance_persist_seconds,
        "governance_snapshot_seconds": governance_snapshot_seconds,
        "admission_seconds": admission_seconds,
        "skill_persist_seconds": skill_persist_seconds,
        "normalized_export_seconds": normalized_export_seconds,
        "total_seconds": _elapsed_seconds(total_started),
    }
    summary_payload = {
        "imported_count": len(imported),
        "imported": imported,
        "timings": timings,
        "governance_snapshot": {
            "policy_count": len(installed_policies),
            "approval_count": len(installed_approvals),
            "revocation_count": len(governance_snapshot["revocations"]),
            "incident_count": len(governance_snapshot["incidents"]),
            "timings": governance_snapshot.get("timings", {}),
        },
        "persist_summaries": {
            key: {
                "persisted_artifacts": int(value.get("persisted_artifacts", 0) or 0),
                "unchanged_artifacts": int(value.get("unchanged_artifacts", 0) or 0),
                "error_artifacts": int(value.get("error_artifacts", 0) or 0),
                "timings": value.get("timings", {}),
            }
            for key, value in persist_summaries.items()
        },
    }

    if batch_mode:
        print(json.dumps(summary_payload, indent=2, sort_keys=True))
        return 0

    item = imported[0]
    print(
        json.dumps(
            {
                "artifact_id": item["artifact_id"],
                "title": item["title"],
                "kind": item["kind"],
                "representation": item["representation"],
                "skill_file": item["skill_file"],
                "normalized_out": item["normalized_out"],
                "admission_status": item.get("admission_status", ""),
                "activation_status": item.get("activation_status", ""),
                "trust_status": item.get("trust_status", ""),
                "compiler_summary": item.get("compiler_summary", {}),
                "store_report": item["store_report"],
                "timings": timings,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0
