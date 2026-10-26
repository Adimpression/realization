# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from applied_theory_types import Artifact
from realized_core_governance.inventory import load_governance_inventory


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
