# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws

HOST_ABI_VERSION = "bssc.host.v1"
WASM_SKILL_ABI_VERSION = "bssc.wasm.v1"
WASM_HOST_BROKER_NAMES = (
    "fs.read_mount",
    "fs.write_mount",
    "fs.list_mount",
    "fs.find_mount",
    "store.named_query",
    "store.skill_state",
    "tool.invoke",
    "skill.invoke",
)

_TYPE_LABELS = {"str", "bool", "int", "float", "mapping", "list", "any"}

WASM_SKILL_ABI: dict[str, Any] = {
    "version": WASM_SKILL_ABI_VERSION,
    "execution_model": "embedded_wasmtime_governed_hostcalls",
    "ambient_capabilities": {
        "filesystem": False,
        "network": False,
        "sqlite": False,
        "clock": False,
        "random": False,
        "environment": False,
        "stdio": False,
    },
    "imports": {
        "bssc": {
            "input_len": {"params": [], "results": ["i32"]},
            "read_input": {"params": ["i32"], "results": ["i32"]},
            "write_output": {"params": ["i32", "i32"], "results": ["i32"]},
            "hostcall": {"params": ["i32", "i32"], "results": ["i32"]},
            "read_hostcall_response": {"params": ["i32"], "results": ["i32"]},
        }
    },
    "exports": {
        "memory": {"kind": "memory"},
        "run": {"params": [], "results": ["i32"]},
    },
    "input_transport": "utf8_json_via_bssc_imports",
    "output_transport": "utf8_json_via_bssc_imports",
    "hostcall_transport": "utf8_json_request_response_via_bssc_imports",
    "host_broker_subset": list(WASM_HOST_BROKER_NAMES),
}

HOST_BROKER_ABI: dict[str, dict[str, Any]] = {
    "fs.read_text": {
        "stability": "transitional",
        "authority": "read",
        "required": {"path": "str"},
        "optional": {},
    },
    "fs.write_text": {
        "stability": "transitional",
        "authority": "write",
        "required": {"path": "str", "text": "str"},
        "optional": {"append": "bool"},
    },
    "fs.list_directory": {
        "stability": "transitional",
        "authority": "read",
        "required": {"path": "str"},
        "optional": {},
    },
    "fs.read_mount": {
        "stability": "stable",
        "authority": "read",
        "required": {"mount": "str"},
        "optional": {"relative_path": "str"},
    },
    "fs.write_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {"mount": "str", "text": "str"},
        "optional": {"relative_path": "str", "append": "bool"},
    },
    "fs.list_mount": {
        "stability": "stable",
        "authority": "read",
        "required": {"mount": "str"},
        "optional": {"relative_path": "str"},
    },
    "fs.find_mount": {
        "stability": "stable",
        "authority": "read",
        "required": {"mount": "str", "suffix": "str"},
        "optional": {"relative_path": "str"},
    },
    "fs.copy_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {
            "source_mount": "str",
            "source_relative_path": "str",
            "destination_mount": "str",
            "destination_relative_path": "str",
        },
        "optional": {},
    },
    "fs.move_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {
            "source_mount": "str",
            "source_relative_path": "str",
            "destination_mount": "str",
            "destination_relative_path": "str",
        },
        "optional": {},
    },
    "fs.delete_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {"mount": "str", "relative_path": "str"},
        "optional": {},
    },
    "fs.create_zip_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {
            "source_mount": "str",
            "source_relative_path": "str",
            "destination_mount": "str",
            "destination_relative_path": "str",
        },
        "optional": {},
    },
    "fs.extract_zip_mount": {
        "stability": "stable",
        "authority": "write",
        "required": {
            "source_mount": "str",
            "source_relative_path": "str",
            "destination_mount": "str",
            "destination_relative_path": "str",
        },
        "optional": {},
    },
    "store.sqlite_query": {
        "stability": "transitional",
        "authority": "read",
        "required": {"sqlite_path": "str", "query": "str"},
        "optional": {"parameters": "list"},
    },
    "store.named_query": {
        "stability": "stable",
        "authority": "read",
        "required": {"query_name": "str"},
        "optional": {"parameters": "any"},
    },
    "store.skill_state": {
        "stability": "stable",
        "authority": "persist",
        "required": {"operation": "str"},
        "optional": {"key": "str", "value": "any"},
    },
    "net.http_get_json": {
        "stability": "stable",
        "authority": "communicate",
        "required": {"url": "str"},
        "optional": {"headers": "mapping", "timeout_seconds": "float"},
    },
    "net.http_get_text": {
        "stability": "stable",
        "authority": "communicate",
        "required": {"url": "str"},
        "optional": {"headers": "mapping", "timeout_seconds": "float"},
    },
    "tool.invoke": {
        "stability": "stable",
        "authority": "execute",
        "required": {"tool_name": "str"},
        "optional": {"arguments": "mapping"},
    },
    "skill.invoke": {
        "stability": "stable",
        "authority": "invoke",
        "required": {"skill_title": "str"},
        "optional": {"semantic_unit": "str", "invocation_payload": "any", "max_steps": "int"},
    },
    "macos.open_browser": {
        "stability": "stable",
        "authority": "execute",
        "required": {"url": "str"},
        "optional": {"browser": "str"},
    },
    "macos.open_app": {
        "stability": "stable",
        "authority": "execute",
        "required": {"application": "str"},
        "optional": {},
    },
    "macos.open_file": {
        "stability": "stable",
        "authority": "execute",
        "required": {"path": "str"},
        "optional": {"application": "str"},
    },
    "macos.open_folder": {
        "stability": "stable",
        "authority": "execute",
        "required": {"folder": "str"},
        "optional": {},
    },
    "macos.open_location": {
        "stability": "stable",
        "authority": "execute",
        "required": {"target": "str"},
        "optional": {},
    },
    "macos.reveal_in_finder": {
        "stability": "stable",
        "authority": "execute",
        "required": {"path": "str"},
        "optional": {},
    },
    "macos.capture_screenshot": {
        "stability": "stable",
        "authority": "write",
        "required": {"path": "str"},
        "optional": {},
    },
    "macos.copy_to_clipboard": {
        "stability": "stable",
        "authority": "execute",
        "required": {"text": "str"},
        "optional": {},
    },
}


def host_abi_version() -> str:
    """
    High Level Purpose:
        In circumstances like stabilizing one host broker contract across Python-first execution now and future Wasm-backed execution later, helps with exposing the current ABI version string.

    Reference to Theory:
        Supports the bundle plan by turning broker mediation into a versioned host ABI rather than an implicit Python-only calling convention.

    Example Input Output:
        Input: `host_abi_version()`
        Output: 'bssc.host.v1'

    Args:
        None.

    Returns:
        str: Result produced by `host_abi_version`.
    """
    return HOST_ABI_VERSION


def wasm_skill_abi_version() -> str:
    """
    High Level Purpose:
        In circumstances like skill import/export and embedded Wasmtime execution, helps with exposing the minimal governed Wasm ABI version used by the current Python host.

    Reference to Theory:
        Supports the orderly move toward Wasm by making the first governed Wasm contract explicit before alternate inner runtimes are introduced.

    Example Input Output:
        Input: `wasm_skill_abi_version()`
        Output: 'bssc.wasm.v1'

    Args:
        None.

    Returns:
        str: Result produced by `wasm_skill_abi_version`.
    """
    return WASM_SKILL_ABI_VERSION


def wasm_skill_abi_spec() -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like validating governed Wasm skills before execution, helps with returning the minimal compute-only Wasm ABI contract enforced by the current host.

    Reference to Theory:
        Supports Wasm readiness by defining one explicit inner-runtime contract under the existing governed host ABI rather than relying on ambient WASI resources.

    Example Input Output:
        Input: `wasm_skill_abi_spec()`
        Output: {'version': 'bssc.wasm.v1', 'execution_model': 'embedded_wasmtime_compute_only', ...}

    Args:
        None.

    Returns:
        dict[str, Any]: Result produced by `wasm_skill_abi_spec`.
    """
    return {
        "version": WASM_SKILL_ABI["version"],
        "execution_model": WASM_SKILL_ABI["execution_model"],
        "ambient_capabilities": dict(WASM_SKILL_ABI["ambient_capabilities"]),
        "imports": {
            module_name: {
                import_name: {
                    "params": list(spec.get("params", [])),
                    "results": list(spec.get("results", [])),
                }
                for import_name, spec in dict(module_spec).items()
            }
            for module_name, module_spec in dict(WASM_SKILL_ABI["imports"]).items()
        },
        "exports": {
            export_name: dict(export_spec)
            for export_name, export_spec in dict(WASM_SKILL_ABI["exports"]).items()
        },
        "input_transport": WASM_SKILL_ABI["input_transport"],
        "output_transport": WASM_SKILL_ABI["output_transport"],
        "hostcall_transport": WASM_SKILL_ABI["hostcall_transport"],
        "host_broker_subset": list(WASM_SKILL_ABI["host_broker_subset"]),
    }


def known_wasm_host_broker_names() -> list[str]:
    """
    High Level Purpose:
        In circumstances like governed Wasm hostcall validation, helps with exposing the intentionally small stable broker subset that the first Wasm tier may call.

    Reference to Theory:
        Supports the orderly Wasm rollout by keeping the first inner-runtime host surface narrower than the full host broker ABI.

    Example Input Output:
        Input: `known_wasm_host_broker_names()`
        Output: ['fs.find_mount', 'fs.list_mount', 'fs.read_mount', 'fs.write_mount', 'skill.invoke', 'store.named_query', 'store.skill_state', 'tool.invoke']

    Args:
        None.

    Returns:
        list[str]: Result produced by `known_wasm_host_broker_names`.
    """
    return sorted(WASM_HOST_BROKER_NAMES)


def known_host_broker_names(*, stable_only: bool = False) -> list[str]:
    """
    High Level Purpose:
        In circumstances like exporting governed broker usage or validating future runtime adapters, helps with returning the declared broker names carried by the current host ABI.

    Reference to Theory:
        Supports Python-first now and Wasm-later by making the mediated effect surface enumerable and explicit.

    Example Input Output:
        Input: `known_host_broker_names(stable_only=True)`
        Output: ['fs.list_mount', 'fs.read_mount', 'fs.write_mount', ...]

    Args:
        stable_only: Value for `stable_only` used by `known_host_broker_names`. Expected type: `bool`. Defaults to `False`.

    Returns:
        list[str]: Result produced by `known_host_broker_names`.
    """
    names = []
    for name, spec in HOST_BROKER_ABI.items():
        if stable_only and collapse_ws(str(spec.get("stability", ""))) != "stable":
            continue
        names.append(name)
    return sorted(names)


def host_broker_abi_spec(name: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like validating mediated effect calls, helps with looking up one broker's ABI declaration by name.

    Reference to Theory:
        Supports a stable host ABI by giving execution layers one shared source of truth for broker arguments.

    Example Input Output:
        Input: `host_broker_abi_spec(name='fs.read_mount')`
        Output: {'stability': 'stable', 'required': {'mount': 'str'}, 'optional': {'relative_path': 'str'}}

    Args:
        name: Value for `name` used by `host_broker_abi_spec`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `host_broker_abi_spec`.
    """
    return dict(HOST_BROKER_ABI.get(collapse_ws(str(name)), {}))


def host_broker_stability(name: str) -> str:
    """
    High Level Purpose:
        In circumstances like admission policy that distinguishes stable host ABI brokers from transitional ones, helps with reading the declared stability class for one broker name.

    Reference to Theory:
        Supports Wasm-readiness by making the stable broker subset explicit before alternate inner runtimes depend on it.

    Example Input Output:
        Input: `host_broker_stability(name='fs.read_mount')`
        Output: 'stable'

    Args:
        name: Value for `name` used by `host_broker_stability`. Expected type: `str`.

    Returns:
        str: Result produced by `host_broker_stability`.
    """
    spec = host_broker_abi_spec(name)
    return collapse_ws(str(spec.get("stability", "")))


def required_authority_for_host_broker(name: str) -> str:
    """
    High Level Purpose:
        In circumstances like grant issuance, child broker checks, and future alternate runtimes, helps with exposing the declared authority required for one host ABI broker.

    Reference to Theory:
        Supports a stable host ABI by making authority semantics part of the broker contract rather than an implicit Python-only convention.

    Example Input Output:
        Input: `required_authority_for_host_broker(name='fs.write_mount')`
        Output: 'write'

    Args:
        name: Value for `name` used by `required_authority_for_host_broker`. Expected type: `str`.

    Returns:
        str: Result produced by `required_authority_for_host_broker`.
    """
    spec = host_broker_abi_spec(name)
    return collapse_ws(str(spec.get("authority", "")))


def _value_matches_declared_type(value: Any, declared_type: str) -> bool:
    type_name = collapse_ws(str(declared_type)).lower()
    if type_name not in _TYPE_LABELS:
        return False
    if value is None:
        return True
    if type_name == "any":
        return True
    if type_name == "str":
        return isinstance(value, str)
    if type_name == "bool":
        return isinstance(value, bool)
    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "float":
        return (isinstance(value, float) or isinstance(value, int)) and not isinstance(value, bool)
    if type_name == "mapping":
        return isinstance(value, Mapping)
    if type_name == "list":
        return isinstance(value, list)
    return False


def validate_host_broker_invocation(
    name: str,
    arguments: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str]:
    """
    High Level Purpose:
        In circumstances like mediated host-effect execution from either the parent controller or a child Python skill, helps with validating one broker request against the versioned host ABI.

    Reference to Theory:
        Supports Wasm-readiness by making broker names and typed payloads explicit now, before there is a second runtime implementation.

    Example Input Output:
        Input: `validate_host_broker_invocation(name='fs.read_mount', arguments={'mount': 'skill_input', 'relative_path': 'docs'})`
        Output: ({'mount': 'skill_input', 'relative_path': 'docs'}, '')

    Args:
        name: Value for `name` used by `validate_host_broker_invocation`. Expected type: `str`.
        arguments: Value for `arguments` used by `validate_host_broker_invocation`. Expected type: `Mapping[str, Any] | None`. Defaults to `None`.

    Returns:
        tuple[dict[str, Any] | None, str]: Result produced by `validate_host_broker_invocation`.
    """
    broker_name = collapse_ws(str(name))
    spec = host_broker_abi_spec(broker_name)
    if not spec:
        return None, f"No host ABI broker is declared for {broker_name}."
    raw_arguments = dict(arguments) if isinstance(arguments, Mapping) else {}
    required = dict(spec.get("required", {})) if isinstance(spec.get("required", {}), Mapping) else {}
    optional = dict(spec.get("optional", {})) if isinstance(spec.get("optional", {}), Mapping) else {}
    allowed_keys = set(required) | set(optional)
    missing = [key for key in required if key not in raw_arguments]
    if missing:
        return None, f"Host ABI broker {broker_name} requires arguments: {', '.join(sorted(missing))}."
    extras = [key for key in raw_arguments if key not in allowed_keys]
    if extras:
        return None, f"Host ABI broker {broker_name} does not declare arguments: {', '.join(sorted(extras))}."
    for key, declared_type in {**required, **optional}.items():
        if key not in raw_arguments:
            continue
        if not _value_matches_declared_type(raw_arguments.get(key), str(declared_type)):
            return (
                None,
                f"Host ABI broker {broker_name} expects {key} to be {declared_type}.",
            )
    return raw_arguments, ""
