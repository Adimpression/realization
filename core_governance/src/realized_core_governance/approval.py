"""Approval-record normalization, projection, and matching rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from realized_core_semantics.artifacts import ArtifactContentView

from ._normalization import collapse_ws
from .vocabulary import (
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)


APPROVAL_RECORD_STATUSES = (
    "approved",
    "revoked",
    "expired",
)


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


def normalize_approval_record_status(
    value: Any,
    *,
    default: str = "approved",
) -> str:
    """Normalize an approval record status to the governance vocabulary."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in APPROVAL_RECORD_STATUSES:
        return normalized
    return default


def skill_approval_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a governed approval payload into a stable record."""
    schema = collapse_ws(str(payload.get("schema", "")))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != "bssc_skill.v2" or kind != "approval":
        return {}
    approval = (
        dict(payload.get("approval", {}))
        if isinstance(payload.get("approval", {}), Mapping)
        else {}
    )
    normalized = {
        "intent": collapse_ws(str(approval.get("intent", ""))),
        "approval_class": normalize_skill_approval_class(
            approval.get("approval_class", "automatic")
        ),
        "subject_titles": _string_list(approval.get("subject_titles", [])),
        "subject_kinds": [
            normalize_skill_kind(item)
            for item in _string_list(approval.get("subject_kinds", []))
        ],
        "approved_authorities": normalize_skill_authorities(
            approval.get("approved_authorities", [])
        ),
        "approved_risk_tiers": [
            normalize_skill_risk_tier(item)
            for item in _string_list(approval.get("approved_risk_tiers", []))
        ],
        "issued_by": collapse_ws(str(approval.get("issued_by", ""))),
        "rationale": collapse_ws(str(approval.get("rationale", ""))),
        "status": normalize_approval_record_status(
            approval.get("status", "approved")
        ),
        "valid_from": collapse_ws(str(approval.get("valid_from", ""))),
        "valid_until": collapse_ws(str(approval.get("valid_until", ""))),
    }
    missing_fields = [
        field_name
        for field_name in (
            "intent",
            "approval_class",
            "subject_titles",
            "issued_by",
            "rationale",
        )
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing_fields:
        raise ValueError(
            "Approval artifact v2 requires non-empty fields: "
            + ", ".join(missing_fields)
        )
    return normalized


def approval_answer_summary(approval: Mapping[str, Any]) -> str:
    """Project a normalized approval record into a readable summary."""
    subjects = (
        ", ".join(_string_list(approval.get("subject_titles", [])))
        or "unspecified skill"
    )
    approval_class = normalize_skill_approval_class(
        approval.get("approval_class", "automatic")
    )
    status = normalize_approval_record_status(
        approval.get("status", "approved")
    )
    return f"Approval record {approval_class} {status} for {subjects}."


def artifact_skill_approval(
    artifact: ArtifactContentView,
) -> dict[str, Any]:
    """Read a normalized approval record from artifact content."""
    content = (
        dict(artifact.content)
        if isinstance(artifact.content, Mapping)
        else {}
    )
    return (
        dict(content.get("skill_approval", {}))
        if isinstance(content.get("skill_approval", {}), Mapping)
        else {}
    )


def artifact_is_approval_record(artifact: ArtifactContentView) -> bool:
    """Return whether an artifact contains an approval record."""
    return bool(artifact_skill_approval(artifact))


def _valid_at_or_open(value: str, *, upper_bound: bool = False) -> bool:
    text = collapse_ws(value)
    if not text:
        return True
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
        now = datetime.now(moment.tzinfo)
    except Exception:
        return True
    return now <= moment if upper_bound else now >= moment


def approval_matches_skill(
    approval: Mapping[str, Any],
    *,
    skill_title: str,
    kind: str,
    requested_authorities: list[str],
    risk_tier: str,
    required_approval_class: str,
) -> bool:
    """Return whether one approval satisfies supplied skill requirements."""
    if (
        normalize_approval_record_status(
            approval.get("status", "approved")
        )
        != "approved"
    ):
        return False
    if not _valid_at_or_open(
        str(approval.get("valid_from", "")),
        upper_bound=False,
    ):
        return False
    if not _valid_at_or_open(
        str(approval.get("valid_until", "")),
        upper_bound=True,
    ):
        return False
    subject_titles = set(_string_list(approval.get("subject_titles", [])))
    if collapse_ws(skill_title) not in subject_titles:
        return False
    subject_kinds = [
        normalize_skill_kind(item)
        for item in _string_list(approval.get("subject_kinds", []))
    ]
    if subject_kinds and normalize_skill_kind(kind) not in subject_kinds:
        return False
    approved_authorities = normalize_skill_authorities(
        approval.get("approved_authorities", [])
    )
    if approved_authorities and set(requested_authorities) - set(
        approved_authorities
    ):
        return False
    approved_risk_tiers = [
        normalize_skill_risk_tier(item)
        for item in _string_list(approval.get("approved_risk_tiers", []))
    ]
    if (
        approved_risk_tiers
        and normalize_skill_risk_tier(risk_tier)
        not in approved_risk_tiers
    ):
        return False
    approval_class = normalize_skill_approval_class(
        approval.get("approval_class", "automatic")
    )
    approval_order = {
        "automatic": 0,
        "operator_approved": 1,
        "multi_party_approved": 2,
        "organization_approved": 3,
        "emergency_approved": 4,
        "prohibited": 5,
    }
    return approval_order[approval_class] >= approval_order[
        normalize_skill_approval_class(required_approval_class)
    ]


def matching_approval_artifacts(
    approval_artifacts: list[ArtifactContentView] | None,
    *,
    skill_title: str,
    kind: str,
    requested_authorities: list[str],
    risk_tier: str,
    required_approval_class: str,
) -> list[ArtifactContentView]:
    """Filter supplied artifacts to approvals satisfying a skill requirement."""
    matches: list[ArtifactContentView] = []
    for artifact in approval_artifacts or []:
        approval = artifact_skill_approval(artifact)
        if not approval:
            continue
        if approval_matches_skill(
            approval,
            skill_title=skill_title,
            kind=kind,
            requested_authorities=requested_authorities,
            risk_tier=risk_tier,
            required_approval_class=required_approval_class,
        ):
            matches.append(artifact)
    return matches


__all__ = [
    "APPROVAL_RECORD_STATUSES",
    "approval_answer_summary",
    "approval_matches_skill",
    "artifact_is_approval_record",
    "artifact_skill_approval",
    "matching_approval_artifacts",
    "normalize_approval_record_status",
    "skill_approval_from_payload",
]
