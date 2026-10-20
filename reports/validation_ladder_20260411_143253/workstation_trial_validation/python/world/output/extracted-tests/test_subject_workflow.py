# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_context import (
    LearningContext,
    LearningUnit,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from workstation.subject_workflow import (
    apply_subject_action,
    default_subject_scenarios,
    new_subject_progress,
    render_subject_status,
    render_subject_workspace,
    subject_has_pending_research_capture,
    subject_action_specs,
)


class SubjectWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _persist_demo_context(self) -> str:
        subject_id = "kinematics-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the initial kinematics subject notes.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Kinematics Demo",
            aliases=("Kinematics Demo",),
            subject_family="Physics / Kinematics",
            summary="Maintained subject for introductory kinematics.",
            units=(unit,),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return subject_id

    def test_default_subject_scenarios_returns_placeholder_when_corpus_is_empty(self) -> None:
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        self.assertTrue(scenario.is_placeholder)
        self.assertIn("No LearningContext yet", render_subject_status(scenario=scenario, progress=progress, phase="research"))

        action_specs = subject_action_specs(scenario=scenario, progress=progress, phase="research")
        self.assertEqual(action_specs[0].label, "Refresh Subjects")
        self.assertEqual(action_specs[1].label, "Use Learn Markdown")
        self.assertTrue(action_specs[1].enabled)

        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="use_markdown_ingress",
        )
        self.assertIn("Learn Markdown", result.status_text)

    def test_subject_workflow_requires_aligned_projection_comparison_before_approval(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        review_specs_before = subject_action_specs(scenario=scenario, progress=progress, phase="review")
        self.assertFalse(review_specs_before[2].enabled)

        approve_before_compare = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        self.assertIn("Compare projections", approve_before_compare.status_text)

        compare_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        self.assertEqual(compare_result.status_text, "Projection comparison aligned.")
        self.assertEqual(progress.comparison_status, "aligned")
        self.assertIn("- verdict: aligned", "\n".join(progress.comparison_receipt_lines))
        self.assertIn("- admitted units covered in subject.md: 1 / 1", "\n".join(progress.comparison_receipt_lines))
        self.assertIn("- admitted units covered in subject.typ: 1 / 1", "\n".join(progress.comparison_receipt_lines))

        review_specs_after = subject_action_specs(scenario=scenario, progress=progress, phase="review")
        self.assertTrue(review_specs_after[2].enabled)

        review_text = render_subject_workspace(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertIn("Projection Comparison Receipt", review_text)
        self.assertIn("- verdict: aligned", review_text)
        self.assertIn("- admitted units covered in subject.md: 1 / 1", review_text)

    def test_subject_workflow_builds_real_publication_from_learning_context(self) -> None:
        subject_id = self._persist_demo_context()
        scenarios = default_subject_scenarios(self.root)
        scenario = next(item for item in scenarios if item.subject_id == subject_id)
        progress = new_subject_progress()

        self.assertIn("Velocity", scenario.unit_preview_lines[0])
        self.assertIn("Kinematics Notes", "\n".join(scenario.source_preview_lines))

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )
        build_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="build_report",
        )

        self.assertTrue(build_result.reload_subjects)
        self.assertIn("Report build completed", build_result.status_text)

        rebuilt_scenarios = default_subject_scenarios(self.root)
        rebuilt = next(item for item in rebuilt_scenarios if item.subject_id == subject_id)
        self.assertTrue(rebuilt.publication_id)
        self.assertTrue(rebuilt.build_id)
        self.assertGreater(rebuilt.publication_section_count, 0)
        self.assertGreater(rebuilt.publication_claim_count, 0)
        self.assertGreater(rebuilt.publication_review_count, 0)
        self.assertTrue(Path(rebuilt.report_pdf_path).is_file())
        self.assertTrue(Path(rebuilt.report_typst_path).is_file())
        self.assertTrue(Path(rebuilt.report_markdown_path).is_file())

        publication_specs = subject_action_specs(scenario=rebuilt, progress=progress, phase="publication")
        self.assertEqual(publication_specs[0].label, "Preview report.md")
        self.assertEqual(publication_specs[1].label, "Rebuild Report")
        self.assertEqual(publication_specs[2].label, "Open Release Packet")
        self.assertEqual(publication_specs[3].label, "Preview report.pdf")
        self.assertTrue(publication_specs[0].enabled)
        self.assertTrue(publication_specs[2].enabled)
        self.assertTrue(publication_specs[3].enabled)

        packet_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="open_release_packet",
        )
        self.assertTrue(packet_result.open_paths)
        self.assertTrue(Path(packet_result.open_paths[0]).is_dir())
        self.assertIn("- packet items:", "\n".join(progress.latest_receipt_lines))

        markdown_preview_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="preview_publication_markdown",
        )
        self.assertEqual(progress.publication_preview_kind, "report.md")
        self.assertEqual(markdown_preview_result.status_text, "Opened report.md.")
        self.assertEqual(markdown_preview_result.open_paths, (rebuilt.report_markdown_path,))

        pdf_preview_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="preview_publication_pdf",
        )
        self.assertEqual(progress.publication_preview_kind, "report.pdf")
        self.assertEqual(pdf_preview_result.status_text, "Opened report.pdf.")
        self.assertEqual(pdf_preview_result.open_paths, (rebuilt.report_pdf_path,))

        publication_text = render_subject_workspace(
            scenario=rebuilt,
            progress=progress,
            phase="publication",
        )
        self.assertIn("Publication Contract", publication_text)
        self.assertIn("Publication Build Receipt", publication_text)
        self.assertIn("- reviews:", publication_text)
        self.assertIn("- xrefs:", publication_text)
        self.assertIn("- sections:", publication_text)
        self.assertIn("- claims:", publication_text)
        self.assertIn("- rendered pdf:", publication_text)
        self.assertIn("Output Preview [report.pdf]", publication_text)
        self.assertIn("report.pdf is a binary artifact.", publication_text)

    def test_subject_workflow_requires_fresh_review_before_rebuild_even_if_publication_exists(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="build_report",
        )

        rebuilt = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        fresh_progress = new_subject_progress()

        publication_specs = subject_action_specs(scenario=rebuilt, progress=fresh_progress, phase="publication")
        self.assertEqual(publication_specs[1].label, "Rebuild Report")
        self.assertFalse(publication_specs[1].enabled)

        blocked_rebuild = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=fresh_progress,
            action_key="build_report",
        )
        self.assertIn("Approve review or lock publication inputs", blocked_rebuild.status_text)

    def test_subject_workflow_stages_confirms_and_cancels_assistant_capture(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        assistant_markdown = "\n".join(
            [
                "# Velocity Notes",
                "",
                "- Velocity is displacement per unit time.",
                "- SI unit: m/s.",
            ]
        )

        stage_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="stage_assistant_capture",
            assistant_message_text=assistant_markdown,
            subject_title_override="Kinematics Demo",
        )
        self.assertEqual(stage_result.status_text, "Research admission preview ready.")
        self.assertTrue(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Research Admission Preview")
        self.assertIn("- proposed subject: Kinematics Demo", progress.latest_receipt_lines)

        cancel_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cancel_assistant_capture",
        )
        self.assertEqual(cancel_result.status_text, "Research admission canceled.")
        self.assertFalse(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Research Admission Canceled")

        progress.review_approved = True
        progress.publication_locked = True
        progress.comparison_status = "aligned"
        progress.projections_compared = True

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="stage_assistant_capture",
            assistant_message_text=assistant_markdown,
            subject_title_override="Kinematics Demo",
        )
        confirm_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="confirm_assistant_capture",
        )
        self.assertEqual(confirm_result.status_text, "Research capture completed.")
        self.assertTrue(confirm_result.reload_subjects)
        self.assertEqual(confirm_result.preferred_subject_key, subject_id)
        self.assertFalse(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Research Capture Receipt")
        self.assertFalse(progress.review_approved)
        self.assertFalse(progress.publication_locked)
        self.assertEqual(progress.comparison_status, "pending")
        self.assertFalse(progress.projections_compared)

        refreshed = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self.assertGreaterEqual(refreshed.source_count, 2)
        self.assertGreaterEqual(refreshed.delta_count, 2)


if __name__ == "__main__":
    unittest.main()
