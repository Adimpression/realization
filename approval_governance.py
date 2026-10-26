"""Compatibility facade for package-owned approval governance rules."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from realized_core_governance import approval as _approval
from realized_core_governance._normalization import collapse_ws
from realized_core_governance.approval import (
    APPROVAL_RECORD_STATUSES,
    approval_answer_summary,
    approval_matches_skill,
    artifact_is_approval_record,
    artifact_skill_approval,
    matching_approval_artifacts,
    normalize_approval_record_status,
    skill_approval_from_payload,
)
from realized_core_governance.vocabulary import (
    normalize_skill_approval_class,
    normalize_skill_authorities,
    normalize_skill_kind,
    normalize_skill_risk_tier,
)
from realized_core_semantics.artifacts import ArtifactContentView


# Preserve inexpensive historical private attributes during the compatibility
# window without adding them to the package's public surface.
_string_list = _approval._string_list
_valid_at_or_open = _approval._valid_at_or_open


__all__ = list(_approval.__all__)
