# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from realized_validation import sqlite_runtime as packaged_validation_sqlite
import validation_sqlite
from validation_sqlite import archive_validation_sqlite, validation_sqlite_paths, validation_sqlite_use_ramdisk


class ValidationSQLiteTests(unittest.TestCase):
    def test_historical_module_is_exact_package_alias(self) -> None:
        self.assertIs(validation_sqlite, packaged_validation_sqlite)

    def test_validation_sqlite_paths_respect_override_root(self) -> None:
        """
        High Level Purpose:
            In circumstances like validator runtime storage configuration, helps with proving that an explicit SQLite runtime root override is honored without changing the archived report-local path.

        Reference to Theory:
            Verifies validation harness storage placement without changing controller or workstation semantics.

        Example Input Output:
            Input: `test_validation_sqlite_paths_respect_override_root()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp) / "reports" / "trial_domain_validation_20260408_000000" / "physics"
            runtime_root = Path(tmp) / "runtime-root"
            report_dir.mkdir(parents=True, exist_ok=True)
            with patch.dict("os.environ", {"VALIDATION_SQLITE_ROOT": str(runtime_root)}, clear=False):
                runtime_path, archived_path = validation_sqlite_paths(
                    report_dir=report_dir,
                    basename="physics.sqlite3",
                )
            self.assertEqual(runtime_path, runtime_root / report_dir.name / "physics.sqlite3")
            self.assertEqual(archived_path, report_dir / "physics.sqlite3")

    def test_archive_validation_sqlite_copies_runtime_database(self) -> None:
        """
        High Level Purpose:
            In circumstances like RAM-backed validator execution, helps with proving that the runtime SQLite database is archived back into the report directory as a usable database.

        Reference to Theory:
            Verifies validation observability and artifact durability without changing controller semantics.

        Example Input Output:
            Input: `test_archive_validation_sqlite_copies_runtime_database()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmp:
            runtime_path = Path(tmp) / "runtime.sqlite3"
            archived_path = Path(tmp) / "report" / "archived.sqlite3"
            connection = sqlite3.connect(str(runtime_path))
            try:
                connection.execute("CREATE TABLE demo(value TEXT)")
                connection.execute("INSERT INTO demo(value) VALUES ('ok')")
                connection.commit()
            finally:
                connection.close()
            result = archive_validation_sqlite(runtime_path, archived_path)
            self.assertEqual(result, archived_path)
            archived_connection = sqlite3.connect(str(archived_path))
            try:
                row = archived_connection.execute("SELECT value FROM demo").fetchone()
            finally:
                archived_connection.close()
            self.assertEqual(row, ("ok",))

    def test_validation_sqlite_use_ramdisk_honors_disable_flag(self) -> None:
        """
        High Level Purpose:
            In circumstances like local validator runtime setup, helps with proving that the RAM-disk path can be disabled explicitly when needed.

        Reference to Theory:
            Verifies validation harness configurability without changing controller or workstation semantics.

        Example Input Output:
            Input: `test_validation_sqlite_use_ramdisk_honors_disable_flag()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with patch.dict("os.environ", {"VALIDATION_SQLITE_USE_RAMDISK": "0"}, clear=False):
            self.assertFalse(validation_sqlite_use_ramdisk())
