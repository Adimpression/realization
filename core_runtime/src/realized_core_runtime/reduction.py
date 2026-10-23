"""Governed lifecycle orchestration from non-achievedness to realization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from realized_core_runtime.attempts import AttemptInterrupted

from realized_core_runtime.contracts import (
    RealizationResumePort,
    RealizationRunPort,
    RealizationRunState,
)


def run_to_realization(
    runtime: RealizationRunPort,
    *,
    max_steps: int = 256,
) -> RealizationRunState:
    """Advance the supplied runtime until closure, pause, exhaustion, or budget."""
    _observe_stop(runtime)
    host_interaction = runtime.runtime_host_interaction_context_payload()
    runtime.state.root().metadata["host_interaction"] = dict(host_interaction)
    runtime.state.root().metadata["host_interaction_backend_kind"] = str(
        host_interaction.get("backend_kind", "host")
    )
    primary_workspace = runtime.primary_host_interaction_workspace()
    if primary_workspace is not None:
        runtime.state.root().metadata["host_interaction_primary_workspace"] = (
            primary_workspace.to_dict()
        )

    runtime.prepare_root_prior_learning_fast_path()
    runtime.initialize_root_semantics()
    runtime.propagate([runtime.state.root()])
    if runtime.is_committable(runtime.state.root()):
        runtime.commit_closure(runtime.state.root())
        runtime.finalize_run()
        return runtime.state

    runtime.refresh_frontier()
    steps = 0
    while runtime.state.frontier and steps < max_steps:
        _observe_stop(runtime)
        steps += 1
        node = runtime.pop_best_frontier()
        if node is None:
            break
        if runtime.is_terminal(node):
            continue

        runtime.state.visit_counts[node.id] = (
            runtime.state.visit_counts.get(node.id, 0) + 1
        )
        runtime.state.record_step(
            kind="frontier_selection",
            node_id=node.id,
            intent="Select the next active frontier element for governed refinement.",
            action="choose next frontier candidate",
            result=f"selected {node.not_label}",
            evaluation=(
                "selection followed an explicit candidate choice over the current "
                "frontier items"
            ),
            payload={
                "proposal_id": node.metadata.get(
                    "frontier_selection_proposal_id", ""
                ),
                "candidate_order": list(
                    node.metadata.get("frontier_candidate_order", [])
                ),
            },
        )

        runtime.reduce_not(node)
        _observe_stop(runtime)
        runtime.propagate([node])
        runtime.refresh_frontier()

        if runtime.is_closed(runtime.state.root()):
            break
        if (
            runtime.state.root_id in runtime.state.paused
            and not runtime.state.frontier
        ):
            break

    runtime.finalize_run()
    _observe_stop(runtime)
    return runtime.state


def _observe_stop(runtime: RealizationRunPort) -> None:
    """Honor an optional attempt stop probe without giving it semantic meaning."""

    probe = getattr(runtime, "attempt_stop_requested", None)
    if isinstance(probe, Callable) and probe():
        raise AttemptInterrupted()


def resume_to_realization(
    runtime: RealizationResumePort,
    *,
    open_status: Any,
    max_steps: int = 256,
) -> RealizationRunState:
    """Reopen eligible state and resume through the application's public run ABI."""
    reopened: list[str] = []
    for node_id in sorted(runtime.state.paused | runtime.state.incomplete):
        if (
            node_id not in runtime.state.closed
            and node_id not in runtime.state.inadmissible
        ):
            runtime.state.paused.discard(node_id)
            runtime.state.incomplete.discard(node_id)
            runtime.state.status[node_id] = open_status
            runtime.state.frontier.add(node_id)
            reopened.append(node_id)

    runtime.state.frontier.add(runtime.state.root_id)
    runtime.state.record_inlet(
        kind="resume_signal",
        semantic_identity=runtime.state.root().semantic_unit,
        payload={"node_id": runtime.state.root_id, "reopened": reopened},
    )
    runtime.state.record_step(
        kind="resume",
        node_id=runtime.state.root_id,
        intent="Resume governed reduction without semantic rupture.",
        action="reopen resumable non-achievednesses",
        result="resume state prepared",
        evaluation="paused or incomplete nodes became eligible for re-evaluation",
        payload={"reopened": reopened},
    )
    return runtime.run(max_steps=max_steps)


__all__ = ["resume_to_realization", "run_to_realization"]
