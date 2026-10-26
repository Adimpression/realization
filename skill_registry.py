# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from applied_theory_types import Artifact, enum_text, utc_now
from artifact import yaml_dump_human
from host_abi import host_abi_version
from realized_core_governance.lifecycle import artifact_skill_lifecycle
from realized_core_governance.records import artifact_skill_admission
from skill_compiler import compiled_skill_summary_from_artifact
from skill_ir import canonical_skill_ir_from_artifact
from skill_export_projection import skill_export_document
from realized_core_governance.safety import (
    artifact_is_incident_record,
    artifact_is_revocation_record,
    governed_safety_lifecycle_overlay,
)
from store import build_artifact_store


SKILL_REGISTRY_SCHEMA_VERSION = "bssc_skill_registry.v1"


def _canonical_digest(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def skill_registry_entry(
    artifact: Artifact,
    *,
    revocation_artifacts: list[Artifact] | None = None,
    incident_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    exported = skill_export_document(artifact)
    canonical_ir = canonical_skill_ir_from_artifact(artifact)
    compiler_summary = compiled_skill_summary_from_artifact(artifact)
    kind = str(exported.get("kind", "")).strip() or enum_text(artifact.artifact_type)
    admission = artifact_skill_admission(artifact)
    lifecycle = artifact_skill_lifecycle(artifact)
    overlay = governed_safety_lifecycle_overlay(
        skill_title=artifact.title,
        kind=kind,
        revocation_artifacts=revocation_artifacts,
        incident_artifacts=incident_artifacts,
    )
    effective_lifecycle = dict(lifecycle)
    effective_lifecycle.update(
        {
            key: value
            for key, value in overlay.items()
            if key not in {"revocation_titles", "incident_titles"} and value not in (None, "", [], {})
        }
    )
    governance = dict(exported.get("governance", {})) if isinstance(exported.get("governance", {}), dict) else {}
    return {
        "artifact_id": artifact.id,
        "title": artifact.title,
        "kind": kind,
        "schema": str(exported.get("schema", "")).strip(),
        "representation": enum_text(artifact.representation),
        "executor": str(exported.get("executor", "")).strip(),
        "entrypoint": str(exported.get("entrypoint", "")).strip(),
        "admission_status": str(admission.get("status", "")).strip(),
        "activation_status": str(effective_lifecycle.get("activation_status", "")).strip(),
        "trust_status": str(effective_lifecycle.get("trust_status", "")).strip(),
        "quarantine_status": str(effective_lifecycle.get("quarantine_status", "")).strip(),
        "policy_titles": list(admission.get("policy_titles", [])) if isinstance(admission.get("policy_titles", []), list) else [],
        "approval_titles": list(admission.get("approval_titles", [])) if isinstance(admission.get("approval_titles", []), list) else [],
        "revocation_titles": list(overlay.get("revocation_titles", [])) if isinstance(overlay.get("revocation_titles", []), list) else [],
        "incident_titles": list(overlay.get("incident_titles", [])) if isinstance(overlay.get("incident_titles", []), list) else [],
        "host_abi_version": str(governance.get("host_abi_version", "")).strip() or host_abi_version(),
        "family": dict(compiler_summary.get("family", {})) if isinstance(compiler_summary.get("family", {}), dict) else {},
        "alias_count": int(compiler_summary.get("alias_count", 0) or 0),
        "compatibility_formats": list(compiler_summary.get("compatibility_formats", []))
        if isinstance(compiler_summary.get("compatibility_formats", []), list)
        else [],
        "normalized_regions": list(compiler_summary.get("normalized_regions", []))
        if isinstance(compiler_summary.get("normalized_regions", []), list)
        else [],
        "normalization_leaf_counts": dict(compiler_summary.get("normalization_leaf_counts", {}))
        if isinstance(compiler_summary.get("normalization_leaf_counts", {}), dict)
        else {},
        "hosting_metadata": dict(canonical_ir.hosting_metadata),
        "export_digest": _canonical_digest(exported),
    }


def skill_registry_document(artifacts: Iterable[Artifact]) -> dict[str, Any]:
    artifact_list = list(artifacts)
    revocations = [artifact for artifact in artifact_list if artifact_is_revocation_record(artifact)]
    incidents = [artifact for artifact in artifact_list if artifact_is_incident_record(artifact)]
    entries = [
        skill_registry_entry(
            artifact,
            revocation_artifacts=revocations,
            incident_artifacts=incidents,
        )
        for artifact in artifact_list
    ]
    return {
        "schema": SKILL_REGISTRY_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "host_abi_version": host_abi_version(),
        "entry_count": len(entries),
        "entries": entries,
    }


def export_skill_registry_text(artifacts: Iterable[Artifact]) -> str:
    return yaml_dump_human(skill_registry_document(artifacts)) + "\n"


def handle_export_skill_registry_command(args: argparse.Namespace) -> int:
    store = build_artifact_store()
    payload = export_skill_registry_text(store.load_all_artifacts())
    out_path = Path(args.out) if getattr(args, "out", None) else None
    if out_path is not None:
        out_path.write_text(payload)
    else:
        print(payload, end="")
    return 0
