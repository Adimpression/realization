"""Textual-local compatibility views built from the public subject contract."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from workstation.contracts.subject import SubjectWorkflowPaneItemView


SUBJECT_PHASES = ("research", "itemize", "draft", "review", "publication")


@dataclass(frozen=True)
class TextualSubjectActionSpec:
    key: str
    label: str
    enabled: bool


@dataclass(frozen=True)
class TextualSubjectGateAction:
    kind: str
    key: str
    label: str
    enabled: bool = True


@dataclass(frozen=True)
class TextualSubjectSelectSpec:
    label: str
    value: str
    options: tuple[tuple[str, str], ...]
    enabled: bool


@dataclass(frozen=True)
class TextualSubjectSwitchSpec:
    label: str
    value: bool
    enabled: bool


@dataclass(frozen=True)
class TextualSubjectSelectionListSpec:
    label: str
    action_key_prefix: str
    options: tuple[tuple[str, str, bool], ...]
    enabled: bool


@dataclass(frozen=True)
class TextualSubjectTableSpec:
    label: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    enabled: bool


_LIST_PROGRESS_FIELDS = {
    "latest_receipt_lines",
    "comparison_receipt_lines",
    "build_receipt_lines",
    "timeline",
    "report_scope_held_entry_ids",
    "report_scope_preview_order_ids",
    "pending_research_capture_preview_lines",
    "itemize_held_item_ids",
}
_BOOL_PROGRESS_FIELDS = {
    "context_opened",
    "projections_compared",
    "review_approved",
    "publication_locked",
    "release_packet_opened",
    "release_review_completed",
}
_INT_PROGRESS_FIELDS = {
    "composition_unit_cursor",
    "composition_import_cursor",
    "report_scope_cursor",
    "research_collection_cursor",
    "research_source_cursor",
    "itemize_cursor",
    "draft_model_cursor",
}
_SPECIAL_PROGRESS_DEFAULTS: dict[str, object] = {
    "review_preview_kind": "subject.md",
    "publication_preview_kind": "report.pdf",
    "comparison_status": "pending",
    "draft_focus_mode": "compose",
    "draft_model_lens": "model",
}


class TextualSubjectProgress:
    """Mutable client-view state whose wire representation is JSON."""

    def __init__(self, payload: Mapping[str, object] | None = None) -> None:
        for key, value in dict(payload or {}).items():
            if key != "schema":
                setattr(self, key, copy.deepcopy(value))
        if not getattr(self, "timeline", None):
            self.timeline = ["Live subject opened."]

    def __getattr__(self, name: str) -> object:
        if name in _LIST_PROGRESS_FIELDS:
            value: object = []
        elif name in _BOOL_PROGRESS_FIELDS:
            value = False
        elif name in _INT_PROGRESS_FIELDS or name.endswith("_cursor"):
            value = 0
        else:
            value = copy.deepcopy(_SPECIAL_PROGRESS_DEFAULTS.get(name, ""))
        setattr(self, name, value)
        return value

    def replace_from_payload(self, payload: Mapping[str, object] | None) -> None:
        self.__dict__.clear()
        for key, value in dict(payload or {}).items():
            if key != "schema":
                setattr(self, key, copy.deepcopy(value))
        if not getattr(self, "timeline", None):
            self.timeline = ["Live subject opened."]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema": "workstation_subject_progress.v1",
            **{key: copy.deepcopy(value) for key, value in self.__dict__.items()},
        }


def new_textual_subject_progress() -> TextualSubjectProgress:
    return TextualSubjectProgress()


def _textual_subject_progress_payload(progress: object) -> dict[str, object]:
    to_payload = getattr(progress, "to_payload", None)
    if callable(to_payload):
        return dict(to_payload())
    values = getattr(progress, "__dict__", None)
    if isinstance(values, dict):
        return {
            "schema": "workstation_subject_progress.v1",
            **{str(key): copy.deepcopy(value) for key, value in values.items()},
        }
    raise TypeError("Subject progress must expose to_payload() or attribute state.")


def textual_subject_progress_fingerprint(progress: object) -> str:
    rendered = json.dumps(
        _textual_subject_progress_payload(progress),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def textual_subject_has_pending_research_capture(progress: TextualSubjectProgress) -> bool:
    return bool(str(getattr(progress, "pending_research_capture_markdown_text", "") or "").strip())


def textual_subject_pending_research_capture_target(progress: TextualSubjectProgress) -> str:
    return (
        str(getattr(progress, "pending_research_capture_subject_title_override", "") or "").strip()
        or str(getattr(progress, "pending_research_capture_subject_title", "") or "").strip()
        or str(getattr(progress, "pending_research_capture_subject_id", "") or "").strip()
    )


def textual_subject_status_title(phase: str) -> str:
    normalized = str(phase or "").strip().casefold()
    return "Subject Status" if normalized == "research" else f"{normalized.title() or 'Subject'} Status"


def normalize_textual_decision_role(value: str) -> str:
    normalized = " ".join(str(value or "").strip().lower().replace("_", " ").split()).replace(" ", "_")
    return normalized if normalized in {
        "",
        "actor",
        "objective",
        "capability",
        "dependency",
        "constraint",
        "boundary",
        "state",
        "transition",
        "decision",
    } else ""


@dataclass(frozen=True)
class TextualPaneItemRecord:
    """Attribute-compatible local wrapper around one typed pane item."""

    view: SubjectWorkflowPaneItemView

    @property
    def attributes(self) -> dict[str, str]:
        return {str(row.label): str(row.value) for row in self.view.attributes}

    @property
    def metadata(self) -> dict[str, object]:
        return {
            "canonical_label": self.view.label,
            "decision_role": self.attributes.get("decision_role", ""),
            "collection_kind": self.attributes.get("collection_kind", ""),
        }

    @property
    def collection_id(self) -> str:
        return self.view.entry_id

    @property
    def staged_source_id(self) -> str:
        return self.view.entry_id

    @property
    def itemized_item_id(self) -> str:
        return self.view.entry_id

    @property
    def review_item_id(self) -> str:
        return self.view.entry_id

    @property
    def construct_candidate_id(self) -> str:
        return self.view.entry_id

    @property
    def entry_id(self) -> str:
        return self.view.entry_id

    @property
    def item_kind(self) -> str:
        prefix = "report_scope_"
        return self.view.entry_kind[len(prefix):] if self.view.entry_kind.startswith(prefix) else self.view.semantic_kind

    @property
    def canonical_label(self) -> str:
        return self.view.label

    @property
    def title(self) -> str:
        return self.view.label

    @property
    def included(self) -> bool | None:
        if self.view.check_state == "checked":
            return True
        if self.view.check_state == "unchecked":
            return False
        return None

    @property
    def staged_source_ids(self) -> tuple[str, ...]:
        return tuple(self.view.related_ids)

    @property
    def child_review_item_ids(self) -> tuple[str, ...]:
        return tuple(self.view.related_ids)

    @property
    def linked_item_ids(self) -> tuple[str, ...]:
        return tuple(self.view.related_ids)

    @property
    def bundle_relpaths(self) -> tuple[str, ...]:
        return tuple("" for _ in range(max(0, int(self.view.bundle_file_count))))

    def __getattr__(self, name: str) -> Any:
        aliases = {
            "subject_id": "",
            "source_itemized_item_id": self.view.source_item_id,
            "itemized_item_id": self.view.source_item_id,
            "parent_review_item_id": self.view.parent_entry_id,
            "ordering": self.view.ordinal,
            "selectable": self.view.selectable,
            "selected": self.view.selected,
            "toggleable": self.view.toggleable,
            "held": self.view.held,
            "reportable": self.view.status != "question",
            "status": self.view.status,
            "semantic_kind": self.view.semantic_kind,
            "render_kind": self.view.render_kind,
            "evidence_mode": self.view.evidence_mode,
            "transform_mode": self.view.transform_mode,
            "source_unit_id": self.view.source_unit_id,
            "source_ref": self.view.source_ref,
            "source_kind": self.view.source_kind,
            "media_type": self.view.media_type,
            "latest_revision_id": self.view.latest_revision_id,
            "revision_id": self.view.latest_revision_id,
            "revision_kind": self.view.latest_revision_kind,
            "revision_count": self.view.revision_count,
            "sort_kind": self.view.sort_kind,
            "summary": self.view.summary,
            "description": self.view.description,
            "query_text": self.view.query_text,
            "notes": self.view.notes,
            "confidence": self.view.confidence,
            "depth": self.view.depth,
            "label": self.view.label,
            "detail_title": self.view.detail_title,
            "detail_lines": tuple(self.view.detail_lines),
            "review_item_id": self.attributes.get("review_item_id", ""),
        }
        if name in aliases:
            return aliases[name]
        raise AttributeError(name)


def source_collection_option_label(record: TextualPaneItemRecord) -> str:
    return record.view.label


def source_collection_workbench_rows(record: TextualPaneItemRecord) -> tuple[tuple[str, str], ...]:
    excluded = {"source_count", "collection_kind"}
    return tuple(
        (row.label, row.value)
        for row in record.view.attributes
        if row.label not in excluded
    )


def latest_source_revision(
    root_path,
    record: TextualPaneItemRecord,
) -> TextualPaneItemRecord | None:
    del root_path
    return record if record.view.latest_revision_id else None


__all__ = [
    "SUBJECT_PHASES",
    "TextualPaneItemRecord",
    "TextualSubjectActionSpec",
    "TextualSubjectGateAction",
    "TextualSubjectProgress",
    "TextualSubjectSelectionListSpec",
    "TextualSubjectSelectSpec",
    "TextualSubjectSwitchSpec",
    "TextualSubjectTableSpec",
    "latest_source_revision",
    "new_textual_subject_progress",
    "normalize_textual_decision_role",
    "source_collection_option_label",
    "source_collection_workbench_rows",
    "textual_subject_has_pending_research_capture",
    "textual_subject_pending_research_capture_target",
    "textual_subject_progress_fingerprint",
    "textual_subject_status_title",
]
