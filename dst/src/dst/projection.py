from __future__ import annotations

from dataclasses import dataclass
import hashlib

from coordinated_transformation.core import (
    Actor,
    Boundary,
    Capability,
    Constraint,
    Decision,
    Dependency,
    Model,
    Objective,
    State,
    Transition,
)
from realized_core_semantics.decision_review import (
    DecisionFrame,
    DecisionReviewItem,
    stable_decision_frame_id,
    stable_decision_review_item_id,
)
from realized_core_semantics.transformation_constructs import (
    TransformationConstructCandidate,
    stable_transformation_construct_candidate_id,
)
from dst.core import DstUseCaseFixture
from dst.normalization import DstNormalizedCase
from realized_core_semantics.identifiers import slugify
from realized_core_semantics.semantic_text import collapse_ws


_SECTION_ROLE_MAP: tuple[tuple[str, str], ...] = (
    ("actors", "actor"),
    ("objectives", "objective"),
    ("capabilities", "capability"),
    ("dependencies", "dependency"),
    ("constraints", "constraint"),
    ("boundaries", "boundary"),
)


@dataclass(frozen=True)
class DstDecisionProjection:
    fixture: DstUseCaseFixture
    frame: DecisionFrame
    items: tuple[DecisionReviewItem, ...]
    current_state_codes: tuple[str, ...]
    target_state_codes: tuple[str, ...]
    direct_decision_titles: tuple[str, ...]
    indirect_decision_titles: tuple[str, ...]


@dataclass(frozen=True)
class DstNormalizedDecisionProjection:
    case: DstNormalizedCase
    frame: DecisionFrame
    items: tuple[DecisionReviewItem, ...]
    current_state_ids: tuple[str, ...]
    target_state_ids: tuple[str, ...]
    candidate_transition_ids: tuple[str, ...]
    candidate_decision_ids: tuple[str, ...]


@dataclass(frozen=True)
class DstNormalizedConstructProjection:
    case: DstNormalizedCase
    candidates: tuple[TransformationConstructCandidate, ...]


def _stable_dst_review_item_id(
    *,
    fixture_id: str,
    decision_role: str,
    label: str,
) -> str:
    normalized = collapse_ws(label) or decision_role
    slug = slugify(normalized, limit=48) or decision_role
    digest = hashlib.sha256(
        f"{fixture_id}::{decision_role}::{normalized}".encode("utf-8")
    ).hexdigest()[:10]
    return f"dstrev_{decision_role}_{slug}_{digest}"


def _stable_normalized_review_item_id(
    *,
    fixture_id: str,
    decision_role: str,
    label: str,
) -> str:
    normalized = collapse_ws(label) or decision_role
    slug = slugify(normalized, limit=48) or decision_role
    digest = hashlib.sha256(
        f"{fixture_id}::normalized::{decision_role}::{normalized}".encode("utf-8")
    ).hexdigest()[:10]
    return f"dstnrev_{decision_role}_{slug}_{digest}"


def _route_tokens(route_expression: str) -> tuple[str, ...]:
    tokens = [collapse_ws(token) for token in route_expression.split("->") if collapse_ws(token)]
    return tuple(tokens)


def _default_decision_question(fixture: DstUseCaseFixture) -> str:
    return f"What decision should guide {fixture.title}?"


def _default_normalized_question(case: DstNormalizedCase) -> str:
    decision_problem = collapse_ws(case.context.decision_problem)
    if decision_problem:
        return decision_problem
    system_name = collapse_ws(case.context.system_name) or case.fixture_id
    return f"What decision should guide {system_name}?"


def _default_current_state_codes(fixture: DstUseCaseFixture) -> tuple[str, ...]:
    route_starts = []
    for path in fixture.candidate_paths:
        tokens = _route_tokens(path.route_expression)
        if tokens:
            route_starts.append(tokens[0])
    if route_starts:
        seen: set[str] = set()
        ordered: list[str] = []
        for token in route_starts:
            if token in seen:
                continue
            seen.add(token)
            ordered.append(token)
        return tuple(ordered)
    state_entries = fixture.section_entries("states")
    if state_entries:
        first = state_entries[0].seed_name()
        return (first,) if first else ()
    return ()


def _default_target_state_codes(fixture: DstUseCaseFixture) -> tuple[str, ...]:
    route_ends = []
    for path in fixture.candidate_paths:
        tokens = _route_tokens(path.route_expression)
        if tokens:
            route_ends.append(tokens[-1])
    if route_ends:
        seen: set[str] = set()
        ordered: list[str] = []
        for token in route_ends:
            if token in seen:
                continue
            seen.add(token)
            ordered.append(token)
        return tuple(ordered)
    state_entries = fixture.section_entries("states")
    if state_entries:
        last = state_entries[-1].seed_name()
        return (last,) if last else ()
    return ()


def project_dst_fixture_to_decision_frame(
    fixture: DstUseCaseFixture,
    *,
    subject_id: str = "",
    question: str = "",
    decision_mode: str = "decision_aid",
    build_epoch_ms: int = 0,
) -> DstDecisionProjection:
    normalized_subject_id = collapse_ws(subject_id) or fixture.fixture_id
    normalized_question = collapse_ws(question) or _default_decision_question(fixture)
    current_state_codes = _default_current_state_codes(fixture)
    target_state_codes = _default_target_state_codes(fixture)

    frame_id = stable_decision_frame_id(
        subject_id=normalized_subject_id,
        question=normalized_question,
    )

    items: list[DecisionReviewItem] = []
    current_state_item_ids: list[str] = []
    target_state_item_ids: list[str] = []
    primary_objective_item_ids: list[str] = []
    scope_boundary_item_ids: list[str] = []
    direct_decision_titles: list[str] = []
    indirect_decision_titles: list[str] = []

    def add_item(
        *,
        decision_role: str,
        label: str,
        notes: str = "",
        metadata: dict[str, object] | None = None,
    ) -> str:
        review_item_id = _stable_dst_review_item_id(
            fixture_id=fixture.fixture_id,
            decision_role=decision_role,
            label=label,
        )
        item = DecisionReviewItem(
            decision_review_item_id=stable_decision_review_item_id(
                decision_frame_id=frame_id,
                review_item_id=review_item_id,
                decision_role=decision_role,
            ),
            review_item_id=review_item_id,
            decision_frame_id=frame_id,
            decision_role=decision_role,
            included=True,
            ordering=len(items) + 1,
            source_refs=(fixture.source_ref,),
            confidence=1.0,
            notes=notes,
            status="active",
            created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
            updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
            metadata={
                "canonical_label": label,
                "source_ref": fixture.source_ref,
                "fixture_id": fixture.fixture_id,
                **(metadata or {}),
            },
        )
        items.append(item)
        return item.decision_review_item_id

    for section_key, decision_role in _SECTION_ROLE_MAP:
        for entry in fixture.section_entries(section_key):
            label = entry.seed_name()
            item_id = add_item(
                decision_role=decision_role,
                label=label,
                notes=entry.text,
                metadata={
                    "fixture_entry_code": entry.code,
                    "fixture_entry_text": entry.text,
                    "section_key": section_key,
                },
            )
            if decision_role == "objective":
                primary_objective_item_ids.append(item_id)
            elif decision_role == "boundary":
                scope_boundary_item_ids.append(item_id)

    for code in current_state_codes:
        current_state_item_ids.append(
            add_item(
                decision_role="current_state",
                label=code,
                metadata={"state_code": code},
            )
        )
    for code in target_state_codes:
        target_state_item_ids.append(
            add_item(
                decision_role="target_state",
                label=code,
                metadata={"state_code": code},
            )
        )

    for entry in fixture.section_entries("transitions"):
        add_item(
            decision_role="transition_candidate",
            label=entry.seed_name(),
            notes=entry.text,
            metadata={
                "fixture_entry_code": entry.code,
                "fixture_entry_text": entry.text,
                "section_key": "transitions",
            },
        )

    for path in fixture.candidate_paths:
        tokens = _route_tokens(path.route_expression)
        if len(tokens) == 2:
            direct_decision_titles.append(path.title)
        else:
            indirect_decision_titles.append(path.title)
        add_item(
            decision_role="decision_candidate",
            label=path.title,
            notes=path.narrative,
            metadata={
                "route_expression": path.route_expression,
                "path_parent_title": path.parent_title,
                "path_highlights": list(path.highlights),
                "path_kind": "direct" if len(tokens) == 2 else "multi_step",
            },
        )

    if fixture.summary:
        add_item(
            decision_role="supporting_evidence",
            label=f"{fixture.title} source summary",
            notes=fixture.summary,
            metadata={"evidence_summary": fixture.summary},
        )

    frame = DecisionFrame(
        decision_frame_id=frame_id,
        subject_id=normalized_subject_id,
        question=normalized_question,
        decision_mode=decision_mode,
        current_state_ids=tuple(current_state_item_ids),
        target_state_ids=tuple(target_state_item_ids),
        primary_objective_ids=tuple(primary_objective_item_ids),
        scope_boundary_ids=tuple(scope_boundary_item_ids),
        status="draft",
        created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata={
            "fixture_id": fixture.fixture_id,
            "source_ref": fixture.source_ref,
            "direct_decision_titles": list(direct_decision_titles),
            "indirect_decision_titles": list(indirect_decision_titles),
        },
    )
    return DstDecisionProjection(
        fixture=fixture,
        frame=frame,
        items=tuple(items),
        current_state_codes=current_state_codes,
        target_state_codes=target_state_codes,
        direct_decision_titles=tuple(direct_decision_titles),
        indirect_decision_titles=tuple(indirect_decision_titles),
    )


def project_normalized_case_to_decision_frame(
    case: DstNormalizedCase,
    *,
    subject_id: str = "",
    question: str = "",
    decision_mode: str = "decision_aid",
    build_epoch_ms: int = 0,
) -> DstNormalizedDecisionProjection:
    normalized_subject_id = collapse_ws(subject_id) or case.fixture_id
    normalized_question = collapse_ws(question) or _default_normalized_question(case)
    frame_id = stable_decision_frame_id(
        subject_id=normalized_subject_id,
        question=normalized_question,
    )

    items: list[DecisionReviewItem] = []
    current_state_item_ids: list[str] = []
    target_state_item_ids: list[str] = []
    primary_objective_item_ids: list[str] = []
    scope_boundary_item_ids: list[str] = []
    actor_item_id_by_normalized_id: dict[str, str] = {}
    objective_item_id_by_normalized_id: dict[str, str] = {}
    capability_item_id_by_normalized_id: dict[str, str] = {}
    dependency_item_id_by_normalized_id: dict[str, str] = {}
    constraint_item_id_by_normalized_id: dict[str, str] = {}
    boundary_item_id_by_normalized_id: dict[str, str] = {}
    state_item_id_by_normalized_id: dict[str, str] = {}
    transition_item_id_by_normalized_id: dict[str, str] = {}

    def add_item(
        *,
        decision_role: str,
        label: str,
        notes: str = "",
        metadata: dict[str, object] | None = None,
    ) -> str:
        review_item_id = _stable_normalized_review_item_id(
            fixture_id=case.fixture_id,
            decision_role=decision_role,
            label=label,
        )
        item = DecisionReviewItem(
            decision_review_item_id=stable_decision_review_item_id(
                decision_frame_id=frame_id,
                review_item_id=review_item_id,
                decision_role=decision_role,
            ),
            review_item_id=review_item_id,
            decision_frame_id=frame_id,
            decision_role=decision_role,
            included=True,
            ordering=len(items) + 1,
            source_refs=(case.source_ref,),
            confidence=1.0,
            notes=notes,
            status="active",
            created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
            updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
            metadata={
                "canonical_label": label,
                "source_ref": case.source_ref,
                "fixture_id": case.fixture_id,
                **(metadata or {}),
            },
        )
        items.append(item)
        return item.decision_review_item_id

    capability_requirement_by_id = {
        item.capability_id: item for item in case.capability_requirements
    }
    decision_status_by_decision_id = {
        item.decision_id: item
        for item in case.decision_status
        if item.state_id == case.context.evaluation_state_id
    }
    admissible_transition_ids = set(case.candidate_sets.candidate_transition_ids_from_current_state)

    for actor in case.actors:
        item_id = add_item(
            decision_role="actor",
            label=actor.name,
            notes=", ".join(actor.roles),
            metadata={"actor_id": actor.id, "roles": list(actor.roles), "can_decide": actor.can_decide},
        )
        actor_item_id_by_normalized_id[actor.id] = item_id
    for objective in case.objectives:
        item_id = add_item(
            decision_role="objective",
            label=objective.name,
            metadata={
                "objective_id": objective.id,
                "shared": objective.shared,
                "mandatory": objective.mandatory,
                "pursued_by": list(objective.pursued_by),
            },
        )
        primary_objective_item_ids.append(item_id)
        objective_item_id_by_normalized_id[objective.id] = item_id
    for dependency in case.dependencies:
        item_id = add_item(
            decision_role="dependency",
            label=dependency.name,
            metadata={"dependency_id": dependency.id},
        )
        dependency_item_id_by_normalized_id[dependency.id] = item_id
    for constraint in case.constraints:
        item_id = add_item(
            decision_role="constraint",
            label=constraint.name,
            metadata={"constraint_id": constraint.id, "kind": constraint.kind},
        )
        constraint_item_id_by_normalized_id[constraint.id] = item_id
    for boundary in case.boundaries:
        item_id = add_item(
            decision_role="boundary",
            label=boundary.name,
            metadata={"boundary_id": boundary.id},
        )
        scope_boundary_item_ids.append(item_id)
        boundary_item_id_by_normalized_id[boundary.id] = item_id
    for capability in case.capabilities:
        requirement = capability_requirement_by_id.get(capability.id)
        item_id = add_item(
            decision_role="capability",
            label=capability.name,
            metadata={
                "capability_id": capability.id,
                "kind": capability.kind,
                "controlled_by": list(capability.controlled_by),
                "required_dependency_decision_review_item_ids": [
                    dependency_item_id_by_normalized_id[dependency_id]
                    for dependency_id in getattr(requirement, "required_dependencies", ())
                    if dependency_id in dependency_item_id_by_normalized_id
                ],
                "crossed_boundary_decision_review_item_ids": [
                    boundary_item_id_by_normalized_id[boundary_id]
                    for boundary_id in getattr(requirement, "crossed_boundaries", ())
                    if boundary_id in boundary_item_id_by_normalized_id
                ],
            },
        )
        capability_item_id_by_normalized_id[capability.id] = item_id
    for state in case.states:
        state_label = state.name
        decision_role = "current_state" if state.is_current is True else "target_state"
        item_id = add_item(
            decision_role=decision_role,
            label=state_label,
            metadata={"state_id": state.id},
        )
        state_item_id_by_normalized_id[state.id] = item_id
        if state.is_current is True:
            current_state_item_ids.append(item_id)
        if state.is_target is True:
            target_state_item_ids.append(item_id)
    for transition in case.transitions:
        item_id = add_item(
            decision_role="transition_candidate",
            label=transition.name,
            notes=f"{transition.source_state_id} -> {transition.target_state_id}",
            metadata={
                "transition_id": transition.id,
                "dst_normalized_transition_id": transition.id,
                "dst_admissible_in_evaluation_state": transition.id in admissible_transition_ids,
                "source_state_id": transition.source_state_id,
                "target_state_id": transition.target_state_id,
                "changes_capabilities": list(transition.changes_capabilities),
                "source_state_decision_review_item_id": state_item_id_by_normalized_id.get(
                    transition.source_state_id,
                    "",
                ),
                "target_state_decision_review_item_id": state_item_id_by_normalized_id.get(
                    transition.target_state_id,
                    "",
                ),
                "changed_capability_decision_review_item_ids": [
                    capability_item_id_by_normalized_id[capability_id]
                    for capability_id in transition.changes_capabilities
                    if capability_id in capability_item_id_by_normalized_id
                ],
                "required_dependency_decision_review_item_ids": [
                    dependency_item_id_by_normalized_id[dependency_id]
                    for dependency_id in transition.required_dependencies
                    if dependency_id in dependency_item_id_by_normalized_id
                ],
                "crossed_boundary_decision_review_item_ids": [
                    boundary_item_id_by_normalized_id[boundary_id]
                    for boundary_id in transition.crossed_boundaries
                    if boundary_id in boundary_item_id_by_normalized_id
                ],
                "constraining_constraint_decision_review_item_ids": [
                    constraint_item_id_by_normalized_id[constraint_id]
                    for constraint_id in transition.constraining_constraints
                    if constraint_id in constraint_item_id_by_normalized_id
                ],
            },
        )
        transition_item_id_by_normalized_id[transition.id] = item_id
    for decision in case.decisions:
        decision_status = decision_status_by_decision_id.get(decision.id)
        status_bits = [
            f"transition={decision.selects_transition_id}",
            f"time={decision.time_label or '<none>'}",
        ]
        add_item(
            decision_role="decision_candidate",
            label=decision.name,
            notes=", ".join(status_bits),
            metadata={
                "decision_id": decision.id,
                "dst_normalized_decision_id": decision.id,
                "dst_valid_in_evaluation_state": None if decision_status is None else decision_status.valid,
                "dst_executable_in_evaluation_state": None if decision_status is None else decision_status.executable,
                "selects_transition_id": decision.selects_transition_id,
                "assignment_count": len(decision.assignments),
                "time_label": decision.time_label,
                "selected_transition_decision_review_item_ids": [
                    transition_item_id_by_normalized_id[decision.selects_transition_id]
                ]
                if decision.selects_transition_id in transition_item_id_by_normalized_id
                else [],
                "assigned_actor_decision_review_item_ids": [
                    actor_item_id_by_normalized_id[assignment.actor_id]
                    for assignment in decision.assignments
                    if assignment.actor_id in actor_item_id_by_normalized_id
                    and assignment.capability_id in capability_item_id_by_normalized_id
                ],
                "assigned_capability_decision_review_item_ids": [
                    capability_item_id_by_normalized_id[assignment.capability_id]
                    for assignment in decision.assignments
                    if assignment.actor_id in actor_item_id_by_normalized_id
                    and assignment.capability_id in capability_item_id_by_normalized_id
                ],
            },
        )

    if case.context.notes or case.assumptions or case.ambiguities or case.missing_information:
        notes_lines: list[str] = []
        if case.context.notes:
            notes_lines.append("context.notes: " + "; ".join(case.context.notes))
        if case.assumptions:
            notes_lines.append("assumptions: " + "; ".join(case.assumptions))
        if case.ambiguities:
            notes_lines.append("ambiguities: " + "; ".join(case.ambiguities))
        if case.missing_information:
            notes_lines.append("missing_information: " + "; ".join(case.missing_information))
        add_item(
            decision_role="supporting_evidence",
            label=f"{case.context.system_name or case.fixture_id} normalized case notes",
            notes="\n".join(notes_lines),
            metadata={"note_groups": len(notes_lines)},
        )

    frame = DecisionFrame(
        decision_frame_id=frame_id,
        subject_id=normalized_subject_id,
        question=normalized_question,
        decision_mode=decision_mode,
        current_state_ids=tuple(current_state_item_ids),
        target_state_ids=tuple(target_state_item_ids),
        primary_objective_ids=tuple(primary_objective_item_ids),
        scope_boundary_ids=tuple(scope_boundary_item_ids),
        status="draft",
        created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        updated_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata={
            "fixture_id": case.fixture_id,
            "source_ref": case.source_ref,
            "dst_normalized_status_seeded": True,
            "evaluation_state_id": case.context.evaluation_state_id,
            "candidate_transition_ids": list(case.candidate_sets.candidate_transition_ids_from_current_state),
            "candidate_decision_ids": list(case.candidate_sets.candidate_decision_ids_from_current_state),
        },
    )
    return DstNormalizedDecisionProjection(
        case=case,
        frame=frame,
        items=tuple(items),
        current_state_ids=tuple(state.id for state in case.states if state.is_current is True),
        target_state_ids=tuple(state.id for state in case.states if state.is_target is True),
        candidate_transition_ids=case.candidate_sets.candidate_transition_ids_from_current_state,
        candidate_decision_ids=case.candidate_sets.candidate_decision_ids_from_current_state,
    )


def project_normalized_case_to_transformation_construct_candidates(
    case: DstNormalizedCase,
    *,
    subject_id: str,
    itemized_item_id: str,
    source_refs: tuple[str, ...] = (),
    review_item_id: str = "",
    build_epoch_ms: int = 0,
) -> DstNormalizedConstructProjection:
    normalized_subject_id = collapse_ws(subject_id) or case.fixture_id
    normalized_itemized_item_id = collapse_ws(itemized_item_id)
    normalized_review_item_id = collapse_ws(review_item_id)
    normalized_source_refs = tuple(
        item for item in (collapse_ws(str(ref)) for ref in source_refs) if item
    )
    now_epoch_ms = max(0, int(build_epoch_ms or 0))
    base_relation_hints = {
        "dst_construct_source": "dst_runtime",
        "dst_fixture_id": case.fixture_id,
    }
    default_summary = collapse_ws(case.context.decision_problem) or (
        f"DST normalized construct candidate for {collapse_ws(case.context.system_name) or case.fixture_id}."
    )
    candidates: list[TransformationConstructCandidate] = []

    def add_candidate(
        *,
        sort_kind: str,
        label: str,
        summary: str = "",
        confidence: float = 0.82,
        relation_hints: dict[str, object] | None = None,
    ) -> None:
        normalized_label = collapse_ws(label)
        if not normalized_label:
            return
        merged_relation_hints = {
            **base_relation_hints,
            **(relation_hints or {}),
        }
        candidates.append(
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=normalized_subject_id,
                    itemized_item_id=normalized_itemized_item_id,
                    sort_kind=sort_kind,
                    canonical_label=normalized_label,
                ),
                subject_id=normalized_subject_id,
                itemized_item_id=normalized_itemized_item_id,
                review_item_id=normalized_review_item_id,
                sort_kind=sort_kind,
                canonical_label=normalized_label,
                summary=collapse_ws(summary) or default_summary,
                source_refs=normalized_source_refs,
                confidence=min(1.0, max(0.0, float(confidence))),
                status="candidate",
                notes="",
                relation_hints=merged_relation_hints,
                created_at_epoch_ms=now_epoch_ms,
                updated_at_epoch_ms=now_epoch_ms,
            )
        )

    for actor in case.actors:
        add_candidate(
            sort_kind="actor",
            label=actor.name,
            relation_hints={
                "normalized_actor_id": actor.id,
                "roles": list(actor.roles),
                "can_decide": actor.can_decide,
            },
        )
    for objective in case.objectives:
        add_candidate(
            sort_kind="objective",
            label=objective.name,
            relation_hints={
                "normalized_objective_id": objective.id,
                "shared": objective.shared,
                "mandatory": objective.mandatory,
            },
        )
    for capability in case.capabilities:
        add_candidate(
            sort_kind="capability",
            label=capability.name,
            relation_hints={
                "normalized_capability_id": capability.id,
                "kind": capability.kind,
                "controlled_by": list(capability.controlled_by),
            },
        )
    for dependency in case.dependencies:
        add_candidate(
            sort_kind="dependency",
            label=dependency.name,
            relation_hints={"normalized_dependency_id": dependency.id},
        )
    for constraint in case.constraints:
        add_candidate(
            sort_kind="constraint",
            label=constraint.name,
            relation_hints={
                "normalized_constraint_id": constraint.id,
                "kind": constraint.kind,
            },
        )
    for boundary in case.boundaries:
        add_candidate(
            sort_kind="boundary",
            label=boundary.name,
            relation_hints={"normalized_boundary_id": boundary.id},
        )
    for state in case.states:
        state_polarity = ""
        if state.is_current is True:
            state_polarity = "current"
        elif state.is_target is True:
            state_polarity = "target"
        add_candidate(
            sort_kind="state",
            label=state.name,
            relation_hints={
                "normalized_state_id": state.id,
                "state_polarity": state_polarity,
                "available_capabilities": list(state.available_capabilities),
            },
        )
    for transition in case.transitions:
        add_candidate(
            sort_kind="transition",
            label=transition.name,
            summary=f"Transition from {transition.source_state_id} to {transition.target_state_id}.",
            relation_hints={
                "normalized_transition_id": transition.id,
                "source_state_id": transition.source_state_id,
                "target_state_id": transition.target_state_id,
                "changes_capabilities": list(transition.changes_capabilities),
            },
        )
    for decision in case.decisions:
        add_candidate(
            sort_kind="decision",
            label=decision.name,
            summary=f"Decision selecting {decision.selects_transition_id}.",
            relation_hints={
                "normalized_decision_id": decision.id,
                "selects_transition_id": decision.selects_transition_id,
                "assignment_count": len(decision.assignments),
                "time_label": decision.time_label,
            },
        )

    deduped_by_id: dict[str, TransformationConstructCandidate] = {}
    for candidate in candidates:
        deduped_by_id[candidate.construct_candidate_id] = candidate
    ordered = tuple(
        sorted(
            deduped_by_id.values(),
            key=lambda candidate: (
                candidate.sort_kind,
                candidate.canonical_label.casefold(),
                candidate.construct_candidate_id,
            ),
        )
    )
    return DstNormalizedConstructProjection(case=case, candidates=ordered)


def coordinated_model_from_dst_projection(
    projection: DstDecisionProjection,
) -> Model:
    fixture = projection.fixture
    actors = frozenset(Actor(entry.seed_name()) for entry in fixture.section_entries("actors"))
    objectives = frozenset(Objective(entry.seed_name()) for entry in fixture.section_entries("objectives"))
    capabilities = frozenset(Capability(entry.seed_name()) for entry in fixture.section_entries("capabilities"))
    dependencies = frozenset(Dependency(entry.seed_name()) for entry in fixture.section_entries("dependencies"))
    constraints = frozenset(Constraint(entry.seed_name()) for entry in fixture.section_entries("constraints"))
    boundaries = frozenset(Boundary(entry.seed_name()) for entry in fixture.section_entries("boundaries"))
    states = frozenset(State(entry.seed_name()) for entry in fixture.section_entries("states"))

    route_edges: dict[str, tuple[str, str]] = {}
    direct_decision_map: dict[str, str] = {}
    for path in fixture.candidate_paths:
        tokens = _route_tokens(path.route_expression)
        if len(tokens) >= 2:
            for index in range(len(tokens) - 1):
                edge_name = f"{tokens[index]} -> {tokens[index + 1]}"
                route_edges.setdefault(edge_name, (tokens[index], tokens[index + 1]))
            if len(tokens) == 2:
                direct_decision_map[path.title] = f"{tokens[0]} -> {tokens[1]}"

    transitions = frozenset(Transition(name) for name in route_edges)
    decisions = frozenset(Decision(path.title) for path in fixture.candidate_paths)
    current_states = frozenset(State(code) for code in projection.current_state_codes)
    target_states = frozenset(State(code) for code in projection.target_state_codes)

    source = {
        Transition(name): State(pair[0])
        for name, pair in route_edges.items()
    }
    target = {
        Transition(name): State(pair[1])
        for name, pair in route_edges.items()
    }
    selects = frozenset(
        (Decision(path_title), Transition(edge_name))
        for path_title, edge_name in direct_decision_map.items()
    )

    return Model(
        actors=actors,
        objectives=objectives,
        capabilities=capabilities,
        dependencies=dependencies,
        constraints=constraints,
        boundaries=boundaries,
        states=states,
        transitions=transitions,
        decisions=decisions,
        current=current_states,
        target_state=target_states,
        selects=selects,
        source=source,
        target=target,
    )


__all__ = [
    "DstDecisionProjection",
    "DstNormalizedConstructProjection",
    "DstNormalizedDecisionProjection",
    "coordinated_model_from_dst_projection",
    "project_dst_fixture_to_decision_frame",
    "project_normalized_case_to_decision_frame",
    "project_normalized_case_to_transformation_construct_candidates",
]
