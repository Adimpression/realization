# See MODULES.md for the repository module map before editing.
"""Contract-only subject workflow projection backend for Textual."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from workstation.contracts.subject import (
    SubjectImportStaging,
    SubjectWorkflowActionOutcomeView,
    SubjectWorkflowClient,
    SubjectWorkflowPaneItemView,
    SubjectWorkflowSnapshotView,
)
from workstation.subject.textual.models import (
    TextualPaneItemRecord,
    TextualSubjectProgress,
    textual_subject_has_pending_research_capture,
    textual_subject_pending_research_capture_target,
    textual_subject_progress_fingerprint,
)


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())


@dataclass
class TextualSubjectWorkflowProjectionBackend:
    client: SubjectWorkflowClient
    _latest_interaction_snapshots: dict[str, SubjectWorkflowSnapshotView] = field(default_factory=dict, init=False)
    _snapshots: dict[tuple[str, str], SubjectWorkflowSnapshotView] = field(default_factory=dict, init=False)
    _latest_snapshot_by_subject: dict[str, SubjectWorkflowSnapshotView] = field(default_factory=dict, init=False)
    _persisted_progress_fingerprints: dict[str, str] = field(default_factory=dict, init=False)

    def list_subjects(self, *, root_path: Path):
        return self.client.list_subjects(root_path=root_path)

    def uses_in_process_service(self) -> bool:
        return False

    def load_progress(self, *, root_path: Path, subject_id: str) -> TextualSubjectProgress:
        progress_json = self.client.get_client_progress_json(
            root_path=root_path,
            subject_id=subject_id,
            client_session_id=self.client.client_session_id,
        )
        progress = TextualSubjectProgress(json.loads(progress_json))
        normalized_subject_id = _clean(subject_id)
        if normalized_subject_id:
            self._persisted_progress_fingerprints[normalized_subject_id] = self.progress_fingerprint(progress)
        return progress

    def load_progress_map(
        self,
        *,
        root_path: Path,
        scenarios,
        existing: dict[str, TextualSubjectProgress] | None = None,
    ) -> dict[str, TextualSubjectProgress]:
        del existing
        return {
            (getattr(scenario, "key", "") or getattr(scenario, "subject_id", "")): self.load_progress(
                root_path=root_path,
                subject_id=getattr(scenario, "subject_id", ""),
            )
            for scenario in scenarios
            if getattr(scenario, "subject_id", "")
        }

    def persist_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress: TextualSubjectProgress,
    ) -> Path | None:
        updated_json = self.client.put_client_progress_json(
            root_path=root_path,
            subject_id=subject_id,
            progress_json=json.dumps(progress.to_payload(), indent=2, sort_keys=True),
            client_session_id=self.client.client_session_id,
        )
        progress.replace_from_payload(json.loads(updated_json))
        normalized_subject_id = _clean(subject_id)
        if normalized_subject_id:
            self._persisted_progress_fingerprints[normalized_subject_id] = self.progress_fingerprint(progress)
            self._invalidate_subject_snapshots(normalized_subject_id)
        return None

    def progress_fingerprint(self, progress: TextualSubjectProgress) -> str:
        return textual_subject_progress_fingerprint(progress)

    def has_pending_research_capture(self, progress: TextualSubjectProgress) -> bool:
        return textual_subject_has_pending_research_capture(progress)

    def pending_research_capture_target(self, progress: TextualSubjectProgress) -> str:
        return textual_subject_pending_research_capture_target(progress)

    def source_collections(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
    ) -> tuple[TextualPaneItemRecord, ...]:
        return self._records(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="research",
            pane_key="research_sources",
            progress=progress,
            entry_kind="source_collection",
        )

    def staged_sources_for_selected_collection(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress: TextualSubjectProgress,
    ) -> tuple[TextualPaneItemRecord | None, tuple[TextualPaneItemRecord, ...]]:
        records = self._records(
            root_path=root_path,
            subject_id=subject_id,
            phase="research",
            pane_key="research_sources",
            progress=progress,
        )
        collections = tuple(record for record in records if record.view.entry_kind == "source_collection")
        sources = tuple(record for record in records if record.view.entry_kind == "staged_source")
        selected_collection = next((record for record in collections if record.view.selected), None)
        return selected_collection, sources

    def itemization_session_and_items(self, *, root_path: Path, scenario):
        records = self._records(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="itemize",
            pane_key="itemize_inventory",
            entry_kind="itemized_item",
        )
        return None, records

    def selected_itemization_item(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
    ) -> TextualPaneItemRecord | None:
        _session, items = self.itemization_session_and_items(root_path=root_path, scenario=scenario)
        return self._selected_record(items, progress.itemize_cursor, progress.itemize_selected_item_id)

    def move_itemize_cursor(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        delta: int,
    ) -> TextualPaneItemRecord | None:
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="itemize",
            progress=progress,
            interaction_key="move_itemize_cursor",
            delta=delta,
        )
        return self.selected_itemization_item(root_path=root_path, scenario=scenario, progress=progress)

    def move_research_source_cursor(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        delta: int,
    ) -> TextualPaneItemRecord | None:
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="research",
            progress=progress,
            interaction_key="move_research_source_cursor",
            delta=delta,
        )
        _collection, sources = self.staged_sources_for_selected_collection(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            progress=progress,
        )
        return self._selected_record(
            sources,
            progress.research_source_cursor,
            progress.research_selected_staged_source_id,
        )

    def flattened_draft_review_items(self, *, root_path: Path, scenario):
        records = self._records(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="draft",
            pane_key="draft_scope_tree",
            entry_kind="draft_review_item",
        )
        return tuple((record, int(record.view.depth)) for record in records)

    def selected_draft_review_item(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
    ):
        flattened = self.flattened_draft_review_items(root_path=root_path, scenario=scenario)
        selected = self._selected_record(
            tuple(record for record, _depth in flattened),
            progress.itemize_cursor,
            progress.draft_selected_review_item_id,
        )
        return selected, "contract_selection" if selected is not None else ""

    def set_draft_selection_to_review_item_id(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        review_item_id: str,
    ) -> None:
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="draft",
            progress=progress,
            interaction_key="set_draft_selection_to_review_item_id",
            target_id=review_item_id,
        )

    def transformation_construct_candidates(
        self,
        *,
        root_path: Path,
        scenario,
        include_rejected: bool = True,
    ) -> tuple[TextualPaneItemRecord, ...]:
        del include_rejected
        return self._records(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="draft",
            pane_key="draft_scope_tree",
            entry_kind="construct_candidate",
        )

    def set_draft_selection_to_construct_candidate_id(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        construct_candidate_id: str,
    ) -> None:
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="draft",
            progress=progress,
            interaction_key="set_draft_selection_to_construct_candidate_id",
            target_id=construct_candidate_id,
        )

    def move_draft_review_cursor(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        delta: int,
    ):
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase="draft",
            progress=progress,
            interaction_key="move_draft_review_cursor",
            delta=delta,
        )
        if _clean(progress.draft_focus_mode).casefold() == "model":
            records = self.transformation_construct_candidates(root_path=root_path, scenario=scenario)
            return self._selected_record(records, progress.draft_model_cursor, progress.draft_selected_construct_candidate_id)
        return self.selected_draft_review_item(root_path=root_path, scenario=scenario, progress=progress)[0]

    def report_scope_entries(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
    ) -> tuple[TextualPaneItemRecord, ...]:
        subject_id = self._subject_id(scenario)
        snapshot = self._latest_snapshot_by_subject.get(subject_id)
        phase = _clean(getattr(getattr(snapshot, "phase_view", None), "phase", "")) if snapshot else ""
        phase = phase if phase in {"review", "publication"} else "review"
        pane_key = "publication_scope_tree" if phase == "publication" else "review_scope_tree"
        return self._records(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            pane_key=pane_key,
            progress=progress,
        )

    def selectable_report_scope_entries(self, entries) -> tuple:
        return tuple(entry for entry in entries if bool(entry.selectable))

    def selected_report_scope_section_entry(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
    ):
        entries = self.report_scope_entries(root_path=root_path, scenario=scenario, progress=progress)
        selectable = self.selectable_report_scope_entries(entries)
        selected = self._selected_record(selectable, progress.report_scope_cursor, "")
        if selected is None or selected.item_kind != "section":
            return None
        section_id = selected.entry_id.split(":", 1)[-1]
        return (
            None,
            selected,
            section_id,
            selected.attributes.get("role", ""),
            selected.detail_title or selected.label,
        )

    def move_report_scope_cursor(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        delta: int,
    ):
        phase = self._report_scope_phase(self._subject_id(scenario))
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase=phase,
            progress=progress,
            interaction_key="move_report_scope_cursor",
            delta=delta,
        )
        return self.selected_report_scope_section_entry(root_path=root_path, scenario=scenario, progress=progress)

    def preview_move_held_report_scope_items(
        self,
        *,
        root_path: Path,
        scenario,
        progress: TextualSubjectProgress,
        delta: int,
    ):
        phase = self._report_scope_phase(self._subject_id(scenario))
        self._apply_interaction_into_progress(
            root_path=root_path,
            subject_id=self._subject_id(scenario),
            phase=phase,
            progress=progress,
            interaction_key="preview_move_held_report_scope_items",
            delta=delta,
        )
        return self.selected_report_scope_section_entry(root_path=root_path, scenario=scenario, progress=progress)

    def take_latest_interaction_snapshot(self, phase: str) -> SubjectWorkflowSnapshotView | None:
        return self._latest_interaction_snapshots.pop(_clean(phase).casefold(), None)

    def get_snapshot(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress: TextualSubjectProgress | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowSnapshotView:
        self._persist_progress_if_changed(
            root_path=root_path,
            subject_id=subject_id,
            progress=progress,
        )
        snapshot = self.client.get_snapshot(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            client_session_id=self.client.client_session_id,
            can_capture_assistant=can_capture_assistant,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
        )
        self._remember_snapshot(subject_id, phase, snapshot)
        return snapshot

    def apply_action(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        action_key: str,
        progress: TextualSubjectProgress | None = None,
        import_staging: SubjectImportStaging | None = None,
        assistant_message_text: str = "",
        subject_title_override: str = "",
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowActionOutcomeView:
        self._persist_progress_if_changed(
            root_path=root_path,
            subject_id=subject_id,
            progress=progress,
        )
        outcome = self.client.apply_action(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            action_key=action_key,
            client_session_id=self.client.client_session_id,
            import_staging=import_staging,
            assistant_message_text=assistant_message_text,
            subject_title_override=subject_title_override,
            can_capture_assistant=can_capture_assistant,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
        )
        self._invalidate_subject_snapshots(subject_id)
        return outcome

    def watch_subject_workflow(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        stop_when=None,
    ):
        return self.client.watch_subject_workflow(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            client_session_id=self.client.client_session_id,
            can_capture_assistant=can_capture_assistant,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
            stop_when=stop_when,
        )

    def _apply_interaction_into_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress: TextualSubjectProgress,
        interaction_key: str,
        delta: int = 0,
        target_id: str = "",
    ) -> None:
        self.persist_progress(root_path=root_path, subject_id=subject_id, progress=progress)
        snapshot, progress_json, _fingerprint = self.client.apply_interaction(
            root_path=root_path,
            subject_id=subject_id,
            phase=phase,
            interaction_key=interaction_key,
            delta=delta,
            target_id=target_id,
            client_session_id=self.client.client_session_id,
        )
        normalized_phase = _clean(phase).casefold()
        self._latest_interaction_snapshots[normalized_phase] = snapshot
        self._invalidate_subject_snapshots(subject_id)
        self._remember_snapshot(subject_id, normalized_phase, snapshot)
        progress.replace_from_payload(json.loads(progress_json))
        normalized_subject_id = _clean(subject_id)
        if normalized_subject_id:
            self._persisted_progress_fingerprints[normalized_subject_id] = self.progress_fingerprint(progress)

    def _records(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        pane_key: str,
        progress: TextualSubjectProgress | None = None,
        entry_kind: str = "",
    ) -> tuple[TextualPaneItemRecord, ...]:
        self._persist_progress_if_changed(
            root_path=root_path,
            subject_id=subject_id,
            progress=progress,
        )
        snapshot = self._snapshots.get((subject_id, phase))
        if snapshot is None:
            snapshot = self.get_snapshot(
                root_path=root_path,
                subject_id=subject_id,
                phase=phase,
                progress=progress,
            )
        pane = next(
            (candidate for candidate in snapshot.pane_bundle.panes if _clean(candidate.key) == _clean(pane_key)),
            None,
        )
        items: tuple[SubjectWorkflowPaneItemView, ...] = tuple(getattr(pane, "items", ()) or ())
        if entry_kind:
            items = tuple(item for item in items if _clean(item.entry_kind) == _clean(entry_kind))
        return tuple(TextualPaneItemRecord(item) for item in items)

    def _remember_snapshot(self, subject_id: str, phase: str, snapshot: SubjectWorkflowSnapshotView) -> None:
        normalized_subject_id = _clean(subject_id)
        normalized_phase = _clean(phase).casefold()
        self._snapshots[(normalized_subject_id, normalized_phase)] = snapshot
        self._latest_snapshot_by_subject[normalized_subject_id] = snapshot

    def _persist_progress_if_changed(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress: TextualSubjectProgress | None,
    ) -> None:
        normalized_subject_id = _clean(subject_id)
        if progress is None or not normalized_subject_id:
            return
        fingerprint = self.progress_fingerprint(progress)
        if self._persisted_progress_fingerprints.get(normalized_subject_id) == fingerprint:
            return
        self.persist_progress(
            root_path=root_path,
            subject_id=normalized_subject_id,
            progress=progress,
        )

    def _invalidate_subject_snapshots(self, subject_id: str) -> None:
        normalized_subject_id = _clean(subject_id)
        self._snapshots = {
            key: snapshot
            for key, snapshot in self._snapshots.items()
            if key[0] != normalized_subject_id
        }

    def _report_scope_phase(self, subject_id: str) -> str:
        snapshot = self._latest_snapshot_by_subject.get(_clean(subject_id))
        phase = _clean(getattr(getattr(snapshot, "phase_view", None), "phase", "")).casefold()
        return phase if phase in {"review", "publication"} else "review"

    @staticmethod
    def _subject_id(scenario) -> str:
        return _clean(getattr(scenario, "subject_id", "")) or _clean(getattr(scenario, "key", ""))

    @staticmethod
    def _selected_record(records, cursor: int, selected_id: str) -> TextualPaneItemRecord | None:
        records = tuple(records)
        normalized_id = _clean(selected_id)
        if normalized_id:
            explicit = next((record for record in records if _clean(record.view.entry_id) == normalized_id), None)
            if explicit is not None:
                return explicit
        selected = next((record for record in records if bool(record.view.selected)), None)
        if selected is not None:
            return selected
        if not records:
            return None
        return records[max(0, min(len(records) - 1, int(cursor or 0)))]


__all__ = ["TextualSubjectWorkflowProjectionBackend"]
