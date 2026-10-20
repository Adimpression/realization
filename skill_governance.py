# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from applied_theory_types import Artifact, utc_now
from execution_framework_primitives import ability_executor_framework, normalize_executor_framework_name
from host_abi import host_broker_stability, known_host_broker_names, required_authority_for_host_broker
from python_skill_brokerization import python_skill_data_surface_assessment
from semantic_text import collapse_ws
from skill_lifecycle import artifact_effective_skill_lifecycle, artifact_skill_lifecycle, skill_lifecycle_allows_invocation
from skill_governance_primitives import (
    SKILL_APPROVAL_CLASSES,
    SKILL_AUTHORITIES,
    SKILL_KIND_CHOICES,
    SKILL_RISK_TIERS,
    normalize_skill_approval_class as _normalize_skill_approval_class,
    normalize_skill_authorities as _normalize_skill_authorities,
    normalize_skill_kind as _normalize_skill_kind,
    normalize_skill_risk_tier as _normalize_skill_risk_tier,
)
from skill_safety_governance import (
    artifact_is_incident_record,
    artifact_is_revocation_record,
    governed_safety_lifecycle_overlay,
)
from virtual_mounts import default_virtual_mount_table

SKILL_SCHEMA_VERSION_V1 = "bssc_skill.v1"
SKILL_SCHEMA_VERSION_V2 = "bssc_skill.v2"
SKILL_SCHEMA_VERSIONS = {SKILL_SCHEMA_VERSION_V1, SKILL_SCHEMA_VERSION_V2}

SKILL_DECLARATION_REQUIRED_FIELDS = (
    "intent",
    "inputs",
    "outputs",
    "authorities_requested",
    "data_classes_touched",
    "side_effects",
    "persistence_behavior",
    "invocation_rights",
    "composition_rights",
    "escalation_rights",
    "approval_requirements",
    "risk_tier",
)
SKILL_AUTHORITY_BOUND_FIELDS = (
    "scope",
    "target",
    "context",
    "duration",
    "triggering_conditions",
    "approval_class",
)

_RISK_INDEX = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}
_APPROVAL_INDEX = {level: index for index, level in enumerate(SKILL_APPROVAL_CLASSES)}
_DECLARATION_COLLECTION_FIELDS = {
    "inputs",
    "outputs",
    "authorities_requested",
    "data_classes_touched",
    "side_effects",
    "invocation_rights",
    "composition_rights",
    "escalation_rights",
    "approval_requirements",
}


def _governed_broker_hints_from_content(content: Mapping[str, Any]) -> list[str]:
    explicit = _string_list(content.get("governed_host_brokers", []))
    if explicit:
        return explicit
    broker_source = "\n".join(
        str(content.get(key, ""))
        for key in ("python_script", "shell_script", "ansible_playbook", "wasm_module")
        if collapse_ws(str(content.get(key, "")))
    )
    discovered: list[str] = []
    for broker_name in known_host_broker_names():
        if broker_name in broker_source:
            discovered.append(broker_name)
    return discovered


def _governed_mount_names_from_content(content: Mapping[str, Any]) -> list[str]:
    explicit_mounts = dict(content.get("virtual_mounts", {})) if isinstance(content.get("virtual_mounts", {}), Mapping) else {}
    discovered: list[str] = []
    for mount_name in explicit_mounts:
        name = collapse_ws(str(mount_name))
        if name and name not in discovered:
            discovered.append(name)
    broker_source = "\n".join(
        collapse_ws(str(content.get(key, "")))
        for key in ("python_script", "shell_script", "ansible_playbook", "wasm_module")
        if collapse_ws(str(content.get(key, "")))
    )
    for pattern in (
        r'mount\s*:\s*str\s*=\s*"([^"]+)"',
        r"mount\s*:\s*str\s*=\s*'([^']+)'",
        r'mount\s*=\s*"([^"]+)"',
        r"mount\s*=\s*'([^']+)'",
        r'[A-Za-z_][A-Za-z0-9_]*mount\s*:\s*str\s*=\s*"([^"]+)"',
        r"[A-Za-z_][A-Za-z0-9_]*mount\s*:\s*str\s*=\s*'([^']+)'",
        r'[A-Za-z_][A-Za-z0-9_]*mount\s*=\s*"([^"]+)"',
        r"[A-Za-z_][A-Za-z0-9_]*mount\s*=\s*'([^']+)'",
    ):
        for raw_name in re.findall(pattern, broker_source):
            name = collapse_ws(str(raw_name))
            if name and name not in discovered:
                discovered.append(name)
    return discovered


def _inferred_data_classes_from_brokers(content: Mapping[str, Any]) -> list[str]:
    governed_broker_hints = _governed_broker_hints_from_content(content)
    mount_names = _governed_mount_names_from_content(content)
    default_mounts = default_virtual_mount_table()
    inferred: list[str] = []
    for mount_name in mount_names:
        mount_spec = dict(default_mounts.get(mount_name, {})) if isinstance(default_mounts.get(mount_name, {}), Mapping) else {}
        if mount_name in content.get("virtual_mounts", {}) and isinstance(content.get("virtual_mounts", {}), Mapping):
            explicit_spec = content.get("virtual_mounts", {}).get(mount_name, {})
            if isinstance(explicit_spec, Mapping):
                mount_spec.update(dict(explicit_spec))
        data_class = collapse_ws(str(mount_spec.get("data_class", "")))
        if data_class and data_class not in inferred:
            inferred.append(data_class)
    if "store.named_query" in governed_broker_hints and "internal" not in inferred:
        inferred.append("internal")
    if "store.skill_state" in governed_broker_hints and "derived" not in inferred:
        inferred.append("derived")
    if (
        any(
            name in governed_broker_hints
            for name in (
                "fs.read_mount",
                "fs.write_mount",
                "fs.list_mount",
                "fs.find_mount",
                "fs.copy_mount",
                "fs.move_mount",
                "fs.delete_mount",
                "fs.create_zip_mount",
                "fs.extract_zip_mount",
            )
        )
        and not inferred
    ):
        inferred.append("public")
    return inferred


def _field_declared(
    declaration: Mapping[str, Any],
    payload: Mapping[str, Any],
    field_name: str,
) -> bool:
    if field_name in declaration:
        return True
    return field_name in payload


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [collapse_ws(str(item)) for item in value if collapse_ws(str(item))]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, str] = {}
    for key, raw in value.items():
        key_text = collapse_ws(str(key))
        value_text = collapse_ws(str(raw))
        if not key_text or not value_text:
            continue
        normalized[key_text] = value_text
    return normalized


def normalize_skill_schema_version(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like importing or exporting externally governed skills, helps with selecting one supported skill schema version and rejecting unsupported declaration formats early.

    Reference to Theory:
        Supports open governance by separating older compact skill bundles from the newer declaration-first governed skill form.

    Example Input Output:
        Input: `normalize_skill_schema_version(value='bssc_skill.v2')`
        Output: 'bssc_skill.v2'

    Args:
        value: Value for `value` used by `normalize_skill_schema_version`. Expected type: `Any`.

    Returns:
        str: Result produced by `normalize_skill_schema_version`.
    """
    normalized = collapse_ws(str(value or SKILL_SCHEMA_VERSION_V1))
    if not normalized:
        return SKILL_SCHEMA_VERSION_V1
    if normalized not in SKILL_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported skill schema version: {normalized}")
    return normalized


def normalize_skill_kind(value: Any, *, default: str = "knowledge") -> str:
    """
    High Level Purpose:
        In circumstances like skill import, export, and policy evaluation, helps with reducing raw skill kind spelling into one supported governed kind.

    Reference to Theory:
        Supports open governance by making skill and policy declarations machine-interpretable before admission checks occur.

    Example Input Output:
        Input: `normalize_skill_kind(value='policy', default='knowledge')`
        Output: 'policy'

    Args:
        value: Value for `value` used by `normalize_skill_kind`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_kind`. Expected type: `str`. Defaults to `'knowledge'`.

    Returns:
        str: Result produced by `normalize_skill_kind`.
    """
    return _normalize_skill_kind(value, default=default)


def composition_binding_targets(declaration: Mapping[str, Any] | None) -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed nested skill invocation, helps with deriving the explicit target titles that a skill is allowed to compose with.

    Reference to Theory:
        Supports composition governance by turning declaration-level composition rights into explicit invokable bindings.

    Example Input Output:
        Input: `composition_binding_targets({'composition_rights': ['skill:Hi Responder', 'invoke:CSV Reader']})`
        Output: ['Hi Responder', 'CSV Reader']

    Args:
        declaration: Value for `declaration` used by `composition_binding_targets`. Expected type: `Mapping[str, Any] | None`.

    Returns:
        list[str]: Result produced by `composition_binding_targets`.
    """
    if not isinstance(declaration, Mapping):
        return []
    targets: list[str] = []
    for item in _string_list(declaration.get("composition_rights", [])):
        raw = collapse_ws(str(item))
        if not raw:
            continue
        if raw == "*":
            return ["*"]
        if ":" in raw:
            prefix, target = raw.split(":", 1)
            if collapse_ws(prefix).lower() not in {"skill", "invoke", "title"}:
                continue
            raw = collapse_ws(target)
        if raw and raw not in targets:
            targets.append(raw)
    return targets


def normalize_skill_risk_tier(value: Any, *, default: str = "tier1_bounded_transform") -> str:
    """
    High Level Purpose:
        In circumstances like declared skill admission and policy comparison, helps with normalizing the declared risk tier into the ordered governance ladder used for checks.

    Reference to Theory:
        Supports open governance section 16 by making every governed skill comparable on one explicit risk scale.

    Example Input Output:
        Input: `normalize_skill_risk_tier(value='tier2_connected')`
        Output: 'tier2_connected'

    Args:
        value: Value for `value` used by `normalize_skill_risk_tier`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_risk_tier`. Expected type: `str`. Defaults to `'tier1_bounded_transform'`.

    Returns:
        str: Result produced by `normalize_skill_risk_tier`.
    """
    return _normalize_skill_risk_tier(value, default=default)


def normalize_skill_approval_class(value: Any, *, default: str = "automatic") -> str:
    """
    High Level Purpose:
        In circumstances like admission and invocation governance, helps with normalizing approval class labels into one explicit approval ladder.

    Reference to Theory:
        Supports open governance section 13 by making approval requirements and policy requirements comparable before effect.

    Example Input Output:
        Input: `normalize_skill_approval_class(value='operator_approved')`
        Output: 'operator_approved'

    Args:
        value: Value for `value` used by `normalize_skill_approval_class`. Expected type: `Any`.
        default: Value for `default` used by `normalize_skill_approval_class`. Expected type: `str`. Defaults to `'automatic'`.

    Returns:
        str: Result produced by `normalize_skill_approval_class`.
    """
    return _normalize_skill_approval_class(value, default=default)


def normalize_skill_authorities(value: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like declaration parsing and policy enforcement, helps with reducing requested authority names into one stable bounded authority set.

    Reference to Theory:
        Supports open governance section 8 by making authority requests explicit, granular, and comparable during admission.

    Example Input Output:
        Input: `normalize_skill_authorities(value=['read', 'execute', 'execute'])`
        Output: ['read', 'execute']

    Args:
        value: Value for `value` used by `normalize_skill_authorities`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `normalize_skill_authorities`.
    """
    return _normalize_skill_authorities(value)


def skill_declaration_from_payload(
    payload: Mapping[str, Any],
    *,
    kind: str,
    fallback_inputs: Mapping[str, Any] | None = None,
    fallback_outputs: Mapping[str, Any] | None = None,
    executor_framework: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing declaration-first governed skills, helps with normalizing and validating the skill declaration required by the v2 schema.

    Reference to Theory:
        Supports open governance section 7 by turning the declarative skill contract into one machine-checkable structure before admission.

    Example Input Output:
        Input: `skill_declaration_from_payload(payload={'schema': 'bssc_skill.v2', 'declaration': {'intent': 'Open a browser URL.', 'inputs': {'url': 'target URL'}, 'outputs': {'status': 'open status'}, 'authorities_requested': ['execute'], 'authority_bounds': {'execute': {'scope': 'local_desktop', 'target': 'browser_application', 'context': 'explicit_user_prompt', 'duration': 'single_invocation', 'triggering_conditions': ['user invokes skill'], 'approval_class': 'automatic'}}, 'data_classes_touched': ['public'], 'side_effects': ['launch browser'], 'persistence_behavior': 'none', 'invocation_rights': ['direct_user_invocation'], 'composition_rights': [], 'escalation_rights': [], 'approval_requirements': ['automatic'], 'risk_tier': 'tier1_bounded_transform'}}, kind='ability', fallback_inputs={}, fallback_outputs={}, executor_framework='python3')`
        Output: {'intent': 'Open a browser URL.', 'inputs': {'url': 'target URL'}, 'outputs': {'status': 'open status'}, 'authorities_requested': ['execute'], 'authority_bounds': {'execute': {'scope': 'local_desktop', 'target': 'browser_application', 'context': 'explicit_user_prompt', 'duration': 'single_invocation', 'triggering_conditions': ['user invokes skill'], 'approval_class': 'automatic'}}, 'data_classes_touched': ['public'], 'side_effects': ['launch browser'], 'persistence_behavior': 'none', 'invocation_rights': ['direct_user_invocation'], 'composition_rights': [], 'escalation_rights': [], 'approval_requirements': ['automatic'], 'risk_tier': 'tier1_bounded_transform', 'executor_framework': 'python3'}

    Args:
        payload: Value for `payload` used by `skill_declaration_from_payload`. Expected type: `Mapping[str, Any]`.
        kind: Value for `kind` used by `skill_declaration_from_payload`. Expected type: `str`.
        fallback_inputs: Value for `fallback_inputs` used by `skill_declaration_from_payload`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        fallback_outputs: Value for `fallback_outputs` used by `skill_declaration_from_payload`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        executor_framework: Value for `executor_framework` used by `skill_declaration_from_payload`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `skill_declaration_from_payload`.
    """
    schema = normalize_skill_schema_version(payload.get("schema", SKILL_SCHEMA_VERSION_V1))
    if schema != SKILL_SCHEMA_VERSION_V2 or kind in {"policy", "approval", "revocation", "incident"}:
        return {}

    declaration = dict(payload.get("declaration", {})) if isinstance(payload.get("declaration", {}), Mapping) else {}
    normalized_inputs = _string_mapping(declaration.get("inputs", fallback_inputs or {}))
    normalized_outputs = _string_mapping(declaration.get("outputs", fallback_outputs or {}))
    authority_bounds_raw = (
        dict(declaration.get("authority_bounds", {}))
        if isinstance(declaration.get("authority_bounds", {}), Mapping)
        else {}
    )
    authority_bounds: dict[str, dict[str, Any]] = {}
    for authority, raw_bounds in authority_bounds_raw.items():
        authority_name = collapse_ws(str(authority)).lower().replace("-", "_").replace(" ", "_")
        if authority_name not in SKILL_AUTHORITIES or not isinstance(raw_bounds, Mapping):
            continue
        triggering_conditions = _string_list(raw_bounds.get("triggering_conditions", []))
        authority_bounds[authority_name] = {
            "scope": collapse_ws(str(raw_bounds.get("scope", ""))),
            "target": collapse_ws(str(raw_bounds.get("target", ""))),
            "context": collapse_ws(str(raw_bounds.get("context", ""))),
            "duration": collapse_ws(str(raw_bounds.get("duration", ""))),
            "triggering_conditions": triggering_conditions,
            "approval_class": normalize_skill_approval_class(raw_bounds.get("approval_class", "automatic")),
        }

    normalized = {
        "intent": collapse_ws(str(declaration.get("intent", payload.get("intent", "")))),
        "inputs": normalized_inputs,
        "outputs": normalized_outputs,
        "authorities_requested": normalize_skill_authorities(
            declaration.get("authorities_requested", payload.get("authorities_requested", []))
        ),
        "authority_bounds": authority_bounds,
        "data_classes_touched": _string_list(
            declaration.get("data_classes_touched", payload.get("data_classes_touched", []))
        ),
        "side_effects": _string_list(declaration.get("side_effects", payload.get("side_effects", []))),
        "persistence_behavior": collapse_ws(
            str(declaration.get("persistence_behavior", payload.get("persistence_behavior", "")))
        ),
        "invocation_rights": _string_list(
            declaration.get("invocation_rights", payload.get("invocation_rights", []))
        ),
        "composition_rights": _string_list(
            declaration.get("composition_rights", payload.get("composition_rights", []))
        ),
        "escalation_rights": _string_list(
            declaration.get("escalation_rights", payload.get("escalation_rights", []))
        ),
        "approval_requirements": [
            normalize_skill_approval_class(item)
            for item in _string_list(declaration.get("approval_requirements", payload.get("approval_requirements", [])))
        ],
        "risk_tier": normalize_skill_risk_tier(
            declaration.get("risk_tier", payload.get("risk_tier", "tier1_bounded_transform"))
        ),
    }
    if executor_framework:
        normalized["executor_framework"] = normalize_executor_framework_name(executor_framework)

    missing_fields: list[str] = []
    for field_name in SKILL_DECLARATION_REQUIRED_FIELDS:
        if field_name in _DECLARATION_COLLECTION_FIELDS:
            if not _field_declared(declaration, payload, field_name):
                missing_fields.append(field_name)
            continue
        if normalized.get(field_name) in (None, "", [], {}):
            missing_fields.append(field_name)
    if missing_fields:
        raise ValueError(
            "Skill declaration v2 requires declared fields: "
            + ", ".join(missing_fields)
        )
    missing_bounds = [
        authority
        for authority in normalized["authorities_requested"]
        if authority not in normalized["authority_bounds"]
    ]
    if missing_bounds:
        raise ValueError(
            "Skill declaration v2 requires authority_bounds for every requested authority: "
            + ", ".join(missing_bounds)
        )
    for authority, bounds in normalized["authority_bounds"].items():
        missing_bound_fields = [
            field_name
            for field_name in SKILL_AUTHORITY_BOUND_FIELDS
            if bounds.get(field_name) in (None, "", [], {})
        ]
        if missing_bound_fields:
            raise ValueError(
                f"Skill declaration v2 authority {authority!r} is missing bounds: "
                + ", ".join(missing_bound_fields)
            )
    return normalized


def skill_policy_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing policy artifacts that govern later skill admission, helps with normalizing the policy document into one machine-checkable policy specification.

    Reference to Theory:
        Supports open governance sections 8, 9, and 13 by making policy explicit before skill admission or invocation.

    Example Input Output:
        Input: `skill_policy_from_payload(payload={'schema': 'bssc_skill.v2', 'kind': 'policy', 'policy': {'intent': 'Admit only bounded local abilities.', 'target_kinds': ['ability'], 'max_risk_tier': 'tier2_connected', 'allowed_authorities': ['read', 'write', 'execute'], 'denied_authorities': ['approve', 'modify', 'escalate'], 'allowed_executors': ['python3'], 'required_approval_for_risk_tiers': {'tier3_sensitive': 'operator_approved'}}})`
        Output: {'intent': 'Admit only bounded local abilities.', 'target_kinds': ['ability'], 'max_risk_tier': 'tier2_connected', 'allowed_authorities': ['read', 'write', 'execute'], 'denied_authorities': ['approve', 'modify', 'escalate'], 'allowed_executors': ['python3'], 'required_approval_for_risk_tiers': {'tier3_sensitive': 'operator_approved'}}

    Args:
        payload: Value for `payload` used by `skill_policy_from_payload`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `skill_policy_from_payload`.
    """
    schema = normalize_skill_schema_version(payload.get("schema", SKILL_SCHEMA_VERSION_V1))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != SKILL_SCHEMA_VERSION_V2 or kind != "policy":
        return {}
    policy = dict(payload.get("policy", {})) if isinstance(payload.get("policy", {}), Mapping) else {}
    normalized_required_approval = {}
    raw_required = (
        dict(policy.get("required_approval_for_risk_tiers", {}))
        if isinstance(policy.get("required_approval_for_risk_tiers", {}), Mapping)
        else {}
    )
    for tier, approval in raw_required.items():
        normalized_required_approval[normalize_skill_risk_tier(tier)] = normalize_skill_approval_class(approval)
    normalized = {
        "intent": collapse_ws(str(policy.get("intent", ""))),
        "target_kinds": [
            normalize_skill_kind(item)
            for item in _string_list(policy.get("target_kinds", ["knowledge", "ability"]))
        ],
        "max_risk_tier": normalize_skill_risk_tier(policy.get("max_risk_tier", "tier1_bounded_transform")),
        "allowed_authorities": normalize_skill_authorities(policy.get("allowed_authorities", [])),
        "denied_authorities": normalize_skill_authorities(policy.get("denied_authorities", [])),
        "allowed_executors": [
            normalize_executor_framework_name(item)
            for item in _string_list(policy.get("allowed_executors", []))
            if normalize_executor_framework_name(item)
        ],
        "allowed_data_classes": _string_list(policy.get("allowed_data_classes", [])),
        "denied_side_effects": _string_list(policy.get("denied_side_effects", [])),
        "required_approval_for_risk_tiers": normalized_required_approval,
    }
    missing_fields = [
        field_name
        for field_name in ("intent", "target_kinds", "max_risk_tier")
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing_fields:
        raise ValueError(
            "Policy artifact v2 requires non-empty fields: "
            + ", ".join(missing_fields)
        )
    return normalized


def policy_answer_summary(policy: Mapping[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like storing policy artifacts inside the existing artifact substrate, helps with producing a readable summary answer that states what the policy admits and constrains.

    Reference to Theory:
        Supports open governance by keeping policy artifacts reviewable in human-readable form even when they are stored in the general artifact substrate.

    Example Input Output:
        Input: `policy_answer_summary(policy={'intent': 'Admit only bounded local abilities.', 'target_kinds': ['ability'], 'max_risk_tier': 'tier2_connected', 'allowed_authorities': ['read', 'execute']})`
        Output: 'Policy intent: Admit only bounded local abilities. Targets: ability. Max risk tier: tier2_connected. Allowed authorities: read, execute.'

    Args:
        policy: Value for `policy` used by `policy_answer_summary`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `policy_answer_summary`.
    """
    intent = collapse_ws(str(policy.get("intent", "")))
    target_kinds = ", ".join(_string_list(policy.get("target_kinds", [])))
    max_risk_tier = normalize_skill_risk_tier(policy.get("max_risk_tier", "tier1_bounded_transform"))
    allowed_authorities = ", ".join(normalize_skill_authorities(policy.get("allowed_authorities", [])))
    denied_authorities = ", ".join(normalize_skill_authorities(policy.get("denied_authorities", [])))
    segments = [
        f"Policy intent: {intent}.",
        f"Targets: {target_kinds}.",
        f"Max risk tier: {max_risk_tier}.",
        f"Allowed authorities: {allowed_authorities}.",
    ]
    if denied_authorities:
        segments.append(f"Denied authorities: {denied_authorities}.")
    return " ".join(segment for segment in segments if collapse_ws(segment))


def artifact_skill_declaration(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like admission checks and governed export, helps with reading the normalized skill declaration that was stored on an artifact at import time.

    Reference to Theory:
        Supports open governance by keeping the admitted declaration available for later policy, review, and replay checks.

    Example Input Output:
        Input: `artifact_skill_declaration(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'intent': 'Open a browser URL.', 'risk_tier': 'tier1_bounded_transform'}

    Args:
        artifact: Value for `artifact` used by `artifact_skill_declaration`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_skill_declaration`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    return dict(content.get("skill_declaration", {})) if isinstance(content.get("skill_declaration", {}), Mapping) else {}


def synthesized_skill_declaration_for_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting legacy artifacts through the governed skill interface, helps with synthesizing one conservative v2 declaration when the artifact has no stored declaration yet.

    Reference to Theory:
        Supports open governance by letting older artifact records participate in declaration-first export without requiring that they were originally imported as governed skills.

    Example Input Output:
        Input: `synthesized_skill_declaration_for_artifact(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python_script'))`
        Output: {'intent': 'Execute the skill described by Physics / Force / Force From Mass And Acceleration.', 'inputs': {'m': 'number', 'a': 'number'}, 'outputs': {'F': 'number'}, 'authorities_requested': ['execute'], 'authority_bounds': {'execute': {'scope': 'local_executor', 'target': 'python3_skill_runtime', 'context': 'explicit_user_prompt', 'duration': 'single_invocation', 'triggering_conditions': ['user invokes skill'], 'approval_class': 'automatic'}}, 'data_classes_touched': ['public'], 'side_effects': ['local executor invocation'], 'persistence_behavior': 'none', 'invocation_rights': ['direct_user_invocation'], 'composition_rights': [], 'escalation_rights': [], 'approval_requirements': ['automatic'], 'risk_tier': 'tier1_bounded_transform', 'executor_framework': 'python3'}

    Args:
        artifact: Value for `artifact` used by `synthesized_skill_declaration_for_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `synthesized_skill_declaration_for_artifact`.
    """
    existing = artifact_skill_declaration(artifact)
    if existing:
        return existing

    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    kind = normalize_skill_kind(
        content.get("skill_kind", ""),
        default=("policy" if artifact_is_policy_record(artifact) else str(getattr(artifact.artifact_type, "value", artifact.artifact_type))),
    )
    if kind == "policy":
        return {}

    title = collapse_ws(str(getattr(artifact, "title", "")))
    question = collapse_ws(str(content.get("question", "")))
    answer = collapse_ws(str(content.get("answer", "")))
    input_contract = _string_mapping(content.get("input_contract", {}))
    output_contract = _string_mapping(content.get("output_contract", {}))
    if kind == "knowledge":
        if not input_contract:
            input_contract = {"question": "knowledge request"}
        if not output_contract:
            output_contract = {"answer": "knowledge answer"}
    else:
        if not input_contract:
            input_contract = {"payload": "execution input"}
        if not output_contract:
            output_contract = {"result": "execution result"}

    representation = str(getattr(artifact.representation, "value", artifact.representation))
    executor_framework = ability_executor_framework(
        representation=representation,
        content=content,
    ) if kind == "ability" else ""
    normalized_executor = normalize_executor_framework_name(executor_framework)

    signal_text = " ".join(
        segment for segment in (
            title,
            question,
            answer,
            collapse_ws(str(content.get("python_script", ""))),
            collapse_ws(str(content.get("shell_script", ""))),
            collapse_ws(str(content.get("ansible_playbook", ""))),
            collapse_ws(str(content.get("wasm_module", ""))),
        )
        if segment
    ).lower()
    governed_authority_hints = normalize_skill_authorities(content.get("governed_authorities", []))
    governed_broker_hints = _governed_broker_hints_from_content(content)

    authorities_requested: list[str]
    if kind == "knowledge":
        authorities_requested = ["read"]
    elif governed_authority_hints:
        authorities_requested = list(governed_authority_hints)
    elif governed_broker_hints:
        authorities_requested = ["execute"]
        for broker_name in governed_broker_hints:
            broker_authority = required_authority_for_host_broker(broker_name)
            if broker_authority and broker_authority not in authorities_requested:
                authorities_requested.append(broker_authority)
    else:
        authorities_requested = ["execute"]
        if normalized_executor == "ansible":
            authorities_requested.append("write")
        elif normalized_executor == "bash" and any(
            marker in signal_text
            for marker in (
                "mkdir",
                "touch",
                "cp ",
                "mv ",
                "rm ",
                "chmod",
                "tar ",
                "unzip",
                "install ",
                "write",
                "create",
                "delete",
                "move",
                "copy",
            )
        ):
            authorities_requested.append("write")
        if any(
            marker in signal_text
            for marker in (
                "http://",
                "https://",
                "requests",
                "urllib",
                "openai",
                "anthropic",
                "slack",
                "github",
                "boto3",
                "supabase",
                "stripe",
                "webbrowser",
                "browser",
                "download",
                "upload",
                "poll ",
            )
        ):
            authorities_requested.append("communicate")

    authority_bounds: dict[str, dict[str, Any]] = {}
    for authority in authorities_requested:
        target = "knowledge_artifact" if authority == "read" and kind == "knowledge" else (
            f"{normalized_executor}_skill_runtime" if authority == "execute" and normalized_executor else "skill_runtime"
        )
        scope = "local_skill_store" if authority == "read" and kind == "knowledge" else (
            "local_configuration_target" if normalized_executor == "ansible" else "local_executor"
        )
        authority_bounds[authority] = {
            "scope": scope,
            "target": target,
            "context": "explicit_user_prompt",
            "duration": "single_invocation",
            "triggering_conditions": ["user invokes skill"],
            "approval_class": "automatic",
        }

    side_effects: list[str]
    if kind == "knowledge":
        side_effects = ["none"]
        persistence_behavior = "none"
        risk_tier = "tier0_passive"
    else:
        side_effects = []
        if governed_broker_hints:
            side_effects.extend(
                f"brokered host effect via {broker_name}"
                for broker_name in governed_broker_hints
            )
        elif normalized_executor == "ansible":
            side_effects.append("configuration changes on declared targets")
        elif normalized_executor == "bash":
            side_effects.append("shell command execution")
        elif normalized_executor == "python3":
            side_effects.append("local executor invocation")
        else:
            side_effects.append("ability execution")
        if "communicate" in authorities_requested:
            side_effects.append("network communication")
        if "write" in authorities_requested:
            side_effects.append("filesystem or external state modification")
        persistence_behavior = "may_modify_external_state" if "write" in authorities_requested else "none"
        if normalized_executor == "ansible":
            risk_tier = "tier3_sensitive"
        elif "communicate" in authorities_requested or "write" in authorities_requested:
            risk_tier = "tier2_connected"
        else:
            risk_tier = "tier1_bounded_transform"

    intent = question or (
        f"Answer the knowledge request described by {title}."
        if kind == "knowledge"
        else f"Execute the skill described by {title}."
    )
    inferred_data_classes = _inferred_data_classes_from_brokers(content)
    payload = {
        "schema": SKILL_SCHEMA_VERSION_V2,
        "kind": kind,
        "declaration": {
            "intent": intent,
            "inputs": input_contract,
            "outputs": output_contract,
            "authorities_requested": authorities_requested,
            "authority_bounds": authority_bounds,
            "data_classes_touched": inferred_data_classes or ["public"],
            "side_effects": side_effects,
            "persistence_behavior": persistence_behavior,
            "invocation_rights": ["direct_user_invocation"],
            "composition_rights": [],
            "escalation_rights": [],
            "approval_requirements": ["automatic"],
            "risk_tier": risk_tier,
        },
    }
    return skill_declaration_from_payload(
        payload,
        kind=kind,
        fallback_inputs=input_contract,
        fallback_outputs=output_contract,
        executor_framework=normalized_executor,
    )


def artifact_skill_policy(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like admission checks and governed export, helps with reading the normalized policy specification stored on a policy artifact.

    Reference to Theory:
        Supports open governance by making policy artifacts machine-readable during admission and review.

    Example Input Output:
        Input: `artifact_skill_policy(artifact=Artifact(id='artifact-skill-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml'))`
        Output: {'intent': 'Admit bounded local skills.', 'max_risk_tier': 'tier2_connected'}

    Args:
        artifact: Value for `artifact` used by `artifact_skill_policy`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_skill_policy`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    return dict(content.get("skill_policy", {})) if isinstance(content.get("skill_policy", {}), Mapping) else {}


def artifact_skill_admission(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like execution gating and governed export, helps with reading the stored admission decision attached to a governed skill artifact.

    Reference to Theory:
        Supports open governance sections 9 and 10 by preserving the admission result that must hold before activation or invocation.

    Example Input Output:
        Input: `artifact_skill_admission(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'status': 'admitted', 'admitted': True}

    Args:
        artifact: Value for `artifact` used by `artifact_skill_admission`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_skill_admission`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    return dict(content.get("skill_admission", {})) if isinstance(content.get("skill_admission", {}), Mapping) else {}


def artifact_is_policy_record(artifact: Artifact) -> bool:
    """
    High Level Purpose:
        In circumstances like answer selection and execution gating, helps with detecting that an artifact is a policy record rather than an invokable or explanatory end-user skill.

    Reference to Theory:
        Supports open governance by keeping policy artifacts reviewable without letting them masquerade as ordinary user-facing abilities.

    Example Input Output:
        Input: `artifact_is_policy_record(artifact=Artifact(id='artifact-skill-policy', title='Local Admission Policy', artifact_type='knowledge', representation='yaml'))`
        Output: True

    Args:
        artifact: Value for `artifact` used by `artifact_is_policy_record`. Expected type: `Artifact`.

    Returns:
        bool: Result produced by `artifact_is_policy_record`.
    """
    return bool(artifact_skill_policy(artifact))


def artifact_current_use_admission(
    artifact: Artifact,
    *,
    policy_artifacts: list[Artifact] | None = None,
    approval_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and host mediation, helps with deriving the admission decision that should govern current use under the currently installed policy and approval artifacts.

    Reference to Theory:
        Supports open governance sections 9, 10, and 13 by preventing invocation from depending only on stale import-time admission when current policy or approval state is available.

    Example Input Output:
        Input: `artifact_current_use_admission(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'), policy_artifacts=[], approval_artifacts=[])`
        Output: {'status': 'held', 'admitted': False, 'rationale': 'No policy artifact is currently installed for governed v2 skills.', 'policy_titles': [], 'approval_titles': [], 'required_approval_class': 'automatic'}

    Args:
        artifact: Value for `artifact` used by `artifact_current_use_admission`. Expected type: `Artifact`.
        policy_artifacts: Value for `policy_artifacts` used by `artifact_current_use_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.
        approval_artifacts: Value for `approval_artifacts` used by `artifact_current_use_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `artifact_current_use_admission`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    schema = normalize_skill_schema_version(content.get("skill_schema", SKILL_SCHEMA_VERSION_V1))
    if schema != SKILL_SCHEMA_VERSION_V2:
        return {
            "status": "legacy_implicit_admit",
            "admitted": True,
            "rationale": "",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    stored_admission = artifact_skill_admission(artifact)
    if artifact_is_policy_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Policy artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [artifact.title],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    from approval_governance import artifact_is_approval_record

    if artifact_is_approval_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Approval artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [artifact.title],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    if artifact_is_revocation_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Revocation artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    if artifact_is_incident_record(artifact):
        return {
            "status": "governance_record",
            "admitted": False,
            "rationale": "Incident artifacts are governance records and are not invokable answer artifacts.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    current_policy_artifacts = policy_artifacts if policy_artifacts is not None else []
    current_approval_artifacts = approval_artifacts if approval_artifacts is not None else []
    if current_policy_artifacts or current_approval_artifacts:
        declaration = artifact_skill_declaration(artifact)
        if not declaration:
            return {
                "status": "held",
                "admitted": False,
                "rationale": "Governed skill has no declaration record for current-use evaluation.",
                "policy_titles": [],
                "approval_titles": [],
                "required_approval_class": "automatic",
                "evaluated_at": utc_now(),
            }
        kind = normalize_skill_kind(content.get("skill_kind", ""), default=str(getattr(artifact.artifact_type, "value", artifact.artifact_type)))
        executor_framework = ability_executor_framework(
            representation=str(getattr(artifact.representation, "value", artifact.representation)),
            content=content,
        )
        return evaluate_skill_admission(
            declaration,
            skill_title=artifact.title,
            kind=kind,
            executor_framework=executor_framework,
            skill_content=content,
            policy_artifacts=current_policy_artifacts,
            approval_artifacts=current_approval_artifacts,
        )
    return stored_admission


def artifact_admitted_for_use(artifact: Artifact) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like runtime reuse and execution gating, helps with deciding whether a governed skill artifact is currently admitted for use.

    Reference to Theory:
        Supports open governance sections 9 and 10 by preventing invocation of governed skills whose admission, activation, trust, or quarantine state does not currently permit use.

    Example Input Output:
        Input: `artifact_admitted_for_use(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: (True, '')

    Args:
        artifact: Value for `artifact` used by `artifact_admitted_for_use`. Expected type: `Artifact`.

    Returns:
        tuple[bool, str]: Result produced by `artifact_admitted_for_use`.
    """
    return artifact_admitted_for_use_with_governance(
        artifact,
        policy_artifacts=None,
        approval_artifacts=None,
    )


def artifact_admitted_for_use_with_governance(
    artifact: Artifact,
    *,
    policy_artifacts: list[Artifact] | None,
    approval_artifacts: list[Artifact] | None,
    revocation_artifacts: list[Artifact] | None = None,
    incident_artifacts: list[Artifact] | None = None,
) -> tuple[bool, str]:
    """
    High Level Purpose:
        In circumstances like invocation-time governance and runtime selection, helps with deciding whether a governed skill artifact is currently admitted for use under stored or current governance state.

    Reference to Theory:
        Supports open governance sections 9, 10, and 13 by allowing runtime use decisions to reflect current policy and approval state when available.

    Example Input Output:
        Input: `artifact_admitted_for_use_with_governance(artifact=Artifact(id='artifact-skill-abc', title='Open Browser URL', artifact_type='ability', representation='python_script'), policy_artifacts=[], approval_artifacts=[])`
        Output: (False, 'No policy artifact is currently installed for governed v2 skills.')

    Args:
        artifact: Value for `artifact` used by `artifact_admitted_for_use_with_governance`. Expected type: `Artifact`.
        policy_artifacts: Value for `policy_artifacts` used by `artifact_admitted_for_use_with_governance`. Expected type: `list[Artifact] | None`.
        approval_artifacts: Value for `approval_artifacts` used by `artifact_admitted_for_use_with_governance`. Expected type: `list[Artifact] | None`.

    Returns:
        tuple[bool, str]: Result produced by `artifact_admitted_for_use_with_governance`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    schema = normalize_skill_schema_version(content.get("skill_schema", SKILL_SCHEMA_VERSION_V1))
    if schema != SKILL_SCHEMA_VERSION_V2:
        return True, ""
    admission = artifact_current_use_admission(
        artifact,
        policy_artifacts=policy_artifacts,
        approval_artifacts=approval_artifacts,
    )
    if not admission:
        return False, "Governed skill has no admission record."
    if str(admission.get("status", "")).strip().lower() != "admitted":
        rationale = collapse_ws(str(admission.get("rationale", "")))
        return False, rationale or "Governed skill is not admitted for use."
    lifecycle = artifact_effective_skill_lifecycle(
        artifact,
        current_admission_status=str(admission.get("status", "")),
    )
    overlay = governed_safety_lifecycle_overlay(
        skill_title=artifact.title,
        kind=normalize_skill_kind(
            content.get("skill_kind", ""),
            default=str(getattr(artifact.artifact_type, "value", artifact.artifact_type)),
        ),
        revocation_artifacts=revocation_artifacts,
        incident_artifacts=incident_artifacts,
    )
    lifecycle.update({key: value for key, value in overlay.items() if key not in {"revocation_titles", "incident_titles"} and value not in (None, "", [], {})})
    lifecycle_allowed, lifecycle_reason = skill_lifecycle_allows_invocation(lifecycle)
    if not lifecycle_allowed:
        return False, lifecycle_reason
    return True, ""


def evaluate_skill_admission(
    declaration: Mapping[str, Any],
    *,
    skill_title: str = "",
    kind: str,
    executor_framework: str = "",
    skill_content: Mapping[str, Any] | None = None,
    policy_artifacts: list[Artifact] | None = None,
    approval_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like skill import and later activation checks, helps with evaluating whether a declaration-first governed skill is admitted, held, or rejected under the currently installed policy artifacts.

    Reference to Theory:
        Supports open governance sections 8, 9, 10, 13, and 16 by applying policy, authority, approval, and risk checks before use.

    Example Input Output:
        Input: `evaluate_skill_admission(declaration={'intent': 'Open a browser URL.', 'authorities_requested': ['execute'], 'authority_bounds': {'execute': {'scope': 'local_desktop', 'target': 'browser_application', 'context': 'explicit_user_prompt', 'duration': 'single_invocation', 'triggering_conditions': ['user invokes skill'], 'approval_class': 'automatic'}}, 'data_classes_touched': ['public'], 'side_effects': ['launch browser'], 'persistence_behavior': 'none', 'invocation_rights': ['direct_user_invocation'], 'composition_rights': [], 'escalation_rights': [], 'approval_requirements': ['automatic'], 'risk_tier': 'tier1_bounded_transform', 'inputs': {'url': 'target URL'}, 'outputs': {'status': 'open status'}}, skill_title='Open Browser URL', kind='ability', executor_framework='python3', policy_artifacts=[], approval_artifacts=[])`
        Output: {'status': 'held', 'admitted': False, 'rationale': 'No policy artifact is currently installed for governed v2 skills.', 'policy_titles': [], 'approval_titles': [], 'required_approval_class': 'automatic', 'evaluated_at': '2026-03-31T12:00:00Z'}

    Args:
        declaration: Value for `declaration` used by `evaluate_skill_admission`. Expected type: `Mapping[str, Any]`.
        skill_title: Value for `skill_title` used by `evaluate_skill_admission`. Expected type: `str`. Defaults to `''`.
        kind: Value for `kind` used by `evaluate_skill_admission`. Expected type: `str`.
        executor_framework: Value for `executor_framework` used by `evaluate_skill_admission`. Expected type: `str`. Defaults to `''`.
        skill_content: Value for `skill_content` used by `evaluate_skill_admission`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.
        policy_artifacts: Value for `policy_artifacts` used by `evaluate_skill_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.
        approval_artifacts: Value for `approval_artifacts` used by `evaluate_skill_admission`. Expected type: `list[Artifact] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `evaluate_skill_admission`.
    """
    normalized_kind = normalize_skill_kind(kind)
    normalized_executor = normalize_executor_framework_name(executor_framework)
    policies = [artifact for artifact in (policy_artifacts or []) if artifact_skill_policy(artifact)]
    if not policies:
        return {
            "status": "held",
            "admitted": False,
            "rationale": "No policy artifact is currently installed for governed v2 skills.",
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }

    requested_authorities = normalize_skill_authorities(declaration.get("authorities_requested", []))
    risk_tier = normalize_skill_risk_tier(declaration.get("risk_tier", "tier1_bounded_transform"))
    approval_requirements = [
        normalize_skill_approval_class(item)
        for item in _string_list(declaration.get("approval_requirements", []))
    ] or ["automatic"]

    if normalized_kind == "ability" and normalized_executor and "execute" not in requested_authorities:
        return {
            "status": "held",
            "admitted": False,
            "rationale": (
                f"Executable {normalized_executor} skills must declare execute authority "
                "before they can be admitted."
            ),
            "policy_titles": [],
            "approval_titles": [],
            "required_approval_class": "automatic",
            "evaluated_at": utc_now(),
        }
    if normalized_kind == "ability" and normalized_executor == "python3" and _RISK_INDEX[risk_tier] >= _RISK_INDEX["tier3_sensitive"]:
        content = dict(skill_content) if isinstance(skill_content, Mapping) else {}
        governed_brokers = _governed_broker_hints_from_content(content)
        transitional_brokers = [
            broker_name
            for broker_name in governed_brokers
            if host_broker_stability(broker_name) == "transitional"
        ]
        if transitional_brokers:
            return {
                "status": "held",
                "admitted": False,
                "rationale": (
                    "Higher-risk Python skills must depend only on stable governed host ABI brokers. "
                    "Detected transitional brokers: " + ", ".join(sorted(transitional_brokers)) + "."
                ),
                "policy_titles": [],
                "approval_titles": [],
                "required_approval_class": "automatic",
                "evaluated_at": utc_now(),
            }
        python_code = str(content.get("python_script", "")).strip()
        if python_code:
            assessment = python_skill_data_surface_assessment(python_code)
            surface_issues: list[str] = []
            if assessment["uses_raw_sqlite"]:
                surface_issues.append("raw sqlite access")
            if assessment["uses_raw_network_io"]:
                surface_issues.append("raw network access")
            if assessment["uses_raw_tool_invocation"]:
                surface_issues.append("raw tool or process invocation")
            if assessment["uses_raw_path_io"]:
                surface_issues.append("raw path-based filesystem access")
            if assessment["uses_legacy_data_brokers"]:
                surface_issues.append("legacy path/sqlite broker surfaces")
            if surface_issues:
                return {
                    "status": "held",
                    "admitted": False,
                    "rationale": (
                        "Higher-risk Python skills must use governed host ABI surfaces such as "
                        "fs.read_mount, fs.write_mount, fs.list_mount, fs.find_mount, "
                        "store.named_query, store.skill_state, net.http_get_json, net.http_get_text, "
                        "or named macOS brokers. "
                        "Detected: " + ", ".join(surface_issues) + "."
                    ),
                    "policy_titles": [],
                    "approval_titles": [],
                    "required_approval_class": "automatic",
                    "evaluated_at": utc_now(),
                }
    if normalized_kind == "ability" and _RISK_INDEX[risk_tier] >= _RISK_INDEX["tier3_sensitive"]:
        content = dict(skill_content) if isinstance(skill_content, Mapping) else {}
        governed_brokers = _governed_broker_hints_from_content(content)
        transitional_brokers = [
            broker_name
            for broker_name in governed_brokers
            if host_broker_stability(broker_name) == "transitional"
        ]
        if transitional_brokers:
            return {
                "status": "held",
                "admitted": False,
                "rationale": (
                    "Higher-risk governed skills must depend only on stable host ABI brokers. "
                    "Detected transitional brokers: " + ", ".join(sorted(transitional_brokers)) + "."
                ),
                "policy_titles": [],
                "approval_titles": [],
                "required_approval_class": "automatic",
                "evaluated_at": utc_now(),
            }

    blocking_reasons: list[str] = []
    required_approval_class = "automatic"
    policy_titles: list[str] = []
    for artifact in policies:
        policy = artifact_skill_policy(artifact)
        policy_titles.append(artifact.title)
        if normalized_kind not in policy.get("target_kinds", []):
            blocking_reasons.append(f"policy {artifact.title!r} does not admit kind {normalized_kind!r}")
            continue
        if _RISK_INDEX[risk_tier] > _RISK_INDEX[normalize_skill_risk_tier(policy.get("max_risk_tier", risk_tier))]:
            blocking_reasons.append(
                f"policy {artifact.title!r} limits risk to {policy.get('max_risk_tier')}, but declaration requests {risk_tier}"
            )
        allowed_authorities = normalize_skill_authorities(policy.get("allowed_authorities", []))
        denied_authorities = normalize_skill_authorities(policy.get("denied_authorities", []))
        disallowed_requested = sorted(set(requested_authorities) & set(denied_authorities))
        if disallowed_requested:
            blocking_reasons.append(
                f"policy {artifact.title!r} denies authorities: {', '.join(disallowed_requested)}"
            )
        missing_allowed = sorted(set(requested_authorities) - set(allowed_authorities))
        if missing_allowed:
            blocking_reasons.append(
                f"policy {artifact.title!r} does not allow authorities: {', '.join(missing_allowed)}"
            )
        allowed_executors = [
            normalize_executor_framework_name(item)
            for item in _string_list(policy.get("allowed_executors", []))
        ]
        if normalized_kind == "ability" and allowed_executors and normalized_executor not in allowed_executors:
            blocking_reasons.append(
                f"policy {artifact.title!r} does not allow executor {normalized_executor or 'unknown'}"
            )
        allowed_data_classes = _string_list(policy.get("allowed_data_classes", []))
        if allowed_data_classes:
            undeclared_data = sorted(
                set(_string_list(declaration.get("data_classes_touched", []))) - set(allowed_data_classes)
            )
            if undeclared_data:
                blocking_reasons.append(
                    f"policy {artifact.title!r} does not allow data classes: {', '.join(undeclared_data)}"
                )
        denied_side_effects = set(_string_list(policy.get("denied_side_effects", [])))
        forbidden_side_effects = sorted(
            set(_string_list(declaration.get("side_effects", []))) & denied_side_effects
        )
        if forbidden_side_effects:
            blocking_reasons.append(
                f"policy {artifact.title!r} denies side effects: {', '.join(forbidden_side_effects)}"
            )
        policy_required_approval = normalize_skill_approval_class(
            dict(policy.get("required_approval_for_risk_tiers", {})).get(risk_tier, "automatic")
        )
        if _APPROVAL_INDEX[policy_required_approval] > _APPROVAL_INDEX[required_approval_class]:
            required_approval_class = policy_required_approval

    if blocking_reasons:
        return {
            "status": "rejected",
            "admitted": False,
            "rationale": "; ".join(blocking_reasons),
            "policy_titles": policy_titles,
            "approval_titles": [],
            "required_approval_class": required_approval_class,
            "evaluated_at": utc_now(),
        }

    strongest_declared_approval = max(
        approval_requirements,
        key=lambda item: _APPROVAL_INDEX[normalize_skill_approval_class(item)],
    )
    if _APPROVAL_INDEX[required_approval_class] > _APPROVAL_INDEX[strongest_declared_approval]:
        return {
            "status": "held",
            "admitted": False,
            "rationale": (
                f"Policy requires approval class {required_approval_class}, "
                f"but declaration only provides {strongest_declared_approval}."
            ),
            "policy_titles": policy_titles,
            "approval_titles": [],
            "required_approval_class": required_approval_class,
            "evaluated_at": utc_now(),
        }
    if required_approval_class != "automatic":
        from approval_governance import matching_approval_artifacts

        matching_approvals = matching_approval_artifacts(
            approval_artifacts,
            skill_title=skill_title,
            kind=normalized_kind,
            requested_authorities=requested_authorities,
            risk_tier=risk_tier,
            required_approval_class=required_approval_class,
        )
        approval_titles = [artifact.title for artifact in matching_approvals]
        if matching_approvals:
            return {
                "status": "admitted",
                "admitted": True,
                "rationale": (
                    f"Declaration satisfied installed policy constraints and matched approval class "
                    f"{required_approval_class}."
                ),
                "policy_titles": policy_titles,
                "approval_titles": approval_titles,
                "required_approval_class": required_approval_class,
                "evaluated_at": utc_now(),
            }
        return {
            "status": "held",
            "admitted": False,
            "rationale": f"Policy requires explicit approval class {required_approval_class} before admission.",
            "policy_titles": policy_titles,
            "approval_titles": [],
            "required_approval_class": required_approval_class,
            "evaluated_at": utc_now(),
        }
    return {
        "status": "admitted",
        "admitted": True,
        "rationale": "Declaration satisfied installed policy constraints and required no additional approval.",
        "policy_titles": policy_titles,
        "approval_titles": [],
        "required_approval_class": required_approval_class,
        "evaluated_at": utc_now(),
    }
