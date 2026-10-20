from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from coordinated_transformation import admissible_transitions, executable_decisions, valid_decisions
from dst import (
    discovery_result_from_fixture,
    normalized_case_from_fixture,
    project_normalized_case_to_transformation_construct_candidates,
    run_dst_pipeline_from_fixture,
    run_live_dst_construct_discovery_for_itemized_item,
)
from dst.core import DstUseCaseFixture, dst_use_cases_from_markdown
from itemize import ItemizedSubjectItem


_REPO_ROOT = Path(__file__).resolve().parents[2]


def embedded_fixture(name: str, markdown: str) -> DstUseCaseFixture:
    fixtures = dst_use_cases_from_markdown(
        markdown,
        source_path=_REPO_ROOT / "dst" / f"{name}.md",
    )
    if len(fixtures) != 1:
        raise AssertionError(f"expected exactly one embedded fixture for {name}, got {len(fixtures)}")
    return fixtures[0]


class DstEmbeddedStory:
    def __init__(self, test_case: unittest.TestCase, *, name: str, markdown: str) -> None:
        self.test_case = test_case
        self.fixture = embedded_fixture(name, markdown)
        self.discovery = None
        self.normalized_case = None
        self.pipeline = None
        self.model = None
        self.current_state = None

    def given_embedded_dst_prose(self) -> None:
        self.test_case.assertTrue(self.fixture.fixture_id)
        self.test_case.assertTrue(self.fixture.title)
        self.test_case.assertTrue(self.fixture.source_ref.startswith("dst/"))

    def when_governed_candidate_path_discovery_runs(self) -> None:
        self.discovery = discovery_result_from_fixture(self.fixture)

    def when_dst_normalization_runs(self) -> None:
        self.test_case.assertIsNotNone(self.discovery)
        assert self.discovery is not None
        self.normalized_case = normalized_case_from_fixture(self.fixture, self.discovery)

    def when_the_end_to_end_dst_pipeline_runs(self, *, subject_id: str = "", question: str = "") -> None:
        self.pipeline = run_dst_pipeline_from_fixture(
            self.fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(self.fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                self.fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id=subject_id or self.fixture.fixture_id,
            question=question,
            build_epoch_ms=101,
        )
        self.discovery = self.pipeline.discovery_result
        self.normalized_case = self.pipeline.normalized_case
        self.model = self.pipeline.coordinated_model
        self.current_state = next(iter(self.model.current))

    def then_candidate_paths_are(self, expected_titles: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.discovery)
        assert self.discovery is not None
        self.test_case.assertEqual(
            tuple(item.title for item in self.discovery.candidate_paths),
            expected_titles,
        )

    def then_candidate_path_routes_are(self, expected_routes: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.discovery)
        assert self.discovery is not None
        self.test_case.assertEqual(
            tuple(item.route_expression for item in self.discovery.candidate_paths),
            expected_routes,
        )

    def then_path_kinds_are(self, expected_kinds: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.discovery)
        assert self.discovery is not None
        self.test_case.assertEqual(
            tuple(item.path_kind for item in self.discovery.candidate_paths),
            expected_kinds,
        )

    def then_sort_atom_context_includes(self, *, actors: tuple[str, ...] = (), capabilities: tuple[str, ...] = ()) -> None:
        self.test_case.assertIsNotNone(self.discovery)
        assert self.discovery is not None
        for actor in actors:
            self.test_case.assertIn(actor, self.discovery.sort_atom_context.actors)
        for capability in capabilities:
            self.test_case.assertIn(capability, self.discovery.sort_atom_context.capabilities)

    def then_the_current_state_is(self, expected_state: str) -> None:
        self.test_case.assertIsNotNone(self.model)
        assert self.model is not None
        self.test_case.assertEqual([state.name for state in self.model.current], [expected_state])

    def then_the_target_states_are(self, expected_states: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        assert self.model is not None
        self.test_case.assertEqual(
            tuple(sorted(state.name for state in self.model.target_state)),
            tuple(sorted(expected_states)),
        )

    def then_valid_decision_titles_are(self, expected_titles: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        self.test_case.assertIsNotNone(self.current_state)
        assert self.model is not None
        assert self.current_state is not None
        self.test_case.assertEqual(
            tuple(item.name for item in valid_decisions(self.model, self.current_state)),
            expected_titles,
        )

    def then_valid_decision_titles_include_set(self, expected_titles: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        self.test_case.assertIsNotNone(self.current_state)
        assert self.model is not None
        assert self.current_state is not None
        self.test_case.assertEqual(
            {item.name for item in valid_decisions(self.model, self.current_state)},
            set(expected_titles),
        )

    def then_executable_decision_titles_include_set(self, expected_titles: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        self.test_case.assertIsNotNone(self.current_state)
        assert self.model is not None
        assert self.current_state is not None
        self.test_case.assertEqual(
            {item.name for item in executable_decisions(self.model, self.current_state)},
            set(expected_titles),
        )

    def then_executable_decision_titles_are(self, expected_titles: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        self.test_case.assertIsNotNone(self.current_state)
        assert self.model is not None
        assert self.current_state is not None
        self.test_case.assertEqual(
            tuple(item.name for item in executable_decisions(self.model, self.current_state)),
            expected_titles,
        )

    def then_admissible_transition_names_are(self, expected_names: tuple[str, ...]) -> None:
        self.test_case.assertIsNotNone(self.model)
        self.test_case.assertIsNotNone(self.current_state)
        assert self.model is not None
        assert self.current_state is not None
        self.test_case.assertEqual(
            tuple(item.name for item in admissible_transitions(self.model, self.current_state)),
            expected_names,
        )

    def then_the_normalized_candidate_surface_has(self, *, transition_count: int, decision_count: int) -> None:
        self.test_case.assertIsNotNone(self.normalized_case)
        assert self.normalized_case is not None
        self.test_case.assertEqual(
            len(self.normalized_case.candidate_sets.candidate_transition_ids_from_current_state),
            transition_count,
        )
        self.test_case.assertEqual(
            len(self.normalized_case.candidate_sets.candidate_decision_ids_from_current_state),
            decision_count,
        )

    def then_selected_item_construct_discovery_returns_runtime_tagged_candidates(self, *, subject_id: str) -> None:
        self.test_case.assertIsNotNone(self.normalized_case)
        assert self.normalized_case is not None
        construct_projection = project_normalized_case_to_transformation_construct_candidates(
            self.normalized_case,
            subject_id=subject_id,
            itemized_item_id="itm_focus",
        )
        self.test_case.assertGreater(len(construct_projection.candidates), 0)
        self.test_case.assertEqual(
            {candidate.sort_kind for candidate in construct_projection.candidates},
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

        selected_item = ItemizedSubjectItem(
            itemized_item_id="itm_regulator",
            subject_id=subject_id,
            item_kind="decision_role_candidate",
            canonical_label="Regulator",
            summary="The regulator constrains which modernization route is admissible.",
            source_refs=(self.fixture.source_ref,),
            confidence=0.88,
            status="candidate",
            metadata={"decision_role": "actor"},
        )

        orchestration_result = run_dst_pipeline_from_fixture(
            self.fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(self.fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                self.fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id=subject_id,
            build_epoch_ms=17,
        )

        with patch(
            "dst.orchestration.run_live_dst_pipeline_from_fixture",
            return_value=orchestration_result,
        ):
            result = run_live_dst_construct_discovery_for_itemized_item(
                selected_item,
                subject_title=self.fixture.title,
                subject_summary=self.fixture.summary,
                subject_source_refs=(self.fixture.source_ref,),
                supporting_items=(selected_item,),
                build_epoch_ms=17,
            )

        self.test_case.assertGreater(len(result.construct_candidates), 0)
        self.test_case.assertTrue(
            all(
                candidate.relation_hints.get("dst_construct_source") == "dst_runtime"
                and candidate.relation_hints.get("dst_fixture_id") == self.fixture.fixture_id
                for candidate in result.construct_candidates
            )
        )
