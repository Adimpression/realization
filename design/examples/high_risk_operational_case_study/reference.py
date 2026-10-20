"""Reference typed implementation for the high-risk operational case study."""

from __future__ import annotations

from design.core import (
    CoordinationRequirement,
    InteractionInvariant,
    InteractionObligation,
    Intent,
    Objective,
    RecoverabilityRequirement,
    RiskClass,
    TaskMorphology,
)
from design.embodiment import InterlockEmbodiment
from design.framework.base import FrameworkEncoding
from design.reality import BoundaryFriction, EvidenceSeverity
from design.revision import DesignSnapshot, RealitySnapshot


def build_reference_snapshot() -> DesignSnapshot:
    objective = Objective(
        id="obj_operational_safe_override",
        name="Keep operators aware while constraining dangerous overrides",
        description=(
            "Operators should see the current plant state, blocking conditions,"
            " and override consequences before taking action."
        ),
        intent_types=(Intent.MONITOR, Intent.VERIFY, Intent.CONFIRM, Intent.INTERRUPT),
        success_metrics=("unsafe overrides are prevented", "recovery remains auditable"),
    )
    obligation = InteractionObligation(
        id="obl_operational_interlock",
        name="High-risk interlock and override discipline",
        description="Expose blocking conditions, require confirmation, and preserve auditability.",
        intent_types=(Intent.MONITOR, Intent.VERIFY, Intent.CONFIRM, Intent.RECOVER),
        task_morphologies=(TaskMorphology.SUPERVISORY, TaskMorphology.EMERGENCY),
        invariants=(
            InteractionInvariant.SALIENCE,
            InteractionInvariant.CONSTRAINT,
            InteractionInvariant.REDUNDANCY,
            InteractionInvariant.RECOVERABILITY,
            InteractionInvariant.TRUSTWORTHINESS,
        ),
        risk_class=RiskClass.CRITICAL,
        recoverability_requirement=RecoverabilityRequirement.REVERSIBLE,
        coordination_requirement=CoordinationRequirement.GOVERNANCE,
    )
    embodiment = InterlockEmbodiment(
        embodiment_id="emb_operational_interlock",
        name="Operational interlock embodiment",
        obligation_refs=(obligation.id,),
        invariant_refs=tuple(invariant.value for invariant in obligation.invariants),
        risk_class=obligation.risk_class,
        recoverability_posture=obligation.recoverability_requirement,
        implementation_notes=(
            "Use interlocks, alarm grouping, explicit override reasons, and audit traces.",
        ),
    )
    encoding = FrameworkEncoding(
        encoding_id="enc_operational_interlock_console",
        framework_name="high_risk_operational",
        component_type="alarm_console_and_interlock",
        embodiment_ref=embodiment.embodiment_id,
        obligation_refs=(obligation.id,),
        required_invariant_refs=obligation.invariants,
        admissible_risk_classes=(RiskClass.HIGH, RiskClass.CRITICAL),
        payload={
            "artifacts": [
                "alarm state board",
                "override interlock",
                "checklist gate",
                "audit record",
            ],
        },
        trace_refs=(obligation.id,),
    )
    return DesignSnapshot(
        snapshot_id="high_risk_operational_case_study_v1",
        objectives=(objective,),
        obligations=(obligation,),
        embodiments=(embodiment,),
        encodings=(encoding,),
        metadata={"case_study": "high_risk_operational_case_study"},
    )


def build_reference_reality_snapshot(snapshot: DesignSnapshot) -> RealitySnapshot:
    encoding = snapshot.encodings[0]
    obligation = snapshot.obligations[0]
    return RealitySnapshot(
        snapshot_id="high_risk_operational_case_study_runtime_v1",
        evidence=(
            BoundaryFriction(
                evidence_id="ev_operational_shift_handoff",
                actor_or_system_source="operations_review",
                observed_fact="Shift handoff friction increases override delay but does not invalidate the interlock discipline.",
                affected_encoding_refs=(encoding.encoding_id,),
                affected_obligation_refs=(obligation.id,),
                severity=EvidenceSeverity.MEDIUM,
            ),
        ),
        metadata={"case_study": "high_risk_operational_case_study"},
    )


def get_reference_bundle() -> tuple[DesignSnapshot, RealitySnapshot]:
    snapshot = build_reference_snapshot()
    return snapshot, build_reference_reality_snapshot(snapshot)

