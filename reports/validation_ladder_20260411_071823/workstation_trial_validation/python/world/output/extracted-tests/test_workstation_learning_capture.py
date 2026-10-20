# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_context import (
    load_learning_context,
    load_learning_delta,
    load_learning_source,
    persist_learning_context,
    new_learning_context,
)
from workstation.learning_capture import capture_workstation_chat_learning_from_tool_receipts
from workstation.models import WorkstationAttachment, WorkstationSession


class WorkstationLearningCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.session = WorkstationSession(
            session_id="ws_learning_capture",
            root_path=str(self.root / "session"),
            created_at="2026-04-10T00:00:00+00:00",
            attachments=(
                WorkstationAttachment(
                    name="main",
                    kind="workspace",
                    source=str(self.workspace),
                    access_mode="read_write",
                    mount_path="/workstation/mounts/main",
                ),
            ),
            allowed_capabilities=("ws.markdown.create",),
            openai_profile=None,
            openai_env_var=None,
            initial_task="",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_capture_persists_chat_markdown_into_learning_context(self) -> None:
        destination = self.workspace / "notes" / "chat_learnings.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            "# Saved Learnings\n\n- The dilution relation preserves amount.\n",
            encoding="utf-8",
        )

        report = capture_workstation_chat_learning_from_tool_receipts(
            session=self.session,
            prompt="Save the learnings from this chemistry discussion as a new markdown in notes/chat_learnings.md.",
            tool_receipts=[
                {
                    "name": "ws.markdown.create",
                    "arguments": {
                        "path": "notes/chat_learnings.md",
                        "markdown_text": "# Saved Learnings\n\n- The dilution relation preserves amount.\n",
                    },
                    "result": {
                        "status": "ok",
                        "capability": "ws.markdown.create",
                        "target": "main",
                        "path": "notes/chat_learnings.md",
                        "absolute_path": str(destination),
                    },
                }
            ],
        )

        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report["subject_id"], "chemistry")
        context = load_learning_context(self.workspace, "chemistry")
        source = load_learning_source(self.workspace, "chemistry", report["source_id"])
        delta = load_learning_delta(self.workspace, "chemistry", report["delta_id"])
        self.assertEqual(context.canonical_title, "Chemistry")
        self.assertGreaterEqual(len(context.units), 1)
        self.assertEqual(context.units[0].unit_kind, "source_note")
        self.assertEqual(source.source_kind, "chat")
        self.assertEqual(source.source_ref, str(destination.resolve()))
        self.assertEqual(delta.source_kind, "chat")
        self.assertEqual(delta.evidence_refs, (report["source_id"],))
        self.assertEqual(len(delta.operations), len(delta.proposed_units))
        self.assertTrue(all(item.operation_kind == "initiate" for item in delta.operations))
        self.assertEqual(
            {item.proposed_unit_ids for item in delta.operations},
            {(unit.unit_id,) for unit in delta.proposed_units},
        )

    def test_capture_reuses_existing_context_from_prompt_subject_hint(self) -> None:
        destination = self.workspace / "notes" / "chat_learnings.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("# Saved Learnings\n\n- Acids donate protons.\n", encoding="utf-8")
        persist_learning_context(
            self.workspace,
            new_learning_context(
                canonical_title="Chemistry",
                subject_id="chemistry",
                subject_family="Science",
            ),
        )

        report = capture_workstation_chat_learning_from_tool_receipts(
            session=self.session,
            prompt="Save the learnings from this chemistry discussion as a new markdown in notes/chat_learnings.md.",
            tool_receipts=[
                {
                    "name": "ws.markdown.create",
                    "arguments": {
                        "path": "notes/chat_learnings.md",
                        "markdown_text": "# Saved Learnings\n\n- Acids donate protons.\n",
                    },
                    "result": {
                        "status": "ok",
                        "capability": "ws.markdown.create",
                        "target": "main",
                        "path": "notes/chat_learnings.md",
                        "absolute_path": str(destination),
                    },
                }
            ],
        )

        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report["matched_existing_subject_id"], "chemistry")
        context = load_learning_context(self.workspace, "chemistry")
        self.assertEqual(context.canonical_title, "Chemistry")
        self.assertEqual(context.subject_family, "Science")

    def test_capture_ignores_plain_markdown_write_without_learning_prompt(self) -> None:
        destination = self.workspace / "notes" / "changelog.md"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("# Changelog\n", encoding="utf-8")

        report = capture_workstation_chat_learning_from_tool_receipts(
            session=self.session,
            prompt="Create a changelog markdown in notes/changelog.md.",
            tool_receipts=[
                {
                    "name": "ws.markdown.create",
                    "arguments": {
                        "path": "notes/changelog.md",
                        "markdown_text": "# Changelog\n",
                    },
                    "result": {
                        "status": "ok",
                        "capability": "ws.markdown.create",
                        "target": "main",
                        "path": "notes/changelog.md",
                        "absolute_path": str(destination),
                    },
                }
            ],
        )

        self.assertIsNone(report)
        self.assertFalse((self.workspace / "corpus").exists())
