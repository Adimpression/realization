# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws, ordered_unique


_MAIN_SIGNATURE_RE = re.compile(
    r"def\s+main\s*\((?P<args>[\s\S]*?)\)\s*(?:->\s*(?P<returns>[^:]+))?\s*:",
    flags=re.MULTILINE,
)
_RAW_SQLITE_MARKERS = (
    "import sqlite3",
    "from sqlite3 import",
    "sqlite3.connect(",
)
_RAW_NETWORK_MARKERS = (
    "import requests",
    "from requests import",
    "requests.get(",
    "requests.post(",
    "requests.put(",
    "requests.patch(",
    "requests.delete(",
    "requests.request(",
    "import httpx",
    "from httpx import",
    "httpx.get(",
    "httpx.post(",
    "httpx.put(",
    "httpx.patch(",
    "httpx.delete(",
    "urllib.request.urlopen(",
    "from urllib.request import urlopen",
    "urlopen(",
)
_RAW_TOOL_INVOCATION_MARKERS = (
    "import subprocess",
    "from subprocess import",
    "subprocess.run(",
    "subprocess.Popen(",
    "subprocess.call(",
    "subprocess.check_call(",
    "subprocess.check_output(",
    "os.system(",
    "asyncio.create_subprocess_exec(",
    "asyncio.create_subprocess_shell(",
)
_RAW_PATH_MARKERS = (
    ".read_text(",
    ".write_text(",
    ".read_bytes(",
    ".write_bytes(",
    ".iterdir(",
    ".rglob(",
    ".mkdir(",
    ".unlink(",
    ".rename(",
    ".replace(",
    'with Path(',
    'Path(',
    'with open(',
    "open(",
    "os.listdir(",
    "os.remove(",
    "os.makedirs(",
    "shutil.copy(",
    "shutil.copy2(",
    "shutil.move(",
    "shutil.rmtree(",
    "zipfile.ZipFile(",
    "tarfile.open(",
)
_LEGACY_DATA_BROKER_MARKERS = (
    'broker_request("fs.read_text"',
    "broker_request('fs.read_text'",
    'broker_request("fs.write_text"',
    "broker_request('fs.write_text'",
    'broker_request("fs.list_directory"',
    "broker_request('fs.list_directory'",
    'broker_request("store.sqlite_query"',
    "broker_request('store.sqlite_query'",
)
_GOVERNED_DATA_BROKER_MARKERS = (
    'broker_request("fs.read_mount"',
    "broker_request('fs.read_mount'",
    'broker_request("fs.write_mount"',
    "broker_request('fs.write_mount'",
    'broker_request("fs.list_mount"',
    "broker_request('fs.list_mount'",
    'broker_request("fs.find_mount"',
    "broker_request('fs.find_mount'",
    'broker_request("fs.copy_mount"',
    "broker_request('fs.copy_mount'",
    'broker_request("fs.move_mount"',
    "broker_request('fs.move_mount'",
    'broker_request("fs.delete_mount"',
    "broker_request('fs.delete_mount'",
    'broker_request("fs.create_zip_mount"',
    "broker_request('fs.create_zip_mount'",
    'broker_request("fs.extract_zip_mount"',
    "broker_request('fs.extract_zip_mount'",
    'broker_request("store.named_query"',
    "broker_request('store.named_query'",
    'broker_request("store.skill_state"',
    "broker_request('store.skill_state'",
    'broker_request("net.http_get_text"',
    "broker_request('net.http_get_text'",
)


@dataclass(frozen=True)
class BrokerizedPythonSkill:
    """
    High Level Purpose:
        In circumstances like learning Python-hosted skills from markdown while preferring brokered host access over raw local effects, helps with carrying the rewritten brokered function text together with the broker names and authority hints it depends on.

    Reference to Theory:
        Supports the Python-first bundle path by separating pure skill logic from host-owned effects and making the governed broker requests explicit at learn time.

    Example Input Output:
        Input: `BrokerizedPythonSkill(python_code='from python_skill_host import broker_request\\n\\ndef main(url: str) -> dict[str, object]:\\n    return broker_request(\"macos.open_browser\", url=url)', broker_names=['macos.open_browser'], authorities=['execute'])`
        Output: BrokerizedPythonSkill(python_code='from python_skill_host import broker_request\\n\\ndef main(url: str) -> dict[str, object]:\\n    return broker_request(\"macos.open_browser\", url=url)', broker_names=['macos.open_browser'], authorities=['execute'])

    Args:
        python_code: Rewritten Python function body that routes through `python_skill_host`.
        broker_names: Named host brokers used by the rewritten skill.
        authorities: Authority hints required by the rewritten skill, including the outer executor boundary when applicable.

    Returns:
        None: Dataclass record used during broker-oriented Python skill learning.
    """

    python_code: str
    broker_names: list[str]
    authorities: list[str]


def literal_host_broker_names_from_python(python_code: str) -> list[str]:
    """Return statically named host brokers referenced by Python skill source.

    Dynamic broker identities are deliberately excluded: they cannot establish
    the exact mechanical ability-to-realizer binding required at invocation.
    """
    try:
        tree = ast.parse(str(python_code or ""))
    except SyntaxError:
        return []

    broker_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        is_broker_request = (
            isinstance(function, ast.Name) and function.id == "broker_request"
        ) or (
            isinstance(function, ast.Attribute)
            and function.attr == "broker_request"
        )
        if not is_broker_request or not node.args:
            continue
        identity = node.args[0]
        if not isinstance(identity, ast.Constant) or not isinstance(identity.value, str):
            continue
        broker_name = collapse_ws(identity.value)
        if broker_name:
            broker_names.append(broker_name)
    return ordered_unique(broker_names)


def python_skill_data_surface_assessment(python_code: str) -> dict[str, bool]:
    """
    High Level Purpose:
        In circumstances like governed admission for Python-hosted skills, helps with classifying whether a skill body uses raw path or SQLite patterns, legacy path brokers, or the newer governed data brokers.

    Reference to Theory:
        Supports broker-first adoption by making higher-risk Python admission depend on mount and named-store surfaces instead of raw paths or arbitrary SQLite.

    Example Input Output:
        Input: `python_skill_data_surface_assessment(python_code='from python_skill_host import broker_request\\n\\ndef main(mount: str, relative_path: str):\\n    return broker_request(\"fs.read_mount\", mount=mount, relative_path=relative_path)')`
        Output: {'uses_raw_sqlite': False, 'uses_raw_network_io': False, 'uses_raw_tool_invocation': False, 'uses_raw_path_io': False, 'uses_legacy_data_brokers': False, 'uses_governed_data_brokers': True}

    Args:
        python_code: Value for `python_code` used by `python_skill_data_surface_assessment`. Expected type: `str`.

    Returns:
        dict[str, bool]: Result produced by `python_skill_data_surface_assessment`.
    """
    code = str(python_code or "")
    return {
        "uses_raw_sqlite": any(marker in code for marker in _RAW_SQLITE_MARKERS),
        "uses_raw_network_io": any(marker in code for marker in _RAW_NETWORK_MARKERS),
        "uses_raw_tool_invocation": any(marker in code for marker in _RAW_TOOL_INVOCATION_MARKERS),
        "uses_raw_path_io": any(marker in code for marker in _RAW_PATH_MARKERS),
        "uses_legacy_data_brokers": any(marker in code for marker in _LEGACY_DATA_BROKER_MARKERS),
        "uses_governed_data_brokers": any(marker in code for marker in _GOVERNED_DATA_BROKER_MARKERS),
    }


def _main_signature_parts(python_code: str) -> tuple[str, str]:
    """
    High Level Purpose:
        In circumstances like rewriting learned Python `main(...)` functions into brokered forms, helps with recovering the original argument list and return annotation so the rewritten skill keeps the same callable surface.

    Reference to Theory:
        Supports broker-oriented learning by preserving the semantic invocation boundary while changing only the host-effect realization path.

    Example Input Output:
        Input: `_main_signature_parts(python_code='def main(url: str, *, browser: str = \"Safari\") -> dict[str, str]:\\n    pass')`
        Output: ('url: str, *, browser: str = "Safari"', 'dict[str, str]')

    Args:
        python_code: Value for `python_code` used by `_main_signature_parts`. Expected type: `str`.

    Returns:
        tuple[str, str]: Result produced by `_main_signature_parts`.
    """
    match = _MAIN_SIGNATURE_RE.search(str(python_code or ""))
    if not match:
        return "", ""
    args_text = str(match.group("args") or "").rstrip()
    return_text = collapse_ws(str(match.group("returns") or "").strip())
    return args_text, return_text


def _render_brokerized_main(
    *,
    args_text: str,
    return_annotation: str,
    body_lines: list[str],
) -> str:
    """
    High Level Purpose:
        In circumstances like emitting one broker-aware Python skill from a recognized raw host-effect pattern, helps with rendering a clean `main(...)` function around the mediated body.

    Reference to Theory:
        Supports Python-host mediation by making the broker import and mediated body explicit while preserving the learned function surface.

    Example Input Output:
        Input: `_render_brokerized_main(args_text='url: str', return_annotation='dict[str, object]', body_lines=['return broker_request(\"macos.open_browser\", url=url)'])`
        Output: 'from python_skill_host import broker_request\\n\\ndef main(url: str) -> dict[str, object]:\\n    return broker_request(\"macos.open_browser\", url=url)'

    Args:
        args_text: Value for `args_text` used by `_render_brokerized_main`. Expected type: `str`.
        return_annotation: Value for `return_annotation` used by `_render_brokerized_main`. Expected type: `str`.
        body_lines: Value for `body_lines` used by `_render_brokerized_main`. Expected type: `list[str]`.

    Returns:
        str: Result produced by `_render_brokerized_main`.
    """
    rendered_return = f" -> {return_annotation}" if return_annotation else ""
    return "\n".join(
        [
            "from python_skill_host import broker_request",
            "",
            f"def main({args_text}){rendered_return}:",
            *[f"    {line}" for line in body_lines],
        ]
    ).strip()


def _status_projection(
    *,
    broker_name: str,
    status_value: str,
    fields: list[str],
    broker_arguments: str,
) -> list[str]:
    """
    High Level Purpose:
        In circumstances like rewriting raw host-effect Python snippets into broker requests while preserving caller-facing result shape, helps with constructing a small result projection around the broker response.

    Reference to Theory:
        Supports broker-first learning by keeping the skill's external semantic contract stable even when the host effect moves behind mediation.

    Example Input Output:
        Input: `_status_projection(broker_name='fs.read_text', status_value='read', fields=['path', 'text'], broker_arguments='path=path')`
        Output: ['result = broker_request("fs.read_text", path=path)', 'if result.get("status") != "ok":', '    return result', 'return {"status": "read", "path": path, "text": result.get("text", "")}']

    Args:
        broker_name: Value for `broker_name` used by `_status_projection`. Expected type: `str`.
        status_value: Value for `status_value` used by `_status_projection`. Expected type: `str`.
        fields: Value for `fields` used by `_status_projection`. Expected type: `list[str]`.
        broker_arguments: Value for `broker_arguments` used by `_status_projection`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_status_projection`.
    """
    if broker_name == "fs.read_text":
        return [
            f'result = broker_request("{broker_name}", {broker_arguments})',
            'if result.get("status") != "ok":',
            "    return result",
            f'return {{"status": "{status_value}", "path": path, "text": result.get("text", "")}}',
        ]
    if broker_name == "fs.write_text":
        return [
            f'result = broker_request("{broker_name}", {broker_arguments})',
            'if result.get("status") != "ok":',
            "    return result",
            f'return {{"status": "{status_value}", "path": path, "text": text}}',
        ]
    if broker_name == "fs.list_directory":
        return [
            f'result = broker_request("{broker_name}", {broker_arguments})',
            'if result.get("status") != "ok":',
            "    return result",
            'return {"status": "listed", "path": path, "entries": result.get("entries", [])}',
        ]
    if broker_name == "net.http_get_json":
        return [
            f'result = broker_request("{broker_name}", {broker_arguments})',
            'if result.get("status") != "ok":',
            "    return result",
            'return {"status": "ok", "url": result.get("url", url), "status_code": result.get("http_status"), "payload": result.get("json")}',
        ]
    result_fields = ", ".join(f'"{field}": {field}' for field in fields)
    return [
        f'result = broker_request("{broker_name}", {broker_arguments})',
        'if result.get("status") != "ok":',
        "    return result",
        f'return {{"status": "{status_value}", {result_fields}}}',
    ]


def brokerize_python_main_for_host_brokers(python_code: str) -> BrokerizedPythonSkill | None:
    """
    High Level Purpose:
        In circumstances like learning Python-hosted skills from fenced snippets or prose-defined `main(...)` relations, helps with replacing recognized raw host-effect patterns with the governed broker API while leaving unmatched Python snippets unchanged.

    Reference to Theory:
        Supports the next Python-first bundle step by making named brokers the preferred learned interface for host effects on macOS, filesystem, store, and network surfaces.

    Example Input Output:
        Input: `brokerize_python_main_for_host_brokers(python_code='def main(url: str, *, browser: str = \"Safari\") -> dict[str, str]:\\n    import subprocess\\n    subprocess.run([\"open\", \"-a\", browser, url], check=True)\\n    return {\"status\": \"opened\", \"browser\": browser, \"url\": url}')`
        Output: BrokerizedPythonSkill(python_code='from python_skill_host import broker_request\\n\\ndef main(url: str, *, browser: str = \"Safari\") -> dict[str, str]:\\n    result = broker_request(\"macos.open_browser\", url=url, browser=browser)\\n    if result.get(\"status\") != \"ok\":\\n        return result\\n    return {\"status\": \"opened\", \"browser\": browser, \"url\": url}', broker_names=['macos.open_browser'], authorities=['execute'])

    Args:
        python_code: Value for `python_code` used by `brokerize_python_main_for_host_brokers`. Expected type: `str`.

    Returns:
        BrokerizedPythonSkill | None: Result produced by `brokerize_python_main_for_host_brokers`.
    """
    code = str(python_code or "").strip()
    if not code or "broker_request(" in code:
        return None
    args_text, return_annotation = _main_signature_parts(code)
    if not args_text:
        return None

    match_specs: list[tuple[list[str], list[str], list[str]]] = []
    if 'subprocess.run(["open", "-a", browser, url], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_browser",
                status_value="opened",
                fields=["browser", "url"],
                broker_arguments="url=url, browser=browser",
            ),
            ["macos.open_browser"],
            ["execute"],
        ))
    if 'subprocess.run(["open", "-a", app], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_app",
                status_value="launched",
                fields=["app"],
                broker_arguments="application=app",
            ),
            ["macos.open_app"],
            ["execute"],
        ))
    if 'subprocess.run(["open", "-a", app, path], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_file",
                status_value="opened",
                fields=["path", "app"],
                broker_arguments="path=path, application=app",
            ),
            ["macos.open_file"],
            ["execute"],
        ))
    if 'subprocess.run(["open", "-a", terminal_app, folder], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_file",
                status_value="opened",
                fields=["folder", "terminal_app"],
                broker_arguments="path=folder, application=terminal_app",
            ),
            ["macos.open_file"],
            ["execute"],
        ))
    if 'subprocess.run(["open", folder], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_folder",
                status_value="opened",
                fields=["folder"],
                broker_arguments="folder=folder",
            ),
            ["macos.open_folder"],
            ["execute"],
        ))
    if 'subprocess.run(["open", settings_url], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.open_location",
                status_value="opened",
                fields=["settings_url"],
                broker_arguments="target=settings_url",
            ),
            ["macos.open_location"],
            ["execute"],
        ))
    if 'subprocess.run(["open", "-R", path], check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.reveal_in_finder",
                status_value="revealed",
                fields=["path"],
                broker_arguments="path=path",
            ),
            ["macos.reveal_in_finder"],
            ["execute"],
        ))
    if (
        'subprocess.run(["screencapture", output_path], check=True)' in code
        or 'subprocess.run(["screencapture", "-x", output_path], check=True)' in code
    ):
        match_specs.append((
            _status_projection(
                broker_name="macos.capture_screenshot",
                status_value="captured",
                fields=["output_path"],
                broker_arguments="path=output_path",
            ),
            ["macos.capture_screenshot"],
            ["execute", "write"],
        ))
    if 'subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)' in code:
        match_specs.append((
            _status_projection(
                broker_name="macos.copy_to_clipboard",
                status_value="copied",
                fields=["text"],
                broker_arguments="text=text",
            ),
            ["macos.copy_to_clipboard"],
            ["execute"],
        ))
    if "sorted(item.name for item in Path(path).iterdir())" in code:
        match_specs.append((
            _status_projection(
                broker_name="fs.list_directory",
                status_value="listed",
                fields=["path"],
                broker_arguments="path=path",
            ),
            ["fs.list_directory"],
            ["execute", "read"],
        ))
    if 'Path(path).read_text(encoding="utf-8")' in code:
        match_specs.append((
            _status_projection(
                broker_name="fs.read_text",
                status_value="read",
                fields=["path"],
                broker_arguments="path=path",
            ),
            ["fs.read_text"],
            ["execute", "read"],
        ))
    if 'Path(path).write_text(text, encoding="utf-8")' in code:
        match_specs.append((
            _status_projection(
                broker_name="fs.write_text",
                status_value="written",
                fields=["path", "text"],
                broker_arguments="path=path, text=text",
            ),
            ["fs.write_text"],
            ["execute", "write"],
        ))
    if 'with Path(path).open("a", encoding="utf-8") as handle:' in code and "handle.write(text)" in code:
        match_specs.append((
            _status_projection(
                broker_name="fs.write_text",
                status_value="appended",
                fields=["path", "text"],
                broker_arguments="path=path, text=text, append=True",
            ),
            ["fs.write_text"],
            ["execute", "write"],
        ))
    if "with urlopen(url) as response:" in code and "json.loads(response.read().decode(\"utf-8\"))" in code:
        match_specs.append((
            _status_projection(
                broker_name="net.http_get_json",
                status_value="ok",
                fields=["url"],
                broker_arguments="url=url",
            ),
            ["net.http_get_json"],
            ["execute", "communicate"],
        ))

    if not match_specs:
        return None
    body_lines, broker_names, authorities = match_specs[0]
    rendered_return = return_annotation or "dict[str, object]"
    return BrokerizedPythonSkill(
        python_code=_render_brokerized_main(
            args_text=args_text,
            return_annotation=rendered_return,
            body_lines=body_lines,
        ),
        broker_names=ordered_unique(broker_names),
        authorities=ordered_unique(["execute", *authorities]),
    )
