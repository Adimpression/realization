"""Read-only governance inventory loading and record classification."""

from __future__ import annotations

import time
from typing import Any, Protocol, runtime_checkable

from realized_core_semantics.artifacts import ArtifactContentView

from .approval import artifact_is_approval_record
from .records import artifact_is_policy_record
from .safety import artifact_is_incident_record, artifact_is_revocation_record


@runtime_checkable
class GovernanceInventoryReader(Protocol):
    """Port for reading the complete persisted artifact inventory once."""

    def load_all_artifacts(self) -> list[ArtifactContentView]: ...


def _elapsed_seconds(started_at: float) -> float:
    return round(time.perf_counter() - started_at, 6)


def load_governance_inventory(store: Any) -> dict[str, Any]:
    """Load and independently classify the supplied artifact inventory."""
    started_at = time.perf_counter()
    artifacts = store.load_all_artifacts()
    return {
        "artifacts": artifacts,
        "policies": [
            artifact for artifact in artifacts if artifact_is_policy_record(artifact)
        ],
        "approvals": [
            artifact for artifact in artifacts if artifact_is_approval_record(artifact)
        ],
        "revocations": [
            artifact
            for artifact in artifacts
            if artifact_is_revocation_record(artifact)
        ],
        "incidents": [
            artifact for artifact in artifacts if artifact_is_incident_record(artifact)
        ],
        "timings": {
            "load_seconds": _elapsed_seconds(started_at),
        },
    }


__all__ = ["GovernanceInventoryReader", "load_governance_inventory"]
