# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from host_interaction_action_dispatch import (
    execute_shared_host_interaction_action,
    is_shared_host_interaction_action_capability,
)
from host_interaction_models import HostInteractionAttachment


class HostInteractionActionDispatchTests(unittest.TestCase):
    def test_is_shared_host_interaction_action_capability_identifies_current_non_skill_surface(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed non-skill capability mediation, helps with verifying that the shared action dispatcher advertises the current extracted non-skill capability set explicitly.

        Reference to Theory:
            Verifies the shared host-interaction substrate by keeping the shared non-skill action boundary explicit instead of shell-local.

        Example Input Output:
            Input: `test_is_shared_host_interaction_action_capability_identifies_current_non_skill_surface()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        self.assertTrue(is_shared_host_interaction_action_capability("ws.repo.tree"))
        self.assertTrue(is_shared_host_interaction_action_capability("ws.repo.search"))
        self.assertTrue(is_shared_host_interaction_action_capability("ws.fs.read"))
        self.assertTrue(is_shared_host_interaction_action_capability("ws.process.run"))
        self.assertTrue(is_shared_host_interaction_action_capability("ws.net.http"))
        self.assertFalse(is_shared_host_interaction_action_capability("ws.skill.invoke"))

    def test_execute_shared_host_interaction_action_dispatches_repo_search(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed non-skill capability execution, helps with verifying that the shared dispatcher can execute repository search directly against one attachment.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring non-skill search no longer depends on workstation-local dispatch logic.

        Example Input Output:
            Input: `test_execute_shared_host_interaction_action_dispatches_repo_search()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
            attachment = HostInteractionAttachment(
                name="main",
                kind="workspace",
                source=str(root),
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            )
            result = execute_shared_host_interaction_action(
                capability="ws.repo.search",
                attachment=attachment,
                arguments={"pattern": "main\\(", "relative_path": "src", "max_matches": 10},
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["capability"], "ws.repo.search")
            self.assertTrue(any("app.py" in line for line in result["matches"]))

    def test_execute_shared_host_interaction_action_uses_injected_read_resolver(self) -> None:
        """
        High Level Purpose:
            In circumstances like shells with extra read-resolution rules, helps with verifying that the shared dispatcher can reuse a caller-provided bounded read resolver instead of forcing one path policy.

        Reference to Theory:
            Verifies the shared host-interaction substrate by keeping the read action shared while allowing shell-specific discovery-file resolution above the substrate.

        Example Input Output:
            Input: `test_execute_shared_host_interaction_action_uses_injected_read_resolver()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "workspace"
            session = root / "session"
            workspace.mkdir()
            session.mkdir()
            (workspace / "README.md").write_text("workspace\n", encoding="utf-8")
            (session / "SKILLS.json").write_text("{\"skills\": []}\n", encoding="utf-8")
            attachment = HostInteractionAttachment(
                name="main",
                kind="workspace",
                source=str(workspace),
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            )
            result = execute_shared_host_interaction_action(
                capability="ws.fs.read",
                attachment=attachment,
                arguments={"path": "SKILLS.json"},
                resolve_read_path=lambda _requested_path: session / "SKILLS.json",
            )
            self.assertEqual(result["status"], "ok")
            self.assertIn("\"skills\": []", result["content"])

    def test_execute_shared_host_interaction_action_dispatches_network_http_without_attachment(self) -> None:
        result = execute_shared_host_interaction_action(
            capability="ws.net.http",
            attachment=None,
            arguments={
                "method": "GET",
                "url": "data:text/plain,hello%20network",
                "timeout_seconds": 5.0,
                "max_response_chars": 100,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["capability"], "ws.net.http")
        self.assertEqual(result["text"], "hello network")


if __name__ == "__main__":
    unittest.main()
