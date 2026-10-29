# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.prompt_directives import (
    semantic_prompt_directive_profile,
    semantic_question_focus_text,
)
from realized_core_engine.semantic_prompt_posture import (
    semantic_prompt_action_posture,
    semantic_prompt_prefers_direct_knowledge_answer,
    semantic_unit_allows_default_invocation_payload,
)
from realized_core_engine.state import SystemState
from realized_core_semantics.applied_model import Artifact, ArtifactType, Evidence
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
    ThreeLevel,
)
from realized_core_semantics.semantic_text import (
    semantic_named_input_keys,
    semantic_requested_output_keys,
)
from realized_core_engine.retrieval_ranking import artifact_focus_alignment_score
from realized_core_engine.store import SQLiteVectorArtifactStore


def make_knowledge_artifact(
    *,
    artifact_id: str,
    title: str,
    question: str,
    answer: str,
) -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating knowledge artifact.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `make_knowledge_artifact(artifact_id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', question='Compute force from mass and acceleration.', answer='F = m * a')`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
        artifact_id: Value for `artifact_id` used by `make_knowledge_artifact`. Expected type: `str`.
        title: Value for `title` used by `make_knowledge_artifact`. Expected type: `str`.
        question: Value for `question` used by `make_knowledge_artifact`. Expected type: `str`.
        answer: Value for `answer` used by `make_knowledge_artifact`. Expected type: `str`.

    Returns:
        Artifact: Result produced by `make_knowledge_artifact`.
    """
    return Artifact(
        id=artifact_id,
        artifact_type=ArtifactType.KNOWLEDGE,
        title=title,
        representation=ArtifactRepresentation.YAML,
        function_bit=0,
        scope="reuse for immediate next-step tablet safety questions",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content={
            "question": question,
            "answer": answer,
            "aliases": [question],
            "structured_learning": {
                "encountered_not": "Tablet Next Step",
                "lookup_keys": ["tablet next step", "tablet safety"],
                "component_nots": ["Tablet", "Next Step"],
                "composed_not": "Tablet Safety",
                "notation_yaml": "",
            },
        },
        justification="Reusable bounded tablet-safety guidance.",
    )


class ArtifactAnswerSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling setUp.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `setUp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.state = SystemState.bootstrap("tablet safety selection")
        self.controller = BSSCController(self.state, llm_policy="off")

    def test_ambiguous_tablet_prompt_prefers_caution_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing ambiguous tablet prompt prefers caution artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_ambiguous_tablet_prompt_prefers_caution_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution",
            title="Unknown tablet identification first",
            question="What should I do if I cannot tell which loose tablet is the right dose?",
            answer="Do not take any tablet until you identify the exact tablet from the label or imprint and confirm with a pharmacist or Poison Help.",
        )
        affirmative = make_knowledge_artifact(
            artifact_id="artifact-affirmative",
            title="Confirmed prescribed tablets",
            question="What should I do when the prescription clearly matches and the directions say take two now?",
            answer="Take the tablets as prescribed if the label and prescription directions match.",
        )

        prompt = "I have 2 tablets in my hand, 10 mg or 100 mg. What should I do next?"
        caution_rank = self.controller.answer_candidate_rank(
            caution,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        affirmative_rank = self.controller.answer_candidate_rank(
            affirmative,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(caution_rank, affirmative_rank)

    def test_confirmed_prescription_prompt_prefers_affirmative_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing confirmed prescription prompt prefers affirmative artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_confirmed_prescription_prompt_prefers_affirmative_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution",
            title="Unknown tablet identification first",
            question="What should I do if I cannot tell which loose tablet is the right dose?",
            answer="Do not take any tablet until you identify the exact tablet from the label or imprint and confirm with a pharmacist or Poison Help.",
        )
        affirmative = make_knowledge_artifact(
            artifact_id="artifact-affirmative",
            title="Confirmed prescribed tablets",
            question="What should I do when the prescription clearly matches and the directions say take two now?",
            answer="Take the tablets as prescribed if the label and prescription directions match.",
        )

        prompt = "My doctor told me to take 2 tablets now, and I have the sealed, labeled tablets that match the prescription. What should I do?"
        caution_rank = self.controller.answer_candidate_rank(
            caution,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        affirmative_rank = self.controller.answer_candidate_rank(
            affirmative,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(affirmative_rank, caution_rank)

    def test_urgent_symptom_prompt_prefers_emergency_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing urgent symptom prompt prefers emergency artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_urgent_symptom_prompt_prefers_emergency_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        ordinary = make_knowledge_artifact(
            artifact_id="artifact-ordinary",
            title="Dizziness without tablets in hand",
            question="What should I do if I feel dizzy and I am not holding any tablets?",
            answer="Sit or lie down, avoid driving, and seek medical advice promptly if the dizziness continues.",
        )
        urgent = make_knowledge_artifact(
            artifact_id="artifact-urgent",
            title="Unknown tablet with trouble breathing",
            question="What should I do if I took an unknown tablet and now have trouble breathing?",
            answer="Call emergency services now; trouble breathing after an unknown tablet is an emergency, and Poison Help can assist once emergency care is on the way.",
        )

        prompt = "I took an unknown tablet and now I have trouble breathing. What should I do?"
        ordinary_rank = self.controller.answer_candidate_rank(
            ordinary,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        urgent_rank = self.controller.answer_candidate_rank(
            urgent,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(urgent_rank, ordinary_rank)

    def test_urgent_unknown_tablet_prompt_penalizes_non_emergency_follow_up_guidance(self) -> None:
        """
        High Level Purpose:
            In circumstances like emergency tablet-safety routing where unknown-tablet prompts can mention both uncertainty and a red-flag symptom, helps with proving that concrete emergency guidance outranks lower-urgency follow-up guidance instead of being demoted by the generic uncertainty posture.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_urgent_unknown_tablet_prompt_penalizes_non_emergency_follow_up_guidance()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        follow_up = make_knowledge_artifact(
            artifact_id="artifact-follow-up",
            title="Unknown tablet already taken and now dizzy",
            question="What should I do if an unknown tablet may already have been swallowed and dizziness starts afterward?",
            answer="Call Poison Help in the United States: 1-800-222-1222, seek urgent medical guidance, and escalate further if severe symptoms appear.",
        )
        emergency = make_knowledge_artifact(
            artifact_id="artifact-emergency",
            title="Red-flag emergency symptoms after an unknown tablet",
            question="What should I do if I took an unknown tablet and now have trouble breathing?",
            answer="Call emergency services now; trouble breathing after an unknown tablet is an emergency, and Poison Help can assist once emergency care is on the way.",
        )

        prompt = "I took an unknown tablet and now I have trouble breathing. What should I do?"
        follow_up_rank = self.controller.answer_candidate_rank(
            follow_up,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        emergency_rank = self.controller.answer_candidate_rank(
            emergency,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(emergency_rank, follow_up_rank)

    def test_ordinal_prompt_does_not_reuse_generic_summary_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing ordinal prompt does not reuse generic summary answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_ordinal_prompt_does_not_reuse_generic_summary_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        summary = Artifact(
            id="artifact-newton-summary",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Newton's laws of motion",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for broad summaries of Newton's laws of motion",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What are Newton's laws of motion?",
                "answer": "First Law: inertia. Second Law: F = m * a. Third Law: equal and opposite reaction.",
                "aliases": ["Newton's laws of motion"],
                "structured_learning": {
                    "encountered_not": "Newton Laws Motion",
                    "lookup_keys": ["newton laws motion"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Broad summary artifact.",
        )
        specific = Artifact(
            id="artifact-newton-first-law",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="First law law of inertia",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for the first law specifically",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is Newton's first law of motion?",
                "answer": "An object remains at rest or in uniform motion unless acted on by an external force.",
                "aliases": ["Newton's first law of motion"],
                "structured_learning": {
                    "encountered_not": "Newton First Law Motion",
                    "lookup_keys": ["newton first law motion"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Specific first-law artifact.",
        )

        current = self.controller.structured_learning_view_for_text("What is Newton's first law of motion?")
        summary_prior = self.controller.artifact_structured_learning_view(summary)
        specific_prior = self.controller.artifact_structured_learning_view(specific)

        self.assertIsNone(self.controller.answer_reuse_preference(current, summary_prior, summary))
        summary_rank = self.controller.answer_candidate_rank(
            summary,
            semantic_unit="What is Newton's first law of motion?",
            current_boundary_shape=self.state.root().boundary_shape,
        )
        specific_rank = self.controller.answer_candidate_rank(
            specific,
            semantic_unit="What is Newton's first law of motion?",
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(specific_rank, summary_rank)

    def test_specific_prompt_prefers_focused_artifact_over_summary_section_variant(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing specific prompt prefers focused artifact over summary section variant.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_specific_prompt_prefers_focused_artifact_over_summary_section_variant()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        summary_variant = Artifact(
            id="artifact-newton-first-law-summary-variant",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Newton's Laws of Motion / First Law Objects Resist Changes In Motion",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for broad summary wording around Newton's laws of motion",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is Newton's first law of motion?",
                "answer": "First Law: Objects resist changes in motion. Second Law: Force determines acceleration. Third Law: Forces occur in pairs.",
                "aliases": ["Newton's first law of motion"],
                "source_sections": ["Summary"],
                "structured_learning": {
                    "title_identity": "Newton's Laws of Motion / First Law Objects Resist Changes In Motion",
                    "encountered_not": "Summary",
                    "goal": "What is Newton's first law of motion?",
                    "lookup_keys": ["newton first law motion", "summary"],
                    "component_nots": ["Newton Laws Motion"],
                    "composed_not": "Newton Laws Motion",
                    "action_posture": "direct_resolution",
                    "notation_yaml": "",
                },
            },
            justification="Summary-derived first-law variant.",
        )
        focused = Artifact(
            id="artifact-newton-first-law-focused",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Newton's Laws of Motion / First Law: Law of Inertia",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for the first law specifically",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is the first law in Newton's Laws of Motion?",
                "answer": "An object remains at rest or in uniform motion in a straight line unless acted upon by an external force.",
                "aliases": ["Newton's first law of motion", "law of inertia"],
                "source_sections": ["First Law: Law of Inertia", "Explanation"],
                "structured_learning": {
                    "title_identity": "Newton's Laws of Motion / First Law: Law of Inertia",
                    "encountered_not": "First Law Law Of Inertia",
                    "goal": "What is the first law in Newton's Laws of Motion?",
                    "lookup_keys": ["newton first law motion", "law of inertia"],
                    "component_nots": ["Newton Laws Motion"],
                    "composed_not": "Newton Laws Motion",
                    "action_posture": "direct_resolution",
                    "notation_yaml": "",
                },
            },
            justification="Focused first-law artifact.",
        )

        prompt = "What is Newton's first law of motion?"
        summary_rank = self.controller.answer_candidate_rank(
            summary_variant,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        focused_rank = self.controller.answer_candidate_rank(
            focused,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(focused_rank, summary_rank)

    def test_compute_prompt_prefers_compute_ready_ability_over_structured_learning_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a normal numeric prompt ranks a compute-ready learned ability ahead of a generic structured-learning record.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_prefers_compute_ready_ability_over_structured_learning_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        python_script = self.controller.expression_ability_script(
            title="Chemistry Relations 02 — Mole as Counting Conversion / Particles From Moles",
            scope="reuse when particle count should be computed from amount of substance and Avogadro's constant",
            input_contract={"n": "number", "N_A": "number"},
            output_contract={"N": "number"},
            expression="n * N_A",
            output_field="N",
        )
        ability = Artifact(
            id="artifact-chemistry-particles",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry Relations 02 — Mole as Counting Conversion / Particles From Moles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for particle-count calculations from moles and Avogadro's constant",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate N from n and N_A?",
                "formal_title_identity": "chemistry_relation_02_mole_as_counting_conversion:particles_from_moles(InputN, AvogadroConstant, ParticleCount) :- ParticleCount is InputN * AvogadroConstant",
                "compute_expression": "n * N_A",
                "output_field": "N",
                "input_contract": {"n": "number", "N_A": "number"},
                "output_contract": {"N": "number"},
                "parameter_aliases": {"n": ["moles"], "N_A": ["Avogadro constant"]},
                "python_script": python_script,
                "structured_learning": {
                    "encountered_not": "Particles From Moles",
                    "lookup_keys": ["particles from moles", "calculate n from n_a"],
                    "component_nots": ["n", "N_A", "N"],
                    "composed_not": "Particles From Moles",
                    "notation_yaml": "",
                },
            },
            justification="Compute-ready chemistry ability artifact.",
        )
        structured_record = Artifact(
            id="artifact-structured-chemistry",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Calculate N From N 2 And N A 3",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same chemistry prompt reappears under prior-encounter lookup",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Calculate N from n=2 and N_A=3.",
                "answer": "committed_state supports reduction of Not<Calculate N from n=2 and N_A=3.>",
                "structured_learning": {
                    "encountered_not": "Calculate N From N 2 And N A 3",
                    "lookup_keys": ["calculate n from n_a"],
                    "component_nots": ["Calculate N From N 2", "N A 3"],
                    "composed_not": "Calculate N From N 2 And N A 3",
                    "notation_yaml": "",
                },
            },
            justification="Generic structured-learning record that should not outrank the executable ability.",
        )
        prompt = "Calculate N from n=2 and N_A=3."
        ability_rank = self.controller.answer_candidate_rank(
            ability,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        record_rank = self.controller.answer_candidate_rank(
            structured_record,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(ability_rank, record_rank)

    def test_compute_prompt_lookup_prefers_output_compatible_ability_over_prior_structured_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a compute prompt selects the artifact whose output contract matches the requested quantity instead of reusing an unrelated prior structured-learning record.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_lookup_prefers_output_compatible_ability_over_prior_structured_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        python_script = self.controller.expression_ability_script(
            title="Chemistry Relations 08 — Ideal Gas State Relation / Pressure From Amount Temperature And Volume",
            scope="reuse when pressure should be computed from amount, gas constant, temperature, and volume",
            input_contract={"n": "number", "R": "number", "T": "number", "V": "number"},
            output_contract={"P": "number"},
            expression="n * R * T / V",
            output_field="P",
        )
        ability = Artifact(
            id="artifact-chemistry-pressure",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry Relations 08 — Ideal Gas State Relation / Pressure From Amount Temperature And Volume",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for ideal-gas pressure calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate P from n, R, T, and V?",
                "compute_expression": "n * R * T / V",
                "output_field": "P",
                "input_contract": {"n": "number", "R": "number", "T": "number", "V": "number"},
                "output_contract": {"P": "number"},
                "python_script": python_script,
                "structured_learning": {
                    "encountered_not": "Pressure From Amount Temperature And Volume",
                    "lookup_keys": ["pressure amount temperature volume", "calculate p from n r t v"],
                    "component_nots": ["n", "R", "T", "V", "P"],
                    "composed_not": "Pressure From Amount Temperature And Volume",
                    "notation_yaml": "",
                },
            },
            justification="Ideal-gas pressure ability artifact.",
        )
        structured_record = Artifact(
            id="artifact-structured-concentration",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Calculate C From N 0 5 And V 2",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same concentration prompt reappears under prior-encounter lookup",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Calculate C from n=0.5 and V=2.",
                "answer": "0.25",
                "structured_learning": {
                    "encountered_not": "Calculate C From N 0 5 And V 2",
                    "lookup_keys": ["calculate c from n v"],
                    "component_nots": ["C", "n", "V"],
                    "composed_not": "Calculate C From N 0 5 And V 2",
                    "notation_yaml": "",
                },
            },
            justification="Prior structured-learning residue from an unrelated concentration calculation.",
        )
        self.controller.state.learned_artifacts = {
            ability.id: ability,
            structured_record.id: structured_record,
        }
        node = self.state.root()
        node.semantic_unit = "Calculate P from n=2 and R=0.5 and T=3 and V=1."
        lookup = self.controller.lookup_prior_non_achievedness(node)
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, ability.id)

    def test_compute_prompt_distinguishes_exact_symbol_case_for_output_field(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic compute routing, helps with proving that the runtime does not collapse `N` and `n` into the same requested output when choosing between learned abilities.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_distinguishes_exact_symbol_case_for_output_field()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        particles_script = self.controller.expression_ability_script(
            title="Chemistry / Particles From Moles",
            scope="reuse for grouped counting",
            input_contract={"n": "number", "N_A": "number"},
            output_contract={"N": "number"},
            expression="n * N_A",
            output_field="N",
        )
        moles_script = self.controller.expression_ability_script(
            title="Chemistry / Moles From Particles",
            scope="reuse for inverse grouped counting",
            input_contract={"N": "number", "N_A": "number"},
            output_contract={"n": "number"},
            expression="N / N_A",
            output_field="n",
        )
        particles = Artifact(
            id="artifact-particles",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry / Particles From Moles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for grouped counting",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate N from n and N_A?",
                "compute_expression": "n * N_A",
                "output_field": "N",
                "input_contract": {"n": "number", "N_A": "number"},
                "output_contract": {"N": "number"},
                "python_script": particles_script,
                "structured_learning": {"encountered_not": "Particles From Moles", "lookup_keys": ["particles from moles"], "component_nots": ["n", "N_A", "N"], "composed_not": "Particles From Moles", "notation_yaml": ""},
            },
            justification="Particles from moles ability.",
        )
        moles = Artifact(
            id="artifact-moles",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry / Moles From Particles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for inverse grouped counting",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate n from N and N_A?",
                "compute_expression": "N / N_A",
                "output_field": "n",
                "input_contract": {"N": "number", "N_A": "number"},
                "output_contract": {"n": "number"},
                "python_script": moles_script,
                "structured_learning": {"encountered_not": "Moles From Particles", "lookup_keys": ["moles from particles"], "component_nots": ["N", "N_A", "n"], "composed_not": "Moles From Particles", "notation_yaml": ""},
            },
            justification="Moles from particles ability.",
        )
        prompt = "Calculate N from n=2 and N_A=3."
        particles_rank = self.controller.answer_candidate_rank(
            particles,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        moles_rank = self.controller.answer_candidate_rank(
            moles,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(particles_rank, moles_rank)

    def test_compute_prompt_exact_structured_record_does_not_beat_executable_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over repeated compute prompts persisted into the same store, helps with proving that an exact-question structured-learning record does not outrank a viable executable ability artifact for the same prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_exact_structured_record_does_not_beat_executable_ability()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        ohm_script = self.controller.expression_ability_script(
            title="Physics / Ohm S Law",
            scope="reuse for circuit current from voltage and resistance",
            input_contract={"V": "number", "R": "number"},
            output_contract={"I": "number"},
            expression="V / R",
            output_field="I",
        )
        ability = Artifact(
            id="artifact-ohm",
            artifact_type=ArtifactType.ABILITY,
            title="Physics / Ohm S Law",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for circuit current from voltage and resistance",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate I from V and R?",
                "compute_expression": "V / R",
                "output_field": "I",
                "input_contract": {"V": "number", "R": "number"},
                "output_contract": {"I": "number"},
                "python_script": ohm_script,
                "structured_learning": {
                    "encountered_not": "Ohm S Law",
                    "lookup_keys": ["calculate i from v r", "ohm law current"],
                    "component_nots": ["V", "R", "I"],
                    "composed_not": "Ohm S Law",
                    "notation_yaml": "",
                },
            },
            justification="Ohm law executable artifact.",
        )
        structured_record = Artifact(
            id="artifact-structured-current",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Calculate I From V 12 And R 4",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same current prompt reappears",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Calculate I from V=12 and R=4.",
                "answer": "AC is rac * ( 12 ** 2 ) * ( 4 )",
                "structured_learning": {
                    "encountered_not": "Calculate I From V 12 And R 4",
                    "lookup_keys": ["calculate i from v r"],
                    "component_nots": ["V", "R", "I"],
                    "composed_not": "Calculate I From V 12 And R 4",
                    "notation_yaml": "",
                },
            },
            justification="Persisted structured-learning residue from a prior bad compute run.",
        )
        self.controller.state.learned_artifacts = {
            structured_record.id: structured_record,
            ability.id: ability,
        }
        node = self.state.root()
        node.semantic_unit = "Calculate I from V=12 and R=4."
        lookup = self.controller.lookup_prior_non_achievedness(node)
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, ability.id)

    def test_compute_prompt_uses_title_leaf_output_phrase_for_speed_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over natural-language compute prompts, helps with proving that a title leaf such as `Speed From Distance And Time` contributes the output concept `speed` even when the raw output field is a noisier internal symbol.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_uses_title_leaf_output_phrase_for_speed_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        python_script = self.controller.expression_ability_script(
            title="Physics / Speed From Distance And Time",
            scope="reuse for speed calculations",
            input_contract={"d": "number", "t": "number"},
            output_contract={"ext_times_speed": "number"},
            expression="d / t",
            output_field="ext_times_speed",
        )
        speed = Artifact(
            id="artifact-speed",
            artifact_type=ArtifactType.ABILITY,
            title="Physics / Speed From Distance And Time",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for speed calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate ext_times_speed from d and t?",
                "compute_expression": "d / t",
                "output_field": "ext_times_speed",
                "input_contract": {"d": "number", "t": "number"},
                "output_contract": {"ext_times_speed": "number"},
                "python_script": python_script,
                "structured_learning": {"encountered_not": "Speed From Distance And Time", "lookup_keys": ["speed from distance and time"], "component_nots": ["d", "t"], "composed_not": "Speed From Distance And Time", "notation_yaml": ""},
            },
            justification="Speed ability.",
        )
        record = Artifact(
            id="artifact-speed-record",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Calculate Spe D 10 T 2",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for prior encounter residue",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Calculate speed from d=10 and t=2.",
                "answer": "committed_state supports reduction of Not<Calculate speed from d=10 and t=2.>",
                "structured_learning": {"encountered_not": "Calculate Speed", "lookup_keys": ["calculate speed"], "component_nots": ["d", "t"], "composed_not": "Calculate Speed", "notation_yaml": ""},
            },
            justification="Generic structured record.",
        )
        prompt = "Calculate speed from d=10 and t=2."
        speed_rank = self.controller.answer_candidate_rank(
            speed,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        record_rank = self.controller.answer_candidate_rank(
            record,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(speed_rank, record_rank)

    def test_compute_prompt_prefers_slanted_side_output_over_shorter_side_overlap(self) -> None:
        """
        High Level Purpose:
            In circumstances like natural-language geometry compute prompts that mention the slanted side or hypotenuse, helps with proving that output-quantity matching outranks a lexically noisy ability about one shorter side.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_compute_prompt_prefers_slanted_side_output_over_shorter_side_overlap()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        requested_keys = semantic_requested_output_keys(
            "Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each"
        )
        self.assertIn("slant side", requested_keys)
        slanted_script = self.controller.expression_ability_script(
            title="Pythagorean Theorem / Equal Side Special Case",
            scope="reuse for slanted side calculations from equal shorter sides",
            input_contract={"s": "number"},
            output_contract={"c": "number"},
            expression="( s ** 2 + s ** 2 ) ** 0.5",
            output_field="c",
        )
        shorter_script = self.controller.expression_ability_script(
            title="Pythagorean Theorem / The Triangle And The Side Roles",
            scope="reuse for the triangle-side-role relation",
            input_contract={"one": "number", "shorter": "number", "side": "number"},
            output_contract={"a": "number"},
            expression="one * shorter * side",
            output_field="a",
        )
        slanted = Artifact(
            id="artifact-pythagorean-slanted",
            artifact_type=ArtifactType.ABILITY,
            title="Pythagorean Theorem / Equal Side Special Case",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for slanted side calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "calculate the slanted side from the other two sides?",
                "compute_expression": "( s ** 2 + s ** 2 ) ** 0.5",
                "output_field": "c",
                "input_contract": {"s": "number"},
                "output_contract": {"c": "number"},
                "python_script": slanted_script,
            },
            justification="Slanted-side Pythagorean shortcut.",
        )
        shorter = Artifact(
            id="artifact-pythagorean-shorter",
            artifact_type=ArtifactType.ABILITY,
            title="Pythagorean Theorem / The Triangle And The Side Roles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for triangle side roles",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate a from one, shorter, side?",
                "compute_expression": "one * shorter * side",
                "output_field": "a",
                "input_contract": {"one": "number", "shorter": "number", "side": "number"},
                "output_contract": {"a": "number"},
                "python_script": shorter_script,
            },
            justification="A lexically overlapping but output-incompatible side-role artifact.",
        )
        prompt = "Calculate the length of the slanted side of a right angeled triangle if the other two sides are 5 metres each"
        slanted_rank = self.controller.answer_candidate_rank(
            slanted,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        shorter_rank = self.controller.answer_candidate_rank(
            shorter,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(slanted_rank, shorter_rank)

    def test_direct_knowledge_prompt_prefers_answer_bearing_knowledge_artifact_over_structured_record(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a direct explanatory question prefers a real knowledge artifact over a generic structured-learning record with matching surface wording.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_prompt_prefers_answer_bearing_knowledge_artifact_over_structured_record()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        knowledge = Artifact(
            id="artifact-mass-conservation",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 01 — Conservation of Amount / Mass Conservation Preserves Total Mass",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for introductory knowledge prompts about mass conservation in reactions",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is mass conservation in a reaction?",
                "answer": "Mass conservation means the total mass remains unchanged across a reaction when the full system is counted.",
                "aliases": ["mass conservation", "conservation of amount"],
                "structured_learning": {
                    "encountered_not": "Mass Conservation In A Reaction",
                    "lookup_keys": ["mass conservation reaction", "conservation of amount"],
                    "component_nots": ["Mass", "Conservation", "Reaction"],
                    "composed_not": "Mass Conservation",
                    "notation_yaml": "",
                },
            },
            justification="Actual chemistry knowledge artifact.",
        )
        structured_record = Artifact(
            id="artifact-structured-mass-conservation",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Mass Conservation Reaction",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same prompt reappears under prior-encounter lookup",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is mass conservation in a reaction?",
                "answer": "committed_state supports reduction of Not<What is mass conservation in a reaction?>",
                "structured_learning": {
                    "encountered_not": "Mass Conservation Reaction",
                    "lookup_keys": ["mass conservation reaction"],
                    "component_nots": ["Mass Conservation"],
                    "composed_not": "Mass Conservation Reaction",
                    "notation_yaml": "",
                },
            },
            justification="Generic structured-learning residue that should lose to the real knowledge artifact.",
        )
        self.controller.state.learned_artifacts = {
            knowledge.id: knowledge,
            structured_record.id: structured_record,
        }
        node = self.state.root()
        node.semantic_unit = "What is mass conservation in a reaction?"
        lookup = self.controller.lookup_prior_non_achievedness(node)
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, knowledge.id)

    def test_direct_knowledge_answer_composition_can_add_focus_and_supporting_clause(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over bare concept questions, helps with proving that the controller can compose a broader direct answer from one narrow artifact plus a supporting knowledge artifact instead of returning only the narrowest section fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_answer_composition_can_add_focus_and_supporting_clause()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        primary = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-io",
            title="Learn Biology: Photosynthesis Relations / Simplified input-output relation",
            question="What is Simplified input-output relation?",
            answer="Carbon dioxide + water + light -> glucose + oxygen.",
        )
        primary.content["source_title"] = "Learn Biology: Photosynthesis Relations"
        support = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-energy",
            title="Learn Biology: Cellular Respiration Relations / Energy conversion builds on transport and enzymes",
            question="What is Energy conversion builds on transport and enzymes?",
            answer="Stored chemical energy can later be made usable for cell work.",
        )
        support.content["source_title"] = "Learn Biology: Cellular Respiration Relations"
        composed = self.controller.compose_direct_knowledge_answer(
            semantic_unit="What is photosynthesis?",
            primary_artifact=primary,
            primary_answer=primary.content["answer"],
            focus_candidates=[primary],
        )
        self.assertIn("Photosynthesis", composed)
        self.controller.state.learned_artifacts = {
            primary.id: primary,
            support.id: support,
        }
        recomposed = self.controller.compose_direct_knowledge_answer(
            semantic_unit="What is photosynthesis?",
            primary_artifact=primary,
            primary_answer=primary.content["answer"],
            focus_candidates=[primary],
        )
        self.assertIn("Photosynthesis", recomposed)
        self.assertIn("chemical energy", recomposed.lower())

    def test_direct_knowledge_answer_can_use_latent_arrow_support_from_artifact_structure(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept questions whose best support artifact has no explicit answer field, helps with proving that the controller can recover a readable answer surface from stored givens and typed input-output structure.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_answer_can_use_latent_arrow_support_from_artifact_structure()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        primary = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-primary",
            title="Learn Biology: Photosynthesis Relations / Complementarity with respiration",
            question="What is Complementarity with respiration?",
            answer="Photosynthesis stores energy in glucose while respiration releases usable energy.",
        )
        support = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-io",
            title="Learn Biology: Photosynthesis Relations / Simplified input-output relation",
            question="What is Simplified input-output relation?",
            answer="Carbon dioxide + water + light -> glucose + oxygen.",
        )
        latent = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-latent",
            title="Learn Biology: Photosynthesis Relations / Biological Energy Can Also Be Stored",
            question="What is Biological energy can also be stored?",
            answer="",
        )
        latent.content.update(
            {
                "answer": "",
                "input_titles": {"light_energy": "Learn Biology: Photosynthesis Relations"},
                "output_titles": {
                    "stored_chemical_energy": "Learn Biology: Photosynthesis Relations / Biological Energy Can Also Be Stored / Stored Chemical Energy"
                },
                "relation_hint_texts": [
                    "Respiration described energy release.",
                    "Photosynthesis gives a complementary direction.",
                    "So:",
                ],
            }
        )
        latent.content["structured_learning"]["givens"] = [
            "So: light energy -> stored chemical energy"
        ]

        latent_answer = self.controller.artifact_answer_text(
            latent,
            semantic_unit="What is photosynthesis?",
        )
        self.assertIn("light energy", latent_answer.lower())
        self.assertIn("chemical energy", latent_answer.lower())

        recomposed = self.controller.compose_direct_knowledge_answer(
            semantic_unit="What is photosynthesis?",
            primary_artifact=primary,
            primary_answer=primary.content["answer"],
            focus_candidates=[primary, support, latent],
        )
        self.assertIn("chemical energy", recomposed.lower())

    def test_bare_concept_prompt_penalizes_complementarity_leaf(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept prompts, helps with proving that a comparative or complementarity leaf is penalized relative to a definition-like semantic leaf.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_penalizes_complementarity_leaf()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        complementarity = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-complementarity",
            title="Learn Biology: Photosynthesis Relations / Complementarity with respiration",
            question="What is Complementarity with respiration?",
            answer="Photosynthesis stores energy in glucose while respiration releases usable energy.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-photosynthesis-definition",
            title="Learn Biology: Photosynthesis Relations / Biological Energy Can Also Be Stored",
            question="What is Biological energy can also be stored?",
            answer="Light energy becomes stored chemical energy.",
        )

        prompt = "What is photosynthesis?"
        complement_rank = self.controller.answer_candidate_rank(
            complementarity,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(definition_rank, complement_rank)

    def test_bare_concept_prompt_penalizes_from_focus_to_other_bridge(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept prompts, helps with proving that a bridge artifact framed as `from X to Y` is demoted when the user asks for the meaning of `X` itself.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_penalizes_from_focus_to_other_bridge()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        bridge = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-bridge",
            title="Learn Biology: Inheritance Relations / From gene expression to inheritance",
            question="What is From gene expression to inheritance?",
            answer="Inheritance concerns how genetic information is transmitted across generations.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-definition",
            title="Learn Biology: Gene Expression Relations / Earlier information theory now becomes more precise",
            question="What is Earlier information theory now becomes more precise?",
            answer="Gene expression is the process by which information in DNA contributes to functional products.",
        )

        prompt = "What is gene expression?"
        bridge_rank = self.controller.answer_candidate_rank(
            bridge,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(definition_rank, bridge_rank)

    def test_direct_knowledge_candidates_can_pull_store_only_definition_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over prior-learning reuse, helps with proving that direct concept selection can recover a better persisted knowledge artifact from the store even when the initial in-memory learning context only loaded a worse bridge artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_candidates_can_pull_store_only_definition_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        bridge = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-bridge",
            title="Learn Biology: Inheritance Relations / From gene expression to inheritance",
            question="What is From gene expression to inheritance?",
            answer="Inheritance concerns how genetic information is transmitted across generations.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-definition",
            title="Learn Biology: Gene Expression Relations / Earlier information theory now becomes more precise",
            question="What is Earlier information theory now becomes more precise?",
            answer="Gene expression is the process by which information in DNA contributes to functional products.",
        )

        self.controller.state.learned_artifacts = {
            bridge.id: bridge,
        }
        self.controller.artifact_store = mock.Mock()
        self.controller.artifact_store.load_all_artifacts.return_value = [
            definition_like,
            bridge,
        ]

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit="What is gene expression?",
            current_boundary_shape=self.state.root().boundary_shape,
            include_unmatched_pool=True,
        )

        self.assertTrue(candidates)
        self.assertEqual(candidates[0][1].id, definition_like.id)

    def test_direct_knowledge_store_only_definition_can_close_runtime_support(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept reuse, helps with proving that a store-only focus-aligned definition artifact can still make the node closure-ready rather than remaining support-only.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_store_only_definition_can_close_runtime_support()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        bridge = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-bridge",
            title="Learn Biology: Inheritance Relations / From gene expression to inheritance",
            question="What is From gene expression to inheritance?",
            answer="Inheritance concerns how genetic information is transmitted across generations.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-gene-expression-definition",
            title="Learn Biology: Gene Expression Relations / Earlier information theory now becomes more precise",
            question="What is Earlier information theory now becomes more precise?",
            answer="Gene expression is the process by which information in DNA contributes to functional products.",
        )

        self.controller.state.learned_artifacts = {
            bridge.id: bridge,
        }
        self.controller.artifact_store = mock.Mock()
        self.controller.artifact_store.load_all_artifacts.return_value = [
            definition_like,
            bridge,
        ]

        node = self.state.root()
        node.semantic_unit = "What is gene expression?"
        used = self.controller.instantiate_reusable_artifact_support(node)

        self.assertTrue(used)
        self.assertTrue(node.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("dna", str(node.metadata.get("direct_resolution_answer", "")).lower())

    def test_bare_concept_prompt_prefers_definition_like_answer_over_relation_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept questions, helps with proving that a concept-bearing answer outranks a later relation fragment when the prompt asks for the concept itself rather than a derived relation.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_prefers_definition_like_answer_over_relation_fragment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-displacement-definition",
            title="Physics / Scalar Relations Do Not Preserve Direction",
            question="What is Scalar Relations Do Not Preserve Direction?",
            answer="Distance is not displacement, and displacement preserves direction.",
        )
        definition_like.content["source_title"] = "Physics Relations — Scalars and Vectors"
        relation_fragment = make_knowledge_artifact(
            artifact_id="artifact-displacement-relation",
            title="Physics / Velocity-displacement relation",
            question="What is Velocity-displacement relation?",
            answer="A time-eliminated kinematic law is v^2 = u^2 + 2as.",
        )
        relation_fragment.content["source_title"] = "Physics Relations — Linear Motion Under Constant Acceleration"
        prompt = "What is displacement?"
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        relation_rank = self.controller.answer_candidate_rank(
            relation_fragment,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        self.assertLess(definition_rank, relation_rank)

    def test_bare_concept_prompt_penalizes_compute_fragment_built_from_focus_term(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept prompts, helps with proving that a calculation-oriented artifact built from the focus term is demoted relative to a definition artifact for that focus.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_penalizes_compute_fragment_built_from_focus_term()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        compute_fragment = make_knowledge_artifact(
            artifact_id="artifact-displacement-compute-fragment",
            title="Physics / Velocity From Displacement And Time",
            question="How do you calculate v from displacement and time?",
            answer="Velocity From Displacement And Time. V.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-displacement-definition",
            title="Physics / Scalar Relations Do Not Preserve Direction",
            question="What is Scalar Relations Do Not Preserve Direction?",
            answer="Distance is not displacement, and displacement preserves direction.",
        )

        prompt = "What is displacement?"
        compute_rank = self.controller.answer_candidate_rank(
            compute_fragment,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(definition_rank, compute_rank)

    def test_bare_concept_prompt_penalizes_latent_title_only_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept prompts, helps with proving that a knowledge artifact with no explicit answer and only a title-derived latent surface is demoted relative to a real definition artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_penalizes_latent_title_only_fragment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        latent_fragment = Artifact(
            id="artifact-displacement-latent-fragment",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Physics / Work From Force And Displacement",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for work calculations from force and displacement",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate W from F and displacement?",
                "answer": "",
                "title_current_identity": "Work From Force And Displacement",
                "input_titles": {"force": "Physics / Force", "displacement": "Physics / Displacement"},
                "output_titles": {"work": "Physics / Work"},
                "structured_learning": {
                    "encountered_not": "Work From Force And Displacement",
                    "lookup_keys": ["work from force displacement"],
                    "component_nots": ["Force", "Displacement"],
                    "composed_not": "Work From Force And Displacement",
                    "notation_yaml": "",
                },
            },
            justification="Latent title-only work fragment.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-displacement-definition-latent-contrast",
            title="Physics / Scalar Relations Do Not Preserve Direction",
            question="What is Scalar Relations Do Not Preserve Direction?",
            answer="Distance is not displacement, and displacement preserves direction.",
        )

        prompt = "What is displacement?"
        latent_rank = self.controller.answer_candidate_rank(
            latent_fragment,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(definition_rank, latent_rank)

    def test_bare_concept_prompt_penalizes_executable_fragment_without_explanatory_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over direct concept prompts, helps with proving that an executable ability artifact with only a latent title surface is demoted relative to a non-executable definition artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_bare_concept_prompt_penalizes_executable_fragment_without_explanatory_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        python_script = self.controller.expression_ability_script(
            title="Physics / Work From Force And Displacement",
            scope="reuse for work calculations from force and displacement",
            input_contract={"F": "number", "d": "number"},
            output_contract={"W": "number"},
            expression="F * d",
            output_field="W",
        )
        executable_fragment = Artifact(
            id="artifact-displacement-executable-fragment",
            artifact_type=ArtifactType.ABILITY,
            title="Physics / Work From Force And Displacement",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for work calculations from force and displacement",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate W from F and displacement?",
                "answer": "",
                "python_script": python_script,
                "input_contract": {"F": "number", "d": "number"},
                "output_contract": {"W": "number"},
                "title_current_identity": "Work From Force And Displacement",
                "input_titles": {"force": "Physics / Force", "displacement": "Physics / Displacement"},
                "output_titles": {"work": "Physics / Work"},
                "structured_learning": {
                    "encountered_not": "Work From Force And Displacement",
                    "lookup_keys": ["work from force displacement"],
                    "component_nots": ["Force", "Displacement"],
                    "composed_not": "Work From Force And Displacement",
                    "notation_yaml": "",
                },
            },
            justification="Executable work fragment without a direct explanatory answer.",
        )
        definition_like = make_knowledge_artifact(
            artifact_id="artifact-displacement-definition-exec-contrast",
            title="Physics / Scalar Relations Do Not Preserve Direction",
            question="What is Scalar Relations Do Not Preserve Direction?",
            answer="Distance is not displacement, and displacement preserves direction.",
        )

        prompt = "What is displacement?"
        executable_rank = self.controller.answer_candidate_rank(
            executable_fragment,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        definition_rank = self.controller.answer_candidate_rank(
            definition_like,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(definition_rank, executable_rank)

    def test_direct_knowledge_prompt_can_reuse_broader_focus_aligned_knowledge_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that a direct explanatory question can still resolve through a broader answer-bearing knowledge artifact when no narrower classified reuse match exists.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_direct_knowledge_prompt_can_reuse_broader_focus_aligned_knowledge_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        broad_knowledge = Artifact(
            id="artifact-conservation-broad",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 01 Conservation of Amount / Conservation",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for introductory chemistry knowledge prompts about conserved quantities",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is conservation?",
                "answer": "Conservation is the broader reusable substrate; mass conservation in a reaction is the case where the total mass remains unchanged across the full counted system.",
                "aliases": ["mass conservation", "conservation of amount"],
                "structured_learning": {
                    "encountered_not": "Conservation",
                    "lookup_keys": ["conservation", "mass conservation", "conservation of amount"],
                    "component_nots": ["Conservation"],
                    "composed_not": "Conservation Of Amount",
                    "notation_yaml": "",
                },
            },
            justification="Broader chemistry knowledge artifact whose answer explicitly covers mass conservation in reactions.",
        )
        structured_record = Artifact(
            id="artifact-structured-mass-conservation-broad",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Structured learning record for Mass Conservation Reaction",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse when the same prompt reappears under prior-encounter lookup",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is mass conservation in a reaction?",
                "answer": "committed_state supports reduction of Not<What is mass conservation in a reaction?>",
                "structured_learning": {
                    "encountered_not": "Mass Conservation Reaction",
                    "lookup_keys": ["mass conservation reaction"],
                    "component_nots": ["Mass Conservation"],
                    "composed_not": "Mass Conservation Reaction",
                    "notation_yaml": "",
                },
            },
            justification="Generic structured-learning residue that should lose to the broader answer-bearing knowledge artifact.",
        )
        self.controller.state.learned_artifacts = {
            broad_knowledge.id: broad_knowledge,
            structured_record.id: structured_record,
        }
        node = self.state.root()
        node.semantic_unit = "What is mass conservation in a reaction?"
        lookup = self.controller.lookup_prior_non_achievedness(node)
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, broad_knowledge.id)
        self.assertEqual(lookup["answer_match_kind"], "focus_alignment")

    def test_lookup_keys_do_not_include_generic_remainder_boilerplate(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing lookup keys do not include generic remainder boilerplate.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_lookup_keys_do_not_include_generic_remainder_boilerplate()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        current = self.controller.structured_learning_view_for_text("What is Python scripting?")
        self.assertIn("python script", current["lookup_keys"])
        self.assertFalse(any("govern confidence" in key for key in current["lookup_keys"]))
        self.assertFalse(any("final realization" in key for key in current["lookup_keys"]))

    def test_generic_overlap_does_not_reuse_unrelated_definition_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing generic overlap does not reuse unrelated definition answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_generic_overlap_does_not_reuse_unrelated_definition_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        statistics = Artifact(
            id="artifact-statistics-definition",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Statistics",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for basic statistics definitions",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is statistics?",
                "answer": "Statistics is the science of collecting, organizing, analyzing, interpreting, and presenting data.",
                "aliases": ["statistics"],
                "structured_learning": {
                    "encountered_not": "Statistics",
                    "goal": "What is statistics?",
                    "lookup_keys": ["statistics"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Specific statistics definition.",
        )

        current = self.controller.structured_learning_view_for_text("What is Python scripting?")
        prior = self.controller.artifact_structured_learning_view(statistics)

        self.assertIsNone(self.controller.classify_structured_learning_match(current, prior))
        self.assertIsNone(self.controller.answer_reuse_preference(current, prior, statistics))

    def test_section_label_is_not_treated_as_named_input_assignment(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing section label is not treated as named input assignment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_section_label_is_not_treated_as_named_input_assignment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(semantic_named_input_keys("First Law: Law of Inertia"), [])

    def test_learning_context_query_variants_include_focus_and_compute_shape(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with proving that learning-context retrieval queries include direct knowledge focus phrases and compute-shaped output-from-input variants.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_learning_context_query_variants_include_focus_and_compute_shape()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        knowledge_variants = self.controller.learning_context_query_variants(
            "What is mass conservation in a reaction?"
        )
        self.assertIn("mass conservation in a reaction", [item.lower() for item in knowledge_variants])

        compute_variants = self.controller.learning_context_query_variants(
            "Calculate P from n=2 and R=0.5 and T=3 and V=1."
        )
        lowered_variants = [item.lower() for item in compute_variants]
        self.assertTrue(any("calculate p from n r t v" in item for item in lowered_variants))

    def test_derivation_prompt_directive_profile_and_focus_are_extracted(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over derivation-style prompts in the offline runtime path, helps with proving that prompt intent and focus extraction preserve the requested derivational posture instead of degrading into a generic compute request.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derivation_prompt_directive_profile_and_focus_are_extracted()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State Newton's second law and explain how it fits the multiplicative-combination substrate."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "state")
        self.assertEqual(semantic_question_focus_text(prompt), "Newton's second law")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))

    def test_state_prompt_focus_drops_relation_scaffolding(self) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side reuse for learned relation prompts, helps with proving that prompt focus extraction keeps the semantic nucleus instead of the literal scaffolding phrase.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_prompt_focus_drops_relation_scaffolding()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the relation that describes diffusion and explain the directional rule it follows."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "state")
        self.assertEqual(directive["focus_text"], "diffusion")
        self.assertEqual(semantic_question_focus_text(prompt), "diffusion")

    def test_state_formula_prompt_contextualizes_formula_role_components(self) -> None:
        """
        High Level Purpose:
            In circumstances like explanatory formula prompts that ask for the law plus variable-role explanation, helps with proving that generic component leaves such as `Input` and `Output Represent` are contextualized by the governing formula focus before retrieval.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_formula_prompt_contextualizes_formula_role_components()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the general conservation formula and explain what the inputs and outputs represent."
        node = self.state.root()
        node.semantic_unit = prompt

        structured = self.controller.ensure_not_elaboration(node)

        component_nots = structured["component_nots"]

        self.assertTrue(
            any(item.endswith("General Conservation Formula Input") for item in component_nots),
            component_nots,
        )
        self.assertTrue(
            any(item.endswith("General Conservation Formula Output Represent") for item in component_nots),
            component_nots,
        )
        self.assertFalse(any(item.endswith("/ Input") or item == "Input" for item in component_nots), component_nots)
        self.assertFalse(
            any(item.endswith("/ Output Represent") or item == "Output Represent" for item in component_nots),
            component_nots,
        )

    def test_construct_prompt_focus_keeps_pathway_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like controller-side reuse for composed pathway prompts, helps with proving that construct prompts keep the pathway family as focus instead of the entire literal chain suffix.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_construct_prompt_focus_keeps_pathway_family()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Construct the full signaling pathway from stimulus detection to response, and explain why receptor presence is necessary for signal effectiveness."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "construct")
        self.assertEqual(directive["focus_text"], "signaling pathway")
        self.assertEqual(semantic_question_focus_text(prompt), "signaling pathway")

    def test_using_relation_write_equation_prompt_is_classified(self) -> None:
        """
        High Level Purpose:
            In circumstances like state-plus-change controller prompts that refer to a governing relation before asking for the updated equation, helps with proving that directive extraction does not fall back to `none`.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_using_relation_write_equation_prompt_is_classified()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Using the constant-acceleration relation, write the equation that updates velocity from "
            "initial velocity, acceleration, and time, and identify the state-plus-change structure."
        )
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "state")
        self.assertIn("constant-acceleration", directive["focus_text"])
        self.assertIn("velocity", directive["focus_text"])
        self.assertTrue(directive["requires_formula"])
        self.assertTrue(directive["requires_substrate"])
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))
        self.assertEqual(semantic_prompt_action_posture(prompt), "direct_resolution")

    def test_construct_prompt_detects_combining_earlier_relations_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like explanatory composition prompts phrased as something being constructed by combining earlier relations, helps with proving that directive extraction classifies the prompt as construct rather than dropping it to `none`.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain how centripetal force is constructed by combining earlier relations for force and centripetal acceleration."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "construct")
        self.assertTrue(directive["requires_chain"])
        self.assertEqual(directive["focus_text"], "centripetal force")
        self.assertEqual(semantic_question_focus_text(prompt), "centripetal force")
        self.assertEqual(semantic_prompt_action_posture(prompt), "direct_resolution")

    def test_construct_prompt_focus_extracts_formula_family_before_chain_scaffolding(self) -> None:
        """
        High Level Purpose:
            In circumstances like formula-bearing construct prompts with explicit derivation scaffolding, helps with proving that directive focus extraction keeps the governing family instead of the whole literal chain request.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how electric power expressions ( P = VI ), ( P = I^2 R ), and ( P = V^2 / R ) are derived "
            "through composition of the driving-response relation and multiplicative combination. Provide the full reasoning chain."
        )
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "construct")
        self.assertTrue(directive["focus_text"].startswith("electric power expressions"))
        self.assertIn("P = I^2 R", directive["focus_text"])
        self.assertIn("P = V^2 / R", semantic_question_focus_text(prompt))

    def test_focus_alignment_accepts_partial_family_overlap_for_construct_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like construct prompts whose focus names a family plus a chain noun, helps with proving that retrieval can still admit family-local artifacts when they overlap on the governing family token.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_focus_alignment_accepts_partial_family_overlap_for_construct_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = make_knowledge_artifact(
            artifact_id="artifact-signaling",
            title="Learn Biology: Signaling and Nervous Control Relations / Receptor relation",
            question="What is Receptor relation?",
            answer="A signal has no biological effect merely by existing. It must be received.",
        )
        self.assertGreater(
            artifact_focus_alignment_score(artifact, "signaling pathway"),
            0,
        )

    def test_construct_prompt_root_fallback_control_decision_prefers_decomposition(self) -> None:
        """
        High Level Purpose:
            In circumstances like construct prompts that explicitly ask for an ordered signaling chain, helps with proving that the fallback controller path decomposes the root instead of forcing direct refinement through one answer surface.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_construct_prompt_root_fallback_control_decision_prefers_decomposition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Construct the full signaling pathway from stimulus detection to response, and explain why receptor presence is necessary for signal effectiveness."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        controller.ensure_not_elaboration(state.root())

        decision = controller.fallback_control_decision(state.root())

        self.assertTrue(decision["should_decompose"])
        self.assertFalse(decision["can_refine_directly"])

    def test_break_this_down_root_fallback_control_decision_prefers_decomposition(self) -> None:
        """
        High Level Purpose:
            In circumstances like multi-result prompts that explicitly ask for separate results, helps with proving that the fallback controller path decomposes the root instead of flattening the ask into one undifferentiated direct answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_break_this_down_root_fallback_control_decision_prefers_decomposition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Break this down carefully if needed: for a cylinder with radius=3 and height=5, "
            "give me the total surface area and the volume as separate results."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        controller.ensure_not_elaboration(state.root())

        decision = controller.fallback_control_decision(state.root())

        self.assertTrue(decision["should_decompose"])
        self.assertFalse(decision["can_refine_directly"])

    def test_title_depth_body_split_flag_keeps_root_decomposition_even_with_single_current_component(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result roots whose current structured-learning view has collapsed to one placeholder component, helps with proving that the explicit title-depth body-split requirement still forces decomposition.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_title_depth_body_split_flag_keeps_root_decomposition_even_with_single_current_component()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Break this down carefully if needed: for a cylinder with radius=3 and height=5, "
            "give me the total surface area and the volume as separate results."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        structured = controller.ensure_not_elaboration(root)
        structured["component_nots"] = ["Structured learning record for Cylinder Measures"]
        structured["title_depth_body_split_needed"] = True
        root.metadata["structured_learning"] = structured

        decision = controller.fallback_control_decision(root)

        self.assertTrue(decision["should_decompose"])
        self.assertFalse(decision["can_refine_directly"])

    def test_preserve_parent_does_not_override_required_root_decomposition(self) -> None:
        """
        High Level Purpose:
            In circumstances like multi-result root prompts where decomposition is structurally required, helps with proving that a stale `preserve_parent` marker does not reopen direct refinement against the active control decision.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_preserve_parent_does_not_override_required_root_decomposition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Break this down carefully if needed: for a cylinder with radius=3 and height=5, "
            "give me the total surface area and the volume as separate results."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)
        root.metadata["decomposition_choice"] = "preserve_parent"

        self.assertFalse(controller.can_refine_directly(root))

    def test_break_this_down_prompt_decompose_or_refine_creates_children_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like fallback decomposition without an LLM supplement, helps with proving that a decomposable multi-result root prompt actually creates children instead of preserving the parent by mistake.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_break_this_down_prompt_decompose_or_refine_creates_children_under_fallback()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Break this down carefully if needed: for a cylinder with radius=3 and height=5, "
            "give me the total surface area and the volume as separate results."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertGreaterEqual(len(children), 2)

    def test_break_this_down_prompt_decompose_or_refine_rebuilds_split_children_from_requested_outputs(self) -> None:
        """
        High Level Purpose:
            In circumstances like split-result roots whose current structured-learning view collapsed to one placeholder component, helps with proving that fallback decomposition rebuilds distinct child outputs from the explicit requested result phrases.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_break_this_down_prompt_decompose_or_refine_rebuilds_split_children_from_requested_outputs()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Break this down carefully if needed: for a cylinder with radius=3 and height=5, "
            "give me the total surface area and the volume as separate results."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        structured = controller.ensure_not_elaboration(root)
        structured["component_nots"] = ["Structured learning record for Cylinder Measures"]
        structured["title_depth_body_split_needed"] = True
        root.metadata["structured_learning"] = structured

        children = controller.decompose_or_refine(root)
        child_units = {child.semantic_unit for child in children}

        self.assertGreaterEqual(len(children), 2)
        self.assertTrue(any(unit.endswith("/ Total Surface Area") for unit in child_units))
        self.assertTrue(any(unit.endswith("/ Volume") for unit in child_units))

    def test_construct_prompt_decompose_or_refine_creates_children_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like llm-off construct prompts whose fallback control already requires decomposition, helps with proving that runtime decomposition synthesizes subordinate children instead of preserving the parent unchanged.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_construct_prompt_decompose_or_refine_creates_children_under_fallback()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Construct the full signaling pathway from stimulus detection to response, "
            "and explain why receptor presence is necessary for signal effectiveness."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertGreaterEqual(len(children), 2)
        self.assertEqual(root.metadata.get("decomposition_choice"), "decompose")
        self.assertTrue(all(child.parent_id == root.id for child in children))

    def test_chemistry_chain_prompt_infers_intermediate_relation_components(self) -> None:
        """
        High Level Purpose:
            In circumstances like chemistry transformation prompts that ask for the full relation chain, helps with proving that structured-learning normalization materializes the intermediate relation stages explicitly.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_chain_prompt_infers_intermediate_relation_components()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Describe the full chain of transformations required to convert mass of a reactant "
            "into concentration of a product in solution, naming each intermediate relation used."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertTrue(structured["title_depth_body_split_needed"])
        self.assertEqual(
            structured["component_nots"],
            [
                "Mass To Mole Conversion",
                "Stoichiometric Ratio From Balanced Equations",
                "Concentration As Amount Per Volume",
            ],
        )

    def test_chemistry_chain_prompt_fallback_control_prefers_decomposition(self) -> None:
        """
        High Level Purpose:
            In circumstances like chemistry prompts that demand an ordered multi-step conversion path, helps with proving that fallback control decomposes the root instead of treating the prompt as one direct answer surface.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_chain_prompt_fallback_control_prefers_decomposition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Describe the full chain of transformations required to convert mass of a reactant "
            "into concentration of a product in solution, naming each intermediate relation used."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        decision = controller.fallback_control_decision(root)

        self.assertTrue(decision["should_decompose"])
        self.assertFalse(decision["can_refine_directly"])

    def test_chemistry_chain_prompt_decompose_or_refine_creates_explicit_relation_children(self) -> None:
        """
        High Level Purpose:
            In circumstances like llm-off chemistry chain prompts, helps with proving that runtime decomposition synthesizes the ordered intermediate relation children rather than preserving the parent unchanged.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_chain_prompt_decompose_or_refine_creates_explicit_relation_children()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Describe the full chain of transformations required to convert mass of a reactant "
            "into concentration of a product in solution, naming each intermediate relation used."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)
        child_units = [child.semantic_unit for child in children]

        self.assertEqual(len(children), 3)
        self.assertEqual(root.metadata.get("decomposition_choice"), "decompose")
        self.assertEqual(
            set(child_units),
            {
                "Mass To Mole Conversion",
                "Stoichiometric Ratio From Balanced Equations",
                "Concentration As Amount Per Volume",
            },
        )
        child_structured = controller.ensure_not_elaboration(children[0])
        self.assertEqual(child_structured["title_identity"], children[0].semantic_unit)
        self.assertEqual(child_structured["component_nots"], [])
        self.assertFalse(child_structured["title_depth_body_split_needed"])
        self.assertTrue(all(child.metadata.get("faithfulness") == "high" for child in children))
        self.assertTrue(all(child.parent_id == root.id for child in children))

    def test_chemistry_chain_prompt_preserves_intermediate_relation_order(self) -> None:
        """
        High Level Purpose:
            In circumstances like chemistry chain prompts whose meaning depends on an ordered transformation path, helps with proving that decomposition preserves the canonical intermediate sequence rather than only recovering an unordered bag of relation names.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_chemistry_chain_prompt_preserves_intermediate_relation_order()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Describe the full chain of transformations required to convert mass of a reactant "
            "into concentration of a product in solution, naming each intermediate relation used."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertEqual(
            [child.semantic_unit for child in children],
            [
                "Mass To Mole Conversion",
                "Stoichiometric Ratio From Balanced Equations",
                "Concentration As Amount Per Volume",
            ],
        )

    def test_relation_bridge_prompt_infers_explicit_source_target_and_substrate_components(self) -> None:
        prompt = (
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, "
            "and explain how this relates to the reusable substrate."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertTrue(structured["title_depth_body_split_needed"])
        self.assertEqual(
            structured["component_nots"],
            [
                "Express How To Compute Mass From Moles And Molar Mass",
                "Reusable Substrate For Molar Mass",
            ],
        )

    def test_relation_bridge_component_fallback_children_keep_parent_lookup_context(self) -> None:
        prompt = (
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, "
            "and explain how this relates to the reusable substrate."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)
        compute_child = next(
            child
            for child in children
            if child.semantic_unit == "Express How To Compute Mass From Moles And Molar Mass"
        )
        substrate_child = next(
            child
            for child in children
            if child.semantic_unit == "Reusable Substrate For Molar Mass"
        )

        compute_structured = controller.ensure_not_elaboration(compute_child)
        substrate_structured = controller.ensure_not_elaboration(substrate_child)

        self.assertEqual(compute_structured["prompt_directive_kind"], "derive")
        self.assertIn(
            "compute mass mole molar mass",
            " ".join(str(item).strip() for item in compute_structured["lookup_keys"]).lower(),
        )
        self.assertEqual(substrate_structured["prompt_directive_kind"], "derive")
        self.assertIn(
            "reusable substrate",
            " ".join(str(item).strip() for item in substrate_structured["lookup_keys"]).lower(),
        )

    def test_relation_bridge_component_fallback_children_select_answer_bearing_artifacts(self) -> None:
        prompt = (
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, "
            "and explain how this relates to the reusable substrate."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)
        children = controller.decompose_or_refine(root)
        compute_child = next(
            child
            for child in children
            if child.semantic_unit == "Express How To Compute Mass From Moles And Molar Mass"
        )
        substrate_child = next(
            child
            for child in children
            if child.semantic_unit == "Reusable Substrate For Molar Mass"
        )

        compute_artifact = Artifact(
            id="artifact-compute-mass-from-moles-and-molar-mass",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 03 — Mass to Mole Conversion / Express How To Compute Mass From Moles And Molar Mass",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for chemistry derivation prompts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "Express how to compute mass from moles and molar mass.",
                "answer": "Compute mass from moles and molar mass with the determinate relation m = nM.",
                "aliases": ["compute mass from moles and molar mass"],
                "structured_learning": controller.structured_learning_view_for_text(
                    "Express how to compute mass from moles and molar mass.",
                    title_identity="Express How To Compute Mass From Moles And Molar Mass",
                    related_artifact_titles=[],
                ),
            },
            justification="Deterministic chemistry compute relation.",
            boundary_shape=list(compute_child.boundary_shape),
            constraints=[],
        )
        substrate_artifact = Artifact(
            id="artifact-reusable-substrate-for-molar-mass",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 03 — Mass to Mole Conversion / Total Per Unit Division",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for chemistry derivation prompts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is the reusable substrate for molar mass?",
                "answer": (
                    "Total-per-unit division is the broader reusable substrate; molar-mass conversion is "
                    "the narrower chemistry law."
                ),
                "aliases": ["reusable substrate for molar mass", "total per unit division"],
                "structured_learning": controller.structured_learning_view_for_text(
                    "What is the reusable substrate for molar mass?",
                    title_identity="Total Per Unit Division",
                    related_artifact_titles=[],
                ),
            },
            justification="Deterministic chemistry substrate explanation.",
            boundary_shape=list(substrate_child.boundary_shape),
            constraints=[],
        )
        state.learned_artifacts[compute_artifact.id] = compute_artifact
        state.learned_artifacts[substrate_artifact.id] = substrate_artifact

        compute_reused = controller.instantiate_reusable_artifact_support(compute_child)
        substrate_reused = controller.instantiate_reusable_artifact_support(substrate_child)

        self.assertTrue(compute_reused)
        self.assertTrue(compute_child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("m = nm", compute_child.metadata.get("direct_resolution_answer", "").lower())
        self.assertTrue(substrate_reused)
        self.assertTrue(substrate_child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn(
            "broader reusable substrate",
            compute_child.metadata.get("direct_resolution_answer", "").lower()
            + " "
            + substrate_child.metadata.get("direct_resolution_answer", "").lower(),
        )

    def test_component_fallback_compute_child_prefers_family_ability_via_governed_reuse_query(self) -> None:
        prompt = (
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, "
            "and explain how this relates to the reusable substrate."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)
        children = controller.decompose_or_refine(root)
        compute_child = next(
            child
            for child in children
            if child.semantic_unit == "Express How To Compute Mass From Moles And Molar Mass"
        )

        mass_from_moles = Artifact(
            id="artifact-mass-from-moles-family-ability",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry Relations 03 — Mass to Mole Conversion / Mass From Moles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for chemistry derivation prompts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate m from n, M?",
                "python_script": "def run(n=None, M=None):\n    return {'m': (n * M) if n is not None and M is not None else None}\n",
                "compute_expression": "n * M",
                "output_field": "m",
                "input_contract": {
                    "n": {"type": "number"},
                    "M": {"type": "number"},
                },
                "output_contract": {
                    "m": {"type": "number"},
                },
                "structured_learning": controller.structured_learning_view_for_text(
                    "Derive how to compute mass from moles and molar mass.",
                    title_identity="Chemistry Relations 03 — Mass to Mole Conversion / Mass From Moles",
                    related_artifact_titles=[],
                ),
            },
            justification="Family-local mass-from-moles ability.",
            boundary_shape=list(compute_child.boundary_shape),
            constraints=[],
        )
        state.learned_artifacts[mass_from_moles.id] = mass_from_moles

        lookup = controller.lookup_prior_non_achievedness(compute_child)

        self.assertEqual(
            lookup["reuse_semantic_unit"],
            "Derive How To Compute Mass From Moles And Molar Mass.",
        )
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, mass_from_moles.id)

        reused = controller.instantiate_reusable_artifact_support(compute_child)

        self.assertTrue(reused)
        self.assertTrue(compute_child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("m = n * m", compute_child.metadata.get("direct_resolution_answer", "").lower())

    def test_component_fallback_nominal_child_prefers_family_knowledge_via_governed_reuse_query(self) -> None:
        prompt = (
            "Starting from solute conservation and concentration definitions, derive the dilution law "
            "( C_1 V_1 = C_2 V_2 ) and explain each substitution step."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)
        children = controller.decompose_or_refine(root)
        concentration_child = next(
            child
            for child in children
            if child.semantic_unit == "Concentration Definitions"
        )

        concentration_artifact = Artifact(
            id="artifact-concentration-form-before-and-after-dilution",
            artifact_type=ArtifactType.KNOWLEDGE,
            title="Chemistry Relations 07 — Dilution as Solute Conservation with Volume Change / Concentration Form Before And After Dilution",
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for chemistry derivation prompts",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "What is concentration form before and after dilution?",
                "answer": (
                    "Concentration definitions provide the amount-per-volume form before and after dilution, "
                    "so the carried substance can be written as concentration times volume."
                ),
                "aliases": [
                    "concentration definitions",
                    "concentration form before and after dilution",
                ],
                "structured_learning": controller.structured_learning_view_for_text(
                    "Explain concentration definitions in the derivation of the dilution law.",
                    title_identity="Chemistry Relations 07 — Dilution as Solute Conservation with Volume Change / Concentration Form Before And After Dilution",
                    related_artifact_titles=[],
                ),
            },
            justification="Family-local concentration definition explanation.",
            boundary_shape=list(concentration_child.boundary_shape),
            constraints=[],
        )
        state.learned_artifacts[concentration_artifact.id] = concentration_artifact

        lookup = controller.lookup_prior_non_achievedness(concentration_child)

        self.assertEqual(
            lookup["reuse_semantic_unit"],
            "What is Concentration Definitions?",
        )
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, concentration_artifact.id)

        reused = controller.instantiate_reusable_artifact_support(concentration_child)

        self.assertTrue(reused)
        self.assertTrue(concentration_child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn(
            "amount-per-volume",
            concentration_child.metadata.get("direct_resolution_answer", "").lower(),
        )

    def test_relation_bridge_prompt_decompose_or_refine_replaces_generic_fragment_children(self) -> None:
        prompt = (
            "Using the stoichiometric ratio relation, derive how to compute the amount of substance ( n_B ) "
            "from a known ( n_A ) and coefficients."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)
        child_units = {child.semantic_unit for child in children}

        self.assertEqual(
            child_units,
            {
                "Stoichiometric Ratio",
                "Derive How To Compute The Amount Of Substance N B From A Known N A And Coefficients",
            },
        )
        self.assertFalse(any("Given Relation" in unit for unit in child_units))

    def test_starting_from_derive_prompt_infers_source_and_target_components(self) -> None:
        prompt = (
            "Starting from solute conservation and concentration definitions, derive the dilution law "
            "( C_1 V_1 = C_2 V_2 ) and explain each substitution step."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertTrue(structured["title_depth_body_split_needed"])
        self.assertEqual(
            structured["component_nots"],
            [
                "Solute Conservation",
                "Concentration Definitions",
                "The Dilution Law C 1 V 1 C 2 V 2",
            ],
        )

    def test_starting_from_derive_prompt_decompose_or_refine_creates_explicit_children(self) -> None:
        prompt = (
            "Starting from solute conservation and concentration definitions, derive the dilution law "
            "( C_1 V_1 = C_2 V_2 ) and explain each substitution step."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)
        child_units = {child.semantic_unit for child in children}

        self.assertEqual(
            child_units,
            {
                "Solute Conservation",
                "Concentration Definitions",
                "The Dilution Law C 1 V 1 C 2 V 2",
            },
        )

    def test_same_family_explain_prompt_extracts_compared_terms(self) -> None:
        prompt = (
            "Explain why mass conservation and atom conservation belong to the same family "
            "but must not be treated as the same law."
        )

        directive = semantic_prompt_directive_profile(prompt)

        self.assertEqual(directive["kind"], "distinguish")
        self.assertEqual(
            directive["compared_terms"],
            ["mass conservation", "atom conservation"],
        )

    def test_same_family_explain_prompt_preserves_parent_surface(self) -> None:
        prompt = (
            "Explain why mass conservation and atom conservation belong to the same family "
            "but must not be treated as the same law."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertEqual(children, [])
        self.assertEqual(root.metadata.get("decomposition_choice"), "preserve_parent")

    def test_formula_bearing_construct_prompt_preserves_parent_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like formula-bearing construct prompts that request one explicit reasoning chain rather than separate body-level results, helps with proving that fallback decomposition preserves the parent instead of fragmenting the prompt into prompt-surface shards.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how electric power expressions ( P = VI ), ( P = I^2 R ), and ( P = V^2 / R ) are derived "
            "through composition of the driving-response relation and multiplicative combination. Provide the full reasoning chain."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertEqual(children, [])
        self.assertEqual(root.metadata.get("decomposition_choice"), "preserve_parent")

    def test_formula_bearing_construct_prompt_clears_component_fragments_in_not_elaboration(self) -> None:
        """
        High Level Purpose:
            In circumstances like formula-bearing construct prompts whose governing task should stay at one root chain, helps with proving that structured learning does not keep polluted component fragments that later retrieval can mistake for real subproblems.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how electric power expressions ( P = VI ), ( P = I^2 R ), and ( P = V^2 / R ) are derived "
            "through composition of the driving-response relation and multiplicative combination. Provide the full reasoning chain."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertEqual(structured.get("component_nots"), [])
        self.assertFalse(any("Multiplicative Combination Provide Full Reason Chain" in item for item in structured.get("lookup_keys", [])))

    def test_equilibrium_construct_prompt_preserves_parent_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like composition prompts that already name the contributing substrates and ask for one full reasoning path, helps with proving that fallback decomposition preserves the governing parent instead of fabricating prompt-surface child shards.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how the equilibrium constant expression composes multiple earlier semantic substrates "
            "(concentration, stoichiometric coefficients, and weighted product ratios), and reconstruct "
            "the full reasoning path from these components to the final form of ( K )."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        decision = controller.fallback_control_decision(root)
        children = controller.decompose_or_refine(root)

        self.assertFalse(decision["should_decompose"])
        self.assertEqual(children, [])
        self.assertEqual(root.metadata.get("decomposition_choice"), "preserve_parent")

    def test_equilibrium_construct_prompt_clears_prompt_surface_fragments_in_not_elaboration(self) -> None:
        """
        High Level Purpose:
            In circumstances like equilibrium composition prompts whose chain must remain one governed reasoning task, helps with proving that structured learning does not keep prompt-surface fragment children that later force an unnecessary pause.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how the equilibrium constant expression composes multiple earlier semantic substrates "
            "(concentration, stoichiometric coefficients, and weighted product ratios), and reconstruct "
            "the full reasoning path from these components to the final form of ( K )."
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertEqual(structured.get("component_nots"), [])
        self.assertFalse(
            any(
                "Reconstruct Full Reason Path These Component Final Form K" in str(item)
                for item in structured.get("lookup_keys", [])
            )
        )

    def test_distinguish_prompt_preserves_parent_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct contrast prompts that already carry both contrasted cases explicitly, helps with proving that fallback decomposition preserves the parent so the contrast remains at one governing node.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain the difference between the general force law ( F = ma ) and the specific case of weight ( W = mg )."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertEqual(children, [])
        self.assertEqual(root.metadata.get("decomposition_choice"), "preserve_parent")

    def test_distinguish_prompt_clears_component_fragments_in_not_elaboration(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct contrast prompts that already carry both cases explicitly, helps with proving that structured learning keeps the contrast at the root instead of manufacturing child fragments that later retrieval can overfit to.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain the difference between the general force law ( F = ma ) and the specific case of weight ( W = mg )."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertEqual(structured.get("component_nots"), [])
        self.assertFalse(any(" / " in str(item) for item in structured.get("lookup_keys", [])))

    def test_identify_reusable_substrate_prompt_preserves_parent_under_fallback(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts that already ask for one broader family explanation, helps with proving that fallback decomposition preserves the parent instead of manufacturing child shards.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)

        self.assertEqual(children, [])
        self.assertEqual(root.metadata.get("decomposition_choice"), "preserve_parent")

    def test_identify_reusable_substrate_prompt_clears_component_fragments_in_not_elaboration(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts that should stay at one governing node, helps with proving that structured learning does not keep fabricated component fragments that later retrieval can overfit to.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()

        structured = controller.ensure_not_elaboration(root)

        self.assertEqual(structured.get("component_nots"), [])
        self.assertFalse(any(" / " in str(item) for item in structured.get("lookup_keys", [])))

    def test_refine_directly_generic_support_only_reuse_does_not_mark_direct_refined(self) -> None:
        """
        High Level Purpose:
            In circumstances like generic children that receive only related support from prior residue, helps with proving that support attachment does not terminate direct refinement before commitment readiness exists.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_refine_directly_generic_support_only_reuse_does_not_mark_direct_refined()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        child = self.state.root()
        child.role = "generic"
        child.metadata.clear()

        def fake_support(node):
            node.metadata["related_support_only"] = True
            return True

        with mock.patch.object(self.controller, "instantiate_reusable_artifact_support", side_effect=fake_support):
            self.controller.refine_directly(child)

        self.assertTrue(child.metadata.get("related_support_only"))
        self.assertFalse(child.metadata.get("direct_resolution_ready_for_commitment", False))
        self.assertFalse(child.metadata.get("direct_refined", False))

    def test_refine_directly_generic_reuse_evidence_does_not_mark_direct_refined(self) -> None:
        """
        High Level Purpose:
            In circumstances like generic children whose reuse path already attached related-support evidence, helps with proving that the evidence side effect does not wrongly terminate the child as directly refined.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        child = self.state.root()
        child.role = "generic"
        child.metadata.clear()

        def fake_support(node):
            self.state.attach_evidence(
                Evidence(
                    id="evidence-related-support",
                    node_id=node.id,
                    observation="Related prior support is available.",
                    source="committed_state",
                    context={"generated_by": "test"},
                    support_effect=ThreeLevel.MEDIUM,
                    confidence=ThreeLevel.MEDIUM,
                )
            )
            node.metadata["related_support_only"] = True
            return True

        with mock.patch.object(self.controller, "instantiate_reusable_artifact_support", side_effect=fake_support):
            self.controller.refine_directly(child)

        self.assertTrue(child.metadata.get("related_support_only"))
        self.assertFalse(child.metadata.get("direct_resolution_ready_for_commitment", False))
        self.assertFalse(child.metadata.get("direct_refined", False))

    def test_diffusion_state_prompt_prefers_diffusion_relation_over_receptor_relation(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct biology relation prompts, helps with proving that the prompt ranks the requested diffusion law above an adjacent receptor-effect fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_diffusion_state_prompt_prefers_diffusion_relation_over_receptor_relation()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the relation that describes diffusion and explain the directional rule it follows."
        diffusion = make_knowledge_artifact(
            artifact_id="artifact-diffusion",
            title="Learn Biology: Membrane Transport Relations / Diffusion relation",
            question="What is Diffusion relation?",
            answer="Diffusion is movement from higher concentration to lower concentration. So: high concentration -> low concentration",
        )
        receptor = make_knowledge_artifact(
            artifact_id="artifact-receptor",
            title="Learn Biology: Signaling and Nervous Control Relations / Receptor relation",
            question="What is Receptor relation?",
            answer="A signal has no biological effect merely by existing. It must be received. So: signal effectiveness depends on target receptivity",
        )

        diffusion_rank = self.controller.answer_candidate_rank(
            diffusion,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        receptor_rank = self.controller.answer_candidate_rank(
            receptor,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(diffusion_rank, receptor_rank)

    def test_state_plus_change_prompt_prefers_velocity_update_over_generic_multiplicative_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like state-plus-change prompts over constant acceleration, helps with proving that the specific velocity-update relation outranks the generic multiplicative substrate.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_plus_change_prompt_prefers_velocity_update_over_generic_multiplicative_family()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Using the constant-acceleration relation, write the equation that updates velocity from "
            "initial velocity, acceleration, and time, and identify the state-plus-change structure."
        )
        velocity_update = make_knowledge_artifact(
            artifact_id="artifact-velocity-update",
            title="Physics Relations / Velocity update",
            question="What is Velocity update?",
            answer="Under constant acceleration, velocity changes linearly with time. v = u + at. input: u initial velocity. input: a acceleration. input: t time. output: v final velocity.",
        )
        multiplicative_family = make_knowledge_artifact(
            artifact_id="artifact-multiplicative-family",
            title="Physics Relations — Force and Mass-Acceleration Relation / Multiplicative Combination",
            question="What is Multiplicative Combination?",
            answer="When one quantity equals one physical factor multiplied by another, the reusable family is multiplicative combination. The reusable formula is P = x * y.",
        )

        velocity_rank = self.controller.answer_candidate_rank(
            velocity_update,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        multiplicative_rank = self.controller.answer_candidate_rank(
            multiplicative_family,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(velocity_rank, multiplicative_rank)

    def test_semantic_prompt_action_posture_marks_direct_explanatory_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over prompt-routing seams, helps with proving that a direct concept question stays on the direct-resolution posture without constructing a full fallback non-achievedness payload.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_semantic_prompt_action_posture_marks_direct_explanatory_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "What is mass conservation in a reaction?"
        self.assertEqual(semantic_prompt_action_posture(prompt), "direct_resolution")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))
        self.assertFalse(semantic_unit_allows_default_invocation_payload(prompt))

    def test_semantic_prompt_action_posture_marks_compute_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over executable reuse routing, helps with proving that named-input compute prompts stay on the compute-or-template posture and admit default invocation payloads.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_semantic_prompt_action_posture_marks_compute_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Calculate force from mass=3 and acceleration=4."
        self.assertEqual(semantic_prompt_action_posture(prompt), "compute_or_template")
        self.assertFalse(semantic_prompt_prefers_direct_knowledge_answer(prompt))
        self.assertTrue(semantic_unit_allows_default_invocation_payload(prompt))

    def test_write_formula_prompt_stays_state_directive(self) -> None:
        """
        High Level Purpose:
            In circumstances like distinguishing explanatory formula prompts from executable file commands, helps with proving that `write the formula` still routes as a law-statement directive.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_write_formula_prompt_stays_state_directive()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Write the formula that relates number of particles to moles and Avogadro's constant."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "state")
        self.assertEqual(semantic_prompt_action_posture(prompt), "direct_resolution")

    def test_write_mount_command_is_not_treated_as_state_directive(self) -> None:
        """
        High Level Purpose:
            In circumstances like broker-first Python command prompts, helps with proving that imperative filesystem actions stay on the executable posture instead of being misread as explanatory `state` requests.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_write_mount_command_is_not_treated_as_state_directive()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Write `hello world` to mount `skill_tmp` at `python-suite.txt`."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "none")
        self.assertEqual(semantic_prompt_action_posture(prompt), "compute_or_template")
        self.assertFalse(semantic_prompt_prefers_direct_knowledge_answer(prompt))
        self.assertTrue(semantic_unit_allows_default_invocation_payload(prompt))

    def test_semantic_prompt_action_posture_marks_uncertain_prompt_for_clarification(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over uncertainty-sensitive routing, helps with proving that unresolved alternatives stay on the clarify-before-acting posture.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_semantic_prompt_action_posture_marks_uncertain_prompt_for_clarification()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "It could be 5 or 7 depending on the missing label."
        self.assertEqual(semantic_prompt_action_posture(prompt), "clarify_before_acting")

    def test_semantic_prompt_action_posture_keeps_action_guidance_prompt_as_next_step_guidance(self) -> None:
        """
        High Level Purpose:
            In circumstances like safety prompts that contain uncertainty but still explicitly ask for the next action, helps with proving that the runtime keeps them on the next-step-guidance posture rather than stalling them as generic clarification prompts.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_semantic_prompt_action_posture_keeps_action_guidance_prompt_as_next_step_guidance()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "My doctor told me to take 2 tablets now, but the loose tablets in front of me are not clearly identified. What should I do?"
        self.assertEqual(semantic_prompt_action_posture(prompt), "next_step_guidance")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))

    def test_semantic_prompt_action_posture_treats_what_next_uncertainty_as_guidance(self) -> None:
        """
        High Level Purpose:
            In circumstances like mixed-tablet safety prompts that explicitly ask what to do next, helps with keeping the prompt on the next-step-guidance path even when uncertainty markers are present.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_semantic_prompt_action_posture_treats_what_next_uncertainty_as_guidance()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "I'm holding 3 tablets: one might be 10 mg, one might be 100 mg, and one is unknown. What next?"
        self.assertEqual(semantic_prompt_action_posture(prompt), "next_step_guidance")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))

    def test_next_step_guidance_prompt_can_collect_direct_knowledge_candidates_without_question_focus(self) -> None:
        """
        High Level Purpose:
            In circumstances like action-guidance prompts that do not expose a clean `what is X` focus phrase, helps with proving that the direct-knowledge reuse path can still collect answer-bearing candidates instead of returning an empty pool.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_next_step_guidance_prompt_can_collect_direct_knowledge_candidates_without_question_focus()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution",
            title="Unknown tablet identification first",
            question="What should I do if I cannot tell which loose tablet is the right dose?",
            answer="Do not take any tablet until you identify the exact tablet from the label or imprint and confirm with a pharmacist or Poison Help.",
        )
        prompt = "My doctor told me to take 2 tablets now, but the loose tablets in front of me are not clearly identified. What should I do?"

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[("focus_alignment", caution)],
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][1].id, caution.id)

    def test_controller_uses_state_bound_artifact_store(self) -> None:
        """
        High Level Purpose:
            In circumstances like validator and CLI runs that bind a controller to a specific SQLite artifact store, helps with proving that the controller reuses the state-bound store instead of silently falling back to the default repository store.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_controller_uses_state_bound_artifact_store()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteVectorArtifactStore()
            store.sqlite_path = Path(temp_dir) / "bound.sqlite3"
            store.load_all_artifacts()
            state = SystemState.bootstrap("store binding")
            state.store = store

            controller = BSSCController(state, llm_policy="off")

            self.assertIs(controller.artifact_store, store)

    def test_lookup_prior_non_achievedness_can_select_persisted_next_step_guidance_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like store-backed next-step guidance prompts that lack a clean `what is X` focus phrase, helps with proving that prior-learning lookup can still select a persisted caution artifact instead of falling back to a fresh structured-learning record.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_lookup_prior_non_achievedness_can_select_persisted_next_step_guidance_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution",
            title="Unknown tablet identification first",
            question="What should I do if I cannot tell which loose tablet is the right dose?",
            answer="Do not take any tablet until you identify the exact tablet from the label or imprint and confirm with a pharmacist or Poison Help.",
        )
        prompt = "My doctor told me to take 2 tablets now, but the loose tablets in front of me are not clearly identified. What should I do?"

        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteVectorArtifactStore()
            store.sqlite_path = Path(temp_dir) / "lookup.sqlite3"
            store.load_all_artifacts()
            store.persist_artifact(caution, run_id="test:tablet-guidance")
            state = SystemState.bootstrap(prompt)
            state.store = store
            controller = BSSCController(state, llm_policy="off")

            lookup = controller.lookup_prior_non_achievedness(state.root())

            self.assertIsNotNone(lookup["answer_artifact"])
            self.assertEqual(lookup["answer_artifact"].id, caution.id)

    def test_next_step_guidance_reuse_stays_support_only_not_closure(self) -> None:
        """
        High Level Purpose:
            In circumstances like next-step guidance prompts that find a loosely aligned caution artifact, helps with proving that reuse remains support-only rather than immediately closing the node.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_next_step_guidance_reuse_stays_support_only_not_closure()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution",
            title="Unknown tablet identification first",
            question="What should I do if I cannot tell which loose tablet is the right dose?",
            answer="Do not take any tablet until you identify the exact tablet from the label or imprint and confirm with a pharmacist or Poison Help.",
        )
        prompt = "My doctor told me to take 2 tablets now, but the loose tablets in front of me are not clearly identified. What should I do?"
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        state.learned_artifacts[caution.id] = caution
        root = state.root()

        reused = controller.instantiate_reusable_artifact_support(root)

        self.assertTrue(reused)
        self.assertTrue(root.metadata.get("related_support_only"))
        self.assertFalse(root.metadata.get("direct_resolution_ready_for_commitment", False))

    def test_strong_grounded_next_step_guidance_reuse_can_close(self) -> None:
        """
        High Level Purpose:
            In circumstances like bounded next-step safety guidance with a strong root-level reuse match and an answer-bearing selected artifact, helps with proving that grounded reuse may close even though weak guidance overlap remains support-only.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_strong_grounded_next_step_guidance_reuse_can_close()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "My doctor told me to take 2 tablets now, but the loose tablets in front of me are not clearly identified. What should I do?"
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution-exact",
            title="Tablet Safety And Immediate Next Steps / Loose tablets when the dose is due now",
            question="I dropped today's tablets and now I cannot tell which is which, but the dose is due now. What should I do?",
            answer="Do not take the loose tablets. Confirm the exact tablet identity from the label or imprint and verify with a pharmacist or Poison Help first.",
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        current = controller.ensure_not_elaboration(root)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "encountered_before",
                "answer_match_kind": "focus_alignment_store",
                "answer_preference": "focus_alignment_store",
                "matched_lookup_keys": ["loose tablet"],
                "matched_artifacts": [caution],
                "reusable_artifacts": [caution],
                "answer_artifact": caution,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(root)

        self.assertTrue(reused)
        self.assertTrue(root.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(
            root.metadata.get("direct_resolution_answer"),
            caution.content.get("answer"),
        )

    def test_grounded_decomposition_related_next_step_guidance_reuse_can_close(self) -> None:
        """
        High Level Purpose:
            In circumstances like fresh learned guidance corpora where the current encounter is grounded by a prior structured match but the selected answer artifact still arrives through a decomposition-related relation, helps with proving that the controller can still close on the selected direct guidance artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_grounded_decomposition_related_next_step_guidance_reuse_can_close()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "The bottle says take 1 tablet now, but I have 2 loose tablets of different strengths and cannot tell which is which. What should I do?"
        caution = make_knowledge_artifact(
            artifact_id="artifact-caution-dose-due",
            title="Tablet Safety And Immediate Next Steps / Loose tablets when the dose is due now",
            question="I dropped today's tablets and now I cannot tell which is which, but the dose is due now. What should I do?",
            answer="Do not guess. Contact the pharmacist or prescriber for identification or replacement guidance.",
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        current = controller.ensure_not_elaboration(root)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "decomposition_related",
                "answer_match_kind": "composition_related",
                "answer_preference": "covers_components",
                "matched_lookup_keys": ["loose tablet", "tablet now"],
                "matched_artifacts": [],
                "reusable_artifacts": [caution],
                "answer_artifact": caution,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(root)

        self.assertTrue(reused)
        self.assertTrue(root.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("Do not guess", root.metadata.get("direct_resolution_answer", ""))

    def test_grounded_direct_knowledge_component_reuse_can_close_generic_child(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed child whose exact structured record is grounded but whose answer-bearing artifact only covers the needed components, helps with proving that direct-knowledge closure can still be admitted for the child.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it."
        ratio_family = make_knowledge_artifact(
            artifact_id="artifact-ratio-family",
            title="Physics Relations Rate of Change in Motion / Ratio Of Change",
            question="What is Ratio Of Change?",
            answer="When a quantity is defined as change per unit of another quantity, the reusable family is ratio-of-change.",
        )
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)
        children = controller.decompose_or_refine(root)
        child = next(
            candidate
            for candidate in children
            if "State General Ratio Change Formula" in candidate.semantic_unit
        )
        current = controller.ensure_not_elaboration(child)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "encountered_before",
                "answer_match_kind": "composition_related",
                "answer_preference": "covers_components",
                "matched_lookup_keys": ["ratio change", "state general ratio change formula"],
                "matched_artifacts": [],
                "reusable_artifacts": [ratio_family],
                "answer_artifact": ratio_family,
                "focus_candidates": [ratio_family],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(child)

        self.assertTrue(reused)
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("ratio-of-change", child.metadata.get("direct_resolution_answer", ""))

    def test_grounded_same_family_direct_resolution_reuse_can_close_generic_child(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct-resolution generic children that match a prior answer-bearing family through a decomposition-related route, helps with proving that grounded same-family reuse can still close instead of remaining support-only.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        family_artifact = make_knowledge_artifact(
            artifact_id="artifact-mass-to-mole-family",
            title="Chemistry Relations 03 — Mass to Mole Conversion / Total Per Unit Division",
            question="What is Total Per Unit Division?",
            answer=(
                "Total-per-unit division is the broader reusable substrate; molar-mass conversion "
                "is a narrower determinate chemistry law that uses grams per mole as the unit size."
            ),
        )
        prompt = "Mass To Mole Conversion"
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        child = state.root()
        child.role = "generic"
        current = controller.ensure_not_elaboration(child)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "decomposition_related",
                "answer_match_kind": "decomposition_related",
                "answer_preference": "same_composed_family",
                "matched_lookup_keys": ["mass mole conversion"],
                "matched_artifacts": [family_artifact],
                "reusable_artifacts": [family_artifact],
                "answer_artifact": family_artifact,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(child)

        self.assertTrue(reused)
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("molar-mass conversion", child.metadata.get("direct_resolution_answer", "").lower())

    def test_component_covering_composition_reuse_can_close_direct_resolution_child(self) -> None:
        family_artifact = make_knowledge_artifact(
            artifact_id="artifact-total-per-unit-division",
            title="Chemistry Relations 03 — Mass To Mole Conversion / Total Per Unit Division",
            question="What is Total Per Unit Division?",
            answer=(
                "Molar-mass conversion reuses total-per-unit division: compute mass from moles and molar mass "
                "with m = nM, and this is the narrower chemistry instance of the broader substrate."
            ),
        )
        prompt = "Molar Mass"
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        node = state.root()
        node.role = "generic"
        current = controller.ensure_not_elaboration(node)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "composition_related",
                "answer_match_kind": "composition_related",
                "answer_preference": "covers_components",
                "matched_lookup_keys": ["molar mass", "total per unit division"],
                "matched_artifacts": [family_artifact],
                "reusable_artifacts": [family_artifact],
                "answer_artifact": family_artifact,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(node)

        self.assertTrue(reused)
        self.assertTrue(node.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertIn("m = nm", node.metadata.get("direct_resolution_answer", "").lower())

    def test_formula_role_reuse_can_close_input_child_with_extracted_input_answer(self) -> None:
        artifact = make_knowledge_artifact(
            artifact_id="artifact-conservation-formula-roles",
            title="Chemistry Relations 01 — Conservation Of Amount",
            question="What is Conservation?",
            answer=(
                "When the total amount before a process equals the total amount after a process, "
                "the reusable formula is: $$ T{before} = T{after} $$ input: Tbefore "
                "output: Tafter If the amount of solute stays the same before and after dilution, "
                "the reusable family is conservation of carried substance."
            ),
        )
        prompt = "General Conservation Formula Input"
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        child = state.root()
        child.role = "generic"
        current = controller.ensure_not_elaboration(child)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "decomposition_related",
                "answer_match_kind": "decomposition_related",
                "answer_preference": "related_key",
                "matched_lookup_keys": [],
                "matched_artifacts": [artifact],
                "reusable_artifacts": [artifact],
                "answer_artifact": artifact,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(child)

        self.assertTrue(reused)
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(child.metadata.get("direct_resolution_answer"), "input: Tbefore")

    def test_formula_role_reuse_can_close_output_child_with_extracted_output_answer(self) -> None:
        artifact = make_knowledge_artifact(
            artifact_id="artifact-conservation-formula-roles",
            title="Chemistry Relations 01 — Conservation Of Amount",
            question="What is Conservation?",
            answer=(
                "When the total amount before a process equals the total amount after a process, "
                "the reusable formula is: $$ T{before} = T{after} $$ input: Tbefore output: Tafter"
            ),
        )
        prompt = "General Conservation Formula Output Represent"
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        child = state.root()
        child.role = "generic"
        current = controller.ensure_not_elaboration(child)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "decomposition_related",
                "answer_match_kind": "decomposition_related",
                "answer_preference": "related_key",
                "matched_lookup_keys": [],
                "matched_artifacts": [artifact],
                "reusable_artifacts": [artifact],
                "answer_artifact": artifact,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(child)

        self.assertTrue(reused)
        self.assertTrue(child.metadata.get("direct_resolution_ready_for_commitment"))
        self.assertEqual(child.metadata.get("direct_resolution_answer"), "output: Tafter")

    def test_formula_role_reuse_preserves_formula_when_prompt_requests_formula_and_roles(self) -> None:
        artifact = make_knowledge_artifact(
            artifact_id="artifact-conservation-formula-roles",
            title="Chemistry Relations 01 — Conservation Of Amount",
            question="What is Mass conservation in a reaction?",
            answer=(
                "General Conservation Formula: Mass conservation in a reaction. "
                "Mass conservation is a conservation law in chemistry. "
                "The reusable formula is: $$ T{before} = T{after} $$ "
                "input: Tbefore output: Tafter"
            ),
        )
        prompt = "State the general conservation formula and explain what the inputs and outputs represent."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        node = state.root()
        node.role = "generic"
        current = controller.ensure_not_elaboration(node)

        with mock.patch.object(
            controller,
            "lookup_prior_non_achievedness",
            return_value={
                "match_kind": "encountered_before",
                "answer_match_kind": "encountered_before",
                "answer_preference": "focus_alignment_store",
                "matched_lookup_keys": [
                    "state general conservation formula input output represent",
                    "state general conservation formula",
                    "input",
                    "output represent",
                ],
                "matched_artifacts": [artifact],
                "reusable_artifacts": [artifact],
                "answer_artifact": artifact,
                "focus_candidates": [],
                "current": current,
            },
        ):
            reused = controller.instantiate_reusable_artifact_support(node)

        self.assertTrue(reused)
        self.assertTrue(node.metadata.get("direct_resolution_ready_for_commitment"))
        answer = node.metadata.get("direct_resolution_answer", "")
        self.assertIn("The reusable formula is: $$ T{before} = T{after} $$", answer)
        self.assertIn("input: Tbefore", answer)
        self.assertIn("output: Tafter", answer)
        self.assertNotEqual(answer, "input: Tbefore output: Tafter")

    def test_learning_context_query_variants_include_derivation_and_substrate_forms(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over derivation and substrate prompts, helps with proving that retrieval queries include directive-specific surfaces instead of only generic focus strings.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_learning_context_query_variants_include_derivation_and_substrate_forms()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        derive_variants = self.controller.learning_context_query_variants(
            "Using the stoichiometric ratio relation, derive how to compute amount of product from limiting reagent."
        )
        lowered_derive = [item.lower() for item in derive_variants]
        self.assertTrue(any("derivation" in item or "relation chain" in item for item in lowered_derive))

        substrate_variants = self.controller.learning_context_query_variants(
            "Identify the reusable substrate underlying the ideal gas relation."
        )
        lowered_substrate = [item.lower() for item in substrate_variants]
        self.assertTrue(any("reusable substrate" in item for item in lowered_substrate))
        self.assertTrue(any("underlying family" in item for item in lowered_substrate))

    def test_learning_context_query_variants_include_relation_and_expressed_compute_forms(self) -> None:
        """
        High Level Purpose:
            In circumstances like chemistry formula and derivation prompts, helps with proving that retrieval variants include relation-shaped and expressed-compute surfaces rather than only the literal prose wrapper.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_learning_context_query_variants_include_relation_and_expressed_compute_forms()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        relation_variants = self.controller.learning_context_query_variants(
            "Write the formula that relates number of particles to moles and Avogadro's constant."
        )
        lowered_relation = [item.lower() for item in relation_variants]
        self.assertTrue(any("number of particles from moles and avogadro's constant" in item for item in lowered_relation))

        derive_variants = self.controller.learning_context_query_variants(
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, and explain how this relates to the reusable substrate."
        )
        lowered_derive = [item.lower() for item in derive_variants]
        self.assertTrue(any("compute mass from moles and molar mass" in item for item in lowered_derive))

    def test_formula_prompt_can_reuse_executable_formula_surface_without_payload(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct formula prompts over executable learned relations, helps with proving that a formula-bearing ability can answer textually without requiring a concrete invocation payload.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_formula_prompt_can_reuse_executable_formula_surface_without_payload()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        python_script = self.controller.expression_ability_script(
            title="Chemistry / Particles From Moles",
            scope="reuse for chemistry amount conversions",
            input_contract={"n": "number", "N_A": "number"},
            output_contract={"N": "number"},
            expression="n * N_A",
            output_field="N",
        )
        executable_formula = Artifact(
            id="artifact-particles-from-moles",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry / Particles From Moles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for chemistry amount conversions",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate N from n, N_A?",
                "answer": "",
                "python_script": python_script,
                "input_contract": {"n": "number", "N_A": "number"},
                "output_contract": {"N": "number"},
                "structured_learning": {
                    "encountered_not": "Particles From Moles",
                    "lookup_keys": ["particles from moles", "number of particles from moles avogadro constant"],
                    "component_nots": ["Particles", "Moles"],
                    "composed_not": "Particles From Moles",
                    "notation_yaml": "",
                },
            },
            justification="Executable chemistry relation.",
        )

        answer = self.controller.artifact_answer_text(
            executable_formula,
            semantic_unit="Write the formula that relates number of particles to moles and Avogadro's constant.",
        )

        self.assertIn("How do you calculate N from n, N_A?", answer)
        self.assertIn("N = n * N_A", answer)

    def test_load_learning_context_for_direct_formula_prompt_keeps_searching_past_first_query(self) -> None:
        """
        High Level Purpose:
            In circumstances like direct formula prompts whose first retrieval query returns only generic residue, helps with proving that loading context keeps searching later query variants long enough to pull in the executable relation.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_load_learning_context_for_direct_formula_prompt_keeps_searching_past_first_query()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        generic_records = [
            make_knowledge_artifact(
                artifact_id=f"artifact-generic-{index}",
                title=f"Structured learning record {index}",
                question=f"What is generic {index}?",
                answer=f"generic answer {index}",
            )
            for index in range(16)
        ]
        for artifact in generic_records:
            artifact.title = f"Structured learning record for Generic Relation {artifact.id}"
            artifact.content["structured_learning"]["encountered_not"] = f"Generic Relation {artifact.id}"
        python_script = self.controller.expression_ability_script(
            title="Chemistry / Particles From Moles",
            scope="reuse for chemistry amount conversions",
            input_contract={"n": "number", "N_A": "number"},
            output_contract={"N": "number"},
            expression="n * N_A",
            output_field="N",
        )
        executable_formula = Artifact(
            id="artifact-particles-from-moles-context",
            artifact_type=ArtifactType.ABILITY,
            title="Chemistry / Particles From Moles",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for chemistry amount conversions",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate N from n, N_A?",
                "answer": "",
                "python_script": python_script,
                "compute_expression": "n * N_A",
                "output_field": "N",
                "input_contract": {"n": "number", "N_A": "number"},
                "output_contract": {"N": "number"},
                "structured_learning": {
                    "encountered_not": "Particles From Moles",
                    "lookup_keys": ["particles from moles", "number of particles from moles"],
                    "component_nots": ["Particles", "Moles"],
                    "composed_not": "Particles From Moles",
                    "notation_yaml": "",
                },
            },
            justification="Executable chemistry relation.",
        )
        prompt = "Write the formula that relates number of particles to moles, and identify the role of each variable."
        query_variants = self.controller.learning_context_query_variants(prompt)
        self.assertGreater(len(query_variants), 1)
        store = mock.Mock()
        store.load_relevant_artifacts.side_effect = lambda query, limit=8: generic_records if query == query_variants[0] else [executable_formula]
        self.controller.artifact_store = store

        node = self.state.root()
        node.semantic_unit = prompt
        self.controller.load_learning_context(node)

        queried_texts = [str(call.args[0]) for call in store.load_relevant_artifacts.call_args_list]
        self.assertGreater(len(queried_texts), 1)

    def test_derivation_prompt_prefers_ratio_of_change_over_adjacent_domain_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over long explanatory physics prompts, helps with proving that the ranking path prefers the requested general ratio-of-change family over an adjacent circuit-law fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derivation_prompt_prefers_ratio_of_change_over_adjacent_domain_fragment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it."
        motion_definition = make_knowledge_artifact(
            artifact_id="artifact-ratio-change",
            title="Physics / General Ratio Of Change",
            question="What is the general ratio of change formula?",
            answer="The general ratio-of-change relation is quantity change divided by the change in the governing variable; in motion this appears as speed or velocity as displacement per unit time.",
        )
        circuit_fragment = make_knowledge_artifact(
            artifact_id="artifact-circuit-fragment",
            title="Physics / Electric Current From Charge And Time",
            question="What is electric current from charge and time?",
            answer="Current is charge per unit time.",
        )

        motion_rank = self.controller.answer_candidate_rank(
            motion_definition,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        circuit_rank = self.controller.answer_candidate_rank(
            circuit_fragment,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(motion_rank, circuit_rank)

    def test_ratio_of_change_prompt_contextualizes_example_component_with_focus(self) -> None:
        """
        High Level Purpose:
            In circumstances like decomposing a formula-plus-example prompt into reusable child nodes, helps with proving that the example child keeps the governing ratio-of-change focus instead of collapsing into an under-specified generic example request.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_ratio_of_change_prompt_contextualizes_example_component_with_focus()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it."

        structured = self.controller.structured_learning_view_for_text(prompt)

        self.assertIn("State General Ratio Change Formula", structured["component_nots"])
        self.assertTrue(
            any(
                "Give One Example Motion" in component and "General Ratio Change Formula" in component
                for component in structured["component_nots"]
            )
        )

    def test_distinguish_prompt_contextualizes_relation_component_with_compared_terms(self) -> None:
        """
        High Level Purpose:
            In circumstances like distinguish prompts that split into a contrast child and a relation child, helps with proving that the relation child keeps the contrasted cases explicit instead of collapsing to a generic reusable-relation fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_distinguish_prompt_contextualizes_relation_component_with_compared_terms()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "What distinguishes a scalar quantity from a vector quantity, and how is this represented in the reusable relation?"

        structured = self.controller.structured_learning_view_for_text(prompt)

        self.assertIn("Distinguishe Scalar Quantity Vector Quantity", structured["component_nots"])
        self.assertTrue(
            any(
                "Thi Represent Reusable Relation" in component
                and "Scalar Quantity" in component
                and "Vector Quantity" in component
                for component in structured["component_nots"]
            )
        )

    def test_formula_child_prompt_prefers_ratio_family_over_state_plus_change_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed formula child under a broader physics explanation prompt, helps with proving that ranking prefers the requested ratio-of-change family over a loose state-plus-change fragment that only overlaps on generic change vocabulary.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_formula_child_prompt_prefers_ratio_family_over_state_plus_change_fragment()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it. / State General Ratio Change Formula"
        ratio_family = make_knowledge_artifact(
            artifact_id="artifact-ratio-family",
            title="Physics Relations Rate of Change in Motion / Ratio Of Change",
            question="What is Ratio Of Change?",
            answer="The general ratio-of-change relation is a change divided by the change in the governing quantity.",
        )
        state_plus_change = make_knowledge_artifact(
            artifact_id="artifact-state-plus-change",
            title="Physics Relations Linear Motion Under Constant Acceleration / Earlier Motion Quantities",
            question="What is S later from S initial and change?",
            answer="A later state is an earlier state plus a change term.",
        )

        ratio_rank = self.controller.answer_candidate_rank(
            ratio_family,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        state_plus_change_rank = self.controller.answer_candidate_rank(
            state_plus_change,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(ratio_rank, state_plus_change_rank)

    def test_focused_direct_knowledge_candidates_filter_state_plus_change_for_ratio_formula_child(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed formula child under a broader ratio-of-change prompt, helps with proving that the direct-knowledge candidate filter keeps the ratio family and drops a change-only fragment that lacks the governing ratio focus.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it. / State General Ratio Change Formula"
        ratio_family = make_knowledge_artifact(
            artifact_id="artifact-ratio-family",
            title="Physics Relations Rate of Change in Motion / Ratio Of Change",
            question="What is Ratio Of Change?",
            answer="When a quantity is defined as change per unit of another quantity, the reusable family is ratio-of-change.",
        )
        state_plus_change = make_knowledge_artifact(
            artifact_id="artifact-state-plus-change",
            title="Physics Relations / S Times Ext Times Later From S And Ext And Initial And Change",
            question="What is S Times Ext Times Later From S And Ext And Initial And Change?",
            answer="A later state can be obtained from an earlier state plus a change term.",
        )

        self.state.learned_artifacts[ratio_family.id] = ratio_family
        self.state.learned_artifacts[state_plus_change.id] = state_plus_change

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[("covers_components", state_plus_change)],
            include_unmatched_pool=True,
        )

        self.assertTrue(candidates)
        self.assertEqual(ratio_family.id, candidates[0][1].id)
        self.assertNotIn(state_plus_change.id, [artifact.id for _, artifact in candidates[:1]])

    def test_example_child_prompt_prefers_motion_example_over_generic_ratio_definition(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed example child under a formula-plus-example physics prompt, helps with proving that ranking prefers a concrete motion example over the reusable substrate definition itself.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_example_child_prompt_prefers_motion_example_over_generic_ratio_definition()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "State the general ratio-of-change formula and give one example from motion that uses it. "
            "/ Give One Example Motion Using General Ratio Of Change Formula"
        )
        ratio_family = make_knowledge_artifact(
            artifact_id="artifact-ratio-family",
            title="Physics Relations Rate of Change in Motion / Ratio Of Change",
            question="What is Ratio Of Change?",
            answer="The general ratio-of-change relation is a change divided by the change in the governing quantity.",
        )
        motion_example = make_knowledge_artifact(
            artifact_id="artifact-motion-example",
            title="Physics Relations — Rate of Change in Motion / Velocity from displacement and time",
            question="What is Velocity from displacement and time?",
            answer="A motion example is velocity from displacement and time, where velocity is displacement per unit time.",
        )

        ratio_rank = self.controller.answer_candidate_rank(
            ratio_family,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        example_rank = self.controller.answer_candidate_rank(
            motion_example,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(example_rank, ratio_rank)

    def test_decompose_or_refine_preserves_contextualized_example_child_focus(self) -> None:
        """
        High Level Purpose:
            In circumstances like fallback root decomposition for a formula-plus-example prompt, helps with proving that the generated example child keeps the governing formula focus instead of collapsing to a weaker store-reused leaf.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_decompose_or_refine_preserves_contextualized_example_child_focus()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "State the general ratio-of-change formula and give one example from motion that uses it."
        state = SystemState.bootstrap(prompt)
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        controller.ensure_not_elaboration(root)

        children = controller.decompose_or_refine(root)
        child_units = {child.semantic_unit for child in children}

        self.assertTrue(
            any(
                "Give One Example Motion" in unit and "General Ratio Change Formula" in unit
                for unit in child_units
            )
        )

    def test_distinguish_relation_child_prefers_scalar_vector_substrate_over_multiplicative_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed distinguish child asking how the contrast is represented in the reusable relation, helps with proving that ranking prefers the scalar/vector substrate over an unrelated multiplicative family.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_distinguish_relation_child_prefers_scalar_vector_substrate_over_multiplicative_family()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "What distinguishes a scalar quantity from a vector quantity, and how is this represented in the reusable relation? "
            "/ Thi Represent Reusable Relation For A Scalar Quantity And A Vector Quantity"
        )
        scalar_vector = make_knowledge_artifact(
            artifact_id="artifact-scalars-vectors",
            title="Physics Relations Scalars And Vectors / Q From Magnitude",
            question="What is Q From Magnitude?",
            answer="A physical quantity can either be treated as magnitude-only or as magnitude-with-direction.",
        )
        multiplicative = make_knowledge_artifact(
            artifact_id="artifact-multiplicative-combination",
            title="Physics / Multiplicative Combination",
            question="What is multiplicative combination?",
            answer="A quantity equals one factor multiplied by another.",
        )

        scalar_vector_rank = self.controller.answer_candidate_rank(
            scalar_vector,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        multiplicative_rank = self.controller.answer_candidate_rank(
            multiplicative,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(scalar_vector_rank, multiplicative_rank)

    def test_focused_direct_knowledge_candidates_prefer_scalar_vector_family_over_q_from_magnitude_child(self) -> None:
        """
        High Level Purpose:
            In circumstances like a decomposed distinguish child, helps with proving that the focused direct-knowledge selector prefers the explicit scalar/vector family summary over a narrower symbolic relation leaf.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "What distinguishes a scalar quantity from a vector quantity, and how is this represented in the reusable relation? "
            "/ Distinguishe Scalar Quantity Vector Quantity"
        )
        family_summary = make_knowledge_artifact(
            artifact_id="artifact-scalars-vectors-family",
            title="Physics Relations Scalars And Vectors / Physics Relations Scalars And Vectors",
            question="What is Physics Relations Scalars And Vectors?",
            answer="Scalar-versus-vector is a reusable representational substrate that later motion laws reuse when direction matters.",
        )
        family_summary.content["source_title"] = "Physics Relations — Scalars and Vectors"
        q_from_magnitude = make_knowledge_artifact(
            artifact_id="artifact-q-from-magnitude",
            title="Physics Relations Scalars And Vectors / Q From Magnitude",
            question="What is Q From Magnitude?",
            answer="A physical quantity can either be treated as magnitude-only or as magnitude-with-direction.",
        )
        q_from_magnitude.content["source_title"] = "Physics Relations — Scalars and Vectors"

        self.state.learned_artifacts[family_summary.id] = family_summary
        self.state.learned_artifacts[q_from_magnitude.id] = q_from_magnitude

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[("covers_components", q_from_magnitude)],
            include_unmatched_pool=True,
        )

        self.assertTrue(candidates)
        self.assertEqual(family_summary.id, candidates[0][1].id)

    def test_focused_direct_knowledge_candidates_filter_adjacent_impulse_family_for_work_energy_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like a multi-part work-energy explanation prompt, helps with proving that the focused direct-knowledge selector rejects an adjacent impulse theorem that overlaps only on generic change/theorem vocabulary.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain how work relates to energy change and state the work-energy theorem in terms of the transfer substrate."
        work_energy = make_knowledge_artifact(
            artifact_id="artifact-work-energy-theorem",
            title="Physics Relations Work And Energy Transfer / Work-energy theorem",
            question="What is Work-energy theorem?",
            answer="Net work changes kinetic energy. This reuses the transfer substrate: work is the change term for kinetic energy.",
        )
        work_energy.content["source_title"] = "Physics Relations — Work and Energy Transfer"
        impulse = make_knowledge_artifact(
            artifact_id="artifact-impulse-theorem",
            title="Physics Relations Momentum And Impulse / Impulse-momentum theorem",
            question="What is Impulse-momentum theorem?",
            answer="Impulse equals change in momentum. This reuses the earlier interaction-causes-change substrate.",
        )
        impulse.content["source_title"] = "Physics Relations — Momentum and Impulse"

        self.state.learned_artifacts[work_energy.id] = work_energy
        self.state.learned_artifacts[impulse.id] = impulse

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[
                ("focus_alignment", impulse),
                ("focus_alignment", work_energy),
            ],
            include_unmatched_pool=False,
        )

        self.assertTrue(candidates)
        self.assertEqual(work_energy.id, candidates[0][1].id)
        self.assertNotEqual(impulse.id, candidates[0][1].id)

    def test_focused_direct_knowledge_candidates_filter_generic_multiplicative_family_for_constant_acceleration_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like a constant-acceleration explanation prompt that asks for both the update equation and the underlying state-plus-change structure, helps with proving that the focused selector rejects a generic multiplicative-combination fragment from another family.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Using the constant acceleration relation, write the equation connecting initial velocity, acceleration, "
            "time, and final velocity, and identify the state-plus-change structure underneath it."
        )
        multiplicative = make_knowledge_artifact(
            artifact_id="artifact-momentum-multiplicative",
            title="Physics Relations Momentum And Impulse / Multiplicative Combination",
            question="What is Multiplicative Combination?",
            answer="Momentum and impulse reuse multiplicative combination and connect interaction over time to change in motion state.",
        )
        linear_state_update = make_knowledge_artifact(
            artifact_id="artifact-constant-accel-state-update",
            title="Physics Relations Linear Motion Under Constant Acceleration / S Times Ext Times Later From S And Ext And Initial And Change",
            question="What is S Times Ext Times Later From S And Ext And Initial And Change?",
            answer="A later state can be obtained from an earlier state plus a change term.",
        )

        self.state.learned_artifacts[multiplicative.id] = multiplicative
        self.state.learned_artifacts[linear_state_update.id] = linear_state_update

        candidates = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[
                ("focus_alignment", multiplicative),
                ("focus_alignment", linear_state_update),
            ],
            include_unmatched_pool=False,
        )

        self.assertTrue(candidates)
        self.assertEqual(linear_state_update.id, candidates[0][1].id)
        self.assertNotEqual(multiplicative.id, candidates[0][1].id)

    def test_answer_candidate_rank_prefers_work_energy_theorem_over_adjacent_ratio_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like a direct explanatory work-energy prompt, helps with proving that answer ranking prefers the work-energy theorem over an adjacent circuit ratio fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain how work relates to energy change and state the work-energy theorem in terms of the transfer substrate."
        work_energy = make_knowledge_artifact(
            artifact_id="artifact-work-energy-theorem-rank",
            title="Physics Relations Work And Energy Transfer / Work-energy theorem",
            question="What is Work-energy theorem?",
            answer="Net work changes kinetic energy. This reuses the transfer substrate: work is the change term for kinetic energy.",
        )
        work_energy.content["source_title"] = "Physics Relations — Work and Energy Transfer"
        ratio = make_knowledge_artifact(
            artifact_id="artifact-electric-ratio-rank",
            title="Physics Relations Electric Circuits / Ratio",
            question="What is Ratio?",
            answer="Circuit laws reuse ratio, multiplicative combination, and substitution to connect drive, response, and energy transfer.",
        )
        ratio.content["source_title"] = "Physics Relations — Electric Circuits"

        work_energy_rank = self.controller.answer_candidate_rank(
            work_energy,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        ratio_rank = self.controller.answer_candidate_rank(
            ratio,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(work_energy_rank, ratio_rank)

    def test_answer_candidate_rank_prefers_constant_acceleration_family_over_multiplicative_fragment(self) -> None:
        """
        High Level Purpose:
            In circumstances like a constant-acceleration explanation prompt, helps with proving that answer ranking prefers the constant-acceleration state-update family over an unrelated multiplicative-combination fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Using the constant acceleration relation, write the equation connecting initial velocity, acceleration, "
            "time, and final velocity, and identify the state-plus-change structure underneath it."
        )
        multiplicative = make_knowledge_artifact(
            artifact_id="artifact-momentum-multiplicative-rank",
            title="Physics Relations Momentum And Impulse / Multiplicative Combination",
            question="What is Multiplicative Combination?",
            answer="Momentum and impulse reuse multiplicative combination and connect interaction over time to change in motion state.",
        )
        linear_state_update = make_knowledge_artifact(
            artifact_id="artifact-constant-accel-state-update-rank",
            title="Physics Relations Linear Motion Under Constant Acceleration / S Times Ext Times Later From S And Ext And Initial And Change",
            question="What is S Times Ext Times Later From S And Ext And Initial And Change?",
            answer="A later state can be obtained from an earlier state plus a change term.",
        )

        linear_rank = self.controller.answer_candidate_rank(
            linear_state_update,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        multiplicative_rank = self.controller.answer_candidate_rank(
            multiplicative,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(linear_rank, multiplicative_rank)

    def test_compose_direct_knowledge_answer_does_not_add_cross_family_supplement(self) -> None:
        """
        High Level Purpose:
            In circumstances like a direct-knowledge work-energy answer, helps with proving that composition does not append cross-family supplements from unrelated source titles.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain how work relates to energy change and state the work-energy theorem in terms of the transfer substrate."
        work_energy = make_knowledge_artifact(
            artifact_id="artifact-work-energy-compose",
            title="Physics Relations Work And Energy Transfer / Work-energy theorem",
            question="What is Work-energy theorem?",
            answer="Net work changes kinetic energy. This reuses the transfer substrate: work is the change term for kinetic energy.",
        )
        work_energy.content["source_title"] = "Physics Relations — Work and Energy Transfer"
        ratio = make_knowledge_artifact(
            artifact_id="artifact-electric-ratio-compose",
            title="Physics Relations Electric Circuits / Ratio",
            question="What is Ratio?",
            answer="Circuit laws reuse ratio, multiplicative combination, and substitution to connect drive, response, and energy transfer.",
        )
        ratio.content["source_title"] = "Physics Relations — Electric Circuits"
        impulse = make_knowledge_artifact(
            artifact_id="artifact-impulse-theorem-compose",
            title="Physics Relations Momentum And Impulse / Impulse-momentum theorem",
            question="What is Impulse-momentum theorem?",
            answer="Impulse equals change in momentum. This reuses the earlier interaction-causes-change substrate.",
        )
        impulse.content["source_title"] = "Physics Relations — Momentum and Impulse"

        answer = self.controller.compose_direct_knowledge_answer(
            semantic_unit=prompt,
            primary_artifact=work_energy,
            primary_answer=work_energy.content["answer"],
            focus_candidates=[ratio, impulse],
        )

        self.assertIn("Work-energy theorem", answer)
        self.assertNotIn("Impulse-momentum theorem", answer)
        self.assertNotIn("Circuit laws reuse ratio", answer)

    def test_construct_prompt_prefers_explanatory_knowledge_over_bare_electric_power_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like electric-power composition prompts, helps with proving that a direct explanatory construct prompt prefers an answer-bearing knowledge artifact over a bare executable ability fragment with no explanatory answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = (
            "Explain how electric power expressions ( P = VI ), ( P = I^2 R ), and ( P = V^2 / R ) are derived "
            "through composition of the driving-response relation and multiplicative combination. Provide the full reasoning chain."
        )
        explanatory = make_knowledge_artifact(
            artifact_id="artifact-electric-power-chain-summary",
            title="Physics Relations — Electric Circuits / Ratio",
            question="What is Electric Power composition?",
            answer="Electric power composes drive-response with multiplicative combination: first P = V I, then substitute V = I R or I = V / R to derive P = I^2 R and P = V^2 / R.",
        )
        explanatory.content["source_title"] = "Physics Relations — Electric Circuits"
        python_script = self.controller.expression_ability_script(
            title="Physics Relations — Electric Circuits / Electric Power",
            scope="reuse for electric power calculations",
            input_contract={"V": "number", "I": "number"},
            output_contract={"P": "number"},
            expression="V * I",
            output_field="P",
        )
        bare_ability = Artifact(
            id="artifact-electric-power-ability-no-answer",
            artifact_type=ArtifactType.ABILITY,
            title="Physics Relations — Electric Circuits / Electric Power",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for electric power calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate P from V and I?",
                "answer": "",
                "python_script": python_script,
                "input_contract": {"V": "number", "I": "number"},
                "output_contract": {"P": "number"},
                "source_title": "Physics Relations — Electric Circuits",
                "title_current_identity": "Electric Power",
                "structured_learning": {
                    "encountered_not": "Electric Power",
                    "lookup_keys": ["electric power", "power from voltage current"],
                    "component_nots": ["Voltage", "Current"],
                    "composed_not": "Electric Power",
                    "notation_yaml": "",
                },
            },
            justification="Bare executable electric-power artifact without explanatory answer.",
        )

        explanatory_rank = self.controller.answer_candidate_rank(
            explanatory,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        ability_rank = self.controller.answer_candidate_rank(
            bare_ability,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(explanatory_rank, ability_rank)

    def test_distinguish_prompt_prefers_explanatory_knowledge_over_bare_force_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like force-law contrast prompts, helps with proving that a distinguish prompt prefers an answer-bearing knowledge artifact over a bare executable ability that only computes one side of the contrast.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Explain the difference between the general force law ( F = ma ) and the specific case of weight ( W = mg )."
        explanatory = make_knowledge_artifact(
            artifact_id="artifact-force-weight-contrast-summary",
            title="Physics Relations — Force and Mass-Acceleration Relation / Determinate Specialization Of The Broader Force",
            question="What is the difference between the general force law and weight?",
            answer="The general law F = ma states that force is mass times whatever acceleration is present; weight W = mg is the special case where the acceleration is specifically gravitational g.",
        )
        explanatory.content["source_title"] = "Physics Relations — Force and Mass-Acceleration Relation"
        python_script = self.controller.expression_ability_script(
            title="Physics Relations — Force and Mass-Acceleration Relation / Weight As A Special Force",
            scope="reuse for weight calculations",
            input_contract={"m": "number", "g": "number"},
            output_contract={"W": "number"},
            expression="m * g",
            output_field="W",
        )
        bare_ability = Artifact(
            id="artifact-weight-special-case-ability-no-answer",
            artifact_type=ArtifactType.ABILITY,
            title="Physics Relations — Force and Mass-Acceleration Relation / Weight As A Special Force",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for weight calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate W from m and g?",
                "answer": "",
                "python_script": python_script,
                "input_contract": {"m": "number", "g": "number"},
                "output_contract": {"W": "number"},
                "source_title": "Physics Relations — Force and Mass-Acceleration Relation",
                "title_current_identity": "Weight As A Special Force",
                "structured_learning": {
                    "encountered_not": "Weight As A Special Force",
                    "lookup_keys": ["weight as a special force", "weight from mass gravity"],
                    "component_nots": ["Mass", "Gravity"],
                    "composed_not": "Weight As A Special Force",
                    "notation_yaml": "",
                },
            },
            justification="Bare executable weight artifact without explanatory contrast answer.",
        )

        explanatory_rank = self.controller.answer_candidate_rank(
            explanatory,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        ability_rank = self.controller.answer_candidate_rank(
            bare_ability,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(explanatory_rank, ability_rank)

    def test_identify_reusable_substrate_prompt_prefers_gravitation_summary_over_gravity_ability(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts for gravitation, helps with proving that ranking prefers an answer-bearing gravitation summary over a bare executable gravitational-law ability.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        explanatory = make_knowledge_artifact(
            artifact_id="artifact-gravitation-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        explanatory.content["source_title"] = "Physics Relations — Gravitation"
        python_script = self.controller.expression_ability_script(
            title="Physics Relations — Gravitation / Gravitational Field Strength",
            scope="reuse for gravitational field strength calculations",
            input_contract={"G": "number", "M": "number", "r": "number"},
            output_contract={"g": "number"},
            expression="G * M / (r ** 2)",
            output_field="g",
        )
        bare_ability = Artifact(
            id="artifact-gravitational-field-strength-no-answer",
            artifact_type=ArtifactType.ABILITY,
            title="Physics Relations — Gravitation / Gravitational Field Strength",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="reuse for gravitational field strength calculations",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": "How do you calculate g from G, M, r?",
                "answer": "",
                "python_script": python_script,
                "input_contract": {"G": "number", "M": "number", "r": "number"},
                "output_contract": {"g": "number"},
                "source_title": "Physics Relations — Gravitation",
                "title_current_identity": "Gravitational Field Strength",
                "structured_learning": {
                    "encountered_not": "Gravitational Field Strength",
                    "lookup_keys": ["gravitational field strength", "gravity inverse square"],
                    "component_nots": ["G", "M", "r"],
                    "composed_not": "Gravitational Field Strength",
                    "notation_yaml": "",
                },
            },
            justification="Bare executable gravitation artifact without explanatory substrate answer.",
        )

        explanatory_rank = self.controller.answer_candidate_rank(
            explanatory,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        ability_rank = self.controller.answer_candidate_rank(
            bare_ability,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(explanatory_rank, ability_rank)

    def test_identify_reusable_substrate_prompt_prefers_substrate_summary_over_determinate_formula_knowledge(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts over a family that also contains determinate law summaries, helps with proving that ranking prefers the broader substrate explanation over a narrower formula-only law description.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        substrate_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-substrate-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        substrate_summary.content["source_title"] = "Physics Relations — Gravitation"
        determinate_formula = make_knowledge_artifact(
            artifact_id="artifact-newtonian-gravitation-formula",
            title="Physics Relations — Gravitation / Newtonian Gravitation",
            question="What is Newtonian gravitation?",
            answer="The gravitational force between two masses is: $$ F = G * m1 * m2 / (r ** 2) $$",
        )
        determinate_formula.content["source_title"] = "Physics Relations — Gravitation"

        substrate_rank = self.controller.answer_candidate_rank(
            substrate_summary,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        determinate_rank = self.controller.answer_candidate_rank(
            determinate_formula,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(substrate_rank, determinate_rank)

    def test_identify_reusable_substrate_prompt_prefers_substrate_summary_over_family_law_distinction_summary(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts over a family store that also contains malformed family-level law-distinction summaries, helps with proving that ranking still prefers the broader substrate explanation over the narrower distinction fragment.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        substrate_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-substrate-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        substrate_summary.content["source_title"] = "Physics Relations — Gravitation"
        family_distinction_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-family-distinction-summary",
            title="Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="gravitational force uses two masses gravitational field strength uses one source mass and one observation location",
        )
        family_distinction_summary.content["source_title"] = "Physics Relations — Gravitation"

        substrate_rank = self.controller.answer_candidate_rank(
            substrate_summary,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        distinction_rank = self.controller.answer_candidate_rank(
            family_distinction_summary,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(substrate_rank, distinction_rank)

    def test_identify_reusable_substrate_composition_prefers_substrate_summary_over_formula_supplement(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts whose initially selected family artifact is only a narrow law-distinction fragment, helps with proving that direct-knowledge composition lifts in the broader substrate summary instead of falling through to a formula-style supplement.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        primary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-family-distinction-summary",
            title="Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="gravitational force uses two masses gravitational field strength uses one source mass and one observation location",
        )
        primary.content["source_title"] = "Physics Relations — Gravitation"
        substrate_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-substrate-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        substrate_summary.content["source_title"] = "Physics Relations — Gravitation"
        formula_fragment = make_knowledge_artifact(
            artifact_id="artifact-gravitational-field-strength-formula",
            title="Physics Relations — Gravitation / Gravitational Field Strength",
            question="How do you calculate g from G, M, r?",
            answer="How do you calculate g from G, M, r?. g = G * M / (r ** 2). inputs: G, M, r. output: g",
        )
        formula_fragment.content["source_title"] = "Physics Relations — Gravitation"

        composed = self.controller.compose_direct_knowledge_answer(
            semantic_unit=prompt,
            primary_artifact=primary,
            primary_answer=str(primary.content.get("answer", "")).strip(),
            focus_candidates=[substrate_summary, formula_fragment],
        )

        self.assertEqual(
            composed,
            "Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )

    def test_identify_reusable_substrate_focus_candidates_admit_broad_substrate_summary(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts whose broader family summary does not repeat the narrow focus phrase verbatim, helps with proving that the focused-candidate filter still admits the substrate-marked family summary so later ranking and composition can use it.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        substrate_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-substrate-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        substrate_summary.content["source_title"] = "Physics Relations — Gravitation"
        family_distinction_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-family-distinction-summary",
            title="Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="gravitational force uses two masses gravitational field strength uses one source mass and one observation location",
        )
        family_distinction_summary.content["source_title"] = "Physics Relations — Gravitation"

        focused = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[
                ("focus_alignment", family_distinction_summary),
                ("focus_alignment", substrate_summary),
            ],
            include_unmatched_pool=False,
        )

        self.assertEqual([artifact.id for _, artifact in focused[:2]], [
            "artifact-gravitation-substrate-summary",
            "artifact-gravitation-family-distinction-summary",
        ])

    def test_identify_reusable_substrate_focus_candidates_reject_wrong_force_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like reusable-substrate prompts whose narrow focus contains a generic term such as `force`, helps with proving that focused-candidate admission still keeps the broader substrate summary inside the correct family instead of drifting into another force-related family.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.
        """
        prompt = "Identify the reusable substrate underlying gravitational force and explain how both multiplicative combination and inverse-square dependence appear in the law."
        gravitation_summary = make_knowledge_artifact(
            artifact_id="artifact-gravitation-substrate-summary",
            title="Physics Relations — Gravitation / Physics Relations Gravitation",
            question="What is Physics Relations Gravitation?",
            answer="Gravitation reuses multiplicative combination together with inverse-square separation structure.",
        )
        gravitation_summary.content["source_title"] = "Physics Relations — Gravitation"
        wrong_force_summary = make_knowledge_artifact(
            artifact_id="artifact-force-family-substrate-summary",
            title="Physics Relations — Force and Mass-Acceleration Relation / Determinate Specialization Of The Broader Force",
            question="What is Determinate Specialization Of The Broader Force?",
            answer="Force laws reuse multiplicative combination, and weight is a determinate specialization of the broader force relation.",
        )
        wrong_force_summary.content["source_title"] = "Physics Relations — Force and Mass-Acceleration Relation"

        focused = self.controller.focused_direct_knowledge_candidates(
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
            candidate_pairs=[
                ("focus_alignment", wrong_force_summary),
                ("focus_alignment", gravitation_summary),
            ],
            include_unmatched_pool=False,
        )

        self.assertEqual([artifact.id for _, artifact in focused], [
            "artifact-gravitation-substrate-summary",
        ])

    def test_derive_prompt_with_named_inputs_still_prefers_direct_knowledge_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like derivation prompts that mention symbolic givens such as `n_A`, `n_B`, and coefficients, helps with proving that the runtime still routes them through direct explanatory reuse instead of collapsing them into bare compute execution.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derive_prompt_with_named_inputs_still_prefers_direct_knowledge_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = "Using the stoichiometric ratio relation, derive how to compute the amount of substance ( n_B ) from a known ( n_A ) and coefficients."
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "derive")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))

    def test_given_relation_prompt_routes_as_derivation_not_bare_compute(self) -> None:
        """
        High Level Purpose:
            In circumstances like explanation prompts that say a relation is given and ask to express a computed form plus its reusable substrate, helps with proving that the runtime keeps the prompt on the derivation/explanation path instead of collapsing it into a concrete compute request.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_given_relation_prompt_routes_as_derivation_not_bare_compute()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt = (
            "Given the relation for molar mass, express how to compute mass from moles and molar mass, "
            "and explain how this relates to the reusable substrate."
        )
        directive = semantic_prompt_directive_profile(prompt)
        self.assertEqual(directive["kind"], "derive")
        self.assertTrue(directive["requires_formula"])
        self.assertTrue(directive["requires_substrate"])
        self.assertEqual(semantic_prompt_action_posture(prompt), "direct_resolution")
        self.assertTrue(semantic_prompt_prefers_direct_knowledge_answer(prompt))

    def test_derive_prompt_composition_preserves_relation_chain(self) -> None:
        """
        High Level Purpose:
            In circumstances like derivation prompts that should expose intermediate semantic dependence, helps with proving that direct answer composition can keep both the governing ratio and the solved target relation visible in the returned answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derive_prompt_composition_preserves_relation_chain()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        ratio_relation = make_knowledge_artifact(
            artifact_id="artifact-stoich-ratio",
            title="Chemistry / Mole Ratio From Coefficients",
            question="What is the stoichiometric ratio relation?",
            answer="The governing ratio is n_A / n_B = nu_A / nu_B.",
        )
        solved_relation = make_knowledge_artifact(
            artifact_id="artifact-stoich-solved",
            title="Chemistry / Solving For An Unknown Amount",
            question="How do you solve for n_B from n_A and the coefficients?",
            answer="Then, solve for the target amount: n_B = n_A * nu_B / nu_A.",
        )

        composed = self.controller.compose_direct_knowledge_answer(
            semantic_unit="Using the stoichiometric ratio relation, derive how to compute the amount of substance ( n_B ) from a known ( n_A ) and coefficients.",
            primary_artifact=ratio_relation,
            primary_answer=ratio_relation.content["answer"],
            focus_candidates=[solved_relation],
        )

        self.assertIn("n_A / n_B = nu_A / nu_B", composed)
        self.assertIn("n_B = n_A * nu_B / nu_A", composed)

    def test_distinguish_prompt_composition_keeps_both_terms_explicit(self) -> None:
        """
        High Level Purpose:
            In circumstances like contrastive prompts over nearby reusable families, helps with proving that direct answer composition keeps both sides explicit instead of collapsing the answer into one side or a generic family description.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_distinguish_prompt_composition_keeps_both_terms_explicit()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        ratio_artifact = make_knowledge_artifact(
            artifact_id="artifact-stoich-ratio-side",
            title="Chemistry / Stoichiometric Ratio",
            question="What is stoichiometric ratio?",
            answer="Stoichiometric ratio fixes the proportional relationship between reactant and product amounts from the balanced coefficients.",
        )
        limiting_artifact = make_knowledge_artifact(
            artifact_id="artifact-limiting-reagent-side",
            title="Chemistry / Limiting Reagent",
            question="What is limiting reagent?",
            answer="Limiting reagent identifies which reactant runs out first and therefore caps the maximum product that can be formed.",
        )

        composed = self.controller.compose_direct_knowledge_answer(
            semantic_unit="Distinguish between stoichiometric ratio and limiting reagent in reaction reasoning.",
            primary_artifact=ratio_artifact,
            primary_answer=ratio_artifact.content["answer"],
            focus_candidates=[limiting_artifact],
        )

        self.assertIn("Stoichiometric Ratio", composed)
        self.assertIn("Limiting Reagent", composed)
        self.assertIn("proportional", composed.lower())
        self.assertIn("runs out first", composed.lower())

    def test_state_prompt_prefers_narrow_law_over_broad_family(self) -> None:
        """
        High Level Purpose:
            In circumstances like state-and-explain prompts that mention both a specific law and its broader reusable family, helps with proving that the runtime ranks the determinate law above the broad family answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_state_prompt_prefers_narrow_law_over_broad_family()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        broad_family = make_knowledge_artifact(
            artifact_id="artifact-multiplicative-family",
            title="Physics / Multiplicative Combination",
            question="What is multiplicative combination?",
            answer="Multiplicative combination is the broader substrate where one quantity is obtained by multiplying governing factors.",
        )
        narrow_law = make_knowledge_artifact(
            artifact_id="artifact-newton-second-law",
            title="Physics / Newton Second Law",
            question="What is Newton's second law?",
            answer="Newton's second law states F = m * a, and it is a determinate force law inside the broader multiplicative-combination family.",
        )

        prompt = "State Newton's second law and explain how it fits the multiplicative-combination substrate."
        broad_rank = self.controller.answer_candidate_rank(
            broad_family,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )
        narrow_rank = self.controller.answer_candidate_rank(
            narrow_law,
            semantic_unit=prompt,
            current_boundary_shape=self.state.root().boundary_shape,
        )

        self.assertLess(narrow_rank, broad_rank)


if __name__ == "__main__":
    unittest.main()
