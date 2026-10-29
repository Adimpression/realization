"""Workstation composition of governance policy and runtime evidence."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_governance.admission import evaluate_skill_admission_with_compatibility
from realized_core_runtime.skill_compatibility import runtime_skill_compatibility_issue
from realized_core_semantics.applied_model import Artifact, utc_now


def evaluate_workstation_skill_admission(
    declaration: Mapping[str, Any],
    *,
    skill_title: str = "",
    kind: str,
    executor_framework: str = "",
    skill_content: Mapping[str, Any] | None = None,
    policy_artifacts: list[Artifact] | None = None,
    approval_artifacts: list[Artifact] | None = None,
) -> dict[str, Any]:
    """Evaluate workstation admission without making runtime own the decision."""
    compatibility_issue = runtime_skill_compatibility_issue(
        kind=kind,
        executor_framework=executor_framework,
        risk_tier=declaration.get("risk_tier", "tier1_bounded_transform"),
        skill_content=skill_content,
    )
    return evaluate_skill_admission_with_compatibility(
        declaration,
        skill_title=skill_title,
        kind=kind,
        executor_framework=executor_framework,
        compatibility_issue=compatibility_issue,
        policy_artifacts=policy_artifacts,
        approval_artifacts=approval_artifacts,
        evaluated_at=utc_now,
    )


__all__ = ["evaluate_workstation_skill_admission"]
