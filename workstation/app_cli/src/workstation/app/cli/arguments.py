"""Argument construction for the installable workstation entry surface."""

from __future__ import annotations

import argparse
from pathlib import Path


WORKSTATION_ACTIONS = (
    "launch",
    "prompt",
    "chat",
    "grpc-host",
    "skill-catalog",
    "skill-import",
    "skill-export",
    "trial-validate",
)


def add_workstation_subcommands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    command_prefix: str = "",
    include_legacy_aliases: bool = False,
) -> None:
    """Register workstation commands without binding their implementations."""

    def command_parser(action: str, *, help: str) -> argparse.ArgumentParser:
        command = f"{command_prefix}{action}"
        aliases = (
            [f"workstation-{action}"]
            if include_legacy_aliases and not command_prefix
            else []
        )
        parser = subparsers.add_parser(command, aliases=aliases, help=help)
        parser.set_defaults(workstation_action=action)
        return parser

    launch = command_parser(
        "launch",
        help="Create one workstation session root against one attached workspace.",
    )
    launch.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path where the workstation session root should be created.",
    )
    launch.add_argument(
        "--workspace",
        type=Path,
        required=True,
        help="Host workspace path to attach as the main workstation attachment.",
    )
    launch.add_argument(
        "--skills-sqlite",
        type=Path,
        help="Optional SQLite skill store to attach for workstation skill invocation.",
    )
    launch.add_argument(
        "--workspace-name",
        default="main",
        help="Attachment name for the primary workspace. Defaults to 'main'.",
    )
    launch.add_argument(
        "--task",
        default="",
        help="Optional initial task text to write into TASK.md.",
    )
    launch.add_argument(
        "--capability",
        action="append",
        default=None,
        help=(
            "Repeat to allow one or more workstation capabilities. Defaults to "
            "the workstation default shell capability set."
        ),
    )
    launch.add_argument(
        "--openai-env-var",
        default="OPENAI_API_KEY",
        help=(
            "Environment variable name that should be treated as the indirect "
            "OpenAI secret reference."
        ),
    )
    launch.add_argument(
        "--openai-profile",
        default="openai_default",
        help="Named OpenAI profile label exposed inside the workstation manifest.",
    )
    launch.add_argument(
        "--allow-direct-llm-decomposition",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Allow bounded direct LLM decomposition during Itemize for weakly "
            "structured prose sources. Defaults to enabled."
        ),
    )

    prompt = command_parser(
        "prompt",
        help="Send one prompt through an existing workstation session.",
    )
    prompt.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path to the workstation session root.",
    )
    prompt.add_argument(
        "--prompt",
        required=True,
        help="Natural-language prompt to send through the workstation session.",
    )
    prompt.add_argument(
        "--model",
        help="Optional explicit OpenAI-compatible model override for this turn.",
    )
    prompt.add_argument(
        "--max-tool-rounds",
        type=int,
        default=8,
        help="Maximum OpenAI tool rounds for this workstation turn.",
    )
    prompt.add_argument(
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
    prompt.add_argument(
        "--governed-treatment",
        choices=["independent", "human_contribution", "follow_up", "correction"],
        default="independent",
        help="How an explicitly governed turn relates to any selected prior run.",
    )
    prompt.add_argument(
        "--governed-parent-run-id",
        default="",
        help=(
            "Prior governed run selected for continuation, follow-up, or "
            "correction."
        ),
    )
    prompt.add_argument(
        "--governed-llm",
        choices=["off", "auto", "required"],
        default="auto",
        help="LLM supplement policy for an explicitly governed turn.",
    )
    prompt.add_argument(
        "--governed-max-steps",
        type=int,
        default=256,
        help="Maximum bounded reduction steps for an explicitly governed turn.",
    )
    prompt.add_argument(
        "--report-out",
        type=Path,
        help="Optional path to write the workstation turn report JSON.",
    )

    chat = command_parser(
        "chat",
        help="Start an interactive host-owned chat loop against a session.",
    )
    chat.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path to the workstation session root.",
    )
    chat.add_argument(
        "--model",
        help="Optional explicit OpenAI-compatible model override for this chat session.",
    )
    chat.add_argument(
        "--max-tool-rounds",
        type=int,
        default=8,
        help="Maximum OpenAI tool rounds for each workstation chat turn.",
    )

    grpc_host = command_parser(
        "grpc-host",
        help="Start the workstation gRPC host and artifact download surface.",
    )
    grpc_host.add_argument(
        "--serve-root",
        type=Path,
        action="append",
        required=True,
        help="Repeat to advertise one or more workstation roots from this host.",
    )
    grpc_host.add_argument(
        "--default-root",
        default="",
        help="Optional default root id or path. Defaults to the first --serve-root.",
    )
    grpc_host.add_argument(
        "--host",
        default="127.0.0.1",
        help="TCP host interface for the gRPC server. Defaults to 127.0.0.1.",
    )
    grpc_host.add_argument(
        "--port",
        type=int,
        default=50051,
        help="TCP port for the gRPC server. Use 0 for an ephemeral port.",
    )
    grpc_host.add_argument(
        "--asset-host",
        default="127.0.0.1",
        help="TCP host for the artifact HTTP server. Defaults to 127.0.0.1.",
    )
    grpc_host.add_argument(
        "--asset-port",
        type=int,
        default=8787,
        help="TCP port for the artifact HTTP server. Use 0 for an ephemeral port.",
    )
    grpc_host.add_argument(
        "--asset-base-url",
        default="",
        help="Optional public base URL for artifact download references.",
    )
    grpc_host.add_argument(
        "--allow-local-path-open",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether artifact refs may advertise direct local opening.",
    )

    skill_catalog = command_parser(
        "skill-catalog",
        help="Return the persistent skill catalog for one workstation session.",
    )
    skill_catalog.add_argument(
        "--root", type=Path, required=True, help="Path to the workstation root."
    )
    skill_catalog.add_argument(
        "--query", default="", help="Optional catalog filter query."
    )
    skill_catalog.add_argument(
        "--limit", type=int, help="Optional maximum number of catalog entries."
    )
    skill_catalog.add_argument(
        "--report-out", type=Path, help="Optional catalog JSON report path."
    )

    skill_import = command_parser(
        "skill-import",
        help="Import one portable skill bundle into a workstation skill home.",
    )
    skill_import.add_argument(
        "--root", type=Path, required=True, help="Path to the workstation root."
    )
    skill_import.add_argument(
        "--skill-file",
        type=Path,
        required=True,
        help="Host path to one portable skill.yaml file.",
    )
    skill_import.add_argument(
        "--report-out", type=Path, help="Optional import JSON report path."
    )

    skill_export = command_parser(
        "skill-export",
        help="Export one governed skill from a workstation skill home.",
    )
    skill_export.add_argument(
        "--root", type=Path, required=True, help="Path to the workstation root."
    )
    skill_export.add_argument(
        "--skill-title", required=True, help="Title of the governed skill to export."
    )
    skill_export.add_argument(
        "--out", type=Path, help="Optional host path for the exported skill bundle."
    )
    skill_export.add_argument(
        "--report-out", type=Path, help="Optional export JSON report path."
    )

    trial_validate = command_parser(
        "trial-validate",
        help="Audit workstation compatibility against trial domains.",
    )
    trial_validate.add_argument(
        "--domains",
        action="append",
        help="Repeat to validate specific domains. Defaults to all domains.",
    )
    trial_validate.add_argument(
        "--workspace",
        type=Path,
        help="Optional workspace attachment. Defaults to the repository root.",
    )
    trial_validate.add_argument(
        "--report-root", type=Path, help="Optional validation report root."
    )
    trial_validate.add_argument(
        "--model", help="Optional model override for workstation trial prompts."
    )
    trial_validate.add_argument(
        "--max-tool-rounds",
        type=int,
        default=8,
        help="Maximum OpenAI tool rounds per workstation trial prompt.",
    )
    trial_validate.add_argument(
        "--report-out", type=Path, help="Optional top-level validation report path."
    )


def build_workstation_parser() -> argparse.ArgumentParser:
    """Build the standalone workstation command parser."""

    parser = argparse.ArgumentParser(
        prog="realized-workstation",
        description="Launch and operate the Realized workstation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_workstation_subcommands(
        subparsers,
        include_legacy_aliases=True,
    )
    return parser


__all__ = [
    "WORKSTATION_ACTIONS",
    "add_workstation_subcommands",
    "build_workstation_parser",
]
