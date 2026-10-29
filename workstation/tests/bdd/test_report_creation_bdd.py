# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import shutil
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from realized_core_semantics.applied_model import ProposalType
from controller_entrypoints import ensure_application_controller_runtime
from workstation.subject.core.decision_review import list_decision_review_items
from workstation.subject.core.decision_review_constructs import list_transformation_construct_candidates
from dst import DST_SOURCE_ROOT, discovery_result_from_fixture, normalized_case_from_fixture, run_dst_pipeline_from_fixture
from realized_core_semantics.itemization import ItemizedSubjectItem
from workstation.subject.core.itemization import (
    list_itemized_subject_items,
    stable_itemized_item_id,
)
from workstation.subject.core.review_composition import list_review_items
from realized_core_semantics.semantic_text import collapse_ws

from workstation.runtime.core.session import launch_workstation_session
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.subject.core.subject_workflow import (
    apply_subject_action,
    default_subject_scenarios,
    load_subject_import_staging,
    load_subject_progress,
    subject_action_specs,
    subject_current_step_actions,
    subject_guidance_phase,
    subject_current_step_view,
    subject_more_action_specs,
    subject_publication_import_included_switch_spec,
    subject_publication_import_target_select_spec,
    subject_publication_import_usage_select_spec,
    render_subject_draft_tree,
)
from workstation.runtime.core.workstation_core import workstation_learn_markdown_action


def _itemization_runtime_provider(controller: object) -> SimpleNamespace:
    return SimpleNamespace(
        bootstrap_controller=lambda **_kwargs: (SimpleNamespace(), controller)
    )


@dataclass(frozen=True)
class ReportCreationArtifacts:
    subject_id: str
    report_typ: str
    report_md: str
    report_pdf_path: str


class WorkflowSubjectStory:
    def __init__(self, test_case: unittest.TestCase, *, root: Path, subject_id: str) -> None:
        self.test_case = test_case
        self.root = root
        self.subject_id = subject_id
        self.progress = load_subject_progress(root, subject_id)
        self.phase = "research"
        self.host_actions = RuntimeSubjectWorkflowHostActions()

    @property
    def scenario(self):
        return next(item for item in default_subject_scenarios(self.root) if item.subject_id == self.subject_id)

    def when_user_switches_to_phase(self, phase: str) -> None:
        self.phase = phase

    def then_current_step_contains(self, text: str) -> None:
        step = subject_current_step_view(
            scenario=self.scenario,
            progress=self.progress,
            phase=self.phase,
        )
        rendered = "\n".join(
            line
            for line in (
                f"Do this now: {step.title}",
                f"Status: {step.status}",
                f"Why: {step.why}",
                *step.detail_lines,
            )
            if line
        )
        self.test_case.assertIn(text, rendered)

    def then_primary_action_is(self, label: str) -> None:
        step = subject_current_step_view(
            scenario=self.scenario,
            progress=self.progress,
            phase=self.phase,
        )
        self.test_case.assertIsNotNone(step.primary_action)
        self.test_case.assertEqual(step.primary_action.label, label)

    def then_visible_action_labels_include(self, *labels: str) -> None:
        canonical_labels = self._current_step_action_labels()
        for label in labels:
            self.test_case.assertIn(label, canonical_labels)

    def then_visible_action_labels_exclude(self, *labels: str) -> None:
        canonical_labels = self._current_step_action_labels()
        for label in labels:
            self.test_case.assertNotIn(label, canonical_labels)

    def then_more_action_labels_include(self, *labels: str) -> None:
        canonical_labels = self._more_action_labels()
        for label in labels:
            self.test_case.assertIn(label, canonical_labels)

    def then_more_action_labels_exclude(self, *labels: str) -> None:
        canonical_labels = self._more_action_labels()
        for label in labels:
            self.test_case.assertNotIn(label, canonical_labels)

    def then_all_visible_action_labels_include(self, *labels: str) -> None:
        canonical_labels = self._current_step_action_labels() | self._more_action_labels()
        for label in labels:
            self.test_case.assertIn(label, canonical_labels)

    def then_all_visible_action_labels_exclude(self, *labels: str) -> None:
        canonical_labels = self._current_step_action_labels() | self._more_action_labels()
        for label in labels:
            self.test_case.assertNotIn(label, canonical_labels)

    def then_phase_action_labels_include(self, *labels: str, import_staging=None) -> None:
        canonical_labels = self._phase_action_labels(import_staging=import_staging)
        for label in labels:
            self.test_case.assertIn(label, canonical_labels)

    def then_phase_action_labels_exclude(self, *labels: str, import_staging=None) -> None:
        canonical_labels = self._phase_action_labels(import_staging=import_staging)
        for label in labels:
            self.test_case.assertNotIn(label, canonical_labels)

    def _current_step_action_labels(self) -> set[str]:
        rendered_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=self.scenario,
                progress=self.progress,
                phase=self.phase,
            )
        ]
        canonical_labels = set(rendered_labels)
        canonical_labels.update(
            label.split(": ", 1)[1]
            for label in rendered_labels
            if ": " in label
        )
        return canonical_labels

    def _more_action_labels(self) -> set[str]:
        rendered_labels = [
            spec.label
            for spec in subject_more_action_specs(
                scenario=self.scenario,
                progress=self.progress,
                phase=self.phase,
            )
        ]
        canonical_labels = set(rendered_labels)
        canonical_labels.update(
            label.split(": ", 1)[1]
            for label in rendered_labels
            if ": " in label
        )
        return canonical_labels

    def _phase_action_labels(self, *, import_staging=None) -> set[str]:
        rendered_labels = [
            action.label
            for action in subject_action_specs(
                scenario=self.scenario,
                progress=self.progress,
                phase=self.phase,
                import_staging=import_staging,
            )
        ]
        canonical_labels = set(rendered_labels)
        canonical_labels.update(
            label.split(": ", 1)[1]
            for label in rendered_labels
            if ": " in label
        )
        return canonical_labels

    def when_user_uses_workflow_action(
        self,
        action_key: str,
        *,
        expected_status: str | None = None,
        import_staging=None,
    ):
        result = apply_subject_action(
            root_path=self.root,
            scenario=self.scenario,
            progress=self.progress,
            action_key=action_key,
            import_staging=import_staging,
            host_actions=self.host_actions,
        )
        if result.next_phase:
            self.phase = str(result.next_phase)
        if expected_status is not None:
            if action_key == "build_report":
                self.test_case.assertIn(expected_status, result.status_text)
            else:
                self.test_case.assertEqual(result.status_text, expected_status)
        return result

    def then_phase_is(self, phase: str) -> None:
        self.test_case.assertEqual(self.phase, phase)

    def then_guidance_phase_is(self, phase: str) -> None:
        self.test_case.assertEqual(
            subject_guidance_phase(
                scenario=self.scenario,
                progress=self.progress,
                phase=self.phase,
            ),
            phase,
        )


class ReportCreationBDDTests(unittest.TestCase):
    def setUp(self) -> None:
        ensure_application_controller_runtime()
        self.tempdir = tempfile.TemporaryDirectory()
        self.enterContext(
            patch.dict(
                "os.environ",
                {"WORKSTATION_HOME": str(Path(self.tempdir.name) / "workstation-home")},
                clear=False,
            )
        )
        self.root = Path(self.tempdir.name) / "workstation-root"
        self.workspace = Path(__file__).resolve().parents[3]
        self.fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "report_creation"
        self.dst_root = DST_SOURCE_ROOT
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Create reports from basic fixture markdown files through the workstation flow.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _given_basic_fixture_subject(self, markdown_name: str) -> str:
        markdown_path = self.fixture_root / markdown_name
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")
        subject_id = str(learn_result.payload["report"]["learning_context"]["subject_id"])
        self.assertTrue(subject_id)
        return subject_id

    def _scenario_for_subject(self, subject_id: str):
        return next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

    def _given_dst_fixture_subject(self, markdown_name: str) -> str:
        markdown_path = self.dst_root / markdown_name
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")
        subject_id = str(learn_result.payload["report"]["learning_context"]["subject_id"])
        self.assertTrue(subject_id)
        return subject_id

    def _fake_dst_pipeline(self, dst_fixture, **kwargs):
        return run_dst_pipeline_from_fixture(
            dst_fixture,
            discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(dst_fixture).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                dst_fixture,
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id=str(kwargs.get("subject_id", "")),
            build_epoch_ms=int(kwargs.get("build_epoch_ms", 0) or 0),
        )

    def _direct_llm_candidate(
        self,
        *,
        subject_id: str,
        label: str,
        summary: str,
        decision_role: str,
    ) -> ItemizedSubjectItem:
        return ItemizedSubjectItem(
            itemized_item_id=stable_itemized_item_id(
                subject_id=subject_id,
                item_kind="decision_role_candidate",
                canonical_label=label,
                source_refs=("source:direct-llm",),
                role=decision_role,
            ),
            subject_id=subject_id,
            item_kind="decision_role_candidate",
            canonical_label=label,
            source_unit_id="",
            aliases=(),
            summary=summary,
            source_refs=("source:direct-llm",),
            confidence=0.86,
            status="candidate",
            linked_item_ids=(),
            created_at_epoch_ms=0,
            updated_at_epoch_ms=0,
            schema_version="itemization.v1",
            metadata={"origin": "markdown_direct_llm_decomposition", "decision_role": decision_role},
        )

    def _direct_llm_candidate_payload(
        self,
        *,
        label: str,
        summary: str,
        decision_role: str,
    ) -> dict[str, object]:
        return {
            "canonical_label": label,
            "item_kind": "decision_role_candidate",
            "decision_role": decision_role,
            "summary": summary,
            "confidence": 0.86,
            "aliases": [],
        }

    def _when_user_runs_numbered_report_flow(
        self,
        subject_id: str,
        *,
        exact_draft: bool = False,
    ) -> ReportCreationArtifacts:
        progress = load_subject_progress(self.root, subject_id)
        numbered_steps = [
            (1, "open_context", "Subject context opened."),
            (2, "generate_itemization", "Itemization generated."),
            (3, "refresh_review_composition", "Draft composition refreshed."),
            (4, "compare_projections", "Projection comparison aligned."),
            (5, "refresh_publication_composition", "Report plan refreshed."),
        ]
        if exact_draft:
            numbered_steps.append((6, "cycle_publication_output_mode", "Publication output mode updated."))
        numbered_steps.extend(
            [
                (7 if exact_draft else 6, "approve_review", "Review approved for report publication."),
                (8 if exact_draft else 7, "lock_publication", "Publication inputs locked."),
                (9 if exact_draft else 8, "build_report", "Report build completed"),
            ]
        )

        for step_number, action_key, expected_status in numbered_steps:
            result = apply_subject_action(
                root_path=self.root,
                scenario=self._scenario_for_subject(subject_id),
                progress=progress,
                action_key=action_key,
            )
            if action_key == "build_report":
                self.assertIn(
                    expected_status,
                    result.status_text,
                    msg=f"step {step_number} ({action_key}) returned {result.status_text!r}",
                )
            else:
                self.assertEqual(
                    result.status_text,
                    expected_status,
                    msg=f"step {step_number} ({action_key}) returned {result.status_text!r}",
                )

        rebuilt = self._scenario_for_subject(subject_id)
        report_typ_path = Path(rebuilt.report_typst_path)
        report_md_path = Path(rebuilt.report_markdown_path)
        self.assertTrue(report_typ_path.is_file())
        self.assertTrue(report_md_path.is_file())
        if shutil.which("typst"):
            self.assertTrue(Path(rebuilt.report_pdf_path).is_file())
        return ReportCreationArtifacts(
            subject_id=subject_id,
            report_typ=report_typ_path.read_text(encoding="utf-8"),
            report_md=report_md_path.read_text(encoding="utf-8"),
            report_pdf_path=rebuilt.report_pdf_path,
        )

    def _approve_import_from_source_to_target(
        self,
        *,
        source_subject_id: str,
        target_story: WorkflowSubjectStory,
    ) -> None:
        self._create_pending_import_from_source_to_target(
            source_subject_id=source_subject_id,
            target_story=target_story,
        )
        target_story.when_user_switches_to_phase("research")
        target_story.then_visible_action_labels_include("Preview Pending Import", "Approve Import", "Reject Import")
        target_story.when_user_uses_workflow_action(
            "preview_pending_import",
            expected_status="Pending subject import preview loaded.",
        )
        target_story.when_user_uses_workflow_action("approve_subject_import", expected_status="Subject import approved.")

    def _create_pending_import_from_source_to_target(
        self,
        *,
        source_subject_id: str,
        target_story: WorkflowSubjectStory,
    ) -> None:
        source_story = WorkflowSubjectStory(self, root=self.root, subject_id=source_subject_id)
        source_story.when_user_switches_to_phase("research")
        source_story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        source_story.when_user_uses_workflow_action("pin_import_source", expected_status="Import source selected.")
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)

        target_story.when_user_switches_to_phase("research")
        target_story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        staging_action_labels = [
            action.label
            for action in subject_action_specs(
                scenario=target_story.scenario,
                progress=target_story.progress,
                phase="research",
                import_staging=staging,
            )
        ]
        self.assertIn("Create Import From Selected Source", staging_action_labels)
        self.assertIn("Clear Import Source", staging_action_labels)
        target_story.when_user_uses_workflow_action("create_subject_import", import_staging=staging)
        target_story.then_phase_is("review")

    def _advance_story_to_publication_plan(self, story: WorkflowSubjectStory) -> None:
        story.when_user_switches_to_phase("itemize")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_switches_to_phase("draft")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_switches_to_phase("review")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_switches_to_phase("publication")
        story.when_user_uses_workflow_action("refresh_publication_composition", expected_status="Report plan refreshed.")

    def test_000_given_find_the_time_fixture_when_user_runs_default_happy_path_then_publication_outputs_exist(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertTrue(artifacts.subject_id)
        self.assertTrue(artifacts.report_typ.strip())
        self.assertTrue(artifacts.report_md.strip())
        self.assertIn("Find the Time", artifacts.report_typ)
        self.assertIn("Find the Time", artifacts.report_md)

    def test_005_given_source_and_target_subjects_when_user_approves_import_and_refreshes_plan_then_publication_import_controls_are_available(self) -> None:
        source_subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")
        target_subject_id = self._given_basic_fixture_subject("02_MEET_GREET_DEPART.md")

        story = WorkflowSubjectStory(self, root=self.root, subject_id=target_subject_id)
        self._approve_import_from_source_to_target(
            source_subject_id=source_subject_id,
            target_story=story,
        )

        story.when_user_switches_to_phase("itemize")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_switches_to_phase("draft")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_switches_to_phase("review")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_switches_to_phase("publication")
        story.when_user_uses_workflow_action("refresh_publication_composition", expected_status="Report plan refreshed.")

        target_spec = subject_publication_import_target_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        included_spec = subject_publication_import_included_switch_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        usage_spec = subject_publication_import_usage_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )

        self.assertTrue(target_spec.enabled)
        self.assertEqual(len(target_spec.options), 1)
        self.assertEqual(target_spec.options[0][0], "Einstein")
        self.assertTrue(included_spec.enabled)
        self.assertTrue(bool(included_spec.value))
        self.assertTrue(usage_spec.enabled)
        self.assertEqual(usage_spec.value, "dependency_only")

    def test_006_given_two_approved_imports_when_user_refreshes_plan_then_publication_import_target_lists_both_sources(self) -> None:
        source_a_subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")
        source_b_subject_id = self._given_basic_fixture_subject("04_WIKIPEDIA.md")
        target_subject_id = self._given_basic_fixture_subject("02_MEET_GREET_DEPART.md")

        story = WorkflowSubjectStory(self, root=self.root, subject_id=target_subject_id)
        self._approve_import_from_source_to_target(
            source_subject_id=source_a_subject_id,
            target_story=story,
        )
        self._approve_import_from_source_to_target(
            source_subject_id=source_b_subject_id,
            target_story=story,
        )

        story.when_user_switches_to_phase("itemize")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_switches_to_phase("draft")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_switches_to_phase("review")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_switches_to_phase("publication")
        story.when_user_uses_workflow_action("refresh_publication_composition", expected_status="Report plan refreshed.")

        target_spec = subject_publication_import_target_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )

        self.assertTrue(target_spec.enabled)
        option_labels = {label for label, _value in target_spec.options}
        self.assertEqual(option_labels, {"Einstein", "Wikipedia"})

    def test_007_given_pending_subject_import_when_user_rejects_it_then_publication_import_controls_remain_unavailable(self) -> None:
        source_subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")
        target_subject_id = self._given_basic_fixture_subject("02_MEET_GREET_DEPART.md")

        story = WorkflowSubjectStory(self, root=self.root, subject_id=target_subject_id)
        self._create_pending_import_from_source_to_target(
            source_subject_id=source_subject_id,
            target_story=story,
        )

        story.when_user_switches_to_phase("research")
        story.then_visible_action_labels_include("Preview Pending Import", "Approve Import", "Reject Import")
        story.when_user_uses_workflow_action(
            "preview_pending_import",
            expected_status="Pending subject import preview loaded.",
        )
        story.when_user_uses_workflow_action("reject_subject_import", expected_status="Subject import rejected.")
        story.then_visible_action_labels_exclude("Preview Pending Import", "Approve Import", "Reject Import")

        self._advance_story_to_publication_plan(story)

        target_spec = subject_publication_import_target_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        included_spec = subject_publication_import_included_switch_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        usage_spec = subject_publication_import_usage_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )

        self.assertFalse(target_spec.enabled)
        self.assertEqual(target_spec.options, ())
        self.assertFalse(included_spec.enabled)
        self.assertFalse(usage_spec.enabled)

    def test_008_given_active_subject_import_when_user_retires_it_then_report_plan_import_controls_clear(self) -> None:
        source_subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")
        target_subject_id = self._given_basic_fixture_subject("02_MEET_GREET_DEPART.md")

        story = WorkflowSubjectStory(self, root=self.root, subject_id=target_subject_id)
        self._approve_import_from_source_to_target(
            source_subject_id=source_subject_id,
            target_story=story,
        )

        self._advance_story_to_publication_plan(story)
        initial_target_spec = subject_publication_import_target_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        self.assertTrue(initial_target_spec.enabled)
        self.assertEqual([label for label, _value in initial_target_spec.options], ["Einstein"])

        story.when_user_switches_to_phase("research")
        story.then_phase_action_labels_include("Retire Active Import")
        story.when_user_uses_workflow_action("retire_subject_import", expected_status="Subject import retired.")

        story.when_user_switches_to_phase("publication")
        story.when_user_uses_workflow_action("refresh_publication_composition", expected_status="Report plan refreshed.")

        target_spec = subject_publication_import_target_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        included_spec = subject_publication_import_included_switch_spec(
            scenario=story.scenario,
            progress=story.progress,
        )
        usage_spec = subject_publication_import_usage_select_spec(
            scenario=story.scenario,
            progress=story.progress,
        )

        self.assertFalse(target_spec.enabled)
        self.assertEqual(target_spec.options, ())
        self.assertFalse(included_spec.enabled)
        self.assertFalse(usage_spec.enabled)

    def test_010_given_find_the_time_fixture_when_user_runs_default_happy_path_then_report_typ_quotes_the_phrase(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn('If you want to ask for the time, say "Velawa Kiiyadha".', artifacts.report_typ)
        self.assertNotIn("> Velawa Kiiyadha", artifacts.report_typ)
        self.assertNotIn("\\> Velawa Kiiyadha", artifacts.report_typ)

    def test_020_given_meet_greet_depart_fixture_when_user_runs_default_happy_path_then_report_typ_renders_reader_facing_examples(self) -> None:
        subject_id = self._given_basic_fixture_subject("02_MEET_GREET_DEPART.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn('If you want to greet someone, say "Ayubowan".', artifacts.report_typ)
        self.assertIn("That's a Sri Lankan greeting saying 'May your lifespan increase'.", artifacts.report_typ)
        self.assertIn('If you need to depart, say "Mama Yannam".', artifacts.report_typ)
        self.assertIn("That's a Sri Lankan way of saying", artifacts.report_typ)
        self.assertIn('"I\'ll leave now".', artifacts.report_typ)
        self.assertNotIn("> Ayubowan", artifacts.report_typ)
        self.assertNotIn("\\> Ayubowan", artifacts.report_typ)
        self.assertNotIn("> Mama Yannam", artifacts.report_typ)
        self.assertNotIn("\\> Mama Yannam", artifacts.report_typ)

    def test_030_given_einstein_fixture_when_user_runs_default_happy_path_then_report_typ_preserves_equation_as_math(self) -> None:
        subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn("$E = M C^2$", artifacts.report_typ)
        self.assertNotIn("$$", artifacts.report_typ)
        self.assertNotIn('$E = "MC"^2$', artifacts.report_typ)

    def test_040_given_einstein_fixture_when_user_switches_to_exact_draft_then_report_typ_contains_only_the_equation_shell(self) -> None:
        subject_id = self._given_basic_fixture_subject("03_EINSTEIN.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id, exact_draft=True)

        self.assertIn("$E = M C^2$", artifacts.report_typ)
        self.assertNotIn("Executive Summary", artifacts.report_typ)
        self.assertNotIn("= Sources <sources>", artifacts.report_typ)
        self.assertNotIn("= Build Notes <report-controls>", artifacts.report_typ)
        self.assertNotIn("SECTION 01", artifacts.report_typ)

    def test_050_given_wikipedia_fixture_when_user_runs_default_happy_path_then_report_typ_normalizes_markdown_links(self) -> None:
        subject_id = self._given_basic_fixture_subject("04_WIKIPEDIA.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn("Open Wikipedia (https://en.wikipedia.org)", artifacts.report_typ)
        self.assertNotIn("[Open Wikipedia](https://en.wikipedia.org)", artifacts.report_typ)
        self.assertNotIn("\\[Open Wikipedia\\](https://en.wikipedia.org)", artifacts.report_typ)

    def test_060_given_heading_only_fixture_when_user_runs_default_happy_path_then_report_typ_still_builds_valid_governed_shell(self) -> None:
        subject_id = self._given_basic_fixture_subject("05_EMPHASIS.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn("Wait!", artifacts.report_typ)
        self.assertIn("= Sources <sources>", artifacts.report_typ)
        self.assertIn("= Build Notes <report-controls>", artifacts.report_typ)
        self.assertNotIn("######", artifacts.report_typ)
        self.assertNotIn("#####", artifacts.report_typ)

    def test_070_given_paragraph_fixture_when_user_runs_default_happy_path_then_report_typ_carries_plain_paragraph_text(self) -> None:
        subject_id = self._given_basic_fixture_subject("06_PARAGRAPHS.md")

        artifacts = self._when_user_runs_numbered_report_flow(subject_id)

        self.assertIn("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", artifacts.report_typ)
        self.assertIn("Donec sed nisi sit amet elit dictum rutrum.", artifacts.report_typ)
        self.assertNotIn("> Lorem ipsum", artifacts.report_typ)

    def test_900_given_learned_subject_when_user_checks_maintained_from_gather_then_workflow_stays_in_gather(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.then_phase_is("research")
        story.then_current_step_contains("Activate this subject")
        story.then_primary_action_is("Activate Subject")

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        story.when_user_switches_to_phase("research")
        story.then_phase_is("research")
        story.then_current_step_contains("Run the maintained-files check")
        story.then_primary_action_is("Check Maintained Files")

        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")

        story.then_phase_is("research")
        story.then_current_step_contains("Create the report plan")

    def test_910_given_fresh_learned_subject_when_user_aligns_maintained_files_then_gather_requires_itemize_before_draft(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.then_phase_is("research")
        story.then_current_step_contains("Run the maintained-files check")
        story.then_primary_action_is("Check Maintained Files")

        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")

        story.then_phase_is("research")
        story.then_guidance_phase_is("itemize")
        story.then_current_step_contains("Generate the itemization inventory")
        story.then_primary_action_is("Generate Itemization")
        story.then_visible_action_labels_include("Generate Itemization")
        story.then_visible_action_labels_exclude("Go To Draft", "Create Draft Composition", "Refresh Draft Composition")

    def test_920_given_current_itemization_when_user_moves_to_draft_then_draft_opens_with_composed_candidate_inventory(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        move_result = story.when_user_uses_workflow_action("goto_draft", expected_status="Moved to Draft.")

        self.assertIn("Entered Draft with composition", move_result.timeline_text)
        story.then_phase_is("draft")
        story.then_current_step_contains("Create the report plan")
        draft_tree = render_subject_draft_tree(
            scenario=story.scenario,
            progress=story.progress,
        )
        self.assertIn("Find the Time (Claim -> Paragraph)", draft_tree)
        self.assertIn("Find the Time (Definition -> Paragraph)", draft_tree)
        story.then_visible_action_labels_exclude("Create Draft Composition", "Refresh Draft Composition")

    def test_922_given_itemized_dst_subject_when_user_suggests_constructs_then_candidates_are_persisted_from_itemize(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus ticketing modernization.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_switches_to_phase("itemize")
        story.then_visible_action_labels_include("Suggest DST Constructs")
        story.when_user_uses_workflow_action(
            "suggest_transformation_constructs",
            expected_status="Transformation constructs suggested.",
        )

        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        self.assertGreater(len(construct_candidates), 0)
        receipt = "\n".join(story.progress.latest_receipt_lines)
        self.assertIn("- method: DST fixture seed", receipt)
        self.assertIn("- suggested constructs:", receipt)

    def test_925_given_weakly_structured_prose_when_itemization_runs_then_default_workstation_policy_uses_direct_llm_decomposition(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v1.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)
        captured: dict[str, object] = {}

        class FakeController:
            def request_proposal(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(
                    id="proposal-direct-itemize",
                    source="fake-runtime",
                    payload={
                        "candidates": [
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="City transit authority",
                                summary="City transit authority leading the fare-payment modernization.",
                                decision_role="actor",
                            ),
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="Legacy fare payment via cash",
                                summary="Current payment mode dominated by cash use.",
                                decision_role="state",
                            ),
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="Legacy fare payment via plastic transit cards",
                                summary="Current payment mode still depends on plastic transit cards.",
                                decision_role="state",
                            ),
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="Introduce contactless bank-card payment",
                                summary="Target payment mode introduces contactless bank-card payment.",
                                decision_role="transition",
                            ),
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="Fare payment supports contactless bank-card payment",
                                summary="The achieved fare-payment arrangement supports contactless bank-card payment.",
                                decision_role="state",
                            ),
                        ]
                    },
                )

        test_case = self

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(FakeController()),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        labels = {
            item.canonical_label
            for item in list_itemized_subject_items(self.root, subject_id)
        }
        self.assertTrue(
            {
                "City transit authority",
                "Legacy fare payment via cash",
                "Legacy fare payment via plastic transit cards",
                "Introduce contactless bank-card payment",
                "Fare payment supports contactless bank-card payment",
            }.issubset(labels)
        )
        self.assertEqual(captured["proposal_type"], ProposalType.NOT_DECOMPOSITION)
        self.assertIn("cash", str(captured["instructions"]).lower())
        self.assertIn("plastic transit cards", str(captured["instructions"]).lower())
        self.assertIn("do not emit bare nouns like 'Cash'", str(captured["instructions"]))
        self.assertIn("emit role-shaped transition labels like 'introduce app-based payment'", str(captured["instructions"]))
        self.assertIn("emit both the transition and the resulting target state or capability", str(captured["instructions"]))
        self.assertIn("- direct llm decomposition: used", "\n".join(story.progress.latest_receipt_lines))

    def test_926_given_workstation_launch_opt_out_when_itemization_runs_then_direct_llm_decomposition_stays_off(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Create reports from basic fixture markdown files through the workstation flow.",
            allow_direct_llm_decomposition=False,
        )
        subject_id = self._given_dst_fixture_subject("City bus prose v1.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            side_effect=AssertionError("direct llm decomposition should be disabled"),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        self.assertIn("- direct llm decomposition: disabled", "\n".join(story.progress.latest_receipt_lines))

    def test_927_given_weakly_structured_prose_when_direct_llm_returns_empty_then_itemization_falls_back_to_generic_source_decomposition(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v1.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        class FakeController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(FakeController()),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        labels = {
            str(item.canonical_label).strip().casefold()
            for item in list_itemized_subject_items(self.root, subject_id)
        }
        self.assertTrue(
            {
                "city transit authority",
                "modernize fare payment",
                "legacy fare payment via cash",
                "legacy fare payment via plastic transit cards",
                "introduce app-based payment",
                "introduce contactless bank-card payment",
                "fare payment supports app-based payment",
                "fare payment supports contactless bank-card payment",
            }.issubset(labels)
        )
        receipt = "\n".join(story.progress.latest_receipt_lines)
        self.assertIn("- direct llm decomposition: fallback", receipt)
        self.assertIn("- direct llm candidates: 0", receipt)

    def test_928_given_prose_with_explicit_party_list_when_itemization_runs_then_actor_candidates_follow_the_source_parties(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v2.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        class FakeController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-v2",
                    source="fake-runtime",
                    payload={
                        "candidates": [
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="City now",
                                summary="The city now wants to introduce app-based payment.",
                                decision_role="actor",
                            ),
                            ReportCreationBDDTests._direct_llm_candidate_payload(
                                self=test_case,
                                label="Introduce app-based payment",
                                summary="Target payment mode introduces app-based payment.",
                                decision_role="transition",
                            ),
                        ]
                    },
                )

        test_case = self

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(FakeController()),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        labels_by_role: dict[str, set[str]] = {}
        for item in list_itemized_subject_items(self.root, subject_id):
            role = str(item.metadata.get("decision_role", "")).casefold()
            if not role:
                continue
            labels_by_role.setdefault(role, set()).add(str(item.canonical_label).casefold())

        self.assertTrue(
            {
                "city transit authority",
                "private bus operators",
                "payment processor",
                "city regulator",
                "passengers",
            }.issubset(labels_by_role.get("actor", set()))
        )
        self.assertNotIn("city now", labels_by_role.get("actor", set()))
        self.assertNotIn("city", labels_by_role.get("actor", set()))
        self.assertIn("keep bus network reliable", labels_by_role.get("constraint", set()))
        self.assertIn("keep bus network accessible", labels_by_role.get("constraint", set()))

    def test_929_given_objective_candidate_from_weak_prose_when_user_suggests_dst_constructs_then_projection_respects_selected_role(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v2.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-v2-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(EmptyController()),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if str(item.metadata.get("decision_role", "")).casefold() == "objective"
            and "easy, fast, trustworthy, and fair" in str(item.canonical_label).casefold()
        )
        story.progress.itemize_selected_item_id = selected_item.itemized_item_id
        story.when_user_switches_to_phase("itemize")
        story.then_visible_action_labels_include("Suggest DST Constructs")
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=RuntimeError("llm unavailable in test"),
        ):
            story.when_user_uses_workflow_action(
                "suggest_transformation_constructs",
                expected_status="Transformation constructs suggested.",
            )

        selected_candidates = [
            candidate
            for candidate in list_transformation_construct_candidates(self.root, subject_id)
            if candidate.itemized_item_id == selected_item.itemized_item_id
        ]

        self.assertEqual(len(selected_candidates), 1)
        self.assertEqual({candidate.sort_kind for candidate in selected_candidates}, {"objective"})

    def test_929a_given_subject_claim_from_weak_prose_when_user_suggests_dst_constructs_then_real_objectives_and_actors_are_materialized(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v2.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-v2-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(EmptyController()),
        ):
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")

        claim_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if collapse_ws(item.item_kind) == "claim" and collapse_ws(item.canonical_label) == "Smart City Travel"
        )
        story.progress.itemize_selected_item_id = claim_item.itemized_item_id
        story.when_user_switches_to_phase("itemize")
        story.then_visible_action_labels_include("Suggest DST Constructs")
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=RuntimeError("llm unavailable in test"),
        ):
            story.when_user_uses_workflow_action(
                "suggest_transformation_constructs",
                expected_status="Transformation constructs suggested.",
            )

        candidate_pairs = {
            (collapse_ws(candidate.canonical_label), collapse_ws(candidate.sort_kind))
            for candidate in list_transformation_construct_candidates(self.root, subject_id)
        }
        self.assertIn(("modernize fare payment", "objective"), candidate_pairs)
        self.assertIn(
            ("changes that can be implemented without disrupting daily service", "objective"),
            candidate_pairs,
        )
        self.assertIn(
            ("the payment system to be easy, fast, trustworthy, and fair", "objective"),
            candidate_pairs,
        )
        self.assertIn(("city regulator", "actor"), candidate_pairs)
        self.assertIn(("city transit authority", "actor"), candidate_pairs)
        self.assertNotIn(("Smart City Travel", "actor"), candidate_pairs)

    def test_930_given_dst_city_bus_markdown_when_user_reaches_draft_then_decision_analysis_is_the_primary_next_step(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus ticketing modernization.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        story.when_user_switches_to_phase("draft")
        story.then_current_step_contains("Start decision analysis")
        story.then_primary_action_is("Start Decision Analysis")
        story.then_visible_action_labels_exclude("Create Report Plan")

    def test_932_given_weak_prose_v10_when_user_focuses_a_later_draft_row_then_start_decision_analysis_remains_primary(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v10.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        later_review_item = next(
            item
            for item in reversed(list_review_items(self.root, subject_id))
            if collapse_ws(item.review_item_id) and collapse_ws(item.review_item_id) != collapse_ws(story.progress.draft_selected_review_item_id)
        )
        story.progress.draft_selected_review_item_id = later_review_item.review_item_id

        story.when_user_switches_to_phase("draft")
        story.then_current_step_contains("Start decision analysis")
        story.then_primary_action_is("Start Decision Analysis")
        story.then_visible_action_labels_exclude("Include In Decision Analysis", "Run Decision Analysis")

    def test_933_given_same_subject_v2_then_v10_when_user_focuses_a_later_nonincluded_draft_row_then_refresh_dst_analysis_remains_primary(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v2.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_uses_workflow_action(
            "create_decision_frame_from_selected_draft_item",
            expected_status="Decision analysis started. Report plan updated.",
        )
        story.when_user_uses_workflow_action(
            "analyze_decision_frame",
            expected_status="Decision analysis completed. Report plan updated.",
        )

        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=self.dst_root / "City bus prose v10.md",
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")
        self.assertEqual(str(learn_result.payload["report"]["learning_context"]["subject_id"]), subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        included_review_item_ids = {
            collapse_ws(item.review_item_id)
            for item in list_decision_review_items(self.root, subject_id)
            if item.included and collapse_ws(item.status) != "rejected"
        }
        later_nonincluded_review_item = next(
            item
            for item in reversed(list_review_items(self.root, subject_id))
            if collapse_ws(item.review_item_id) and collapse_ws(item.review_item_id) not in included_review_item_ids
        )
        story.progress.draft_selected_review_item_id = later_nonincluded_review_item.review_item_id

        story.when_user_switches_to_phase("draft")
        story.then_current_step_contains("Refresh the DST-backed decision analysis")
        story.then_primary_action_is("Refresh DST Analysis")
        story.then_visible_action_labels_exclude("Include In Decision Analysis", "Review: Hand To Review")

    def test_934_given_weak_prose_v10_when_user_enters_review_or_publication_before_analysis_then_draft_start_decision_analysis_remains_primary(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v10.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        story.when_user_switches_to_phase("review")
        story.then_current_step_contains("Start decision analysis")
        story.then_primary_action_is("Start Decision Analysis")
        story.then_all_visible_action_labels_exclude("Approve For Report")

        story.when_user_switches_to_phase("publication")
        story.then_current_step_contains("Start decision analysis")
        story.then_primary_action_is("Start Decision Analysis")
        story.then_all_visible_action_labels_exclude("Lock Report Inputs", "Build Report")

    def test_936_given_same_subject_v2_then_v10_when_user_enters_review_or_publication_then_draft_refresh_dst_analysis_remains_primary(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus prose v2.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_uses_workflow_action(
            "create_decision_frame_from_selected_draft_item",
            expected_status="Decision analysis started. Report plan updated.",
        )
        story.when_user_uses_workflow_action(
            "analyze_decision_frame",
            expected_status="Decision analysis completed. Report plan updated.",
        )

        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=self.dst_root / "City bus prose v10.md",
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")
        self.assertEqual(str(learn_result.payload["report"]["learning_context"]["subject_id"]), subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

        story.when_user_switches_to_phase("review")
        story.then_current_step_contains("Refresh the DST-backed decision analysis")
        story.then_primary_action_is("Refresh DST Analysis")
        story.then_all_visible_action_labels_exclude("Approve For Report")

        story.when_user_switches_to_phase("publication")
        story.then_current_step_contains("Refresh the DST-backed decision analysis")
        story.then_primary_action_is("Refresh DST Analysis")
        story.then_all_visible_action_labels_exclude("Lock Report Inputs", "Build Report")

    def test_935_given_current_report_plan_when_user_reviews_it_then_preview_and_compare_paths_are_available_before_approval(self) -> None:
        subject_id = self._given_basic_fixture_subject("01_FIND_THE_TIME.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
        story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
        story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
        story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
        story.when_user_uses_workflow_action("refresh_publication_composition", expected_status="Report plan refreshed.")

        story.when_user_switches_to_phase("review")
        story.then_visible_action_labels_include("Preview Report Plan", "Compare Report Plans", "Approve For Report")
        story.when_user_uses_workflow_action(
            "preview_publication_composition",
            expected_status="Report plan preview loaded.",
        )
        self.assertEqual(story.progress.latest_receipt_title, "Report Plan Preview")
        story.when_user_uses_workflow_action(
            "preview_publication_composition_diff",
            expected_status="Report plan diff loaded.",
        )
        self.assertEqual(story.progress.latest_receipt_title, "Report Plan Diff")
        self.assertTrue(any("baseline" in line.casefold() for line in story.progress.latest_receipt_lines))

    def test_940_given_dst_city_bus_markdown_when_user_runs_decision_flow_then_report_contains_decision_matrix(self) -> None:
        subject_id = self._given_dst_fixture_subject("City bus ticketing modernization.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")

            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.then_primary_action_is("Run Decision Analysis")
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.then_phase_is("review")
            story.then_primary_action_is("Approve For Report")
            story.then_current_step_contains("Approve the report and decision analysis")
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_typ = Path(rebuilt.report_typst_path).read_text(encoding="utf-8")
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_typ)
        self.assertIn("Decision Recommendation", report_typ)
        self.assertIn("Decision Option Matrix", report_md)
        self.assertIn("Decision Recommendation", report_md)
        self.assertIn("Case Frame", report_md)
        self.assertIn("Execution Guidance", report_md)

    def test_950_given_dst_hospital_markdown_when_user_runs_decision_flow_then_report_contains_decision_matrix(self) -> None:
        subject_id = self._given_dst_fixture_subject("Hospital medication system upgrade.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_typ = Path(rebuilt.report_typst_path).read_text(encoding="utf-8")
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_typ)
        self.assertIn("Decision Recommendation", report_typ)
        self.assertIn("Case Frame", report_md)
        self.assertIn("Execution Guidance", report_md)

    def test_960_given_dst_national_markdown_when_user_runs_decision_flow_then_only_the_executable_rollout_is_recommended(self) -> None:
        subject_id = self._given_dst_fixture_subject("National School System Exam Digitization Rollout.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_md)
        self.assertIn("Recommended options: Resilience-first audited rollout.", report_md)
        self.assertNotIn("Recommended options: Conservative layered rollout", report_md)
        self.assertIn("Resilience-first audited rollout | recommended |", report_md)
        self.assertIn("Conservative layered rollout | valid_but_not_executable |", report_md)
        self.assertIn("Direct national leap | blocked |", report_md)
        self.assertIn("### Case Frame", report_md)
        self.assertIn("### Execution Guidance", report_md)
        self.assertNotIn("Why this is very complex", report_md)

    def test_970_given_dst_regional_markdown_when_user_runs_decision_flow_then_only_balanced_configuration_is_recommended(self) -> None:
        subject_id = self._given_dst_fixture_subject("Regional emergency alerting system.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_md)
        self.assertIn("Recommended options: Balanced configuration.", report_md)
        self.assertNotIn("Recommended options: Resilience-first configuration", report_md)
        self.assertIn("Balanced configuration | recommended |", report_md)
        self.assertIn("Inclusion-first configuration | valid_but_not_executable |", report_md)
        self.assertIn("Speed-first configuration | blocked |", report_md)
        self.assertIn("### Case Frame", report_md)
        self.assertIn("### Execution Guidance", report_md)
        self.assertNotIn("Many good outcomes", report_md)

    def test_980_given_dst_library_markdown_when_user_runs_decision_flow_then_report_reads_like_a_decision_publication(self) -> None:
        subject_id = self._given_dst_fixture_subject("Town library self-checkout rollout.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        report_typst = Path(rebuilt.report_typst_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_md)
        self.assertIn("Recommended options: Branch pilot with staffed support.", report_md)
        self.assertIn("Branch pilot with staffed support | recommended |", report_md)
        self.assertIn(
            "staffed checkout only → Branch pilot with staffed support → multi-branch kiosks with staffed support",
            report_md,
        )
        self.assertIn("library administration", report_md)
        self.assertIn("Kiosk-first cutover | blocked |", report_md)
        self.assertIn("### Case Frame", report_md)
        self.assertIn("### 3.1 Option Assessment and Ranking", report_md)
        self.assertIn("### 3.2 Path and Coordination Model", report_md)
        self.assertIn("### 3.3 Dependencies and Risk", report_md)
        self.assertIn("### 4.1 Execution Guidance", report_md)
        self.assertIn("### Decision Recommendation Receipt", report_md)
        self.assertIn("Recommended option: Branch pilot with staffed support", report_md)
        self.assertIn("Recommended path:", report_md)
        self.assertIn("Recommended actors: library administration", report_md)
        self.assertIn("Recommended capabilities:", report_md)
        self.assertIn("Blocked options:", report_md)
        self.assertIn("Path: staffed checkout only → Kiosk-first cutover → kiosk-first checkout with minimal staffed support", report_md)
        self.assertIn("### Decision Ranking Summary", report_md)
        self.assertIn("### Execution Guidance", report_md)
        self.assertIn("Candidate paths: 1", report_md)
        self.assertIn("Policy guidance:", report_md)
        self.assertIn("Blocked option readings:", report_md)
        self.assertIn("Kiosk-first cutover: Do not advance under current conditions.", report_md)
        self.assertIn("To reconsider: close dependencies", report_md)
        self.assertIn("Implementation prerequisites:", report_md)
        self.assertIn("Coordination boundaries to govern:", report_md)
        self.assertIn("Blocked option readings", report_typst)

    def test_990_given_dst_clinic_markdown_when_user_runs_decision_flow_then_report_distinguishes_recommended_and_non_executable_options(self) -> None:
        subject_id = self._given_dst_fixture_subject("Community clinic appointment reminders.md")
        story = WorkflowSubjectStory(self, root=self.root, subject_id=subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=self._fake_dst_pipeline,
        ):
            story.when_user_uses_workflow_action("open_context", expected_status="Subject context opened.")
            story.when_user_uses_workflow_action("compare_projections", expected_status="Projection comparison aligned.")
            story.when_user_uses_workflow_action("generate_itemization", expected_status="Itemization generated.")
            story.when_user_uses_workflow_action("refresh_review_composition", expected_status="Draft composition refreshed.")
            story.when_user_switches_to_phase("draft")
            story.then_primary_action_is("Start Decision Analysis")
            story.when_user_uses_workflow_action(
                "create_decision_frame_from_selected_draft_item",
                expected_status="Decision analysis started from DST discovery. Report plan updated.",
            )
            story.when_user_uses_workflow_action(
                "analyze_decision_frame",
                expected_status="Decision analysis completed. Report plan updated.",
            )
            story.when_user_uses_workflow_action("approve_review", expected_status="Review approved for report publication.")
            story.when_user_uses_workflow_action("lock_publication", expected_status="Publication inputs locked.")
            story.when_user_uses_workflow_action("build_report", expected_status="Report build completed")

        rebuilt = self._scenario_for_subject(subject_id)
        report_md = Path(rebuilt.report_markdown_path).read_text(encoding="utf-8")
        report_typst = Path(rebuilt.report_typst_path).read_text(encoding="utf-8")
        self.assertIn("Decision Option Matrix", report_md)
        self.assertIn("Recommended options: Inclusive reminder rollout.", report_md)
        self.assertIn("Inclusive reminder rollout | recommended |", report_md)
        self.assertIn(
            "manual phone reminders only → Inclusive reminder rollout → SMS reminders with multilingual templates and call fallback",
            report_md,
        )
        self.assertIn("clinic operations lead", report_md)
        self.assertIn("Lean SMS rollout | valid_but_not_executable |", report_md)
        self.assertIn("Portal-only reminders | blocked |", report_md)
        self.assertIn("### Case Frame", report_md)
        self.assertIn("### 3.1 Option Assessment and Ranking", report_md)
        self.assertIn("### 3.2 Path and Coordination Model", report_md)
        self.assertIn("### 3.3 Dependencies and Risk", report_md)
        self.assertIn("### 4.1 Execution Guidance", report_md)
        self.assertIn("### Decision Recommendation Receipt", report_md)
        self.assertIn("Recommended option: Inclusive reminder rollout", report_md)
        self.assertIn("Recommended path:", report_md)
        self.assertIn("Recommended actors: clinic operations lead", report_md)
        self.assertIn("Recommended capabilities:", report_md)
        self.assertIn("Reserve options:", report_md)
        self.assertIn("Blocked options:", report_md)
        self.assertIn("Path: manual phone reminders only → Lean SMS rollout → SMS reminders only", report_md)
        self.assertIn("Path: manual phone reminders only → Portal-only reminders → portal-app-only reminders", report_md)
        self.assertIn("### Decision Ranking Summary", report_md)
        self.assertIn("### Execution Guidance", report_md)
        self.assertIn("Candidate paths: 1", report_md)
        self.assertIn("Policy guidance:", report_md)
        self.assertIn("Reserve option readings:", report_md)
        self.assertIn("Lean SMS rollout: Keep in reserve until execution conditions are materially stronger.", report_md)
        self.assertIn("Blocked option readings:", report_md)
        self.assertIn("Portal-only reminders: Do not advance under current conditions.", report_md)
        self.assertIn("To reconsider: close dependencies", report_md)
        self.assertIn("Implementation prerequisites:", report_md)
        self.assertIn("Coordination boundaries to govern:", report_md)
        self.assertIn("Alternatives to keep in reserve:", report_md)
        self.assertIn("Lean SMS rollout: responsible actors:", report_md)
        self.assertIn("Reserve option readings", report_typst)
        self.assertIn("Blocked option readings", report_typst)
        self.assertNotIn("This path automates the first reminder", report_md)

if __name__ == "__main__":
    unittest.main()
