# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from realized_core_semantics.applied_model import Artifact
from realized_core_governance.lifecycle import artifact_skill_lifecycle
from realized_core_governance.records import artifact_skill_declaration
from realized_core_governance.vocabulary import normalize_skill_kind
from realized_skill_semantics.ir import (
    CanonicalSkillIR,
    derived_skill_family_metadata_from_title,
    normalized_skill_aliases,
    normalized_skill_family_metadata,
)
from realized_skill_semantics.normalization import normalized_skill_normalization_payload
from realized_core_semantics.semantic_text import collapse_ws
from realized_skill_semantics.compatibility import (
    normalized_skill_compatibility_payload,
)
from realized_skill_application.normalization import (
    synthesized_skill_normalization_for_artifact,
)
from realized_core_runtime.skill_declarations import synthesized_skill_declaration_for_artifact
from realized_skill_semantics.declaration import normalize_skill_schema_version
from realized_skill_semantics.execution import ability_executor_framework


def _normalized_string_list(values: Any) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    if not isinstance(values, list):
        return normalized
    for item in values:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _skill_kind_from_artifact(artifact: Artifact) -> str:
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    for key, value in (
        ("skill_kind", content.get("skill_kind")),
        ("policy", "policy" if content.get("skill_policy") else ""),
        ("approval", "approval" if content.get("skill_approval") else ""),
        ("revocation", "revocation" if content.get("skill_revocation") else ""),
        ("incident", "incident" if content.get("skill_incident") else ""),
    ):
        normalized = normalize_skill_kind(value, default="")
        if normalized:
            return normalized
    return normalize_skill_kind(
        getattr(getattr(artifact, "artifact_type", None), "value", getattr(artifact, "artifact_type", "")),
        default="knowledge",
    )


def _runtime_package_reference_for_artifact(artifact: Artifact) -> dict[str, Any]:
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    representation = str(getattr(getattr(artifact, "representation", None), "value", getattr(artifact, "representation", "")))
    executor_framework = ability_executor_framework(representation=representation, content=content)
    body_field = ""
    body_text = ""
    for candidate in ("python_script", "shell_script", "ansible_playbook", "wasm_module"):
        candidate_text = str(content.get(candidate, "")).strip()
        if candidate_text:
            body_field = candidate
            body_text = candidate_text
            break
    runtime_reference = {
        "representation": representation,
        "executor_framework": executor_framework,
        "entrypoint": collapse_ws(str(content.get("entrypoint", ""))),
    }
    if body_field:
        runtime_reference["body_field"] = body_field
        runtime_reference["body_sha256"] = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
    dependencies = _normalized_string_list(content.get("dependencies", []))
    if dependencies:
        runtime_reference["dependencies"] = dependencies
    return {key: value for key, value in runtime_reference.items() if value not in ("", [], {}, None)}


def skill_hosting_metadata_for_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like canonical skill IR projection, helps with projecting the runtime-hosting surface for one artifact without copying the full executable body.

    Reference to Theory:
        Supports canonical hosted skills by separating declaration and normalization from the concrete hosting substrate that will execute the skill.

    Example Input Output:
        Input: `skill_hosting_metadata_for_artifact(artifact)`
        Output: {'executor_framework': 'python3', 'representation': 'python_script', 'entrypoint': 'main'}

    Args:
        artifact: Value for `artifact` used by `skill_hosting_metadata_for_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `skill_hosting_metadata_for_artifact`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    hosting = dict(_runtime_package_reference_for_artifact(artifact))
    governed_host_brokers = _normalized_string_list(content.get("governed_host_brokers", []))
    if governed_host_brokers:
        hosting["governed_host_brokers"] = governed_host_brokers
    governed_authorities = _normalized_string_list(content.get("governed_authorities", []))
    if governed_authorities:
        hosting["governed_authorities"] = governed_authorities
    host_abi_version = collapse_ws(str(content.get("host_abi_version", "")))
    if host_abi_version:
        hosting["host_abi_version"] = host_abi_version
    if isinstance(content.get("virtual_mounts", {}), Mapping):
        hosting["virtual_mounts"] = sorted(
            collapse_ws(str(name))
            for name in dict(content.get("virtual_mounts", {})).keys()
            if collapse_ws(str(name))
        )
    return hosting


def canonical_skill_ir_from_artifact(artifact: Artifact) -> CanonicalSkillIR:
    """
    High Level Purpose:
        In circumstances like canonical skill import/export and future invocation unification, helps with projecting one stored artifact into the theory-backed canonical skill IR.

    Reference to Theory:
        Supports the staged skill model by keeping canonical declaration, normalization, family identity, and hosting metadata available without replacing the persisted artifact envelope.

    Example Input Output:
        Input: `canonical_skill_ir_from_artifact(artifact)`
        Output: CanonicalSkillIR(artifact_id='artifact-skill-123', title='Read Text File', ...)

    Args:
        artifact: Value for `artifact` used by `canonical_skill_ir_from_artifact`. Expected type: `Artifact`.

    Returns:
        CanonicalSkillIR: Result produced by `canonical_skill_ir_from_artifact`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    declaration = artifact_skill_declaration(artifact) or synthesized_skill_declaration_for_artifact(artifact)
    lifecycle = artifact_skill_lifecycle(artifact)
    normalization = normalized_skill_normalization_payload(content.get("skill_normalization", {}))
    if not normalization:
        normalization = synthesized_skill_normalization_for_artifact(artifact)
    title = collapse_ws(str(getattr(artifact, "title", "")))
    return CanonicalSkillIR(
        artifact_id=collapse_ws(str(getattr(artifact, "id", ""))),
        title=title,
        schema=normalize_skill_schema_version(content.get("skill_schema", "bssc_skill.v1")),
        kind=_skill_kind_from_artifact(artifact),
        declaration=dict(declaration),
        lifecycle=dict(lifecycle),
        runtime_package_reference=_runtime_package_reference_for_artifact(artifact),
        normalization=normalization,
        aliases=normalized_skill_aliases(content.get("aliases", []), title=title),
        family=normalized_skill_family_metadata(content.get("skill_family", {}), title=title),
        compatibility=normalized_skill_compatibility_payload(content.get("skill_compatibility", {})),
        hosting_metadata=skill_hosting_metadata_for_artifact(artifact),
    )


def canonical_skill_ir_dict_from_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like tests and compact reporting, helps with projecting one artifact directly into dictionary-form canonical skill IR.

    Reference to Theory:
        Supports the staged skill compiler plan by making the artifact-centered canonical skill projection easy to inspect without introducing a new persistence layer.

    Example Input Output:
        Input: `canonical_skill_ir_dict_from_artifact(artifact)`
        Output: {'artifact_id': 'artifact-skill-123', 'title': 'Read Text File'}

    Args:
        artifact: Value for `artifact` used by `canonical_skill_ir_dict_from_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `canonical_skill_ir_dict_from_artifact`.
    """
    return canonical_skill_ir_from_artifact(artifact).to_dict()
