"""Narrow command-line interface for the governed core and SQLite store."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from realized_core_engine import (
    inspect as inspect_state,
    resume as resume_engine,
    run as run_engine,
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
    elif args.command == "chat":
        return run_core_chat_loop(
            CoreConversationHost(
                root=args.root,
                configuration=configuration_from_namespace(args),
            )
        )
    else:
        return 1
    print(json.dumps(result.summary, indent=2, sort_keys=True))
    return 0


__all__ = ["build_parser", "main"]
