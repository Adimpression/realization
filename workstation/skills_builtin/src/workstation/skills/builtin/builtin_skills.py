# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
import json
from typing import Any

from realized_core_semantics.applied_model import Artifact


def _wat_bytes(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like authoring builtin workstation Wasm skills, helps with encoding UTF-8 JSON text into WAT byte escapes for static module data sections.

    Reference to Theory:
        Supports the workstation shell / worker-runtime model by letting builtin Wasm workers remain self-contained without ambient host files.

    Example Input Output:
        Input: `_wat_bytes(text='{"status":"ok"}')`
        Output: '\\7b\\22\\73\\74\\61\\74\\75\\73\\22\\3a\\22\\6f\\6b\\22\\7d'

    Args:
        text: Value for `text` used by `_wat_bytes`. Expected type: `str`.

    Returns:
        str: Result produced by `_wat_bytes`.
    """
    return "".join(f"\\{byte:02x}" for byte in text.encode("utf-8"))


def _repo_search_python_script() -> str:
    """
    High Level Purpose:
        In circumstances like providing one builtin higher-level workstation worker, helps with returning the governed Python body for repository search over delegated virtual mounts.

    Reference to Theory:
        Supports the workstation model by moving a higher-level behavior into a skill that sits on top of the workstation kernel rather than inside it.

    Example Input Output:
        Input: `_repo_search_python_script()`
        Output: 'from __future__ import annotations\\n...'

    Args:
        None.

    Returns:
        str: Result produced by `_repo_search_python_script`.
    """
    return """
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys

from python_skill_host import broker_request

_TEXT_SUFFIXES = (
    ".c",
    ".cc",
    ".cfg",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
)


def _candidate_paths(mount: str, relative_path: str) -> list[str]:
    seen: set[str] = set()
    matches: list[str] = []
    for suffix in _TEXT_SUFFIXES:
        result = broker_request("fs.find_mount", mount=mount, relative_path=relative_path, suffix=suffix)
        if result.get("status") != "ok":
            continue
        for item in result.get("matches", []):
            relative = str(item).strip()
            if not relative or relative in seen:
                continue
            seen.add(relative)
            matches.append(relative)
    return sorted(matches)


def _mount_relative_candidate_path(relative_path: str, candidate: str) -> str:
    normalized_relative_path = str(relative_path).strip().strip("/")
    normalized_candidate = str(candidate).strip().lstrip("/")
    if not normalized_relative_path:
        return normalized_candidate
    if not normalized_candidate:
        return normalized_relative_path
    return f"{normalized_relative_path}/{normalized_candidate}"


def main(
    mount: str,
    pattern: str,
    relative_path: str = "",
    *,
    glob: str = "",
    max_matches: int = 100,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    normalized_mount = str(mount).strip()
    normalized_pattern = str(pattern)
    normalized_relative_path = str(relative_path).strip()
    normalized_glob = str(glob).strip()
    bounded_max_matches = max(1, int(max_matches))
    if not normalized_mount:
        return {"status": "error", "answer": "No mount was provided.", "result": {"matches": []}}
    if not normalized_pattern:
        return {"status": "error", "answer": "No search pattern was provided.", "result": {"matches": []}}
    try:
        compiled = re.compile(normalized_pattern)
    except re.error:
        compiled = None
    matches: list[str] = []
    for candidate in _candidate_paths(normalized_mount, normalized_relative_path):
        if normalized_glob and not fnmatch.fnmatch(candidate, normalized_glob):
            continue
        read_result = broker_request(
            "fs.read_mount",
            mount=normalized_mount,
            relative_path=_mount_relative_candidate_path(normalized_relative_path, candidate),
        )
        if read_result.get("status") != "ok":
            continue
        text = str(read_result.get("text", ""))
        for line_number, line in enumerate(text.splitlines(), start=1):
            found = bool(compiled.search(line)) if compiled is not None else normalized_pattern in line
            if not found:
                continue
            matches.append(f"{candidate}:{line_number}:{line.strip()}")
            if len(matches) >= bounded_max_matches:
                break
        if len(matches) >= bounded_max_matches:
            break
    answer = f"Found {len(matches)} matches for {normalized_pattern!r}."
    return {
        "status": "ok",
        "answer": answer,
        "mount": normalized_mount,
        "relative_path": normalized_relative_path,
        "pattern": normalized_pattern,
        "glob": normalized_glob,
        "match_count": len(matches),
        "matches": matches,
    }


def run(payload: dict[str, object]) -> dict[str, object]:
    result_value = main(
        mount=str(payload.get("mount", "")),
        pattern=str(payload.get("pattern", "")),
        relative_path=str(payload.get("relative_path", "")),
        glob=str(payload.get("glob", "")),
        max_matches=int(payload.get("max_matches", 100)),
    )
    return {
        "status": "ok" if result_value.get("status") == "ok" else "error",
        "answer": str(result_value.get("answer", "")),
        "result": result_value,
        "notes": [],
    }


def __bssc_cli_main__() -> None:
    parser = argparse.ArgumentParser(description="Workstation Repo Search")
    parser.add_argument("--input-json", help="Optional JSON payload. Prefer stdin when omitted.")
    args = parser.parse_args()
    raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
    payload = json.loads(raw) if raw else {}
    if not isinstance(payload, dict):
        payload = {}
    sys.stdout.write(json.dumps(run(payload), indent=2, sort_keys=True))
    sys.stdout.write("\\n")


if __name__ == "__main__":
    __bssc_cli_main__()
""".strip()


def _repo_tree_python_script() -> str:
    """
    High Level Purpose:
        In circumstances like providing one builtin higher-level workstation worker, helps with returning the governed Python body for bounded directory-tree inspection over delegated virtual mounts.

    Reference to Theory:
        Supports the workstation model by moving repository-tree inspection into a skill that sits on top of the workstation kernel instead of inside it.

    Example Input Output:
        Input: `_repo_tree_python_script()`
        Output: 'from __future__ import annotations\\n...'

    Args:
        None.

    Returns:
        str: Result produced by `_repo_tree_python_script`.
    """
    return """
from __future__ import annotations

import argparse
import json
import sys

from python_skill_host import broker_request


def _join_relative_path(base: str, name: str) -> str:
    normalized_base = str(base).strip().strip("/")
    normalized_name = str(name).strip().strip("/")
    if not normalized_base:
        return normalized_name
    if not normalized_name:
        return normalized_base
    return f"{normalized_base}/{normalized_name}"


def _walk_tree(mount: str, relative_path: str, *, max_depth: int, max_entries: int) -> list[str]:
    lines: list[str] = []

    def _visit(current_relative_path: str, prefix: str, depth: int) -> None:
        if len(lines) >= max_entries:
            return
        listing = broker_request("fs.list_mount", mount=mount, relative_path=current_relative_path)
        if listing.get("status") != "ok":
            return
        entries = [str(item).strip() for item in listing.get("entries", []) if str(item).strip()]
        for entry in entries:
            if len(lines) >= max_entries:
                return
            child_relative_path = _join_relative_path(current_relative_path, entry)
            try:
                child_listing = broker_request("fs.list_mount", mount=mount, relative_path=child_relative_path)
            except Exception:
                child_listing = {"status": "error"}
            is_directory = child_listing.get("status") == "ok"
            lines.append(f"{prefix}{entry}/" if is_directory else f"{prefix}{entry}")
            if is_directory and depth < max_depth:
                _visit(child_relative_path, prefix + "  ", depth + 1)

    _visit(str(relative_path).strip().strip("/"), "", 1)
    return lines


def main(
    mount: str,
    relative_path: str = "",
    *,
    max_depth: int = 3,
    max_entries: int = 100,
    __dependencies__: tuple[str, ...] = (),
) -> dict[str, object]:
    normalized_mount = str(mount).strip()
    normalized_relative_path = str(relative_path).strip()
    bounded_max_depth = max(1, int(max_depth))
    bounded_max_entries = max(1, int(max_entries))
    if not normalized_mount:
        return {"status": "error", "answer": "No mount was provided.", "result": {"tree": []}}
    tree = _walk_tree(
        normalized_mount,
        normalized_relative_path,
        max_depth=bounded_max_depth,
        max_entries=bounded_max_entries,
    )
    answer = f"Listed {len(tree)} entries from {normalized_mount}."
    return {
        "status": "ok",
        "answer": answer,
        "mount": normalized_mount,
        "relative_path": normalized_relative_path,
        "max_depth": bounded_max_depth,
        "max_entries": bounded_max_entries,
        "entry_count": len(tree),
        "tree": tree,
    }


def run(payload: dict[str, object]) -> dict[str, object]:
    result_value = main(
        mount=str(payload.get("mount", "")),
        relative_path=str(payload.get("relative_path", "")),
        max_depth=int(payload.get("max_depth", 3)),
        max_entries=int(payload.get("max_entries", 100)),
    )
    return {
        "status": "ok" if result_value.get("status") == "ok" else "error",
        "answer": str(result_value.get("answer", "")),
        "result": result_value,
        "notes": [],
    }


def __bssc_cli_main__() -> None:
    parser = argparse.ArgumentParser(description="Workstation Repo Tree")
    parser.add_argument("--input-json", help="Optional JSON payload. Prefer stdin when omitted.")
    args = parser.parse_args()
    raw = args.input_json.encode("utf-8") if args.input_json else sys.stdin.buffer.read()
    payload = json.loads(raw) if raw else {}
    if not isinstance(payload, dict):
        payload = {}
    sys.stdout.write(json.dumps(run(payload), indent=2, sort_keys=True))
    sys.stdout.write("\\n")


if __name__ == "__main__":
    __bssc_cli_main__()
""".strip()


def _wasm_greeting_module_text() -> str:
    """
    High Level Purpose:
        In circumstances like providing one builtin workstation Wasm demo worker, helps with returning a minimal governed Wasm module that proves the workstation can invoke a Wasmtime-backed skill.

    Reference to Theory:
        Supports the workstation shell / worker-runtime model by keeping Wasmtime as one inner worker runtime instead of the workstation shell itself.

    Example Input Output:
        Input: `_wasm_greeting_module_text()`
        Output: '(module ...)'

    Args:
        None.

    Returns:
        str: Result produced by `_wasm_greeting_module_text`.
    """
    payload = {
        "status": "ok",
        "answer": "hello from workstation wasm",
        "result": {"greeting": "hello from workstation wasm"},
        "notes": ["executed through workstation wasm demo skill"],
    }
    payload_text = json.dumps(payload, separators=(",", ":"))
    return (
        "(module\n"
        '  (import "bssc" "input_len" (func $input_len (result i32)))\n'
        '  (import "bssc" "read_input" (func $read_input (param i32) (result i32)))\n'
        '  (import "bssc" "write_output" (func $write_output (param i32 i32) (result i32)))\n'
        '  (memory (export "memory") 1)\n'
        f'  (data (i32.const 1024) "{_wat_bytes(payload_text)}")\n'
        '  (func (export "run") (result i32)\n'
        "    call $input_len\n"
        "    drop\n"
        "    i32.const 0\n"
        "    call $read_input\n"
        "    drop\n"
        "    i32.const 1024\n"
        f"    i32.const {len(payload_text.encode('utf-8'))}\n"
        "    call $write_output\n"
        "    drop\n"
        "    i32.const 0))"
    )


def builtin_workstation_skill_documents() -> tuple[dict[str, Any], ...]:
    """
    High Level Purpose:
        In circumstances like workstation launch and skill discovery, helps with defining the builtin workstation worker skills that the shell can always expose alongside attached stores.

    Reference to Theory:
        Supports the workstation architecture by keeping higher-level behaviors as pluggable workers instead of growing the workstation kernel capability set.

    Example Input Output:
        Input: `builtin_workstation_skill_documents()`
        Output: ({'schema': 'bssc_skill.v1', 'kind': 'ability', 'title': 'Workstation Repo Search', ...},)

    Args:
        None.

    Returns:
        tuple[dict[str, Any], ...]: Result produced by `builtin_workstation_skill_documents`.
    """
    return (
        {
            "schema": "bssc_skill.v1",
            "kind": "ability",
            "title": "Workstation Repo Tree",
            "executor": "python3",
            "entrypoint": "main",
            "inputs": {
                "mount": "governed workstation attachment mount name",
                "relative_path": "optional relative directory inside the mount",
                "max_depth": "maximum traversal depth",
                "max_entries": "maximum lines to return",
            },
            "outputs": {
                "tree": "bounded directory-tree lines",
                "entry_count": "number of entries returned",
            },
            "governed_host_brokers": ["fs.list_mount"],
            "python": _repo_tree_python_script(),
        },
        {
            "schema": "bssc_skill.v1",
            "kind": "ability",
            "title": "Workstation Repo Search",
            "executor": "python3",
            "entrypoint": "main",
            "inputs": {
                "mount": "governed workstation attachment mount name",
                "pattern": "regular expression or literal text to search for",
                "relative_path": "optional relative directory inside the mount",
                "glob": "optional fnmatch-style relative path filter",
                "max_matches": "maximum match lines to return",
            },
            "outputs": {
                "matches": "matched lines with file and line number",
                "match_count": "number of matches returned",
            },
            "governed_host_brokers": ["fs.find_mount", "fs.read_mount"],
            "python": _repo_search_python_script(),
        },
        {
            "schema": "bssc_skill.v1",
            "kind": "ability",
            "title": "Workstation Greeting From Wasm",
            "executor": "wasm_wasi",
            "entrypoint": "run",
            "outputs": {
                "greeting": "greeting text",
            },
            "wasm_abi_version": "bssc.wasm.v1",
            "wasm_format": "wat",
            "wasm": _wasm_greeting_module_text(),
        },
    )


@lru_cache(maxsize=4)
def builtin_workstation_skill_artifacts(
    artifact_factory: Callable[[Any], Artifact],
) -> tuple[Artifact, ...]:
    """
    High Level Purpose:
        In circumstances like workstation skill discovery and invocation, helps with hydrating the builtin workstation skill documents into reusable in-memory artifact records.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by letting builtin workers use the same governed artifact interface as store-backed skills.

    Example Input Output:
        Input: `builtin_workstation_skill_artifacts(artifact_factory)`
        Output: (Artifact(id='artifact-skill-...', title='Workstation Repo Search', artifact_type='ability', representation='python_script'),)

    Args:
        artifact_factory: Entry-composed translator from a portable skill document to an artifact.

    Returns:
        tuple[Artifact, ...]: Result produced by `builtin_workstation_skill_artifacts`.
    """
    return tuple(
        artifact_factory(document)
        for document in builtin_workstation_skill_documents()
    )


def resolve_builtin_workstation_skill(
    title: str,
    artifact_factory: Callable[[Any], Artifact],
) -> Artifact | None:
    """
    High Level Purpose:
        In circumstances like workstation skill invocation, helps with resolving one builtin workstation worker by immutable title.

    Reference to Theory:
        Supports the pluggable-worker model by making builtin workers discoverable and invokable through the same skill title surface as store-backed skills.

    Example Input Output:
        Input: `resolve_builtin_workstation_skill(title='Workstation Repo Search', artifact_factory=artifact_factory)`
        Output: Artifact(id='artifact-skill-...', title='Workstation Repo Search', artifact_type='ability', representation='python_script')

    Args:
        title: Value for `title` used by `resolve_builtin_workstation_skill`. Expected type: `str`.
        artifact_factory: Entry-composed translator from a portable skill document to an artifact.

    Returns:
        Artifact | None: Result produced by `resolve_builtin_workstation_skill`.
    """
    normalized_title = str(title).strip()
    for artifact in builtin_workstation_skill_artifacts(artifact_factory):
        if str(getattr(artifact, "title", "")).strip() == normalized_title:
            return artifact
    return None
