# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_START_RE = re.compile(r"^\s*```([A-Za-z0-9_+\-#.]*)\s*$")
FUNCTION_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:->\s*([^:]+))?:\s*$")
IMPORT_RE = re.compile(r"^\s*(?:from\s+([A-Za-z0-9_.]+)\s+import|import\s+([A-Za-z0-9_., ]+))")
SHELL_PARAMETER_RE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")
ANSIBLE_PARAMETER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


@dataclass
class FenceRecord:
    source_path: str
    fence_index: int
    language: str
    heading_path: list[str] = field(default_factory=list)
    intro_context: list[str] = field(default_factory=list)
    preceding_paragraphs: list[str] = field(default_factory=list)
    code: str = ""


@dataclass
class FenceStrategy:
    source_path: str
    fence_index: int
    language: str
    heading_path: list[str]
    strategy_name: str
    recommended_artifact_type: str
    recommended_representation: str
    executable: bool
    entrypoint_name: str
    parameter_names: list[str] = field(default_factory=list)
    dependency_metadata_kind: str = "unknown"
    inline_imports: list[str] = field(default_factory=list)
    detected_calls: list[str] = field(default_factory=list)
    return_signals: list[str] = field(default_factory=list)
    semantic_lines: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def collapse_ws(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like converting fenced markdown snippets into language-aware extraction plans, helps with normalizing whitespace before semantic comparison and reporting.

    Reference to Theory:
        Supports the markdown-to-semantic-unit path by making fenced snippet context stable enough to compare and reuse across headings and future decomposition passes.

    Example Input Output:
        Input: `collapse_ws(text='open   -a   \"Google Chrome\"   \"https://example.com\"')`
        Output: 'open -a "Google Chrome" "https://example.com"'

    Args:
        text: Value for `text` used by `collapse_ws`. Expected type: `str`.

    Returns:
        str: Result produced by `collapse_ws`.
    """
    return re.sub(r"\s+", " ", str(text or "")).strip()


def ordered_unique(values: list[str]) -> list[str]:
    """
    High Level Purpose:
        In circumstances like collecting imports, detected calls, and semantic hints from one fenced snippet, helps with preserving first-seen order while removing duplicates.

    Reference to Theory:
        Supports stable semantic identity formation by keeping extracted support signals reusable without repetition noise.

    Example Input Output:
        Input: `ordered_unique(values=['subprocess', 'urllib.parse', 'subprocess'])`
        Output: ['subprocess', 'urllib.parse']

    Args:
        values: Value for `values` used by `ordered_unique`. Expected type: `list[str]`.

    Returns:
        list[str]: Result produced by `ordered_unique`.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _strip_inline_comment(text: str) -> str:
    """
    High Level Purpose:
        In circumstances like parsing Python function signatures and shell commands from fenced snippets, helps with removing trailing inline comments that would corrupt lightweight extraction.

    Reference to Theory:
        Supports reusable semantic extraction from source-local wording by stripping incidental residue before identifying stable executable structure.

    Example Input Output:
        Input: `_strip_inline_comment(text='browser: str = \"Safari\",  # default browser')`
        Output: 'browser: str = "Safari",'

    Args:
        text: Value for `text` used by `_strip_inline_comment`. Expected type: `str`.

    Returns:
        str: Result produced by `_strip_inline_comment`.
    """
    return str(text or "").split("#", 1)[0].rstrip()


def _split_top_level_csv(text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like reading parameter lists from fenced Python signatures, helps with splitting comma-separated fields without breaking nested type or default syntax.

    Reference to Theory:
        Supports semantic extraction by preserving the meaningful executable boundary of each parameter rather than naively following surface punctuation.

    Example Input Output:
        Input: `_split_top_level_csv(text='url: str, *, browser: str = \"Safari\", __dependencies__: tuple[str, ...] = ()')`
        Output: ['url: str', '*', 'browser: str = "Safari"', '__dependencies__: tuple[str, ...] = ()']

    Args:
        text: Value for `text` used by `_split_top_level_csv`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_split_top_level_csv`.
    """
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for char in str(text or ""):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _parameter_names_from_signature(signature_text: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like recovering reusable call surfaces from fenced Python snippets, helps with extracting the semantic parameter names from a `main(...)` signature.

    Reference to Theory:
        Supports title-depth and decomposition reuse by isolating the minimally stable input symbols that future calls depend on.

    Example Input Output:
        Input: `_parameter_names_from_signature(signature_text='url: str, *, browser: str = \"Safari\", __dependencies__: tuple[str, ...] = ()')`
        Output: ['url', 'browser']

    Args:
        signature_text: Value for `signature_text` used by `_parameter_names_from_signature`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_parameter_names_from_signature`.
    """
    names: list[str] = []
    for part in _split_top_level_csv(signature_text):
        cleaned = _strip_inline_comment(part).strip()
        if not cleaned or cleaned in {"*", "/"}:
            continue
        name = cleaned.split(":", 1)[0].split("=", 1)[0].strip()
        if name.startswith("**") or name.startswith("*"):
            name = name.lstrip("*").strip()
        if not name or name == "__dependencies__":
            continue
        names.append(name)
    return ordered_unique(names)


def _extract_imports_from_python(code: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like understanding fenced Python execution templates, helps with identifying import dependencies that appear directly in the code body.

    Reference to Theory:
        Supports stable executable identity by separating presupposed substrate imports from later operational details.

    Example Input Output:
        Input: `_extract_imports_from_python(code='def main(x: int):\\n    import subprocess\\n    import urllib.parse')`
        Output: ['subprocess', 'urllib.parse']

    Args:
        code: Value for `code` used by `_extract_imports_from_python`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_extract_imports_from_python`.
    """
    imports: list[str] = []
    for raw_line in str(code or "").splitlines():
        match = IMPORT_RE.match(raw_line)
        if not match:
            continue
        from_module = str(match.group(1) or "").strip()
        import_group = str(match.group(2) or "").strip()
        if from_module:
            imports.append(from_module)
            continue
        if import_group:
            for item in import_group.split(","):
                name = str(item or "").strip()
                if name:
                    imports.append(name)
    return ordered_unique(imports)


def _detect_call_lines(code: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like turning fenced code into a reusable ability strategy, helps with surfacing the operational calls that most likely define the executable burden of the snippet.

    Reference to Theory:
        Supports decomposition by distinguishing executable determination from surrounding explanation and scaffolding.

    Example Input Output:
        Input: `_detect_call_lines(code='subprocess.run([\"open\", url], check=True)\\nreturn {\"status\": \"opened\"}')`
        Output: ['subprocess.run(["open", url], check=True)']

    Args:
        code: Value for `code` used by `_detect_call_lines`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_detect_call_lines`.
    """
    lines: list[str] = []
    for raw_line in str(code or "").splitlines():
        text = collapse_ws(raw_line)
        if "(" in text and ")" in text and not text.startswith(("def ", "class ", "if ", "for ", "while ")):
            if any(token in text for token in ("subprocess.", "os.", "Path(", "urllib.", "pbcopy", "screencapture", "open(")):
                lines.append(text)
    return ordered_unique(lines)


def _detect_return_lines(code: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like classifying fenced code as a reusable callable artifact, helps with recording the output-form signals visible in explicit return statements.

    Reference to Theory:
        Supports semantic identity recovery by identifying the achieved output determination of the snippet, not just its surrounding explanation.

    Example Input Output:
        Input: `_detect_return_lines(code='return {\"status\": \"opened\", \"url\": url}')`
        Output: ['return {"status": "opened", "url": url}']

    Args:
        code: Value for `code` used by `_detect_return_lines`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_detect_return_lines`.
    """
    returns = [collapse_ws(line) for line in str(code or "").splitlines() if collapse_ws(line).startswith("return ")]
    return ordered_unique(returns)


def extract_markdown_fences(markdown_text: str, *, source_path: str = "") -> list[FenceRecord]:
    """
    High Level Purpose:
        In circumstances like preparing markdown curricula for executable learning across multiple languages, helps with recovering fenced code blocks together with their heading path and nearby semantic context.

    Reference to Theory:
        Supports markdown decomposition by separating executable fenced material from surrounding discourse while preserving the broad-to-narrow heading path it belongs to.

    Example Input Output:
        Input: `extract_markdown_fences(markdown_text='# Device\\n## Python\\n```python\\ndef main():\\n    import subprocess\\n```', source_path='/tmp/device.md')`
        Output: [FenceRecord(source_path='/tmp/device.md', fence_index=1, language='python', heading_path=['Device', 'Python'], intro_context=[], preceding_paragraphs=[], code='def main():\\n    import subprocess')]

    Args:
        markdown_text: Value for `markdown_text` used by `extract_markdown_fences`. Expected type: `str`.
        source_path: Value for `source_path` used by `extract_markdown_fences`. Expected type: `str`. Defaults to `''`.

    Returns:
        list[FenceRecord]: Result produced by `extract_markdown_fences`.
    """
    heading_stack: list[str] = []
    intro_context: list[str] = []
    section_paragraphs: list[str] = []
    in_fence = False
    fence_language = ""
    fence_lines: list[str] = []
    fence_index = 0
    records: list[FenceRecord] = []

    for raw_line in str(markdown_text or "").splitlines():
        fence_match = FENCE_START_RE.match(raw_line)
        if fence_match:
            if in_fence:
                fence_index += 1
                records.append(
                    FenceRecord(
                        source_path=source_path,
                        fence_index=fence_index,
                        language=fence_language,
                        heading_path=list(heading_stack),
                        intro_context=list(intro_context[-3:]),
                        preceding_paragraphs=list(section_paragraphs[-3:]),
                        code="\n".join(fence_lines).strip(),
                    )
                )
                in_fence = False
                fence_language = ""
                fence_lines = []
            else:
                in_fence = True
                fence_language = str(fence_match.group(1) or "").strip().lower() or "plain"
                fence_lines = []
            continue

        if in_fence:
            fence_lines.append(raw_line.rstrip("\n"))
            continue

        heading_match = HEADING_RE.match(raw_line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = collapse_ws(heading_match.group(2))
            while len(heading_stack) >= level:
                heading_stack.pop()
            heading_stack.append(heading_text)
            section_paragraphs = []
            if level == 1 and not intro_context:
                intro_context.append(heading_text)
            continue

        stripped = collapse_ws(raw_line)
        if not stripped:
            continue
        if heading_stack:
            section_paragraphs.append(stripped)
        else:
            intro_context.append(stripped)

    return records


def _python_fence_strategy(record: FenceRecord) -> FenceStrategy:
    """
    High Level Purpose:
        In circumstances like turning a fenced Python snippet into a reusable learning strategy, helps with identifying entrypoint, imports, dependency metadata, and executable-semantic rewrite lines.

    Reference to Theory:
        Supports semantic decomposition by extracting the executable unit from its surrounding markdown context while preserving the heading-grounded identity path.

    Example Input Output:
        Input: `_python_fence_strategy(record=FenceRecord(source_path='/tmp/device.md', fence_index=1, language='python', heading_path=['Device', 'Python'], code='def main(url: str, *, __dependencies__: tuple[str, ...] = ()) -> dict[str, str]:\\n    import subprocess\\n    subprocess.run([\"open\", url], check=True)\\n    return {\"status\": \"opened\", \"url\": url}'))`
        Output: FenceStrategy(source_path='/tmp/device.md', fence_index=1, language='python', heading_path=['Device', 'Python'], strategy_name='python_main_entrypoint', recommended_artifact_type='ability', recommended_representation='python_script', executable=True, entrypoint_name='main', parameter_names=['url'], dependency_metadata_kind='signature_inline', inline_imports=['subprocess'], detected_calls=['subprocess.run(["open", url], check=True)'], return_signals=['return {"status": "opened", "url": url}'], semantic_lines=['function name is `main`', 'named inputs: `url`', 'imports inside `main`: `subprocess`', 'execute `subprocess.run(["open", url], check=True)`', 'return `return {"status": "opened", "url": url}`'], notes=[])

    Args:
        record: Value for `record` used by `_python_fence_strategy`. Expected type: `FenceRecord`.

    Returns:
        FenceStrategy: Result produced by `_python_fence_strategy`.
    """
    code = str(record.code or "")
    functions: list[tuple[str, str, str]] = []
    try:
        module = ast.parse(code)
    except Exception:
        module = None
    if module is not None:
        for node in module.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            signature_parts: list[str] = []
            for arg in node.args.args:
                if arg.arg == "self":
                    continue
                signature_parts.append(arg.arg)
            if node.args.vararg is not None:
                signature_parts.append(f"*{node.args.vararg.arg}")
            if node.args.kwonlyargs:
                signature_parts.append("*")
                for arg in node.args.kwonlyargs:
                    signature_parts.append(arg.arg)
            if node.args.kwarg is not None:
                signature_parts.append(f"**{node.args.kwarg.arg}")
            functions.append((str(node.name), ", ".join(signature_parts), ""))
    if not functions:
        functions = [match.groups() for match in FUNCTION_DEF_RE.finditer(code)]
    entrypoint_name = ""
    parameter_names: list[str] = []
    notes: list[str] = []
    for name, signature_text, _return_type in functions:
        if name == "main":
            entrypoint_name = "main"
            parameter_names = _parameter_names_from_signature(signature_text)
            break
    if not entrypoint_name and functions:
        entrypoint_name = str(functions[0][0])
        parameter_names = _parameter_names_from_signature(str(functions[0][1]))
        notes.append("No explicit `main` entrypoint found; first function used as the provisional executable head.")

    imports = _extract_imports_from_python(code)
    calls = _detect_call_lines(code)
    returns = _detect_return_lines(code)

    dependency_metadata_kind = "none"
    if "__dependencies__" in code:
        dependency_metadata_kind = "signature_inline"
    elif "# dependencies =" in code or "# /// script" in code:
        dependency_metadata_kind = "pep723_header"

    semantic_lines: list[str] = []
    if entrypoint_name:
        semantic_lines.append(f"function name is `{entrypoint_name}`")
    if parameter_names:
        semantic_lines.append("named inputs: " + ", ".join(f"`{name}`" for name in parameter_names))
    if imports:
        semantic_lines.append("imports inside `main`: " + ", ".join(f"`{name}`" for name in imports))
    for call in calls[:3]:
        semantic_lines.append(f"execute `{call}`")
    for ret in returns[:2]:
        semantic_lines.append(f"return `{ret}`")

    executable = bool(entrypoint_name and calls)
    return FenceStrategy(
        source_path=record.source_path,
        fence_index=record.fence_index,
        language=record.language,
        heading_path=list(record.heading_path),
        strategy_name="python_main_entrypoint" if entrypoint_name == "main" else "python_callable_snippet",
        recommended_artifact_type="ability" if executable else "candidate",
        recommended_representation="python_script",
        executable=executable,
        entrypoint_name=entrypoint_name,
        parameter_names=parameter_names,
        dependency_metadata_kind=dependency_metadata_kind,
        inline_imports=imports,
        detected_calls=calls,
        return_signals=returns,
        semantic_lines=semantic_lines,
        notes=notes,
    )


def _shell_fence_strategy(record: FenceRecord) -> FenceStrategy:
    """
    High Level Purpose:
        In circumstances like extracting shell or terminal fenced snippets for future multi-language learning, helps with classifying command-oriented blocks as executable shell strategies.

    Reference to Theory:
        Supports semantic decomposition by preserving the command substrate as a reusable executable unit rather than flattening it into adjacent prose.

    Example Input Output:
        Input: `_shell_fence_strategy(record=FenceRecord(source_path='/tmp/device.md', fence_index=1, language='bash', heading_path=['Device', 'Command'], code='open -a \"Google Chrome\" \"https://example.com\"'))`
        Output: FenceStrategy(source_path='/tmp/device.md', fence_index=1, language='bash', heading_path=['Device', 'Command'], strategy_name='shell_command_block', recommended_artifact_type='ability', recommended_representation='shell_script', executable=True, entrypoint_name='main', parameter_names=[], dependency_metadata_kind='none', inline_imports=[], detected_calls=['open -a \"Google Chrome\" \"https://example.com\"'], return_signals=[], semantic_lines=['shell command block', 'execute `open -a \"Google Chrome\" \"https://example.com\"`'], notes=[])

    Args:
        record: Value for `record` used by `_shell_fence_strategy`. Expected type: `FenceRecord`.

    Returns:
        FenceStrategy: Result produced by `_shell_fence_strategy`.
    """
    commands = [collapse_ws(line) for line in str(record.code or "").splitlines() if collapse_ws(line)]
    parameter_names = ordered_unique(
        name
        for name in SHELL_PARAMETER_RE.findall(str(record.code or ""))
        if name not in {"PATH", "HOME", "PWD", "SHELL"}
    )
    semantic_lines = ["shell command block"]
    for command in commands[:3]:
        semantic_lines.append(f"execute `{command}`")
    if parameter_names:
        semantic_lines.append("named shell parameters: " + ", ".join(f"`{name}`" for name in parameter_names))
    return FenceStrategy(
        source_path=record.source_path,
        fence_index=record.fence_index,
        language=record.language,
        heading_path=list(record.heading_path),
        strategy_name="shell_command_block",
        recommended_artifact_type="ability" if bool(commands) else "candidate",
        recommended_representation="shell_script",
        executable=bool(commands),
        entrypoint_name="main" if commands else "",
        parameter_names=parameter_names,
        dependency_metadata_kind="none",
        inline_imports=[],
        detected_calls=commands,
        return_signals=[],
        semantic_lines=semantic_lines,
        notes=[],
    )


def _ansible_fence_strategy(record: FenceRecord) -> FenceStrategy:
    """
    High Level Purpose:
        In circumstances like extracting infrastructure-automation playbooks from fenced markdown, helps with recognizing Ansible-shaped YAML as a reusable executable strategy instead of generic prose.

    Reference to Theory:
        Supports decomposition by preserving automation substrates as distinct executable families that can later be matched and reused structurally.

    Example Input Output:
        Input: `_ansible_fence_strategy(record=FenceRecord(source_path='/tmp/ops.md', fence_index=1, language='ansible', heading_path=['Ops'], code='- hosts: localhost\\n  tasks:\\n    - debug:\\n        msg: \"{{ name }}\"'))`
        Output: FenceStrategy(source_path='/tmp/ops.md', fence_index=1, language='ansible', heading_path=['Ops'], strategy_name='ansible_playbook', recommended_artifact_type='ability', recommended_representation='ansible_playbook', executable=True, entrypoint_name='playbook', parameter_names=['name'], dependency_metadata_kind='none', inline_imports=[], detected_calls=['ansible-playbook'], return_signals=[], semantic_lines=['ansible playbook block', 'named playbook parameters: `name`'], notes=[])

    Args:
        record: Value for `record` used by `_ansible_fence_strategy`. Expected type: `FenceRecord`.

    Returns:
        FenceStrategy: Result produced by `_ansible_fence_strategy`.
    """
    code = str(record.code or "")
    lowered = code.lower()
    executable = "hosts:" in lowered and "tasks:" in lowered
    parameter_names = ordered_unique(ANSIBLE_PARAMETER_RE.findall(code))
    semantic_lines = ["ansible playbook block"]
    if parameter_names:
        semantic_lines.append("named playbook parameters: " + ", ".join(f"`{name}`" for name in parameter_names))
    return FenceStrategy(
        source_path=record.source_path,
        fence_index=record.fence_index,
        language=record.language,
        heading_path=list(record.heading_path),
        strategy_name="ansible_playbook",
        recommended_artifact_type="ability" if executable else "candidate",
        recommended_representation="ansible_playbook",
        executable=executable,
        entrypoint_name="playbook" if executable else "",
        parameter_names=parameter_names,
        dependency_metadata_kind="none",
        inline_imports=[],
        detected_calls=["ansible-playbook"] if executable else [],
        return_signals=[],
        semantic_lines=semantic_lines,
        notes=[] if executable else ["Fence looked like YAML but not a clear Ansible playbook."],
    )


def _generic_fence_strategy(record: FenceRecord) -> FenceStrategy:
    """
    High Level Purpose:
        In circumstances like encountering fenced snippets in future languages without a specialized extractor yet, helps with preserving them as a generic extraction candidate instead of dropping them.

    Reference to Theory:
        Supports semantic preservation by keeping fenced executable or declarative material available for later deeper determination rather than treating it as accidental formatting.

    Example Input Output:
        Input: `_generic_fence_strategy(record=FenceRecord(source_path='/tmp/device.md', fence_index=1, language='applescript', heading_path=['Device'], code='tell application \"Finder\" to activate'))`
        Output: FenceStrategy(source_path='/tmp/device.md', fence_index=1, language='applescript', heading_path=['Device'], strategy_name='generic_fenced_snippet', recommended_artifact_type='candidate', recommended_representation='text', executable=False, entrypoint_name='', parameter_names=[], dependency_metadata_kind='unknown', inline_imports=[], detected_calls=[], return_signals=[], semantic_lines=['language fence: `applescript`', 'preserve the fenced body for a future language-specific extractor'], notes=['No specialized extraction strategy is registered for this language yet.'])

    Args:
        record: Value for `record` used by `_generic_fence_strategy`. Expected type: `FenceRecord`.

    Returns:
        FenceStrategy: Result produced by `_generic_fence_strategy`.
    """
    return FenceStrategy(
        source_path=record.source_path,
        fence_index=record.fence_index,
        language=record.language,
        heading_path=list(record.heading_path),
        strategy_name="generic_fenced_snippet",
        recommended_artifact_type="candidate",
        recommended_representation="text",
        executable=False,
        entrypoint_name="",
        parameter_names=[],
        dependency_metadata_kind="unknown",
        inline_imports=[],
        detected_calls=[],
        return_signals=[],
        semantic_lines=[
            f"language fence: `{record.language}`",
            "preserve the fenced body for a future language-specific extractor",
        ],
        notes=["No specialized extraction strategy is registered for this language yet."],
    )


def fence_strategy_for_record(record: FenceRecord) -> FenceStrategy:
    """
    High Level Purpose:
        In circumstances like preparing a mixed-language markdown corpus for executable extraction, helps with dispatching each fenced snippet to the right language-aware strategy.

    Reference to Theory:
        Supports decomposition by separating substrate language handling from the narrower executable determination rules for each fenced snippet.

    Example Input Output:
        Input: `fence_strategy_for_record(record=FenceRecord(source_path='/tmp/device.md', fence_index=1, language='python', heading_path=['Device'], code='def main():\\n    import subprocess'))`
        Output: FenceStrategy(source_path='/tmp/device.md', fence_index=1, language='python', heading_path=['Device'], strategy_name='python_main_entrypoint', recommended_artifact_type='candidate', recommended_representation='python_script', executable=False, entrypoint_name='main', parameter_names=[], dependency_metadata_kind='none', inline_imports=['subprocess'], detected_calls=[], return_signals=[], semantic_lines=['function name is `main`', 'imports inside `main`: `subprocess`'], notes=[])

    Args:
        record: Value for `record` used by `fence_strategy_for_record`. Expected type: `FenceRecord`.

    Returns:
        FenceStrategy: Result produced by `fence_strategy_for_record`.
    """
    language = str(record.language or "").lower()
    if language in {"python", "py"}:
        return _python_fence_strategy(record)
    if language in {"bash", "sh", "zsh", "shell"}:
        return _shell_fence_strategy(record)
    if language in {"ansible", "ansible-playbook"}:
        return _ansible_fence_strategy(record)
    if language in {"yaml", "yml"} and ("hosts:" in str(record.code or "").lower() and "tasks:" in str(record.code or "").lower()):
        return _ansible_fence_strategy(record)
    return _generic_fence_strategy(record)


def build_fence_strategy_report(source_paths: list[str]) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like auditing markdown teaching corpora for future executable learning across multiple languages, helps with producing one structured report of all fenced snippets and their recommended extraction strategy.

    Reference to Theory:
        Supports semantic reuse by making fenced executable material explicit and queryable rather than leaving it hidden behind formatting that the current learner may ignore.

    Example Input Output:
        Input: `build_fence_strategy_report(source_paths=['/tmp/device.md'])`
        Output: {'document_count': 1, 'fence_count': 1, 'documents': [{'source_path': '/tmp/device.md', 'fence_count': 1, 'strategies': [{'strategy_name': 'python_main_entrypoint'}]}]}

    Args:
        source_paths: Value for `source_paths` used by `build_fence_strategy_report`. Expected type: `list[str]`.

    Returns:
        dict[str, Any]: Result produced by `build_fence_strategy_report`.
    """
    documents: list[dict[str, Any]] = []
    total_fences = 0
    executable_fences = 0
    for source_path in source_paths:
        path = Path(source_path)
        text = path.read_text(encoding="utf-8")
        records = extract_markdown_fences(text, source_path=str(path))
        strategies = [fence_strategy_for_record(record) for record in records]
        total_fences += len(strategies)
        executable_fences += sum(1 for strategy in strategies if strategy.executable)
        documents.append(
            {
                "source_path": str(path),
                "fence_count": len(strategies),
                "strategies": [asdict(strategy) for strategy in strategies],
            }
        )
    return {
        "document_count": len(source_paths),
        "fence_count": total_fences,
        "executable_fence_count": executable_fences,
        "documents": documents,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    High Level Purpose:
        In circumstances like running a standalone fence-extraction audit from the command line, helps with collecting source markdown paths and optional report output parameters.

    Reference to Theory:
        Supports reproducible semantic inspection by making the fence-extraction strategy executable as a bounded external tool.

    Example Input Output:
        Input: `parse_args(argv=['trials/deviceuser/01_LEARN_DEVICEUSER_CAPABILITIES_BROWSER_URL.md', '--report-out', '/tmp/fences.json'])`
        Output: Namespace(markdown_files=['trials/deviceuser/01_LEARN_DEVICEUSER_CAPABILITIES_BROWSER_URL.md'], report_out='/tmp/fences.json')

    Args:
        argv: Value for `argv` used by `parse_args`. Expected type: `list[str] | None`. Defaults to `None`.

    Returns:
        argparse.Namespace: Result produced by `parse_args`.
    """
    parser = argparse.ArgumentParser(description="Extract fenced-code learning strategies from markdown files.")
    parser.add_argument("markdown_files", nargs="+", help="Markdown files to inspect.")
    parser.add_argument("--report-out", help="Optional path to write the JSON report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    High Level Purpose:
        In circumstances like auditing fenced executable examples in markdown curricula, helps with producing a JSON strategy report that can guide future multi-language ingestion work.

    Reference to Theory:
        Supports semantic decomposition and reuse by making fenced executable material visible as structured strategy records before deeper controller integration.

    Example Input Output:
        Input: `main(argv=['/tmp/device.md', '--report-out', '/tmp/fences.json'])`
        Output: 0

    Args:
        argv: Value for `argv` used by `main`. Expected type: `list[str] | None`. Defaults to `None`.

    Returns:
        int: Result produced by `main`.
    """
    args = parse_args(argv)
    report = build_fence_strategy_report([str(Path(item)) for item in args.markdown_files])
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.report_out:
        Path(args.report_out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
