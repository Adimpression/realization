# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Renderer-neutral workstation layout. UI implementations are responsible for
# translating these semantic tabs, panes, and sizing hints into Textual and
# Flutter controls. The goal is shared structure so the supported shells do not
# drift.

WORKSTATION_LAYOUT: dict[str, Any] = {
    "tabs": (
        {
            "key": "chat",
            "title": "Chat",
            "panes": (
                {
                    "key": "status",
                    "title": "Status",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "activity",
                    "title": "Activity",
                    "width": "fill",
                    "height_mode": "fixed",
                    "height_units": 3,
                    "text_role": "accent",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "transcript",
                    "title": "Transcript",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
                {
                    "key": "composer",
                    "title": "",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 3,
                    "text_role": "prompt",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "suggestions",
                    "title": "Suggestions",
                    "width": "fill",
                    "height_mode": "fixed",
                    "height_units": 8,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
                {
                    "key": "hint",
                    "title": "",
                    "width": "fill",
                    "height_mode": "fixed",
                    "height_units": 1,
                    "text_role": "muted",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
            ),
        },
        {
            "key": "research",
            "title": "Gather",
            "panes": (
                {
                    "key": "actions",
                    "title": "Actions",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 4,
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "progress",
                    "title": "Progress",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "learning",
                    "title": "Learning",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "itemize",
            "title": "Itemize",
            "panes": (
                {
                    "key": "actions",
                    "title": "Actions",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 4,
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "progress",
                    "title": "Progress",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "learning",
                    "title": "Learning",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "draft",
            "title": "Draft",
            "panes": (
                {
                    "key": "actions",
                    "title": "Actions",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 4,
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "progress",
                    "title": "Progress",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "learning",
                    "title": "Learning",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "review",
            "title": "Review",
            "panes": (
                {
                    "key": "actions",
                    "title": "Actions",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 4,
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "progress",
                    "title": "Progress",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "learning",
                    "title": "Learning",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "publication",
            "title": "Publication",
            "panes": (
                {
                    "key": "actions",
                    "title": "Actions",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 4,
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": False,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "progress",
                    "title": "Progress",
                    "width": "fill",
                    "height_mode": "content",
                    "min_height_units": 2,
                    "text_role": "default",
                    "surface_role": "inactive",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": False,
                },
                {
                    "key": "learning",
                    "title": "Learning",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "permissions",
            "title": "Permissions",
            "panes": (
                {
                    "key": "permissions",
                    "title": "Permissions",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "activity",
            "title": "Activity",
            "panes": (
                {
                    "key": "activity_feed",
                    "title": "Activity",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
        {
            "key": "skills",
            "title": "Skills",
            "panes": (
                {
                    "key": "skills",
                    "title": "Skills",
                    "width": "fill",
                    "height_mode": "fill",
                    "text_role": "default",
                    "surface_role": "active",
                    "wrap": True,
                    "scroll_x": False,
                    "scroll_y": True,
                },
            ),
        },
    ),
    "desktop_shell_states": (
        {
            "key": "gather.main",
            "tab_key": "research",
            "title": "Gather",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "subject_status", "title": "Subject Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "source_set", "title": "Source Set", "placement": "controls"},
                {"key": "revision_baseline", "title": "Revision Baseline", "placement": "controls"},
                {"key": "in_source_set", "title": "In Source Set", "placement": "controls"},
                {"key": "source_sets", "title": "Source Sets", "placement": "workbench_left"},
                {"key": "learned_snapshot", "title": "Learned Snapshot", "placement": "workbench_right"},
            ),
        },
        {
            "key": "gather.journal",
            "tab_key": "research",
            "title": "Gather Journal",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "journal", "title": "Gather Journal", "placement": "full_pane"},
            ),
        },
        {
            "key": "gather.source_detail",
            "tab_key": "research",
            "title": "Source Detail",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "source_detail", "title": "Source Detail", "placement": "full_pane"},
            ),
        },
        {
            "key": "itemize.main",
            "tab_key": "itemize",
            "title": "Itemize",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "itemize_status", "title": "Itemize Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "decision_role", "title": "Decision Role", "placement": "controls"},
                {"key": "hold_for_merge", "title": "Hold For Merge", "placement": "controls"},
                {"key": "item_inventory", "title": "Item Inventory", "placement": "workbench_left"},
                {"key": "item_detail", "title": "", "placement": "workbench_right"},
            ),
        },
        {
            "key": "draft.compose",
            "tab_key": "draft",
            "title": "Draft",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "draft_status", "title": "Draft Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "selected_change", "title": "Selected Change", "placement": "controls"},
                {"key": "view", "title": "View", "placement": "controls"},
                {"key": "lens", "title": "Lens", "placement": "controls"},
                {"key": "draft_inventory", "title": "Draft Item Inventory", "placement": "workbench_left"},
                {"key": "draft_detail", "title": "", "placement": "workbench_right"},
            ),
        },
        {
            "key": "draft.frame",
            "tab_key": "draft",
            "title": "Draft Frame",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "draft_status", "title": "Draft Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "selected_change", "title": "Selected Change", "placement": "controls"},
                {"key": "view", "title": "View", "placement": "controls"},
                {"key": "lens", "title": "Lens", "placement": "controls"},
                {"key": "case_objects", "title": "Case Objects", "placement": "workbench_left"},
                {"key": "case_frame", "title": "Case Frame", "placement": "workbench_center"},
                {"key": "draft_detail", "title": "", "placement": "workbench_right"},
                {"key": "issues_validation", "title": "Issues & Validation", "placement": "workbench_bottom"},
            ),
        },
        {
            "key": "draft.model",
            "tab_key": "draft",
            "title": "Draft Model",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "draft_status", "title": "Draft Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "selected_change", "title": "Selected Change", "placement": "controls"},
                {"key": "view", "title": "View", "placement": "controls"},
                {"key": "lens", "title": "Lens", "placement": "controls"},
                {"key": "case_objects", "title": "Case Objects", "placement": "workbench_left"},
                {"key": "transformation_model", "title": "Transformation Model", "placement": "workbench_center"},
                {"key": "draft_detail", "title": "", "placement": "workbench_right"},
                {"key": "issues_validation", "title": "Issues & Validation", "placement": "workbench_bottom"},
            ),
        },
        {
            "key": "draft.explore",
            "tab_key": "draft",
            "title": "Draft Explore",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "draft_status", "title": "Draft Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "selected_change", "title": "Selected Change", "placement": "controls"},
                {"key": "view", "title": "View", "placement": "controls"},
                {"key": "lens", "title": "Lens", "placement": "controls"},
                {"key": "case_objects", "title": "Case Objects", "placement": "workbench_left"},
                {"key": "explore_alternatives", "title": "Explore Alternatives", "placement": "workbench_center"},
                {"key": "draft_detail", "title": "", "placement": "workbench_right"},
                {"key": "issues_validation", "title": "Issues & Validation", "placement": "workbench_bottom"},
            ),
        },
        {
            "key": "review.main",
            "tab_key": "review",
            "title": "Review",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "review_status", "title": "Review Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "report_plan", "title": "Report Plan", "placement": "controls"},
                {"key": "selected_item", "title": "Selected Item", "placement": "controls"},
                {"key": "selected_section", "title": "Selected Section", "placement": "controls"},
                {"key": "report_scope", "title": "Report Scope", "placement": "workbench_left"},
                {"key": "selection_details", "title": "Selection Details", "placement": "workbench_right"},
            ),
        },
        {
            "key": "review.journal",
            "tab_key": "review",
            "title": "Review Journal",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "journal", "title": "Review Journal", "placement": "full_pane"},
                {"key": "review_status", "title": "Review Status", "placement": "footer"},
            ),
        },
        {
            "key": "publication.main",
            "tab_key": "publication",
            "title": "Publication",
            "sections": (
                {"key": "subject_header", "title": "Current Subject", "placement": "header"},
                {"key": "subject_nav", "title": "", "placement": "header_controls"},
                {"key": "current_step", "title": "Current Step", "placement": "gate_left"},
                {"key": "publication_status", "title": "Publication Status", "placement": "gate_right"},
                {"key": "more_actions", "title": "More Actions", "placement": "actions"},
                {"key": "report_plan", "title": "Report Plan", "placement": "controls"},
                {"key": "selected_support", "title": "Selected Support", "placement": "controls"},
                {"key": "selected_item", "title": "Selected Item", "placement": "controls"},
                {"key": "selected_section", "title": "Selected Section", "placement": "controls"},
                {"key": "report_scope", "title": "Report Scope", "placement": "workbench_left"},
                {"key": "selection_details", "title": "Selection Details", "placement": "workbench_right"},
            ),
        },
    ),
}

_WORKSTATION_TAB_KEY_ALIASES: dict[str, str] = {
    "learn_markdown": "research",
    "learn": "research",
}

WORKSTATION_PANEL_KIND_TO_LAYOUT_PANE: dict[str, tuple[str, str]] = {
    "permission_panel": ("permissions", "permissions"),
    "activity_feed": ("activity", "activity_feed"),
    "skill_catalog": ("skills", "skills"),
}

_WORKSTATION_SUBJECT_GATE_HEIGHT_UNITS = 12
_WORKSTATION_LAYOUT_ARTIFACT_PATH = Path(__file__).with_name("workstation_layout.json")


def _json_compatible_layout(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_compatible_layout(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_compatible_layout(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible_layout(item) for item in value]
    return value


def workstation_tabs() -> tuple[dict[str, Any], ...]:
    return tuple(WORKSTATION_LAYOUT.get("tabs", ()))


def workstation_tab_keys() -> list[str]:
    return [str(item.get("key", "")) for item in workstation_tabs()]


def workstation_tab_layout(tab_key: str) -> dict[str, Any]:
    normalized = _WORKSTATION_TAB_KEY_ALIASES.get(str(tab_key or ""), str(tab_key or ""))
    for tab in workstation_tabs():
        if str(tab.get("key", "")) == normalized:
            return tab
    raise KeyError(f"Unknown workstation tab: {tab_key}")


def workstation_tab_title(tab_key: str) -> str:
    return str(workstation_tab_layout(tab_key).get("title", tab_key))


def workstation_pane_layouts(tab_key: str) -> tuple[dict[str, Any], ...]:
    return tuple(workstation_tab_layout(tab_key).get("panes", ()))


def workstation_pane_layout(tab_key: str, pane_key: str) -> dict[str, Any]:
    normalized = str(pane_key or "")
    for pane in workstation_pane_layouts(tab_key):
        if str(pane.get("key", "")) == normalized:
            return pane
    raise KeyError(f"Unknown workstation pane: {tab_key}.{pane_key}")


def workstation_pane_title(tab_key: str, pane_key: str) -> str:
    return str(workstation_pane_layout(tab_key, pane_key).get("title", pane_key))


def workstation_pane_text_role(tab_key: str, pane_key: str) -> str:
    return str(workstation_pane_layout(tab_key, pane_key).get("text_role", "default"))


def workstation_pane_surface_role(tab_key: str, pane_key: str) -> str:
    return str(workstation_pane_layout(tab_key, pane_key).get("surface_role", "active"))


def workstation_shell_states() -> tuple[dict[str, Any], ...]:
    return tuple(WORKSTATION_LAYOUT.get("desktop_shell_states", ()))


def workstation_shell_state_keys() -> tuple[str, ...]:
    return tuple(str(state.get("key", "")) for state in workstation_shell_states())


def workstation_shell_state_layout(key: str) -> dict[str, Any]:
    normalized = str(key or "")
    for state in workstation_shell_states():
        if str(state.get("key", "")) == normalized:
            return state
    raise KeyError(f"Unknown workstation shell state: {key}")


def workstation_panel_title(panel_kind: str, *, fallback: str = "") -> str:
    layout_address = WORKSTATION_PANEL_KIND_TO_LAYOUT_PANE.get(str(panel_kind or ""))
    if not layout_address:
        return str(fallback or panel_kind or "")
    tab_key, pane_key = layout_address
    return workstation_pane_title(tab_key, pane_key)


def export_workstation_layout_artifact(path: Path | None = None) -> Path:
    target = Path(path or _WORKSTATION_LAYOUT_ARTIFACT_PATH).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(workstation_layout_artifact_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def workstation_layout_artifact_path() -> Path:
    return _WORKSTATION_LAYOUT_ARTIFACT_PATH


def workstation_layout_artifact_payload() -> dict[str, Any]:
    return _json_compatible_layout(WORKSTATION_LAYOUT)


def workstation_subject_gate_height_units() -> int:
    return _WORKSTATION_SUBJECT_GATE_HEIGHT_UNITS
