from __future__ import annotations

from dataclasses import replace
import unittest

from dst import (
    DstAdmissibilityRecord,
    DstDecisionStatus,
    DstNormalizedConstraint,
    DstRiskIndicator,
    build_dst_case_revision,
    build_dst_case_snapshot,
    build_dst_case_snapshot_from_orchestration_result,
    coordinated_model_from_normalized_case,
    discovery_result_from_fixture,
    load_dst_normalized_case,
    load_dst_use_cases,
    normalized_case_from_fixture,
    project_normalized_case_to_decision_frame,
    run_dst_pipeline_from_fixture,
)


class DstRevisionTests(unittest.TestCase):
    def _smart_city_fixture(self):
        return next(
            item
            for item in load_dst_use_cases()
            if item.fixture_id == "smart-city-travel-incremental"
        )

    def _city_bus_case(self):
        case = load_dst_normalized_case("city-bus-ticketing-modernization")
        self.assertIsNotNone(case)
        assert case is not None
        return case

    def _fixture_by_id(self, fixture_id: str):
        return next(item for item in load_dst_use_cases() if item.fixture_id == fixture_id)

    def _build_snapshot_for_case(
        self,
        case,
        *,
        source_basis_refs: tuple[str, ...] | None = None,
        predecessor_snapshot_id: str = "",
    ):
        discovery = discovery_result_from_fixture(self._fixture_by_id(case.fixture_id))
        projection = project_normalized_case_to_decision_frame(
            case,
            subject_id=case.fixture_id,
            question=f"What decision should guide {case.fixture_id}?",
            build_epoch_ms=19,
        )
        return build_dst_case_snapshot(
            discovery_result=discovery,
            normalized_case=case,
            decision_projection=projection,
            coordinated_model=coordinated_model_from_normalized_case(case),
            source_basis_refs=source_basis_refs or (case.source_ref,),
            subject_id=projection.frame.subject_id,
            question=projection.frame.question,
            predecessor_snapshot_id=predecessor_snapshot_id,
            created_at_epoch_ms=projection.frame.updated_at_epoch_ms,
        )

    def test_build_dst_case_snapshot_from_orchestration_result_preserves_existing_pipeline_outputs(self) -> None:
        fixture = self._smart_city_fixture()
        result = run_dst_pipeline_from_fixture(
            fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id="smart-city-travel",
            question="What should guide Smart City Travel?",
            build_epoch_ms=37,
        )

        snapshot = build_dst_case_snapshot_from_orchestration_result(
            result,
            source_basis_refs=("dst/City bus prose v2.md", "dst/City bus prose v10.md"),
            revision_source="workstation_markdown_import",
            revision_reason="cumulative_same_subject_import",
        )

        self.assertEqual(snapshot.fixture_id, fixture.fixture_id)
        self.assertEqual(snapshot.subject_id, "smart-city-travel")
        self.assertEqual(snapshot.question, "What should guide Smart City Travel?")
        self.assertEqual(snapshot.source_basis_refs, ("dst/City bus prose v2.md", "dst/City bus prose v10.md"))
        self.assertEqual(snapshot.discovery_result, result.discovery_result)
        self.assertEqual(snapshot.normalized_case, result.normalized_case)
        self.assertEqual(snapshot.decision_projection, result.decision_projection)
        self.assertEqual(snapshot.coordinated_model, result.coordinated_model)
        self.assertEqual(snapshot.created_at_epoch_ms, 37)
        self.assertTrue(snapshot.snapshot_id.startswith("dstsnap_smart-city-travel_"))

    def test_build_dst_case_revision_treats_source_basis_change_as_upstream_refresh_without_formal_evaluation_change(self) -> None:
        fixture = self._smart_city_fixture()
        result = run_dst_pipeline_from_fixture(
            fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id="smart-city-travel",
            question="What should guide Smart City Travel?",
            build_epoch_ms=41,
        )
        before_snapshot = build_dst_case_snapshot_from_orchestration_result(
            result,
            source_basis_refs=("dst/City bus prose v2.md",),
        )
        after_snapshot = build_dst_case_snapshot_from_orchestration_result(
            result,
            source_basis_refs=("dst/City bus prose v2.md", "dst/City bus prose v10.md"),
            predecessor_snapshot_id=before_snapshot.snapshot_id,
        )

        revision = build_dst_case_revision(before_snapshot, after_snapshot)

        self.assertEqual(revision.structure_delta.changed_sections, ())
        self.assertEqual(revision.evaluation_delta.changed_transition_ids, ())
        self.assertEqual(revision.evaluation_delta.changed_decision_ids, ())
        self.assertTrue(revision.invalidation.source_basis_changed)
        self.assertTrue(revision.invalidation.requires_discovery_refresh)
        self.assertTrue(revision.invalidation.requires_normalization_refresh)
        self.assertFalse(revision.invalidation.requires_formal_re_evaluation)
        self.assertEqual(revision.invalidation.impacted_transition_ids, ())
        self.assertEqual(revision.invalidation.impacted_decision_ids, ())

    def test_build_dst_case_revision_detects_newly_blocked_transition_and_decision_without_mutating_existing_snapshot_contracts(self) -> None:
        before_case = self._city_bus_case()
        transition_id = before_case.candidate_sets.candidate_transition_ids_from_current_state[0]
        decision_id = before_case.candidate_sets.candidate_decision_ids_from_current_state[0]
        evaluation_state_id = before_case.context.evaluation_state_id
        blocking_constraint = DstNormalizedConstraint(
            id="q_block",
            name="new audit freeze",
            kind="governance",
        )

        after_case = replace(
            before_case,
            constraints=before_case.constraints + (blocking_constraint,),
            states=tuple(
                replace(
                    item,
                    active_constraints=item.active_constraints + (blocking_constraint.id,),
                )
                if item.id == evaluation_state_id
                else item
                for item in before_case.states
            ),
            transitions=tuple(
                replace(
                    item,
                    constraining_constraints=item.constraining_constraints + (blocking_constraint.id,),
                )
                if item.id == transition_id
                else item
                for item in before_case.transitions
            ),
            transition_admissibility=tuple(
                DstAdmissibilityRecord(
                    subject_id=item.subject_id,
                    state_id=item.state_id,
                    admissible=False,
                    reasons=item.reasons + ("new audit freeze blocks the route",),
                )
                if item.subject_id == transition_id and item.state_id == evaluation_state_id
                else item
                for item in before_case.transition_admissibility
            ),
            decision_status=tuple(
                DstDecisionStatus(
                    decision_id=item.decision_id,
                    state_id=item.state_id,
                    valid=False,
                    executable=False,
                    reasons=item.reasons + ("selected route is no longer admissible",),
                )
                if item.decision_id == decision_id and item.state_id == evaluation_state_id
                else item
                for item in before_case.decision_status
            ),
            candidate_sets=replace(
                before_case.candidate_sets,
                candidate_transition_ids_from_current_state=tuple(
                    item
                    for item in before_case.candidate_sets.candidate_transition_ids_from_current_state
                    if item != transition_id
                ),
                candidate_decision_ids_from_current_state=tuple(
                    item
                    for item in before_case.candidate_sets.candidate_decision_ids_from_current_state
                    if item != decision_id
                ),
            ),
        )

        before_snapshot = self._build_snapshot_for_case(before_case)
        after_snapshot = self._build_snapshot_for_case(
            after_case,
            predecessor_snapshot_id=before_snapshot.snapshot_id,
        )

        revision = build_dst_case_revision(before_snapshot, after_snapshot)

        self.assertIn("constraints", revision.structure_delta.changed_sections)
        self.assertIn("states", revision.structure_delta.changed_sections)
        self.assertIn("transitions", revision.structure_delta.changed_sections)
        self.assertIn("transition_admissibility", revision.structure_delta.changed_sections)
        self.assertIn("decision_status", revision.structure_delta.changed_sections)
        self.assertEqual(revision.evaluation_delta.newly_blocked_transition_ids, (transition_id,))
        self.assertEqual(revision.evaluation_delta.newly_blocked_decision_ids, (decision_id,))
        self.assertEqual(revision.evaluation_delta.newly_invalid_decision_ids, (decision_id,))
        self.assertTrue(revision.invalidation.requires_normalization_refresh)
        self.assertTrue(revision.invalidation.requires_formal_re_evaluation)
        self.assertEqual(revision.invalidation.impacted_transition_ids, (transition_id,))
        self.assertEqual(revision.invalidation.impacted_decision_ids, (decision_id,))

    def test_build_dst_case_revision_detects_newly_risky_transition_without_treating_it_as_newly_blocked(self) -> None:
        before_case = self._city_bus_case()
        transition_id = before_case.candidate_sets.candidate_transition_ids_from_current_state[0]
        evaluation_state_id = before_case.context.evaluation_state_id
        after_case = replace(
            before_case,
            risk_indicators=before_case.risk_indicators + (
                DstRiskIndicator(
                    target_type="transition",
                    target_id=transition_id,
                    state_id=evaluation_state_id,
                    risks=("new payment-boundary friction",),
                ),
            ),
        )

        before_snapshot = self._build_snapshot_for_case(before_case)
        after_snapshot = self._build_snapshot_for_case(
            after_case,
            predecessor_snapshot_id=before_snapshot.snapshot_id,
        )

        revision = build_dst_case_revision(before_snapshot, after_snapshot)

        self.assertEqual(revision.evaluation_delta.newly_risky_transition_ids, (transition_id,))
        self.assertEqual(revision.evaluation_delta.newly_blocked_transition_ids, ())
        self.assertTrue(revision.invalidation.requires_formal_re_evaluation)
        self.assertEqual(revision.invalidation.impacted_transition_ids, (transition_id,))


if __name__ == "__main__":
    unittest.main()
