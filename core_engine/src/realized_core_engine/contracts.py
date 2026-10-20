"""Stable contracts for invoking the governed core engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


type EngineLlmPolicy = Literal["off", "auto", "required"]
type EngineFeatureToggle = Literal["on", "off"]
type EnginePrologQueryPriming = Literal["off", "fallback", "force"]
type EngineExecutor = Literal["python3", "bash", "ansible", "wasm_wasi"]


@dataclass(frozen=True, slots=True)
class EngineConfiguration:
    """Typed, transport-neutral configuration for one engine invocation."""

    evidence_path: Path | None = None
    state_output_path: Path | None = None
    sqlite_path: Path | None = None
    max_steps: int = 256
    llm_policy: EngineLlmPolicy = "auto"
    discovery: EngineFeatureToggle | None = None
    reflection: EngineFeatureToggle | None = None
    contemplation: EngineFeatureToggle | None = None
    prolog_query_priming: EnginePrologQueryPriming | None = None
    supported_executors: tuple[EngineExecutor, ...] | None = None


@dataclass(frozen=True, slots=True)
class EngineResult:
    """Stable result projection that does not expose mutable engine state."""

    summary: dict[str, Any]


__all__ = [
    "EngineConfiguration",
    "EngineExecutor",
    "EngineFeatureToggle",
    "EngineLlmPolicy",
    "EnginePrologQueryPriming",
    "EngineResult",
]
