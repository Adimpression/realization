# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

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
    TransitionPath,
    admissible_transition_paths,
    admissible_transition,
    executable_decision,
    risk_capability,
    risk_transition,
    valid_decision,
)
from decision_review_models import DecisionFrame, DecisionReviewItem
from decision_review_policy import DecisionPolicyProfile, default_decision_policy_profile
from learning_context_paths import decision_review_paths
from semantic_text import collapse_ws


DECISION_ANALYSIS_SCHEMA_VERSION = "decision_review_analysis.v1"


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _stable_receipt_id(*parts: Any) -> str:
    rendered = "::".join(collapse_ws(str(part)) for part in parts if collapse_ws(str(part)))
    return f"decrct_{hashlib.sha256(rendered.encode('utf-8')).hexdigest()[:10]}"


def _decision_item_label(item: DecisionReviewItem) -> str:
    return collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.decision_review_item_id


def _decision_policy_allows(rule_id: str, policy: DecisionPolicyProfile) -> bool:
    return collapse_ws(rule_id) in {collapse_ws(item) for item in policy.rule_ids}


def _metadata_decision_item_ids(
    metadata: dict[str, Any],
    *,
    plural_key: str,
    singular_key: str,
) -> tuple[str, ...]:
    raw_value = metadata.get(plural_key)
    values: list[Any] = []
    if isinstance(raw_value, (list, tuple, set)):
        values.extend(raw_value)
    elif raw_value is not None and collapse_ws(str(raw_value)):
        values.append(raw_value)
    singular_value = metadata.get(singular_key)
    if singular_value is not None and collapse_ws(str(singular_value)):
        values.append(singular_value)
    ordered_ids: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = collapse_ws(str(value))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered_ids.append(normalized)
    return tuple(ordered_ids)


def _decision_items_by_ids(
    item_by_id: dict[str, DecisionReviewItem],
    decision_review_item_ids: tuple[str, ...],
) -> tuple[DecisionReviewItem, ...]:
    resolved: list[DecisionReviewItem] = []
    seen: set[str] = set()
    for decision_review_item_id in decision_review_item_ids:
        normalized = collapse_ws(decision_review_item_id)
        if not normalized or normalized in seen:
            continue
        item = item_by_id.get(normalized)
        if item is None:
            continue
        seen.add(normalized)
        resolved.append(item)
    return tuple(resolved)


def _transition_item_ready_for_analysis(item: DecisionReviewItem | None) -> bool:
    if item is None or item.decision_role != "transition_candidate":
        return False
    metadata = dict(item.metadata)
    return bool(
        collapse_ws(str(metadata.get("source_state_decision_review_item_id", "")))
        and collapse_ws(str(metadata.get("target_state_decision_review_item_id", "")))
        and _metadata_decision_item_ids(
            metadata,
            plural_key="changed_capability_decision_review_item_ids",
            singular_key="changed_capability_decision_review_item_id",
        )
    )


def _decision_item_ready_for_analysis(
    item: DecisionReviewItem | None,
    *,
    item_by_id: dict[str, DecisionReviewItem],
) -> bool:
    if item is None or item.decision_role != "decision_candidate":
        return False
    metadata = dict(item.metadata)
    selected_transition_items = _decision_items_by_ids(
        item_by_id,
        _metadata_decision_item_ids(
            metadata,
            plural_key="selected_transition_decision_review_item_ids",
            singular_key="selected_transition_decision_review_item_id",
        ),
    )
    return bool(
        selected_transition_items
        and all(_transition_item_ready_for_analysis(item) for item in selected_transition_items)
        and _metadata_decision_item_ids(
            metadata,
            plural_key="assigned_actor_decision_review_item_ids",
            singular_key="assigned_actor_decision_review_item_id",
        )
    )


def _transition_path_signature(path: TransitionPath) -> str:
    if not path.transitions or len(path.states) < 2:
        return path.start.name
    parts = [path.states[0].name]
    for index, transition in enumerate(path.transitions):
        parts.append(f"--{transition.name}-->")
        parts.append(path.states[index + 1].name)
    return " ".join(parts)


def _metadata_bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = collapse_ws(str(value)).lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def _decision_option_outcomes(
    items: tuple[DecisionReviewItem, ...],
    *,
    admissible_transition_ids: tuple[str, ...],
    valid_decision_ids: tuple[str, ...],
    executable_decision_ids: tuple[str, ...],
    risk_summary: dict[str, Any],
    reachable_pairs_count: int,
    policy: DecisionPolicyProfile,
) -> tuple[dict[str, Any], ...]:
    decision_candidates = tuple(
        item
        for item in items
        if item.included and collapse_ws(item.status) != "rejected" and item.decision_role == "decision_candidate"
    )
    valid_set = {collapse_ws(item) for item in valid_decision_ids}
    executable_set = {collapse_ws(item) for item in executable_decision_ids}
    admissible_transition_count = len(tuple(item for item in admissible_transition_ids if collapse_ws(item)))
    transition_risk_count = int(risk_summary.get("transition_risk_count", 0) or 0)
    capability_risk_count = int(risk_summary.get("capability_risk_count", 0) or 0)
    supporting_evidence_count = int(risk_summary.get("supporting_evidence_count", 0) or 0)
    boundary_count = int(risk_summary.get("boundary_count", 0) or 0)
    transition_count = int(risk_summary.get("transition_candidate_count", 0) or 0)

    outcomes: list[dict[str, Any]] = []
    for item in decision_candidates:
        option_id = _decision_item_label(item)
        score = 0
        reasons: list[str] = []
        if option_id in executable_set:
            score += 100
            reasons.append("executable")
            status = "recommended"
        elif option_id in valid_set:
            score += 60
            reasons.append("valid")
            status = "valid_but_not_executable"
        else:
            status = "blocked"
            reasons.append("not currently valid")
        if _decision_policy_allows("prefer_executable_over_merely_valid", policy) and option_id in executable_set:
            score += 20
        if _decision_policy_allows("penalize_active_high_friction_boundaries", policy) and boundary_count:
            score -= 5 * boundary_count
            reasons.append(f"{boundary_count} active boundaries")
        if _decision_policy_allows("penalize_coordination_heavy_transitions", policy) and transition_count > 1:
            score -= max(0, transition_count - 1) * 3
            reasons.append(f"{transition_count} transition candidates")
        if _decision_policy_allows("prefer_lower_residual_risk", policy):
            risk_penalty = (transition_risk_count * 4) + (capability_risk_count * 2)
            if risk_penalty:
                score -= risk_penalty
                reasons.append(f"risk penalty {risk_penalty}")
        if _decision_policy_allows("prefer_shorter_reachable_paths", policy) and admissible_transition_count:
            score += max(1, min(5, reachable_pairs_count or 0))
            reasons.append("reachable path available")
        if _decision_policy_allows("require_source_support_above_minimum_threshold", policy):
            if supporting_evidence_count > 0:
                score += min(10, supporting_evidence_count * 2)
                reasons.append("source support present")
            else:
                score -= 25
                reasons.append("no supporting evidence")
        outcomes.append(
            {
                "option_id": option_id,
                "status": status,
                "score": score,
                "reasons": tuple(reasons),
            }
        )
    outcomes.sort(
        key=lambda item: (
            {"recommended": 0, "valid_but_not_executable": 1, "blocked": 2}.get(str(item.get("status")), 9),
            -int(item.get("score", 0) or 0),
            str(item.get("option_id", "")),
        )
    )
    return tuple(outcomes)


@dataclass(frozen=True)
class DecisionAnalysisReceipt:
    receipt_id: str
    decision_frame_id: str
    model_snapshot_hash: str
    policy_snapshot_hash: str
    admissible_transition_ids: tuple[str, ...] = ()
    valid_decision_ids: tuple[str, ...] = ()
    executable_decision_ids: tuple[str, ...] = ()
    risk_summary: dict[str, Any] = field(default_factory=dict)
    reachable_pairs_count: int = 0
    blocking_conditions: tuple[str, ...] = ()
    recommendation_status: str = "pending"
    created_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = DECISION_ANALYSIS_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "decision_frame_id": self.decision_frame_id,
            "model_snapshot_hash": self.model_snapshot_hash,
            "policy_snapshot_hash": self.policy_snapshot_hash,
            "admissible_transition_ids": list(self.admissible_transition_ids),
            "valid_decision_ids": list(self.valid_decision_ids),
            "executable_decision_ids": list(self.executable_decision_ids),
            "risk_summary": dict(self.risk_summary),
            "reachable_pairs_count": int(self.reachable_pairs_count),
            "blocking_conditions": list(self.blocking_conditions),
            "recommendation_status": self.recommendation_status,
            "created_at_epoch_ms": int(self.created_at_epoch_ms),
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DecisionAnalysisReceipt":
        return cls(
            receipt_id=collapse_ws(str(payload.get("receipt_id", ""))),
            decision_frame_id=collapse_ws(str(payload.get("decision_frame_id", ""))),
            model_snapshot_hash=collapse_ws(str(payload.get("model_snapshot_hash", ""))),
            policy_snapshot_hash=collapse_ws(str(payload.get("policy_snapshot_hash", ""))),
            admissible_transition_ids=tuple(str(item) for item in payload.get("admissible_transition_ids", []) if collapse_ws(str(item))),
            valid_decision_ids=tuple(str(item) for item in payload.get("valid_decision_ids", []) if collapse_ws(str(item))),
            executable_decision_ids=tuple(str(item) for item in payload.get("executable_decision_ids", []) if collapse_ws(str(item))),
            risk_summary=dict(payload.get("risk_summary", {})),
            reachable_pairs_count=max(0, int(payload.get("reachable_pairs_count", 0) or 0)),
            blocking_conditions=tuple(str(item) for item in payload.get("blocking_conditions", []) if collapse_ws(str(item))),
            recommendation_status=collapse_ws(str(payload.get("recommendation_status", ""))) or "pending",
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
            schema_version=collapse_ws(str(payload.get("schema_version", DECISION_ANALYSIS_SCHEMA_VERSION))) or DECISION_ANALYSIS_SCHEMA_VERSION,
        )


def decision_analysis_receipts_root(root_path: str | Any, subject_id: str) -> Any:
    return decision_review_paths(root_path, subject_id)["root"] / "receipts"


def persist_decision_analysis_receipt(root_path: str | Any, subject_id: str, receipt: DecisionAnalysisReceipt) -> Any:
    receipts_root = decision_analysis_receipts_root(root_path, subject_id)
    receipts_root.mkdir(parents=True, exist_ok=True)
    target = receipts_root / f"{receipt.receipt_id}.json"
    target.write_text(json.dumps(receipt.to_dict(), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def list_decision_analysis_receipts(root_path: str | Any, subject_id: str) -> tuple[DecisionAnalysisReceipt, ...]:
    receipts_root = decision_analysis_receipts_root(root_path, subject_id)
    if not receipts_root.exists():
        return ()
    receipts: list[DecisionAnalysisReceipt] = []
    for path in sorted(receipts_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        receipt = DecisionAnalysisReceipt.from_dict(payload)
        if receipt.receipt_id:
            receipts.append(receipt)
    return tuple(sorted(receipts, key=lambda item: (int(item.created_at_epoch_ms or 0), item.receipt_id)))


def decision_review_model(
    frame: DecisionFrame,
    items: tuple[DecisionReviewItem, ...],
) -> Model:
    active_items = tuple(
        item
        for item in items
        if item.included and collapse_ws(item.status) != "rejected"
    )
    actors = frozenset(Actor(_decision_item_label(item)) for item in active_items if item.decision_role == "actor")
    objectives = frozenset(Objective(_decision_item_label(item)) for item in active_items if item.decision_role == "objective")
    capabilities = frozenset(Capability(_decision_item_label(item)) for item in active_items if item.decision_role == "capability")
    dependencies = frozenset(Dependency(_decision_item_label(item)) for item in active_items if item.decision_role == "dependency")
    constraints = frozenset(Constraint(_decision_item_label(item)) for item in active_items if item.decision_role == "constraint")
    boundaries = frozenset(Boundary(_decision_item_label(item)) for item in active_items if item.decision_role == "boundary")
    states = frozenset(
        State(_decision_item_label(item))
        for item in active_items
        if item.decision_role in {"current_state", "target_state"}
    )
    transitions = frozenset(
        Transition(_decision_item_label(item))
        for item in active_items
        if item.decision_role == "transition_candidate"
    )
    decisions = frozenset(
        Decision(_decision_item_label(item))
        for item in active_items
        if item.decision_role == "decision_candidate"
    )
    current_item_ids = {collapse_ws(item_id) for item_id in frame.current_state_ids if collapse_ws(item_id)}
    target_item_ids = {collapse_ws(item_id) for item_id in frame.target_state_ids if collapse_ws(item_id)}
    item_by_id = {
        collapse_ws(item.decision_review_item_id): item
        for item in active_items
        if collapse_ws(item.decision_review_item_id)
    }
    current_states = frozenset(
        State(_decision_item_label(item))
        for item in active_items
        if item.decision_role == "current_state"
        and collapse_ws(item.decision_review_item_id) in current_item_ids
    )
    target_states = frozenset(
        State(_decision_item_label(item))
        for item in active_items
        if item.decision_role == "target_state"
        and collapse_ws(item.decision_review_item_id) in target_item_ids
    )
    transition_source: dict[Transition, State] = {}
    transition_target: dict[Transition, State] = {}
    changed_capabilities: set[tuple[Transition, Capability]] = set()
    required_dependencies: set[tuple[Capability, Dependency]] = set()
    crossed_boundaries: set[tuple[Capability, Boundary]] = set()
    selected_transitions: set[tuple[Decision, Transition]] = set()
    assigned_actors: set[tuple[Decision, Actor, Capability]] = set()
    can_decide_pairs: set[tuple[Actor, Decision]] = set()
    for item in active_items:
        if item.decision_role == "capability":
            capability = Capability(_decision_item_label(item))
            required_dependency_items = _decision_items_by_ids(
                item_by_id,
                _metadata_decision_item_ids(
                    dict(item.metadata),
                    plural_key="required_dependency_decision_review_item_ids",
                    singular_key="required_dependency_decision_review_item_id",
                ),
            )
            crossed_boundary_items = _decision_items_by_ids(
                item_by_id,
                _metadata_decision_item_ids(
                    dict(item.metadata),
                    plural_key="crossed_boundary_decision_review_item_ids",
                    singular_key="crossed_boundary_decision_review_item_id",
                ),
            )
            for dependency_item in required_dependency_items:
                if dependency_item.decision_role != "dependency":
                    continue
                required_dependencies.add((capability, Dependency(_decision_item_label(dependency_item))))
            for boundary_item in crossed_boundary_items:
                if boundary_item.decision_role != "boundary":
                    continue
                crossed_boundaries.add((capability, Boundary(_decision_item_label(boundary_item))))
        elif item.decision_role == "transition_candidate":
            transition = Transition(_decision_item_label(item))
            source_item_id = collapse_ws(str(item.metadata.get("source_state_decision_review_item_id", "")))
            target_item_id = collapse_ws(str(item.metadata.get("target_state_decision_review_item_id", "")))
            changed_capability_items = _decision_items_by_ids(
                item_by_id,
                _metadata_decision_item_ids(
                    dict(item.metadata),
                    plural_key="changed_capability_decision_review_item_ids",
                    singular_key="changed_capability_decision_review_item_id",
                ),
            )
            source_item = item_by_id.get(source_item_id)
            target_item = item_by_id.get(target_item_id)
            if source_item is not None and source_item.decision_role in {"current_state", "target_state"}:
                transition_source[transition] = State(_decision_item_label(source_item))
            if target_item is not None and target_item.decision_role in {"current_state", "target_state"}:
                transition_target[transition] = State(_decision_item_label(target_item))
            for changed_capability_item in changed_capability_items:
                if changed_capability_item.decision_role != "capability":
                    continue
                changed_capabilities.add(
                    (
                        transition,
                        Capability(_decision_item_label(changed_capability_item)),
                    )
                )
        elif item.decision_role == "decision_candidate":
            decision = Decision(_decision_item_label(item))
            selected_transition_items = _decision_items_by_ids(
                item_by_id,
                _metadata_decision_item_ids(
                    dict(item.metadata),
                    plural_key="selected_transition_decision_review_item_ids",
                    singular_key="selected_transition_decision_review_item_id",
                ),
            )
            assigned_actor_items = _decision_items_by_ids(
                item_by_id,
                _metadata_decision_item_ids(
                    dict(item.metadata),
                    plural_key="assigned_actor_decision_review_item_ids",
                    singular_key="assigned_actor_decision_review_item_id",
                ),
            )
            for selected_transition_item in selected_transition_items:
                if selected_transition_item.decision_role != "transition_candidate":
                    continue
                transition = Transition(_decision_item_label(selected_transition_item))
                selected_transitions.add((decision, transition))
                changed_capability_items = _decision_items_by_ids(
                    item_by_id,
                    _metadata_decision_item_ids(
                        dict(selected_transition_item.metadata),
                        plural_key="changed_capability_decision_review_item_ids",
                        singular_key="changed_capability_decision_review_item_id",
                    ),
                )
                for assigned_actor_item in assigned_actor_items:
                    if assigned_actor_item.decision_role != "actor":
                        continue
                    actor = Actor(_decision_item_label(assigned_actor_item))
                    can_decide_pairs.add((actor, decision))
                    for changed_capability_item in changed_capability_items:
                        if changed_capability_item.decision_role != "capability":
                            continue
                        capability = Capability(_decision_item_label(changed_capability_item))
                        assigned_actors.add((decision, actor, capability))
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
        can_decide=frozenset(can_decide_pairs),
        requires=frozenset(required_dependencies),
        crosses=frozenset(crossed_boundaries),
        changes=frozenset(changed_capabilities),
        selects=frozenset(selected_transitions),
        assigns=frozenset(assigned_actors),
        source=transition_source,
        target=transition_target,
    )


def analyze_decision_frame(
    frame: DecisionFrame,
    items: tuple[DecisionReviewItem, ...],
    *,
    policy_profile: DecisionPolicyProfile | None = None,
    build_epoch_ms: int = 0,
) -> DecisionAnalysisReceipt:
    policy = policy_profile or default_decision_policy_profile(
        decision_frame_id=frame.decision_frame_id,
        build_epoch_ms=build_epoch_ms,
    )
    model = decision_review_model(frame, items)
    active_items = tuple(
        item
        for item in items
        if item.included and collapse_ws(item.status) != "rejected"
    )
    active_item_by_id = {
        collapse_ws(item.decision_review_item_id): item
        for item in active_items
        if collapse_ws(item.decision_review_item_id)
    }
    decision_item_by_label = {
        _decision_item_label(item): item
        for item in active_items
        if item.decision_role == "decision_candidate"
    }
    blocking_conditions: list[str] = []
    if not collapse_ws(frame.question):
        blocking_conditions.append("Decision question is not set.")
    if not frame.current_state_ids:
        blocking_conditions.append("Current state is not defined.")
    if not frame.target_state_ids:
        blocking_conditions.append("Target state is not defined.")
    if not any(item.decision_role == "objective" and item.included for item in items):
        blocking_conditions.append("No primary objective is assigned.")
    if not any(item.decision_role == "decision_candidate" and item.included for item in items):
        blocking_conditions.append("No decision candidate is assigned.")
    for item in items:
        if not item.included or collapse_ws(item.status) == "rejected":
            continue
        label = _decision_item_label(item)
        metadata = dict(item.metadata)
        if item.decision_role == "transition_candidate":
            if not collapse_ws(str(metadata.get("source_state_decision_review_item_id", ""))):
                blocking_conditions.append(f"Transition candidate '{label}' is missing its source state.")
            if not collapse_ws(str(metadata.get("target_state_decision_review_item_id", ""))):
                blocking_conditions.append(f"Transition candidate '{label}' is missing its target state.")
            if not _metadata_decision_item_ids(
                metadata,
                plural_key="changed_capability_decision_review_item_ids",
                singular_key="changed_capability_decision_review_item_id",
            ):
                blocking_conditions.append(f"Transition candidate '{label}' is missing its changed capability.")
        elif item.decision_role == "decision_candidate":
            if not _metadata_decision_item_ids(
                metadata,
                plural_key="selected_transition_decision_review_item_ids",
                singular_key="selected_transition_decision_review_item_id",
            ):
                blocking_conditions.append(f"Decision candidate '{label}' is missing its selected transition.")
            if not _metadata_decision_item_ids(
                metadata,
                plural_key="assigned_actor_decision_review_item_ids",
                singular_key="assigned_actor_decision_review_item_id",
            ):
                blocking_conditions.append(f"Decision candidate '{label}' is missing its assigned actor.")

    admissible_transition_ids = tuple(
        transition.name
        for transition in sorted(model.transitions, key=lambda item: item.name)
        for state in sorted(model.current, key=lambda item: item.name)
        if admissible_transition(model, transition, state)
    )
    computed_admissible_transition_set = {
        collapse_ws(item) for item in admissible_transition_ids if collapse_ws(item)
    }
    ordered_transition_items = tuple(
        item for item in active_items if item.decision_role == "transition_candidate"
    )
    has_explicit_transition_status = any(
        _metadata_bool_or_none(item.metadata.get("dst_admissible_in_evaluation_state")) is not None
        for item in ordered_transition_items
    )
    if has_explicit_transition_status:
        admissible_transition_ids = tuple(
            _decision_item_label(item)
            for item in ordered_transition_items
            if (
                _metadata_bool_or_none(item.metadata.get("dst_admissible_in_evaluation_state")) is True
                or (
                    _metadata_bool_or_none(item.metadata.get("dst_admissible_in_evaluation_state")) is None
                    and _decision_item_label(item) in computed_admissible_transition_set
                )
            )
        )

    computed_valid_decision_set = {
        decision.name
        for decision in sorted(model.decisions, key=lambda item: item.name)
        for state in sorted(model.current, key=lambda item: item.name)
        if valid_decision(model, decision, state)
        and _decision_item_ready_for_analysis(
            decision_item_by_label.get(decision.name),
            item_by_id=active_item_by_id,
        )
    }
    computed_executable_decision_set = {
        decision.name
        for decision in sorted(model.decisions, key=lambda item: item.name)
        for state in sorted(model.current, key=lambda item: item.name)
        if executable_decision(model, decision, state)
        and _decision_item_ready_for_analysis(
            decision_item_by_label.get(decision.name),
            item_by_id=active_item_by_id,
        )
    }
    ordered_decision_items = tuple(
        item for item in active_items if item.decision_role == "decision_candidate"
    )
    has_explicit_decision_status = any(
        _metadata_bool_or_none(item.metadata.get("dst_valid_in_evaluation_state")) is not None
        or _metadata_bool_or_none(item.metadata.get("dst_executable_in_evaluation_state")) is not None
        for item in ordered_decision_items
    )
    if has_explicit_decision_status:
        valid_decision_ids = tuple(
            _decision_item_label(item)
            for item in ordered_decision_items
            if (
                _metadata_bool_or_none(item.metadata.get("dst_valid_in_evaluation_state")) is True
                or (
                    _metadata_bool_or_none(item.metadata.get("dst_valid_in_evaluation_state")) is None
                    and _decision_item_label(item) in computed_valid_decision_set
                )
            )
            and _decision_item_ready_for_analysis(item, item_by_id=active_item_by_id)
        )
        executable_decision_ids = tuple(
            _decision_item_label(item)
            for item in ordered_decision_items
            if (
                _metadata_bool_or_none(item.metadata.get("dst_executable_in_evaluation_state")) is True
                or (
                    _metadata_bool_or_none(item.metadata.get("dst_executable_in_evaluation_state")) is None
                    and _decision_item_label(item) in computed_executable_decision_set
                )
            )
            and _decision_item_ready_for_analysis(item, item_by_id=active_item_by_id)
        )
    else:
        valid_decision_ids = tuple(
            decision.name
            for decision in sorted(model.decisions, key=lambda item: item.name)
            if decision.name in computed_valid_decision_set
        )
        executable_decision_ids = tuple(
            decision.name
            for decision in sorted(model.decisions, key=lambda item: item.name)
            if decision.name in computed_executable_decision_set
        )
    risk_summary = {
        "capability_risk_count": sum(
            1
            for capability in model.capabilities
            for state in model.current
            if risk_capability(model, capability, state)
        ),
        "transition_risk_count": sum(
            1
            for transition in model.transitions
            for state in model.current
            if risk_transition(model, transition, state)
        ),
        "included_item_count": sum(1 for item in items if item.included and collapse_ws(item.status) != "rejected"),
        "supporting_evidence_count": sum(
            1
            for item in items
            if item.included and collapse_ws(item.status) != "rejected" and item.decision_role == "supporting_evidence"
        ),
        "boundary_count": sum(
            1
            for item in items
            if item.included and collapse_ws(item.status) != "rejected" and item.decision_role == "boundary"
        ),
        "transition_candidate_count": sum(
            1
            for item in items
            if item.included and collapse_ws(item.status) != "rejected" and item.decision_role == "transition_candidate"
        ),
        "dependency_count": sum(
            1
            for item in items
            if item.included and collapse_ws(item.status) != "rejected" and item.decision_role == "dependency"
        ),
    }
    candidate_paths = admissible_transition_paths(
        model,
        start_states=tuple(sorted(model.current, key=lambda item: item.name)),
        target_states=tuple(sorted(model.target_state, key=lambda item: item.name)),
        max_depth=max(1, min(6, len(model.transitions) or 1)),
    )
    candidate_path_signatures = tuple(_transition_path_signature(path) for path in candidate_paths)
    risk_summary["candidate_path_count"] = len(candidate_paths)
    option_outcomes = _decision_option_outcomes(
        items,
        admissible_transition_ids=admissible_transition_ids,
        valid_decision_ids=valid_decision_ids,
        executable_decision_ids=executable_decision_ids,
        risk_summary=risk_summary,
        reachable_pairs_count=len(getattr(model, "reachable", ()) or ()),
        policy=policy,
    )
    policy_blocking_conditions: list[str] = []
    if _decision_policy_allows("reject_unresolved_critical_dependencies", policy):
        dependency_count = int(risk_summary.get("dependency_count", 0) or 0)
        if dependency_count and not executable_decision_ids:
            policy_blocking_conditions.append("Dependency candidates remain unresolved against executable options.")
    if _decision_policy_allows("require_source_support_above_minimum_threshold", policy):
        if not int(risk_summary.get("supporting_evidence_count", 0) or 0):
            policy_blocking_conditions.append("Policy requires at least one supporting evidence item.")
    recommended_option_ids = tuple(
        str(item.get("option_id", ""))
        for item in option_outcomes
        if str(item.get("status", "")) == "recommended"
    )
    recommendation_status = "decision_aid_ready"
    if blocking_conditions or policy_blocking_conditions:
        recommendation_status = "blocked"
    elif recommended_option_ids:
        recommendation_status = "recommendable"
    elif valid_decision_ids:
        recommendation_status = "valid_but_not_executable"
    receipt = DecisionAnalysisReceipt(
        receipt_id=_stable_receipt_id(frame.decision_frame_id, frame.content_hash(), policy.content_hash()),
        decision_frame_id=frame.decision_frame_id,
        model_snapshot_hash=_stable_json_hash(
            {
                "frame": frame.to_dict(),
                "items": [item.to_dict() for item in items],
            }
        ),
        policy_snapshot_hash=policy.content_hash(),
        admissible_transition_ids=admissible_transition_ids,
        valid_decision_ids=valid_decision_ids,
        executable_decision_ids=executable_decision_ids,
        risk_summary=risk_summary,
        reachable_pairs_count=len(getattr(model, "reachable", ()) or ()),
        blocking_conditions=tuple((*blocking_conditions, *policy_blocking_conditions)),
        recommendation_status=recommendation_status,
        created_at_epoch_ms=max(0, int(build_epoch_ms or 0)),
        metadata={
            "question": frame.question,
            "decision_mode": frame.decision_mode,
            "policy_profile_id": policy.policy_profile_id,
            "policy_profile_kind": getattr(policy, "profile_kind", "conservative"),
            "policy_rule_count": len(policy.rule_ids),
            "policy_rule_ids": tuple(policy.rule_ids),
            "recommended_option_ids": recommended_option_ids,
            "candidate_path_count": len(candidate_paths),
            "candidate_path_signatures": candidate_path_signatures,
            "option_outcomes": option_outcomes,
        },
    )
    return receipt
