# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from realized_host_interaction.receipts import (
    append_host_interaction_receipt,
    host_interaction_assistant_response_receipt,
    host_interaction_capability_call_receipt,
    host_interaction_delegation_approval_decision_receipt,
    host_interaction_delegation_approval_requested_receipt,
    host_interaction_receipts_path,
    host_interaction_user_prompt_receipt,
)


class HostInteractionReceiptsTests(unittest.TestCase):
    def test_receipts_path_uses_canonical_session_location(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-interaction event logging, helps with verifying that receipt events always target the canonical session log location.

        Reference to Theory:
            Verifies the shared host-interaction substrate by keeping receipt storage-path rules explicit and centralized rather than shell-local.

        Example Input Output:
            Input: `test_receipts_path_uses_canonical_session_location()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        path = host_interaction_receipts_path(Path("/tmp/ws"))
        self.assertEqual(path, Path("/tmp/ws").resolve() / "receipts" / "events.jsonl")

    def test_append_host_interaction_receipt_writes_jsonl_event(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-interaction event logging, helps with verifying that receipt events are appended as JSONL records under the canonical log path.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring append-only receipt persistence is reusable across host-backed shells.

        Example Input Output:
            Input: `test_append_host_interaction_receipt_writes_jsonl_event()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            append_host_interaction_receipt(root, {"kind": "user_prompt", "prompt": "hello"})
            append_host_interaction_receipt(root, {"kind": "assistant_response", "assistant_text": "done"})
            lines = (root / "receipts" / "events.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 2)
            payloads = [json.loads(line) for line in lines]
            self.assertEqual(payloads[0]["kind"], "user_prompt")
            self.assertEqual(payloads[0]["prompt"], "hello")
            self.assertEqual(payloads[1]["kind"], "assistant_response")
            self.assertEqual(payloads[1]["assistant_text"], "done")

    def test_append_host_interaction_receipt_normalizes_legacy_stream(self) -> None:
        """
        High Level Purpose:
            In circumstances like ongoing workstation use over an older receipt file, helps with verifying that appending a new receipt rewrites a legacy concatenated JSON stream into true JSONL.

        Reference to Theory:
            Verifies the shared host-interaction substrate can preserve parseable append-only receipts across workstation upgrades.

        Example Input Output:
            Input: `test_append_host_interaction_receipt_normalizes_legacy_stream()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            receipts_path = root / "receipts" / "events.jsonl"
            receipts_path.parent.mkdir(parents=True, exist_ok=True)
            receipts_path.write_text(
                '{\n  "kind": "user_prompt",\n  "prompt": "hello"\n}\n{\n  "kind": "assistant_response",\n  "assistant_text": "done"\n}\n'
            )
            append_host_interaction_receipt(root, {"kind": "capability_call", "capability": "ws.skill.catalog"})
            payloads = [json.loads(line) for line in receipts_path.read_text().splitlines() if line.strip()]
            self.assertEqual(len(payloads), 3)
            self.assertEqual(payloads[0]["kind"], "user_prompt")
            self.assertEqual(payloads[1]["kind"], "assistant_response")
            self.assertEqual(payloads[2]["kind"], "capability_call")

    def test_receipt_builders_preserve_expected_shape(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed prompt sessions, helps with verifying that the common receipt builders produce the expected event kinds and stable payload fields.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring shells reuse one event vocabulary for prompts, capability calls, assistant responses, and approval flow.

        Example Input Output:
            Input: `test_receipt_builders_preserve_expected_shape()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        prompt_receipt = host_interaction_user_prompt_receipt(
            prompt="Inspect the project.",
            task_contract={"semantic_unit": "Inspect the project."},
        )
        capability_receipt = host_interaction_capability_call_receipt(
            capability="ws.skill.catalog",
            arguments={"target": "skills"},
            result={"status": "ok"},
            source="cli",
        )
        assistant_receipt = host_interaction_assistant_response_receipt(
            assistant_text="Done.",
            model="workstation-test-model",
            rounds=1,
            tool_calls=0,
            requested_skill="Demo Skill",
            fulfilled_by="ws.skill.invoke",
            fallback_used=False,
        )
        request_receipt = host_interaction_delegation_approval_requested_receipt(
            request={"capability": "ws.skill.invoke"},
        )
        decision_receipt = host_interaction_delegation_approval_decision_receipt(
            request={"capability": "ws.skill.invoke"},
            decision={"approved": True},
        )

        self.assertEqual(prompt_receipt["kind"], "user_prompt")
        self.assertEqual(capability_receipt["kind"], "capability_call")
        self.assertEqual(capability_receipt["source"], "cli")
        self.assertEqual(assistant_receipt["kind"], "assistant_response")
        self.assertEqual(assistant_receipt["tool_calls"], 0)
        self.assertEqual(assistant_receipt["requested_skill"], "Demo Skill")
        self.assertEqual(assistant_receipt["fulfilled_by"], "ws.skill.invoke")
        self.assertFalse(assistant_receipt["fallback_used"])
        self.assertEqual(request_receipt["kind"], "delegation_approval_requested")
        self.assertEqual(decision_receipt["kind"], "delegation_approval_decision")
