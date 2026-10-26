"""Revocation and incident normalization, matching, and safety overlays."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from realized_core_semantics.artifacts import (
    ArtifactContentView,
    TitledArtifactContentView,
)

from ._normalization import collapse_ws
from .lifecycle import (
    normalize_skill_activation_status,
    normalize_skill_installation_status,
    normalize_skill_quarantine_status,
    normalize_skill_trust_status,
)
from .vocabulary import normalize_skill_kind


REVOCATION_RECORD_STATUSES = ("active", "rescinded")
INCIDENT_RECORD_STATUSES = ("open", "monitoring", "resolved")
INCIDENT_SEVERITIES = ("low", "medium", "high", "critical")
INCIDENT_ENFORCEMENT_ACTIONS = (
    "none",
    "restrict",
    "suspend",
    "quarantine",
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


_normalize_skill_kind = normalize_skill_kind


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


def normalize_revocation_record_status(
    value: Any,
    *,
    default: str = "active",
) -> str:
    """Normalize a revocation status to the governance vocabulary."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in REVOCATION_RECORD_STATUSES:
        return normalized
    return default


def normalize_incident_record_status(
    value: Any,
    *,
    default: str = "open",
) -> str:
    """Normalize an incident status to the governance vocabulary."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in INCIDENT_RECORD_STATUSES:
        return normalized
    return default


def normalize_incident_severity(
    value: Any,
    *,
    default: str = "medium",
) -> str:
    """Normalize an incident severity to the governance vocabulary."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in INCIDENT_SEVERITIES:
        return normalized
    return default


def normalize_incident_enforcement_action(
    value: Any,
    *,
    default: str = "none",
) -> str:
    """Normalize an incident action to the governance vocabulary."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in INCIDENT_ENFORCEMENT_ACTIONS:
        return normalized
    return default


def skill_revocation_from_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize a governed revocation payload into a stable record."""
    schema = collapse_ws(str(payload.get("schema", "")))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != "bssc_skill.v2" or kind != "revocation":
        return {}
    revocation = (
        dict(payload.get("revocation", {}))
        if isinstance(payload.get("revocation", {}), Mapping)
        else {}
    )
    normalized = {
        "intent": collapse_ws(str(revocation.get("intent", ""))),
        "subject_titles": _string_list(revocation.get("subject_titles", [])),
        "subject_kinds": [
            normalize_skill_kind(item)
            for item in _string_list(revocation.get("subject_kinds", []))
        ],
        "trust_status": normalize_skill_trust_status(
            revocation.get("trust_status", "revoked"),
            default="revoked",
        ),
        "quarantine_status": normalize_skill_quarantine_status(
            revocation.get("quarantine_status", "clear")
        ),
        "activation_status": normalize_skill_activation_status(
            revocation.get("activation_status", "inactive"),
            default="inactive",
        ),
        "installation_status": normalize_skill_installation_status(
            revocation.get("installation_status", "blocked"),
            default="blocked",
        ),
        "status": normalize_revocation_record_status(
            revocation.get("status", "active")
        ),
        "issued_by": collapse_ws(str(revocation.get("issued_by", ""))),
        "rationale": collapse_ws(str(revocation.get("rationale", ""))),
        "valid_from": collapse_ws(str(revocation.get("valid_from", ""))),
        "valid_until": collapse_ws(str(revocation.get("valid_until", ""))),
    }
    missing = [
        field_name
        for field_name in ("intent", "subject_titles", "issued_by", "rationale")
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing:
        raise ValueError(
            "Revocation artifact v2 requires non-empty fields: "
            + ", ".join(missing)
        )
    return normalized


def skill_incident_from_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize a governed incident payload into a stable record."""
    schema = collapse_ws(str(payload.get("schema", "")))
    kind = normalize_skill_kind(payload.get("kind", "knowledge"))
    if schema != "bssc_skill.v2" or kind != "incident":
        return {}
    incident = (
        dict(payload.get("incident", {}))
        if isinstance(payload.get("incident", {}), Mapping)
        else {}
    )
    normalized = {
        "intent": collapse_ws(str(incident.get("intent", ""))),
        "subject_titles": _string_list(incident.get("subject_titles", [])),
        "subject_kinds": [
            normalize_skill_kind(item)
            for item in _string_list(incident.get("subject_kinds", []))
        ],
        "severity": normalize_incident_severity(
            incident.get("severity", "medium")
        ),
        "enforcement_action": normalize_incident_enforcement_action(
            incident.get("enforcement_action", "none")
        ),
        "status": normalize_incident_record_status(
            incident.get("status", "open")
        ),
        "issued_by": collapse_ws(str(incident.get("issued_by", ""))),
        "rationale": collapse_ws(str(incident.get("rationale", ""))),
        "valid_from": collapse_ws(str(incident.get("valid_from", ""))),
        "valid_until": collapse_ws(str(incident.get("valid_until", ""))),
    }
    missing = [
        field_name
        for field_name in (
            "intent",
            "subject_titles",
            "severity",
            "issued_by",
            "rationale",
        )
        if normalized.get(field_name) in (None, "", [], {})
    ]
    if missing:
        raise ValueError(
            "Incident artifact v2 requires non-empty fields: "
            + ", ".join(missing)
        )
    return normalized


def revocation_answer_summary(revocation: Mapping[str, Any]) -> str:
    """Project a revocation record into a readable summary."""
    subjects = (
        ", ".join(_string_list(revocation.get("subject_titles", [])))
        or "unspecified skill"
    )
    status = normalize_revocation_record_status(
        revocation.get("status", "active")
    )
    trust = normalize_skill_trust_status(
        revocation.get("trust_status", "revoked"),
        default="revoked",
    )
    return f"Revocation record {status} for {subjects} with trust status {trust}."


def incident_answer_summary(incident: Mapping[str, Any]) -> str:
    """Project an incident record into a readable summary."""
    subjects = (
        ", ".join(_string_list(incident.get("subject_titles", [])))
        or "unspecified skill"
    )
    status = normalize_incident_record_status(incident.get("status", "open"))
    severity = normalize_incident_severity(incident.get("severity", "medium"))
    action = normalize_incident_enforcement_action(
        incident.get("enforcement_action", "none")
    )
    return (
        f"Incident record {status} for {subjects} at severity {severity} "
        f"with action {action}."
    )


def artifact_skill_revocation(
    artifact: ArtifactContentView,
) -> dict[str, Any]:
    """Read a normalized revocation record from artifact content."""
    content = (
        dict(artifact.content)
        if isinstance(artifact.content, Mapping)
        else {}
    )
    return (
        dict(content.get("skill_revocation", {}))
        if isinstance(content.get("skill_revocation", {}), Mapping)
        else {}
    )


def artifact_skill_incident(
    artifact: ArtifactContentView,
) -> dict[str, Any]:
    """Read a normalized incident record from artifact content."""
    content = (
        dict(artifact.content)
        if isinstance(artifact.content, Mapping)
        else {}
    )
    return (
        dict(content.get("skill_incident", {}))
        if isinstance(content.get("skill_incident", {}), Mapping)
        else {}
    )


def artifact_is_revocation_record(artifact: ArtifactContentView) -> bool:
    """Return whether an artifact contains a revocation record."""
    return bool(artifact_skill_revocation(artifact))


def artifact_is_incident_record(artifact: ArtifactContentView) -> bool:
    """Return whether an artifact contains an incident record."""
    return bool(artifact_skill_incident(artifact))


def revocation_matches_skill(
    revocation: Mapping[str, Any],
    *,
    skill_title: str,
    kind: str,
) -> bool:
    """Return whether one active revocation applies to a supplied skill."""
    if (
        normalize_revocation_record_status(revocation.get("status", "active"))
        != "active"
    ):
        return False
    if not _valid_at_or_open(
        str(revocation.get("valid_from", "")),
        upper_bound=False,
    ):
        return False
    if not _valid_at_or_open(
        str(revocation.get("valid_until", "")),
        upper_bound=True,
    ):
        return False
    if collapse_ws(skill_title) not in set(
        _string_list(revocation.get("subject_titles", []))
    ):
        return False
    subject_kinds = [
        normalize_skill_kind(item)
        for item in _string_list(revocation.get("subject_kinds", []))
    ]
    if subject_kinds and normalize_skill_kind(kind) not in subject_kinds:
        return False
    return True


def incident_matches_skill(
    incident: Mapping[str, Any],
    *,
    skill_title: str,
    kind: str,
) -> bool:
    """Return whether one unresolved incident applies to a supplied skill."""
    if normalize_incident_record_status(incident.get("status", "open")) == "resolved":
        return False
    if not _valid_at_or_open(
        str(incident.get("valid_from", "")),
        upper_bound=False,
    ):
        return False
    if not _valid_at_or_open(
        str(incident.get("valid_until", "")),
        upper_bound=True,
    ):
        return False
    if collapse_ws(skill_title) not in set(
        _string_list(incident.get("subject_titles", []))
    ):
        return False
    subject_kinds = [
        normalize_skill_kind(item)
        for item in _string_list(incident.get("subject_kinds", []))
    ]
    if subject_kinds and normalize_skill_kind(kind) not in subject_kinds:
        return False
    return True


def matching_revocation_artifacts(
    revocation_artifacts: list[TitledArtifactContentView] | None,
    *,
    skill_title: str,
    kind: str,
) -> list[TitledArtifactContentView]:
    """Filter supplied artifacts to active revocations for a skill."""
    matches: list[TitledArtifactContentView] = []
    for artifact in revocation_artifacts or []:
        record = artifact_skill_revocation(artifact)
        if record and revocation_matches_skill(
            record,
            skill_title=skill_title,
            kind=kind,
        ):
            matches.append(artifact)
    return matches


def matching_incident_artifacts(
    incident_artifacts: list[TitledArtifactContentView] | None,
    *,
    skill_title: str,
    kind: str,
) -> list[TitledArtifactContentView]:
    """Filter supplied artifacts to unresolved incidents for a skill."""
    matches: list[TitledArtifactContentView] = []
    for artifact in incident_artifacts or []:
        record = artifact_skill_incident(artifact)
        if record and incident_matches_skill(
            record,
            skill_title=skill_title,
            kind=kind,
        ):
            matches.append(artifact)
    return matches


def governed_safety_lifecycle_overlay(
    *,
    skill_title: str,
    kind: str,
    revocation_artifacts: list[TitledArtifactContentView] | None = None,
    incident_artifacts: list[TitledArtifactContentView] | None = None,
) -> dict[str, Any]:
    """Project supplied safety records into a lifecycle overlay."""
    revocations = matching_revocation_artifacts(
        revocation_artifacts,
        skill_title=skill_title,
        kind=kind,
    )
    incidents = matching_incident_artifacts(
        incident_artifacts,
        skill_title=skill_title,
        kind=kind,
    )
    if revocations:
        record = artifact_skill_revocation(revocations[-1])
        return {
            "trust_status": normalize_skill_trust_status(
                record.get("trust_status", "revoked"),
                default="revoked",
            ),
            "quarantine_status": normalize_skill_quarantine_status(
                record.get("quarantine_status", "clear")
            ),
            "activation_status": normalize_skill_activation_status(
                record.get("activation_status", "inactive"),
                default="inactive",
            ),
            "installation_status": normalize_skill_installation_status(
                record.get("installation_status", "blocked"),
                default="blocked",
            ),
            "status_reason": collapse_ws(str(record.get("rationale", "")))
            or "Skill is currently revoked.",
            "revocation_titles": [artifact.title for artifact in revocations],
            "incident_titles": [artifact.title for artifact in incidents],
        }
    if incidents:
        strongest = max(
            incidents,
            key=lambda item: INCIDENT_ENFORCEMENT_ACTIONS.index(
                normalize_incident_enforcement_action(
                    artifact_skill_incident(item).get(
                        "enforcement_action",
                        "none",
                    )
                )
            ),
        )
        record = artifact_skill_incident(strongest)
        action = normalize_incident_enforcement_action(
            record.get("enforcement_action", "none")
        )
        overlay: dict[str, Any] = {
            "status_reason": collapse_ws(str(record.get("rationale", "")))
            or "Skill is currently constrained by an incident record.",
            "revocation_titles": [],
            "incident_titles": [artifact.title for artifact in incidents],
        }
        if action == "restrict":
            overlay["trust_status"] = "restricted"
        elif action == "suspend":
            overlay["trust_status"] = "suspended"
            overlay["activation_status"] = "inactive"
        elif action == "quarantine":
            overlay["quarantine_status"] = "quarantined"
            overlay["activation_status"] = "inactive"
        return overlay
    return {
        "revocation_titles": [],
        "incident_titles": [],
    }


__all__ = [
    "INCIDENT_ENFORCEMENT_ACTIONS",
    "INCIDENT_RECORD_STATUSES",
    "INCIDENT_SEVERITIES",
    "REVOCATION_RECORD_STATUSES",
    "artifact_is_incident_record",
    "artifact_is_revocation_record",
    "artifact_skill_incident",
    "artifact_skill_revocation",
    "governed_safety_lifecycle_overlay",
    "incident_answer_summary",
    "incident_matches_skill",
    "matching_incident_artifacts",
    "matching_revocation_artifacts",
    "normalize_incident_enforcement_action",
    "normalize_incident_record_status",
    "normalize_incident_severity",
    "normalize_revocation_record_status",
    "revocation_answer_summary",
    "revocation_matches_skill",
    "skill_incident_from_payload",
    "skill_revocation_from_payload",
]
