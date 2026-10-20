# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from applied_theory_types import Artifact
from approval_governance import artifact_is_approval_record
from skill_governance import artifact_is_policy_record
from skill_safety_governance import artifact_is_incident_record, artifact_is_revocation_record


def _elapsed_seconds(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)


def load_governance_inventory(store: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like repeated governed skill admission and runtime effect checks, helps with loading the installed governance records once and expressing them as one reusable snapshot.

    Reference to Theory:
        Supports open governance by separating policy, approval, revocation, and incident inventory loading from controller/runtime orchestration.

    Example Input Output:
        Input: `load_governance_inventory(store=artifact_store)`
        Output: {'policies': [Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], 'approvals': [], 'revocations': [], 'incidents': [], 'timings': {'load_seconds': 0.010421}}

    Args:
        store: Value for `store` used by `load_governance_inventory`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `load_governance_inventory`.
    """
    started_at = time.perf_counter()
    artifacts = store.load_all_artifacts()
    return {
        "artifacts": artifacts,
        "policies": [artifact for artifact in artifacts if artifact_is_policy_record(artifact)],
        "approvals": [artifact for artifact in artifacts if artifact_is_approval_record(artifact)],
        "revocations": [artifact for artifact in artifacts if artifact_is_revocation_record(artifact)],
        "incidents": [artifact for artifact in artifacts if artifact_is_incident_record(artifact)],
        "timings": {
            "load_seconds": _elapsed_seconds(started_at),
        },
    }


def controller_governance_snapshot(controller: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like controller or host-runtime governed use checks, helps with reusing one cached governance inventory snapshot until the store contents materially change.

    Reference to Theory:
        Supports open governance by keeping current-use evaluation tied to installed records without forcing repeated full-store scans inside one controller session.

    Example Input Output:
        Input: `controller_governance_snapshot(controller)`
        Output: {'policies': [Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], 'approvals': [], 'revocations': [], 'incidents': []}

    Args:
        controller: Value for `controller` used by `controller_governance_snapshot`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `controller_governance_snapshot`.
    """
    cached = getattr(controller, "_current_skill_governance_snapshot_cache", None)
    if isinstance(cached, Mapping) and cached:
        return dict(cached)
    snapshot = load_governance_inventory(controller.artifact_store)
    controller._current_skill_governance_snapshot_cache = snapshot
    return dict(snapshot)


def controller_governance_artifacts(controller: Any) -> tuple[list[Artifact], list[Artifact]]:
    """
    High Level Purpose:
        In circumstances like current-use executable or answer gating, helps with exposing the currently installed policy and approval artifacts from the cached governance inventory.

    Reference to Theory:
        Supports open governance by making current-use checks consume one shared inventory view instead of each caller scanning the store independently.

    Example Input Output:
        Input: `controller_governance_artifacts(controller)`
        Output: ([Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], [])

    Args:
        controller: Value for `controller` used by `controller_governance_artifacts`. Expected type: `Any`.

    Returns:
        tuple[list[Artifact], list[Artifact]]: Result produced by `controller_governance_artifacts`.
    """
    snapshot = controller_governance_snapshot(controller)
    return list(snapshot["policies"]), list(snapshot["approvals"])


def invalidate_controller_governance_snapshot(controller: Any) -> None:
    """
    High Level Purpose:
        In circumstances like persisting new governed artifacts during one controller session, helps with dropping the cached governance inventory so later checks see the updated store contents.

    Reference to Theory:
        Supports open governance by keeping cached current-use evaluation inputs aligned with the persisted registry of governed records.

    Example Input Output:
        Input: `invalidate_controller_governance_snapshot(controller)`
        Output: None

    Args:
        controller: Value for `controller` used by `invalidate_controller_governance_snapshot`. Expected type: `Any`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    controller._current_skill_governance_snapshot_cache = None
