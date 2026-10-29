# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

from realized_core_llm import (
    ChatContentPolicy,
    ChatProviderDependencyError,
    ChatRequestFallback,
    ChatRetryPolicy,
    OpenAICompatibleChatTransport,
    build_openai_compatible_client,
)
from realized_core_semantics.semantic_text import collapse_ws
from workstation.skills.core.direct_composition import prompt_explicitly_requests_skill
from workstation.foundation.models import TaskBoundaryContract, WorkstationSession
from workstation.skills.core.skill_invocation import workstation_skill_invocation_status_answer


def workstation_tool_wire_name(capability_name: str) -> str:
    """
    High Level Purpose:
        In circumstances like OpenAI-compatible workstation tool exposure, helps with translating a workstation capability name into a provider-safe function name.

    Reference to Theory:
        Supports the workstation capability model by preserving the stable workstation capability vocabulary while adapting it to provider-specific tool-name constraints.

    Example Input Output:
        Input: `workstation_tool_wire_name(capability_name='ws.repo.tree')`
        Output: 'ws__repo__tree'

    Args:
        capability_name: Value for `capability_name` used by `workstation_tool_wire_name`. Expected type: `str`.

    Returns:
        str: Result produced by `workstation_tool_wire_name`.
    """
    return str(capability_name).replace(".", "__")


def workstation_tool_capability_name(wire_name: str) -> str:
    """
    High Level Purpose:
        In circumstances like provider tool-call decoding for workstation sessions, helps with recovering the stable workstation capability name from a provider-safe wire name.

    Reference to Theory:
        Supports the workstation capability model by keeping provider adaptation reversible without changing the workstation-facing capability vocabulary.

    Example Input Output:
        Input: `workstation_tool_capability_name(wire_name='ws__repo__tree')`
        Output: 'ws.repo.tree'

    Args:
        wire_name: Value for `wire_name` used by `workstation_tool_capability_name`. Expected type: `str`.

    Returns:
        str: Result produced by `workstation_tool_capability_name`.
    """
    return str(wire_name).replace("__", ".")


def normalize_workstation_tool_definitions_for_provider(
    tool_definitions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """
    High Level Purpose:
        In circumstances like OpenAI-compatible workstation tool prompting, helps with converting stable workstation capability definitions into provider-safe tool definitions together with a reverse name map.

    Reference to Theory:
        Supports the workstation host-owned driver by adapting the tool surface to provider constraints without changing the stable workstation capability vocabulary.

    Example Input Output:
        Input: `normalize_workstation_tool_definitions_for_provider(tool_definitions=[{'type': 'function', 'function': {'name': 'ws.repo.tree', 'parameters': {'type': 'object'}}}])`
        Output: ([{'type': 'function', 'function': {'name': 'ws__repo__tree', 'parameters': {'type': 'object'}}}], {'ws__repo__tree': 'ws.repo.tree'})

    Args:
        tool_definitions: Value for `tool_definitions` used by `normalize_workstation_tool_definitions_for_provider`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[list[dict[str, Any]], dict[str, str]]: Result produced by `normalize_workstation_tool_definitions_for_provider`.
    """
    normalized: list[dict[str, Any]] = []
    reverse_map: dict[str, str] = {}
    for definition in tool_definitions:
        function_payload = dict(definition.get("function", {}))
        original_name = str(function_payload.get("name", ""))
        wire_name = workstation_tool_wire_name(original_name)
        reverse_map[wire_name] = original_name
        function_payload["name"] = wire_name
        normalized.append(
            {
                "type": definition.get("type", "function"),
                "function": function_payload,
            }
        )
    return normalized, reverse_map


def build_workstation_openai_client(*, api_key_env_var: str) -> Any:
    """
    High Level Purpose:
        In circumstances like host-owned workstation prompting, helps with building the OpenAI-compatible client while keeping credential resolution outside the workstation root.

    Reference to Theory:
        Supports the workstation host-owned session-driver model by ensuring provider access remains outside the sandboxed workstation surface.

    Example Input Output:
        Input: `build_workstation_openai_client(api_key_env_var='OPENAI_API_KEY')`
        Output: OpenAI(...)

    Args:
        api_key_env_var: Value for `api_key_env_var` used by `build_workstation_openai_client`. Expected type: `str`.

    Returns:
        Any: Result produced by `build_workstation_openai_client`.
    """
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        raise RuntimeError(f"{api_key_env_var} environment variable not set.")
    base_url = os.getenv("OPENAI_BASE_URL")
    try:
        return build_openai_compatible_client(
            api_key=api_key,
            timeout_seconds=float(
                os.getenv(
                    "WORKSTATION_OPENAI_TIMEOUT_SECONDS",
                    os.getenv("LLM_TIMEOUT_SECONDS", "60"),
                )
            ),
            base_url=base_url,
        )
    except ChatProviderDependencyError as exc:
        raise RuntimeError(
            "The 'openai' package is required for workstation LLM prompting."
        ) from exc


def resolve_workstation_openai_model(model: str | None = None) -> str:
    """
    High Level Purpose:
        In circumstances like host-owned workstation prompting, helps with resolving the model name for one workstation session turn.

    Reference to Theory:
        Supports the workstation host-owned LLM model by making provider selection explicit and outside the workstation boundary.

    Example Input Output:
        Input: `resolve_workstation_openai_model(model=None)`
        Output: 'gpt-5.4'

    Args:
        model: Value for `model` used by `resolve_workstation_openai_model`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        str: Result produced by `resolve_workstation_openai_model`.
    """
    resolved = (model or os.getenv("WORKSTATION_OPENAI_MODEL") or os.getenv("OPENAI_MODEL") or "").strip()
    if not resolved:
        raise RuntimeError("No workstation model configured. Set WORKSTATION_OPENAI_MODEL or OPENAI_MODEL.")
    return resolved


def build_workstation_system_message(
    session: WorkstationSession,
    task_contract: TaskBoundaryContract,
) -> str:
    """
    High Level Purpose:
        In circumstances like host-owned workstation LLM turns, helps with building the governing system prompt that explains the workstation boundary, attachments, and available planning contract.

    Reference to Theory:
        Supports the workstation model by keeping attachments, capabilities, and boundary-complete task state explicit instead of ambient.

    Example Input Output:
        Input: `build_workstation_system_message(session=3, task_contract=3)`
        Output: 'You are operating inside one governed workstation session...'

    Args:
        session: Value for `session` used by `build_workstation_system_message`. Expected type: `WorkstationSession`.
        task_contract: Value for `task_contract` used by `build_workstation_system_message`. Expected type: `TaskBoundaryContract`.

    Returns:
        str: Result produced by `build_workstation_system_message`.
    """
    attachment_lines = [
        f"- {attachment.name}: kind={attachment.kind}, access_mode={attachment.access_mode}, mount_path={attachment.mount_path}"
        for attachment in session.attachments
    ]
    capability_lines = [f"- {capability}" for capability in session.allowed_capabilities]
    has_skill_invoke = "ws.skill.invoke" in session.allowed_capabilities
    has_skill_compose = "ws.skill.compose" in session.allowed_capabilities
    has_workflow_run = "ws.workflow.run" in session.allowed_capabilities
    contract_json = json.dumps(task_contract.to_dict(), indent=2, sort_keys=True)
    shortlist_lines: list[str] = []
    preferred_shortlist_title = ""
    shortlist_path = session.root() / "TASK_SKILLS.json"
    if shortlist_path.exists():
        try:
            shortlist_payload = json.loads(shortlist_path.read_text())
            shortlist_skills = list(shortlist_payload.get("skills", []))
            if shortlist_skills:
                preferred_shortlist_title = str(shortlist_skills[0].get("title", ""))
            for item in shortlist_skills[:8]:
                input_names = sorted(
                    str(name).strip()
                    for name in dict(item.get("inputs", {})).keys()
                    if str(name).strip()
                )
                shortlist_lines.append(
                    "- "
                    + str(item.get("title", ""))
                    + (
                        f" (score={item.get('score')}, executor={item.get('executor_framework', '')}"
                        + (f", inputs={', '.join(input_names)}" if input_names else "")
                        + ")"
                        if item.get("score") is not None
                        else ""
                    )
                )
        except Exception:
            shortlist_lines = []
            preferred_shortlist_title = ""
    return (
        "You are operating inside one governed workstation session.\n"
        "Use only the provided workstation tools when you need host interaction.\n"
        "Do not assume ambient filesystem, shell, network, or secret access.\n"
        "Workstation discovery files such as README.md, WORKSTATION.toml, ATTACHMENTS.json, TOOLS.json, TASK.md, TASK_SKILLS.json, and SKILLS.json when present live on the `session` attachment.\n"
        "Attachments:\n"
        f"{chr(10).join(attachment_lines)}\n"
        "Allowed capabilities:\n"
        f"{chr(10).join(capability_lines)}\n"
        "Current normalized task boundary contract:\n"
        f"{contract_json}\n"
        + (
            "Prompt-local skill shortlist:\n"
            f"{chr(10).join(shortlist_lines)}\n"
            if shortlist_lines
            else ""
        )
        + (
            "If `ws.skill.invoke` is available, prefer installed skills for higher-level behaviors and use `SKILLS.json` to discover them.\n"
            + (
                "If `ws.workflow.run` is available, prefer it for explicit multi-step skill pipelines, conditional skill branches, iterative skill loops, or any task that needs skill-to-skill field mapping through first-class workflow objects.\n"
                if has_workflow_run
                else (
                    "If `ws.skill.compose` is available, prefer it for explicit multi-step skill pipelines, conditional skill branches, iterative skill loops, or any task that needs skill-to-skill field mapping.\n"
                    if has_skill_compose
                    else ""
                )
            )
            + (
                "Use `ws.workflow.list` and `ws.workflow.get` when you need to inspect persisted workflow plans or prior workflow runs.\n"
                if "ws.workflow.list" in session.allowed_capabilities and "ws.workflow.get" in session.allowed_capabilities
                else ""
            )
            +
            "If `ws.skill.catalog` is available, use it when you need the current persistent skill-home inventory or skill-home locations; when many skills may be installed, prefer a short `query` to narrow the worker shortlist first.\n"
            "If `TASK_SKILLS.json` is present, treat it as the preferred shortlist for this exact prompt before falling back to generic fs/process tools.\n"
            "If `ws.skill.import` or `ws.skill.export` are available, use them for worker lifecycle operations instead of editing the skill store directly.\n"
            "If `ws.markdown.create` or `ws.markdown.append` are available, use them when the user wants to save chat learnings into markdown instead of trying to write files through unrelated tools.\n"
            "When repository search or tree inspection is needed, prefer the corresponding repo skill listed in `SKILLS.json` over a direct high-level workstation repo tool.\n"
            "If the user explicitly asks to use a skill or skill family, stay on the skill path: invoke the skill, ask a brief clarification, ask for permission escalation, or return a bounded skill-invocation failure. Do not silently substitute unrelated generic fs/process/repo tools.\n"
            + (
                f"For this prompt, try invoking the top shortlisted skill `{preferred_shortlist_title}` before generic fs/process tools when it fits the ask.\n"
                if preferred_shortlist_title
                else ""
            )
            +
            "When invoking a skill, request delegated workstation capabilities only if the invocation truly needs them.\n"
            if has_skill_invoke
            else ""
        )
        + "When the task requires host inspection, use tools before answering."
    )


def run_workstation_openai_turn(
    *,
    session: WorkstationSession,
    task_contract: TaskBoundaryContract,
    prompt: str,
    message_history: list[dict[str, Any]],
    tool_definitions: list[dict[str, Any]],
    tool_executor: Callable[[str, dict[str, Any]], dict[str, Any]],
    model: str | None = None,
    client: Any | None = None,
    max_tool_rounds: int = 8,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like one host-owned workstation session turn, helps with running an OpenAI-compatible chat/tool loop until the model emits a final assistant answer.

    Reference to Theory:
        Supports the workstation host-owned session-driver model by keeping the provider call and tool mediation outside the workstation boundary while still allowing governed capability use.

    Example Input Output:
        Input: `run_workstation_openai_turn(session=3, task_contract=3, prompt='Inspect the project.', message_history=[], tool_definitions=[], tool_executor=lambda n, a: {}, model='gpt-5.4', client=3)`
        Output: {'assistant_text': 'I inspected the project.', 'tool_receipts': [], 'model': 'gpt-5.4', 'rounds': 1}

    Args:
        session: Value for `session` used by `session`. Expected type: `WorkstationSession`.
        task_contract: Value for `task_contract` used by `task_contract`. Expected type: `TaskBoundaryContract`.
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.
        message_history: Value for `message_history` used by `message_history`. Expected type: `list[dict[str, Any]]`.
        tool_definitions: Value for `tool_definitions` used by `tool_definitions`. Expected type: `list[dict[str, Any]]`.
        tool_executor: Value for `tool_executor` used by `tool_executor`. Expected type: `Callable[[str, dict[str, Any]], dict[str, Any]]`.
        model: Value for `model` used by `model`. Expected type: `str | None`. Defaults to `None`.
        client: Value for `client` used by `client`. Expected type: `Any | None`. Defaults to `None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`. Defaults to `8`.

    Returns:
        dict[str, Any]: Result produced by `run_workstation_openai_turn`.
    """
    client = client or build_workstation_openai_client(api_key_env_var=session.openai_env_var or "OPENAI_API_KEY")
    resolved_model = model or os.getenv("WORKSTATION_OPENAI_MODEL") or os.getenv("OPENAI_MODEL")
    if not resolved_model:
        if client is not None:
            resolved_model = "workstation-test-model"
        else:
            resolved_model = resolve_workstation_openai_model(model)
    provider_tool_definitions, tool_name_map = normalize_workstation_tool_definitions_for_provider(
        tool_definitions
    )
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": build_workstation_system_message(session, task_contract),
        },
        *message_history,
        {
            "role": "user",
            "content": prompt,
        },
    ]
    tool_receipts: list[dict[str, Any]] = []
    explicit_skill_request = prompt_explicitly_requests_skill(prompt)
    rounds = 0
    while rounds < max_tool_rounds:
        rounds += 1
        request_kwargs: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "tools": provider_tool_definitions or None,
            "temperature": 0.0,
        }
        response = _create_workstation_chat_completion(client=client, request_kwargs=request_kwargs)
        tool_calls = [tool_call.to_dict() for tool_call in response.tool_calls]
        content = response.text
        if tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": content or "",
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                arguments = json.loads(tool_call["function"]["arguments"] or "{}")
                capability_name = tool_name_map.get(
                    tool_call["function"]["name"],
                    workstation_tool_capability_name(tool_call["function"]["name"]),
                )
                result = tool_executor(capability_name, arguments)
                tool_receipts.append(
                    {
                        "tool_call_id": tool_call["id"],
                        "name": capability_name,
                        "wire_name": tool_call["function"]["name"],
                        "arguments": arguments,
                        "result": result,
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result, sort_keys=True),
                    }
                )
                if explicit_skill_request and capability_name in {"ws.skill.invoke", "ws.skill.compose", "ws.workflow.run"}:
                    status = collapse_ws(str(result.get("status", ""))).casefold()
                    if status in {"approval_required", "unsupported", "error"}:
                        if capability_name == "ws.skill.invoke":
                            assistant_text = (
                                workstation_skill_invocation_status_answer(result)
                                or f"Invocation of {collapse_ws(str(result.get('skill_title', 'requested skill')))} failed."
                            )
                        else:
                            assistant_text = collapse_ws(str(result.get("answer", ""))) or "Requested skill composition failed."
                        return {
                            "assistant_text": assistant_text,
                            "tool_receipts": tool_receipts,
                            "model": resolved_model,
                            "rounds": rounds,
                            "requested_skill": collapse_ws(
                                str(result.get("skill_title", arguments.get("skill_title", "")))
                            ) or ", ".join(
                                str(item) for item in list(result.get("requested_skill_titles", []))[:3]
                            ),
                            "fulfilled_by": capability_name,
                            "fallback_used": False,
                        }
                if capability_name in {"ws.skill.invoke", "ws.skill.compose", "ws.workflow.run"}:
                    status = collapse_ws(str(result.get("status", ""))).casefold()
                    if status in {"approval_required", "unsupported"}:
                        if capability_name == "ws.skill.invoke":
                            assistant_text = (
                                workstation_skill_invocation_status_answer(result)
                                or f"Invocation of {collapse_ws(str(result.get('skill_title', arguments.get('skill_title', 'requested skill'))))} requires approval before it can continue."
                            )
                        else:
                            assistant_text = collapse_ws(str(result.get("answer", ""))) or "Requested skill composition requires approval before it can continue."
                        return {
                            "assistant_text": assistant_text,
                            "tool_receipts": tool_receipts,
                            "model": resolved_model,
                            "rounds": rounds,
                            "requested_skill": collapse_ws(
                                str(result.get("skill_title", arguments.get("skill_title", "")))
                            ) or ", ".join(
                                str(item) for item in list(result.get("requested_skill_titles", []))[:3]
                            ),
                            "fulfilled_by": capability_name,
                            "fallback_used": False,
                        }
            continue
        assistant_text = content.strip() if content else ""
        if explicit_skill_request and not any(
            str(item.get("name", "")).strip() in {"ws.skill.invoke", "ws.skill.compose", "ws.workflow.run"} for item in tool_receipts
        ):
            assistant_text = (
                "This request explicitly asked to use a skill, but no skill was invoked. "
                "Retry with a clearer skill name or let the workstation clarify the required inputs."
            )
        messages.append({"role": "assistant", "content": assistant_text})
        return {
            "assistant_text": assistant_text,
            "tool_receipts": tool_receipts,
            "model": resolved_model,
            "rounds": rounds,
            "fallback_used": bool(explicit_skill_request and not any(
                str(item.get("name", "")).strip() in {"ws.skill.invoke", "ws.skill.compose", "ws.workflow.run"} for item in tool_receipts
            )),
        }
    raise RuntimeError(f"Workstation LLM turn exceeded max_tool_rounds={max_tool_rounds}.")


def _create_workstation_chat_completion(
    *,
    client: Any,
    request_kwargs: dict[str, Any],
    max_attempts: int = 3,
    retry_delay_seconds: float = 1.0,
) -> Any:
    """
    High Level Purpose:
        In circumstances like host-owned workstation provider calls, helps with issuing one chat-completion request while tolerating a small class of transient provider failures and provider-specific unsupported-temperature errors.

    Reference to Theory:
        Supports the workstation shell by keeping provider reliability handling in the host-owned driver instead of leaking transient transport concerns into workstation or skill logic.

    Example Input Output:
        Input: `_create_workstation_chat_completion(client=3, request_kwargs={'model': 'gpt-5.4', 'messages': []})`
        Output: provider response object

    Args:
        client: Value for `client` used by `_create_workstation_chat_completion`. Expected type: `Any`.
        request_kwargs: Value for `request_kwargs` used by `_create_workstation_chat_completion`. Expected type: `dict[str, Any]`.
        max_attempts: Value for `max_attempts` used by `_create_workstation_chat_completion`. Expected type: `int`. Defaults to `3`.
        retry_delay_seconds: Value for `retry_delay_seconds` used by `_create_workstation_chat_completion`. Expected type: `float`. Defaults to `1.0`.

    Returns:
        Any: Result produced by `_create_workstation_chat_completion`.
    """
    attempts = max(1, int(max_attempts))
    return OpenAICompatibleChatTransport(
        client=client,
        fallbacks=(
            ChatRequestFallback(
                parameter="temperature",
                required_error_markers=("temperature",),
                any_error_markers=("unsupported", "default (1)"),
            ),
        ),
        retry_policy=ChatRetryPolicy(
            max_transient_retries=max(0, attempts - 1),
            max_provider_attempts=attempts,
            retry_delays_seconds=(max(0.0, float(retry_delay_seconds)),),
            retry_status_codes=frozenset({429}),
            retry_server_errors=True,
            retry_error_markers=(
                "error code: 500",
                "error code: 502",
                "error code: 503",
                "error code: 504",
                "error code: 429",
                "internalservererror",
                "rate limit",
                "temporarily unavailable",
                "timed out",
                "timeout",
                "connection reset",
                "server error",
            ),
        ),
        content_policy=ChatContentPolicy(
            mapping_requires_text_type=True,
            include_object_text=True,
            strip_string_content=False,
        ),
        sleep=time.sleep,
    ).complete(request_kwargs)


_LEGACY_MODULE = "workstation.foundation.host.llm_driver"
for _public_function in (
    workstation_tool_wire_name,
    workstation_tool_capability_name,
    normalize_workstation_tool_definitions_for_provider,
    build_workstation_openai_client,
    resolve_workstation_openai_model,
    build_workstation_system_message,
    run_workstation_openai_turn,
):
    _public_function.__module__ = _LEGACY_MODULE

__all__ = [
    "build_workstation_openai_client",
    "build_workstation_system_message",
    "normalize_workstation_tool_definitions_for_provider",
    "resolve_workstation_openai_model",
    "run_workstation_openai_turn",
    "workstation_tool_capability_name",
    "workstation_tool_wire_name",
]
