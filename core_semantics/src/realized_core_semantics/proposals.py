"""Stable vocabulary for advisory proposals and supplement depth."""

from __future__ import annotations

from enum import Enum


class SupplementMode(Enum):
    FAST = "fast"
    DEEP = "deep"


class ProposalGovernanceStatus(Enum):
    SUGGESTED = "suggested"
    ADMITTED = "admitted"
    REVISED = "revised"
    REJECTED = "rejected"
    HOLDON = "holdon"
    ESCALATED = "escalated"


class ProposalType(Enum):
    SEMANTIC_TARGET = "SemanticTargetProposal"
    NOT_ELABORATION = "NotElaborationProposal"
    MARKDOWN_LEARNING = "MarkdownLearningProposal"
    MARKDOWN_TITLE_REPAIR = "MarkdownTitleRepairProposal"
    MARKDOWN_ABILITY_LEARNING = "MarkdownAbilityLearningProposal"
    MARKDOWN_FUNCTIONALIZATION = "MarkdownFunctionalizationProposal"
    MARKDOWN_EXPRESSION_SYNTHESIS = "MarkdownExpressionSynthesisProposal"
    CONTROL_DECISION = "ControlDecisionProposal"
    NODE_ASSESSMENT = "NodeAssessmentProposal"
    DISCOVERY_AUDIT = "DiscoveryAuditProposal"
    IMMEDIATE_LEARNING = "ImmediateLearningProposal"
    CANDIDATE_SELECTION = "CandidateSelectionProposal"
    NOT_DECOMPOSITION = "NotDecompositionProposal"
    DIRECT_RESOLUTION = "DirectResolutionProposal"
    REALIZATION_WITNESS = "RealizationWitnessProposal"
    RETRIEVAL_PLAN = "RetrievalPlanProposal"
    CAPABILITY_DRAFT = "CapabilityDraftProposal"
    UNCERTAINTY_ASSESSMENT = "UncertaintyAssessmentProposal"
    NEXT_ACTION = "NextActionProposal"
    REFLECTION = "ReflectionProposal"
    CONTEMPLATION = "ContemplationProposal"
    REFRAME = "ReframeProposal"
    EXPLANATION_DRAFT = "ExplanationDraft"
    DST_DISCOVERY = "DstDiscoveryProposal"
    DST_NORMALIZATION = "DstNormalizationProposal"


__all__ = [
    "ProposalGovernanceStatus",
    "ProposalType",
    "SupplementMode",
]
