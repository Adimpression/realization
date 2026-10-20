# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _run_open_command(command: list[str]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated macOS host actions for opening apps, files, or folders, helps with executing the `open` command and returning one structured broker result.

    Reference to Theory:
        Supports host-owned effects on macOS by keeping device actions inside a named broker rather than scattered raw subprocess usage.

    Example Input Output:
        Input: `_run_open_command(command=['open', '-a', 'Safari', 'https://example.com'])`
        Output: {'status': 'ok', 'command': ['open', '-a', 'Safari', 'https://example.com'], 'stdout': '', 'stderr': ''}

    Args:
        command: Value for `command` used by `_run_open_command`. Expected type: `list[str]`.

    Returns:
        dict[str, Any]: Result produced by `_run_open_command`.
    """
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "command": list(command),
        "stdout": str(completed.stdout or "").strip(),
        "stderr": str(completed.stderr or "").strip(),
        "exit_code": int(completed.returncode),
    }


def open_browser(*, url: str, browser: str = "Safari") -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated device-user actions on macOS, helps with opening one browser at a target URL through the named browser broker.

    Reference to Theory:
        Supports bundle-style host mediation by making browser launch a named macOS effect instead of a raw script-side subprocess pattern.

    Example Input Output:
        Input: `open_browser(url='https://example.com', browser='Safari')`
        Output: {'status': 'ok', 'browser': 'Safari', 'url': 'https://example.com'}

    Args:
        url: Value for `url` used by `open_browser`. Expected type: `str`.
        browser: Value for `browser` used by `open_browser`. Expected type: `str`. Defaults to `'Safari'`.

    Returns:
        dict[str, Any]: Result produced by `open_browser`.
    """
    result = _run_open_command(["open", "-a", str(browser), str(url)])
    result.update({"browser": str(browser), "url": str(url)})
    return result


def open_app(*, application: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated device-user actions on macOS, helps with launching one application by name through the named app broker.

    Reference to Theory:
        Supports host-owned device effects by turning application launch into an explicit brokered action.

    Example Input Output:
        Input: `open_app(application='TextEdit')`
        Output: {'status': 'ok', 'application': 'TextEdit'}

    Args:
        application: Value for `application` used by `open_app`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `open_app`.
    """
    result = _run_open_command(["open", "-a", str(application)])
    result.update({"application": str(application)})
    return result


def open_file(*, path: str, application: str = "") -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated file-opening actions on macOS, helps with opening one file optionally in a chosen application through the named file broker.

    Reference to Theory:
        Supports host-owned effects by moving file opening into a named mediated action rather than direct subprocess usage inside skills.

    Example Input Output:
        Input: `open_file(path='/Users/ravindranathakila/Downloads/example.txt', application='TextEdit')`
        Output: {'status': 'ok', 'path': '/Users/ravindranathakila/Downloads/example.txt', 'application': 'TextEdit'}

    Args:
        path: Value for `path` used by `open_file`. Expected type: `str`.
        application: Value for `application` used by `open_file`. Expected type: `str`. Defaults to `''`.

    Returns:
        dict[str, Any]: Result produced by `open_file`.
    """
    command = ["open"]
    if str(application).strip():
        command.extend(["-a", str(application)])
    command.append(str(path))
    result = _run_open_command(command)
    result.update({"path": str(path), "application": str(application).strip()})
    return result


def open_folder(*, folder: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated Finder-style folder browsing on macOS, helps with opening one directory through the named folder broker.

    Reference to Theory:
        Supports host-owned device effects by turning folder browsing into an explicit named action.

    Example Input Output:
        Input: `open_folder(folder='/Applications')`
        Output: {'status': 'ok', 'folder': '/Applications'}

    Args:
        folder: Value for `folder` used by `open_folder`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `open_folder`.
    """
    result = _run_open_command(["open", str(folder)])
    result.update({"folder": str(folder)})
    return result


def open_location(*, target: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated macOS actions that open one general URL, system settings deep link, or path without a specialized broker, helps with routing that target through the generic `open` command.

    Reference to Theory:
        Supports host-owned macOS effects by keeping uncategorized open-target actions behind a named broker instead of raw subprocess calls inside skills.

    Example Input Output:
        Input: `open_location(target='x-apple.systempreferences:com.apple.preference.general')`
        Output: {'status': 'ok', 'target': 'x-apple.systempreferences:com.apple.preference.general'}

    Args:
        target: Value for `target` used by `open_location`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `open_location`.
    """
    result = _run_open_command(["open", str(target)])
    result.update({"target": str(target)})
    return result


def reveal_in_finder(*, path: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated file-location actions on macOS, helps with revealing one path in Finder through the named reveal broker.

    Reference to Theory:
        Supports host-owned device effects by separating Finder reveal from raw subprocess execution.

    Example Input Output:
        Input: `reveal_in_finder(path='/Users/ravindranathakila/service/realized/README.md')`
        Output: {'status': 'ok', 'path': '/Users/ravindranathakila/service/realized/README.md'}

    Args:
        path: Value for `path` used by `reveal_in_finder`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `reveal_in_finder`.
    """
    result = _run_open_command(["open", "-R", str(path)])
    result.update({"path": str(path)})
    return result


def capture_screenshot(*, path: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated screenshot capture on macOS, helps with asking the system screenshot tool to write one image file through the named screenshot broker.

    Reference to Theory:
        Supports host-owned device effects by keeping screenshot capture inside a named brokered action.

    Example Input Output:
        Input: `capture_screenshot(path='/tmp/example.png')`
        Output: {'status': 'ok', 'path': '/tmp/example.png'}

    Args:
        path: Value for `path` used by `capture_screenshot`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `capture_screenshot`.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["screencapture", "-x", str(target)],
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "path": str(target),
        "stdout": str(completed.stdout or "").strip(),
        "stderr": str(completed.stderr or "").strip(),
        "exit_code": int(completed.returncode),
    }


def copy_to_clipboard(*, text: str) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like mediated clipboard writes on macOS, helps with copying one text payload through `pbcopy` while returning a structured broker result.

    Reference to Theory:
        Supports host-owned device effects by making clipboard mutation a named brokered action.

    Example Input Output:
        Input: `copy_to_clipboard(text='hello')`
        Output: {'status': 'ok', 'text': 'hello', 'bytes_written': 5}

    Args:
        text: Value for `text` used by `copy_to_clipboard`. Expected type: `str`.

    Returns:
        dict[str, Any]: Result produced by `copy_to_clipboard`.
    """
    payload = str(text)
    completed = subprocess.run(
        ["pbcopy"],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "status": "ok" if completed.returncode == 0 else "error",
        "text": payload,
        "bytes_written": len(payload.encode("utf-8")),
        "stdout": str(completed.stdout or "").strip(),
        "stderr": str(completed.stderr or "").strip(),
        "exit_code": int(completed.returncode),
    }
