"""Outbound ports that keep Blend independent of effects and presentation."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .coordination import BlendCoordinationRecord
from .history import BlendHistoryRecord
from .observations import BlendExecutionObservation
from .operators import BlendOperator, BlendOperatorInvocation
from .workflows import BlendWorkflowPlan, BlendWorkflowRun
from .worlds import BlendWorld


BlendExecutionObserver = Callable[[BlendExecutionObservation], None]


@dataclass(frozen=True)
class BlendCompositionExecutionEvent:
    """Neutral lifecycle data emitted by a composed-step execution adapter."""

    kind: str
    step_id: str
    title: str
    iteration: int
    branch_label: str = ""
    status: str = ""
    input_payload: dict[str, Any] | None = None
    output_payload: Any = None
    binding_receipts: list[dict[str, Any]] | None = None
    condition_receipts: list[dict[str, Any]] | None = None
    skipped_reason: str = ""
    error: str = ""
    result_payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "step_id": self.step_id,
            "title": self.title,
            "iteration": self.iteration,
            "branch_label": self.branch_label,
            "status": self.status,
            "input_payload": self.input_payload,
            "output_payload": self.output_payload,
            "binding_receipts": self.binding_receipts,
            "condition_receipts": self.condition_receipts,
            "skipped_reason": self.skipped_reason,
            "error": self.error,
            "result_payload": self.result_payload,
        }


@dataclass(frozen=True)
class BlendCompositionExecutionResult:
    """Neutral authoritative output returned by a composition adapter."""

    steps: list[dict[str, Any]]
    plan_authorities: list[str]
    final_outputs_by_step: dict[str, Any]


BlendCompositionInvoker = Callable[[str, dict[str, Any], dict[str, Any]], Any]
BlendCompositionObserver = Callable[[BlendCompositionExecutionEvent], None]


@runtime_checkable
class BlendCompositionPort(Protocol):
    """Execute branch, iteration, binding, and skip mechanics for a workflow."""

    def execute(
        self,
        *,
        steps: Sequence[dict[str, Any]],
        invoker: BlendCompositionInvoker,
        root_inputs: Mapping[str, Any],
        root_references: Mapping[str, Any],
        execution_observer: BlendCompositionObserver | None = None,
    ) -> BlendCompositionExecutionResult: ...


@runtime_checkable
class BlendClock(Protocol):
    """Supply timestamps without coupling orchestration to a system clock."""

    def now(self) -> str: ...


@runtime_checkable
class BlendIdentifierFactory(Protocol):
    """Supply prefixed identifiers without coupling orchestration to UUIDs."""

    def new_identifier(self, prefix: str) -> str: ...


@runtime_checkable
class BlendOperatorInvocationPort(Protocol):
    """Execute an already resolved operator through a composed runtime adapter."""

    def invoke(
        self,
        *,
        operator: BlendOperator,
        invocation: BlendOperatorInvocation,
        handle: Any,
    ) -> dict[str, Any]: ...


@runtime_checkable
class BlendWorkflowRepository(Protocol):
    """Persist and query authoritative workflow plans and runs."""

    def load_plan(self, workflow_id: str) -> BlendWorkflowPlan: ...

    def load_run(self, workflow_run_id: str) -> BlendWorkflowRun: ...

    def load_index(self) -> dict[str, Any]: ...

    def list_summaries(
        self,
        *,
        kind: str = "runs",
        status: str = "",
        limit: int = 20,
    ) -> Sequence[dict[str, Any]]: ...

    def list_runs_for_plan(
        self,
        workflow_id: str,
        *,
        status: str = "",
        limit: int = 20,
    ) -> Sequence[dict[str, Any]]: ...

    def persist(
        self,
        *,
        plan: BlendWorkflowPlan,
        run: BlendWorkflowRun,
        session_id: str = "",
    ) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]: ...


@runtime_checkable
class BlendWorldRepository(Protocol):
    """Persist and query authoritative Blend worlds."""

    def exists(self) -> bool: ...

    def load(self) -> BlendWorld: ...

    def persist(self, world: BlendWorld) -> str: ...


@runtime_checkable
class BlendHistoryRepository(Protocol):
    """Persist and query authoritative narratable history."""

    def append(self, record: BlendHistoryRecord) -> BlendHistoryRecord: ...

    def list_for_aggregate(
        self,
        *,
        aggregate_kind: str,
        aggregate_id: str,
    ) -> Sequence[BlendHistoryRecord]: ...


@runtime_checkable
class BlendCoordinationRepository(Protocol):
    """Persist and query structural multi-actor coordination state."""

    def load(self, coordination_id: str) -> BlendCoordinationRecord: ...

    def persist(self, record: BlendCoordinationRecord) -> BlendCoordinationRecord: ...


__all__ = [
    "BlendClock",
    "BlendCompositionExecutionEvent",
    "BlendCompositionExecutionResult",
    "BlendCompositionInvoker",
    "BlendCompositionObserver",
    "BlendCompositionPort",
    "BlendCoordinationRepository",
    "BlendExecutionObserver",
    "BlendHistoryRepository",
    "BlendIdentifierFactory",
    "BlendOperatorInvocationPort",
    "BlendWorkflowRepository",
    "BlendWorldRepository",
]
