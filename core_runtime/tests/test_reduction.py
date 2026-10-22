from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any

from realized_core_runtime import (
    AttemptInterrupted,
    resume_to_realization,
    run_to_realization,
)


@dataclass
class FakeNode:
    id: str = "root"
    not_label: str = "Not(realized)"
    semantic_unit: str = "Realize the requested result"
    metadata: dict[str, Any] = field(default_factory=dict)


class FakeState:
    def __init__(self) -> None:
        self.root_id = "root"
        self.root_node = FakeNode()
        self.frontier = {self.root_id}
        self.paused: set[str] = set()
        self.incomplete: set[str] = set()
        self.closed: set[str] = set()
        self.inadmissible: set[str] = set()
        self.status: dict[str, Any] = {}
        self.visit_counts: dict[str, int] = {}
        self.steps: list[dict[str, Any]] = []
        self.inlets: list[dict[str, Any]] = []

    def root(self) -> FakeNode:
        return self.root_node

    def record_step(self, **record: Any) -> dict[str, Any]:
        self.steps.append(record)
        return record

    def record_inlet(self, **record: Any) -> dict[str, Any]:
        self.inlets.append(record)
        return record


@dataclass
class FakeWorkspace:
    path: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path}


class FakeRuntime:
    def __init__(self) -> None:
        self.state = FakeState()
        self.actions: list[str] = []
        self.committable = False
        self.terminal = False
        self.close_on_reduce = False
        self.pause_on_reduce = False
        self.return_no_frontier_node = False
        self.resume_calls: list[int] = []

    def runtime_host_interaction_context_payload(self) -> dict[str, Any]:
        self.actions.append("host_context")
        return {"backend_kind": "test", "allowed_capabilities": ["read"]}

    def primary_host_interaction_workspace(self) -> FakeWorkspace:
        self.actions.append("primary_workspace")
        return FakeWorkspace(path="/workspace")

    def prepare_root_prior_learning_fast_path(self) -> None:
        self.actions.append("prepare_prior_learning")

    def initialize_root_semantics(self) -> None:
        self.actions.append("initialize_semantics")

    def propagate(self, seeds: list[FakeNode]) -> None:
        self.actions.append("propagate:" + ",".join(node.id for node in seeds))

    def is_committable(self, node: FakeNode) -> bool:
        self.actions.append(f"committable:{node.id}")
        return self.committable

    def commit_closure(self, node: FakeNode) -> None:
        self.actions.append(f"commit:{node.id}")
        self.state.closed.add(node.id)

    def finalize_run(self) -> None:
        self.actions.append("finalize")

    def refresh_frontier(self) -> None:
        self.actions.append("refresh_frontier")

    def pop_best_frontier(self) -> FakeNode | None:
        self.actions.append("pop_frontier")
        if self.return_no_frontier_node:
            self.state.frontier.clear()
            return None
        self.state.frontier.discard(self.state.root_id)
        return self.state.root()

    def is_terminal(self, node: FakeNode) -> bool:
        self.actions.append(f"terminal:{node.id}")
        return self.terminal

    def reduce_not(self, node: FakeNode) -> None:
        self.actions.append(f"reduce:{node.id}")
        if self.close_on_reduce:
            self.state.closed.add(node.id)
        if self.pause_on_reduce:
            self.state.paused.add(node.id)

    def is_closed(self, node: FakeNode) -> bool:
        self.actions.append(f"closed:{node.id}")
        return node.id in self.state.closed

    def run(self, *, max_steps: int = 256) -> FakeState:
        self.resume_calls.append(max_steps)
        return self.state


class RealizationLifecycleContractTests(unittest.TestCase):
    def test_immediately_committable_root_closes_and_finalizes_once(self) -> None:
        runtime = FakeRuntime()
        runtime.committable = True

        result = run_to_realization(runtime, max_steps=9)

        self.assertIs(runtime.state, result)
        self.assertEqual(
            [
                "host_context",
                "primary_workspace",
                "prepare_prior_learning",
                "initialize_semantics",
                "propagate:root",
                "committable:root",
                "commit:root",
                "finalize",
            ],
            runtime.actions,
        )
        self.assertEqual(
            "test",
            runtime.state.root().metadata["host_interaction_backend_kind"],
        )
        self.assertEqual(
            {"path": "/workspace"},
            runtime.state.root().metadata["host_interaction_primary_workspace"],
        )

    def test_frontier_selection_reduces_propagates_and_stops_at_closure(self) -> None:
        runtime = FakeRuntime()
        runtime.close_on_reduce = True
        runtime.state.root().metadata.update(
            {
                "frontier_selection_proposal_id": "proposal-1",
                "frontier_candidate_order": ("root", "later"),
            }
        )

        result = run_to_realization(runtime, max_steps=4)

        self.assertIs(runtime.state, result)
        self.assertEqual({"root": 1}, runtime.state.visit_counts)
        self.assertEqual(1, len(runtime.state.steps))
        self.assertEqual("frontier_selection", runtime.state.steps[0]["kind"])
        self.assertEqual("selected Not(realized)", runtime.state.steps[0]["result"])
        self.assertEqual(
            {"proposal_id": "proposal-1", "candidate_order": ["root", "later"]},
            runtime.state.steps[0]["payload"],
        )
        self.assertEqual(1, runtime.actions.count("reduce:root"))
        self.assertEqual("finalize", runtime.actions[-1])

    def test_zero_step_budget_finalizes_without_reducing_frontier(self) -> None:
        runtime = FakeRuntime()

        run_to_realization(runtime, max_steps=0)

        self.assertNotIn("pop_frontier", runtime.actions)
        self.assertFalse(any(action.startswith("reduce:") for action in runtime.actions))
        self.assertEqual("finalize", runtime.actions[-1])

    def test_optional_attempt_stop_probe_interrupts_before_semantic_work(self) -> None:
        runtime = FakeRuntime()
        runtime.attempt_stop_requested = lambda: True

        with self.assertRaises(AttemptInterrupted):
            run_to_realization(runtime, max_steps=4)

        self.assertEqual([], runtime.actions)
        self.assertEqual(set(), runtime.state.closed)
        self.assertEqual([], runtime.state.steps)

    def test_terminal_frontier_node_is_not_reduced(self) -> None:
        runtime = FakeRuntime()
        runtime.terminal = True

        run_to_realization(runtime, max_steps=2)

        self.assertFalse(any(action.startswith("reduce:") for action in runtime.actions))
        self.assertEqual({}, runtime.state.visit_counts)
        self.assertEqual([], runtime.state.steps)
        self.assertEqual("finalize", runtime.actions[-1])

    def test_paused_root_with_empty_frontier_finalizes_after_one_reduction(self) -> None:
        runtime = FakeRuntime()
        runtime.pause_on_reduce = True

        run_to_realization(runtime, max_steps=8)

        self.assertEqual({"root"}, runtime.state.paused)
        self.assertEqual(1, runtime.actions.count("reduce:root"))
        self.assertEqual("finalize", runtime.actions[-1])

    def test_resume_reopens_only_eligible_nodes_then_uses_public_run_abi(self) -> None:
        runtime = FakeRuntime()
        runtime.state.frontier.clear()
        runtime.state.paused.update({"root", "already-closed"})
        runtime.state.incomplete.update({"eligible", "inadmissible"})
        runtime.state.closed.add("already-closed")
        runtime.state.inadmissible.add("inadmissible")
        open_status = object()

        result = resume_to_realization(
            runtime,
            open_status=open_status,
            max_steps=13,
        )

        self.assertIs(runtime.state, result)
        self.assertEqual([13], runtime.resume_calls)
        self.assertEqual({"eligible", "root"}, runtime.state.frontier)
        self.assertIs(open_status, runtime.state.status["eligible"])
        self.assertIs(open_status, runtime.state.status["root"])
        self.assertEqual({"already-closed"}, runtime.state.paused)
        self.assertEqual({"inadmissible"}, runtime.state.incomplete)
        self.assertEqual("resume_signal", runtime.state.inlets[0]["kind"])
        self.assertEqual(
            ["eligible", "root"],
            runtime.state.inlets[0]["payload"]["reopened"],
        )
        self.assertEqual("resume", runtime.state.steps[0]["kind"])


if __name__ == "__main__":
    unittest.main()
