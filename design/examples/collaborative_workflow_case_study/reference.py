"""Reference typed implementation for the collaborative workflow case study."""

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
from design.embodiment import HandoffEmbodiment
from design.framework.base import FrameworkEncoding
from design.reality import EvidenceSeverity, HandoffFailure
from design.revision import DesignSnapshot, RealitySnapshot


def build_reference_snapshot() -> DesignSnapshot:
    objective = Objective(
        id="obj_collaborative_handoff",
        name="Keep multi-actor work visible through handoff and escalation",
        description=(
            "Collaborative work should preserve ownership, status, and escalation"
            " clarity across contributors."
        ),
        intent_types=(Intent.COORDINATE, Intent.MONITOR, Intent.RECOVER),
        success_metrics=("ownership is legible", "handoffs do not lose intent"),
    )
    obligation = InteractionObligation(
        id="obl_collaborative_handoff",
        name="Shared workflow handoff discipline",
        description="Represent owners, status, blockers, and escalation paths explicitly.",
        intent_types=(Intent.COORDINATE, Intent.MONITOR, Intent.RECOVER, Intent.CONFIRM),
        task_morphologies=(TaskMorphology.COLLABORATIVE, TaskMorphology.BRANCHING),
        invariants=(
            InteractionInvariant.VISIBILITY,
            InteractionInvariant.CONSISTENCY,
            InteractionInvariant.STATE_AWARENESS,
            InteractionInvariant.RECOVERABILITY,
        ),
        risk_class=RiskClass.NORMAL,
        recoverability_requirement=RecoverabilityRequirement.STRONG,
        coordination_requirement=CoordinationRequirement.MULTI_ACTOR,
    )
    embodiment = HandoffEmbodiment(
        embodiment_id="emb_collaborative_handoff",
        name="Collaborative handoff embodiment",
        obligation_refs=(obligation.id,),
        invariant_refs=tuple(invariant.value for invariant in obligation.invariants),
        risk_class=obligation.risk_class,
        recoverability_posture=obligation.recoverability_requirement,
        implementation_notes=(
            "Use shared boards, explicit owner fields, handoff packets, and escalation markers.",
        ),
    )
    encoding = FrameworkEncoding(
        encoding_id="enc_collaborative_board",
        framework_name="collaborative_workflow",
        component_type="shared_board_and_handoff_packet",
        embodiment_ref=embodiment.embodiment_id,
        obligation_refs=(obligation.id,),
        required_invariant_refs=obligation.invariants,
        admissible_risk_classes=(RiskClass.LOW, RiskClass.NORMAL, RiskClass.HIGH),
        payload={
            "artifacts": [
                "shared board",
                "owner field",
                "handoff packet",
                "escalation path",
            ],
        },
        trace_refs=(obligation.id,),
    )
    return DesignSnapshot(
        snapshot_id="collaborative_workflow_case_study_v1",
        objectives=(objective,),
        obligations=(obligation,),
        embodiments=(embodiment,),
        encodings=(encoding,),
        metadata={"case_study": "collaborative_workflow_case_study"},
    )


def build_reference_reality_snapshot(snapshot: DesignSnapshot) -> RealitySnapshot:
    encoding = snapshot.encodings[0]
    obligation = snapshot.obligations[0]
    return RealitySnapshot(
        snapshot_id="collaborative_workflow_case_study_runtime_v1",
        evidence=(
            HandoffFailure(
                evidence_id="ev_collaborative_handoff_gap",
                actor_or_system_source="workflow_audit",
                observed_fact="A handoff packet omitted escalation context and exposed a coordination gap.",
                affected_encoding_refs=(encoding.encoding_id,),
                affected_obligation_refs=(obligation.id,),
                severity=EvidenceSeverity.HIGH,
            ),
        ),
        metadata={"case_study": "collaborative_workflow_case_study"},
    )


def get_reference_bundle() -> tuple[DesignSnapshot, RealitySnapshot]:
    snapshot = build_reference_snapshot()
    return snapshot, build_reference_reality_snapshot(snapshot)

