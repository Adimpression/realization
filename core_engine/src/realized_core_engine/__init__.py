"""Public ABI for the canonical governed realization engine."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORT_MODULES = {
    "EngineConfiguration": "realized_core_engine.contracts",
    "EngineExecutor": "realized_core_engine.contracts",
    "EngineFeatureToggle": "realized_core_engine.contracts",
    "EngineInlet": "realized_core_engine.contracts",
    "EngineInletKind": "realized_core_engine.contracts",
    "EngineLlmPolicy": "realized_core_engine.contracts",
    "EnginePrologQueryPriming": "realized_core_engine.contracts",
    "EngineResult": "realized_core_engine.contracts",
    "ArtifactRepository": "realized_core_engine.persistence",
    "open_sqlite_artifact_repository": "realized_core_engine.persistence",
    "AdmissionDecision": "realized_core_engine.resumption_contracts",
    "AdmissionDisposition": "realized_core_engine.resumption_contracts",
    "ContinuationInlet": "realized_core_engine.resumption_contracts",
    "GoverningDirection": "realized_core_engine.resumption_contracts",
    "HoldDisposition": "realized_core_engine.resumption_contracts",
    "HoldOn": "realized_core_engine.resumption_contracts",
    "IdentityDisposition": "realized_core_engine.resumption_contracts",
    "IdentityDispositionKind": "realized_core_engine.resumption_contracts",
    "InletRelationship": "realized_core_engine.resumption_contracts",
    "InspectionRequest": "realized_core_engine.resumption_contracts",
    "InspectionResult": "realized_core_engine.resumption_contracts",
    "InspectionTargetKind": "realized_core_engine.resumption_contracts",
    "InspectionView": "realized_core_engine.resumption_contracts",
    "OperationKind": "realized_core_engine.resumption_contracts",
    "ProjectionPolicy": "realized_core_engine.resumption_contracts",
    "Realignment": "realized_core_engine.resumption_contracts",
    "Reversal": "realized_core_engine.resumption_contracts",
    "ResumptionIdentity": "realized_core_engine.resumption_contracts",
    "ResumptionRequest": "realized_core_engine.resumption_contracts",
    "ResumptionResult": "realized_core_engine.resumption_contracts",
    "SemanticDelta": "realized_core_engine.resumption_contracts",
    "SemanticItem": "realized_core_engine.resumption_contracts",
    "SemanticOutcome": "realized_core_engine.resumption_contracts",
    "StartRequest": "realized_core_engine.resumption_contracts",
    "Supersession": "realized_core_engine.resumption_contracts",
    "NormalizedRequestInProgressError": "realized_core_engine.resumption_service",
    "InterruptionRequest": "realized_core_runtime",
    "InterruptionResult": "realized_core_runtime",
    "ResumptionEngine": "realized_core_engine.api",
    "inspect": "realized_core_engine.api",
    "inspect_resumption": "realized_core_engine.api",
    "interrupt_attempt": "realized_core_engine.api",
    "lookup_normalized_request": "realized_core_engine.api",
    "open_resumption_engine": "realized_core_engine.api",
    "resume": "realized_core_engine.api",
    "resume_objective": "realized_core_engine.api",
    "run": "realized_core_engine.api",
    "start_objective": "realized_core_engine.api",
}

__all__ = list(_EXPORT_MODULES)


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
