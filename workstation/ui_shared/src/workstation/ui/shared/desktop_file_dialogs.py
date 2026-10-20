# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

_MACOS_DIALOG_FALLBACK = object()


def desktop_select_markdown_file(
    *,
    title: str = "Select Markdown File",
    initial_directory: Path | None = None,
) -> Path | None:
    selected_paths = desktop_select_markdown_files(
        title=title,
        initial_directory=initial_directory,
    )
    if not selected_paths:
        return None
    return selected_paths[0]


def desktop_select_markdown_files(
    *,
    title: str = "Select Markdown Files",
    initial_directory: Path | None = None,
) -> tuple[Path, ...]:
    macos_selected = _macos_select_files(
        title=title,
        initial_directory=initial_directory,
        allowed_extensions=("md", "markdown"),
        allow_multiple=True,
    )
    if macos_selected is not _MACOS_DIALOG_FALLBACK:
        return macos_selected
    dialog_root, filedialog, _messagebox = _desktop_dialog_modules()
    _prepare_dialog_root(dialog_root)
    try:
        selected = filedialog.askopenfilenames(
            title=title,
            initialdir=str(initial_directory) if initial_directory is not None else None,
            filetypes=[
                ("Markdown Files", "*.md *.markdown"),
                ("All Files", "*.*"),
            ],
        )
    finally:
        _destroy_dialog_root(dialog_root)
    if not selected:
        return ()
    resolved_paths: list[Path] = []
    for entry in selected:
        rendered = str(entry or "").strip()
        if not rendered:
            continue
        resolved_paths.append(Path(rendered).expanduser().resolve())
    return tuple(resolved_paths)


def desktop_prompt_url(
    *,
    title: str = "Learn URL",
    prompt: str = "Enter a URL to learn from:",
    initial_value: str = "https://",
) -> str | None:
    macos_selected = _macos_prompt_text(
        title=title,
        prompt=prompt,
        initial_value=initial_value,
    )
    if macos_selected is not _MACOS_DIALOG_FALLBACK:
        rendered = str(macos_selected or "").strip()
        return rendered or None
    from tkinter import simpledialog

    dialog_root, _filedialog, _messagebox = _desktop_dialog_modules()
    _prepare_dialog_root(dialog_root)
    try:
        selected = simpledialog.askstring(
            title=title,
            prompt=prompt,
            initialvalue=initial_value,
            parent=dialog_root,
        )
    finally:
        _destroy_dialog_root(dialog_root)
    rendered = str(selected or "").strip()
    return rendered or None


def desktop_confirm_export(
    *,
    title: str = "Export Learned Skill",
    message: str = "Export the learned skill bundle to a file?",
) -> bool:
    macos_selected = _macos_confirm_dialog(title=title, message=message)
    if macos_selected is not _MACOS_DIALOG_FALLBACK:
        return bool(macos_selected)
    dialog_root, _filedialog, messagebox = _desktop_dialog_modules()
    _prepare_dialog_root(dialog_root)
    try:
        return bool(messagebox.askyesno(title, message))
    finally:
        _destroy_dialog_root(dialog_root)


def desktop_select_skill_export_path(
    *,
    title: str = "Export Learned Skill",
    default_filename: str = "learned.skill.yaml",
    initial_directory: Path | None = None,
) -> Path | None:
    macos_selected = _macos_save_path(
        title=title,
        default_filename=default_filename,
        initial_directory=initial_directory,
    )
    if macos_selected is not _MACOS_DIALOG_FALLBACK:
        return macos_selected
    dialog_root, filedialog, _messagebox = _desktop_dialog_modules()
    _prepare_dialog_root(dialog_root)
    try:
        selected = filedialog.asksaveasfilename(
            title=title,
            initialdir=str(initial_directory) if initial_directory is not None else None,
            initialfile=default_filename,
            defaultextension=".yaml",
            filetypes=[
                ("YAML Files", "*.yaml *.yml"),
                ("All Files", "*.*"),
            ],
        )
    finally:
        _destroy_dialog_root(dialog_root)
    if not selected:
        return None
    return Path(str(selected)).expanduser().resolve()


def desktop_open_path(path: Path) -> bool:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return False
    try:
        if sys.platform == "darwin":
            if resolved.is_file() and resolved.suffix.casefold() in {".md", ".markdown", ".typ", ".txt", ".json", ".yaml", ".yml"}:
                process = subprocess.run(
                    ["open", "-a", "TextEdit", str(resolved)],
                    capture_output=True,
                    text=True,
                )
                if process.returncode == 0:
                    return True
            process = subprocess.run(
                ["open", str(resolved)],
                capture_output=True,
                text=True,
            )
            return process.returncode == 0
        if os.name == "nt":
            os.startfile(str(resolved))  # type: ignore[attr-defined]
            return True
        process = subprocess.run(
            ["xdg-open", str(resolved)],
            capture_output=True,
            text=True,
        )
        return process.returncode == 0
    except Exception:
        return False


def _macos_select_files(
    *,
    title: str,
    initial_directory: Path | None,
    allowed_extensions: tuple[str, ...],
    allow_multiple: bool,
):
    if not _should_use_macos_dialogs():
        return _MACOS_DIALOG_FALLBACK
    default_directory = _normalized_dialog_directory(initial_directory)
    type_clause = "{" + ", ".join(f'"{extension}"' for extension in allowed_extensions) + "}"
    selection_clause = " with multiple selections allowed" if allow_multiple else ""
    script_lines = (
        "on run argv",
        "set dialogTitle to item 1 of argv",
        "set defaultDir to item 2 of argv",
        "try",
        f'if defaultDir is not "" then',
        f"set chosenFiles to choose file with prompt dialogTitle default location (POSIX file defaultDir) of type {type_clause}{selection_clause}",
        "else",
        f"set chosenFiles to choose file with prompt dialogTitle of type {type_clause}{selection_clause}",
        "end if",
        "on error number -128",
        'return ""',
        "end try",
        "set originalDelimiters to AppleScript's text item delimiters",
        "set AppleScript's text item delimiters to linefeed",
        "set renderedPaths to {}",
        "if class of chosenFiles is list then",
        "repeat with chosenFile in chosenFiles",
        "set end of renderedPaths to POSIX path of chosenFile",
        "end repeat",
        "else",
        "set end of renderedPaths to POSIX path of chosenFiles",
        "end if",
        "set renderedText to renderedPaths as text",
        "set AppleScript's text item delimiters to originalDelimiters",
        "return renderedText",
        "end run",
    )
    stdout = _run_macos_dialog(script_lines, title, str(default_directory or ""))
    if stdout is _MACOS_DIALOG_FALLBACK:
        return _MACOS_DIALOG_FALLBACK
    if not stdout:
        return ()
    resolved_paths: list[Path] = []
    for entry in str(stdout).splitlines():
        rendered = str(entry or "").strip()
        if not rendered:
            continue
        resolved_paths.append(Path(rendered).expanduser().resolve())
    return tuple(resolved_paths)


def _macos_save_path(
    *,
    title: str,
    default_filename: str,
    initial_directory: Path | None,
):
    if not _should_use_macos_dialogs():
        return _MACOS_DIALOG_FALLBACK
    default_directory = _normalized_dialog_directory(initial_directory)
    script_lines = (
        "on run argv",
        "set dialogTitle to item 1 of argv",
        "set defaultName to item 2 of argv",
        "set defaultDir to item 3 of argv",
        "try",
        'if defaultDir is not "" then',
        "set chosenFile to choose file name with prompt dialogTitle default name defaultName default location (POSIX file defaultDir)",
        "else",
        "set chosenFile to choose file name with prompt dialogTitle default name defaultName",
        "end if",
        "return POSIX path of chosenFile",
        "on error number -128",
        'return ""',
        "end try",
        "end run",
    )
    stdout = _run_macos_dialog(
        script_lines,
        title,
        str(default_filename or ""),
        str(default_directory or ""),
    )
    if stdout is _MACOS_DIALOG_FALLBACK:
        return _MACOS_DIALOG_FALLBACK
    rendered = str(stdout or "").strip()
    if not rendered:
        return None
    return Path(rendered).expanduser().resolve()


def _macos_prompt_text(
    *,
    title: str,
    prompt: str,
    initial_value: str,
):
    if not _should_use_macos_dialogs():
        return _MACOS_DIALOG_FALLBACK
    script_lines = (
        "on run argv",
        "set dialogTitle to item 1 of argv",
        "set dialogPrompt to item 2 of argv",
        "set initialValue to item 3 of argv",
        "try",
        'set dialogResult to display dialog dialogPrompt with title dialogTitle default answer initialValue buttons {"Cancel", "OK"} default button "OK"',
        "return text returned of dialogResult",
        "on error number -128",
        'return ""',
        "end try",
        "end run",
    )
    return _run_macos_dialog(script_lines, title, prompt, initial_value)


def _macos_confirm_dialog(*, title: str, message: str):
    if not _should_use_macos_dialogs():
        return _MACOS_DIALOG_FALLBACK
    script_lines = (
        "on run argv",
        "set dialogTitle to item 1 of argv",
        "set dialogMessage to item 2 of argv",
        "try",
        'display dialog dialogMessage with title dialogTitle buttons {"Cancel", "OK"} default button "OK"',
        'return "ok"',
        "on error number -128",
        'return ""',
        "end try",
        "end run",
    )
    stdout = _run_macos_dialog(script_lines, title, message)
    if stdout is _MACOS_DIALOG_FALLBACK:
        return _MACOS_DIALOG_FALLBACK
    return bool(str(stdout or "").strip())


def _run_macos_dialog(script_lines: tuple[str, ...], *arguments: str):
    command = ["osascript"]
    for line in script_lines:
        command.extend(["-e", line])
    command.append("--")
    command.extend(str(argument) for argument in arguments)
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return _MACOS_DIALOG_FALLBACK
    if process.returncode != 0:
        return _MACOS_DIALOG_FALLBACK
    return str(process.stdout or "").strip()


def _should_use_macos_dialogs() -> bool:
    return sys.platform == "darwin"


def _normalized_dialog_directory(initial_directory: Path | None) -> Path | None:
    if initial_directory is None:
        return None
    try:
        resolved = Path(initial_directory).expanduser().resolve()
    except Exception:
        return None
    if resolved.is_dir():
        return resolved
    parent = resolved.parent
    if parent.exists() and parent.is_dir():
        return parent
    return None


def _desktop_dialog_modules():
    import tkinter as tk
    from tkinter import filedialog, messagebox

    dialog_root = tk.Tk()
    dialog_root.withdraw()
    try:
        dialog_root.attributes("-topmost", True)
    except Exception:
        pass
    return dialog_root, filedialog, messagebox


def _prepare_dialog_root(dialog_root) -> None:
    try:
        dialog_root.update_idletasks()
    except Exception:
        pass
    try:
        dialog_root.lift()
    except Exception:
        pass
    try:
        dialog_root.focus_force()
    except Exception:
        pass
    _activate_current_desktop_app()


def _activate_current_desktop_app() -> None:
    if sys.platform != "darwin":
        return
    script = (
        'tell application "System Events" '
        f'to set frontmost of the first process whose unix id is {os.getpid()} to true'
    )
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        pass


def _destroy_dialog_root(dialog_root) -> None:
    try:
        dialog_root.update_idletasks()
    except Exception:
        pass
    try:
        dialog_root.update()
    except Exception:
        pass
    try:
        dialog_root.destroy()
    except Exception:
        pass
