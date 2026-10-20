"""Transport-neutral subject workflow request and response contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable


@dataclass(frozen=True)
class SubjectImportStaging:
    source_subject_id: str
    source_subject_title: str
    source_subject_version_id: str = ""
    import_kind: str = "definition_support"
    selection_profile: str = "units_only"


@dataclass(frozen=True)
class SubjectWorkflowScenarioView:
    key: str
    subject_id: str
    title: str
    family_title: str
    context_id: str
    summary: str
    governance_status: str
    context_snapshot_hash: str
    unit_count: int
    admitted_unit_count: int
    source_count: int
    delta_count: int
    applied_delta_count: int
    import_count: int
    pending_import_count: int
    reasoning_import_count: int
    imported_subject_count: int
    context_path: str
    subject_markdown_path: str
    subject_typst_path: str
    publication_id: str
    publication_title: str
    build_id: str
    build_status: str
    validation_status: str
    build_path: str
    publication_section_count: int
    publication_claim_count: int
    publication_source_count: int
    publication_entity_count: int
    publication_xref_count: int
    publication_review_count: int
    report_markdown_path: str
    report_typst_path: str
    report_pdf_path: str
    composition_id: str
    composition_status: str
    composition_title: str
    composition_scope_summary: str
    composition_learning_context_snapshot_hash: str
    composition_included_unit_count: int
    composition_selected_import_count: int
    composition_section_count: int
    source_collection_count: int
    staged_source_count: int
    source_collection_preview_lines: tuple[str, ...]
    source_preview_lines: tuple[str, ...]
    staged_source_preview_lines: tuple[str, ...]
    unit_preview_lines: tuple[str, ...]
    delta_preview_lines: tuple[str, ...]
    pending_import_preview_lines: tuple[str, ...]
    import_preview_lines: tuple[str, ...]
    is_placeholder: bool


@dataclass(frozen=True)
class SubjectWorkflowKeyValueRowView:
    label: str
    value: str


@dataclass(frozen=True)
class SubjectWorkflowPaneItemView:
    """Typed, interaction-safe projection for one item rendered in a pane."""

    entry_id: str
    entry_kind: str
    label: str
    ordinal: int = 0
    parent_entry_id: str = ""
    depth: int = 0
    selectable: bool = False
    selected: bool = False
    toggleable: bool = False
    check_state: str = "none"
    held: bool = False
    status: str = ""
    semantic_kind: str = ""
    render_kind: str = ""
    evidence_mode: str = ""
    transform_mode: str = ""
    source_unit_id: str = ""
    source_item_id: str = ""
    source_ref: str = ""
    source_kind: str = ""
    media_type: str = ""
    latest_revision_id: str = ""
    latest_revision_kind: str = ""
    revision_count: int = 0
    bundle_file_count: int = 0
    sort_kind: str = ""
    summary: str = ""
    description: str = ""
    query_text: str = ""
    notes: str = ""
    confidence: float = 0.0
    related_ids: tuple[str, ...] = ()
    detail_title: str = ""
    detail_lines: tuple[str, ...] = ()
    attributes: tuple[SubjectWorkflowKeyValueRowView, ...] = ()


@dataclass(frozen=True)
class SubjectWorkflowGateActionView:
    display_kind: str
    action_kind: str
    key: str
    label: str
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowActionSpecView:
    key: str
    label: str
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowOptionView:
    label: str
    value: str


@dataclass(frozen=True)
class SubjectWorkflowSelectionOptionView:
    label: str
    value: str
    selected: bool


@dataclass(frozen=True)
class SubjectWorkflowSelectSpecView:
    key: str
    label: str
    value: str
    options: tuple[SubjectWorkflowOptionView, ...]
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowSwitchSpecView:
    key: str
    label: str
    value: bool
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowSelectionListSpecView:
    key: str
    label: str
    action_key_prefix: str
    options: tuple[SubjectWorkflowSelectionOptionView, ...]
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowTableSpecView:
    key: str
    label: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    enabled: bool


@dataclass(frozen=True)
class SubjectWorkflowControlBundleView:
    phase: str
    more_actions: tuple[SubjectWorkflowActionSpecView, ...]
    selects: tuple[SubjectWorkflowSelectSpecView, ...]
    switches: tuple[SubjectWorkflowSwitchSpecView, ...]
    selection_lists: tuple[SubjectWorkflowSelectionListSpecView, ...]
    tables: tuple[SubjectWorkflowTableSpecView, ...]
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class SubjectWorkflowPaneView:
    key: str
    title: str
    lines: tuple[str, ...]
    rows: tuple[SubjectWorkflowKeyValueRowView, ...] = ()
    is_structured_table: bool = False
    items: tuple[SubjectWorkflowPaneItemView, ...] = ()


@dataclass(frozen=True)
class SubjectWorkflowPaneBundleView:
    phase: str
    panes: tuple[SubjectWorkflowPaneView, ...]
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class SubjectWorkflowCurrentStepView:
    title: str
    status: str
    why: str
    detail_lines: tuple[str, ...]
    actions: tuple[SubjectWorkflowGateActionView, ...]


@dataclass(frozen=True)
class SubjectWorkflowTextSectionView:
    title: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class SubjectWorkflowStatusView:
    title: str
    rows: tuple[SubjectWorkflowKeyValueRowView, ...]


@dataclass(frozen=True)
class SubjectWorkflowPhaseView:
    phase: str
    phase_title: str
    preferred_phase: str
    scenario: SubjectWorkflowScenarioView
    current_step: SubjectWorkflowCurrentStepView
    status_view: SubjectWorkflowStatusView
    journey_lines: tuple[str, ...]
    workspace_view: SubjectWorkflowTextSectionView
    latest_receipt_title: str
    latest_receipt_lines: tuple[str, ...]
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class SubjectWorkflowSnapshotView:
    phase_view: SubjectWorkflowPhaseView
    control_bundle: SubjectWorkflowControlBundleView
    pane_bundle: SubjectWorkflowPaneBundleView
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class WorkstationArtifactRefView:
    label: str
    server_path: str
    mime_type: str
    download_url: str
    can_open_locally: bool


@dataclass(frozen=True)
class SubjectWorkflowActionOutcomeView:
    status_text: str
    timeline_text: str
    next_phase: str
    next_tab: str
    reload_subjects: bool
    open_paths: tuple[str, ...]
    preferred_subject_key: str
    phase_view: SubjectWorkflowPhaseView
    open_artifacts: tuple[WorkstationArtifactRefView, ...] = ()
    trace_id: str = ""
    parent_id: str = ""


@dataclass(frozen=True)
class SubjectWorkflowWatchEventView:
    event_kind: str
    snapshot: SubjectWorkflowSnapshotView
    channel_key: str = ""
    sequence: int = 0
    snapshot_version: str = ""
    progress_fingerprint: str = ""
    trace_id: str = ""
    parent_id: str = ""


@runtime_checkable
class SubjectWorkflowClient(Protocol):
    @property
    def client_session_id(self) -> str: ...

    def list_subjects(self, *, root_path: Path) -> tuple[SubjectWorkflowScenarioView, ...]: ...

    def get_phase_view(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        client_session_id: str = "",
    ) -> SubjectWorkflowPhaseView: ...

    def get_control_bundle(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        client_session_id: str = "",
    ) -> SubjectWorkflowControlBundleView: ...

    def get_pane_bundle(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        client_session_id: str = "",
    ) -> SubjectWorkflowPaneBundleView: ...

    def get_snapshot(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        client_session_id: str = "",
    ) -> SubjectWorkflowSnapshotView: ...

    def apply_action(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        action_key: str,
        assistant_message_text: str = "",
        subject_title_override: str = "",
        import_staging: SubjectImportStaging | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        client_session_id: str = "",
    ) -> SubjectWorkflowActionOutcomeView: ...

    def get_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str = "",
    ) -> str: ...

    def put_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress_json: str,
        client_session_id: str = "",
    ) -> str: ...

    def apply_interaction(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        interaction_key: str,
        delta: int = 0,
        target_id: str = "",
        preview_only: bool = False,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        client_session_id: str = "",
    ) -> tuple[SubjectWorkflowSnapshotView, str, str]: ...

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
        client_session_id: str = "",
        stop_when: Callable[[], bool] | None = None,
    ): ...


SubjectImportStaging.__module__ = "workstation.subject.core.subject_workflow"
for _view_type in (
    SubjectWorkflowScenarioView,
    SubjectWorkflowKeyValueRowView,
    SubjectWorkflowPaneItemView,
    SubjectWorkflowGateActionView,
    SubjectWorkflowActionSpecView,
    SubjectWorkflowOptionView,
    SubjectWorkflowSelectionOptionView,
    SubjectWorkflowSelectSpecView,
    SubjectWorkflowSwitchSpecView,
    SubjectWorkflowSelectionListSpecView,
    SubjectWorkflowTableSpecView,
    SubjectWorkflowControlBundleView,
    SubjectWorkflowPaneView,
    SubjectWorkflowPaneBundleView,
    SubjectWorkflowCurrentStepView,
    SubjectWorkflowTextSectionView,
    SubjectWorkflowStatusView,
    SubjectWorkflowPhaseView,
    SubjectWorkflowSnapshotView,
    WorkstationArtifactRefView,
    SubjectWorkflowActionOutcomeView,
    SubjectWorkflowWatchEventView,
):
    _view_type.__module__ = "workstation.subject.service.subject_workflow_api"
SubjectWorkflowClient.__module__ = "workstation.subject.service.subject_workflow_client"
del _view_type

__all__ = [
    "SubjectImportStaging",
    "SubjectWorkflowActionOutcomeView",
    "SubjectWorkflowActionSpecView",
    "SubjectWorkflowClient",
    "SubjectWorkflowControlBundleView",
    "SubjectWorkflowCurrentStepView",
    "SubjectWorkflowGateActionView",
    "SubjectWorkflowKeyValueRowView",
    "SubjectWorkflowOptionView",
    "SubjectWorkflowPaneBundleView",
    "SubjectWorkflowPaneItemView",
    "SubjectWorkflowPaneView",
    "SubjectWorkflowPhaseView",
    "SubjectWorkflowScenarioView",
    "SubjectWorkflowSelectionListSpecView",
    "SubjectWorkflowSelectionOptionView",
    "SubjectWorkflowSelectSpecView",
    "SubjectWorkflowSnapshotView",
    "SubjectWorkflowStatusView",
    "SubjectWorkflowSwitchSpecView",
    "SubjectWorkflowTableSpecView",
    "SubjectWorkflowTextSectionView",
    "SubjectWorkflowWatchEventView",
    "WorkstationArtifactRefView",
]
