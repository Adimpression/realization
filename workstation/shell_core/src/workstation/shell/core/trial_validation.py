# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from workstation.runtime.core.session import launch_workstation_session, prompt_workstation_session
from workstation.skills.core.skill_invocation import list_available_workstation_skills
from workstation.skills.core.skill_management import import_workstation_skill_file


def _repo_root() -> Path:
    resolved = Path(__file__).resolve()
    for parent in resolved.parents:
        if (parent / "pyproject.toml").exists() and (
            parent / "architecture" / "boundaries.toml"
        ).exists():
            return parent
    return resolved.parents[6]


REPO_ROOT = _repo_root()
TRIALS_ROOT = REPO_ROOT / "trials"
REPORTS_ROOT = REPO_ROOT / "reports"
LOCAL_ENV = REPO_ROOT / "local.env"


def _utc_timestamp_slug() -> str:
    """
    High Level Purpose:
        In circumstances like workstation trial audit reporting, helps with generating one stable UTC timestamp slug for the report directory name.

    Reference to Theory:
        Supports repeatable workstation validation by giving each audit run an isolated durable report root.

    Example Input Output:
        Input: `_utc_timestamp_slug()`
        Output: '20260403_114500'

    Args:
        None.

    Returns:
        str: Result produced by `_utc_timestamp_slug`.
    """
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _load_local_env_if_needed() -> list[str]:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with loading provider credentials from `local.env` when the host environment has not already supplied them.

    Reference to Theory:
        Supports workstation trial auditing by reusing the same host-owned provider path as ordinary workstation prompting without requiring an external shell wrapper.

    Example Input Output:
        Input: `_load_local_env_if_needed()`
        Output: ['OPENAI_API_KEY']

    Args:
        None.

    Returns:
        list[str]: Result produced by `_load_local_env_if_needed`.
    """
    if os.getenv("OPENAI_API_KEY", "").strip() or not LOCAL_ENV.exists():
        return []
    applied: list[str] = []
    for raw_line in LOCAL_ENV.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key_text = key.strip()
        if not key_text or key_text in os.environ:
            continue
        value_text = value.strip().strip("'").strip('"')
        os.environ[key_text] = value_text
        applied.append(key_text)
    return applied


@contextmanager
def _temporary_environment(overrides: dict[str, str]) -> Any:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with applying one temporary environment override for a bounded validation scope and restoring the prior host environment afterward.

    Reference to Theory:
        Supports safe workstation compatibility runs by letting the validator inject fake toolchains or scoped host settings without permanently mutating the outer shell state.

    Example Input Output:
        Input: `with _temporary_environment({'PATH': '/tmp/fakebin:/usr/bin'}): ...`
        Output: context manager for temporary environment mutation

    Args:
        overrides: Value for `overrides` used by `_temporary_environment`. Expected type: `dict[str, str]`.

    Returns:
        Any: Context manager result produced by `_temporary_environment`.
    """
    original: dict[str, str | None] = {key: os.environ.get(key) for key in overrides}
    try:
        for key, value in overrides.items():
            os.environ[str(key)] = str(value)
        yield
    finally:
        for key, prior in original.items():
            if prior is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prior


def _materialize_deviceuser_fake_macos_toolchain(report_dir: Path) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation validation of device-user trial workers, helps with creating one fake macOS command toolchain so prompts can be audited without opening real apps or mutating the real desktop.

    Reference to Theory:
        Supports safe workstation/trial compatibility work by preserving the worker surface while replacing side-effecting host commands with bounded receipt-producing fakes.

    Example Input Output:
        Input: `_materialize_deviceuser_fake_macos_toolchain(Path('/tmp/report/deviceuser'))`
        Output: {'PATH': '/tmp/report/deviceuser/fakebin:...', 'WORKSTATION_DEVICEUSER_FAKE_LOG': '/tmp/report/deviceuser/fake_macos_tools.log'}

    Args:
        report_dir: Value for `report_dir` used by `_materialize_deviceuser_fake_macos_toolchain`. Expected type: `Path`.

    Returns:
        dict[str, str]: Result produced by `_materialize_deviceuser_fake_macos_toolchain`.
    """
    fakebin = Path(report_dir) / "fakebin"
    fakebin.mkdir(parents=True, exist_ok=True)
    fake_log = Path(report_dir) / "fake_macos_tools.log"
    fake_open = fakebin / "open"
    fake_open.write_text(
        "\n".join(
            [
                "#!/bin/zsh",
                f"print -r -- \"open:$@\" >> {fake_log}",
            ]
        )
        + "\n"
    )
    fake_pbcopy = fakebin / "pbcopy"
    fake_pbcopy.write_text(
        "\n".join(
            [
                "#!/bin/zsh",
                "input=$(cat)",
                f"print -r -- \"pbcopy:$input\" >> {fake_log}",
            ]
        )
        + "\n"
    )
    fake_screencapture = fakebin / "screencapture"
    fake_screencapture.write_text(
        "\n".join(
            [
                "#!/bin/zsh",
                f"print -r -- \"screencapture:$@\" >> {fake_log}",
                "dest=${@: -1}",
                "mkdir -p \"$(dirname \"$dest\")\"",
                ": > \"$dest\"",
            ]
        )
        + "\n"
    )
    for script in (fake_open, fake_pbcopy, fake_screencapture):
        script.chmod(0o755)
    return {
        "PATH": str(fakebin) + os.pathsep + os.environ.get("PATH", ""),
        "WORKSTATION_DEVICEUSER_FAKE_LOG": str(fake_log),
    }


def _materialize_apiclient_fake_http_environment(report_dir: Path) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation validation of API-client trial workers, helps with creating one fake HTTP layer for placeholder hosts so the imported workers can execute deterministically without depending on public DNS or external services.

    Reference to Theory:
        Supports safe workstation/trial compatibility work by preserving the governed worker surface while replacing unstable placeholder network dependencies with bounded local responses.

    Example Input Output:
        Input: `_materialize_apiclient_fake_http_environment(Path('/tmp/report/apiclient'))`
        Output: {'PYTHONPATH': '/tmp/report/apiclient/fake_http:...', 'WORKSTATION_APICLIENT_FAKE_LOG': '/tmp/report/apiclient/fake_http.log'}

    Args:
        report_dir: Value for `report_dir` used by `_materialize_apiclient_fake_http_environment`. Expected type: `Path`.

    Returns:
        dict[str, str]: Result produced by `_materialize_apiclient_fake_http_environment`.
    """
    fake_root = Path(report_dir) / "fake_http"
    fake_root.mkdir(parents=True, exist_ok=True)
    fake_log = Path(report_dir) / "fake_http.log"
    sitecustomize = fake_root / "sitecustomize.py"
    sitecustomize.write_text(
        "\n".join(
            [
                "import io",
                "import json",
                "import os",
                "from urllib.parse import parse_qs, urlparse",
                "import urllib.request as _urllib_request",
                "",
                "_FAKE_LOG = os.getenv('WORKSTATION_APICLIENT_FAKE_LOG', '')",
                "_POLL_COUNTS = {}",
                "_ORIGINAL_URLOPEN = _urllib_request.urlopen",
                "",
                "",
                "def _append_log(message):",
                "    if not _FAKE_LOG:",
                "        return",
                "    with open(_FAKE_LOG, 'a', encoding='utf-8') as handle:",
                "        handle.write(str(message) + '\\n')",
                "",
                "",
                "class _FakeHTTPResponse:",
                "    def __init__(self, body, *, status=200, headers=None):",
                "        self._body = body if isinstance(body, bytes) else str(body).encode('utf-8')",
                "        self.status = int(status)",
                "        self.code = int(status)",
                "        self.headers = headers or {}",
                "",
                "    def read(self, *args, **kwargs):",
                "        return self._body",
                "",
                "    def __enter__(self):",
                "        return self",
                "",
                "    def __exit__(self, exc_type, exc, tb):",
                "        return False",
                "",
                "",
                "def _request_components(request_or_url, data=None):",
                "    if hasattr(request_or_url, 'full_url'):",
                "        request = request_or_url",
                "        url = request.full_url",
                "        method = getattr(request, 'method', None) or request.get_method()",
                "        headers = dict(getattr(request, 'headers', {}) or {})",
                "        body = getattr(request, 'data', None)",
                "    else:",
                "        url = str(request_or_url)",
                "        method = 'POST' if data is not None else 'GET'",
                "        headers = {}",
                "        body = data",
                "    if isinstance(body, bytes):",
                "        body_text = body.decode('utf-8')",
                "    elif body is None:",
                "        body_text = ''",
                "    else:",
                "        body_text = str(body)",
                "    return url, str(method).upper(), headers, body_text",
                "",
                "",
                "def _json_response(payload, *, status=200):",
                "    return _FakeHTTPResponse(json.dumps(payload), status=status, headers={'Content-Type': 'application/json'})",
                "",
                "",
                "def _handle_fake_http(request_or_url, data=None):",
                "    url, method, headers, body_text = _request_components(request_or_url, data=data)",
                "    parsed = urlparse(url)",
                "    host = parsed.netloc.casefold()",
                "    path = parsed.path",
                "    query = parse_qs(parsed.query)",
                "    _append_log(f'{method} {url}')",
                "    if host == 'api.example.com':",
                "        if path == '/items/42' and method == 'GET':",
                "            return _json_response({'id': 42, 'name': 'widget-42'})",
                "        if path == '/search' and method == 'GET':",
                "            return _json_response({'items': ['widget-a', 'widget-b'], 'query': {k: v[-1] for k, v in query.items()}})",
                "        if path == '/users' and method == 'POST':",
                "            return _json_response({'status': 'created', 'payload': json.loads(body_text or '{}')}, status=201)",
                "        if path == '/users/42' and method in {'PUT', 'PATCH'}:",
                "            return _json_response({'status': 'updated', 'method': method, 'payload': json.loads(body_text or '{}')})",
                "        if path == '/users/42' and method == 'DELETE':",
                "            return _FakeHTTPResponse(json.dumps({'status': 'deleted', 'url': url}), status=200, headers={'Content-Type': 'application/json'})",
                "        if path == '/profile' and method == 'GET':",
                "            token = headers.get('Authorization', '')",
                "            return _json_response({'status': 'ok', 'authorization': token, 'profile': {'name': 'demo-user'}})",
                "        if path == '/items' and method == 'GET' and 'page' not in query:",
                "            return _json_response({'items': [1, 2, 3], 'headers': headers})",
                "        if path == '/items' and method == 'GET' and 'page' in query:",
                "            return _json_response({'page': int(query.get('page', ['1'])[-1]), 'per_page': int(query.get('per_page', ['10'])[-1]), 'items': ['item-1', 'item-2']})",
                "        if path == '/token' and method == 'POST':",
                "            form = {k: v[-1] for k, v in parse_qs(body_text).items()}",
                "            return _json_response({'access_token': 'fake-access-token', 'token_type': 'bearer', 'scope': form.get('scope', '')})",
                "        if path == '/jobs/42' and method == 'GET':",
                "            count = _POLL_COUNTS.get(url, 0) + 1",
                "            _POLL_COUNTS[url] = count",
                "            state = 'completed' if count >= 2 else 'running'",
                "            return _json_response({'status': state, 'attempt': count})",
                "    if host == 'example.com' and path == '/report.pdf' and method == 'GET':",
                "        return _FakeHTTPResponse(b'%PDF-1.4\\n% workstation fake report\\n', status=200, headers={'Content-Type': 'application/pdf'})",
                "    return None",
                "",
                "",
                "def _fake_urlopen(request_or_url, data=None, *args, **kwargs):",
                "    response = _handle_fake_http(request_or_url, data=data)",
                "    if response is not None:",
                "        return response",
                "    return _ORIGINAL_URLOPEN(request_or_url, data=data, *args, **kwargs)",
                "",
                "",
                "_urllib_request.urlopen = _fake_urlopen",
            ]
        )
        + "\n"
    )
    pythonpath = str(fake_root)
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath = pythonpath + os.pathsep + existing_pythonpath
    return {
        "PYTHONPATH": pythonpath,
        "WORKSTATION_APICLIENT_FAKE_LOG": str(fake_log),
    }


def _materialize_ansible_fake_toolchain(report_dir: Path) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation validation of ansible trial workers, helps with creating one fake `ansible-playbook` toolchain so bounded localhost automation prompts can execute deterministically without mutating real host packages, services, or users.

    Reference to Theory:
        Supports safe workstation/trial compatibility work by preserving the governed ansible worker surface while replacing privileged or host-specific side effects with validator-owned fixtures.

    Example Input Output:
        Input: `_materialize_ansible_fake_toolchain(Path('/tmp/report/ansible'))`
        Output: {'PATH': '/tmp/report/ansible/fakebin:...', 'WORKSTATION_ANSIBLE_FAKE_LOG': '/tmp/report/ansible/fake_ansible.log'}

    Args:
        report_dir: Value for `report_dir` used by `_materialize_ansible_fake_toolchain`. Expected type: `Path`.

    Returns:
        dict[str, str]: Result produced by `_materialize_ansible_fake_toolchain`.
    """
    fakebin = Path(report_dir) / "fakebin"
    fakebin.mkdir(parents=True, exist_ok=True)
    fake_log = Path(report_dir) / "fake_ansible.log"
    fake_ansible = fakebin / "ansible-playbook"
    fake_ansible.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import json",
                "import os",
                "import shutil",
                "import sys",
                "import zipfile",
                "from pathlib import Path",
                "",
                "_FAKE_LOG = os.getenv('WORKSTATION_ANSIBLE_FAKE_LOG', '')",
                "",
                "",
                "def _append_log(message):",
                "    if not _FAKE_LOG:",
                "        return",
                "    with open(_FAKE_LOG, 'a', encoding='utf-8') as handle:",
                "        handle.write(str(message) + '\\n')",
                "",
                "",
                "def _load_vars(argv):",
                "    for index, value in enumerate(argv):",
                "        if value == '--extra-vars' and index + 1 < len(argv):",
                "            extra = argv[index + 1]",
                "            if extra.startswith('@'):",
                "                return json.loads(Path(extra[1:]).read_text(encoding='utf-8'))",
                "    return {}",
                "",
                "",
                "def _load_playbook_text(argv):",
                "    for value in argv[1:]:",
                "        if value.startswith('-'):",
                "            continue",
                "        candidate = Path(value)",
                "        if candidate.exists():",
                "            return candidate.read_text(encoding='utf-8')",
                "    return ''",
                "",
                "",
                "def _task_name(playbook_text):",
                "    for line in playbook_text.splitlines():",
                "        stripped = line.strip()",
                "        if stripped.startswith('- name:'):",
                "            return stripped.split(':', 1)[1].strip()",
                "    return ''",
                "",
                "",
                "def _render_port(value):",
                "    return str(value).strip() or '8080'",
                "",
                "",
                "def _write_text(path_text, content):",
                "    path = Path(path_text)",
                "    path.parent.mkdir(parents=True, exist_ok=True)",
                "    path.write_text(content, encoding='utf-8')",
                "",
                "",
                "def _stdout(task_name, *, changed=True, ok=True, message='localhost'):",
                "    task_status = 'changed' if changed else 'ok'",
                "    recap_ok = '1' if ok else '0'",
                "    recap_changed = '1' if changed and ok else '0'",
                "    recap_failed = '0' if ok else '1'",
                "    return '\\n'.join([",
                "        'PLAY [localhost] ***************************************************************',",
                "        '',",
                "        f'TASK [{task_name}] ******************************************************',",
                "        f'{task_status}: [{message}]',",
                "        '',",
                "        'PLAY RECAP *********************************************************************',",
                "        f'{message:<26} : ok={recap_ok}    changed={recap_changed}    unreachable=0    failed={recap_failed}    skipped=0    rescued=0    ignored=0',",
                "    ])",
                "",
                "",
                "def main(argv):",
                "    playbook_text = _load_playbook_text(argv)",
                "    payload = _load_vars(argv)",
                "    task_name = _task_name(playbook_text)",
                "    _append_log(json.dumps({'argv': argv[1:], 'task_name': task_name, 'payload': payload}, sort_keys=True))",
                "    try:",
                "        if 'package:' in playbook_text:",
                "            sys.stdout.write(_stdout(task_name or 'Ensure package is installed', changed=False) + '\\n')",
                "            return 0",
                "        if 'file:' in playbook_text and 'state: directory' in playbook_text:",
                "            path = Path(str(payload.get('path', '')))",
                "            path.mkdir(parents=True, exist_ok=True)",
                "            mode = str(payload.get('mode', '')).strip()",
                "            if mode:",
                "                path.chmod(int(mode, 8))",
                "            sys.stdout.write(_stdout(task_name or 'Ensure directory exists') + '\\n')",
                "            return 0",
                "        if 'copy:' in playbook_text and 'remote_src: true' in playbook_text:",
                "            source = Path(str(payload.get('source', '')))",
                "            destination = Path(str(payload.get('destination', '')))",
                "            destination.parent.mkdir(parents=True, exist_ok=True)",
                "            shutil.copyfile(source, destination)",
                "            sys.stdout.write(_stdout(task_name or 'Copy file to destination') + '\\n')",
                "            return 0",
                "        if 'copy:' in playbook_text and 'content:' in playbook_text and 'port={{ port }}' not in playbook_text:",
                "            _write_text(str(payload.get('path', '')), str(payload.get('content', '')))",
                "            sys.stdout.write(_stdout(task_name or 'Write file content') + '\\n')",
                "            return 0",
                "        if 'lineinfile:' in playbook_text:",
                "            path = Path(str(payload.get('path', '')))",
                "            path.parent.mkdir(parents=True, exist_ok=True)",
                "            existing = path.read_text(encoding='utf-8') if path.exists() else ''",
                "            line = str(payload.get('line', ''))",
                "            lines = existing.splitlines()",
                "            if line not in lines:",
                "                if existing and not existing.endswith('\\n'):",
                "                    existing += '\\n'",
                "                existing += line + '\\n'",
                "                path.write_text(existing, encoding='utf-8')",
                "            sys.stdout.write(_stdout(task_name or 'Ensure line is present') + '\\n')",
                "            return 0",
                "        if 'get_url:' in playbook_text:",
                "            destination = Path(str(payload.get('destination', '')))",
                "            destination.parent.mkdir(parents=True, exist_ok=True)",
                "            destination.write_text('<html><body>fake ansible download</body></html>\\n', encoding='utf-8')",
                "            sys.stdout.write(_stdout(task_name or 'Download URL to file') + '\\n')",
                "            return 0",
                "        if 'unarchive:' in playbook_text:",
                "            archive = Path(str(payload.get('archive', '')))",
                "            destination = Path(str(payload.get('destination', '')))",
                "            destination.mkdir(parents=True, exist_ok=True)",
                "            with zipfile.ZipFile(archive, 'r') as handle:",
                "                handle.extractall(destination)",
                "            sys.stdout.write(_stdout(task_name or 'Extract archive') + '\\n')",
                "            return 0",
                "        if 'service:' in playbook_text:",
                "            sys.stdout.write(_stdout(task_name or 'Ensure service is started and enabled', changed=False) + '\\n')",
                "            return 0",
                "        if 'git:' in playbook_text:",
                "            destination = Path(str(payload.get('destination', '')))",
                "            destination.mkdir(parents=True, exist_ok=True)",
                "            _write_text(str(destination / 'README.md'), '# fake cloned repo\\n')",
                "            _write_text(str(destination / '.git' / 'HEAD'), 'ref: refs/heads/main\\n')",
                "            sys.stdout.write(_stdout(task_name or 'Clone Git repository') + '\\n')",
                "            return 0",
                "        if 'file:' in playbook_text and 'state: file' in playbook_text:",
                "            path = Path(str(payload.get('path', '')))",
                "            if not path.exists():",
                "                path.parent.mkdir(parents=True, exist_ok=True)",
                "                path.write_text('', encoding='utf-8')",
                "            mode = str(payload.get('mode', '')).strip()",
                "            if mode:",
                "                path.chmod(int(mode, 8))",
                "            sys.stdout.write(_stdout(task_name or 'Ensure file mode') + '\\n')",
                "            return 0",
                "        if 'user:' in playbook_text:",
                "            sys.stdout.write(_stdout(task_name or 'Ensure user exists', changed=False) + '\\n')",
                "            return 0",
                "        if 'copy:' in playbook_text and 'port={{ port }}' in playbook_text:",
                "            _write_text(str(payload.get('path', '')), f\"port={_render_port(payload.get('port'))}\\n\")",
                "            sys.stdout.write(_stdout(task_name or 'Render template content') + '\\n')",
                "            return 0",
                "        sys.stderr.write('fake ansible-playbook did not recognize the playbook shape\\n')",
                "        return 2",
                "    except Exception as exc:",
                "        sys.stderr.write(str(exc) + '\\n')",
                "        return 1",
                "",
                "",
                "if __name__ == '__main__':",
                "    raise SystemExit(main(sys.argv))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    fake_ansible.chmod(0o755)
    return {
        "PATH": str(fakebin) + os.pathsep + os.environ.get("PATH", ""),
        "WORKSTATION_ANSIBLE_FAKE_LOG": str(fake_log),
    }


def _materialize_sdkuser_fake_sdk_environment(report_dir: Path) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation validation of SDK-user trial workers, helps with creating one fake SDK import layer so child Python workers can exercise the expected client shapes deterministically without depending on external package installation or real cloud credentials.

    Reference to Theory:
        Supports safe workstation/trial compatibility work by preserving the governed SDK worker surface while replacing unstable package and service dependencies with validator-owned stand-ins.

    Example Input Output:
        Input: `_materialize_sdkuser_fake_sdk_environment(Path('/tmp/report/sdkuser'))`
        Output: {'PYTHONPATH': '/tmp/report/sdkuser/fake_sdk:...', 'WORKSTATION_SDKUSER_FAKE_LOG': '/tmp/report/sdkuser/fake_sdk.log'}

    Args:
        report_dir: Value for `report_dir` used by `_materialize_sdkuser_fake_sdk_environment`. Expected type: `Path`.

    Returns:
        dict[str, str]: Result produced by `_materialize_sdkuser_fake_sdk_environment`.
    """
    fake_root = Path(report_dir) / "fake_sdk"
    fake_root.mkdir(parents=True, exist_ok=True)
    fake_log = Path(report_dir) / "fake_sdk.log"
    sitecustomize = fake_root / "sitecustomize.py"
    sitecustomize.write_text(
        "\n".join(
            [
                "import json",
                "import os",
                "import sys",
                "from pathlib import Path",
                "from types import ModuleType, SimpleNamespace",
                "",
                "_FAKE_LOG = os.getenv('WORKSTATION_SDKUSER_FAKE_LOG', '')",
                "",
                "",
                "def _append_log(message):",
                "    if not _FAKE_LOG:",
                "        return",
                "    with open(_FAKE_LOG, 'a', encoding='utf-8') as handle:",
                "        handle.write(str(message) + '\\n')",
                "",
                "",
                "def _register(name, module):",
                "    sys.modules[name] = module",
                "    return module",
                "",
                "",
                "def _make_openai_module():",
                "    module = ModuleType('openai')",
                "    class _Responses:",
                "        def create(self, *, model, input):",
                "            _append_log(json.dumps({'sdk': 'openai.responses', 'model': model, 'input': input}, sort_keys=True))",
                "            text = 'Hello.' if 'hello' in str(input).casefold() else f'Fake OpenAI response for: {input}'",
                "            return SimpleNamespace(output_text=text, id='resp_fake_openai_1')",
                "    class _Embeddings:",
                "        def create(self, *, model, input):",
                "            _append_log(json.dumps({'sdk': 'openai.embeddings', 'model': model, 'input': input}, sort_keys=True))",
                "            return SimpleNamespace(data=[SimpleNamespace(embedding=[0.11, 0.22, 0.33, 0.44])])",
                "    class OpenAI:",
                "        def __init__(self, *args, **kwargs):",
                "            self.responses = _Responses()",
                "            self.embeddings = _Embeddings()",
                "    module.OpenAI = OpenAI",
                "    return module",
                "",
                "",
                "def _make_anthropic_module():",
                "    module = ModuleType('anthropic')",
                "    class Anthropic:",
                "        def __init__(self, *args, **kwargs):",
                "            self.messages = self",
                "        def create(self, *, model, max_tokens, messages):",
                "            _append_log(json.dumps({'sdk': 'anthropic.messages', 'model': model, 'max_tokens': max_tokens}, sort_keys=True))",
                "            text = 'API reliability is strongest when retries, backoff, and observability are built in.'",
                "            return SimpleNamespace(content=[SimpleNamespace(type='text', text=text)])",
                "    module.Anthropic = Anthropic",
                "    return module",
                "",
                "",
                "def _make_boto3_module():",
                "    module = ModuleType('boto3')",
                "    class _S3Client:",
                "        def list_objects_v2(self, *, Bucket, Prefix=''):",
                "            _append_log(json.dumps({'sdk': 'boto3.s3.list_objects_v2', 'bucket': Bucket, 'prefix': Prefix}, sort_keys=True))",
                "            keys = ['reports/daily.json', 'reports/report.txt', 'logs/app.log']",
                "            filtered = [key for key in keys if str(key).startswith(str(Prefix or ''))]",
                "            return {'Contents': [{'Key': key} for key in filtered]}",
                "        def upload_file(self, local_path, bucket, key):",
                "            _append_log(json.dumps({'sdk': 'boto3.s3.upload_file', 'local_path': local_path, 'bucket': bucket, 'key': key}, sort_keys=True))",
                "            return None",
                "    def client(service_name):",
                "        if service_name != 's3':",
                "            raise ValueError(f'Unsupported fake boto3 service: {service_name}')",
                "        return _S3Client()",
                "    module.client = client",
                "    return module",
                "",
                "",
                "def _make_google_modules():",
                "    google = ModuleType('google')",
                "    cloud = ModuleType('google.cloud')",
                "    storage = ModuleType('google.cloud.storage')",
                "    class _Blob:",
                "        def __init__(self, name):",
                "            self.name = name",
                "        def download_to_filename(self, destination):",
                "            _append_log(json.dumps({'sdk': 'google.cloud.storage.download_to_filename', 'blob_name': self.name, 'destination': destination}, sort_keys=True))",
                "            path = Path(destination)",
                "            path.parent.mkdir(parents=True, exist_ok=True)",
                "            path.write_text('{\"status\":\"ok\",\"source\":\"fake-gcs\"}\\n', encoding='utf-8')",
                "    class _Bucket:",
                "        def __init__(self, name):",
                "            self.name = name",
                "        def blob(self, blob_name):",
                "            return _Blob(blob_name)",
                "    class Client:",
                "        def bucket(self, name):",
                "            _append_log(json.dumps({'sdk': 'google.cloud.storage.bucket', 'bucket': name}, sort_keys=True))",
                "            return _Bucket(name)",
                "    storage.Client = Client",
                "    cloud.storage = storage",
                "    google.cloud = cloud",
                "    _register('google', google)",
                "    _register('google.cloud', cloud)",
                "    _register('google.cloud.storage', storage)",
                "",
                "",
                "def _make_slack_module():",
                "    module = ModuleType('slack_sdk')",
                "    class WebClient:",
                "        def __init__(self, token):",
                "            self.token = token",
                "        def chat_postMessage(self, *, channel, text):",
                "            _append_log(json.dumps({'sdk': 'slack_sdk.chat_postMessage', 'channel': channel, 'text': text}, sort_keys=True))",
                "            return {'ts': '12345.6789'}",
                "    module.WebClient = WebClient",
                "    return module",
                "",
                "",
                "def _make_github_module():",
                "    module = ModuleType('github')",
                "    class _Issue:",
                "        def __init__(self, number, title):",
                "            self.number = number",
                "            self.title = title",
                "    class _Repo:",
                "        def __init__(self, name):",
                "            self.name = name",
                "        def get_issues(self, *, state='open'):",
                "            _append_log(json.dumps({'sdk': 'github.get_issues', 'repo': self.name, 'state': state}, sort_keys=True))",
                "            return [_Issue(1, 'Fix flaky deploy'), _Issue(2, 'Improve API reliability docs')]",
                "    class Github:",
                "        def __init__(self, token):",
                "            self.token = token",
                "        def get_repo(self, name):",
                "            return _Repo(name)",
                "    module.Github = Github",
                "    return module",
                "",
                "",
                "def _make_kubernetes_modules():",
                "    kubernetes = ModuleType('kubernetes')",
                "    client = ModuleType('kubernetes.client')",
                "    config = ModuleType('kubernetes.config')",
                "    def load_kube_config():",
                "        _append_log(json.dumps({'sdk': 'kubernetes.load_kube_config'}, sort_keys=True))",
                "        return None",
                "    class CoreV1Api:",
                "        def list_namespaced_pod(self, *, namespace):",
                "            _append_log(json.dumps({'sdk': 'kubernetes.list_namespaced_pod', 'namespace': namespace}, sort_keys=True))",
                "            pods = [SimpleNamespace(metadata=SimpleNamespace(name='api-0')), SimpleNamespace(metadata=SimpleNamespace(name='worker-0'))]",
                "            return SimpleNamespace(items=pods)",
                "    config.load_kube_config = load_kube_config",
                "    client.CoreV1Api = CoreV1Api",
                "    kubernetes.client = client",
                "    kubernetes.config = config",
                "    _register('kubernetes', kubernetes)",
                "    _register('kubernetes.client', client)",
                "    _register('kubernetes.config', config)",
                "",
                "",
                "def _make_redis_module():",
                "    module = ModuleType('redis')",
                "    class _RedisClient:",
                "        def __init__(self, url):",
                "            self.url = url",
                "        def get(self, key):",
                "            _append_log(json.dumps({'sdk': 'redis.get', 'url': self.url, 'key': key}, sort_keys=True))",
                "            return b'fake-session-value'",
                "    def from_url(url):",
                "        return _RedisClient(url)",
                "    module.from_url = from_url",
                "    return module",
                "",
                "",
                "def _make_stripe_module():",
                "    module = ModuleType('stripe')",
                "    module.api_key = ''",
                "    class _Customer:",
                "        @staticmethod",
                "        def retrieve(customer_id):",
                "            _append_log(json.dumps({'sdk': 'stripe.Customer.retrieve', 'customer_id': customer_id}, sort_keys=True))",
                "            return {'id': customer_id, 'email': 'customer@example.com'}",
                "    module.Customer = _Customer",
                "    return module",
                "",
                "",
                "def _make_supabase_module():",
                "    module = ModuleType('supabase')",
                "    class _Query:",
                "        def __init__(self, table):",
                "            self._table = table",
                "        def select(self, *_args, **_kwargs):",
                "            return self",
                "        def execute(self):",
                "            _append_log(json.dumps({'sdk': 'supabase.select', 'table': self._table}, sort_keys=True))",
                "            return SimpleNamespace(data=[{'id': 1, 'name': 'Ada'}, {'id': 2, 'name': 'Linus'}])",
                "    class _Client:",
                "        def __init__(self, url, key):",
                "            self.url = url",
                "            self.key = key",
                "        def table(self, name):",
                "            return _Query(name)",
                "    def create_client(url, key):",
                "        return _Client(url, key)",
                "    module.create_client = create_client",
                "    return module",
                "",
                "",
                "_register('openai', _make_openai_module())",
                "_register('anthropic', _make_anthropic_module())",
                "_register('boto3', _make_boto3_module())",
                "_make_google_modules()",
                "_register('slack_sdk', _make_slack_module())",
                "_register('github', _make_github_module())",
                "_make_kubernetes_modules()",
                "_register('redis', _make_redis_module())",
                "_register('stripe', _make_stripe_module())",
                "_register('supabase', _make_supabase_module())",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    pythonpath = str(fake_root)
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if existing_pythonpath:
        pythonpath = pythonpath + os.pathsep + existing_pythonpath
    return {
        "PYTHONPATH": pythonpath,
        "WORKSTATION_SDKUSER_FAKE_LOG": str(fake_log),
    }


def _materialize_common_trial_host_fixtures() -> None:
    """
    High Level Purpose:
        In circumstances like workstation validation across shell-, ansible-, and SDK-oriented trial domains, helps with creating a small stable set of local host fixtures that those prompts assume exist.

    Reference to Theory:
        Supports repeatable workstation/trial compatibility runs by replacing incidental host preconditions with explicit validator-owned fixtures.

    Example Input Output:
        Input: `_materialize_common_trial_host_fixtures()`
        Output: None

    Args:
        None.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    zip_path = Path("/tmp/example.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("example/README.txt", "workstation trial fixture\n")
    Path("/tmp/report.txt").write_text("workstation sdk fixture\n")
    Path("/tmp/demo.sh").write_text("#!/usr/bin/env bash\nprintf 'demo fixture\\n'\n")


def _slugify_prompt(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like workstation trial reporting, helps with converting one prompt into a short stable filename stem.

    Reference to Theory:
        Supports durable workstation audit artifacts by giving each prompt report a predictable path without depending on the model output.

    Example Input Output:
        Input: `_slugify_prompt('Find every occurrence of the symbol BSSCController under /tmp/project.')`
        Output: 'find_every_occurrence_of_the_symbol_bssccontroller_under'

    Args:
        text: Value for `text` used by `_slugify_prompt`. Expected type: `str`.

    Returns:
        str: Result produced by `_slugify_prompt`.
    """
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    if not tokens:
        return "prompt"
    return "_".join(tokens[:8]).strip("_") or "prompt"


def _parse_trial_prompts(path: Path) -> tuple[str, ...]:
    """
    High Level Purpose:
        In circumstances like workstation trial auditing, helps with extracting prompt bullets from one `PROMPTS.md` file into executable workstation prompts.

    Reference to Theory:
        Supports workstation compatibility checks against the existing trial corpus by reusing the prompt surfaces already curated for each domain.

    Example Input Output:
        Input: `_parse_trial_prompts(Path('/tmp/trials/demo/PROMPTS.md'))`
        Output: ('What is gene expression?',)

    Args:
        path: Value for `path` used by `_parse_trial_prompts`. Expected type: `Path`.

    Returns:
        tuple[str, ...]: Result produced by `_parse_trial_prompts`.
    """
    if not path.exists():
        return ()
    prompts: list[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            prompt = line[2:].strip()
            if prompt:
                prompts.append(prompt)
    return tuple(prompts)


def _trial_domain_names(trials_root: Path, requested_domains: tuple[str, ...] | None) -> tuple[str, ...]:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with resolving the ordered set of domain names that should be audited.

    Reference to Theory:
        Supports repeatable workstation compatibility runs by keeping domain selection explicit and stable.

    Example Input Output:
        Input: `_trial_domain_names(Path('/tmp/trials'), ('chemistry', 'python'))`
        Output: ('chemistry', 'python')

    Args:
        trials_root: Value for `trials_root` used by `_trial_domain_names`. Expected type: `Path`.
        requested_domains: Value for `requested_domains` used by `_trial_domain_names`. Expected type: `tuple[str, ...] | None`.

    Returns:
        tuple[str, ...]: Result produced by `_trial_domain_names`.
    """
    if requested_domains:
        return tuple(dict.fromkeys(str(item).strip() for item in requested_domains if str(item).strip()))
    discovered = sorted(
        entry.name
        for entry in Path(trials_root).iterdir()
        if entry.is_dir() and ((entry / "PROMPTS.md").exists() or (entry / "skill.yaml").exists())
    )
    return tuple(discovered)


def _workstation_prompt_route(report: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation trial audits, helps with classifying how one workstation turn completed so compatibility issues can be tied to routing rather than only final text.

    Reference to Theory:
        Supports workstation/trial compatibility work by distinguishing direct worker composition, governed skill invocation, and broader tool fallback.

    Example Input Output:
        Input: `_workstation_prompt_route({'model': 'workstation-direct-composition', 'tool_receipts': [{'name': 'ws.skill.invoke'}]})`
        Output: {'used_direct_composition': True, 'used_skill_invoke': True, 'tool_names': ['ws.skill.invoke'], 'invoked_skill_titles': ['Workstation Repo Search']}

    Args:
        report: Value for `report` used by `_workstation_prompt_route`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_workstation_prompt_route`.
    """
    tool_receipts = list(report.get("tool_receipts", []))
    tool_names = [
        str(item.get("name", "")).strip()
        for item in tool_receipts
        if isinstance(item, dict) and str(item.get("name", "")).strip()
    ]
    invoked_skill_titles: list[str] = []
    for item in tool_receipts:
        if not isinstance(item, dict) or str(item.get("name", "")).strip() != "ws.skill.invoke":
            continue
        result = item.get("result", {})
        arguments = item.get("arguments", {})
        skill_title = ""
        if isinstance(result, dict):
            skill_title = str(result.get("skill_title", "")).strip()
        if not skill_title and isinstance(arguments, dict):
            skill_title = str(arguments.get("skill_title", "")).strip()
        if skill_title:
            invoked_skill_titles.append(skill_title)
    return {
        "used_direct_composition": str(report.get("model", "")).strip() == "workstation-direct-composition",
        "used_skill_invoke": "ws.skill.invoke" in tool_names,
        "tool_names": tool_names,
        "invoked_skill_titles": invoked_skill_titles,
    }


def _trimmed_text(value: Any, *, limit: int = 12000) -> str:
    """
    High Level Purpose:
        In circumstances like workstation trial reporting, helps with bounding one captured text field so the validator does not exhaust local disk by persisting full assistant transcripts for every prompt.

    Reference to Theory:
        Supports repeatable workstation audits by keeping the report artifacts durable and compact while preserving enough evidence to classify routing and answer quality.

    Example Input Output:
        Input: `_trimmed_text('abc', limit=2)`
        Output: 'ab'

    Args:
        value: Value for `value` used by `_trimmed_text`. Expected type: `Any`.
        limit: Value for `limit` used by `limit`. Expected type: `int`. Defaults to `12000`.

    Returns:
        str: Result produced by `_trimmed_text`.
    """
    text = str(value or "")
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit]


def _bounded_tool_receipts(report: dict[str, Any]) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with projecting raw tool receipts into a compact form that still preserves routing and basic error information.

    Reference to Theory:
        Supports workstation audit durability by keeping only the receipt fields needed for route classification and debugging instead of writing full nested traces for every prompt.

    Example Input Output:
        Input: `_bounded_tool_receipts({'tool_receipts': [{'name': 'ws.skill.invoke', 'result': {'skill_title': 'Demo'}}]})`
        Output: [{'name': 'ws.skill.invoke', 'result': {'skill_title': 'Demo'}}]

    Args:
        report: Value for `report` used by `_bounded_tool_receipts`. Expected type: `dict[str, Any]`.

    Returns:
        list[dict[str, Any]]: Result produced by `_bounded_tool_receipts`.
    """
    bounded: list[dict[str, Any]] = []
    for item in list(report.get("tool_receipts", [])):
        if not isinstance(item, dict):
            continue
        arguments = item.get("arguments", {})
        result = item.get("result", {})
        bounded.append(
            {
                "name": str(item.get("name", "")),
                "arguments": {
                    "skill_title": str(arguments.get("skill_title", "")) if isinstance(arguments, dict) else "",
                    "target": str(arguments.get("target", "")) if isinstance(arguments, dict) else "",
                },
                "result": {
                    "status": str(result.get("status", "")) if isinstance(result, dict) else "",
                    "skill_title": str(result.get("skill_title", "")) if isinstance(result, dict) else "",
                    "executor_framework": str(result.get("executor_framework", "")) if isinstance(result, dict) else "",
                    "error": _trimmed_text(result.get("error", ""), limit=500) if isinstance(result, dict) else "",
                    "error_type": str(result.get("error_type", "")) if isinstance(result, dict) else "",
                    "answer": _trimmed_text(result.get("answer", ""), limit=2000) if isinstance(result, dict) else "",
                },
            }
        )
    return bounded


def _terminal_tool_receipt_status(report: dict[str, Any]) -> str:
    """
    High Level Purpose:
        In circumstances like workstation trial result classification, helps with extracting the terminal bounded tool status so prompt success cannot drift away from the last executed tool outcome.

    Reference to Theory:
        Supports workstation audit integrity by wiring durable per-prompt status to the actual last tool result instead of only the assistant text.

    Example Input Output:
        Input: `_terminal_tool_receipt_status({'tool_receipts': [{'result': {'status': 'approval_required'}}]})`
        Output: 'approval_required'

    Args:
        report: Value for `report` used by `_terminal_tool_receipt_status`. Expected type: `dict[str, Any]`.

    Returns:
        str: Result produced by `_terminal_tool_receipt_status`.
    """
    for item in reversed(list(report.get("tool_receipts", []))):
        if not isinstance(item, dict):
            continue
        result = item.get("result", {})
        if not isinstance(result, dict):
            continue
        status = str(result.get("status", "")).strip()
        if status:
            return status
    return ""


def _bounded_prompt_report(report: dict[str, Any]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with reducing one raw workstation turn report into a compact durable JSON artifact.

    Reference to Theory:
        Supports large workstation sweeps by keeping per-prompt reports bounded without losing the route information needed to classify compatibility gaps.

    Example Input Output:
        Input: `_bounded_prompt_report({'assistant_text': 'ok', 'tool_receipts': []})`
        Output: {'assistant_text': 'ok', 'tool_receipts': []}

    Args:
        report: Value for `report` used by `_bounded_prompt_report`. Expected type: `dict[str, Any]`.

    Returns:
        dict[str, Any]: Result produced by `_bounded_prompt_report`.
    """
    task_contract = report.get("task_contract", {})
    return {
        "assistant_text": _trimmed_text(report.get("assistant_text", "")),
        "model": str(report.get("model", "")),
        "rounds": int(report.get("rounds", 0) or 0),
        "tool_receipts": _bounded_tool_receipts(report),
        "task_contract": {
            "semantic_unit": str(task_contract.get("semantic_unit", "")) if isinstance(task_contract, dict) else "",
        },
    }


def _run_default_workstation_trial_prompt(
    *,
    root_path: Path,
    prompt: str,
    model: str | None,
    max_tool_rounds: int,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like real workstation trial validation, helps with running one prompt through the normal workstation session path while auto-approving bounded one-invocation delegation so the trial can observe the final worker outcome.

    Reference to Theory:
        Supports faithful workstation compatibility audits by exercising the real prompt surface while keeping delegation host-owned and explicit.

    Example Input Output:
        Input: `_run_default_workstation_trial_prompt(root_path=Path('/tmp/ws'), prompt='Write hello', model=None, max_tool_rounds=8)`
        Output: {'assistant_text': 'Wrote hello', 'tool_receipts': [{'name': 'ws.skill.invoke', 'result': {'status': 'ok'}}]}

    Args:
        root_path: Value for `root_path` used by `root_path`. Expected type: `Path`.
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.
        model: Value for `model` used by `model`. Expected type: `str | None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`.

    Returns:
        dict[str, Any]: Result produced by `_run_default_workstation_trial_prompt`.
    """
    return prompt_workstation_session(
        root_path=root_path,
        prompt=prompt,
        model=model,
        max_tool_rounds=max_tool_rounds,
        delegation_approval_callback=lambda _request: True,
    )


def _cleanup_prompt_session(prompt_root: Path, *, keep: bool) -> None:
    """
    High Level Purpose:
        In circumstances like workstation trial validation, helps with reclaiming disk by removing one per-prompt workstation session tree after the validator has extracted the needed routing evidence.

    Reference to Theory:
        Supports broad workstation sweeps over the trial corpus by keeping prompt-local session state ephemeral unless that prompt failed and needs debugging.

    Example Input Output:
        Input: `_cleanup_prompt_session(Path('/tmp/ws/sessions/01_demo'), keep=False)`
        Output: None

    Args:
        prompt_root: Value for `prompt_root` used by `_cleanup_prompt_session`. Expected type: `Path`.
        keep: Value for `keep` used by `keep`. Expected type: `bool`.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """
    if keep:
        return
    shutil.rmtree(prompt_root, ignore_errors=True)


def validate_workstation_trial_domains(
    *,
    domains: tuple[str, ...] | None = None,
    workspace_path: Path | None = None,
    trials_root: Path = TRIALS_ROOT,
    report_root: Path | None = None,
    model: str | None = None,
    max_tool_rounds: int = 8,
    prompt_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like auditing workstation compatibility against the existing trial corpus, helps with importing each domain bundle into a fresh per-domain workstation skill store and running its prompt set through fresh workstation sessions.

    Reference to Theory:
        Supports workstation/trial integration by testing the workstation shell against the same governed worker corpora used elsewhere in the repository, while keeping the audit isolated from the outer 5-layer BSSC architecture.

    Example Input Output:
        Input: `validate_workstation_trial_domains(domains=('symbolsearch',), workspace_path=Path('/tmp/project'), model='gpt-5.4')`
        Output: {'status': 'ok', 'domains': [{'domain': 'symbolsearch', 'prompt_summary': {'ok': 12, 'total': 12}}]}

    Args:
        domains: Value for `domains` used by `validate_workstation_trial_domains`. Expected type: `tuple[str, ...] | None`. Defaults to `None`.
        workspace_path: Value for `workspace_path` used by `workspace_path`. Expected type: `Path | None`. Defaults to `None`.
        trials_root: Value for `trials_root` used by `trials_root`. Expected type: `Path`. Defaults to `TRIALS_ROOT`.
        report_root: Value for `report_root` used by `report_root`. Expected type: `Path | None`. Defaults to `None`.
        model: Value for `model` used by `model`. Expected type: `str | None`. Defaults to `None`.
        max_tool_rounds: Value for `max_tool_rounds` used by `max_tool_rounds`. Expected type: `int`. Defaults to `8`.
        prompt_runner: Value for `prompt_runner` used by `prompt_runner`. Expected type: `Callable[..., dict[str, Any]] | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `validate_workstation_trial_domains`.
    """
    runner = prompt_runner or _run_default_workstation_trial_prompt
    applied_env = _load_local_env_if_needed()
    _materialize_common_trial_host_fixtures()
    selected_domains = _trial_domain_names(Path(trials_root), domains)
    workspace = Path(workspace_path or REPO_ROOT).expanduser().resolve()
    started_at = datetime.now(timezone.utc).isoformat()
    run_report_root = Path(report_root or (REPORTS_ROOT / f"workstation_trial_validation_{_utc_timestamp_slug()}"))
    run_report_root.mkdir(parents=True, exist_ok=True)
    domain_results: list[dict[str, Any]] = []
    for domain_name in selected_domains:
        domain_dir = Path(trials_root) / domain_name
        domain_report_dir = run_report_root / domain_name
        domain_report_dir.mkdir(parents=True, exist_ok=True)
        prompts_file = domain_dir / "PROMPTS.md"
        bundle_file = domain_dir / "skill.yaml"
        prompts = _parse_trial_prompts(prompts_file)
        if not prompts:
            domain_results.append(
                {
                    "domain": domain_name,
                    "status": "skipped_no_prompts",
                    "prompts_file": str(prompts_file),
                    "bundle_file": str(bundle_file),
                }
            )
            continue
        if not bundle_file.exists():
            domain_results.append(
                {
                    "domain": domain_name,
                    "status": "skipped_no_bundle",
                    "prompts_file": str(prompts_file),
                    "bundle_file": str(bundle_file),
                    "prompt_count": len(prompts),
                }
            )
            continue
        domain_sqlite = domain_report_dir / f"{domain_name}.sqlite3"
        if domain_sqlite.exists():
            domain_sqlite.unlink()
        canonical_export_path = domain_report_dir / "canonical_skill.yaml"
        domain_env_overrides: dict[str, str] = {}
        if domain_name == "deviceuser":
            domain_env_overrides = _materialize_deviceuser_fake_macos_toolchain(domain_report_dir)
        elif domain_name == "apiclient":
            domain_env_overrides = _materialize_apiclient_fake_http_environment(domain_report_dir)
        elif domain_name == "ansible":
            domain_env_overrides = _materialize_ansible_fake_toolchain(domain_report_dir)
        elif domain_name == "sdkuser":
            domain_env_overrides = _materialize_sdkuser_fake_sdk_environment(domain_report_dir)
        with _temporary_environment(domain_env_overrides):
            import_report = import_workstation_skill_file(
                skill_store_path=domain_sqlite,
                source_file=bundle_file,
                canonical_export_path=canonical_export_path,
            )
            catalog = list_available_workstation_skills(domain_sqlite)
            domain_world_root = domain_report_dir / "world"
            prompt_results: list[dict[str, Any]] = []
            for index, prompt in enumerate(prompts, start=1):
                prompt_slug = _slugify_prompt(prompt)
                prompt_root = domain_report_dir / "sessions" / f"{index:02d}_{prompt_slug}"
                launch_workstation_session(
                    root_path=prompt_root,
                    workspace_path=workspace,
                    blend_world_path=domain_world_root,
                    skills_sqlite_path=domain_sqlite,
                    initial_task="Use installed trial skills when appropriate.",
                )
                prompt_status = "ok"
                report_path = domain_report_dir / f"prompt_{index:02d}_{prompt_slug}.json"
                try:
                    report = runner(
                        root_path=prompt_root,
                        prompt=prompt,
                        model=model,
                        max_tool_rounds=max_tool_rounds,
                    )
                    bounded_report = _bounded_prompt_report(report)
                    report_path.write_text(json.dumps(bounded_report, indent=2, sort_keys=True) + "\n")
                    route = _workstation_prompt_route(bounded_report)
                    assistant_text = str(bounded_report.get("assistant_text", "")).strip()
                    terminal_tool_status = _terminal_tool_receipt_status(bounded_report)
                    if terminal_tool_status in {"error", "approval_required"}:
                        prompt_status = f"error_terminal_tool_{terminal_tool_status}"
                    elif not assistant_text:
                        prompt_status = "error_empty_answer"
                    prompt_results.append(
                        {
                            "name": prompt_slug,
                            "prompt": prompt,
                            "status": prompt_status,
                            "terminal_tool_status": terminal_tool_status,
                            "assistant_text": assistant_text,
                            "report": str(report_path),
                            "route": route,
                        }
                    )
                    _cleanup_prompt_session(prompt_root, keep=prompt_status != "ok")
                except Exception as exc:
                    prompt_status = "error_exception"
                    error_payload = {
                        "prompt": prompt,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    }
                    report_path.write_text(json.dumps(error_payload, indent=2, sort_keys=True) + "\n")
                    prompt_results.append(
                        {
                            "name": prompt_slug,
                            "prompt": prompt,
                            "status": prompt_status,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                            "report": str(report_path),
                            "route": {
                                "used_direct_composition": False,
                                "used_skill_invoke": False,
                                "tool_names": [],
                                "invoked_skill_titles": [],
                            },
                        }
                    )
                    _cleanup_prompt_session(prompt_root, keep=True)
        ok_count = sum(1 for item in prompt_results if item.get("status") == "ok")
        direct_count = sum(1 for item in prompt_results if item.get("route", {}).get("used_direct_composition"))
        skill_count = sum(1 for item in prompt_results if item.get("route", {}).get("used_skill_invoke"))
        domain_status = "ok" if ok_count == len(prompt_results) else ("partial" if ok_count else "error")
        domain_result = {
            "domain": domain_name,
            "status": domain_status,
            "prompts_file": str(prompts_file),
            "bundle_file": str(bundle_file),
            "sqlite": str(domain_sqlite),
            "canonical_export": str(canonical_export_path),
            "import_report": import_report,
            "skill_catalog_count": len(catalog),
            "world_root": str(domain_world_root.resolve()),
            "prompt_results": prompt_results,
            "prompt_summary": {
                "ok": ok_count,
                "total": len(prompt_results),
                "used_direct_composition": direct_count,
                "used_skill_invoke": skill_count,
            },
        }
        if "WORKSTATION_DEVICEUSER_FAKE_LOG" in domain_env_overrides:
            domain_result["fake_log"] = domain_env_overrides["WORKSTATION_DEVICEUSER_FAKE_LOG"]
        if "WORKSTATION_APICLIENT_FAKE_LOG" in domain_env_overrides:
            domain_result["fake_log"] = domain_env_overrides["WORKSTATION_APICLIENT_FAKE_LOG"]
        if "WORKSTATION_ANSIBLE_FAKE_LOG" in domain_env_overrides:
            domain_result["fake_log"] = domain_env_overrides["WORKSTATION_ANSIBLE_FAKE_LOG"]
        if "WORKSTATION_SDKUSER_FAKE_LOG" in domain_env_overrides:
            domain_result["fake_log"] = domain_env_overrides["WORKSTATION_SDKUSER_FAKE_LOG"]
        domain_results.append(domain_result)
    overall_status = "ok" if all(item.get("status") in {"ok", "skipped_no_bundle", "skipped_no_prompts"} for item in domain_results) else "partial"
    return {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "workspace": str(workspace),
        "trials_root": str(Path(trials_root).resolve()),
        "report_root": str(run_report_root),
        "model": str(model or ""),
        "max_tool_rounds": int(max_tool_rounds),
        "applied_env": applied_env,
        "domains": domain_results,
    }
