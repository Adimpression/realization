# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from realized_core_semantics.applied_model import CrossBoundaryResult
from realized_core_runtime import measured_performance
from realized_host_interaction.realizers import HostRealizerProvider
from realized_core_runtime.executor_support import (
    DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS,
    SUPPORTED_EXECUTOR_FRAMEWORKS_ENV,
    normalize_supported_executor_frameworks,
)
from realized_skill_semantics.execution import (
    EXECUTOR_FRAMEWORK_ALIASES,
    EXECUTOR_FRAMEWORK_CONTENT_KEYS,
    EXECUTOR_FRAMEWORK_REPRESENTATIONS,
    SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES,
    ability_executable_text,
    ability_executor_framework,
    executor_framework_content_key,
    normalize_executor_framework_name,
)
from realized_core_runtime.fence_extraction import (
    extract_markdown_fences,
    fence_strategy_for_record,
)
from realized_core_runtime.host_abi import wasm_skill_abi_version
from realized_core_runtime.python_brokerization import (
    brokerize_python_main_for_host_brokers,
    literal_host_broker_names_from_python,
)
from realized_core_runtime.python_transport import python_skill_host_bridge
from realized_core_runtime.temporary import runtime_temporary_directory
from realized_core_semantics.semantic_text import collapse_ws, ordered_unique, titleize_semantic_unit
from realized_core_runtime.wasm import execute_wasm_cross_boundary


GENERIC_FENCE_HEADING_PHRASES = {
    "core capability",
    "capability",
    "executable relation",
    "executable python relation",
    "executable bash relation",
    "executable shell relation",
    "executable ansible relation",
    "inputs and outputs",
    "input and output",
    "natural language paraphrases",
    "natural-language paraphrases",
    "one sentence summary",
    "one-sentence summary",
    "summary",
    "notes",
    "examples",
    "example",
}

PYTHON_SKILL_HOST_PACKAGE_DEPENDENCIES = (
    "realized_core_governance",
    "realized_core_runtime",
    "realized_core_semantics",
    "realized_host_interaction",
    "realized_skill_semantics",
)


def _python_skill_host_import_roots() -> list[str]:
    """Return only the import roots required by the child host bridge."""
    roots: list[str] = []
    for package_name in PYTHON_SKILL_HOST_PACKAGE_DEPENDENCIES:
        spec = importlib.util.find_spec(package_name)
        locations = list(spec.submodule_search_locations or []) if spec else []
        if locations:
            roots.append(str(Path(locations[0]).resolve().parent))
    return ordered_unique(roots)


def executor_framework_representation(framework: str) -> str:
    """
    High Level Purpose:
        In circumstances like storing or importing executor-backed abilities, helps with mapping an executor framework to the representation that should describe the learned artifact body.

    Reference to Theory:
        Supports the artifact/boundary layer by keeping external execution form aligned with stored semantic identity.

    Example Input Output:
        Input: `executor_framework_representation(framework='bash')`
        Output: 'shell_script'

    Args:
        framework: Value for `framework` used by `executor_framework_representation`. Expected type: `str`.

    Returns:
        str: Result produced by `executor_framework_representation`.
    """
    normalized = normalize_executor_framework_name(framework)
    return EXECUTOR_FRAMEWORK_REPRESENTATIONS.get(normalized, "code")


def supported_executor_framework_prompt_block(supported_executors: Sequence[str]) -> str:
    """
    High Level Purpose:
        In circumstances like LLM-guided markdown functionalization, helps with stating exactly which executor frameworks are admissible so the model can align learned abilities to the active execution surface.

    Reference to Theory:
        Supports governed artifact admission by exposing the allowed external execution boundary before semantic ability emission.

    Example Input Output:
        Input: `supported_executor_framework_prompt_block(supported_executors=['python3', 'bash'])`
        Output: 'Supported executor frameworks for this training run: ...'

    Args:
        supported_executors: Value for `supported_executors` used by `supported_executor_framework_prompt_block`. Expected type: `Sequence[str]`.

    Returns:
        str: Result produced by `supported_executor_framework_prompt_block`.
    """
    normalized = normalize_supported_executor_frameworks(supported_executors)
    if not normalized:
        normalized = list(DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS)
    lines = ["Supported executor frameworks for this training run:"]
    if "python3" in normalized:
        lines.append("- python3: use representation `python_script`, content.python_script, script_language `python`, and entrypoint `main`.")
    if "bash" in normalized:
        lines.append("- bash: use representation `shell_script`, content.shell_script, script_language `bash`, and treat the fenced shell body as the executable surface.")
    if "ansible" in normalized:
        lines.append("- ansible: use representation `ansible_playbook`, content.ansible_playbook, and script_language `ansible`.")
    if "wasm_wasi" in normalized:
        lines.append("- wasm_wasi: use representation `wasm_module`, content.wasm_module, script_language `wasm`, entrypoint `run`, and the governed Wasm ABI version `"
                     + wasm_skill_abi_version()
                     + "`.")
    lines.append("- Prefer a direct match to one of the supported executor frameworks when the source material already presents an executable relation in that framework.")
    lines.append("- If no plugged in executor supports a fenced executable snippet, do not emit an ability artifact for that fence and preserve the failure explicitly.")
    return "\n".join(lines)


def executor_framework_for_strategy(
    strategy: Mapping[str, Any],
    supported_executors: Sequence[str],
) -> str:
    """
    High Level Purpose:
        In circumstances like markdown fence learning, helps with deciding whether one extracted fenced strategy has a directly supported executor in the active training configuration.

    Reference to Theory:
        Supports governed executable admission by checking framework support before ability emission rather than after persistence.

    Example Input Output:
        Input: `executor_framework_for_strategy(strategy={'recommended_representation': 'python_script'}, supported_executors=['python3'])`
        Output: 'python3'

    Args:
        strategy: Value for `strategy` used by `executor_framework_for_strategy`. Expected type: `Mapping[str, Any]`.
        supported_executors: Value for `supported_executors` used by `executor_framework_for_strategy`. Expected type: `Sequence[str]`.

    Returns:
        str: Result produced by `executor_framework_for_strategy`.
    """
    supported = set(normalize_supported_executor_frameworks(supported_executors))
    representation = str(strategy.get("recommended_representation", "")).strip().lower()
    language = str(strategy.get("language", "")).strip().lower()
    if representation == "python_script" or language in {"py", "python"}:
        return "python3" if "python3" in supported else ""
    if representation == "shell_script" or language in {"bash", "sh", "shell", "zsh"}:
        return "bash" if "bash" in supported else ""
    if representation == "ansible_playbook" or language in {"ansible", "ansible-playbook", "yaml", "yml"}:
        return "ansible" if "ansible" in supported else ""
    if representation == "wasm_module" or language in {"wasm", "wat", "wast"}:
        return "wasm_wasi" if "wasm_wasi" in supported else ""
    return ""


def _shell_parameter_names(code: str) -> list[str]:
    names = re.findall(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", str(code or ""))
    return ordered_unique(name for name in names if name not in {"PATH", "HOME", "PWD", "SHELL"})


def _ansible_parameter_names(code: str) -> list[str]:
    names = re.findall(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}", str(code or ""))
    return ordered_unique(names)


def _json_scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def _shell_env_key_fragment(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_]", "_", collapse_ws(str(value))).strip("_")
    return text.upper()


def _populate_nested_shell_env(
    env: dict[str, str],
    *,
    prefix: str,
    value: Any,
) -> None:
    if not prefix:
        return
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            fragment = _shell_env_key_fragment(key)
            if not fragment:
                continue
            _populate_nested_shell_env(
                env,
                prefix=f"{prefix}_{fragment}",
                value=nested_value,
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return
    if prefix not in {"PATH", "HOME", "PWD", "SHELL"}:
        env[prefix] = _json_scalar_text(value)


def _mount_aware_screenshot_shell_script() -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            'mount_name=\"${PAYLOAD_MOUNT:-${MOUNT:-}}\"',
            'relative_path=\"${PAYLOAD_RELATIVE_PATH:-${RELATIVE_PATH:-}}\"',
            'target_path=\"$(python3 - <<'"'"'PY'"'"'',
            "import json",
            "import os",
            "from pathlib import Path",
            "",
            'mount_name = os.environ.get(\"PAYLOAD_MOUNT\") or os.environ.get(\"MOUNT\") or \"\"',
            'relative_path = os.environ.get(\"PAYLOAD_RELATIVE_PATH\") or os.environ.get(\"RELATIVE_PATH\") or \"\"',
            'mounts = json.loads(os.environ.get(\"BSSC_VIRTUAL_MOUNTS_JSON\", \"{}\") or \"{}\")',
            "root = \"\"",
            "if isinstance(mounts, dict):",
            "    mount_record = mounts.get(mount_name, {})",
            "    if isinstance(mount_record, dict):",
            "        root = str(mount_record.get(\"root\", \"\") or \"\")",
            "if not mount_name or not relative_path or not root:",
            "    raise SystemExit(1)",
            "target = Path(root) / relative_path",
            "target.parent.mkdir(parents=True, exist_ok=True)",
            "print(target)",
            "PY",
            ')\"',
            "",
            'screencapture -x \"$target_path\"',
            "",
            "python3 - <<'PY'",
            "import json",
            "import os",
            "import sys",
            "",
            "payload = {",
            '    \"status\": \"ok\",',
            '    \"answer\": \"captured\",',
            '    \"result\": {',
            '        \"status\": \"captured\",',
            '        \"mount\": os.environ.get(\"PAYLOAD_MOUNT\") or os.environ.get(\"MOUNT\") or \"\",',
            '        \"relative_path\": os.environ.get(\"PAYLOAD_RELATIVE_PATH\") or os.environ.get(\"RELATIVE_PATH\") or \"\",',
            "    },",
            '    \"notes\": [],',
            "}",
            "sys.stdout.write(json.dumps(payload, sort_keys=True))",
            "sys.stdout.write(\"\\n\")",
            "PY",
        ]
    )


def normalize_ability_runtime_content(
    content: Mapping[str, Any] | None,
    *,
    title: str = "",
) -> dict[str, Any]:
    normalized = dict(content) if isinstance(content, Mapping) else {}
    framework = normalize_executor_framework_name(normalized.get("executor_framework", ""))
    if framework == "python3":
        python_script = str(normalized.get("python_script", "") or "")
        if python_script and "governed_host_brokers" not in normalized:
            broker_names = literal_host_broker_names_from_python(python_script)
            if broker_names:
                normalized["governed_host_brokers"] = broker_names
        return normalized
    if framework != "bash":
        return normalized
    shell_script = str(normalized.get("shell_script", "") or "")
    if not shell_script:
        return normalized
    title_casefold = collapse_ws(str(title)).casefold()
    input_names = {
        collapse_ws(str(name)).casefold()
        for name in dict(normalized.get("input_contract", {})).keys()
        if collapse_ws(str(name))
    }
    if (
        "screenshot" in title_casefold
        and "screencapture" in shell_script.casefold()
        and "BSSC_VIRTUAL_MOUNTS_JSON" not in shell_script
        and ("payload" in input_names or {"mount", "relative_path"} <= input_names)
    ):
        normalized["shell_script"] = _mount_aware_screenshot_shell_script()
        authorities = [
            collapse_ws(str(item))
            for item in normalized.get("governed_authorities", [])
            if collapse_ws(str(item))
        ]
        for required in ("execute", "write"):
            if required not in authorities:
                authorities.append(required)
        normalized["governed_authorities"] = authorities
        broker_names = [
            collapse_ws(str(item))
            for item in normalized.get("governed_host_brokers", [])
            if collapse_ws(str(item))
        ]
        if "macos.capture_screenshot" not in broker_names:
            broker_names.append("macos.capture_screenshot")
        normalized["governed_host_brokers"] = broker_names
    return normalized


def bash_command_block_ability_script(raw_shell_body: str) -> str:
    """
    High Level Purpose:
        In circumstances like learning a directly fenced shell command as a reusable executable artifact, helps with wrapping the raw shell body in a small JSON-emitting harness so the governed runtime can treat it like other executable abilities.

    Reference to Theory:
        Supports executable artifact admission by turning a raw command substrate into a boundary-safe callable result surface.

    Example Input Output:
        Input: `bash_command_block_ability_script(raw_shell_body='open -a \"Google Chrome\" \"$url\"')`
        Output: '#!/usr/bin/env bash\nset -euo pipefail\n...'

    Args:
        raw_shell_body: Value for `raw_shell_body` used by `bash_command_block_ability_script`. Expected type: `str`.

    Returns:
        str: Result produced by `bash_command_block_ability_script`.
    """
    body = str(raw_shell_body or "").strip()
    if not body:
        return ""
    result_json = json.dumps(
        {
            "status": "ok",
            "answer": "executed",
            "result": {"status": "executed"},
            "notes": [],
        },
        sort_keys=True,
    )
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        "# BSSC exposes the structured input payload as JSON and as env vars for shell-based abilities.\n"
        f"{body}\n\n"
        "printf '%s\\n' "
        + json.dumps(result_json)
        + "\n"
    ).strip()


def _looks_like_generic_fence_heading(text: str) -> bool:
    """
    High Level Purpose:
        In circumstances like choosing a reusable capability title from markdown heading paths, helps with rejecting local meta-section labels such as `Core capability` or `Inputs and outputs` so the learned title stays semantically specific.

    Reference to Theory:
        Supports direct executor-aligned learning by keeping the learned identity tied to the capability itself instead of to document scaffolding.

    Example Input Output:
        Input: `_looks_like_generic_fence_heading(text='Executable Python relation')`
        Output: True

    Args:
        text: Value for `text` used by `_looks_like_generic_fence_heading`. Expected type: `str`.

    Returns:
        bool: Result produced by `_looks_like_generic_fence_heading`.
    """
    normalized = collapse_ws(str(text or "").strip()).lower()
    if not normalized:
        return True
    normalized = re.sub(r"^[0-9]+[.)-]?\s*", "", normalized).strip()
    return normalized in GENERIC_FENCE_HEADING_PHRASES


def _preferred_fence_heading_text(path: Sequence[str], fallback_heading: str) -> str:
    """
    High Level Purpose:
        In circumstances like learning executable abilities from fenced markdown snippets, helps with preferring the nearest non-generic semantic heading so the learned title can match future prompts directly.

    Reference to Theory:
        Supports direct executor-aligned learning by preserving semantic identity from the document path instead of inheriting local scaffold headings.

    Example Input Output:
        Input: `_preferred_fence_heading_text(path=['Launch Browser At Specific URL', 'Executable Python relation'], fallback_heading='Executable Python relation')`
        Output: 'Launch Browser At Specific URL'

    Args:
        path: Value for `path` used by `_preferred_fence_heading_text`. Expected type: `Sequence[str]`.
        fallback_heading: Value for `fallback_heading` used by `_preferred_fence_heading_text`. Expected type: `str`.

    Returns:
        str: Result produced by `_preferred_fence_heading_text`.
    """
    candidates = [collapse_ws(str(item).strip()) for item in path if collapse_ws(str(item).strip())]
    for candidate in reversed(candidates):
        if not _looks_like_generic_fence_heading(candidate):
            return candidate
    return collapse_ws(str(fallback_heading or "").strip()) or "Executable capability"


def supported_fence_learning_records(
    source_path: Path,
    *,
    supported_executors: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like markdown-learning over mixed fenced snippets, helps with converting supported fenced executables into learning-ready encounter records while reporting unsupported fences explicitly.

    Reference to Theory:
        Supports decomposition and governed artifact admission by separating supported executable substrates from unsupported ones before semantic ability synthesis begins.

    Example Input Output:
        Input: `supported_fence_learning_records(source_path=Path('/tmp/device.md'), supported_executors=['python3', 'bash'])`
        Output: ([{'encounter_id': 'fence_1', 'executor_framework': 'bash'}], [{'message': 'no plugged in executor supports applescript'}])

    Args:
        source_path: Value for `source_path` used by `supported_fence_learning_records`. Expected type: `Path`.
        supported_executors: Value for `supported_executors` used by `supported_fence_learning_records`. Expected type: `Sequence[str]`.

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: Result produced by `supported_fence_learning_records`.
    """
    text = source_path.read_text(encoding="utf-8")
    records = extract_markdown_fences(text, source_path=str(source_path))
    supported: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    supported_list = normalize_supported_executor_frameworks(supported_executors)
    for record in records:
        strategy = fence_strategy_for_record(record)
        strategy_dict = {
            "source_path": strategy.source_path,
            "fence_index": strategy.fence_index,
            "language": strategy.language,
            "heading_path": list(strategy.heading_path),
            "strategy_name": strategy.strategy_name,
            "recommended_artifact_type": strategy.recommended_artifact_type,
            "recommended_representation": strategy.recommended_representation,
            "executable": bool(strategy.executable),
            "entrypoint_name": strategy.entrypoint_name,
            "parameter_names": list(strategy.parameter_names),
            "dependency_metadata_kind": strategy.dependency_metadata_kind,
            "inline_imports": list(strategy.inline_imports),
            "detected_calls": list(strategy.detected_calls),
            "return_signals": list(strategy.return_signals),
            "semantic_lines": list(strategy.semantic_lines),
            "notes": list(strategy.notes),
        }
        framework = executor_framework_for_strategy(strategy_dict, supported_list)
        if framework:
            parameter_names = list(strategy.parameter_names)
            if framework == "bash" and not parameter_names:
                parameter_names = _shell_parameter_names(record.code)
            if framework == "ansible" and not parameter_names:
                parameter_names = _ansible_parameter_names(record.code)
            heading = list(strategy.heading_path)[-1] if strategy.heading_path else f"Fence {strategy.fence_index}"
            preferred_heading = _preferred_fence_heading_text(strategy.heading_path, heading)
            supported.append(
                {
                    "encounter_id": f"fence_{strategy.fence_index}",
                    "heading": heading,
                    "path": list(strategy.heading_path),
                    "sections": list(strategy.heading_path),
                    "candidate_kinds": ["template", "fence", framework],
                    "encounter_kind": "template",
                    "equation_bearing": False,
                    "parameterized": bool(parameter_names),
                    "reusable": bool(strategy.executable),
                    "extracted_form": "; ".join(strategy.semantic_lines[:3]),
                    "paragraphs": list(record.preceding_paragraphs[-2:]),
                    "bullets": list(strategy.semantic_lines),
                    "equations": [],
                    "code_blocks": [record.code],
                    "fence_language": record.language,
                    "executor_framework": framework,
                    "entrypoint_name": strategy.entrypoint_name,
                    "parameter_names": parameter_names,
                    "dependency_metadata_kind": strategy.dependency_metadata_kind,
                    "inline_imports": list(strategy.inline_imports),
                    "detected_calls": list(strategy.detected_calls),
                    "return_signals": list(strategy.return_signals),
                    "artifact_title_hint": titleize_semantic_unit(preferred_heading),
                }
            )
            continue
        failures.append(
            {
                "source_path": str(source_path),
                "fence_index": strategy.fence_index,
                "language": record.language or "plain",
                "heading_path": list(strategy.heading_path),
                "strategy_name": strategy.strategy_name,
                "message": f"no plugged in executor supports {record.language or 'plain'}",
            }
        )
    return supported, failures


def fence_encounter_ability_payload(
    encounter: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like learning directly from a supported fenced executable snippet, helps with projecting that snippet into an ability payload that already matches the plugged executor framework.

    Reference to Theory:
        Supports governed executable learning by admitting a direct executor-aligned body instead of forcing the LLM to reconstruct it from prose.

    Example Input Output:
        Input: `fence_encounter_ability_payload(encounter={'heading': 'Executable Python relation', 'executor_framework': 'python3', 'code_blocks': ['def main(url: str):\\n    return {\"url\": url}']})`
        Output: {'artifact_type': 'ability', 'representation': 'python_script', 'content': {'python_script': 'def main(url: str):\\n    return {\"url\": url}'}}`

    Args:
        encounter: Value for `encounter` used by `fence_encounter_ability_payload`. Expected type: `Mapping[str, Any]`.

    Returns:
        dict[str, Any] | None: Result produced by `fence_encounter_ability_payload`.
    """
    framework = normalize_executor_framework_name(encounter.get("executor_framework", ""))
    code_blocks = [str(item).strip() for item in encounter.get("code_blocks", []) if str(item).strip()] if isinstance(encounter.get("code_blocks", []), list) else []
    code_block = code_blocks[0] if code_blocks else ""
    if not framework or not code_block:
        return None

    heading = collapse_ws(str(encounter.get("heading", "")).strip()) or "Executable capability"
    path = [collapse_ws(str(item).strip()) for item in encounter.get("path", []) if collapse_ws(str(item).strip())] if isinstance(encounter.get("path", []), list) else []
    preferred_heading = _preferred_fence_heading_text(path, heading)
    title = (
        titleize_semantic_unit(str(encounter.get("artifact_title_hint", "")).strip())
        or titleize_semantic_unit(preferred_heading)
        or titleize_semantic_unit(heading)
        or heading
    )
    parameter_names = [str(item).strip() for item in encounter.get("parameter_names", []) if str(item).strip()] if isinstance(encounter.get("parameter_names", []), list) else []
    question = f"How do you execute {title.lower()}?"
    if framework == "python3" and parameter_names:
        question = f"How do you use {title.lower()} from {', '.join(parameter_names)}?"
    aliases = ordered_unique(
        [title]
        + ([preferred_heading] if preferred_heading else [])
        + [heading]
        + path
        + [str(item).strip() for item in encounter.get("bullets", []) if str(item).strip()]
    )
    content: dict[str, Any] = {
        "entrypoint": str(encounter.get("entrypoint_name", "")).strip() or "main",
        "script_language": "python" if framework == "python3" else ("bash" if framework == "bash" else "ansible"),
        "executor_framework": framework,
        "input_contract": {name: "required input value" for name in parameter_names},
        "output_contract": {"result": "execution result"},
    }
    representation = executor_framework_representation(framework)
    if framework == "python3":
        brokerized = brokerize_python_main_for_host_brokers(code_block)
        if brokerized is not None:
            content["python_script"] = brokerized.python_code
            content["governed_host_brokers"] = list(brokerized.broker_names)
            content["governed_authorities"] = list(brokerized.authorities)
        else:
            content["python_script"] = code_block
        content["dependencies"] = ["msgspec", "orjson"]
    elif framework == "bash":
        content["shell_script"] = bash_command_block_ability_script(code_block)
        content["dependencies"] = []
    elif framework == "ansible":
        content["ansible_playbook"] = code_block
        content["entrypoint"] = "playbook"
        content["dependencies"] = []
    elif framework == "wasm_wasi":
        content["wasm_module"] = code_block
        content["entrypoint"] = "run"
        content["dependencies"] = []
        content["wasm_abi_version"] = wasm_skill_abi_version()
        content["wasm_format"] = "wat"
    else:
        return None
    content = normalize_ability_runtime_content(content, title=title)

    return {
        "artifact_type": "ability",
        "title": title,
        "semantic_unit": title,
        "question": question,
        "related_titles": [],
        "relation_rationale": "",
        "aliases": aliases,
        "component_nots": [titleize_semantic_unit(name) for name in parameter_names if titleize_semantic_unit(name)],
        "composed_not": title,
        "sections": [str(item).strip() for item in encounter.get("sections", []) if str(item).strip()] if isinstance(encounter.get("sections", []), list) else [],
        "why_reusable": "The source markdown already presents this executable relation directly in a supported executor framework.",
        "encounter_id": str(encounter.get("encounter_id", "")).strip(),
        "encounter_kind": "template",
        "equation_bearing": False,
        "parameterized": bool(parameter_names),
        "representation": representation,
        "scope": f"reuse when later prompts ask for {title.lower()} under compatible inputs",
        "reusability": "broad_reuse",
        "admissibility": "admitted",
        "learning_relation": "extends_parameters",
        "constraints": ["derived directly from a supported fenced executable snippet"],
        "content": content,
    }


def _python_cross_boundary(
    python_script: str,
    stdin_payload: Any,
    *,
    timeout_seconds: float | None = None,
    host_runtime_context: Mapping[str, Any] | None = None,
    realizer_provider: HostRealizerProvider | None = None,
) -> CrossBoundaryResult:
    script_text = str(python_script or "").strip()
    if not script_text:
        return CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr="cross_boundary received an empty python script.",
            notes=["No executable script text was supplied."],
        )

    try:
        timeout = max(1.0, float(timeout_seconds if timeout_seconds is not None else os.getenv("FUNCTION_BOUNDARY_TIMEOUT_SECONDS", "45")))
    except ValueError:
        timeout = 45.0

    stdin_text = json.dumps(stdin_payload, sort_keys=True)
    with runtime_temporary_directory(prefix="bssc_cross_boundary_") as temp_dir:
        script_path = Path(temp_dir) / "boundary_artifact.py"
        script_path.write_text(script_text if script_text.endswith("\n") else f"{script_text}\n", encoding="utf-8")
        host_trace_path = Path(temp_dir) / "host_trace.jsonl"
        command = ["uv", "run", "--no-project", str(script_path)]
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "").strip()
        pythonpath = _python_skill_host_import_roots()
        if existing_pythonpath:
            pythonpath.extend(existing_pythonpath.split(os.pathsep))
        env["PYTHONPATH"] = os.pathsep.join(ordered_unique(pythonpath))
        env["BSSC_PYTHON_SKILL_HOST_CONTEXT"] = json.dumps(dict(host_runtime_context or {}), sort_keys=True)
        env["BSSC_PYTHON_SKILL_HOST_TRACE_PATH"] = str(host_trace_path)
        bridge = (
            python_skill_host_bridge(
                realizer_provider,
                governance_context=dict(host_runtime_context or {}),
            )
            if realizer_provider is not None
            else nullcontext({})
        )
        with bridge as bridge_environment:
            env.update(bridge_environment)
            try:
                completed = subprocess.run(
                    command,
                    input=stdin_text,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                return CrossBoundaryResult(
                    ok=False,
                    command=command,
                    exit_code=124,
                    stdout=exc.stdout or "",
                    stderr=exc.stderr or f"cross_boundary timed out after {timeout:.1f}s.",
                    notes=["The executable artifact did not finish before the boundary timeout."],
                )
            except Exception as exc:
                return CrossBoundaryResult(
                    ok=False,
                    command=command,
                    exit_code=1,
                    stdout="",
                    stderr=str(exc),
                    notes=["cross_boundary failed before process completion."],
                )

        stdout = str(completed.stdout or "").strip()
        stderr = str(completed.stderr or "").strip()
        parsed_output: Any = None
        result_value: Any = None
        answer_text = ""
        notes: list[str] = []
        host_traces: list[dict[str, Any]] = []

        if host_trace_path.exists():
            for raw_line in host_trace_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    parsed_line = json.loads(line)
                except Exception:
                    continue
                if isinstance(parsed_line, Mapping):
                    host_traces.append(dict(parsed_line))

        if stdout:
            try:
                parsed_output = json.loads(stdout)
            except Exception:
                parsed_output = None
        if isinstance(parsed_output, Mapping):
            parsed_output = dict(parsed_output)
            result_value = parsed_output.get("result")
            answer_text = str(parsed_output.get("answer", "")).strip()
            parsed_notes = parsed_output.get("notes", [])
            if isinstance(parsed_notes, list):
                notes = [str(item).strip() for item in parsed_notes if str(item).strip()]
            if host_traces:
                parsed_output["_bssc_host_traces"] = host_traces

        return CrossBoundaryResult(
            ok=completed.returncode == 0,
            command=command,
            exit_code=int(completed.returncode),
            stdout=stdout,
            stderr=stderr,
            parsed_output=parsed_output,
            result=result_value,
            answer=answer_text,
            notes=notes,
            metadata={"host_traces": host_traces},
        )


def _shell_cross_boundary(
    shell_script: str,
    stdin_payload: Any,
    *,
    shell_binary: str = "bash",
    timeout_seconds: float | None = None,
    host_runtime_context: Mapping[str, Any] | None = None,
) -> CrossBoundaryResult:
    script_text = str(shell_script or "").strip()
    if not script_text:
        return CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr="cross_boundary received an empty shell script.",
            notes=["No executable script text was supplied."],
        )
    shell_path = shutil.which(shell_binary)
    if not shell_path:
        return CrossBoundaryResult(
            ok=False,
            command=[shell_binary],
            exit_code=127,
            stdout="",
            stderr=f"{shell_binary} is not available on PATH.",
            notes=["The requested shell executor is not installed."],
        )

    try:
        timeout = max(1.0, float(timeout_seconds if timeout_seconds is not None else os.getenv("FUNCTION_BOUNDARY_TIMEOUT_SECONDS", "45")))
    except ValueError:
        timeout = 45.0

    stdin_text = json.dumps(stdin_payload, sort_keys=True)
    with runtime_temporary_directory(prefix="bssc_cross_boundary_shell_") as temp_dir:
        script_path = Path(temp_dir) / "boundary_artifact.sh"
        script_path.write_text(script_text if script_text.endswith("\n") else f"{script_text}\n", encoding="utf-8")
        os.chmod(script_path, 0o755)
        env = os.environ.copy()
        env["BSSC_INPUT_JSON"] = stdin_text
        if isinstance(host_runtime_context, Mapping):
            env["BSSC_VIRTUAL_MOUNTS_JSON"] = json.dumps(
                dict(host_runtime_context.get("virtual_mounts", {}))
                if isinstance(host_runtime_context.get("virtual_mounts", {}), Mapping)
                else {},
                sort_keys=True,
            )
            workspace_root = collapse_ws(str(host_runtime_context.get("workspace_root", "")))
            if workspace_root:
                env["BSSC_WORKSPACE_ROOT"] = workspace_root
        if isinstance(stdin_payload, Mapping):
            for key, value in stdin_payload.items():
                key_text = str(key or "").strip()
                if not key_text:
                    continue
                value_text = _json_scalar_text(value)
                if key_text not in {"PATH", "HOME", "PWD", "SHELL"}:
                    env[key_text] = value_text
                upper_key_text = key_text.upper()
                if upper_key_text not in {"PATH", "HOME", "PWD", "SHELL"}:
                    env[upper_key_text] = value_text
                _populate_nested_shell_env(env, prefix=_shell_env_key_fragment(key_text), value=value)
        command = [shell_path, str(script_path)]
        try:
            completed = subprocess.run(
                command,
                input=stdin_text,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            return CrossBoundaryResult(
                ok=False,
                command=command,
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"{shell_binary} execution timed out after {timeout:.1f}s.",
                notes=["The shell-backed artifact did not finish before the boundary timeout."],
            )
        except Exception as exc:
            return CrossBoundaryResult(
                ok=False,
                command=command,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                notes=["Shell-backed execution failed before process completion."],
            )

        stdout = str(completed.stdout or "").strip()
        stderr = str(completed.stderr or "").strip()
        parsed_output: Any = None
        result_value: Any = None
        answer_text = ""
        notes: list[str] = []
        stdout_lines = [line for line in stdout.splitlines() if line.strip()]
        json_candidates = [stdout] + list(reversed(stdout_lines))
        for candidate in json_candidates:
            try:
                parsed_output = json.loads(candidate)
                break
            except Exception:
                continue
        if isinstance(parsed_output, Mapping):
            result_value = parsed_output.get("result")
            answer_text = str(parsed_output.get("answer", "")).strip()
            parsed_notes = parsed_output.get("notes", [])
            if isinstance(parsed_notes, list):
                notes = [str(item).strip() for item in parsed_notes if str(item).strip()]
        return CrossBoundaryResult(
            ok=completed.returncode == 0,
            command=command,
            exit_code=int(completed.returncode),
            stdout=stdout,
            stderr=stderr,
            parsed_output=parsed_output,
            result=result_value,
            answer=answer_text,
            notes=notes,
        )


def _ansible_cross_boundary(
    ansible_playbook: str,
    stdin_payload: Any,
    *,
    timeout_seconds: float | None = None,
) -> CrossBoundaryResult:
    playbook_text = str(ansible_playbook or "").strip()
    if not playbook_text:
        return CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr="cross_boundary received an empty ansible playbook.",
            notes=["No executable playbook text was supplied."],
        )
    ansible_binary = shutil.which("ansible-playbook")
    if not ansible_binary:
        return CrossBoundaryResult(
            ok=False,
            command=["ansible-playbook"],
            exit_code=127,
            stdout="",
            stderr="ansible-playbook is not available on PATH.",
            notes=["The requested ansible executor is not installed."],
        )
    try:
        timeout = max(1.0, float(timeout_seconds if timeout_seconds is not None else os.getenv("FUNCTION_BOUNDARY_TIMEOUT_SECONDS", "45")))
    except ValueError:
        timeout = 45.0
    with runtime_temporary_directory(prefix="bssc_cross_boundary_ansible_") as temp_dir:
        playbook_path = Path(temp_dir) / "boundary_playbook.yml"
        vars_path = Path(temp_dir) / "boundary_vars.json"
        playbook_path.write_text(playbook_text if playbook_text.endswith("\n") else f"{playbook_text}\n", encoding="utf-8")
        vars_path.write_text(json.dumps(stdin_payload, sort_keys=True), encoding="utf-8")
        command = [
            ansible_binary,
            "-i",
            "localhost,",
            "-c",
            "local",
            str(playbook_path),
            "--extra-vars",
            f"@{vars_path}",
        ]
        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CrossBoundaryResult(
                ok=False,
                command=command,
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"ansible execution timed out after {timeout:.1f}s.",
                notes=["The ansible-backed artifact did not finish before the boundary timeout."],
            )
        except Exception as exc:
            return CrossBoundaryResult(
                ok=False,
                command=command,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                notes=["Ansible-backed execution failed before process completion."],
            )
        stdout = str(completed.stdout or "").strip()
        stderr = str(completed.stderr or "").strip()
        parsed_output = {
            "status": "ok" if completed.returncode == 0 else "error",
            "answer": "",
            "result": {"stdout": stdout, "stderr": stderr},
            "notes": [],
        }
        return CrossBoundaryResult(
            ok=completed.returncode == 0,
            command=command,
            exit_code=int(completed.returncode),
            stdout=stdout,
            stderr=stderr,
            parsed_output=parsed_output,
            result=parsed_output["result"],
            answer="",
            notes=[],
        )


@measured_performance("effect_latency_ns")
def execute_cross_boundary(
    *,
    framework: str,
    executable_text: str,
    stdin_payload: Any,
    timeout_seconds: float | None = None,
    host_runtime_context: Mapping[str, Any] | None = None,
    realizer_provider: HostRealizerProvider | None = None,
) -> CrossBoundaryResult:
    """
    High Level Purpose:
        In circumstances like runtime artifact invocation across multiple supported external executors, helps with dispatching the executable body to the correct boundary runner.

    Reference to Theory:
        Supports governed cross-boundary execution by routing ability artifacts through the executor surface they were admitted under.

    Example Input Output:
        Input: `execute_cross_boundary(framework='bash', executable_text='echo ok', stdin_payload={'url': 'https://example.com'})`
        Output: CrossBoundaryResult(ok=True, command=['/bin/bash', '/tmp/...'], exit_code=0, stdout='...')

    Args:
        framework: Value for `framework` used by `execute_cross_boundary`. Expected type: `str`.
        executable_text: Value for `executable_text` used by `execute_cross_boundary`. Expected type: `str`.
        stdin_payload: Value for `stdin_payload` used by `execute_cross_boundary`. Expected type: `Any`.
        timeout_seconds: Value for `timeout_seconds` used by `execute_cross_boundary`. Expected type: `float | None`. Defaults to `None`.

    Returns:
        CrossBoundaryResult: Result produced by `execute_cross_boundary`.
    """
    normalized = normalize_executor_framework_name(framework)
    if normalized == "python3":
        return _python_cross_boundary(
            executable_text,
            stdin_payload,
            timeout_seconds=timeout_seconds,
            host_runtime_context=host_runtime_context,
            realizer_provider=realizer_provider,
        )
    if normalized == "bash":
        return _shell_cross_boundary(
            executable_text,
            stdin_payload,
            shell_binary="bash",
            timeout_seconds=timeout_seconds,
            host_runtime_context=host_runtime_context,
        )
    if normalized == "ansible":
        return _ansible_cross_boundary(executable_text, stdin_payload, timeout_seconds=timeout_seconds)
    if normalized == "wasm_wasi":
        return execute_wasm_cross_boundary(
            executable_text,
            stdin_payload,
            timeout_seconds=timeout_seconds,
            host_runtime_context=host_runtime_context,
            realizer_provider=realizer_provider,
        )
    return CrossBoundaryResult(
        ok=False,
        command=[],
        exit_code=1,
        stdout="",
        stderr=f"Unsupported executor framework: {framework}.",
        notes=["No runtime executor is registered for this artifact."],
    )
