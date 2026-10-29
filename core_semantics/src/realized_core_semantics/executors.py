"""Dependency-light executor identity and declaration normalization."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
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

EXECUTOR_FRAMEWORK_REPRESENTATIONS = dict(EXECUTOR_FRAMEWORK_CONTENT_KEYS)

DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS = ("python3",)

__all__ = [
    "DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS",
    "EXECUTOR_FRAMEWORK_ALIASES",
    "EXECUTOR_FRAMEWORK_CONTENT_KEYS",
    "EXECUTOR_FRAMEWORK_REPRESENTATIONS",
    "SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES",
    "executor_framework_content_key",
    "normalize_executor_framework_name",
    "normalize_supported_executor_frameworks",
]


def normalize_executor_framework_name(value: Any) -> str:
    """Normalize one executor-framework name or accepted alias."""
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    return EXECUTOR_FRAMEWORK_ALIASES.get(normalized, normalized)


def executor_framework_content_key(framework: str) -> str:
    """Return the declared content field for one executor identity."""
    normalized = normalize_executor_framework_name(framework)
    return EXECUTOR_FRAMEWORK_CONTENT_KEYS.get(normalized, "executable_body")


def normalize_supported_executor_frameworks(
    values: Iterable[Any] | str | None,
    *,
    default: Sequence[str] = DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS,
) -> list[str]:
    """Normalize, filter, and de-duplicate a declared executor set."""
    if values is None:
        raw_values: list[Any] = list(default)
    elif isinstance(values, str):
        raw_values = [item for item in re.split(r"[,\s]+", values) if item]
    else:
        raw_values = []
        for item in values:
            if isinstance(item, str):
                raw_values.extend(
                    piece for piece in re.split(r"[,\s]+", item) if piece
                )
            elif item not in (None, ""):
                raw_values.append(item)

    normalized: list[str] = []
    for item in raw_values:
        framework = normalize_executor_framework_name(item)
        if (
            framework in SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES
            and framework not in normalized
        ):
            normalized.append(framework)
    if normalized:
        return normalized
    return [
        normalize_executor_framework_name(item)
        for item in default
        if normalize_executor_framework_name(item)
    ]
