# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import replace
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from controller_entrypoints import ensure_application_controller_runtime
from decision_review import list_decision_review_items, load_decision_frame
from decision_review_constructs import (
    TransformationConstructCandidate,
    deterministic_transformation_construct_candidates_from_itemized_item,
    list_transformation_construct_candidates,
    normalize_transformation_construct_sort_kind,
    persist_transformation_construct_candidates,
    stable_transformation_construct_candidate_id,
)
from decision_review_policy import load_decision_policy_profile
from decision_review_projection import list_decision_analysis_receipts
from dst import (
    DST_SOURCE_ROOT,
    discovery_result_from_fixture,
    load_dst_use_cases,
    normalized_case_from_fixture,
    run_dst_pipeline_from_fixture,
)
from gather_sources import (
    latest_source_revision,
    list_source_collections,
    list_staged_sources,
    new_source_collection,
    new_source_revision,
    new_staged_source,
    persist_source_collection,
    persist_source_revision,
    persist_staged_source,
)
from learning_context import (
    LearningContext,
    LearningUnit,
    list_subject_imports,
    load_learning_context,
    load_learning_source,
    new_learning_delta,
    new_learning_source,
    new_subject_import,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    persist_subject_import,
    stable_learning_unit_id,
)
from itemize import (
    ItemizedSubjectItem,
    canonical_learning_subject_id,
    itemization_paths,
    list_itemized_subject_items,
    load_itemization_session,
    normalize_itemized_decision_role,
)
from publication import PublicationComposition, list_publication_compositions, publication_subject_root
from review_composition import (
    list_review_items,
    list_review_transform_receipts,
    load_review_composition,
    review_composition_paths,
)
from semantic_text import collapse_ws
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.subject.core.subject_workflow import (
    _decision_review_state,
    _prune_same_label_construct_clones_for_explicit_item_role,
    _prune_same_label_subject_title_construct_clones,
    _gate_phase_action,
    _gate_subject_nav_action,
    _normalize_current_step_gate_action_for_phase,
    _report_scope_entries,
    _report_item_select_label,
    _subject_transformation_construct_candidates,
    _set_report_scope_cursor_to_entry_id,
    apply_subject_action,
    default_subject_scenarios,
    load_subject_import_staging,
    load_subject_progress,
    load_subject_progress_map,
    new_subject_progress,
    persist_subject_progress,
    render_subject_current_step,
    subject_current_step_view,
    render_subject_draft_detail,
    render_subject_draft_issue_tray,
    render_subject_draft_model_main,
    render_subject_draft_tree,
    subject_draft_model_main_title,
    subject_draft_tree_title,
    render_subject_itemize_detail,
    render_subject_itemize_inventory,
    render_subject_itemize_target,
    render_subject_publication_gate,
    render_subject_report_scope_detail,
    render_subject_report_scope_tree,
    render_subject_journey,
    render_subject_research_observation,
    render_subject_research_sources,
    render_subject_research_target,
    render_subject_review_gate,
    render_subject_status,
    render_subject_workspace,
    move_draft_review_cursor,
    move_itemize_cursor,
    move_report_scope_cursor,
    preview_move_held_report_scope_items,
    subject_current_step_actions,
    subject_more_action_specs,
    subject_publication_gate_actions,
    subject_review_gate_actions,
    subject_draft_evidence_mode_select_spec,
    subject_draft_model_construct_lane_select_spec,
    subject_draft_model_relation_selection_list_specs,
    subject_draft_model_transition_source_select_spec,
    subject_draft_model_transition_target_select_spec,
    subject_draft_model_construct_sort_select_spec,
    subject_draft_model_policy_profile_select_spec,
    subject_draft_decision_included_switch_spec,
    subject_draft_render_kind_select_spec,
    subject_draft_semantic_kind_select_spec,
    subject_draft_transform_mode_select_spec,
    subject_has_pending_research_capture,
    subject_action_specs,
    subject_itemize_decision_role_select_spec,
    subject_itemize_hold_switch_spec,
    subject_research_selected_source_collection_membership_switch_spec,
    subject_research_selected_source_change_summary_table_spec,
    subject_research_selected_source_revision_history_table_spec,
    subject_research_source_collection_actionable_export_table_spec,
    subject_research_source_collection_export_applied_table_spec,
    subject_research_source_collection_member_export_status_table_spec,
    subject_research_source_collection_member_revision_table_spec,
    subject_research_source_collection_merge_export_history_table_spec,
    subject_research_source_collection_select_spec,
    subject_research_source_revision_baseline_select_spec,
    subject_review_composition_unit_included_switch_spec,
    subject_review_composition_unit_target_select_spec,
    subject_review_publication_diff_baseline_select_spec,
    subject_review_publication_output_mode_select_spec,
    subject_review_publication_section_included_switch_spec,
    subject_review_publication_section_target_select_spec,
    subject_review_publication_section_plan_select_spec,
    subject_progress_path,
)
from workstation.runtime.core.session import launch_workstation_session
from workstation.runtime.core.workstation_core import workstation_learn_markdown_action


def _itemization_runtime_provider(controller: object) -> SimpleNamespace:
    return SimpleNamespace(
        bootstrap_controller=lambda **_kwargs: (SimpleNamespace(), controller)
    )


class SubjectWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _select_report_section(
        self,
        *,
        scenario,
        progress,
        section_title: str,
    ) -> None:
        progress.report_scope_cursor = 0
        for _ in range(64):
            detail = render_subject_report_scope_detail(
                scenario=scenario,
                progress=progress,
            )
            if detail.startswith(section_title) and "Type: Report section" in detail:
                return
            moved = move_report_scope_cursor(
                self.root,
                scenario=scenario,
                progress=progress,
                delta=1,
            )
            if moved is None:
                break
        raise AssertionError(f"Unable to select report section {section_title!r}.")

    def _persist_demo_context(self) -> str:
        subject_id = "kinematics-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Kinematics Notes\n\n"
                "## Velocity\n\n"
                "Velocity is displacement per unit time.\n\n"
                "## Acceleration From Velocity Change\n"
                "- Inputs: dv, dt\n"
                "- Output: a\n"
                "- Xref depends_on: Velocity\n\n"
                "$$ a = dv / dt $$\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the initial kinematics subject notes.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Kinematics Demo",
            aliases=("Kinematics Demo",),
            subject_family="Physics / Kinematics",
            summary="Maintained subject for introductory kinematics.",
            units=(unit,),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return subject_id

    def _persist_itemize_editor_context(self) -> str:
        subject_id = "itemize-editor-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Controls Notes",
            source_ref="notes/controls.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Controls\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n\n"
                "## Controls\nAccess and audit controls matter.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the itemize editor demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Itemize Editor Demo",
                aliases=("Itemize Editor Demo",),
                subject_family="Governance",
                summary="Itemize editor coverage subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Controls",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Controls",
                        aliases=("Access Controls", "Audit Controls"),
                        statement="Access and audit controls matter.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        return subject_id

    def _persist_dst_subject_context(self) -> str:
        subject_id = "dst-city-bus-demo"
        source_path = (
            Path(__file__).resolve().parents[2]
            / "dst"
            / "City bus ticketing modernization.md"
        ).resolve()
        source = new_learning_source(
            subject_id=subject_id,
            title="City Bus Ticketing Modernization",
            source_ref=str(source_path),
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# City Bus Ticketing Modernization\n\n"
                "The city bus operator needs a governed decision frame for ticketing modernization.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the DST bus modernization subject.",
        )
        persist_learning_delta(self.root, delta)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="City Bus Ticketing Modernization",
            aliases=("City Bus Ticketing Modernization",),
            subject_family="Decision Support",
            summary="DST-backed decision-support subject.",
            units=(
                LearningUnit(
                    unit_id=stable_learning_unit_id(
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Ticketing Modernization",
                    ),
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Ticketing Modernization",
                    statement="The operator must choose among materially distinct modernization paths.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return subject_id

    def _persist_relative_item_label_context(self) -> str:
        subject_id = "relative-item-label-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Relative Item Notes",
            source_ref="notes/relative-item.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Relative Item Demo\n\n"
                "## Situation\nCore situation.\n\n"
                "## Actors\nPeople involved.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the relative item label demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Relative Item Demo",
                aliases=("Relative Item Demo",),
                subject_family="Demo",
                summary="Relative item label coverage subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Relative Item Demo / Situation",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Relative Item Demo / Situation",
                        statement="Core situation.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Relative Item Demo / Situation / Actors",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Relative Item Demo / Situation / Actors",
                        statement="People involved.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        return subject_id

    def _persist_regional_dst_subject_context(self) -> str:
        subject_id = "regional-emergency-alerting-system"
        source_path = (
            Path(__file__).resolve().parents[2]
            / "dst"
            / "Regional emergency alerting system.md"
        ).resolve()
        source = new_learning_source(
            subject_id=subject_id,
            title="Regional emergency alerting system",
            source_ref=str(source_path),
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Regional emergency alerting system\n\n"
                "This is real-world, intuitive, and highly complex under the surface.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the DST regional emergency alerting subject.",
        )
        persist_learning_delta(self.root, delta)
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Regional emergency alerting system",
            aliases=("Regional emergency alerting system",),
            subject_family="Regional emergency alerting system",
            summary="This is real-world, intuitive, and highly complex under the surface.",
            units=(
                LearningUnit(
                    unit_id=stable_learning_unit_id(
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Regional emergency alerting system / Many good outcomes",
                    ),
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Regional emergency alerting system / Many good outcomes",
                    statement="This is real-world, intuitive, and highly complex under the surface.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return subject_id

    def _all_subject_publication_compositions(self, subject_id: str) -> tuple[PublicationComposition, ...]:
        records: list[PublicationComposition] = []
        publications_root = publication_subject_root(self.root, subject_id)
        if not publications_root.exists():
            return ()
        for path in sorted(publications_root.glob("pub_*/compositions/*.json")):
            try:
                payload = path.read_text(encoding="utf-8")
            except Exception:
                continue
            try:
                records.append(PublicationComposition.from_dict(json.loads(payload)))
            except Exception:
                continue
        return tuple(
            sorted(
                records,
                key=lambda item: (
                    int(item.updated_at_epoch_ms or 0),
                    int(item.created_at_epoch_ms or 0),
                    item.composition_id,
                ),
            )
        )

    def test_subject_workflow_generate_itemization_materializes_validated_inventory(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )

        self.assertEqual(result.status_text, "Itemization generated.")
        self.assertTrue(itemization_paths(self.root, subject_id)["session"].is_file())
        session = load_itemization_session(self.root, subject_id)
        items = list_itemized_subject_items(self.root, subject_id)
        self.assertEqual(session.subject_id, subject_id)
        self.assertGreater(len(items), 0)
        self.assertIn("- validation: ok", "\n".join(progress.latest_receipt_lines))
        self.assertIn("- item count:", "\n".join(progress.latest_receipt_lines))

        refreshed = default_subject_scenarios(self.root)[0]
        status_text = render_subject_status(scenario=refreshed, progress=progress, phase="research")
        target_text = render_subject_research_target(scenario=refreshed, progress=progress)
        workspace_text = render_subject_workspace(scenario=refreshed, progress=progress, phase="research")
        self.assertIn("Itemization:", status_text)
        self.assertIn("Itemization", target_text)
        self.assertIn("- itemization:", workspace_text)

    def test_subject_workflow_research_current_step_actions_offer_itemization_generate_refresh_and_preview(self) -> None:
        self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        actions_before = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        labels_before = [action.label for action in actions_before]
        self.assertIn("Itemize: Generate Itemization", labels_before)
        self.assertNotIn("Preview Itemization", labels_before)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        refreshed = default_subject_scenarios(self.root)[0]
        actions_after = subject_current_step_actions(
            scenario=refreshed,
            progress=progress,
            phase="research",
        )
        labels_after = [action.label for action in actions_after]
        self.assertIn("Itemize: Refresh Itemization", labels_after)
        self.assertIn("Preview Maintained Files", labels_after)

        preview_result = apply_subject_action(
            root_path=self.root,
            scenario=refreshed,
            progress=progress,
            action_key="preview_itemization",
        )
        self.assertEqual(preview_result.status_text, "Itemization inventory loaded.")
        self.assertIn("Itemization Inventory", progress.latest_receipt_title)

    def test_subject_workflow_gather_requires_itemize_before_draft_after_maintained_files_align(self) -> None:
        self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        compare_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        self.assertEqual(compare_result.status_text, "Projection comparison aligned.")

        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        actions = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        labels = [action.label for action in actions]

        self.assertIn("Generate the itemization inventory", current_step)
        self.assertEqual(labels[0], "Itemize: Generate Itemization")
        self.assertNotIn("Go To Draft", labels)
        self.assertNotIn("Create Draft Composition", labels)
        self.assertNotIn("Refresh Draft Composition", labels)

    def test_subject_workflow_itemize_phase_focuses_on_inventory_and_detail_panels(self) -> None:
        self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )

        current_step_before = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="itemize",
        )
        actions_before = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="itemize",
        )
        labels_before = [action.label for action in actions_before]
        self.assertIn("Generate the itemization inventory", current_step_before)
        self.assertIn("Generate Itemization", labels_before)
        self.assertNotIn("Preview Itemization", labels_before)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        refreshed = default_subject_scenarios(self.root)[0]

        current_step_after = render_subject_current_step(
            scenario=refreshed,
            progress=progress,
            phase="itemize",
        )
        actions_after = subject_current_step_actions(
            scenario=refreshed,
            progress=progress,
            phase="itemize",
        )
        labels_after = [action.label for action in actions_after]
        inventory_text = render_subject_itemize_inventory(scenario=refreshed, progress=progress)
        detail_text = render_subject_itemize_detail(scenario=refreshed, progress=progress)
        target_text = render_subject_itemize_target(scenario=refreshed, progress=progress)
        workspace_text = render_subject_workspace(scenario=refreshed, progress=progress, phase="itemize")

        self.assertIn("Orient the selected item", current_step_after)
        self.assertIn("Promote Item", labels_after)
        self.assertIn("Reject Item", labels_after)
        action_specs_after = subject_action_specs(scenario=refreshed, progress=progress, phase="itemize")
        action_labels_after = [spec.label for spec in action_specs_after if spec.label]
        self.assertNotIn("Hold For Merge", action_labels_after)
        self.assertNotIn("Go To Draft", action_labels_after)
        self.assertIn("Itemized Inventory", inventory_text)
        self.assertIn("Kind:", detail_text)
        self.assertNotIn("Current Item", detail_text)
        self.assertNotIn("Label:", detail_text)
        self.assertIn("Itemize Target", target_text)
        self.assertIn("Itemize Journal", workspace_text)

    def test_subject_workflow_itemize_inventory_pads_decision_roles_before_labels(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise itemize formatting.",
        )
        subject_id = "smart-city-travel"
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(
            self.root,
            source,
            source_text="\n".join(
                [
                    "# Smart City Travel",
                    "",
                    "- A city transit authority wants to modernize fare payment.",
                    "- Today riders mostly use cash and plastic transit cards.",
                    "- The city wants to introduce app-based and contactless bank-card payment.",
                ]
            ),
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Smart City Travel",
                aliases=("Smart City Travel",),
                subject_family="Transit",
                summary="Fare modernization prose.",
                units=(
                    LearningUnit(
                        unit_id="unit_smart_city_travel",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Smart City Travel",
                        statement="A city transit authority wants to modernize fare payment.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
            host_actions=RuntimeSubjectWorkflowHostActions(),
        )

        inventory_text = render_subject_itemize_inventory(scenario=scenario, progress=progress)

        self.assertIn("[c] objective  - modernize fare payment", inventory_text)
        self.assertIn("[c] state      - legacy fare payment via cash", inventory_text)
        self.assertIn("[c] transition - introduce app-based payment", inventory_text)
        self.assertIn("[c] state      - fare payment supports contactless bank-card payment", inventory_text)
        self.assertIn("[c] Smart City Travel (claim)", inventory_text)

    def test_subject_workflow_draft_phase_focuses_on_report_scope_and_workspace(self) -> None:
        self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        current_step_before = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="draft",
        )
        actions_before = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="draft",
        )
        labels_before = [action.label for action in actions_before]
        self.assertIn("Create the draft composition", current_step_before)
        self.assertIn("Create Draft Composition", labels_before)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )

        refreshed = default_subject_scenarios(self.root)[0]
        current_step_after = render_subject_current_step(
            scenario=refreshed,
            progress=progress,
            phase="draft",
        )
        tree_text = render_subject_report_scope_tree(scenario=refreshed, progress=progress)
        detail_text = render_subject_report_scope_detail(scenario=refreshed, progress=progress)
        workspace_text = render_subject_workspace(scenario=refreshed, progress=progress, phase="draft")

        self.assertTrue(
            any(
                marker in current_step_after
                for marker in (
                    "Finish shaping this report item",
                    "Start decision analysis",
                    "Run decision analysis",
                    "Decision analysis is ready",
                    "Finish the draft and hand it to Review",
                )
            )
        )
        self.assertIn("Question-shaped items are tagged [question]", tree_text)
        self.assertIn("Report plan status: draft", tree_text)
        self.assertIn("Included in report:", detail_text)
        self.assertIn("Draft Journal", workspace_text)
        self.assertIn("draft composition id:", workspace_text)
        self.assertIn("Review remains the explicit approval gate", workspace_text)
        draft_action_labels = tuple(
            spec.label for spec in subject_action_specs(scenario=refreshed, progress=progress, phase="draft")
        )
        self.assertTrue(draft_action_labels[0].startswith("Semantic ("))
        self.assertTrue(draft_action_labels[1].startswith("Render ("))
        self.assertTrue(draft_action_labels[2].startswith("Evidence ("))
        self.assertTrue(draft_action_labels[3].startswith("Transform ("))

    def test_subject_workflow_refresh_review_composition_includes_all_non_rejected_items_even_when_one_item_is_promoted(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")

        beta_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Beta",
            item_kind="glossary_term",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="promote_selected_itemized_item",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        draft_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        self.assertEqual(draft_result.status_text, "Draft composition refreshed.")
        self.assertTrue(review_composition_paths(self.root, subject_id)["composition"].is_file())

        review_composition = load_review_composition(self.root, subject_id)
        review_items = list_review_items(self.root, subject_id)
        selected_review_item = next(
            item for item in review_items if item.source_itemized_item_id == beta_item_id
        )
        self.assertTrue(selected_review_item.included)
        self.assertIn("Draft Composition", progress.latest_receipt_title)

        plan_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        self.assertEqual(plan_result.status_text, "Report plan refreshed.")

        refreshed = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        composition = self._latest_subject_composition(scenario=refreshed)

        self.assertEqual(composition.metadata.get("draft_review_composition_id"), review_composition.review_composition_id)
        self.assertEqual(composition.metadata.get("unit_selection_mode"), "draft_review")
        self.assertGreaterEqual(len(composition.included_unit_ids), 2)
        self.assertIn(stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Alpha"), composition.included_unit_ids)
        self.assertIn(stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Beta"), composition.included_unit_ids)
        self.assertIn("Beta", render_subject_workspace(scenario=refreshed, progress=progress, phase="draft"))

    def test_subject_workflow_goto_draft_auto_materializes_current_draft_composition_from_itemization(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")

        move_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="goto_draft",
        )

        refreshed = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        current_step = render_subject_current_step(
            scenario=refreshed,
            progress=progress,
            phase="draft",
        )
        draft_tree = render_subject_draft_tree(
            scenario=refreshed,
            progress=progress,
        )
        workspace_text = render_subject_workspace(scenario=refreshed, progress=progress, phase="draft")

        self.assertEqual(move_result.status_text, "Moved to Draft.")
        self.assertTrue(review_composition_paths(self.root, subject_id)["composition"].is_file())
        self.assertIn("Create the report plan", current_step)
        self.assertIn("Alpha", draft_tree)
        self.assertIn("Draft Journal", workspace_text)
        self.assertIn("draft composition id:", workspace_text)

    def test_subject_workflow_draft_model_mode_shows_transformation_construct_inventory(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        open_model = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        draft_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        draft_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        draft_issue_tray = render_subject_draft_issue_tray(scenario=scenario, progress=progress)
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")
        action_specs = subject_action_specs(scenario=scenario, progress=progress, phase="draft")

        self.assertEqual(open_model.status_text, "Moved Draft focus to Model.")
        self.assertRegex(subject_draft_tree_title(scenario=scenario, progress=progress), r"^Case Objects \(\d+\)$")
        self.assertEqual(subject_draft_model_main_title(scenario=scenario, progress=progress), "Transformation Model")
        self.assertIn("Accept this construct into decision analysis", current_step)
        self.assertNotIn("Active lens:", draft_tree)
        self.assertNotIn("Objects (", draft_tree)
        self.assertIn("Tabs:", draft_main)
        self.assertIn("Capabilities | Dependencies | Constraints | States | Transitions", draft_main)
        self.assertIn("Inspector", draft_detail)
        self.assertIn("Status Snapshot", draft_issue_tray)
        self.assertIn("open issues:", draft_issue_tray)
        self.assertIn("recommendation status:", draft_issue_tray)
        self.assertIn("mode: Model", workspace_text)
        self.assertIn("lens: Model", workspace_text)
        self.assertEqual(action_specs[0].label, "Back To Compose")
        self.assertEqual(action_specs[1].label, "Frame")
        self.assertEqual(action_specs[2].label, "Model")
        self.assertEqual(action_specs[3].label, "Explore")
        self.assertFalse(action_specs[2].enabled)

    def test_subject_workflow_accept_construct_candidate_creates_decision_analysis_frame(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        accept = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="accept_selected_draft_construct_candidate",
        )

        frame = load_decision_frame(self.root, subject_id)
        decision_items = list_decision_review_items(self.root, subject_id)
        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")
        action_specs = subject_action_specs(scenario=scenario, progress=progress, phase="draft")

        self.assertIn("Construct accepted into decision analysis.", accept.status_text)
        self.assertTrue(frame.decision_frame_id)
        self.assertGreater(len(decision_items), 0)
        self.assertTrue(any(candidate.status == "accepted" for candidate in construct_candidates))
        self.assertIn("Run decision analysis", current_step)
        self.assertIn("mode: Model", workspace_text)
        self.assertIn("lens: Model", workspace_text)
        self.assertIn("accepted constructs: 1", workspace_text)
        self.assertEqual(action_specs[0].label, "Back To Compose")
        self.assertEqual(action_specs[1].label, "Frame")
        self.assertEqual(action_specs[2].label, "Model")
        self.assertEqual(action_specs[3].label, "Explore")

    def test_subject_workflow_accept_construct_candidate_can_cycle_lane(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="accept_selected_draft_construct_candidate",
        )

        cycle = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_selected_draft_construct_lane",
        )

        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        action_specs = subject_action_specs(scenario=scenario, progress=progress, phase="draft")

        self.assertIn("Construct role updated.", cycle.status_text)
        self.assertIn("lane: Supporting Evidence", draft_detail)
        self.assertEqual(action_specs[1].label, "Frame")
        self.assertEqual(action_specs[2].label, "Model")
        self.assertEqual(action_specs[3].label, "Explore")

    def test_subject_workflow_draft_model_widget_specs_support_sort_lane_and_policy_selection(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        sort_spec = subject_draft_model_construct_sort_select_spec(scenario=scenario, progress=progress)
        lane_spec_before_accept = subject_draft_model_construct_lane_select_spec(scenario=scenario, progress=progress)
        policy_spec_before_accept = subject_draft_model_policy_profile_select_spec(scenario=scenario, progress=progress)

        self.assertEqual(sort_spec.label, "Change Type")
        self.assertEqual(lane_spec_before_accept.label, "Change Role")
        self.assertEqual(policy_spec_before_accept.label, "Decision Policy")
        self.assertTrue(sort_spec.enabled)
        self.assertFalse(lane_spec_before_accept.enabled)
        self.assertFalse(policy_spec_before_accept.enabled)

        next_sort = next(value for _label, value in sort_spec.options if value != sort_spec.value)
        sort_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_sort:{next_sort}",
        )

        self.assertEqual(sort_result.status_text, "Construct type updated.")
        self.assertEqual(
            subject_draft_model_construct_sort_select_spec(scenario=scenario, progress=progress).value,
            next_sort,
        )

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="accept_selected_draft_construct_candidate",
        )

        sort_spec_after_accept = subject_draft_model_construct_sort_select_spec(scenario=scenario, progress=progress)
        lane_spec = subject_draft_model_construct_lane_select_spec(scenario=scenario, progress=progress)
        policy_spec = subject_draft_model_policy_profile_select_spec(scenario=scenario, progress=progress)

        self.assertTrue(sort_spec_after_accept.enabled)
        self.assertTrue(lane_spec.enabled)
        self.assertTrue(policy_spec.enabled)

        accepted_next_sort = next(
            value for _label, value in sort_spec_after_accept.options if value != sort_spec_after_accept.value
        )
        accepted_sort_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_sort:{accepted_next_sort}",
        )
        self.assertTrue(accepted_sort_result.status_text.startswith("Construct type updated."))
        self.assertEqual(
            subject_draft_model_construct_sort_select_spec(scenario=scenario, progress=progress).value,
            accepted_next_sort,
        )
        accepted_lane_spec = subject_draft_model_construct_lane_select_spec(scenario=scenario, progress=progress)
        self.assertTrue(accepted_lane_spec.enabled)
        self.assertIn(
            accepted_lane_spec.value,
            tuple(value for _label, value in accepted_lane_spec.options),
        )
        next_lane = next(value for _label, value in accepted_lane_spec.options if value != accepted_lane_spec.value)
        lane_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_lane:{next_lane}",
        )
        policy_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_decision_policy_profile:balanced",
        )
        self.assertIn("Construct role updated.", lane_result.status_text)
        self.assertEqual(
            subject_draft_model_construct_lane_select_spec(scenario=scenario, progress=progress).value,
            next_lane,
        )
        self.assertTrue(policy_result.status_text.startswith("Decision policy updated."))
        self.assertEqual(load_decision_policy_profile(self.root, subject_id).profile_kind, "balanced")

    def test_subject_workflow_draft_model_lens_switch_preserves_selected_construct(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )
        selected_before = progress.draft_selected_construct_candidate_id

        frame_view = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_frame_view",
        )
        frame_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        frame_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        frame_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        frame_workspace = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")

        self.assertEqual(frame_view.status_text, "Draft Model is now showing Frame.")
        self.assertEqual(progress.draft_selected_construct_candidate_id, selected_before)
        self.assertRegex(subject_draft_tree_title(scenario=scenario, progress=progress), r"^Case Objects \(\d+\)$")
        self.assertEqual(subject_draft_model_main_title(scenario=scenario, progress=progress), "Case Frame")
        self.assertNotIn("Active lens:", frame_tree)
        self.assertIn("Context | Actors | Objectives", frame_main)
        self.assertIn("Inspector", frame_detail)
        self.assertIn("Status Snapshot", frame_detail)
        self.assertIn("recommendation status:", frame_main)
        self.assertIn("lens: Frame", frame_workspace)

        explore_view = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_explore_view",
        )
        explore_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        explore_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        explore_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        explore_workspace = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")

        self.assertEqual(explore_view.status_text, "Draft Model is now showing Explore.")
        self.assertEqual(progress.draft_selected_construct_candidate_id, selected_before)
        self.assertRegex(subject_draft_tree_title(scenario=scenario, progress=progress), r"^Case Objects \(\d+\)$")
        self.assertEqual(subject_draft_model_main_title(scenario=scenario, progress=progress), "Explore Alternatives")
        self.assertNotIn("Active lens:", explore_tree)
        self.assertIn("Alternatives | Compare | Rationale", explore_main)
        self.assertIn("Inspector", explore_detail)
        self.assertIn("Status Snapshot", explore_detail)
        self.assertIn("open issues:", explore_main)
        self.assertIn("lens: Explore", explore_workspace)

    def test_subject_workflow_draft_model_guides_lane_and_relation_binding_before_analysis(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        itemized_items = list_itemized_subject_items(self.root, subject_id)
        source_ids = tuple(item.itemized_item_id for item in itemized_items)
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="state",
                    canonical_label="Current State",
                    disambiguator="current",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="state",
                canonical_label="Current State",
                summary="Current governed state.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                relation_hints={"state_polarity": "current"},
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[1],
                    sort_kind="state",
                    canonical_label="Target State",
                    disambiguator="target",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[1],
                sort_kind="state",
                canonical_label="Target State",
                summary="Target governed state.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                relation_hints={"state_polarity": "target"},
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="capability",
                    canonical_label="Decision Support Capability",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="capability",
                canonical_label="Decision Support Capability",
                summary="Capability candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="actor",
                    canonical_label="Operations Team",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="actor",
                canonical_label="Operations Team",
                summary="Actor candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="transition",
                    canonical_label="Move To Target",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="transition",
                canonical_label="Move To Target",
                summary="Transition candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="decision",
                    canonical_label="Choose The Transition",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="decision",
                canonical_label="Choose The Transition",
                summary="Decision candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[1],
                    sort_kind="objective",
                    canonical_label="Reach Target",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[1],
                sort_kind="objective",
                canonical_label="Reach Target",
                summary="Objective candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
        )
        persist_transformation_construct_candidates(self.root, subject_id, candidates)
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        for candidate in candidates:
            progress.draft_selected_construct_candidate_id = candidate.construct_candidate_id
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="accept_selected_draft_construct_candidate",
            )

        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Inspect the next missing relation", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="focus_next_missing_draft_model_relation",
        )
        progress.draft_selected_construct_candidate_id = candidates[4].construct_candidate_id
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Bind the transition source state", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_transition_source",
        )
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Bind the transition target state", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_transition_target",
        )
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Bind the changed capability for this transition", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_transition_changed_capability",
        )
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        self.assertIn("source state: Current State", draft_detail)
        self.assertIn("target state: Target State", draft_detail)
        self.assertIn("changed capabilities (1): Decision Support Capability", draft_detail)

        progress.draft_selected_construct_candidate_id = candidates[5].construct_candidate_id
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Select the first transition for this decision", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_selected_transition",
        )
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Assign the actor for this decision", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_assigned_actor",
        )
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Run decision analysis", current_step)
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        self.assertIn("selected transitions (1): Move To Target", draft_detail)
        self.assertIn("assigned actors (1): Operations Team", draft_detail)

        analyze = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="analyze_decision_frame",
        )
        receipts = list_decision_analysis_receipts(self.root, subject_id)
        self.assertIn("Decision analysis completed.", analyze.status_text)
        self.assertEqual(receipts[-1].admissible_transition_ids, ("Move To Target",))
        self.assertEqual(receipts[-1].valid_decision_ids, ("Choose The Transition",))
        self.assertEqual(receipts[-1].executable_decision_ids, ("Choose The Transition",))
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_explore_view",
        )
        explore_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        self.assertIn("evaluated paths:", explore_main)
        self.assertIn("Current State --Move To Target--> Target State", explore_main)

    def test_subject_workflow_draft_model_capability_relations_bind_dependencies_and_boundaries(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        itemized_items = list_itemized_subject_items(self.root, subject_id)
        source_ids = tuple(item.itemized_item_id for item in itemized_items[:3])
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="capability",
                    canonical_label="Decision Support Capability",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="capability",
                canonical_label="Decision Support Capability",
                summary="Capability candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[1],
                    sort_kind="dependency",
                    canonical_label="Carrier Uptime",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[1],
                sort_kind="dependency",
                canonical_label="Carrier Uptime",
                summary="Dependency candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="boundary",
                    canonical_label="Carrier Boundary",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="boundary",
                canonical_label="Carrier Boundary",
                summary="Boundary candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
        )
        persist_transformation_construct_candidates(self.root, subject_id, candidates)
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        for candidate in candidates:
            progress.draft_selected_construct_candidate_id = candidate.construct_candidate_id
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="accept_selected_draft_construct_candidate",
            )

        progress.draft_selected_construct_candidate_id = candidates[0].construct_candidate_id
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Link the first dependency for this capability", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_capability_dependency",
        )
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        self.assertIn("Link the first boundary for this capability", current_step)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="bind_selected_draft_construct_capability_boundary",
        )
        draft_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        self.assertIn("Capability dependencies: 1", draft_main)
        self.assertIn("Capability boundaries: 1", draft_main)
        self.assertIn("required dependencies (1): Carrier Uptime", draft_detail)
        self.assertIn("crossed boundaries (1): Carrier Boundary", draft_detail)

    def test_subject_workflow_draft_model_relation_selection_specs_and_direct_set_actions_track_selected_construct(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        itemized_items = list_itemized_subject_items(self.root, subject_id)
        source_ids = tuple(item.itemized_item_id for item in itemized_items)
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="state",
                    canonical_label="Current State",
                    disambiguator="current",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="state",
                canonical_label="Current State",
                summary="Current state.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                relation_hints={"state_polarity": "current"},
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[1],
                    sort_kind="state",
                    canonical_label="Target State",
                    disambiguator="target",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[1],
                sort_kind="state",
                canonical_label="Target State",
                summary="Target state.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                relation_hints={"state_polarity": "target"},
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="capability",
                    canonical_label="Decision Support Capability",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="capability",
                canonical_label="Decision Support Capability",
                summary="Capability candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[1],
                    sort_kind="dependency",
                    canonical_label="Carrier Uptime",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[1],
                sort_kind="dependency",
                canonical_label="Carrier Uptime",
                summary="Dependency candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="boundary",
                    canonical_label="Carrier Boundary",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="boundary",
                canonical_label="Carrier Boundary",
                summary="Boundary candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[2],
                    sort_kind="transition",
                    canonical_label="Move To Target",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[2],
                sort_kind="transition",
                canonical_label="Move To Target",
                summary="Transition candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="decision",
                    canonical_label="Choose The Transition",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="decision",
                canonical_label="Choose The Transition",
                summary="Decision candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=source_ids[0],
                    sort_kind="actor",
                    canonical_label="Operations Team",
                ),
                subject_id=subject_id,
                itemized_item_id=source_ids[0],
                sort_kind="actor",
                canonical_label="Operations Team",
                summary="Actor candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="candidate",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
        )
        persist_transformation_construct_candidates(self.root, subject_id, candidates)
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )
        for candidate in candidates:
            progress.draft_selected_construct_candidate_id = candidate.construct_candidate_id
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="accept_selected_draft_construct_candidate",
            )

        progress.draft_selected_construct_candidate_id = candidates[2].construct_candidate_id
        capability_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertEqual(tuple(spec.label for spec in capability_specs), ("Dependencies", "Boundaries"))
        dependency_id = capability_specs[0].options[0][1]
        boundary_id = capability_specs[1].options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_capability_dependencies:{dependency_id}",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_capability_boundaries:{boundary_id}",
        )
        capability_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertTrue(capability_specs[0].options[0][2])
        self.assertTrue(capability_specs[1].options[0][2])

        progress.draft_selected_construct_candidate_id = candidates[5].construct_candidate_id
        transition_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertEqual(tuple(spec.label for spec in transition_specs), ("Changed Capabilities",))
        transition_source_spec = subject_draft_model_transition_source_select_spec(scenario=scenario, progress=progress)
        transition_target_spec = subject_draft_model_transition_target_select_spec(scenario=scenario, progress=progress)
        self.assertEqual(transition_source_spec.label, "Source State")
        self.assertEqual(transition_target_spec.label, "Target State")
        self.assertEqual(
            tuple(label for label, _value in transition_source_spec.options),
            ("Current State", "Target State"),
        )
        self.assertFalse(transition_target_spec.enabled)
        source_state_id = transition_source_spec.options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_transition_source:{source_state_id}",
        )
        transition_target_spec = subject_draft_model_transition_target_select_spec(scenario=scenario, progress=progress)
        self.assertTrue(transition_target_spec.enabled)
        self.assertEqual(tuple(label for label, _value in transition_target_spec.options), ("Target State",))
        target_state_id = transition_target_spec.options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_transition_target:{target_state_id}",
        )
        transition_source_spec = subject_draft_model_transition_source_select_spec(scenario=scenario, progress=progress)
        transition_target_spec = subject_draft_model_transition_target_select_spec(scenario=scenario, progress=progress)
        self.assertEqual(transition_source_spec.value, source_state_id)
        self.assertEqual(transition_target_spec.value, target_state_id)
        capability_id = transition_specs[0].options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_transition_changed_capabilities:{capability_id}",
        )
        transition_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertTrue(transition_specs[0].options[0][2])
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        self.assertIn("source state: Current State", draft_detail)
        self.assertIn("target state: Target State", draft_detail)

        progress.draft_selected_construct_candidate_id = candidates[6].construct_candidate_id
        decision_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertEqual(tuple(spec.label for spec in decision_specs), ("Selected Transitions", "Assigned Actors"))
        self.assertFalse(decision_specs[1].enabled)
        transition_id = decision_specs[0].options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_selected_transitions:{transition_id}",
        )
        decision_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertTrue(decision_specs[0].options[0][2])
        self.assertTrue(decision_specs[1].enabled)
        actor_id = decision_specs[1].options[0][1]
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_draft_construct_assigned_actors:{actor_id}",
        )
        decision_specs = subject_draft_model_relation_selection_list_specs(scenario=scenario, progress=progress)
        self.assertTrue(decision_specs[1].options[0][2])
        draft_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        self.assertIn("selected transitions (1): Move To Target", draft_detail)
        self.assertIn("assigned actors (1): Operations Team", draft_detail)

    def test_subject_workflow_draft_orientation_cycles_selected_review_item(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_itemized_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        refreshed = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        action_specs = subject_action_specs(scenario=refreshed, progress=progress, phase="draft")
        self.assertEqual(action_specs[0].label, "Semantic (Definition)")
        self.assertEqual(action_specs[1].label, "Render (Paragraph)")
        self.assertEqual(action_specs[2].label, "Evidence (Inline Handles)")
        self.assertEqual(action_specs[3].label, "Transform (Keep)")

        apply_subject_action(
            root_path=self.root,
            scenario=refreshed,
            progress=progress,
            action_key="cycle_selected_draft_review_semantic_kind",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=refreshed,
            progress=progress,
            action_key="cycle_selected_draft_review_render_kind",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=refreshed,
            progress=progress,
            action_key="cycle_selected_draft_review_evidence_mode",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=refreshed,
            progress=progress,
            action_key="cycle_selected_draft_review_transform_mode",
        )

        review_items = list_review_items(self.root, subject_id)
        selected_review_item = next(
            item
            for item in review_items
            if item.source_itemized_item_id == selected_itemized_item_id
        )
        self.assertEqual(selected_review_item.semantic_kind, "metric")
        self.assertEqual(selected_review_item.render_kind, "equation_block")
        self.assertEqual(selected_review_item.evidence_mode, "source_basis_panel")
        self.assertEqual(selected_review_item.transform_mode, "split")

        workspace_text = render_subject_workspace(scenario=refreshed, progress=progress, phase="draft")
        self.assertIn("Selected Item", workspace_text)
        self.assertIn("- label: Alpha", workspace_text)
        self.assertIn("- semantic kind: Metric", workspace_text)
        self.assertIn("- render kind: Equation Block", workspace_text)
        self.assertIn("- evidence mode: Source Basis Panel", workspace_text)
        self.assertIn("- transform mode: Split", workspace_text)
        self.assertIn("- selection source: draft selection", workspace_text)

    def test_subject_workflow_move_draft_review_cursor_and_reorder_selected_review_item(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        alpha_source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )
        beta_source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Beta",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        moved_selection = move_draft_review_cursor(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=-1,
        )
        self.assertIsNotNone(moved_selection)
        self.assertEqual(progress.itemize_selected_item_id, moved_selection.source_itemized_item_id)
        selected_source_item_id = moved_selection.source_itemized_item_id

        before_positions = {
            item.source_itemized_item_id: index
            for index, item in enumerate(list_review_items(self.root, subject_id))
        }
        move_earlier = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="move_selected_draft_review_item_earlier",
        )
        after_positions = {
            item.source_itemized_item_id: index
            for index, item in enumerate(list_review_items(self.root, subject_id))
        }
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")

        self.assertEqual(move_earlier.status_text, "Draft item moved earlier.")
        self.assertEqual(progress.itemize_selected_item_id, selected_source_item_id)
        self.assertLess(after_positions[selected_source_item_id], before_positions[selected_source_item_id])
        self.assertIn(alpha_source_item_id, before_positions)
        self.assertIn("Draft Item Order", workspace_text)
        self.assertIn("- label:", workspace_text)

    def test_subject_workflow_persist_subject_progress_preserves_itemize_and_draft_selection(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        beta_source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Beta",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        persisted_review_item = next(
            item for item in list_review_items(self.root, subject_id) if item.source_itemized_item_id == beta_source_item_id
        )
        persist_subject_progress(self.root, subject_id, progress)
        reloaded = load_subject_progress(self.root, subject_id)

        self.assertEqual(reloaded.itemize_selected_item_id, beta_source_item_id)
        self.assertEqual(reloaded.draft_selected_review_item_id, persisted_review_item.review_item_id)

    def test_subject_workflow_load_subject_progress_reconciles_draft_model_cursor_from_selected_construct(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        itemized_items = list_itemized_subject_items(self.root, subject_id)
        self.assertGreaterEqual(len(itemized_items), 2)
        progress.itemize_selected_item_id = itemized_items[0].itemized_item_id
        custom_candidates = (
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=itemized_items[0].itemized_item_id,
                    sort_kind="actor",
                    canonical_label="Operations Team",
                ),
                subject_id=subject_id,
                itemized_item_id=itemized_items[0].itemized_item_id,
                sort_kind="actor",
                canonical_label="Operations Team",
                summary="Actor candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="accepted",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
            TransformationConstructCandidate(
                construct_candidate_id=stable_transformation_construct_candidate_id(
                    subject_id=subject_id,
                    itemized_item_id=itemized_items[1].itemized_item_id,
                    sort_kind="transition",
                    canonical_label="Move To Target",
                ),
                subject_id=subject_id,
                itemized_item_id=itemized_items[1].itemized_item_id,
                sort_kind="transition",
                canonical_label="Move To Target",
                summary="Transition candidate.",
                source_refs=("notes/controls.md",),
                confidence=0.8,
                status="accepted",
                created_at_epoch_ms=101,
                updated_at_epoch_ms=101,
            ),
        )
        persist_transformation_construct_candidates(self.root, subject_id, custom_candidates)
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        candidates = _subject_transformation_construct_candidates(self.root, scenario, include_rejected=True)
        self.assertGreaterEqual(len(candidates), 2)
        target_candidate = candidates[-1]
        progress.draft_selected_construct_candidate_id = target_candidate.construct_candidate_id
        progress.draft_model_cursor = 0

        persist_subject_progress(self.root, subject_id, progress)
        reloaded = load_subject_progress(self.root, subject_id)
        expected_index = next(
            index
            for index, candidate in enumerate(candidates)
            if collapse_ws(candidate.construct_candidate_id) == collapse_ws(target_candidate.construct_candidate_id)
        )

        self.assertEqual(reloaded.draft_selected_construct_candidate_id, target_candidate.construct_candidate_id)
        self.assertEqual(reloaded.draft_model_cursor, expected_index)
        self.assertEqual(reloaded.itemize_selected_item_id, target_candidate.itemized_item_id)

    def test_subject_workflow_refresh_review_composition_preserves_existing_manual_order(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        alpha_source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )
        beta_source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Beta",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        for _ in range(4):
            ordered_positions = {
                item.source_itemized_item_id: index
                for index, item in enumerate(list_review_items(self.root, subject_id))
            }
            if ordered_positions.get(beta_source_item_id, 999) < ordered_positions.get(alpha_source_item_id, -1):
                break
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="move_selected_draft_review_item_earlier",
            )

        reordered_positions = {
            item.source_itemized_item_id: index
            for index, item in enumerate(list_review_items(self.root, subject_id))
        }
        self.assertLess(reordered_positions[beta_source_item_id], reordered_positions[alpha_source_item_id])

        refresh = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        refreshed_positions = {
            item.source_itemized_item_id: index
            for index, item in enumerate(list_review_items(self.root, subject_id))
        }

        self.assertEqual(refresh.status_text, "Draft composition refreshed.")
        self.assertLess(refreshed_positions[beta_source_item_id], refreshed_positions[alpha_source_item_id])

    def test_subject_workflow_draft_split_merge_and_promote_child_review_items(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Controls", item_kind="entity")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        split = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="split_selected_draft_review_item",
        )
        split_items = list_review_items(self.root, subject_id)
        split_children = [
            item
            for item in split_items
            if item.metadata.get("origin") == "review_split"
        ]
        self.assertEqual(split.status_text, "Draft item split into child review items.")
        self.assertEqual({item.metadata.get("canonical_label") for item in split_children}, {"Access Controls", "Audit Controls"})

        merge = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="merge_selected_draft_review_item_with_next_sibling",
        )
        merged_items = list_review_items(self.root, subject_id)
        merged_item = next(item for item in merged_items if item.metadata.get("origin") == "review_merge")
        self.assertEqual(merge.status_text, "Draft sibling items merged.")
        self.assertEqual(progress.draft_selected_review_item_id, merged_item.review_item_id)

        promote = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="promote_selected_draft_review_item_to_root",
        )
        promoted_items = list_review_items(self.root, subject_id)
        promoted_item = next(item for item in promoted_items if item.review_item_id == merged_item.review_item_id)
        transform_receipts = list_review_transform_receipts(self.root, subject_id)
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")
        gather_workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="review")

        self.assertEqual(promote.status_text, "Child review item promoted to root.")
        self.assertEqual(promoted_item.parent_review_item_id, "")
        self.assertEqual(tuple(receipt.transform_kind for receipt in transform_receipts), ("split", "merge", "promote"))
        self.assertIn("Decision Analysis", workspace_text)
        self.assertIn("parent review item: <root>", workspace_text)
        self.assertIn("Review Transform Receipts", workspace_text)
        self.assertIn("- receipt count: 3", workspace_text)
        self.assertIn("Review Transform Receipts", gather_workspace_text)
        self.assertIn("- receipt count: 3", gather_workspace_text)

    def test_subject_workflow_decision_frame_create_add_and_analyze(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Alpha", item_kind="entity")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_selected_itemized_item_decision_role",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        create_frame = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_decision_frame_from_selected_draft_item",
        )
        add_item = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="add_selected_draft_review_item_to_decision_frame",
        )
        analyze = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="analyze_decision_frame",
        )

        frame = load_decision_frame(self.root, subject_id)
        decision_items = list_decision_review_items(self.root, subject_id)
        receipts = list_decision_analysis_receipts(self.root, subject_id)
        policy_profile = load_decision_policy_profile(self.root, subject_id)
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="review")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        review_current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="review")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        self.assertEqual(create_frame.status_text, "Decision analysis started. Report plan updated.")
        self.assertEqual(add_item.status_text, "Draft item included in decision analysis. Report plan updated.")
        self.assertEqual(analyze.status_text, "Decision analysis completed. Report plan updated.")
        self.assertTrue(frame.decision_frame_id)
        self.assertGreater(len(decision_items), 1)
        self.assertTrue(any(item.decision_role == "actor" for item in decision_items))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(policy_profile.profile_kind, "conservative")
        self.assertTrue(bool(scenario.composition_id))
        self.assertIn("Decision Analysis", workspace_text)
        self.assertIn("Run decision analysis", review_current_step)
        self.assertIn("attached decision analysis is blocked", review_current_step)
        self.assertIn("Draft", review_current_step)

    def test_subject_workflow_cycles_decision_policy_profile_and_surfaces_recommendation_state(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Alpha", item_kind="entity")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_selected_itemized_item_decision_role",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_decision_frame_from_selected_draft_item",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="add_selected_draft_review_item_to_decision_frame",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="analyze_decision_frame",
        )

        cycle = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_decision_policy_profile",
        )

        receipts = list_decision_analysis_receipts(self.root, subject_id)
        policy_profile = load_decision_policy_profile(self.root, subject_id)
        draft_workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")
        draft_actions = subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        draft_action_labels = [action.label for action in draft_actions]

        self.assertEqual(cycle.status_text, "Decision analysis rerun under the selected policy. Report plan updated.")
        self.assertEqual(policy_profile.profile_kind, "balanced")
        self.assertGreaterEqual(len(receipts), 2)
        self.assertEqual(receipts[-1].metadata.get("policy_profile_kind"), "balanced")
        self.assertIn("policy: Balanced", draft_workspace_text)
        self.assertIn("recommendation status:", draft_workspace_text)
        self.assertIn("Run Decision Analysis", draft_action_labels)
        self.assertIn("Open Model", draft_action_labels)

    def test_subject_workflow_draft_prefers_dst_decision_frame_creation_for_matching_source_fixture(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        before_actions = subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        before_labels = [action.label for action in before_actions]

        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        captured: dict[str, object] = {}

        def _fake_run_live_dst_pipeline(dst_fixture, **kwargs):
            captured["fixture_id"] = dst_fixture.fixture_id
            captured["subject_id"] = kwargs.get("subject_id")
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

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=_fake_run_live_dst_pipeline,
        ):
            create_frame = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )

        frame = load_decision_frame(self.root, subject_id)
        decision_items = list_decision_review_items(self.root, subject_id)
        draft_workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="draft")
        after_actions = subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        after_labels = [action.label for action in after_actions]

        self.assertIn("Start Decision Analysis", before_labels)
        self.assertIn("Open Model", before_labels)
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        self.assertEqual(create_frame.status_text, "Decision analysis started from DST discovery. Report plan updated.")
        self.assertEqual(captured["fixture_id"], fixture.fixture_id)
        self.assertEqual(captured["subject_id"], subject_id)
        self.assertTrue(frame.decision_frame_id)
        self.assertTrue(frame.metadata.get("dst_seeded"))
        self.assertEqual(frame.metadata.get("dst_fixture_id"), fixture.fixture_id)
        self.assertGreater(len(decision_items), 5)
        self.assertTrue(bool(scenario.composition_id))
        self.assertIn("source: DST governed discovery", draft_workspace_text)
        self.assertIn("Run Decision Analysis", after_labels)
        self.assertIn("Open Model", after_labels)
        self.assertNotIn("Include In Decision Analysis", after_labels)
        self.assertEqual(
            next(action.kind for action in before_actions if action.label == "Open Model"),
            "subject_action",
        )
        self.assertEqual(
            next(action.kind for action in after_actions if action.label == "Open Model"),
            "subject_action",
        )

    def test_subject_workflow_current_step_same_tab_nav_is_normalized_to_button(self) -> None:
        action = _normalize_current_step_gate_action_for_phase(
            current_phase="draft",
            action=_gate_subject_nav_action("open_draft_model_view", "Open Model"),
        )
        self.assertEqual(action.kind, "subject_action")
        self.assertEqual(action.key, "open_draft_model_view")
        self.assertEqual(action.label, "Open Model")

    def test_subject_workflow_current_step_rejects_same_tab_phase_nav(self) -> None:
        with self.assertRaises(AssertionError):
            _normalize_current_step_gate_action_for_phase(
                current_phase="draft",
                action=_gate_phase_action("draft", "Draft"),
            )

    def test_subject_workflow_draft_decision_included_switch_tracks_selected_item_and_toggle_removes_decision_item(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_decision_frame_from_selected_draft_item",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        before_spec = subject_draft_decision_included_switch_spec(scenario=scenario, progress=progress)
        before_tree = render_subject_draft_tree(scenario=scenario, progress=progress)

        self.assertTrue(before_spec.enabled)
        self.assertTrue(before_spec.value)
        self.assertIn("[d]", before_tree)

        remove_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_draft_review_item_in_decision_frame",
        )

        after_spec = subject_draft_decision_included_switch_spec(scenario=scenario, progress=progress)
        after_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        after_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        frame = load_decision_frame(self.root, subject_id)
        decision_items = list_decision_review_items(self.root, subject_id)
        latest_receipts = list_decision_analysis_receipts(self.root, subject_id)
        selected_line = next((line for line in after_tree.splitlines() if line.startswith(">")), "")

        self.assertIn("removed from decision analysis", remove_result.status_text.casefold())
        self.assertFalse(after_spec.value)
        self.assertIn("selected in decision frame: no", collapse_ws(after_detail))
        self.assertIn("[x][ ]", selected_line)
        self.assertGreater(len(decision_items), 0)
        self.assertEqual(
            frame.metadata.get("draft_decision_selection_mode"),
            "explicit",
        )
        self.assertNotIn("latest_analysis_receipt_id", frame.metadata)
        self.assertEqual(len(latest_receipts), 0)

    def test_subject_workflow_draft_decision_defaults_to_included_until_first_manual_toggle(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        before_spec = subject_draft_decision_included_switch_spec(scenario=scenario, progress=progress)
        before_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        before_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        before_frame = load_decision_frame(self.root, subject_id)

        self.assertTrue(before_spec.enabled)
        self.assertTrue(before_spec.value)
        self.assertIn("[x][d]", next((line for line in before_tree.splitlines() if line.startswith(">")), ""))
        self.assertIn("selected in decision frame: yes", collapse_ws(before_detail))
        self.assertFalse(before_frame.decision_frame_id)

        toggle_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_draft_review_item_in_decision_frame",
        )

        after_spec = subject_draft_decision_included_switch_spec(scenario=scenario, progress=progress)
        after_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        after_detail = render_subject_draft_detail(scenario=scenario, progress=progress)
        after_frame = load_decision_frame(self.root, subject_id)
        after_items = list_decision_review_items(self.root, subject_id)

        self.assertIn("removed from decision analysis", toggle_result.status_text.casefold())
        self.assertFalse(after_spec.value)
        self.assertIn("[x][ ]", next((line for line in after_tree.splitlines() if line.startswith(">")), ""))
        self.assertIn("selected in decision frame: no", collapse_ws(after_detail))
        self.assertTrue(after_frame.decision_frame_id)
        self.assertEqual(after_frame.metadata.get("draft_decision_selection_mode"), "explicit")
        self.assertGreater(len(after_items), 0)

    def test_persist_transformation_construct_candidates_removes_stale_files_missing_from_new_set(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        first_candidate = TransformationConstructCandidate(
            construct_candidate_id="cand_first",
            subject_id=subject_id,
            itemized_item_id="itm_first",
            sort_kind="actor",
            canonical_label="Alpha",
            summary="Alpha actor.",
            source_refs=("source:controls",),
            confidence=0.8,
            status="candidate",
        )
        stale_candidate = TransformationConstructCandidate(
            construct_candidate_id="cand_stale",
            subject_id=subject_id,
            itemized_item_id="itm_stale",
            sort_kind="objective",
            canonical_label="Itemize Editor Demo",
            summary="Stale generic construct.",
            source_refs=("source:controls",),
            confidence=0.6,
            status="candidate",
        )

        persist_transformation_construct_candidates(self.root, subject_id, (first_candidate, stale_candidate))
        persist_transformation_construct_candidates(self.root, subject_id, (first_candidate,))

        listed = list_transformation_construct_candidates(self.root, subject_id)
        listed_ids = {candidate.construct_candidate_id for candidate in listed}

        self.assertEqual(listed_ids, {"cand_first"})

    def test_subject_workflow_refresh_dst_decision_analysis_preserves_curated_constructs_across_label_churn(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        discovery = discovery_result_from_fixture(fixture)
        baseline_case = normalized_case_from_fixture(fixture, discovery)
        target_objective = baseline_case.objectives[0]
        refreshed_label = f"{target_objective.name} (refreshed)"
        refreshed_case = replace(
            baseline_case,
            objectives=tuple(
                replace(item, name=refreshed_label)
                if item.id == target_objective.id
                else item
                for item in baseline_case.objectives
            ),
        )

        def _pipeline_for(case):
            return run_dst_pipeline_from_fixture(
                fixture,
                discovery_runner=lambda **_runner_kwargs: discovery.to_dict(),
                normalization_runner=lambda **_runner_kwargs: case.to_dict(),
                subject_id=subject_id,
                build_epoch_ms=int(time.time() * 1000),
            )

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=[_pipeline_for(baseline_case), _pipeline_for(refreshed_case)],
        ):
            start = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
            before_frame = load_decision_frame(self.root, subject_id)
            before_items = list_decision_review_items(self.root, subject_id)
            before_candidates = list_transformation_construct_candidates(self.root, subject_id)
            target_candidate_before = next(
                candidate
                for candidate in before_candidates
                if collapse_ws(str(candidate.relation_hints.get("normalized_objective_id", ""))) == target_objective.id
            )
            persist_transformation_construct_candidates(
                self.root,
                subject_id,
                tuple(
                    replace(candidate, notes="curated objective note")
                    if collapse_ws(candidate.construct_candidate_id) == collapse_ws(target_candidate_before.construct_candidate_id)
                    else candidate
                    for candidate in before_candidates
                ),
            )
            refresh = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="refresh_dst_decision_analysis",
            )

        after_frame = load_decision_frame(self.root, subject_id)
        after_items = list_decision_review_items(self.root, subject_id)
        after_candidates = list_transformation_construct_candidates(self.root, subject_id)
        target_candidate_after = next(
            candidate
            for candidate in after_candidates
            if collapse_ws(str(candidate.relation_hints.get("normalized_objective_id", ""))) == target_objective.id
        )
        target_item_before = next(
            item for item in before_items
            if collapse_ws(str(item.metadata.get("objective_id", ""))) == target_objective.id
        )
        target_item_after = next(
            item for item in after_items
            if collapse_ws(str(item.metadata.get("objective_id", ""))) == target_objective.id
        )

        self.assertEqual(start.status_text, "Decision analysis started from DST discovery. Report plan updated.")
        self.assertEqual(refresh.status_text, "DST decision analysis refreshed. Report plan updated.")
        self.assertEqual(after_frame.decision_frame_id, before_frame.decision_frame_id)
        self.assertEqual(target_item_after.decision_review_item_id, target_item_before.decision_review_item_id)
        self.assertEqual(target_candidate_after.construct_candidate_id, target_candidate_before.construct_candidate_id)
        self.assertEqual(target_candidate_after.notes, "curated objective note")
        self.assertEqual(target_candidate_after.canonical_label, target_candidate_before.canonical_label)
        self.assertEqual(
            collapse_ws(str(target_candidate_after.relation_hints.get("latest_generated_canonical_label", ""))),
            refreshed_label,
        )

    def test_subject_workflow_requires_dst_refresh_when_same_subject_later_matches_dst_fixture(self) -> None:
        ensure_application_controller_runtime()
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise same-subject DST refresh boundary.",
            allow_direct_llm_decomposition=True,
        )
        subject_id = canonical_learning_subject_id("Smart City Travel")

        def _scenario():
            return next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        progress = load_subject_progress(self.root, subject_id)
        host_actions = RuntimeSubjectWorkflowHostActions()
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
            "create_decision_frame_from_selected_draft_item",
            "analyze_decision_frame",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=_scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        initial_decision_state = _decision_review_state(self.root, _scenario())
        initial_frame = initial_decision_state["frame"]
        self.assertFalse(bool(initial_frame.metadata.get("dst_seeded")))
        self.assertEqual(initial_decision_state["recommendation_status"], "blocked")

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=_scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        refreshed_scenario = _scenario()
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
        progress.draft_selected_review_item_id = later_nonincluded_review_item.review_item_id
        current_step = render_subject_current_step(
            scenario=refreshed_scenario,
            progress=progress,
            phase="draft",
        )
        action_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=refreshed_scenario,
                progress=progress,
                phase="draft",
            )
        ]
        self.assertIn("Refresh the DST-backed decision analysis", current_step)
        self.assertIn("Refresh DST Analysis", action_labels)
        self.assertNotIn("Review: Hand To Review", action_labels)

        rerun_result = apply_subject_action(
            root_path=self.root,
            scenario=refreshed_scenario,
            progress=progress,
            action_key="cycle_decision_policy_profile",
            host_actions=host_actions,
        )
        self.assertEqual(rerun_result.status_text, "Decision analysis rerun under the selected policy. Report plan updated.")

        refreshed_decision_state = _decision_review_state(self.root, _scenario())
        refreshed_frame = refreshed_decision_state["frame"]
        self.assertTrue(bool(refreshed_frame.metadata.get("dst_seeded")))
        self.assertEqual(refreshed_decision_state["recommendation_status"], "recommendable")
        self.assertGreaterEqual(int(refreshed_decision_state["item_count"]), int(initial_decision_state["item_count"]))

    def test_subject_workflow_weak_prose_review_and_publication_route_back_to_start_decision_analysis(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise weak-prose decision-analysis recovery routing.",
            allow_direct_llm_decomposition=True,
        )
        subject_id = canonical_learning_subject_id("Smart City Travel")

        def _scenario():
            return next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        progress = load_subject_progress(self.root, subject_id)
        host_actions = RuntimeSubjectWorkflowHostActions()
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=_scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        review_step = subject_current_step_view(scenario=_scenario(), progress=progress, phase="review")
        review_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=_scenario(),
                progress=progress,
                phase="review",
            )
        ]
        publication_step = subject_current_step_view(scenario=_scenario(), progress=progress, phase="publication")
        publication_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=_scenario(),
                progress=progress,
                phase="publication",
            )
        ]

        self.assertEqual(review_step.primary_action.label, "Start Decision Analysis")
        self.assertIn("Review cannot create or approve the report plan", review_step.status)
        self.assertIn("Draft: Start Decision Analysis", review_labels)
        self.assertNotIn("Approve For Report", review_labels)

        self.assertEqual(publication_step.primary_action.label, "Start Decision Analysis")
        self.assertIn("Review cannot create or approve the report plan", publication_step.status)
        self.assertIn("Draft: Start Decision Analysis", publication_labels)
        self.assertNotIn("Lock Report Inputs", publication_labels)

    def test_subject_workflow_same_subject_v2_then_v10_review_and_publication_route_back_to_refresh_dst_analysis(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise same-subject DST refresh routing from later phases.",
            allow_direct_llm_decomposition=True,
        )
        subject_id = canonical_learning_subject_id("Smart City Travel")

        def _scenario():
            return next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        progress = load_subject_progress(self.root, subject_id)
        host_actions = RuntimeSubjectWorkflowHostActions()
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
            "create_decision_frame_from_selected_draft_item",
            "analyze_decision_frame",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=_scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=_scenario(),
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        review_step = subject_current_step_view(scenario=_scenario(), progress=progress, phase="review")
        review_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=_scenario(),
                progress=progress,
                phase="review",
            )
        ]
        publication_step = subject_current_step_view(scenario=_scenario(), progress=progress, phase="publication")
        publication_labels = [
            action.label
            for action in subject_current_step_actions(
                scenario=_scenario(),
                progress=progress,
                phase="publication",
            )
        ]

        self.assertEqual(review_step.primary_action.label, "Refresh DST Analysis")
        self.assertIn("Review cannot create or approve the report plan", review_step.status)
        self.assertIn("Draft: Refresh DST Analysis", review_labels)
        self.assertNotIn("Approve For Report", review_labels)

        self.assertEqual(publication_step.primary_action.label, "Refresh DST Analysis")
        self.assertIn("Review cannot create or approve the report plan", publication_step.status)
        self.assertIn("Draft: Refresh DST Analysis", publication_labels)
        self.assertNotIn("Lock Report Inputs", publication_labels)

    def test_subject_workflow_dst_transition_source_select_spec_includes_intermediate_state_bindings(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")

        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        def _fake_run_live_dst_pipeline(dst_fixture, **kwargs):
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

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=_fake_run_live_dst_pipeline,
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="analyze_decision_frame",
            )
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="open_draft_model_view",
            )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        accepted_transition = next(
            candidate
            for candidate in list_transformation_construct_candidates(self.root, subject_id)
            if collapse_ws(candidate.status) == "accepted"
            and collapse_ws(candidate.sort_kind) == "transition"
            and collapse_ws(candidate.canonical_label) == "add compatibility and inspection tools"
        )
        progress.draft_selected_construct_candidate_id = accepted_transition.construct_candidate_id

        source_spec = subject_draft_model_transition_source_select_spec(scenario=scenario, progress=progress)
        target_spec = subject_draft_model_transition_target_select_spec(scenario=scenario, progress=progress)

        self.assertTrue(source_spec.enabled)
        self.assertTrue(target_spec.enabled)
        self.assertIn(
            "improved closed-loop card system",
            tuple(label for label, _value in source_spec.options),
        )
        self.assertIn(source_spec.value, {value for _label, value in source_spec.options})
        self.assertIn(target_spec.value, {value for _label, value in target_spec.options})

    def test_subject_workflow_draft_approved_keeps_open_model_available_for_dst_subjects(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=lambda dst_fixture, **kwargs: run_dst_pipeline_from_fixture(
                dst_fixture,
                discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(dst_fixture).to_dict(),
                normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                    dst_fixture,
                    runner_kwargs["discovery"],
                ).to_dict(),
                subject_id=str(kwargs.get("subject_id", "")),
                build_epoch_ms=int(kwargs.get("build_epoch_ms", 0) or 0),
            ),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="analyze_decision_frame",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        approved_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        approved_labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        ]
        open_model = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )
        model_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")

        self.assertIn("Draft composition is approved", approved_step)
        self.assertIn("Open Model", approved_labels)
        self.assertIn("Refresh DST Analysis", approved_labels)
        self.assertEqual(open_model.status_text, "Moved Draft focus to Model.")
        self.assertNotIn("Draft composition is approved", model_step)
        self.assertTrue(
            ("Decision analysis" in model_step) or ("missing relation" in model_step),
            model_step,
        )

    def test_subject_workflow_built_publication_keeps_open_model_available_for_dst_subjects(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")

        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        def _fake_run_live_dst_pipeline(dst_fixture, **kwargs):
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

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=_fake_run_live_dst_pipeline,
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="analyze_decision_frame",
            )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="approve_review")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="lock_publication")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        build_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="build_report",
        )
        self.assertTrue(build_result.reload_subjects)

        rebuilt = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        publication_specs = subject_action_specs(scenario=rebuilt, progress=progress, phase="publication")

        self.assertEqual(publication_specs[0].label, "Preview report.pdf")
        self.assertEqual(publication_specs[1].label, "Rebuild Report")
        self.assertEqual(publication_specs[2].label, "Open Model")
        self.assertEqual(publication_specs[3].label, "Open Release Folder")

    def test_subject_workflow_review_and_publication_keep_model_actions_available_for_dst_subjects(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=lambda dst_fixture, **kwargs: run_dst_pipeline_from_fixture(
                dst_fixture,
                discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(dst_fixture).to_dict(),
                normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                    dst_fixture,
                    runner_kwargs["discovery"],
                ).to_dict(),
                subject_id=str(kwargs.get("subject_id", "")),
                build_epoch_ms=int(kwargs.get("build_epoch_ms", 0) or 0),
            ),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="analyze_decision_frame",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        review_step = render_subject_current_step(scenario=scenario, progress=progress, phase="review")
        review_labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="review")
        ]

        approve = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        publication_step = render_subject_current_step(scenario=scenario, progress=progress, phase="publication")
        publication_labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="publication")
        ]

        self.assertIn("Approve the report and decision analysis", review_step)
        self.assertIn("Draft: Open Model", review_labels)
        self.assertEqual(approve.status_text, "Review approved for report publication.")
        self.assertIn("attached decision analysis", publication_step)
        self.assertIn("Draft: Open Model", publication_labels)

    def test_subject_workflow_dst_decision_frame_syncs_regional_case_construct_sorts_into_draft_model(self) -> None:
        subject_id = self._persist_regional_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
        )
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=lambda dst_fixture, **kwargs: run_dst_pipeline_from_fixture(
                dst_fixture,
                discovery_runner=lambda **_runner_kwargs: discovery_result_from_fixture(dst_fixture).to_dict(),
                normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                    dst_fixture,
                    runner_kwargs["discovery"],
                ).to_dict(),
                subject_id=str(kwargs.get("subject_id", "")),
                build_epoch_ms=int(kwargs.get("build_epoch_ms", 0) or 0),
            ),
        ):
            result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )

        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        accepted_candidates = tuple(
            candidate for candidate in construct_candidates if collapse_ws(candidate.status) == "accepted"
        )
        draft_tree = render_subject_draft_tree(scenario=scenario, progress=progress)
        draft_main = render_subject_draft_model_main(scenario=scenario, progress=progress)
        frame = load_decision_frame(self.root, subject_id)
        decision_items = list_decision_review_items(self.root, subject_id)

        self.assertIn("Decision analysis started from DST discovery.", result.status_text)
        self.assertGreaterEqual(len(construct_candidates), 20)
        self.assertGreaterEqual(len(accepted_candidates), 20)
        self.assertTrue(any(candidate.sort_kind == "actor" for candidate in accepted_candidates))
        self.assertTrue(any(candidate.sort_kind == "capability" for candidate in accepted_candidates))
        self.assertTrue(any(candidate.sort_kind == "boundary" for candidate in accepted_candidates))
        self.assertTrue(any(collapse_ws(candidate.review_item_id) for candidate in accepted_candidates))
        self.assertNotIn("Objects (", draft_tree)
        self.assertIn("[a] hospitals (Actor -> Actor)", draft_tree)
        self.assertIn("[a] agency-to-telecom boundary (Boundary -> Boundary)", draft_tree)
        self.assertNotIn("more constructs", draft_tree)
        self.assertIn("Accepted decision items:", draft_main)
        self.assertNotIn("Status", draft_tree)
        self.assertTrue(frame.metadata.get("dst_seeded"))
        self.assertGreaterEqual(len(decision_items), 20)

    def test_subject_workflow_plain_report_draft_hides_decision_analysis_until_decision_work_exists(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        ]

        self.assertIn("Finish shaping this report item", current_step)
        self.assertIn("decision analysis: not currently needed for this subject", current_step)
        self.assertIn("Review: Hand To Review", labels)
        self.assertNotIn("Start Decision Analysis", labels)
        self.assertNotIn("Include In Decision Analysis", labels)
        self.assertNotIn("Run Decision Analysis", labels)

    def test_subject_workflow_weak_prose_draft_surfaces_decision_analysis_after_construct_suggestion(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise weak-prose Draft decision entry after construct suggestion.",
            allow_direct_llm_decomposition=True,
        )
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        subject_id = canonical_learning_subject_id("Smart City Travel")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = load_subject_progress(self.root, subject_id)
        host_actions = RuntimeSubjectWorkflowHostActions()

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(EmptyController()),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="generate_itemization",
                host_actions=host_actions,
            )
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=RuntimeError("llm unavailable in test"),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        later_review_item = next(
            item
            for item in reversed(list_review_items(self.root, subject_id))
            if collapse_ws(item.review_item_id) and collapse_ws(item.review_item_id) != collapse_ws(progress.draft_selected_review_item_id)
        )
        progress.draft_selected_review_item_id = later_review_item.review_item_id
        current_step = render_subject_current_step(scenario=scenario, progress=progress, phase="draft")
        labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="draft")
        ]

        self.assertIn("Start decision analysis", current_step)
        self.assertIn("Start Decision Analysis", labels)
        self.assertIn("Open Model", labels)
        self.assertNotIn("Include In Decision Analysis", labels)
        self.assertNotIn("Run Decision Analysis", labels)

    def _select_itemized_candidate(
        self,
        *,
        subject_id: str,
        progress: object,
        label: str,
        item_kind: str,
    ) -> str:
        item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.canonical_label == label and item.item_kind == item_kind
        )
        progress.itemize_selected_item_id = item.itemized_item_id
        return item.itemized_item_id

    def test_subject_workflow_itemize_selection_and_detail_follow_cursor(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        initial_detail = render_subject_itemize_detail(scenario=scenario, progress=progress)
        selected = move_itemize_cursor(self.root, scenario=scenario, progress=progress, delta=1)

        self.assertIsNotNone(selected)
        updated_detail = render_subject_itemize_detail(scenario=scenario, progress=progress)
        self.assertIn("Kind:", initial_detail)
        self.assertNotIn("Current Item", initial_detail)
        self.assertNotIn("Label:", initial_detail)
        self.assertNotEqual(initial_detail, updated_detail)
        self.assertIn(selected.canonical_label, updated_detail)

    def test_subject_workflow_itemize_cursor_clamps_at_list_ends(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        items = list_itemized_subject_items(self.root, subject_id)
        self.assertGreaterEqual(len(items), 2)

        selected_top = move_itemize_cursor(self.root, scenario=scenario, progress=progress, delta=-1)
        self.assertIsNotNone(selected_top)
        self.assertEqual(progress.itemize_cursor, 0)
        self.assertEqual(progress.itemize_selected_item_id, items[0].itemized_item_id)

        for _ in range(len(items) + 3):
            move_itemize_cursor(self.root, scenario=scenario, progress=progress, delta=1)

        self.assertEqual(progress.itemize_cursor, len(items) - 1)
        self.assertEqual(progress.itemize_selected_item_id, items[-1].itemized_item_id)

    def test_subject_workflow_draft_cursor_clamps_at_list_ends(self) -> None:
        self._persist_demo_context()
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        refreshed = default_subject_scenarios(self.root)[0]

        selected_top = move_draft_review_cursor(self.root, scenario=refreshed, progress=progress, delta=-1)
        self.assertIsNotNone(selected_top)
        first_review_item_id = selected_top.review_item_id

        selected_bottom = selected_top
        for _ in range(20):
            selected_bottom = move_draft_review_cursor(self.root, scenario=refreshed, progress=progress, delta=1)

        self.assertIsNotNone(selected_bottom)
        last_review_item_id = selected_bottom.review_item_id
        self.assertNotEqual(first_review_item_id, last_review_item_id)

        selected_still_bottom = move_draft_review_cursor(self.root, scenario=refreshed, progress=progress, delta=1)
        self.assertIsNotNone(selected_still_bottom)
        self.assertEqual(selected_still_bottom.review_item_id, last_review_item_id)

    def test_subject_workflow_report_scope_cursor_clamps_at_list_ends(self) -> None:
        subject_id = self._persist_report_scope_reorder_context(subject_id="scope-clamp-demo")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        selected_top = move_report_scope_cursor(self.root, scenario=scenario, progress=progress, delta=-1)
        self.assertIsNotNone(selected_top)
        self.assertEqual(progress.report_scope_cursor, 0)

        selected_bottom = selected_top
        for _ in range(20):
            selected_bottom = move_report_scope_cursor(self.root, scenario=scenario, progress=progress, delta=1)

        self.assertIsNotNone(selected_bottom)
        bottom_index = int(progress.report_scope_cursor)
        selected_still_bottom = move_report_scope_cursor(self.root, scenario=scenario, progress=progress, delta=1)
        self.assertIsNotNone(selected_still_bottom)
        self.assertEqual(int(progress.report_scope_cursor), bottom_index)
        self.assertEqual(selected_still_bottom.entry_id, selected_bottom.entry_id)

    def test_subject_workflow_itemize_suggest_transformation_constructs_persists_candidates(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        action_labels = [
            action.label
            for action in subject_current_step_actions(scenario=scenario, progress=progress, phase="itemize")
        ]
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=RuntimeError("llm unavailable in test"),
        ):
            suggest = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )

        detail_text = render_subject_itemize_detail(scenario=scenario, progress=progress)
        target_text = render_subject_itemize_target(scenario=scenario, progress=progress)
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="itemize")
        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)

        self.assertIn("Refresh Itemization", action_labels)
        self.assertIn("Suggest DST Constructs", action_labels)
        self.assertEqual(suggest.status_text, "Transformation constructs suggested.")
        self.assertGreater(len(construct_candidates), 0)
        self.assertIn("Transformation Constructs", detail_text)
        self.assertIn(selected_item.canonical_label, detail_text)
        self.assertIn("transformation constructs:", target_text)
        self.assertIn("transformation constructs:", workspace_text)
        self.assertTrue(any(candidate.itemized_item_id == selected_item.itemized_item_id for candidate in construct_candidates))

    def test_subject_workflow_deterministic_suggest_constructs_respects_explicit_objective_role(self) -> None:
        item = ItemizedSubjectItem(
            itemized_item_id="itm_smart_city_objective",
            subject_id="smart-city-travel",
            item_kind="decision_role_candidate",
            canonical_label="the payment system to be easy, fast, trustworthy, and fair",
            summary="Passengers need the payment system to be easy, fast, trustworthy, and fair.",
            source_refs=("source:city-bus-prose-v2",),
            confidence=0.75,
            metadata={"decision_role": "objective"},
        )

        candidates = deterministic_transformation_construct_candidates_from_itemized_item(item)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].sort_kind, "objective")
        self.assertEqual(candidates[0].canonical_label, item.canonical_label)

    def test_subject_workflow_prunes_same_label_live_construct_clones_for_explicit_objective_role(self) -> None:
        item = ItemizedSubjectItem(
            itemized_item_id="itm_smart_city_objective",
            subject_id="smart-city-travel",
            item_kind="decision_role_candidate",
            canonical_label="the payment system to be easy, fast, trustworthy, and fair",
            summary="Passengers need the payment system to be easy, fast, trustworthy, and fair.",
            source_refs=("source:city-bus-prose-v2",),
            confidence=0.75,
            metadata={"decision_role": "objective"},
        )
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id="cand_actor",
                subject_id=item.subject_id,
                itemized_item_id=item.itemized_item_id,
                sort_kind="actor",
                canonical_label=item.canonical_label,
                summary=item.summary,
                source_refs=item.source_refs,
                confidence=0.7,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_decision",
                subject_id=item.subject_id,
                itemized_item_id=item.itemized_item_id,
                sort_kind="decision",
                canonical_label=item.canonical_label,
                summary=item.summary,
                source_refs=item.source_refs,
                confidence=0.7,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_objective",
                subject_id=item.subject_id,
                itemized_item_id=item.itemized_item_id,
                sort_kind="objective",
                canonical_label=item.canonical_label,
                summary=item.summary,
                source_refs=item.source_refs,
                confidence=0.9,
                status="candidate",
            ),
        )

        pruned = _prune_same_label_construct_clones_for_explicit_item_role(item, candidates)

        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0].sort_kind, "objective")

    def test_subject_workflow_prunes_generic_subject_title_construct_clones_when_specific_labels_exist(self) -> None:
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id="cand_title_actor",
                subject_id="smart-city-travel",
                itemized_item_id="itm_title_claim",
                sort_kind="actor",
                canonical_label="Smart City Travel",
                summary="Generic title actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.5,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_title_capability",
                subject_id="smart-city-travel",
                itemized_item_id="itm_title_claim",
                sort_kind="capability",
                canonical_label="Smart City Travel",
                summary="Generic title capability.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.5,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_city_regulator",
                subject_id="smart-city-travel",
                itemized_item_id="itm_city_regulator",
                sort_kind="actor",
                canonical_label="city regulator",
                summary="A real actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.9,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_private_ops",
                subject_id="smart-city-travel",
                itemized_item_id="itm_private_ops",
                sort_kind="actor",
                canonical_label="private bus operators",
                summary="A real actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.9,
                status="candidate",
            ),
        )

        pruned = _prune_same_label_subject_title_construct_clones(
            candidates,
            subject_title="Smart City Travel",
        )

        labels = {candidate.canonical_label for candidate in pruned}
        self.assertNotIn("Smart City Travel", labels)
        self.assertIn("city regulator", labels)
        self.assertIn("private bus operators", labels)

    def test_subject_workflow_prunes_single_generic_subject_title_construct_when_specific_labels_exist(self) -> None:
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id="cand_title_actor",
                subject_id="smart-city-travel",
                itemized_item_id="itm_title_claim",
                sort_kind="actor",
                canonical_label="Smart City Travel",
                summary="Generic title actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.5,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_city_regulator",
                subject_id="smart-city-travel",
                itemized_item_id="itm_city_regulator",
                sort_kind="actor",
                canonical_label="city regulator",
                summary="A real actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.9,
                status="candidate",
            ),
        )

        pruned = _prune_same_label_subject_title_construct_clones(
            candidates,
            subject_title="Smart City Travel",
        )

        labels = {candidate.canonical_label for candidate in pruned}
        self.assertNotIn("Smart City Travel", labels)
        self.assertIn("city regulator", labels)

    def test_subject_workflow_prunes_generic_subject_title_construct_clones_down_to_one_when_only_title_group_exists(self) -> None:
        candidates = (
            TransformationConstructCandidate(
                construct_candidate_id="cand_title_actor",
                subject_id="smart-city-travel",
                itemized_item_id="itm_title_claim",
                sort_kind="actor",
                canonical_label="Smart City Travel",
                summary="Generic title actor.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.5,
                status="candidate",
            ),
            TransformationConstructCandidate(
                construct_candidate_id="cand_title_objective",
                subject_id="smart-city-travel",
                itemized_item_id="itm_title_claim",
                sort_kind="objective",
                canonical_label="Smart City Travel",
                summary="Generic title objective.",
                source_refs=("source:city-bus-prose-v2",),
                confidence=0.8,
                status="candidate",
            ),
        )

        pruned = _prune_same_label_subject_title_construct_clones(
            candidates,
            subject_title="Smart City Travel",
        )

        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0].canonical_label, "Smart City Travel")

    def test_subject_workflow_suggest_constructs_prunes_generic_subject_title_clones_from_case_objects(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise smart city travel DST construct pruning.",
        )
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

A city transit authority wants to modernize fare payment.
At present, most passengers pay using cash or plastic transit cards.
The city now wants to introduce app-based payment and contactless bank-card payment, while keeping the bus network reliable and accessible.

The main parties involved are the transit authority, private bus operators, the payment processor, the city regulator, and passengers.
Each party has a different concern. The transit authority wants a faster and more reliable fare system.
Private bus operators need changes that can be implemented without disrupting daily service.
The payment processor must support secure and dependable transactions.
The regulator must ensure that the system follows legal, privacy, and inclusion requirements.
Passengers need the payment system to be easy, fast, trustworthy, and fair.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel-v2.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Smart City Travel",
                aliases=("Smart City Travel",),
                subject_family="Transit",
                summary="Fare modernization prose with stakeholder list.",
                units=(
                    LearningUnit(
                        unit_id="unit_smart_city_travel",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Smart City Travel",
                        statement="A city transit authority wants to modernize fare payment.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        host_actions = RuntimeSubjectWorkflowHostActions()
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
            host_actions=host_actions,
        )

        items = list_itemized_subject_items(self.root, subject_id)
        claim_item = next(
            item
            for item in items
            if collapse_ws(item.item_kind) == "claim" and collapse_ws(item.canonical_label) == "Smart City Travel"
        )
        city_regulator_item = next(
            item
            for item in items
            if normalize_itemized_decision_role(item.metadata.get("decision_role", "")) == "actor"
            and collapse_ws(item.canonical_label) == "city regulator"
        )

        progress.itemize_selected_item_id = collapse_ws(claim_item.itemized_item_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
            host_actions=host_actions,
        )
        progress.itemize_selected_item_id = collapse_ws(city_regulator_item.itemized_item_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="suggest_transformation_constructs",
            host_actions=host_actions,
        )

        candidates = list_transformation_construct_candidates(self.root, subject_id)
        subject_title_candidates = [
            candidate
            for candidate in candidates
            if collapse_ws(candidate.canonical_label).casefold() == "smart city travel"
        ]
        candidate_pairs = {
            (collapse_ws(candidate.canonical_label), normalize_transformation_construct_sort_kind(candidate.sort_kind))
            for candidate in candidates
        }

        self.assertEqual(subject_title_candidates, [])
        self.assertIn(("city regulator", "actor"), candidate_pairs)

    def test_subject_workflow_suggest_constructs_from_subject_claim_expands_to_weak_prose_role_candidates(self) -> None:
        launch_workstation_session(
            root_path=self.root,
            workspace_path=Path(__file__).resolve().parents[2],
            initial_task="Exercise smart city travel umbrella-claim DST expansion.",
        )
        subject_id = canonical_learning_subject_id("Smart City Travel")
        markdown_text = """
# Smart City Travel

A city transit authority wants to modernize fare payment.
At present, most passengers pay using cash or plastic transit cards.
The city now wants to introduce app-based payment and contactless bank-card payment, while keeping the bus network reliable and accessible.

The main parties involved are the transit authority, private bus operators, the payment processor, the city regulator, and passengers.
Each party has a different concern. The transit authority wants a faster and more reliable fare system.
Private bus operators need changes that can be implemented without disrupting daily service.
The payment processor must support secure and dependable transactions.
The regulator must ensure that the system follows legal, privacy, and inclusion requirements.
Passengers need the payment system to be easy, fast, trustworthy, and fair.
""".strip()
        source = new_learning_source(
            subject_id=subject_id,
            title="Smart City Travel",
            source_ref="/tmp/smart-city-travel-v2.md",
            source_kind="markdown",
            media_type="text/markdown",
            section_count=0,
        )
        persist_learning_source(self.root, source, source_text=markdown_text)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Smart City Travel",
                aliases=("Smart City Travel",),
                subject_family="Transit",
                summary="Fare modernization prose with stakeholder list.",
                units=(
                    LearningUnit(
                        unit_id="unit_smart_city_travel",
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Smart City Travel",
                        statement="A city transit authority wants to modernize fare payment.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        host_actions = RuntimeSubjectWorkflowHostActions()
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
            host_actions=host_actions,
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
            host_actions=host_actions,
        )

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        with patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=_itemization_runtime_provider(EmptyController()),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="generate_itemization",
                host_actions=host_actions,
            )

        claim_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if collapse_ws(item.item_kind) == "claim" and collapse_ws(item.canonical_label) == "Smart City Travel"
        )
        progress.itemize_selected_item_id = collapse_ws(claim_item.itemized_item_id)

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=RuntimeError("llm unavailable in test"),
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
                host_actions=host_actions,
            )

        candidate_pairs = {
            (collapse_ws(candidate.canonical_label), normalize_transformation_construct_sort_kind(candidate.sort_kind))
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

    def test_subject_workflow_itemize_suggest_transformation_constructs_prefers_live_dst_discovery_when_available(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        live_candidate = TransformationConstructCandidate(
            construct_candidate_id=stable_transformation_construct_candidate_id(
                subject_id=subject_id,
                itemized_item_id=selected_item.itemized_item_id,
                sort_kind="objective",
                canonical_label=selected_item.canonical_label,
            ),
            subject_id=subject_id,
            itemized_item_id=selected_item.itemized_item_id,
            sort_kind="objective",
            canonical_label=selected_item.canonical_label,
            summary="Live DST normalization found an objective construct.",
            source_refs=selected_item.source_refs,
            confidence=0.91,
            status="candidate",
            relation_hints={"dst_construct_source": "dst_runtime"},
            created_at_epoch_ms=101,
            updated_at_epoch_ms=101,
        )

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            return_value=type(
                "_FakeConstructDiscoveryResult",
                (),
                {
                    "construct_candidates": (live_candidate,),
                    "orchestration_result": type(
                        "_FakeOrchestrationResult",
                        (),
                        {
                            "discovery_proposal_id": "proposal-discovery",
                            "normalization_proposal_id": "proposal-normalization",
                        },
                    )(),
                },
            )(),
        ) as live_discovery:
            suggest = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )

        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        detail_text = render_subject_itemize_detail(scenario=scenario, progress=progress)

        self.assertTrue(live_discovery.called)
        self.assertEqual(suggest.status_text, "Transformation constructs suggested.")
        self.assertIn("Objective", detail_text)
        self.assertTrue(
            any(
                candidate.sort_kind == "objective"
                and candidate.relation_hints.get("dst_construct_source") == "dst_runtime"
                for candidate in construct_candidates
            )
        )

    def test_subject_workflow_itemize_suggest_transformation_constructs_preserves_curated_candidate_across_label_churn(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        existing_candidate = TransformationConstructCandidate(
            construct_candidate_id=stable_transformation_construct_candidate_id(
                subject_id=subject_id,
                itemized_item_id=selected_item.itemized_item_id,
                sort_kind="objective",
                canonical_label="Original objective",
            ),
            subject_id=subject_id,
            itemized_item_id=selected_item.itemized_item_id,
            sort_kind="objective",
            canonical_label="Original objective",
            summary="Curated objective wording.",
            source_refs=selected_item.source_refs,
            confidence=0.91,
            status="candidate",
            notes="curated construct note",
            relation_hints={
                "normalized_objective_id": "objective-1",
                "dst_construct_source": "dst_runtime",
            },
            created_at_epoch_ms=101,
            updated_at_epoch_ms=101,
        )
        persist_transformation_construct_candidates(self.root, subject_id, (existing_candidate,))

        refreshed_candidate = TransformationConstructCandidate(
            construct_candidate_id=stable_transformation_construct_candidate_id(
                subject_id=subject_id,
                itemized_item_id=selected_item.itemized_item_id,
                sort_kind="objective",
                canonical_label="Original objective (refreshed)",
            ),
            subject_id=subject_id,
            itemized_item_id=selected_item.itemized_item_id,
            sort_kind="objective",
            canonical_label="Original objective (refreshed)",
            summary="Freshly generated objective wording.",
            source_refs=selected_item.source_refs,
            confidence=0.94,
            status="candidate",
            relation_hints={
                "normalized_objective_id": "objective-1",
                "dst_construct_source": "dst_runtime",
            },
            created_at_epoch_ms=202,
            updated_at_epoch_ms=202,
        )

        fake_discovery_result = type(
            "_FakeConstructDiscoveryResult",
            (),
            {
                "construct_candidates": (refreshed_candidate,),
                "orchestration_result": type(
                    "_FakeOrchestrationResult",
                    (),
                    {
                        "discovery_proposal_id": "proposal-discovery",
                        "normalization_proposal_id": "proposal-normalization",
                    },
                )(),
            },
        )()

        with patch(
            "workstation.subject.core.subject_workflow._run_live_dst_construct_discovery_with_timeout",
            return_value=(fake_discovery_result, ""),
        ):
            suggest = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )

        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        preserved_candidate = next(
            candidate
            for candidate in construct_candidates
            if collapse_ws(str(candidate.relation_hints.get("normalized_objective_id", ""))) == "objective-1"
        )

        self.assertEqual(suggest.status_text, "Transformation constructs suggested.")
        self.assertEqual(preserved_candidate.construct_candidate_id, existing_candidate.construct_candidate_id)
        self.assertEqual(preserved_candidate.notes, "curated construct note")
        self.assertEqual(preserved_candidate.canonical_label, "Original objective")
        self.assertEqual(
            collapse_ws(str(preserved_candidate.relation_hints.get("latest_generated_canonical_label", ""))),
            "Original objective (refreshed)",
        )

    def test_subject_workflow_itemize_suggest_transformation_constructs_uses_dst_fixture_projection_for_dst_subjects(self) -> None:
        subject_id = self._persist_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if collapse_ws(item.status) == "candidate"
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=AssertionError("fixture-backed suggestion should not invoke live discovery"),
        ) as live_discovery:
            suggest = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )

        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)
        receipt_text = "\n".join(progress.latest_receipt_lines)

        self.assertFalse(live_discovery.called)
        self.assertEqual(suggest.status_text, "Transformation constructs suggested.")
        self.assertIn("DST fixture seed", receipt_text)
        self.assertTrue(
            any(
                collapse_ws(str(candidate.relation_hints.get("dst_fixture_id")))
                for candidate in construct_candidates
            )
        )

    def test_subject_workflow_itemize_suggest_transformation_constructs_times_out_live_discovery_and_falls_back(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
        progress.projections_compared = True
        progress.comparison_status = "aligned"

        def _slow_live_discovery(*_args, **_kwargs):
            time.sleep(0.05)
            raise AssertionError("slow discovery should have timed out before returning")

        with patch(
            "workstation.subject.core.subject_workflow._LIVE_DST_CONSTRUCT_DISCOVERY_TIMEOUT_SECONDS",
            0.01,
        ), patch(
            "workstation.subject.core.subject_workflow.run_live_dst_construct_discovery_for_itemized_item",
            side_effect=_slow_live_discovery,
        ):
            suggest = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="suggest_transformation_constructs",
            )

        receipt_text = "\n".join(progress.latest_receipt_lines)
        construct_candidates = list_transformation_construct_candidates(self.root, subject_id)

        self.assertEqual(suggest.status_text, "Transformation constructs suggested.")
        self.assertIn("deterministic fallback", receipt_text)
        self.assertIn("timed out after", receipt_text)
        self.assertTrue(any(candidate.itemized_item_id == selected_item.itemized_item_id for candidate in construct_candidates))

    def test_subject_workflow_itemize_promote_reject_restore_and_cycle_decision_role(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )

        promote = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="promote_selected_itemized_item",
        )
        cycle_role = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_selected_itemized_item_decision_role",
        )
        reject = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="reject_selected_itemized_item",
        )
        restore = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="restore_selected_itemized_item",
        )

        updated_item = next(
            item for item in list_itemized_subject_items(self.root, subject_id)
            if item.itemized_item_id == selected_item_id
        )
        detail_text = render_subject_itemize_detail(scenario=scenario, progress=progress)

        self.assertEqual(promote.status_text, "Item promoted.")
        self.assertEqual(cycle_role.status_text, "Decision role updated.")
        self.assertEqual(reject.status_text, "Item rejected.")
        self.assertEqual(restore.status_text, "Item restored to candidate.")
        self.assertEqual(updated_item.status, "candidate")
        self.assertEqual(updated_item.metadata.get("decision_role"), "actor")
        self.assertIn("Decision role: actor", detail_text)

    def test_subject_workflow_itemize_decision_role_select_spec_tracks_selected_item_role(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        initial_spec = subject_itemize_decision_role_select_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertEqual(initial_spec.label, "Decision Role")
        self.assertEqual(initial_spec.value, "")
        self.assertTrue(initial_spec.enabled)
        self.assertIn(("Actor", "actor"), initial_spec.options)

        set_role = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_itemized_item_decision_role:actor",
        )
        self.assertEqual(set_role.status_text, "Decision role updated.")

        updated_spec = subject_itemize_decision_role_select_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertEqual(updated_spec.value, "actor")

    def test_subject_workflow_itemize_hold_switch_spec_tracks_selected_item_hold_state(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Alpha", item_kind="entity")

        initial_spec = subject_itemize_hold_switch_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertEqual(initial_spec.label, "Hold For Merge")
        self.assertFalse(initial_spec.value)
        self.assertTrue(initial_spec.enabled)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_itemized_item",
        )

        updated_spec = subject_itemize_hold_switch_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertTrue(updated_spec.value)
        self.assertTrue(updated_spec.enabled)

    def test_subject_workflow_itemize_hold_and_merge_creates_merged_candidate(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Alpha", item_kind="entity")
        hold_alpha = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_itemized_item",
        )
        self._select_itemized_candidate(subject_id=subject_id, progress=progress, label="Beta", item_kind="entity")
        hold_beta = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_itemized_item",
        )
        merge = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="merge_held_itemized_items",
        )

        items = list_itemized_subject_items(self.root, subject_id)
        merged_item = next(item for item in items if item.metadata.get("origin") == "itemize_merge")
        alpha_item = next(item for item in items if item.canonical_label == "Alpha" and item.item_kind == "entity")
        beta_item = next(item for item in items if item.canonical_label == "Beta" and item.item_kind == "entity")
        detail_text = render_subject_itemize_detail(scenario=scenario, progress=progress)

        self.assertEqual(hold_alpha.status_text, "Item held for merge.")
        self.assertEqual(hold_beta.status_text, "Item held for merge.")
        self.assertEqual(merge.status_text, "Held items merged.")
        self.assertEqual(alpha_item.status, "merged")
        self.assertEqual(beta_item.status, "merged")
        self.assertIn(alpha_item.itemized_item_id, merged_item.linked_item_ids)
        self.assertIn(beta_item.itemized_item_id, merged_item.linked_item_ids)
        self.assertEqual(progress.itemize_selected_item_id, merged_item.itemized_item_id)
        self.assertIn("Alpha matters. | Beta matters.", detail_text)
        self.assertIn("origin: itemize_merge", detail_text)

    def test_subject_workflow_draft_semantic_kind_select_spec_tracks_selected_item_kind(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        initial_spec = subject_draft_semantic_kind_select_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertEqual(initial_spec.label, "Semantic Kind")
        self.assertTrue(initial_spec.enabled)
        self.assertTrue(bool(initial_spec.value))

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_draft_review_semantic_kind:definition",
        )

        updated_spec = subject_draft_semantic_kind_select_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertEqual(updated_spec.value, "definition")

    def test_subject_workflow_draft_render_evidence_transform_select_specs_track_selected_item(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        render_spec = subject_draft_render_kind_select_spec(scenario=scenario, progress=progress)
        evidence_spec = subject_draft_evidence_mode_select_spec(scenario=scenario, progress=progress)
        transform_spec = subject_draft_transform_mode_select_spec(scenario=scenario, progress=progress)
        self.assertEqual(render_spec.label, "Render Style")
        self.assertEqual(evidence_spec.label, "Evidence Mode")
        self.assertEqual(transform_spec.label, "Transform Mode")
        self.assertTrue(render_spec.enabled)
        self.assertTrue(evidence_spec.enabled)
        self.assertTrue(transform_spec.enabled)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_draft_review_render_kind:equation_block",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_draft_review_evidence_mode:citation_box",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_draft_review_transform_mode:rewrite_manual",
        )

        render_updated = subject_draft_render_kind_select_spec(scenario=scenario, progress=progress)
        evidence_updated = subject_draft_evidence_mode_select_spec(scenario=scenario, progress=progress)
        transform_updated = subject_draft_transform_mode_select_spec(scenario=scenario, progress=progress)
        self.assertEqual(render_updated.value, "equation_block")
        self.assertEqual(evidence_updated.value, "citation_box")
        self.assertEqual(transform_updated.value, "rewrite_manual")

    def test_subject_workflow_review_publication_select_specs_track_report_plan(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        output_spec = subject_review_publication_output_mode_select_spec(scenario=scenario, progress=progress)
        section_spec = subject_review_publication_section_plan_select_spec(scenario=scenario, progress=progress)
        baseline_spec = subject_review_publication_diff_baseline_select_spec(scenario=scenario, progress=progress)
        unit_target_spec = subject_review_composition_unit_target_select_spec(scenario=scenario, progress=progress)
        include_unit_spec = subject_review_composition_unit_included_switch_spec(scenario=scenario, progress=progress)
        section_target_spec = subject_review_publication_section_target_select_spec(scenario=scenario, progress=progress)
        section_include_spec = subject_review_publication_section_included_switch_spec(scenario=scenario, progress=progress)
        self.assertEqual(output_spec.label, "Output Style")
        self.assertEqual(section_spec.label, "Report Structure")
        self.assertEqual(baseline_spec.label, "Diff Baseline")
        self.assertEqual(unit_target_spec.label, "Item")
        self.assertEqual(include_unit_spec.label, "In Report")
        self.assertEqual(section_target_spec.label, "Section")
        self.assertEqual(section_include_spec.label, "In Report")
        self.assertTrue(output_spec.enabled)
        self.assertTrue(section_spec.enabled)
        self.assertTrue(baseline_spec.enabled)
        self.assertTrue(unit_target_spec.enabled)
        self.assertTrue(include_unit_spec.enabled)
        self.assertTrue(section_target_spec.enabled)
        self.assertFalse(section_include_spec.enabled)
        self.assertGreaterEqual(len(unit_target_spec.options), 2)
        self.assertGreaterEqual(len(section_target_spec.options), 2)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_publication_output_mode:exact_draft",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_publication_output_mode:report",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_publication_section_plan:brief",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_publication_diff_baseline:snapshot",
        )
        current_target = collapse_ws(unit_target_spec.value)
        alternate_target = next(
            value
            for _label, value in unit_target_spec.options
            if collapse_ws(value) != current_target
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_composition_unit:{alternate_target}",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_composition_unit",
        )
        target_section_id = collapse_ws(section_target_spec.options[0][1])
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_selected_publication_section:{target_section_id}",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_publication_section",
        )

        output_updated = subject_review_publication_output_mode_select_spec(scenario=scenario, progress=progress)
        section_updated = subject_review_publication_section_plan_select_spec(scenario=scenario, progress=progress)
        baseline_updated = subject_review_publication_diff_baseline_select_spec(scenario=scenario, progress=progress)
        unit_target_updated = subject_review_composition_unit_target_select_spec(scenario=scenario, progress=progress)
        include_unit_updated = subject_review_composition_unit_included_switch_spec(scenario=scenario, progress=progress)
        section_target_updated = subject_review_publication_section_target_select_spec(scenario=scenario, progress=progress)
        section_include_updated = subject_review_publication_section_included_switch_spec(scenario=scenario, progress=progress)
        self.assertEqual(output_updated.value, "report")
        self.assertEqual(section_updated.value, "custom")
        self.assertEqual(baseline_updated.value, "snapshot")
        self.assertEqual(unit_target_updated.value, alternate_target)
        self.assertFalse(include_unit_updated.value)
        self.assertEqual(section_target_updated.value, target_section_id)
        self.assertFalse(section_include_updated.value)

    def test_subject_workflow_report_item_select_uses_relative_labels(self) -> None:
        self.assertEqual(
            _report_item_select_label(
                "Relative Item Demo",
                "Relative Item Demo / Situation",
                "fallback",
            ),
            "Situation",
        )
        self.assertEqual(
            _report_item_select_label(
                "Relative Item Demo",
                "Relative Item Demo / Situation / Actors",
                "fallback",
            ),
            "Situation / Actors",
        )

    def test_subject_workflow_review_composition_unit_switch_disables_for_last_included_unit(self) -> None:
        subject_id = self._persist_regional_dst_subject_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        include_unit_spec = subject_review_composition_unit_included_switch_spec(scenario=scenario, progress=progress)

        self.assertTrue(include_unit_spec.value)
        self.assertFalse(include_unit_spec.enabled)

    def test_subject_workflow_research_select_specs_track_selected_source_set_and_revision(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        staged_source = new_staged_source(
            subject_id=subject_id,
            title="Operator Source",
            source_ref="https://example.test/operator-source",
            source_kind="url",
            metadata={"requested_url": "https://example.test/operator-source"},
        )
        capture_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id=subject_id,
                source_ref=staged_source.source_ref,
                revision_kind="capture",
            ),
            created_at_epoch_ms=1000,
        )
        manual_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id=subject_id,
                source_ref=staged_source.source_ref,
                revision_kind="manual_curation",
            ),
            created_at_epoch_ms=2000,
        )
        merge_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id=subject_id,
                source_ref=staged_source.source_ref,
                revision_kind="merge",
            ),
            created_at_epoch_ms=3000,
        )
        persist_source_revision(self.root, capture_revision, markdown_text="# Capture\n\nInitial notes.\n")
        persist_source_revision(self.root, manual_revision, markdown_text="# Manual\n\nRefined notes.\n")
        persist_source_revision(self.root, merge_revision, markdown_text="# Merge\n\nMerged notes.\n")
        persist_staged_source(
            self.root,
            replace(
                staged_source,
                latest_revision_id=merge_revision.revision_id,
                revision_count=3,
                updated_at_epoch_ms=merge_revision.created_at_epoch_ms,
            ),
        )
        focused_collection = new_source_collection(
            subject_id=subject_id,
            title="Focused Sources",
            description="Operator-managed focused set.",
            staged_source_ids=(staged_source.staged_source_id,),
            query_text="focused operator source",
        )
        persist_source_collection(self.root, focused_collection)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = focused_collection.collection_id
        progress.research_selected_staged_source_id = staged_source.staged_source_id

        collection_spec = subject_research_source_collection_select_spec(scenario=scenario, progress=progress)
        baseline_spec = subject_research_source_revision_baseline_select_spec(scenario=scenario, progress=progress)
        membership_spec = subject_research_selected_source_collection_membership_switch_spec(scenario=scenario, progress=progress)
        target_text = render_subject_research_target(scenario=scenario, progress=progress)

        self.assertEqual(collection_spec.label, "Source Set")
        self.assertEqual(baseline_spec.label, "Revision Baseline")
        self.assertEqual(membership_spec.label, "In Source Set")
        self.assertTrue(collection_spec.enabled)
        self.assertTrue(baseline_spec.enabled)
        self.assertTrue(membership_spec.enabled)
        self.assertEqual(collection_spec.value, focused_collection.collection_id)
        self.assertEqual(membership_spec.value, True)
        option_labels = {label for label, _value in collection_spec.options}
        self.assertIn("All Gather Sources [1 source, no saved query]", option_labels)
        self.assertIn("Focused Sources [1 source, query saved]", option_labels)
        self.assertIn(capture_revision.revision_id, {value for _label, value in baseline_spec.options})
        self.assertIn(manual_revision.revision_id, {value for _label, value in baseline_spec.options})
        self.assertIn("Source-set workbench", target_text)
        self.assertIn("Find Sources Ready: yes", target_text)
        self.assertIn("Sync Source Set Ready: yes", target_text)
        self.assertIn("Apply Set Export Ready: yes", target_text)
        self.assertIn("Merge Source Set Ready: yes", target_text)
        self.assertIn("Merge Set Sources Ready: yes", target_text)
        self.assertIn("Refreshable Urls: 1", target_text)

        default_collection = next(
            collection for collection in list_source_collections(self.root, subject_id) if collection.title == "All Gather Sources"
        )
        switch_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_research_source_collection:{default_collection.collection_id}",
        )
        self.assertEqual(switch_result.status_text, "Source set selection updated.")
        default_membership_spec = subject_research_selected_source_collection_membership_switch_spec(
            scenario=scenario,
            progress=progress,
        )
        self.assertFalse(default_membership_spec.enabled)

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_research_source_collection:{focused_collection.collection_id}",
        )
        baseline_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key=f"set_research_source_revision_baseline:{capture_revision.revision_id}",
        )
        self.assertEqual(baseline_result.status_text, "Staged-source diff baseline updated.")
        baseline_updated = subject_research_source_revision_baseline_select_spec(scenario=scenario, progress=progress)
        self.assertEqual(baseline_updated.value, capture_revision.revision_id)

    def test_subject_workflow_itemize_split_creates_child_candidates(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        source_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Controls",
            item_kind="entity",
        )

        split = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="split_selected_itemized_item",
        )

        items = list_itemized_subject_items(self.root, subject_id)
        source_item = next(item for item in items if item.itemized_item_id == source_item_id)
        split_children = [
            item
            for item in items
            if item.metadata.get("origin") == "itemize_split"
            and item.metadata.get("split_from") == source_item_id
        ]

        self.assertEqual(split.status_text, "Item split into child candidates.")
        self.assertEqual(source_item.status, "split")
        self.assertEqual({item.canonical_label for item in split_children}, {"Access Controls", "Audit Controls"})
        self.assertEqual(progress.itemize_selected_item_id, split_children[0].itemized_item_id)

    def test_subject_workflow_itemize_manual_rephrase_updates_itemized_intermediate_without_touching_source(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )

        source_context = load_learning_context(self.root, subject_id)
        source = load_learning_source(self.root, subject_id, source_context.linked_source_ids[0])
        source_body_path = self.root / "corpus" / subject_id / "sources" / source.body_relpath
        original_source_text = source_body_path.read_text(encoding="utf-8")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_itemize_manual_rephrase",
        )
        rephrase_path = Path(start.open_paths[0])
        rephrase_path.write_text(
            "[label]\nAlpha Revised\n\n[text]\nAlpha matters in a reusable normalized form.\n",
            encoding="utf-8",
        )

        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_itemize_manual_rephrase",
        )

        updated_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.itemized_item_id == selected_item_id
        )

        self.assertEqual(start.status_text, "Manual rephrase file opened.")
        self.assertEqual(apply_result.status_text, "Manual itemize rephrase applied.")
        self.assertEqual(updated_item.canonical_label, "Alpha Revised")
        self.assertEqual(updated_item.summary, "Alpha matters in a reusable normalized form.")
        self.assertEqual(updated_item.metadata.get("last_rephrase_phase"), "itemize")
        self.assertEqual(updated_item.metadata.get("last_rephrase_mode"), "manual")
        self.assertEqual(source_body_path.read_text(encoding="utf-8"), original_source_text)

    def test_subject_workflow_itemize_llm_rephrase_updates_itemized_intermediate_without_touching_source(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )

        source_context = load_learning_context(self.root, subject_id)
        source = load_learning_source(self.root, subject_id, source_context.linked_source_ids[0])
        source_body_path = self.root / "corpus" / subject_id / "sources" / source.body_relpath
        original_source_text = source_body_path.read_text(encoding="utf-8")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_itemize_llm_rephrase",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_itemize_llm_rephrase",
            assistant_message_text="[label]\nAlpha Revised\n\n[text]\nAlpha matters in a reusable normalized form.\n",
        )

        updated_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.itemized_item_id == selected_item_id
        )

        self.assertEqual(start.status_text, "LLM itemize rephrase started.")
        self.assertEqual(apply_result.status_text, "LLM itemize rephrase applied.")
        self.assertEqual(updated_item.canonical_label, "Alpha Revised")
        self.assertEqual(updated_item.summary, "Alpha matters in a reusable normalized form.")
        self.assertEqual(updated_item.metadata.get("last_rephrase_phase"), "itemize")
        self.assertEqual(updated_item.metadata.get("last_rephrase_mode"), "llm_proposal")
        self.assertEqual(source_body_path.read_text(encoding="utf-8"), original_source_text)

    def test_subject_workflow_generate_itemization_preserves_manual_itemize_rephrase_across_context_refresh(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="glossary_term",
        )

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_itemize_manual_rephrase",
        )
        rephrase_path = Path(start.open_paths[0])
        rephrase_path.write_text(
            "[label]\nProgram Steering\n\n[text]\nCoordinate the program through one steering forum.\n",
            encoding="utf-8",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_itemize_manual_rephrase",
        )

        existing_context = load_learning_context(self.root, subject_id)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=existing_context.subject_id,
                canonical_title=existing_context.canonical_title,
                aliases=existing_context.aliases,
                subject_family=existing_context.subject_family,
                summary=existing_context.summary,
                units=tuple(
                    LearningUnit(
                        unit_id=unit.unit_id,
                        subject_id=unit.subject_id,
                        unit_kind=unit.unit_kind,
                        canonical_title="Governance Steering Committee" if unit.canonical_title == "Alpha" else unit.canonical_title,
                        aliases=unit.aliases,
                        statement=(
                            "The steering committee coordinates the program."
                            if unit.canonical_title == "Alpha"
                            else unit.statement
                        ),
                        provenance_refs=unit.provenance_refs,
                        status=unit.status,
                    )
                    for unit in existing_context.units
                ),
                linked_source_ids=existing_context.linked_source_ids,
                applied_delta_ids=existing_context.applied_delta_ids,
                governance_status=existing_context.governance_status,
            ),
        )

        refresh_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        refreshed_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.itemized_item_id == selected_item_id
        )

        self.assertEqual(refresh_result.status_text, "Itemization generated.")
        self.assertEqual(refreshed_item.canonical_label, "Program Steering")
        self.assertEqual(refreshed_item.summary, "Coordinate the program through one steering forum.")
        self.assertEqual(
            refreshed_item.metadata.get("latest_generated_canonical_label"),
            "Governance Steering Committee",
        )

    def test_subject_workflow_generate_itemization_preserves_llm_itemize_rephrase_across_context_refresh(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="glossary_term",
        )

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_itemize_llm_rephrase",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_itemize_llm_rephrase",
            assistant_message_text="[label]\nProgram Steering\n\n[text]\nCoordinate the program through one steering forum.\n",
        )

        existing_context = load_learning_context(self.root, subject_id)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=existing_context.subject_id,
                canonical_title=existing_context.canonical_title,
                aliases=existing_context.aliases,
                subject_family=existing_context.subject_family,
                summary=existing_context.summary,
                units=tuple(
                    LearningUnit(
                        unit_id=unit.unit_id,
                        subject_id=unit.subject_id,
                        unit_kind=unit.unit_kind,
                        canonical_title="Governance Steering Committee" if unit.canonical_title == "Alpha" else unit.canonical_title,
                        aliases=unit.aliases,
                        statement=(
                            "The steering committee coordinates the program."
                            if unit.canonical_title == "Alpha"
                            else unit.statement
                        ),
                        provenance_refs=unit.provenance_refs,
                        status=unit.status,
                    )
                    for unit in existing_context.units
                ),
                linked_source_ids=existing_context.linked_source_ids,
                applied_delta_ids=existing_context.applied_delta_ids,
                governance_status=existing_context.governance_status,
            ),
        )

        refresh_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        refreshed_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.itemized_item_id == selected_item_id
        )

        self.assertEqual(refresh_result.status_text, "Itemization generated.")
        self.assertEqual(refreshed_item.canonical_label, "Program Steering")
        self.assertEqual(refreshed_item.summary, "Coordinate the program through one steering forum.")
        self.assertEqual(refreshed_item.metadata.get("last_rephrase_mode"), "llm_proposal")
        self.assertEqual(
            refreshed_item.metadata.get("latest_generated_canonical_label"),
            "Governance Steering Committee",
        )

    def test_subject_workflow_draft_manual_rephrase_updates_review_item_and_persists_rewrite_receipt(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        source_context = load_learning_context(self.root, subject_id)
        source = load_learning_source(self.root, subject_id, source_context.linked_source_ids[0])
        source_body_path = self.root / "corpus" / subject_id / "sources" / source.body_relpath
        original_source_text = source_body_path.read_text(encoding="utf-8")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_draft_manual_rephrase",
        )
        rephrase_path = Path(start.open_paths[0])
        rephrase_path.write_text(
            "[label]\nAlpha Publication Form\n\n[text]\nAlpha matters in a clearer publication-ready sentence.\n",
            encoding="utf-8",
        )

        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_draft_manual_rephrase",
        )

        updated_review_item = next(
            item
            for item in list_review_items(self.root, subject_id)
            if collapse_ws(item.source_itemized_item_id) == selected_item_id
        )
        latest_receipt = list_review_transform_receipts(self.root, subject_id)[-1]

        self.assertEqual(start.status_text, "Manual draft rephrase file opened.")
        self.assertIn("Manual draft rephrase applied.", apply_result.status_text)
        self.assertEqual(updated_review_item.notes, "Alpha matters in a clearer publication-ready sentence.")
        self.assertEqual(updated_review_item.metadata.get("canonical_label"), "Alpha Publication Form")
        self.assertEqual(updated_review_item.transform_mode, "rewrite_manual")
        self.assertEqual(latest_receipt.transform_kind, "rewrite")
        self.assertEqual(source_body_path.read_text(encoding="utf-8"), original_source_text)

    def test_subject_workflow_draft_llm_rephrase_updates_review_item_and_persists_rewrite_receipt(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item_id = self._select_itemized_candidate(
            subject_id=subject_id,
            progress=progress,
            label="Alpha",
            item_kind="entity",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        source_context = load_learning_context(self.root, subject_id)
        source = load_learning_source(self.root, subject_id, source_context.linked_source_ids[0])
        source_body_path = self.root / "corpus" / subject_id / "sources" / source.body_relpath
        original_source_text = source_body_path.read_text(encoding="utf-8")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_draft_llm_rephrase",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_draft_llm_rephrase",
            assistant_message_text="[label]\nAlpha Publication Form\n\n[text]\nAlpha matters in a clearer publication-ready sentence.\n",
        )

        updated_review_item = next(
            item
            for item in list_review_items(self.root, subject_id)
            if collapse_ws(item.source_itemized_item_id) == selected_item_id
        )
        latest_receipt = list_review_transform_receipts(self.root, subject_id)[-1]

        self.assertEqual(start.status_text, "LLM draft rephrase started.")
        self.assertIn("LLM draft rephrase applied.", apply_result.status_text)
        self.assertEqual(updated_review_item.notes, "Alpha matters in a clearer publication-ready sentence.")
        self.assertEqual(updated_review_item.metadata.get("canonical_label"), "Alpha Publication Form")
        self.assertEqual(updated_review_item.transform_mode, "rewrite_llm_proposal")
        self.assertEqual(latest_receipt.transform_kind, "rewrite")
        self.assertEqual(source_body_path.read_text(encoding="utf-8"), original_source_text)

    def test_subject_workflow_review_manual_section_brief_updates_publication_composition_metadata(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self._select_report_section(scenario=scenario, progress=progress, section_title="Summary")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_review_section_manual_rephrase",
        )
        rephrase_path = Path(start.open_paths[0])
        rephrase_path.write_text(
            "[label]\nExecutive summary brief\n\n[text]\nOpen with the decision outcome, then explain why that recommendation holds under current constraints.\n",
            encoding="utf-8",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_review_section_manual_rephrase",
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        composition = self._latest_subject_composition(scenario=scenario)
        guidance_by_id = composition.metadata.get("section_guidance_by_id", {})
        summary_guidance = guidance_by_id.get("report-summary", {})

        self.assertEqual(start.status_text, "Manual section brief file opened.")
        self.assertEqual(apply_result.status_text, "Manual section brief applied.")
        self.assertEqual(summary_guidance.get("label"), "Executive summary brief")
        self.assertEqual(
            summary_guidance.get("text"),
            "Open with the decision outcome, then explain why that recommendation holds under current constraints.",
        )
        self.assertEqual(summary_guidance.get("mode"), "manual")

    def test_subject_workflow_review_llm_section_brief_clears_approval_when_report_plan_changes(self) -> None:
        subject_id = self._persist_itemize_editor_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="approve_review")
        self.assertTrue(progress.review_approved)

        self._select_report_section(scenario=scenario, progress=progress, section_title="Analysis")
        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_review_section_llm_rephrase",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_review_section_llm_rephrase",
            assistant_message_text="[label]\nAnalysis frame\n\n[text]\nExplain the admissible options, compare them, and state why the chosen path remains preferred.\n",
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        composition = self._latest_subject_composition(scenario=scenario)
        guidance_by_id = composition.metadata.get("section_guidance_by_id", {})
        analysis_guidance = guidance_by_id.get("report-analysis", {})

        self.assertEqual(start.status_text, "LLM section brief started.")
        self.assertIn("LLM section brief applied.", apply_result.status_text)
        self.assertIn("Review approval cleared.", apply_result.status_text)
        self.assertFalse(progress.review_approved)
        self.assertEqual(analysis_guidance.get("label"), "Analysis frame")
        self.assertEqual(analysis_guidance.get("mode"), "llm_proposal")

    def _persist_supporting_import_for_demo_context(self, *, subject_id: str) -> None:
        source_context = LearningContext(
            subject_id="dynamics-support",
            canonical_title="Dynamics Support",
            aliases=("Dynamics Support",),
            subject_family="Physics",
            summary="Supporting dynamics concepts for neighboring subjects.",
            governance_status="active",
        )
        persist_learning_context(self.root, source_context)
        active_context = load_learning_context(self.root, subject_id)
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id=subject_id,
                active_subject_version_id=active_context.content_hash(),
                active_subject_title=active_context.canonical_title,
                source_subject_id=source_context.subject_id,
                source_subject_version_id=source_context.content_hash(),
                source_subject_title=source_context.canonical_title,
                import_kind="definition_support",
                imported_unit_ids=("unit_force", "unit_mass"),
                rationale="Borrow dynamics terms without internalizing them into kinematics.",
            ),
        )

    def _persist_importable_source_context(self) -> str:
        subject_id = "dynamics-importable"
        source = new_learning_source(
            subject_id=subject_id,
            title="Dynamics Import Notes",
            source_ref="notes/dynamics-import.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Dynamics Import Notes\n\nForce equals mass times acceleration.\n",
        )
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title="Force",
            ),
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title="Force",
            statement="Force equals mass times acceleration.",
            linked_skill_ids=("force-skill",),
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Dynamics Importable",
            aliases=("Dynamics Importable",),
            subject_family="Physics / Dynamics",
            summary="Importable neighboring dynamics context.",
            units=(unit,),
            linked_source_ids=(source.source_id,),
            linked_skill_ids=("force-skill",),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        return subject_id

    def _persist_report_scope_reorder_context(self, *, subject_id: str = "reorder-demo") -> str:
        source = new_learning_source(
            subject_id=subject_id,
            title="Reorder Notes",
            source_ref="notes/reorder.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Reorder Notes\n\nA maintained subject with multiple report-scope units.\n",
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit multiple units for report-scope composition testing.",
        )
        persist_learning_delta(self.root, delta)
        units = (
            LearningUnit(
                unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Alpha"),
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title="Alpha",
                statement="Alpha anchors the definition lane.",
                provenance_refs=(source.source_id,),
                status="admitted",
            ),
            LearningUnit(
                unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="relation", canonical_title="Beta"),
                subject_id=subject_id,
                unit_kind="relation",
                canonical_title="Beta",
                statement="Beta is an analysis relation.",
                provenance_refs=(source.source_id,),
                status="admitted",
            ),
            LearningUnit(
                unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="ability", canonical_title="Gamma"),
                subject_id=subject_id,
                unit_kind="ability",
                canonical_title="Gamma",
                statement="Gamma is an implementation ability.",
                provenance_refs=(source.source_id,),
                status="admitted",
            ),
            LearningUnit(
                unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="misconception", canonical_title="Delta"),
                subject_id=subject_id,
                unit_kind="misconception",
                canonical_title="Delta",
                statement="Delta is an analysis misconception.",
                provenance_refs=(source.source_id,),
                status="admitted",
            ),
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Reorder Demo",
                aliases=("Reorder Demo",),
                subject_family="Physics / Ordering",
                summary="Maintained subject for report-scope reordering.",
                units=units,
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        return subject_id

    def _persist_multiple_supporting_imports_for_subject(self, *, subject_id: str) -> None:
        for suffix, title in (
            ("import-alpha", "Import Alpha"),
            ("import-beta", "Import Beta"),
            ("import-gamma", "Import Gamma"),
        ):
            source_context = LearningContext(
                subject_id=suffix,
                canonical_title=title,
                aliases=(title,),
                subject_family="Physics / Imports",
                summary=f"{title} support.",
                governance_status="active",
            )
            persist_learning_context(self.root, source_context)
            active_context = load_learning_context(self.root, subject_id)
            persist_subject_import(
                self.root,
                new_subject_import(
                    active_subject_id=subject_id,
                    active_subject_version_id=active_context.content_hash(),
                    active_subject_title=active_context.canonical_title,
                    source_subject_id=source_context.subject_id,
                    source_subject_version_id=source_context.content_hash(),
                    source_subject_title=source_context.canonical_title,
                    import_kind="definition_support",
                    imported_unit_ids=(f"unit_{suffix}",),
                    rationale=f"Borrow {title.lower()} support.",
                ),
            )

    def _progress_with_current_report_plan(self, *, subject_id: str) -> tuple[object, object]:
        scenario, progress = self._progress_with_current_draft_composition(subject_id=subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        return scenario, progress

    def _progress_with_current_draft_composition(self, *, subject_id: str) -> tuple[object, object]:
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        return scenario, progress

    def _move_report_scope_selection_to_label(self, *, scenario: object, progress: object, label: str) -> None:
        selectable_count_guard = 0
        while label not in render_subject_report_scope_detail(scenario=scenario, progress=progress):
            selected = move_report_scope_cursor(
                self.root,
                scenario=scenario,
                progress=progress,
                delta=1,
            )
            self.assertIsNotNone(selected)
            selectable_count_guard += 1
            self.assertLess(selectable_count_guard, 64, f"Could not reach report-scope label {label!r}")

    def _latest_subject_composition(self, *, scenario: object):
        if scenario.publication_id:
            compositions = list_publication_compositions(self.root, scenario.subject_id, scenario.publication_id)
            if compositions:
                return compositions[-1]
        publications_root = self.root / "corpus" / scenario.subject_id / "publications"
        for publication_root in sorted(publications_root.iterdir()) if publications_root.exists() else ():
            compositions = list_publication_compositions(self.root, scenario.subject_id, publication_root.name)
            if compositions:
                return compositions[-1]
        self.fail("Expected at least one publication composition.")

    def test_default_subject_scenarios_returns_placeholder_when_corpus_is_empty(self) -> None:
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        self.assertTrue(scenario.is_placeholder)
        self.assertIn("No subject yet", render_subject_status(scenario=scenario, progress=progress, phase="research"))

        action_specs = subject_action_specs(scenario=scenario, progress=progress, phase="research")
        self.assertEqual(action_specs[0].label, "Ask Follow-up In Chat")
        self.assertEqual(action_specs[0].key, "goto_chat")
        self.assertTrue(action_specs[0].enabled)
        self.assertEqual(action_specs[1].label, "Import Markdown File")
        self.assertEqual(action_specs[2].label, "Refresh Subjects")
        self.assertTrue(action_specs[1].enabled)

        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="use_markdown_ingress",
        )
        self.assertIn("Select Markdown File", result.status_text)

        chat_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="goto_chat",
        )
        self.assertEqual(chat_result.status_text, "Moved to Chat for a follow-up question.")
        self.assertEqual(chat_result.next_tab, "chat")

    def test_markdown_busy_state_updates_current_step_and_journey(self) -> None:
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
            markdown_selected_path="/tmp/example.md",
            markdown_status_text="Converting markdown to a portable skill bundle...",
            markdown_busy=True,
        )
        journey = render_subject_journey(
            scenario=scenario,
            progress=progress,
            phase="research",
            markdown_selected_path="/tmp/example.md",
            markdown_status_text="Converting markdown to a portable skill bundle...",
            markdown_busy=True,
        )
        actions = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="research",
            markdown_selected_path="/tmp/example.md",
            markdown_status_text="Converting markdown to a portable skill bundle...",
            markdown_busy=True,
        )

        self.assertIn("Do this now: Import markdown into the first subject", current_step)
        self.assertIn("- source markdown: example.md", current_step)
        self.assertIn("Gather material: importing example.md", journey)
        self.assertEqual(actions, ())

    def test_placeholder_gate_actions_surface_add_last_assistant_when_available(self) -> None:
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()

        review_gate_actions = subject_review_gate_actions(
            scenario=scenario,
            progress=progress,
            phase="research",
            can_capture_assistant=True,
        )
        publication_gate_actions = subject_publication_gate_actions(
            scenario=scenario,
            progress=progress,
            phase="research",
            can_capture_assistant=True,
        )

        self.assertEqual(review_gate_actions[0].label, "Add Last Assistant")
        self.assertEqual(review_gate_actions[0].key, "stage_assistant_capture")
        self.assertEqual(review_gate_actions[1].label, "Import Markdown File")
        self.assertEqual(publication_gate_actions, ())

    def test_subject_workflow_requires_aligned_projection_comparison_before_approval(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        review_specs_before = subject_action_specs(scenario=scenario, progress=progress, phase="review")
        self.assertFalse(review_specs_before[3].enabled)

        approve_before_compare = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        self.assertIn("Compare Maintained Files", approve_before_compare.status_text)

        open_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        self.assertEqual(open_result.status_text, "Subject context opened.")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="generate_itemization",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
        )

        compare_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )
        self.assertEqual(compare_result.status_text, "Projection comparison aligned.")
        self.assertIsNone(compare_result.next_phase)
        self.assertEqual(progress.comparison_status, "aligned")
        self.assertIn("- verdict: aligned", "\n".join(progress.comparison_receipt_lines))
        self.assertIn("- items covered in subject.md: 1 / 1", "\n".join(progress.comparison_receipt_lines))
        self.assertIn("- items covered in subject.typ: 1 / 1", "\n".join(progress.comparison_receipt_lines))
        current_step_after_compare = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertIn("The maintained-files check completed and the files are aligned.", current_step_after_compare)

        review_specs_after = subject_action_specs(scenario=scenario, progress=progress, phase="review")
        self.assertEqual(review_specs_after[2].label, "Refresh Report Plan")
        self.assertTrue(review_specs_after[2].enabled)
        self.assertFalse(review_specs_after[3].enabled)

        refresh_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_publication_composition",
        )
        self.assertEqual(refresh_result.status_text, "Report plan refreshed.")
        self.assertEqual(refresh_result.next_phase, "draft")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        review_specs_ready = subject_action_specs(scenario=scenario, progress=progress, phase="review")
        self.assertTrue(review_specs_ready[3].enabled)

        review_text = render_subject_workspace(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertIn("Review Completion", review_text)
        self.assertIn("Maintained Files Summary", review_text)
        self.assertIn("Maintained Files Check", review_text)
        self.assertIn("Report Plan", review_text)
        self.assertIn("- verdict: aligned", review_text)
        self.assertIn("- items covered in subject.md: 1 / 1", review_text)
        self.assertIn("- blocker: none", review_text)

    def test_subject_workflow_builds_real_publication_from_learning_context(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self.assertIn("Velocity", scenario.unit_preview_lines[0])
        self.assertIn("Kinematics Notes", "\n".join(scenario.source_preview_lines))
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )
        build_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="build_report",
        )

        self.assertTrue(build_result.reload_subjects)
        self.assertIn("Report build completed", build_result.status_text)

        rebuilt_scenarios = default_subject_scenarios(self.root)
        rebuilt = next(item for item in rebuilt_scenarios if item.subject_id == subject_id)
        self.assertTrue(rebuilt.publication_id)
        self.assertTrue(rebuilt.build_id)
        self.assertTrue(rebuilt.composition_id)
        self.assertEqual(rebuilt.composition_status, "approved")
        self.assertGreater(rebuilt.publication_section_count, 0)
        self.assertGreater(rebuilt.publication_claim_count, 0)
        self.assertGreater(rebuilt.publication_review_count, 0)
        self.assertTrue(Path(rebuilt.report_pdf_path).is_file())
        self.assertTrue(Path(rebuilt.report_typst_path).is_file())
        self.assertTrue(Path(rebuilt.report_markdown_path).is_file())
        self.assertEqual(build_result.open_paths, (rebuilt.report_pdf_path,))

        publication_specs = subject_action_specs(scenario=rebuilt, progress=progress, phase="publication")
        self.assertEqual(publication_specs[0].label, "Preview report.pdf")
        self.assertEqual(publication_specs[1].label, "Rebuild Report")
        self.assertEqual(publication_specs[2].label, "Open Release Folder")
        self.assertEqual(publication_specs[3].label, "Preview report.md")
        self.assertTrue(publication_specs[0].enabled)
        self.assertTrue(publication_specs[2].enabled)
        self.assertTrue(publication_specs[3].enabled)

        packet_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="open_release_packet",
        )
        self.assertTrue(packet_result.open_paths)
        self.assertTrue(Path(packet_result.open_paths[0]).is_dir())
        self.assertIn("- packet items:", "\n".join(progress.latest_receipt_lines))
        current_step_after_packet = render_subject_current_step(
            scenario=rebuilt,
            progress=progress,
            phase="publication",
        )
        current_actions_after_packet = subject_current_step_actions(
            scenario=rebuilt,
            progress=progress,
            phase="publication",
        )
        self.assertIn("Do this now: Finish the release review", current_step_after_packet)
        self.assertEqual(current_actions_after_packet[0].label, "Finish Release Review")

        complete_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="complete_release_review",
        )
        self.assertEqual(complete_result.status_text, "Release review completed.")
        self.assertTrue(progress.release_review_completed)

        markdown_preview_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="preview_publication_markdown",
        )
        self.assertEqual(progress.publication_preview_kind, "report.md")
        self.assertEqual(markdown_preview_result.status_text, "Opened report.md.")
        self.assertEqual(markdown_preview_result.open_paths, (rebuilt.report_markdown_path,))

        pdf_preview_result = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=progress,
            action_key="preview_publication_pdf",
        )
        self.assertEqual(progress.publication_preview_kind, "report.pdf")
        self.assertEqual(pdf_preview_result.status_text, "Opened report.pdf.")
        self.assertEqual(pdf_preview_result.open_paths, (rebuilt.report_pdf_path,))

        publication_text = render_subject_workspace(
            scenario=rebuilt,
            progress=progress,
            phase="publication",
        )
        self.assertIn("Publication Contract", publication_text)
        self.assertIn("Publication Completion", publication_text)
        self.assertIn("Build Artifacts", publication_text)
        self.assertIn("Publication Build Receipt", publication_text)
        self.assertIn("- report plan id:", publication_text)
        self.assertIn("- report plan status:", publication_text)
        self.assertIn("- reviews:", publication_text)
        self.assertIn("- xrefs:", publication_text)
        self.assertIn("- sections:", publication_text)
        self.assertIn("- claims:", publication_text)
        self.assertIn("- rendered pdf:", publication_text)
        self.assertIn("- release packet:", publication_text)
        self.assertIn("- packet contents:", publication_text)
        self.assertIn("Output Preview [report.pdf]", publication_text)
        self.assertIn("report.pdf is a binary artifact.", publication_text)

    def test_subject_workflow_surfaces_reasoning_scope_import_counts(self) -> None:
        subject_id = self._persist_demo_context()
        self._persist_supporting_import_for_demo_context(subject_id=subject_id)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        status_text = render_subject_status(scenario=scenario, progress=progress, phase="research")
        workspace_text = render_subject_workspace(scenario=scenario, progress=progress, phase="research")
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)
        observation_text = render_subject_research_observation(scenario=scenario, progress=progress)
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        review_gate_text = render_subject_review_gate(scenario=scenario, progress=progress)
        publication_gate_text = render_subject_publication_gate(scenario=scenario, progress=progress)
        review_gate_actions = subject_review_gate_actions(scenario=scenario, progress=progress, phase="research")
        publication_gate_actions = subject_publication_gate_actions(scenario=scenario, progress=progress, phase="research")

        self.assertEqual(scenario.import_count, 1)
        self.assertEqual(scenario.reasoning_import_count, 1)
        self.assertEqual(scenario.imported_subject_count, 1)
        self.assertTrue(scenario.import_preview_lines)
        self.assertIn("Reasoning Scope: 1 support items from 1 subjects", status_text)
        self.assertNotIn("Review Gate", status_text)
        self.assertNotIn("Publication Gate", status_text)
        self.assertIn("- sources: 1", workspace_text)
        self.assertIn("- active support: 1", sources_text)
        self.assertIn("Active support", sources_text)
        self.assertIn("Learned now", observation_text)
        self.assertIn("- active support in reasoning scope: 1", target_text)
        self.assertIn("Report readiness", target_text)
        self.assertIn("Pending imports: clear", review_gate_text)
        self.assertIn("Inputs: pending", publication_gate_text)
        self.assertIn("Blocked by: Open the subject context.", review_gate_text)
        self.assertIn("Blocked by review gate: yes", publication_gate_text)
        self.assertIn("Blocked by: Open the subject context.", publication_gate_text)
        self.assertEqual(review_gate_actions[0].label, "Open Subject Context")
        self.assertEqual(publication_gate_actions[0].label, "Review")
        self.assertIn("Dynamics Support [definition_support]", "\n".join(scenario.import_preview_lines))

    def test_subject_workflow_research_sources_surface_staged_sources_before_import(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        revision_history_spec = subject_research_selected_source_revision_history_table_spec(
            scenario=scenario,
            progress=progress,
        )
        change_summary_spec = subject_research_selected_source_change_summary_table_spec(
            scenario=scenario,
            progress=progress,
        )
        current_actions = subject_current_step_actions(scenario=scenario, progress=progress, phase="research")

        self.assertEqual(scenario.staged_source_count, 1)
        self.assertEqual(len(list_staged_sources(self.root, "example-article")), 1)
        self.assertIn("Sources (1)", sources_text)
        self.assertIn("> [url] Example Article", sources_text)
        self.assertIn("status=staged", sources_text)
        self.assertIn("bundle=3 files", sources_text)
        self.assertIn("Selected staged source", target_text)
        self.assertIn("Markdown body:", target_text)
        self.assertIn("- # Example Article", target_text)
        self.assertIn("Export proposal preview", target_text)
        self.assertIn("- current admitted, itemized, or draft learnings are not rich enough yet", target_text)
        self.assertIn("Gather source workspace", target_text)
        self.assertIn("- latest staged source: Example Article", target_text)
        self.assertEqual(len(revision_history_spec.rows), 1)
        self.assertEqual(revision_history_spec.rows[0][0], "current")
        self.assertEqual(revision_history_spec.rows[0][1], "capture")
        self.assertIn(("latest revision kind", "capture"), change_summary_spec.rows)
        self.assertIn(("note", "no prior revision exists yet"), change_summary_spec.rows)
        self.assertEqual(current_actions[0].label, "Activate Subject")

    def test_subject_workflow_research_sources_surface_default_source_collection_context(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        collections = list_source_collections(self.root, "example-article")

        self.assertEqual(len(collections), 1)
        self.assertEqual(collections[0].title, "All Gather Sources")
        self.assertEqual(
            collections[0].staged_source_ids,
            tuple(item.staged_source_id for item in list_staged_sources(self.root, "example-article")),
        )
        self.assertIn("Source sets (1)", sources_text)
        self.assertIn("- current set: All Gather Sources", sources_text)
        self.assertIn("- find sources ready: no", sources_text)
        self.assertIn("- sync source set ready: yes", sources_text)
        self.assertIn("- apply set export ready: no", sources_text)
        self.assertIn("- source sets: 1", target_text)
        self.assertIn("- current source set: All Gather Sources", target_text)

    def test_subject_workflow_research_source_sets_can_be_created_and_filtered(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        second_source = new_staged_source(
            subject_id="example-article",
            title="Operator Checklist",
            source_ref="https://example.test/checklist",
            source_kind="url",
            metadata={"requested_url": "https://example.test/checklist"},
        )
        second_revision = new_source_revision(
            staged_source_id=second_source.staged_source_id,
            subject_id=second_source.subject_id,
            source_ref=second_source.source_ref,
            revision_kind="capture",
        )
        persist_source_revision(
            self.root,
            second_revision,
            markdown_text="# Operator Checklist\n\nChecklist source.\n",
            bundle_files={"rendered.html": "<html><body>Checklist</body></html>"},
        )
        persist_staged_source(
            self.root,
            replace(
                second_source,
                latest_revision_id=second_revision.revision_id,
                revision_count=1,
                updated_at_epoch_ms=second_revision.created_at_epoch_ms,
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        create_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        collections = list_source_collections(self.root, "example-article")
        filtered_sources_text = render_subject_research_sources(scenario=scenario, progress=progress)

        cycle_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_research_source_collection",
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        cycled_sources_text = render_subject_research_sources(scenario=scenario, progress=progress)

        self.assertEqual(create_result.status_text, "Source set created.")
        self.assertEqual(len(collections), 2)
        self.assertTrue(any(collection.title.startswith("Focused: ") for collection in collections))
        self.assertIn("Sources (2)", filtered_sources_text)
        self.assertIn("> [set] Focused:", filtered_sources_text)
        self.assertIn("in-set=yes", filtered_sources_text)
        self.assertIn("in-set=no", filtered_sources_text)
        self.assertEqual(cycle_result.status_text, "Source set selection updated.")
        self.assertIn("> [set] All Gather Sources", cycled_sources_text)
        self.assertIn("Sources (2)", cycled_sources_text)

    def test_subject_workflow_can_create_source_collection_from_query(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_query",
            assistant_message_text="Energy Route Sources | energy exports transport routes | Sources for cross-border routing.",
        )

        collections = list_source_collections(self.root, "example-article")
        created = next(
            item for item in collections if collapse_ws(item.metadata.get("collection_kind", "")) == "topic_query"
        )
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)
        target_text = render_subject_research_target(scenario=scenario, progress=progress)

        self.assertEqual(result.status_text, "Source set created from query.")
        self.assertEqual(created.query_text, "energy exports transport routes")
        self.assertEqual(created.description, "Sources for cross-border routing.")
        self.assertEqual(collapse_ws(created.metadata.get("collection_kind", "")), "topic_query")
        self.assertEqual(collapse_ws(progress.research_selected_source_collection_id), created.collection_id)
        self.assertIn("- current set: Energy Route Sources", sources_text)
        self.assertIn("- query/topic: energy exports transport routes", sources_text)
        self.assertIn("Kind: topic/query", target_text)
        self.assertIn("Saved query/topic: energy exports transport routes", target_text)

    def test_subject_workflow_can_apply_source_collection_synthesis_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged_result = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        focused_collection = next(
            item
            for item in list_source_collections(self.root, scenario.subject_id)
            if item.collection_id == progress.research_selected_source_collection_id
        )
        persist_source_collection(
            self.root,
            replace(
                focused_collection,
                title="Energy Export Sources",
                query_text="energy exports transport routes",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")

        start_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_synthesis",
            assistant_message_text="Draft source-set synthesis requested.",
        )
        current_step_text = render_subject_current_step(scenario=scenario, progress=progress, phase="research")

        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_synthesis",
            assistant_message_text=(
                "[summary]\n"
                "Coverage of cross-border energy exports, transport modes, and infrastructure dependencies.\n\n"
                "[questions]\n"
                "What transit chokepoints matter most?\n"
                "Which regulator decisions affect interconnector capacity?\n\n"
                "[query]\n"
                "energy exports transport routes interconnectors chokepoints"
            ),
        )

        updated_collection = next(
            item
            for item in list_source_collections(self.root, scenario.subject_id)
            if item.collection_id == progress.research_selected_source_collection_id
        )
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)
        context = load_learning_context(self.root, scenario.subject_id)

        self.assertEqual(start_result.status_text, "LLM source-set synthesis started.")
        self.assertIn("Apply the source-set synthesis", current_step_text)
        self.assertEqual(apply_result.status_text, "Source-set synthesis applied.")
        self.assertEqual(
            updated_collection.metadata.get("knowledgebase_summary"),
            "Coverage of cross-border energy exports, transport modes, and infrastructure dependencies.",
        )
        self.assertEqual(
            tuple(updated_collection.metadata.get("knowledgebase_open_questions", ())),
            (
                "What transit chokepoints matter most?",
                "Which regulator decisions affect interconnector capacity?",
            ),
        )
        self.assertEqual(updated_collection.metadata.get("last_knowledge_synthesis_mode"), "llm")
        self.assertEqual(
            updated_collection.query_text,
            "energy exports transport routes interconnectors chokepoints",
        )
        self.assertIn("Knowledgebase", target_text)
        self.assertIn("Summary: Coverage of cross-border energy exports", target_text)
        self.assertIn("Open questions: 2", target_text)
        self.assertIn("- knowledge summary: Coverage of cross-border energy exports", sources_text)
        self.assertIn("- open questions: 2", sources_text)
        self.assertFalse(context.linked_source_ids)

    def test_subject_workflow_can_apply_manual_curation_to_selected_staged_source_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_manual_curation",
        )
        pending_path = Path(progress.research_source_manual_curation_path)
        pending_path.write_text(
            "# Gather Manual Source Curation\n\n"
            "[label]\n"
            "Example Source Notes\n\n"
            "[text]\n"
            "# Example Source Notes\n\n"
            "Velocity is displacement per unit time.\n\n"
            "Keep this as source-only notes.\n",
            encoding="utf-8",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_manual_curation",
        )

        staged_source = list_staged_sources(self.root, "example-article")[0]
        latest_revision = latest_source_revision(self.root, staged_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        learning_context = load_learning_context(self.root, "example-article")

        self.assertEqual(start.status_text, "Manual source curation file opened.")
        self.assertIn("Apply the manual source curation", current_step)
        self.assertEqual(apply_result.status_text, "Manual source curation applied.")
        self.assertEqual(staged_source.title, "Example Source Notes")
        self.assertEqual(latest_revision.revision_kind, "manual_curation")
        self.assertEqual(latest_revision.metadata.get("curation_mode"), "manual")
        self.assertIn("Keep this as source-only notes.", body_path.read_text(encoding="utf-8"))
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_llm_curation_to_selected_staged_source_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_llm_curation",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_llm_curation",
            assistant_message_text=(
                "[label]\nExample Source Notes\n\n[text]\n"
                "# Example Source Notes\n\n"
                "Velocity is displacement per unit time.\n\n"
                "Keep this as source-only notes.\n"
            ),
        )

        staged_source = list_staged_sources(self.root, "example-article")[0]
        latest_revision = latest_source_revision(self.root, staged_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        learning_context = load_learning_context(self.root, "example-article")

        self.assertEqual(start.status_text, "LLM source curation started.")
        self.assertIn("Apply the source curation", current_step)
        self.assertEqual(apply_result.status_text, "LLM source curation applied.")
        self.assertEqual(staged_source.title, "Example Source Notes")
        self.assertEqual(latest_revision.revision_kind, "llm_curation")
        self.assertEqual(latest_revision.metadata.get("curation_mode"), "llm")
        self.assertEqual(
            latest_revision.metadata.get("source_collection_id"),
            list_source_collections(self.root, "example-article")[0].collection_id,
        )
        self.assertIn("Keep this as source-only notes.", body_path.read_text(encoding="utf-8"))
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_merge_back_to_selected_staged_source_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-article",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="example-article",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-article",
                canonical_title="Example Article",
                aliases=("Example Article",),
                subject_family="Example Article",
                summary="A maintained subject with admitted learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_merge_back",
            assistant_message_text=(
                "[label]\nExample Source Notes\n\n[text]\n"
                "# Example Source Notes\n\n"
                "Velocity is displacement per unit time.\n\n"
                "Add maintained notes about how this source should be used during import.\n"
            ),
        )

        staged_source = list_staged_sources(self.root, "example-article")[0]
        latest_revision = latest_source_revision(self.root, staged_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        learning_context = load_learning_context(self.root, "example-article")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        revision_history_spec = subject_research_selected_source_revision_history_table_spec(
            scenario=scenario,
            progress=progress,
        )
        change_summary_spec = subject_research_selected_source_change_summary_table_spec(
            scenario=scenario,
            progress=progress,
        )

        self.assertEqual(start.status_text, "LLM merge-back proposal started.")
        self.assertIn("Apply the merge-back proposal", current_step)
        self.assertEqual(apply_result.status_text, "Source merge-back applied.")
        self.assertEqual(staged_source.title, "Example Source Notes")
        self.assertEqual(latest_revision.revision_kind, "merge")
        self.assertEqual(latest_revision.metadata.get("merge_mode"), "llm")
        self.assertEqual(latest_revision.metadata.get("merge_scope"), "subject_intermediate")
        self.assertEqual(latest_revision.metadata.get("admitted_unit_count"), 1)
        self.assertIn("Add maintained notes about how this source should be used during import.", body_path.read_text(encoding="utf-8"))
        self.assertIn("Export proposal preview", target_text)
        self.assertIn("- proposed revision kind: merge", target_text)
        self.assertIn("- subject summary note: A maintained subject with admitted learnings.", target_text)
        self.assertEqual(len(revision_history_spec.rows), 2)
        self.assertIn(("revision flow", "capture → merge"), change_summary_spec.rows)
        self.assertIn(
            ("latest addition", "Add maintained notes about how this source should be used during import."),
            change_summary_spec.rows,
        )
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_cycle_selected_staged_source_diff_baseline(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        manual_start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_manual_curation",
        )
        Path(progress.research_source_manual_curation_path).write_text(
            "# Gather Manual Source Curation\n\n"
            "[label]\n"
            "Example Source Notes\n\n"
            "[text]\n"
            "# Example Source Notes\n\n"
            "Velocity is displacement per unit time.\n\n"
            "Keep this as source-only notes.\n",
            encoding="utf-8",
        )
        manual_apply = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_manual_curation",
        )

        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-article",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="example-article",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-article",
                canonical_title="Example Article",
                aliases=("Example Article",),
                subject_family="Example Article",
                summary="A maintained subject with admitted learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )
        merge_start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        merge_apply = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_merge_back",
            assistant_message_text=(
                "[label]\nExample Source Notes\n\n[text]\n"
                "# Example Source Notes\n\n"
                "Velocity is displacement per unit time.\n\n"
                "Keep this as source-only notes.\n\n"
                "Add maintained notes about how this source should be used during import.\n"
            ),
        )

        target_before_cycle = render_subject_research_target(scenario=scenario, progress=progress)
        cycle_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_research_source_revision_baseline",
        )
        target_after_cycle = render_subject_research_target(scenario=scenario, progress=progress)

        self.assertEqual(manual_start.status_text, "Manual source curation file opened.")
        self.assertEqual(manual_apply.status_text, "Manual source curation applied.")
        self.assertEqual(merge_start.status_text, "LLM merge-back proposal started.")
        self.assertEqual(merge_apply.status_text, "Source merge-back applied.")
        self.assertIn("Selected diff baseline: manual_curation /", target_before_cycle)
        self.assertIn("Latest revision kind: merge", target_before_cycle)
        self.assertEqual(cycle_result.status_text, "Staged-source diff baseline updated.")
        self.assertIn("- selected baseline: capture", "\n".join(progress.latest_receipt_lines))
        self.assertIn("Selected diff baseline: capture /", target_after_cycle)
        self.assertIn("Latest revision kind: merge", target_after_cycle)

    def test_subject_workflow_can_apply_manual_curation_to_selected_source_collection_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        second_source = new_staged_source(
            subject_id="example-article",
            title="Operator Checklist",
            source_ref="https://example.test/checklist",
            source_kind="url",
            metadata={"requested_url": "https://example.test/checklist"},
        )
        second_revision = new_source_revision(
            staged_source_id=second_source.staged_source_id,
            subject_id=second_source.subject_id,
            source_ref=second_source.source_ref,
            revision_kind="capture",
        )
        persist_source_revision(
            self.root,
            second_revision,
            markdown_text="# Operator Checklist\n\nChecklist source.\n",
            bundle_files={"rendered.html": "<html><body>Checklist</body></html>"},
        )
        persist_staged_source(
            self.root,
            replace(
                second_source,
                latest_revision_id=second_revision.revision_id,
                revision_count=1,
                updated_at_epoch_ms=second_revision.created_at_epoch_ms,
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_manual_curation",
        )
        pending_path = Path(progress.research_source_collection_manual_curation_path)
        pending_path.write_text(
            "# Gather Manual Source Set Curation\n\n"
            "[label]\n"
            "Energy Transport Sources\n\n"
            "[description]\n"
            "Sources about cross-border energy exports, infrastructure, and transport routes.\n\n"
            "[query]\n"
            "energy exports transport routes\n",
            encoding="utf-8",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_manual_curation",
        )

        collections = list_source_collections(self.root, "example-article")
        curated_collection = next(
            item for item in collections if item.collection_id == progress.research_selected_source_collection_id
        )
        learning_context = load_learning_context(self.root, "example-article")
        sources_text = render_subject_research_sources(scenario=scenario, progress=progress)

        self.assertEqual(start.status_text, "Manual source-set curation file opened.")
        self.assertIn("Apply the manual source-set curation", current_step)
        self.assertEqual(apply_result.status_text, "Manual source-set curation applied.")
        self.assertEqual(curated_collection.title, "Energy Transport Sources")
        self.assertEqual(
            curated_collection.description,
            "Sources about cross-border energy exports, infrastructure, and transport routes.",
        )
        self.assertEqual(curated_collection.query_text, "energy exports transport routes")
        self.assertEqual(curated_collection.metadata.get("last_curation_mode"), "manual")
        self.assertIn("notes=Sources about cross-border energy exports", sources_text)
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_llm_curation_to_selected_source_collection_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_llm_curation",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_llm_curation",
            assistant_message_text=(
                "[label]\nEnergy Transport Sources\n\n"
                "[description]\n"
                "Sources about cross-border energy exports, infrastructure, and transport routes.\n\n"
                "[query]\n"
                "energy exports transport routes\n"
            ),
        )

        collections = list_source_collections(self.root, "example-article")
        curated_collection = next(
            item for item in collections if item.collection_id == progress.research_selected_source_collection_id
        )
        learning_context = load_learning_context(self.root, "example-article")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)

        self.assertEqual(start.status_text, "LLM source-set curation started.")
        self.assertIn("Apply the source-set curation", current_step)
        self.assertEqual(apply_result.status_text, "LLM source-set curation applied.")
        self.assertEqual(curated_collection.title, "Energy Transport Sources")
        self.assertEqual(
            curated_collection.description,
            "Sources about cross-border energy exports, infrastructure, and transport routes.",
        )
        self.assertEqual(curated_collection.query_text, "energy exports transport routes")
        self.assertEqual(curated_collection.metadata.get("last_curation_mode"), "llm")
        self.assertIn("- current set notes: Sources about cross-border energy exports, infrastructure, and transport routes.", target_text)
        self.assertIn("- current query/topic: energy exports transport routes", target_text)
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_discovered_sources_to_selected_source_collection_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        focused_collection = next(
            item
            for item in list_source_collections(self.root, "example-article")
            if item.collection_id == progress.research_selected_source_collection_id
        )
        persist_source_collection(
            self.root,
            replace(
                focused_collection,
                title="Energy Export Sources",
                description="Sources about energy exports and how they move across borders.",
                query_text="energy exports transport routes",
            ),
        )

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_discovery",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_discovery",
            assistant_message_text=(
                "[source]\n"
                "[label]\nExample Article\n\n"
                "[url]\nhttps://example.test/article?ref=final\n\n"
                "[notes]\nBaseline explainer for energy exports and routes.\n\n"
                "[source]\n"
                "[label]\nGrid Interconnector Overview\n\n"
                "[url]\nhttps://example.test/interconnectors\n\n"
                "[notes]\nUse this to cover cross-border electricity interconnectors and operator constraints.\n"
            ),
        )

        updated_collection = next(
            item
            for item in list_source_collections(self.root, "example-article")
            if item.collection_id == progress.research_selected_source_collection_id
        )
        staged_sources = list_staged_sources(self.root, "example-article")
        new_source = next(item for item in staged_sources if item.source_ref == "https://example.test/interconnectors")
        latest_revision = latest_source_revision(self.root, new_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        learning_context = load_learning_context(self.root, "example-article")

        self.assertEqual(start.status_text, "LLM source discovery started.")
        self.assertIn("Apply discovered sources", current_step)
        self.assertEqual(apply_result.status_text, "Discovered sources applied.")
        self.assertEqual(latest_revision.revision_kind, "discovery")
        self.assertEqual(latest_revision.metadata.get("source_collection_id"), updated_collection.collection_id)
        self.assertEqual(latest_revision.metadata.get("discovery_query_text"), "energy exports transport routes")
        self.assertIn(
            "Use this to cover cross-border electricity interconnectors",
            body_path.read_text(encoding="utf-8"),
        )
        self.assertIn(new_source.staged_source_id, updated_collection.staged_source_ids)
        self.assertEqual(updated_collection.metadata.get("last_discovery_mode"), "llm")
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_merge_back_to_selected_source_collection_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nThis source explains energy exports.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        focused_collection = next(
            item
            for item in list_source_collections(self.root, "example-article")
            if item.collection_id == progress.research_selected_source_collection_id
        )
        persist_source_collection(
            self.root,
            replace(
                focused_collection,
                title="Energy Export Sources",
                description="Sources about energy exports and how they move across borders.",
                query_text="energy exports transport routes",
            ),
        )
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-article",
                unit_kind="definition",
                canonical_title="Cross-border transport modes",
            ),
            subject_id="example-article",
            unit_kind="definition",
            canonical_title="Cross-border transport modes",
            statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-article",
                canonical_title="Example Article",
                aliases=("Example Article",),
                subject_family="Example Article",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_merge_back",
            assistant_message_text=(
                "[label]\nEnergy Export Sources\n\n"
                "[description]\n"
                "Sources about energy exports, transport routes, and how cross-border infrastructure shapes the trade.\n\n"
                "[query]\n"
                "energy exports transport routes interconnectors\n"
            ),
        )

        updated_collection = next(
            item
            for item in list_source_collections(self.root, "example-article")
            if item.collection_id == progress.research_selected_source_collection_id
        )
        learning_context = load_learning_context(self.root, "example-article")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)

        self.assertEqual(start.status_text, "LLM source-set merge-back proposal started.")
        self.assertIn("Apply the source-set merge-back proposal", current_step)
        self.assertEqual(apply_result.status_text, "Source-set merge-back applied.")
        self.assertEqual(
            updated_collection.description,
            "Sources about energy exports, transport routes, and how cross-border infrastructure shapes the trade.",
        )
        self.assertEqual(updated_collection.query_text, "energy exports transport routes interconnectors")
        self.assertEqual(updated_collection.metadata.get("last_merge_back_mode"), "llm")
        self.assertIn("Selected source set", target_text)
        self.assertIn("Source-set export preview", target_text)
        self.assertIn("- current query/topic: energy exports transport routes interconnectors", target_text)
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_set_source_merge_back_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-one",
            final_url="https://example.test/source-one",
            title="Source One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Source One\n\nInitial source one notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-two",
            final_url="https://example.test/source-two",
            title="Source Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Source Two\n\nInitial source two notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-two"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            first_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            second_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Sources about energy exports and transport routes.",
            staged_source_ids=(
                str(first_result.payload["staged_source_id"]),
                str(second_result.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="energy-exports",
                canonical_title="Energy Exports",
                aliases=("Energy Exports",),
                subject_family="Energy Exports",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="energy-exports",
                            unit_kind="definition",
                            canonical_title="Cross-border transport modes",
                        ),
                        subject_id="energy-exports",
                        unit_kind="definition",
                        canonical_title="Cross-border transport modes",
                        statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
                        provenance_refs=(),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id

        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_source_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        current_step = render_subject_current_step(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_collection_source_merge_back",
            assistant_message_text=(
                "[source]\n"
                "[url]\nhttps://example.test/source-one\n\n"
                "[label]\nSource One\n\n"
                "[text]\n# Source One\n\nUpdated notes about energy export transport routes and interconnectors.\n\n"
                "[source]\n"
                "[url]\nhttps://example.test/source-two\n\n"
                "[label]\nSource Two\n\n"
                "[text]\n# Source Two\n\nUpdated notes about shipping and bulk-terminal dependencies.\n"
            ),
        )

        staged_sources = list_staged_sources(self.root, "energy-exports")
        latest_texts = {}
        latest_kinds = {}
        for staged_source in staged_sources:
            latest_revision = latest_source_revision(self.root, staged_source)
            self.assertIsNotNone(latest_revision)
            latest_kinds[staged_source.source_ref] = latest_revision.revision_kind
            body_path = self.root / "corpus" / "energy-exports" / "gather" / "revisions" / latest_revision.markdown_relpath
            latest_texts[staged_source.source_ref] = body_path.read_text(encoding="utf-8")
        learning_context = load_learning_context(self.root, "energy-exports")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        member_export_spec = subject_research_source_collection_member_export_status_table_spec(
            scenario=scenario,
            progress=progress,
        )
        member_revision_spec = subject_research_source_collection_member_revision_table_spec(
            scenario=scenario,
            progress=progress,
        )
        merge_export_spec = subject_research_source_collection_merge_export_history_table_spec(
            scenario=scenario,
            progress=progress,
        )

        self.assertEqual(start.status_text, "LLM set-source merge-back proposal started.")
        self.assertIn("Apply the source-set source merge-back proposal", current_step)
        self.assertEqual(apply_result.status_text, "Set-source merge-back applied.")
        self.assertEqual(latest_kinds["https://example.test/source-one"], "merge")
        self.assertEqual(latest_kinds["https://example.test/source-two"], "merge")
        self.assertIn("Updated notes about energy export transport routes and interconnectors.", latest_texts["https://example.test/source-one"])
        self.assertIn("Updated notes about shipping and bulk-terminal dependencies.", latest_texts["https://example.test/source-two"])
        self.assertIn("Source-set export preview", target_text)
        self.assertEqual(len(member_export_spec.rows), 2)
        self.assertEqual(member_revision_spec.rows[0][1], "2")
        self.assertIn(("members with merge revisions", "2"), merge_export_spec.rows)
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_selected_source_collection_export_preview_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-one",
            final_url="https://example.test/source-one",
            title="Source One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Source One\n\nInitial source one notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-two",
            final_url="https://example.test/source-two",
            title="Source Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Source Two\n\nInitial source two notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-two"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            first_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            second_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Sources about energy exports and transport routes.",
            staged_source_ids=(
                str(first_result.payload["staged_source_id"]),
                str(second_result.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="energy-exports",
                canonical_title="Energy Exports",
                aliases=("Energy Exports",),
                subject_family="Energy Exports",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="energy-exports",
                            unit_kind="definition",
                            canonical_title="Cross-border transport modes",
                        ),
                        subject_id="energy-exports",
                        unit_kind="definition",
                        canonical_title="Cross-border transport modes",
                        statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
                        provenance_refs=(),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id

        more_specs = subject_more_action_specs(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_selected_source_collection_export_preview",
        )

        staged_sources = list_staged_sources(self.root, "energy-exports")
        latest_texts = {}
        latest_revisions = {}
        for staged_source in staged_sources:
            latest_revision = latest_source_revision(self.root, staged_source)
            self.assertIsNotNone(latest_revision)
            latest_revisions[staged_source.source_ref] = latest_revision
            body_path = (
                self.root
                / "corpus"
                / "energy-exports"
                / "gather"
                / "revisions"
                / latest_revision.markdown_relpath
            )
            latest_texts[staged_source.source_ref] = body_path.read_text(encoding="utf-8")
        updated_collection = next(
            item
            for item in list_source_collections(self.root, "energy-exports")
            if item.collection_id == collection.collection_id
        )
        learning_context = load_learning_context(self.root, "energy-exports")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        member_export_spec = subject_research_source_collection_member_export_status_table_spec(
            scenario=scenario,
            progress=progress,
        )
        actionable_export_spec = subject_research_source_collection_actionable_export_table_spec(
            scenario=scenario,
            progress=progress,
        )
        merge_export_spec = subject_research_source_collection_merge_export_history_table_spec(
            scenario=scenario,
            progress=progress,
        )
        export_applied_spec = subject_research_source_collection_export_applied_table_spec(
            scenario=scenario,
            progress=progress,
        )

        self.assertTrue(any(spec.key == "apply_selected_source_collection_export_preview" for spec in more_specs))
        self.assertEqual(apply_result.status_text, "Set export preview applied.")
        self.assertEqual(latest_revisions["https://example.test/source-one"].revision_kind, "merge")
        self.assertEqual(
            latest_revisions["https://example.test/source-one"].metadata.get("merge_mode"),
            "deterministic_export_preview",
        )
        self.assertEqual(latest_revisions["https://example.test/source-two"].revision_kind, "merge")
        self.assertIn("## Governed learning additions", latest_texts["https://example.test/source-one"])
        self.assertIn(
            "item note: Cross-border transport modes",
            latest_texts["https://example.test/source-one"],
        )
        self.assertIn("## Governed learning additions", latest_texts["https://example.test/source-two"])
        self.assertEqual(updated_collection.metadata.get("last_export_applied_source_count"), 2)
        self.assertEqual(updated_collection.metadata.get("last_export_applied_entry_count"), 4)
        self.assertIn("Source-set export preview", target_text)
        self.assertFalse(actionable_export_spec.enabled)
        self.assertIn(("members with export-applied revisions", "2"), merge_export_spec.rows)
        self.assertIn(("total export-applied revisions", "2"), merge_export_spec.rows)
        self.assertIn(("members aligned with current export", "2"), merge_export_spec.rows)
        self.assertTrue(all(row[2] == "aligned" for row in member_export_spec.rows))
        self.assertEqual(len(export_applied_spec.rows), 2)
        self.assertTrue(all(row[1] == "2" and row[3] == "aligned" for row in export_applied_spec.rows))
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_apply_selected_staged_source_export_preview_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-one",
            final_url="https://example.test/source-one",
            title="Source One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Source One\n\nInitial source one notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-two",
            final_url="https://example.test/source-two",
            title="Source Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Source Two\n\nInitial source two notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-two"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            first_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            second_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Sources about energy exports and transport routes.",
            staged_source_ids=(
                str(first_result.payload["staged_source_id"]),
                str(second_result.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="energy-exports",
                canonical_title="Energy Exports",
                aliases=("Energy Exports",),
                subject_family="Energy Exports",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="energy-exports",
                            unit_kind="definition",
                            canonical_title="Cross-border transport modes",
                        ),
                        subject_id="energy-exports",
                        unit_kind="definition",
                        canonical_title="Cross-border transport modes",
                        statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
                        provenance_refs=(),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id
        progress.research_selected_staged_source_id = str(first_result.payload["staged_source_id"])

        more_specs = subject_more_action_specs(
            scenario=scenario,
            progress=progress,
            phase="research",
        )
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_selected_staged_source_export_preview",
        )

        staged_sources = list_staged_sources(self.root, "energy-exports")
        revisions_by_ref = {
            staged_source.source_ref: latest_source_revision(self.root, staged_source)
            for staged_source in staged_sources
        }
        source_one_body_path = (
            self.root
            / "corpus"
            / "energy-exports"
            / "gather"
            / "revisions"
            / revisions_by_ref["https://example.test/source-one"].markdown_relpath
        )
        source_two_body_path = (
            self.root
            / "corpus"
            / "energy-exports"
            / "gather"
            / "revisions"
            / revisions_by_ref["https://example.test/source-two"].markdown_relpath
        )
        updated_collection = next(
            item
            for item in list_source_collections(self.root, "energy-exports")
            if item.collection_id == collection.collection_id
        )
        learning_context = load_learning_context(self.root, "energy-exports")
        target_text = render_subject_research_target(scenario=scenario, progress=progress)
        member_export_spec = subject_research_source_collection_member_export_status_table_spec(
            scenario=scenario,
            progress=progress,
        )
        actionable_export_spec = subject_research_source_collection_actionable_export_table_spec(
            scenario=scenario,
            progress=progress,
        )
        export_applied_spec = subject_research_source_collection_export_applied_table_spec(
            scenario=scenario,
            progress=progress,
        )

        self.assertTrue(any(spec.key == "apply_selected_staged_source_export_preview" for spec in more_specs))
        self.assertEqual(apply_result.status_text, "Selected source export preview applied.")
        self.assertEqual(revisions_by_ref["https://example.test/source-one"].revision_kind, "merge")
        self.assertEqual(
            revisions_by_ref["https://example.test/source-one"].metadata.get("merge_scope"),
            "selected_source_export_preview",
        )
        self.assertEqual(revisions_by_ref["https://example.test/source-two"].revision_kind, "capture")
        self.assertIn("## Governed learning additions", source_one_body_path.read_text(encoding="utf-8"))
        self.assertNotIn("## Governed learning additions", source_two_body_path.read_text(encoding="utf-8"))
        self.assertEqual(updated_collection.metadata.get("last_export_applied_source_count"), 1)
        self.assertEqual(updated_collection.metadata.get("last_export_applied_entry_count"), 2)
        self.assertIn("Source-set export preview", target_text)
        self.assertTrue(any(row[0] == "Source One" and row[2] == "aligned" for row in member_export_spec.rows))
        self.assertTrue(any(row[0] == "Source Two" and row[2] == "pending" and row[3] == "2" for row in member_export_spec.rows))
        self.assertEqual(actionable_export_spec.rows, (("Source Two", "pending", "2", "0", "<none>"),))
        self.assertEqual(len(export_applied_spec.rows), 1)
        self.assertEqual(export_applied_spec.rows[0][0], "Source One")
        self.assertEqual(export_applied_spec.rows[0][1], "2")
        self.assertEqual(export_applied_spec.rows[0][3], "aligned")
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_source_collection_export_history_marks_changed_targets_after_learning_updates(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-one",
            final_url="https://example.test/source-one",
            title="Source One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Source One\n\nInitial source one notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/source-two",
            final_url="https://example.test/source-two",
            title="Source Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Source Two\n\nInitial source two notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Source Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source-two"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            first_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            second_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Sources about energy exports and transport routes.",
            staged_source_ids=(
                str(first_result.payload["staged_source_id"]),
                str(second_result.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="energy-exports",
                canonical_title="Energy Exports",
                aliases=("Energy Exports",),
                subject_family="Energy Exports",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="energy-exports",
                            unit_kind="definition",
                            canonical_title="Cross-border transport modes",
                        ),
                        subject_id="energy-exports",
                        unit_kind="definition",
                        canonical_title="Cross-border transport modes",
                        statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
                        provenance_refs=(),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_selected_source_collection_export_preview",
        )
        self.assertEqual(apply_result.status_text, "Set export preview applied.")

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="energy-exports",
                canonical_title="Energy Exports",
                aliases=("Energy Exports",),
                subject_family="Energy Exports",
                summary="Updated governed learnings now emphasize LNG shipping corridors and cross-border electricity interconnectors.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="energy-exports",
                            unit_kind="definition",
                            canonical_title="Liquefied natural gas shipping corridors",
                        ),
                        subject_id="energy-exports",
                        unit_kind="definition",
                        canonical_title="Liquefied natural gas shipping corridors",
                        statement="Liquefied natural gas exports depend on marine corridors, regasification terminals, and coordinated port capacity.",
                        provenance_refs=(),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(),
            ),
        )

        refreshed_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        actionable_export_spec = subject_research_source_collection_actionable_export_table_spec(
            scenario=refreshed_scenario,
            progress=progress,
        )
        merge_export_spec = subject_research_source_collection_merge_export_history_table_spec(
            scenario=refreshed_scenario,
            progress=progress,
        )
        member_export_spec = subject_research_source_collection_member_export_status_table_spec(
            scenario=refreshed_scenario,
            progress=progress,
        )
        self.assertIn(("members with changed export targets", "2"), merge_export_spec.rows)
        self.assertTrue(all(row[2] == "changed" for row in member_export_spec.rows))
        self.assertEqual(len(actionable_export_spec.rows), 2)
        self.assertTrue(all(row[1] == "changed" and row[2] == "2" and row[3] == "2" for row in actionable_export_spec.rows))

    def test_subject_workflow_can_refresh_selected_staged_source_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        initial_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nInitial source notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Initial</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577700000,
            markdown_text="# Example Article\n\nRefreshed source notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=initial_capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")

        with patch("url_learning_capture.capture_url_learning_bundle", return_value=refreshed_capture):
            apply_result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="refresh_selected_staged_source",
                host_actions=RuntimeSubjectWorkflowHostActions(),
            )

        staged_source = list_staged_sources(self.root, "example-article")[0]
        latest_revision = latest_source_revision(self.root, staged_source)
        self.assertIsNotNone(latest_revision)
        body_path = self.root / "corpus" / "example-article" / "gather" / "revisions" / latest_revision.markdown_relpath
        learning_context = load_learning_context(self.root, "example-article")
        more_specs = subject_more_action_specs(
            scenario=scenario,
            progress=progress,
            phase="research",
        )

        self.assertEqual(apply_result.status_text, "Selected staged source refreshed.")
        self.assertEqual(latest_revision.revision_kind, "refresh")
        self.assertEqual(staged_source.revision_count, 2)
        self.assertIn("Refreshed source notes.", body_path.read_text(encoding="utf-8"))
        self.assertTrue(any(spec.key == "refresh_selected_staged_source" for spec in more_specs))
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_sync_selected_source_collection_without_importing(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-one",
            final_url="https://example.test/article-one",
            title="Article One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Article One\n\nInitial one.\n",
            bundle_files={
                "rendered.html": "<html><body>Article One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-one"},
            elements=(),
            asset_manifest=(),
        )
        capture_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-two",
            final_url="https://example.test/article-two",
            title="Article Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577601000,
            markdown_text="# Article Two\n\nInitial two.\n",
            bundle_files={
                "rendered.html": "<html><body>Article Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-two"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_one = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-one",
            final_url="https://example.test/article-one?fresh=1",
            title="Article One",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577700000,
            markdown_text="# Article One\n\nRefreshed one.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed One</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-one"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_two = CapturedUrlLearningBundle(
            requested_url="https://example.test/article-two",
            final_url="https://example.test/article-two?fresh=1",
            title="Article Two",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577701000,
            markdown_text="# Article Two\n\nRefreshed two.\n",
            bundle_files={
                "rendered.html": "<html><body>Refreshed Two</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article-two"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[capture_one, capture_two]):
            staged_one = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/article-one",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )
            staged_two = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/article-two",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

        collection = new_source_collection(
            subject_id="energy-exports",
            title="Energy Export Sources",
            description="Tracked sources for energy export topics.",
            staged_source_ids=(
                str(staged_one.payload["staged_source_id"]),
                str(staged_two.payload["staged_source_id"]),
            ),
            query_text="energy exports transport routes",
        )
        persist_source_collection(self.root, collection)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id

        with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[refreshed_one, refreshed_two]):
            apply_result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="sync_selected_source_collection",
                host_actions=RuntimeSubjectWorkflowHostActions(),
            )

        staged_sources = list_staged_sources(self.root, "energy-exports")
        latest_bodies = []
        for staged_source in staged_sources:
            latest_revision = latest_source_revision(self.root, staged_source)
            self.assertIsNotNone(latest_revision)
            self.assertEqual(latest_revision.revision_kind, "refresh")
            body_path = self.root / "corpus" / "energy-exports" / "gather" / "revisions" / latest_revision.markdown_relpath
            latest_bodies.append(body_path.read_text(encoding="utf-8"))
        learning_context = load_learning_context(self.root, "energy-exports")
        more_specs = subject_more_action_specs(
            scenario=scenario,
            progress=progress,
            phase="research",
        )

        self.assertEqual(apply_result.status_text, "Selected source set synced.")
        self.assertTrue(any("Refreshed one." in body for body in latest_bodies))
        self.assertTrue(any("Refreshed two." in body for body in latest_bodies))
        self.assertTrue(any(spec.key == "sync_selected_source_collection" for spec in more_specs))
        self.assertEqual(len(learning_context.linked_source_ids), 0)

    def test_subject_workflow_can_import_selected_staged_source_explicitly_from_gather(self) -> None:
        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/article",
            final_url="https://example.test/article?ref=final",
            title="Example Article",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Article\n\nVelocity is displacement per unit time.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Article</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/article"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/article")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-article")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        with (
            patch(
                "workstation.runtime.core.subject_host_actions.workstation_import_staged_source_action",
                return_value=type(
                    "_ImportResult",
                    (),
                    {
                        "status": "ok",
                        "message": "Imported staged source.",
                        "details": (
                            "Subject id: example-article",
                            "Staged source id: staged_source_example_123",
                        ),
                        "payload": {},
                    },
                )(),
            ) as import_mock,
        ):
            result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="import_selected_staged_source",
                host_actions=RuntimeSubjectWorkflowHostActions(),
            )

        self.assertEqual(result.status_text, "Imported the selected staged source.")
        self.assertTrue(result.reload_subjects)
        self.assertEqual(result.preferred_subject_key, "example-article")
        self.assertIn("imported staged source", "\n".join(progress.latest_receipt_lines))
        current_actions = subject_current_step_actions(scenario=scenario, progress=progress, phase="research")
        self.assertTrue(any(action.label == "Import Selected Staged Source" for action in current_actions))
        import_mock.assert_called_once()

    def test_subject_workflow_supports_shaping_publication_composition_scope(self) -> None:
        subject_id = "composition-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Composition Notes",
            source_ref="notes/composition.md",
            source_kind="markdown",
        )
        persist_learning_source(self.root, source, source_text="# Composition Notes\n")
        context = LearningContext(
            subject_id=subject_id,
            canonical_title="Composition Demo",
            aliases=("Composition Demo",),
            subject_family="Physics",
            summary="A multi-unit subject for publication composition shaping.",
            units=(
                LearningUnit(
                    unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Velocity"),
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title="Velocity",
                    statement="Velocity is displacement per unit time.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
                LearningUnit(
                    unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="relation", canonical_title="Acceleration"),
                    subject_id=subject_id,
                    unit_kind="relation",
                    canonical_title="Acceleration",
                    statement="Acceleration is the rate of change of velocity.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, context)
        self._persist_supporting_import_for_demo_context(subject_id=subject_id)

        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        review_actions = subject_review_gate_actions(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        review_labels = tuple(action.label for action in review_actions)
        self.assertIn("Preview Report Plan Diff", review_labels)
        self.assertTrue(any(label.startswith("Choose Item For Report (Velocity)") for label in review_labels))
        self.assertTrue(any(label.startswith("Exclude Item From Report (Velocity)") for label in review_labels))

        publication_actions = subject_publication_gate_actions(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        publication_labels = tuple(action.label for action in publication_actions)
        self.assertTrue(any(label.startswith("Change Report Structure (Full)") for label in publication_labels))
        self.assertTrue(any(label.startswith("Remove Support From Report (Dynamics Support)") for label in publication_labels))
        self.assertTrue(any(label.startswith("Change Support Use (dependency only)") for label in publication_labels))

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Dynamics Support")
        review_more_labels = tuple(
            spec.label
            for spec in subject_more_action_specs(
                scenario=scenario,
                progress=progress,
                phase="review",
            )
        )
        self.assertIn("Use Selected Import As Background Only", review_more_labels)
        self.assertIn("Use Selected Import As Comparison", review_more_labels)
        self.assertIn("Use Selected Import As Transcluded Support", review_more_labels)

        preview_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="preview_publication_composition",
        )
        self.assertEqual(preview_result.status_text, "Report plan preview loaded.")
        self.assertIn("- section plan: Full", "\n".join(progress.latest_receipt_lines))

        approve_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        self.assertEqual(approve_result.status_text, "Review approved for report publication.")

        cycle_unit_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_composition_unit_target",
        )
        self.assertEqual(cycle_unit_result.status_text, "Item selection updated.")

        toggle_unit_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_composition_unit",
        )
        self.assertEqual(toggle_unit_result.status_text, "Item scope updated.")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self.assertEqual(scenario.composition_included_unit_count, 1)

        cycle_sections_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_publication_section_plan",
        )
        self.assertEqual(cycle_sections_result.status_text, "Report section plan updated.")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self.assertEqual(scenario.composition_section_count, 3)

        set_usage_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="set_selected_publication_import_usage_comparison",
        )
        self.assertEqual(set_usage_result.status_text, "Support use updated.")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        updated = self._latest_subject_composition(scenario=scenario)
        self.assertIn("comparison", tuple(updated.import_usage_by_id.values()))

        review_specs = subject_action_specs(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertFalse(any(label.startswith("Change Diff Baseline") for label in (spec.label for spec in review_specs)))

        publication_specs = subject_action_specs(
            scenario=scenario,
            progress=progress,
            phase="publication",
        )
        publication_spec_labels = tuple(spec.label for spec in publication_specs)
        self.assertIn("Preview Report Plan Diff", publication_spec_labels)
        self.assertFalse(any(label.startswith("Change Diff Baseline") for label in publication_spec_labels))

        cycle_baseline_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_publication_diff_baseline",
        )
        self.assertEqual(cycle_baseline_result.status_text, "Report plan diff baseline updated.")
        self.assertIn("- selected baseline: Previous Revision", "\n".join(progress.latest_receipt_lines))

        diff_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="preview_publication_composition_diff",
        )
        self.assertEqual(diff_result.status_text, "Report plan diff loaded.")
        diff_text = "\n".join(progress.latest_receipt_lines)
        self.assertIn("- baseline mode: Previous Revision", diff_text)
        self.assertIn("- baseline: previous revision (", diff_text)
        self.assertIn("- removed sections: none", diff_text)
        self.assertIn("dependency only -> comparison", diff_text)

        cycle_snapshot_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_publication_diff_baseline",
        )
        self.assertEqual(cycle_snapshot_result.status_text, "Report plan diff baseline updated.")

        snapshot_diff_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="preview_publication_composition_diff",
        )
        self.assertEqual(snapshot_diff_result.status_text, "Report plan diff loaded.")
        snapshot_diff_text = "\n".join(progress.latest_receipt_lines)
        self.assertIn("- baseline mode: Current Subject Snapshot", snapshot_diff_text)
        self.assertIn("- baseline: current subject snapshot", snapshot_diff_text)
        self.assertIn("- removed units: Velocity", snapshot_diff_text)
        review_text = render_subject_workspace(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertIn("How To Use Review", review_text)
        self.assertIn("- 1. Compare Maintained Files", review_text)
        self.assertIn("- 2. Refresh Report Plan", review_text)
        self.assertIn("- 4. Change Diff Baseline", review_text)
        self.assertIn("- 9. Approve For Report", review_text)
        self.assertIn("- diff baseline: Current Subject Snapshot", review_text)

    def test_subject_workflow_renders_and_updates_report_scope_tree(self) -> None:
        subject_id = self._persist_demo_context()
        self._persist_supporting_import_for_demo_context(subject_id=subject_id)
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        tree_text = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        detail_text = render_subject_report_scope_detail(scenario=scenario, progress=progress)

        self.assertIn("Items (1)", tree_text)
        self.assertIn("Support (1)", tree_text)
        self.assertIn("Report sections (6)", tree_text)
        self.assertIn(">     [-] Velocity", tree_text)
        self.assertIn("Velocity", detail_text)
        self.assertIn("This item must stay in the report.", detail_text)

        selected = move_report_scope_cursor(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(selected)
        self.assertEqual(selected.item_kind, "import")

        tree_text = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        detail_text = render_subject_report_scope_detail(scenario=scenario, progress=progress)
        self.assertIn(">     [x] Dynamics Support [dependency only]", tree_text)
        self.assertIn("Current report use: dependency only", detail_text)

        toggle_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="toggle_selected_report_scope_item",
        )
        self.assertEqual(toggle_result.status_text, "Report import scope updated.")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        tree_text = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertIn(">     [ ] Dynamics Support", tree_text)

    def test_subject_workflow_marks_question_unit_as_excluded_from_report_scope(self) -> None:
        subject_id = self._persist_demo_context()
        source = new_learning_source(
            subject_id=subject_id,
            title="Python Ability Notes",
            source_ref="notes/python-ability.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Python Ability\n\nHow do you calculate velocity in Python?\n",
        )
        ability = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="ability",
                canonical_title="Python Ability",
            ),
            subject_id=subject_id,
            unit_kind="ability",
            canonical_title="Python Ability",
            statement="How do you calculate velocity in Python?",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        context = load_learning_context(self.root, subject_id)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=context.subject_id,
                canonical_title=context.canonical_title,
                aliases=context.aliases,
                subject_family=context.subject_family,
                summary=context.summary,
                units=tuple([*context.units, ability]),
                linked_source_ids=tuple([*context.linked_source_ids, source.source_id]),
                linked_skill_ids=context.linked_skill_ids,
                linked_document_section_ids=context.linked_document_section_ids,
                applied_delta_ids=context.applied_delta_ids,
                governance_status=context.governance_status,
                metadata=context.metadata,
            ),
        )

        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)
        tree_text = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertIn("[q] Python Ability [question]", tree_text)
        self.assertNotIn(">   [q] Python Ability [question]", tree_text)
        composition = self._latest_subject_composition(scenario=scenario)
        self.assertNotIn(ability.unit_id, composition.included_unit_ids)
        self.assertIn(ability.unit_id, composition.excluded_unit_ids)

    def test_subject_workflow_hold_and_release_reorders_report_scope_units_as_collapsed_block(self) -> None:
        subject_id = self._persist_report_scope_reorder_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Beta")
        hold_beta = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_beta.status_text, "Held report-scope item for reordering.")

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Delta")
        hold_delta = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_delta.status_text, "Held report-scope item for reordering.")

        composition_before_preview = self._latest_subject_composition(scenario=scenario)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Delta")
        preview_selected = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=-1,
        )
        self.assertIsNotNone(preview_selected)
        preview_tree = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertIn("h   [x] Beta", preview_tree)
        self.assertIn("h   [x] Delta", preview_tree)
        self.assertLess(preview_tree.find("Beta"), preview_tree.find("Alpha"))
        self.assertLess(preview_tree.find("Delta"), preview_tree.find("Alpha"))
        self.assertLess(preview_tree.find("Beta"), preview_tree.find("Delta"))
        self.assertLess(preview_tree.find("Alpha"), preview_tree.find("Gamma"))

        composition_during_preview = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(composition_during_preview.included_unit_ids, composition_before_preview.included_unit_ids)

        release_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="release_held_report_scope_items",
        )
        self.assertEqual(release_result.status_text, "Report-scope order updated.")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        released_tree = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertNotIn("h   [x] Beta", released_tree)
        self.assertLess(released_tree.find("Beta"), released_tree.find("Alpha"))
        self.assertLess(released_tree.find("Delta"), released_tree.find("Alpha"))
        updated = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(
            updated.included_unit_ids,
            (
                stable_learning_unit_id(subject_id=subject_id, unit_kind="relation", canonical_title="Beta"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="misconception", canonical_title="Delta"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Alpha"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="ability", canonical_title="Gamma"),
            ),
        )
        self.assertEqual(
            tuple(updated.metadata.get("report_scope_unit_order_ids", ())),
            updated.included_unit_ids,
        )

    def test_subject_workflow_hold_and_release_reorders_non_adjacent_units_as_collapsed_block(self) -> None:
        subject_id = self._persist_report_scope_reorder_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Alpha")
        hold_alpha = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_alpha.status_text, "Held report-scope item for reordering.")

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Gamma")
        hold_gamma = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_gamma.status_text, "Held report-scope item for reordering.")

        composition_before_preview = self._latest_subject_composition(scenario=scenario)

        selected_before_preview = move_report_scope_cursor(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=-1,
        )
        self.assertIsNotNone(selected_before_preview)
        self.assertIn("Gamma", render_subject_report_scope_detail(scenario=scenario, progress=progress))
        preview_selected = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(preview_selected)
        preview_tree = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertIn("h   [x] Alpha", preview_tree)
        self.assertIn("h   [x] Gamma", preview_tree)
        self.assertLess(preview_tree.find("Beta"), preview_tree.find("Alpha"))
        self.assertLess(preview_tree.find("Alpha"), preview_tree.find("Gamma"))
        self.assertLess(preview_tree.find("Gamma"), preview_tree.find("Delta"))
        self.assertLess(preview_tree.find("Beta"), preview_tree.find("Delta"))

        composition_during_preview = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(composition_during_preview.included_unit_ids, composition_before_preview.included_unit_ids)

        release_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="release_held_report_scope_items",
        )
        self.assertEqual(release_result.status_text, "Report-scope order updated.")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        updated = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(
            updated.included_unit_ids,
            (
                stable_learning_unit_id(subject_id=subject_id, unit_kind="relation", canonical_title="Beta"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Alpha"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="ability", canonical_title="Gamma"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="misconception", canonical_title="Delta"),
            ),
        )
        self.assertEqual(
            tuple(updated.metadata.get("report_scope_unit_order_ids", ())),
            updated.included_unit_ids,
        )

    def test_subject_workflow_navigation_stays_linear_while_held_item_movement_requires_preview_action(self) -> None:
        subject_id = self._persist_report_scope_reorder_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Alpha")
        hold_alpha = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_alpha.status_text, "Held report-scope item for reordering.")

        selected = move_report_scope_cursor(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(selected)
        detail_after_move = render_subject_report_scope_detail(scenario=scenario, progress=progress)
        self.assertNotIn("Alpha", detail_after_move)
        self.assertIn("Gamma", detail_after_move)
        self.assertEqual(progress.report_scope_preview_order_ids, [])

        entries = _report_scope_entries(self.root, scenario=scenario, progress=progress)
        alpha_entry = next(item for item in entries if item.label == "Alpha")
        _set_report_scope_cursor_to_entry_id(progress, entries, alpha_entry.entry_id)
        preview_selected = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(preview_selected)
        preview_tree = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertLess(preview_tree.find("Beta"), preview_tree.find("Alpha"))
        self.assertEqual(
            tuple(progress.report_scope_preview_order_ids),
            (
                stable_learning_unit_id(subject_id=subject_id, unit_kind="relation", canonical_title="Beta"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Alpha"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="ability", canonical_title="Gamma"),
                stable_learning_unit_id(subject_id=subject_id, unit_kind="misconception", canonical_title="Delta"),
            ),
        )

    def test_subject_workflow_hold_cannot_cross_report_scope_lanes(self) -> None:
        subject_id = self._persist_demo_context()
        self._persist_supporting_import_for_demo_context(subject_id=subject_id)
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        hold_unit = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(hold_unit.status_text, "Held report-scope item for reordering.")

        selected = move_report_scope_cursor(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(selected)
        self.assertNotIn("Velocity", render_subject_report_scope_detail(scenario=scenario, progress=progress))
        no_preview = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNone(no_preview)

        cross_lane = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self.assertEqual(
            cross_lane.status_text,
            "Held report-scope items must stay within one lane. Release the current held items first.",
        )

    def test_subject_workflow_hold_and_release_reorders_report_scope_imports(self) -> None:
        subject_id = self._persist_demo_context()
        self._persist_multiple_supporting_imports_for_subject(subject_id=subject_id)
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Import Alpha")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Import Gamma")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Import Gamma")
        preview_selected = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=1,
        )
        self.assertIsNotNone(preview_selected)
        preview_tree = render_subject_report_scope_tree(scenario=scenario, progress=progress)
        self.assertLess(preview_tree.find("Import Beta"), preview_tree.find("Import Alpha"))
        self.assertLess(preview_tree.find("Import Alpha"), preview_tree.find("Import Gamma"))

        release_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="release_held_report_scope_items",
        )
        self.assertEqual(release_result.status_text, "Report-scope order updated.")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        updated = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(
            updated.selected_subject_import_ids,
            (
                next(import_id for import_id in updated.selected_subject_import_ids if "import-beta" in import_id),
                next(import_id for import_id in updated.selected_subject_import_ids if "import-alpha" in import_id),
                next(import_id for import_id in updated.selected_subject_import_ids if "import-gamma" in import_id),
            ),
        )
        self.assertEqual(
            tuple(updated.metadata.get("report_scope_import_order_ids", ())),
            updated.selected_subject_import_ids,
        )

    def test_subject_workflow_hold_and_release_reorders_report_scope_sections(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)

        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Analysis")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Appendix")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="hold_selected_report_scope_item",
        )
        self._move_report_scope_selection_to_label(scenario=scenario, progress=progress, label="Appendix")
        preview_selected = preview_move_held_report_scope_items(
            self.root,
            scenario=scenario,
            progress=progress,
            delta=-1,
        )
        self.assertIsNotNone(preview_selected)

        release_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="release_held_report_scope_items",
        )
        self.assertEqual(release_result.status_text, "Report-scope order updated.")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        updated = self._latest_subject_composition(scenario=scenario)
        self.assertEqual(
            updated.section_ids,
            (
                "report-summary",
                "report-analysis",
                "report-appendix",
                "report-definitions",
                "report-implementation",
                "report-evidence",
            ),
        )

    def test_subject_workflow_supports_pin_create_approve_and_retire_import_flow(self) -> None:
        target_subject_id = self._persist_demo_context()
        source_subject_id = self._persist_importable_source_context()

        scenarios = default_subject_scenarios(self.root)
        source_scenario = next(item for item in scenarios if item.subject_id == source_subject_id)
        target_scenario = next(item for item in scenarios if item.subject_id == target_subject_id)
        source_progress = new_subject_progress()
        target_progress = new_subject_progress()

        pin_result = apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="open_context",
        )
        self.assertEqual(pin_result.status_text, "Subject context opened.")
        pin_result = apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="pin_import_source",
        )
        self.assertEqual(pin_result.status_text, "Import source selected.")
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)
        self.assertEqual(staging.source_subject_id, source_subject_id)

        apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="open_context",
        )

        research_specs = subject_action_specs(
            scenario=target_scenario,
            progress=target_progress,
            phase="research",
            can_capture_assistant=False,
            import_staging=staging,
        )
        self.assertEqual(research_specs[1].label, "Create Import From Selected Source")

        create_result = apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="create_subject_import",
            import_staging=staging,
        )
        self.assertTrue(create_result.reload_subjects)
        self.assertEqual(create_result.next_phase, "review")
        self.assertIsNone(load_subject_import_staging(self.root))

        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        self.assertEqual(target_scenario.pending_import_count, 1)
        self.assertEqual(target_scenario.reasoning_import_count, 0)
        self.assertTrue(target_scenario.pending_import_preview_lines)

        review_specs = subject_action_specs(
            scenario=target_scenario,
            progress=target_progress,
            phase="review",
        )
        self.assertEqual(review_specs[1].label, "Preview Pending Import")
        self.assertEqual(review_specs[2].label, "Approve Import")
        self.assertEqual(review_specs[3].label, "Reject Import")

        approve_result = apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="approve_subject_import",
        )
        self.assertEqual(approve_result.status_text, "Subject import approved.")

        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        self.assertEqual(target_scenario.pending_import_count, 0)
        self.assertEqual(target_scenario.reasoning_import_count, 1)

        research_specs = subject_action_specs(
            scenario=target_scenario,
            progress=target_progress,
            phase="research",
            can_capture_assistant=False,
        )
        self.assertEqual(research_specs[1].label, "Retire Active Import")

        retire_result = apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="retire_subject_import",
        )
        self.assertEqual(retire_result.status_text, "Subject import retired.")

        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        self.assertEqual(target_scenario.reasoning_import_count, 0)

    def test_subject_workflow_supports_widening_and_inspecting_staged_import_scope(self) -> None:
        target_subject_id = self._persist_demo_context()
        source_subject_id = self._persist_importable_source_context()

        source_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == source_subject_id)
        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        source_progress = new_subject_progress()
        target_progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="pin_import_source",
        )
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)
        self.assertEqual(staging.selection_profile, "units_only")
        self.assertIn("- import scope: units only", "\n".join(source_progress.latest_receipt_lines))
        self.assertIn("- scope step: 1 of 3", "\n".join(source_progress.latest_receipt_lines))
        self.assertIn("- staged scope: 1 units", "\n".join(source_progress.latest_receipt_lines))

        source_specs = subject_action_specs(
            scenario=source_scenario,
            progress=source_progress,
            phase="research",
            import_staging=staging,
        )
        self.assertEqual(source_specs[1].label, "Expand Import Scope")

        widen_once = apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="advance_import_selection",
            import_staging=staging,
        )
        self.assertEqual(widen_once.status_text, "Import source scope expanded.")
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)
        self.assertEqual(staging.selection_profile, "units_and_skills")

        widen_twice = apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="advance_import_selection",
            import_staging=staging,
        )
        self.assertEqual(widen_twice.status_text, "Import source scope expanded.")
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)
        self.assertEqual(staging.selection_profile, "full_context")

        target_text = render_subject_research_target(
            scenario=target_scenario,
            progress=target_progress,
            import_staging=staging,
        )
        self.assertIn("Selected Import Source", target_text)
        self.assertIn("- import scope: full context", target_text)
        self.assertIn("- staged scope: 1 units, 1 skills, 1 sources", target_text)
        self.assertIn("Dynamics Import Notes", target_text)
        workspace_text = render_subject_workspace(
            scenario=target_scenario,
            progress=target_progress,
            phase="research",
            import_staging=staging,
        )
        self.assertIn("Selected Import Source", workspace_text)
        self.assertIn("expand the import scope here, then switch to another subject and create the import there", workspace_text)
        self.assertIn("- staged skills: force-skill", workspace_text)

        apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="open_context",
        )
        create_result = apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="create_subject_import",
            import_staging=staging,
        )
        self.assertEqual(create_result.next_phase, "review")

        subject_imports = list_subject_imports(self.root, target_subject_id)
        self.assertEqual(len(subject_imports), 1)
        self.assertEqual(subject_imports[0].metadata.get("selection_profile"), "full_context")
        self.assertEqual(subject_imports[0].imported_skill_ids, ("force-skill",))
        self.assertEqual(len(subject_imports[0].imported_source_ids), 1)

    def test_subject_workflow_research_current_step_surfaces_import_shortcuts(self) -> None:
        target_subject_id = self._persist_demo_context()
        source_subject_id = self._persist_importable_source_context()

        source_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == source_subject_id)
        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        source_progress = new_subject_progress()
        target_progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="open_context",
        )
        source_actions = subject_current_step_actions(
            scenario=source_scenario,
            progress=source_progress,
            phase="research",
        )
        source_action_keys = [action.key for action in source_actions]
        source_action_labels = [action.label for action in source_actions]
        source_action_kinds = [action.kind for action in source_actions]
        self.assertEqual(source_action_keys[0], "compare_projections")
        self.assertIn("pin_import_source", source_action_keys)
        self.assertIn("itemize", source_action_keys)
        self.assertIn("toggle_review_preview", source_action_keys)
        self.assertIn("phase_nav", source_action_kinds)
        self.assertIn("Check Maintained Files", source_action_labels)
        self.assertIn("Select As Import Source", source_action_labels)
        self.assertIn("Itemize: Generate Itemization", source_action_labels)
        self.assertIn("Preview Maintained Files", source_action_labels)

        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="pin_import_source",
        )
        staging = load_subject_import_staging(self.root)
        self.assertIsNotNone(staging)

        apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="open_context",
        )
        target_actions = subject_current_step_actions(
            scenario=target_scenario,
            progress=target_progress,
            phase="research",
            import_staging=staging,
        )
        self.assertEqual(
            [action.key for action in target_actions],
            ["create_subject_import", "clear_import_staging"],
        )
        self.assertEqual(
            [action.label for action in target_actions],
            ["Create Import From Selected Source", "Clear Import Source"],
        )

    def test_subject_workflow_can_reject_pending_subject_import(self) -> None:
        target_subject_id = self._persist_demo_context()
        source_subject_id = self._persist_importable_source_context()

        source_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == source_subject_id)
        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        source_progress = new_subject_progress()
        target_progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=source_scenario,
            progress=source_progress,
            action_key="pin_import_source",
        )
        staging = load_subject_import_staging(self.root)
        apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="open_context",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="create_subject_import",
            import_staging=staging,
        )

        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        reject_result = apply_subject_action(
            root_path=self.root,
            scenario=target_scenario,
            progress=target_progress,
            action_key="reject_subject_import",
        )
        self.assertEqual(reject_result.status_text, "Subject import rejected.")

        target_scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == target_subject_id)
        self.assertEqual(target_scenario.pending_import_count, 0)
        self.assertEqual(target_scenario.reasoning_import_count, 0)

    def test_subject_workflow_requires_fresh_review_before_rebuild_even_if_publication_exists(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="build_report",
        )

        rebuilt = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        fresh_progress = new_subject_progress()

        publication_specs = subject_action_specs(scenario=rebuilt, progress=fresh_progress, phase="publication")
        self.assertEqual(publication_specs[1].label, "Rebuild Report")
        self.assertFalse(publication_specs[1].enabled)

        blocked_rebuild = apply_subject_action(
            root_path=self.root,
            scenario=rebuilt,
            progress=fresh_progress,
            action_key="build_report",
        )
        self.assertIn("Approve review or lock publication inputs", blocked_rebuild.status_text)

    def test_subject_workflow_persists_review_and_publication_gate_progress(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )

        persisted_path = persist_subject_progress(self.root, subject_id, progress)
        self.assertEqual(persisted_path, subject_progress_path(self.root, subject_id))
        self.assertTrue(Path(persisted_path).is_file())

        reloaded = load_subject_progress(self.root, subject_id)
        self.assertTrue(reloaded.context_opened)
        self.assertEqual(reloaded.comparison_status, "aligned")
        self.assertTrue(reloaded.review_approved)
        self.assertTrue(reloaded.publication_locked)
        self.assertFalse(reloaded.release_review_completed)

        scenarios = default_subject_scenarios(self.root)
        progress_map = load_subject_progress_map(self.root, scenarios)
        self.assertTrue(progress_map[subject_id].publication_locked)

    def test_subject_workflow_marks_invalid_subject_typ_as_drifted(self) -> None:
        if shutil.which("typst") is None:
            self.skipTest("typst is not installed")
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_context",
        )
        Path(scenario.subject_typst_path).write_text(
            "\n".join(
                [
                    "= Kinematics Demo",
                    "",
                    "== Definitions <definitions>",
                    "",
                    "=== Velocity <unit-unit_velocity>",
                    "",
                    "- Statement: Velocity is displacement per unit time.",
                    "#set page(margin: (",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        compare_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="compare_projections",
        )

        self.assertEqual(compare_result.status_text, "Projection comparison found drift.")
        self.assertEqual(progress.comparison_status, "drifted")
        self.assertIn("- subject.typ typst validation: error", "\n".join(progress.comparison_receipt_lines))
        self.assertIn("- verdict: drifted", "\n".join(progress.comparison_receipt_lines))

        current_actions = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertEqual(len(current_actions), 1)
        self.assertEqual(current_actions[0].label, "Gather: Check Maintained Files")

    def test_subject_workflow_surfaces_failed_report_build_validation(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )

        with patch(
            "workstation.subject.core.subject_workflow.materialize_report_publication_from_learning_context",
            return_value={
                "publication_id": "pub_demo",
                "composition_id": "pubcomp_demo",
                "build_id": "pubbuild_demo",
                "build_path": str(self.root / "corpus" / "demo" / "publications" / "builds" / "pubbuild_demo.json"),
                "validation_status": "error",
                "validation_errors": ("Typst compile failed: unknown variable cg",),
                "section_count": 1,
                "claim_count": 1,
                "source_count": 1,
                "entity_count": 0,
                "xref_count": 0,
                "review_count": 0,
                "import_count": 0,
                "imported_subject_count": 0,
                "publication_path": str(self.root / "corpus" / "demo" / "publications" / "pub_demo.json"),
                "output_paths": {
                    "md": "",
                    "typ": str(self.root / "corpus" / "demo" / "publications" / "outputs" / "report.typ"),
                    "pdf": "",
                },
            },
        ):
            build_result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="build_report",
            )

        self.assertEqual(
            build_result.status_text,
            "Report build failed [error]: Typst compile failed: unknown variable cg",
        )
        self.assertTrue(build_result.reload_subjects)
        self.assertIn("- validation: error", "\n".join(progress.build_receipt_lines))
        self.assertIn("- rendered pdf: <none> (<missing>)", "\n".join(progress.build_receipt_lines))

    def test_subject_workflow_build_step_has_no_secondary_preview_before_first_build(self) -> None:
        subject_id = self._persist_demo_context()
        scenario, progress = self._progress_with_current_report_plan(subject_id=subject_id)
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="approve_review",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="lock_publication",
        )

        current_actions = subject_current_step_actions(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertEqual(current_actions[0].label, "Publication: Build Report")
        self.assertEqual(len(current_actions), 1)

    def test_subject_workflow_rejects_retired_typst_preview_action(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="preview_publication_typst",
        )
        self.assertEqual(
            result.status_text,
            "Typst-source preview is retired. Use Preview report.pdf or Open Release Folder.",
        )
        self.assertFalse(result.open_paths)

    def test_subject_workflow_stages_confirms_and_cancels_assistant_capture(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        host_actions = RuntimeSubjectWorkflowHostActions()
        assistant_markdown = "\n".join(
            [
                "# Velocity Notes",
                "",
                "- Velocity is displacement per unit time.",
                "- SI unit: m/s.",
            ]
        )

        stage_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="stage_assistant_capture",
            assistant_message_text=assistant_markdown,
            subject_title_override="Kinematics Demo",
            host_actions=host_actions,
        )
        self.assertEqual(stage_result.status_text, "Gather source staging preview ready.")
        self.assertTrue(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Gather Source Staging Preview")
        self.assertIn("- proposed subject: Kinematics Demo", progress.latest_receipt_lines)

        cancel_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cancel_assistant_capture",
            host_actions=host_actions,
        )
        self.assertEqual(cancel_result.status_text, "Gather source staging canceled.")
        self.assertFalse(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Gather Source Staging Canceled")

        progress.review_approved = True
        progress.publication_locked = True
        progress.comparison_status = "aligned"
        progress.projections_compared = True

        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="stage_assistant_capture",
            assistant_message_text=assistant_markdown,
            subject_title_override="Kinematics Demo",
            host_actions=host_actions,
        )
        confirm_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="confirm_assistant_capture",
            host_actions=host_actions,
        )
        self.assertEqual(confirm_result.status_text, "Gather source staged.")
        self.assertTrue(confirm_result.reload_subjects)
        self.assertEqual(confirm_result.preferred_subject_key, subject_id)
        self.assertFalse(subject_has_pending_research_capture(progress))
        self.assertEqual(progress.latest_receipt_title, "Gather Source Staging Receipt")
        self.assertTrue(progress.review_approved)
        self.assertTrue(progress.publication_locked)
        self.assertEqual(progress.comparison_status, "aligned")
        self.assertTrue(progress.projections_compared)

        refreshed = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        self.assertGreaterEqual(refreshed.staged_source_count, scenario.staged_source_count + 1)
        self.assertEqual(refreshed.source_count, scenario.source_count)
        self.assertEqual(refreshed.delta_count, scenario.delta_count)

    def test_subject_workflow_can_switch_publication_output_mode_to_exact_draft(self) -> None:
        subject_id = self._persist_demo_context()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()

        for action_key in (
            "open_context",
            "generate_itemization",
            "refresh_review_composition",
            "compare_projections",
            "refresh_publication_composition",
        ):
            result = apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key=action_key,
            )
            self.assertTrue(collapse_ws(result.status_text))
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)

        result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="cycle_publication_output_mode",
        )

        self.assertEqual(result.status_text, "Publication output mode updated.")
        self.assertEqual(progress.latest_receipt_title, "Report Plan")
        self.assertIn("Exact Draft", "".join(progress.latest_receipt_lines))

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        latest_composition = self._all_subject_publication_compositions(subject_id)[-1]
        self.assertEqual(latest_composition.composition_id, scenario.composition_id)
        self.assertEqual(latest_composition.publication_type, "exact_draft")
        self.assertEqual(latest_composition.section_ids, ())

        gate_actions = subject_publication_gate_actions(
            scenario=scenario,
            progress=progress,
            phase="review",
        )
        self.assertTrue(any("Change Output Style (Exact Draft)" == action.label for action in gate_actions))


if __name__ == "__main__":
    unittest.main()
