from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import clean_workspace


class CleanWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def _touch(self, relative_path: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated\n", encoding="utf-8")
        return path

    def test_default_cleanup_preserves_state_and_dependency_environments(self) -> None:
        removable = (
            self._touch("package/__pycache__/module.pyc").parent,
            self._touch("package/build/output.txt").parent,
            self._touch("package/src/example.egg-info/PKG-INFO").parent,
            self._touch("workstation/ui_flutter/.dart_tool/state").parent,
            self._touch("workstation/ui_flutter/ios/Flutter/ephemeral/state").parent,
        )
        metadata = self._touch("package/.DS_Store")
        preserved = (
            self._touch(".venv/marker"),
            self._touch(".uv-cache/marker"),
            self._touch("ram/marker"),
            self._touch("reports/marker"),
            self._touch("state/marker"),
            self._touch("tmp/marker"),
            self._touch("local.env"),
            self._touch("offline.env"),
        )

        with (
            patch.object(clean_workspace, "_tracked_paths", return_value=frozenset()),
            patch.object(clean_workspace, "_is_git_ignored", return_value=True),
        ):
            targets = clean_workspace.cleanup_targets(self.root)
        clean_workspace.remove_targets(targets)

        for path in removable:
            self.assertFalse(path.exists())
        self.assertFalse(metadata.exists())
        for path in preserved:
            self.assertTrue(path.exists())

    def test_environment_cleanup_requires_explicit_opt_in(self) -> None:
        environment_markers = (
            self._touch(".venv/marker"),
            self._touch(".uv-cache/marker"),
        )

        with (
            patch.object(clean_workspace, "_tracked_paths", return_value=frozenset()),
            patch.object(clean_workspace, "_is_git_ignored", return_value=True),
        ):
            default_targets = clean_workspace.cleanup_targets(self.root)
            opted_in_targets = clean_workspace.cleanup_targets(
                self.root,
                include_environments=True,
            )

        self.assertFalse(
            any(path.name in {".venv", ".uv-cache"} for path in default_targets)
        )
        self.assertTrue(
            {path.name for path in opted_in_targets}.issuperset({".venv", ".uv-cache"})
        )
        clean_workspace.remove_targets(opted_in_targets)
        for path in environment_markers:
            self.assertFalse(path.exists())

    def test_tracked_content_is_never_removed(self) -> None:
        tracked = self._touch("source/build/keep.txt")
        with (
            patch.object(
                clean_workspace,
                "_tracked_paths",
                return_value=frozenset({"source/build/keep.txt"}),
            ),
            patch.object(clean_workspace, "_is_git_ignored", return_value=True),
        ):
            targets = clean_workspace.cleanup_targets(self.root)

        self.assertNotIn(tracked.parent, targets)

    def test_nested_git_worktree_is_never_traversed(self) -> None:
        self._touch("nested/.git")
        nested_build = self._touch("nested/build/output.txt").parent

        with (
            patch.object(clean_workspace, "_tracked_paths", return_value=frozenset()),
            patch.object(clean_workspace, "_is_git_ignored", return_value=True),
        ):
            targets = clean_workspace.cleanup_targets(self.root)

        self.assertNotIn(nested_build, targets)


if __name__ == "__main__":
    unittest.main()
