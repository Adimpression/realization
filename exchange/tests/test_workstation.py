from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from realized_exchange.workstation import RealizedSkillExchangeProvider
from workstation.subject.core.learning_context import (
    LearningContext,
    LearningUnit,
    canonical_learning_subject_id,
    learning_context_paths,
)


class RealizedSkillExchangeProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = RealizedSkillExchangeProvider()

    def test_canonical_skill_bundle_round_trips_through_provider(self) -> None:
        document = {
            "schema": "bssc_skill.v1",
            "kind": "knowledge",
            "title": "Portable Knowledge",
            "answer": "A stable fact.",
        }
        artifact = self.provider.artifact_from_skill_document(document)
        bundle = self.provider.export_skill_bundle_text([artifact])

        with TemporaryDirectory() as tempdir:
            source = Path(tempdir) / "portable.yaml"
            source.write_text(bundle, encoding="utf-8")
            payloads = self.provider.load_import_payload_documents(source)

        imported = next(
            payload for payload in payloads if payload.get("title") == "Portable Knowledge"
        )
        self.assertEqual("knowledge", imported["kind"])

    def test_artifact_bundle_is_projected_to_portable_skill_payloads(self) -> None:
        document = {
            "schema": "bssc_skill.v1",
            "kind": "knowledge",
            "title": "Artifact Origin",
            "answer": "A projected fact.",
        }
        artifact = self.provider.artifact_from_skill_document(document)

        from realized_exchange.artifact_yaml import artifact_export_bundle_yaml

        with TemporaryDirectory() as tempdir:
            source = Path(tempdir) / "artifact.yaml"
            source.write_text(
                artifact_export_bundle_yaml([artifact]),
                encoding="utf-8",
            )
            payloads = self.provider.load_import_payload_documents(source)

        self.assertTrue(
            any(payload.get("title") == "Artifact Origin" for payload in payloads)
        )

    def test_learning_context_skill_is_materialized_through_provider(self) -> None:
        subject_id = canonical_learning_subject_id("Projection Boundary")
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Projection Boundary",
            units=(
                LearningUnit(
                    unit_id="unit_projection_boundary",
                    subject_id=subject_id,
                    canonical_title="Projection Boundary",
                    statement="Projection follows authoritative persistence.",
                    status="admitted",
                    linked_skill_ids=("skill_projection_boundary",),
                ),
            ),
            governance_status="active",
        )

        with TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            reports = self.provider.materialize_learning_context_skills(
                root,
                context,
            )
            output_path = (
                learning_context_paths(root, subject_id)["derived_skills"]
                / "skill_projection_boundary.yaml"
            )

            self.assertTrue(output_path.is_file())
            self.assertEqual("skill_projection_boundary", reports[0]["skill_id"])
            self.assertIn("bssc_skill.v2", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
