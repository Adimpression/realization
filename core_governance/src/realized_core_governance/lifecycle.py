"""Skill lifecycle normalization and lifecycle-only current-use rules."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_governance._normalization import collapse_ws
from realized_core_semantics.artifacts import ArtifactContentView
from realized_core_semantics.values import utc_now


SKILL_REVIEW_STATUSES = (
    "pending_review",
    "reviewed",
    "review_rejected",
)
SKILL_INSTALLATION_STATUSES = (
    "installed",
    "blocked",
)
SKILL_ACTIVATION_STATUSES = (
    "active",
    "inactive",
)
SKILL_TRUST_STATUSES = (
    "trusted",
    "restricted",
    "suspended",
    "revoked",
)
SKILL_QUARANTINE_STATUSES = (
    "clear",
    "quarantined",
)


def _lifecycle_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): item for key, item in value.items()}


def normalize_skill_review_status(
    value: Any,
    *,
    default: str = "pending_review",
) -> str:
    """Return a known review status or the caller's default."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_REVIEW_STATUSES:
        return normalized
    return default


def normalize_skill_installation_status(
    value: Any,
    *,
    default: str = "installed",
) -> str:
    """Return a known installation status or the caller's default."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_INSTALLATION_STATUSES:
        return normalized
    return default


def normalize_skill_activation_status(
    value: Any,
    *,
    default: str = "active",
) -> str:
    """Return a known activation status or the caller's default."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_ACTIVATION_STATUSES:
        return normalized
    return default


def normalize_skill_trust_status(
    value: Any,
    *,
    default: str = "trusted",
) -> str:
    """Return a known trust status or the caller's default."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_TRUST_STATUSES:
        return normalized
    return default


def normalize_skill_quarantine_status(
    value: Any,
    *,
    default: str = "clear",
) -> str:
    """Return a known quarantine status or the caller's default."""
    normalized = collapse_ws(str(value or default)).lower()
    if normalized in SKILL_QUARANTINE_STATUSES:
        return normalized
    return default


def synthesized_skill_lifecycle(
    *,
    admission_status: str = "",
    policy_record: bool = False,
    default_updated_at: str = "",
) -> dict[str, Any]:
    """Synthesize conservative lifecycle state from an admission result."""
    normalized_admission = collapse_ws(admission_status).lower()
    if policy_record and not normalized_admission:
        normalized_admission = "admitted"
    if normalized_admission == "admitted":
        installation_status = "installed"
        activation_status = "active"
        trust_status = "trusted"
        status_reason = "Skill is installed, active, and trusted for invocation."
    elif normalized_admission == "held":
        installation_status = "installed"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = (
            "Skill remains installed but inactive while admission is held."
        )
    elif normalized_admission == "rejected":
        installation_status = "blocked"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = "Skill is blocked because admission was rejected."
    else:
        installation_status = "installed"
        activation_status = "inactive"
        trust_status = "restricted"
        status_reason = (
            "Skill lifecycle was synthesized without a current admitted "
            "invocation state."
        )
    return {
        "review_status": "pending_review",
        "admission_status": normalized_admission,
        "installation_status": installation_status,
        "activation_status": activation_status,
        "trust_status": trust_status,
        "quarantine_status": "clear",
        "status_reason": status_reason,
        "updated_at": collapse_ws(default_updated_at) or utc_now(),
    }


def skill_lifecycle_from_payload(
    payload: Mapping[str, Any] | None = None,
    *,
    admission_status: str = "",
    policy_record: bool = False,
    default_updated_at: str = "",
) -> dict[str, Any]:
    """Normalize a lifecycle block and reconcile its admission projection."""
    raw_payload = _lifecycle_mapping(payload)
    raw_lifecycle = _lifecycle_mapping(raw_payload.get("lifecycle", raw_payload))
    defaults = synthesized_skill_lifecycle(
        admission_status=admission_status
        or raw_lifecycle.get("admission_status", ""),
        policy_record=policy_record,
        default_updated_at=default_updated_at
        or raw_lifecycle.get("updated_at", ""),
    )
    return {
        "review_status": normalize_skill_review_status(
            raw_lifecycle.get("review_status", defaults["review_status"])
        ),
        "admission_status": collapse_ws(
            admission_status or raw_lifecycle.get("admission_status", "")
        )
        or defaults["admission_status"],
        "installation_status": normalize_skill_installation_status(
            raw_lifecycle.get(
                "installation_status", defaults["installation_status"]
            )
        ),
        "activation_status": normalize_skill_activation_status(
            raw_lifecycle.get("activation_status", defaults["activation_status"])
        ),
        "trust_status": normalize_skill_trust_status(
            raw_lifecycle.get("trust_status", defaults["trust_status"])
        ),
        "quarantine_status": normalize_skill_quarantine_status(
            raw_lifecycle.get(
                "quarantine_status", defaults["quarantine_status"]
            )
        ),
        "status_reason": collapse_ws(
            str(raw_lifecycle.get("status_reason", defaults["status_reason"]))
        ),
        "updated_at": collapse_ws(
            str(raw_lifecycle.get("updated_at", defaults["updated_at"]))
        )
        or defaults["updated_at"],
    }


def artifact_skill_lifecycle(artifact: ArtifactContentView) -> dict[str, Any]:
    """Read or conservatively synthesize an artifact lifecycle record."""
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    raw_lifecycle = _lifecycle_mapping(content.get("skill_lifecycle", {}))
    raw_admission = _lifecycle_mapping(content.get("skill_admission", {}))
    if not raw_lifecycle and not raw_admission and not content.get("skill_policy"):
        return {}
    return skill_lifecycle_from_payload(
        raw_lifecycle,
        admission_status=str(
            raw_admission.get("status", raw_lifecycle.get("admission_status", ""))
        ),
        policy_record=bool(content.get("skill_policy")),
        default_updated_at=str(
            raw_lifecycle.get("updated_at")
            or raw_admission.get("evaluated_at")
            or content.get("created_at")
            or ""
        ),
    )


def artifact_effective_skill_lifecycle(
    artifact: ArtifactContentView,
    *,
    current_admission_status: str = "",
) -> dict[str, Any]:
    """Project lifecycle state that governs current artifact use."""
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    raw_lifecycle = _lifecycle_mapping(content.get("skill_lifecycle", {}))
    if raw_lifecycle:
        return artifact_skill_lifecycle(artifact)
    raw_admission = _lifecycle_mapping(content.get("skill_admission", {}))
    if (
        not raw_admission
        and not current_admission_status
        and not content.get("skill_policy")
    ):
        return {}
    admission_status = collapse_ws(current_admission_status) or collapse_ws(
        str(raw_admission.get("status", ""))
    )
    return synthesized_skill_lifecycle(
        admission_status=admission_status,
        policy_record=bool(content.get("skill_policy")),
        default_updated_at=str(
            raw_admission.get("evaluated_at") or content.get("created_at") or ""
        ),
    )


def skill_lifecycle_allows_invocation(
    lifecycle: Mapping[str, Any] | None,
) -> tuple[bool, str]:
    """Evaluate only the lifecycle gates for current invocation."""
    normalized = _lifecycle_mapping(lifecycle)
    if not normalized:
        return True, ""
    quarantine_status = normalize_skill_quarantine_status(
        normalized.get("quarantine_status", "clear")
    )
    if quarantine_status == "quarantined":
        return False, "Governed skill is quarantined and cannot be invoked."
    trust_status = normalize_skill_trust_status(
        normalized.get("trust_status", "trusted")
    )
    if trust_status in {"restricted", "suspended", "revoked"}:
        return False, f"Governed skill trust status is {trust_status}."
    installation_status = normalize_skill_installation_status(
        normalized.get("installation_status", "installed")
    )
    if installation_status != "installed":
        return False, (
            f"Governed skill installation status is {installation_status}."
        )
    activation_status = normalize_skill_activation_status(
        normalized.get("activation_status", "active")
    )
    if activation_status != "active":
        return False, f"Governed skill activation status is {activation_status}."
    return True, ""


__all__ = [
    "SKILL_ACTIVATION_STATUSES",
    "SKILL_INSTALLATION_STATUSES",
    "SKILL_QUARANTINE_STATUSES",
    "SKILL_REVIEW_STATUSES",
    "SKILL_TRUST_STATUSES",
    "artifact_effective_skill_lifecycle",
    "artifact_skill_lifecycle",
    "normalize_skill_activation_status",
    "normalize_skill_installation_status",
    "normalize_skill_quarantine_status",
    "normalize_skill_review_status",
    "normalize_skill_trust_status",
    "skill_lifecycle_allows_invocation",
    "skill_lifecycle_from_payload",
    "synthesized_skill_lifecycle",
]
