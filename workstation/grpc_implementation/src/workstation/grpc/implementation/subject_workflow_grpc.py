# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
from concurrent import futures
from pathlib import Path
from typing import Callable

import grpc

from semantic_text import collapse_ws
from workstation.contracts.subject import (
    SubjectImportStaging,
    SubjectWorkflowActionSpecView,
    SubjectWorkflowActionOutcomeView,
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
    SubjectWorkflowSnapshotView,
    SubjectWorkflowSelectionListSpecView,
    SubjectWorkflowSelectionOptionView,
    SubjectWorkflowSelectSpecView,
    SubjectWorkflowStatusView,
    SubjectWorkflowSwitchSpecView,
    SubjectWorkflowTableSpecView,
    SubjectWorkflowTextSectionView,
    SubjectWorkflowWatchEventView,
    WorkstationArtifactRefView,
)
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.grpc.definitions import subject_workflow_pb2, subject_workflow_pb2_grpc, workstation_assets_pb2
from workstation.subject.core.subject_workflow import subject_progress_fingerprint
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService


def _scenario_summary_message(view: SubjectWorkflowScenarioView) -> subject_workflow_pb2.SubjectScenarioSummary:
    return subject_workflow_pb2.SubjectScenarioSummary(
        key=view.key,
        subject_id=view.subject_id,
        title=view.title,
        family_title=view.family_title,
        context_id=view.context_id,
        summary=view.summary,
        governance_status=view.governance_status,
        context_snapshot_hash=view.context_snapshot_hash,
        unit_count=view.unit_count,
        admitted_unit_count=view.admitted_unit_count,
        source_count=view.source_count,
        delta_count=view.delta_count,
        applied_delta_count=view.applied_delta_count,
        import_count=view.import_count,
        pending_import_count=view.pending_import_count,
        reasoning_import_count=view.reasoning_import_count,
        imported_subject_count=view.imported_subject_count,
        context_path=view.context_path,
        subject_markdown_path=view.subject_markdown_path,
        subject_typst_path=view.subject_typst_path,
        publication_id=view.publication_id,
        publication_title=view.publication_title,
        build_id=view.build_id,
        build_status=view.build_status,
        validation_status=view.validation_status,
        build_path=view.build_path,
        publication_section_count=view.publication_section_count,
        publication_claim_count=view.publication_claim_count,
        publication_source_count=view.publication_source_count,
        publication_entity_count=view.publication_entity_count,
        publication_xref_count=view.publication_xref_count,
        publication_review_count=view.publication_review_count,
        report_markdown_path=view.report_markdown_path,
        report_typst_path=view.report_typst_path,
        report_pdf_path=view.report_pdf_path,
        composition_id=view.composition_id,
        composition_status=view.composition_status,
        composition_title=view.composition_title,
        composition_scope_summary=view.composition_scope_summary,
        composition_learning_context_snapshot_hash=view.composition_learning_context_snapshot_hash,
        composition_included_unit_count=view.composition_included_unit_count,
        composition_selected_import_count=view.composition_selected_import_count,
        composition_section_count=view.composition_section_count,
        source_collection_count=view.source_collection_count,
        staged_source_count=view.staged_source_count,
        source_collection_preview_lines=list(view.source_collection_preview_lines),
        source_preview_lines=list(view.source_preview_lines),
        staged_source_preview_lines=list(view.staged_source_preview_lines),
        unit_preview_lines=list(view.unit_preview_lines),
        delta_preview_lines=list(view.delta_preview_lines),
        pending_import_preview_lines=list(view.pending_import_preview_lines),
        import_preview_lines=list(view.import_preview_lines),
        is_placeholder=view.is_placeholder,
    )


def _key_value_row_message(view: SubjectWorkflowKeyValueRowView) -> subject_workflow_pb2.KeyValueRow:
    return subject_workflow_pb2.KeyValueRow(label=view.label, value=view.value)


def _pane_item_message(view: SubjectWorkflowPaneItemView) -> subject_workflow_pb2.SubjectPaneItemView:
    return subject_workflow_pb2.SubjectPaneItemView(
        entry_id=view.entry_id,
        entry_kind=view.entry_kind,
        label=view.label,
        ordinal=view.ordinal,
        parent_entry_id=view.parent_entry_id,
        depth=view.depth,
        selectable=view.selectable,
        selected=view.selected,
        toggleable=view.toggleable,
        check_state=view.check_state,
        held=view.held,
        status=view.status,
        semantic_kind=view.semantic_kind,
        render_kind=view.render_kind,
        evidence_mode=view.evidence_mode,
        transform_mode=view.transform_mode,
        source_unit_id=view.source_unit_id,
        source_item_id=view.source_item_id,
        source_ref=view.source_ref,
        source_kind=view.source_kind,
        media_type=view.media_type,
        latest_revision_id=view.latest_revision_id,
        latest_revision_kind=view.latest_revision_kind,
        revision_count=view.revision_count,
        bundle_file_count=view.bundle_file_count,
        sort_kind=view.sort_kind,
        summary=view.summary,
        description=view.description,
        query_text=view.query_text,
        notes=view.notes,
        confidence=view.confidence,
        related_ids=list(view.related_ids),
        detail_title=view.detail_title,
        detail_lines=list(view.detail_lines),
        attributes=[_key_value_row_message(row) for row in view.attributes],
    )


def _gate_action_display_kind(kind: str) -> subject_workflow_pb2.SubjectGateAction.DisplayKind:
    if collapse_ws(kind) == "link":
        return subject_workflow_pb2.SubjectGateAction.LINK
    return subject_workflow_pb2.SubjectGateAction.BUTTON


def _gate_action_message(view: SubjectWorkflowGateActionView) -> subject_workflow_pb2.SubjectGateAction:
    return subject_workflow_pb2.SubjectGateAction(
        display_kind=_gate_action_display_kind(view.display_kind),
        action_kind=view.action_kind,
        key=view.key,
        label=view.label,
        enabled=view.enabled,
    )


def _action_spec_message(view: SubjectWorkflowActionSpecView) -> subject_workflow_pb2.SubjectActionSpec:
    return subject_workflow_pb2.SubjectActionSpec(
        key=view.key,
        label=view.label,
        enabled=view.enabled,
    )


def _option_message(view: SubjectWorkflowOptionView) -> subject_workflow_pb2.SubjectOption:
    return subject_workflow_pb2.SubjectOption(label=view.label, value=view.value)


def _selection_option_message(
    view: SubjectWorkflowSelectionOptionView,
) -> subject_workflow_pb2.SubjectSelectionOption:
    return subject_workflow_pb2.SubjectSelectionOption(
        label=view.label,
        value=view.value,
        selected=view.selected,
    )


def _select_spec_message(view: SubjectWorkflowSelectSpecView) -> subject_workflow_pb2.SubjectSelectSpecView:
    return subject_workflow_pb2.SubjectSelectSpecView(
        key=view.key,
        label=view.label,
        value=view.value,
        options=[_option_message(option) for option in view.options],
        enabled=view.enabled,
    )


def _switch_spec_message(view: SubjectWorkflowSwitchSpecView) -> subject_workflow_pb2.SubjectSwitchSpecView:
    return subject_workflow_pb2.SubjectSwitchSpecView(
        key=view.key,
        label=view.label,
        value=view.value,
        enabled=view.enabled,
    )


def _selection_list_spec_message(
    view: SubjectWorkflowSelectionListSpecView,
) -> subject_workflow_pb2.SubjectSelectionListSpecView:
    return subject_workflow_pb2.SubjectSelectionListSpecView(
        key=view.key,
        label=view.label,
        action_key_prefix=view.action_key_prefix,
        options=[_selection_option_message(option) for option in view.options],
        enabled=view.enabled,
    )


def _table_spec_message(view: SubjectWorkflowTableSpecView) -> subject_workflow_pb2.SubjectTableSpecView:
    return subject_workflow_pb2.SubjectTableSpecView(
        key=view.key,
        label=view.label,
        columns=list(view.columns),
        rows=[subject_workflow_pb2.SubjectTableRow(cells=list(row)) for row in view.rows],
        enabled=view.enabled,
    )


def _control_bundle_message(
    view: SubjectWorkflowControlBundleView,
) -> subject_workflow_pb2.GetSubjectControlBundleResponse:
    return subject_workflow_pb2.GetSubjectControlBundleResponse(
        bundle=subject_workflow_pb2.SubjectControlBundleView(
            phase=view.phase,
            more_actions=[_action_spec_message(action) for action in view.more_actions],
            selects=[_select_spec_message(spec) for spec in view.selects],
            switches=[_switch_spec_message(spec) for spec in view.switches],
            selection_lists=[_selection_list_spec_message(spec) for spec in view.selection_lists],
            tables=[_table_spec_message(spec) for spec in view.tables],
        ),
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _pane_message(view: SubjectWorkflowPaneView) -> subject_workflow_pb2.SubjectPaneView:
    return subject_workflow_pb2.SubjectPaneView(
        key=view.key,
        title=view.title,
        lines=list(view.lines),
        rows=[_key_value_row_message(row) for row in view.rows],
        is_structured_table=bool(view.is_structured_table),
        items=[_pane_item_message(item) for item in view.items],
    )


def _pane_bundle_message(
    view: SubjectWorkflowPaneBundleView,
) -> subject_workflow_pb2.GetSubjectPaneBundleResponse:
    return subject_workflow_pb2.GetSubjectPaneBundleResponse(
        bundle=subject_workflow_pb2.SubjectPaneBundleView(
            phase=view.phase,
            panes=[_pane_message(pane) for pane in view.panes],
        ),
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _snapshot_view_message(view: SubjectWorkflowSnapshotView) -> subject_workflow_pb2.SubjectWorkflowSnapshotView:
    return subject_workflow_pb2.SubjectWorkflowSnapshotView(
        phase_view=_phase_view_message(view.phase_view),
        control_bundle=_control_bundle_message(view.control_bundle).bundle,
        pane_bundle=_pane_bundle_message(view.pane_bundle).bundle,
    )


def _snapshot_response_message(
    view: SubjectWorkflowSnapshotView,
) -> subject_workflow_pb2.GetSubjectWorkflowSnapshotResponse:
    return subject_workflow_pb2.GetSubjectWorkflowSnapshotResponse(
        snapshot=_snapshot_view_message(view),
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _snapshot_update_message(
    view: SubjectWorkflowWatchEventView,
) -> subject_workflow_pb2.SubjectWorkflowSnapshotUpdate:
    return subject_workflow_pb2.SubjectWorkflowSnapshotUpdate(
        event_kind=view.event_kind,
        snapshot=_snapshot_view_message(view.snapshot),
        channel_key=view.channel_key,
        sequence=int(view.sequence or 0),
        snapshot_version=view.snapshot_version,
        progress_fingerprint=view.progress_fingerprint,
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _current_step_message(view: SubjectWorkflowCurrentStepView) -> subject_workflow_pb2.SubjectCurrentStepView:
    return subject_workflow_pb2.SubjectCurrentStepView(
        title=view.title,
        status=view.status,
        why=view.why,
        detail_lines=list(view.detail_lines),
        actions=[_gate_action_message(action) for action in view.actions],
    )


def _text_section_message(view: SubjectWorkflowTextSectionView) -> subject_workflow_pb2.TextSection:
    return subject_workflow_pb2.TextSection(title=view.title, lines=list(view.lines))


def _status_view_message(view: SubjectWorkflowStatusView) -> subject_workflow_pb2.SubjectStatusView:
    return subject_workflow_pb2.SubjectStatusView(
        title=view.title,
        rows=[_key_value_row_message(row) for row in view.rows],
    )


def _phase_view_message(view: SubjectWorkflowPhaseView) -> subject_workflow_pb2.SubjectPhaseView:
    return subject_workflow_pb2.SubjectPhaseView(
        phase=view.phase,
        phase_title=view.phase_title,
        preferred_phase=view.preferred_phase,
        scenario=_scenario_summary_message(view.scenario),
        current_step=_current_step_message(view.current_step),
        status_view=_status_view_message(view.status_view),
        journey_lines=list(view.journey_lines),
        workspace_view=_text_section_message(view.workspace_view),
        latest_receipt_title=view.latest_receipt_title,
        latest_receipt_lines=list(view.latest_receipt_lines),
    )


def _artifact_ref_message(view: WorkstationArtifactRefView) -> workstation_assets_pb2.ArtifactRef:
    return workstation_assets_pb2.ArtifactRef(
        label=view.label,
        server_path=view.server_path,
        mime_type=view.mime_type,
        download_url=view.download_url,
        can_open_locally=bool(view.can_open_locally),
    )


def _action_outcome_message(
    view: SubjectWorkflowActionOutcomeView,
    *,
    open_artifacts: tuple[WorkstationArtifactRefView, ...] = (),
) -> subject_workflow_pb2.ApplySubjectActionResponse:
    return subject_workflow_pb2.ApplySubjectActionResponse(
        result=subject_workflow_pb2.SubjectActionResult(
            status_text=view.status_text,
            timeline_text=view.timeline_text,
            next_phase=view.next_phase,
            next_tab=view.next_tab,
            reload_subjects=view.reload_subjects,
            open_paths=list(view.open_paths),
            preferred_subject_key=view.preferred_subject_key,
            open_artifacts=[_artifact_ref_message(item) for item in (open_artifacts or view.open_artifacts)],
        ),
        view=_phase_view_message(view.phase_view),
        trace_id=view.trace_id,
        parent_id=view.parent_id,
    )


def _import_staging_from_message(
    message: subject_workflow_pb2.SubjectImportStaging | None,
) -> SubjectImportStaging | None:
    if message is None:
        return None
    if not collapse_ws(message.source_subject_id):
        return None
    return SubjectImportStaging(
        source_subject_id=message.source_subject_id,
        source_subject_title=message.source_subject_title,
        source_subject_version_id=message.source_subject_version_id,
        import_kind=message.import_kind or "definition_support",
        selection_profile=message.selection_profile or "units_only",
    )


def _projection_context_kwargs(
    message: subject_workflow_pb2.SubjectPhaseProjectionContext | None,
) -> dict[str, object]:
    if message is None:
        return {}
    return {
        "can_capture_assistant": bool(message.can_capture_assistant),
        "markdown_selected_path": message.markdown_selected_path,
        "markdown_status_text": message.markdown_status_text,
        "markdown_busy": bool(message.markdown_busy),
    }


def _registered_trace_fields(
    *,
    message_kind: str,
    prefix: str,
    parent_id: str = "",
    components: tuple[object, ...] = (),
) -> tuple[str, str]:
    trace_id = (
        derived_trace_id(prefix, *(components or (parent_id or new_trace_id(prefix),)))
        if components
        else new_trace_id(prefix)
    )
    return register_message_trace(
        trace_id=trace_id,
        parent_id=parent_id,
        message_kind=message_kind,
    )


class SubjectWorkflowGrpcService(subject_workflow_pb2_grpc.SubjectWorkflowServiceServicer):
    def __init__(
        self,
        service: SubjectWorkflowApiService | None = None,
        *,
        artifact_ref_resolver: Callable[[Path, str, tuple[str, ...]], tuple[WorkstationArtifactRefView, ...]] | None = None,
        root_initializer: Callable[[Path], Path] | None = None,
    ) -> None:
        self._service = service or SubjectWorkflowApiService()
        self._artifact_ref_resolver = artifact_ref_resolver
        self._root_initializer = root_initializer

    def _ready_root_path(self, root_path: str | Path) -> Path:
        resolved = Path(root_path).expanduser().resolve()
        if self._root_initializer is not None:
            return self._root_initializer(resolved)
        return resolved

    def ListSubjects(
        self,
        request: subject_workflow_pb2.ListSubjectsRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.ListSubjectsResponse:
        del context
        subjects = self._service.list_subjects(root_path=self._ready_root_path(request.root_path))
        parent_id = new_trace_id("subject-list-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="ListSubjectsResponse",
            prefix="subject-list-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, len(subjects)),
        )
        return subject_workflow_pb2.ListSubjectsResponse(
            subjects=[_scenario_summary_message(item) for item in subjects],
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def GetSubjectPhaseView(
        self,
        request: subject_workflow_pb2.GetSubjectPhaseViewRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.GetSubjectPhaseViewResponse:
        try:
            view = self._service.get_phase_view(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
                **_projection_context_kwargs(request.projection_context),
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return subject_workflow_pb2.GetSubjectPhaseViewResponse(
            view=_phase_view_message(view),
            trace_id=view.trace_id,
            parent_id=view.parent_id,
        )

    def GetSubjectControlBundle(
        self,
        request: subject_workflow_pb2.GetSubjectControlBundleRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.GetSubjectControlBundleResponse:
        try:
            view = self._service.get_control_bundle(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
                **_projection_context_kwargs(request.projection_context),
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return _control_bundle_message(view)

    def GetSubjectPaneBundle(
        self,
        request: subject_workflow_pb2.GetSubjectPaneBundleRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.GetSubjectPaneBundleResponse:
        try:
            view = self._service.get_pane_bundle(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return _pane_bundle_message(view)

    def GetSubjectWorkflowSnapshot(
        self,
        request: subject_workflow_pb2.GetSubjectWorkflowSnapshotRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.GetSubjectWorkflowSnapshotResponse:
        try:
            view = self._service.get_snapshot(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
                **_projection_context_kwargs(request.projection_context),
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        return _snapshot_response_message(view)

    def WatchSubjectWorkflow(
        self,
        request: subject_workflow_pb2.WatchSubjectWorkflowRequest,
        context: grpc.ServicerContext,
    ):
        try:
            for event_view in self._service.watch_subject_workflow(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
                stop_when=lambda: not context.is_active(),
                **_projection_context_kwargs(request.projection_context),
            ):
                yield _snapshot_update_message(event_view)
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def ApplySubjectAction(
        self,
        request: subject_workflow_pb2.ApplySubjectActionRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.ApplySubjectActionResponse:
        try:
            result = self._service.apply_action(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                action_key=request.action_key,
                client_session_id=request.client_session_id,
                assistant_message_text=request.assistant_message_text,
                subject_title_override=request.subject_title_override,
                import_staging=_import_staging_from_message(request.import_staging),
                **_projection_context_kwargs(request.projection_context),
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        open_artifacts = (
            self._artifact_ref_resolver(
                self._ready_root_path(request.root_path),
                request.client_session_id,
                result.open_paths,
            )
            if self._artifact_ref_resolver is not None
            else result.open_artifacts
        )
        return _action_outcome_message(result, open_artifacts=open_artifacts)

    def GetClientSubjectProgress(
        self,
        request: subject_workflow_pb2.GetClientSubjectProgressRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.GetClientSubjectProgressResponse:
        try:
            progress_json = self._service.get_client_progress_json(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                client_session_id=request.client_session_id,
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        parent_id = new_trace_id("subject-progress-get-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="GetClientSubjectProgressResponse",
            prefix="subject-progress-get-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, request.subject_id, request.client_session_id, progress_json),
        )
        return subject_workflow_pb2.GetClientSubjectProgressResponse(
            progress_json=progress_json,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def PutClientSubjectProgress(
        self,
        request: subject_workflow_pb2.PutClientSubjectProgressRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.PutClientSubjectProgressResponse:
        try:
            progress_json = self._service.put_client_progress_json(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                client_session_id=request.client_session_id,
                progress_json=request.progress_json,
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        parent_id = new_trace_id("subject-progress-put-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="PutClientSubjectProgressResponse",
            prefix="subject-progress-put-response",
            parent_id=parent_id,
            components=(parent_id, request.root_path, request.subject_id, request.client_session_id, progress_json),
        )
        return subject_workflow_pb2.PutClientSubjectProgressResponse(
            progress_json=progress_json,
            trace_id=trace_id,
            parent_id=parent_id,
        )

    def ApplySubjectInteraction(
        self,
        request: subject_workflow_pb2.ApplySubjectInteractionRequest,
        context: grpc.ServicerContext,
    ) -> subject_workflow_pb2.ApplySubjectInteractionResponse:
        try:
            snapshot, progress = self._service.apply_interaction(
                root_path=self._ready_root_path(request.root_path),
                subject_id=request.subject_id,
                phase=request.phase,
                client_session_id=request.client_session_id,
                interaction_key=request.interaction_key,
                delta=int(request.delta or 0),
                target_id=request.target_id,
                preview_only=bool(request.preview_only),
                **_projection_context_kwargs(request.projection_context),
            )
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        progress_json = self._service._progress_json(progress)
        parent_id = new_trace_id("subject-interaction-request")
        trace_id, parent_id = _registered_trace_fields(
            message_kind="ApplySubjectInteractionResponse",
            prefix="subject-interaction-response",
            parent_id=parent_id,
            components=(
                parent_id,
                request.root_path,
                request.subject_id,
                request.phase,
                request.client_session_id,
                request.interaction_key,
                request.delta,
                request.target_id,
                progress_json,
            ),
        )
        return subject_workflow_pb2.ApplySubjectInteractionResponse(
            snapshot=_snapshot_view_message(snapshot),
            progress_json=progress_json,
            progress_fingerprint=subject_progress_fingerprint(progress),
            trace_id=trace_id,
            parent_id=parent_id,
        )


def build_subject_workflow_grpc_server(
    *,
    service: SubjectWorkflowApiService | None = None,
    max_workers: int = 4,
) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    subject_workflow_pb2_grpc.add_SubjectWorkflowServiceServicer_to_server(
        SubjectWorkflowGrpcService(service=service),
        server,
    )
    return server


def bind_subject_workflow_grpc_server_unix_socket(
    server: grpc.Server,
    *,
    socket_path: Path,
) -> int:
    resolved = Path(socket_path).expanduser().resolve()
    try:
        os.unlink(resolved)
    except FileNotFoundError:
        pass
    return server.add_insecure_port(f"unix://{resolved}")
