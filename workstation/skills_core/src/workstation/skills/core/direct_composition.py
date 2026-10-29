# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from realized_core_semantics.semantic_text import collapse_ws
from workstation.foundation.models import WorkstationSession
from workstation.contracts.shell_prompt_routing import match_workstation_shell_utility_prompt
from workstation.skills.core.skill_management import workstation_prompt_skill_shortlist_payload


_DIRECT_COMPOSITION_SCORE_THRESHOLD = 8


def _clean_path_candidate(value: str) -> str:
    cleaned = collapse_ws(str(value))
    return cleaned.rstrip(".,;:!?")


def _ordered_unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = collapse_ws(str(value))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def _mount_candidates_from_prompt(prompt: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like workstation direct composition for mount-oriented workers, helps with recovering mount names from ordinary prompt phrasing so mount-scoped worker inputs can be filled without a full controller loop.

    Reference to Theory:
        Supports direct skill composition by binding obvious mount references from the task surface into explicit worker arguments before broader tool planning.

    Example Input Output:
        Input: `_mount_candidates_from_prompt('Copy `foo.txt` from mount `skill_input` to mount `skill_tmp`.')`
        Output: ['skill_input', 'skill_tmp']

    Args:
        prompt: Value for `prompt` used by `_mount_candidates_from_prompt`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_mount_candidates_from_prompt`.
    """
    return _ordered_unique_strings(
        [
            collapse_ws(str(item))
            for item in re.findall(r"\bmount\s+`?([A-Za-z_][A-Za-z0-9_\-]*)`?", str(prompt), flags=re.IGNORECASE)
        ]
    )


def _number_candidates_from_prompt(prompt: str) -> list[str]:
    """
    High Level Purpose:
        In circumstances like direct workstation composition for numeric worker inputs, helps with extracting stable numeric literals from one prompt.

    Reference to Theory:
        Supports direct skill composition by preserving prompt-local numeric givens such as page numbers, modes, ports, and polling parameters.

    Example Input Output:
        Input: `_number_candidates_from_prompt('Fetch page `2` with page size `50`.')`
        Output: ['2', '50']

    Args:
        prompt: Value for `prompt` used by `_number_candidates_from_prompt`. Expected type: `str`.

    Returns:
        list[str]: Result produced by `_number_candidates_from_prompt`.
    """
    backtick_numbers = [
        collapse_ws(str(item))
        for item in re.findall(r"`([0-9]+(?:\.[0-9]+)?)`", str(prompt))
    ]
    prompt_without_urls = re.sub(r"https?://[^\s'\"`]+", " ", str(prompt))
    prompt_without_urls_or_paths = re.sub(r"(?<![A-Za-z0-9_])/[^\s'\"`]+", " ", prompt_without_urls)
    bare_numbers = [
        collapse_ws(str(item))
        for item in re.findall(r"\b([0-9]+(?:\.[0-9]+)?)\b", prompt_without_urls_or_paths)
    ]
    return _ordered_unique_strings(backtick_numbers + bare_numbers)


def _browser_name_from_prompt(prompt: str) -> str:
    """
    High Level Purpose:
        In circumstances like browser-oriented workstation workers, helps with recovering the named browser from the prompt when it is stated naturally rather than as a structured argument.

    Reference to Theory:
        Supports direct skill composition by binding obvious user-facing application names into worker inputs before the generic tool loop expands context.

    Example Input Output:
        Input: `_browser_name_from_prompt('Open Google Chrome to `https://example.com`.')`
        Output: 'Google Chrome'

    Args:
        prompt: Value for `prompt` used by `_browser_name_from_prompt`. Expected type: `str`.

    Returns:
        str: Result produced by `_browser_name_from_prompt`.
    """
    normalized_prompt = collapse_ws(str(prompt))
    browser_variants = (
        "Google Chrome",
        "Safari",
        "Firefox",
        "Arc",
        "Brave",
        "Microsoft Edge",
        "Edge",
        "Chrome",
    )
    for variant in browser_variants:
        if re.search(rf"\b{re.escape(variant)}\b", normalized_prompt, flags=re.IGNORECASE):
            return variant
    return ""


def prompt_explicitly_requests_skill(prompt: str) -> bool:
    """
    High Level Purpose:
        In circumstances like workstation chat turns, helps with recognizing when the user explicitly asked to use a skill or skill family rather than merely requesting an outcome.

    Reference to Theory:
        Supports the workstation skill-first policy by letting the shell keep explicit skill requests on the skill path instead of silently substituting generic host tools.

    Example Input Output:
        Input: `prompt_explicitly_requests_skill('Use the symbol search skill to find BSSCController under src.')`
        Output: True

    Args:
        prompt: Value for `prompt` used by `prompt`. Expected type: `str`.

    Returns:
        bool: Result produced by `prompt_explicitly_requests_skill`.
    """
    normalized = collapse_ws(str(prompt))
    if not normalized:
        return False
    return bool(
        re.search(
            r"\b(?:use|invoke|run)\b.+\bskill\b",
            normalized,
            flags=re.IGNORECASE,
        )
    )


def _skill_action_bonus(*, prompt: str, skill_title: str) -> int:
    """
    High Level Purpose:
        In circumstances like workstation direct composition over shortlisted workers, helps with lightly reranking the shortlist using shared action words from the user prompt and the worker title.

    Reference to Theory:
        Supports direct skill composition by preferring the obvious prompt-local worker when retrieval scores are close but the action semantics in the title match the ask.

    Example Input Output:
        Input: `_skill_action_bonus(prompt='Write `hello` to mount `skill_tmp` at `note.txt`.', skill_title='Python Commands 03 — Write Text File')`
        Output: 3

    Args:
        prompt: Value for `prompt` used by `_skill_action_bonus`. Expected type: `str`.
        skill_title: Value for `skill_title` used by `_skill_action_bonus`. Expected type: `str`.

    Returns:
        int: Result produced by `_skill_action_bonus`.
    """
    action_terms = {
        "append",
        "archive",
        "capture",
        "change",
        "checksum",
        "clone",
        "copy",
        "count",
        "create",
        "delete",
        "download",
        "embedding",
        "ensure",
        "export",
        "extract",
        "fetch",
        "find",
        "launch",
        "list",
        "move",
        "open",
        "patch",
        "poll",
        "post",
        "print",
        "put",
        "read",
        "remove",
        "render",
        "reveal",
        "search",
        "select",
        "send",
        "show",
        "take",
        "tree",
        "upload",
        "write",
    }
    prompt_tokens = set(re.findall(r"[a-z0-9_]+", collapse_ws(str(prompt)).casefold()))
    title_tokens = set(re.findall(r"[a-z0-9_]+", collapse_ws(str(skill_title)).casefold()))
    lowered_title = collapse_ws(str(skill_title)).casefold()
    shared_actions = action_terms.intersection(prompt_tokens).intersection(title_tokens)
    bonus = len(shared_actions) * 2
    if "entries" in prompt_tokens and "list" in title_tokens:
        bonus += 1
    if "contents" in prompt_tokens and "list" in title_tokens:
        bonus += 1
    if "clipboard" in prompt_tokens and "clipboard" in title_tokens:
        bonus += 1
    if "finder" in prompt_tokens and "finder" in title_tokens:
        bonus += 1
    if "terminal" in prompt_tokens and "terminal" in title_tokens:
        bonus += 1
    if "directory" in prompt_tokens and "directory" in title_tokens:
        bonus += 2
    if "mode" in prompt_tokens and "mode" in title_tokens:
        bonus += 2
    if "json" in prompt_tokens and "json" in title_tokens:
        bonus += 3
    if (
        "fetch" in prompt_tokens
        and "page" in prompt_tokens
        and ("size" in prompt_tokens or "per" in prompt_tokens)
        and "get paginated json" in lowered_title
    ):
        bonus += 8
    if "csv" in prompt_tokens and "csv" in title_tokens:
        bonus += 3
    if "zip" in prompt_tokens and ("zip" in title_tokens or "archive" in title_tokens):
        bonus += 3
    if "archive" in prompt_tokens and "archive" in title_tokens:
        bonus += 2
    if "template" in prompt_tokens and "template" in title_tokens:
        bonus += 2
    if "download" in prompt_tokens and "url" in title_tokens:
        bonus += 2
    plain_write_literal_match = re.search(r"\bwrite\s+`([^`]+)`", str(prompt), flags=re.IGNORECASE)
    plain_write_literal = collapse_ws(str(plain_write_literal_match.group(1))) if plain_write_literal_match else ""
    writes_plain_text = bool(plain_write_literal) and not plain_write_literal.startswith(("{", "["))
    writes_txt_target = bool(re.search(r"`[^`]+\.txt`", str(prompt), flags=re.IGNORECASE))
    if {"create", "directory"} <= prompt_tokens and "ensure directory exists" in lowered_title:
        bonus += 4
    if "write" in prompt_tokens and writes_plain_text and "write text file" in lowered_title:
        bonus += 5
    if "append" in prompt_tokens and writes_plain_text and "append text file" in lowered_title:
        bonus += 5
    if "write" in prompt_tokens and writes_txt_target and "write text file" in lowered_title:
        bonus += 4
    if {"write", "text"} <= prompt_tokens and "write file content" in lowered_title:
        bonus += 5
    if "line" in prompt_tokens and "present" in prompt_tokens and "ensure line present" in lowered_title:
        bonus += 4
    if "mode" in prompt_tokens and "ensure file mode" in lowered_title:
        bonus += 4
    if "render" in prompt_tokens and "template" in prompt_tokens and "render template to file" in lowered_title:
        bonus += 4
    if "package" in prompt_tokens and ({"install", "installed"} & prompt_tokens) and "ensure package installed" in lowered_title:
        bonus += 4
    if "clone" in prompt_tokens and "clone git repository" in lowered_title:
        bonus += 4
    if "service" in prompt_tokens and "ensure service is started and enabled" in lowered_title:
        bonus += 4
    if "user" in prompt_tokens and "ensure user exists" in lowered_title:
        bonus += 4
    if "move" in prompt_tokens and "move file" in lowered_title:
        bonus += 4
    if "copy" in prompt_tokens and "copy file" in lowered_title:
        bonus += 4
    if ({"delete", "remove"} & prompt_tokens) and (
        "delete file" in lowered_title or "remove file" in lowered_title
    ):
        bonus += 4
    if "write" in prompt_tokens and "json" in prompt_tokens and "write json file" in lowered_title:
        bonus += 5
    if "read" in prompt_tokens and "json" in prompt_tokens and "read json file" in lowered_title:
        bonus += 4
    if "extract" in prompt_tokens and ("extract zip archive" in lowered_title or "extract archive" in lowered_title):
        bonus += 4
    if "download" in prompt_tokens and "download url to file" in lowered_title:
        bonus += 4
    if (
        {"open", "launch"} & prompt_tokens
        and ({"browser", "chrome", "safari", "firefox", "brave", "arc", "edge"} & prompt_tokens or "https" in prompt_tokens or "http" in prompt_tokens or "url" in prompt_tokens)
        and "launch browser at specific url" in lowered_title
    ):
        bonus += 4
    if (
        {"open", "launch"} & prompt_tokens
        and ("app" in prompt_tokens or "application" in prompt_tokens)
        and "launch application by name" in lowered_title
    ):
        bonus += 3
    if "settings" in prompt_tokens and "settings pane" in lowered_title:
        bonus += 3
    if "screenshot" in prompt_tokens and ("screenshot" in title_tokens or "capture" in title_tokens):
        bonus += 3
    if (
        "screenshot" in prompt_tokens
        and "mount" in prompt_tokens
        and ("python" in title_tokens or "function" in title_tokens)
        and ("screenshot" in title_tokens or "capture" in title_tokens)
    ):
        bonus += 4
    return bonus


def _skill_action_penalty(*, prompt: str, skill_title: str) -> int:
    """
    High Level Purpose:
        In circumstances like direct workstation skill selection over short command-style titles, helps with demoting obviously wrong action families when the prompt names one filesystem action but the shortlisted worker title names another.

    Reference to Theory:
        Supports direct skill composition by preventing near-neighbor command workers such as copy vs move from winning solely on lexical overlap when the prompt's primary action is already explicit.

    Example Input Output:
        Input: `_skill_action_penalty(prompt='Move `a` from mount `skill_tmp` to mount `skill_output` at `b`.', skill_title='Python Commands 05 — Copy File')`
        Output: 6

    Args:
        prompt: Value for `prompt` used by `_skill_action_penalty`. Expected type: `str`.
        skill_title: Value for `skill_title` used by `_skill_action_penalty`. Expected type: `str`.

    Returns:
        int: Result produced by `_skill_action_penalty`.
    """
    prompt_tokens = set(re.findall(r"[a-z0-9_]+", collapse_ws(str(prompt)).casefold()))
    lowered_title = collapse_ws(str(skill_title)).casefold()
    primary_action = ""
    for candidate in ("move", "copy", "delete", "remove", "extract", "download", "write", "append", "read", "list"):
        if candidate in prompt_tokens:
            primary_action = candidate
            break
    if not primary_action:
        return 0

    conflicting_pairs = {
        "fetch": (
            "put json body",
            "post json body",
            "patch json body",
            "delete resource",
            "post form urlencoded data",
        ),
        "move": ("copy file",),
        "copy": ("move file",),
        "extract": ("create zip archive", "copy file", "move file"),
        "delete": ("copy file", "move file", "write text file", "append text file"),
        "remove": ("copy file", "move file", "write text file", "append text file"),
        "read": ("write text file", "append text file"),
        "write": ("read text file", "read json file", "read csv file"),
    }
    penalty = (
        6
        if any(
            re.search(rf"\b{re.escape(marker)}\b", lowered_title)
            for marker in conflicting_pairs.get(primary_action, ())
        )
        else 0
    )
    plain_write_literal_match = re.search(r"\bwrite\s+`([^`]+)`", str(prompt), flags=re.IGNORECASE)
    plain_write_literal = collapse_ws(str(plain_write_literal_match.group(1))) if plain_write_literal_match else ""
    writes_plain_text = bool(plain_write_literal) and not plain_write_literal.startswith(("{", "["))
    writes_txt_target = bool(re.search(r"`[^`]+\.txt`", str(prompt), flags=re.IGNORECASE))
    if "write" in prompt_tokens and (writes_plain_text or writes_txt_target):
        if "write json file" in lowered_title or "write csv file" in lowered_title:
            penalty += 6
    return penalty


def _parse_key_value_mapping(candidates: list[str], *, separator: str) -> dict[str, str]:
    """
    High Level Purpose:
        In circumstances like workstation direct composition for API-style workers, helps with turning literal `key=value` or `Key: Value` prompt fragments into one structured mapping payload.

    Reference to Theory:
        Supports direct skill composition by preserving structured request inputs in the form the selected worker actually expects.

    Example Input Output:
        Input: `_parse_key_value_mapping(['q=widgets', 'limit=10'], separator='=')`
        Output: {'q': 'widgets', 'limit': '10'}

    Args:
        candidates: Value for `candidates` used by `_parse_key_value_mapping`. Expected type: `list[str]`.
        separator: Value for `separator` used by `_parse_key_value_mapping`. Expected type: `str`.

    Returns:
        dict[str, str]: Result produced by `_parse_key_value_mapping`.
    """
    parsed: dict[str, str] = {}
    for candidate in candidates:
        if separator not in str(candidate):
            continue
        key, value = str(candidate).split(separator, 1)
        key_text = collapse_ws(str(key))
        value_text = collapse_ws(str(value))
        if not key_text:
            continue
        parsed[key_text] = value_text
    return parsed


def _value_for_worker_name(
    *,
    name: str,
    description: str,
    normalized_prompt: str,
    literal_candidates: list[str],
    value_like_literals: list[str],
    path_candidates: list[str],
    url_candidates: list[str],
    mount_candidates: list[str],
    number_candidates: list[str],
) -> Any | None:
    """
    High Level Purpose:
        In circumstances like direct workstation worker composition, helps with deriving one structured worker input from prompt-local literals and common natural-language patterns.

    Reference to Theory:
        Supports direct skill composition by letting the shell turn obvious task-bound values into explicit invocation payloads before broader planning or tool use.

    Example Input Output:
        Input: `_value_for_worker_name(name='source_mount', description='required input value', normalized_prompt='Copy `a` from mount `skill_input` to mount `skill_tmp`.', literal_candidates=['a', 'skill_input', 'skill_tmp'], value_like_literals=['a', 'skill_input', 'skill_tmp'], path_candidates=['a'], url_candidates=[], mount_candidates=['skill_input', 'skill_tmp'], number_candidates=[])`
        Output: 'skill_input'

    Args:
        name: Value for `name` used by `_value_for_worker_name`. Expected type: `str`.
        description: Value for `description` used by `_value_for_worker_name`. Expected type: `str`.
        normalized_prompt: Value for `normalized_prompt` used by `_value_for_worker_name`. Expected type: `str`.
        literal_candidates: Value for `literal_candidates` used by `_value_for_worker_name`. Expected type: `list[str]`.
        value_like_literals: Value for `value_like_literals` used by `_value_for_worker_name`. Expected type: `list[str]`.
        path_candidates: Value for `path_candidates` used by `_value_for_worker_name`. Expected type: `list[str]`.
        url_candidates: Value for `url_candidates` used by `_value_for_worker_name`. Expected type: `list[str]`.
        mount_candidates: Value for `mount_candidates` used by `_value_for_worker_name`. Expected type: `list[str]`.
        number_candidates: Value for `number_candidates` used by `_value_for_worker_name`. Expected type: `list[str]`.

    Returns:
        Any | None: Result produced by `_value_for_worker_name`.
    """
    relative_path_candidates = [candidate for candidate in path_candidates if not str(candidate).startswith("/")]
    text_like_literals = [
        candidate
        for candidate in value_like_literals
        if candidate not in mount_candidates
        and candidate not in path_candidates
        and candidate not in url_candidates
    ]
    prompt_value_candidates = [
        candidate
        for candidate in value_like_literals
        if candidate not in mount_candidates and candidate not in url_candidates
    ]
    if name in {"mount"}:
        return mount_candidates[0] if mount_candidates else None
    if name in {"source_mount"}:
        contextual_source_mount = re.search(r"\bfrom\s+mount\s+`?([A-Za-z_][A-Za-z0-9_\-]*)`?", normalized_prompt, flags=re.IGNORECASE)
        if contextual_source_mount:
            return collapse_ws(str(contextual_source_mount.group(1)))
        return mount_candidates[0] if mount_candidates else None
    if name in {"destination_mount"}:
        contextual_destination_mount = re.search(r"\b(?:to|into|in)\s+mount\s+`?([A-Za-z_][A-Za-z0-9_\-]*)`?", normalized_prompt, flags=re.IGNORECASE)
        if contextual_destination_mount:
            return collapse_ws(str(contextual_destination_mount.group(1)))
        if len(mount_candidates) >= 2:
            return mount_candidates[-1]
        return mount_candidates[0] if mount_candidates else None
    if name in {"root", "search_root", "directory", "dir"}:
        scoped_root_match = re.search(
            r"\b(?:under|within|in)\s+`?([A-Za-z0-9_./-]+)`?(?:[.!?,;:]|$)",
            normalized_prompt,
            flags=re.IGNORECASE,
        )
        if scoped_root_match:
            scoped_root = _clean_path_candidate(str(scoped_root_match.group(1)))
            if scoped_root.casefold() not in {
                "this",
                "workspace",
                "this workspace",
                "the workspace",
                "repo",
                "repository",
                "the repo",
                "the repository",
            }:
                return scoped_root
        return path_candidates[-1] if path_candidates else None
    if name in {"relative_path"}:
        if relative_path_candidates:
            return relative_path_candidates[-1]
        if path_candidates:
            return path_candidates[-1]
        return prompt_value_candidates[-1] if prompt_value_candidates else None
    if name in {"source_relative_path"}:
        contextual_source_path = re.search(
            r"\bfrom\s+mount\s+`?[A-Za-z_][A-Za-z0-9_\-]*`?\s+at\s+`([^`]+)`",
            normalized_prompt,
            flags=re.IGNORECASE,
        )
        if contextual_source_path:
            return _clean_path_candidate(str(contextual_source_path.group(1)))
        if relative_path_candidates:
            return relative_path_candidates[0]
        if path_candidates:
            return path_candidates[0]
        if re.search(r"\bfrom\s+mount\b", normalized_prompt, flags=re.IGNORECASE):
            return prompt_value_candidates[0] if prompt_value_candidates else None
        return prompt_value_candidates[0] if prompt_value_candidates else None
    if name in {"destination_relative_path"}:
        contextual_destination_path = re.search(
            r"\b(?:to|into|in)\s+mount\s+`?[A-Za-z_][A-Za-z0-9_\-]*`?\s+at\s+`([^`]+)`",
            normalized_prompt,
            flags=re.IGNORECASE,
        )
        if contextual_destination_path:
            return _clean_path_candidate(str(contextual_destination_path.group(1)))
        if relative_path_candidates:
            return relative_path_candidates[-1]
        if path_candidates:
            return path_candidates[-1]
        if re.search(r"\bin\s+mount\b", normalized_prompt, flags=re.IGNORECASE) and re.search(r"\bfrom\s+mount\b", normalized_prompt, flags=re.IGNORECASE):
            return prompt_value_candidates[0] if prompt_value_candidates else None
        return prompt_value_candidates[-1] if prompt_value_candidates else None
    if name in {"source"}:
        return path_candidates[0] if path_candidates else None
    if name == "prefix":
        prefix_match = re.search(r"\bprefix\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
        if prefix_match:
            return collapse_ws(str(prefix_match.group(1)))
        return ""
    if name in {"local_path"}:
        upload_path_match = re.search(r"\bupload\s+`([^`]+)`\s+to\b", normalized_prompt, flags=re.IGNORECASE)
        if upload_path_match:
            return _clean_path_candidate(str(upload_path_match.group(1)))
        return path_candidates[-1] if path_candidates else None
    if name in {"destination", "path"}:
        return path_candidates[-1] if path_candidates else None
    if name in {"archive"}:
        return path_candidates[0] if path_candidates else None
    if name in {"source_dir"}:
        contextual_source_dir = re.search(
            r"\bfrom\s+(?!mount\b)(?:`([^`]+)`|\"([^\"]+)\"|'([^']+)'|([A-Za-z0-9_./-]+))",
            normalized_prompt,
            flags=re.IGNORECASE,
        )
        if contextual_source_dir:
            contextual_value = next(
                (
                    collapse_ws(str(value))
                    for value in contextual_source_dir.groups()
                    if collapse_ws(str(value or ""))
                ),
                "",
            )
            if contextual_value:
                return _clean_path_candidate(contextual_value)
        return path_candidates[-1] if path_candidates else None
    if name == "supabase_url":
        return "https://demo.supabase.local"
    if name == "redis_url":
        return "redis://fake-redis.local:6379/0"
    if name in {"url", "uri", "repo_url", "supabase_url", "redis_url"}:
        return url_candidates[0] if url_candidates else None
    if name in {"browser"}:
        browser = _browser_name_from_prompt(normalized_prompt)
        if browser:
            return browser
        return text_like_literals[0] if text_like_literals else None
    if name in {"symbol", "module", "tag", "package", "name", "query", "pattern", "suffix", "glob", "key"}:
        if name == "name":
            for candidate in path_candidates:
                candidate_text = collapse_ws(str(candidate))
                if candidate_text and not candidate_text.startswith("/"):
                    return candidate_text.rsplit("/", 1)[-1]
        if name == "key":
            explicit_key_match = re.search(r"\bas\s+key\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if explicit_key_match:
                return collapse_ws(str(explicit_key_match.group(1)))
        if name == "query":
            query_pairs = [candidate for candidate in text_like_literals if "=" in candidate and "&" not in candidate]
            if query_pairs:
                query_mapping = _parse_key_value_mapping(query_pairs, separator="=")
                if query_mapping:
                    return query_mapping
        if name == "symbol":
            for pattern in (
                r"\bclass\s+definition\s+for\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"\bfunction\s+definition\s+for\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"\boccurrences?\s+of\s+(?:the\s+)?symbol\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"\bsymbol\s+([A-Za-z_][A-Za-z0-9_]*)",
            ):
                matched = re.search(pattern, normalized_prompt, flags=re.IGNORECASE)
                if matched:
                    return collapse_ws(str(matched.group(1)))
        if value_like_literals:
            candidate = value_like_literals[0]
            if name in {"pattern", "query"}:
                candidate = _normalized_literal_pattern(candidate)
            return candidate
        keyword_pattern = None
        if name == "symbol":
            keyword_pattern = r"\bsymbol\s+([A-Za-z_][A-Za-z0-9_]*)"
        elif name == "module":
            keyword_pattern = r"\bmodule\s+([A-Za-z_][A-Za-z0-9_\.]*)"
        elif name == "tag":
            keyword_pattern = r"\btag\s+([A-Za-z_][A-Za-z0-9_\-]*)"
        elif name == "package":
            keyword_pattern = r"\bpackage\s+([A-Za-z_][A-Za-z0-9_\-\.]*)"
        elif name == "key":
            keyword_pattern = r"\bkeys?\s+named\s+([A-Za-z_][A-Za-z0-9_\-\.]*)"
        elif name == "suffix":
            keyword_pattern = r"\bsuffix\s+(\.[A-Za-z0-9_]+)"
        if keyword_pattern is not None:
            matched = re.search(keyword_pattern, normalized_prompt, flags=re.IGNORECASE)
            if matched:
                return collapse_ws(str(matched.group(1)))
        if name in {"tag", "pattern", "query"} and re.search(r"\bTODO\b", normalized_prompt):
            return "TODO"
        return None
    if name in {"json_text"}:
        for candidate in text_like_literals:
            if candidate.startswith("{") or candidate.startswith("["):
                return candidate
        return text_like_literals[-1] if text_like_literals else None
    if name in {"csv_text", "text", "content", "line", "headers", "form_fields", "prompt"}:
        if name == "text":
            text_match = re.search(r"\btext\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if text_match:
                return collapse_ws(str(text_match.group(1)))
            message_match = re.search(r"\bmessage\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if message_match:
                return collapse_ws(str(message_match.group(1)))
        if name == "prompt":
            prompt_match = re.search(r"\bprompt\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if prompt_match:
                return collapse_ws(str(prompt_match.group(1)))
        if name == "form_fields":
            form_like = [candidate for candidate in text_like_literals if "=" in candidate]
            if form_like:
                form_mapping = _parse_key_value_mapping(form_like, separator="=")
                if form_mapping:
                    return form_mapping
        if name == "headers":
            header_like = [candidate for candidate in text_like_literals if ":" in candidate]
            if header_like:
                header_mapping = _parse_key_value_mapping(header_like, separator=":")
                if header_mapping:
                    return header_mapping
        if name == "prompt" and text_like_literals:
            return text_like_literals[-1]
        return text_like_literals[-1] if text_like_literals else None
    if name in {"model"}:
        model_match = re.search(r"\bmodel\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
        if model_match:
            return collapse_ws(str(model_match.group(1)))
        return text_like_literals[0] if text_like_literals else None
    if name in {
        "package_name",
        "bucket",
        "blob_name",
        "channel",
        "repo_name",
        "namespace",
        "service_name",
        "username",
        "customer_id",
        "table",
        "status_field",
        "target_value",
        "token",
        "api_key",
        "supabase_key",
    }:
        if name == "bucket":
            bucket_match = re.search(r"\bbucket\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if bucket_match:
                return collapse_ws(str(bucket_match.group(1)))
        if name == "blob_name":
            blob_match = re.search(r"\bblob\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if blob_match:
                return collapse_ws(str(blob_match.group(1)))
        if name == "channel":
            channel_match = re.search(r"\bchannel\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if channel_match:
                return collapse_ws(str(channel_match.group(1)))
        if name == "repo_name":
            repo_match = re.search(r"\brepositor(?:y|ies)\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if repo_match:
                return collapse_ws(str(repo_match.group(1)))
        if name == "namespace":
            namespace_match = re.search(r"\bnamespace\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if namespace_match:
                return collapse_ws(str(namespace_match.group(1)))
        if name == "customer_id":
            customer_match = re.search(r"\bcustomer\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if customer_match:
                return collapse_ws(str(customer_match.group(1)))
        if name == "table":
            table_match = re.search(r"\btable\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if table_match:
                return collapse_ws(str(table_match.group(1)))
        if name == "key":
            redis_key_match = re.search(r"\bkey\s+`([^`]+)`", normalized_prompt, flags=re.IGNORECASE)
            if redis_key_match:
                return collapse_ws(str(redis_key_match.group(1)))
        if name == "status_field":
            field_match = re.search(r"\bfield\s+`?([A-Za-z_][A-Za-z0-9_\-]*)`?", normalized_prompt, flags=re.IGNORECASE)
            if field_match:
                return collapse_ws(str(field_match.group(1)))
        if name == "target_value":
            target_match = re.search(r"\b(?:becomes|equals|is)\s+`?([^`]+?)`?(?:[\.\s]|$)", normalized_prompt, flags=re.IGNORECASE)
            if target_match:
                return collapse_ws(str(target_match.group(1))).rstrip(".,;:!?")
            if len(text_like_literals) >= 2:
                return text_like_literals[-1]
        if name == "token":
            if "slack" in normalized_prompt.casefold():
                return "xoxb-fake-slack-token"
            if "github" in normalized_prompt.casefold():
                return "ghp_fake_github_token"
        if name == "api_key":
            if "stripe" in normalized_prompt.casefold():
                return "sk_test_fake"
        if name == "supabase_key":
            return "fake-supabase-key"
        return text_like_literals[0] if text_like_literals else None
    if name in {"mode", "page", "per_page", "port", "max_attempts", "poll_interval_seconds", "max_tokens"}:
        if name == "per_page" and len(number_candidates) >= 2:
            return number_candidates[1]
        if name == "page" and number_candidates:
            return number_candidates[0]
        if name == "max_tokens":
            explicit_max_tokens = re.search(r"\bmax\s+tokens?\s+`?([0-9]+)`?", normalized_prompt, flags=re.IGNORECASE)
            if explicit_max_tokens:
                return collapse_ws(str(explicit_max_tokens.group(1)))
            return "64"
        if name == "poll_interval_seconds":
            return number_candidates[0] if number_candidates else "1"
        if name == "max_attempts":
            return number_candidates[-1] if number_candidates else "10"
        return number_candidates[0] if number_candidates else None
    if "required" in description.casefold():
        return None
    return None


def _derive_payload_execution_input(
    *,
    skill_title: str,
    normalized_prompt: str,
    mount_candidates: list[str],
    path_candidates: list[str],
    relative_path_candidates: list[str],
    url_candidates: list[str],
    text_like_literals: list[str],
    number_candidates: list[str],
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation direct composition for payload-shaped workers, helps with synthesizing one structured execution payload from the prompt and the selected worker title.

    Reference to Theory:
        Supports the workstation shell/worker split by keeping high-level prompt understanding in the shell while still feeding payload-oriented workers explicit structured inputs.

    Example Input Output:
        Input: `_derive_payload_execution_input(skill_title='Device User Capabilities 10 — Capture Screenshot To File', normalized_prompt='Take a screenshot and save it to mount `skill_tmp` at `shot.png`.', mount_candidates=['skill_tmp'], path_candidates=['shot.png'], relative_path_candidates=['shot.png'], url_candidates=[], text_like_literals=[], number_candidates=[])`
        Output: {'mount': 'skill_tmp', 'relative_path': 'shot.png'}

    Args:
        skill_title: Value for `skill_title` used by `_derive_payload_execution_input`. Expected type: `str`.
        normalized_prompt: Value for `normalized_prompt` used by `_derive_payload_execution_input`. Expected type: `str`.
        mount_candidates: Value for `mount_candidates` used by `_derive_payload_execution_input`. Expected type: `list[str]`.
        path_candidates: Value for `path_candidates` used by `_derive_payload_execution_input`. Expected type: `list[str]`.
        relative_path_candidates: Value for `relative_path_candidates` used by `_derive_payload_execution_input`. Expected type: `list[str]`.
        url_candidates: Value for `url_candidates` used by `_derive_payload_execution_input`. Expected type: `list[str]`.
        text_like_literals: Value for `text_like_literals` used by `_derive_payload_execution_input`. Expected type: `list[str]`.
        number_candidates: Value for `number_candidates` used by `_derive_payload_execution_input`. Expected type: `list[str]`.

    Returns:
        dict[str, Any] | None: Result produced by `_derive_payload_execution_input`.
    """
    lowered_title = collapse_ws(str(skill_title)).casefold()
    browser = _browser_name_from_prompt(normalized_prompt)
    if "launch browser at specific url" in lowered_title:
        payload: dict[str, Any] = {}
        if url_candidates:
            payload["url"] = url_candidates[0]
        if browser:
            payload["browser"] = browser
        return payload or None
    if "launch application by name" in lowered_title:
        app_match = re.search(r"\blaunch\s+the\s+`?([^`]+?)`?\s+app\b", normalized_prompt, flags=re.IGNORECASE)
        if app_match:
            return {"app": collapse_ws(str(app_match.group(1)))}
        return {"app": text_like_literals[0]} if text_like_literals else None
    if "open file in chosen app" in lowered_title:
        payload = {}
        if mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[0]
        app_match = re.search(r"\bin\s+([A-Za-z][A-Za-z0-9 ]+)$", normalized_prompt)
        if app_match:
            payload["app"] = collapse_ws(str(app_match.group(1)))
        return payload or None
    if "open folder in finder" in lowered_title or "open terminal at directory" in lowered_title or "reveal file in finder" in lowered_title:
        payload = {}
        if mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[0]
        return payload or None
    if "search the web in browser" in lowered_title:
        payload = {}
        if text_like_literals:
            payload["query"] = text_like_literals[-1]
        payload["browser"] = browser or "Safari"
        return payload or None
    if "open system settings pane" in lowered_title:
        pane_match = re.search(r"\bopen\s+the\s+(.+?)\s+settings pane\b", normalized_prompt, flags=re.IGNORECASE)
        if pane_match:
            return {"pane": collapse_ws(str(pane_match.group(1)))}
        return None
    if "copy text to clipboard" in lowered_title:
        return {"text": text_like_literals[-1]} if text_like_literals else None
    if "capture screenshot to file" in lowered_title:
        payload = {}
        if mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[-1]
        return payload or None
    if "repo tree" in lowered_title or "directory tree" in lowered_title:
        payload = {}
        if mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[-1]
        if number_candidates:
            payload["max_depth"] = int(float(number_candidates[0]))
        if len(number_candidates) >= 2:
            payload["max_entries"] = int(float(number_candidates[1]))
        return payload or None
    if "read text file" in lowered_title or "read json file" in lowered_title or "read csv file" in lowered_title:
        payload = {}
        if mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[-1]
        return payload or None
    if "write text file" in lowered_title or "append text file" in lowered_title:
        payload = {}
        destination_mount_match = re.search(
            r"\b(?:to|into|in)\s+mount\s+`?([A-Za-z_][A-Za-z0-9_\-]*)`?",
            normalized_prompt,
            flags=re.IGNORECASE,
        )
        if destination_mount_match:
            payload["mount"] = collapse_ws(str(destination_mount_match.group(1)))
        elif len(mount_candidates) >= 2:
            payload["mount"] = mount_candidates[-1]
        elif mount_candidates:
            payload["mount"] = mount_candidates[0]
        if relative_path_candidates:
            payload["relative_path"] = relative_path_candidates[-1]
        if text_like_literals:
            payload["text"] = text_like_literals[-1]
        return payload or None
    return None


def _normalized_literal_pattern(value: str) -> str:
    """
    High Level Purpose:
        In circumstances like direct workstation composition for search-oriented workers, helps with converting one user-supplied literal pattern into a regex-safe form when it contains punctuation that would otherwise be misread by `rg`.

    Reference to Theory:
        Supports direct skill composition by preserving literal search intent when the prompt names a concrete string rather than an explicit regular expression.

    Example Input Output:
        Input: `_normalized_literal_pattern('.run(')`
        Output: '\\.run\\('

    Args:
        value: Value for `value` used by `_normalized_literal_pattern`. Expected type: `str`.

    Returns:
        str: Result produced by `_normalized_literal_pattern`.
    """
    normalized = collapse_ws(str(value))
    if not normalized:
        return normalized
    if "\\" in normalized:
        return normalized
    if re.search(r"[^A-Za-z0-9_\-]", normalized):
        return re.escape(normalized)
    return normalized


def _prompt_literal_candidates(prompt: str) -> tuple[list[str], list[str], list[str]]:
    """
    High Level Purpose:
        In circumstances like workstation direct worker composition, helps with extracting stable literal candidates from the raw prompt so common worker inputs can be derived without a full controller loop.

    Reference to Theory:
        Supports direct skill composition by letting the workstation shell bind obvious prompt literals into explicit worker inputs before escalating to heavier planning.

    Example Input Output:
        Input: `_prompt_literal_candidates('Find symbol `BSSCController` under `/tmp/project`.')`
        Output: (['BSSCController', '/tmp/project'], ['/tmp/project'], [])

    Args:
        prompt: Value for `prompt` used by `_prompt_literal_candidates`. Expected type: `str`.

    Returns:
        tuple[list[str], list[str], list[str]]: Result produced by `_prompt_literal_candidates`.
    """
    normalized_prompt = str(prompt or "")
    literal_candidates = _ordered_unique_strings(re.findall(r"`([^`]+)`", normalized_prompt))
    path_candidates = [
        _clean_path_candidate(candidate)
        for candidate in literal_candidates
        if not str(candidate).startswith(("http://", "https://"))
        and (
            candidate.startswith("/")
        or candidate.startswith("./")
        or "/" in candidate
        or re.fullmatch(r"[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+", candidate)
        )
    ]
    quoted_candidates = _ordered_unique_strings(re.findall(r"['\"]([^'\"]+)['\"]", normalized_prompt))
    url_candidates = _ordered_unique_strings(re.findall(r"https?://[^\s'\"`]+", normalized_prompt))
    for candidate in quoted_candidates:
        if (
            not str(candidate).startswith(("http://", "https://"))
            and (
            candidate.startswith("/")
            or candidate.startswith("./")
            or "/" in candidate
            or re.fullmatch(r"[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+", candidate)
            )
        ):
            path_candidates.append(_clean_path_candidate(candidate))
    prompt_without_urls = re.sub(r"https?://[^\s'\"`]+", " ", normalized_prompt)
    path_candidates.extend(
        _clean_path_candidate(candidate)
        for candidate in re.findall(r"(?<![A-Za-z0-9_])(/[^\s'\"`]+)", prompt_without_urls)
    )
    path_candidates.extend(
        _clean_path_candidate(candidate)
        for candidate in re.findall(
            r"(?<![A-Za-z0-9_/])((?:\./)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+)",
            prompt_without_urls,
        )
    )
    return (
        _ordered_unique_strings(literal_candidates + quoted_candidates),
        _ordered_unique_strings(path_candidates),
        url_candidates,
    )


def _derive_workstation_invocation_payload_from_prompt(
    *,
    inputs: Mapping[str, Any],
    prompt: str,
    skill_title: str | None = None,
    allow_partial: bool = False,
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation direct worker composition, helps with deriving one minimal invocation payload from prompt literals for skills whose inputs are obvious from the user ask.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by allowing direct worker composition when the prompt already contains the needed inputs explicitly.

    Example Input Output:
        Input: `derive_workstation_invocation_payload_from_prompt(inputs={'symbol': 'required input value', 'root': 'required input value'}, prompt='Find symbol `BSSCController` under `/tmp/project`.')`
        Output: {'symbol': 'BSSCController', 'root': '/tmp/project'}

    Args:
        inputs: Value for `inputs` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `Mapping[str, Any]`.
        prompt: Value for `prompt` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `str`.
        skill_title: Value for `skill_title` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        dict[str, Any] | None: Result produced by `derive_workstation_invocation_payload_from_prompt`.
    """
    input_items = {
        collapse_ws(str(name)): collapse_ws(str(description))
        for name, description in dict(inputs).items()
        if collapse_ws(str(name))
    }
    if not input_items:
        return {}
    normalized_prompt = collapse_ws(str(prompt))
    literal_candidates, path_candidates, url_candidates = _prompt_literal_candidates(normalized_prompt)
    mount_candidates = _mount_candidates_from_prompt(normalized_prompt)
    number_candidates = _number_candidates_from_prompt(normalized_prompt)
    relative_path_candidates = [candidate for candidate in path_candidates if not str(candidate).startswith("/")]
    value_like_literals = [
        candidate
        for candidate in literal_candidates
        if candidate not in path_candidates and candidate not in url_candidates and candidate not in mount_candidates
    ]
    text_like_literals = [
        candidate
        for candidate in value_like_literals
        if candidate not in number_candidates
    ]
    title_inferred_payload = _derive_payload_execution_input(
        skill_title=str(skill_title or ""),
        normalized_prompt=normalized_prompt,
        mount_candidates=mount_candidates,
        path_candidates=path_candidates,
        relative_path_candidates=relative_path_candidates,
        url_candidates=url_candidates,
        text_like_literals=text_like_literals,
        number_candidates=number_candidates,
    )
    declared_input_names = {collapse_ws(str(name)) for name in input_items}

    def _title_inferred_payload_matches_declared_inputs(payload: Any) -> bool:
        if not isinstance(payload, Mapping):
            return False
        if "payload" in {name.casefold() for name in declared_input_names}:
            return True
        payload_keys = {collapse_ws(str(key)) for key in payload}
        return bool(payload_keys.intersection(declared_input_names))
    derived: dict[str, Any] = {}
    for raw_name, description in input_items.items():
        name = raw_name.casefold()
        required = "required" in description.casefold() or not description
        if name == "payload":
            payload = _derive_payload_execution_input(
                skill_title=str(skill_title or ""),
                normalized_prompt=normalized_prompt,
                mount_candidates=mount_candidates,
                path_candidates=path_candidates,
                relative_path_candidates=relative_path_candidates,
                url_candidates=url_candidates,
                text_like_literals=text_like_literals,
                number_candidates=number_candidates,
            )
            if payload is not None:
                derived[raw_name] = payload
                continue
            if required:
                if allow_partial:
                    continue
                return title_inferred_payload if title_inferred_payload is not None else None
            continue
        value = _value_for_worker_name(
            name=name,
            description=description,
            normalized_prompt=normalized_prompt,
            literal_candidates=literal_candidates,
            value_like_literals=value_like_literals,
            path_candidates=path_candidates,
            url_candidates=url_candidates,
            mount_candidates=mount_candidates,
            number_candidates=number_candidates,
        )
        if value is not None:
            derived[raw_name] = value
            continue
        if required:
            if allow_partial:
                continue
            return (
                title_inferred_payload
                if _title_inferred_payload_matches_declared_inputs(title_inferred_payload)
                else None
            )
    if (
        title_inferred_payload is not None
        and "payload" not in {name.casefold() for name in input_items}
        and _title_inferred_payload_matches_declared_inputs(title_inferred_payload)
    ):
        for key, value in title_inferred_payload.items():
            derived[collapse_ws(str(key))] = value
    if not derived and _title_inferred_payload_matches_declared_inputs(title_inferred_payload):
        return title_inferred_payload
    if not derived:
        if allow_partial:
            return {}
        return None
    return derived


def derive_workstation_invocation_payload_from_prompt(
    *,
    inputs: Mapping[str, Any],
    prompt: str,
    skill_title: str | None = None,
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation direct worker composition, helps with deriving one complete minimal invocation payload from prompt literals for skills whose required inputs are obvious from the user ask.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by allowing direct worker composition when the prompt already contains the needed inputs explicitly.

    Example Input Output:
        Input: `derive_workstation_invocation_payload_from_prompt(inputs={'symbol': 'required input value', 'root': 'required input value'}, prompt='Find symbol `BSSCController` under `/tmp/project`.')`
        Output: {'symbol': 'BSSCController', 'root': '/tmp/project'}

    Args:
        inputs: Value for `inputs` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `Mapping[str, Any]`.
        prompt: Value for `prompt` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `str`.
        skill_title: Value for `skill_title` used by `derive_workstation_invocation_payload_from_prompt`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        dict[str, Any] | None: Result produced by `derive_workstation_invocation_payload_from_prompt`.
    """
    return _derive_workstation_invocation_payload_from_prompt(
        inputs=inputs,
        prompt=prompt,
        skill_title=skill_title,
        allow_partial=False,
    )


def derive_workstation_partial_invocation_payload_from_prompt(
    *,
    inputs: Mapping[str, Any],
    prompt: str,
    skill_title: str | None = None,
) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like multi-step workstation planning, helps with recovering the prompt-local input fields that are obvious even when the full required worker payload is not yet satisfiable without skill-to-skill mapping.

    Reference to Theory:
        Supports bounded automatic composition planning by letting the shell separate prompt-derived root bindings from leaf bindings supplied by earlier skills.

    Example Input Output:
        Input: `derive_workstation_partial_invocation_payload_from_prompt(inputs={'mount': 'required input value', 'relative_path': 'required input value', 'text': 'required input value'}, prompt='Read `src/demo.py` and write it to mount `skill_tmp` at `demo.copy`.')`
        Output: {'mount': 'skill_tmp', 'relative_path': 'demo.copy'}

    Args:
        inputs: Value for `inputs` used by `derive_workstation_partial_invocation_payload_from_prompt`. Expected type: `Mapping[str, Any]`.
        prompt: Value for `prompt` used by `derive_workstation_partial_invocation_payload_from_prompt`. Expected type: `str`.
        skill_title: Value for `skill_title` used by `derive_workstation_partial_invocation_payload_from_prompt`. Expected type: `str | None`. Defaults to `None`.

    Returns:
        dict[str, Any]: Result produced by `derive_workstation_partial_invocation_payload_from_prompt`.
    """
    partial = _derive_workstation_invocation_payload_from_prompt(
        inputs=inputs,
        prompt=prompt,
        skill_title=skill_title,
        allow_partial=True,
    )
    return dict(partial) if isinstance(partial, Mapping) else {}


def preferred_workstation_skill_invocation_plan(
    *,
    session: WorkstationSession,
    prompt: str,
) -> dict[str, Any] | None:
    """
    High Level Purpose:
        In circumstances like workstation prompting against a large imported worker inventory, helps with selecting one direct worker invocation plan when the prompt-local shortlist is strong enough to justify composition before generic tool use.

    Reference to Theory:
        Supports the workstation design choice to prefer direct skill composition before plugging in the full controller or falling back to broad process tools.

    Example Input Output:
        Input: `preferred_workstation_skill_invocation_plan(session=3, prompt='Find every occurrence of the symbol `BSSCController` under `/tmp/project`.')`
        Output: {'skill_title': 'Symbol Search Commands 01 — Find Symbol Occurrences / Symbol Search Commands 01 Find Symbol Occurrences', 'semantic_unit': 'Find every occurrence of the symbol `BSSCController` under `/tmp/project`.', 'invocation_payload': {'symbol': 'BSSCController', 'root': '/tmp/project'}}

    Args:
        session: Value for `session` used by `preferred_workstation_skill_invocation_plan`. Expected type: `WorkstationSession`.
        prompt: Value for `prompt` used by `preferred_workstation_skill_invocation_plan`. Expected type: `str`.

    Returns:
        dict[str, Any] | None: Result produced by `preferred_workstation_skill_invocation_plan`.
    """
    if match_workstation_shell_utility_prompt(prompt) is not None:
        return None
    shortlist = workstation_prompt_skill_shortlist_payload(session=session, prompt=prompt, limit=10)
    skills = list(shortlist.get("skills", []))
    if not skills:
        return None
    scored_skills: list[dict[str, Any]] = []
    for raw_skill in skills:
        if not isinstance(raw_skill, Mapping):
            continue
        item = dict(raw_skill)
        title = collapse_ws(str(item.get("title", "")))
        base_score = int(item.get("score", 0) or 0)
        item["_effective_score"] = (
            base_score
            + _skill_action_bonus(prompt=prompt, skill_title=title)
            - _skill_action_penalty(prompt=prompt, skill_title=title)
        )
        scored_skills.append(item)
    if not scored_skills:
        return None
    scored_skills.sort(key=lambda item: int(item.get("_effective_score", 0) or 0), reverse=True)
    for index, candidate in enumerate(scored_skills):
        skill_title = collapse_ws(str(candidate.get("title", "")))
        if not skill_title:
            continue
        effective_score = int(candidate.get("_effective_score", 0) or 0)
        if skill_title == "Workstation Repo Search":
            if effective_score < _DIRECT_COMPOSITION_SCORE_THRESHOLD:
                continue
            return {
                "skill_title": skill_title,
                "semantic_unit": collapse_ws(str(prompt)),
            }
        if collapse_ws(str(candidate.get("kind", ""))).casefold() == "knowledge":
            if effective_score < _DIRECT_COMPOSITION_SCORE_THRESHOLD:
                continue
            return {
                "skill_title": skill_title,
                "semantic_unit": collapse_ws(str(prompt)),
            }
        inputs = dict(candidate.get("inputs", {})) if isinstance(candidate.get("inputs", {}), Mapping) else {}
        derived_payload = derive_workstation_invocation_payload_from_prompt(
            inputs=inputs,
            prompt=prompt,
            skill_title=skill_title,
        )
        if derived_payload is None:
            continue
        if effective_score < _DIRECT_COMPOSITION_SCORE_THRESHOLD:
            next_effective_score = (
                int(scored_skills[index + 1].get("_effective_score", 0) or 0)
                if (index + 1) < len(scored_skills)
                else -1
            )
            if not (
                derived_payload
                and (
                    ((index + 1) == len(scored_skills) and effective_score >= (_DIRECT_COMPOSITION_SCORE_THRESHOLD - 2))
                    or (effective_score >= (_DIRECT_COMPOSITION_SCORE_THRESHOLD - 3) and effective_score >= (next_effective_score + 2))
                )
            ):
                continue
        plan: dict[str, Any] = {
            "skill_title": skill_title,
            "semantic_unit": collapse_ws(str(prompt)),
        }
        if derived_payload:
            plan["invocation_payload"] = derived_payload
        return plan
    return None
