"""Policy and approval evaluation for governed skill admission."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from realized_core_semantics.artifacts import TitledArtifactContentView
from realized_skill_semantics.execution import normalize_executor_framework_name

from ._normalization import collapse_ws
from .approval import matching_approval_artifacts
from .records import artifact_skill_policy
from .vocabulary import (
    SKILL_APPROVAL_CLASSES,
    SKILL_RISK_TIERS,
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)


_RISK_INDEX = {tier: index for index, tier in enumerate(SKILL_RISK_TIERS)}
_APPROVAL_INDEX = {
    level: index for index, level in enumerate(SKILL_APPROVAL_CLASSES)
}


def _string_list(value: Any) -> list[str]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return [
            collapse_ws(str(item))
            for item in value
            if collapse_ws(str(item))
        ]
    return [collapse_ws(str(value))] if collapse_ws(str(value)) else []


def _decision(
    *,
    status: str,
    admitted: bool,
    rationale: str,
    policy_titles: list[str],
    approval_titles: list[str],
    required_approval_class: str,
    evaluated_at: Callable[[], str],
) -> dict[str, Any]:
    return {
        "status": status,
        "admitted": admitted,
        "rationale": rationale,
        "policy_titles": policy_titles,
        "approval_titles": approval_titles,
        "required_approval_class": required_approval_class,
        "evaluated_at": evaluated_at(),
    }


def evaluate_skill_policy_admission(
    declaration: Mapping[str, Any],
    *,
    skill_title: str = "",
    kind: str,
    executor_framework: str = "",
    policy_artifacts: list[TitledArtifactContentView] | None = None,
    approval_artifacts: list[TitledArtifactContentView] | None = None,
    evaluated_at: Callable[[], str],
) -> dict[str, Any]:
    """Evaluate supplied policy and approval records for one declaration."""
    normalized_kind = normalize_skill_kind(kind)
    normalized_executor = normalize_executor_framework_name(executor_framework)
    policies = [
        artifact
        for artifact in (policy_artifacts or [])
        if artifact_skill_policy(artifact)
    ]
    if not policies:
        return _decision(
            status="held",
            admitted=False,
            rationale=(
                "No policy artifact is currently installed for governed v2 skills."
            ),
            policy_titles=[],
            approval_titles=[],
            required_approval_class="automatic",
            evaluated_at=evaluated_at,
        )

    requested_authorities = normalize_skill_authorities(
        declaration.get("authorities_requested", [])
    )
    risk_tier = normalize_skill_risk_tier(
        declaration.get("risk_tier", "tier1_bounded_transform")
    )
    approval_requirements = [
        normalize_skill_approval_class(item)
        for item in _string_list(declaration.get("approval_requirements", []))
    ] or ["automatic"]

    if (
        normalized_kind == "ability"
        and normalized_executor
        and "execute" not in requested_authorities
    ):
        return _decision(
            status="held",
            admitted=False,
            rationale=(
                f"Executable {normalized_executor} skills must declare execute authority "
                "before they can be admitted."
            ),
            policy_titles=[],
            approval_titles=[],
            required_approval_class="automatic",
            evaluated_at=evaluated_at,
        )

    blocking_reasons: list[str] = []
    required_approval_class = "automatic"
    policy_titles: list[str] = []
    for artifact in policies:
        policy = artifact_skill_policy(artifact)
        policy_titles.append(artifact.title)
        if normalized_kind not in policy.get("target_kinds", []):
            blocking_reasons.append(
                f"policy {artifact.title!r} does not admit kind {normalized_kind!r}"
            )
            continue
        if _RISK_INDEX[risk_tier] > _RISK_INDEX[
            normalize_skill_risk_tier(policy.get("max_risk_tier", risk_tier))
        ]:
            blocking_reasons.append(
                f"policy {artifact.title!r} limits risk to "
                f"{policy.get('max_risk_tier')}, but declaration requests {risk_tier}"
            )
        allowed_authorities = normalize_skill_authorities(
            policy.get("allowed_authorities", [])
        )
        denied_authorities = normalize_skill_authorities(
            policy.get("denied_authorities", [])
        )
        disallowed_requested = sorted(
            set(requested_authorities) & set(denied_authorities)
        )
        if disallowed_requested:
            blocking_reasons.append(
                f"policy {artifact.title!r} denies authorities: "
                + ", ".join(disallowed_requested)
            )
        missing_allowed = sorted(
            set(requested_authorities) - set(allowed_authorities)
        )
        if missing_allowed:
            blocking_reasons.append(
                f"policy {artifact.title!r} does not allow authorities: "
                + ", ".join(missing_allowed)
            )
        allowed_executors = [
            normalize_executor_framework_name(item)
            for item in _string_list(policy.get("allowed_executors", []))
        ]
        if (
            normalized_kind == "ability"
            and allowed_executors
            and normalized_executor not in allowed_executors
        ):
            blocking_reasons.append(
                f"policy {artifact.title!r} does not allow executor "
                f"{normalized_executor or 'unknown'}"
            )
        allowed_data_classes = _string_list(
            policy.get("allowed_data_classes", [])
        )
        if allowed_data_classes:
            undeclared_data = sorted(
                set(_string_list(declaration.get("data_classes_touched", [])))
                - set(allowed_data_classes)
            )
            if undeclared_data:
                blocking_reasons.append(
                    f"policy {artifact.title!r} does not allow data classes: "
                    + ", ".join(undeclared_data)
                )
        denied_side_effects = set(
            _string_list(policy.get("denied_side_effects", []))
        )
        forbidden_side_effects = sorted(
            set(_string_list(declaration.get("side_effects", [])))
            & denied_side_effects
        )
        if forbidden_side_effects:
            blocking_reasons.append(
                f"policy {artifact.title!r} denies side effects: "
                + ", ".join(forbidden_side_effects)
            )
        policy_required_approval = normalize_skill_approval_class(
            dict(policy.get("required_approval_for_risk_tiers", {})).get(
                risk_tier,
                "automatic",
            )
        )
        if (
            _APPROVAL_INDEX[policy_required_approval]
            > _APPROVAL_INDEX[required_approval_class]
        ):
            required_approval_class = policy_required_approval

    if blocking_reasons:
        return _decision(
            status="rejected",
            admitted=False,
            rationale="; ".join(blocking_reasons),
            policy_titles=policy_titles,
            approval_titles=[],
            required_approval_class=required_approval_class,
            evaluated_at=evaluated_at,
        )

    strongest_declared_approval = max(
        approval_requirements,
        key=lambda item: _APPROVAL_INDEX[normalize_skill_approval_class(item)],
    )
    if (
        _APPROVAL_INDEX[required_approval_class]
        > _APPROVAL_INDEX[strongest_declared_approval]
    ):
        return _decision(
            status="held",
            admitted=False,
            rationale=(
                f"Policy requires approval class {required_approval_class}, "
                f"but declaration only provides {strongest_declared_approval}."
            ),
            policy_titles=policy_titles,
            approval_titles=[],
            required_approval_class=required_approval_class,
            evaluated_at=evaluated_at,
        )

    if required_approval_class != "automatic":
        matching_approvals = matching_approval_artifacts(
            approval_artifacts,
            skill_title=skill_title,
            kind=normalized_kind,
            requested_authorities=requested_authorities,
            risk_tier=risk_tier,
            required_approval_class=required_approval_class,
        )
        approval_titles = [artifact.title for artifact in matching_approvals]
        if matching_approvals:
            return _decision(
                status="admitted",
                admitted=True,
                rationale=(
                    "Declaration satisfied installed policy constraints and "
                    f"matched approval class {required_approval_class}."
                ),
                policy_titles=policy_titles,
                approval_titles=approval_titles,
                required_approval_class=required_approval_class,
                evaluated_at=evaluated_at,
            )
        return _decision(
            status="held",
            admitted=False,
            rationale=(
                "Policy requires explicit approval class "
                f"{required_approval_class} before admission."
            ),
            policy_titles=policy_titles,
            approval_titles=[],
            required_approval_class=required_approval_class,
            evaluated_at=evaluated_at,
        )

    return _decision(
        status="admitted",
        admitted=True,
        rationale=(
            "Declaration satisfied installed policy constraints and required "
            "no additional approval."
        ),
        policy_titles=policy_titles,
        approval_titles=[],
        required_approval_class=required_approval_class,
        evaluated_at=evaluated_at,
    )


__all__ = ["evaluate_skill_policy_admission"]
