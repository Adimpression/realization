# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_exchange.learning_context import LearningContext, LearningUnit
from workstation.subject.core.learning_context_projection import (
    render_learning_context_subject_markdown,
    render_learning_context_subject_typ,
)
from workstation.subject.core.publication_render import validate_rendered_typst


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
        self.assertIn(r"- source\_kinematics\_001", typst)
        self.assertIn("== Derived Skills <derived-skills>", typst)
        self.assertIn(r"- skill\_acceleration\_formula", typst)
        self.assertIn("== Update Log <update-log>", typst)
        self.assertIn(r"- delta\_kinematics\_001", typst)

    def test_subject_typ_projection_escapes_typst_sensitive_unit_fields(self) -> None:
        context = LearningContext(
            subject_id="chemistry-relations-02-mole-as-counting-conversion",
            canonical_title="Chemistry Relations 02 — Mole as Counting Conversion",
            aliases=("Chemistry Relations 02 — Mole as Counting Conversion", "02 Learn Chemistry Relations Mole"),
            subject_family="Chemistry Relations 02 — Mole as Counting Conversion",
            summary="Grouped counting substrate.",
            units=(
                LearningUnit(
                    unit_id="unit_problematic_typst",
                    subject_id="chemistry-relations-02-mole-as-counting-conversion",
                    unit_kind="definition",
                    canonical_title="Chemistry Relations 02 — Mole as Counting Conversion / Grouped Counting",
                    statement="The reusable formula is: $$ C = G cg $$ input: G input: c_g output: C",
                    aliases=("input: G", "input: c_g", "C = G * c_g"),
                    linked_artifact_ids=("artifact_ability-chemistry-relations-02-mole-as-counting-_3cfd71",),
                    provenance_refs=("source_users-ravindranathakila-service-realized-trials-_295c24bd24",),
                    structured_fields={
                        "artifact_type": "ability",
                        "input_contract": {"G": "number", "c_g": "number"},
                    },
                    status="admitted",
                ),
            ),
            linked_source_ids=("source_users-ravindranathakila-service-realized-trials-_295c24bd24",),
            governance_status="active",
        )

        typst = render_learning_context_subject_typ(context)

        self.assertIn(r"source\_users-ravindranathakila-service-realized-trials-\_295c24bd24", typst)
        self.assertIn(r"input: c\_g", typst)
        self.assertIn(r"C = G \* c\_g", typst)
        self.assertIn(r"artifact\_ability-chemistry-relations-02-mole-as-counting-\_3cfd71", typst)
        self.assertIn(r'\{"artifact\_type": "ability", "input\_contract": \{"G": "number", "c\_g": "number"\}\}', typst)

        validation_report, _ = validate_rendered_typst(typst)
        if validation_report.get("status") != "unavailable":
            self.assertEqual(validation_report.get("status"), "ok")
