"""Public application interface over the canonical governed engine."""

from __future__ import annotations

import os
from dataclasses import replace
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
from realized_core_engine.canonical_reduction import CanonicalReductionAdapter
from realized_core_engine.resumption_contracts import (
    InspectionRequest,
    InspectionResult,
    ResumptionRequest,
    ResumptionResult,
    StartRequest,
)
from realized_core_engine.resumption_repository import SQLiteResumptionRepository
from realized_core_engine.resumption_service import ResumptionService
from realized_core_runtime import InterruptionRequest, InterruptionResult


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
    evidence_specs = (
        load_evidence_specs(configuration.evidence_path)
        if configuration.evidence_path is not None
        else []
    )
    evidence_specs.extend(inlet.to_evidence_spec() for inlet in configuration.inlets)
    if evidence_specs:
        attach_evidence_specs(state, evidence_specs)


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


class ResumptionEngine:
    """Supported application ABI for governed semantic continuation."""

    def __init__(
        self,
        *,
        configuration: EngineConfiguration | None = None,
    ) -> None:
        self.configuration = _configuration(configuration)
        _configure_environment(self.configuration)
        self.sqlite_path = _resumption_sqlite_path(self.configuration)
        repository = SQLiteResumptionRepository(self.sqlite_path)
        self._service = ResumptionService(
            repository,
            reduction_controller=CanonicalReductionAdapter(),
        )

    def start(self, request: StartRequest) -> ResumptionResult:
        return self._service.start(
            replace(
                request,
                execution_policy=self._execution_policy(
                    request.execution_policy
                ),
            )
        )

    def resume(self, request: ResumptionRequest) -> ResumptionResult:
        return self._service.resume(
            replace(
                request,
                execution_policy=self._execution_policy(
                    request.execution_policy
                ),
            )
        )

    def interrupt(self, request: InterruptionRequest) -> InterruptionResult:
        return self._service.interrupt(request)

    def inspect(self, request: InspectionRequest) -> InspectionResult:
        return self._service.inspect(request)

    def _execution_policy(self, supplied: dict[str, object]) -> dict[str, object]:
        evidence_specs = (
            load_evidence_specs(self.configuration.evidence_path)
            if self.configuration.evidence_path is not None
            else []
        )
        evidence_specs.extend(
            inlet.to_evidence_spec() for inlet in self.configuration.inlets
        )
        configured: dict[str, object] = {
            "sqlite_path": str(self.sqlite_path),
            "max_steps": self.configuration.max_steps,
            "llm_policy": self.configuration.llm_policy,
            "evidence_specs": evidence_specs,
        }
        for key, value in (
            ("discovery", self.configuration.discovery),
            ("reflection", self.configuration.reflection),
            ("contemplation", self.configuration.contemplation),
            ("prolog_query_priming", self.configuration.prolog_query_priming),
            ("supported_executors", self.configuration.supported_executors),
        ):
            if value is not None:
                configured[key] = value
        return {**configured, **dict(supplied)}


def _resumption_sqlite_path(configuration: EngineConfiguration) -> Path:
    selected = configuration.sqlite_path
    if selected is None:
        selected = Path(
            os.getenv(STATE_SQLITE_PATH_ENV, "state/realization.sqlite3")
        )
    return Path(selected).expanduser().resolve()


def open_resumption_engine(
    *,
    configuration: EngineConfiguration | None = None,
) -> ResumptionEngine:
    """Open the canonical semantic application boundary over plain SQLite."""

    return ResumptionEngine(configuration=configuration)


def start_objective(
    request: StartRequest,
    *,
    configuration: EngineConfiguration | None = None,
) -> ResumptionResult:
    return open_resumption_engine(configuration=configuration).start(request)


def resume_objective(
    request: ResumptionRequest,
    *,
    configuration: EngineConfiguration | None = None,
) -> ResumptionResult:
    return open_resumption_engine(configuration=configuration).resume(request)


def interrupt_attempt(
    request: InterruptionRequest,
    *,
    configuration: EngineConfiguration | None = None,
) -> InterruptionResult:
    return open_resumption_engine(configuration=configuration).interrupt(request)


def inspect_resumption(
    request: InspectionRequest,
    *,
    configuration: EngineConfiguration | None = None,
) -> InspectionResult:
    return open_resumption_engine(configuration=configuration).inspect(request)


__all__ = [
    "ResumptionEngine",
    "inspect",
    "inspect_resumption",
    "interrupt_attempt",
    "open_resumption_engine",
    "resume",
    "resume_objective",
    "run",
    "start_objective",
]
