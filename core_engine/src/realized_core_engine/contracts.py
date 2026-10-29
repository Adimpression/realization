"""Stable contracts for invoking the governed core engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from realized_host_interaction.context import HostInteractionContext


type EngineLlmPolicy = Literal["off", "auto", "required"]
type EngineFeatureToggle = Literal["on", "off"]
type EnginePrologQueryPriming = Literal["off", "fallback", "force"]
type EngineExecutor = Literal["python3", "bash", "ansible", "wasm_wasi"]
type EngineInletKind = Literal["evidence", "human_contribution", "prior_result"]


@dataclass(frozen=True, slots=True)
class EngineInlet:
    """One explicitly admitted, provenance-bearing engine boundary input."""

    kind: EngineInletKind
    content: str
    source_ref: str
    target: str = "root"
    context: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    support_strength: Literal["low", "medium", "high"] = "high"
    confidence: Literal["low", "medium", "high"] = "high"
    polarity: Literal["support", "contradict", "neutral"] = "support"

    def to_evidence_spec(self) -> dict[str, Any]:
        """Project the public contract into the canonical evidence inlet shape."""

        source = {
            "human_contribution": "human",
            "prior_result": "governed_prior_result",
        }.get(self.kind, "external")
        return {
            "target": self.target,
            "observation": self.content,
            "source": source,
            "context": {
                **dict(self.context),
                "engine_inlet_kind": self.kind,
                "source_ref": self.source_ref,
            },
            "provenance": [self.source_ref, *self.provenance],
            "support_strength": self.support_strength,
            "confidence": self.confidence,
            "polarity": self.polarity,
        }


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
    inlets: tuple[EngineInlet, ...] = ()
    host_interaction_context: HostInteractionContext | None = field(
        default=None,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True, slots=True)
class EngineResult:
    """Stable result projection that does not expose mutable engine state."""

    summary: dict[str, Any]


__all__ = [
    "EngineConfiguration",
    "EngineExecutor",
    "EngineFeatureToggle",
    "EngineInlet",
    "EngineInletKind",
    "EngineLlmPolicy",
    "EnginePrologQueryPriming",
    "EngineResult",
]
