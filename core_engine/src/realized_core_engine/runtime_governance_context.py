# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.applied_model import Artifact
from realized_core_runtime.capabilities import runtime_skill_declaration_for_artifact
from realized_core_engine.governed_skill_access import artifact_governed_use_state
from realized_core_governance.authority import (
    evaluate_authority_grants as evaluate_runtime_authority_grants,
)
from realized_core_governance.lifecycle import artifact_effective_skill_lifecycle
from realized_core_governance.records import artifact_skill_admission
from realized_core_governance.trace import (
    EFFECT_TRACE_RECEIPT_SCHEMA_VERSION,
    effect_trace_receipt as runtime_effect_trace_receipt,
)


def runtime_artifact_governance_context(owner: Any, artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like runtime host mediation or alternate-runtime execution, helps with resolving one artifact's current governance context through one narrow facade instead of making callers stitch together declaration, admission, and lifecycle state themselves.

    Reference to Theory:
        Supports the runtime layer boundary by keeping current-use governance resolution behind a runtime-facing service surface rather than spreading low-level governance calls across mediation code.

    Example Input Output:
        Input: `runtime_artifact_governance_context(owner=controller, artifact=Artifact(id='artifact-browser', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'declaration': {'authorities_requested': ['execute']}, 'admission': {'status': 'admitted'}, 'lifecycle': {'activation_status': 'active'}, 'admitted': True, 'admission_reason': ''}

    Args:
        owner: Value for `owner` used by `runtime_artifact_governance_context`. Expected type: `Any`.
        artifact: Value for `artifact` used by `runtime_artifact_governance_context`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `runtime_artifact_governance_context`.
    """
    use_state = artifact_governed_use_state(owner, artifact)
    return {
        "declaration": runtime_skill_declaration_for_artifact(artifact),
        "admission": dict(use_state.get("admission", {})) if isinstance(use_state.get("admission", {}), Mapping) else {},
        "lifecycle": dict(use_state.get("lifecycle", {})) if isinstance(use_state.get("lifecycle", {}), Mapping) else {},
        "admitted": bool(use_state.get("admitted")),
        "admission_reason": str(use_state.get("admission_reason", "")),
    }


def runtime_artifact_trace_context(
    artifact: Artifact,
    *,
    admission_snapshot: Mapping[str, Any] | None = None,
    lifecycle_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like effect-trace recording, helps with deriving the declaration, admission, and lifecycle snapshots that should be attached to one governed runtime effect trace.

    Reference to Theory:
        Supports constitutional tracing by keeping runtime trace snapshots behind one small governance facade instead of letting runtime code reach into several low-level governance modules.

    Example Input Output:
        Input: `runtime_artifact_trace_context(artifact=Artifact(id='artifact-force', title='Force', artifact_type='ability', representation='python_script'))`
        Output: {'declaration': {'authorities_requested': ['execute']}, 'admission': {'status': 'admitted'}, 'lifecycle': {'activation_status': 'active'}}

    Args:
        artifact: Value for `artifact` used by `runtime_artifact_trace_context`. Expected type: `Artifact`.
        admission_snapshot: Value for `admission_snapshot` used by `runtime_artifact_trace_context`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        lifecycle_snapshot: Value for `lifecycle_snapshot` used by `runtime_artifact_trace_context`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `runtime_artifact_trace_context`.
    """
    admission = (
        dict(admission_snapshot)
        if isinstance(admission_snapshot, Mapping)
        else artifact_skill_admission(artifact)
    )
    lifecycle = (
        dict(lifecycle_snapshot)
        if isinstance(lifecycle_snapshot, Mapping)
        else artifact_effective_skill_lifecycle(
            artifact,
            current_admission_status=str(admission.get("status", "")),
        )
    )
    return {
        "declaration": runtime_skill_declaration_for_artifact(artifact),
        "admission": dict(admission) if isinstance(admission, Mapping) else {},
        "lifecycle": dict(lifecycle) if isinstance(lifecycle, Mapping) else {},
    }
