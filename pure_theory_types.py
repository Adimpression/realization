# See MODULES.md for the repository module map before editing.
"""Pydantic-compatible pure theory types derived from THEORY.md V2.0.3.

Every enum and model in this module is grounded in the current theory text.
Each class docstring cites the relevant THEORY.md section number and title.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, TypeAlias

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


EntityId: TypeAlias = str
JsonMap: TypeAlias = dict[str, Any]


class TheoryModel(BaseModel):
    """THEORY.md §31.1 "System form".

    Common Pydantic base model for pure theory objects.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class CarrierKind(str, Enum):
    """THEORY.md §4.4 "Boundary-shape completeness" and §4.7 "Structural consequence".

    Canonical BSSC carrier kinds.
    """

    DATA = "D*"
    REFERENCE = "R*"
    MIXED = "D* ⊕ R*"


class BoundaryLaneKind(str, Enum):
    """THEORY.md §4.5.1 "Canonical classes with Values and References".

    Canonical lane symbols before multiplicity is applied.
    """

    INPUT_VALUE = "a"
    INPUT_REFERENCE = "a'"
    READ_VALUE = "b"
    READ_REFERENCE = "b'"
    WRITE_VALUE = "c"
    WRITE_REFERENCE = "c'"
    OUTPUT_VALUE = "d"
    OUTPUT_REFERENCE = "d'"


class BoundaryShapeTermKind(str, Enum):
    """THEORY.md §4.5.1 "Canonical classes with Values and References".

    Multiplicity-bearing boundary-shape terms over the canonical lane alphabet.
    Each term denotes one or more instances of the corresponding lane kind.
    """

    INPUT_VALUE = "a*"
    INPUT_REFERENCE = "a'*"
    READ_VALUE = "b*"
    READ_REFERENCE = "b'*"
    WRITE_VALUE = "c*"
    WRITE_REFERENCE = "c'*"
    OUTPUT_VALUE = "d*"
    OUTPUT_REFERENCE = "d'*"


# Compatibility digression:
# `main.py` historically imported `BoundaryShapeAtomKind`. The academically
# correct object here is a multiplicity-bearing term, not an atom, so the
# canonical name is `BoundaryShapeTermKind`. Keep the old name as an alias so
# runtime code and stored states can migrate without a hard break.
BoundaryShapeAtomKind = BoundaryShapeTermKind


class BoundaryClassKind(str, Enum):
    """THEORY.md §4.5 "Canonical classes".

    Exact first-order BSSC boundary classes.
    """

    CFORWARD = "Cforward"
    CBACKWARD = "Cbackward"
    SFORWARD = "Sforward"
    SBACKWARD = "Sbackward"
    LEFTH = "Lefth"
    LEFTHMIRROR = "Lefthmirror"
    RIGHTH = "Righth"
    RIGHTHMIRROR = "Righthmirror"
    CROSS = "Cross"


class NonAchievednessMisalignmentKind(str, Enum):
    """THEORY.md §3.3.1 "Remainder form of non-achievedness".

    Primary dimensions along which a realized state may fail to satisfy the
    intended achievedness target.
    """

    SPECIFICATION = "specification"
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    FUNCTIONAL = "functional"
    EPISTEMIC = "epistemic"
    CONTEXTUAL = "contextual"
    COMPLETION = "completion"
    PRECISION = "precision"
    FIDELITY = "fidelity"
    MODAL = "modal"


class NonAchievednessOriginKind(str, Enum):
    """THEORY.md §3.3.4 "Origin layers of non-achievedness".

    Coarse origin layers for where the unreduced remainder principally arises.
    """

    PROMPT = "prompt"
    MODEL = "model"
    TOOL = "tool"
    KNOWLEDGE = "knowledge"
    CONSTRAINT = "constraint"
    ONTOLOGICAL = "ontological"


class NonAchievednessDegreeKind(str, Enum):
    """THEORY.md §3.3.5 "Degree of non-achievedness".

    Magnitude classes for how much remainder remains relative to the target.
    """

    NULL = "null"
    RESIDUAL = "residual"
    PARTIAL = "partial"
    DOMINANT = "dominant"
    TOTAL = "total"
    CATEGORY_ERROR = "category_error"


class RemainderShapeKind(str, Enum):
    """THEORY.md §3.3.6 "Remainder topology".

    Topological forms the unreduced remainder may take.
    """

    MISSING = "missing"
    DISTORTED = "distorted"
    MISWEIGHTED = "misweighted"
    MISPLACED = "misplaced"
    PREMATURELY_CLOSED = "prematurely_closed"
    OVERGENERATED = "overgenerated"
    UNDERDETERMINED = "underdetermined"
    SELF_CONTRADICTORY = "self_contradictory"
    EXTERNALLY_INCONSISTENT = "externally_inconsistent"
    BLOCKED = "blocked"


class EvidenceStageKind(str, Enum):
    """THEORY.md §11.4 "Stratification".

    The evidence-to-commitment stratification that must be preserved.
    """

    OBSERVATION = "observation"
    INTERPRETED_FACT = "interpreted_fact"
    CLAIM = "claim"
    PROPOSED_COMMITMENT = "proposed_commitment"
    COMMITTED_ACHIEVEDNESS = "committed_achievedness"


class ArtifactTypeKind(str, Enum):
    """THEORY.md §18.2 "Primary division" and §§18.3-18.11.

    Primary reusable artifact classes recognized by the theory.
    """

    KNOWLEDGE = "knowledge"
    ABILITY = "ability"
    CAPABILITY = "capability"
    DUTY_TEMPLATE = "duty_template"
    CLOSURE_PATTERN = "closure_pattern"
    REJECTION_PATTERN = "rejection_pattern"
    UNCERTAINTY_PATTERN = "uncertainty_pattern"
    COMPOSITION = "composition"
    EVALUATION = "evaluation"


class PainKind(str, Enum):
    """THEORY.md §17.6 "Pain and gain" and §31.8 "Pain-gain form".

    Pain axis for developmental run classification.
    """

    NO_PAIN = "no-pain"
    PAIN = "pain"

    @classmethod
    def _missing_(cls, value: object) -> "PainKind" | None:
        # Runtime digression: main.py historically used `no_pain` while the
        # theory text uses `no-pain`. Accept both spellings here so theory-side
        # validation can be reused without maintaining a second enum family.
        """
        High Level Purpose:
            In circumstances like pure theory typing and serialization boundaries, helps with handling missing.

        Reference to Theory:
            Defines pure theory data structures that correspond directly to the ontology and theory sections implemented in the system.

        Example Input Output:
            Input: `_missing_(value=3)`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            value: Value for `value` used by `_missing_`. Expected type: `object`.

        Returns:
            'PainKind' | None: Result produced by `_missing_`.
        """
        if isinstance(value, str) and value.strip().lower().replace("-", "_") == "no_pain":
            return cls.NO_PAIN
        return None


class GainKind(str, Enum):
    """THEORY.md §17.6 "Pain and gain" and §31.8 "Pain-gain form".

    Gain axis for developmental run classification.
    """

    NO_GAIN = "no-gain"
    GAIN = "gain"

    @classmethod
    def _missing_(cls, value: object) -> "GainKind" | None:
        # Runtime digression: main.py historically used `no_gain` while the
        # theory text uses `no-gain`. Accept both spellings here so theory-side
        # validation can be reused without maintaining a second enum family.
        """
        High Level Purpose:
            In circumstances like pure theory typing and serialization boundaries, helps with handling missing.

        Reference to Theory:
            Defines pure theory data structures that correspond directly to the ontology and theory sections implemented in the system.

        Example Input Output:
            Input: `_missing_(value=3)`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            value: Value for `value` used by `_missing_`. Expected type: `object`.

        Returns:
            'GainKind' | None: Result produced by `_missing_`.
        """
        if isinstance(value, str) and value.strip().lower().replace("-", "_") == "no_gain":
            return cls.NO_GAIN
        return None


class GainTypeKind(str, Enum):
    """THEORY.md §17.9 "Typed gain".

    Typed developmental gain classes.
    """

    KNOWLEDGE_GAIN = "knowledge_gain"
    ABILITY_GAIN = "ability_gain"
    CAPABILITY_GAIN = "capability_gain"
    DUTY_TEMPLATE_GAIN = "duty_template_gain"
    CLOSURE_PATTERN_GAIN = "closure_pattern_gain"
    REJECTION_PATTERN_GAIN = "rejection_pattern_gain"
    UNCERTAINTY_PATTERN_GAIN = "uncertainty_pattern_gain"
    COMPOSITION_GAIN = "composition_gain"
    EVALUATION_GAIN = "evaluation_gain"


class RunOutcomeKind(str, Enum):
    """THEORY.md §24.3 "Run outcomes".

    Theory-level run outcomes.
    """

    # Runtime digression note:
    # `main.py` currently collapses theory-level outcomes into the coarser
    # states `completed`, `paused`, `incomplete`, and `ongoing`. We do not
    # alias those values here because the collapse is lossy: a runtime `paused`
    # does not uniquely determine which theory-level pause class occurred.

    COMMITMENT_COMPLETED = "commitment_completed"
    PAUSED_FOR_HUMAN_CONTRIBUTION = "paused_for_human_contribution"
    PAUSED_FOR_CAPABILITY_EMERGENCE = "paused_for_capability_emergence"
    PAUSED_UNDER_HOLDON = "paused_under_holdon"
    REFRAMED_THROUGH_CONTEMPLATION = "reframed_through_contemplation"
    JUSTIFIED_INCOMPLETION = "justified_incompletion"
    RESUMED_FROM_DURABLE_STATE = "resumed_from_durable_state"


class OntologyResidenceKind(str, Enum):
    """THEORY.md §26.2 "Three-layer semantic residence".

    Ontological residence layers.
    """

    AUTHORITATIVE_DURABLE_STATE = "authoritative_durable_state"
    OPERATIONAL_WORKING_SEMANTICS = "operational_working_semantics"
    EMBEDDED_SEMANTICS = "embedded_semantics"


class ProposalBudgetKind(str, Enum):
    """THEORY.md §21.5 "Proposal-budget principle".

    Budgeted expensive-motion families.
    """

    DISCOVERY_REFINEMENT = "discovery_refinement"
    SUPPLEMENTATION = "supplementation"
    REFRAMING = "reframing"
    UNCERTAINTY_REASSESSMENT = "uncertainty_reassessment"
    ARTIFACT_PROPOSAL = "artifact_proposal"


class OntologyObjectKind(str, Enum):
    """THEORY.md §26.1 "Ontology function" and §30.6 "Distinction preservation".

    Stable ontology object kinds the theory explicitly treats as semantically
    distinct.
    """

    NON_ACHIEVEDNESS = "non_achievedness"
    DUTY = "duty"
    STEP = "step"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    CAPABILITY = "capability"
    KNOWLEDGE_ARTIFACT = "knowledge_artifact"
    TEMPLATE_BEARING_ARTIFACT = "template_bearing_artifact"
    PRODUCT = "product"
    RUN = "run"
    HUMAN_CONTRIBUTION = "human_contribution"
    RESUMPTION_EVENT = "resumption_event"
    CERTAINTY_STATE = "certainty_state"
    COMMITMENT = "commitment"
    TEMPLATE_SCHEMA = "template_schema"
    PAIN_GAIN_CLASSIFICATION = "pain_gain_classification"
    DISCOVERY_AUDIT = "discovery_audit"
    FRONTIER_REJECTION = "frontier_rejection"
    BOUNDARY_TRANSITION = "boundary_transition"
    HOLDON = "holdon"


class SemanticUnit(TheoryModel):
    """THEORY.md §3.1 "Semantic unit".

    Stable semantic bearer used as the identity center for non-achievedness.
    """

    id: EntityId
    text: str
    notes: list[str] = Field(default_factory=list)


class NonAchievedness(TheoryModel):
    """THEORY.md §3 "Semantic units, achievedness, and non-achievedness",
    §7 "Not ontology", and §8 "Decomposition".

    Represented non-achievedness, including parent-child refinement position.
    """

    id: EntityId
    semantic_unit_id: EntityId | None = None
    semantic_unit: str
    description: str = ""
    intended_object: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    actual_realization: str = ""
    missing_components: list[str] = Field(default_factory=list)
    distorted_components: list[str] = Field(default_factory=list)
    misalignment_types: list[NonAchievednessMisalignmentKind] = Field(default_factory=list)
    origin_layers: list[NonAchievednessOriginKind] = Field(default_factory=list)
    degree: NonAchievednessDegreeKind | None = None
    remainder_shapes: list[RemainderShapeKind] = Field(default_factory=list)
    why_it_matters: list[str] = Field(default_factory=list)
    minimal_repair: list[str] = Field(default_factory=list)
    full_repair: list[str] = Field(default_factory=list)
    boundary_shape: list[BoundaryShapeTermKind] = Field(default_factory=list)
    parent_not_id: EntityId | None = None
    child_not_ids: list[EntityId] = Field(default_factory=list)
    relevance_to_parent: str = ""
    admissibility_condition: str = ""
    current_status: str = "open"
    blocker_ids: list[EntityId] = Field(default_factory=list)
    holdon_ids: list[EntityId] = Field(default_factory=list)
    certainty_state_id: EntityId | None = None


class DecompositionRecord(TheoryModel):
    """THEORY.md §6.1 "Durable state", §8.1 "Decomposition law",
    and §30.3 "Decomposition faithfulness".

    Durable record of a governed decomposition step.
    """

    id: EntityId
    parent_not_id: EntityId
    child_not_ids: list[EntityId] = Field(default_factory=list)
    materially_increases_determination: bool = True
    faithfulness_notes: str = ""
    identity_preserving: bool = True


class Duty(TheoryModel):
    """THEORY.md §9 "Duty".

    Governed obligation to reduce one or more represented non-achievednesses.
    """

    id: EntityId
    target_not_ids: list[EntityId] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    context: JsonMap = Field(default_factory=dict)
    acceptance_form: str = ""
    admissibility_basis: str = ""


class CertaintyState(TheoryModel):
    """THEORY.md §10 "Certainty".

    Governed certainty attached to the reduction state of a non-achievedness.
    """

    id: EntityId
    target_not_id: EntityId
    achievedness_statement: str = ""
    status_text: str = ""
    governance_basis: str = ""
    evidence_ids: list[EntityId] = Field(default_factory=list)
    committable: bool = False


class CertaintyTransition(TheoryModel):
    """THEORY.md §10.3 "Certainty progression" and §28.3 "Provenance".

    Durable, inspectable record of certainty progression.
    """

    id: EntityId
    target_not_id: EntityId
    from_certainty_state_id: EntityId | None = None
    to_certainty_state_id: EntityId
    rationale: str = ""
    evidence_ids: list[EntityId] = Field(default_factory=list)


class Evidence(TheoryModel):
    """THEORY.md §11 "Evidence".

    Support-bearing content used in governed reduction.
    """

    id: EntityId
    target_not_ids: list[EntityId] = Field(default_factory=list)
    observation: str
    source: str
    context: JsonMap = Field(default_factory=dict)
    support_effect: str = ""
    stage: EvidenceStageKind = EvidenceStageKind.OBSERVATION
    provenance_ids: list[EntityId] = Field(default_factory=list)


class Claim(TheoryModel):
    """THEORY.md §11.4 "Stratification".

    Claim formed above evidence but below proposed commitment.
    """

    id: EntityId
    target_not_id: EntityId
    evidence_ids: list[EntityId] = Field(default_factory=list)
    interpreted_fact: str = ""
    claim_text: str


class ProposedCommitment(TheoryModel):
    """THEORY.md §11.4 "Stratification" and §6.4 "Commitment rule".

    Proposed commitment that remains below accepted durable commitment.
    """

    id: EntityId
    target_not_id: EntityId
    claim_ids: list[EntityId] = Field(default_factory=list)
    evidence_ids: list[EntityId] = Field(default_factory=list)
    justification: str = ""


class Commitment(TheoryModel):
    """THEORY.md §6.4 "Commitment rule" and §10.5 "Closure condition".

    Durable committed achievedness accepted under governance.
    """

    id: EntityId
    target_not_id: EntityId
    achievedness_statement: str
    certainty_state_id: EntityId | None = None
    evidence_ids: list[EntityId] = Field(default_factory=list)
    justification: str = ""


class Unknown(TheoryModel):
    """THEORY.md §12.2 "Unknown as local insufficiency".

    Structured local insufficiency within a larger non-achievedness.
    """

    id: EntityId
    missing_what: str
    why_it_matters: str
    blocking_power: str
    reduction_paths: list[str] = Field(default_factory=list)


class Blocker(TheoryModel):
    """THEORY.md §12.3 "Blocker".

    Represented insufficiency that currently blocks justified continuation.
    """

    id: EntityId
    target_not_id: EntityId
    unknown_id: EntityId | None = None
    blocking_not_id: EntityId | None = None
    why_continuation_is_blocked: str
    required_for_justified_continuation: bool = True


class HoldOnCondition(TheoryModel):
    """THEORY.md §12.4 "HoldOn" and §19.9 "HoldOn-awareness".

    Governed suspension posture over continuation or instantiation.
    """

    id: EntityId
    target_not_id: EntityId
    reason: str
    ordinary_continuation_blocked: bool = True
    ordinary_instantiation_blocked: bool = True
    diagnostic_use_allowed: bool = False
    relevant_conditions: list[str] = Field(default_factory=list)
    resumption_conditions: list[str] = Field(default_factory=list)


class PausePoint(TheoryModel):
    """THEORY.md §6.1 "Durable state" and §23.4 "Pause and resume".

    Durable pause point preserved inside controller state.
    """

    id: EntityId
    target_not_id: EntityId
    reason: str
    required_return_kind: str = ""
    resumption_conditions: list[str] = Field(default_factory=list)


class ReflectionRecord(TheoryModel):
    """THEORY.md §13 "Reflection".

    Retrospective control-intelligence record over a composition subset.
    """

    id: EntityId
    higher_not_id: EntityId
    composition_subset_not_ids: list[EntityId] = Field(default_factory=list)
    coherence_assessment: str = ""
    decomposition_sufficiency: str = ""
    local_drift_notes: list[str] = Field(default_factory=list)
    mistaken_assumptions: list[str] = Field(default_factory=list)
    local_certainty_progression: str = ""
    higher_not_bearing_assessment: str = ""
    reusable_scope_assessment: str = ""
    holdon_respect_assessment: str = ""


class ContemplationRecord(TheoryModel):
    """THEORY.md §14 "Contemplation".

    Prospective control-intelligence record over future paths and reframings.
    """

    id: EntityId
    target_not_id: EntityId
    candidate_paths: list[str] = Field(default_factory=list)
    candidate_subordinate_not_ids: list[EntityId] = Field(default_factory=list)
    upward_reframe_candidates: list[str] = Field(default_factory=list)
    reuse_decisions: list[str] = Field(default_factory=list)
    preferred_path: str = ""
    rationale: str = ""


class Capability(TheoryModel):
    """THEORY.md §15 "Capabilities".

    Reusable means of reducing non-achievedness or advancing justified certainty.
    """

    id: EntityId
    affordance: str
    input_form: str
    output_form: str
    limits: JsonMap = Field(default_factory=dict)
    semantic_role: str
    admissibility_conditions: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    relation_to_evidence: str = ""
    implementing_ability_artifact_id: EntityId | None = None


class GenesisRecord(TheoryModel):
    """THEORY.md §16 "Genesis".

    Controlled emergence of missing capability in service of main reduction.
    """

    id: EntityId
    capability_not_id: EntityId
    missing_capability_description: str
    generated_capability_id: EntityId | None = None
    service_of_not_id: EntityId | None = None
    rationale: str = ""


class GovernabilityEnvelopeState(TheoryModel):
    """THEORY.md §17.1 "Governability envelope" and §31.1 "System form".

    Current state of what lies inside or outside the lawful governability envelope.
    """

    id: EntityId
    closable_not_ids: list[EntityId] = Field(default_factory=list)
    reducible_not_ids: list[EntityId] = Field(default_factory=list)
    correctly_rejectable_not_ids: list[EntityId] = Field(default_factory=list)
    outside_envelope_not_ids: list[EntityId] = Field(default_factory=list)
    boundary_notes: list[str] = Field(default_factory=list)


class BoundaryTopology(TheoryModel):
    """THEORY.md §4.5 "Canonical classes", §4.6 "Semantic interpretation",
    and §4.8 "Soundness requirement".

    BSSC boundary topology and its semantic interpretation.
    """

    id: EntityId
    boundary_class: BoundaryClassKind
    input_carrier_kinds: list[CarrierKind] = Field(default_factory=list)
    output_carrier_kinds: list[CarrierKind] = Field(default_factory=list)
    semantic_interpretation: str = ""
    soundness_requirements: list[str] = Field(default_factory=list)
    sound: bool = True


class BoundaryTransition(TheoryModel):
    """THEORY.md §4.3 "Boundary principle", §4.9 "Structural consequence",
    and §6.1 "Durable state".

    Controlled boundary-carrier transition preserved in durable state.
    """

    id: EntityId
    topology_id: EntityId | None = None
    boundary_class: BoundaryClassKind | None = None
    input_carrier_kinds: list[CarrierKind] = Field(default_factory=list)
    output_carrier_kinds: list[CarrierKind] = Field(default_factory=list)
    semantic_identity: str
    payload_summary: str = ""
    provenance_ids: list[EntityId] = Field(default_factory=list)
    soundness_notes: list[str] = Field(default_factory=list)


class InteractionSurface(TheoryModel):
    """THEORY.md §27 "Inlets, outlets, waits, and resumption" and §31.1 "System form".

    Base interaction-surface record.
    """

    id: EntityId
    surface_type: str
    kind: str
    semantic_identity: str
    related_not_id: EntityId | None = None
    boundary_transition_id: EntityId | None = None
    carrier_kind: CarrierKind | None = None
    payload_summary: str = ""
    provenance_ids: list[EntityId] = Field(default_factory=list)


class Inlet(InteractionSurface):
    """THEORY.md §27.2 "Inlets".

    BSSC-consistent carrier entry into controlled state.
    """

    surface_type: Literal["inlet"] = "inlet"


class Outlet(InteractionSurface):
    """THEORY.md §27.3 "Outlets".

    BSSC-consistent carrier exit preserving semantic continuity.
    """

    surface_type: Literal["outlet"] = "outlet"


class Wait(InteractionSurface):
    """THEORY.md §27.4 "Waits".

    Governed pause pending boundary return for justified continuation.
    """

    surface_type: Literal["wait"] = "wait"
    required_boundary_return: str = ""
    resumption_conditions: list[str] = Field(default_factory=list)


class ResumptionEvent(InteractionSurface):
    """THEORY.md §27.5 "Resumption".

    Governed restoration of admissible continuation.
    """

    surface_type: Literal["resumption"] = "resumption"
    wait_id: EntityId | None = None
    satisfied_conditions: list[str] = Field(default_factory=list)


class HumanContribution(TheoryModel):
    """THEORY.md §23 "Human participation".

    Human participation record, optionally linked to durable evidence.
    """

    id: EntityId
    target_not_id: EntityId | None = None
    contribution_types: list[str] = Field(default_factory=list)
    content: str
    evidence_id: EntityId | None = None
    provenance_ids: list[EntityId] = Field(default_factory=list)


class BSSCAwareness(TheoryModel):
    """THEORY.md §19.8 "BSSC-awareness".

    Required BSSC-awareness carried by every template-bearing artifact.
    """

    admissible_place_in_realization: str = Field(
        validation_alias=AliasChoices("admissible_place_in_realization", "instantiation_zone")
    )
    required_governed_state: str = Field(
        validation_alias=AliasChoices("required_governed_state", "required_state")
    )
    permitted_governed_effect: str = Field(
        validation_alias=AliasChoices("permitted_governed_effect", "permitted_effect")
    )
    may_support: list[str] = Field(default_factory=list)
    may_not_by_itself_justify: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _accept_runtime_digressions(cls, value: object) -> object:
        # Runtime digression: main.py historically emitted a shorter BSSC shape
        # with `instantiation_zone`, `required_state`, `permitted_effect`, and
        # a boolean `not_self_justifying`. Accept that form here so the theory
        # model can validate the live controller schema directly.
        """
        High Level Purpose:
            In circumstances like pure theory typing and serialization boundaries, helps with handling accept runtime digressions.

        Reference to Theory:
            Defines pure theory data structures that correspond directly to the ontology and theory sections implemented in the system.

        Example Input Output:
            Input: `_accept_runtime_digressions(value=3)`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            value: Value for `value` used by `_accept_runtime_digressions`. Expected type: `object`.

        Returns:
            object: Result produced by `_accept_runtime_digressions`.
        """
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "may_not_by_itself_justify" not in payload and payload.get("not_self_justifying") is True:
            payload["may_not_by_itself_justify"] = ["closure"]
        payload.pop("not_self_justifying", None)
        return payload


class HoldOnAwareness(TheoryModel):
    """THEORY.md §19.9 "HoldOn-awareness".

    Required HoldOn-awareness carried by every template-bearing artifact.
    """

    relevant_holdon_blocks_instantiation: bool = Field(
        validation_alias=AliasChoices("relevant_holdon_blocks_instantiation", "blocked_by_holdon")
    )
    diagnostic_use_allowed: bool
    relevant_holdon_conditions: list[str] = Field(default_factory=list)
    can_produce_or_intensify_holdon: bool = False
    resumption_condition: str = ""


class TemplateSchema(TheoryModel):
    """THEORY.md §19.7 "Universal template schema".

    Universal schema that all template-bearing artifacts should carry.
    """

    id: EntityId
    preconditions: list[str] = Field(default_factory=list)
    invariant_core: str
    variation_parameters: list[str] = Field(default_factory=list)
    governed_function: str
    bssc_awareness: BSSCAwareness
    holdon_awareness: HoldOnAwareness
    completion_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)
    harvest_conditions: list[str] = Field(default_factory=list)
    scope_of_reuse: str


class ArtifactBase(TheoryModel):
    """THEORY.md §18.1 "Artifact ontology" and §20.2 "Admission conditions".

    Shared base for all reusable governed residues.
    """

    id: EntityId
    representation: str
    scope: str
    boundary_shape: list[BoundaryShapeTermKind] = Field(default_factory=list)
    provenance_ids: list[EntityId] = Field(default_factory=list)
    reusability: str
    justification: str = ""
    admissibility_conditions: list[str] = Field(default_factory=list)
    related_artifact_ids: list[EntityId] = Field(default_factory=list)


class KnowledgeArtifact(ArtifactBase):
    """THEORY.md §18.3 "Knowledge artifact" and §30.9 "Knowledge exception".

    Sole non-templatic primary reusable artifact class.
    """

    artifact_type: Literal["knowledge"] = "knowledge"
    domain_content: str
    citations: list[str] = Field(default_factory=list)
    index_terms: list[str] = Field(default_factory=list)


class TemplateBearingArtifact(ArtifactBase):
    """THEORY.md §18.2 "Primary division", §19.3 "Universal BSSC-HoldOn
    templating principle", and §19.17 "Admission doctrine".

    Base class for all template-bearing artifacts.
    """

    artifact_type: ArtifactTypeKind
    template_schema: TemplateSchema
    failure_or_escalation_behavior: list[str] = Field(default_factory=list)


class AbilityArtifact(TemplateBearingArtifact):
    """THEORY.md §18.4 "Ability artifact" and §20.3 "Ability-specific conditions".

    Reusable executable procedure admitted under templating discipline.
    """

    artifact_type: Literal["ability"] = "ability"
    executable_form: str
    failure_modes: list[str] = Field(default_factory=list)
    evaluation_artifact_ids: list[EntityId] = Field(default_factory=list)


class CapabilityArtifact(TemplateBearingArtifact):
    """THEORY.md §18.5 "Capability artifact".

    Reusable specification of what may be done under what conditions.
    """

    artifact_type: Literal["capability"] = "capability"
    input_form: str
    output_form: str
    affordance: str
    limits: JsonMap = Field(default_factory=dict)
    relation_to_evidence: str = ""
    implementing_ability_artifact_id: EntityId | None = None


class DutyTemplateArtifact(TemplateBearingArtifact):
    """THEORY.md §18.6 "Duty template artifact" and §20.4
    "Duty-template-specific conditions".

    Reusable governed pattern for recurring duty classes.
    """

    artifact_type: Literal["duty_template"] = "duty_template"
    applicability_conditions: list[str] = Field(default_factory=list)
    parameter_schema: JsonMap = Field(default_factory=dict)
    expected_evidence_forms: list[str] = Field(default_factory=list)
    closure_conditions: list[str] = Field(default_factory=list)
    escalation_conditions: list[str] = Field(default_factory=list)
    rejection_conditions: list[str] = Field(default_factory=list)


class ClosurePatternArtifact(TemplateBearingArtifact):
    """THEORY.md §18.7 "Closure pattern artifact".

    Reusable pattern of how a class of Nots closes with certainty.
    """

    artifact_type: Literal["closure_pattern"] = "closure_pattern"
    supported_not_classes: list[str] = Field(default_factory=list)
    closure_structures: list[str] = Field(default_factory=list)


class RejectionPatternArtifact(TemplateBearingArtifact):
    """THEORY.md §18.8 "Rejection pattern artifact".

    Reusable pattern for honest non-closure.
    """

    artifact_type: Literal["rejection_pattern"] = "rejection_pattern"
    insufficiency_patterns: list[str] = Field(default_factory=list)
    rejection_structures: list[str] = Field(default_factory=list)


class UncertaintyPatternArtifact(TemplateBearingArtifact):
    """THEORY.md §18.9 "Uncertainty pattern artifact".

    Reusable pattern of insufficiency, ambiguity, or instability.
    """

    artifact_type: Literal["uncertainty_pattern"] = "uncertainty_pattern"
    ambiguity_signatures: list[str] = Field(default_factory=list)
    evidence_gap_signatures: list[str] = Field(default_factory=list)
    blocker_signatures: list[str] = Field(default_factory=list)
    stale_holdon_signatures: list[str] = Field(default_factory=list)


class CompositionArtifact(TemplateBearingArtifact):
    """THEORY.md §18.10 "Composition artifact" and §21.1
    "Duty-centered composition principle".

    Reusable project-level realizational composition structure.
    """

    artifact_type: Literal["composition"] = "composition"
    governing_duty_family: str = ""
    admissible_duty_templates: list[EntityId] = Field(default_factory=list)
    required_capabilities: list[EntityId] = Field(default_factory=list)
    preferred_closure_patterns: list[EntityId] = Field(default_factory=list)
    relevant_rejection_patterns: list[EntityId] = Field(default_factory=list)
    relevant_uncertainty_patterns: list[EntityId] = Field(default_factory=list)
    expected_harvest_artifacts: list[ArtifactTypeKind] = Field(default_factory=list)


class EvaluationArtifact(TemplateBearingArtifact):
    """THEORY.md §18.11 "Evaluation artifact".

    Reusable criterion set for checking correctness, adequacy, or reuse quality.
    """

    artifact_type: Literal["evaluation"] = "evaluation"
    criteria: list[str] = Field(default_factory=list)
    test_forms: list[str] = Field(default_factory=list)
    score_functions: list[str] = Field(default_factory=list)
    reuse_quality_checks: list[str] = Field(default_factory=list)


TheoryArtifact: TypeAlias = (
    KnowledgeArtifact
    | AbilityArtifact
    | CapabilityArtifact
    | DutyTemplateArtifact
    | ClosurePatternArtifact
    | RejectionPatternArtifact
    | UncertaintyPatternArtifact
    | CompositionArtifact
    | EvaluationArtifact
)

TemplateBearingTheoryArtifact: TypeAlias = (
    AbilityArtifact
    | CapabilityArtifact
    | DutyTemplateArtifact
    | ClosurePatternArtifact
    | RejectionPatternArtifact
    | UncertaintyPatternArtifact
    | CompositionArtifact
    | EvaluationArtifact
)


class ArtifactInstantiationRecord(TheoryModel):
    """THEORY.md §19.11 "Non-inert residue principle", §19.12
    "Reuse-witness law", and §31.5.2 "Artifact-instantiation law".

    Governed instantiation attempt for an admitted artifact.
    """

    id: EntityId
    artifact_id: EntityId
    target_not_id: EntityId
    in_scope: bool
    holdon_permitted: bool
    freshness_ok: bool = True
    produced_reuse_witness_id: EntityId | None = None
    notes: list[str] = Field(default_factory=list)


class ReuseWitness(TheoryModel):
    """THEORY.md §19.12 "Reuse-witness law".

    Support-bearing witness produced by governed reuse of admitted residue.
    """

    id: EntityId
    artifact_id: EntityId
    target_not_id: EntityId
    produced_effect: str
    evidence_ids: list[EntityId] = Field(default_factory=list)
    support_notes: list[str] = Field(default_factory=list)


class RealizationWitness(TheoryModel):
    """THEORY.md §19.14 "Present-witness principle", §19.15
    "Double-witness requirement for first-instance closure", and
    §31.5.3 "Present-realization law".

    Present realization witness produced within the current governed episode.
    """

    id: EntityId
    target_not_id: EntityId
    produced_support: str
    method: str
    scope_faithful: bool = True
    evidence_ids: list[EntityId] = Field(default_factory=list)


class EvaluationWitness(TheoryModel):
    """THEORY.md §19.15 "Double-witness requirement for first-instance closure"
    and §31.5.3 "Present-realization law".

    Evaluation witness or invariant check paired with a realization witness.
    """

    id: EntityId
    target_not_id: EntityId
    invariant_or_check: str
    passed: bool
    scope_faithful: bool = True
    evidence_ids: list[EntityId] = Field(default_factory=list)


class DiscoveryAudit(TheoryModel):
    """THEORY.md §17.10 "Discovery audit" and §31.5 "Discovery-and-harvest law".

    Mandatory bounded harvest audit over a governed encounter.
    """

    id: EntityId
    run_id: EntityId
    target_not_id: EntityId
    making_conditions: list[str] = Field(default_factory=list)
    reusable_residue_present: bool | None = None
    candidate_artifact_types: list[ArtifactTypeKind] = Field(default_factory=list)
    recommended_representation: str = ""
    scope_and_constraints: list[str] = Field(default_factory=list)
    admission_justified_now: bool | None = None
    boundedness_notes: list[str] = Field(default_factory=list)


class FrontierRejectionRecord(TheoryModel):
    """THEORY.md §17.11 "Frontier rejection doctrine" and §31.6
    "Frontier-rejection law".

    Honest uncertainty-based rejection at the current governability frontier.
    """

    id: EntityId
    rejected_not_id: EntityId
    insufficiency_class: str
    missing_condition: str
    missing_artifact_family_or_capability: str = ""
    nearest_governable_decomposition: str = ""
    bridge_condition: str = ""


class DevelopmentalReuseRecord(TheoryModel):
    """THEORY.md §20.7 "Developmental reuse principle" and §31.5.1
    "Developmental reuse law".

    Record of later governed retrieval and successful in-scope reuse.
    """

    id: EntityId
    source_artifact_id: EntityId
    run_id: EntityId
    target_not_id: EntityId
    retrieved: bool
    in_scope: bool
    reused: bool
    reuse_witness_generated: bool = False
    blocking_condition: str = ""


class PainGainClassification(TheoryModel):
    """THEORY.md §§17.6-17.9, §24.4 "Mandatory run classification",
    and §31.8 "Pain-gain form".

    Developmental classification pair plus typed gain where present.
    """

    id: EntityId
    run_id: EntityId
    pain: PainKind
    gain: GainKind
    gain_type: GainTypeKind | None = None
    four_cell_class: str = ""
    discovery_audit_id: EntityId | None = None
    frontier_rejection_record_id: EntityId | None = None
    developmental_reuse_record_ids: list[EntityId] = Field(default_factory=list)


class Product(TheoryModel):
    """THEORY.md §25 "Products".

    Secondary product or witness meaningful only relative to reduction.
    """

    id: EntityId
    semantic_identity: str
    participates_in_not_id: EntityId | None = None
    witness_description: str = ""
    commitment_id: EntityId | None = None
    accepted_for_achievedness: bool = False


class OntologyEntry(TheoryModel):
    """THEORY.md §26 "Ontology and naming".

    Ontological stabilization record across authoritative, working, and embedded
    semantic layers.
    """

    id: EntityId
    object_kind: OntologyObjectKind
    semantic_identity: str
    authoritative_semantics: JsonMap = Field(default_factory=dict)
    working_semantics: JsonMap = Field(default_factory=dict)
    embedded_semantics: JsonMap = Field(default_factory=dict)
    residence_layer: OntologyResidenceKind = OntologyResidenceKind.AUTHORITATIVE_DURABLE_STATE


class ProvenanceLink(TheoryModel):
    """THEORY.md §6.1 "Durable state" and §28.3 "Provenance".

    Recoverable provenance edge between semantically meaningful objects.
    """

    id: EntityId
    source_id: EntityId
    target_id: EntityId
    relation: str
    notes: list[str] = Field(default_factory=list)


class TraceStep(TheoryModel):
    """THEORY.md §6.2 "Ledger", §28.1 "Trace purpose", and §28.2
    "Causal trace form".

    Semantically meaningful step within the durable trace/ledger.
    """

    id: EntityId
    step_index: int
    target_not_id: EntityId | None = None
    description: str
    chosen_branch: str = ""
    rejected_branch: str = ""
    evidence_ids: list[EntityId] = Field(default_factory=list)
    capability_ids: list[EntityId] = Field(default_factory=list)
    artifact_ids: list[EntityId] = Field(default_factory=list)
    commitment_id: EntityId | None = None
    result: str = ""


class BudgetCounter(TheoryModel):
    """THEORY.md §21.5 "Proposal-budget principle" and §31.1 "System form".

    Budget counter for one expensive-motion family.
    """

    kind: ProposalBudgetKind
    limit: int | None = None
    spent: int = 0


class ProposalBudgetState(TheoryModel):
    """THEORY.md §21.4 "Dominant distinction principle", §21.5
    "Proposal-budget principle", and §21.8 "Spin response doctrine".

    Active expensive-motion budgets and anti-spin metadata for a Not.
    """

    target_not_id: EntityId | None = None
    dominant_distinction: str = ""
    discovery_refinement: BudgetCounter = Field(
        default_factory=lambda: BudgetCounter(kind=ProposalBudgetKind.DISCOVERY_REFINEMENT)
    )
    supplementation: BudgetCounter = Field(
        default_factory=lambda: BudgetCounter(kind=ProposalBudgetKind.SUPPLEMENTATION)
    )
    reframing: BudgetCounter = Field(
        default_factory=lambda: BudgetCounter(kind=ProposalBudgetKind.REFRAMING)
    )
    uncertainty_reassessment: BudgetCounter = Field(
        default_factory=lambda: BudgetCounter(kind=ProposalBudgetKind.UNCERTAINTY_REASSESSMENT)
    )
    artifact_proposal: BudgetCounter = Field(
        default_factory=lambda: BudgetCounter(kind=ProposalBudgetKind.ARTIFACT_PROPOSAL)
    )
    spin_detected: bool = False
    monotone_progress_notes: list[str] = Field(default_factory=list)


class GovernanceState(TheoryModel):
    """THEORY.md §5.3 "What the controller governs", §29.2
    "Restraint mechanisms", and §30 "Invariants".

    Governance-side thresholds, checks, and restraint structures.
    """

    active_invariants: list[str] = Field(default_factory=list)
    commitment_thresholds: list[str] = Field(default_factory=list)
    artifact_admission_thresholds: list[str] = Field(default_factory=list)
    faithfulness_checks: list[str] = Field(default_factory=list)
    envelope_checks: list[str] = Field(default_factory=list)
    restraint_mechanisms: list[str] = Field(default_factory=list)


class Run(TheoryModel):
    """THEORY.md §24 "Runs".

    Bounded governed attempt to reduce represented non-achievedness under
    current conditions.
    """

    id: EntityId
    initial_not_ids: list[EntityId] = Field(default_factory=list)
    starting_state_ref: str = ""
    step_history_ids: list[EntityId] = Field(default_factory=list)
    produced_manifestation_ids: list[EntityId] = Field(default_factory=list)
    outcome: RunOutcomeKind
    classification_record_id: EntityId | None = None


class RunRecord(TheoryModel):
    """THEORY.md §24.4 "Mandatory run classification" and §31.1 "System form".

    Run classification and harvest record for formal-system coordinate R.
    """

    id: EntityId
    run_id: EntityId
    outcome: RunOutcomeKind
    classification_id: EntityId
    discovery_audit_id: EntityId | None = None
    harvested_artifact_ids: list[EntityId] = Field(default_factory=list)
    frontier_rejection_record_id: EntityId | None = None
    developmental_reuse_record_ids: list[EntityId] = Field(default_factory=list)


InteractionSurfaceRecord: TypeAlias = Inlet | Outlet | Wait | ResumptionEvent


class DurableState(TheoryModel):
    """THEORY.md §6.1 "Durable state".

    Minimum durable state plus theory-required support records.
    """

    semantic_units: list[SemanticUnit] = Field(default_factory=list)
    non_achievednesses: list[NonAchievedness] = Field(default_factory=list)
    decomposition_records: list[DecompositionRecord] = Field(default_factory=list)
    duties: list[Duty] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    proposed_commitments: list[ProposedCommitment] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    certainty_states: list[CertaintyState] = Field(default_factory=list)
    certainty_transitions: list[CertaintyTransition] = Field(default_factory=list)
    unknowns: list[Unknown] = Field(default_factory=list)
    blockers: list[Blocker] = Field(default_factory=list)
    holdon_conditions: list[HoldOnCondition] = Field(default_factory=list)
    pause_points: list[PausePoint] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    genesis_records: list[GenesisRecord] = Field(default_factory=list)
    knowledge_artifacts: list[KnowledgeArtifact] = Field(default_factory=list)
    template_bearing_artifacts: list[TemplateBearingTheoryArtifact] = Field(default_factory=list)
    artifact_instantiations: list[ArtifactInstantiationRecord] = Field(default_factory=list)
    reuse_witnesses: list[ReuseWitness] = Field(default_factory=list)
    realization_witnesses: list[RealizationWitness] = Field(default_factory=list)
    evaluation_witnesses: list[EvaluationWitness] = Field(default_factory=list)
    human_contributions: list[HumanContribution] = Field(default_factory=list)
    boundary_topologies: list[BoundaryTopology] = Field(default_factory=list)
    boundary_transitions: list[BoundaryTransition] = Field(default_factory=list)
    inlets: list[Inlet] = Field(default_factory=list)
    outlets: list[Outlet] = Field(default_factory=list)
    waits: list[Wait] = Field(default_factory=list)
    resumptions: list[ResumptionEvent] = Field(default_factory=list)
    reflection_records: list[ReflectionRecord] = Field(default_factory=list)
    contemplation_records: list[ContemplationRecord] = Field(default_factory=list)
    discovery_audits: list[DiscoveryAudit] = Field(default_factory=list)
    frontier_rejections: list[FrontierRejectionRecord] = Field(default_factory=list)
    developmental_reuse_records: list[DevelopmentalReuseRecord] = Field(default_factory=list)
    pain_gain_classifications: list[PainGainClassification] = Field(default_factory=list)
    products: list[Product] = Field(default_factory=list)
    template_schemas: list[TemplateSchema] = Field(default_factory=list)
    ontology_entries: list[OntologyEntry] = Field(default_factory=list)
    provenance_links: list[ProvenanceLink] = Field(default_factory=list)
    trace_steps: list[TraceStep] = Field(default_factory=list)
    runs: list[Run] = Field(default_factory=list)
    run_records: list[RunRecord] = Field(default_factory=list)


class FormalSystem(TheoryModel):
    """THEORY.md §31.1 "System form".

    Formal-system view of the controller state tuple:
    S = (N, D, O, E, C, K, A, Sigma, H, G, I, P, T, HoldOn, R, E_C, B).
    """

    non_achievednesses: list[NonAchievedness] = Field(default_factory=list, alias="N")
    duties: list[Duty] = Field(default_factory=list, alias="D")
    ontology: list[OntologyEntry] = Field(default_factory=list, alias="O")
    evidence: list[Evidence] = Field(default_factory=list, alias="E")
    capabilities: list[Capability] = Field(default_factory=list, alias="C")
    knowledge_artifacts: list[KnowledgeArtifact] = Field(default_factory=list, alias="K")
    template_bearing_artifacts: list[TemplateBearingTheoryArtifact] = Field(default_factory=list, alias="A")
    durable_state: DurableState = Field(default_factory=DurableState, alias="Sigma")
    trace_history: list[TraceStep] = Field(default_factory=list, alias="H")
    governance: GovernanceState = Field(default_factory=GovernanceState, alias="G")
    interaction_surfaces: list[InteractionSurfaceRecord] = Field(default_factory=list, alias="I")
    products: list[Product] = Field(default_factory=list, alias="P")
    template_schemas: list[TemplateSchema] = Field(default_factory=list, alias="T")
    holdon_state: list[HoldOnCondition] = Field(default_factory=list, alias="HoldOn")
    run_records: list[RunRecord] = Field(default_factory=list, alias="R")
    governability_envelope_state: GovernabilityEnvelopeState = Field(
        default_factory=lambda: GovernabilityEnvelopeState(id="envelope"),
        alias="E_C",
    )
    proposal_budgets: list[ProposalBudgetState] = Field(default_factory=list, alias="B")


__all__ = [
    "ArtifactBase",
    "ArtifactInstantiationRecord",
    "ArtifactTypeKind",
    "AbilityArtifact",
    "Blocker",
    "BoundaryClassKind",
    "BoundaryLaneKind",
    "BoundaryShapeAtomKind",
    "BoundaryShapeTermKind",
    "BoundaryTopology",
    "BoundaryTransition",
    "BSSCAwareness",
    "Capability",
    "CapabilityArtifact",
    "CarrierKind",
    "CertaintyState",
    "CertaintyTransition",
    "Claim",
    "Commitment",
    "CompositionArtifact",
    "ContemplationRecord",
    "DecompositionRecord",
    "DevelopmentalReuseRecord",
    "DiscoveryAudit",
    "DurableState",
    "Duty",
    "DutyTemplateArtifact",
    "EntityId",
    "EvaluationArtifact",
    "EvaluationWitness",
    "Evidence",
    "EvidenceStageKind",
    "FormalSystem",
    "FrontierRejectionRecord",
    "GainKind",
    "GainTypeKind",
    "GenesisRecord",
    "GovernabilityEnvelopeState",
    "GovernanceState",
    "HoldOnAwareness",
    "HoldOnCondition",
    "HumanContribution",
    "Inlet",
    "InteractionSurface",
    "InteractionSurfaceRecord",
    "JsonMap",
    "KnowledgeArtifact",
    "NonAchievedness",
    "OntologyEntry",
    "OntologyObjectKind",
    "OntologyResidenceKind",
    "Outlet",
    "PainGainClassification",
    "PainKind",
    "PausePoint",
    "Product",
    "ProposalBudgetKind",
    "ProposalBudgetState",
    "ProposedCommitment",
    "ProvenanceLink",
    "RealizationWitness",
    "ReflectionRecord",
    "ResumptionEvent",
    "ReuseWitness",
    "Run",
    "RunOutcomeKind",
    "RunRecord",
    "SemanticUnit",
    "TemplateBearingArtifact",
    "TemplateBearingTheoryArtifact",
    "TemplateSchema",
    "TheoryArtifact",
    "TheoryModel",
    "TraceStep",
    "Unknown",
    "Wait",
]
