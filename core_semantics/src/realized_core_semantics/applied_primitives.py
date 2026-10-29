# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from enum import Enum
from typing import Any

from realized_core_semantics.values import json_safe, utc_now

__all__ = [
    "ABILITY_SCRIPT_DEPENDENCIES",
    "ARTIFACT_ADMISSION_LEVELS",
    "ARTIFACT_REPRESENTATION_LEVELS",
    "ARTIFACT_REUSE_LEVELS",
    "ARTIFACT_TYPES",
    "ArtifactAdmission",
    "ArtifactRepresentation",
    "ArtifactReuse",
    "ArtifactType",
    "BOUNDARY_OUTPUT_TERMS",
    "BOUNDARY_SHAPE_TERMS",
    "BOUNDARY_WRITE_TERMS",
    "BoundaryShapeTerm",
    "CLOSURE_RULE_LEVELS",
    "ClaimStance",
    "ClosureRule",
    "DecompositionMode",
    "EvidencePolarity",
    "GAIN_CLASSES",
    "GainClass",
    "LEARNING_RELATIONS",
    "LearningRelation",
    "NOT_DEGREE_VALUES",
    "NOT_MISALIGNMENT_VALUES",
    "NOT_ORIGIN_VALUES",
    "NOT_REMAINDER_SHAPE_VALUES",
    "NodeOrigin",
    "NotDegreeKind",
    "NotMisalignmentKind",
    "NotOriginKind",
    "NotRemainderShapeKind",
    "PAIN_CLASSES",
    "PRIORITY_LEVELS",
    "PURE_THEORY_GAIN_VALUES",
    "PURE_THEORY_PAIN_VALUES",
    "PURE_THEORY_TYPES_ENABLED",
    "PYTHON_ARTIFACT_REPRESENTATIONS",
    "PainClass",
    "PauseBoundary",
    "PriorityLevel",
    "PureTheoryAbilityArtifact",
    "PureTheoryBSSCAwareness",
    "PureTheoryCapabilityArtifact",
    "PureTheoryClosurePatternArtifact",
    "PureTheoryCompositionArtifact",
    "PureTheoryDutyTemplateArtifact",
    "PureTheoryEvaluationArtifact",
    "PureTheoryGainKind",
    "PureTheoryHoldOnAwareness",
    "PureTheoryKnowledgeArtifact",
    "PureTheoryPainKind",
    "PureTheoryRejectionPatternArtifact",
    "PureTheoryTemplateSchema",
    "PureTheoryUncertaintyPatternArtifact",
    "RunOutcome",
    "RuntimeStrEnum",
    "SUPPORT_SCORE_LEVELS",
    "SupportScore",
    "TEMPLATE_BEARING_ARTIFACT_TYPES",
    "THEORY_VERSION",
    "THREE_LEVELS",
    "ThreeLevel",
    "json_safe",
    "utc_now",
]

try:
    from realized_core_semantics.theory import (
        AbilityArtifact as PureTheoryAbilityArtifact,
        ArtifactTypeKind as ArtifactType,
        BoundaryShapeTermKind as BoundaryShapeTerm,
        BSSCAwareness as PureTheoryBSSCAwareness,
        CapabilityArtifact as PureTheoryCapabilityArtifact,
        ClosurePatternArtifact as PureTheoryClosurePatternArtifact,
        CompositionArtifact as PureTheoryCompositionArtifact,
        DutyTemplateArtifact as PureTheoryDutyTemplateArtifact,
        EvaluationArtifact as PureTheoryEvaluationArtifact,
        GainKind as PureTheoryGainKind,
        HoldOnAwareness as PureTheoryHoldOnAwareness,
        KnowledgeArtifact as PureTheoryKnowledgeArtifact,
        NonAchievednessDegreeKind as NotDegreeKind,
        NonAchievednessMisalignmentKind as NotMisalignmentKind,
        NonAchievednessOriginKind as NotOriginKind,
        PainKind as PureTheoryPainKind,
        RejectionPatternArtifact as PureTheoryRejectionPatternArtifact,
        RemainderShapeKind as NotRemainderShapeKind,
        TemplateSchema as PureTheoryTemplateSchema,
        UncertaintyPatternArtifact as PureTheoryUncertaintyPatternArtifact,
    )

    PURE_THEORY_TYPES_ENABLED = True
except Exception:
    PURE_THEORY_TYPES_ENABLED = False

    class ArtifactType(str, Enum):
        KNOWLEDGE = "knowledge"
        ABILITY = "ability"
        CAPABILITY = "capability"
        DUTY_TEMPLATE = "duty_template"
        CLOSURE_PATTERN = "closure_pattern"
        REJECTION_PATTERN = "rejection_pattern"
        UNCERTAINTY_PATTERN = "uncertainty_pattern"
        COMPOSITION = "composition"
        EVALUATION = "evaluation"

    class BoundaryShapeTerm(str, Enum):
        INPUT_VALUE = "a*"
        INPUT_REFERENCE = "a'*"
        READ_VALUE = "b*"
        READ_REFERENCE = "b'*"
        WRITE_VALUE = "c*"
        WRITE_REFERENCE = "c'*"
        OUTPUT_VALUE = "d*"
        OUTPUT_REFERENCE = "d'*"

    class NotMisalignmentKind(str, Enum):
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

    class NotOriginKind(str, Enum):
        PROMPT = "prompt"
        MODEL = "model"
        TOOL = "tool"
        KNOWLEDGE = "knowledge"
        CONSTRAINT = "constraint"
        ONTOLOGICAL = "ontological"

    class NotDegreeKind(str, Enum):
        NULL = "null"
        RESIDUAL = "residual"
        PARTIAL = "partial"
        DOMINANT = "dominant"
        TOTAL = "total"
        CATEGORY_ERROR = "category_error"

    class NotRemainderShapeKind(str, Enum):
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

    PureTheoryBSSCAwareness = None
    PureTheoryKnowledgeArtifact = None
    PureTheoryAbilityArtifact = None
    PureTheoryCapabilityArtifact = None
    PureTheoryDutyTemplateArtifact = None
    PureTheoryClosurePatternArtifact = None
    PureTheoryRejectionPatternArtifact = None
    PureTheoryUncertaintyPatternArtifact = None
    PureTheoryCompositionArtifact = None
    PureTheoryEvaluationArtifact = None
    PureTheoryHoldOnAwareness = None
    PureTheoryTemplateSchema = None
    PureTheoryPainKind = None
    PureTheoryGainKind = None


THEORY_VERSION = "2.2.2"


class RuntimeStrEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class ThreeLevel(RuntimeStrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PriorityLevel(RuntimeStrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClosureRule(RuntimeStrEnum):
    LIGHT = "light"
    NORMAL = "normal"
    STRICT = "strict"


class SupportScore(RuntimeStrEnum):
    VERY_BAD = "very_bad"
    BAD = "bad"
    OK = "ok"


class PainClass(RuntimeStrEnum):
    NO_PAIN = "no_pain"
    PAIN = "pain"


class GainClass(RuntimeStrEnum):
    NO_GAIN = "no_gain"
    GAIN = "gain"


class DecompositionMode(RuntimeStrEnum):
    AND = "AND"
    OR = "OR"


class NodeOrigin(RuntimeStrEnum):
    CONTROLLER = "controller"
    PROMPT = "prompt"
    REFRAMING = "reframing"


class EvidencePolarity(RuntimeStrEnum):
    SUPPORT = "support"
    COUNTER = "counter"


class ClaimStance(RuntimeStrEnum):
    SUPPORTS = "supports"
    COUNTERS = "counters"


class PauseBoundary(RuntimeStrEnum):
    RESUME_SIGNAL = "resume_signal"
    EVIDENCE_ATTACHMENT = "evidence_attachment"
    HUMAN_CONTRIBUTION = "human_contribution"
    CAPABILITY_EMERGENCE = "capability_emergence"


class ArtifactReuse(RuntimeStrEnum):
    INSTANCE_ONLY = "instance_only"
    LOCAL_REUSE = "local_reuse"
    BROAD_REUSE = "broad_reuse"


class ArtifactAdmission(RuntimeStrEnum):
    REJECTED = "rejected"
    CANDIDATE = "candidate"
    ADMITTED = "admitted"


class ArtifactRepresentation(RuntimeStrEnum):
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    SCHEMA = "schema"
    PYTHON_SCRIPT = "python_script"
    SHELL_SCRIPT = "shell_script"
    ANSIBLE_PLAYBOOK = "ansible_playbook"
    WASM_MODULE = "wasm_module"
    PYTHON_MODULE = "python_module"
    MARKDOWN = "markdown"
    CODE = "code"


class LearningRelation(RuntimeStrEnum):
    NEW_FAMILY = "new_family"
    INSTANCE_OF_EXISTING = "instance_of_existing"
    REFINES_EXISTING = "refines_existing"
    EXTENDS_PARAMETERS = "extends_parameters"


class RunOutcome(Enum):
    COMPLETED = "completed"
    PAUSED = "paused"
    INCOMPLETE = "incomplete"
    ONGOING = "ongoing"


THREE_LEVELS = tuple(item.value for item in ThreeLevel)
PRIORITY_LEVELS = tuple(item.value for item in PriorityLevel)
CLOSURE_RULE_LEVELS = tuple(item.value for item in ClosureRule)
SUPPORT_SCORE_LEVELS = tuple(item.value for item in SupportScore)
BOUNDARY_SHAPE_TERMS = tuple(item.value for item in BoundaryShapeTerm)
NOT_MISALIGNMENT_VALUES = tuple(item.value for item in NotMisalignmentKind)
NOT_ORIGIN_VALUES = tuple(item.value for item in NotOriginKind)
NOT_DEGREE_VALUES = tuple(item.value for item in NotDegreeKind)
NOT_REMAINDER_SHAPE_VALUES = tuple(item.value for item in NotRemainderShapeKind)
BOUNDARY_WRITE_TERMS = frozenset({BoundaryShapeTerm.WRITE_VALUE, BoundaryShapeTerm.WRITE_REFERENCE})
BOUNDARY_OUTPUT_TERMS = frozenset({BoundaryShapeTerm.OUTPUT_VALUE, BoundaryShapeTerm.OUTPUT_REFERENCE})
PURE_THEORY_PAIN_VALUES = tuple(item.value for item in PureTheoryPainKind) if PureTheoryPainKind is not None else ()
PURE_THEORY_GAIN_VALUES = tuple(item.value for item in PureTheoryGainKind) if PureTheoryGainKind is not None else ()
PAIN_CLASSES = tuple(value for value in dict.fromkeys([item.value for item in PainClass] + list(PURE_THEORY_PAIN_VALUES)))
GAIN_CLASSES = tuple(value for value in dict.fromkeys([item.value for item in GainClass] + list(PURE_THEORY_GAIN_VALUES)))
ARTIFACT_REUSE_LEVELS = tuple(item.value for item in ArtifactReuse)
ARTIFACT_ADMISSION_LEVELS = tuple(item.value for item in ArtifactAdmission)
ARTIFACT_REPRESENTATION_LEVELS = tuple(item.value for item in ArtifactRepresentation)
PYTHON_ARTIFACT_REPRESENTATIONS = (
    ArtifactRepresentation.PYTHON_SCRIPT.value,
    ArtifactRepresentation.PYTHON_MODULE.value,
)
ABILITY_SCRIPT_DEPENDENCIES = ("msgspec", "orjson")
ARTIFACT_TYPES = tuple(item.value for item in ArtifactType)
TEMPLATE_BEARING_ARTIFACT_TYPES = tuple(
    artifact_type for artifact_type in ARTIFACT_TYPES if artifact_type != "knowledge"
)
LEARNING_RELATIONS = (
    LearningRelation.NEW_FAMILY.value,
    LearningRelation.INSTANCE_OF_EXISTING.value,
    LearningRelation.REFINES_EXISTING.value,
    LearningRelation.EXTENDS_PARAMETERS.value,
)
