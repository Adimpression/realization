# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from realized_core_semantics.applied_model import CrossBoundaryResult
from realized_core_runtime.host_abi import (
    host_abi_version,
    known_wasm_host_broker_names,
    required_authority_for_host_broker,
    validate_host_broker_invocation,
    wasm_skill_abi_spec,
    wasm_skill_abi_version,
)
from realized_host_interaction.realizers import (
    HostBrokerInvocation,
    HostRealizerProvider,
)
from realized_core_semantics.semantic_text import collapse_ws


def _func_signature_text(func_type: Any) -> tuple[list[str], list[str]]:
    params = [str(item) for item in getattr(func_type, "params", [])]
    results = [str(item) for item in getattr(func_type, "results", [])]
    return params, results


def _validate_wasm_skill_abi(module: Any) -> list[str]:
    spec = wasm_skill_abi_spec()
    allowed_imports = {
        (module_name, import_name): import_spec
        for module_name, module_items in dict(spec.get("imports", {})).items()
        for import_name, import_spec in dict(module_items).items()
    }
    errors: list[str] = []
    for import_item in getattr(module, "imports", []):
        import_key = (str(import_item.module), str(import_item.name))
        expected = allowed_imports.get(import_key)
        if expected is None:
            errors.append(
                f"Unsupported Wasm import {import_item.module}.{import_item.name}; "
                f"only the governed {wasm_skill_abi_version()} imports are allowed."
            )
            continue
        params, results = _func_signature_text(import_item.type)
        if params != list(expected.get("params", [])) or results != list(expected.get("results", [])):
            errors.append(
                f"Wasm import {import_item.module}.{import_item.name} does not match the expected signature "
                f"{expected.get('params', [])} -> {expected.get('results', [])}."
            )
    exports = {str(item.name): item.type for item in getattr(module, "exports", [])}
    if "memory" not in exports:
        errors.append("Wasm skill ABI requires an exported memory named `memory`.")
    if "run" not in exports:
        errors.append("Wasm skill ABI requires an exported function named `run`.")
    else:
        params, results = _func_signature_text(exports["run"])
        if params != [] or results != ["i32"]:
            errors.append("Wasm export `run` must have signature [] -> [i32].")
    return errors


def _mapping_context(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return dict(value)


def _approval_class(value: Any, *, default: str = "automatic") -> str:
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in {"automatic", "operator_approved", "admin_approved", "manual_review"}:
        return normalized
    return default


def _wasm_host_trace(
    *,
    context: Mapping[str, Any],
    broker_name: str,
    required_authority: str,
    grant_ids: list[str],
    allowed: bool,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    admission = dict(context.get("admission", {})) if isinstance(context.get("admission", {}), Mapping) else {}
    return {
        "kind": "wasm_skill_broker",
        "artifact_id": collapse_ws(str(context.get("artifact_id", ""))),
        "artifact_title": collapse_ws(str(context.get("artifact_title", ""))),
        "semantic_unit": collapse_ws(str(context.get("semantic_unit", ""))),
        "effect_kind": collapse_ws(str(broker_name)),
        "required_authority": collapse_ws(str(required_authority)),
        "grant_ids": list(grant_ids),
        "allowed": bool(allowed),
        "approval_class": _approval_class(admission.get("required_approval_class", "automatic")),
        "host_abi_version": host_abi_version(),
        "wasm_abi_version": wasm_skill_abi_version(),
        "result": dict(result),
    }


def execute_wasm_cross_boundary(
    wasm_module_text: str,
    stdin_payload: Any,
    *,
    timeout_seconds: float | None = None,
    host_runtime_context: Mapping[str, Any] | None = None,
    realizer_provider: HostRealizerProvider | None = None,
) -> CrossBoundaryResult:
    module_text = str(wasm_module_text or "").strip()
    if not module_text:
        return CrossBoundaryResult(
            ok=False,
            command=[],
            exit_code=1,
            stdout="",
            stderr="cross_boundary received an empty wasm module body.",
            notes=["No executable Wasm module text was supplied."],
        )

    try:
        import wasmtime
    except Exception as exc:
        return CrossBoundaryResult(
            ok=False,
            command=["wasmtime:embedded"],
            exit_code=127,
            stdout="",
            stderr=f"wasmtime is not available in the Python environment: {exc}",
            notes=["The requested Wasm executor is not installed."],
        )

    try:
        engine = wasmtime.Engine()
        module = wasmtime.Module(engine, module_text)
    except Exception as exc:
        return CrossBoundaryResult(
            ok=False,
            command=["wasmtime:embedded"],
            exit_code=1,
            stdout="",
            stderr=str(exc),
            notes=["The Wasm module could not be compiled by Wasmtime."],
            metadata={"wasm_abi_version": wasm_skill_abi_version()},
        )

    validation_errors = _validate_wasm_skill_abi(module)
    if validation_errors:
        return CrossBoundaryResult(
            ok=False,
            command=["wasmtime:embedded"],
            exit_code=1,
            stdout="",
            stderr="\n".join(validation_errors),
            notes=["The Wasm module did not satisfy the governed compute-only Wasm ABI."],
            metadata={"wasm_abi_version": wasm_skill_abi_version()},
        )

    input_bytes = json.dumps(stdin_payload, sort_keys=True).encode("utf-8")
    output_buffer = bytearray()
    hostcall_response_buffer = bytearray()
    host_traces: list[dict[str, Any]] = []
    nested_effect_traces: list[dict[str, Any]] = []
    nested_capability_grants: list[dict[str, Any]] = []
    context = _mapping_context(host_runtime_context)
    grants = [dict(item) for item in context.get("grants", []) if isinstance(item, Mapping)]
    admission = dict(context.get("admission", {})) if isinstance(context.get("admission", {}), Mapping) else {}
    admitted = bool(admission.get("admitted", True))
    allowed_wasm_brokers = set(known_wasm_host_broker_names())
    raw_declared_host_brokers = context.get("declared_host_brokers", [])
    declared_host_brokers = {
        collapse_ws(str(item))
        for item in raw_declared_host_brokers
        if collapse_ws(str(item))
    } if isinstance(raw_declared_host_brokers, Sequence) and not isinstance(
        raw_declared_host_brokers,
        (str, bytes, bytearray),
    ) else set()
    strict_realizer_declaration = bool(context.get("strict_realizer_declaration"))

    try:
        store = wasmtime.Store(engine)
        linker = wasmtime.Linker(engine)

        def input_len() -> int:
            return len(input_bytes)

        def read_input(caller: Any, ptr: int) -> int:
            memory = caller.get("memory")
            if memory is None:
                return -1
            memory.write(caller, input_bytes, int(ptr))
            return len(input_bytes)

        def write_output(caller: Any, ptr: int, length: int) -> int:
            memory = caller.get("memory")
            if memory is None:
                return -1
            data = memory.read(caller, int(ptr), int(ptr) + int(length))
            output_buffer.clear()
            output_buffer.extend(bytes(data))
            return int(length)

        def hostcall(caller: Any, ptr: int, length: int) -> int:
            from realized_core_runtime.host_brokers import invoke_host_broker

            memory = caller.get("memory")
            if memory is None:
                return -1
            raw_request = bytes(memory.read(caller, int(ptr), int(ptr) + int(length)))
            error_result: dict[str, Any]
            try:
                parsed_request = json.loads(raw_request.decode("utf-8"))
            except Exception as exc:
                error_result = {
                    "status": "error",
                    "broker": "",
                    "error": f"Invalid Wasm hostcall request JSON: {exc}",
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name="",
                        required_authority="",
                        grant_ids=[],
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            if not isinstance(parsed_request, Mapping):
                error_result = {
                    "status": "error",
                    "broker": "",
                    "error": "Wasm hostcall request must be a JSON object.",
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name="",
                        required_authority="",
                        grant_ids=[],
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            broker_name = collapse_ws(
                str(
                    parsed_request.get("broker_name", "")
                    or parsed_request.get("broker", "")
                    or parsed_request.get("name", "")
                )
            )
            raw_arguments = parsed_request.get("arguments", {})
            required_authority = required_authority_for_host_broker(broker_name)
            grant_ids = [
                collapse_ws(str(item.get("id", "")))
                for item in grants
                if collapse_ws(str(item.get("authority", ""))) == required_authority
                and collapse_ws(str(item.get("id", "")))
            ]
            if strict_realizer_declaration and broker_name not in declared_host_brokers:
                error_result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": f"Skill declaration does not bind the exact host broker {broker_name!r}.",
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name=broker_name,
                        required_authority=required_authority,
                        grant_ids=grant_ids,
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            if broker_name not in allowed_wasm_brokers:
                error_result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": (
                        f"Wasm hostcalls may only use the governed broker subset: "
                        f"{', '.join(sorted(allowed_wasm_brokers))}."
                    ),
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name=broker_name,
                        required_authority=required_authority,
                        grant_ids=grant_ids,
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            normalized_arguments, abi_error = validate_host_broker_invocation(
                broker_name,
                raw_arguments if isinstance(raw_arguments, Mapping) else {},
            )
            if normalized_arguments is None:
                error_result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": abi_error,
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name=broker_name,
                        required_authority=required_authority,
                        grant_ids=grant_ids,
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            if not admitted:
                error_result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": collapse_ws(str(admission.get("rationale", "")))
                    or "Governed Wasm skill is not admitted for broker use.",
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name=broker_name,
                        required_authority=required_authority,
                        grant_ids=grant_ids,
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            if required_authority and not grant_ids:
                error_result = {
                    "status": "error",
                    "broker": broker_name,
                    "error": f"Runtime grants do not cover required authority {required_authority} for {broker_name}.",
                }
                hostcall_response_buffer.clear()
                hostcall_response_buffer.extend(json.dumps(error_result, sort_keys=True).encode("utf-8"))
                host_traces.append(
                    _wasm_host_trace(
                        context=context,
                        broker_name=broker_name,
                        required_authority=required_authority,
                        grant_ids=grant_ids,
                        allowed=False,
                        result=error_result,
                    )
                )
                return len(hostcall_response_buffer)
            if realizer_provider is not None:
                broker_result = realizer_provider.invoke_broker(
                    HostBrokerInvocation(
                        identity=broker_name,
                        arguments=normalized_arguments,
                        governance_context=context,
                    )
                )
            else:
                broker_result = invoke_host_broker(
                    broker_name,
                    arguments=normalized_arguments,
                    governance_context=context,
                )
            if isinstance(broker_result, Mapping):
                nested_effect_traces.extend(
                    dict(item)
                    for item in broker_result.get("nested_effect_traces", [])
                    if isinstance(item, Mapping)
                )
                nested_capability_grants.extend(
                    dict(item)
                    for item in broker_result.get("nested_capability_grants", [])
                    if isinstance(item, Mapping)
                )
            hostcall_response_buffer.clear()
            hostcall_response_buffer.extend(json.dumps(broker_result, sort_keys=True).encode("utf-8"))
            host_traces.append(
                _wasm_host_trace(
                    context=context,
                    broker_name=broker_name,
                    required_authority=required_authority,
                    grant_ids=grant_ids,
                    allowed=True,
                    result=broker_result,
                )
            )
            return len(hostcall_response_buffer)

        def read_hostcall_response(caller: Any, ptr: int) -> int:
            memory = caller.get("memory")
            if memory is None:
                return -1
            memory.write(caller, bytes(hostcall_response_buffer), int(ptr))
            return len(hostcall_response_buffer)

        linker.define(
            store,
            "bssc",
            "input_len",
            wasmtime.Func(
                store,
                wasmtime.FuncType([], [wasmtime.ValType.i32()]),
                lambda: input_len(),
            ),
        )
        linker.define(
            store,
            "bssc",
            "read_input",
            wasmtime.Func(
                store,
                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                read_input,
                access_caller=True,
            ),
        )
        linker.define(
            store,
            "bssc",
            "write_output",
            wasmtime.Func(
                store,
                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                write_output,
                access_caller=True,
            ),
        )
        linker.define(
            store,
            "bssc",
            "hostcall",
            wasmtime.Func(
                store,
                wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                hostcall,
                access_caller=True,
            ),
        )
        linker.define(
            store,
            "bssc",
            "read_hostcall_response",
            wasmtime.Func(
                store,
                wasmtime.FuncType([wasmtime.ValType.i32()], [wasmtime.ValType.i32()]),
                read_hostcall_response,
                access_caller=True,
            ),
        )
        instance = linker.instantiate(store, module)
        run = instance.exports(store)["run"]
        exit_code = int(run(store))
    except Exception as exc:
        return CrossBoundaryResult(
            ok=False,
            command=["wasmtime:embedded", "run"],
            exit_code=1,
            stdout="",
            stderr=str(exc),
            notes=["Embedded Wasmtime execution failed before completion."],
            metadata={"wasm_abi_version": wasm_skill_abi_version()},
        )

    stdout = output_buffer.decode("utf-8").strip()
    parsed_output: Any = None
    result_value: Any = None
    answer_text = ""
    notes: list[str] = []
    if stdout:
        try:
            parsed_output = json.loads(stdout)
        except Exception:
            parsed_output = None
    if isinstance(parsed_output, Mapping):
        parsed_output = dict(parsed_output)
        result_value = parsed_output.get("result")
        if result_value is None:
            result_value = dict(parsed_output)
        answer_text = str(parsed_output.get("answer", "")).strip()
        parsed_notes = parsed_output.get("notes", [])
        if isinstance(parsed_notes, list):
            notes = [str(item).strip() for item in parsed_notes if str(item).strip()]
        if host_traces:
            parsed_output["_bssc_host_traces"] = list(host_traces)
    if timeout_seconds is not None:
        notes = list(notes) + ["Embedded Wasmtime execution does not yet enforce timeout preemption."]

    return CrossBoundaryResult(
        ok=exit_code == 0,
        command=["wasmtime:embedded", "run"],
        exit_code=exit_code,
        stdout=stdout,
        stderr="",
        parsed_output=parsed_output,
        result=result_value,
        answer=answer_text,
        notes=notes,
        metadata={
            "wasm_abi_version": wasm_skill_abi_version(),
            "host_runtime_context_used": bool(host_runtime_context),
            "host_traces": list(host_traces),
            "nested_effect_traces": list(nested_effect_traces),
            "nested_capability_grants": list(nested_capability_grants),
        },
    )
