# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_context import LearningContext, LearningUnit, persist_learning_context
from learning_context_skill_projection import learning_context_projected_skill_ids
from skill_schema_io import load_skill_yaml_payload_documents


class LearningContextSkillProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_persist_learning_context_materializes_admitted_linked_skill_projection(self) -> None:
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            subject_family="Physics",
            units=(
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    status="admitted",
                    linked_skill_ids=("skill_acceleration_summary",),
                    provenance_refs=("source_kinematics_001",),
                ),
                LearningUnit(
                    unit_id="unit_note",
                    subject_id="kinematics",
                    unit_kind="source_note",
                    canonical_title="Chat Note 1",
                    statement="Learners often confuse speed and velocity.",
                    status="proposed",
                    linked_skill_ids=("skill_chat_note",),
                    provenance_refs=("source_chat_001",),
                ),
            ),
            governance_status="active",
        )

        persist_learning_context(self.root, context)

        derived_skills_root = self.root / "corpus" / "kinematics" / "derived" / "skills"
        projected_files = sorted(path.name for path in derived_skills_root.glob("*.yaml"))

        self.assertEqual(projected_files, ["skill_acceleration_summary.yaml"])
        payloads = load_skill_yaml_payload_documents(derived_skills_root / "skill_acceleration_summary.yaml")
        self.assertEqual(len(payloads), 1)
        payload = payloads[0]
        self.assertEqual(payload["kind"], "knowledge")
        self.assertEqual(payload["title"], "Kinematics / Acceleration / skill_acceleration_summary")
        self.assertEqual(payload["answer"], "Acceleration is the rate of change of velocity.")
        self.assertEqual(payload["family"]["label"], "Kinematics")
        self.assertEqual(payload["compatibility"]["adapters"][0]["format"], "learning_context_projection")

    def test_learning_context_projected_skill_ids_unifies_context_and_unit_links(self) -> None:
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            linked_skill_ids=("skill_velocity_summary",),
            units=(
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    status="admitted",
                    linked_skill_ids=("skill_acceleration_summary",),
                ),
            ),
        )

        self.assertEqual(
            learning_context_projected_skill_ids(context),
            ("skill_velocity_summary", "skill_acceleration_summary"),
        )
