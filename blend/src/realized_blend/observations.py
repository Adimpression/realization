"""Lossy lifecycle observations emitted after Blend execution transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from realized_core_semantics.values import json_safe


@dataclass(frozen=True)
class BlendWorkflowExecutionEvent:
    kind: str
    workflow_execution_id: str
    workflow_id: str
    session_id: str
    capability_name: str
    target_name: str
    timestamp: str
    workflow_run_id: str = ""
    step_id: str = ""
    operator_name: str = ""
    operator_kind: str = ""
    iteration: int = 0
    branch_label: str = ""
    status: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return json_safe(
            {
                "kind": self.kind,
                "workflow_execution_id": self.workflow_execution_id,
                "workflow_id": self.workflow_id,
                "workflow_run_id": self.workflow_run_id,
                "session_id": self.session_id,
                "capability_name": self.capability_name,
                "target_name": self.target_name,
                "timestamp": self.timestamp,
                "step_id": self.step_id,
                "operator_name": self.operator_name,
                "operator_kind": self.operator_kind,
                "iteration": self.iteration,
                "branch_label": self.branch_label,
                "status": self.status,
                "payload": self.payload,
            }
        )


BlendExecutionObservation = BlendWorkflowExecutionEvent


__all__ = ["BlendExecutionObservation", "BlendWorkflowExecutionEvent"]
