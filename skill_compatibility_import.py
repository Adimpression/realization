# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from semantic_text import collapse_ws


def _normalized_adapter_entry(value: Any) -> dict[str, Any]:
    adapter = dict(value) if isinstance(value, Mapping) else {}
    format_name = collapse_ws(str(adapter.get("format", "")))
    if not format_name:
        return {}
    normalized: dict[str, Any] = {"format": format_name}
    direction = collapse_ws(str(adapter.get("direction", "")))
    if direction:
        normalized["direction"] = direction
    for key in ("name", "surface", "title", "path", "entrypoint"):
        text = collapse_ws(str(adapter.get(key, "")))
        if text:
            normalized[key] = text
    metadata = dict(adapter.get("metadata", {})) if isinstance(adapter.get("metadata", {}), Mapping) else {}
    if metadata:
        normalized["metadata"] = metadata
    return normalized


def normalized_skill_compatibility_payload(value: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like portable skill import and export bridging, helps with normalizing one optional compatibility envelope into a stable adapter-list shape.

    Reference to Theory:
        Supports compatibility-tier exchange by preserving foreign-surface lineage explicitly without replacing the canonical hosted skill model.

    Example Input Output:
        Input: `normalized_skill_compatibility_payload({'format': 'openai_tool', 'direction': 'import', 'name': 'repo_search'})`
        Output: {'adapters': [{'format': 'openai_tool', 'direction': 'import', 'name': 'repo_search'}]}

    Args:
        value: Value for `value` used by `normalized_skill_compatibility_payload`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `normalized_skill_compatibility_payload`.
    """
    if not isinstance(value, Mapping):
        return {}
    raw_mapping = dict(value)
    adapters_raw = raw_mapping.get("adapters")
    if isinstance(adapters_raw, list):
        adapters = [
            normalized
            for item in adapters_raw
            if (normalized := _normalized_adapter_entry(item))
        ]
    else:
        single = _normalized_adapter_entry(raw_mapping)
        adapters = [single] if single else []
    if not adapters:
        return {}
    return {"adapters": adapters}


def _json_schema_type_text(schema: Mapping[str, Any]) -> str:
    raw_type = schema.get("type", "")
    if isinstance(raw_type, list):
        parts = [collapse_ws(str(item)) for item in raw_type if collapse_ws(str(item))]
        if parts:
            return " | ".join(parts)
    type_text = collapse_ws(str(raw_type))
    if type_text:
        return type_text
    for key in ("enum", "oneOf", "anyOf", "allOf"):
        if key in schema:
            return key
    return "value"


def _contract_from_json_schema(schema: Any) -> dict[str, str]:
    payload = dict(schema) if isinstance(schema, Mapping) else {}
    properties = dict(payload.get("properties", {})) if isinstance(payload.get("properties", {}), Mapping) else {}
    required = {
        collapse_ws(str(item))
        for item in list(payload.get("required", []))
        if collapse_ws(str(item))
    }
    contract: dict[str, str] = {}
    for raw_name, raw_schema in properties.items():
        name = collapse_ws(str(raw_name))
        if not name or not isinstance(raw_schema, Mapping):
            continue
        field_schema = dict(raw_schema)
        description = collapse_ws(str(field_schema.get("description", "")))
        type_text = _json_schema_type_text(field_schema)
        entry = description or type_text
        if name in required and "required" not in entry.casefold():
            entry = f"required {entry}".strip()
        if entry:
            contract[name] = entry
        elif name in required:
            contract[name] = "required value"
        else:
            contract[name] = "value"
    return contract


def canonical_skill_document_from_openai_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing one OpenAI function-tool definition, helps with projecting the foreign tool surface into the canonical portable skill document shape.

    Reference to Theory:
        Supports compatibility-tier exchange by treating OpenAI tool definitions as first-class import sources while keeping the canonical hosted document schema unchanged.

    Example Input Output:
        Input: `canonical_skill_document_from_openai_tool({'type': 'function', 'function': {'name': 'repo_search', 'description': 'Search the repo'}})`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'ability', 'title': 'repo_search', 'compatibility': {'adapters': [...]}}

    Args:
        tool: Value for `tool` used by `canonical_skill_document_from_openai_tool`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `canonical_skill_document_from_openai_tool`.
    """
    wrapper = dict(tool)
    function_payload = (
        dict(wrapper.get("function", {}))
        if str(wrapper.get("type", "")).strip() == "function" and isinstance(wrapper.get("function", {}), Mapping)
        else wrapper
    )
    name = collapse_ws(str(function_payload.get("name", "")))
    if not name:
        raise ValueError("OpenAI tool definitions require a non-empty function name.")
    description = collapse_ws(str(function_payload.get("description", "")))
    parameters = dict(function_payload.get("parameters", {})) if isinstance(function_payload.get("parameters", {}), Mapping) else {}
    return {
        "schema": "bssc_skill.v1",
        "kind": "ability",
        "title": name,
        "description": [description] if description else ["Compatibility-tier imported OpenAI tool declaration."],
        "inputs": _contract_from_json_schema(parameters),
        "outputs": {"result": "tool result"},
        "compatibility": {
            "adapters": [
                {
                    "direction": "import",
                    "format": "openai_tool",
                    "surface": "function",
                    "name": name,
                }
            ]
        },
    }


def canonical_skill_document_from_mcp_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing one MCP tool descriptor, helps with projecting the foreign tool surface into the canonical portable skill document shape.

    Reference to Theory:
        Supports compatibility-tier exchange by letting MCP tool metadata enter the canonical skill layer without pretending the MCP descriptor is the hosted runtime model.

    Example Input Output:
        Input: `canonical_skill_document_from_mcp_tool({'name': 'repo_search', 'description': 'Search the repo', 'inputSchema': {'type': 'object'}})`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'ability', 'title': 'repo_search', 'compatibility': {'adapters': [...]}}

    Args:
        tool: Value for `tool` used by `canonical_skill_document_from_mcp_tool`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `canonical_skill_document_from_mcp_tool`.
    """
    payload = dict(tool)
    name = collapse_ws(str(payload.get("name", "")))
    if not name:
        raise ValueError("MCP tool definitions require a non-empty name.")
    description = collapse_ws(str(payload.get("description", "")))
    input_schema = dict(payload.get("inputSchema", {})) if isinstance(payload.get("inputSchema", {}), Mapping) else {}
    return {
        "schema": "bssc_skill.v1",
        "kind": "ability",
        "title": name,
        "description": [description] if description else ["Compatibility-tier imported MCP tool declaration."],
        "inputs": _contract_from_json_schema(input_schema),
        "outputs": {"result": "tool result"},
        "compatibility": {
            "adapters": [
                {
                    "direction": "import",
                    "format": "mcp_tool",
                    "name": name,
                }
            ]
        },
    }


def canonical_skill_document_from_instruction_skill_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like importing one instruction-skill bundle, helps with projecting the foreign instruction surface into a canonical knowledge-skill document.

    Reference to Theory:
        Supports compatibility-tier exchange by preserving instruction skills as portable knowledge surfaces while keeping hosted execution separate from prompt-only instructions.

    Example Input Output:
        Input: `canonical_skill_document_from_instruction_skill_bundle({'title': 'Repo Checks', 'instructions': 'Run tests first.'})`
        Output: {'schema': 'bssc_skill.v2', 'kind': 'knowledge', 'title': 'Repo Checks', 'answer': 'Run tests first.'}

    Args:
        bundle: Value for `bundle` used by `canonical_skill_document_from_instruction_skill_bundle`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `canonical_skill_document_from_instruction_skill_bundle`.
    """
    payload = dict(bundle)
    title = collapse_ws(str(payload.get("title", payload.get("name", ""))))
    if not title:
        raise ValueError("Instruction skill bundles require a non-empty title.")
    instructions = str(payload.get("instructions", payload.get("content", ""))).strip()
    if not instructions:
        raise ValueError("Instruction skill bundles require non-empty instructions.")
    description = collapse_ws(str(payload.get("description", "")))
    format_name = collapse_ws(str(payload.get("format", ""))) or "instruction_skill_bundle"
    return {
        "schema": "bssc_skill.v1",
        "kind": "knowledge",
        "title": title,
        "description": [description] if description else ["Imported instruction skill bundle."],
        "answer": instructions,
        "compatibility": {
            "adapters": [
                {
                    "direction": "import",
                    "format": format_name,
                    "title": title,
                }
            ]
        },
    }
