from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parent.parent
DST_SOURCE_ROOT = Path(__file__).resolve().parent
_DST_PACKAGE_TYPED_FIXTURE_ROOT = DST_SOURCE_ROOT / "tests" / "fixtures" / "dst"
_DST_LEGACY_TYPED_FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "dst"
DST_TYPED_FIXTURE_ROOT = (
    _DST_PACKAGE_TYPED_FIXTURE_ROOT
    if _DST_PACKAGE_TYPED_FIXTURE_ROOT.exists()
    else _DST_LEGACY_TYPED_FIXTURE_ROOT
)

CANONICAL_SECTION_ALIASES: dict[str, str] = {
    "situation": "situation",
    "actors": "actors",
    "actor": "actors",
    "objectives": "objectives",
    "objective": "objectives",
    "capabilities": "capabilities",
    "capability": "capabilities",
    "dependencies": "dependencies",
    "dependency": "dependencies",
    "constraints": "constraints",
    "constraint": "constraints",
    "boundaries": "boundaries",
    "boundary": "boundaries",
    "states": "states",
    "state": "states",
    "transitions": "transitions",
    "transition": "transitions",
}
CORE_USE_CASE_SECTION_KEYS: tuple[str, ...] = (
    "actors",
    "objectives",
    "capabilities",
    "dependencies",
    "constraints",
    "boundaries",
    "states",
    "transitions",
)

_HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*[*-]\s+(.*\S)\s*$")
_NUMBERING_PREFIX_RE = re.compile(r"^\s*\d+(?:\.\d+)*\s*[\.\)]?\s*")
_WS_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_ROUTE_TOKEN_RE = re.compile(r"s[\w-]*")
_ROUTE_RE = re.compile(r"s[\w-]*(?:\s*->\s*s[\w-]*)+")
_CODED_ITEM_RE = re.compile(r"^`([^`]+)`\s*:\s*(.+)$")


@dataclass(frozen=True)
class DstEntry:
    code: str
    text: str

    @classmethod
    def from_bullet(cls, bullet: str) -> "DstEntry":
        item = bullet.strip()
        match = _CODED_ITEM_RE.match(item)
        if match:
            return cls(code=_collapse_ws(match.group(1)), text=_collapse_ws(match.group(2)))
        return cls(code="", text=_collapse_ws(item))

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstEntry":
        return cls(
            code=str(payload.get("code", "") or ""),
            text=str(payload.get("text", "") or ""),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "text": self.text,
        }

    def display(self) -> str:
        if self.code:
            return f"`{self.code}`: {self.text}"
        return self.text

    def seed_name(self) -> str:
        return self.code or self.text


@dataclass(frozen=True)
class DstSection:
    key: str
    title: str
    narrative: str
    entries: tuple[DstEntry, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstSection":
        return cls(
            key=str(payload["key"]),
            title=str(payload["title"]),
            narrative=str(payload.get("narrative", "") or ""),
            entries=tuple(
                DstEntry.from_dict(entry)
                for entry in list(payload.get("entries", []))
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "title": self.title,
            "narrative": self.narrative,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @property
    def bullet_items(self) -> tuple[str, ...]:
        return tuple(entry.display() for entry in self.entries)


@dataclass(frozen=True)
class DstCandidatePath:
    title: str
    parent_title: str
    route_expression: str
    narrative: str
    highlights: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstCandidatePath":
        return cls(
            title=str(payload["title"]),
            parent_title=str(payload["parent_title"]),
            route_expression=str(payload.get("route_expression", "") or ""),
            narrative=str(payload.get("narrative", "") or ""),
            highlights=tuple(str(item) for item in list(payload.get("highlights", []))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "parent_title": self.parent_title,
            "route_expression": self.route_expression,
            "narrative": self.narrative,
            "highlights": list(self.highlights),
        }


@dataclass(frozen=True)
class DstUseCaseFixture:
    fixture_id: str
    title: str
    title_key: str
    source_ref: str
    summary: str
    sections: tuple[DstSection, ...]
    candidate_paths: tuple[DstCandidatePath, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DstUseCaseFixture":
        return cls(
            fixture_id=str(payload["fixture_id"]),
            title=str(payload["title"]),
            title_key=str(payload["title_key"]),
            source_ref=str(payload["source_ref"]),
            summary=str(payload.get("summary", "") or ""),
            sections=tuple(
                DstSection.from_dict(section)
                for section in list(payload.get("sections", []))
            ),
            candidate_paths=tuple(
                DstCandidatePath.from_dict(path)
                for path in list(payload.get("candidate_paths", []))
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "fixture_id": self.fixture_id,
            "title": self.title,
            "title_key": self.title_key,
            "source_ref": self.source_ref,
            "summary": self.summary,
            "sections": [section.to_dict() for section in self.sections],
            "candidate_paths": [path.to_dict() for path in self.candidate_paths],
        }

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_ref

    def section(self, key: str) -> DstSection | None:
        normalized = _normalize_section_key(key)
        for section in self.sections:
            if section.key == normalized:
                return section
        return None

    def section_entries(self, key: str) -> tuple[DstEntry, ...]:
        section = self.section(key)
        return section.entries if section is not None else ()

    def section_items(self, key: str) -> tuple[str, ...]:
        return tuple(entry.display() for entry in self.section_entries(key))

    def coordinated_seed(self) -> "DstCoordinatedSeed":
        return DstCoordinatedSeed(
            title=self.title,
            source_ref=self.source_ref,
            actors=tuple(entry.seed_name() for entry in self.section_entries("actors")),
            objectives=tuple(entry.seed_name() for entry in self.section_entries("objectives")),
            capabilities=tuple(entry.seed_name() for entry in self.section_entries("capabilities")),
            dependencies=tuple(entry.seed_name() for entry in self.section_entries("dependencies")),
            constraints=tuple(entry.seed_name() for entry in self.section_entries("constraints")),
            boundaries=tuple(entry.seed_name() for entry in self.section_entries("boundaries")),
            states=tuple(entry.seed_name() for entry in self.section_entries("states")),
            transitions=tuple(entry.seed_name() for entry in self.section_entries("transitions")),
            candidate_path_titles=tuple(path.title for path in self.candidate_paths),
            candidate_route_expressions=tuple(
                path.route_expression for path in self.candidate_paths if path.route_expression
            ),
        )


@dataclass(frozen=True)
class DstCoordinatedSeed:
    title: str
    source_ref: str
    actors: tuple[str, ...]
    objectives: tuple[str, ...]
    capabilities: tuple[str, ...]
    dependencies: tuple[str, ...]
    constraints: tuple[str, ...]
    boundaries: tuple[str, ...]
    states: tuple[str, ...]
    transitions: tuple[str, ...]
    candidate_path_titles: tuple[str, ...]
    candidate_route_expressions: tuple[str, ...]


@dataclass(frozen=True)
class DstFixtureCatalog:
    fixtures: tuple[DstUseCaseFixture, ...]
    duplicate_title_keys: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class _HeadingBlock:
    level: int
    title: str
    body: str
    start: int = 0
    end: int = 0


def _collapse_ws(value: str) -> str:
    return _WS_RE.sub(" ", value).strip()


def _strip_numbering_prefix(title: str) -> str:
    return _NUMBERING_PREFIX_RE.sub("", title).strip()


def _normalize_section_key(title: str) -> str:
    normalized = _collapse_ws(_strip_numbering_prefix(title)).lower()
    return CANONICAL_SECTION_ALIASES.get(normalized, normalized)


def _title_key(title: str) -> str:
    lowered = _NON_ALNUM_RE.sub("-", _strip_numbering_prefix(title).lower()).strip("-")
    return lowered


def _heading_blocks(markdown: str) -> tuple[_HeadingBlock, ...]:
    matches = list(_HEADING_RE.finditer(markdown))
    blocks: list[_HeadingBlock] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        blocks.append(
            _HeadingBlock(
                level=len(match.group(1)),
                title=_collapse_ws(match.group(2)),
                body=markdown[body_start:body_end].strip(),
                start=match.start(),
                end=body_end,
            )
        )
    return tuple(blocks)


def _section_blocks(markdown: str, level: int) -> tuple[_HeadingBlock, ...]:
    matches = list(_HEADING_RE.finditer(markdown))
    selected = [match for match in matches if len(match.group(1)) == level]
    blocks: list[_HeadingBlock] = []
    for match in selected:
        body_start = match.end()
        body_end = len(markdown)
        for later in matches:
            if later.start() <= match.start():
                continue
            if len(later.group(1)) <= level:
                body_end = later.start()
                break
        blocks.append(
            _HeadingBlock(
                level=level,
                title=_collapse_ws(match.group(2)),
                body=markdown[body_start:body_end].strip(),
                start=match.start(),
                end=body_end,
            )
        )
    return tuple(blocks)


def _paragraphs(text: str) -> tuple[str, ...]:
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---":
            cleaned_lines.append("")
            continue
        cleaned_lines.append(line.rstrip())
    joined = "\n".join(cleaned_lines)
    chunks = [_collapse_ws(chunk) for chunk in re.split(r"\n\s*\n", joined) if chunk.strip()]
    return tuple(chunk for chunk in chunks if chunk and not chunk.startswith("#"))


def _first_summary_paragraph(text: str) -> str:
    for paragraph in _paragraphs(text):
        if paragraph.startswith(">"):
            continue
        return paragraph
    return ""


def _body_before_nested_heading(text: str, level: int) -> str:
    matches = list(_HEADING_RE.finditer(text))
    for match in matches:
        if len(match.group(1)) == level:
            return text[:match.start()].strip()
    return text.strip()


def _contiguous_bullet_blocks(text: str) -> tuple[tuple[str, ...], ...]:
    blocks: list[tuple[str, ...]] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = _BULLET_RE.match(line)
        if match:
            current.append(match.group(1).strip())
            continue
        if current and not stripped:
            blocks.append(tuple(current))
            current = []
            continue
        if current and stripped:
            blocks.append(tuple(current))
            current = []
    if current:
        blocks.append(tuple(current))
    return tuple(blocks)


def _narrative_without_bullets(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            lines.append("")
            continue
        if _HEADING_RE.match(stripped) or _BULLET_RE.match(line):
            continue
        lines.append(line.rstrip())
    paragraphs = [
        paragraph
        for paragraph in _paragraphs("\n".join(lines))
        if paragraph.lower() not in {"for example:", "for example"}
    ]
    return "\n\n".join(paragraphs)


def _is_candidate_parent(title: str) -> bool:
    normalized = _normalize_section_key(title)
    return any(
        token in normalized
        for token in (
            "solution",
            "solutions",
            "candidate path",
            "candidate paths",
            "possible candidate paths",
        )
    )


def _sanitize_route_expression(route_expression: str, *, allowed_state_codes: set[str]) -> str:
    if not route_expression:
        return ""
    tokens = [token for token in _ROUTE_TOKEN_RE.findall(route_expression) if token in allowed_state_codes]
    if len(tokens) >= 2:
        return " -> ".join(tokens)
    return route_expression


def _route_expression(text: str, *, allowed_state_codes: set[str]) -> str:
    candidate_lines: list[str] = []
    for line in text.splitlines():
        normalized = line.replace("`", "")
        if _ROUTE_RE.search(normalized):
            candidate_lines.append(normalized)
    if not candidate_lines:
        return ""
    preferred = [
        line for line in candidate_lines
        if "admissible" in line.lower() and "inadmissible" not in line.lower()
    ]
    chosen = preferred[0] if preferred else candidate_lines[0]
    match = _ROUTE_RE.search(chosen)
    if not match:
        return ""
    return _sanitize_route_expression(_collapse_ws(match.group(0)), allowed_state_codes=allowed_state_codes)


def _extract_section_entries(key: str, text: str) -> tuple[DstEntry, ...]:
    bullet_blocks = _contiguous_bullet_blocks(text)
    if not bullet_blocks:
        return ()
    first_block = tuple(DstEntry.from_bullet(item) for item in bullet_blocks[0])
    if key in {"states", "transitions"} and not any(entry.code for entry in first_block):
        return ()
    return first_block


def _candidate_from_block(
    block: _HeadingBlock,
    *,
    parent_title: str,
    allowed_state_codes: set[str],
) -> DstCandidatePath | None:
    route_expression = _route_expression(block.body, allowed_state_codes=allowed_state_codes)
    if not (_is_candidate_parent(parent_title) or route_expression):
        return None
    highlights = tuple(item for block_items in _contiguous_bullet_blocks(block.body) for item in block_items)
    return DstCandidatePath(
        title=_strip_numbering_prefix(block.title),
        parent_title=_strip_numbering_prefix(parent_title),
        route_expression=route_expression,
        narrative=_narrative_without_bullets(block.body),
        highlights=highlights,
    )


def _looks_like_use_case(block: _HeadingBlock) -> bool:
    section_keys = {
        _normalize_section_key(child.title)
        for child in (*_section_blocks(block.body, 2), *_section_blocks(block.body, 3))
    }
    return len(section_keys.intersection(CORE_USE_CASE_SECTION_KEYS)) >= 3


def list_dst_source_paths(root: Path | None = None) -> tuple[Path, ...]:
    source_root = root or DST_SOURCE_ROOT
    excluded_names = {"DST.md", "DST_IMPLEMENTATION.md", "DST_PROMPT.md"}
    return tuple(
        sorted(
            path
            for path in source_root.glob("*.md")
            if path.is_file() and path.name not in excluded_names
        )
    )


def list_dst_fixture_paths(root: Path | None = None) -> tuple[Path, ...]:
    fixture_root = root or DST_TYPED_FIXTURE_ROOT
    return tuple(sorted(path for path in fixture_root.glob("*.json") if path.is_file()))


def dst_use_cases_from_markdown(markdown: str, *, source_path: Path) -> tuple[DstUseCaseFixture, ...]:
    h1_blocks = _section_blocks(markdown, 1)
    use_case_blocks = tuple(block for block in h1_blocks if _looks_like_use_case(block))
    fixtures: list[DstUseCaseFixture] = []
    for h1 in use_case_blocks:
        sections: list[DstSection] = []
        state_codes: set[str] = set()
        for h2 in _section_blocks(h1.body, 2):
            h3_blocks = _section_blocks(h2.body, 3)
            key = _normalize_section_key(h2.title)
            if key == "situation":
                situation_body = _body_before_nested_heading(h2.body, 3)
                sections.append(
                    DstSection(
                        key="situation",
                        title=_strip_numbering_prefix(h2.title),
                        narrative=_narrative_without_bullets(situation_body),
                        entries=(),
                    )
                )
            elif key in CORE_USE_CASE_SECTION_KEYS:
                section_body = _body_before_nested_heading(h2.body, 3) if h3_blocks else h2.body
                entries = _extract_section_entries(key, section_body)
                sections.append(
                    DstSection(
                        key=key,
                        title=_strip_numbering_prefix(h2.title),
                        narrative=_narrative_without_bullets(section_body),
                        entries=entries,
                    )
                )
                if key == "states":
                    state_codes.update(entry.code for entry in entries if entry.code)
            for h3 in h3_blocks:
                child_key = _normalize_section_key(h3.title)
                if child_key in CORE_USE_CASE_SECTION_KEYS:
                    entries = _extract_section_entries(child_key, h3.body)
                    sections.append(
                        DstSection(
                            key=child_key,
                            title=_strip_numbering_prefix(h3.title),
                            narrative=_narrative_without_bullets(h3.body),
                            entries=entries,
                        )
                    )
                    if child_key == "states":
                        state_codes.update(entry.code for entry in entries if entry.code)
        candidate_paths: list[DstCandidatePath] = []
        for h2 in _section_blocks(h1.body, 2):
            h3_blocks = _section_blocks(h2.body, 3)
            for h3 in h3_blocks:
                candidate = _candidate_from_block(
                    h3,
                    parent_title=h2.title,
                    allowed_state_codes=state_codes,
                )
                if candidate is not None:
                    candidate_paths.append(candidate)
            if not h3_blocks:
                candidate = _candidate_from_block(
                    h2,
                    parent_title=h2.title,
                    allowed_state_codes=state_codes,
                )
                if candidate is not None:
                    candidate_paths.append(candidate)
        source_ref = str(source_path.relative_to(REPO_ROOT))
        fixtures.append(
            DstUseCaseFixture(
                fixture_id=_title_key(source_path.stem),
                title=_strip_numbering_prefix(h1.title),
                title_key=_title_key(h1.title),
                source_ref=source_ref,
                summary=_first_summary_paragraph(h1.body),
                sections=tuple(sections),
                candidate_paths=tuple(candidate_paths),
            )
        )
    return tuple(fixtures)


def load_dst_source_use_cases(root: Path | None = None) -> tuple[DstUseCaseFixture, ...]:
    fixtures: list[DstUseCaseFixture] = []
    for path in list_dst_source_paths(root):
        fixtures.extend(dst_use_cases_from_markdown(path.read_text(encoding="utf-8"), source_path=path))
    return tuple(sorted(fixtures, key=lambda item: (item.source_ref, item.title.lower())))


def load_dst_use_cases(root: Path | None = None) -> tuple[DstUseCaseFixture, ...]:
    fixture_root = root or DST_TYPED_FIXTURE_ROOT
    fixtures = tuple(
        DstUseCaseFixture.from_dict(json.loads(path.read_text(encoding="utf-8")))
        for path in list_dst_fixture_paths(fixture_root)
    )
    return tuple(sorted(fixtures, key=lambda item: (item.source_ref, item.title.lower())))


def load_dst_fixture_catalog(root: Path | None = None) -> DstFixtureCatalog:
    fixtures = load_dst_use_cases(root)
    collisions: dict[str, list[str]] = {}
    for fixture in fixtures:
        collisions.setdefault(fixture.title_key, []).append(fixture.source_ref)
    duplicate_title_keys = {
        key: tuple(sorted(source_refs))
        for key, source_refs in collisions.items()
        if len(source_refs) > 1
    }
    return DstFixtureCatalog(fixtures=fixtures, duplicate_title_keys=duplicate_title_keys)


def normalize_dst_source_ref(path_text: str) -> str:
    normalized = _collapse_ws(path_text)
    if not normalized:
        return ""
    path = Path(normalized).expanduser()
    try:
        resolved = path.resolve(strict=False)
    except Exception:
        resolved = path
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except Exception:
        pass
    if not path.is_absolute():
        return normalized
    return str(resolved)


def match_dst_fixture_for_source_refs(
    source_refs: tuple[str, ...] | list[str],
    *,
    fixtures: tuple[DstUseCaseFixture, ...] | None = None,
) -> DstUseCaseFixture | None:
    normalized_refs = {
        normalize_dst_source_ref(str(item))
        for item in source_refs
        if _collapse_ws(str(item))
    }
    normalized_refs.discard("")
    if not normalized_refs:
        return None
    catalog = fixtures or load_dst_use_cases()
    for fixture in catalog:
        if normalize_dst_source_ref(fixture.source_ref) in normalized_refs:
            return fixture
    # Browser uploads and copied markdown ingress rewrite the path outside the
    # repo, but they preserve the canonical filename. Fall back to a unique
    # basename match so the governed DST route still survives that transport hop.
    source_names = {
        Path(ref).name.casefold()
        for ref in normalized_refs
        if Path(ref).name
    }
    if not source_names:
        return None
    basename_matches = [
        fixture
        for fixture in catalog
        if Path(normalize_dst_source_ref(fixture.source_ref)).name.casefold()
        in source_names
    ]
    if len(basename_matches) == 1:
        return basename_matches[0]
    return None


__all__ = [
    "CANONICAL_SECTION_ALIASES",
    "CORE_USE_CASE_SECTION_KEYS",
    "DST_SOURCE_ROOT",
    "DST_TYPED_FIXTURE_ROOT",
    "DstCandidatePath",
    "DstCoordinatedSeed",
    "DstEntry",
    "DstFixtureCatalog",
    "DstSection",
    "DstUseCaseFixture",
    "dst_use_cases_from_markdown",
    "list_dst_fixture_paths",
    "list_dst_source_paths",
    "load_dst_fixture_catalog",
    "load_dst_source_use_cases",
    "load_dst_use_cases",
    "match_dst_fixture_for_source_refs",
    "normalize_dst_source_ref",
]
