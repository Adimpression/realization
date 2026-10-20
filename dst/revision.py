from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Iterable

from coordinated_transformation.core import Model
from dst.discovery import DstDiscoveryResult
from dst.normalization import DstNormalizedCase
from dst.orchestration import DstOrchestrationResult
from dst.projection import DstNormalizedDecisionProjection
from id_generation import slugify
from semantic_text import collapse_ws


def _ordered_unique_texts(items: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _stable_json_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _snapshot_digest_payload(
    *,
    fixture_id: str,
    subject_id: str,
    question: str,
    source_basis_refs: tuple[str, ...],
    predecessor_snapshot_id: str,
) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "subject_id": subject_id,
        "question": question,
        "source_basis_refs": list(source_basis_refs),
        "predecessor_snapshot_id": predecessor_snapshot_id,
    }


def stable_dst_case_snapshot_id(
    *,
    fixture_id: str,
    subject_id: str,
    question: str,
    source_basis_refs: tuple[str, ...],
    predecessor_snapshot_id: str = "",
) -> str:
    normalized_fixture_id = collapse_ws(fixture_id) or "dst"
    normalized_subject_id = collapse_ws(subject_id) or normalized_fixture_id
    normalized_question = collapse_ws(question)
    digest = _stable_json_digest(
        _snapshot_digest_payload(
            fixture_id=normalized_fixture_id,
            subject_id=normalized_subject_id,
            question=normalized_question,
            source_basis_refs=source_basis_refs,
            predecessor_snapshot_id=collapse_ws(predecessor_snapshot_id),
        )
    )
    slug = slugify(normalized_subject_id or normalized_fixture_id, limit=32) or "dst"
    return f"dstsnap_{slug}_{digest}"


@dataclass(frozen=True)
class DstCaseSnapshot:
    snapshot_id: str
    fixture_id: str
    source_ref: str
    subject_id: str
    question: str
    source_basis_refs: tuple[str, ...]
    source_basis_digest: str
    predecessor_snapshot_id: str = ""
    revision_source: str = ""
    revision_reason: str = ""
    created_at_epoch_ms: int = 0
    discovery_digest: str = ""
    normalized_case_digest: str = ""
    discovery_result: DstDiscoveryResult | None = None
    normalized_case: DstNormalizedCase | None = None
    decision_projection: DstNormalizedDecisionProjection | None = None
    coordinated_model: Model | None = None


@dataclass(frozen=True)
class DstRecordDelta:
    section: str
    added_ids: tuple[str, ...] = ()
    removed_ids: tuple[str, ...] = ()
    changed_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DstRevisionDelta:
    changed_sections: tuple[str, ...] = ()
    record_deltas: tuple[DstRecordDelta, ...] = ()


@dataclass(frozen=True)
class DstEvaluationDelta:
    changed_transition_ids: tuple[str, ...] = ()
    newly_blocked_transition_ids: tuple[str, ...] = ()
    newly_unblocked_transition_ids: tuple[str, ...] = ()
    newly_risky_transition_ids: tuple[str, ...] = ()
    newly_non_risky_transition_ids: tuple[str, ...] = ()
    changed_decision_ids: tuple[str, ...] = ()
    newly_invalid_decision_ids: tuple[str, ...] = ()
    newly_valid_decision_ids: tuple[str, ...] = ()
    newly_blocked_decision_ids: tuple[str, ...] = ()
    newly_executable_decision_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DstRevisionInvalidation:
    source_basis_changed: bool = False
    discovery_changed: bool = False
    requires_discovery_refresh: bool = False
    requires_normalization_refresh: bool = False
    requires_formal_re_evaluation: bool = False
    impacted_transition_ids: tuple[str, ...] = ()
    impacted_decision_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class DstCaseRevision:
    before_snapshot: DstCaseSnapshot
    after_snapshot: DstCaseSnapshot
    structure_delta: DstRevisionDelta
    evaluation_delta: DstEvaluationDelta
    invalidation: DstRevisionInvalidation


@dataclass(frozen=True)
class _RecordSectionSpec:
    section: str
    accessor: Callable[[DstNormalizedCase], tuple[Any, ...]]
    keyer: Callable[[Any], str]
    serializer: Callable[[Any], dict[str, Any]]


def _key_identity(item: Any) -> str:
    return collapse_ws(str(getattr(item, "id", "")))


def _key_capability_requirement(item: Any) -> str:
    return collapse_ws(str(getattr(item, "capability_id", "")))


def _key_admissibility(item: Any) -> str:
    return f"{collapse_ws(str(getattr(item, 'subject_id', '')))}@{collapse_ws(str(getattr(item, 'state_id', '')))}"


def _key_decision_status(item: Any) -> str:
    return f"{collapse_ws(str(getattr(item, 'decision_id', '')))}@{collapse_ws(str(getattr(item, 'state_id', '')))}"


def _key_coordination_requirement(item: Any) -> str:
    return f"{collapse_ws(str(getattr(item, 'type', '')))}@{collapse_ws(str(getattr(item, 'target_id', '')))}"


def _key_risk_indicator(item: Any) -> str:
    return "@".join(
        (
            collapse_ws(str(getattr(item, "target_type", ""))),
            collapse_ws(str(getattr(item, "target_id", ""))),
            collapse_ws(str(getattr(item, "state_id", ""))),
        )
    )


def _key_fallback(item: Any) -> str:
    return f"{collapse_ws(str(getattr(item, 'from_transition_id', '')))}->{collapse_ws(str(getattr(item, 'fallback_transition_id', '')))}"


_RECORD_SECTION_SPECS: tuple[_RecordSectionSpec, ...] = (
    _RecordSectionSpec("actors", lambda case: case.actors, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("objectives", lambda case: case.objectives, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("capabilities", lambda case: case.capabilities, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("dependencies", lambda case: case.dependencies, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("constraints", lambda case: case.constraints, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("boundaries", lambda case: case.boundaries, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("states", lambda case: case.states, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("capability_requirements", lambda case: case.capability_requirements, _key_capability_requirement, lambda item: item.to_dict()),
    _RecordSectionSpec(
        "capability_admissibility",
        lambda case: case.capability_admissibility,
        _key_admissibility,
        lambda item: item.to_dict(subject_key="capability_id"),
    ),
    _RecordSectionSpec("transitions", lambda case: case.transitions, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec(
        "transition_admissibility",
        lambda case: case.transition_admissibility,
        _key_admissibility,
        lambda item: item.to_dict(subject_key="transition_id"),
    ),
    _RecordSectionSpec("decisions", lambda case: case.decisions, _key_identity, lambda item: item.to_dict()),
    _RecordSectionSpec("decision_status", lambda case: case.decision_status, _key_decision_status, lambda item: item.to_dict()),
    _RecordSectionSpec(
        "coordination_requirements",
        lambda case: case.coordination_requirements,
        _key_coordination_requirement,
        lambda item: item.to_dict(),
    ),
    _RecordSectionSpec("risk_indicators", lambda case: case.risk_indicators, _key_risk_indicator, lambda item: item.to_dict()),
    _RecordSectionSpec("fallbacks", lambda case: case.fallbacks, _key_fallback, lambda item: item.to_dict()),
)

_ADMISSIBILITY_SENSITIVE_SECTIONS: frozenset[str] = frozenset(
    {
        "actors",
        "capabilities",
        "dependencies",
        "constraints",
        "boundaries",
        "states",
        "capability_requirements",
        "capability_admissibility",
        "transitions",
        "transition_admissibility",
        "decisions",
        "decision_status",
        "coordination_requirements",
        "risk_indicators",
        "fallbacks",
        "candidate_sets",
    }
)


def build_dst_case_snapshot(
    *,
    discovery_result: DstDiscoveryResult,
    normalized_case: DstNormalizedCase,
    decision_projection: DstNormalizedDecisionProjection,
    coordinated_model: Model,
    source_basis_refs: tuple[str, ...] = (),
    subject_id: str = "",
    question: str = "",
    predecessor_snapshot_id: str = "",
    revision_source: str = "",
    revision_reason: str = "",
    created_at_epoch_ms: int = 0,
) -> DstCaseSnapshot:
    normalized_subject_id = collapse_ws(subject_id) or collapse_ws(decision_projection.frame.subject_id) or normalized_case.fixture_id
    normalized_question = collapse_ws(question) or collapse_ws(decision_projection.frame.question)
    normalized_source_ref = collapse_ws(normalized_case.source_ref) or collapse_ws(discovery_result.source_ref)
    normalized_source_basis_refs = _ordered_unique_texts(source_basis_refs or (normalized_source_ref,))
    source_basis_digest = _stable_json_digest(list(normalized_source_basis_refs))
    snapshot_id = stable_dst_case_snapshot_id(
        fixture_id=normalized_case.fixture_id,
        subject_id=normalized_subject_id,
        question=normalized_question,
        source_basis_refs=normalized_source_basis_refs,
        predecessor_snapshot_id=collapse_ws(predecessor_snapshot_id),
    )
    return DstCaseSnapshot(
        snapshot_id=snapshot_id,
        fixture_id=normalized_case.fixture_id,
        source_ref=normalized_source_ref,
        subject_id=normalized_subject_id,
        question=normalized_question,
        source_basis_refs=normalized_source_basis_refs,
        source_basis_digest=source_basis_digest,
        predecessor_snapshot_id=collapse_ws(predecessor_snapshot_id),
        revision_source=collapse_ws(revision_source),
        revision_reason=collapse_ws(revision_reason),
        created_at_epoch_ms=max(
            0,
            int(created_at_epoch_ms or getattr(decision_projection.frame, "updated_at_epoch_ms", 0) or 0),
        ),
        discovery_digest=_stable_json_digest(discovery_result.to_dict()),
        normalized_case_digest=_stable_json_digest(normalized_case.to_dict()),
        discovery_result=discovery_result,
        normalized_case=normalized_case,
        decision_projection=decision_projection,
        coordinated_model=coordinated_model,
    )


def build_dst_case_snapshot_from_orchestration_result(
    result: DstOrchestrationResult,
    *,
    source_basis_refs: tuple[str, ...] = (),
    subject_id: str = "",
    question: str = "",
    predecessor_snapshot_id: str = "",
    revision_source: str = "",
    revision_reason: str = "",
    created_at_epoch_ms: int = 0,
) -> DstCaseSnapshot:
    return build_dst_case_snapshot(
        discovery_result=result.discovery_result,
        normalized_case=result.normalized_case,
        decision_projection=result.decision_projection,
        coordinated_model=result.coordinated_model,
        source_basis_refs=source_basis_refs or (result.fixture.source_ref, result.normalized_case.source_ref),
        subject_id=subject_id or result.decision_projection.frame.subject_id,
        question=question or result.decision_projection.frame.question,
        predecessor_snapshot_id=predecessor_snapshot_id,
        revision_source=revision_source,
        revision_reason=revision_reason,
        created_at_epoch_ms=created_at_epoch_ms or result.decision_projection.frame.updated_at_epoch_ms,
    )


def _record_payloads(
    records: tuple[Any, ...],
    keyer: Callable[[Any], str],
    serializer: Callable[[Any], dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for item in records:
        key = collapse_ws(keyer(item))
        if not key:
            continue
        payloads[key] = dict(serializer(item))
    return payloads


def _build_record_delta(
    *,
    section: str,
    before_records: tuple[Any, ...],
    after_records: tuple[Any, ...],
    keyer: Callable[[Any], str],
    serializer: Callable[[Any], dict[str, Any]],
) -> DstRecordDelta | None:
    before_payloads = _record_payloads(before_records, keyer, serializer)
    after_payloads = _record_payloads(after_records, keyer, serializer)
    before_keys = set(before_payloads)
    after_keys = set(after_payloads)
    added = tuple(sorted(after_keys - before_keys))
    removed = tuple(sorted(before_keys - after_keys))
    changed = tuple(
        sorted(
            key
            for key in (before_keys & after_keys)
            if before_payloads[key] != after_payloads[key]
        )
    )
    if not added and not removed and not changed:
        return None
    return DstRecordDelta(
        section=section,
        added_ids=added,
        removed_ids=removed,
        changed_ids=changed,
    )


def _transition_admissibility_by_id(case: DstNormalizedCase) -> dict[str, dict[str, Any]]:
    evaluation_state_id = collapse_ws(case.context.evaluation_state_id)
    result: dict[str, dict[str, Any]] = {}
    for item in case.transition_admissibility:
        if evaluation_state_id and item.state_id != evaluation_state_id:
            continue
        payload = item.to_dict(subject_key="transition_id")
        result[item.subject_id] = payload
    return result


def _decision_status_by_id(case: DstNormalizedCase) -> dict[str, dict[str, Any]]:
    evaluation_state_id = collapse_ws(case.context.evaluation_state_id)
    result: dict[str, dict[str, Any]] = {}
    for item in case.decision_status:
        if evaluation_state_id and item.state_id != evaluation_state_id:
            continue
        result[item.decision_id] = item.to_dict()
    return result


def _transition_risks_by_id(case: DstNormalizedCase) -> dict[str, tuple[str, ...]]:
    evaluation_state_id = collapse_ws(case.context.evaluation_state_id)
    result: dict[str, tuple[str, ...]] = {}
    for item in case.risk_indicators:
        if item.target_type != "transition":
            continue
        if evaluation_state_id and item.state_id and item.state_id != evaluation_state_id:
            continue
        result[item.target_id] = tuple(item.risks)
    return result


def _candidate_transition_ids(case: DstNormalizedCase) -> tuple[str, ...]:
    return tuple(case.candidate_sets.candidate_transition_ids_from_current_state)


def _candidate_decision_ids(case: DstNormalizedCase) -> tuple[str, ...]:
    return tuple(case.candidate_sets.candidate_decision_ids_from_current_state)


def _build_structure_delta(before_case: DstNormalizedCase, after_case: DstNormalizedCase) -> DstRevisionDelta:
    changed_sections: list[str] = []
    record_deltas: list[DstRecordDelta] = []

    if before_case.source_ref != after_case.source_ref:
        changed_sections.append("source_ref")
    if before_case.context.to_dict() != after_case.context.to_dict():
        changed_sections.append("context")

    for spec in _RECORD_SECTION_SPECS:
        delta = _build_record_delta(
            section=spec.section,
            before_records=spec.accessor(before_case),
            after_records=spec.accessor(after_case),
            keyer=spec.keyer,
            serializer=spec.serializer,
        )
        if delta is None:
            continue
        changed_sections.append(spec.section)
        record_deltas.append(delta)

    if before_case.candidate_sets.to_dict() != after_case.candidate_sets.to_dict():
        changed_sections.append("candidate_sets")
    if before_case.assumptions != after_case.assumptions:
        changed_sections.append("assumptions")
    if before_case.ambiguities != after_case.ambiguities:
        changed_sections.append("ambiguities")
    if before_case.missing_information != after_case.missing_information:
        changed_sections.append("missing_information")
    if before_case.schema_version != after_case.schema_version:
        changed_sections.append("schema_version")

    return DstRevisionDelta(
        changed_sections=_ordered_unique_texts(changed_sections),
        record_deltas=tuple(record_deltas),
    )


def _build_evaluation_delta(before_case: DstNormalizedCase, after_case: DstNormalizedCase) -> DstEvaluationDelta:
    before_transition = _transition_admissibility_by_id(before_case)
    after_transition = _transition_admissibility_by_id(after_case)
    before_transition_risks = _transition_risks_by_id(before_case)
    after_transition_risks = _transition_risks_by_id(after_case)
    before_decisions = _decision_status_by_id(before_case)
    after_decisions = _decision_status_by_id(after_case)

    candidate_transition_delta = set(_candidate_transition_ids(before_case)) ^ set(_candidate_transition_ids(after_case))
    candidate_decision_delta = set(_candidate_decision_ids(before_case)) ^ set(_candidate_decision_ids(after_case))

    transition_ids = set(before_transition) | set(after_transition) | set(before_transition_risks) | set(after_transition_risks) | candidate_transition_delta
    changed_transition_ids: list[str] = []
    newly_blocked_transition_ids: list[str] = []
    newly_unblocked_transition_ids: list[str] = []
    newly_risky_transition_ids: list[str] = []
    newly_non_risky_transition_ids: list[str] = []
    for transition_id in sorted(transition_ids):
        before_transition_payload = before_transition.get(transition_id)
        after_transition_payload = after_transition.get(transition_id)
        before_admissible = None if before_transition_payload is None else before_transition_payload.get("admissible")
        after_admissible = None if after_transition_payload is None else after_transition_payload.get("admissible")
        before_risks = before_transition_risks.get(transition_id, ())
        after_risks = after_transition_risks.get(transition_id, ())
        if (
            before_transition_payload != after_transition_payload
            or before_risks != after_risks
            or transition_id in candidate_transition_delta
        ):
            changed_transition_ids.append(transition_id)
        if before_admissible is True and after_admissible is False:
            newly_blocked_transition_ids.append(transition_id)
        if before_admissible is False and after_admissible is True:
            newly_unblocked_transition_ids.append(transition_id)
        if not before_risks and after_risks:
            newly_risky_transition_ids.append(transition_id)
        if before_risks and not after_risks:
            newly_non_risky_transition_ids.append(transition_id)

    decision_ids = set(before_decisions) | set(after_decisions) | candidate_decision_delta
    changed_decision_ids: list[str] = []
    newly_invalid_decision_ids: list[str] = []
    newly_valid_decision_ids: list[str] = []
    newly_blocked_decision_ids: list[str] = []
    newly_executable_decision_ids: list[str] = []
    for decision_id in sorted(decision_ids):
        before_payload = before_decisions.get(decision_id)
        after_payload = after_decisions.get(decision_id)
        before_valid = None if before_payload is None else before_payload.get("valid")
        after_valid = None if after_payload is None else after_payload.get("valid")
        before_executable = None if before_payload is None else before_payload.get("executable")
        after_executable = None if after_payload is None else after_payload.get("executable")
        if before_payload != after_payload or decision_id in candidate_decision_delta:
            changed_decision_ids.append(decision_id)
        if before_valid is True and after_valid is False:
            newly_invalid_decision_ids.append(decision_id)
        if before_valid is False and after_valid is True:
            newly_valid_decision_ids.append(decision_id)
        if before_executable is True and after_executable is False:
            newly_blocked_decision_ids.append(decision_id)
        if before_executable is False and after_executable is True:
            newly_executable_decision_ids.append(decision_id)

    return DstEvaluationDelta(
        changed_transition_ids=tuple(changed_transition_ids),
        newly_blocked_transition_ids=tuple(newly_blocked_transition_ids),
        newly_unblocked_transition_ids=tuple(newly_unblocked_transition_ids),
        newly_risky_transition_ids=tuple(newly_risky_transition_ids),
        newly_non_risky_transition_ids=tuple(newly_non_risky_transition_ids),
        changed_decision_ids=tuple(changed_decision_ids),
        newly_invalid_decision_ids=tuple(newly_invalid_decision_ids),
        newly_valid_decision_ids=tuple(newly_valid_decision_ids),
        newly_blocked_decision_ids=tuple(newly_blocked_decision_ids),
        newly_executable_decision_ids=tuple(newly_executable_decision_ids),
    )


def _build_invalidation(
    before_snapshot: DstCaseSnapshot,
    after_snapshot: DstCaseSnapshot,
    structure_delta: DstRevisionDelta,
    evaluation_delta: DstEvaluationDelta,
) -> DstRevisionInvalidation:
    source_basis_changed = before_snapshot.source_basis_refs != after_snapshot.source_basis_refs
    discovery_changed = before_snapshot.discovery_digest != after_snapshot.discovery_digest
    requires_discovery_refresh = source_basis_changed or discovery_changed
    requires_normalization_refresh = (
        requires_discovery_refresh
        or before_snapshot.normalized_case_digest != after_snapshot.normalized_case_digest
        or bool(structure_delta.changed_sections)
    )
    impacted_transition_ids = _ordered_unique_texts(
        (
            *evaluation_delta.changed_transition_ids,
        )
    )
    impacted_decision_ids = _ordered_unique_texts(
        (
            *evaluation_delta.changed_decision_ids,
        )
    )
    requires_formal_re_evaluation = bool(
        set(structure_delta.changed_sections) & _ADMISSIBILITY_SENSITIVE_SECTIONS
        or impacted_transition_ids
        or impacted_decision_ids
    )
    reasons: list[str] = []
    if source_basis_changed:
        reasons.append("source_basis_refs_changed")
    if discovery_changed:
        reasons.append("discovery_result_changed")
    for section in structure_delta.changed_sections:
        reasons.append(f"normalized_section_changed:{section}")
    if evaluation_delta.newly_blocked_transition_ids:
        reasons.append("transition_admissibility_narrowed")
    if evaluation_delta.newly_unblocked_transition_ids:
        reasons.append("transition_admissibility_expanded")
    if evaluation_delta.newly_blocked_decision_ids:
        reasons.append("decision_executability_narrowed")
    if evaluation_delta.newly_executable_decision_ids:
        reasons.append("decision_executability_expanded")
    if evaluation_delta.newly_risky_transition_ids:
        reasons.append("transition_risk_increased")
    if evaluation_delta.newly_non_risky_transition_ids:
        reasons.append("transition_risk_reduced")
    return DstRevisionInvalidation(
        source_basis_changed=source_basis_changed,
        discovery_changed=discovery_changed,
        requires_discovery_refresh=requires_discovery_refresh,
        requires_normalization_refresh=requires_normalization_refresh,
        requires_formal_re_evaluation=requires_formal_re_evaluation,
        impacted_transition_ids=impacted_transition_ids,
        impacted_decision_ids=impacted_decision_ids,
        reasons=_ordered_unique_texts(reasons),
    )


def build_dst_case_revision(
    before_snapshot: DstCaseSnapshot,
    after_snapshot: DstCaseSnapshot,
) -> DstCaseRevision:
    if before_snapshot.normalized_case is None or after_snapshot.normalized_case is None:
        raise ValueError("dst case revision requires normalized snapshots")
    structure_delta = _build_structure_delta(
        before_snapshot.normalized_case,
        after_snapshot.normalized_case,
    )
    evaluation_delta = _build_evaluation_delta(
        before_snapshot.normalized_case,
        after_snapshot.normalized_case,
    )
    invalidation = _build_invalidation(
        before_snapshot,
        after_snapshot,
        structure_delta,
        evaluation_delta,
    )
    return DstCaseRevision(
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        structure_delta=structure_delta,
        evaluation_delta=evaluation_delta,
        invalidation=invalidation,
    )


__all__ = [
    "DstCaseRevision",
    "DstCaseSnapshot",
    "DstEvaluationDelta",
    "DstRecordDelta",
    "DstRevisionDelta",
    "DstRevisionInvalidation",
    "build_dst_case_revision",
    "build_dst_case_snapshot",
    "build_dst_case_snapshot_from_orchestration_result",
    "stable_dst_case_snapshot_id",
]
