# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from learning_context import LearningContext, LearningUnit
from learning_context_projection import (
    render_learning_context_subject_markdown,
    render_learning_context_subject_typ,
)


class LearningContextProjectionTests(unittest.TestCase):
    def test_subject_document_projection_groups_units_and_links_deterministically(self) -> None:
        context = LearningContext(
            subject_id="kinematics",
            canonical_title="Kinematics",
            aliases=("Kinematics", "Motion Notes"),
            subject_family="Physics",
            summary="Core motion relations.",
            units=(
                LearningUnit(
                    unit_id="unit_velocity",
                    subject_id="kinematics",
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is the rate of change of position.",
                    status="admitted",
                    provenance_refs=("source_kinematics_001",),
                ),
                LearningUnit(
                    unit_id="unit_acceleration",
                    subject_id="kinematics",
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    status="admitted",
                    provenance_refs=("source_kinematics_001",),
                    linked_skill_ids=("skill_acceleration_formula",),
                ),
                LearningUnit(
                    unit_id="unit_note",
                    subject_id="kinematics",
                    unit_kind="source_note",
                    canonical_title="Chat Note 1",
                    statement="Learners often confuse speed and velocity.",
                    status="proposed",
                    provenance_refs=("source_chat_001",),
                ),
            ),
            linked_source_ids=("source_kinematics_001", "source_chat_001"),
            linked_skill_ids=("skill_acceleration_formula",),
            applied_delta_ids=("delta_kinematics_001",),
            governance_status="active",
        )

        markdown = render_learning_context_subject_markdown(context)
        typst = render_learning_context_subject_typ(context)

        self.assertIn("# Kinematics", markdown)
        self.assertIn("<!-- section-id: definitions -->", markdown)
        self.assertIn("## Governing Relations", markdown)
        self.assertIn("### Acceleration", markdown)
        self.assertIn("### Sources", markdown)
        self.assertIn("`source_kinematics_001`", markdown)
        self.assertIn("## Derived Skills", markdown)
        self.assertIn("`skill_acceleration_formula`", markdown)
        self.assertIn("## Update Log", markdown)
        self.assertIn("`delta_kinematics_001`", markdown)

        self.assertIn("= Kinematics", typst)
        self.assertIn("== Definitions <definitions>", typst)
        self.assertIn("== Governing Relations <governing-relations>", typst)
        self.assertIn("=== Acceleration <unit-unit_acceleration>", typst)
        self.assertIn("=== Sources <provenance-sources>", typst)
        self.assertIn("- source_kinematics_001", typst)
        self.assertIn("== Derived Skills <derived-skills>", typst)
        self.assertIn("- skill_acceleration_formula", typst)
        self.assertIn("== Update Log <update-log>", typst)
        self.assertIn("- delta_kinematics_001", typst)
