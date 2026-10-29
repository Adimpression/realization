# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from typing import Any

from realized_core_semantics.applied_model import Artifact
from realized_core_engine.governance_inventory import (
    controller_governance_artifacts,
    controller_governance_snapshot,
    invalidate_controller_governance_snapshot,
)
from realized_core_engine.governed_skill_access import (
    artifact_has_governed_answer_capability,
    artifact_is_governed_executable,
)


def current_skill_governance_artifacts(self: Any) -> tuple[list[Artifact], list[Artifact]]:
    """
    High Level Purpose:
        In circumstances like controller-side routing and invocation-time governed use checks, helps with exposing the currently installed policy and approval artifacts through one controller/governance bridge instead of loading them inline inside the controller file.

    Reference to Theory:
        Supports open governance layering by keeping the controller dependent on a narrow governance-access bridge rather than on direct policy inventory mechanics.

    Example Input Output:
        Input: `current_skill_governance_artifacts(self=controller)`
        Output: ([Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], [])

    Args:
        self: Bound controller instance that owns the artifact store and governance cache used by this method.

    Returns:
        tuple[list[Artifact], list[Artifact]]: Result produced by `current_skill_governance_artifacts`.
    """
    return controller_governance_artifacts(self)


def current_skill_governance_snapshot(self: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like repeated controller or runtime current-use checks during one session, helps with exposing the cached governance inventory through one bridge method rather than forcing callers to know how governance inventory is loaded.

    Reference to Theory:
        Supports open governance layering by keeping controller and runtime access to current policy, approval, revocation, and incident records behind one shared facade.

    Example Input Output:
        Input: `current_skill_governance_snapshot(self=controller)`
        Output: {'policies': [Artifact(id='artifact-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml')], 'approvals': [], 'revocations': [], 'incidents': []}

    Args:
        self: Bound controller instance that owns the artifact store and governance cache used by this method.

    Returns:
        dict[str, Any]: Result produced by `current_skill_governance_snapshot`.
    """
    return controller_governance_snapshot(self)


def invalidate_current_skill_governance_snapshot(self: Any) -> None:
    """
    High Level Purpose:
        In circumstances like persisting new governed artifacts during one controller session, helps with invalidating the cached governance inventory through one bridge method so later use checks see updated records.

    Reference to Theory:
        Supports open governance layering by keeping governance-cache invalidation out of the controller file while preserving the controller-level API surface that other runtime modules already call.

    Example Input Output:
        Input: `invalidate_current_skill_governance_snapshot(self=controller)`
        Output: None

    Args:
        self: Bound controller instance that owns the governance cache used by this method.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    invalidate_controller_governance_snapshot(self)


def artifact_is_executable_function(self: Any, artifact: Artifact) -> bool:
    """
    High Level Purpose:
        In circumstances like controller-side reuse selection and executable ability routing, helps with deciding whether one artifact is currently executable under the installed governance state and supported executor set.

    Reference to Theory:
        Supports open governance layering by keeping executable gating behind one controller/governance bridge instead of embedding current-use admission logic directly in the controller file.

    Example Input Output:
        Input: `artifact_is_executable_function(self=controller, artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'))`
        Output: True

    Args:
        self: Bound controller instance that owns runtime content normalization and supported executor configuration.
        artifact: Value for `artifact` used by `artifact_is_executable_function`. Expected type: `Artifact`.

    Returns:
        bool: Result produced by `artifact_is_executable_function`.
    """
    return artifact_is_governed_executable(self, artifact)


def artifact_has_answer_capability(
    self: Any,
    artifact: Artifact,
    *,
    semantic_unit: str = "",
) -> bool:
    """
    High Level Purpose:
        In circumstances like direct answer reuse, ranking, and support selection, helps with deciding whether one artifact can currently produce a usable answer surface under the installed governance state.

    Reference to Theory:
        Supports open governance layering by keeping answer-capability gating behind one controller/governance bridge instead of embedding current-use admission mechanics directly in the controller file.

    Example Input Output:
        Input: `artifact_has_answer_capability(self=controller, artifact=Artifact(id='artifact-add', title='math:add:add(A, B, C) :- C is A + B', artifact_type='knowledge', representation='yaml'), semantic_unit='math:add:add(2, X, Y)')`
        Output: True

    Args:
        self: Bound controller instance that owns runtime content normalization and answer-surface helpers.
        artifact: Value for `artifact` used by `artifact_has_answer_capability`. Expected type: `Artifact`.
        semantic_unit: Value for `semantic_unit` used by `artifact_has_answer_capability`. Expected type: `str`. Defaults to `''`.

    Returns:
        bool: Result produced by `artifact_has_answer_capability`.
    """
    return artifact_has_governed_answer_capability(
        self,
        artifact,
        semantic_unit=semantic_unit,
    )
