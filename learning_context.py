# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from id_generation import make_id, slugify
from learning_context_paths import (
    canonical_learning_subject_id,
    ensure_learning_context_home,
    learning_context_home,
    learning_context_paths,
    learning_corpus_root,
    learning_source_bundle_root,
    resolve_learning_context_root,
)
from semantic_text import collapse_ws


LEARNING_CONTEXT_SCHEMA_VERSION = "learning_context.v1"
LEARNING_DELTA_SCHEMA_VERSION = "learning_delta.v1"
VALID_LEARNING_UNIT_KINDS = {
    "definition",
    "relation",
    "ability",
    "example",
    "counterexample",
    "boundary",
    "misconception",
    "open_question",
    "source_note",
}
VALID_LEARNING_UNIT_STATUSES = {
    "proposed",
    "admitted",
    "deprecated",
    "superseded",
    "rejected",
}
VALID_LEARNING_DELTA_STATUSES = {
    "proposed",
    "admitted",
    "rejected",
    "applied",
}
VALID_LEARNING_DELTA_OPERATION_KINDS = {
    "initiate",
    "append",
    "replace",
    "remove",
    "improve",
    "link",
    "split",
    "merge",
    "reject",
    "restore",
}
VALID_LEARNING_CONTEXT_STATUSES = {
    "draft",
    "active",
    "held",
    "deprecated",
    "archived",
}
VALID_LEARNING_SOURCE_KINDS = {"markdown", "chat", "import", "manual", "url"}
VALID_SUBJECT_IMPORT_KINDS = {
    "definition_support",
    "comparison",
    "method_transfer",
    "example_transfer",
    "counterexample_transfer",
    "background_only",
    "publication_dependency",
    "review_dependency",
}
VALID_SUBJECT_IMPORT_STATUSES = {
    "active",
    "retired",
    "rejected",
}
VALID_SUBJECT_IMPORT_REVIEW_STATUSES = {
    "pending",
    "approved",
    "rejected",
}
LEARNING_DELTA_OPERATION_KIND_ALIASES = {
    "add": "initiate",
    "deprecate": "remove",
    "delete": "remove",
}
LEARNING_UNIT_PATCH_KEYS = {
    "statement",
    "statement_append",
    "aliases_add",
    "provenance_refs_add",
    "linked_artifact_ids_add",
    "linked_skill_ids_add",
    "linked_section_ids_add",
    "structured_fields_merge",
    "metadata_merge",
}
LEARNING_DELTA_OPERATION_ALLOWED_PATCH_KEYS = {
    "append": {
        "statement_append",
        "aliases_add",
        "provenance_refs_add",
        "linked_artifact_ids_add",
        "linked_skill_ids_add",
        "linked_section_ids_add",
        "structured_fields_merge",
        "metadata_merge",
    },
    "improve": set(LEARNING_UNIT_PATCH_KEYS),
    "link": {
        "provenance_refs_add",
        "linked_artifact_ids_add",
        "linked_skill_ids_add",
        "linked_section_ids_add",
        "metadata_merge",
    },
}


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


def _normalized_choice(value: Any, *, allowed: set[str], default: str) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    return text if text in allowed else default


def _stable_json_hash(payload: Any) -> str:
    rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _stable_learning_record_id(prefix: str, *parts: Any) -> str:
    normalized_parts = [collapse_ws(str(part)).lower() for part in parts if collapse_ws(str(part))]
    rendered = "::".join(normalized_parts)
    slug = slugify(normalized_parts[-1] if normalized_parts else prefix, limit=48)
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:10] if rendered else "0" * 10
    return f"{prefix}_{slug}_{digest}"


def _normalized_learning_delta_operation_kind(value: Any) -> str:
    text = collapse_ws(str(value)).lower().replace(" ", "_")
    text = LEARNING_DELTA_OPERATION_KIND_ALIASES.get(text, text)
    if text in VALID_LEARNING_DELTA_OPERATION_KINDS:
        return text
    return "initiate"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def stable_learning_unit_id(*, subject_id: str, unit_kind: str, canonical_title: str) -> str:
    return _stable_learning_record_id("unit", canonical_learning_subject_id(subject_id), unit_kind, canonical_title)


def stable_learning_source_id(*, subject_id: str, title: str, source_ref: str = "") -> str:
    return _stable_learning_record_id("source", canonical_learning_subject_id(subject_id), title, source_ref)


def stable_subject_import_id(
    *,
    active_subject_id: str,
    active_subject_version_id: str,
    source_subject_id: str,
    source_subject_version_id: str,
    import_kind: str,
    imported_unit_ids: tuple[str, ...] = (),
    imported_skill_ids: tuple[str, ...] = (),
    imported_source_ids: tuple[str, ...] = (),
    imported_claim_ids: tuple[str, ...] = (),
    imported_section_ids: tuple[str, ...] = (),
) -> str:
    return _stable_learning_record_id(
        "subject_import",
        canonical_learning_subject_id(active_subject_id),
        collapse_ws(active_subject_version_id),
        canonical_learning_subject_id(source_subject_id),
        collapse_ws(source_subject_version_id),
        collapse_ws(import_kind),
        *imported_unit_ids,
        *imported_skill_ids,
        *imported_source_ids,
        *imported_claim_ids,
        *imported_section_ids,
    )


@dataclass(frozen=True)
class LearningUnit:
    unit_id: str
    subject_id: str = ""
    unit_kind: str = "definition"
    canonical_title: str = ""
    aliases: tuple[str, ...] = ()
    statement: str = ""
    structured_fields: dict[str, Any] = field(default_factory=dict)
    provenance_refs: tuple[str, ...] = ()
    status: str = "proposed"
    linked_artifact_ids: tuple[str, ...] = ()
    linked_skill_ids: tuple[str, ...] = ()
    linked_section_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "subject_id": self.subject_id,
            "unit_kind": self.unit_kind,
            "canonical_title": self.canonical_title,
            "aliases": list(self.aliases),
            "statement": self.statement,
            "structured_fields": dict(self.structured_fields),
            "provenance_refs": list(self.provenance_refs),
            "status": self.status,
            "linked_artifact_ids": list(self.linked_artifact_ids),
            "linked_skill_ids": list(self.linked_skill_ids),
            "linked_section_ids": list(self.linked_section_ids),
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningUnit":
        return cls(
            unit_id=collapse_ws(str(payload.get("unit_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            unit_kind=_normalized_choice(
                payload.get("unit_kind", "definition"),
                allowed=VALID_LEARNING_UNIT_KINDS,
                default="definition",
            ),
            canonical_title=collapse_ws(str(payload.get("canonical_title", ""))),
            aliases=_ordered_unique_texts(payload.get("aliases", [])),
            statement=str(payload.get("statement", "")),
            structured_fields=dict(payload.get("structured_fields", {})),
            provenance_refs=_ordered_unique_texts(payload.get("provenance_refs", [])),
            status=_normalized_choice(
                payload.get("status", "proposed"),
                allowed=VALID_LEARNING_UNIT_STATUSES,
                default="proposed",
            ),
            linked_artifact_ids=_ordered_unique_texts(payload.get("linked_artifact_ids", [])),
            linked_skill_ids=_ordered_unique_texts(payload.get("linked_skill_ids", [])),
            linked_section_ids=_ordered_unique_texts(payload.get("linked_section_ids", [])),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class LearningDeltaOperation:
    operation_id: str
    operation_kind: str = "initiate"
    target_unit_ids: tuple[str, ...] = ()
    proposed_unit_ids: tuple[str, ...] = ()
    rationale: str = ""
    evidence_refs: tuple[str, ...] = ()
    patch: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_kind": self.operation_kind,
            "target_unit_ids": list(self.target_unit_ids),
            "proposed_unit_ids": list(self.proposed_unit_ids),
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "patch": dict(self.patch),
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningDeltaOperation":
        proposed_unit_ids = payload.get("proposed_unit_ids", ())
        if not proposed_unit_ids and "replacement_unit_ids" in payload:
            proposed_unit_ids = payload.get("replacement_unit_ids", ())
        return cls(
            operation_id=collapse_ws(str(payload.get("operation_id", ""))),
            operation_kind=_normalized_learning_delta_operation_kind(payload.get("operation_kind", "initiate")),
            target_unit_ids=_ordered_unique_texts(payload.get("target_unit_ids", [])),
            proposed_unit_ids=_ordered_unique_texts(proposed_unit_ids),
            rationale=str(payload.get("rationale", "")),
            evidence_refs=_ordered_unique_texts(payload.get("evidence_refs", [])),
            patch=dict(payload.get("patch", {})),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class LearningDelta:
    delta_id: str
    subject_id: str
    source_kind: str = ""
    rationale: str = ""
    evidence_refs: tuple[str, ...] = ()
    proposed_units: tuple[LearningUnit, ...] = ()
    deprecated_unit_ids: tuple[str, ...] = ()
    operations: tuple[LearningDeltaOperation, ...] = ()
    derived_skill_ids: tuple[str, ...] = ()
    document_section_ids: tuple[str, ...] = ()
    status: str = "proposed"
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": LEARNING_DELTA_SCHEMA_VERSION,
            "delta_id": self.delta_id,
            "subject_id": self.subject_id,
            "source_kind": self.source_kind,
            "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "proposed_units": [unit.to_dict() for unit in self.proposed_units],
            "deprecated_unit_ids": list(self.deprecated_unit_ids),
            "operations": [operation.to_dict() for operation in self.operations],
            "derived_skill_ids": list(self.derived_skill_ids),
            "document_section_ids": list(self.document_section_ids),
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningDelta":
        subject_id = canonical_learning_subject_id(str(payload.get("subject_id", "")))
        units = []
        for item in payload.get("proposed_units", []):
            if not isinstance(item, dict):
                continue
            unit = LearningUnit.from_dict(item)
            if not unit.subject_id:
                unit = LearningUnit(
                    unit_id=unit.unit_id,
                    subject_id=subject_id,
                    unit_kind=unit.unit_kind,
                    canonical_title=unit.canonical_title,
                    aliases=unit.aliases,
                    statement=unit.statement,
                    structured_fields=unit.structured_fields,
                    provenance_refs=unit.provenance_refs,
                    status=unit.status,
                    linked_artifact_ids=unit.linked_artifact_ids,
                    linked_skill_ids=unit.linked_skill_ids,
                    linked_section_ids=unit.linked_section_ids,
                    metadata=unit.metadata,
                )
            units.append(unit)
        operations = []
        for item in payload.get("operations", []):
            if not isinstance(item, dict):
                continue
            operations.append(LearningDeltaOperation.from_dict(item))
        return cls(
            delta_id=collapse_ws(str(payload.get("delta_id", ""))),
            subject_id=subject_id,
            source_kind=collapse_ws(str(payload.get("source_kind", ""))),
            rationale=str(payload.get("rationale", "")),
            evidence_refs=_ordered_unique_texts(payload.get("evidence_refs", [])),
            proposed_units=tuple(units),
            deprecated_unit_ids=_ordered_unique_texts(payload.get("deprecated_unit_ids", [])),
            operations=tuple(operations),
            derived_skill_ids=_ordered_unique_texts(payload.get("derived_skill_ids", [])),
            document_section_ids=_ordered_unique_texts(payload.get("document_section_ids", [])),
            status=_normalized_choice(
                payload.get("status", "proposed"),
                allowed=VALID_LEARNING_DELTA_STATUSES,
                default="proposed",
            ),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class LearningSource:
    source_id: str
    subject_id: str
    source_kind: str = "markdown"
    title: str = ""
    source_ref: str = ""
    media_type: str = "text/markdown"
    section_count: int = 0
    body_relpath: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "subject_id": self.subject_id,
            "source_kind": self.source_kind,
            "title": self.title,
            "source_ref": self.source_ref,
            "media_type": self.media_type,
            "section_count": self.section_count,
            "body_relpath": self.body_relpath,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningSource":
        try:
            section_count = max(0, int(payload.get("section_count", 0)))
        except Exception:
            section_count = 0
        return cls(
            source_id=collapse_ws(str(payload.get("source_id", ""))),
            subject_id=canonical_learning_subject_id(str(payload.get("subject_id", ""))),
            source_kind=_normalized_choice(
                payload.get("source_kind", "markdown"),
                allowed=VALID_LEARNING_SOURCE_KINDS,
                default="markdown",
            ),
            title=collapse_ws(str(payload.get("title", ""))),
            source_ref=str(payload.get("source_ref", "")),
            media_type=collapse_ws(str(payload.get("media_type", ""))) or "text/markdown",
            section_count=section_count,
            body_relpath=str(payload.get("body_relpath", "")),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class SubjectImport:
    import_id: str
    active_subject_id: str
    active_subject_version_id: str = ""
    active_subject_title: str = ""
    source_subject_id: str = ""
    source_subject_version_id: str = ""
    source_subject_title: str = ""
    import_kind: str = "background_only"
    imported_unit_ids: tuple[str, ...] = ()
    imported_skill_ids: tuple[str, ...] = ()
    imported_source_ids: tuple[str, ...] = ()
    imported_claim_ids: tuple[str, ...] = ()
    imported_section_ids: tuple[str, ...] = ()
    rationale: str = ""
    created_at_epoch_ms: int = 0
    review_status: str = "approved"
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "active_subject_id": self.active_subject_id,
            "active_subject_version_id": self.active_subject_version_id,
            "active_subject_title": self.active_subject_title,
            "source_subject_id": self.source_subject_id,
            "source_subject_version_id": self.source_subject_version_id,
            "source_subject_title": self.source_subject_title,
            "import_kind": self.import_kind,
            "imported_unit_ids": list(self.imported_unit_ids),
            "imported_skill_ids": list(self.imported_skill_ids),
            "imported_source_ids": list(self.imported_source_ids),
            "imported_claim_ids": list(self.imported_claim_ids),
            "imported_section_ids": list(self.imported_section_ids),
            "rationale": self.rationale,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "review_status": self.review_status,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SubjectImport":
        created_at_epoch_ms = 0
        try:
            created_at_epoch_ms = max(0, int(payload.get("created_at_epoch_ms", 0) or 0))
        except Exception:
            created_at_epoch_ms = 0
        active_subject_id = canonical_learning_subject_id(str(payload.get("active_subject_id", "")))
        source_subject_id = canonical_learning_subject_id(str(payload.get("source_subject_id", "")))
        imported_unit_ids = _ordered_unique_texts(payload.get("imported_unit_ids", []))
        imported_skill_ids = _ordered_unique_texts(payload.get("imported_skill_ids", []))
        imported_source_ids = _ordered_unique_texts(payload.get("imported_source_ids", []))
        imported_claim_ids = _ordered_unique_texts(payload.get("imported_claim_ids", []))
        imported_section_ids = _ordered_unique_texts(payload.get("imported_section_ids", []))
        import_kind = _normalized_choice(
            payload.get("import_kind", "background_only"),
            allowed=VALID_SUBJECT_IMPORT_KINDS,
            default="background_only",
        )
        import_id = collapse_ws(str(payload.get("import_id", "")))
        if not import_id:
            import_id = stable_subject_import_id(
                active_subject_id=active_subject_id,
                active_subject_version_id=collapse_ws(str(payload.get("active_subject_version_id", ""))),
                source_subject_id=source_subject_id,
                source_subject_version_id=collapse_ws(str(payload.get("source_subject_version_id", ""))),
                import_kind=import_kind,
                imported_unit_ids=imported_unit_ids,
                imported_skill_ids=imported_skill_ids,
                imported_source_ids=imported_source_ids,
                imported_claim_ids=imported_claim_ids,
                imported_section_ids=imported_section_ids,
            )
        return cls(
            import_id=import_id,
            active_subject_id=active_subject_id,
            active_subject_version_id=collapse_ws(str(payload.get("active_subject_version_id", ""))),
            active_subject_title=collapse_ws(str(payload.get("active_subject_title", ""))),
            source_subject_id=source_subject_id,
            source_subject_version_id=collapse_ws(str(payload.get("source_subject_version_id", ""))),
            source_subject_title=collapse_ws(str(payload.get("source_subject_title", ""))),
            import_kind=import_kind,
            imported_unit_ids=imported_unit_ids,
            imported_skill_ids=imported_skill_ids,
            imported_source_ids=imported_source_ids,
            imported_claim_ids=imported_claim_ids,
            imported_section_ids=imported_section_ids,
            rationale=str(payload.get("rationale", "")),
            created_at_epoch_ms=created_at_epoch_ms,
            review_status=_normalized_choice(
                payload.get("review_status", "approved"),
                allowed=VALID_SUBJECT_IMPORT_REVIEW_STATUSES,
                default="approved",
            ),
            status=_normalized_choice(
                payload.get("status", "active"),
                allowed=VALID_SUBJECT_IMPORT_STATUSES,
                default="active",
            ),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class SubjectReasoningScope:
    active_subject_id: str
    active_subject_version_id: str
    active_subject_title: str
    imported_subjects: tuple[SubjectImport, ...] = ()
    global_retrieval_policy: str = "disabled"

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_subject_id": self.active_subject_id,
            "active_subject_version_id": self.active_subject_version_id,
            "active_subject_title": self.active_subject_title,
            "imported_subjects": [item.to_dict() for item in self.imported_subjects],
            "global_retrieval_policy": self.global_retrieval_policy,
        }


@dataclass(frozen=True)
class LearningContext:
    subject_id: str
    canonical_title: str
    aliases: tuple[str, ...] = ()
    subject_family: str = ""
    summary: str = ""
    units: tuple[LearningUnit, ...] = ()
    linked_source_ids: tuple[str, ...] = ()
    linked_skill_ids: tuple[str, ...] = ()
    linked_document_section_ids: tuple[str, ...] = ()
    applied_delta_ids: tuple[str, ...] = ()
    governance_status: str = "draft"
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "schema_version": LEARNING_CONTEXT_SCHEMA_VERSION,
            "subject_id": self.subject_id,
            "canonical_title": self.canonical_title,
            "aliases": list(self.aliases),
            "subject_family": self.subject_family,
            "summary": self.summary,
            "units": [unit.to_dict() for unit in self.units],
            "linked_source_ids": list(self.linked_source_ids),
            "linked_skill_ids": list(self.linked_skill_ids),
            "linked_document_section_ids": list(self.linked_document_section_ids),
            "applied_delta_ids": list(self.applied_delta_ids),
            "governance_status": self.governance_status,
            "metadata": dict(self.metadata),
        }

    def content_hash(self) -> str:
        return _stable_json_hash(self.snapshot_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.snapshot_payload()
        payload["content_hash"] = self.content_hash()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearningContext":
        subject_id = canonical_learning_subject_id(str(payload.get("subject_id", "")))
        units = []
        for item in payload.get("units", []):
            if not isinstance(item, dict):
                continue
            unit = LearningUnit.from_dict(item)
            if not unit.subject_id:
                unit = LearningUnit(
                    unit_id=unit.unit_id,
                    subject_id=subject_id,
                    unit_kind=unit.unit_kind,
                    canonical_title=unit.canonical_title,
                    aliases=unit.aliases,
                    statement=unit.statement,
                    structured_fields=unit.structured_fields,
                    provenance_refs=unit.provenance_refs,
                    status=unit.status,
                    linked_artifact_ids=unit.linked_artifact_ids,
                    linked_skill_ids=unit.linked_skill_ids,
                    linked_section_ids=unit.linked_section_ids,
                    metadata=unit.metadata,
                )
            units.append(unit)
        return cls(
            subject_id=subject_id,
            canonical_title=collapse_ws(str(payload.get("canonical_title", ""))),
            aliases=_ordered_unique_texts(payload.get("aliases", [])),
            subject_family=collapse_ws(str(payload.get("subject_family", ""))),
            summary=str(payload.get("summary", "")),
            units=tuple(units),
            linked_source_ids=_ordered_unique_texts(payload.get("linked_source_ids", [])),
            linked_skill_ids=_ordered_unique_texts(payload.get("linked_skill_ids", [])),
            linked_document_section_ids=_ordered_unique_texts(payload.get("linked_document_section_ids", [])),
            applied_delta_ids=_ordered_unique_texts(payload.get("applied_delta_ids", [])),
            governance_status=_normalized_choice(
                payload.get("governance_status", "draft"),
                allowed=VALID_LEARNING_CONTEXT_STATUSES,
                default="draft",
            ),
            metadata=dict(payload.get("metadata", {})),
        )


def new_learning_context(*, canonical_title: str, subject_id: str = "", subject_family: str = "") -> LearningContext:
    normalized_title = collapse_ws(canonical_title)
    normalized_subject_id = canonical_learning_subject_id(subject_id or normalized_title)
    return LearningContext(
        subject_id=normalized_subject_id,
        canonical_title=normalized_title,
        aliases=(normalized_title,) if normalized_title else (),
        subject_family=collapse_ws(subject_family),
        governance_status="draft",
    )


def new_learning_delta(*, subject_id: str, source_kind: str = "", rationale: str = "") -> LearningDelta:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    return LearningDelta(
        delta_id=make_id("delta", normalized_subject_id),
        subject_id=normalized_subject_id,
        source_kind=collapse_ws(source_kind),
        rationale=str(rationale or ""),
    )


def new_learning_source(
    *,
    subject_id: str,
    title: str,
    source_ref: str = "",
    source_kind: str = "markdown",
    media_type: str = "text/markdown",
    section_count: int = 0,
    body_relpath: str = "",
    metadata: dict[str, Any] | None = None,
) -> LearningSource:
    normalized_subject_id = canonical_learning_subject_id(subject_id)
    return LearningSource(
        source_id=stable_learning_source_id(
            subject_id=normalized_subject_id,
            title=title or normalized_subject_id,
            source_ref=source_ref,
        ),
        subject_id=normalized_subject_id,
        source_kind=_normalized_choice(source_kind, allowed=VALID_LEARNING_SOURCE_KINDS, default="markdown"),
        title=collapse_ws(title),
        source_ref=str(source_ref or ""),
        media_type=collapse_ws(media_type) or "text/markdown",
        section_count=max(0, int(section_count or 0)),
        body_relpath=str(body_relpath or ""),
        metadata=dict(metadata or {}),
    )


def new_subject_import(
    *,
    active_subject_id: str,
    active_subject_version_id: str,
    source_subject_id: str,
    source_subject_version_id: str,
    import_kind: str = "background_only",
    active_subject_title: str = "",
    source_subject_title: str = "",
    imported_unit_ids: tuple[str, ...] = (),
    imported_skill_ids: tuple[str, ...] = (),
    imported_source_ids: tuple[str, ...] = (),
    imported_claim_ids: tuple[str, ...] = (),
    imported_section_ids: tuple[str, ...] = (),
    rationale: str = "",
    created_at_epoch_ms: int | None = None,
    review_status: str = "approved",
    status: str = "active",
    metadata: dict[str, Any] | None = None,
) -> SubjectImport:
    normalized_active_subject_id = canonical_learning_subject_id(active_subject_id)
    normalized_source_subject_id = canonical_learning_subject_id(source_subject_id)
    normalized_import_kind = _normalized_choice(
        import_kind,
        allowed=VALID_SUBJECT_IMPORT_KINDS,
        default="background_only",
    )
    normalized_unit_ids = _ordered_unique_texts(imported_unit_ids)
    normalized_skill_ids = _ordered_unique_texts(imported_skill_ids)
    normalized_source_ids = _ordered_unique_texts(imported_source_ids)
    normalized_claim_ids = _ordered_unique_texts(imported_claim_ids)
    normalized_section_ids = _ordered_unique_texts(imported_section_ids)
    normalized_created_at_epoch_ms = (
        max(0, int(created_at_epoch_ms))
        if created_at_epoch_ms is not None
        else int(time.time() * 1000)
    )
    return SubjectImport(
        import_id=stable_subject_import_id(
            active_subject_id=normalized_active_subject_id,
            active_subject_version_id=collapse_ws(active_subject_version_id),
            source_subject_id=normalized_source_subject_id,
            source_subject_version_id=collapse_ws(source_subject_version_id),
            import_kind=normalized_import_kind,
            imported_unit_ids=normalized_unit_ids,
            imported_skill_ids=normalized_skill_ids,
            imported_source_ids=normalized_source_ids,
            imported_claim_ids=normalized_claim_ids,
            imported_section_ids=normalized_section_ids,
        ),
        active_subject_id=normalized_active_subject_id,
        active_subject_version_id=collapse_ws(active_subject_version_id),
        active_subject_title=collapse_ws(active_subject_title),
        source_subject_id=normalized_source_subject_id,
        source_subject_version_id=collapse_ws(source_subject_version_id),
        source_subject_title=collapse_ws(source_subject_title),
        import_kind=normalized_import_kind,
        imported_unit_ids=normalized_unit_ids,
        imported_skill_ids=normalized_skill_ids,
        imported_source_ids=normalized_source_ids,
        imported_claim_ids=normalized_claim_ids,
        imported_section_ids=normalized_section_ids,
        rationale=str(rationale or ""),
        created_at_epoch_ms=normalized_created_at_epoch_ms,
        review_status=_normalized_choice(
            review_status,
            allowed=VALID_SUBJECT_IMPORT_REVIEW_STATUSES,
            default="approved",
        ),
        status=_normalized_choice(
            status,
            allowed=VALID_SUBJECT_IMPORT_STATUSES,
            default="active",
        ),
        metadata=dict(metadata or {}),
    )


def _aliases_index_payload(context: LearningContext) -> dict[str, Any]:
    lookup_keys = _ordered_unique_texts(
        list(context.aliases)
        + [context.canonical_title, context.subject_id, context.subject_family]
    )
    return {
        "subject_id": context.subject_id,
        "canonical_title": context.canonical_title,
        "aliases": list(context.aliases),
        "lookup_keys": list(lookup_keys),
        "content_hash": context.content_hash(),
    }


def _units_index_payload(context: LearningContext) -> dict[str, Any]:
    return {
        "subject_id": context.subject_id,
        "units": [
            {
                "unit_id": unit.unit_id,
                "unit_kind": unit.unit_kind,
                "canonical_title": unit.canonical_title,
                "aliases": list(unit.aliases),
                "status": unit.status,
                "linked_skill_ids": list(unit.linked_skill_ids),
                "linked_artifact_ids": list(unit.linked_artifact_ids),
            }
            for unit in context.units
        ],
        "content_hash": context.content_hash(),
    }


def _subject_import_slice_counts(subject_import: SubjectImport) -> dict[str, int]:
    return {
        "unit_count": len(subject_import.imported_unit_ids),
        "skill_count": len(subject_import.imported_skill_ids),
        "source_count": len(subject_import.imported_source_ids),
        "claim_count": len(subject_import.imported_claim_ids),
        "section_count": len(subject_import.imported_section_ids),
    }


def _subject_imports_index_payload(subject_id: str, subject_imports: tuple[SubjectImport, ...]) -> dict[str, Any]:
    active_imports = tuple(
        item
        for item in subject_imports
        if item.status == "active" and item.review_status == "approved"
    )
    imported_subject_ids = sorted({item.source_subject_id for item in active_imports if collapse_ws(item.source_subject_id)})
    imports_payload = [
        {
            "import_id": item.import_id,
            "source_subject_id": item.source_subject_id,
            "source_subject_title": item.source_subject_title,
            "source_subject_version_id": item.source_subject_version_id,
            "import_kind": item.import_kind,
            "review_status": item.review_status,
            "status": item.status,
            "created_at_epoch_ms": item.created_at_epoch_ms,
            **_subject_import_slice_counts(item),
        }
        for item in subject_imports
    ]
    return {
        "subject_id": subject_id,
        "import_count": len(subject_imports),
        "active_import_count": len(active_imports),
        "imported_subject_count": len(imported_subject_ids),
        "imports": imports_payload,
        "content_hash": _stable_json_hash(imports_payload),
    }


def persist_learning_context(root_path: Path, context: LearningContext) -> Path:
    from learning_context_projection import (
        render_learning_context_subject_markdown,
        render_learning_context_subject_typ,
    )
    from learning_context_skill_projection import materialize_learning_context_skill_projections

    normalized = LearningContext.from_dict(context.to_dict())
    paths = ensure_learning_context_home(root_path, normalized.subject_id)
    _write_json(paths["context"], normalized.to_dict())
    _write_json(paths["aliases_index"], _aliases_index_payload(normalized))
    _write_json(paths["units_index"], _units_index_payload(normalized))
    _write_json(
        paths["imports_index"],
        _subject_imports_index_payload(
            normalized.subject_id,
            list_subject_imports(root_path, normalized.subject_id),
        ),
    )
    paths["subject_typ"].write_text(render_learning_context_subject_typ(normalized), encoding="utf-8")
    paths["subject_md"].write_text(render_learning_context_subject_markdown(normalized), encoding="utf-8")
    materialize_learning_context_skill_projections(root_path, normalized)
    return paths["context"]


def load_learning_context(root_path: Path, subject_id: str) -> LearningContext:
    path = learning_context_paths(root_path, subject_id)["context"]
    return LearningContext.from_dict(json.loads(path.read_text(encoding="utf-8")))


def persist_subject_import(root_path: Path, subject_import: SubjectImport) -> Path:
    normalized = SubjectImport.from_dict(subject_import.to_dict())
    paths = ensure_learning_context_home(root_path, normalized.active_subject_id)
    target = paths["imports"] / f"{normalized.import_id}.json"
    _write_json(target, normalized.to_dict())
    _write_json(
        paths["imports_index"],
        _subject_imports_index_payload(
            normalized.active_subject_id,
            list_subject_imports(root_path, normalized.active_subject_id),
        ),
    )
    return target


def load_subject_import(root_path: Path, active_subject_id: str, import_id: str) -> SubjectImport:
    path = learning_context_paths(root_path, active_subject_id)["imports"] / f"{collapse_ws(import_id)}.json"
    return SubjectImport.from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_subject_imports(root_path: Path, active_subject_id: str) -> tuple[SubjectImport, ...]:
    imports_root = learning_context_paths(root_path, active_subject_id)["imports"]
    if not imports_root.exists():
        return ()
    subject_imports: list[SubjectImport] = []
    for path in sorted(imports_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        subject_imports.append(SubjectImport.from_dict(payload))
    return tuple(
        sorted(
            subject_imports,
            key=lambda item: (
                item.created_at_epoch_ms,
                item.source_subject_title.casefold(),
                item.source_subject_id,
                item.import_id,
            ),
        )
    )


def load_subject_reasoning_scope(
    root_path: Path,
    subject_id: str,
    *,
    global_retrieval_policy: str = "disabled",
) -> SubjectReasoningScope:
    context = load_learning_context(root_path, subject_id)
    subject_imports = tuple(
        item
        for item in list_subject_imports(root_path, context.subject_id)
        if item.status == "active" and item.review_status == "approved"
    )
    return SubjectReasoningScope(
        active_subject_id=context.subject_id,
        active_subject_version_id=context.content_hash(),
        active_subject_title=context.canonical_title,
        imported_subjects=subject_imports,
        global_retrieval_policy=collapse_ws(global_retrieval_policy) or "disabled",
    )


def persist_learning_delta(root_path: Path, delta: LearningDelta) -> Path:
    normalized = LearningDelta.from_dict(delta.to_dict())
    paths = ensure_learning_context_home(root_path, normalized.subject_id)
    target = paths["deltas"] / f"{normalized.delta_id}.json"
    _write_json(target, normalized.to_dict())
    return target


def persist_learning_source(root_path: Path, source: LearningSource, *, source_text: str = "") -> Path:
    normalized = LearningSource.from_dict(source.to_dict())
    paths = ensure_learning_context_home(root_path, normalized.subject_id)
    body_relpath = normalized.body_relpath or f"{normalized.source_id}.md"
    normalized = LearningSource(
        source_id=normalized.source_id,
        subject_id=normalized.subject_id,
        source_kind=normalized.source_kind,
        title=normalized.title,
        source_ref=normalized.source_ref,
        media_type=normalized.media_type,
        section_count=normalized.section_count,
        body_relpath=body_relpath,
        metadata=normalized.metadata,
    )
    target = paths["sources"] / f"{normalized.source_id}.json"
    _write_json(target, normalized.to_dict())
    if source_text:
        body_path = paths["sources"] / body_relpath
        body_path.parent.mkdir(parents=True, exist_ok=True)
        body_path.write_text(str(source_text), encoding="utf-8")
    return target


def persist_learning_source_bundle_files(
    root_path: Path,
    *,
    subject_id: str,
    source_id: str,
    bundle_files: Mapping[str, Any],
) -> tuple[Path, ...]:
    bundle_root = learning_source_bundle_root(root_path, subject_id, source_id)
    bundle_root.mkdir(parents=True, exist_ok=True)
    persisted: list[Path] = []
    for raw_relpath, raw_content in bundle_files.items():
        relpath_text = str(raw_relpath or "").strip()
        if not relpath_text:
            continue
        relpath = Path(relpath_text)
        if relpath.is_absolute() or ".." in relpath.parts:
            raise ValueError(f"Bundle file path must be relative: {relpath_text}")
        target = bundle_root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(raw_content, bytes):
            target.write_bytes(raw_content)
        else:
            target.write_text(str(raw_content), encoding="utf-8")
        persisted.append(target)
    return tuple(persisted)


def load_learning_source(root_path: Path, subject_id: str, source_id: str) -> LearningSource:
    path = learning_context_paths(root_path, subject_id)["sources"] / f"{collapse_ws(source_id)}.json"
    return LearningSource.from_dict(json.loads(path.read_text(encoding="utf-8")))


def load_learning_delta(root_path: Path, subject_id: str, delta_id: str) -> LearningDelta:
    path = learning_context_paths(root_path, subject_id)["deltas"] / f"{collapse_ws(delta_id)}.json"
    return LearningDelta.from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_learning_contexts(root_path: Path) -> tuple[dict[str, Any], ...]:
    corpus_root = learning_corpus_root(root_path)
    if not corpus_root.exists():
        return ()
    summaries: list[dict[str, Any]] = []
    for child in sorted(corpus_root.iterdir()):
        context_path = child / "context.json"
        if not context_path.is_file():
            continue
        context = load_learning_context(root_path, child.name)
        subject_imports = list_subject_imports(root_path, context.subject_id)
        active_subject_imports = [
            item
            for item in subject_imports
            if item.status == "active" and item.review_status == "approved"
        ]
        summaries.append(
            {
                "subject_id": context.subject_id,
                "canonical_title": context.canonical_title,
                "subject_family": context.subject_family,
                "governance_status": context.governance_status,
                "unit_count": len(context.units),
                "applied_delta_count": len(context.applied_delta_ids),
                "subject_import_count": len(subject_imports),
                "active_subject_import_count": len(active_subject_imports),
            }
        )
    return tuple(summaries)


def learning_context_lookup_keys(context: LearningContext) -> tuple[str, ...]:
    return _ordered_unique_texts(
        canonical_learning_subject_id(item)
        for item in (
            context.subject_id,
            context.canonical_title,
            *context.aliases,
        )
        if collapse_ws(str(item))
    )


def find_learning_context_by_lookup(root_path: Path, *candidates: str) -> LearningContext | None:
    normalized_candidates = _ordered_unique_texts(
        canonical_learning_subject_id(item)
        for item in candidates
        if collapse_ws(str(item))
    )
    if not normalized_candidates:
        return None
    matches: list[LearningContext] = []
    for summary in list_learning_contexts(root_path):
        subject_id = collapse_ws(str(summary.get("subject_id", "")))
        if not subject_id:
            continue
        context = load_learning_context(root_path, subject_id)
        if set(learning_context_lookup_keys(context)).intersection(normalized_candidates):
            matches.append(context)
    if len(matches) != 1:
        return None
    return matches[0]


def _normalized_learning_unit_for_subject(unit: LearningUnit, subject_id: str) -> LearningUnit:
    if unit.subject_id == subject_id:
        return unit
    return replace(unit, subject_id=subject_id)


def _learning_delta_proposed_unit_pool(delta: LearningDelta, subject_id: str) -> dict[str, LearningUnit]:
    return {
        unit.unit_id: _normalized_learning_unit_for_subject(unit, subject_id)
        for unit in delta.proposed_units
    }


def _unit_with_added_provenance(unit: LearningUnit, evidence_refs: tuple[str, ...] = ()) -> LearningUnit:
    if not evidence_refs:
        return unit
    return replace(
        unit,
        provenance_refs=_ordered_unique_texts(list(unit.provenance_refs) + list(evidence_refs)),
    )


def _unit_with_status(unit: LearningUnit, status: str, *, evidence_refs: tuple[str, ...] = ()) -> LearningUnit:
    normalized_status = _normalized_choice(
        status,
        allowed=VALID_LEARNING_UNIT_STATUSES,
        default=unit.status,
    )
    return replace(_unit_with_added_provenance(unit, evidence_refs), status=normalized_status)


def _patch_values_as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _validated_operation_patch(operation: LearningDeltaOperation) -> dict[str, Any]:
    patch = dict(operation.patch)
    allowed_keys = LEARNING_DELTA_OPERATION_ALLOWED_PATCH_KEYS.get(operation.operation_kind)
    if allowed_keys is None:
        if patch:
            raise ValueError(f"LearningDelta operation {operation.operation_id} does not accept patch data.")
        return {}
    unknown_keys = sorted(set(patch) - allowed_keys)
    if unknown_keys:
        raise ValueError(
            f"LearningDelta operation {operation.operation_id} has unsupported patch keys: {', '.join(unknown_keys)}"
        )
    return patch


def _unit_with_patch(
    unit: LearningUnit,
    patch: dict[str, Any],
    *,
    evidence_refs: tuple[str, ...] = (),
) -> LearningUnit:
    updated = unit
    if "statement" in patch:
        updated = replace(updated, statement=str(patch.get("statement", "")))
    if "statement_append" in patch:
        appended = str(patch.get("statement_append", "")).strip()
        if appended:
            statement = updated.statement.rstrip()
            updated = replace(
                updated,
                statement=f"{statement}\n\n{appended}" if statement else appended,
            )
    if "aliases_add" in patch:
        updated = replace(
            updated,
            aliases=_ordered_unique_texts(list(updated.aliases) + _patch_values_as_list(patch.get("aliases_add"))),
        )
    if "provenance_refs_add" in patch:
        updated = replace(
            updated,
            provenance_refs=_ordered_unique_texts(
                list(updated.provenance_refs) + _patch_values_as_list(patch.get("provenance_refs_add"))
            ),
        )
    if "linked_artifact_ids_add" in patch:
        updated = replace(
            updated,
            linked_artifact_ids=_ordered_unique_texts(
                list(updated.linked_artifact_ids) + _patch_values_as_list(patch.get("linked_artifact_ids_add"))
            ),
        )
    if "linked_skill_ids_add" in patch:
        updated = replace(
            updated,
            linked_skill_ids=_ordered_unique_texts(
                list(updated.linked_skill_ids) + _patch_values_as_list(patch.get("linked_skill_ids_add"))
            ),
        )
    if "linked_section_ids_add" in patch:
        updated = replace(
            updated,
            linked_section_ids=_ordered_unique_texts(
                list(updated.linked_section_ids) + _patch_values_as_list(patch.get("linked_section_ids_add"))
            ),
        )
    if "structured_fields_merge" in patch:
        updated = replace(
            updated,
            structured_fields={
                **updated.structured_fields,
                **dict(patch.get("structured_fields_merge", {})),
            },
        )
    if "metadata_merge" in patch:
        updated = replace(
            updated,
            metadata={
                **updated.metadata,
                **dict(patch.get("metadata_merge", {})),
            },
        )
    return _unit_with_added_provenance(updated, evidence_refs)


def _require_learning_unit(by_id: dict[str, LearningUnit], unit_id: str, *, operation_id: str) -> LearningUnit:
    unit = by_id.get(unit_id)
    if unit is None:
        raise ValueError(f"LearningDelta operation {operation_id} references missing unit {unit_id!r}.")
    return unit


def _operation_proposed_units(
    operation: LearningDeltaOperation,
    proposed_pool: dict[str, LearningUnit],
) -> tuple[LearningUnit, ...]:
    units: list[LearningUnit] = []
    for unit_id in operation.proposed_unit_ids:
        unit = proposed_pool.get(unit_id)
        if unit is None:
            raise ValueError(
                f"LearningDelta operation {operation.operation_id} references missing proposed unit {unit_id!r}."
            )
        units.append(_unit_with_added_provenance(unit, operation.evidence_refs))
    return tuple(units)


def _apply_explicit_learning_operation(
    by_id: dict[str, LearningUnit],
    proposed_pool: dict[str, LearningUnit],
    operation: LearningDeltaOperation,
) -> None:
    targets = tuple(operation.target_unit_ids)
    proposed_units = _operation_proposed_units(operation, proposed_pool)
    patch = _validated_operation_patch(operation)
    overlapping_ids = set(operation.target_unit_ids).intersection(operation.proposed_unit_ids)
    if overlapping_ids:
        raise ValueError(
            f"LearningDelta operation {operation.operation_id} reuses target ids as proposed ids: {sorted(overlapping_ids)!r}"
        )

    if operation.operation_kind == "initiate":
        if targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} initiate does not accept targets.")
        if not proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} initiate requires proposed units.")
        for unit in proposed_units:
            by_id[unit.unit_id] = unit
        return

    if operation.operation_kind == "append":
        if not targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} append requires targets.")
        if proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} append does not add new units.")
        if "statement" in patch:
            raise ValueError(f"LearningDelta operation {operation.operation_id} append cannot replace statement text.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_patch(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                patch,
                evidence_refs=operation.evidence_refs,
            )
        return

    if operation.operation_kind == "replace":
        if not targets or not proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} replace requires targets and proposed units.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_status(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                "superseded",
                evidence_refs=operation.evidence_refs,
            )
        for unit in proposed_units:
            by_id[unit.unit_id] = unit
        return

    if operation.operation_kind == "remove":
        if not targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} remove requires targets.")
        if proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} remove does not add new units.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_status(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                "deprecated",
                evidence_refs=operation.evidence_refs,
            )
        return

    if operation.operation_kind == "improve":
        if not targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} improve requires targets.")
        if proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} improve does not add new units.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_patch(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                patch,
                evidence_refs=operation.evidence_refs,
            )
        return

    if operation.operation_kind == "link":
        if not targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} link requires targets.")
        if proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} link does not add new units.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_patch(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                patch,
                evidence_refs=operation.evidence_refs,
            )
        return

    if operation.operation_kind == "split":
        if len(targets) != 1 or len(proposed_units) < 2:
            raise ValueError(
                f"LearningDelta operation {operation.operation_id} split requires 1 target and at least 2 proposed units."
            )
        target_id = targets[0]
        by_id[target_id] = _unit_with_status(
            _require_learning_unit(by_id, target_id, operation_id=operation.operation_id),
            "superseded",
            evidence_refs=operation.evidence_refs,
        )
        for unit in proposed_units:
            by_id[unit.unit_id] = unit
        return

    if operation.operation_kind == "merge":
        if len(targets) < 2 or len(proposed_units) != 1:
            raise ValueError(
                f"LearningDelta operation {operation.operation_id} merge requires at least 2 targets and exactly 1 proposed unit."
            )
        for unit_id in targets:
            by_id[unit_id] = _unit_with_status(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                "superseded",
                evidence_refs=operation.evidence_refs,
            )
        by_id[proposed_units[0].unit_id] = proposed_units[0]
        return

    if operation.operation_kind == "reject":
        if not targets and not proposed_units:
            raise ValueError(
                f"LearningDelta operation {operation.operation_id} reject requires targets or proposed units."
            )
        for unit_id in targets:
            by_id[unit_id] = _unit_with_status(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                "rejected",
                evidence_refs=operation.evidence_refs,
            )
        for unit in proposed_units:
            by_id[unit.unit_id] = _unit_with_status(unit, "rejected", evidence_refs=operation.evidence_refs)
        return

    if operation.operation_kind == "restore":
        if not targets:
            raise ValueError(f"LearningDelta operation {operation.operation_id} restore requires targets.")
        if proposed_units:
            raise ValueError(f"LearningDelta operation {operation.operation_id} restore does not add new units.")
        for unit_id in targets:
            by_id[unit_id] = _unit_with_status(
                _require_learning_unit(by_id, unit_id, operation_id=operation.operation_id),
                "admitted",
                evidence_refs=operation.evidence_refs,
            )
        return

    raise ValueError(f"Unsupported LearningDelta operation kind: {operation.operation_kind}")


def apply_learning_delta(context: LearningContext, delta: LearningDelta) -> LearningContext:
    normalized_context = LearningContext.from_dict(context.to_dict())
    normalized_delta = LearningDelta.from_dict(delta.to_dict())
    if normalized_context.subject_id != normalized_delta.subject_id:
        raise ValueError("LearningDelta subject_id does not match LearningContext subject_id.")

    by_id: dict[str, LearningUnit] = {unit.unit_id: unit for unit in normalized_context.units}
    proposed_pool = _learning_delta_proposed_unit_pool(normalized_delta, normalized_context.subject_id)
    if not normalized_delta.operations:
        for unit in normalized_delta.proposed_units:
            normalized_unit = _normalized_learning_unit_for_subject(unit, normalized_context.subject_id)
            by_id[normalized_unit.unit_id] = normalized_unit
    for unit_id in normalized_delta.deprecated_unit_ids:
        current = by_id.get(unit_id)
        if current is None:
            continue
        by_id[unit_id] = _unit_with_status(current, "deprecated")
    for operation in normalized_delta.operations:
        _apply_explicit_learning_operation(by_id, proposed_pool, operation)
    units = tuple(sorted(by_id.values(), key=lambda item: (item.unit_kind, item.canonical_title, item.unit_id)))
    unit_linked_skill_ids = [
        str(skill_id)
        for unit in units
        for skill_id in unit.linked_skill_ids
        if collapse_ws(str(skill_id))
    ]
    operation_evidence_refs = [
        str(source_id)
        for operation in normalized_delta.operations
        for source_id in operation.evidence_refs
        if collapse_ws(str(source_id))
    ]
    return LearningContext(
        subject_id=normalized_context.subject_id,
        canonical_title=normalized_context.canonical_title,
        aliases=_ordered_unique_texts(list(normalized_context.aliases)),
        subject_family=normalized_context.subject_family,
        summary=normalized_context.summary,
        units=units,
        linked_source_ids=_ordered_unique_texts(
            list(normalized_context.linked_source_ids)
            + list(normalized_delta.evidence_refs)
            + operation_evidence_refs
        ),
        linked_skill_ids=_ordered_unique_texts(
            list(normalized_context.linked_skill_ids)
            + list(normalized_delta.derived_skill_ids)
            + unit_linked_skill_ids
        ),
        linked_document_section_ids=_ordered_unique_texts(
            list(normalized_context.linked_document_section_ids) + list(normalized_delta.document_section_ids)
        ),
        applied_delta_ids=_ordered_unique_texts(list(normalized_context.applied_delta_ids) + [normalized_delta.delta_id]),
        governance_status="active" if units else normalized_context.governance_status,
        metadata=dict(normalized_context.metadata),
    )
