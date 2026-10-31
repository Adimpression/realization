"""Historical aggregate CLI parser owned by the entry composition surface."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from realized_core_engine.configuration import (
    STATE_SQLITE_PATH_ENV,
    add_controller_feature_toggle_arguments,
    add_prolog_query_priming_argument,
    add_sqlite_path_argument,
    add_supported_executor_arguments,
    apply_controller_feature_toggle_overrides,
    apply_sqlite_path_override,
)
from workstation.app.cli.arguments import add_workstation_subcommands


_COMMANDS = {
    "run",
    "resume",
    "inspect",
    "artifact-export",
    "artifact-import",
    "export-skill",
    "export-skill-registry",
    "import-skill",
    "export-run-bundle",
    "replay-run-bundle",
    "markdown-learn",
    "convert-markdown-to-yaml",
    "load-yaml-and-run",
    "workstation-launch",
    "workstation-prompt",
    "workstation-chat",
    "workstation-grpc-host",
    "workstation-skill-catalog",
    "workstation-skill-import",
    "workstation-skill-export",
    "workstation-trial-validate",
    "validation-ladder",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the historical all-in-one command surface without owning behavior."""

    normalized_argv = list(argv if argv is not None else os.sys.argv[1:])
    if (
        normalized_argv
        and normalized_argv[0] not in _COMMANDS
        and not normalized_argv[0].startswith("-")
    ):
        normalized_argv = ["run", "--prompt", normalized_argv[0], *normalized_argv[1:]]

    parser = argparse.ArgumentParser(
        description=(
            "Self-contained theoretical implementation of THEORY.md as a "
            "BSSC-governed Not-centric controller."
        ),
        epilog=(
            "Evidence JSON example: "
            '[{"target":"root","observation":"validated supporting fact",'
            '"source":"human","support_strength":"high","confidence":"high"}]'
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Start a fresh governed run from a prompt."
    )
    run_parser.add_argument(
        "--prompt", required=True, help="High-level prompt to represent as Not<X>."
    )
    run_parser.add_argument(
        "--evidence-file", type=Path, help="Optional JSON file with evidence items."
    )
    run_parser.add_argument(
        "--state-out", type=Path, help="Optional path to write durable state JSON."
    )
    run_parser.add_argument(
        "--max-steps",
        type=int,
        default=256,
        help="Maximum controller steps for the bounded run.",
    )
    run_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider configuration comes from the environment.",
    )
    add_controller_feature_toggle_arguments(run_parser)
    add_prolog_query_priming_argument(run_parser)
    add_supported_executor_arguments(run_parser)
    add_sqlite_path_argument(run_parser)

    resume_parser = subparsers.add_parser(
        "resume", help="Resume from a previously saved durable state."
    )
    resume_parser.add_argument(
        "--state-in",
        type=Path,
        required=True,
        help="Path to a saved durable state JSON file.",
    )
    resume_parser.add_argument(
        "--evidence-file",
        type=Path,
        help="Optional JSON file with additional evidence items.",
    )
    resume_parser.add_argument(
        "--state-out", type=Path, help="Optional path to write updated state JSON."
    )
    resume_parser.add_argument(
        "--max-steps",
        type=int,
        default=256,
        help="Maximum controller steps for the resumed run.",
    )
    resume_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider configuration comes from the environment.",
    )
    add_controller_feature_toggle_arguments(resume_parser)
    add_prolog_query_priming_argument(resume_parser)
    add_supported_executor_arguments(resume_parser)
    add_sqlite_path_argument(resume_parser)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect a saved durable state."
    )
    inspect_parser.add_argument(
        "--state",
        type=Path,
        required=True,
        help="Path to a saved durable state JSON file.",
    )

    markdown_learn_parser = subparsers.add_parser(
        "markdown-learn", help="Learn reusable artifacts from a markdown document."
    )
    _add_markdown_arguments(markdown_learn_parser, include_output=False)

    markdown_convert_parser = subparsers.add_parser(
        "convert-markdown-to-yaml",
        help=(
            "Learn artifacts from markdown and export YAML without requiring a "
            "persistent target store."
        ),
    )
    _add_markdown_arguments(markdown_convert_parser, include_output=True)

    artifact_export_parser = subparsers.add_parser(
        "artifact-export", help="Export stored artifacts as human-readable YAML."
    )
    artifact_export_parser.add_argument(
        "--artifact-id", help="Serialized artifact identifier to export."
    )
    artifact_export_parser.add_argument(
        "--artifact-ids-file",
        type=Path,
        help="Optional JSON or newline file containing artifact ids.",
    )
    artifact_export_parser.add_argument(
        "--all", action="store_true", help="Export all stored artifacts."
    )
    artifact_export_parser.add_argument(
        "--out", type=Path, help="Optional YAML output path."
    )
    artifact_export_parser.add_argument(
        "--out-dir", type=Path, help="Directory for batch YAML exports."
    )
    add_sqlite_path_argument(artifact_export_parser)

    artifact_import_parser = subparsers.add_parser(
        "artifact-import", help="Import artifact YAML into the configured store."
    )
    _add_import_file_arguments(artifact_import_parser, noun="artifact")
    add_sqlite_path_argument(artifact_import_parser)

    skill_export_parser = subparsers.add_parser(
        "export-skill", help="Export stored artifacts as compact skill YAML."
    )
    skill_export_parser.add_argument(
        "--skill-title", help="Immutable skill title to export."
    )
    skill_export_parser.add_argument(
        "--skill-titles-file",
        type=Path,
        help="Optional JSON or newline file containing skill titles.",
    )
    skill_export_parser.add_argument(
        "--all", action="store_true", help="Export all stored skills."
    )
    skill_export_parser.add_argument(
        "--out", type=Path, help="Optional skill YAML output path."
    )
    skill_export_parser.add_argument(
        "--out-dir", type=Path, help="Directory for batch skill YAML exports."
    )
    add_sqlite_path_argument(skill_export_parser)

    skill_registry_export_parser = subparsers.add_parser(
        "export-skill-registry",
        help="Export a local governed registry index for all stored skills.",
    )
    skill_registry_export_parser.add_argument(
        "--out", type=Path, help="Optional registry YAML output path."
    )
    add_sqlite_path_argument(skill_registry_export_parser)

    skill_import_parser = subparsers.add_parser(
        "import-skill", help="Import compact skill YAML into the configured store."
    )
    _add_import_file_arguments(skill_import_parser, noun="skill")
    add_sqlite_path_argument(skill_import_parser)

    run_bundle_export_parser = subparsers.add_parser(
        "export-run-bundle",
        help="Export a saved governed state as a replayable run bundle.",
    )
    run_bundle_export_parser.add_argument(
        "--state", type=Path, required=True, help="Durable state JSON to export."
    )
    run_bundle_export_parser.add_argument(
        "--out", type=Path, help="Optional run-bundle YAML output path."
    )
    run_bundle_export_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default="off",
        help="Recorded LLM policy metadata for the replay bundle.",
    )
    run_bundle_export_parser.add_argument(
        "--max-steps",
        type=int,
        default=256,
        help="Recorded max-steps metadata for the replay bundle.",
    )
    add_sqlite_path_argument(run_bundle_export_parser)

    run_bundle_replay_parser = subparsers.add_parser(
        "replay-run-bundle", help="Replay a previously exported run bundle."
    )
    run_bundle_replay_parser.add_argument(
        "--bundle-file", type=Path, required=True, help="Run-bundle YAML path."
    )
    run_bundle_replay_parser.add_argument(
        "--state-out", type=Path, help="Optional durable replay state path."
    )
    run_bundle_replay_parser.add_argument(
        "--report-out", type=Path, help="Optional replay verification report."
    )
    run_bundle_replay_parser.add_argument(
        "--max-steps", type=int, help="Optional replay max-steps override."
    )
    run_bundle_replay_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        help="Optional replay LLM policy override.",
    )
    add_sqlite_path_argument(run_bundle_replay_parser)

    load_yaml_and_run_parser = subparsers.add_parser(
        "load-yaml-and-run",
        help="Import artifact YAML and run a prompt against that store.",
    )
    load_yaml_and_run_parser.add_argument(
        "--artifact-file",
        type=Path,
        action="append",
        help="Artifact YAML path. Repeat for batch import.",
    )
    load_yaml_and_run_parser.add_argument(
        "--artifact-files-file",
        type=Path,
        help="Optional JSON or newline file containing artifact YAML paths.",
    )
    load_yaml_and_run_parser.add_argument(
        "--artifact-dir", type=Path, help="Directory containing artifact YAML files."
    )
    load_yaml_and_run_parser.add_argument(
        "--prompt", required=True, help="High-level prompt to run after import."
    )
    load_yaml_and_run_parser.add_argument(
        "--evidence-file", type=Path, help="Optional JSON evidence file."
    )
    load_yaml_and_run_parser.add_argument(
        "--state-out", type=Path, help="Optional durable state output path."
    )
    load_yaml_and_run_parser.add_argument(
        "--max-steps", type=int, default=256, help="Maximum controller steps."
    )
    load_yaml_and_run_parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy. Provider configuration comes from the environment.",
    )
    add_controller_feature_toggle_arguments(load_yaml_and_run_parser)
    add_prolog_query_priming_argument(load_yaml_and_run_parser)
    add_supported_executor_arguments(load_yaml_and_run_parser)
    add_sqlite_path_argument(load_yaml_and_run_parser)

    add_workstation_subcommands(subparsers, command_prefix="workstation-")

    validation_ladder_parser = subparsers.add_parser(
        "validation-ladder",
        help="Run unit, workstation-trial, and chemistry validation layers.",
    )
    validation_ladder_parser.add_argument(
        "--workspace", type=Path, help="Optional workstation-trial workspace."
    )
    validation_ladder_parser.add_argument(
        "--report-root", type=Path, help="Optional validation report root."
    )
    validation_ladder_parser.add_argument(
        "--model", help="Optional model override for the workstation trial layer."
    )
    validation_ladder_parser.add_argument(
        "--report-out", type=Path, help="Optional top-level report path."
    )

    return parser.parse_args(normalized_argv)


def _add_markdown_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_output: bool,
) -> None:
    parser.add_argument(
        "--markdown-file", type=Path, required=True, help="Markdown document path."
    )
    if include_output:
        parser.add_argument("--out", type=Path, help="Optional YAML output path.")
    parser.add_argument(
        "--state-out", type=Path, help="Optional durable state JSON path."
    )
    parser.add_argument(
        "--report-out", type=Path, help="Optional markdown-learning report path."
    )
    parser.add_argument(
        "--max-artifacts",
        type=int,
        default=8,
        help="Maximum number of learned artifacts to extract.",
    )
    parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy for markdown artifact extraction.",
    )
    add_controller_feature_toggle_arguments(parser)
    add_supported_executor_arguments(parser)
    add_sqlite_path_argument(parser)


def _add_import_file_arguments(
    parser: argparse.ArgumentParser,
    *,
    noun: str,
) -> None:
    parser.add_argument(
        f"--{noun}-file",
        type=Path,
        action="append",
        help=f"{noun.title()} YAML path. Repeat for batch import.",
    )
    parser.add_argument(
        f"--{noun}-files-file",
        type=Path,
        help=f"Optional JSON or newline file containing {noun} YAML paths.",
    )
    parser.add_argument(
        f"--{noun}-dir",
        type=Path,
        help=f"Optional directory containing {noun} YAML files.",
    )
    parser.add_argument(
        "--normalized-out", type=Path, help="Optional normalized YAML output path."
    )
    parser.add_argument(
        "--normalized-out-dir",
        type=Path,
        help="Optional directory for normalized batch YAML outputs.",
    )


__all__ = [
    "STATE_SQLITE_PATH_ENV",
    "add_controller_feature_toggle_arguments",
    "add_prolog_query_priming_argument",
    "add_sqlite_path_argument",
    "add_supported_executor_arguments",
    "apply_controller_feature_toggle_overrides",
    "apply_sqlite_path_override",
    "parse_args",
]
