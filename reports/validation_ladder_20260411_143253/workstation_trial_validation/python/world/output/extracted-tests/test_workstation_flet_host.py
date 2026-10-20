# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from blend_workflow import BlendWorkflowBinding, BlendWorkflowPlan, BlendWorkflowRun, BlendWorkflowStep
from blend_workflow_store import persist_blend_workflow_objects
from workstation.layout import workstation_pane_title, workstation_panel_title
from workstation.chat_ui import workstation_chat_apply_prompt_suggestion, workstation_chat_context
from workstation.flet_host import (
    _build_workstation_flet_page,
    _flet_tab_navigation_direction,
    _flet_chat_transcript_list,
    _scroll_flet_chat_transcript_to_end,
    _chat_content,
    build_workstation_flet_page,
    workstation_flet_available,
    workstation_flet_control_for_field,
    workstation_flet_dashboard_spec,
)
from workstation.projection_models import WorkstationActivityEventView
from workstation.session import launch_workstation_session
from workstation.workstation_core import workstation_invoke_skill_action


class WorkstationFletHostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "root"
        self.workspace = Path(self.tempdir.name) / "workspace"
        self.skills_sqlite = Path(self.tempdir.name) / "skills.sqlite3"
        self.workspace.mkdir(parents=True, exist_ok=True)
        launch_workstation_session(
            root_path=self.root,
            workspace_path=self.workspace,
            skills_sqlite_path=self.skills_sqlite,
            initial_task="Test workstation flet host.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_dashboard_spec_projects_core_panels_and_skill_form(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            skill_query="Workstation Repo Search",
        )
        panel_kinds = {panel.panel_kind for panel in spec.panels}
        self.assertIn("chat", panel_kinds)
        self.assertIn("research", panel_kinds)
        self.assertIn("review", panel_kinds)
        self.assertIn("publication", panel_kinds)
        self.assertIn("permission_panel", panel_kinds)
        self.assertIn("activity_feed", panel_kinds)
        self.assertIn("skill_catalog", panel_kinds)
        self.assertIn("skill_form", panel_kinds)
        form_panel = next(panel for panel in spec.panels if panel.panel_kind == "skill_form")
        input_form = form_panel.payload["input_form"]
        self.assertTrue(any(section["title"] == "Location" for section in input_form["sections"]))
        mount_field = next(field for field in input_form["fields"] if field["field_name"] == "mount")
        self.assertEqual(mount_field["section"], "Location")
        self.assertTrue(mount_field["constraints"]["attachment_backed"])

    def test_dashboard_spec_can_include_workflow_panel(self) -> None:
        workflow_plan = BlendWorkflowPlan(
            workflow_id="",
            workflow_kind="skill_compose",
            session_id="ws-1",
            created_at="2026-04-06T00:00:00+00:00",
            root_inputs={"text": "hello"},
            final_output_step="consume",
            steps=(
                BlendWorkflowStep(
                    step_id="emit",
                    operator_kind="skill",
                    operator_name="Emit Text",
                ),
                BlendWorkflowStep(
                    step_id="consume",
                    operator_kind="skill",
                    operator_name="Consume Text",
                    bindings=(
                        BlendWorkflowBinding(
                            {
                                "source_step_id": "emit",
                                "source_path": "/d/text",
                                "target_path": "/a/text",
                                "mapper": {"kind": "identity"},
                            }
                        ),
                    ),
                ),
            ),
            metadata={"target": "skills"},
        )
        workflow_run = BlendWorkflowRun(
            workflow_run_id="",
            workflow_id="",
            plan=workflow_plan,
            status="ok",
            session_id="ws-1",
            started_at="2026-04-06T00:00:01+00:00",
            finished_at="2026-04-06T00:00:02+00:00",
            final_output_step="consume",
            final_output="done",
            final_outputs_by_step={"emit": "hello", "consume": "done"},
            steps=[
                {"step_id": "emit", "status": "ok"},
                {"step_id": "consume", "status": "ok", "answer": "done"},
            ],
            plan_authorities=["read"],
        )
        _persisted_plan, persisted_run, _store = persist_blend_workflow_objects(
            root_path=self.root,
            plan=workflow_plan,
            run=workflow_run,
            session_id="ws-1",
        )
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            workflow_run_id=persisted_run.workflow_run_id,
        )
        workflow_panel = next(panel for panel in spec.panels if panel.panel_kind == "workflow")
        self.assertEqual(workflow_panel.payload["workflow_timeline"]["workflow_run_id"], persisted_run.workflow_run_id)
        self.assertEqual(len(workflow_panel.payload["workflow_timeline"]["entries"]), 2)

    def test_flet_control_builder_selects_control_kind_from_field_projection(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            skill_query="Workstation Repo Search",
        )
        form_panel = next(panel for panel in spec.panels if panel.panel_kind == "skill_form")
        input_form = form_panel.payload["input_form"]
        mount_field = next(field for field in input_form["fields"] if field["field_name"] == "mount")
        path_field = next(field for field in input_form["fields"] if field["field_name"] == "relative_path")
        self.assertTrue(workstation_flet_available())
        self.assertEqual(workstation_flet_control_for_field(mount_field).__class__.__name__, "Dropdown")
        self.assertEqual(workstation_flet_control_for_field(path_field).__class__.__name__, "TextField")

    def test_dashboard_spec_can_merge_supplemental_activity_events(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            supplemental_activity_events=[
                WorkstationActivityEventView(
                    event_kind="blend_step_started",
                    message="Step started: Emit Text",
                    status="started",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                    step_id="emit",
                )
            ],
        )
        activity_panel = next(panel for panel in spec.panels if panel.panel_kind == "activity_feed")
        self.assertTrue(
            any(item.get("message") == "Step started: Emit Text" for item in activity_panel.payload["events"])
        )
        rendered_messages = [str(item.get("rendered_message", "")) for item in activity_panel.payload["events"]]
        self.assertTrue(any("├─ Step started: Emit Text" in item for item in rendered_messages))

    def test_flet_tabs_style_permission_skill_and_activity_titles(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            supplemental_activity_events=[
                WorkstationActivityEventView(
                    event_kind="blend_step_started",
                    message="Step started: Emit Text [in: payload]",
                    status="started",
                    workflow_execution_id="bwf_exec_demo",
                    workflow_id="workflow_demo",
                    step_id="emit",
                    tree_depth=1,
                )
            ],
        )
        permissions_page = _build_page_with_panel_kind(spec, panel_kind="permission_panel")
        activity_page = _build_page_with_panel_kind(spec, panel_kind="activity_feed")
        skills_page = _build_page_with_panel_kind(spec, panel_kind="skill_catalog")
        permissions_panel = _active_panel_content(permissions_page)
        activity_panel = _active_panel_content(activity_page)
        skills_panel = _active_panel_content(skills_page)

        permission_titles = [
            control
            for control in _walk_flet_controls(permissions_panel)
            if control.__class__.__name__ == "Text" and str(getattr(control, "value", "") or "").startswith("ws.")
        ]
        self.assertTrue(permission_titles)
        self.assertTrue(all(getattr(control, "weight", None) for control in permission_titles[:1]))

        skill_titles = [
            control
            for control in _walk_flet_controls(skills_panel)
            if control.__class__.__name__ == "Text" and "Workstation" in str(getattr(control, "value", "") or "")
        ]
        self.assertTrue(skill_titles)
        self.assertTrue(any(getattr(control, "weight", None) for control in skill_titles))

        activity_texts = [
            control
            for control in _walk_flet_controls(activity_panel)
            if control.__class__.__name__ == "Text" and getattr(control, "spans", None)
        ]
        self.assertTrue(activity_texts)
        activity_spans = list(getattr(activity_texts[0], "spans", []) or [])
        self.assertTrue(any("[in: payload]" in str(getattr(span, "text", "") or "") for span in activity_spans))

    def test_build_workstation_flet_page_highlights_current_tab(self) -> None:
        spec = workstation_flet_dashboard_spec(root_path=self.root)
        page_view = build_workstation_flet_page(spec)
        tab_controls = page_view.controls[0].content.controls
        tab_labels = [_button_label(control) for control in tab_controls]
        self.assertGreaterEqual(len(tab_labels), 7)
        self.assertTrue(tab_labels[0].startswith("● 1. Chat"))
        self.assertTrue(tab_labels[1].startswith("  2. Research"))

    def test_flet_tab_navigation_direction_accepts_shift_tab_aliases(self) -> None:
        self.assertEqual(_flet_tab_navigation_direction(key_text="tab", shift=False), 0)
        self.assertEqual(_flet_tab_navigation_direction(key_text="tab", shift=True), 1)
        self.assertEqual(_flet_tab_navigation_direction(key_text="shift+tab", shift=False), 1)
        self.assertEqual(_flet_tab_navigation_direction(key_text="ISO_Left_Tab", shift=False), 1)
        self.assertIsNone(_flet_tab_navigation_direction(key_text="enter", shift=False))

    def test_dashboard_spec_can_project_markdown_feedback_state(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            markdown_selected_path="/tmp/example.md",
            markdown_status_text="Learning and importing: example.md",
            markdown_busy=True,
        )
        research_panel = next(panel for panel in spec.panels if panel.panel_kind == "research")
        self.assertIn("/tmp/example.md", research_panel.payload["status_text"])
        self.assertIn("Learning and importing: example.md", research_panel.payload["status_text"])
        self.assertTrue(research_panel.payload["markdown_busy"])

    def test_dashboard_spec_can_attach_action_results(self) -> None:
        skill_result = workstation_invoke_skill_action(
            root_path=self.root,
            skill_query="Workstation Greeting From Wasm",
            raw_inputs={"payload": "hello"},
        )
        workflow_plan = BlendWorkflowPlan(
            workflow_id="",
            workflow_kind="skill_compose",
            session_id="ws-1",
            created_at="2026-04-06T00:00:00+00:00",
            root_inputs={},
            final_output_step="greet",
            steps=(
                BlendWorkflowStep(
                    step_id="greet",
                    operator_kind="skill",
                    operator_name="Workstation Greeting From Wasm",
                ),
            ),
            metadata={"target": "skills"},
        )
        workflow_run = BlendWorkflowRun(
            workflow_run_id="",
            workflow_id="",
            plan=workflow_plan,
            status="ok",
            session_id="ws-1",
            started_at="2026-04-06T00:00:01+00:00",
            finished_at="2026-04-06T00:00:02+00:00",
            final_output_step="greet",
            final_output={"greeting": "hello from workstation wasm"},
            final_outputs_by_step={"greet": {"greeting": "hello from workstation wasm"}},
            steps=[{"step_id": "greet", "status": "ok"}],
            plan_authorities=["execute"],
        )
        persisted_plan, persisted_run, _store = persist_blend_workflow_objects(
            root_path=self.root,
            plan=workflow_plan,
            run=workflow_run,
            session_id="ws-1",
        )
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            skill_query="Workstation Greeting From Wasm",
            workflow_id=persisted_plan.workflow_id,
            workflow_run_id=persisted_run.workflow_run_id,
            skill_action_result=skill_result.to_dict(),
            workflow_action_result={
                "action_kind": "workflow_run",
                "status": "ok",
                "title": "Workflow Run",
                "message": "Workflow completed",
                "workflow_id": persisted_plan.workflow_id,
                "workflow_run_id": persisted_run.workflow_run_id,
                "payload": {},
            },
        )
        skill_panel = next(panel for panel in spec.panels if panel.panel_kind == "skill_form")
        workflow_panel = next(panel for panel in spec.panels if panel.panel_kind == "workflow")
        self.assertEqual(skill_panel.payload["action_result"]["status"], "ok")
        self.assertEqual(workflow_panel.payload["action_result"]["workflow_run_id"], persisted_run.workflow_run_id)

    def test_build_workstation_flet_page_uses_current_tabs_api(self) -> None:
        spec = workstation_flet_dashboard_spec(root_path=self.root)
        page_view = build_workstation_flet_page(spec)
        self.assertEqual(page_view.__class__.__name__, "View")

    def test_build_workstation_flet_page_renders_action_buttons_for_skill_and_workflow_panels(self) -> None:
        workflow_plan = BlendWorkflowPlan(
            workflow_id="",
            workflow_kind="skill_compose",
            session_id="ws-1",
            created_at="2026-04-06T00:00:00+00:00",
            root_inputs={},
            final_output_step="greet",
            steps=(
                BlendWorkflowStep(
                    step_id="greet",
                    operator_kind="skill",
                    operator_name="Workstation Greeting From Wasm",
                ),
            ),
            metadata={"target": "skills"},
        )
        workflow_run = BlendWorkflowRun(
            workflow_run_id="",
            workflow_id="",
            plan=workflow_plan,
            status="ok",
            session_id="ws-1",
            started_at="2026-04-06T00:00:01+00:00",
            finished_at="2026-04-06T00:00:02+00:00",
            final_output_step="greet",
            final_output={"greeting": "hello from workstation wasm"},
            final_outputs_by_step={"greet": {"greeting": "hello from workstation wasm"}},
            steps=[{"step_id": "greet", "status": "ok"}],
            plan_authorities=["execute"],
        )
        persisted_plan, persisted_run, _store = persist_blend_workflow_objects(
            root_path=self.root,
            plan=workflow_plan,
            run=workflow_run,
            session_id="ws-1",
        )
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            skill_query="Workstation Greeting From Wasm",
            workflow_id=persisted_plan.workflow_id,
            workflow_run_id=persisted_run.workflow_run_id,
        )
        skill_page = _build_page_with_panel_kind(spec, panel_kind="skill_form")
        workflow_page = _build_page_with_panel_kind(spec, panel_kind="workflow")
        skill_labels = {
            _button_label(control)
            for control in _walk_flet_controls(skill_page)
            if _is_flet_button(control)
        }
        workflow_labels = {
            _button_label(control)
            for control in _walk_flet_controls(workflow_page)
            if _is_flet_button(control)
        }
        self.assertIn("Invoke Skill", skill_labels)
        self.assertIn("Rerun Workflow", workflow_labels)

    def test_chat_panel_keeps_prompt_outside_scrollable_transcript(self) -> None:
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "",
                "busy": False,
            },
            on_prompt=lambda _prompt: None,
        )
        self.assertEqual(chat_panel.__class__.__name__, "Column")
        self.assertGreaterEqual(len(chat_panel.controls), 5)
        prompt_field = _find_first_flet_control(chat_panel, lambda control: control.__class__.__name__ == "TextField")
        transcript_list = _find_first_flet_control(
            chat_panel,
            lambda control: control.__class__.__name__ == "ListView" and getattr(control, "data", None) == "chat_transcript",
        )
        suggestion_list = _find_first_flet_control(
            chat_panel,
            lambda control: control.__class__.__name__ == "ListView" and getattr(control, "data", None) == "chat_suggestions",
        )
        composer_row = _find_first_flet_control(
            chat_panel.controls[3],
            lambda control: control.__class__.__name__ == "Row",
        )
        self.assertIsNotNone(prompt_field)
        self.assertIsNotNone(transcript_list)
        self.assertIsNotNone(suggestion_list)
        self.assertTrue(bool(getattr(composer_row, "expand", False)))
        self.assertEqual(getattr(prompt_field, "expand", None), 1)
        self.assertTrue(bool(getattr(prompt_field, "shift_enter", False)))
        self.assertTrue(bool(getattr(prompt_field, "ignore_up_down_keys", False)))
        self.assertIsNotNone(getattr(prompt_field, "on_submit", None))
        self.assertTrue(bool(getattr(transcript_list, "auto_scroll", False)))

    def test_chat_submit_clears_prompt_before_dispatch(self) -> None:
        class _PageStub:
            def __init__(self) -> None:
                self.updated = False

            def update(self) -> None:
                self.updated = True

        observed_prompt_values: list[str] = []
        captured_prompts: list[str] = []
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "",
                "busy": False,
            },
            on_prompt=lambda prompt: (
                observed_prompt_values.append(str(prompt_field.value or "")),
                captured_prompts.append(prompt),
            ),
        )
        prompt_field = _find_first_flet_control(chat_panel, lambda control: control.__class__.__name__ == "TextField")
        prompt_field.value = "hello workstation"
        page = _PageStub()
        prompt_field.on_submit(SimpleNamespace(page=page))
        self.assertEqual(captured_prompts, ["hello workstation"])
        self.assertEqual(observed_prompt_values, [""])
        self.assertEqual(prompt_field.value, "")
        self.assertTrue(page.updated)

    def test_chat_submit_keeps_prompt_when_busy(self) -> None:
        captured_prompts: list[str] = []
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "Running prompt...",
                "busy": True,
            },
            on_prompt=lambda prompt: captured_prompts.append(prompt),
        )
        prompt_field = _find_first_flet_control(chat_panel, lambda control: control.__class__.__name__ == "TextField")
        prompt_field.value = "hello workstation"
        prompt_field.on_submit(SimpleNamespace(page=None))
        self.assertEqual(captured_prompts, [])
        self.assertEqual(prompt_field.value, "hello workstation")

    def test_chat_panel_fragment_suggestions_insert_skill_title(self) -> None:
        context = workstation_chat_context(self.root)
        suggestion_titles = (
            "API Client Commands 01 — Get Json From Url / Api Client Commands 01 Get Json From Url",
            "API Client Commands 02 — Get Json With Query Parameters / Api Client Commands 02 Get Json With Query Parameters",
            "API Client Commands 03 — Post Json To Url / Api Client Commands 03 Post Json To Url",
            "API Client Commands 04 — Delete Json From Url / Api Client Commands 04 Delete Json From Url",
            "API Client Commands 05 — Patch Json On Url / Api Client Commands 05 Patch Json On Url",
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
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "",
                "busy": False,
            },
            on_prompt=lambda _prompt: None,
            prompt_text="Use AP to fetch",
            on_prompt_text_change=lambda _value: None,
            prompt_suggestions=suggestion_titles,
            prompt_suggestion_applier=lambda current_value, selected_value: workstation_chat_apply_prompt_suggestion(
                context=suggestion_context,
                buffer_text=str(current_value or ""),
                suggestion=str(selected_value or ""),
            ),
        )
        composer_container = chat_panel.controls[3]
        composer_column = composer_container.content
        suggestion_panel = chat_panel.controls[4]
        suggestion_wrap = _find_first_flet_control(
            suggestion_panel,
            lambda control: control.__class__.__name__ == "ListView" and getattr(control, "data", None) == "chat_suggestions",
        )
        self.assertTrue(bool(getattr(suggestion_panel, "visible", False)))
        self.assertTrue(bool(getattr(suggestion_wrap, "visible", False)))
        self.assertEqual(len(suggestion_wrap.controls), len(suggestion_titles))
        first_suggestion_row = suggestion_wrap.controls[0]
        second_suggestion_row = suggestion_wrap.controls[1]
        suggested_title = _button_label(first_suggestion_row)
        self.assertIn("API Client Commands", suggested_title)
        self.assertTrue(suggested_title.startswith("> "))
        self.assertTrue(_button_label(second_suggestion_row).startswith("  "))
        first_suggestion_row.on_click(SimpleNamespace(page=None))
        prompt_field = _find_first_flet_control(composer_column, lambda control: control.__class__.__name__ == "TextField")
        self.assertEqual(str(prompt_field.value or ""), f"Use {suggested_title[2:]} to fetch")

    def test_chat_panel_registers_prompt_runtime_for_in_place_suggestion_updates(self) -> None:
        registered_prompt_field = None
        registered_refresher = None

        def _register_runtime(prompt_field, refresh_suggestions) -> None:
            nonlocal registered_prompt_field
            nonlocal registered_refresher
            registered_prompt_field = prompt_field
            registered_refresher = refresh_suggestions

        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "",
                "busy": False,
            },
            on_prompt=lambda _prompt: None,
            prompt_text="Use AP to fetch",
            prompt_suggestions=[
                "API Alpha",
                "API Beta",
                "API Gamma",
            ],
            register_chat_prompt_runtime=_register_runtime,
        )
        self.assertIsNotNone(registered_prompt_field)
        self.assertTrue(callable(registered_refresher))

        suggestion_panel = chat_panel.controls[4]
        suggestion_wrap = _find_first_flet_control(
            suggestion_panel,
            lambda control: control.__class__.__name__ == "ListView" and getattr(control, "data", None) == "chat_suggestions",
        )

        registered_refresher("Use AP to fetch", selected_index=1)
        self.assertTrue(_button_label(suggestion_wrap.controls[0]).startswith("  "))
        self.assertTrue(_button_label(suggestion_wrap.controls[1]).startswith("> "))

    def test_chat_panel_renders_pending_prompt_immediately(self) -> None:
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "Running prompt...",
                "activity_text": "",
                "pending_prompt": "hello pending",
                "busy": True,
            },
            on_prompt=lambda _prompt: None,
        )
        rendered_text_values = {
            str(getattr(control, "value", "") or "")
            for control in _walk_flet_controls(chat_panel)
            if control.__class__.__name__ == "Text"
        }
        self.assertIn("hello pending", rendered_text_values)

    def test_chat_panel_renders_transient_activity_strip_above_transcript(self) -> None:
        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "Running prompt...",
                "activity_text": "Step started: Emit Text..",
                "busy": True,
            },
            on_prompt=lambda _prompt: None,
        )
        self.assertGreaterEqual(len(chat_panel.controls), 3)
        activity_container = chat_panel.controls[1]
        transcript_container = chat_panel.controls[2]
        self.assertEqual(activity_container.__class__.__name__, "Container")
        self.assertEqual(transcript_container.__class__.__name__, "Container")
        activity_text_controls = [
            control
            for control in _walk_flet_controls(activity_container)
            if control.__class__.__name__ == "Text"
        ]
        activity_values = [str(getattr(control, "value", "") or "") for control in activity_text_controls]
        self.assertIn("Activity", activity_values)
        self.assertIn("Step started: Emit Text..", activity_values)
        activity_message = next(
            control for control in activity_text_controls if str(getattr(control, "value", "") or "") == "Step started: Emit Text.."
        )
        self.assertTrue(bool(getattr(activity_message, "selectable", False)))

    def test_chat_panel_keeps_activity_strip_slot_when_idle(self) -> None:
        import flet as ft

        chat_panel = _chat_content(
            {
                "transcript": {"messages": []},
                "action_result": {},
                "status_text": "",
                "activity_text": "",
                "busy": False,
            },
            on_prompt=lambda _prompt: None,
        )
        self.assertGreaterEqual(len(chat_panel.controls), 3)
        activity_container = chat_panel.controls[1]
        activity_text_controls = [
            control
            for control in _walk_flet_controls(activity_container)
            if control.__class__.__name__ == "Text"
        ]
        activity_values = [str(getattr(control, "value", "") or "") for control in activity_text_controls]
        self.assertIn("Activity", activity_values)
        self.assertIn("", activity_values)
        self.assertEqual(getattr(chat_panel, "horizontal_alignment", None), ft.CrossAxisAlignment.STRETCH)

    def test_scroll_flet_chat_transcript_to_end_targets_chat_list(self) -> None:
        page_view = build_workstation_flet_page(workstation_flet_dashboard_spec(root_path=self.root))
        scroll_calls: list[dict[str, object]] = []

        AttachedListView = type(
            "ListView",
            (),
            {
                "page": property(lambda self: object()),
                "scroll_to": lambda self, *, offset=None, duration=0, **_kwargs: scroll_calls.append(
                    {"offset": offset, "duration": duration}
                ),
            },
        )

        with patch("workstation.flet_host._flet_chat_transcript_list", return_value=AttachedListView()):
            _scroll_flet_chat_transcript_to_end(page_view)
        self.assertEqual(scroll_calls, [{"offset": -1, "duration": 0}])

    def test_scroll_flet_chat_transcript_to_end_ignores_closed_session_scroll(self) -> None:
        page_view = build_workstation_flet_page(workstation_flet_dashboard_spec(root_path=self.root))
        transcript_list = _flet_chat_transcript_list(page_view)
        self.assertIsNotNone(transcript_list)

        async def _raise_closed() -> None:
            raise RuntimeError("Session closed")

        class _PageStub:
            def run_task(self, func, *args):
                return asyncio.run(func(*args))

        transcript_list.scroll_to = lambda **_kwargs: _raise_closed()  # type: ignore[method-assign]
        _scroll_flet_chat_transcript_to_end(page_view, page=_PageStub())

    def test_scroll_flet_chat_transcript_to_end_ignores_unattached_control(self) -> None:
        page_view = build_workstation_flet_page(workstation_flet_dashboard_spec(root_path=self.root))
        UnattachedListView = type(
            "ListView",
            (),
            {
                "page": property(
                    lambda self: (_ for _ in ()).throw(RuntimeError("Control must be added to the page first"))
                )
            },
        )

        with patch("workstation.flet_host._flet_chat_transcript_list", return_value=UnattachedListView()):
            _scroll_flet_chat_transcript_to_end(page_view)

    def test_chat_panel_busy_disables_controls_without_transcript_status_block(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            chat_status_text="Running prompt...",
            chat_busy=True,
        )
        page_view = build_workstation_flet_page(spec)
        chat_panel = _active_panel_content(page_view)
        prompt_fields = [control for control in _walk_flet_controls(chat_panel) if control.__class__.__name__ == "TextField"]
        self.assertEqual(len(prompt_fields), 1)
        self.assertTrue(bool(getattr(prompt_fields[0], "disabled", False)))
        rendered_text_values = {
            str(getattr(control, "value", "") or "")
            for control in _walk_flet_controls(chat_panel)
            if control.__class__.__name__ == "Text"
        }
        self.assertNotIn("Running prompt...", rendered_text_values)
        self.assertIn("Working... activity is shown above while the current turn runs.", rendered_text_values)

    def test_learn_markdown_panel_shows_status_and_disables_buttons_while_busy(self) -> None:
        spec = workstation_flet_dashboard_spec(
            root_path=self.root,
            markdown_selected_path="/tmp/example.md",
            markdown_status_text="Learning and importing: example.md",
            markdown_busy=True,
        )
        page_view = _build_page_with_panel_kind(spec, panel_kind="research")
        learn_panel = _active_panel_content(page_view)
        button_labels = {
            _button_label(control): control
            for control in _walk_flet_controls(learn_panel)
            if _is_flet_button(control)
        }
        self.assertIn("Learn Markdown", button_labels)
        self.assertTrue(bool(getattr(button_labels["Learn Markdown"], "disabled", False)))
        rendered_text_values = {
            str(getattr(control, "value", "") or "")
            for control in _walk_flet_controls(learn_panel)
            if control.__class__.__name__ == "Text"
        }
        combined_text = "\n".join(rendered_text_values)
        self.assertIn("/tmp/example.md", combined_text)
        self.assertIn("Learning and importing: example.md", combined_text)

    def test_research_panel_uses_phase_workspace_titles(self) -> None:
        spec = workstation_flet_dashboard_spec(root_path=self.root)
        page_view = _build_page_with_panel_kind(spec, panel_kind="research")
        rendered_text_values = {
            str(getattr(control, "value", "") or "")
            for control in _walk_flet_controls(_active_panel_content(page_view))
            if control.__class__.__name__ == "Text"
        }
        self.assertIn("Research Controls", rendered_text_values)
        self.assertIn("Research Status", rendered_text_values)
        self.assertIn("Research Journal", rendered_text_values)
        self.assertIn("Sources", rendered_text_values)
        self.assertIn("Observed Contents", rendered_text_values)
        self.assertIn("Target", rendered_text_values)

    def test_read_only_panels_use_shared_layout_titles(self) -> None:
        spec = workstation_flet_dashboard_spec(root_path=self.root)
        for panel_kind in ("permission_panel", "activity_feed", "skill_catalog"):
            page_view = _build_page_with_panel_kind(spec, panel_kind=panel_kind)
            rendered_text_values = {
                str(getattr(control, "value", "") or "")
                for control in _walk_flet_controls(_active_panel_content(page_view))
                if control.__class__.__name__ == "Text"
            }
            self.assertIn(workstation_panel_title(panel_kind), rendered_text_values)

    def test_dashboard_read_only_panel_texts_are_selectable(self) -> None:
        spec = workstation_flet_dashboard_spec(root_path=self.root)
        chat_page = build_workstation_flet_page(spec)
        skills_page = _build_page_with_panel_kind(spec, panel_kind="skill_catalog")
        text_controls = [
            control
            for control in list(_walk_flet_controls(chat_page)) + list(_walk_flet_controls(skills_page))
            if control.__class__.__name__ == "Text"
        ]
        matching_values = {
            str(getattr(control, "value", "") or ""): control
            for control in text_controls
        }
        self.assertTrue(bool(getattr(matching_values["Built-in"], "selectable", False)))
        self.assertTrue(bool(getattr(matching_values["Imported"], "selectable", False)))
        self.assertTrue(bool(getattr(matching_values["No conversation yet."], "selectable", False)))


def _walk_flet_controls(control):
    yield control
    for attribute in ("controls", "tabs", "actions"):
        value = getattr(control, attribute, None)
        if isinstance(value, list):
            for item in value:
                yield from _walk_flet_controls(item)
    for attribute in ("content", "title", "subtitle", "leading", "trailing"):
        value = getattr(control, attribute, None)
        if value is not None:
            yield from _walk_flet_controls(value)


def _find_first_flet_control(control, predicate):
    for item in _walk_flet_controls(control):
        if predicate(item):
            return item
    raise AssertionError("Expected matching Flet control was not found.")


def _is_flet_button(control) -> bool:
    return control.__class__.__name__ in {
        "Button",
        "ElevatedButton",
        "FilledButton",
        "OutlinedButton",
        "TextButton",
        "IconButton",
    }


def _active_panel_content(page_view):
    return page_view.controls[1].content


def _build_page_with_panel_kind(spec, *, panel_kind: str):
    panel_index = next(index for index, panel in enumerate(spec.panels) if panel.panel_kind == panel_kind)
    return _build_workstation_flet_page(
        spec,
        on_prompt=lambda _prompt: None,
        on_learn_markdown=lambda: None,
        on_export_learned_bundle=lambda: None,
        on_subject_nav=lambda _delta: None,
        on_subject_action=lambda _phase, _action_key: None,
        on_invoke_skill=lambda _raw_inputs: None,
        on_run_workflow=lambda: None,
        active_tab_index=panel_index,
        on_tab_change=None,
        register_panel_focus_target=None,
        chat_input_text="",
        on_chat_input_change=None,
        chat_prompt_suggestions=(),
        selected_chat_prompt_suggestion_index=0,
        on_chat_prompt_suggestion_selected=None,
        chat_prompt_suggestion_provider=None,
        chat_prompt_suggestion_applier=None,
        register_chat_prompt_runtime=None,
        on_chat_prompt_key_down=None,
    )


def _button_label(control) -> str:
    content = getattr(control, "content", None)
    if isinstance(content, str):
        return content
    text = getattr(content, "value", None)
    if text is not None:
        return str(text or "")
    controls = getattr(content, "controls", None)
    if isinstance(controls, list) and controls:
        return _button_label(controls[0])
    return str(getattr(control, "value", "") or "")


if __name__ == "__main__":
    unittest.main()
