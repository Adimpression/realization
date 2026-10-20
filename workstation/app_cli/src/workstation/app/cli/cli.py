# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import TextIO

from host_interaction_receipts import host_interaction_capability_call_receipt
from semantic_text import collapse_ws
from workstation.foundation.host.subject_workflow import create_subject_workflow_client
from workstation.ui.shared.activity_view import start_workstation_activity_tail, workstation_activity_log_offset
from workstation.shell.core.application_facade import (
    DEFAULT_WORKSTATION_CAPABILITIES,
    WorkstationDelegationEscalationDecision,
    WorkstationDelegationEscalationRequest,
    append_workstation_receipt_and_publish,
    execute_workstation_capability,
    launch_workstation_session,
    load_workstation_session,
    prompt_workstation_session,
    run_workstation_chat_slash_command,
)
from workstation.shell.core.trial_validation import validate_workstation_trial_domains
from workstation.ui.textual.chat_ui import (
    prompt_for_workstation_escalation_enhanced,
    run_enhanced_workstation_chat_loop,
    workstation_chat_assistant_block_text,
    workstation_chat_named_block_text,
    workstation_chat_context,
    workstation_chat_help_text,
    workstation_chat_ui_supported,
)


def handle_workstation_launch_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like CLI-driven creation of one workstation session, helps with materializing the workstation root and returning its session summary as JSON.

    Reference to Theory:
        Supports the workstation entry surface by letting the host create one governed session without entangling it with the outer BSSC controller flow.

    Example Input Output:
        Input: `handle_workstation_launch_command(args=Namespace(root=Path('/tmp/ws'), workspace=Path('/tmp/project'), task='Inspect the project.'))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-launch`.

    Returns:
        int: Process-style exit status.
    """
    capabilities = tuple(args.capability or DEFAULT_WORKSTATION_CAPABILITIES)
    report = launch_workstation_session(
        root_path=Path(args.root),
        workspace_path=Path(args.workspace),
        skills_sqlite_path=Path(args.skills_sqlite) if getattr(args, "skills_sqlite", None) else None,
        initial_task=args.task or "",
        workspace_name=args.workspace_name,
        allowed_capabilities=capabilities,
        openai_env_var=args.openai_env_var,
        openai_profile=args.openai_profile,
        allow_direct_llm_decomposition=bool(getattr(args, "allow_direct_llm_decomposition", True)),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def handle_workstation_prompt_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like CLI-driven workstation usage, helps with sending one user prompt through the host-owned session driver and printing the resulting turn report as JSON.

    Reference to Theory:
        Supports the workstation entry surface by routing natural-language prompts into boundary-complete task normalization and the host-owned LLM/tool loop.

    Example Input Output:
        Input: `handle_workstation_prompt_command(args=Namespace(root=Path('/tmp/ws'), prompt='Inspect the project.', model='gpt-5.4'))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-prompt`.

    Returns:
        int: Process-style exit status.
    """
    report = prompt_workstation_session(
        root_path=Path(args.root),
        prompt=args.prompt,
        model=args.model,
        max_tool_rounds=args.max_tool_rounds,
    )
    if getattr(args, "report_out", None):
        Path(args.report_out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def handle_workstation_chat_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like interactive workstation use from a terminal, helps with running a host-owned REPL loop over one existing workstation session.

    Reference to Theory:
        Supports the workstation REPL model by keeping the loop outside the workstation boundary while reusing the same host-owned session driver for each turn.

    Example Input Output:
        Input: `handle_workstation_chat_command(args=Namespace(root=Path('/tmp/ws'), model='gpt-5.4', max_tool_rounds=8))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-chat`.

    Returns:
        int: Process-style exit status.
    """
    return run_workstation_chat_loop(
        root=Path(args.root),
        model=args.model,
        max_tool_rounds=args.max_tool_rounds,
        input_stream=sys.stdin,
        output_stream=sys.stdout,
    )


def handle_workstation_grpc_host_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like cross-platform workstation projection hosting, helps with launching the combined workstation gRPC host over TCP together with the companion artifact download surface.

    Reference to Theory:
        Supports the projection split by exposing the shared workstation contract over transport surfaces that non-local clients such as Flutter desktop, mobile, and web can consume without assuming a shared filesystem.

    Example Input Output:
        Input: `handle_workstation_grpc_host_command(args=Namespace(serve_root=[Path('/tmp/ws')], host='127.0.0.1', port=50051, asset_host='127.0.0.1', asset_port=8787))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-grpc-host`.

    Returns:
        int: Process-style exit status.
    """
    from workstation.grpc.implementation.workstation_artifact_http import start_workstation_artifact_http_server
    from workstation.grpc.implementation.workstation_bootstrap_grpc import WorkstationRootRegistry
    from workstation.grpc.implementation.workstation_grpc_host import (
        bind_workstation_grpc_server_tcp,
        build_workstation_grpc_server,
    )

    served_roots = WorkstationRootRegistry.from_paths(
        (Path(path) for path in getattr(args, "serve_root", ()) or ()),
        default_root=str(getattr(args, "default_root", "") or ""),
    ).descriptors()
    artifact_http = start_workstation_artifact_http_server(
        host=str(getattr(args, "asset_host", "127.0.0.1") or "127.0.0.1"),
        port=int(getattr(args, "asset_port", 8787) or 8787),
    )
    artifact_download_base_url = collapse_ws(getattr(args, "asset_base_url", "")) or artifact_http.base_url
    server = build_workstation_grpc_server(
        served_roots=served_roots,
        artifact_download_base_url=artifact_download_base_url,
        artifact_download_registry=artifact_http.registry,
        allow_local_path_open=bool(getattr(args, "allow_local_path_open", True)),
    )
    bound = bind_workstation_grpc_server_tcp(
        server,
        host=str(getattr(args, "host", "127.0.0.1") or "127.0.0.1"),
        port=int(getattr(args, "port", 50051) or 50051),
    )
    if bound <= 0:
        artifact_http.close()
        raise RuntimeError("Failed to bind workstation gRPC host.")
    server.start()
    print(
        json.dumps(
            {
                "grpc_host": str(getattr(args, "host", "127.0.0.1") or "127.0.0.1"),
                "grpc_port": int(bound),
                "asset_base_url": artifact_download_base_url,
                "asset_http_bind": f"{artifact_http.server.server_address[0]}:{artifact_http.server.server_address[1]}",
                "served_roots": [str(root.root_path) for root in served_roots],
            },
            indent=2,
            sort_keys=True,
        )
    )
    try:
        server.wait_for_termination()
    finally:
        server.stop(grace=None).wait()
        artifact_http.close()
    return 0


def handle_workstation_skill_catalog_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like deterministic workstation lifecycle inspection from the CLI, helps with returning the current persistent workstation skill catalog for one workstation session.

    Reference to Theory:
        Supports the workstation lifecycle surface by making worker inventory inspection available as a first-class CLI operation instead of only through conversational tool use.

    Example Input Output:
        Input: `handle_workstation_skill_catalog_command(args=Namespace(root=Path('/tmp/ws')))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-skill-catalog`.

    Returns:
        int: Process-style exit status.
    """
    session = load_workstation_session(Path(args.root))
    capability_arguments = {
        "target": "skills",
        "query": str(getattr(args, "query", "")),
    }
    if getattr(args, "limit", None) is not None:
        capability_arguments["limit"] = int(args.limit)
    report = execute_workstation_capability(session, "ws.skill.catalog", capability_arguments)
    _append_workstation_cli_receipt(
        root=Path(args.root),
        session_id=session.session_id,
        capability="ws.skill.catalog",
        arguments=capability_arguments,
        result=report,
    )
    _emit_workstation_cli_report(report=report, report_out=getattr(args, "report_out", None))
    return 0


def handle_workstation_skill_import_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like deterministic workstation skill lifecycle management from the CLI, helps with importing one portable skill bundle into the persistent workstation skill home for one workstation session.

    Reference to Theory:
        Supports the workstation lifecycle surface by making governed worker import available as a first-class CLI operation over the same persistent skill home used by chat.

    Example Input Output:
        Input: `handle_workstation_skill_import_command(args=Namespace(root=Path('/tmp/ws'), skill_file=Path('/tmp/skill.yaml')))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-skill-import`.

    Returns:
        int: Process-style exit status.
    """
    root = Path(args.root)
    session = load_workstation_session(root)
    source_file = Path(args.skill_file).expanduser().resolve()
    imports_attachment = _require_workstation_attachment(session, "skills_imports")
    staged_source_path = Path(imports_attachment.source) / source_file.name
    staged_source_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_file, staged_source_path)
    capability_arguments = {
        "target": "skills",
        "source_target": "skills_imports",
        "path": source_file.name,
    }
    report = execute_workstation_capability(session, "ws.skill.import", capability_arguments)
    _append_workstation_cli_receipt(
        root=root,
        session_id=session.session_id,
        capability="ws.skill.import",
        arguments=capability_arguments,
        result=report,
    )
    _emit_workstation_cli_report(report=report, report_out=getattr(args, "report_out", None))
    return 0


def handle_workstation_skill_export_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like deterministic workstation skill lifecycle management from the CLI, helps with exporting one governed worker from the persistent workstation skill home for one workstation session.

    Reference to Theory:
        Supports the workstation lifecycle surface by making governed worker export available as a first-class CLI operation over the same persistent skill home used by chat.

    Example Input Output:
        Input: `handle_workstation_skill_export_command(args=Namespace(root=Path('/tmp/ws'), skill_title='Workstation Greeting'))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-skill-export`.

    Returns:
        int: Process-style exit status.
    """
    root = Path(args.root)
    session = load_workstation_session(root)
    capability_arguments = {
        "target": "skills",
        "skill_title": args.skill_title,
    }
    report = execute_workstation_capability(session, "ws.skill.export", capability_arguments)
    if getattr(args, "out", None):
        host_output_path = Path(args.out).expanduser().resolve()
        host_output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(report["destination_path"]), host_output_path)
        report = dict(report)
        report["copied_to"] = str(host_output_path)
    _append_workstation_cli_receipt(
        root=root,
        session_id=session.session_id,
        capability="ws.skill.export",
        arguments=capability_arguments,
        result=report,
    )
    _emit_workstation_cli_report(report=report, report_out=getattr(args, "report_out", None))
    return 0


def handle_workstation_trial_validate_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like auditing workstation compatibility with the repository trial corpora, helps with running the workstation-oriented trial validator and emitting one JSON summary report.

    Reference to Theory:
        Supports workstation/trial integration by giving the workstation package its own repeatable validation surface without entangling it with the outer controller trial runner.

    Example Input Output:
        Input: `handle_workstation_trial_validate_command(args=Namespace(domains=['symbolsearch'], workspace=Path('/tmp/project')))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `workstation-trial-validate`.

    Returns:
        int: Process-style exit status.
    """
    report = validate_workstation_trial_domains(
        domains=tuple(getattr(args, "domains", []) or ()),
        workspace_path=Path(args.workspace) if getattr(args, "workspace", None) else None,
        report_root=Path(args.report_root) if getattr(args, "report_root", None) else None,
        model=getattr(args, "model", None),
        max_tool_rounds=int(getattr(args, "max_tool_rounds", 8)),
    )
    _emit_workstation_cli_report(report=report, report_out=getattr(args, "report_out", None))
    return 0


def run_workstation_chat_loop(
    *,
    root: Path,
    model: str | None,
    max_tool_rounds: int,
    input_stream: TextIO,
    output_stream: TextIO,
) -> int:
    """
    High Level Purpose:
        In circumstances like terminal-hosted workstation chat sessions, helps with repeatedly reading user prompts, sending them through the workstation session driver, and printing assistant replies until exit.

    Reference to Theory:
        Supports the workstation REPL model by making interactive chat a host-owned prompt surface rather than an ambient shell inside the workstation.

    Example Input Output:
        Input: `run_workstation_chat_loop(root=Path('/tmp/ws'), model='gpt-5.4', max_tool_rounds=8, input_stream=3, output_stream=3)`
        Output: 0

    Args:
        root: Value for `root` used by `run_workstation_chat_loop`. Expected type: `Path`.
        model: Value for `model` used by `model`. Expected type: `str | None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`.
        input_stream: Value for `input_stream` used by `input_stream`. Expected type: `TextIO`.
        output_stream: Value for `output_stream` used by `output_stream`. Expected type: `TextIO`.

    Returns:
        int: Result produced by `run_workstation_chat_loop`.
    """
    if workstation_chat_ui_supported(input_stream=input_stream, output_stream=output_stream):
        return run_enhanced_workstation_chat_loop(
            root=root,
            model=model,
            max_tool_rounds=max_tool_rounds,
            subject_workflow_client=create_subject_workflow_client(),
        )
    output_stream.write("Workstation chat started. Type /exit or /quit to stop.\n")
    output_stream.flush()
    while True:
        output_stream.write("workstation> ")
        output_stream.flush()
        try:
            line = input_stream.readline()
        except KeyboardInterrupt:
            output_stream.write("\nInput interrupted. Type /exit to quit.\n")
            output_stream.flush()
            continue
        if line == "":
            output_stream.write("\n")
            output_stream.flush()
            return 0
        prompt = line.strip()
        if not prompt:
            continue
        if prompt == "/help":
            output_stream.write(workstation_chat_help_text(workstation_chat_context(root)) + "\n")
            output_stream.flush()
            continue
        if prompt in {"/exit", "/quit"}:
            output_stream.write("Session ended.\n")
            output_stream.flush()
            return 0
        if prompt.startswith("/"):
            activity_stop = start_workstation_activity_tail(
                root=root,
                start_offset=workstation_activity_log_offset(root),
                emit=lambda text: _write_activity_line(output_stream=output_stream, text=text),
            )
            try:
                handled, command_output = run_workstation_chat_slash_command(root=root, command_text=prompt)
            finally:
                activity_stop()
            if handled:
                rendered = workstation_chat_named_block_text(label="shell", text=command_output)
                if rendered:
                    output_stream.write(rendered + "\n")
                    output_stream.flush()
                continue
        activity_stop = start_workstation_activity_tail(
            root=root,
            start_offset=workstation_activity_log_offset(root),
            emit=lambda text: _write_activity_line(output_stream=output_stream, text=text),
        )
        try:
            report = prompt_workstation_session(
                root_path=root,
                prompt=prompt,
                model=model,
                max_tool_rounds=max_tool_rounds,
                delegation_approval_callback=lambda request: _prompt_for_workstation_escalation(
                    request=request,
                    input_stream=input_stream,
                    output_stream=output_stream,
                ),
            )
        finally:
            activity_stop()
        rendered = workstation_chat_assistant_block_text(str(report.get("assistant_text", "")))
        if rendered:
            output_stream.write(rendered + "\n")
            output_stream.flush()


def _emit_workstation_cli_report(*, report: dict[str, object], report_out: Path | None) -> None:
    """
    High Level Purpose:
        In circumstances like workstation lifecycle CLI commands, helps with emitting one stable JSON report to stdout and optionally to a file.

    Reference to Theory:
        Supports the workstation entry surface by making deterministic lifecycle commands inspectable and scriptable.

    Example Input Output:
        Input: `_emit_workstation_cli_report(report={'status': 'ok'}, report_out=Path('/tmp/report.json'))`
        Output: None

    Args:
        report: Value for `report` used by `_emit_workstation_cli_report`. Expected type: `dict[str, object]`.
        report_out: Value for `report_out` used by `report_out`. Expected type: `Path | None`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    payload = json.dumps(report, indent=2, sort_keys=True)
    if report_out is not None:
        Path(report_out).write_text(payload + "\n")
    print(payload)


def _append_workstation_cli_receipt(
    *,
    root: Path,
    session_id: str,
    capability: str,
    arguments: dict[str, object],
    result: dict[str, object],
) -> None:
    """
    High Level Purpose:
        In circumstances like direct workstation lifecycle CLI commands, helps with appending a capability-style receipt so deterministic CLI operations remain visible in the workstation receipt log.

    Reference to Theory:
        Supports the workstation receipt model by keeping CLI lifecycle operations on the same audit surface as chat-driven capability calls.

    Example Input Output:
        Input: `_append_workstation_cli_receipt(root=Path('/tmp/ws'), session_id='ws_123', capability='ws.skill.catalog', arguments={'target': 'skills'}, result={'status': 'ok'})`
        Output: None

    Args:
        root: Value for `root` used by `_append_workstation_cli_receipt`. Expected type: `Path`.
        session_id: Value for `session_id` used by `_append_workstation_cli_receipt`. Expected type: `str`.
        capability: Value for `capability` used by `_append_workstation_cli_receipt`. Expected type: `str`.
        arguments: Value for `arguments` used by `arguments`. Expected type: `dict[str, object]`.
        result: Value for `result` used by `result`. Expected type: `dict[str, object]`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    append_workstation_receipt_and_publish(
        root_path=Path(root),
        session_id=session_id,
        receipt=host_interaction_capability_call_receipt(
            capability=capability,
            arguments=arguments,
            result=result,
            source="cli",
        ),
    )


def _write_activity_line(*, output_stream: TextIO, text: str) -> None:
    output_stream.write(f"activity {collapse_ws(str(text))}\n")
    output_stream.flush()


def _require_workstation_attachment(session, name: str):
    """
    High Level Purpose:
        In circumstances like direct workstation lifecycle CLI commands, helps with resolving one required session attachment by name and failing clearly when it is absent.

    Reference to Theory:
        Supports the workstation attachment model by keeping CLI lifecycle operations bound to declared session resources rather than ambient host paths.

    Example Input Output:
        Input: `_require_workstation_attachment(session=3, name='skills_imports')`
        Output: WorkstationAttachment(name='skills_imports', kind='skill_imports', source='/tmp/.workstation/workstation/skills/imports', access_mode='read_write', mount_path='/workstation/skills/imports')

    Args:
        session: Workstation session carrying attachments.
        name: Value for `name` used by `_require_workstation_attachment`. Expected type: `str`.

    Returns:
        object: Attachment-like object resolved by name.
    """
    for attachment in session.attachments:
        if attachment.name == name:
            return attachment
    raise ValueError(f"Required workstation attachment {name!r} is not available in this session.")


def _prompt_for_workstation_escalation(
    *,
    request: WorkstationDelegationEscalationRequest,
    input_stream: TextIO,
    output_stream: TextIO,
) -> WorkstationDelegationEscalationDecision:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat sessions, helps with asking the user whether one invocation-scoped delegated-rights escalation should be approved.

    Reference to Theory:
        Supports the workstation escalation model by keeping approval at the host-owned REPL boundary rather than inside the invoked skill.

    Example Input Output:
        Input: `_prompt_for_workstation_escalation(request=3, input_stream=3, output_stream=3)`
        Output: WorkstationDelegationEscalationDecision(approved=True, scope='one_invocation', rationale='User approved interactive escalation.')

    Args:
        request: Value for `request` used by `_prompt_for_workstation_escalation`. Expected type: `WorkstationDelegationEscalationRequest`.
        input_stream: Value for `input_stream` used by `input_stream`. Expected type: `TextIO`.
        output_stream: Value for `output_stream` used by `output_stream`. Expected type: `TextIO`.

    Returns:
        WorkstationDelegationEscalationDecision: Result produced by `_prompt_for_workstation_escalation`.
    """
    if workstation_chat_ui_supported(input_stream=input_stream, output_stream=output_stream):
        return prompt_for_workstation_escalation_enhanced(request)
    delegated_lines = ", ".join(
        f"{item.get('capability', '')}({item.get('target', '')})"
        for item in request.requested_delegation
    ) or "no additional rights listed"
    output_stream.write(
        "Escalation requested: "
        f"skill={request.skill_title or '<unknown>'}, "
        f"capability={request.capability}, "
        f"rights={delegated_lines}, "
        f"scope={request.scope}. Approve? [y/N] "
    )
    output_stream.flush()
    try:
        answer = input_stream.readline()
    except KeyboardInterrupt:
        output_stream.write("\nEscalation canceled.\n")
        output_stream.flush()
        answer = ""
    approved = str(answer or "").strip().casefold() in {"y", "yes"}
    if approved:
        return WorkstationDelegationEscalationDecision(
            approved=True,
            scope=request.scope,
            rationale="User approved interactive workstation escalation.",
        )
    return WorkstationDelegationEscalationDecision(
        approved=False,
        scope=request.scope,
        rationale="User denied interactive workstation escalation.",
    )
