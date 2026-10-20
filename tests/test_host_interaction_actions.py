# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from host_interaction_actions import (
    host_interaction_fs_read,
    host_interaction_net_http,
    host_interaction_process_run,
    host_interaction_repo_tree,
)
from host_interaction_models import HostInteractionAttachment


class HostInteractionActionsTests(unittest.TestCase):
    def test_host_interaction_repo_tree_returns_bounded_relative_entries(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed attachment inspection, helps with verifying that the shared repo-tree helper returns relative entries rooted inside the declared attachment.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring bounded tree inspection can be reused below workstation shell code.

        Example Input Output:
            Input: `test_host_interaction_repo_tree_returns_bounded_relative_entries()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            attachment = HostInteractionAttachment(
                name="main",
                kind="workspace",
                source=str(root),
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            )
            result = host_interaction_repo_tree(attachment, max_depth=2, max_entries=10)
            self.assertEqual(result["status"], "ok")
            self.assertIn("README.md", result["tree"])
            self.assertIn("src/", result["tree"])
            self.assertIn("src/app.py", result["tree"])

    def test_host_interaction_fs_read_supports_explicit_resolved_path(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed file reads, helps with verifying that callers can inject an already-resolved bounded path when extra shell-specific resolution was needed first.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring file-read result shaping can be shared even when path resolution policy differs by shell.

        Example Input Output:
            Input: `test_host_interaction_fs_read_supports_explicit_resolved_path()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            target = root / "README.md"
            target.write_text("abcdef", encoding="utf-8")
            attachment = HostInteractionAttachment(
                name="main",
                kind="workspace",
                source=str(root),
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            )
            result = host_interaction_fs_read(
                attachment,
                requested_path="README.md",
                resolved_path=target,
                max_chars=3,
            )
            self.assertEqual(result["content"], "abc")
            self.assertTrue(result["truncated"])

    def test_host_interaction_process_run_executes_within_attachment_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared host-backed bounded command execution, helps with verifying that subprocesses run inside the declared attachment root and return bounded stdout/stderr fields.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring attachment-scoped process execution is reusable below workstation shell code.

        Example Input Output:
            Input: `test_host_interaction_process_run_executes_within_attachment_root()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            attachment = HostInteractionAttachment(
                name="main",
                kind="workspace",
                source=str(root),
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            )
            result = host_interaction_process_run(
                attachment,
                argv=["python3", "-c", "print('hello from host action')"],
                cwd_relative_path=".",
                timeout_seconds=5.0,
                max_output_chars=100,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["returncode"], 0)
            self.assertIn("hello from host action", result["stdout"])

    def test_host_interaction_net_http_returns_bounded_text_and_json(self) -> None:
        result = host_interaction_net_http(
            method="GET",
            url="data:application/json,%7B%22ok%22%3Atrue%2C%22value%22%3A42%7D",
            timeout_seconds=5.0,
            max_response_chars=100,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["capability"], "ws.net.http")
        self.assertEqual(result["method"], "GET")
        self.assertEqual(result["json"], {"ok": True, "value": 42})
        self.assertIn('"ok":true', result["text"].replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
