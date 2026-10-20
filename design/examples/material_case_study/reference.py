"""Reference typed implementation for the Material case study."""

from __future__ import annotations

from design.controllers import DesignCompiler
from design.core import (
    InteractionInvariant,
    InteractionObligation,
    Intent,
    Objective,
    RecoverabilityRequirement,
    RiskClass,
    TaskMorphology,
)
from design.reality import EvidenceSeverity, FeedbackEvent
from design.revision import DesignSnapshot, RealitySnapshot


def build_reference_snapshot() -> DesignSnapshot:
    compiler = DesignCompiler()
    objective = Objective(
        id="obj_material_primary_action",
        name="Let the user commit the dominant next action clearly",
        description=(
            "The interface should present a primary committed action with"
            " unambiguous visibility and immediate feedback."
        ),
        intent_types=(Intent.TRIGGER, Intent.CONFIRM),
        success_metrics=("primary action is found quickly", "commit is deliberate"),
    )
    obligation = InteractionObligation(
        id="obl_material_primary_action",
        name="Primary committed digital action",
        description="Encode the dominant committed action as the most legible control.",
        intent_types=(Intent.TRIGGER, Intent.CONFIRM),
        task_morphologies=(TaskMorphology.ONE_SHOT,),
        invariants=(
            InteractionInvariant.VISIBILITY,
            InteractionInvariant.SALIENCE,
            InteractionInvariant.FEEDBACK,
            InteractionInvariant.CONSTRAINT,
        ),
        risk_class=RiskClass.NORMAL,
        recoverability_requirement=RecoverabilityRequirement.BASIC,
    )
    embodiment = compiler.compile_obligation_to_embodiment(
        obligation,
        name="Primary action embodiment",
    )
    encoding = compiler.compile_embodiment_to_material_button(
        embodiment,
        variant="filled",
    )
    return DesignSnapshot(
        snapshot_id="material_case_study_v1",
        objectives=(objective,),
        obligations=(obligation,),
        embodiments=(embodiment,),
        encodings=(encoding,),
        metadata={"case_study": "material_case_study"},
    )


def build_reference_reality_snapshot(snapshot: DesignSnapshot) -> RealitySnapshot:
    encoding = snapshot.encodings[0]
    obligation = snapshot.obligations[0]
    return RealitySnapshot(
        snapshot_id="material_case_study_runtime_v1",
        evidence=(
            FeedbackEvent(
                evidence_id="ev_material_feedback_visible",
                actor_or_system_source="runtime_telemetry",
                observed_fact="Users consistently detect the filled action and receive immediate feedback.",
                affected_encoding_refs=(encoding.encoding_id,),
                affected_obligation_refs=(obligation.id,),
                severity=EvidenceSeverity.LOW,
            ),
        ),
        metadata={"case_study": "material_case_study"},
    )


def get_reference_bundle() -> tuple[DesignSnapshot, RealitySnapshot]:
    snapshot = build_reference_snapshot()
    return snapshot, build_reference_reality_snapshot(snapshot)

