from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from learning_context_paths import canonical_learning_subject_id, learning_context_home
from semantic_text import collapse_ws


STAGED_SOURCE_SCHEMA_VERSION = "staged_source.v1"
SOURCE_REVISION_SCHEMA_VERSION = "source_revision.v1"
SOURCE_COLLECTION_SCHEMA_VERSION = "source_collection.v1"
VALID_STAGED_SOURCE_STATUSES = {"staged", "imported", "archived"}
VALID_SOURCE_REVISION_KINDS = {"capture", "discovery", "refresh", "llm_curation", "manual_curation", "merge"}


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _stable_gather_record_id(prefix: str, *parts: Any) -> str:
    normalized = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:12] if rendered else ("0" * 12)
    slug_source = normalized[-1] if normalized else prefix
    slug = "".join(char if char.isalnum() else "-" for char in slug_source).strip("-")[:48] or prefix
    return f"{prefix}_{slug}_{digest}"


def _normalized_choice(value: Any, *, allowed: set[str], default: str) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    return text if text in allowed else default


def gather_source_paths(root_path: Path, subject_id: str) -> dict[str, Path]:
    subject_home = learning_context_home(Path(root_path).expanduser().resolve(), subject_id)
    gather_root = subject_home / "gather"
    return {
        "root": gather_root,
        "sources": gather_root / "sources",
        "revisions": gather_root / "revisions",
        "bundles": gather_root / "bundles",
        "collections": gather_root / "collections",
        "indexes": gather_root / "indexes",
    }


def staged_source_body_path(root_path: Path, subject_id: str, revision_id: str) -> Path:
    return gather_source_paths(root_path, subject_id)["revisions"] / f"{collapse_ws(revision_id)}.md"


def staged_source_bundle_root(root_path: Path, subject_id: str, revision_id: str) -> Path:
    return gather_source_paths(root_path, subject_id)["bundles"] / collapse_ws(revision_id)


@dataclass(frozen=True)
class StagedSource:
    staged_source_id: str
    subject_id: str
    title: str
    source_ref: str
    source_kind: str = "url"
    media_type: str = "text/markdown"
    status: str = "staged"
    latest_revision_id: str = ""
    revision_count: int = 0
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": STAGED_SOURCE_SCHEMA_VERSION,
            "staged_source_id": self.staged_source_id,
            "subject_id": self.subject_id,
            "title": self.title,
            "source_ref": self.source_ref,
            "source_kind": self.source_kind,
            "media_type": self.media_type,
            "status": self.status,
            "latest_revision_id": self.latest_revision_id,
            "revision_count": self.revision_count,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StagedSource":
        return cls(
            staged_source_id=collapse_ws(str(payload.get("staged_source_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            title=collapse_ws(str(payload.get("title", ""))),
            source_ref=str(payload.get("source_ref", "") or ""),
            source_kind=collapse_ws(str(payload.get("source_kind", ""))) or "url",
            media_type=collapse_ws(str(payload.get("media_type", ""))) or "text/markdown",
            status=_normalized_choice(payload.get("status", "staged"), allowed=VALID_STAGED_SOURCE_STATUSES, default="staged"),
            latest_revision_id=collapse_ws(str(payload.get("latest_revision_id", ""))),
            revision_count=max(0, int(payload.get("revision_count", 0) or 0)),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class SourceRevision:
    revision_id: str
    staged_source_id: str
    subject_id: str
    revision_kind: str = "capture"
    source_ref: str = ""
    markdown_relpath: str = ""
    bundle_relpaths: tuple[str, ...] = ()
    created_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SOURCE_REVISION_SCHEMA_VERSION,
            "revision_id": self.revision_id,
            "staged_source_id": self.staged_source_id,
            "subject_id": self.subject_id,
            "revision_kind": self.revision_kind,
            "source_ref": self.source_ref,
            "markdown_relpath": self.markdown_relpath,
            "bundle_relpaths": list(self.bundle_relpaths),
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SourceRevision":
        return cls(
            revision_id=collapse_ws(str(payload.get("revision_id", ""))),
            staged_source_id=collapse_ws(str(payload.get("staged_source_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            revision_kind=_normalized_choice(
                payload.get("revision_kind", "capture"),
                allowed=VALID_SOURCE_REVISION_KINDS,
                default="capture",
            ),
            source_ref=str(payload.get("source_ref", "") or ""),
            markdown_relpath=str(payload.get("markdown_relpath", "") or ""),
            bundle_relpaths=tuple(
                str(item)
                for item in payload.get("bundle_relpaths", [])
                if collapse_ws(str(item))
            ),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class SourceCollection:
    collection_id: str
    subject_id: str
    title: str
    description: str = ""
    staged_source_ids: tuple[str, ...] = ()
    query_text: str = ""
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SOURCE_COLLECTION_SCHEMA_VERSION,
            "collection_id": self.collection_id,
            "subject_id": self.subject_id,
            "title": self.title,
            "description": self.description,
            "staged_source_ids": list(self.staged_source_ids),
            "query_text": self.query_text,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SourceCollection":
        return cls(
            collection_id=collapse_ws(str(payload.get("collection_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            title=collapse_ws(str(payload.get("title", ""))),
            description=str(payload.get("description", "") or ""),
            staged_source_ids=tuple(
                collapse_ws(str(item))
                for item in payload.get("staged_source_ids", [])
                if collapse_ws(str(item))
            ),
            query_text=str(payload.get("query_text", "") or ""),
            created_at_epoch_ms=max(0, int(payload.get("created_at_epoch_ms", 0) or 0)),
            updated_at_epoch_ms=max(0, int(payload.get("updated_at_epoch_ms", 0) or 0)),
            metadata=dict(payload.get("metadata", {})),
        )


def new_staged_source(
    *,
    subject_id: str,
    title: str,
    source_ref: str = "",
    source_kind: str = "url",
    media_type: str = "text/markdown",
    metadata: dict[str, Any] | None = None,
) -> StagedSource:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    now_ms = int(time.time() * 1000)
    return StagedSource(
        staged_source_id=_stable_gather_record_id(
            "staged_source",
            normalized_subject_id,
            title or normalized_subject_id,
            source_ref,
        ),
        subject_id=normalized_subject_id,
        title=collapse_ws(title),
        source_ref=str(source_ref or ""),
        source_kind=collapse_ws(source_kind) or "url",
        media_type=collapse_ws(media_type) or "text/markdown",
        status="staged",
        created_at_epoch_ms=now_ms,
        updated_at_epoch_ms=now_ms,
        metadata=dict(metadata or {}),
    )


def new_source_revision(
    *,
    staged_source_id: str,
    subject_id: str,
    source_ref: str = "",
    revision_kind: str = "capture",
    metadata: dict[str, Any] | None = None,
) -> SourceRevision:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    now_ms = int(time.time() * 1000)
    revision_id = _stable_gather_record_id(
        "source_revision",
        normalized_subject_id,
        staged_source_id,
        revision_kind,
        now_ms,
        source_ref,
    )
    return SourceRevision(
        revision_id=revision_id,
        staged_source_id=collapse_ws(staged_source_id),
        subject_id=normalized_subject_id,
        revision_kind=_normalized_choice(revision_kind, allowed=VALID_SOURCE_REVISION_KINDS, default="capture"),
        source_ref=str(source_ref or ""),
        markdown_relpath=f"{revision_id}.md",
        bundle_relpaths=(),
        created_at_epoch_ms=now_ms,
        metadata=dict(metadata or {}),
    )


def default_source_collection(
    *,
    subject_id: str,
    staged_source_ids: tuple[str, ...] | list[str] = (),
    existing: SourceCollection | None = None,
) -> SourceCollection:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    now_ms = int(time.time() * 1000)
    source_ids = tuple(
        dict.fromkeys(
            collapse_ws(str(item))
            for item in staged_source_ids
            if collapse_ws(str(item))
        )
    )
    created_at = existing.created_at_epoch_ms if isinstance(existing, SourceCollection) else now_ms
    metadata = dict(existing.metadata) if isinstance(existing, SourceCollection) else {}
    metadata.setdefault("collection_kind", "all_gather_sources")
    return SourceCollection(
        collection_id=_stable_gather_record_id("source_collection", normalized_subject_id, "all-gather-sources"),
        subject_id=normalized_subject_id,
        title="All Gather Sources",
        description="The full staged-source set for this subject before corpus admission.",
        staged_source_ids=source_ids,
        query_text="",
        created_at_epoch_ms=created_at,
        updated_at_epoch_ms=now_ms,
        metadata=metadata,
    )


def new_source_collection(
    *,
    subject_id: str,
    title: str,
    description: str = "",
    staged_source_ids: tuple[str, ...] | list[str] = (),
    query_text: str = "",
    metadata: dict[str, Any] | None = None,
) -> SourceCollection:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    now_ms = int(time.time() * 1000)
    normalized_title = collapse_ws(title) or "Source Set"
    source_ids = tuple(
        dict.fromkeys(
            collapse_ws(str(item))
            for item in staged_source_ids
            if collapse_ws(str(item))
        )
    )
    normalized_metadata = dict(metadata or {})
    normalized_metadata.setdefault("collection_kind", "manual")
    return SourceCollection(
        collection_id=_stable_gather_record_id(
            "source_collection",
            normalized_subject_id,
            normalized_title,
            now_ms,
        ),
        subject_id=normalized_subject_id,
        title=normalized_title,
        description=str(description or ""),
        staged_source_ids=source_ids,
        query_text=str(query_text or ""),
        created_at_epoch_ms=now_ms,
        updated_at_epoch_ms=now_ms,
        metadata=normalized_metadata,
    )


def persist_staged_source(root_path: Path, staged_source: StagedSource) -> Path:
    normalized = StagedSource.from_dict(staged_source.to_dict())
    target = gather_source_paths(root_path, normalized.subject_id)["sources"] / f"{normalized.staged_source_id}.json"
    _write_json(target, normalized.to_dict())
    return target


def persist_source_collection(root_path: Path, collection: SourceCollection) -> Path:
    normalized = SourceCollection.from_dict(collection.to_dict())
    target = gather_source_paths(root_path, normalized.subject_id)["collections"] / f"{normalized.collection_id}.json"
    _write_json(target, normalized.to_dict())
    return target


def load_staged_source(root_path: Path, subject_id: str, staged_source_id: str) -> StagedSource:
    path = gather_source_paths(root_path, subject_id)["sources"] / f"{collapse_ws(staged_source_id)}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return StagedSource.from_dict(_read_json(path))


def load_source_collection(root_path: Path, subject_id: str, collection_id: str) -> SourceCollection:
    path = gather_source_paths(root_path, subject_id)["collections"] / f"{collapse_ws(collection_id)}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return SourceCollection.from_dict(_read_json(path))


def list_staged_sources(root_path: Path, subject_id: str, *, include_archived: bool = False) -> tuple[StagedSource, ...]:
    sources_root = gather_source_paths(root_path, subject_id)["sources"]
    if not sources_root.exists():
        return ()
    items: list[StagedSource] = []
    for path in sorted(sources_root.glob("*.json")):
        source = StagedSource.from_dict(_read_json(path))
        if not collapse_ws(source.staged_source_id):
            continue
        if not include_archived and source.status == "archived":
            continue
        items.append(source)
    return tuple(sorted(items, key=lambda item: (-item.updated_at_epoch_ms, item.title.casefold(), item.staged_source_id)))


def list_source_collections(root_path: Path, subject_id: str) -> tuple[SourceCollection, ...]:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    collections_root = gather_source_paths(root_path, normalized_subject_id)["collections"]
    items: list[SourceCollection] = []
    if collections_root.exists():
        for path in sorted(collections_root.glob("*.json")):
            collection = SourceCollection.from_dict(_read_json(path))
            if not collapse_ws(collection.collection_id):
                continue
            items.append(collection)
    staged_sources = list_staged_sources(root_path, normalized_subject_id)
    source_ids = tuple(collapse_ws(item.staged_source_id) for item in staged_sources if collapse_ws(item.staged_source_id))
    existing_default = next(
        (
            item
            for item in items
            if collapse_ws(str(item.metadata.get("collection_kind", ""))) == "all_gather_sources"
        ),
        None,
    )
    default_collection = default_source_collection(
        subject_id=normalized_subject_id,
        staged_source_ids=source_ids,
        existing=existing_default,
    )
    if existing_default is None or existing_default.staged_source_ids != default_collection.staged_source_ids:
        persist_source_collection(root_path, default_collection)
        items = [item for item in items if item.collection_id != default_collection.collection_id]
        items.append(default_collection)
    return tuple(
        sorted(
            items,
            key=lambda item: (
                0 if collapse_ws(str(item.metadata.get("collection_kind", ""))) == "all_gather_sources" else 1,
                item.title.casefold(),
                item.collection_id,
            ),
        )
    )


def persist_source_revision(
    root_path: Path,
    revision: SourceRevision,
    *,
    markdown_text: str,
    bundle_files: Mapping[str, Any] | None = None,
) -> tuple[Path, Path, tuple[Path, ...]]:
    normalized = SourceRevision.from_dict(revision.to_dict())
    paths = gather_source_paths(root_path, normalized.subject_id)
    revision_target = paths["revisions"] / f"{normalized.revision_id}.json"
    markdown_target = staged_source_body_path(root_path, normalized.subject_id, normalized.revision_id)
    markdown_target.parent.mkdir(parents=True, exist_ok=True)
    markdown_target.write_text(str(markdown_text or ""), encoding="utf-8")
    persisted_bundle_paths: list[Path] = []
    bundle_relpaths: list[str] = []
    for raw_relpath, raw_content in dict(bundle_files or {}).items():
        relpath_text = str(raw_relpath or "").strip()
        if not relpath_text:
            continue
        relpath = Path(relpath_text)
        if relpath.is_absolute() or ".." in relpath.parts:
            raise ValueError(f"Bundle file path must be relative: {relpath_text}")
        target = staged_source_bundle_root(root_path, normalized.subject_id, normalized.revision_id) / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(raw_content, bytes):
            target.write_bytes(raw_content)
        else:
            target.write_text(str(raw_content), encoding="utf-8")
        persisted_bundle_paths.append(target)
        bundle_relpaths.append(relpath_text)
    normalized = SourceRevision(
        revision_id=normalized.revision_id,
        staged_source_id=normalized.staged_source_id,
        subject_id=normalized.subject_id,
        revision_kind=normalized.revision_kind,
        source_ref=normalized.source_ref,
        markdown_relpath=markdown_target.name,
        bundle_relpaths=tuple(bundle_relpaths),
        created_at_epoch_ms=normalized.created_at_epoch_ms,
        metadata=dict(normalized.metadata),
    )
    _write_json(revision_target, normalized.to_dict())
    return revision_target, markdown_target, tuple(persisted_bundle_paths)


def load_source_revision(root_path: Path, subject_id: str, revision_id: str) -> SourceRevision:
    path = gather_source_paths(root_path, subject_id)["revisions"] / f"{collapse_ws(revision_id)}.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    return SourceRevision.from_dict(_read_json(path))


def list_source_revisions(
    root_path: Path,
    subject_id: str,
    *,
    staged_source_id: str = "",
) -> tuple[SourceRevision, ...]:
    revisions_root = gather_source_paths(root_path, subject_id)["revisions"]
    if not revisions_root.exists():
        return ()
    normalized_source_id = collapse_ws(staged_source_id)
    items: list[SourceRevision] = []
    for path in sorted(revisions_root.glob("*.json")):
        revision = SourceRevision.from_dict(_read_json(path))
        if not collapse_ws(revision.revision_id):
            continue
        if normalized_source_id and collapse_ws(revision.staged_source_id) != normalized_source_id:
            continue
        items.append(revision)
    return tuple(
        sorted(
            items,
            key=lambda item: (-item.created_at_epoch_ms, item.revision_kind, item.revision_id),
        )
    )


def latest_source_revision(root_path: Path, staged_source: StagedSource) -> SourceRevision | None:
    revision_id = collapse_ws(staged_source.latest_revision_id)
    if not revision_id:
        return None
    try:
        return load_source_revision(root_path, staged_source.subject_id, revision_id)
    except Exception:
        return None
