# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from decision_review import load_decision_frame
from semantic_text import collapse_ws
from workstation.runtime.core.session import launch_workstation_session
from workstation.subject.core.subject_workflow import (
    _itemization_state,
    _latest_publication_composition,
    _review_composition_state,
    apply_subject_action,
    default_subject_scenarios,
    load_subject_progress,
)
from workstation.runtime.core.workstation_core import workstation_learn_markdown_action

from workstation.tests.bdd.smart_city_travel_incremental_support import (
    IncrementalLadderRung,
    deterministic_incremental_dst_pipeline,
    load_smart_city_travel_incremental_dst_fixture,
    load_smart_city_travel_incremental_ladder_spec,
    rung_requires_staged_route_projection,
)


@unittest.skipUnless(
    os.environ.get("OPENAI_API_KEY"),
    "OPENAI_API_KEY is not configured; skipping provider-backed incremental ladder.",
)
class SmartCityTravelIncrementalReportLadderLiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "workstation-root"
        self.workspace = Path(__file__).resolve().parents[3]
        self.spec = load_smart_city_travel_incremental_ladder_spec()
        self.dst_fixture = load_smart_city_travel_incremental_dst_fixture()
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Provider-backed incremental Smart City Travel publication validation.",
            allow_direct_llm_decomposition=True,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_incremental_same_subject_publication_ladder_live(self) -> None:
        learned_subject_id = ""
        for rung in self.spec.rungs:
            with self.subTest(rung=rung.name):
                result_subject_id = self._learn_markdown(rung.markdown_files[-1])
                if not learned_subject_id:
                    learned_subject_id = result_subject_id
                self.assertEqual(result_subject_id, learned_subject_id)
                self._assert_subject_reuse(learned_subject_id=learned_subject_id, rung=rung)
                report_md, report_typ = self._advance_subject_through_publication(
                    subject_id=learned_subject_id,
                    rung=rung,
                )
                self._assert_workflow_health(subject_id=learned_subject_id, rung=rung)
                self._assert_report_semantics(
                    rung=rung,
                    report_md=report_md,
                    report_typ=report_typ,
                )

    def _learn_markdown(self, markdown_relpath: str) -> str:
        result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=self.workspace / markdown_relpath,
            testing_lightweight=True,
        )
        self.assertEqual(result.status, "ok")
        subject_id = str(result.payload["report"]["learning_context"]["subject_id"])
        self.assertTrue(subject_id)
        return subject_id

    def _scenario(self, subject_id: str):
        return next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

    def _apply(
        self,
        *,
        subject_id: str,
        progress,
        action_key: str,
        expected_exact: str | None = None,
        expected_contains: str | None = None,
    ):
        result = apply_subject_action(
            root_path=self.root,
            scenario=self._scenario(subject_id),
            progress=progress,
            action_key=action_key,
        )
        if expected_exact is not None:
            self.assertEqual(result.status_text, expected_exact)
        if expected_contains is not None:
            self.assertIn(expected_contains, result.status_text)
        return result

    def _advance_subject_through_publication(
        self,
        *,
        subject_id: str,
        rung: IncrementalLadderRung,
    ) -> tuple[str, str]:
        progress = load_subject_progress(self.root, subject_id)
        self._apply(subject_id=subject_id, progress=progress, action_key="open_context", expected_exact="Subject context opened.")
        self._apply(subject_id=subject_id, progress=progress, action_key="compare_projections", expected_exact="Projection comparison aligned.")
        self._apply(subject_id=subject_id, progress=progress, action_key="generate_itemization", expected_exact="Itemization generated.")
        self._apply(
            subject_id=subject_id,
            progress=progress,
            action_key="refresh_review_composition",
            expected_exact="Draft composition refreshed.",
        )
        if rung.decision_analysis_expected:
            with patch(
                "workstation.subject.core.subject_workflow._dst_fixture_for_subject",
                return_value=self.dst_fixture,
            ), patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=lambda fixture, **kwargs: deterministic_incremental_dst_pipeline(
                    fixture,
                    staged_route_projection=rung_requires_staged_route_projection(rung),
                    **kwargs,
                ),
            ):
                frame = load_decision_frame(self.root, subject_id)
                decision_action = (
                    "refresh_dst_decision_analysis"
                    if collapse_ws(frame.decision_frame_id)
                    else "create_decision_frame_from_selected_draft_item"
                )
                expected_status = (
                    "DST decision analysis refreshed. Report plan updated."
                    if decision_action == "refresh_dst_decision_analysis"
                    else "Decision analysis started from DST discovery. Report plan updated."
                )
                self._apply(
                    subject_id=subject_id,
                    progress=progress,
                    action_key=decision_action,
                    expected_exact=expected_status,
                )
                self._apply(
                    subject_id=subject_id,
                    progress=progress,
                    action_key="analyze_decision_frame",
                    expected_exact="Decision analysis completed. Report plan updated.",
                )
        else:
            self._apply(
                subject_id=subject_id,
                progress=progress,
                action_key="refresh_publication_composition",
                expected_exact="Report plan refreshed.",
            )
        self._apply(
            subject_id=subject_id,
            progress=progress,
            action_key="approve_review",
            expected_exact="Review approved for report publication.",
        )
        self._apply(
            subject_id=subject_id,
            progress=progress,
            action_key="lock_publication",
            expected_exact="Publication inputs locked.",
        )
        self._apply(
            subject_id=subject_id,
            progress=progress,
            action_key="build_report",
            expected_contains="Report build completed [ok].",
        )
        scenario = self._scenario(subject_id)
        report_md = Path(scenario.report_markdown_path).read_text(encoding="utf-8")
        report_typ = Path(scenario.report_typst_path).read_text(encoding="utf-8")
        return report_md, report_typ

    def _assert_subject_reuse(self, *, learned_subject_id: str, rung: IncrementalLadderRung) -> None:
        scenario = self._scenario(learned_subject_id)
        self.assertEqual(scenario.subject_id, self.spec.subject_id)
        self.assertEqual(scenario.title, self.spec.subject_title)
        self.assertEqual(scenario.source_count, len(rung.markdown_files))

    def _assert_workflow_health(self, *, subject_id: str, rung: IncrementalLadderRung) -> None:
        scenario = self._scenario(subject_id)
        itemization_state = _itemization_state(self.root, scenario)
        review_state = _review_composition_state(self.root, scenario)
        latest_publication_composition = _latest_publication_composition(
            self.root,
            subject_id=subject_id,
            subject_title=scenario.title,
            publication_id=scenario.publication_id,
        )
        expected = rung.required_workflow_health
        self.assertEqual(scenario.subject_id, expected.subject_id)
        self.assertEqual(collapse_ws(str(itemization_state.get("freshness", ""))), expected.itemization_freshness)
        self.assertEqual(
            collapse_ws(str(itemization_state.get("validation_status", ""))),
            expected.itemization_validation,
        )
        self.assertEqual(bool(review_state.get("current")), expected.draft_composition_current)
        self.assertIsNotNone(latest_publication_composition)
        self.assertEqual(
            collapse_ws(latest_publication_composition.learning_context_snapshot_hash),
            collapse_ws(scenario.context_snapshot_hash),
        )
        if expected.report_build_completed:
            self.assertTrue(bool(scenario.build_id))
            self.assertEqual(scenario.validation_status, "ok")
            self.assertTrue(Path(scenario.report_markdown_path).is_file())
            self.assertTrue(Path(scenario.report_typst_path).is_file())

    def _assert_report_semantics(
        self,
        *,
        rung: IncrementalLadderRung,
        report_md: str,
        report_typ: str,
    ) -> None:
        for required in rung.required_markdown_substrings:
            self.assertIn(required, report_md)
        for forbidden in rung.forbidden_markdown_substrings:
            self.assertNotIn(forbidden, report_md)
        for typst_smoke in rung.optional_typst_substrings:
            self.assertIn(typst_smoke, report_typ)
        for markdown_file in rung.markdown_files:
            self.assertIn(markdown_file, report_md)


if __name__ == "__main__":
    unittest.main()
