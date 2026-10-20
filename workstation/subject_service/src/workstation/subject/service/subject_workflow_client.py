# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import uuid

import grpc

from semantic_text import collapse_ws
from workstation.contracts.subject import (
    SubjectImportStaging,
    SubjectWorkflowActionOutcomeView,
    SubjectWorkflowActionSpecView,
    SubjectWorkflowClient,
    SubjectWorkflowControlBundleView,
    SubjectWorkflowCurrentStepView,
    SubjectWorkflowGateActionView,
    SubjectWorkflowKeyValueRowView,
    SubjectWorkflowOptionView,
    SubjectWorkflowPaneBundleView,
    SubjectWorkflowPaneItemView,
    SubjectWorkflowPaneView,
    SubjectWorkflowPhaseView,
    SubjectWorkflowScenarioView,
    SubjectWorkflowSelectionListSpecView,
    SubjectWorkflowSelectionOptionView,
    SubjectWorkflowSelectSpecView,
    SubjectWorkflowSnapshotView,
    SubjectWorkflowStatusView,
    SubjectWorkflowSwitchSpecView,
    SubjectWorkflowTableSpecView,
    SubjectWorkflowTextSectionView,
    SubjectWorkflowWatchEventView,
    WorkstationArtifactRefView,
)
from workstation.grpc.definitions import subject_workflow_pb2, subject_workflow_pb2_grpc
from workstation.subject.core.subject_workflow import subject_progress_fingerprint
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService


def _projection_context_message(
    *,
    can_capture_assistant: bool = False,
    markdown_selected_path: str = "",
    markdown_status_text: str = "",
    markdown_busy: bool = False,
) -> subject_workflow_pb2.SubjectPhaseProjectionContext:
    return subject_workflow_pb2.SubjectPhaseProjectionContext(
        can_capture_assistant=bool(can_capture_assistant),
        markdown_selected_path=str(markdown_selected_path or ""),
        markdown_status_text=str(markdown_status_text or ""),
        markdown_busy=bool(markdown_busy),
    )


def _import_staging_message(import_staging: SubjectImportStaging | None) -> subject_workflow_pb2.SubjectImportStaging:
    if import_staging is None:
        return subject_workflow_pb2.SubjectImportStaging()
    return subject_workflow_pb2.SubjectImportStaging(
        source_subject_id=import_staging.source_subject_id,
        source_subject_title=import_staging.source_subject_title,
        source_subject_version_id=import_staging.source_subject_version_id,
        import_kind=import_staging.import_kind,
        selection_profile=import_staging.selection_profile,
    )


def _scenario_view_from_message(message: subject_workflow_pb2.SubjectScenarioSummary) -> SubjectWorkflowScenarioView:
    return SubjectWorkflowScenarioView(
        key=message.key,
        subject_id=message.subject_id,
        title=message.title,
        family_title=message.family_title,
        context_id=message.context_id,
        summary=message.summary,
        governance_status=message.governance_status,
        context_snapshot_hash=message.context_snapshot_hash,
        unit_count=int(message.unit_count or 0),
        admitted_unit_count=int(message.admitted_unit_count or 0),
        source_count=int(message.source_count or 0),
        delta_count=int(message.delta_count or 0),
        applied_delta_count=int(message.applied_delta_count or 0),
        import_count=int(message.import_count or 0),
        pending_import_count=int(message.pending_import_count or 0),
        reasoning_import_count=int(message.reasoning_import_count or 0),
        imported_subject_count=int(message.imported_subject_count or 0),
        context_path=message.context_path,
        subject_markdown_path=message.subject_markdown_path,
        subject_typst_path=message.subject_typst_path,
        publication_id=message.publication_id,
        publication_title=message.publication_title,
        build_id=message.build_id,
        build_status=message.build_status,
        validation_status=message.validation_status,
        build_path=message.build_path,
        publication_section_count=int(message.publication_section_count or 0),
        publication_claim_count=int(message.publication_claim_count or 0),
        publication_source_count=int(message.publication_source_count or 0),
        publication_entity_count=int(message.publication_entity_count or 0),
        publication_xref_count=int(message.publication_xref_count or 0),
        publication_review_count=int(message.publication_review_count or 0),
        report_markdown_path=message.report_markdown_path,
        report_typst_path=message.report_typst_path,
        report_pdf_path=message.report_pdf_path,
        composition_id=message.composition_id,
        composition_status=message.composition_status,
        composition_title=message.composition_title,
        composition_scope_summary=message.composition_scope_summary,
        composition_learning_context_snapshot_hash=message.composition_learning_context_snapshot_hash,
        composition_included_unit_count=int(message.composition_included_unit_count or 0),
        composition_selected_import_count=int(message.composition_selected_import_count or 0),
        composition_section_count=int(message.composition_section_count or 0),
        source_collection_count=int(message.source_collection_count or 0),
        staged_source_count=int(message.staged_source_count or 0),
        source_collection_preview_lines=tuple(message.source_collection_preview_lines),
        source_preview_lines=tuple(message.source_preview_lines),
        staged_source_preview_lines=tuple(message.staged_source_preview_lines),
        unit_preview_lines=tuple(message.unit_preview_lines),
        delta_preview_lines=tuple(message.delta_preview_lines),
        pending_import_preview_lines=tuple(message.pending_import_preview_lines),
        import_preview_lines=tuple(message.import_preview_lines),
        is_placeholder=bool(message.is_placeholder),
    )


def _key_value_row_view_from_message(message: subject_workflow_pb2.KeyValueRow) -> SubjectWorkflowKeyValueRowView:
    return SubjectWorkflowKeyValueRowView(label=message.label, value=message.value)


def _pane_item_view_from_message(
    message: subject_workflow_pb2.SubjectPaneItemView,
) -> SubjectWorkflowPaneItemView:
    return SubjectWorkflowPaneItemView(
        entry_id=message.entry_id,
        entry_kind=message.entry_kind,
        label=message.label,
        ordinal=int(message.ordinal or 0),
        parent_entry_id=message.parent_entry_id,
        depth=int(message.depth or 0),
        selectable=bool(message.selectable),
        selected=bool(message.selected),
        toggleable=bool(message.toggleable),
        check_state=message.check_state,
        held=bool(message.held),
        status=message.status,
        semantic_kind=message.semantic_kind,
        render_kind=message.render_kind,
        evidence_mode=message.evidence_mode,
        transform_mode=message.transform_mode,
        source_unit_id=message.source_unit_id,
        source_item_id=message.source_item_id,
        source_ref=message.source_ref,
        source_kind=message.source_kind,
        media_type=message.media_type,
        latest_revision_id=message.latest_revision_id,
        latest_revision_kind=message.latest_revision_kind,
        revision_count=int(message.revision_count or 0),
        bundle_file_count=int(message.bundle_file_count or 0),
        sort_kind=message.sort_kind,
        summary=message.summary,
        description=message.description,
        query_text=message.query_text,
        notes=message.notes,
        confidence=float(message.confidence or 0.0),
        related_ids=tuple(message.related_ids),
        detail_title=message.detail_title,
        detail_lines=tuple(message.detail_lines),
        attributes=tuple(_key_value_row_view_from_message(row) for row in message.attributes),
    )


def _gate_action_view_from_message(
    message: subject_workflow_pb2.SubjectGateAction,
) -> SubjectWorkflowGateActionView:
    return SubjectWorkflowGateActionView(
        display_kind="link"
        if int(message.display_kind or 0) == int(subject_workflow_pb2.SubjectGateAction.LINK)
        else "button",
        action_kind=message.action_kind,
        key=message.key,
        label=message.label,
        enabled=bool(message.enabled),
    )


def _action_spec_view_from_message(
    message: subject_workflow_pb2.SubjectActionSpec,
) -> SubjectWorkflowActionSpecView:
    return SubjectWorkflowActionSpecView(
        key=message.key,
        label=message.label,
        enabled=bool(message.enabled),
    )


def _option_view_from_message(message: subject_workflow_pb2.SubjectOption) -> SubjectWorkflowOptionView:
    return SubjectWorkflowOptionView(label=message.label, value=message.value)


def _selection_option_view_from_message(
    message: subject_workflow_pb2.SubjectSelectionOption,
) -> SubjectWorkflowSelectionOptionView:
    return SubjectWorkflowSelectionOptionView(
        label=message.label,
        value=message.value,
        selected=bool(message.selected),
    )


def _select_spec_view_from_message(
    message: subject_workflow_pb2.SubjectSelectSpecView,
) -> SubjectWorkflowSelectSpecView:
    return SubjectWorkflowSelectSpecView(
        key=message.key,
        label=message.label,
        value=message.value,
        options=tuple(_option_view_from_message(item) for item in message.options),
        enabled=bool(message.enabled),
    )


def _switch_spec_view_from_message(
    message: subject_workflow_pb2.SubjectSwitchSpecView,
) -> SubjectWorkflowSwitchSpecView:
    return SubjectWorkflowSwitchSpecView(
        key=message.key,
        label=message.label,
        value=bool(message.value),
        enabled=bool(message.enabled),
    )


def _selection_list_spec_view_from_message(
    message: subject_workflow_pb2.SubjectSelectionListSpecView,
) -> SubjectWorkflowSelectionListSpecView:
    return SubjectWorkflowSelectionListSpecView(
        key=message.key,
        label=message.label,
        action_key_prefix=message.action_key_prefix,
        options=tuple(_selection_option_view_from_message(item) for item in message.options),
        enabled=bool(message.enabled),
    )


def _table_spec_view_from_message(
    message: subject_workflow_pb2.SubjectTableSpecView,
) -> SubjectWorkflowTableSpecView:
    return SubjectWorkflowTableSpecView(
        key=message.key,
        label=message.label,
        columns=tuple(message.columns),
        rows=tuple(tuple(row.cells) for row in message.rows),
        enabled=bool(message.enabled),
    )


def _control_bundle_view_from_message(
    message: subject_workflow_pb2.SubjectControlBundleView,
) -> SubjectWorkflowControlBundleView:
    return SubjectWorkflowControlBundleView(
        phase=message.phase,
        more_actions=tuple(_action_spec_view_from_message(item) for item in message.more_actions),
        selects=tuple(_select_spec_view_from_message(item) for item in message.selects),
        switches=tuple(_switch_spec_view_from_message(item) for item in message.switches),
        selection_lists=tuple(_selection_list_spec_view_from_message(item) for item in message.selection_lists),
        tables=tuple(_table_spec_view_from_message(item) for item in message.tables),
    )


def _pane_view_from_message(message: subject_workflow_pb2.SubjectPaneView) -> SubjectWorkflowPaneView:
    return SubjectWorkflowPaneView(
        key=message.key,
        title=message.title,
        lines=tuple(message.lines),
        rows=tuple(_key_value_row_view_from_message(item) for item in message.rows),
        is_structured_table=bool(message.is_structured_table),
        items=tuple(_pane_item_view_from_message(item) for item in message.items),
    )


def _pane_bundle_view_from_message(
    message: subject_workflow_pb2.SubjectPaneBundleView,
) -> SubjectWorkflowPaneBundleView:
    return SubjectWorkflowPaneBundleView(
        phase=message.phase,
        panes=tuple(_pane_view_from_message(item) for item in message.panes),
    )


def _current_step_view_from_message(
    message: subject_workflow_pb2.SubjectCurrentStepView,
) -> SubjectWorkflowCurrentStepView:
    return SubjectWorkflowCurrentStepView(
        title=message.title,
        status=message.status,
        why=message.why,
        detail_lines=tuple(message.detail_lines),
        actions=tuple(_gate_action_view_from_message(item) for item in message.actions),
    )


def _text_section_view_from_message(message: subject_workflow_pb2.TextSection) -> SubjectWorkflowTextSectionView:
    return SubjectWorkflowTextSectionView(
        title=message.title,
        lines=tuple(message.lines),
    )


def _status_view_from_message(
    message: subject_workflow_pb2.SubjectStatusView,
) -> SubjectWorkflowStatusView:
    return SubjectWorkflowStatusView(
        title=message.title,
        rows=tuple(_key_value_row_view_from_message(item) for item in message.rows),
    )


def _phase_view_from_message(message: subject_workflow_pb2.SubjectPhaseView) -> SubjectWorkflowPhaseView:
    return SubjectWorkflowPhaseView(
        phase=message.phase,
        phase_title=message.phase_title,
        preferred_phase=message.preferred_phase,
        scenario=_scenario_view_from_message(message.scenario),
        current_step=_current_step_view_from_message(message.current_step),
        status_view=_status_view_from_message(message.status_view),
        journey_lines=tuple(message.journey_lines),
        workspace_view=_text_section_view_from_message(message.workspace_view),
        latest_receipt_title=message.latest_receipt_title,
        latest_receipt_lines=tuple(message.latest_receipt_lines),
    )


def _snapshot_view_from_message(
    message: subject_workflow_pb2.SubjectWorkflowSnapshotView,
) -> SubjectWorkflowSnapshotView:
    return SubjectWorkflowSnapshotView(
        phase_view=_phase_view_from_message(message.phase_view),
        control_bundle=_control_bundle_view_from_message(message.control_bundle),
        pane_bundle=_pane_bundle_view_from_message(message.pane_bundle),
    )


def _action_outcome_view_from_message(
    message: subject_workflow_pb2.ApplySubjectActionResponse,
) -> SubjectWorkflowActionOutcomeView:
    result = message.result
    return SubjectWorkflowActionOutcomeView(
        status_text=result.status_text,
        timeline_text=result.timeline_text,
        next_phase=result.next_phase,
        next_tab=result.next_tab,
        reload_subjects=bool(result.reload_subjects),
        open_paths=tuple(result.open_paths),
        preferred_subject_key=result.preferred_subject_key,
        phase_view=_phase_view_from_message(message.view),
        open_artifacts=tuple(
            WorkstationArtifactRefView(
                label=item.label,
                server_path=item.server_path,
                mime_type=item.mime_type,
                download_url=item.download_url,
                can_open_locally=bool(item.can_open_locally),
            )
            for item in result.open_artifacts
        ),
    )


def _watch_event_view_from_message(
    message: subject_workflow_pb2.SubjectWorkflowSnapshotUpdate,
) -> SubjectWorkflowWatchEventView:
    return SubjectWorkflowWatchEventView(
        event_kind=message.event_kind,
        snapshot=_snapshot_view_from_message(message.snapshot),
        channel_key=message.channel_key,
        sequence=int(message.sequence or 0),
        snapshot_version=message.snapshot_version,
        progress_fingerprint=message.progress_fingerprint,
    )


@dataclass
class InProcessSubjectWorkflowClient:
    service: SubjectWorkflowApiService | None = None
    client_session_id: str = ""

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = SubjectWorkflowApiService()
        if not collapse_ws(self.client_session_id):
            self.client_session_id = f"client-{uuid.uuid4().hex}"

    def list_subjects(self, *, root_path: Path) -> tuple[SubjectWorkflowScenarioView, ...]:
        return self.service.list_subjects(root_path=root_path)

    def get_phase_view(self, **kwargs) -> SubjectWorkflowPhaseView:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.get_phase_view(**kwargs)

    def get_control_bundle(self, **kwargs) -> SubjectWorkflowControlBundleView:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.get_control_bundle(**kwargs)

    def get_pane_bundle(self, **kwargs) -> SubjectWorkflowPaneBundleView:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.get_pane_bundle(**kwargs)

    def get_snapshot(self, **kwargs) -> SubjectWorkflowSnapshotView:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.get_snapshot(**kwargs)

    def apply_action(self, **kwargs) -> SubjectWorkflowActionOutcomeView:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.apply_action(**kwargs)

    def get_client_progress_json(self, **kwargs) -> str:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.get_client_progress_json(**kwargs)

    def put_client_progress_json(self, **kwargs) -> str:
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.put_client_progress_json(**kwargs)

    def apply_interaction(self, **kwargs) -> tuple[SubjectWorkflowSnapshotView, str, str]:
        kwargs.setdefault("client_session_id", self.client_session_id)
        snapshot, progress = self.service.apply_interaction(**kwargs)
        return snapshot, self.service._progress_json(progress), subject_progress_fingerprint(progress)

    def watch_subject_workflow(self, **kwargs):
        kwargs.setdefault("client_session_id", self.client_session_id)
        return self.service.watch_subject_workflow(**kwargs)


@dataclass
class GrpcSubjectWorkflowClient:
    channel: grpc.Channel
    client_session_id: str = ""

    def __post_init__(self) -> None:
        self._stub = subject_workflow_pb2_grpc.SubjectWorkflowServiceStub(self.channel)
        if not collapse_ws(self.client_session_id):
            self.client_session_id = f"client-{uuid.uuid4().hex}"

    def close(self) -> None:
        try:
            self.channel.close()
        except Exception:
            pass

    def list_subjects(self, *, root_path: Path) -> tuple[SubjectWorkflowScenarioView, ...]:
        response = self._stub.ListSubjects(
            subject_workflow_pb2.ListSubjectsRequest(root_path=str(Path(root_path).expanduser().resolve()))
        )
        return tuple(_scenario_view_from_message(item) for item in response.subjects)

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
    ) -> SubjectWorkflowPhaseView:
        response = self._stub.GetSubjectPhaseView(
            subject_workflow_pb2.GetSubjectPhaseViewRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return _phase_view_from_message(response.view)

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
    ) -> SubjectWorkflowControlBundleView:
        response = self._stub.GetSubjectControlBundle(
            subject_workflow_pb2.GetSubjectControlBundleRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return _control_bundle_view_from_message(response.bundle)

    def get_pane_bundle(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        client_session_id: str = "",
    ) -> SubjectWorkflowPaneBundleView:
        response = self._stub.GetSubjectPaneBundle(
            subject_workflow_pb2.GetSubjectPaneBundleRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return _pane_bundle_view_from_message(response.bundle)

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
    ) -> SubjectWorkflowSnapshotView:
        response = self._stub.GetSubjectWorkflowSnapshot(
            subject_workflow_pb2.GetSubjectWorkflowSnapshotRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return _snapshot_view_from_message(response.snapshot)

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
    ) -> SubjectWorkflowActionOutcomeView:
        response = self._stub.ApplySubjectAction(
            subject_workflow_pb2.ApplySubjectActionRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                action_key=collapse_ws(action_key),
                assistant_message_text=str(assistant_message_text or ""),
                subject_title_override=str(subject_title_override or ""),
                import_staging=_import_staging_message(import_staging),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return _action_outcome_view_from_message(response)

    def get_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str = "",
    ) -> str:
        response = self._stub.GetClientSubjectProgress(
            subject_workflow_pb2.GetClientSubjectProgressRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        return response.progress_json

    def put_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress_json: str,
        client_session_id: str = "",
    ) -> str:
        response = self._stub.PutClientSubjectProgress(
            subject_workflow_pb2.PutClientSubjectProgressRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
                progress_json=str(progress_json or ""),
            )
        )
        return response.progress_json

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
    ) -> tuple[SubjectWorkflowSnapshotView, str, str]:
        response = self._stub.ApplySubjectInteraction(
            subject_workflow_pb2.ApplySubjectInteractionRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
                interaction_key=collapse_ws(interaction_key),
                delta=int(delta or 0),
                target_id=str(target_id or ""),
                preview_only=bool(preview_only),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
            )
        )
        return (
            _snapshot_view_from_message(response.snapshot),
            response.progress_json,
            response.progress_fingerprint,
        )

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
    ):
        response_stream = self._stub.WatchSubjectWorkflow(
            subject_workflow_pb2.WatchSubjectWorkflowRequest(
                root_path=str(Path(root_path).expanduser().resolve()),
                subject_id=collapse_ws(subject_id),
                phase=collapse_ws(phase),
                projection_context=_projection_context_message(
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                client_session_id=collapse_ws(client_session_id) or self.client_session_id,
            )
        )
        try:
            try:
                for message in response_stream:
                    if stop_when is not None and stop_when():
                        break
                    yield _watch_event_view_from_message(message)
            except grpc.RpcError as error:
                if error.code() not in (
                    grpc.StatusCode.CANCELLED,
                    grpc.StatusCode.UNAVAILABLE,
                ):
                    raise
        finally:
            try:
                response_stream.cancel()
            except Exception:
                pass


def subject_workflow_grpc_unix_socket_target(socket_path: Path) -> str:
    resolved = Path(socket_path).expanduser().resolve()
    return f"unix://{resolved}"


def open_subject_workflow_grpc_unix_socket_channel(socket_path: Path) -> grpc.Channel:
    return grpc.insecure_channel(subject_workflow_grpc_unix_socket_target(socket_path))


def new_grpc_subject_workflow_client_for_unix_socket(
    socket_path: Path,
    *,
    client_session_id: str = "",
) -> GrpcSubjectWorkflowClient:
    return GrpcSubjectWorkflowClient(
        open_subject_workflow_grpc_unix_socket_channel(socket_path),
        client_session_id=client_session_id,
    )
