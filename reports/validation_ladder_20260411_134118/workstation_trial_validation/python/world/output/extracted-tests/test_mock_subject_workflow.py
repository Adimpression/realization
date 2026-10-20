from __future__ import annotations

import unittest

from workstation.mock_subject_workflow import (
    apply_mock_subject_action,
    default_mock_subject_scenarios,
    new_mock_subject_progress,
    render_mock_subject_status,
    render_mock_subject_workspace,
)


class MockSubjectWorkflowTests(unittest.TestCase):
    def test_mock_subject_flow_advances_from_research_to_publication(self) -> None:
        scenario = default_mock_subject_scenarios()[0]
        progress = new_mock_subject_progress()

        self.assertIn("pending", render_mock_subject_status(scenario=scenario, progress=progress, phase="research"))

        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="observe_source")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="draft_intake")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="admit_delta")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="open_context")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="compare_projections")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="approve_review")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="lock_publication")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="build_report")

        status_text = render_mock_subject_status(scenario=scenario, progress=progress, phase="publication")
        self.assertIn("delta=admitted", status_text)
        self.assertIn("ready=yes", status_text)
        self.assertIn("build=ready", status_text)

    def test_review_and_publication_renderers_switch_preview_targets(self) -> None:
        scenario = default_mock_subject_scenarios()[1]
        progress = new_mock_subject_progress()

        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="observe_source")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="draft_intake")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="admit_delta")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="toggle_review_preview")

        review_text = render_mock_subject_workspace(scenario=scenario, progress=progress, phase="review")
        self.assertIn("Projection Preview [subject.typ]", review_text)

        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="open_context")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="compare_projections")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="approve_review")
        apply_mock_subject_action(scenario=scenario, progress=progress, action_key="toggle_publication_preview")

        publication_text = render_mock_subject_workspace(scenario=scenario, progress=progress, phase="publication")
        self.assertIn("Output Preview [report.md]", publication_text)

    def test_last_assistant_message_can_be_captured_into_research_intake(self) -> None:
        scenario = default_mock_subject_scenarios()[0]
        progress = new_mock_subject_progress()

        result = apply_mock_subject_action(
            scenario=scenario,
            progress=progress,
            action_key="capture_last_assistant",
            assistant_message_text="Conservation of amount should stay at subject level while executable dilution logic stays derived.",
        )

        self.assertIn("added", result.status_text.lower())
        self.assertEqual(len(progress.captured_assistant_messages), 1)

        research_text = render_mock_subject_workspace(scenario=scenario, progress=progress, phase="research")
        self.assertIn("captured assistant messages available to intake: 1", research_text)


if __name__ == "__main__":
    unittest.main()
