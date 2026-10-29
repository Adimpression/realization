# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import Any

from realized_core_runtime.host_abi import (
    host_abi_version,
    required_authority_for_host_broker,
    validate_host_broker_invocation,
)
from realized_core_runtime.python_transport import (
    PYTHON_SKILL_HOST_ENDPOINT_ENV,
    PYTHON_SKILL_HOST_PROVIDER_REQUIRED_ENV,
    PYTHON_SKILL_HOST_TOKEN_ENV,
    request_parent_host_broker,
)
from realized_core_governance.vocabulary import normalize_skill_approval_class
from realized_core_semantics.semantic_text import collapse_ws

_HOST_CONTEXT_ENV = "BSSC_PYTHON_SKILL_HOST_CONTEXT"
_HOST_TRACE_PATH_ENV = "BSSC_PYTHON_SKILL_HOST_TRACE_PATH"


class HostBrokerError(RuntimeError):
    """
    High Level Purpose:
        In circumstances like Python skills using the governed host broker API, helps with signaling that a requested brokered effect was denied before or during host dispatch.

    Reference to Theory:
        Supports Python-first host mediation by giving skills one explicit error surface for denied broker operations.

    Example Input Output:
        Input: `HostBrokerError('Runtime grants do not cover write authority.')`
        Output: HostBrokerError('Runtime grants do not cover write authority.')

    Args:
        None.

    Returns:
        None: Exception type used for governed broker failures.
    """


def _runtime_context() -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like Python skills calling named host brokers, helps with loading the parent-provided runtime mediation context from the child process environment.

    Reference to Theory:
        Supports broker-aware skills by carrying grants, declaration, and admission state into the Python child runtime.

    Example Input Output:
        Input: `_runtime_context()`
        Output: {'artifact_id': 'artifact-brokered-file-write', 'grants': [{'authority': 'write'}]}

    Args:
        None.

    Returns:
        dict[str, Any]: Result produced by `_runtime_context`.
    """
    raw = os.getenv(_HOST_CONTEXT_ENV, "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _append_trace(record: Mapping[str, Any]) -> None:
    """
    High Level Purpose:
        In circumstances like child-side host broker calls inside Python skills, helps with appending one JSON trace record to the parent-provided trace sink on a best-effort basis.

    Reference to Theory:
        Supports constitutional trace continuity across the Python process boundary without turning trace-sink filesystem failures into user-visible execution failures.

    Example Input Output:
        Input: `_append_trace(record={'effect_kind': 'fs.write_text', 'allowed': True})`
        Output: None

    Args:
        record: Value for `record` used by `_append_trace`. Expected type: `Mapping[str, Any]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    trace_path = os.getenv(_HOST_TRACE_PATH_ENV, "").strip()
    if not trace_path:
        return
    try:
        with open(trace_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(dict(record), sort_keys=True))
            handle.write("\n")
    except OSError:
        return


def broker_request(name: str, /, **arguments: Any) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like Python skills that need filesystem, store, network, or macOS effects, helps with routing those effects through the governed broker API instead of raw host access.

    Reference to Theory:
        Supports the next bundle step by giving Python skills a named broker surface that uses declaration-derived grants at runtime.

    Example Input Output:
        Input: `broker_request('fs.write_text', path='/tmp/demo.txt', text='hello')`
        Output: {'status': 'ok', 'path': '/tmp/demo.txt', 'bytes_written': 5, 'append': False}

    Args:
        name: Value for `name` used by `broker_request`. Expected type: `str`.
        arguments: Arbitrary keyword arguments passed to the named broker.

    Returns:
        dict[str, Any]: Result produced by `broker_request`.
    """
    broker_name = collapse_ws(str(name))
    context = _runtime_context()
    grants = [dict(item) for item in context.get("grants", []) if isinstance(item, Mapping)]
    admission = dict(context.get("admission", {})) if isinstance(context.get("admission", {}), Mapping) else {}
    artifact_id = collapse_ws(str(context.get("artifact_id", "")))
    artifact_title = collapse_ws(str(context.get("artifact_title", "")))
    semantic_unit = collapse_ws(str(context.get("semantic_unit", "")))
    declared_host_abi_version = collapse_ws(str(context.get("host_abi_version", "")))
    current_host_abi_version = host_abi_version()
    required_authority = required_authority_for_host_broker(broker_name)
    grant_ids = [
        collapse_ws(str(item.get("id", "")))
        for item in grants
        if collapse_ws(str(item.get("authority", ""))) == required_authority and collapse_ws(str(item.get("id", "")))
    ]
    admission_status = collapse_ws(str(admission.get("status", "admitted"))).lower()
    admitted = bool(admission.get("admitted", admission_status in {"admitted", "legacy_implicit_admit"}))
    approval_class = normalize_skill_approval_class(admission.get("required_approval_class", "automatic"))
    if declared_host_abi_version and declared_host_abi_version != current_host_abi_version:
        rationale = (
            f"Python skill host ABI mismatch: parent declared {declared_host_abi_version}, "
            f"child runtime implements {current_host_abi_version}."
        )
        _append_trace(
            {
                "kind": "python_skill_broker",
                "artifact_id": artifact_id,
                "artifact_title": artifact_title,
                "semantic_unit": semantic_unit,
                "effect_kind": broker_name,
                "required_authority": required_authority,
                "grant_ids": grant_ids,
                "allowed": False,
                "approval_class": approval_class,
                "host_abi_version": current_host_abi_version,
                "result": {"status": "error", "error": rationale},
            }
        )
        raise HostBrokerError(rationale)
    normalized_arguments, abi_error = validate_host_broker_invocation(broker_name, arguments)
    if normalized_arguments is None:
        _append_trace(
            {
                "kind": "python_skill_broker",
                "artifact_id": artifact_id,
                "artifact_title": artifact_title,
                "semantic_unit": semantic_unit,
                "effect_kind": broker_name,
                "required_authority": required_authority,
                "grant_ids": grant_ids,
                "allowed": False,
                "approval_class": approval_class,
                "host_abi_version": current_host_abi_version,
                "result": {"status": "error", "error": abi_error},
            }
        )
        raise HostBrokerError(abi_error)
    raw_declared_brokers = context.get("declared_host_brokers", [])
    declared_brokers = {
        collapse_ws(str(item))
        for item in raw_declared_brokers
        if collapse_ws(str(item))
    } if isinstance(raw_declared_brokers, Sequence) and not isinstance(
        raw_declared_brokers,
        (str, bytes, bytearray),
    ) else set()
    if bool(context.get("strict_realizer_declaration")) and broker_name not in declared_brokers:
        rationale = f"Skill declaration does not bind the exact host broker {broker_name!r}."
        _append_trace(
            {
                "kind": "python_skill_broker",
                "artifact_id": artifact_id,
                "artifact_title": artifact_title,
                "semantic_unit": semantic_unit,
                "effect_kind": broker_name,
                "required_authority": required_authority,
                "grant_ids": grant_ids,
                "allowed": False,
                "approval_class": approval_class,
                "host_abi_version": current_host_abi_version,
                "result": {"status": "error", "error": rationale},
            }
        )
        raise HostBrokerError(rationale)
    if not admitted:
        rationale = collapse_ws(str(admission.get("rationale", ""))) or "Governed skill is not admitted for broker use."
        _append_trace(
            {
                "kind": "python_skill_broker",
                "artifact_id": artifact_id,
                "artifact_title": artifact_title,
                "semantic_unit": semantic_unit,
                "effect_kind": broker_name,
                "required_authority": required_authority,
                "grant_ids": grant_ids,
                "allowed": False,
                "approval_class": approval_class,
                "host_abi_version": current_host_abi_version,
                "result": {"status": "error", "error": rationale},
            }
        )
        raise HostBrokerError(rationale)
    if required_authority and not grant_ids:
        rationale = f"Runtime grants do not cover required authority {required_authority} for {broker_name}."
        _append_trace(
            {
                "kind": "python_skill_broker",
                "artifact_id": artifact_id,
                "artifact_title": artifact_title,
                "semantic_unit": semantic_unit,
                "effect_kind": broker_name,
                "required_authority": required_authority,
                "grant_ids": grant_ids,
                "allowed": False,
                "approval_class": approval_class,
                "host_abi_version": current_host_abi_version,
                "result": {"status": "error", "error": rationale},
            }
        )
        raise HostBrokerError(rationale)
    provider_required = os.getenv(PYTHON_SKILL_HOST_PROVIDER_REQUIRED_ENV, "").strip() == "1"
    if provider_required:
        endpoint = os.getenv(PYTHON_SKILL_HOST_ENDPOINT_ENV, "").strip()
        token = os.getenv(PYTHON_SKILL_HOST_TOKEN_ENV, "").strip()
        if not endpoint or not token:
            rationale = "The parent required an injected host provider but did not expose its invocation bridge."
            _append_trace(
                {
                    "kind": "python_skill_broker",
                    "artifact_id": artifact_id,
                    "artifact_title": artifact_title,
                    "semantic_unit": semantic_unit,
                    "effect_kind": broker_name,
                    "required_authority": required_authority,
                    "grant_ids": grant_ids,
                    "allowed": False,
                    "approval_class": approval_class,
                    "host_abi_version": current_host_abi_version,
                    "result": {"status": "error", "error": rationale},
                }
            )
            raise HostBrokerError(rationale)
        result = request_parent_host_broker(
            endpoint=endpoint,
            token=token,
            broker_name=broker_name,
            arguments=normalized_arguments,
        )
    else:
        from realized_core_runtime.host_brokers import invoke_host_broker

        result = invoke_host_broker(
            broker_name,
            arguments=normalized_arguments,
            governance_context=context,
        )
    _append_trace(
        {
            "kind": "python_skill_broker",
            "artifact_id": artifact_id,
            "artifact_title": artifact_title,
            "semantic_unit": semantic_unit,
            "effect_kind": broker_name,
            "required_authority": required_authority,
            "grant_ids": grant_ids,
            "allowed": True,
            "approval_class": approval_class,
            "host_abi_version": current_host_abi_version,
            "result": result,
        }
    )
    return result
