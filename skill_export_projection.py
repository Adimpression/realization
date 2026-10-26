# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from realized_core_governance.approval import (
    artifact_is_approval_record,
    artifact_skill_approval,
)
from applied_theory_types import ABILITY_SCRIPT_DEPENDENCIES, Artifact
from host_abi import host_abi_version, wasm_skill_abi_version
from realized_core_governance.lifecycle import artifact_skill_lifecycle
from realized_core_governance.records import (
    artifact_is_policy_record,
    artifact_skill_admission,
    artifact_skill_declaration,
    artifact_skill_policy,
)
from side import artifact_export_description, load_batch_list
from skill_governance import (
    SKILL_RISK_TIERS,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
    synthesized_skill_declaration_for_artifact,
)
from realized_core_governance.safety import (
    artifact_is_incident_record,
    artifact_is_revocation_record,
    artifact_skill_incident,
    artifact_skill_revocation,
)
from skill_schema_io import _runtime, _yaml_string_list, stable_skill_artifact_id
from realized_skill_semantics.declaration import (
    SKILL_SCHEMA_VERSION_V2,
    normalize_skill_schema_version,
)
from realized_skill_semantics.execution import (
    ability_executable_text,
    ability_executor_framework,
    normalize_executor_framework_name,
)
from realized_skill_semantics.normalization import normalized_skill_normalization_payload
from skill_boundary_normalization import synthesized_skill_normalization_for_artifact
from skill_compatibility_import import normalized_skill_compatibility_payload
from skill_ir import canonical_skill_ir_from_artifact


SKILL_EXPORT_SCHEMA_VERSION = SKILL_SCHEMA_VERSION_V2


def _skill_governance_from_artifact(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like projecting one canonical artifact into the portable skill export surface, helps with gathering the optional governance envelope that should travel with the compact skill kernel.

    Reference to Theory:
        Supports open governance export by preserving scope, lifecycle-bearing context, host ABI hints, and other governance-relevant fields without forcing them into the minimal kernel.

    Example Input Output:
        Input: `_skill_governance_from_artifact(artifact=Artifact(id='artifact-browser', title='Open Browser URL', artifact_type='ability', representation='python_script'))`
        Output: {'scope': 'device automation', 'governed_authorities': ['execute'], 'host_abi_version': 'bssc.host.v1'}

    Args:
        artifact: Value for `artifact` used by `_skill_governance_from_artifact`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `_skill_governance_from_artifact`.
    """
    runtime = _runtime()
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    structured = runtime.artifact_structured_learning_from_content(artifact)
    governance: dict[str, Any] = {
        "scope": artifact.scope,
        "justification": artifact.justification,
        "function_bit": artifact.function_bit,
        "boundary_shape": [term.value for term in artifact.boundary_shape],
        "reusability": runtime.enum_text(artifact.reusability),
        "admissibility": runtime.enum_text(artifact.admissibility),
        "learning_relation": runtime.enum_text(artifact.learning_relation),
        "created_at": artifact.created_at,
    }
    if artifact.provenance:
        governance["provenance"] = list(artifact.provenance)
    if artifact.constraints:
        governance["constraints"] = list(artifact.constraints)
    if artifact.template_schema:
        governance["template_schema"] = artifact.template_schema
    if artifact.related_artifact_ids:
        governance["related_artifact_ids"] = list(artifact.related_artifact_ids)
    if structured:
        governance["structured_learning"] = structured
    if isinstance(content.get("controller_features"), Mapping):
        governance["controller_features"] = dict(content.get("controller_features", {}))
    if isinstance(content.get("governed_authorities"), list):
        authorities = _yaml_string_list(content.get("governed_authorities", []))
        if authorities:
            governance["governed_authorities"] = authorities
    if isinstance(content.get("governed_host_brokers"), list):
        broker_names = _yaml_string_list(content.get("governed_host_brokers", []))
        if broker_names:
            governance["governed_host_brokers"] = broker_names
            governance["host_abi_version"] = str(content.get("host_abi_version", "")).strip() or host_abi_version()
    if isinstance(content.get("virtual_mounts"), Mapping):
        governance["virtual_mounts"] = dict(content.get("virtual_mounts", {}))
    if isinstance(content.get("named_queries"), Mapping):
        governance["named_queries"] = dict(content.get("named_queries", {}))
    skill_state_namespace = str(content.get("skill_state_namespace", "")).strip()
    if skill_state_namespace:
        governance["skill_state_namespace"] = skill_state_namespace
    return governance


def skill_export_document(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting a stored artifact through the smaller skill-facing interface, helps with projecting the canonical artifact into a minimal portable kernel plus optional governance envelope.

    Reference to Theory:
        Supports open governance import/export by making the skill kernel compact while preserving an audit-complete envelope for adopters that want it.

    Example Input Output:
        Input: `skill_export_document(artifact=Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml'))`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'knowledge', 'title': 'What Is Force?', 'answer': 'F = m * a'}

    Args:
        artifact: Value for `artifact` used by `skill_export_document`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `skill_export_document`.
    """
    runtime = _runtime()
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    policy = artifact_skill_policy(artifact)
    approval = artifact_skill_approval(artifact)
    revocation = artifact_skill_revocation(artifact)
    incident = artifact_skill_incident(artifact)
    admission = artifact_skill_admission(artifact)
    skill_kind = (
        "policy"
        if policy
        else "approval"
        if approval
        else "revocation"
        if revocation
        else "incident"
        if incident
        else normalize_skill_kind(runtime.enum_text(artifact.artifact_type), default=runtime.enum_text(artifact.artifact_type))
    )
    declaration = (
        artifact_skill_declaration(artifact) or synthesized_skill_declaration_for_artifact(artifact)
        if skill_kind not in {"policy", "approval", "revocation", "incident"}
        else {}
    )
    schema = (
        normalize_skill_schema_version(content.get("skill_schema", SKILL_EXPORT_SCHEMA_VERSION))
        if policy
        else SKILL_EXPORT_SCHEMA_VERSION
    )
    artifact_type = runtime.enum_text(artifact.artifact_type)
    document: dict[str, Any] = {
        "schema": schema,
        "kind": skill_kind,
        "title": artifact.title,
    }

    description = artifact_export_description(artifact)
    if description:
        document["description"] = description

    question = str(content.get("question", "")).strip()
    if question and skill_kind != "policy":
        document["question"] = question

    if declaration and schema == SKILL_SCHEMA_VERSION_V2:
        document["declaration"] = declaration
    if policy and schema == SKILL_SCHEMA_VERSION_V2:
        document["policy"] = policy
    if approval and schema == SKILL_SCHEMA_VERSION_V2:
        document["approval"] = approval
    if revocation and schema == SKILL_SCHEMA_VERSION_V2:
        document["revocation"] = revocation
    if incident and schema == SKILL_SCHEMA_VERSION_V2:
        document["incident"] = incident
    if admission and schema == SKILL_SCHEMA_VERSION_V2 and skill_kind not in {"policy", "approval", "revocation", "incident"}:
        document["admission"] = admission
    lifecycle = artifact_skill_lifecycle(artifact)
    if lifecycle and schema == SKILL_SCHEMA_VERSION_V2:
        document["lifecycle"] = lifecycle

    if skill_kind in {"policy", "approval", "revocation", "incident"}:
        pass
    elif artifact_type == "knowledge":
        answer = str(content.get("answer", "")).strip()
        if answer:
            document["answer"] = answer
    elif artifact_type == "ability":
        executor = ability_executor_framework(
            representation=runtime.enum_text(artifact.representation),
            content=content,
        )
        if executor:
            document["executor"] = executor
        entrypoint = str(content.get("entrypoint", "")).strip()
        if entrypoint:
            document["entrypoint"] = entrypoint
        input_contract = dict(content.get("input_contract", {})) if isinstance(content.get("input_contract", {}), Mapping) else {}
        output_contract = dict(content.get("output_contract", {})) if isinstance(content.get("output_contract", {}), Mapping) else {}
        document["inputs"] = input_contract
        if output_contract:
            document["outputs"] = output_contract
        dependencies = _yaml_string_list(content.get("dependencies", []))
        if dependencies:
            filtered_dependencies = [
                dependency
                for dependency in dependencies
                if dependency not in ABILITY_SCRIPT_DEPENDENCIES
            ]
            if filtered_dependencies:
                document["dependencies"] = filtered_dependencies
        python_script = str(content.get("python_script", "")).strip()
        shell_script = str(content.get("shell_script", "")).strip()
        ansible_playbook = str(content.get("ansible_playbook", "")).strip()
        wasm_module = str(content.get("wasm_module", "")).strip()
        if python_script:
            document["python"] = python_script
        if shell_script:
            document["shell"] = shell_script
        if ansible_playbook:
            document["ansible"] = ansible_playbook
        if wasm_module:
            document["wasm"] = wasm_module
            document["wasm_abi_version"] = str(content.get("wasm_abi_version", "")).strip() or wasm_skill_abi_version()
            document["wasm_format"] = str(content.get("wasm_format", "")).strip() or "wat"
    else:
        answer = str(content.get("answer", "")).strip()
        if answer:
            document["answer"] = answer

    governance = _skill_governance_from_artifact(artifact)
    if governance:
        document["governance"] = governance
    canonical_ir = canonical_skill_ir_from_artifact(artifact)
    if canonical_ir.aliases:
        document["aliases"] = list(canonical_ir.aliases)
    if canonical_ir.family:
        document["family"] = dict(canonical_ir.family)
    if canonical_ir.hosting_metadata:
        document["hosting_metadata"] = dict(canonical_ir.hosting_metadata)
    compatibility = normalized_skill_compatibility_payload(content.get("skill_compatibility", {}))
    if compatibility:
        document["compatibility"] = compatibility
    normalization = normalized_skill_normalization_payload(content.get("skill_normalization", {}))
    if not normalization and skill_kind not in {"policy", "approval", "revocation", "incident"}:
        normalization = synthesized_skill_normalization_for_artifact(artifact)
    if normalization:
        document["normalization"] = normalization
    return document


def artifact_is_skill_exportable(artifact: Artifact) -> bool:
    """
    High Level Purpose:
        In circumstances like exporting portable skill bundles for fresh-system installation, helps with deciding whether one stored artifact survives the compact skill interface without depending on richer internal artifact semantics.

    Reference to Theory:
        Supports open governance import/export by keeping the skill-facing interface limited to portable, installable kernels rather than every internal artifact residue shape.

    Example Input Output:
        Input: `artifact_is_skill_exportable(artifact=Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml'))`
        Output: True

    Args:
        artifact: Value for `artifact` used by `artifact_is_skill_exportable`. Expected type: `Artifact`.

    Returns:
        bool: Result produced by `artifact_is_skill_exportable`.
    """
    runtime = _runtime()
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    if artifact_is_policy_record(artifact) or artifact_is_approval_record(artifact) or artifact_is_revocation_record(artifact) or artifact_is_incident_record(artifact):
        return True
    artifact_type = runtime.enum_text(artifact.artifact_type)
    if artifact_type == "ability":
        if ability_executable_text(
            representation=runtime.enum_text(artifact.representation),
            content=content,
        ):
            return True
        return bool(normalized_skill_compatibility_payload(content.get("skill_compatibility", {})))
    if artifact_type == "knowledge":
        return bool(str(content.get("answer", "")).strip())
    return False


def synthesized_bundle_policy_document(documents: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like exporting one multi-skill bundle that should import cleanly on a fresh governed store, helps with synthesizing a local admission policy that admits the packaged non-governance skills.

    Reference to Theory:
        Supports open governance import/export by making a portable bundle self-contained under v2 admission rules instead of relying on some external preinstalled policy.

    Example Input Output:
        Input: `synthesized_bundle_policy_document(documents=[{'schema': 'bssc_skill.v2', 'kind': 'ability', 'title': 'Open Browser URL', 'executor': 'python3', 'declaration': {...}}])`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'policy', 'title': 'Local Bundle Admission Policy / 6d20b0a4d6c0', 'policy': {...}}

    Args:
        documents: Value for `documents` used by `synthesized_bundle_policy_document`. Expected type: `Iterable[Mapping[str, Any]]`.

    Returns:
        dict[str, Any]: Result produced by `synthesized_bundle_policy_document`.
    """
    runtime = _runtime()
    doc_list = [dict(document) for document in documents if isinstance(document, Mapping)]
    non_governance = [
        document
        for document in doc_list
        if normalize_skill_kind(document.get("kind", "")) not in {"policy", "approval", "revocation", "incident"}
    ]
    if not non_governance:
        return {}

    risk_index = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}
    target_kinds = runtime.ordered_unique(
        normalize_skill_kind(document.get("kind", ""), default="knowledge")
        for document in non_governance
    )
    allowed_authorities: list[str] = []
    allowed_executors: list[str] = []
    allowed_data_classes: list[str] = []
    max_risk_tier = "tier0_readonly"
    titles: list[str] = []
    for document in non_governance:
        title = str(document.get("title", "")).strip()
        if title:
            titles.append(title)
        declaration = dict(document.get("declaration", {})) if isinstance(document.get("declaration", {}), Mapping) else {}
        allowed_authorities.extend(normalize_skill_authorities(declaration.get("authorities_requested", [])))
        executor = normalize_executor_framework_name(document.get("executor", ""))
        if executor:
            allowed_executors.append(executor)
        allowed_data_classes.extend(_yaml_string_list(declaration.get("data_classes_touched", [])))
        risk_tier = normalize_skill_risk_tier(declaration.get("risk_tier", max_risk_tier), default=max_risk_tier)
        if risk_index.get(risk_tier, 0) > risk_index.get(max_risk_tier, 0):
            max_risk_tier = risk_tier

    bundle_hash = hashlib.sha256("||".join(sorted(titles)).encode("utf-8")).hexdigest()[:12]
    policy: dict[str, Any] = {
        "intent": "Admit the governed skills packaged in this bundle on a fresh system.",
        "target_kinds": list(target_kinds),
        "max_risk_tier": max_risk_tier,
        "allowed_authorities": runtime.ordered_unique(allowed_authorities),
        "denied_authorities": [],
        "allowed_executors": runtime.ordered_unique(item for item in allowed_executors if item),
        "required_approval_for_risk_tiers": {},
    }
    normalized_data_classes = runtime.ordered_unique(item for item in allowed_data_classes if str(item).strip())
    if normalized_data_classes:
        policy["allowed_data_classes"] = list(normalized_data_classes)
    return {
        "schema": SKILL_SCHEMA_VERSION_V2,
        "kind": "policy",
        "title": f"Local Bundle Admission Policy / {bundle_hash}",
        "policy": policy,
    }


def export_skill_text(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like skill export and batch transfer workflows, helps with rendering one artifact as the compact skill-facing YAML representation.

    Reference to Theory:
        Supports open governance import/export by exposing the portable skill kernel and optional governance envelope as a human-readable schema.

    Example Input Output:
        Input: `export_skill_text(artifact=Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml'))`
        Output: 'schema: bssc_skill.v2\\nkind: knowledge\\ntitle: What Is Force?\\n...'

    Args:
        artifact: Value for `artifact` used by `export_skill_text`. Expected type: `Artifact`.

    Returns:
        str: Result produced by `export_skill_text`.
    """
    runtime = _runtime()
    return runtime.yaml_dump_human(skill_export_document(artifact)) + "\n"


def export_skill_bundle_text(artifacts: Iterable[Artifact]) -> str:
    """
    High Level Purpose:
        In circumstances like batch skill export, helps with rendering several artifacts into one multi-document skill YAML bundle.

    Reference to Theory:
        Supports open governance import/export by making the portable skill kernel transferable in batches without losing governance envelopes.

    Example Input Output:
        Input: `export_skill_bundle_text(artifacts=[Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml')])`
        Output: 'schema: bssc_skill.v2\\nkind: knowledge\\ntitle: What Is Force?\\n...'

    Args:
        artifacts: Value for `artifacts` used by `export_skill_bundle_text`. Expected type: `Iterable[Artifact]`.

    Returns:
        str: Result produced by `export_skill_bundle_text`.
    """
    exportable_artifacts = [artifact for artifact in artifacts if artifact_is_skill_exportable(artifact)]
    documents = [skill_export_document(artifact) for artifact in exportable_artifacts]
    normalized_documents: list[dict[str, Any]] = []
    for document in documents:
        if not isinstance(document, Mapping):
            continue
        normalized_document = dict(document)
        kind = normalize_skill_kind(normalized_document.get("kind", ""))
        if kind not in {"policy", "approval", "revocation", "incident"}:
            normalized_document.pop("admission", None)
            normalized_document.pop("lifecycle", None)
        normalized_documents.append(normalized_document)
    documents = normalized_documents
    if documents and not any(normalize_skill_kind(document.get("kind", "")) == "policy" for document in documents):
        bundle_policy = synthesized_bundle_policy_document(documents)
        if bundle_policy:
            documents = [bundle_policy, *documents]
    serialized_documents = [
        _runtime().yaml_dump_human(document).rstrip()
        for document in documents
        if isinstance(document, Mapping) and document
    ]
    serialized = [document for document in serialized_documents if document]
    if not serialized:
        return ""
    return "\n---\n".join(serialized) + "\n"


def _load_all_artifacts_by_title(store: Any) -> dict[str, Artifact]:
    """
    High Level Purpose:
        In circumstances like title-oriented batch skill export, helps with indexing the artifact store by immutable semantic title once so requested exports can resolve efficiently.

    Reference to Theory:
        Supports open governance export by using title identity as the stable external selector without forcing repeated full-store scans for each requested title.

    Example Input Output:
        Input: `_load_all_artifacts_by_title(store=artifact_store)`
        Output: {'What Is Force?': Artifact(id='artifact-force', title='What Is Force?', artifact_type='knowledge', representation='yaml')}

    Args:
        store: Value for `store` used by `_load_all_artifacts_by_title`. Expected type: `Any`.

    Returns:
        dict[str, Artifact]: Result produced by `_load_all_artifacts_by_title`.
    """
    artifacts = store.load_all_artifacts()
    return {
        str(artifact.title).strip(): artifact
        for artifact in artifacts
        if str(artifact.title).strip()
    }


def skill_kind_from_artifact(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like governed skill export and installation reporting, helps with deriving the effective portable skill kind from one canonical artifact.

    Reference to Theory:
        Supports the exchange and governance surfaces by recovering whether an artifact should be treated as a policy, approval, revocation, incident, or ordinary knowledge/ability skill in portable form.

    Example Input Output:
        Input: `skill_kind_from_artifact(artifact=Artifact(id='artifact-policy', title='Local Policy', artifact_type='knowledge', representation='yaml'))`
        Output: 'policy'

    Args:
        artifact: Value for `artifact` used by `skill_kind_from_artifact`. Expected type: `Artifact`.

    Returns:
        str: Result produced by `skill_kind_from_artifact`.
    """
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    if artifact_is_policy_record(artifact):
        return "policy"
    if artifact_is_approval_record(artifact):
        return "approval"
    if artifact_is_revocation_record(artifact):
        return "revocation"
    if artifact_is_incident_record(artifact):
        return "incident"
    return normalize_skill_kind(content.get("skill_kind", ""), default=_runtime().enum_text(artifact.artifact_type))


def resolve_export_skill_titles(args: argparse.Namespace) -> list[str]:
    """
    High Level Purpose:
        In circumstances like title-oriented skill export, helps with collecting the requested skill titles from direct flags or batch files.

    Reference to Theory:
        Supports open governance import/export by using immutable semantic titles as the primary external selection surface.

    Example Input Output:
        Input: `resolve_export_skill_titles(args=Namespace(skill_title='What Is Force?', skill_titles_file=None))`
        Output: ['What Is Force?']

    Args:
        args: Value for `args` used by `resolve_export_skill_titles`. Expected type: `argparse.Namespace`.

    Returns:
        list[str]: Result produced by `resolve_export_skill_titles`.
    """
    runtime = _runtime()
    titles: list[str] = []
    if getattr(args, "skill_title", None):
        titles.append(str(args.skill_title).strip())
    if getattr(args, "skill_titles_file", None):
        titles.extend(load_batch_list(args.skill_titles_file, object_key="skill_titles"))
    return runtime.ordered_unique(item for item in titles if item)


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


def handle_export_skill_command(args: argparse.Namespace) -> int:
    """
    High Level Purpose:
        In circumstances like exporting stored artifacts through the smaller skill-facing interface, helps with selecting artifacts by immutable title and rendering them as skill YAML.

    Reference to Theory:
        Supports open governance import/export by exposing the minimal skill kernel plus governance envelope without changing the richer artifact export path used for testing.

    Example Input Output:
        Input: `handle_export_skill_command(args=Namespace(skill_title='What Is Force?', all=False, out=Path('/tmp/skill.yaml')))`
        Output: 0

    Args:
        args: Value for `args` used by `handle_export_skill_command`. Expected type: `argparse.Namespace`.

    Returns:
        int: Result produced by `handle_export_skill_command`.
    """
    runtime = _runtime()
    store = runtime.build_artifact_store()
    if args.all and (args.skill_title or args.skill_titles_file):
        raise SystemExit("Use either --all or explicit skill titles, not both.")
    if args.out and args.out_dir:
        raise SystemExit("Use either --out or --out-dir for batch skill export, not both.")

    skill_titles = resolve_export_skill_titles(args)
    batch_mode = bool(args.all or args.skill_titles_file or len(skill_titles) > 1 or args.out_dir)
    if args.all:
        artifacts = store.load_all_artifacts()
        missing_titles: list[str] = []
    else:
        if not skill_titles:
            raise SystemExit("export-skill requires --skill-title, --skill-titles-file, or --all.")
        title_index = _load_all_artifacts_by_title(store)
        artifacts = []
        missing_titles = []
        for title in skill_titles:
            artifact = title_index.get(title)
            if artifact is None:
                missing_titles.append(title)
                continue
            artifacts.append(artifact)
    if batch_mode:
        exported: list[dict[str, Any]] = []
        if args.out:
            payload = export_skill_bundle_text(artifacts)
            args.out.write_text(payload)
            for artifact in artifacts:
                exported.append(
                    {
                        "artifact_id": artifact.id,
                        "title": artifact.title,
                        "kind": skill_kind_from_artifact(artifact),
                        "out": str(args.out),
                    }
                )
        else:
            if not args.out_dir:
                raise SystemExit("Batch skill export requires --out or --out-dir.")
            args.out_dir.mkdir(parents=True, exist_ok=True)
            for artifact in artifacts:
                out_path = args.out_dir / batch_skill_export_filename(artifact)
                out_path.write_text(export_skill_text(artifact))
                exported.append(
                    {
                        "artifact_id": artifact.id,
                        "title": artifact.title,
                        "kind": skill_kind_from_artifact(artifact),
                        "out": str(out_path),
                    }
                )
        print(
            json.dumps(
                {
                    "exported_count": len(exported),
                    "missing_titles": missing_titles,
                    "exported": exported,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if not artifacts and missing_titles:
        raise SystemExit(f"Skills not found: {', '.join(missing_titles)}")

    payload = export_skill_text(artifacts[0])
    if args.out:
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0
