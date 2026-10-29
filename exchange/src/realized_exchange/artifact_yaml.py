# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml

from realized_core_semantics.applied_model import Artifact, ControllerFeatureToggles
from realized_core_engine.artifact_semantics import artifact_export_in_entries, artifact_export_out_entries
from realized_core_semantics.boundary import infer_artifact_boundary_shape, infer_function_bit
from realized_skill_semantics.execution import (
    ability_executable_text,
    ability_executor_framework,
    executor_framework_content_key,
)


def _ordered_unique_text(values: Iterable[str]) -> list[str]:
    """Preserve first-occurrence order while dropping blank and duplicate text."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _runtime() -> Any:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with accessing the runtime-backed main namespace used by this code path.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs.

    Example Input Output:
        Input: `_runtime()`
        Output: main

    Args:
        None.

    Returns:
        Any: Result produced by `_runtime`.
    """
    from realized_exchange import dependencies as runtime
    return runtime


def yaml_top_level_declaration(document: Any) -> tuple[str, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling yaml top level declaration.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs.

    Example Input Output:
        Input: `yaml_top_level_declaration(document=3)`
        Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

    Args:
        document: Value for `document` used by `yaml_top_level_declaration`. Expected type: `Any`.

    Returns:
        tuple[str, dict[str, Any]]: Result produced by `yaml_top_level_declaration`.
    """
    if not isinstance(document, Mapping) or not document:
        raise ValueError("Artifact YAML must be a non-empty mapping.")
    if len(document) != 1:
        raise ValueError("Artifact YAML must have exactly one top-level semantic-unit key.")
    title, payload = next(iter(document.items()))
    if not isinstance(payload, Mapping):
        raise ValueError("Artifact YAML declaration body must be a mapping.")
    return str(title).strip(), dict(payload)


def artifact_export_description(artifact: Artifact) -> list[str]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export description.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_export_description(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        artifact: Value for `artifact` used by `artifact_export_description`. Expected type: `Artifact`.

    Returns:
        list[str]: Result produced by `artifact_export_description`.
    """
    content = artifact.content if isinstance(artifact.content, Mapping) else {}
    description: list[str] = []
    if artifact.justification:
        description.append(artifact.justification)
    if artifact.artifact_type == "knowledge":
        question = str(content.get("question", "")).strip()
        if question:
            description.append(f"Knowledge artifact for: {question}")
    elif artifact.artifact_type == "ability":
        description.append("Executable ability artifact.")
    else:
        description.append(f"Reusable {artifact.artifact_type.replace('_', ' ')} artifact.")
    return _ordered_unique_text(description)


def artifact_export_metadata(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export metadata.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_export_metadata(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_export_metadata`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_export_metadata`.
    """
    runtime = _runtime()
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    structured = runtime.artifact_structured_learning_from_content(artifact)
    metadata: dict[str, Any] = {
        "artifact_id": artifact.id,
        "artifact_type": runtime.enum_text(artifact.artifact_type),
        "representation": runtime.enum_text(artifact.representation),
        "function_bit": artifact.function_bit,
        "boundary_shape": [term.value for term in artifact.boundary_shape],
        "scope": artifact.scope,
        "reusability": runtime.enum_text(artifact.reusability),
        "admissibility": runtime.enum_text(artifact.admissibility),
        "learning_relation": runtime.enum_text(artifact.learning_relation),
        "created_at": artifact.created_at,
    }
    if artifact.provenance:
        metadata["provenance"] = artifact.provenance
    if artifact.related_artifact_ids:
        metadata["related_artifact_ids"] = artifact.related_artifact_ids
    if artifact.constraints:
        metadata["constraints"] = artifact.constraints
    if artifact.template_schema:
        metadata["template_schema"] = artifact.template_schema
    if artifact.justification:
        metadata["justification"] = artifact.justification

    controller_features = content.pop("controller_features", None)
    if isinstance(controller_features, Mapping):
        metadata["controller_features"] = ControllerFeatureToggles.from_dict(dict(controller_features)).to_dict()

    question = str(content.pop("question", "")).strip()
    answer = str(content.pop("answer", "")).strip()
    if question:
        metadata["question"] = question
    if answer:
        metadata["answer"] = answer

    if structured:
        metadata["structured_learning"] = structured

    for key in (
        "entrypoint",
        "dependencies",
        "input_contract",
        "output_contract",
        "python_script",
        "shell_script",
        "ansible_playbook",
        "wasm_module",
        "wasm_abi_version",
        "wasm_format",
        "script_language",
        "executor_framework",
    ):
        value = content.pop(key, None)
        if value not in (None, "", [], {}):
            metadata[key] = value

    if content:
        metadata["content"] = content
    return metadata


def artifact_export_document(artifact: Artifact) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export document.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_export_document(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        artifact: Value for `artifact` used by `artifact_export_document`. Expected type: `Artifact`.

    Returns:
        dict[str, Any]: Result produced by `artifact_export_document`.
    """
    return {
        artifact.title: {
            "Description": artifact_export_description(artifact),
            "In": artifact_export_in_entries(artifact),
            "Out": artifact_export_out_entries(artifact),
            "Metadata": artifact_export_metadata(artifact),
        }
    }


def artifact_export_yaml(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export yaml.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    runtime = _runtime()
    return runtime.yaml_dump_human(artifact_export_document(artifact)) + "\n"


def artifact_export_bundle_yaml(artifacts: Iterable[Artifact]) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export bundle yaml.

    Reference to Theory:
        None.

    Example Input Output:
        None.

    Args:
        None.

    Returns:
        None.
    """
    documents = [artifact_export_yaml(artifact).rstrip() for artifact in artifacts]
    documents = [document for document in documents if document]
    if not documents:
        return ""
    return "\n---\n".join(documents) + "\n"


def artifact_export_bundle_text(artifacts: Iterable[Artifact]) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact export bundle text.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_export_bundle_text(artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}])`
        Output: 'F = m * a'

    Args:
        artifacts: Value for `artifacts` used by `artifact_export_bundle_text`. Expected type: `Iterable[Artifact]`.

    Returns:
        str: Result produced by `artifact_export_bundle_text`.
    """
    return artifact_export_bundle_yaml(artifacts)


def artifact_structured_learning_from_import(
    *,
    title: str,
    question: str,
    metadata: Mapping[str, Any],
    in_entries: list[str],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact structured learning from import.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_structured_learning_from_import(title='Physics / Force / Force From Mass And Acceleration', question='Compute force from mass and acceleration.', metadata={'source_document': 'physics_force.md', 'topic': 'force'}, in_entries=['mass', 'acceleration', 'force'])`
        Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

    Args:
        title: Value for `title` used by `artifact_structured_learning_from_import`. Expected type: `str`.
        question: Value for `question` used by `artifact_structured_learning_from_import`. Expected type: `str`.
        metadata: Value for `metadata` used by `artifact_structured_learning_from_import`. Expected type: `Mapping[str, Any]`.
        in_entries: Value for `in_entries` used by `artifact_structured_learning_from_import`. Expected type: `list[str]`.

    Returns:
        dict[str, Any]: Result produced by `artifact_structured_learning_from_import`.
    """
    runtime = _runtime()
    structured = metadata.get("structured_learning", {})
    if isinstance(structured, Mapping):
        if any(
            structured.get(key) not in (None, "", [], {})
            for key in (
                "encountered_not",
                "goal",
                "lookup_keys",
                "component_nots",
                "composed_not",
                *runtime.STRUCTURED_LEARNING_EXTRA_FIELDS,
            )
        ):
            normalized = runtime.normalize_not_elaboration_payload(
                question or title,
                structured,
                related_artifact_titles=[],
            )
            normalized["lookup_keys"] = runtime.ordered_unique(
                list(normalized.get("lookup_keys", [])) + runtime.learning_lookup_keys(question or title)
            )[:24]
            return normalized

    encountered_not = runtime.titleize_semantic_unit(str(metadata.get("encountered_not", "")).strip()) or runtime.titleize_semantic_unit(title)
    component_nots = runtime.yaml_string_list(metadata.get("component_nots", [])) or in_entries
    component_nots = runtime.ordered_unique(runtime.titleize_semantic_unit(item) or item for item in component_nots if str(item).strip())
    composed_not = runtime.titleize_semantic_unit(str(metadata.get("composed_not", "")).strip())
    if not composed_not and len(component_nots) > 1:
        composed_not = encountered_not
    fallback = runtime.fallback_not_elaboration_for_text(question or title)
    fallback["encountered_not"] = encountered_not
    fallback["lookup_keys"] = runtime.yaml_string_list(metadata.get("lookup_keys", [])) or fallback.get("lookup_keys", [])
    fallback["component_nots"] = component_nots
    fallback["composed_not"] = composed_not
    fallback["notation_yaml"] = runtime.render_structured_learning_yaml(
        semantic_unit=question or title,
        encountered_not=encountered_not,
        component_nots=component_nots,
        composed_not=composed_not,
        related_artifact_titles=[],
        intended_object=str(fallback.get("intended_object", "")),
        success_criteria=list(fallback.get("success_criteria", [])),
        actual_realization=str(fallback.get("actual_realization", "")),
        givens=fallback.get("givens", []),
        unknowns=fallback.get("unknowns", []),
        missing_components=fallback.get("missing_components", []),
        distorted_components=fallback.get("distorted_components", []),
        differentiators=fallback.get("differentiators", []),
        contrastive_cases=fallback.get("contrastive_cases", []),
        risk_of_wrong_closure=fallback.get("risk_of_wrong_closure", []),
        disallowed_assumptions=fallback.get("disallowed_assumptions", []),
        misalignment_types=fallback.get("misalignment_types", []),
        origin_layers=fallback.get("origin_layers", []),
        degree=str(fallback.get("degree", "")),
        remainder_shapes=fallback.get("remainder_shapes", []),
        why_it_matters=fallback.get("why_it_matters", []),
        minimal_repair=fallback.get("minimal_repair", []),
        full_repair=fallback.get("full_repair", []),
        action_posture=str(fallback.get("action_posture", "")),
    )
    return fallback


def artifact_from_yaml_document(document: Any) -> Artifact:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling artifact from yaml document.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `artifact_from_yaml_document(document=3)`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        document: Value for `document` used by `artifact_from_yaml_document`. Expected type: `Any`.

    Returns:
        Artifact: Result produced by `artifact_from_yaml_document`.
    """
    runtime = _runtime()
    title, payload = yaml_top_level_declaration(document)
    description_entries = runtime.yaml_string_list(payload.get("Description", []))
    in_entries = runtime.yaml_string_list(payload.get("In", []))
    out_entries = runtime.yaml_string_list(payload.get("Out", []))
    metadata = dict(payload.get("Metadata", {})) if isinstance(payload.get("Metadata", {}), Mapping) else {}

    artifact_type = runtime.normalize_artifact_type(metadata.get("artifact_type", "knowledge"))
    representation_default = "yaml" if artifact_type != "ability" else "python_script"
    representation = runtime.normalize_artifact_representation(
        metadata.get("representation", representation_default),
        artifact_type=artifact_type,
    )
    scope = str(metadata.get("scope", "")).strip() or (
        "reuse when the same or closely related item appears again under an ordinary stable reading"
        if artifact_type == "knowledge"
        else "reuse when the same executable ability family is needed under compatible inputs"
    )
    justification = str(metadata.get("justification", "")).strip() or (
        description_entries[0] if description_entries else f"Imported {artifact_type.replace('_', ' ')} artifact from YAML."
    )
    reusability = runtime.normalize_artifact_reuse(metadata.get("reusability", "local_reuse"))
    admissibility = runtime.normalize_artifact_admission(metadata.get("admissibility", "admitted"))
    learning_relation = runtime.normalize_learning_relation(metadata.get("learning_relation", "new_family"))
    provenance = runtime.yaml_string_list(metadata.get("provenance", []))
    related_artifact_ids = runtime.yaml_string_list(metadata.get("related_artifact_ids", []))
    constraints = runtime.yaml_string_list(metadata.get("constraints", []))
    template_schema = dict(metadata.get("template_schema", {})) if isinstance(metadata.get("template_schema", {}), Mapping) else {}
    created_at = str(metadata.get("created_at", "")).strip() or runtime.utc_now()
    artifact_id = (
        str(metadata.get("artifact_id") or metadata.get("id") or "").strip()
        or runtime.make_id("artifact", f"{runtime.enum_text(artifact_type)}-{title}")
    )

    content = dict(metadata.get("content", {})) if isinstance(metadata.get("content", {}), Mapping) else {}
    if isinstance(metadata.get("controller_features"), Mapping):
        content["controller_features"] = ControllerFeatureToggles.from_dict(
            dict(metadata.get("controller_features", {}))
        ).to_dict()
    if isinstance(metadata.get("governed_authorities"), list):
        content["governed_authorities"] = runtime.yaml_string_list(metadata.get("governed_authorities", []))
    if isinstance(metadata.get("governed_host_brokers"), list):
        content["governed_host_brokers"] = runtime.yaml_string_list(metadata.get("governed_host_brokers", []))

    if artifact_type == "knowledge":
        question = str(metadata.get("question") or content.get("question") or title).strip()
        structured_learning = artifact_structured_learning_from_import(
            title=title,
            question=question,
            metadata=metadata,
            in_entries=in_entries,
        )
        answer = str(metadata.get("answer") or content.get("answer") or "\n".join(out_entries)).strip()
        if not answer:
            answer = str(
                structured_learning.get("notation_yaml")
                or structured_learning.get("goal")
                or structured_learning.get("encountered_not")
                or "\n".join(description_entries)
            ).strip()
        if not answer:
            raise ValueError(
                "Knowledge artifact import requires an answer-bearing field, or a structured_learning payload that can be reconstructed."
            )
        content["question"] = question
        content["answer"] = answer
        content["structured_learning"] = structured_learning
        content.setdefault("description", description_entries)
    elif artifact_type == "ability":
        compatibility_only_ability = isinstance(content.get("skill_compatibility", {}), Mapping) and bool(
            dict(content.get("skill_compatibility", {}))
        )
        executor_framework = ability_executor_framework(representation=representation, content={**content, **metadata})
        executable_text = ability_executable_text(representation=representation, content={**content, **metadata})
        if not executable_text and not compatibility_only_ability:
            content_key = executor_framework_content_key(executor_framework)
            raise ValueError(
                f"Ability artifact import requires Metadata.{content_key}."
            )
        question = str(metadata.get("question") or content.get("question") or title).strip()
        content["question"] = question
        if executable_text:
            content_key = executor_framework_content_key(executor_framework)
            content[content_key] = executable_text
            default_entrypoint = "playbook" if executor_framework == "ansible" else "run"
            content["entrypoint"] = str(metadata.get("entrypoint") or content.get("entrypoint") or default_entrypoint).strip() or default_entrypoint
        dependencies = runtime.yaml_string_list(metadata.get("dependencies", []))
        if not dependencies:
            dependencies = runtime.yaml_string_list(content.get("dependencies", []))
        if executor_framework == "python3":
            content["dependencies"] = runtime.ordered_unique(dependencies + list(runtime.ABILITY_SCRIPT_DEPENDENCIES))
        elif dependencies:
            content["dependencies"] = runtime.ordered_unique(dependencies)
        raw_input_contract = metadata.get("input_contract", content.get("input_contract", None))
        raw_output_contract = metadata.get("output_contract", content.get("output_contract", None))
        has_explicit_input_contract = isinstance(raw_input_contract, Mapping)
        has_explicit_output_contract = isinstance(raw_output_contract, Mapping)
        input_contract = dict(raw_input_contract) if has_explicit_input_contract else {}
        output_contract = dict(raw_output_contract) if has_explicit_output_contract else {}
        content["input_contract"] = (
            input_contract
            if has_explicit_input_contract
            else runtime.contract_mapping_from_entries(in_entries, prefix="input") or {"payload": "stdin payload or JSON input"}
        )
        content["output_contract"] = (
            output_contract
            if has_explicit_output_contract
            else runtime.contract_mapping_from_entries(out_entries, prefix="output") or {"result": "JSON result"}
        )
        content["script_language"] = str(
            metadata.get("script_language")
            or content.get("script_language")
            or (
                "python"
                if executor_framework == "python3"
                else "wasm"
                if executor_framework == "wasm_wasi"
                else executor_framework
            )
        ).strip() or (
            "python"
            if executor_framework == "python3"
            else "wasm"
            if executor_framework == "wasm_wasi"
            else executor_framework
        )
        if executor_framework:
            content["executor_framework"] = executor_framework
        if executor_framework == "wasm_wasi":
            wasm_abi_version = str(metadata.get("wasm_abi_version") or content.get("wasm_abi_version") or "").strip()
            if wasm_abi_version:
                content["wasm_abi_version"] = wasm_abi_version
            wasm_format = str(metadata.get("wasm_format") or content.get("wasm_format") or "").strip()
            if wasm_format:
                content["wasm_format"] = wasm_format
        content["structured_learning"] = artifact_structured_learning_from_import(
            title=title,
            question=question,
            metadata=metadata,
            in_entries=in_entries,
        )
        content.setdefault("description", description_entries)
    else:
        question = str(metadata.get("question") or content.get("question") or title).strip()
        answer = str(metadata.get("answer") or content.get("answer") or "\n".join(out_entries)).strip()
        if question:
            content["question"] = question
        if answer:
            content["answer"] = answer
        if description_entries:
            content.setdefault("description", description_entries)

    function_bit = runtime.normalize_function_bit(
        metadata.get("function_bit")
        if metadata.get("function_bit") not in (None, "")
        else infer_function_bit(
            artifact_type=artifact_type,
            representation=representation,
            content=content,
        )
    )
    boundary_shape = runtime.normalize_boundary_shape(
        metadata.get("boundary_shape"),
        default=infer_artifact_boundary_shape(
            artifact_type=artifact_type,
            representation=representation,
            title=title,
            scope=scope,
            content=content,
            function_bit=function_bit,
        ),
    )
    return Artifact(
        id=artifact_id,
        artifact_type=artifact_type,
        title=title,
        representation=representation,
        function_bit=function_bit,
        scope=scope,
        provenance=provenance,
        reusability=reusability,
        admissibility=admissibility,
        template_schema=template_schema,
        learning_relation=learning_relation,
        related_artifact_ids=related_artifact_ids,
        content=content,
        justification=justification,
        boundary_shape=boundary_shape,
        constraints=constraints,
        created_at=created_at,
    )


def load_artifact_yaml_documents(path: Path) -> list[Artifact]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with loading artifact yaml documents.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `load_artifact_yaml_documents(path=Path('/tmp/physics_force.md'))`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        path: Value for `path` used by `load_artifact_yaml_documents`. Expected type: `Path`.

    Returns:
        list[Artifact]: Result produced by `load_artifact_yaml_documents`.
    """
    documents = list(yaml.safe_load_all(path.read_text()))
    artifacts: list[Artifact] = []
    for document in documents:
        if document in (None, "", [], {}):
            continue
        artifacts.append(artifact_from_yaml_document(document))
    return artifacts


def load_artifact_yaml(path: Path) -> Artifact:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with loading artifact yaml.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `load_artifact_yaml(path=Path('/tmp/physics_force.md'))`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        path: Value for `path` used by `load_artifact_yaml`. Expected type: `Path`.

    Returns:
        Artifact: Result produced by `load_artifact_yaml`.
    """
    artifacts = load_artifact_yaml_documents(path)
    if not artifacts:
        raise ValueError(f"No artifact document found in {path}.")
    return artifacts[0]


def export_artifact_text(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling export artifact text.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `export_artifact_text(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: 'F = m * a'

    Args:
        artifact: Value for `artifact` used by `export_artifact_text`. Expected type: `Artifact`.

    Returns:
        str: Result produced by `export_artifact_text`.
    """
    return artifact_export_yaml(artifact)


def export_artifact_bundle_text(artifacts: Iterable[Artifact]) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling export artifact bundle text.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `export_artifact_bundle_text(artifacts=[{'title': 'Physics / Force / Force From Mass And Acceleration'}])`
        Output: 'F = m * a'

    Args:
        artifacts: Value for `artifacts` used by `export_artifact_bundle_text`. Expected type: `Iterable[Artifact]`.

    Returns:
        str: Result produced by `export_artifact_bundle_text`.
    """
    return artifact_export_bundle_text(artifacts)


def load_batch_list(path: Path, *, object_key: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with loading batch list.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs.

    Example Input Output:
        Input: `load_batch_list(path=Path('/tmp/physics_force.md'), object_key='force')`
        Output: ['Physics', 'Force', 'Force From Mass And Acceleration']

    Args:
        path: Value for `path` used by `load_batch_list`. Expected type: `Path`.
        object_key: Value for `object_key` used by `load_batch_list`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `load_batch_list`.
    """
    raw_text = path.read_text().strip()
    if not raw_text:
        return []
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, list):
        return [str(item).strip() for item in payload if str(item).strip()]
    if isinstance(payload, Mapping):
        values = payload.get(object_key, [])
        if isinstance(values, list):
            return [str(item).strip() for item in values if str(item).strip()]
    return [line.strip() for line in raw_text.splitlines() if line.strip()]


def batch_artifact_export_filename(artifact: Artifact) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling batch artifact export filename.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `batch_artifact_export_filename(artifact=Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python'))`
        Output: 'F = m * a'

    Args:
        artifact: Value for `artifact` used by `batch_artifact_export_filename`. Expected type: `Artifact`.

    Returns:
        str: Result produced by `batch_artifact_export_filename`.
    """
    return f"{artifact.id}.yaml"


def resolve_export_artifact_ids(args: argparse.Namespace) -> list[str]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with resolving export artifact ids.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `resolve_export_artifact_ids(args=Namespace(discovery='off', reflection='on', contemplation='on'))`
        Output: [{'title': 'Physics / Force / Force From Mass And Acceleration'}]

    Args:
        args: Value for `args` used by `resolve_export_artifact_ids`. Expected type: `argparse.Namespace`.

    Returns:
        list[str]: Result produced by `resolve_export_artifact_ids`.
    """
    runtime = _runtime()
    artifact_ids: list[str] = []
    if args.artifact_id:
        artifact_ids.append(str(args.artifact_id).strip())
    if args.artifact_ids_file:
        artifact_ids.extend(load_batch_list(args.artifact_ids_file, object_key="artifact_ids"))
    return runtime.ordered_unique(item for item in artifact_ids if item)


def resolve_import_artifact_files(args: argparse.Namespace) -> list[Path]:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with resolving import artifact files.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `resolve_import_artifact_files(args=Namespace(discovery='off', reflection='on', contemplation='on'))`
        Output: Path('/tmp/physics_force.md')

    Args:
        args: Value for `args` used by `resolve_import_artifact_files`. Expected type: `argparse.Namespace`.

    Returns:
        list[Path]: Result produced by `resolve_import_artifact_files`.
    """
    files: list[Path] = []
    for item in args.artifact_file or []:
        files.append(item)
    if args.artifact_files_file:
        files.extend(Path(item).expanduser() for item in load_batch_list(args.artifact_files_file, object_key="artifact_files"))
    if args.artifact_dir:
        files.extend(sorted(path for path in args.artifact_dir.iterdir() if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}))
    normalized: list[Path] = []
    seen: set[str] = set()
    for path in files:
        resolved = path.expanduser()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(resolved)
    return normalized


def normalized_bundle_filename_for_source(path: Path) -> str:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling normalized bundle filename for source.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs.

    Example Input Output:
        Input: `normalized_bundle_filename_for_source(path=Path('/tmp/physics_force.md'))`
        Output: 'F = m * a'

    Args:
        path: Value for `path` used by `normalized_bundle_filename_for_source`. Expected type: `Path`.

    Returns:
        str: Result produced by `normalized_bundle_filename_for_source`.
    """
    return path.name if path.suffix.lower() in {".yaml", ".yml"} else f"{path.name}.yaml"


def handle_artifact_export_command(args: argparse.Namespace) -> int:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling handle artifact export command.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `handle_artifact_export_command(args=Namespace(discovery='off', reflection='on', contemplation='on'))`
        Output: 3

    Args:
        args: Value for `args` used by `handle_artifact_export_command`. Expected type: `argparse.Namespace`.

    Returns:
        int: Result produced by `handle_artifact_export_command`.
    """
    runtime = _runtime()
    store = runtime.build_artifact_store()
    if args.all and (args.artifact_id or args.artifact_ids_file):
        raise SystemExit("Use either --all or explicit artifact ids, not both.")
    if args.out and args.out_dir:
        raise SystemExit("Use either --out or --out-dir for batch artifact export, not both.")
    artifact_ids = resolve_export_artifact_ids(args)
    batch_mode = bool(args.all or args.artifact_ids_file or len(artifact_ids) > 1 or args.out_dir)
    if args.all:
        artifacts = store.load_all_artifacts()
        missing_ids: list[str] = []
    else:
        if not artifact_ids:
            raise SystemExit("artifact-export requires --artifact-id, --artifact-ids-file, or --all.")
        artifacts = []
        missing_ids = []
        for artifact_id in artifact_ids:
            artifact = store.load_artifact_by_id(artifact_id)
            if artifact is None:
                missing_ids.append(artifact_id)
                continue
            artifacts.append(artifact)
    if not artifacts and missing_ids:
        raise SystemExit(f"Artifacts not found: {', '.join(missing_ids)}")
    if batch_mode:
        exported: list[dict[str, Any]] = []
        if args.out:
            payload = export_artifact_bundle_text(artifacts)
            args.out.write_text(payload)
            for artifact in artifacts:
                exported.append(
                    {
                        "artifact_id": artifact.id,
                        "title": artifact.title,
                        "artifact_type": artifact.artifact_type,
                        "out": str(args.out),
                    }
                )
        else:
            if not args.out_dir:
                raise SystemExit("Batch artifact export requires --out or --out-dir.")
            args.out_dir.mkdir(parents=True, exist_ok=True)
            for artifact in artifacts:
                out_path = args.out_dir / batch_artifact_export_filename(artifact)
                out_path.write_text(export_artifact_text(artifact))
                exported.append(
                    {
                        "artifact_id": artifact.id,
                        "title": artifact.title,
                        "artifact_type": artifact.artifact_type,
                        "out": str(out_path),
                    }
                )
        print(
            json.dumps(
                {
                    "exported_count": len(exported),
                    "missing_ids": missing_ids,
                    "exported": exported,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    artifact = artifacts[0]
    payload = export_artifact_text(artifact)
    if args.out:
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0


def handle_artifact_import_command(args: argparse.Namespace) -> int:
    """
    High Level Purpose:
        In circumstances like artifact import, export, and batch transfer workflows, helps with handling handle artifact import command.

    Reference to Theory:
        Handles import/export and side-channel serialization of artifacts so semantic identities and reuse structures can move safely across runs. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `handle_artifact_import_command(args=Namespace(discovery='off', reflection='on', contemplation='on'))`
        Output: 3

    Args:
        args: Value for `args` used by `handle_artifact_import_command`. Expected type: `argparse.Namespace`.

    Returns:
        int: Result produced by `handle_artifact_import_command`.
    """
    runtime = _runtime()
    store = runtime.build_artifact_store()
    artifact_files = resolve_import_artifact_files(args)
    if not artifact_files:
        raise SystemExit("artifact-import requires --artifact-file, --artifact-files-file, or --artifact-dir.")
    if args.normalized_out and args.normalized_out_dir:
        raise SystemExit("Use either --normalized-out or --normalized-out-dir, not both.")
    source_artifacts: list[tuple[Path, list[Artifact]]] = []
    for artifact_file in artifact_files:
        source_artifacts.append((artifact_file, load_artifact_yaml_documents(artifact_file)))
    total_artifacts = sum(len(items) for _, items in source_artifacts)
    batch_mode = (
        len(artifact_files) > 1
        or total_artifacts > 1
        or args.artifact_files_file is not None
        or args.artifact_dir is not None
        or args.normalized_out_dir is not None
    )
    if batch_mode and args.normalized_out:
        raise SystemExit("Use --normalized-out only for a single imported artifact; use --normalized-out-dir for batch or multi-document import.")
    if batch_mode and args.normalized_out_dir:
        args.normalized_out_dir.mkdir(parents=True, exist_ok=True)

    imported: list[dict[str, Any]] = []
    imported_entries: list[tuple[Path, Artifact, Path | None]] = []
    for artifact_file, artifacts in source_artifacts:
        normalized_out_path = None
        if batch_mode and args.normalized_out_dir:
            normalized_out_path = args.normalized_out_dir / normalized_bundle_filename_for_source(artifact_file)
            normalized_out_path.write_text(export_artifact_bundle_text(artifacts))
        elif not batch_mode and args.normalized_out:
            args.normalized_out.write_text(export_artifact_bundle_text(artifacts))
            normalized_out_path = args.normalized_out
        for artifact in artifacts:
            imported_entries.append((artifact_file, artifact, normalized_out_path))

    artifacts_to_persist = [artifact for _, artifact, _ in imported_entries]
    store_summary = store.persist_artifacts(artifacts_to_persist, run_id="artifact_import")
    store_reports = list(store_summary.get("reports", []))
    for (artifact_file, artifact, normalized_out_path), report in zip(imported_entries, store_reports, strict=False):
        imported.append(
            {
                "artifact_id": report.get("artifact_id", artifact.id),
                "title": artifact.title,
                "artifact_type": artifact.artifact_type,
                "representation": artifact.representation,
                "artifact_file": str(artifact_file),
                "normalized_out": str(normalized_out_path) if normalized_out_path else "",
                "store_report": report,
            }
        )

    if batch_mode:
        print(
            json.dumps(
                {
                    "imported_count": len(imported),
                    "imported": imported,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    item = imported[0]
    print(
        json.dumps(
            {
                "artifact_id": item["artifact_id"],
                "title": item["title"],
                "artifact_type": item["artifact_type"],
                "representation": item["representation"],
                "artifact_file": item["artifact_file"],
                "normalized_out": item["normalized_out"],
                "store_report": item["store_report"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0
