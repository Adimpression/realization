"""Deterministic projections from governed artifacts into skill vocabulary."""

from __future__ import annotations

from collections.abc import Mapping

from realized_core_governance.approval import artifact_is_approval_record
from realized_core_governance.records import artifact_is_policy_record
from realized_core_governance.safety import (
    artifact_is_incident_record,
    artifact_is_revocation_record,
)
from realized_core_governance.vocabulary import normalize_skill_kind
from realized_core_semantics.applied_model import Artifact, enum_text


def skill_kind_from_artifact(artifact: Artifact) -> str:
    """Project one artifact into its effective portable skill kind."""
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    if artifact_is_policy_record(artifact):
        return "policy"
    if artifact_is_approval_record(artifact):
        return "approval"
    if artifact_is_revocation_record(artifact):
        return "revocation"
    if artifact_is_incident_record(artifact):
        return "incident"
    return normalize_skill_kind(
        content.get("skill_kind", ""),
        default=enum_text(artifact.artifact_type),
    )


__all__ = ["skill_kind_from_artifact"]
