"""Typed semantic contracts for governed resumption.

The contracts in this module contain no transcript or provider-session state.
They are canonical values suitable for deterministic serialization, hashing,
SQLite persistence, transport, and replay.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

from realized_core_runtime import AttemptExecutionOutcome


JsonObject = dict[str, Any]


def canonical_json(value: Any) -> str:
    """Serialize a contract value deterministically."""

    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def content_digest(value: Any) -> str:
    """Return the canonical SHA-256 digest for a contract value."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class OperationKind(StrEnum):
    START = "start"
    CONTINUE = "continue"
    DERIVE = "derive"
    RESUME_AFTER_INTERRUPTION = "resume_after_interruption"
    RESUME_SUSPENDED = "resume_suspended"
    AUGMENT = "augment"
    CORRECT = "correct"
    REDIRECT_AND_REALIGN = "redirect_and_realign"
    BRANCH = "branch"
    MERGE = "merge"
    EXPLAIN = "explain"
    VERIFY = "verify"
    REVERSE = "reverse"
    RECONSTRUCT = "reconstruct"


class InletRelationship(StrEnum):
    CONTINUATION = "continuation"
    AUGMENTATION = "augmentation"
    REDIRECTION = "redirection"
    CORRECTION = "correction"
    REVERSAL = "reversal"
    HOLD_SATISFACTION = "hold_satisfaction"


class SemanticOutcome(StrEnum):
    COMPLETED = "completed"
    PAUSED = "paused"
    INCOMPLETE = "incomplete"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"
    CONFLICTED = "conflicted"
    STALE = "stale"
    EXPIRED = "expired"
    FAILED = "failed"
    EXHAUSTED = "exhausted"


class AdmissionDisposition(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NARROWED = "narrowed"
    HELD = "held"
    CLARIFICATION_REQUIRED = "clarification_required"


class IdentityDispositionKind(StrEnum):
    SAME_OBJECTIVE = "same_objective"
    DERIVED_OBJECTIVE = "derived_objective"
    BRANCH = "branch"


class HoldDisposition(StrEnum):
    REMAIN_HELD = "remain_held"
    RESUME = "resume"
    EXPIRE = "expire"
    FAIL = "fail"
    ESCALATE = "escalate"
    REFRAME = "reframe"


class InspectionTargetKind(StrEnum):
    REVISION = "revision"
    BRANCH_HEAD = "branch_head"
    ATTEMPT = "attempt"
    TRANSITION = "transition"


class InspectionView(StrEnum):
    CURRENT_STATE = "current_state"
    NON_ACHIEVEDNESS = "non_achievedness"
    GOVERNING_DIRECTION = "governing_direction"
    REALIGNMENT = "realignment"
    PATH = "path"
    PROVENANCE = "provenance"
    ATTEMPT = "attempt"
    TRANSITION = "transition"
    BRANCH_GRAPH = "branch_graph"
    RECONSTRUCTION = "reconstruction"


@dataclass(frozen=True, slots=True)
class SemanticItem:
    item_id: str
    kind: str
    payload: JsonObject
    evidence_references: tuple[str, ...] = ()
    provenance_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()

    def to_dict(self) -> JsonObject:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "evidence_references": list(self.evidence_references),
            "provenance_references": list(self.provenance_references),
            "governance_references": list(self.governance_references),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> SemanticItem:
        return cls(
            item_id=str(value["item_id"]),
            kind=str(value["kind"]),
            payload=dict(value.get("payload", {})),
            evidence_references=tuple(value.get("evidence_references", ())),
            provenance_references=tuple(value.get("provenance_references", ())),
            governance_references=tuple(value.get("governance_references", ())),
        )


@dataclass(frozen=True, slots=True)
class GoverningDirection:
    objective: str
    scope: str
    constraints: tuple[str, ...] = ()
    required_outcome: str = ""

    def to_dict(self) -> JsonObject:
        return {
            "objective": self.objective,
            "scope": self.scope,
            "constraints": list(self.constraints),
            "required_outcome": self.required_outcome,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> GoverningDirection:
        return cls(
            objective=str(value.get("objective", "")),
            scope=str(value.get("scope", "")),
            constraints=tuple(value.get("constraints", ())),
            required_outcome=str(value.get("required_outcome", "")),
        )


@dataclass(frozen=True, slots=True)
class HoldOn:
    """Complete durable semantic suspension object from resumption theory."""

    hold_id: str
    unresolved_semantic_object: JsonObject
    continuation_carrier: JsonObject
    resume_predicate: JsonObject
    failure_or_expiry_predicate: JsonObject
    temporal_policy: JsonObject
    correlation: JsonObject
    multiplicity: JsonObject
    scope: JsonObject
    provenance_and_governance: JsonObject
    disposition: HoldDisposition = HoldDisposition.REMAIN_HELD

    def to_dict(self) -> JsonObject:
        return {
            "hold_id": self.hold_id,
            "unresolved_semantic_object": dict(self.unresolved_semantic_object),
            "continuation_carrier": dict(self.continuation_carrier),
            "resume_predicate": dict(self.resume_predicate),
            "failure_or_expiry_predicate": dict(
                self.failure_or_expiry_predicate
            ),
            "temporal_policy": dict(self.temporal_policy),
            "correlation": dict(self.correlation),
            "multiplicity": dict(self.multiplicity),
            "scope": dict(self.scope),
            "provenance_and_governance": dict(
                self.provenance_and_governance
            ),
            "disposition": self.disposition.value,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> HoldOn:
        return cls(
            hold_id=str(value["hold_id"]),
            unresolved_semantic_object=dict(
                value.get("unresolved_semantic_object", {})
            ),
            continuation_carrier=dict(value.get("continuation_carrier", {})),
            resume_predicate=dict(value.get("resume_predicate", {})),
            failure_or_expiry_predicate=dict(
                value.get("failure_or_expiry_predicate", {})
            ),
            temporal_policy=dict(value.get("temporal_policy", {})),
            correlation=dict(value.get("correlation", {})),
            multiplicity=dict(value.get("multiplicity", {})),
            scope=dict(value.get("scope", {})),
            provenance_and_governance=dict(
                value.get("provenance_and_governance", {})
            ),
            disposition=HoldDisposition(
                value.get("disposition", HoldDisposition.REMAIN_HELD.value)
            ),
        )


@dataclass(frozen=True, slots=True)
class IdentityDisposition:
    kind: IdentityDispositionKind
    target_scope_id: str
    target_objective_id: str
    target_branch_id: str
    rationale: str

    def to_dict(self) -> JsonObject:
        return {
            "kind": self.kind.value,
            "target_scope_id": self.target_scope_id,
            "target_objective_id": self.target_objective_id,
            "target_branch_id": self.target_branch_id,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> IdentityDisposition:
        return cls(
            kind=IdentityDispositionKind(value["kind"]),
            target_scope_id=str(value["target_scope_id"]),
            target_objective_id=str(value["target_objective_id"]),
            target_branch_id=str(value["target_branch_id"]),
            rationale=str(value.get("rationale", "")),
        )


@dataclass(frozen=True, slots=True)
class Realignment:
    source_revision_id: str
    redirection_inlet_id: str
    affected_item_ids: tuple[str, ...]
    identity_disposition: IdentityDisposition
    retained_item_ids: tuple[str, ...]
    superseded_item_ids: tuple[str, ...]
    introduced_items: tuple[SemanticItem, ...]
    unresolved_applicability_item_ids: tuple[str, ...]
    resulting_non_achievedness: tuple[SemanticItem, ...]
    evidence_references: tuple[str, ...]
    governance_references: tuple[str, ...]
    completeness_statement: str

    def to_dict(self) -> JsonObject:
        return {
            "source_revision_id": self.source_revision_id,
            "redirection_inlet_id": self.redirection_inlet_id,
            "affected_item_ids": list(self.affected_item_ids),
            "identity_disposition": self.identity_disposition.to_dict(),
            "retained_item_ids": list(self.retained_item_ids),
            "superseded_item_ids": list(self.superseded_item_ids),
            "introduced_items": [item.to_dict() for item in self.introduced_items],
            "unresolved_applicability_item_ids": list(
                self.unresolved_applicability_item_ids
            ),
            "resulting_non_achievedness": [
                item.to_dict() for item in self.resulting_non_achievedness
            ],
            "evidence_references": list(self.evidence_references),
            "governance_references": list(self.governance_references),
            "completeness_statement": self.completeness_statement,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> Realignment:
        return cls(
            source_revision_id=str(value["source_revision_id"]),
            redirection_inlet_id=str(value["redirection_inlet_id"]),
            affected_item_ids=tuple(value.get("affected_item_ids", ())),
            identity_disposition=IdentityDisposition.from_dict(
                dict(value["identity_disposition"])
            ),
            retained_item_ids=tuple(value.get("retained_item_ids", ())),
            superseded_item_ids=tuple(value.get("superseded_item_ids", ())),
            introduced_items=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("introduced_items", ())
            ),
            unresolved_applicability_item_ids=tuple(
                value.get("unresolved_applicability_item_ids", ())
            ),
            resulting_non_achievedness=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("resulting_non_achievedness", ())
            ),
            evidence_references=tuple(value.get("evidence_references", ())),
            governance_references=tuple(
                value.get("governance_references", ())
            ),
            completeness_statement=str(
                value.get("completeness_statement", "")
            ),
        )


@dataclass(frozen=True, slots=True)
class Supersession:
    target_item_id: str
    replacement: SemanticItem | None
    evidence_references: tuple[str, ...]
    rationale: str

    def to_dict(self) -> JsonObject:
        return {
            "target_item_id": self.target_item_id,
            "replacement": (
                self.replacement.to_dict() if self.replacement is not None else None
            ),
            "evidence_references": list(self.evidence_references),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> Supersession:
        raw_replacement = value.get("replacement")
        return cls(
            target_item_id=str(value["target_item_id"]),
            replacement=(
                SemanticItem.from_dict(dict(raw_replacement))
                if isinstance(raw_replacement, dict)
                else None
            ),
            evidence_references=tuple(value.get("evidence_references", ())),
            rationale=str(value.get("rationale", "")),
        )


@dataclass(frozen=True, slots=True)
class Reversal:
    """Explicit request to restore one direct parent of the current revision."""

    target_transition_artifact_id: str
    restore_parent_revision_id: str
    evidence_references: tuple[str, ...]
    rationale: str

    def to_dict(self) -> JsonObject:
        return {
            "target_transition_artifact_id": self.target_transition_artifact_id,
            "restore_parent_revision_id": self.restore_parent_revision_id,
            "evidence_references": list(self.evidence_references),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> Reversal:
        return cls(
            target_transition_artifact_id=str(
                value["target_transition_artifact_id"]
            ),
            restore_parent_revision_id=str(
                value["restore_parent_revision_id"]
            ),
            evidence_references=tuple(value.get("evidence_references", ())),
            rationale=str(value.get("rationale", "")),
        )


@dataclass(frozen=True, slots=True)
class SemanticDelta:
    achieved: tuple[SemanticItem, ...] = ()
    non_achievedness: tuple[SemanticItem, ...] = ()
    resolved_non_achievedness_ids: tuple[str, ...] = ()
    holds: tuple[HoldOn, ...] = ()
    resolved_hold_ids: tuple[str, ...] = ()
    supersessions: tuple[Supersession, ...] = ()
    governing_direction: GoverningDirection | None = None

    def to_dict(self) -> JsonObject:
        return {
            "achieved": [item.to_dict() for item in self.achieved],
            "non_achievedness": [
                item.to_dict() for item in self.non_achievedness
            ],
            "resolved_non_achievedness_ids": list(
                self.resolved_non_achievedness_ids
            ),
            "holds": [hold.to_dict() for hold in self.holds],
            "resolved_hold_ids": list(self.resolved_hold_ids),
            "supersessions": [item.to_dict() for item in self.supersessions],
            "governing_direction": (
                self.governing_direction.to_dict()
                if self.governing_direction is not None
                else None
            ),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> SemanticDelta:
        raw_direction = value.get("governing_direction")
        return cls(
            achieved=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("achieved", ())
            ),
            non_achievedness=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("non_achievedness", ())
            ),
            resolved_non_achievedness_ids=tuple(
                value.get("resolved_non_achievedness_ids", ())
            ),
            holds=tuple(
                HoldOn.from_dict(dict(item))
                for item in value.get("holds", ())
            ),
            resolved_hold_ids=tuple(value.get("resolved_hold_ids", ())),
            supersessions=tuple(
                Supersession.from_dict(dict(item))
                for item in value.get("supersessions", ())
            ),
            governing_direction=(
                GoverningDirection.from_dict(dict(raw_direction))
                if isinstance(raw_direction, dict)
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class SemanticState:
    achieved: tuple[SemanticItem, ...]
    non_achievedness: tuple[SemanticItem, ...]
    governing_direction: GoverningDirection
    refinement_graph: JsonObject = field(default_factory=dict)
    duties_and_obligations: tuple[JsonObject, ...] = ()
    certainty: JsonObject = field(default_factory=dict)
    blockers: JsonObject = field(default_factory=dict)
    conflicts: JsonObject = field(default_factory=dict)
    evidence_and_support: JsonObject = field(default_factory=dict)
    commitments: tuple[JsonObject, ...] = ()
    supersession_edges: tuple[JsonObject, ...] = ()
    contradiction_edges: tuple[JsonObject, ...] = ()
    realignments: tuple[Realignment, ...] = ()
    unresolved_applicability_item_ids: tuple[str, ...] = ()
    holds: tuple[HoldOn, ...] = ()
    hold_evaluations: tuple[JsonObject, ...] = ()
    capability_declarations: tuple[JsonObject, ...] = ()
    scope_imports: tuple[JsonObject, ...] = ()
    provenance_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    engine_state: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "achieved": [item.to_dict() for item in self.achieved],
            "non_achievedness": [
                item.to_dict() for item in self.non_achievedness
            ],
            "governing_direction": self.governing_direction.to_dict(),
            "refinement_graph": dict(self.refinement_graph),
            "duties_and_obligations": [
                dict(value) for value in self.duties_and_obligations
            ],
            "certainty": dict(self.certainty),
            "blockers": dict(self.blockers),
            "conflicts": dict(self.conflicts),
            "evidence_and_support": dict(self.evidence_and_support),
            "commitments": [dict(value) for value in self.commitments],
            "supersession_edges": [
                dict(value) for value in self.supersession_edges
            ],
            "contradiction_edges": [
                dict(value) for value in self.contradiction_edges
            ],
            "realignments": [value.to_dict() for value in self.realignments],
            "unresolved_applicability_item_ids": list(
                self.unresolved_applicability_item_ids
            ),
            "holds": [value.to_dict() for value in self.holds],
            "hold_evaluations": [
                dict(value) for value in self.hold_evaluations
            ],
            "capability_declarations": [
                dict(value) for value in self.capability_declarations
            ],
            "scope_imports": [dict(value) for value in self.scope_imports],
            "provenance_references": list(self.provenance_references),
            "governance_references": list(self.governance_references),
            "engine_state": dict(self.engine_state),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> SemanticState:
        return cls(
            achieved=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("achieved", ())
            ),
            non_achievedness=tuple(
                SemanticItem.from_dict(dict(item))
                for item in value.get("non_achievedness", ())
            ),
            governing_direction=GoverningDirection.from_dict(
                dict(value.get("governing_direction", {}))
            ),
            refinement_graph=dict(value.get("refinement_graph", {})),
            duties_and_obligations=tuple(
                dict(item) for item in value.get("duties_and_obligations", ())
            ),
            certainty=dict(value.get("certainty", {})),
            blockers=dict(value.get("blockers", {})),
            conflicts=dict(value.get("conflicts", {})),
            evidence_and_support=dict(value.get("evidence_and_support", {})),
            commitments=tuple(
                dict(item) for item in value.get("commitments", ())
            ),
            supersession_edges=tuple(
                dict(item) for item in value.get("supersession_edges", ())
            ),
            contradiction_edges=tuple(
                dict(item) for item in value.get("contradiction_edges", ())
            ),
            realignments=tuple(
                Realignment.from_dict(dict(item))
                for item in value.get("realignments", ())
            ),
            unresolved_applicability_item_ids=tuple(
                value.get("unresolved_applicability_item_ids", ())
            ),
            holds=tuple(
                HoldOn.from_dict(dict(item))
                for item in value.get("holds", ())
            ),
            hold_evaluations=tuple(
                dict(item) for item in value.get("hold_evaluations", ())
            ),
            capability_declarations=tuple(
                dict(item) for item in value.get("capability_declarations", ())
            ),
            scope_imports=tuple(
                dict(item) for item in value.get("scope_imports", ())
            ),
            provenance_references=tuple(
                value.get("provenance_references", ())
            ),
            governance_references=tuple(
                value.get("governance_references", ())
            ),
            engine_state=dict(value.get("engine_state", {})),
        )

    @property
    def digest(self) -> str:
        return content_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class ResumptionIdentity:
    scope_id: str
    objective_id: str
    branch_id: str
    revision_id: str
    state_digest: str

    def to_dict(self) -> JsonObject:
        return {
            "scope_id": self.scope_id,
            "objective_id": self.objective_id,
            "branch_id": self.branch_id,
            "revision_id": self.revision_id,
            "state_digest": self.state_digest,
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> ResumptionIdentity:
        return cls(
            scope_id=str(value["scope_id"]),
            objective_id=str(value["objective_id"]),
            branch_id=str(value["branch_id"]),
            revision_id=str(value["revision_id"]),
            state_digest=str(value["state_digest"]),
        )

    @property
    def causal_anchor(self) -> str:
        return canonical_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class Revision:
    identity: ResumptionIdentity
    parent_revision_ids: tuple[str, ...]
    state: SemanticState
    provenance_references: tuple[str, ...]
    governance_references: tuple[str, ...]
    transition_artifact_id: str
    revision_digest: str
    created_at: str

    def canonical_content(self) -> JsonObject:
        return {
            "identity": self.identity.to_dict(),
            "parent_revision_ids": list(self.parent_revision_ids),
            "state": self.state.to_dict(),
            "provenance_references": list(self.provenance_references),
            "governance_references": list(self.governance_references),
            "transition_artifact_id": self.transition_artifact_id,
        }

    def verify(self) -> bool:
        return (
            self.identity.state_digest == self.state.digest
            and self.revision_digest == content_digest(self.canonical_content())
        )


@dataclass(frozen=True, slots=True)
class ProjectionPolicy:
    policy_id: str = "resumption-projection-v1"
    max_inline_items: int = 512
    include_path: bool = False
    permitted_item_ids: tuple[str, ...] = ()

    def to_dict(self) -> JsonObject:
        return {
            "policy_id": self.policy_id,
            "max_inline_items": self.max_inline_items,
            "include_path": self.include_path,
            "permitted_item_ids": list(self.permitted_item_ids),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> ProjectionPolicy:
        return cls(
            policy_id=str(value.get("policy_id", "resumption-projection-v1")),
            max_inline_items=int(value.get("max_inline_items", 512)),
            include_path=bool(value.get("include_path", False)),
            permitted_item_ids=tuple(value.get("permitted_item_ids", ())),
        )


@dataclass(frozen=True, slots=True)
class ResumptionProjection:
    identity: ResumptionIdentity
    policy: ProjectionPolicy
    state: SemanticState
    external_references: tuple[str, ...]
    completeness_statement: str
    projection_digest: str

    def canonical_content(self) -> JsonObject:
        return {
            "identity": self.identity.to_dict(),
            "policy": self.policy.to_dict(),
            "state": self.state.to_dict(),
            "external_references": list(self.external_references),
            "completeness_statement": self.completeness_statement,
        }

    def verify(self) -> bool:
        return self.projection_digest == content_digest(self.canonical_content())

    @classmethod
    def from_dict(cls, value: JsonObject) -> ResumptionProjection:
        return cls(
            identity=ResumptionIdentity.from_dict(dict(value["identity"])),
            policy=ProjectionPolicy.from_dict(dict(value["policy"])),
            state=SemanticState.from_dict(dict(value["state"])),
            external_references=tuple(
                value.get("external_references", ())
            ),
            completeness_statement=str(
                value.get("completeness_statement", "")
            ),
            projection_digest=str(value.get("projection_digest", "")),
        )


@dataclass(frozen=True, slots=True)
class ContinuationInlet:
    inlet_id: str
    kind: str
    payload: JsonObject
    target: str
    relationship: InletRelationship
    source: str
    provenance: tuple[str, ...]
    correlation: JsonObject
    authority_context: JsonObject
    delta: SemanticDelta = field(default_factory=SemanticDelta)
    realignment: Realignment | None = None
    reversal: Reversal | None = None

    def to_dict(self) -> JsonObject:
        value = {
            "inlet_id": self.inlet_id,
            "kind": self.kind,
            "payload": dict(self.payload),
            "target": self.target,
            "relationship": self.relationship.value,
            "source": self.source,
            "provenance": list(self.provenance),
            "correlation": dict(self.correlation),
            "authority_context": dict(self.authority_context),
            "delta": self.delta.to_dict(),
            "realignment": (
                self.realignment.to_dict()
                if self.realignment is not None
                else None
            ),
        }
        if self.reversal is not None:
            value["reversal"] = self.reversal.to_dict()
        return value

    @property
    def digest(self) -> str:
        return content_digest(self.to_dict())

    @classmethod
    def from_dict(cls, value: JsonObject) -> ContinuationInlet:
        raw_realignment = value.get("realignment")
        raw_reversal = value.get("reversal")
        return cls(
            inlet_id=str(value["inlet_id"]),
            kind=str(value["kind"]),
            payload=dict(value.get("payload", {})),
            target=str(value.get("target", "root")),
            relationship=InletRelationship(value["relationship"]),
            source=str(value.get("source", "external")),
            provenance=tuple(value.get("provenance", ())),
            correlation=dict(value.get("correlation", {})),
            authority_context=dict(value.get("authority_context", {})),
            delta=SemanticDelta.from_dict(dict(value.get("delta", {}))),
            realignment=(
                Realignment.from_dict(dict(raw_realignment))
                if isinstance(raw_realignment, dict)
                else None
            ),
            reversal=(
                Reversal.from_dict(dict(raw_reversal))
                if isinstance(raw_reversal, dict)
                else None
            ),
        )


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    disposition: AdmissionDisposition
    rationale: str
    governance_references: tuple[str, ...] = ()
    checks: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "disposition": self.disposition.value,
            "rationale": self.rationale,
            "governance_references": list(self.governance_references),
            "checks": dict(self.checks),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> AdmissionDecision:
        return cls(
            disposition=AdmissionDisposition(value["disposition"]),
            rationale=str(value.get("rationale", "")),
            governance_references=tuple(
                value.get("governance_references", ())
            ),
            checks=dict(value.get("checks", {})),
        )


@dataclass(frozen=True, slots=True)
class TransitionArtifact:
    artifact_id: str
    source_identity: ResumptionIdentity | None
    source_revision_digest: str | None
    projection_policy: ProjectionPolicy
    projection_digest: str | None
    projection_completeness_statement: str
    inlet_id: str | None
    inlet_digest: str | None
    operation: OperationKind
    reconciliation: JsonObject
    proposal_references: tuple[str, ...]
    admission: AdmissionDecision
    admitted_delta: JsonObject
    rejected_delta: JsonObject
    superseded_delta: JsonObject
    conflicting_delta: JsonObject
    unresolved_delta: JsonObject
    hold_evaluation: JsonObject
    capability_receipt_references: tuple[str, ...]
    effect_receipt_references: tuple[str, ...]
    semantic_outcome: SemanticOutcome
    resulting_revision_id: str | None
    resulting_revision_digest: str | None
    decision_flow_signature: str
    realignment: Realignment | None = None
    projection_artifact: JsonObject | None = None
    inlet_artifact: JsonObject | None = None
    proposal_interactions: tuple[JsonObject, ...] = ()

    def to_dict(self) -> JsonObject:
        return {
            "artifact_id": self.artifact_id,
            "source_identity": (
                self.source_identity.to_dict()
                if self.source_identity is not None
                else None
            ),
            "source_revision_digest": self.source_revision_digest,
            "projection_policy": self.projection_policy.to_dict(),
            "projection_digest": self.projection_digest,
            "projection_completeness_statement": (
                self.projection_completeness_statement
            ),
            "inlet_id": self.inlet_id,
            "inlet_digest": self.inlet_digest,
            "operation": self.operation.value,
            "reconciliation": dict(self.reconciliation),
            "proposal_references": list(self.proposal_references),
            "admission": self.admission.to_dict(),
            "admitted_delta": dict(self.admitted_delta),
            "rejected_delta": dict(self.rejected_delta),
            "superseded_delta": dict(self.superseded_delta),
            "conflicting_delta": dict(self.conflicting_delta),
            "unresolved_delta": dict(self.unresolved_delta),
            "hold_evaluation": dict(self.hold_evaluation),
            "capability_receipt_references": list(
                self.capability_receipt_references
            ),
            "effect_receipt_references": list(
                self.effect_receipt_references
            ),
            "semantic_outcome": self.semantic_outcome.value,
            "resulting_revision_id": self.resulting_revision_id,
            "resulting_revision_digest": self.resulting_revision_digest,
            "decision_flow_signature": self.decision_flow_signature,
            "realignment": (
                self.realignment.to_dict()
                if self.realignment is not None
                else None
            ),
            "projection_artifact": (
                dict(self.projection_artifact)
                if self.projection_artifact is not None
                else None
            ),
            "inlet_artifact": (
                dict(self.inlet_artifact)
                if self.inlet_artifact is not None
                else None
            ),
            "proposal_interactions": [
                dict(item) for item in self.proposal_interactions
            ],
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> TransitionArtifact:
        raw_source = value.get("source_identity")
        raw_realignment = value.get("realignment")
        return cls(
            artifact_id=str(value["artifact_id"]),
            source_identity=(
                ResumptionIdentity.from_dict(dict(raw_source))
                if isinstance(raw_source, dict)
                else None
            ),
            source_revision_digest=(
                str(value["source_revision_digest"])
                if value.get("source_revision_digest") is not None
                else None
            ),
            projection_policy=ProjectionPolicy.from_dict(
                dict(value.get("projection_policy", {}))
            ),
            projection_digest=(
                str(value["projection_digest"])
                if value.get("projection_digest") is not None
                else None
            ),
            projection_completeness_statement=str(
                value.get("projection_completeness_statement", "")
            ),
            inlet_id=(
                str(value["inlet_id"])
                if value.get("inlet_id") is not None
                else None
            ),
            inlet_digest=(
                str(value["inlet_digest"])
                if value.get("inlet_digest") is not None
                else None
            ),
            operation=OperationKind(value["operation"]),
            reconciliation=dict(value.get("reconciliation", {})),
            proposal_references=tuple(value.get("proposal_references", ())),
            admission=AdmissionDecision.from_dict(
                dict(value["admission"])
            ),
            admitted_delta=dict(value.get("admitted_delta", {})),
            rejected_delta=dict(value.get("rejected_delta", {})),
            superseded_delta=dict(value.get("superseded_delta", {})),
            conflicting_delta=dict(value.get("conflicting_delta", {})),
            unresolved_delta=dict(value.get("unresolved_delta", {})),
            hold_evaluation=dict(value.get("hold_evaluation", {})),
            capability_receipt_references=tuple(
                value.get("capability_receipt_references", ())
            ),
            effect_receipt_references=tuple(
                value.get("effect_receipt_references", ())
            ),
            semantic_outcome=SemanticOutcome(value["semantic_outcome"]),
            resulting_revision_id=(
                str(value["resulting_revision_id"])
                if value.get("resulting_revision_id") is not None
                else None
            ),
            resulting_revision_digest=(
                str(value["resulting_revision_digest"])
                if value.get("resulting_revision_digest") is not None
                else None
            ),
            decision_flow_signature=str(
                value.get("decision_flow_signature", "")
            ),
            realignment=(
                Realignment.from_dict(dict(raw_realignment))
                if isinstance(raw_realignment, dict)
                else None
            ),
            projection_artifact=(
                dict(value["projection_artifact"])
                if isinstance(value.get("projection_artifact"), dict)
                else None
            ),
            inlet_artifact=(
                dict(value["inlet_artifact"])
                if isinstance(value.get("inlet_artifact"), dict)
                else None
            ),
            proposal_interactions=tuple(
                dict(item)
                for item in value.get("proposal_interactions", ())
            ),
        )

    def decision_flow_content(self) -> JsonObject:
        """Return the externally represented flow covered by the signature."""

        return {
            "source_identity": (
                self.source_identity.to_dict()
                if self.source_identity is not None
                else None
            ),
            "source_revision_digest": self.source_revision_digest,
            "projection_policy": self.projection_policy.to_dict(),
            "projection_digest": self.projection_digest,
            "projection_completeness_statement": (
                self.projection_completeness_statement
            ),
            "inlet_id": self.inlet_id,
            "inlet_digest": self.inlet_digest,
            "operation": self.operation.value,
            "reconciliation": dict(self.reconciliation),
            "proposal_references": list(self.proposal_references),
            "admission": self.admission.to_dict(),
            "admitted_delta": dict(self.admitted_delta),
            "rejected_delta": dict(self.rejected_delta),
            "superseded_delta": dict(self.superseded_delta),
            "conflicting_delta": dict(self.conflicting_delta),
            "unresolved_delta": dict(self.unresolved_delta),
            "hold_evaluation": dict(self.hold_evaluation),
            "capability_receipt_references": list(
                self.capability_receipt_references
            ),
            "effect_receipt_references": list(
                self.effect_receipt_references
            ),
            "semantic_outcome": self.semantic_outcome.value,
            "resulting_revision_id": self.resulting_revision_id,
            "resulting_revision_digest": self.resulting_revision_digest,
            "realignment": (
                self.realignment.to_dict()
                if self.realignment is not None
                else None
            ),
            "projection_artifact": (
                dict(self.projection_artifact)
                if self.projection_artifact is not None
                else None
            ),
            "inlet_artifact": (
                dict(self.inlet_artifact)
                if self.inlet_artifact is not None
                else None
            ),
            "proposal_interactions": [
                dict(item) for item in self.proposal_interactions
            ],
        }

    @property
    def expected_decision_flow_signature(self) -> str:
        return content_digest(self.decision_flow_content())

    def verify_decision_flow_signature(self) -> bool:
        return (
            self.decision_flow_signature
            == self.expected_decision_flow_signature
        )


@dataclass(frozen=True, slots=True)
class StartRequest:
    scope_id: str
    objective_id: str
    branch_id: str
    initial_inlet: ContinuationInlet
    governing_direction: GoverningDirection
    governance_policy: JsonObject = field(default_factory=dict)
    execution_policy: JsonObject = field(default_factory=dict)
    projection_policy: ProjectionPolicy = field(default_factory=ProjectionPolicy)

    def to_dict(self) -> JsonObject:
        return {
            "scope_id": self.scope_id,
            "objective_id": self.objective_id,
            "branch_id": self.branch_id,
            "initial_inlet": self.initial_inlet.to_dict(),
            "governing_direction": self.governing_direction.to_dict(),
            "governance_policy": dict(self.governance_policy),
            "execution_policy": dict(self.execution_policy),
            "projection_policy": self.projection_policy.to_dict(),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> StartRequest:
        return cls(
            scope_id=str(value["scope_id"]),
            objective_id=str(value["objective_id"]),
            branch_id=str(value.get("branch_id", "main")),
            initial_inlet=ContinuationInlet.from_dict(
                dict(value["initial_inlet"])
            ),
            governing_direction=GoverningDirection.from_dict(
                dict(value["governing_direction"])
            ),
            governance_policy=dict(value.get("governance_policy", {})),
            execution_policy=dict(value.get("execution_policy", {})),
            projection_policy=ProjectionPolicy.from_dict(
                dict(value.get("projection_policy", {}))
            ),
        )


@dataclass(frozen=True, slots=True)
class ResumptionRequest:
    anchor: ResumptionIdentity
    operation: OperationKind
    expected_branch_head_revision_id: str
    inlet: ContinuationInlet | None = None
    projection_policy: ProjectionPolicy = field(default_factory=ProjectionPolicy)
    governance_policy: JsonObject = field(default_factory=dict)
    execution_policy: JsonObject = field(default_factory=dict)
    source_attempt_id: str | None = None
    merge_parent_identities: tuple[ResumptionIdentity, ...] = ()

    def to_dict(self) -> JsonObject:
        return {
            "anchor": self.anchor.to_dict(),
            "operation": self.operation.value,
            "expected_branch_head_revision_id": (
                self.expected_branch_head_revision_id
            ),
            "inlet": self.inlet.to_dict() if self.inlet is not None else None,
            "projection_policy": self.projection_policy.to_dict(),
            "governance_policy": dict(self.governance_policy),
            "execution_policy": dict(self.execution_policy),
            "source_attempt_id": self.source_attempt_id,
            "merge_parent_identities": [
                identity.to_dict()
                for identity in self.merge_parent_identities
            ],
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> ResumptionRequest:
        raw_inlet = value.get("inlet")
        return cls(
            anchor=ResumptionIdentity.from_dict(dict(value["anchor"])),
            operation=OperationKind(value["operation"]),
            expected_branch_head_revision_id=str(
                value["expected_branch_head_revision_id"]
            ),
            inlet=(
                ContinuationInlet.from_dict(dict(raw_inlet))
                if isinstance(raw_inlet, dict)
                else None
            ),
            projection_policy=ProjectionPolicy.from_dict(
                dict(value.get("projection_policy", {}))
            ),
            governance_policy=dict(value.get("governance_policy", {})),
            execution_policy=dict(value.get("execution_policy", {})),
            source_attempt_id=(
                str(value["source_attempt_id"])
                if value.get("source_attempt_id") is not None
                else None
            ),
            merge_parent_identities=tuple(
                ResumptionIdentity.from_dict(dict(item))
                for item in value.get("merge_parent_identities", ())
            ),
        )


@dataclass(frozen=True, slots=True)
class ReductionContext:
    """Prepared semantic context supplied to a controller reduction adapter."""

    projection: ResumptionProjection | None
    operation: OperationKind
    admitted_inlet: ContinuationInlet | None
    candidate_state: SemanticState
    execution_policy: JsonObject


@dataclass(frozen=True, slots=True)
class ReductionProposal:
    """Advisory externally represented result of advancing prepared reduction."""

    delta: SemanticDelta = field(default_factory=SemanticDelta)
    resulting_state: SemanticState | None = None
    semantic_outcome: SemanticOutcome | None = None
    proposal_references: tuple[str, ...] = ()
    proposal_interactions: tuple[JsonObject, ...] = ()
    capability_receipt_references: tuple[str, ...] = ()
    effect_receipt_references: tuple[str, ...] = ()
    reconciliation: JsonObject = field(default_factory=dict)
    presentation: JsonObject = field(default_factory=dict)


@runtime_checkable
class ReductionController(Protocol):
    """Controller-owned adapter for advancing an already prepared reduction."""

    def reduce(
        self,
        context: ReductionContext,
        *,
        should_stop: Callable[[], bool],
    ) -> ReductionProposal: ...


@dataclass(frozen=True, slots=True)
class ResumptionResult:
    source_revision_identity: ResumptionIdentity | None
    execution_attempt_id: str
    execution_outcome: AttemptExecutionOutcome
    semantic_outcome: SemanticOutcome | None
    resulting_revision_identity: ResumptionIdentity | None
    transition_artifact_reference: str | None
    attempt_artifact_reference: str
    realignment_summary: JsonObject | None
    identity_disposition: IdentityDisposition | None
    achieved_state_summary: tuple[str, ...]
    non_achievedness_summary: tuple[str, ...]
    active_hold_summary: tuple[str, ...]
    diagnostics: JsonObject
    presentation: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "source_revision_identity": (
                self.source_revision_identity.to_dict()
                if self.source_revision_identity is not None
                else None
            ),
            "execution_attempt_id": self.execution_attempt_id,
            "execution_outcome": self.execution_outcome.value,
            "semantic_outcome": (
                self.semantic_outcome.value
                if self.semantic_outcome is not None
                else None
            ),
            "resulting_revision_identity": (
                self.resulting_revision_identity.to_dict()
                if self.resulting_revision_identity is not None
                else None
            ),
            "transition_artifact_reference": (
                self.transition_artifact_reference
            ),
            "attempt_artifact_reference": self.attempt_artifact_reference,
            "realignment_summary": (
                dict(self.realignment_summary)
                if self.realignment_summary is not None
                else None
            ),
            "identity_disposition": (
                self.identity_disposition.to_dict()
                if self.identity_disposition is not None
                else None
            ),
            "achieved_state_summary": list(self.achieved_state_summary),
            "non_achievedness_summary": list(
                self.non_achievedness_summary
            ),
            "active_hold_summary": list(self.active_hold_summary),
            "diagnostics": dict(self.diagnostics),
            "presentation": dict(self.presentation),
        }


@dataclass(frozen=True, slots=True)
class InspectionRequest:
    target_kind: InspectionTargetKind
    target_id: str
    view: InspectionView
    scope_id: str | None = None
    objective_id: str | None = None
    branch_id: str | None = None
    principal: str = "local"
    authority_context: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "view": self.view.value,
            "scope_id": self.scope_id,
            "objective_id": self.objective_id,
            "branch_id": self.branch_id,
            "principal": self.principal,
            "authority_context": dict(self.authority_context),
        }

    @classmethod
    def from_dict(cls, value: JsonObject) -> InspectionRequest:
        return cls(
            target_kind=InspectionTargetKind(value["target_kind"]),
            target_id=str(value["target_id"]),
            view=InspectionView(value["view"]),
            scope_id=(
                str(value["scope_id"])
                if value.get("scope_id") is not None
                else None
            ),
            objective_id=(
                str(value["objective_id"])
                if value.get("objective_id") is not None
                else None
            ),
            branch_id=(
                str(value["branch_id"])
                if value.get("branch_id") is not None
                else None
            ),
            principal=str(value.get("principal", "local")),
            authority_context=dict(value.get("authority_context", {})),
        )


@dataclass(frozen=True, slots=True)
class InspectionResult:
    target_kind: InspectionTargetKind
    target_id: str
    view: InspectionView
    payload: JsonObject

    def to_dict(self) -> JsonObject:
        return {
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "view": self.view.value,
            "payload": dict(self.payload),
        }


__all__ = [
    "AdmissionDecision",
    "AdmissionDisposition",
    "ContinuationInlet",
    "GoverningDirection",
    "HoldDisposition",
    "HoldOn",
    "IdentityDisposition",
    "IdentityDispositionKind",
    "InletRelationship",
    "InspectionRequest",
    "InspectionResult",
    "InspectionTargetKind",
    "InspectionView",
    "JsonObject",
    "OperationKind",
    "ProjectionPolicy",
    "Realignment",
    "Reversal",
    "ReductionContext",
    "ReductionController",
    "ReductionProposal",
    "ResumptionIdentity",
    "ResumptionProjection",
    "ResumptionRequest",
    "ResumptionResult",
    "Revision",
    "SemanticDelta",
    "SemanticItem",
    "SemanticOutcome",
    "SemanticState",
    "StartRequest",
    "Supersession",
    "TransitionArtifact",
    "canonical_json",
    "content_digest",
]
