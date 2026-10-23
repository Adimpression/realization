from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
THEORY_PATH = ROOT / "RESUMPTION.md"
SCENARIO_PATH = (
    ROOT / "trials" / "governed_chat" / "RESUMPTION_JOURNEY.json"
)

EXECUTABLE_PROBES = {
    "start_brief": "test_corrections_restart_and_presentation_do_not_replace_state",
    "correct_color": "test_corrections_restart_and_presentation_do_not_replace_state",
    "correct_deadline": "test_corrections_restart_and_presentation_do_not_replace_state",
    "inspect_current_after_corrections": "test_corrections_restart_and_presentation_do_not_replace_state",
    "restart_and_resume": "test_corrections_restart_and_presentation_do_not_replace_state",
    "replace_provider_and_resume": "test_corrections_restart_and_presentation_do_not_replace_state",
    "rerender_then_resume": "test_corrections_restart_and_presentation_do_not_replace_state",
    "interrupt_candidate": "test_interruption_and_resume_exclude_unfinished_candidate_work",
    "resume_after_interruption": "test_interruption_and_resume_exclude_unfinished_candidate_work",
    "augment_budget": "test_augmentation_redirection_and_clarification_preserve_uncertainty",
    "redirect_checklist": "test_augmentation_redirection_and_clarification_preserve_uncertainty",
    "clarify_realignment": "test_augmentation_redirection_and_clarification_preserve_uncertainty",
    "explain_deadline": "test_explanation_and_reversal_use_persisted_path_artifacts",
    "verify_path": "test_explanation_and_reversal_use_persisted_path_artifacts",
    "reconstruct_path": "test_explanation_and_reversal_use_persisted_path_artifacts",
    "reverse_deadline": "test_explanation_and_reversal_use_persisted_path_artifacts",
    "ambiguous_reversal": "test_explanation_and_reversal_use_persisted_path_artifacts",
    "branch_executive": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "branch_technical": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "merge_branches": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "stale_continuation_rejected": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "independent_request": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "similarity_cannot_bind": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
    "prose_only_handoff_rejected": "test_branches_stale_anchors_and_unbound_prose_preserve_identity",
}


def _load_scenario() -> dict[str, object]:
    payload = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("The resumption journey must be a JSON object.")
    return payload


def _theory_principle_ids() -> set[str]:
    text = THEORY_PATH.read_text(encoding="utf-8")
    return set(re.findall(r"^### (3\.\d+) ", text, flags=re.MULTILINE))


class ResumptionJourneySpecificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = _load_scenario()
        self.flows = list(self.scenario["flows"])
        self.steps = {
            step["step_id"]: step
            for flow in self.flows
            for step in flow["steps"]
        }

    def test_scenario_uses_a_neutral_domain(self) -> None:
        serialized = json.dumps(self.scenario).casefold()
        self.assertIn("cedar", serialized)

    def test_every_resumption_principle_has_a_concrete_probe(self) -> None:
        coverage = self.scenario["principle_coverage"]
        self.assertEqual(_theory_principle_ids(), set(coverage))
        for principle_id, step_ids in coverage.items():
            with self.subTest(principle=principle_id):
                self.assertTrue(step_ids)
                self.assertTrue(set(step_ids).issubset(self.steps))

    def test_every_scenario_step_has_an_executable_real_host_probe(self) -> None:
        from core_app.tests import test_resumption_journey as executable

        self.assertEqual(set(self.steps), set(EXECUTABLE_PROBES))
        test_case = executable.ResumptionConversationJourneyTests
        for step_id, method_name in EXECUTABLE_PROBES.items():
            with self.subTest(step=step_id):
                self.assertTrue(hasattr(test_case, method_name))

    def test_scenario_includes_every_normative_operation_family(self) -> None:
        operations = {step["operation"] for step in self.steps.values()}
        required = {
            "start",
            "correct",
            "restart_host_and_resume",
            "replace_provider_and_resume",
            "rerender_then_resume",
            "interrupt",
            "resume_after_interruption",
            "augment",
            "redirect_and_realign",
            "continue_realignment",
            "explain",
            "verify",
            "reconstruct",
            "reverse",
            "branch",
            "merge",
            "continue_from_stale_head",
            "attempt_similarity_only_continuation",
            "attempt_prose_only_handoff",
        }
        self.assertTrue(required.issubset(operations))

    def test_baseline_keeps_turn_completion_separate_from_objective_completion(
        self,
    ) -> None:
        for step_id in ("start_brief", "correct_color", "correct_deadline"):
            with self.subTest(step=step_id):
                expected = self.steps[step_id]["expect"]
                self.assertTrue(expected["turn_complete"])
                self.assertFalse(expected["objective_complete"])
                self.assertIn("audience", expected["non_achieved"])

    def test_independent_request_establishes_identity_explicitly(self) -> None:
        prompt = self.steps["independent_request"]["prompt"].casefold()

        self.assertIn("separately", prompt)
        self.assertIn("new objective", prompt)

    def test_direction_change_requires_explicit_uncertainty_and_realignment(
        self,
    ) -> None:
        redirected = self.steps["redirect_checklist"]["expect"]
        self.assertEqual(
            {"color", "deadline", "audience", "budget"},
            set(redirected["unresolved_applicability"]),
        )
        self.assertFalse(redirected["old_frontier_executable"])
        clarified = self.steps["clarify_realignment"]["expect"]
        self.assertEqual([], clarified["unresolved_applicability"])


if __name__ == "__main__":
    unittest.main()
