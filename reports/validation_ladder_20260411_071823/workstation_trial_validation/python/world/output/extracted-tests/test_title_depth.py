# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    BSSCController,
    BoundaryShapeTerm,
    ClosureRule,
    DecompositionMode,
    LearningRelation,
    NodeStatus,
    NodeOrigin,
    PriorityLevel,
    ProposalGovernanceStatus,
    ProposalObject,
    ProposalType,
    SemanticNode,
    SupplementMode,
    SystemState,
    SupportScore,
    SupportView,
    ThreeLevel,
    artifact_structured_learning_from_content,
    classify_title_depth_relation,
    derive_semantic_title_depth_view,
    normalize_not_elaboration_payload,
)
from prompt_directives import semantic_prompt_directive_profile
from semantic_text import semantic_requested_output_phrases


def make_title_depth_artifact(*, artifact_id: str, title: str, question: str, answer: str) -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating title depth artifact.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `make_title_depth_artifact(artifact_id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', question='Compute force from mass and acceleration.', answer='F = m * a')`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        artifact_id: Value for `artifact_id` used by `make_title_depth_artifact`. Expected type: `str`.
        title: Value for `title` used by `make_title_depth_artifact`. Expected type: `str`.
        question: Value for `question` used by `make_title_depth_artifact`. Expected type: `str`.
        answer: Value for `answer` used by `make_title_depth_artifact`. Expected type: `str`.

    Returns:
        Artifact: Result produced by `make_title_depth_artifact`.
    """
    return Artifact(
        id=artifact_id,
        artifact_type=ArtifactType.KNOWLEDGE,
        title=title,
        representation=ArtifactRepresentation.YAML,
        function_bit=0,
        scope="test title-depth reuse",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content={
            "question": question,
            "answer": answer,
        },
        justification="test artifact",
        boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
    )


def make_imported_style_title_depth_ability(
    *,
    artifact_id: str,
    title: str,
    question: str,
    answer: str,
) -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over imported executable workers whose stored structured-learning title is shallower than the artifact display title, helps with creating an imported-style title-depth ability artifact.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

    Example Input Output:
        Input: `make_imported_style_title_depth_ability(artifact_id='artifact-area', title='Cylinder Measures / Total Surface Area Of A Cylinder', question='How do you calculate A from r and h?', answer='A = 2πr(r + h).')`
        Output: Artifact(id='artifact-area', title='Cylinder Measures / Total Surface Area Of A Cylinder', artifact_type='ability', representation='python_script')

    Args:
        artifact_id: Value for `artifact_id` used by `make_imported_style_title_depth_ability`. Expected type: `str`.
        title: Value for `title` used by `title`. Expected type: `str`.
        question: Value for `question` used by `question`. Expected type: `str`.
        answer: Value for `answer` used by `answer`. Expected type: `str`.

    Returns:
        Artifact: Result produced by `make_imported_style_title_depth_ability`.
    """
    return Artifact(
        id=artifact_id,
        artifact_type=ArtifactType.ABILITY,
        title=title,
        representation=ArtifactRepresentation.PYTHON_SCRIPT,
        function_bit=1,
        scope="test imported title-depth ability",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content={
            "question": question,
            "answer": answer,
            "input_contract": {"r": "radius", "h": "height"},
            "output_contract": {"A": "total surface area"},
            "structured_learning": {
                "title_identity": "Total Surface Area Of A Cylinder",
                "title_depth_segments": ["Total Surface Area Of A Cylinder"],
                "title_depth_prefixes": ["Total Surface Area Of A Cylinder"],
                "title_depth_exposed_depth": 1,
                "title_depth_minimal_sufficient_depth": 1,
                "title_depth_assessment": "surface_unsegmented",
                "title_depth_reuse_bias": "ground_reuse",
                "goal": question,
            },
            "python_script": "def run(r, h):\n    return {'A': 2 * 3.14159 * r * (r + h)}\n",
        },
        justification="test imported-style ability",
        boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
    )


class TitleDepthTests(unittest.TestCase):
    def test_split_results_prompt_is_constructive_and_extracts_requested_outputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like title-depth validation for compound prompts, helps with testing split results prompt is constructive and extracts requested outputs.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_split_results_prompt_is_constructive_and_extracts_requested_outputs()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."

        directive = semantic_prompt_directive_profile(prompt)
        requested_outputs = semantic_requested_output_phrases(prompt)

        self.assertEqual(directive["kind"], "construct")
        self.assertTrue(directive["requires_chain"])
        self.assertEqual(
            requested_outputs,
            ["total surface area", "volume"],
        )

    def test_derive_semantic_title_depth_view_builds_ordered_prefix_chain(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing derive semantic title depth view builds ordered prefix chain.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_derive_semantic_title_depth_view_builds_ordered_prefix_chain()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        view = derive_semantic_title_depth_view(
            "Physics / Newtons Second Law / Force From Mass And Acceleration"
        )

        self.assertEqual(
            view["segments"],
            [
                "Physics",
                "Newtons Second Law",
                "Force From Mass And Acceleration",
            ],
        )
        self.assertEqual(
            view["prefixes"],
            [
                "Physics",
                "Physics / Newtons Second Law",
                "Physics / Newtons Second Law / Force From Mass And Acceleration",
            ],
        )
        self.assertEqual(view["exposed_depth"], 3)

    def test_normalized_not_elaboration_derives_title_depth_from_formal_title_identity(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing normalized not elaboration derives title depth from formal title identity.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_normalized_not_elaboration_derives_title_depth_from_formal_title_identity()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        normalized = normalize_not_elaboration_payload(
            "Calculate force for mass=3 and acceleration=4.",
            {
                "goal": "Calculate force for mass=3 and acceleration=4.",
                "title_identity": "Physics / Newtons Second Law / Force From Mass And Acceleration",
            },
            title_identity="Physics / Newtons Second Law / Force From Mass And Acceleration",
        )

        self.assertEqual(
            normalized["title_depth_segments"],
            [
                "Physics",
                "Newtons Second Law",
                "Force From Mass And Acceleration",
            ],
        )
        self.assertEqual(
            normalized["title_identity"],
            "Physics / Newtons Second Law / Force From Mass And Acceleration",
        )
        self.assertEqual(normalized["goal"], "Calculate force for mass=3 and acceleration=4.")

    def test_artifact_structured_learning_uses_artifact_title_as_identity_source(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing artifact structured learning uses artifact title as identity source.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_artifact_structured_learning_uses_artifact_title_as_identity_source()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = make_title_depth_artifact(
            artifact_id="artifact-force",
            title="Physics / Newtons Second Law / Force From Mass And Acceleration",
            question="Calculate force for mass=3 and acceleration=4.",
            answer="12",
        )

        structured = artifact_structured_learning_from_content(artifact)

        self.assertEqual(
            structured["title_identity"],
            "Physics / Newtons Second Law / Force From Mass And Acceleration",
        )
        self.assertEqual(
            structured["title_depth_prefixes"][-1],
            "Physics / Newtons Second Law / Force From Mass And Acceleration",
        )
        self.assertEqual(structured["title_identity"], structured["goal"])
        self.assertTrue(
            any("mass" in key or "acceleration" in key for key in structured["lookup_keys"]),
        )

    def test_title_depth_relation_prefers_exact_identity_over_ground_prefix(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing title depth relation prefers exact identity over ground prefix.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_title_depth_relation_prefers_exact_identity_over_ground_prefix()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("title depth selection"), llm_policy="off")
        exact = make_title_depth_artifact(
            artifact_id="artifact-exact",
            title="Physics / Newtons Second Law / Force From Mass And Acceleration",
            question="Calculate force for mass=3 and acceleration=4.",
            answer="12",
        )
        ground = make_title_depth_artifact(
            artifact_id="artifact-ground",
            title="Physics / Newtons Second Law",
            question="Use Newtons second law.",
            answer="Force equals mass times acceleration.",
        )

        query = "Physics / Newtons Second Law / Force From Mass And Acceleration"
        exact_rank = controller.answer_candidate_rank(
            exact,
            semantic_unit=query,
            current_boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
        )
        ground_rank = controller.answer_candidate_rank(
            ground,
            semantic_unit=query,
            current_boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
        )

        self.assertLess(exact_rank, ground_rank)
        self.assertEqual(
            classify_title_depth_relation(query, ground.title)[0],
            "prior_is_ground_prefix",
        )

    def test_decomposition_prompt_carries_title_depth_prior(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing decomposition prompt carries title depth prior.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_decomposition_prompt_carries_title_depth_prior()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics / Newtons Second Law / Force From Mass And Acceleration")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        node = SemanticNode(
            id="node-title-depth",
            semantic_unit="Physics / Newtons Second Law / Force From Mass And Acceleration",
            role="generic",
            description="Decompose the force relation only if a real body-level split is needed.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(node, parent_id=root.id)
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
            if kwargs["proposal_type"] == ProposalType.NOT_ELABORATION:
                return ProposalObject(
                    id="proposal-title-depth-elaboration",
                    proposal_type=ProposalType.NOT_ELABORATION,
                    target_scope=node.semantic_unit,
                    originating_not_id=node.id,
                    mode=SupplementMode.FAST,
                    prompt_state_reference="test",
                    revision_count=0,
                    governance_status=ProposalGovernanceStatus.SUGGESTED,
                    payload={
                        "title_identity": node.semantic_unit,
                        "encountered_not": "Force From Mass And Acceleration",
                        "goal": node.semantic_unit,
                        "title_depth_minimal_sufficient_depth": 3,
                        "title_depth_assessment": "adequate_segmentation",
                        "title_depth_body_split_needed": False,
                        "title_depth_body_split_reason": "preserve the full determinate identity",
                        "title_depth_reuse_bias": "determinate_reuse",
                        "title_depth_hidden_depth_note": "hidden depth may remain beyond the exposed title",
                        "component_nots": ["Mass Input", "Acceleration Input"],
                        "composed_not": "Force From Mass And Acceleration",
                        "lookup_keys": ["force from mass and acceleration"],
                    },
                    source="heuristic",
                )
            captured["instructions"] = kwargs["instructions"]
            return ProposalObject(
                id="proposal-title-depth",
                proposal_type=ProposalType.NOT_DECOMPOSITION,
                target_scope=node.semantic_unit,
                originating_not_id=node.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "decompose_now": False,
                    "preserve_parent": True,
                    "preserve_reason": "keep the semantic unit whole",
                    "children": [],
                    "alternate_decompositions": [],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        controller.decompose_or_refine(node)

        instructions = captured["instructions"]
        self.assertIn("Title-depth prior:", instructions)
        self.assertIn("Force From Mass And Acceleration", instructions)
        self.assertIn("Physics / Newtons Second Law", instructions)
        self.assertIn("title_depth_anchor_prefix", instructions)
        self.assertIn("namespace_rationale", instructions)

    def test_ensure_not_elaboration_grounds_split_results_prompt_in_reusable_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like title-depth validation for split-result prompts over learned reusable families, helps with testing ensure not elaboration grounds split results prompt in reusable family.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_ensure_not_elaboration_grounds_split_results_prompt_in_reusable_family()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Geometry / Cylinder Measures",
            question="What is cylinder measures?",
            answer="A cylinder family groups reusable measures.",
        )
        state.learned_artifacts["artifact-cylinder-area"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-area",
            title="Geometry / Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate total surface area of a cylinder?",
            answer="A = 2πr(r + h)",
        )
        state.learned_artifacts["artifact-cylinder-volume"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-volume",
            title="Geometry / Cylinder Measures / Volume Of A Cylinder",
            question="How do you calculate volume of a cylinder?",
            answer="V = πr^2h",
        )
        root = state.root()

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
                id="proposal-title-depth-family-grounding",
                proposal_type=ProposalType.NOT_ELABORATION,
                target_scope=root.semantic_unit,
                originating_not_id=root.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "title_identity": root.semantic_unit,
                    "encountered_not": "Cylinder Surface Area And Volume",
                    "goal": root.semantic_unit,
                    "title_depth_minimal_sufficient_depth": 1,
                    "title_depth_assessment": "surface_unsegmented",
                    "title_depth_body_split_needed": False,
                    "title_depth_reuse_bias": "ground_reuse",
                    "component_nots": [],
                    "composed_not": "Cylinder Surface Area And Volume",
                    "lookup_keys": ["cylinder", "total surface area", "volume"],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        structured = controller.ensure_not_elaboration(root)

        self.assertEqual(structured["title_identity"], "Geometry / Cylinder Measures")
        self.assertEqual(
            structured["component_nots"],
            ["Total Surface Area Of A Cylinder", "Volume Of A Cylinder"],
        )
        self.assertTrue(structured["title_depth_body_split_needed"])

    def test_shared_reusable_family_title_requires_actual_common_parentage(self) -> None:
        """
        High Level Purpose:
            In circumstances like title-depth family grounding across multiple learned namespaces, helps with proving that family lifting only uses the actual common slash prefix of the matched titles.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_shared_reusable_family_title_requires_actual_common_parentage()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("family title"), llm_policy="off")

        family_title = controller.shared_reusable_family_title(
            [
                "Geometry / Cylinder Measures / Volume Of A Cylinder",
                "Statistics / Distribution Measures / Volume Of A Distribution",
            ]
        )

        self.assertEqual(family_title, "")

    def test_shared_reusable_family_title_resolves_unique_extended_parentage(self) -> None:
        """
        High Level Purpose:
            In circumstances like store-backed title-depth family grounding from partially anchored determinate titles, helps with proving that the shared family is lifted only through one unique structural extension path in the reusable store.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_shared_reusable_family_title_resolves_unique_extended_parentage()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("family title unique extension")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-cylinder-area"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-area",
            title="Geometry / Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate total surface area of a cylinder?",
            answer="A = 2πr(r + h)",
        )
        state.learned_artifacts["artifact-cylinder-volume"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-volume",
            title="Geometry / Cylinder Measures / Volume Of A Cylinder",
            question="How do you calculate volume of a cylinder?",
            answer="V = πr^2h",
        )

        family_title = controller.shared_reusable_family_title(
            [
                "Cylinder Measures / Total Surface Area Of A Cylinder",
                "Cylinder Measures / Volume Of A Cylinder",
            ]
        )

        self.assertEqual(family_title, "Geometry / Cylinder Measures")

    def test_shared_reusable_family_title_refuses_ambiguous_extended_parentage(self) -> None:
        """
        High Level Purpose:
            In circumstances like store-backed title-depth family grounding where multiple namespaces provide the same leaf-family extension path, helps with proving that family lifting refuses the ambiguity instead of choosing one namespace heuristically.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_shared_reusable_family_title_refuses_ambiguous_extended_parentage()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("family title ambiguous extension")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-geometry-area"] = make_title_depth_artifact(
            artifact_id="artifact-geometry-area",
            title="Geometry / Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate total surface area of a cylinder?",
            answer="A = 2πr(r + h)",
        )
        state.learned_artifacts["artifact-geometry-volume"] = make_title_depth_artifact(
            artifact_id="artifact-geometry-volume",
            title="Geometry / Cylinder Measures / Volume Of A Cylinder",
            question="How do you calculate volume of a cylinder?",
            answer="V = πr^2h",
        )
        state.learned_artifacts["artifact-manufacturing-area"] = make_title_depth_artifact(
            artifact_id="artifact-manufacturing-area",
            title="Manufacturing / Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate total surface area of a cylinder?",
            answer="A = 2πr(r + h)",
        )
        state.learned_artifacts["artifact-manufacturing-volume"] = make_title_depth_artifact(
            artifact_id="artifact-manufacturing-volume",
            title="Manufacturing / Cylinder Measures / Volume Of A Cylinder",
            question="How do you calculate volume of a cylinder?",
            answer="V = πr^2h",
        )

        family_title = controller.shared_reusable_family_title(
            [
                "Cylinder Measures / Total Surface Area Of A Cylinder",
                "Cylinder Measures / Volume Of A Cylinder",
            ]
        )

        self.assertEqual(family_title, "")

    def test_shared_reusable_family_title_refuses_unique_leaf_only_family_guess(self) -> None:
        """
        High Level Purpose:
            In circumstances like partially anchored determinate titles that share only one broad family leaf token, helps with proving that family lifting does not guess a parent family solely because the reusable pool contains one matching leaf-family artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_shared_reusable_family_title_refuses_unique_leaf_only_family_guess()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("family title single segment guess")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Geometry concepts / Cylinder Measures",
            question="What is cylinder measures?",
            answer="Cylinder measures names the reusable family.",
        )

        family_title = controller.shared_reusable_family_title(
            [
                "Cylinder Measures / Total Surface Area Of A Cylinder",
                "Cylinder Measures / Volume Of A Cylinder",
            ]
        )

        self.assertEqual(family_title, "")

    def test_best_reusable_title_for_phrase_uses_governing_context(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result prompts whose leaf outputs exist in multiple learned families, helps with proving that governing prompt context keeps the reusable title match inside the correct family.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_best_reusable_title_for_phrase_uses_governing_context()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("context-aware title match")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-cylinder-volume"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-volume",
            title="Geometry / Cylinder Measures / Volume Of A Cylinder",
            question="How do you calculate volume of a cylinder?",
            answer="V = πr^2h",
        )
        state.learned_artifacts["artifact-sphere-volume"] = make_title_depth_artifact(
            artifact_id="artifact-sphere-volume",
            title="Geometry / Sphere Measures / Volume Of A Sphere",
            question="How do you calculate volume of a sphere?",
            answer="V = 4/3 πr^3",
        )

        matched_title = controller.best_reusable_title_for_phrase(
            "volume",
            semantic_context="for a cylinder with radius=3 and height=5",
        )

        self.assertEqual(matched_title, "Geometry / Cylinder Measures / Volume Of A Cylinder")

    def test_best_reusable_title_for_phrase_ignores_structured_learning_record_titles(self) -> None:
        """
        High Level Purpose:
            In circumstances like live reusable pools that contain both family titles and structured-learning record artifacts, helps with proving that family grounding ignores the record titles instead of mistaking them for reusable determinate identities.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_best_reusable_title_for_phrase_ignores_structured_learning_record_titles()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("structured learning record title match")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-structured-record"] = make_title_depth_artifact(
            artifact_id="artifact-structured-record",
            title="Structured learning record for Break Thi Down Carefully Need Cylinder With Radiu 3 Height 5 Give Me Total Surface Area Volume Separate Result",
            question="What was the prior structured learning record?",
            answer="A prior structured learning record exists.",
        )
        state.learned_artifacts["artifact-cylinder-area"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-area",
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate total surface area of a cylinder?",
            answer="A = 2πr(r + h)",
        )

        matched_title = controller.best_reusable_title_for_phrase(
            "total surface area",
            semantic_context="for a cylinder with radius=3 and height=5",
        )

        self.assertEqual(matched_title, "Cylinder Measures / Total Surface Area Of A Cylinder")

    def test_artifact_structured_learning_view_prefers_deeper_artifact_title_over_leaf_only_structured_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like imported executable workers whose stored structured-learning view only preserves the terminal leaf identity, helps with proving that reuse view recovery restores the deeper artifact title before matching.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_artifact_structured_learning_view_prefers_deeper_artifact_title_over_leaf_only_structured_title()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("artifact structured view depth recovery")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_imported_style_title_depth_ability(
            artifact_id="artifact-imported-area",
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate A from r and h?",
            answer="A = 2πr(r + h).",
        )

        structured = controller.artifact_structured_learning_view(artifact)

        self.assertEqual(
            structured["title_identity"],
            "Cylinder Measures / Total Surface Area Of A Cylinder",
        )
        self.assertEqual(
            structured["title_depth_prefixes"],
            [
                "Cylinder Measures",
                "Cylinder Measures / Total Surface Area Of A Cylinder",
            ],
        )

    def test_classify_structured_learning_match_treats_underanchored_suffix_leaf_as_encountered_before(self) -> None:
        """
        High Level Purpose:
            In circumstances like title-depth child reuse against imported workers whose stored title omits the broader ground but preserves the determinate suffix path, helps with proving that exact suffix alignment is treated as encountered-before rather than mere decomposition-related support.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_classify_structured_learning_match_treats_underanchored_suffix_leaf_as_encountered_before()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        controller = BSSCController(SystemState.bootstrap("suffix child match"), llm_policy="off")
        current = {
            "title_identity": "Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            "title_depth_reuse_bias": "determinate_reuse",
        }
        prior = {
            "title_identity": "Cylinder Measures / Total Surface Area Of A Cylinder",
        }

        match_kind = controller.classify_structured_learning_match(current, prior)

        self.assertEqual(match_kind, "encountered_before")

    def test_canonicalize_child_semantic_title_ignores_broader_reused_prefix(self) -> None:
        """
        High Level Purpose:
            In circumstances like title-depth child decomposition over a store-backed reusable corpus, helps with proving that child canonicalization does not collapse a body-level child back to a broader reused family prefix.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_canonicalize_child_semantic_title_ignores_broader_reused_prefix()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("title depth child canonicalization")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-cylinder-root"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-root",
            title="Cylinder geometry",
            question="Cylinder geometry family.",
            answer="family",
        )
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Cylinder geometry / Cylinder Measures",
            question="Cylinder measures family.",
            answer="family",
        )

        child_title = controller.canonicalize_child_semantic_title(
            parent_title="Cylinder geometry / Cylinder Measures",
            proposed_title="Total Surface Area Of A Cylinder",
            prefer_store_reuse=True,
            exclude_titles=[
                "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results.",
                "Cylinder geometry / Cylinder Measures",
                "Total Surface Area Of A Cylinder",
                "Volume Of A Cylinder",
            ],
        )

        self.assertEqual(
            child_title,
            "Cylinder geometry / Cylinder Measures / Total Surface Area Of A Cylinder",
        )

    def test_canonicalize_child_semantic_title_preserves_directive_bearing_leaf(self) -> None:
        """
        High Level Purpose:
            In circumstances like deterministic chemistry chain decomposition over a store-backed reusable corpus, helps with proving that child canonicalization does not weaken an explicit directive-bearing leaf such as `Express How To ...` back to a looser reusable `Compute ...` title.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_canonicalize_child_semantic_title_preserves_directive_bearing_leaf()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("title depth directive canonicalization")
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts["artifact-chemistry-family"] = make_title_depth_artifact(
            artifact_id="artifact-chemistry-family",
            title="Chemistry Relations 03 — Mass to Mole Conversion / Chemistry Relations 03 Mass to Mole Conversion",
            question="Mass to mole conversion family.",
            answer="family",
        )
        state.learned_artifacts["artifact-chemistry-compute"] = make_title_depth_artifact(
            artifact_id="artifact-chemistry-compute",
            title="Chemistry Relations 03 — Mass to Mole Conversion / Chemistry Relations 03 Mass to Mole Conversion / Compute Mass From Moles And Molar Mass",
            question="Compute mass from moles and molar mass.",
            answer="m = n * M",
        )

        child_title = controller.canonicalize_child_semantic_title(
            parent_title="Chemistry Relations 03 — Mass to Mole Conversion / Chemistry Relations 03 Mass to Mole Conversion",
            proposed_title="Express How To Compute Mass From Moles And Molar Mass",
            prefer_store_reuse=True,
            exclude_titles=[
                "Chemistry Relations 03 — Mass to Mole Conversion / Chemistry Relations 03 Mass to Mole Conversion",
                "Compute Mass From Moles And Molar Mass",
            ],
        )

        self.assertEqual(
            child_title,
            "Chemistry Relations 03 — Mass to Mole Conversion / Chemistry Relations 03 Mass to Mole Conversion / Express How To Compute Mass From Moles And Molar Mass",
        )

    def test_not_elaboration_prompt_carries_theory_and_root_local_namespace(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing not elaboration prompt carries theory and root local namespace.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_not_elaboration_prompt_carries_theory_and_root_local_namespace()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics / Newtons Second Law / Force From Mass And Acceleration")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
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
                id="proposal-not-title-depth",
                proposal_type=ProposalType.NOT_ELABORATION,
                target_scope=root.semantic_unit,
                originating_not_id=root.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "title_identity": root.semantic_unit,
                    "encountered_not": "Force From Mass And Acceleration",
                    "goal": root.semantic_unit,
                    "title_depth_minimal_sufficient_depth": 3,
                    "title_depth_assessment": "adequate_segmentation",
                    "title_depth_body_split_needed": False,
                    "title_depth_body_split_reason": "the title is already determinate enough",
                    "title_depth_reuse_bias": "determinate_reuse",
                    "title_depth_hidden_depth_note": "hidden depth may still exceed exposed depth",
                    "component_nots": ["Mass Input", "Acceleration Input"],
                    "composed_not": "Force From Mass And Acceleration",
                    "lookup_keys": ["force from mass and acceleration"],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        normalized = controller.ensure_not_elaboration(root)

        instructions = captured["instructions"]
        self.assertIn("Title-depth law (infer from the formal title and context; it is never explicitly specified):", instructions)
        self.assertIn("Derived title-depth context:", instructions)
        self.assertIn("Root-local title namespace:", instructions)
        self.assertNotIn("Namespace guardrails:", instructions)
        self.assertIn(root.semantic_unit, instructions)
        self.assertEqual(normalized["title_identity"], root.semantic_unit)

    def test_not_elaboration_anchors_title_under_parent_when_llm_returns_local_identity(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing not elaboration anchors title under parent when llm returns local identity.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_not_elaboration_anchors_title_under_parent_when_llm_returns_local_identity()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        parent = SemanticNode(
            id="node-parent-title-anchor",
            semantic_unit="Physics / Newtons Second Law",
            role="generic",
            description="Parent physics law identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(parent, parent_id=root.id)
        child = SemanticNode(
            id="node-child-title-anchor",
            semantic_unit="Force From Mass And Acceleration",
            role="generic",
            description="Child reduction that should be anchored under the parent title.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=2,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=parent.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=parent.id)

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
                id="proposal-anchor-current-title",
                proposal_type=ProposalType.NOT_ELABORATION,
                target_scope=child.semantic_unit,
                originating_not_id=child.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "title_identity": "Force From Mass And Acceleration",
                    "encountered_not": "Force From Mass And Acceleration",
                    "goal": child.semantic_unit,
                    "title_depth_minimal_sufficient_depth": 1,
                    "title_depth_assessment": "adequate_segmentation",
                    "component_nots": ["Mass", "Acceleration"],
                    "composed_not": "Force From Mass And Acceleration",
                    "lookup_keys": ["force from mass and acceleration"],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        normalized = controller.ensure_not_elaboration(child)
        self.assertEqual(
            normalized["title_identity"],
            "Physics / Newtons Second Law / Force From Mass And Acceleration",
        )

    def test_not_elaboration_canonicalizes_component_nots_with_store_reuse_and_parent_anchor(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing not elaboration canonicalizes component nots with store reuse and parent anchor.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_not_elaboration_canonicalizes_component_nots_with_store_reuse_and_parent_anchor()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        parent = SemanticNode(
            id="node-parent-component-anchor",
            semantic_unit="Physics / Newtons Second Law",
            role="generic",
            description="Parent physics law identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(parent, parent_id=root.id)
        child = SemanticNode(
            id="node-child-component-anchor",
            semantic_unit="Force From Mass And Acceleration",
            role="generic",
            description="Child reduction with semantic components.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=2,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=parent.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=parent.id)
        reused_mass = make_title_depth_artifact(
            artifact_id="artifact-reused-mass-component",
            title="Physics / Newtons Second Law / Force From Mass And Acceleration / Mass",
            question="What is the mass input?",
            answer="m",
        )

        def fake_load_relevant_artifacts(_semantic_unit: str, *, limit: int = 8):
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake load relevant artifacts.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

            Example Input Output:
                Input: `fake_load_relevant_artifacts(_semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
                Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

            Args:
                _semantic_unit: Value for `_semantic_unit` used by `fake_load_relevant_artifacts`. Expected type: `str`.
                limit: Value for `limit` used by `fake_load_relevant_artifacts`. Expected type: `int`. Defaults to `8`.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            return [reused_mass]

        controller.artifact_store.load_relevant_artifacts = fake_load_relevant_artifacts  # type: ignore[method-assign]

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
                id="proposal-anchor-component-titles",
                proposal_type=ProposalType.NOT_ELABORATION,
                target_scope=child.semantic_unit,
                originating_not_id=child.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "title_identity": "Force From Mass And Acceleration",
                    "encountered_not": "Force From Mass And Acceleration",
                    "goal": child.semantic_unit,
                    "title_depth_minimal_sufficient_depth": 1,
                    "title_depth_assessment": "adequate_segmentation",
                    "component_nots": ["Mass", "Acceleration"],
                    "composed_not": "Force From Mass And Acceleration",
                    "lookup_keys": ["force from mass and acceleration"],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        normalized = controller.ensure_not_elaboration(child)
        self.assertEqual(
            normalized["component_nots"],
            [
                "Physics / Newtons Second Law / Force From Mass And Acceleration / Mass",
                "Physics / Newtons Second Law / Force From Mass And Acceleration / Acceleration",
            ],
        )

    def test_root_local_title_namespace_uses_parent_structured_title_not_prompt_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like child title-depth elaboration beneath a prompt-surface root, helps with testing root local title namespace uses parent structured title not prompt surface.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_root_local_title_namespace_uses_parent_structured_title_not_prompt_surface()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": "Geometry concepts / Cylinder Measures",
        }
        child = SemanticNode(
            id="node-child-title-namespace",
            semantic_unit="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            role="generic",
            description="Child cylinder area identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        payload = controller.root_local_title_namespace_payload(child)

        self.assertEqual(payload["parent_title_identity"], "Geometry concepts / Cylinder Measures")
        self.assertEqual(payload["root_title_identity"], "Geometry concepts / Cylinder Measures")

    def test_resolve_root_local_title_identity_keeps_already_anchored_child_title(self) -> None:
        """
        High Level Purpose:
            In circumstances like child title-depth elaboration under a structured parent family, helps with testing resolve root local title identity keeps already anchored child title.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_resolve_root_local_title_identity_keeps_already_anchored_child_title()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": "Geometry concepts / Cylinder Measures",
        }
        child = SemanticNode(
            id="node-child-resolve-title",
            semantic_unit="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            role="generic",
            description="Child cylinder area identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        resolved = controller.resolve_root_local_title_identity(
            node=child,
            proposed_title="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
        )

        self.assertEqual(resolved, "Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder")

    def test_refine_directly_generic_child_can_reuse_aligned_title_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like decomposed title-depth children under a learned family, helps with testing refine directly generic child can reuse aligned title artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refine_directly_generic_child_can_reuse_aligned_title_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": "Geometry concepts / Cylinder Measures",
        }
        child = SemanticNode(
            id="node-child-generic-reuse",
            semantic_unit="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            role="generic",
            description="Child cylinder area identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)
        state.learned_artifacts["artifact-cylinder-area-knowledge"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-area-knowledge",
            title="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            question="What is the total surface area of a cylinder?",
            answer="A = 2πr(r + h).",
        )

        controller.refine_directly(child)

        self.assertTrue(child.metadata.get("direct_refined"))
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(
            child.metadata.get("structured_learning_lookup", {}).get("match_kind"),
            "encountered_before",
        )

    def test_refine_directly_generic_child_prefers_imported_leaf_ability_over_broader_family_support(self) -> None:
        """
        High Level Purpose:
            In circumstances like live imported title-depth stores where the broader family is a knowledge artifact but the determinate child answer lives in an executable imported worker, helps with proving that the child closes through the leaf worker rather than stopping on broader family support.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_refine_directly_generic_child_prefers_imported_leaf_ability_over_broader_family_support()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": "Geometry concepts / Cylinder Measures",
        }
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Geometry concepts / Cylinder Measures",
            question="What does cylinder measures refer to?",
            answer="Cylinder measures is the reusable family for area and volume formulas.",
        )
        state.learned_artifacts["artifact-cylinder-area-imported"] = make_imported_style_title_depth_ability(
            artifact_id="artifact-cylinder-area-imported",
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate A from r and h?",
            answer="A = 2πr(r + h).",
        )
        child = SemanticNode(
            id="node-child-imported-generic-reuse",
            semantic_unit="Geometry concepts / Cylinder Measures / Total Surface Area Of A Cylinder",
            role="generic",
            description="Child cylinder area identity.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        controller.refine_directly(child)

        self.assertTrue(child.metadata.get("direct_refined"))
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(
            child.metadata.get("structured_learning_lookup", {}).get("match_kind"),
            "encountered_before",
        )

    def test_refine_directly_generic_prompt_local_child_reuses_matching_determinate_leaf(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result children that still carry a prompt-local broader prefix, helps with proving that exact determinate leaf equality is enough to reuse the matching learned child artifact without heuristic family lifting.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_refine_directly_generic_prompt_local_child_reuses_matching_determinate_leaf()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": prompt,
            "title_depth_body_split_needed": True,
            "title_depth_reuse_bias": "determinate_reuse",
            "component_nots": ["Total Surface Area Of A Cylinder", "Volume Of A Cylinder"],
        }
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Cylinder Measures",
            question="What does cylinder measures refer to?",
            answer="Cylinder measures is the reusable family for area and volume formulas.",
        )
        state.learned_artifacts["artifact-cylinder-area-imported"] = make_imported_style_title_depth_ability(
            artifact_id="artifact-cylinder-area-imported",
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            question="How do you calculate A from r and h?",
            answer="A = 2πr(r + h).",
        )
        child = SemanticNode(
            id="node-child-prompt-local-determinate-reuse",
            semantic_unit=f"{prompt} / Total Surface Area Of A Cylinder",
            role="generic",
            description="Prompt-local split child.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        controller.refine_directly(child)

        self.assertTrue(child.metadata.get("direct_refined"))
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(
            child.metadata.get("structured_learning_lookup", {}).get("match_kind"),
            "encountered_before",
        )

    def test_lookup_prior_non_achievedness_prefers_exact_split_child_leaf_over_broad_family_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result children where a broad family answer and an exact determinate leaf answer coexist in the learned pool, helps with proving that the governed reuse path picks the exact child leaf rather than the broader family explanation.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_lookup_prior_non_achievedness_prefers_exact_split_child_leaf_over_broad_family_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": prompt,
            "title_depth_body_split_needed": True,
            "title_depth_reuse_bias": "determinate_reuse",
            "component_nots": ["Total Surface Area Of A Cylinder", "Volume Of A Cylinder"],
        }
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Mathematics / Geometric Measurements / Cylinder Measures",
            question="What are cylinder measures?",
            answer="Total surface area and volume are related cylinder measures but should stay separate when asked separately.",
        )
        state.learned_artifacts["artifact-cylinder-area"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-area",
            title="Cylinder Measures / Total Surface Area Of A Cylinder",
            question="What is the total surface area of a cylinder?",
            answer="150.79644737231007",
        )
        state.learned_artifacts["artifact-cylinder-volume"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-volume",
            title="Cylinder Measures / Volume Of A Cylinder",
            question="What is the volume of a cylinder?",
            answer="141.3716694115407",
        )
        child = SemanticNode(
            id="node-child-prompt-local-volume-leaf",
            semantic_unit=f"{prompt} / Volume Of A Cylinder",
            role="generic",
            description="Prompt-local split child.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        lookup = controller.lookup_prior_non_achievedness(child)

        self.assertEqual(
            lookup["answer_artifact"].id,
            "artifact-cylinder-volume",
        )
        self.assertIn(
            lookup["answer_preference"],
            {"same_key", "same_not", "encountered_before", "related_key"},
        )

        controller.refine_directly(child)

        self.assertIn("141.3716694115407", str(child.metadata.get("direct_resolution_answer", "")))
        self.assertEqual(
            child.metadata.get("structured_learning", {}).get("title_identity"),
            "Cylinder Measures / Volume Of A Cylinder",
        )
        self.assertEqual(
            child.metadata.get("structured_learning", {}).get("title_depth_prefixes"),
            ["Cylinder Measures", "Cylinder Measures / Volume Of A Cylinder"],
        )

    def test_refine_directly_split_child_prefers_executable_leaf_result_over_broad_family_prose(self) -> None:
        """
        High Level Purpose:
            In circumstances like live split-result reuse where the exact leaf artifact is executable but the broader family prose is also focus-aligned, helps with proving that the child closes from the executable leaf result rather than being flattened back into family narration.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_refine_directly_split_child_prefers_executable_leaf_result_over_broad_family_prose()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["not_elaboration"] = {
            "encountered_not": "Cylinder surface area and volume",
            "goal": prompt,
            "title_identity": prompt,
            "title_depth_body_split_needed": True,
            "title_depth_reuse_bias": "determinate_reuse",
            "component_nots": ["Total Surface Area Of A Cylinder", "Volume Of A Cylinder"],
        }
        state.learned_artifacts["artifact-cylinder-family"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-family",
            title="Mathematics / Geometric Measurements / Cylinder Measures",
            question="What is Cylinder Measures?",
            answer="For a cylinder with radius r and height h, total surface area is 2πr(r+h) and volume is πr²h.",
        )
        state.learned_artifacts["artifact-cylinder-distinguish"] = make_title_depth_artifact(
            artifact_id="artifact-cylinder-distinguish",
            title="Cylinder Measures",
            question="What is 4. Distinguishing the measures?",
            answer="These two calculations are related but not the same: If a prompt asks for both, keep them separate instead of collapsing them into one quantity.",
        )
        state.learned_artifacts["artifact-cylinder-volume-imported"] = Artifact(
            id="artifact-cylinder-volume-imported",
            artifact_type=ArtifactType.ABILITY,
            title="Cylinder Measures / Volume Of A Cylinder",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="test imported title-depth ability",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate V from r, h?",
                "answer": "141.3716694115407",
                "input_contract": {"r": "radius", "h": "height"},
                "output_contract": {"V": "number"},
                "structured_learning": {
                    "title_identity": "Volume Of A Cylinder",
                    "title_depth_segments": ["Volume Of A Cylinder"],
                    "title_depth_prefixes": ["Volume Of A Cylinder"],
                    "title_depth_exposed_depth": 1,
                    "title_depth_minimal_sufficient_depth": 1,
                    "title_depth_assessment": "surface_unsegmented",
                    "title_depth_reuse_bias": "ground_reuse",
                    "goal": "How do you calculate V from r, h?",
                },
                "python_script": """# /// script
# dependencies = ["msgspec", "orjson"]
import math
import sys

import msgspec
import orjson


class InputPayload(msgspec.Struct, kw_only=True):
    payload: dict[str, float]


class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, float]
    notes: list[str] = []


def run(payload: InputPayload) -> OutputPayload:
    r = float(payload.payload.get("r", 0))
    h = float(payload.payload.get("h", 0))
    value = math.pi * r * r * h
    return OutputPayload(status="ok", answer=str(value), result={"V": value})


if __name__ == "__main__":
    raw = sys.stdin.buffer.read()
    payload = orjson.loads(raw) if raw else {}
    typed_input = msgspec.convert({"payload": payload}, type=InputPayload)
    result = run(typed_input)
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result), option=orjson.OPT_INDENT_2))
""",
            },
            justification="test imported volume ability",
            boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
        )
        child = SemanticNode(
            id="node-child-executable-volume",
            semantic_unit=f"{prompt} / Volume Of A Cylinder",
            role="generic",
            description="Prompt-local split child.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(child, parent_id=root.id)

        controller.refine_directly(child)

        answer = str(child.metadata.get("direct_resolution_answer", ""))
        self.assertIn("141.3716694115407", answer)
        self.assertNotIn("keep them separate", answer.lower())

    def test_commit_closure_materializes_split_root_answer_and_family_title_from_children(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result root closure after both child leaves have already closed, helps with proving that the committed root product carries the shared family title and a composed answer instead of an empty root answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_commit_closure_materializes_split_root_answer_and_family_title_from_children()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Break this down carefully if needed: for a cylinder with radius=3 and height=5, give me the total surface area and the volume as separate results."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.metadata["structured_learning"] = {
            "title_identity": prompt,
            "title_depth_body_split_needed": True,
            "title_depth_prefixes": [prompt],
            "title_depth_minimal_sufficient_depth": 1,
        }
        root.metadata["not_elaboration"] = dict(root.metadata["structured_learning"])
        area_child = SemanticNode(
            id="node-root-area-child",
            semantic_unit=f"{prompt} / Total Surface Area Of A Cylinder",
            role="generic",
            description="Area child.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        area_child.metadata["structured_learning"] = {
            "title_identity": "Geometry / Cylinder Measures / Total Surface Area Of A Cylinder",
        }
        area_child.metadata["direct_resolution_answer"] = "150.79644737231007"
        volume_child = SemanticNode(
            id="node-root-volume-child",
            semantic_unit=f"{prompt} / Volume Of A Cylinder",
            role="generic",
            description="Volume child.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.HIGH,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        volume_child.metadata["structured_learning"] = {
            "title_identity": "Geometry / Cylinder Measures / Volume Of A Cylinder",
        }
        volume_child.metadata["direct_resolution_answer"] = "141.3716694115407"
        state.register_node(area_child, parent_id=root.id)
        state.register_node(volume_child, parent_id=root.id)
        state.closed.update({area_child.id, volume_child.id})
        state.status[area_child.id] = NodeStatus.CLOSED
        state.status[volume_child.id] = NodeStatus.CLOSED
        state.support[root.id] = SupportView(direct=[], upstream=[], score=SupportScore.OK)
        state.certainty[root.id] = ThreeLevel.HIGH

        controller.commit_closure(root)

        structured = root.metadata.get("structured_learning", {})
        self.assertEqual(
            structured.get("title_identity"),
            "Geometry / Cylinder Measures",
        )
        self.assertEqual(
            structured.get("title_depth_prefixes"),
            ["Geometry", "Geometry / Cylinder Measures"],
        )
        product = next(product for product in state.products.values() if product.node_id == root.id)
        answer = str(product.content.get("answer", ""))
        self.assertIn("150.79644737231007", answer)
        self.assertIn("141.3716694115407", answer)

    def test_decomposition_rejects_namespace_collisions_and_prefix_restatements(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing decomposition rejects namespace collisions and prefix restatements.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_decomposition_rejects_namespace_collisions_and_prefix_restatements()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics / Newtons Second Law / Force From Mass And Acceleration")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        node = SemanticNode(
            id="node-title-depth-collision",
            semantic_unit="Physics / Newtons Second Law / Force From Mass And Acceleration",
            role="generic",
            description="Split only if a body-level refinement is materially distinct.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(node, parent_id=root.id)

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
            if kwargs["proposal_type"] == ProposalType.NOT_ELABORATION:
                return ProposalObject(
                    id="proposal-title-depth-collision-elaboration",
                    proposal_type=ProposalType.NOT_ELABORATION,
                    target_scope=node.semantic_unit,
                    originating_not_id=node.id,
                    mode=SupplementMode.FAST,
                    prompt_state_reference="test",
                    revision_count=0,
                    governance_status=ProposalGovernanceStatus.SUGGESTED,
                    payload={
                        "title_identity": node.semantic_unit,
                        "encountered_not": "Force From Mass And Acceleration",
                        "goal": node.semantic_unit,
                        "title_depth_minimal_sufficient_depth": 3,
                        "title_depth_assessment": "adequate_segmentation",
                        "title_depth_body_split_needed": True,
                        "title_depth_body_split_reason": "a body-level split may be useful if the children stay distinct",
                        "title_depth_reuse_bias": "determinate_reuse",
                        "title_depth_hidden_depth_note": "hidden depth may remain beyond the exposed title",
                        "component_nots": ["Mass Input", "Acceleration Input"],
                        "composed_not": "Force From Mass And Acceleration",
                        "lookup_keys": ["force from mass and acceleration"],
                    },
                    source="heuristic",
                )
            return ProposalObject(
                id="proposal-title-depth-collision",
                proposal_type=ProposalType.NOT_DECOMPOSITION,
                target_scope=node.semantic_unit,
                originating_not_id=node.id,
                mode=SupplementMode.FAST,
                prompt_state_reference="test",
                revision_count=0,
                governance_status=ProposalGovernanceStatus.SUGGESTED,
                payload={
                    "decompose_now": True,
                    "preserve_parent": False,
                    "children": [
                        {
                            "semantic_unit": "Physics / Newtons Second Law",
                            "description": "bad prefix restatement",
                            "boundary_shape": ["d*"],
                            "decomposition_mode": "and",
                            "closure_threshold": "normal",
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": "medium",
                            "title_depth_anchor_prefix": "Physics / Newtons Second Law",
                            "namespace_rationale": "bad",
                        },
                        {
                            "semantic_unit": "Mass Input",
                            "description": "reserved collision",
                            "boundary_shape": ["a*"],
                            "decomposition_mode": "and",
                            "closure_threshold": "normal",
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": "medium",
                            "title_depth_anchor_prefix": "Physics / Newtons Second Law / Force From Mass And Acceleration",
                            "namespace_rationale": "bad",
                        },
                        {
                            "semantic_unit": "Acceleration Input",
                            "description": "nearby artifact collision",
                            "boundary_shape": ["a*"],
                            "decomposition_mode": "and",
                            "closure_threshold": "normal",
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": "medium",
                            "title_depth_anchor_prefix": "Physics / Newtons Second Law / Force From Mass And Acceleration",
                            "namespace_rationale": "bad",
                        },
                        {
                            "semantic_unit": "Combine Confirmed Inputs Into Force",
                            "description": "valid body-level split",
                            "boundary_shape": ["a*", "d*"],
                            "decomposition_mode": "and",
                            "closure_threshold": "normal",
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": "high",
                            "title_depth_anchor_prefix": "Physics / Newtons Second Law / Force From Mass And Acceleration",
                            "namespace_rationale": "distinct body-level work under the full title identity",
                        },
                        {
                            "semantic_unit": "Combine Confirmed Inputs Into Force",
                            "description": "duplicate sibling",
                            "boundary_shape": ["a*", "d*"],
                            "decomposition_mode": "and",
                            "closure_threshold": "normal",
                            "evidence_required": False,
                            "required": True,
                            "priority_bias": "high",
                            "title_depth_anchor_prefix": "Physics / Newtons Second Law / Force From Mass And Acceleration",
                            "namespace_rationale": "duplicate",
                        },
                    ],
                    "alternate_decompositions": [],
                },
                source="heuristic",
            )

        controller.request_proposal = fake_request_proposal  # type: ignore[method-assign]
        children = controller.decompose_or_refine(node)

        self.assertEqual(len(children), 1)
        self.assertEqual(
            children[0].semantic_unit,
            "Physics / Newtons Second Law / Force From Mass And Acceleration / Combine Confirmed Inputs Into Force",
        )
        self.assertEqual(
            children[0].metadata["title_depth_anchor_prefix"],
            "Physics / Newtons Second Law / Force From Mass And Acceleration",
        )
        self.assertEqual(
            children[0].metadata["namespace_rationale"],
            "distinct body-level work under the full title identity",
        )

    def test_build_artifact_from_payload_adds_semantic_input_output_titles(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing build artifact from payload adds semantic input output titles.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to THEORY.md section 8.8 on title-depth and decomposition.

        Example Input Output:
            Input: `test_build_artifact_from_payload_adds_semantic_input_output_titles()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Physics / Newtons Second Law / Force From Mass And Acceleration")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        node = SemanticNode(
            id="node-ability-io-title",
            semantic_unit="Physics / Newtons Second Law / Force From Mass And Acceleration",
            role="generic",
            description="Ability with semantic input and output titles.",
            decomposition_mode=DecompositionMode.AND,
            closure_threshold=ClosureRule.NORMAL,
            evidence_required=False,
            required=True,
            depth=1,
            priority_bias=PriorityLevel.MEDIUM,
            parent_id=root.id,
            origin=NodeOrigin.CONTROLLER,
        )
        state.register_node(node, parent_id=root.id)
        reused_input = make_title_depth_artifact(
            artifact_id="artifact-reused-mass",
            title="Physics / Newtons Second Law / Force From Mass And Acceleration / Mass",
            question="What is the mass input?",
            answer="m",
        )

        def fake_load_relevant_artifacts(_semantic_unit: str, *, limit: int = 8):
            """
            High Level Purpose:
                In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling fake load relevant artifacts.

            Reference to Theory:
                Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

            Example Input Output:
                Input: `fake_load_relevant_artifacts(_semantic_unit='Physics / Force / Force From Mass And Acceleration', limit=3)`
                Output: {'title': 'Physics / Force / Force From Mass And Acceleration', 'artifact_type': 'ability', 'representation': 'python'}

            Args:
                _semantic_unit: Value for `_semantic_unit` used by `fake_load_relevant_artifacts`. Expected type: `str`.
                limit: Value for `limit` used by `fake_load_relevant_artifacts`. Expected type: `int`. Defaults to `8`.

            Returns:
                Any: Result produced by this function; it may also be `None` for side-effect-driven helpers.
            """
            return [reused_input]

        controller.artifact_store.load_relevant_artifacts = fake_load_relevant_artifacts  # type: ignore[method-assign]
        artifact = controller.build_artifact_from_payload(
            node=node,
            payload={
                "artifact_type": "ability",
                "title": "Physics / Newtons Second Law / Force From Mass And Acceleration",
                "scope": "reuse when later prompts ask to compute force from mass and acceleration",
                "justification": "test ability payload",
                "content": {
                    "python_script": "def compute(mass, acceleration):\n    return mass * acceleration\n",
                    "input_contract": {"mass": "number", "acceleration": "number"},
                    "output_contract": {"force": "number"},
                },
            },
            provenance=[node.id],
        )
        self.assertIsNotNone(artifact)
        assert artifact is not None
        self.assertEqual(
            artifact.content.get("input_titles", {}).get("mass"),
            "Physics / Newtons Second Law / Force From Mass And Acceleration / Mass",
        )
        self.assertEqual(
            artifact.content.get("input_titles", {}).get("acceleration"),
            "Physics / Newtons Second Law / Force From Mass And Acceleration / Acceleration",
        )
        self.assertEqual(
            artifact.content.get("output_titles", {}).get("force"),
            "Physics / Newtons Second Law / Force From Mass And Acceleration / Force",
        )


if __name__ == "__main__":
    unittest.main()
