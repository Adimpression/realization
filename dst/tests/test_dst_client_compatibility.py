import unittest
from pathlib import Path
from unittest.mock import patch

import dst
from dst import (
    discovery_result_from_fixture,
    load_dst_normalized_case,
    load_dst_use_cases,
    match_dst_fixture_for_source_refs,
    normalized_case_from_fixture,
    project_normalized_case_to_transformation_construct_candidates,
    run_dst_pipeline_from_fixture,
    run_live_dst_construct_discovery_for_itemized_item,
)
from dst.projection import project_normalized_case_to_decision_frame
from realized_core_semantics.itemization import ItemizedSubjectItem


class DstClientCompatibilityTests(unittest.TestCase):
    def _smart_city_fixture(self):
        return next(
            item for item in load_dst_use_cases() if item.fixture_id == "smart-city-travel-incremental"
        )

    def _manual_item(self) -> ItemizedSubjectItem:
        return ItemizedSubjectItem(
            itemized_item_id="itm_smart_city_actor",
            subject_id="smart-city-travel",
            item_kind="decision_role_candidate",
            canonical_label="City Regulator",
            summary="The city regulator decides which payment modernization path is acceptable.",
            source_refs=("dst/City bus prose v10.md",),
            confidence=0.84,
            status="candidate",
            metadata={"decision_role": "actor"},
        )

    def test_package_root_exports_all_current_external_entrypoints(self) -> None:
        expected_names = {
            "DstControllerBootstrap",
            "DstControllerBootstrapUnavailable",
            "discovery_result_from_fixture",
            "load_dst_normalized_case",
            "load_dst_use_cases",
            "match_dst_fixture_for_source_refs",
            "normalized_case_from_fixture",
            "project_normalized_case_to_transformation_construct_candidates",
            "run_dst_pipeline_from_fixture",
            "run_live_dst_construct_discovery_for_itemized_item",
            "run_live_dst_pipeline_from_fixture",
        }

        missing = sorted(name for name in expected_names if not hasattr(dst, name))

        self.assertEqual(missing, [])

    def test_workstation_style_fixture_matching_works_with_cumulative_same_subject_source_refs(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        fixture = match_dst_fixture_for_source_refs(
            (
                str((repo_root / "dst" / "City bus prose v2.md").resolve()),
                "dst/City bus prose v10.md",
            ),
            fixtures=load_dst_use_cases(),
        )

        self.assertIsNotNone(fixture)
        assert fixture is not None
        self.assertEqual(fixture.fixture_id, "smart-city-travel-incremental")
        self.assertEqual(fixture.title, "Smart City Travel")

    def test_bdd_style_deterministic_pipeline_for_incremental_fixture_preserves_current_result_shape(self) -> None:
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
            build_epoch_ms=11,
        )

        self.assertEqual(result.fixture.fixture_id, "smart-city-travel-incremental")
        self.assertEqual(result.discovery_prompt_packet.fixture_id, fixture.fixture_id)
        self.assertEqual(result.discovery_result.fixture_id, fixture.fixture_id)
        self.assertEqual(result.normalized_case.fixture_id, fixture.fixture_id)
        self.assertEqual(result.decision_projection.frame.subject_id, "smart-city-travel")
        self.assertEqual(result.decision_projection.frame.question, "What should guide Smart City Travel?")
        self.assertEqual(result.decision_projection.candidate_transition_ids, ("t1", "t4"))
        self.assertEqual(result.decision_projection.candidate_decision_ids, ("x1", "x2"))
        self.assertEqual([state.name for state in result.coordinated_model.current], ["legacy fare system"])

    def test_subject_workflow_style_construct_projection_preserves_runtime_candidate_shape(self) -> None:
        fixture = self._smart_city_fixture()
        discovery = discovery_result_from_fixture(fixture)
        normalized_case = normalized_case_from_fixture(fixture, discovery)

        projection = project_normalized_case_to_transformation_construct_candidates(
            normalized_case,
            subject_id="smart-city-travel",
            itemized_item_id="itm_smart_city_focus",
        )

        self.assertEqual(projection.case.fixture_id, fixture.fixture_id)
        self.assertGreater(len(projection.candidates), 0)
        self.assertEqual(
            {candidate.sort_kind for candidate in projection.candidates},
            {
                "actor",
                "objective",
                "capability",
                "dependency",
                "constraint",
                "boundary",
                "state",
                "transition",
                "decision",
            },
        )
        self.assertTrue(
            all(candidate.subject_id == "smart-city-travel" for candidate in projection.candidates)
        )
        self.assertTrue(
            all(candidate.itemized_item_id == "itm_smart_city_focus" for candidate in projection.candidates)
        )
        self.assertTrue(
            all(
                candidate.relation_hints.get("dst_construct_source") == "dst_runtime"
                and candidate.relation_hints.get("dst_fixture_id") == fixture.fixture_id
                for candidate in projection.candidates
            )
        )

    def test_decision_review_style_projection_from_loaded_normalized_case_preserves_candidate_surface(self) -> None:
        normalized_case = load_dst_normalized_case("smart-city-travel-incremental")

        self.assertIsNotNone(normalized_case)
        assert normalized_case is not None

        projection = project_normalized_case_to_decision_frame(
            normalized_case,
            subject_id="smart-city-travel",
            question="What should guide Smart City Travel?",
            build_epoch_ms=21,
        )

        self.assertEqual(projection.case.fixture_id, "smart-city-travel-incremental")
        self.assertEqual(projection.frame.subject_id, "smart-city-travel")
        self.assertEqual(projection.frame.question, "What should guide Smart City Travel?")
        self.assertEqual(projection.candidate_transition_ids, ("t1", "t4"))
        self.assertEqual(projection.candidate_decision_ids, ("x1", "x2"))
        self.assertGreater(len(projection.current_state_ids), 0)
        self.assertGreater(len(projection.target_state_ids), 0)

    def test_subject_workflow_style_live_construct_discovery_returns_runtime_tagged_candidates(self) -> None:
        selected_item = self._manual_item()
        fixture = self._smart_city_fixture()
        orchestration_result = run_dst_pipeline_from_fixture(
            fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id=selected_item.subject_id,
            build_epoch_ms=17,
        )

        with patch(
            "dst.orchestration.run_live_dst_pipeline_from_fixture",
            return_value=orchestration_result,
        ):
            result = run_live_dst_construct_discovery_for_itemized_item(
                selected_item,
                subject_title="Smart City Travel",
                subject_summary="The city wants to modernize fare payment without disrupting service.",
                subject_source_refs=("dst/City bus prose v10.md",),
                supporting_items=(selected_item,),
                build_epoch_ms=17,
            )

        self.assertEqual(result.fixture.title, "Smart City Travel")
        self.assertEqual(result.orchestration_result.normalized_case.fixture_id, fixture.fixture_id)
        self.assertGreater(len(result.construct_candidates), 0)
        self.assertTrue(
            all(
                candidate.relation_hints.get("dst_construct_source") == "dst_runtime"
                for candidate in result.construct_candidates
            )
        )


if __name__ == "__main__":
    unittest.main()
