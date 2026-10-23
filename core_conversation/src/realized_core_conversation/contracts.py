"""Typed application-layer plans for governed conversation turns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from realized_core_engine import (
    GoverningDirection,
    IdentityDispositionKind,
    OperationKind,
    SemanticDelta,
    SemanticItem,
)


@dataclass(frozen=True, slots=True)
class CorrectionPlan:
    """Propose one exact semantic replacement after selector resolution."""

    target_selector: str
    replacement: SemanticItem | None
    rationale: str
    evidence_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_selector": self.target_selector,
            "replacement": (
                self.replacement.to_dict()
                if self.replacement is not None
                else None
            ),
            "rationale": self.rationale,
            "evidence_references": list(self.evidence_references),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> CorrectionPlan:
        raw_replacement = value.get("replacement")
        return cls(
            target_selector=str(value.get("target_selector", "")),
            replacement=(
                SemanticItem.from_dict(dict(raw_replacement))
                if isinstance(raw_replacement, dict)
                else None
            ),
            rationale=str(value.get("rationale", "")),
            evidence_references=tuple(
                str(item)
                for item in value.get("evidence_references", ())
            ),
        )


@dataclass(frozen=True, slots=True)
class RealignmentPlan:
    """Application proposal for exhaustive redirection realignment."""

    affected_selectors: tuple[str, ...]
    retained_selectors: tuple[str, ...] = ()
    superseded_selectors: tuple[str, ...] = ()
    unresolved_selectors: tuple[str, ...] = ()
    introduced_items: tuple[SemanticItem, ...] = ()
    identity_disposition: IdentityDispositionKind = (
        IdentityDispositionKind.SAME_OBJECTIVE
    )
    target_scope_id: str = ""
    target_objective_id: str = ""
    target_branch_id: str = ""
    rationale: str = ""
    evidence_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    completeness_statement: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected_selectors": list(self.affected_selectors),
            "retained_selectors": list(self.retained_selectors),
            "superseded_selectors": list(self.superseded_selectors),
            "unresolved_selectors": list(self.unresolved_selectors),
            "introduced_items": [
                item.to_dict() for item in self.introduced_items
            ],
            "identity_disposition": self.identity_disposition.value,
            "target_scope_id": self.target_scope_id,
            "target_objective_id": self.target_objective_id,
            "target_branch_id": self.target_branch_id,
            "rationale": self.rationale,
            "evidence_references": list(self.evidence_references),
            "governance_references": list(self.governance_references),
            "completeness_statement": self.completeness_statement,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RealignmentPlan:
        return cls(
            affected_selectors=tuple(
                str(item) for item in value.get("affected_selectors", ())
            ),
            retained_selectors=tuple(
                str(item) for item in value.get("retained_selectors", ())
            ),
            superseded_selectors=tuple(
                str(item)
                for item in value.get("superseded_selectors", ())
            ),
            unresolved_selectors=tuple(
                str(item)
                for item in value.get("unresolved_selectors", ())
            ),
            introduced_items=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("introduced_items", ())
            ),
            identity_disposition=IdentityDispositionKind(
                str(
                    value.get(
                        "identity_disposition",
                        IdentityDispositionKind.SAME_OBJECTIVE.value,
                    )
                )
            ),
            target_scope_id=str(value.get("target_scope_id", "")),
            target_objective_id=str(
                value.get("target_objective_id", "")
            ),
            target_branch_id=str(value.get("target_branch_id", "")),
            rationale=str(value.get("rationale", "")),
            evidence_references=tuple(
                str(item)
                for item in value.get("evidence_references", ())
            ),
            governance_references=tuple(
                str(item)
                for item in value.get("governance_references", ())
            ),
            completeness_statement=str(
                value.get("completeness_statement", "")
            ),
        )


@dataclass(frozen=True, slots=True)
class ReversalPlan:
    """Propose restoration of one exact parent transition."""

    target_transition_artifact_id: str
    restore_parent_revision_id: str
    rationale: str
    evidence_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_transition_artifact_id": (
                self.target_transition_artifact_id
            ),
            "restore_parent_revision_id": self.restore_parent_revision_id,
            "rationale": self.rationale,
            "evidence_references": list(self.evidence_references),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ReversalPlan:
        return cls(
            target_transition_artifact_id=str(
                value.get("target_transition_artifact_id", "")
            ),
            restore_parent_revision_id=str(
                value.get("restore_parent_revision_id", "")
            ),
            rationale=str(value.get("rationale", "")),
            evidence_references=tuple(
                str(item)
                for item in value.get("evidence_references", ())
            ),
        )


@dataclass(frozen=True, slots=True)
class ConversationTurnPlan:
    """Advisory plan that a conversation host translates to the engine ABI."""

    operation: OperationKind
    prompt: str = ""
    parent_run_id: str = ""
    semantic_delta: SemanticDelta = field(default_factory=SemanticDelta)
    governing_direction: GoverningDirection | None = None
    corrections: tuple[CorrectionPlan, ...] = ()
    realignment: RealignmentPlan | None = None
    reversal: ReversalPlan | None = None
    target_hold_id: str = ""
    selected_item_ids: tuple[str, ...] = ()
    selected_item_selectors: tuple[str, ...] = ()
    target_scope_id: str = ""
    target_objective_id: str = ""
    target_branch_id: str = ""
    source_attempt_id: str = ""
    merge_parent_run_ids: tuple[str, ...] = ()
    inlet_kind: str = "conversation_turn"
    treatment_label: str = ""
    inlet_payload: dict[str, Any] = field(default_factory=dict)
    authority_context: dict[str, Any] = field(
        default_factory=lambda: {"principal": "local-user"}
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation.value,
            "prompt": self.prompt,
            "parent_run_id": self.parent_run_id,
            "semantic_delta": self.semantic_delta.to_dict(),
            "governing_direction": (
                self.governing_direction.to_dict()
                if self.governing_direction is not None
                else None
            ),
            "corrections": [item.to_dict() for item in self.corrections],
            "realignment": (
                self.realignment.to_dict()
                if self.realignment is not None
                else None
            ),
            "reversal": (
                self.reversal.to_dict()
                if self.reversal is not None
                else None
            ),
            "target_hold_id": self.target_hold_id,
            "selected_item_ids": list(self.selected_item_ids),
            "selected_item_selectors": list(
                self.selected_item_selectors
            ),
            "target_scope_id": self.target_scope_id,
            "target_objective_id": self.target_objective_id,
            "target_branch_id": self.target_branch_id,
            "source_attempt_id": self.source_attempt_id,
            "merge_parent_run_ids": list(self.merge_parent_run_ids),
            "inlet_kind": self.inlet_kind,
            "treatment_label": self.treatment_label,
            "inlet_payload": dict(self.inlet_payload),
            "authority_context": dict(self.authority_context),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ConversationTurnPlan:
        raw_direction = value.get("governing_direction")
        raw_realignment = value.get("realignment")
        raw_reversal = value.get("reversal")
        return cls(
            operation=OperationKind(str(value["operation"])),
            prompt=str(value.get("prompt", "")),
            parent_run_id=str(value.get("parent_run_id", "")),
            semantic_delta=SemanticDelta.from_dict(
                dict(value.get("semantic_delta", {}))
            ),
            governing_direction=(
                GoverningDirection.from_dict(dict(raw_direction))
                if isinstance(raw_direction, dict)
                else None
            ),
            corrections=tuple(
                CorrectionPlan.from_dict(dict(item))
                for item in value.get("corrections", ())
            ),
            realignment=(
                RealignmentPlan.from_dict(dict(raw_realignment))
                if isinstance(raw_realignment, dict)
                else None
            ),
            reversal=(
                ReversalPlan.from_dict(dict(raw_reversal))
                if isinstance(raw_reversal, dict)
                else None
            ),
            target_hold_id=str(value.get("target_hold_id", "")),
            selected_item_ids=tuple(
                str(item) for item in value.get("selected_item_ids", ())
            ),
            selected_item_selectors=tuple(
                str(item)
                for item in value.get("selected_item_selectors", ())
            ),
            target_scope_id=str(value.get("target_scope_id", "")),
            target_objective_id=str(
                value.get("target_objective_id", "")
            ),
            target_branch_id=str(value.get("target_branch_id", "")),
            source_attempt_id=str(value.get("source_attempt_id", "")),
            merge_parent_run_ids=tuple(
                str(item) for item in value.get("merge_parent_run_ids", ())
            ),
            inlet_kind=str(value.get("inlet_kind", "conversation_turn")),
            treatment_label=str(value.get("treatment_label", "")),
            inlet_payload=dict(value.get("inlet_payload", {})),
            authority_context=dict(
                value.get("authority_context", {"principal": "local-user"})
            ),
        )


__all__ = [
    "ConversationTurnPlan",
    "CorrectionPlan",
    "RealignmentPlan",
    "ReversalPlan",
]
