"""Portable executor descriptors for declared ability content."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES = (
    "python3",
    "bash",
    "ansible",
    "wasm_wasi",
)

EXECUTOR_FRAMEWORK_ALIASES = {
    "python": "python3",
    "py": "python3",
    "python3": "python3",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "ansible": "ansible",
    "ansible-playbook": "ansible",
    "wasm": "wasm_wasi",
    "wat": "wasm_wasi",
    "wasi": "wasm_wasi",
    "wasmtime": "wasm_wasi",
    "wasm_wasi": "wasm_wasi",
}

EXECUTOR_FRAMEWORK_CONTENT_KEYS = {
    "python3": "python_script",
    "bash": "shell_script",
    "ansible": "ansible_playbook",
    "wasm_wasi": "wasm_module",
}

EXECUTOR_FRAMEWORK_REPRESENTATIONS = {
    "python3": "python_script",
    "bash": "shell_script",
    "ansible": "ansible_playbook",
    "wasm_wasi": "wasm_module",
}

__all__ = [
    "EXECUTOR_FRAMEWORK_ALIASES",
    "EXECUTOR_FRAMEWORK_CONTENT_KEYS",
    "EXECUTOR_FRAMEWORK_REPRESENTATIONS",
    "SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES",
    "ability_executable_text",
    "ability_executor_framework",
    "executor_framework_content_key",
    "normalize_executor_framework_name",
]


def normalize_executor_framework_name(value: Any) -> str:
    """Normalize one portable executor-framework name or alias."""
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    return EXECUTOR_FRAMEWORK_ALIASES.get(normalized, normalized)


def executor_framework_content_key(framework: str) -> str:
    """Return the ability content field for one executor descriptor."""
    normalized = normalize_executor_framework_name(framework)
    return EXECUTOR_FRAMEWORK_CONTENT_KEYS.get(normalized, "executable_body")


def ability_executor_framework(
    *,
    representation: str = "",
    content: Mapping[str, Any] | None = None,
) -> str:
    """Infer the declared executor descriptor from portable ability content."""
    payload = dict(content) if isinstance(content, Mapping) else {}
    explicit = normalize_executor_framework_name(
        payload.get("executor_framework", "")
    )
    if explicit:
        return explicit
    normalized_representation = str(representation or "").strip().lower()
    if normalized_representation == "python_script":
        return "python3"
    if normalized_representation == "shell_script":
        return "bash"
    if normalized_representation == "ansible_playbook":
        return "ansible"
    if normalized_representation == "wasm_module":
        return "wasm_wasi"
    script_language = normalize_executor_framework_name(
        payload.get("script_language", "")
    )
    if script_language in SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES:
        return script_language
    if str(payload.get("python_script", "")).strip():
        return "python3"
    if str(payload.get("shell_script", "")).strip():
        return "bash"
    if str(payload.get("ansible_playbook", "")).strip():
        return "ansible"
    if str(payload.get("wasm_module", "")).strip():
        return "wasm_wasi"
    return ""


def ability_executable_text(
    *,
    representation: str = "",
    content: Mapping[str, Any] | None = None,
) -> str:
    """Return the executable body selected by the portable descriptor."""
    payload = dict(content) if isinstance(content, Mapping) else {}
    framework = ability_executor_framework(
        representation=representation,
        content=payload,
    )
    key = executor_framework_content_key(framework)
    return str(payload.get(key, "")).strip()
