# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from realized_core_engine.controller_runtime import BSSCController, build_artifact_store
from realized_core_engine.state import SystemState
from realized_core_semantics.applied_model import Artifact, ArtifactType, BoundaryShapeTerm
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
)
from realized_core_semantics.boundary import infer_artifact_boundary_shape
from realized_core_semantics.normalization import normalize_boundary_shape


class ArtifactBoundaryShapeTests(unittest.TestCase):
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
        self.tempdir = tempfile.TemporaryDirectory(prefix="artifact_boundary_shape_")
        self.sqlite_path = str(Path(self.tempdir.name) / "artifact_boundary_shape.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path

    def tearDown(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with handling tearDown.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `tearDown()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        if self.previous_sqlite_path is None:
            os.environ.pop("STATE_SQLITE_PATH", None)
        else:
            os.environ["STATE_SQLITE_PATH"] = self.previous_sqlite_path
        self.tempdir.cleanup()

    def make_knowledge_artifact(
        self,
        *,
        artifact_id: str,
        title: str,
        question: str,
        answer: str,
        boundary_shape: tuple[str, ...],
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
            self: Bound instance that owns the runtime state used by this method.
            artifact_id: Value for `artifact_id` used by `make_knowledge_artifact`. Expected type: `str`.
            title: Value for `title` used by `make_knowledge_artifact`. Expected type: `str`.
            question: Value for `question` used by `make_knowledge_artifact`. Expected type: `str`.
            answer: Value for `answer` used by `make_knowledge_artifact`. Expected type: `str`.
            boundary_shape: Value for `boundary_shape` used by `make_knowledge_artifact`. Expected type: `tuple[str, ...]`.

        Returns:
            Artifact: Result produced by `make_knowledge_artifact`.
        """
        return Artifact(
            id=artifact_id,
            artifact_type=ArtifactType.KNOWLEDGE,
            title=title,
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for the same bounded greeting family",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            template_schema={},
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            content={
                "question": question,
                "answer": answer,
                "structured_learning": {
                    "encountered_not": "Say Hi",
                    "lookup_keys": ["say hi"],
                    "component_nots": [],
                    "composed_not": "",
                    "notation_yaml": "",
                },
            },
            justification="Test artifact for boundary-shape-aware reuse.",
            boundary_shape=normalize_boundary_shape(boundary_shape, default=()),
        )

    def test_boundary_shape_persists_in_dedicated_rows(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing boundary shape persists in dedicated rows.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_boundary_shape_persists_in_dedicated_rows()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact = self.make_knowledge_artifact(
            artifact_id="artifact-email-sender",
            title="Greeting Email Sender",
            question="Say hi.",
            answer="hi",
            boundary_shape=("a*", "c*"),
        )

        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = sqlite3.connect(self.sqlite_path)
        try:
            rows = connection.execute(
                """
                SELECT boundary_term
                FROM bssc_artifact_boundary_shape_terms
                WHERE artifact_id = ?
                ORDER BY term_index ASC
                """,
                (artifact.id,),
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual([row[0] for row in rows], ["a*", "c*"])

        loaded = store.load_artifact_by_id(artifact.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(tuple(term.value for term in loaded.boundary_shape), ("a*", "c*"))

        connection = sqlite3.connect(self.sqlite_path)
        try:
            payload_json = connection.execute(
                "SELECT payload_json FROM bssc_artifacts WHERE artifact_id = ?",
                (artifact.id,),
            ).fetchone()[0]
        finally:
            connection.close()
        payload = json.loads(payload_json)
        self.assertEqual(payload.get("storage_mode"), "normalized_tables")
        self.assertNotIn("content", payload)
        self.assertNotIn("template_schema", payload)

    def test_reuse_prefers_boundary_compatible_artifact(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing reuse prefers boundary compatible artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_reuse_prefers_boundary_compatible_artifact()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        state = SystemState.bootstrap("Say hi.")
        controller = BSSCController(state, llm_policy="off")
        root = state.root()
        root.boundary_shape = normalize_boundary_shape(["d*"])

        output_only = self.make_knowledge_artifact(
            artifact_id="artifact-hi-output",
            title="Hi Output",
            question="Say hi.",
            answer="hi",
            boundary_shape=("d*",),
        )
        side_effecting = self.make_knowledge_artifact(
            artifact_id="artifact-hi-email",
            title="Hi Email Sender",
            question="Say hi.",
            answer="hi",
            boundary_shape=("a*", "c*"),
        )

        state.learned_artifacts[output_only.id] = output_only
        state.learned_artifacts[side_effecting.id] = side_effecting

        lookup = controller.lookup_prior_non_achievedness(root)
        self.assertIsNotNone(lookup["answer_artifact"])
        self.assertEqual(lookup["answer_artifact"].id, output_only.id)
        self.assertEqual(lookup["answer_preference"], "same_not")
        self.assertEqual(tuple(term.value for term in lookup["answer_artifact"].boundary_shape), ("d*",))

    def test_loads_from_normalized_rows_when_payload_json_is_corrupted(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing loads from normalized rows when payload json is corrupted.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_loads_from_normalized_rows_when_payload_json_is_corrupted()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact = self.make_knowledge_artifact(
            artifact_id="artifact-normalized-hydration",
            title="Hi Normalized",
            question="Say hi.",
            answer="hi",
            boundary_shape=("d*",),
        )

        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = sqlite3.connect(self.sqlite_path)
        try:
            connection.execute(
                "UPDATE bssc_artifacts SET payload_json = ? WHERE artifact_id = ?",
                ("{not-valid-json", artifact.id),
            )
            connection.commit()
        finally:
            connection.close()

        loaded = store.load_artifact_by_id(artifact.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.id, artifact.id)
        self.assertEqual(loaded.title, artifact.title)
        self.assertEqual(loaded.content.get("question"), "Say hi.")
        self.assertEqual(loaded.content.get("answer"), "hi")
        self.assertEqual(tuple(term.value for term in loaded.boundary_shape), ("d*",))

        relevant = store.load_relevant_artifacts("Say hi.", limit=4)
        self.assertTrue(any(item.id == artifact.id for item in relevant))

    def test_knowledge_answer_text_does_not_create_write_boundary(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing knowledge answer text does not create write boundary.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_knowledge_answer_text_does_not_create_write_boundary()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        boundary_shape = infer_artifact_boundary_shape(
            artifact_type=ArtifactType.KNOWLEDGE,
            representation=ArtifactRepresentation.YAML,
            title="Next Step Guidance",
            scope="reuse for bounded next-step guidance",
            content={
                "question": "What should I do next?",
                "answer": "Contact the pharmacist and send an email to support if needed.",
            },
            function_bit=0,
        )
        self.assertEqual(tuple(term.value for term in boundary_shape), ("d*",))


if __name__ == "__main__":
    unittest.main()
