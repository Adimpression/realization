"""Reference typed implementation for the physical service case study."""

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
from design.embodiment import QueueEmbodiment
from design.framework.base import FrameworkEncoding
from design.reality import EvidenceSeverity, QueueCongestion
from design.revision import DesignSnapshot, RealitySnapshot


def build_reference_snapshot() -> DesignSnapshot:
    objective = Objective(
        id="obj_physical_queue_guidance",
        name="Guide service users through a fair and legible queue",
        description=(
            "The service environment should make queue state, next steps, and"
            " exception handling physically obvious."
        ),
        intent_types=(Intent.LOCATE, Intent.SELECT, Intent.NAVIGATE),
        success_metrics=("users find the correct queue", "handoffs remain orderly"),
    )
    obligation = InteractionObligation(
        id="obl_physical_queue_guidance",
        name="Queue guidance and exception routing",
        description="Expose the queue, the current stage, and the exception desk clearly.",
        intent_types=(Intent.LOCATE, Intent.NAVIGATE, Intent.COORDINATE),
        task_morphologies=(TaskMorphology.SEQUENTIAL, TaskMorphology.COLLABORATIVE),
        invariants=(
            InteractionInvariant.VISIBILITY,
            InteractionInvariant.MAPPING,
            InteractionInvariant.STATE_AWARENESS,
            InteractionInvariant.RECOVERABILITY,
        ),
        risk_class=RiskClass.NORMAL,
        recoverability_requirement=RecoverabilityRequirement.STRONG,
        coordination_requirement=CoordinationRequirement.HANDOFF,
    )
    embodiment = QueueEmbodiment(
        embodiment_id="emb_physical_queue_guidance",
        name="Queue guidance embodiment",
        obligation_refs=(obligation.id,),
        invariant_refs=tuple(invariant.value for invariant in obligation.invariants),
        risk_class=obligation.risk_class,
        recoverability_posture=obligation.recoverability_requirement,
        implementation_notes=(
            "Use signage, queue rails, ticketing, and a visible exception desk.",
        ),
    )
    encoding = FrameworkEncoding(
        encoding_id="enc_physical_queue_counter",
        framework_name="physical_service",
        component_type="service_counter_and_queue",
        embodiment_ref=embodiment.embodiment_id,
        obligation_refs=(obligation.id,),
        required_invariant_refs=obligation.invariants,
        admissible_risk_classes=(RiskClass.LOW, RiskClass.NORMAL),
        payload={
            "artifacts": [
                "queue signage",
                "ticket dispenser",
                "exception desk",
                "current counter indicator",
            ],
        },
        trace_refs=(obligation.id,),
    )
    return DesignSnapshot(
        snapshot_id="physical_service_case_study_v1",
        objectives=(objective,),
        obligations=(obligation,),
        embodiments=(embodiment,),
        encodings=(encoding,),
        metadata={"case_study": "physical_service_case_study"},
    )


def build_reference_reality_snapshot(snapshot: DesignSnapshot) -> RealitySnapshot:
    encoding = snapshot.encodings[0]
    obligation = snapshot.obligations[0]
    return RealitySnapshot(
        snapshot_id="physical_service_case_study_runtime_v1",
        evidence=(
            QueueCongestion(
                evidence_id="ev_physical_queue_peak_load",
                actor_or_system_source="floor_observation",
                observed_fact="Peak-hour congestion forms before the ticket dispenser and needs clearer overflow routing.",
                affected_encoding_refs=(encoding.encoding_id,),
                affected_obligation_refs=(obligation.id,),
                severity=EvidenceSeverity.MEDIUM,
            ),
        ),
        metadata={"case_study": "physical_service_case_study"},
    )


def get_reference_bundle() -> tuple[DesignSnapshot, RealitySnapshot]:
    snapshot = build_reference_snapshot()
    return snapshot, build_reference_reality_snapshot(snapshot)

