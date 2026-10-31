# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import realized_core_runtime.temporary as runtime_temp
from realized_core_runtime.virtual_mounts import default_virtual_mount_table


class RuntimeTempTests(unittest.TestCase):
    def test_preferred_runtime_temp_root_honors_override(self) -> None:
        """
        High Level Purpose:
            In circumstances like RAM-backed validation or workstation execution, helps with proving that the explicit runtime-temp override wins over repo-local defaults.

        Reference to Theory:
            Verifies the implemented runtime-storage behavior without changing controller semantics.

        Example Input Output:
            Input: `test_preferred_runtime_temp_root_honors_override()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory(prefix="runtime_temp_override_") as tmpdir:
            override = Path(tmpdir) / "override-temp"
            with mock.patch.dict(os.environ, {runtime_temp.RUNTIME_TEMP_ROOT_ENV: str(override)}, clear=False):
                self.assertEqual(runtime_temp.preferred_runtime_temp_root(), override)

    def test_preferred_runtime_temp_root_falls_back_to_repo_ram_tmp(self) -> None:
        """
        High Level Purpose:
            In circumstances like a full system temp volume, helps with proving that runtime temp allocation falls back to the repo-local RAM-backed path.

        Reference to Theory:
            Verifies the implemented runtime-storage behavior without changing controller semantics.

        Example Input Output:
            Input: `test_preferred_runtime_temp_root_falls_back_to_repo_ram_tmp()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory(prefix="runtime_temp_repo_root_") as tmpdir:
            repo_root = Path(tmpdir)
            with (
                mock.patch.dict(os.environ, {runtime_temp.RUNTIME_TEMP_ROOT_ENV: ""}, clear=False),
                mock.patch.object(runtime_temp, "REPO_ROOT", repo_root),
            ):
                root = runtime_temp.preferred_runtime_temp_root()
                self.assertEqual(root, repo_root / "ram" / "tmp")
                self.assertTrue(root.is_dir())

    def test_runtime_temporary_directory_creates_under_preferred_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like boundary execution helpers, helps with proving that temporary directories are created under the chosen runtime-temp root.

        Reference to Theory:
            Verifies the implemented runtime-storage behavior without changing controller semantics.

        Example Input Output:
            Input: `test_runtime_temporary_directory_creates_under_preferred_root()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory(prefix="runtime_temp_dir_") as tmpdir:
            override = Path(tmpdir) / "preferred"
            with mock.patch.dict(os.environ, {runtime_temp.RUNTIME_TEMP_ROOT_ENV: str(override)}, clear=False):
                with runtime_temp.runtime_temporary_directory(prefix="bssc-demo-") as created:
                    self.assertTrue(Path(created).is_dir())
                    self.assertEqual(Path(created).parent, override)

    def test_virtual_mounts_use_runtime_temp_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like host-executed skills that need derived scratch storage, helps with proving that virtual mounts anchor their temp roots under the same runtime-temp selection.

        Reference to Theory:
            Verifies the implemented runtime-storage behavior without changing controller semantics.

        Example Input Output:
            Input: `test_virtual_mounts_use_runtime_temp_root()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory(prefix="runtime_temp_mounts_") as tmpdir:
            override = Path(tmpdir) / "preferred"
            with mock.patch.dict(os.environ, {runtime_temp.RUNTIME_TEMP_ROOT_ENV: str(override)}, clear=False):
                mounts = default_virtual_mount_table(
                    artifact_id="artifact-demo",
                    workspace_root="/repo",
                    sqlite_path="/repo/state.sqlite3",
                )
            self.assertTrue(Path(mounts["skill_tmp"]["root"]).resolve().is_relative_to(override.resolve()))


if __name__ == "__main__":
    unittest.main()
