# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.non_achievedness_normalization import normalize_not_elaboration_payload
from realized_core_engine.state import SystemState
from realized_core_semantics import title_semantics
from realized_core_semantics.applied_model import Artifact, ArtifactType, BoundaryShapeTerm, LLMSupplementResult
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
)
from realized_core_semantics.title_semantics import derive_semantic_title_depth_view


def make_prolog_artifact(*, artifact_id: str, title: str, answer: str = "") -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over symbolic title matching and reusable clause identity, helps with creating a stored artifact whose formal title is already Prolog-shaped.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

    Example Input Output:
        Input: `make_prolog_artifact(artifact_id='artifact-add', title='math:add:add(A, B, C) :- C is A + B', answer='C is A + B')`
        Output: Artifact(id='artifact-add', title='math:add:add(A, B, C) :- C is A + B', artifact_type='knowledge', representation='yaml')

    Args:
        artifact_id: Value for `artifact_id` used by `make_prolog_artifact`. Expected type: `str`.
        title: Value for `title` used by `make_prolog_artifact`. Expected type: `str`.
        answer: Value for `answer` used by `make_prolog_artifact`. Expected type: `str`. Defaults to `''`.

    Returns:
        Artifact: Result produced by `make_prolog_artifact`.
    """
    return Artifact(
        id=artifact_id,
        artifact_type=ArtifactType.KNOWLEDGE,
        title=title,
        representation=ArtifactRepresentation.YAML,
        function_bit=0,
        scope="test prolog reuse",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content={
            "question": "What clause matches this symbolic head?",
            "answer": answer,
            "structured_learning": {
                "title_identity": title,
            },
        },
        justification="test artifact",
        boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
    )


def make_prolog_force_ability_artifact() -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over natural-language prompts that should bridge into symbolic Prolog retrieval, helps with creating a reusable executable ability artifact backed by a Prolog formal identity.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

    Example Input Output:
        Input: `make_prolog_force_ability_artifact()`
        Output: Artifact(id='artifact-force-prolog', title=\"Newton's Laws of Motion / Force-Mass-Acceleration Relationship\", artifact_type='ability', representation='python_script')

    Args:
        None.

    Returns:
        Artifact: Result produced by `make_prolog_force_ability_artifact`.
    """
    formal_title_identity = "newtons_laws_of_motion:force_mass_acceleration_relationship(Mass, Acceleration, Force) :- Force is Mass * Acceleration"
    return Artifact(
        id="artifact-force-prolog",
        artifact_type=ArtifactType.ABILITY,
        title="Newton's Laws of Motion / Force-Mass-Acceleration Relationship",
        representation=ArtifactRepresentation.PYTHON_SCRIPT,
        function_bit=1,
        scope="reuse when force should be computed from mass and acceleration",
        provenance=["test"],
        reusability=ArtifactReuse.BROAD_REUSE,
        admissibility=ArtifactAdmission.ADMITTED,
        template_schema={},
        learning_relation=LearningRelation.NEW_FAMILY,
        related_artifact_ids=[],
        content={
            "question": "How do you calculate F from m, a?",
            "formal_title_identity": formal_title_identity,
            "python_script": """
# /// script
# requires-python = ">=3.11"
# dependencies = ["msgspec", "orjson"]
# ///
from __future__ import annotations
import sys
import msgspec
import orjson

class OutputPayload(msgspec.Struct, kw_only=True):
    status: str
    answer: str
    result: dict[str, float]
    notes: list[str] = []

def main() -> None:
    payload = orjson.loads(sys.stdin.buffer.read() or b"{}")
    m = float(payload.get("m", 0))
    a = float(payload.get("a", 0))
    force = m * a
    if force.is_integer():
        answer = str(int(force))
        force_value = int(force)
    else:
        answer = str(force)
        force_value = force
    result = OutputPayload(status="ok", answer=answer, result={"F": force_value})
    sys.stdout.buffer.write(orjson.dumps(msgspec.to_builtins(result)))
    sys.stdout.buffer.write(b"\\n")

if __name__ == "__main__":
    main()
            """.strip(),
            "entrypoint": "main",
            "script_language": "python",
            "dependencies": ["msgspec", "orjson"],
            "input_contract": {"m": "number", "a": "number"},
            "output_contract": {"F": "number"},
            "structured_learning": {
                "title_identity": formal_title_identity,
                "encountered_not": "Force Mass Acceleration Relationship",
                "lookup_keys": ["force mass acceleration relationship", "mass", "acceleration", "force"],
                "component_nots": ["Mass", "Acceleration", "Force"],
                "composed_not": "Force Mass Acceleration Relationship",
                "notation_yaml": "",
            },
        },
        justification="Reusable force ability for Prolog-backed retrieval tests.",
        boundary_shape=(BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE),
    )


class PrologTitleRepresentationTests(unittest.TestCase):
    def test_title_depth_prompt_block_switches_to_prolog_guidance(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic title prompting and semantic decomposition guidance, helps with testing title depth prompt block switches to prolog guidance.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_title_depth_prompt_block_switches_to_prolog_guidance()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            instructions = title_semantics.title_depth_theory_prompt_block()

        self.assertIn("broad:ground:resolved_head", instructions)
        self.assertIn("Head :- Body", instructions)
        self.assertNotIn("A / B / C", instructions)

    def test_derive_semantic_title_depth_view_supports_prolog_namespace_clause(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic title storage and ordered determination, helps with testing derive semantic title depth view supports prolog namespace clause.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derive_semantic_title_depth_view_supports_prolog_namespace_clause()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            view = derive_semantic_title_depth_view(
                "physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration",
                minimal_sufficient_depth=3,
            )

        self.assertEqual(
            view["segments"],
            ["physics", "force", "force_from_mass_and_acceleration(Mass, Acceleration, Force)"],
        )
        self.assertEqual(
            view["prefixes"],
            [
                "physics",
                "physics:force",
                "physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)",
            ],
        )
        self.assertEqual(view["exposed_depth"], 3)
        self.assertEqual(view["minimal_sufficient_depth"], 3)

    def test_normalize_not_elaboration_payload_populates_prolog_title_metadata(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over additive symbolic-title storage, helps with testing normalize not elaboration payload populates prolog title metadata.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_normalize_not_elaboration_payload_populates_prolog_title_metadata()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            normalized = normalize_not_elaboration_payload(
                "compute force from mass and acceleration",
                {
                    "title_identity": "physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration",
                    "encountered_not": "determine force",
                    "goal": "compute force from mass and acceleration",
                },
                boundary_shape=(BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.INPUT_VALUE, BoundaryShapeTerm.OUTPUT_VALUE),
            )

        self.assertEqual(normalized["title_representation_mode"], "prolog")
        self.assertEqual(
            normalized["title_prolog_head"],
            "physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force)",
        )
        self.assertEqual(normalized["title_prolog_body"], "Force is Mass * Acceleration")
        self.assertEqual(normalized["title_prolog_predicate"], "force_from_mass_and_acceleration")
        self.assertEqual(normalized["title_prolog_arity"], 3)
        self.assertEqual(
            normalized["title_prolog_head_canonical"],
            "force_from_mass_and_acceleration(V1, V2, V3)",
        )

    def test_semantic_title_match_score_prefers_unifiable_prolog_head(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic head reuse and candidate selection, helps with testing semantic title match score prefers unifiable prolog head.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_semantic_title_match_score_prefers_unifiable_prolog_head()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Compute force.")
        controller = BSSCController(state, llm_policy="off")

        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            score = controller.semantic_title_match_score(
                hint="force_from_mass_and_acceleration(2, Acceleration, Force)",
                anchor_title="physics:force",
                candidate_title="physics:force:force_from_mass_and_acceleration(Mass, Acceleration, Force) :- Force is Mass * Acceleration",
            )

        self.assertGreaterEqual(score, 95)

    def test_reusable_semantic_title_match_reuses_matching_prolog_head(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic candidate retrieval and reuse, helps with testing reusable semantic title match reuses matching prolog head.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_reusable_semantic_title_match_reuses_matching_prolog_head()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Reuse symbolic clauses.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_artifact(
            artifact_id="artifact-add",
            title="math:add:add(A, B, C) :- C is A + B",
            answer="C is A + B",
        )

        controller.reusable_artifact_candidates = lambda: []
        controller.artifact_store.load_relevant_artifacts = lambda query_text, *, limit=8: [artifact]

        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            reused = controller.reusable_semantic_title_match(
                hint="add(X, Y, Z)",
                anchor_title="math:add",
                exclude_titles=[],
            )

        self.assertEqual(reused, "math:add:add(A, B, C) :- C is A + B")

    def test_artifact_answer_text_instantiates_prolog_body_from_query_head(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic clause retrieval, helps with testing artifact answer text instantiates prolog body from query head.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_artifact_answer_text_instantiates_prolog_body_from_query_head()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Reuse symbolic clauses.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_artifact(
            artifact_id="artifact-add",
            title="math:add:add(A, B, C) :- C is A + B",
            answer="",
        )

        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            answer = controller.artifact_answer_text(
                artifact,
                semantic_unit="math:add:add(2, X, Y)",
            )

        self.assertEqual(answer, "Y is 2 + X")

    def test_answer_reuse_preference_accepts_prolog_clause_body_without_plain_answer(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over symbolic clause reuse, helps with testing answer reuse preference accepts prolog clause body without plain answer.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_answer_reuse_preference_accepts_prolog_clause_body_without_plain_answer()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("math:add:add(2, X, Y)")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_artifact(
            artifact_id="artifact-add",
            title="math:add:add(A, B, C) :- C is A + B",
            answer="",
        )

        with patch.dict(
            os.environ,
            {title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG},
            clear=False,
        ):
            current = normalize_not_elaboration_payload(
                "math:add:add(2, X, Y)",
                {
                    "title_identity": "math:add:add(2, X, Y)",
                    "encountered_not": "math:add:add(2, X, Y)",
                    "goal": "math:add:add(2, X, Y)",
                },
                boundary_shape=(BoundaryShapeTerm.OUTPUT_VALUE,),
            )
            prior = controller.artifact_structured_learning_view(artifact)
            preference = controller.answer_reuse_preference(current, prior, artifact)

        self.assertEqual(preference, "same_key")

    def test_derive_artifact_invocation_payload_uses_prolog_argument_aliases_for_normal_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over natural-language prompts that mention semantic field names rather than symbolic contract keys, helps with testing derive artifact invocation payload uses prolog argument aliases for normal text.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_derive_artifact_invocation_payload_uses_prolog_argument_aliases_for_normal_text()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Calculate force for mass=3 and acceleration=4.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_force_ability_artifact()

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_OFF,
            },
            clear=False,
        ):
            payload = controller.derive_artifact_invocation_payload(
                artifact,
                semantic_unit="Calculate force for mass=3 and acceleration=4.",
            )

        self.assertEqual(payload, {"m": 3, "a": 4})

    def test_artifact_query_semantic_unit_synthesizes_prolog_head_from_normal_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over candidate-first Prolog retrieval for normal prompts, helps with testing artifact query semantic unit synthesizes prolog head from normal text.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_artifact_query_semantic_unit_synthesizes_prolog_head_from_normal_text()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Calculate force for mass=3 and acceleration=4.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_force_ability_artifact()

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_OFF,
            },
            clear=False,
        ):
            query_text = controller.artifact_query_semantic_unit(
                artifact,
                semantic_unit="Calculate force for mass=3 and acceleration=4.",
            )

        self.assertEqual(
            query_text,
            "newtons_laws_of_motion:force_mass_acceleration_relationship(3, 4, Force)",
        )

    def test_artifact_answer_text_executes_prolog_backed_ability_from_normal_text(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over normal-language prompts that should land on a Prolog-backed executable artifact, helps with testing artifact answer text executes prolog backed ability from normal text.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_artifact_answer_text_executes_prolog_backed_ability_from_normal_text()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Calculate force for mass=3 and acceleration=4.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_force_ability_artifact()

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_OFF,
            },
            clear=False,
        ):
            answer = controller.artifact_answer_text(
                artifact,
                semantic_unit="Calculate force for mass=3 and acceleration=4.",
            )

        self.assertEqual(answer, "12")

    def test_lookup_prior_non_achievedness_prefers_prolog_backed_ability_for_normal_compute_prompt(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over root-level reuse for a normal compute prompt, helps with testing lookup prior non achievedness prefers prolog backed ability for normal compute prompt.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_lookup_prior_non_achievedness_prefers_prolog_backed_ability_for_normal_compute_prompt()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Calculate force for mass=3 and acceleration=4.")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_force_ability_artifact()
        state.learned_artifacts[artifact.id] = artifact

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_OFF,
            },
            clear=False,
        ):
            lookup = controller.lookup_prior_non_achievedness(state.root())

        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, artifact.id)

    def test_artifact_answer_text_executes_prolog_backed_ability_from_prolog_head(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over explicitly symbolic prompts, helps with testing artifact answer text executes prolog backed ability from prolog head.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_artifact_answer_text_executes_prolog_backed_ability_from_prolog_head()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("newtons_laws_of_motion:force_mass_acceleration_relationship(3, 4, Force)")
        controller = BSSCController(state, llm_policy="off")
        artifact = make_prolog_force_ability_artifact()

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_OFF,
            },
            clear=False,
        ):
            answer = controller.artifact_answer_text(
                artifact,
                semantic_unit="newtons_laws_of_motion:force_mass_acceleration_relationship(3, 4, Force)",
            )

        self.assertEqual(answer, "12")

    def test_artifact_query_semantic_unit_uses_llm_priming_when_forced(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over optional LLM-backed Prolog query priming, helps with testing artifact query semantic unit uses llm priming when forced.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_artifact_query_semantic_unit_uses_llm_priming_when_forced()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Please compute force from the given mass and acceleration.")
        controller = BSSCController(state, llm_policy="auto")
        artifact = make_prolog_force_ability_artifact()
        controller.llm.enabled = True
        controller.llm.propose_json = lambda **kwargs: LLMSupplementResult(  # type: ignore[assignment]
            payload={
                "query_title_identity": "newtons_laws_of_motion:force_mass_acceleration_relationship(Mass, Acceleration, Force)",
                "rationale": "The prompt targets the stored force relationship.",
            },
            source="llm",
            provider="openai",
            model="test-model",
        )

        with patch.dict(
            os.environ,
            {
                title_semantics.TITLE_REPRESENTATION_MODE_ENV: title_semantics.TITLE_REPRESENTATION_MODE_PROLOG,
                title_semantics.PROLOG_QUERY_PRIMING_MODE_ENV: title_semantics.PROLOG_QUERY_PRIMING_MODE_FORCE,
            },
            clear=False,
        ):
            query_text = controller.artifact_query_semantic_unit(
                artifact,
                semantic_unit="Please compute force from the given mass and acceleration.",
            )

        self.assertEqual(
            query_text,
            "newtons_laws_of_motion:force_mass_acceleration_relationship(Mass, Acceleration, Force)",
        )
