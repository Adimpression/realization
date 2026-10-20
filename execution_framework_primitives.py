# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SUPPORTED_EXECUTOR_FRAMEWORKS_ENV = "BSSC_SUPPORTED_EXECUTORS"
DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS = ("python3",)
SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES = ("python3", "bash", "ansible", "wasm_wasi")

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


def normalize_executor_framework_name(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    return EXECUTOR_FRAMEWORK_ALIASES.get(normalized, normalized)


def normalize_supported_executor_frameworks(
    values: Iterable[Any] | str | None,
    *,
    default: Sequence[str] = DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS,
) -> list[str]:
    raw_values: list[Any] = []
    if values is None:
        raw_values = list(default)
    elif isinstance(values, str):
        raw_values = [item for item in re.split(r"[,\s]+", values) if item]
    else:
        for item in values:
            if isinstance(item, str):
                raw_values.extend(piece for piece in re.split(r"[,\s]+", item) if piece)
            elif item not in (None, ""):
                raw_values.append(item)

    normalized: list[str] = []
    for item in raw_values:
        framework = normalize_executor_framework_name(item)
        if framework in SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES and framework not in normalized:
            normalized.append(framework)
    if normalized:
        return normalized
    return [
        normalize_executor_framework_name(item)
        for item in default
        if normalize_executor_framework_name(item)
    ]


def executor_framework_content_key(framework: str) -> str:
    """
    High Level Purpose:
        In circumstances like hydrating, exporting, or dispatching executable artifacts, helps with choosing the content field that carries the framework-specific body.

    Reference to Theory:
        Supports executable artifact persistence by separating semantic identity from the specific external execution body used to realize it.

    Example Input Output:
        Input: `executor_framework_content_key(framework='ansible')`
        Output: 'ansible_playbook'

    Args:
        framework: Value for `framework` used by `executor_framework_content_key`. Expected type: `str`.

    Returns:
        str: Result produced by `executor_framework_content_key`.
    """
    normalized = normalize_executor_framework_name(framework)
    return EXECUTOR_FRAMEWORK_CONTENT_KEYS.get(normalized, "executable_body")


def ability_executor_framework(
    *,
    representation: str = "",
    content: Mapping[str, Any] | None = None,
) -> str:
    """
    High Level Purpose:
        In circumstances like runtime dispatch and artifact normalization, helps with recovering which executor framework an ability artifact actually targets.

    Reference to Theory:
        Supports governed reuse by making external execution choice derivable from stored artifact constitution.

    Example Input Output:
        Input: `ability_executor_framework(representation='shell_script', content={'executor_framework': 'bash'})`
        Output: 'bash'

    Args:
        representation: Value for `representation` used by `ability_executor_framework`. Expected type: `str`. Defaults to `''`.
        content: Value for `content` used by `ability_executor_framework`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `ability_executor_framework`.
    """
    payload = dict(content) if isinstance(content, Mapping) else {}
    explicit = normalize_executor_framework_name(payload.get("executor_framework", ""))
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
    script_language = normalize_executor_framework_name(payload.get("script_language", ""))
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
    """
    High Level Purpose:
        In circumstances like runtime execution or export/import checks, helps with retrieving the actual executable body from an ability artifact regardless of which framework it uses.

    Reference to Theory:
        Supports executable-boundary reuse by giving one stable read path for the realized body while keeping framework-specific storage fields intact.

    Example Input Output:
        Input: `ability_executable_text(representation='python_script', content={'python_script': 'def main():\\n    return 3'})`
        Output: 'def main():\n    return 3'

    Args:
        representation: Value for `representation` used by `ability_executable_text`. Expected type: `str`. Defaults to `''`.
        content: Value for `content` used by `ability_executable_text`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        str: Result produced by `ability_executable_text`.
    """
    payload = dict(content) if isinstance(content, Mapping) else {}
    framework = ability_executor_framework(representation=representation, content=payload)
    key = executor_framework_content_key(framework)
    return str(payload.get(key, "")).strip()
