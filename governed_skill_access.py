# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from applied_theory_types import Artifact
from realized_core_governance.approval import artifact_is_approval_record
from governance_inventory import controller_governance_snapshot
from realized_core_governance.lifecycle import artifact_effective_skill_lifecycle
from realized_core_governance.records import artifact_is_policy_record
from realized_skill_semantics.execution import (
    ability_executable_text,
    ability_executor_framework,
)
from skill_governance import (
    artifact_admitted_for_use_with_governance,
    artifact_current_use_admission,
    normalize_skill_kind,
)
from realized_core_governance.safety import governed_safety_lifecycle_overlay


def _artifact_kind_text(artifact: Artifact) -> str:
    return normalize_skill_kind(
        getattr(getattr(artifact, "artifact_type", None), "value", getattr(artifact, "artifact_type", "")),
        default="knowledge",
    )


def artifact_governed_use_state(owner: Any, artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like runtime invocation or controller-side artifact routing, helps with resolving one artifact's current governance context once and reusing that state across executable and answer-capability checks.

    Reference to Theory:
        Supports open governance by separating current-use admission, lifecycle overlay, and governance inventory access from controller and host-runtime orchestration.

    Example Input Output:
        Input: `artifact_governed_use_state(owner=controller, artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'admitted': True, 'admission_reason': '', 'policies': [Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], 'approvals': []}

    Args:
        owner: Value for `owner` used by `artifact_governed_use_state`. Expected type: `Any`.
        artifact: Value for `artifact` used by `artifact_governed_use_state`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_governed_use_state`.
    """
    snapshot = controller_governance_snapshot(owner)
    policies = list(snapshot["policies"])
    approvals = list(snapshot["approvals"])
    revocations = list(snapshot["revocations"])
    incidents = list(snapshot["incidents"])
    current_admission = artifact_current_use_admission(
        artifact,
        policy_artifacts=policies,
        approval_artifacts=approvals,
    )
    effective_lifecycle = artifact_effective_skill_lifecycle(
        artifact,
        current_admission_status=str(current_admission.get("status", "")),
    )
    effective_lifecycle.update(
        {
            key: value
            for key, value in governed_safety_lifecycle_overlay(
                skill_title=artifact.title,
                kind=_artifact_kind_text(artifact),
                revocation_artifacts=revocations,
                incident_artifacts=incidents,
            ).items()
            if key not in {"revocation_titles", "incident_titles"} and value not in (None, "", [], {})
        }
    )
    admitted, admission_reason = artifact_admitted_for_use_with_governance(
        artifact,
        policy_artifacts=policies,
        approval_artifacts=approvals,
        revocation_artifacts=revocations,
        incident_artifacts=incidents,
    )
    return {
        "snapshot": snapshot,
        "policies": policies,
        "approvals": approvals,
        "revocations": revocations,
        "incidents": incidents,
        "admission": current_admission,
        "lifecycle": effective_lifecycle,
        "admitted": admitted,
        "admission_reason": admission_reason,
    }


def _artifact_is_executable_with_state(owner: Any, artifact: Artifact, *, use_state: Mapping[str, Any]) -> bool:
    if not bool(use_state.get("admitted")):
        return False
    if int(artifact.function_bit or 0) != 1:
        return False
    content = owner.artifact_runtime_content(artifact)
    framework = ability_executor_framework(
        representation=str(artifact.representation),
        content=content,
    )
    if framework and framework not in owner.supported_executor_frameworks():
        return False
    return bool(
        ability_executable_text(
            representation=str(artifact.representation),
            content=content,
        )
    )


def artifact_is_governed_executable(owner: Any, artifact: Artifact) -> bool:
    """
    High Level Purpose:
        In circumstances like controller-side routing and direct reusable ability selection, helps with deciding whether one artifact is currently executable under installed governance and supported executor settings.

    Reference to Theory:
        Supports open governance by making executable routing depend on current admission and authority state instead of only on artifact shape.

    Example Input Output:
        Input: `artifact_is_governed_executable(owner=controller, artifact=Artifact(id='artifact-force', title='Force From Mass And Acceleration', artifact_type='ability', representation='python_script'))`
        Output: True

    Args:
        owner: Value for `owner` used by `artifact_is_governed_executable`. Expected type: `Any`.
        artifact: Value for `artifact` used by `artifact_is_governed_executable`. Expected type: `Artifact`.

    Returns:
        bool: Result produced by `artifact_is_governed_executable`.
    """
    return _artifact_is_executable_with_state(
        owner,
        artifact,
        use_state=artifact_governed_use_state(owner, artifact),
    )


def artifact_has_governed_answer_capability(
    owner: Any,
    artifact: Artifact,
    *,
    semantic_unit: str = "",
) -> bool:
    """
    High Level Purpose:
        In circumstances like direct answer reuse and semantic support ranking, helps with checking whether one artifact can currently yield a usable answer surface under the installed governance state.

    Reference to Theory:
        Supports open governance by ensuring current-use answer capability follows current admission, revocation, and incident state rather than only stale import-time metadata.

    Example Input Output:
        Input: `artifact_has_governed_answer_capability(owner=controller, artifact=Artifact(id='artifact-add', title='math:add:add(A, B, C) :- C is A + B', artifact_type='knowledge', representation='yaml'), semantic_unit='math:add:add(2, X, Y)')`
        Output: True

    Args:
        owner: Value for `owner` used by `artifact_has_governed_answer_capability`. Expected type: `Any`.
        artifact: Value for `artifact` used by `artifact_has_governed_answer_capability`. Expected type: `Artifact`.
        semantic_unit: Value for `semantic_unit` used by `artifact_has_governed_answer_capability`. Expected type: `str`. Defaults to `''`.

    Returns:
        bool: Result produced by `artifact_has_governed_answer_capability`.
    """
    use_state = artifact_governed_use_state(owner, artifact)
    if (
        not bool(use_state.get("admitted"))
        or artifact_is_policy_record(artifact)
        or artifact_is_approval_record(artifact)
    ):
        return False
    content = owner.artifact_runtime_content(artifact)
    effective_semantic_unit = owner.artifact_query_semantic_unit(
        artifact,
        semantic_unit=semantic_unit,
    )
    if str(content.get("answer", "")).strip():
        return True
    if owner.artifact_prolog_clause_answer(artifact, semantic_unit=effective_semantic_unit):
        return True
    if owner.artifact_latent_knowledge_answer_text(
        artifact,
        semantic_unit=effective_semantic_unit or semantic_unit,
    ):
        return True
    return _artifact_is_executable_with_state(owner, artifact, use_state=use_state)
