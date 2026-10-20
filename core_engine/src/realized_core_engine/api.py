"""Public application interface over the canonical governed engine."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

from args import STATE_SQLITE_PATH_ENV, apply_controller_feature_toggle_overrides
from controller_runtime import build_controller
from system_state import (
    SystemState,
    attach_evidence_specs,
    load_evidence_specs,
    load_state,
    save_state,
)
from title_semantics import PROLOG_QUERY_PRIMING_MODE_ENV

from realized_core_engine.contracts import EngineConfiguration, EngineResult


def _configuration(value: EngineConfiguration | None) -> EngineConfiguration:
    return value if value is not None else EngineConfiguration()


def _configure_environment(configuration: EngineConfiguration) -> None:
    # The installable core intentionally selects the plain SQLite path only.
    os.environ["STATE_VECTOR_MODE"] = "off"
    if configuration.sqlite_path is not None:
        os.environ[STATE_SQLITE_PATH_ENV] = str(configuration.sqlite_path.expanduser())
    if configuration.prolog_query_priming:
        os.environ[PROLOG_QUERY_PRIMING_MODE_ENV] = (
            configuration.prolog_query_priming
        )


def _apply_configuration(
    state: SystemState,
    configuration: EngineConfiguration,
) -> None:
    apply_controller_feature_toggle_overrides(
        state,
        SimpleNamespace(
            discovery=configuration.discovery,
            reflection=configuration.reflection,
            contemplation=configuration.contemplation,
            supported_executors=configuration.supported_executors,
        ),
    )
    if configuration.evidence_path is not None:
        attach_evidence_specs(
            state,
            load_evidence_specs(configuration.evidence_path),
        )


def _execute(
    state: SystemState,
    configuration: EngineConfiguration,
    *,
    resume_existing: bool,
) -> EngineResult:
    _configure_environment(configuration)
    _apply_configuration(state, configuration)
    controller = build_controller(
        state=state,
        llm_policy=configuration.llm_policy,
    )
    if resume_existing:
        controller.resume(max_steps=configuration.max_steps)
    else:
        controller.run(max_steps=configuration.max_steps)
    if configuration.state_output_path is not None:
        save_state(state, configuration.state_output_path)
    return EngineResult(summary=state.summary())


def run(
    prompt: str,
    *,
    configuration: EngineConfiguration | None = None,
) -> EngineResult:
    """Start a governed realization from a new represented prompt."""

    return _execute(
        SystemState.bootstrap(prompt),
        _configuration(configuration),
        resume_existing=False,
    )


def resume(
    state_path: Path,
    *,
    configuration: EngineConfiguration | None = None,
) -> EngineResult:
    """Resume a governed realization from durable state."""

    return _execute(
        load_state(state_path),
        _configuration(configuration),
        resume_existing=True,
    )


def inspect(state_path: Path) -> EngineResult:
    """Read the stable summary projection of durable state without running it."""

    return EngineResult(summary=load_state(state_path).summary())


__all__ = ["inspect", "resume", "run"]
