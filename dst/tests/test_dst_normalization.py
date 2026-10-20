import unittest
from dataclasses import replace

from coordinated_transformation import admissible_transitions, executable_decisions, valid_decisions
from dst import (
    build_dst_normalization_prompt,
    coordinated_model_from_normalized_case,
    list_dst_normalized_fixture_paths,
    load_dst_normalized_case,
    load_dst_normalized_cases,
    load_dst_use_cases,
    normalized_case_from_fixture,
)


class DstNormalizationTests(unittest.TestCase):
    def test_normalized_fixture_root_lists_checked_in_prompt_normalization_cases(self) -> None:
        paths = list_dst_normalized_fixture_paths()

        self.assertEqual(
            [path.name for path in paths],
            [
                "city-bus-ticketing-modernization.json",
                "community-clinic-appointment-reminders.json",
                "hospital-medication-system-upgrade.json",
                "national-school-system-exam-digitization-rollout.json",
                "regional-emergency-alerting-system.json",
                "smart-city-travel-incremental.json",
                "town-library-self-checkout-rollout.json",
            ],
        )

    def test_load_dst_normalized_cases_reads_valid_typed_prompt_outputs(self) -> None:
        cases = load_dst_normalized_cases()

        self.assertEqual(len(cases), 7)
        self.assertEqual(
            [case.fixture_id for case in cases],
            [
                "city-bus-ticketing-modernization",
                "community-clinic-appointment-reminders",
                "hospital-medication-system-upgrade",
                "national-school-system-exam-digitization-rollout",
                "regional-emergency-alerting-system",
                "smart-city-travel-incremental",
                "town-library-self-checkout-rollout",
            ],
        )
        case = cases[0]
        self.assertEqual(
            case.candidate_sets.candidate_transition_ids_from_current_state,
            ("t1", "t3"),
        )
        self.assertEqual(
            {item.id for item in case.states if item.is_target is True},
            {"s2", "s3"},
        )

    def test_build_dst_normalization_prompt_wraps_template_around_prompt_input(self) -> None:
        prompt = build_dst_normalization_prompt("Governed discovery candidate paths:\n- p1")

        self.assertIn("You are an information-extraction engine for a coordinated-transformation decision model.", prompt)
        self.assertIn("INPUT TO NORMALIZE", prompt)
        self.assertIn("Governed discovery candidate paths:", prompt)

    def test_normalized_case_from_fixture_falls_back_to_deterministic_structured_case_when_no_checked_in_case_exists(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "hospital-medication-system-upgrade"
        )
        synthetic_fixture = replace(
            fixture,
            fixture_id="hospital-medication-system-upgrade-synthetic",
            source_ref="dst/Hospital medication system upgrade synthetic.md",
        )

        self.assertIsNone(load_dst_normalized_case(synthetic_fixture.fixture_id))
        case = normalized_case_from_fixture(synthetic_fixture)

        self.assertEqual(case.fixture_id, synthetic_fixture.fixture_id)
        self.assertEqual(case.context.evaluation_state_id, "s0")
        self.assertEqual([item.id for item in case.transitions], ["t1"])
        self.assertEqual([item.id for item in case.decisions], ["x1"])
        self.assertEqual(
            case.candidate_sets.candidate_transition_ids_from_current_state,
            ("t1",),
        )
        self.assertEqual(
            case.candidate_sets.candidate_decision_ids_from_current_state,
            ("x1",),
        )

    def test_normalized_case_builds_formal_model_that_exposes_current_admissible_and_executable_options(self) -> None:
        case = load_dst_normalized_case("city-bus-ticketing-modernization")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual({state.name for state in model.current}, {"legacy fare system"})
        self.assertEqual(
            {state.name for state in model.target_state},
            {"hybrid card plus compatibility tools", "full account-based open-loop payment"},
        )
        self.assertEqual(
            [transition.name for transition in admissible_transitions(model, current_state)],
            ["upgrade existing transit card system"],
        )
        self.assertEqual(
            [decision.name for decision in valid_decisions(model, current_state)],
            ["Start with closed-loop upgrade"],
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Start with closed-loop upgrade"],
        )

    def test_hospital_normalized_case_materializes_the_single_safe_cutover_option(self) -> None:
        case = load_dst_normalized_case("hospital-medication-system-upgrade")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual(
            [transition.name for transition in admissible_transitions(model, current_state)],
            ["prepared direct cutover to validated electronic prescribing"],
        )
        self.assertEqual(
            [decision.name for decision in valid_decisions(model, current_state)],
            ["Complete readiness work, then cut over directly"],
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Complete readiness work, then cut over directly"],
        )

    def test_national_normalized_case_materializes_competing_rollout_options_with_one_executable_recommendation(self) -> None:
        case = load_dst_normalized_case("national-school-system-exam-digitization-rollout")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual(
            set(decision.name for decision in valid_decisions(model, current_state)),
            {
                "Conservative layered rollout",
                "Readiness-based regional rollout",
                "Resilience-first audited rollout",
            },
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Resilience-first audited rollout"],
        )

    def test_regional_normalized_case_materializes_balanced_configuration_as_the_only_executable_option(self) -> None:
        case = load_dst_normalized_case("regional-emergency-alerting-system")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual(
            set(decision.name for decision in valid_decisions(model, current_state)),
            {
                "Resilience-first configuration",
                "Inclusion-first configuration",
                "Balanced configuration",
            },
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Balanced configuration"],
        )

    def test_library_normalized_case_materializes_staffed_rollout_as_the_only_executable_option(self) -> None:
        case = load_dst_normalized_case("town-library-self-checkout-rollout")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual(
            [decision.name for decision in valid_decisions(model, current_state)],
            ["Branch pilot with staffed support"],
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Branch pilot with staffed support"],
        )

    def test_clinic_normalized_case_keeps_inclusive_rollout_executable_and_lean_sms_only_valid(self) -> None:
        case = load_dst_normalized_case("community-clinic-appointment-reminders")
        self.assertIsNotNone(case)
        assert case is not None

        model = coordinated_model_from_normalized_case(case)
        current_state = next(iter(model.current))

        self.assertEqual(
            set(decision.name for decision in valid_decisions(model, current_state)),
            {"Inclusive reminder rollout", "Lean SMS rollout"},
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Inclusive reminder rollout"],
        )


if __name__ == "__main__":
    unittest.main()
