# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from governance_inventory import load_governance_inventory
from semantic_text import collapse_ws
from skill_schema_io import artifact_from_skill_document


WORKSTATION_DEFAULT_POLICY_TITLE = "Workstation Skill Home Policy"
_WORKSTATION_TRANSIENT_BUNDLE_POLICY_PREFIX = "Local Bundle Admission Policy / "


def workstation_default_policy_payload() -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill-home import and invocation, helps with defining the durable default admission policy that should govern workers installed into one shared workstation skill home.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by keeping shared worker governance local to the workstation substrate instead of inheriting every bundle-local installation policy forever.

    Example Input Output:
        Input: `workstation_default_policy_payload()`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'policy', 'title': 'Workstation Skill Home Policy', 'policy': {'allowed_executors': ['python3', 'bash', 'ansible', 'wasm_wasi']}}

    Args:
        None.

    Returns:
        dict[str, Any]: Result produced by `workstation_default_policy_payload`.
    """
    return {
        "schema": "bssc_skill.v2",
        "kind": "policy",
        "title": WORKSTATION_DEFAULT_POLICY_TITLE,
        "policy": {
            "intent": "Admit governed workers installed into the workstation skill home.",
            "target_kinds": ["knowledge", "ability"],
            "max_risk_tier": "tier3_sensitive",
            "allowed_authorities": ["read", "write", "execute", "communicate"],
            "denied_authorities": [],
            "allowed_executors": ["python3", "bash", "ansible", "wasm_wasi"],
            "required_approval_for_risk_tiers": {},
        },
    }


def workstation_default_policy_artifact() -> Any:
    """
    High Level Purpose:
        In circumstances like workstation-specific governance snapshot construction, helps with materializing the workstation default policy as one ordinary policy artifact.

    Reference to Theory:
        Supports workstation governance reuse by expressing the default skill-home policy through the same artifact substrate used elsewhere in the system.

    Example Input Output:
        Input: `workstation_default_policy_artifact()`
        Output: Artifact(id='artifact-policy-...', title='Workstation Skill Home Policy', artifact_type='policy_record')

    Args:
        None.

    Returns:
        Any: Result produced by `workstation_default_policy_artifact`.
    """
    return artifact_from_skill_document(workstation_default_policy_payload())


def workstation_is_transient_bundle_policy_payload(payload: Mapping[str, Any]) -> bool:
    """
    High Level Purpose:
        In circumstances like workstation-side bundle import, helps with identifying the synthetic local bundle policy that fresh-system exports prepend for installation but that should not become a permanent shared workstation policy.

    Reference to Theory:
        Supports workstation skill-home hygiene by distinguishing installation-time policy scaffolding from durable workstation governance.

    Example Input Output:
        Input: `workstation_is_transient_bundle_policy_payload({'kind': 'policy', 'title': 'Local Bundle Admission Policy / abc123'})`
        Output: True

    Args:
        payload: Value for `payload` used by `workstation_is_transient_bundle_policy_payload`. Expected type: `Mapping[str, Any]`.

    Returns:
        bool: Result produced by `workstation_is_transient_bundle_policy_payload`.
    """
    kind = collapse_ws(str(payload.get("kind", ""))).lower()
    title = collapse_ws(str(payload.get("title", "")))
    return kind == "policy" and title.startswith(_WORKSTATION_TRANSIENT_BUNDLE_POLICY_PREFIX)


def workstation_is_transient_bundle_policy_artifact(artifact: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like workstation runtime governance loading, helps with identifying stored bundle-local policy artifacts that should be ignored in favor of the workstation skill-home policy.

    Reference to Theory:
        Supports the workstation shell by preventing per-bundle installation policies from contaminating shared worker admission decisions.

    Example Input Output:
        Input: `workstation_is_transient_bundle_policy_artifact(artifact=3)`
        Output: True

    Args:
        artifact: Value for `artifact` used by `workstation_is_transient_bundle_policy_artifact`. Expected type: `Any`.

    Returns:
        bool: Result produced by `workstation_is_transient_bundle_policy_artifact`.
    """
    title = collapse_ws(str(getattr(artifact, "title", "")))
    return title.startswith(_WORKSTATION_TRANSIENT_BUNDLE_POLICY_PREFIX)


def workstation_governance_inventory(store: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation worker import and invocation, helps with loading a governance snapshot that keeps durable workstation policy while filtering out transient bundle-local policy artifacts.

    Reference to Theory:
        Supports workstation compatibility with many imported trial bundles by evaluating workers against the workstation skill-home policy rather than the accidental intersection of all bundle-local export policies.

    Example Input Output:
        Input: `workstation_governance_inventory(store=3)`
        Output: {'policies': [Artifact(title='Workstation Skill Home Policy')], 'approvals': [], 'revocations': [], 'incidents': [], 'artifacts': []}

    Args:
        store: Value for `store` used by `workstation_governance_inventory`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `workstation_governance_inventory`.
    """
    inventory = load_governance_inventory(store)
    filtered_policies = [
        artifact
        for artifact in inventory.get("policies", [])
        if not workstation_is_transient_bundle_policy_artifact(artifact)
    ]
    if not any(collapse_ws(str(getattr(artifact, "title", ""))) == WORKSTATION_DEFAULT_POLICY_TITLE for artifact in filtered_policies):
        filtered_policies.insert(0, workstation_default_policy_artifact())
    return {
        **inventory,
        "policies": filtered_policies,
    }


def ensure_workstation_skill_home_policy(store: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill-home initialization, helps with persisting the durable workstation default policy into the shared store when it is missing.

    Reference to Theory:
        Supports outside-the-session usability of the workstation skill home by ensuring the default workstation policy exists as a real stored governance artifact, not only as an in-memory fallback.

    Example Input Output:
        Input: `ensure_workstation_skill_home_policy(store=3)`
        Output: {'status': 'ok', 'created': True, 'title': 'Workstation Skill Home Policy'}

    Args:
        store: Value for `store` used by `ensure_workstation_skill_home_policy`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `ensure_workstation_skill_home_policy`.
    """
    inventory = load_governance_inventory(store)
    if any(collapse_ws(str(getattr(artifact, "title", ""))) == WORKSTATION_DEFAULT_POLICY_TITLE for artifact in inventory.get("policies", [])):
        return {
            "status": "ok",
            "created": False,
            "title": WORKSTATION_DEFAULT_POLICY_TITLE,
        }
    artifact = workstation_default_policy_artifact()
    summary = store.persist_artifacts([artifact], run_id="workstation_skill_home:default_policy")
    return {
        "status": "ok",
        "created": True,
        "title": WORKSTATION_DEFAULT_POLICY_TITLE,
        "persist_summary": summary,
    }
