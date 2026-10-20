import unittest

from dst import (
    DST_SOURCE_ROOT,
    DST_TYPED_FIXTURE_ROOT,
    coordinated_model_from_dst_projection,
    list_dst_fixture_paths,
    list_dst_source_paths,
    load_dst_fixture_catalog,
    load_dst_source_use_cases,
    load_dst_use_cases,
    match_dst_fixture_for_source_refs,
    normalize_dst_source_ref,
    project_dst_fixture_to_decision_frame,
)
from coordinated_transformation import admissible_transitions, executable_decisions, valid_decisions


class DstFixtureTests(unittest.TestCase):
    def test_typed_fixture_root_lists_current_checked_in_dst_fixtures(self) -> None:
        paths = list_dst_fixture_paths()

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
        self.assertTrue(all(path.parent == DST_TYPED_FIXTURE_ROOT for path in paths))

    def test_source_root_lists_current_markdown_use_case_corpus(self) -> None:
        paths = list_dst_source_paths()

        self.assertEqual(
            [path.name for path in paths],
            [
                "City bus prose v1.md",
                "City bus prose v10.md",
                "City bus prose v2.md",
                "City bus prose v3.md",
                "City bus prose v4.md",
                "City bus prose v5.md",
                "City bus prose v6.md",
                "City bus prose v7.md",
                "City bus prose v8.md",
                "City bus prose v9.md",
                "City bus ticketing modernization.md",
                "Community center room booking reminders.md",
                "Community clinic appointment reminders.md",
                "Hospital medication system upgrade.md",
                "National School System Exam Digitization Rollout.md",
                "Regional emergency alerting system.md",
                "School canteen cashless payments.md",
                "Town library self-checkout rollout.md",
            ],
        )
        self.assertTrue(all(path.parent == DST_SOURCE_ROOT for path in paths))

    def test_load_dst_fixture_catalog_reads_checked_in_typed_cases(self) -> None:
        catalog = load_dst_fixture_catalog()

        self.assertEqual(len(catalog.fixtures), 7)
        self.assertEqual(catalog.duplicate_title_keys, {})
        self.assertEqual(
            [fixture.fixture_id for fixture in catalog.fixtures],
            [
                "smart-city-travel-incremental",
                "city-bus-ticketing-modernization",
                "community-clinic-appointment-reminders",
                "hospital-medication-system-upgrade",
                "national-school-system-exam-digitization-rollout",
                "regional-emergency-alerting-system",
                "town-library-self-checkout-rollout",
            ],
        )

    def test_source_compatible_dst_cases_reconcile_to_checked_in_typed_fixtures(self) -> None:
        typed = {fixture.fixture_id: fixture.to_dict() for fixture in load_dst_use_cases()}
        projected = {fixture.fixture_id: fixture.to_dict() for fixture in load_dst_source_use_cases()}

        self.assertEqual(
            projected["community-clinic-appointment-reminders"],
            typed["community-clinic-appointment-reminders"],
        )
        self.assertEqual(
            projected["town-library-self-checkout-rollout"],
            typed["town-library-self-checkout-rollout"],
        )

    def test_source_only_cases_without_candidate_paths_remain_available_for_workstation_discovery(self) -> None:
        projected = {fixture.fixture_id: fixture for fixture in load_dst_source_use_cases()}

        school = projected["school-canteen-cashless-payments"]
        center = projected["community-center-room-booking-reminders"]

        self.assertEqual(school.candidate_paths, ())
        self.assertEqual(center.candidate_paths, ())
        self.assertIsNotNone(school.section("objectives"))
        self.assertIsNotNone(center.section("constraints"))

    def test_hospital_fixture_captures_the_single_viable_path_not_the_inadmissible_one(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "hospital-medication-system-upgrade"
        )

        self.assertEqual(len(fixture.candidate_paths), 1)
        self.assertEqual(fixture.candidate_paths[0].title, "Outcome")
        self.assertEqual(fixture.candidate_paths[0].route_expression, "s0 -> s2")
        self.assertEqual(
            fixture.candidate_paths[0].highlights,
            (
                "`s0 -> s2`",
                "mixed-mode prescribing remains inadmissible because it violates safety and regulatory constraints",
                "direct cutover becomes viable only after training, integration, and approval are complete before go-live",
            ),
        )

    def test_national_fixture_uses_typed_entries_and_normalized_candidate_routes(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "national-school-system-exam-digitization-rollout"
        )

        self.assertEqual(len(fixture.section_entries("actors")), 11)
        self.assertEqual(len(fixture.section_entries("constraints")), 11)
        self.assertEqual(len(fixture.section_entries("transitions")), 13)
        self.assertEqual(
            fixture.section_entries("actors")[0].code,
            "a1",
        )
        self.assertEqual(
            fixture.section_entries("actors")[0].text,
            "national education ministry",
        )
        self.assertEqual(
            [path.route_expression for path in fixture.candidate_paths],
            [
                "s0 -> s1 -> s2 -> s5",
                "s0 -> s1 -> s2 -> s4 -> s6",
                "s0 -> s5",
                "s0 -> s1 -> s2 -> s9 -> s6",
                "s0 -> s1 -> s2 -> s3",
            ],
        )

    def test_regional_fixture_preserves_candidate_configurations_without_fake_transition_graph(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "regional-emergency-alerting-system"
        )

        self.assertEqual(len(fixture.section_entries("capabilities")), 8)
        self.assertEqual(len(fixture.section_entries("states")), 0)
        self.assertEqual(fixture.section("transitions"), None)
        self.assertEqual(
            [path.title for path in fixture.candidate_paths],
            [
                "Example A: speed-first configuration",
                "Example B: resilience-first configuration",
                "Example C: inclusion-first configuration",
                "Example D: balanced configuration",
            ],
        )

    def test_simple_library_fixture_still_reconciles_as_a_decision_publication_case(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "town-library-self-checkout-rollout"
        )

        self.assertEqual(fixture.summary, "A town library network wants shorter checkout lines and less repetitive desk work.")
        self.assertEqual(
            [path.route_expression for path in fixture.candidate_paths],
            ["s0 -> s1 -> s2", "s0 -> s3"],
        )

    def test_simple_clinic_fixture_keeps_three_easy_to_grasp_path_families(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "community-clinic-appointment-reminders"
        )

        self.assertEqual(len(fixture.section_entries("actors")), 5)
        self.assertEqual(
            [path.title for path in fixture.candidate_paths],
            [
                "Path A: inclusive reminder rollout",
                "Path B: lean SMS rollout",
                "Path C: portal-only reminders",
            ],
        )

    def test_fixture_can_project_to_coordinated_transformation_seed_surface(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        seed = fixture.coordinated_seed()

        self.assertEqual(seed.title, "City bus ticketing modernization")
        self.assertEqual(seed.source_ref, "dst/City bus ticketing modernization.md")
        self.assertEqual(len(seed.actors), 5)
        self.assertEqual(seed.objectives, ("o1", "o2", "o3"))
        self.assertEqual(seed.capabilities, ("k1", "k2", "k3", "k4"))
        self.assertEqual(seed.dependencies, ("d1", "d2", "d3"))
        self.assertEqual(seed.constraints, ("q1", "q2", "q3"))
        self.assertEqual(seed.boundaries, ("β1", "β2", "β3"))
        self.assertEqual(seed.states, ("s0", "s1", "s2", "s3"))
        self.assertEqual(seed.transitions, ("τ1", "τ2", "τ3"))
        self.assertEqual(seed.candidate_route_expressions, ("s0 -> s1 -> s2", "s0 -> s3"))

    def test_normalize_dst_source_ref_canonicalizes_repo_relative_and_absolute_refs(self) -> None:
        absolute = str((DST_SOURCE_ROOT / "City bus ticketing modernization.md").resolve())

        self.assertEqual(
            normalize_dst_source_ref("dst/City bus ticketing modernization.md"),
            "dst/City bus ticketing modernization.md",
        )
        self.assertEqual(
            normalize_dst_source_ref(absolute),
            "dst/City bus ticketing modernization.md",
        )

    def test_match_dst_fixture_for_source_refs_matches_repo_relative_and_absolute_source_refs(self) -> None:
        absolute = str((DST_SOURCE_ROOT / "City bus ticketing modernization.md").resolve())

        fixture = match_dst_fixture_for_source_refs(
            ("notes/unrelated.md", absolute),
            fixtures=load_dst_use_cases(),
        )

        self.assertIsNotNone(fixture)
        assert fixture is not None
        self.assertEqual(fixture.fixture_id, "city-bus-ticketing-modernization")

    def test_match_dst_fixture_for_source_refs_matches_staged_upload_by_unique_filename(self) -> None:
        staged_upload = "/tmp/workstation-root/uploads/flutter-shell-1/City bus prose v10.md"

        fixture = match_dst_fixture_for_source_refs(
            ("notes/unrelated.md", staged_upload),
            fixtures=load_dst_use_cases(),
        )

        self.assertIsNotNone(fixture)
        assert fixture is not None
        self.assertEqual(fixture.fixture_id, "smart-city-travel-incremental")

    def test_dst_fixture_can_project_to_decision_frame_and_decision_items(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        projection = project_dst_fixture_to_decision_frame(fixture, build_epoch_ms=100)

        self.assertEqual(projection.frame.subject_id, "city-bus-ticketing-modernization")
        self.assertEqual(
            projection.frame.question,
            "What decision should guide City bus ticketing modernization?",
        )
        self.assertEqual(projection.current_state_codes, ("s0",))
        self.assertEqual(projection.target_state_codes, ("s2", "s3"))
        self.assertEqual(projection.direct_decision_titles, ("Path B: coordinated leap",))
        self.assertEqual(projection.indirect_decision_titles, ("Path A: conservative modernization",))
        role_counts = {}
        for item in projection.items:
            role_counts[item.decision_role] = role_counts.get(item.decision_role, 0) + 1
        self.assertEqual(
            role_counts,
            {
                "actor": 5,
                "objective": 3,
                "capability": 4,
                "dependency": 3,
                "constraint": 3,
                "boundary": 3,
                "current_state": 1,
                "target_state": 2,
                "transition_candidate": 3,
                "decision_candidate": 2,
                "supporting_evidence": 1,
            },
        )
        self.assertEqual(len(projection.frame.primary_objective_ids), 3)
        self.assertEqual(len(projection.frame.scope_boundary_ids), 3)
        self.assertEqual(len(projection.frame.current_state_ids), 1)
        self.assertEqual(len(projection.frame.target_state_ids), 2)

    def test_dst_decision_projection_builds_theory_facing_model_for_bus_case(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        projection = project_dst_fixture_to_decision_frame(fixture)
        model = coordinated_model_from_dst_projection(projection)
        current_state = next(iter(model.current))

        self.assertEqual({state.name for state in model.current}, {"s0"})
        self.assertEqual({state.name for state in model.target_state}, {"s2", "s3"})
        self.assertEqual(
            {transition.name for transition in model.transitions},
            {"s0 -> s1", "s1 -> s2", "s0 -> s3"},
        )
        self.assertEqual(
            {transition.name for transition in admissible_transitions(model, current_state)},
            {"s0 -> s1", "s0 -> s3"},
        )
        self.assertEqual(
            [decision.name for decision in valid_decisions(model, current_state)],
            ["Path B: coordinated leap"],
        )
        self.assertEqual(
            [decision.name for decision in executable_decisions(model, current_state)],
            ["Path B: coordinated leap"],
        )

    def test_dst_decision_projection_keeps_multistep_paths_but_only_direct_leaps_are_immediate_model_decisions(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "national-school-system-exam-digitization-rollout"
        )

        projection = project_dst_fixture_to_decision_frame(fixture)
        model = coordinated_model_from_dst_projection(projection)
        current_state = next(iter(model.current))

        self.assertEqual(
            projection.direct_decision_titles,
            ("Path C: direct leap",),
        )
        self.assertEqual(
            projection.indirect_decision_titles,
            (
                "Path A: conservative layering",
                "Path B: resilience-first modernization",
                "Path D: regional rollout",
                "Path E: pilot then stall",
            ),
        )
        self.assertEqual(
            [decision.name for decision in valid_decisions(model, current_state)],
            ["Path C: direct leap"],
        )
        self.assertIn("s0 -> s5", {transition.name for transition in model.transitions})


if __name__ == "__main__":
    unittest.main()
