# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applied_theory_primitives import json_safe


def _host_interaction_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collapse_host_interaction_text(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like shaping shared host-interaction receipts, helps with normalizing one optional text-like field into a comparable stripped string.

    Reference to Theory:
        Supports the shared receipt substrate by keeping attachment and delegation metadata stable even when upstream callers supply mixed text-like values.

    Example Input Output:
        Input: `_collapse_host_interaction_text(' main ')`
        Output: 'main'

    Args:
        value: Value for `value` used by `_collapse_host_interaction_text`. Expected type: `Any`.

    Returns:
        str: Result produced by `_collapse_host_interaction_text`.
    """
    return str(value or "").strip()


def _host_interaction_capability_target(
    *,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> str:
    """
    High Level Purpose:
        In circumstances like shared capability-call receipt emission, helps with projecting one stable attachment target even when the target is supplied only in either the arguments or the result payload.

    Reference to Theory:
        Supports the workstation receipt contract by keeping the capability target explicit instead of burying it inside capability-specific payloads.

    Example Input Output:
        Input: `_host_interaction_capability_target(arguments={'target': 'main'}, result={})`
        Output: 'main'

    Args:
        arguments: Value for `arguments` used by `_host_interaction_capability_target`. Expected type: `dict[str, Any]`.
        result: Value for `result` used by `_host_interaction_capability_target`. Expected type: `dict[str, Any]`.

    Returns:
        str: Result produced by `_host_interaction_capability_target`.
    """
    for mapping in (result, arguments):
        target = _collapse_host_interaction_text(mapping.get("target", ""))
        if target:
            return target
    return ""


def _host_interaction_capability_delegation_receipt(
    *,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation-to-skill invocation receipts, helps with projecting requested, approved, escalated, granted, missing, and unsupported delegated rights into one stable top-level receipt field.

    Reference to Theory:
        Supports the workstation delegation model by making receipt consumers able to explain what authority was requested, granted, or still missing without reverse-engineering capability-specific result blobs.

    Example Input Output:
        Input: `_host_interaction_capability_delegation_receipt(arguments={'requested_delegation': [{'capability': 'ws.fs.read', 'target': 'main'}]}, result={'status': 'ok', 'granted_delegation': [{'capability': 'ws.fs.read', 'target': 'main'}]})`
        Output: {'status': 'ok', 'requested': [{'capability': 'ws.fs.read', 'target': 'main'}], 'granted': [{'capability': 'ws.fs.read', 'target': 'main'}]}

    Args:
        arguments: Value for `arguments` used by `_host_interaction_capability_delegation_receipt`. Expected type: `dict[str, Any]`.
        result: Value for `result` used by `_host_interaction_capability_delegation_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any] | None: Result produced by `_host_interaction_capability_delegation_receipt`.
    """
    projected: dict[str, Any] = {}
    saw_delegation_field = False

    def _project_list_field(*, output_key: str, argument_key: str, result_key: str) -> None:
        nonlocal saw_delegation_field
        if result_key in result:
            saw_delegation_field = True
            raw_value = result.get(result_key)
        elif argument_key in arguments:
            saw_delegation_field = True
            raw_value = arguments.get(argument_key)
        else:
            return
        if isinstance(raw_value, (list, tuple)):
            projected[output_key] = json_safe(list(raw_value))
            return
        projected[output_key] = []

    _project_list_field(
        output_key="requested",
        argument_key="requested_delegation",
        result_key="requested_delegation",
    )
    _project_list_field(
        output_key="approved",
        argument_key="approved_delegation",
        result_key="approved_delegation",
    )
    _project_list_field(
        output_key="escalated",
        argument_key="escalated_delegation",
        result_key="escalated_delegation",
    )
    _project_list_field(
        output_key="granted",
        argument_key="granted_delegation",
        result_key="granted_delegation",
    )
    _project_list_field(
        output_key="missing",
        argument_key="missing_delegation",
        result_key="missing_delegation",
    )
    _project_list_field(
        output_key="unsupported",
        argument_key="unsupported_delegation",
        result_key="unsupported_delegation",
    )

    scope = _collapse_host_interaction_text(
        result.get("approved_delegation_scope", arguments.get("approved_delegation_scope", ""))
    )
    if scope:
        saw_delegation_field = True
        projected["scope"] = scope

    status = _collapse_host_interaction_text(result.get("status", ""))
    if status and saw_delegation_field:
        projected["status"] = status

    return projected or None


def _host_interaction_capability_invocation_receipt(
    *,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation receipts, helps with projecting the canonical invocation contract into one stable top-level receipt field.

    Reference to Theory:
        Supports skill contract cleanup by exposing invocation request/result contracts at the receipt boundary instead of forcing consumers to inspect capability-specific payload shapes.

    Example Input Output:
        Input: `_host_interaction_capability_invocation_receipt(arguments={}, result={'invocation_request': {'skill_title': 'Demo'}, 'invocation_result': {'status': 'ok'}})`
        Output: {'request': {'skill_title': 'Demo'}, 'result': {'status': 'ok'}}

    Args:
        arguments: Value for `arguments` used by `_host_interaction_capability_invocation_receipt`. Expected type: `dict[str, Any]`.
        result: Value for `result` used by `_host_interaction_capability_invocation_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any] | None: Result produced by `_host_interaction_capability_invocation_receipt`.
    """
    request_payload = result.get("invocation_request", arguments.get("invocation_request"))
    result_payload = result.get("invocation_result", arguments.get("invocation_result"))
    if not isinstance(request_payload, Mapping) and not isinstance(result_payload, Mapping):
        return None
    projected: dict[str, Any] = {}
    if isinstance(request_payload, Mapping):
        projected["request"] = json_safe(dict(request_payload))
    if isinstance(result_payload, Mapping):
        projected["result"] = json_safe(dict(result_payload))
    return projected or None


def _host_interaction_composition_step_receipts(steps: Any) -> list[dict[str, Any]]:
    projected_steps: list[dict[str, Any]] = []
    if not isinstance(steps, list):
        return projected_steps
    for raw_step in steps:
        if not isinstance(raw_step, Mapping):
            continue
        step: dict[str, Any] = {}
        for key in ("step_id", "title", "status", "iteration", "branch_label", "skipped_reason"):
            value = raw_step.get(key)
            if value in ("", None, [], {}):
                continue
            step[key] = json_safe(value)
        if isinstance(raw_step.get("binding_receipts"), list):
            step["binding_receipts"] = json_safe(list(raw_step.get("binding_receipts", [])))
        if isinstance(raw_step.get("condition_receipts"), list):
            step["condition_receipts"] = json_safe(list(raw_step.get("condition_receipts", [])))
        if step:
            projected_steps.append(step)
    return projected_steps


def _host_interaction_capability_composition_receipt(
    *,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation skill composition and workflow execution receipts, helps with projecting one stable lineage summary for requested skills, final output selection, and leaf-binding receipts.

    Reference to Theory:
        Supports skill contract cleanup by making composition lineage explicit at the receipt boundary instead of leaving binding and condition receipts buried inside result blobs.

    Example Input Output:
        Input: `_host_interaction_capability_composition_receipt(arguments={'workflow_id': 'wf-1'}, result={'requested_skill_titles': ['Emit'], 'steps': [{'step_id': 'emit'}]})`
        Output: {'workflow_id': 'wf-1', 'requested_skill_titles': ['Emit'], 'steps': [{'step_id': 'emit'}]}

    Args:
        arguments: Value for `arguments` used by `_host_interaction_capability_composition_receipt`. Expected type: `dict[str, Any]`.
        result: Value for `result` used by `_host_interaction_capability_composition_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any] | None: Result produced by `_host_interaction_capability_composition_receipt`.
    """
    projected: dict[str, Any] = {}
    workflow_id = _collapse_host_interaction_text(result.get("workflow_id", arguments.get("workflow_id", "")))
    if workflow_id:
        projected["workflow_id"] = workflow_id
    requested_skill_titles = result.get("requested_skill_titles", arguments.get("requested_skill_titles"))
    if isinstance(requested_skill_titles, list):
        projected["requested_skill_titles"] = json_safe(list(requested_skill_titles))
    final_output_step = _collapse_host_interaction_text(
        result.get("final_output_step", arguments.get("final_output_step", ""))
    )
    if final_output_step:
        projected["final_output_step"] = final_output_step
    plan_authorities = result.get("plan_authorities")
    if isinstance(plan_authorities, list):
        projected["plan_authorities"] = json_safe(list(plan_authorities))
    steps = _host_interaction_composition_step_receipts(result.get("steps"))
    if steps:
        projected["steps"] = steps
    return projected or None


def host_interaction_receipts_path(root: Path) -> Path:
    """
    High Level Purpose:
        In circumstances like shared host-interaction event logging, helps with resolving the canonical append-only receipt log path beneath one host-backed session root.

    Reference to Theory:
        Supports the shared host-interaction substrate by giving different backends one stable event-log location contract instead of duplicating file-path rules inside each shell.

    Example Input Output:
        Input: `host_interaction_receipts_path(Path('/tmp/ws'))`
        Output: Path('/tmp/ws/receipts/events.jsonl')

    Args:
        root: Value for `root` used by `host_interaction_receipts_path`. Expected type: `Path`.

    Returns:
        Path: Result produced by `host_interaction_receipts_path`.
    """
    return Path(root).expanduser().resolve() / "receipts" / "events.jsonl"


def append_host_interaction_receipt(root: Path, payload: dict[str, Any]) -> None:
    """
    High Level Purpose:
        In circumstances like shared host-interaction event logging, helps with appending one JSONL receipt event into the canonical host-backed receipt log.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping receipt emission append-only and consistent across different host-backed shells and tools.

    Example Input Output:
        Input: `append_host_interaction_receipt(Path('/tmp/ws'), {'kind': 'user_prompt'})`
        Output: None

    Args:
        root: Value for `root` used by `append_host_interaction_receipt`. Expected type: `Path`.
        payload: Value for `payload` used by `append_host_interaction_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    path = host_interaction_receipts_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_legacy_host_interaction_receipt_log(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(json_safe(payload), sort_keys=True) + "\n")


def _normalize_legacy_host_interaction_receipt_log(path: Path) -> None:
    """
    High Level Purpose:
        In circumstances like ongoing workstation use across older receipt formats, helps with rewriting legacy concatenated JSON receipt streams into true line-delimited JSON before the next append occurs.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping receipt logs append-only and parseable even when earlier workstation runs used an older multi-line JSON object stream.

    Example Input Output:
        Input: `_normalize_legacy_host_interaction_receipt_log(Path('/tmp/ws/receipts/events.jsonl'))`
        Output: None

    Args:
        path: Value for `path` used by `path`. Expected type: `Path`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    if not path.exists():
        return
    text = path.read_text()
    if not text.strip():
        return
    stripped_lines = [line for line in text.splitlines() if line.strip()]
    try:
        for line in stripped_lines:
            json.loads(line)
        return
    except Exception:
        pass
    decoder = json.JSONDecoder()
    index = 0
    payloads: list[Any] = []
    try:
        while index < len(text):
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text):
                break
            payload, end = decoder.raw_decode(text, index)
            payloads.append(payload)
            index = end
    except Exception:
        return
    if not payloads:
        return
    path.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in payloads))


def host_interaction_user_prompt_receipt(
    *,
    prompt: str,
    task_contract: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed prompt sessions, helps with shaping one stable receipt event for the incoming user prompt and its normalized task contract.

    Reference to Theory:
        Supports the shared host-interaction substrate by making prompt ingress explicit and replayable independently of any particular shell implementation.

    Example Input Output:
        Input: `host_interaction_user_prompt_receipt(prompt='Inspect the project.', task_contract={'semantic_unit': 'Inspect the project.'})`
        Output: {'kind': 'user_prompt', 'timestamp': '2026-04-04T00:00:00+00:00', 'prompt': 'Inspect the project.', 'task_contract': {'semantic_unit': 'Inspect the project.'}}

    Args:
        prompt: Value for `prompt` used by `host_interaction_user_prompt_receipt`. Expected type: `str`.
        task_contract: Value for `task_contract` used by `host_interaction_user_prompt_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_user_prompt_receipt`.
    """
    return {
        "kind": "user_prompt",
        "timestamp": _host_interaction_timestamp(),
        "prompt": prompt,
        "task_contract": dict(task_contract),
    }


def host_interaction_capability_call_receipt(
    *,
    capability: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    source: str = "",
    phase: str = "",
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed capability execution, helps with shaping one stable receipt event for a capability call and its result.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping capability effects explicit and comparable across chat-driven and deterministic CLI-driven execution.

    Example Input Output:
        Input: `host_interaction_capability_call_receipt(capability='ws.skill.catalog', arguments={'target': 'skills'}, result={'status': 'ok'}, source='cli')`
        Output: {'kind': 'capability_call', 'timestamp': '2026-04-04T00:00:00+00:00', 'capability': 'ws.skill.catalog', 'arguments': {'target': 'skills'}, 'result': {'status': 'ok'}, 'source': 'cli'}

    Args:
        capability: Value for `capability` used by `host_interaction_capability_call_receipt`. Expected type: `str`.
        arguments: Value for `arguments` used by `host_interaction_capability_call_receipt`. Expected type: `dict[str, Any]`.
        result: Value for `result` used by `host_interaction_capability_call_receipt`. Expected type: `dict[str, Any]`.
        source: Value for `source` used by `host_interaction_capability_call_receipt`. Expected type: `str`. Defaults to `''`.
        phase: Value for `phase` used by `host_interaction_capability_call_receipt`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_capability_call_receipt`.
    """
    payload = {
        "kind": "capability_call",
        "timestamp": _host_interaction_timestamp(),
        "capability": capability,
        "arguments": json_safe(dict(arguments)),
        "result": json_safe(dict(result)),
    }
    target = _host_interaction_capability_target(arguments=arguments, result=result)
    if target:
        payload["target"] = target
    delegation = _host_interaction_capability_delegation_receipt(arguments=arguments, result=result)
    if delegation is not None:
        payload["delegation"] = delegation
    invocation = _host_interaction_capability_invocation_receipt(arguments=arguments, result=result)
    if invocation is not None:
        payload["invocation"] = invocation
    composition = _host_interaction_capability_composition_receipt(arguments=arguments, result=result)
    if composition is not None:
        payload["composition"] = composition
    if source:
        payload["source"] = source
    if phase:
        payload["phase"] = phase
    return payload


def host_interaction_assistant_response_receipt(
    *,
    assistant_text: str,
    model: str,
    rounds: int,
    tool_calls: int,
    requested_skill: str = "",
    fulfilled_by: str = "",
    fallback_used: bool | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed prompt sessions, helps with shaping one stable receipt event for the final assistant-visible response.

    Reference to Theory:
        Supports the shared host-interaction substrate by making the final answer, model identity, and tool-call count replayable independent of the surrounding shell.

    Example Input Output:
        Input: `host_interaction_assistant_response_receipt(assistant_text='Done.', model='gpt-5.4', rounds=1, tool_calls=0, requested_skill='Demo Skill', fulfilled_by='ws.skill.invoke', fallback_used=False)`
        Output: {'kind': 'assistant_response', 'timestamp': '2026-04-04T00:00:00+00:00', 'assistant_text': 'Done.', 'model': 'gpt-5.4', 'rounds': 1, 'tool_calls': 0, 'requested_skill': 'Demo Skill', 'fulfilled_by': 'ws.skill.invoke', 'fallback_used': False}

    Args:
        assistant_text: Value for `assistant_text` used by `host_interaction_assistant_response_receipt`. Expected type: `str`.
        model: Value for `model` used by `host_interaction_assistant_response_receipt`. Expected type: `str`.
        rounds: Value for `rounds` used by `host_interaction_assistant_response_receipt`. Expected type: `int`.
        tool_calls: Value for `tool_calls` used by `host_interaction_assistant_response_receipt`. Expected type: `int`.
        requested_skill: Value for `requested_skill` used by `host_interaction_assistant_response_receipt`. Expected type: `str`. Defaults to `''`.
        fulfilled_by: Value for `fulfilled_by` used by `host_interaction_assistant_response_receipt`. Expected type: `str`. Defaults to `''`.
        fallback_used: Value for `fallback_used` used by `fallback_used`. Expected type: `bool | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_assistant_response_receipt`.
    """
    payload = {
        "kind": "assistant_response",
        "timestamp": _host_interaction_timestamp(),
        "assistant_text": assistant_text,
        "model": model,
        "rounds": int(rounds),
        "tool_calls": int(tool_calls),
    }
    if requested_skill:
        payload["requested_skill"] = str(requested_skill)
    if fulfilled_by:
        payload["fulfilled_by"] = str(fulfilled_by)
    if fallback_used is not None:
        payload["fallback_used"] = bool(fallback_used)
    return payload


def host_interaction_delegation_approval_requested_receipt(
    *,
    request: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed escalation prompting, helps with shaping one stable receipt event for a delegation-approval request.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping approval requests explicit at the host boundary rather than burying them inside worker behavior.

    Example Input Output:
        Input: `host_interaction_delegation_approval_requested_receipt(request={'capability': 'ws.skill.invoke'})`
        Output: {'kind': 'delegation_approval_requested', 'timestamp': '2026-04-04T00:00:00+00:00', 'request': {'capability': 'ws.skill.invoke'}}

    Args:
        request: Value for `request` used by `host_interaction_delegation_approval_requested_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_delegation_approval_requested_receipt`.
    """
    return {
        "kind": "delegation_approval_requested",
        "timestamp": _host_interaction_timestamp(),
        "request": dict(request),
    }


def host_interaction_delegation_approval_decision_receipt(
    *,
    request: dict[str, Any],
    decision: dict[str, Any],
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like shared host-backed escalation prompting, helps with shaping one stable receipt event for the resulting delegation approval or denial decision.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping host approval decisions explicit and replayable across shells.

    Example Input Output:
        Input: `host_interaction_delegation_approval_decision_receipt(request={'capability': 'ws.skill.invoke'}, decision={'approved': True})`
        Output: {'kind': 'delegation_approval_decision', 'timestamp': '2026-04-04T00:00:00+00:00', 'request': {'capability': 'ws.skill.invoke'}, 'decision': {'approved': True}}

    Args:
        request: Value for `request` used by `host_interaction_delegation_approval_decision_receipt`. Expected type: `dict[str, Any]`.
        decision: Value for `decision` used by `host_interaction_delegation_approval_decision_receipt`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_delegation_approval_decision_receipt`.
    """
    return {
        "kind": "delegation_approval_decision",
        "timestamp": _host_interaction_timestamp(),
        "request": dict(request),
        "decision": dict(decision),
    }
