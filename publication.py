# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from id_generation import slugify
from semantic_text import collapse_ws


PUBLICATION_SCHEMA_VERSION = "publication.v1"
PUBLICATION_BUILD_SCHEMA_VERSION = "publication_build.v1"
PUBLICATION_COMPOSITION_SCHEMA_VERSION = "publication_composition.v1"
VALID_PUBLICATION_XREF_TYPES = frozenset(
    {
        "supports",
        "contradicts",
        "defines",
        "extends",
        "depends_on",
        "supersedes",
        "example_of",
        "derived_from",
        "see_also",
    }
)
VALID_PUBLICATION_XREF_TARGET_KINDS = frozenset(
    {
        "publication",
        "section",
        "claim",
        "unit",
        "source",
        "entity",
        "block",
    }
)
VALID_PUBLICATION_SECTION_ROLES = frozenset(
    {
        "summary",
        "background",
        "definition",
        "evidence",
        "analysis",
        "comparison",
        "recommendation",
        "implementation",
        "appendix",
    }
)


def publication_statement_is_reportable(statement: str, *, unit_kind: str = "") -> bool:
    normalized_statement = collapse_ws(statement)
    if not normalized_statement:
        return False
    normalized_kind = collapse_ws(unit_kind).casefold()
    if normalized_kind in {"open_question", "source_note"}:
        return False
    lowered = normalized_statement.casefold()
    if normalized_statement.endswith("?"):
        return False
    if lowered.startswith("how do you calculate "):
        return False
    return True


def _ordered_unique_texts(items: list[Any] | tuple[Any, ...] | set[Any] | None) -> tuple[str, ...]:
    if not items:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        text = collapse_ws(str(item))
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _normalized_publication_xref_type(value: str) -> str:
    normalized = collapse_ws(value).lower().replace("-", "_").replace(" ", "_")
    return normalized


def _normalized_publication_xref_kind(value: str) -> str:
    normalized = collapse_ws(value).lower().replace("-", "_").replace(" ", "_")
    return normalized


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_publication_id(*, subject_id: str, publication_type: str, title: str) -> str:
    return f"pub_{slugify(subject_id, limit=40)}_{slugify(publication_type, limit=16)}_{hashlib.sha256(collapse_ws(title).encode('utf-8')).hexdigest()[:10]}"


def stable_publication_build_id(*, publication_snapshot_hash: str, learning_context_snapshot_hash: str, renderer_id: str, template_id: str) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_snapshot_hash),
                collapse_ws(learning_context_snapshot_hash),
                collapse_ws(renderer_id),
                collapse_ws(template_id),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"pubbuild_{digest}"


def stable_publication_composition_id(
    *,
    publication_id: str,
    learning_context_snapshot_hash: str,
    title: str,
) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_id),
                collapse_ws(learning_context_snapshot_hash),
                collapse_ws(title),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"pubcomp_{digest}"


def stable_publication_xref_id(
    *,
    publication_id: str,
    from_kind: str,
    from_id: str,
    xref_type: str,
    to_kind: str,
    to_id: str,
) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_id),
                _normalized_publication_xref_kind(from_kind),
                collapse_ws(from_id),
                _normalized_publication_xref_type(xref_type),
                _normalized_publication_xref_kind(to_kind),
                collapse_ws(to_id),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"xref_{slugify(xref_type, limit=20)}_{digest}"


def stable_publication_block_id(
    *,
    publication_id: str,
    block_kind: str,
    title: str,
    anchor_id: str = "",
) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_id),
                collapse_ws(block_kind),
                collapse_ws(title),
                collapse_ws(anchor_id),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"blk_{slugify(block_kind, limit=20)}_{digest}"


def stable_publication_entity_id(
    *,
    publication_id: str,
    entity_kind: str,
    canonical_name: str,
) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_id),
                collapse_ws(entity_kind),
                collapse_ws(canonical_name),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"ent_{slugify(entity_kind, limit=20)}_{digest}"


def stable_publication_review_id(
    *,
    publication_id: str,
    target_kind: str,
    target_id: str,
    reviewer: str,
    review_state: str,
) -> str:
    digest = hashlib.sha256(
        "::".join(
            [
                collapse_ws(publication_id),
                collapse_ws(target_kind),
                collapse_ws(target_id),
                collapse_ws(reviewer),
                collapse_ws(review_state),
            ]
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"review_{digest}"


@dataclass(frozen=True)
class Publication:
    publication_id: str
    publication_type: str
    subject_id: str
    title: str
    status: str
    scope_summary: str
    learning_context_ref: str
    learning_context_snapshot_hash: str
    included_unit_ids: tuple[str, ...] = ()
    excluded_unit_ids: tuple[str, ...] = ()
    root_section_ids: tuple[str, ...] = ()
    block_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    schema_version: str = PUBLICATION_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "publication_id": self.publication_id,
            "publication_type": self.publication_type,
            "subject_id": self.subject_id,
            "title": self.title,
            "status": self.status,
            "scope_summary": self.scope_summary,
            "learning_context_ref": self.learning_context_ref,
            "learning_context_snapshot_hash": self.learning_context_snapshot_hash,
            "included_unit_ids": list(self.included_unit_ids),
            "excluded_unit_ids": list(self.excluded_unit_ids),
            "root_section_ids": list(self.root_section_ids),
            "block_ids": list(self.block_ids),
            "claim_ids": list(self.claim_ids),
            "entity_ids": list(self.entity_ids),
            "source_ids": list(self.source_ids),
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Publication":
        return cls(
            publication_id=collapse_ws(str(payload.get("publication_id", ""))),
            publication_type=collapse_ws(str(payload.get("publication_type", ""))),
            subject_id=collapse_ws(str(payload.get("subject_id", ""))),
            title=collapse_ws(str(payload.get("title", ""))),
            status=collapse_ws(str(payload.get("status", ""))),
            scope_summary=str(payload.get("scope_summary", "")),
            learning_context_ref=str(payload.get("learning_context_ref", "")),
            learning_context_snapshot_hash=collapse_ws(str(payload.get("learning_context_snapshot_hash", ""))),
            included_unit_ids=_ordered_unique_texts(payload.get("included_unit_ids", [])),
            excluded_unit_ids=_ordered_unique_texts(payload.get("excluded_unit_ids", [])),
            root_section_ids=_ordered_unique_texts(payload.get("root_section_ids", [])),
            block_ids=_ordered_unique_texts(payload.get("block_ids", [])),
            claim_ids=_ordered_unique_texts(payload.get("claim_ids", [])),
            entity_ids=_ordered_unique_texts(payload.get("entity_ids", [])),
            source_ids=_ordered_unique_texts(payload.get("source_ids", [])),
            created_at_epoch_ms=int(payload.get("created_at_epoch_ms", 0) or 0),
            updated_at_epoch_ms=int(payload.get("updated_at_epoch_ms", 0) or 0),
            schema_version=collapse_ws(str(payload.get("schema_version", PUBLICATION_SCHEMA_VERSION))) or PUBLICATION_SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class PublicationSection:
    section_id: str
    publication_id: str
    parent_section_id: str
    role: str
    title: str
    ordinal: str
    child_section_ids: tuple[str, ...] = ()
    block_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()
    xref_ids: tuple[str, ...] = ()
    status: str = "active"

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "publication_id": self.publication_id,
            "parent_section_id": self.parent_section_id,
            "role": self.role,
            "title": self.title,
            "ordinal": self.ordinal,
            "child_section_ids": list(self.child_section_ids),
            "block_ids": list(self.block_ids),
            "claim_ids": list(self.claim_ids),
            "xref_ids": list(self.xref_ids),
            "status": self.status,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload


@dataclass(frozen=True)
class PublicationClaim:
    claim_id: str
    publication_id: str
    statement: str
    claim_kind: str
    scope: str
    status: str
    certainty: str
    source_ids: tuple[str, ...] = ()
    entity_ids: tuple[str, ...] = ()
    related_unit_ids: tuple[str, ...] = ()
    xref_ids: tuple[str, ...] = ()
    last_reviewed_epoch_ms: int = 0

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "publication_id": self.publication_id,
            "statement": self.statement,
            "claim_kind": self.claim_kind,
            "scope": self.scope,
            "status": self.status,
            "certainty": self.certainty,
            "source_ids": list(self.source_ids),
            "entity_ids": list(self.entity_ids),
            "related_unit_ids": list(self.related_unit_ids),
            "xref_ids": list(self.xref_ids),
            "last_reviewed_epoch_ms": self.last_reviewed_epoch_ms,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload


@dataclass(frozen=True)
class PublicationBlock:
    block_id: str
    publication_id: str
    block_kind: str
    title: str
    body: str
    included_block_refs: tuple[str, ...] = ()
    status: str = "active"

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "publication_id": self.publication_id,
            "block_kind": self.block_kind,
            "title": self.title,
            "body": self.body,
            "included_block_refs": list(self.included_block_refs),
            "status": self.status,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PublicationBlock":
        return cls(
            block_id=collapse_ws(str(payload.get("block_id", ""))),
            publication_id=collapse_ws(str(payload.get("publication_id", ""))),
            block_kind=collapse_ws(str(payload.get("block_kind", ""))),
            title=str(payload.get("title", "")),
            body=str(payload.get("body", "")),
            included_block_refs=_ordered_unique_texts(payload.get("included_block_refs", [])),
            status=collapse_ws(str(payload.get("status", "active"))) or "active",
        )


@dataclass(frozen=True)
class PublicationSource:
    source_id: str
    publication_id: str
    title: str
    publisher: str
    source_ref: str
    published_at: str
    retrieved_at_epoch_ms: int
    trust_class: str
    freshness_class: str
    jurisdiction: str
    excerpt: str

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "publication_id": self.publication_id,
            "title": self.title,
            "publisher": self.publisher,
            "source_ref": self.source_ref,
            "published_at": self.published_at,
            "retrieved_at_epoch_ms": self.retrieved_at_epoch_ms,
            "trust_class": self.trust_class,
            "freshness_class": self.freshness_class,
            "jurisdiction": self.jurisdiction,
            "excerpt": self.excerpt,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload


@dataclass(frozen=True)
class PublicationEntity:
    entity_id: str
    publication_id: str
    entity_kind: str
    canonical_name: str
    aliases: tuple[str, ...] = ()
    source_ref: str = ""

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "publication_id": self.publication_id,
            "entity_kind": self.entity_kind,
            "canonical_name": self.canonical_name,
            "aliases": list(self.aliases),
            "source_ref": self.source_ref,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload


@dataclass(frozen=True)
class PublicationCrossReference:
    xref_id: str
    publication_id: str
    from_id: str
    to_id: str
    xref_type: str
    from_kind: str = ""
    to_kind: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "xref_id": self.xref_id,
            "publication_id": self.publication_id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "xref_type": _normalized_publication_xref_type(self.xref_type),
            "from_kind": _normalized_publication_xref_kind(self.from_kind),
            "to_kind": _normalized_publication_xref_kind(self.to_kind),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PublicationCrossReference":
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            xref_id=collapse_ws(str(payload.get("xref_id", ""))),
            publication_id=collapse_ws(str(payload.get("publication_id", ""))),
            from_id=collapse_ws(str(payload.get("from_id", ""))),
            to_id=collapse_ws(str(payload.get("to_id", ""))),
            xref_type=_normalized_publication_xref_type(str(payload.get("xref_type", ""))),
            from_kind=_normalized_publication_xref_kind(str(payload.get("from_kind", ""))),
            to_kind=_normalized_publication_xref_kind(str(payload.get("to_kind", ""))),
            status=collapse_ws(str(payload.get("status", "active"))) or "active",
            metadata={str(key): value for key, value in metadata.items()},
        )


@dataclass(frozen=True)
class PublicationReviewRecord:
    review_id: str
    publication_id: str
    target_kind: str
    target_id: str
    review_state: str
    reviewer: str
    reason: str
    created_at_epoch_ms: int

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "review_id": self.review_id,
            "publication_id": self.publication_id,
            "target_kind": collapse_ws(self.target_kind),
            "target_id": self.target_id,
            "review_state": collapse_ws(self.review_state),
            "reviewer": self.reviewer,
            "reason": self.reason,
            "created_at_epoch_ms": self.created_at_epoch_ms,
        }

    def version_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["version_hash"] = self.version_hash()
        return payload


@dataclass(frozen=True)
class PublicationBuild:
    build_id: str
    publication_id: str
    publication_snapshot_hash: str
    learning_context_snapshot_hash: str
    renderer_id: str
    renderer_version: str
    template_id: str
    template_version: str
    build_status: str
    started_at_epoch_ms: int
    finished_at_epoch_ms: int
    validation_report: dict[str, Any] = field(default_factory=dict)
    render_artifact_ids: tuple[str, ...] = ()
    schema_version: str = PUBLICATION_BUILD_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "build_id": self.build_id,
            "publication_id": self.publication_id,
            "publication_snapshot_hash": self.publication_snapshot_hash,
            "learning_context_snapshot_hash": self.learning_context_snapshot_hash,
            "renderer_id": self.renderer_id,
            "renderer_version": self.renderer_version,
            "template_id": self.template_id,
            "template_version": self.template_version,
            "build_status": self.build_status,
            "started_at_epoch_ms": self.started_at_epoch_ms,
            "finished_at_epoch_ms": self.finished_at_epoch_ms,
            "validation_report": dict(self.validation_report),
            "render_artifact_ids": list(self.render_artifact_ids),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload


@dataclass(frozen=True)
class PublicationComposition:
    composition_id: str
    publication_id: str
    subject_id: str
    publication_type: str
    title: str
    scope_summary: str
    learning_context_snapshot_hash: str
    selected_subject_import_ids: tuple[str, ...] = ()
    included_unit_ids: tuple[str, ...] = ()
    excluded_unit_ids: tuple[str, ...] = ()
    section_ids: tuple[str, ...] = ()
    import_usage_by_id: dict[str, str] = field(default_factory=dict)
    status: str = "draft"
    created_at_epoch_ms: int = 0
    updated_at_epoch_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = PUBLICATION_COMPOSITION_SCHEMA_VERSION

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "composition_id": self.composition_id,
            "publication_id": self.publication_id,
            "subject_id": self.subject_id,
            "publication_type": self.publication_type,
            "title": self.title,
            "scope_summary": self.scope_summary,
            "learning_context_snapshot_hash": self.learning_context_snapshot_hash,
            "selected_subject_import_ids": list(self.selected_subject_import_ids),
            "included_unit_ids": list(self.included_unit_ids),
            "excluded_unit_ids": list(self.excluded_unit_ids),
            "section_ids": list(self.section_ids),
            "import_usage_by_id": dict(self.import_usage_by_id),
            "status": self.status,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "updated_at_epoch_ms": self.updated_at_epoch_ms,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "PublicationComposition":
        import_usage_by_id = payload.get("import_usage_by_id", {})
        if not isinstance(import_usage_by_id, dict):
            import_usage_by_id = {}
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return cls(
            composition_id=collapse_ws(str(payload.get("composition_id", ""))),
            publication_id=collapse_ws(str(payload.get("publication_id", ""))),
            subject_id=collapse_ws(str(payload.get("subject_id", ""))),
            publication_type=collapse_ws(str(payload.get("publication_type", ""))),
            title=collapse_ws(str(payload.get("title", ""))),
            scope_summary=str(payload.get("scope_summary", "")),
            learning_context_snapshot_hash=collapse_ws(str(payload.get("learning_context_snapshot_hash", ""))),
            selected_subject_import_ids=_ordered_unique_texts(payload.get("selected_subject_import_ids", [])),
            included_unit_ids=_ordered_unique_texts(payload.get("included_unit_ids", [])),
            excluded_unit_ids=_ordered_unique_texts(payload.get("excluded_unit_ids", [])),
            section_ids=_ordered_unique_texts(payload.get("section_ids", [])),
            import_usage_by_id={collapse_ws(str(key)): collapse_ws(str(value)) for key, value in import_usage_by_id.items() if collapse_ws(str(key))},
            status=collapse_ws(str(payload.get("status", "draft"))) or "draft",
            created_at_epoch_ms=int(payload.get("created_at_epoch_ms", 0) or 0),
            updated_at_epoch_ms=int(payload.get("updated_at_epoch_ms", 0) or 0),
            metadata={str(key): value for key, value in metadata.items()},
            schema_version=collapse_ws(str(payload.get("schema_version", PUBLICATION_COMPOSITION_SCHEMA_VERSION))) or PUBLICATION_COMPOSITION_SCHEMA_VERSION,
        )


@dataclass(frozen=True)
class RenderArtifact:
    artifact_id: str
    publication_id: str
    build_id: str
    format: str
    path: str
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "publication_id": self.publication_id,
            "build_id": self.build_id,
            "format": self.format,
            "path": self.path,
            "content_hash": self.content_hash,
        }


def publication_claim_ids_for_source(claims: tuple[PublicationClaim, ...], source_id: str) -> tuple[str, ...]:
    normalized_source_id = collapse_ws(source_id)
    return tuple(
        claim.claim_id
        for claim in claims
        if normalized_source_id and normalized_source_id in set(claim.source_ids)
    )


def publication_claim_ids_for_entity(claims: tuple[PublicationClaim, ...], entity_id: str) -> tuple[str, ...]:
    normalized_entity_id = collapse_ws(entity_id)
    return tuple(
        claim.claim_id
        for claim in claims
        if normalized_entity_id and normalized_entity_id in set(claim.entity_ids)
    )


def publication_claim_ids_impacted_by_source_ids(
    claims: tuple[PublicationClaim, ...],
    source_ids: tuple[str, ...] | list[str] | set[str],
) -> tuple[str, ...]:
    normalized_source_ids = {collapse_ws(source_id) for source_id in source_ids if collapse_ws(source_id)}
    if not normalized_source_ids:
        return ()
    return tuple(
        claim.claim_id
        for claim in claims
        if normalized_source_ids.intersection({collapse_ws(source_id) for source_id in claim.source_ids})
    )


def publication_claim_ids_impacted_by_entity_ids(
    claims: tuple[PublicationClaim, ...],
    entity_ids: tuple[str, ...] | list[str] | set[str],
) -> tuple[str, ...]:
    normalized_entity_ids = {collapse_ws(entity_id) for entity_id in entity_ids if collapse_ws(entity_id)}
    if not normalized_entity_ids:
        return ()
    return tuple(
        claim.claim_id
        for claim in claims
        if normalized_entity_ids.intersection({collapse_ws(entity_id) for entity_id in claim.entity_ids})
    )


def publication_claim_ids_impacted_by_unit_ids(
    claims: tuple[PublicationClaim, ...],
    unit_ids: tuple[str, ...] | list[str] | set[str],
) -> tuple[str, ...]:
    normalized_unit_ids = {collapse_ws(unit_id) for unit_id in unit_ids if collapse_ws(unit_id)}
    if not normalized_unit_ids:
        return ()
    return tuple(
        claim.claim_id
        for claim in claims
        if normalized_unit_ids.intersection({collapse_ws(unit_id) for unit_id in claim.related_unit_ids})
    )


def publication_child_sections(
    sections: tuple[PublicationSection, ...],
    parent_section_id: str,
) -> tuple[PublicationSection, ...]:
    normalized_parent_id = collapse_ws(parent_section_id)
    return tuple(
        sorted(
            (
                section
                for section in sections
                if collapse_ws(section.parent_section_id) == normalized_parent_id
            ),
            key=lambda section: (collapse_ws(section.ordinal), collapse_ws(section.title), collapse_ws(section.section_id)),
        )
    )


def publication_xrefs_for_node(
    xrefs: tuple[PublicationCrossReference, ...],
    *,
    node_kind: str,
    node_id: str,
) -> tuple[PublicationCrossReference, ...]:
    normalized_kind = _normalized_publication_xref_kind(node_kind)
    normalized_id = collapse_ws(node_id)
    return tuple(
        xref
        for xref in xrefs
        if normalized_id
        and (
            (xref.from_kind == normalized_kind and collapse_ws(xref.from_id) == normalized_id)
            or (xref.to_kind == normalized_kind and collapse_ws(xref.to_id) == normalized_id)
        )
    )


def publication_reviews_for_target(
    reviews: tuple[PublicationReviewRecord, ...],
    *,
    target_kind: str,
    target_id: str,
) -> tuple[PublicationReviewRecord, ...]:
    normalized_kind = collapse_ws(target_kind)
    normalized_id = collapse_ws(target_id)
    return tuple(
        review
        for review in reviews
        if collapse_ws(review.target_kind) == normalized_kind and collapse_ws(review.target_id) == normalized_id
    )


def _publication_record_diff(
    previous_records: tuple[Any, ...],
    current_records: tuple[Any, ...],
    *,
    id_attr: str,
    version_func: Any,
) -> dict[str, tuple[str, ...]]:
    previous_versions = {
        collapse_ws(str(getattr(record, id_attr, ""))): collapse_ws(str(version_func(record)))
        for record in previous_records
        if collapse_ws(str(getattr(record, id_attr, "")))
    }
    current_versions = {
        collapse_ws(str(getattr(record, id_attr, ""))): collapse_ws(str(version_func(record)))
        for record in current_records
        if collapse_ws(str(getattr(record, id_attr, "")))
    }
    added = tuple(sorted(record_id for record_id in current_versions if record_id not in previous_versions))
    removed = tuple(sorted(record_id for record_id in previous_versions if record_id not in current_versions))
    changed = tuple(
        sorted(
            record_id
            for record_id in current_versions
            if record_id in previous_versions and current_versions[record_id] != previous_versions[record_id]
        )
    )
    unchanged = tuple(
        sorted(
            record_id
            for record_id in current_versions
            if record_id in previous_versions and current_versions[record_id] == previous_versions[record_id]
        )
    )
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def publication_diff_summary(
    *,
    previous_sections: tuple[PublicationSection, ...] = (),
    current_sections: tuple[PublicationSection, ...] = (),
    previous_blocks: tuple[PublicationBlock, ...] = (),
    current_blocks: tuple[PublicationBlock, ...] = (),
    previous_claims: tuple[PublicationClaim, ...] = (),
    current_claims: tuple[PublicationClaim, ...] = (),
    previous_sources: tuple[PublicationSource, ...] = (),
    current_sources: tuple[PublicationSource, ...] = (),
    previous_entities: tuple[PublicationEntity, ...] = (),
    current_entities: tuple[PublicationEntity, ...] = (),
    previous_xrefs: tuple[PublicationCrossReference, ...] = (),
    current_xrefs: tuple[PublicationCrossReference, ...] = (),
    previous_reviews: tuple[PublicationReviewRecord, ...] = (),
    current_reviews: tuple[PublicationReviewRecord, ...] = (),
) -> dict[str, dict[str, tuple[str, ...]]]:
    return {
        "sections": _publication_record_diff(
            previous_sections,
            current_sections,
            id_attr="section_id",
            version_func=lambda section: section.version_hash(),
        ),
        "blocks": _publication_record_diff(
            previous_blocks,
            current_blocks,
            id_attr="block_id",
            version_func=lambda block: block.version_hash(),
        ),
        "claims": _publication_record_diff(
            previous_claims,
            current_claims,
            id_attr="claim_id",
            version_func=lambda claim: claim.version_hash(),
        ),
        "sources": _publication_record_diff(
            previous_sources,
            current_sources,
            id_attr="source_id",
            version_func=lambda source: source.version_hash(),
        ),
        "entities": _publication_record_diff(
            previous_entities,
            current_entities,
            id_attr="entity_id",
            version_func=lambda entity: entity.version_hash(),
        ),
        "xrefs": _publication_record_diff(
            previous_xrefs,
            current_xrefs,
            id_attr="xref_id",
            version_func=lambda xref: xref.version_hash(),
        ),
        "reviews": _publication_record_diff(
            previous_reviews,
            current_reviews,
            id_attr="review_id",
            version_func=lambda review: review.version_hash(),
        ),
    }


def publication_subject_root(root_path: Path, subject_id: str) -> Path:
    return Path(root_path).expanduser().resolve() / "corpus" / collapse_ws(subject_id) / "publications"


def publication_paths(root_path: Path, subject_id: str, publication_id: str) -> dict[str, Path]:
    home = publication_subject_root(root_path, subject_id) / publication_id
    return {
        "root": home,
        "publication": home / "publication.json",
        "compositions": home / "compositions",
        "composition_revisions": home / "composition_revisions",
        "sections": home / "sections",
        "blocks": home / "blocks",
        "claims": home / "claims",
        "sources": home / "sources",
        "entities": home / "entities",
        "xrefs": home / "xrefs",
        "reviews": home / "reviews",
        "builds": home / "builds",
        "outputs": home / "outputs",
    }


def ensure_publication_home(root_path: Path, subject_id: str, publication_id: str) -> dict[str, Path]:
    paths = publication_paths(root_path, subject_id, publication_id)
    for key in ("root", "compositions", "composition_revisions", "sections", "blocks", "claims", "sources", "entities", "xrefs", "reviews", "builds", "outputs"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def persist_publication(
    root_path: Path,
    publication: Publication,
    *,
    sections: tuple[PublicationSection, ...],
    blocks: tuple[PublicationBlock, ...] = (),
    claims: tuple[PublicationClaim, ...],
    sources: tuple[PublicationSource, ...],
    entities: tuple[PublicationEntity, ...] = (),
    xrefs: tuple[PublicationCrossReference, ...] = (),
    reviews: tuple[PublicationReviewRecord, ...] = (),
) -> Path:
    normalized = Publication.from_dict(publication.to_dict())
    paths = ensure_publication_home(root_path, normalized.subject_id, normalized.publication_id)
    _write_json(paths["publication"], normalized.to_dict())
    for section in sections:
        _write_json(paths["sections"] / f"{section.section_id}.json", section.to_dict())
    for block in blocks:
        _write_json(paths["blocks"] / f"{block.block_id}.json", block.to_dict())
    for claim in claims:
        _write_json(paths["claims"] / f"{claim.claim_id}.json", claim.to_dict())
    for source in sources:
        _write_json(paths["sources"] / f"{source.source_id}.json", source.to_dict())
    for entity in entities:
        _write_json(paths["entities"] / f"{entity.entity_id}.json", entity.to_dict())
    for xref in xrefs:
        _write_json(paths["xrefs"] / f"{xref.xref_id}.json", xref.to_dict())
    for review in reviews:
        _write_json(paths["reviews"] / f"{review.review_id}.json", review.to_dict())
    return paths["publication"]


def persist_publication_composition(
    root_path: Path,
    composition: PublicationComposition,
) -> Path:
    normalized = PublicationComposition.from_dict(composition.to_dict())
    paths = ensure_publication_home(root_path, normalized.subject_id, normalized.publication_id)
    target = paths["compositions"] / f"{normalized.composition_id}.json"
    if target.exists():
        try:
            existing_payload = json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            existing_payload = {}
        if isinstance(existing_payload, dict):
            try:
                existing = PublicationComposition.from_dict(existing_payload)
            except Exception:
                existing = None
            if existing is not None and existing.content_hash() != normalized.content_hash():
                revision_stamp = int(existing.updated_at_epoch_ms or existing.created_at_epoch_ms or int(target.stat().st_mtime * 1000))
                revision_target = paths["composition_revisions"] / f"{existing.composition_id}__{revision_stamp}.json"
                _write_json(revision_target, existing.to_dict())
    _write_json(target, normalized.to_dict())
    return target


def list_publication_compositions(
    root_path: Path,
    subject_id: str,
    publication_id: str,
) -> tuple[PublicationComposition, ...]:
    composition_root = publication_paths(root_path, subject_id, publication_id)["compositions"]
    if not composition_root.exists():
        return ()
    records: list[PublicationComposition] = []
    for path in sorted(composition_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        try:
            records.append(PublicationComposition.from_dict(payload))
        except Exception:
            continue
    return tuple(
        sorted(
            records,
            key=lambda item: (
                int(item.updated_at_epoch_ms or 0),
                int(item.created_at_epoch_ms or 0),
                collapse_ws(item.composition_id),
            ),
        )
    )


def list_publication_composition_revisions(
    root_path: Path,
    subject_id: str,
    publication_id: str,
    *,
    composition_id: str = "",
) -> tuple[PublicationComposition, ...]:
    revision_root = publication_paths(root_path, subject_id, publication_id)["composition_revisions"]
    if not revision_root.exists():
        return ()
    target_composition_id = collapse_ws(composition_id)
    records: list[PublicationComposition] = []
    for path in sorted(revision_root.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        try:
            record = PublicationComposition.from_dict(payload)
        except Exception:
            continue
        if target_composition_id and collapse_ws(record.composition_id) != target_composition_id:
            continue
        records.append(record)
    return tuple(
        sorted(
            records,
            key=lambda item: (
                int(item.updated_at_epoch_ms or 0),
                int(item.created_at_epoch_ms or 0),
                collapse_ws(item.composition_id),
            ),
        )
    )


def persist_publication_build(
    root_path: Path,
    subject_id: str,
    publication_id: str,
    build: PublicationBuild,
    *,
    render_artifacts: tuple[RenderArtifact, ...],
    output_texts: dict[str, str],
    output_blobs: dict[str, bytes] | None = None,
) -> Path:
    paths = ensure_publication_home(root_path, subject_id, publication_id)
    output_root = paths["outputs"] / build.build_id
    output_root.mkdir(parents=True, exist_ok=True)
    for filename, text in output_texts.items():
        (output_root / filename).write_text(text, encoding="utf-8")
    for filename, blob in (output_blobs or {}).items():
        (output_root / filename).write_bytes(blob)
    build_payload = build.to_dict()
    build_payload["render_artifacts"] = [artifact.to_dict() for artifact in render_artifacts]
    _write_json(paths["builds"] / f"{build.build_id}.json", build_payload)
    return paths["builds"] / f"{build.build_id}.json"
