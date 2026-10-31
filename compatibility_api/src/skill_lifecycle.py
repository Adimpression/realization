# See MODULES.md for the repository module map before editing.
"""Compatibility facade for canonical skill lifecycle rules."""

from realized_core_governance.lifecycle import (
    SKILL_ACTIVATION_STATUSES,
    SKILL_INSTALLATION_STATUSES,
    SKILL_QUARANTINE_STATUSES,
    SKILL_REVIEW_STATUSES,
    SKILL_TRUST_STATUSES,
    ArtifactContentView,
    _lifecycle_mapping,
    artifact_effective_skill_lifecycle,
    artifact_skill_lifecycle,
    normalize_skill_activation_status,
    normalize_skill_installation_status,
    normalize_skill_quarantine_status,
    normalize_skill_review_status,
    normalize_skill_trust_status,
    skill_lifecycle_allows_invocation,
    skill_lifecycle_from_payload,
    synthesized_skill_lifecycle,
    collapse_ws,
    utc_now,
)


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
