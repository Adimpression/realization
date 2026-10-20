# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import asyncio
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from learning_context import (
    LearningContext,
    LearningUnit,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from publication_projection import materialize_report_publication_from_learning_context
from workstation.chat_ui import (
    _TextualWorkstationChatApp,
    _scroll_window_to_end,
    _WorkstationChatPaneState,
    _scroll_window_linewise,
    _textual_scroll_to_end,
    _textual_copy_selected_text,
    _window_scroll_cursor_position,
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
    workstation_chat_prepare_markdown_prompt,
    workstation_chat_prompt_target_plan,
    workstation_chat_routed_llm_prompt_text,
    workstation_chat_resume_research_prompt,
    workstation_chat_suggestions,
    workstation_chat_ui_supported,
)
from workstation.models import WorkstationDelegationEscalationRequest
from workstation.session import launch_workstation_session


class WorkstationChatUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
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
        prepare_plan = workstation_chat_prompt_target_plan(
            context=workstation_chat_context(self.root),
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
                self.assertIsNotNone(app.query_one("#review_tab"))
                self.assertIsNotNone(app.query_one("#publication_tab"))
                self.assertIsNotNone(app.query_one("#permissions_tab"))
                self.assertIsNotNone(app.query_one("#activity_tab"))
                self.assertIsNotNone(app.query_one("#skills_tab"))
                self.assertIsNotNone(app.query_one("#learn_markdown_button"))
                self.assertIsNotNone(app.query_one("#export_learned_button"))
                await pilot.click("#input")
                await pilot.press("/", "h", "enter")
                await pilot.pause()
                transcripts = list(app.query("#transcript"))
                self.assertTrue(transcripts)
                transcript = transcripts[0]
                self.assertGreater(len(getattr(transcript, "lines", [])), 0)
                self.assertTrue(any("Permission model" in str(line) for line in transcript.lines))

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
                with patch("workstation.chat_ui._run_enhanced_workstation_turn_worker", lambda **_kwargs: None):
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
                await pilot.pause()
                panel = app.query_one("#learn_status_panel")
                rendered = str(panel.render())
                self.assertIn("State: Running", rendered)
                self.assertIn("demo.md", rendered)
                self.assertIn("Converting markdown to a portable skill bundle...", rendered)

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
                header = str(app.query_one("#subject_flow_header").render())
                subject_display = str(app.query_one("#subject_research_subject_display").render())
                status = str(app.query_one("#learn_status_panel").render())
                learn_result = app.query_one("#learn_result")
                self.assertIn("Live corpus workflow over LearningContext.", header)
                self.assertIn("Phase: Research", header)
                self.assertIn("Kinematics Demo", subject_display)
                self.assertIn("Kinematics Demo", status)
                self.assertTrue(any("Research Journal: Kinematics Demo" in str(line) for line in learn_result.lines))

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
                status = str(app.query_one("#learn_status_panel").render())
                learn_result = app.query_one("#learn_result")
                self.assertIn("No LearningContext yet", status)
                self.assertIn("Use Learn Markdown", "\n".join(str(line) for line in learn_result.lines))

                action_one = app.query_one("#subject_research_action_1_button")
                action_two = app.query_one("#subject_research_action_2_button")
                action_three = app.query_one("#subject_research_action_3_button")
                action_four = app.query_one("#subject_research_action_4_button")
                self.assertEqual(str(getattr(action_one, "label", "")), "Refresh Subjects")
                self.assertEqual(str(getattr(action_two, "label", "")), "Use Learn Markdown")
                self.assertEqual(str(getattr(action_three, "label", "")), "Add Last Assistant")
                self.assertEqual(str(getattr(action_four, "label", "")), "Open Context")
                self.assertTrue(getattr(action_three, "disabled", False))
                self.assertTrue(getattr(action_four, "disabled", False))

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
                to_dict=lambda: {
                    "action_kind": "learn_markdown",
                    "status": "ok",
                    "title": "Learn Markdown",
                    "message": "Imported 1 skill from kinematics.md.",
                    "payload": {
                        "canonical_export_path": str(self.root / "learned_markdown" / "kinematics.skill.yaml"),
                        "suggested_export_filename": "kinematics.skill.yaml",
                        "report": {
                            "subject_id": "kinematics-demo",
                        },
                    },
                }
            )

        async def _exercise() -> None:
            app = _TextualWorkstationChatApp(
                root=self.root,
                model=None,
                max_tool_rounds=2,
            )
            with patch("workstation.chat_ui.desktop_select_markdown_file", return_value=markdown_path), patch(
                "workstation.chat_ui.workstation_learn_markdown_action",
                side_effect=_fake_result,
            ), patch(
                "workstation.chat_ui.desktop_select_skill_export_path",
                side_effect=AssertionError("learn markdown should not auto-open export selection"),
            ):
                async with app.run_test(size=(180, 60)) as pilot:
                    await pilot.pause()
                    await pilot.click("#tab_button_learn_tab")
                    await pilot.pause()
                    await pilot.click("#learn_markdown_button")
                    await pilot.pause()
                    await pilot.pause()
                    status = str(app.query_one("#learn_status_panel").render())
                    header = str(app.query_one("#subject_flow_header").render())
                    subject_display = str(app.query_one("#subject_research_subject_display").render())
                    action_three = app.query_one("#subject_research_action_3_button")
                    action_four = app.query_one("#subject_research_action_4_button")
                    self.assertIn("Markdown Ingress", status)
                    self.assertNotIn("Imported 1 skill", app._state.transcript_text())
                    self.assertIn("Learned and imported: kinematics.md", status)
                    self.assertIn("Last result: ok", status)
                    self.assertIn("Phase: Research", header)
                    self.assertIn("Kinematics Demo", subject_display)
                    self.assertTrue(getattr(action_three, "disabled", False))
                    self.assertFalse(getattr(action_four, "disabled", False))

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
                await pilot.click("#subject_research_action_3_button")
                await pilot.pause()
                status_after_open = str(app.query_one("#learn_status_panel").render())
                self.assertIn("Live corpus workflow ready", status_after_open)

                await pilot.click("#subject_research_action_4_button")
                await pilot.pause()
                status_after_open = str(app.query_one("#learn_status_panel").render())
                self.assertIn("Subject context opened", status_after_open)

                await pilot.click("#tab_button_review_tab")
                await pilot.pause()
                header = str(app.query_one("#review_flow_header").render())
                review_result = app.query_one("#review_result")
                self.assertEqual(app._active_tab_id(), "review_tab")
                self.assertIn("Phase: Review", header)
                self.assertTrue(any("Review Workspace: kinematics-demo" in str(line) for line in review_result.lines))

                action_one = app.query_one("#subject_review_action_1_button")
                action_two = app.query_one("#subject_review_action_2_button")
                action_three = app.query_one("#subject_review_action_3_button")
                action_four = app.query_one("#subject_review_action_4_button")
                self.assertEqual(str(getattr(action_one, "label", "")), "Open Context")
                self.assertEqual(str(getattr(action_two, "label", "")), "Compare Projections")
                self.assertEqual(str(getattr(action_three, "label", "")), "Approve For Report")
                self.assertEqual(str(getattr(action_four, "label", "")), "Preview subject.md")

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
                "workstation.chat_ui.desktop_open_path",
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
                    self.assertEqual(str(getattr(action_one, "label", "")), "Preview report.md")
                    self.assertEqual(str(getattr(action_two, "label", "")), "Rebuild Report")
                    self.assertEqual(str(getattr(action_three, "label", "")), "Open Release Packet")
                    self.assertEqual(str(getattr(action_four, "label", "")), "Preview report.pdf")

                    await pilot.click("#subject_publication_action_3_button")
                    await pilot.pause()
                    await pilot.click("#subject_publication_action_1_button")
                    await pilot.pause()
                    await pilot.click("#subject_publication_action_4_button")
                    await pilot.pause()
                    status = str(app.query_one("#publication_status_panel").render())
                    learn_result = app.query_one("#publication_result")
                    self.assertIn("Opened report.pdf.", status)
                    self.assertTrue(any("Output Preview [report.pdf]" in str(line) for line in learn_result.lines))

        asyncio.run(_exercise())
        self.assertIn(expected_packet_path, opened_paths)
        self.assertIn(expected_report_md, opened_paths)
        self.assertIn(expected_report_pdf, opened_paths)
        self.assertTrue(expected_report_pdf.is_file())

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
        self.assertEqual(app._textual_log_wrap_width(_Widget(0)), 108)
        self.assertEqual(app._textual_log_wrap_width(_Widget(60)), 56)

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


if __name__ == "__main__":
    unittest.main()
