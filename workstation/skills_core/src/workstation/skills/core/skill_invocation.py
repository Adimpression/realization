# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from realized_core_runtime.capabilities import runtime_skill_declaration_for_artifact
from realized_core_semantics.semantic_text import collapse_ws
from realized_host_interaction.delegation import (
    host_interaction_delegation_requires_escalation as requested_delegation_requires_escalation,
    normalized_requested_delegation,
)
from realized_skill_application.projection import skill_kind_from_artifact
from realized_skill_semantics.execution import ability_executor_framework
from workstation.contracts.runtime import ArtifactRepository
from workstation.foundation.host.artifact_repository import artifact_repository_provider
from workstation.foundation.host.governance import workstation_governance_inventory
from workstation.foundation.host.skill_exchange import skill_exchange_provider
from workstation.skills.builtin import (
    builtin_workstation_skill_artifacts,
    resolve_builtin_workstation_skill,
)
from workstation.skills.core.invocation_contract import (
    skill_invocation_request_from_artifact,
    skill_invocation_result_from_mapping,
)


_GENERIC_NESTED_ANSWER_TEXTS = {"executed", "ok", "completed", "success"}
_NESTED_ANSWER_MAX_LINES = 25
_NESTED_ANSWER_MAX_CHARS = 4000
_NESTED_TRACE_MAX_ITEMS = 20
_NESTED_LIST_MAX_ITEMS = 25
_NESTED_STRING_MAX_CHARS = 2000


def _builtin_skill_artifacts() -> tuple[Any, ...]:
    return builtin_workstation_skill_artifacts(
        skill_exchange_provider().artifact_from_skill_document
    )


def _normalized_skill_title_key(title: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation skill resolution from natural-language tool calls, helps with collapsing title punctuation and separator noise into one stable comparison key.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by making worker resolution tolerant to shortened or punctuation-variant titles without introducing ambient ambiguity.

    Example Input Output:
        Input: `_normalized_skill_title_key('Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences')`
        Output: 'symbol search commands 01 find symbol occurrences symbol search commands 01 find symbol occurrences'

    Args:
        title: Value for `title` used by `_normalized_skill_title_key`. Expected type: `str`.

    Returns:
        str: Result produced by `_normalized_skill_title_key`.
    """
    normalized = collapse_ws(str(title)).casefold()
    normalized = "".join(character if character.isalnum() else " " for character in normalized)
    return collapse_ws(normalized)


def _workstation_skill_catalog_entry(
    artifact: Any,
    *,
    source_kind: str,
    source_target: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation discovery-file materialization, helps with projecting one resolved skill artifact into a compact catalog entry that records both skill shape and where the workstation will source it from.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by making worker provenance explicit instead of implicit in the surrounding store layout.

    Example Input Output:
        Input: `_workstation_skill_catalog_entry(artifact=3, source_kind='builtin_workstation')`
        Output: {'title': 'Workstation Repo Search', 'kind': 'ability', 'executor_framework': 'python3', 'source_kind': 'builtin_workstation'}

    Args:
        artifact: Value for `artifact` used by `_workstation_skill_catalog_entry`. Expected type: `Any`.
        source_kind: Value for `source_kind` used by `_workstation_skill_catalog_entry`. Expected type: `str`.
        source_target: Value for `source_target` used by `_workstation_skill_catalog_entry`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `_workstation_skill_catalog_entry`.
    """
    declaration = runtime_skill_declaration_for_artifact(artifact)
    executor_framework = (
        declaration.get("executor_framework", "")
        or ability_executor_framework(
            representation=str(getattr(artifact, "representation", "")),
            content=dict(getattr(artifact, "content", {}) or {}),
        )
    )
    return {
        "title": str(getattr(artifact, "title", "")),
        "kind": skill_kind_from_artifact(artifact),
        "representation": str(
            getattr(getattr(artifact, "representation", None), "value", getattr(artifact, "representation", ""))
        ),
        "executor_framework": str(executor_framework or ""),
        "risk_tier": str(declaration.get("risk_tier", "")),
        "authorities_requested": list(declaration.get("authorities_requested", [])),
        "inputs": dict(declaration.get("inputs", {})) if isinstance(declaration.get("inputs", {}), Mapping) else {},
        "outputs": dict(declaration.get("outputs", {})) if isinstance(declaration.get("outputs", {}), Mapping) else {},
        "source_kind": collapse_ws(str(source_kind)),
        "source_target": collapse_ws(str(source_target)),
    }


def list_available_workstation_skills(skill_store_path: Path) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation discovery-file materialization, helps with projecting both builtin workstation skills and attached-store skills into one compact machine-readable catalog.

    Reference to Theory:
        Supports the workstation discovery surface by making all workstation-visible pluggable workers explicit instead of requiring ambient store inspection.

    Example Input Output:
        Input: `list_available_workstation_skills(skill_store_path=Path('/tmp/skills.sqlite3'))`
        Output: [{'title': 'Workstation Repo Search', 'kind': 'ability', 'executor_framework': 'python3'}, {'title': 'Say Hi From Wasm', 'kind': 'ability', 'executor_framework': 'wasm_wasi'}]

    Args:
        skill_store_path: Value for `skill_store_path` used by `list_available_workstation_skills`. Expected type: `Path`.

    Returns:
        list[dict[str, Any]]: Result produced by `list_available_workstation_skills`.
    """
    by_title: dict[str, dict[str, Any]] = {}
    for artifact in _builtin_skill_artifacts():
        entry = _workstation_skill_catalog_entry(artifact, source_kind="builtin_workstation")
        by_title[str(entry.get("title", ""))] = entry
    store = workstation_skill_store(skill_store_path)
    artifacts = store.load_all_artifacts()
    for artifact in artifacts:
        skill_kind = skill_kind_from_artifact(artifact)
        if skill_kind not in {"knowledge", "ability"}:
            continue
        entry = _workstation_skill_catalog_entry(
            artifact,
            source_kind="attached_skill_store",
            source_target="skills",
        )
        by_title[str(entry.get("title", ""))] = entry
    catalog = list(by_title.values())
    catalog.sort(key=lambda item: str(item.get("title", "")).casefold())
    return catalog


def workstation_skill_store(skill_store_path: Path) -> ArtifactRepository:
    """
    High Level Purpose:
        In circumstances like workstation-side governed skill discovery and invocation, helps with binding a SQLite-backed artifact store instance to one explicit workstation skill-store path.

    Reference to Theory:
        Supports the workstation attachment model by keeping skill invocation scoped to a declared skill-store attachment rather than ambient store configuration.

    Example Input Output:
        Input: `workstation_skill_store(skill_store_path=Path('/tmp/skills.sqlite3'))`
        Output: SQLiteVectorArtifactStore(...)

    Args:
        skill_store_path: Value for `skill_store_path` used by `workstation_skill_store`. Expected type: `Path`.

    Returns:
        SQLiteVectorArtifactStore: Result produced by `workstation_skill_store`.
    """
    return artifact_repository_provider().open_artifact_repository(
        sqlite_path=Path(skill_store_path),
        vector_mode="off",
    )


def resolve_workstation_skill(
    *,
    skill_title: str,
    skill_store_path: Path,
) -> tuple[Any, dict[str, str]] | None:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation, helps with resolving one skill title against the attached governed store first and then against builtin workstation workers.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by letting store-installed workers override builtin workers while keeping builtin workers available as a portable fallback.

    Example Input Output:
        Input: `resolve_workstation_skill(skill_title='Workstation Repo Search', skill_store_path=Path('/tmp/skills.sqlite3'))`
        Output: (Artifact(id='artifact-skill-...', title='Workstation Repo Search', artifact_type='ability', representation='python_script'), {'source_kind': 'builtin_workstation', 'source_target': ''})

    Args:
        skill_title: Value for `skill_title` used by `resolve_workstation_skill`. Expected type: `str`.
        skill_store_path: Value for `skill_store_path` used by `resolve_workstation_skill`. Expected type: `Path`.

    Returns:
        tuple[Any, dict[str, str]] | None: Result produced by `resolve_workstation_skill`.
    """
    normalized_title = collapse_ws(str(skill_title))
    store = workstation_skill_store(skill_store_path)
    inventory = workstation_governance_inventory(store)
    installed = [
        artifact
        for artifact in inventory.get("artifacts", [])
        if collapse_ws(str(getattr(artifact, "title", ""))) == normalized_title
    ]
    if installed:
        return installed[0], {"source_kind": "attached_skill_store", "source_target": "skills"}
    normalized_title_key = _normalized_skill_title_key(normalized_title)
    if normalized_title_key:
        normalized_installed = [
            artifact
            for artifact in inventory.get("artifacts", [])
            if _normalized_skill_title_key(str(getattr(artifact, "title", ""))) == normalized_title_key
        ]
        if len(normalized_installed) == 1:
            return normalized_installed[0], {"source_kind": "attached_skill_store", "source_target": "skills"}
        prefix_installed = [
            artifact
            for artifact in inventory.get("artifacts", [])
            if (
                _normalized_skill_title_key(str(getattr(artifact, "title", ""))).startswith(normalized_title_key)
            )
        ]
        if len(prefix_installed) == 1:
            return prefix_installed[0], {"source_kind": "attached_skill_store", "source_target": "skills"}
    builtin = resolve_builtin_workstation_skill(
        normalized_title,
        skill_exchange_provider().artifact_from_skill_document,
    )
    if builtin is not None:
        return builtin, {"source_kind": "builtin_workstation", "source_target": ""}
    if normalized_title_key:
        builtin_candidates = [
            artifact
            for artifact in _builtin_skill_artifacts()
            if (
                _normalized_skill_title_key(str(getattr(artifact, "title", ""))) == normalized_title_key
                or _normalized_skill_title_key(str(getattr(artifact, "title", ""))).startswith(normalized_title_key)
            )
        ]
        if len(builtin_candidates) == 1:
            return builtin_candidates[0], {"source_kind": "builtin_workstation", "source_target": ""}
    return None


def _skill_input_mapping(artifact: Any) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation, helps with recovering the declared input mapping for one resolved skill artifact in a stable dictionary shape.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by letting invocation planning reason over explicit declared inputs instead of ambient prompt guesses.

    Example Input Output:
        Input: `_skill_input_mapping(artifact=3)`
        Output: {'symbol': 'required input value', 'root': 'required input value'}

    Args:
        artifact: Value for `artifact` used by `_skill_input_mapping`. Expected type: `Any`.

    Returns:
        dict[str, str]: Result produced by `_skill_input_mapping`.
    """
    declaration = runtime_skill_declaration_for_artifact(artifact)
    raw_inputs = declaration.get("inputs", {})
    if isinstance(raw_inputs, Mapping):
        return {
            collapse_ws(str(name)): collapse_ws(str(description))
            for name, description in dict(raw_inputs).items()
            if collapse_ws(str(name))
        }
    return {}


def _required_skill_input_names(inputs: Mapping[str, Any]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like workstation worker invocation planning, helps with recovering the required top-level input names from one declared input mapping.

    Reference to Theory:
        Supports explicit worker invocation by distinguishing required inputs from optional ones before the shell tries to derive prompt-local payload values.

    Example Input Output:
        Input: `_required_skill_input_names({'symbol': 'required input value', 'glob': 'optional input value'})`
        Output: ['symbol']

    Args:
        inputs: Value for `inputs` used by `_required_skill_input_names`. Expected type: `Mapping[str, Any]`.

    Returns:
        list[str]: Result produced by `_required_skill_input_names`.
    """
    required_names: list[str] = []
    for raw_name, raw_description in dict(inputs).items():
        name = collapse_ws(str(raw_name))
        description = collapse_ws(str(raw_description))
        if not name:
            continue
        if not description or "required" in description.casefold():
            required_names.append(name)
    return required_names


def _skill_payload_has_required_inputs(
    *,
    payload: Any,
    required_names: list[str],
) -> bool:
    """
    High Level Purpose:
        In circumstances like workstation worker invocation planning, helps with deciding whether one payload already satisfies the required top-level input contract.

    Reference to Theory:
        Supports explicit worker invocation by preventing unnecessary fallback or clarification when the payload already contains the required inputs.

    Example Input Output:
        Input: `_skill_payload_has_required_inputs(payload={'symbol': 'BSSCController', 'root': 'src'}, required_names=['symbol', 'root'])`
        Output: True

    Args:
        payload: Value for `payload` used by `_skill_payload_has_required_inputs`. Expected type: `Any`.
        required_names: Value for `required_names` used by `_skill_payload_has_required_inputs`. Expected type: `list[str]`.

    Returns:
        bool: Result produced by `_skill_payload_has_required_inputs`.
    """
    if not required_names:
        return True
    if not isinstance(payload, Mapping):
        return False
    for name in required_names:
        if name not in payload:
            return False
        value = payload.get(name)
        if value is None:
            return False
    return True


def workstation_skill_invocation_payload(
    *,
    artifact: Any,
    semantic_unit: str,
    explicit_payload: Any,
) -> tuple[Any, list[str]]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation from natural-language prompts, helps with merging any explicit payload with prompt-derived inputs and reporting which required inputs remain missing.

    Reference to Theory:
        Supports skill-first workstation behavior by letting the shell complete obvious worker inputs from the prompt instead of silently falling back to generic tools.

    Example Input Output:
        Input: `workstation_skill_invocation_payload(artifact=3, semantic_unit='Find Python class definition for BSSCController under src.', explicit_payload=None)`
        Output: ({'symbol': 'BSSCController', 'root': 'src'}, [])

    Args:
        artifact: Value for `artifact` used by `artifact`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `semantic_unit`. Expected type: `str`.
        explicit_payload: Value for `explicit_payload` used by `explicit_payload`. Expected type: `Any`.

    Returns:
        tuple[Any, list[str]]: Result produced by `workstation_skill_invocation_payload`.
    """
    from workstation.skills.core.direct_composition import derive_workstation_invocation_payload_from_prompt

    inputs = _skill_input_mapping(artifact)
    required_names = _required_skill_input_names(inputs)
    if not inputs:
        if explicit_payload is None:
            return {}, []
        return explicit_payload, []
    if sorted(inputs) == ["payload"] and explicit_payload is None:
        return {"payload": {}}, []

    if _skill_payload_has_required_inputs(payload=explicit_payload, required_names=required_names):
        return explicit_payload, []

    derived_payload = derive_workstation_invocation_payload_from_prompt(
        inputs=inputs,
        prompt=semantic_unit,
        skill_title=str(getattr(artifact, "title", "")),
    )
    merged_payload: Any = explicit_payload
    if isinstance(explicit_payload, Mapping) and isinstance(derived_payload, Mapping):
        merged_payload = dict(derived_payload)
        merged_payload.update(dict(explicit_payload))
    elif explicit_payload is None:
        merged_payload = derived_payload

    missing_required_inputs = [
        name for name in required_names if not _skill_payload_has_required_inputs(payload=merged_payload, required_names=[name])
    ]
    return merged_payload, missing_required_inputs


def workstation_missing_required_inputs(
    *,
    artifact: Any,
    payload: Any,
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation after attachment-scoped payload normalization, helps with recomputing which declared required inputs remain absent from the final payload.

    Reference to Theory:
        Supports skill-first workstation behavior by letting the shell apply bounded normalization steps, such as defaulting a workspace mount, before deciding that an explicit skill request is still under-specified.

    Example Input Output:
        Input: `workstation_missing_required_inputs(artifact=3, payload={'mount': 'main', 'relative_path': 'src/demo.py'})`
        Output: []

    Args:
        artifact: Value for `artifact` used by `artifact`. Expected type: `Any`.
        payload: Value for `payload` used by `payload`. Expected type: `Any`.

    Returns:
        list[str]: Result produced by `workstation_missing_required_inputs`.
    """
    inputs = _skill_input_mapping(artifact)
    required_names = _required_skill_input_names(inputs)
    return [
        name
        for name in required_names
        if not _skill_payload_has_required_inputs(payload=payload, required_names=[name])
    ]


def workstation_explicit_invocation_payload(
    *,
    artifact: Any,
    arguments: Mapping[str, Any],
    explicit_payload: Any,
) -> Any:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation from model-produced tool calls, helps with merging top-level declared skill inputs into the explicit payload shape expected by the nested worker runtime.

    Reference to Theory:
        Supports skill-first workstation behavior by tolerating natural model tool arguments for declared worker inputs instead of requiring one rigid nested payload wrapper.

    Example Input Output:
        Input: `workstation_explicit_invocation_payload(artifact=3, arguments={'mount': 'main', 'relative_path': 'src/demo.py'}, explicit_payload=None)`
        Output: {'mount': 'main', 'relative_path': 'src/demo.py'}

    Args:
        artifact: Value for `artifact` used by `artifact`. Expected type: `Any`.
        arguments: Value for `arguments` used by `arguments`. Expected type: `Mapping[str, Any]`.
        explicit_payload: Value for `explicit_payload` used by `explicit_payload`. Expected type: `Any`.

    Returns:
        Any: Result produced by `workstation_explicit_invocation_payload`.
    """
    inputs = _skill_input_mapping(artifact)
    if not inputs:
        return explicit_payload
    if not isinstance(explicit_payload, Mapping) and explicit_payload is not None:
        return explicit_payload
    merged_payload: dict[str, Any] = dict(explicit_payload) if isinstance(explicit_payload, Mapping) else {}
    for name in inputs:
        if name not in arguments:
            continue
        value = arguments.get(name)
        if value is None:
            continue
        if isinstance(value, str) and not collapse_ws(value):
            continue
        merged_payload[name] = value
    if merged_payload:
        return merged_payload
    return explicit_payload


def workstation_skill_invocation_error_answer(
    *,
    skill_title: str,
    missing_required_inputs: list[str],
) -> str:
    """
    High Level Purpose:
        In circumstances like explicit workstation skill requests that still lack required inputs, helps with rendering one bounded failure answer instead of forcing a silent generic-tool fallback.

    Reference to Theory:
        Supports skill-first workstation behavior by keeping explicit skill requests on the skill path even when prompt-local input derivation is insufficient.

    Example Input Output:
        Input: `workstation_skill_invocation_error_answer(skill_title='Demo Skill', missing_required_inputs=['symbol', 'root'])`
        Output: 'Invocation of Demo Skill failed: Could not derive required inputs from the request (symbol, root).'

    Args:
        skill_title: Value for `skill_title` used by `skill_title`. Expected type: `str`.
        missing_required_inputs: Value for `missing_required_inputs` used by `missing_required_inputs`. Expected type: `list[str]`.

    Returns:
        str: Result produced by `workstation_skill_invocation_error_answer`.
    """
    names = ", ".join(collapse_ws(str(item)) for item in missing_required_inputs if collapse_ws(str(item)))
    if names:
        return f"Invocation of {collapse_ws(str(skill_title))} failed: Could not derive required inputs from the request ({names})."
    return f"Invocation of {collapse_ws(str(skill_title))} failed: Could not derive required inputs from the request."


def workstation_skill_invocation_request(
    *,
    artifact: Any,
    semantic_unit: str,
    payload: Any,
    missing_required_inputs: list[str],
    invocation_mode: str,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation over direct requests and LLM-routed tool calls, helps with projecting one canonical invocation request record from the bound worker payload.

    Reference to Theory:
        Supports the shared invocation-contract migration by keeping workstation binding on the same normalized request surface that future runtime and API invocation will use.

    Example Input Output:
        Input: `workstation_skill_invocation_request(artifact=3, semantic_unit='Find BSSCController', payload={'symbol': 'BSSCController'}, missing_required_inputs=[], invocation_mode='llm_routed')`
        Output: {'skill_title': 'Symbol Search', 'payload': {'symbol': 'BSSCController'}, 'bindings': [{'name': 'symbol', 'status': 'provided'}]}

    Args:
        artifact: Value for `artifact` used by `artifact`. Expected type: `Any`.
        semantic_unit: Value for `semantic_unit` used by `semantic_unit`. Expected type: `str`.
        payload: Value for `payload` used by `payload`. Expected type: `Any`.
        missing_required_inputs: Value for `missing_required_inputs` used by `missing_required_inputs`. Expected type: `list[str]`.
        invocation_mode: Value for `invocation_mode` used by `invocation_mode`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `workstation_skill_invocation_request`.
    """
    return skill_invocation_request_from_artifact(
        artifact,
        semantic_unit=semantic_unit,
        payload=payload,
        missing_required_inputs=missing_required_inputs,
        invocation_mode=invocation_mode,
    ).to_dict()


def workstation_skill_invocation_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation result projection for nested worker execution, helps with projecting one canonical invocation result record from the terminal workstation payload.

    Reference to Theory:
        Supports the shared invocation-contract migration by making workstation success, approval, unsupported, and error outcomes share one normalized result shape.

    Example Input Output:
        Input: `workstation_skill_invocation_result({'status': 'ok', 'skill_title': 'Repo Search', 'answer': 'src/app.py'})`
        Output: {'skill_title': 'Repo Search', 'status': 'ok', 'answer': 'src/app.py'}

    Args:
        result: Value for `result` used by `result`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `workstation_skill_invocation_result`.
    """
    return skill_invocation_result_from_mapping(result).to_dict()


def workstation_skill_invocation_status_answer(result: Mapping[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation and direct-composition handling, helps with projecting one user-facing answer string from non-success status payloads such as approval requests or bounded invocation failures.

    Reference to Theory:
        Supports the skill-first workstation policy by keeping turns on the skill path even when invocation needs approval or fails, instead of forcing generic tool fallback.

    Example Input Output:
        Input: `workstation_skill_invocation_status_answer({'status': 'approval_required', 'skill_title': 'Demo Skill', 'missing_delegation': [{'capability': 'ws.fs.write', 'target': 'scratch'}]})`
        Output: 'Invocation of Demo Skill requires approval before it can continue.\n\nRequested delegation:\n- ws.fs.write on scratch'

    Args:
        result: Value for `result` used by `result`. Expected type: `Mapping[str, Any]`.

    Returns:
        str: Result produced by `workstation_skill_invocation_status_answer`.
    """
    answer_text = str(result.get("answer", "") or "").strip()
    if answer_text:
        return answer_text
    status = collapse_ws(str(result.get("status", ""))).casefold()
    skill_title = collapse_ws(str(result.get("skill_title", "requested skill"))) or "requested skill"
    if status == "approval_required":
        missing_delegation = [
            item
            for item in list(result.get("missing_delegation", []))
            if isinstance(item, Mapping)
        ]
        requested_lines = [
            f"- {collapse_ws(str(item.get('capability', '')))} on {collapse_ws(str(item.get('target', '')))}"
            for item in missing_delegation
            if collapse_ws(str(item.get("capability", ""))) and collapse_ws(str(item.get("target", "")))
        ]
        if requested_lines:
            return (
                f"Invocation of {skill_title} requires approval before it can continue.\n\n"
                "Requested delegation:\n"
                + "\n".join(requested_lines)
            )
        return f"Invocation of {skill_title} requires approval before it can continue."
    if status == "unsupported":
        unsupported_delegation = [
            item
            for item in list(result.get("unsupported_delegation", []))
            if isinstance(item, Mapping)
        ]
        unsupported_lines = [
            f"- {collapse_ws(str(item.get('capability', '')))} on {collapse_ws(str(item.get('target', '')))}"
            for item in unsupported_delegation
            if collapse_ws(str(item.get("capability", ""))) and collapse_ws(str(item.get("target", "")))
        ]
        if unsupported_lines:
            return (
                f"Invocation of {skill_title} could not continue because some requested workstation rights are unsupported.\n\n"
                "Unsupported delegation:\n"
                + "\n".join(unsupported_lines)
            )
        return f"Invocation of {skill_title} could not continue because some requested workstation rights are unsupported."
    error_text = str(result.get("error", "") or "").strip()
    if error_text:
        return error_text
    stderr_text = str(result.get("stderr", "") or "").strip()
    if stderr_text:
        return stderr_text
    return ""


def workstation_nested_skill_answer_text(result: Any) -> str:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation, helps with projecting the most useful shell-facing answer text out of one nested worker result.

    Reference to Theory:
        Supports the shell / pluggable-worker split by keeping worker result shaping consistent across worker implementations.

    Example Input Output:
        Input: `workstation_nested_skill_answer_text(result=3)`
        Output: 'src/demo.py:1:class BSSCController:'

    Args:
        result: Value for `result` used by `result`. Expected type: `Any`.

    Returns:
        str: Result produced by `workstation_nested_skill_answer_text`.
    """
    def _meaningful_answer(text: str) -> str:
        normalized = collapse_ws(str(text))
        if normalized.casefold() in _GENERIC_NESTED_ANSWER_TEXTS:
            return ""
        return normalized

    def _bounded_multiline_answer(text: str) -> str:
        raw_text = str(text or "").strip()
        if not raw_text:
            return ""
        lines = [line.rstrip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            return ""
        limited = lines[:_NESTED_ANSWER_MAX_LINES]
        rendered = "\n".join(limited)
        if len(rendered) > _NESTED_ANSWER_MAX_CHARS:
            rendered = rendered[: _NESTED_ANSWER_MAX_CHARS - 1].rstrip() + "…"
        truncated = len(lines) > len(limited) or len(raw_text) > len(rendered)
        if truncated:
            rendered = rendered.rstrip() + "\n... [truncated]"
        return rendered

    direct_answer = _meaningful_answer(str(getattr(result, "answer", "")))
    parsed_output = getattr(result, "parsed_output", None)
    parsed_output_matches = parsed_output.get("matches", []) if isinstance(parsed_output, Mapping) else []
    if isinstance(parsed_output_matches, list):
        rendered_matches = [collapse_ws(str(item)) for item in parsed_output_matches if collapse_ws(str(item))]
        if rendered_matches:
            return _bounded_multiline_answer("\n".join(rendered_matches))
    if isinstance(parsed_output, Mapping):
        parsed_answer = _meaningful_answer(str(parsed_output.get("answer", "")))
        if parsed_answer:
            return parsed_answer
    result_value = getattr(result, "result", None)
    if isinstance(result_value, Mapping):
        result_matches = result_value.get("matches", [])
        if isinstance(result_matches, list):
            rendered_matches = [collapse_ws(str(item)) for item in result_matches if collapse_ws(str(item))]
            if rendered_matches:
                return _bounded_multiline_answer("\n".join(rendered_matches))
        fallback_answer = _meaningful_answer(str(result_value.get("answer", "")))
        if fallback_answer:
            return fallback_answer
    stdout_text = str(getattr(result, "stdout", "") or "").strip()
    if stdout_text:
        stdout_lines = [line for line in stdout_text.splitlines() if line.strip()]
        if stdout_lines:
            try:
                trailing_payload = json.loads(stdout_lines[-1])
            except Exception:
                trailing_payload = None
            if isinstance(trailing_payload, Mapping) and len(stdout_lines) > 1:
                rendered = "\n".join(stdout_lines[:-1]).strip()
                if rendered:
                    return _bounded_multiline_answer(rendered)
        return _bounded_multiline_answer(stdout_text)
    if direct_answer:
        return direct_answer
    return ""


def workstation_nested_skill_failure_answer_text(*, skill_title: str, result: Any) -> str:
    """
    High Level Purpose:
        In circumstances like workstation direct worker composition over failing workers, helps with projecting one concise failure explanation from the nested worker result.

    Reference to Theory:
        Supports the shell / pluggable-worker split by letting the shell close one failed worker turn deterministically instead of silently drifting to unrelated host tools.

    Example Input Output:
        Input: `workstation_nested_skill_failure_answer_text(skill_title='Demo Skill', result=3)`
        Output: 'Invocation of Demo Skill failed: SyntaxError: unmatched \")\".'

    Args:
        skill_title: Value for `skill_title` used by `skill_title`. Expected type: `str`.
        result: Value for `result` used by `result`. Expected type: `Any`.

    Returns:
        str: Result produced by `workstation_nested_skill_failure_answer_text`.
    """
    stderr_text = str(getattr(result, "stderr", "") or "").strip()
    if stderr_text:
        stderr_lines = [collapse_ws(line) for line in stderr_text.splitlines() if collapse_ws(line)]
        if stderr_lines:
            return f"Invocation of {collapse_ws(str(skill_title))} failed: {stderr_lines[-1]}"
    notes = [collapse_ws(str(item)) for item in list(getattr(result, "notes", []) or []) if collapse_ws(str(item))]
    if notes:
        return f"Invocation of {collapse_ws(str(skill_title))} failed: {notes[-1]}"
    return ""


def workstation_nested_skill_terminal_error(result: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like workstation wrapping of nested skill execution, helps with deciding whether a child runtime that exited cleanly still returned an error-shaped terminal payload that should propagate as a failed workstation skill invocation.

    Reference to Theory:
        Supports governed nested execution by treating explicit worker-level failure payloads as real terminal failures instead of masking them behind a transport-level `ok`.

    Example Input Output:
        Input: `workstation_nested_skill_terminal_error(result=3)`
        Output: True

    Args:
        result: Value for `result` used by `result`. Expected type: `Any`.

    Returns:
        bool: Result produced by `workstation_nested_skill_terminal_error`.
    """
    terminal_statuses = {"error", "unsupported", "approval_required"}
    for candidate in (getattr(result, "parsed_output", None), getattr(result, "result", None)):
        # Generated workers wrap their declared output under `result`; the
        # cross-boundary envelope may add one additional `result` layer.
        current = candidate
        for _ in range(3):
            if not isinstance(current, Mapping):
                break
            status = collapse_ws(str(current.get("status", ""))).casefold()
            if status in terminal_statuses:
                return True
            nested = current.get("result")
            if not isinstance(nested, Mapping) or nested is current:
                break
            current = nested
    return False


def _bounded_nested_value(value: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like workstation receipt projection for nested worker execution, helps with bounding recursive JSON-like payloads so one large worker trace does not exhaust workstation session storage.

    Reference to Theory:
        Supports the shell / pluggable-worker split by keeping worker debugging context available without letting nested broker traces dominate the workstation shell's durable artifacts.

    Example Input Output:
        Input: `_bounded_nested_value({'matches': ['a'] * 100})`
        Output: {'matches': ['a', ...]}

    Args:
        value: Value for `value` used by `_bounded_nested_value`. Expected type: `Any`.

    Returns:
        Any: Result produced by `_bounded_nested_value`.
    """
    if isinstance(value, str):
        text = value.strip()
        if len(text) > _NESTED_STRING_MAX_CHARS:
            return text[: _NESTED_STRING_MAX_CHARS - 1].rstrip() + "…"
        return text
    if isinstance(value, Mapping):
        bounded: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if isinstance(item, list):
                limit = _NESTED_LIST_MAX_ITEMS
                if collapse_ws(key_text).casefold() in {"matches", "grant_ids", "policy_titles", "side_effects"}:
                    limit = min(limit, 20)
                bounded[key_text] = [_bounded_nested_value(entry) for entry in item[:limit]]
            else:
                bounded[key_text] = _bounded_nested_value(item)
        return bounded
    if isinstance(value, list):
        return [_bounded_nested_value(item) for item in value[:_NESTED_LIST_MAX_ITEMS]]
    return value


def _bounded_nested_machine_value(value: Any) -> Any:
    if isinstance(value, str):
        if len(value) > _NESTED_STRING_MAX_CHARS:
            return value[: _NESTED_STRING_MAX_CHARS - 1] + "…"
        return value
    if isinstance(value, Mapping):
        bounded: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if isinstance(item, list):
                limit = _NESTED_LIST_MAX_ITEMS
                if collapse_ws(key_text).casefold() in {"matches", "grant_ids", "policy_titles", "side_effects"}:
                    limit = min(limit, 20)
                bounded[key_text] = [_bounded_nested_machine_value(entry) for entry in item[:limit]]
            else:
                bounded[key_text] = _bounded_nested_machine_value(item)
        return bounded
    if isinstance(value, list):
        return [_bounded_nested_machine_value(item) for item in value[:_NESTED_LIST_MAX_ITEMS]]
    return value


def bounded_nested_effect_traces(traces: list[Any]) -> list[Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation receipts, helps with bounding nested effect traces before they are persisted into chat receipts or validation artifacts.

    Reference to Theory:
        Supports workstation observability without letting one high-volume worker invocation dominate durable shell state.

    Example Input Output:
        Input: `bounded_nested_effect_traces([{'result': {'matches': ['a'] * 100}}])`
        Output: [{'result': {'matches': ['a', ...]}}]

    Args:
        traces: Value for `traces` used by `traces`. Expected type: `list[Any]`.

    Returns:
        list[Any]: Result produced by `bounded_nested_effect_traces`.
    """
    bounded_items = [_bounded_nested_value(item) for item in list(traces or [])]
    if len(bounded_items) <= _NESTED_TRACE_MAX_ITEMS:
        return bounded_items
    selected: list[Any] = []
    seen_effect_kinds: set[str] = set()
    for item in bounded_items:
        effect_kind = collapse_ws(
            str(
                item.get("request", {}).get("effect_kind", "")
                if isinstance(item, Mapping)
                else ""
            )
            or str(item.get("effect_kind", "") if isinstance(item, Mapping) else "")
        )
        if effect_kind and effect_kind not in seen_effect_kinds:
            selected.append(item)
            seen_effect_kinds.add(effect_kind)
        if len(selected) >= _NESTED_TRACE_MAX_ITEMS:
            return selected[:_NESTED_TRACE_MAX_ITEMS]
    for item in bounded_items:
        if len(selected) >= _NESTED_TRACE_MAX_ITEMS:
            break
        if item in selected:
            continue
        selected.append(item)
    return selected[:_NESTED_TRACE_MAX_ITEMS]


def bounded_nested_capability_grants(grants: list[Any]) -> list[Any]:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation receipts, helps with bounding nested capability-grant payloads before they are persisted into durable shell artifacts.

    Reference to Theory:
        Supports workstation observability while keeping grant metadata compact enough for repeated validation sweeps.

    Example Input Output:
        Input: `bounded_nested_capability_grants([{'side_effects': ['a'] * 100}])`
        Output: [{'side_effects': ['a', ...]}]

    Args:
        grants: Value for `grants` used by `grants`. Expected type: `list[Any]`.

    Returns:
        list[Any]: Result produced by `bounded_nested_capability_grants`.
    """
    return [_bounded_nested_value(item) for item in list(grants or [])[:_NESTED_TRACE_MAX_ITEMS]]


def bounded_nested_output_payload(value: Any) -> Any:
    """
    High Level Purpose:
        In circumstances like workstation skill-to-skill composition, helps with bounding one nested worker output payload before it is surfaced for machine-consumable composition or receipts.

    Reference to Theory:
        Supports explicit skill composition by preserving structured worker outputs in a bounded form instead of collapsing them to answer prose only.

    Example Input Output:
        Input: `bounded_nested_output_payload({'matches': ['a'] * 100})`
        Output: {'matches': ['a', ...]}

    Args:
        value: Value for `value` used by `value`. Expected type: `Any`.

    Returns:
        Any: Result produced by `bounded_nested_output_payload`.
    """
    return _bounded_nested_machine_value(value)
