# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import unittest

from workstation.ui.shared.layout import (
    WORKSTATION_LAYOUT,
    workstation_layout_artifact_payload,
    workstation_layout_artifact_path,
    workstation_shell_state_keys,
    workstation_shell_state_layout,
    workstation_tab_layout,
    workstation_tab_title,
)


class WorkstationLayoutTests(unittest.TestCase):
    def test_subject_tabs_have_distinct_layout_entries(self) -> None:
        self.assertEqual(workstation_tab_title("research"), "Gather")
        self.assertEqual(workstation_tab_title("itemize"), "Itemize")
        self.assertEqual(workstation_tab_title("draft"), "Draft")
        self.assertEqual(workstation_tab_title("review"), "Review")
        self.assertEqual(workstation_tab_title("publication"), "Publication")

    def test_legacy_learn_markdown_alias_still_maps_to_gather(self) -> None:
        self.assertEqual(workstation_tab_layout("learn_markdown")["key"], "research")

    def test_layout_artifact_matches_python_source_of_truth(self) -> None:
        artifact = json.loads(workstation_layout_artifact_path().read_text(encoding="utf-8"))
        self.assertEqual(artifact, workstation_layout_artifact_payload())

    def test_desktop_shell_states_cover_textual_reference_states(self) -> None:
        self.assertEqual(
            workstation_shell_state_keys(),
            (
                "gather.main",
                "gather.journal",
                "gather.source_detail",
                "itemize.main",
                "draft.compose",
                "draft.frame",
                "draft.model",
                "draft.explore",
                "review.main",
                "review.journal",
                "publication.main",
            ),
        )

    def test_gather_main_shell_preserves_textual_section_titles(self) -> None:
        gather_main = workstation_shell_state_layout("gather.main")
        self.assertEqual(gather_main["tab_key"], "research")
        self.assertEqual(
            [section["title"] for section in gather_main["sections"]],
            [
                "Current Subject",
                "",
                "Current Step",
                "Subject Status",
                "More Actions",
                "Source Set",
                "Revision Baseline",
                "In Source Set",
                "Source Sets",
                "Learned Snapshot",
            ],
        )

    def test_draft_frame_shell_preserves_textual_workbench_titles(self) -> None:
        draft_frame = workstation_shell_state_layout("draft.frame")
        self.assertEqual(draft_frame["tab_key"], "draft")
        self.assertEqual(
            [section["title"] for section in draft_frame["sections"]],
            [
                "Current Subject",
                "",
                "Current Step",
                "Draft Status",
                "More Actions",
                "Selected Change",
                "View",
                "Lens",
                "Case Objects",
                "Case Frame",
                "",
                "Issues & Validation",
            ],
        )
