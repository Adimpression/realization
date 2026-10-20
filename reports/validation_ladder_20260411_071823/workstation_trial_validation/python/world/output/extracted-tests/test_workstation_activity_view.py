# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from host_interaction_receipts import append_host_interaction_receipt
from workstation.activity_view import (
    start_workstation_activity_tail,
    workstation_activity_line,
    workstation_activity_log_offset,
)


class WorkstationActivityViewTests(unittest.TestCase):
    def test_workstation_activity_line_formats_receipts_for_humans(self) -> None:
        """
        High Level Purpose:
            In circumstances like workstation shell activity rendering, helps with verifying that structured receipts become concise progress lines instead of raw JSON dumps.

        Reference to Theory:
            Verifies the receipt log remains the source of truth while the shell presents a cleaner human-facing activity surface.

        Example Input Output:
            Input: `test_workstation_activity_line_formats_receipts_for_humans()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        started = workstation_activity_line(
            {
                "kind": "capability_call",
                "capability": "ws.skill.invoke",
                "arguments": {
                    "skill_title": "Symbol Search Commands 03 — Find Python Class Definition",
                    "invocation_payload": {"symbol": "BSSCController", "root": "src"},
                },
                "result": {"status": "started"},
                "phase": "started",
            },
            prompt_elapsed_seconds=0.4,
        )
        finished = workstation_activity_line(
            {
                "kind": "capability_call",
                "capability": "ws.skill.invoke",
                "arguments": {"skill_title": "Symbol Search Commands 03 — Find Python Class Definition"},
                "result": {
                    "status": "ok",
                    "skill_title": "Symbol Search Commands 03 — Find Python Class Definition",
                    "answer": "Found class BSSCController in src/demo.py line 1",
                },
            },
            prompt_elapsed_seconds=1.6,
            elapsed_seconds=1.2,
        )
        prompt = workstation_activity_line(
            {
                "kind": "user_prompt",
                "prompt": "Use the symbol search skill to find BSSCController.",
            },
            prompt_elapsed_seconds=0.0,
        )
        approval = workstation_activity_line(
            {
                "kind": "delegation_approval_requested",
                "request": {
                    "skill_title": "Python Commands 03 — Write Text File",
                    "requested_delegation": [{"capability": "ws.fs.write", "target": "main"}],
                },
            },
            prompt_elapsed_seconds=2.0,
        )
        permission_started = workstation_activity_line(
            {
                "kind": "capability_call",
                "capability": "ws.permissions.grant",
                "arguments": {"capability": "ws.repo.search"},
                "result": {"status": "started"},
                "phase": "started",
            },
            prompt_elapsed_seconds=0.3,
        )
        permission_finished = workstation_activity_line(
            {
                "kind": "capability_call",
                "capability": "ws.permissions.grant",
                "arguments": {"capability": "ws.repo.search"},
                "result": {"status": "ok", "capability": "ws.repo.search"},
            },
            prompt_elapsed_seconds=0.5,
            elapsed_seconds=0.2,
        )
        assistant = workstation_activity_line(
            {
                "kind": "assistant_response",
                "assistant_text": "Found it in src/demo.py.",
            },
            prompt_elapsed_seconds=1.8,
        )
        self.assertEqual(prompt, "Prompt received (t+0.0s)")
        self.assertIn("Invoking skill: Symbol Search Commands 03 — Find Python Class Definition", started)
        self.assertIn("[in: symbol=BSSCController, root=src]", started)
        self.assertIn("(t+0.4s)", started)
        self.assertIn("Skill completed: Symbol Search Commands 03 — Find Python Class Definition", finished)
        self.assertIn("[out: Found class BSSCController in src/demo.py line 1]", finished)
        self.assertIn("(t+1.6s, op ~1.2s)", finished)
        self.assertIn("Approval required", approval)
        self.assertIn("(t+2.0s)", approval)
        self.assertEqual(permission_started, "Granting permission: ws.repo.search (t+0.3s)")
        self.assertEqual(permission_finished, "Granted permission: ws.repo.search (t+0.5s, op ~0.2s)")
        self.assertEqual(assistant, "Assistant response ready [out: Found it in src/demo.py.] (t+1.8s)")

    def test_start_workstation_activity_tail_emits_new_receipts(self) -> None:
        """
        High Level Purpose:
            In circumstances like interactive workstation chat turns, helps with verifying that the activity tail follows newly appended receipts and emits formatted lines in near real time.

        Reference to Theory:
            Verifies the shell activity surface is derived from the durable receipt stream rather than a separate transient progress channel.

        Example Input Output:
            Input: `test_start_workstation_activity_tail_emits_new_receipts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            emitted: list[str] = []
            stop = start_workstation_activity_tail(
                root=root,
                start_offset=workstation_activity_log_offset(root),
                emit=emitted.append,
            )
            try:
                append_host_interaction_receipt(
                    root,
                    {
                        "kind": "user_prompt",
                        "prompt": "What skills are available?",
                        "timestamp": "2026-04-04T12:00:00+00:00",
                    },
                )
                append_host_interaction_receipt(
                    root,
                    {
                        "kind": "capability_call",
                        "timestamp": "2026-04-04T12:00:00.200000+00:00",
                        "capability": "ws.skill.catalog",
                        "arguments": {},
                        "result": {"status": "started"},
                        "phase": "started",
                    },
                )
                append_host_interaction_receipt(
                    root,
                    {
                        "kind": "capability_call",
                        "timestamp": "2026-04-04T12:00:00.800000+00:00",
                        "capability": "ws.skill.catalog",
                        "arguments": {},
                        "result": {"status": "ok", "returned_skill_count": 14},
                    },
                )
                deadline = time.time() + 2.0
                while time.time() < deadline and len(emitted) < 3:
                    time.sleep(0.05)
            finally:
                stop()
            self.assertIn("Prompt received (t+0.0s)", emitted)
            self.assertIn("Listing available skills (t+0.2s)", emitted)
            self.assertIn("Listed 14 skills (t+0.8s, op ~0.6s)", emitted)


if __name__ == "__main__":
    unittest.main()
