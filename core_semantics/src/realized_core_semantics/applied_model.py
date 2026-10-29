# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from realized_core_semantics.applied_primitives import (
    ABILITY_SCRIPT_DEPENDENCIES,
    ARTIFACT_ADMISSION_LEVELS,
    ARTIFACT_REPRESENTATION_LEVELS,
    ARTIFACT_REUSE_LEVELS,
    ARTIFACT_TYPES,
    BOUNDARY_OUTPUT_TERMS,
    BOUNDARY_SHAPE_TERMS,
    BOUNDARY_WRITE_TERMS,
    CLOSURE_RULE_LEVELS,
    GAIN_CLASSES,
    LEARNING_RELATIONS,
    NOT_DEGREE_VALUES,
    NOT_MISALIGNMENT_VALUES,
    NOT_ORIGIN_VALUES,
    NOT_REMAINDER_SHAPE_VALUES,
    PAIN_CLASSES,
    PRIORITY_LEVELS,
    PURE_THEORY_GAIN_VALUES,
    PURE_THEORY_PAIN_VALUES,
    PURE_THEORY_TYPES_ENABLED,
    PYTHON_ARTIFACT_REPRESENTATIONS,
    SUPPORT_SCORE_LEVELS,
    TEMPLATE_BEARING_ARTIFACT_TYPES,
    THEORY_VERSION,
    THREE_LEVELS,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BoundaryShapeTerm,
    ClaimStance,
    ClosureRule,
    DecompositionMode,
    EvidencePolarity,
    GainClass,
    LearningRelation,
    NodeOrigin,
    NotDegreeKind,
    NotMisalignmentKind,
    NotOriginKind,
    NotRemainderShapeKind,
    PainClass,
    PauseBoundary,
    PriorityLevel,
    PureTheoryAbilityArtifact,
    PureTheoryBSSCAwareness,
    PureTheoryCapabilityArtifact,
    PureTheoryClosurePatternArtifact,
    PureTheoryCompositionArtifact,
    PureTheoryDutyTemplateArtifact,
    PureTheoryEvaluationArtifact,
    PureTheoryGainKind,
    PureTheoryHoldOnAwareness,
    PureTheoryKnowledgeArtifact,
    PureTheoryPainKind,
    PureTheoryRejectionPatternArtifact,
    PureTheoryTemplateSchema,
    PureTheoryUncertaintyPatternArtifact,
    RunOutcome,
    RuntimeStrEnum,
    SupportScore,
    ThreeLevel,
    json_safe,
    utc_now,
)
from realized_core_semantics.applied_primitives import __all__ as _primitive_exports
from realized_core_semantics.proposals import (
    ProposalGovernanceStatus,
    ProposalType,
    SupplementMode,
)

__all__ = [
    *_primitive_exports,
    "Artifact",
    "BSSCCarrier",
    "Capability",
    "Claim",
    "Commitment",
    "ControllerFeatureToggles",
    "CrossBoundaryResult",
    "DiscoveryAudit",
    "EdgeType",
    "Evidence",
    "GovernanceRules",
    "GraphEdge",
    "HumanContribution",
    "LLMSupplementReceipt",
    "LLMSupplementResult",
    "NodeStatus",
    "OntologyEntry",
    "PausePoint",
    "Product",
    "ProposalGovernanceStatus",
    "ProposalObject",
    "ProposalType",
    "ProposedCommitment",
    "Result",
    "RuntimeDeterminismPolicy",
    "SemanticNode",
    "StepRecord",
    "SupplementMode",
    "SupportView",
    "enum_text",
]


def enum_text(value: Any) -> str:
    """
    High Level Purpose:
        In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with handling enum text.

    Reference to Theory:
        Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

    Example Input Output:
        Input: `enum_text(value=3)`
        Output: 'F = m * a'

    Args:
        value: Value for `value` used by `enum_text`. Expected type: `Any`.

    Returns:
        str: Result produced by `enum_text`.
    """
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class NodeStatus(Enum):
    OPEN = "open"
    BLOCKED = "blocked"
    CLOSABLE = "closable"
    CLOSED = "closed"
    INADMISSIBLE = "inadmissible"
    INCOMPLETE = "incomplete"
    PAUSED = "paused"


class Result(Enum):
    CLOSED = "closed"
    PAUSED = "paused"
    INCOMPLETE = "incomplete"
    CONTINUE = "continue"
    DEFERRED = "deferred"


class EdgeType(Enum):
    REFINES = "refines"
    DEPENDS_ON = "depends_on"
    SUPPORTED_BY = "supported_by"
    BLOCKS = "blocks"
    ALTERNATIVE_TO = "alternative_to"
    REFRAMES_TO = "reframes_to"
    CLOSES_TO = "closes_to"


@dataclass
class CrossBoundaryResult:
    ok: bool
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    parsed_output: Any = None
    result: Any = None
    answer: str = ""
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)


@dataclass
class BSSCCarrier:
    id: str
    kind: str
    semantic_identity: str
    payload: dict[str, Any]
    provenance: list[str]
    created_at: str
    theory_version: str = THEORY_VERSION

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BSSCCarrier":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'BSSCCarrier': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            kind=data["kind"],
            semantic_identity=data["semantic_identity"],
            payload=data.get("payload", {}),
            provenance=list(data.get("provenance", [])),
            created_at=data["created_at"],
            theory_version=data.get("theory_version", THEORY_VERSION),
        )


@dataclass
class SemanticNode:
    id: str
    semantic_unit: str
    role: str = "generic"
    description: str = ""
    boundary_shape: tuple[BoundaryShapeTerm, ...] = field(
        default_factory=lambda: (BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE)
    )
    decomposition_mode: DecompositionMode = DecompositionMode.AND
    closure_threshold: ClosureRule = ClosureRule.NORMAL
    evidence_required: bool = False
    required: bool = True
    depth: int = 0
    priority_bias: PriorityLevel = PriorityLevel.MEDIUM
    parent_id: str | None = None
    origin: NodeOrigin = NodeOrigin.CONTROLLER
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def not_label(self) -> str:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with handling not label.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `not_label()`
            Output: 'F = m * a'

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            str: Result produced by `not_label`.
        """
        return f"Not<{self.semantic_unit}>"

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SemanticNode":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'SemanticNode': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import (
            normalize_boundary_shape,
            normalize_decomposition_mode,
            normalize_closure_rule,
            normalize_priority,
            normalize_node_origin,
        )

        return cls(
            id=data["id"],
            semantic_unit=data["semantic_unit"],
            role=data.get("role", "generic"),
            description=data.get("description", ""),
            boundary_shape=normalize_boundary_shape(data.get("boundary_shape")),
            decomposition_mode=normalize_decomposition_mode(data.get("decomposition_mode", DecompositionMode.AND)),
            closure_threshold=normalize_closure_rule(data.get("closure_threshold", ClosureRule.NORMAL)),
            evidence_required=bool(data.get("evidence_required", False)),
            required=bool(data.get("required", True)),
            depth=int(data.get("depth", 0)),
            priority_bias=normalize_priority(data.get("priority_bias", PriorityLevel.MEDIUM)),
            parent_id=data.get("parent_id"),
            origin=normalize_node_origin(data.get("origin", NodeOrigin.CONTROLLER)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class GraphEdge:
    src: str
    dst: str
    type: EdgeType
    weight: PriorityLevel = PriorityLevel.MEDIUM
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return {
            "src": self.src,
            "dst": self.dst,
            "type": self.type.value,
            "weight": self.weight,
            "metadata": json_safe(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphEdge":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'GraphEdge': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_priority

        return cls(
            src=data["src"],
            dst=data["dst"],
            type=EdgeType(data["type"]),
            weight=normalize_priority(data.get("weight", PriorityLevel.MEDIUM)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class Evidence:
    id: str
    node_id: str
    observation: str
    source: str
    context: dict[str, Any]
    support_effect: ThreeLevel
    confidence: ThreeLevel
    polarity: EvidencePolarity = EvidencePolarity.SUPPORT
    provenance: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: Evidence(statement='F = m * a')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Evidence': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_three_level, normalize_evidence_polarity

        return cls(
            id=data["id"],
            node_id=data["node_id"],
            observation=data["observation"],
            source=data["source"],
            context=dict(data.get("context", {})),
            support_effect=normalize_three_level(
                data.get("support_effect", data.get("support_strength", ThreeLevel.MEDIUM)),
                default=ThreeLevel.MEDIUM,
            ),
            confidence=normalize_three_level(data.get("confidence", ThreeLevel.MEDIUM), default=ThreeLevel.MEDIUM),
            polarity=normalize_evidence_polarity(data.get("polarity", EvidencePolarity.SUPPORT)),
            provenance=list(data.get("provenance", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class Capability:
    id: str
    affordance: str
    input_form: str
    output_form: str
    limits: dict[str, Any]
    semantic_role: str
    service_axis: str = "governed_reduction"
    realizer: str = "controller"
    validated: bool = False
    provenance: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Capability":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Capability': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            affordance=data["affordance"],
            input_form=data["input_form"],
            output_form=data["output_form"],
            limits=dict(data.get("limits", {})),
            semantic_role=data["semantic_role"],
            service_axis=data.get("service_axis", "governed_reduction"),
            realizer=data.get("realizer", "controller"),
            validated=bool(data.get("validated", False)),
            provenance=list(data.get("provenance", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class HumanContribution:
    id: str
    content: str
    related_node_id: str
    provenance: list[str]
    accepted: bool = True
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HumanContribution":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'HumanContribution': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            content=data["content"],
            related_node_id=data["related_node_id"],
            provenance=list(data.get("provenance", [])),
            accepted=bool(data.get("accepted", True)),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class Product:
    id: str
    node_id: str
    content: dict[str, Any]
    committed: bool
    provenance: list[str]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Product":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Product': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            content=dict(data.get("content", {})),
            committed=bool(data.get("committed", False)),
            provenance=list(data.get("provenance", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class Artifact:
    """Canonical in-memory artifact record.

    In memory, the artifact identifier is always `id`.
    External interfaces may serialize the same identifier under the field name
    `artifact_id` for DB rows, CLI payloads, and YAML metadata, but hydrated
    `Artifact` objects should be addressed as `artifact.id`.
    """

    id: str
    artifact_type: ArtifactType
    title: str
    representation: ArtifactRepresentation
    function_bit: int
    scope: str
    provenance: list[str]
    reusability: ArtifactReuse
    admissibility: ArtifactAdmission
    template_schema: dict[str, Any]
    learning_relation: LearningRelation
    related_artifact_ids: list[str]
    content: dict[str, Any]
    justification: str
    boundary_shape: tuple[BoundaryShapeTerm, ...] = field(default_factory=lambda: (BoundaryShapeTerm.OUTPUT_VALUE,))
    constraints: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Artifact":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Artifact': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import (
            normalize_artifact_admission,
            normalize_artifact_representation,
            normalize_artifact_reuse,
            normalize_artifact_type,
            normalize_boundary_shape,
            normalize_function_bit,
            normalize_learning_relation,
        )
        content = dict(data.get("content", {}))
        if isinstance(data.get("controller_features"), Mapping) and "controller_features" not in content:
            content["controller_features"] = ControllerFeatureToggles.from_dict(
                dict(data.get("controller_features", {}))
            ).to_dict()

        return cls(
            id=data["id"],
            artifact_type=normalize_artifact_type(data.get("artifact_type", "knowledge")),
            title=data.get("title", ""),
            representation=normalize_artifact_representation(
                data.get("representation", "json"),
                artifact_type=data.get("artifact_type", "knowledge"),
            ),
            function_bit=normalize_function_bit(data.get("function_bit", 0)),
            scope=data.get("scope", ""),
            provenance=list(data.get("provenance", [])),
            reusability=normalize_artifact_reuse(data.get("reusability", "local_reuse")),
            admissibility=normalize_artifact_admission(data.get("admissibility", "candidate")),
            template_schema=dict(data.get("template_schema", {})),
            learning_relation=normalize_learning_relation(data.get("learning_relation", "new_family")),
            related_artifact_ids=list(data.get("related_artifact_ids", [])),
            content=content,
            justification=data.get("justification", ""),
            boundary_shape=normalize_boundary_shape(data.get("boundary_shape", (BoundaryShapeTerm.OUTPUT_VALUE,))),
            constraints=list(data.get("constraints", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class DiscoveryAudit:
    id: str
    node_id: str
    run_outcome: RunOutcome
    pain_class: PainClass
    gain_class: GainClass
    gain_types: list[ArtifactType]
    enablers: list[str]
    diagnostics: list[str]
    artifact_ids: list[str]
    immediate_learning_ids: list[str]
    immediate_learning_units: list[dict[str, Any]]
    provenance: list[str]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiscoveryAudit":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: DiscoveryAudit(query='force formula')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'DiscoveryAudit': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import (
            normalize_artifact_type,
            normalize_gain_class,
            normalize_pain_class,
            normalize_run_outcome,
        )

        return cls(
            id=data["id"],
            node_id=data["node_id"],
            run_outcome=normalize_run_outcome(data.get("run_outcome", RunOutcome.ONGOING)),
            pain_class=normalize_pain_class(data.get("pain_class", PainClass.PAIN)),
            gain_class=normalize_gain_class(data.get("gain_class", GainClass.NO_GAIN)),
            gain_types=[normalize_artifact_type(item, default=ArtifactType.KNOWLEDGE) for item in data.get("gain_types", [])],
            enablers=[str(item) for item in data.get("enablers", [])],
            diagnostics=[str(item) for item in data.get("diagnostics", [])],
            artifact_ids=[str(item) for item in data.get("artifact_ids", [])],
            immediate_learning_ids=[str(item) for item in data.get("immediate_learning_ids", [])],
            immediate_learning_units=[
                dict(item) for item in data.get("immediate_learning_units", []) if isinstance(item, Mapping)
            ],
            provenance=[str(item) for item in data.get("provenance", [])],
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class Claim:
    id: str
    node_id: str
    evidence_id: str
    interpreted_fact: str
    claim_text: str
    stance: ClaimStance
    provenance: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Claim":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Claim': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_claim_stance

        return cls(
            id=data["id"],
            node_id=data["node_id"],
            evidence_id=data["evidence_id"],
            interpreted_fact=data["interpreted_fact"],
            claim_text=data["claim_text"],
            stance=normalize_claim_stance(data["stance"]),
            provenance=list(data.get("provenance", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class ProposedCommitment:
    id: str
    node_id: str
    claim_ids: list[str]
    evidence_ids: list[str]
    justification: str
    accepted: bool = False
    provenance: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposedCommitment":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'ProposedCommitment': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            node_id=data["node_id"],
            claim_ids=list(data.get("claim_ids", [])),
            evidence_ids=list(data.get("evidence_ids", [])),
            justification=data["justification"],
            accepted=bool(data.get("accepted", False)),
            provenance=list(data.get("provenance", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class OntologyEntry:
    id: str
    entity_id: str
    kind: str
    semantic_identity: str
    authoritative_ref: str
    working_semantics: dict[str, Any]
    embedded_refs: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OntologyEntry":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'OntologyEntry': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            entity_id=data["entity_id"],
            kind=data["kind"],
            semantic_identity=data["semantic_identity"],
            authoritative_ref=data["authoritative_ref"],
            working_semantics=dict(data.get("working_semantics", {})),
            embedded_refs=list(data.get("embedded_refs", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class ProposalObject:
    id: str
    proposal_type: ProposalType
    target_scope: str
    originating_not_id: str | None
    mode: SupplementMode
    prompt_state_reference: str
    revision_count: int
    governance_status: ProposalGovernanceStatus
    payload: dict[str, Any]
    source: str
    provider: str | None = None
    model: str | None = None
    rationale: str = ""
    raw_text: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProposalObject":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: ProposalObject(proposal_type=ProposalType.NOT_ELABORATION, rationale='Need a minimally sufficient title.')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'ProposalObject': Result produced by `from_dict`.
        """
        return cls(
            id=data["id"],
            proposal_type=ProposalType(data["proposal_type"]),
            target_scope=data["target_scope"],
            originating_not_id=data.get("originating_not_id"),
            mode=SupplementMode(data["mode"]),
            prompt_state_reference=data["prompt_state_reference"],
            revision_count=int(data.get("revision_count", 0)),
            governance_status=ProposalGovernanceStatus(data.get("governance_status", ProposalGovernanceStatus.SUGGESTED.value)),
            payload=dict(data.get("payload", {})),
            source=data.get("source", "heuristic"),
            provider=data.get("provider"),
            model=data.get("model"),
            rationale=data.get("rationale", ""),
            raw_text=data.get("raw_text", ""),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class LLMSupplementResult:
    payload: dict[str, Any] | None
    source: str
    provider: str | None
    model: str | None
    raw_text: str = ""
    error: str | None = None
    receipt: dict[str, Any] | None = None


@dataclass
class PausePoint:
    id: str
    node_id: str
    reason: str
    required_boundary: PauseBoundary
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PausePoint":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 3

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'PausePoint': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_pause_boundary

        return cls(
            id=data["id"],
            node_id=data["node_id"],
            reason=data["reason"],
            required_boundary=normalize_pause_boundary(data["required_boundary"]),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class Commitment:
    id: str
    node_id: str
    certainty: ThreeLevel
    justification: str
    evidence_ids: list[str]
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Commitment":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: Commitment(content='F = m * a')

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'Commitment': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_three_level

        return cls(
            id=data["id"],
            node_id=data["node_id"],
            certainty=normalize_three_level(data.get("certainty", ThreeLevel.LOW), default=ThreeLevel.LOW),
            justification=data["justification"],
            evidence_ids=list(data.get("evidence_ids", [])),
            created_at=data.get("created_at", utc_now()),
        )


@dataclass
class SupportView:
    direct: list[str]
    upstream: list[str]
    score: SupportScore

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SupportView":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'SupportView': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_support_score

        return cls(
            direct=list(data.get("direct", [])),
            upstream=list(data.get("upstream", [])),
            score=normalize_support_score(data.get("score", SupportScore.VERY_BAD)),
        )


@dataclass
class StepRecord:
    seq: int
    kind: str
    node_id: str | None
    intent: str
    action: str
    result: str
    evaluation: str
    commit_effect: str = ""
    timestamp: str = field(default_factory=utc_now)
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepRecord":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'StepRecord': Result produced by `from_dict`.
        """
        return cls(
            seq=int(data["seq"]),
            kind=data["kind"],
            node_id=data.get("node_id"),
            intent=data["intent"],
            action=data["action"],
            result=data["result"],
            evaluation=data["evaluation"],
            commit_effect=data.get("commit_effect", ""),
            timestamp=data.get("timestamp", utc_now()),
            payload=dict(data.get("payload", {})),
        )


@dataclass
class GovernanceRules:
    closure_threshold_default: ClosureRule = ClosureRule.NORMAL
    support_branch_closure_threshold: ClosureRule = ClosureRule.STRICT
    faithfulness_requirement: ThreeLevel = ThreeLevel.MEDIUM
    max_depth: int = 4
    max_nodes: int = 128
    max_children_per_node: int = 6

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GovernanceRules":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: GovernanceRules(max_depth=6, max_nodes=64, max_children_per_node=4)

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any]`.

        Returns:
            'GovernanceRules': Result produced by `from_dict`.
        """
        from realized_core_semantics.normalization import normalize_closure_rule, normalize_three_level

        return cls(
            closure_threshold_default=normalize_closure_rule(data.get("closure_threshold_default", ClosureRule.NORMAL)),
            support_branch_closure_threshold=normalize_closure_rule(
                data.get("support_branch_closure_threshold", data.get("support_threshold_default", ClosureRule.STRICT))
            ),
            faithfulness_requirement=normalize_three_level(
                data.get("faithfulness_requirement", data.get("faithfulness_overlap_floor", ThreeLevel.MEDIUM)),
                default=ThreeLevel.MEDIUM,
            ),
            max_depth=int(data.get("max_depth", 4)),
            max_nodes=int(data.get("max_nodes", 128)),
            max_children_per_node=int(data.get("max_children_per_node", 6)),
        )


@dataclass
class ControllerFeatureToggles:
    discovery_enabled: bool = True
    reflection_enabled: bool = True
    contemplation_enabled: bool = True
    supported_executors: list[str] = field(default_factory=lambda: ["python3"])

    def to_dict(self) -> dict[str, Any]:
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with serializing the current object into dictionary form.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `to_dict()`
            Output: {'question': 'What is force?', 'answer': 'F = m * a', 'inputs': ['mass', 'acceleration'], 'output': 'force'}

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            dict[str, Any]: Result produced by `to_dict`.
        """
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ControllerFeatureToggles":
        """
        High Level Purpose:
            In circumstances like applied theory typing, runtime data exchange, and configuration handling, helps with reconstructing the current object from dictionary data.

        Reference to Theory:
            Defines applied/runtime theory data structures that carry semantic and controller laws into executable code.

        Example Input Output:
            Input: `from_dict(data={'title': 'Physics / Force / Force From Mass And Acceleration'})`
            Output: 'F = m * a'

        Args:
            cls: Bound class used to construct or inspect class-level behavior.
            data: Value for `data` used by `from_dict`. Expected type: `dict[str, Any] | None`.

        Returns:
            'ControllerFeatureToggles': Result produced by `from_dict`.
        """
        from realized_core_semantics.executors import normalize_supported_executor_frameworks
        from realized_core_semantics.normalization import normalize_controller_feature_toggle_enabled

        payload = data or {}
        return cls(
            discovery_enabled=normalize_controller_feature_toggle_enabled(
                payload.get("discovery_enabled", payload.get("discovery", True)),
                default=True,
            ),
            reflection_enabled=normalize_controller_feature_toggle_enabled(
                payload.get("reflection_enabled", payload.get("reflection", True)),
                default=True,
            ),
            contemplation_enabled=normalize_controller_feature_toggle_enabled(
                payload.get("contemplation_enabled", payload.get("contemplation", True)),
                default=True,
            ),
            supported_executors=normalize_supported_executor_frameworks(
                payload.get("supported_executors"),
                default=("python3",),
            ),
        )


@dataclass
class RuntimeDeterminismPolicy:
    """
    High Level Purpose:
        Makes runtime determinism an explicit, serializable contract so replayability can be verified as a concrete property instead of an informal claim.

    Notes:
        This is intentionally additive. If a stored state or run bundle omits this field, the runtime defaults to the historical behavior (mode=governed, llm_strategy=live).
    """

    mode: str = "governed"  # governed|deterministic|replay
    llm_strategy: str = "live"  # off|live|record|replay
    llm_seed: int | None = None
    llm_system_fingerprint: str | None = None
    clock_strategy: str = "real"  # real|frozen|canonicalized
    random_strategy: str = "real"  # real|seeded
    host_effect_strategy: str = "allow"  # allow|deny|record_only
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return json_safe(self)

    @classmethod
    def from_dict(cls, data: Any | None) -> "RuntimeDeterminismPolicy":
        payload = dict(data) if isinstance(data, Mapping) else {}
        mode = str(payload.get("mode", "")).strip() or "governed"
        llm_strategy = str(payload.get("llm_strategy", "")).strip() or "live"
        seed_value = payload.get("llm_seed")
        try:
            seed = int(seed_value) if seed_value is not None else None
        except (TypeError, ValueError):
            seed = None
        return cls(
            mode=mode,
            llm_strategy=llm_strategy,
            llm_seed=seed,
            llm_system_fingerprint=str(payload.get("llm_system_fingerprint", "")).strip() or None,
            clock_strategy=str(payload.get("clock_strategy", "")).strip() or "real",
            random_strategy=str(payload.get("random_strategy", "")).strip() or "real",
            host_effect_strategy=str(payload.get("host_effect_strategy", "")).strip() or "allow",
            note=str(payload.get("note", "")).strip(),
        )


@dataclass
class LLMSupplementReceipt:
    proposal_type: str
    mode: str
    request_digest: str
    response_digest: str
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None
    seed: int | None = None
    system_fingerprint: str | None = None
    parse_status: str = "ok"
    repair_count: int = 0
    error: str | None = None
    raw_text: str = ""
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return json_safe(self)
