from __future__ import annotations

import unittest

from dst.tests.dst_revision_bdd_support import DstRevisionStory


class DstRevisionBehaviorBDDTests(unittest.TestCase):
    def test_bdd_a_new_constraint_can_block_a_previously_executable_decision_without_changing_the_core_theory(self) -> None:
        story = DstRevisionStory(self)

        story.given_the_direct_route_is_currently_admissible()
        story.then_the_original_snapshot_is_core_valid()
        story.then_the_direct_decision_is_executable_in_the_original_snapshot()

        story.when_a_new_active_constraint_is_introduced_without_transition_clearance()
        story.then_the_revised_snapshot_is_core_valid()
        story.then_the_same_direct_decision_is_blocked_in_the_revised_snapshot()

    def test_bdd_a_new_actor_does_not_unblock_progress_until_the_revision_changes_admissibility_relevant_facts(self) -> None:
        story = DstRevisionStory(self)

        story.given_the_direct_route_is_currently_blocked()
        story.then_the_original_snapshot_is_core_valid()
        story.when_a_new_actor_joins_but_no_admissibility_fact_changes()
        story.then_the_revised_snapshot_is_core_valid()
        story.then_the_new_actor_has_not_magically_unblocked_the_route()

        story.when_the_revision_satisfies_the_missing_dependency_and_grants_constraint_clearance()
        story.then_the_final_snapshot_is_core_valid()
        story.then_the_direct_route_becomes_executable_only_after_the_admissibility_facts_change()

    def test_bdd_a_revision_can_resume_progress_by_enabling_an_alternative_transition_while_the_old_one_stays_blocked(self) -> None:
        story = DstRevisionStory(self)

        story.given_the_direct_route_is_currently_blocked()
        story.when_an_alternative_staged_transition_is_added()
        story.then_the_revised_snapshot_is_core_valid()
        story.then_the_alternative_path_is_available_while_the_original_direct_path_remains_blocked()

    def test_bdd_boundary_friction_can_raise_risk_without_changing_admissibility(self) -> None:
        story = DstRevisionStory(self)

        story.given_the_direct_route_is_currently_admissible()
        story.when_boundary_friction_appears_without_changing_admissibility()
        story.then_the_revised_snapshot_is_core_valid()
        story.then_boundary_friction_marks_the_route_risky_without_making_it_inadmissible()


if __name__ == "__main__":
    unittest.main()
