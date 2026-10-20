import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from workstation.ui.shared import desktop_file_dialogs


class DesktopFileDialogsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name).resolve()

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def test_desktop_select_markdown_files_prefers_macos_native_dialog(self) -> None:
        first_path = self.root / "docs" / "alpha.md"
        second_path = self.root / "docs" / "beta.markdown"
        first_path.parent.mkdir(parents=True, exist_ok=True)
        process = SimpleNamespace(
            returncode=0,
            stdout=f"{first_path}\n{second_path}\n",
            stderr="",
        )
        with patch("workstation.ui.shared.desktop_file_dialogs._should_use_macos_dialogs", return_value=True), patch(
            "workstation.ui.shared.desktop_file_dialogs.subprocess.run",
            return_value=process,
        ) as run_mock, patch(
            "workstation.ui.shared.desktop_file_dialogs._desktop_dialog_modules",
            side_effect=AssertionError("Tk fallback should not be used when the native macOS dialog succeeds."),
        ):
            selected_paths = desktop_file_dialogs.desktop_select_markdown_files(
                initial_directory=self.root / "docs",
            )
        self.assertEqual(selected_paths, (first_path, second_path))
        self.assertEqual(run_mock.call_count, 1)
        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], "osascript")
        self.assertIn("Select Markdown Files", command)
        self.assertIn(str((self.root / "docs").resolve()), command)

    def test_desktop_select_markdown_files_falls_back_to_tk_when_native_dialog_fails(self) -> None:
        selected_path = self.root / "docs" / "fallback.md"
        askopenfilenames = Mock(return_value=(str(selected_path),))
        fake_dialog_root = object()
        fake_filedialog = SimpleNamespace(askopenfilenames=askopenfilenames)
        with patch("workstation.ui.shared.desktop_file_dialogs._should_use_macos_dialogs", return_value=True), patch(
            "workstation.ui.shared.desktop_file_dialogs.subprocess.run",
            side_effect=OSError("osascript unavailable"),
        ), patch(
            "workstation.ui.shared.desktop_file_dialogs._desktop_dialog_modules",
            return_value=(fake_dialog_root, fake_filedialog, None),
        ), patch(
            "workstation.ui.shared.desktop_file_dialogs._prepare_dialog_root",
        ), patch(
            "workstation.ui.shared.desktop_file_dialogs._destroy_dialog_root",
        ):
            selected_paths = desktop_file_dialogs.desktop_select_markdown_files(
                initial_directory=self.root / "docs",
            )
        self.assertEqual(selected_paths, (selected_path,))
        askopenfilenames.assert_called_once()

    def test_desktop_prompt_url_prefers_macos_native_dialog(self) -> None:
        process = SimpleNamespace(
            returncode=0,
            stdout="https://example.com/research\n",
            stderr="",
        )
        with patch("workstation.ui.shared.desktop_file_dialogs._should_use_macos_dialogs", return_value=True), patch(
            "workstation.ui.shared.desktop_file_dialogs.subprocess.run",
            return_value=process,
        ) as run_mock, patch(
            "workstation.ui.shared.desktop_file_dialogs._desktop_dialog_modules",
            side_effect=AssertionError("Tk fallback should not be used when the native macOS prompt succeeds."),
        ):
            selected_url = desktop_file_dialogs.desktop_prompt_url()
        self.assertEqual(selected_url, "https://example.com/research")
        self.assertEqual(run_mock.call_count, 1)
        self.assertEqual(run_mock.call_args.args[0][0], "osascript")

    def test_desktop_select_skill_export_path_prefers_macos_native_dialog(self) -> None:
        export_path = self.root / "exports" / "learned.skill.yaml"
        process = SimpleNamespace(
            returncode=0,
            stdout=f"{export_path}\n",
            stderr="",
        )
        with patch("workstation.ui.shared.desktop_file_dialogs._should_use_macos_dialogs", return_value=True), patch(
            "workstation.ui.shared.desktop_file_dialogs.subprocess.run",
            return_value=process,
        ) as run_mock, patch(
            "workstation.ui.shared.desktop_file_dialogs._desktop_dialog_modules",
            side_effect=AssertionError("Tk fallback should not be used when the native macOS save dialog succeeds."),
        ):
            selected_path = desktop_file_dialogs.desktop_select_skill_export_path(
                initial_directory=self.root / "exports",
            )
        self.assertEqual(selected_path, export_path)
        self.assertEqual(run_mock.call_count, 1)
        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], "osascript")
        self.assertIn("Export Learned Skill", command)


if __name__ == "__main__":
    unittest.main()
