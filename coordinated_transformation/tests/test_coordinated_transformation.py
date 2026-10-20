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
    TimePoint,
    Transition,
    admissible_capabilities,
    admissible_transition_paths,
    admissible_transitions,
    check_axioms,
    executable_decision,
    executable_decisions,
    least_reachable_closure,
    valid_decision,
    valid_decisions,
)


def build_example_model() -> tuple[Model, State, State, Decision, Transition, Capability]:
    a1 = Actor("operator")
    a2 = Actor("regulator")

    o1 = Objective("continuity")

    k_old = Capability("legacy")
    k_new = Capability("unified")

    d1 = Dependency("certified")
    q1 = Constraint("no_mixed_mode")
    b1 = Boundary("regulatory")

    s0 = State("legacy_state")
    s1 = State("target_state")

    t1 = Transition("migrate")
    dec1 = Decision("select_migrate")
    tm1 = TimePoint("2026-04-14T10:00:00Z")

    m = Model(
        actors=frozenset({a1, a2}),
        objectives=frozenset({o1}),
        capabilities=frozenset({k_old, k_new}),
        dependencies=frozenset({d1}),
        constraints=frozenset({q1}),
        boundaries=frozenset({b1}),
        states=frozenset({s0, s1}),
        transitions=frozenset({t1}),
        decisions=frozenset({dec1}),
        times=frozenset({tm1}),
        controls=frozenset({(a1, k_new)}),
        can_decide=frozenset({(a1, dec1)}),
        advances=frozenset({(k_new, o1)}),
        requires=frozenset({(k_new, d1)}),
        limited_by=frozenset({(k_new, q1)}),
        available=frozenset({(k_old, s0), (k_new, s1)}),
        operational=frozenset({(k_old, s0)}),
        satisfied=frozenset({(d1, s0)}),
        active=frozenset({(q1, s0)}),
        admissible_under=frozenset({(k_new, q1, s0)}),
        current=frozenset({s0}),
        target_state=frozenset({s1}),
        changes=frozenset({(t1, k_new)}),
        requires_for_transition=frozenset({(t1, d1)}),
        constrained_by_transition=frozenset({(t1, q1)}),
        transition_admissible_under=frozenset({(t1, q1, s0)}),
        selects=frozenset({(dec1, t1)}),
        assigns=frozenset({(dec1, a1, k_new)}),
        at_time=frozenset({(dec1, tm1)}),
        valid=frozenset({(dec1, s0)}),
        executable=frozenset({(dec1, s0)}),
        source={t1: s0},
        target={t1: s1},
    )
    return m, s0, s1, dec1, t1, k_new


class CoordinatedTransformationTests(unittest.TestCase):
    def test_example_model_matches_theory_behavior(self) -> None:
        m, s0, s1, dec1, t1, k_new = build_example_model()
        m.reachable = least_reachable_closure(m)

        self.assertCountEqual(
            [capability.name for capability in admissible_capabilities(m, s0)],
            ["legacy", "unified"],
        )
        self.assertEqual(admissible_transitions(m, s0), [t1])
        self.assertEqual(valid_decisions(m, s0), [dec1])
        self.assertEqual(executable_decisions(m, s0), [dec1])
        self.assertIn((s0, s0), m.reachable)
        self.assertIn((s1, s1), m.reachable)
        self.assertIn((s0, s1), m.reachable)
        self.assertEqual(check_axioms(m), [])

    def test_valid_decision_requires_assigned_actor_for_every_changed_capability(self) -> None:
        m, s0, _s1, dec1, _t1, _k_new = build_example_model()
        m.assigns = frozenset()

        self.assertFalse(valid_decision(m, dec1, s0))
        self.assertFalse(executable_decision(m, dec1, s0))

    def test_reachability_closure_adds_transitive_pairs(self) -> None:
        s0 = State("s0")
        s1 = State("s1")
        s2 = State("s2")

        t1 = Transition("t1")
        t2 = Transition("t2")

        d = Dependency("ready")

        m = Model(
            states=frozenset({s0, s1, s2}),
            transitions=frozenset({t1, t2}),
            dependencies=frozenset({d}),
            requires_for_transition=frozenset({(t1, d), (t2, d)}),
            satisfied=frozenset({(d, s0), (d, s1)}),
            source={t1: s0, t2: s1},
            target={t1: s1, t2: s2},
        )

        reachable = least_reachable_closure(m)

        self.assertIn((s0, s1), reachable)
        self.assertIn((s1, s2), reachable)
        self.assertIn((s0, s2), reachable)

    def test_axiom_checker_reports_multiple_selected_transitions(self) -> None:
        s0 = State("s0")
        s1 = State("s1")
        s2 = State("s2")
        t1 = Transition("t1")
        t2 = Transition("t2")
        dec = Decision("dec")

        m = Model(
            states=frozenset({s0, s1, s2}),
            transitions=frozenset({t1, t2}),
            decisions=frozenset({dec}),
            selects=frozenset({(dec, t1), (dec, t2)}),
            source={t1: s0, t2: s0},
            target={t1: s1, t2: s2},
        )

        violations = check_axioms(m)

        self.assertTrue(any(v.axiom == "A1" for v in violations))

    def test_admissible_transition_paths_enumerates_multi_step_paths_to_target(self) -> None:
        s0 = State("s0")
        s1 = State("s1")
        s2 = State("s2")
        t1 = Transition("t1")
        t2 = Transition("t2")
        d = Dependency("ready")

        m = Model(
            states=frozenset({s0, s1, s2}),
            transitions=frozenset({t1, t2}),
            dependencies=frozenset({d}),
            current=frozenset({s0}),
            target_state=frozenset({s2}),
            requires_for_transition=frozenset({(t1, d), (t2, d)}),
            satisfied=frozenset({(d, s0), (d, s1)}),
            source={t1: s0, t2: s1},
            target={t1: s1, t2: s2},
        )

        paths = admissible_transition_paths(m)

        self.assertEqual(len(paths), 1)
        self.assertEqual(tuple(transition.name for transition in paths[0].transitions), ("t1", "t2"))
        self.assertEqual(tuple(state.name for state in paths[0].states), ("s0", "s1", "s2"))


if __name__ == "__main__":
    unittest.main()
