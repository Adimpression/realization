# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.state import SystemState
from realized_core_semantics.applied_model import NodeStatus, ProposalObject, SemanticNode, SupportView
from realized_core_semantics.applied_primitives import (
    ClosureRule,
    DecompositionMode,
    NodeOrigin,
    PriorityLevel,
    SupportScore,
    ThreeLevel,
)
from realized_core_semantics.proposals import ProposalGovernanceStatus, ProposalType, SupplementMode


class DecompositionPromptContextTests(unittest.TestCase):
    def make_child(self, *, node_id: str, semantic_unit: str, depth: int, parent_id: str) -> SemanticNode:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating child.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `make_child(node_id='artifact-force', semantic_unit='Physics / Force / Force From Mass And Acceleration', depth=3, parent_id='artifact-force')`
            Output: SemanticNode(id='not-force', semantic_unit='Physics / Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            node_id: Value for `node_id` used by `make_child`. Expected type: `str`.
            semantic_unit: Value for `semantic_unit` used by `make_child`. Expected type: `str`.
            depth: Value for `depth` used by `make_child`. Expected type: `int`.
            parent_id: Value for `parent_id` used by `make_child`. Expected type: `str`.

        Returns:
            SemanticNode: Result produced by `make_child`.
        """
        return SemanticNode(
            id=node_id,
            semantic_unit=semantic_unit,
            role="generic",
            description=f"Work on {semantic_unit}.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=depth,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=parent_id,
            origin=NodeOrigin.CONTROLLER,
        )

    def build_controller_with_siblings(self) -> tuple[BSSCController, SemanticNode, SemanticNode, SemanticNode, SemanticNode]:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with building controller with siblings.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `build_controller_with_siblings()`
            Output: ('Physics', 'Force')

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            tuple[BSSCController, SemanticNode, SemanticNode, SemanticNode, SemanticNode]: Result produced by `build_controller_with_siblings`.
        """
        state = SystemState.bootstrap("Solve the mechanics task.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        parent = SemanticNode(
            id="node-parent",
            semantic_unit="determine the governing mechanics relation",
            role="support",
            description="Figure out the relevant relation before applying it.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(parent, parent_id=root.id)

        prior_certain = self.make_child(
            node_id="node-prior-certain",
            semantic_unit="identify the already-settled force relation",
            depth=2,
            parent_id=parent.id,
        )
        state.register_node(prior_certain, parent_id=parent.id)
        state.certainty[prior_certain.id] = ThreeLevel.HIGH
        state.status[prior_certain.id] = NodeStatus.CLOSED
        state.support[prior_certain.id] = SupportView(direct=["ev-1"], upstream=[], score=SupportScore.OK)

        prior_uncertain = self.make_child(
            node_id="node-prior-uncertain",
            semantic_unit="consider whether extra context is needed",
            depth=2,
            parent_id=parent.id,
        )
        state.register_node(prior_uncertain, parent_id=parent.id)
        state.certainty[prior_uncertain.id] = ThreeLevel.LOW
        state.status[prior_uncertain.id] = NodeStatus.OPEN

        current = self.make_child(
            node_id="node-current",
            semantic_unit="decompose the remaining calculation step",
            depth=2,
            parent_id=parent.id,
        )
        state.register_node(current, parent_id=parent.id)

        future_certain = self.make_child(
            node_id="node-future-certain",
            semantic_unit="future sibling that should not appear",
            depth=2,
            parent_id=parent.id,
        )
        state.register_node(future_certain, parent_id=parent.id)
        state.certainty[future_certain.id] = ThreeLevel.HIGH
        state.status[future_certain.id] = NodeStatus.CLOSED

        return controller, parent, prior_certain, current, future_certain

    def test_prior_certain_sibling_context_only_includes_earlier_certain_siblings(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing prior certain sibling context only includes earlier certain siblings.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_prior_certain_sibling_context_only_includes_earlier_certain_siblings()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller, _, prior_certain, current, future_certain = self.build_controller_with_siblings()

        siblings = controller.decomposition_certain_sibling_context_payload(current)

        self.assertEqual([item["id"] for item in siblings], [prior_certain.id])
        self.assertNotIn(future_certain.id, [item["id"] for item in siblings])

    def test_decomposition_prompt_includes_parent_and_prior_certain_siblings_only(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing decomposition prompt includes parent and prior certain siblings only.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_decomposition_prompt_includes_parent_and_prior_certain_siblings_only()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller, parent, prior_certain, current, future_certain = self.build_controller_with_siblings()
        captured: dict[str, str] = {}

        def fake_request_proposal(**kwargs):
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake request proposal.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

            Example Input Output:
                Input: `fake_request_proposal()`
                Output: 'F = m * a'

            Args:
                **kwargs: Additional keyword arguments forwarded by the caller.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            captured["instructions"] = kwargs["instructions"]
            return ProposalObject(
                id="proposal-decompose",
                proposal_type=ProposalType.NOT_DECOMPOSITION,
                target_scope=current.semantic_unit,
                originating_not_id=current.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "decompose_now": False,
                    "preserve_parent": True,
                    "preserve_reason": "test preserve",
                    "children": [],
                    "alternate_decompositions": [],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]

        controller.decompose_or_refine(current)

        instructions = captured["instructions"]
        self.assertIn("Parent overview:", instructions)
        self.assertIn(parent.semantic_unit, instructions)
        self.assertIn("Prior certain siblings:", instructions)
        self.assertIn(prior_certain.semantic_unit, instructions)
        self.assertIn("Root-local title namespace:", instructions)
        self.assertIn(future_certain.semantic_unit, instructions)


if __name__ == "__main__":
    unittest.main()
