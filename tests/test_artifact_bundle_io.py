# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from realized_core_semantics.applied_model import Artifact, ArtifactType
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
)
from realized_core_semantics.normalization import normalize_boundary_shape
from realized_exchange.artifact_yaml import (
    artifact_export_bundle_text,
    load_artifact_yaml_documents,
)


def make_artifact(*, artifact_id: str, title: str, question: str, answer: str) -> Artifact:
    """
    High Level Purpose:
        In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with creating artifact.

    Reference to Theory:
        Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test. This function is especially tied to the artifact/boundary rules used to keep body constitution coherent with semantic identity.

    Example Input Output:
        Input: `make_artifact(artifact_id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', question='Compute force from mass and acceleration.', answer='F = m * a')`
        Output: Artifact(id='artifact-force', title='Physics / Force / Force From Mass And Acceleration', artifact_type='ability', representation='python')

    Args:
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
        scope="reuse for bundle I/O tests",
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
                "encountered_not": title,
                "lookup_keys": [title.lower()],
                "component_nots": [],
                "composed_not": "",
                "notation_yaml": "",
            },
        },
        justification="Bundle round-trip test artifact.",
        boundary_shape=normalize_boundary_shape(("d*",), default=()),
    )


class ArtifactBundleIOTests(unittest.TestCase):
    def test_multidoc_bundle_round_trip(self) -> None:
        """
        High Level Purpose:
            In circumstances like regression testing over semantic decomposition, reuse, boundary behavior, and controller decisions, helps with testing multidoc bundle round trip.

        Reference to Theory:
            Verifies the implemented theory, especially title-depth, decomposition, semantic reuse, boundary-shape behavior, and the controller rules relevant to this test.

        Example Input Output:
            Input: `test_multidoc_bundle_round_trip()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifacts = [
            make_artifact(
                artifact_id="artifact-bundle-one",
                title="Bundle One",
                question="What is bundle one?",
                answer="bundle one",
            ),
            make_artifact(
                artifact_id="artifact-bundle-two",
                title="Bundle Two",
                question="What is bundle two?",
                answer="bundle two",
            ),
        ]

        bundle_text = artifact_export_bundle_text(artifacts)
        self.assertIn("\n---\n", bundle_text)

        with tempfile.TemporaryDirectory(prefix="artifact_bundle_io_") as tempdir:
            bundle_path = Path(tempdir) / "bundle.yaml"
            bundle_path.write_text(bundle_text)
            loaded = load_artifact_yaml_documents(bundle_path)

        self.assertEqual(len(loaded), 2)
        self.assertEqual([artifact.title for artifact in loaded], ["Bundle One", "Bundle Two"])
        self.assertEqual([artifact.content.get("answer") for artifact in loaded], ["bundle one", "bundle two"])


if __name__ == "__main__":
    unittest.main()
