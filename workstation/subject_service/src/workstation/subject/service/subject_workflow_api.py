# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from queue import Empty, Queue
from dataclasses import dataclass, field
from typing import Callable, Iterator

from realized_core_semantics.semantic_text import collapse_ws
from workstation.contracts.subject import (
    SubjectImportStaging,
    SubjectWorkflowActionOutcomeView,
    SubjectWorkflowActionSpecView,
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
from workstation.foundation.events.event_bus import publish_workstation_event, workstation_event_bus
from workstation.foundation.events.message_tracing import derived_trace_id, new_trace_id, register_message_trace
from workstation.subject.core.subject_workflow import (
    SubjectActionSpec,
    SubjectActionResult,
    SubjectCurrentStepView,
    SubjectGateAction,
    SubjectProgress,
    SubjectScenario,
    SubjectSelectionListSpec,
    SubjectSelectSpec,
    SubjectSwitchSpec,
    SubjectTableSpec,
    apply_subject_action,
    render_subject_journey,
    render_subject_itemize_detail,
    render_subject_itemize_inventory,
    render_subject_itemize_target,
    render_subject_draft_detail,
    render_subject_draft_issue_tray,
    render_subject_draft_model_main,
    render_subject_draft_tree,
    render_subject_report_scope_detail,
    render_subject_report_scope_tree,
    render_subject_research_observation,
    render_subject_research_sources,
    render_subject_research_target,
    render_subject_workspace,
    sanitized_subject_progress_for_persistence,
    subject_draft_detail_title,
    subject_draft_detail_rows,
    subject_draft_review_inventory,
    subject_draft_model_main_title,
    subject_draft_result_title,
    subject_draft_tree_title,
    subject_current_step_actions,
    subject_current_step_view,
    subject_draft_decision_included_switch_spec,
    subject_draft_evidence_mode_select_spec,
    subject_draft_model_construct_lane_select_spec,
    subject_draft_model_construct_sort_select_spec,
    subject_draft_model_construct_inventory,
    subject_draft_model_policy_profile_select_spec,
    subject_draft_model_relation_selection_list_specs,
    subject_draft_model_transition_source_select_spec,
    subject_draft_model_transition_target_select_spec,
    subject_draft_render_kind_select_spec,
    subject_draft_semantic_kind_select_spec,
    subject_draft_transform_mode_select_spec,
    subject_guidance_phase,
    subject_itemize_decision_role_select_spec,
    subject_itemize_hold_switch_spec,
    subject_itemize_detail_title,
    subject_more_action_specs,
    subject_phase_title,
    subject_publication_build_artifacts_table_spec,
    subject_publication_build_receipt_table_spec,
    subject_publication_import_included_switch_spec,
    subject_publication_import_target_select_spec,
    subject_publication_import_usage_select_spec,
    subject_publication_latest_receipt_table_spec,
    subject_research_selected_source_change_summary_table_spec,
    subject_research_selected_source_collection_membership_switch_spec,
    subject_research_selected_source_revision_history_table_spec,
    subject_research_source_collection_actionable_export_table_spec,
    subject_research_source_collection_export_applied_table_spec,
    subject_research_source_collection_member_export_status_table_spec,
    subject_research_source_collection_member_revision_table_spec,
    subject_research_source_collection_merge_export_history_table_spec,
    subject_research_source_collection_select_spec,
    subject_research_source_inventory,
    subject_research_target_title,
    subject_research_source_revision_baseline_select_spec,
    subject_review_comparison_history_table_spec,
    subject_review_composition_unit_included_switch_spec,
    subject_review_composition_unit_target_select_spec,
    subject_review_latest_receipt_table_spec,
    subject_review_publication_diff_baseline_select_spec,
    subject_review_publication_output_mode_select_spec,
    subject_review_publication_section_included_switch_spec,
    subject_review_publication_section_plan_select_spec,
    subject_review_publication_section_target_select_spec,
    subject_report_scope_detail_title,
    source_collection_option_label,
    subject_workflow_request_cache,
    subject_progress_client_view_payload,
    subject_status_rows,
    subject_progress_fingerprint,
    subject_progress_from_dict,
    subject_progress_to_dict,
    move_draft_review_cursor,
    move_itemize_cursor,
    move_research_source_cursor,
    move_report_scope_cursor,
    preview_move_held_report_scope_items,
    _draft_focus_mode,
    _itemization_session_and_items,
    _report_scope_entries,
    _report_section_spec_by_id,
    _selected_itemization_item,
    _selected_report_scope_entry,
    _selected_transformation_construct_candidate,
    _subject_transformation_construct_candidates,
    _valid_itemize_held_item_ids,
    _set_draft_selection_to_construct_candidate_id,
    _set_draft_selection_to_review_item_id,
    _stable_json_hash,
)
from workstation.subject.core.subject_workflow_repository import SubjectWorkflowRepository
from workstation.subject.core.host_actions import (
    SubjectWorkflowHostActions,
    UnavailableSubjectWorkflowHostActions,
)
from workstation.subject.service.client_sessions import WorkstationClientSessionRegistry


def _registered_trace(
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


def _normalized_phase(phase: str) -> str:
    normalized = collapse_ws(phase).casefold()
    if normalized in {"research", "itemize", "draft", "review", "publication"}:
        return normalized
    return "research"


def _subject_workflow_snapshot_version(
    *,
    subject_id: str,
    phase: str,
    progress_fingerprint: str,
    snapshot: SubjectWorkflowSnapshotView,
) -> str:
    scenario = getattr(getattr(snapshot, "phase_view", None), "scenario", None)
    context_snapshot_hash = collapse_ws(str(getattr(scenario, "context_snapshot_hash", "")))
    return _stable_json_hash(
        {
            "subject_id": collapse_ws(subject_id),
            "phase": collapse_ws(phase),
            "progress_fingerprint": collapse_ws(progress_fingerprint),
            "context_snapshot_hash": context_snapshot_hash,
        }
    )[:16]


def _local_artifact_ref_view_from_path(path_text: str) -> WorkstationArtifactRefView:
    resolved = Path(str(path_text or "")).expanduser().resolve()
    mime_type, _ = mimetypes.guess_type(str(resolved))
    label = resolved.name or resolved.as_posix()
    return WorkstationArtifactRefView(
        label=label,
        server_path=str(resolved),
        mime_type=mime_type or ("inode/directory" if resolved.is_dir() else "application/octet-stream"),
        download_url="",
        can_open_locally=resolved.exists(),
    )


def _scenario_view_from_scenario(scenario: SubjectScenario) -> SubjectWorkflowScenarioView:
    return SubjectWorkflowScenarioView(
        key=scenario.key,
        subject_id=scenario.subject_id,
        title=scenario.title,
        family_title=scenario.family_title,
        context_id=scenario.context_id,
        summary=scenario.summary,
        governance_status=scenario.governance_status,
        context_snapshot_hash=scenario.context_snapshot_hash,
        unit_count=int(scenario.unit_count or 0),
        admitted_unit_count=int(scenario.admitted_unit_count or 0),
        source_count=int(scenario.source_count or 0),
        delta_count=int(scenario.delta_count or 0),
        applied_delta_count=int(scenario.applied_delta_count or 0),
        import_count=int(scenario.import_count or 0),
        pending_import_count=int(scenario.pending_import_count or 0),
        reasoning_import_count=int(scenario.reasoning_import_count or 0),
        imported_subject_count=int(scenario.imported_subject_count or 0),
        context_path=scenario.context_path,
        subject_markdown_path=scenario.subject_markdown_path,
        subject_typst_path=scenario.subject_typst_path,
        publication_id=scenario.publication_id,
        publication_title=scenario.publication_title,
        build_id=scenario.build_id,
        build_status=scenario.build_status,
        validation_status=scenario.validation_status,
        build_path=scenario.build_path,
        publication_section_count=int(scenario.publication_section_count or 0),
        publication_claim_count=int(scenario.publication_claim_count or 0),
        publication_source_count=int(scenario.publication_source_count or 0),
        publication_entity_count=int(scenario.publication_entity_count or 0),
        publication_xref_count=int(scenario.publication_xref_count or 0),
        publication_review_count=int(scenario.publication_review_count or 0),
        report_markdown_path=scenario.report_markdown_path,
        report_typst_path=scenario.report_typst_path,
        report_pdf_path=scenario.report_pdf_path,
        composition_id=scenario.composition_id,
        composition_status=scenario.composition_status,
        composition_title=scenario.composition_title,
        composition_scope_summary=scenario.composition_scope_summary,
        composition_learning_context_snapshot_hash=scenario.composition_learning_context_snapshot_hash,
        composition_included_unit_count=int(scenario.composition_included_unit_count or 0),
        composition_selected_import_count=int(scenario.composition_selected_import_count or 0),
        composition_section_count=int(scenario.composition_section_count or 0),
        source_collection_count=int(scenario.source_collection_count or 0),
        staged_source_count=int(scenario.staged_source_count or 0),
        source_collection_preview_lines=tuple(str(line) for line in scenario.source_collection_preview_lines),
        source_preview_lines=tuple(str(line) for line in scenario.source_preview_lines),
        staged_source_preview_lines=tuple(str(line) for line in scenario.staged_source_preview_lines),
        unit_preview_lines=tuple(str(line) for line in scenario.unit_preview_lines),
        delta_preview_lines=tuple(str(line) for line in scenario.delta_preview_lines),
        pending_import_preview_lines=tuple(str(line) for line in scenario.pending_import_preview_lines),
        import_preview_lines=tuple(str(line) for line in scenario.import_preview_lines),
        is_placeholder=bool(scenario.is_placeholder),
    )


def _display_kind_for_action(action: SubjectGateAction) -> str:
    if collapse_ws(action.kind) in {"phase_nav", "subject_nav"}:
        return "link"
    return "button"


def _gate_action_view_from_action(action: SubjectGateAction) -> SubjectWorkflowGateActionView:
    return SubjectWorkflowGateActionView(
        display_kind=_display_kind_for_action(action),
        action_kind=collapse_ws(action.kind),
        key=collapse_ws(action.key),
        label=action.label,
        enabled=bool(action.enabled),
    )


def _action_spec_view(key: str, spec: SubjectActionSpec) -> SubjectWorkflowActionSpecView:
    return SubjectWorkflowActionSpecView(
        key=collapse_ws(key) or collapse_ws(spec.key),
        label=spec.label,
        enabled=bool(spec.enabled),
    )


def _select_spec_view(key: str, spec: SubjectSelectSpec) -> SubjectWorkflowSelectSpecView:
    return SubjectWorkflowSelectSpecView(
        key=collapse_ws(key),
        label=spec.label,
        value=spec.value,
        options=tuple(
            SubjectWorkflowOptionView(label=str(label or ""), value=str(value or ""))
            for label, value in spec.options
        ),
        enabled=bool(spec.enabled),
    )


def _switch_spec_view(key: str, spec: SubjectSwitchSpec) -> SubjectWorkflowSwitchSpecView:
    return SubjectWorkflowSwitchSpecView(
        key=collapse_ws(key),
        label=spec.label,
        value=bool(spec.value),
        enabled=bool(spec.enabled),
    )


def _selection_list_spec_view(key: str, spec: SubjectSelectionListSpec) -> SubjectWorkflowSelectionListSpecView:
    return SubjectWorkflowSelectionListSpecView(
        key=collapse_ws(key),
        label=spec.label,
        action_key_prefix=spec.action_key_prefix,
        options=tuple(
            SubjectWorkflowSelectionOptionView(
                label=str(label or ""),
                value=str(value or ""),
                selected=bool(selected),
            )
            for label, value, selected in spec.options
        ),
        enabled=bool(spec.enabled),
    )


def _table_spec_view(key: str, spec: SubjectTableSpec) -> SubjectWorkflowTableSpecView:
    return SubjectWorkflowTableSpecView(
        key=collapse_ws(key),
        label=spec.label,
        columns=tuple(str(column or "") for column in spec.columns),
        rows=tuple(tuple(str(cell or "") for cell in row) for row in spec.rows),
        enabled=bool(spec.enabled),
    )


def _pane_view(
    key: str,
    title: str,
    text: str,
    *,
    is_structured_table: bool = False,
    rows: tuple[SubjectWorkflowKeyValueRowView, ...] = (),
    items: tuple[SubjectWorkflowPaneItemView, ...] = (),
) -> SubjectWorkflowPaneView:
    lines = _lines_from_rendered_text(text)
    return SubjectWorkflowPaneView(
        key=collapse_ws(key),
        title=str(title or ""),
        lines=lines,
        rows=rows,
        is_structured_table=bool(is_structured_table),
        items=items,
    )


def _current_step_view_from_step(
    step: SubjectCurrentStepView,
    actions: tuple[SubjectGateAction, ...],
) -> SubjectWorkflowCurrentStepView:
    return SubjectWorkflowCurrentStepView(
        title=step.title,
        status=step.status,
        why=step.why,
        detail_lines=tuple(str(item) for item in step.detail_lines),
        actions=tuple(_gate_action_view_from_action(action) for action in actions),
    )


def _status_view_for_phase(
    *,
    scenario: SubjectScenario,
    progress: SubjectProgress,
    phase: str,
) -> SubjectWorkflowStatusView:
    rows = tuple(
        SubjectWorkflowKeyValueRowView(label=label, value=value)
        for label, value in subject_status_rows(
            scenario=scenario,
            progress=progress,
            phase=phase,
        )
    )
    return SubjectWorkflowStatusView(
        title=f"{subject_phase_title(phase)} Status",
        rows=rows,
    )


def _workspace_title_for_phase(phase: str) -> str:
    phase_title = subject_phase_title(phase)
    if phase == "research":
        return "Gather Journal"
    return f"{phase_title} Journal"


def _lines_from_rendered_text(text: str) -> tuple[str, ...]:
    return tuple(str(line) for line in str(text or "").splitlines())


def _attributes(*rows: tuple[str, object]) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    return tuple(
        SubjectWorkflowKeyValueRowView(label=str(label), value=str(value))
        for label, value in rows
        if collapse_ws(str(label))
    )


def _selected_pane_item(
    items: tuple[SubjectWorkflowPaneItemView, ...],
) -> SubjectWorkflowPaneItemView | None:
    return next((item for item in items if item.selected), None)


def _pane_item_attribute(item: SubjectWorkflowPaneItemView, key: str) -> str:
    normalized_key = collapse_ws(key)
    return next(
        (
            row.value
            for row in item.attributes
            if collapse_ws(row.label) == normalized_key
        ),
        "",
    )


def _display_token(value: object, *, fallback: str = "<none>") -> str:
    normalized = collapse_ws(str(value or ""))
    return normalized.replace("_", " ").title() if normalized else fallback


def _research_observation_rows(scenario: SubjectScenario) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    """Project stable research facts without decoding their rendered prose."""
    if scenario.is_placeholder:
        return _attributes(("Subject summary", "No subject exists yet."))
    return _attributes(
        ("Subject summary", scenario.summary or "<none>"),
        ("Items", scenario.admitted_unit_count),
        ("Total items", scenario.unit_count),
        ("Sources", scenario.source_count),
        ("Applied deltas", f"{scenario.applied_delta_count} of {scenario.delta_count}"),
        ("Active support", scenario.reasoning_import_count),
    )


def _research_source_pane_items(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    progress: SubjectProgress,
) -> tuple[SubjectWorkflowPaneItemView, ...]:
    collections, selected_collection, sources, workbench_rows = subject_research_source_inventory(
        root_path=root_path,
        scenario=scenario,
        progress=progress,
    )
    selected_collection_id = collapse_ws(
        getattr(selected_collection, "collection_id", "") if selected_collection is not None else ""
    )
    selected_source_id = collapse_ws(progress.research_selected_staged_source_id)
    if selected_source_id and all(
        collapse_ws(source.staged_source_id) != selected_source_id
        for source, _revision in sources
    ):
        selected_source_id = ""
    if not selected_source_id and sources:
        selected_source_id = collapse_ws(
            sources[max(0, min(len(sources) - 1, int(progress.research_source_cursor or 0)))][0].staged_source_id
        )
    items: list[SubjectWorkflowPaneItemView] = []
    for ordinal, collection in enumerate(collections):
        collection_id = collapse_ws(collection.collection_id)
        selected = collection_id == selected_collection_id
        attributes = [
            ("source_count", len(collection.staged_source_ids)),
            ("collection_kind", collapse_ws(str(collection.metadata.get("collection_kind", "")))),
        ]
        if selected:
            attributes.extend(workbench_rows)
        items.append(
            SubjectWorkflowPaneItemView(
                entry_id=collection_id,
                entry_kind="source_collection",
                label=source_collection_option_label(collection),
                ordinal=ordinal,
                selected=selected,
                related_ids=tuple(collection.staged_source_ids),
                description=collection.description,
                query_text=collection.query_text,
                attributes=_attributes(*attributes),
            )
        )
    selected_collection_source_ids = {
        collapse_ws(item)
        for item in getattr(selected_collection, "staged_source_ids", ())
        if collapse_ws(item)
    }
    for ordinal, (source, revision) in enumerate(sources):
        source_id = collapse_ws(source.staged_source_id)
        items.append(
            SubjectWorkflowPaneItemView(
                entry_id=source_id,
                entry_kind="staged_source",
                label=collapse_ws(source.title) or source_id,
                ordinal=ordinal,
                parent_entry_id=selected_collection_id,
                depth=1,
                selectable=True,
                selected=source_id == selected_source_id,
                status=source.status,
                source_ref=source.source_ref,
                source_kind=source.source_kind,
                media_type=source.media_type,
                latest_revision_id=source.latest_revision_id,
                latest_revision_kind=(revision.revision_kind if revision is not None else ""),
                revision_count=int(source.revision_count or 0),
                bundle_file_count=(len(revision.bundle_relpaths) if revision is not None else 0),
                attributes=_attributes(
                    ("in_selected_collection", source_id in selected_collection_source_ids),
                ),
            )
        )
    return tuple(items)


def _itemize_pane_items(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    progress: SubjectProgress,
) -> tuple[SubjectWorkflowPaneItemView, ...]:
    _session, items = _itemization_session_and_items(root_path, scenario)
    selected = _selected_itemization_item(root_path, scenario=scenario, progress=progress)
    selected_id = collapse_ws(selected.itemized_item_id) if selected is not None else ""
    held_ids = set(_valid_itemize_held_item_ids(items=items, progress=progress))
    return tuple(
        SubjectWorkflowPaneItemView(
            entry_id=collapse_ws(item.itemized_item_id),
            entry_kind="itemized_item",
            label=collapse_ws(item.canonical_label) or item.itemized_item_id,
            ordinal=ordinal,
            selectable=True,
            selected=collapse_ws(item.itemized_item_id) == selected_id,
            toggleable=True,
            check_state="checked" if collapse_ws(item.itemized_item_id) in held_ids else "unchecked",
            held=collapse_ws(item.itemized_item_id) in held_ids,
            status=item.status,
            semantic_kind=item.item_kind,
            source_unit_id=item.source_unit_id,
            summary=item.summary,
            confidence=float(item.confidence or 0.0),
            related_ids=tuple(item.linked_item_ids),
            attributes=_attributes(
                ("decision_role", item.metadata.get("decision_role", "")),
                ("aliases", " | ".join(item.aliases)),
                ("source_refs", " | ".join(item.source_refs)),
            ),
        )
        for ordinal, item in enumerate(items)
    )


def _itemize_detail_rows(
    items: tuple[SubjectWorkflowPaneItemView, ...],
) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    selected = _selected_pane_item(items)
    if selected is None:
        return _attributes(("Item detail", "No itemized candidates are available yet."))
    rows: list[tuple[str, object]] = [
        ("Kind", selected.semantic_kind or "<none>"),
        ("Status", selected.status or "<none>"),
        ("Confidence", f"{selected.confidence:.2f}"),
        ("Source unit", selected.source_unit_id or "<none>"),
        ("Item id", selected.entry_id or "<none>"),
        ("Held for merge", "yes" if selected.held else "no"),
        ("Summary", selected.summary or "<none>"),
        ("Aliases", _pane_item_attribute(selected, "aliases") or "<none>"),
        ("Source refs", _pane_item_attribute(selected, "source_refs") or "<none>"),
    ]
    decision_role = _pane_item_attribute(selected, "decision_role")
    if decision_role:
        rows.append(("Decision role", decision_role))
    return _attributes(*rows)


def _itemize_target_rows(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    items: tuple[SubjectWorkflowPaneItemView, ...],
) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    if scenario.is_placeholder:
        return _attributes(("Itemize target", "Itemize sits between Gather and Draft."))
    construct_count = len(
        _subject_transformation_construct_candidates(
            root_path,
            scenario,
            include_rejected=False,
        )
    )
    return _attributes(
        ("Itemize Target", "Draft Handoff"),
        ("Subject", scenario.title),
        ("Context", scenario.context_path or "<missing>"),
        ("Item count", len(items)),
        ("Transformation constructs", construct_count),
        ("Promoted", sum(1 for item in items if collapse_ws(item.status) == "promoted")),
        ("Rejected", sum(1 for item in items if collapse_ws(item.status) == "rejected")),
        ("Held", sum(1 for item in items if item.held)),
    )


def _draft_pane_items(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    progress: SubjectProgress,
) -> tuple[SubjectWorkflowPaneItemView, ...]:
    if _draft_focus_mode(progress) == "model":
        candidate_inventory = subject_draft_model_construct_inventory(
            root_path,
            scenario=scenario,
        )
        selected = _selected_transformation_construct_candidate(
            root_path,
            scenario=scenario,
            progress=progress,
            include_rejected=False,
        )
        selected_id = collapse_ws(selected.construct_candidate_id) if selected is not None else ""
        return tuple(
            SubjectWorkflowPaneItemView(
                entry_id=collapse_ws(candidate.construct_candidate_id),
                entry_kind="construct_candidate",
                label=collapse_ws(candidate.canonical_label) or candidate.construct_candidate_id,
                ordinal=ordinal,
                selectable=True,
                selected=collapse_ws(candidate.construct_candidate_id) == selected_id,
                status=candidate.status,
                source_item_id=candidate.itemized_item_id,
                sort_kind=candidate.sort_kind,
                summary=candidate.summary,
                notes=candidate.notes,
                confidence=float(candidate.confidence or 0.0),
                related_ids=tuple(candidate.source_refs),
                attributes=_attributes(
                    ("review_item_id", candidate.review_item_id),
                    ("lane", lane),
                ),
            )
            for ordinal, (candidate, lane) in enumerate(candidate_inventory)
        )
    flattened, selected_id, decision_included_ids, statements = subject_draft_review_inventory(
        root_path=root_path,
        scenario=scenario,
        progress=progress,
    )
    decision_included = set(decision_included_ids)
    return tuple(
        SubjectWorkflowPaneItemView(
            entry_id=collapse_ws(item.review_item_id),
            entry_kind="draft_review_item",
            label=(collapse_ws(str(item.metadata.get("canonical_label", ""))) or item.review_item_id),
            ordinal=ordinal,
            parent_entry_id=item.parent_review_item_id,
            depth=max(0, int(depth)),
            selectable=True,
            selected=collapse_ws(item.review_item_id) == selected_id,
            toggleable=True,
            check_state="checked" if item.included else "unchecked",
            status=item.status,
            semantic_kind=item.semantic_kind,
            render_kind=item.render_kind,
            evidence_mode=item.evidence_mode,
            transform_mode=item.transform_mode,
            source_unit_id=item.source_unit_id,
            source_item_id=item.source_itemized_item_id,
            notes=item.notes,
            related_ids=tuple(item.child_review_item_ids),
            attributes=_attributes(
                ("in_decision", collapse_ws(item.review_item_id) in decision_included),
                ("source_statement", statements.get(collapse_ws(item.source_unit_id), "")),
                ("source_refs", " | ".join(item.source_refs)),
            ),
        )
        for ordinal, (item, depth) in enumerate(flattened)
    )


def _draft_model_rows(
    *,
    scenario: SubjectScenario,
    progress: SubjectProgress,
    items: tuple[SubjectWorkflowPaneItemView, ...],
) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    if scenario.is_placeholder:
        return _attributes(("Transformation model", "Open or create a subject first."))
    if _draft_focus_mode(progress) != "model":
        return _attributes(("Transformation model", "Open Model to inspect case objects."))
    selected = _selected_pane_item(items)
    sort_counts: dict[str, int] = {}
    for item in items:
        sort_key = collapse_ws(item.sort_kind) or "unclassified"
        sort_counts[sort_key] = sort_counts.get(sort_key, 0) + 1
    rows: list[tuple[str, object]] = [
        ("Lens", _display_token(getattr(progress, "draft_model_lens", "model"), fallback="Model")),
        ("Subject", scenario.title),
        ("Case objects", len(items)),
        (
            "Accepted decision items",
            sum(1 for item in items if _pane_item_attribute(item, "lane")),
        ),
        ("Selected object", selected.label if selected is not None else "<none>"),
    ]
    rows.extend((_display_token(sort_kind), count) for sort_kind, count in sorted(sort_counts.items()))
    return _attributes(*rows)


def _draft_detail_rows(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    progress: SubjectProgress,
) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    return tuple(
        SubjectWorkflowKeyValueRowView(label=label, value=value)
        for label, value in subject_draft_detail_rows(
            root_path=root_path,
            scenario=scenario,
            progress=progress,
        )
    )


def _report_scope_pane_items(
    *,
    root_path: Path,
    scenario: SubjectScenario,
    progress: SubjectProgress,
) -> tuple[SubjectWorkflowPaneItemView, ...]:
    entries = _report_scope_entries(root_path, scenario=scenario, progress=progress)
    selected = _selected_report_scope_entry(entries, progress)
    selected_id = collapse_ws(selected.entry_id) if selected is not None else ""
    held_ids = {collapse_ws(item) for item in progress.report_scope_held_entry_ids if collapse_ws(item)}
    section_specs = _report_section_spec_by_id()
    projected: list[SubjectWorkflowPaneItemView] = []
    for ordinal, entry in enumerate(entries):
        section_id = collapse_ws(entry.entry_id.split(":", 1)[-1]) if entry.item_kind == "section" else ""
        role = section_specs.get(section_id, ("", ""))[0] if section_id else ""
        projected.append(SubjectWorkflowPaneItemView(
            entry_id=collapse_ws(entry.entry_id),
            entry_kind=f"report_scope_{collapse_ws(entry.item_kind) or 'item'}",
            label=entry.label,
            ordinal=ordinal,
            depth=max(0, int(entry.depth)),
            selectable=bool(entry.selectable),
            selected=collapse_ws(entry.entry_id) == selected_id,
            toggleable=bool(entry.toggleable),
            check_state=(
                "checked" if entry.included is True else "unchecked" if entry.included is False else "none"
            ),
            held=collapse_ws(entry.entry_id) in held_ids,
            status="reportable" if entry.reportable else "question",
            detail_title=entry.detail_title,
            detail_lines=tuple(entry.detail_lines),
            attributes=_attributes(*entry.detail_rows, ("role", role)),
        ))
    return tuple(projected)


def _report_scope_detail_rows(
    *,
    scenario: SubjectScenario,
    items: tuple[SubjectWorkflowPaneItemView, ...],
) -> tuple[SubjectWorkflowKeyValueRowView, ...]:
    if scenario.is_placeholder:
        return _attributes(("Report plan details", "Select or create a subject first."))
    selected = _selected_pane_item(items)
    if selected is None:
        message = (
            "Nothing is selectable yet."
            if collapse_ws(scenario.composition_id)
            else "The report plan has not been created yet."
        )
        return _attributes(("Report plan details", message))
    detail_rows = tuple(row for row in selected.attributes if row.label != "role")
    return (
        SubjectWorkflowKeyValueRowView(
            label="Selection",
            value=selected.detail_title or selected.label,
        ),
        *detail_rows,
        SubjectWorkflowKeyValueRowView(
            label="Held for reordering",
            value="yes" if selected.held else "no",
        ),
    )


_PHASE_CONTROL_SELECT_KEYS: dict[str, tuple[str, ...]] = {
    "research": (
        "research_source_collection",
        "research_source_revision_baseline",
    ),
    "itemize": ("itemize_decision_role",),
    "draft": (
        "draft_semantic_kind",
        "draft_render_kind",
        "draft_evidence_mode",
        "draft_transform_mode",
        "draft_model_construct_sort",
        "draft_model_construct_lane",
        "draft_model_transition_source",
        "draft_model_transition_target",
        "draft_model_policy_profile",
    ),
    "review": (
        "review_publication_output_mode",
        "review_publication_section_plan",
        "review_publication_diff_baseline",
        "review_composition_unit_target",
        "review_publication_section_target",
    ),
    "publication": (
        "publication_output_mode",
        "publication_section_plan",
        "publication_diff_baseline",
        "publication_import_target",
        "publication_composition_unit_target",
        "publication_section_target",
        "publication_import_usage",
    ),
}

_PHASE_CONTROL_SWITCH_KEYS: dict[str, tuple[str, ...]] = {
    "research": ("research_selected_source_collection_membership",),
    "itemize": ("itemize_hold",),
    "draft": ("draft_decision_included",),
    "review": (
        "review_composition_unit_included",
        "review_publication_section_included",
    ),
    "publication": (
        "publication_composition_unit_included",
        "publication_section_included",
        "publication_import_included",
    ),
}

_PHASE_CONTROL_SELECTION_LIST_KEYS: dict[str, tuple[str, ...]] = {
    "draft": ("draft_model_relations",),
}

_PHASE_CONTROL_TABLE_KEYS: dict[str, tuple[str, ...]] = {
    "research": (
        "research_source_revision_history",
        "research_source_change_summary",
        "research_source_collection_member_export_status",
        "research_source_collection_member_revision",
        "research_source_collection_merge_export_history",
        "research_source_collection_actionable_export",
        "research_source_collection_export_applied",
    ),
    "review": (
        "review_comparison_history",
        "review_latest_receipt",
    ),
    "publication": (
        "publication_build_artifacts",
        "publication_build_receipt",
        "publication_latest_receipt",
    ),
}


def _research_sources_title(*, scenario: SubjectScenario, progress: SubjectProgress) -> str:
    spec = subject_research_source_collection_select_spec(
        scenario=scenario,
        progress=progress,
    )
    selected_value = collapse_ws(spec.value)
    for label, value in spec.options:
        if collapse_ws(value) == selected_value and collapse_ws(label):
            return collapse_ws(label)
    return "Source Sets"


@dataclass
class SubjectWorkflowApiService:
    repository: SubjectWorkflowRepository = field(default_factory=SubjectWorkflowRepository)
    client_sessions: WorkstationClientSessionRegistry = field(default_factory=WorkstationClientSessionRegistry)
    host_actions: SubjectWorkflowHostActions = field(default_factory=UnavailableSubjectWorkflowHostActions)

    def _ensure_client_session(
        self,
        *,
        root_path: Path,
        client_session_id: str,
    ) -> str:
        normalized_session_id = collapse_ws(client_session_id)
        if not normalized_session_id:
            return ""
        return self.client_sessions.open_client_session(
            root_path=Path(root_path).expanduser().resolve(),
            client_session_id=normalized_session_id,
        )

    def _load_effective_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
    ) -> SubjectProgress:
        if progress_override is not None:
            return progress_override
        resolved_root = Path(root_path).expanduser().resolve()
        durable_progress = self.repository.load_progress(
            root_path=resolved_root,
            subject_id=subject_id,
        )
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        if not normalized_session_id:
            return durable_progress
        return self.client_sessions.subject_progress_with_session_view(
            root_path=resolved_root,
            client_session_id=normalized_session_id,
            subject_id=subject_id,
            durable_progress=durable_progress,
        )

    def _update_client_session_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str,
        progress: SubjectProgress,
    ) -> None:
        normalized_session_id = self._ensure_client_session(
            root_path=root_path,
            client_session_id=client_session_id,
        )
        if not normalized_session_id:
            return
        self.client_sessions.update_subject_view_from_progress(
            root_path=Path(root_path).expanduser().resolve(),
            client_session_id=normalized_session_id,
            subject_id=subject_id,
            progress=progress,
        )

    @staticmethod
    def _progress_json(progress: SubjectProgress) -> str:
        return json.dumps(subject_progress_to_dict(progress), indent=2, sort_keys=True)

    @staticmethod
    def _progress_from_json(progress_json: str) -> SubjectProgress:
        payload = json.loads(str(progress_json or "").strip() or "{}")
        if not isinstance(payload, dict):
            raise ValueError("Subject progress payload must be a JSON object.")
        return subject_progress_from_dict(payload)

    @staticmethod
    def _durable_progress_payload(progress: SubjectProgress) -> dict[str, object]:
        return subject_progress_to_dict(sanitized_subject_progress_for_persistence(progress))

    def _select_spec_for_key(
        self,
        *,
        key: str,
        scenario: SubjectScenario,
        progress: SubjectProgress,
    ) -> SubjectSelectSpec:
        builders: dict[str, object] = {
            "itemize_decision_role": subject_itemize_decision_role_select_spec,
            "research_source_collection": subject_research_source_collection_select_spec,
            "research_source_revision_baseline": subject_research_source_revision_baseline_select_spec,
            "draft_semantic_kind": subject_draft_semantic_kind_select_spec,
            "draft_render_kind": subject_draft_render_kind_select_spec,
            "draft_evidence_mode": subject_draft_evidence_mode_select_spec,
            "draft_transform_mode": subject_draft_transform_mode_select_spec,
            "draft_model_construct_sort": subject_draft_model_construct_sort_select_spec,
            "draft_model_construct_lane": subject_draft_model_construct_lane_select_spec,
            "draft_model_transition_source": subject_draft_model_transition_source_select_spec,
            "draft_model_transition_target": subject_draft_model_transition_target_select_spec,
            "draft_model_policy_profile": subject_draft_model_policy_profile_select_spec,
            "review_publication_output_mode": subject_review_publication_output_mode_select_spec,
            "review_publication_section_plan": subject_review_publication_section_plan_select_spec,
            "review_publication_diff_baseline": subject_review_publication_diff_baseline_select_spec,
            "review_composition_unit_target": subject_review_composition_unit_target_select_spec,
            "review_publication_section_target": subject_review_publication_section_target_select_spec,
            "publication_output_mode": subject_review_publication_output_mode_select_spec,
            "publication_section_plan": subject_review_publication_section_plan_select_spec,
            "publication_diff_baseline": subject_review_publication_diff_baseline_select_spec,
            "publication_import_target": subject_publication_import_target_select_spec,
            "publication_composition_unit_target": subject_review_composition_unit_target_select_spec,
            "publication_section_target": subject_review_publication_section_target_select_spec,
            "publication_import_usage": subject_publication_import_usage_select_spec,
        }
        builder = builders.get(collapse_ws(key))
        if builder is None:
            raise ValueError(f"Unknown subject select spec key: {key}")
        return builder(scenario=scenario, progress=progress)

    def _switch_spec_for_key(
        self,
        *,
        key: str,
        scenario: SubjectScenario,
        progress: SubjectProgress,
    ) -> SubjectSwitchSpec:
        builders: dict[str, object] = {
            "research_selected_source_collection_membership": subject_research_selected_source_collection_membership_switch_spec,
            "itemize_hold": subject_itemize_hold_switch_spec,
            "draft_decision_included": subject_draft_decision_included_switch_spec,
            "review_composition_unit_included": subject_review_composition_unit_included_switch_spec,
            "review_publication_section_included": subject_review_publication_section_included_switch_spec,
            "publication_composition_unit_included": subject_review_composition_unit_included_switch_spec,
            "publication_section_included": subject_review_publication_section_included_switch_spec,
            "publication_import_included": subject_publication_import_included_switch_spec,
        }
        builder = builders.get(collapse_ws(key))
        if builder is None:
            raise ValueError(f"Unknown subject switch spec key: {key}")
        return builder(scenario=scenario, progress=progress)

    def _table_spec_for_key(
        self,
        *,
        key: str,
        scenario: SubjectScenario,
        progress: SubjectProgress,
    ) -> SubjectTableSpec:
        builders: dict[str, object] = {
            "research_source_revision_history": subject_research_selected_source_revision_history_table_spec,
            "research_source_change_summary": subject_research_selected_source_change_summary_table_spec,
            "research_source_collection_member_export_status": subject_research_source_collection_member_export_status_table_spec,
            "research_source_collection_member_revision": subject_research_source_collection_member_revision_table_spec,
            "research_source_collection_merge_export_history": subject_research_source_collection_merge_export_history_table_spec,
            "research_source_collection_actionable_export": subject_research_source_collection_actionable_export_table_spec,
            "research_source_collection_export_applied": subject_research_source_collection_export_applied_table_spec,
            "review_comparison_history": subject_review_comparison_history_table_spec,
            "review_latest_receipt": subject_review_latest_receipt_table_spec,
            "publication_build_artifacts": subject_publication_build_artifacts_table_spec,
            "publication_build_receipt": subject_publication_build_receipt_table_spec,
            "publication_latest_receipt": subject_publication_latest_receipt_table_spec,
        }
        builder = builders.get(collapse_ws(key))
        if builder is None:
            raise ValueError(f"Unknown subject table spec key: {key}")
        return builder(scenario=scenario, progress=progress)

    def _selection_list_specs_for_key(
        self,
        *,
        key: str,
        scenario: SubjectScenario,
        progress: SubjectProgress,
    ) -> tuple[SubjectSelectionListSpec, ...]:
        normalized_key = collapse_ws(key)
        if normalized_key == "draft_model_relations":
            return subject_draft_model_relation_selection_list_specs(
                scenario=scenario,
                progress=progress,
            )
        raise ValueError(f"Unknown subject selection-list spec key: {key}")

    def list_subjects(self, *, root_path: Path) -> tuple[SubjectWorkflowScenarioView, ...]:
        scenarios = self.repository.list_scenarios(root_path=root_path)
        return tuple(_scenario_view_from_scenario(scenario) for scenario in scenarios)

    def load_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str = "",
    ) -> SubjectProgress:
        resolved_root = Path(root_path).expanduser().resolve()
        scenario = self._select_subject_scenario(resolved_root, subject_id)
        return self._load_effective_progress(
            root_path=resolved_root,
            subject_id=scenario.subject_id,
            client_session_id=client_session_id,
        )

    def load_progress_map(
        self,
        *,
        root_path: Path,
        scenarios: tuple[SubjectScenario, ...] | tuple[object, ...],
        client_session_id: str = "",
        existing: dict[str, SubjectProgress] | None = None,
    ) -> dict[str, SubjectProgress]:
        del existing
        resolved_root = Path(root_path).expanduser().resolve()
        progress_by_key: dict[str, SubjectProgress] = {}
        for scenario in scenarios:
            subject_id = collapse_ws(getattr(scenario, "subject_id", "")) or collapse_ws(getattr(scenario, "key", ""))
            key = collapse_ws(getattr(scenario, "key", "")) or subject_id
            if not subject_id or not key:
                continue
            progress_by_key[key] = self.load_progress(
                root_path=resolved_root,
                subject_id=subject_id,
                client_session_id=client_session_id,
            )
        return progress_by_key

    def persist_progress(
        self,
        *,
        root_path: Path,
        subject_id: str,
        progress: SubjectProgress,
        client_session_id: str = "",
    ) -> Path | None:
        resolved_root = Path(root_path).expanduser().resolve()
        scenario = self._select_subject_scenario(resolved_root, subject_id)
        persisted: Path | None = None
        normalized_subject_id = collapse_ws(scenario.subject_id)
        if normalized_subject_id:
            durable_payload = self._durable_progress_payload(progress)
            persisted_payload = self._durable_progress_payload(
                self.repository.load_progress(
                    root_path=resolved_root,
                    subject_id=normalized_subject_id,
                )
            )
            if durable_payload != persisted_payload:
                persisted = self.repository.persist_progress(
                    root_path=resolved_root,
                    subject_id=normalized_subject_id,
                    progress=progress,
                )
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        if normalized_session_id:
            self._update_client_session_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                client_session_id=normalized_session_id,
                progress=progress,
            )
            publish_workstation_event(
                root_path=resolved_root,
                session_id="subject_workflow_api",
                event_kind="subject_workflow_client_view_changed",
                payload={
                    "subject_id": scenario.subject_id,
                    "client_session_id": normalized_session_id,
                    "progress_fingerprint": subject_progress_fingerprint(progress),
                },
            )
        return persisted

    def get_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str,
    ) -> str:
        progress = self.load_progress(
            root_path=root_path,
            subject_id=subject_id,
            client_session_id=client_session_id,
        )
        return self._progress_json(progress)

    def put_client_progress_json(
        self,
        *,
        root_path: Path,
        subject_id: str,
        client_session_id: str,
        progress_json: str,
    ) -> str:
        progress = self._progress_from_json(progress_json)
        resolved_root = Path(root_path).expanduser().resolve()
        scenario = self._select_subject_scenario(resolved_root, subject_id)
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        if normalized_session_id:
            self._update_client_session_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                client_session_id=normalized_session_id,
                progress=progress,
            )
            publish_workstation_event(
                root_path=resolved_root,
                session_id="subject_workflow_api",
                event_kind="subject_workflow_client_view_changed",
                payload={
                    "subject_id": scenario.subject_id,
                    "client_session_id": normalized_session_id,
                    "progress_fingerprint": subject_progress_fingerprint(
                        self.load_progress(
                            root_path=resolved_root,
                            subject_id=scenario.subject_id,
                            client_session_id=normalized_session_id,
                        )
                    ),
                },
            )
        return self._progress_json(
            self.load_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                client_session_id=normalized_session_id,
            )
        )

    def apply_interaction(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        client_session_id: str,
        interaction_key: str,
        delta: int = 0,
        target_id: str = "",
        preview_only: bool = False,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> tuple[SubjectWorkflowSnapshotView, SubjectProgress]:
        del preview_only
        resolved_root = Path(root_path).expanduser().resolve()
        scenario = self._select_subject_scenario(resolved_root, subject_id)
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        progress = self._load_effective_progress(
            root_path=resolved_root,
            subject_id=scenario.subject_id,
            client_session_id=normalized_session_id,
        )
        normalized_key = collapse_ws(interaction_key)
        normalized_target_id = collapse_ws(target_id)
        if normalized_key == "move_itemize_cursor":
            move_itemize_cursor(
                resolved_root,
                scenario=scenario,
                progress=progress,
                delta=int(delta or 0),
            )
        elif normalized_key == "move_research_source_cursor":
            move_research_source_cursor(
                resolved_root,
                scenario=scenario,
                progress=progress,
                delta=int(delta or 0),
            )
        elif normalized_key == "move_draft_review_cursor":
            move_draft_review_cursor(
                resolved_root,
                scenario=scenario,
                progress=progress,
                delta=int(delta or 0),
            )
        elif normalized_key == "move_report_scope_cursor":
            move_report_scope_cursor(
                resolved_root,
                scenario=scenario,
                progress=progress,
                delta=int(delta or 0),
            )
        elif normalized_key == "preview_move_held_report_scope_items":
            preview_move_held_report_scope_items(
                resolved_root,
                scenario=scenario,
                progress=progress,
                delta=int(delta or 0),
            )
        elif normalized_key == "set_draft_selection_to_review_item_id":
            _set_draft_selection_to_review_item_id(
                resolved_root,
                scenario=scenario,
                progress=progress,
                review_item_id=normalized_target_id,
            )
        elif normalized_key == "set_draft_selection_to_construct_candidate_id":
            _set_draft_selection_to_construct_candidate_id(
                resolved_root,
                scenario=scenario,
                progress=progress,
                construct_candidate_id=normalized_target_id,
            )
        else:
            raise ValueError(f"Unknown subject interaction key: {interaction_key}")
        self.persist_progress(
            root_path=resolved_root,
            subject_id=scenario.subject_id,
            progress=progress,
            client_session_id=normalized_session_id,
        )
        snapshot = self.get_snapshot(
            root_path=resolved_root,
            subject_id=scenario.subject_id,
            phase=phase,
            progress_override=progress,
            client_session_id=normalized_session_id,
            can_capture_assistant=can_capture_assistant,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
        )
        return snapshot, progress

    def get_control_bundle(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
        import_staging_override: SubjectImportStaging | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowControlBundleView:
        with subject_workflow_request_cache():
            resolved_root = Path(root_path).expanduser().resolve()
            parent_trace_id = new_trace_id("subject-control-request")
            scenario = self._select_subject_scenario(resolved_root, subject_id)
            progress = self._load_effective_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                progress_override=progress_override,
                client_session_id=client_session_id,
            )
            normalized_phase = _normalized_phase(phase)
            import_staging = import_staging_override or self.repository.load_import_staging(root_path=resolved_root)
            more_actions = tuple(
                _action_spec_view(spec.key, spec)
                for spec in subject_more_action_specs(
                    scenario=scenario,
                    progress=progress,
                    phase=normalized_phase,
                    can_capture_assistant=can_capture_assistant,
                    import_staging=import_staging,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                )
            )
            trace_id, parent_id = _registered_trace(
                message_kind="GetSubjectControlBundleResponse",
                prefix="subject-control-response",
                parent_id=parent_trace_id,
                components=(
                    parent_trace_id,
                    resolved_root,
                    scenario.subject_id,
                    normalized_phase,
                    subject_progress_fingerprint(progress),
                ),
            )
            return SubjectWorkflowControlBundleView(
                phase=normalized_phase,
                more_actions=more_actions,
                selects=tuple(
                    _select_spec_view(
                        key,
                        self._select_spec_for_key(
                            key=key,
                            scenario=scenario,
                            progress=progress,
                        ),
                    )
                    for key in _PHASE_CONTROL_SELECT_KEYS.get(normalized_phase, ())
                ),
                switches=tuple(
                    _switch_spec_view(
                        key,
                        self._switch_spec_for_key(
                            key=key,
                            scenario=scenario,
                            progress=progress,
                        ),
                    )
                    for key in _PHASE_CONTROL_SWITCH_KEYS.get(normalized_phase, ())
                ),
                selection_lists=tuple(
                    _selection_list_spec_view(key, spec)
                    for key in _PHASE_CONTROL_SELECTION_LIST_KEYS.get(normalized_phase, ())
                    for spec in self._selection_list_specs_for_key(
                        key=key,
                        scenario=scenario,
                        progress=progress,
                    )
                ),
                tables=tuple(
                    _table_spec_view(
                        key,
                        self._table_spec_for_key(
                            key=key,
                            scenario=scenario,
                            progress=progress,
                        ),
                    )
                    for key in _PHASE_CONTROL_TABLE_KEYS.get(normalized_phase, ())
                ),
                trace_id=trace_id,
                parent_id=parent_id,
            )

    def get_pane_bundle(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
        import_staging_override: SubjectImportStaging | None = None,
    ) -> SubjectWorkflowPaneBundleView:
        with subject_workflow_request_cache():
            resolved_root = Path(root_path).expanduser().resolve()
            parent_trace_id = new_trace_id("subject-pane-request")
            scenario = self._select_subject_scenario(resolved_root, subject_id)
            progress = self._load_effective_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                progress_override=progress_override,
                client_session_id=client_session_id,
            )
            normalized_phase = _normalized_phase(phase)
            import_staging = import_staging_override or self.repository.load_import_staging(root_path=resolved_root)
            panes: tuple[SubjectWorkflowPaneView, ...]
            if normalized_phase == "research":
                panes = (
                    _pane_view(
                        "research_sources",
                        _research_sources_title(scenario=scenario, progress=progress),
                        render_subject_research_sources(scenario=scenario, progress=progress),
                        items=_research_source_pane_items(
                            root_path=resolved_root,
                            scenario=scenario,
                            progress=progress,
                        ),
                    ),
                    _pane_view(
                        "research_observation",
                        "Learned Snapshot",
                        render_subject_research_observation(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_research_observation_rows(scenario),
                    ),
                    _pane_view(
                        "research_target",
                        subject_research_target_title(scenario=scenario, progress=progress),
                        render_subject_research_target(
                            scenario=scenario,
                            progress=progress,
                            import_staging=import_staging,
                        ),
                    ),
                )
            elif normalized_phase == "itemize":
                itemize_items = _itemize_pane_items(
                    root_path=resolved_root,
                    scenario=scenario,
                    progress=progress,
                )
                panes = (
                    _pane_view(
                        "itemize_inventory",
                        "Item Inventory",
                        render_subject_itemize_inventory(scenario=scenario, progress=progress),
                        items=itemize_items,
                    ),
                    _pane_view(
                        "itemize_detail",
                        subject_itemize_detail_title(scenario=scenario, progress=progress),
                        render_subject_itemize_detail(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_itemize_detail_rows(itemize_items),
                    ),
                    _pane_view(
                        "itemize_target",
                        "Draft Handoff",
                        render_subject_itemize_target(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_itemize_target_rows(
                            root_path=resolved_root,
                            scenario=scenario,
                            items=itemize_items,
                        ),
                    ),
                )
            elif normalized_phase == "draft":
                draft_items = _draft_pane_items(
                    root_path=resolved_root,
                    scenario=scenario,
                    progress=progress,
                )
                panes = (
                    _pane_view(
                        "draft_scope_tree",
                        subject_draft_tree_title(scenario=scenario, progress=progress),
                        render_subject_draft_tree(scenario=scenario, progress=progress),
                        items=draft_items,
                    ),
                    _pane_view(
                        "draft_model_main",
                        subject_draft_model_main_title(scenario=scenario, progress=progress),
                        render_subject_draft_model_main(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_draft_model_rows(
                            scenario=scenario,
                            progress=progress,
                            items=draft_items,
                        ),
                    ),
                    _pane_view(
                        "draft_detail",
                        subject_draft_detail_title(scenario=scenario, progress=progress),
                        render_subject_draft_detail(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_draft_detail_rows(
                            root_path=resolved_root,
                            scenario=scenario,
                            progress=progress,
                        ),
                    ),
                    _pane_view(
                        "draft_result",
                        subject_draft_result_title(scenario=scenario, progress=progress),
                        render_subject_draft_issue_tray(scenario=scenario, progress=progress),
                    ),
                )
            elif normalized_phase == "review":
                report_scope_items = _report_scope_pane_items(
                    root_path=resolved_root,
                    scenario=scenario,
                    progress=progress,
                )
                panes = (
                    _pane_view(
                        "review_scope_tree",
                        "Report Scope",
                        render_subject_report_scope_tree(scenario=scenario, progress=progress),
                        items=report_scope_items,
                    ),
                    _pane_view(
                        "review_scope_detail",
                        subject_report_scope_detail_title(scenario=scenario, progress=progress),
                        render_subject_report_scope_detail(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_report_scope_detail_rows(
                            scenario=scenario,
                            items=report_scope_items,
                        ),
                    ),
                )
            elif normalized_phase == "publication":
                report_scope_items = _report_scope_pane_items(
                    root_path=resolved_root,
                    scenario=scenario,
                    progress=progress,
                )
                panes = (
                    _pane_view(
                        "publication_scope_tree",
                        "Report Scope",
                        render_subject_report_scope_tree(scenario=scenario, progress=progress),
                        items=report_scope_items,
                    ),
                    _pane_view(
                        "publication_scope_detail",
                        subject_report_scope_detail_title(scenario=scenario, progress=progress),
                        render_subject_report_scope_detail(scenario=scenario, progress=progress),
                        is_structured_table=True,
                        rows=_report_scope_detail_rows(
                            scenario=scenario,
                            items=report_scope_items,
                        ),
                    ),
                )
            else:
                panes = ()
            trace_id, parent_id = _registered_trace(
                message_kind="GetSubjectPaneBundleResponse",
                prefix="subject-pane-response",
                parent_id=parent_trace_id,
                components=(
                    parent_trace_id,
                    resolved_root,
                    scenario.subject_id,
                    normalized_phase,
                    subject_progress_fingerprint(progress),
                ),
            )
            return SubjectWorkflowPaneBundleView(
                phase=normalized_phase,
                panes=panes,
                trace_id=trace_id,
                parent_id=parent_id,
            )

    def get_phase_view(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
        import_staging_override: SubjectImportStaging | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowPhaseView:
        with subject_workflow_request_cache():
            resolved_root = Path(root_path).expanduser().resolve()
            parent_trace_id = new_trace_id("subject-phase-request")
            scenario = self._select_subject_scenario(resolved_root, subject_id)
            progress = self._load_effective_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                progress_override=progress_override,
                client_session_id=client_session_id,
            )
            import_staging = import_staging_override or self.repository.load_import_staging(root_path=resolved_root)
            normalized_phase = _normalized_phase(phase)
            current_step = subject_current_step_view(
                scenario=scenario,
                progress=progress,
                phase=normalized_phase,
                can_capture_assistant=can_capture_assistant,
                import_staging=import_staging,
                markdown_selected_path=markdown_selected_path,
                markdown_status_text=markdown_status_text,
                markdown_busy=markdown_busy,
            )
            actions = subject_current_step_actions(
                scenario=scenario,
                progress=progress,
                phase=normalized_phase,
                can_capture_assistant=can_capture_assistant,
                import_staging=import_staging,
                markdown_selected_path=markdown_selected_path,
                markdown_status_text=markdown_status_text,
                markdown_busy=markdown_busy,
            )
            trace_id, parent_id = _registered_trace(
                message_kind="GetSubjectPhaseViewResponse",
                prefix="subject-phase-response",
                parent_id=parent_trace_id,
                components=(
                    parent_trace_id,
                    resolved_root,
                    scenario.subject_id,
                    normalized_phase,
                    subject_progress_fingerprint(progress),
                ),
            )
            return SubjectWorkflowPhaseView(
                phase=normalized_phase,
                phase_title=subject_phase_title(normalized_phase),
                preferred_phase=subject_guidance_phase(
                    scenario=scenario,
                    progress=progress,
                    phase=normalized_phase,
                    can_capture_assistant=can_capture_assistant,
                    import_staging=import_staging,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                ),
                scenario=_scenario_view_from_scenario(scenario),
                current_step=_current_step_view_from_step(current_step, actions),
                status_view=_status_view_for_phase(
                    scenario=scenario,
                    progress=progress,
                    phase=normalized_phase,
                ),
                journey_lines=_lines_from_rendered_text(
                    render_subject_journey(
                        scenario=scenario,
                        progress=progress,
                        phase=normalized_phase,
                        import_staging=import_staging,
                        markdown_selected_path=markdown_selected_path,
                        markdown_status_text=markdown_status_text,
                        markdown_busy=markdown_busy,
                    )
                ),
                workspace_view=SubjectWorkflowTextSectionView(
                    title=_workspace_title_for_phase(normalized_phase),
                    lines=_lines_from_rendered_text(
                        render_subject_workspace(
                            scenario=scenario,
                            progress=progress,
                            phase=normalized_phase,
                            import_staging=import_staging,
                        )
                    ),
                ),
                latest_receipt_title=collapse_ws(progress.latest_receipt_title),
                latest_receipt_lines=tuple(str(line) for line in progress.latest_receipt_lines),
                trace_id=trace_id,
                parent_id=parent_id,
            )

    def get_snapshot(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
        import_staging_override: SubjectImportStaging | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowSnapshotView:
        with subject_workflow_request_cache():
            parent_trace_id = new_trace_id("subject-snapshot-request")
            phase_view = self.get_phase_view(
                root_path=root_path,
                subject_id=subject_id,
                phase=phase,
                progress_override=progress_override,
                client_session_id=client_session_id,
                import_staging_override=import_staging_override,
                can_capture_assistant=can_capture_assistant,
                markdown_selected_path=markdown_selected_path,
                markdown_status_text=markdown_status_text,
                markdown_busy=markdown_busy,
            )
            normalized_phase = collapse_ws(phase_view.phase) or _normalized_phase(phase)
            control_bundle = self.get_control_bundle(
                root_path=root_path,
                subject_id=subject_id,
                phase=normalized_phase,
                progress_override=progress_override,
                client_session_id=client_session_id,
                import_staging_override=import_staging_override,
                can_capture_assistant=can_capture_assistant,
                markdown_selected_path=markdown_selected_path,
                markdown_status_text=markdown_status_text,
                markdown_busy=markdown_busy,
            )
            pane_bundle = self.get_pane_bundle(
                root_path=root_path,
                subject_id=subject_id,
                phase=normalized_phase,
                progress_override=progress_override,
                client_session_id=client_session_id,
                import_staging_override=import_staging_override,
            )
            trace_id, parent_id = _registered_trace(
                message_kind="GetSubjectWorkflowSnapshotResponse",
                prefix="subject-snapshot-response",
                parent_id=parent_trace_id,
                components=(
                    parent_trace_id,
                    Path(root_path).expanduser().resolve(),
                    collapse_ws(subject_id),
                    normalized_phase,
                    phase_view.trace_id,
                    control_bundle.trace_id,
                    pane_bundle.trace_id,
                ),
            )
            return SubjectWorkflowSnapshotView(
                phase_view=phase_view,
                control_bundle=control_bundle,
                pane_bundle=pane_bundle,
                trace_id=trace_id,
                parent_id=parent_id,
            )

    def watch_subject_workflow(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        client_session_id: str = "",
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
        stop_when: Callable[[], bool] | None = None,
    ) -> Iterator[SubjectWorkflowWatchEventView]:
        resolved_root = Path(root_path).expanduser().resolve()
        selected = self._select_subject_scenario(resolved_root, subject_id)
        normalized_subject_id = collapse_ws(selected.subject_id) or collapse_ws(selected.key)
        normalized_phase = _normalized_phase(phase)
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        channel_key = f"subject/{normalized_subject_id}/{normalized_phase}"
        stream_trace_id = new_trace_id("subject-watch-stream")
        event_queue: Queue[object] = Queue()

        def _handle(event: object) -> None:
            try:
                payload = getattr(event, "payload", {}) or {}
            except Exception:
                payload = {}
            event_client_session_id = collapse_ws(str(payload.get("client_session_id", "")))
            event_subject_id = collapse_ws(str(payload.get("subject_id", "")))
            preferred_subject_key = collapse_ws(str(payload.get("preferred_subject_key", "")))
            event_kind = collapse_ws(str(getattr(event, "kind", ""))) or "subject_workflow_changed"
            if event_kind == "subject_workflow_client_view_changed" and event_client_session_id != normalized_session_id:
                return
            if event_subject_id and event_subject_id != normalized_subject_id and preferred_subject_key != normalized_subject_id:
                return
            event_queue.put(event)

        unsubscribe_changed = workstation_event_bus(resolved_root).subscribe("subject_workflow_changed", _handle)
        unsubscribe_view = workstation_event_bus(resolved_root).subscribe("subject_workflow_client_view_changed", _handle)
        try:
            sequence = 0
            initial_progress = self._load_effective_progress(
                root_path=resolved_root,
                subject_id=normalized_subject_id,
                client_session_id=normalized_session_id,
            )
            initial_fingerprint = subject_progress_fingerprint(initial_progress)
            initial_snapshot = self.get_snapshot(
                root_path=resolved_root,
                subject_id=normalized_subject_id,
                phase=normalized_phase,
                client_session_id=normalized_session_id,
                can_capture_assistant=can_capture_assistant,
                markdown_selected_path=markdown_selected_path,
                markdown_status_text=markdown_status_text,
                markdown_busy=markdown_busy,
            )
            yield SubjectWorkflowWatchEventView(
                event_kind="initial",
                snapshot=initial_snapshot,
                channel_key=channel_key,
                sequence=sequence,
                snapshot_version=_subject_workflow_snapshot_version(
                    subject_id=normalized_subject_id,
                    phase=normalized_phase,
                    progress_fingerprint=initial_fingerprint,
                    snapshot=initial_snapshot,
                ),
                progress_fingerprint=initial_fingerprint,
                trace_id=_registered_trace(
                    message_kind="WatchSubjectWorkflow.initial",
                    prefix="subject-watch-event",
                    parent_id=stream_trace_id,
                    components=(
                        stream_trace_id,
                        channel_key,
                        "initial",
                        initial_fingerprint,
                    ),
                )[0],
                parent_id=stream_trace_id,
            )
            while True:
                if stop_when is not None and stop_when():
                    break
                try:
                    event = event_queue.get(timeout=0.25)
                except Empty:
                    continue
                sequence += 1
                current_progress = self._load_effective_progress(
                    root_path=resolved_root,
                    subject_id=normalized_subject_id,
                    client_session_id=normalized_session_id,
                )
                progress_fingerprint = subject_progress_fingerprint(current_progress)
                snapshot = self.get_snapshot(
                    root_path=resolved_root,
                    subject_id=normalized_subject_id,
                    phase=normalized_phase,
                    client_session_id=normalized_session_id,
                    can_capture_assistant=can_capture_assistant,
                    markdown_selected_path=markdown_selected_path,
                    markdown_status_text=markdown_status_text,
                    markdown_busy=markdown_busy,
                )
                event_trace_parent = collapse_ws(str(getattr(event, "trace_id", ""))) or stream_trace_id
                trace_id, parent_id = _registered_trace(
                    message_kind="WatchSubjectWorkflow.changed",
                    prefix="subject-watch-event",
                    parent_id=event_trace_parent,
                    components=(
                        stream_trace_id,
                        event_trace_parent,
                        channel_key,
                        sequence,
                        progress_fingerprint,
                    ),
                )
                yield SubjectWorkflowWatchEventView(
                    event_kind=collapse_ws(str(getattr(event, "kind", ""))) or "subject_workflow_changed",
                    snapshot=snapshot,
                    channel_key=channel_key,
                    sequence=sequence,
                    snapshot_version=_subject_workflow_snapshot_version(
                        subject_id=normalized_subject_id,
                        phase=normalized_phase,
                        progress_fingerprint=progress_fingerprint,
                        snapshot=snapshot,
                    ),
                    progress_fingerprint=progress_fingerprint,
                    trace_id=trace_id,
                    parent_id=parent_id,
                )
        finally:
            try:
                unsubscribe_changed()
            except Exception:
                pass
            try:
                unsubscribe_view()
            except Exception:
                pass

    def apply_action(
        self,
        *,
        root_path: Path,
        subject_id: str,
        phase: str,
        action_key: str,
        progress_override: SubjectProgress | None = None,
        client_session_id: str = "",
        assistant_message_text: str = "",
        subject_title_override: str = "",
        import_staging: SubjectImportStaging | None = None,
        can_capture_assistant: bool = False,
        markdown_selected_path: str = "",
        markdown_status_text: str = "",
        markdown_busy: bool = False,
    ) -> SubjectWorkflowActionOutcomeView:
        resolved_root = Path(root_path).expanduser().resolve()
        parent_trace_id = new_trace_id("subject-action-request")
        scenario = self._select_subject_scenario(resolved_root, subject_id)
        normalized_session_id = self._ensure_client_session(
            root_path=resolved_root,
            client_session_id=client_session_id,
        )
        progress = self._load_effective_progress(
            root_path=resolved_root,
            subject_id=scenario.subject_id,
            progress_override=progress_override,
            client_session_id=normalized_session_id,
        )
        effective_import_staging = (
            import_staging
            if import_staging is not None
            else self.repository.load_import_staging(root_path=resolved_root)
        )
        result = apply_subject_action(
            root_path=resolved_root,
            scenario=scenario,
            progress=progress,
            action_key=action_key,
            assistant_message_text=assistant_message_text,
            subject_title_override=subject_title_override,
            import_staging=effective_import_staging,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
            host_actions=self.host_actions,
        )
        if collapse_ws(scenario.subject_id):
            self.repository.persist_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                progress=progress,
            )
            self._update_client_session_progress(
                root_path=resolved_root,
                subject_id=scenario.subject_id,
                client_session_id=normalized_session_id,
                progress=progress,
            )
        next_phase = _normalized_phase(result.next_phase or phase)
        selected_subject_id = collapse_ws(result.preferred_subject_key) or collapse_ws(scenario.subject_id)
        phase_view = self.get_phase_view(
            root_path=resolved_root,
            subject_id=selected_subject_id,
            phase=next_phase,
            progress_override=(
                progress
                if collapse_ws(selected_subject_id) == collapse_ws(scenario.subject_id)
                else None
            ),
            client_session_id=normalized_session_id,
            import_staging_override=effective_import_staging,
            can_capture_assistant=can_capture_assistant,
            markdown_selected_path=markdown_selected_path,
            markdown_status_text=markdown_status_text,
            markdown_busy=markdown_busy,
        )
        trace_id, parent_id = _registered_trace(
            message_kind="ApplySubjectActionResponse",
            prefix="subject-action-response",
            parent_id=parent_trace_id,
            components=(
                parent_trace_id,
                resolved_root,
                collapse_ws(action_key),
                phase_view.trace_id,
                subject_progress_fingerprint(progress),
            ),
        )
        outcome = SubjectWorkflowActionOutcomeView(
            status_text=result.status_text,
            timeline_text=result.timeline_text,
            next_phase=collapse_ws(str(result.next_phase or "")),
            next_tab=collapse_ws(str(result.next_tab or "")),
            reload_subjects=bool(result.reload_subjects),
            open_paths=tuple(str(path) for path in result.open_paths),
            preferred_subject_key=collapse_ws(result.preferred_subject_key),
            phase_view=phase_view,
            open_artifacts=tuple(_local_artifact_ref_view_from_path(path) for path in result.open_paths),
            trace_id=trace_id,
            parent_id=parent_id,
        )
        publish_workstation_event(
            root_path=resolved_root,
            session_id="subject_workflow_api",
            event_kind="subject_workflow_changed",
            payload={
                "subject_id": selected_subject_id,
                "action_key": collapse_ws(action_key),
                "phase": collapse_ws(phase),
                "next_phase": outcome.next_phase,
                "reload_subjects": outcome.reload_subjects,
                "preferred_subject_key": outcome.preferred_subject_key,
                "progress_fingerprint": subject_progress_fingerprint(progress),
                "client_session_id": normalized_session_id,
            },
        )
        return outcome

    def _select_subject_scenario(self, root_path: Path, subject_id: str) -> SubjectScenario:
        normalized_subject_id = collapse_ws(subject_id)
        scenarios = self.repository.list_scenarios(root_path=root_path)
        if not scenarios:
            raise ValueError("No subject scenarios are available.")
        if not normalized_subject_id:
            return scenarios[0]
        for scenario in scenarios:
            if collapse_ws(scenario.subject_id) == normalized_subject_id or collapse_ws(scenario.key) == normalized_subject_id:
                return scenario
        raise ValueError(f"Unknown subject id: {normalized_subject_id}")
