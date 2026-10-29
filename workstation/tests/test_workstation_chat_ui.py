# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import asyncio
from dataclasses import replace
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from decision_review import list_decision_review_items
from decision_review_constructs import (
    TransformationConstructCandidate,
    deterministic_transformation_construct_candidates_from_itemized_item,
    persist_transformation_construct_candidates,
    stable_transformation_construct_candidate_id,
)
from itemize import list_itemized_subject_items, materialize_itemization_session
from learning_context import (
    LearningContext,
    LearningUnit,
    new_subject_import,
    new_learning_delta,
    new_learning_source,
    persist_subject_import,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from publication_projection import materialize_report_publication_from_learning_context
from review_composition import list_review_items
from dst import DST_SOURCE_ROOT, discovery_result_from_fixture, normalized_case_from_fixture, run_dst_pipeline_from_fixture
from semantic_text import collapse_ws
from gather_sources import (
    list_source_collections,
    list_staged_sources,
    new_source_collection,
    new_source_revision,
    new_staged_source,
    persist_source_collection,
    persist_source_revision,
    persist_staged_source,
)
from workstation.subject.core.subject_workflow import (
    _latest_publication_composition,
    _subject_transformation_construct_candidates,
    apply_subject_action,
    default_subject_scenarios,
    load_subject_progress,
    move_report_scope_cursor,
    new_subject_progress,
    persist_subject_progress,
    render_subject_report_scope_detail,
    subject_draft_model_relation_selection_list_specs,
    subject_draft_model_transition_source_select_spec,
    subject_draft_model_transition_target_select_spec,
)
from workstation.ui.textual.chat_ui import (
    _FocusableTextualDataTable,
    _FocusableTextualLog,
    _FocusableTextualOptionList,
    _FocusableTextualTree,
    _TextualTabContentPayload,
    _TextualWorkstationChatApp,
    _copy_text_to_system_clipboard,
    _draft_evidence_mode_select_id,
    _draft_model_construct_lane_select_id,
    _draft_model_relation_label_id,
    _draft_model_relation_selection_list_id,
    _draft_model_construct_sort_select_id,
    _draft_model_transition_source_select_id,
    _draft_model_transition_target_select_id,
    _draft_model_lens_tab_id,
    _draft_model_lens_tabs_id,
    _draft_model_policy_profile_select_id,
    _draft_decision_included_switch_id,
    _draft_render_kind_select_id,
    _draft_semantic_kind_select_id,
    _draft_transform_mode_select_id,
    _itemize_decision_role_select_id,
    _itemize_hold_switch_id,
    _publication_diff_baseline_select_id,
    _publication_build_artifacts_table_id,
    _publication_build_receipt_table_id,
    _publication_composition_unit_included_switch_id,
    _publication_composition_unit_target_select_id,
    _publication_import_included_switch_id,
    _publication_import_target_select_id,
    _publication_import_usage_select_id,
    _publication_latest_receipt_table_id,
    _publication_output_mode_select_id,
    _publication_section_included_switch_id,
    _publication_section_target_select_id,
    _publication_section_plan_select_id,
    _research_source_collection_membership_switch_id,
    _research_source_collection_actionable_export_table_id,
    _research_source_collection_export_applied_table_id,
    _research_source_collection_member_export_status_table_id,
    _research_source_collection_select_id,
    _research_source_collection_member_revision_table_id,
    _research_source_collection_merge_export_history_table_id,
    _research_source_change_summary_table_id,
    _research_source_revision_baseline_select_id,
    _research_source_revision_history_table_id,
    _review_composition_unit_included_switch_id,
    _review_composition_unit_target_select_id,
    _review_comparison_history_table_id,
    _review_latest_receipt_table_id,
    _review_publication_diff_baseline_select_id,
    _review_publication_output_mode_select_id,
    _review_publication_section_included_switch_id,
    _review_publication_section_target_select_id,
    _review_publication_section_plan_select_id,
    _research_detail_llm_button_id,
    _research_detail_manual_rephrase_button_id,
    _research_sources_llm_button_id,
    _research_sources_manual_rephrase_button_id,
    _review_detail_llm_button_id,
    _review_detail_manual_rephrase_button_id,
    _scroll_window_to_end,
    _subject_action_button_ids,
    _subject_gate_panel_id,
    _subject_gate_summary_id,
    _subject_gate_status_table_id,
    _subject_header_subject_id,
    _subject_last_action_panel_id,
    _subject_nav_button_id,
    _WorkstationChatPaneState,
    configure_textual_subject_workflow_client_factory,
    _scroll_window_linewise,
    _textual_copy_selected_text_from_widget,
    _textual_scroll_to_end,
    _textual_copy_text,
    _textual_copy_selected_text,
    _window_scroll_cursor_position,
    _textual_pane_toggle_button_id,
    _textual_scroll_line_into_view,
    workstation_chat_apply_prompt_suggestion,
    workstation_chat_assistant_block_text,
    workstation_chat_activity_strip_text,
    workstation_chat_completion_candidates,
    workstation_chat_context,
    workstation_chat_help_text,
    workstation_chat_history_path,
    workstation_chat_inline_completion,
    workstation_chat_live_suggestions,
    workstation_chat_named_block_text,
    workstation_chat_prepare_last_assistant_resolution,
    workstation_chat_prepare_markdown_prompt,
    workstation_chat_prompt_target_plan,
    workstation_chat_routed_llm_prompt_text,
    workstation_chat_resume_research_prompt,
    workstation_chat_suggestions,
    workstation_chat_ui_supported,
)
from workstation.foundation.models import WorkstationDelegationEscalationRequest
from workstation.runtime.core.session import launch_workstation_session
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.runtime.core.workstation_core import workstation_learn_markdown_action
from workstation.shell.core.workstation_shell_client import InProcessWorkstationShellClient
from workstation.skills.core.skill_management import import_workstation_skill_file
from workstation.skills.planning.skill_home import resolve_workstation_skill_home
from workstation.subject.service.subject_workflow_client import InProcessSubjectWorkflowClient
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService


def _itemization_runtime_provider(controller: object) -> SimpleNamespace:
    return SimpleNamespace(
        bootstrap_controller=lambda **_kwargs: (SimpleNamespace(), controller)
    )


def _table_rows(table: object) -> list[tuple[str, ...]]:
    return [
        tuple(str(cell) for cell in table.get_row_at(index))
        for index in range(int(getattr(table, "row_count", 0) or 0))
    ]


def _table_text(table: object) -> str:
    return "\n".join(" | ".join(row) for row in _table_rows(table))


def _tree_text(tree: object) -> str:
    labels: list[str] = []
    stack = list(getattr(getattr(tree, "root", None), "children", ()) or ())
    while stack:
        node = stack.pop(0)
        labels.append(str(getattr(node, "label", "") or ""))
        stack[0:0] = list(getattr(node, "children", ()) or ())
    return "\n".join(labels)


class WorkstationChatUiTests(unittest.TestCase):
    def setUp(self) -> None:
        configure_textual_subject_workflow_client_factory(
            lambda: InProcessSubjectWorkflowClient(
                service=SubjectWorkflowApiService(
                    host_actions=RuntimeSubjectWorkflowHostActions(),
                )
            )
        )
        self.tempdir = tempfile.TemporaryDirectory()
        self.enterContext(
            patch.dict(
                "os.environ",
                {"WORKSTATION_HOME": str(Path(self.tempdir.name) / "workstation-home")},
                clear=False,
            )
        )
        self.root = Path(self.tempdir.name) / "root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        (self.workspace / "trials").mkdir(parents=True, exist_ok=True)
        (self.workspace / "src").mkdir(parents=True, exist_ok=True)
        (self.workspace / "exports").mkdir(parents=True, exist_ok=True)
        (self.workspace / "trials" / "python.skill.yaml").write_text("schema: bssc_skill.v2\nkind: ability\ntitle: Demo Skill\n")
        (self.workspace / "src" / "demo.py").write_text("class BSSCController:\n    pass\n")
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            initial_task="Test workstation chat UI helpers.",
        )
        (self.root / "SKILLS.json").write_text(
            json.dumps(
                {
                    "skills": [
                        {"title": "Workstation Repo Search", "source_kind": "builtin_workstation"},
                        {
                            "title": "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
                            "source_kind": "attached_skill_store",
                        },
                        {
                            "title": "Python Commands 03 — Write Text File / Python Commands 03 Write Text File",
                            "source_kind": "attached_skill_store",
                        },
                    ]
                }
            )
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_focusable_textual_data_table_routes_research_source_navigation_keys(self) -> None:
        move_calls: list[int] = []
        fake_app = SimpleNamespace(
            _move_research_source_cursor=lambda delta, calls=move_calls: calls.append(delta) or True,
        )
        fake_table = SimpleNamespace(id="subject_sources_panel", app=fake_app)
        event_up = SimpleNamespace(key="up", stop=lambda: None)
        event_down = SimpleNamespace(key="down", stop=lambda: None)

        _FocusableTextualDataTable.on_key(fake_table, event_up)
        _FocusableTextualDataTable.on_key(fake_table, event_down)

        self.assertEqual(move_calls, [-1, 1])

    def test_review_scope_local_refresh_defers_to_service_guidance_phase(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
        stay_result = SimpleNamespace(
            reload_subjects=False,
            next_phase="",
            next_tab="",
            phase_view=SimpleNamespace(preferred_phase="review", phase="review"),
        )
        move_result = SimpleNamespace(
            reload_subjects=False,
            next_phase="",
            next_tab="",
            phase_view=SimpleNamespace(preferred_phase="publication", phase="review"),
        )

        self.assertTrue(
            app._should_use_local_review_scope_refresh(
                "review",
                "toggle_selected_report_scope_item",
                stay_result,
            )
        )
        self.assertFalse(
            app._should_use_local_review_scope_refresh(
                "review",
                "toggle_selected_report_scope_item",
                move_result,
            )
        )

    def test_draft_local_refresh_defers_to_service_guidance_phase(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
        stay_result = SimpleNamespace(
            reload_subjects=False,
            next_phase="",
            next_tab="",
            phase_view=SimpleNamespace(preferred_phase="draft", phase="draft"),
        )
        move_result = SimpleNamespace(
            reload_subjects=False,
            next_phase="",
            next_tab="",
            phase_view=SimpleNamespace(preferred_phase="review", phase="draft"),
        )

        self.assertTrue(
            app._should_use_local_draft_refresh(
                "draft",
                "open_draft_model_view",
                stay_result,
            )
        )
        self.assertFalse(
            app._should_use_local_draft_refresh(
                "draft",
                "open_draft_model_view",
                move_result,
            )
        )

    def _query_subject_gate_button_by_label(
        self,
        app: _TextualWorkstationChatApp,
        *,
        phase: str,
        label: str,
    ):
        for index in range(1, 6):
            try:
                button = app.query_one(f"#subject_{phase}_review_gate_action_{index}_button")
            except Exception:
                continue
            if str(getattr(button, "label", "")) == label:
                return button
        self.fail(f"Could not find {phase} gate button with label {label!r}.")

    def _find_subject_gate_button_by_label(
        self,
        app: _TextualWorkstationChatApp,
        *,
        phase: str,
        label: str,
    ):
        for index in range(1, 6):
            try:
                button = app.query_one(f"#subject_{phase}_review_gate_action_{index}_button")
            except Exception:
                continue
            if str(getattr(button, "label", "")) == label:
                return button
        return None

    def _find_subject_gate_button_by_prefix(
        self,
        app: _TextualWorkstationChatApp,
        *,
        phase: str,
        prefix: str,
    ):
        normalized_prefix = str(prefix or "")
        for index in range(1, 6):
            try:
                button = app.query_one(f"#subject_{phase}_review_gate_action_{index}_button")
            except Exception:
                continue
            label = str(getattr(button, "label", "") or "")
            if label.startswith(normalized_prefix):
                return button
        return None

    async def _wait_for_subject_gate_button_label(
        self,
        pilot: Any,
        app: _TextualWorkstationChatApp,
        *,
        phase: str,
        label: str,
        attempts: int = 6,
    ):
        for _ in range(max(1, int(attempts))):
            for index in range(1, 6):
                try:
                    button = app.query_one(f"#subject_{phase}_review_gate_action_{index}_button")
                except Exception:
                    continue
                if str(getattr(button, "label", "")) == label:
                    return button
            await pilot.pause()
        self.fail(f"Could not find {phase} gate button with label {label!r} after waiting.")

    def _seed_report_scope_subject(
        self,
        subject_id: str,
        *,
        unit_titles: tuple[str, ...] = (
            "Actors",
            "Boundaries",
            "Capabilities",
            "Constraints",
            "Dependencies",
            "Objectives",
            "States",
            "Transitions",
            "Vendors",
            "Balances",
            "Top Ups",
            "Cashiers",
            "Parents",
            "Students",
            "Receipts",
        ),
    ):
        source = new_learning_source(
            subject_id=subject_id,
            title="Report Scope Notes",
            source_ref=f"notes/{subject_id}.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Report Scope Notes\n\n" + "\n\n".join(f"## {title}\n{title} matter." for title in unit_titles),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit enough units for report-scope UI behavior.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title=subject_id.replace("-", " ").title(),
                aliases=(subject_id.replace("-", " ").title(),),
                subject_family="Workstation UI",
                summary="A maintained subject for report-scope widget behavior.",
                units=tuple(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title=title,
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title=title,
                        statement=f"{title}.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    )
                    for title in unit_titles
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)
        return scenario, progress

    def _seed_publication_import_control_subject(self, subject_id: str):
        source = new_learning_source(
            subject_id=subject_id,
            title="Publication Import Control Notes",
            source_ref=f"notes/{subject_id}.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Publication Import Control Notes\n\n## Alpha\nAlpha matters.\n",
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit publication import control demo.",
        )
        persist_learning_delta(self.root, delta)
        active_context = LearningContext(
            subject_id=subject_id,
            canonical_title=subject_id.replace("-", " ").title(),
            aliases=(subject_id.replace("-", " ").title(),),
            subject_family="Workstation UI",
            summary="A subject for publication imported-support widget behavior.",
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
            ),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, active_context)

        subject_imports = []
        for suffix, title in (
            ("alpha", "Widget Import Support Alpha"),
            ("zeta", "Widget Import Support Zeta"),
        ):
            import_subject_id = f"{subject_id}-{suffix}-support"
            import_source = new_learning_source(
                subject_id=import_subject_id,
                title=f"{title} Notes",
                source_ref=f"notes/{import_subject_id}.md",
            )
            persist_learning_source(
                self.root,
                import_source,
                source_text=f"# {title} Notes\n\n## Support\n{title} is useful supporting material.\n",
            )
            import_delta = new_learning_delta(
                subject_id=import_subject_id,
                source_kind="markdown",
                rationale=f"Admit {title}.",
            )
            persist_learning_delta(self.root, import_delta)
            import_unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=import_subject_id,
                    unit_kind="definition",
                    canonical_title="Support",
                ),
                subject_id=import_subject_id,
                unit_kind="definition",
                canonical_title="Support",
                statement=f"{title} is useful supporting material.",
                provenance_refs=(import_source.source_id,),
                status="admitted",
            )
            import_context = LearningContext(
                subject_id=import_subject_id,
                canonical_title=title,
                aliases=(title,),
                subject_family="Workstation UI",
                summary=f"Supporting subject for {title}.",
                units=(import_unit,),
                linked_source_ids=(import_source.source_id,),
                applied_delta_ids=(import_delta.delta_id,),
                governance_status="active",
            )
            persist_learning_context(self.root, import_context)
            subject_import = new_subject_import(
                active_subject_id=active_context.subject_id,
                active_subject_version_id=active_context.content_hash(),
                active_subject_title=active_context.canonical_title,
                source_subject_id=import_context.subject_id,
                source_subject_version_id=import_context.content_hash(),
                source_subject_title=import_context.canonical_title,
                import_kind="definition_support",
                imported_unit_ids=(import_unit.unit_id,),
                rationale=f"Borrow {title} for publication import controls.",
            )
            persist_subject_import(self.root, subject_import)
            subject_imports.append(subject_import)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == active_context.subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == active_context.subject_id)
        subject_imports = tuple(
            sorted(
                subject_imports,
                key=lambda item: (
                    collapse_ws(item.source_subject_title) or collapse_ws(item.source_subject_id),
                    collapse_ws(item.import_id),
                ),
            )
        )
        return scenario, progress, subject_imports

    def _prepare_draft_model_relation_demo(self, *, selected_construct_kind: str) -> tuple[str, dict[str, str]]:
        subject_id = f"draft-model-relation-{selected_construct_kind}-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Draft Model Relation Notes",
            source_ref="notes/draft-model-relations.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft Model Relation Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n\n"
                "## Controls\nAccess and audit controls matter.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the draft model relation widget subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title=f"Draft Model Relation {selected_construct_kind.title()} Demo",
                aliases=(f"Draft Model Relation {selected_construct_kind.title()} Demo",),
                subject_family="Governance",
                summary="Maintained subject for Draft Model relation binding widgets.",
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

        progress.draft_selected_construct_candidate_id = candidates[5].construct_candidate_id
        transition_specs = subject_draft_model_relation_selection_list_specs(
            scenario=scenario,
            progress=progress,
        )
        if transition_specs and transition_specs[0].options:
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key=(
                    "set_selected_draft_construct_transition_changed_capabilities:"
                    f"{transition_specs[0].options[0][1]}"
                ),
            )

        selected_map = {
            "capability": candidates[2].construct_candidate_id,
            "transition": candidates[5].construct_candidate_id,
            "decision": candidates[6].construct_candidate_id,
        }
        progress.draft_selected_construct_candidate_id = selected_map[selected_construct_kind]
        relation_specs = subject_draft_model_relation_selection_list_specs(
            scenario=scenario,
            progress=progress,
        )
        relation_ids: dict[str, str] = {}
        for spec in relation_specs:
            for option_label, option_value, _selected in spec.options:
                normalized_label = str(option_label)
                if normalized_label == "Carrier Uptime":
                    relation_ids["dependency_id"] = option_value
                elif normalized_label == "Carrier Boundary":
                    relation_ids["boundary_id"] = option_value
                elif normalized_label == "Move To Target":
                    relation_ids["transition_id"] = option_value
                elif normalized_label == "Operations Team":
                    relation_ids["actor_id"] = option_value
        transition_source_spec = subject_draft_model_transition_source_select_spec(
            scenario=scenario,
            progress=progress,
        )
        transition_target_spec = subject_draft_model_transition_target_select_spec(
            scenario=scenario,
            progress=progress,
        )
        if transition_source_spec.options:
            relation_ids["source_state_id"] = transition_source_spec.options[0][1]
        if transition_target_spec.options:
            relation_ids["target_state_id"] = transition_target_spec.options[0][1]
        persist_subject_progress(self.root, scenario.subject_id, progress)
        return subject_id, relation_ids

    def test_workstation_chat_context_reads_workspace_and_skill_inventory(self) -> None:
        """
        High Level Purpose:
            In circumstances like enhanced workstation chat prompting, helps with verifying that the UI context loader sees the current workspace root, visible skills, and relative workspace paths.

        Reference to Theory:
            Verifies the chat frontend stays a thin shell over session files and attachments rather than introducing a separate source of truth.

        Example Input Output:
            Input: `test_workstation_chat_context_reads_workspace_and_skill_inventory()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        context = workstation_chat_context(self.root)
        self.assertEqual(context.workspace_root, self.workspace.resolve())
        self.assertIn("Workstation Repo Search", context.skill_titles)
        self.assertIn(
            "Python Commands 02 — Read Text File / Python Commands 02 Read Text File",
            context.imported_skill_titles,
        )
        self.assertIn("src/demo.py", context.workspace_paths)
        self.assertEqual(context.subject_titles, ())

    def test_workstation_chat_pane_state_renders_persistent_activity_and_transcript(self) -> None:
        context = workstation_chat_context(self.root)
        state = _WorkstationChatPaneState(root=self.root.resolve(), context=context)
        state.append_activity_line("Invoking skill: Workstation Repo Search [in: pattern=chat]")
        state.append_transcript_block(label="assistant", text="Found it.\n\nsrc/demo.py")
        self.assertIn("Invoking skill: Workstation Repo Search", state.activity_text())
        self.assertIn("Assistant", state.transcript_text())
        self.assertIn("src/demo.py", state.transcript_text())
        state.set_current_input_text("/")
        self.assertIn("/help", state.suggestions_text())
        self.assertIn("Up/Down navigates suggestions when text is present.", state.banner_text())

    def test_workstation_chat_pane_state_tracks_transient_activity_strip_during_turn(self) -> None:
        context = workstation_chat_context(self.root)
        state = _WorkstationChatPaneState(root=self.root.resolve(), context=context)
        state.start_turn()
        try:
            self.assertEqual(state.activity_strip_text(), "")
            state.append_activity_line("Invoking skill: Workstation Repo Search [in: pattern=chat]")
            self.assertIn("Invoking skill: Workstation Repo Search", state.activity_strip_text())
            self.assertTrue(state.advance_activity_pulse())
            self.assertTrue(state.activity_strip_text().endswith("."))
        finally:
            state.finish_turn()
        self.assertIn("Invoking skill: Workstation Repo Search", state.activity_strip_text())
        state.current_turn_activity_visible_until = 0.0
        self.assertTrue(state.expire_activity_strip_if_needed())
        self.assertEqual(state.activity_strip_text(), "")

    def test_textual_chat_tab_hides_activity_panel_when_idle(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                self.assertFalse(app.query_one("#chat_activity_panel").display)

        asyncio.run(_exercise())

    def test_workstation_chat_activity_strip_text_animates_suffix(self) -> None:
        self.assertEqual(
            workstation_chat_activity_strip_text("Blend step started", pulse_index=0),
            "Blend step started",
        )
        self.assertEqual(
            workstation_chat_activity_strip_text("Blend step started", pulse_index=3),
            "Blend step started...",
        )

    def test_textual_copy_selected_text_copies_selection_when_present(self) -> None:
        copied: list[str] = []
        screen = SimpleNamespace(get_selected_text=lambda: "Copied pane text")
        app = SimpleNamespace(copy_to_clipboard=lambda value: copied.append(str(value)))
        self.assertTrue(_textual_copy_selected_text(screen, app))
        self.assertEqual(copied, ["Copied pane text"])

    def test_textual_copy_text_copies_transcript_when_present(self) -> None:
        copied: list[str] = []
        app = SimpleNamespace(copy_to_clipboard=lambda value: copied.append(str(value)))
        with patch("workstation.ui.textual.chat_ui._copy_text_to_system_clipboard", return_value=False) as copy_system:
            self.assertTrue(_textual_copy_text(app, "You\n  hello"))
        copy_system.assert_called_once_with("You\n  hello")
        self.assertEqual(copied, ["You\n  hello"])

    def test_copy_text_to_system_clipboard_uses_pbcopy_on_macos(self) -> None:
        with patch("workstation.ui.textual.chat_ui.sys.platform", "darwin"), patch(
            "workstation.ui.textual.chat_ui.subprocess.run"
        ) as run:
            self.assertTrue(_copy_text_to_system_clipboard("hello"))
        run.assert_called_once()
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["pbcopy"])
        self.assertEqual(kwargs["input"], b"hello")
        self.assertTrue(kwargs["check"])

    def test_textual_copy_selected_text_from_widget_copies_widget_selection(self) -> None:
        copied: list[str] = []
        widget = SimpleNamespace(
            text_selection=object(),
            get_selection=lambda selection: ("Selected transcript line", "\n"),
        )
        app = SimpleNamespace(copy_to_clipboard=lambda value: copied.append(str(value)))
        with patch("workstation.ui.textual.chat_ui._copy_text_to_system_clipboard", return_value=False):
            self.assertTrue(_textual_copy_selected_text_from_widget(widget, app))
        self.assertEqual(copied, ["Selected transcript line"])

    def test_workstation_chat_pane_state_switches_input_status_for_approval(self) -> None:
        context = workstation_chat_context(self.root)
        state = _WorkstationChatPaneState(root=self.root.resolve(), context=context)
        event = state.begin_approval(
            WorkstationDelegationEscalationRequest(
                capability="ws.skill.invoke",
                target="skills",
                skill_title="Python Commands 03 — Write Text File",
                requested_delegation=({"capability": "ws.fs.write", "target": "main"},),
                rationale="Need to write into the workspace.",
                scope="one_invocation",
            )
        )
        self.assertIn("Approve? [yes/no]", state.input_status_text())
        self.assertTrue(state.awaiting_approval())
        self.assertFalse(state.resolve_approval_from_input("later"))
        self.assertTrue(state.awaiting_approval())
        self.assertTrue(state.resolve_approval_from_input("yes"))
        event.wait(timeout=0.1)
        self.assertFalse(state.awaiting_approval())
    def test_workstation_chat_live_suggestions_follow_slash_prefix(self) -> None:
        context = workstation_chat_context(self.root)
        suggestions = workstation_chat_live_suggestions(context=context, buffer_text="/")
        self.assertIn("/help", suggestions)
        self.assertIn("/prepare-markdown", suggestions)
        self.assertIn("/prepare-last-assistant-markdown", suggestions)
        self.assertEqual(
            workstation_chat_live_suggestions(context=context, buffer_text="the"),
            [],
        )

    def test_workstation_chat_pane_state_formats_slash_suggestions_with_help_text(self) -> None:
        context = workstation_chat_context(self.root)
        state = _WorkstationChatPaneState(root=self.root.resolve(), context=context)
        state.set_current_input_text("/")
        rendered = state.suggestions_text()
        self.assertIn("/prepare-markdown <text>", rendered)
        self.assertIn("then use /start-research", rendered)
        self.assertIn("/start-research", rendered)

    def test_workstation_chat_live_suggestions_keep_slash_prefix_in_command_space(self) -> None:
        context = workstation_chat_context(self.root)
        suggestion_titles = (
            "API Client Commands 01 — Demo / API Client Commands 01 Demo",
            "API Client Commands 02 — Demo / API Client Commands 02 Demo",
        )
        suggestion_context = type(context)(
            root=context.root,
            workspace_root=context.workspace_root,
            skill_titles=suggestion_titles,
            builtin_skill_titles=(),
            imported_skill_titles=suggestion_titles,
            subject_titles=context.subject_titles,
            workspace_paths=context.workspace_paths,
            allowed_capabilities=context.allowed_capabilities,
        )
        suggestions = workstation_chat_live_suggestions(
            context=suggestion_context,
            buffer_text="/api",
        )
        self.assertEqual(suggestions, [])

    def test_workstation_chat_live_suggestions_return_all_matching_skills(self) -> None:
        context = workstation_chat_context(self.root)
        suggestion_titles = tuple(
            f"API Client Commands 0{index} — Demo / API Client Commands 0{index} Demo"
            for index in range(1, 6)
        )
        suggestion_context = type(context)(
            root=context.root,
            workspace_root=context.workspace_root,
            skill_titles=suggestion_titles,
            builtin_skill_titles=(),
            imported_skill_titles=suggestion_titles,
            subject_titles=context.subject_titles,
            workspace_paths=context.workspace_paths,
            allowed_capabilities=context.allowed_capabilities,
        )
        suggestions = workstation_chat_live_suggestions(
            context=suggestion_context,
            buffer_text="API",
        )
        self.assertEqual(suggestions, list(suggestion_titles))

    def test_workstation_chat_apply_prompt_suggestion_preserves_non_skill_text(self) -> None:
        context = workstation_chat_context(self.root)
        suggestion = "Python Commands 02 — Read Text File / Python Commands 02 Read Text File"
        applied = workstation_chat_apply_prompt_suggestion(
            context=context,
            buffer_text="Use py to inspect src/demo.py",
            suggestion=suggestion,
        )
        self.assertEqual(
            applied,
            "Use Python Commands 02 — Read Text File / Python Commands 02 Read Text File to inspect src/demo.py",
        )

    def test_workstation_chat_apply_prompt_suggestion_keeps_full_replacement_for_non_skill_suggestion(self) -> None:
        context = workstation_chat_context(self.root)
        applied = workstation_chat_apply_prompt_suggestion(
            context=context,
            buffer_text="/h",
            suggestion="/help",
        )
        self.assertEqual(applied, "/help")

    def test_workstation_chat_inline_completion_uses_fast_path_cases_only(self) -> None:
        context = workstation_chat_context(self.root)
        self.assertEqual(
            workstation_chat_inline_completion(context=context, buffer_text="/"),
            "/help",
        )
        self.assertIsNone(
            workstation_chat_inline_completion(
                context=context,
                buffer_text="tell me what is in this workspace",
            )
        )

    def test_workstation_chat_history_path_lives_under_session_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like interactive workstation history navigation, helps with verifying that enhanced chat input history is stored beneath the workstation root instead of in ambient user-global terminal state.

        Reference to Theory:
            Verifies command-history persistence remains part of the host-owned workstation shell boundary.

        Example Input Output:
            Input: `test_workstation_chat_history_path_lives_under_session_root()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertEqual(
            workstation_chat_history_path(self.root),
            self.root.resolve() / "history" / "chat_input.txt",
        )

    def test_workstation_chat_suggestions_include_import_and_read_prompts(self) -> None:
        """
        High Level Purpose:
            In circumstances like enhanced workstation chat prompting, helps with verifying that the UI offers high-value next prompts covering skill discovery, import, and path-aware worker use.

        Reference to Theory:
            Verifies the outer chat UI steers the user toward the skill-first path without changing the underlying capability semantics.

        Example Input Output:
            Input: `test_workstation_chat_suggestions_include_import_and_read_prompts()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        context = workstation_chat_context(self.root)
        suggestions = workstation_chat_suggestions(context)
        self.assertTrue(
            any("What skills are available right now?" in item for item in suggestions)
        )
        self.assertTrue(
            any("Import the skill file at trials/python.skill.yaml" in item for item in suggestions)
        )
        self.assertTrue(
            any("Use the Python read-text-file skill to read src/demo.py" in item for item in suggestions)
        )

    def test_workstation_chat_completion_candidates_cover_import_titles_and_paths(self) -> None:
        """
        High Level Purpose:
            In circumstances like enhanced workstation chat tab completion, helps with verifying that import prompts, skill-title prompts, and path-aware file prompts produce relevant completions.

        Reference to Theory:
            Verifies the richer terminal UI remains a convenience layer over the current skill/path context rather than a separate planner.

        Example Input Output:
            Input: `test_workstation_chat_completion_candidates_cover_import_titles_and_paths()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session_payload = json.loads((self.root / "SESSION.json").read_text())
        session_payload["allowed_capabilities"] = list(
            dict.fromkeys([*session_payload.get("allowed_capabilities", []), "ws.repo.tree"])
        )
        (self.root / "SESSION.json").write_text(json.dumps(session_payload))
        context = workstation_chat_context(self.root)
        import_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="Import the skill file at tr",
        )
        self.assertIn(
            "Import the skill file at trials/python.skill.yaml into this workstation.",
            import_candidates,
        )
        title_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text='Use the skill titled "Python Commands 02',
        )
        self.assertTrue(
            any("Python Commands 02 — Read Text File" in item for item in title_candidates)
        )
        path_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="Use the Python read-text-file skill to read s",
        )
        self.assertIn(
            "Use the Python read-text-file skill to read src/demo.py and show me the contents.",
            path_candidates,
        )
        slash_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/h",
        )
        self.assertIn("/help", slash_candidates)
        prepare_slash_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/pre",
        )
        self.assertIn("/prepare-markdown", prepare_slash_candidates)
        start_research_into_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/start-research-i",
        )
        self.assertIn("/start-research-into", start_research_into_candidates)
        curate_source_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/curate-s",
        )
        self.assertIn("/curate-source", curate_source_candidates)
        self.assertIn("/curate-source-set", curate_source_candidates)
        import_slash_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/import-skill tr",
        )
        self.assertIn("/import-skill trials/python.skill.yaml", import_slash_candidates)
        describe_slash_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/describe-skill Py",
        )
        self.assertTrue(
            any(candidate.startswith('/describe-skill "Python Commands 02') for candidate in describe_slash_candidates)
        )
        grant_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/grant-permission ws.r",
        )
        self.assertIn("/grant-permission ws.repo.search", grant_candidates)
        net_grant_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/grant-permission ws.n",
        )
        self.assertIn("/grant-permission ws.net.http", net_grant_candidates)
        revoke_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/revoke-permission ws.r",
        )
        self.assertIn("/revoke-permission ws.repo.tree", revoke_candidates)
        export_path_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text='/export-skill "Python Commands 02 — Read Text File / Python Commands 02 Read Text File" ex',
        )
        self.assertIn(
            '/export-skill "Python Commands 02 — Read Text File / Python Commands 02 Read Text File" exports/',
            export_path_candidates,
        )
        skill_insert_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="Py",
        )
        self.assertTrue(
            any(candidate.startswith("Python Commands 03") for candidate in skill_insert_candidates)
        )
        internal_substring_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="ead",
        )
        self.assertEqual(internal_substring_candidates, [])

    def test_resume_research_completion_uses_live_subject_titles(self) -> None:
        subject_source = new_learning_source(
            subject_id="formula-particles-moles",
            title="Formula Particles Moles Notes",
            source_ref="notes/formula-particles-moles.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            subject_source,
            source_text="# Formula Particles Moles\n\nN = n × NA\n",
        )
        subject_delta = new_learning_delta(
            subject_id="formula-particles-moles",
            source_kind="markdown",
            rationale="Seed one subject for resume-research-with-llm completion.",
        )
        persist_learning_delta(self.root, subject_delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="formula-particles-moles",
                canonical_title="Formula Particles Moles",
                aliases=("Formula Particles Moles",),
                summary="Particles to moles relation.",
                units=(),
                linked_source_ids=(subject_source.source_id,),
                applied_delta_ids=(subject_delta.delta_id,),
            ),
        )
        context = workstation_chat_context(self.root)
        suggestions = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/resume-research-with-llm Fo",
        )
        self.assertIn("/resume-research-with-llm Formula Particles Moles", suggestions)

    def test_resume_research_tab_completion_adds_space_and_shows_sorted_subject_list(self) -> None:
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="zoology",
                canonical_title="Zoology",
                aliases=("Zoology",),
                units=(),
            ),
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="algebra",
                canonical_title="Algebra",
                aliases=("Algebra",),
                units=(),
            ),
        )
        context = workstation_chat_context(self.root)
        completion_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/resume-research-with-llm",
        )
        self.assertEqual(completion_candidates, ["/resume-research-with-llm "])
        applied = workstation_chat_apply_prompt_suggestion(
            context=context,
            buffer_text="/resume-research-with-llm",
            suggestion="/resume-research-with-llm ",
        )
        self.assertEqual(applied, "/resume-research-with-llm ")
        suggestions = workstation_chat_live_suggestions(
            context=context,
            buffer_text=applied,
        )
        self.assertEqual(
            suggestions,
            [
                "/resume-research-with-llm Algebra",
                "/resume-research-with-llm Zoology",
            ],
        )

    def test_start_research_into_tab_completion_adds_space_and_shows_sorted_subject_list(self) -> None:
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="zoology",
                canonical_title="Zoology",
                aliases=("Zoology",),
                units=(),
            ),
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="algebra",
                canonical_title="Algebra",
                aliases=("Algebra",),
                units=(),
            ),
        )
        context = workstation_chat_context(self.root)
        completion_candidates = workstation_chat_completion_candidates(
            context=context,
            buffer_text="/start-research-into",
        )
        self.assertEqual(completion_candidates, ["/start-research-into "])
        applied = workstation_chat_apply_prompt_suggestion(
            context=context,
            buffer_text="/start-research-into",
            suggestion="/start-research-into ",
        )
        self.assertEqual(applied, "/start-research-into ")
        suggestions = workstation_chat_live_suggestions(
            context=context,
            buffer_text=applied,
        )
        self.assertEqual(
            suggestions,
            [
                "/start-research-into Algebra",
                "/start-research-into Zoology",
            ],
        )

    def test_prepare_markdown_and_resume_research_prompt_targets_expand_deterministically(self) -> None:
        empty_context = workstation_chat_context(self.root)
        prepare_plan = workstation_chat_prompt_target_plan(
            context=empty_context,
            prompt_text="/prepare-markdown particle count equals amount times avogadro",
        )
        self.assertIsNotNone(prepare_plan)
        assert prepare_plan is not None
        self.assertEqual(prepare_plan.kind, "llm_prompt")
        self.assertFalse(prepare_plan.move_to_research)
        self.assertIn("Return markdown only", prepare_plan.llm_prompt)
        self.assertIn(
            "particle count equals amount times avogadro",
            workstation_chat_prepare_markdown_prompt("particle count equals amount times avogadro"),
        )

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="physics",
                canonical_title="Physics",
                aliases=("Physics",),
                units=(),
            ),
        )
        resume_context = workstation_chat_context(self.root)
        resume_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/resume-research-with-llm Physics",
        )
        self.assertIsNotNone(resume_plan)
        assert resume_plan is not None
        self.assertEqual(resume_plan.kind, "llm_prompt")
        self.assertEqual(resume_plan.subject_title, "Physics")
        self.assertFalse(resume_plan.move_to_research)
        self.assertIn('Study this maintained subject: "Physics".', resume_plan.llm_prompt)
        self.assertIn('Study this maintained subject: "Physics".', workstation_chat_resume_research_prompt("Physics"))
        self.assertIn("[routed-to-llm]", workstation_chat_routed_llm_prompt_text(resume_plan.llm_prompt))

        start_research_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/start-research",
        )
        self.assertIsNotNone(start_research_plan)
        assert start_research_plan is not None
        self.assertEqual(start_research_plan.kind, "start_research")
        self.assertFalse(start_research_plan.move_to_research)

        start_research_into_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/start-research-into Physics",
        )
        self.assertIsNotNone(start_research_into_plan)
        assert start_research_into_plan is not None
        self.assertEqual(start_research_into_plan.kind, "start_research")
        self.assertFalse(start_research_into_plan.move_to_research)
        self.assertEqual(start_research_into_plan.subject_title, "Physics")

        curate_source_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/curate-source",
        )
        self.assertIsNotNone(curate_source_plan)
        assert curate_source_plan is not None
        self.assertEqual(curate_source_plan.kind, "research_follow_up")
        self.assertEqual(curate_source_plan.command_name, "/curate-source")
        self.assertFalse(curate_source_plan.move_to_research)

        edit_source_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/edit-source",
        )
        self.assertIsNotNone(edit_source_plan)
        assert edit_source_plan is not None
        self.assertEqual(edit_source_plan.kind, "research_action")
        self.assertEqual(edit_source_plan.command_name, "/edit-source")
        self.assertFalse(edit_source_plan.move_to_research)

        create_source_set_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/create-source-set",
        )
        self.assertIsNotNone(create_source_set_plan)
        assert create_source_set_plan is not None
        self.assertEqual(create_source_set_plan.kind, "research_action")
        self.assertEqual(create_source_set_plan.command_name, "/create-source-set")

        create_source_set_from_query_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/create-source-set-from-query Energy Route Sources | energy exports transport routes | cross-border energy routing",
        )
        self.assertIsNotNone(create_source_set_from_query_plan)
        assert create_source_set_from_query_plan is not None
        self.assertEqual(create_source_set_from_query_plan.kind, "research_action")
        self.assertEqual(create_source_set_from_query_plan.command_name, "/create-source-set-from-query")
        self.assertIn("Energy Route Sources", create_source_set_from_query_plan.command_arguments)
        self.assertIn("energy exports transport routes", create_source_set_from_query_plan.command_arguments)

        refresh_source_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/refresh-source",
        )
        self.assertIsNotNone(refresh_source_plan)
        assert refresh_source_plan is not None
        self.assertEqual(refresh_source_plan.kind, "research_action")
        self.assertEqual(refresh_source_plan.command_name, "/refresh-source")

        apply_source_export_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/apply-source-export",
        )
        self.assertIsNotNone(apply_source_export_plan)
        assert apply_source_export_plan is not None
        self.assertEqual(apply_source_export_plan.kind, "research_action")
        self.assertEqual(apply_source_export_plan.command_name, "/apply-source-export")

        merge_source_set_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/merge-source-set",
        )
        self.assertIsNotNone(merge_source_set_plan)
        assert merge_source_set_plan is not None
        self.assertEqual(merge_source_set_plan.kind, "research_follow_up")
        self.assertEqual(merge_source_set_plan.command_name, "/merge-source-set")

        synthesize_source_set_plan = workstation_chat_prompt_target_plan(
            context=resume_context,
            prompt_text="/synthesize-source-set",
        )
        self.assertIsNotNone(synthesize_source_set_plan)
        assert synthesize_source_set_plan is not None
        self.assertEqual(synthesize_source_set_plan.kind, "research_follow_up")
        self.assertEqual(synthesize_source_set_plan.command_name, "/synthesize-source-set")

        no_subject_curate_plan = workstation_chat_prompt_target_plan(
            context=empty_context,
            prompt_text="/find-sources",
        )
        self.assertIsNotNone(no_subject_curate_plan)
        assert no_subject_curate_plan is not None
        self.assertEqual(no_subject_curate_plan.kind, "shell")
        self.assertIn("No subjects are available yet", no_subject_curate_plan.shell_text)

        no_subject_edit_plan = workstation_chat_prompt_target_plan(
            context=empty_context,
            prompt_text="/edit-source-set",
        )
        self.assertIsNotNone(no_subject_edit_plan)
        assert no_subject_edit_plan is not None
        self.assertEqual(no_subject_edit_plan.kind, "shell")
        self.assertIn("No subjects are available yet", no_subject_edit_plan.shell_text)

        no_subject_sync_plan = workstation_chat_prompt_target_plan(
            context=empty_context,
            prompt_text="/sync-source-set",
        )
        self.assertIsNotNone(no_subject_sync_plan)
        assert no_subject_sync_plan is not None
        self.assertEqual(no_subject_sync_plan.kind, "shell")
        self.assertIn("No subjects are available yet", no_subject_sync_plan.shell_text)

    def test_prepare_last_assistant_markdown_resolution_uses_last_reply_and_guards_empty_state(self) -> None:
        llm_prompt, routed_text = workstation_chat_prepare_last_assistant_resolution(
            "Hello [Name], I'm [Your Name]."
        )
        self.assertIn("Hello [Name], I'm [Your Name].", llm_prompt)
        self.assertIn("Prepare research-ingress markdown from the last assistant reply.", routed_text)

        empty_prompt, empty_shell_text = workstation_chat_prepare_last_assistant_resolution("")
        self.assertEqual(empty_prompt, "")
        self.assertIn("No assistant reply is available yet.", empty_shell_text)

    def test_workstation_chat_path_suggestions_require_path_visibility(self) -> None:
        """
        High Level Purpose:
            In circumstances like slash-command path completion, helps with verifying that workspace-path suggestions are only offered when the workstation session exposes path/search visibility.

        Reference to Theory:
            Verifies the shell suggestion layer respects the workstation capability boundary instead of assuming ambient path visibility.

        Example Input Output:
            Input: `test_workstation_chat_path_suggestions_require_path_visibility()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        session_payload = json.loads((self.root / "SESSION.json").read_text())
        session_payload["allowed_capabilities"] = ["ws.skill.catalog", "ws.skill.import", "ws.skill.export", "ws.skill.invoke"]
        (self.root / "SESSION.json").write_text(json.dumps(session_payload))
        context = workstation_chat_context(self.root)
        self.assertEqual(
            workstation_chat_completion_candidates(
                context=context,
                buffer_text="/import-skill tr",
            ),
            [],
        )
        self.assertEqual(
            workstation_chat_completion_candidates(
                context=context,
                buffer_text='/export-skill "Python Commands 02 — Read Text File / Python Commands 02 Read Text File" ex',
            ),
            [],
        )

    def test_workstation_chat_help_text_lists_cli_and_chat_usage(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation chat self-documentation, helps with verifying that `/help` covers both chat-native workflows and the deterministic CLI entrypoints.

        Reference to Theory:
            Verifies the help surface stays at the shell boundary and explains the real product surfaces instead of exposing internal capability helpers.

        Example Input Output:
            Input: `test_workstation_chat_help_text_lists_cli_and_chat_usage()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        context = workstation_chat_context(self.root)
        rendered = workstation_chat_help_text(context)
        self.assertIn("/help", rendered)
        self.assertIn("/prepare-markdown", rendered)
        self.assertIn("/start-research", rendered)
        self.assertIn("/start-research-into", rendered)
        self.assertIn("/resume-research-with-llm", rendered)
        self.assertIn("/research", rendered)
        self.assertIn("/list-skills", rendered)
        self.assertIn("/describe-skill", rendered)
        self.assertIn("/permissions", rendered)
        self.assertIn("/workstation-root", rendered)
        self.assertIn("/grant-permission", rendered)
        self.assertIn("/import-skill", rendered)
        self.assertIn("/revoke-permission", rendered)
        self.assertIn("/export-skill", rendered)
        self.assertIn("workstation-launch", rendered)
        self.assertIn("workstation-chat", rendered)
        self.assertIn("workstation-skill-import", rendered)
        self.assertIn("Import the skill file at trials/python.skill.yaml", rendered)

    def test_workstation_chat_assistant_block_text_preserves_newlines(self) -> None:
        """
        High Level Purpose:
            In circumstances like enhanced workstation assistant rendering, helps with verifying that multiline model output is preserved verbatim instead of being whitespace-collapsed.

        Reference to Theory:
            Verifies the chat UI changes only presentation at the shell boundary while keeping assistant content stable and inspectable.

        Example Input Output:
            Input: `test_workstation_chat_assistant_block_text_preserves_newlines()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rendered = workstation_chat_assistant_block_text("Line one\n\n- item a\n- item b")
        self.assertIn("Assistant", rendered)
        self.assertIn("  Line one", rendered)
        self.assertIn("  - item a", rendered)
        self.assertNotIn("```", rendered)

    def test_workstation_chat_named_block_text_uses_requested_label(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation chat rendering of local slash-command output, helps with verifying that non-assistant output can render in the same block style under its own label.

        Reference to Theory:
            Verifies the shell presentation layer can distinguish assistant replies from direct shell-command output without changing the underlying content.

        Example Input Output:
            Input: `test_workstation_chat_named_block_text_uses_requested_label()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        rendered = workstation_chat_named_block_text(label="shell", text="one\ntwo")
        self.assertIn("System", rendered)
        self.assertIn("  one", rendered)
        self.assertIn("  two", rendered)
        self.assertNotIn("```", rendered)

    def test_workstation_chat_named_block_text_formats_json_payload(self) -> None:
        rendered = workstation_chat_named_block_text(
            label="assistant",
            text="{'status': 'read', 'mount': 'main', 'relative_path': 'trials/python.skill.yaml'}",
        )
        self.assertIn("Assistant", rendered)
        self.assertIn("  [json]", rendered)
        self.assertIn('  "status": "read"', rendered)
        self.assertIn('  "relative_path": "trials/python.skill.yaml"', rendered)
        self.assertNotIn("```", rendered)

    def test_workstation_chat_named_block_text_formats_yaml_payload(self) -> None:
        rendered = workstation_chat_named_block_text(
            label="assistant",
            text="schema: bssc_skill.v2\nkind: ability\ntitle: Demo Skill\n",
        )
        self.assertIn("Assistant", rendered)
        self.assertIn("  [yaml]", rendered)
        self.assertIn("  schema: bssc_skill.v2", rendered)
        self.assertNotIn("```", rendered)

    def test_workstation_chat_named_block_text_preserves_existing_markdown_fences(self) -> None:
        rendered = workstation_chat_named_block_text(
            label="assistant",
            text="Here is the result:\n\n```yaml\nschema: bssc_skill.v2\nkind: ability\n```",
        )
        self.assertIn("Assistant", rendered)
        self.assertIn("  [markdown]", rendered)
        self.assertIn("  [yaml]", rendered)
        self.assertIn("  schema: bssc_skill.v2", rendered)
        self.assertNotIn("```", rendered)

    def test_workstation_chat_ui_supported_requires_real_tty(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation chat frontend selection, helps with verifying that non-interactive streams keep using the plain loop instead of the readline UI.

        Reference to Theory:
            Verifies the richer chat frontend remains optional and does not disturb deterministic non-interactive surfaces.

        Example Input Output:
            Input: `test_workstation_chat_ui_supported_requires_real_tty()`
            Output: None

        Args:
            self: Bound test-case instance.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertFalse(
            workstation_chat_ui_supported(
                input_stream=io.StringIO(),
                output_stream=io.StringIO(),
            )
        )

    def test_textual_chat_app_mounts_and_handles_help_submission(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                self.assertIsNotNone(app.query_one("#root_tabs"))
                self.assertIsNotNone(app.query_one("#chat_tab"))
                self.assertIsNotNone(app.query_one("#learn_tab"))
                self.assertIsNotNone(app.query_one("#draft_tab"))
                self.assertIsNotNone(app.query_one("#review_tab"))
                self.assertIsNotNone(app.query_one("#publication_tab"))
                self.assertIsNotNone(app.query_one("#permissions_tab"))
                self.assertIsNotNone(app.query_one("#activity_tab"))
                self.assertIsNotNone(app.query_one("#skills_tab"))
                self.assertIsNotNone(app.query_one("#learn_markdown_button"))
                self.assertIsNotNone(app.query_one("#export_learned_button"))
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                app.on_input_submitted(SimpleNamespace(input=input_widget, value="/help"))
                transcript = None
                for _ in range(10):
                    await pilot.pause()
                    transcripts = list(app.query("#transcript"))
                    self.assertTrue(transcripts)
                    transcript = transcripts[0]
                    if any("Permission model" in str(line) for line in getattr(transcript, "lines", ())):
                        break
                transcripts = list(app.query("#transcript"))
                self.assertTrue(transcripts)
                transcript = transcripts[0]
                self.assertGreater(len(getattr(transcript, "lines", [])), 0)
                self.assertTrue(any("Permission model" in str(line) for line in transcript.lines))

        asyncio.run(_exercise())

    def test_textual_chat_tab_bdd_routes_help_submission_from_visible_chat_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "chat_tab")
                self.assertTrue(bool(getattr(app.query_one("#chat_tab"), "display", True)))
                self.assertGreater(int(getattr(app.query_one("#transcript").region, "width", 0) or 0), 0)

                await pilot.click("#input")
                input_widget = app.query_one("#input")
                input_widget.value = "/help"
                await pilot.press("enter")
                for _ in range(10):
                    await pilot.pause()
                    transcript_text = app._state.transcript_text()
                    if "Permission model" in transcript_text:
                        break

                transcript_text = app._state.transcript_text()
                self.assertIn("/help", transcript_text)
                self.assertIn("Permission model", transcript_text)
                self.assertIn("/list-skills", transcript_text)

        asyncio.run(_exercise())

    def test_textual_permissions_tab_bdd_shows_session_capabilities_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_permissions_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "permissions_tab")
                self.assertTrue(bool(getattr(app.query_one("#permissions_panel"), "display", True)))
                self.assertGreater(int(getattr(app.query_one("#permissions").region, "width", 0) or 0), 0)

                rendered = app._permissions_text()
                self.assertIn("Granted session capabilities:", rendered)
                self.assertIn("Available capabilities:", rendered)
                self.assertIn("Protected shell capabilities:", rendered)
                self.assertIn("/permissions <skill title>", rendered)

        asyncio.run(_exercise())

    def test_textual_activity_tab_bdd_shows_recent_activity_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                app._state.append_activity_line("Invoking skill: Workstation Repo Search [in: pattern=chat]")
                await pilot.pause()
                await pilot.click("#tab_button_activity_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "activity_tab")
                self.assertTrue(bool(getattr(app.query_one("#activity_panel"), "display", True)))
                self.assertGreater(int(getattr(app.query_one("#activity").region, "width", 0) or 0), 0)
                self.assertIn("Invoking skill: Workstation Repo Search", app._state.activity_text())

        asyncio.run(_exercise())

    def test_textual_skills_tab_bdd_shows_visible_skill_catalog_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        skill_home = resolve_workstation_skill_home()
        skill_source = self.workspace / "trials" / "python-commands-02.skill.yaml"
        skill_source.write_text(
            "\n".join(
                [
                    "schema: bssc_skill.v1",
                    "kind: knowledge",
                    "title: Python Commands 02 — Read Text File",
                    "answer: Read the requested text file.",
                    "",
                ]
            )
        )
        import_workstation_skill_file(
            skill_store_path=skill_home["store_path"],
            source_file=skill_source,
            canonical_export_path=skill_home["exports_path"] / "python-commands-02.skill.yaml",
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_skills_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "skills_tab")
                self.assertTrue(bool(getattr(app.query_one("#skills_panel"), "display", True)))
                self.assertGreater(int(getattr(app.query_one("#skills").region, "width", 0) or 0), 0)

                rendered = app._skills_text()
                self.assertIn("Built-in skills", rendered)
                self.assertIn("Imported skills", rendered)
                self.assertIn("Workstation Repo Search", rendered)
                self.assertIn("Python Commands 02", rendered)
                self.assertIn("Total visible:", rendered)

        asyncio.run(_exercise())

    def test_textual_subject_tabs_start_and_stop_subject_workflow_watch(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")
        markdown_path = DST_SOURCE_ROOT / "City bus prose v2.md"
        result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(result.status, "ok")
        scenarios = tuple(default_subject_scenarios(self.root))
        self.assertTrue(any(not item.is_placeholder for item in scenarios))

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.pause()

                self.assertIsNotNone(app._subject_workflow_watch_key)
                self.assertIsNotNone(app._subject_workflow_watch_thread)
                self.assertTrue(bool(app._subject_workflow_watch_thread.is_alive()))

                await pilot.click("#tab_button_activity_tab")
                await pilot.pause()
                await pilot.pause()

                self.assertIsNone(app._subject_workflow_watch_key)

        asyncio.run(_exercise())

    def test_textual_chat_app_tab_cycles_panels_and_shift_tab_switches_tabs(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#input")
                await pilot.press("tab")
                await pilot.pause()
                self.assertIs(app.focused, app.query_one("#transcript"))
                await pilot.press("shift+tab")
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "learn_tab")
                self.assertIs(app.focused, app.query_one("#learn_markdown_button"))

        asyncio.run(_exercise())

    def test_textual_chat_app_submit_keeps_transcript_scrolled_to_bottom(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#input")
                with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", lambda **_kwargs: None):
                    for index in range(12):
                        for key in ("h", "e", "l", "l", "o", "space", str(index % 10), "enter"):
                            await pilot.press(key)
                        await pilot.pause()
                await pilot.pause()
                transcript = app.query_one("#transcript")
                self.assertEqual(getattr(transcript, "scroll_y", None), getattr(transcript, "max_scroll_y", None))

        asyncio.run(_exercise())

    def test_textual_chat_app_arrow_navigation_selects_skill_suggestion(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#input")
                await pilot.press("u", "s", "e", "space", "p", "y")
                await pilot.pause()
                suggestions = app._active_prompt_suggestions()
                self.assertGreaterEqual(len(suggestions), 2)
                expected_title = suggestions[1]
                await pilot.press("down")
                await pilot.press("tab")
                await pilot.pause()
                input_widget = app.query_one("#input")
                self.assertEqual(getattr(input_widget, "value", ""), f"use {expected_title}")

        asyncio.run(_exercise())

    def test_textual_chat_app_keeps_prompt_when_turn_is_busy(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                app._state.busy = True
                await pilot.click("#input")
                await pilot.press("h", "e", "l", "l", "o", "space", "a", "g", "a", "i", "n", "enter")
                await pilot.pause()
                input_widget = app.query_one("#input")
                self.assertEqual(getattr(input_widget, "value", ""), "hello again")
                transcript = app.query_one("#transcript")
                self.assertTrue(any("A turn is already running." in str(line) for line in transcript.lines))

        asyncio.run(_exercise())

    def test_textual_chat_app_prepare_last_assistant_markdown_uses_previous_assistant_reply(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        captured_worker_kwargs: list[dict[str, object]] = []
        assistant_text = "Hello [Name], I'm [Your Name]. Nice to meet you."
        seed_shell_client = InProcessWorkstationShellClient(client_session_id="seed-assistant-transcript")
        seed_shell_client.append_shell_turn(
            root_path=self.root,
            assistant_text=assistant_text,
            assistant_role="assistant",
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                with patch(
                    "workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker",
                    side_effect=lambda **kwargs: captured_worker_kwargs.append(dict(kwargs)),
                ):
                    app.on_input_submitted(
                        SimpleNamespace(
                            input=input_widget,
                            value="/prepare-last-assistant-markdown",
                        )
                    )
                    await pilot.pause()

        asyncio.run(_exercise())
        self.assertEqual(
            [str(kwargs.get("prompt", "")) for kwargs in captured_worker_kwargs],
            [workstation_chat_prepare_markdown_prompt(assistant_text)],
        )
        self.assertEqual([bool(kwargs.get("force_llm_only")) for kwargs in captured_worker_kwargs], [True])

    def test_textual_learn_tab_renders_progress_panel_state(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                app._apply_markdown_state_update(
                    selected_path=self.workspace / "demo.md",
                    busy=True,
                    status_text="Converting markdown to a portable skill bundle...",
                )
                app._markdown_busy_started_at = time.monotonic() - 1.1
                await pilot.pause()
                panel = app.query_one("#learn_ingress_panel")
                current_step_panel = app.query_one("#subject_research_review_gate_summary")
                journey_panel = app.query_one(f"#{_subject_gate_status_table_id('research', 'publication')}")
                rendered = str(panel.render())
                self.assertIn("Markdown Ingress", rendered)
                self.assertIn("State: Running", rendered)
                self.assertIn("demo.md", rendered)
                self.assertIn("Converting markdown to a portable skill bundle...", rendered)
                self.assertIn("Elapsed:", rendered)
                self.assertIn("Progress: still working", rendered)
                self.assertIn("Import markdown into the first subject", str(current_step_panel.render()))
                journey_text = _table_text(journey_panel)
                self.assertIn("Mode | Live subject workflow", journey_text)
                self.assertIn("Gather | 0 sources, 0 deltas, 0 items", journey_text)

        asyncio.run(_exercise())

    def test_textual_learn_progress_refresh_reuses_warm_research_snapshot(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            original_get_snapshot = app._subject_projection_backend.get_snapshot
            snapshot_call_count = 0

            def _counted_get_snapshot(*args, **kwargs):
                nonlocal snapshot_call_count
                snapshot_call_count += 1
                return original_get_snapshot(*args, **kwargs)

            with patch.object(app._subject_projection_backend, "get_snapshot", side_effect=_counted_get_snapshot):
                async with app.run_test() as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app._apply_markdown_state_update(
                        selected_path=self.workspace / "demo.md",
                        busy=True,
                        status_text="Converting markdown to a portable skill bundle...",
                    )
                    await pilot.pause()
                    await pilot.pause()

                    warm_snapshot_call_count = snapshot_call_count
                    self.assertGreater(warm_snapshot_call_count, 0)

                    app._refresh_learn_progress_tick()
                    await pilot.pause()
                    await pilot.pause()
                    self.assertEqual(snapshot_call_count, warm_snapshot_call_count)

                    app.request_state_refresh()
                    await pilot.pause()
                    await pilot.pause()
                    self.assertEqual(snapshot_call_count, warm_snapshot_call_count)

        asyncio.run(_exercise())

    def test_textual_learn_tab_uses_live_subject_projection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        persist_subject_progress(self.root, "kinematics-demo", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                root_tabs = app.query_one("#root_tabs")
                review_gate = str(app.query_one("#subject_research_review_gate_summary").render())
                publication_gate = app.query_one(f"#{_subject_gate_status_table_id('research', 'publication')}")
                observation_panel = app.query_one("#subject_observation_panel")
                review_gate_next = app.query_one("#subject_research_review_gate_action_1_button")
                publication_gate_next = app.query_one("#subject_research_publication_gate_action_1_button")
                learn_result = app.query_one("#learn_result")
                self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                self.assertIn("Kinematics Demo", str(getattr(root_tabs, "border_title", "")))
                publication_gate_text = _table_text(publication_gate)
                self.assertEqual(len(app.query("#subject_research_publication_gate_summary")), 0)
                self.assertIn("Mode | Live subject workflow", publication_gate_text)
                self.assertIn("Phase | Gather", publication_gate_text)
                self.assertIn("Gather Intake |", publication_gate_text)
                self.assertFalse(bool(getattr(publication_gate, "show_header", True)))
                self.assertEqual(str(getattr(publication_gate, "cursor_type", "")), "none")
                self.assertFalse(bool(getattr(publication_gate, "show_horizontal_scrollbar", True)))
                self.assertIn("Subject summary", _table_text(observation_panel))
                self.assertFalse(bool(getattr(observation_panel, "show_header", True)))
                self.assertEqual(str(getattr(observation_panel, "cursor_type", "")), "none")
                self.assertIn("Last Action: Live subject workflow ready.", review_gate)
                self.assertIn("Do this now: Run the maintained-files check", review_gate)
                self.assertEqual(len(app.query("#learn_status_panel")), 0)
                self.assertEqual(str(getattr(review_gate_next, "label", "")), "Check Maintained Files")
                self.assertEqual(str(getattr(publication_gate_next, "label", "")), "")
                self.assertTrue(any("Gather Journal: Kinematics Demo" in str(line) for line in learn_result.lines))

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_empty_state_guides_user_to_markdown_ingress(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                review_gate = str(app.query_one("#subject_research_review_gate_summary").render())
                learn_result = app.query_one("#learn_result")
                review_gate_next_one = app.query_one("#subject_research_review_gate_action_1_button")
                review_gate_next_two = app.query_one("#subject_research_review_gate_action_2_button")
                publication_gate_next_one = app.query_one("#subject_research_publication_gate_action_1_button")
                publication_gate_next_two = app.query_one("#subject_research_publication_gate_action_2_button")
                publication_gate = app.query_one(f"#{_subject_gate_status_table_id('research', 'publication')}")
                publication_gate_text = _table_text(publication_gate)
                self.assertEqual(len(app.query("#subject_research_publication_gate_summary")), 0)
                self.assertIn("Subject | No subject yet", publication_gate_text)
                self.assertIn("Gather | 0 sources, 0 deltas, 0 items", publication_gate_text)
                self.assertIn("Last Action: Live subject workflow ready.", review_gate)
                self.assertIn("Do this now: Create the first subject", review_gate)
                self.assertEqual(str(getattr(review_gate_next_one, "label", "")), "Ask Follow-up In Chat")
                self.assertEqual(str(getattr(review_gate_next_two, "label", "")), "Import Markdown File")
                self.assertEqual(len(app.query("#learn_status_panel")), 0)
                self.assertEqual(str(getattr(publication_gate_next_one, "label", "")), "")
                self.assertEqual(str(getattr(publication_gate_next_two, "label", "")), "")
                self.assertGreater(int(getattr(review_gate_next_one.region, "height", 0) or 0), 0)
                self.assertFalse(bool(getattr(publication_gate_next_one, "display", True)))
                self.assertFalse(bool(getattr(publication_gate_next_two, "display", True)))
                self.assertIn("Import Markdown File", "\n".join(str(line) for line in learn_result.lines))

                action_one = app.query_one("#subject_research_action_1_button")
                action_two = app.query_one("#subject_research_action_2_button")
                action_three = app.query_one("#subject_research_action_3_button")
                action_four = app.query_one("#subject_research_action_4_button")
                self.assertEqual(str(getattr(action_one, "label", "")), "Refresh Subjects")
                self.assertEqual(str(getattr(action_two, "label", "")), "")
                self.assertEqual(str(getattr(action_three, "label", "")), "")
                self.assertEqual(str(getattr(action_four, "label", "")), "")
                self.assertFalse(getattr(action_one, "disabled", False))
                self.assertFalse(bool(getattr(action_two, "display", True)))
                self.assertFalse(bool(getattr(action_three, "display", True)))
                self.assertFalse(bool(getattr(action_four, "display", True)))

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_empty_state_follow_up_action_switches_to_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test() as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "chat_tab")
                transcript = app._state.transcript_text()
                self.assertIn("Moved to Chat for a follow-up question.", transcript)

        asyncio.run(_exercise())

    def test_textual_research_tab_layout_keeps_research_actions_in_visible_controls_band(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(160, 45)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                controls_panel = app.query_one("#learn_actions_panel")
                action_one = app.query_one("#subject_research_action_1_button")
                action_four = app.query_one("#subject_research_action_4_button")
                review_gate = app.query_one("#subject_research_review_gate_panel")
                publication_gate = app.query_one("#subject_research_publication_gate_panel")
                review_gate_next = app.query_one("#subject_research_review_gate_action_1_button")
                publication_gate_next = app.query_one("#subject_research_publication_gate_action_1_button")
                self.assertGreater(int(getattr(controls_panel.size, "height", 0) or 0), 0)
                self.assertLess(int(getattr(review_gate.region, "y", 0) or 0), int(getattr(controls_panel.region, "y", 0) or 0))
                self.assertLess(int(getattr(publication_gate.region, "y", 0) or 0), int(getattr(controls_panel.region, "y", 0) or 0))
                self.assertEqual(len(app.query("#learn_status_panel")), 0)
                self.assertGreater(int(getattr(review_gate_next.region, "height", 0) or 0), 0)
                self.assertLess(int(getattr(review_gate_next.region, "y", 0) or 0), int(getattr(controls_panel.region, "y", 0) or 0))
                publication_gate_next_label = str(getattr(publication_gate_next, "label", "") or "")
                if publication_gate_next_label:
                    self.assertGreater(int(getattr(publication_gate_next.region, "height", 0) or 0), 0)
                    self.assertLess(int(getattr(publication_gate_next.region, "y", 0) or 0), int(getattr(controls_panel.region, "y", 0) or 0))
                else:
                    self.assertFalse(bool(getattr(publication_gate_next, "display", True)))

        asyncio.run(_exercise())

    def test_textual_subject_header_keeps_journal_below_subject_navigation(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(160, 45)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                prev_button = app.query_one("#subject_prev_button")
                next_button = app.query_one("#subject_next_button")
                journal_button = app.query_one("#subject_research_journal_button")

                self.assertEqual(
                    int(getattr(prev_button.region, "y", 0) or 0),
                    int(getattr(next_button.region, "y", 0) or 0),
                )
                self.assertGreater(
                    int(getattr(journal_button.region, "y", 0) or 0),
                    int(getattr(next_button.region, "y", 0) or 0),
                )
                self.assertGreaterEqual(
                    int(getattr(prev_button.region, "width", 0) or 0),
                    len("Previous Subject") + 2,
                )
                self.assertGreaterEqual(
                    int(getattr(next_button.region, "width", 0) or 0),
                    len("Next Subject") + 2,
                )
                self.assertGreaterEqual(
                    int(getattr(journal_button.region, "width", 0) or 0),
                    len("Journal") + 2,
                )

        asyncio.run(_exercise())

    def test_textual_review_tab_gate_panels_share_height(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(160, 45)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                review_gate = app.query_one("#subject_review_review_gate_panel")
                publication_gate = app.query_one("#subject_review_publication_gate_panel")
                self.assertGreater(int(getattr(review_gate.region, "height", 0) or 0), 0)
                self.assertFalse(bool(getattr(publication_gate, "display", True)))

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_clicking_learn_markdown_updates_ingress_state(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = self.workspace / "notes" / "kinematics.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text("# Kinematics Demo\n\nVelocity is displacement per unit time.\n", encoding="utf-8")

        def _fake_result(*args, **kwargs):
            del args, kwargs
            unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id="kinematics-demo",
                    unit_kind="definition",
                    canonical_title="Velocity",
                ),
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
                statement="Velocity is displacement per unit time.",
                provenance_refs=(),
                status="admitted",
            )
            persist_learning_context(
                self.root,
                LearningContext(
                    subject_id="kinematics-demo",
                    canonical_title="Kinematics Demo",
                    aliases=("Kinematics Demo",),
                    subject_family="Physics / Kinematics",
                    summary="Maintained subject for introductory kinematics.",
                    units=(unit,),
                    linked_source_ids=(),
                    applied_delta_ids=(),
                    governance_status="active",
                ),
            )
            return SimpleNamespace(
                status="ok",
                message="Staged markdown source for Kinematics Demo.",
                payload={
                    "subject_id": "kinematics-demo",
                    "subject_title": "Kinematics Demo",
                    "context_path": str(self.root / "corpus" / "kinematics-demo" / "context.json"),
                    "staged_source_id": "staged_source_kinematics_demo",
                },
            )

        def _fake_import_result(*args, **kwargs):
            del args, kwargs
            return SimpleNamespace(
                status="ok",
                message="Imported 1 skill from Kinematics Demo.",
                payload={
                    "subject_id": "kinematics-demo",
                    "report": {
                        "subject_id": "kinematics-demo",
                        "context_path": str(self.root / "corpus" / "kinematics-demo" / "context.json"),
                    },
                    "imported_titles": ["Velocity"],
                    "canonical_export_path": "kinematics-demo.learned.md",
                },
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch("workstation.ui.textual.chat_ui.desktop_select_markdown_files", return_value=(markdown_path,)), patch(
                "workstation.runtime.core.subject_host_actions.workstation_stage_markdown_source_action",
                side_effect=_fake_result,
            ), patch(
                "workstation.runtime.core.subject_host_actions.workstation_import_staged_source_action",
                side_effect=_fake_import_result,
            ), patch(
                "workstation.ui.textual.chat_ui.desktop_select_skill_export_path",
                side_effect=AssertionError("learn markdown should not auto-open export selection"),
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app.on_button_pressed(SimpleNamespace(button=app.query_one("#learn_markdown_button")))
                    await pilot.pause()
                    await pilot.pause()
                    ingress = str(app.query_one("#learn_ingress_panel").render())
                    root_tabs = app.query_one("#root_tabs")
                    action_one = app.query_one("#subject_research_action_1_button")
                    action_two = app.query_one("#subject_research_action_2_button")
                    action_three = app.query_one("#subject_research_action_3_button")
                    action_four = app.query_one("#subject_research_action_4_button")
                    current_step = str(app.query_one("#subject_research_review_gate_summary").render())
                    self.assertEqual(len(app.query("#learn_status_panel")), 0)
                    self.assertIn("Markdown Ingress", ingress)
                    self.assertNotIn("Imported 1 skill", app._state.transcript_text())
                    self.assertIn("Stage: Imported 1 skill from Kinematics Demo.", ingress)
                    self.assertIn("Current Subject: Kinematics Demo", str(getattr(root_tabs, "border_title", "")))
                    current_step_action = app.query_one("#subject_research_review_gate_action_1_button")
                    self.assertIn("Do this now: Activate this subject", current_step)
                    self.assertEqual(str(getattr(current_step_action, "label", "")), "Activate Subject")
                    self.assertEqual(str(getattr(action_one, "label", "")), "Ask Follow-up In Chat")
                    self.assertFalse(getattr(action_one, "disabled", False))
                    self.assertEqual(str(getattr(action_two, "label", "")), "")
                    self.assertEqual(str(getattr(action_three, "label", "")), "")
                    self.assertEqual(str(getattr(action_four, "label", "")), "")

        asyncio.run(_exercise())

    def test_textual_research_gate_use_markdown_action_opens_picker_and_updates_ingress_state(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = self.workspace / "notes" / "gate-kinematics.md"
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text("# Gate Kinematics Demo\n\nVelocity is displacement per unit time.\n", encoding="utf-8")

        def _fake_result(*args, **kwargs):
            del args, kwargs
            unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id="gate-kinematics-demo",
                    unit_kind="definition",
                    canonical_title="Velocity",
                ),
                subject_id="gate-kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
                statement="Velocity is displacement per unit time.",
                provenance_refs=(),
                status="admitted",
            )
            persist_learning_context(
                self.root,
                LearningContext(
                    subject_id="gate-kinematics-demo",
                    canonical_title="Gate Kinematics Demo",
                    aliases=("Gate Kinematics Demo",),
                    subject_family="Physics / Kinematics",
                    summary="Maintained subject created through gate action markdown ingress.",
                    units=(unit,),
                    linked_source_ids=(),
                    applied_delta_ids=(),
                    governance_status="active",
                ),
            )
            return SimpleNamespace(
                status="ok",
                message="Staged markdown source for Gate Kinematics Demo.",
                payload={
                    "subject_id": "gate-kinematics-demo",
                    "subject_title": "Gate Kinematics Demo",
                    "context_path": str(self.root / "corpus" / "gate-kinematics-demo" / "context.json"),
                    "staged_source_id": "staged_source_gate_kinematics_demo",
                },
            )

        def _fake_import_result(*args, **kwargs):
            del args, kwargs
            return SimpleNamespace(
                status="ok",
                message="Imported 1 skill from Gate Kinematics Demo.",
                payload={
                    "subject_id": "gate-kinematics-demo",
                    "report": {
                        "subject_id": "gate-kinematics-demo",
                        "context_path": str(self.root / "corpus" / "gate-kinematics-demo" / "context.json"),
                    },
                    "imported_titles": ["Velocity"],
                    "canonical_export_path": "gate-kinematics-demo.learned.md",
                },
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch("workstation.ui.textual.chat_ui.desktop_select_markdown_files", return_value=(markdown_path,)) as select_mock, patch(
                "workstation.runtime.core.subject_host_actions.workstation_stage_markdown_source_action",
                side_effect=_fake_result,
            ), patch(
                "workstation.runtime.core.subject_host_actions.workstation_import_staged_source_action",
                side_effect=_fake_import_result,
            ), patch(
                "workstation.ui.textual.chat_ui.desktop_select_skill_export_path",
                side_effect=AssertionError("gate markdown ingress should not auto-open export selection"),
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app.on_button_pressed(SimpleNamespace(button=app.query_one("#subject_research_review_gate_action_2_button")))
                    await pilot.pause()
                    await pilot.pause()
                    ingress = str(app.query_one("#learn_ingress_panel").render())
                    root_tabs = app.query_one("#root_tabs")
                    self.assertEqual(select_mock.call_count, 1)
                    self.assertIn("Stage: Imported 1 skill from Gate Kinematics Demo.", ingress)
                    self.assertIn("Current Subject: Gate Kinematics Demo", str(getattr(root_tabs, "border_title", "")))

        asyncio.run(_exercise())

    def test_textual_markdown_ingress_text_shows_queued_markdown_files(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        first_markdown = self.workspace / "notes" / "alpha.md"
        second_markdown = self.workspace / "notes" / "beta.md"
        third_markdown = self.workspace / "notes" / "gamma.md"
        app = _TextualWorkstationChatApp(
            root=self.root,
            model=None,
            max_tool_rounds=2,
        )
        app._apply_markdown_state_update(
            selected_path=first_markdown,
            pending_paths=(second_markdown, third_markdown),
            source_label="",
            source_field_label="Markdown",
            ingress_title="Markdown Ingress",
            busy=True,
            status_text="Learning and importing: alpha.md",
        )
        ingress = app._learn_markdown_ingress_text()
        self.assertIn("Markdown Ingress", ingress)
        self.assertIn(str(first_markdown), ingress)
        self.assertIn("Queued: 2 more files", ingress)
        self.assertIn("Up next: beta.md, gamma.md", ingress)

    def test_textual_research_tab_bdd_clicking_learn_url_updates_ingress_state(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source_url = "https://example.test/kinematics"

        def _fake_result(*args, **kwargs):
            del args, kwargs
            unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id="kinematics-url-demo",
                    unit_kind="definition",
                    canonical_title="Velocity",
                ),
                subject_id="kinematics-url-demo",
                unit_kind="definition",
                canonical_title="Velocity",
                statement="Velocity is displacement per unit time.",
                provenance_refs=(),
                status="admitted",
            )
            persist_learning_context(
                self.root,
                LearningContext(
                    subject_id="kinematics-url-demo",
                    canonical_title="Kinematics URL Demo",
                    aliases=("Kinematics URL Demo",),
                    subject_family="Physics / Kinematics",
                    summary="Maintained subject created from URL learning.",
                    units=(unit,),
                    linked_source_ids=(),
                    applied_delta_ids=(),
                    governance_status="active",
                ),
            )
            return SimpleNamespace(
                status="ok",
                message="Staged URL source for Kinematics URL Demo.",
                payload={
                    "subject_id": "kinematics-url-demo",
                    "subject_title": "Kinematics URL Demo",
                    "context_path": str(self.root / "corpus" / "kinematics-url-demo" / "context.json"),
                    "staged_source_id": "staged_source_kinematics-url-demo",
                    "revision_id": "source_revision_kinematics-url-demo",
                    "capture": {
                        "subject_id": "kinematics-url-demo",
                    },
                    "capture_report": {
                        "requested_url": source_url,
                        "final_url": source_url,
                        "title": "Kinematics URL Demo",
                    },
                },
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch("workstation.ui.textual.chat_ui.desktop_prompt_url", return_value=source_url), patch(
                "workstation.runtime.core.subject_host_actions.workstation_learn_url_action",
                side_effect=_fake_result,
            ), patch(
                "workstation.ui.textual.chat_ui.desktop_select_skill_export_path",
                side_effect=AssertionError("learn url should not auto-open export selection"),
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app.on_button_pressed(SimpleNamespace(button=app.query_one("#learn_url_button")))
                    await pilot.pause()
                    await pilot.pause()
                    ingress = str(app.query_one("#learn_ingress_panel").render())
                    root_tabs = app.query_one("#root_tabs")
                    current_step = str(app.query_one("#subject_research_review_gate_summary").render())
                    self.assertIn("URL Ingress", ingress)
                    self.assertIn(f"URL: {source_url}", ingress)
                    self.assertIn("Stage: Staged URL source for Kinematics URL Demo.", ingress)
                    self.assertIn("Do this now: Activate this subject", current_step)
                    self.assertIn("Current Subject: Kinematics URL Demo", str(getattr(root_tabs, "border_title", "")))

        asyncio.run(_exercise())

    def test_textual_research_source_inventory_up_down_persists_selection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="gather-widget-demo",
                canonical_title="Gather Widget Demo",
                aliases=("Gather Widget Demo",),
                subject_family="Research / Sources",
                summary="Source inventory widget demo subject.",
                units=(),
                linked_source_ids=(),
                applied_delta_ids=(),
                governance_status="active",
            ),
        )

        first_source = new_staged_source(
            subject_id="gather-widget-demo",
            title="First Source",
            source_ref="https://example.test/first",
            source_kind="url",
        )
        second_source = new_staged_source(
            subject_id="gather-widget-demo",
            title="Second Source",
            source_ref="https://example.test/second",
            source_kind="url",
        )
        persist_staged_source(self.root, first_source)
        persist_staged_source(self.root, second_source)
        persist_source_revision(
            self.root,
            new_source_revision(
                staged_source_id=first_source.staged_source_id,
                subject_id="gather-widget-demo",
                source_ref=first_source.source_ref,
                revision_kind="capture",
            ),
            markdown_text="# First Source\n\nFirst.\n",
        )
        persist_source_revision(
            self.root,
            new_source_revision(
                staged_source_id=second_source.staged_source_id,
                subject_id="gather-widget-demo",
                source_ref=second_source.source_ref,
                revision_kind="capture",
            ),
            markdown_text="# Second Source\n\nSecond.\n",
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                inventory_panel = app.query_one("#subject_sources_panel")
                self.assertIsInstance(inventory_panel, _FocusableTextualDataTable)
                inventory_panel.focus()
                await pilot.pause()

                initial_selected = str(app._mock_subject_progress().research_selected_staged_source_id)
                await pilot.press("down")
                await pilot.pause()
                moved_selected = str(app._mock_subject_progress().research_selected_staged_source_id)
                await pilot.pause()
                persisted_selected = str(app._mock_subject_progress().research_selected_staged_source_id)

                staged_order = [
                    staged_source.staged_source_id
                    for staged_source in list_staged_sources(self.root, "gather-widget-demo")
                ]
                initial_index = staged_order.index(initial_selected)
                expected_moved = staged_order[min(len(staged_order) - 1, initial_index + 1)]

                self.assertNotEqual(initial_selected, moved_selected)
                self.assertEqual(expected_moved, moved_selected)
                self.assertEqual(moved_selected, persisted_selected)

                await pilot.press("up")
                await pilot.pause()
                returned_selected = str(app._mock_subject_progress().research_selected_staged_source_id)
                self.assertEqual(initial_selected, returned_selected)

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_existing_subject_advances_to_review(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = next(
            scenario
            for scenario in default_subject_scenarios(self.root)
            if scenario.subject_id == "kinematics-demo"
        )
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")
        persist_subject_progress(self.root, "kinematics-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                status_after_open = _table_text(
                    app.query_one(f"#{_subject_gate_status_table_id('research', 'publication')}")
                )
                review_gate_after_open = str(app.query_one("#subject_research_review_gate_summary").render())
                self.assertNotIn("Subject context opened", status_after_open)
                self.assertIn("Last Action:", review_gate_after_open)
                self.assertIn("Do this now: Run the maintained-files check", review_gate_after_open)

                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                root_tabs = app.query_one("#root_tabs")
                review_result = app.query_one("#review_result")
                self.assertEqual(app._active_tab_id(), "review_tab")
                self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                self.assertTrue(any("Review Journal: kinematics-demo" in str(line) for line in review_result.lines))

                current_step = str(app.query_one("#subject_review_review_gate_summary").render())
                current_step_action = app.query_one("#subject_review_review_gate_action_1_button")
                action_one = app.query_one("#subject_review_action_1_button")
                action_two = app.query_one("#subject_review_action_2_button")
                action_three = app.query_one("#subject_review_action_3_button")
                action_four = app.query_one("#subject_review_action_4_button")
                self.assertIn("Do this now: Create the report plan", current_step)
                self.assertEqual(str(getattr(current_step_action, "label", "")), "Create Report Plan")
                self.assertEqual(str(getattr(action_one, "label", "")), "Compare Maintained Files")
                self.assertEqual(str(getattr(action_two, "label", "")), "")
                self.assertEqual(str(getattr(action_three, "label", "")), "")
                self.assertEqual(str(getattr(action_four, "label", "")), "")

        asyncio.run(_exercise())

    def test_textual_research_sources_panel_renders_inventory_as_table(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="gather-table-demo",
                canonical_title="Gather Table Demo",
                aliases=("Gather Table Demo",),
                subject_family="Research / Sources",
                summary="Gather table demo subject.",
                units=(),
                linked_source_ids=(),
                applied_delta_ids=(),
                governance_status="active",
            ),
        )

        source = new_staged_source(
            subject_id="gather-table-demo",
            title="Example Source",
            source_ref="https://example.test/source",
            source_kind="url",
        )
        persist_staged_source(self.root, source)
        persist_source_revision(
            self.root,
            new_source_revision(
                staged_source_id=source.staged_source_id,
                subject_id="gather-table-demo",
                source_ref=source.source_ref,
                revision_kind="capture",
            ),
            markdown_text="# Example Source\n\nCaptured.\n",
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                app._reload_mock_subject_scenarios(preferred_key="gather-table-demo")
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                panel = app.query_one("#subject_sources_panel")
                self.assertIsInstance(panel, _FocusableTextualDataTable)
                self.assertFalse(bool(getattr(panel, "show_header", True)))
                self.assertFalse(bool(getattr(panel, "show_horizontal_scrollbar", True)))
                table_text = _table_text(panel)
                self.assertIn(" | Staged Source Inventory", table_text)
                self.assertIn("Current Set | All Gather Sources", table_text)
                self.assertIn("Find Sources Ready | no", table_text)
                self.assertIn("Sync Source Set Ready | yes", table_text)
                self.assertIn("Apply Set Export Ready | no", table_text)
                self.assertIn("Set | Current: All Gather Sources", table_text)
                self.assertIn("Set | Current: All Gather Sources [1 source, no saved query]", table_text)
                self.assertIn("Set Summary | sources: 1 | query: <none>", table_text)
                self.assertIn("Source | Selected: [url] Example Source", table_text)
                self.assertIn("Status | staged", table_text)
                self.assertIn("Ref | https://example.test/source", table_text)
                self.assertIn("Bundle | missing", table_text)
                self.assertIn("Revisions | 0", table_text)
                self.assertIn(" | Admission State", table_text)

        asyncio.run(_exercise())

    def test_textual_research_selected_source_llm_button_routes_source_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    self.assertIsInstance(app.query_one("#subject_sources_panel"), _FocusableTextualDataTable)
                    self.assertFalse(getattr(app.query_one(f"#{_research_detail_llm_button_id()}"), "disabled", True))
                    app.query_one(f"#{_research_detail_llm_button_id()}").press()
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Curate this selected staged source in Gather.", worker_prompts[0])
            self.assertIn("Selected staged source: Example Source", worker_prompts[0])
            self.assertIn("Treat it as source material only", worker_prompts[0])
            self.assertIn("Return only this format:", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_llm_curation_staged_source_id,
                list_staged_sources(self.root, "example-source")[0].staged_source_id,
            )

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_revision_history_and_latest_change_summary(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                self.assertFalse(app.query_one("#subject_target_panel_shell").display)
                hidden_pane_button = app.query_one("#subject_research_hidden_pane_button")
                self.assertTrue(bool(getattr(hidden_pane_button, "display", False)))
                hidden_pane_button.press()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "subject_target_panel")
                self.assertTrue(app.query_one("#subject_target_panel_shell").display)
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                target_panel_text_normalized = " ".join(target_panel_text.split())
                self.assertIn("Export proposal preview", target_panel_text_normalized)
                self.assertIn(
                    "current admitted, itemized, or draft learnings are not rich enough yet",
                    target_panel_text_normalized,
                )
                revision_table = app.query_one(f"#{_research_source_revision_history_table_id()}")
                self.assertTrue(bool(getattr(revision_table, "display", False)))
                self.assertEqual(int(getattr(revision_table, "row_count", 0) or 0), 1)
                revision_row = tuple(str(cell) for cell in revision_table.get_row_at(0))
                self.assertEqual(revision_row[0], "current")
                self.assertEqual(revision_row[1], "capture")
                change_summary_table = app.query_one(f"#{_research_source_change_summary_table_id()}")
                self.assertTrue(bool(getattr(change_summary_table, "display", False)))
                change_rows = [
                    tuple(str(cell) for cell in change_summary_table.get_row_at(index))
                    for index in range(int(getattr(change_summary_table, "row_count", 0) or 0))
                ]
                self.assertIn(("latest revision kind", "capture"), change_rows)
                self.assertIn(("note", "no prior revision exists yet"), change_rows)

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_export_proposal_preview_from_current_learnings(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-source",
                canonical_title="Example Source",
                aliases=("Example Source",),
                subject_family="Example Source",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="example-source",
                            unit_kind="definition",
                            canonical_title="Cross-border transport modes",
                        ),
                        subject_id="example-source",
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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                target_panel_text_normalized = " ".join(target_panel_text.split())
                self.assertIn("Export proposal preview", target_panel_text_normalized)
                self.assertIn("proposed revision kind: merge", target_panel_text_normalized)
                self.assertIn(
                    "subject summary note: A maintained subject with admitted transport-route learnings.",
                    target_panel_text_normalized,
                )
                self.assertIn(
                    "item note: Cross-border transport modes — Energy resources move through pipelines, shipping, "
                    "interconnectors, and bulk terminals.",
                    target_panel_text_normalized,
                )
                self.assertNotIn("subject summary note: -", target_panel_text_normalized)

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_export_applied_history_for_source_set(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                self.assertIn("Source-set export preview", " ".join(target_panel_text.split()))
                member_export_table = app.query_one(f"#{_research_source_collection_member_export_status_table_id()}")
                self.assertTrue(bool(getattr(member_export_table, "display", False)))
                member_export_rows = [
                    tuple(str(cell) for cell in member_export_table.get_row_at(index))
                    for index in range(int(getattr(member_export_table, "row_count", 0) or 0))
                ]
                self.assertTrue(any(row[0] == "Source One" and row[1] == "merge" and row[2] == "aligned" and row[3] == "0" for row in member_export_rows))
                self.assertTrue(any(row[0] == "Source Two" and row[1] == "merge" and row[2] == "aligned" and row[3] == "0" for row in member_export_rows))
                merge_history_table = app.query_one(f"#{_research_source_collection_merge_export_history_table_id()}")
                self.assertTrue(bool(getattr(merge_history_table, "display", False)))
                merge_history_rows = [
                    tuple(str(cell) for cell in merge_history_table.get_row_at(index))
                    for index in range(int(getattr(merge_history_table, "row_count", 0) or 0))
                ]
                self.assertIn(("members with export-applied revisions", "2"), merge_history_rows)
                self.assertIn(("total export-applied revisions", "2"), merge_history_rows)
                self.assertIn(("members aligned with current export", "2"), merge_history_rows)
                self.assertTrue(
                    any(label.startswith("export event ") and "Source One [export]" in value for label, value in merge_history_rows)
                )
                actionable_table = app.query_one(f"#{_research_source_collection_actionable_export_table_id()}")
                self.assertFalse(bool(getattr(actionable_table, "display", False)))
                export_applied_table = app.query_one(f"#{_research_source_collection_export_applied_table_id()}")
                self.assertTrue(bool(getattr(export_applied_table, "display", False)))
                export_applied_rows = [
                    tuple(str(cell) for cell in export_applied_table.get_row_at(index))
                    for index in range(int(getattr(export_applied_table, "row_count", 0) or 0))
                ]
                self.assertEqual(len(export_applied_rows), 2)
                self.assertTrue(any(row[0] == "Source One" and row[1] == "2" and row[3] == "aligned" for row in export_applied_rows))

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_selected_source_export_applied_target(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_selected_staged_source_export_preview",
        )
        self.assertEqual(apply_result.status_text, "Selected source export preview applied.")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                self.assertIn("Source-set export preview", " ".join(target_panel_text.split()))
                member_export_table = app.query_one(f"#{_research_source_collection_member_export_status_table_id()}")
                self.assertTrue(bool(getattr(member_export_table, "display", False)))
                member_export_rows = [
                    tuple(str(cell) for cell in member_export_table.get_row_at(index))
                    for index in range(int(getattr(member_export_table, "row_count", 0) or 0))
                ]
                self.assertTrue(any(row[0] == "Source One" and row[2] == "aligned" for row in member_export_rows))
                self.assertTrue(any(row[0] == "Source Two" and row[2] == "pending" and row[3] == "2" for row in member_export_rows))
                actionable_table = app.query_one(f"#{_research_source_collection_actionable_export_table_id()}")
                self.assertTrue(bool(getattr(actionable_table, "display", False)))
                actionable_rows = [
                    tuple(str(cell) for cell in actionable_table.get_row_at(index))
                    for index in range(int(getattr(actionable_table, "row_count", 0) or 0))
                ]
                self.assertEqual(actionable_rows, [("Source Two", "pending", "2", "0", "<none>")])
                export_applied_table = app.query_one(f"#{_research_source_collection_export_applied_table_id()}")
                self.assertTrue(bool(getattr(export_applied_table, "display", False)))
                export_applied_rows = [
                    tuple(str(cell) for cell in export_applied_table.get_row_at(index))
                    for index in range(int(getattr(export_applied_table, "row_count", 0) or 0))
                ]
                self.assertEqual(len(export_applied_rows), 1)
                self.assertEqual(export_applied_rows[0][0], "Source One")
                self.assertEqual(export_applied_rows[0][1], "2")
                self.assertEqual(export_applied_rows[0][3], "aligned")

        asyncio.run(_exercise())

    def test_textual_research_target_panel_can_cycle_diff_baseline(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        start_manual = apply_subject_action(
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
            "This source explains the current energy transport routes.\n\n"
            "Keep this as source-only notes.\n",
            encoding="utf-8",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_manual_curation",
        )
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-source",
                unit_kind="definition",
                canonical_title="Energy transport routes",
            ),
            subject_id="example-source",
            unit_kind="definition",
            canonical_title="Energy transport routes",
            statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-source",
                canonical_title="Example Source",
                aliases=("Example Source",),
                subject_family="Example Source",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_merge_back",
            assistant_message_text=(
                "[label]\nExample Source Notes\n\n[text]\n"
                "# Example Source Notes\n\n"
                "This source explains the current energy transport routes.\n\n"
                "Keep this as source-only notes.\n\n"
                "Add maintained notes about how this source should be used during import.\n"
            ),
        )
        persist_subject_progress(self.root, "example-source", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                before_text = _table_text(app.query_one("#subject_target_panel"))
                before_change_summary_table = app.query_one(f"#{_research_source_change_summary_table_id()}")
                before_change_rows = [
                    tuple(str(cell) for cell in before_change_summary_table.get_row_at(index))
                    for index in range(int(getattr(before_change_summary_table, "row_count", 0) or 0))
                ]
                app._apply_mock_subject_action("research", "cycle_research_source_revision_baseline")
                await pilot.pause()
                after_text = _table_text(app.query_one("#subject_target_panel"))
                after_change_summary_table = app.query_one(f"#{_research_source_change_summary_table_id()}")
                after_change_rows = [
                    tuple(str(cell) for cell in after_change_summary_table.get_row_at(index))
                    for index in range(int(getattr(after_change_summary_table, "row_count", 0) or 0))
                ]
                before_text_normalized = " ".join(before_text.split())
                after_text_normalized = " ".join(after_text.split())

                self.assertEqual(start_manual.status_text, "Manual source curation file opened.")
                self.assertIn("Selected diff baseline: manual_curation /", before_text_normalized)
                self.assertIn(("revision flow", "manual_curation → merge"), before_change_rows)
                self.assertIn("Selected diff baseline: capture /", after_text_normalized)
                self.assertIn(("revision flow", "capture → merge"), after_change_rows)

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_export_applied_history_for_source_set(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                self.assertIn("Source-set export preview", " ".join(target_panel_text.split()))
                member_export_table = app.query_one(f"#{_research_source_collection_member_export_status_table_id()}")
                self.assertTrue(bool(getattr(member_export_table, "display", False)))
                member_export_rows = [
                    tuple(str(cell) for cell in member_export_table.get_row_at(index))
                    for index in range(int(getattr(member_export_table, "row_count", 0) or 0))
                ]
                self.assertTrue(any(row[0] == "Source One" and row[1] == "merge" and row[2] == "aligned" and row[3] == "0" for row in member_export_rows))
                self.assertTrue(any(row[0] == "Source Two" and row[1] == "merge" and row[2] == "aligned" and row[3] == "0" for row in member_export_rows))
                merge_history_table = app.query_one(f"#{_research_source_collection_merge_export_history_table_id()}")
                self.assertTrue(bool(getattr(merge_history_table, "display", False)))
                merge_history_rows = [
                    tuple(str(cell) for cell in merge_history_table.get_row_at(index))
                    for index in range(int(getattr(merge_history_table, "row_count", 0) or 0))
                ]
                self.assertIn(("members with export-applied revisions", "2"), merge_history_rows)
                self.assertIn(("total export-applied revisions", "2"), merge_history_rows)
                self.assertIn(("members aligned with current export", "2"), merge_history_rows)
                self.assertTrue(
                    any(label.startswith("export event ") and "Source One [export]" in value for label, value in merge_history_rows)
                )
                actionable_table = app.query_one(f"#{_research_source_collection_actionable_export_table_id()}")
                self.assertFalse(bool(getattr(actionable_table, "display", False)))
                export_applied_table = app.query_one(f"#{_research_source_collection_export_applied_table_id()}")
                self.assertTrue(bool(getattr(export_applied_table, "display", False)))
                export_applied_rows = [
                    tuple(str(cell) for cell in export_applied_table.get_row_at(index))
                    for index in range(int(getattr(export_applied_table, "row_count", 0) or 0))
                ]
                self.assertEqual(len(export_applied_rows), 2)
                self.assertTrue(any(row[0] == "Source One" and row[1] == "2" and row[3] == "aligned" for row in export_applied_rows))

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_selected_source_export_applied_target(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        apply_result = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_selected_staged_source_export_preview",
        )
        self.assertEqual(apply_result.status_text, "Selected source export preview applied.")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                self.assertIn("Source-set export preview", " ".join(target_panel_text.split()))
                member_export_table = app.query_one(f"#{_research_source_collection_member_export_status_table_id()}")
                self.assertTrue(bool(getattr(member_export_table, "display", False)))
                member_export_rows = [
                    tuple(str(cell) for cell in member_export_table.get_row_at(index))
                    for index in range(int(getattr(member_export_table, "row_count", 0) or 0))
                ]
                self.assertTrue(any(row[0] == "Source One" and row[2] == "aligned" for row in member_export_rows))
                self.assertTrue(any(row[0] == "Source Two" and row[2] == "pending" and row[3] == "2" for row in member_export_rows))
                actionable_table = app.query_one(f"#{_research_source_collection_actionable_export_table_id()}")
                self.assertTrue(bool(getattr(actionable_table, "display", False)))
                actionable_rows = [
                    tuple(str(cell) for cell in actionable_table.get_row_at(index))
                    for index in range(int(getattr(actionable_table, "row_count", 0) or 0))
                ]
                self.assertEqual(actionable_rows, [("Source Two", "pending", "2", "0", "<none>")])
                export_applied_table = app.query_one(f"#{_research_source_collection_export_applied_table_id()}")
                self.assertTrue(bool(getattr(export_applied_table, "display", False)))
                export_applied_rows = [
                    tuple(str(cell) for cell in export_applied_table.get_row_at(index))
                    for index in range(int(getattr(export_applied_table, "row_count", 0) or 0))
                ]
                self.assertEqual(len(export_applied_rows), 1)
                self.assertEqual(export_applied_rows[0][0], "Source One")
                self.assertEqual(export_applied_rows[0][1], "2")
                self.assertEqual(export_applied_rows[0][3], "aligned")

        asyncio.run(_exercise())

    def test_textual_research_target_panel_can_cycle_diff_baseline(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        start_manual = apply_subject_action(
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
            "This source explains the current energy transport routes.\n\n"
            "Keep this as source-only notes.\n",
            encoding="utf-8",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_manual_curation",
        )
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-source",
                unit_kind="definition",
                canonical_title="Energy transport routes",
            ),
            subject_id="example-source",
            unit_kind="definition",
            canonical_title="Energy transport routes",
            statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-source",
                canonical_title="Example Source",
                aliases=("Example Source",),
                subject_family="Example Source",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_merge_back",
            assistant_message_text="Earlier assistant reply.",
        )
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="apply_research_source_merge_back",
            assistant_message_text=(
                "[label]\nExample Source Notes\n\n[text]\n"
                "# Example Source Notes\n\n"
                "This source explains the current energy transport routes.\n\n"
                "Keep this as source-only notes.\n\n"
                "Add maintained notes about how this source should be used during import.\n"
            ),
        )
        persist_subject_progress(self.root, "example-source", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                before_text = _table_text(app.query_one("#subject_target_panel"))
                before_change_summary_table = app.query_one(f"#{_research_source_change_summary_table_id()}")
                before_change_rows = [
                    tuple(str(cell) for cell in before_change_summary_table.get_row_at(index))
                    for index in range(int(getattr(before_change_summary_table, "row_count", 0) or 0))
                ]
                app._apply_mock_subject_action("research", "cycle_research_source_revision_baseline")
                await pilot.pause()
                after_text = _table_text(app.query_one("#subject_target_panel"))
                after_change_summary_table = app.query_one(f"#{_research_source_change_summary_table_id()}")
                after_change_rows = [
                    tuple(str(cell) for cell in after_change_summary_table.get_row_at(index))
                    for index in range(int(getattr(after_change_summary_table, "row_count", 0) or 0))
                ]
                before_text_normalized = " ".join(before_text.split())
                after_text_normalized = " ".join(after_text.split())

                self.assertEqual(start_manual.status_text, "Manual source curation file opened.")
                self.assertIn("Selected diff baseline: manual_curation /", before_text_normalized)
                self.assertIn(("revision flow", "manual_curation → merge"), before_change_rows)
                self.assertIn("Selected diff baseline: capture /", after_text_normalized)
                self.assertIn(("revision flow", "capture → merge"), after_change_rows)

        asyncio.run(_exercise())

    def test_textual_research_target_panel_shows_collection_member_revision_and_merge_export_history(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id
        start = apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="start_research_source_collection_source_merge_back",
        )
        self.assertEqual(start.status_text, "LLM set-source merge-back proposal started.")
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
        self.assertEqual(apply_result.status_text, "Set-source merge-back applied.")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                self.assertFalse(app.query_one("#subject_target_panel_shell").display)
                hidden_pane_button = app.query_one("#subject_research_hidden_pane_button")
                self.assertTrue(bool(getattr(hidden_pane_button, "display", False)))
                hidden_pane_button.press()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "subject_target_panel")
                self.assertTrue(app.query_one("#subject_target_panel_shell").display)
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                target_panel_text_normalized = " ".join(target_panel_text.split())
                self.assertIn("Source-set export preview", target_panel_text_normalized)
                member_export_table = app.query_one(f"#{_research_source_collection_member_export_status_table_id()}")
                self.assertTrue(bool(getattr(member_export_table, "display", False)))
                member_export_rows = [
                    tuple(str(cell) for cell in member_export_table.get_row_at(index))
                    for index in range(int(getattr(member_export_table, "row_count", 0) or 0))
                ]
                self.assertEqual(len(member_export_rows), 2)
                member_revision_table = app.query_one(f"#{_research_source_collection_member_revision_table_id()}")
                self.assertTrue(bool(getattr(member_revision_table, "display", False)))
                self.assertGreaterEqual(int(getattr(member_revision_table, "row_count", 0) or 0), 2)
                member_rows = [
                    tuple(str(cell) for cell in member_revision_table.get_row_at(index))
                    for index in range(int(getattr(member_revision_table, "row_count", 0) or 0))
                ]
                source_one_row = next(row for row in member_rows if row[0] == "Source One")
                self.assertEqual(source_one_row[1], "2")
                self.assertEqual(source_one_row[2], "merge")
                self.assertIn("→", source_one_row[3])
                merge_history_table = app.query_one(f"#{_research_source_collection_merge_export_history_table_id()}")
                self.assertTrue(bool(getattr(merge_history_table, "display", False)))
                merge_rows = [
                    tuple(str(cell) for cell in merge_history_table.get_row_at(index))
                    for index in range(int(getattr(merge_history_table, "row_count", 0) or 0))
                ]
                self.assertIn(("member sources", "2"), merge_rows)
                self.assertIn(("members with merge revisions", "2"), merge_rows)
                self.assertIn(("members with export-applied revisions", "0"), merge_rows)

        asyncio.run(_exercise())

    def test_textual_research_merge_back_action_routes_selected_source_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-source",
                unit_kind="definition",
                canonical_title="Energy transport routes",
            ),
            subject_id="example-source",
            unit_kind="definition",
            canonical_title="Energy transport routes",
            statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-source",
                canonical_title="Example Source",
                aliases=("Example Source",),
                subject_family="Example Source",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )

        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app._apply_mock_subject_action("research", "start_research_source_merge_back")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Prepare a merge-back proposal for this selected staged source.", worker_prompts[0])
            self.assertIn("Current learned subject state:", worker_prompts[0])
            self.assertIn("Selected staged source: Example Source", worker_prompts[0])
            self.assertIn("keeping them at the source layer", worker_prompts[0].casefold())
            self.assertEqual(
                app._mock_subject_progress().research_source_merge_back_staged_source_id,
                list_staged_sources(self.root, "example-source")[0].staged_source_id,
            )

        asyncio.run(_exercise())

    def test_textual_research_manual_curation_button_opens_edit_file(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    self.assertFalse(getattr(app.query_one(f"#{_research_detail_manual_rephrase_button_id()}"), "disabled", True))
                    app.query_one(f"#{_research_detail_manual_rephrase_button_id()}").press()
                    await pilot.pause()

            self.assertEqual(len(opened_paths), 1)
            self.assertTrue(opened_paths[0].is_file())

        asyncio.run(_exercise())

    def test_textual_research_source_set_llm_button_routes_collection_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)
        focused_collection = next(
            item
            for item in list_source_collections(self.root, scenario.subject_id)
            if item.collection_id == progress.research_selected_source_collection_id
        )
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    self.assertFalse(getattr(app.query_one(f"#{_research_sources_llm_button_id()}"), "disabled", True))
                    app.query_one(f"#{_research_sources_llm_button_id()}").press()
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Curate this selected Gather source set.", worker_prompts[0])
            self.assertIn(f"Selected source set: {focused_collection.title}", worker_prompts[0])
            self.assertIn("[description]", worker_prompts[0])
            self.assertIn("[query]", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_llm_curation_collection_id,
                focused_collection.collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_research_source_set_discovery_action_routes_collection_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
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
            for item in list_source_collections(self.root, scenario.subject_id)
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
        persist_subject_progress(self.root, scenario.subject_id, progress)
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app._apply_mock_subject_action("research", "start_research_source_collection_discovery")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Find high-value source material for this selected Gather source set.", worker_prompts[0])
            self.assertIn("Selected source set: Energy Export Sources", worker_prompts[0])
            self.assertIn("Saved query/topic: energy exports transport routes", worker_prompts[0])
            self.assertIn("[source]", worker_prompts[0])
            self.assertIn("[url]", worker_prompts[0])
            self.assertIn("[notes]", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_discovery_collection_id,
                focused_collection.collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_chat_find_sources_command_routes_selected_source_set_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
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
            for item in list_source_collections(self.root, scenario.subject_id)
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
        persist_subject_progress(self.root, scenario.subject_id, progress)
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/find-sources"
                    await pilot.press("enter")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Find high-value source material for this selected Gather source set.", worker_prompts[0])
            self.assertIn("Selected source set: Energy Export Sources", worker_prompts[0])
            self.assertIn("Saved query/topic: energy exports transport routes", worker_prompts[0])
            self.assertIn(
                "Started a Gather source-discovery turn in Chat.",
                app._state.transcript_text(),
            )

        asyncio.run(_exercise())

    def test_textual_chat_edit_source_command_opens_manual_source_curation_file(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source",
            )

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        persist_subject_progress(self.root, scenario.subject_id, progress)
        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/edit-source"
                    await pilot.press("enter")
                    await pilot.pause()

            self.assertEqual(len(opened_paths), 1)
            self.assertTrue(opened_paths[0].is_file())
            self.assertIn(
                "Manual source curation file opened.",
                app._state.transcript_text(),
            )

        asyncio.run(_exercise())

    def test_textual_chat_edit_source_set_command_opens_manual_source_set_curation_file(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)
        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/edit-source-set"
                    await pilot.press("enter")
                    await pilot.pause()

            self.assertEqual(len(opened_paths), 1)
            self.assertTrue(opened_paths[0].is_file())
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_manual_curation_collection_id,
                progress.research_selected_source_collection_id,
            )
            self.assertIn(
                "Manual source-set curation file opened.",
                app._state.transcript_text(),
            )

        asyncio.run(_exercise())

    def test_textual_chat_create_source_set_command_creates_focused_collection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged_result = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                input_widget.value = "/create-source-set"
                await pilot.press("enter")
                await pilot.pause()

            manual_collections = [
                item for item in list_source_collections(self.root, scenario.subject_id)
                if collapse_ws(item.metadata.get("collection_kind", "")) == "manual"
            ]
            self.assertEqual(len(manual_collections), 1)
            self.assertEqual(
                collapse_ws(app._mock_subject_progress().research_selected_source_collection_id),
                manual_collections[0].collection_id,
            )
            self.assertIn("Source set created.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_chat_create_source_set_from_query_command_creates_topic_query_collection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                input_widget.value = "/create-source-set-from-query Energy Route Sources | energy exports transport routes | Sources for cross-border energy routing."
                await pilot.press("enter")
                await pilot.pause()

            created_collection = next(
                item
                for item in list_source_collections(self.root, scenario.subject_id)
                if collapse_ws(item.metadata.get("collection_kind", "")) == "topic_query"
            )
            self.assertEqual(created_collection.query_text, "energy exports transport routes")
            self.assertEqual(
                collapse_ws(app._mock_subject_progress().research_selected_source_collection_id),
                created_collection.collection_id,
            )
            self.assertIn("Source set created from query.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_chat_synthesize_source_set_command_routes_selected_set_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged_result = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
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
                description="Sources about energy exports and how they move across borders.",
                query_text="energy exports transport routes",
            ),
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/synthesize-source-set"
                    await pilot.press("enter")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Synthesize this selected Gather source set", worker_prompts[0])
            self.assertIn("Selected source set: Energy Export Sources", worker_prompts[0])
            self.assertIn("[summary]", worker_prompts[0])
            self.assertIn("[questions]", worker_prompts[0])
            self.assertIn("[query]", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_synthesis_collection_id,
                focused_collection.collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_chat_refresh_source_command_refreshes_selected_source(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        initial_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nInitial notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577605000,
            markdown_text="# Example Source\n\nRefreshed notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source refreshed</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=initial_capture):
            staged_result = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("url_learning_capture.capture_url_learning_bundle", return_value=refreshed_capture):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/refresh-source"
                    await pilot.press("enter")
                    await pilot.pause()

            refreshed_source = next(
                item for item in list_staged_sources(self.root, scenario.subject_id)
                if item.staged_source_id == str(staged_result.payload["staged_source_id"])
            )
            self.assertEqual(int(refreshed_source.revision_count or 0), 2)
            self.assertIn("Selected staged source refreshed.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_chat_sync_source_set_command_syncs_selected_collection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        initial_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nInitial notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        refreshed_capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577605000,
            markdown_text="# Example Source\n\nSynced notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source synced</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=initial_capture):
            staged_result = workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(
            item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source"
        )
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("url_learning_capture.capture_url_learning_bundle", return_value=refreshed_capture):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#input")
                    input_widget = app.query_one("#input")
                    input_widget.value = "/sync-source-set"
                    await pilot.press("enter")
                    await pilot.pause()

            selected_source = next(
                item for item in list_staged_sources(self.root, scenario.subject_id)
                if item.staged_source_id == str(staged_result.payload["staged_source_id"])
            )
            self.assertEqual(int(selected_source.revision_count or 0), 2)
            self.assertIn("Selected source set synced.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_chat_apply_source_export_command_applies_selected_preview(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nInitial source notes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            staged_result = workstation_learn_url_action(
                root_path=self.root,
                source_url="https://example.test/source",
                subject_id="energy-exports",
                subject_title="Energy Exports",
            )

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
        progress.research_selected_staged_source_id = str(staged_result.payload["staged_source_id"])
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                input_widget.value = "/apply-source-export"
                await pilot.press("enter")
                await pilot.pause()

            selected_source = next(
                item for item in list_staged_sources(self.root, scenario.subject_id)
                if item.staged_source_id == str(staged_result.payload["staged_source_id"])
            )
            self.assertEqual(int(selected_source.revision_count or 0), 2)
            self.assertIn("Selected source export preview applied.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_chat_apply_source_set_export_command_applies_selected_collection_preview(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#input")
                input_widget = app.query_one("#input")
                input_widget.value = "/apply-source-set-export"
                await pilot.press("enter")
                await pilot.pause()

            updated_sources = {
                item.staged_source_id: int(item.revision_count or 0)
                for item in list_staged_sources(self.root, scenario.subject_id)
            }
            self.assertEqual(updated_sources[str(first_result.payload["staged_source_id"])], 2)
            self.assertEqual(updated_sources[str(second_result.payload["staged_source_id"])], 2)
            self.assertIn("Set export preview applied.", app._state.transcript_text())

        asyncio.run(_exercise())

    def test_textual_research_source_set_merge_back_action_routes_collection_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="example-source",
                unit_kind="definition",
                canonical_title="Cross-border transport modes",
            ),
            subject_id="example-source",
            unit_kind="definition",
            canonical_title="Cross-border transport modes",
            statement="Energy resources move through pipelines, shipping, interconnectors, and bulk terminals.",
            provenance_refs=(),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="example-source",
                canonical_title="Example Source",
                aliases=("Example Source",),
                subject_family="Example Source",
                summary="A maintained subject with admitted transport-route learnings.",
                units=(unit,),
                linked_source_ids=(),
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
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
            for item in list_source_collections(self.root, scenario.subject_id)
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
        persist_subject_progress(self.root, scenario.subject_id, progress)
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app._apply_mock_subject_action("research", "start_research_source_collection_merge_back")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Prepare a merge-back proposal for this selected Gather source set.", worker_prompts[0])
            self.assertIn("Selected source set: Energy Export Sources", worker_prompts[0])
            self.assertIn("Current learned subject state:", worker_prompts[0])
            self.assertIn("[description]", worker_prompts[0])
            self.assertIn("[query]", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_merge_back_collection_id,
                focused_collection.collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_research_set_source_merge_back_action_routes_multi_source_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "energy-exports")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = collection.collection_id
        persist_subject_progress(self.root, scenario.subject_id, progress)
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    app._apply_mock_subject_action("research", "start_research_source_collection_source_merge_back")
                    await pilot.pause()

            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Prepare merge-back proposals for the member staged sources in this selected Gather source set.", worker_prompts[0])
            self.assertIn("Selected source set: Energy Export Sources", worker_prompts[0])
            self.assertIn("Current learned subject state:", worker_prompts[0])
            self.assertIn("[source]", worker_prompts[0])
            self.assertIn("[url]", worker_prompts[0])
            self.assertIn("[label]", worker_prompts[0])
            self.assertIn("[text]", worker_prompts[0])
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_source_merge_back_collection_id,
                collection.collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_research_source_set_sync_action_is_visible_and_runs(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch("url_learning_capture.capture_url_learning_bundle", side_effect=[refreshed_one, refreshed_two]):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    action_buttons = [
                        app.query_one(f"#subject_research_action_{index}_button")
                        for index in range(1, 5)
                    ]
                    labels = [str(getattr(button, "label", "") or "") for button in action_buttons]
                    self.assertIn("Sync Source Set", labels)
                    sync_button = next(button for button in action_buttons if str(getattr(button, "label", "") or "") == "Sync Source Set")
                    sync_button.press()
                    await pilot.pause()

                    refreshed_sources = list_staged_sources(self.root, "energy-exports")
                    self.assertTrue(refreshed_sources)
                    self.assertTrue(all(int(getattr(source, "revision_count", 0) or 0) >= 2 for source in refreshed_sources))

        asyncio.run(_exercise())

    def test_textual_research_source_set_manual_curation_button_opens_edit_file(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from url_learning_capture import CapturedUrlLearningBundle
        from workstation.runtime.core.workstation_core import workstation_learn_url_action

        capture = CapturedUrlLearningBundle(
            requested_url="https://example.test/source",
            final_url="https://example.test/source",
            title="Example Source",
            media_type="text/html",
            status_code=200,
            fetched_at_epoch_ms=1712577600000,
            markdown_text="# Example Source\n\nThis source explains the current energy transport routes.\n",
            bundle_files={
                "rendered.html": "<html><body>Example Source</body></html>",
                "elements.json": "[]",
                "asset-manifest.json": "[]",
            },
            metadata={"requested_url": "https://example.test/source"},
            elements=(),
            asset_manifest=(),
        )
        with patch("url_learning_capture.capture_url_learning_bundle", return_value=capture):
            workstation_learn_url_action(root_path=self.root, source_url="https://example.test/source")

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "example-source")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="create_source_collection_from_selected_staged_source",
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)
        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    self.assertFalse(getattr(app.query_one(f"#{_research_sources_manual_rephrase_button_id()}"), "disabled", True))
                    app.query_one(f"#{_research_sources_manual_rephrase_button_id()}").press()
                    await pilot.pause()

            self.assertEqual(len(opened_paths), 1)
            self.assertTrue(opened_paths[0].is_file())
            self.assertEqual(
                app._mock_subject_progress().research_source_collection_manual_curation_collection_id,
                progress.research_selected_source_collection_id,
            )

        asyncio.run(_exercise())

    def test_textual_gather_tab_bdd_check_maintained_advances_to_review_when_report_plan_is_next(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
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
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = next(
            scenario
            for scenario in default_subject_scenarios(self.root)
            if scenario.subject_id == "kinematics-demo"
        )
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "learn_tab")

                current_step_action = app.query_one("#subject_research_review_gate_action_1_button")
                self.assertEqual(str(getattr(current_step_action, "label", "")), "Check Maintained Files")

                current_step_action.press()
                await pilot.pause()
                await pilot.pause()

                if app._active_tab_id() == "learn_tab":
                    current_step_after_compare = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="research",
                        label="Create Report Plan",
                    )
                    self.assertTrue(current_step_after_compare.has_class("subject_gate_action_button_phase_nav"))
                    current_step_after_compare.press()
                    await pilot.pause()
                    await pilot.pause()

                self.assertEqual(app._active_tab_id(), "review_tab")
                gather_gate_after_compare = str(app.query_one("#subject_review_review_gate_summary").render())
                current_step_after_compare = app.query_one("#subject_review_review_gate_action_1_button")
                self.assertIn("Create the report plan", gather_gate_after_compare)
                self.assertIn("The maintained-files check completed and the files are aligned.", gather_gate_after_compare)
                self.assertIn("Last Action: Projection comparison aligned.", gather_gate_after_compare)
                self.assertEqual(str(getattr(current_step_after_compare, "label", "")), "Create Report Plan")

        asyncio.run(_exercise())

    def test_textual_gather_tab_bdd_after_check_maintained_advances_to_itemize_and_focuses_generate(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = self.workspace / "trials" / "fresh-gather.md"
        markdown_path.write_text(
            "# Fresh Gather Demo\n\n"
            "Velocity is displacement per unit time.\n",
            encoding="utf-8",
        )
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                activate_action = app.query_one("#subject_research_review_gate_action_1_button")
                self.assertEqual(str(getattr(activate_action, "label", "")), "Activate Subject")
                activate_action.press()
                await pilot.pause()

                maintained_action = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="research",
                    label="Check Maintained Files",
                )
                self.assertEqual(str(getattr(maintained_action, "label", "")), "Check Maintained Files")
                maintained_action.press()
                await pilot.pause()
                await pilot.pause()

                current_step_action = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="research",
                    label="Generate Itemization",
                )
                self.assertTrue(current_step_action.has_class("subject_gate_action_button_phase_nav"))
                current_step_action.press()
                await pilot.pause()

                for _ in range(10):
                    if app._active_tab_id() == "itemize_tab":
                        break
                    await pilot.pause()
                self.assertEqual(app._active_tab_id(), "itemize_tab")
                action_one = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="itemize",
                    label="Generate Itemization",
                )
                current_step = str(app.query_one("#subject_itemize_review_gate_summary").render())
                action_two = app.query_one("#subject_itemize_review_gate_action_2_button")
                action_three = app.query_one("#subject_itemize_review_gate_action_3_button")
                action_four = app.query_one("#subject_itemize_review_gate_action_4_button")

                self.assertIn("Generate the itemization inventory", current_step)
                self.assertEqual(str(getattr(action_one, "label", "")), "Generate Itemization")
                self.assertEqual(str(getattr(action_two, "label", "")), "")
                self.assertEqual(str(getattr(action_three, "label", "")), "")
                self.assertEqual(str(getattr(action_four, "label", "")), "")

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_generates_and_previews_itemization_inventory(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
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
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = next(
            scenario
            for scenario in default_subject_scenarios(self.root)
            if scenario.subject_id == "kinematics-demo"
        )
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()

                current_step_action_one = app.query_one("#subject_research_review_gate_action_1_button")
                current_step_action_two = app.query_one("#subject_research_review_gate_action_2_button")
                current_step_action_three = app.query_one("#subject_research_review_gate_action_3_button")
                current_step_action_four = app.query_one("#subject_research_review_gate_action_4_button")
                self.assertEqual(str(getattr(current_step_action_one, "label", "")), "Check Maintained Files")
                self.assertEqual(str(getattr(current_step_action_two, "label", "")), "Select As Import Source")
                self.assertEqual(str(getattr(current_step_action_three, "label", "")), "Refresh Itemization")
                self.assertEqual(str(getattr(current_step_action_four, "label", "")), "Preview Maintained Files")

                hidden_pane_button = app.query_one("#subject_research_hidden_pane_button")
                self.assertTrue(bool(getattr(hidden_pane_button, "display", False)))
                hidden_pane_button.press()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "subject_target_panel")
                self.assertTrue(app.query_one("#subject_target_panel_shell").display)

        asyncio.run(_exercise())

    def test_textual_research_cross_phase_itemize_action_navigates_without_running_itemization(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n",
        )
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = next(
            scenario
            for scenario in default_subject_scenarios(self.root)
            if scenario.subject_id == "kinematics-demo"
        )
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="compare_projections")
        persist_subject_progress(self.root, "kinematics-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                current_step_action = app.query_one("#subject_research_review_gate_action_1_button")
                self.assertEqual(str(getattr(current_step_action, "label", "")), "Generate Itemization")
                self.assertTrue(current_step_action.has_class("subject_gate_action_button_phase_nav"))

                current_step_action.press()
                await pilot.pause()

                for _ in range(10):
                    if app._active_tab_id() == "itemize_tab":
                        break
                    await pilot.pause()
                self.assertEqual(app._active_tab_id(), "itemize_tab")
                itemize_step = str(app.query_one("#subject_itemize_review_gate_summary").render())
                itemize_action = app.query_one("#subject_itemize_review_gate_action_1_button")
                itemize_status = _table_text(
                    app.query_one(f"#{_subject_gate_status_table_id('itemize', 'publication')}")
                )
                self.assertIn("Generate the itemization inventory", itemize_step)
                self.assertEqual(str(getattr(itemize_action, "label", "")), "Generate Itemization")
                self.assertEqual(len(app.query("#subject_itemize_publication_gate_summary")), 0)
                self.assertIn("Itemization | not generated yet", itemize_status)
                self.assertEqual(len(app.query("#itemize_status_panel")), 0)

        asyncio.run(_exercise())

    def test_textual_subject_page_title_renders_above_gate_bar_for_shared_subject_tabs(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n",
        )
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        phase_specs = (
            ("research", "learn_tab", "research_gate_bar", "subject_prev_button", "subject_next_button"),
            ("itemize", "itemize_tab", "itemize_gate_bar", _subject_nav_button_id("itemize", "prev"), _subject_nav_button_id("itemize", "next")),
            ("draft", "draft_tab", "draft_gate_bar", _subject_nav_button_id("draft", "prev"), _subject_nav_button_id("draft", "next")),
            ("review", "review_tab", "review_gate_bar", _subject_nav_button_id("review", "prev"), _subject_nav_button_id("review", "next")),
            ("publication", "publication_tab", "publication_gate_bar", _subject_nav_button_id("publication", "prev"), _subject_nav_button_id("publication", "next")),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()

                for phase, tab_id, gate_bar_id, prev_id, next_id in phase_specs:
                    await pilot.click(f"#tab_button_{tab_id}")
                    await pilot.pause()
                    root_tabs = app.query_one("#root_tabs")
                    title_widget = app.query_one(f"#{_subject_header_subject_id(phase)}")
                    gate_bar = app.query_one(f"#{gate_bar_id}")
                    prev_button = app.query_one(f"#{prev_id}")
                    next_button = app.query_one(f"#{next_id}")
                    self.assertFalse(title_widget.display)
                    self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                    self.assertIn("Kinematics Demo", str(getattr(root_tabs, "border_title", "")))
                    self.assertLess(int(prev_button.region.y), int(gate_bar.region.y))
                    self.assertEqual(int(prev_button.region.y), int(next_button.region.y))
                    self.assertLess(int(prev_button.region.x), int(next_button.region.x))

        asyncio.run(_exercise())

    def test_textual_current_step_surfaces_last_action_and_secondary_gate_matches_phase_layout(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n",
        )
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        phase_specs = (
            ("research", "learn_tab"),
            ("itemize", "itemize_tab"),
            ("draft", "draft_tab"),
            ("review", "review_tab"),
            ("publication", "publication_tab"),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                for phase, tab_id in phase_specs:
                    await pilot.click(f"#tab_button_{tab_id}")
                    await pilot.pause()
                    current_step = str(app.query_one(f"#{_subject_gate_summary_id(phase, 'review')}").render())
                    secondary_gate = app.query_one(f"#{_subject_gate_panel_id(phase, 'publication')}")
                    self.assertIn("Last Action:", current_step)
                    self.assertEqual(len(app.query(f"#{_subject_last_action_panel_id(phase)}")), 0)
                    if phase in {"research", "itemize", "draft"}:
                        secondary_summary = _table_text(
                            app.query_one(f"#{_subject_gate_status_table_id(phase, 'publication')}")
                        )
                        self.assertTrue(secondary_gate.display)
                        self.assertIn("Mode | Live subject workflow", secondary_summary)
                        self.assertIn("Subject | Kinematics Demo", secondary_summary)
                    else:
                        secondary_summary = str(app.query_one(f"#{_subject_gate_summary_id(phase, 'publication')}").render())
                        self.assertFalse(secondary_gate.display)
                        self.assertEqual("", secondary_summary)

        asyncio.run(_exercise())

    def test_textual_itemize_tab_bdd_shows_item_inventory_and_workspace(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
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
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                activate_action = app.query_one("#subject_research_review_gate_action_1_button")
                self.assertEqual(str(getattr(activate_action, "label", "")), "Activate Subject")
                activate_action.press()
                await pilot.pause()

                maintained_action = app.query_one("#subject_research_review_gate_action_1_button")
                self.assertEqual(str(getattr(maintained_action, "label", "")), "Check Maintained Files")
                maintained_action.press()
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "itemize_tab")
                root_tabs = app.query_one("#root_tabs")
                status_panel = _table_text(
                    app.query_one(f"#{_subject_gate_status_table_id('itemize', 'publication')}")
                )
                current_step = str(app.query_one("#subject_itemize_review_gate_summary").render())
                current_step_action = app.query_one("#subject_itemize_review_gate_action_1_button")
                self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                self.assertEqual(len(app.query("#subject_itemize_publication_gate_summary")), 0)
                self.assertIn("Itemization | not generated yet", status_panel)
                self.assertIn("Generate the itemization inventory", current_step)
                self.assertEqual(str(getattr(current_step_action, "label", "")), "Generate Itemization")
                self.assertEqual(len(app.query("#itemize_status_panel")), 0)

                current_step_action.press()
                for _ in range(40):
                    await pilot.pause()
                    refreshed_action = app.query_one("#subject_itemize_review_gate_action_1_button")
                    detail_panel = app.query_one("#itemize_detail_panel")
                    detail_text = _table_text(detail_panel)
                    detail_title = str(app.query_one("#itemize_detail_panel_title").render())
                    if (
                        str(getattr(refreshed_action, "label", "")) == "Promote Item"
                        and "Kind |" in detail_text
                        and "No itemized candidates" not in detail_text
                        and "Acceleration From Velocity Change" in detail_title
                    ):
                        break
                else:
                    self.fail("Generate Itemization did not materialize the itemize workspace in time")

                inventory_text = "\n".join(str(line) for line in app.query_one("#itemize_inventory_panel").lines)
                detail_panel = app.query_one("#itemize_detail_panel")
                detail_text = _table_text(detail_panel)
                target_text = _table_text(app.query_one("#itemize_target_panel"))
                result_text = "\n".join(str(line) for line in app.query_one("#itemize_result").lines)
                current_step = str(app.query_one("#subject_itemize_review_gate_summary").render())
                refreshed_action = app.query_one("#subject_itemize_review_gate_action_1_button")
                detail_title = str(app.query_one("#itemize_detail_panel_title").render())
                itemize_more_action_labels = [
                    str(getattr(app.query_one(f"#subject_itemize_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_itemize_action_{index}_button"), "display", False))
                ]

                self.assertFalse(app.query_one("#itemize_target_panel_shell").display)
                self.assertIn(
                    "Item Inventory",
                    str(app.query_one("#itemize_inventory_panel_title").render()),
                )
                self.assertIn("Kind |", detail_text)
                self.assertNotIn("Current Item", detail_text)
                self.assertNotIn("Label |", detail_text)
                self.assertIn("Itemize Target", target_text)
                self.assertIn("Itemize Journal: kinematics-demo", result_text)
                self.assertIn("Acceleration From Velocity Change", detail_title)
                self.assertIn("Last Action: Itemization generated.", current_step)
                self.assertFalse(bool(getattr(detail_panel, "show_header", True)))
                self.assertEqual(str(getattr(detail_panel, "cursor_type", "")), "none")
                self.assertFalse(bool(getattr(detail_panel, "show_horizontal_scrollbar", True)))
                self.assertEqual(str(getattr(refreshed_action, "label", "")), "Promote Item")
                self.assertNotIn("Hold For Merge", itemize_more_action_labels)
                self.assertNotIn("Go To Draft", itemize_more_action_labels)

        asyncio.run(_exercise())

    def test_textual_itemize_decision_role_select_updates_selected_item(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="itemize-select-demo",
            title="Itemize Select Notes",
            source_ref="notes/itemize-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Controls Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="itemize-select-demo",
            source_kind="markdown",
            rationale="Admit itemize select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="itemize-select-demo",
                canonical_title="Itemize Select Demo",
                aliases=("Itemize Select Demo",),
                subject_family="Governance",
                summary="Itemize select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="itemize-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="itemize-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()
                app.query_one("#subject_itemize_review_gate_action_1_button").press()
                await pilot.pause()

                role_select = app.query_one(f"#{_itemize_decision_role_select_id()}")
                self.assertFalse(bool(getattr(role_select, "disabled", True)))

                self.assertTrue(getattr(role_select, "display", True))
                self.assertEqual(str(getattr(role_select, "prompt", "")), "Decision Role")

                hold_switch = app.query_one(f"#{_itemize_hold_switch_id()}")
                self.assertFalse(bool(getattr(hold_switch, "disabled", True)))
                self.assertTrue(getattr(hold_switch, "display", True))

        asyncio.run(_exercise())

    def test_textual_itemize_detail_pane_can_maximize_and_restore(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="itemize-max-demo",
            title="Itemize Max Notes",
            source_ref="notes/itemize-max.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Itemize Max Notes\n\n"
                "## Selected Candidate\n\n"
                "This candidate should appear in the item detail pane.\n\n"
                "$$ y = m x + b $$\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="itemize-max-demo",
            source_kind="markdown",
            rationale="Admit the itemize maximize subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="itemize-max-demo",
                unit_kind="definition",
                canonical_title="Selected Candidate",
            ),
            subject_id="itemize-max-demo",
            unit_kind="definition",
            canonical_title="Selected Candidate",
            statement="This candidate should appear in the item detail pane.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="itemize-max-demo",
                canonical_title="Itemize Max Demo",
                aliases=("Itemize Max Demo",),
                subject_family="Physics",
                summary="A maintained subject for item detail maximize behavior.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()
                app.query_one("#subject_itemize_review_gate_action_1_button").press()
                await pilot.pause()

                await pilot.click("#itemize_detail_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "itemize_detail_panel")

                app.action_toggle_maximized_pane()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "itemize_detail_panel")
                self.assertTrue(app.query_one("#subject_itemize_workbench").display)
                self.assertTrue(app.query_one("#itemize_detail_wrapper").display)
                self.assertEqual(len(app.query("#itemize_status_panel")), 0)

                app.action_toggle_maximized_pane()
                await pilot.pause()
                self.assertIsNone(app._maximized_pane_id)
                self.assertTrue(app.query_one("#itemize_detail_wrapper").display)

        asyncio.run(_exercise())

    def test_textual_draft_semantic_kind_select_is_present_for_selected_item(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="draft-select-demo",
            title="Draft Select Notes",
            source_ref="notes/draft-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="draft-select-demo",
            source_kind="markdown",
            rationale="Admit draft select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="draft-select-demo",
                canonical_title="Draft Select Demo",
                aliases=("Draft Select Demo",),
                subject_family="Governance",
                summary="Draft select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="draft-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="draft-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()
                app.query_one("#subject_itemize_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                semantic_select = app.query_one(f"#{_draft_semantic_kind_select_id()}")
                self.assertFalse(bool(getattr(semantic_select, "disabled", True)))
                self.assertTrue(getattr(semantic_select, "display", True))
                self.assertEqual(str(getattr(semantic_select, "prompt", "")), "Semantic Kind")

                render_select = app.query_one(f"#{_draft_render_kind_select_id()}")
                evidence_select = app.query_one(f"#{_draft_evidence_mode_select_id()}")
                transform_select = app.query_one(f"#{_draft_transform_mode_select_id()}")
                self.assertFalse(bool(getattr(render_select, "disabled", True)))
                self.assertFalse(bool(getattr(evidence_select, "disabled", True)))
                self.assertFalse(bool(getattr(transform_select, "disabled", True)))
                self.assertEqual(str(getattr(render_select, "prompt", "")), "Render Style")
                self.assertEqual(str(getattr(evidence_select, "prompt", "")), "Evidence Mode")
                self.assertEqual(str(getattr(transform_select, "prompt", "")), "Transform Mode")

        asyncio.run(_exercise())

    def test_textual_review_publication_selects_are_present_for_current_report_plan(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="review-select-demo",
            title="Review Select Notes",
            source_ref="notes/review-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Review Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="review-select-demo",
            source_kind="markdown",
            rationale="Admit review select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="review-select-demo",
                canonical_title="Review Select Demo",
                aliases=("Review Select Demo",),
                subject_family="Governance",
                summary="Review select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="review-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="review-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="review-select-demo",
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id="review-select-demo",
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "review-select-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                output_select = app.query_one(f"#{_review_publication_output_mode_select_id()}")
                section_select = app.query_one(f"#{_review_publication_section_plan_select_id()}")
                baseline_select = app.query_one(f"#{_review_publication_diff_baseline_select_id()}")
                unit_target_select = app.query_one(f"#{_review_composition_unit_target_select_id()}")
                include_unit_switch = app.query_one(f"#{_review_composition_unit_included_switch_id()}")
                section_target_select = app.query_one(f"#{_review_publication_section_target_select_id()}")
                include_section_switch = app.query_one(f"#{_review_publication_section_included_switch_id()}")

                self.assertFalse(bool(getattr(output_select, "disabled", True)))
                self.assertFalse(bool(getattr(section_select, "disabled", True)))
                self.assertFalse(bool(getattr(baseline_select, "disabled", True)))
                self.assertFalse(bool(getattr(unit_target_select, "disabled", True)))
                self.assertFalse(bool(getattr(include_unit_switch, "disabled", True)))
                self.assertFalse(bool(getattr(section_target_select, "disabled", True)))
                self.assertTrue(bool(getattr(include_section_switch, "disabled", False)))
                self.assertEqual(str(getattr(output_select, "prompt", "")), "Output Style")
                self.assertEqual(str(getattr(section_select, "prompt", "")), "Report Structure")
                self.assertEqual(str(getattr(baseline_select, "prompt", "")), "Diff Baseline")
                self.assertEqual(str(getattr(unit_target_select, "prompt", "")), "Item")
                self.assertEqual(str(getattr(section_target_select, "prompt", "")), "Section")

        asyncio.run(_exercise())

    def test_textual_review_tab_places_selected_section_beside_selected_item(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        self._seed_report_scope_subject("review-layout-demo")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                plan_group = app.query_one("#review_plan_group")
                item_group = app.query_one("#review_item_group")
                section_group = app.query_one("#review_section_group")
                scope_workbench = app.query_one("#review_scope_workbench")

                self.assertEqual(int(getattr(item_group.region, "y", 0) or 0), int(getattr(section_group.region, "y", 0) or 0))
                self.assertGreater(int(getattr(section_group.region, "x", 0) or 0), int(getattr(item_group.region, "x", 0) or 0))
                self.assertGreater(int(getattr(item_group.region, "y", 0) or 0), int(getattr(plan_group.region, "y", 0) or 0))
                self.assertGreater(int(getattr(scope_workbench.region, "y", 0) or 0), int(getattr(item_group.region, "y", 0) or 0))

        asyncio.run(_exercise())

    def test_textual_review_report_plan_widgets_update_scope_structure_and_output(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "review-report-plan-widget-update-demo"
        scenario, _progress = self._seed_report_scope_subject(
            subject_id,
            unit_titles=(
                "Actors",
                "Boundaries",
                "Capabilities",
                "Constraints",
            ),
        )
        boundaries_unit_id = stable_learning_unit_id(
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title="Boundaries",
        )

        def _latest_composition():
            composition = _latest_publication_composition(
                self.root,
                subject_id=scenario.subject_id,
                subject_title=scenario.title,
                publication_id=scenario.publication_id,
            )
            self.assertIsNotNone(composition)
            return composition

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                unit_target_select = app.query_one(f"#{_review_composition_unit_target_select_id()}")
                unit_target_select.value = boundaries_unit_id
                await pilot.pause()
                await pilot.pause()

                include_unit_switch = app.query_one(f"#{_review_composition_unit_included_switch_id()}")
                self.assertFalse(bool(getattr(include_unit_switch, "disabled", True)))
                self.assertTrue(bool(getattr(include_unit_switch, "value", False)))

                await pilot.click(f"#{_review_composition_unit_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertNotIn(boundaries_unit_id, composition.included_unit_ids)
                self.assertIn(boundaries_unit_id, composition.excluded_unit_ids)

                section_target_select = app.query_one(f"#{_review_publication_section_target_select_id()}")
                section_target_select.value = "report-appendix"
                await pilot.pause()
                await pilot.pause()

                include_section_switch = app.query_one(f"#{_review_publication_section_included_switch_id()}")
                self.assertFalse(bool(getattr(include_section_switch, "disabled", True)))
                self.assertTrue(bool(getattr(include_section_switch, "value", False)))

                await pilot.click(f"#{_review_publication_section_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertNotIn("report-appendix", composition.section_ids)

                section_plan_select = app.query_one(f"#{_review_publication_section_plan_select_id()}")
                section_plan_select.value = "brief"
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertEqual(
                    composition.section_ids,
                    ("report-summary", "report-definitions", "report-analysis"),
                )

                output_select = app.query_one(f"#{_review_publication_output_mode_select_id()}")
                output_select.value = "exact_draft"
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertEqual(composition.publication_type, "exact_draft")
                self.assertEqual(composition.section_ids, ())

                output_select = app.query_one(f"#{_review_publication_output_mode_select_id()}")
                output_select.value = "report"
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertEqual(composition.publication_type, "report")
                self.assertEqual(
                    composition.section_ids,
                    ("report-summary", "report-definitions", "report-analysis"),
                )

                baseline_select = app.query_one(f"#{_review_publication_diff_baseline_select_id()}")
                self.assertFalse(bool(getattr(baseline_select, "disabled", True)))
                baseline_select.value = "snapshot"
                await pilot.pause()
                await pilot.pause()

                stored_progress = load_subject_progress(self.root, scenario.subject_id)
                self.assertEqual(stored_progress.publication_diff_baseline_mode, "snapshot")

                review_result_text = "\n".join(str(line) for line in app.query_one("#review_result").lines)
                self.assertIn("Report Plan Diff Baseline", review_result_text)
                self.assertIn("Current Subject Snapshot", review_result_text)

        asyncio.run(_exercise())

    def test_textual_review_include_unit_switch_disables_for_last_included_unit(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "review-single-unit-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Review Single Unit Notes",
            source_ref="notes/review-single-unit.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Review Single Unit Notes\n\n## Alpha\nAlpha matters.\n",
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit review single-unit demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Review Single Unit Demo",
                aliases=("Review Single Unit Demo",),
                subject_family="Governance",
                summary="Review single-unit demo subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                include_unit_switch = app.query_one(f"#{_review_composition_unit_included_switch_id()}")
                self.assertTrue(bool(getattr(include_unit_switch, "disabled", False)))

        asyncio.run(_exercise())

    def test_textual_review_include_section_switch_enables_after_section_target_selected(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="review-section-select-demo",
            title="Review Section Select Notes",
            source_ref="notes/review-section-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Review Section Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="review-section-select-demo",
            source_kind="markdown",
            rationale="Admit review section select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="review-section-select-demo",
                canonical_title="Review Section Select Demo",
                aliases=("Review Section Select Demo",),
                subject_family="Governance",
                summary="Review section select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="review-section-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="review-section-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="review-section-select-demo",
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id="review-section-select-demo",
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "review-section-select-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                include_section_switch = app.query_one(f"#{_review_publication_section_included_switch_id()}")
                self.assertTrue(bool(getattr(include_section_switch, "disabled", False)))

                app._apply_mock_subject_action("review", "set_selected_publication_section:report-summary")
                await pilot.pause()

                include_section_switch = app.query_one(f"#{_review_publication_section_included_switch_id()}")
                self.assertFalse(bool(getattr(include_section_switch, "disabled", True)))

        asyncio.run(_exercise())

    def test_textual_review_result_panel_shows_comparison_and_latest_receipt_tables_from_visible_journal_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "review-result-table-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Review Result Table Notes",
            source_ref="notes/review-result-table.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Review Result Table Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit review result table demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Review Result Table Demo",
                aliases=("Review Result Table Demo",),
                subject_family="Governance",
                summary="Review result table demo subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                await pilot.click("#subject_review_journal_button")
                await pilot.pause()

                review_result_text = "\n".join(str(line) for line in app.query_one("#review_result").lines)
                self.assertIn("Review Journal: review-result-table-demo", review_result_text)
                self.assertIn("Maintained File Preview", review_result_text)

                comparison_table = app.query_one(f"#{_review_comparison_history_table_id()}")
                latest_receipt_table = app.query_one(f"#{_review_latest_receipt_table_id()}")
                self.assertTrue(bool(getattr(comparison_table, "display", False)))
                self.assertTrue(bool(getattr(latest_receipt_table, "display", False)))
                self.assertGreaterEqual(int(getattr(comparison_table, "row_count", 0) or 0), 1)
                self.assertGreaterEqual(int(getattr(latest_receipt_table, "row_count", 0) or 0), 1)

                comparison_rows = tuple(
                    tuple(str(cell) for cell in comparison_table.get_row_at(index))
                    for index in range(int(getattr(comparison_table, "row_count", 0) or 0))
                )
                latest_rows = tuple(
                    tuple(str(cell) for cell in latest_receipt_table.get_row_at(index))
                    for index in range(int(getattr(latest_receipt_table, "row_count", 0) or 0))
                )
                self.assertTrue(any(row[0] == "verdict" and row[1] == "aligned" for row in comparison_rows))
                self.assertTrue(any(row[0] == "status" for row in latest_rows))

        asyncio.run(_exercise())

    def test_textual_review_section_target_selection_scrolls_tree_to_visible_section(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "review-section-scroll-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Review Section Scroll Notes",
            source_ref="notes/review-section-scroll.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Review Section Scroll Notes\n\n"
                "## Actors\nActors matter.\n\n"
                "## Boundaries\nBoundaries matter.\n\n"
                "## Capabilities\nCapabilities matter.\n\n"
                "## Constraints\nConstraints matter.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit enough units to push report sections below the fold.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Review Section Scroll Demo",
                aliases=("Review Section Scroll Demo",),
                subject_family="Physics / Review",
                summary="A subject for validating review-scope section scrolling.",
                units=tuple(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title=title),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title=title,
                        statement=f"{title}.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    )
                    for title in (
                        "Actors",
                        "Boundaries",
                        "Capabilities",
                        "Constraints",
                        "Dependencies",
                        "Objectives",
                        "States",
                        "Transitions",
                        "Vendors",
                        "Balances",
                        "Top Ups",
                        "Cashiers",
                        "Parents",
                        "Students",
                        "Receipts",
                    )
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 22)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                section_target_select = app.query_one(f"#{_review_publication_section_target_select_id()}")
                section_target_select.value = "report-analysis"
                await pilot.pause()
                await pilot.pause()

                tree_panel = app.query_one("#review_scope_tree_panel")
                detail_panel = app.query_one("#review_scope_detail_panel")
                tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in tree_panel.root.children
                    for node in (heading, *heading.children)
                )
                detail_text = _table_text(detail_panel)

                self.assertIn("> [x] Analysis", tree_text)
                self.assertIn("Analysis", detail_text)
                self.assertIn("Analysis", str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""))
                self.assertGreater(int(getattr(getattr(tree_panel, "scroll_offset", None), "y", 0) or 0), 0)

        asyncio.run(_exercise())

    def test_textual_publication_selects_are_present_for_current_report_plan(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="publication-select-demo",
            title="Publication Select Notes",
            source_ref="notes/publication-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="publication-select-demo",
            source_kind="markdown",
            rationale="Admit publication select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="publication-select-demo",
                canonical_title="Publication Select Demo",
                aliases=("Publication Select Demo",),
                subject_family="Governance",
                summary="Publication select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="publication-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="publication-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="publication-select-demo",
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id="publication-select-demo",
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "publication-select-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                output_select = app.query_one(f"#{_publication_output_mode_select_id()}")
                section_select = app.query_one(f"#{_publication_section_plan_select_id()}")
                baseline_select = app.query_one(f"#{_publication_diff_baseline_select_id()}")
                unit_target_select = app.query_one(f"#{_publication_composition_unit_target_select_id()}")
                include_unit_switch = app.query_one(f"#{_publication_composition_unit_included_switch_id()}")
                section_target_select = app.query_one(f"#{_publication_section_target_select_id()}")
                include_section_switch = app.query_one(f"#{_publication_section_included_switch_id()}")

                self.assertFalse(bool(getattr(output_select, "disabled", True)))
                self.assertFalse(bool(getattr(section_select, "disabled", True)))
                self.assertFalse(bool(getattr(baseline_select, "disabled", True)))
                self.assertFalse(bool(getattr(unit_target_select, "disabled", True)))
                self.assertFalse(bool(getattr(include_unit_switch, "disabled", True)))
                self.assertFalse(bool(getattr(section_target_select, "disabled", True)))
                self.assertTrue(bool(getattr(include_section_switch, "disabled", False)))
                self.assertEqual(str(getattr(output_select, "prompt", "")), "Output Style")
                self.assertEqual(str(getattr(section_select, "prompt", "")), "Report Structure")
                self.assertEqual(str(getattr(baseline_select, "prompt", "")), "Diff Baseline")
                self.assertEqual(str(getattr(unit_target_select, "prompt", "")), "Item")
                self.assertEqual(str(getattr(section_target_select, "prompt", "")), "Section")

        asyncio.run(_exercise())

    def test_textual_publication_scope_tree_supports_keyboard_selection_and_preview(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="publication-tree-demo",
            title="Publication Tree Notes",
            source_ref="notes/publication-tree.md",
        )
        persist_learning_source(self.root, source, source_text="# Publication Tree Notes\n")
        delta = new_learning_delta(
            subject_id="publication-tree-demo",
            source_kind="markdown",
            rationale="Admit publication-tree-demo units.",
        )
        persist_learning_delta(self.root, delta)
        velocity_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="publication-tree-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="publication-tree-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        acceleration_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="publication-tree-demo",
                unit_kind="relation",
                canonical_title="Acceleration",
            ),
            subject_id="publication-tree-demo",
            unit_kind="relation",
            canonical_title="Acceleration",
            statement="Acceleration is the rate of change of velocity.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="publication-tree-demo",
                canonical_title="Publication Tree Demo",
                aliases=("Publication Tree Demo",),
                subject_family="Physics",
                summary="A multi-unit subject for publication scope editing.",
                units=(velocity_unit, acceleration_unit),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "publication-tree-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, "publication-tree-demo", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                tree_panel = app.query_one("#publication_scope_tree_panel")
                detail_panel = app.query_one("#publication_scope_detail_panel")
                self.assertIsInstance(tree_panel, _FocusableTextualTree)
                self.assertFalse(bool(getattr(detail_panel, "show_header", True)))
                self.assertEqual(str(getattr(detail_panel, "cursor_type", "")), "none")
                await pilot.click("#publication_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "publication_scope_tree_panel")

                def _tree_text() -> str:
                    return "\n".join(
                        str(getattr(node, "label", "") or "")
                        for heading in tree_panel.root.children
                        for node in (heading, *heading.children)
                    )

                initial_tree_text = _tree_text()
                initial_detail_text = _table_text(detail_panel)
                self.assertIn("> [x] Velocity", initial_tree_text)
                self.assertIn("[x] Acceleration", initial_tree_text)
                self.assertIn("Velocity", initial_detail_text)

                await pilot.press("down")
                await pilot.pause()
                moved_tree_text = _tree_text()
                moved_detail_text = _table_text(detail_panel)
                self.assertIn("> [x] Acceleration", moved_tree_text)
                self.assertNotIn("> [x] Velocity", moved_tree_text)
                self.assertIn("Acceleration", str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""))
                self.assertIn("Acceleration", moved_detail_text)

                await pilot.press("x")
                await pilot.pause()
                toggled_tree_text = _tree_text()
                publication_result_text = "\n".join(str(line) for line in app.query_one("#publication_result").lines)
                self.assertIn("  [-] Velocity", toggled_tree_text)
                self.assertIn("> [ ] Acceleration", toggled_tree_text)
                self.assertIn("latest unit action: excluded Acceleration", publication_result_text)

                await pilot.press("enter")
                await pilot.pause()
                publication_result_text = "\n".join(str(line) for line in app.query_one("#publication_result").lines)
                self.assertIn("Report Scope Preview", publication_result_text)
                self.assertIn("Acceleration", publication_result_text)

        asyncio.run(_exercise())

    def test_textual_publication_section_target_selection_scrolls_tree_to_visible_section(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "publication-section-scroll-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Publication Section Scroll Notes",
            source_ref="notes/publication-section-scroll.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Section Scroll Notes\n\n"
                "## Actors\nActors matter.\n\n"
                "## Boundaries\nBoundaries matter.\n\n"
                "## Capabilities\nCapabilities matter.\n\n"
                "## Constraints\nConstraints matter.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit enough units to push publication sections below the fold.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Publication Section Scroll Demo",
                aliases=("Publication Section Scroll Demo",),
                subject_family="Physics / Publication",
                summary="A subject for validating publication-scope section scrolling.",
                units=tuple(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title=title),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title=title,
                        statement=f"{title}.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    )
                    for title in (
                        "Actors",
                        "Boundaries",
                        "Capabilities",
                        "Constraints",
                        "Dependencies",
                        "Objectives",
                        "States",
                        "Transitions",
                        "Vendors",
                        "Balances",
                        "Top Ups",
                        "Cashiers",
                        "Parents",
                        "Students",
                        "Receipts",
                    )
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 22)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                section_target_select = app.query_one(f"#{_publication_section_target_select_id()}")
                section_target_select.value = "report-analysis"
                await pilot.pause()
                await pilot.pause()

                tree_panel = app.query_one("#publication_scope_tree_panel")
                detail_panel = app.query_one("#publication_scope_detail_panel")
                tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in tree_panel.root.children
                    for node in (heading, *heading.children)
                )
                detail_text = _table_text(detail_panel)

                self.assertIn("> [x] Analysis", tree_text)
                self.assertIn("Analysis", detail_text)
                self.assertIn("Analysis", str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""))
                self.assertGreater(int(getattr(getattr(tree_panel, "scroll_offset", None), "y", 0) or 0), 0)

        asyncio.run(_exercise())

    def test_textual_review_section_target_selection_scrolls_tree_to_visible_section(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        self._seed_report_scope_subject("review-section-scroll-demo")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 22)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                section_target_select = app.query_one(f"#{_review_publication_section_target_select_id()}")
                section_target_select.value = "report-appendix"
                await pilot.pause()
                await pilot.pause()

                tree_panel = app.query_one("#review_scope_tree_panel")
                detail_panel = app.query_one("#review_scope_detail_panel")
                tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in tree_panel.root.children
                    for node in (heading, *heading.children)
                )
                detail_text = _table_text(detail_panel)

                self.assertIn("> [x] Appendix", tree_text)
                self.assertIn("Appendix", detail_text)
                self.assertIn("Appendix", str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""))
                self.assertGreater(int(getattr(getattr(tree_panel, "scroll_offset", None), "y", 0) or 0), 0)

        asyncio.run(_exercise())

    def test_textual_review_and_publication_scope_maximize_keeps_nested_workbench_visible(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        self._seed_report_scope_subject("scope-maximize-visible-demo")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                await pilot.click("#review_scope_tree_panel")
                await pilot.pause()

                app.action_toggle_maximized_pane()
                await pilot.pause()
                await pilot.pause()

                self.assertEqual(app._maximized_pane_id, "review_scope_tree_panel")
                self.assertTrue(app.query_one("#review_actions_panel").display)
                self.assertTrue(app.query_one("#review_scope_workbench").display)
                self.assertTrue(app.query_one("#review_scope_tree_wrapper").display)
                self.assertFalse(app.query_one("#review_scope_detail_wrapper").display)
                self.assertGreater(int(getattr(app.query_one("#review_actions_panel").region, "height", 0) or 0), 0)
                self.assertGreater(int(getattr(app.query_one("#review_scope_workbench").region, "height", 0) or 0), 0)
                self.assertGreater(int(getattr(app.query_one("#review_scope_tree_panel").region, "height", 0) or 0), 0)
                self.assertTrue(tuple(app.query_one("#review_scope_tree_panel").root.children))

                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()
                await pilot.click(f"#{_textual_pane_toggle_button_id('publication_scope_tree_panel')}")
                await pilot.pause()
                await pilot.pause()

                self.assertEqual(app._maximized_pane_id, "publication_scope_tree_panel")
                self.assertTrue(app.query_one("#publication_actions_panel").display)
                self.assertTrue(app.query_one("#publication_scope_workbench").display)
                self.assertTrue(app.query_one("#publication_scope_tree_wrapper").display)
                self.assertFalse(app.query_one("#publication_scope_detail_wrapper").display)
                self.assertGreater(int(getattr(app.query_one("#publication_actions_panel").region, "height", 0) or 0), 0)
                self.assertGreater(int(getattr(app.query_one("#publication_scope_workbench").region, "height", 0) or 0), 0)
                self.assertGreater(int(getattr(app.query_one("#publication_scope_tree_panel").region, "height", 0) or 0), 0)
                self.assertTrue(tuple(app.query_one("#publication_scope_tree_panel").root.children))

        asyncio.run(_exercise())

    def test_textual_publication_tab_compacts_plan_and_support_controls_into_shared_top_row(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        self._seed_report_scope_subject("publication-layout-demo")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                plan_support_row = app.query_one("#publication_plan_support_row")
                plan_group = app.query_one("#publication_plan_group")
                support_group = app.query_one("#publication_support_group")
                item_group = app.query_one("#publication_item_group")
                section_group = app.query_one("#publication_section_group")
                scope_workbench = app.query_one("#publication_scope_workbench")

                self.assertTrue(bool(getattr(plan_support_row, "display", False)))
                self.assertEqual(int(getattr(plan_group.region, "y", 0) or 0), int(getattr(support_group.region, "y", 0) or 0))
                self.assertGreater(int(getattr(support_group.region, "x", 0) or 0), int(getattr(plan_group.region, "x", 0) or 0))
                self.assertEqual(int(getattr(item_group.region, "y", 0) or 0), int(getattr(section_group.region, "y", 0) or 0))
                self.assertGreater(int(getattr(item_group.region, "y", 0) or 0), int(getattr(plan_group.region, "y", 0) or 0))
                self.assertGreater(int(getattr(scope_workbench.region, "y", 0) or 0), int(getattr(item_group.region, "y", 0) or 0))

        asyncio.run(_exercise())

    def test_textual_publication_result_panel_shows_build_artifact_and_receipt_tables_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "publication-result-table-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Publication Result Table Notes",
            source_ref="notes/publication-result-table.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text="# Publication Result Table Notes\n\n## Alpha\nAlpha matters.\n",
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit publication result table demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Publication Result Table Demo",
                aliases=("Publication Result Table Demo",),
                subject_family="Governance",
                summary="Publication result table demo subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="approve_review")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="lock_publication")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="build_report")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                publication_result_text = "\n".join(str(line) for line in app.query_one("#publication_result").lines)
                self.assertIn("Publication Journal: report / publication-result-table-demo", publication_result_text)
                self.assertIn("Output Preview", publication_result_text)

                artifacts_table = app.query_one(f"#{_publication_build_artifacts_table_id()}")
                build_receipt_table = app.query_one(f"#{_publication_build_receipt_table_id()}")
                latest_receipt_table = app.query_one(f"#{_publication_latest_receipt_table_id()}")
                self.assertTrue(bool(getattr(artifacts_table, "display", False)))
                self.assertTrue(bool(getattr(build_receipt_table, "display", False)))
                self.assertFalse(bool(getattr(latest_receipt_table, "display", True)))
                self.assertGreaterEqual(int(getattr(artifacts_table, "row_count", 0) or 0), 4)
                self.assertGreaterEqual(int(getattr(build_receipt_table, "row_count", 0) or 0), 1)

                artifact_rows = tuple(
                    tuple(str(cell) for cell in artifacts_table.get_row_at(index))
                    for index in range(int(getattr(artifacts_table, "row_count", 0) or 0))
                )
                receipt_rows = tuple(
                    tuple(str(cell) for cell in build_receipt_table.get_row_at(index))
                    for index in range(int(getattr(build_receipt_table, "row_count", 0) or 0))
                )
                self.assertTrue(any(row[0] == "report.pdf" and "report.pdf" in row[1] for row in artifact_rows))
                self.assertTrue(any(row[0] == "validation" for row in artifact_rows))
                self.assertTrue(any(row[0] == "validation" for row in receipt_rows))

        asyncio.run(_exercise())

    def test_textual_publication_preview_diff_opens_result_pane_and_hides_legacy_baseline_action(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "publication-diff-preview-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Publication Diff Preview Notes",
            source_ref="notes/publication-diff-preview.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Diff Preview Notes\n\n"
                "## Actors\nActors matter.\n\n"
                "## Boundaries\nBoundaries matter.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit publication diff preview demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Publication Diff Preview Demo",
                aliases=("Publication Diff Preview Demo",),
                subject_family="Governance",
                summary="Publication diff preview demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Actors",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Actors",
                        statement="Actors matter.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id=subject_id,
                            unit_kind="definition",
                            canonical_title="Boundaries",
                        ),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Boundaries",
                        statement="Boundaries matter.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                action_buttons = [
                    app.query_one(f"#{button_id}")
                    for button_id in _subject_action_button_ids("publication")
                ]
                action_labels = [str(getattr(button, "label", "") or "") for button in action_buttons]
                self.assertIn("Preview Report Plan Diff", action_labels)
                self.assertFalse(any("Change Diff Baseline" in label for label in action_labels))

                preview_button = next(
                    button
                    for button in action_buttons
                    if str(getattr(button, "label", "") or "") == "Preview Report Plan Diff"
                )
                preview_button.press()
                await pilot.pause()

                self.assertEqual(app._maximized_pane_id, "publication_result")
                self.assertTrue(app.query_one("#publication_result_panel").display)
                publication_result_text = "\n".join(str(line) for line in app.query_one("#publication_result").lines)
                self.assertIn("Publication Journal: report / publication-diff-preview-demo", publication_result_text)
                self.assertIn("Report Plan Diff", publication_result_text)
                self.assertIn("baseline mode:", publication_result_text)
                self.assertIn("removed units:", publication_result_text)

                latest_receipt_table = app.query_one(f"#{_publication_latest_receipt_table_id()}")
                self.assertTrue(bool(getattr(latest_receipt_table, "display", False)))
                latest_rows = tuple(
                    tuple(str(cell) for cell in latest_receipt_table.get_row_at(index))
                    for index in range(int(getattr(latest_receipt_table, "row_count", 0) or 0))
                )
                self.assertTrue(any(row[0] == "baseline mode" for row in latest_rows))

        asyncio.run(_exercise())

    def test_textual_publication_select_action_keeps_active_publication_tab(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="publication-select-stay-demo",
            title="Publication Select Stay Notes",
            source_ref="notes/publication-select-stay.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Select Stay Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="publication-select-stay-demo",
            source_kind="markdown",
            rationale="Admit publication select stay demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="publication-select-stay-demo",
                canonical_title="Publication Select Stay Demo",
                aliases=("Publication Select Stay Demo",),
                subject_family="Governance",
                summary="Publication select stay demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="publication-select-stay-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="publication-select-stay-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "publication-select-stay-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "publication_tab")
                app._apply_mock_subject_action("publication", "set_publication_output_mode:exact_draft")
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "publication_tab")

        asyncio.run(_exercise())

    def test_textual_publication_import_controls_are_present_for_current_report_plan(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="publication-import-select-demo",
            title="Publication Import Select Notes",
            source_ref="notes/publication-import-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Import Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="publication-import-select-demo",
            source_kind="markdown",
            rationale="Admit publication import select demo.",
        )
        persist_learning_delta(self.root, delta)
        active_context = LearningContext(
            subject_id="publication-import-select-demo",
            canonical_title="Publication Import Select Demo",
            aliases=("Publication Import Select Demo",),
            subject_family="Governance",
            summary="Publication import select demo subject.",
            units=(
                LearningUnit(
                    unit_id=stable_learning_unit_id(
                        subject_id="publication-import-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                    ),
                    subject_id="publication-import-select-demo",
                    unit_kind="definition",
                    canonical_title="Alpha",
                    statement="Alpha matters.",
                    provenance_refs=(source.source_id,),
                    status="admitted",
                ),
            ),
            linked_source_ids=(source.source_id,),
            applied_delta_ids=(delta.delta_id,),
            governance_status="active",
        )
        persist_learning_context(self.root, active_context)
        import_context = LearningContext(
            subject_id="publication-import-support",
            canonical_title="Publication Import Support",
            aliases=("Publication Import Support",),
            subject_family="Governance",
            summary="Supporting imported subject.",
            governance_status="active",
        )
        persist_learning_context(self.root, import_context)
        persist_subject_import(
            self.root,
            new_subject_import(
                active_subject_id=active_context.subject_id,
                active_subject_version_id=active_context.content_hash(),
                active_subject_title=active_context.canonical_title,
                source_subject_id=import_context.subject_id,
                source_subject_version_id=import_context.content_hash(),
                source_subject_title=import_context.canonical_title,
                import_kind="definition_support",
                imported_unit_ids=("unit_import_alpha",),
                rationale="Borrow supporting import for publication controls.",
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == active_context.subject_id)
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                target_select = app.query_one(f"#{_publication_import_target_select_id()}")
                included_switch = app.query_one(f"#{_publication_import_included_switch_id()}")
                usage_select = app.query_one(f"#{_publication_import_usage_select_id()}")

                self.assertFalse(bool(getattr(target_select, "disabled", True)))
                self.assertFalse(bool(getattr(included_switch, "disabled", True)))
                self.assertFalse(bool(getattr(usage_select, "disabled", True)))
                self.assertEqual(str(getattr(target_select, "prompt", "")), "Support")
                self.assertEqual(str(getattr(usage_select, "prompt", "")), "Use")

        asyncio.run(_exercise())

    def test_textual_publication_import_widgets_update_selected_import_scope_and_usage(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        scenario, _progress, subject_imports = self._seed_publication_import_control_subject(
            "publication-import-widget-update-demo"
        )
        first_import, second_import = subject_imports

        def _latest_composition():
            composition = _latest_publication_composition(
                self.root,
                subject_id=scenario.subject_id,
                subject_title=scenario.title,
                publication_id=scenario.publication_id,
            )
            self.assertIsNotNone(composition)
            return composition

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                focus_ids = [str(getattr(widget, "id", "") or "") for widget in app._focus_order_for_active_tab()]
                self.assertLess(
                    focus_ids.index(_publication_import_target_select_id()),
                    focus_ids.index(_publication_import_included_switch_id()),
                )
                self.assertLess(
                    focus_ids.index(_publication_import_included_switch_id()),
                    focus_ids.index(_publication_import_usage_select_id()),
                )
                self.assertLess(
                    focus_ids.index(_publication_import_usage_select_id()),
                    focus_ids.index(_publication_composition_unit_target_select_id()),
                )

                target_select = app.query_one(f"#{_publication_import_target_select_id()}")
                included_switch = app.query_one(f"#{_publication_import_included_switch_id()}")
                usage_select = app.query_one(f"#{_publication_import_usage_select_id()}")

                self.assertFalse(bool(getattr(target_select, "disabled", True)))
                self.assertFalse(bool(getattr(included_switch, "disabled", True)))
                self.assertFalse(bool(getattr(usage_select, "disabled", True)))
                self.assertEqual(str(getattr(target_select, "value", "")), first_import.import_id)

                target_select.value = second_import.import_id
                await pilot.pause()
                await pilot.pause()

                target_select = app.query_one(f"#{_publication_import_target_select_id()}")
                included_switch = app.query_one(f"#{_publication_import_included_switch_id()}")
                usage_select = app.query_one(f"#{_publication_import_usage_select_id()}")
                self.assertEqual(str(getattr(target_select, "value", "")), second_import.import_id)
                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertFalse(bool(getattr(usage_select, "disabled", True)))

                await pilot.click(f"#{_publication_import_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertIn(first_import.import_id, composition.selected_subject_import_ids)
                self.assertNotIn(second_import.import_id, composition.selected_subject_import_ids)

                included_switch = app.query_one(f"#{_publication_import_included_switch_id()}")
                usage_select = app.query_one(f"#{_publication_import_usage_select_id()}")
                self.assertFalse(bool(getattr(included_switch, "value", True)))
                self.assertTrue(bool(getattr(usage_select, "disabled", False)))

                await pilot.click(f"#{_publication_import_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertIn(second_import.import_id, composition.selected_subject_import_ids)
                usage_select = app.query_one(f"#{_publication_import_usage_select_id()}")
                self.assertFalse(bool(getattr(usage_select, "disabled", True)))

                usage_select.value = "comparison"
                await pilot.pause()
                await pilot.pause()

                composition = _latest_composition()
                self.assertEqual(composition.import_usage_by_id.get(second_import.import_id), "comparison")
                self.assertEqual(composition.import_usage_by_id.get(first_import.import_id), "dependency_only")

                publication_result_text = "\n".join(str(line) for line in app.query_one("#publication_result").lines)
                self.assertIn("Support Use Updated", publication_result_text)
                self.assertIn(second_import.source_subject_title, publication_result_text)
                self.assertIn("comparison", publication_result_text)

        asyncio.run(_exercise())

    def test_textual_publication_include_section_switch_enables_after_section_target_selected(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="publication-section-select-demo",
            title="Publication Section Select Notes",
            source_ref="notes/publication-section-select.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Publication Section Select Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="publication-section-select-demo",
            source_kind="markdown",
            rationale="Admit publication section select demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="publication-section-select-demo",
                canonical_title="Publication Section Select Demo",
                aliases=("Publication Section Select Demo",),
                subject_family="Governance",
                summary="Publication section select demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="publication-section-select-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="publication-section-select-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="publication-section-select-demo",
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id="publication-section-select-demo",
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "publication-section-select-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()

                include_section_switch = app.query_one(f"#{_publication_section_included_switch_id()}")
                self.assertTrue(bool(getattr(include_section_switch, "disabled", False)))

                app._apply_mock_subject_action("publication", "set_selected_publication_section:report-summary")
                await pilot.pause()

                include_section_switch = app.query_one(f"#{_publication_section_included_switch_id()}")
                self.assertFalse(bool(getattr(include_section_switch, "disabled", True)))

        asyncio.run(_exercise())

    def test_textual_research_choice_controls_are_present_for_selected_staged_source_context(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="research-control-demo",
                canonical_title="Research Control Demo",
                aliases=("Research Control Demo",),
                subject_family="Research",
                summary="Research control demo subject.",
                units=(),
                linked_source_ids=(),
                governance_status="active",
            ),
        )
        staged_source = new_staged_source(
            subject_id="research-control-demo",
            title="Control Source",
            source_ref="https://example.test/control-source",
            source_kind="url",
            metadata={"requested_url": "https://example.test/control-source"},
        )
        capture_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id="research-control-demo",
                source_ref=staged_source.source_ref,
                revision_kind="capture",
            ),
            created_at_epoch_ms=1000,
        )
        manual_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id="research-control-demo",
                source_ref=staged_source.source_ref,
                revision_kind="manual_curation",
            ),
            created_at_epoch_ms=2000,
        )
        merge_revision = replace(
            new_source_revision(
                staged_source_id=staged_source.staged_source_id,
                subject_id="research-control-demo",
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
            subject_id="research-control-demo",
            title="Focused Sources",
            description="Operator-managed focused set.",
            staged_source_ids=(staged_source.staged_source_id,),
            query_text="control source",
        )
        persist_source_collection(self.root, focused_collection)

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "research-control-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        progress.research_selected_source_collection_id = focused_collection.collection_id
        progress.research_selected_staged_source_id = staged_source.staged_source_id
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                collection_select = app.query_one(f"#{_research_source_collection_select_id()}")
                baseline_select = app.query_one(f"#{_research_source_revision_baseline_select_id()}")
                membership_switch = app.query_one(f"#{_research_source_collection_membership_switch_id()}")

                self.assertFalse(bool(getattr(collection_select, "disabled", True)))
                self.assertFalse(bool(getattr(baseline_select, "disabled", True)))
                self.assertFalse(bool(getattr(membership_switch, "disabled", True)))
                self.assertEqual(str(getattr(collection_select, "prompt", "")), "Source Set")
                self.assertEqual(str(getattr(baseline_select, "prompt", "")), "Revision Baseline")
                self.assertTrue(getattr(membership_switch, "value", False))
                self.assertEqual(str(getattr(collection_select, "value", "")), focused_collection.collection_id)
                self.assertFalse(app.query_one("#subject_target_panel_shell").display)
                hidden_pane_button = app.query_one("#subject_research_hidden_pane_button")
                hidden_pane_button.press()
                await pilot.pause()
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                target_panel_text_normalized = " ".join(target_panel_text.split())
                self.assertIn("Source-set workbench", target_panel_text_normalized)
                self.assertIn("Find Sources Ready: yes", target_panel_text_normalized)
                self.assertIn("Sync Source Set Ready: yes", target_panel_text_normalized)
                self.assertIn("Apply Set Export Ready: yes", target_panel_text_normalized)
                self.assertIn("Refreshable Urls: 1", target_panel_text_normalized)

        asyncio.run(_exercise())

    def test_textual_draft_model_selects_are_present_when_model_mode_is_active(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        subject_id = "draft-model-widget-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Draft Model Widget Notes",
            source_ref="notes/draft-model-widget.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft Model Widget Notes\n\n"
                "## Operations Team\n\n"
                "Operations owns the rollout.\n\n"
                "## Enable Alerts\n\n"
                "Enable alerts across the boundary.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the draft model widget subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title="Operations Team",
            ),
            subject_id=subject_id,
            unit_kind="definition",
            canonical_title="Operations Team",
            statement="Operations owns the rollout.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Draft Model Widget Demo",
                aliases=("Draft Model Widget Demo",),
                subject_family="Operations",
                summary="Maintained subject for Draft Model widget controls.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                open_model_button = app.query_one("#subject_draft_review_gate_action_2_button")
                open_model_label = str(getattr(open_model_button, "label", ""))
                if open_model_label == "Open Model":
                    open_model_button.press()
                    await pilot.pause()
                else:
                    self.assertEqual(open_model_label, "Back To Compose")

                self.assertFalse(bool(getattr(app.query_one("#draft_choice_group"), "display", True)))
                self.assertTrue(bool(getattr(app.query_one("#draft_model_construct_group"), "display", False)))

                sort_select = app.query_one(f"#{_draft_model_construct_sort_select_id()}")
                lane_select = app.query_one(f"#{_draft_model_construct_lane_select_id()}")
                policy_select = app.query_one(f"#{_draft_model_policy_profile_select_id()}")

                self.assertFalse(bool(getattr(sort_select, "disabled", True)))
                self.assertFalse(bool(getattr(lane_select, "disabled", True)))
                self.assertFalse(bool(getattr(policy_select, "disabled", True)))
                self.assertEqual(str(getattr(sort_select, "prompt", "")), "Change Type")
                self.assertEqual(str(getattr(lane_select, "prompt", "")), "Change Role")
                self.assertEqual(str(getattr(policy_select, "prompt", "")), "Decision Policy")

        asyncio.run(_exercise())

    def test_textual_draft_model_capability_relation_selection_lists_bind_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id, relation_ids = self._prepare_draft_model_relation_demo(selected_construct_kind="capability")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                open_model_button = app.query_one("#subject_draft_review_gate_action_2_button")
                open_model_label = str(getattr(open_model_button, "label", ""))
                if open_model_label == "Open Model":
                    open_model_button.press()
                    await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")
                scenario = app._mock_subject_scenario()
                progress = app._mock_subject_progress()
                candidates = _subject_transformation_construct_candidates(
                    self.root,
                    scenario=scenario,
                    include_rejected=False,
                )
                target_index = next(
                    index
                    for index, candidate in enumerate(candidates)
                    if collapse_ws(candidate.status) == "accepted"
                    and collapse_ws(candidate.sort_kind) == "capability"
                    and collapse_ws(candidate.canonical_label) == "Decision Support Capability"
                )
                current_index = int(getattr(progress, "draft_model_cursor", 0) or 0)
                key = "down" if target_index >= current_index else "up"
                for _ in range(abs(target_index - current_index)):
                    await pilot.press(key)
                await pilot.pause()
                selected_progress = app._mock_subject_progress()
                selected_candidate = candidates[target_index]
                self.assertEqual(
                    collapse_ws(selected_progress.draft_selected_construct_candidate_id),
                    collapse_ws(selected_candidate.construct_candidate_id),
                )

                relation_row = app.query_one("#draft_model_relation_row")
                dependency_label = app.query_one(f"#{_draft_model_relation_label_id(0)}")
                boundary_label = app.query_one(f"#{_draft_model_relation_label_id(1)}")
                dependency_list = app.query_one(f"#{_draft_model_relation_selection_list_id(0)}")
                boundary_list = app.query_one(f"#{_draft_model_relation_selection_list_id(1)}")

                self.assertEqual(app._active_tab_id(), "draft_tab")
                self.assertTrue(bool(getattr(relation_row, "display", False)))
                self.assertEqual(str(dependency_label.render()), "Dependencies")
                self.assertEqual(str(boundary_label.render()), "Boundaries")
                self.assertFalse(bool(getattr(dependency_list, "disabled", True)))
                self.assertFalse(bool(getattr(boundary_list, "disabled", True)))

                dependency_list.select(relation_ids["dependency_id"])
                app.on_selection_list_selected_changed(SimpleNamespace(selection_list=dependency_list))
                for _ in range(8):
                    await pilot.pause()
                    detail_rows = {
                        (collapse_ws(row[0]), collapse_ws(row[1]))
                        for row in _table_rows(app.query_one("#draft_scope_detail_panel"))
                        if len(row) >= 2
                    }
                    if ("required dependencies (1)", "Carrier Uptime") in detail_rows:
                        break
                boundary_list = app.query_one(f"#{_draft_model_relation_selection_list_id(1)}")
                boundary_list.select(relation_ids["boundary_id"])
                app.on_selection_list_selected_changed(SimpleNamespace(selection_list=boundary_list))
                detail_rows = set()
                for _ in range(8):
                    await pilot.pause()
                    detail_rows = {
                        (collapse_ws(row[0]), collapse_ws(row[1]))
                        for row in _table_rows(app.query_one("#draft_scope_detail_panel"))
                        if len(row) >= 2
                    }
                    if ("crossed boundaries (1)", "Carrier Boundary") in detail_rows:
                        break
                self.assertIn(("required dependencies (1)", "Carrier Uptime"), detail_rows)
                self.assertIn(("crossed boundaries (1)", "Carrier Boundary"), detail_rows)

        asyncio.run(_exercise())

    def test_textual_draft_model_transition_state_selects_bind_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id, relation_ids = self._prepare_draft_model_relation_demo(selected_construct_kind="transition")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                open_model_button = app.query_one("#subject_draft_review_gate_action_2_button")
                open_model_label = str(getattr(open_model_button, "label", ""))
                if open_model_label == "Open Model":
                    open_model_button.press()
                    await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")
                scenario = app._mock_subject_scenario()
                progress = app._mock_subject_progress()
                candidates = _subject_transformation_construct_candidates(
                    self.root,
                    scenario=scenario,
                    include_rejected=False,
                )
                target_index = next(
                    index
                    for index, candidate in enumerate(candidates)
                    if collapse_ws(candidate.status) == "accepted"
                    and collapse_ws(candidate.sort_kind) == "transition"
                    and collapse_ws(candidate.canonical_label) == "Move To Target"
                )
                current_index = int(getattr(progress, "draft_model_cursor", 0) or 0)
                key = "down" if target_index >= current_index else "up"
                for _ in range(abs(target_index - current_index)):
                    await pilot.press(key)
                await pilot.pause()
                selected_progress = app._mock_subject_progress()
                selected_candidate = candidates[target_index]
                self.assertEqual(
                    collapse_ws(selected_progress.draft_selected_construct_candidate_id),
                    collapse_ws(selected_candidate.construct_candidate_id),
                )

                transition_row = app.query_one("#draft_model_transition_row")
                source_select = app.query_one(f"#{_draft_model_transition_source_select_id()}")
                target_select = app.query_one(f"#{_draft_model_transition_target_select_id()}")

                self.assertEqual(app._active_tab_id(), "draft_tab")
                self.assertTrue(bool(getattr(transition_row, "display", False)))
                self.assertFalse(bool(getattr(source_select, "disabled", True)))
                self.assertTrue(bool(getattr(target_select, "disabled", False)))
                self.assertEqual(str(getattr(source_select, "prompt", "")), "From State")
                self.assertEqual(str(getattr(target_select, "prompt", "")), "To State")

                source_select.value = relation_ids["source_state_id"]
                await pilot.pause()
                await pilot.pause()

                target_select = app.query_one(f"#{_draft_model_transition_target_select_id()}")
                self.assertFalse(bool(getattr(target_select, "disabled", True)))
                target_select.value = relation_ids["target_state_id"]
                await pilot.pause()
                await pilot.pause()

                detail_rows = {
                    (collapse_ws(row[0]), collapse_ws(row[1]))
                    for row in _table_rows(app.query_one("#draft_scope_detail_panel"))
                    if len(row) >= 2
                }
                self.assertIn(("source state", "Current State"), detail_rows)
                self.assertIn(("target state", "Target State"), detail_rows)

        asyncio.run(_exercise())

    def test_textual_draft_model_decision_relation_selection_lists_bind_from_visible_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id, relation_ids = self._prepare_draft_model_relation_demo(selected_construct_kind="decision")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                open_model_button = app.query_one("#subject_draft_review_gate_action_2_button")
                open_model_label = str(getattr(open_model_button, "label", ""))
                if open_model_label == "Open Model":
                    open_model_button.press()
                    await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")
                scenario = app._mock_subject_scenario()
                progress = app._mock_subject_progress()
                candidates = _subject_transformation_construct_candidates(
                    self.root,
                    scenario=scenario,
                    include_rejected=False,
                )
                target_index = next(
                    index
                    for index, candidate in enumerate(candidates)
                    if collapse_ws(candidate.status) == "accepted"
                    and collapse_ws(candidate.sort_kind) == "decision"
                    and collapse_ws(candidate.canonical_label) == "Choose The Transition"
                )
                current_index = int(getattr(progress, "draft_model_cursor", 0) or 0)
                key = "down" if target_index >= current_index else "up"
                for _ in range(abs(target_index - current_index)):
                    await pilot.press(key)
                await pilot.pause()
                selected_progress = app._mock_subject_progress()
                selected_candidate = candidates[target_index]
                self.assertEqual(
                    collapse_ws(selected_progress.draft_selected_construct_candidate_id),
                    collapse_ws(selected_candidate.construct_candidate_id),
                )

                relation_row = app.query_one("#draft_model_relation_row")
                transition_label = app.query_one(f"#{_draft_model_relation_label_id(0)}")
                actor_label = app.query_one(f"#{_draft_model_relation_label_id(1)}")
                transition_list = app.query_one(f"#{_draft_model_relation_selection_list_id(0)}")
                actor_list = app.query_one(f"#{_draft_model_relation_selection_list_id(1)}")

                self.assertTrue(bool(getattr(relation_row, "display", False)))
                self.assertEqual(str(transition_label.render()), "Selected Transitions")
                self.assertEqual(str(actor_label.render()), "Assigned Actors")
                self.assertFalse(bool(getattr(transition_list, "disabled", True)))
                self.assertTrue(bool(getattr(actor_list, "disabled", False)))

                transition_list.select(relation_ids["transition_id"])
                for _ in range(8):
                    await pilot.pause()
                    actor_list = app.query_one(f"#{_draft_model_relation_selection_list_id(1)}")
                    if not bool(getattr(actor_list, "disabled", True)):
                        break
                self.assertFalse(bool(getattr(actor_list, "disabled", True)))

                actor_list.select(relation_ids["actor_id"])
                detail_rows = set()
                for _ in range(8):
                    await pilot.pause()
                    detail_rows = {
                        (collapse_ws(row[0]), collapse_ws(row[1]))
                        for row in _table_rows(app.query_one("#draft_scope_detail_panel"))
                        if len(row) >= 2
                    }
                    if (
                        ("selected transitions (1)", "Move To Target") in detail_rows
                        and ("assigned actors (1)", "Operations Team") in detail_rows
                    ):
                        break
                self.assertIn(("selected transitions (1)", "Move To Target"), detail_rows)
                self.assertIn(("assigned actors (1)", "Operations Team"), detail_rows)

        asyncio.run(_exercise())

    def test_textual_draft_tab_bdd_shows_report_scope_and_workspace(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
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
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

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
        persist_subject_progress(self.root, "kinematics-demo", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "draft_tab")
                root_tabs = app.query_one("#root_tabs")
                status_widget = app.query_one(f"#{_subject_gate_status_table_id('draft', 'publication')}")
                status_panel = _table_text(status_widget)
                current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                tree_text = _table_text(app.query_one("#draft_scope_tree_panel"))
                detail_panel = app.query_one("#draft_scope_detail_panel")
                detail_text = _table_text(detail_panel)
                result_text = "\n".join(str(line) for line in app.query_one("#draft_result").lines)
                review_actions = [
                    app.query_one(f"#subject_draft_review_gate_action_{index}_button")
                    for index in range(1, 5)
                ]
                orientation_action = app.query_one("#subject_draft_action_1_button")
                draft_more_actions_row = app.query_one("#subject_draft_more_actions_row")
                semantic_select = app.query_one(f"#{_draft_semantic_kind_select_id()}")
                render_select = app.query_one(f"#{_draft_render_kind_select_id()}")
                evidence_select = app.query_one(f"#{_draft_evidence_mode_select_id()}")
                transform_select = app.query_one(f"#{_draft_transform_mode_select_id()}")
                detail_title = str(app.query_one("#draft_scope_detail_panel_title").render())

                self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                self.assertEqual(len(app.query("#subject_draft_publication_gate_summary")), 0)
                self.assertIn("Itemization |", status_panel)
                self.assertFalse(bool(getattr(status_widget, "show_header", True)))
                self.assertEqual(str(getattr(status_widget, "cursor_type", "")), "none")
                self.assertFalse(bool(getattr(status_widget, "show_horizontal_scrollbar", True)))
                self.assertIn("Create the draft composition", current_step)
                self.assertIn("no persisted draft review items yet", tree_text)
                self.assertTrue(detail_text)
                self.assertIn("Selection Details", detail_title)
                self.assertIn("Create Report Plan first", detail_text)
                self.assertFalse(bool(getattr(detail_panel, "show_header", True)))
                self.assertEqual(str(getattr(detail_panel, "cursor_type", "")), "none")
                self.assertIn("Draft Journal: kinematics-demo", result_text)
                self.assertIn("Selected Item", result_text)
                self.assertIn("draft composition: <none>", result_text)
                self.assertTrue(bool(getattr(draft_more_actions_row, "display", False)))
                self.assertTrue(bool(getattr(orientation_action, "display", False)))
                self.assertEqual(str(getattr(orientation_action, "label", "")), "Preview Itemization")
                self.assertTrue(bool(getattr(semantic_select, "disabled", False)))
                self.assertTrue(bool(getattr(render_select, "disabled", False)))
                self.assertTrue(bool(getattr(evidence_select, "disabled", False)))
                self.assertTrue(bool(getattr(transform_select, "disabled", False)))
                review_action_labels = {
                    str(getattr(button, "label", ""))
                    for button in review_actions
                }
                self.assertTrue(
                    any("Create Draft Composition" in label for label in review_action_labels),
                    review_action_labels,
                )

        asyncio.run(_exercise())

    def test_textual_draft_model_lens_strip_preserves_selection_across_frame_model_explore(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        source = new_learning_source(
            subject_id="draft-model-demo",
            title="Draft Model Notes",
            source_ref="notes/draft-model.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft Model Notes\n\n"
                "## Operations Team\n\n"
                "Operations owns the rollout.\n\n"
                "## Enable Alerts\n\n"
                "Enable alerts across the boundary.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="draft-model-demo",
            source_kind="markdown",
            rationale="Admit the draft model subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="draft-model-demo",
                unit_kind="definition",
                canonical_title="Operations Team",
            ),
            subject_id="draft-model-demo",
            unit_kind="definition",
            canonical_title="Operations Team",
            statement="Operations owns the rollout.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="draft-model-demo",
                canonical_title="Draft Model Demo",
                aliases=("Draft Model Demo",),
                subject_family="Operations",
                summary="Maintained subject for Draft Model lens behavior.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "draft-model-demo")
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        selected_item = next(
            item
            for item in list_itemized_subject_items(self.root, "draft-model-demo")
            if deterministic_transformation_construct_candidates_from_itemized_item(item)
        )
        progress.itemize_selected_item_id = selected_item.itemized_item_id
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
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "draft-model-demo")
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="open_draft_model_view",
        )
        persist_subject_progress(self.root, "draft-model-demo", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                open_model_button = app.query_one("#subject_draft_review_gate_action_2_button")
                open_model_label = str(getattr(open_model_button, "label", ""))
                if open_model_label == "Open Model":
                    open_model_button.press()
                    await pilot.pause()
                lens_tabs = app.query_one(f"#{_draft_model_lens_tabs_id()}")
                frame_tab = app.query_one(f"#{_draft_model_lens_tab_id('frame')}")
                model_tab = app.query_one(f"#{_draft_model_lens_tab_id('model')}")
                explore_tab = app.query_one(f"#{_draft_model_lens_tab_id('explore')}")
                tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                main_title = str(app.query_one("#draft_model_main_panel_title").render())
                detail_title = str(app.query_one("#draft_scope_detail_panel_title").render())
                issue_title = str(app.query_one("#draft_result_title").render())
                issue_text = "\n".join(str(line) for line in app.query_one("#draft_result").lines)

                self.assertTrue(bool(getattr(lens_tabs, "display", False)))
                self.assertEqual(str(getattr(lens_tabs, "active", "") or ""), _draft_model_lens_tab_id("model"))
                self.assertEqual(getattr(getattr(frame_tab, "styles", None), "color", None).a, 1.0)
                self.assertEqual(getattr(getattr(explore_tab, "styles", None), "color", None).a, 1.0)
                self.assertEqual(getattr(getattr(model_tab, "styles", None), "color", None).a, 1.0)
                self.assertRegex(tree_title, r"Case Objects \(\d+\)")
                self.assertIn("Transformation Model", main_title)
                self.assertTrue(detail_title)
                self.assertTrue(app.query_one("#draft_model_main_wrapper").display)
                self.assertTrue(app.query_one("#draft_result_panel").display)
                self.assertIn("Issues & Validation", issue_title)
                self.assertNotIn("Issues & Validation", issue_text.splitlines()[0] if issue_text.splitlines() else "")
                self.assertIn("Status Snapshot", issue_text)
                self.assertIn("open issues:", issue_text)
                self.assertIn("recommendation status:", issue_text)

                await pilot.click(f"#{_draft_model_lens_tab_id('frame')}")
                await pilot.pause()
                frame_tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                frame_main_title = str(app.query_one("#draft_model_main_panel_title").render())
                frame_detail_title = str(app.query_one("#draft_scope_detail_panel_title").render())
                frame_tabs = app.query_one(f"#{_draft_model_lens_tabs_id()}")
                self.assertRegex(frame_tree_title, r"Case Objects \(\d+\)")
                self.assertIn("Case Frame", frame_main_title)
                self.assertEqual(frame_detail_title, detail_title)
                self.assertEqual(str(getattr(frame_tabs, "active", "") or ""), _draft_model_lens_tab_id("frame"))

                await pilot.click(f"#{_draft_model_lens_tab_id('explore')}")
                await pilot.pause()
                explore_tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                explore_main_title = str(app.query_one("#draft_model_main_panel_title").render())
                explore_detail_title = str(app.query_one("#draft_scope_detail_panel_title").render())
                explore_tabs = app.query_one(f"#{_draft_model_lens_tabs_id()}")
                self.assertRegex(explore_tree_title, r"Case Objects \(\d+\)")
                self.assertIn("Explore Alternatives", explore_main_title)
                self.assertEqual(explore_detail_title, detail_title)
                self.assertEqual(str(getattr(explore_tabs, "active", "") or ""), _draft_model_lens_tab_id("explore"))

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_flow_surfaces_decision_analysis_as_the_next_step(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=_fake_run_live_dst_pipeline,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    activate_action = app.query_one("#subject_research_review_gate_action_1_button")
                    self.assertEqual(str(getattr(activate_action, "label", "")), "Activate Subject")
                    activate_action.press()
                    await pilot.pause()
                    maintained_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="research",
                        label="Check Maintained Files",
                    )
                    self.assertEqual(str(getattr(maintained_action, "label", "")), "Check Maintained Files")
                    maintained_action.press()
                    await pilot.pause()

                    await pilot.click("#tab_button_itemize_tab")
                    await pilot.pause()
                    self.assertEqual(app._active_tab_id(), "itemize_tab")
                    generate_itemization = app.query_one("#subject_itemize_review_gate_action_1_button")
                    self.assertEqual(str(getattr(generate_itemization, "label", "")), "Generate Itemization")
                    generate_itemization.press()
                    await pilot.pause()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()
                    create_draft = self._find_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Create Draft Composition",
                    )
                    if create_draft is not None:
                        create_draft.press()
                        await pilot.pause()
                        await pilot.pause()
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    start_analysis = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Start Decision Analysis",
                    )
                    open_model_before = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Open Model",
                    )
                    self.assertIn("Start decision analysis", current_step)
                    self.assertEqual(str(getattr(start_analysis, "label", "")), "Start Decision Analysis")
                    self.assertEqual(str(getattr(open_model_before, "label", "")), "Open Model")
                    start_analysis.press()
                    await pilot.pause()

                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    run_analysis = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Run Decision Analysis",
                    )
                    open_model_after_start = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Open Model",
                    )
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    self.assertNotIn("Start decision analysis", current_step)
                    self.assertEqual(str(getattr(run_analysis, "label", "")), "Run Decision Analysis")
                    self.assertEqual(str(getattr(open_model_after_start, "label", "")), "Open Model")
                    run_analysis.press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "review_tab")
                    approve_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="review",
                        label="Approve For Report",
                    )
                    review_step = str(app.query_one("#subject_review_review_gate_summary").render())
                    self.assertIn("Approve the report and decision analysis", review_step)
                    self.assertEqual(str(getattr(approve_action, "label", "")), "Approve For Report")
                    self.assertIn("Last Action: Decision analysis completed. Report plan updated.", review_step)

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_draft_keeps_open_model_visible_after_decision_analysis_completion(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=_fake_run_live_dst_pipeline,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()
                    await pilot.pause()
                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()
                    await pilot.pause()
                    await pilot.click("#tab_button_itemize_tab")
                    await pilot.pause()
                    await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="itemize",
                        label="Generate Itemization",
                    )).press()
                    await pilot.pause()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()
                    create_draft = self._find_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Create Draft Composition",
                    )
                    if create_draft is not None:
                        create_draft.press()
                        await pilot.pause()
                        await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Start Decision Analysis",
                    )).press()
                    await pilot.pause()
                    await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Run Decision Analysis",
                    )).press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "review_tab")
                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "draft_tab")
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    rerun_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Re-run Analysis (Balanced)",
                    )
                    open_model_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Open Model",
                    )
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", "") or "")
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    self.assertIn("Decision analysis is ready", current_step)
                    self.assertEqual(str(getattr(rerun_action, "label", "")), "Re-run Analysis (Balanced)")
                    self.assertEqual(str(getattr(open_model_action, "label", "")), "Open Model")
                    self.assertFalse(any(label.startswith("Role (") for label in draft_gate_labels), draft_gate_labels)

                    open_model_action.press()
                    await pilot.pause()

                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    self.assertIn("Case Objects", tree_title)

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_transition_state_selects_stay_bound_for_real_model_surface(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=_fake_run_live_dst_pipeline,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()
                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()

                    await pilot.click("#tab_button_itemize_tab")
                    await pilot.pause()
                    app.query_one("#subject_itemize_review_gate_action_1_button").press()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    create_draft = self._find_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Create Draft Composition",
                    )
                    if create_draft is not None:
                        create_draft.press()
                        await pilot.pause()
                    self._query_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Start Decision Analysis",
                    ).press()
                    await pilot.pause()
                    await pilot.pause()
                    run_button = self._find_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Run Decision Analysis",
                    )
                    if run_button is not None:
                        run_button.press()
                        await pilot.pause()
                        await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()
                    self._query_subject_gate_button_by_label(
                        app,
                        phase="draft",
                        label="Open Model",
                    ).press()
                    await pilot.pause()
                    await pilot.pause()

                    tree_panel = app.query_one("#draft_scope_tree_panel")
                    await pilot.click("#draft_scope_tree_panel")
                    await pilot.pause()
                    self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")

                    scenario = app._mock_subject_scenario()
                    progress = app._mock_subject_progress()
                    candidates = _subject_transformation_construct_candidates(
                        self.root,
                        scenario=scenario,
                        include_rejected=False,
                    )
                    target_index = next(
                        index
                        for index, candidate in enumerate(candidates)
                        if collapse_ws(candidate.status) == "accepted"
                        and collapse_ws(candidate.sort_kind) == "transition"
                        and collapse_ws(candidate.canonical_label) == "add compatibility and inspection tools"
                    )
                    current_index = int(getattr(progress, "draft_model_cursor", 0) or 0)
                    key = "down" if target_index >= current_index else "up"
                    for _ in range(abs(target_index - current_index)):
                        await pilot.press(key)
                    await pilot.pause()

                    selected_progress = app._mock_subject_progress()
                    selected_candidate = candidates[target_index]
                    self.assertEqual(
                        collapse_ws(selected_progress.draft_selected_construct_candidate_id),
                        collapse_ws(selected_candidate.construct_candidate_id),
                    )

                    transition_row = app.query_one("#draft_model_transition_row")
                    source_select = app.query_one(f"#{_draft_model_transition_source_select_id()}")
                    target_select = app.query_one(f"#{_draft_model_transition_target_select_id()}")
                    null_value = getattr(type(source_select), "NULL", object())

                    self.assertTrue(bool(getattr(transition_row, "display", False)))
                    self.assertFalse(bool(getattr(source_select, "disabled", True)))
                    self.assertFalse(bool(getattr(target_select, "disabled", True)))
                    self.assertNotEqual(getattr(source_select, "value", null_value), null_value)
                    self.assertNotEqual(getattr(target_select, "value", null_value), null_value)

        asyncio.run(_exercise())

    def test_textual_draft_decision_included_switch_toggles_selected_item_membership(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        markdown_path = DST_SOURCE_ROOT / "City bus prose v2.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
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
            action_key="create_decision_frame_from_selected_draft_item",
        )
        decision_items = list_decision_review_items(self.root, scenario.subject_id)
        self.assertGreater(len(decision_items), 0)
        progress.draft_selected_review_item_id = collapse_ws(decision_items[0].review_item_id)
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                included_switch = app.query_one(f"#{_draft_decision_included_switch_id()}")
                detail_panel = app.query_one("#draft_scope_detail_panel")
                tree_panel = app.query_one("#draft_scope_tree_panel")
                selected_row = tuple(str(cell) for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0)))

                self.assertTrue(bool(getattr(included_switch, "display", True)))
                self.assertFalse(bool(getattr(included_switch, "disabled", True)))
                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertIn("selected in decision frame | yes", collapse_ws(_table_text(detail_panel)))
                self.assertEqual(selected_row[0], "x")
                self.assertGreaterEqual(len(selected_row), 2)

                await pilot.click(f"#{_draft_decision_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()

                selected_row = tuple(str(cell) for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0)))
                self.assertFalse(bool(getattr(included_switch, "value", True)))
                self.assertIn("selected in decision frame | no", collapse_ws(_table_text(detail_panel)))
                self.assertEqual(selected_row[0], "x")
                self.assertGreaterEqual(len(selected_row), 2)

                await pilot.click(f"#{_draft_decision_included_switch_id()}")
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()

                selected_row = tuple(str(cell) for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0)))
                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertIn("selected in decision frame | yes", collapse_ws(_table_text(detail_panel)))
                self.assertEqual(selected_row[0], "x")
                self.assertGreaterEqual(len(selected_row), 2)

        asyncio.run(_exercise())

    def test_textual_draft_compose_inventory_supports_up_down_and_decision_toggle_for_weak_prose(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        markdown_path = DST_SOURCE_ROOT / "City bus prose v2.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        scenario = default_subject_scenarios(self.root)[0]
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
        apply_subject_action(
            root_path=self.root,
            scenario=scenario,
            progress=progress,
            action_key="refresh_review_composition",
            host_actions=host_actions,
        )
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                detail_panel = app.query_one("#draft_scope_detail_panel")
                included_switch = app.query_one(f"#{_draft_decision_included_switch_id()}")
                tree_panel = app.query_one("#draft_scope_tree_panel")
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()

                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")
                self.assertIn("Smart City Travel", collapse_ws(_table_text(detail_panel)))
                self.assertTrue(bool(getattr(included_switch, "value", False)))

                await pilot.press("down")
                await pilot.pause()

                detail_text = collapse_ws(_table_text(detail_panel))
                selected_row = tuple(
                    str(cell)
                    for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                )
                selected_line = " | ".join(selected_row)

                self.assertIn(
                    "changes that can be implemented without disrupting daily service",
                    detail_text,
                )
                self.assertIn(
                    "changes that can be implemented without disrupting daily service",
                    selected_line,
                )
                self.assertFalse(bool(getattr(included_switch, "disabled", True)))
                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertIn("x", selected_row[0])
                self.assertGreaterEqual(len(selected_row), 2)

                await pilot.click(f"#{_draft_decision_included_switch_id()}")
                detail_text = ""
                selected_row = ()
                for _ in range(8):
                    await pilot.pause()
                    detail_text = collapse_ws(_table_text(detail_panel))
                    selected_row = tuple(
                        str(cell)
                        for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                    )
                    if (
                        not bool(getattr(included_switch, "value", False))
                        and "selected in decision frame | no" in detail_text
                    ):
                        break

                selected_line = " | ".join(selected_row)
                self.assertFalse(bool(getattr(included_switch, "value", False)))
                self.assertIn("selected in decision frame | no", detail_text)
                self.assertIn("x", selected_row[0])
                self.assertGreaterEqual(len(selected_row), 2)

                await pilot.click(f"#{_draft_decision_included_switch_id()}")
                for _ in range(8):
                    await pilot.pause()
                    detail_text = collapse_ws(_table_text(detail_panel))
                    selected_row = tuple(
                        str(cell)
                        for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                    )
                    if (
                        bool(getattr(included_switch, "value", False))
                        and "selected in decision frame | yes" in detail_text
                    ):
                        break

                selected_line = " | ".join(selected_row)
                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertIn("selected in decision frame | yes", detail_text)
                self.assertIn("x", selected_row[0])
                self.assertGreaterEqual(len(selected_row), 2)

        asyncio.run(_exercise())

    def test_textual_weak_prose_draft_shows_start_decision_analysis_after_construct_suggestion(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        markdown_path = DST_SOURCE_ROOT / "City bus prose v2.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        class EmptyController:
            def request_proposal(self, **kwargs):
                return SimpleNamespace(
                    id="proposal-direct-itemize-empty",
                    source="fake-runtime",
                    payload={"candidates": []},
                )

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.pause()

                current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                start_analysis = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="draft",
                    label="Start Decision Analysis",
                )
                open_model = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="draft",
                    label="Open Model",
                )

                draft_gate_labels = [
                    str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                ]

                self.assertIn("Start decision analysis", current_step)
                self.assertEqual(str(getattr(start_analysis, "label", "")), "Start Decision Analysis")
                self.assertEqual(str(getattr(open_model, "label", "")), "Open Model")
                self.assertNotIn("Hand To Review", draft_gate_labels)

        asyncio.run(_exercise())

    def test_textual_weak_prose_review_and_publication_route_back_to_start_decision_analysis(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        markdown_path = DST_SOURCE_ROOT / "City bus prose v10.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key=action_key)
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                await pilot.pause()

                review_start = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="review",
                    label="Start Decision Analysis",
                )
                review_step = str(app.query_one("#subject_review_review_gate_summary").render())
                review_labels = [
                    str(getattr(app.query_one(f"#subject_review_review_gate_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_review_review_gate_action_{index}_button"), "display", False))
                ]

                self.assertIn("Start decision analysis", review_step)
                self.assertEqual(str(getattr(review_start, "label", "")), "Start Decision Analysis")
                self.assertNotIn("Approve For Report", review_labels)

                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()
                await pilot.pause()

                publication_start = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="publication",
                    label="Start Decision Analysis",
                )
                publication_step = str(app.query_one("#subject_publication_review_gate_summary").render())
                publication_labels = [
                    str(getattr(app.query_one(f"#subject_publication_review_gate_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_publication_review_gate_action_{index}_button"), "display", False))
                ]

                self.assertIn("Start decision analysis", publication_step)
                self.assertEqual(str(getattr(publication_start, "label", "")), "Start Decision Analysis")
                self.assertNotIn("Lock Report Inputs", publication_labels)
                self.assertNotIn("Build Report", publication_labels)

        asyncio.run(_exercise())

    def test_textual_same_subject_v2_then_v10_draft_toggle_stays_responsive(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            load_subject_progress,
            persist_subject_progress,
        )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        progress = load_subject_progress(self.root, scenario.subject_id)
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
                scenario=scenario,
                progress=progress,
                action_key=action_key,
            )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key=action_key,
            )
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()

                tree_panel = app.query_one("#draft_scope_tree_panel")
                detail_panel = app.query_one("#draft_scope_detail_panel")
                included_switch = app.query_one(f"#{_draft_decision_included_switch_id()}")

                found_toggle_candidate = False
                for _ in range(40):
                    selected_row = tuple(
                        str(cell)
                        for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                    )
                    if "x" in collapse_ws(selected_row[0]) and not bool(getattr(included_switch, "value", True)):
                        found_toggle_candidate = True
                        break
                    await pilot.press("down")
                    await pilot.pause()

                self.assertTrue(found_toggle_candidate, "expected a later v10 draft row outside the decision frame")
                self.assertFalse(bool(getattr(included_switch, "value", True)))

                await pilot.press("d")
                detail_text = ""
                selected_row = ()
                for _ in range(20):
                    await pilot.pause()
                    detail_text = collapse_ws(_table_text(detail_panel))
                    selected_row = tuple(
                        str(cell)
                        for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                    )
                    if (
                        bool(getattr(included_switch, "value", False))
                        and "selected in decision frame | yes" in detail_text
                    ):
                        break

                self.assertTrue(bool(getattr(included_switch, "value", False)))
                self.assertGreaterEqual(len(selected_row), 2)
                self.assertIn("selected in decision frame | yes", detail_text)

        asyncio.run(_exercise())

    def test_textual_same_subject_v2_then_v10_review_and_publication_route_back_to_refresh_dst_analysis(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            load_subject_progress,
            persist_subject_progress,
        )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        progress = load_subject_progress(self.root, scenario.subject_id)
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
            "create_decision_frame_from_selected_draft_item",
            "analyze_decision_frame",
        ):
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key=action_key)

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key=action_key)
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                await pilot.pause()

                review_refresh = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="review",
                    label="Refresh DST Analysis",
                )
                review_step = str(app.query_one("#subject_review_review_gate_summary").render())
                review_labels = [
                    str(getattr(app.query_one(f"#subject_review_review_gate_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_review_review_gate_action_{index}_button"), "display", False))
                ]

                self.assertIn("Refresh the DST-backed decision analysis", review_step)
                self.assertEqual(str(getattr(review_refresh, "label", "")), "Refresh DST Analysis")
                self.assertNotIn("Approve For Report", review_labels)

                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()
                await pilot.pause()

                publication_refresh = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="publication",
                    label="Refresh DST Analysis",
                )
                publication_step = str(app.query_one("#subject_publication_review_gate_summary").render())
                publication_labels = [
                    str(getattr(app.query_one(f"#subject_publication_review_gate_action_{index}_button"), "label", "") or "")
                    for index in range(1, 5)
                    if bool(getattr(app.query_one(f"#subject_publication_review_gate_action_{index}_button"), "display", False))
                ]

                self.assertIn("Refresh the DST-backed decision analysis", publication_step)
                self.assertEqual(str(getattr(publication_refresh, "label", "")), "Refresh DST Analysis")
                self.assertNotIn("Lock Report Inputs", publication_labels)
                self.assertNotIn("Build Report", publication_labels)

        asyncio.run(_exercise())

    def test_textual_draft_stale_tab_payload_is_ignored_after_local_cursor_move(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            load_subject_progress,
            persist_subject_progress,
        )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        progress = load_subject_progress(self.root, scenario.subject_id)
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
                scenario=scenario,
                progress=progress,
                action_key=action_key,
            )
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()

                tree_panel = app.query_one("#draft_scope_tree_panel")
                detail_panel = app.query_one("#draft_scope_detail_panel")
                original_request_id = int(getattr(app, "_tab_refresh_request_id", 0) or 0)

                before_row = int(getattr(tree_panel, "cursor_row", 0) or 0)
                await pilot.press("down")
                await pilot.pause()

                after_row = int(getattr(tree_panel, "cursor_row", 0) or 0)
                self.assertGreater(after_row, before_row)
                current_detail_text = collapse_ws(_table_text(detail_panel))

                stale_payload = _TextualTabContentPayload(
                    tab_id="draft_tab",
                    request_id=original_request_id,
                    wrap_width=80,
                    current_step_text="stale current step",
                    review_scope_lines=("0 | x | stale draft row",),
                    review_scope_detail_lines=("field | stale detail",),
                )
                app._apply_tab_content_payload(stale_payload)
                await pilot.pause()

                self.assertEqual(int(getattr(tree_panel, "cursor_row", 0) or 0), after_row)
                self.assertEqual(collapse_ws(_table_text(detail_panel)), current_detail_text)
                self.assertNotIn("stale detail", collapse_ws(_table_text(detail_panel)))

        asyncio.run(_exercise())

    def test_textual_draft_watch_event_does_not_revert_newer_local_selection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            load_subject_progress,
            persist_subject_progress,
        )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v2.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        progress = load_subject_progress(self.root, scenario.subject_id)
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
                scenario=scenario,
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )

        workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=DST_SOURCE_ROOT / "City bus prose v10.md",
            testing_lightweight=False,
        )
        scenario = default_subject_scenarios(self.root)[0]
        for action_key in (
            "open_context",
            "compare_projections",
            "generate_itemization",
            "refresh_review_composition",
        ):
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key=action_key,
                host_actions=host_actions,
            )
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()

                tree_panel = app.query_one("#draft_scope_tree_panel")
                included_switch = app.query_one(f"#{_draft_decision_included_switch_id()}")
                found_toggle_candidate = False
                for _ in range(40):
                    selected_row = tuple(
                        str(cell)
                        for cell in tree_panel.get_row_at(int(getattr(tree_panel, "cursor_row", 0) or 0))
                    )
                    if "x" in collapse_ws(selected_row[0]) and not bool(getattr(included_switch, "value", True)):
                        found_toggle_candidate = True
                        break
                    await pilot.press("down")
                    await pilot.pause()

                self.assertTrue(found_toggle_candidate)
                self.assertFalse(bool(getattr(included_switch, "value", True)))

                await pilot.press("d")
                for _ in range(20):
                    await pilot.pause()
                    if bool(getattr(included_switch, "value", False)):
                        break
                self.assertTrue(bool(getattr(included_switch, "value", False)))

                stale_progress = load_subject_progress(self.root, scenario.subject_id)
                stale_snapshot = app._subject_projection_backend.get_snapshot(
                    root_path=self.root,
                    subject_id=scenario.subject_id,
                    phase="draft",
                    progress=stale_progress,
                    **app._subject_phase_projection_kwargs(),
                )
                stale_progress_fingerprint = app._subject_projection_backend.progress_fingerprint(stale_progress)

                await pilot.press("down")
                await pilot.pause()
                await pilot.press("down")
                await pilot.pause()

                selected_before = collapse_ws(app._mock_subject_progress().draft_selected_review_item_id)
                watch_key = app._subject_workflow_watch_identity()
                self.assertIsNotNone(watch_key)

                app._apply_subject_workflow_watch_event(
                    watch_key,
                    SimpleNamespace(
                        event_kind="subject_workflow_changed",
                        snapshot=stale_snapshot,
                        channel_key=f"subject/{scenario.subject_id}/draft",
                        sequence=int(getattr(app, "_subject_workflow_watch_last_sequence", 0) or 0) + 1,
                        snapshot_version="stale-snapshot",
                        progress_fingerprint=stale_progress_fingerprint,
                    ),
                )
                await pilot.pause()

                selected_after = collapse_ws(app._mock_subject_progress().draft_selected_review_item_id)
                self.assertEqual(selected_after, selected_before)
                self.assertNotEqual(selected_after, collapse_ws(stale_progress.draft_selected_review_item_id))

        asyncio.run(_exercise())

    def test_textual_regional_dst_model_view_shows_full_case_objects_after_starting_decision_analysis(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "Regional emergency alerting system.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.pause()

                for _ in range(20):
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    if "Case Objects" in tree_title:
                        break
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    if "Open Model" in draft_gate_labels:
                        open_model_action = next(
                            app.query_one(f"#subject_draft_review_gate_action_{index}_button")
                            for index in range(1, 5)
                            if str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                            == "Open Model"
                        )
                        open_model_action.press()
                    await pilot.pause()

                for _ in range(10):
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    if "Case Objects" in tree_title:
                        break
                    await pilot.pause()

                tree_text = _table_text(app.query_one("#draft_scope_tree_panel"))
                main_panel = app.query_one("#draft_model_main_panel")
                main_text = _table_text(main_panel)
                detail_text = _table_text(app.query_one("#draft_scope_detail_panel"))
                pane_tree_text = app._mock_subject_pane_text("draft", "draft_scope_tree")

                first_tree_line = next((line for line in tree_text.splitlines() if line.strip()), "")
                tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                self.assertNotEqual(first_tree_line, "Case Objects")
                self.assertIn("Case Objects", tree_title)
                self.assertNotIn("Objects (", tree_text)
                self.assertNotIn("Active lens:", tree_text)
                self.assertIn("a | hospitals (Actor -> Actor)", tree_text)
                self.assertIn(
                    "[a] agency-to-telecom boundary (Boundary -> Boundary)",
                    pane_tree_text,
                )
                self.assertIsInstance(main_panel, _FocusableTextualDataTable)
                self.assertFalse(bool(getattr(main_panel, "show_header", True)))
                self.assertFalse(bool(getattr(main_panel, "show_horizontal_scrollbar", True)))
                self.assertEqual(str(getattr(main_panel, "cursor_type", "")), "none")
                normalized_main_text = collapse_ws(main_text)
                self.assertIn("Accepted decision items", normalized_main_text)
                self.assertIn("Selected object | hospitals", normalized_main_text)
                first_detail_line = next((line for line in detail_text.splitlines() if line.strip()), "")
                self.assertNotEqual(first_detail_line, "hospitals")
                self.assertIn("hospitals", detail_text)
                self.assertIn("status | accepted", detail_text)

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_approved_draft_still_offers_open_model(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=_fake_run_live_dst_pipeline,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    activate_action = app.query_one("#subject_research_review_gate_action_1_button")
                    self.assertEqual(str(getattr(activate_action, "label", "")), "Activate Subject")
                    activate_action.press()
                    maintained_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="research",
                        label="Check Maintained Files",
                    )
                    self.assertEqual(str(getattr(maintained_action, "label", "")), "Check Maintained Files")
                    maintained_action.press()
                    await pilot.pause()

                    if app._active_tab_id() != "itemize_tab":
                        await pilot.click("#tab_button_itemize_tab")
                        await pilot.pause()
                        await pilot.pause()
                    self.assertEqual(app._active_tab_id(), "itemize_tab")
                    generate_itemization = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="itemize",
                        label="Generate Itemization",
                    )
                    self.assertEqual(str(getattr(generate_itemization, "label", "")), "Generate Itemization")
                    generate_itemization.press()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()
                    start_analysis = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Start Decision Analysis",
                    )
                    self.assertEqual(str(getattr(start_analysis, "label", "")), "Start Decision Analysis")
                    start_analysis.press()
                    await pilot.pause()
                    await pilot.pause()

                    run_analysis = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Run Decision Analysis",
                    )
                    self.assertEqual(str(getattr(run_analysis, "label", "")), "Run Decision Analysis")
                    run_analysis.press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "review_tab")
                    approve_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="review",
                        label="Approve For Report",
                    )
                    self.assertEqual(str(getattr(approve_action, "label", "")), "Approve For Report")
                    approve_action.press()
                    await pilot.pause()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "draft_tab")
                    open_model_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Open Model",
                    )
                    refresh_dst_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Refresh DST Analysis",
                    )
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    self.assertIn("Draft composition is approved", current_step)
                    self.assertEqual(str(getattr(open_model_action, "label", "")), "Open Model")
                    self.assertFalse(open_model_action.has_class("subject_gate_action_button_phase_nav"))
                    self.assertEqual(str(getattr(refresh_dst_action, "label", "")), "Refresh DST Analysis")

                    open_model_action.press()
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    for _ in range(10):
                        await pilot.pause()
                        current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                        if "Draft composition is approved" not in current_step:
                            break
                    tree_text = _table_text(app.query_one("#draft_scope_tree_panel"))

                    self.assertEqual(app._active_tab_id(), "draft_tab")
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    self.assertIn("Case Objects", tree_title)
                    self.assertNotIn("Draft composition is approved", current_step)
                    first_tree_line = next((line for line in tree_text.splitlines() if line.strip()), "")
                    self.assertNotEqual(first_tree_line, "Case Objects")
                    self.assertNotIn("Objects (", tree_text)
                    self.assertNotIn("Active lens:", tree_text)

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_review_and_publication_keep_open_model_available(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
                side_effect=_fake_run_live_dst_pipeline,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()
                    app.query_one("#subject_research_review_gate_action_1_button").press()
                    await pilot.pause()
                    if app._active_tab_id() != "itemize_tab":
                        await pilot.click("#tab_button_itemize_tab")
                        await pilot.pause()
                        await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="itemize",
                        label="Generate Itemization",
                    )).press()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Start Decision Analysis",
                    )).press()
                    await pilot.pause()
                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="draft",
                        label="Run Decision Analysis",
                    )).press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "review_tab")
                    review_open_model = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="review",
                        label="Open Model",
                    )
                    review_step = str(app.query_one("#subject_review_review_gate_summary").render())
                    self.assertIn("Approve the report and decision analysis", review_step)
                    self.assertEqual(str(getattr(review_open_model, "label", "")), "Open Model")
                    self.assertTrue(review_open_model.has_class("subject_gate_action_button_phase_nav"))

                    (await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="review",
                        label="Approve For Report",
                    )).press()
                    await pilot.pause()
                    await pilot.pause()

                    if app._active_tab_id() != "publication_tab":
                        await pilot.click("#tab_button_publication_tab")
                        await pilot.pause()
                    self.assertEqual(app._active_tab_id(), "publication_tab")
                    publication_open_model = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="publication",
                        label="Open Model",
                    )
                    publication_step = str(app.query_one("#subject_publication_review_gate_summary").render())
                    self.assertIn("attached decision analysis", publication_step)
                    self.assertEqual(str(getattr(publication_open_model, "label", "")), "Open Model")
                    self.assertTrue(publication_open_model.has_class("subject_gate_action_button_phase_nav"))

                    publication_open_model.press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "draft_tab")
                    self.assertEqual(collapse_ws(getattr(app._mock_subject_progress(), "draft_focus_mode", "")), "compose")
                    current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                    self.assertNotIn("Last Action: Moved Draft focus to Model.", current_step)
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    self.assertIn("Open Model", draft_gate_labels)

        asyncio.run(_exercise())

    def test_textual_dst_city_bus_built_publication_action_row_keeps_open_model_available(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
        progress = new_subject_progress()
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=_fake_run_live_dst_pipeline,
        ):
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="analyze_decision_frame",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="approve_review",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="lock_publication",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="build_report",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="open_release_packet",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="complete_release_review",
            )
        persist_subject_progress(self.root, "city-bus-ticketing-modernization", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_publication_tab")
                await pilot.pause()
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "publication_tab")
                action_one = app.query_one("#subject_publication_action_1_button")
                action_two = app.query_one("#subject_publication_action_2_button")
                action_three = app.query_one("#subject_publication_action_3_button")
                action_four = app.query_one("#subject_publication_action_4_button")
                visible_actions = (action_one, action_two, action_three, action_four)
                labels = [str(getattr(button, "label", "")) for button in visible_actions]
                self.assertIn("Open Model", labels)
                self.assertTrue(
                    any(label in {"Preview report.pdf", "Open Release Folder", "Rebuild Report"} for label in labels),
                    msg=f"Unexpected publication actions: {labels}",
                )

                open_model_action = next(button for button in visible_actions if str(getattr(button, "label", "")) == "Open Model")
                open_model_action.press()
                await pilot.pause()
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "draft_tab")
                self.assertEqual(collapse_ws(getattr(app._mock_subject_progress(), "draft_focus_mode", "")), "compose")
                current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                self.assertNotIn("Last Action: Moved Draft focus to Model.", current_step)
                draft_gate_labels: list[str] = []
                for _ in range(20):
                    await pilot.pause()
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    if "Open Model" in draft_gate_labels:
                        break
                self.assertIn("Open Model", draft_gate_labels)

        asyncio.run(_exercise())

    def test_textual_draft_open_model_phase_nav_returns_to_compose_with_open_model_button(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "City bus ticketing modernization.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

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

        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
        progress = new_subject_progress()
        with patch(
            "workstation.subject.core.subject_workflow.run_live_dst_pipeline_from_fixture",
            side_effect=_fake_run_live_dst_pipeline,
        ):
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
            apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="goto_draft")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="create_decision_frame_from_selected_draft_item",
            )
            scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "city-bus-ticketing-modernization")
            apply_subject_action(
                root_path=self.root,
                scenario=scenario,
                progress=progress,
                action_key="analyze_decision_frame",
            )
        progress.draft_focus_mode = "model"
        persist_subject_progress(self.root, "city-bus-ticketing-modernization", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                gate_buttons = [
                    app.query_one(f"#subject_review_review_gate_action_{index}_button")
                    for index in range(1, 5)
                ]
                phase_nav_buttons = [
                    button
                    for button in gate_buttons
                    if bool(getattr(button, "display", False))
                    and button.has_class("subject_gate_action_button_phase_nav")
                    and "Open Model" in str(getattr(button, "label", ""))
                ]
                self.assertTrue(
                    phase_nav_buttons,
                    msg=[str(getattr(button, "label", "")) for button in gate_buttons],
                )
                self.assertEqual(str(getattr(phase_nav_buttons[0], "label", "")), "Open Model")

                phase_nav_buttons[0].press()
                await pilot.pause()
                await pilot.pause()

                self.assertEqual(app._active_tab_id(), "draft_tab")
                self.assertEqual(collapse_ws(getattr(app._mock_subject_progress(), "draft_focus_mode", "")), "compose")
                current_step = str(app.query_one("#subject_draft_review_gate_summary").render())
                self.assertNotIn("Last Action: Moved Draft focus to Model.", current_step)
                draft_gate_labels: list[str] = []
                for _ in range(20):
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    if "Open Model" in draft_gate_labels:
                        break
                    await pilot.pause()
                self.assertIn("Open Model", draft_gate_labels)

        asyncio.run(_exercise())

    def test_textual_regional_dst_case_objects_shows_all_rows_and_scrolls_with_selection(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "Regional emergency alerting system.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
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
        persist_subject_progress(self.root, scenario.subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(140, 34)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()
                await pilot.pause()

                for _ in range(20):
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    if "Case Objects" in tree_title:
                        break
                    draft_gate_labels = [
                        str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                        for index in range(1, 5)
                        if bool(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "display", False))
                    ]
                    if "Open Model" in draft_gate_labels:
                        open_model_action = next(
                            app.query_one(f"#subject_draft_review_gate_action_{index}_button")
                            for index in range(1, 5)
                            if str(getattr(app.query_one(f"#subject_draft_review_gate_action_{index}_button"), "label", ""))
                            == "Open Model"
                        )
                        open_model_action.press()
                    await pilot.pause()

                for _ in range(10):
                    tree_title = str(app.query_one("#draft_scope_tree_panel_title").render())
                    if "Case Objects" in tree_title:
                        break
                    await pilot.pause()
                tree_panel = app.query_one("#draft_scope_tree_panel")
                self.assertIsInstance(tree_panel, _FocusableTextualDataTable)
                tree_panel.focus()
                await pilot.pause()
                initial_selected = str(app._mock_subject_progress().draft_selected_construct_candidate_id)
                initial_scroll_y = float(getattr(tree_panel, "scroll_y", 0.0) or 0.0)
                tree_text = _table_text(tree_panel)

                self.assertNotIn("Objects (", tree_text)
                self.assertNotIn("Active lens:", tree_text)
                self.assertNotIn("more constructs", tree_text)

                for _ in range(20):
                    await pilot.press("down")
                    await pilot.pause()

                updated_scroll_y = float(getattr(tree_panel, "scroll_y", 0.0) or 0.0)
                max_scroll_y = float(getattr(tree_panel, "max_scroll_y", 0.0) or 0.0)
                updated_selected = str(app._mock_subject_progress().draft_selected_construct_candidate_id)

                self.assertNotEqual(initial_selected, updated_selected)
                if max_scroll_y > initial_scroll_y:
                    self.assertGreater(updated_scroll_y, initial_scroll_y)

        asyncio.run(_exercise())

    def test_textual_draft_detail_pane_can_maximize_and_seed_chat_prompt(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        source = new_learning_source(
            subject_id="draft-ask-demo",
            title="Draft Ask Notes",
            source_ref="notes/draft-ask.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft Ask Notes\n\n"
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
            subject_id="draft-ask-demo",
            source_kind="markdown",
            rationale="Admit the draft ask subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="draft-ask-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="draft-ask-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="draft-ask-demo",
                canonical_title="Draft Ask Demo",
                aliases=("Draft Ask Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for draft detail chat handoff.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

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
        persist_subject_progress(self.root, "draft-ask-demo", progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                await pilot.click("#draft_scope_detail_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_detail_panel")

                app.action_toggle_maximized_pane()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "draft_scope_detail_panel")
                self.assertFalse(app.query_one("#draft_scope_tree_wrapper").display)
                self.assertTrue(app.query_one("#draft_scope_detail_wrapper").display)
                self.assertFalse(app.query_one("#draft_result_panel").display)
                self.assertEqual(len(app.query("#draft_status_panel")), 0)

                worker_prompts: list[str] = []

                def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
                    worker_prompts.append(prompt)

                self.assertEqual(str(getattr(app.query_one("#draft_scope_detail_llm_button"), "label", "")), "@llm")
                with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                    app.query_one("#draft_scope_detail_llm_button").press()
                    await pilot.pause()

                self.assertEqual(app._active_tab_id(), "chat_tab")
                input_widget = app.query_one("#input")
                self.assertEqual(str(getattr(input_widget, "value", "") or ""), "")
                transcript_text = app._state.transcript_text()
                self.assertIn("Started a draft-item rephrase in Chat.", transcript_text)
                self.assertEqual(len(worker_prompts), 1)
                self.assertIn("Rephrase this selected draft item for publication clarity.", worker_prompts[0])
                self.assertIn("[label]", worker_prompts[0])
                self.assertIn("[text]", worker_prompts[0])
                self.assertIn("Selection details:", worker_prompts[0])

        asyncio.run(_exercise())

    def test_textual_itemize_detail_llm_button_routes_rephrase_prompt_into_chat(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "itemize-ask-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Itemize Ask Demo",
            source_ref="notes/itemize-ask.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Itemize Ask Demo\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the itemize ask demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Itemize Ask Demo",
                aliases=("Itemize Ask Demo",),
                subject_family="Governance",
                summary="Maintained subject for itemize detail chat handoff.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        persist_subject_progress(self.root, subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()

                await pilot.click("#itemize_detail_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "itemize_detail_panel")

                worker_prompts: list[str] = []

                def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
                    worker_prompts.append(prompt)

                self.assertEqual(str(getattr(app.query_one("#itemize_detail_llm_button"), "label", "")), "@llm")
                with patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                    app.query_one("#itemize_detail_llm_button").press()
                    await pilot.pause()

                transcript_text = app._state.transcript_text()
                self.assertEqual(app._active_tab_id(), "chat_tab")
                self.assertEqual(len(worker_prompts), 1)
                self.assertIn("Started an itemize-item rephrase in Chat.", transcript_text)
                self.assertIn("Rephrase this selected itemized candidate for clarity as a normalized intermediate.", worker_prompts[0])
                self.assertIn("[label]", worker_prompts[0])
                self.assertIn("[text]", worker_prompts[0])
                self.assertIn("Do not turn it into final publication prose.", worker_prompts[0])
                self.assertIn("Item details:", worker_prompts[0])

        asyncio.run(_exercise())

    def test_textual_manual_rephrase_buttons_open_edit_files(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "manual-rephrase-ui-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Manual Rephrase UI Demo",
            source_ref="notes/manual-rephrase.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Manual Rephrase UI Demo\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the manual rephrase ui demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Manual Rephrase UI Demo",
                aliases=("Manual Rephrase UI Demo",),
                subject_family="Governance",
                summary="Manual rephrase UI coverage subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        persist_subject_progress(self.root, subject_id, progress)

        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_itemize_tab")
                    await pilot.pause()
                    app.query_one("#itemize_detail_manual_rephrase_button").press()
                    await pilot.pause()

                    await pilot.click("#tab_button_draft_tab")
                    await pilot.pause()
                    app.query_one("#draft_scope_detail_manual_rephrase_button").press()
                    await pilot.pause()

            self.assertGreaterEqual(len(opened_paths), 2)
            self.assertTrue(all(path.is_file() for path in opened_paths[:2]))

        asyncio.run(_exercise())

    def test_textual_review_section_brief_buttons_open_chat_and_manual_file(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "review-section-brief-ui-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Review Section Brief UI Demo",
            source_ref="notes/review-section-brief.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Review Section Brief UI Demo\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the review section brief ui demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Review Section Brief UI Demo",
                aliases=("Review Section Brief UI Demo",),
                subject_family="Governance",
                summary="Review section brief UI coverage subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        progress.projections_compared = True
        progress.comparison_status = "aligned"
        progress.report_scope_cursor = 0
        for _ in range(64):
            detail = render_subject_report_scope_detail(scenario=scenario, progress=progress)
            if detail.startswith("Summary") and "Type: Report section" in detail:
                break
            move_report_scope_cursor(self.root, scenario=scenario, progress=progress, delta=1)
        persist_subject_progress(self.root, subject_id, progress)

        opened_paths: list[Path] = []
        worker_prompts: list[str] = []

        def _capture_worker(*, state, prompt, model, max_tool_rounds, force_llm_only=False) -> None:
            worker_prompts.append(prompt)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ), patch("workstation.ui.textual.chat_ui._run_enhanced_workstation_turn_worker", _capture_worker):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_review_tab")
                    await pilot.pause()
                    self.assertEqual(str(getattr(app.query_one(f'#{_review_detail_llm_button_id()}'), "label", "")), "@llm")
                    self.assertFalse(getattr(app.query_one(f'#{_review_detail_llm_button_id()}'), "disabled", True))
                    self.assertFalse(getattr(app.query_one(f'#{_review_detail_manual_rephrase_button_id()}'), "disabled", True))

                    app.query_one(f"#{_review_detail_manual_rephrase_button_id()}").press()
                    await pilot.pause()
                    app.query_one(f"#{_review_detail_llm_button_id()}").press()
                    await pilot.pause()

            self.assertTrue(opened_paths and opened_paths[0].is_file())
            self.assertEqual(len(worker_prompts), 1)
            self.assertIn("Draft a section brief for the selected report section.", worker_prompts[0])
            self.assertIn("This is publication-composition guidance, not source cleanup and not final report prose.", worker_prompts[0])
            self.assertIn("[label]", worker_prompts[0])
            self.assertIn("[text]", worker_prompts[0])

        asyncio.run(_exercise())

    def test_textual_itemize_inventory_typed_option_selects_row(self) -> None:
        selected_ordinals: list[int] = []

        class _FakeBackend:
            @staticmethod
            def itemization_session_and_items(*, root_path, scenario):
                del root_path, scenario
                return None, (
                    SimpleNamespace(itemized_item_id="first-item"),
                    SimpleNamespace(itemized_item_id="second-item"),
                )

        class _FakeApp:
            def __init__(self) -> None:
                self._inventory_option_sync_suppressed = set()
                self._subject_projection_backend = _FakeBackend()
                self._root = Path(".")
                self._progress = SimpleNamespace(
                    itemize_cursor=0,
                    itemize_selected_item_id="first-item",
                )
                self._widget = SimpleNamespace(
                    inventory_items=(
                        SimpleNamespace(entry_id="first-item"),
                        SimpleNamespace(entry_id="second-item"),
                    )
                )

            def query_one(self, selector: str):
                self.assert_selector = selector
                return self._widget

            @staticmethod
            def _mock_subject_scenario():
                return SimpleNamespace(subject_id="typed-subject")

            def _mock_subject_progress(self):
                return self._progress

            def _select_itemize_row_ordinal(self, ordinal: int) -> bool:
                selected_ordinals.append(ordinal)
                return True

        class _FakeWidget:
            id = "itemize_inventory_panel"
            scroll_y = 0
            scroll_target_y = 0

            def __init__(self, app: object) -> None:
                self.app = app
                self.focused = False
                self.lines = (
                    "Itemized Inventory",
                    "Items (2)",
                    ">  [c] First Item",
                    "   [c] Second Item",
                )

            def focus(self) -> None:
                self.focused = True

        fake_app = _FakeApp()
        fake_widget = _FakeWidget(fake_app)
        rendered_click_handled = _TextualWorkstationChatApp._handle_focusable_textual_log_click(
            fake_app,
            fake_widget,
            SimpleNamespace(),
        )
        typed_option_handled = _TextualWorkstationChatApp._handle_inventory_option_highlight(
            fake_app,
            "itemize_inventory_panel",
            1,
        )

        self.assertFalse(rendered_click_handled)
        self.assertTrue(typed_option_handled)
        self.assertEqual(selected_ordinals, [1])
        self.assertTrue(fake_widget.focused)

    def test_textual_research_sources_data_table_row_selects_source(self) -> None:
        class _FakeApp:
            def __init__(self) -> None:
                self._inventory_option_sync_suppressed = set()
                self._programmatic_data_table_cursor_event_counts = {}
                self.handled_rows: list[int] = []

            def _select_research_source_row_ordinal_if_needed(self, row_index: int) -> bool:
                self.handled_rows.append(row_index)
                return True

        class _FakeDataTableEvent:
            def __init__(self, cursor_row: int, row_index: int) -> None:
                self.data_table = SimpleNamespace(id="subject_sources_panel", _research_source_row_ordinals={cursor_row: row_index})
                self.cursor_row = cursor_row
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        fake_app = _FakeApp()
        event = _FakeDataTableEvent(7, 5)

        _TextualWorkstationChatApp._handle_data_table_row_event(fake_app, event)

        self.assertEqual(fake_app.handled_rows, [5])
        self.assertTrue(event.stopped)

    def test_textual_draft_programmatic_data_table_row_events_are_ignored(self) -> None:
        class _FakeApp:
            def __init__(self) -> None:
                self._inventory_option_sync_suppressed = set()
                self._programmatic_data_table_cursor_event_counts = {
                    "draft_scope_tree_panel": {7: 2},
                }
                self.handled_rows: list[int] = []

            def _select_draft_row_ordinal_if_needed(self, row_index: int) -> bool:
                self.handled_rows.append(row_index)
                return True

        class _FakeDataTableEvent:
            def __init__(self, cursor_row: int) -> None:
                self.data_table = SimpleNamespace(id="draft_scope_tree_panel")
                self.cursor_row = cursor_row
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        fake_app = _FakeApp()

        first_event = _FakeDataTableEvent(7)
        _TextualWorkstationChatApp._handle_data_table_row_event(fake_app, first_event)
        self.assertEqual(fake_app.handled_rows, [])
        self.assertEqual(fake_app._programmatic_data_table_cursor_event_counts["draft_scope_tree_panel"].get(7), 1)
        self.assertFalse(first_event.stopped)

        second_event = _FakeDataTableEvent(7)
        _TextualWorkstationChatApp._handle_data_table_row_event(fake_app, second_event)
        self.assertEqual(fake_app.handled_rows, [])
        self.assertNotIn("draft_scope_tree_panel", fake_app._programmatic_data_table_cursor_event_counts)
        self.assertFalse(second_event.stopped)

        third_event = _FakeDataTableEvent(7)
        _TextualWorkstationChatApp._handle_data_table_row_event(fake_app, third_event)
        self.assertEqual(fake_app.handled_rows, [7])
        self.assertTrue(third_event.stopped)

    def test_textual_draft_programmatic_switch_events_are_ignored(self) -> None:
        class _FakeApp:
            def __init__(self) -> None:
                self._suppress_switch_events = False
                self._programmatic_switch_change_counts = {
                    _draft_decision_included_switch_id(): {True: 2},
                }
                self.actions: list[tuple[str, str]] = []

            def _consume_programmatic_switch_change(self, switch_id: str, target_value: bool) -> bool:
                return _TextualWorkstationChatApp._consume_programmatic_switch_change(self, switch_id, target_value)

            def _mock_subject_draft_decision_included_spec(self) -> Any:
                return SimpleNamespace(enabled=True, value=False)

            def _apply_mock_subject_action(self, phase: str, action_key: str) -> None:
                self.actions.append((phase, action_key))

        class _FakeSwitchEvent:
            def __init__(self, value: bool) -> None:
                self.switch = SimpleNamespace(id=_draft_decision_included_switch_id())
                self.value = value

        fake_app = _FakeApp()

        _TextualWorkstationChatApp.on_switch_changed(fake_app, _FakeSwitchEvent(True))
        self.assertEqual(fake_app.actions, [])
        self.assertEqual(
            fake_app._programmatic_switch_change_counts[_draft_decision_included_switch_id()].get(True),
            1,
        )

        _TextualWorkstationChatApp.on_switch_changed(fake_app, _FakeSwitchEvent(True))
        self.assertEqual(fake_app.actions, [])
        self.assertNotIn(_draft_decision_included_switch_id(), fake_app._programmatic_switch_change_counts)

        _TextualWorkstationChatApp.on_switch_changed(fake_app, _FakeSwitchEvent(True))
        self.assertEqual(
            fake_app.actions,
            [("draft", "toggle_selected_draft_review_item_in_decision_frame")],
        )

    def test_textual_draft_info_button_toggles_separate_help_panel(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                app._set_active_tab("draft_tab")
                await pilot.pause()
                self.assertFalse(app.query_one("#detached_pane_shell").display)
                self.assertTrue(app.query_one("#root_tabs").display)
                tab_bar = app.query_one("#tab_bar")
                root_tabs = app.query_one("#root_tabs")
                tab_bar_bottom = int(getattr(tab_bar.region, "y", 0) or 0) + int(getattr(tab_bar.region, "height", 0) or 0)
                self.assertGreaterEqual(int(getattr(root_tabs.region, "y", 0) or 0), tab_bar_bottom)
                self.assertGreater(app.query_one("#draft_scope_tree_panel_info_button").region.width, 0)
                self.assertGreater(app.query_one("#draft_scope_tree_panel_info_button").region.height, 0)

                app.query_one("#draft_scope_tree_panel_info_button").press()
                await pilot.pause()

                self.assertTrue(app.query_one("#detached_pane_shell").display)
                self.assertFalse(app.query_one("#root_tabs").display)
                self.assertTrue(app.query_one("#tab_bar").display)
                self.assertGreater(app.query_one("#tab_button_draft_tab").region.width, 0)
                self.assertGreater(app.query_one("#tab_button_review_tab").region.width, 0)
                detached = app.query_one("#detached_pane_shell")
                self.assertGreaterEqual(int(getattr(detached.region, "y", 0) or 0), tab_bar_bottom)
                info_title = str(app.query_one("#detached_pane_title").render())
                info_text = "\n".join(str(line) for line in app.query_one("#detached_pane_panel").lines)
                self.assertIn("Help", info_title)
                self.assertIn("Draft Item Inventory", info_text)
                self.assertIn("without wrapping", info_text)

                app.query_one("#detached_pane_info_button").press()
                await pilot.pause()
                self.assertFalse(app.query_one("#detached_pane_shell").display)
                self.assertTrue(app.query_one("#root_tabs").display)

        asyncio.run(_exercise())

    def test_textual_itemize_info_button_opens_detached_help_pane(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                app._set_active_tab("itemize_tab")
                await pilot.pause()
                tab_bar = app.query_one("#tab_bar")
                root_tabs = app.query_one("#root_tabs")
                tab_bar_bottom = int(getattr(tab_bar.region, "y", 0) or 0) + int(getattr(tab_bar.region, "height", 0) or 0)
                self.assertGreaterEqual(int(getattr(root_tabs.region, "y", 0) or 0), tab_bar_bottom)
                self.assertGreater(app.query_one("#itemize_inventory_panel_info_button").region.width, 0)
                self.assertGreater(app.query_one("#itemize_inventory_panel_info_button").region.height, 0)

                app.query_one("#itemize_inventory_panel_info_button").press()
                await pilot.pause()

                self.assertTrue(app.query_one("#detached_pane_shell").display)
                self.assertFalse(app.query_one("#root_tabs").display)
                self.assertTrue(app.query_one("#tab_bar").display)
                self.assertGreater(app.query_one("#tab_button_itemize_tab").region.width, 0)
                self.assertGreater(app.query_one("#tab_button_draft_tab").region.width, 0)
                detached = app.query_one("#detached_pane_shell")
                self.assertGreaterEqual(int(getattr(detached.region, "y", 0) or 0), tab_bar_bottom)
                info_title = str(app.query_one("#detached_pane_title").render())
                info_text = "\n".join(str(line) for line in app.query_one("#detached_pane_panel").lines)
                self.assertIn("Help", info_title)
                self.assertIn("Item Inventory", info_text)
                self.assertIn("select it directly", info_text)

                app.query_one("#detached_pane_dismiss_button").press()
                await pilot.pause()

                self.assertFalse(app.query_one("#detached_pane_shell").display)
                self.assertTrue(app.query_one("#root_tabs").display)

        asyncio.run(_exercise())

    def test_textual_draft_tab_bdd_supports_workspace_selection_and_reordering(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        subject_id = "draft-ui-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Draft UI Notes",
            source_ref="notes/draft-ui.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Draft UI Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the draft ui demo subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Draft UI Demo",
                aliases=("Draft UI Demo",),
                subject_family="Governance",
                summary="Draft workspace ui demo subject.",
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
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        scenario = default_subject_scenarios(self.root)[0]
        progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        beta_item = next(
            item
            for item in list_itemized_subject_items(self.root, subject_id)
            if item.canonical_label == "Beta" and item.item_kind == "entity"
        )
        progress.itemize_selected_item_id = beta_item.itemized_item_id
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        persist_subject_progress(self.root, subject_id, progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_draft_tab")
                await pilot.pause()

                await pilot.click("#draft_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "draft_scope_tree_panel")

                app.action_toggle_maximized_pane()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "draft_scope_tree_panel")
                self.assertFalse(app.query_one("#draft_gate_bar").display)
                self.assertFalse(app.query_one("#draft_actions_panel").display)
                self.assertEqual(len(app.query("#draft_status_panel")), 0)
                self.assertTrue(app.query_one("#draft_scope_tree_wrapper").display)
                self.assertFalse(app.query_one("#draft_scope_detail_wrapper").display)
                self.assertFalse(app.query_one("#draft_result_panel").display)
                await pilot.pause()

                before_positions = {
                    item.source_itemized_item_id: index
                    for index, item in enumerate(list_review_items(self.root, subject_id))
                }
                await pilot.press("shift+up")
                await pilot.pause()
                after_positions = {
                    item.source_itemized_item_id: index
                    for index, item in enumerate(list_review_items(self.root, subject_id))
                }
                result_text = _table_text(app.query_one("#draft_scope_tree_panel"))
                current_step = str(app.query_one("#subject_draft_review_gate_summary").render())

                self.assertLess(after_positions[beta_item.itemized_item_id], before_positions[beta_item.itemized_item_id])
                self.assertIn("Beta", result_text)
                self.assertIn("Last Action: Draft item moved earlier.", current_step)

                app.action_toggle_maximized_pane()
                await pilot.pause()
                self.assertIsNone(app._maximized_pane_id)
                self.assertTrue(app.query_one("#draft_gate_bar").display)
                self.assertTrue(app.query_one("#draft_actions_panel").display)
                self.assertEqual(len(app.query("#draft_status_panel")), 0)
                self.assertTrue(app.query_one("#draft_scope_tree_wrapper").display)
                self.assertTrue(app.query_one("#draft_scope_detail_wrapper").display)
                self.assertFalse(app.query_one("#draft_result_panel").display)

        asyncio.run(_exercise())

    def test_textual_itemize_tab_bdd_supports_navigation_hold_and_promote(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="itemize-ui-demo",
            title="Controls Notes",
            source_ref="notes/controls.md",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Controls Notes\n\n"
                "## Alpha\nAlpha matters.\n\n"
                "## Beta\nBeta matters.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id="itemize-ui-demo",
            source_kind="markdown",
            rationale="Admit itemize ui demo.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="itemize-ui-demo",
                canonical_title="Itemize UI Demo",
                aliases=("Itemize UI Demo",),
                subject_family="Governance",
                summary="Itemize ui demo subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="itemize-ui-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="itemize-ui-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="itemize-ui-demo",
                            unit_kind="definition",
                            canonical_title="Beta",
                        ),
                        subject_id="itemize-ui-demo",
                        unit_kind="definition",
                        canonical_title="Beta",
                        statement="Beta matters.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        materialize_itemization_session(self.root, "itemize-ui-demo")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(root=self.root, model=None, max_tool_rounds=2)
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_itemize_tab")
                await pilot.pause()

                inventory_panel = app.query_one("#itemize_inventory_panel")
                self.assertIsInstance(inventory_panel, _FocusableTextualOptionList)
                inventory_panel.focus()
                await pilot.pause()
                first_selected = str(app._mock_subject_progress().itemize_selected_item_id)

                await pilot.press("down")
                await pilot.pause()
                second_selected = str(app._mock_subject_progress().itemize_selected_item_id)

                await pilot.press("h")
                await pilot.pause()
                held_ids = tuple(app._mock_subject_progress().itemize_held_item_ids)
                app._apply_mock_subject_action("itemize", "promote_selected_itemized_item")
                await pilot.pause()

                promoted_item = next(
                    item
                    for item in list_itemized_subject_items(self.root, "itemize-ui-demo")
                    if item.itemized_item_id == str(app._mock_subject_progress().itemize_selected_item_id)
                )

                self.assertNotEqual(first_selected, second_selected)
                self.assertEqual(len(held_ids), 1)
                self.assertEqual(promoted_item.status, "promoted")

        asyncio.run(_exercise())

    def test_textual_research_tab_bdd_supports_selecting_and_approving_subject_imports(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        def _persist_subject(subject_id: str, title: str, statement: str) -> None:
            source = new_learning_source(
                subject_id=subject_id,
                title=f"{title} Notes",
                source_ref=f"notes/{subject_id}.md",
            )
            persist_learning_source(self.root, source, source_text=f"# {title}\n\n{statement}\n")
            delta = new_learning_delta(
                subject_id=subject_id,
                source_kind="markdown",
                rationale=f"Admit {title}.",
            )
            persist_learning_delta(self.root, delta)
            unit = LearningUnit(
                unit_id=stable_learning_unit_id(
                    subject_id=subject_id,
                    unit_kind="definition",
                    canonical_title=title,
                ),
                subject_id=subject_id,
                unit_kind="definition",
                canonical_title=title,
                statement=statement,
                provenance_refs=(source.source_id,),
                status="admitted",
            )
            persist_learning_context(
                self.root,
                LearningContext(
                    subject_id=subject_id,
                    canonical_title=title,
                    aliases=(title,),
                    subject_family="Physics / Imports",
                    summary=f"Maintained subject for {title}.",
                    units=(unit,),
                    linked_source_ids=(source.source_id,),
                    applied_delta_ids=(delta.delta_id,),
                    governance_status="active",
                ),
            )

        _persist_subject(
            "import-source-demo",
            "Import Source Demo",
            "Grouped counting is reusable support.",
        )
        _persist_subject(
            "target-subject-demo",
            "Target Subject Demo",
            "The target subject combines prior support.",
        )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()

                root_tabs = app.query_one("#root_tabs")
                self.assertIn("Current Subject: Import Source Demo", str(getattr(root_tabs, "border_title", "")))

                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                current_step_action_one = app.query_one("#subject_research_review_gate_action_1_button")
                current_step_action_two = app.query_one("#subject_research_review_gate_action_2_button")
                current_step_action_three = app.query_one("#subject_research_review_gate_action_3_button")
                self.assertEqual(str(getattr(current_step_action_one, "label", "")), "Check Maintained Files")
                self.assertEqual(str(getattr(current_step_action_two, "label", "")), "Select As Import Source")
                self.assertEqual(str(getattr(current_step_action_three, "label", "")), "Generate Itemization")

                await pilot.click("#subject_research_review_gate_action_2_button")
                await pilot.pause()
                current_step = str(app.query_one("#subject_research_review_gate_summary").render())
                target_panel_text = _table_text(app.query_one("#subject_target_panel"))
                self.assertFalse(app.query_one("#subject_target_panel_shell").display)
                self.assertIn("Last Action: Import source selected.", current_step)
                self.assertIn("Selected Import Source", collapse_ws(target_panel_text))
                self.assertIn("Import Source Demo", collapse_ws(target_panel_text))

                await pilot.click("#subject_next_button")
                await pilot.pause()
                root_tabs = app.query_one("#root_tabs")
                self.assertIn("Current Subject: Target Subject Demo", str(getattr(root_tabs, "border_title", "")))

                target_primary_action = app.query_one("#subject_research_review_gate_action_1_button")
                if str(getattr(target_primary_action, "label", "")) == "Activate Subject":
                    target_primary_action.press()
                    await pilot.pause()

                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                current_step_summary = str(app.query_one("#subject_research_review_gate_summary").render())
                current_step_action_one = app.query_one("#subject_research_review_gate_action_1_button")
                current_step_action_two = app.query_one("#subject_research_review_gate_action_2_button")
                self.assertIn("Create import from the selected source", current_step_summary)
                self.assertEqual(str(getattr(current_step_action_one, "label", "")), "Create Import From Selected Source")
                self.assertEqual(str(getattr(current_step_action_two, "label", "")), "Clear Import Source")

                await pilot.click("#subject_research_review_gate_action_1_button")
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "review_tab")
                review_summary = str(app.query_one("#subject_review_review_gate_summary").render())
                review_action_one = app.query_one("#subject_review_review_gate_action_1_button")
                self.assertIn("Inspect the pending import", review_summary)
                self.assertEqual(str(getattr(review_action_one, "label", "")), "Preview Pending Import")

                await pilot.click("#subject_review_review_gate_action_1_button")
                await pilot.pause()
                self.assertEqual(app._active_tab_id(), "learn_tab")
                gather_summary = str(app.query_one("#subject_research_review_gate_summary").render())
                self.assertIn("Inspect the pending import", gather_summary)
                gather_action_two = await self._wait_for_subject_gate_button_label(
                    pilot,
                    app,
                    phase="research",
                    label="Approve Import",
                    attempts=20,
                )
                self.assertEqual(str(getattr(gather_action_two, "label", "")), "Approve Import")
                stale_research_snapshot = app._subject_projection_backend.get_snapshot(
                    root_path=self.root,
                    subject_id="target-subject-demo",
                    phase="research",
                    progress=app._mock_subject_progress(),
                    **app._subject_phase_projection_kwargs(),
                )
                app._subject_snapshot_cache["research"] = stale_research_snapshot
                gather_action_two.press()
                for _ in range(20):
                    await pilot.pause()
                    gather_summary = str(app.query_one("#subject_research_review_gate_summary").render())
                    if "Last Action: Subject import approved." in gather_summary:
                        break
                self.assertEqual(app._active_tab_id(), "learn_tab")
                self.assertIn("Last Action: Subject import approved.", gather_summary)

                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                root_tabs = app.query_one("#root_tabs")
                self.assertIn("Current Subject: Target Subject Demo", str(getattr(root_tabs, "border_title", "")))
                target_status = _table_text(
                    app.query_one(f"#{_subject_gate_status_table_id('research', 'publication')}")
                )
                self.assertIn("Reasoning Scope | 1 support items from 1", " ".join(target_status.split()))

        asyncio.run(_exercise())

    def test_textual_review_tab_keeps_report_plan_actions_visible_after_aligned_compare(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = default_subject_scenarios(self.root)[0]
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(160, 45)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_learn_tab")
                await pilot.pause()
                app.query_one("#subject_research_review_gate_action_1_button").press()
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                app.query_one("#subject_review_review_gate_action_1_button").press()
                await pilot.pause()

                current_step = str(app.query_one("#subject_review_review_gate_summary").render())
                primary_action = app.query_one("#subject_review_review_gate_action_1_button")
                secondary_action = app.query_one("#subject_review_review_gate_action_2_button")
                tertiary_action = app.query_one("#subject_review_review_gate_action_3_button")
                quaternary_action = app.query_one("#subject_review_review_gate_action_4_button")
                review_gate_panel = app.query_one("#subject_review_review_gate_panel")
                actions_panel = app.query_one("#review_actions_panel")
                more_action = app.query_one("#subject_review_action_1_button")

                self.assertIn("Run the maintained-files check", current_step)
                self.assertEqual(str(getattr(primary_action, "label", "")), "Check Maintained Files")
                self.assertTrue(primary_action.has_class("subject_gate_action_button_phase_nav"))
                self.assertEqual(str(getattr(secondary_action, "label", "")), "")
                self.assertEqual(str(getattr(tertiary_action, "label", "")), "")
                self.assertEqual(str(getattr(quaternary_action, "label", "")), "")
                self.assertTrue(bool(getattr(primary_action, "display", False)))
                self.assertIsNotNone(review_gate_panel)
                self.assertIsNotNone(actions_panel)
                self.assertIsNotNone(more_action)

        asyncio.run(_exercise())

    def test_textual_publication_actions_open_release_packet_and_outputs(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        context = LearningContext(
            subject_id="kinematics-demo",
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
        build_result = materialize_report_publication_from_learning_context(self.root, context, build_epoch_ms=1)
        expected_packet_path = (
            self.root
            / "corpus"
            / "kinematics-demo"
            / "publications"
            / str(build_result["publication_id"])
            / "outputs"
            / str(build_result["build_id"])
        ).resolve()
        expected_report_md = expected_packet_path / "report.md"
        expected_report_pdf = expected_packet_path / "report.pdf"
        opened_paths: list[Path] = []

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch(
                "workstation.ui.textual.chat_ui.desktop_open_path",
                side_effect=lambda path: opened_paths.append(Path(path).resolve()) or True,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_publication_tab")
                    await pilot.pause()
                    action_one = app.query_one("#subject_publication_action_1_button")
                    action_two = app.query_one("#subject_publication_action_2_button")
                    action_three = app.query_one("#subject_publication_action_3_button")
                    action_four = app.query_one("#subject_publication_action_4_button")
                    root_tabs = app.query_one("#root_tabs")
                    gate_bar = app.query_one("#publication_gate_bar")
                    prev_button = app.query_one("#subject_publication_prev_button")
                    next_button = app.query_one("#subject_publication_next_button")
                    self.assertEqual(str(getattr(action_one, "label", "")), "Preview report.pdf")
                    self.assertEqual(str(getattr(action_two, "label", "")), "Open Release Folder")
                    self.assertEqual(str(getattr(action_three, "label", "")), "Preview report.md")
                    self.assertEqual(str(getattr(action_four, "label", "")), "")
                    self.assertIn("Current Subject:", str(getattr(root_tabs, "border_title", "")))
                    self.assertIn("Kinematics Demo", str(getattr(root_tabs, "border_title", "")))
                    self.assertLess(int(getattr(prev_button.region, "y", 0) or 0), int(getattr(gate_bar.region, "y", 0) or 0))
                    self.assertLessEqual(
                        abs(int(getattr(prev_button.region, "y", 0) or 0) - int(getattr(next_button.region, "y", 0) or 0)),
                        1,
                    )
                    self.assertEqual(len(app.query("#subject_publication_last_action_panel")), 0)
                    self.assertLessEqual(
                        abs(int(getattr(action_one.region, "height", 0) or 0) - int(getattr(action_two.region, "height", 0) or 0)),
                        0,
                    )

                    app.query_one("#subject_publication_action_2_button").press()
                    await pilot.pause()
                    app.query_one("#subject_publication_action_1_button").press()
                    await pilot.pause()
                    self.assertLessEqual(
                        abs(int(getattr(action_one.region, "height", 0) or 0) - int(getattr(action_two.region, "height", 0) or 0)),
                        0,
                    )
                    status = str(app.query_one("#publication_status_panel").render())
                    learn_result = app.query_one("#publication_result")
                    self.assertNotIn("Opened report.pdf.", status)
                    self.assertTrue(any("Output Preview [report.pdf]" in str(line) for line in learn_result.lines))

                    app.query_one("#subject_publication_action_3_button").press()
                    await pilot.pause()
                    self.assertIn("Opened report.md.", app._mock_subject_status_text)

        asyncio.run(_exercise())
        self.assertIn(expected_packet_path, opened_paths)
        self.assertTrue(expected_report_md.is_file())
        self.assertTrue(expected_report_pdf.is_file())

    def test_textual_publication_build_report_runs_in_background(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        from workstation.subject.core.subject_workflow import (
            apply_subject_action,
            default_subject_scenarios,
            new_subject_progress,
            persist_subject_progress,
        )

        source = new_learning_source(
            subject_id="kinematics-demo",
            title="Kinematics Notes",
            source_ref="notes/kinematics.md",
        )
        persist_learning_source(self.root, source, source_text="# Kinematics Notes\n\nVelocity is displacement per unit time.\n")
        delta = new_learning_delta(
            subject_id="kinematics-demo",
            source_kind="markdown",
            rationale="Admit the kinematics subject.",
        )
        persist_learning_delta(self.root, delta)
        unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="kinematics-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="kinematics-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="kinematics-demo",
                canonical_title="Kinematics Demo",
                aliases=("Kinematics Demo",),
                subject_family="Physics / Kinematics",
                summary="Maintained subject for introductory kinematics.",
                units=(unit,),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )

        progress = new_subject_progress()
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "kinematics-demo")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="compare_projections")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="refresh_publication_composition")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "kinematics-demo")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="approve_review")
        scenario = next(item for item in default_subject_scenarios(self.root) if item.subject_id == "kinematics-demo")
        apply_subject_action(root_path=self.root, scenario=scenario, progress=progress, action_key="lock_publication")
        persist_subject_progress(self.root, "kinematics-demo", progress)

        thread_start_calls: list[tuple[str, str, str]] = []

        def _capture_background_start(
            _app: object,
            phase: str,
            scenario: object,
            _progress: object,
            action_key: str,
        ) -> None:
            thread_start_calls.append((phase, getattr(scenario, "subject_id", ""), action_key))

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch.object(
                _TextualWorkstationChatApp,
                "_start_subject_action_thread",
                autospec=True,
                side_effect=_capture_background_start,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_review_tab")
                    await pilot.pause()
                    review_gate_action = app.query_one("#subject_review_review_gate_action_1_button")
                    self.assertEqual(str(getattr(review_gate_action, "label", "")), "Build Report")
                    self.assertTrue(review_gate_action.has_class("subject_gate_action_button_phase_nav"))
                    review_gate_action.press()
                    await pilot.pause()
                    self.assertEqual(app._active_tab_id(), "publication_tab")

                    publication_action = app.query_one("#subject_publication_review_gate_action_1_button")
                    self.assertEqual(str(getattr(publication_action, "label", "")), "Build Report")
                    publication_action.press()
                    await pilot.pause()
                    self.assertTrue(thread_start_calls)
                    self.assertTrue(app._state.is_busy())
                    self.assertEqual(thread_start_calls[-1], ("publication", "kinematics-demo", "build_report"))
                    self.assertIn("Building report publication in the background", app._mock_subject_status_text)
                    current_step = str(app.query_one("#subject_publication_review_gate_summary").render())
                    self.assertIn("Do this now: Build the report", current_step)

        asyncio.run(_exercise())

    def test_textual_itemize_suggest_constructs_runs_in_background(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        markdown_path = DST_SOURCE_ROOT / "Regional emergency alerting system.md"
        learn_result = workstation_learn_markdown_action(
            root_path=self.root,
            markdown_path=markdown_path,
            testing_lightweight=True,
        )
        self.assertEqual(learn_result.status, "ok")

        thread_start_calls: list[tuple[str, str, str]] = []

        def _capture_background_start(
            _app: object,
            phase: str,
            scenario: object,
            _progress: object,
            action_key: str,
        ) -> None:
            thread_start_calls.append((phase, getattr(scenario, "subject_id", ""), action_key))

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch.object(
                _TextualWorkstationChatApp,
                "_start_subject_action_thread",
                autospec=True,
                side_effect=_capture_background_start,
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()

                    activate_action = app.query_one("#subject_research_review_gate_action_1_button")
                    self.assertEqual(str(getattr(activate_action, "label", "")), "Activate Subject")
                    activate_action.press()
                    await pilot.pause()

                    maintained_action = app.query_one("#subject_research_review_gate_action_1_button")
                    self.assertEqual(str(getattr(maintained_action, "label", "")), "Check Maintained Files")
                    maintained_action.press()
                    await pilot.pause()
                    await pilot.pause()

                    generate_itemization_nav = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="research",
                        label="Generate Itemization",
                    )
                    self.assertTrue(generate_itemization_nav.has_class("subject_gate_action_button_phase_nav"))
                    generate_itemization_nav.press()
                    await pilot.pause()
                    await pilot.pause()

                    self.assertEqual(app._active_tab_id(), "itemize_tab")
                    generate_itemization = app.query_one("#subject_itemize_review_gate_action_1_button")
                    self.assertEqual(str(getattr(generate_itemization, "label", "")), "Generate Itemization")
                    generate_itemization.press()
                    await pilot.pause()

                    suggest_action = await self._wait_for_subject_gate_button_label(
                        pilot,
                        app,
                        phase="itemize",
                        label="Suggest DST Constructs",
                    )
                    suggest_action.press()
                    await pilot.pause()

                    self.assertTrue(thread_start_calls)
                    self.assertTrue(app._state.is_busy())
                    self.assertEqual(
                        thread_start_calls[-1],
                        ("itemize", "regional-emergency-alerting-system", "suggest_transformation_constructs"),
                    )
                    self.assertIn("Suggesting transformation constructs in the background", app._mock_subject_status_text)
                    current_step = str(app.query_one("#subject_itemize_review_gate_summary").render())
                    self.assertIn("Do this now: Orient the selected item", current_step)

        asyncio.run(_exercise())

    def test_textual_review_scope_tree_supports_keyboard_selection_and_preview(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="composition-demo",
            title="Composition Notes",
            source_ref="notes/composition.md",
        )
        persist_learning_source(self.root, source, source_text="# Composition Notes\n")
        delta = new_learning_delta(
            subject_id="composition-demo",
            source_kind="markdown",
            rationale="Admit composition units.",
        )
        persist_learning_delta(self.root, delta)
        velocity_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="composition-demo",
                unit_kind="definition",
                canonical_title="Velocity",
            ),
            subject_id="composition-demo",
            unit_kind="definition",
            canonical_title="Velocity",
            statement="Velocity is displacement per unit time.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        acceleration_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="composition-demo",
                unit_kind="relation",
                canonical_title="Acceleration",
            ),
            subject_id="composition-demo",
            unit_kind="relation",
            canonical_title="Acceleration",
            statement="Acceleration is the rate of change of velocity.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="composition-demo",
                canonical_title="Composition Demo",
                aliases=("Composition Demo",),
                subject_family="Physics",
                summary="A multi-unit subject for report scope editing.",
                units=(velocity_unit, acceleration_unit),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = default_subject_scenarios(self.root)[0]
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, "composition-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                tree_panel = app.query_one("#review_scope_tree_panel")
                detail_panel = app.query_one("#review_scope_detail_panel")
                workbench = app.query_one("#review_scope_workbench")
                review_result = app.query_one("#review_result")
                self.assertIsInstance(tree_panel, _FocusableTextualTree)
                self.assertFalse(bool(getattr(detail_panel, "show_header", True)))
                self.assertEqual(str(getattr(detail_panel, "cursor_type", "")), "none")
                await pilot.click("#review_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "review_scope_tree_panel")
                self.assertGreater(int(getattr(workbench.region, "height", 0) or 0), 20)
                self.assertGreater(
                    int(getattr(workbench.region, "height", 0) or 0),
                    int(getattr(review_result.region, "height", 0) or 0),
                )

                def _tree_text() -> str:
                    return "\n".join(
                        str(getattr(node, "label", "") or "")
                        for heading in tree_panel.root.children
                        for node in (heading, *heading.children)
                    )

                initial_tree_text = _tree_text()
                initial_detail_text = _table_text(detail_panel)
                self.assertIn("> [x] Velocity", initial_tree_text)
                self.assertIn("[x] Acceleration", initial_tree_text)
                self.assertIn("Velocity", initial_detail_text)

                await pilot.press("down")
                await pilot.pause()
                moved_tree_text = _tree_text()
                moved_detail_text = _table_text(detail_panel)
                self.assertIn("> [x] Acceleration", moved_tree_text)
                self.assertNotIn("> [x] Velocity", moved_tree_text)
                self.assertIn("Acceleration", str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""))
                self.assertIn("Acceleration", moved_detail_text)

                await pilot.press("x")
                await pilot.pause()
                toggled_tree_text = _tree_text()
                review_result_text = "\n".join(str(line) for line in app.query_one("#review_result").lines)
                self.assertIn("  [-] Velocity", toggled_tree_text)
                self.assertIn("> [ ] Acceleration", toggled_tree_text)
                self.assertIn("latest unit action: excluded Acceleration", review_result_text)

                await pilot.click("#review_scope_detail_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "review_scope_detail_panel")
                await pilot.press("x")
                await pilot.pause()
                retoggled_tree_text = _tree_text()
                self.assertIn("> [x] Acceleration", retoggled_tree_text)

                await pilot.press("enter")
                await pilot.pause()
                review_result_text = "\n".join(str(line) for line in app.query_one("#review_result").lines)
                self.assertIn("Report Scope Preview", review_result_text)
                self.assertIn("Acceleration", review_result_text)

        asyncio.run(_exercise())

    def test_textual_review_scope_tree_select_node_keeps_cursor_on_child(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="review-tree-select-demo",
            title="Review Tree Select Notes",
            source_ref="notes/review-tree-select.md",
        )
        persist_learning_source(self.root, source, source_text="# Review Tree Select Notes\n")
        delta = new_learning_delta(
            subject_id="review-tree-select-demo",
            source_kind="markdown",
            rationale="Admit review-tree-select-demo units.",
        )
        persist_learning_delta(self.root, delta)
        actors_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="review-tree-select-demo",
                unit_kind="definition",
                canonical_title="Actors",
            ),
            subject_id="review-tree-select-demo",
            unit_kind="definition",
            canonical_title="Actors",
            statement="Actors participate in the system.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        boundaries_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="review-tree-select-demo",
                unit_kind="definition",
                canonical_title="Boundaries",
            ),
            subject_id="review-tree-select-demo",
            unit_kind="definition",
            canonical_title="Boundaries",
            statement="Boundaries constrain coordination.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="review-tree-select-demo",
                canonical_title="Review Tree Select Demo",
                aliases=("Review Tree Select Demo",),
                subject_family="Physics",
                summary="A maintained subject for Review tree selection behavior.",
                units=(actors_unit, boundaries_unit),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = default_subject_scenarios(self.root)[0]
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, "review-tree-select-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                tree_panel = app.query_one("#review_scope_tree_panel")
                detail_panel = app.query_one("#review_scope_detail_panel")
                headings = tuple(tree_panel.root.children)
                self.assertTrue(headings)
                selectable_children = tuple(headings[0].children)
                self.assertGreaterEqual(len(selectable_children), 2)

                await pilot.click("#review_scope_tree_panel")
                await pilot.pause()
                tree_panel.select_node(selectable_children[1])
                await pilot.pause()

                self.assertIn(
                    "Boundaries",
                    str(getattr(getattr(tree_panel, "cursor_node", None), "label", "") or ""),
                )
                detail_text = _table_text(detail_panel)
                self.assertIn("Boundaries", detail_text)

        asyncio.run(_exercise())

    def test_textual_f8_maximizes_focused_review_scope_pane_and_restores_it(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="maximize-demo",
            title="Maximize Notes",
            source_ref="notes/maximize.md",
        )
        persist_learning_source(self.root, source, source_text="# Maximize Notes\n")
        delta = new_learning_delta(
            subject_id="maximize-demo",
            source_kind="markdown",
            rationale="Admit maximize-demo units.",
        )
        persist_learning_delta(self.root, delta)
        alpha_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="maximize-demo",
                unit_kind="definition",
                canonical_title="Alpha",
            ),
            subject_id="maximize-demo",
            unit_kind="definition",
            canonical_title="Alpha",
            statement="Alpha stays in the report scope.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        beta_unit = LearningUnit(
            unit_id=stable_learning_unit_id(
                subject_id="maximize-demo",
                unit_kind="relation",
                canonical_title="Beta",
            ),
            subject_id="maximize-demo",
            unit_kind="relation",
            canonical_title="Beta",
            statement="Beta gives the review pane more than one selectable item.",
            provenance_refs=(source.source_id,),
            status="admitted",
        )
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="maximize-demo",
                canonical_title="Maximize Demo",
                aliases=("Maximize Demo",),
                subject_family="Physics",
                summary="A maintained subject for pane maximize behavior.",
                units=(alpha_unit, beta_unit),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = default_subject_scenarios(self.root)[0]
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, "maximize-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                await pilot.click("#review_scope_tree_panel")
                await pilot.pause()
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "review_scope_tree_panel")
                self.assertFalse(app.query_one("#review_result_panel").display)

                await pilot.click(f"#{_textual_pane_toggle_button_id('review_scope_tree_panel')}")
                await pilot.pause()
                self.assertTrue(app.query_one("#detached_pane_shell").display)
                self.assertFalse(app.query_one("#root_tabs").display)
                self.assertTrue(app.query_one("#tab_bar").display)
                self.assertEqual(str(app._detached_pane_spec.get("pane_id", "") or ""), "review_scope_tree_panel")
                detached_tree = app.query_one("#detached_review_scope_tree_panel")
                self.assertTrue(detached_tree.display)
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "detached_review_scope_tree_panel")
                detached_tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in detached_tree.root.children
                    for node in (heading, *heading.children)
                )
                self.assertIn("Alpha", detached_tree_text)
                self.assertIn("Beta", detached_tree_text)

                await pilot.press("down")
                await pilot.pause()
                self.assertIn(
                    "Beta",
                    str(getattr(getattr(detached_tree, "cursor_node", None), "label", "") or ""),
                )

                await pilot.press("x")
                await pilot.pause()
                detached_tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in detached_tree.root.children
                    for node in (heading, *heading.children)
                )
                self.assertIn("> [ ] Beta", detached_tree_text)
                self.assertTrue(app.query_one("#detached_pane_shell").display)
                self.assertFalse(app.query_one("#root_tabs").display)
                self.assertEqual(str(getattr(app.focused, "id", "") or ""), "detached_review_scope_tree_panel")

                app.query_one("#detached_pane_dismiss_button").press()
                await pilot.pause()
                self.assertFalse(app.query_one("#detached_pane_shell").display)
                self.assertTrue(app.query_one("#root_tabs").display)
                self.assertTrue(app.query_one("#review_gate_bar").display)
                self.assertTrue(app.query_one("#review_actions_panel").display)
                self.assertTrue(app.query_one("#review_status_panel").display)
                self.assertTrue(app.query_one("#review_scope_workbench").display)
                self.assertTrue(app.query_one("#review_scope_tree_wrapper").display)
                self.assertTrue(app.query_one("#review_scope_detail_wrapper").display)
                self.assertFalse(app.query_one("#review_result_panel").display)

                app.query_one("#subject_review_journal_button").press()
                await pilot.pause()
                self.assertEqual(app._maximized_pane_id, "review_result")
                self.assertTrue(app.query_one("#review_result_panel").display)

        asyncio.run(_exercise())

    def test_textual_review_scope_tree_supports_hold_move_and_release_shortcuts(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        source = new_learning_source(
            subject_id="composition-reorder-demo",
            title="Composition Reorder Notes",
            source_ref="notes/composition-reorder.md",
        )
        persist_learning_source(self.root, source, source_text="# Composition Reorder Notes\n")
        delta = new_learning_delta(
            subject_id="composition-reorder-demo",
            source_kind="markdown",
            rationale="Admit reorderable report-scope units.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id="composition-reorder-demo",
                canonical_title="Composition Reorder Demo",
                aliases=("Composition Reorder Demo",),
                subject_family="Physics / Ordering",
                summary="A multi-unit subject for staged report-scope reordering.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="composition-reorder-demo",
                            unit_kind="definition",
                            canonical_title="Alpha",
                        ),
                        subject_id="composition-reorder-demo",
                        unit_kind="definition",
                        canonical_title="Alpha",
                        statement="Alpha definition.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="composition-reorder-demo",
                            unit_kind="relation",
                            canonical_title="Beta",
                        ),
                        subject_id="composition-reorder-demo",
                        unit_kind="relation",
                        canonical_title="Beta",
                        statement="Beta relation.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="composition-reorder-demo",
                            unit_kind="ability",
                            canonical_title="Gamma",
                        ),
                        subject_id="composition-reorder-demo",
                        unit_kind="ability",
                        canonical_title="Gamma",
                        statement="Gamma ability.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(
                            subject_id="composition-reorder-demo",
                            unit_kind="misconception",
                            canonical_title="Delta",
                        ),
                        subject_id="composition-reorder-demo",
                        unit_kind="misconception",
                        canonical_title="Delta",
                        statement="Delta misconception.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        seeded_scenario = default_subject_scenarios(self.root)[0]
        seeded_progress = new_subject_progress()
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="open_context")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="generate_itemization")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_review_composition")
        apply_subject_action(root_path=self.root, scenario=seeded_scenario, progress=seeded_progress, action_key="refresh_publication_composition")
        persist_subject_progress(self.root, "composition-reorder-demo", seeded_progress)

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            async with app.run_test(size=(180, 60)) as pilot:
                await pilot.pause()
                await pilot.click("#tab_button_review_tab")
                await pilot.pause()

                tree_panel = app.query_one("#review_scope_tree_panel")
                self.assertIsInstance(tree_panel, _FocusableTextualTree)
                await pilot.click("#review_scope_tree_panel")
                await pilot.pause()

                await pilot.press("down")
                await pilot.pause()
                await pilot.press("h")
                await pilot.pause()
                await pilot.press("down")
                await pilot.pause()
                await pilot.press("h")
                await pilot.pause()
                await pilot.press("up")
                await pilot.pause()

                preview_tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in tree_panel.root.children
                    for node in (heading, *heading.children)
                )
                self.assertIn("h [x] Beta", preview_tree_text)
                self.assertIn("h [x] Delta", preview_tree_text)

                await pilot.press("r")
                await pilot.pause()

                released_tree_text = "\n".join(
                    str(getattr(node, "label", "") or "")
                    for heading in tree_panel.root.children
                    for node in (heading, *heading.children)
                )
                review_result_text = "\n".join(str(line) for line in app.query_one("#review_result").lines)
                self.assertNotIn("h [x] Beta", released_tree_text)
                self.assertIn("Report Scope Reorder Released", review_result_text)
                self.assertIn("released held items without moving: 2", review_result_text)

        asyncio.run(_exercise())

    def test_textual_log_wrap_width_falls_back_to_app_width_when_widget_unset(self) -> None:
        if _TextualWorkstationChatApp is None:
            self.skipTest("textual is not installed")

        class _Size:
            def __init__(self, width: int) -> None:
                self.width = width

        class _Widget:
            def __init__(self, width: int) -> None:
                self.size = _Size(width)

        class _AppStub:
            _textual_log_wrap_width = _TextualWorkstationChatApp._textual_log_wrap_width

            def __init__(self) -> None:
                self.size = _Size(120)
                self.screen = type("_Screen", (), {"size": _Size(100)})()

        app = _AppStub()
        self.assertEqual(app._textual_log_wrap_width(_Widget(0)), 110)
        self.assertEqual(app._textual_log_wrap_width(_Widget(60)), 58)

    def test_scroll_window_linewise_clamps_at_zero(self) -> None:
        class _WindowStub:
            vertical_scroll = 0

        window = _WindowStub()
        _scroll_window_linewise(window, 3)
        self.assertEqual(window.vertical_scroll, 3)
        _scroll_window_linewise(window, -10)
        self.assertEqual(window.vertical_scroll, 0)

    def test_window_scroll_cursor_position_tracks_scroll_offset(self) -> None:
        class _WindowStub:
            vertical_scroll = 2

        point = _window_scroll_cursor_position(_WindowStub(), "one\ntwo\nthree\nfour")
        if point is None:
            self.assertIsNone(point)
            return
        self.assertEqual((point.x, point.y), (0, 2))

    def test_scroll_window_to_end_moves_to_last_line(self) -> None:
        class _WindowStub:
            vertical_scroll = 0

        window = _WindowStub()
        _scroll_window_to_end(window, "one\ntwo\nthree\nfour")
        self.assertEqual(window.vertical_scroll, 3)

    def test_textual_scroll_to_end_uses_forced_vertical_scroll(self) -> None:
        class _WidgetStub:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def scroll_end(self, **kwargs: object) -> None:
                self.calls.append(dict(kwargs))

        widget = _WidgetStub()
        _textual_scroll_to_end(widget)
        self.assertEqual(
            widget.calls,
            [{"animate": False, "force": True, "immediate": True, "x_axis": False}],
        )

    def test_textual_scroll_line_into_view_moves_down_when_selection_falls_below_viewport(self) -> None:
        class _RegionStub:
            height = 4

        class _WidgetStub:
            def __init__(self) -> None:
                self.scroll_y = 0.0
                self.scroll_target_y = 0.0
                self.max_scroll_y = 20.0
                self.scrollable_content_region = _RegionStub()
                self.calls: list[dict[str, object]] = []

            def scroll_to(self, **kwargs: object) -> None:
                self.calls.append(dict(kwargs))

        widget = _WidgetStub()
        _textual_scroll_line_into_view(widget, 6)
        self.assertEqual(widget.scroll_y, 5.0)
        self.assertEqual(widget.scroll_target_y, 5.0)
        self.assertEqual(
            widget.calls,
            [{"y": 5.0, "animate": False, "force": True, "immediate": True}],
        )


class FocusableTextualLogTests(unittest.TestCase):
    def test_focusable_textual_log_routes_draft_workspace_navigation_and_reorder_keys(self) -> None:
        class _FakeEvent:
            def __init__(self, key: str) -> None:
                self.key = key
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        for widget_id in ("draft_scope_tree_panel", "draft_scope_detail_panel", "draft_result"):
            move_calls: list[int] = []
            reorder_calls: list[int] = []
            fake_app = SimpleNamespace(
                _move_draft_review_cursor=lambda delta, calls=move_calls: calls.append(delta) or True,
                _move_selected_draft_review_item=lambda delta, calls=reorder_calls: calls.append(delta) or True,
            )
            fake_log = SimpleNamespace(id=widget_id, app=fake_app)

            up_event = _FakeEvent("up")
            _FocusableTextualLog.on_key(fake_log, up_event)
            self.assertEqual(move_calls, [-1], msg=widget_id)
            self.assertTrue(up_event.stopped, msg=widget_id)

            down_event = _FakeEvent("down")
            _FocusableTextualLog.on_key(fake_log, down_event)
            self.assertEqual(move_calls, [-1, 1], msg=widget_id)
            self.assertTrue(down_event.stopped, msg=widget_id)

            reorder_up_event = _FakeEvent("shift+up")
            _FocusableTextualLog.on_key(fake_log, reorder_up_event)
            self.assertEqual(reorder_calls, [-1], msg=widget_id)
            self.assertTrue(reorder_up_event.stopped, msg=widget_id)

            reorder_down_event = _FakeEvent("shift+down")
            _FocusableTextualLog.on_key(fake_log, reorder_down_event)
            self.assertEqual(reorder_calls, [-1, 1], msg=widget_id)
            self.assertTrue(reorder_down_event.stopped, msg=widget_id)

    def test_focusable_textual_data_table_routes_draft_workspace_navigation_keys(self) -> None:
        class _FakeEvent:
            def __init__(self, key: str) -> None:
                self.key = key
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        move_calls: list[int] = []
        reorder_calls: list[int] = []
        decision_toggle_calls: list[str] = []
        fake_app = SimpleNamespace(
            _move_draft_review_cursor=lambda delta, calls=move_calls: calls.append(delta) or True,
            _move_selected_draft_review_item=lambda delta, calls=reorder_calls: calls.append(delta) or True,
            _toggle_draft_decision_included=lambda calls=decision_toggle_calls: calls.append("toggle") or True,
        )
        fake_table = SimpleNamespace(id="draft_model_main_panel", app=fake_app)

        up_event = _FakeEvent("up")
        _FocusableTextualDataTable.on_key(fake_table, up_event)
        self.assertEqual(move_calls, [-1])
        self.assertTrue(up_event.stopped)

        down_event = _FakeEvent("down")
        _FocusableTextualDataTable.on_key(fake_table, down_event)
        self.assertEqual(move_calls, [-1, 1])
        self.assertTrue(down_event.stopped)

        reorder_up_event = _FakeEvent("shift+up")
        _FocusableTextualDataTable.on_key(fake_table, reorder_up_event)
        self.assertEqual(reorder_calls, [-1])
        self.assertTrue(reorder_up_event.stopped)

        reorder_down_event = _FakeEvent("shift+down")
        _FocusableTextualDataTable.on_key(fake_table, reorder_down_event)
        self.assertEqual(reorder_calls, [-1, 1])
        self.assertTrue(reorder_down_event.stopped)

        decision_toggle_event = _FakeEvent("d")
        _FocusableTextualDataTable.on_key(fake_table, decision_toggle_event)
        self.assertEqual(decision_toggle_calls, ["toggle"])
        self.assertTrue(decision_toggle_event.stopped)

    def test_focusable_textual_option_list_routes_draft_decision_toggle_key(self) -> None:
        toggle_calls: list[str] = []
        fake_app = SimpleNamespace(
            _toggle_draft_decision_included=lambda calls=toggle_calls: calls.append("toggle") or True,
        )
        fake_list = SimpleNamespace(id="draft_scope_tree_panel", app=fake_app)

        _FocusableTextualOptionList.action_toggle_inventory_decision(fake_list)

        self.assertEqual(toggle_calls, ["toggle"])

    def test_focusable_textual_log_routes_review_scope_hold_release_and_preview_move_keys(self) -> None:
        hold_calls: list[str] = []
        release_calls: list[str] = []
        preview_move_calls: list[int] = []

        class _FakeEvent:
            def __init__(self, key: str) -> None:
                self.key = key
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        fake_app = SimpleNamespace(
            _hold_review_scope_item=lambda: hold_calls.append("hold") or True,
            _release_review_scope_items=lambda: release_calls.append("release") or True,
            _move_review_scope_cursor=lambda _delta: False,
            _preview_move_review_scope_items=lambda delta: preview_move_calls.append(delta) or True,
            _toggle_review_scope_item=lambda: False,
            _preview_review_scope_item=lambda: False,
        )
        fake_log = SimpleNamespace(id="review_scope_detail_panel", app=fake_app)

        hold_event = _FakeEvent("h")
        _FocusableTextualLog.on_key(fake_log, hold_event)
        self.assertEqual(hold_calls, ["hold"])
        self.assertTrue(hold_event.stopped)

        release_event = _FakeEvent("r")
        _FocusableTextualLog.on_key(fake_log, release_event)
        self.assertEqual(release_calls, ["release"])
        self.assertTrue(release_event.stopped)

        preview_up_event = _FakeEvent("shift+up")
        _FocusableTextualLog.on_key(fake_log, preview_up_event)
        self.assertEqual(preview_move_calls, [-1])
        self.assertTrue(preview_up_event.stopped)

        preview_down_event = _FakeEvent("shift+down")
        _FocusableTextualLog.on_key(fake_log, preview_down_event)
        self.assertEqual(preview_move_calls, [-1, 1])
        self.assertTrue(preview_down_event.stopped)

        preview_up_fallback_event = _FakeEvent("k")
        _FocusableTextualLog.on_key(fake_log, preview_up_fallback_event)
        self.assertEqual(preview_move_calls, [-1, 1, -1])
        self.assertTrue(preview_up_fallback_event.stopped)

        preview_down_fallback_event = _FakeEvent("j")
        _FocusableTextualLog.on_key(fake_log, preview_down_fallback_event)
        self.assertEqual(preview_move_calls, [-1, 1, -1, 1])
        self.assertTrue(preview_down_fallback_event.stopped)

    def test_focusable_textual_log_routes_itemize_navigation_hold_and_preview_keys(self) -> None:
        move_calls: list[int] = []
        hold_calls: list[str] = []
        preview_calls: list[str] = []

        class _FakeEvent:
            def __init__(self, key: str) -> None:
                self.key = key
                self.stopped = False

            def stop(self) -> None:
                self.stopped = True

        fake_app = SimpleNamespace(
            _move_itemize_cursor=lambda delta: move_calls.append(delta) or True,
            _hold_itemize_item=lambda: hold_calls.append("hold") or True,
            _preview_itemize_item=lambda: preview_calls.append("preview") or True,
        )
        fake_log = SimpleNamespace(id="itemize_inventory_panel", app=fake_app)

        up_event = _FakeEvent("up")
        _FocusableTextualLog.on_key(fake_log, up_event)
        self.assertEqual(move_calls, [-1])
        self.assertTrue(up_event.stopped)

        down_event = _FakeEvent("down")
        _FocusableTextualLog.on_key(fake_log, down_event)
        self.assertEqual(move_calls, [-1, 1])
        self.assertTrue(down_event.stopped)

        hold_event = _FakeEvent("h")
        _FocusableTextualLog.on_key(fake_log, hold_event)
        self.assertEqual(hold_calls, ["hold"])
        self.assertTrue(hold_event.stopped)

        preview_event = _FakeEvent("enter")
        _FocusableTextualLog.on_key(fake_log, preview_event)
        self.assertEqual(preview_calls, ["preview"])
        self.assertTrue(preview_event.stopped)


if __name__ == "__main__":
    unittest.main()
