# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from workstation.subject.core.subject_workflow_state_transitions import (
    SUBJECT_WORKFLOW_TRANSITIONS,
    preferred_subject_workflow_tab_for_current_step,
    SubjectWorkflowCurrentStepInputs,
    SubjectWorkflowCurrentStepState,
    SubjectWorkflowJourneyStatus,
    SubjectWorkflowObject,
    SubjectWorkflowStateInputs,
    SubjectWorkflowStatus,
    SubjectWorkflowTab,
    render_subject_workflow_journey_lines,
    resolve_subject_workflow_current_step,
    resolve_subject_workflow_journey,
)


class SubjectWorkflowStateTransitionsTests(unittest.TestCase):
    def test_transition_rows_are_high_resolution_and_flat(self) -> None:
        self.assertIn(
            (
                SubjectWorkflowTab.RESEARCH,
                SubjectWorkflowObject.SUBJECT_PROGRESS,
                SubjectWorkflowStatus.CLOSED,
                SubjectWorkflowTab.ITEMIZE,
                SubjectWorkflowObject.SUBJECT_PROGRESS,
                SubjectWorkflowStatus.BLOCKED,
            ),
            {
                (
                    row.from_tab,
                    row.from_object,
                    row.from_status,
                    row.to_tab,
                    row.to_object,
                    row.to_status,
                )
                for row in SUBJECT_WORKFLOW_TRANSITIONS
            },
        )
        self.assertIn(
            (
                SubjectWorkflowTab.ITEMIZE,
                SubjectWorkflowObject.ITEMIZATION_SESSION,
                SubjectWorkflowStatus.SEED_PROMOTED_ONLY,
                SubjectWorkflowTab.DRAFT,
                SubjectWorkflowObject.REVIEW_COMPOSITION,
                SubjectWorkflowStatus.SEED_PROMOTED_ONLY,
            ),
            {
                (
                    row.from_tab,
                    row.from_object,
                    row.from_status,
                    row.to_tab,
                    row.to_object,
                    row.to_status,
                )
                for row in SUBJECT_WORKFLOW_TRANSITIONS
            },
        )

    def test_resolve_journey_placeholder_subject_is_blocked_before_itemize(self) -> None:
        resolution = resolve_subject_workflow_journey(
            SubjectWorkflowStateInputs(
                subject_exists=False,
                context_opened=False,
                admitted_unit_count=0,
                pending_import_count=0,
                itemization_exists=False,
                itemization_current=False,
                itemization_valid=False,
                draft_composition_exists=False,
                draft_composition_current=False,
                maintained_files_aligned=False,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(resolution.gather, SubjectWorkflowJourneyStatus.GATHER_NOT_STARTED)
        self.assertEqual(resolution.itemize, SubjectWorkflowJourneyStatus.ITEMIZE_BLOCKED_NO_SUBJECT)
        self.assertEqual(resolution.shape, SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_NO_SUBJECT)
        self.assertEqual(resolution.release, SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_DRAFT_REVIEW)

    def test_resolve_journey_reports_stale_itemization_and_pending_draft(self) -> None:
        resolution = resolve_subject_workflow_journey(
            SubjectWorkflowStateInputs(
                subject_exists=True,
                context_opened=True,
                admitted_unit_count=2,
                pending_import_count=0,
                itemization_exists=True,
                itemization_current=False,
                itemization_valid=True,
                draft_composition_exists=False,
                draft_composition_current=False,
                maintained_files_aligned=False,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(resolution.gather, SubjectWorkflowJourneyStatus.GATHER_READY)
        self.assertEqual(resolution.itemize, SubjectWorkflowJourneyStatus.ITEMIZE_IN_PROGRESS_REFRESH)
        self.assertEqual(resolution.shape, SubjectWorkflowJourneyStatus.SHAPE_BLOCKED_ITEMIZE)

    def test_resolve_journey_keeps_shape_in_progress_until_report_plan_exists(self) -> None:
        resolution = resolve_subject_workflow_journey(
            SubjectWorkflowStateInputs(
                subject_exists=True,
                context_opened=True,
                admitted_unit_count=2,
                pending_import_count=0,
                itemization_exists=True,
                itemization_current=True,
                itemization_valid=True,
                draft_composition_exists=True,
                draft_composition_current=True,
                maintained_files_aligned=False,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(
            resolution.shape,
            SubjectWorkflowJourneyStatus.SHAPE_IN_PROGRESS_CREATE_REPORT_PLAN,
        )

    def test_resolve_journey_distinguishes_failed_build_from_ready_release(self) -> None:
        resolution = resolve_subject_workflow_journey(
            SubjectWorkflowStateInputs(
                subject_exists=True,
                context_opened=True,
                admitted_unit_count=3,
                pending_import_count=0,
                itemization_exists=True,
                itemization_current=True,
                itemization_valid=True,
                draft_composition_exists=True,
                draft_composition_current=True,
                maintained_files_aligned=True,
                report_plan_current=True,
                review_approved=True,
                publication_locked=True,
                publication_build_exists=True,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(resolution.release, SubjectWorkflowJourneyStatus.RELEASE_BLOCKED_FIX_BUILD)
        lines = render_subject_workflow_journey_lines(resolution)
        self.assertIn("4. Release the report: blocked - fix the report build", lines)

    def test_resolve_journey_handles_markdown_busy_first_subject(self) -> None:
        resolution = resolve_subject_workflow_journey(
            SubjectWorkflowStateInputs(
                subject_exists=False,
                context_opened=False,
                admitted_unit_count=0,
                pending_import_count=0,
                itemization_exists=False,
                itemization_current=False,
                itemization_valid=False,
                draft_composition_exists=False,
                draft_composition_current=False,
                maintained_files_aligned=False,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
                markdown_busy=True,
                markdown_source_label="example.md",
            )
        )

        self.assertEqual(resolution.gather, SubjectWorkflowJourneyStatus.GATHER_IMPORTING)
        self.assertEqual(
            resolution.itemize,
            SubjectWorkflowJourneyStatus.ITEMIZE_WAITING_FOR_FIRST_IMPORT,
        )
        lines = render_subject_workflow_journey_lines(resolution)
        self.assertIn("1. Gather material: importing example.md", lines)
        self.assertIn(
            "2. Itemize the subject: blocked until the import finishes and creates the first subject",
            lines,
        )

    def test_resolve_current_step_requires_itemize_before_draft_after_maintained_files_align(self) -> None:
        resolution = resolve_subject_workflow_current_step(
            SubjectWorkflowCurrentStepInputs(
                phase=SubjectWorkflowTab.RESEARCH,
                subject_exists=True,
                context_opened=True,
                pending_import_count=0,
                maintained_files_aligned=True,
                itemization_exists=False,
                itemization_current=False,
                itemization_valid=False,
                draft_composition_exists=False,
                draft_composition_current=False,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(resolution.state, SubjectWorkflowCurrentStepState.ITEMIZE_GENERATE)

    def test_resolve_current_step_in_draft_prefers_report_plan_creation_over_review_gate(self) -> None:
        resolution = resolve_subject_workflow_current_step(
            SubjectWorkflowCurrentStepInputs(
                phase=SubjectWorkflowTab.DRAFT,
                subject_exists=True,
                context_opened=True,
                pending_import_count=0,
                maintained_files_aligned=False,
                itemization_exists=True,
                itemization_current=True,
                itemization_valid=True,
                draft_composition_exists=True,
                draft_composition_current=True,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(
            resolution.state,
            SubjectWorkflowCurrentStepState.DRAFT_CREATE_REPORT_PLAN,
        )

    def test_resolve_current_step_in_draft_prefers_shaping_before_report_plan_for_decision_flow(self) -> None:
        resolution = resolve_subject_workflow_current_step(
            SubjectWorkflowCurrentStepInputs(
                phase=SubjectWorkflowTab.DRAFT,
                subject_exists=True,
                context_opened=True,
                pending_import_count=0,
                maintained_files_aligned=False,
                itemization_exists=True,
                itemization_current=True,
                itemization_valid=True,
                draft_composition_exists=True,
                draft_composition_current=True,
                draft_shape_precedes_report_plan=True,
                report_plan_current=False,
                review_approved=False,
                publication_locked=False,
                publication_build_exists=False,
                publication_build_ready=False,
                release_packet_opened=False,
                release_review_completed=False,
            )
        )

        self.assertEqual(
            resolution.state,
            SubjectWorkflowCurrentStepState.DRAFT_SHAPE,
        )

    def test_preferred_guidance_tab_keeps_gather_for_maintained_files_but_routes_itemize_after_alignment(self) -> None:
        self.assertEqual(
            preferred_subject_workflow_tab_for_current_step(
                state=SubjectWorkflowCurrentStepState.REVIEW_CHECK_MAINTAINED_FILES,
                current_tab=SubjectWorkflowTab.RESEARCH,
            ),
            SubjectWorkflowTab.RESEARCH,
        )
        self.assertEqual(
            preferred_subject_workflow_tab_for_current_step(
                state=SubjectWorkflowCurrentStepState.ITEMIZE_GENERATE,
                current_tab=SubjectWorkflowTab.RESEARCH,
            ),
            SubjectWorkflowTab.ITEMIZE,
        )

    def test_preferred_guidance_tab_keeps_draft_when_draft_is_already_approved(self) -> None:
        self.assertEqual(
            preferred_subject_workflow_tab_for_current_step(
                state=SubjectWorkflowCurrentStepState.DRAFT_APPROVED,
                current_tab=SubjectWorkflowTab.DRAFT,
            ),
            SubjectWorkflowTab.DRAFT,
        )


if __name__ == "__main__":
    unittest.main()
