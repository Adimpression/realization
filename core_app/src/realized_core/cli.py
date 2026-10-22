"""Narrow command-line interface for the governed core and SQLite store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from realized_core_engine import (
    InspectionRequest,
    InterruptionRequest,
    ResumptionRequest,
    StartRequest,
    inspect as inspect_state,
    inspect_resumption,
    interrupt_attempt,
    resume as resume_engine,
    resume_objective,
    run as run_engine,
    start_objective,
)
from realized_core_engine.cli_support import (
    add_runtime_arguments,
    configuration_from_namespace,
)
from realized_core.chat import CoreConversationHost, run_core_chat_loop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="realized-core",
        description=(
            "Run the canonical governed realization engine with plain SQLite "
            "persistence."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Start a fresh governed run from a prompt.",
    )
    run_parser.add_argument(
        "--prompt",
        required=True,
        help="High-level prompt represented as the root non-achievedness.",
    )
    add_runtime_arguments(run_parser)

    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume a previously saved governed state.",
    )
    resume_parser.add_argument(
        "--state-in",
        type=Path,
        required=True,
        help="Path to the saved durable state JSON.",
    )
    add_runtime_arguments(resume_parser)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Print the summary of a saved governed state.",
    )
    inspect_parser.add_argument(
        "--state",
        type=Path,
        required=True,
        help="Path to the saved durable state JSON.",
    )

    objective_start_parser = subparsers.add_parser(
        "objective-start",
        help="Start a typed governed objective from a JSON request.",
    )
    _add_request_file_argument(objective_start_parser)
    add_runtime_arguments(objective_start_parser, include_state_out=False)

    objective_resume_parser = subparsers.add_parser(
        "objective-resume",
        help="Run a typed continuation from an exact causal anchor.",
    )
    _add_request_file_argument(objective_resume_parser)
    add_runtime_arguments(objective_resume_parser, include_state_out=False)

    interrupt_parser = subparsers.add_parser(
        "attempt-interrupt",
        help="Interrupt one exact execution attempt without semantic mutation.",
    )
    _add_request_file_argument(interrupt_parser)
    interrupt_parser.add_argument(
        "--sqlite",
        type=Path,
        required=True,
        help="SQLite database containing the execution attempt.",
    )

    resumption_inspect_parser = subparsers.add_parser(
        "resumption-inspect",
        help="Inspect a typed revision, branch, attempt, or transition.",
    )
    _add_request_file_argument(resumption_inspect_parser)
    resumption_inspect_parser.add_argument(
        "--sqlite",
        type=Path,
        required=True,
        help="SQLite database containing the requested object.",
    )

    chat_parser = subparsers.add_parser(
        "chat",
        help="Run a thin conversation host over explicit governed reductions.",
    )
    chat_parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Directory for transcript, run bindings, checkpoints, and SQLite.",
    )
    add_runtime_arguments(chat_parser, include_state_out=False)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "run":
        result = run_engine(
            args.prompt,
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "resume":
        result = resume_engine(
            args.state_in,
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "inspect":
        result = inspect_state(args.state)
    elif args.command == "objective-start":
        result = start_objective(
            StartRequest.from_dict(_load_json_object(args.request)),
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "objective-resume":
        result = resume_objective(
            ResumptionRequest.from_dict(_load_json_object(args.request)),
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "attempt-interrupt":
        result = interrupt_attempt(
            InterruptionRequest.from_dict(_load_json_object(args.request)),
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "resumption-inspect":
        result = inspect_resumption(
            InspectionRequest.from_dict(_load_json_object(args.request)),
            configuration=configuration_from_namespace(args),
        )
    elif args.command == "chat":
        return run_core_chat_loop(
            CoreConversationHost(
                root=args.root,
                configuration=configuration_from_namespace(args),
            )
        )
    else:
        return 1
    payload = result.summary if hasattr(result, "summary") else result.to_dict()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _add_request_file_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--request",
        type=Path,
        required=True,
        help="Path to the typed JSON request.",
    )


def _load_json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("A typed request file must contain one JSON object.")
    return value


__all__ = ["build_parser", "main"]
