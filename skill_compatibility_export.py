# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from normalize import normalize_notation_key
from semantic_text import collapse_ws
from skill_export_projection import skill_export_document


def _compatibility_safe_name(title: str) -> str:
    normalized = normalize_notation_key(title).replace(" ", "_").replace("/", "_")
    normalized = normalized.replace("-", "_")
    return normalized[:64] or "skill"


def _json_schema_from_contract(contract: Any) -> dict[str, Any]:
    mapping = dict(contract) if isinstance(contract, Mapping) else {}
    properties: dict[str, Any] = {}
    required: list[str] = []
    for raw_name, raw_description in mapping.items():
        name = collapse_ws(str(raw_name))
        description = collapse_ws(str(raw_description))
        if not name:
            continue
        is_required = not description or "required" in description.casefold()
        type_text = "string"
        lowered = description.casefold()
        if "int" in lowered or "number" in lowered or "float" in lowered:
            type_text = "number"
        elif "bool" in lowered:
            type_text = "boolean"
        elif "list" in lowered or "array" in lowered:
            type_text = "array"
        elif "object" in lowered or "mapping" in lowered or "dict" in lowered:
            type_text = "object"
        properties[name] = {
            "type": type_text,
            "description": description or "input value",
        }
        if is_required:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def openai_tool_definition_from_skill_artifact(artifact: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like compatibility-tier export into OpenAI tool definitions, helps with projecting one canonical hosted skill into the OpenAI function-tool surface.

    Reference to Theory:
        Supports compatibility export by deriving foreign invocation metadata from the canonical skill declaration instead of treating the foreign tool definition as the hosted runtime model.

    Example Input Output:
        Input: `openai_tool_definition_from_skill_artifact(artifact)`
        Output: {'type': 'function', 'function': {'name': 'repo_search', 'parameters': {'type': 'object'}}}

    Args:
        artifact: Value for `artifact` used by `openai_tool_definition_from_skill_artifact`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `openai_tool_definition_from_skill_artifact`.
    """
    exported = skill_export_document(artifact)
    title = collapse_ws(str(exported.get("title", "")))
    description_entries = exported.get("description", [])
    description = (
        collapse_ws(str(description_entries[0]))
        if isinstance(description_entries, list) and description_entries
        else collapse_ws(str(description_entries))
    )
    return {
        "type": "function",
        "function": {
            "name": _compatibility_safe_name(title),
            "description": description or title or "Portable skill export",
            "parameters": _json_schema_from_contract(exported.get("inputs", {})),
        },
    }


def mcp_tool_definition_from_skill_artifact(artifact: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like compatibility-tier export into MCP tool descriptors, helps with projecting one canonical hosted skill into the MCP tool surface.

    Reference to Theory:
        Supports compatibility export by using the canonical declaration and title as the source of truth for the MCP descriptor.

    Example Input Output:
        Input: `mcp_tool_definition_from_skill_artifact(artifact)`
        Output: {'name': 'repo_search', 'description': 'Search the repo', 'inputSchema': {'type': 'object'}}

    Args:
        artifact: Value for `artifact` used by `mcp_tool_definition_from_skill_artifact`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `mcp_tool_definition_from_skill_artifact`.
    """
    exported = skill_export_document(artifact)
    title = collapse_ws(str(exported.get("title", "")))
    description_entries = exported.get("description", [])
    description = (
        collapse_ws(str(description_entries[0]))
        if isinstance(description_entries, list) and description_entries
        else collapse_ws(str(description_entries))
    )
    return {
        "name": _compatibility_safe_name(title),
        "description": description or title or "Portable skill export",
        "inputSchema": _json_schema_from_contract(exported.get("inputs", {})),
    }


def instruction_skill_bundle_from_artifact(artifact: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like compatibility-tier export into instruction skill bundles, helps with projecting one canonical skill into a compact instruction bundle surface.

    Reference to Theory:
        Supports compatibility export by letting canonical knowledge or ability skills publish a prompt-facing projection without replacing the canonical hosted skill model.

    Example Input Output:
        Input: `instruction_skill_bundle_from_artifact(artifact)`
        Output: {'format': 'instruction_skill_bundle', 'title': 'Repo Checks', 'instructions': 'Run tests first.'}

    Args:
        artifact: Value for `artifact` used by `instruction_skill_bundle_from_artifact`. Expected type: `Any`.

    Returns:
        dict[str, Any]: Result produced by `instruction_skill_bundle_from_artifact`.
    """
    exported = skill_export_document(artifact)
    title = collapse_ws(str(exported.get("title", "")))
    description_entries = exported.get("description", [])
    description = (
        collapse_ws(str(description_entries[0]))
        if isinstance(description_entries, list) and description_entries
        else collapse_ws(str(description_entries))
    )
    instructions = str(exported.get("answer", "")).strip()
    if not instructions:
        inputs = dict(exported.get("inputs", {})) if isinstance(exported.get("inputs", {}), Mapping) else {}
        input_names = ", ".join(collapse_ws(str(name)) for name in inputs.keys() if collapse_ws(str(name)))
        instructions = (
            f"Invoke {title}."
            if not input_names
            else f"Invoke {title} with inputs: {input_names}."
        )
    return {
        "format": "instruction_skill_bundle",
        "title": title,
        "description": description or title or "Portable skill export",
        "instructions": instructions,
    }
