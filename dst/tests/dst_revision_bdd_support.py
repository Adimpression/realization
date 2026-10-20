from __future__ import annotations

from dataclasses import replace
import unittest

from coordinated_transformation import (
    Actor,
    Boundary,
    Capability,
    Constraint,
    Decision,
    Dependency,
    Model,
    Objective,
    State,
    Transition,
    admissible_transition,
    check_axioms,
    executable_decision,
    executable_decisions,
    least_reachable_closure,
    risk_transition,
    valid_decision,
)


def with_reachability(model: Model) -> Model:
    model.reachable = least_reachable_closure(model)
    return model


class DstRevisionStory:
    def __init__(self, test_case: unittest.TestCase) -> None:
        self.test_case = test_case
        self.operator = Actor("transit authority")
        self.regulator = Actor("city regulator")
        self.certifier = Actor("certification authority")

        self.continuity = Objective("preserve continuity")

        self.closed_loop = Capability("improved closed-loop card system")
        self.open_loop = Capability("open-loop payment acceptance")

        self.certified = Dependency("certification approval")
        self.network_ready = Dependency("payment network readiness")

        self.audit_gate = Constraint("audit gate")
        self.no_downtime = Constraint("no downtime")

        self.payment_boundary = Boundary("transit-payment boundary")

        self.legacy = State("legacy fare system")
        self.staged = State("staged card modernization")
        self.target = State("full open-loop payment")

        self.staged_transition = Transition("staged modernization route")
        self.direct_transition = Transition("direct open-loop route")

        self.select_staged = Decision("select staged modernization")
        self.select_direct = Decision("select direct modernization")

        self.base_direct_snapshot = None
        self.revised_snapshot = None
        self.final_snapshot = None

    def _snapshot_with_direct_route_ready(self) -> Model:
        return with_reachability(
            Model(
                actors=frozenset({self.operator, self.regulator}),
                objectives=frozenset({self.continuity}),
                capabilities=frozenset({self.open_loop}),
                dependencies=frozenset({self.certified, self.network_ready}),
                constraints=frozenset(),
                boundaries=frozenset({self.payment_boundary}),
                states=frozenset({self.legacy, self.target}),
                transitions=frozenset({self.direct_transition}),
                decisions=frozenset({self.select_direct}),
                controls=frozenset({(self.operator, self.open_loop)}),
                can_decide=frozenset({(self.operator, self.select_direct)}),
                advances=frozenset({(self.open_loop, self.continuity)}),
                changes=frozenset({(self.direct_transition, self.open_loop)}),
                requires_for_transition=frozenset(
                    {
                        (self.direct_transition, self.certified),
                        (self.direct_transition, self.network_ready),
                    }
                ),
                satisfied=frozenset(
                    {
                        (self.certified, self.legacy),
                        (self.network_ready, self.legacy),
                    }
                ),
                crosses_transition=frozenset({(self.direct_transition, self.payment_boundary)}),
                current=frozenset({self.legacy}),
                target_state=frozenset({self.target}),
                selects=frozenset({(self.select_direct, self.direct_transition)}),
                assigns=frozenset({(self.select_direct, self.operator, self.open_loop)}),
                source={self.direct_transition: self.legacy},
                target={self.direct_transition: self.target},
            )
        )

    def _snapshot_with_direct_route_blocked(self) -> Model:
        return with_reachability(
            Model(
                actors=frozenset({self.operator, self.regulator}),
                objectives=frozenset({self.continuity}),
                capabilities=frozenset({self.open_loop}),
                dependencies=frozenset({self.certified, self.network_ready}),
                constraints=frozenset({self.audit_gate}),
                boundaries=frozenset({self.payment_boundary}),
                states=frozenset({self.legacy, self.target}),
                transitions=frozenset({self.direct_transition}),
                decisions=frozenset({self.select_direct}),
                controls=frozenset({(self.operator, self.open_loop)}),
                can_decide=frozenset({(self.operator, self.select_direct)}),
                advances=frozenset({(self.open_loop, self.continuity)}),
                changes=frozenset({(self.direct_transition, self.open_loop)}),
                requires_for_transition=frozenset(
                    {
                        (self.direct_transition, self.certified),
                        (self.direct_transition, self.network_ready),
                    }
                ),
                constrained_by_transition=frozenset({(self.direct_transition, self.audit_gate)}),
                active=frozenset({(self.audit_gate, self.legacy)}),
                satisfied=frozenset({(self.network_ready, self.legacy)}),
                crosses_transition=frozenset({(self.direct_transition, self.payment_boundary)}),
                current=frozenset({self.legacy}),
                target_state=frozenset({self.target}),
                selects=frozenset({(self.select_direct, self.direct_transition)}),
                assigns=frozenset({(self.select_direct, self.operator, self.open_loop)}),
                source={self.direct_transition: self.legacy},
                target={self.direct_transition: self.target},
            )
        )

    def given_the_direct_route_is_currently_admissible(self) -> None:
        self.base_direct_snapshot = self._snapshot_with_direct_route_ready()

    def given_the_direct_route_is_currently_blocked(self) -> None:
        self.base_direct_snapshot = self._snapshot_with_direct_route_blocked()

    def when_a_new_active_constraint_is_introduced_without_transition_clearance(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.revised_snapshot = with_reachability(
            replace(
                self.base_direct_snapshot,
                constraints=frozenset({self.audit_gate}),
                constrained_by_transition=frozenset({(self.direct_transition, self.audit_gate)}),
                active=frozenset({(self.audit_gate, self.legacy)}),
                transition_admissible_under=frozenset(),
            )
        )

    def when_a_new_actor_joins_but_no_admissibility_fact_changes(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.revised_snapshot = with_reachability(
            replace(
                self.base_direct_snapshot,
                actors=frozenset({self.operator, self.regulator, self.certifier}),
            )
        )

    def when_the_revision_satisfies_the_missing_dependency_and_grants_constraint_clearance(self) -> None:
        self.test_case.assertIsNotNone(self.revised_snapshot)
        assert self.revised_snapshot is not None
        self.final_snapshot = with_reachability(
            replace(
                self.revised_snapshot,
                satisfied=frozenset(
                    {
                        (self.certified, self.legacy),
                        (self.network_ready, self.legacy),
                    }
                ),
                transition_admissible_under=frozenset(
                    {(self.direct_transition, self.audit_gate, self.legacy)}
                ),
            )
        )

    def when_an_alternative_staged_transition_is_added(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.revised_snapshot = with_reachability(
            replace(
                self.base_direct_snapshot,
                capabilities=frozenset({self.open_loop, self.closed_loop}),
                constraints=frozenset({self.audit_gate, self.no_downtime}),
                states=frozenset({self.legacy, self.staged, self.target}),
                transitions=frozenset({self.direct_transition, self.staged_transition}),
                decisions=frozenset({self.select_direct, self.select_staged}),
                controls=frozenset(
                    {
                        (self.operator, self.open_loop),
                        (self.operator, self.closed_loop),
                    }
                ),
                advances=frozenset(
                    {
                        (self.open_loop, self.continuity),
                        (self.closed_loop, self.continuity),
                    }
                ),
                changes=frozenset(
                    {
                        (self.direct_transition, self.open_loop),
                        (self.staged_transition, self.closed_loop),
                    }
                ),
                constrained_by_transition=frozenset({(self.direct_transition, self.audit_gate)}),
                active=frozenset(
                    {
                        (self.audit_gate, self.legacy),
                        (self.no_downtime, self.legacy),
                    }
                ),
                selects=frozenset(
                    {
                        (self.select_direct, self.direct_transition),
                        (self.select_staged, self.staged_transition),
                    }
                ),
                assigns=frozenset(
                    {
                        (self.select_direct, self.operator, self.open_loop),
                        (self.select_staged, self.operator, self.closed_loop),
                    }
                ),
                can_decide=frozenset(
                    {
                        (self.operator, self.select_direct),
                        (self.operator, self.select_staged),
                    }
                ),
                source={
                    self.direct_transition: self.legacy,
                    self.staged_transition: self.legacy,
                },
                target={
                    self.direct_transition: self.target,
                    self.staged_transition: self.staged,
                },
                target_state=frozenset({self.staged, self.target}),
            )
        )

    def when_boundary_friction_appears_without_changing_admissibility(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.revised_snapshot = with_reachability(
            replace(
                self.base_direct_snapshot,
                friction_at=frozenset({(self.payment_boundary, self.legacy)}),
            )
        )

    def then_the_original_snapshot_is_core_valid(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.test_case.assertEqual(check_axioms(self.base_direct_snapshot), [])

    def then_the_revised_snapshot_is_core_valid(self) -> None:
        self.test_case.assertIsNotNone(self.revised_snapshot)
        assert self.revised_snapshot is not None
        self.test_case.assertEqual(check_axioms(self.revised_snapshot), [])

    def then_the_final_snapshot_is_core_valid(self) -> None:
        self.test_case.assertIsNotNone(self.final_snapshot)
        assert self.final_snapshot is not None
        self.test_case.assertEqual(check_axioms(self.final_snapshot), [])

    def then_the_direct_decision_is_executable_in_the_original_snapshot(self) -> None:
        self.test_case.assertIsNotNone(self.base_direct_snapshot)
        assert self.base_direct_snapshot is not None
        self.test_case.assertTrue(
            admissible_transition(self.base_direct_snapshot, self.direct_transition, self.legacy)
        )
        self.test_case.assertTrue(
            valid_decision(self.base_direct_snapshot, self.select_direct, self.legacy)
        )
        self.test_case.assertTrue(
            executable_decision(self.base_direct_snapshot, self.select_direct, self.legacy)
        )

    def then_the_same_direct_decision_is_blocked_in_the_revised_snapshot(self) -> None:
        self.test_case.assertIsNotNone(self.revised_snapshot)
        assert self.revised_snapshot is not None
        self.test_case.assertFalse(
            admissible_transition(self.revised_snapshot, self.direct_transition, self.legacy)
        )
        self.test_case.assertFalse(
            valid_decision(self.revised_snapshot, self.select_direct, self.legacy)
        )
        self.test_case.assertFalse(
            executable_decision(self.revised_snapshot, self.select_direct, self.legacy)
        )
        self.test_case.assertEqual(executable_decisions(self.revised_snapshot, self.legacy), [])

    def then_the_new_actor_has_not_magically_unblocked_the_route(self) -> None:
        self.then_the_same_direct_decision_is_blocked_in_the_revised_snapshot()

    def then_the_direct_route_becomes_executable_only_after_the_admissibility_facts_change(self) -> None:
        self.test_case.assertIsNotNone(self.final_snapshot)
        assert self.final_snapshot is not None
        self.test_case.assertTrue(
            admissible_transition(self.final_snapshot, self.direct_transition, self.legacy)
        )
        self.test_case.assertTrue(
            executable_decision(self.final_snapshot, self.select_direct, self.legacy)
        )
        self.test_case.assertEqual(
            [item.name for item in executable_decisions(self.final_snapshot, self.legacy)],
            ["select direct modernization"],
        )

    def then_the_alternative_path_is_available_while_the_original_direct_path_remains_blocked(self) -> None:
        self.test_case.assertIsNotNone(self.revised_snapshot)
        assert self.revised_snapshot is not None
        self.test_case.assertFalse(
            admissible_transition(self.revised_snapshot, self.direct_transition, self.legacy)
        )
        self.test_case.assertTrue(
            admissible_transition(self.revised_snapshot, self.staged_transition, self.legacy)
        )
        self.test_case.assertEqual(
            {item.name for item in executable_decisions(self.revised_snapshot, self.legacy)},
            {"select staged modernization"},
        )

    def then_boundary_friction_marks_the_route_risky_without_making_it_inadmissible(self) -> None:
        self.test_case.assertIsNotNone(self.revised_snapshot)
        assert self.revised_snapshot is not None
        self.test_case.assertTrue(
            admissible_transition(self.revised_snapshot, self.direct_transition, self.legacy)
        )
        self.test_case.assertTrue(
            executable_decision(self.revised_snapshot, self.select_direct, self.legacy)
        )
        self.test_case.assertTrue(
            risk_transition(self.revised_snapshot, self.direct_transition, self.legacy)
        )
