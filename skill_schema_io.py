# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from approval_governance import (
    approval_answer_summary,
    skill_approval_from_payload,
)
from applied_theory_types import Artifact, enum_text
from artifact import (
    artifact_structured_learning_from_content,
    yaml_dump_human,
    yaml_string_list,
)
from execution_frameworks import normalize_ability_runtime_content, normalize_executor_framework_name
from host_abi import wasm_skill_abi_version
from normalize import normalize_notation_key
from semantic_text import ordered_unique
from side import artifact_from_yaml_document, load_batch_list
from skill_lifecycle import skill_lifecycle_from_payload
from skill_governance import (
    SKILL_SCHEMA_VERSION_V1,
    normalize_skill_kind,
    normalize_skill_schema_version,
    policy_answer_summary,
    skill_declaration_from_payload,
    skill_policy_from_payload,
)
from skill_boundary_normalization import (
    normalized_skill_normalization_payload,
    synthesized_skill_normalization_for_artifact,
)
from skill_compatibility_import import normalized_skill_compatibility_payload
from skill_ir import normalized_skill_aliases, normalized_skill_family_metadata
from store import build_artifact_store

SKILL_IMPORT_SCHEMA_VERSION = SKILL_SCHEMA_VERSION_V1
from skill_safety_governance import (
    incident_answer_summary,
    revocation_answer_summary,
    skill_incident_from_payload,
    skill_revocation_from_payload,
)


SKILL_GOVERNANCE_IMPORT_FIELDS = {
    "scope",
    "justification",
    "function_bit",
    "boundary_shape",
    "reusability",
    "admissibility",
    "learning_relation",
    "created_at",
    "provenance",
    "constraints",
    "template_schema",
    "related_artifact_ids",
    "structured_learning",
    "controller_features",
    "governed_authorities",
    "governed_host_brokers",
    "host_abi_version",
    "virtual_mounts",
    "named_queries",
    "skill_state_namespace",
}


class _RuntimeFacade:
    @staticmethod
    def artifact_structured_learning_from_content(artifact: Artifact) -> dict[str, Any]:
        return artifact_structured_learning_from_content(artifact)

    @staticmethod
    def build_artifact_store() -> Any:
        return build_artifact_store()

    @staticmethod
    def enum_text(value: Any) -> str:
        return enum_text(value)

    @staticmethod
    def ordered_unique(values: Any) -> list[str]:
        return ordered_unique(values)

    @staticmethod
    def yaml_dump_human(value: Any) -> str:
        return yaml_dump_human(value)

    @staticmethod
    def yaml_string_list(value: Any) -> list[str]:
        return yaml_string_list(value)


_RUNTIME_FACADE = _RuntimeFacade()


def _runtime() -> _RuntimeFacade:
    """
    High Level Purpose:
        In circumstances like skill schema hydration and exchange-surface normalization, helps with exposing one narrow compatibility facade backed by root helpers instead of importing controller/runtime composition from `main.py`.

    Reference to Theory:
        Supports the entry/exchange layer by keeping portable skill hydration aligned with canonical helper behavior while avoiding direct reach-through into the runtime composition surface.

    Example Input Output:
        Input: `_runtime()`
        Output: _RuntimeFacade()

    Args:
        None.

    Returns:
        _RuntimeFacade: Result produced by `_runtime`.
    """
    return _RUNTIME_FACADE


def stable_skill_artifact_id(title: str) -> str:
    """
    High Level Purpose:
        In circumstances like idempotent skill import based on immutable semantic titles, helps with deriving one stable artifact identifier from the title alone.

    Reference to Theory:
        Supports open governance import/export by making the portable kernel reproducible without depending on store-local ids while still preserving deterministic identity.

    Example Input Output:
        Input: `stable_skill_artifact_id(title='Physics / Force / Force From Mass And Acceleration')`
        Output: 'artifact-skill-6d20b0a4d6c0'

    Args:
        title: Value for `title` used by `stable_skill_artifact_id`. Expected type: `str`.

    Returns:
        str: Result produced by `stable_skill_artifact_id`.
    """
    normalized = normalize_notation_key(title)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"artifact-skill-{digest}"


def yaml_skill_top_level_document(document: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like loading portable skill YAML documents, helps with validating that each document is a non-empty top-level mapping with an explicit title.

    Reference to Theory:
        Supports the exchange layer by keeping the portable skill schema explicit and bounded before any governance or persistence logic runs.

    Example Input Output:
        Input: `yaml_skill_top_level_document(document={'schema': 'bssc_skill.v1', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'})`
        Output: {'schema': 'bssc_skill.v1', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'}

    Args:
        document: Value for `document` used by `yaml_skill_top_level_document`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `yaml_skill_top_level_document`.
    """
    if not isinstance(document, Mapping) or not document:
        raise ValueError("Skill YAML must be a non-empty mapping.")
    payload = {str(key): value for key, value in document.items()}
    title = str(payload.get("title", "")).strip()
    if not title:
        raise ValueError("Skill YAML requires a non-empty top-level `title`.")
    return payload


def _yaml_string_list(value: Any) -> list[str]:
    """
    High Level Purpose:
        In circumstances like skill schema normalization, helps with converting one YAML field into a clean string list through the shared runtime rules.

    Reference to Theory:
        Supports exchange-layer normalization by preserving one consistent list-shaping rule across skill import and export.

    Example Input Output:
        Input: `_yaml_string_list(value=['python3', ' bash '])`
        Output: ['python3', 'bash']

    Args:
        value: Value for `value` used by `_yaml_string_list`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `_yaml_string_list`.
    """
    return yaml_string_list(value)


def _normalized_contract(value: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like loading skill input and output contracts from YAML, helps with normalizing one loose mapping into a compact canonical contract surface.

    Reference to Theory:
        Supports exchange-layer portability by keeping schema hydration tolerant of human-authored YAML while still producing canonical runtime contracts.

    Example Input Output:
        Input: `_normalized_contract(value={'mass': 'number', 'units': ['kg', 'g']})`
        Output: {'mass': 'number', 'units': ['kg', 'g']}

    Args:
        value: Value for `value` used by `_normalized_contract`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `_normalized_contract`.
    """
    if not isinstance(value, Mapping):
        return {}
    normalized: dict[str, Any] = {}
    for key, raw in value.items():
        key_text = str(key or "").strip()
        if not key_text:
            continue
        if isinstance(raw, list):
            items = [str(item).strip() for item in raw if str(item).strip()]
            if items:
                normalized[key_text] = items
            continue
        raw_text = str(raw).strip()
        if raw_text:
            normalized[key_text] = raw_text
    return normalized


def _contract_entries(contract: Mapping[str, Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like hydrating a portable skill document into the legacy artifact envelope, helps with rendering one contract mapping into the legacy line-oriented `In` and `Out` entry shape.

    Reference to Theory:
        Supports exchange-layer compatibility by preserving one bounded bridge between the portable skill kernel and the older artifact YAML surface.

    Example Input Output:
        Input: `_contract_entries(contract={'mass': 'number', 'units': ['kg', 'g']})`
        Output: ['mass: number', 'units: kg', 'units: g']

    Args:
        contract: Value for `contract` used by `_contract_entries`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[str]: Result produced by `_contract_entries`.
    """
    entries: list[str] = []
    for key, value in contract.items():
        if isinstance(value, list):
            entries.extend(f"{key}: {item}" for item in value if str(item).strip())
            continue
        value_text = str(value).strip()
        if value_text:
            entries.append(f"{key}: {value_text}")
    return entries


def _skill_executor_and_body(payload: Mapping[str, Any]) -> tuple[str, str]:
    """
    High Level Purpose:
        In circumstances like ability-skill hydration, helps with resolving the single declared executor framework together with its executable body field.

    Reference to Theory:
        Supports portable skill exchange by ensuring an ability document has one coherent executor/body pairing before it becomes a runtime artifact.

    Example Input Output:
        Input: `_skill_executor_and_body(payload={'executor': 'python3', 'python': 'def main():\\n    return 1'})`
        Output: ('python3', 'def main():\\n    return 1')

    Args:
        payload: Value for `payload` used by `_skill_executor_and_body`. Expected type: `Mapping[str, Any]`.

    Returns:
        tuple[str, str]: Result produced by `_skill_executor_and_body`.
    """
    executor = normalize_executor_framework_name(payload.get("executor", ""))
    body_pairs = [
        ("python3", "python", str(payload.get("python", "")).strip()),
        ("bash", "shell", str(payload.get("shell", "")).strip()),
        ("ansible", "ansible", str(payload.get("ansible", "")).strip()),
        ("wasm_wasi", "wasm", str(payload.get("wasm", "")).strip()),
    ]
    detected = [(framework, field_name, body) for framework, field_name, body in body_pairs if body]
    if executor:
        for framework, _field_name, body in detected:
            if framework == executor:
                return framework, body
        if detected:
            raise ValueError("Skill YAML executor does not match the supplied executable body field.")
        raise ValueError("Ability skill YAML requires a matching executable body field.")
    if len(detected) == 1:
        framework, _field_name, body = detected[0]
        return framework, body
    if len(detected) > 1:
        raise ValueError("Ability skill YAML must not provide multiple executable body fields.")
    return "", ""


def _legacy_artifact_document_from_skill(payload: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like hydrating a portable skill document into the canonical artifact model, helps with producing the bounded legacy artifact YAML shape expected by the existing artifact loader.

    Reference to Theory:
        Supports exchange-layer compatibility by turning the portable skill kernel plus governance envelope into the canonical artifact hydration path without bypassing the existing artifact schema.

    Example Input Output:
        Input: `_legacy_artifact_document_from_skill(payload={'schema': 'bssc_skill.v2', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'})`
        Output: {'What Is Force?': {'Description': [...], 'Metadata': {...}}}

    Args:
        payload: Value for `payload` used by `_legacy_artifact_document_from_skill`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_legacy_artifact_document_from_skill`.
    """
    title = str(payload.get("title", "")).strip()
    schema = normalize_skill_schema_version(payload.get("schema", SKILL_IMPORT_SCHEMA_VERSION))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    question = str(payload.get("question", "")).strip()
    answer = str(payload.get("answer", "")).strip()
    description_entries = _yaml_string_list(payload.get("description", []))
    fallback_inputs = _normalized_contract(payload.get("inputs", {}))
    fallback_outputs = _normalized_contract(payload.get("outputs", {}))
    explicit_inputs = "inputs" in payload
    explicit_outputs = "outputs" in payload
    governance = dict(payload.get("governance", {})) if isinstance(payload.get("governance", {}), Mapping) else {}
    compatibility = normalized_skill_compatibility_payload(payload.get("compatibility", {}))
    executor_framework = ""
    body = ""
    if kind == "ability":
        executor_framework, body = _skill_executor_and_body(payload)
    declaration = skill_declaration_from_payload(
        payload,
        kind=kind,
        fallback_inputs=fallback_inputs,
        fallback_outputs=fallback_outputs,
        executor_framework=executor_framework,
    )
    policy = skill_policy_from_payload(payload)
    approval = skill_approval_from_payload(payload)
    revocation = skill_revocation_from_payload(payload)
    incident = skill_incident_from_payload(payload)
    if kind == "ability":
        inputs = (
            fallback_inputs
            if explicit_inputs
            else (declaration.get("inputs", fallback_inputs) if declaration else fallback_inputs)
        )
        outputs = (
            fallback_outputs
            if explicit_outputs
            else (declaration.get("outputs", fallback_outputs) if declaration else fallback_outputs)
        )
    else:
        inputs = declaration.get("inputs", fallback_inputs) if declaration else fallback_inputs
        outputs = declaration.get("outputs", fallback_outputs) if declaration else fallback_outputs

    metadata: dict[str, Any] = {
        "artifact_id": stable_skill_artifact_id(title),
        "artifact_type": "knowledge" if kind in {"policy", "approval", "revocation", "incident"} else enum_text(kind),
    }
    if question:
        metadata["question"] = question
    content = dict(metadata.get("content", {})) if isinstance(metadata.get("content", {}), Mapping) else {}
    content["skill_schema"] = schema
    content["skill_kind"] = kind
    if declaration:
        content["skill_declaration"] = declaration
    if policy:
        content["skill_policy"] = policy
    if approval:
        content["skill_approval"] = approval
    if revocation:
        content["skill_revocation"] = revocation
    if incident:
        content["skill_incident"] = incident
    if kind == "knowledge":
        if not answer:
            raise ValueError("Knowledge skill YAML requires a non-empty `answer`.")
        metadata["answer"] = answer
    elif kind == "ability":
        compatibility_only_ability = bool(compatibility) and not executor_framework and not body
        if not executor_framework and not body and not compatibility_only_ability:
            raise ValueError("Ability skill YAML requires one executable body field among `python`, `shell`, or `ansible`.")
        if executor_framework and not body:
            raise ValueError("Ability skill YAML requires a matching executable body field.")
        if not compatibility_only_ability and (not executor_framework or not body):
            raise ValueError("Ability skill YAML requires one executable body field among `python`, `shell`, or `ansible`.")
        if not compatibility_only_ability:
            metadata["representation"] = {
                "python3": "python_script",
                "bash": "shell_script",
                "ansible": "ansible_playbook",
                "wasm_wasi": "wasm_module",
            }[executor_framework]
            metadata["executor_framework"] = executor_framework
            metadata["script_language"] = (
                "python"
                if executor_framework == "python3"
                else "wasm"
                if executor_framework == "wasm_wasi"
                else executor_framework
            )
            metadata["entrypoint"] = str(payload.get("entrypoint", "")).strip() or (
                "main"
                if executor_framework == "python3"
                else "playbook"
                if executor_framework == "ansible"
                else "run"
                if executor_framework == "wasm_wasi"
                else "main"
            )
            if executor_framework == "python3":
                metadata["python_script"] = body
            elif executor_framework == "bash":
                metadata["shell_script"] = body
            elif executor_framework == "wasm_wasi":
                metadata["wasm_module"] = body
                metadata["wasm_abi_version"] = str(payload.get("wasm_abi_version", "")).strip() or wasm_skill_abi_version()
                metadata["wasm_format"] = str(payload.get("wasm_format", "")).strip() or "wat"
            else:
                metadata["ansible_playbook"] = body
        dependencies = _yaml_string_list(payload.get("dependencies", []))
        if dependencies:
            metadata["dependencies"] = dependencies
        if inputs:
            metadata["input_contract"] = inputs
        if outputs:
            metadata["output_contract"] = outputs
    elif kind == "policy":
        if not policy:
            raise ValueError("Policy skill YAML requires a non-empty `policy` block under schema v2.")
        metadata["answer"] = policy_answer_summary(policy)
    elif kind == "approval":
        if not approval:
            raise ValueError("Approval skill YAML requires a non-empty `approval` block under schema v2.")
        metadata["answer"] = approval_answer_summary(approval)
    elif kind == "revocation":
        if not revocation:
            raise ValueError("Revocation skill YAML requires a non-empty `revocation` block under schema v2.")
        metadata["answer"] = revocation_answer_summary(revocation)
    elif kind == "incident":
        if not incident:
            raise ValueError("Incident skill YAML requires a non-empty `incident` block under schema v2.")
        metadata["answer"] = incident_answer_summary(incident)
    else:
        if answer:
            metadata["answer"] = answer

    if description_entries:
        description = description_entries
    elif kind == "knowledge" and answer:
        description = [f"Knowledge skill for: {title}"]
    elif kind == "ability":
        description = ["Executable skill artifact."]
    elif kind == "policy":
        description = ["Governed policy artifact for skill admission and invocation."]
    elif kind == "approval":
        description = ["Governed approval artifact for skill admission and invocation."]
    elif kind == "revocation":
        description = ["Governed revocation artifact for current-use lifecycle denial and trust withdrawal."]
    elif kind == "incident":
        description = ["Governed incident artifact for current-use restriction, suspension, or quarantine."]
    else:
        description = []

    metadata.update(
        {
            key: value
            for key, value in governance.items()
            if key in SKILL_GOVERNANCE_IMPORT_FIELDS
        }
    )
    if isinstance(governance.get("virtual_mounts"), Mapping):
        content["virtual_mounts"] = dict(governance.get("virtual_mounts", {}))
    if isinstance(governance.get("named_queries"), Mapping):
        content["named_queries"] = dict(governance.get("named_queries", {}))
    host_abi = str(governance.get("host_abi_version", "")).strip()
    if host_abi:
        content["host_abi_version"] = host_abi
    skill_state_namespace = str(governance.get("skill_state_namespace", "")).strip()
    if skill_state_namespace:
        content["skill_state_namespace"] = skill_state_namespace
    if isinstance(governance.get("related_titles"), list):
        related_titles = [str(item).strip() for item in governance.get("related_titles", []) if str(item).strip()]
        if related_titles:
            content["related_titles"] = related_titles
    aliases = normalized_skill_aliases(payload.get("aliases", []), title=title)
    if aliases:
        content["aliases"] = aliases
    family = normalized_skill_family_metadata(payload.get("family", {}), title=title)
    if family:
        content["skill_family"] = family
    normalization = normalized_skill_normalization_payload(payload.get("normalization", {}))
    if normalization:
        content["skill_normalization"] = normalization
    if compatibility:
        content["skill_compatibility"] = compatibility
    if content:
        metadata["content"] = content

    return {
        title: {
            "Description": description,
            "In": _contract_entries(inputs),
            "Out": _contract_entries(outputs) if outputs else ([answer] if kind in {"knowledge", "policy", "approval", "revocation", "incident"} and answer else []),
            "Metadata": metadata,
        }
    }


def artifact_from_skill_document(document: Any) -> Artifact:
    """
    High Level Purpose:
        In circumstances like importing the smaller skill-facing YAML interface, helps with hydrating a portable skill document into the canonical in-memory artifact form.

    Reference to Theory:
        Supports open governance import/export by separating a minimal skill kernel from the richer artifact envelope while preserving one canonical hydration path.

    Example Input Output:
        Input: `artifact_from_skill_document(document={'schema': 'bssc_skill.v1', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'})`
        Output: Artifact(id='artifact-skill-6d20b0a4d6c0', title='What Is Force?', artifact_type='knowledge', representation='yaml')

    Args:
        document: Value for `document` used by `artifact_from_skill_document`. Expected type: `Any`.

    Returns:
        Artifact: Result produced by `artifact_from_skill_document`.
    """
    payload = yaml_skill_top_level_document(document)
    legacy_document = _legacy_artifact_document_from_skill(payload)
    artifact = artifact_from_yaml_document(legacy_document)
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if kind == "ability":
        if "inputs" in payload:
            content["input_contract"] = _normalized_contract(payload.get("inputs", {}))
        if "outputs" in payload:
            content["output_contract"] = _normalized_contract(payload.get("outputs", {}))
    admission = dict(content.get("skill_admission", {})) if isinstance(content.get("skill_admission", {}), Mapping) else {}
    raw_lifecycle = payload.get("lifecycle", {})
    if (
        isinstance(raw_lifecycle, Mapping)
        and raw_lifecycle
    ) or admission or bool(content.get("skill_policy")):
        content["skill_lifecycle"] = skill_lifecycle_from_payload(
            payload,
            admission_status=str(admission.get("status", "")),
            policy_record=bool(content.get("skill_policy")),
            default_updated_at=str(admission.get("evaluated_at", content.get("created_at", ""))),
        )
    if not isinstance(content.get("skill_normalization", {}), Mapping) or not dict(content.get("skill_normalization", {})):
        content["skill_normalization"] = synthesized_skill_normalization_for_artifact(artifact)
    else:
        content["skill_normalization"] = normalized_skill_normalization_payload(content.get("skill_normalization", {}))
    if kind == "ability":
        content = normalize_ability_runtime_content(content, title=str(getattr(artifact, "title", "")))
    artifact.content = content
    return artifact


def load_skill_yaml_documents(path: Path) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like batch skill import and replay hydration, helps with loading one or more portable skill YAML documents from disk into canonical artifacts.

    Reference to Theory:
        Supports exchange-layer portability by making the external skill schema loadable without mixing CLI or installation concerns into the caller.

    Example Input Output:
        Input: `load_skill_yaml_documents(path=Path('/tmp/skills.yaml'))`
        Output: [Artifact(id='artifact-skill-6d20b0a4d6c0', title='What Is Force?', artifact_type='knowledge', representation='yaml')]

    Args:
        path: Value for `path` used by `load_skill_yaml_documents`. Expected type: `Path`.

    Returns:
        list[Artifact]: Result produced by `load_skill_yaml_documents`.
    """
    documents = load_skill_yaml_payload_documents(path)
    return [artifact_from_skill_document(document) for document in documents]


def load_skill_yaml_payload_documents(path: Path) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like governed skill import and replay verification, helps with loading raw top-level skill payloads so admission and installation code can inspect declarations before persistence.

    Reference to Theory:
        Supports exchange-layer correctness by preserving the external skill document surface long enough for governance-aware callers to evaluate it explicitly.

    Example Input Output:
        Input: `load_skill_yaml_payload_documents(path=Path('/tmp/skills.yaml'))`
        Output: [{'schema': 'bssc_skill.v2', 'kind': 'ability', 'title': 'Open Browser URL'}]

    Args:
        path: Value for `path` used by `load_skill_yaml_payload_documents`. Expected type: `Path`.

    Returns:
        list[dict[str, Any]]: Result produced by `load_skill_yaml_payload_documents`.
    """
    documents = list(yaml.safe_load_all(path.read_text()))
    payloads: list[dict[str, Any]] = []
    for document in documents:
        if document in (None, "", [], {}):
            continue
        payloads.append(yaml_skill_top_level_document(document))
    return payloads


def resolve_import_skill_files(args: argparse.Namespace) -> list[Path]:
    """
    High Level Purpose:
        In circumstances like batch skill import, helps with resolving skill YAML files from direct flags, a batch file, or a directory.

    Reference to Theory:
        Supports the exchange layer by making the portable skill kernel loadable from one or many source files without giving callers store or governance responsibilities.

    Example Input Output:
        Input: `resolve_import_skill_files(args=Namespace(skill_file=[Path('/tmp/skill.yaml')], skill_files_file=None, skill_dir=None))`
        Output: [Path('/tmp/skill.yaml')]

    Args:
        args: Value for `args` used by `resolve_import_skill_files`. Expected type: `argparse.Namespace`.

    Returns:
        list[Path]: Result produced by `resolve_import_skill_files`.
    """
    files: list[Path] = []
    for path in getattr(args, "skill_file", []) or []:
        files.append(Path(path))
    if getattr(args, "skill_files_file", None):
        files.extend(Path(item) for item in load_batch_list(args.skill_files_file, object_key="skill_files"))
    if getattr(args, "skill_dir", None):
        files.extend(
            sorted(
                path
                for path in Path(args.skill_dir).iterdir()
                if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
            )
        )
    return [Path(item) for item in ordered_unique(str(path.resolve()) for path in files if str(path).strip())]


def normalized_skill_bundle_filename_for_source(path: Path) -> str:
    """
    High Level Purpose:
        In circumstances like writing normalized outputs for imported skill bundles, helps with deriving a stable YAML bundle filename from the source path.

    Reference to Theory:
        Supports exchange-layer determinism by giving normalized skill exports one file naming rule independent of the caller.

    Example Input Output:
        Input: `normalized_skill_bundle_filename_for_source(path=Path('/tmp/skills.yml'))`
        Output: 'skills.yml'

    Args:
        path: Value for `path` used by `normalized_skill_bundle_filename_for_source`. Expected type: `Path`.

    Returns:
        str: Result produced by `normalized_skill_bundle_filename_for_source`.
    """
    return path.name if path.suffix.lower() in {".yaml", ".yml"} else f"{path.name}.yaml"


def batch_skill_export_filename(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like batch skill export into a directory, helps with deriving a deterministic safe filename from the immutable skill title without depending on store-local ids.

    Reference to Theory:
        Supports open governance import/export by making title-based skill identity portable and idempotent across stores and runs.

    Example Input Output:
        Input: `batch_skill_export_filename(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='knowledge', representation='yaml'))`
        Output: 'artifact-skill-6d20b0a4d6c0.yaml'

    Args:
        artifact: Value for `artifact` used by `batch_skill_export_filename`. Expected type: `Artifact`.

    Returns:
        str: Result produced by `batch_skill_export_filename`.
    """
    return f"{stable_skill_artifact_id(artifact.title)}.yaml"
