import unittest
from pathlib import Path
from unittest.mock import patch

from workstation.ui.shared import desktop_file_dialogs


class _FakeDialogRoot:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def update_idletasks(self) -> None:
        self.calls.append("update_idletasks")

    def lift(self) -> None:
        self.calls.append("lift")

    def focus_force(self) -> None:
        self.calls.append("focus_force")

    def update(self) -> None:
        self.calls.append("update")

    def destroy(self) -> None:
        self.calls.append("destroy")


class _FakeFileDialog:
    def __init__(self) -> None:
        self.open_kwargs: dict[str, object] | None = None
        self.opens_kwargs: dict[str, object] | None = None
        self.save_kwargs: dict[str, object] | None = None

    def askopenfilename(self, **kwargs):
        self.open_kwargs = dict(kwargs)
        return "/tmp/example.md"

    def askopenfilenames(self, **kwargs):
        self.opens_kwargs = dict(kwargs)
        return ("/tmp/example-a.md", "/tmp/example-b.md")

    def asksaveasfilename(self, **kwargs):
        self.save_kwargs = dict(kwargs)
        return "/tmp/exported.skill.yaml"


class _FakeMessageBox:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def askyesno(self, title, message, **kwargs):
        self.kwargs = {"title": title, "message": message, **kwargs}
        return True


class _FakeSimpleDialog:
    def __init__(self) -> None:
        self.kwargs: dict[str, object] | None = None

    def askstring(self, title, prompt, **kwargs):
        self.kwargs = {"title": title, "prompt": prompt, **kwargs}
        return "https://example.test/article"


class DesktopFileDialogsTests(unittest.TestCase):
    def test_select_markdown_file_prepares_dialog_and_activates_app(self) -> None:
        root = _FakeDialogRoot()
        filedialog = _FakeFileDialog()
        messagebox = _FakeMessageBox()

        with patch.object(
            desktop_file_dialogs,
            "_should_use_macos_dialogs",
            return_value=False,
        ), patch.object(
            desktop_file_dialogs,
            "_desktop_dialog_modules",
            return_value=(root, filedialog, messagebox),
        ), patch.object(desktop_file_dialogs, "_activate_current_desktop_app") as activate_mock:
            selected = desktop_file_dialogs.desktop_select_markdown_file(initial_directory=Path("/tmp"))

        self.assertEqual(selected, Path("/tmp/example-a.md").resolve())
        self.assertEqual(filedialog.opens_kwargs["initialdir"], "/tmp")
        self.assertIn("update_idletasks", root.calls)
        self.assertIn("lift", root.calls)
        self.assertIn("focus_force", root.calls)
        self.assertIn("destroy", root.calls)
        activate_mock.assert_called_once_with()

    def test_select_skill_export_path_prepares_dialog_and_activates_app(self) -> None:
        root = _FakeDialogRoot()
        filedialog = _FakeFileDialog()
        messagebox = _FakeMessageBox()

        with patch.object(
            desktop_file_dialogs,
            "_should_use_macos_dialogs",
            return_value=False,
        ), patch.object(
            desktop_file_dialogs,
            "_desktop_dialog_modules",
            return_value=(root, filedialog, messagebox),
        ), patch.object(desktop_file_dialogs, "_activate_current_desktop_app") as activate_mock:
            selected = desktop_file_dialogs.desktop_select_skill_export_path(initial_directory=Path("/tmp"))

        self.assertEqual(selected, Path("/tmp/exported.skill.yaml").resolve())
        self.assertEqual(filedialog.save_kwargs["initialdir"], "/tmp")
        self.assertIn("destroy", root.calls)
        activate_mock.assert_called_once_with()

    def test_select_markdown_files_prepares_dialog_and_activates_app(self) -> None:
        root = _FakeDialogRoot()
        filedialog = _FakeFileDialog()
        messagebox = _FakeMessageBox()

        with patch.object(
            desktop_file_dialogs,
            "_should_use_macos_dialogs",
            return_value=False,
        ), patch.object(
            desktop_file_dialogs,
            "_desktop_dialog_modules",
            return_value=(root, filedialog, messagebox),
        ), patch.object(desktop_file_dialogs, "_activate_current_desktop_app") as activate_mock:
            selected = desktop_file_dialogs.desktop_select_markdown_files(initial_directory=Path("/tmp"))

        self.assertEqual(
            selected,
            (
                Path("/tmp/example-a.md").resolve(),
                Path("/tmp/example-b.md").resolve(),
            ),
        )
        self.assertEqual(filedialog.opens_kwargs["initialdir"], "/tmp")
        self.assertIn("destroy", root.calls)
        activate_mock.assert_called_once_with()

    def test_confirm_export_prepares_dialog_and_activates_app(self) -> None:
        root = _FakeDialogRoot()
        filedialog = _FakeFileDialog()
        messagebox = _FakeMessageBox()

        with patch.object(
            desktop_file_dialogs,
            "_should_use_macos_dialogs",
            return_value=False,
        ), patch.object(
            desktop_file_dialogs,
            "_desktop_dialog_modules",
            return_value=(root, filedialog, messagebox),
        ), patch.object(desktop_file_dialogs, "_activate_current_desktop_app") as activate_mock:
            approved = desktop_file_dialogs.desktop_confirm_export()

        self.assertTrue(approved)
        self.assertIn("destroy", root.calls)
        activate_mock.assert_called_once_with()

    def test_prompt_url_prepares_dialog_and_activates_app(self) -> None:
        root = _FakeDialogRoot()
        filedialog = _FakeFileDialog()
        messagebox = _FakeMessageBox()
        simpledialog = _FakeSimpleDialog()

        with patch.object(
            desktop_file_dialogs,
            "_should_use_macos_dialogs",
            return_value=False,
        ), patch.object(
            desktop_file_dialogs,
            "_desktop_dialog_modules",
            return_value=(root, filedialog, messagebox),
        ), patch("tkinter.simpledialog.askstring", side_effect=simpledialog.askstring), patch.object(
            desktop_file_dialogs, "_activate_current_desktop_app"
        ) as activate_mock:
            selected = desktop_file_dialogs.desktop_prompt_url()

        self.assertEqual(selected, "https://example.test/article")
        self.assertEqual(simpledialog.kwargs["initialvalue"], "https://")
        self.assertIs(simpledialog.kwargs["parent"], root)
        self.assertIn("update", root.calls)
        self.assertIn("destroy", root.calls)
        activate_mock.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
