# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from realized_core_semantics.applied_model import Artifact
from realized_core_runtime.host_abi import known_host_broker_names, required_authority_for_host_broker
from realized_core_governance.declarations import (
    skill_declaration_from_payload,
)
from realized_core_governance.records import (
    artifact_is_policy_record,
    artifact_skill_declaration,
)
from realized_core_governance.vocabulary import (
    normalize_skill_approval_class as _normalize_skill_approval_class,
    normalize_skill_authorities as _normalize_skill_authorities,
    normalize_skill_kind as _normalize_skill_kind,
    normalize_skill_risk_tier as _normalize_skill_risk_tier,
)
from realized_core_semantics.semantic_text import collapse_ws
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V2,
)
from realized_skill_semantics.execution import (
    ability_executor_framework,
    normalize_executor_framework_name,
)
from realized_core_runtime.virtual_mounts import default_virtual_mount_table

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


__all__ = [
    "normalize_skill_approval_class",
    "normalize_skill_authorities",
    "normalize_skill_kind",
    "normalize_skill_risk_tier",
    "synthesized_skill_declaration_for_artifact",
]
