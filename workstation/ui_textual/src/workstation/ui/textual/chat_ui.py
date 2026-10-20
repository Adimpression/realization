# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import datetime as _datetime
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import textwrap
import time
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from semantic_text import collapse_ws
from workstation.contracts.shell import (
    WorkstationChatContext,
    WorkstationChatPromptTargetPlan,
    WorkstationShellClient,
)
from workstation.contracts.subject import SubjectWorkflowClient
from workstation.ui.shared.activity_view import start_workstation_activity_tail, workstation_activity_log_offset
from workstation.shell.core.application_facade import (
    AVAILABLE_WORKSTATION_CAPABILITIES,
    InProcessWorkstationShellClient,
    WorkstationDelegationEscalationDecision,
    WorkstationDelegationEscalationRequest,
    WorkstationProjectionSubscriberController,
    canonical_workstation_chat_slash_command_text,
    workstation_chat_context as _shared_workstation_chat_context,
    workstation_chat_help_text as _shared_workstation_chat_help_text,
    workstation_chat_prepare_last_assistant_resolution as _shared_workstation_chat_prepare_last_assistant_resolution,
    workstation_chat_prepare_markdown_prompt as _shared_workstation_chat_prepare_markdown_prompt,
    workstation_chat_prompt_target_plan as _shared_workstation_chat_prompt_target_plan,
    workstation_chat_resume_research_prompt as _shared_workstation_chat_resume_research_prompt,
    workstation_chat_routed_llm_prompt_text as _shared_workstation_chat_routed_llm_prompt_text,
    workstation_chat_slash_commands,
    workstation_export_learned_skill_bundle_action,
)
from workstation.ui.shared.desktop_file_dialogs import (
    desktop_open_path,
    desktop_prompt_url,
    desktop_select_markdown_files,
    desktop_select_skill_export_path,
)
from workstation.ui.shared.colors import (
    ACTIVE_AREA_BACKGROUND as _ACTIVE_AREA_BACKGROUND,
    ACTIVE_AREA_FRAME as _ACTIVE_AREA_FRAME,
    ACTIVE_TEXT_A_COLOR as _ACTIVE_TEXT_A_COLOR,
    ACTIVE_TEXT_B_COLOR as _ACTIVE_TEXT_B_COLOR,
    ACTIVE_TEXT_C_COLOR as _ACTIVE_TEXT_C_COLOR,
    ACTIVE_TEXT_D_COLOR as _ACTIVE_TEXT_D_COLOR,
    ACTIVE_TEXT_F_COLOR as _ACTIVE_TEXT_F_COLOR,
    INACTIVE_AREA_BACKGROUND as _INACTIVE_AREA_BACKGROUND,
    INACTIVE_AREA_FRAME as _INACTIVE_AREA_FRAME,
    INACTIVE_TEXT_A_COLOR as _INACTIVE_TEXT_A_COLOR,
    PAGE_BACKGROUND as _PAGE_BACKGROUND,
    SUBJECT_CONTROL_ACTIVE_BACKGROUND as _SUBJECT_CONTROL_ACTIVE_BACKGROUND,
    SUBJECT_CONTROL_BACKGROUND as _SUBJECT_CONTROL_BACKGROUND,
    SUBJECT_CONTROL_DISABLED_BACKGROUND as _SUBJECT_CONTROL_DISABLED_BACKGROUND,
    SUBJECT_CONTROL_TEXT_COLOR as _SUBJECT_CONTROL_TEXT_COLOR,
)
from workstation.ui.shared.theme import (
    ASSISTANT_TEXT_COLOR as _ASSISTANT_TEXT_COLOR,
    CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR as _CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR,
    CONTROL_BUTTON_BACKGROUND_COLOR as _CONTROL_BUTTON_BACKGROUND_COLOR,
    CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR as _CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR,
    CONTROL_BUTTON_TEXT_COLOR as _CONTROL_BUTTON_TEXT_COLOR,
    DEFAULT_TEXT_COLOR as _DEFAULT_TEXT_COLOR,
    DISABLED_TEXT_COLOR as _DISABLED_TEXT_COLOR,
    MUTED_TEXT_COLOR as _MUTED_TEXT_COLOR,
    PROMPT_TEXT_COLOR as _PROMPT_TEXT_COLOR,
    SUBJECT_HEADER_TEXT_COLOR as _SUBJECT_HEADER_TEXT_COLOR,
    SYSTEM_TEXT_COLOR as _SYSTEM_TEXT_COLOR,
    TIME_TEXT_COLOR as _TIME_TEXT_COLOR,
    USER_TEXT_COLOR as _USER_TEXT_COLOR,
)
from workstation.ui.shared.layout import (
    workstation_pane_layout,
    workstation_pane_title,
    workstation_pane_text_role,
    workstation_subject_gate_height_units,
    workstation_tab_title,
)
from workstation.subject.textual.application_facade import (
    MOCK_SUBJECT_PHASES,
    MockSubjectActionSpec,
    MockSubjectGateAction,
    MockSubjectProgress,
    MockSubjectScenario,
    MockSubjectSelectionListSpec,
    MockSubjectSelectSpec,
    MockSubjectSwitchSpec,
    MockSubjectTableSpec,
    TextualSubjectWorkflowProjectionBackend,
    latest_source_revision,
    mock_source_collection_option_label,
    mock_subject_research_source_collection_workbench_rows,
    mock_subject_status_title,
    new_mock_subject_progress,
    normalize_itemized_decision_role,
)
from workstation.foundation.projections import (
    split_rendered_workstation_activity_line,
)


_textual_subject_workflow_client_factory: Callable[[], SubjectWorkflowClient] | None = None


def configure_textual_subject_workflow_client_factory(
    factory: Callable[[], SubjectWorkflowClient],
) -> None:
    """Configure the compatibility default used by direct UI construction."""
    if not callable(factory):
        raise TypeError("factory must be callable")
    global _textual_subject_workflow_client_factory
    _textual_subject_workflow_client_factory = factory


def _create_textual_subject_workflow_client() -> SubjectWorkflowClient:
    factory = _textual_subject_workflow_client_factory
    if factory is None:
        raise RuntimeError(
            "No subject workflow client was supplied. The entry layer must inject one "
            "or configure the direct-construction compatibility factory."
        )
    return factory()

try:
    from textual import events as textual_events
    from textual.app import App as TextualApp, ComposeResult
    from textual.binding import Binding as TextualBinding
    from textual.containers import Horizontal, Vertical
    from textual.suggester import Suggester as TextualSuggester
    from textual.widgets import (
        Button as TextualButton,
        DataTable as TextualDataTable,
        Input as TextualInput,
        Log as TextualLog,
        OptionList as TextualOptionList,
        RichLog as TextualRichLog,
        SelectionList as TextualSelectionList,
        Select as TextualSelect,
        Static as TextualStatic,
        Switch as TextualSwitch,
        Tab as TextualTab,
        TabbedContent as TextualTabbedContent,
        Tabs as TextualTabs,
        TabPane as TextualTabPane,
        Tree as TextualTree,
    )
    from textual.widgets.option_list import Option as TextualOption
except Exception:  # pragma: no cover - optional dependency guard
    textual_events = None
    TextualApp = None
    ComposeResult = Any
    TextualBinding = None
    Horizontal = None
    Vertical = None
    TextualSuggester = None
    TextualButton = None
    TextualDataTable = None
    TextualInput = None
    TextualLog = None
    TextualOptionList = None
    TextualOption = None
    TextualRichLog = None
    TextualSelectionList = None
    TextualSelect = None
    TextualStatic = None
    TextualSwitch = None
    TextualTab = None
    TextualTabbedContent = None
    TextualTabs = None
    TextualTabPane = None
    TextualTree = None

try:
    from rich.text import Text as RichText
except Exception:  # pragma: no cover - optional dependency guard
    RichText = None

try:
    from prompt_toolkit import Application, PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.data_structures import Point
    from prompt_toolkit.filters import has_focus
    from prompt_toolkit.formatted_text import ANSI
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import HSplit, Layout, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.layout.margins import ScrollbarMargin
    from prompt_toolkit.widgets import Frame, TextArea
    from prompt_toolkit.shortcuts import print_formatted_text
except Exception:  # pragma: no cover - optional dependency guard
    Application = None
    PromptSession = None
    Completer = object
    Completion = None
    Point = None
    has_focus = None
    ANSI = None
    FileHistory = None
    KeyBindings = None
    HSplit = None
    Layout = None
    Window = None
    FormattedTextControl = None
    ScrollbarMargin = None
    Frame = None
    TextArea = None
    print_formatted_text = None

if TextualLog is not None:  # pragma: no branch - optional dependency guard
    class _FocusableTextualLog(TextualLog):
        can_focus = True

        def _focus_from_pointer_event(self, event: Any) -> None:
            try:
                self.focus()
            except Exception:
                return
            if hasattr(event, "stop"):
                event.stop()

        def on_mouse_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_click(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is not None:
                handler = getattr(app, "_handle_focusable_textual_log_click", None)
                if callable(handler):
                    try:
                        if bool(handler(self, event)):
                            return
                    except Exception:
                        pass
            self._focus_from_pointer_event(event)

        def on_key(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            key = str(getattr(event, "key", "") or "")
            normalized_key = str(key).casefold()
            handled = False
            if widget_id in {
                "review_scope_tree_panel",
                "review_scope_detail_panel",
            }:
                if key == "up":
                    handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(1))
                elif key in {"shift+up", "shift+cursor_up"} or normalized_key == "k":
                    handled = bool(getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(-1))
                elif key in {"shift+down", "shift+cursor_down"} or normalized_key == "j":
                    handled = bool(getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(1))
                elif normalized_key == "h":
                    handled = bool(getattr(app, "_hold_review_scope_item", lambda: False)())
                elif normalized_key == "x":
                    handled = bool(getattr(app, "_toggle_review_scope_item", lambda: False)())
                elif normalized_key == "r":
                    handled = bool(getattr(app, "_release_review_scope_items", lambda: False)())
                elif key == "enter":
                    handled = bool(getattr(app, "_preview_review_scope_item", lambda: False)())
            elif widget_id in {"subject_sources_panel", "subject_target_panel"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(1))
            elif widget_id in {"itemize_inventory_panel", "itemize_detail_panel"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(1))
                elif normalized_key == "h":
                    handled = bool(getattr(app, "_hold_itemize_item", lambda: False)())
                elif key == "enter":
                    handled = bool(getattr(app, "_preview_itemize_item", lambda: False)())
            elif widget_id in {"draft_scope_tree_panel", "draft_model_main_panel", "draft_scope_detail_panel", "draft_result"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(1))
                elif key in {"shift+up", "shift+cursor_up"}:
                    handled = bool(getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(-1))
                elif key in {"shift+down", "shift+cursor_down"}:
                    handled = bool(getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(1))
                elif normalized_key == "d":
                    handled = bool(getattr(app, "_toggle_draft_decision_included", lambda: False)())
            if handled:
                event.stop()
else:  # pragma: no cover - optional dependency guard
    _FocusableTextualLog = Any

if TextualDataTable is not None:  # pragma: no branch - optional dependency guard
    class _FocusableTextualDataTable(TextualDataTable):
        can_focus = True

        def _focus_from_pointer_event(self, event: Any) -> None:
            try:
                self.focus()
            except Exception:
                return
            if getattr(self, "cursor_type", "none") == "none" and hasattr(event, "stop"):
                event.stop()

        def on_mouse_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_click(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_key(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            key = str(getattr(event, "key", "") or "")
            normalized_key = str(key).casefold()
            handled = False
            if widget_id in {"subject_sources_panel", "subject_target_panel", "subject_observation_panel"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(1))
            elif widget_id in {"itemize_inventory_panel", "itemize_detail_panel"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(1))
                elif normalized_key == "h":
                    handled = bool(getattr(app, "_hold_itemize_item", lambda: False)())
                elif key == "enter":
                    handled = bool(getattr(app, "_preview_itemize_item", lambda: False)())
            elif widget_id in {"draft_scope_tree_panel", "draft_model_main_panel", "draft_scope_detail_panel", "draft_result"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(1))
                elif key in {"shift+up", "shift+cursor_up"}:
                    handled = bool(getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(-1))
                elif key in {"shift+down", "shift+cursor_down"}:
                    handled = bool(getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(1))
                elif normalized_key == "d":
                    handled = bool(getattr(app, "_toggle_draft_decision_included", lambda: False)())
            elif widget_id in {"review_scope_tree_panel", "review_scope_detail_panel", "publication_scope_tree_panel", "publication_scope_detail_panel"}:
                if key == "up":
                    handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(-1))
                elif key == "down":
                    handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(1))
                elif key in {"shift+up", "shift+cursor_up"} or normalized_key == "k":
                    handled = bool(getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(-1))
                elif key in {"shift+down", "shift+cursor_down"} or normalized_key == "j":
                    handled = bool(getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(1))
                elif normalized_key == "h":
                    handled = bool(getattr(app, "_hold_review_scope_item", lambda: False)())
                elif normalized_key == "x":
                    handled = bool(getattr(app, "_toggle_review_scope_item", lambda: False)())
                elif normalized_key == "r":
                    handled = bool(getattr(app, "_release_review_scope_items", lambda: False)())
                elif key == "enter":
                    handled = bool(getattr(app, "_preview_review_scope_item", lambda: False)())
            if handled:
                if key == "up":
                    marker = getattr(app, "_mark_pending_data_table_cursor_action", None)
                    if callable(marker):
                        marker(widget_id, -1)
                elif key == "down":
                    marker = getattr(app, "_mark_pending_data_table_cursor_action", None)
                    if callable(marker):
                        marker(widget_id, 1)
                event.stop()

        def action_cursor_up(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            consume = getattr(app, "_consume_pending_data_table_cursor_action", None)
            if callable(consume) and bool(consume(widget_id, -1)):
                return
            handled = False
            if widget_id in {"subject_sources_panel", "subject_target_panel", "subject_observation_panel"}:
                handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(-1))
            elif widget_id in {"itemize_inventory_panel", "itemize_detail_panel"}:
                handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(-1))
            elif widget_id in {"draft_scope_tree_panel", "draft_model_main_panel", "draft_scope_detail_panel", "draft_result"}:
                handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(-1))
            elif widget_id in {"review_scope_tree_panel", "review_scope_detail_panel", "publication_scope_tree_panel", "publication_scope_detail_panel"}:
                handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(-1))
            if handled:
                return
            try:
                super().action_cursor_up()
            except Exception:
                pass

        def action_cursor_down(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            consume = getattr(app, "_consume_pending_data_table_cursor_action", None)
            if callable(consume) and bool(consume(widget_id, 1)):
                return
            handled = False
            if widget_id in {"subject_sources_panel", "subject_target_panel", "subject_observation_panel"}:
                handled = bool(getattr(app, "_move_research_source_cursor", lambda _delta: False)(1))
            elif widget_id in {"itemize_inventory_panel", "itemize_detail_panel"}:
                handled = bool(getattr(app, "_move_itemize_cursor", lambda _delta: False)(1))
            elif widget_id in {"draft_scope_tree_panel", "draft_model_main_panel", "draft_scope_detail_panel", "draft_result"}:
                handled = bool(getattr(app, "_move_draft_review_cursor", lambda _delta: False)(1))
            elif widget_id in {"review_scope_tree_panel", "review_scope_detail_panel", "publication_scope_tree_panel", "publication_scope_detail_panel"}:
                handled = bool(getattr(app, "_move_review_scope_cursor", lambda _delta: False)(1))
            if handled:
                return
            try:
                super().action_cursor_down()
            except Exception:
                pass
else:  # pragma: no cover - optional dependency guard
    _FocusableTextualDataTable = Any

if TextualOptionList is not None and TextualBinding is not None:  # pragma: no branch - optional dependency guard
    class _FocusableTextualOptionList(TextualOptionList):
        can_focus = True
        BINDINGS = [
            TextualBinding("down", "cursor_down", "Down", show=False),
            TextualBinding("end", "last", "Last", show=False),
            TextualBinding("enter", "activate_inventory", "Activate", show=False),
            TextualBinding("home", "first", "First", show=False),
            TextualBinding("pagedown", "page_down", "Page Down", show=False),
            TextualBinding("pageup", "page_up", "Page Up", show=False),
            TextualBinding("up", "cursor_up", "Up", show=False),
            TextualBinding("d", "toggle_inventory_decision", "Decision", show=False),
            TextualBinding("h", "inventory_hold", "Hold", show=False),
            TextualBinding("x", "toggle_inventory", "Toggle", show=False),
            TextualBinding("r", "inventory_release", "Release", show=False),
            TextualBinding("shift+up", "inventory_reorder_up", "Move Earlier", show=False),
            TextualBinding("shift+down", "inventory_reorder_down", "Move Later", show=False),
            TextualBinding("k", "inventory_reorder_up", "Preview Earlier", show=False),
            TextualBinding("j", "inventory_reorder_down", "Preview Later", show=False),
        ]

        def __init__(self, *content: Any, **kwargs: Any) -> None:
            kwargs.setdefault("markup", False)
            kwargs.setdefault("compact", True)
            super().__init__(*content, **kwargs)
            self.lines: tuple[str, ...] = ()
            self.inventory_items: tuple[Any, ...] = ()

        def _focus_from_pointer_event(self, event: Any) -> None:
            try:
                self.focus()
            except Exception:
                return
            if hasattr(event, "stop"):
                event.stop()

        def on_mouse_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def clear(self) -> None:  # pragma: no cover - compatibility helper
            self.lines = ()
            self.inventory_items = ()
            self.set_options(())

        def write_line(self, line: Any) -> None:  # pragma: no cover - compatibility helper
            self.set_rendered_lines((*self.lines, str(line or "")))

        def set_rendered_lines(self, lines: Iterable[str]) -> None:
            """Render non-interactive fallback text when no typed items exist."""
            rendered_lines = tuple(str(line or "") for line in lines)
            self.lines = rendered_lines
            self.inventory_items = ()
            options = tuple(
                TextualOption(
                    line,
                    id=f"{getattr(self, 'id', 'inventory')}::fallback::{index}",
                    disabled=True,
                )
                for index, line in enumerate(rendered_lines)
            )
            self.set_options(options)

        def set_inventory_items(self, items: Iterable[Any]) -> None:
            """Render typed itemization entries as one interactive option each."""
            inventory_items = tuple(
                item
                for item in items
                if collapse_ws(str(getattr(item, "entry_kind", "") or "")) == "itemized_item"
            )
            self.inventory_items = inventory_items
            self.lines = tuple(_textual_itemize_item_label(item) for item in inventory_items)
            self.set_options(
                tuple(
                    TextualOption(
                        label,
                        id=(
                            collapse_ws(str(getattr(item, "entry_id", "") or ""))
                            or f"{getattr(self, 'id', 'inventory')}::{index}"
                        ),
                    )
                    for index, (item, label) in enumerate(zip(inventory_items, self.lines))
                )
            )
            selected_index = next(
                (
                    index
                    for index, item in enumerate(inventory_items)
                    if bool(getattr(item, "selected", False))
                ),
                0,
            )
            if inventory_items:
                try:
                    self.highlighted = selected_index
                    self.scroll_to_highlight()
                except Exception:
                    pass

        def _move_inventory_cursor(self, delta: int) -> None:
            if not self.inventory_items:
                return
            selectable_ordinals = tuple(range(len(self.inventory_items)))
            try:
                current_highlight = int(getattr(self, "highlighted", None))
            except Exception:
                current_highlight = -1
            if current_highlight in selectable_ordinals:
                current_position = selectable_ordinals.index(current_highlight)
            else:
                current_position = next(
                    (
                        index
                        for index, item in enumerate(self.inventory_items)
                        if bool(getattr(item, "selected", False))
                    ),
                    0 if delta >= 0 else len(selectable_ordinals) - 1,
                )
            next_position = max(0, min(len(selectable_ordinals) - 1, current_position + int(delta)))
            target_ordinal = selectable_ordinals[next_position]
            try:
                self.highlighted = target_ordinal
            except Exception:
                pass
            try:
                self.scroll_to_highlight()
            except Exception:
                pass
            app = getattr(self, "app", None)
            if app is not None:
                try:
                    getattr(app, "_handle_inventory_option_highlight", lambda *_args: False)(
                        str(getattr(self, "id", "") or ""),
                        target_ordinal,
                    )
                except Exception:
                    pass

        def action_cursor_down(self) -> None:  # pragma: no cover - requires textual runtime
            self._move_inventory_cursor(1)

        def action_cursor_up(self) -> None:  # pragma: no cover - requires textual runtime
            self._move_inventory_cursor(-1)

        def action_select(self) -> None:  # pragma: no cover - requires textual runtime
            return

        def action_activate_inventory(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "itemize_inventory_panel":
                handled = bool(getattr(app, "_preview_itemize_item", lambda: False)())
                if handled:
                    return
            if widget_id == "review_scope_tree_panel":
                getattr(app, "_preview_review_scope_item", lambda: False)()

        def action_inventory_hold(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "itemize_inventory_panel":
                getattr(app, "_hold_itemize_item", lambda: False)()
            elif widget_id == "review_scope_tree_panel":
                getattr(app, "_hold_review_scope_item", lambda: False)()

        def action_toggle_inventory(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "review_scope_tree_panel":
                getattr(app, "_toggle_review_scope_item", lambda: False)()

        def action_toggle_inventory_decision(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "draft_scope_tree_panel":
                getattr(app, "_toggle_draft_decision_included", lambda: False)()

        def action_inventory_release(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "review_scope_tree_panel":
                getattr(app, "_release_review_scope_items", lambda: False)()

        def action_inventory_reorder_up(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "draft_scope_tree_panel":
                getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(-1)
            elif widget_id == "review_scope_tree_panel":
                getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(-1)

        def action_inventory_reorder_down(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is None:
                return
            widget_id = str(getattr(self, "id", "") or "")
            if widget_id == "draft_scope_tree_panel":
                getattr(app, "_move_selected_draft_review_item", lambda _delta: False)(1)
            elif widget_id == "review_scope_tree_panel":
                getattr(app, "_preview_move_review_scope_items", lambda _delta: False)(1)
else:  # pragma: no cover - optional dependency guard
    _FocusableTextualOptionList = Any

if TextualSelectionList is not None:  # pragma: no branch - optional dependency guard
    class _FocusableTextualSelectionList(TextualSelectionList):
        can_focus = True

        def _focus_from_pointer_event(self, event: Any) -> None:
            try:
                self.focus()
            except Exception:
                return
            if hasattr(event, "stop"):
                event.stop()

        def on_mouse_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_click(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def _on_option_list_option_highlighted(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            try:
                option_index = int(getattr(event, "option_index", -1) or -1)
            except Exception:
                option_index = -1
            if option_index < 0:
                return
            try:
                self.get_option_at_index(option_index)
            except Exception:
                return
            try:
                return super()._on_option_list_option_highlighted(event)
            except Exception:
                return
else:  # pragma: no cover - optional dependency guard
    _FocusableTextualSelectionList = Any

if TextualTree is not None and TextualBinding is not None:  # pragma: no branch - optional dependency guard
    class _FocusableTextualTree(TextualTree):
        can_focus = True
        BINDINGS = [
            TextualBinding("down", "cursor_down", "Down", show=False),
            TextualBinding("up", "cursor_up", "Up", show=False),
            TextualBinding("enter", "activate_inventory", "Activate", show=False),
            TextualBinding("h", "inventory_hold", "Hold", show=False),
            TextualBinding("x", "toggle_inventory", "Toggle", show=False),
            TextualBinding("r", "inventory_release", "Release", show=False),
            TextualBinding("shift+up", "inventory_reorder_up", "Move Earlier", show=False),
            TextualBinding("shift+down", "inventory_reorder_down", "Move Later", show=False),
            TextualBinding("k", "inventory_reorder_up", "Preview Earlier", show=False),
            TextualBinding("j", "inventory_reorder_down", "Preview Later", show=False),
        ]

        def __init__(self, label: Any, **kwargs: Any) -> None:
            super().__init__(label, **kwargs)
            self.show_root = False
            self.guide_depth = 4

        def _focus_from_pointer_event(self, event: Any) -> None:
            try:
                self.focus()
            except Exception:
                return
            if hasattr(event, "stop"):
                event.stop()

        def on_mouse_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)

        def on_mouse_scroll_up(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)
            try:
                self.scroll_up(animate=False)
            except Exception:
                pass
            try:
                current_y = int(getattr(getattr(self, "scroll_offset", None), "y", 0) or 0)
                self.scroll_to(y=max(0, current_y - 3), animate=False, force=True, immediate=True)
            except Exception:
                pass

        def on_mouse_scroll_down(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._focus_from_pointer_event(event)
            try:
                self.scroll_down(animate=False)
            except Exception:
                pass
            try:
                current_y = int(getattr(getattr(self, "scroll_offset", None), "y", 0) or 0)
                self.scroll_to(y=max(0, current_y + 3), animate=False, force=True, immediate=True)
            except Exception:
                pass

        def action_cursor_down(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is not None:
                widget_id = str(getattr(self, "id", "") or "")
                if widget_id == "subject_sources_panel":
                    getattr(app, "_move_research_source_cursor", lambda _delta: False)(1)
                    return
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_move_review_scope_cursor", lambda *_args: False)(1, phase)

        def action_cursor_up(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            if app is not None:
                widget_id = str(getattr(self, "id", "") or "")
                if widget_id == "subject_sources_panel":
                    getattr(app, "_move_research_source_cursor", lambda _delta: False)(-1)
                    return
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_move_review_scope_cursor", lambda *_args: False)(-1, phase)

        def action_activate_inventory(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_preview_review_scope_item", lambda *_args: False)(phase)

        def action_inventory_hold(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_hold_review_scope_item", lambda *_args: False)(phase)

        def action_toggle_inventory(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_toggle_review_scope_item", lambda *_args: False)(phase)

        def action_inventory_release(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_release_review_scope_items", lambda *_args: False)(phase)

        def action_inventory_reorder_up(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_preview_move_review_scope_items", lambda *_args: False)(-1, phase)

        def action_inventory_reorder_down(self) -> None:  # pragma: no cover - requires textual runtime
            app = getattr(self, "app", None)
            widget_id = str(getattr(self, "id", "") or "")
            if app is not None and widget_id != "subject_sources_panel":
                phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                getattr(app, "_preview_move_review_scope_items", lambda *_args: False)(1, phase)
else:  # pragma: no cover - optional dependency guard
    _FocusableTextualTree = Any

_CHAT_SLASH_COMMANDS = workstation_chat_slash_commands()
_CHAT_SLASH_COMMAND_HELP_LINES = {
    "/help": "/help  Show workstation chat and CLI usage.",
    "/apply-source-export": (
        "/apply-source-export  Apply the selected staged Gather source export preview back into staged source history."
    ),
    "/apply-source-set-export": (
        "/apply-source-set-export  Apply the selected Gather source set export preview back into staged source history."
    ),
    "/create-source-set": (
        "/create-source-set  Create a focused Gather source set from the selected staged source."
    ),
    "/create-source-set-from-query": (
        "/create-source-set-from-query <title> | <query> | [description]  Create an empty Gather source set from a topic/query."
    ),
    "/edit-source": (
        "/edit-source  Open the manual edit file for the selected staged Gather source."
    ),
    "/edit-source-set": (
        "/edit-source-set  Open the manual edit file for the selected Gather source set."
    ),
    "/curate-source": (
        "/curate-source  Open a Chat curation turn for the selected staged Gather source."
    ),
    "/merge-source": (
        "/merge-source  Open a Chat merge-back turn for the selected staged Gather source."
    ),
    "/curate-source-set": (
        "/curate-source-set  Open a Chat curation turn for the selected Gather source set."
    ),
    "/find-sources": (
        "/find-sources  Open a Chat discovery turn for the selected Gather source set using its saved query."
    ),
    "/merge-source-set": (
        "/merge-source-set  Open a Chat merge-back turn for the selected Gather source set."
    ),
    "/merge-set-sources": (
        "/merge-set-sources  Open a Chat merge-back turn for the staged sources inside the selected Gather source set."
    ),
    "/synthesize-source-set": (
        "/synthesize-source-set  Open a Chat synthesis turn for the selected Gather source set to summarize coverage and open questions."
    ),
    "/prepare-markdown": (
        "/prepare-markdown <text>  Ask the assistant to turn raw source text into research-ready markdown; "
        "use /prepare-last-assistant-markdown when the source is the most recent assistant reply, then use /start-research."
    ),
    "/prepare-last-assistant-markdown": (
        "/prepare-last-assistant-markdown  Ask the assistant to turn the most recent assistant reply into research-ready markdown; "
        "then use /start-research."
    ),
    "/start-research": (
        "/start-research  Preview staging of the last assistant markdown reply as a Gather source, then confirm before writing."
    ),
    "/start-research-into": (
        "/start-research-into <subject title>  Preview staging into one chosen subject as a Gather source, then confirm before writing."
    ),
    "/refresh-source": (
        "/refresh-source  Refresh the selected URL-backed staged Gather source into a new staged revision."
    ),
    "/resume-research-with-llm": (
        "/resume-research-with-llm <subject title>  Ask the assistant to study one existing subject and continue "
        "the research; use /start-research later to stage new markdown."
    ),
    "/research": "/research  Move focus to the Gather workflow tab.",
    "/sync-source-set": (
        "/sync-source-set  Refresh the URL-backed staged sources inside the selected Gather source set."
    ),
    "/list-skills": "/list-skills [query]  List visible skills, optionally filtered by query text.",
    "/describe-skill": (
        "/describe-skill <skill title>  Show one skill's declaration, inputs, outputs, and executor."
    ),
    "/permissions": "/permissions [skill title]  Show session capabilities or one skill's declared permissions.",
    "/workstation-root": "/workstation-root  Show the current workstation root path.",
    "/grant-permission": "/grant-permission <capability>  Add one workstation session capability.",
    "/import-skill": "/import-skill <skill_path>  Import a portable skill bundle directly from chat.",
    "/revoke-permission": "/revoke-permission <capability>  Remove one non-protected workstation session capability.",
    "/export-skill": "/export-skill <skill title> [destination_path]  Export one skill directly from chat.",
    "/exit": "/exit  End this chat session.",
    "/quit": "/quit  End this chat session.",
}
_YES_NO_CHOICES = ("yes", "no")
_WORKSPACE_PATH_SCAN_LIMIT = 160
_SUGGESTION_LIMIT = 3
_ACTIVITY_PANE_MAX_LINES = 80
_TRANSCRIPT_PANE_MAX_BLOCKS = 120
_ACTIVITY_STRIP_MAX_CHARS = 180
_ACTIVITY_STRIP_SUFFIXES = ("", ".", "..", "...")
_ACTIVITY_STRIP_RETENTION_SECONDS = 7.0
_TRANSCRIPT_BOTTOM_FOLLOW_SECONDS = 2.0
_SUBJECT_GATE_HEIGHT_UNITS = workstation_subject_gate_height_units()
_SHOW_ROUTED_LLM_PROMPT_IN_TRANSCRIPT = True
_FENCED_BLOCK_PATTERN = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)
_UNSET = object()
_SKILL_MATCH_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "i",
        "in",
        "into",
        "is",
        "it",
        "me",
        "of",
        "on",
        "or",
        "show",
        "skill",
        "skills",
        "tell",
        "the",
        "to",
        "use",
        "with",
    }
)


def _render_prompt_suggestion_text(suggestion: str) -> str:
    rendered = str(suggestion or "")
    stripped = rendered.strip()
    if rendered == stripped and stripped in _CHAT_SLASH_COMMAND_HELP_LINES:
        return _CHAT_SLASH_COMMAND_HELP_LINES[stripped]
    if rendered.endswith(" ") and stripped == "/resume-research-with-llm":
        return _CHAT_SLASH_COMMAND_HELP_LINES["/resume-research-with-llm"]
    if rendered.endswith(" ") and stripped == "/start-research-into":
        return _CHAT_SLASH_COMMAND_HELP_LINES["/start-research-into"]
    return rendered

_TEXTUAL_TAB_DOM_IDS = {
    "chat": "chat_tab",
    "learn_markdown": "learn_tab",
    "permissions": "permissions_tab",
    "activity": "activity_tab",
    "skills": "skills_tab",
}

_TEXTUAL_TAB_ORDER: tuple[str, ...] = (
    "chat_tab",
    "learn_tab",
    "itemize_tab",
    "draft_tab",
    "review_tab",
    "publication_tab",
    "permissions_tab",
    "activity_tab",
    "skills_tab",
)

_TEXTUAL_TAB_LAYOUT_KEYS: dict[str, str] = {
    "chat_tab": "chat",
    "learn_tab": "research",
    "itemize_tab": "itemize",
    "draft_tab": "draft",
    "review_tab": "review",
    "publication_tab": "publication",
    "permissions_tab": "permissions",
    "activity_tab": "activity",
    "skills_tab": "skills",
}

_TEXTUAL_PANE_DOM_IDS = {
    ("chat", "status"): "chat_status_panel",
    ("chat", "activity"): "chat_activity_panel",
    ("chat", "transcript"): "transcript",
    ("chat", "composer"): "composer",
    ("chat", "suggestions"): "suggestion_bar",
    ("chat", "hint"): "hintbar",
    ("learn_markdown", "actions"): "learn_actions_panel",
    ("learn_markdown", "learning"): "learn_result",
    ("permissions", "permissions"): "permissions",
    ("activity", "activity_feed"): "activity",
    ("skills", "skills"): "skills",
}

_TEXTUAL_TAB_TITLE_OVERRIDES = {
    "learn_tab": "Gather",
    "itemize_tab": "Itemize",
    "draft_tab": "Draft",
    "review_tab": "Review",
    "publication_tab": "Publication",
}

_SUBJECT_PHASE_TO_TAB_ID = {
    "research": "learn_tab",
    "itemize": "itemize_tab",
    "draft": "draft_tab",
    "review": "review_tab",
    "publication": "publication_tab",
}

_SUBJECT_TAB_ID_TO_PHASE = {
    tab_id: phase for phase, tab_id in _SUBJECT_PHASE_TO_TAB_ID.items()
}

_SUBJECT_PHASE_BUTTON_PREFIXES = {
    "research": "subject_research",
    "itemize": "subject_itemize",
    "draft": "subject_draft",
    "review": "subject_review",
    "publication": "subject_publication",
}

_TEXTUAL_MAXIMIZABLE_PANES: dict[str, dict[str, str]] = {
    "transcript": {"tab_id": "chat_tab", "outer_id": "transcript_panel", "wrapper_id": "transcript_panel"},
    "learn_result": {"tab_id": "learn_tab", "outer_id": "learn_result_panel", "wrapper_id": "learn_result_panel"},
    "subject_sources_panel": {
        "tab_id": "learn_tab",
        "outer_id": "subject_research_workbench",
        "wrapper_id": "subject_sources_panel_shell",
    },
    "subject_target_panel": {
        "tab_id": "learn_tab",
        "outer_id": "subject_target_panel_shell",
        "wrapper_id": "subject_target_panel_shell",
    },
    "itemize_result": {"tab_id": "itemize_tab", "outer_id": "itemize_result_panel", "wrapper_id": "itemize_result_panel"},
    "itemize_inventory_panel": {
        "tab_id": "itemize_tab",
        "outer_id": "subject_itemize_workbench",
        "wrapper_id": "itemize_inventory_wrapper",
    },
    "itemize_target_panel": {
        "tab_id": "itemize_tab",
        "outer_id": "itemize_target_panel_shell",
        "wrapper_id": "itemize_target_panel_shell",
    },
    "itemize_detail_panel": {
        "tab_id": "itemize_tab",
        "outer_id": "subject_itemize_workbench",
        "wrapper_id": "itemize_detail_wrapper",
    },
    "draft_scope_tree_panel": {
        "tab_id": "draft_tab",
        "outer_id": "draft_scope_workbench",
        "wrapper_id": "draft_scope_tree_wrapper",
    },
    "draft_scope_detail_panel": {
        "tab_id": "draft_tab",
        "outer_id": "draft_scope_workbench",
        "wrapper_id": "draft_scope_detail_wrapper",
    },
    "draft_model_main_panel": {
        "tab_id": "draft_tab",
        "outer_id": "draft_scope_workbench",
        "wrapper_id": "draft_model_main_wrapper",
    },
    "draft_result": {"tab_id": "draft_tab", "outer_id": "draft_result_panel", "wrapper_id": "draft_result_panel"},
    "review_scope_tree_panel": {
        "tab_id": "review_tab",
        "outer_id": "review_actions_panel",
        "wrapper_id": "review_scope_tree_wrapper",
    },
    "review_scope_detail_panel": {
        "tab_id": "review_tab",
        "outer_id": "review_actions_panel",
        "wrapper_id": "review_scope_detail_wrapper",
    },
    "review_result": {"tab_id": "review_tab", "outer_id": "review_result_panel", "wrapper_id": "review_result_panel"},
    "publication_scope_tree_panel": {
        "tab_id": "publication_tab",
        "outer_id": "publication_actions_panel",
        "wrapper_id": "publication_scope_tree_wrapper",
    },
    "publication_scope_detail_panel": {
        "tab_id": "publication_tab",
        "outer_id": "publication_actions_panel",
        "wrapper_id": "publication_scope_detail_wrapper",
    },
    "publication_result": {
        "tab_id": "publication_tab",
        "outer_id": "publication_result_panel",
        "wrapper_id": "publication_result_panel",
    },
    "permissions": {"tab_id": "permissions_tab", "outer_id": "permissions_panel", "wrapper_id": "permissions_panel"},
    "activity": {"tab_id": "activity_tab", "outer_id": "activity_panel", "wrapper_id": "activity_panel"},
    "skills": {"tab_id": "skills_tab", "outer_id": "skills_panel", "wrapper_id": "skills_panel"},
}

_TEXTUAL_CLICK_FOCUS_TARGETS: dict[str, str] = {
    "subject_sources_panel_shell": "subject_sources_panel",
    "subject_sources_panel": "subject_sources_panel",
    "subject_observation_panel": "subject_observation_panel",
    "subject_target_panel_shell": "subject_target_panel",
    "subject_target_panel": "subject_target_panel",
    "itemize_inventory_wrapper": "itemize_inventory_panel",
    "itemize_inventory_panel": "itemize_inventory_panel",
    "itemize_detail_wrapper": "itemize_detail_panel",
    "itemize_detail_panel": "itemize_detail_panel",
    "itemize_target_panel_shell": "itemize_target_panel",
    "itemize_target_panel": "itemize_target_panel",
    "draft_scope_tree_wrapper": "draft_scope_tree_panel",
    "draft_scope_tree_panel": "draft_scope_tree_panel",
    "draft_model_main_wrapper": "draft_model_main_panel",
    "draft_model_main_panel": "draft_model_main_panel",
    "draft_scope_detail_wrapper": "draft_scope_detail_panel",
    "draft_scope_detail_panel": "draft_scope_detail_panel",
    "review_scope_tree_wrapper": "review_scope_tree_panel",
    "review_scope_tree_panel": "review_scope_tree_panel",
    "review_scope_detail_wrapper": "review_scope_detail_panel",
    "review_scope_detail_panel": "review_scope_detail_panel",
    "publication_scope_tree_wrapper": "publication_scope_tree_panel",
    "publication_scope_tree_panel": "publication_scope_tree_panel",
    "publication_scope_detail_wrapper": "publication_scope_detail_panel",
    "publication_scope_detail_panel": "publication_scope_detail_panel",
}

_TEXTUAL_OPTION_LIST_PANEL_IDS = frozenset(
    {
        "itemize_inventory_panel",
    }
)

_TEXTUAL_TREE_PANEL_IDS = frozenset(
    {
        "review_scope_tree_panel",
        "detached_review_scope_tree_panel",
        "publication_scope_tree_panel",
    }
)

_TEXTUAL_TAB_SECTION_IDS: dict[str, tuple[str, ...]] = {
    "chat_tab": ("chat_status_panel", "chat_activity_panel", "transcript_panel", "chat_info_panel_shell", "composer", "suggestion_bar", "hintbar"),
    "learn_tab": (
        "research_gate_bar",
        "learn_actions_panel",
        "subject_research_workbench",
        "subject_target_panel_shell",
        "learn_info_panel_shell",
        "learn_result_panel",
    ),
    "itemize_tab": (
        "itemize_gate_bar",
        "itemize_actions_panel",
        "subject_itemize_workbench",
        "itemize_info_panel_shell",
        "itemize_target_panel_shell",
        "itemize_result_panel",
    ),
    "draft_tab": ("draft_gate_bar", "draft_actions_panel", "draft_scope_workbench", "draft_info_panel_shell", "draft_result_panel"),
    "review_tab": ("review_gate_bar", "review_actions_panel", "review_scope_workbench", "review_info_panel_shell", "review_result_panel", "review_status_panel"),
    "publication_tab": (
        "publication_gate_bar",
        "publication_actions_panel",
        "publication_scope_workbench",
        "publication_info_panel_shell",
        "publication_result_panel",
        "publication_status_panel",
    ),
    "permissions_tab": ("permissions_panel", "permissions_info_panel_shell"),
    "activity_tab": ("activity_panel", "activity_info_panel_shell"),
    "skills_tab": ("skills_panel", "skills_info_panel_shell"),
}

_TEXTUAL_HIDDEN_UTILITY_SECTION_IDS: frozenset[str] = frozenset(
    {
        "chat_info_panel_shell",
        "learn_info_panel_shell",
        "itemize_info_panel_shell",
        "draft_info_panel_shell",
        "review_info_panel_shell",
        "publication_info_panel_shell",
        "permissions_info_panel_shell",
        "activity_info_panel_shell",
        "skills_info_panel_shell",
        "subject_target_panel_shell",
        "learn_result_panel",
        "itemize_target_panel_shell",
        "itemize_result_panel",
        "draft_result_panel",
        "review_result_panel",
        "publication_result_panel",
    }
)


def _subject_nav_button_id(phase: str, direction: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{direction}_button"


def _subject_header_subject_id(phase: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_subject_display"


def _subject_controls_header_row_id(phase: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_controls_header_row"


def _subject_last_action_panel_id(phase: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_last_action_panel"


def _subject_gate_panel_id(phase: str, gate: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_panel"


def _subject_gate_summary_id(phase: str, gate: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_summary"


def _subject_gate_status_table_id(phase: str, gate: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_status_table"


def _subject_gate_next_label_id(phase: str, gate: str) -> str:
    return f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_next_label"


def _subject_gate_action_button_ids(phase: str, gate: str) -> tuple[str, str, str, str]:
    prefix = f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_action"
    return tuple(f"{prefix}_{index}_button" for index in range(1, 5))


def _subject_gate_action_prefix_ids(phase: str, gate: str) -> tuple[str, str, str, str]:
    prefix = f"{_SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]}_{gate}_gate_action"
    return tuple(f"{prefix}_{index}_prefix" for index in range(1, 5))


def _subject_gate_action_row_id(phase: str, gate: str) -> str:
    prefix = _SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]
    return f"{prefix}_{gate}_gate_action_row"


def _subject_action_button_ids(phase: str) -> tuple[str, str, str, str]:
    prefix = _SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]
    return tuple(f"{prefix}_action_{index}_button" for index in range(1, 5))


def _subject_phase_action_row_id(phase: str) -> str:
    prefix = _SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]
    return f"{prefix}_more_actions_row"


def _subject_current_step_text_with_last_action(current_step_text: str, last_action_text: str) -> str:
    current_step = str(current_step_text or "").strip()
    last_action = collapse_ws(last_action_text)
    if last_action and current_step:
        return f"Last Action: {last_action}\n\n{current_step}"
    if last_action:
        return f"Last Action: {last_action}"
    return current_step


def _literal_table_rows_from_lines(lines: Iterable[str]) -> tuple[tuple[str, str], ...]:
    """Keep rendered prose display-only; structure must come from the contract."""
    return tuple(
        ("", line)
        for raw_line in lines
        if (line := collapse_ws(str(raw_line or "")))
    )


def _wrap_subject_status_table_cell(text: str, *, width: int) -> tuple[str, int]:
    normalized = collapse_ws(text)
    if not normalized:
        return ("", 1)
    wrapped = textwrap.wrap(
        normalized,
        width=max(8, int(width or 0)),
        break_long_words=True,
        break_on_hyphens=True,
    ) or [normalized]
    return ("\n".join(wrapped), len(wrapped))


def _subject_secondary_gate_title(phase: str) -> str:
    normalized = collapse_ws(str(phase or "")).casefold()
    if normalized in {"research", "itemize", "draft"}:
        return mock_subject_status_title(normalized)
    return ""


_TEXTUAL_STRUCTURED_TABLE_IDS = frozenset(
    {
        _subject_gate_status_table_id("research", "publication"),
        _subject_gate_status_table_id("itemize", "publication"),
        _subject_gate_status_table_id("draft", "publication"),
        "subject_target_panel",
        "subject_observation_panel",
        "itemize_target_panel",
        "draft_model_main_panel",
        "itemize_detail_panel",
        "draft_scope_detail_panel",
        "review_scope_detail_panel",
        "publication_scope_detail_panel",
    }
)

_STRUCTURED_PANE_BUNDLE_KEYS: dict[str, tuple[str, str]] = {
    "subject_observation_panel": ("research", "research_observation"),
    "subject_target_panel": ("research", "research_target"),
    "itemize_detail_panel": ("itemize", "itemize_detail"),
    "itemize_target_panel": ("itemize", "itemize_target"),
    "draft_model_main_panel": ("draft", "draft_model_main"),
    "draft_scope_detail_panel": ("draft", "draft_detail"),
    "review_scope_detail_panel": ("review", "review_scope_detail"),
    "publication_scope_detail_panel": ("publication", "publication_scope_detail"),
}


def _subject_journal_button_id(phase: str) -> str:
    prefix = _SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]
    return f"{prefix}_journal_button"


def _subject_hidden_pane_button_id(phase: str) -> str:
    prefix = _SUBJECT_PHASE_BUTTON_PREFIXES[str(phase)]
    return f"{prefix}_hidden_pane_button"


def _subject_hidden_pane_button_label(phase: str) -> str:
    return {
        "research": "View Subject Assets",
        "itemize": "View Draft Handoff",
    }.get(collapse_ws(str(phase or "")).casefold(), "View Pane")


def _subject_hidden_pane_id(phase: str) -> str | None:
    return {
        "research": "subject_target_panel",
        "itemize": "itemize_target_panel",
    }.get(collapse_ws(str(phase or "")).casefold())


def _draft_detail_llm_button_id() -> str:
    return "draft_scope_detail_llm_button"


def _itemize_detail_llm_button_id() -> str:
    return "itemize_detail_llm_button"


def _research_detail_llm_button_id() -> str:
    return "subject_target_llm_button"


def _research_detail_manual_rephrase_button_id() -> str:
    return "subject_target_manual_rephrase_button"


def _research_sources_llm_button_id() -> str:
    return "subject_sources_llm_button"


def _research_sources_manual_rephrase_button_id() -> str:
    return "subject_sources_manual_rephrase_button"


def _research_source_collection_select_id() -> str:
    return "research_source_collection_select"


def _research_source_revision_baseline_select_id() -> str:
    return "research_source_revision_baseline_select"


def _research_source_collection_membership_switch_id() -> str:
    return "research_source_collection_membership_switch"


def _research_source_revision_history_table_title_id() -> str:
    return "research_source_revision_history_table_title"


def _research_source_revision_history_table_id() -> str:
    return "research_source_revision_history_table"


def _research_source_change_summary_table_title_id() -> str:
    return "research_source_change_summary_table_title"


def _research_source_change_summary_table_id() -> str:
    return "research_source_change_summary_table"


def _research_source_collection_member_export_status_table_title_id() -> str:
    return "research_source_collection_member_export_status_table_title"


def _research_source_collection_member_export_status_table_id() -> str:
    return "research_source_collection_member_export_status_table"


def _research_source_collection_member_revision_table_title_id() -> str:
    return "research_source_collection_member_revision_table_title"


def _research_source_collection_member_revision_table_id() -> str:
    return "research_source_collection_member_revision_table"


def _research_source_collection_merge_export_history_table_title_id() -> str:
    return "research_source_collection_merge_export_history_table_title"


def _research_source_collection_merge_export_history_table_id() -> str:
    return "research_source_collection_merge_export_history_table"


def _research_source_collection_actionable_export_table_title_id() -> str:
    return "research_source_collection_actionable_export_table_title"


def _research_source_collection_actionable_export_table_id() -> str:
    return "research_source_collection_actionable_export_table"


def _research_source_collection_export_applied_table_title_id() -> str:
    return "research_source_collection_export_applied_table_title"


def _research_source_collection_export_applied_table_id() -> str:
    return "research_source_collection_export_applied_table"


def _review_comparison_history_table_title_id() -> str:
    return "review_comparison_history_table_title"


def _review_comparison_history_table_id() -> str:
    return "review_comparison_history_table"


def _review_latest_receipt_table_title_id() -> str:
    return "review_latest_receipt_table_title"


def _review_latest_receipt_table_id() -> str:
    return "review_latest_receipt_table"


def _publication_build_artifacts_table_title_id() -> str:
    return "publication_build_artifacts_table_title"


def _publication_build_artifacts_table_id() -> str:
    return "publication_build_artifacts_table"


def _publication_build_receipt_table_title_id() -> str:
    return "publication_build_receipt_table_title"


def _publication_build_receipt_table_id() -> str:
    return "publication_build_receipt_table"


def _publication_latest_receipt_table_title_id() -> str:
    return "publication_latest_receipt_table_title"


def _publication_latest_receipt_table_id() -> str:
    return "publication_latest_receipt_table"


def _itemize_detail_manual_rephrase_button_id() -> str:
    return "itemize_detail_manual_rephrase_button"


def _draft_detail_manual_rephrase_button_id() -> str:
    return "draft_scope_detail_manual_rephrase_button"


def _itemize_decision_role_select_id() -> str:
    return "itemize_decision_role_select"


def _itemize_hold_switch_id() -> str:
    return "itemize_hold_switch"


def _draft_semantic_kind_select_id() -> str:
    return "draft_semantic_kind_select"


def _draft_render_kind_select_id() -> str:
    return "draft_render_kind_select"


def _draft_evidence_mode_select_id() -> str:
    return "draft_evidence_mode_select"


def _draft_transform_mode_select_id() -> str:
    return "draft_transform_mode_select"


def _draft_decision_included_switch_id() -> str:
    return "draft_decision_included_switch"


def _draft_model_construct_sort_select_id() -> str:
    return "draft_model_construct_sort_select"


def _draft_model_construct_lane_select_id() -> str:
    return "draft_model_construct_lane_select"


def _draft_model_transition_source_select_id() -> str:
    return "draft_model_transition_source_select"


def _draft_model_transition_target_select_id() -> str:
    return "draft_model_transition_target_select"


def _draft_model_policy_profile_select_id() -> str:
    return "draft_model_policy_profile_select"


def _draft_model_relation_wrapper_id(slot: int) -> str:
    return f"draft_model_relation_wrapper_{slot}"


def _draft_model_relation_label_id(slot: int) -> str:
    return f"draft_model_relation_label_{slot}"


def _draft_model_relation_selection_list_id(slot: int) -> str:
    return f"draft_model_relation_selection_list_{slot}"


def _draft_model_lens_tabs_id() -> str:
    return "draft_model_lens_tabs"


def _draft_model_lens_tab_id(lens: str) -> str:
    normalized = collapse_ws(str(lens or "")).casefold()
    if normalized not in {"frame", "model", "explore"}:
        normalized = "model"
    return f"draft_model_lens_tab_{normalized}"


def _review_publication_output_mode_select_id() -> str:
    return "review_publication_output_mode_select"


def _review_publication_section_plan_select_id() -> str:
    return "review_publication_section_plan_select"


def _review_publication_diff_baseline_select_id() -> str:
    return "review_publication_diff_baseline_select"


def _review_composition_unit_target_select_id() -> str:
    return "review_composition_unit_target_select"


def _review_composition_unit_included_switch_id() -> str:
    return "review_composition_unit_included_switch"


def _review_publication_section_target_select_id() -> str:
    return "review_publication_section_target_select"


def _review_publication_section_included_switch_id() -> str:
    return "review_publication_section_included_switch"


def _publication_composition_unit_target_select_id() -> str:
    return "publication_composition_unit_target_select"


def _publication_composition_unit_included_switch_id() -> str:
    return "publication_composition_unit_included_switch"


def _publication_section_target_select_id() -> str:
    return "publication_section_target_select"


def _publication_section_included_switch_id() -> str:
    return "publication_section_included_switch"


def _publication_output_mode_select_id() -> str:
    return "publication_output_mode_select"


def _publication_section_plan_select_id() -> str:
    return "publication_section_plan_select"


def _publication_diff_baseline_select_id() -> str:
    return "publication_diff_baseline_select"


def _publication_import_target_select_id() -> str:
    return "publication_import_target_select"


def _publication_import_included_switch_id() -> str:
    return "publication_import_included_switch"


def _publication_import_usage_select_id() -> str:
    return "publication_import_usage_select"


def _review_detail_llm_button_id() -> str:
    return "review_scope_detail_llm_button"


def _review_detail_manual_rephrase_button_id() -> str:
    return "review_scope_detail_manual_rephrase_button"


_PANE_EXPAND_LABEL = "+"
_PANE_RESTORE_LABEL = "-"

_TEXTUAL_INFO_PANEL_IDS: dict[str, tuple[str, str]] = {
    "chat_tab": ("chat_info_panel_shell", "chat_info_panel"),
    "learn_tab": ("learn_info_panel_shell", "learn_info_panel"),
    "itemize_tab": ("itemize_info_panel_shell", "itemize_info_panel"),
    "draft_tab": ("draft_info_panel_shell", "draft_info_panel"),
    "review_tab": ("review_info_panel_shell", "review_info_panel"),
    "publication_tab": ("publication_info_panel_shell", "publication_info_panel"),
    "permissions_tab": ("permissions_info_panel_shell", "permissions_info_panel"),
    "activity_tab": ("activity_info_panel_shell", "activity_info_panel"),
    "skills_tab": ("skills_info_panel_shell", "skills_info_panel"),
}

_TEXTUAL_INFO_PANE_TABS: dict[str, str] = {
    "transcript": "chat_tab",
    "subject_sources_panel": "learn_tab",
    "subject_target_panel": "learn_tab",
    "learn_result": "learn_tab",
    "itemize_inventory_panel": "itemize_tab",
    "itemize_detail_panel": "itemize_tab",
    "itemize_target_panel": "itemize_tab",
    "itemize_result": "itemize_tab",
    "draft_scope_tree_panel": "draft_tab",
    "draft_model_main_panel": "draft_tab",
    "draft_scope_detail_panel": "draft_tab",
    "draft_result": "draft_tab",
    "review_scope_tree_panel": "review_tab",
    "review_scope_detail_panel": "review_tab",
    "review_result": "review_tab",
    "publication_scope_tree_panel": "publication_tab",
    "publication_scope_detail_panel": "publication_tab",
    "publication_result": "publication_tab",
    "permissions": "permissions_tab",
    "activity": "activity_tab",
    "skills": "skills_tab",
}

def _textual_pane_title_widget_id(pane_id: str) -> str:
    return f"{collapse_ws(str(pane_id or ''))}_title"


def _textual_pane_info_button_id(pane_id: str) -> str:
    return f"{collapse_ws(str(pane_id or ''))}_info_button"


def _textual_info_panel_title_id(tab_id: str) -> str:
    return f"{collapse_ws(str(tab_id or ''))}_info_title"


def _textual_detached_pane_title_id() -> str:
    return "detached_pane_title"


def _textual_detached_pane_info_button_id() -> str:
    return "detached_pane_info_button"


def _textual_detached_pane_dismiss_button_id() -> str:
    return "detached_pane_dismiss_button"


def _pane_item_attribute_value(item: Any, key: str) -> str:
    normalized_key = collapse_ws(key)
    return next(
        (
            str(getattr(row, "value", "") or "")
            for row in (getattr(item, "attributes", ()) or ())
            if collapse_ws(str(getattr(row, "label", "") or "")) == normalized_key
        ),
        "",
    )


def _textual_itemize_item_label(item: Any) -> str:
    status = {
        "candidate": "c",
        "promoted": "p",
        "rejected": "r",
        "merged": "m",
        "split": "s",
    }.get(collapse_ws(str(getattr(item, "status", "") or "")).casefold(), "?")
    prefix = " ".join(
        part
        for part in (
            ">" if bool(getattr(item, "selected", False)) else " ",
            "[h]" if bool(getattr(item, "held", False)) else "   ",
            f"[{status}]",
        )
        if part
    )
    label = collapse_ws(str(getattr(item, "label", "") or "")) or "<unnamed item>"
    decision_role = collapse_ws(_pane_item_attribute_value(item, "decision_role"))
    semantic_kind = collapse_ws(str(getattr(item, "semantic_kind", "") or ""))
    if decision_role:
        label = f"{decision_role} - {label}"
    elif semantic_kind:
        label = f"{label} ({semantic_kind})"
    return f"{prefix} {label}".rstrip()


def _subject_journal_pane_id(phase: str) -> str:
    return {
        "research": "learn_result",
        "itemize": "itemize_result",
        "draft": "draft_result",
        "review": "review_result",
        "publication": "publication_result",
    }.get(collapse_ws(str(phase or "")).casefold(), "learn_result")


def _textual_pane_toggle_button_id(pane_id: str) -> str:
    return f"{collapse_ws(str(pane_id or ''))}_toggle_button"


def _textual_pane_id_from_focus_id(focus_id: str) -> str | None:
    normalized_focus_id = collapse_ws(str(focus_id or ""))
    if normalized_focus_id in _TEXTUAL_MAXIMIZABLE_PANES:
        return normalized_focus_id
    for pane_id in _TEXTUAL_MAXIMIZABLE_PANES:
        if normalized_focus_id == _textual_pane_toggle_button_id(pane_id):
            return pane_id
    return None


def _textual_tab_dom_id(tab_key: str) -> str:
    return _TEXTUAL_TAB_DOM_IDS.get(str(tab_key or ""), f"{tab_key}_tab")


def _textual_tab_key_from_dom_id(dom_id: str) -> str:
    normalized = str(dom_id or "")
    for tab_key, candidate in _TEXTUAL_TAB_DOM_IDS.items():
        if candidate == normalized:
            return tab_key
    return normalized.removesuffix("_tab")


def _textual_tab_layout_key(tab_id: str) -> str:
    return _TEXTUAL_TAB_LAYOUT_KEYS.get(str(tab_id or ""), _textual_tab_key_from_dom_id(tab_id))


def _textual_pane_dom_id(tab_key: str, pane_key: str) -> str:
    return _TEXTUAL_PANE_DOM_IDS[(str(tab_key or ""), str(pane_key or ""))]


def _textual_bold_border_title(title: str) -> Any:
    rendered = str(title or "")
    if RichText is not None:
        return RichText(rendered, style="bold")
    return f"[bold]{rendered}[/bold]"


def _textual_border_title(title: str) -> Any:
    rendered = str(title or "")
    if RichText is not None:
        return RichText(rendered)
    return rendered


def _layout_height_units(tab_key: str, pane_key: str, *, default: int) -> int:
    pane = workstation_pane_layout(tab_key, pane_key)
    value = pane.get("height_units", pane.get("min_height_units", default))
    try:
        return max(1, int(value))
    except Exception:
        return default


def _layout_text_color(tab_key: str, pane_key: str, *, default: str) -> str:
    role = workstation_pane_text_role(tab_key, pane_key)
    return {
        "default": _DEFAULT_TEXT_COLOR,
        "muted": _MUTED_TEXT_COLOR,
        "accent": _ACTIVE_TEXT_C_COLOR,
        "prompt": _PROMPT_TEXT_COLOR,
    }.get(role, default)


_CHAT_ACTIVITY_HEIGHT_UNITS = _layout_height_units("chat", "activity", default=3)
_CHAT_SUGGESTIONS_HEIGHT_UNITS = _layout_height_units("chat", "suggestions", default=8)
_CHAT_HINT_HEIGHT_UNITS = _layout_height_units("chat", "hint", default=1)
_CHAT_STATUS_MIN_HEIGHT_UNITS = _layout_height_units("chat", "status", default=2)
_LEARN_ACTIONS_MIN_HEIGHT_UNITS = _layout_height_units("learn_markdown", "actions", default=4)
_LEARN_PROGRESS_MIN_HEIGHT_UNITS = _layout_height_units("learn_markdown", "progress", default=2)
_CHAT_ACTIVITY_TEXT_COLOR = _layout_text_color("chat", "activity", default=_ACTIVE_TEXT_C_COLOR)
_CHAT_HINT_TEXT_COLOR = _layout_text_color("chat", "hint", default=_MUTED_TEXT_COLOR)

_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_DIM = "\033[2m"


def _ansi_color_escape(color: str) -> str:
    normalized = str(color or "").strip().casefold()
    ansi_named = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "bright_black": "\033[90m",
        "bright_red": "\033[91m",
        "bright_green": "\033[92m",
        "bright_yellow": "\033[93m",
        "bright_blue": "\033[94m",
        "bright_magenta": "\033[95m",
        "bright_cyan": "\033[96m",
        "bright_white": "\033[97m",
    }
    if normalized in ansi_named:
        return ansi_named[normalized]
    if normalized.startswith("ansi_"):
        return ansi_named.get(normalized[5:], "\033[39m")
    if normalized.startswith("#") and len(normalized) == 7:
        red = int(normalized[1:3], 16)
        green = int(normalized[3:5], 16)
        blue = int(normalized[5:7], 16)
        return f"\033[38;2;{red};{green};{blue}m"
    return "\033[39m"


_ANSI_DEFAULT_TEXT = _ansi_color_escape(_DEFAULT_TEXT_COLOR)
_ANSI_CYAN = _ansi_color_escape(_ACTIVE_TEXT_C_COLOR)
_ANSI_GREEN = _ansi_color_escape(_PROMPT_TEXT_COLOR)
_ANSI_YELLOW = _ansi_color_escape(_ACTIVE_TEXT_C_COLOR)
_ANSI_TIME = _ansi_color_escape(_TIME_TEXT_COLOR)
_ANSI_USER = _ansi_color_escape(_USER_TEXT_COLOR)
_ANSI_USER_BOLD = f"{_ANSI_BOLD}{_ANSI_USER}"
_ANSI_ASSISTANT = _ansi_color_escape(_ASSISTANT_TEXT_COLOR)
_ANSI_ASSISTANT_BOLD = f"{_ANSI_BOLD}{_ANSI_ASSISTANT}"
_ANSI_SYSTEM = _ansi_color_escape(_SYSTEM_TEXT_COLOR)
_ANSI_SYSTEM_BOLD = f"{_ANSI_BOLD}{_ANSI_SYSTEM}"

_RICH_USER_STYLE = _USER_TEXT_COLOR
_RICH_ASSISTANT_STYLE = _ASSISTANT_TEXT_COLOR
_RICH_SYSTEM_STYLE = _SYSTEM_TEXT_COLOR
_RICH_DEFAULT_STYLE = _DEFAULT_TEXT_COLOR
_RICH_TIME_STYLE = _TIME_TEXT_COLOR
_RICH_PERMISSION_TITLE_STYLE = f"bold {_ACTIVE_TEXT_A_COLOR}"
_RICH_SKILL_TITLE_STYLE = f"bold {_ACTIVE_TEXT_A_COLOR}"
_RICH_ACTIVITY_TREE_STYLE = _TIME_TEXT_COLOR
_RICH_ACTIVITY_MAIN_STYLE = _DEFAULT_TEXT_COLOR
_RICH_ACTIVITY_IN_STYLE = f"bold {_ACTIVE_TEXT_A_COLOR}"
_RICH_ACTIVITY_OUT_STYLE = f"bold {_ASSISTANT_TEXT_COLOR}"
_RICH_ACTIVITY_REASON_STYLE = f"bold {_ACTIVE_TEXT_C_COLOR}"
_RICH_ACTIVITY_META_STYLE = f"bold {_MUTED_TEXT_COLOR}"
_RICH_ACTIVITY_TIME_STYLE = _TIME_TEXT_COLOR

TEXTUAL_CHAT_CSS = f"""
Screen {{
    layout: vertical;
    background: {_PAGE_BACKGROUND};
    color: {_DEFAULT_TEXT_COLOR};
    layers: base overlay chrome;
}}

.ActiveArea {{
    background: {_ACTIVE_AREA_BACKGROUND};
}}

.InactiveArea {{
    background: {_INACTIVE_AREA_BACKGROUND};
}}

#tab_bar {{
    layer: chrome;
    dock: top;
    height: auto;
    margin: 0 1 0 1;
    padding: 0;
    background: {_PAGE_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
}}

.tab_button {{
    height: 3;
    margin: 0 1 0 0;
    padding: 0 2;
    background: transparent;
    color: {_INACTIVE_TEXT_A_COLOR};
    text-style: none;
    content-align: center middle;
    border: none;
}}

.tab_button_active {{
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
    border: round {_ACTIVE_AREA_FRAME};
}}

#root_tabs {{
    height: 1fr;
    margin: 1 1 0 1;
    background: {_PAGE_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0;
}}

#detached_pane_shell {{
    height: 1fr;
    margin: 1 1 0 1;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
}}

.tab_body {{
    height: 1fr;
}}

#chat_tab {{
    height: 1fr;
}}

#chat_status_panel {{
    height: auto;
    min-height: 1;
    padding: 0 1;
    margin-bottom: 0;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
}}

#chat_activity_panel {{
    height: {_CHAT_ACTIVITY_HEIGHT_UNITS};
    min-height: {_CHAT_ACTIVITY_HEIGHT_UNITS};
    padding: 0 1;
    margin: 0 0 1 0;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    color: {_CHAT_ACTIVITY_TEXT_COLOR};
    content-align: left middle;
}}

#transcript_panel {{
    height: 1fr;
    background: {_PAGE_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
    padding: 0 1;
}}

.max_panel_shell {{
    height: 1fr;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
}}

.max_panel_header {{
    height: 3;
    min-height: 3;
    margin: 0 0 0 0;
    padding: 0 1;
    align: left middle;
    background: transparent;
}}

.max_panel_header_spacer {{
    width: 1fr;
}}

.pane_header_title {{
    width: 1fr;
    height: 3;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
    content-align: left middle;
}}

.pane_toggle_button {{
    min-width: 6;
    height: 3;
    background: {_INACTIVE_AREA_BACKGROUND};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: none;
    border: round {_INACTIVE_AREA_FRAME};
    content-align: center middle;
}}

.pane_toggle_button:hover,
.pane_toggle_button:focus,
.pane_toggle_button.-active {{
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: none;
    border: round {_ACTIVE_AREA_FRAME};
}}

.pane_toggle_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: {_CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR};
    border: round {_CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR};
}}

.pane_icon_button {{
    width: 5;
    min-width: 5;
    height: 3;
    background: transparent;
    color: {_INACTIVE_TEXT_A_COLOR};
    text-style: bold;
    border: none;
    padding: 0 1;
    content-align: center middle;
}}

.pane_icon_button:hover,
.pane_icon_button:focus,
.pane_icon_button.-active {{
    background: transparent;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
    border: none;
}}

.pane_icon_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: transparent;
    border: none;
}}

.pane_header_text_button {{
    min-width: 4;
    height: 3;
    background: transparent;
    color: {_INACTIVE_TEXT_A_COLOR};
    text-style: none;
    border: none;
    padding: 0 1;
    content-align: center middle;
}}

.pane_header_text_button:hover,
.pane_header_text_button:focus,
.pane_header_text_button.-active {{
    background: transparent;
    color: {_INACTIVE_TEXT_A_COLOR};
    text-style: bold;
    border: none;
}}

.pane_header_text_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: transparent;
    border: none;
}}

#transcript,
.max_panel_body_log {{
    height: 1fr;
    background: transparent;
    border: none;
    padding: 0;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

.subject_target_table_title {{
    height: 1;
    min-height: 1;
    margin: 0 1;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
}}

.subject_target_table {{
    height: 8;
    min-height: 6;
    margin: 0 0 1 0;
    background: transparent;
    border: none;
}}

.result_table_title {{
    height: 1;
    min-height: 1;
    margin: 0 1;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
}}

.result_table {{
    height: 6;
    min-height: 4;
    margin: 0 0 1 0;
    background: transparent;
    border: none;
}}

#review_comparison_history_table {{
    height: 9;
    min-height: 7;
}}

.inventory_option_list > .option-list--option {{
    padding: 0;
}}

.inventory_option_list > .option-list--option-disabled {{
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
}}

.transcript_copy_button {{
    min-width: 6;
    background: transparent;
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: none;
    border: none;
}}

.transcript_copy_button:hover,
.transcript_copy_button:focus,
.transcript_copy_button.-active {{
    background: transparent;
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: none;
    border: none;
}}

.transcript_copy_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: transparent;
    border: none;
}}

#learn_tab,
#itemize_tab,
#draft_tab,
#review_tab,
#publication_tab,
#permissions_tab,
#activity_tab,
#skills_tab {{
    height: 1fr;
}}

#activity {{
    height: 1fr;
    background: transparent;
    border: none;
    padding: 0;
}}

#learn_actions_panel,
#itemize_actions_panel,
#draft_actions_panel,
#review_actions_panel,
#publication_actions_panel {{
    height: auto;
    min-height: 6;
    padding: 0 1;
    margin-bottom: 0;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
}}

#learn_ingress_panel {{
    height: auto;
    margin-top: 1;
    margin-bottom: 0;
    color: {_MUTED_TEXT_COLOR};
}}

#review_status_panel,
#publication_status_panel {{
    height: auto;
    min-height: {_LEARN_PROGRESS_MIN_HEIGHT_UNITS};
    padding: 0 1;
    margin-top: 1;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
}}

#learn_result_panel,
#itemize_result_panel,
#draft_result_panel,
#review_result_panel,
#publication_result_panel {{
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
}}

#learn_result,
#itemize_result,
#draft_result,
#review_result,
#publication_result,
#permissions,
#skills {{
    height: 1fr;
    background: transparent;
    border: none;
    padding: 0;
}}

#learn_result {{
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#itemize_result {{
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#draft_result {{
    height: 9;
    min-height: 9;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#review_result {{
    height: 9;
    min-height: 9;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#publication_result {{
    height: 9;
    min-height: 9;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#draft_scope_workbench,
#review_scope_workbench,
#publication_scope_workbench {{
    width: 1fr;
    height: 1fr;
    min-height: 22;
    margin-bottom: 1;
}}

.review_scope_panel_wrapper {{
    width: 1fr;
    height: 1fr;
    background: {_ACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
}}

#draft_scope_tree_panel,
#draft_model_main_panel,
#draft_scope_detail_panel,
#review_scope_tree_panel,
#review_scope_detail_panel,
#publication_scope_tree_panel,
#publication_scope_detail_panel,
#detached_review_scope_tree_panel {{
    width: 1fr;
    height: 1fr;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
    background: transparent;
    border: none;
    padding: 0;
}}

.inventory_tree {{
    color: {_DEFAULT_TEXT_COLOR};
    background: transparent;
}}

.inventory_tree > .tree--label {{
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
}}

.inventory_tree > .tree--guides {{
    color: {_INACTIVE_AREA_FRAME};
}}

.inventory_tree > .tree--guides-hover {{
    color: {_ACTIVE_AREA_FRAME};
}}

.inventory_tree > .tree--guides-selected {{
    color: {_ACTIVE_AREA_FRAME};
}}

.inventory_tree > .tree--cursor {{
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    background: {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
    text-style: bold;
}}

.inventory_tree > .tree--highlight-line {{
    background: rgba(0, 0, 0, 0);
}}

#draft_scope_tree_wrapper,
#draft_model_main_wrapper,
#review_scope_tree_wrapper {{
    margin-right: 1;
}}

#draft_scope_tree_wrapper {{
    min-width: 34;
}}

#draft_model_main_wrapper {{
    min-width: 44;
}}

#draft_scope_detail_wrapper {{
    min-width: 38;
}}

.action_button {{
    width: 1fr;
    margin-bottom: 1;
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: none;
    border: round {_CONTROL_BUTTON_BACKGROUND_COLOR};
}}

.action_button:hover,
.action_button:focus,
.action_button.-active {{
    background: {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    text-style: bold;
    border: round {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
}}

.subject_action_row {{
    height: 3;
}}

.subject_phase_action_row {{
    height: 3;
}}

.subject_action_row_spacer {{
    width: 1fr;
}}

.subject_choice_row {{
    height: auto;
    margin-top: 1;
}}

.subject_choice_row_grouped {{
    margin-top: 0;
}}

.subject_choice_group {{
    height: auto;
    margin-top: 1;
}}

.subject_choice_group_row {{
    height: auto;
    margin-top: 1;
}}

.subject_choice_group_row > .subject_choice_group {{
    width: 1fr;
    margin-top: 0;
    margin-right: 1;
}}

.subject_choice_group_row > .subject_choice_group:last-child {{
    margin-right: 0;
}}

.subject_choice_group_title {{
    height: 1;
    margin-bottom: 0;
    color: {_ACTIVE_TEXT_F_COLOR};
    text-style: bold;
}}

.subject_choice_field {{
    width: 34;
    max-width: 34;
    height: auto;
}}

.subject_choice_tabs_field {{
    width: 1fr;
    height: auto;
}}

.subject_choice_list_field {{
    width: 1fr;
    height: auto;
}}

.subject_choice_switch_field {{
    width: 18;
    max-width: 18;
    height: auto;
}}

#publication_plan_support_row > .subject_choice_group {{
    min-width: 0;
}}

#review_selection_group_row > .subject_choice_group,
#publication_selection_group_row > .subject_choice_group {{
    min-width: 0;
}}

#publication_choice_row > .subject_choice_field,
#publication_import_choice_row > .subject_choice_field {{
    width: 1fr;
    max-width: 100%;
    min-width: 16;
}}

#publication_import_choice_row > .subject_choice_switch_field {{
    width: 14;
    max-width: 14;
}}

.subject_choice_label {{
    height: 1;
    margin-bottom: 0;
    color: {_ACTIVE_TEXT_F_COLOR};
}}

.subject_choice_select {{
    width: 1fr;
    height: 3;
    color: {_ACTIVE_TEXT_A_COLOR};
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_choice_tabs {{
    width: 1fr;
    height: 3;
}}

.subject_choice_tabs Tab {{
    color: {_ACTIVE_TEXT_D_COLOR};
    background: transparent;
    text-style: none;
}}

.subject_choice_tabs Tab:hover,
.subject_choice_tabs Tab:focus {{
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    background: transparent;
    text-style: bold;
}}

.subject_choice_tabs Tab.-active {{
    color: {_ACTIVE_TEXT_A_COLOR};
    background: transparent;
    text-style: underline bold;
}}

.subject_choice_select > SelectCurrent {{
    color: {_ACTIVE_TEXT_A_COLOR};
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
}}

.subject_choice_select > SelectCurrent Static#label {{
    color: {_ACTIVE_TEXT_A_COLOR};
}}

.subject_choice_select > SelectCurrent.-has-value Static#label {{
    color: {_ACTIVE_TEXT_A_COLOR};
}}

.subject_choice_select > SelectCurrent .arrow {{
    color: {_ACTIVE_TEXT_A_COLOR};
}}

.subject_choice_select:focus > SelectCurrent,
.subject_choice_select.-expanded > SelectCurrent {{
    color: {_ACTIVE_TEXT_A_COLOR};
    background: {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
}}

.subject_choice_select > SelectOverlay {{
    color: {_ACTIVE_TEXT_D_COLOR};
    background: {_ACTIVE_AREA_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_choice_select:disabled,
.subject_choice_select:disabled > SelectCurrent {{
    color: {_INACTIVE_TEXT_A_COLOR};
    background: {_SUBJECT_CONTROL_BACKGROUND};
}}

.subject_choice_select:disabled > SelectCurrent Static#label,
.subject_choice_select:disabled > SelectCurrent.-has-value Static#label,
.subject_choice_select:disabled > SelectCurrent .arrow {{
    color: {_INACTIVE_TEXT_A_COLOR};
}}

.subject_choice_selection_list {{
    width: 1fr;
    height: 7;
    min-height: 7;
    color: {_SUBJECT_CONTROL_TEXT_COLOR};
    background: {_SUBJECT_CONTROL_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_choice_selection_list:focus {{
    background: {_SUBJECT_CONTROL_ACTIVE_BACKGROUND};
    border: round {_ACTIVE_TEXT_B_COLOR};
}}

.subject_choice_selection_list:disabled {{
    color: {_ACTIVE_TEXT_F_COLOR};
    background: {_SUBJECT_CONTROL_DISABLED_BACKGROUND};
}}

.subject_choice_selection_list > .option-list--option {{
    color: {_SUBJECT_CONTROL_TEXT_COLOR};
}}

.subject_choice_selection_list > .option-list--option-highlighted {{
    color: {_CONTROL_BUTTON_TEXT_COLOR};
    background: {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
}}

.subject_choice_selection_list > .option-list--option-disabled {{
    color: {_ACTIVE_TEXT_F_COLOR};
}}

.subject_choice_selection_list > .selection-list--button,
.subject_choice_selection_list > .selection-list--button-highlighted,
.subject_choice_selection_list > .selection-list--button-selected,
.subject_choice_selection_list > .selection-list--button-selected-highlighted {{
    color: {_CONTROL_BUTTON_TEXT_COLOR};
}}

.subject_choice_switch {{
    width: 8;
    min-width: 8;
    height: 3;
    padding: 0 1;
    color: {_SUBJECT_CONTROL_TEXT_COLOR};
    background: {_SUBJECT_CONTROL_DISABLED_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_choice_switch:hover {{
    background: {_SUBJECT_CONTROL_BACKGROUND};
}}

.subject_choice_switch:focus {{
    background: {_SUBJECT_CONTROL_ACTIVE_BACKGROUND};
    border: round {_ACTIVE_TEXT_B_COLOR};
}}

.subject_choice_switch > .switch--slider {{
    background: {_ACTIVE_AREA_BACKGROUND};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
}}

.subject_choice_switch.-on {{
    background: #1c6b46;
    border: round #2fa36d;
}}

.subject_choice_switch.-on > .switch--slider {{
    background: #8fe0b0;
    color: {_CONTROL_BUTTON_TEXT_COLOR};
}}

.subject_choice_switch.-on:hover {{
    background: #227b52;
}}

.subject_choice_switch.-on:focus {{
    background: #227b52;
    border: round #49c788;
}}

.subject_choice_switch:disabled {{
    color: {_ACTIVE_TEXT_F_COLOR};
    background: {_SUBJECT_CONTROL_DISABLED_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_choice_switch:disabled > .switch--slider {{
    background: {_ACTIVE_AREA_BACKGROUND};
    color: {_CONTROL_BUTTON_TEXT_COLOR};
}}

.subject_gate_row {{
    height: auto;
    margin-bottom: 1;
}}

.subject_gate_bar {{
    height: {_SUBJECT_GATE_HEIGHT_UNITS};
    margin-bottom: 1;
}}

.subject_gate_panel {{
    width: 1fr;
    height: 1fr;
    padding: 0 2;
    margin-right: 1;
    background: {_ACTIVE_AREA_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_gate_panel_last {{
    margin-right: 0;
}}

.subject_gate_summary {{
    width: 1fr;
    height: 1fr;
    padding: 0 1 0 0;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
    color: {_DEFAULT_TEXT_COLOR};
}}

.subject_gate_status_table {{
    width: 1fr;
    height: 1fr;
    margin: 0;
    overflow-x: hidden;
    overflow-y: auto;
    background: transparent;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

.subject_gate_next_label {{
    width: 1fr;
    height: auto;
    margin-top: 1;
    color: {_DEFAULT_TEXT_COLOR};
}}

.subject_gate_action_row {{
    height: auto;
    margin-top: 1;
}}

.subject_gate_action_slot {{
    width: auto;
    height: auto;
    margin-right: 1;
}}

.subject_gate_action_slot_last {{
    margin-right: 0;
}}

.subject_gate_action_prefix {{
    width: auto;
    height: 1;
    min-height: 1;
    margin-bottom: 0;
    content-align: center bottom;
    color: {_INACTIVE_TEXT_A_COLOR};
    text-style: bold;
}}

.subject_gate_action_button {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    height: 3;
    padding: 0 1;
    background: {_CONTROL_BUTTON_BACKGROUND_COLOR};
    color: {_DEFAULT_TEXT_COLOR};
    text-style: bold;
    border: round {_CONTROL_BUTTON_BACKGROUND_COLOR};
    content-align: center middle;
}}

.subject_gate_action_button_compact {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    padding: 0 1;
    color: {_DEFAULT_TEXT_COLOR};
}}

.subject_gate_action_button_last {{
    margin-right: 0;
}}

.subject_gate_action_button_placeholder {{
    background: transparent;
    color: transparent;
    border: none;
}}

.subject_gate_action_button:hover,
.subject_gate_action_button:focus,
.subject_gate_action_button.-active {{
    background: {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
    color: {_DEFAULT_TEXT_COLOR};
    text-style: bold;
    border: round {_CONTROL_BUTTON_ACTIVE_BACKGROUND_COLOR};
}}

.subject_gate_action_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR};
}}

.subject_gate_action_button_phase_nav {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    height: 3;
    padding: 0 1;
    margin-right: 1;
    background: transparent;
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_INACTIVE_AREA_FRAME};
    content-align: center middle;
}}

.subject_gate_action_button_phase_nav:hover,
.subject_gate_action_button_phase_nav:focus,
.subject_gate_action_button_phase_nav.-active {{
    background: {_INACTIVE_AREA_BACKGROUND};
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_action_button {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    height: 3;
    padding: 0 1;
    margin-right: 1;
    background: transparent;
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_INACTIVE_AREA_FRAME};
}}

.secondary_action_button {{
    background: transparent;
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_INACTIVE_AREA_FRAME};
}}

.subject_phase_action_button {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    text-wrap: nowrap;
}}

.subject_action_button:hover,
.subject_action_button:focus,
.subject_action_button.-active {{
    background: {_INACTIVE_AREA_BACKGROUND};
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_action_button:disabled,
.action_button:disabled {{
    color: {_DISABLED_TEXT_COLOR};
    background: {_CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR};
    border: round {_CONTROL_BUTTON_DISABLED_BACKGROUND_COLOR};
}}

.subject_controls_header_row {{
    height: auto;
    margin-bottom: 0;
}}

.subject_header_main {{
    width: 1fr;
    height: auto;
    margin-right: 1;
}}

.subject_page_header_row {{
    height: auto;
    margin: 1 0;
}}

.subject_page_title {{
    width: 1fr;
    height: 3;
    margin: 0;
    padding: 0 0 0 1;
    content-align: left middle;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
}}

.subject_page_nav_row {{
    width: auto;
    height: 3;
}}

.subject_flow_header {{
    width: 1fr;
    margin-bottom: 0;
    color: {_MUTED_TEXT_COLOR};
}}

.subject_header_sidebar {{
    width: 40;
    min-width: 40;
    height: auto;
}}

.subject_sidebar_nav_row {{
    height: 3;
}}

.subject_sidebar_utility_row {{
    height: 3;
    margin-top: 1;
}}

.subject_sidebar_utility_spacer {{
    width: 1fr;
}}

.subject_header_subject {{
    width: 1fr;
    height: 2;
    min-height: 2;
    margin-bottom: 1;
    content-align: left middle;
    color: {_ACTIVE_TEXT_A_COLOR};
    text-style: bold;
}}

.subject_header_utility_button {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    height: 3;
    padding: 0 1;
    margin-left: 1;
    background: transparent;
    color: {_DEFAULT_TEXT_COLOR};
    content-align: center middle;
    text-wrap: nowrap;
    text-style: none;
    border: round {_INACTIVE_AREA_FRAME};
}}

.subject_header_utility_button:hover,
.subject_header_utility_button:focus,
.subject_header_utility_button.-active {{
    background: {_INACTIVE_AREA_BACKGROUND};
    color: {_DEFAULT_TEXT_COLOR};
    text-style: none;
    border: round {_ACTIVE_AREA_FRAME};
}}

.subject_nav_button {{
    width: auto;
    min-width: 0;
    max-width: 100w;
    text-wrap: nowrap;
}}

#composer {{
    layout: horizontal;
    height: 3;
    margin-top: 0;
    padding: 0 1;
    background: {_PAGE_BACKGROUND};
    border: round {_ACTIVE_AREA_FRAME};
}}

#prompt_label {{
    width: 16;
    content-align: center middle;
    color: {_PROMPT_TEXT_COLOR};
    text-style: bold;
}}

#input {{
    width: 1fr;
    border: none;
    background: transparent;
    color: {_ACTIVE_TEXT_B_COLOR};
}}

#input > .input--placeholder {{
    color: {_ACTIVE_TEXT_C_COLOR};
}}

#input:disabled {{
    color: {_DISABLED_TEXT_COLOR};
}}

#inline_hint {{
    width: 24;
    min-width: 12;
    padding-right: 1;
    content-align: left middle;
    color: {_MUTED_TEXT_COLOR};
}}

#hintbar {{
    height: {_CHAT_HINT_HEIGHT_UNITS};
    margin-top: 0;
    color: {_CHAT_HINT_TEXT_COLOR};
    padding: 0 1;
}}

#suggestion_bar {{
    height: {_CHAT_SUGGESTIONS_HEIGHT_UNITS};
    margin: 0 1;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#subject_research_workbench {{
    height: 1fr;
    min-height: 12;
    margin-bottom: 1;
}}

#subject_itemize_workbench {{
    height: 1fr;
    min-height: 12;
    margin-bottom: 1;
}}

#subject_target_panel_shell,
#itemize_target_panel_shell {{
    margin-bottom: 1;
}}

.maximized_workbench {{
    height: 1fr;
}}

.subject_research_panel {{
    width: 1fr;
    height: 1fr;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
    margin-right: 1;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
}}

#subject_sources_panel_shell {{
    width: 1fr;
    height: 1fr;
    background: {_INACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
    margin-right: 1;
}}

#subject_observation_panel {{
    margin-right: 0;
    background: transparent;
}}

.subject_itemize_panel_wrapper {{
    width: 1fr;
    height: 1fr;
    background: {_ACTIVE_AREA_BACKGROUND};
    border: round {_INACTIVE_AREA_FRAME};
    padding: 0 1;
}}

#itemize_inventory_panel,
#itemize_detail_panel,
#itemize_target_panel {{
    width: 1fr;
    height: 1fr;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-size-horizontal: 0;
    scrollbar-size-vertical: 0;
    background: transparent;
    border: none;
    padding: 0;
}}

#itemize_inventory_wrapper {{
    margin-right: 1;
}}

#itemize_detail_wrapper {{
    margin-right: 1;
}}

"""


@dataclass
class _WorkstationChatPaneState:
    root: Path
    context: WorkstationChatContext
    application: Any | None = None
    shell_client: WorkstationShellClient = field(default_factory=InProcessWorkstationShellClient)
    shell_activity_text_cache: str = "No activity yet."
    shell_permissions_text_cache: str = ""
    shell_skills_text_cache: str = ""
    shell_transcript_snapshot_version: str = ""
    shell_activity_snapshot_version: str = ""
    shell_permissions_snapshot_version: str = ""
    shell_skills_snapshot_version: str = ""
    activity_lines: list[str] = field(default_factory=list)
    transcript_entries: list["_WorkstationTranscriptEntry"] = field(default_factory=list)
    busy: bool = False
    pending_approval_request: WorkstationDelegationEscalationRequest | None = None
    pending_approval_event: threading.Event | None = None
    pending_approval_decision: WorkstationDelegationEscalationDecision | None = None
    pending_research_capture: _PendingResearchCapture | None = None
    stop_activity_tail: Any | None = None
    current_input_text: str = ""
    current_turn_activity_line: str = ""
    current_turn_activity_pulse_index: int = 0
    current_turn_activity_visible_until: float | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)
    projection_controller: WorkstationProjectionSubscriberController | None = None

    def invalidate(self) -> None:
        app = self.application
        if app is not None:
            try:
                refresh_callback = getattr(app, "request_state_refresh", None)
                if callable(refresh_callback):
                    refresh_callback()
                else:
                    app.invalidate()
            except Exception:
                pass

    def refresh_context(self) -> None:
        with self.lock:
            self.context = workstation_chat_context(self.root)
        self.invalidate()

    def set_transcript_messages(self, messages: Iterable[Any]) -> None:
        entries: list[_WorkstationTranscriptEntry] = []
        for item in tuple(messages or ()):
            entry = _workstation_transcript_entry(
                label=str(getattr(item, "role", "") or ""),
                text=str(getattr(item, "content", "") or ""),
                timestamp_epoch_ms=int(getattr(item, "timestamp_epoch_ms", 0) or 0),
            )
            if entry is not None:
                entries.append(entry)
        with self.lock:
            self.transcript_entries = entries[-_TRANSCRIPT_PANE_MAX_BLOCKS :]
        self.invalidate()

    def apply_shell_snapshot(self, snapshot: Any) -> None:
        with self.lock:
            self.context = getattr(snapshot, "context", self.context)
            self.shell_transcript_snapshot_version = str(getattr(snapshot, "snapshot_version", "") or "")
        self.set_transcript_messages(tuple(getattr(snapshot, "messages", ()) or ()))

    def record_shell_message(self, *, text: str, prompt_text: str = "") -> Any | None:
        rendered_text = str(text or "").strip()
        if not collapse_ws(rendered_text):
            return None
        try:
            snapshot = self.shell_client.append_shell_turn(
                root_path=self.root,
                prompt_text=str(prompt_text or ""),
                assistant_text=rendered_text,
            )
        except Exception:
            self.append_transcript_block(label="shell", text=rendered_text)
            return None
        self.apply_shell_snapshot(snapshot)
        return snapshot

    def set_shell_activity_text(self, text: str, *, snapshot_version: str = "") -> None:
        with self.lock:
            self.shell_activity_text_cache = str(text or "")
            if collapse_ws(snapshot_version):
                self.shell_activity_snapshot_version = str(snapshot_version or "")
        self.invalidate()

    def set_shell_permissions_text(self, text: str, *, snapshot_version: str = "") -> None:
        with self.lock:
            self.shell_permissions_text_cache = str(text or "")
            if collapse_ws(snapshot_version):
                self.shell_permissions_snapshot_version = str(snapshot_version or "")
        self.invalidate()

    def set_shell_skills_text(self, text: str, *, snapshot_version: str = "") -> None:
        with self.lock:
            self.shell_skills_text_cache = str(text or "")
            if collapse_ws(snapshot_version):
                self.shell_skills_snapshot_version = str(snapshot_version or "")
        self.invalidate()

    def shell_snapshot_version(self, channel_key: str) -> str:
        normalized = collapse_ws(str(channel_key or "")).casefold()
        with self.lock:
            if normalized == "shell/transcript":
                return str(self.shell_transcript_snapshot_version or "")
            if normalized == "shell/activity":
                return str(self.shell_activity_snapshot_version or "")
            if normalized == "shell/permissions":
                return str(self.shell_permissions_snapshot_version or "")
            if normalized == "shell/skills":
                return str(self.shell_skills_snapshot_version or "")
        return ""

    def append_activity_line(self, text: str) -> None:
        rendered = collapse_ws(str(text))
        if not rendered:
            return
        with self.lock:
            self.activity_lines.append(rendered)
            self.activity_lines = self.activity_lines[-_ACTIVITY_PANE_MAX_LINES :]
            if self.busy:
                self.current_turn_activity_line = rendered
                self.current_turn_activity_pulse_index = 0
                self.current_turn_activity_visible_until = None
        app = self.application
        if app is not None:
            append_callback = getattr(app, "append_activity_line_ui", None)
            if callable(append_callback):
                try:
                    append_callback(rendered)
                    return
                except Exception:
                    pass
        self.invalidate()

    def append_transcript_block(self, *, label: str, text: str) -> None:
        entry = _workstation_transcript_entry(label=label, text=text)
        if entry is None:
            return
        with self.lock:
            self.transcript_entries.append(entry)
            self.transcript_entries = self.transcript_entries[-_TRANSCRIPT_PANE_MAX_BLOCKS :]
        app = self.application
        if app is not None:
            append_callback = getattr(app, "append_transcript_block_ui", None)
            if callable(append_callback):
                try:
                    append_callback(entry)
                    return
                except Exception:
                    pass
        self.invalidate()

    def clear_input_interrupted_notice(self) -> None:
        self.record_shell_message(text="Input interrupted. Type /exit to quit.")

    def start_turn(self) -> None:
        with self.lock:
            if self.stop_activity_tail is not None:
                try:
                    self.stop_activity_tail()
                except Exception:
                    pass
                self.stop_activity_tail = None
            self.busy = True
            self.current_turn_activity_line = ""
            self.current_turn_activity_pulse_index = 0
            self.current_turn_activity_visible_until = None
            start_offset = workstation_activity_log_offset(self.root)
            self.stop_activity_tail = start_workstation_activity_tail(
                root=self.root,
                start_offset=start_offset,
                emit=self.append_activity_line,
            )
        self.invalidate()

    def finish_turn(self) -> None:
        with self.lock:
            stop = self.stop_activity_tail
            self.stop_activity_tail = None
            self.busy = False
            if collapse_ws(self.current_turn_activity_line):
                self.current_turn_activity_visible_until = time.monotonic() + _ACTIVITY_STRIP_RETENTION_SECONDS
            else:
                self.current_turn_activity_line = ""
                self.current_turn_activity_pulse_index = 0
                self.current_turn_activity_visible_until = None
        if stop is not None:
            try:
                stop()
            except Exception:
                pass
        self.refresh_context()

    def stop_projection_controller(self) -> None:
        controller = self.projection_controller
        self.projection_controller = None
        if controller is not None:
            controller.stop()

    def begin_approval(self, request: WorkstationDelegationEscalationRequest) -> threading.Event:
        event = threading.Event()
        with self.lock:
            self.pending_approval_request = request
            self.pending_approval_event = event
            self.pending_approval_decision = None
        self.invalidate()
        return event

    def begin_research_capture(self, pending_capture: _PendingResearchCapture) -> None:
        with self.lock:
            self.pending_research_capture = pending_capture
        self.invalidate()

    def awaiting_research_capture(self) -> bool:
        with self.lock:
            return self.pending_research_capture is not None

    def pending_research_capture_snapshot(self) -> _PendingResearchCapture | None:
        with self.lock:
            return self.pending_research_capture

    def clear_pending_research_capture(self) -> _PendingResearchCapture | None:
        with self.lock:
            pending_capture = self.pending_research_capture
            self.pending_research_capture = None
        self.invalidate()
        return pending_capture

    def cancel_research_capture(self) -> bool:
        pending_capture = self.clear_pending_research_capture()
        if pending_capture is None:
            return False
        self.record_shell_message(text="Gather source staging canceled.")
        return True

    def resolve_approval_from_input(self, answer_text: str) -> bool:
        with self.lock:
            request = self.pending_approval_request
            event = self.pending_approval_event
            if request is None or event is None:
                return False
            normalized = collapse_ws(str(answer_text)).casefold()
            if normalized not in {"y", "yes", "n", "no"}:
                return False
            approved = normalized in {"y", "yes"}
            self.pending_approval_decision = WorkstationDelegationEscalationDecision(
                approved=approved,
                scope=request.scope,
                rationale=(
                    "User approved interactive workstation escalation."
                    if approved
                    else "User denied interactive workstation escalation."
                ),
            )
            self.pending_approval_request = None
            self.pending_approval_event = None
        event.set()
        self.invalidate()
        return True

    def cancel_approval(self) -> bool:
        with self.lock:
            request = self.pending_approval_request
            event = self.pending_approval_event
            if request is None or event is None:
                return False
            self.pending_approval_decision = WorkstationDelegationEscalationDecision(
                approved=False,
                scope=request.scope,
                rationale="User denied interactive workstation escalation.",
            )
            self.pending_approval_request = None
            self.pending_approval_event = None
        event.set()
        self.record_shell_message(text="Escalation canceled.")
        self.invalidate()
        return True

    def take_approval_decision(self) -> WorkstationDelegationEscalationDecision:
        with self.lock:
            decision = self.pending_approval_decision
            self.pending_approval_decision = None
        if decision is None:
            return WorkstationDelegationEscalationDecision(
                approved=False,
                scope="one_invocation",
                rationale="Interactive approval ended without an explicit decision.",
            )
        return decision

    def banner_text(self) -> str:
        with self.lock:
            context = self.context
        return workstation_chat_banner(context)

    def suggestions_text(self) -> str:
        with self.lock:
            context = self.context
            buffer_text = self.current_input_text
        suggestions = workstation_chat_live_suggestions(context=context, buffer_text=buffer_text)
        if not suggestions:
            return ""
        return f"{_ANSI_DIM}Suggestions:{_ANSI_RESET} " + " | ".join(
            _render_prompt_suggestion_text(suggestion) for suggestion in suggestions
        )

    def set_current_input_text(self, text: str, *, refresh: bool = True) -> None:
        with self.lock:
            self.current_input_text = str(text or "")
        if refresh:
            self.invalidate()

    def transcript_text(self) -> str:
        with self.lock:
            entries = list(self.transcript_entries)
        if not entries:
            return "No conversation yet."
        width = max(int(shutil.get_terminal_size((100, 40)).columns or 100) - 8, 40)
        return "\n\n".join(_render_transcript_entry_plain(item, width=width, use_ansi=False) for item in entries)

    def transcript_ansi_text(self) -> str:
        with self.lock:
            entries = list(self.transcript_entries)
        if not entries:
            return "No conversation yet."
        width = max(int(shutil.get_terminal_size((100, 40)).columns or 100) - 8, 40)
        return "\n\n".join(_render_transcript_entry_plain(item, width=width, use_ansi=True) for item in entries)

    def transcript_cursor_text(self) -> str:
        return self.transcript_text()

    def transcript_entries_snapshot(self) -> tuple["_WorkstationTranscriptEntry", ...]:
        with self.lock:
            return tuple(self.transcript_entries)

    def activity_strip_text(self) -> str:
        with self.lock:
            busy = self.busy
            activity_line = self.current_turn_activity_line
            pulse_index = self.current_turn_activity_pulse_index
            visible_until = self.current_turn_activity_visible_until
        if not busy and (visible_until is None or visible_until <= time.monotonic()):
            return ""
        return workstation_chat_activity_strip_text(
            activity_line,
            pulse_index=pulse_index,
        )

    def activity_text(self) -> str:
        with self.lock:
            shell_text = self.shell_activity_text_cache
            fallback_lines = list(self.activity_lines)
        normalized_shell_text = str(shell_text or "").strip()
        if fallback_lines:
            if normalized_shell_text and normalized_shell_text != "No activity yet.":
                return "\n".join([normalized_shell_text, *fallback_lines])
            return "\n".join(fallback_lines)
        if normalized_shell_text:
            return normalized_shell_text
        return "No activity yet."

    def input_status_text(self) -> str:
        with self.lock:
            request = self.pending_approval_request
            pending_research_capture = self.pending_research_capture
            busy = self.busy
        if request is not None:
            delegated_lines = ", ".join(
                f"{item.get('capability', '')}({item.get('target', '')})"
                for item in request.requested_delegation
            ) or "no additional rights listed"
            return (
                f"{_ANSI_YELLOW}Approve? [yes/no]{_ANSI_RESET} "
                f"skill={request.skill_title or '<unknown>'} rights={delegated_lines}"
            )
        if pending_research_capture is not None:
            preview_report = dict(getattr(pending_research_capture, "preview_report", {}) or {})
            target_title = collapse_ws(str(preview_report.get("canonical_title", ""))) or "<unknown>"
            return (
                f"{_ANSI_YELLOW}Confirm Gather source staging? [yes/no]{_ANSI_RESET} "
                f"target={target_title} or use /start-research-into <subject title>"
            )
        if busy:
            return f"{_ANSI_DIM}Working... activity is shown above while the current turn runs.{_ANSI_RESET}"
        return f"{_ANSI_BOLD}{_ANSI_GREEN}workstation>{_ANSI_RESET}"

    def is_busy(self) -> bool:
        with self.lock:
            return self.busy

    def advance_activity_pulse(self) -> bool:
        with self.lock:
            if not collapse_ws(self.current_turn_activity_line):
                return False
            if not self.busy:
                visible_until = self.current_turn_activity_visible_until
                if visible_until is None or visible_until <= time.monotonic():
                    return False
            self.current_turn_activity_pulse_index = (
                self.current_turn_activity_pulse_index + 1
            ) % len(_ACTIVITY_STRIP_SUFFIXES)
            return True

    def expire_activity_strip_if_needed(self) -> bool:
        with self.lock:
            if self.busy:
                return False
            visible_until = self.current_turn_activity_visible_until
            if visible_until is None or visible_until > time.monotonic():
                return False
            if not self.current_turn_activity_line and self.current_turn_activity_visible_until is None:
                return False
            self.current_turn_activity_line = ""
            self.current_turn_activity_pulse_index = 0
            self.current_turn_activity_visible_until = None
            return True

    def awaiting_approval(self) -> bool:
        with self.lock:
            return self.pending_approval_request is not None


@dataclass(frozen=True)
class _WorkstationTranscriptEntry:
    label: str
    text: str
    timestamp_epoch_ms: int


@dataclass(frozen=True)
class _PendingResearchCapture:
    markdown_text: str
    command_text: str
    subject_title_override: str
    preview_report: dict[str, Any]


@dataclass(frozen=True)
class _TextualTabContentPayload:
    tab_id: str
    request_id: int
    wrap_width: int
    log_lines: tuple[str, ...] = ()
    renderables: tuple[Any, ...] = ()
    transcript_blocks: tuple[tuple[Any, ...], ...] = ()
    learn_status_text: str = ""
    learn_ingress_text: str = ""
    last_action_text: str = ""
    current_step_text: str = ""
    journey_text: str = ""
    current_step_actions: tuple[MockSubjectGateAction, ...] = ()
    subject_sources_lines: tuple[str, ...] = ()
    subject_observation_lines: tuple[str, ...] = ()
    subject_target_lines: tuple[str, ...] = ()
    itemize_inventory_lines: tuple[str, ...] = ()
    itemize_inventory_items: tuple[Any, ...] = ()
    itemize_detail_lines: tuple[str, ...] = ()
    itemize_target_lines: tuple[str, ...] = ()
    review_scope_lines: tuple[str, ...] = ()
    draft_model_main_lines: tuple[str, ...] = ()
    review_scope_detail_lines: tuple[str, ...] = ()
    itemize_detail_title: str = ""
    draft_model_main_title: str = ""
    review_scope_detail_title: str = ""
    learn_result_title: str = ""


def _mock_subject_scenario_from_api_view(view: Any) -> MockSubjectScenario:
    return MockSubjectScenario(
        key=str(getattr(view, "key", "") or ""),
        subject_id=str(getattr(view, "subject_id", "") or ""),
        title=str(getattr(view, "title", "") or ""),
        family_title=str(getattr(view, "family_title", "") or ""),
        context_id=str(getattr(view, "context_id", "") or ""),
        summary=str(getattr(view, "summary", "") or ""),
        governance_status=str(getattr(view, "governance_status", "") or ""),
        context_snapshot_hash=str(getattr(view, "context_snapshot_hash", "") or ""),
        unit_count=int(getattr(view, "unit_count", 0) or 0),
        admitted_unit_count=int(getattr(view, "admitted_unit_count", 0) or 0),
        source_count=int(getattr(view, "source_count", 0) or 0),
        delta_count=int(getattr(view, "delta_count", 0) or 0),
        applied_delta_count=int(getattr(view, "applied_delta_count", 0) or 0),
        import_count=int(getattr(view, "import_count", 0) or 0),
        pending_import_count=int(getattr(view, "pending_import_count", 0) or 0),
        reasoning_import_count=int(getattr(view, "reasoning_import_count", 0) or 0),
        imported_subject_count=int(getattr(view, "imported_subject_count", 0) or 0),
        context_path=str(getattr(view, "context_path", "") or ""),
        subject_markdown_path=str(getattr(view, "subject_markdown_path", "") or ""),
        subject_typst_path=str(getattr(view, "subject_typst_path", "") or ""),
        publication_id=str(getattr(view, "publication_id", "") or ""),
        publication_title=str(getattr(view, "publication_title", "") or ""),
        build_id=str(getattr(view, "build_id", "") or ""),
        build_status=str(getattr(view, "build_status", "") or ""),
        validation_status=str(getattr(view, "validation_status", "") or ""),
        build_path=str(getattr(view, "build_path", "") or ""),
        publication_section_count=int(getattr(view, "publication_section_count", 0) or 0),
        publication_claim_count=int(getattr(view, "publication_claim_count", 0) or 0),
        publication_source_count=int(getattr(view, "publication_source_count", 0) or 0),
        publication_entity_count=int(getattr(view, "publication_entity_count", 0) or 0),
        publication_xref_count=int(getattr(view, "publication_xref_count", 0) or 0),
        publication_review_count=int(getattr(view, "publication_review_count", 0) or 0),
        report_markdown_path=str(getattr(view, "report_markdown_path", "") or ""),
        report_typst_path=str(getattr(view, "report_typst_path", "") or ""),
        report_pdf_path=str(getattr(view, "report_pdf_path", "") or ""),
        composition_id=str(getattr(view, "composition_id", "") or ""),
        composition_status=str(getattr(view, "composition_status", "") or ""),
        composition_title=str(getattr(view, "composition_title", "") or ""),
        composition_scope_summary=str(getattr(view, "composition_scope_summary", "") or ""),
        composition_learning_context_snapshot_hash=str(
            getattr(view, "composition_learning_context_snapshot_hash", "") or ""
        ),
        composition_included_unit_count=int(getattr(view, "composition_included_unit_count", 0) or 0),
        composition_selected_import_count=int(getattr(view, "composition_selected_import_count", 0) or 0),
        composition_section_count=int(getattr(view, "composition_section_count", 0) or 0),
        source_collection_count=int(getattr(view, "source_collection_count", 0) or 0),
        staged_source_count=int(getattr(view, "staged_source_count", 0) or 0),
        source_collection_preview_lines=tuple(
            str(line or "") for line in getattr(view, "source_collection_preview_lines", ()) or ()
        ),
        source_preview_lines=tuple(str(line or "") for line in getattr(view, "source_preview_lines", ()) or ()),
        staged_source_preview_lines=tuple(
            str(line or "") for line in getattr(view, "staged_source_preview_lines", ()) or ()
        ),
        unit_preview_lines=tuple(str(line or "") for line in getattr(view, "unit_preview_lines", ()) or ()),
        delta_preview_lines=tuple(str(line or "") for line in getattr(view, "delta_preview_lines", ()) or ()),
        pending_import_preview_lines=tuple(
            str(line or "") for line in getattr(view, "pending_import_preview_lines", ()) or ()
        ),
        import_preview_lines=tuple(str(line or "") for line in getattr(view, "import_preview_lines", ()) or ()),
        is_placeholder=bool(getattr(view, "is_placeholder", False)),
    )


def _list_mock_subject_scenarios_via_api(
    root_path: Path,
    client: SubjectWorkflowClient | None = None,
    projection_backend: TextualSubjectWorkflowProjectionBackend | None = None,
) -> tuple[MockSubjectScenario, ...]:
    backend = projection_backend or TextualSubjectWorkflowProjectionBackend(
        client or _create_textual_subject_workflow_client()
    )
    scenario_views = backend.list_subjects(root_path=Path(root_path).expanduser().resolve())
    return tuple(_mock_subject_scenario_from_api_view(view) for view in scenario_views)


def format_chat_timestamp_epoch_ms(timestamp_epoch_ms: int) -> str:
    try:
        normalized = int(timestamp_epoch_ms or 0)
    except Exception:
        normalized = 0
    if normalized <= 0:
        return ""
    try:
        moment = _datetime.datetime.fromtimestamp(normalized / 1000, tz=_datetime.timezone.utc).astimezone()
    except Exception:
        return ""
    return moment.strftime("%I:%M %p").lstrip("0")


def _workstation_transcript_entry(*, label: str, text: str, timestamp_epoch_ms: int | None = None) -> _WorkstationTranscriptEntry | None:
    body = str(text or "").strip("\n")
    if not body.strip():
        return None
    if timestamp_epoch_ms is None or int(timestamp_epoch_ms or 0) <= 0:
        timestamp_epoch_ms = int(time.time() * 1000)
    return _WorkstationTranscriptEntry(
        label=collapse_ws(str(label)) or "output",
        text=body,
        timestamp_epoch_ms=int(timestamp_epoch_ms),
    )


def _transcript_entries_from_messages(messages: Iterable[Any]) -> list[_WorkstationTranscriptEntry]:
    entries: list[_WorkstationTranscriptEntry] = []
    for item in tuple(messages or ()):
        entry = _workstation_transcript_entry(
            label=str(getattr(item, "role", "") or ""),
            text=str(getattr(item, "content", "") or ""),
            timestamp_epoch_ms=int(getattr(item, "timestamp_epoch_ms", 0) or 0),
        )
        if entry is not None:
            entries.append(entry)
    return entries[-_TRANSCRIPT_PANE_MAX_BLOCKS :]


def _initial_transcript_entries(root: Path) -> list[_WorkstationTranscriptEntry]:
    return []


def workstation_chat_activity_strip_text(activity_text: str, *, pulse_index: int = 0) -> str:
    normalized = collapse_ws(str(activity_text))
    if not normalized:
        return ""
    shortened = textwrap.shorten(
        normalized,
        width=_ACTIVITY_STRIP_MAX_CHARS,
        placeholder="...",
    )
    suffix = _ACTIVITY_STRIP_SUFFIXES[int(pulse_index) % len(_ACTIVITY_STRIP_SUFFIXES)]
    return f"{shortened}{suffix}"


def workstation_chat_ui_supported(*, input_stream: Any, output_stream: Any) -> bool:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat usage, helps with deciding whether the enhanced ANSI/readline frontend can be used safely instead of the plain line loop.

    Reference to Theory:
        Supports separation of concerns by keeping the richer terminal UX as an optional outer shell layer over the unchanged workstation session core.

    Example Input Output:
        Input: `workstation_chat_ui_supported(input_stream=sys.stdin, output_stream=sys.stdout)`
        Output: True

    Args:
        input_stream: Candidate input stream.
        output_stream: Candidate output stream.

    Returns:
        bool: Result produced by `workstation_chat_ui_supported`.
    """
    if TextualApp is None and PromptSession is None:
        return False
    return bool(
        input_stream is sys.stdin
        and output_stream is sys.stdout
        and hasattr(input_stream, "isatty")
        and hasattr(output_stream, "isatty")
        and input_stream.isatty()
        and output_stream.isatty()
    )


def workstation_chat_history_path(root: Path) -> Path:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat history navigation, helps with resolving the canonical prompt-history file used by the enhanced shell frontend.

    Reference to Theory:
        Supports the host-owned shell layer by keeping input-history persistence explicit under the workstation root rather than as ambient terminal state.

    Example Input Output:
        Input: `workstation_chat_history_path(Path('/tmp/ws'))`
        Output: Path('/tmp/ws/history/chat_input.txt')

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.

    Returns:
        Path: Result produced by `workstation_chat_history_path`.
    """
    return Path(root).expanduser().resolve() / "history" / "chat_input.txt"


def workstation_chat_context(root: Path) -> WorkstationChatContext:
    return _shared_workstation_chat_context(Path(root).expanduser().resolve())


def workstation_chat_banner(context: WorkstationChatContext) -> str:
    """
    High Level Purpose:
        In circumstances like interactive workstation chat startup, helps with rendering one compact status banner that makes the current workspace, skill inventory, and completion model visible.

    Reference to Theory:
        Supports the host-owned chat surface by making session context explicit at the shell boundary instead of leaving it implicit in the underlying session files.

    Example Input Output:
        Input: `workstation_chat_banner(context=WorkstationChatContext(...))`
        Output: '+ Workstation Chat\\n  Root: /tmp/ws\\n  Workspace: /tmp/project\\n  Skills: 14 total (12 imported)\\n  Tab completes skills, paths, and slash commands.'

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.

    Returns:
        str: Result produced by `workstation_chat_banner`.
    """
    total = len(context.skill_titles)
    imported = len(context.imported_skill_titles)
    workspace_text = str(context.workspace_root) if context.workspace_root is not None else "<none>"
    lines = [
        f"{_ANSI_BOLD}{_ANSI_CYAN}+ Workstation Chat{_ANSI_RESET}",
        f"  {_ANSI_DIM}Root:{_ANSI_RESET} {context.root}",
        f"  {_ANSI_DIM}Workspace:{_ANSI_RESET} {workspace_text}",
        f"  {_ANSI_DIM}Skills:{_ANSI_RESET} {total} total ({imported} imported)",
        f"  {_ANSI_DIM}Hints:{_ANSI_RESET} Up/Down navigates suggestions when text is present. Tab selects. Shift+Tab switches tabs.",
    ]
    return "\n".join(lines)


def workstation_chat_help_text(context: WorkstationChatContext) -> str:
    return _shared_workstation_chat_help_text(context)


def _strip_wrapping_quotes(text: str) -> str:
    rendered = str(text or "").strip()
    if len(rendered) >= 2 and rendered[0] == rendered[-1] and rendered[0] in {"'", '"'}:
        return rendered[1:-1].strip()
    return rendered


def _subject_action_label_parts(label: str) -> tuple[str, str]:
    normalized_label = collapse_ws(str(label or ""))
    if not normalized_label:
        return ("", "")
    if ":" not in normalized_label:
        return ("", normalized_label)
    prefix, suffix = normalized_label.split(":", 1)
    normalized_prefix = collapse_ws(prefix)
    normalized_suffix = collapse_ws(suffix)
    if not normalized_prefix or not normalized_suffix:
        return ("", normalized_label)
    return (normalized_prefix, normalized_suffix)


def _subject_title_completion_candidates(
    *,
    context: WorkstationChatContext,
    raw_prefix: str,
    command_name: str,
) -> list[str]:
    prefix = _strip_wrapping_quotes(raw_prefix).casefold()
    subject_titles = sorted(
        [title for title in context.subject_titles if collapse_ws(title)],
        key=str.casefold,
    )
    if not prefix:
        return [f"{command_name} {title}" for title in subject_titles]
    return [
        f"{command_name} {title}"
        for title in subject_titles
        if title.casefold().startswith(prefix)
    ]


def _resolved_subject_title_for_resume(*, context: WorkstationChatContext, raw_subject_text: str) -> str:
    normalized = _strip_wrapping_quotes(raw_subject_text)
    if not collapse_ws(normalized):
        return ""
    for title in context.subject_titles:
        if title.casefold() == normalized.casefold():
            return title
    return ""


def workstation_chat_prepare_markdown_prompt(example_text: str) -> str:
    return _shared_workstation_chat_prepare_markdown_prompt(example_text)


def workstation_chat_prepare_last_assistant_routed_text(assistant_text: str) -> str:
    preview = textwrap.shorten(collapse_ws(str(assistant_text or "")), width=220, placeholder="...")
    return "\n".join(
        [
            "[routed-to-llm]",
            "Prepare research-ingress markdown from the last assistant reply.",
            f"Source preview: {preview or '<empty>'}",
        ]
    ).rstrip()


def workstation_chat_prepare_last_assistant_resolution(assistant_text: str) -> tuple[str, str]:
    return _shared_workstation_chat_prepare_last_assistant_resolution(assistant_text)


def workstation_chat_resume_research_prompt(subject_title: str) -> str:
    return _shared_workstation_chat_resume_research_prompt(subject_title)


_RESEARCH_CHAT_ACTION_TARGET_SPECS: dict[str, dict[str, str]] = {
    "/apply-source-export": {
        "action_key": "apply_selected_staged_source_export_preview",
        "missing_text": "/apply-source-export requires a selected staged source in Gather with governed additions ready to stage.",
    },
    "/apply-source-set-export": {
        "action_key": "apply_selected_source_collection_export_preview",
        "missing_text": "/apply-source-set-export requires a selected focused source set in Gather with governed additions ready to stage.",
    },
    "/create-source-set": {
        "action_key": "create_source_collection_from_selected_staged_source",
        "missing_text": "/create-source-set requires a selected staged source in Gather.",
    },
    "/create-source-set-from-query": {
        "action_key": "create_source_collection_from_query",
        "missing_text": (
            "/create-source-set-from-query requires: <title> | <query> | [description]. "
            "It creates an empty Gather source set from a topic/query."
        ),
    },
    "/edit-source": {
        "action_key": "start_research_source_manual_curation",
        "missing_text": "/edit-source requires a selected staged source in Gather.",
    },
    "/edit-source-set": {
        "action_key": "start_research_source_collection_manual_curation",
        "missing_text": "/edit-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
    "/refresh-source": {
        "action_key": "refresh_selected_staged_source",
        "missing_text": "/refresh-source requires a selected URL-backed staged source in Gather.",
    },
    "/sync-source-set": {
        "action_key": "sync_selected_source_collection",
        "missing_text": "/sync-source-set requires a selected source set in Gather with refreshable URL-backed sources.",
    },
}

_RESEARCH_CHAT_PROMPT_TARGET_SPECS: dict[str, dict[str, str]] = {
    "/curate-source": {
        "action_key": "start_research_source_llm_curation",
        "progress_field": "research_source_llm_curation_staged_source_id",
        "started_text": "Started a Gather source curation in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
        "missing_text": "/curate-source requires a selected staged source in Gather.",
    },
    "/merge-source": {
        "action_key": "start_research_source_merge_back",
        "progress_field": "research_source_merge_back_staged_source_id",
        "started_text": "Started a Gather source merge-back in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
        "missing_text": "/merge-source requires a selected staged source in Gather and current learned subject state.",
    },
    "/curate-source-set": {
        "action_key": "start_research_source_collection_llm_curation",
        "progress_field": "research_source_collection_llm_curation_collection_id",
        "started_text": "Started a Gather source-set curation in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
        "missing_text": "/curate-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
    "/find-sources": {
        "action_key": "start_research_source_collection_discovery",
        "progress_field": "research_source_collection_discovery_collection_id",
        "started_text": "Started a Gather source-discovery turn in Chat. Reply with repeated [source] blocks using [label], [url], and [notes] only, and keep the result at the source layer.",
        "missing_text": "/find-sources requires a selected source set in Gather with a saved query.",
    },
    "/merge-source-set": {
        "action_key": "start_research_source_collection_merge_back",
        "progress_field": "research_source_collection_merge_back_collection_id",
        "started_text": "Started a Gather source-set merge-back in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
        "missing_text": "/merge-source-set requires a selected source set in Gather plus current learned subject state.",
    },
    "/merge-set-sources": {
        "action_key": "start_research_source_collection_source_merge_back",
        "progress_field": "research_source_collection_source_merge_back_collection_id",
        "started_text": "Started a Gather set-source merge-back in Chat. Reply with repeated [source] blocks using [url], [label], and [text] only, and keep the result at the source layer.",
        "missing_text": "/merge-set-sources requires a selected source set in Gather plus current learned subject state.",
    },
    "/synthesize-source-set": {
        "action_key": "start_research_source_collection_synthesis",
        "progress_field": "research_source_collection_synthesis_collection_id",
        "started_text": (
            "Started a Gather source-set synthesis in Chat. Reply with [summary], [questions], and [query] sections only, "
            "and keep the result at the source layer."
        ),
        "missing_text": "/synthesize-source-set requires a selected source set in Gather. The default All Gather Sources set is not eligible.",
    },
}


def workstation_chat_prompt_target_plan(
    *,
    context: WorkstationChatContext,
    prompt_text: str,
) -> WorkstationChatPromptTargetPlan | None:
    return _shared_workstation_chat_prompt_target_plan(context=context, prompt_text=prompt_text)


def _pane_view_text_by_key(bundle: Any, pane_key: str) -> str:
    for pane in tuple(getattr(bundle, "panes", ()) or ()):
        if collapse_ws(getattr(pane, "key", "")) == collapse_ws(pane_key):
            return "\n".join(tuple(getattr(pane, "lines", ()) or ())).strip()
    return ""


def _pane_view_title_by_key(bundle: Any, pane_key: str) -> str:
    for pane in tuple(getattr(bundle, "panes", ()) or ()):
        if collapse_ws(getattr(pane, "key", "")) == collapse_ws(pane_key):
            return collapse_ws(getattr(pane, "title", ""))
    return ""


def workstation_chat_research_capture_text(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Gather source staged from the last assistant markdown.",
            f"- subject: {collapse_ws(str(report.get('canonical_title', ''))) or '<unknown>'}",
            f"- subject_id: {collapse_ws(str(report.get('subject_id', ''))) or '<unknown>'}",
            f"- context: {collapse_ws(str(report.get('context_path', ''))) or '<missing>'}",
            f"- staged source: {collapse_ws(str(report.get('staged_source_id', ''))) or '<unknown>'}",
            f"- revision: {collapse_ws(str(report.get('revision_id', ''))) or '<unknown>'}",
            f"- staged items: {int(report.get('proposed_unit_count', 0) or 0)}",
        ]
    )


def workstation_chat_research_preview_text(report: dict[str, Any]) -> str:
    canonical_title = collapse_ws(str(report.get("canonical_title", ""))) or "<unknown>"
    matched_existing_subject_id = collapse_ws(str(report.get("matched_existing_subject_id", "")))
    override_title = collapse_ws(str(report.get("subject_title_override", "")))
    lines = [
        "Gather staged-source preview from the last assistant markdown.",
        f"- document: {collapse_ws(str(report.get('document_title', ''))) or '<unknown>'}",
        f"- proposed subject: {canonical_title}",
        (
            f"- target context: existing subject ({matched_existing_subject_id})"
            if matched_existing_subject_id
            else "- target context: new subject"
        ),
        f"- items to stage: {int(report.get('proposed_unit_count', 0) or 0)}",
    ]
    if override_title:
        lines.append(f"- subject override: {override_title}")
    lines.extend(
        [
            "",
            "Reply yes to stage, no to cancel, or use /start-research-into <subject title> to choose another subject.",
        ]
    )
    return "\n".join(lines)


def workstation_chat_routed_llm_prompt_text(llm_prompt: str) -> str:
    return _shared_workstation_chat_routed_llm_prompt_text(llm_prompt)


def workstation_chat_prompt_target_plan_via_shell(
    *,
    shell_client: WorkstationShellClient,
    root_path: Path,
    prompt_text: str,
) -> WorkstationChatPromptTargetPlan | None:
    prepared = shell_client.prepare_chat_prompt_target(
        root_path=Path(root_path).expanduser().resolve(),
        prompt_text=prompt_text,
    )
    if collapse_ws(getattr(prepared, "kind", "")) in {"", "none"}:
        return None
    routing_metadata: dict[str, Any] = {}
    raw_metadata = str(getattr(prepared, "routing_metadata_json", "") or "")
    if raw_metadata:
        try:
            parsed = json.loads(raw_metadata)
        except Exception:
            parsed = {}
        if isinstance(parsed, dict):
            routing_metadata = parsed
    return WorkstationChatPromptTargetPlan(
        kind=str(getattr(prepared, "kind", "") or ""),
        command_name=str(routing_metadata.get("command_name", "") or ""),
        command_arguments=str(routing_metadata.get("command_arguments", "") or ""),
        llm_prompt=str(getattr(prepared, "prepared_prompt", "") or ""),
        shell_text=str(getattr(prepared, "shell_text", "") or ""),
        move_to_research=bool(routing_metadata.get("move_to_research", False)),
        subject_title=str(routing_metadata.get("subject_title", "") or ""),
    )


def _latest_transcript_assistant_text(state: _WorkstationChatPaneState) -> str:
    for entry in reversed(state.transcript_entries_snapshot()):
        if collapse_ws(str(entry.label)).casefold() == "assistant":
            return str(entry.text or "").strip()
    return ""


def workstation_chat_assistant_block_text(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation chat assistant rendering, helps with preserving multiline model output verbatim while presenting it in one visually separated block.

    Reference to Theory:
        Supports the outer shell UX by changing only presentation at the chat boundary and leaving underlying workstation execution semantics untouched.

    Example Input Output:
        Input: `workstation_chat_assistant_block_text("Line one\\nLine two")`
        Output: 'assistant\\n[text]\\nLine one\\nLine two'

    Args:
        text: Value for `text` used by `text`. Expected type: `str`.

    Returns:
        str: Result produced by `workstation_chat_assistant_block_text`.
    """
    body = str(text or "").strip("\n")
    if not body.strip():
        return ""
    return workstation_chat_named_block_text(label="assistant", text=body)


def workstation_chat_named_block_text(*, label: str, text: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation chat output rendering, helps with presenting one multiline text payload in a visually separated preformatted block under an explicit label.

    Reference to Theory:
        Supports the outer shell UX by keeping presentation consistent across assistant replies and local shell-command output while leaving the underlying session logic unchanged.

    Example Input Output:
        Input: `workstation_chat_named_block_text(label='shell', text='Line one\\nLine two')`
        Output: 'System\\n  Line one\\n  Line two'

    Args:
        label: Value for `label` used by `label`. Expected type: `str`.
        text: Value for `text` used by `text`. Expected type: `str`.

    Returns:
        str: Result produced by `workstation_chat_named_block_text`.
    """
    body = str(text or "").strip("\n")
    if not body.strip():
        return ""
    normalized_label = collapse_ws(str(label)) or "output"
    display_label = _transcript_display_label(normalized_label)
    format_name, rendered_body = _format_transcript_block_body(body)
    lines = [display_label]
    if format_name != "text":
        lines.append("  " + f"[{format_name}]")
    lines.extend(_indent_transcript_body_lines(rendered_body))
    return "\n".join(lines)


def _format_transcript_block_body(text: str) -> tuple[str, str]:
    stripped = str(text or "").strip("\n")
    if not stripped.strip():
        return "text", ""
    if "```" in stripped:
        return "markdown", _replace_markdown_fences_for_transcript(stripped)
    structured = _parse_structured_transcript_value(stripped)
    if structured is not None:
        return "json", json.dumps(structured, indent=2, sort_keys=True)
    if _looks_like_yaml_text(stripped):
        return "yaml", stripped
    return "text", stripped


def _replace_markdown_fences_for_transcript(text: str) -> str:
    def _render_match(match: re.Match[str]) -> str:
        fence_kind = collapse_ws(str(match.group(1) or "")) or "text"
        fence_body = str(match.group(2) or "").strip("\n")
        return "\n".join([f"[{fence_kind}]", fence_body])

    return _FENCED_BLOCK_PATTERN.sub(_render_match, str(text or "").strip("\n"))


def _transcript_display_label(label: str) -> str:
    normalized = collapse_ws(str(label)).casefold()
    if normalized == "user":
        return "You"
    if normalized == "assistant":
        return "Assistant"
    if normalized == "shell":
        return "System"
    return collapse_ws(str(label)).replace("_", " ").title() or "Output"


def _indent_transcript_body_lines(text: str) -> list[str]:
    lines = str(text or "").splitlines() or [""]
    return [f"  {line}" if line else "" for line in lines]


def _transcript_role_styles(label: str) -> tuple[str, str, str, str]:
    normalized = collapse_ws(str(label)).casefold()
    if normalized == "user":
        return _ANSI_USER_BOLD, _ANSI_USER, f"bold {_RICH_USER_STYLE}", _RICH_USER_STYLE
    if normalized == "assistant":
        return _ANSI_ASSISTANT_BOLD, _ANSI_ASSISTANT, f"bold {_RICH_ASSISTANT_STYLE}", _RICH_ASSISTANT_STYLE
    if normalized == "shell":
        return _ANSI_SYSTEM_BOLD, _ANSI_SYSTEM, f"bold {_RICH_SYSTEM_STYLE}", _RICH_SYSTEM_STYLE
    return f"{_ANSI_BOLD}{_ANSI_DEFAULT_TEXT}", _ANSI_DEFAULT_TEXT, f"bold {_RICH_DEFAULT_STYLE}", _RICH_DEFAULT_STYLE


def _render_transcript_entry_plain(
    entry: _WorkstationTranscriptEntry,
    *,
    width: int,
    use_ansi: bool,
) -> str:
    label_text = _transcript_display_label(entry.label)
    time_text = format_chat_timestamp_epoch_ms(entry.timestamp_epoch_ms)
    header_plain = _transcript_header_plain(label_text, time_text, width=width)
    format_name, rendered_body = _format_transcript_block_body(entry.text)
    header_ansi, body_ansi, _header_rich, _body_rich = _transcript_role_styles(entry.label)
    if use_ansi:
        header_line = f"{header_ansi}{header_plain}{_ANSI_RESET}"
        if time_text:
            header_line = _transcript_header_ansi(label_text, time_text, width=width, header_style=header_ansi)
        body_lines = [
            f"{body_ansi}{line}{_ANSI_RESET}" if line else ""
            for line in _indent_transcript_body_lines(rendered_body)
        ]
        if format_name != "text":
            body_lines = [f"{body_ansi}  [{format_name}]{_ANSI_RESET}"] + body_lines
        return "\n".join([header_line, *body_lines])
    lines = [header_plain]
    if format_name != "text":
        lines.append("  " + f"[{format_name}]")
    lines.extend(_indent_transcript_body_lines(rendered_body))
    return "\n".join(lines)


def _transcript_header_plain(label_text: str, time_text: str, *, width: int) -> str:
    if not time_text:
        return label_text
    usable_width = max(int(width or 0), len(label_text) + len(time_text) + 1)
    spacing = max(1, usable_width - len(label_text) - len(time_text))
    return f"{label_text}{' ' * spacing}{time_text}"


def _transcript_header_ansi(label_text: str, time_text: str, *, width: int, header_style: str) -> str:
    if not time_text:
        return f"{header_style}{label_text}{_ANSI_RESET}"
    usable_width = max(int(width or 0), len(label_text) + len(time_text) + 1)
    spacing = max(1, usable_width - len(label_text) - len(time_text))
    return (
        f"{header_style}{label_text}{_ANSI_RESET}"
        + (" " * spacing)
        + f"{_ANSI_TIME}{time_text}{_ANSI_RESET}"
    )


def _render_transcript_entry_rich(entry: _WorkstationTranscriptEntry, *, width: int) -> list[Any]:
    if RichText is None:
        return [_render_transcript_entry_plain(entry, width=width, use_ansi=False)]
    label_text = _transcript_display_label(entry.label)
    time_text = format_chat_timestamp_epoch_ms(entry.timestamp_epoch_ms)
    _header_ansi, _body_ansi, header_rich, body_rich = _transcript_role_styles(entry.label)
    renderables: list[Any] = []
    header = RichText()
    header.append(label_text, style=header_rich)
    if time_text:
        usable_width = max(int(width or 0), len(label_text) + len(time_text) + 1)
        spacing = max(1, usable_width - len(label_text) - len(time_text))
        header.append(" " * spacing, style=body_rich)
        header.append(time_text, style=_RICH_TIME_STYLE)
    renderables.append(header)
    format_name, rendered_body = _format_transcript_block_body(entry.text)
    if format_name != "text":
        renderables.append(RichText("  " + f"[{format_name}]", style=body_rich))
    for line in _indent_transcript_body_lines(rendered_body):
        renderables.append(RichText(line, style=body_rich))
    return renderables


def _wrap_textual_log_lines(text: str, *, width: int) -> list[str]:
    wrap_width = max(int(width or 0), 24)
    rendered_lines: list[str] = []
    for raw_line in str(text or "").splitlines() or [""]:
        plain_line = _plain_ui_text(raw_line)
        if not plain_line:
            rendered_lines.append("")
            continue
        wrapped = textwrap.wrap(
            plain_line,
            width=wrap_width,
            expand_tabs=False,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=False,
            break_on_hyphens=False,
            subsequent_indent="  ",
        )
        rendered_lines.extend(wrapped or [""])
    return rendered_lines


def _textual_copy_selected_text(screen: Any, app: Any) -> bool:
    try:
        selection = screen.get_selected_text()
    except Exception:
        return False
    if selection is None:
        return False
    return _textual_copy_text(app, selection)


def _copy_text_to_system_clipboard(text: str) -> bool:
    rendered = str(text or "")
    if not rendered:
        return False
    command_variants: list[list[str]] = []
    if sys.platform == "darwin":
        command_variants.append(["pbcopy"])
    elif os.name == "nt":
        command_variants.append(["clip"])
    else:
        if shutil.which("wl-copy"):
            command_variants.append(["wl-copy"])
        if shutil.which("xclip"):
            command_variants.append(["xclip", "-selection", "clipboard"])
        if shutil.which("xsel"):
            command_variants.append(["xsel", "--clipboard", "--input"])
    for command in command_variants:
        try:
            subprocess.run(command, input=rendered.encode("utf-8"), check=True)
            return True
        except Exception:
            continue
    return False


def _textual_copy_text(app: Any, text: str) -> bool:
    rendered = str(text or "")
    if not rendered.strip():
        return False
    copied = False
    try:
        app.copy_to_clipboard(rendered)
        copied = True
    except Exception:
        copied = False
    return _copy_text_to_system_clipboard(rendered) or copied


def _textual_copy_selected_text_from_widget(widget: Any, app: Any) -> bool:
    try:
        selection = getattr(widget, "text_selection", None)
    except Exception:
        return False
    if selection is None:
        return False
    try:
        extracted = widget.get_selection(selection)
    except Exception:
        return False
    if not extracted:
        return False
    if isinstance(extracted, tuple):
        selected_text = str(extracted[0] or "")
    else:
        selected_text = str(extracted or "")
    return _textual_copy_text(app, selected_text)


def _textual_scroll_to_end(widget: Any) -> None:
    try:
        target_y = float(getattr(widget, "max_scroll_y", 0) or 0)
    except Exception:
        target_y = 0.0
    for attribute_name in ("scroll_target_y", "scroll_y"):
        try:
            setattr(widget, attribute_name, target_y)
        except Exception:
            pass
    scroll_to_attempts = (
        {"y": target_y, "animate": False, "force": True, "immediate": True},
        {"y": target_y, "animate": False, "force": True},
        {"y": target_y, "animate": False},
    )
    for kwargs in scroll_to_attempts:
        try:
            widget.scroll_to(**kwargs)
            return
        except TypeError:
            continue
        except Exception:
            break
    scroll_attempts = (
        {"animate": False, "force": True, "immediate": True, "x_axis": False},
        {"animate": False, "force": True, "x_axis": False},
        {"animate": False, "x_axis": False},
    )
    for kwargs in scroll_attempts:
        try:
            widget.scroll_end(**kwargs)
            return
        except TypeError:
            continue
        except Exception:
            return


def _textual_scroll_line_into_view(widget: Any, line_index: int, *, context: int = 2) -> None:
    try:
        selected_index = max(0, int(line_index))
    except Exception:
        return
    try:
        current_y = int(float(getattr(widget, "scroll_y", 0) or 0))
    except Exception:
        current_y = 0
    viewport_height = 0
    for value in (
        getattr(getattr(widget, "scrollable_content_region", None), "height", 0),
        getattr(getattr(widget, "content_region", None), "height", 0),
        getattr(getattr(widget, "size", None), "height", 0),
    ):
        try:
            viewport_height = int(value or 0)
        except Exception:
            viewport_height = 0
        if viewport_height > 0:
            break
    if viewport_height <= 0:
        viewport_height = 10
    max_scroll_y = 0
    try:
        max_scroll_y = max(0, int(float(getattr(widget, "max_scroll_y", 0) or 0)))
    except Exception:
        max_scroll_y = 0
    target_y = current_y
    visible_top = current_y + max(0, int(context))
    visible_bottom = current_y + max(0, viewport_height - int(context) - 1)
    if selected_index < visible_top:
        target_y = max(0, selected_index - int(context))
    elif selected_index > visible_bottom:
        target_y = max(0, selected_index - max(1, viewport_height - int(context) - 1))
    target_y = min(max_scroll_y, max(0, int(target_y)))
    if target_y == current_y and selected_index >= current_y and selected_index <= max(current_y, visible_bottom):
        return
    for attribute_name in ("scroll_target_y", "scroll_y"):
        try:
            setattr(widget, attribute_name, float(target_y))
        except Exception:
            pass
    for kwargs in (
        {"y": float(target_y), "animate": False, "force": True, "immediate": True},
        {"y": float(target_y), "animate": False, "force": True},
        {"y": float(target_y), "animate": False},
    ):
        try:
            widget.scroll_to(**kwargs)
            return
        except TypeError:
            continue
        except Exception:
            break


def _rich_line(text: str, *, style: str = "") -> Any:
    if RichText is None:
        return text
    return RichText(str(text or ""), style=style or None)


def _rich_bullet_line(text: str, *, bullet_style: str = _RICH_TIME_STYLE, text_style: str = _RICH_DEFAULT_STYLE) -> Any:
    if RichText is None:
        return f"- {text}"
    line = RichText()
    line.append("- ", style=bullet_style)
    line.append(str(text or ""), style=text_style)
    return line


def _activity_section_style(section_text: str) -> str:
    lowered = collapse_ws(str(section_text)).casefold()
    if lowered.startswith("[in:"):
        return _RICH_ACTIVITY_IN_STYLE
    if lowered.startswith("[out:"):
        return _RICH_ACTIVITY_OUT_STYLE
    if lowered.startswith("[reason:"):
        return _RICH_ACTIVITY_REASON_STYLE
    if lowered.startswith("[run:"):
        return _RICH_ACTIVITY_META_STYLE
    return _RICH_ACTIVITY_META_STYLE


def _render_activity_rich_line(text: str) -> Any:
    tree_prefix, main_text, sections, timing_text = split_rendered_workstation_activity_line(text)
    if RichText is None:
        return str(text or "")
    line = RichText()
    if tree_prefix:
        line.append(tree_prefix, style=_RICH_ACTIVITY_TREE_STYLE)
    if main_text:
        line.append(main_text, style=_RICH_ACTIVITY_MAIN_STYLE)
    for section in sections:
        if line.plain:
            line.append(" ")
        line.append(section, style=_activity_section_style(section))
    if timing_text:
        if line.plain:
            line.append(" ")
        line.append(timing_text, style=_RICH_ACTIVITY_TIME_STYLE)
    return line


def _render_permissions_rich_lines(text: str) -> tuple[Any, ...]:
    renderables: list[Any] = []
    for raw_line in str(text or "").splitlines() or [""]:
        stripped = str(raw_line or "")
        if not stripped:
            renderables.append("")
        elif stripped.startswith("- "):
            renderables.append(_rich_bullet_line(stripped[2:], text_style=_RICH_DEFAULT_STYLE))
        elif stripped.startswith("/"):
            renderables.append(_rich_line(stripped, style=_RICH_ACTIVITY_META_STYLE))
        elif stripped.endswith(":"):
            renderables.append(_rich_line(stripped, style=_RICH_PERMISSION_TITLE_STYLE))
        else:
            renderables.append(_rich_line(stripped, style=_RICH_DEFAULT_STYLE))
    return tuple(renderables)


def _render_skills_rich_lines(text: str) -> tuple[Any, ...]:
    renderables: list[Any] = []
    for raw_line in str(text or "").splitlines() or [""]:
        stripped = str(raw_line or "")
        normalized = collapse_ws(stripped).casefold()
        if not stripped:
            renderables.append("")
        elif stripped.startswith("- "):
            renderables.append(_rich_bullet_line(stripped[2:], text_style=_RICH_DEFAULT_STYLE))
        elif normalized.startswith("skills matching:") or normalized.startswith("total visible:"):
            renderables.append(_rich_line(stripped, style=_RICH_SKILL_TITLE_STYLE))
        elif normalized.endswith("skills"):
            renderables.append(_rich_line(stripped, style=_RICH_SKILL_TITLE_STYLE))
        else:
            renderables.append(_rich_line(stripped, style=_RICH_DEFAULT_STYLE))
    return tuple(renderables)


def _workstation_action_result_text(payload: dict[str, Any]) -> str:
    title = collapse_ws(str(payload.get("title", ""))) or "Action"
    status = collapse_ws(str(payload.get("status", ""))) or "unknown"
    message = collapse_ws(str(payload.get("message", "")))
    details = payload.get("details", [])
    if not isinstance(details, list):
        details = []
    lines = [f"{title} [{status}]"]
    if message:
        lines.append(message)
    lines.extend(str(item) for item in details if collapse_ws(str(item)))
    payload_preview = str(payload.get("payload_preview", "") or "")
    if payload_preview:
        lines.append(payload_preview)
    return "\n".join(lines)


def _parse_structured_transcript_value(text: str) -> Any | None:
    stripped = str(text or "").strip()
    if not stripped:
        return None
    if stripped.startswith(("{", "[")):
        try:
            return json.loads(stripped)
        except Exception:
            pass
        try:
            parsed = ast.literal_eval(stripped)
        except Exception:
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
    return None


def _looks_like_yaml_text(text: str) -> bool:
    stripped = str(text or "").strip()
    if not stripped or stripped.startswith(("{", "[")):
        return False
    lines = [line.rstrip() for line in stripped.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    yaml_like = 0
    colon_like = 0
    for line in lines[:12]:
        candidate = line.lstrip()
        if candidate.startswith("- "):
            yaml_like += 1
            continue
        if ":" in candidate and not candidate.startswith(("http://", "https://")):
            key, _, value = candidate.partition(":")
            if key.strip():
                yaml_like += 1
                colon_like += 1
    return yaml_like >= 2 and colon_like >= 1


def workstation_chat_suggestions(context: WorkstationChatContext) -> list[str]:
    """
    High Level Purpose:
        In circumstances like enhanced workstation chat prompting, helps with producing a few high-value next-prompt suggestions from the current skill, path, and permission context.

    Reference to Theory:
        Supports skill-first chat by steering the user toward installed workers, import flows, and approval-aware write operations without changing the execution substrate.

    Example Input Output:
        Input: `workstation_chat_suggestions(context=WorkstationChatContext(...))`
        Output: ['What skills are available right now? Separate built-in workstation skills from imported skills.', 'Import the skill file at trials/symbolsearch.skill.yaml into this workstation.']

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.

    Returns:
        list[str]: Result produced by `workstation_chat_suggestions`.
    """
    suggestions: list[str] = []
    suggestions.append("What skills are available right now? Separate built-in workstation skills from imported skills.")
    trial_skill_paths = [
        candidate
        for candidate in context.workspace_paths
        if candidate.startswith("trials/") and candidate.endswith((".yaml", ".yml"))
    ]
    for path_text in trial_skill_paths[:2]:
        suggestions.append(f"Import the skill file at {path_text} into this workstation.")
    if any("Python Commands 02" in title for title in context.skill_titles):
        readable_paths = [
            candidate
            for candidate in context.workspace_paths
            if candidate.endswith((".py", ".md", ".txt", ".json", ".yaml", ".yml", ".csv"))
        ]
        if readable_paths:
            suggestions.append(
                f"Use the Python read-text-file skill to read {readable_paths[0]} and show me the contents."
            )
    if any("Python Commands 03" in title for title in context.skill_titles):
        suggestions.append(
            "Use the Python write-text-file skill to create exports/summary.txt with a short summary of the current workspace."
        )
    if context.imported_skill_titles:
        first_title = context.imported_skill_titles[0]
        suggestions.append(f'Use the skill titled "{first_title}".')
    return _ordered_unique_non_empty_strings(suggestions)[:_SUGGESTION_LIMIT]


def _skill_match_query(buffer_text: str) -> str:
    return collapse_ws(str(buffer_text or ""))


def _skill_match_keywords(buffer_text: str) -> tuple[str, ...]:
    collapsed = _skill_match_query(buffer_text)
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", collapsed.casefold())
        if len(token) >= 2 and token not in _SKILL_MATCH_STOPWORDS
    ]
    return tuple(_ordered_unique_non_empty_strings(tokens))


def _matching_skill_title_candidates(*, context: WorkstationChatContext, buffer_text: str) -> list[str]:
    title_query = _skill_match_query(buffer_text)
    keywords = _skill_match_keywords(buffer_text)
    if not title_query or not keywords:
        return []
    ordered_titles = _ordered_unique_non_empty_strings(
        list(context.imported_skill_titles) + list(context.builtin_skill_titles) + list(context.skill_titles)
    )
    query_lower = title_query.casefold()
    scored_matches: list[tuple[tuple[int, int, int, int, int], str]] = []
    for index, title in enumerate(ordered_titles):
        title_lower = title.casefold()
        if title_lower == query_lower:
            continue
        title_tokens = [token for token in re.split(r"[^a-z0-9]+", title_lower) if token]
        matched_keyword_count = 0
        prefix_match_count = 0
        exact_token_match_count = 0
        for keyword in keywords:
            exact_token_match = keyword in title_tokens
            token_prefix = any(token.startswith(keyword) for token in title_tokens)
            if not (exact_token_match or token_prefix):
                continue
            matched_keyword_count += 1
            if exact_token_match:
                exact_token_match_count += 1
            if token_prefix:
                prefix_match_count += 1
        if matched_keyword_count == 0:
            continue
        scored_matches.append(
            (
                (
                    0 if matched_keyword_count == len(keywords) else 1,
                    len(keywords) - matched_keyword_count,
                    0 if prefix_match_count > 0 else 1,
                    0 if exact_token_match_count > 0 else 1,
                    len(title),
                    index,
                ),
                title,
            )
        )
    scored_matches.sort(key=lambda item: item[0])
    return [title for _score, title in scored_matches]


def _replace_skill_query_fragment(*, buffer_text: str, skill_title: str) -> str:
    current_text = str(buffer_text or "")
    selected_title = str(skill_title or "")
    if not collapse_ws(selected_title):
        return current_text
    title_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", selected_title.casefold())
        if len(token) >= 2 and token not in _SKILL_MATCH_STOPWORDS
    ]
    if not title_tokens:
        return selected_title
    token_matches = list(re.finditer(r"[A-Za-z0-9]+", current_text))
    if not token_matches:
        return selected_title
    matching_indexes: list[int] = []
    for index, match in enumerate(token_matches):
        token = str(match.group(0) or "").casefold()
        if len(token) < 2 or token in _SKILL_MATCH_STOPWORDS:
            continue
        token_start = match.start()
        token_end = match.end()
        if (
            (token_start > 0 and current_text[token_start - 1] in "./\\")
            or (token_end < len(current_text) and current_text[token_end] in "./\\")
        ):
            continue
        if any(candidate.startswith(token) for candidate in title_tokens):
            matching_indexes.append(index)
    if not matching_indexes:
        return selected_title
    last_index = matching_indexes[-1]
    first_index = last_index
    matching_index_set = set(matching_indexes)
    while first_index > 0:
        previous_index = first_index - 1
        if previous_index not in matching_index_set:
            break
        gap = current_text[token_matches[previous_index].end() : token_matches[first_index].start()]
        if any(not (character.isspace() or character in "-_/") for character in gap):
            break
        first_index = previous_index
    start = token_matches[first_index].start()
    end = token_matches[last_index].end()
    return f"{current_text[:start]}{selected_title}{current_text[end:]}"


def workstation_chat_apply_prompt_suggestion(
    *,
    context: WorkstationChatContext,
    buffer_text: str,
    suggestion: str,
) -> str:
    """
    High Level Purpose:
        In circumstances like interactive workstation prompt autosuggest selection, helps with applying one suggestion into the current prompt without discarding unrelated prompt text.

    Reference to Theory:
        Supports the outer shell UX by treating autosuggest insertion as a host-side text-edit projection rather than changing the underlying skill selection logic.

    Example Input Output:
        Input: `workstation_chat_apply_prompt_suggestion(context=ctx, buffer_text='Use AP to fetch JSON.', suggestion='API Client Commands 01')`
        Output: 'Use API Client Commands 01 to fetch JSON.'

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.
        buffer_text: Value for `buffer_text` used by `buffer_text`. Expected type: `str`.
        suggestion: Value for `suggestion` used by `suggestion`. Expected type: `str`.

    Returns:
        str: Result produced by `workstation_chat_apply_prompt_suggestion`.
    """
    selected_value = str(suggestion or "")
    if not collapse_ws(selected_value):
        return str(buffer_text or "")
    if selected_value.strip().casefold() == "/resume-research-with-llm":
        return "/resume-research-with-llm "
    if selected_value.strip().casefold() == "/start-research-into":
        return "/start-research-into "
    skill_title_pool = {title.casefold() for title in context.skill_titles}
    if selected_value.casefold() in skill_title_pool:
        return _replace_skill_query_fragment(buffer_text=str(buffer_text or ""), skill_title=selected_value)
    return selected_value


def workstation_chat_completion_candidates(
    *,
    context: WorkstationChatContext,
    buffer_text: str,
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like enhanced workstation chat tab completion, helps with producing context-sensitive completions for slash commands, skill titles, paths, and approval answers.

    Reference to Theory:
        Supports the workstation shell UX by making likely prompt continuations available at the outer chat boundary rather than encoding them into the underlying skill/session logic.

    Example Input Output:
        Input: `workstation_chat_completion_candidates(context=ctx, buffer_text='Import the skill file at tr')`
        Output: ['Import the skill file at trials/python.skill.yaml into this workstation.']

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.
        buffer_text: Value for `buffer_text` used by `buffer_text`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `workstation_chat_completion_candidates`.
    """
    normalized = str(buffer_text or "")
    stripped = normalized.lstrip()
    slash_prefix = stripped.casefold()
    lower = collapse_ws(stripped).casefold()
    if not lower:
        return workstation_chat_suggestions(context) + list(_CHAT_SLASH_COMMANDS)
    if lower in {"y", "ye", "yes", "n", "no"}:
        return list(_YES_NO_CHOICES)
    if stripped.startswith("/"):
        if slash_prefix == "/prepare-last-assistant-markdown":
            return ["/prepare-last-assistant-markdown"]
        if slash_prefix == "/resume-research-with-llm":
            return ["/resume-research-with-llm "]
        if slash_prefix.startswith("/resume-research-with-llm "):
            prefix = stripped[len("/resume-research-with-llm ") :]
            return _subject_title_completion_candidates(
                context=context,
                raw_prefix=prefix,
                command_name="/resume-research-with-llm",
            )
        if slash_prefix == "/start-research-into":
            return ["/start-research-into "]
        if slash_prefix.startswith("/start-research-into "):
            prefix = stripped[len("/start-research-into ") :]
            return _subject_title_completion_candidates(
                context=context,
                raw_prefix=prefix,
                command_name="/start-research-into",
            )
        if lower.startswith("/import-skill "):
            if not _context_can_suggest_workspace_paths(context):
                return []
            prefix = stripped[len("/import-skill ") :]
            return [
                f"/import-skill {candidate}"
                for candidate in context.workspace_paths
                if candidate.endswith((".yaml", ".yml")) and candidate.startswith(prefix)
            ]
        if lower.startswith("/describe-skill "):
            prefix = stripped[len("/describe-skill ") :].casefold()
            return [
                f'/describe-skill "{title}"'
                for title in context.skill_titles
                if title.casefold().startswith(prefix)
            ]
        if lower.startswith("/permissions "):
            prefix = stripped[len("/permissions ") :].casefold()
            return [
                f'/permissions "{title}"'
                for title in context.skill_titles
                if title.casefold().startswith(prefix)
            ]
        if lower.startswith("/grant-permission "):
            prefix = stripped[len("/grant-permission ") :].casefold()
            return [
                f"/grant-permission {capability}"
                for capability in _grantable_capability_candidates(context)
                if capability.casefold().startswith(prefix)
            ]
        if lower.startswith("/export-skill "):
            return _slash_export_skill_completion_candidates(context=context, stripped=stripped)
        if lower.startswith("/revoke-permission "):
            prefix = stripped[len("/revoke-permission ") :].casefold()
            return [
                f"/revoke-permission {capability}"
                for capability in _revocable_capability_candidates(context)
                if capability.casefold().startswith(prefix)
            ]
        return [command for command in _CHAT_SLASH_COMMANDS if command.startswith(stripped)]
    if lower.startswith("import the skill file at "):
        prefix = stripped[len("Import the skill file at ") :]
        return [
            f"Import the skill file at {candidate} into this workstation."
            for candidate in context.workspace_paths
            if candidate.endswith((".yaml", ".yml")) and candidate.startswith(prefix)
        ]
    if lower.startswith("use the skill titled \"") or lower.startswith("export the skill titled \""):
        quote_prefix = stripped.split('"', 1)[0] + '"'
        title_prefix = stripped[len(quote_prefix) :]
        suffix = '"' if lower.startswith("use the skill titled \"") else '"'
        return [
            f"{quote_prefix}{title}{suffix}"
            for title in context.skill_titles
            if title.casefold().startswith(title_prefix.casefold())
        ]
    if lower.startswith("use the python read-text-file skill to read "):
        prefix = stripped[len("Use the Python read-text-file skill to read ") :]
        return [
            f"Use the Python read-text-file skill to read {candidate} and show me the contents."
            for candidate in context.workspace_paths
            if candidate.startswith(prefix)
        ]
    if lower.startswith("use the python write-text-file skill to create "):
        prefix = stripped[len("Use the Python write-text-file skill to create ") :]
        return [
            f"Use the Python write-text-file skill to create {candidate} with a short summary of the current workspace."
            for candidate in context.workspace_paths
            if candidate.startswith(prefix)
        ] + [
            f"Use the Python write-text-file skill to create exports/summary.txt with a short summary of the current workspace."
            if "exports/summary.txt".startswith(prefix)
            else ""
        ]
    skill_candidates = _matching_skill_title_candidates(context=context, buffer_text=normalized)
    if skill_candidates:
        return skill_candidates
    generic_candidates = workstation_chat_suggestions(context) + list(_CHAT_SLASH_COMMANDS)
    return [
        candidate
        for candidate in _ordered_unique_non_empty_strings(generic_candidates)
        if candidate.casefold().startswith(stripped.casefold())
    ]


def workstation_chat_live_suggestions(
    *,
    context: WorkstationChatContext,
    buffer_text: str,
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like persistent workstation shell suggestions, helps with projecting the current input buffer into a short visible suggestion list instead of only showing generic global hints.

    Reference to Theory:
        Supports the richer shell UX by keeping visible suggestions aligned with the current input context while leaving the underlying completion and execution logic unchanged.

    Example Input Output:
        Input: `workstation_chat_live_suggestions(context=ctx, buffer_text='/')`
        Output: ['/help', '/list-skills', '/permissions']

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.
        buffer_text: Value for `buffer_text` used by `buffer_text`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `workstation_chat_live_suggestions`.
    """
    normalized = str(buffer_text or "")
    stripped = normalized.strip()
    slash_prefix = normalized.lstrip().casefold()
    if not stripped:
        return workstation_chat_suggestions(context)
    if stripped == "/":
        return ["/help", "/prepare-markdown", "/prepare-last-assistant-markdown", "/start-research"]
    if normalized.lstrip().startswith("/"):
        slash_candidates = workstation_chat_completion_candidates(context=context, buffer_text=normalized)
        if slash_prefix.startswith("/resume-research-with-llm ") or slash_prefix.startswith("/start-research-into "):
            return slash_candidates
        return slash_candidates[:_SUGGESTION_LIMIT]
    matching_skill_titles = _matching_skill_title_candidates(context=context, buffer_text=normalized)
    if matching_skill_titles:
        return matching_skill_titles
    return workstation_chat_completion_candidates(context=context, buffer_text=normalized)[:_SUGGESTION_LIMIT]


def workstation_chat_inline_completion(
    *,
    context: WorkstationChatContext,
    buffer_text: str,
) -> str | None:
    """
    High Level Purpose:
        In circumstances like Textual inline completion, helps with producing one low-latency completion candidate for the current input buffer instead of evaluating the broader visible-suggestion surface.

    Reference to Theory:
        Supports a responsive host-owned chat UI by narrowing the autosuggest path to prompt-local completion cases while leaving the richer suggestion system available elsewhere.

    Example Input Output:
        Input: `workstation_chat_inline_completion(context=ctx, buffer_text='/he')`
        Output: '/help'

    Args:
        context: Value for `context` used by `context`. Expected type: `WorkstationChatContext`.
        buffer_text: Value for `buffer_text` used by `buffer_text`. Expected type: `str`.

    Returns:
        str | None: Result produced by `workstation_chat_inline_completion`.
    """
    value = str(buffer_text or "")
    stripped = value.strip()
    slash_prefix = value.lstrip().casefold()
    if not stripped or len(value) > 240:
        return None
    lower = collapse_ws(stripped).casefold()
    candidate_pool: list[str]
    if stripped == "/":
        candidate_pool = ["/help", "/prepare-markdown", "/prepare-last-assistant-markdown", "/start-research"]
    elif value.lstrip().startswith("/"):
        if slash_prefix.startswith("/resume-research-with-llm ") or slash_prefix.startswith("/start-research-into "):
            return None
        candidate_pool = workstation_chat_completion_candidates(context=context, buffer_text=value)[:_SUGGESTION_LIMIT]
    elif lower in {"y", "ye", "yes", "n", "no"}:
        candidate_pool = list(_YES_NO_CHOICES)
    elif (
        lower.startswith("import the skill file at ")
        or lower.startswith("use the skill titled \"")
        or lower.startswith("export the skill titled \"")
        or lower.startswith("use the python read-text-file skill to read ")
        or lower.startswith("use the python write-text-file skill to create ")
    ):
        candidate_pool = workstation_chat_completion_candidates(context=context, buffer_text=value)[:1]
    else:
        return None
    for candidate in candidate_pool:
        if candidate.casefold().startswith(value.casefold()) and candidate != value:
            return candidate
    return None


def _textual_status_text(state: _WorkstationChatPaneState) -> str:
    return _plain_ui_text(state.input_status_text())


def _textual_prompt_label_text(state: _WorkstationChatPaneState) -> str:
    if state.awaiting_approval():
        return "approve>"
    return "workstation>"


if (
    TextualApp is not None
    and TextualButton is not None
    and TextualInput is not None
    and TextualLog is not None
    and TextualRichLog is not None
    and TextualStatic is not None
    and TextualSuggester is not None
):

    class _WorkstationTextualInput(TextualInput):
        pass

    class _TextualWorkstationChatApp(TextualApp[int]):
        CSS = TEXTUAL_CHAT_CSS

        BINDINGS = [
            TextualBinding("tab", "focus_next_panel", "Next Panel", show=False, priority=True),
            TextualBinding("shift+tab", "next_tab", "Next Tab", show=False, priority=True),
            TextualBinding("f6", "next_tab", "Next Tab"),
            TextualBinding("ctrl+f6", "previous_tab", "Previous Tab"),
            TextualBinding("f8", "toggle_maximized_pane", "Maximize / Restore Pane", show=False, priority=True),
            TextualBinding("ctrl+c", "copy_selection_or_cancel", "Copy / Cancel"),
            TextualBinding("ctrl+shift+c,super+c", "copy_selected_text", "Copy Selected Text", show=False),
            TextualBinding("escape", "cancel_or_interrupt", "Cancel", show=False),
            TextualBinding("up", "history_previous", "Prev History"),
            TextualBinding("down", "history_next", "Next History"),
        ]

        def __init__(
            self,
            *,
            root: Path,
            model: str | None,
            max_tool_rounds: int,
            subject_workflow_client: SubjectWorkflowClient | None = None,
            shell_client: WorkstationShellClient | None = None,
        ) -> None:
            super().__init__(ansi_color=False)
            root_path = Path(root).expanduser().resolve()
            self._root = root_path
            self._model = model
            self._max_tool_rounds = max_tool_rounds
            self._subject_workflow_client = (
                subject_workflow_client or _create_textual_subject_workflow_client()
            )
            self._shell_client = shell_client or InProcessWorkstationShellClient(
                client_session_id=self._subject_workflow_client.client_session_id
            )
            initial_snapshot = self._shell_client.get_chat_snapshot(root_path=root_path)
            initial_activity = self._shell_client.get_activity_view(root_path=root_path, limit=_ACTIVITY_PANE_MAX_LINES)
            initial_permissions = self._shell_client.get_permissions_view(root_path=root_path)
            initial_skills = self._shell_client.get_skills_view(root_path=root_path)
            self._state = _WorkstationChatPaneState(
                root=root_path,
                context=initial_snapshot.context,
                transcript_entries=_transcript_entries_from_messages(initial_snapshot.messages),
                shell_client=self._shell_client,
                shell_activity_text_cache=initial_activity.text,
                shell_permissions_text_cache=initial_permissions.text,
                shell_skills_text_cache=initial_skills.text,
                shell_transcript_snapshot_version=initial_snapshot.snapshot_version,
                shell_activity_snapshot_version=initial_activity.snapshot_version,
                shell_permissions_snapshot_version=initial_permissions.snapshot_version,
                shell_skills_snapshot_version=initial_skills.snapshot_version,
            )
            self._state.application = self
            self._history = _workstation_prompt_history_entries(root_path)
            self._history_index = len(self._history)
            self._projection_controller = WorkstationProjectionSubscriberController(
                root_path=root_path,
                activity_limit=_ACTIVITY_PANE_MAX_LINES,
            )
            self._markdown_action_result: dict[str, Any] | None = None
            self._markdown_export_result: dict[str, Any] | None = None
            self._markdown_status_text = ""
            self._markdown_busy = False
            self._markdown_selected_path: Path | None = None
            self._markdown_pending_paths: tuple[Path, ...] = ()
            self._learning_source_label = ""
            self._learning_source_field_label = "Markdown"
            self._learning_ingress_title = "Markdown Ingress"
            self._markdown_busy_started_at: float | None = None
            self._research_projection_input_cache_key: tuple[bool, str, str, bool] | None = None
            self._active_tab_id_value = "chat_tab"
            self._selected_prompt_suggestion_index = 0
            self._tab_refresh_request_id = 0
            self._tab_refresh_worker_active = False
            self._tab_refresh_worker_request_id = 0
            self._transcript_follow_bottom_until: float | None = None
            self._mock_subject_scenarios: tuple[MockSubjectScenario, ...] = ()
            self._mock_subject_progress_by_key: dict[str, MockSubjectProgress] = {}
            self._dirty_subject_progress_keys: set[str] = set()
            self._mock_subject_index = 0
            self._mock_subject_status_text = "Live subject workflow ready."
            self._subject_projection_backend = TextualSubjectWorkflowProjectionBackend(self._subject_workflow_client)
            self._shell_watch_thread: threading.Thread | None = None
            self._shell_watch_stop_event: threading.Event | None = None
            self._shell_watch_last_sequence = -1
            self._subject_workflow_watch_thread: threading.Thread | None = None
            self._subject_workflow_watch_stop_event: threading.Event | None = None
            self._subject_workflow_watch_key: tuple[str, str, bool, str, str, bool] | None = None
            self._subject_workflow_watch_last_sequence = -1
            self._subject_gate_action_targets: dict[str, tuple[str, str]] = {}
            self._subject_snapshot_cache: dict[str, Any] = {}
            self._subject_local_interaction_fingerprints: dict[str, str] = {}
            self._draft_cursor_sync_request_id = 0
            self._draft_model_deferred_refresh_request_id = 0
            self._programmatic_data_table_cursor_event_counts: dict[str, dict[int, int]] = {}
            self._pending_data_table_cursor_actions: dict[tuple[str, int], int] = {}
            self._programmatic_switch_change_counts: dict[str, dict[bool, int]] = {}
            self._maximized_pane_id: str | None = None
            self._info_pane_id: str | None = None
            self._detached_pane_spec: dict[str, str] | None = None
            self._rendered_log_lines: dict[str, tuple[str, ...]] = {}
            self._pane_header_titles: dict[str, str] = {}
            self._inventory_option_sync_suppressed: set[str] = set()
            self._pending_review_scope_tree_sync_entry_id = ""
            self._suppress_select_events = False
            self._suppress_selection_list_events = False
            self._suppress_switch_events = False
            self._suppress_tabs_events = False
            self._tabs_events_ready = False
            self._app_worker_threads: set[threading.Thread] = set()
            self._app_worker_threads_lock = threading.Lock()
            self._reload_mock_subject_scenarios()

        def compose(self) -> ComposeResult:  # pragma: no cover - requires textual runtime
            with Vertical():
                with Horizontal(id="tab_bar"):
                    for dom_id in self._tab_ids():
                        yield TextualButton(
                            self._tab_title(dom_id),
                            id=f"tab_button_{dom_id}",
                            classes="tab_button",
                        )
                with Vertical(id="root_tabs"):
                    with Vertical(id="chat_tab", classes="tab_body"):
                        yield TextualStatic(id="chat_status_panel")
                        yield TextualStatic(id="chat_activity_panel")
                        with Vertical(id="transcript_panel"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("transcript"), classes="pane_header_title")
                                yield TextualButton("Copy", id="copy_transcript_button", classes="transcript_copy_button")
                                yield TextualButton("i", id=_textual_pane_info_button_id("transcript"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("transcript"), classes="pane_icon_button")
                            yield TextualRichLog(id="transcript", auto_scroll=True, highlight=False, wrap=True, min_width=0)
                        with Vertical(id="chat_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("chat_tab"), classes="pane_header_title")
                            yield TextualLog(id="chat_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        with Horizontal(id="composer"):
                            yield TextualStatic(id="prompt_label")
                            yield _WorkstationTextualInput(
                                placeholder="Type a prompt or /help",
                                id="input",
                            )
                            yield TextualStatic(id="inline_hint")
                        yield TextualLog(id="suggestion_bar", auto_scroll=False, highlight=False)
                        yield TextualStatic(
                            "Enter sends. Up/Down: suggestions. Tab: accept. Shift+Tab: tabs. F8: pane. Ctrl+C: copy pane text.",
                            id="hintbar",
                        )
                    with Vertical(id="learn_tab", classes="tab_body"):
                        with Horizontal(classes="subject_page_header_row"):
                            yield TextualStatic(
                                id=_subject_header_subject_id("research"),
                                classes="subject_page_title",
                            )
                            with Horizontal(classes="subject_page_nav_row"):
                                yield TextualButton("Previous Subject", id="subject_prev_button", classes="subject_action_button subject_nav_button")
                                yield TextualButton("Next Subject", id="subject_next_button", classes="subject_action_button subject_nav_button")
                        with Horizontal(id="research_gate_bar", classes="subject_gate_bar"):
                            with Vertical(
                                id=_subject_gate_panel_id("research", "review"),
                                classes="subject_gate_panel",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("research", "review"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("research", "review"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("research", "review"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "review")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("research", "review")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "review")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("research", "review")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "review")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("research", "review")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "review")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("research", "review")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                            with Vertical(
                                id=_subject_gate_panel_id("research", "publication"),
                                classes="subject_gate_panel subject_gate_panel_last",
                            ):
                                yield TextualDataTable(
                                    id=_subject_gate_status_table_id("research", "publication"),
                                    classes="subject_gate_status_table",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("research", "publication"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("research", "publication"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "publication")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("research", "publication")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "publication")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("research", "publication")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "publication")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("research", "publication")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("research", "publication")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("research", "publication")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                        with Vertical(id="learn_actions_panel"):
                            with Horizontal(id=_subject_controls_header_row_id("research"), classes="subject_controls_header_row"):
                                with Vertical(classes="subject_header_main"):
                                    yield TextualStatic(id="subject_flow_header", classes="subject_flow_header")
                                    yield TextualStatic(id="learn_ingress_panel")
                            with Horizontal(id=_subject_phase_action_row_id("research"), classes="subject_action_row subject_phase_action_row"):
                                yield TextualButton("Action 1", id=_subject_action_button_ids("research")[0], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 2", id=_subject_action_button_ids("research")[1], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 3", id=_subject_action_button_ids("research")[2], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 4", id=_subject_action_button_ids("research")[3], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Learn Markdown", id="learn_markdown_button", classes="subject_action_button secondary_action_button")
                                yield TextualButton("Learn URL", id="learn_url_button", classes="subject_action_button secondary_action_button")
                                yield TextualButton("Export Learned", id="export_learned_button", classes="subject_action_button secondary_action_button")
                                yield TextualStatic("", classes="subject_action_row_spacer")
                                yield TextualButton(
                                    _subject_hidden_pane_button_label("research"),
                                    id=_subject_hidden_pane_button_id("research"),
                                    classes="subject_header_utility_button",
                                )
                                yield TextualButton("Journal", id=_subject_journal_button_id("research"), classes="subject_header_utility_button")
                            with Horizontal(id="research_choice_row", classes="subject_choice_row"):
                                with Vertical(classes="subject_choice_field"):
                                    yield TextualStatic("Source Set", classes="subject_choice_label")
                                    yield TextualSelect(
                                        [],
                                        prompt="Source Set",
                                        allow_blank=True,
                                        compact=True,
                                        disabled=True,
                                        id=_research_source_collection_select_id(),
                                        classes="subject_choice_select",
                                    )
                                with Vertical(classes="subject_choice_field"):
                                    yield TextualStatic("Revision Baseline", classes="subject_choice_label")
                                    yield TextualSelect(
                                        [],
                                        prompt="Revision Baseline",
                                        allow_blank=True,
                                        compact=True,
                                        disabled=True,
                                        id=_research_source_revision_baseline_select_id(),
                                        classes="subject_choice_select",
                                    )
                                with Vertical(classes="subject_choice_switch_field"):
                                    yield TextualStatic("In Source Set", classes="subject_choice_label")
                                    yield TextualSwitch(
                                        False,
                                        id=_research_source_collection_membership_switch_id(),
                                        classes="subject_choice_switch",
                                        disabled=True,
                                    )
                        with Horizontal(id="subject_research_workbench"):
                            with Vertical(id="subject_sources_panel_shell", classes="subject_research_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("subject_sources_panel"), classes="pane_header_title")
                                    yield TextualButton("@llm", id=_research_sources_llm_button_id(), classes="pane_header_text_button")
                                    yield TextualButton("=", id=_research_sources_manual_rephrase_button_id(), classes="pane_icon_button")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("subject_sources_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("subject_sources_panel"), classes="pane_icon_button")
                                yield _FocusableTextualDataTable(id="subject_sources_panel", classes="max_panel_body_log")
                            yield _FocusableTextualDataTable(id="subject_observation_panel", classes="subject_research_panel")
                        with Vertical(id="subject_target_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("subject_target_panel"), classes="pane_header_title")
                                yield TextualButton("@llm", id=_research_detail_llm_button_id(), classes="pane_header_text_button")
                                yield TextualButton("=", id=_research_detail_manual_rephrase_button_id(), classes="pane_icon_button")
                                yield TextualButton("i", id=_textual_pane_info_button_id("subject_target_panel"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("subject_target_panel"), classes="pane_icon_button")
                            yield _FocusableTextualDataTable(id="subject_target_panel", classes="max_panel_body_log")
                            yield TextualStatic("", id=_research_source_revision_history_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_revision_history_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_change_summary_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_change_summary_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_collection_member_export_status_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_collection_member_export_status_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_collection_member_revision_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_collection_member_revision_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_collection_merge_export_history_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_collection_merge_export_history_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_collection_actionable_export_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_collection_actionable_export_table_id(), classes="subject_target_table")
                            yield TextualStatic("", id=_research_source_collection_export_applied_table_title_id(), classes="subject_target_table_title")
                            yield TextualDataTable(id=_research_source_collection_export_applied_table_id(), classes="subject_target_table")
                        with Vertical(id="learn_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("learn_tab"), classes="pane_header_title")
                            yield TextualLog(id="learn_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        with Vertical(id="learn_result_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("learn_result"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("learn_result"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("learn_result"), classes="pane_icon_button")
                            yield TextualLog(id="learn_result", auto_scroll=True, highlight=False, classes="max_panel_body_log")
                    with Vertical(id="itemize_tab", classes="tab_body"):
                        with Horizontal(classes="subject_page_header_row"):
                            yield TextualStatic(
                                id=_subject_header_subject_id("itemize"),
                                classes="subject_page_title",
                            )
                            with Horizontal(classes="subject_page_nav_row"):
                                yield TextualButton("Previous Subject", id=_subject_nav_button_id("itemize", "prev"), classes="subject_action_button subject_nav_button")
                                yield TextualButton("Next Subject", id=_subject_nav_button_id("itemize", "next"), classes="subject_action_button subject_nav_button")
                        with Horizontal(id="itemize_gate_bar", classes="subject_gate_bar"):
                            with Vertical(
                                id=_subject_gate_panel_id("itemize", "review"),
                                classes="subject_gate_panel",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("itemize", "review"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("itemize", "review"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("itemize", "review"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "review")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("itemize", "review")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "review")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("itemize", "review")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "review")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("itemize", "review")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "review")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("itemize", "review")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                            with Vertical(
                                id=_subject_gate_panel_id("itemize", "publication"),
                                classes="subject_gate_panel subject_gate_panel_last",
                            ):
                                yield TextualDataTable(
                                    id=_subject_gate_status_table_id("itemize", "publication"),
                                    classes="subject_gate_status_table",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("itemize", "publication"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("itemize", "publication"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "publication")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("itemize", "publication")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "publication")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("itemize", "publication")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "publication")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("itemize", "publication")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("itemize", "publication")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("itemize", "publication")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                        with Vertical(id="itemize_actions_panel"):
                            with Horizontal(id=_subject_controls_header_row_id("itemize"), classes="subject_controls_header_row"):
                                with Vertical(classes="subject_header_main"):
                                    yield TextualStatic(id="itemize_flow_header", classes="subject_flow_header")
                            with Horizontal(id=_subject_phase_action_row_id("itemize"), classes="subject_action_row subject_phase_action_row"):
                                yield TextualButton("Action 1", id=_subject_action_button_ids("itemize")[0], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 2", id=_subject_action_button_ids("itemize")[1], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 3", id=_subject_action_button_ids("itemize")[2], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 4", id=_subject_action_button_ids("itemize")[3], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualStatic("", classes="subject_action_row_spacer")
                                yield TextualButton(
                                    _subject_hidden_pane_button_label("itemize"),
                                    id=_subject_hidden_pane_button_id("itemize"),
                                    classes="subject_header_utility_button",
                                )
                                yield TextualButton("Journal", id=_subject_journal_button_id("itemize"), classes="subject_header_utility_button")
                            with Horizontal(id="itemize_choice_row", classes="subject_choice_row"):
                                with Vertical(classes="subject_choice_field"):
                                    yield TextualStatic("Decision Role", classes="subject_choice_label")
                                    yield TextualSelect(
                                        [],
                                        id=_itemize_decision_role_select_id(),
                                        allow_blank=True,
                                        prompt="Decision Role",
                                        compact=True,
                                        classes="subject_choice_select",
                                    )
                                with Vertical(classes="subject_choice_switch_field"):
                                    yield TextualStatic("Hold For Merge", classes="subject_choice_label")
                                    yield TextualSwitch(
                                        False,
                                        id=_itemize_hold_switch_id(),
                                        classes="subject_choice_switch",
                                    )
                        with Horizontal(id="subject_itemize_workbench"):
                            with Vertical(id="itemize_inventory_wrapper", classes="subject_itemize_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("itemize_inventory_panel"), classes="pane_header_title")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("itemize_inventory_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("itemize_inventory_panel"), classes="pane_icon_button")
                                yield _FocusableTextualOptionList(id="itemize_inventory_panel", classes="max_panel_body_log inventory_option_list")
                            with Vertical(id="itemize_detail_wrapper", classes="subject_itemize_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("itemize_detail_panel"), classes="pane_header_title")
                                    yield TextualButton("@llm", id=_itemize_detail_llm_button_id(), classes="pane_header_text_button")
                                    yield TextualButton("=", id=_itemize_detail_manual_rephrase_button_id(), classes="pane_icon_button")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("itemize_detail_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("itemize_detail_panel"), classes="pane_icon_button")
                                yield _FocusableTextualDataTable(id="itemize_detail_panel", classes="max_panel_body_log")
                        with Vertical(id="itemize_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("itemize_tab"), classes="pane_header_title")
                            yield TextualLog(id="itemize_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        with Vertical(id="itemize_target_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("itemize_target_panel"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("itemize_target_panel"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("itemize_target_panel"), classes="pane_icon_button")
                            yield _FocusableTextualDataTable(id="itemize_target_panel", classes="max_panel_body_log")
                        with Vertical(id="itemize_result_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("itemize_result"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("itemize_result"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("itemize_result"), classes="pane_icon_button")
                            yield TextualLog(id="itemize_result", auto_scroll=True, highlight=False, classes="max_panel_body_log")
                    with Vertical(id="draft_tab", classes="tab_body"):
                        with Horizontal(classes="subject_page_header_row"):
                            yield TextualStatic(
                                id=_subject_header_subject_id("draft"),
                                classes="subject_page_title",
                            )
                            with Horizontal(classes="subject_page_nav_row"):
                                yield TextualButton("Previous Subject", id=_subject_nav_button_id("draft", "prev"), classes="subject_action_button subject_nav_button")
                                yield TextualButton("Next Subject", id=_subject_nav_button_id("draft", "next"), classes="subject_action_button subject_nav_button")
                        with Horizontal(id="draft_gate_bar", classes="subject_gate_bar"):
                            with Vertical(
                                id=_subject_gate_panel_id("draft", "review"),
                                classes="subject_gate_panel",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("draft", "review"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("draft", "review"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("draft", "review"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "review")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("draft", "review")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "review")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("draft", "review")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "review")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("draft", "review")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "review")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("draft", "review")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                            with Vertical(
                                id=_subject_gate_panel_id("draft", "publication"),
                                classes="subject_gate_panel subject_gate_panel_last",
                            ):
                                yield TextualDataTable(
                                    id=_subject_gate_status_table_id("draft", "publication"),
                                    classes="subject_gate_status_table",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("draft", "publication"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("draft", "publication"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "publication")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("draft", "publication")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "publication")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("draft", "publication")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "publication")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("draft", "publication")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("draft", "publication")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("draft", "publication")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                        with Vertical(id="draft_actions_panel"):
                            with Horizontal(id=_subject_controls_header_row_id("draft"), classes="subject_controls_header_row"):
                                with Vertical(classes="subject_header_main"):
                                    yield TextualStatic(id="draft_flow_header", classes="subject_flow_header")
                            with Horizontal(id=_subject_phase_action_row_id("draft"), classes="subject_action_row subject_phase_action_row"):
                                yield TextualButton("Action 1", id=_subject_action_button_ids("draft")[0], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 2", id=_subject_action_button_ids("draft")[1], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 3", id=_subject_action_button_ids("draft")[2], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 4", id=_subject_action_button_ids("draft")[3], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualStatic("", classes="subject_action_row_spacer")
                                yield TextualButton("Journal", id=_subject_journal_button_id("draft"), classes="subject_header_utility_button")
                            with Vertical(id="draft_choice_group", classes="subject_choice_group"):
                                yield TextualStatic("Selected Item", classes="subject_choice_group_title")
                                with Horizontal(id="draft_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Semantic Kind", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_semantic_kind_select_id(),
                                            allow_blank=True,
                                            prompt="Semantic Kind",
                                            compact=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Render Style", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_render_kind_select_id(),
                                            allow_blank=True,
                                            prompt="Render Style",
                                            compact=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Evidence Mode", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_evidence_mode_select_id(),
                                            allow_blank=True,
                                            prompt="Evidence Mode",
                                            compact=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Transform Mode", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_transform_mode_select_id(),
                                            allow_blank=True,
                                            prompt="Transform Mode",
                                            compact=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_switch_field"):
                                        yield TextualStatic("In Decision", classes="subject_choice_label")
                                        yield TextualSwitch(
                                            False,
                                            id=_draft_decision_included_switch_id(),
                                            classes="subject_choice_switch",
                                        )
                            with Vertical(id="draft_model_construct_group", classes="subject_choice_group"):
                                yield TextualStatic("Selected Change", classes="subject_choice_group_title")
                                with Horizontal(id="draft_model_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Change Type", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_model_construct_sort_select_id(),
                                            allow_blank=True,
                                            prompt="Change Type",
                                            compact=True,
                                            disabled=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Change Role", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_model_construct_lane_select_id(),
                                            allow_blank=True,
                                            prompt="Change Role",
                                            compact=True,
                                            disabled=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Decision Policy", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_model_policy_profile_select_id(),
                                            allow_blank=True,
                                            prompt="Decision Policy",
                                            compact=True,
                                            disabled=True,
                                            classes="subject_choice_select",
                                        )
                            with Vertical(id="draft_model_transition_group", classes="subject_choice_group"):
                                yield TextualStatic("State Change", classes="subject_choice_group_title")
                                with Horizontal(id="draft_model_transition_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("From State", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_model_transition_source_select_id(),
                                            allow_blank=True,
                                            prompt="From State",
                                            compact=True,
                                            disabled=True,
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("To State", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            id=_draft_model_transition_target_select_id(),
                                            allow_blank=True,
                                            prompt="To State",
                                            compact=True,
                                            disabled=True,
                                            classes="subject_choice_select",
                                        )
                            with Vertical(id="draft_model_lens_group", classes="subject_choice_group"):
                                yield TextualStatic("View", classes="subject_choice_group_title")
                                with Horizontal(id="draft_model_lens_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(classes="subject_choice_tabs_field"):
                                        yield TextualStatic("Lens", classes="subject_choice_label")
                                        yield TextualTabs(
                                            TextualTab("Frame", id=_draft_model_lens_tab_id("frame")),
                                            TextualTab("Model", id=_draft_model_lens_tab_id("model")),
                                            TextualTab("Explore", id=_draft_model_lens_tab_id("explore")),
                                            id=_draft_model_lens_tabs_id(),
                                            classes="subject_choice_tabs",
                                        )
                            with Vertical(id="draft_model_relation_group", classes="subject_choice_group"):
                                yield TextualStatic("Links", classes="subject_choice_group_title")
                                with Horizontal(id="draft_model_relation_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(id=_draft_model_relation_wrapper_id(0), classes="subject_choice_list_field"):
                                        yield TextualStatic("", id=_draft_model_relation_label_id(0), classes="subject_choice_label")
                                        yield _FocusableTextualSelectionList(
                                            id=_draft_model_relation_selection_list_id(0),
                                            disabled=True,
                                            compact=True,
                                            classes="subject_choice_selection_list",
                                        )
                                    with Vertical(id=_draft_model_relation_wrapper_id(1), classes="subject_choice_list_field"):
                                        yield TextualStatic("", id=_draft_model_relation_label_id(1), classes="subject_choice_label")
                                        yield _FocusableTextualSelectionList(
                                            id=_draft_model_relation_selection_list_id(1),
                                            disabled=True,
                                            compact=True,
                                            classes="subject_choice_selection_list",
                                        )
                        with Horizontal(id="draft_scope_workbench"):
                            with Vertical(id="draft_scope_tree_wrapper", classes="review_scope_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("draft_scope_tree_panel"), classes="pane_header_title")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("draft_scope_tree_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("draft_scope_tree_panel"), classes="pane_icon_button")
                                yield _FocusableTextualDataTable(id="draft_scope_tree_panel", classes="max_panel_body_log")
                            with Vertical(id="draft_model_main_wrapper", classes="review_scope_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("draft_model_main_panel"), classes="pane_header_title")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("draft_model_main_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("draft_model_main_panel"), classes="pane_icon_button")
                                yield _FocusableTextualDataTable(id="draft_model_main_panel", classes="max_panel_body_log")
                            with Vertical(id="draft_scope_detail_wrapper", classes="review_scope_panel_wrapper"):
                                with Horizontal(classes="max_panel_header"):
                                    yield TextualStatic("", id=_textual_pane_title_widget_id("draft_scope_detail_panel"), classes="pane_header_title")
                                    yield TextualButton("@llm", id=_draft_detail_llm_button_id(), classes="pane_header_text_button")
                                    yield TextualButton("=", id=_draft_detail_manual_rephrase_button_id(), classes="pane_icon_button")
                                    yield TextualButton("i", id=_textual_pane_info_button_id("draft_scope_detail_panel"), classes="pane_icon_button")
                                    yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("draft_scope_detail_panel"), classes="pane_icon_button")
                                yield _FocusableTextualDataTable(id="draft_scope_detail_panel", classes="max_panel_body_log")
                        with Vertical(id="draft_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("draft_tab"), classes="pane_header_title")
                            yield TextualLog(id="draft_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        with Vertical(id="draft_result_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("draft_result"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("draft_result"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("draft_result"), classes="pane_icon_button")
                            yield _FocusableTextualLog(id="draft_result", auto_scroll=True, highlight=False, classes="max_panel_body_log")
                    with Vertical(id="review_tab", classes="tab_body"):
                        with Horizontal(classes="subject_page_header_row"):
                            yield TextualStatic(
                                id=_subject_header_subject_id("review"),
                                classes="subject_page_title",
                            )
                            with Horizontal(classes="subject_page_nav_row"):
                                yield TextualButton("Previous Subject", id=_subject_nav_button_id("review", "prev"), classes="subject_action_button subject_nav_button")
                                yield TextualButton("Next Subject", id=_subject_nav_button_id("review", "next"), classes="subject_action_button subject_nav_button")
                        with Horizontal(id="review_gate_bar", classes="subject_gate_bar"):
                            with Vertical(
                                id=_subject_gate_panel_id("review", "review"),
                                classes="subject_gate_panel",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("review", "review"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("review", "review"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("review", "review"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "review")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("review", "review")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "review")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("review", "review")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "review")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("review", "review")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "review")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("review", "review")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                            with Vertical(
                                id=_subject_gate_panel_id("review", "publication"),
                                classes="subject_gate_panel subject_gate_panel_last",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("review", "publication"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("review", "publication"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("review", "publication"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "publication")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("review", "publication")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "publication")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("review", "publication")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "publication")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("review", "publication")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("review", "publication")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("review", "publication")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                        with Vertical(id="review_actions_panel"):
                            with Horizontal(id=_subject_controls_header_row_id("review"), classes="subject_controls_header_row"):
                                with Vertical(classes="subject_header_main"):
                                    yield TextualStatic(id="review_flow_header", classes="subject_flow_header")
                            with Horizontal(id=_subject_phase_action_row_id("review"), classes="subject_action_row subject_phase_action_row"):
                                yield TextualButton("Action 1", id=_subject_action_button_ids("review")[0], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 2", id=_subject_action_button_ids("review")[1], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 3", id=_subject_action_button_ids("review")[2], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 4", id=_subject_action_button_ids("review")[3], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualStatic("", classes="subject_action_row_spacer")
                                yield TextualButton("Journal", id=_subject_journal_button_id("review"), classes="subject_header_utility_button")
                            with Vertical(id="review_plan_group", classes="subject_choice_group"):
                                yield TextualStatic("Report Plan", classes="subject_choice_group_title")
                                with Horizontal(id="review_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Output Style", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            prompt="Output Style",
                                            allow_blank=True,
                                            compact=True,
                                            disabled=True,
                                            id=_review_publication_output_mode_select_id(),
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Report Structure", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            prompt="Report Structure",
                                            allow_blank=True,
                                            compact=True,
                                            disabled=True,
                                            id=_review_publication_section_plan_select_id(),
                                            classes="subject_choice_select",
                                        )
                                    with Vertical(classes="subject_choice_field"):
                                        yield TextualStatic("Diff Baseline", classes="subject_choice_label")
                                        yield TextualSelect(
                                            [],
                                            prompt="Diff Baseline",
                                            allow_blank=True,
                                            compact=True,
                                            disabled=True,
                                            id=_review_publication_diff_baseline_select_id(),
                                            classes="subject_choice_select",
                                        )
                            with Horizontal(id="review_selection_group_row", classes="subject_choice_group_row"):
                                with Vertical(id="review_item_group", classes="subject_choice_group"):
                                    yield TextualStatic("Selected Item", classes="subject_choice_group_title")
                                    with Horizontal(id="review_scope_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Item", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Item",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_review_composition_unit_target_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_switch_field"):
                                            yield TextualStatic("In Report", classes="subject_choice_label")
                                            yield TextualSwitch(
                                                False,
                                                id=_review_composition_unit_included_switch_id(),
                                                classes="subject_choice_switch",
                                                disabled=True,
                                            )
                                with Vertical(id="review_section_group", classes="subject_choice_group"):
                                    yield TextualStatic("Selected Section", classes="subject_choice_group_title")
                                    with Horizontal(id="review_section_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Section", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Section",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_review_publication_section_target_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_switch_field"):
                                            yield TextualStatic("In Report", classes="subject_choice_label")
                                            yield TextualSwitch(
                                                False,
                                                id=_review_publication_section_included_switch_id(),
                                                classes="subject_choice_switch",
                                                disabled=True,
                                            )
                            with Horizontal(id="review_scope_workbench"):
                                with Vertical(id="review_scope_tree_wrapper", classes="review_scope_panel_wrapper"):
                                    with Horizontal(classes="max_panel_header"):
                                        yield TextualStatic("", id=_textual_pane_title_widget_id("review_scope_tree_panel"), classes="pane_header_title")
                                        yield TextualButton("i", id=_textual_pane_info_button_id("review_scope_tree_panel"), classes="pane_icon_button")
                                        yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("review_scope_tree_panel"), classes="pane_icon_button")
                                    yield _FocusableTextualTree("Report Scope", id="review_scope_tree_panel", classes="max_panel_body_log inventory_tree")
                                with Vertical(id="review_scope_detail_wrapper", classes="review_scope_panel_wrapper"):
                                    with Horizontal(classes="max_panel_header"):
                                        yield TextualStatic("", id=_textual_pane_title_widget_id("review_scope_detail_panel"), classes="pane_header_title")
                                        yield TextualButton("@llm", id=_review_detail_llm_button_id(), classes="pane_header_text_button")
                                        yield TextualButton("=", id=_review_detail_manual_rephrase_button_id(), classes="pane_icon_button")
                                        yield TextualButton("i", id=_textual_pane_info_button_id("review_scope_detail_panel"), classes="pane_icon_button")
                                        yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("review_scope_detail_panel"), classes="pane_icon_button")
                                    yield _FocusableTextualDataTable(id="review_scope_detail_panel", classes="max_panel_body_log")
                        with Vertical(id="review_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("review_tab"), classes="pane_header_title")
                            yield TextualLog(id="review_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        with Vertical(id="review_result_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("review_result"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("review_result"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("review_result"), classes="pane_icon_button")
                            yield TextualLog(id="review_result", auto_scroll=True, highlight=False, classes="max_panel_body_log")
                            yield TextualStatic("", id=_review_comparison_history_table_title_id(), classes="result_table_title")
                            yield TextualDataTable(id=_review_comparison_history_table_id(), classes="result_table")
                            yield TextualStatic("", id=_review_latest_receipt_table_title_id(), classes="result_table_title")
                            yield TextualDataTable(id=_review_latest_receipt_table_id(), classes="result_table")
                        yield TextualStatic(id="review_status_panel")
                    with Vertical(id="publication_tab", classes="tab_body"):
                        with Horizontal(classes="subject_page_header_row"):
                            yield TextualStatic(
                                id=_subject_header_subject_id("publication"),
                                classes="subject_page_title",
                            )
                            with Horizontal(classes="subject_page_nav_row"):
                                yield TextualButton("Previous Subject", id=_subject_nav_button_id("publication", "prev"), classes="subject_action_button subject_nav_button")
                                yield TextualButton("Next Subject", id=_subject_nav_button_id("publication", "next"), classes="subject_action_button subject_nav_button")
                        with Horizontal(id="publication_gate_bar", classes="subject_gate_bar"):
                            with Vertical(
                                id=_subject_gate_panel_id("publication", "review"),
                                classes="subject_gate_panel",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("publication", "review"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("publication", "review"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("publication", "review"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "review")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("publication", "review")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "review")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("publication", "review")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "review")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("publication", "review")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "review")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("publication", "review")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                            with Vertical(
                                id=_subject_gate_panel_id("publication", "publication"),
                                classes="subject_gate_panel subject_gate_panel_last",
                            ):
                                yield TextualStatic(
                                    id=_subject_gate_summary_id("publication", "publication"),
                                    classes="subject_gate_summary",
                                )
                                yield TextualStatic(
                                    id=_subject_gate_next_label_id("publication", "publication"),
                                    classes="subject_gate_next_label",
                                )
                                with Horizontal(id=_subject_gate_action_row_id("publication", "publication"), classes="subject_gate_action_row"):
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "publication")[0], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 1", id=_subject_gate_action_button_ids("publication", "publication")[0], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "publication")[1], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 2", id=_subject_gate_action_button_ids("publication", "publication")[1], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "publication")[2], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 3", id=_subject_gate_action_button_ids("publication", "publication")[2], classes="subject_gate_action_button")
                                    with Vertical(classes="subject_gate_action_slot subject_gate_action_slot_last"):
                                        yield TextualStatic("", id=_subject_gate_action_prefix_ids("publication", "publication")[3], classes="subject_gate_action_prefix")
                                        yield TextualButton("Next 4", id=_subject_gate_action_button_ids("publication", "publication")[3], classes="subject_gate_action_button subject_gate_action_button_last")
                        with Vertical(id="publication_actions_panel"):
                            with Horizontal(id=_subject_controls_header_row_id("publication"), classes="subject_controls_header_row"):
                                with Vertical(classes="subject_header_main"):
                                    yield TextualStatic(id="publication_flow_header", classes="subject_flow_header")
                            with Horizontal(id=_subject_phase_action_row_id("publication"), classes="subject_action_row subject_phase_action_row"):
                                yield TextualButton("Action 1", id=_subject_action_button_ids("publication")[0], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 2", id=_subject_action_button_ids("publication")[1], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 3", id=_subject_action_button_ids("publication")[2], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualButton("Action 4", id=_subject_action_button_ids("publication")[3], classes="subject_action_button secondary_action_button subject_phase_action_button")
                                yield TextualStatic("", classes="subject_action_row_spacer")
                                yield TextualButton("Journal", id=_subject_journal_button_id("publication"), classes="subject_header_utility_button")
                            with Horizontal(id="publication_plan_support_row", classes="subject_choice_group_row"):
                                with Vertical(id="publication_plan_group", classes="subject_choice_group"):
                                    yield TextualStatic("Report Plan", classes="subject_choice_group_title")
                                    with Horizontal(id="publication_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Output Style", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Output Style",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_output_mode_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Report Structure", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Report Structure",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_section_plan_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Diff Baseline", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Diff Baseline",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_diff_baseline_select_id(),
                                                classes="subject_choice_select",
                                            )
                                with Vertical(id="publication_support_group", classes="subject_choice_group"):
                                    yield TextualStatic("Selected Support", classes="subject_choice_group_title")
                                    with Horizontal(id="publication_import_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Support", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Support",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_import_target_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_switch_field"):
                                            yield TextualStatic("In Report", classes="subject_choice_label")
                                            yield TextualSwitch(
                                                False,
                                                id=_publication_import_included_switch_id(),
                                                classes="subject_choice_switch",
                                                disabled=True,
                                            )
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Use", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Use",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_import_usage_select_id(),
                                                classes="subject_choice_select",
                                            )
                            with Horizontal(id="publication_selection_group_row", classes="subject_choice_group_row"):
                                with Vertical(id="publication_item_group", classes="subject_choice_group"):
                                    yield TextualStatic("Selected Item", classes="subject_choice_group_title")
                                    with Horizontal(id="publication_unit_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Item", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Item",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_composition_unit_target_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_switch_field"):
                                            yield TextualStatic("In Report", classes="subject_choice_label")
                                            yield TextualSwitch(
                                                False,
                                                id=_publication_composition_unit_included_switch_id(),
                                                classes="subject_choice_switch",
                                                disabled=True,
                                            )
                                with Vertical(id="publication_section_group", classes="subject_choice_group"):
                                    yield TextualStatic("Selected Section", classes="subject_choice_group_title")
                                    with Horizontal(id="publication_section_choice_row", classes="subject_choice_row subject_choice_row_grouped"):
                                        with Vertical(classes="subject_choice_field"):
                                            yield TextualStatic("Section", classes="subject_choice_label")
                                            yield TextualSelect(
                                                [],
                                                prompt="Section",
                                                allow_blank=True,
                                                compact=True,
                                                disabled=True,
                                                id=_publication_section_target_select_id(),
                                                classes="subject_choice_select",
                                            )
                                        with Vertical(classes="subject_choice_switch_field"):
                                            yield TextualStatic("In Report", classes="subject_choice_label")
                                            yield TextualSwitch(
                                                False,
                                                id=_publication_section_included_switch_id(),
                                                classes="subject_choice_switch",
                                                disabled=True,
                                            )
                            with Horizontal(id="publication_scope_workbench"):
                                with Vertical(id="publication_scope_tree_wrapper", classes="review_scope_panel_wrapper"):
                                    with Horizontal(classes="max_panel_header"):
                                        yield TextualStatic("", id=_textual_pane_title_widget_id("publication_scope_tree_panel"), classes="pane_header_title")
                                        yield TextualButton("i", id=_textual_pane_info_button_id("publication_scope_tree_panel"), classes="pane_icon_button")
                                        yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("publication_scope_tree_panel"), classes="pane_icon_button")
                                    yield _FocusableTextualTree("Report Scope", id="publication_scope_tree_panel", classes="max_panel_body_log inventory_tree")
                                with Vertical(id="publication_scope_detail_wrapper", classes="review_scope_panel_wrapper"):
                                    with Horizontal(classes="max_panel_header"):
                                        yield TextualStatic("", id=_textual_pane_title_widget_id("publication_scope_detail_panel"), classes="pane_header_title")
                                        yield TextualButton("i", id=_textual_pane_info_button_id("publication_scope_detail_panel"), classes="pane_icon_button")
                                        yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("publication_scope_detail_panel"), classes="pane_icon_button")
                                    yield _FocusableTextualDataTable(id="publication_scope_detail_panel", classes="max_panel_body_log")
                        with Vertical(id="publication_result_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("publication_result"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("publication_result"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("publication_result"), classes="pane_icon_button")
                            yield TextualLog(id="publication_result", auto_scroll=True, highlight=False, classes="max_panel_body_log")
                            yield TextualStatic("", id=_publication_build_artifacts_table_title_id(), classes="result_table_title")
                            yield TextualDataTable(id=_publication_build_artifacts_table_id(), classes="result_table")
                            yield TextualStatic("", id=_publication_build_receipt_table_title_id(), classes="result_table_title")
                            yield TextualDataTable(id=_publication_build_receipt_table_id(), classes="result_table")
                            yield TextualStatic("", id=_publication_latest_receipt_table_title_id(), classes="result_table_title")
                            yield TextualDataTable(id=_publication_latest_receipt_table_id(), classes="result_table")
                        with Vertical(id="publication_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("publication_tab"), classes="pane_header_title")
                            yield TextualLog(id="publication_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                        yield TextualStatic(id="publication_status_panel")
                    with Vertical(id="permissions_tab", classes="tab_body"):
                        with Vertical(id="permissions_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("permissions"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("permissions"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("permissions"), classes="pane_icon_button")
                            yield TextualRichLog(id="permissions", auto_scroll=False, highlight=False, wrap=True, classes="max_panel_body_log")
                        with Vertical(id="permissions_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("permissions_tab"), classes="pane_header_title")
                            yield TextualLog(id="permissions_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                    with Vertical(id="activity_tab", classes="tab_body"):
                        with Vertical(id="activity_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("activity"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("activity"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("activity"), classes="pane_icon_button")
                            yield TextualRichLog(id="activity", auto_scroll=True, highlight=False, wrap=True, classes="max_panel_body_log")
                        with Vertical(id="activity_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("activity_tab"), classes="pane_header_title")
                            yield TextualLog(id="activity_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                    with Vertical(id="skills_tab", classes="tab_body"):
                        with Vertical(id="skills_panel", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_pane_title_widget_id("skills"), classes="pane_header_title")
                                yield TextualButton("i", id=_textual_pane_info_button_id("skills"), classes="pane_icon_button")
                                yield TextualButton(_PANE_EXPAND_LABEL, id=_textual_pane_toggle_button_id("skills"), classes="pane_icon_button")
                            yield TextualRichLog(id="skills", auto_scroll=False, highlight=False, wrap=True, classes="max_panel_body_log")
                        with Vertical(id="skills_info_panel_shell", classes="max_panel_shell"):
                            with Horizontal(classes="max_panel_header"):
                                yield TextualStatic("", id=_textual_info_panel_title_id("skills_tab"), classes="pane_header_title")
                            yield TextualLog(id="skills_info_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                with Vertical(id="detached_pane_shell", classes="max_panel_shell"):
                    with Horizontal(classes="max_panel_header"):
                        yield TextualStatic("", id=_textual_detached_pane_title_id(), classes="pane_header_title")
                        yield TextualButton("i", id=_textual_detached_pane_info_button_id(), classes="pane_icon_button")
                        yield TextualButton(_PANE_RESTORE_LABEL, id=_textual_detached_pane_dismiss_button_id(), classes="pane_icon_button")
                    yield TextualLog(id="detached_pane_panel", auto_scroll=False, highlight=False, classes="max_panel_body_log")
                    yield _FocusableTextualTree(
                        "Report Scope",
                        id="detached_review_scope_tree_panel",
                        classes="max_panel_body_log inventory_tree",
                    )

        def on_mount(self) -> None:  # pragma: no cover - requires textual runtime
            self.query_one("#transcript_panel", Vertical).border_title = ""
            self.query_one("#activity_panel", Vertical).border_title = ""
            self.query_one("#permissions_panel", Vertical).border_title = ""
            self.query_one("#skills_panel", Vertical).border_title = ""
            self.query_one("#learn_result_panel", Vertical).border_title = ""
            self.query_one("#itemize_result_panel", Vertical).border_title = ""
            self.query_one("#draft_result_panel", Vertical).border_title = ""
            self.query_one("#review_result_panel", Vertical).border_title = ""
            self.query_one("#publication_result_panel", Vertical).border_title = ""
            self.query_one("#review_status_panel", TextualStatic).border_title = _textual_border_title(mock_subject_status_title("review"))
            self.query_one("#publication_status_panel", TextualStatic).border_title = _textual_border_title(mock_subject_status_title("publication"))
            self.query_one("#subject_sources_panel_shell", Vertical).border_title = ""
            self.query_one("#subject_target_panel_shell", Vertical).border_title = ""
            self.query_one("#itemize_inventory_wrapper", Vertical).border_title = ""
            self.query_one("#itemize_detail_wrapper", Vertical).border_title = ""
            self.query_one("#itemize_target_panel_shell", Vertical).border_title = ""
            self.query_one("#draft_scope_tree_wrapper", Vertical).border_title = ""
            self.query_one("#draft_model_main_wrapper", Vertical).border_title = ""
            self.query_one("#draft_scope_detail_wrapper", Vertical).border_title = ""
            self.query_one("#review_scope_tree_wrapper", Vertical).border_title = ""
            self.query_one("#review_scope_detail_wrapper", Vertical).border_title = ""
            self.query_one(f"#{_textual_pane_dom_id('chat', 'status')}", TextualStatic).border_title = _textual_border_title(workstation_pane_layout("chat", "status")["title"])
            self.query_one(f"#{_textual_pane_dom_id('chat', 'activity')}", TextualStatic).border_title = _textual_border_title(workstation_pane_layout("chat", "activity")["title"])
            self.query_one(f"#{_textual_pane_dom_id('chat', 'suggestions')}", TextualLog).border_title = _textual_border_title(workstation_pane_layout("chat", "suggestions")["title"])
            self.query_one(f"#{_textual_pane_dom_id('learn_markdown', 'actions')}", Vertical).border_title = _textual_border_title("More Actions")
            self.query_one("#itemize_actions_panel", Vertical).border_title = _textual_border_title("More Actions")
            self.query_one("#draft_actions_panel", Vertical).border_title = _textual_border_title("More Actions")
            self.query_one("#review_actions_panel", Vertical).border_title = _textual_border_title("More Actions")
            self.query_one("#publication_actions_panel", Vertical).border_title = _textual_border_title("More Actions")
            self.query_one("#learn_ingress_panel", TextualStatic).display = False
            self.query_one("#inline_hint", TextualStatic).display = False
            self._set_widget_display(_subject_controls_header_row_id("research"), False)
            self._set_widget_display(_subject_controls_header_row_id("itemize"), False)
            self._set_widget_display(_subject_controls_header_row_id("draft"), False)
            self._set_widget_display(_subject_controls_header_row_id("review"), False)
            self._set_widget_display(_subject_controls_header_row_id("publication"), False)
            for phase in MOCK_SUBJECT_PHASES:
                self.query_one(
                    f"#{_subject_gate_panel_id(phase, 'review')}",
                    Vertical,
                ).border_title = _textual_bold_border_title("Current Step")
                secondary_gate_title = _subject_secondary_gate_title(phase)
                secondary_gate_panel = self.query_one(
                    f"#{_subject_gate_panel_id(phase, 'publication')}",
                    Vertical,
                )
                secondary_gate_panel.border_title = (
                    _textual_bold_border_title(secondary_gate_title)
                    if secondary_gate_title
                    else ""
                )
                secondary_gate_panel.display = bool(secondary_gate_title)
            self.query_one("#subject_observation_panel").border_title = _textual_border_title("Learned Snapshot")
            self._set_pane_header_title("subject_sources_panel", "Source Sets")
            self._set_pane_header_title("transcript", workstation_pane_layout("chat", "transcript")["title"])
            self._set_pane_header_title("subject_target_panel", self._mock_subject_research_target_title())
            self._set_pane_header_title("learn_result", self._mock_subject_workspace_title("research"))
            self._set_pane_header_title("itemize_inventory_panel", "Item Inventory")
            self._set_pane_header_title("itemize_detail_panel", "Item Detail")
            self._set_pane_header_title("itemize_target_panel", "Draft Handoff")
            self._set_pane_header_title("itemize_result", self._mock_subject_workspace_title("itemize"))
            self._set_pane_header_title("draft_scope_tree_panel", self._mock_subject_draft_tree_title())
            self._set_pane_header_title("draft_model_main_panel", self._mock_subject_draft_model_main_title())
            self._set_pane_header_title("draft_scope_detail_panel", self._mock_subject_draft_detail_title())
            self._set_pane_header_title("draft_result", self._mock_subject_draft_result_title())
            self._set_pane_header_title("review_scope_tree_panel", "Report Scope")
            self._set_pane_header_title("review_scope_detail_panel", self._mock_subject_review_scope_detail_title())
            self._set_pane_header_title("review_result", self._mock_subject_workspace_title("review"))
            self._set_pane_header_title("publication_result", self._mock_subject_workspace_title("publication"))
            self._set_pane_header_title("permissions", workstation_pane_layout("permissions", "permissions")["title"])
            self._set_pane_header_title("activity", workstation_pane_layout("activity", "activity_feed")["title"])
            self._set_pane_header_title("skills", workstation_pane_layout("skills", "skills")["title"])
            self.query_one("#detached_pane_shell", Vertical).display = False
            self.query_one("#detached_review_scope_tree_panel", _FocusableTextualTree).display = False
            self._refresh_info_pane()
            self._refresh_pane_info_buttons()
            self._refresh_subject_journal_buttons()
            self._refresh_subject_hidden_pane_buttons()
            self.set_interval(0.4, self._refresh_activity_pulse_tick)
            self.set_interval(0.5, self._refresh_learn_progress_tick)
            self._projection_controller.start(
                on_activity_line=self._state.append_activity_line,
                on_context_invalidated=self._state.refresh_context,
                on_projection_invalidated=self._handle_projection_invalidated,
            )
            self._state.projection_controller = self._projection_controller
            self._start_shell_watch()
            self._apply_active_tab_state()
            self.request_state_refresh()
            self.call_after_refresh(self._enable_tabs_events)
            self._refresh_research_detail_buttons()
            self._refresh_itemize_detail_buttons()
            self._refresh_draft_detail_buttons()
            self._refresh_pane_toggle_buttons()
            self._refresh_pane_info_buttons()
            self.query_one("#input", TextualInput).focus()
            self._refresh_workspace_body_layout()

        def _enable_tabs_events(self) -> None:
            self._tabs_events_ready = True

        def on_resize(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._refresh_workspace_body_layout()

        def on_unmount(self) -> None:  # pragma: no cover - requires textual runtime
            self._stop_shell_watch()
            self._stop_subject_workflow_watch()
            self._stop_app_workers()
            self._projection_controller.stop()
            self._state.stop_projection_controller()
            try:
                self._shell_client.close_client_session(root_path=self._root)
            except Exception:
                pass

        def request_state_refresh(self, *, clear_subject_snapshot_cache: bool = False) -> None:
            if threading.current_thread() is threading.main_thread():
                try:
                    self._refresh_from_state(clear_subject_snapshot_cache=clear_subject_snapshot_cache)
                    return
                except Exception:
                    pass
            try:
                self.call_from_thread(
                    self._refresh_from_state,
                    clear_subject_snapshot_cache=clear_subject_snapshot_cache,
                )
            except Exception:
                try:
                    self._refresh_from_state(clear_subject_snapshot_cache=clear_subject_snapshot_cache)
                except Exception:
                    pass

        def _handle_projection_invalidated(self) -> None:
            active_tab_id = self._active_tab_id()
            if active_tab_id in {"activity_tab", "permissions_tab", "skills_tab"}:
                try:
                    self.call_from_thread(self._schedule_active_tab_refresh)
                    return
                except Exception:
                    pass
            if active_tab_id not in _SUBJECT_TAB_ID_TO_PHASE:
                try:
                    self.call_from_thread(self.request_state_refresh)
                    return
                except Exception:
                    pass

        def resolve_inline_completion(self, value: str) -> str | None:
            with self._state.lock:
                context = self._state.context
            return workstation_chat_inline_completion(context=context, buffer_text=value)

        def refresh_inline_hint(self) -> None:
            try:
                self.call_from_thread(self._refresh_inline_hint)
            except Exception:
                try:
                    self._refresh_inline_hint()
                except Exception:
                    pass

        def _active_tab_id(self) -> str:
            return str(self._active_tab_id_value or "chat_tab")

        def _focused_maximizable_pane_id(self) -> str | None:
            focus_id = str(getattr(self.focused, "id", "") or "")
            return _textual_pane_id_from_focus_id(focus_id)

        def _refresh_pane_toggle_buttons(self) -> None:
            for pane_id in _TEXTUAL_MAXIMIZABLE_PANES:
                button_id = _textual_pane_toggle_button_id(pane_id)
                try:
                    button = self.query_one(f"#{button_id}", TextualButton)
                except Exception:
                    continue
                button.label = (
                    _PANE_RESTORE_LABEL
                    if collapse_ws(str(self._maximized_pane_id or "")) == pane_id
                    else _PANE_EXPAND_LABEL
                )

        def _set_pane_header_title(self, pane_id: str, title: str) -> None:
            self._pane_header_titles[collapse_ws(str(pane_id or ""))] = str(title or "")
            try:
                self.query_one(
                    f"#{_textual_pane_title_widget_id(pane_id)}",
                    TextualStatic,
                ).update(str(title or ""))
            except Exception:
                return

        def _deduplicate_pane_leading_title(
            self,
            widget_id: str,
            lines: Iterable[str],
        ) -> list[str]:
            rendered_lines = [str(line or "") for line in lines]
            title = collapse_ws(self._pane_header_titles.get(collapse_ws(widget_id), ""))
            if not title:
                return rendered_lines
            first_non_empty_index = next(
                (index for index, line in enumerate(rendered_lines) if collapse_ws(line)),
                None,
            )
            if first_non_empty_index is None:
                return rendered_lines
            first_line = collapse_ws(rendered_lines[first_non_empty_index])
            if first_line != title:
                return rendered_lines
            del rendered_lines[first_non_empty_index]
            if (
                first_non_empty_index < len(rendered_lines)
                and not collapse_ws(rendered_lines[first_non_empty_index])
            ):
                del rendered_lines[first_non_empty_index]
            return rendered_lines

        def _pane_info_visible_for(self, pane_id: str) -> bool:
            return collapse_ws(str(self._info_pane_id or "")) == collapse_ws(str(pane_id or ""))

        def _detached_pane_visible(self) -> bool:
            return self._detached_pane_spec is not None

        def _dismiss_detached_pane(self) -> None:
            spec = self._detached_pane_spec or {}
            if collapse_ws(str(spec.get("mode", ""))) == "info":
                self._info_pane_id = None
            self._detached_pane_spec = None

        def _refresh_detached_pane(self) -> None:
            spec = self._detached_pane_spec
            detached_visible = spec is not None
            self._set_widget_display("root_tabs", not detached_visible)
            self._set_widget_display("detached_pane_shell", detached_visible)
            self._refresh_workspace_body_layout()
            if not detached_visible:
                return
            detached_tree_mode = (
                collapse_ws(str(spec.get("mode", ""))) == "maximize"
                and collapse_ws(str(spec.get("pane_id", ""))) == "review_scope_tree_panel"
            )
            self._set_widget_display("detached_pane_panel", not detached_tree_mode)
            self._set_widget_display("detached_review_scope_tree_panel", detached_tree_mode)
            title = str(spec.get("title", "") or "")
            body = str(spec.get("text", "") or "")
            try:
                self.query_one(
                    f"#{_textual_detached_pane_title_id()}",
                    TextualStatic,
                ).update(title)
            except Exception:
                pass
            if detached_tree_mode:
                try:
                    self._refresh_review_scope_tree_widget("detached_review_scope_tree_panel")
                except Exception:
                    pass
                self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())
                try:
                    self.query_one("#detached_review_scope_tree_panel", _FocusableTextualTree).focus()
                except Exception:
                    pass
            else:
                try:
                    self._replace_log_text(
                        self.query_one("#detached_pane_panel", TextualLog),
                        body,
                    )
                except Exception:
                    pass
            try:
                info_button = self.query_one(
                    f"#{_textual_detached_pane_info_button_id()}",
                    TextualButton,
                )
                info_mode = collapse_ws(str(spec.get("mode", ""))) == "info"
                info_button.display = info_mode
                info_button.label = "i"
                if info_mode:
                    info_button.add_class("-active")
                else:
                    info_button.remove_class("-active")
            except Exception:
                pass

        def _refresh_workspace_body_layout(self) -> None:
            try:
                tab_bar = self.query_one("#tab_bar", Horizontal)
            except Exception:
                return
            offset_y = max(0, int(getattr(tab_bar.region, "height", 0) or 0))
            screen_height = max(1, int(getattr(self.size, "height", 0) or 0))
            body_height = max(1, screen_height - offset_y - 1)
            for widget_id in ("root_tabs", "detached_pane_shell"):
                try:
                    widget = self.query_one(f"#{widget_id}")
                except Exception:
                    continue
                try:
                    widget.styles.offset = (0, offset_y)
                    widget.styles.height = body_height
                except Exception:
                    continue

        def _pane_title_for_info(self, pane_id: str) -> str:
            try:
                widget = self.query_one(f"#{_textual_pane_title_widget_id(pane_id)}", TextualStatic)
                return collapse_ws(str(getattr(widget, "renderable", "") or getattr(widget, "_content", "") or ""))
            except Exception:
                return collapse_ws(str(pane_id or "")).replace("_", " ").title()

        def _pane_help_text(self, pane_id: str) -> str:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            if normalized_pane_id == "transcript":
                return "\n".join(
                    [
                        "Transcript",
                        "",
                        "- Scroll to inspect the running conversation.",
                        "- Copy exports the full transcript text.",
                        "- Selection in the transcript does not change workflow state.",
                    ]
                )
            if normalized_pane_id == "itemize_inventory_panel":
                return "\n".join(
                    [
                        "Item Inventory",
                        "",
                        "- Up/Down moves the selected item without wrapping.",
                        "- Enter previews the selected item.",
                        "- H holds or unholds the selected item for merge.",
                        "- Click an item row to select it directly.",
                    ]
                )
            if normalized_pane_id == "itemize_detail_panel":
                return "\n".join(
                    [
                        "Item Detail",
                        "",
                        "- Shows the currently selected item from Item Inventory.",
                        "- Preview actions update this pane.",
                    ]
                )
            if normalized_pane_id == "subject_sources_panel":
                return "\n".join(
                    [
                        "Source Sets",
                        "",
                        "- Shows the selected Gather source set and the full staged-source inventory.",
                        "- The selected source set is management context; it does not hide other staged sources.",
                        "- Use the phase action to cycle source sets.",
                        "- @llm drafts source-set metadata curation for the selected focused set.",
                        "- = opens a manual source-set curation file for the selected focused set.",
                    ]
                )
            if normalized_pane_id == "subject_target_panel":
                return "\n".join(
                    [
                        "Source Detail",
                        "",
                        "- Shows the currently selected staged source in Gather.",
                        "- Source sets stay at the source layer and provide management context for the selected source.",
                        "- @llm drafts a source-layer curation revision for the current selection.",
                        "- = opens a manual source-curation file for the current selection.",
                        "- The result is still a staged source revision; importing is still explicit.",
                    ]
                )
            if normalized_pane_id == "draft_scope_tree_panel":
                if self._draft_model_mode_active():
                    return "\n".join(
                        [
                            "Case Objects",
                            "",
                            "- Up/Down moves the selected construct without wrapping.",
                            "- Click a construct row to select it directly.",
                            "- Selection persists across Frame, Model, and Explore.",
                            "- Shift+Up/Down reorders compose items only after returning to compose mode.",
                        ]
                    )
                return "\n".join(
                    [
                        "Draft Item Inventory",
                        "",
                        "- Up/Down moves the selected draft item without wrapping.",
                        "- Shift+Up/Down reorders the selected draft item.",
                        "- Click a draft row to select it directly.",
                    ]
                )
            if normalized_pane_id == "draft_model_main_panel":
                return "\n".join(
                    [
                        "Lens View",
                        "",
                        "- Frame defines what the case is.",
                        "- Model structures relations and bindings.",
                        "- Explore shows alternatives, admissibility, and blockers.",
                    ]
                )
            if normalized_pane_id == "draft_scope_detail_panel":
                return "\n".join(
                    [
                        "Inspector",
                        "",
                        "- Shows the currently selected draft item or construct.",
                        "- @llm opens a chat follow-up for the current selection.",
                    ]
                )
            if normalized_pane_id == "review_scope_tree_panel":
                return "\n".join(
                    [
                        "Report Scope",
                        "",
                        "- Up/Down moves the selected report-scope entry without wrapping.",
                        "- Shift+Up/Down previews held-item movement.",
                        "- H holds or unholds the selected entry for reordering.",
                        "- X toggles inclusion when the selected entry is toggleable.",
                        "- R releases held items at the previewed destination.",
                        "- Enter copies the selected entry preview into the review receipt.",
                        "- Click a selectable row to select it directly.",
                    ]
                )
            if normalized_pane_id == "publication_scope_tree_panel":
                return "\n".join(
                    [
                        "Report Scope",
                        "",
                        "- Up/Down moves the selected report-scope entry without wrapping.",
                        "- X toggles inclusion when the selected entry is toggleable.",
                        "- Enter copies the selected entry preview into the publication journal.",
                        "- Click a selectable row to select it directly.",
                    ]
                )
            if normalized_pane_id == "review_scope_detail_panel":
                return "\n".join(
                    [
                        "Selection Details",
                        "",
                        "- Shows the currently selected report-scope item in detail.",
                    ]
                )
            if normalized_pane_id == "publication_scope_detail_panel":
                return "\n".join(
                    [
                        "Selection Details",
                        "",
                        "- Shows the currently selected publication report-scope item in detail.",
                    ]
                )
            return "\n".join(
                [
                    "Pane Help",
                    "",
                    "- This pane has no additional interaction notes yet.",
                ]
            )

        def _pane_maximize_text(self, pane_id: str) -> str:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            if normalized_pane_id == "review_scope_tree_panel":
                return self._mock_subject_review_scope_tree_text()
            if normalized_pane_id == "review_scope_detail_panel":
                return self._mock_subject_review_scope_detail_text()
            if normalized_pane_id == "publication_scope_tree_panel":
                return self._mock_subject_pane_text("publication", "publication_scope_tree")
            if normalized_pane_id == "publication_scope_detail_panel":
                return self._mock_subject_publication_scope_detail_text()
            return self._pane_help_text(pane_id)

        def _toggle_detached_pane_snapshot(self, pane_id: str) -> None:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            spec = self._detached_pane_spec or {}
            if (
                collapse_ws(str(spec.get("mode", ""))) == "maximize"
                and collapse_ws(str(spec.get("pane_id", ""))) == normalized_pane_id
            ):
                self._dismiss_detached_pane()
                self._refresh_detached_pane()
                self._focus_first_panel_for_active_tab()
                return
            self._detached_pane_spec = {
                "mode": "maximize",
                "pane_id": normalized_pane_id,
                "tab_id": self._active_tab_id(),
                "title": self._pane_title_for_info(normalized_pane_id),
                "text": self._pane_maximize_text(normalized_pane_id),
            }
            self._refresh_detached_pane()

        def _refresh_info_pane(self) -> None:
            active_tab_id = self._active_tab_id()
            detached_spec = self._detached_pane_spec or {}
            detached_mode = collapse_ws(str(detached_spec.get("mode", "") or ""))
            for tab_id, (shell_id, _panel_id) in _TEXTUAL_INFO_PANEL_IDS.items():
                self._set_widget_display(shell_id, False)
            info_pane_id = collapse_ws(str(self._info_pane_id or ""))
            if not info_pane_id:
                if detached_mode == "info":
                    self._dismiss_detached_pane()
                self._refresh_detached_pane()
                return
            if _TEXTUAL_INFO_PANE_TABS.get(info_pane_id) != active_tab_id:
                if detached_mode == "info":
                    self._dismiss_detached_pane()
                self._refresh_detached_pane()
                return
            title = f"Help · {self._pane_title_for_info(info_pane_id)}"
            self._detached_pane_spec = {
                "mode": "info",
                "pane_id": info_pane_id,
                "tab_id": active_tab_id,
                "title": title,
                "text": self._pane_help_text(info_pane_id),
            }
            self._refresh_detached_pane()

        def _toggle_pane_info(self, pane_id: str) -> None:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            if not normalized_pane_id:
                return
            if self._pane_info_visible_for(normalized_pane_id):
                self._info_pane_id = None
            else:
                self._info_pane_id = normalized_pane_id
                self._maximized_pane_id = None
            self._apply_active_tab_state()

        def _refresh_pane_info_buttons(self) -> None:
            for pane_id in _TEXTUAL_INFO_PANE_TABS:
                try:
                    button = self.query_one(
                        f"#{_textual_pane_info_button_id(pane_id)}",
                        TextualButton,
                    )
                except Exception:
                    continue
                button.label = "i"
                if self._pane_info_visible_for(pane_id):
                    button.add_class("-active")
                else:
                    button.remove_class("-active")
            try:
                detached_info_button = self.query_one(
                    f"#{_textual_detached_pane_info_button_id()}",
                    TextualButton,
                )
                detached_info_button.label = "i"
                if self._detached_pane_visible():
                    detached_info_button.add_class("-active")
                else:
                    detached_info_button.remove_class("-active")
            except Exception:
                pass

        def _draft_model_mode_active(self) -> bool:
            try:
                return collapse_ws(str(getattr(self._mock_subject_progress(), "draft_focus_mode", "") or "")).casefold() == "model"
            except Exception:
                return False

        def _refresh_subject_journal_buttons(self) -> None:
            maximized_pane_id = collapse_ws(str(self._maximized_pane_id or ""))
            for phase in MOCK_SUBJECT_PHASES:
                try:
                    button = self.query_one(f"#{_subject_journal_button_id(phase)}", TextualButton)
                except Exception:
                    continue
                journal_pane_id = _subject_journal_pane_id(phase)
                default_label = "Issues" if phase == "draft" and self._draft_model_mode_active() else "Journal"
                button.label = "Hide" if maximized_pane_id == journal_pane_id else default_label

        def _refresh_subject_hidden_pane_buttons(self) -> None:
            maximized_pane_id = collapse_ws(str(self._maximized_pane_id or ""))
            for phase in ("research", "itemize"):
                try:
                    button = self.query_one(f"#{_subject_hidden_pane_button_id(phase)}", TextualButton)
                except Exception:
                    continue
                pane_id = collapse_ws(str(_subject_hidden_pane_id(phase) or ""))
                button.label = "Hide" if pane_id and maximized_pane_id == pane_id else _subject_hidden_pane_button_label(phase)

        def _toggle_maximized_pane_by_id(self, pane_id: str) -> None:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            if normalized_pane_id not in _TEXTUAL_MAXIMIZABLE_PANES:
                return
            if collapse_ws(str(self._maximized_pane_id or "")) == normalized_pane_id:
                self._maximized_pane_id = None
            else:
                self._maximized_pane_id = normalized_pane_id
            self._apply_active_tab_state()
            try:
                self.query_one(f"#{normalized_pane_id}").focus()
            except Exception:
                pass
            self._schedule_active_tab_refresh()

        def _show_maximized_pane_by_id(self, pane_id: str) -> None:
            normalized_pane_id = collapse_ws(str(pane_id or ""))
            if normalized_pane_id not in _TEXTUAL_MAXIMIZABLE_PANES:
                return
            if collapse_ws(str(self._maximized_pane_id or "")) != normalized_pane_id:
                self._maximized_pane_id = normalized_pane_id
                self._apply_active_tab_state()
            try:
                self.query_one(f"#{normalized_pane_id}").focus()
            except Exception:
                pass
            self._schedule_active_tab_refresh()

        def _should_surface_subject_result_pane(self, phase: str, action_key: str, progress: Any) -> bool:
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            normalized_action = collapse_ws(str(action_key or "")).casefold()
            if normalized_phase not in {"review", "publication"}:
                return False
            if not getattr(progress, "latest_receipt_lines", None):
                return False
            return normalized_action in {
                "compare_projections",
                "preview_publication_composition",
                "preview_publication_composition_diff",
                "preview_selected_report_scope_item",
            }

        def _maximized_pane_spec(self) -> dict[str, str] | None:
            pane_id = collapse_ws(str(self._maximized_pane_id or ""))
            if not pane_id:
                return None
            spec = _TEXTUAL_MAXIMIZABLE_PANES.get(pane_id)
            if spec is None:
                return None
            if collapse_ws(spec.get("tab_id", "")) != self._active_tab_id():
                return None
            return {"pane_id": pane_id, **spec}

        def _set_widget_display(self, widget_id: str, visible: bool) -> None:
            try:
                self.query_one(f"#{widget_id}").display = bool(visible)
            except Exception:
                return

        def _set_widget_class(self, widget_id: str, class_name: str, enabled: bool) -> None:
            try:
                widget = self.query_one(f"#{widget_id}")
            except Exception:
                return
            try:
                if enabled:
                    widget.add_class(class_name)
                else:
                    widget.remove_class(class_name)
            except Exception:
                return

        def _set_scope_actions_panel_workbench_only(
            self,
            phase: str,
            enabled: bool,
            *,
            wrapper_id: str = "",
        ) -> None:
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            if normalized_phase not in {"review", "publication"}:
                return
            panel_id = f"{normalized_phase}_actions_panel"
            workbench_id = f"{normalized_phase}_scope_workbench"
            tree_wrapper_id = f"{normalized_phase}_scope_tree_wrapper"
            detail_wrapper_id = f"{normalized_phase}_scope_detail_wrapper"
            try:
                panel = self.query_one(f"#{panel_id}")
            except Exception:
                return
            self._set_widget_class(panel_id, "maximized_workbench", enabled)
            self._set_widget_class(workbench_id, "maximized_workbench", enabled)
            for child in tuple(getattr(panel, "children", ()) or ()):
                child_id = collapse_ws(str(getattr(child, "id", "") or ""))
                try:
                    child.display = (child_id == workbench_id) if enabled else True
                except Exception:
                    continue
            if enabled:
                selected_wrapper_id = collapse_ws(str(wrapper_id or ""))
                self._set_widget_display(workbench_id, True)
                self._set_widget_display(tree_wrapper_id, selected_wrapper_id == tree_wrapper_id)
                self._set_widget_display(detail_wrapper_id, selected_wrapper_id == detail_wrapper_id)
                return
            self._set_widget_display(workbench_id, True)
            self._set_widget_display(tree_wrapper_id, True)
            self._set_widget_display(detail_wrapper_id, True)

        def _apply_tab_pane_maximize_state(self) -> None:  # pragma: no cover - requires textual runtime
            active_tab_id = self._active_tab_id()
            self._set_widget_class("subject_itemize_workbench", "maximized_workbench", False)
            self._set_widget_class("draft_scope_workbench", "maximized_workbench", False)
            self._set_widget_class("review_scope_workbench", "maximized_workbench", False)
            self._set_widget_class("publication_scope_workbench", "maximized_workbench", False)
            self._set_scope_actions_panel_workbench_only("review", False)
            self._set_scope_actions_panel_workbench_only("publication", False)
            for widget_id in _TEXTUAL_TAB_SECTION_IDS.get(active_tab_id, ()):
                self._set_widget_display(widget_id, True)
            for widget_id in _TEXTUAL_HIDDEN_UTILITY_SECTION_IDS:
                self._set_widget_display(widget_id, False)
            if active_tab_id == "itemize_tab":
                self._set_widget_display("itemize_inventory_wrapper", True)
                self._set_widget_display("itemize_detail_wrapper", True)
            if active_tab_id == "draft_tab":
                self._set_widget_display("draft_scope_tree_wrapper", True)
                self._set_widget_display("draft_model_main_wrapper", self._draft_model_mode_active())
                self._set_widget_display("draft_scope_detail_wrapper", True)
                self._set_widget_display("draft_result_panel", self._draft_model_mode_active())
            if active_tab_id == "review_tab":
                self._set_widget_display("review_scope_tree_wrapper", True)
                self._set_widget_display("review_scope_detail_wrapper", True)
            if active_tab_id == "publication_tab":
                self._set_widget_display("publication_scope_tree_wrapper", True)
                self._set_widget_display("publication_scope_detail_wrapper", True)
            maximized = self._maximized_pane_spec()
            if maximized is None:
                try:
                    self.refresh(layout=True)
                except Exception:
                    pass
                try:
                    self.query_one(f"#{active_tab_id}").refresh(layout=True)
                except Exception:
                    pass
                self._refresh_pane_toggle_buttons()
                self._refresh_info_pane()
                self._refresh_pane_info_buttons()
                self._refresh_subject_journal_buttons()
                if active_tab_id == "review_tab":
                    self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())
                if active_tab_id == "publication_tab":
                    self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())
                if active_tab_id == "chat_tab":
                    self._refresh_prompt_suggestions()
                return
            outer_id = collapse_ws(maximized.get("outer_id", ""))
            pane_id = collapse_ws(maximized.get("pane_id", ""))
            wrapper_id = collapse_ws(maximized.get("wrapper_id", "")) or outer_id
            for widget_id in _TEXTUAL_TAB_SECTION_IDS.get(active_tab_id, ()):
                self._set_widget_display(widget_id, widget_id == outer_id)
            if outer_id == "subject_itemize_workbench":
                self._set_widget_class("subject_itemize_workbench", "maximized_workbench", True)
                self._set_widget_display("itemize_inventory_wrapper", wrapper_id == "itemize_inventory_wrapper")
                self._set_widget_display("itemize_detail_wrapper", wrapper_id == "itemize_detail_wrapper")
            if outer_id == "draft_scope_workbench":
                self._set_widget_class("draft_scope_workbench", "maximized_workbench", True)
                self._set_widget_display("draft_scope_tree_wrapper", wrapper_id == "draft_scope_tree_wrapper")
                self._set_widget_display("draft_model_main_wrapper", wrapper_id == "draft_model_main_wrapper")
                self._set_widget_display("draft_scope_detail_wrapper", wrapper_id == "draft_scope_detail_wrapper")
            if outer_id == "review_scope_workbench":
                self._set_widget_class("review_scope_workbench", "maximized_workbench", True)
                self._set_widget_display("review_scope_tree_wrapper", wrapper_id == "review_scope_tree_wrapper")
                self._set_widget_display("review_scope_detail_wrapper", wrapper_id == "review_scope_detail_wrapper")
            if outer_id == "review_actions_panel":
                self._set_scope_actions_panel_workbench_only("review", True, wrapper_id=wrapper_id)
            if outer_id == "publication_scope_workbench":
                self._set_widget_class("publication_scope_workbench", "maximized_workbench", True)
                self._set_widget_display("publication_scope_tree_wrapper", wrapper_id == "publication_scope_tree_wrapper")
                self._set_widget_display("publication_scope_detail_wrapper", wrapper_id == "publication_scope_detail_wrapper")
            if outer_id == "publication_actions_panel":
                self._set_scope_actions_panel_workbench_only("publication", True, wrapper_id=wrapper_id)
            try:
                self.refresh(layout=True)
            except Exception:
                pass
            for widget_id in filter(None, (active_tab_id, outer_id, wrapper_id, pane_id)):
                try:
                    self.query_one(f"#{widget_id}").refresh(layout=True)
                except Exception:
                    continue
            try:
                tab_body = self.query_one(f"#{active_tab_id}", Vertical)
                for child in getattr(tab_body, "children", ()):
                    try:
                        child.refresh(layout=True)
                    except Exception:
                        continue
            except Exception:
                pass
            self._refresh_pane_toggle_buttons()
            self._refresh_info_pane()
            self._refresh_pane_info_buttons()
            self._refresh_subject_journal_buttons()
            self._refresh_subject_hidden_pane_buttons()
            if active_tab_id in {"review_tab", "publication_tab"}:
                self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())

        def action_toggle_maximized_pane(self) -> None:  # pragma: no cover - requires textual runtime
            focused_pane_id = self._focused_maximizable_pane_id()
            if focused_pane_id is None:
                return
            self._toggle_maximized_pane_by_id(focused_pane_id)

        def _tab_title(self, tab_id: str) -> str:
            return _TEXTUAL_TAB_TITLE_OVERRIDES.get(
                tab_id,
                workstation_tab_title(_textual_tab_layout_key(tab_id)),
            )

        def _subject_phase_for_tab_id(self, tab_id: str | None = None) -> str:
            active_tab_id = str(tab_id or self._active_tab_id() or "")
            return _SUBJECT_TAB_ID_TO_PHASE.get(active_tab_id, "research")

        def _set_subject_phase(self, phase: str) -> None:
            target_tab_id = _SUBJECT_PHASE_TO_TAB_ID.get(str(phase or "").casefold())
            if not target_tab_id:
                return
            self._dismiss_detached_pane()
            self._maximized_pane_id = None
            self._active_tab_id_value = target_tab_id
            self._apply_active_tab_state()
            self._refresh_current_subject_phase_projection()
            self._focus_first_panel_for_active_tab()

        def _set_active_tab(self, tab_id: str) -> None:
            target_tab_id = str(tab_id or "")
            if target_tab_id not in self._tab_ids():
                return
            self._dismiss_detached_pane()
            self._maximized_pane_id = None
            self._active_tab_id_value = target_tab_id
            self._apply_active_tab_state()
            if target_tab_id in _SUBJECT_TAB_ID_TO_PHASE:
                self._refresh_current_subject_phase_projection()
            else:
                self.request_state_refresh()
            self._focus_first_panel_for_active_tab()

        def _focus_subject_primary_gate_action_for_phase(self, phase: str) -> bool:
            try:
                button = self.query_one(
                    f"#{_subject_gate_action_button_ids(phase, 'review')[0]}",
                    TextualButton,
                )
            except Exception:
                return False
            if bool(getattr(button, "disabled", False)) or not bool(getattr(button, "display", True)):
                return False
            try:
                button.focus()
            except Exception:
                return False
            return True

        def _schedule_focus_subject_primary_gate_action_for_phase(self, phase: str) -> None:
            callback = getattr(self, "call_after_refresh", None) or getattr(self, "call_later", None)
            if callable(callback):
                try:
                    callback(self._focus_subject_primary_gate_action_for_phase, phase)
                    return
                except Exception:
                    pass
            try:
                self._focus_subject_primary_gate_action_for_phase(phase)
            except Exception:
                pass

        def _guided_subject_phase_from_action_result(self, current_phase: str, result: Any) -> str:
            normalized_current_phase = collapse_ws(str(current_phase or "")).casefold() or "research"
            explicit_phase = collapse_ws(str(getattr(result, "next_phase", "") or "")).casefold()
            if explicit_phase in MOCK_SUBJECT_PHASES:
                return explicit_phase
            phase_view = getattr(result, "phase_view", None)
            preferred_phase = collapse_ws(str(getattr(phase_view, "preferred_phase", "") or "")).casefold()
            if preferred_phase in MOCK_SUBJECT_PHASES:
                return preferred_phase
            rendered_phase = collapse_ws(str(getattr(phase_view, "phase", "") or "")).casefold()
            if rendered_phase in MOCK_SUBJECT_PHASES:
                return rendered_phase
            return normalized_current_phase

        def _mock_subject_scenario(self) -> MockSubjectScenario:
            if not self._mock_subject_scenarios:
                raise RuntimeError("No mock subject scenarios are configured.")
            index = max(0, min(self._mock_subject_index, len(self._mock_subject_scenarios) - 1))
            return self._mock_subject_scenarios[index]

        def _reload_mock_subject_scenarios(
            self,
            *,
            preferred_key: str = "",
            refresh_progress_for_keys: tuple[str, ...] = (),
        ) -> None:
            current_key = ""
            if self._mock_subject_scenarios:
                try:
                    current_key = self._mock_subject_scenario().key
                except Exception:
                    current_key = ""
            scenarios = _list_mock_subject_scenarios_via_api(
                self._root,
                client=self._subject_workflow_client,
                projection_backend=self._subject_projection_backend,
            )
            refresh_key_set = {collapse_ws(item) for item in refresh_progress_for_keys if collapse_ws(item)}
            existing_progress = {
                key: value
                for key, value in self._mock_subject_progress_by_key.items()
                if collapse_ws(key) not in refresh_key_set
            }
            progress_by_key = self._subject_projection_backend.load_progress_map(
                root_path=self._root,
                scenarios=scenarios,
                existing=existing_progress,
            )
            self._mock_subject_scenarios = scenarios
            self._mock_subject_progress_by_key = progress_by_key
            available_keys = [scenario.key for scenario in scenarios]
            target_key = preferred_key or current_key
            if available_keys and target_key in available_keys:
                self._mock_subject_index = available_keys.index(target_key)
            else:
                self._mock_subject_index = 0
            try:
                self.request_state_refresh()
            except Exception:
                pass

        def _mock_subject_progress(self) -> MockSubjectProgress:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress_by_key.get(scenario.key)
            if progress is None:
                progress = (
                    self._subject_projection_backend.load_progress(
                        root_path=self._root,
                        subject_id=scenario.subject_id,
                    )
                    if not scenario.is_placeholder and collapse_ws(scenario.subject_id)
                    else new_mock_subject_progress()
                )
                self._mock_subject_progress_by_key[scenario.key] = progress
            return progress

        def _replace_mock_subject_scenario(self, scenario_view: Any) -> None:
            replacement = _mock_subject_scenario_from_api_view(scenario_view)
            replacement_key = collapse_ws(getattr(replacement, "key", ""))
            replacement_subject_id = collapse_ws(getattr(replacement, "subject_id", ""))
            updated: list[MockSubjectScenario] = []
            replaced = False
            for existing in self._mock_subject_scenarios:
                existing_key = collapse_ws(getattr(existing, "key", ""))
                existing_subject_id = collapse_ws(getattr(existing, "subject_id", ""))
                if (
                    replacement_key
                    and existing_key == replacement_key
                ) or (
                    replacement_subject_id
                    and existing_subject_id == replacement_subject_id
                ):
                    updated.append(replacement)
                    replaced = True
                else:
                    updated.append(existing)
            if replaced:
                self._mock_subject_scenarios = tuple(updated)

        def _mark_subject_progress_dirty(self, scenario: MockSubjectScenario | None = None) -> None:
            selected_scenario = scenario or self._mock_subject_scenario()
            key = collapse_ws(getattr(selected_scenario, "key", ""))
            subject_id = collapse_ws(getattr(selected_scenario, "subject_id", ""))
            if key:
                self._dirty_subject_progress_keys.add(key)
            if subject_id:
                self._dirty_subject_progress_keys.add(subject_id)

        def _clear_subject_progress_dirty(self, scenario: MockSubjectScenario | None = None) -> None:
            selected_scenario = scenario or self._mock_subject_scenario()
            key = collapse_ws(getattr(selected_scenario, "key", ""))
            subject_id = collapse_ws(getattr(selected_scenario, "subject_id", ""))
            if key:
                self._dirty_subject_progress_keys.discard(key)
            if subject_id:
                self._dirty_subject_progress_keys.discard(subject_id)

        def _persist_subject_progress_if_dirty(self, scenario: MockSubjectScenario | None = None) -> None:
            selected_scenario = scenario or self._mock_subject_scenario()
            if bool(getattr(selected_scenario, "is_placeholder", False)):
                return
            key = collapse_ws(getattr(selected_scenario, "key", ""))
            subject_id = collapse_ws(getattr(selected_scenario, "subject_id", ""))
            if not subject_id:
                return
            if key not in self._dirty_subject_progress_keys and subject_id not in self._dirty_subject_progress_keys:
                return
            self._subject_projection_backend.persist_progress(
                root_path=self._root,
                subject_id=subject_id,
                progress=self._mock_subject_progress(),
            )
            self._clear_subject_progress_dirty(selected_scenario)

        def _subject_phase_projection_kwargs(self, *, assistant_message_text: str | None = None) -> dict[str, Any]:
            effective_assistant_text = (
                self._latest_assistant_research_capture_text()
                if assistant_message_text is None
                else str(assistant_message_text or "")
            )
            return {
                "can_capture_assistant": bool(collapse_ws(effective_assistant_text)),
                "markdown_selected_path": str(self._markdown_selected_path or ""),
                "markdown_status_text": self._markdown_status_text,
                "markdown_busy": self._markdown_busy,
            }

        def _research_projection_input_key(self) -> tuple[bool, str, str, bool]:
            projection_kwargs = self._subject_phase_projection_kwargs()
            return (
                bool(projection_kwargs.get("can_capture_assistant", False)),
                str(projection_kwargs.get("markdown_selected_path", "") or ""),
                str(projection_kwargs.get("markdown_status_text", "") or ""),
                bool(projection_kwargs.get("markdown_busy", False)),
            )

        def _invalidate_research_snapshot_if_projection_inputs_changed(self) -> None:
            next_key = self._research_projection_input_key()
            if self._research_projection_input_cache_key == next_key:
                return
            self._research_projection_input_cache_key = next_key
            self._subject_snapshot_cache.pop("research", None)

        def _stop_subject_workflow_watch(self) -> None:
            stop_event = self._subject_workflow_watch_stop_event
            thread = self._subject_workflow_watch_thread
            self._subject_workflow_watch_stop_event = None
            self._subject_workflow_watch_thread = None
            self._subject_workflow_watch_key = None
            self._subject_workflow_watch_last_sequence = -1
            if stop_event is not None:
                try:
                    stop_event.set()
                except Exception:
                    pass
            if thread is not None and thread.is_alive():
                thread.join(timeout=5.0)

        def _refresh_subject_workflow_projection_from_snapshot(self) -> None:
            self._refresh_mock_subject_controls()
            self._schedule_active_tab_refresh()
            self._apply_tab_pane_maximize_state()
            self._refresh_info_pane()
            self._refresh_pane_info_buttons()

        def _refresh_current_subject_phase_projection(self) -> None:
            active_phase = _SUBJECT_TAB_ID_TO_PHASE.get(self._active_tab_id())
            if active_phase in MOCK_SUBJECT_PHASES:
                self._subject_snapshot_cache.pop(active_phase, None)
            self._refresh_subject_workflow_projection_from_snapshot()

        def _subject_workflow_watch_identity(self) -> tuple[str, str, bool, str, str, bool] | None:
            active_tab_id = self._active_tab_id()
            phase = _SUBJECT_TAB_ID_TO_PHASE.get(active_tab_id)
            if not phase:
                return None
            try:
                scenario = self._mock_subject_scenario()
            except Exception:
                return None
            subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
            if not subject_id or bool(getattr(scenario, "is_placeholder", False)):
                return None
            projection_kwargs = self._subject_phase_projection_kwargs()
            return (
                subject_id,
                phase,
                bool(projection_kwargs.get("can_capture_assistant", False)),
                str(projection_kwargs.get("markdown_selected_path", "") or ""),
                str(projection_kwargs.get("markdown_status_text", "") or ""),
                bool(projection_kwargs.get("markdown_busy", False)),
            )

        def _subject_workflow_watch_worker(
            self,
            watch_key: tuple[str, str, bool, str, str, bool],
            stop_event: threading.Event,
        ) -> None:
            subject_id, phase, can_capture_assistant, markdown_selected_path, markdown_status_text, markdown_busy = watch_key
            try:
                for event in self._subject_projection_backend.watch_subject_workflow(
                    root_path=self._root,
                    subject_id=subject_id,
                    phase=phase,
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                    stop_when=stop_event.is_set,
                ):
                    if stop_event.is_set():
                        break
                    try:
                        self.call_from_thread(
                            self._apply_subject_workflow_watch_event,
                            watch_key,
                            event,
                        )
                    except Exception:
                        break
            finally:
                if self._subject_workflow_watch_key == watch_key:
                    self._subject_workflow_watch_thread = None
                    self._subject_workflow_watch_stop_event = None

        def _apply_subject_workflow_watch_event(
            self,
            watch_key: tuple[str, str, bool, str, str, bool],
            event: Any,
        ) -> None:
            if self._subject_workflow_watch_key != watch_key:
                return
            snapshot = getattr(event, "snapshot", None)
            if snapshot is None:
                return
            event_sequence = int(getattr(event, "sequence", -1) or -1)
            last_sequence = int(getattr(self, "_subject_workflow_watch_last_sequence", -1) or -1)
            if event_sequence >= 0 and event_sequence <= last_sequence:
                return
            if event_sequence >= 0:
                self._subject_workflow_watch_last_sequence = event_sequence
            phase = collapse_ws(str(getattr(getattr(snapshot, "phase_view", None), "phase", "") or watch_key[1]))
            event_kind = collapse_ws(str(getattr(event, "event_kind", "") or ""))
            event_progress_fingerprint = collapse_ws(str(getattr(event, "progress_fingerprint", "") or ""))
            pending_local_fingerprint = collapse_ws(self._subject_local_interaction_fingerprints.get(phase, ""))
            if event_kind == "subject_workflow_client_view_changed" and pending_local_fingerprint:
                if not event_progress_fingerprint or event_progress_fingerprint != pending_local_fingerprint:
                    return
                self._subject_local_interaction_fingerprints.pop(phase, None)
                try:
                    scenario = self._mock_subject_scenario()
                    subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or watch_key[0]
                    if (
                        phase
                        and subject_id
                        and not bool(getattr(scenario, "is_placeholder", False))
                    ):
                        local_progress = self._mock_subject_progress()
                        local_progress_fingerprint = self._subject_projection_backend.progress_fingerprint(local_progress)
                        if local_progress_fingerprint and local_progress_fingerprint == event_progress_fingerprint:
                            self._clear_subject_progress_dirty(scenario)
                except Exception:
                    pass
                return
            effective_snapshot = snapshot
            try:
                scenario = self._mock_subject_scenario()
                subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or watch_key[0]
                if subject_id and not bool(getattr(scenario, "is_placeholder", False)):
                    key = collapse_ws(getattr(scenario, "key", ""))
                    dirty = key in self._dirty_subject_progress_keys or subject_id in self._dirty_subject_progress_keys
                    if dirty:
                        local_progress = self._mock_subject_progress()
                        local_progress_fingerprint = self._subject_projection_backend.progress_fingerprint(local_progress)
                        effective_snapshot = self._subject_projection_backend.get_snapshot(
                            root_path=self._root,
                            subject_id=subject_id,
                            phase=phase or watch_key[1],
                            progress=local_progress,
                            **self._subject_phase_projection_kwargs(),
                        )
                        if event_progress_fingerprint and event_progress_fingerprint == local_progress_fingerprint:
                            self._clear_subject_progress_dirty(scenario)
                    else:
                        self._mock_subject_progress_by_key[scenario.key] = self._subject_projection_backend.load_progress(
                            root_path=self._root,
                            subject_id=subject_id,
                        )
            except Exception:
                pass
            if phase:
                self._subject_snapshot_cache[phase] = effective_snapshot
            scenario_view = getattr(getattr(effective_snapshot, "phase_view", None), "scenario", None)
            if scenario_view is not None:
                self._replace_mock_subject_scenario(scenario_view)
            self._refresh_subject_workflow_projection_from_snapshot()

        def _stop_shell_watch(self) -> None:
            stop_event = self._shell_watch_stop_event
            thread = self._shell_watch_thread
            self._shell_watch_stop_event = None
            self._shell_watch_thread = None
            self._shell_watch_last_sequence = -1
            if stop_event is not None:
                stop_event.set()
            if thread is not None and thread.is_alive():
                thread.join(timeout=5.0)

        def _shell_channel_version_rank(self, channel_key: str, snapshot_version: str) -> tuple[int, int]:
            normalized_channel = collapse_ws(str(channel_key or "")).casefold()
            normalized_version = str(snapshot_version or "")
            fingerprint = normalized_version.partition("::")[2]
            if not fingerprint:
                return (0, 0)
            stat_key_by_channel = {
                "shell/transcript": "messages",
                "shell/activity": "activity",
                "shell/permissions": "session",
                "shell/skills": "skills",
            }
            target_key = stat_key_by_channel.get(normalized_channel, "")
            if not target_key:
                return (0, 0)
            for segment in fingerprint.split("|"):
                key, _, value = segment.partition("=")
                if collapse_ws(key).casefold() != target_key:
                    continue
                major_text, _, minor_text = str(value or "").partition(":")
                try:
                    return (int(major_text or 0), int(minor_text or 0))
                except Exception:
                    return (0, 0)
            return (0, 0)

        def _shell_watch_event_is_stale(self, channel_key: str, snapshot_version: str) -> bool:
            current_version = self._state.shell_snapshot_version(channel_key)
            if not collapse_ws(current_version):
                return False
            if collapse_ws(current_version) == collapse_ws(snapshot_version):
                return True
            current_rank = self._shell_channel_version_rank(channel_key, current_version)
            incoming_rank = self._shell_channel_version_rank(channel_key, snapshot_version)
            return incoming_rank < current_rank

        def _shell_watch_worker(self, stop_event: threading.Event) -> None:
            try:
                for event in self._shell_client.watch_workstation_shell(
                    root_path=self._root,
                    last_seen_version=self._state.shell_snapshot_version("shell/transcript"),
                    stop_when=stop_event.is_set,
                ):
                    if stop_event.is_set():
                        break
                    event_sequence = int(getattr(event, "sequence", -1) or -1)
                    if event_sequence >= 0 and event_sequence <= self._shell_watch_last_sequence:
                        continue
                    if event_sequence >= 0:
                        self._shell_watch_last_sequence = event_sequence
                    self.call_from_thread(self._apply_shell_watch_event, event)
            except Exception:
                return

        def _apply_shell_watch_event(self, event: Any) -> None:
            channel_key = collapse_ws(str(getattr(event, "channel_key", "") or ""))
            snapshot_version = str(getattr(event, "snapshot_version", "") or "")
            if channel_key and snapshot_version and self._shell_watch_event_is_stale(channel_key, snapshot_version):
                return
            chat_snapshot = getattr(event, "chat_snapshot", None)
            activity_view = getattr(event, "activity_view", None)
            permissions_view = getattr(event, "permissions_view", None)
            skills_view = getattr(event, "skills_view", None)
            if chat_snapshot is not None:
                self._state.apply_shell_snapshot(chat_snapshot)
            if activity_view is not None:
                self._state.set_shell_activity_text(
                    str(getattr(activity_view, "text", "") or ""),
                    snapshot_version=str(getattr(activity_view, "snapshot_version", "") or ""),
                )
            if permissions_view is not None:
                self._state.set_shell_permissions_text(
                    str(getattr(permissions_view, "text", "") or ""),
                    snapshot_version=str(getattr(permissions_view, "snapshot_version", "") or ""),
                )
            if skills_view is not None:
                self._state.set_shell_skills_text(
                    str(getattr(skills_view, "text", "") or ""),
                    snapshot_version=str(getattr(skills_view, "snapshot_version", "") or ""),
                )
            self.request_state_refresh()

        def _start_shell_watch(self) -> None:
            self._stop_shell_watch()
            stop_event = threading.Event()
            self._shell_watch_stop_event = stop_event
            self._shell_watch_thread = threading.Thread(
                target=self._shell_watch_worker,
                args=(stop_event,),
                daemon=True,
                name="shell-watch",
            )
            self._shell_watch_thread.start()

        def _start_app_worker(
            self,
            *,
            target: Any,
            args: tuple[Any, ...] = (),
            kwargs: dict[str, Any] | None = None,
            name: str | None = None,
        ) -> threading.Thread:
            worker_kwargs = dict(kwargs or {})

            def _runner() -> None:
                try:
                    target(*args, **worker_kwargs)
                finally:
                    with self._app_worker_threads_lock:
                        self._app_worker_threads.discard(thread)

            thread = threading.Thread(
                target=_runner,
                daemon=True,
                name=name,
            )
            with self._app_worker_threads_lock:
                self._app_worker_threads.add(thread)
            thread.start()
            return thread

        def _stop_app_workers(self) -> None:
            with self._app_worker_threads_lock:
                threads = tuple(self._app_worker_threads)
                self._app_worker_threads.clear()
            for thread in threads:
                if thread.is_alive():
                    thread.join(timeout=5.0)

        def _ensure_subject_workflow_watch(self) -> None:
            watch_key = self._subject_workflow_watch_identity()
            if watch_key is None:
                self._stop_subject_workflow_watch()
                return
            active_thread = self._subject_workflow_watch_thread
            if self._subject_workflow_watch_key == watch_key and active_thread is not None and active_thread.is_alive():
                return
            previous_watch_key = self._subject_workflow_watch_key
            previous_phase = collapse_ws(str(previous_watch_key[1] if previous_watch_key else ""))
            next_phase = collapse_ws(str(watch_key[1]))
            if previous_phase:
                self._subject_snapshot_cache.pop(previous_phase, None)
            if next_phase:
                self._subject_snapshot_cache.pop(next_phase, None)
            self._stop_subject_workflow_watch()
            stop_event = threading.Event()
            worker = threading.Thread(
                target=self._subject_workflow_watch_worker,
                args=(watch_key, stop_event),
                daemon=True,
                name=f"subject-watch-{watch_key[1]}",
            )
            self._subject_workflow_watch_key = watch_key
            self._subject_workflow_watch_stop_event = stop_event
            self._subject_workflow_watch_thread = worker
            self._subject_workflow_watch_last_sequence = -1
            worker.start()

        def _mock_subject_snapshot(self, phase: str):
            normalized_phase = collapse_ws(str(phase or "")).casefold() or "research"
            cached = self._subject_snapshot_cache.get(normalized_phase)
            if cached is not None:
                return cached
            scenario = self._mock_subject_scenario()
            subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
            snapshot = self._subject_projection_backend.get_snapshot(
                root_path=self._root,
                subject_id=subject_id,
                phase=normalized_phase,
                progress=self._mock_subject_progress(),
                **self._subject_phase_projection_kwargs(),
            )
            self._subject_snapshot_cache[normalized_phase] = snapshot
            return snapshot

        def _mock_subject_control_bundle(self, phase: str):
            return getattr(self._mock_subject_snapshot(phase), "control_bundle", None)

        def _mock_subject_pane_bundle(self, phase: str):
            return getattr(self._mock_subject_snapshot(phase), "pane_bundle", None)

        def _mock_subject_pane_view_from_bundle(self, phase: str, key: str):
            bundle = self._mock_subject_pane_bundle(phase)
            normalized_key = collapse_ws(key)
            for pane in getattr(bundle, "panes", ()) or ():
                if collapse_ws(getattr(pane, "key", "")) == normalized_key:
                    return pane
            raise KeyError(f"Missing subject pane view: {phase}/{key}")

        def _mock_subject_pane_text(self, phase: str, key: str) -> str:
            pane = self._mock_subject_pane_view_from_bundle(phase, key)
            return "\n".join(str(line or "") for line in getattr(pane, "lines", ()) or ())

        def _mock_subject_pane_title(self, phase: str, key: str) -> str:
            pane = self._mock_subject_pane_view_from_bundle(phase, key)
            return str(getattr(pane, "title", "") or "")

        def _mock_subject_pane_rows(self, phase: str, key: str) -> tuple[tuple[str, str], ...]:
            pane = self._mock_subject_pane_view_from_bundle(phase, key)
            return tuple(
                (
                    str(getattr(row, "label", "") or ""),
                    str(getattr(row, "value", "") or ""),
                )
                for row in (getattr(pane, "rows", ()) or ())
            )

        def _mock_subject_pane_items(self, phase: str, key: str) -> tuple[Any, ...]:
            pane = self._mock_subject_pane_view_from_bundle(phase, key)
            return tuple(getattr(pane, "items", ()) or ())

        def _mock_subject_pane_is_structured_table(self, phase: str, key: str) -> bool:
            pane = self._mock_subject_pane_view_from_bundle(phase, key)
            return bool(getattr(pane, "is_structured_table", False))

        def _mock_subject_select_spec_from_bundle(self, phase: str, key: str):
            bundle = self._mock_subject_control_bundle(phase)
            normalized_key = collapse_ws(key)
            for spec in getattr(bundle, "selects", ()) or ():
                if collapse_ws(getattr(spec, "key", "")) == normalized_key:
                    return spec
            raise KeyError(f"Missing subject select spec: {phase}/{key}")

        def _mock_subject_switch_spec_from_bundle(self, phase: str, key: str):
            bundle = self._mock_subject_control_bundle(phase)
            normalized_key = collapse_ws(key)
            for spec in getattr(bundle, "switches", ()) or ():
                if collapse_ws(getattr(spec, "key", "")) == normalized_key:
                    return spec
            raise KeyError(f"Missing subject switch spec: {phase}/{key}")

        def _mock_subject_table_spec_from_bundle(self, phase: str, key: str):
            bundle = self._mock_subject_control_bundle(phase)
            normalized_key = collapse_ws(key)
            for spec in getattr(bundle, "tables", ()) or ():
                if collapse_ws(getattr(spec, "key", "")) == normalized_key:
                    return spec
            raise KeyError(f"Missing subject table spec: {phase}/{key}")

        def _mock_subject_action_spec_from_bundle(self, phase: str, key: str) -> MockSubjectActionSpec:
            bundle = self._mock_subject_control_bundle(phase)
            normalized_key = collapse_ws(key)
            for spec in getattr(bundle, "more_actions", ()) or ():
                if collapse_ws(getattr(spec, "key", "")) == normalized_key:
                    return MockSubjectActionSpec(
                        key=collapse_ws(getattr(spec, "key", "")),
                        label=str(getattr(spec, "label", "") or ""),
                        enabled=bool(getattr(spec, "enabled", False)),
                    )
            raise KeyError(f"Missing subject action spec: {phase}/{key}")

        def _mock_subject_select_spec_from_api_view(self, spec: Any) -> MockSubjectSelectSpec:
            return MockSubjectSelectSpec(
                label=str(getattr(spec, "label", "") or ""),
                value=str(getattr(spec, "value", "") or ""),
                options=tuple(
                    (
                        str(getattr(option, "label", "") or ""),
                        str(getattr(option, "value", "") or ""),
                    )
                    for option in getattr(spec, "options", ()) or ()
                ),
                enabled=bool(getattr(spec, "enabled", False)),
            )

        def _mock_subject_switch_spec_from_api_view(self, spec: Any) -> MockSubjectSwitchSpec:
            return MockSubjectSwitchSpec(
                label=str(getattr(spec, "label", "") or ""),
                value=bool(getattr(spec, "value", False)),
                enabled=bool(getattr(spec, "enabled", False)),
            )

        def _mock_subject_selection_list_spec_from_api_view(self, spec: Any) -> MockSubjectSelectionListSpec:
            return MockSubjectSelectionListSpec(
                label=str(getattr(spec, "label", "") or ""),
                action_key_prefix=str(getattr(spec, "action_key_prefix", "") or ""),
                options=tuple(
                    (
                        str(getattr(option, "label", "") or ""),
                        str(getattr(option, "value", "") or ""),
                        bool(getattr(option, "selected", False)),
                    )
                    for option in getattr(spec, "options", ()) or ()
                ),
                enabled=bool(getattr(spec, "enabled", False)),
            )

        def _mock_subject_table_spec_from_api_view(self, spec: Any) -> MockSubjectTableSpec:
            return MockSubjectTableSpec(
                label=str(getattr(spec, "label", "") or ""),
                columns=tuple(str(column or "") for column in getattr(spec, "columns", ()) or ()),
                rows=tuple(
                    tuple(str(cell or "") for cell in row)
                    for row in getattr(spec, "rows", ()) or ()
                ),
                enabled=bool(getattr(spec, "enabled", False)),
            )

        def _mock_subject_phase_view(self, phase: str):
            scenario = self._mock_subject_scenario()
            if not self._subject_projection_backend.uses_in_process_service():
                self._persist_subject_progress_if_dirty(scenario)
            return getattr(self._mock_subject_snapshot(phase), "phase_view", None)

        def _render_subject_status_view_text(self, phase_view: Any) -> str:
            rows = tuple(getattr(getattr(phase_view, "status_view", None), "rows", ()) or ())
            return "\n".join(
                f"{collapse_ws(getattr(row, 'label', ''))}: {getattr(row, 'value', '')}"
                for row in rows
                if collapse_ws(getattr(row, "label", "")) or collapse_ws(getattr(row, "value", ""))
            )

        def _render_subject_current_step_view_text(self, phase_view: Any) -> str:
            step = getattr(phase_view, "current_step", None)
            if step is None:
                return ""
            lines = [
                f"Do this now: {getattr(step, 'title', '')}",
                f"Status: {getattr(step, 'status', '')}",
                f"Why: {getattr(step, 'why', '')}",
            ]
            lines.extend(tuple(str(item or "") for item in getattr(step, "detail_lines", ()) or ()))
            return "\n".join(line for line in lines if collapse_ws(line))

        def _render_subject_journey_view_text(self, phase_view: Any) -> str:
            return "\n".join(str(line or "") for line in getattr(phase_view, "journey_lines", ()) or ())

        def _subject_gate_actions_from_phase_view(self, phase_view: Any) -> tuple[MockSubjectGateAction, ...]:
            step = getattr(phase_view, "current_step", None)
            if step is None:
                return ()
            return tuple(
                MockSubjectGateAction(
                    kind=collapse_ws(getattr(action, "action_kind", "")),
                    key=collapse_ws(getattr(action, "key", "")),
                    label=str(getattr(action, "label", "") or ""),
                    enabled=bool(getattr(action, "enabled", False)),
                )
                for action in getattr(step, "actions", ()) or ()
            )

        def _render_subject_workspace_view_text(self, phase_view: Any) -> str:
            workspace_view = getattr(phase_view, "workspace_view", None)
            return "\n".join(str(line or "") for line in getattr(workspace_view, "lines", ()) or ())

        def _refresh_subject_progress_after_api_action(self, scenario: MockSubjectScenario, result: Any) -> MockSubjectProgress:
            preferred_key = collapse_ws(str(getattr(result, "preferred_subject_key", "") or ""))
            target_subject_id = collapse_ws(
                str(
                    getattr(
                        getattr(getattr(result, "phase_view", None), "scenario", None),
                        "subject_id",
                        "",
                    )
                    or getattr(scenario, "subject_id", "")
                )
            )
            current_key = collapse_ws(getattr(scenario, "key", ""))
            current_subject_id = collapse_ws(getattr(scenario, "subject_id", ""))
            should_reload_subjects = bool(getattr(result, "reload_subjects", False))
            if preferred_key and preferred_key != current_key:
                should_reload_subjects = True
            if target_subject_id and current_subject_id and target_subject_id != current_subject_id:
                should_reload_subjects = True
            result_scenario_view = getattr(getattr(result, "phase_view", None), "scenario", None)
            same_subject_reload = (
                should_reload_subjects
                and not preferred_key
                and current_subject_id
                and target_subject_id == current_subject_id
                and result_scenario_view is not None
            )
            if same_subject_reload:
                self._replace_mock_subject_scenario(result_scenario_view)
                should_reload_subjects = False
            if should_reload_subjects:
                self._reload_mock_subject_scenarios(
                    preferred_key=preferred_key or target_subject_id or current_key,
                    refresh_progress_for_keys=tuple(
                        item
                        for item in (
                            preferred_key,
                            target_subject_id,
                            current_key,
                            current_subject_id,
                        )
                        if collapse_ws(item)
                    ),
                )
                return self._mock_subject_progress()
            if self._subject_projection_backend.uses_in_process_service():
                refreshed_progress = self._mock_subject_progress_by_key.get(current_key)
                if refreshed_progress is None:
                    refreshed_progress = self._mock_subject_progress()
            elif not getattr(scenario, "is_placeholder", False) and current_subject_id:
                refreshed_progress = self._subject_projection_backend.load_progress(
                    root_path=self._root,
                    subject_id=current_subject_id,
                )
            else:
                refreshed_progress = new_mock_subject_progress()
            self._mock_subject_progress_by_key[current_key] = refreshed_progress
            self._clear_subject_progress_dirty(scenario)
            return refreshed_progress

        def _invoke_subject_workflow_action(
            self,
            *,
            scenario: MockSubjectScenario,
            phase: str,
            action_key: str,
            assistant_message_text: str = "",
            subject_title_override: str = "",
        ) -> Any:
            subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
            if not self._subject_projection_backend.uses_in_process_service():
                self._persist_subject_progress_if_dirty(scenario)
            return self._subject_projection_backend.apply_action(
                root_path=self._root,
                subject_id=subject_id,
                phase=phase,
                action_key=action_key,
                progress=self._mock_subject_progress(),
                assistant_message_text=assistant_message_text,
                subject_title_override=subject_title_override,
                **self._subject_phase_projection_kwargs(
                    assistant_message_text=assistant_message_text,
                ),
            )

        def _mock_subject_control_specs(
            self,
            phase: str,
        ) -> tuple[MockSubjectActionSpec, MockSubjectActionSpec, MockSubjectActionSpec, MockSubjectActionSpec]:
            specs = list(
                MockSubjectActionSpec(
                    key=collapse_ws(getattr(spec, "key", "")),
                    label=str(getattr(spec, "label", "") or ""),
                    enabled=bool(getattr(spec, "enabled", False)),
                )
                for spec in getattr(self._mock_subject_control_bundle(phase), "more_actions", ()) or ()
            )
            while len(specs) < 4:
                specs.append(MockSubjectActionSpec(key="", label="", enabled=False))
            return tuple(specs[:4])

        def _mock_subject_itemize_decision_role_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("itemize", "itemize_decision_role")
            )

        def _mock_subject_research_source_collection_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("research", "research_source_collection")
            )

        def _mock_subject_research_source_revision_baseline_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("research", "research_source_revision_baseline")
            )

        def _mock_subject_research_selected_source_collection_membership_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("research", "research_selected_source_collection_membership")
            )

        def _mock_subject_research_source_revision_history_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_revision_history")
            )

        def _mock_subject_research_source_change_summary_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_change_summary")
            )

        def _mock_subject_research_source_collection_member_export_status_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_collection_member_export_status")
            )

        def _mock_subject_research_source_collection_member_revision_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_collection_member_revision")
            )

        def _mock_subject_research_source_collection_merge_export_history_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_collection_merge_export_history")
            )

        def _mock_subject_research_source_collection_actionable_export_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_collection_actionable_export")
            )

        def _mock_subject_research_source_collection_export_applied_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("research", "research_source_collection_export_applied")
            )

        def _mock_subject_review_comparison_history_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("review", "review_comparison_history")
            )

        def _mock_subject_review_latest_receipt_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("review", "review_latest_receipt")
            )

        def _mock_subject_publication_build_artifacts_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("publication", "publication_build_artifacts")
            )

        def _mock_subject_publication_build_receipt_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("publication", "publication_build_receipt")
            )

        def _mock_subject_publication_latest_receipt_table_spec(self) -> MockSubjectTableSpec:
            return self._mock_subject_table_spec_from_api_view(
                self._mock_subject_table_spec_from_bundle("publication", "publication_latest_receipt")
            )

        def _mock_subject_itemize_hold_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("itemize", "itemize_hold")
            )

        def _mock_subject_draft_semantic_kind_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_semantic_kind")
            )

        def _mock_subject_draft_render_kind_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_render_kind")
            )

        def _mock_subject_draft_evidence_mode_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_evidence_mode")
            )

        def _mock_subject_draft_transform_mode_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_transform_mode")
            )

        def _mock_subject_draft_decision_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("draft", "draft_decision_included")
            )

        def _mock_subject_draft_model_construct_sort_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_model_construct_sort")
            )

        def _mock_subject_draft_model_construct_lane_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_model_construct_lane")
            )

        def _mock_subject_draft_model_transition_source_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_model_transition_source")
            )

        def _mock_subject_draft_model_transition_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_model_transition_target")
            )

        def _mock_subject_draft_model_policy_profile_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("draft", "draft_model_policy_profile")
            )

        def _mock_subject_draft_model_relation_specs(self):
            return tuple(
                self._mock_subject_selection_list_spec_from_api_view(spec)
                for spec in getattr(self._mock_subject_control_bundle("draft"), "selection_lists", ()) or ()
            )

        def _refresh_itemize_decision_role_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_itemize_decision_role_select_id()}", TextualSelect)
            spec = self._mock_subject_itemize_decision_role_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_research_source_collection_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_research_source_collection_select_id()}", TextualSelect)
            spec = self._mock_subject_research_source_collection_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_research_source_revision_baseline_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_research_source_revision_baseline_select_id()}", TextualSelect)
            spec = self._mock_subject_research_source_revision_baseline_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_research_source_collection_membership_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_research_source_collection_membership_switch_id()}", TextualSwitch)
            spec = self._mock_subject_research_selected_source_collection_membership_spec()
            self._set_switch_state_programmatically(
                switch_id=_research_source_collection_membership_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _apply_data_table_spec(
            self,
            *,
            title_widget_id: str,
            table_widget_id: str,
            spec: MockSubjectTableSpec,
        ) -> None:
            if TextualDataTable is None:
                return
            title_widget = self.query_one(f"#{title_widget_id}", TextualStatic)
            table = self.query_one(f"#{table_widget_id}", TextualDataTable)
            if not spec.enabled or not spec.rows:
                title_widget.update("")
                title_widget.display = False
                table.display = False
                try:
                    table.clear(columns=True)
                except Exception:
                    pass
                return
            title_widget.update(spec.label)
            title_widget.display = True
            table.display = True
            try:
                table.clear(columns=True)
            except Exception:
                pass
            table.cursor_type = "row"
            table.zebra_stripes = True
            table.add_columns(*spec.columns)
            for row in spec.rows:
                table.add_row(*row)

        def _apply_structured_table_lines(
            self,
            *,
            widget: Any,
            lines: Iterable[str],
        ) -> None:
            if TextualDataTable is None:
                return
            widget_id = str(getattr(widget, "id", "") or "")
            table = widget
            row_lines = tuple(str(line or "") for line in lines)
            rows = _literal_table_rows_from_lines(row_lines)
            try:
                table.clear(columns=True)
            except Exception:
                pass
            if not rows:
                table.display = False
                return
            available_width = int(getattr(getattr(table, "size", None), "width", 0) or 0)
            if available_width <= 0:
                available_width = int(getattr(getattr(table, "region", None), "width", 0) or 0)
            available_width = max(available_width, 48)
            key_width = max(14, min(24, available_width // 3))
            value_width = max(24, available_width - key_width - 4)
            table.display = True
            table.cursor_type = "none"
            table.show_header = False
            table.show_row_labels = False
            table.show_horizontal_scrollbar = False
            table.show_vertical_scrollbar = False
            table.zebra_stripes = False
            try:
                table.styles.overflow_x = "hidden"
                table.styles.overflow_y = "auto"
                table.styles.scrollbar_size_horizontal = 0
                table.styles.scrollbar_size_vertical = 0
                table.styles.background = "transparent"
            except Exception:
                pass
            table.add_column("Field", width=key_width)
            table.add_column("Value", width=value_width)
            for key, value in rows:
                wrapped_key, key_height = _wrap_subject_status_table_cell(key, width=key_width)
                wrapped_value, value_height = _wrap_subject_status_table_cell(value, width=value_width)
                table.add_row(
                    wrapped_key,
                    wrapped_value,
                    height=max(key_height, value_height),
                )

        def _apply_structured_table_rows(
            self,
            *,
            widget: Any,
            rows: Iterable[tuple[str, str]],
        ) -> None:
            if TextualDataTable is None:
                return
            table = widget
            normalized_rows = tuple(
                (
                    collapse_ws(str(key or "")),
                    collapse_ws(str(value or "")),
                )
                for key, value in rows
            )
            try:
                table.clear(columns=True)
            except Exception:
                pass
            if not normalized_rows:
                table.display = False
                return
            available_width = int(getattr(getattr(table, "size", None), "width", 0) or 0)
            if available_width <= 0:
                available_width = int(getattr(getattr(table, "region", None), "width", 0) or 0)
            available_width = max(available_width, 48)
            key_width = max(14, min(24, available_width // 3))
            value_width = max(24, available_width - key_width - 4)
            table.display = True
            table.cursor_type = "none"
            table.show_header = False
            table.show_row_labels = False
            table.show_horizontal_scrollbar = False
            table.show_vertical_scrollbar = False
            table.zebra_stripes = False
            try:
                table.styles.overflow_x = "hidden"
                table.styles.overflow_y = "auto"
                table.styles.scrollbar_size_horizontal = 0
                table.styles.scrollbar_size_vertical = 0
                table.styles.background = "transparent"
            except Exception:
                pass
            table.add_column("Field", width=key_width)
            table.add_column("Value", width=value_width)
            for key, value in normalized_rows:
                wrapped_key, key_height = _wrap_subject_status_table_cell(key, width=key_width)
                wrapped_value, value_height = _wrap_subject_status_table_cell(value, width=value_width)
                table.add_row(
                    wrapped_key,
                    wrapped_value,
                    height=max(key_height, value_height),
                )

        def _apply_draft_scope_table_lines(
            self,
            *,
            widget: Any,
            lines: Iterable[str],
        ) -> None:
            if TextualDataTable is None:
                return
            table = widget
            scenario = self._mock_subject_scenario()
            if self._draft_model_mode_active():
                candidates = self._subject_projection_backend.transformation_construct_candidates(
                    root_path=self._root,
                    scenario=scenario,
                )
                mode = "model" if candidates else "fallback"
                projected_rows: list[tuple[str, ...]] = []
                for candidate in candidates:
                    sort_label = collapse_ws(candidate.sort_kind).replace("_", " ").title()
                    lane_label = collapse_ws(candidate.attributes.get("lane", "")).replace("_", " ").title()
                    orientation = f"{sort_label} -> {lane_label}" if lane_label else sort_label
                    projected_rows.append((
                        {"candidate": "c", "accepted": "a", "rejected": "r"}.get(
                            collapse_ws(candidate.status).casefold(),
                            "?",
                        ),
                        f"{candidate.canonical_label} ({orientation})".rstrip(),
                    ))
                rows = tuple(projected_rows)
            else:
                review_items = self._subject_projection_backend.flattened_draft_review_items(
                    root_path=self._root,
                    scenario=scenario,
                )
                mode = "review" if review_items else "fallback"
                projected_rows: list[tuple[str, ...]] = []
                for review_item, depth in review_items:
                    semantic_kind = collapse_ws(review_item.semantic_kind).replace("_", " ").title()
                    render_kind = collapse_ws(review_item.render_kind).replace("_", " ").title()
                    label = f"{'  ' * max(0, int(depth))}{review_item.canonical_label}"
                    statement = collapse_ws(review_item.attributes.get("source_statement", ""))
                    if statement:
                        label = f"{label}: {textwrap.shorten(statement, width=96, placeholder='...')}"
                    if semantic_kind or render_kind:
                        label = f"{label} ({semantic_kind} -> {render_kind})"
                    projected_rows.append(
                        (
                            "x" if review_item.included is True else " ",
                            "d"
                            if collapse_ws(review_item.attributes.get("in_decision", "")).casefold()
                            in {"true", "yes", "1"}
                            else " ",
                            label,
                        )
                    )
                rows = tuple(projected_rows)
            if not rows:
                rows = tuple(
                    (line,)
                    for raw_line in lines
                    if (line := collapse_ws(str(raw_line or "")))
                )
            try:
                table.clear(columns=True)
            except Exception:
                pass
            if not rows:
                table.display = False
                return
            available_width = int(getattr(getattr(table, "size", None), "width", 0) or 0)
            if available_width <= 0:
                available_width = int(getattr(getattr(table, "region", None), "width", 0) or 0)
            available_width = max(available_width, 48)
            table.display = True
            table.show_row_labels = False
            table.show_horizontal_scrollbar = False
            table.show_vertical_scrollbar = False
            table.zebra_stripes = False
            try:
                table.styles.overflow_x = "hidden"
                table.styles.overflow_y = "auto"
                table.styles.scrollbar_size_horizontal = 0
                table.styles.scrollbar_size_vertical = 0
                table.styles.background = "transparent"
            except Exception:
                pass
            if mode == "review":
                label_width = max(20, available_width - 5)
                table.cursor_type = "row"
                table.show_header = True
                table.add_column("X", width=3)
                table.add_column("Draft Item", width=label_width)
                for included, _decision, label in rows:
                    table.add_row(
                        included,
                        label,
                    )
                return
            if mode == "model":
                status_width = 3
                label_width = max(20, available_width - status_width - 2)
                table.cursor_type = "row"
                table.show_header = True
                table.add_column("S", width=status_width)
                table.add_column("Case Object", width=label_width)
                for status, label in rows:
                    wrapped_status, status_height = _wrap_subject_status_table_cell(status, width=status_width)
                    wrapped_label, label_height = _wrap_subject_status_table_cell(label, width=label_width)
                    table.add_row(
                        wrapped_status,
                        wrapped_label,
                        height=max(status_height, label_height),
                    )
                return
            table.cursor_type = "row"
            table.show_header = False
            table.add_column("Draft Item Inventory", width=max(24, available_width - 2))
            for row in rows:
                table.add_row(*row)

        def _research_sources_tree_label(self, *, prefix: str, source_kind: str, label: str) -> Any:
            text = _plain_ui_text(f"{prefix}[{source_kind}] {label}")
            return RichText(text) if RichText is not None else text

        def _append_research_source_tree_fields(self, parent: Any, rows: Iterable[tuple[str, str]]) -> None:
            for key, value in rows:
                normalized_key = collapse_ws(str(key or ""))
                normalized_value = collapse_ws(str(value or ""))
                if normalized_key and normalized_value:
                    parent.add_leaf(f"{normalized_key}: {normalized_value}", data={"selectable": False})
                elif normalized_value:
                    parent.add_leaf(normalized_value, data={"selectable": False})
                elif normalized_key:
                    parent.add_leaf(normalized_key, data={"selectable": False})

        def _refresh_research_sources_tree_widget(self, widget_id: str = "subject_sources_panel") -> None:  # pragma: no cover - requires textual runtime
            try:
                widget = self.query_one(f"#{widget_id}")
            except Exception:
                return
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            root_path = Path(self._root)
            collections = self._subject_projection_backend.source_collections(
                root_path=root_path,
                scenario=scenario,
                progress=progress,
            )
            selected_collection, staged_sources = self._subject_projection_backend.staged_sources_for_selected_collection(
                root_path=root_path,
                subject_id=scenario.subject_id,
                progress=progress,
            )
            selected_source_id = collapse_ws(getattr(progress, "research_selected_staged_source_id", ""))
            if selected_source_id and all(
                collapse_ws(getattr(staged_source, "staged_source_id", "")) != selected_source_id
                for staged_source in staged_sources
            ):
                selected_source_id = ""
            if not selected_source_id and staged_sources:
                selected_index = max(0, min(len(staged_sources) - 1, int(getattr(progress, "research_source_cursor", 0) or 0)))
                selected_source_id = collapse_ws(getattr(staged_sources[selected_index], "staged_source_id", ""))
            if TextualDataTable is not None and isinstance(widget, _FocusableTextualDataTable):
                table = widget
                try:
                    table.clear(columns=True)
                except Exception:
                    pass
                available_width = int(getattr(getattr(table, "size", None), "width", 0) or 0)
                if available_width <= 0:
                    available_width = int(getattr(getattr(table, "region", None), "width", 0) or 0)
                available_width = max(available_width, 48)
                key_width = max(16, min(24, available_width // 3))
                value_width = max(24, available_width - key_width - 4)
                table.display = True
                table.cursor_type = "row" if staged_sources else "none"
                table.show_header = False
                table.show_row_labels = False
                table.show_horizontal_scrollbar = False
                table.show_vertical_scrollbar = False
                table.zebra_stripes = False
                try:
                    table.styles.overflow_x = "hidden"
                    table.styles.overflow_y = "auto"
                    table.styles.scrollbar_size_horizontal = 0
                    table.styles.scrollbar_size_vertical = 0
                    table.styles.background = "transparent"
                except Exception:
                    pass
                table.add_column("Field", width=key_width)
                table.add_column("Value", width=value_width)
                row_to_source_ordinal: dict[int, int] = {}
                source_to_primary_row: dict[int, int] = {}

                def _add_row(key: str, value: str, *, source_ordinal: int | None = None) -> None:
                    wrapped_key, key_height = _wrap_subject_status_table_cell(key, width=key_width)
                    wrapped_value, value_height = _wrap_subject_status_table_cell(value, width=value_width)
                    row_index = int(getattr(table, "row_count", 0) or 0)
                    table.add_row(
                        wrapped_key,
                        wrapped_value,
                        height=max(key_height, value_height),
                    )
                    if source_ordinal is not None:
                        row_to_source_ordinal[row_index] = int(source_ordinal)
                        source_to_primary_row.setdefault(int(source_ordinal), row_index)

                _add_row("", "Staged Source Inventory")
                if selected_collection is not None:
                    workbench_rows = mock_subject_research_source_collection_workbench_rows(
                        root_path=root_path,
                        scenario=scenario,
                        progress=progress,
                        selected_collection=selected_collection,
                    )
                    _add_row("Current Set", collapse_ws(getattr(selected_collection, "title", "")) or collapse_ws(getattr(selected_collection, "collection_id", "")) or "<none>")
                    _add_row("Included Sources", str(len(getattr(selected_collection, "staged_source_ids", ()) or ())))
                    _add_row("Notes", collapse_ws(getattr(selected_collection, "description", "")) or "<none>")
                    _add_row("Query/Topic", collapse_ws(getattr(selected_collection, "query_text", "")) or "<none>")
                    for label, value in workbench_rows:
                        _add_row(str(label).title(), value)
                if collections:
                    _add_row("", "Source Sets")
                    selected_collection_id = collapse_ws(getattr(selected_collection, "collection_id", ""))
                    for collection in collections:
                        collection_id = collapse_ws(getattr(collection, "collection_id", ""))
                        collection_title = mock_source_collection_option_label(collection)
                        if collection_id and collection_id == selected_collection_id:
                            collection_title = f"Current: {collection_title}"
                        _add_row("Set", collection_title)
                        _add_row(
                            "Set Summary",
                            " | ".join(
                                [
                                    f"sources: {len(getattr(collection, 'staged_source_ids', ()) or ())}",
                                    f"query: {collapse_ws(getattr(collection, 'query_text', '')) or '<none>'}",
                                ]
                            ),
                        )
                        description = collapse_ws(getattr(collection, "description", ""))
                        if description:
                            _add_row("Set Notes", description)
                else:
                    _add_row("Source Sets", "No source sets yet.")

                _add_row("", "Sources")
                selected_collection_source_ids = {
                    collapse_ws(item)
                    for item in getattr(selected_collection, "staged_source_ids", ())
                    if collapse_ws(item)
                }
                selected_source_ordinal = None
                if staged_sources:
                    if selected_source_id:
                        for index, staged_source in enumerate(staged_sources):
                            if collapse_ws(getattr(staged_source, "staged_source_id", "")) == selected_source_id:
                                selected_source_ordinal = index
                                break
                    if selected_source_ordinal is None:
                        selected_source_ordinal = max(0, min(len(staged_sources) - 1, int(getattr(progress, "research_source_cursor", 0) or 0)))
                    for index, staged_source in enumerate(staged_sources):
                        staged_source_id = collapse_ws(getattr(staged_source, "staged_source_id", ""))
                        source_kind = collapse_ws(getattr(staged_source, "source_kind", "")) or "source"
                        source_title = collapse_ws(getattr(staged_source, "title", "")) or staged_source_id or "<none>"
                        is_selected = bool(selected_source_ordinal == index)
                        latest_revision = latest_source_revision(root_path, staged_source)
                        bundle_text = f"{len(getattr(latest_revision, 'bundle_relpaths', ()) or ())} files" if latest_revision is not None else "missing"
                        latest_kind = collapse_ws(getattr(latest_revision, "revision_kind", "")) if latest_revision is not None else ""
                        in_selected_set = (
                            selected_collection is not None
                            and staged_source_id in selected_collection_source_ids
                        )
                        source_label = f"[{source_kind}] {source_title}"
                        if is_selected:
                            source_label = f"Selected: {source_label}"
                        _add_row("Source", source_label, source_ordinal=index)
                        _add_row("Status", collapse_ws(getattr(staged_source, "status", "")) or "staged", source_ordinal=index)
                        _add_row("Ref", collapse_ws(getattr(staged_source, "source_ref", "")) or "<no-ref>", source_ordinal=index)
                        _add_row("Bundle", bundle_text, source_ordinal=index)
                        _add_row("Revisions", str(int(getattr(staged_source, "revision_count", 0) or 0)), source_ordinal=index)
                        if latest_kind:
                            _add_row("Latest Revision", latest_kind, source_ordinal=index)
                        if selected_collection is not None:
                            _add_row("In Set", "yes" if in_selected_set else "no", source_ordinal=index)
                else:
                    _add_row("Sources", "None staged yet.")

                _add_row("", "Admission State")
                _add_row("Linked Sources", str(scenario.source_count))
                _add_row("Deltas Applied", f"{scenario.applied_delta_count} of {scenario.delta_count}")
                _add_row("Active Support", str(scenario.reasoning_import_count))
                _add_row("Pending Support", str(scenario.pending_import_count))

                if scenario.source_preview_lines:
                    _add_row("", "Admitted Source Files")
                    for line in scenario.source_preview_lines:
                        normalized_line = collapse_ws(str(line or ""))
                        if normalized_line:
                            _add_row("Admitted Source File", normalized_line)
                if scenario.delta_preview_lines:
                    _add_row("", "Latest Delta")
                    _add_row("Delta", collapse_ws(str(scenario.delta_preview_lines[0] or "")))
                if scenario.pending_import_preview_lines:
                    _add_row("", "Pending Support")
                    for line in scenario.pending_import_preview_lines:
                        normalized_line = collapse_ws(str(line or ""))
                        if normalized_line:
                            _add_row("Pending Support", normalized_line)
                if scenario.import_preview_lines:
                    _add_row("", "Active Support")
                    for line in scenario.import_preview_lines:
                        normalized_line = collapse_ws(str(line or ""))
                        if normalized_line:
                            _add_row("Active Support", normalized_line)

                setattr(table, "_research_source_row_ordinals", row_to_source_ordinal)
                setattr(table, "_research_source_primary_rows", source_to_primary_row)
                if selected_source_ordinal is not None:
                    target_row = source_to_primary_row.get(int(selected_source_ordinal))
                    if target_row is not None:
                        self._inventory_option_sync_suppressed.add(widget_id)
                        try:
                            table.move_cursor(row=target_row, column=0, animate=False, scroll=True)
                        except Exception:
                            pass
                        finally:
                            self._inventory_option_sync_suppressed.discard(widget_id)
                        for scheduler_name in ("call_after_refresh", "call_later"):
                            scheduler = getattr(self, scheduler_name, None)
                            if not callable(scheduler):
                                continue
                            try:
                                scheduler(lambda row=target_row: table.move_cursor(row=row, column=0, animate=False, scroll=True))
                            except Exception:
                                continue
                return
            if TextualTree is None or not isinstance(widget, _FocusableTextualTree):
                return
            tree = widget

            self._inventory_option_sync_suppressed.add(widget_id)
            try:
                tree.reset("Source Sets")
                tree.show_root = False
                root = tree.root
                root.expand()
                inventory_branch = root.add("Staged Source Inventory", data={"selectable": False}, expand=True, allow_expand=True)

                set_branch = inventory_branch.add(
                    f"Source Sets ({scenario.source_collection_count})",
                    data={"selectable": False},
                    expand=True,
                    allow_expand=True,
                )
                if collections:
                    selected_collection_id = collapse_ws(getattr(selected_collection, "collection_id", ""))
                    for collection in collections:
                        collection_id = collapse_ws(getattr(collection, "collection_id", ""))
                        prefix = "> " if collection_id and collection_id == selected_collection_id else "  "
                        collection_node = set_branch.add(
                            self._research_sources_tree_label(
                                prefix=prefix,
                                source_kind="set",
                                label=mock_source_collection_option_label(collection),
                            ),
                            data={"selectable": False},
                            expand=bool(collection_id and collection_id == selected_collection_id),
                            allow_expand=True,
                        )
                        self._append_research_source_tree_fields(
                            collection_node,
                            (
                                ("sources", str(len(getattr(collection, "staged_source_ids", ()) or ()))),
                                ("query", collapse_ws(getattr(collection, "query_text", "")) or "<none>"),
                                ("notes", collapse_ws(getattr(collection, "description", "")) or "<none>"),
                            ),
                        )
                        if collection_id and collection_id == selected_collection_id:
                            self._append_research_source_tree_fields(
                                collection_node,
                                mock_subject_research_source_collection_workbench_rows(
                                    root_path=root_path,
                                    scenario=scenario,
                                    progress=progress,
                                    selected_collection=collection,
                                ),
                            )
                else:
                    set_branch.add_leaf("No source sets yet.", data={"selectable": False})

                sources_branch = inventory_branch.add(
                    f"Sources ({scenario.staged_source_count})",
                    data={"selectable": False},
                    expand=True,
                    allow_expand=True,
                )
                selected_node = None
                selected_collection_source_ids = {
                    collapse_ws(item)
                    for item in getattr(selected_collection, "staged_source_ids", ())
                    if collapse_ws(item)
                }
                if staged_sources:
                    for index, staged_source in enumerate(staged_sources):
                        staged_source_id = collapse_ws(getattr(staged_source, "staged_source_id", ""))
                        source_kind = collapse_ws(getattr(staged_source, "source_kind", "")) or "source"
                        source_title = collapse_ws(getattr(staged_source, "title", "")) or staged_source_id
                        is_selected = bool(staged_source_id and staged_source_id == selected_source_id)
                        source_node = sources_branch.add(
                            self._research_sources_tree_label(
                                prefix="> " if is_selected else "  ",
                                source_kind=source_kind,
                                label=source_title,
                            ),
                            data={
                                "selectable": True,
                                "selectable_index": index,
                                "staged_source_id": staged_source_id,
                            },
                            expand=is_selected,
                            allow_expand=True,
                        )
                        revision_count = int(getattr(staged_source, "revision_count", 0) or 0)
                        latest_revision = latest_source_revision(root_path, staged_source)
                        bundle_text = f"{len(getattr(latest_revision, 'bundle_relpaths', ()) or ())} files" if latest_revision is not None else "missing"
                        latest_kind = collapse_ws(getattr(latest_revision, "revision_kind", "")) if latest_revision is not None else ""
                        source_rows: list[tuple[str, str]] = [
                            ("status", collapse_ws(getattr(staged_source, "status", "")) or "staged"),
                            ("ref", collapse_ws(getattr(staged_source, "source_ref", "")) or "<no-ref>"),
                            ("bundle", bundle_text),
                            ("revisions", str(revision_count)),
                        ]
                        if latest_kind:
                            source_rows.append(("latest", latest_kind))
                        if selected_collection is not None:
                            source_rows.append(
                                (
                                    "in set",
                                    "yes" if staged_source_id in selected_collection_source_ids else "no",
                                )
                            )
                        self._append_research_source_tree_fields(source_node, source_rows)
                        if is_selected:
                            selected_node = source_node
                else:
                    sources_branch.add_leaf("No sources staged yet.", data={"selectable": False})

                admission_branch = inventory_branch.add(
                    "Admission State",
                    data={"selectable": False},
                    expand=True,
                    allow_expand=True,
                )
                self._append_research_source_tree_fields(
                    admission_branch,
                    (
                        ("linked sources", str(scenario.source_count)),
                        ("deltas applied", f"{scenario.applied_delta_count} of {scenario.delta_count}"),
                        ("active support", str(scenario.reasoning_import_count)),
                        ("pending support", str(scenario.pending_import_count)),
                    ),
                )

                supplemental_sections: tuple[tuple[str, tuple[str, ...]], ...] = (
                    ("Admitted Source Files", tuple(scenario.source_preview_lines)),
                    ("Latest Delta", tuple(scenario.delta_preview_lines[:1])),
                    ("Pending Support", tuple(scenario.pending_import_preview_lines)),
                    ("Active Support", tuple(scenario.import_preview_lines)),
                )
                for label, lines in supplemental_sections:
                    if not lines:
                        continue
                    branch = inventory_branch.add(
                        label,
                        data={"selectable": False},
                        expand=True,
                        allow_expand=True,
                    )
                    for line in lines:
                        normalized_line = collapse_ws(str(line or ""))
                        if normalized_line:
                            branch.add_leaf(normalized_line, data={"selectable": False})

                try:
                    tree.refresh(layout=True)
                except Exception:
                    pass
                if selected_node is not None:
                    try:
                        tree.move_cursor(selected_node, animate=False)
                    except Exception:
                        pass
                    try:
                        tree.scroll_to_node(selected_node, animate=False)
                    except Exception:
                        pass
                    line = int(getattr(selected_node, "_line", -1) or -1)
                    if line >= 0:
                        try:
                            tree.scroll_to_line(line, animate=False)
                        except Exception:
                            pass
                        try:
                            tree.scroll_to(y=max(line - 1, 0), animate=False, force=True, immediate=True)
                        except Exception:
                            pass
            finally:
                self._inventory_option_sync_suppressed.discard(widget_id)

        def _refresh_research_source_revision_history_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_revision_history_table_title_id(),
                table_widget_id=_research_source_revision_history_table_id(),
                spec=self._mock_subject_research_source_revision_history_table_spec(),
            )

        def _refresh_research_source_change_summary_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_change_summary_table_title_id(),
                table_widget_id=_research_source_change_summary_table_id(),
                spec=self._mock_subject_research_source_change_summary_table_spec(),
            )

        def _refresh_research_source_collection_member_export_status_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_collection_member_export_status_table_title_id(),
                table_widget_id=_research_source_collection_member_export_status_table_id(),
                spec=self._mock_subject_research_source_collection_member_export_status_table_spec(),
            )

        def _refresh_research_source_collection_member_revision_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_collection_member_revision_table_title_id(),
                table_widget_id=_research_source_collection_member_revision_table_id(),
                spec=self._mock_subject_research_source_collection_member_revision_table_spec(),
            )

        def _refresh_research_source_collection_merge_export_history_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_collection_merge_export_history_table_title_id(),
                table_widget_id=_research_source_collection_merge_export_history_table_id(),
                spec=self._mock_subject_research_source_collection_merge_export_history_table_spec(),
            )

        def _refresh_research_source_collection_actionable_export_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_collection_actionable_export_table_title_id(),
                table_widget_id=_research_source_collection_actionable_export_table_id(),
                spec=self._mock_subject_research_source_collection_actionable_export_table_spec(),
            )

        def _refresh_research_source_collection_export_applied_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_research_source_collection_export_applied_table_title_id(),
                table_widget_id=_research_source_collection_export_applied_table_id(),
                spec=self._mock_subject_research_source_collection_export_applied_table_spec(),
            )

        def _refresh_review_comparison_history_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_review_comparison_history_table_title_id(),
                table_widget_id=_review_comparison_history_table_id(),
                spec=self._mock_subject_review_comparison_history_table_spec(),
            )

        def _refresh_review_latest_receipt_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_review_latest_receipt_table_title_id(),
                table_widget_id=_review_latest_receipt_table_id(),
                spec=self._mock_subject_review_latest_receipt_table_spec(),
            )

        def _refresh_publication_build_artifacts_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_publication_build_artifacts_table_title_id(),
                table_widget_id=_publication_build_artifacts_table_id(),
                spec=self._mock_subject_publication_build_artifacts_table_spec(),
            )

        def _refresh_publication_build_receipt_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_publication_build_receipt_table_title_id(),
                table_widget_id=_publication_build_receipt_table_id(),
                spec=self._mock_subject_publication_build_receipt_table_spec(),
            )

        def _refresh_publication_latest_receipt_table(self) -> None:
            self._apply_data_table_spec(
                title_widget_id=_publication_latest_receipt_table_title_id(),
                table_widget_id=_publication_latest_receipt_table_id(),
                spec=self._mock_subject_publication_latest_receipt_table_spec(),
            )

        def _refresh_itemize_hold_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_itemize_hold_switch_id()}", TextualSwitch)
            spec = self._mock_subject_itemize_hold_spec()
            self._set_switch_state_programmatically(
                switch_id=_itemize_hold_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_draft_decision_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_draft_decision_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_draft_decision_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_draft_decision_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _set_switch_state_programmatically(
            self,
            *,
            switch_id: str,
            switch: Any,
            value: bool,
            enabled: bool,
        ) -> None:
            normalized_switch_id = collapse_ws(str(switch_id or ""))
            target_value = bool(value)
            if bool(getattr(switch, "value", False)) != target_value:
                pending_counts = self._programmatic_switch_change_counts.setdefault(normalized_switch_id, {})
                pending_counts[target_value] = int(pending_counts.get(target_value, 0) or 0) + 1
            self._suppress_switch_events = True
            try:
                switch.value = target_value
                switch.disabled = not enabled
            finally:
                self._suppress_switch_events = False

        def _consume_programmatic_switch_change(self, switch_id: str, target_value: bool) -> bool:
            normalized_switch_id = collapse_ws(str(switch_id or ""))
            pending_counts = self._programmatic_switch_change_counts.get(normalized_switch_id) or {}
            pending_count = int(pending_counts.get(bool(target_value), 0) or 0)
            if pending_count <= 0:
                return False
            if pending_count <= 1:
                pending_counts.pop(bool(target_value), None)
            else:
                pending_counts[bool(target_value)] = pending_count - 1
            if not pending_counts:
                self._programmatic_switch_change_counts.pop(normalized_switch_id, None)
            return True

        def _refresh_draft_semantic_kind_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_semantic_kind_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_semantic_kind_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_render_kind_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_render_kind_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_render_kind_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_evidence_mode_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_evidence_mode_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_evidence_mode_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_transform_mode_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_transform_mode_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_transform_mode_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_model_construct_sort_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_model_construct_sort_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_model_construct_sort_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_model_construct_lane_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_model_construct_lane_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_model_construct_lane_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_model_transition_selects(self) -> None:
            if TextualSelect is None:
                return
            source_select = self.query_one(f"#{_draft_model_transition_source_select_id()}", TextualSelect)
            target_select = self.query_one(f"#{_draft_model_transition_target_select_id()}", TextualSelect)
            source_spec = self._mock_subject_draft_model_transition_source_spec()
            target_spec = self._mock_subject_draft_model_transition_target_spec()
            row_visible = self._draft_model_mode_active() and bool(source_spec.options or target_spec.options)
            self._set_widget_display("draft_model_transition_group", row_visible)
            self._set_widget_display("draft_model_transition_row", row_visible)
            self._suppress_select_events = True
            try:
                with source_select.prevent(TextualSelect.Changed):
                    source_select.set_options([(label, value) for label, value in source_spec.options])
                    source_select.value = source_spec.value if collapse_ws(source_spec.value) else TextualSelect.NULL
                source_select.disabled = not source_spec.enabled
                with target_select.prevent(TextualSelect.Changed):
                    target_select.set_options([(label, value) for label, value in target_spec.options])
                    target_select.value = target_spec.value if collapse_ws(target_spec.value) else TextualSelect.NULL
                target_select.disabled = not target_spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_model_policy_profile_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_draft_model_policy_profile_select_id()}", TextualSelect)
            spec = self._mock_subject_draft_model_policy_profile_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_draft_model_lens_tabs(self) -> None:
            if TextualTabs is None:
                return
            tabs = self.query_one(f"#{_draft_model_lens_tabs_id()}", TextualTabs)
            model_mode_active = self._draft_model_mode_active()
            self._set_widget_display("draft_choice_group", not model_mode_active)
            self._set_widget_display("draft_choice_row", not model_mode_active)
            self._set_widget_display("draft_model_construct_group", model_mode_active)
            self._set_widget_display("draft_model_choice_row", model_mode_active)
            active_lens = collapse_ws(str(getattr(self._mock_subject_progress(), "draft_model_lens", "") or "")).casefold()
            if active_lens not in {"frame", "model", "explore"}:
                active_lens = "model"
            try:
                self.query_one("#draft_model_lens_group").display = model_mode_active
            except Exception:
                pass
            try:
                self.query_one("#draft_model_lens_row").display = model_mode_active
            except Exception:
                pass
            self._suppress_tabs_events = True
            try:
                tabs.disabled = not model_mode_active
                tabs.display = model_mode_active
                tabs.active = _draft_model_lens_tab_id(active_lens)
            finally:
                self._suppress_tabs_events = False

        def _refresh_draft_model_relation_selection_lists(self) -> None:
            if TextualSelectionList is None:
                return
            specs = self._mock_subject_draft_model_relation_specs()
            row_visible = self._draft_model_mode_active() and bool(specs)
            self._set_widget_display("draft_model_relation_group", row_visible)
            self._set_widget_display("draft_model_relation_row", row_visible)
            for slot in range(2):
                wrapper_id = _draft_model_relation_wrapper_id(slot)
                label_id = _draft_model_relation_label_id(slot)
                list_id = _draft_model_relation_selection_list_id(slot)
                try:
                    wrapper = self.query_one(f"#{wrapper_id}")
                    label_widget = self.query_one(f"#{label_id}", TextualStatic)
                    selection_list = self.query_one(f"#{list_id}", TextualSelectionList)
                except Exception:
                    continue
                spec = specs[slot] if slot < len(specs) and row_visible else None
                wrapper.display = spec is not None
                if spec is None:
                    label_widget.update("")
                    self._suppress_selection_list_events = True
                    try:
                        with selection_list.prevent(TextualSelectionList.SelectedChanged):
                            selection_list.clear_options()
                        selection_list.disabled = True
                    finally:
                        self._suppress_selection_list_events = False
                    continue
                label_widget.update(spec.label)
                highlighted_index = getattr(selection_list, "highlighted", None)
                option_count = len(spec.options)
                self._suppress_selection_list_events = True
                try:
                    with selection_list.prevent(TextualSelectionList.SelectedChanged):
                        selection_list.clear_options()
                        selection_list.add_options(
                            (label, value, selected)
                            for label, value, selected in spec.options
                        )
                        if option_count and bool(getattr(selection_list, "has_focus", False)):
                            next_highlight = highlighted_index if isinstance(highlighted_index, int) else 0
                            selection_list.highlighted = max(0, min(option_count - 1, next_highlight))
                    selection_list.disabled = not spec.enabled
                finally:
                    self._suppress_selection_list_events = False

        def _mock_subject_review_publication_output_mode_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("review", "review_publication_output_mode")
            )

        def _mock_subject_review_publication_section_plan_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("review", "review_publication_section_plan")
            )

        def _mock_subject_review_publication_diff_baseline_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("review", "review_publication_diff_baseline")
            )

        def _mock_subject_review_composition_unit_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("review", "review_composition_unit_target")
            )

        def _mock_subject_review_composition_unit_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("review", "review_composition_unit_included")
            )

        def _mock_subject_review_publication_section_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("review", "review_publication_section_target")
            )

        def _mock_subject_review_publication_section_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("review", "review_publication_section_included")
            )

        def _mock_subject_publication_output_mode_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_output_mode")
            )

        def _mock_subject_publication_section_plan_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_section_plan")
            )

        def _mock_subject_publication_diff_baseline_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_diff_baseline")
            )

        def _mock_subject_publication_import_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_import_target")
            )

        def _mock_subject_publication_composition_unit_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_composition_unit_target")
            )

        def _mock_subject_publication_composition_unit_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("publication", "publication_composition_unit_included")
            )

        def _mock_subject_publication_section_target_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_section_target")
            )

        def _mock_subject_publication_section_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("publication", "publication_section_included")
            )

        def _mock_subject_publication_import_included_spec(self):
            return self._mock_subject_switch_spec_from_api_view(
                self._mock_subject_switch_spec_from_bundle("publication", "publication_import_included")
            )

        def _mock_subject_publication_import_usage_spec(self):
            return self._mock_subject_select_spec_from_api_view(
                self._mock_subject_select_spec_from_bundle("publication", "publication_import_usage")
            )

        def _refresh_review_publication_output_mode_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_review_publication_output_mode_select_id()}", TextualSelect)
            spec = self._mock_subject_review_publication_output_mode_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_review_publication_section_plan_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_review_publication_section_plan_select_id()}", TextualSelect)
            spec = self._mock_subject_review_publication_section_plan_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_review_publication_diff_baseline_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_review_publication_diff_baseline_select_id()}", TextualSelect)
            spec = self._mock_subject_review_publication_diff_baseline_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_review_composition_unit_target_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_review_composition_unit_target_select_id()}", TextualSelect)
            spec = self._mock_subject_review_composition_unit_target_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_review_composition_unit_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_review_composition_unit_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_review_composition_unit_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_review_composition_unit_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_review_publication_section_target_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_review_publication_section_target_select_id()}", TextualSelect)
            spec = self._mock_subject_review_publication_section_target_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_review_publication_section_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_review_publication_section_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_review_publication_section_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_review_publication_section_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_publication_output_mode_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_output_mode_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_output_mode_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_section_plan_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_section_plan_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_section_plan_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_diff_baseline_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_diff_baseline_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_diff_baseline_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_import_target_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_import_target_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_import_target_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_composition_unit_target_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_composition_unit_target_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_composition_unit_target_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_composition_unit_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_publication_composition_unit_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_publication_composition_unit_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_publication_composition_unit_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_publication_section_target_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_section_target_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_section_target_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _refresh_publication_section_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_publication_section_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_publication_section_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_publication_section_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_publication_import_included_switch(self) -> None:
            if TextualSwitch is None:
                return
            switch = self.query_one(f"#{_publication_import_included_switch_id()}", TextualSwitch)
            spec = self._mock_subject_publication_import_included_spec()
            self._set_switch_state_programmatically(
                switch_id=_publication_import_included_switch_id(),
                switch=switch,
                value=bool(spec.value),
                enabled=bool(spec.enabled),
            )

        def _refresh_publication_import_usage_select(self) -> None:
            if TextualSelect is None:
                return
            select = self.query_one(f"#{_publication_import_usage_select_id()}", TextualSelect)
            spec = self._mock_subject_publication_import_usage_spec()
            options = [(label, value) for label, value in spec.options]
            self._suppress_select_events = True
            try:
                with select.prevent(TextualSelect.Changed):
                    select.set_options(options)
                    select.value = spec.value if collapse_ws(spec.value) else TextualSelect.NULL
                select.disabled = not spec.enabled
            finally:
                self._suppress_select_events = False

        def _mock_subject_header_text(self, phase: str) -> str:
            return ""

        def _mock_subject_header_subject_text(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            title = collapse_ws(scenario.title)
            return f"Current Subject: {title}" if title else ""

        def _mock_subject_status_panel_text(self, phase: str) -> str:
            return self._render_subject_status_view_text(self._mock_subject_phase_view(phase))

        def _mock_subject_last_action_text(self) -> str:
            return collapse_ws(self._mock_subject_status_text) or "Live subject workflow ready."

        def _mock_subject_current_step_text(self, phase: str) -> str:
            return self._render_subject_current_step_view_text(self._mock_subject_phase_view(phase))

        def _mock_subject_journey_text(self, phase: str) -> str:
            journey_text = self._render_subject_journey_view_text(self._mock_subject_phase_view(phase))
            last_action = collapse_ws(self._mock_subject_last_action_text())
            if not last_action:
                return journey_text
            if not collapse_ws(journey_text):
                return f"Last Action: {last_action}"
            return f"Last Action: {last_action}\n{journey_text}"

        def _mock_subject_current_step_actions(self, phase: str) -> tuple[MockSubjectGateAction, ...]:
            return self._subject_gate_actions_from_phase_view(self._mock_subject_phase_view(phase))

        def _mock_subject_workspace_text(self, phase: str) -> str:
            return self._render_subject_workspace_view_text(self._mock_subject_phase_view(phase))

        def _mock_subject_research_sources_text(self) -> str:
            return self._mock_subject_pane_text("research", "research_sources")

        def _mock_subject_research_observation_text(self) -> str:
            return self._mock_subject_pane_text("research", "research_observation")

        def _mock_subject_research_target_text(self) -> str:
            return self._mock_subject_pane_text("research", "research_target")

        def _mock_subject_research_target_title(self) -> str:
            return self._mock_subject_pane_title("research", "research_target")

        def _selected_research_source_collection(self):
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return None
            progress = self._mock_subject_progress()
            collections = self._subject_projection_backend.source_collections(
                root_path=self._root,
                scenario=scenario,
                progress=progress,
            )
            if not collections:
                return None
            selected_id = collapse_ws(getattr(progress, "research_selected_source_collection_id", ""))
            if selected_id:
                for collection in collections:
                    if collapse_ws(getattr(collection, "collection_id", "")) == selected_id:
                        return collection
            index = max(0, min(len(collections) - 1, int(getattr(progress, "research_collection_cursor", 0) or 0)))
            return collections[index]

        def _mock_subject_research_sources_title(self) -> str:
            return self._mock_subject_pane_title("research", "research_sources") or "Source Sets"

        def _mock_subject_itemize_inventory_text(self) -> str:
            return self._mock_subject_pane_text("itemize", "itemize_inventory")

        def _mock_subject_itemize_detail_text(self) -> str:
            return self._mock_subject_pane_text("itemize", "itemize_detail")

        def _mock_subject_itemize_detail_title(self) -> str:
            return self._mock_subject_pane_title("itemize", "itemize_detail")

        def _mock_subject_itemize_target_text(self) -> str:
            return self._mock_subject_pane_text("itemize", "itemize_target")

        def _mock_subject_review_scope_tree_text(self) -> str:
            return self._mock_subject_pane_text("review", "review_scope_tree")

        def _mock_subject_draft_scope_tree_text(self) -> str:
            return self._mock_subject_pane_text("draft", "draft_scope_tree")

        def _mock_subject_review_scope_detail_text(self) -> str:
            return self._mock_subject_pane_text("review", "review_scope_detail")

        def _mock_subject_publication_scope_detail_text(self) -> str:
            return self._mock_subject_pane_text("publication", "publication_scope_detail")

        def _mock_subject_draft_detail_text(self) -> str:
            return self._mock_subject_pane_text("draft", "draft_detail")

        def _mock_subject_review_scope_detail_title(self) -> str:
            return self._mock_subject_pane_title("review", "review_scope_detail")

        def _mock_subject_publication_scope_detail_title(self) -> str:
            return self._mock_subject_pane_title("publication", "publication_scope_detail")

        def _mock_subject_draft_detail_title(self) -> str:
            return self._mock_subject_pane_title("draft", "draft_detail")

        def _mock_subject_draft_tree_title(self) -> str:
            return self._mock_subject_pane_title("draft", "draft_scope_tree")

        def _mock_subject_draft_model_main_text(self) -> str:
            return self._mock_subject_pane_text("draft", "draft_model_main")

        def _mock_subject_draft_model_main_title(self) -> str:
            return self._mock_subject_pane_title("draft", "draft_model_main")

        def _mock_subject_draft_result_title(self) -> str:
            return self._mock_subject_pane_title("draft", "draft_result")

        def _mock_subject_draft_issue_tray_text(self) -> str:
            return self._mock_subject_pane_text("draft", "draft_result")

        def _mock_subject_workspace_title(self, phase: str) -> str:
            workspace_view = getattr(self._mock_subject_phase_view(phase), "workspace_view", None)
            return str(getattr(workspace_view, "title", "") or "")

        def _research_sources_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return ""
            collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
            if collection_kind == "all_gather_sources":
                return ""
            sources_text = str(self._mock_subject_research_sources_text() or "").strip()
            if not sources_text:
                return ""
            return (
                "Curate this selected Gather source set.\n"
                "Treat it as source-management metadata only, not as admitted corpus truth and not as publication prose.\n"
                "You may improve the set title, describe what belongs in the set, and refine the saved topic/query text.\n"
                "Do not rewrite the individual source bodies here.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<source set title>\n\n"
                "[description]\n"
                "<what belongs in this source set and how it should be maintained>\n\n"
                "[query]\n"
                "<saved topic or query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {collapse_ws(getattr(selected_collection, 'title', '')) or collapse_ws(getattr(selected_collection, 'collection_id', ''))}\n\n"
                "Source-set details:\n"
                f"{sources_text}"
            )

        def _research_source_discovery_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return ""
            collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
            if collection_kind == "all_gather_sources":
                return ""
            query_text = collapse_ws(getattr(selected_collection, "query_text", ""))
            if not query_text:
                return ""
            sources_text = str(self._mock_subject_research_sources_text() or "").strip()
            if not sources_text:
                return ""
            return (
                "Find high-value source material for this selected Gather source set.\n"
                "Treat the result as staged source discovery only, not as admitted corpus truth and not as publication prose.\n"
                "Use the saved query/topic and the current source-set context.\n"
                "Prefer direct source URLs and avoid duplicates.\n\n"
                "Return only this format, repeating one block per source:\n\n"
                "[source]\n"
                "[label]\n"
                "<short source title>\n\n"
                "[url]\n"
                "<direct source url>\n\n"
                "[notes]\n"
                "<why this source is relevant and how it should be used at the source layer>\n\n"
                "Provide up to 5 sources.\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {collapse_ws(getattr(selected_collection, 'title', '')) or collapse_ws(getattr(selected_collection, 'collection_id', ''))}\n"
                f"Saved query/topic: {query_text}\n\n"
                "Source-set details:\n"
                f"{sources_text}"
            )

        def _research_source_collection_synthesis_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return ""
            collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
            if collection_kind == "all_gather_sources":
                return ""
            sources_text = str(self._mock_subject_research_sources_text() or "").strip()
            target_text = str(self._mock_subject_research_target_text() or "").strip()
            if not sources_text:
                return ""
            return (
                "Synthesize this selected Gather source set into a maintained source-layer knowledgebase summary.\n"
                "Treat the result as staged source-set metadata only, not as admitted corpus truth and not as publication prose.\n"
                "Summarize what the set currently covers, what remains missing or uncertain, and how the saved query/topic should evolve.\n"
                "Do not rewrite the individual staged source bodies here.\n\n"
                "Return only this format:\n"
                "[summary]\n"
                "<what this source set currently covers and how it should be used>\n\n"
                "[questions]\n"
                "<one open question per line; may be blank>\n\n"
                "[query]\n"
                "<updated saved topic/query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {collapse_ws(getattr(selected_collection, 'title', '')) or collapse_ws(getattr(selected_collection, 'collection_id', ''))}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and current knowledgebase state:\n"
                f"{target_text}"
            )

        def _research_source_collection_merge_back_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return ""
            collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
            if collection_kind == "all_gather_sources":
                return ""
            sources_text = str(self._mock_subject_research_sources_text() or "").strip()
            observation_text = str(self._mock_subject_research_observation_text() or "").strip()
            target_text = str(self._mock_subject_research_target_text() or "").strip()
            if not sources_text or not observation_text:
                return ""
            return (
                "Prepare a merge-back proposal for this selected Gather source set.\n"
                "Use the current subject learnings to improve the source-set notes and saved query so future discovery and maintenance reflect what the subject now knows.\n"
                "Keep the result at the source layer only. Do not treat it as admitted corpus truth, do not turn it into publication prose, and do not rewrite the individual staged source bodies here.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<source set title>\n\n"
                "[description]\n"
                "<updated source-set notes and maintenance framing>\n\n"
                "[query]\n"
                "<updated saved topic or query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {collapse_ws(getattr(selected_collection, 'title', '')) or collapse_ws(getattr(selected_collection, 'collection_id', ''))}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and export preview:\n"
                f"{target_text}"
            )

        def _research_source_collection_source_merge_back_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return ""
            collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
            if collection_kind == "all_gather_sources":
                return ""
            sources_text = str(self._mock_subject_research_sources_text() or "").strip()
            observation_text = str(self._mock_subject_research_observation_text() or "").strip()
            target_text = str(self._mock_subject_research_target_text() or "").strip()
            if not sources_text or not observation_text or not target_text:
                return ""
            return (
                "Prepare merge-back proposals for the member staged sources in this selected Gather source set.\n"
                "Use the current subject learnings to improve the staged source notes while keeping them at the source layer.\n"
                "Do not treat the result as admitted corpus truth and do not turn it into publication prose.\n"
                "Update only the staged sources that clearly need changes.\n\n"
                "Return only this format, repeating one block per staged source that should change:\n\n"
                "[source]\n"
                "[url]\n"
                "<existing staged source url>\n\n"
                "[label]\n"
                "<updated staged source title>\n\n"
                "[text]\n"
                "<updated staged source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {collapse_ws(getattr(selected_collection, 'title', '')) or collapse_ws(getattr(selected_collection, 'collection_id', ''))}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and member export targets:\n"
                f"{target_text}"
            )

        def _research_detail_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            detail_title = collapse_ws(self._mock_subject_research_target_title())
            detail_text = str(self._mock_subject_research_target_text() or "").strip()
            if not detail_text or detail_title == "Source Detail":
                return ""
            return (
                "Curate this selected staged source in Gather.\n"
                "Treat it as source material only, not as admitted corpus truth and not as publication prose.\n"
                "You may de-jargonize, clarify, summarize, reorganize headings, or make the source easier to maintain for future import.\n"
                "Do not turn it into final report language.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short source title>\n\n"
                "[text]\n"
                "<curated source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected staged source: {detail_title}\n\n"
                "Source details:\n"
                f"{detail_text}"
            )

        def _research_source_merge_back_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            detail_title = collapse_ws(self._mock_subject_research_target_title())
            detail_text = str(self._mock_subject_research_target_text() or "").strip()
            observation_text = str(self._mock_subject_research_observation_text() or "").strip()
            if not detail_text or detail_title == "Current subject assets" or not observation_text:
                return ""
            return (
                "Prepare a merge-back proposal for this selected staged source.\n"
                "Use the current subject learnings to improve the staged source notes while keeping them at the source layer.\n"
                "Do not treat the result as admitted corpus truth and do not turn it into publication prose.\n"
                "You may fold learned facts, clarifying headings, topic framing, and maintenance notes back into the staged source.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short source title>\n\n"
                "[text]\n"
                "<updated staged source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected staged source: {detail_title}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Current staged source details:\n"
                f"{detail_text}"
            )

        def _itemize_detail_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            detail_title = collapse_ws(self._mock_subject_itemize_detail_title())
            detail_text = str(self._mock_subject_itemize_detail_text() or "").strip()
            if not detail_title or not detail_text:
                return ""
            return (
                "Rephrase this selected itemized candidate for clarity as a normalized intermediate.\n"
                "Preserve the facts and source meaning.\n"
                "Do not turn it into final publication prose.\n"
                "Prefer reusable wording that will make later Draft composition easier.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short normalized label>\n\n"
                "[text]\n"
                "<rephrased normalized wording>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected item: {detail_title}\n\n"
                "Item details:\n"
                f"{detail_text}"
            )

        def _draft_detail_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            detail_title = collapse_ws(self._mock_subject_draft_detail_title())
            detail_text = str(self._mock_subject_draft_detail_text() or "").strip()
            if not detail_title or not detail_text:
                return ""
            return (
                "Rephrase this selected draft item for publication clarity.\n"
                "Stay grounded in the material below. Do not invent facts.\n"
                "Preserve scope, evidence intent, and meaning while improving readability and maturity.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short publication-ready label>\n\n"
                "[text]\n"
                "<rephrased draft wording>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected item: {detail_title}\n\n"
                "Selection details:\n"
                f"{detail_text}"
            )

        def _review_scope_detail_chat_prompt(self) -> str:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return ""
            selected = self._subject_projection_backend.selected_report_scope_section_entry(
                root_path=self._root,
                scenario=scenario,
                progress=self._mock_subject_progress(),
            )
            if selected is None:
                return ""
            _composition, _entry, _section_id, role, title = selected
            detail_text = str(self._mock_subject_review_scope_detail_text() or "").strip()
            if not title or not detail_text:
                return ""
            return (
                "Draft a section brief for the selected report section.\n"
                "This is publication-composition guidance, not source cleanup and not final report prose.\n"
                "Stay grounded in the material below. Do not invent facts.\n"
                "Explain what this section should accomplish and what the reader should take from it.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short section brief label>\n\n"
                "[text]\n"
                "<brief guidance for composing this section>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Section: {title}\n"
                f"Role: {role or '<unknown>'}\n\n"
                "Section details:\n"
                f"{detail_text}"
            )

        def _selected_itemize_item_supports_manual_rephrase(self) -> bool:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return False
            selected_item = self._subject_projection_backend.selected_itemization_item(
                root_path=self._root,
                scenario=scenario,
                progress=self._mock_subject_progress(),
            )
            return (
                selected_item is not None
                and collapse_ws(str(getattr(selected_item, "status", ""))) in {"candidate", "promoted", "rejected"}
            )

        def _selected_draft_item_supports_manual_rephrase(self) -> bool:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return False
            selected_item, _selection_source = self._subject_projection_backend.selected_draft_review_item(
                root_path=self._root,
                scenario=scenario,
                progress=self._mock_subject_progress(),
            )
            return selected_item is not None

        def _selected_review_section_supports_shaping(self) -> bool:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return False
            return (
                self._subject_projection_backend.selected_report_scope_section_entry(
                    root_path=self._root,
                    scenario=scenario,
                    progress=self._mock_subject_progress(),
                )
                is not None
            )

        def _selected_research_source_supports_manual_curation(self) -> bool:
            scenario = self._mock_subject_scenario()
            if getattr(scenario, "is_placeholder", False):
                return False
            progress = self._mock_subject_progress()
            _selected_collection, staged_sources = self._subject_projection_backend.staged_sources_for_selected_collection(
                root_path=self._root,
                subject_id=collapse_ws(getattr(scenario, "subject_id", "")),
                progress=progress,
            )
            selected_id = collapse_ws(getattr(progress, "research_selected_staged_source_id", ""))
            if selected_id:
                return any(collapse_ws(source.staged_source_id) == selected_id for source in staged_sources)
            return bool(staged_sources)

        def _selected_research_collection_supports_curation(self) -> bool:
            selected_collection = self._selected_research_source_collection()
            if selected_collection is None:
                return False
            return collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", ""))) != "all_gather_sources"

        def _refresh_itemize_detail_buttons(self) -> None:
            try:
                llm_button = self.query_one(f"#{_itemize_detail_llm_button_id()}", TextualButton)
                llm_button.disabled = not bool(collapse_ws(self._itemize_detail_chat_prompt()))
            except Exception:
                pass
            try:
                manual_button = self.query_one(f"#{_itemize_detail_manual_rephrase_button_id()}", TextualButton)
                manual_button.disabled = not self._selected_itemize_item_supports_manual_rephrase()
            except Exception:
                pass

        def _refresh_research_detail_buttons(self) -> None:
            try:
                llm_button = self.query_one(f"#{_research_sources_llm_button_id()}", TextualButton)
                llm_button.disabled = not bool(collapse_ws(self._research_sources_chat_prompt()))
            except Exception:
                pass
            try:
                manual_button = self.query_one(f"#{_research_sources_manual_rephrase_button_id()}", TextualButton)
                manual_button.disabled = not self._selected_research_collection_supports_curation()
            except Exception:
                pass
            try:
                llm_button = self.query_one(f"#{_research_detail_llm_button_id()}", TextualButton)
                llm_button.disabled = not bool(collapse_ws(self._research_detail_chat_prompt()))
            except Exception:
                pass
            try:
                manual_button = self.query_one(f"#{_research_detail_manual_rephrase_button_id()}", TextualButton)
                manual_button.disabled = not self._selected_research_source_supports_manual_curation()
            except Exception:
                pass

        def _refresh_draft_detail_buttons(self) -> None:
            try:
                llm_button = self.query_one(f"#{_draft_detail_llm_button_id()}", TextualButton)
                llm_button.disabled = not bool(collapse_ws(self._draft_detail_chat_prompt()))
            except Exception:
                pass
            try:
                manual_button = self.query_one(f"#{_draft_detail_manual_rephrase_button_id()}", TextualButton)
                manual_button.disabled = not self._selected_draft_item_supports_manual_rephrase()
            except Exception:
                pass

        def _refresh_review_detail_buttons(self) -> None:
            try:
                llm_button = self.query_one(f"#{_review_detail_llm_button_id()}", TextualButton)
                llm_button.disabled = not bool(collapse_ws(self._review_scope_detail_chat_prompt()))
            except Exception:
                pass
            try:
                manual_button = self.query_one(f"#{_review_detail_manual_rephrase_button_id()}", TextualButton)
                manual_button.disabled = not self._selected_review_section_supports_shaping()
            except Exception:
                pass

        def _open_follow_up_in_chat(self, *, prompt: str, started_text: str) -> bool:
            if not collapse_ws(prompt):
                return False
            self._set_active_tab("chat_tab")
            if self._state.is_busy():
                self._state.append_transcript_block(label="shell", text="A turn is already running.")
                return False
            input_widget = self.query_one("#input", TextualInput)
            input_widget.value = ""
            self._state.set_current_input_text("", refresh=False)
            self._refresh_inline_hint()
            self._refresh_prompt_suggestions()
            input_widget.focus()
            self._record_shell_status_turn(shell_text=started_text)
            self._pin_transcript_to_bottom()
            self._start_app_worker(
                target=_run_enhanced_workstation_turn_worker,
                kwargs={
                    "state": self._state,
                    "prompt": prompt,
                    "model": self._model,
                    "max_tool_rounds": self._max_tool_rounds,
                },
                name="chat-follow-up-worker",
            )
            return True

        def _open_itemize_detail_in_chat(self) -> bool:
            if self._state.is_busy():
                return False
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="itemize",
                action_key="start_itemize_llm_rephrase",
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self.request_state_refresh()
            if not collapse_ws(progress.itemize_llm_rephrase_item_id):
                return False
            return self._open_follow_up_in_chat(
                prompt=self._itemize_detail_chat_prompt(),
                started_text="Started an itemize-item rephrase in Chat. Reply with [label] and [text] sections only.",
            )

        def _open_research_follow_up_in_chat(
            self,
            *,
            action_key: str,
            progress_field: str,
            prompt: str,
            started_text: str,
        ) -> bool:
            if not collapse_ws(prompt):
                return False
            if self._state.is_busy():
                return False
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="research",
                action_key=action_key,
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self.request_state_refresh()
            if not collapse_ws(str(getattr(progress, progress_field, "") or "")):
                return False
            return self._open_follow_up_in_chat(
                prompt=prompt,
                started_text=started_text,
            )

        def _open_research_sources_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_collection_llm_curation",
                progress_field="research_source_collection_llm_curation_collection_id",
                prompt=self._research_sources_chat_prompt(),
                started_text="Started a Gather source-set curation in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
            )

        def _open_research_source_discovery_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_collection_discovery",
                progress_field="research_source_collection_discovery_collection_id",
                prompt=self._research_source_discovery_chat_prompt(),
                started_text="Started a Gather source-discovery turn in Chat. Reply with repeated [source] blocks using [label], [url], and [notes] only, and keep the result at the source layer.",
            )

        def _open_research_source_collection_synthesis_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_collection_synthesis",
                progress_field="research_source_collection_synthesis_collection_id",
                prompt=self._research_source_collection_synthesis_chat_prompt(),
                started_text="Started a Gather source-set synthesis in Chat. Reply with [summary], [questions], and [query] sections only, and keep the result at the source layer.",
            )

        def _open_research_source_collection_merge_back_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_collection_merge_back",
                progress_field="research_source_collection_merge_back_collection_id",
                prompt=self._research_source_collection_merge_back_chat_prompt(),
                started_text="Started a Gather source-set merge-back in Chat. Reply with [label], [description], and [query] sections only, and keep the result at the source layer.",
            )

        def _open_research_source_collection_source_merge_back_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_collection_source_merge_back",
                progress_field="research_source_collection_source_merge_back_collection_id",
                prompt=self._research_source_collection_source_merge_back_chat_prompt(),
                started_text="Started a Gather set-source merge-back in Chat. Reply with repeated [source] blocks using [url], [label], and [text] only, and keep the result at the source layer.",
            )

        def _open_research_detail_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_llm_curation",
                progress_field="research_source_llm_curation_staged_source_id",
                prompt=self._research_detail_chat_prompt(),
                started_text="Started a Gather source curation in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
            )

        def _open_research_source_merge_back_in_chat(self) -> bool:
            return self._open_research_follow_up_in_chat(
                action_key="start_research_source_merge_back",
                progress_field="research_source_merge_back_staged_source_id",
                prompt=self._research_source_merge_back_chat_prompt(),
                started_text="Started a Gather source merge-back in Chat. Reply with [label] and [text] sections only, and keep the result at the source layer.",
            )

        def _handle_research_chat_action_target(self, command_name: str, arguments_text: str = "") -> bool:
            normalized_command = collapse_ws(command_name)
            spec = _RESEARCH_CHAT_ACTION_TARGET_SPECS.get(normalized_command)
            if spec is None:
                return False
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="research",
                action_key=str(spec.get("action_key", "")),
                assistant_message_text=str(arguments_text or self._latest_assistant_research_capture_text()),
            )
            self._apply_mock_subject_action_result(
                "research",
                scenario,
                progress,
                str(spec.get("action_key", "")),
                result,
            )
            refreshed_progress = self._mock_subject_progress()
            message_lines = [collapse_ws(result.status_text)]
            message_lines.extend(str(line).rstrip() for line in getattr(refreshed_progress, "latest_receipt_lines", ()) if collapse_ws(str(line)))
            message = "\n".join(line for line in message_lines if collapse_ws(line)).rstrip()
            if message:
                self._record_shell_status_turn(prompt_text=normalized_command, shell_text=message)
            return True

        def _handle_research_chat_prompt_target(self, command_name: str) -> bool:
            normalized_command = collapse_ws(command_name)
            if normalized_command == "/curate-source":
                return self._open_research_detail_in_chat()
            if normalized_command == "/merge-source":
                return self._open_research_source_merge_back_in_chat()
            if normalized_command == "/curate-source-set":
                return self._open_research_sources_in_chat()
            if normalized_command == "/find-sources":
                return self._open_research_source_discovery_in_chat()
            if normalized_command == "/synthesize-source-set":
                return self._open_research_source_collection_synthesis_in_chat()
            if normalized_command == "/merge-source-set":
                return self._open_research_source_collection_merge_back_in_chat()
            if normalized_command == "/merge-set-sources":
                return self._open_research_source_collection_source_merge_back_in_chat()
            return False

        def _open_draft_detail_in_chat(self) -> bool:
            if self._state.is_busy():
                return False
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="draft",
                action_key="start_draft_llm_rephrase",
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self.request_state_refresh()
            if not collapse_ws(progress.draft_llm_rephrase_review_item_id):
                return False
            return self._open_follow_up_in_chat(
                prompt=self._draft_detail_chat_prompt(),
                started_text="Started a draft-item rephrase in Chat. Reply with [label] and [text] sections only.",
            )

        def _open_review_scope_detail_in_chat(self) -> bool:
            if self._state.is_busy():
                return False
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="review",
                action_key="start_review_section_llm_rephrase",
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self.request_state_refresh()
            if not collapse_ws(progress.review_section_llm_rephrase_section_id):
                return False
            return self._open_follow_up_in_chat(
                prompt=self._review_scope_detail_chat_prompt(),
                started_text="Started a report-section brief in Chat. Reply with [label] and [text] sections only.",
            )

        def _sync_pending_research_capture_state(self) -> None:
            progress = self._mock_subject_progress()
            if self._subject_projection_backend.has_pending_research_capture(progress):
                self._state.begin_research_capture(
                    _PendingResearchCapture(
                        markdown_text="",
                        command_text="",
                        subject_title_override="",
                        preview_report={
                            "canonical_title": self._subject_projection_backend.pending_research_capture_target(progress),
                        },
                    )
                )
                return
            self._state.clear_pending_research_capture()

        def _latest_assistant_research_capture_text(self) -> str:
            for entry in reversed(self._state.transcript_entries_snapshot()):
                if collapse_ws(str(entry.label)).casefold() == "assistant":
                    return str(entry.text or "").strip()
            return ""

        def _handle_start_research_command(self) -> bool:
            return self._handle_start_research_command_with_override("")

        def _handle_start_research_command_with_override(self, subject_title_override: str, *, prompt_text: str = "") -> bool:
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="research",
                action_key="stage_assistant_capture",
                assistant_message_text=self._latest_assistant_research_capture_text(),
                subject_title_override=subject_title_override,
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self._sync_pending_research_capture_state()
            self.request_state_refresh()
            if progress.latest_receipt_lines:
                self._record_shell_status_turn(
                    prompt_text=prompt_text,
                    shell_text="\n".join(
                        [
                            result.status_text,
                            *progress.latest_receipt_lines,
                            "",
                            "Reply yes to stage, no to cancel, or use /start-research-into <subject title> to choose another subject.",
                        ]
                    ).rstrip(),
                )
            elif result.status_text:
                self._record_shell_status_turn(prompt_text=prompt_text, shell_text=result.status_text)
            return True

        def _confirm_pending_research_capture(self, *, prompt_text: str = "") -> bool:
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="research",
                action_key="confirm_assistant_capture",
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self._sync_pending_research_capture_state()
            if result.reload_subjects:
                self._state.refresh_context()
            else:
                self.request_state_refresh()
            if result.status_text:
                receipt_lines = (
                    progress.latest_receipt_lines
                    if not self._subject_projection_backend.has_pending_research_capture(progress)
                    else []
                )
                if receipt_lines:
                    self._record_shell_status_turn(
                        prompt_text=prompt_text,
                        shell_text="\n".join([result.status_text, *receipt_lines]).rstrip(),
                    )
                else:
                    self._record_shell_status_turn(prompt_text=prompt_text, shell_text=result.status_text)
            if result.next_phase in MOCK_SUBJECT_PHASES:
                self._set_subject_phase(str(result.next_phase))
            elif collapse_ws(str(result.next_tab or "")).casefold() == "chat":
                self._set_active_tab("chat_tab")
            return True

        def _cancel_pending_research_capture(self, *, prompt_text: str = "") -> bool:
            scenario = self._mock_subject_scenario()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase="research",
                action_key="cancel_assistant_capture",
            )
            self._refresh_subject_progress_after_api_action(scenario, result)
            self._mock_subject_status_text = result.status_text
            self._sync_pending_research_capture_state()
            self.request_state_refresh()
            if result.status_text:
                self._record_shell_status_turn(prompt_text=prompt_text, shell_text=result.status_text)
            return True

        def _step_mock_subject(self, delta: int) -> None:
            if not self._mock_subject_scenarios:
                return
            total = len(self._mock_subject_scenarios)
            self._mock_subject_index = (self._mock_subject_index + int(delta)) % total
            self._mock_subject_status_text = f"Selected subject: {self._mock_subject_scenario().title}."
            if self._active_tab_id() in _SUBJECT_TAB_ID_TO_PHASE:
                self._refresh_current_subject_phase_projection()
            else:
                self.request_state_refresh()

        def _subject_action_runs_in_background(self, action_key: str) -> bool:
            normalized = collapse_ws(str(action_key or "")).casefold()
            return normalized in {"build_report", "suggest_transformation_constructs"}

        def _apply_mock_subject_action_result(
            self,
            phase: str,
            scenario: MockSubjectScenario,
            progress: MockSubjectProgress,
            action_key: str,
            result: Any,
        ) -> None:
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            open_failures: list[str] = []
            for open_path in getattr(result, "open_paths", ()) or ():
                if not desktop_open_path(Path(str(open_path))):
                    open_failures.append(str(open_path))
            self._mock_subject_status_text = result.status_text
            self._sync_pending_research_capture_state()
            if open_failures:
                self._mock_subject_status_text = (
                    f"{self._mock_subject_status_text} Unable to open: {', '.join(open_failures)}"
                )
            if collapse_ws(str(result.next_tab or "")).casefold() == "chat" and result.status_text:
                self._record_shell_status_turn(shell_text=result.status_text)
            target_phase = collapse_ws(str(result.next_phase or "")).casefold()
            target_tab = collapse_ws(str(result.next_tab or "")).casefold()
            current_phase = collapse_ws(str(phase or "")).casefold() or self._subject_phase_for_tab_id()
            current_tab = self._active_tab_id()
            guided_phase = self._guided_subject_phase_from_action_result(current_phase, result)
            if self._should_surface_subject_result_pane(current_phase, action_key, progress):
                self._show_maximized_pane_by_id(_subject_journal_pane_id(current_phase))
            if target_phase in MOCK_SUBJECT_PHASES:
                if target_phase == current_phase:
                    self._refresh_current_subject_phase_projection()
                else:
                    self._set_subject_phase(target_phase)
                    self._schedule_focus_subject_primary_gate_action_for_phase(target_phase)
            elif target_tab == "chat":
                if current_tab == "chat_tab":
                    self.request_state_refresh()
                else:
                    self._set_active_tab("chat_tab")
            else:
                if guided_phase in MOCK_SUBJECT_PHASES and guided_phase != current_phase:
                    self._set_subject_phase(guided_phase)
                    self._schedule_focus_subject_primary_gate_action_for_phase(guided_phase)
                    return
                current_phase_tab_id = _SUBJECT_PHASE_TO_TAB_ID.get(current_phase)
                if current_phase_tab_id and current_tab != current_phase_tab_id:
                    self._set_subject_phase(current_phase)
                    return
                self._refresh_current_subject_phase_projection()

        def _apply_mock_subject_action_worker(
            self,
            phase: str,
            scenario: MockSubjectScenario,
            progress: MockSubjectProgress,
            action_key: str,
            assistant_message_text: str,
            projection_kwargs: dict[str, Any],
        ) -> None:
            try:
                if (
                    not self._subject_projection_backend.uses_in_process_service()
                    and not getattr(scenario, "is_placeholder", False)
                    and collapse_ws(getattr(scenario, "subject_id", ""))
                ):
                    self._subject_projection_backend.persist_progress(
                        root_path=self._root,
                        subject_id=collapse_ws(getattr(scenario, "subject_id", "")),
                        progress=progress,
                    )
                result = self._subject_projection_backend.apply_action(
                    root_path=self._root,
                    subject_id=collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", "")),
                    action_key=action_key,
                    phase=phase,
                    progress=progress,
                    assistant_message_text=assistant_message_text,
                    **projection_kwargs,
                )
                self.call_from_thread(self._apply_mock_subject_action_result, phase, scenario, progress, action_key, result)
            except Exception as exc:
                message = f"{collapse_ws(str(action_key or '')).replace('_', ' ').title()} failed: {exc}"
                self.call_from_thread(setattr, self, "_mock_subject_status_text", message)
                self.call_from_thread(self.request_state_refresh)
            finally:
                self.call_from_thread(self._state.finish_turn)

        def _start_subject_action_thread(
            self,
            phase: str,
            scenario: MockSubjectScenario,
            progress: MockSubjectProgress,
            action_key: str,
        ) -> None:
            self._start_app_worker(
                target=self._apply_mock_subject_action_worker,
                args=(
                    phase,
                    scenario,
                    progress,
                    action_key,
                    self._latest_assistant_research_capture_text(),
                    self._subject_phase_projection_kwargs(),
                ),
                name=f"subject-action-{collapse_ws(action_key) or 'unknown'}",
            )

        def _apply_mock_subject_action(self, phase: str, action_key: str) -> None:
            if collapse_ws(str(action_key or "")).casefold() == "use_markdown_ingress":
                self._start_learn_markdown_ingress()
                return
            if collapse_ws(str(action_key or "")).casefold() == "start_research_source_collection_discovery":
                self._open_research_source_discovery_in_chat()
                return
            if collapse_ws(str(action_key or "")).casefold() == "start_research_source_collection_merge_back":
                self._open_research_source_collection_merge_back_in_chat()
                return
            if collapse_ws(str(action_key or "")).casefold() == "start_research_source_collection_source_merge_back":
                self._open_research_source_collection_source_merge_back_in_chat()
                return
            if collapse_ws(str(action_key or "")).casefold() == "start_research_source_merge_back":
                self._open_research_source_merge_back_in_chat()
                return
            if self._subject_action_runs_in_background(action_key):
                if self._state.is_busy():
                    return
                scenario = self._mock_subject_scenario()
                progress = self._mock_subject_progress()
                self._mock_subject_status_text = (
                    "Building report publication in the background. The UI should remain responsive."
                    if collapse_ws(str(action_key or "")).casefold() == "build_report"
                    else "Suggesting transformation constructs in the background. The UI should remain responsive."
                    if collapse_ws(str(action_key or "")).casefold() == "suggest_transformation_constructs"
                    else f"Running {collapse_ws(str(action_key or '')).replace('_', ' ')} in the background."
                )
                self._state.start_turn()
                self.request_state_refresh()
                self._start_subject_action_thread(phase, scenario, progress, action_key)
                return
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            result = self._invoke_subject_workflow_action(
                scenario=scenario,
                phase=phase,
                action_key=action_key,
                assistant_message_text=self._latest_assistant_research_capture_text(),
            )
            progress = self._refresh_subject_progress_after_api_action(scenario, result)
            if self._should_use_local_review_scope_refresh(phase, action_key, result):
                self._mock_subject_status_text = result.status_text
                self._sync_pending_research_capture_state()
                if self._should_surface_subject_result_pane(phase, action_key, progress):
                    self._show_maximized_pane_by_id(_subject_journal_pane_id(phase))
                self._refresh_report_scope_live_panels(collapse_ws(str(phase or "")).casefold())
                self._refresh_report_scope_control_widgets(collapse_ws(str(phase or "")).casefold())
                return
            if self._should_use_local_draft_refresh(phase, action_key, result):
                self._mock_subject_status_text = result.status_text
                self._sync_pending_research_capture_state()
                self._refresh_draft_live_panels()
                return
            self._apply_mock_subject_action_result(phase, scenario, progress, action_key, result)

        def _apply_active_tab_state(self) -> None:  # pragma: no cover - requires textual runtime
            active = self._active_tab_id()
            for index, tab_id in enumerate(self._tab_ids(), start=1):
                pane = self.query_one(f"#{tab_id}", Vertical)
                pane.display = tab_id == active
                button = self.query_one(f"#tab_button_{tab_id}", TextualButton)
                title = self._tab_title(tab_id)
                if tab_id == active:
                    button.add_class("tab_button_active")
                    button.label = f"● {index}. {title}"
                else:
                    button.remove_class("tab_button_active")
                    button.label = f"  {index}. {title}"
            self._refresh_root_tabs_border_title()
            self._apply_tab_pane_maximize_state()
            self._refresh_info_pane()
            self._refresh_pane_info_buttons()
            self._ensure_subject_workflow_watch()

        def append_activity_line_ui(self, text: str) -> None:
            try:
                self.call_from_thread(self._append_activity_line_ui, text)
            except Exception:
                try:
                    self._append_activity_line_ui(text)
                except Exception:
                    pass

        def append_transcript_block_ui(self, text: str) -> None:
            try:
                self.call_from_thread(self._append_transcript_block_ui, text)
            except Exception:
                try:
                    self._append_transcript_block_ui(text)
                except Exception:
                    pass

        def _refresh_from_state(self, *, clear_subject_snapshot_cache: bool = False) -> None:  # pragma: no cover - requires textual runtime
            self.query_one("#chat_status_panel", TextualStatic).update(_textual_status_text(self._state))
            self.query_one("#prompt_label", TextualStatic).update(_textual_prompt_label_text(self._state))
            self._refresh_inline_hint()
            self._refresh_prompt_suggestions()
            self._invalidate_research_snapshot_if_projection_inputs_changed()
            if clear_subject_snapshot_cache:
                self._subject_snapshot_cache = {}
            self._ensure_subject_workflow_watch()
            self._refresh_mock_subject_controls()
            self._schedule_active_tab_refresh()
            self._apply_tab_pane_maximize_state()
            self._refresh_info_pane()
            self._refresh_pane_info_buttons()
            self._refresh_chat_activity_panel()

        def _refresh_mock_subject_controls(self) -> None:  # pragma: no cover - requires textual runtime
            for header_id in (
                "#subject_flow_header",
                "#itemize_flow_header",
                "#draft_flow_header",
                "#review_flow_header",
                "#publication_flow_header",
            ):
                try:
                    header = self.query_one(header_id, TextualStatic)
                except Exception:
                    continue
                header.update("")
                header.display = False
            for phase in ("research", "itemize", "draft", "review", "publication"):
                try:
                    title_widget = self.query_one(f"#{_subject_header_subject_id(phase)}", TextualStatic)
                except Exception:
                    continue
                title_widget.update("")
                title_widget.display = False
            self._refresh_root_tabs_border_title()
            active_phase = _SUBJECT_TAB_ID_TO_PHASE.get(self._active_tab_id())
            if active_phase in MOCK_SUBJECT_PHASES:
                self._refresh_subject_phase_action_row(active_phase)
            self.query_one("#learn_markdown_button", TextualButton).disabled = self._state.is_busy()
            self.query_one("#learn_url_button", TextualButton).disabled = self._state.is_busy()
            self.query_one("#export_learned_button", TextualButton).disabled = (
                not self._current_learned_bundle_payload() or self._markdown_busy
            )
            if active_phase == "research":
                self._refresh_research_source_collection_select()
                self._refresh_research_source_revision_baseline_select()
                self._refresh_research_source_collection_membership_switch()
                self._set_pane_header_title("subject_sources_panel", self._mock_subject_research_sources_title())
                self._set_pane_header_title("subject_target_panel", self._mock_subject_research_target_title())
                self._set_pane_header_title("learn_result", self._mock_subject_workspace_title("research"))
                self._refresh_research_detail_buttons()
            elif active_phase == "itemize":
                self._refresh_itemize_decision_role_select()
                self._refresh_itemize_hold_switch()
                self._set_pane_header_title("itemize_detail_panel", self._mock_subject_itemize_detail_title())
                self._set_pane_header_title("itemize_result", self._mock_subject_workspace_title("itemize"))
                self._refresh_itemize_detail_buttons()
            elif active_phase == "draft":
                self._refresh_draft_decision_included_switch()
                self._refresh_draft_semantic_kind_select()
                self._refresh_draft_render_kind_select()
                self._refresh_draft_evidence_mode_select()
                self._refresh_draft_transform_mode_select()
                self._refresh_draft_model_construct_sort_select()
                self._refresh_draft_model_construct_lane_select()
                self._refresh_draft_model_transition_selects()
                self._refresh_draft_model_policy_profile_select()
                self._refresh_draft_model_lens_tabs()
                self._refresh_draft_model_relation_selection_lists()
                self._set_pane_header_title("draft_scope_tree_panel", self._mock_subject_draft_tree_title())
                self._set_pane_header_title("draft_model_main_panel", self._mock_subject_draft_model_main_title())
                self._set_pane_header_title("draft_scope_detail_panel", self._mock_subject_draft_detail_title())
                self._set_pane_header_title("draft_result", self._mock_subject_draft_result_title())
                self._refresh_draft_detail_buttons()
            elif active_phase == "review":
                self._refresh_review_publication_output_mode_select()
                self._refresh_review_publication_section_plan_select()
                self._refresh_review_publication_diff_baseline_select()
                self._refresh_review_composition_unit_target_select()
                self._refresh_review_composition_unit_included_switch()
                self._refresh_review_publication_section_target_select()
                self._refresh_review_publication_section_included_switch()
                self._refresh_review_comparison_history_table()
                self._refresh_review_latest_receipt_table()
                self._set_pane_header_title("review_scope_detail_panel", self._mock_subject_review_scope_detail_title())
                self._set_pane_header_title("review_result", self._mock_subject_workspace_title("review"))
                self._refresh_review_scope_tree_widget()
                self._refresh_review_detail_buttons()
            elif active_phase == "publication":
                self._refresh_publication_output_mode_select()
                self._refresh_publication_section_plan_select()
                self._refresh_publication_diff_baseline_select()
                self._refresh_publication_import_target_select()
                self._refresh_publication_composition_unit_target_select()
                self._refresh_publication_composition_unit_included_switch()
                self._refresh_publication_section_target_select()
                self._refresh_publication_section_included_switch()
                self._refresh_publication_import_included_switch()
                self._refresh_publication_import_usage_select()
                self._refresh_publication_build_artifacts_table()
                self._refresh_publication_build_receipt_table()
                self._refresh_publication_latest_receipt_table()
                self._set_pane_header_title("publication_result", self._mock_subject_workspace_title("publication"))
            self._refresh_subject_journal_buttons()
            self._refresh_subject_hidden_pane_buttons()
            self._refresh_pane_info_buttons()
            self._set_widget_display("draft_choice_group", not self._draft_model_mode_active())
            self._set_widget_display("draft_choice_row", not self._draft_model_mode_active())
            self._set_widget_display("draft_model_construct_group", self._draft_model_mode_active())
            self._set_widget_display("draft_model_choice_row", self._draft_model_mode_active())

        def _refresh_subject_phase_action_row(self, phase: str) -> None:
            action_specs = self._mock_subject_control_specs(phase)
            draft_duplicate_compose_keys = {
                "cycle_selected_draft_review_semantic_kind",
                "cycle_selected_draft_review_render_kind",
                "cycle_selected_draft_review_evidence_mode",
                "cycle_selected_draft_review_transform_mode",
            }
            show_draft_more_actions = True
            if phase == "draft":
                visible_action_keys = {
                    collapse_ws(spec.key)
                    for spec in action_specs
                    if collapse_ws(spec.key) and bool(spec.enabled)
                }
                if visible_action_keys and visible_action_keys.issubset(draft_duplicate_compose_keys):
                    show_draft_more_actions = False
            visible_phase_actions = False
            for index, button_id in enumerate(_subject_action_button_ids(phase)):
                try:
                    button = self.query_one(f"#{button_id}", TextualButton)
                except Exception:
                    continue
                if phase == "draft" and not show_draft_more_actions:
                    button.label = ""
                    button.disabled = True
                    button.display = False
                    continue
                if index < len(action_specs):
                    spec = action_specs[index]
                    if (
                        phase == "draft"
                        and self._draft_model_mode_active()
                        and collapse_ws(spec.key) in {
                            "open_draft_model_frame_view",
                            "open_draft_model_model_view",
                            "open_draft_model_explore_view",
                        }
                    ):
                        button.label = ""
                        button.disabled = True
                        button.display = False
                        continue
                    button.label = spec.label
                    button.disabled = not spec.enabled
                    button.display = bool(collapse_ws(spec.label))
                    visible_phase_actions = visible_phase_actions or button.display
                else:
                    button.label = ""
                    button.disabled = True
                    button.display = False
            row_visible = visible_phase_actions
            if phase == "research":
                row_visible = True
            if phase == "draft" and not show_draft_more_actions:
                row_visible = False
            self._set_widget_display(_subject_phase_action_row_id(phase), row_visible)

        def _refresh_root_tabs_border_title(self) -> None:
            root_tabs = self.query_one("#root_tabs", Vertical)
            active = collapse_ws(self._active_tab_id())
            if active in {"learn_tab", "itemize_tab", "draft_tab", "review_tab", "publication_tab"}:
                title = collapse_ws(self._mock_subject_header_subject_text())
                root_tabs.border_title = _textual_bold_border_title(title) if title else ""
                return
            root_tabs.border_title = ""

        def _refresh_inline_hint(self) -> None:  # pragma: no cover - requires textual runtime
            input_widget = self.query_one("#input", TextualInput)
            current_value = str(getattr(input_widget, "value", "") or "")
            completion = self.resolve_inline_completion(current_value)
            hint_widget = self.query_one("#inline_hint", TextualStatic)
            if completion and completion.casefold().startswith(current_value.casefold()):
                suffix = completion[len(current_value) :]
                normalized_suffix = str(suffix or "")
                if normalized_suffix and "\n" not in normalized_suffix and len(normalized_suffix) <= 24:
                    hint_widget.display = True
                    hint_widget.update(normalized_suffix)
                else:
                    hint_widget.display = False
                    hint_widget.update("")
            else:
                hint_widget.display = False
                hint_widget.update("")

        def _append_activity_line_ui(self, text: str) -> None:  # pragma: no cover - requires textual runtime
            self._refresh_chat_activity_panel()
            if self._active_tab_id() != "activity_tab":
                return
            self._schedule_active_tab_refresh()

        def _append_transcript_block_ui(self, text: str) -> None:  # pragma: no cover - requires textual runtime
            if self._active_tab_id() != "chat_tab":
                return
            try:
                widget = self.query_one("#transcript", TextualRichLog)
                entries = self._state.transcript_entries_snapshot()
                if entries:
                    if len(entries) == 1:
                        try:
                            widget.clear()
                        except Exception:
                            pass
                    elif getattr(widget, "lines", None):
                        widget.write("")
                    wrap_width = self._tab_content_wrap_width("chat_tab")
                    for renderable in _render_transcript_entry_rich(entries[-1], width=wrap_width):
                        widget.write(renderable, width=wrap_width)
            except Exception:
                pass
            self._schedule_active_tab_refresh()
            self._schedule_transcript_scroll_to_end()

        def _record_shell_status_turn(self, *, prompt_text: str = "", shell_text: str) -> None:
            self._state.record_shell_message(text=shell_text, prompt_text=prompt_text)
            self._schedule_transcript_scroll_to_end()

        def _replace_log_text(self, widget: Any, text: str) -> None:  # pragma: no cover - requires textual runtime
            widget_id = str(getattr(widget, "id", "") or "")
            if widget_id in {"activity", "permissions", "skills", "learn_result", "suggestion_bar"}:
                wrap_width = self._textual_log_wrap_width(widget)
                rendered_lines = _wrap_textual_log_lines(text, width=wrap_width)
            else:
                rendered_lines = [_plain_ui_text(line) for line in str(text or "").splitlines() or [""]]
            self._replace_log_lines(widget, rendered_lines)

        def _replace_log_lines(self, widget: Any, lines: Iterable[str]) -> None:  # pragma: no cover - requires textual runtime
            widget_id = str(getattr(widget, "id", "") or "")
            rendered_lines = self._deduplicate_pane_leading_title(widget_id, lines)
            self._rendered_log_lines[widget_id] = tuple(str(line or "") for line in rendered_lines)
            if widget_id == "subject_sources_panel":
                self._refresh_research_sources_tree_widget(widget_id)
                return
            if widget_id == "draft_scope_tree_panel" and TextualDataTable is not None and isinstance(widget, _FocusableTextualDataTable):
                self._apply_draft_scope_table_lines(widget=widget, lines=rendered_lines)
                self._sync_draft_scope_table_cursor_from_progress()
                return
            if widget_id in _TEXTUAL_STRUCTURED_TABLE_IDS and TextualDataTable is not None:
                pane_spec = _STRUCTURED_PANE_BUNDLE_KEYS.get(widget_id)
                if pane_spec is not None:
                    phase, pane_key = pane_spec
                    try:
                        if self._mock_subject_pane_is_structured_table(phase, pane_key):
                            self._apply_structured_table_rows(
                                widget=widget,
                                rows=self._mock_subject_pane_rows(phase, pane_key),
                            )
                            return
                    except Exception:
                        pass
                self._apply_structured_table_lines(widget=widget, lines=rendered_lines)
                return
            if isinstance(widget, _FocusableTextualOptionList):
                self._inventory_option_sync_suppressed.add(widget_id)
                try:
                    widget.set_rendered_lines(rendered_lines)
                finally:
                    self._inventory_option_sync_suppressed.discard(widget_id)
                return
            try:
                widget.clear()
            except Exception:
                pass
            for line in rendered_lines:
                widget.write_line(line)

        def _replace_rich_log_renderables(self, widget: Any, renderables: Iterable[Any]) -> None:  # pragma: no cover - requires textual runtime
            try:
                widget.clear()
            except Exception:
                pass
            for renderable in renderables:
                widget.write(renderable)

        def _schedule_active_tab_refresh(self) -> None:  # pragma: no cover - requires textual runtime
            active_tab_id = self._active_tab_id()
            self._tab_refresh_request_id += 1
            request_id = self._tab_refresh_request_id
            if self._tab_refresh_worker_active:
                return
            self._start_active_tab_refresh_worker(
                tab_id=active_tab_id,
                request_id=request_id,
            )

        def _invalidate_active_tab_refresh_payloads(
            self,
            *,
            tab_id: str | None = None,
        ) -> None:  # pragma: no cover - requires textual runtime
            active_tab_id = self._active_tab_id()
            if tab_id is not None and collapse_ws(str(tab_id or "")) != collapse_ws(active_tab_id):
                return
            self._tab_refresh_request_id += 1
            self._tab_refresh_worker_request_id = self._tab_refresh_request_id

        def _start_active_tab_refresh_worker(
            self,
            *,
            tab_id: str,
            request_id: int,
        ) -> None:  # pragma: no cover - requires textual runtime
            wrap_width = self._tab_content_wrap_width(tab_id)
            pane_wrap_widths = self._subject_phase_panel_wrap_widths(tab_id)
            self._tab_refresh_worker_active = True
            self._tab_refresh_worker_request_id = int(request_id)
            self.run_worker(
                lambda: self._compute_tab_content_payload(
                    tab_id=tab_id,
                    request_id=request_id,
                    wrap_width=wrap_width,
                    pane_wrap_widths=pane_wrap_widths,
                ),
                name=f"refresh-{tab_id}",
                group="textual-tab-content",
                description=f"Refresh {tab_id}",
                exit_on_error=False,
                exclusive=True,
                thread=True,
            )

        def _tab_content_wrap_width(self, tab_id: str) -> int:  # pragma: no cover - requires textual runtime
            widget_id = {
                "chat_tab": "#transcript",
                "activity_tab": "#activity",
                "learn_tab": "#learn_result",
                "itemize_tab": "#itemize_result",
                "draft_tab": "#draft_result",
                "review_tab": "#review_result",
                "publication_tab": "#publication_result",
                "permissions_tab": "#permissions",
                "skills_tab": "#skills",
            }.get(tab_id)
            if not widget_id:
                return 80
            try:
                return self._textual_log_wrap_width(self.query_one(widget_id))
            except Exception:
                return 80

        def _subject_phase_panel_wrap_widths(self, tab_id: str) -> dict[str, int]:  # pragma: no cover - requires textual runtime
            panel_ids_by_tab = {
                "learn_tab": (
                    "#subject_sources_panel",
                    "#subject_observation_panel",
                    "#subject_target_panel",
                ),
                "itemize_tab": (
                    "#itemize_inventory_panel",
                    "#itemize_detail_panel",
                    "#itemize_target_panel",
                ),
                "draft_tab": (
                    "#draft_scope_tree_panel",
                    "#draft_model_main_panel",
                    "#draft_scope_detail_panel",
                ),
                "review_tab": (
                    "#review_scope_tree_panel",
                    "#review_scope_detail_panel",
                ),
            }
            panel_ids = panel_ids_by_tab.get(tab_id, ())
            widths: dict[str, int] = {}
            for panel_id in panel_ids:
                try:
                    panel = self.query_one(panel_id)
                except Exception:
                    continue
                panel_width = int(getattr(getattr(panel, "size", None), "width", 0) or 0)
                if panel_width > 16:
                    widths[panel_id] = max(panel_width - 2, 16)
            if widths:
                return widths
            if tab_id == "learn_tab":
                fallback_width = max(self._tab_content_wrap_width("learn_tab") // 3 - 2, 16)
            elif tab_id == "itemize_tab":
                fallback_width = max(self._tab_content_wrap_width("itemize_tab") // 3 - 2, 16)
            elif tab_id == "draft_tab":
                fallback_width = max(self._tab_content_wrap_width("draft_tab") // 2 - 2, 16)
            elif tab_id == "review_tab":
                fallback_width = max(self._tab_content_wrap_width("review_tab") // 2 - 2, 16)
            else:
                fallback_width = max(self._tab_content_wrap_width(tab_id) - 2, 16)
            return {panel_id: fallback_width for panel_id in panel_ids}

        def _compute_tab_content_payload(
            self,
            *,
            tab_id: str,
            request_id: int,
            wrap_width: int,
            pane_wrap_widths: dict[str, int] | None = None,
        ) -> None:
            payload: _TextualTabContentPayload | None = None
            try:
                if tab_id == "chat_tab":
                    payload = _TextualTabContentPayload(
                        tab_id=tab_id,
                        request_id=request_id,
                        wrap_width=wrap_width,
                        transcript_blocks=tuple(
                            tuple(_render_transcript_entry_rich(entry, width=wrap_width))
                            for entry in self._state.transcript_entries_snapshot()
                        ),
                    )
                elif tab_id == "activity_tab":
                    payload = _TextualTabContentPayload(
                        tab_id=tab_id,
                        request_id=request_id,
                        wrap_width=wrap_width,
                        renderables=tuple(
                            _render_activity_rich_line(item)
                            for item in (self._state.activity_text().splitlines() or ["No activity yet."])
                        ),
                    )
                elif tab_id in {"learn_tab", "itemize_tab", "draft_tab", "review_tab", "publication_tab"}:
                    phase = self._subject_phase_for_tab_id(tab_id)
                    phase_view = self._mock_subject_phase_view(phase)
                    normalized_pane_wrap_widths = {
                        str(panel_id): max(int(width or 0), 16)
                        for panel_id, width in (pane_wrap_widths or {}).items()
                    }
                    payload = _TextualTabContentPayload(
                        tab_id=tab_id,
                        request_id=request_id,
                        wrap_width=wrap_width,
                        learn_status_text=self._render_subject_status_view_text(phase_view),
                        learn_ingress_text=(
                            self._learn_markdown_ingress_text()
                            if phase == "research"
                            else ""
                        ),
                        last_action_text=self._mock_subject_last_action_text(),
                        current_step_text=self._render_subject_current_step_view_text(phase_view),
                        journey_text=self._mock_subject_journey_text(phase),
                        current_step_actions=self._subject_gate_actions_from_phase_view(phase_view),
                        subject_sources_lines=tuple(
                            str(self._mock_subject_research_sources_text() or "").splitlines()
                            if phase == "research"
                            else ()
                        ),
                        subject_observation_lines=tuple(
                            str(self._mock_subject_research_observation_text() or "").splitlines()
                            if phase == "research"
                            else ()
                        ),
                        subject_target_lines=tuple(
                            str(self._mock_subject_research_target_text() or "").splitlines()
                            if phase == "research"
                            else ()
                        ),
                        itemize_inventory_lines=tuple(
                            _wrap_textual_log_lines(
                                self._mock_subject_itemize_inventory_text(),
                                width=normalized_pane_wrap_widths.get("#itemize_inventory_panel", 16),
                            )
                            if phase == "itemize"
                            else ()
                        ),
                        itemize_inventory_items=(
                            self._mock_subject_pane_items("itemize", "itemize_inventory")
                            if phase == "itemize"
                            else ()
                        ),
                        itemize_detail_lines=tuple(
                            str(self._mock_subject_itemize_detail_text() or "").splitlines()
                            if phase == "itemize"
                            else ()
                        ),
                        itemize_detail_title=(
                            self._mock_subject_itemize_detail_title()
                            if phase == "itemize"
                            else ""
                        ),
                        itemize_target_lines=tuple(
                            str(self._mock_subject_itemize_target_text() or "").splitlines()
                            if phase == "itemize"
                            else ()
                        ),
                        review_scope_lines=tuple(
                            _wrap_textual_log_lines(
                                (
                                    self._mock_subject_draft_scope_tree_text()
                                    if phase == "draft"
                                    else ""
                                ),
                                width=normalized_pane_wrap_widths.get(
                                    "#draft_scope_tree_panel" if phase == "draft" else "#review_scope_tree_panel",
                                    16,
                                ),
                            )
                            if phase in {"draft", "review"}
                            else ()
                        ),
                        draft_model_main_lines=tuple(
                            str(self._mock_subject_draft_model_main_text() or "").splitlines()
                            if phase == "draft"
                            else ()
                        ),
                        review_scope_detail_lines=tuple(
                            str(
                                self._mock_subject_draft_detail_text()
                                if phase == "draft"
                                else self._mock_subject_review_scope_detail_text()
                            ).splitlines()
                            if phase in {"draft", "review"}
                            else ()
                        ),
                        review_scope_detail_title=(
                            (
                                self._mock_subject_draft_detail_title()
                                if phase == "draft"
                                else self._mock_subject_review_scope_detail_title()
                            )
                            if phase in {"draft", "review"} else ""
                        ),
                        draft_model_main_title=(
                            self._mock_subject_draft_model_main_title()
                            if phase == "draft"
                            else ""
                        ),
                        learn_result_title=(
                            self._mock_subject_draft_result_title()
                            if phase == "draft"
                            else self._mock_subject_workspace_title(phase)
                        ),
                        log_lines=tuple(
                            _wrap_textual_log_lines(
                                self._mock_subject_draft_issue_tray_text()
                                if phase == "draft"
                                else self._render_subject_workspace_view_text(phase_view),
                                width=wrap_width,
                            )
                        ),
                    )
                elif tab_id == "permissions_tab":
                    payload = _TextualTabContentPayload(
                        tab_id=tab_id,
                        request_id=request_id,
                        wrap_width=wrap_width,
                        renderables=_render_permissions_rich_lines(self._permissions_text()),
                    )
                elif tab_id == "skills_tab":
                    payload = _TextualTabContentPayload(
                        tab_id=tab_id,
                        request_id=request_id,
                        wrap_width=wrap_width,
                        renderables=_render_skills_rich_lines(self._skills_text()),
                    )
            except Exception as exc:
                payload = _TextualTabContentPayload(
                    tab_id=tab_id,
                    request_id=request_id,
                    wrap_width=wrap_width,
                    log_lines=(f"Unable to refresh tab content: {exc}",),
                )
            if payload is None:
                return
            try:
                self.call_from_thread(self._apply_tab_content_payload, payload)
            except Exception:
                pass

        def _apply_tab_content_payload(self, payload: _TextualTabContentPayload) -> None:  # pragma: no cover - requires textual runtime
            self._tab_refresh_worker_active = False
            if payload.request_id != self._tab_refresh_request_id:
                self._schedule_latest_active_tab_refresh_if_needed()
                return
            if payload.tab_id != self._active_tab_id():
                self._schedule_latest_active_tab_refresh_if_needed()
                return
            try:
                if payload.tab_id == "chat_tab":
                    widget = self.query_one("#transcript", TextualRichLog)
                    try:
                        widget.clear()
                    except Exception:
                        pass
                    if not payload.transcript_blocks:
                        widget.write("No conversation yet.")
                        return
                    for index, block in enumerate(payload.transcript_blocks):
                        for renderable in block:
                            widget.write(renderable, width=payload.wrap_width)
                        if index < len(payload.transcript_blocks) - 1:
                            widget.write("")
                    self._schedule_transcript_scroll_to_end()
                    return
                if payload.tab_id == "activity_tab":
                    self._replace_rich_log_renderables(self.query_one("#activity", TextualRichLog), payload.renderables)
                    return
                if payload.tab_id == "learn_tab":
                    ingress_panel = self.query_one("#learn_ingress_panel", TextualStatic)
                    if collapse_ws(payload.learn_ingress_text):
                        ingress_panel.display = True
                        ingress_panel.update(payload.learn_ingress_text)
                    else:
                        ingress_panel.update("")
                        ingress_panel.display = False
                    self._set_widget_display(
                        _subject_controls_header_row_id("research"),
                        bool(collapse_ws(payload.learn_ingress_text)),
                    )
                    self._apply_subject_gate_panel(
                        phase="research",
                        gate="review",
                        summary_text=_subject_current_step_text_with_last_action(
                            payload.current_step_text,
                            payload.last_action_text,
                        ),
                        actions=payload.current_step_actions,
                    )
                    self._apply_subject_secondary_gate_panel(
                        phase="research",
                        summary_text=payload.learn_status_text,
                    )
                    self._set_pane_header_title("subject_sources_panel", self._mock_subject_research_sources_title())
                    self._set_pane_header_title("subject_target_panel", self._mock_subject_research_target_title())
                    if payload.learn_result_title:
                        self._set_pane_header_title("learn_result", payload.learn_result_title)
                    self._replace_log_lines(self.query_one("#subject_sources_panel"), payload.subject_sources_lines)
                    self._replace_log_lines(self.query_one("#subject_observation_panel"), payload.subject_observation_lines)
                    self._replace_log_lines(self.query_one("#subject_target_panel"), payload.subject_target_lines)
                    self._refresh_research_source_revision_history_table()
                    self._refresh_research_source_change_summary_table()
                    self._refresh_research_source_collection_member_export_status_table()
                    self._refresh_research_source_collection_member_revision_table()
                    self._refresh_research_source_collection_merge_export_history_table()
                    self._refresh_research_source_collection_actionable_export_table()
                    self._refresh_research_source_collection_export_applied_table()
                    self._replace_log_lines(self.query_one("#learn_result", TextualLog), payload.log_lines)
                    return
                if payload.tab_id == "itemize_tab":
                    self._set_widget_display(_subject_controls_header_row_id("itemize"), False)
                    self._apply_subject_gate_panel(
                        phase="itemize",
                        gate="review",
                        summary_text=_subject_current_step_text_with_last_action(
                            payload.current_step_text,
                            payload.last_action_text,
                        ),
                        actions=payload.current_step_actions,
                    )
                    self._apply_subject_secondary_gate_panel(
                        phase="itemize",
                        summary_text=payload.learn_status_text,
                    )
                    self._set_pane_header_title("itemize_inventory_panel", "Item Inventory")
                    if payload.itemize_detail_title:
                        self._set_pane_header_title("itemize_detail_panel", payload.itemize_detail_title)
                    self._set_pane_header_title("itemize_target_panel", "Draft Handoff")
                    if payload.learn_result_title:
                        self._set_pane_header_title("itemize_result", payload.learn_result_title)
                    itemize_inventory = self.query_one("#itemize_inventory_panel")
                    if (
                        isinstance(itemize_inventory, _FocusableTextualOptionList)
                        and payload.itemize_inventory_items
                    ):
                        self._inventory_option_sync_suppressed.add("itemize_inventory_panel")
                        try:
                            itemize_inventory.set_inventory_items(payload.itemize_inventory_items)
                            self._rendered_log_lines["itemize_inventory_panel"] = tuple(
                                itemize_inventory.lines
                            )
                        finally:
                            self._inventory_option_sync_suppressed.discard(
                                "itemize_inventory_panel"
                            )
                    else:
                        self._replace_log_lines(
                            itemize_inventory,
                            payload.itemize_inventory_lines,
                        )
                    self._replace_log_lines(self.query_one("#itemize_detail_panel"), payload.itemize_detail_lines)
                    self._replace_log_lines(self.query_one("#itemize_target_panel"), payload.itemize_target_lines)
                    self._replace_log_lines(self.query_one("#itemize_result", TextualLog), payload.log_lines)
                    return
                if payload.tab_id == "draft_tab":
                    self._set_widget_display(_subject_controls_header_row_id("draft"), False)
                    self._apply_subject_gate_panel(
                        phase="draft",
                        gate="review",
                        summary_text=_subject_current_step_text_with_last_action(
                            payload.current_step_text,
                            payload.last_action_text,
                        ),
                        actions=payload.current_step_actions,
                    )
                    self._apply_subject_secondary_gate_panel(
                        phase="draft",
                        summary_text=payload.learn_status_text,
                    )
                    self._set_pane_header_title("draft_scope_tree_panel", self._mock_subject_draft_tree_title())
                    self._set_pane_header_title(
                        "draft_model_main_panel",
                        payload.draft_model_main_title or self._mock_subject_draft_model_main_title(),
                    )
                    if payload.review_scope_detail_title:
                        self._set_pane_header_title("draft_scope_detail_panel", payload.review_scope_detail_title)
                    if payload.learn_result_title:
                        self._set_pane_header_title("draft_result", payload.learn_result_title)
                    self._replace_log_lines(self.query_one("#draft_scope_tree_panel"), payload.review_scope_lines)
                    self._replace_log_lines(self.query_one("#draft_model_main_panel"), payload.draft_model_main_lines)
                    self._replace_log_lines(self.query_one("#draft_scope_detail_panel"), payload.review_scope_detail_lines)
                    self._replace_log_lines(self.query_one("#draft_result", TextualLog), payload.log_lines)
                    return
                if payload.tab_id == "review_tab":
                    self._set_widget_display(_subject_controls_header_row_id("review"), False)
                    self._apply_subject_gate_panel(
                        phase="review",
                        gate="review",
                        summary_text=_subject_current_step_text_with_last_action(
                            payload.current_step_text,
                            payload.last_action_text,
                        ),
                        actions=payload.current_step_actions,
                    )
                    self._apply_subject_secondary_gate_panel(
                        phase="review",
                        summary_text="",
                    )
                    self.query_one("#review_status_panel", TextualStatic).update(payload.learn_status_text)
                    self._set_widget_display("review_status_panel", True)
                    self._set_pane_header_title("review_scope_tree_panel", "Report Scope")
                    if payload.review_scope_detail_title:
                        self._set_pane_header_title("review_scope_detail_panel", payload.review_scope_detail_title)
                    if payload.learn_result_title:
                        self._set_pane_header_title("review_result", payload.learn_result_title)
                    self._refresh_review_scope_tree_widget()
                    self._replace_log_lines(self.query_one("#review_scope_detail_panel"), payload.review_scope_detail_lines)
                    self._replace_log_lines(self.query_one("#review_result", TextualLog), payload.log_lines)
                    self._refresh_review_comparison_history_table()
                    self._refresh_review_latest_receipt_table()
                    return
                if payload.tab_id == "publication_tab":
                    self._set_widget_display(_subject_controls_header_row_id("publication"), False)
                    self._apply_subject_secondary_gate_panel(
                        phase="publication",
                        summary_text="",
                    )
                    self._set_widget_display("publication_status_panel", True)
                    self._refresh_publication_scope_live_panels()
                    return
                if payload.tab_id == "permissions_tab":
                    self._replace_rich_log_renderables(self.query_one("#permissions", TextualRichLog), payload.renderables)
                    return
                if payload.tab_id == "skills_tab":
                    self._replace_rich_log_renderables(self.query_one("#skills", TextualRichLog), payload.renderables)
            finally:
                self._schedule_latest_active_tab_refresh_if_needed()

        def _schedule_latest_active_tab_refresh_if_needed(self) -> None:  # pragma: no cover - requires textual runtime
            if self._tab_refresh_worker_active:
                return
            if self._tab_refresh_worker_request_id == self._tab_refresh_request_id:
                return
            self._start_active_tab_refresh_worker(
                tab_id=self._active_tab_id(),
                request_id=self._tab_refresh_request_id,
            )

        def _apply_subject_gate_panel(
            self,
            *,
            phase: str,
            gate: str,
            summary_text: str,
            actions: tuple[MockSubjectGateAction, ...],
        ) -> None:
            summary_widget = self.query_one(
                f"#{_subject_gate_summary_id(phase, gate)}",
                TextualStatic,
            )
            summary_widget.update(summary_text)
            next_label_widget = self.query_one(
                f"#{_subject_gate_next_label_id(phase, gate)}",
                TextualStatic,
            )
            next_label_widget.update("Actions" if actions else "")
            next_label_widget.display = bool(actions)
            button_ids = _subject_gate_action_button_ids(phase, gate)
            prefix_ids = _subject_gate_action_prefix_ids(phase, gate)
            for button_id in button_ids:
                self._subject_gate_action_targets.pop(button_id, None)
            action_row = self.query_one(
                f"#{_subject_gate_action_row_id(phase, gate)}",
                Horizontal,
            )
            for index, button_id in enumerate(button_ids):
                button = self.query_one(f"#{button_id}", TextualButton)
                prefix_widget = self.query_one(f"#{prefix_ids[index]}", TextualStatic)
                if index < len(actions):
                    action = actions[index]
                    prefix_label, button_label = _subject_action_label_parts(action.label)
                    button.label = button_label
                    button.disabled = not action.enabled
                    button.display = True
                    prefix_widget.update(prefix_label)
                    prefix_widget.display = True
                    if collapse_ws(action.key) in {
                        "approve_review",
                        "lock_publication",
                        "build_report",
                        "preview_publication_composition",
                        "preview_publication_composition_diff",
                        "open_release_packet",
                        "preview_publication_pdf",
                    }:
                        button.add_class("subject_gate_action_button_compact")
                    else:
                        button.remove_class("subject_gate_action_button_compact")
                    if collapse_ws(action.kind) in {"phase_nav", "subject_nav"}:
                        button.add_class("subject_gate_action_button_phase_nav")
                    else:
                        button.remove_class("subject_gate_action_button_phase_nav")
                    button.remove_class("subject_gate_action_button_placeholder")
                    self._subject_gate_action_targets[button_id] = (action.kind, action.key)
                else:
                    button.label = ""
                    button.disabled = True
                    button.display = False
                    prefix_widget.update("")
                    prefix_widget.display = False
                    button.remove_class("subject_gate_action_button_compact")
                    button.remove_class("subject_gate_action_button_phase_nav")
                    button.add_class("subject_gate_action_button_placeholder")
            action_row.display = bool(actions)

        def _apply_subject_secondary_gate_panel(
            self,
            *,
            phase: str,
            summary_text: str,
        ) -> None:
            panel_id = _subject_gate_panel_id(phase, "publication")
            panel = self.query_one(f"#{panel_id}", Vertical)
            title = _subject_secondary_gate_title(phase)
            visible = bool(title)
            panel.border_title = _textual_bold_border_title(title) if title else ""
            panel.display = visible
            summary_widget = None
            try:
                summary_widget = self.query_one(
                    f"#{_subject_gate_summary_id(phase, 'publication')}",
                    TextualStatic,
                )
            except Exception:
                summary_widget = None
            status_table = None
            if TextualDataTable is not None:
                try:
                    status_table = self.query_one(
                        f"#{_subject_gate_status_table_id(phase, 'publication')}",
                        TextualDataTable,
                    )
                except Exception:
                    status_table = None
            if not visible:
                if summary_widget is not None:
                    summary_widget.update("")
                    summary_widget.display = False
                if status_table is not None:
                    status_table.display = False
                    try:
                        status_table.clear(columns=True)
                    except Exception:
                        pass
                self.query_one(
                    f"#{_subject_gate_next_label_id(phase, 'publication')}",
                    TextualStatic,
                ).update("")
                self.query_one(
                    f"#{_subject_gate_next_label_id(phase, 'publication')}",
                    TextualStatic,
                ).display = False
                action_row = self.query_one(
                    f"#{_subject_gate_action_row_id(phase, 'publication')}",
                    Horizontal,
                )
                for button_id in _subject_gate_action_button_ids(phase, "publication"):
                    button = self.query_one(f"#{button_id}", TextualButton)
                    button.label = ""
                    button.disabled = True
                    button.display = False
                    button.remove_class("subject_gate_action_button_phase_nav")
                    button.add_class("subject_gate_action_button_placeholder")
                    self._subject_gate_action_targets.pop(button_id, None)
                for prefix_id in _subject_gate_action_prefix_ids(phase, "publication"):
                    prefix_widget = self.query_one(f"#{prefix_id}", TextualStatic)
                    prefix_widget.update("")
                    prefix_widget.display = False
                action_row.display = False
                return
            next_label_widget = self.query_one(
                f"#{_subject_gate_next_label_id(phase, 'publication')}",
                TextualStatic,
            )
            next_label_widget.update("")
            next_label_widget.display = False
            action_row = self.query_one(
                f"#{_subject_gate_action_row_id(phase, 'publication')}",
                Horizontal,
            )
            for button_id in _subject_gate_action_button_ids(phase, "publication"):
                button = self.query_one(f"#{button_id}", TextualButton)
                button.label = ""
                button.disabled = True
                button.display = False
                button.remove_class("subject_gate_action_button_compact")
                button.remove_class("subject_gate_action_button_phase_nav")
                button.add_class("subject_gate_action_button_placeholder")
                self._subject_gate_action_targets.pop(button_id, None)
            for prefix_id in _subject_gate_action_prefix_ids(phase, "publication"):
                prefix_widget = self.query_one(f"#{prefix_id}", TextualStatic)
                prefix_widget.update("")
                prefix_widget.display = False
            action_row.display = False
            if summary_widget is not None:
                summary_widget.update("")
                summary_widget.display = False
            if status_table is not None:
                phase_view = self._mock_subject_phase_view(phase)
                status_rows = tuple(
                    (
                        str(getattr(row, "label", "") or ""),
                        str(getattr(row, "value", "") or ""),
                    )
                    for row in (
                        getattr(getattr(phase_view, "status_view", None), "rows", ())
                        or ()
                    )
                )
                self._apply_structured_table_rows(
                    widget=status_table,
                    rows=status_rows,
                )

        def _refresh_chat_activity_panel(self) -> None:  # pragma: no cover - requires textual runtime
            panel = self.query_one("#chat_activity_panel", TextualStatic)
            activity_text = self._state.activity_strip_text()
            panel.display = bool(activity_text)
            panel.update(activity_text or "")

        def _pin_transcript_to_bottom(self, *, seconds: float = _TRANSCRIPT_BOTTOM_FOLLOW_SECONDS) -> None:
            self._transcript_follow_bottom_until = time.monotonic() + max(0.0, float(seconds))
            self._schedule_transcript_scroll_to_end()

        def _clear_transcript_bottom_follow(self) -> None:
            self._transcript_follow_bottom_until = None

        def _transcript_bottom_follow_active(self) -> bool:
            visible_until = self._transcript_follow_bottom_until
            return visible_until is not None and visible_until > time.monotonic()

        def _schedule_transcript_scroll_to_end(self) -> None:  # pragma: no cover - requires textual runtime
            if self._active_tab_id() != "chat_tab":
                return
            try:
                widget = self.query_one("#transcript", TextualRichLog)
            except Exception:
                return
            _textual_scroll_to_end(widget)
            for scheduler_name in ("call_after_refresh", "call_later"):
                scheduler = getattr(self, scheduler_name, None)
                if not callable(scheduler):
                    continue
                try:
                    scheduler(_textual_scroll_to_end, widget)
                except Exception:
                    continue

        def _review_scope_tree_label(self, entry: Any, held_entry_ids: set[str], selected_entry_id: str = "") -> str:
            if not bool(getattr(entry, "selectable", False)):
                label = _plain_ui_text(str(getattr(entry, "label", "") or ""))
                return RichText(label) if RichText is not None else label
            included = bool(getattr(entry, "included", False))
            toggleable = bool(getattr(entry, "toggleable", False))
            checkbox = "[x]" if included else "[ ]"
            if not toggleable and included:
                checkbox = "[-]"
            entry_id = collapse_ws(str(getattr(entry, "entry_id", "") or ""))
            selected_flag = "> " if entry_id and entry_id == selected_entry_id else "  "
            held_flag = "h " if collapse_ws(str(getattr(entry, "entry_id", "") or "")) in held_entry_ids else ""
            label = _plain_ui_text(f"{selected_flag}{held_flag}{checkbox} {str(getattr(entry, 'label', '') or '')}")
            return RichText(label) if RichText is not None else label

        def _current_review_scope_selected_entry_id(self) -> str:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            entries = self._subject_projection_backend.report_scope_entries(
                root_path=self._root,
                scenario=scenario,
                progress=progress,
            )
            selectable_entries = self._subject_projection_backend.selectable_report_scope_entries(entries)
            if not selectable_entries:
                return ""
            selected_index = max(0, min(len(selectable_entries) - 1, int(getattr(progress, "report_scope_cursor", 0) or 0)))
            return collapse_ws(str(getattr(selectable_entries[selected_index], "entry_id", "") or ""))

        def _find_review_scope_tree_node(self, tree: Any, entry_id: str) -> Any:
            normalized_entry_id = collapse_ws(str(entry_id or ""))
            if not normalized_entry_id:
                return None
            stack = list(getattr(getattr(tree, "root", None), "children", ()) or ())
            while stack:
                node = stack.pop(0)
                data = getattr(node, "data", None) or {}
                if collapse_ws(str(data.get("entry_id", "") or "")) == normalized_entry_id and bool(data.get("selectable")):
                    return node
                stack[0:0] = list(getattr(node, "children", ()) or ())
            return None

        def _sync_review_scope_tree_cursor_for_widget(self, widget_id: str, entry_id: str) -> None:  # pragma: no cover - requires textual runtime
            if TextualTree is None:
                return
            try:
                tree = self.query_one(f"#{widget_id}", _FocusableTextualTree)
            except Exception:
                return
            node = self._find_review_scope_tree_node(tree, entry_id)
            self._inventory_option_sync_suppressed.add(widget_id)
            try:
                if node is None:
                    tree.move_cursor(None, animate=False)
                    return
                tree.move_cursor(node, animate=False)
                try:
                    tree.scroll_to_node(node, animate=False)
                except Exception:
                    pass
                line = int(getattr(node, "_line", -1) or -1)
                try:
                    tree.scroll_to_line(line, animate=False)
                except Exception:
                    pass
                if line >= 0:
                    try:
                        tree.scroll_to(y=max(line - 1, 0), animate=False, force=True, immediate=True)
                    except Exception:
                        pass
                try:
                    tree.refresh(layout=True)
                except Exception:
                    pass
            finally:
                self._inventory_option_sync_suppressed.discard(widget_id)

        def _sync_review_scope_tree_cursor(self, entry_id: str) -> None:  # pragma: no cover - requires textual runtime
            normalized_entry_id = collapse_ws(str(entry_id or ""))
            if not normalized_entry_id:
                return
            for widget_id in ("review_scope_tree_panel", "detached_review_scope_tree_panel", "publication_scope_tree_panel"):
                try:
                    widget = self.query_one(f"#{widget_id}")
                except Exception:
                    continue
                if not bool(getattr(widget, "display", False)):
                    continue
                self._sync_review_scope_tree_cursor_for_widget(widget_id, normalized_entry_id)

        def _schedule_review_scope_tree_cursor_sync(self, entry_id: str) -> None:  # pragma: no cover - requires textual runtime
            normalized_entry_id = collapse_ws(str(entry_id or ""))
            if not normalized_entry_id:
                return
            self._pending_review_scope_tree_sync_entry_id = normalized_entry_id

            def _apply_pending_sync(attempt: int = 0) -> None:
                pending_entry_id = collapse_ws(str(self._pending_review_scope_tree_sync_entry_id or ""))
                if not pending_entry_id:
                    return
                self._sync_review_scope_tree_cursor(pending_entry_id)
                if attempt < 2:
                    self._pending_review_scope_tree_sync_entry_id = pending_entry_id
                    scheduler = getattr(self, "call_after_refresh", None)
                    if not callable(scheduler):
                        scheduler = getattr(self, "call_later", None)
                    if callable(scheduler):
                        try:
                            scheduler(lambda next_attempt=attempt + 1: _apply_pending_sync(next_attempt))
                            return
                        except Exception:
                            pass
                self._pending_review_scope_tree_sync_entry_id = ""

            scheduler = getattr(self, "call_after_refresh", None)
            if callable(scheduler):
                try:
                    scheduler(_apply_pending_sync)
                    return
                except Exception:
                    pass
            scheduler = getattr(self, "call_later", None)
            if callable(scheduler):
                try:
                    scheduler(_apply_pending_sync)
                    return
                except Exception:
                    pass
            _apply_pending_sync()

        def _refresh_review_scope_tree_widget(self, widget_id: str = "review_scope_tree_panel") -> None:  # pragma: no cover - requires textual runtime
            if TextualTree is None:
                return
            try:
                tree = self.query_one(f"#{widget_id}", _FocusableTextualTree)
            except Exception:
                return
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            entries = self._subject_projection_backend.report_scope_entries(
                root_path=self._root,
                scenario=scenario,
                progress=progress,
            )
            held_entry_ids = {
                collapse_ws(item)
                for item in getattr(progress, "report_scope_held_entry_ids", ())
                if collapse_ws(item)
            }
            selected_entry_id = ""
            selectable_entries = self._subject_projection_backend.selectable_report_scope_entries(entries)
            if selectable_entries:
                selected_index = max(0, min(len(selectable_entries) - 1, int(getattr(progress, "report_scope_cursor", 0) or 0)))
                selected_entry_id = collapse_ws(str(getattr(selectable_entries[selected_index], "entry_id", "") or ""))
            self._inventory_option_sync_suppressed.add(widget_id)
            try:
                tree.reset("Report Scope")
                tree.show_root = False
                root = tree.root
                root.expand()
                node_stack: dict[int, Any] = {-1: root}
                if not entries:
                    pane_phase = "publication" if widget_id == "publication_scope_tree_panel" else "review"
                    pane_key = "publication_scope_tree" if pane_phase == "publication" else "review_scope_tree"
                    placeholder_lines = tuple(
                        str(line or "")
                        for line in self._mock_subject_pane_text(pane_phase, pane_key).splitlines()
                        if collapse_ws(str(line or ""))
                    ) or ("No report plan is available yet.",)
                    for line in placeholder_lines:
                        root.add_leaf(line, data={"selectable": False})
                else:
                    selectable_index = -1
                    for entry in entries:
                        depth = max(0, int(getattr(entry, "depth", 0) or 0))
                        parent = node_stack.get(depth - 1, root)
                        selectable = bool(getattr(entry, "selectable", False))
                        if selectable:
                            selectable_index += 1
                        node = (
                            parent.add_leaf(
                                self._review_scope_tree_label(entry, held_entry_ids, selected_entry_id=selected_entry_id),
                                data={
                                    "entry_id": collapse_ws(str(getattr(entry, "entry_id", "") or "")),
                                    "selectable": selectable,
                                    "selectable_index": selectable_index if selectable else None,
                                },
                            )
                            if selectable
                            else parent.add(
                                self._review_scope_tree_label(entry, held_entry_ids, selected_entry_id=selected_entry_id),
                                data={
                                    "entry_id": collapse_ws(str(getattr(entry, "entry_id", "") or "")),
                                    "selectable": False,
                                    "selectable_index": None,
                                },
                                expand=True,
                                allow_expand=True,
                            )
                        )
                        node_stack[depth] = node
                        for stale_depth in tuple(existing_depth for existing_depth in node_stack if existing_depth > depth):
                            node_stack.pop(stale_depth, None)
            finally:
                self._inventory_option_sync_suppressed.discard(widget_id)

        def _refresh_review_scope_live_panels(self) -> None:  # pragma: no cover - requires textual runtime
            self._subject_snapshot_cache.pop("review", None)
            self._apply_subject_gate_panel(
                phase="review",
                gate="review",
                summary_text=_subject_current_step_text_with_last_action(
                    self._mock_subject_current_step_text("review"),
                    self._mock_subject_last_action_text(),
                ),
                actions=self._mock_subject_current_step_actions("review"),
            )
            self._apply_subject_secondary_gate_panel(
                phase="review",
                summary_text="",
            )
            self.query_one("#review_status_panel", TextualStatic).update(self._mock_subject_status_panel_text("review"))
            self._set_widget_display("review_status_panel", True)
            self._refresh_review_publication_output_mode_select()
            self._refresh_review_publication_section_plan_select()
            self._refresh_review_publication_diff_baseline_select()
            self._refresh_review_composition_unit_target_select()
            self._refresh_review_composition_unit_included_switch()
            self._refresh_review_publication_section_target_select()
            self._refresh_review_publication_section_included_switch()
            self._set_pane_header_title("review_scope_tree_panel", "Report Scope")
            self._set_pane_header_title("review_scope_detail_panel", self._mock_subject_review_scope_detail_title())
            self._set_pane_header_title("review_result", self._mock_subject_workspace_title("review"))
            self._refresh_review_scope_tree_widget()
            try:
                detached_tree = self.query_one("#detached_review_scope_tree_panel")
            except Exception:
                detached_tree = None
            if detached_tree is not None and bool(getattr(detached_tree, "display", False)):
                self._refresh_review_scope_tree_widget("detached_review_scope_tree_panel")
            self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())
            if detached_tree is not None and bool(getattr(detached_tree, "display", False)):
                try:
                    detached_tree.focus()
                except Exception:
                    pass
            self._refresh_review_detail_buttons()
            detail_widget = self.query_one("#review_scope_detail_panel")
            self._replace_log_lines(
                detail_widget,
                str(self._mock_subject_review_scope_detail_text() or "").splitlines(),
            )
            result_widget = self.query_one("#review_result", TextualLog)
            self._replace_log_lines(
                result_widget,
                _wrap_textual_log_lines(
                    self._mock_subject_workspace_text("review"),
                    width=self._textual_log_wrap_width(result_widget),
                ),
            )

        def _refresh_publication_scope_live_panels(self) -> None:  # pragma: no cover - requires textual runtime
            self._subject_snapshot_cache.pop("publication", None)
            self._apply_subject_gate_panel(
                phase="publication",
                gate="review",
                summary_text=_subject_current_step_text_with_last_action(
                    self._mock_subject_current_step_text("publication"),
                    self._mock_subject_last_action_text(),
                ),
                actions=self._mock_subject_current_step_actions("publication"),
            )
            self._apply_subject_secondary_gate_panel(
                phase="publication",
                summary_text="",
            )
            self.query_one("#publication_status_panel", TextualStatic).update(self._mock_subject_status_panel_text("publication"))
            self._set_widget_display("publication_status_panel", True)
            self._refresh_publication_output_mode_select()
            self._refresh_publication_section_plan_select()
            self._refresh_publication_diff_baseline_select()
            self._refresh_publication_import_target_select()
            self._refresh_publication_composition_unit_target_select()
            self._refresh_publication_composition_unit_included_switch()
            self._refresh_publication_section_target_select()
            self._refresh_publication_section_included_switch()
            self._refresh_publication_import_included_switch()
            self._refresh_publication_import_usage_select()
            self._set_pane_header_title("publication_scope_tree_panel", "Report Scope")
            self._set_pane_header_title("publication_scope_detail_panel", self._mock_subject_publication_scope_detail_title())
            self._set_pane_header_title("publication_result", self._mock_subject_workspace_title("publication"))
            self._refresh_review_scope_tree_widget("publication_scope_tree_panel")
            self._schedule_review_scope_tree_cursor_sync(self._current_review_scope_selected_entry_id())
            detail_widget = self.query_one("#publication_scope_detail_panel")
            self._replace_log_lines(
                detail_widget,
                str(self._mock_subject_publication_scope_detail_text() or "").splitlines(),
            )
            result_widget = self.query_one("#publication_result", TextualLog)
            self._replace_log_lines(
                result_widget,
                _wrap_textual_log_lines(
                    self._mock_subject_workspace_text("publication"),
                    width=self._textual_log_wrap_width(result_widget),
                ),
            )
            self._refresh_publication_build_artifacts_table()
            self._refresh_publication_build_receipt_table()
            self._refresh_publication_latest_receipt_table()

        def _refresh_draft_live_panels(self) -> None:  # pragma: no cover - requires textual runtime
            self._invalidate_active_tab_refresh_payloads(tab_id="draft_tab")
            self._subject_snapshot_cache.pop("draft", None)
            self._apply_subject_gate_panel(
                phase="draft",
                gate="review",
                summary_text=_subject_current_step_text_with_last_action(
                    self._mock_subject_current_step_text("draft"),
                    self._mock_subject_last_action_text(),
                ),
                actions=self._mock_subject_current_step_actions("draft"),
            )
            self._apply_subject_secondary_gate_panel(
                phase="draft",
                summary_text=self._mock_subject_status_panel_text("draft"),
            )
            self._refresh_draft_decision_included_switch()
            self._refresh_draft_semantic_kind_select()
            self._refresh_draft_render_kind_select()
            self._refresh_draft_evidence_mode_select()
            self._refresh_draft_transform_mode_select()
            self._refresh_draft_model_construct_sort_select()
            self._refresh_draft_model_construct_lane_select()
            self._refresh_draft_model_transition_selects()
            self._refresh_draft_model_policy_profile_select()
            self._refresh_draft_model_lens_tabs()
            self._refresh_draft_model_relation_selection_lists()
            self._set_pane_header_title("draft_scope_tree_panel", self._mock_subject_draft_tree_title())
            self._set_pane_header_title("draft_model_main_panel", self._mock_subject_draft_model_main_title())
            self._set_pane_header_title("draft_scope_detail_panel", self._mock_subject_draft_detail_title())
            self._set_pane_header_title("draft_result", self._mock_subject_draft_result_title())
            self._replace_log_lines(
                self.query_one("#draft_scope_tree_panel"),
                str(self._mock_subject_draft_scope_tree_text() or "").splitlines(),
            )
            self._replace_log_lines(
                self.query_one("#draft_model_main_panel"),
                str(self._mock_subject_draft_model_main_text() or "").splitlines(),
            )
            self._replace_log_lines(
                self.query_one("#draft_scope_detail_panel"),
                str(self._mock_subject_draft_detail_text() or "").splitlines(),
            )
            result_widget = self.query_one("#draft_result", TextualLog)
            self._replace_log_lines(
                result_widget,
                _wrap_textual_log_lines(
                    self._mock_subject_draft_issue_tray_text(),
                    width=self._textual_log_wrap_width(result_widget),
                ),
            )
            self._refresh_draft_detail_buttons()
            self._set_widget_display("draft_scope_tree_wrapper", True)
            self._set_widget_display("draft_model_main_wrapper", self._draft_model_mode_active())
            self._set_widget_display("draft_scope_detail_wrapper", True)
            self._set_widget_display("draft_result_panel", self._draft_model_mode_active())
            self._sync_draft_scope_table_cursor_from_progress()

        def _refresh_draft_model_selection_controls(self) -> None:
            self._refresh_draft_model_construct_sort_select()
            self._refresh_draft_model_construct_lane_select()
            self._refresh_draft_model_transition_selects()
            self._refresh_draft_model_policy_profile_select()
            self._refresh_draft_model_lens_tabs()
            self._refresh_draft_model_relation_selection_lists()
            self._refresh_draft_detail_buttons()

        def _run_draft_model_deferred_refresh(self, request_id: int) -> None:
            if int(request_id) != int(getattr(self, "_draft_model_deferred_refresh_request_id", 0) or 0):
                return
            if not self._draft_model_mode_active():
                return
            self._refresh_draft_model_selection_controls()

        def _schedule_draft_model_deferred_refresh(self) -> None:
            self._draft_model_deferred_refresh_request_id = int(
                getattr(self, "_draft_model_deferred_refresh_request_id", 0) or 0
            ) + 1
            request_id = self._draft_model_deferred_refresh_request_id
            callback = getattr(self, "call_later", None) or getattr(self, "call_after_refresh", None)
            if callable(callback):
                try:
                    callback(self._run_draft_model_deferred_refresh, request_id)
                    return
                except Exception:
                    pass
            self._run_draft_model_deferred_refresh(request_id)

        def _refresh_draft_selection_live_panels(
            self,
            *,
            clear_snapshot_cache: bool = True,
            defer_model_controls: bool = False,
        ) -> None:  # pragma: no cover - requires textual runtime
            self._invalidate_active_tab_refresh_payloads(tab_id="draft_tab")
            if clear_snapshot_cache:
                self._subject_snapshot_cache.pop("draft", None)
            if self._draft_model_mode_active():
                if defer_model_controls:
                    self._schedule_draft_model_deferred_refresh()
                else:
                    self._refresh_draft_model_selection_controls()
                self._set_pane_header_title("draft_model_main_panel", self._mock_subject_draft_model_main_title())
                self._replace_log_lines(
                    self.query_one("#draft_model_main_panel"),
                    str(self._mock_subject_draft_model_main_text() or "").splitlines(),
                )
            else:
                self._refresh_draft_decision_included_switch()
                self._refresh_draft_semantic_kind_select()
                self._refresh_draft_render_kind_select()
                self._refresh_draft_evidence_mode_select()
                self._refresh_draft_transform_mode_select()
            self._set_pane_header_title("draft_scope_detail_panel", self._mock_subject_draft_detail_title())
            self._replace_log_lines(
                self.query_one("#draft_scope_detail_panel"),
                str(self._mock_subject_draft_detail_text() or "").splitlines(),
            )
            self._set_pane_header_title("draft_result", self._mock_subject_draft_result_title())
            result_widget = self.query_one("#draft_result", TextualLog)
            self._replace_log_lines(
                result_widget,
                _wrap_textual_log_lines(
                    self._mock_subject_draft_issue_tray_text(),
                    width=self._textual_log_wrap_width(result_widget),
                ),
            )
            if not self._draft_model_mode_active():
                self._refresh_draft_detail_buttons()
            self._sync_draft_scope_table_cursor_from_progress(schedule_after_refresh=False)

        def _prime_subject_snapshot_cache_from_backend(self, phase: str) -> bool:
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            if not normalized_phase:
                return False
            snapshot = self._subject_projection_backend.take_latest_interaction_snapshot(normalized_phase)
            if snapshot is None:
                return False
            self._subject_snapshot_cache[normalized_phase] = snapshot
            self._subject_local_interaction_fingerprints[normalized_phase] = self._subject_projection_backend.progress_fingerprint(
                self._mock_subject_progress()
            )
            return True

        def _refresh_report_scope_control_widgets(self, phase: str) -> None:  # pragma: no cover - requires textual runtime
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            self._subject_snapshot_cache.pop(normalized_phase, None)
            if normalized_phase == "publication":
                self._refresh_publication_output_mode_select()
                self._refresh_publication_section_plan_select()
                self._refresh_publication_diff_baseline_select()
                self._refresh_publication_import_target_select()
                self._refresh_publication_import_included_switch()
                self._refresh_publication_import_usage_select()
                self._refresh_publication_composition_unit_target_select()
                self._refresh_publication_composition_unit_included_switch()
                self._refresh_publication_section_target_select()
                self._refresh_publication_section_included_switch()
                return
            if normalized_phase == "review":
                self._refresh_review_publication_output_mode_select()
                self._refresh_review_publication_section_plan_select()
                self._refresh_review_publication_diff_baseline_select()
                self._refresh_review_composition_unit_target_select()
                self._refresh_review_composition_unit_included_switch()
                self._refresh_review_publication_section_target_select()
                self._refresh_review_publication_section_included_switch()

        def _refresh_report_scope_live_panels(self, phase: str) -> None:  # pragma: no cover - requires textual runtime
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            if normalized_phase == "publication":
                self._refresh_publication_scope_live_panels()
                return
            self._refresh_review_scope_live_panels()

        def _should_use_local_review_scope_refresh(self, phase: str, action_key: str, result: Any) -> bool:
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            if normalized_phase not in {"review", "publication"}:
                return False
            normalized_action = collapse_ws(str(action_key or "")).casefold()
            local_actions = {
                "toggle_selected_report_scope_item",
                "hold_selected_report_scope_item",
                "release_held_report_scope_items",
                "preview_selected_report_scope_item",
                "preview_publication_composition_diff",
                "toggle_selected_composition_unit",
                "toggle_selected_publication_import",
                "toggle_selected_publication_section",
            }
            local_prefixes = (
                "set_selected_composition_unit:",
                "set_selected_publication_section:",
                "set_publication_output_mode:",
                "set_publication_section_plan:",
                "set_publication_diff_baseline:",
                "set_publication_import_target:",
                "set_selected_publication_import_usage_",
            )
            if normalized_action not in local_actions and not normalized_action.startswith(local_prefixes):
                return False
            target_tab = collapse_ws(str(getattr(result, "next_tab", "") or "")).casefold()
            if target_tab == "chat":
                return False
            if normalized_phase == "review":
                phase_view = getattr(result, "phase_view", None)
                guided_phase = collapse_ws(
                    str(
                        getattr(phase_view, "preferred_phase", "")
                        or getattr(phase_view, "phase", "")
                        or ""
                    )
                ).casefold()
                if guided_phase and guided_phase != normalized_phase:
                    return False
            return True

        def _should_use_local_draft_refresh(self, phase: str, action_key: str, result: Any) -> bool:
            normalized_phase = collapse_ws(str(phase or "")).casefold()
            if normalized_phase != "draft":
                return False
            normalized_action = collapse_ws(str(action_key or "")).casefold()
            if normalized_action not in {
                "toggle_selected_draft_review_item_in_decision_frame",
                "move_selected_draft_review_item_earlier",
                "move_selected_draft_review_item_later",
                "open_draft_model_view",
                "open_draft_compose_view",
                "open_draft_model_frame_view",
                "open_draft_model_model_view",
                "open_draft_model_explore_view",
            } and not normalized_action.startswith(
                (
                    "set_selected_draft_review_",
                    "set_selected_draft_construct_",
                )
            ):
                return False
            if bool(getattr(result, "reload_subjects", False)):
                return False
            target_tab = collapse_ws(str(getattr(result, "next_tab", "") or "")).casefold()
            if target_tab == "chat":
                return False
            guided_phase = self._guided_subject_phase_from_action_result(normalized_phase, result)
            return guided_phase == normalized_phase

        def _textual_log_wrap_width(self, widget: Any) -> int:  # pragma: no cover - requires textual runtime
            widget_width = int(getattr(getattr(widget, "size", None), "width", 0) or 0)
            if widget_width > 28:
                return max(widget_width - 2, 24)
            app_width = int(getattr(getattr(self, "size", None), "width", 0) or 0)
            if app_width > 40:
                return max(app_width - 10, 24)
            screen_width = int(getattr(getattr(getattr(self, "screen", None), "size", None), "width", 0) or 0)
            if screen_width > 40:
                return max(screen_width - 10, 24)
            return 80

        def _tab_ids(self) -> list[str]:
            return list(_TEXTUAL_TAB_ORDER)

        def _active_prompt_suggestions(self) -> list[str]:
            input_widget = self.query_one("#input", TextualInput)
            current_value = str(getattr(input_widget, "value", "") or "")
            if not current_value.strip():
                return []
            with self._state.lock:
                context = self._state.context
            return workstation_chat_live_suggestions(context=context, buffer_text=current_value)

        def _refresh_prompt_suggestions(self) -> None:  # pragma: no cover - requires textual runtime
            suggestions = self._active_prompt_suggestions()
            bar = self.query_one("#suggestion_bar", TextualLog)
            if not suggestions:
                self._selected_prompt_suggestion_index = 0
                bar.display = False
                self._replace_log_text(bar, "")
            else:
                self._selected_prompt_suggestion_index = max(
                    0,
                    min(self._selected_prompt_suggestion_index, len(suggestions) - 1),
                )
                lines = [
                    (
                        f"> {_render_prompt_suggestion_text(suggestion)}"
                        if index == self._selected_prompt_suggestion_index
                        else f"  {_render_prompt_suggestion_text(suggestion)}"
                    )
                    for index, suggestion in enumerate(suggestions)
                ]
                bar.display = True
                self._replace_log_text(bar, "\n".join(lines))
                try:
                    bar.scroll_to(y=self._selected_prompt_suggestion_index, animate=False, force=True, immediate=True)
                except Exception:
                    pass

        def _chat_focus_order(self) -> list[Any]:
            return [self.query_one("#input", TextualInput), self.query_one("#transcript", TextualRichLog)]

        def _move_selected_prompt_suggestion(self, delta: int) -> bool:
            suggestions = self._active_prompt_suggestions()
            if not suggestions:
                return False
            self._selected_prompt_suggestion_index = (
                self._selected_prompt_suggestion_index + int(delta)
            ) % len(suggestions)
            self._refresh_prompt_suggestions()
            return True

        def _apply_selected_prompt_suggestion(self) -> bool:
            suggestions = self._active_prompt_suggestions()
            if not suggestions:
                return False
            selected_index = max(0, min(self._selected_prompt_suggestion_index, len(suggestions) - 1))
            selected_value = suggestions[selected_index]
            input_widget = self.query_one("#input", TextualInput)
            with self._state.lock:
                context = self._state.context
            applied_value = workstation_chat_apply_prompt_suggestion(
                context=context,
                buffer_text=str(getattr(input_widget, "value", "") or ""),
                suggestion=selected_value,
            )
            input_widget.value = applied_value
            try:
                input_widget.cursor_position = len(applied_value)
            except Exception:
                pass
            self._state.set_current_input_text(applied_value, refresh=False)
            self._refresh_inline_hint()
            self._refresh_prompt_suggestions()
            input_widget.focus()
            return True

        def _focus_order_for_active_tab(self) -> list[Any]:
            if self._detached_pane_visible():
                focus_order: list[Any] = []
                try:
                    detached_tree = self.query_one("#detached_review_scope_tree_panel", _FocusableTextualTree)
                    if bool(getattr(detached_tree, "display", False)):
                        focus_order.append(detached_tree)
                except Exception:
                    pass
                try:
                    focus_order.append(
                        self.query_one(
                            f"#{_textual_detached_pane_info_button_id()}",
                            TextualButton,
                        )
                    )
                except Exception:
                    pass
                try:
                    focus_order.append(
                        self.query_one(
                            f"#{_textual_detached_pane_dismiss_button_id()}",
                            TextualButton,
                        )
                    )
                except Exception:
                    pass
                try:
                    detached_log = self.query_one("#detached_pane_panel", TextualLog)
                    if bool(getattr(detached_log, "display", False)):
                        focus_order.append(detached_log)
                except Exception:
                    pass
                return focus_order
            maximized = self._maximized_pane_spec()
            if maximized is not None:
                try:
                    focus_order = [self.query_one(f"#{maximized['pane_id']}")]
                    if collapse_ws(maximized.get("pane_id", "")) == "subject_sources_panel":
                        focus_order.append(self.query_one(f"#{_research_sources_llm_button_id()}", TextualButton))
                        focus_order.append(self.query_one(f"#{_research_sources_manual_rephrase_button_id()}", TextualButton))
                    if collapse_ws(maximized.get("pane_id", "")) == "subject_target_panel":
                        focus_order.append(self.query_one(f"#{_research_detail_llm_button_id()}", TextualButton))
                        focus_order.append(self.query_one(f"#{_research_detail_manual_rephrase_button_id()}", TextualButton))
                    if collapse_ws(maximized.get("pane_id", "")) == "itemize_detail_panel":
                        focus_order.append(self.query_one(f"#{_itemize_detail_llm_button_id()}", TextualButton))
                        focus_order.append(self.query_one(f"#{_itemize_detail_manual_rephrase_button_id()}", TextualButton))
                    if collapse_ws(maximized.get("pane_id", "")) == "draft_scope_detail_panel":
                        focus_order.append(self.query_one(f"#{_draft_detail_llm_button_id()}", TextualButton))
                        focus_order.append(self.query_one(f"#{_draft_detail_manual_rephrase_button_id()}", TextualButton))
                    return focus_order
                except Exception:
                    return []
            active = self._active_tab_id()
            if active == "chat_tab":
                return self._chat_focus_order()
            if active == "learn_tab":
                focus_order = [
                    self.query_one("#learn_markdown_button", TextualButton),
                    self.query_one("#learn_url_button", TextualButton),
                    self.query_one("#export_learned_button", TextualButton),
                    self.query_one("#subject_prev_button", TextualButton),
                    self.query_one("#subject_next_button", TextualButton),
                    self.query_one(f"#{_subject_hidden_pane_button_id('research')}", TextualButton),
                    self.query_one(f"#{_subject_journal_button_id('research')}", TextualButton),
                    *(self.query_one(f"#{button_id}", TextualButton) for button_id in _subject_action_button_ids("research")),
                    self.query_one(f"#{_research_source_collection_select_id()}", TextualSelect),
                    self.query_one(f"#{_research_source_revision_baseline_select_id()}", TextualSelect),
                    self.query_one(f"#{_research_source_collection_membership_switch_id()}", TextualSwitch),
                    self.query_one("#subject_sources_panel"),
                    self.query_one(f"#{_research_sources_llm_button_id()}", TextualButton),
                    self.query_one(f"#{_research_sources_manual_rephrase_button_id()}", TextualButton),
                    self.query_one("#subject_target_panel"),
                    self.query_one(f"#{_research_detail_llm_button_id()}", TextualButton),
                    self.query_one(f"#{_research_detail_manual_rephrase_button_id()}", TextualButton),
                ]
                return focus_order
            if active == "itemize_tab":
                focus_order = [
                    self.query_one(f"#{_subject_nav_button_id('itemize', 'prev')}", TextualButton),
                    self.query_one(f"#{_subject_nav_button_id('itemize', 'next')}", TextualButton),
                    self.query_one(f"#{_subject_hidden_pane_button_id('itemize')}", TextualButton),
                    self.query_one(f"#{_subject_journal_button_id('itemize')}", TextualButton),
                    self.query_one(f"#{_itemize_decision_role_select_id()}", TextualSelect),
                    self.query_one(f"#{_itemize_hold_switch_id()}", TextualSwitch),
                    self.query_one("#itemize_inventory_panel"),
                    self.query_one("#itemize_detail_panel"),
                    self.query_one(f"#{_itemize_detail_llm_button_id()}", TextualButton),
                    self.query_one(f"#{_itemize_detail_manual_rephrase_button_id()}", TextualButton),
                ]
                for button_id in _subject_action_button_ids("itemize"):
                    button = self.query_one(f"#{button_id}", TextualButton)
                    if bool(getattr(button, "display", True)):
                        focus_order.append(button)
                return focus_order
            if active == "draft_tab":
                focus_order: list[Any] = []
                for button_id in _subject_action_button_ids("draft"):
                    button = self.query_one(f"#{button_id}", TextualButton)
                    if bool(getattr(button, "display", True)):
                        focus_order.append(button)
                if self._draft_model_mode_active():
                    focus_order.append(self.query_one(f"#{_draft_model_lens_tabs_id()}", TextualTabs))
                    focus_order.append(self.query_one(f"#{_draft_model_construct_sort_select_id()}", TextualSelect))
                    focus_order.append(self.query_one(f"#{_draft_model_construct_lane_select_id()}", TextualSelect))
                    try:
                        transition_row = self.query_one("#draft_model_transition_row")
                        if bool(getattr(transition_row, "display", False)):
                            focus_order.append(self.query_one(f"#{_draft_model_transition_source_select_id()}", TextualSelect))
                            focus_order.append(self.query_one(f"#{_draft_model_transition_target_select_id()}", TextualSelect))
                    except Exception:
                        pass
                    focus_order.append(self.query_one(f"#{_draft_model_policy_profile_select_id()}", TextualSelect))
                    if TextualSelectionList is not None:
                        for slot in range(2):
                            wrapper = self.query_one(f"#{_draft_model_relation_wrapper_id(slot)}")
                            if bool(getattr(wrapper, "display", False)):
                                focus_order.append(
                                    self.query_one(
                                        f"#{_draft_model_relation_selection_list_id(slot)}",
                                        TextualSelectionList,
                                    )
                                )
                else:
                    focus_order.append(self.query_one(f"#{_draft_semantic_kind_select_id()}", TextualSelect))
                    focus_order.append(self.query_one(f"#{_draft_render_kind_select_id()}", TextualSelect))
                    focus_order.append(self.query_one(f"#{_draft_evidence_mode_select_id()}", TextualSelect))
                    focus_order.append(self.query_one(f"#{_draft_transform_mode_select_id()}", TextualSelect))
                    focus_order.append(self.query_one(f"#{_draft_decision_included_switch_id()}", TextualSwitch))
                focus_order.append(self.query_one("#draft_scope_tree_panel"))
                if self._draft_model_mode_active():
                    focus_order.append(self.query_one("#draft_model_main_panel"))
                focus_order.extend(
                    [
                        self.query_one("#draft_scope_detail_panel"),
                        self.query_one(f"#{_draft_detail_llm_button_id()}", TextualButton),
                        self.query_one(f"#{_draft_detail_manual_rephrase_button_id()}", TextualButton),
                        self.query_one(f"#{_subject_nav_button_id('draft', 'prev')}", TextualButton),
                        self.query_one(f"#{_subject_nav_button_id('draft', 'next')}", TextualButton),
                        self.query_one(f"#{_subject_journal_button_id('draft')}", TextualButton),
                    ]
                )
                return focus_order
            if active == "review_tab":
                focus_order = [
                    *(self.query_one(f"#{button_id}", TextualButton) for button_id in _subject_action_button_ids("review")),
                    self.query_one(f"#{_review_publication_output_mode_select_id()}", TextualSelect),
                    self.query_one(f"#{_review_publication_section_plan_select_id()}", TextualSelect),
                    self.query_one(f"#{_review_publication_diff_baseline_select_id()}", TextualSelect),
                    self.query_one(f"#{_review_composition_unit_target_select_id()}", TextualSelect),
                    self.query_one(f"#{_review_composition_unit_included_switch_id()}", TextualSwitch),
                    self.query_one(f"#{_review_publication_section_target_select_id()}", TextualSelect),
                    self.query_one(f"#{_review_publication_section_included_switch_id()}", TextualSwitch),
                    self.query_one("#review_scope_tree_panel"),
                    self.query_one("#review_scope_detail_panel"),
                    self.query_one(f"#{_review_detail_llm_button_id()}", TextualButton),
                    self.query_one(f"#{_review_detail_manual_rephrase_button_id()}", TextualButton),
                    self.query_one(f"#{_subject_nav_button_id('review', 'prev')}", TextualButton),
                    self.query_one(f"#{_subject_nav_button_id('review', 'next')}", TextualButton),
                    self.query_one(f"#{_subject_journal_button_id('review')}", TextualButton),
                ]
                return focus_order
            if active == "publication_tab":
                focus_order = [
                    self.query_one(f"#{_publication_output_mode_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_section_plan_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_diff_baseline_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_import_target_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_import_included_switch_id()}", TextualSwitch),
                    self.query_one(f"#{_publication_import_usage_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_composition_unit_target_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_composition_unit_included_switch_id()}", TextualSwitch),
                    self.query_one(f"#{_publication_section_target_select_id()}", TextualSelect),
                    self.query_one(f"#{_publication_section_included_switch_id()}", TextualSwitch),
                    self.query_one("#publication_scope_tree_panel"),
                    self.query_one("#publication_scope_detail_panel"),
                    self.query_one(f"#{_subject_nav_button_id('publication', 'prev')}", TextualButton),
                    self.query_one(f"#{_subject_nav_button_id('publication', 'next')}", TextualButton),
                    self.query_one(f"#{_subject_journal_button_id('publication')}", TextualButton),
                    *(self.query_one(f"#{button_id}", TextualButton) for button_id in _subject_action_button_ids("publication")),
                ]
                return focus_order
            if active == "permissions_tab":
                return [self.query_one("#permissions", TextualRichLog)]
            if active == "activity_tab":
                return [self.query_one("#activity", TextualRichLog)]
            if active == "skills_tab":
                return [self.query_one("#skills", TextualRichLog)]
            return []

        def _focus_first_panel_for_active_tab(self) -> None:  # pragma: no cover - requires textual runtime
            focus_order = self._focus_order_for_active_tab()
            if focus_order:
                focus_order[0].focus()

        def action_focus_next_panel(self) -> None:  # pragma: no cover - requires textual runtime
            if self._maximized_pane_spec() is not None:
                focus_order = self._focus_order_for_active_tab()
                if focus_order:
                    focus_order[0].focus()
                return
            if self.focused is self.query_one("#input", TextualInput) and self._apply_selected_prompt_suggestion():
                return
            focus_order = self._focus_order_for_active_tab()
            if not focus_order:
                return
            self._focus_relative(focus_order, 1)

        def action_next_tab(self) -> None:  # pragma: no cover - requires textual runtime
            if self._maximized_pane_spec() is not None:
                return
            self._dismiss_detached_pane()
            tab_ids = self._tab_ids()
            current = self._active_tab_id()
            if current not in tab_ids:
                self._active_tab_id_value = tab_ids[0]
                self._apply_active_tab_state()
                self.request_state_refresh()
                self._focus_first_panel_for_active_tab()
                return
            self._active_tab_id_value = tab_ids[(tab_ids.index(current) + 1) % len(tab_ids)]
            self._apply_active_tab_state()
            self.request_state_refresh()
            self._focus_first_panel_for_active_tab()

        def action_previous_tab(self) -> None:  # pragma: no cover - requires textual runtime
            if self._maximized_pane_spec() is not None:
                return
            self._dismiss_detached_pane()
            tab_ids = self._tab_ids()
            current = self._active_tab_id()
            if current not in tab_ids:
                self._active_tab_id_value = tab_ids[0]
                self._apply_active_tab_state()
                self.request_state_refresh()
                self._focus_first_panel_for_active_tab()
                return
            self._active_tab_id_value = tab_ids[(tab_ids.index(current) - 1) % len(tab_ids)]
            self._apply_active_tab_state()
            self.request_state_refresh()
            self._focus_first_panel_for_active_tab()

        def _focus_relative(self, focus_order: list[Any], delta: int) -> None:  # pragma: no cover - requires textual runtime
            current = self.focused
            if current not in focus_order:
                focus_order[0 if delta >= 0 else -1].focus()
                return
            index = focus_order.index(current)
            focus_order[(index + delta) % len(focus_order)].focus()

        def _report_scope_phase(self) -> str | None:
            try:
                focus_id = str(getattr(self.focused, "id", "") or "")
            except Exception:
                return None
            if self._active_tab_id() == "review_tab" and focus_id in {
                "review_scope_tree_panel",
                "review_scope_detail_panel",
                "detached_review_scope_tree_panel",
            }:
                return "review"
            if self._active_tab_id() == "publication_tab" and focus_id in {
                "publication_scope_tree_panel",
                "publication_scope_detail_panel",
            }:
                return "publication"
            return None

        def _review_scope_focus_active(self) -> bool:
            return self._report_scope_phase() is not None

        def _research_focus_active(self) -> bool:
            return (
                self._active_tab_id() == "learn_tab"
                and str(getattr(self.focused, "id", "") or "") in {"subject_sources_panel", "subject_target_panel"}
            )

        def _itemize_focus_active(self) -> bool:
            return (
                self._active_tab_id() == "itemize_tab"
                and str(getattr(self.focused, "id", "") or "") in {"itemize_inventory_panel", "itemize_detail_panel"}
            )

        def _draft_workspace_focus_active(self) -> bool:
            return (
                self._active_tab_id() == "draft_tab"
                and str(getattr(self.focused, "id", "") or "") in {"draft_scope_tree_panel", "draft_model_main_panel", "draft_scope_detail_panel", "draft_result"}
            )

        def _move_itemize_cursor(self, delta: int) -> bool:
            if not self._itemize_focus_active():
                return False
            selected = self._subject_projection_backend.move_itemize_cursor(
                root_path=self._root,
                scenario=self._mock_subject_scenario(),
                progress=self._mock_subject_progress(),
                delta=delta,
            )
            if selected is None:
                return False
            self._mark_subject_progress_dirty()
            self._refresh_current_subject_phase_projection()
            return True

        def _move_research_source_cursor(self, delta: int) -> bool:
            if not self._research_focus_active():
                return False
            selected = self._subject_projection_backend.move_research_source_cursor(
                root_path=self._root,
                scenario=self._mock_subject_scenario(),
                progress=self._mock_subject_progress(),
                delta=delta,
            )
            if selected is None:
                return False
            self._mark_subject_progress_dirty()
            self._refresh_current_subject_phase_projection()
            return True

        def _select_research_row_ordinal(self, ordinal: int) -> bool:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            _selected_collection, staged_sources = self._subject_projection_backend.staged_sources_for_selected_collection(
                root_path=self._root,
                subject_id=scenario.subject_id,
                progress=progress,
            )
            if not staged_sources:
                return False
            target_index = max(0, min(len(staged_sources) - 1, int(ordinal)))
            selected = staged_sources[target_index]
            progress.research_source_cursor = target_index
            progress.research_selected_staged_source_id = collapse_ws(selected.staged_source_id)
            self._mark_subject_progress_dirty(scenario)
            self._refresh_current_subject_phase_projection()
            return True

        def _select_itemize_row_ordinal(self, ordinal: int) -> bool:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            _session, items = self._subject_projection_backend.itemization_session_and_items(
                root_path=self._root,
                scenario=scenario,
            )
            if not items:
                return False
            target_index = max(0, min(len(items) - 1, int(ordinal)))
            selected = items[target_index]
            progress.itemize_cursor = target_index
            progress.itemize_selected_item_id = collapse_ws(selected.itemized_item_id)
            self._mark_subject_progress_dirty(scenario)
            self._refresh_current_subject_phase_projection()
            return True

        def _hold_itemize_item(self) -> bool:
            if not self._itemize_focus_active():
                return False
            self._apply_mock_subject_action("itemize", "hold_selected_itemized_item")
            return True

        def _preview_itemize_item(self) -> bool:
            if not self._itemize_focus_active():
                return False
            self._apply_mock_subject_action("itemize", "preview_selected_itemized_item")
            return True

        def _move_draft_review_cursor(self, delta: int) -> bool:
            if not self._draft_workspace_focus_active():
                return False
            selected = self._subject_projection_backend.move_draft_review_cursor(
                root_path=self._root,
                scenario=self._mock_subject_scenario(),
                progress=self._mock_subject_progress(),
                delta=delta,
            )
            if selected is None:
                return False
            self._mark_subject_progress_dirty()
            primed_snapshot = self._prime_subject_snapshot_cache_from_backend("draft")
            self._refresh_draft_selection_live_panels(
                clear_snapshot_cache=not primed_snapshot,
                defer_model_controls=self._draft_model_mode_active(),
            )
            return True

        def _select_draft_row_ordinal(self, ordinal: int) -> bool:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            if self._draft_model_mode_active():
                candidates = self._subject_projection_backend.transformation_construct_candidates(
                    root_path=self._root,
                    scenario=scenario,
                    include_rejected=True,
                )
                if not candidates:
                    return False
                target_index = max(0, min(len(candidates) - 1, int(ordinal)))
                self._subject_projection_backend.set_draft_selection_to_construct_candidate_id(
                    root_path=self._root,
                    scenario=scenario,
                    progress=progress,
                    construct_candidate_id=candidates[target_index].construct_candidate_id,
                )
                self._mark_subject_progress_dirty(scenario)
                primed_snapshot = self._prime_subject_snapshot_cache_from_backend("draft")
                self._refresh_draft_selection_live_panels(
                    clear_snapshot_cache=not primed_snapshot,
                    defer_model_controls=True,
                )
                return True
            review_items = self._subject_projection_backend.flattened_draft_review_items(
                root_path=self._root,
                scenario=scenario,
            )
            if not review_items:
                return False
            target_index = max(0, min(len(review_items) - 1, int(ordinal)))
            selected_review_item, _selected_depth = review_items[target_index]
            self._subject_projection_backend.set_draft_selection_to_review_item_id(
                root_path=self._root,
                scenario=scenario,
                progress=progress,
                review_item_id=selected_review_item.review_item_id,
            )
            self._mark_subject_progress_dirty(scenario)
            primed_snapshot = self._prime_subject_snapshot_cache_from_backend("draft")
            self._refresh_draft_selection_live_panels(clear_snapshot_cache=not primed_snapshot)
            return True

        def _select_draft_row_ordinal_if_needed(self, ordinal: int) -> bool:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            if self._draft_model_mode_active():
                candidates = self._subject_projection_backend.transformation_construct_candidates(
                    root_path=self._root,
                    scenario=scenario,
                    include_rejected=True,
                )
                if not candidates:
                    return False
                target_index = max(0, min(len(candidates) - 1, int(ordinal)))
                selected = candidates[target_index]
                if collapse_ws(getattr(progress, "draft_selected_construct_candidate_id", "")) == collapse_ws(
                    selected.construct_candidate_id
                ):
                    return False
                return self._select_draft_row_ordinal(target_index)
            review_items = self._subject_projection_backend.flattened_draft_review_items(
                root_path=self._root,
                scenario=scenario,
            )
            if not review_items:
                return False
            target_index = max(0, min(len(review_items) - 1, int(ordinal)))
            selected_review_item, _selected_depth = review_items[target_index]
            if collapse_ws(getattr(progress, "draft_selected_review_item_id", "")) == collapse_ws(
                selected_review_item.review_item_id
            ):
                return False
            return self._select_draft_row_ordinal(target_index)

        def _sync_draft_scope_table_cursor_from_progress(
            self,
            *,
            schedule_after_refresh: bool = True,
        ) -> None:
            try:
                widget = self.query_one("#draft_scope_tree_panel")
            except Exception:
                return
            if TextualDataTable is None or not isinstance(widget, _FocusableTextualDataTable):
                return
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            if self._draft_model_mode_active():
                row_count = int(getattr(widget, "row_count", 0) or 0)
                if row_count <= 0:
                    return
                target_row = max(0, min(row_count - 1, int(getattr(progress, "draft_model_cursor", 0) or 0)))
            else:
                review_items = self._subject_projection_backend.flattened_draft_review_items(
                    root_path=self._root,
                    scenario=scenario,
                )
                if not review_items:
                    return
                selected_review_item_id = collapse_ws(getattr(progress, "draft_selected_review_item_id", ""))
                target_row = next(
                    (
                        index
                        for index, (review_item, _depth) in enumerate(review_items)
                        if collapse_ws(review_item.review_item_id) == selected_review_item_id
                    ),
                    max(0, min(len(review_items) - 1, int(getattr(progress, "itemize_cursor", 0) or 0))),
                )

            self._draft_cursor_sync_request_id = int(getattr(self, "_draft_cursor_sync_request_id", 0) or 0) + 1
            request_id = self._draft_cursor_sync_request_id

            def _move_cursor() -> None:
                if int(getattr(self, "_draft_cursor_sync_request_id", 0) or 0) != int(request_id):
                    return
                pending_counts = self._programmatic_data_table_cursor_event_counts.setdefault(
                    "draft_scope_tree_panel",
                    {},
                )
                pending_counts[int(target_row)] = int(pending_counts.get(int(target_row), 0) or 0) + 2
                self._inventory_option_sync_suppressed.add("draft_scope_tree_panel")
                try:
                    widget.move_cursor(row=int(target_row), column=0, animate=False, scroll=True)
                except Exception:
                    pass
                finally:
                    self._inventory_option_sync_suppressed.discard("draft_scope_tree_panel")

            _move_cursor()
            if schedule_after_refresh:
                scheduler = getattr(self, "call_after_refresh", None)
                if callable(scheduler):
                    try:
                        scheduler(_move_cursor)
                    except Exception:
                        pass

        def _mark_pending_data_table_cursor_action(self, widget_id: str, delta: int) -> None:
            normalized_widget_id = collapse_ws(str(widget_id or ""))
            normalized_delta = -1 if int(delta) < 0 else 1
            key = (normalized_widget_id, normalized_delta)
            self._pending_data_table_cursor_actions[key] = int(
                self._pending_data_table_cursor_actions.get(key, 0) or 0
            ) + 1

        def _consume_pending_data_table_cursor_action(self, widget_id: str, delta: int) -> bool:
            normalized_widget_id = collapse_ws(str(widget_id or ""))
            normalized_delta = -1 if int(delta) < 0 else 1
            key = (normalized_widget_id, normalized_delta)
            pending_count = int(self._pending_data_table_cursor_actions.get(key, 0) or 0)
            if pending_count <= 0:
                return False
            if pending_count <= 1:
                self._pending_data_table_cursor_actions.pop(key, None)
            else:
                self._pending_data_table_cursor_actions[key] = pending_count - 1
            return True

        def _move_selected_draft_review_item(self, delta: int) -> bool:
            if not self._draft_workspace_focus_active():
                return False
            action_key = (
                "move_selected_draft_review_item_earlier"
                if int(delta) < 0
                else "move_selected_draft_review_item_later"
            )
            self._apply_mock_subject_action("draft", action_key)
            return True

        def _toggle_draft_decision_included(self) -> bool:
            if not self._draft_workspace_focus_active():
                return False
            spec = self._mock_subject_draft_decision_included_spec()
            if not bool(getattr(spec, "enabled", False)):
                return False
            self._apply_mock_subject_action("draft", "toggle_selected_draft_review_item_in_decision_frame")
            return True

        def _move_review_scope_cursor(self, delta: int, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            selected = self._subject_projection_backend.move_report_scope_cursor(
                root_path=self._root,
                scenario=self._mock_subject_scenario(),
                progress=self._mock_subject_progress(),
                delta=delta,
            )
            if selected is None:
                return False
            self._mark_subject_progress_dirty()
            self._refresh_report_scope_live_panels(phase)
            self._focus_report_scope_tree(phase)
            return True

        def _focus_report_scope_tree(self, phase: str) -> None:
            widget_id = "publication_scope_tree_panel" if phase == "publication" else "review_scope_tree_panel"
            try:
                self.query_one(f"#{widget_id}").focus()
            except Exception:
                pass

        def _select_review_scope_row_ordinal(self, ordinal: int) -> bool:
            phase = self._report_scope_phase()
            if phase is None:
                return False
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            entries = self._subject_projection_backend.report_scope_entries(
                root_path=self._root,
                scenario=scenario,
                progress=progress,
            )
            selectable_entries = self._subject_projection_backend.selectable_report_scope_entries(entries)
            if not selectable_entries:
                return False
            progress.report_scope_cursor = max(0, min(len(selectable_entries) - 1, int(ordinal)))
            self._mark_subject_progress_dirty(scenario)
            self._refresh_report_scope_live_panels(phase)
            return True

        def _handle_inventory_option_highlight(self, widget_id: str, option_index: int) -> bool:
            normalized_widget_id = collapse_ws(str(widget_id or ""))
            if normalized_widget_id not in _TEXTUAL_OPTION_LIST_PANEL_IDS:
                return False
            if normalized_widget_id in self._inventory_option_sync_suppressed:
                return False
            if normalized_widget_id == "itemize_inventory_panel":
                try:
                    widget = self.query_one("#itemize_inventory_panel")
                except Exception:
                    return False
                typed_items = tuple(getattr(widget, "inventory_items", ()) or ())
                row_ordinal = int(option_index)
                if row_ordinal < 0 or row_ordinal >= len(typed_items):
                    return False
                scenario = self._mock_subject_scenario()
                progress = self._mock_subject_progress()
                _session, items = self._subject_projection_backend.itemization_session_and_items(
                    root_path=self._root,
                    scenario=scenario,
                )
                if not items:
                    return False
                target_index = max(0, min(len(items) - 1, row_ordinal))
                selected = items[target_index]
                if (
                    int(getattr(progress, "itemize_cursor", 0) or 0) == target_index
                    and collapse_ws(getattr(progress, "itemize_selected_item_id", "")) == collapse_ws(selected.itemized_item_id)
                ):
                    return False
                return self._select_itemize_row_ordinal(row_ordinal)
            return False

        def _select_research_source_row_ordinal_if_needed(self, row_ordinal: int) -> bool:
            progress = self._mock_subject_progress()
            scenario = self._mock_subject_scenario()
            _selected_collection, staged_sources = self._subject_projection_backend.staged_sources_for_selected_collection(
                root_path=self._root,
                subject_id=scenario.subject_id,
                progress=progress,
            )
            if not staged_sources:
                return False
            source_row_ordinal = max(0, min(len(staged_sources) - 1, int(row_ordinal)))
            selected = staged_sources[source_row_ordinal]
            if (
                int(getattr(progress, "research_source_cursor", 0) or 0) == source_row_ordinal
                and collapse_ws(getattr(progress, "research_selected_staged_source_id", "")) == collapse_ws(selected.staged_source_id)
            ):
                return False
            return self._select_research_row_ordinal(source_row_ordinal)

        def on_option_list_option_highlighted(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            option_list = getattr(event, "option_list", None)
            widget_id = str(getattr(option_list, "id", "") or "")
            option_index = int(getattr(event, "option_index", -1) or -1)
            if option_index < 0:
                return
            if self._handle_inventory_option_highlight(widget_id, option_index):
                try:
                    event.stop()
                except Exception:
                    pass

        def _handle_data_table_row_event(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            data_table = getattr(event, "data_table", None)
            widget_id = collapse_ws(str(getattr(data_table, "id", "") or ""))
            if widget_id in self._inventory_option_sync_suppressed:
                return
            cursor_row = int(getattr(event, "cursor_row", -1) or -1)
            if cursor_row < 0:
                return
            pending_programmatic_rows = self._programmatic_data_table_cursor_event_counts.get(widget_id) or {}
            pending_count = int(pending_programmatic_rows.get(cursor_row, 0) or 0)
            if pending_count > 0:
                if pending_count <= 1:
                    pending_programmatic_rows.pop(cursor_row, None)
                else:
                    pending_programmatic_rows[cursor_row] = pending_count - 1
                if not pending_programmatic_rows:
                    self._programmatic_data_table_cursor_event_counts.pop(widget_id, None)
                return
            if widget_id == "subject_sources_panel":
                row_to_source_ordinal = getattr(data_table, "_research_source_row_ordinals", {}) or {}
                source_row_ordinal = row_to_source_ordinal.get(cursor_row)
                if source_row_ordinal is None:
                    return
                if self._select_research_source_row_ordinal_if_needed(int(source_row_ordinal)):
                    try:
                        event.stop()
                    except Exception:
                        pass
                return
            if widget_id != "draft_scope_tree_panel":
                return
            if self._select_draft_row_ordinal_if_needed(cursor_row):
                try:
                    event.stop()
                except Exception:
                    pass

        def on_data_table_row_highlighted(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._handle_data_table_row_event(event)

        def on_data_table_row_selected(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._handle_data_table_row_event(event)

        def _handle_tree_selection_event(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            control = getattr(event, "control", None)
            widget_id = collapse_ws(str(getattr(control, "id", "") or ""))
            if widget_id not in _TEXTUAL_TREE_PANEL_IDS:
                return
            if widget_id in self._inventory_option_sync_suppressed:
                return
            node = getattr(event, "node", None)
            data = getattr(node, "data", None) or {}
            if not bool(data.get("selectable")):
                return
            selectable_index = data.get("selectable_index")
            if selectable_index is None:
                return
            if widget_id == "subject_sources_panel":
                if self._select_research_source_row_ordinal_if_needed(int(selectable_index)):
                    try:
                        event.stop()
                    except Exception:
                        pass
                return
            progress = self._mock_subject_progress()
            current_index = max(0, int(getattr(progress, "report_scope_cursor", 0) or 0))
            if current_index == int(selectable_index):
                return
            if self._select_review_scope_row_ordinal(int(selectable_index)):
                try:
                    event.stop()
                except Exception:
                    pass

        def on_tree_node_highlighted(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            return

        def on_tree_node_selected(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            self._handle_tree_selection_event(event)

        def on_tabs_tab_activated(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if TextualTabs is None or self._suppress_tabs_events or not self._tabs_events_ready:
                return
            tabs = getattr(event, "tabs", None)
            if collapse_ws(str(getattr(tabs, "id", "") or "")) != _draft_model_lens_tabs_id():
                return
            tab = getattr(event, "tab", None)
            tab_id = collapse_ws(str(getattr(tab, "id", "") or ""))
            action_key_by_tab_id = {
                _draft_model_lens_tab_id("frame"): "open_draft_model_frame_view",
                _draft_model_lens_tab_id("model"): "open_draft_model_model_view",
                _draft_model_lens_tab_id("explore"): "open_draft_model_explore_view",
            }
            action_key = action_key_by_tab_id.get(tab_id)
            current_lens = collapse_ws(str(getattr(self._mock_subject_progress(), "draft_model_lens", "") or "")).casefold()
            if current_lens not in {"frame", "model", "explore"}:
                current_lens = "model"
            if not action_key or not self._draft_model_mode_active() or tab_id == _draft_model_lens_tab_id(current_lens):
                return
            self._apply_mock_subject_action("draft", action_key)
            try:
                event.stop()
            except Exception:
                pass

        def _handle_focusable_textual_log_click(self, widget: Any, event: Any) -> bool:
            del event
            try:
                widget.focus()
            except Exception:
                pass
            return False

        def _preview_move_review_scope_items(self, delta: int, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            selected = self._subject_projection_backend.preview_move_held_report_scope_items(
                root_path=self._root,
                scenario=self._mock_subject_scenario(),
                progress=self._mock_subject_progress(),
                delta=delta,
            )
            if selected is None:
                return False
            self._refresh_report_scope_live_panels(phase)
            self._focus_report_scope_tree(phase)
            return True

        def _toggle_review_scope_item(self, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            self._apply_mock_subject_action(phase, "toggle_selected_report_scope_item")
            self._focus_report_scope_tree(phase)
            return True

        def _hold_review_scope_item(self, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            self._apply_mock_subject_action(phase, "hold_selected_report_scope_item")
            self._focus_report_scope_tree(phase)
            return True

        def _release_review_scope_items(self, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            self._apply_mock_subject_action(phase, "release_held_report_scope_items")
            self._focus_report_scope_tree(phase)
            return True

        def _preview_review_scope_item(self, phase_override: str | None = None) -> bool:
            phase = phase_override or self._report_scope_phase()
            if phase is None:
                return False
            self._apply_mock_subject_action(phase, "preview_selected_report_scope_item")
            self._focus_report_scope_tree(phase)
            return True

        def _permissions_text(self) -> str:
            return str(self._state.shell_permissions_text_cache or "")

        def _skills_text(self) -> str:
            return str(self._state.shell_skills_text_cache or "")

        def _learn_results_text(self) -> str:
            blocks: list[str] = []
            if collapse_ws(self._markdown_status_text):
                blocks.append(self._markdown_status_text)
            if isinstance(self._markdown_action_result, dict) and self._markdown_action_result:
                blocks.append(_workstation_action_result_text(self._markdown_action_result))
            if isinstance(self._markdown_export_result, dict) and self._markdown_export_result:
                blocks.append(_workstation_action_result_text(self._markdown_export_result))
            if not blocks:
                return "No learning actions yet."
            return "\n\n".join(blocks)

        def _learn_markdown_ingress_text(self) -> str:
            lines: list[str] = []
            if not (
                self._markdown_busy
                or self._markdown_selected_path is not None
                or self._markdown_pending_paths
                or collapse_ws(self._learning_source_label)
                or self._markdown_action_result
            ):
                return ""
            lines.append(collapse_ws(self._learning_ingress_title) or "Learning Ingress")
            lines.append(f"State: {'Running' if self._markdown_busy else 'Idle'}")
            if self._markdown_selected_path is not None:
                lines.append(f"Markdown: {self._markdown_selected_path}")
                if self._markdown_pending_paths:
                    pending_count = len(self._markdown_pending_paths)
                    lines.append(f"Queued: {pending_count} more file{'s' if pending_count != 1 else ''}")
                    preview_names = ", ".join(path.name for path in self._markdown_pending_paths[:3])
                    if preview_names:
                        lines.append(f"Up next: {preview_names}")
                    if pending_count > 3:
                        lines.append(f"Then: +{pending_count - 3} more")
            elif collapse_ws(self._learning_source_label):
                lines.append(
                    f"{collapse_ws(self._learning_source_field_label) or 'Source'}: {self._learning_source_label}"
                )
            if collapse_ws(self._markdown_status_text):
                lines.append(f"Stage: {self._markdown_status_text}")
            if self._markdown_busy and self._markdown_busy_started_at is not None:
                elapsed = max(0.0, time.monotonic() - self._markdown_busy_started_at)
                lines.append(f"Elapsed: ~{elapsed:.0f}s")
                dot_count = int(elapsed / 0.5) % 3 + 1
                lines.append(f"Progress: still working{'.' * dot_count}")
            elif self._markdown_action_result:
                final_status = collapse_ws(str(self._markdown_action_result.get("status", ""))) or "unknown"
                lines.append(f"Last result: {final_status}")
            return "\n".join(lines)

        def _refresh_learn_progress_tick(self) -> None:  # pragma: no cover - requires textual runtime
            if not self._markdown_busy:
                return
            if self._active_tab_id() == "learn_tab":
                self._schedule_active_tab_refresh()

        def _refresh_activity_pulse_tick(self) -> None:  # pragma: no cover - requires textual runtime
            if self._transcript_bottom_follow_active():
                try:
                    self._schedule_transcript_scroll_to_end()
                except Exception:
                    pass
            elif self._transcript_follow_bottom_until is not None:
                self._transcript_follow_bottom_until = None
            if self._state.advance_activity_pulse():
                try:
                    self._refresh_chat_activity_panel()
                except Exception:
                    return
                return
            if not self._state.expire_activity_strip_if_needed():
                return
            try:
                self._refresh_chat_activity_panel()
            except Exception:
                return

        def _apply_markdown_state_update(
            self,
            *,
            status_text: str | None = None,
            busy: bool | None = None,
            selected_path: Path | None | object = _UNSET,
            pending_paths: tuple[Path, ...] | list[Path] | object = _UNSET,
            source_label: str | None | object = _UNSET,
            source_field_label: str | None = None,
            ingress_title: str | None = None,
            action_result: dict[str, Any] | None | object = _UNSET,
            export_result: dict[str, Any] | None | object = _UNSET,
        ) -> None:
            if status_text is not None:
                self._markdown_status_text = collapse_ws(str(status_text))
            if selected_path is not _UNSET:
                self._markdown_selected_path = selected_path if isinstance(selected_path, Path) else None
            if pending_paths is not _UNSET:
                if isinstance(pending_paths, list | tuple):
                    self._markdown_pending_paths = tuple(path for path in pending_paths if isinstance(path, Path))
                else:
                    self._markdown_pending_paths = ()
            if source_label is not _UNSET:
                self._learning_source_label = collapse_ws(str(source_label or ""))
            if source_field_label is not None:
                self._learning_source_field_label = collapse_ws(str(source_field_label)) or "Source"
            if ingress_title is not None:
                self._learning_ingress_title = collapse_ws(str(ingress_title)) or "Learning Ingress"
            if action_result is not _UNSET:
                self._markdown_action_result = action_result if isinstance(action_result, dict) else None
            if export_result is not _UNSET:
                self._markdown_export_result = export_result if isinstance(export_result, dict) else None
            if busy is not None:
                next_busy = bool(busy)
                if next_busy and not self._markdown_busy:
                    self._markdown_busy_started_at = time.monotonic()
                if not next_busy:
                    self._markdown_busy_started_at = None
                self._markdown_busy = next_busy
            self.request_state_refresh()

        def _post_markdown_state_update(self, **kwargs: Any) -> None:
            try:
                self.call_from_thread(self._apply_markdown_state_update, **kwargs)
            except Exception:
                self._apply_markdown_state_update(**kwargs)

        def _start_learn_markdown_ingress(self) -> None:
            if self._state.is_busy():
                self._state.append_transcript_block(label="shell", text="A turn is already running.")
                return
            selected_paths = desktop_select_markdown_files(
                initial_directory=self._state.context.workspace_root or self._root,
            )
            if not selected_paths:
                self._apply_markdown_state_update(
                    ingress_title="Markdown Ingress",
                    source_field_label="Markdown",
                    source_label="",
                    status_text="Markdown selection canceled.",
                    busy=False,
                )
                return
            selected_path = selected_paths[0]
            pending_paths = tuple(selected_paths[1:])
            self._apply_markdown_state_update(
                selected_path=selected_path,
                pending_paths=pending_paths,
                source_label="",
                source_field_label="Markdown",
                ingress_title="Markdown Ingress",
                action_result=None,
                export_result=None,
                busy=True,
                status_text=(
                    f"Queued learning for {len(selected_paths)} markdown file{'s' if len(selected_paths) != 1 else ''}."
                ),
            )
            self._start_app_worker(
                target=self._learn_markdown_worker,
                args=(tuple(selected_paths),),
                name="learn-markdown-worker",
            )

        def _start_learn_url_ingress(self) -> None:
            if self._state.is_busy():
                self._state.append_transcript_block(label="shell", text="A turn is already running.")
                return
            selected_url = desktop_prompt_url(
                title="Learn URL",
                prompt="Enter a URL to learn from:",
                initial_value="https://",
            )
            if selected_url is None:
                self._apply_markdown_state_update(
                    ingress_title="URL Ingress",
                    source_field_label="URL",
                    source_label="",
                    status_text="URL selection canceled.",
                    busy=False,
                )
                return
            self._apply_markdown_state_update(
                selected_path=None,
                source_label=selected_url,
                source_field_label="URL",
                ingress_title="URL Ingress",
                action_result=None,
                export_result=None,
                busy=True,
                status_text="Queued learning for URL.",
            )
            self._start_app_worker(
                target=self._learn_url_worker,
                args=(selected_url,),
                name="learn-url-worker",
            )

        def action_cancel_or_interrupt(self) -> None:  # pragma: no cover - requires textual runtime
            input_widget = self.query_one("#input", TextualInput)
            if self._state.awaiting_approval():
                self._state.cancel_approval()
                input_widget.value = ""
                return
            if self._state.awaiting_research_capture():
                self._cancel_pending_research_capture()
                input_widget.value = ""
                return
            input_widget.value = ""
            self._state.clear_input_interrupted_notice()

        def action_copy_selected_text(self) -> None:  # pragma: no cover - requires textual runtime
            _textual_copy_selected_text(getattr(self, "screen", None), self)

        def action_copy_selection_or_cancel(self) -> None:  # pragma: no cover - requires textual runtime
            if _textual_copy_selected_text(getattr(self, "screen", None), self):
                return
            self.action_cancel_or_interrupt()

        def action_copy_transcript_text(self) -> None:  # pragma: no cover - requires textual runtime
            transcript = self.query_one("#transcript", TextualRichLog)
            if _textual_copy_selected_text_from_widget(transcript, self):
                return
            _textual_copy_text(self, self._state.transcript_text())

        def action_history_previous(self) -> None:  # pragma: no cover - requires textual runtime
            input_widget = self.query_one("#input", TextualInput)
            if self.focused is not input_widget:
                return
            current_value = collapse_ws(str(getattr(input_widget, "value", "") or ""))
            if current_value:
                self._move_selected_prompt_suggestion(-1)
                return
            if not self._history:
                return
            self._history_index = max(0, self._history_index - 1)
            self._set_input_from_history()

        def action_history_next(self) -> None:  # pragma: no cover - requires textual runtime
            input_widget = self.query_one("#input", TextualInput)
            if self.focused is not input_widget:
                return
            current_value = collapse_ws(str(getattr(input_widget, "value", "") or ""))
            if current_value:
                self._move_selected_prompt_suggestion(1)
                return
            if not self._history:
                return
            self._history_index = min(len(self._history), self._history_index + 1)
            self._set_input_from_history()

        def _set_input_from_history(self) -> None:  # pragma: no cover - requires textual runtime
            input_widget = self.query_one("#input", TextualInput)
            if self._history_index >= len(self._history):
                input_widget.value = ""
            else:
                input_widget.value = self._history[self._history_index]
            self._state.set_current_input_text(input_widget.value)

        def on_button_pressed(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            button_id = str(getattr(getattr(event, "button", None), "id", "") or "")
            if button_id.startswith("tab_button_"):
                target_tab = button_id[len("tab_button_") :]
                if target_tab in self._tab_ids():
                    if target_tab == "draft_tab":
                        self._dismiss_detached_pane()
                        current_phase = _SUBJECT_TAB_ID_TO_PHASE.get(self._active_tab_id(), "")
                        if current_phase in MOCK_SUBJECT_PHASES and current_phase != "draft":
                            self._apply_mock_subject_action(current_phase, "goto_draft")
                        else:
                            self._set_active_tab(target_tab)
                        return
                    self._set_active_tab(target_tab)
                return
            if button_id.startswith("suggestion_button_"):
                try:
                    suggestion_index = int(button_id.rsplit("_", 1)[-1])
                except Exception:
                    suggestion_index = -1
                suggestions = self._active_prompt_suggestions()
                if 0 <= suggestion_index < len(suggestions):
                    self._selected_prompt_suggestion_index = suggestion_index
                    self._apply_selected_prompt_suggestion()
                return
            if button_id == "subject_prev_button":
                self._step_mock_subject(-1)
                return
            if button_id == "subject_next_button":
                self._step_mock_subject(1)
                return
            if button_id == "copy_transcript_button":
                self.action_copy_transcript_text()
                return
            if button_id == _itemize_detail_llm_button_id():
                self._open_itemize_detail_in_chat()
                return
            if button_id == _research_sources_llm_button_id():
                self._open_research_sources_in_chat()
                return
            if button_id == _research_detail_llm_button_id():
                self._open_research_detail_in_chat()
                return
            if button_id == _research_sources_manual_rephrase_button_id():
                self._apply_mock_subject_action("research", "start_research_source_collection_manual_curation")
                return
            if button_id == _research_detail_manual_rephrase_button_id():
                self._apply_mock_subject_action("research", "start_research_source_manual_curation")
                return
            if button_id == _itemize_detail_manual_rephrase_button_id():
                self._apply_mock_subject_action("itemize", "start_itemize_manual_rephrase")
                return
            if button_id == _draft_detail_llm_button_id():
                self._open_draft_detail_in_chat()
                return
            if button_id == _draft_detail_manual_rephrase_button_id():
                self._apply_mock_subject_action("draft", "start_draft_manual_rephrase")
                return
            if button_id == _review_detail_llm_button_id():
                self._open_review_scope_detail_in_chat()
                return
            if button_id == _review_detail_manual_rephrase_button_id():
                self._apply_mock_subject_action("review", "start_review_section_manual_rephrase")
                return
            if button_id == _textual_detached_pane_info_button_id():
                self._dismiss_detached_pane()
                self._apply_active_tab_state()
                self._focus_first_panel_for_active_tab()
                return
            if button_id == _textual_detached_pane_dismiss_button_id():
                self._dismiss_detached_pane()
                self._apply_active_tab_state()
                self._focus_first_panel_for_active_tab()
                return
            for pane_id in _TEXTUAL_INFO_PANE_TABS:
                if button_id == _textual_pane_info_button_id(pane_id):
                    self._toggle_pane_info(pane_id)
                    return
            if button_id == _textual_pane_toggle_button_id("review_scope_tree_panel"):
                self._toggle_detached_pane_snapshot("review_scope_tree_panel")
                return
            for pane_id in _TEXTUAL_MAXIMIZABLE_PANES:
                if button_id == _textual_pane_toggle_button_id(pane_id):
                    self._toggle_maximized_pane_by_id(pane_id)
                    return
            for phase in ("draft", "itemize", "review", "publication"):
                if button_id == _subject_nav_button_id(phase, "prev"):
                    self._step_mock_subject(-1)
                    return
                if button_id == _subject_nav_button_id(phase, "next"):
                    self._step_mock_subject(1)
                    return
                if button_id == _subject_journal_button_id(phase):
                    self._toggle_maximized_pane_by_id(_subject_journal_pane_id(phase))
                    return
            if button_id == _subject_journal_button_id("research"):
                self._toggle_maximized_pane_by_id(_subject_journal_pane_id("research"))
                return
            for phase in ("research", "itemize"):
                if button_id == _subject_hidden_pane_button_id(phase):
                    pane_id = _subject_hidden_pane_id(phase)
                    if pane_id:
                        self._toggle_maximized_pane_by_id(pane_id)
                        self._schedule_active_tab_refresh()
                    return
            for phase in MOCK_SUBJECT_PHASES:
                action_button_ids = _subject_action_button_ids(phase)
                if button_id in action_button_ids:
                    action_map = {
                        action_button_ids[index]: spec
                        for index, spec in enumerate(self._mock_subject_control_specs(phase))
                    }
                    spec = action_map.get(button_id)
                    if spec is not None and spec.enabled:
                        self._apply_mock_subject_action(phase, spec.key)
                    return
                gate_button_ids = (
                    *_subject_gate_action_button_ids(phase, "review"),
                    *_subject_gate_action_button_ids(phase, "publication"),
                )
                if button_id in gate_button_ids:
                    target = self._subject_gate_action_targets.get(button_id)
                    if not target:
                        return
                    target_kind, target_key = target
                    if target_kind == "phase_nav":
                        if collapse_ws(str(target_key or "")).casefold() == "draft":
                            self._apply_mock_subject_action(phase, "goto_draft")
                            return
                        self._set_subject_phase(target_key)
                        return
                    if target_kind == "subject_nav":
                        self._apply_mock_subject_action(phase, target_key)
                        return
                    if target_kind == "subject_action":
                        self._apply_mock_subject_action(phase, target_key)
                        return
            if button_id == "learn_markdown_button":
                self._start_learn_markdown_ingress()
                return
            if button_id == "learn_url_button":
                self._start_learn_url_ingress()
                return
            if button_id == "export_learned_button":
                if not self._current_learned_bundle_payload() or self._markdown_busy:
                    return
                payload = self._current_learned_bundle_payload()
                canonical_export_path = Path(str(payload.get("canonical_export_path", ""))).expanduser()
                destination_path = desktop_select_skill_export_path(
                    default_filename=str(payload.get("suggested_export_filename", "") or canonical_export_path.name),
                    initial_directory=self._state.context.workspace_root or self._root,
                )
                if destination_path is None:
                    self._apply_markdown_state_update(
                        status_text="Skill export canceled.",
                        busy=False,
                    )
                    return
                self._apply_markdown_state_update(
                    busy=True,
                    status_text=f"Exporting learned skill to: {destination_path.name}",
                )
                self._start_app_worker(
                    target=self._export_learned_bundle_worker,
                    args=(destination_path,),
                    name="export-learned-bundle-worker",
                )
                return

        def on_select_changed(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if TextualSelect is None or self._suppress_select_events:
                return
            select = getattr(event, "select", None)
            select_id = str(getattr(select, "id", "") or "")
            raw_value = getattr(event, "value", TextualSelect.NULL)
            scheduler = getattr(self, "call_after_refresh", None)
            if not callable(scheduler):
                scheduler = getattr(self, "call_later", None)

            if select_id == _research_source_collection_select_id():
                spec = self._mock_subject_research_source_collection_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_source_collection_selection() -> None:
                    self._apply_mock_subject_action(
                        "research",
                        f"set_research_source_collection:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_source_collection_selection)
                    return
                _apply_source_collection_selection()
                return

            if select_id == _research_source_revision_baseline_select_id():
                spec = self._mock_subject_research_source_revision_baseline_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_source_revision_baseline_selection() -> None:
                    self._apply_mock_subject_action(
                        "research",
                        f"set_research_source_revision_baseline:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_source_revision_baseline_selection)
                    return
                _apply_source_revision_baseline_selection()
                return

            if select_id == _itemize_decision_role_select_id():
                spec = self._mock_subject_itemize_decision_role_spec()
                if not spec.enabled:
                    return
                selected_value = ""
                if raw_value is not TextualSelect.NULL:
                    selected_value = normalize_itemized_decision_role(str(raw_value or ""))
                if selected_value == normalize_itemized_decision_role(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_role_selection() -> None:
                    self._apply_mock_subject_action(
                        "itemize",
                        f"set_selected_itemized_item_decision_role:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_role_selection)
                    return
                _apply_role_selection()
                return

            if select_id == _draft_semantic_kind_select_id():
                spec = self._mock_subject_draft_semantic_kind_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_semantic_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_review_semantic_kind:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_semantic_selection)
                    return
                _apply_semantic_selection()
                return

            if select_id == _draft_render_kind_select_id():
                spec = self._mock_subject_draft_render_kind_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_render_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_review_render_kind:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_render_selection)
                    return
                _apply_render_selection()
                return

            if select_id == _draft_evidence_mode_select_id():
                spec = self._mock_subject_draft_evidence_mode_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_evidence_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_review_evidence_mode:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_evidence_selection)
                    return
                _apply_evidence_selection()
                return

            if select_id == _draft_transform_mode_select_id():
                spec = self._mock_subject_draft_transform_mode_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_transform_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_review_transform_mode:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_transform_selection)
                    return
                _apply_transform_selection()
                return

            if select_id == _draft_model_construct_sort_select_id():
                spec = self._mock_subject_draft_model_construct_sort_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_construct_sort_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_construct_sort:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_construct_sort_selection)
                    return
                _apply_construct_sort_selection()
                return

            if select_id == _draft_model_construct_lane_select_id():
                spec = self._mock_subject_draft_model_construct_lane_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_construct_lane_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_construct_lane:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_construct_lane_selection)
                    return
                _apply_construct_lane_selection()
                return

            if select_id == _draft_model_transition_source_select_id():
                spec = self._mock_subject_draft_model_transition_source_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_transition_source_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_construct_transition_source:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_transition_source_selection)
                    return
                _apply_transition_source_selection()
                return

            if select_id == _draft_model_transition_target_select_id():
                spec = self._mock_subject_draft_model_transition_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_transition_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_selected_draft_construct_transition_target:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_transition_target_selection)
                    return
                _apply_transition_target_selection()
                return

            if select_id == _draft_model_policy_profile_select_id():
                spec = self._mock_subject_draft_model_policy_profile_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_policy_profile_selection() -> None:
                    self._apply_mock_subject_action(
                        "draft",
                        f"set_decision_policy_profile:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_policy_profile_selection)
                    return
                _apply_policy_profile_selection()
                return

            if select_id == _review_publication_output_mode_select_id():
                spec = self._mock_subject_review_publication_output_mode_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_output_mode_selection() -> None:
                    self._apply_mock_subject_action(
                        "review",
                        f"set_publication_output_mode:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_output_mode_selection)
                    return
                _apply_output_mode_selection()
                return

            if select_id == _review_publication_section_plan_select_id():
                spec = self._mock_subject_review_publication_section_plan_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_section_plan_selection() -> None:
                    self._apply_mock_subject_action(
                        "review",
                        f"set_publication_section_plan:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_section_plan_selection)
                    return
                _apply_section_plan_selection()
                return

            if select_id == _review_publication_diff_baseline_select_id():
                spec = self._mock_subject_review_publication_diff_baseline_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_diff_baseline_selection() -> None:
                    self._apply_mock_subject_action(
                        "review",
                        f"set_publication_diff_baseline:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_diff_baseline_selection)
                    return
                _apply_diff_baseline_selection()
                return

            if select_id == _review_composition_unit_target_select_id():
                spec = self._mock_subject_review_composition_unit_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_review_unit_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "review",
                        f"set_selected_composition_unit:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_review_unit_target_selection)
                    return
                _apply_review_unit_target_selection()
                return

            if select_id == _review_publication_section_target_select_id():
                spec = self._mock_subject_review_publication_section_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_review_section_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "review",
                        f"set_selected_publication_section:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_review_section_target_selection)
                    return
                _apply_review_section_target_selection()
                return

            if select_id == _publication_output_mode_select_id():
                spec = self._mock_subject_publication_output_mode_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_output_mode_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_publication_output_mode:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_output_mode_selection)
                    return
                _apply_publication_output_mode_selection()
                return

            if select_id == _publication_section_plan_select_id():
                spec = self._mock_subject_publication_section_plan_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_section_plan_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_publication_section_plan:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_section_plan_selection)
                    return
                _apply_publication_section_plan_selection()
                return

            if select_id == _publication_diff_baseline_select_id():
                spec = self._mock_subject_publication_diff_baseline_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_diff_baseline_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_publication_diff_baseline:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_diff_baseline_selection)
                    return
                _apply_publication_diff_baseline_selection()
                return

            if select_id == _publication_import_target_select_id():
                spec = self._mock_subject_publication_import_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_import_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_publication_import_target:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_import_target_selection)
                    return
                _apply_publication_import_target_selection()
                return

            if select_id == _publication_composition_unit_target_select_id():
                spec = self._mock_subject_publication_composition_unit_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_unit_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_selected_composition_unit:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_unit_target_selection)
                    return
                _apply_publication_unit_target_selection()
                return

            if select_id == _publication_section_target_select_id():
                spec = self._mock_subject_publication_section_target_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_section_target_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_selected_publication_section:{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_section_target_selection)
                    return
                _apply_publication_section_target_selection()
                return

            if select_id == _publication_import_usage_select_id():
                spec = self._mock_subject_publication_import_usage_spec()
                if not spec.enabled:
                    return
                selected_value = collapse_ws(str(raw_value or "")) if raw_value is not TextualSelect.NULL else ""
                if selected_value == collapse_ws(spec.value):
                    return
                try:
                    select.expanded = False
                except Exception:
                    pass

                def _apply_publication_import_usage_selection() -> None:
                    self._apply_mock_subject_action(
                        "publication",
                        f"set_selected_publication_import_usage_{selected_value}",
                    )

                if callable(scheduler):
                    scheduler(_apply_publication_import_usage_selection)
                    return
                _apply_publication_import_usage_selection()
                return

        def on_selection_list_selected_changed(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if TextualSelectionList is None or self._suppress_selection_list_events:
                return
            selection_list = getattr(event, "selection_list", None)
            selection_list_id = str(getattr(selection_list, "id", "") or "")
            if not selection_list_id.startswith("draft_model_relation_selection_list_"):
                return
            try:
                slot = int(selection_list_id.rsplit("_", 1)[-1])
            except Exception:
                return
            specs = self._mock_subject_draft_model_relation_specs()
            if slot < 0 or slot >= len(specs):
                return
            spec = specs[slot]
            if not spec.enabled:
                return
            selected_id_set = {
                collapse_ws(str(value))
                for value in getattr(selection_list, "selected", ())
                if collapse_ws(str(value))
            }
            selected_values = tuple(
                value
                for _label, value, _selected in spec.options
                if collapse_ws(value) in selected_id_set
            )
            current_values = tuple(
                value
                for _label, value, selected in spec.options
                if selected
            )
            if selected_values == current_values:
                return

            def _apply_relation_selection() -> None:
                self._apply_mock_subject_action(
                    "draft",
                    f"{spec.action_key_prefix}{','.join(selected_values)}",
                )

            _apply_relation_selection()

        def on_switch_changed(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if TextualSwitch is None or self._suppress_switch_events:
                return
            switch = getattr(event, "switch", None)
            switch_id = str(getattr(switch, "id", "") or "")
            target_value = bool(getattr(event, "value", False))
            if self._consume_programmatic_switch_change(switch_id, target_value):
                return
            if switch_id == _research_source_collection_membership_switch_id():
                spec = self._mock_subject_research_selected_source_collection_membership_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return

                def _apply_membership_toggle() -> None:
                    self._apply_mock_subject_action("research", "toggle_selected_staged_source_in_collection")

                scheduler = getattr(self, "call_after_refresh", None)
                if callable(scheduler):
                    scheduler(_apply_membership_toggle)
                    return
                scheduler = getattr(self, "call_later", None)
                if callable(scheduler):
                    scheduler(_apply_membership_toggle)
                    return
                _apply_membership_toggle()
                return
            if switch_id == _itemize_hold_switch_id():
                spec = self._mock_subject_itemize_hold_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("itemize", "hold_selected_itemized_item")
                return
            if switch_id == _draft_decision_included_switch_id():
                spec = self._mock_subject_draft_decision_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("draft", "toggle_selected_draft_review_item_in_decision_frame")
                return
            if switch_id == _publication_import_included_switch_id():
                spec = self._mock_subject_publication_import_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("publication", "toggle_selected_publication_import")
                return
            if switch_id == _publication_composition_unit_included_switch_id():
                spec = self._mock_subject_publication_composition_unit_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("publication", "toggle_selected_composition_unit")
                return
            if switch_id == _publication_section_included_switch_id():
                spec = self._mock_subject_publication_section_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("publication", "toggle_selected_publication_section")
                return
            if switch_id == _review_composition_unit_included_switch_id():
                spec = self._mock_subject_review_composition_unit_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("review", "toggle_selected_composition_unit")
                return
            if switch_id == _review_publication_section_included_switch_id():
                spec = self._mock_subject_review_publication_section_included_spec()
                if not spec.enabled:
                    return
                if target_value == bool(spec.value):
                    return
                self._apply_mock_subject_action("review", "toggle_selected_publication_section")

        def on_click(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            widget = getattr(event, "widget", None)
            widget_id = str(getattr(widget, "id", "") or "")
            target_id = _TEXTUAL_CLICK_FOCUS_TARGETS.get(widget_id)
            if not target_id:
                return
            try:
                self.query_one(f"#{target_id}").focus()
            except Exception:
                return
            if hasattr(event, "stop"):
                event.stop()

        def on_input_changed(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if getattr(event.input, "id", "") != "input":
                return
            self._state.set_current_input_text(str(getattr(event, "value", "") or ""), refresh=False)
            self._selected_prompt_suggestion_index = 0
            self._refresh_inline_hint()
            self._refresh_prompt_suggestions()

        def on_input_submitted(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            if getattr(event.input, "id", "") != "input":
                return
            prompt = str(getattr(event, "value", "") or "").strip()
            canonical_prompt = canonical_workstation_chat_slash_command_text(prompt)
            if not prompt:
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                return
            if self._state.awaiting_approval():
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                if not self._state.resolve_approval_from_input(prompt):
                    self._state.append_transcript_block(label="shell", text="Reply yes or no.")
                return
            if self._state.awaiting_research_capture():
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                normalized_answer = collapse_ws(prompt).casefold()
                if normalized_answer in {"y", "yes"}:
                    self._confirm_pending_research_capture(prompt_text=prompt)
                    return
                if normalized_answer in {"n", "no"}:
                    self._cancel_pending_research_capture(prompt_text=prompt)
                    return
                normalized_pending_command = canonical_workstation_chat_slash_command_text(prompt)
                pending_command_name, _, pending_raw_args = normalized_pending_command.partition(" ")
                if pending_command_name == "/start-research-into":
                    subject_override = pending_raw_args.strip()
                    self._handle_start_research_command_with_override(subject_override, prompt_text=prompt)
                    return
                self._record_shell_status_turn(
                    prompt_text=prompt,
                    shell_text="Reply yes to stage, no to cancel, or use /start-research-into <subject title>.",
                )
                return
            prompt_target_plan = workstation_chat_prompt_target_plan_via_shell(
                shell_client=self._shell_client,
                root_path=self._root,
                prompt_text=prompt,
            )
            if prompt_target_plan is not None:
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                if prompt_target_plan.kind == "switch_research":
                    if prompt_target_plan.move_to_research:
                        self._set_subject_phase("research")
                    if prompt_target_plan.shell_text:
                        self._record_shell_status_turn(prompt_text=prompt, shell_text=prompt_target_plan.shell_text)
                    return
                if prompt_target_plan.kind == "shell":
                    self._record_shell_status_turn(prompt_text=prompt, shell_text=prompt_target_plan.shell_text)
                    return
                if self._state.is_busy():
                    self._state.append_transcript_block(label="shell", text="A turn is already running.")
                    return
                if prompt_target_plan.kind == "research_action":
                    command_name = collapse_ws(prompt_target_plan.command_name)
                    if not self._handle_research_chat_action_target(command_name, prompt_target_plan.command_arguments):
                        spec = _RESEARCH_CHAT_ACTION_TARGET_SPECS.get(command_name, {})
                        self._record_shell_status_turn(
                            prompt_text=prompt,
                            shell_text=str(spec.get("missing_text", "This Gather maintenance action is not available right now.")),
                        )
                    return
                if prompt_target_plan.kind == "research_follow_up":
                    command_name = collapse_ws(prompt_target_plan.command_name)
                    if not self._handle_research_chat_prompt_target(command_name):
                        spec = _RESEARCH_CHAT_PROMPT_TARGET_SPECS.get(command_name, {})
                        self._record_shell_status_turn(
                            prompt_text=prompt,
                            shell_text=str(spec.get("missing_text", "This Gather chat target is not available right now.")),
                        )
                    return
                if prompt_target_plan.kind == "prepare_last_assistant_markdown":
                    llm_prompt = str(prompt_target_plan.llm_prompt or "")
                    if not collapse_ws(llm_prompt):
                        self._record_shell_status_turn(
                            prompt_text=prompt,
                            shell_text=prompt_target_plan.shell_text,
                        )
                        return
                    self._state.append_transcript_block(label="user", text=prompt)
                    if _SHOW_ROUTED_LLM_PROMPT_IN_TRANSCRIPT:
                        self._state.append_transcript_block(
                            label="user",
                            text=prompt_target_plan.shell_text,
                        )
                    self._pin_transcript_to_bottom()
                    _append_workstation_prompt_history(self._root, prompt)
                    self._history.append(prompt)
                    self._history = self._history[-500:]
                    self._history_index = len(self._history)
                    self._start_app_worker(
                        target=_run_enhanced_workstation_turn_worker,
                        kwargs={
                            "state": self._state,
                            "prompt": llm_prompt,
                            "model": self._model,
                            "max_tool_rounds": self._max_tool_rounds,
                            "force_llm_only": True,
                        },
                        name="chat-llm-only-worker",
                    )
                    return
                if prompt_target_plan.kind == "start_research":
                    self._handle_start_research_command_with_override(
                        prompt_target_plan.subject_title,
                        prompt_text=prompt,
                    )
                    return
                if prompt_target_plan.kind == "llm_prompt":
                    llm_only = canonical_workstation_chat_slash_command_text(prompt).partition(" ")[0] in {
                        "/prepare-markdown",
                        "/prepare-last-assistant-markdown",
                    }
                    self._state.append_transcript_block(label="user", text=prompt)
                    if _SHOW_ROUTED_LLM_PROMPT_IN_TRANSCRIPT:
                        self._state.append_transcript_block(
                            label="user",
                            text=workstation_chat_routed_llm_prompt_text(prompt_target_plan.llm_prompt),
                        )
                    self._pin_transcript_to_bottom()
                    _append_workstation_prompt_history(self._root, prompt)
                    self._history.append(prompt)
                    self._history = self._history[-500:]
                    self._history_index = len(self._history)
                    if prompt_target_plan.move_to_research:
                        self._set_subject_phase("research")
                    self._start_app_worker(
                        target=_run_enhanced_workstation_turn_worker,
                        kwargs={
                            "state": self._state,
                            "prompt": prompt_target_plan.llm_prompt,
                            "model": self._model,
                            "max_tool_rounds": self._max_tool_rounds,
                            "force_llm_only": llm_only,
                        },
                        name="chat-routed-llm-worker",
                    )
                    return
            if canonical_prompt == "/help":
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                self._record_shell_status_turn(
                    prompt_text=prompt,
                    shell_text=workstation_chat_help_text(self._state.context),
                )
                return
            if canonical_prompt in {"/exit", "/quit"}:
                event.input.value = ""
                self._state.set_current_input_text("", refresh=False)
                self._refresh_inline_hint()
                self.exit(0)
                return
            if self._state.is_busy():
                self._state.append_transcript_block(label="shell", text="A turn is already running.")
                self._pin_transcript_to_bottom()
                return
            event.input.value = ""
            self._state.set_current_input_text("", refresh=False)
            self._refresh_inline_hint()
            self._state.append_transcript_block(label="user", text=prompt)
            self._pin_transcript_to_bottom()
            _append_workstation_prompt_history(self._root, prompt)
            self._history.append(prompt)
            self._history = self._history[-500:]
            self._history_index = len(self._history)
            self._start_app_worker(
                target=_run_enhanced_workstation_turn_worker,
                kwargs={
                    "state": self._state,
                    "prompt": prompt,
                    "model": self._model,
                    "max_tool_rounds": self._max_tool_rounds,
                },
                name="chat-submit-worker",
            )

        def on_key(self, event: Any) -> None:  # pragma: no cover - requires textual runtime
            transcript = self.query_one("#transcript", TextualRichLog)
            if self.focused is transcript and getattr(event, "key", "") in {"up", "down"}:
                self._clear_transcript_bottom_follow()
                direction = -1 if event.key == "up" else 1
                try:
                    transcript.scroll_relative(y=direction)
                except Exception:
                    pass
                event.stop()

        def _current_learned_bundle_payload(self) -> dict[str, Any]:
            payload = self._markdown_action_result.get("payload", {}) if isinstance(self._markdown_action_result, dict) else {}
            if not isinstance(payload, dict):
                return {}
            if not collapse_ws(str(payload.get("canonical_export_path", ""))):
                return {}
            return payload

        def _apply_subject_ingress_result_from_worker(
            self,
            *,
            phase: str,
            scenario: MockSubjectScenario,
            progress: MockSubjectProgress,
            action_key: str,
            result: Any,
        ) -> None:
            applied = threading.Event()

            def _apply() -> None:
                try:
                    self._apply_mock_subject_action_result(phase, scenario, progress, action_key, result)
                finally:
                    applied.set()

            try:
                self.call_from_thread(_apply)
            except Exception:
                _apply()
            applied.wait(timeout=5)

        def _learn_markdown_worker(self, selected_paths: tuple[Path, ...]) -> None:
            total_paths = len(selected_paths)
            for index, selected_path in enumerate(selected_paths, start=1):
                pending_paths = tuple(selected_paths[index:])
                try:
                    self._post_markdown_state_update(
                        selected_path=selected_path,
                        pending_paths=pending_paths,
                        source_label="",
                        source_field_label="Markdown",
                        ingress_title="Markdown Ingress",
                        action_result=None,
                        export_result=None,
                        busy=True,
                        status_text=(
                            f"Importing {selected_path.name} through the subject workflow service..."
                            if total_paths == 1
                            else f"Importing {selected_path.name} through the subject workflow service ({len(pending_paths)} queued)."
                        ),
                    )
                    scenario = self._mock_subject_scenario()
                    progress = self._mock_subject_progress()
                    result = self._subject_projection_backend.apply_action(
                        root_path=self._root,
                        subject_id=collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", "")),
                        action_key="use_markdown_ingress",
                        phase="research",
                        progress=progress,
                        **{
                            **self._subject_phase_projection_kwargs(),
                            "markdown_selected_path": str(selected_path),
                            "markdown_status_text": "Markdown upload staged.",
                            "markdown_busy": True,
                        },
                    )
                    self._post_markdown_state_update(
                        action_result=None,
                        export_result=None,
                        busy=bool(pending_paths),
                        selected_path=selected_path,
                        pending_paths=pending_paths,
                        source_label="",
                        source_field_label="Markdown",
                        ingress_title="Markdown Ingress",
                        status_text=collapse_ws(str(getattr(result, "status_text", ""))) or f"Imported {selected_path.name}.",
                    )
                    self._apply_subject_ingress_result_from_worker(
                        phase="research",
                        scenario=scenario,
                        progress=progress,
                        action_key="use_markdown_ingress",
                        result=result,
                    )
                except Exception as exc:
                    self._post_markdown_state_update(
                        action_result=None,
                        export_result=None,
                        busy=False,
                        selected_path=selected_path,
                        pending_paths=(),
                        source_label="",
                        source_field_label="Markdown",
                        ingress_title="Markdown Ingress",
                        status_text=f"Markdown intake failed: {exc}",
                    )
                    try:
                        self.call_from_thread(setattr, self, "_mock_subject_status_text", f"Markdown intake failed: {exc}")
                    except Exception:
                        self._mock_subject_status_text = f"Markdown intake failed: {exc}"
                    return

        def _learn_url_worker(self, selected_url: str) -> None:
            scenario = self._mock_subject_scenario()
            progress = self._mock_subject_progress()
            try:
                self._post_markdown_state_update(
                    selected_path=None,
                    source_label=selected_url,
                    source_field_label="URL",
                    ingress_title="URL Ingress",
                    busy=True,
                    status_text=f"Importing {selected_url} through the subject workflow service...",
                )
                result = self._subject_projection_backend.apply_action(
                    root_path=self._root,
                    subject_id=collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", "")),
                    action_key="use_url_ingress",
                    phase="research",
                    progress=progress,
                    assistant_message_text=selected_url,
                    subject_title_override="" if scenario.is_placeholder else scenario.title,
                    **self._subject_phase_projection_kwargs(assistant_message_text=selected_url),
                )
                self._post_markdown_state_update(
                    action_result=None,
                    export_result=None,
                    busy=False,
                    selected_path=None,
                    source_label=selected_url,
                    source_field_label="URL",
                    ingress_title="URL Ingress",
                    status_text=collapse_ws(str(getattr(result, "status_text", ""))) or f"Queued URL intake for {selected_url}.",
                )
                self._apply_subject_ingress_result_from_worker(
                    phase="research",
                    scenario=scenario,
                    progress=progress,
                    action_key="use_url_ingress",
                    result=result,
                )
            except Exception as exc:
                self._post_markdown_state_update(
                    action_result=None,
                    export_result=None,
                    busy=False,
                    selected_path=None,
                    source_label=selected_url,
                    source_field_label="URL",
                    ingress_title="URL Ingress",
                    status_text=f"URL intake failed: {exc}",
                )
                try:
                    self.call_from_thread(setattr, self, "_mock_subject_status_text", f"URL intake failed: {exc}")
                except Exception:
                    self._mock_subject_status_text = f"URL intake failed: {exc}"

        def _export_learned_bundle_worker(self, destination_path: Path) -> None:
            payload = self._current_learned_bundle_payload()
            if not payload:
                self._post_markdown_state_update(busy=False)
                return
            canonical_export_path = Path(str(payload.get("canonical_export_path", ""))).expanduser()
            if not str(canonical_export_path).strip():
                self._post_markdown_state_update(busy=False)
                return
            result = workstation_export_learned_skill_bundle_action(
                root_path=self._root,
                source_bundle_path=canonical_export_path,
                destination_path=destination_path,
            ).to_dict()
            self._post_markdown_state_update(
                export_result=result,
                busy=False,
                status_text=(
                f"Exported learned skill to: {destination_path.name}"
                if collapse_ws(str(result.get("status", ""))) == "ok"
                else f"Export failed: {destination_path.name}"
                ),
            )

    def _run_textual_workstation_chat_loop(
        *,
        root: Path,
        model: str | None,
        max_tool_rounds: int,
        subject_workflow_client: SubjectWorkflowClient,
    ) -> int:
        app = _TextualWorkstationChatApp(
            root=Path(root).expanduser().resolve(),
            model=model,
            max_tool_rounds=max_tool_rounds,
            subject_workflow_client=subject_workflow_client,
        )
        result = app.run()
        try:
            return int(result or 0)
        except Exception:
            return 0

else:

    _TextualWorkstationChatApp = None

    def _run_textual_workstation_chat_loop(
        *,
        root: Path,
        model: str | None,
        max_tool_rounds: int,
        subject_workflow_client: SubjectWorkflowClient,
    ) -> int:
        del subject_workflow_client
        raise RuntimeError("Textual is not available.")


def run_enhanced_workstation_chat_loop(
    *,
    root: Path,
    model: str | None,
    max_tool_rounds: int,
    subject_workflow_client: SubjectWorkflowClient | None = None,
) -> int:
    """
    High Level Purpose:
        In circumstances like interactive workstation terminal usage, helps with running the ANSI/readline-enhanced chat frontend while leaving prompt execution and permission handling in the existing workstation session layer.

    Reference to Theory:
        Supports separation of concerns by making the richer terminal UX a host-owned outer shell over the unchanged workstation session and skill runtime.

    Example Input Output:
        Input: `run_enhanced_workstation_chat_loop(root=Path('/tmp/ws'), model='gpt-5.4', max_tool_rounds=8)`
        Output: 0

    Args:
        root: Value for `root` used by `root`. Expected type: `Path`.
        model: Value for `model` used by `model`. Expected type: `str | None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`.

    Returns:
        int: Result produced by `run_enhanced_workstation_chat_loop`.
    """
    resolved_subject_workflow_client = (
        subject_workflow_client or _create_textual_subject_workflow_client()
    )
    if TextualApp is not None:
        return _run_textual_workstation_chat_loop(
            root=root,
            model=model,
            max_tool_rounds=max_tool_rounds,
            subject_workflow_client=resolved_subject_workflow_client,
        )
    if Application is None or TextArea is None or KeyBindings is None or Layout is None or HSplit is None:
        raise RuntimeError("Textual or prompt_toolkit is required for the enhanced workstation chat frontend.")
    return _run_prompt_toolkit_workstation_chat_loop(
        root=root,
        model=model,
        max_tool_rounds=max_tool_rounds,
        subject_workflow_client=resolved_subject_workflow_client,
    )


def _run_prompt_toolkit_workstation_chat_loop(
    *,
    root: Path,
    model: str | None,
    max_tool_rounds: int,
    subject_workflow_client: SubjectWorkflowClient,
) -> int:
    if Application is None or TextArea is None or KeyBindings is None or Layout is None or HSplit is None:
        raise RuntimeError("prompt_toolkit is required for the enhanced workstation chat frontend fallback.")
    root_path = Path(root).expanduser().resolve()
    state = _WorkstationChatPaneState(
        root=root_path,
        context=workstation_chat_context(root_path),
        transcript_entries=_initial_transcript_entries(root_path),
    )
    prompt_subject_workflow_client = subject_workflow_client
    prompt_subject_projection_backend = TextualSubjectWorkflowProjectionBackend(prompt_subject_workflow_client)
    chat_history = _workstation_prompt_history(root_path)
    prompt_subject_progress_by_key: dict[str, MockSubjectProgress] = {}
    prompt_subject_preferred_key = ""

    def _prompt_subject_scenario_and_progress() -> tuple[MockSubjectScenario, MockSubjectProgress]:
        nonlocal prompt_subject_preferred_key
        scenarios = _list_mock_subject_scenarios_via_api(
            root_path,
            client=prompt_subject_workflow_client,
        )
        if not scenarios:
            raise RuntimeError("No subject scenarios are available.")
        scenario = scenarios[0]
        if prompt_subject_preferred_key:
            for candidate in scenarios:
                if candidate.key == prompt_subject_preferred_key:
                    scenario = candidate
                    break
        progress = prompt_subject_progress_by_key.get(scenario.key)
        if progress is None:
            progress = (
                prompt_subject_projection_backend.load_progress(
                    root_path=root_path,
                    subject_id=scenario.subject_id,
                )
                if not scenario.is_placeholder and collapse_ws(scenario.subject_id)
                else new_mock_subject_progress()
            )
            prompt_subject_progress_by_key[scenario.key] = progress
        prompt_subject_preferred_key = scenario.key
        return scenario, progress

    def _prompt_apply_subject_action(
        *,
        phase: str,
        scenario: MockSubjectScenario,
        progress: MockSubjectProgress,
        action_key: str,
        assistant_message_text: str = "",
        subject_title_override: str = "",
    ) -> tuple[Any, MockSubjectProgress]:
        subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
        if (
            not prompt_subject_projection_backend.uses_in_process_service()
            and not getattr(scenario, "is_placeholder", False)
            and collapse_ws(getattr(scenario, "subject_id", ""))
        ):
            prompt_subject_projection_backend.persist_progress(
                root_path=root_path,
                subject_id=collapse_ws(getattr(scenario, "subject_id", "")),
                progress=progress,
            )
        result = prompt_subject_projection_backend.apply_action(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            action_key=action_key,
            progress=progress,
            assistant_message_text=assistant_message_text,
            subject_title_override=subject_title_override,
        )
        refreshed_progress = (
            prompt_subject_projection_backend.load_progress(root_path=root_path, subject_id=subject_id)
            if not getattr(scenario, "is_placeholder", False) and subject_id
            else new_mock_subject_progress()
        )
        prompt_subject_progress_by_key[scenario.key] = refreshed_progress
        return result, refreshed_progress

    def _sync_prompt_subject_research_capture_state(progress: MockSubjectProgress) -> None:
        if prompt_subject_projection_backend.has_pending_research_capture(progress):
            state.begin_research_capture(
                _PendingResearchCapture(
                    markdown_text="",
                    command_text="",
                    subject_title_override="",
                    preview_report={
                        "canonical_title": prompt_subject_projection_backend.pending_research_capture_target(progress),
                    },
                )
            )
            return
        state.clear_pending_research_capture()

    def _prompt_selected_research_source_collection(
        *,
        scenario: MockSubjectScenario,
        progress: MockSubjectProgress,
    ) -> Any:
        if getattr(scenario, "is_placeholder", False):
            return None
        collections = prompt_subject_projection_backend.source_collections(
            root_path=root_path,
            scenario=scenario,
            progress=progress,
        )
        if not collections:
            return None
        selected_id = collapse_ws(getattr(progress, "research_selected_source_collection_id", ""))
        if selected_id:
            for collection in collections:
                if collapse_ws(getattr(collection, "collection_id", "")) == selected_id:
                    return collection
        index = max(0, min(len(collections) - 1, int(getattr(progress, "research_collection_cursor", 0) or 0)))
        return collections[index]

    def _prompt_research_follow_up_prompt(
        *,
        command_name: str,
        scenario: MockSubjectScenario,
        progress: MockSubjectProgress,
    ) -> str:
        if getattr(scenario, "is_placeholder", False):
            return ""
        subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
        if not subject_id:
            return ""
        prompt_subject_projection_backend.persist_progress(
            root_path=root_path,
            subject_id=subject_id,
            progress=progress,
        )
        pane_bundle = prompt_subject_projection_backend.get_snapshot(
            root_path=root_path,
            subject_id=subject_id,
            phase="research",
        ).pane_bundle
        detail_title = _pane_view_title_by_key(pane_bundle, "research_target")
        detail_text = _pane_view_text_by_key(pane_bundle, "research_target")
        sources_text = _pane_view_text_by_key(pane_bundle, "research_sources")
        observation_text = _pane_view_text_by_key(pane_bundle, "research_observation")
        selected_collection = _prompt_selected_research_source_collection(scenario=scenario, progress=progress)
        selected_collection_title = (
            collapse_ws(getattr(selected_collection, "title", ""))
            or collapse_ws(getattr(selected_collection, "collection_id", ""))
        )
        collection_kind = collapse_ws(str(getattr(selected_collection, "metadata", {}).get("collection_kind", "")))
        query_text = collapse_ws(getattr(selected_collection, "query_text", ""))
        if command_name == "/curate-source":
            if not detail_text or detail_title == "Source Detail":
                return ""
            return (
                "Curate this selected staged source in Gather.\n"
                "Treat it as source material only, not as admitted corpus truth and not as publication prose.\n"
                "You may de-jargonize, clarify, summarize, reorganize headings, or make the source easier to maintain for future import.\n"
                "Do not turn it into final report language.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<short source title>\n\n"
                "[text]\n"
                "<curated source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected staged source: {detail_title}\n\n"
                "Source details:\n"
                f"{detail_text}"
            )
        if command_name == "/merge-source":
            if not detail_text or detail_title == "Current subject assets" or not observation_text:
                return ""
            return (
                "Prepare a merge-back proposal for this selected staged source.\n"
                "Use the current subject learnings to improve the staged source notes while keeping them at the source layer.\n"
                "Do not treat the result as admitted corpus truth and do not turn it into publication prose.\n"
                "Return only this format:\n"
                "[label]\n"
                "<updated staged source title>\n\n"
                "[text]\n"
                "<updated staged source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected staged source: {detail_title}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Source details and export preview:\n"
                f"{detail_text}"
            )
        if selected_collection is None or collection_kind == "all_gather_sources":
            return ""
        if command_name == "/curate-source-set":
            if not sources_text:
                return ""
            return (
                "Curate this selected Gather source set.\n"
                "Treat it as source-management metadata only, not as admitted corpus truth and not as publication prose.\n"
                "You may improve the set title, describe what belongs in the set, and refine the saved topic/query text.\n"
                "Do not rewrite the individual source bodies here.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<source set title>\n\n"
                "[description]\n"
                "<what belongs in this source set and how it should be maintained>\n\n"
                "[query]\n"
                "<saved topic or query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {selected_collection_title}\n\n"
                "Source-set details:\n"
                f"{sources_text}"
            )
        if command_name == "/find-sources":
            if not query_text or not sources_text:
                return ""
            return (
                "Find high-value source material for this selected Gather source set.\n"
                "Treat the result as staged source discovery only, not as admitted corpus truth and not as publication prose.\n"
                "Use the saved query/topic and the current source-set context.\n"
                "Prefer direct source URLs and avoid duplicates.\n\n"
                "Return only this format, repeating one block per source:\n\n"
                "[source]\n"
                "[label]\n"
                "<short source title>\n\n"
                "[url]\n"
                "<direct source url>\n\n"
                "[notes]\n"
                "<why this source is relevant and how it should be used at the source layer>\n\n"
                "Provide up to 5 sources.\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {selected_collection_title}\n"
                f"Saved query/topic: {query_text}\n\n"
                "Source-set details:\n"
                f"{sources_text}"
            )
        if command_name == "/synthesize-source-set":
            if not sources_text:
                return ""
            return (
                "Synthesize this selected Gather source set into a maintained source-layer knowledgebase summary.\n"
                "Treat the result as staged source-set metadata only, not as admitted corpus truth and not as publication prose.\n"
                "Summarize what the set currently covers, what remains missing or uncertain, and how the saved query/topic should evolve.\n"
                "Do not rewrite the individual staged source bodies here.\n\n"
                "Return only this format:\n"
                "[summary]\n"
                "<what this source set currently covers and how it should be used>\n\n"
                "[questions]\n"
                "<one open question per line; may be blank>\n\n"
                "[query]\n"
                "<updated saved topic/query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {selected_collection_title}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and current knowledgebase state:\n"
                f"{detail_text}"
            )
        if command_name == "/merge-source-set":
            if not sources_text or not observation_text:
                return ""
            return (
                "Prepare a merge-back proposal for this selected Gather source set.\n"
                "Use the current subject learnings to improve the source-set notes and saved query so future discovery and maintenance reflect what the subject now knows.\n"
                "Keep the result at the source layer only. Do not treat it as admitted corpus truth, do not turn it into publication prose, and do not rewrite the individual staged source bodies here.\n\n"
                "Return only this format:\n"
                "[label]\n"
                "<source set title>\n\n"
                "[description]\n"
                "<updated source-set notes and maintenance framing>\n\n"
                "[query]\n"
                "<updated saved topic or query text; may be blank>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {selected_collection_title}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and export preview:\n"
                f"{detail_text}"
            )
        if command_name == "/merge-set-sources":
            if not sources_text or not observation_text or not detail_text:
                return ""
            return (
                "Prepare merge-back proposals for the member staged sources in this selected Gather source set.\n"
                "Use the current subject learnings to improve the staged source notes while keeping them at the source layer.\n"
                "Do not treat the result as admitted corpus truth and do not turn it into publication prose.\n"
                "Update only the staged sources that clearly need changes.\n\n"
                "Return only this format, repeating one block per staged source that should change:\n\n"
                "[source]\n"
                "[url]\n"
                "<existing staged source url>\n\n"
                "[label]\n"
                "<updated staged source title>\n\n"
                "[text]\n"
                "<updated staged source markdown>\n\n"
                f"Subject: {collapse_ws(str(getattr(scenario, 'title', ''))) or '<unknown>'}\n"
                f"Selected source set: {selected_collection_title}\n\n"
                "Current learned subject state:\n"
                f"{observation_text}\n\n"
                "Source-set workspace:\n"
                f"{sources_text}\n\n"
                "Source-set detail and member export targets:\n"
                f"{detail_text}"
            )
        return ""

    def _submit_prompt_follow_up_in_chat(*, started_text: str, prompt_text: str) -> None:
        state.record_shell_message(text=started_text)
        _scroll_window_to_end(transcript_body, state.transcript_cursor_text())
        if application is not None:
            try:
                application.invalidate()
            except Exception:
                pass
        worker = threading.Thread(
            target=_run_enhanced_workstation_turn_worker,
            kwargs={
                "state": state,
                "prompt": prompt_text,
                "model": model,
                "max_tool_rounds": max_tool_rounds,
            },
            daemon=True,
        )
        worker.start()

    def _handle_prompt_research_action_command(command_name: str, arguments_text: str = "") -> None:
        nonlocal prompt_subject_preferred_key
        spec = _RESEARCH_CHAT_ACTION_TARGET_SPECS.get(collapse_ws(command_name), {})
        scenario, progress = _prompt_subject_scenario_and_progress()
        result, progress = _prompt_apply_subject_action(
            phase="research",
            scenario=scenario,
            progress=progress,
            action_key=str(spec.get("action_key", "")),
            assistant_message_text=str(arguments_text or _latest_transcript_assistant_text(state)),
        )
        _sync_prompt_subject_research_capture_state(progress)
        if result.reload_subjects:
            state.refresh_context()
            if result.preferred_subject_key:
                prompt_subject_preferred_key = result.preferred_subject_key
        open_failures: list[str] = []
        for open_path in getattr(result, "open_paths", ()) or ():
            if not desktop_open_path(Path(str(open_path))):
                open_failures.append(str(open_path))
        message_lines = [collapse_ws(result.status_text)]
        message_lines.extend(str(line).rstrip() for line in getattr(progress, "latest_receipt_lines", ()) if collapse_ws(str(line)))
        if open_failures:
            message_lines.append(f"Unable to open: {', '.join(open_failures)}")
        message = "\n".join(line for line in message_lines if collapse_ws(line)).rstrip()
        state.record_shell_message(
            text=message or str(spec.get("missing_text", "This Gather maintenance action is not available right now.")),
            prompt_text=collapse_ws(command_name),
        )

    def _handle_prompt_research_follow_up_command(command_name: str) -> None:
        nonlocal prompt_subject_preferred_key
        spec = _RESEARCH_CHAT_PROMPT_TARGET_SPECS.get(collapse_ws(command_name), {})
        scenario, progress = _prompt_subject_scenario_and_progress()
        prompt_text = _prompt_research_follow_up_prompt(
            command_name=collapse_ws(command_name),
            scenario=scenario,
            progress=progress,
        )
        if not collapse_ws(prompt_text):
            state.record_shell_message(
                text=str(spec.get("missing_text", "This Gather chat target is not available right now.")),
                prompt_text=collapse_ws(command_name),
            )
            return
        result, progress = _prompt_apply_subject_action(
            phase="research",
            scenario=scenario,
            progress=progress,
            action_key=str(spec.get("action_key", "")),
            assistant_message_text=_latest_transcript_assistant_text(state),
        )
        _sync_prompt_subject_research_capture_state(progress)
        if result.reload_subjects:
            state.refresh_context()
            if result.preferred_subject_key:
                prompt_subject_preferred_key = result.preferred_subject_key
        progress_field = collapse_ws(str(spec.get("progress_field", "")))
        if not collapse_ws(str(getattr(progress, progress_field, "") or "")):
            state.record_shell_message(
                text=result.status_text or str(spec.get("missing_text", "This Gather chat target is not available right now.")),
                prompt_text=collapse_ws(command_name),
            )
            return
        _submit_prompt_follow_up_in_chat(
            started_text=str(spec.get("started_text", "")),
            prompt_text=prompt_text,
        )

    header_window = Window(
        content=FormattedTextControl(lambda: _ui_prompt_text(state.banner_text())),
        height=5,
        dont_extend_height=True,
    )
    activity_control = FormattedTextControl(
        text=lambda: state.activity_text(),
        focusable=False,
        show_cursor=False,
    )
    activity_body = Window(
        content=activity_control,
        right_margins=[ScrollbarMargin(display_arrows=True)] if ScrollbarMargin is not None else [],
        wrap_lines=True,
        always_hide_cursor=True,
    )
    activity_window = Frame(
        activity_body,
        title=workstation_pane_title("chat", "activity"),
        height=10,
    )
    transcript_body: Any = None
    transcript_control = FormattedTextControl(
        text=lambda: _ui_prompt_text(state.transcript_ansi_text()),
        focusable=True,
        show_cursor=True,
        get_cursor_position=lambda: _window_scroll_cursor_position(transcript_body, state.transcript_cursor_text()),
    )
    transcript_body = Window(
        content=transcript_control,
        right_margins=[ScrollbarMargin(display_arrows=True)] if ScrollbarMargin is not None else [],
        wrap_lines=True,
        always_hide_cursor=False,
        cursorline=True,
    )
    transcript_window = Frame(
        transcript_body,
        title=workstation_pane_title("chat", "transcript"),
    )
    suggestions_window = Window(
        content=FormattedTextControl(lambda: _ui_prompt_text(state.suggestions_text())),
        height=1,
        dont_extend_height=True,
    )
    status_window = Window(
        content=FormattedTextControl(lambda: _ui_prompt_text(state.input_status_text())),
        height=1,
        dont_extend_height=True,
    )
    input_field = TextArea(
        multiline=False,
        wrap_lines=False,
        completer=_PromptToolkitChatCompleter(state),
        complete_while_typing=True,
        history=chat_history,
        accept_handler=lambda _buffer: (_submit_from_input() or True),
    )
    try:
        input_field.buffer.on_text_changed.add_handler(lambda _event: state.set_current_input_text(input_field.text))
    except Exception:
        pass

    key_bindings = KeyBindings()

    @key_bindings.add("f6")
    def _handle_focus_next(event) -> None:  # pragma: no cover - requires prompt_toolkit runtime
        event.app.layout.focus_next()

    @key_bindings.add("c-f6")
    def _handle_focus_previous(event) -> None:  # pragma: no cover - requires prompt_toolkit runtime
        event.app.layout.focus_previous()

    @key_bindings.add("up", filter=has_focus(transcript_control) if has_focus is not None else True)
    def _handle_transcript_up(event) -> None:  # pragma: no cover - requires prompt_toolkit runtime
        _scroll_window_linewise(transcript_body, -1)
        event.app.invalidate()

    @key_bindings.add("down", filter=has_focus(transcript_control) if has_focus is not None else True)
    def _handle_transcript_down(event) -> None:  # pragma: no cover - requires prompt_toolkit runtime
        _scroll_window_linewise(transcript_body, 1)
        event.app.invalidate()

    @key_bindings.add("c-c")
    def _handle_ctrl_c(event) -> None:  # pragma: no cover - requires prompt_toolkit runtime
        if state.awaiting_approval():
            state.cancel_approval()
            input_field.buffer.text = ""
            return
        if state.awaiting_research_capture():
            scenario, progress = _prompt_subject_scenario_and_progress()
            result, progress = _prompt_apply_subject_action(
                phase="research",
                scenario=scenario,
                progress=progress,
                action_key="cancel_assistant_capture",
            )
            _sync_prompt_subject_research_capture_state(progress)
            if result.status_text:
                state.record_shell_message(text=result.status_text)
            input_field.buffer.text = ""
            return
        input_field.buffer.text = ""
        state.clear_input_interrupted_notice()

    def _submit_from_input() -> None:
        nonlocal prompt_subject_preferred_key
        prompt = str(input_field.text or "").strip()
        canonical_prompt = canonical_workstation_chat_slash_command_text(prompt)
        if not prompt:
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            return
        if state.awaiting_approval():
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            if not state.resolve_approval_from_input(prompt):
                state.record_shell_message(text="Reply yes or no.", prompt_text=prompt)
            return
        if state.awaiting_research_capture():
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            normalized_answer = collapse_ws(prompt).casefold()
            scenario, progress = _prompt_subject_scenario_and_progress()
            if normalized_answer in {"y", "yes"}:
                result, progress = _prompt_apply_subject_action(
                    phase="research",
                    scenario=scenario,
                    progress=progress,
                    action_key="confirm_assistant_capture",
                    assistant_message_text="",
                )
                _sync_prompt_subject_research_capture_state(progress)
                if result.reload_subjects:
                    state.refresh_context()
                    if result.preferred_subject_key:
                        prompt_subject_preferred_key = result.preferred_subject_key
                if result.status_text:
                    if (
                        progress.latest_receipt_lines
                        and not prompt_subject_projection_backend.has_pending_research_capture(progress)
                    ):
                        state.record_shell_message(
                            text="\n".join([result.status_text, *progress.latest_receipt_lines]).rstrip(),
                            prompt_text=prompt,
                        )
                    else:
                        state.record_shell_message(text=result.status_text, prompt_text=prompt)
                return
            if normalized_answer in {"n", "no"}:
                result, progress = _prompt_apply_subject_action(
                    phase="research",
                    scenario=scenario,
                    progress=progress,
                    action_key="cancel_assistant_capture",
                    assistant_message_text="",
                )
                _sync_prompt_subject_research_capture_state(progress)
                if result.status_text:
                    state.record_shell_message(text=result.status_text, prompt_text=prompt)
                return
            normalized_pending_command = canonical_workstation_chat_slash_command_text(prompt)
            pending_command_name, _, pending_raw_args = normalized_pending_command.partition(" ")
            if pending_command_name == "/start-research-into":
                result, progress = _prompt_apply_subject_action(
                    phase="research",
                    scenario=scenario,
                    progress=progress,
                    action_key="stage_assistant_capture",
                    assistant_message_text=_latest_transcript_assistant_text(state),
                    subject_title_override=pending_raw_args.strip(),
                )
                _sync_prompt_subject_research_capture_state(progress)
                if progress.latest_receipt_lines:
                    state.record_shell_message(
                        text="\n".join(
                            [
                                result.status_text,
                                *progress.latest_receipt_lines,
                                "",
                                "Reply yes to stage, no to cancel, or use /start-research-into <subject title> to choose another subject.",
                            ]
                        ).rstrip(),
                        prompt_text=prompt,
                    )
                elif result.status_text:
                    state.record_shell_message(text=result.status_text, prompt_text=prompt)
                return
            state.record_shell_message(
                text="Reply yes to stage, no to cancel, or use /start-research-into <subject title>.",
                prompt_text=prompt,
            )
            return
        prompt_target_plan = workstation_chat_prompt_target_plan_via_shell(
            shell_client=state.shell_client,
            root_path=root_path,
            prompt_text=prompt,
        )
        if prompt_target_plan is not None:
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            if prompt_target_plan.kind == "switch_research":
                if prompt_target_plan.shell_text:
                    state.record_shell_message(text=prompt_target_plan.shell_text, prompt_text=prompt)
                return
            if prompt_target_plan.kind == "shell":
                state.record_shell_message(text=prompt_target_plan.shell_text, prompt_text=prompt)
                return
            if state.is_busy():
                state.append_transcript_block(label="shell", text="A turn is already running.")
                return
            if prompt_target_plan.kind == "research_action":
                _handle_prompt_research_action_command(
                    prompt_target_plan.command_name,
                    prompt_target_plan.command_arguments,
                )
                return
            if prompt_target_plan.kind == "research_follow_up":
                _handle_prompt_research_follow_up_command(prompt_target_plan.command_name)
                return
            if prompt_target_plan.kind == "prepare_last_assistant_markdown":
                llm_prompt = str(prompt_target_plan.llm_prompt or "")
                if not collapse_ws(llm_prompt):
                    state.record_shell_message(text=prompt_target_plan.shell_text, prompt_text=prompt)
                    return
                state.append_transcript_block(label="user", text=prompt)
                if _SHOW_ROUTED_LLM_PROMPT_IN_TRANSCRIPT:
                    state.append_transcript_block(
                        label="user",
                        text=prompt_target_plan.shell_text,
                    )
                _scroll_window_to_end(transcript_body, state.transcript_cursor_text())
                if application is not None:
                    try:
                        application.invalidate()
                    except Exception:
                        pass
                worker = threading.Thread(
                    target=_run_enhanced_workstation_turn_worker,
                    kwargs={
                        "state": state,
                        "prompt": llm_prompt,
                        "model": model,
                        "max_tool_rounds": max_tool_rounds,
                        "force_llm_only": True,
                    },
                    daemon=True,
                )
                worker.start()
                return
            if prompt_target_plan.kind == "start_research":
                scenario, progress = _prompt_subject_scenario_and_progress()
                result, progress = _prompt_apply_subject_action(
                    phase="research",
                    scenario=scenario,
                    progress=progress,
                    action_key="stage_assistant_capture",
                    assistant_message_text=_latest_transcript_assistant_text(state),
                    subject_title_override=prompt_target_plan.subject_title,
                )
                _sync_prompt_subject_research_capture_state(progress)
                if progress.latest_receipt_lines:
                    state.record_shell_message(
                        text="\n".join(
                            [
                                result.status_text,
                                *progress.latest_receipt_lines,
                                "",
                                "Reply yes to stage, no to cancel, or use /start-research-into <subject title> to choose another subject.",
                            ]
                        ).rstrip(),
                        prompt_text=prompt,
                    )
                elif result.status_text:
                    state.record_shell_message(text=result.status_text, prompt_text=prompt)
                return
            if prompt_target_plan.kind == "llm_prompt":
                llm_only = canonical_workstation_chat_slash_command_text(prompt).partition(" ")[0] in {
                    "/prepare-markdown",
                    "/prepare-last-assistant-markdown",
                }
                state.append_transcript_block(label="user", text=prompt)
                if _SHOW_ROUTED_LLM_PROMPT_IN_TRANSCRIPT:
                    state.append_transcript_block(
                        label="user",
                        text=workstation_chat_routed_llm_prompt_text(prompt_target_plan.llm_prompt),
                    )
                _scroll_window_to_end(transcript_body, state.transcript_cursor_text())
                if application is not None:
                    try:
                        application.invalidate()
                    except Exception:
                        pass
                worker = threading.Thread(
                    target=_run_enhanced_workstation_turn_worker,
                    kwargs={
                        "state": state,
                        "prompt": prompt_target_plan.llm_prompt,
                        "model": model,
                        "max_tool_rounds": max_tool_rounds,
                        "force_llm_only": llm_only,
                    },
                    daemon=True,
                )
                worker.start()
                return
        if canonical_prompt == "/help":
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            state.record_shell_message(text=workstation_chat_help_text(state.context), prompt_text=prompt)
            return
        if canonical_prompt in {"/exit", "/quit"}:
            input_field.buffer.text = ""
            state.set_current_input_text("", refresh=False)
            if application is not None:
                application.exit(result=0)
            return
        if state.is_busy():
            state.append_transcript_block(label="shell", text="A turn is already running.")
            return
        input_field.buffer.text = ""
        state.set_current_input_text("", refresh=False)
        state.append_transcript_block(label="user", text=prompt)
        _scroll_window_to_end(transcript_body, state.transcript_cursor_text())
        if application is not None:
            try:
                application.invalidate()
            except Exception:
                pass
        worker = threading.Thread(
            target=_run_enhanced_workstation_turn_worker,
            kwargs={
                "state": state,
                "prompt": prompt,
                "model": model,
                "max_tool_rounds": max_tool_rounds,
            },
            daemon=True,
        )
        worker.start()

    layout = Layout(
        HSplit(
            [
                header_window,
                activity_window,
                transcript_window,
                suggestions_window,
                status_window,
                Frame(
                    input_field,
                    title=workstation_pane_title("chat", "composer"),
                    height=4,
                ),
            ]
        ),
        focused_element=input_field,
    )
    application = Application(
        layout=layout,
        key_bindings=key_bindings,
        full_screen=True,
        mouse_support=True,
    )
    state.application = application
    state.projection_controller = WorkstationProjectionSubscriberController(
        root_path=root_path,
        activity_limit=_ACTIVITY_PANE_MAX_LINES,
    )
    state.projection_controller.start(
        on_activity_line=state.append_activity_line,
        on_context_invalidated=state.refresh_context,
        on_projection_invalidated=state.invalidate,
    )
    try:
        return int(application.run() or 0)
    finally:
        state.stop_projection_controller()


def _run_enhanced_workstation_turn_worker(
    *,
    state: _WorkstationChatPaneState,
    prompt: str,
    model: str | None,
    max_tool_rounds: int,
    force_llm_only: bool = False,
) -> None:
    state.start_turn()
    try:
        report = state.shell_client.submit_chat_input(
            root_path=state.root,
            prompt_text=prompt,
            model=model,
            max_tool_rounds=max_tool_rounds,
            force_llm_only=force_llm_only,
        )
        state.apply_shell_snapshot(report)
    except Exception as exc:
        state.record_shell_message(text=f"Turn failed: {exc}")
    finally:
        state.finish_turn()


def _prompt_for_workstation_escalation_in_pane(
    state: _WorkstationChatPaneState,
    request: WorkstationDelegationEscalationRequest,
) -> WorkstationDelegationEscalationDecision:
    event = state.begin_approval(request)
    event.wait()
    return state.take_approval_decision()


def prompt_for_workstation_escalation_enhanced(
    request: WorkstationDelegationEscalationRequest,
) -> WorkstationDelegationEscalationDecision:
    """
    High Level Purpose:
        In circumstances like interactive workstation skill escalation, helps with presenting a styled approval prompt and simple yes/no completion while keeping the approval decision at the host shell boundary.

    Reference to Theory:
        Supports the workstation permission model by making escalation approval explicit and host-owned even in the richer terminal frontend.

    Example Input Output:
        Input: `prompt_for_workstation_escalation_enhanced(request=3)`
        Output: WorkstationDelegationEscalationDecision(approved=True, scope='one_invocation', rationale='User approved interactive workstation escalation.')

    Args:
        request: Value for `request` used by `request`. Expected type: `WorkstationDelegationEscalationRequest`.

    Returns:
        WorkstationDelegationEscalationDecision: Result produced by `prompt_for_workstation_escalation_enhanced`.
    """
    delegated_lines = ", ".join(
        f"{item.get('capability', '')}({item.get('target', '')})"
        for item in request.requested_delegation
    ) or "no additional rights listed"
    _ui_print(
        f"{_ANSI_YELLOW}Escalation requested{_ANSI_RESET}: "
        f"skill={request.skill_title or '<unknown>'}, "
        f"rights={delegated_lines}, "
        f"scope={request.scope}"
    )
    answer = ""
    if PromptSession is not None:
        session = PromptSession(
            completer=_PromptToolkitChoiceCompleter(_YES_NO_CHOICES),
            complete_while_typing=True,
        )
        try:
            answer = session.prompt(_ui_prompt_text(f"{_ANSI_BOLD}Approve? [yes/no]{_ANSI_RESET} ")).strip().casefold()
        except KeyboardInterrupt:
            _ui_print(f"{_ANSI_DIM}Escalation canceled.{_ANSI_RESET}")
            answer = ""
        except EOFError:
            answer = ""
    else:
        try:
            answer = input(_plain_ui_text(f"{_ANSI_BOLD}Approve? [yes/no]{_ANSI_RESET} ")).strip().casefold()
        except KeyboardInterrupt:
            _ui_print(f"{_ANSI_DIM}Escalation canceled.{_ANSI_RESET}")
            answer = ""
        except EOFError:
            answer = ""
    if answer in {"y", "yes"}:
        return WorkstationDelegationEscalationDecision(
            approved=True,
            scope=request.scope,
            rationale="User approved interactive workstation escalation.",
        )
    return WorkstationDelegationEscalationDecision(
        approved=False,
        scope=request.scope,
        rationale="User denied interactive workstation escalation.",
    )


class _PromptToolkitChatCompleter(Completer):
    def __init__(self, state: _WorkstationChatPaneState) -> None:
        self._state = state

    def get_completions(self, document, complete_event):  # pragma: no cover - requires prompt_toolkit runtime
        if self._state.awaiting_approval():
            for choice in _YES_NO_CHOICES:
                yield Completion(choice, start_position=-len(document.text_before_cursor))
            return
        buffer_text = str(document.text_before_cursor or "")
        for candidate in workstation_chat_completion_candidates(
            context=self._state.context,
            buffer_text=buffer_text,
        ):
            if not candidate:
                continue
            yield Completion(candidate, start_position=-len(document.text_before_cursor))


class _PromptToolkitChoiceCompleter(Completer):
    def __init__(self, choices: Iterable[str]) -> None:
        self._choices = tuple(_ordered_unique_non_empty_strings(list(choices)))

    def get_completions(self, document, complete_event):  # pragma: no cover - requires prompt_toolkit runtime
        buffer_text = collapse_ws(str(document.text_before_cursor or "")).casefold()
        for choice in self._choices:
            if not buffer_text or choice.casefold().startswith(buffer_text):
                yield Completion(choice, start_position=-len(document.text_before_cursor))


def _read_workstation_skill_catalog(root: Path) -> dict[str, Any]:
    skills_path = Path(root) / "SKILLS.json"
    if not skills_path.exists():
        return {}
    try:
        parsed = json.loads(skills_path.read_text())
    except Exception:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _workspace_relative_paths(workspace_root: Path | None) -> list[str]:
    if workspace_root is None or not workspace_root.exists():
        return []
    collected: list[str] = []
    root = Path(workspace_root).expanduser().resolve()
    pending: deque[Path] = deque([root])
    while pending and len(collected) < _WORKSPACE_PATH_SCAN_LIMIT:
        current_path = pending.popleft()
        try:
            relative_root = current_path.relative_to(root)
        except ValueError:
            continue
        relative_root_text = relative_root.as_posix()
        is_root_directory = relative_root_text in {"", "."}
        if not is_root_directory:
            collected.append(relative_root.as_posix() + "/")
            if len(collected) >= _WORKSPACE_PATH_SCAN_LIMIT:
                break
        try:
            with os.scandir(current_path) as iterator:
                for entry in iterator:
                    name = str(getattr(entry, "name", "") or "")
                    if not name or name.startswith("."):
                        continue
                    relative_entry = (relative_root / name) if str(relative_root) else Path(name)
                    try:
                        is_directory = entry.is_dir(follow_symlinks=False)
                    except OSError:
                        continue
                    if is_directory:
                        pending.append(Path(entry.path))
                        if is_root_directory:
                            collected.append(Path(name).as_posix() + "/")
                        else:
                            collected.append(relative_entry.as_posix() + "/")
                    else:
                        if is_root_directory:
                            collected.append(Path(name).as_posix())
                        else:
                            collected.append(relative_entry.as_posix())
                    if len(collected) >= _WORKSPACE_PATH_SCAN_LIMIT:
                        break
        except OSError:
            continue
    return sorted(_ordered_unique_non_empty_strings(collected))


def _ordered_unique_non_empty_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        value = collapse_ws(str(raw))
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _ui_print(text: str) -> None:
    rendered = str(text or "")
    if print_formatted_text is not None and ANSI is not None:
        try:
            print_formatted_text(ANSI(rendered))
            return
        except Exception:
            pass
    sys.stdout.write(rendered + "\n")
    sys.stdout.flush()


def _ui_prompt_text(text: str) -> Any:
    rendered = str(text or "")
    if ANSI is not None:
        try:
            return ANSI(rendered)
        except Exception:
            pass
    return rendered


def _ui_activity_text(text: str) -> str:
    rendered = collapse_ws(str(text))
    if not rendered:
        return ""
    return f"{_ANSI_DIM}activity{_ANSI_RESET} {rendered}"


_ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def _plain_ui_text(text: str) -> str:
    return _ANSI_PATTERN.sub("", str(text or ""))


def _context_can_suggest_workspace_paths(context: WorkstationChatContext) -> bool:
    capabilities = {collapse_ws(str(item)) for item in context.allowed_capabilities}
    return bool(
        capabilities.intersection(
            {
                "ws.repo.tree",
                "ws.repo.search",
                "ws.fs.read",
            }
        )
    )


def _grantable_capability_candidates(context: WorkstationChatContext) -> list[str]:
    granted = {collapse_ws(str(item)) for item in context.allowed_capabilities}
    return [
        capability
        for capability in _all_known_workstation_capabilities()
        if capability not in granted
    ]


def _revocable_capability_candidates(context: WorkstationChatContext) -> list[str]:
    protected = {"ws.skill.catalog", "ws.skill.import", "ws.skill.export"}
    return [
        capability
        for capability in _ordered_unique_non_empty_strings(context.allowed_capabilities)
        if capability not in protected
    ]


def _all_known_workstation_capabilities() -> list[str]:
    return _ordered_unique_non_empty_strings(AVAILABLE_WORKSTATION_CAPABILITIES)


def _slash_export_skill_completion_candidates(
    *,
    context: WorkstationChatContext,
    stripped: str,
) -> list[str]:
    suffix = stripped[len("/export-skill ") :]
    if suffix.startswith('"'):
        closing_quote = suffix.find('"', 1)
        if closing_quote < 0:
            prefix = suffix[1:].casefold()
            return [
                f'/export-skill "{title}"'
                for title in context.skill_titles
                if title.casefold().startswith(prefix)
            ]
        skill_title = collapse_ws(suffix[1:closing_quote])
        if not skill_title:
            return []
        trailing = suffix[closing_quote + 1 :]
        path_prefix = trailing.lstrip()
        if not _context_can_suggest_workspace_paths(context):
            return [f'/export-skill "{skill_title}"'] if not path_prefix else []
        candidates = [
            candidate
            for candidate in context.workspace_paths
            if candidate.startswith(path_prefix)
        ]
        if not candidates and not path_prefix:
            candidates = list(context.workspace_paths)
        return [
            f'/export-skill "{skill_title}" {candidate}'
            for candidate in candidates
        ]
    prefix = suffix.casefold()
    return [
        f'/export-skill "{title}"'
        for title in context.skill_titles
        if title.casefold().startswith(prefix)
    ]


def _workstation_prompt_history(root: Path) -> Any:
    history_path = workstation_chat_history_path(root)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    if FileHistory is not None:
        try:
            return FileHistory(str(history_path))
        except Exception:
            pass
    return None


def _workstation_prompt_history_entries(root: Path) -> list[str]:
    history_path = workstation_chat_history_path(root)
    if not history_path.exists():
        return []
    try:
        return [
            line.rstrip("\n")
            for line in history_path.read_text(encoding="utf-8").splitlines()
            if collapse_ws(line)
        ]
    except Exception:
        return []


def _append_workstation_prompt_history(root: Path, prompt: str) -> None:
    normalized = str(prompt or "").rstrip("\n")
    if not collapse_ws(normalized):
        return
    history_path = workstation_chat_history_path(root)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with history_path.open("a", encoding="utf-8") as handle:
            handle.write(normalized + "\n")
    except Exception:
        pass


def _scroll_window_linewise(window: Any, delta: int) -> None:
    current = int(getattr(window, "vertical_scroll", 0) or 0)
    setattr(window, "vertical_scroll", max(0, current + int(delta)))


def _scroll_window_to_end(window: Any, text: str) -> None:
    lines = str(text or "").splitlines() or [""]
    setattr(window, "vertical_scroll", max(0, len(lines) - 1))


def _window_scroll_cursor_position(window: Any, text: str) -> Any:
    if Point is None:
        return None
    lines = str(text or "").splitlines() or [""]
    y = max(0, int(getattr(window, "vertical_scroll", 0) or 0))
    y = min(y, max(0, len(lines) - 1))
    return Point(x=0, y=y)
