"""Dependency-inversion ports for the governed realization lifecycle."""

from __future__ import annotations

from collections.abc import Iterable, MutableMapping, MutableSet
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RealizationNode(Protocol):
    """Minimum node surface needed by lifecycle orchestration."""

    id: str
    not_label: str
    semantic_unit: str
    metadata: MutableMapping[str, Any]


@runtime_checkable
class SerializableWorkspace(Protocol):
    """Workspace projection accepted by the runtime context ledger."""

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class RealizationRunState(Protocol):
    """State operations used while advancing one realization run."""

    root_id: str
    frontier: MutableSet[str]
    paused: MutableSet[str]
    visit_counts: MutableMapping[str, int]

    def root(self) -> RealizationNode: ...

    def record_step(
        self,
        *,
        kind: str,
        node_id: str | None,
        intent: str,
        action: str,
        result: str,
        evaluation: str,
        payload: dict[str, Any] | None = None,
    ) -> Any: ...


@runtime_checkable
class RealizationResumeState(RealizationRunState, Protocol):
    """Additional state operations needed only when resuming a run."""

    incomplete: MutableSet[str]
    closed: MutableSet[str]
    inadmissible: MutableSet[str]
    status: MutableMapping[str, Any]

    def record_inlet(
        self,
        *,
        kind: str,
        semantic_identity: str,
        payload: dict[str, Any],
    ) -> Any: ...


@runtime_checkable
class RealizationRunPort(Protocol):
    """Domain and infrastructure behavior required by a fresh run."""

    state: RealizationRunState

    def runtime_host_interaction_context_payload(self) -> dict[str, Any]: ...

    def primary_host_interaction_workspace(
        self,
    ) -> SerializableWorkspace | None: ...

    def prepare_root_prior_learning_fast_path(self) -> Any: ...

    def initialize_root_semantics(self) -> Any: ...

    def propagate(self, seeds: Iterable[RealizationNode]) -> Any: ...

    def is_committable(self, node: RealizationNode) -> bool: ...

    def commit_closure(self, node: RealizationNode) -> Any: ...

    def finalize_run(self) -> Any: ...

    def refresh_frontier(self) -> Any: ...

    def pop_best_frontier(self) -> RealizationNode | None: ...

    def is_terminal(self, node: RealizationNode) -> bool: ...

    def reduce_not(self, node: RealizationNode) -> Any: ...

    def is_closed(self, node: RealizationNode) -> bool: ...


@runtime_checkable
class RealizationResumePort(Protocol):
    """Narrow application adapter required to resume through its public run ABI."""

    state: RealizationResumeState

    def run(self, *, max_steps: int = 256) -> RealizationRunState: ...


__all__ = [
    "RealizationNode",
    "RealizationResumePort",
    "RealizationResumeState",
    "RealizationRunPort",
    "RealizationRunState",
    "SerializableWorkspace",
]
