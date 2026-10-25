# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Any, Iterator

import controller_runtime
from realized_core_engine import (
    EngineConfiguration,
    EngineInlet,
    inspect as inspect_core_state,
    resume as resume_core_run,
    run as start_core_run,
)
from args import (
    STATE_SQLITE_PATH_ENV,
    apply_controller_feature_toggle_overrides,
    apply_sqlite_path_override,
    parse_args,
)
from runtime_temp import runtime_temporary_directory
from side import (
    export_artifact_bundle_text,
    handle_artifact_export_command,
    handle_artifact_import_command,
    load_artifact_yaml_documents,
    resolve_import_artifact_files,
)
from replay_verifier import replay_run_bundle_document
from run_bundle_io import export_run_bundle_text, load_run_bundle_document
from governed_skill_installation import handle_import_skill_command
from skill_export_projection import handle_export_skill_command
from skill_registry import handle_export_skill_registry_command
from system_state import (
    SystemState,
    attach_evidence_specs,
    load_evidence_specs,
    load_state,
    save_state,
)
from title_semantics import PROLOG_QUERY_PRIMING_MODE_ENV
from validation_ladder import handle_validation_ladder_command
from workstation.app.cli.cli import (
    handle_workstation_chat_command,
    handle_workstation_grpc_host_command,
    handle_workstation_launch_command,
    handle_workstation_prompt_command,
    handle_workstation_skill_catalog_command,
    handle_workstation_skill_export_command,
    handle_workstation_skill_import_command,
    handle_workstation_trial_validate_command,
)
from workstation.foundation.host.controller_runtime import register_controller_runtime_provider
from workstation.foundation.host.subject_workflow import register_subject_workflow_client_factory
from workstation.contracts.runtime import GovernedTurnRequest, GovernedTurnResult
from workstation.subject.service.subject_workflow_client import InProcessSubjectWorkflowClient


def _runtime_main():
    """
    High Level Purpose:
        In circumstances like running the controller through either `python main.py` or `import main`, helps with resolving the canonical runtime namespace without duplicating the controller implementation.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `_runtime_main()`
        Output: controller_runtime

    Args:
        None.

    Returns:
        Any: Result produced by `_runtime_main`.
    """
    return controller_runtime


def build_controller(*, state: SystemState | None = None, llm_policy: str = "auto"):
    """
    High Level Purpose:
        In circumstances like CLI-run bootstrap, validation scripts, or external callers that already assembled a runtime state, helps with creating the controller instance that owns the governed semantic runtime.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `build_controller(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'), llm_policy='required')`
        Output: BSSCController(state=SystemState.bootstrap(prompt='Compute force from mass and acceleration.'), llm_policy='required')

    Args:
        state: Value for `state` used by `build_controller`. Expected type: `SystemState | None`. Defaults to `None`.
        llm_policy: Value for `llm_policy` used by `build_controller`. Expected type: `str`. Defaults to `'auto'`.

    Returns:
        Any: Result produced by `build_controller`.
    """
    if state is None:
        raise ValueError("state must be provided to build_controller in this implementation.")
    return controller_runtime.build_controller(state=state, llm_policy=llm_policy)


class _ApplicationControllerRuntimeProvider:
    """Controller implementation bound by the outer CLI composition layer."""

    def bootstrap_controller(
        self,
        *,
        semantic_unit: str,
        llm_policy: str,
    ) -> tuple[Any, Any]:
        state = SystemState.bootstrap(semantic_unit)
        return state, build_controller(state=state, llm_policy=llm_policy)

    def perform_governed_turn(
        self,
        request: GovernedTurnRequest,
    ) -> GovernedTurnResult:
        checkpoint_path = Path(request.checkpoint_path).expanduser().resolve()
        sqlite_path = Path(request.sqlite_path).expanduser().resolve()
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        treatment = str(request.treatment).strip()
        parent_run_id = str(request.parent_run_id or "").strip()
        parent_summary: dict[str, Any] | None = None
        parent_checkpoint_path = (
            Path(request.parent_checkpoint_path).expanduser().resolve()
            if request.parent_checkpoint_path is not None
            else None
        )

        if treatment != "independent":
            if parent_checkpoint_path is None or not parent_checkpoint_path.is_file():
                raise ValueError(
                    f"{treatment} requires an existing parent reduction checkpoint."
                )
            parent_summary = inspect_core_state(parent_checkpoint_path).summary
            actual_parent_run_id = str(parent_summary.get("run_id", "")).strip()
            if parent_run_id and parent_run_id != actual_parent_run_id:
                raise ValueError("The selected parent run does not match its checkpoint.")
            parent_run_id = actual_parent_run_id

        inlets: tuple[EngineInlet, ...] = ()
        if treatment == "human_contribution":
            parent_outcome = str((parent_summary or {}).get("run_outcome", ""))
            if parent_outcome not in {"paused", "incomplete"}:
                raise ValueError(
                    "A human contribution may resume only a paused or incomplete run."
                )
            inlets = (
                EngineInlet(
                    kind="human_contribution",
                    content=request.prompt,
                    source_ref=request.user_message_id,
                    provenance=(request.turn_id, request.session_id, parent_run_id),
                    context={
                        "session_id": request.session_id,
                        "turn_id": request.turn_id,
                        "parent_run_id": parent_run_id,
                    },
                ),
            )
            result = resume_core_run(
                parent_checkpoint_path,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                    inlets=inlets,
                ),
            )
        elif treatment in {"follow_up", "correction"}:
            parent_outcome = str((parent_summary or {}).get("run_outcome", ""))
            prior_answer = str((parent_summary or {}).get("final_answer", "") or "").strip()
            if parent_outcome != "completed" or not prior_answer:
                raise ValueError(
                    f"A {treatment} requires a completed parent run with a committed result."
                )
            inlets = (
                EngineInlet(
                    kind="prior_result",
                    content=prior_answer,
                    source_ref=parent_run_id,
                    provenance=(request.turn_id, request.session_id),
                    context={
                        "relationship": treatment,
                        "parent_run_id": parent_run_id,
                    },
                ),
            )
            result = start_core_run(
                request.prompt,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                    inlets=inlets,
                ),
            )
        elif treatment == "independent":
            result = start_core_run(
                request.prompt,
                configuration=EngineConfiguration(
                    state_output_path=checkpoint_path,
                    sqlite_path=sqlite_path,
                    max_steps=max(0, int(request.max_steps)),
                    llm_policy=request.llm_policy,
                ),
            )
        else:
            raise ValueError(f"Unsupported governed turn treatment: {treatment}")

        summary = dict(result.summary)
        run_outcome = str(summary.get("run_outcome", "ongoing"))
        root_status = str(dict(summary.get("root", {})).get("status", "open"))
        assistant_text = str(summary.get("final_answer", "") or "").strip()
        if not assistant_text:
            assistant_text = {
                "paused": "The governed run paused for an explicit boundary contribution.",
                "incomplete": "The governed run is incomplete and remains available for explicit continuation.",
                "ongoing": "The governed run remains in progress.",
            }.get(run_outcome, "The governed run completed without a projected answer.")
        return GovernedTurnResult(
            assistant_text=assistant_text,
            run_id=str(summary.get("run_id", "")),
            parent_run_id=parent_run_id,
            run_outcome=run_outcome,
            root_status=root_status,
            checkpoint_path=checkpoint_path,
            sqlite_path=sqlite_path,
            summary=summary,
        )

    def learn_markdown_bundle(
        self,
        *,
        root_path: Path,
        markdown_path: Path,
        source_label: str,
        bundle_output_path: Path,
        max_artifacts: int,
        source_bundle_override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        previous_learning_context_root = os.environ.get("LEARNING_CONTEXT_ROOT")
        previous_sqlite_path = os.environ.get(STATE_SQLITE_PATH_ENV)
        with runtime_temporary_directory(prefix="workstation-url-learn-state-") as sqlite_dir_text:
            sqlite_path = Path(sqlite_dir_text) / "state.sqlite3"
            os.environ["LEARNING_CONTEXT_ROOT"] = str(Path(root_path).expanduser().resolve())
            os.environ[STATE_SQLITE_PATH_ENV] = str(sqlite_path)
            try:
                label = " ".join(str(source_label or "").split()) or markdown_path.name
                state = SystemState.bootstrap(
                    f"Learn from source: {label}",
                    bootstrap_mode="markdown_ingestion",
                )
                controller = build_controller(
                    state=state,
                    llm_policy=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
                )
                report = controller.learn_from_markdown_document(
                    markdown_path,
                    max_artifacts=max(1, int(max_artifacts)),
                    source_bundle_override=source_bundle_override,
                )
                bundle_output_path.write_text(
                    export_artifact_bundle_text(list(state.learned_artifacts.values())),
                    encoding="utf-8",
                )
                return dict(report)
            finally:
                if previous_learning_context_root is None:
                    os.environ.pop("LEARNING_CONTEXT_ROOT", None)
                else:
                    os.environ["LEARNING_CONTEXT_ROOT"] = previous_learning_context_root
                if previous_sqlite_path is None:
                    os.environ.pop(STATE_SQLITE_PATH_ENV, None)
                else:
                    os.environ[STATE_SQLITE_PATH_ENV] = previous_sqlite_path


def ensure_application_controller_runtime() -> None:
    """Bind the application controller adapter at an executable composition root."""
    register_controller_runtime_provider(_ApplicationControllerRuntimeProvider())
    register_subject_workflow_client_factory(InProcessSubjectWorkflowClient)


ensure_application_controller_runtime()


@contextmanager
def sqlite_override_scope(
    args,
    *,
    temporary_when_missing: bool = False,
) -> Iterator[Path | None]:
    """
    High Level Purpose:
        In circumstances like CLI commands that need a specific persistent artifact store or a scratch conversion store, helps with applying an explicit SQLite override or a temporary SQLite path for just the lifetime of one command.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `sqlite_override_scope(args=Namespace(sqlite=Path('/workspace/realized/state/common.sqlite3')), temporary_when_missing=False)`
        Output: `Path('/workspace/realized/state/common.sqlite3')`

    Args:
        args: Parsed CLI arguments that may carry `--sqlite`.
        temporary_when_missing: Whether to create a temporary SQLite path when `--sqlite` is absent.

    Returns:
        Iterator[Path | None]: Context-managed SQLite path visible to later store construction in this command.
    """
    previous_value = os.environ.get(STATE_SQLITE_PATH_ENV)
    temporary_dir: tempfile.TemporaryDirectory[str] | None = None
    selected_path = apply_sqlite_path_override(args)
    try:
        if selected_path is None and temporary_when_missing:
            temporary_dir = runtime_temporary_directory(prefix="bssc-cli-sqlite-")
            selected_path = Path(temporary_dir.name) / "state.sqlite3"
            os.environ[STATE_SQLITE_PATH_ENV] = str(selected_path)
        yield selected_path
    finally:
        if previous_value is None:
            os.environ.pop(STATE_SQLITE_PATH_ENV, None)
        else:
            os.environ[STATE_SQLITE_PATH_ENV] = previous_value
        if temporary_dir is not None:
            temporary_dir.cleanup()


def handle_convert_markdown_to_yaml_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like turning one markdown lesson into a portable artifact bundle without committing it to the default long-lived store, helps with learning artifacts from markdown and exporting the learned result as YAML.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `handle_convert_markdown_to_yaml_command(args=Namespace(markdown_file=Path('/tmp/deviceuser.md'), out=Path('/tmp/deviceuser.yaml'), llm='off', max_artifacts=4))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `convert-markdown-to-yaml`.

    Returns:
        int: Process-style exit status.
    """
    markdown_path = Path(args.markdown_file)
    state = SystemState.bootstrap(
        f"Learn from markdown: {markdown_path.name}",
        bootstrap_mode="markdown_ingestion",
    )
    apply_controller_feature_toggle_overrides(state, args)
    controller = build_controller(state=state, llm_policy=args.llm)
    report = controller.learn_from_markdown_document(markdown_path, max_artifacts=args.max_artifacts)
    if args.state_out:
        save_state(state, args.state_out)
    if args.report_out:
        args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True))
    artifacts = list(state.learned_artifacts.values())
    payload = export_artifact_bundle_text(artifacts)
    if args.out:
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0


def handle_load_yaml_and_run_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like bootstrapping a runtime directly from exported artifact YAML and then immediately probing it with a prompt, helps with loading the YAML bundle into the selected artifact store before running the normal governed controller.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `handle_load_yaml_and_run_command(args=Namespace(artifact_file=[Path('/tmp/deviceuser.yaml')], prompt='Say hi.', llm='off', max_steps=64))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `load-yaml-and-run`.

    Returns:
        int: Process-style exit status.
    """
    runtime = _runtime_main()
    store = runtime.build_artifact_store()
    artifact_files = resolve_import_artifact_files(args)
    if not artifact_files:
        raise SystemExit("load-yaml-and-run requires --artifact-file, --artifact-files-file, or --artifact-dir.")
    imported: list[dict[str, object]] = []
    imported_artifacts = []
    imported_entries: list[tuple[Path, object]] = []
    for artifact_file in artifact_files:
        artifacts = load_artifact_yaml_documents(artifact_file)
        for artifact in artifacts:
            imported_artifacts.append(artifact)
            imported_entries.append((artifact_file, artifact))
    store_summary = store.persist_artifacts(imported_artifacts, run_id="load_yaml_and_run")
    store_reports = list(store_summary.get("reports", []))
    for (artifact_file, artifact), store_report in zip(imported_entries, store_reports, strict=False):
        imported.append(
            {
                "artifact_id": store_report.get("artifact_id", artifact.id),
                "title": artifact.title,
                "artifact_type": artifact.artifact_type,
                "representation": artifact.representation,
                "artifact_file": str(artifact_file),
                "store_report": store_report,
            }
        )
    if getattr(args, "prolog_query_priming", None):
        os.environ[PROLOG_QUERY_PRIMING_MODE_ENV] = str(args.prolog_query_priming).strip()
    state = SystemState.bootstrap(args.prompt)
    apply_controller_feature_toggle_overrides(state, args)
    for artifact in imported_artifacts:
        state.learned_artifacts[artifact.id] = artifact
    if args.evidence_file:
        attach_evidence_specs(state, load_evidence_specs(args.evidence_file))
    controller = build_controller(state=state, llm_policy=args.llm)
    controller.run(max_steps=args.max_steps)
    if args.state_out:
        save_state(state, args.state_out)
    print(
        json.dumps(
            {
                "imported_count": len(imported),
                "imported": imported,
                "run": state.summary(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def handle_export_run_bundle_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like exporting a previously saved governed run as a replayable bundle, helps with loading the durable state and packaging it together with the referenced skills and constitutional trace.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `handle_export_run_bundle_command(args=Namespace(state=Path('/tmp/state.json'), out=Path('/tmp/run-bundle.yaml'), llm='off', max_steps=64))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `export-run-bundle`.

    Returns:
        int: Process-style exit status.
    """
    runtime = _runtime_main()
    state = load_state(Path(args.state))
    store = runtime.build_artifact_store()
    payload = export_run_bundle_text(
        state,
        store,
        llm_policy=args.llm,
        max_steps=args.max_steps,
    )
    if args.out:
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0


def handle_replay_run_bundle_command(args) -> int:
    """
    High Level Purpose:
        In circumstances like replay verification of a governed execution, helps with loading the exported run bundle, importing its skills into a fresh or selected store, and rerunning the prompt.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `handle_replay_run_bundle_command(args=Namespace(bundle_file=Path('/tmp/run-bundle.yaml'), sqlite=Path('/tmp/replay.sqlite3'), llm='off', max_steps=64))`
        Output: 0

    Args:
        args: Parsed CLI arguments for `replay-run-bundle`.

    Returns:
        int: Process-style exit status.
    """
    bundle = load_run_bundle_document(Path(args.bundle_file))
    report = replay_run_bundle_document(
        bundle,
        sqlite_path=Path(args.sqlite) if getattr(args, "sqlite", None) else None,
        llm_policy=getattr(args, "llm", None),
        max_steps=getattr(args, "max_steps", None),
        state_out=getattr(args, "state_out", None),
    )
    if getattr(args, "report_out", None):
        args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main() -> int:
    """
    High Level Purpose:
        In circumstances like command-line execution of governed runs, resume flows, markdown learning, or artifact import/export, helps with routing the parsed CLI command into the appropriate controller entry path.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `main()` with `os.sys.argv=['main.py', 'run', '--prompt', 'Compute force from mass=3 and acceleration=4.', '--llm', 'off']`
        Output: 0

    Args:
        None.

    Returns:
        int: Result produced by `main`.
    """
    args = parse_args()
    with sqlite_override_scope(
        args,
        temporary_when_missing=(args.command == "convert-markdown-to-yaml"),
    ):
        if args.command == "run":
            if getattr(args, "prolog_query_priming", None):
                os.environ[PROLOG_QUERY_PRIMING_MODE_ENV] = str(args.prolog_query_priming).strip()
            state = SystemState.bootstrap(args.prompt)
            apply_controller_feature_toggle_overrides(state, args)
            if args.evidence_file:
                attach_evidence_specs(state, load_evidence_specs(args.evidence_file))
            controller = build_controller(state=state, llm_policy=args.llm)
            controller.run(max_steps=args.max_steps)
            if args.state_out:
                save_state(state, args.state_out)
            print(json.dumps(state.summary(), indent=2, sort_keys=True))
            return 0

        if args.command == "resume":
            if getattr(args, "prolog_query_priming", None):
                os.environ[PROLOG_QUERY_PRIMING_MODE_ENV] = str(args.prolog_query_priming).strip()
            state = load_state(args.state_in)
            apply_controller_feature_toggle_overrides(state, args)
            if args.evidence_file:
                attach_evidence_specs(state, load_evidence_specs(args.evidence_file))
            controller = build_controller(state=state, llm_policy=args.llm)
            controller.resume(max_steps=args.max_steps)
            if args.state_out:
                save_state(state, args.state_out)
            print(json.dumps(state.summary(), indent=2, sort_keys=True))
            return 0

        if args.command == "inspect":
            state = load_state(args.state)
            print(json.dumps(state.summary(), indent=2, sort_keys=True))
            return 0

        if args.command == "markdown-learn":
            markdown_path = Path(args.markdown_file)
            state = SystemState.bootstrap(
                f"Learn from markdown: {markdown_path.name}",
                bootstrap_mode="markdown_ingestion",
            )
            apply_controller_feature_toggle_overrides(state, args)
            controller = build_controller(state=state, llm_policy=args.llm)
            report = controller.learn_from_markdown_document(markdown_path, max_artifacts=args.max_artifacts)
            if args.state_out:
                save_state(state, args.state_out)
            if args.report_out:
                args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True))
            print(json.dumps(report, indent=2, sort_keys=True))
            return 0

        if args.command == "convert-markdown-to-yaml":
            return handle_convert_markdown_to_yaml_command(args)

        if args.command == "artifact-export":
            return handle_artifact_export_command(args)

        if args.command == "artifact-import":
            return handle_artifact_import_command(args)

        if args.command == "export-skill":
            return handle_export_skill_command(args)

        if args.command == "export-skill-registry":
            return handle_export_skill_registry_command(args)

        if args.command == "import-skill":
            return handle_import_skill_command(args)

        if args.command == "export-run-bundle":
            return handle_export_run_bundle_command(args)

        if args.command == "replay-run-bundle":
            return handle_replay_run_bundle_command(args)

        if args.command == "load-yaml-and-run":
            return handle_load_yaml_and_run_command(args)

        if args.command == "workstation-launch":
            return handle_workstation_launch_command(args)

        if args.command == "workstation-prompt":
            return handle_workstation_prompt_command(args)

        if args.command == "workstation-chat":
            return handle_workstation_chat_command(args)

        if args.command == "workstation-grpc-host":
            return handle_workstation_grpc_host_command(args)

        if args.command == "workstation-skill-catalog":
            return handle_workstation_skill_catalog_command(args)

        if args.command == "workstation-skill-import":
            return handle_workstation_skill_import_command(args)

        if args.command == "workstation-skill-export":
            return handle_workstation_skill_export_command(args)

        if args.command == "workstation-trial-validate":
            return handle_workstation_trial_validate_command(args)

        if args.command == "validation-ladder":
            return handle_validation_ladder_command(args)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
