"""Compatibility facade for package-owned skill safety governance rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from realized_core_governance import safety as _safety
from realized_core_governance._normalization import collapse_ws
from realized_core_governance.lifecycle import (
    normalize_skill_activation_status,
    normalize_skill_installation_status,
    normalize_skill_quarantine_status,
    normalize_skill_trust_status,
)
from realized_core_governance.safety import (
    INCIDENT_ENFORCEMENT_ACTIONS,
    INCIDENT_RECORD_STATUSES,
    INCIDENT_SEVERITIES,
    REVOCATION_RECORD_STATUSES,
    artifact_is_incident_record,
    artifact_is_revocation_record,
    artifact_skill_incident,
    artifact_skill_revocation,
    governed_safety_lifecycle_overlay,
    incident_answer_summary,
    incident_matches_skill,
    matching_incident_artifacts,
    matching_revocation_artifacts,
    normalize_incident_enforcement_action,
    normalize_incident_record_status,
    normalize_incident_severity,
    normalize_revocation_record_status,
    revocation_answer_summary,
    revocation_matches_skill,
    skill_incident_from_payload,
    skill_revocation_from_payload,
)
from realized_core_governance.vocabulary import normalize_skill_kind
from realized_core_semantics.artifacts import (
    ArtifactContentView,
    TitledArtifactContentView,
)


# Preserve inexpensive historical private attributes during the compatibility
# window without adding them to the package's public surface.
_SKILL_KINDS = {
    "knowledge",
    "ability",
    "policy",
    "approval",
    "revocation",
    "incident",
}
_string_list = _safety._string_list
_normalize_skill_kind = _safety._normalize_skill_kind
_valid_at_or_open = _safety._valid_at_or_open


__all__ = list(_safety.__all__)
