# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from execution_frameworks import (
    SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES,
    SUPPORTED_EXECUTOR_FRAMEWORKS_ENV,
    normalize_supported_executor_frameworks,
)
from normalize import normalize_controller_feature_toggle_enabled

STATE_SQLITE_PATH_ENV = "STATE_SQLITE_PATH"


def add_controller_feature_toggle_arguments(parser: argparse.ArgumentParser) -> None:
    """
    High Level Purpose:
        In circumstances like CLI setup and controller runtime configuration, helps with handling add controller feature toggle arguments.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `add_controller_feature_toggle_arguments(parser=3)`
        Output: None

    Args:
        parser: Value for `parser` used by `add_controller_feature_toggle_arguments`. Expected type: `argparse.ArgumentParser`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    parser.add_argument(
        "--discovery",
        choices=["on", "off"],
        default=None,
        help="Toggle bounded discovery harvest on or off for this run.",
    )
    parser.add_argument(
        "--reflection",
        choices=["on", "off"],
        default=None,
        help="Toggle retrospective reflection on or off for this run.",
    )
    parser.add_argument(
        "--contemplation",
        choices=["on", "off"],
        default=None,
        help="Toggle prospective contemplation on or off for this run.",
    )


def add_prolog_query_priming_argument(parser: argparse.ArgumentParser) -> None:
    """
    High Level Purpose:
        In circumstances like CLI setup for structural Prolog retrieval experiments, helps with selecting whether LLM-based query priming is disabled, fallback-only, or forced.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `add_prolog_query_priming_argument(parser=ArgumentParser(prog='bssc'))`
        Output: None

    Args:
        parser: Value for `parser` used by `add_prolog_query_priming_argument`. Expected type: `argparse.ArgumentParser`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    parser.add_argument(
        "--prolog-query-priming",
        choices=["off", "fallback", "force"],
        default=os.getenv("BSSC_PROLOG_QUERY_PRIMING", "fallback"),
        help="When Prolog title representation is active, control whether LLM query priming is disabled, used as fallback, or forced.",
    )


def add_supported_executor_arguments(parser: argparse.ArgumentParser) -> None:
    """
    High Level Purpose:
        In circumstances like markdown training and later runtime reuse across multiple external execution surfaces, helps with declaring which executor frameworks the current command is allowed to rely on.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `add_supported_executor_arguments(parser=ArgumentParser(prog='bssc'))`
        Output: None

    Args:
        parser: Value for `parser` used by `add_supported_executor_arguments`. Expected type: `argparse.ArgumentParser`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    parser.add_argument(
        "--supported-executor",
        dest="supported_executors",
        action="append",
        choices=list(SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES),
        default=None,
        help=(
            "Repeat to allow one or more external executor frameworks for this command, "
            "for example --supported-executor python3 --supported-executor bash."
        ),
    )


def add_sqlite_path_argument(parser: argparse.ArgumentParser) -> None:
    """
    High Level Purpose:
        In circumstances like CLI-driven learning, import/export, and runtime reuse against different persistent stores, helps with declaring an explicit SQLite artifact-store path that should override environment defaults for the current command.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `add_sqlite_path_argument(parser=ArgumentParser(prog='bssc'))`
        Output: None

    Args:
        parser: Value for `parser` used by `add_sqlite_path_argument`. Expected type: `argparse.ArgumentParser`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=None,
        help="Override the SQLite artifact-store path for this command. This takes precedence over STATE_SQLITE_PATH.",
    )


def apply_controller_feature_toggle_overrides(state: Any, args: argparse.Namespace) -> None:
    """
    High Level Purpose:
        In circumstances like CLI setup and controller runtime configuration, helps with applying controller feature toggle overrides.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `apply_controller_feature_toggle_overrides(state={'controller_features': {'discovery_enabled': False, 'reflection_enabled': True, 'contemplation_enabled': True}}, args=Namespace(discovery='off', reflection='on', contemplation='on'))`
        Output: None

    Args:
        state: Value for `state` used by `apply_controller_feature_toggle_overrides`. Expected type: `Any`.
        args: Value for `args` used by `apply_controller_feature_toggle_overrides`. Expected type: `argparse.Namespace`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    discovery = getattr(args, "discovery", None)
    reflection = getattr(args, "reflection", None)
    contemplation = getattr(args, "contemplation", None)
    supported_executors = getattr(args, "supported_executors", None)
    if discovery is not None:
        state.controller_features.discovery_enabled = normalize_controller_feature_toggle_enabled(
            discovery,
            default=state.controller_features.discovery_enabled,
        )
    if reflection is not None:
        state.controller_features.reflection_enabled = normalize_controller_feature_toggle_enabled(
            reflection,
            default=state.controller_features.reflection_enabled,
        )
    if contemplation is not None:
        state.controller_features.contemplation_enabled = normalize_controller_feature_toggle_enabled(
            contemplation,
            default=state.controller_features.contemplation_enabled,
        )
    if supported_executors is None:
        env_value = os.getenv(SUPPORTED_EXECUTOR_FRAMEWORKS_ENV)
        if env_value is not None:
            supported_executors = [item for item in env_value.split(",") if item.strip()]
    if supported_executors is not None:
        state.controller_features.supported_executors = normalize_supported_executor_frameworks(
            supported_executors,
            default=state.controller_features.supported_executors,
        )


def apply_sqlite_path_override(args: argparse.Namespace) -> Path | None:
    """
    High Level Purpose:
        In circumstances like CLI commands that need to target a specific persistent artifact store, helps with applying the explicit SQLite-path override before later store construction reads environment state.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `apply_sqlite_path_override(args=Namespace(sqlite=Path('/workspace/realized/state/common.sqlite3')))`
        Output: Path('/workspace/realized/state/common.sqlite3')

    Args:
        args: Value for `args` used by `apply_sqlite_path_override`. Expected type: `argparse.Namespace`.

    Returns:
        Path | None: Result produced by `apply_sqlite_path_override`.
    """
    sqlite_path = getattr(args, "sqlite", None)
    if sqlite_path is None:
        return None
    resolved = Path(sqlite_path).expanduser()
    os.environ[STATE_SQLITE_PATH_ENV] = str(resolved)
    return resolved


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    High Level Purpose:
        In circumstances like CLI setup and controller runtime configuration, helps with parsing args.

    Reference to Theory:
        Exposes CLI/runtime entry points for the theory-backed controller without changing the theory itself.

    Example Input Output:
        Input: `parse_args(argv=['mass', 'acceleration', 'force'])`
        Output: Namespace(discovery='off', reflection='on', contemplation='on')

    Args:
        argv: Value for `argv` used by `parse_args`. Expected type: `list[str] | None`. Defaults to `None`.

    Returns:
        argparse.Namespace: Result produced by `parse_args`.
    """
    normalized_argv = list(argv if argv is not None else os.sys.argv[1:])
    if (
        normalized_argv
        and normalized_argv[0] not in {"run", "resume", "inspect", "artifact-export", "artifact-import", "export-skill", "export-skill-registry", "import-skill", "export-run-bundle", "replay-run-bundle", "markdown-learn", "convert-markdown-to-yaml", "load-yaml-and-run", "workstation-launch", "workstation-prompt", "workstation-chat", "workstation-grpc-host", "workstation-skill-catalog", "workstation-skill-import", "workstation-skill-export", "workstation-trial-validate", "validation-ladder"}
        and not normalized_argv[0].startswith("-")
    ):
        normalized_argv = ["run", "--prompt", normalized_argv[0], *normalized_argv[1:]]

    parser = argparse.ArgumentParser(
        description="Self-contained theoretical implementation of THEORY.md as a BSSC-governed Not-centric controller.",
        epilog=(
            "Evidence JSON example: "
            '[{"target":"root","observation":"validated supporting fact","source":"human","support_strength":"high","confidence":"high"}]'
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Start a fresh governed run from a prompt.")
    run_parser.add_argument("--prompt", required=True, help="High-level prompt to represent as Not<X>.")
    run_parser.add_argument("--evidence-file", type=Path, help="Optional JSON file with evidence items.")
    run_parser.add_argument("--state-out", type=Path, help="Optional path to write durable state JSON.")
    run_parser.add_argument("--max-steps", type=int, default=256, help="Maximum controller steps for the bounded run.")
    run_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider and model configuration come from environment variables.",
    )
    add_controller_feature_toggle_arguments(run_parser)
    add_prolog_query_priming_argument(run_parser)
    add_supported_executor_arguments(run_parser)
    add_sqlite_path_argument(run_parser)

    resume_parser = subparsers.add_parser("resume", help="Resume from a previously saved durable state.")
    resume_parser.add_argument("--state-in", type=Path, required=True, help="Path to a saved durable state JSON file.")
    resume_parser.add_argument("--evidence-file", type=Path, help="Optional JSON file with additional evidence items.")
    resume_parser.add_argument("--state-out", type=Path, help="Optional path to write updated durable state JSON.")
    resume_parser.add_argument("--max-steps", type=int, default=256, help="Maximum controller steps for the resumed run.")
    resume_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider and model configuration come from environment variables.",
    )
    add_controller_feature_toggle_arguments(resume_parser)
    add_prolog_query_priming_argument(resume_parser)
    add_supported_executor_arguments(resume_parser)
    add_sqlite_path_argument(resume_parser)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a saved durable state.")
    inspect_parser.add_argument("--state", type=Path, required=True, help="Path to a saved durable state JSON file.")

    markdown_learn_parser = subparsers.add_parser("markdown-learn", help="Learn reusable artifacts from a markdown document.")
    markdown_learn_parser.add_argument("--markdown-file", type=Path, required=True, help="Path to the markdown document to ingest.")
    markdown_learn_parser.add_argument("--state-out", type=Path, help="Optional path to write durable controller state JSON.")
    markdown_learn_parser.add_argument("--report-out", type=Path, help="Optional path to write the markdown-learning report JSON.")
    markdown_learn_parser.add_argument("--max-artifacts", type=int, default=8, help="Maximum number of learned artifacts to extract from the markdown document.")
    markdown_learn_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy for markdown artifact extraction.",
    )
    add_controller_feature_toggle_arguments(markdown_learn_parser)
    add_supported_executor_arguments(markdown_learn_parser)
    add_sqlite_path_argument(markdown_learn_parser)

    markdown_convert_parser = subparsers.add_parser("convert-markdown-to-yaml", help="Learn artifacts from a markdown document and export them as YAML without requiring a persistent target store.")
    markdown_convert_parser.add_argument("--markdown-file", type=Path, required=True, help="Path to the markdown document to ingest.")
    markdown_convert_parser.add_argument("--out", type=Path, help="Optional path to write the YAML artifact bundle. Prints to stdout when omitted.")
    markdown_convert_parser.add_argument("--state-out", type=Path, help="Optional path to write durable controller state JSON.")
    markdown_convert_parser.add_argument("--report-out", type=Path, help="Optional path to write the markdown-learning report JSON.")
    markdown_convert_parser.add_argument("--max-artifacts", type=int, default=8, help="Maximum number of learned artifacts to extract from the markdown document.")
    markdown_convert_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy for markdown artifact extraction.",
    )
    add_controller_feature_toggle_arguments(markdown_convert_parser)
    add_supported_executor_arguments(markdown_convert_parser)
    add_sqlite_path_argument(markdown_convert_parser)

    artifact_export_parser = subparsers.add_parser("artifact-export", help="Export a stored artifact as human-readable YAML.")
    artifact_export_parser.add_argument("--artifact-id", help="Serialized artifact identifier to export from the configured artifact store (hydrates to Artifact.id in memory).")
    artifact_export_parser.add_argument("--artifact-ids-file", type=Path, help="Optional JSON or newline file containing serialized artifact ids for batch export.")
    artifact_export_parser.add_argument("--all", action="store_true", help="Export all stored artifacts.")
    artifact_export_parser.add_argument("--out", type=Path, help="Optional path to write the YAML export. For batch export this writes a multi-document YAML bundle.")
    artifact_export_parser.add_argument("--out-dir", type=Path, help="Directory for batch YAML exports. Required for --all or --artifact-ids-file.")
    add_sqlite_path_argument(artifact_export_parser)

    artifact_import_parser = subparsers.add_parser("artifact-import", help="Import an artifact YAML file into the configured artifact store.")
    artifact_import_parser.add_argument("--artifact-file", type=Path, action="append", help="Path to an artifact YAML file. Repeat for batch import.")
    artifact_import_parser.add_argument("--artifact-files-file", type=Path, help="Optional JSON or newline file containing artifact YAML paths for batch import.")
    artifact_import_parser.add_argument("--artifact-dir", type=Path, help="Optional directory containing artifact YAML files for batch import.")
    artifact_import_parser.add_argument("--normalized-out", type=Path, help="Optional path to write the normalized YAML export after single import.")
    artifact_import_parser.add_argument("--normalized-out-dir", type=Path, help="Optional directory to write normalized YAML exports for batch import.")
    add_sqlite_path_argument(artifact_import_parser)

    skill_export_parser = subparsers.add_parser("export-skill", help="Export a stored artifact as the compact skill YAML interface.")
    skill_export_parser.add_argument("--skill-title", help="Immutable skill title to export from the configured artifact store.")
    skill_export_parser.add_argument("--skill-titles-file", type=Path, help="Optional JSON or newline file containing skill titles for batch export.")
    skill_export_parser.add_argument("--all", action="store_true", help="Export all stored skills.")
    skill_export_parser.add_argument("--out", type=Path, help="Optional path to write the skill YAML export. For batch export this writes a multi-document YAML bundle.")
    skill_export_parser.add_argument("--out-dir", type=Path, help="Directory for batch skill YAML exports. Required for --all or --skill-titles-file.")
    add_sqlite_path_argument(skill_export_parser)

    skill_registry_export_parser = subparsers.add_parser("export-skill-registry", help="Export a local governed registry index for all stored skills.")
    skill_registry_export_parser.add_argument("--out", type=Path, help="Optional path to write the registry YAML. Prints to stdout when omitted.")
    add_sqlite_path_argument(skill_registry_export_parser)

    skill_import_parser = subparsers.add_parser("import-skill", help="Import compact skill YAML into the configured artifact store.")
    skill_import_parser.add_argument("--skill-file", type=Path, action="append", help="Path to a skill YAML file. Repeat for batch import.")
    skill_import_parser.add_argument("--skill-files-file", type=Path, help="Optional JSON or newline file containing skill YAML paths for batch import.")
    skill_import_parser.add_argument("--skill-dir", type=Path, help="Optional directory containing skill YAML files for batch import.")
    skill_import_parser.add_argument("--normalized-out", type=Path, help="Optional path to write the normalized skill YAML export after single import.")
    skill_import_parser.add_argument("--normalized-out-dir", type=Path, help="Optional directory to write normalized skill YAML exports for batch import.")
    add_sqlite_path_argument(skill_import_parser)

    run_bundle_export_parser = subparsers.add_parser("export-run-bundle", help="Export a saved governed run state as a replayable run bundle.")
    run_bundle_export_parser.add_argument("--state", type=Path, required=True, help="Path to the durable state JSON to export.")
    run_bundle_export_parser.add_argument("--out", type=Path, help="Optional path to write the run bundle YAML. Prints to stdout when omitted.")
    run_bundle_export_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default="off",
        help="Recorded LLM policy metadata for the replay bundle.",
    )
    run_bundle_export_parser.add_argument("--max-steps", type=int, default=256, help="Recorded max-steps metadata for the replay bundle.")
    add_sqlite_path_argument(run_bundle_export_parser)

    run_bundle_replay_parser = subparsers.add_parser("replay-run-bundle", help="Replay a previously exported governed run bundle into a fresh or selected SQLite store.")
    run_bundle_replay_parser.add_argument("--bundle-file", type=Path, required=True, help="Path to the run bundle YAML file.")
    run_bundle_replay_parser.add_argument("--state-out", type=Path, help="Optional path to write durable replay state JSON.")
    run_bundle_replay_parser.add_argument("--report-out", type=Path, help="Optional path to write replay verification JSON.")
    run_bundle_replay_parser.add_argument("--max-steps", type=int, help="Optional replay max-steps override.")
    run_bundle_replay_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        help="Optional replay LLM policy override.",
    )
    add_sqlite_path_argument(run_bundle_replay_parser)

    load_yaml_and_run_parser = subparsers.add_parser("load-yaml-and-run", help="Import artifact YAML into the configured store and then run a prompt against that store.")
    load_yaml_and_run_parser.add_argument("--artifact-file", type=Path, action="append", help="Path to an artifact YAML file. Repeat for batch import.")
    load_yaml_and_run_parser.add_argument("--artifact-files-file", type=Path, help="Optional JSON or newline file containing artifact YAML paths for batch import.")
    load_yaml_and_run_parser.add_argument("--artifact-dir", type=Path, help="Optional directory containing artifact YAML files for batch import.")
    load_yaml_and_run_parser.add_argument("--prompt", required=True, help="High-level prompt to run after the YAML artifacts are loaded.")
    load_yaml_and_run_parser.add_argument("--evidence-file", type=Path, help="Optional JSON file with evidence items.")
    load_yaml_and_run_parser.add_argument("--state-out", type=Path, help="Optional path to write durable state JSON.")
    load_yaml_and_run_parser.add_argument("--max-steps", type=int, default=256, help="Maximum controller steps for the bounded run.")
    load_yaml_and_run_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider and model configuration come from environment variables.",
    )
    add_controller_feature_toggle_arguments(load_yaml_and_run_parser)
    add_prolog_query_priming_argument(load_yaml_and_run_parser)
    add_supported_executor_arguments(load_yaml_and_run_parser)
    add_sqlite_path_argument(load_yaml_and_run_parser)

    workstation_launch_parser = subparsers.add_parser("workstation-launch", help="Create one workstation session root against one attached workspace.")
    workstation_launch_parser.add_argument("--root", type=Path, required=True, help="Path where the workstation session root should be created.")
    workstation_launch_parser.add_argument("--workspace", type=Path, required=True, help="Host workspace path to attach as the main workstation attachment.")
    workstation_launch_parser.add_argument("--skills-sqlite", type=Path, help="Optional SQLite skill store to attach for workstation skill invocation.")
    workstation_launch_parser.add_argument("--workspace-name", default="main", help="Attachment name for the primary workspace. Defaults to 'main'.")
    workstation_launch_parser.add_argument("--task", default="", help="Optional initial task text to write into TASK.md.")
    workstation_launch_parser.add_argument("--capability", action="append", default=None, help="Repeat to allow one or more workstation capabilities. Defaults to the workstation default shell capability set.")
    workstation_launch_parser.add_argument("--openai-env-var", default="OPENAI_API_KEY", help="Environment variable name that should be treated as the indirect OpenAI secret reference.")
    workstation_launch_parser.add_argument("--openai-profile", default="openai_default", help="Named OpenAI profile label exposed inside the workstation manifest.")
    workstation_launch_parser.add_argument(
        "--allow-direct-llm-decomposition",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Allow bounded direct LLM decomposition during Itemize for weakly structured prose sources. Defaults to enabled.",
    )

    workstation_prompt_parser = subparsers.add_parser("workstation-prompt", help="Send one prompt through an existing workstation session.")
    workstation_prompt_parser.add_argument("--root", type=Path, required=True, help="Path to the workstation session root.")
    workstation_prompt_parser.add_argument("--prompt", required=True, help="Natural-language prompt to send through the workstation session.")
    workstation_prompt_parser.add_argument("--model", help="Optional explicit OpenAI-compatible model override for this turn.")
    workstation_prompt_parser.add_argument("--max-tool-rounds", type=int, default=8, help="Maximum OpenAI tool rounds for this workstation turn.")
    workstation_prompt_parser.add_argument(
        "--mode",
        choices=[
            "normal",
            "llm_only",
            "governed_reduction",
            "governed_conversation",
        ],
        default="normal",
        help=(
            "Explicit turn route. Governed reduction and governed conversation "
            "are opt-in and never replace normal chat."
        ),
    )
    workstation_prompt_parser.add_argument(
        "--governed-treatment",
        choices=["independent", "human_contribution", "follow_up", "correction"],
        default="independent",
        help="How an explicitly governed turn relates to any selected prior run.",
    )
    workstation_prompt_parser.add_argument("--governed-parent-run-id", default="", help="Prior governed run selected for continuation, follow-up, or correction.")
    workstation_prompt_parser.add_argument("--governed-llm", choices=["off", "auto", "required"], default="auto", help="LLM supplement policy for an explicitly governed turn.")
    workstation_prompt_parser.add_argument("--governed-max-steps", type=int, default=256, help="Maximum bounded reduction steps for an explicitly governed turn.")
    workstation_prompt_parser.add_argument("--report-out", type=Path, help="Optional path to write the workstation turn report JSON.")

    workstation_chat_parser = subparsers.add_parser("workstation-chat", help="Start an interactive host-owned chat loop against an existing workstation session.")
    workstation_chat_parser.add_argument("--root", type=Path, required=True, help="Path to the workstation session root.")
    workstation_chat_parser.add_argument("--model", help="Optional explicit OpenAI-compatible model override for this chat session.")
    workstation_chat_parser.add_argument("--max-tool-rounds", type=int, default=8, help="Maximum OpenAI tool rounds for each workstation chat turn.")

    workstation_grpc_host_parser = subparsers.add_parser("workstation-grpc-host", help="Start the combined workstation gRPC host with bootstrap and asset download support.")
    workstation_grpc_host_parser.add_argument("--serve-root", type=Path, action="append", required=True, help="Repeat to advertise one or more workstation roots from this host.")
    workstation_grpc_host_parser.add_argument("--default-root", default="", help="Optional default served root id or absolute path. Defaults to the first --serve-root.")
    workstation_grpc_host_parser.add_argument("--host", default="127.0.0.1", help="TCP host interface for the gRPC server. Defaults to 127.0.0.1.")
    workstation_grpc_host_parser.add_argument("--port", type=int, default=50051, help="TCP port for the gRPC server. Use 0 for an ephemeral port.")
    workstation_grpc_host_parser.add_argument("--asset-host", default="127.0.0.1", help="TCP host interface for the companion artifact HTTP server. Defaults to 127.0.0.1.")
    workstation_grpc_host_parser.add_argument("--asset-port", type=int, default=8787, help="TCP port for the companion artifact HTTP server. Use 0 for an ephemeral port.")
    workstation_grpc_host_parser.add_argument("--asset-base-url", default="", help="Optional public base URL to publish inside artifact download references. Defaults to the local artifact HTTP bind URL.")
    workstation_grpc_host_parser.add_argument(
        "--allow-local-path-open",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether artifact refs may advertise direct local opening when the path exists on the host. Defaults to enabled.",
    )

    workstation_skill_catalog_parser = subparsers.add_parser("workstation-skill-catalog", help="Return the persistent workstation skill catalog for one workstation session.")
    workstation_skill_catalog_parser.add_argument("--root", type=Path, required=True, help="Path to the workstation session root.")
    workstation_skill_catalog_parser.add_argument("--query", default="", help="Optional short query used to filter the workstation skill catalog.")
    workstation_skill_catalog_parser.add_argument("--limit", type=int, help="Optional maximum number of catalog entries to return after filtering.")
    workstation_skill_catalog_parser.add_argument("--report-out", type=Path, help="Optional path to write the catalog JSON report.")

    workstation_skill_import_parser = subparsers.add_parser("workstation-skill-import", help="Import one portable skill bundle into the persistent workstation skill home for one workstation session.")
    workstation_skill_import_parser.add_argument("--root", type=Path, required=True, help="Path to the workstation session root.")
    workstation_skill_import_parser.add_argument("--skill-file", type=Path, required=True, help="Host path to one portable skill.yaml file.")
    workstation_skill_import_parser.add_argument("--report-out", type=Path, help="Optional path to write the import JSON report.")

    workstation_skill_export_parser = subparsers.add_parser("workstation-skill-export", help="Export one governed skill from the persistent workstation skill home for one workstation session.")
    workstation_skill_export_parser.add_argument("--root", type=Path, required=True, help="Path to the workstation session root.")
    workstation_skill_export_parser.add_argument("--skill-title", required=True, help="Title of the governed skill to export.")
    workstation_skill_export_parser.add_argument("--out", type=Path, help="Optional host path to copy the exported skill bundle to after canonical export.")
    workstation_skill_export_parser.add_argument("--report-out", type=Path, help="Optional path to write the export JSON report.")

    workstation_trial_validate_parser = subparsers.add_parser("workstation-trial-validate", help="Audit workstation compatibility against one or more trial domains.")
    workstation_trial_validate_parser.add_argument("--domains", action="append", help="Repeat to validate one or more specific trial domains. Defaults to all discovered domains.")
    workstation_trial_validate_parser.add_argument("--workspace", type=Path, help="Optional workspace path to attach for each workstation trial session. Defaults to the repository root.")
    workstation_trial_validate_parser.add_argument("--report-root", type=Path, help="Optional directory to use as the workstation trial validation report root.")
    workstation_trial_validate_parser.add_argument("--model", help="Optional explicit OpenAI-compatible model override for workstation trial prompts.")
    workstation_trial_validate_parser.add_argument("--max-tool-rounds", type=int, default=8, help="Maximum OpenAI tool rounds per workstation trial prompt.")
    workstation_trial_validate_parser.add_argument("--report-out", type=Path, help="Optional path to write the top-level workstation trial validation JSON report.")

    validation_ladder_parser = subparsers.add_parser("validation-ladder", help="Run the layered acceptance ladder: unit suite, workstation trial sweep, then chemistry domain validation.")
    validation_ladder_parser.add_argument("--workspace", type=Path, help="Optional workspace path to use for the workstation trial layer. Defaults to the repository root.")
    validation_ladder_parser.add_argument("--report-root", type=Path, help="Optional directory to use as the validation ladder report root.")
    validation_ladder_parser.add_argument("--model", help="Optional explicit model override for the workstation trial layer.")
    validation_ladder_parser.add_argument("--report-out", type=Path, help="Optional path to write the top-level validation ladder JSON report.")

    return parser.parse_args(normalized_argv)
