# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from main import (
    BSSCController,
    BoundaryShapeTerm,
    ClosureRule,
    DecompositionMode,
    PriorityLevel,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposalType,
    SupplementMode,
    SystemState,
    normalize_boundary_shape,
)


class BoundaryShapeTypingTests(unittest.TestCase):
    def test_bootstrap_root_has_default_boundary_shape(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing bootstrap root has default boundary shape.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_bootstrap_root_has_default_boundary_shape()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Answer the question.")
        self.assertEqual(
            tuple(atom.value for atom in state.root().boundary_shape),
            (BoundaryShapeTerm.OUTPUT_VALUE.value,),
        )

    def test_normalize_boundary_shape_accepts_prime_star_notation(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing normalize boundary shape accepts prime star notation.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_normalize_boundary_shape_accepts_prime_star_notation()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        shape = normalize_boundary_shape(["a*", "b'*", "d*"])
        self.assertEqual(
            tuple(atom.value for atom in shape),
            (
                BoundaryShapeTerm.INPUT_VALUE.value,
                BoundaryShapeTerm.READ_REFERENCE.value,
                BoundaryShapeTerm.OUTPUT_VALUE.value,
            ),
        )

    def test_decomposition_child_uses_explicit_boundary_shape(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing decomposition child uses explicit boundary shape.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_decomposition_child_uses_explicit_boundary_shape()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Solve the task.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.boundary_shape = normalize_boundary_shape(["a*", "d*"])

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
            return ProposalObject(
                id="proposal-explicit-shape",
                proposal_type=ProposalType.NOT_DECOMPOSITION,
                target_scope=root.semantic_unit,
                originating_not_id=root.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "decompose_now": True,
                    "preserve_parent": False,
                    "children": [
                        {
                            "semantic_unit": "read the referenced dataset",
                            "description": "Pull the needed data in.",
                            "boundary_shape": ["b'*", "d*"],
                            "decomposition_mode": DecompositionMode.AND.value,
                            "closure_threshold": ClosureRule.NORMAL.value,
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": PriorityLevel.MEDIUM.value,
                        }
                    ],
                    "alternate_decompositions": [],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        children = controller.decompose_or_refine(root)
        self.assertEqual(len(children), 1)
        self.assertEqual(
            tuple(atom.value for atom in children[0].boundary_shape),
            (BoundaryShapeTerm.READ_REFERENCE.value, BoundaryShapeTerm.OUTPUT_VALUE.value),
        )

    def test_decomposition_child_inherits_parent_boundary_shape_when_unspecified(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing decomposition child inherits parent boundary shape when unspecified.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_decomposition_child_inherits_parent_boundary_shape_when_unspecified()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Solve the task.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.boundary_shape = normalize_boundary_shape(["a*", "c*", "d*"])

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
            return ProposalObject(
                id="proposal-inherit-shape",
                proposal_type=ProposalType.NOT_DECOMPOSITION,
                target_scope=root.semantic_unit,
                originating_not_id=root.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "decompose_now": True,
                    "preserve_parent": False,
                    "children": [
                        {
                            "semantic_unit": "carry out the remaining transformation",
                            "description": "Continue the same boundary contract.",
                            "decomposition_mode": DecompositionMode.AND.value,
                            "closure_threshold": ClosureRule.NORMAL.value,
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": PriorityLevel.MEDIUM.value,
                        }
                    ],
                    "alternate_decompositions": [],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        children = controller.decompose_or_refine(root)
        self.assertEqual(len(children), 1)
        self.assertEqual(
            tuple(atom.value for atom in children[0].boundary_shape),
            tuple(atom.value for atom in root.boundary_shape),
        )

    def test_bootstrap_root_infers_write_boundary_for_send_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing bootstrap root infers write boundary for send prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_bootstrap_root_infers_write_boundary_for_send_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Send an email to recipient='alice@example.com' message='hi'.")
        self.assertEqual(
            tuple(atom.value for atom in state.root().boundary_shape),
            (
                BoundaryShapeTerm.INPUT_VALUE.value,
                BoundaryShapeTerm.WRITE_VALUE.value,
                BoundaryShapeTerm.OUTPUT_VALUE.value,
            ),
        )

    def test_bootstrap_root_infers_read_reference_boundary_for_path_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing bootstrap root infers read reference boundary for path prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_bootstrap_root_infers_read_reference_boundary_for_path_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Read the greeting from path='/tmp/greeting.txt'.")
        self.assertEqual(
            tuple(atom.value for atom in state.root().boundary_shape),
            (
                BoundaryShapeTerm.INPUT_REFERENCE.value,
                BoundaryShapeTerm.READ_REFERENCE.value,
                BoundaryShapeTerm.OUTPUT_VALUE.value,
            ),
        )


if __name__ == "__main__":
    unittest.main()
