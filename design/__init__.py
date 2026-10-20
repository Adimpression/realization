"""Cross-domain design mediation package.

This package is intentionally documentation-first.

It packages:
* the axiomatic human-factors base,
* the cross-domain mediation theory,
* case studies showing compilation into concrete artifact vocabularies,
* and the typed design mediation layer that preserves the theory through
  implementation and revision.
"""

from .controllers import (
    DesignCompiler,
    DriftDetector,
    EncodingAdmissibilityChecker,
    EncodingRecompiler,
    ObligationValidator,
    RealityAlignmentChecker,
    RevisionPlanner,
)
from .core import (
    Constraint,
    CoordinationRequirement,
    FeedbackRequirement,
    InteractionInvariant,
    InteractionObligation,
    Intent,
    Objective,
    RecoverabilityRequirement,
    RiskClass,
    TaskMorphology,
)
from .embodiment import (
    ActionEmbodiment,
    AuditEmbodiment,
    ContainmentEmbodiment,
    DesignEmbodiment,
    EmbodimentKind,
    HandoffEmbodiment,
    InputEmbodiment,
    InterlockEmbodiment,
    NavigationEmbodiment,
    QueueEmbodiment,
    SelectionEmbodiment,
    StatusEmbodiment,
)
from .examples import EXAMPLE_MODULES
from .framework import (
    FrameworkEncoding,
    MaterialButtonEncoding,
    MaterialCardEncoding,
    MaterialDialogEncoding,
    MaterialNavigationBarEncoding,
)
from .reality import (
    ActionEvent,
    AdoptionDrift,
    BoundaryFriction,
    ConstraintActivation,
    EvidenceSeverity,
    FeedbackEvent,
    HandoffFailure,
    ObservedSignal,
    OverrideEvent,
    QueueCongestion,
    RealityEvidence,
    TrustFailure,
)
from .revision import (
    AlignmentCheck,
    AlignmentStatus,
    DesignSnapshot,
    DriftReport,
    InvalidatedEncoding,
    RealitySnapshot,
    RecompilationRequired,
)
from .trace import (
    DesignRef,
    EmbodimentRef,
    EncodingRef,
    EvidenceLink,
    ObjectiveRef,
    ObservationRef,
    ObligationRef,
    RevisionRef,
)

AXIOMATIC_SYSTEM_DOC = "AXIOMATIC_SYSTEM_FOR_DESIGN.md"
CROSS_DOMAIN_MEDIATION_DOC = "CROSS_DOMAIN_DESIGN_MEDIATION.md"
TYPE_SYSTEM_DOC = "DESIGN_TYPE_SYSTEM.md"
TYPE_SYSTEM_IMPLEMENTATION_DOC = "DESIGN_TYPE_SYSTEM_IMPLEMENTATION.md"

PACKAGE_DOCS = {
    "axiomatic_system": AXIOMATIC_SYSTEM_DOC,
    "cross_domain_mediation": CROSS_DOMAIN_MEDIATION_DOC,
    "type_system": TYPE_SYSTEM_DOC,
    "type_system_implementation": TYPE_SYSTEM_IMPLEMENTATION_DOC,
}

__all__ = [
    "AXIOMATIC_SYSTEM_DOC",
    "CROSS_DOMAIN_MEDIATION_DOC",
    "TYPE_SYSTEM_DOC",
    "TYPE_SYSTEM_IMPLEMENTATION_DOC",
    "PACKAGE_DOCS",
    "ActionEmbodiment",
    "ActionEvent",
    "AdoptionDrift",
    "AlignmentCheck",
    "AlignmentStatus",
    "AuditEmbodiment",
    "BoundaryFriction",
    "Constraint",
    "ConstraintActivation",
    "ContainmentEmbodiment",
    "CoordinationRequirement",
    "DesignCompiler",
    "DesignEmbodiment",
    "DesignRef",
    "DesignSnapshot",
    "DriftDetector",
    "DriftReport",
    "EmbodimentKind",
    "EmbodimentRef",
    "EncodingAdmissibilityChecker",
    "EncodingRecompiler",
    "EncodingRef",
    "EXAMPLE_MODULES",
    "EvidenceLink",
    "EvidenceSeverity",
    "FeedbackEvent",
    "FeedbackRequirement",
    "FrameworkEncoding",
    "HandoffEmbodiment",
    "HandoffFailure",
    "InputEmbodiment",
    "InteractionInvariant",
    "InteractionObligation",
    "Intent",
    "InterlockEmbodiment",
    "InvalidatedEncoding",
    "MaterialButtonEncoding",
    "MaterialCardEncoding",
    "MaterialDialogEncoding",
    "MaterialNavigationBarEncoding",
    "NavigationEmbodiment",
    "Objective",
    "ObjectiveRef",
    "ObservedSignal",
    "ObservationRef",
    "ObligationRef",
    "ObligationValidator",
    "OverrideEvent",
    "QueueCongestion",
    "QueueEmbodiment",
    "RealityAlignmentChecker",
    "RealityEvidence",
    "RealitySnapshot",
    "RecoverabilityRequirement",
    "RecompilationRequired",
    "RevisionPlanner",
    "RevisionRef",
    "RiskClass",
    "SelectionEmbodiment",
    "StatusEmbodiment",
    "TaskMorphology",
    "TrustFailure",
]
