"""Read-only projections of stored skill-governance records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.artifacts import ArtifactContentView


__all__ = [
    "artifact_is_policy_record",
    "artifact_skill_admission",
    "artifact_skill_declaration",
    "artifact_skill_policy",
]


def _stored_mapping(
    artifact: ArtifactContentView,
    key: str,
) -> dict[str, Any]:
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    value = content.get(key, {})
    return dict(value) if isinstance(value, Mapping) else {}


def artifact_skill_declaration(
    artifact: ArtifactContentView,
) -> dict[str, Any]:
    """Return a defensive copy of one stored skill declaration."""
    return _stored_mapping(artifact, "skill_declaration")


def artifact_skill_policy(artifact: ArtifactContentView) -> dict[str, Any]:
    """Return a defensive copy of one stored skill policy."""
    return _stored_mapping(artifact, "skill_policy")


def artifact_skill_admission(artifact: ArtifactContentView) -> dict[str, Any]:
    """Return a defensive copy of one stored skill admission record."""
    return _stored_mapping(artifact, "skill_admission")


def artifact_is_policy_record(artifact: ArtifactContentView) -> bool:
    """Identify a policy record from its non-empty stored policy projection."""
    return bool(artifact_skill_policy(artifact))
