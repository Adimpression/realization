# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
import importlib
from unittest import mock
from pathlib import Path

from main import (
    Artifact,
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    ArtifactType,
    LearningRelation,
    build_artifact_store,
    normalize_boundary_shape,
)
from store import EmbeddingGemmaEncoder
from store import SQLiteVectorArtifactStore


class ArtifactSearchHybridTests(unittest.TestCase):
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
        self.tempdir = tempfile.TemporaryDirectory(prefix="artifact_search_hybrid_")
        self.sqlite_path = str(Path(self.tempdir.name) / "artifact_search_hybrid.sqlite3")
        self.previous_sqlite_path = os.environ.get("STATE_SQLITE_PATH")
        self.previous_vector_mode = os.environ.get("STATE_VECTOR_MODE")
        os.environ["STATE_SQLITE_PATH"] = self.sqlite_path
        os.environ.pop("STATE_VECTOR_MODE", None)

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
        if self.previous_vector_mode is None:
            os.environ.pop("STATE_VECTOR_MODE", None)
        else:
            os.environ["STATE_VECTOR_MODE"] = self.previous_vector_mode
        self.tempdir.cleanup()

    def make_artifact(self, *, artifact_id: str, title: str, question: str, answer: str) -> Artifact:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating artifact.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `make_artifact(artifact_id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', question='Compute force from mass and acceleration.', answer='F = m * a')`
            Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

        Args:
            self: Bound instance that owns the runtime state used by this method.
            artifact_id: Value for `artifact_id` used by `make_artifact`. Expected type: `str`.
            title: Value for `title` used by `make_artifact`. Expected type: `str`.
            question: Value for `question` used by `make_artifact`. Expected type: `str`.
            answer: Value for `answer` used by `make_artifact`. Expected type: `str`.

        Returns:
            Artifact: Result produced by `make_artifact`.
        """
        return Artifact(
            id=artifact_id,
            artifact_type=ArtifactType.KNOWLEDGE,
            title=title,
            representation=ArtifactRepresentation.YAML,
            function_bit=0,
            scope="reuse for unresolved-alternative next-step guidance",
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
            justification="Reusable guidance for unresolved decisive alternatives.",
            boundary_shape=normalize_boundary_shape(("d*",), default=()),
        )

    def test_persist_creates_hybrid_search_rows(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing persist creates hybrid search rows.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_persist_creates_hybrid_search_rows()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact = self.make_artifact(
            artifact_id="artifact-hybrid-search",
            title="Confirm decisive fact before action",
            question="What should I do when one decisive fact remains unconfirmed before action?",
            answer="Do not act until the decisive fact is confirmed.",
        )

        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = sqlite3.connect(self.sqlite_path)
        try:
            search_row = connection.execute(
                """
                SELECT canonical_text, failure_signature, repair_operator, applicability
                FROM bssc_artifact_search_units
                WHERE artifact_id = ?
                """,
                (artifact.id,),
            ).fetchone()
            fts_row = connection.execute(
                """
                SELECT artifact_id
                FROM bssc_artifact_search_fts
                WHERE bssc_artifact_search_fts MATCH ?
                LIMIT 1
                """,
                ('"decisive" OR "unconfirmed"',),
            ).fetchone()
        finally:
            connection.close()

        self.assertIsNotNone(search_row)
        self.assertIsNotNone(fts_row)
        self.assertEqual(fts_row[0], artifact.id)

    def test_vector_disabled_persist_avoids_sqlite_vec_and_encoder_startup(self) -> None:
        """
        High Level Purpose:
            In circumstances like bundle or markdown import runs with vector retrieval disabled, helps with proving that persistence does not pay eager sqlite-vec or embedding-encoder startup cost before any vector path is actually needed.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_vector_disabled_persist_avoids_sqlite_vec_and_encoder_startup()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        previous_vector_mode = os.environ.get("STATE_VECTOR_MODE")
        os.environ["STATE_VECTOR_MODE"] = "off"
        real_import_module = importlib.import_module

        def guarded_import(module_name: str, *args, **kwargs):
            if module_name == "sqlite_vec":
                raise AssertionError("sqlite_vec should not be imported when STATE_VECTOR_MODE=off")
            return real_import_module(module_name, *args, **kwargs)

        try:
            with (
                mock.patch("store.importlib.import_module", side_effect=guarded_import),
                mock.patch("store.EmbeddingGemmaEncoder", side_effect=AssertionError("encoder should stay lazy when vectors are off")),
            ):
                store = build_artifact_store()
                artifact = self.make_artifact(
                    artifact_id="artifact-vector-disabled-startup",
                    title="No eager vector startup",
                    question="What should persistence do when vectors are disabled?",
                    answer="Persist the artifact without importing sqlite_vec or constructing the embedding encoder.",
                )
                report = store.persist_artifact(artifact)
        finally:
            if previous_vector_mode is None:
                os.environ.pop("STATE_VECTOR_MODE", None)
            else:
                os.environ["STATE_VECTOR_MODE"] = previous_vector_mode

        self.assertEqual(report.get("status"), "persisted")
        self.assertFalse(report.get("vector_enabled"))

    def test_batch_persist_canonicalizes_duplicate_notation_keys_within_same_batch(self) -> None:
        """
        High Level Purpose:
            In circumstances like markdown-learning batch persistence where multiple artifacts normalize to the same title-depth identity, helps with proving the batched store path canonicalizes against earlier items in the same batch instead of tripping the notation-key uniqueness constraint.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_batch_persist_canonicalizes_duplicate_notation_keys_within_same_batch()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        previous_vector_mode = os.environ.get("STATE_VECTOR_MODE")
        os.environ["STATE_VECTOR_MODE"] = "off"
        try:
            store = build_artifact_store()
            first = self.make_artifact(
                artifact_id="artifact-duplicate-notation-a",
                title="Newton's Laws of Motion / Second Law: Law of Acceleration",
                question="What is Newton's second law of motion?",
                answer="Force equals mass times acceleration.",
            )
            second = self.make_artifact(
                artifact_id="artifact-duplicate-notation-b",
                title="Newton's Laws of Motion / Second Law: Law of Acceleration",
                question="What is Newton's second law of motion?",
                answer="Acceleration is proportional to force and inversely proportional to mass.",
            )
            report = store.persist_artifacts((first, second), run_id="duplicate_notation_batch")
        finally:
            if previous_vector_mode is None:
                os.environ.pop("STATE_VECTOR_MODE", None)
            else:
                os.environ["STATE_VECTOR_MODE"] = previous_vector_mode

        self.assertEqual(report.get("status"), "persisted")
        reports = list(report.get("reports", []))
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0].get("artifact_id"), first.id)
        self.assertEqual(reports[1].get("artifact_id"), first.id)

        connection = sqlite3.connect(self.sqlite_path)
        try:
            artifact_count = connection.execute("SELECT COUNT(*) FROM bssc_artifacts").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(int(artifact_count), 1)

    def test_retrieval_works_without_legacy_lookup_columns(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing retrieval works without legacy lookup columns.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_retrieval_works_without_legacy_lookup_columns()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact = self.make_artifact(
            artifact_id="artifact-search-only",
            title="Opaque guidance artifact",
            question="What should I do when one decisive fact remains unconfirmed before action?",
            answer="Do not act until the decisive fact is confirmed.",
        )

        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = sqlite3.connect(self.sqlite_path)
        try:
            sqlite_vec = importlib.import_module("sqlite_vec")
            connection.enable_load_extension(True)
            sqlite_vec.load(connection)
            connection.execute("DELETE FROM bssc_artifact_vec WHERE artifact_id = ?", (artifact.id,))
            connection.execute(
                """
                UPDATE bssc_artifacts
                SET
                    title = ?,
                    scope = '',
                    structured_encountered_not = '',
                    structured_lookup_blob = '',
                    structured_composed_not = '',
                    notation_key = ?,
                    notation_key_normalized = ?
                WHERE artifact_id = ?
                """,
                ("Opaque Artifact", "opaque artifact", "opaque artifact", artifact.id),
            )
            connection.commit()
        finally:
            connection.close()

        relevant = store.load_relevant_artifacts(
            "I still cannot confirm which decisive alternative is true. What should I do next?",
            limit=4,
        )
        self.assertTrue(any(item.id == artifact.id for item in relevant))

    def test_persist_skips_unresolved_search_links(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing persist skips unresolved search links.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_persist_skips_unresolved_search_links()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact = self.make_artifact(
            artifact_id="artifact-search-link-gap",
            title="Gap artifact",
            question="What should I do when a decisive variable is still unknown?",
            answer="Pause and resolve the unknown before acting.",
        )
        artifact.related_artifact_ids = ["artifact-not-yet-persisted"]

        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = sqlite3.connect(self.sqlite_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM bssc_artifact_search_links WHERE from_artifact_id = ?",
                (artifact.id,),
            ).fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(count, 0)

    def test_batch_persist_canonicalizes_same_notation_key_within_batch(self) -> None:
        """
        High Level Purpose:
            In circumstances like batch markdown-learning persistence, helps with verifying that same-notation artifacts are canonicalized against earlier writes in the same batch instead of falling back out of the SQLite store.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

        Example Input Output:
            Input: `test_batch_persist_canonicalizes_same_notation_key_within_batch()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        store = build_artifact_store()
        artifact_a = self.make_artifact(
            artifact_id="artifact-batch-duplicate-a",
            title="Reusable duplicate artifact",
            question="What should I do when the decisive fact is still unresolved?",
            answer="Pause and resolve the decisive fact before acting.",
        )
        artifact_b = self.make_artifact(
            artifact_id="artifact-batch-duplicate-b",
            title="Reusable duplicate artifact",
            question="What should I do when the decisive fact is still unresolved?",
            answer="Pause and resolve the decisive fact before acting.",
        )

        report = store.persist_artifacts([artifact_a, artifact_b], run_id="test_batch_duplicate")

        self.assertNotIn("fallback_from", report)
        self.assertEqual(report.get("status"), "persisted")
        self.assertEqual(report.get("persisted_artifacts"), 1)
        self.assertEqual(report.get("unchanged_artifacts"), 1)
        reports = report.get("reports", [])
        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0].get("status"), "persisted")
        self.assertEqual(reports[1].get("status"), "unchanged")
        self.assertEqual(reports[1].get("artifact_id"), artifact_a.id)

        connection = sqlite3.connect(self.sqlite_path)
        try:
            count = connection.execute("SELECT COUNT(*) FROM bssc_artifacts").fetchone()[0]
        finally:
            connection.close()

        self.assertEqual(count, 1)

    def test_batch_persist_encodes_main_and_search_surfaces_in_one_pass(self) -> None:
        """
        High Level Purpose:
            In circumstances like batched bundle import indexing, helps with proving that vector encoding runs once across the whole prepared batch instead of paying model overhead separately for main surfaces and search surfaces.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_batch_persist_encodes_main_and_search_surfaces_in_one_pass()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        class FakeEncoder:
            VECTOR_DIMENSION = 3

            def __init__(self) -> None:
                self.model_repo = "test-encoder"
                self.calls: list[list[str]] = []

            def available(self) -> bool:
                return True

            def describe(self) -> dict[str, object]:
                return {"repo": self.model_repo, "available": True, "dimension": self.VECTOR_DIMENSION}

            def encode(self, texts: list[str]) -> list[list[float]]:
                self.calls.append(list(texts))
                return [[0.1, 0.2, 0.3] for _ in texts]

        store = build_artifact_store()
        fake_encoder = FakeEncoder()
        store.encoder = fake_encoder
        artifact_a = self.make_artifact(
            artifact_id="artifact-batch-encode-a",
            title="Batch encode A",
            question="How should I proceed when decisive facts remain unresolved?",
            answer="Pause until the decisive facts are resolved.",
        )
        artifact_b = self.make_artifact(
            artifact_id="artifact-batch-encode-b",
            title="Batch encode B",
            question="How should I proceed when decisive facts remain unresolved in a second case?",
            answer="Pause until the decisive facts are resolved in the second case.",
        )

        report = store.persist_artifacts([artifact_a, artifact_b], run_id="test_batch_single_encode")

        self.assertEqual(report.get("status"), "persisted")
        self.assertEqual(len(fake_encoder.calls), 1)
        self.assertEqual(len(fake_encoder.calls[0]), 8)

    def test_batch_persist_fetches_existing_payloads_once_for_the_whole_batch(self) -> None:
        store = build_artifact_store()
        artifact_a = self.make_artifact(
            artifact_id="artifact-batch-existing-a",
            title="Batch existing A",
            question="What is the first batch item?",
            answer="The first batch item is A.",
        )
        artifact_b = self.make_artifact(
            artifact_id="artifact-batch-existing-b",
            title="Batch existing B",
            question="What is the second batch item?",
            answer="The second batch item is B.",
        )

        original_fetch = store._fetch_existing_payload_json_map
        seen_batches: list[list[str]] = []

        def wrapped_fetch(connection, artifact_ids):
            seen_batches.append(list(artifact_ids))
            return original_fetch(connection, artifact_ids)

        with (
            mock.patch.object(store, "vector_enabled", return_value=False),
            mock.patch.object(store, "_fetch_existing_payload_json_map", side_effect=wrapped_fetch),
        ):
            report = store.persist_artifacts([artifact_a, artifact_b], run_id="test_batch_existing_lookup")

        self.assertEqual(report.get("status"), "persisted")
        self.assertEqual(seen_batches, [[artifact_a.id, artifact_b.id]])

    def test_connection_is_closed_when_sqlite_initialization_fails(self) -> None:
        class FailingConnection:
            row_factory = None

            def __init__(self) -> None:
                self.closed = False

            def execute(self, _statement: str) -> None:
                raise sqlite3.OperationalError("simulated initialization failure")

            def close(self) -> None:
                self.closed = True

        connection = FailingConnection()
        store = SQLiteVectorArtifactStore()
        store.sqlite3 = mock.Mock(Row=sqlite3.Row)
        store.sqlite3.connect.return_value = connection

        with self.assertRaisesRegex(sqlite3.OperationalError, "simulated initialization failure"):
            store._connect()

        self.assertTrue(connection.closed)

    def test_hybrid_search_skips_vector_when_exact_deterministic_match_exists(self) -> None:
        store = build_artifact_store()
        artifact = self.make_artifact(
            artifact_id="artifact-exact-hybrid-match",
            title="Mass To Mole Conversion",
            question="What relation converts mass to amount in moles?",
            answer="Divide mass by molar mass.",
        )
        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        connection = store._connect()
        try:
            store._ensure_schema(connection)
            with mock.patch.object(store, "_vector_candidate_scores", side_effect=AssertionError("unexpected vector scoring")):
                candidate_ids = store._hybrid_candidate_ids(connection, "Mass To Mole Conversion", limit=4)
        finally:
            connection.close()

        self.assertIn(artifact.id, candidate_ids)

    def test_load_relevant_artifacts_skips_legacy_pass_when_hybrid_exact_match_is_enough(self) -> None:
        store = build_artifact_store()
        artifact = self.make_artifact(
            artifact_id="artifact-exact-load-match",
            title="Stoichiometric Ratio From Balanced Equations",
            question="What relation maps one substance amount to another using balanced coefficients?",
            answer="Apply the balanced-equation mole ratio.",
        )
        report = store.persist_artifact(artifact)
        self.assertEqual(report.get("status"), "persisted")

        with mock.patch.object(store, "_legacy_candidate_ids", side_effect=AssertionError("unexpected legacy pass")):
            relevant = store.load_relevant_artifacts("Stoichiometric Ratio From Balanced Equations", limit=4)

        self.assertTrue(any(item.id == artifact.id for item in relevant))


class EmbeddingGemmaEncoderTests(unittest.TestCase):
    def test_available_checks_module_specs_without_importing_runtime_modules(self) -> None:
        """
        High Level Purpose:
            In circumstances like controller startup and bundle import setup, helps with proving that embedding availability checks do not eagerly import the heavy ONNX/tokenizer stack.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_available_checks_module_specs_without_importing_runtime_modules()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with (
            mock.patch("store.importlib.util.find_spec", return_value=object()) as find_spec,
            mock.patch("store.importlib.import_module", side_effect=AssertionError("unexpected eager import")),
        ):
            encoder = EmbeddingGemmaEncoder()
            self.assertTrue(encoder.available())

        self.assertGreaterEqual(find_spec.call_count, 3)

    def test_encode_reuses_cached_vectors_across_calls_and_batch_duplicates(self) -> None:
        encoder = EmbeddingGemmaEncoder()
        uncached_calls: list[list[str]] = []
        vectors = {
            "mass": [1.0, 0.0, 0.0],
            "force": [0.0, 1.0, 0.0],
        }

        def fake_uncached(texts: list[str]) -> list[list[float]]:
            uncached_calls.append(list(texts))
            return [vectors[text] for text in texts]

        with (
            mock.patch.object(encoder, "_load", return_value=True),
            mock.patch.object(encoder, "_encode_uncached", side_effect=fake_uncached),
        ):
            first = encoder.encode(["mass", "mass", "force"])
            second = encoder.encode(["force", "mass"])

        self.assertEqual(uncached_calls, [["mass", "force"]])
        self.assertEqual(first, [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        self.assertEqual(second, [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])


if __name__ == "__main__":
    unittest.main()
