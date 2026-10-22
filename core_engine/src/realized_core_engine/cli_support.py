"""Argparse adapter for the separately packaged core command line."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import cast

from args import (
    add_controller_feature_toggle_arguments,
    add_prolog_query_priming_argument,
    add_supported_executor_arguments,
)

from realized_core_engine.contracts import (
    EngineConfiguration,
    EngineExecutor,
    EngineFeatureToggle,
    EngineLlmPolicy,
    EnginePrologQueryPriming,
)


def add_runtime_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_state_out: bool = True,
) -> None:
    """Add the established engine options to a command parser."""

    parser.add_argument(
        "--evidence-file",
        type=Path,
        help="Optional JSON file containing evidence items.",
    )
    if include_state_out:
        parser.add_argument(
            "--state-out",
            type=Path,
            help="Optional path for the resulting durable state JSON.",
        )
    parser.add_argument(
        "--sqlite",
        type=Path,
        help=(
            "SQLite database path. Defaults to STATE_SQLITE_PATH or "
            "state/realization.sqlite3."
        ),
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=256,
        help="Maximum number of bounded controller steps.",
    )
    parser.add_argument(
        "--llm",
        choices=["off", "auto", "required"],
        default=os.getenv("LLM_SUPPLEMENT_POLICY", "auto"),
        help="LLM supplement policy; provider configuration comes from the environment.",
    )
    add_controller_feature_toggle_arguments(parser)
    add_prolog_query_priming_argument(parser)
    add_supported_executor_arguments(parser)


def configuration_from_namespace(args: argparse.Namespace) -> EngineConfiguration:
    """Project parsed command arguments into the transport-neutral contract."""

    supported_executors = getattr(args, "supported_executors", None)
    return EngineConfiguration(
        evidence_path=getattr(args, "evidence_file", None),
        state_output_path=getattr(args, "state_out", None),
        sqlite_path=getattr(args, "sqlite", None),
        max_steps=int(getattr(args, "max_steps", 256)),
        llm_policy=cast(EngineLlmPolicy, getattr(args, "llm", "auto")),
        discovery=cast(
            EngineFeatureToggle | None,
            getattr(args, "discovery", None),
        ),
        reflection=cast(
            EngineFeatureToggle | None,
            getattr(args, "reflection", None),
        ),
        contemplation=cast(
            EngineFeatureToggle | None,
            getattr(args, "contemplation", None),
        ),
        prolog_query_priming=cast(
            EnginePrologQueryPriming | None,
            getattr(args, "prolog_query_priming", None),
        ),
        supported_executors=(
            tuple(cast(list[EngineExecutor], supported_executors))
            if supported_executors is not None
            else None
        ),
    )


__all__ = ["add_runtime_arguments", "configuration_from_namespace"]
