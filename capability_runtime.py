# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from applied_theory_types import Artifact, json_safe, utc_now
from host_abi import known_host_broker_names, required_authority_for_host_broker
from realized_core_governance.records import (
    artifact_is_policy_record,
    artifact_skill_admission,
    artifact_skill_declaration,
)
from realized_skill_semantics.execution import normalize_executor_framework_name
from semantic_text import collapse_ws
from skill_governance import (
    normalize_skill_kind,
    synthesized_skill_declaration_for_artifact,
)

EFFECT_KIND_REQUIRED_AUTHORITIES = {
    "execute.python3": "execute",
    "execute.bash": "execute",
    "execute.ansible": "execute",
    "execute.wasm_wasi": "execute",
    "net.http": "communicate",
    "skill.invoke": "invoke",
    "tool.invoke": "execute",
    **{
        broker_name: required_authority_for_host_broker(broker_name)
        for broker_name in known_host_broker_names()
    },
}


@dataclass
class CapabilityGrant:
    id: str
    artifact_id: str
    artifact_title: str
    skill_kind: str
    authority: str
    scope: str
    target: str
    context: str
    duration: str
    triggering_conditions: list[str] = field(default_factory=list)
    approval_class: str = "automatic"
    risk_tier: str = "tier1_bounded_transform"
    executor_framework: str = ""
    effect_kind: str = ""
    semantic_unit: str = ""
    data_classes_touched: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    policy_titles: list[str] = field(default_factory=list)
    admission_status: str = "legacy_implicit_admit"
    issued_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like runtime host mediation before skill execution, helps with turning one issued capability grant into durable dictionary form for trace and replay surfaces.

        Reference to Theory:
            Supports bundle-style host governance by making invocation-time authority grants explicit instead of leaving execution rights implicit inside the skill body.

        Example Input Output:
            Input: `to_dict()`
            Output: {'id': 'grant-abc123', 'artifact_id': 'artifact-force-function', 'authority': 'execute', 'effect_kind': 'execute.python3'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


def required_authority_for_effect_kind(effect_kind: str) -> str:
    """
    High Level Purpose:
        In circumstances like mediated runtime execution and future brokered host effects, helps with mapping an effect kind such as `execute.python3` to the authority that must have been granted first.

    Reference to Theory:
        Supports open governance by separating requested authority from concrete effect realization at runtime.

    Example Input Output:
        Input: `required_authority_for_effect_kind(effect_kind='execute.bash')`
        Output: 'execute'

    Args:
        effect_kind: Value for `effect_kind` used by `required_authority_for_effect_kind`. Expected type: `str`.

    Returns:
        str: Result produced by `required_authority_for_effect_kind`.
    """
    normalized = collapse_ws(str(effect_kind))
    return EFFECT_KIND_REQUIRED_AUTHORITIES.get(normalized, "")


def runtime_skill_declaration_for_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like runtime effect mediation for both legacy artifacts and governed v2 skills, helps with recovering one usable declaration surface for grant issuance.

    Reference to Theory:
        Supports the bridge from current artifact execution to declaration-first governance by synthesizing conservative declarations for older artifacts when needed.

    Example Input Output:
        Input: `runtime_skill_declaration_for_artifact(artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'))`
        Output: {'intent': 'Execute the skill described by Force from mass and acceleration.', 'authorities_requested': ['execute'], 'risk_tier': 'tier1_bounded_transform'}

    Args:
        artifact: Value for `artifact` used by `runtime_skill_declaration_for_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `runtime_skill_declaration_for_artifact`.
    """
    if artifact_is_policy_record(artifact):
        return {}
    declared = artifact_skill_declaration(artifact)
    if declared:
        return dict(declared)
    return synthesized_skill_declaration_for_artifact(artifact)


def _capability_grant_id(
    *,
    artifact_id: str,
    authority: str,
    effect_kind: str,
    issued_at: str,
) -> str:
    """
    High Level Purpose:
        In circumstances like runtime issuance of capability grants for one invocation, helps with deriving a stable short identifier for the grant record without needing a separate global counter.

    Reference to Theory:
        Supports governed replay and traceability by giving each issued grant a durable identity rooted in the invocation context.

    Example Input Output:
        Input: `_capability_grant_id(artifact_id='artifact-force-function', authority='execute', effect_kind='execute.python3', issued_at='2026-03-31T12:00:00+00:00')`
        Output: 'grant-1f2e3d4c5b6a'

    Args:
        artifact_id: Value for `artifact_id` used by `_capability_grant_id`. Expected type: `str`.
        authority: Value for `authority` used by `_capability_grant_id`. Expected type: `str`.
        effect_kind: Value for `effect_kind` used by `_capability_grant_id`. Expected type: `str`.
        issued_at: Value for `issued_at` used by `_capability_grant_id`. Expected type: `str`.

    Returns:
        str: Result produced by `_capability_grant_id`.
    """
    digest = hashlib.sha1(
        f"{artifact_id}|{authority}|{effect_kind}|{issued_at}".encode("utf-8")
    ).hexdigest()
    return f"grant-{digest[:12]}"


def issue_capability_grants_for_artifact(
    artifact: Artifact,
    *,
    effect_kind: str,
    executor_framework: str = "",
    semantic_unit: str = "",
    admission_snapshot: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like runtime host mediation for executable skills, helps with turning the artifact declaration into explicit per-invocation capability grants that can be checked and traced before effect.

    Reference to Theory:
        Supports open governance and the bundle host model by deriving concrete runtime grants from declared authorities and bounds rather than treating admission alone as sufficient execution permission.

    Example Input Output:
        Input: `issue_capability_grants_for_artifact(artifact=Artifact(id='artifact-force-function', title='Force from mass and acceleration', artifact_type='ability', representation='python_script'), effect_kind='execute.python3', executor_framework='python3', semantic_unit='Calculate force from mass=3 and acceleration=4.')`
        Output: [{'id': 'grant-1f2e3d4c5b6a', 'artifact_id': 'artifact-force-function', 'authority': 'execute', 'effect_kind': 'execute.python3'}]

    Args:
        artifact: Value for `artifact` used by `issue_capability_grants_for_artifact`. Expected type: `Artifact`.
        effect_kind: Value for `effect_kind` used by `issue_capability_grants_for_artifact`. Expected type: `str`.
        executor_framework: Value for `executor_framework` used by `issue_capability_grants_for_artifact`. Expected type: `str`. Defaults to `''`.
        semantic_unit: Value for `semantic_unit` used by `issue_capability_grants_for_artifact`. Expected type: `str`. Defaults to `''`.
        admission_snapshot: Value for `admission_snapshot` used by `issue_capability_grants_for_artifact`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        list[dict[str, Any]]: Result produced by `issue_capability_grants_for_artifact`.
    """
    declaration = runtime_skill_declaration_for_artifact(artifact)
    if not declaration:
        return []
    admission = (
        dict(admission_snapshot)
        if isinstance(admission_snapshot, Mapping)
        else artifact_skill_admission(artifact)
    )
    authority_bounds = (
        dict(declaration.get("authority_bounds", {}))
        if isinstance(declaration.get("authority_bounds", {}), Mapping)
        else {}
    )
    issued_at = utc_now()
    normalized_executor = normalize_executor_framework_name(
        executor_framework or declaration.get("executor_framework", "")
    )
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    skill_kind = normalize_skill_kind(
        content.get("skill_kind", ""),
        default=str(getattr(artifact.artifact_type, "value", artifact.artifact_type)),
    )
    policy_titles = [
        collapse_ws(str(item))
        for item in admission.get("policy_titles", [])
        if collapse_ws(str(item))
    ] if isinstance(admission, Mapping) else []
    grants: list[dict[str, Any]] = []
    for authority in declaration.get("authorities_requested", []):
        bounds = dict(authority_bounds.get(authority, {})) if isinstance(authority_bounds.get(authority, {}), Mapping) else {}
        grant = CapabilityGrant(
            id=_capability_grant_id(
                artifact_id=str(getattr(artifact, "id", "")),
                authority=str(authority),
                effect_kind=effect_kind,
                issued_at=issued_at,
            ),
            artifact_id=str(getattr(artifact, "id", "")),
            artifact_title=collapse_ws(str(getattr(artifact, "title", ""))),
            skill_kind=skill_kind,
            authority=collapse_ws(str(authority)),
            scope=collapse_ws(str(bounds.get("scope", ""))),
            target=collapse_ws(str(bounds.get("target", ""))),
            context=collapse_ws(str(bounds.get("context", ""))),
            duration=collapse_ws(str(bounds.get("duration", ""))),
            triggering_conditions=[
                collapse_ws(str(item))
                for item in bounds.get("triggering_conditions", [])
                if collapse_ws(str(item))
            ] if isinstance(bounds.get("triggering_conditions", []), list) else [],
            approval_class=collapse_ws(str(bounds.get("approval_class", "automatic"))),
            risk_tier=collapse_ws(str(declaration.get("risk_tier", "tier1_bounded_transform"))),
            executor_framework=normalized_executor,
            effect_kind=collapse_ws(str(effect_kind)),
            semantic_unit=collapse_ws(str(semantic_unit)),
            data_classes_touched=[
                collapse_ws(str(item))
                for item in declaration.get("data_classes_touched", [])
                if collapse_ws(str(item))
            ] if isinstance(declaration.get("data_classes_touched", []), list) else [],
            side_effects=[
                collapse_ws(str(item))
                for item in declaration.get("side_effects", [])
                if collapse_ws(str(item))
            ] if isinstance(declaration.get("side_effects", []), list) else [],
            policy_titles=policy_titles,
            admission_status=collapse_ws(str(admission.get("status", "legacy_implicit_admit")))
            if isinstance(admission, Mapping)
            else "legacy_implicit_admit",
            issued_at=issued_at,
        )
        grants.append(grant.to_dict())
    return grants
