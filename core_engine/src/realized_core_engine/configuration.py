"""Runtime configuration adaptation shared by engine composition surfaces."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from realized_core_runtime.execution import (
    SUPPORTED_EXECUTOR_FRAMEWORKS_ENV,
    normalize_supported_executor_frameworks,
)
from realized_core_semantics.normalization import (
    normalize_controller_feature_toggle_enabled,
)
from realized_skill_semantics.execution import (
    SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES,
)


STATE_SQLITE_PATH_ENV = "STATE_SQLITE_PATH"


def add_controller_feature_toggle_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """Declare controller feature switches on an outer parser."""

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
    """Declare structural Prolog-query priming policy on an outer parser."""

    parser.add_argument(
        "--prolog-query-priming",
        choices=["off", "fallback", "force"],
        default=os.getenv("BSSC_PROLOG_QUERY_PRIMING", "fallback"),
        help=(
            "When Prolog title representation is active, control whether LLM "
            "query priming is disabled, used as fallback, or forced."
        ),
    )


def add_supported_executor_arguments(parser: argparse.ArgumentParser) -> None:
    """Declare the externally supplied executor frameworks for one run."""

    parser.add_argument(
        "--supported-executor",
        dest="supported_executors",
        action="append",
        choices=list(SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES),
        default=None,
        help=(
            "Repeat to allow external executor frameworks, for example "
            "--supported-executor python3 --supported-executor bash."
        ),
    )


def add_sqlite_path_argument(parser: argparse.ArgumentParser) -> None:
    """Declare an explicit artifact-store path on an outer parser."""

    parser.add_argument(
        "--sqlite",
        type=Path,
        default=None,
        help=(
            "Override the SQLite artifact-store path for this command. This "
            "takes precedence over STATE_SQLITE_PATH."
        ),
    )


def apply_controller_feature_toggle_overrides(
    state: Any,
    args: argparse.Namespace,
) -> None:
    """Apply parsed feature and executor selections to controller state."""

    discovery = getattr(args, "discovery", None)
    reflection = getattr(args, "reflection", None)
    contemplation = getattr(args, "contemplation", None)
    supported_executors = getattr(args, "supported_executors", None)
    if discovery is not None:
        state.controller_features.discovery_enabled = (
            normalize_controller_feature_toggle_enabled(
                discovery,
                default=state.controller_features.discovery_enabled,
            )
        )
    if reflection is not None:
        state.controller_features.reflection_enabled = (
            normalize_controller_feature_toggle_enabled(
                reflection,
                default=state.controller_features.reflection_enabled,
            )
        )
    if contemplation is not None:
        state.controller_features.contemplation_enabled = (
            normalize_controller_feature_toggle_enabled(
                contemplation,
                default=state.controller_features.contemplation_enabled,
            )
        )
    if supported_executors is None:
        environment_value = os.getenv(SUPPORTED_EXECUTOR_FRAMEWORKS_ENV)
        if environment_value is not None:
            supported_executors = [
                item for item in environment_value.split(",") if item.strip()
            ]
    if supported_executors is not None:
        state.controller_features.supported_executors = (
            normalize_supported_executor_frameworks(
                supported_executors,
                default=state.controller_features.supported_executors,
            )
        )


def apply_sqlite_path_override(args: argparse.Namespace) -> Path | None:
    """Apply an explicit SQLite override for historical entry composition."""

    sqlite_path = getattr(args, "sqlite", None)
    if sqlite_path is None:
        return None
    resolved = Path(sqlite_path).expanduser()
    os.environ[STATE_SQLITE_PATH_ENV] = str(resolved)
    return resolved


__all__ = [
    "STATE_SQLITE_PATH_ENV",
    "add_controller_feature_toggle_arguments",
    "add_prolog_query_priming_argument",
    "add_sqlite_path_argument",
    "add_supported_executor_arguments",
    "apply_controller_feature_toggle_overrides",
    "apply_sqlite_path_override",
]
