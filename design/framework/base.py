"""Framework-agnostic encoding base types."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import InteractionInvariant, RiskClass


@dataclass(frozen=True, slots=True)
class FrameworkEncoding:
    encoding_id: str
    framework_name: str
    component_type: str
    embodiment_ref: str
    obligation_refs: tuple[str, ...] = ()
    required_invariant_refs: tuple[InteractionInvariant, ...] = ()
    admissible_risk_classes: tuple[RiskClass, ...] = (
        RiskClass.LOW,
        RiskClass.NORMAL,
    )
    payload: dict[str, object] = field(default_factory=dict)
    trace_refs: tuple[str, ...] = ()

