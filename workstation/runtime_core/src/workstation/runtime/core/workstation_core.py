# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from collections.abc import Callable
from typing import Any

from realized_core_semantics.values import json_safe
from blend_context import BlendContext
from blend_operator_store import (
    BlendOperatorProvider,
    get_blend_operator_summary,
    list_blend_operator_summaries,
)
from blend_workflow_store import (
    list_blend_workflow_summaries,
    load_blend_workflow_index,
    list_blend_workflow_runs_for_plan,
    load_blend_workflow_plan,
    load_blend_workflow_run,
)
from gather_sources import (
    SourceCollection,
    StagedSource,
    latest_source_revision,
    list_source_collections,
    list_staged_sources,
    load_staged_source,
    new_source_revision,
    new_staged_source,
    persist_source_collection,
    persist_source_revision,
    persist_staged_source,
    staged_source_body_path,
    staged_source_bundle_root,
)
from realized_host_interaction.receipts import host_interaction_receipts_path
from realized_skill_semantics.execution import ability_executor_framework
from learning_context import load_learning_context, new_learning_context, persist_learning_context
from semantic_text import collapse_ws
from skill_schema_io import normalized_skill_bundle_filename_for_source
from skill_ir import canonical_skill_ir_from_artifact
from workstation.foundation.events.event_bus import publish_workstation_event
from workstation.foundation.models import WorkstationSession
from workstation.foundation.projections import (
    WorkstationActionResultView,
    WorkstationActivityEventView,
    WorkstationActivityFeedView,
    WorkstationChatMessageView,
    WorkstationChatTranscriptView,
    WorkstationOperatorDetailView,
    WorkstationOperatorSummaryEntryView,
    WorkstationOperatorSummaryListView,
    WorkstationPermissionPanelView,
    WorkstationSkillCatalogEntryView,
    WorkstationSkillCatalogView,
    WorkstationSkillDescriptorView,
    WorkstationSkillFieldView,
    WorkstationSkillFormSectionView,
    WorkstationSkillInputFormView,
    WorkstationWorkflowTimelineEntryView,
    WorkstationWorkflowTimelineView,
    WorkstationWorkflowSummaryEntryView,
    WorkstationWorkflowSummaryListView,
    WorkstationWorkflowGraphView,
    annotate_workstation_activity_events,
    render_workstation_activity_line,
    workstation_activity_event_view,
    workstation_permission_panel_view,
    workstation_workflow_graph_view,
)
from workstation.skills.core.skill_invocation import list_available_workstation_skills, resolve_workstation_skill


def _repo_root() -> Path:
    resolved = Path(__file__).resolve()
    for parent in resolved.parents:
        if (parent / "pyproject.toml").exists() and (parent / "main.py").exists():
            return parent
    return resolved.parents[6]


def _runtime_cli_command(*arguments: str) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, *arguments]
    return [sys.executable, str(_repo_root() / "main.py"), *arguments]


def _runtime_cli_cwd() -> str:
    if getattr(sys, "frozen", False):
        return str(Path.cwd())
    return str(_repo_root())


def _normalized_learning_report(report: dict[str, Any]) -> dict[str, Any]:
    normalized = json_safe(dict(report))
    learning_context_report = (
        dict(normalized.get("learning_context", {}))
        if isinstance(normalized.get("learning_context", {}), dict)
        else {}
    )
    for key in ("subject_id", "context_path", "canonical_title", "subject_family", "source_kind"):
        if key not in normalized and collapse_ws(str(learning_context_report.get(key, ""))):
            normalized[key] = learning_context_report.get(key)
    return normalized


def _ensure_gather_subject_workspace(
    *,
    root_path: Path,
    subject_id: str,
    subject_title: str,
) -> tuple[str, str, str]:
    normalized_subject_id = collapse_ws(subject_id)
    normalized_subject_title = collapse_ws(subject_title) or normalized_subject_id or "Gather Source"
    if not normalized_subject_id:
        context = new_learning_context(canonical_title=normalized_subject_title)
        persist_learning_context(root_path, context)
        return (
            context.subject_id,
            context.canonical_title or normalized_subject_title,
            str((root_path / "corpus" / context.subject_id / "context.json").resolve()),
        )
    try:
        context = load_learning_context(root_path, normalized_subject_id)
    except Exception:
        context = new_learning_context(
            canonical_title=normalized_subject_title,
            subject_id=normalized_subject_id,
        )
        persist_learning_context(root_path, context)
    return (
        context.subject_id,
        context.canonical_title or normalized_subject_title,
        str((root_path / "corpus" / context.subject_id / "context.json").resolve()),
    )


def _first_markdown_heading(markdown_text: str) -> str:
    for raw_line in str(markdown_text or "").splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("#"):
            continue
        heading = collapse_ws(stripped.lstrip("#").strip())
        if heading:
            return heading
    return ""


def _staged_source_import_override(root_path: Path, staged_source: StagedSource, revision) -> dict[str, Any]:
    bundle_root = staged_source_bundle_root(root_path, staged_source.subject_id, revision.revision_id)
    bundle_files: dict[str, Any] = {}
    for relpath_text in revision.bundle_relpaths:
        relpath = Path(relpath_text)
        path = bundle_root / relpath
        if not path.exists():
            continue
        try:
            bundle_files[relpath_text] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bundle_files[relpath_text] = path.read_bytes()
    metadata = dict(staged_source.metadata)
    source_metadata = revision.metadata.get("source_metadata", {})
    if isinstance(source_metadata, dict):
        metadata.update(source_metadata)
    return {
        "source_kind": staged_source.source_kind or "url",
        "source_ref": revision.source_ref or staged_source.source_ref,
        "media_type": staged_source.media_type or "text/markdown",
        "title": staged_source.title,
        "metadata": metadata,
        "bundle_files": bundle_files,
    }


def _learn_markdown_bundle_in_process(
    *,
    root_path: Path,
    markdown_path: Path,
    source_label: str,
    bundle_output_path: Path,
    max_artifacts: int = 8,
    source_bundle_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from workstation.foundation.host.controller_runtime import controller_runtime_provider

    report = controller_runtime_provider().learn_markdown_bundle(
        root_path=Path(root_path).expanduser().resolve(),
        markdown_path=Path(markdown_path).expanduser().resolve(),
        source_label=source_label,
        bundle_output_path=Path(bundle_output_path).expanduser().resolve(),
        max_artifacts=max(1, int(max_artifacts)),
        source_bundle_override=source_bundle_override,
    )
    return _normalized_learning_report(report)


def workstation_permission_panel_for_session(
    *,
    session: WorkstationSession,
    available_capabilities: list[str] | tuple[str, ...],
    protected_capabilities: list[str] | tuple[str, ...],
) -> WorkstationPermissionPanelView:
    return workstation_permission_panel_view(
        session=session,
        available_capabilities=available_capabilities,
        protected_capabilities=protected_capabilities,
    )


def workstation_skill_catalog_for_session(
    *,
    session: WorkstationSession,
    query: str = "",
) -> WorkstationSkillCatalogView:
    skill_store_path = _workstation_skill_store_path(session)
    catalog = list_available_workstation_skills(skill_store_path)
    normalized_query = collapse_ws(str(query))
    if normalized_query:
        query_key = normalized_query.casefold()
        filtered: list[dict[str, Any]] = []
        for item in catalog:
            title = collapse_ws(str(item.get("title", "")))
            if query_key in title.casefold():
                filtered.append(dict(item))
        catalog = filtered
    builtin: list[WorkstationSkillCatalogEntryView] = []
    imported: list[WorkstationSkillCatalogEntryView] = []
    for item in catalog:
        if not isinstance(item, dict):
            continue
        entry = WorkstationSkillCatalogEntryView(
            skill_title=collapse_ws(str(item.get("title", ""))),
            kind=collapse_ws(str(item.get("kind", ""))),
            source_kind=collapse_ws(str(item.get("source_kind", ""))),
            executor_framework=collapse_ws(str(item.get("executor_framework", ""))),
        )
        if entry.source_kind == "builtin_workstation":
            builtin.append(entry)
        else:
            imported.append(entry)
    return WorkstationSkillCatalogView(
        query=normalized_query,
        builtin=tuple(builtin),
        imported=tuple(imported),
        total_visible=len(builtin) + len(imported),
    )


def workstation_activity_event_view_from_event(
    *,
    event_kind: str,
    payload: dict[str, Any],
) -> WorkstationActivityEventView | None:
    normalized_kind = collapse_ws(str(event_kind))
    event_payload = dict(payload) if isinstance(payload, dict) else {}
    details = event_payload.get("payload", {})
    if not isinstance(details, dict):
        details = {}
    if normalized_kind == "blend_workflow_started":
        step_count = int(details.get("step_count", 0) or 0)
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=f"Workflow started ({step_count} steps)" if step_count else "Workflow started",
            status="started",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
        )
    if normalized_kind == "blend_step_started":
        operator_name = _short_skill_title(str(event_payload.get("operator_name", "")))
        input_preview = _short_preview(json.dumps(json_safe(details.get("input_payload")), sort_keys=True), limit=72) if details.get("input_payload") is not None else ""
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview(f"Step started: {operator_name or 'workflow step'}", input_preview, label="in"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "started",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
            step_id=collapse_ws(str(event_payload.get("step_id", ""))),
            branch_label=collapse_ws(str(event_payload.get("branch_label", ""))),
            iteration=int(event_payload.get("iteration", 0) or 0),
        )
    if normalized_kind == "blend_step_completed":
        operator_name = _short_skill_title(str(event_payload.get("operator_name", "")))
        output_preview = _short_preview(json.dumps(json_safe(details.get("output_payload")), sort_keys=True), limit=72) if details.get("output_payload") is not None else ""
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview(f"Step completed: {operator_name or 'workflow step'}", output_preview, label="out"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "ok",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
            step_id=collapse_ws(str(event_payload.get("step_id", ""))),
            branch_label=collapse_ws(str(event_payload.get("branch_label", ""))),
            iteration=int(event_payload.get("iteration", 0) or 0),
        )
    if normalized_kind == "blend_step_skipped":
        operator_name = _short_skill_title(str(event_payload.get("operator_name", "")))
        reason = collapse_ws(str(details.get("skipped_reason", "")))
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview(f"Step skipped: {operator_name or 'workflow step'}", reason, label="reason"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "skipped",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
            step_id=collapse_ws(str(event_payload.get("step_id", ""))),
            branch_label=collapse_ws(str(event_payload.get("branch_label", ""))),
            iteration=int(event_payload.get("iteration", 0) or 0),
        )
    if normalized_kind == "blend_step_blocked":
        operator_name = _short_skill_title(str(event_payload.get("operator_name", "")))
        reason = _short_preview(
            collapse_ws(str(details.get("error", ""))) or collapse_ws(str(details.get("result_payload", ""))),
            limit=72,
        )
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview(f"Step blocked: {operator_name or 'workflow step'}", reason, label="reason"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "approval_required",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
            step_id=collapse_ws(str(event_payload.get("step_id", ""))),
            branch_label=collapse_ws(str(event_payload.get("branch_label", ""))),
            iteration=int(event_payload.get("iteration", 0) or 0),
        )
    if normalized_kind == "blend_step_failed":
        operator_name = _short_skill_title(str(event_payload.get("operator_name", "")))
        reason = _short_preview(collapse_ws(str(details.get("error", ""))), limit=72)
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview(f"Step failed: {operator_name or 'workflow step'}", reason, label="reason"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "error",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
            step_id=collapse_ws(str(event_payload.get("step_id", ""))),
            branch_label=collapse_ws(str(event_payload.get("branch_label", ""))),
            iteration=int(event_payload.get("iteration", 0) or 0),
        )
    if normalized_kind == "blend_workflow_completed":
        final_step = collapse_ws(str(details.get("final_output_step", "")))
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=f"Workflow completed{f': {final_step}' if final_step else ''}",
            status=collapse_ws(str(event_payload.get("status", ""))) or "ok",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
        )
    if normalized_kind == "blend_workflow_failed":
        blocked_step = collapse_ws(str(details.get("blocked_step_id", "")))
        error_text = collapse_ws(str(details.get("error", "")))
        preview = blocked_step or error_text
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview("Workflow failed", preview, label="reason"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "error",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=collapse_ws(str(event_payload.get("workflow_run_id", ""))),
        )
    if normalized_kind == "blend_workflow_persisted":
        workflow_run_id = collapse_ws(str(event_payload.get("workflow_run_id", "")))
        return WorkstationActivityEventView(
            event_kind=normalized_kind,
            message=_with_preview("Workflow persisted", workflow_run_id, label="run"),
            status=collapse_ws(str(event_payload.get("status", ""))) or "ok",
            workflow_execution_id=collapse_ws(str(event_payload.get("workflow_execution_id", ""))),
            workflow_id=collapse_ws(str(event_payload.get("workflow_id", ""))),
            workflow_run_id=workflow_run_id,
        )
    return None


def workstation_recent_activity_feed(
    *,
    root_path: Path,
    limit: int = 50,
    supplemental_events: list[WorkstationActivityEventView] | tuple[WorkstationActivityEventView, ...] | None = None,
) -> WorkstationActivityFeedView:
    path = host_interaction_receipts_path(Path(root_path))
    if not path.exists():
        return WorkstationActivityFeedView(events=())
    events: list[WorkstationActivityEventView] = []
    started_timestamps_by_signature: dict[str, list[float]] = {}
    current_prompt_started_at: float | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                receipt = json.loads(line)
            except Exception:
                continue
            if not isinstance(receipt, dict):
                continue
            timestamp_seconds = _receipt_timestamp_seconds(receipt)
            if collapse_ws(str(receipt.get("kind", ""))) == "user_prompt":
                current_prompt_started_at = timestamp_seconds
            elapsed_seconds: float | None = None
            if collapse_ws(str(receipt.get("kind", ""))) == "capability_call":
                signature = _capability_receipt_signature(receipt)
                phase = collapse_ws(str(receipt.get("phase", ""))).casefold()
                if signature:
                    if phase == "started":
                        started_timestamps_by_signature.setdefault(signature, []).append(timestamp_seconds)
                    else:
                        started_candidates = started_timestamps_by_signature.get(signature, [])
                        if started_candidates:
                            started_at = started_candidates.pop(0)
                            elapsed_seconds = max(0.0, timestamp_seconds - started_at)
                            if not started_candidates:
                                started_timestamps_by_signature.pop(signature, None)
            prompt_elapsed: float | None = None
            if current_prompt_started_at is not None:
                prompt_elapsed = max(0.0, timestamp_seconds - current_prompt_started_at)
            event_view = workstation_activity_event_view(
                receipt,
                elapsed_seconds=elapsed_seconds,
                prompt_elapsed_seconds=prompt_elapsed,
            )
            if event_view is not None and collapse_ws(event_view.message):
                events.append(event_view)
    if supplemental_events:
        events.extend(item for item in supplemental_events if isinstance(item, WorkstationActivityEventView))
    bounded_limit = max(1, min(int(limit or 50), 500))
    return WorkstationActivityFeedView(events=annotate_workstation_activity_events(tuple(events[-bounded_limit:])))


def workstation_workflow_summary_list_view(
    *,
    root_path: Path,
    kind: str = "runs",
    status: str = "",
    limit: int = 20,
) -> WorkstationWorkflowSummaryListView:
    root = Path(root_path).expanduser().resolve()
    normalized_kind = collapse_ws(str(kind)) or "runs"
    collection_name = "plans" if normalized_kind.casefold() == "plans" else "runs"
    index_payload = load_blend_workflow_index(root)
    items = list_blend_workflow_summaries(
        root,
        kind=normalized_kind,
        status=status,
        limit=limit,
    )
    return WorkstationWorkflowSummaryListView(
        kind=collection_name,
        items=tuple(_workflow_summary_entry_view(item) for item in items if isinstance(item, dict)),
        returned_count=len(items),
        total_count=len([item for item in index_payload.get(collection_name, []) if isinstance(item, dict)]),
        latest_plan_id=collapse_ws(str(index_payload.get("latest_plan_id", ""))),
        latest_run_id=collapse_ws(str(index_payload.get("latest_run_id", ""))),
    )


def workstation_operator_summary_list_view(
    *,
    context: BlendContext,
    providers: tuple[BlendOperatorProvider, ...] | list[BlendOperatorProvider],
    operator_kind: str = "",
    query: str = "",
    limit: int = 20,
) -> WorkstationOperatorSummaryListView:
    items = list_blend_operator_summaries(
        context=context,
        providers=providers,
        operator_kind=operator_kind,
        query=query,
        limit=limit,
    )
    return WorkstationOperatorSummaryListView(
        operator_kind=collapse_ws(str(operator_kind)),
        query=collapse_ws(str(query)),
        items=tuple(_operator_summary_entry_view(item) for item in items if isinstance(item, dict)),
        returned_count=len(items),
        provider_ids=tuple(item.provider_id for item in providers),
    )


def workstation_operator_detail_view(
    *,
    context: BlendContext,
    providers: tuple[BlendOperatorProvider, ...] | list[BlendOperatorProvider],
    operator_name: str,
    operator_kind: str = "",
) -> WorkstationOperatorDetailView | None:
    operator_summary = get_blend_operator_summary(
        context=context,
        providers=providers,
        operator_name=operator_name,
        operator_kind=operator_kind,
    )
    if operator_summary is None:
        return None
    return WorkstationOperatorDetailView(operator=dict(operator_summary))


def workstation_change_session_capabilities(
    *,
    root: Path,
    session: WorkstationSession,
    added_capabilities: list[str],
    removed_capabilities: list[str],
) -> WorkstationSession:
    from workstation.runtime.core.session import persist_workstation_session

    granted: list[str] = []
    seen: set[str] = set()
    removed = {collapse_ws(str(item)) for item in removed_capabilities if collapse_ws(str(item))}
    for capability in session.allowed_capabilities:
        normalized = collapse_ws(str(capability))
        if not normalized or normalized in seen or normalized in removed:
            continue
        granted.append(normalized)
        seen.add(normalized)
    for capability in added_capabilities:
        normalized = collapse_ws(str(capability))
        if not normalized or normalized in seen:
            continue
        granted.append(normalized)
        seen.add(normalized)
    updated = WorkstationSession(
        session_id=session.session_id,
        root_path=session.root_path,
        created_at=session.created_at,
        attachments=session.attachments,
        allowed_capabilities=tuple(granted),
        openai_profile=session.openai_profile,
        openai_env_var=session.openai_env_var,
        initial_task=session.initial_task,
    )
    persist_workstation_session(root, updated)
    publish_workstation_event(
        root_path=root,
        session_id=updated.session_id,
        event_kind="session_changed",
        payload={
            "allowed_capabilities": list(updated.allowed_capabilities),
            "attachment_names": [attachment.name for attachment in updated.attachments],
        },
    )
    publish_workstation_event(
        root_path=root,
        session_id=updated.session_id,
        event_kind="permissions_changed",
        payload={
            "allowed_capabilities": list(updated.allowed_capabilities),
            "added_capabilities": [collapse_ws(str(item)) for item in added_capabilities if collapse_ws(str(item))],
            "removed_capabilities": [collapse_ws(str(item)) for item in removed_capabilities if collapse_ws(str(item))],
        },
    )
    return updated


def workstation_skill_descriptor_for_query(
    *,
    session: WorkstationSession,
    skill_query: str,
) -> WorkstationSkillDescriptorView:
    artifact, source = _require_resolved_skill(session=session, skill_query=skill_query)
    skill_ir = canonical_skill_ir_from_artifact(artifact)
    declaration = dict(skill_ir.declaration)
    executor_framework = collapse_ws(str(skill_ir.hosting_metadata.get("executor_framework", ""))) or collapse_ws(
        str(skill_ir.runtime_package_reference.get("executor_framework", ""))
    )
    if not executor_framework:
        executor_framework = (
            ability_executor_framework(
                representation=str(getattr(artifact, "representation", "")),
                content=dict(getattr(artifact, "content", {}) or {}),
            )
            or ""
        )
    inputs = tuple(
        _skill_field_view(
            session=session,
            field_name=str(name),
            raw_value=value,
            normalization=skill_ir.normalization,
            io_direction="input",
        )
        for name, value in dict(declaration.get("inputs", {})).items()
    )
    outputs = tuple(
        _skill_field_view(
            session=session,
            field_name=str(name),
            raw_value=value,
            normalization=skill_ir.normalization,
            io_direction="output",
        )
        for name, value in dict(declaration.get("outputs", {})).items()
    )
    return WorkstationSkillDescriptorView(
        skill_title=skill_ir.title,
        kind=skill_ir.kind,
        source_kind=collapse_ws(str(source.get("source_kind", ""))),
        executor_framework=executor_framework,
        risk_tier=collapse_ws(str(declaration.get("risk_tier", ""))),
        authorities_requested=tuple(
            collapse_ws(str(item))
            for item in declaration.get("authorities_requested", [])
            if collapse_ws(str(item))
        ),
        aliases=tuple(str(item) for item in skill_ir.aliases),
        family=dict(skill_ir.family),
        inputs=inputs,
        outputs=outputs,
        input_form=_skill_input_form_view(
            skill_title=skill_ir.title,
            executor_framework=executor_framework,
            fields=inputs,
        ),
    )


def workstation_workflow_query_view(
    *,
    root_path: Path,
    workflow_id: str = "",
    workflow_run_id: str = "",
) -> dict[str, Any]:
    root = Path(root_path).expanduser().resolve()
    normalized_workflow_run_id = collapse_ws(str(workflow_run_id))
    normalized_workflow_id = collapse_ws(str(workflow_id))
    if normalized_workflow_run_id:
        workflow_run = load_blend_workflow_run(root, normalized_workflow_run_id)
        workflow_graph = workstation_workflow_graph_view(
            workflow_plan=workflow_run.plan,
            workflow_run=workflow_run,
        )
        workflow_timeline = workstation_workflow_timeline_view(workflow_run=workflow_run)
        return {
            "status": "ok",
            "kind": "run",
            "workflow_id": workflow_run.workflow_id,
            "workflow_run_id": workflow_run.workflow_run_id,
            "workflow_run": workflow_run.to_dict(),
            "workflow_graph": workflow_graph.to_dict(),
            "workflow_timeline": workflow_timeline.to_dict(),
        }
    if normalized_workflow_id:
        workflow_plan = load_blend_workflow_plan(root, normalized_workflow_id)
        workflow_graph = workstation_workflow_graph_view(
            workflow_plan=workflow_plan,
        )
        related_runs = list_blend_workflow_runs_for_plan(root, normalized_workflow_id)
        workflow_run_history = WorkstationWorkflowSummaryListView(
            kind="runs",
            items=tuple(
                _workflow_summary_entry_view(item)
                for item in related_runs
                if isinstance(item, dict)
            ),
            returned_count=len(related_runs),
            total_count=len(related_runs),
        )
        return {
            "status": "ok",
            "kind": "plan",
            "workflow_id": workflow_plan.workflow_id,
            "workflow_plan": workflow_plan.to_dict(),
            "workflow_graph": workflow_graph.to_dict(),
            "workflow_runs": related_runs,
            "workflow_run_history": workflow_run_history.to_dict(),
        }
    return {
        "status": "error",
        "kind": "",
        "error": "workflow_id or workflow_run_id is required.",
    }


def workstation_invoke_skill_action(
    *,
    root_path: Path,
    skill_query: str,
    raw_inputs: dict[str, Any] | None = None,
) -> WorkstationActionResultView:
    from workstation.runtime.core.capabilities import execute_workstation_capability
    from workstation.runtime.core.session import load_workstation_session

    root = Path(root_path).expanduser().resolve()
    session = load_workstation_session(root)
    try:
        descriptor = workstation_skill_descriptor_for_query(
            session=session,
            skill_query=skill_query,
        )
    except Exception as exc:
        return WorkstationActionResultView(
            action_kind="skill_invoke",
            status="error",
            title=f"Skill: {collapse_ws(str(skill_query)) or '<unknown>'}",
            message=collapse_ws(str(exc)) or "Unable to resolve skill.",
        )
    invocation_payload = _normalized_skill_form_payload(
        descriptor=descriptor,
        raw_inputs=raw_inputs or {},
    )
    result = execute_workstation_capability(
        session,
        "ws.skill.invoke",
        {
            "target": "skills",
            "skill_title": descriptor.skill_title,
            "invocation_payload": invocation_payload,
        },
    )
    return _action_result_view_from_capability_result(
        action_kind="skill_invoke",
        title=f"Skill: {descriptor.skill_title}",
        result=result,
    )


def workstation_run_workflow_action(
    *,
    root_path: Path,
    workflow_id: str = "",
    workflow_run_id: str = "",
) -> WorkstationActionResultView:
    from workstation.runtime.core.capabilities import execute_workstation_capability
    from workstation.runtime.core.session import load_workstation_session

    root = Path(root_path).expanduser().resolve()
    session = load_workstation_session(root)
    normalized_workflow_id = collapse_ws(str(workflow_id))
    normalized_workflow_run_id = collapse_ws(str(workflow_run_id))
    if not normalized_workflow_id and normalized_workflow_run_id:
        try:
            normalized_workflow_id = load_blend_workflow_run(root, normalized_workflow_run_id).workflow_id
        except FileNotFoundError:
            normalized_workflow_id = ""
    if not normalized_workflow_id:
        return WorkstationActionResultView(
            action_kind="workflow_run",
            status="error",
            title="Workflow Run",
            message="workflow_id or workflow_run_id is required.",
            workflow_run_id=normalized_workflow_run_id,
        )
    result = execute_workstation_capability(
        session,
        "ws.workflow.run",
        {"workflow_id": normalized_workflow_id},
    )
    return _action_result_view_from_capability_result(
        action_kind="workflow_run",
        title="Workflow Run",
        result=result,
    )


def workstation_chat_transcript_view(
    *,
    root_path: Path,
    limit: int = 120,
) -> WorkstationChatTranscriptView:
    root = Path(root_path).expanduser().resolve()
    message_path = root / "MESSAGES.jsonl"
    messages: list[WorkstationChatMessageView] = []
    if message_path.exists():
        for line in message_path.read_text().splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            role = collapse_ws(str(payload.get("role", ""))) or "message"
            content = str(payload.get("content", "") or "")
            messages.append(
                WorkstationChatMessageView(
                    role=role,
                    content=content,
                    timestamp_epoch_ms=_message_timestamp_epoch_ms(payload),
                    message_id=collapse_ws(str(payload.get("message_id", ""))),
                    turn_id=collapse_ws(str(payload.get("turn_id", ""))),
                    sequence=int(payload.get("sequence", 0) or 0),
                )
            )
    return WorkstationChatTranscriptView(messages=tuple(messages[-max(int(limit), 1) :]))


def workstation_prompt_action(
    *,
    root_path: Path,
    prompt: str,
    model: str | None = None,
    max_tool_rounds: int = 8,
) -> WorkstationActionResultView:
    from workstation.runtime.core.session import prompt_workstation_session

    normalized_prompt = str(prompt or "").strip()
    if not normalized_prompt:
        return WorkstationActionResultView(
            action_kind="chat_prompt",
            status="error",
            title="Chat Prompt",
            message="Prompt is required.",
        )
    try:
        result = prompt_workstation_session(
            root_path=Path(root_path).expanduser().resolve(),
            prompt=normalized_prompt,
            model=model,
            max_tool_rounds=max_tool_rounds,
        )
    except Exception as exc:
        return WorkstationActionResultView(
            action_kind="chat_prompt",
            status="error",
            title="Chat Prompt",
            message=collapse_ws(str(exc)) or "Prompt execution failed.",
        )
    status = "ok"
    fulfilled_by = collapse_ws(str(result.get("fulfilled_by", "")))
    rounds = int(result.get("rounds", 0) or 0)
    details = tuple(
        item
        for item in (
            f"Fulfilled by: {fulfilled_by}" if fulfilled_by else "",
            f"Rounds: {rounds}",
        )
        if item
    )
    return WorkstationActionResultView(
        action_kind="chat_prompt",
        status=status,
        title="Chat Prompt",
        message=str(result.get("assistant_text", "") or ""),
        details=details,
        payload_preview=_short_preview(_json_preview(result.get("tool_receipts", [])), limit=240),
        payload=json_safe(result),
    )


def workstation_learn_markdown_action(
    *,
    root_path: Path,
    markdown_path: Path,
    max_artifacts: int = 8,
    progress_callback: Callable[[str], None] | None = None,
    testing_lightweight: bool = False,
) -> WorkstationActionResultView:
    from workstation.runtime.core.capabilities import execute_workstation_capability
    from workstation.runtime.core.session import load_workstation_session

    root = Path(root_path).expanduser().resolve()
    source_markdown_path = Path(markdown_path).expanduser().resolve()

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    if not source_markdown_path.exists() or not source_markdown_path.is_file():
        return WorkstationActionResultView(
            action_kind="learn_markdown",
            status="error",
            title="Learn Markdown",
            message=f"Markdown source does not exist: {source_markdown_path}",
        )
    if source_markdown_path.suffix.casefold() not in {".md", ".markdown"}:
        return WorkstationActionResultView(
            action_kind="learn_markdown",
            status="error",
            title="Learn Markdown",
            message="Select a Markdown file ending in .md or .markdown.",
        )
    _emit_progress(f"Preparing markdown learning for: {source_markdown_path.name}")
    session = load_workstation_session(root)
    report: dict[str, Any] = {}
    learning_context_root = str(root)
    with tempfile.TemporaryDirectory(prefix="workstation-markdown-learn-") as tempdir_text:
        tempdir = Path(tempdir_text)
        learned_bundle_path = tempdir / normalized_skill_bundle_filename_for_source(source_markdown_path)
        report_path = tempdir / "report.json"
        _emit_progress("Converting markdown to a portable skill bundle...")
        command = _runtime_cli_command(
            "convert-markdown-to-yaml",
            "--markdown-file",
            str(source_markdown_path),
            "--out",
            str(learned_bundle_path),
            "--report-out",
            str(report_path),
            "--max-artifacts",
            str(max(1, int(max_artifacts))),
        )
        if testing_lightweight:
            command.extend(["--llm", "off"])
        command_env = dict(os.environ)
        command_env["LEARNING_CONTEXT_ROOT"] = learning_context_root
        if testing_lightweight:
            command_env["STATE_VECTOR_MODE"] = "off"
            command_env["LLM_SUPPLEMENT_POLICY"] = "off"
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=_runtime_cli_cwd(),
            env=command_env,
        )
        if process.returncode != 0:
            _emit_progress("Markdown conversion failed.")
            return WorkstationActionResultView(
                action_kind="learn_markdown",
                status="error",
                title="Learn Markdown",
                message=_short_preview(
                    collapse_ws(process.stderr) or collapse_ws(process.stdout) or "Markdown learning failed.",
                    limit=240,
                ),
                details=tuple(
                    item
                    for item in (
                        f"Markdown: {source_markdown_path}",
                        f"Command: {' '.join(command)}",
                        f"LearningContext root: {learning_context_root}",
                    )
                ),
            )
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text())
            except Exception:
                report = {}
        _emit_progress("Staging learned bundle for workstation import...")
        staged_relative_path = Path("learned_markdown") / learned_bundle_path.name
        staged_source_path = root / staged_relative_path
        staged_source_path.parent.mkdir(parents=True, exist_ok=True)
        staged_source_path.write_text(learned_bundle_path.read_text())
        _emit_progress("Importing learned bundle into the workstation skill store...")
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "session",
                "path": str(staged_relative_path).replace("\\", "/"),
                "canonical_export_path": learned_bundle_path.name,
            },
        )
    status = collapse_ws(str(import_result.get("status", ""))) or "error"
    imported_titles = tuple(
        collapse_ws(str(item.get("title", "")))
        for item in import_result.get("imported", [])
        if isinstance(item, dict) and collapse_ws(str(item.get("title", "")))
    )
    canonical_export_path = collapse_ws(str(import_result.get("canonical_export_path", "")))
    publish_workstation_event(
        root_path=root,
        session_id=session.session_id,
        event_kind="markdown_learning_completed",
        payload={
            "markdown_path": str(source_markdown_path),
            "learned_count": int(report.get("learned_count", 0) or 0),
            "imported_count": int(import_result.get("imported_count", 0) or 0),
            "imported_titles": list(imported_titles),
            "canonical_export_path": canonical_export_path,
            "learning_context_root": learning_context_root,
            "context_path": str(report.get("context_path", "")),
            "subject_id": str(report.get("subject_id", "")),
            "status": status,
        },
    )
    if status == "ok":
        _emit_progress(
            f"Imported {int(import_result.get('imported_count', 0) or 0)} "
            f"skill{'' if int(import_result.get('imported_count', 0) or 0) == 1 else 's'} from markdown."
        )
    else:
        _emit_progress("Markdown learning finished with an import error.")
    return WorkstationActionResultView(
        action_kind="learn_markdown",
        status=status,
        title="Learn Markdown",
        message=(
            f"Imported {int(import_result.get('imported_count', 0) or 0)} skill"
            f"{'' if int(import_result.get('imported_count', 0) or 0) == 1 else 's'} from {source_markdown_path.name}."
        ),
        details=tuple(
            item
            for item in (
                f"Markdown: {source_markdown_path}",
                f"LearningContext root: {learning_context_root}",
                f"Context path: {collapse_ws(str(report.get('context_path', '')))}" if collapse_ws(str(report.get("context_path", ""))) else "",
                f"Subject id: {collapse_ws(str(report.get('subject_id', '')))}" if collapse_ws(str(report.get("subject_id", ""))) else "",
                f"Learned artifacts: {int(report.get('learned_count', 0) or 0)}",
                f"Imported count: {int(import_result.get('imported_count', 0) or 0)}",
                f"Imported titles: {', '.join(imported_titles) if imported_titles else '<none>'}",
                f"Canonical export: {canonical_export_path}" if canonical_export_path else "",
            )
            if item
        ),
        payload_preview=_short_preview(_json_preview(report), limit=240),
        payload=json_safe(
            {
                "markdown_path": str(source_markdown_path),
                "report": report,
                "import_result": import_result,
                "canonical_export_path": canonical_export_path,
                "suggested_export_filename": learned_bundle_path.name,
                "imported_titles": list(imported_titles),
                "learning_context_root": learning_context_root,
            }
        ),
    )


def workstation_stage_markdown_source_action(
    *,
    root_path: Path,
    markdown_path: Path,
    subject_id: str = "",
    subject_title: str = "",
    progress_callback: Callable[[str], None] | None = None,
) -> WorkstationActionResultView:
    root = Path(root_path).expanduser().resolve()
    source_markdown_path = Path(markdown_path).expanduser().resolve()

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    if not source_markdown_path.exists() or not source_markdown_path.is_file():
        return WorkstationActionResultView(
            action_kind="stage_markdown_source",
            status="error",
            title="Stage Markdown Source",
            message=f"Markdown source does not exist: {source_markdown_path}",
        )
    if source_markdown_path.suffix.casefold() not in {".md", ".markdown"}:
        return WorkstationActionResultView(
            action_kind="stage_markdown_source",
            status="error",
            title="Stage Markdown Source",
            message="Select a Markdown file ending in .md or .markdown.",
        )

    markdown_text = source_markdown_path.read_text(encoding="utf-8")
    inferred_title = (
        collapse_ws(subject_title)
        or _first_markdown_heading(markdown_text)
        or source_markdown_path.stem.replace("-", " ").replace("_", " ").strip()
        or source_markdown_path.stem
        or "Gather Source"
    )
    normalized_source_ref = str(source_markdown_path)

    _emit_progress(f"Preparing markdown capture for: {source_markdown_path.name}")
    _emit_progress("Creating Gather source workspace...")
    resolved_subject_id, resolved_subject_title, context_path = _ensure_gather_subject_workspace(
        root_path=root,
        subject_id=collapse_ws(subject_id),
        subject_title=inferred_title,
    )
    _emit_progress("Saving markdown source into Gather...")
    staged_source = new_staged_source(
        subject_id=resolved_subject_id,
        title=inferred_title,
        source_ref=normalized_source_ref,
        source_kind="markdown",
        media_type="text/markdown",
        metadata={
            "original_path": normalized_source_ref,
            "source_name": source_markdown_path.name,
        },
    )
    try:
        existing_source = load_staged_source(root, resolved_subject_id, staged_source.staged_source_id)
    except Exception:
        existing_source = None
    revision = new_source_revision(
        staged_source_id=staged_source.staged_source_id,
        subject_id=resolved_subject_id,
        source_ref=normalized_source_ref,
        revision_kind="capture",
        metadata={
            "source_metadata": {
                "original_path": normalized_source_ref,
                "source_name": source_markdown_path.name,
            },
        },
    )
    revision_target, markdown_target, persisted_bundle_paths = persist_source_revision(
        root,
        revision,
        markdown_text=markdown_text,
        bundle_files={},
    )
    persisted_source_path = persist_staged_source(
        root,
        StagedSource(
            staged_source_id=staged_source.staged_source_id,
            subject_id=staged_source.subject_id,
            title=staged_source.title,
            source_ref=staged_source.source_ref,
            source_kind=staged_source.source_kind,
            media_type=staged_source.media_type,
            status="staged",
            latest_revision_id=revision.revision_id,
            revision_count=(existing_source.revision_count + 1) if existing_source is not None else 1,
            created_at_epoch_ms=existing_source.created_at_epoch_ms if existing_source is not None else staged_source.created_at_epoch_ms,
            updated_at_epoch_ms=revision.created_at_epoch_ms,
            metadata=dict(staged_source.metadata),
        ),
    )
    publish_workstation_event(
        root_path=root,
        session_id="",
        event_kind="markdown_source_staged",
        payload={
            "markdown_path": normalized_source_ref,
            "title": inferred_title,
            "subject_id": resolved_subject_id,
            "subject_title": resolved_subject_title,
            "context_path": context_path,
            "staged_source_id": staged_source.staged_source_id,
            "revision_id": revision.revision_id,
            "status": "ok",
        },
    )
    _emit_progress("Staged markdown source in Gather.")
    return WorkstationActionResultView(
        action_kind="stage_markdown_source",
        status="ok",
        title="Stage Markdown Source",
        message=f"Staged markdown source for {resolved_subject_title}.",
        details=tuple(
            item
            for item in (
                f"Markdown: {source_markdown_path}",
                f"Title: {inferred_title}",
                f"Subject id: {resolved_subject_id}",
                f"Context path: {context_path}",
                f"Staged source id: {staged_source.staged_source_id}",
                f"Revision id: {revision.revision_id}",
                f"Revision markdown: {markdown_target}",
                f"Revision bundle root: {staged_source_bundle_root(root, resolved_subject_id, revision.revision_id)}",
                f"Bundle files: {len(persisted_bundle_paths)}",
                f"Staged source record: {persisted_source_path}",
                f"Source revision record: {revision_target}",
            )
            if item
        ),
        payload=json_safe(
            {
                "markdown_path": normalized_source_ref,
                "subject_id": resolved_subject_id,
                "subject_title": resolved_subject_title,
                "context_path": context_path,
                "staged_source_id": staged_source.staged_source_id,
                "revision_id": revision.revision_id,
                "revision_markdown_path": str(markdown_target),
                "revision_bundle_root": str(staged_source_bundle_root(root, resolved_subject_id, revision.revision_id)),
            }
        ),
    )


def workstation_learn_url_action(
    *,
    root_path: Path,
    source_url: str | None = None,
    url: str | None = None,
    subject_id: str = "",
    subject_title: str = "",
    max_artifacts: int = 8,
    max_assets: int = 8,
    progress_callback: Callable[[str], None] | None = None,
) -> WorkstationActionResultView:
    from url_learning_capture import capture_url_learning_bundle

    root = Path(root_path).expanduser().resolve()
    normalized_url = collapse_ws(source_url or url)

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    if not normalized_url:
        return WorkstationActionResultView(
            action_kind="learn_url",
            status="error",
            title="Learn URL",
            message="Enter a URL to learn from.",
        )
    _emit_progress(f"Preparing URL capture for: {normalized_url}")
    try:
        _emit_progress("Fetching URL and extracting canonical markdown...")
        capture = capture_url_learning_bundle(
            url=normalized_url,
            max_assets=max_assets,
        )
    except Exception as exc:
        _emit_progress("URL capture failed.")
        return WorkstationActionResultView(
            action_kind="learn_url",
            status="error",
            title="Learn URL",
            message=collapse_ws(str(exc)) or "URL capture failed.",
            details=(f"URL: {normalized_url}",),
        )
    resolved_subject_title = collapse_ws(subject_title) or capture.title or capture.suggested_source_name or normalized_url
    _emit_progress("Creating Gather source workspace...")
    resolved_subject_id, resolved_subject_title, context_path = _ensure_gather_subject_workspace(
        root_path=root,
        subject_id=collapse_ws(subject_id),
        subject_title=resolved_subject_title,
    )
    _emit_progress("Saving captured source into Gather...")
    staged_source = new_staged_source(
        subject_id=resolved_subject_id,
        title=capture.title or capture.suggested_source_name or normalized_url,
        source_ref=capture.requested_url or normalized_url,
        source_kind="url",
        media_type=capture.media_type,
        metadata={
            "requested_url": capture.requested_url,
            "final_url": capture.final_url,
            "status_code": capture.status_code,
            "fetched_at_epoch_ms": capture.fetched_at_epoch_ms,
        },
    )
    try:
        existing_source = load_staged_source(root, resolved_subject_id, staged_source.staged_source_id)
    except Exception:
        existing_source = None
    revision = new_source_revision(
        staged_source_id=staged_source.staged_source_id,
        subject_id=resolved_subject_id,
        source_ref=capture.requested_url or normalized_url,
        revision_kind="capture",
        metadata={
            "capture_report": capture.report(),
            "source_metadata": dict(capture.metadata),
        },
    )
    revision_target, markdown_target, persisted_bundle_paths = persist_source_revision(
        root,
        revision,
        markdown_text=capture.markdown_text,
        bundle_files=capture.bundle_files,
    )
    persisted_source_path = persist_staged_source(
        root,
        StagedSource(
            staged_source_id=staged_source.staged_source_id,
            subject_id=staged_source.subject_id,
            title=staged_source.title,
            source_ref=staged_source.source_ref,
            source_kind=staged_source.source_kind,
            media_type=staged_source.media_type,
            status="staged",
            latest_revision_id=revision.revision_id,
            revision_count=(existing_source.revision_count + 1) if existing_source is not None else 1,
            created_at_epoch_ms=existing_source.created_at_epoch_ms if existing_source is not None else staged_source.created_at_epoch_ms,
            updated_at_epoch_ms=revision.created_at_epoch_ms,
            metadata=dict(staged_source.metadata),
        ),
    )
    publish_workstation_event(
        root_path=root,
        session_id="",
        event_kind="url_source_staged",
        payload={
            "source_url": normalized_url,
            "final_url": capture.final_url,
            "title": capture.title,
            "subject_id": resolved_subject_id,
            "subject_title": resolved_subject_title,
            "context_path": context_path,
            "staged_source_id": staged_source.staged_source_id,
            "revision_id": revision.revision_id,
            "status": "ok",
            "asset_count": len(capture.asset_manifest),
        },
    )
    _emit_progress("Staged URL source in Gather.")
    return WorkstationActionResultView(
        action_kind="learn_url",
        status="ok",
        title="Learn URL",
        message=f"Staged URL source for {resolved_subject_title}.",
        details=tuple(
            item
            for item in (
                f"Requested URL: {capture.requested_url}",
                f"Final URL: {capture.final_url}",
                f"Title: {capture.title}" if collapse_ws(capture.title) else "",
                f"Subject id: {resolved_subject_id}",
                f"Context path: {context_path}",
                f"Staged source id: {staged_source.staged_source_id}",
                f"Revision id: {revision.revision_id}",
                f"Revision markdown: {markdown_target}",
                f"Revision bundle root: {staged_source_bundle_root(root, resolved_subject_id, revision.revision_id)}",
                f"Preserved assets: {len(capture.asset_manifest)}",
                f"Bundle files: {len(persisted_bundle_paths)}",
                f"Staged source record: {persisted_source_path}",
                f"Source revision record: {revision_target}",
            )
            if item
        ),
        payload_preview=_short_preview(_json_preview(capture.report()), limit=240),
        payload=json_safe(
            {
                "source_url": normalized_url,
                "capture_report": capture.report(),
                "subject_id": resolved_subject_id,
                "subject_title": resolved_subject_title,
                "context_path": context_path,
                "staged_source_id": staged_source.staged_source_id,
                "revision_id": revision.revision_id,
                "revision_markdown_path": str(markdown_target),
                "revision_bundle_root": str(staged_source_bundle_root(root, resolved_subject_id, revision.revision_id)),
            }
        ),
    )


def workstation_refresh_staged_source_action(
    *,
    root_path: Path,
    subject_id: str,
    staged_source_id: str = "",
    max_assets: int = 8,
    progress_callback: Callable[[str], None] | None = None,
) -> WorkstationActionResultView:
    from url_learning_capture import capture_url_learning_bundle

    root = Path(root_path).expanduser().resolve()
    normalized_subject_id = collapse_ws(subject_id)
    if not normalized_subject_id:
        return WorkstationActionResultView(
            action_kind="refresh_staged_source",
            status="error",
            title="Refresh Staged Source",
            message="Open a subject workspace first.",
        )

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    staged_sources = list_staged_sources(root, normalized_subject_id)
    selected = None
    if collapse_ws(staged_source_id):
        for item in staged_sources:
            if item.staged_source_id == collapse_ws(staged_source_id):
                selected = item
                break
    elif staged_sources:
        selected = staged_sources[0]
    if selected is None:
        return WorkstationActionResultView(
            action_kind="refresh_staged_source",
            status="error",
            title="Refresh Staged Source",
            message="No staged source is available for this subject.",
        )
    if collapse_ws(selected.source_kind).casefold() != "url":
        return WorkstationActionResultView(
            action_kind="refresh_staged_source",
            status="error",
            title="Refresh Staged Source",
            message="Only URL-backed staged sources can be refreshed right now.",
        )
    source_url = collapse_ws(selected.source_ref) or collapse_ws(str(selected.metadata.get("requested_url", "")))
    if not source_url:
        return WorkstationActionResultView(
            action_kind="refresh_staged_source",
            status="error",
            title="Refresh Staged Source",
            message="The selected staged source is missing its source URL.",
        )
    previous_revision = latest_source_revision(root, selected)
    _emit_progress(f"Refreshing staged source: {selected.title or selected.staged_source_id}")
    try:
        _emit_progress("Fetching URL and extracting canonical markdown...")
        capture = capture_url_learning_bundle(
            url=source_url,
            max_assets=max_assets,
        )
    except Exception as exc:
        _emit_progress("Staged source refresh failed.")
        return WorkstationActionResultView(
            action_kind="refresh_staged_source",
            status="error",
            title="Refresh Staged Source",
            message=collapse_ws(str(exc)) or "Staged source refresh failed.",
            details=(
                f"Subject id: {selected.subject_id}",
                f"Staged source id: {selected.staged_source_id}",
                f"Source URL: {source_url}",
            ),
        )
    _emit_progress("Saving refreshed source revision into Gather...")
    revision = new_source_revision(
        staged_source_id=selected.staged_source_id,
        subject_id=selected.subject_id,
        source_ref=capture.requested_url or source_url,
        revision_kind="refresh",
        metadata={
            "capture_report": capture.report(),
            "source_metadata": dict(capture.metadata),
            "previous_revision_id": previous_revision.revision_id if previous_revision is not None else "",
            "refresh_mode": "url_capture",
        },
    )
    revision_target, markdown_target, persisted_bundle_paths = persist_source_revision(
        root,
        revision,
        markdown_text=capture.markdown_text,
        bundle_files=capture.bundle_files,
    )
    updated_metadata = dict(selected.metadata)
    updated_metadata.update(
        {
            "requested_url": capture.requested_url,
            "final_url": capture.final_url,
            "status_code": capture.status_code,
            "fetched_at_epoch_ms": capture.fetched_at_epoch_ms,
            "last_refresh_revision_id": revision.revision_id,
            "last_refresh_mode": "url_capture",
        }
    )
    refreshed_source = StagedSource(
        staged_source_id=selected.staged_source_id,
        subject_id=selected.subject_id,
        title=selected.title or capture.title or capture.suggested_source_name or source_url,
        source_ref=selected.source_ref or capture.requested_url or source_url,
        source_kind=selected.source_kind,
        media_type=capture.media_type or selected.media_type,
        status=selected.status,
        latest_revision_id=revision.revision_id,
        revision_count=max(0, int(selected.revision_count or 0)) + 1,
        created_at_epoch_ms=selected.created_at_epoch_ms,
        updated_at_epoch_ms=revision.created_at_epoch_ms,
        metadata=updated_metadata,
    )
    persisted_source_path = persist_staged_source(root, refreshed_source)
    publish_workstation_event(
        root_path=root,
        session_id="",
        event_kind="url_source_refreshed",
        payload={
            "source_url": source_url,
            "final_url": capture.final_url,
            "title": refreshed_source.title,
            "subject_id": refreshed_source.subject_id,
            "staged_source_id": refreshed_source.staged_source_id,
            "revision_id": revision.revision_id,
            "status": "ok",
            "asset_count": len(capture.asset_manifest),
        },
    )
    _emit_progress("Refreshed staged source in Gather.")
    return WorkstationActionResultView(
        action_kind="refresh_staged_source",
        status="ok",
        title="Refresh Staged Source",
        message=f"Refreshed staged source for {refreshed_source.title or refreshed_source.staged_source_id}.",
        details=tuple(
            item
            for item in (
                f"Requested URL: {capture.requested_url}",
                f"Final URL: {capture.final_url}",
                f"Title: {capture.title}" if collapse_ws(capture.title) else "",
                f"Subject id: {refreshed_source.subject_id}",
                f"Staged source id: {refreshed_source.staged_source_id}",
                f"Revision id: {revision.revision_id}",
                f"Revision markdown: {markdown_target}",
                f"Revision bundle root: {staged_source_bundle_root(root, refreshed_source.subject_id, revision.revision_id)}",
                f"Preserved assets: {len(capture.asset_manifest)}",
                f"Bundle files: {len(persisted_bundle_paths)}",
                f"Staged source record: {persisted_source_path}",
                f"Source revision record: {revision_target}",
            )
            if item
        ),
        payload_preview=_short_preview(_json_preview(capture.report()), limit=240),
        payload=json_safe(
            {
                "source_url": source_url,
                "capture_report": capture.report(),
                "subject_id": refreshed_source.subject_id,
                "staged_source_id": refreshed_source.staged_source_id,
                "revision_id": revision.revision_id,
                "revision_markdown_path": str(markdown_target),
                "revision_bundle_root": str(staged_source_bundle_root(root, refreshed_source.subject_id, revision.revision_id)),
            }
        ),
    )


def workstation_sync_source_collection_action(
    *,
    root_path: Path,
    subject_id: str,
    collection_id: str = "",
    max_assets: int = 8,
    progress_callback: Callable[[str], None] | None = None,
) -> WorkstationActionResultView:
    root = Path(root_path).expanduser().resolve()
    normalized_subject_id = collapse_ws(subject_id)
    if not normalized_subject_id:
        return WorkstationActionResultView(
            action_kind="sync_source_collection",
            status="error",
            title="Sync Source Set",
            message="Open a subject workspace first.",
        )

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    collections = list_source_collections(root, normalized_subject_id)
    if not collections:
        return WorkstationActionResultView(
            action_kind="sync_source_collection",
            status="error",
            title="Sync Source Set",
            message="No source set is available for this subject.",
        )
    selected_collection: SourceCollection | None = None
    if collapse_ws(collection_id):
        for item in collections:
            if collapse_ws(item.collection_id) == collapse_ws(collection_id):
                selected_collection = item
                break
    if selected_collection is None:
        selected_collection = collections[0]

    staged_sources = list_staged_sources(root, normalized_subject_id)
    staged_source_by_id = {
        collapse_ws(item.staged_source_id): item
        for item in staged_sources
        if collapse_ws(item.staged_source_id)
    }
    member_ids = [
        collapse_ws(item)
        for item in selected_collection.staged_source_ids
        if collapse_ws(item)
    ]
    member_sources = [
        staged_source_by_id[item_id]
        for item_id in member_ids
        if item_id in staged_source_by_id
    ]
    refreshable_sources = [
        item
        for item in member_sources
        if collapse_ws(item.source_kind).casefold() == "url" and bool(collapse_ws(item.source_ref))
    ]
    skipped_count = max(0, len(member_sources) - len(refreshable_sources))
    if not refreshable_sources:
        return WorkstationActionResultView(
            action_kind="sync_source_collection",
            status="error",
            title="Sync Source Set",
            message="The selected source set has no URL-backed staged sources to sync.",
            details=(
                f"Subject id: {normalized_subject_id}",
                f"Source set: {selected_collection.title or selected_collection.collection_id}",
            ),
        )

    _emit_progress(f"Syncing source set: {selected_collection.title or selected_collection.collection_id}")
    refreshed: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []
    for index, staged_source in enumerate(refreshable_sources, start=1):
        _emit_progress(
            f"Refreshing {index}/{len(refreshable_sources)}: {staged_source.title or staged_source.staged_source_id}"
        )
        result = workstation_refresh_staged_source_action(
            root_path=root,
            subject_id=normalized_subject_id,
            staged_source_id=staged_source.staged_source_id,
            max_assets=max_assets,
            progress_callback=progress_callback,
        )
        if collapse_ws(result.status) == "ok":
            payload = result.payload if isinstance(result.payload, dict) else {}
            refreshed.append(
                {
                    "staged_source_id": collapse_ws(staged_source.staged_source_id),
                    "title": collapse_ws(staged_source.title) or collapse_ws(staged_source.staged_source_id),
                    "revision_id": collapse_ws(str(payload.get("revision_id", ""))),
                    "source_url": collapse_ws(str(payload.get("source_url", ""))),
                }
            )
        else:
            failed.append(
                {
                    "staged_source_id": collapse_ws(staged_source.staged_source_id),
                    "title": collapse_ws(staged_source.title) or collapse_ws(staged_source.staged_source_id),
                    "message": collapse_ws(result.message) or "refresh failed",
                }
            )

    now_ms = int(time.time() * 1000)
    updated_collection = SourceCollection(
        collection_id=selected_collection.collection_id,
        subject_id=selected_collection.subject_id,
        title=selected_collection.title,
        description=selected_collection.description,
        staged_source_ids=selected_collection.staged_source_ids,
        query_text=selected_collection.query_text,
        created_at_epoch_ms=selected_collection.created_at_epoch_ms,
        updated_at_epoch_ms=max(now_ms, selected_collection.updated_at_epoch_ms),
        metadata={
            **dict(selected_collection.metadata),
            "last_sync_mode": "url_refresh_batch",
            "last_sync_at_epoch_ms": now_ms,
            "last_sync_refreshable_count": len(refreshable_sources),
            "last_sync_refreshed_count": len(refreshed),
            "last_sync_failed_count": len(failed),
            "last_sync_skipped_count": skipped_count,
        },
    )
    persist_source_collection(root, updated_collection)
    publish_workstation_event(
        root_path=root,
        session_id="",
        event_kind="source_collection_synced",
        payload={
            "subject_id": normalized_subject_id,
            "collection_id": updated_collection.collection_id,
            "collection_title": updated_collection.title,
            "refreshable_count": len(refreshable_sources),
            "refreshed_count": len(refreshed),
            "failed_count": len(failed),
            "skipped_count": skipped_count,
            "status": "ok" if refreshed else "error",
        },
    )
    if refreshed:
        _emit_progress(
            f"Synced {len(refreshed)} of {len(refreshable_sources)} URL-backed sources in the selected source set."
        )
    else:
        _emit_progress("Source-set sync finished without refreshed sources.")
    message = (
        f"Synced source set {updated_collection.title or updated_collection.collection_id}."
        if refreshed and not failed
        else (
            f"Synced source set {updated_collection.title or updated_collection.collection_id} with some failures."
            if refreshed
            else f"Source-set sync failed for {updated_collection.title or updated_collection.collection_id}."
        )
    )
    status = "ok" if refreshed else "error"
    return WorkstationActionResultView(
        action_kind="sync_source_collection",
        status=status,
        title="Sync Source Set",
        message=message,
        details=tuple(
            item
            for item in (
                f"Subject id: {normalized_subject_id}",
                f"Source set: {updated_collection.title or updated_collection.collection_id}",
                f"Refreshable sources: {len(refreshable_sources)}",
                f"Refreshed: {len(refreshed)}",
                f"Failed: {len(failed)}",
                f"Skipped: {skipped_count}",
                *(
                    f"Failed source: {entry.get('title', '<unknown>')} ({entry.get('message', 'refresh failed')})"
                    for entry in failed[:8]
                ),
            )
            if item
        ),
        payload_preview=_short_preview(
            _json_preview(
                {
                    "collection_title": updated_collection.title,
                    "refreshed_count": len(refreshed),
                    "failed_count": len(failed),
                    "skipped_count": skipped_count,
                }
            ),
            limit=240,
        ),
        payload=json_safe(
            {
                "subject_id": normalized_subject_id,
                "collection_id": updated_collection.collection_id,
                "collection_title": updated_collection.title,
                "refreshable_count": len(refreshable_sources),
                "refreshed_count": len(refreshed),
                "failed_count": len(failed),
                "skipped_count": skipped_count,
                "refreshed_sources": refreshed,
                "failed_sources": failed,
            }
        ),
    )


def workstation_import_staged_source_action(
    *,
    root_path: Path,
    subject_id: str,
    staged_source_id: str = "",
    max_artifacts: int = 8,
    progress_callback: Callable[[str], None] | None = None,
) -> WorkstationActionResultView:
    from workstation.runtime.core.capabilities import execute_workstation_capability
    from workstation.runtime.core.session import load_workstation_session

    root = Path(root_path).expanduser().resolve()
    normalized_subject_id = collapse_ws(subject_id)
    if not normalized_subject_id:
        return WorkstationActionResultView(
            action_kind="import_staged_source",
            status="error",
            title="Import Staged Source",
            message="Open a subject workspace first.",
        )

    def _emit_progress(message: str) -> None:
        if progress_callback is None:
            return
        rendered = collapse_ws(str(message))
        if not rendered:
            return
        try:
            progress_callback(rendered)
        except Exception:
            return

    staged_sources = list_staged_sources(root, normalized_subject_id)
    selected = None
    if collapse_ws(staged_source_id):
        for item in staged_sources:
            if item.staged_source_id == collapse_ws(staged_source_id):
                selected = item
                break
    elif staged_sources:
        selected = staged_sources[0]
    if selected is None:
        return WorkstationActionResultView(
            action_kind="import_staged_source",
            status="error",
            title="Import Staged Source",
            message="No staged source is available for this subject.",
        )
    revision = latest_source_revision(root, selected)
    if revision is None:
        return WorkstationActionResultView(
            action_kind="import_staged_source",
            status="error",
            title="Import Staged Source",
            message="The selected staged source has no revision to import.",
        )
    markdown_path = staged_source_body_path(root, selected.subject_id, revision.revision_id)
    if not markdown_path.is_file():
        return WorkstationActionResultView(
            action_kind="import_staged_source",
            status="error",
            title="Import Staged Source",
            message="The selected staged source revision is missing its markdown body.",
        )

    session = load_workstation_session(root)
    _emit_progress(f"Importing staged source: {selected.title or selected.staged_source_id}")
    with tempfile.TemporaryDirectory(prefix="workstation-staged-source-import-") as tempdir_text:
        tempdir = Path(tempdir_text)
        learned_bundle_path = tempdir / normalized_skill_bundle_filename_for_source(markdown_path)
        _emit_progress("Learning reusable artifacts from staged source markdown...")
        try:
            report = _learn_markdown_bundle_in_process(
                root_path=root,
                markdown_path=markdown_path,
                source_label=selected.title or selected.source_ref or selected.staged_source_id,
                bundle_output_path=learned_bundle_path,
                max_artifacts=max_artifacts,
                source_bundle_override=_staged_source_import_override(root, selected, revision),
            )
        except Exception as exc:
            _emit_progress("Staged source import failed.")
            return WorkstationActionResultView(
                action_kind="import_staged_source",
                status="error",
                title="Import Staged Source",
                message=collapse_ws(str(exc)) or "Staged source import failed.",
                details=(
                    f"Subject id: {selected.subject_id}",
                    f"Staged source id: {selected.staged_source_id}",
                    f"Revision id: {revision.revision_id}",
                ),
            )
        if not learned_bundle_path.is_file():
            learned_bundle_path.write_text("", encoding="utf-8")
        staged_relative_path = Path("learned_url") / learned_bundle_path.name
        staged_bundle_path = root / staged_relative_path
        staged_bundle_path.parent.mkdir(parents=True, exist_ok=True)
        staged_bundle_path.write_text(learned_bundle_path.read_text(encoding="utf-8"), encoding="utf-8")
        _emit_progress("Importing learned bundle into the workstation skill store...")
        import_result = execute_workstation_capability(
            session,
            "ws.skill.import",
            {
                "source_target": "session",
                "path": str(staged_relative_path).replace("\\", "/"),
                "canonical_export_path": learned_bundle_path.name,
            },
        )

    status = collapse_ws(str(import_result.get("status", ""))) or "error"
    imported_titles = tuple(
        collapse_ws(str(item.get("title", "")))
        for item in import_result.get("imported", [])
        if isinstance(item, dict) and collapse_ws(str(item.get("title", "")))
    )
    persist_staged_source(
        root,
        StagedSource(
            staged_source_id=selected.staged_source_id,
            subject_id=selected.subject_id,
            title=selected.title,
            source_ref=selected.source_ref,
            source_kind=selected.source_kind,
            media_type=selected.media_type,
            status="imported" if status == "ok" else selected.status,
            latest_revision_id=selected.latest_revision_id,
            revision_count=selected.revision_count,
            created_at_epoch_ms=selected.created_at_epoch_ms,
            updated_at_epoch_ms=selected.updated_at_epoch_ms,
            metadata={
                **dict(selected.metadata),
                "last_imported_revision_id": revision.revision_id if status == "ok" else dict(selected.metadata).get("last_imported_revision_id", ""),
                "last_imported_at_epoch_ms": int(time.time() * 1000) if status == "ok" else dict(selected.metadata).get("last_imported_at_epoch_ms", 0),
            },
        ),
    )
    learning_context_report = report.get("learning_context", {}) if isinstance(report, dict) else {}
    publish_workstation_event(
        root_path=root,
        session_id=session.session_id,
        event_kind="staged_source_import_completed",
        payload={
            "subject_id": normalized_subject_id,
            "staged_source_id": selected.staged_source_id,
            "revision_id": revision.revision_id,
            "status": status,
            "imported_count": int(import_result.get("imported_count", 0) or 0),
            "context_path": str(learning_context_report.get("context_path", "") or report.get("context_path", "")),
        },
    )
    if status == "ok":
        _emit_progress(
            f"Imported {int(import_result.get('imported_count', 0) or 0)} "
            f"skill{'' if int(import_result.get('imported_count', 0) or 0) == 1 else 's'} from staged source."
        )
    else:
        _emit_progress("Staged source import finished with an import error.")
    canonical_export_path = collapse_ws(str(import_result.get("canonical_export_path", "")))
    return WorkstationActionResultView(
        action_kind="import_staged_source",
        status=status,
        title="Import Staged Source",
        message=(
            f"Imported {int(import_result.get('imported_count', 0) or 0)} skill"
            f"{'' if int(import_result.get('imported_count', 0) or 0) == 1 else 's'} from {selected.title or selected.source_ref or selected.staged_source_id}."
        ),
        details=tuple(
            item
            for item in (
                f"Subject id: {selected.subject_id}",
                f"Staged source id: {selected.staged_source_id}",
                f"Revision id: {revision.revision_id}",
                f"Context path: {collapse_ws(str(learning_context_report.get('context_path', '') or report.get('context_path', '')))}",
                f"Imported count: {int(import_result.get('imported_count', 0) or 0)}",
                f"Imported titles: {', '.join(imported_titles) if imported_titles else '<none>'}",
                f"Canonical export: {canonical_export_path}" if canonical_export_path else "",
            )
            if item
        ),
        payload=json_safe(
            {
                "subject_id": selected.subject_id,
                "staged_source_id": selected.staged_source_id,
                "revision_id": revision.revision_id,
                "report": report,
                "canonical_export_path": canonical_export_path,
                "suggested_export_filename": Path(canonical_export_path).name if canonical_export_path else "",
            }
        ),
    )


def workstation_export_learned_skill_bundle_action(
    *,
    root_path: Path,
    source_bundle_path: Path,
    destination_path: Path,
) -> WorkstationActionResultView:
    from workstation.runtime.core.session import load_workstation_session

    root = Path(root_path).expanduser().resolve()
    source_path = Path(source_bundle_path).expanduser().resolve()
    output_path = Path(destination_path).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        return WorkstationActionResultView(
            action_kind="learned_skill_export",
            status="error",
            title="Export Learned Skill",
            message=f"Learned skill bundle does not exist: {source_path}",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, output_path)
    publish_workstation_event(
        root_path=root,
        session_id=load_workstation_session(root).session_id,
        event_kind="learned_skill_bundle_exported",
        payload={
            "source_bundle_path": str(source_path),
            "destination_path": str(output_path),
            "status": "ok",
        },
    )
    return WorkstationActionResultView(
        action_kind="learned_skill_export",
        status="ok",
        title="Export Learned Skill",
        message=f"Copied learned skill bundle to {output_path}.",
        details=(
            f"Source: {source_path}",
            f"Destination: {output_path}",
        ),
        payload_preview=str(output_path),
        payload=json_safe(
            {
                "source_bundle_path": str(source_path),
                "destination_path": str(output_path),
            }
        ),
    )


def render_workstation_event_activity_line(
    *,
    event_kind: str,
    payload: dict[str, Any],
) -> str:
    from workstation.foundation.projections import render_workstation_activity_event

    event_view = workstation_activity_event_view_from_event(
        event_kind=event_kind,
        payload=payload,
    )
    if event_view is None:
        return ""
    return render_workstation_activity_event(event_view)


def _normalized_skill_form_payload(
    *,
    descriptor: WorkstationSkillDescriptorView,
    raw_inputs: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    fields_by_name = {
        field.field_name: field
        for field in descriptor.input_form.fields
        if collapse_ws(str(field.field_name))
    }
    for field_name, field in fields_by_name.items():
        raw_value = raw_inputs.get(field_name)
        normalized = _normalized_form_field_value(field=field, raw_value=raw_value)
        if normalized is None:
            continue
        payload[field_name] = normalized
    return payload


def _normalized_form_field_value(
    *,
    field: WorkstationSkillFieldView,
    raw_value: Any,
) -> Any:
    if raw_value is None:
        if field.default_value is None:
            return None
        raw_value = field.default_value
    if field.widget_hint == "checkbox":
        if isinstance(raw_value, str):
            return collapse_ws(raw_value).casefold() in {"1", "true", "yes", "on"}
        return bool(raw_value)
    if isinstance(raw_value, str):
        if not field.constraints.get("multiline"):
            raw_value = raw_value.strip()
        if raw_value == "":
            return None
    if field.widget_hint == "number":
        return _normalized_numeric_value(raw_value)
    return raw_value


def _normalized_numeric_value(value: Any) -> Any:
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except Exception:
        try:
            return float(text)
        except Exception:
            return value


def _action_result_view_from_capability_result(
    *,
    action_kind: str,
    title: str,
    result: dict[str, Any],
) -> WorkstationActionResultView:
    status = collapse_ws(str(result.get("status", ""))) or "error"
    workflow_id = collapse_ws(str(result.get("workflow_id", "")))
    workflow_run_id = collapse_ws(str(result.get("workflow_run_id", "")))
    message = (
        collapse_ws(str(result.get("answer", "")))
        or collapse_ws(str(result.get("error", "")))
        or _short_preview(_json_preview(result.get("final_output")), limit=120)
        or _short_preview(_json_preview(result.get("result_payload")), limit=120)
    )
    details: list[str] = []
    capability = collapse_ws(str(result.get("capability", "")))
    if capability:
        details.append(f"Capability: {capability}")
    target = collapse_ws(str(result.get("target", "")))
    if target:
        details.append(f"Target: {target}")
    executor_framework = collapse_ws(str(result.get("executor_framework", "")))
    if executor_framework:
        details.append(f"Executor: {executor_framework}")
    if workflow_id:
        details.append(f"Workflow: {workflow_id}")
    if workflow_run_id:
        details.append(f"Run: {workflow_run_id}")
    payload_preview = _short_preview(
        _json_preview(
            result.get("final_output")
            if result.get("final_output") is not None
            else result.get("result_payload")
        ),
        limit=240,
    )
    return WorkstationActionResultView(
        action_kind=action_kind,
        status=status,
        title=title,
        message=message,
        details=tuple(details),
        payload_preview=payload_preview,
        workflow_id=workflow_id,
        workflow_run_id=workflow_run_id,
        payload=json_safe(result),
    )


def _json_preview(value: Any) -> str:
    if value is None:
        return ""
    try:
        return json.dumps(json_safe(value), sort_keys=True)
    except Exception:
        return collapse_ws(str(value))


def _require_resolved_skill(*, session: WorkstationSession, skill_query: str) -> tuple[Any, dict[str, str]]:
    resolved = resolve_workstation_skill(
        skill_title=skill_query,
        skill_store_path=_workstation_skill_store_path(session),
    )
    if resolved is None:
        raise ValueError(f"No visible workstation skill matches {skill_query!r}.")
    artifact, source = resolved
    return artifact, source


def _workstation_skill_store_path(session: WorkstationSession) -> Path:
    for attachment in session.attachments:
        if attachment.kind == "skill_store" or attachment.name == "skills":
            return Path(str(attachment.source)).expanduser().resolve()
    raise ValueError("This workstation session has no attached skill store.")


def _skill_field_view(
    *,
    session: WorkstationSession,
    field_name: str,
    raw_value: Any,
    normalization: dict[str, Any],
    io_direction: str,
) -> WorkstationSkillFieldView:
    normalized_name = collapse_ws(str(field_name))
    description = ""
    required = io_direction == "input"
    default_value: Any = None
    if isinstance(raw_value, dict):
        description = collapse_ws(
            str(
                raw_value.get("description", "")
                or raw_value.get("answer", "")
                or raw_value.get("notes", "")
            )
        )
        if "required" in raw_value:
            required = bool(raw_value.get("required"))
        if "default" in raw_value:
            default_value = raw_value.get("default")
    else:
        description = collapse_ws(str(raw_value))
        if io_direction == "input" and "optional" in description.casefold():
            required = False
    data_type = _field_data_type_from_normalization(normalization, normalized_name)
    widget_hint = _field_widget_hint(normalized_name, data_type)
    options = _field_options(session=session, field_name=normalized_name)
    return WorkstationSkillFieldView(
        field_name=normalized_name,
        label=_field_label(normalized_name),
        io_direction=io_direction,
        description=description,
        data_type=data_type,
        required=required,
        widget_hint=widget_hint,
        default_value=default_value,
        options=options,
        constraints=_field_constraints(
            field_name=normalized_name,
            io_direction=io_direction,
            data_type=data_type,
            widget_hint=widget_hint,
            required=required,
            default_value=default_value,
            options=options,
        ),
        section=_field_section(normalized_name, widget_hint),
        placeholder=_field_placeholder(
            field_name=normalized_name,
            widget_hint=widget_hint,
            default_value=default_value,
            options=options,
        ),
    )


def _skill_input_form_view(
    *,
    skill_title: str,
    executor_framework: str,
    fields: tuple[WorkstationSkillFieldView, ...],
) -> WorkstationSkillInputFormView:
    return WorkstationSkillInputFormView(
        skill_title=skill_title,
        executor_framework=executor_framework,
        fields=fields,
        sections=_skill_form_sections(fields),
    )


def _field_data_type_from_normalization(normalization: dict[str, Any], field_name: str) -> str:
    needle = collapse_ws(str(field_name)).casefold()
    for region_payload in dict(normalization.get("regions", {})).values():
        if not isinstance(region_payload, dict):
            continue
        for leaf in region_payload.get("leaves", []):
            if not isinstance(leaf, dict):
                continue
            path_text = collapse_ws(str(leaf.get("path", "")))
            tail = path_text.rsplit("/", 1)[-1].casefold() if path_text else ""
            if tail != needle:
                continue
            return collapse_ws(str(leaf.get("data_type", "")))
    return ""


def _field_widget_hint(field_name: str, data_type: str) -> str:
    normalized_name = collapse_ws(str(field_name)).casefold()
    normalized_type = collapse_ws(str(data_type))
    if normalized_name == "mount":
        return "attachment"
    if any(token in normalized_name for token in ("path", "file", "directory", "dir")):
        return "path"
    if "url" in normalized_name:
        return "url"
    if normalized_type in {"Boolean", "Bools"}:
        return "checkbox"
    if normalized_type in {"Int", "Ints", "Float", "Floats"}:
        return "number"
    return "text"


def _field_label(field_name: str) -> str:
    tokens = [part for part in collapse_ws(str(field_name)).replace("_", " ").split(" ") if part]
    if not tokens:
        return ""
    return " ".join(token[:1].upper() + token[1:] for token in tokens)


def _field_options(*, session: WorkstationSession, field_name: str) -> tuple[str, ...]:
    normalized_name = collapse_ws(str(field_name)).casefold()
    if normalized_name != "mount":
        return ()
    options: list[str] = []
    seen: set[str] = set()
    for attachment in session.attachments:
        if attachment.kind == "secret_ref":
            continue
        name = collapse_ws(str(attachment.name))
        if not name or name in seen:
            continue
        seen.add(name)
        options.append(name)
    return tuple(options)


def _field_constraints(
    *,
    field_name: str,
    io_direction: str,
    data_type: str,
    widget_hint: str,
    required: bool,
    default_value: Any,
    options: tuple[str, ...],
) -> dict[str, Any]:
    constraints: dict[str, Any] = {
        "required": bool(required),
        "io_direction": collapse_ws(str(io_direction)),
    }
    if default_value is not None:
        constraints["has_default"] = True
    normalized_name = collapse_ws(str(field_name)).casefold()
    normalized_type = collapse_ws(str(data_type))
    if widget_hint:
        constraints["widget_hint"] = widget_hint
    if options:
        constraints["allowed_values"] = list(options)
    if widget_hint == "attachment":
        constraints["attachment_backed"] = True
    if widget_hint == "path":
        constraints["path_like"] = True
        if normalized_name == "relative_path":
            constraints["path_scope"] = "workspace_relative"
    if widget_hint == "url":
        constraints["url_like"] = True
    if widget_hint == "number":
        constraints["numeric_like"] = True
    if widget_hint == "checkbox":
        constraints["boolean_like"] = True
    if normalized_type in {"Strings", "Bytess", "Ints", "Bools", "Floats"}:
        constraints["repeated"] = True
    if _field_is_multiline(normalized_name, widget_hint):
        constraints["multiline"] = True
    if any(token in normalized_name for token in ("token", "password", "secret", "key")):
        constraints["secret_like"] = True
    return constraints


def _field_section(field_name: str, widget_hint: str) -> str:
    normalized_name = collapse_ws(str(field_name)).casefold()
    if widget_hint in {"attachment", "path"} or any(
        token in normalized_name for token in ("mount", "path", "file", "dir", "directory")
    ):
        return "Location"
    if widget_hint == "url" or any(
        token in normalized_name for token in ("url", "method", "header", "query", "timeout", "page", "size")
    ):
        return "Request"
    if any(
        token in normalized_name
        for token in ("body", "text", "json", "csv", "content", "prompt", "stdin")
    ):
        return "Content"
    if any(token in normalized_name for token in ("symbol", "pattern", "name", "search")):
        return "Selection"
    return "Inputs"


def _field_placeholder(
    *,
    field_name: str,
    widget_hint: str,
    default_value: Any,
    options: tuple[str, ...],
) -> str:
    if default_value is not None:
        return collapse_ws(str(default_value))
    normalized_name = collapse_ws(str(field_name)).casefold()
    if normalized_name == "mount" and "main" in options:
        return "main"
    if options:
        return collapse_ws(str(options[0]))
    if widget_hint == "attachment":
        return "Select attachment"
    if widget_hint == "path":
        return "src/example.txt"
    if widget_hint == "url":
        return "https://example.com"
    if widget_hint == "number":
        return "0"
    if widget_hint == "checkbox":
        return ""
    if "json" in normalized_name:
        return '{"key":"value"}'
    if "csv" in normalized_name:
        return "col1,col2"
    if "text" in normalized_name or "content" in normalized_name or "body" in normalized_name:
        return "Enter text"
    if "symbol" in normalized_name or "pattern" in normalized_name or "name" in normalized_name:
        return "example"
    return ""


def _field_is_multiline(field_name: str, widget_hint: str) -> bool:
    if widget_hint in {"attachment", "path", "url", "number", "checkbox"}:
        return False
    normalized_name = collapse_ws(str(field_name)).casefold()
    return any(token in normalized_name for token in ("body", "text", "json", "csv", "content", "prompt"))


def _skill_form_sections(
    fields: tuple[WorkstationSkillFieldView, ...],
) -> tuple[WorkstationSkillFormSectionView, ...]:
    ordered_sections: list[str] = []
    by_section: dict[str, list[str]] = {}
    for field in fields:
        title = collapse_ws(field.section) or "Inputs"
        if title not in by_section:
            by_section[title] = []
            ordered_sections.append(title)
        by_section[title].append(field.field_name)
    return tuple(
        WorkstationSkillFormSectionView(
            section_id=collapse_ws(title).casefold().replace(" ", "_"),
            title=title,
            field_names=tuple(names),
        )
        for title in ordered_sections
        for names in [by_section.get(title, [])]
    )


def workstation_workflow_timeline_view(
    *,
    workflow_run: Any,
) -> WorkstationWorkflowTimelineView:
    entries: list[WorkstationWorkflowTimelineEntryView] = []
    for index, step in enumerate(getattr(workflow_run, "steps", []) or [], start=1):
        if not isinstance(step, dict):
            continue
        step_id = collapse_ws(str(step.get("step_id", "")))
        operator_name = collapse_ws(
            str(
                step.get("operator_name", "")
                or step.get("skill_title", "")
                or step.get("resolved_target", "")
                or step_id
            )
        )
        title = operator_name or step_id or f"step_{index}"
        output_preview = _workflow_step_output_preview(step)
        entries.append(
            WorkstationWorkflowTimelineEntryView(
                sequence_index=index,
                step_id=step_id,
                title=title,
                status=collapse_ws(str(step.get("status", ""))),
                operator_kind=collapse_ws(str(step.get("operator_kind", ""))),
                operator_name=operator_name,
                branch_label=collapse_ws(str(step.get("branch_label", ""))),
                target=collapse_ws(str(step.get("resolved_target", ""))),
                applicability=collapse_ws(str(step.get("context_applicability", ""))),
                output_preview=output_preview,
            )
        )
    return WorkstationWorkflowTimelineView(
        workflow_id=collapse_ws(str(getattr(workflow_run, "workflow_id", ""))),
        workflow_run_id=collapse_ws(str(getattr(workflow_run, "workflow_run_id", ""))),
        status=collapse_ws(str(getattr(workflow_run, "status", ""))),
        started_at=collapse_ws(str(getattr(workflow_run, "started_at", ""))),
        finished_at=collapse_ws(str(getattr(workflow_run, "finished_at", ""))),
        final_output_step=collapse_ws(str(getattr(workflow_run, "final_output_step", ""))),
        entries=tuple(entries),
    )


def _workflow_summary_entry_view(payload: dict[str, Any]) -> WorkstationWorkflowSummaryEntryView:
    return WorkstationWorkflowSummaryEntryView(
        workflow_id=collapse_ws(str(payload.get("workflow_id", ""))),
        workflow_run_id=collapse_ws(str(payload.get("workflow_run_id", ""))),
        workflow_kind=collapse_ws(str(payload.get("workflow_kind", ""))),
        status=collapse_ws(str(payload.get("status", ""))),
        session_id=collapse_ws(str(payload.get("session_id", ""))),
        step_count=int(payload.get("step_count", 0) or 0),
        final_output_step=collapse_ws(str(payload.get("final_output_step", ""))),
        created_at=collapse_ws(str(payload.get("created_at", ""))),
        started_at=collapse_ws(str(payload.get("started_at", ""))),
        finished_at=collapse_ws(str(payload.get("finished_at", ""))),
        path=collapse_ws(str(payload.get("path", ""))),
    )


def _workflow_step_output_preview(step: dict[str, Any]) -> str:
    preview = _short_preview(str(step.get("answer", "")), limit=72)
    if preview:
        return preview
    parsed_output = step.get("parsed_output")
    if isinstance(parsed_output, dict):
        preview = _first_list_item_preview(parsed_output.get("matches", []))
        if preview:
            return preview
        preview = _short_preview(_jsonish_preview(parsed_output), limit=72)
        if preview:
            return preview
    result_payload = step.get("result_payload")
    if isinstance(result_payload, dict):
        preview = _short_preview(_jsonish_preview(result_payload), limit=72)
        if preview:
            return preview
    return _short_preview(str(step.get("final_output", "")), limit=72)


def _jsonish_preview(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, default=repr)
    except Exception:
        return repr(value)


def _operator_summary_entry_view(payload: dict[str, Any]) -> WorkstationOperatorSummaryEntryView:
    return WorkstationOperatorSummaryEntryView(
        operator_id=collapse_ws(str(payload.get("operator_id", ""))),
        operator_name=collapse_ws(str(payload.get("operator_name", ""))),
        operator_kind=collapse_ws(str(payload.get("operator_kind", ""))),
        source_kind=collapse_ws(str(payload.get("source_kind", ""))),
        execution_adapter=collapse_ws(str(payload.get("execution_adapter", ""))),
        semantic_description=collapse_ws(str(payload.get("semantic_description", ""))),
        provider_id=collapse_ws(str(payload.get("provider_id", ""))),
    )


def _capability_started_activity_message(*, capability: str, arguments: dict[str, Any]) -> str:
    if capability == "ws.permissions.list":
        return "Listing session permissions"
    if capability == "ws.permissions.grant":
        capability_name = collapse_ws(str(arguments.get("capability", "")))
        return f"Granting permission: {capability_name}" if capability_name else "Granting permission"
    if capability == "ws.permissions.revoke":
        capability_name = collapse_ws(str(arguments.get("capability", "")))
        return f"Revoking permission: {capability_name}" if capability_name else "Revoking permission"
    if capability == "ws.net.http":
        method = collapse_ws(str(arguments.get("method", "GET"))).upper() or "GET"
        url = _short_preview(str(arguments.get("url", "")), limit=72)
        return _with_preview(f"HTTP {method}", url, label="in")
    if capability == "ws.skill.import":
        return f"Importing skill from {_display_path(str(arguments.get('path', '')))}"
    if capability == "ws.skill.catalog":
        return "Listing available skills"
    if capability == "ws.skill.describe":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        return f"Describing skill: {title or 'requested skill'}"
    if capability == "ws.skill.export":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        target_path = _display_path(str(arguments.get("out", arguments.get("path", ""))))
        if title and target_path:
            return f"Exporting {title} to {target_path}"
        if title:
            return f"Exporting {title}"
        return "Exporting skill"
    if capability == "ws.skill.permissions":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        return f"Inspecting permissions: {title or 'requested skill'}"
    if capability == "ws.skill.invoke":
        title = _short_skill_title(str(arguments.get("skill_title", "")))
        input_preview = _skill_input_preview(arguments)
        return _with_preview(f"Invoking skill: {title or 'requested skill'}", input_preview, label="in")
    if capability == "ws.skill.compose":
        input_preview = _skill_compose_input_preview(arguments)
        return _with_preview("Composing skills", input_preview, label="in")
    if capability == "ws.repo.search":
        pattern = collapse_ws(str(arguments.get("pattern", "")))
        relative_path = _display_path(str(arguments.get("path", arguments.get("relative_path", ""))))
        if pattern and relative_path:
            return f"Searching {relative_path} for {pattern}"
        if pattern:
            return f"Searching for {pattern}"
        return "Searching workspace"
    if capability == "ws.repo.tree":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Listing {target_path}" if target_path else "Listing workspace"
    if capability == "ws.fs.read":
        target_path = _display_path(str(arguments.get("path", "")))
        return f"Reading {target_path}" if target_path else "Reading file"
    if capability == "ws.process.run":
        argv = arguments.get("argv", [])
        command_text = " ".join(str(item) for item in argv[:4]) if isinstance(argv, list) else ""
        return f"Running command: {command_text}" if command_text else "Running command"
    return f"Running {capability}" if capability else ""


def _capability_finished_activity_message(
    *,
    capability: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    phase: str,
) -> str:
    status = collapse_ws(str(result.get("status", ""))).casefold()
    if capability == "ws.permissions.list":
        granted = result.get("granted_capabilities", [])
        count = len(granted) if isinstance(granted, list) else 0
        return f"Permissions ready: {count} granted" if status == "ok" else "Permission listing failed"
    if capability == "ws.permissions.grant":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        return f"Granted permission: {capability_name or 'capability'}" if status == "ok" else f"Grant failed: {capability_name or 'capability'}"
    if capability == "ws.permissions.revoke":
        capability_name = collapse_ws(str(result.get("capability", arguments.get("capability", ""))))
        return f"Revoked permission: {capability_name or 'capability'}" if status == "ok" else f"Revoke failed: {capability_name or 'capability'}"
    if capability == "ws.net.http":
        method = collapse_ws(str(result.get("method", arguments.get("method", "GET")))).upper() or "GET"
        url = _short_preview(str(result.get("url", arguments.get("url", ""))), limit=72)
        prefix = f"HTTP {method} ok" if status == "ok" else f"HTTP {method} failed"
        return _with_preview(prefix, _net_http_output_preview(result, fallback=url), label="out")
    if capability == "ws.skill.import":
        imported_count = int(result.get("imported_count", 0) or 0)
        if status == "ok":
            return _with_preview(
                f"Imported {imported_count} skill{'s' if imported_count != 1 else ''}",
                _imported_skills_preview(result),
                label="out",
            )
        return "Skill import failed"
    if capability == "ws.skill.catalog":
        returned = int(result.get("returned_skill_count", 0) or 0)
        return f"Listed {returned} skill{'s' if returned != 1 else ''}" if status == "ok" else "Skill listing failed"
    if capability == "ws.skill.describe":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        return f"Described skill: {title or 'skill'}" if status == "ok" else f"Describe failed for {title or 'skill'}"
    if capability == "ws.skill.export":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "ok":
            return _with_preview(
                f"Exported {title or 'skill'}",
                _display_path(str(result.get("destination_path", ""))),
                label="out",
            )
        return f"Export failed for {title or 'skill'}"
    if capability == "ws.skill.permissions":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        return f"Permissions ready: {title or 'skill'}" if status == "ok" else f"Permissions failed for {title or 'skill'}"
    if capability == "ws.skill.invoke":
        title = _short_skill_title(str(result.get("skill_title", arguments.get("skill_title", ""))))
        if status == "approval_required":
            return f"Waiting for approval: {title or 'skill'}"
        if phase == "after_escalation" and status == "ok":
            return _with_preview(f"Skill completed after approval: {title or 'skill'}", _skill_output_preview(result), label="out")
        if status == "ok":
            return _with_preview(f"Skill completed: {title or 'skill'}", _skill_output_preview(result), label="out")
        return _with_preview(f"Skill failed: {title or 'skill'}", _skill_error_preview(result), label="out")
    if capability == "ws.skill.compose":
        if status == "approval_required":
            title = _short_skill_title(str(result.get("blocked_skill_title", "")))
            return f"Waiting for approval: {title or 'skill composition'}"
        output_preview = _skill_compose_output_preview(result)
        if status == "ok":
            return _with_preview("Skill composition completed", output_preview, label="out")
        return _with_preview("Skill composition failed", output_preview or _skill_error_preview(result), label="out")
    if capability == "ws.repo.search":
        match_count = int(result.get("match_count", 0) or 0)
        if status == "ok":
            return _with_preview(
                f"Search completed: {match_count} match{'es' if match_count != 1 else ''}",
                _search_output_preview(result),
                label="out",
            )
        return "Search failed"
    if capability == "ws.repo.tree":
        if status == "ok":
            tree = result.get("tree", [])
            count = len(tree) if isinstance(tree, list) else 0
            return _with_preview(
                f"Listed {count} entr{'ies' if count != 1 else 'y'}",
                _first_list_item_preview(tree),
                label="out",
            )
        return "Listing failed"
    if capability == "ws.fs.read":
        if status == "ok":
            return _with_preview(
                f"Read {_display_path(str(result.get('path', arguments.get('path', ''))))}",
                _content_preview(str(result.get("content", ""))),
                label="out",
            )
        return "Read failed"
    if capability == "ws.process.run":
        exit_code = result.get("exit_code")
        prefix = "Command completed" if exit_code in {0, "0"} else "Command failed"
        return _with_preview(prefix, _process_output_preview(result), label="out")
    if capability:
        if status == "ok":
            return f"Completed {capability}"
        if status:
            return f"{capability} {status}"
    return ""


def _short_skill_title(text: str) -> str:
    raw = collapse_ws(str(text))
    if " / " in raw:
        return raw.split(" / ", 1)[0].strip()
    return raw


def _display_path(text: str) -> str:
    value = collapse_ws(str(text))
    if not value:
        return ""
    return value.rstrip("/")


def _capability_receipt_signature(receipt: dict[str, Any]) -> str:
    capability = collapse_ws(str(receipt.get("capability", "")))
    arguments = receipt.get("arguments", {})
    if not capability or not isinstance(arguments, dict):
        return ""
    try:
        return capability + "|" + json.dumps(arguments, sort_keys=True, separators=(",", ":"))
    except Exception:
        return capability + "|" + repr(arguments)


def _receipt_timestamp_seconds(receipt: dict[str, Any]) -> float:
    raw = collapse_ws(str(receipt.get("timestamp", "")))
    if not raw:
        return time.time()
    try:
        return datetime.fromisoformat(raw).timestamp()
    except Exception:
        return time.time()


def _message_timestamp_epoch_ms(payload: dict[str, Any]) -> int:
    raw_epoch_ms = payload.get("timestamp_epoch_ms", 0)
    try:
        epoch_ms = int(raw_epoch_ms or 0)
    except Exception:
        epoch_ms = 0
    if epoch_ms > 0:
        return epoch_ms
    raw_epoch = payload.get("timestamp_epoch", 0)
    try:
        epoch_seconds = float(raw_epoch or 0)
    except Exception:
        epoch_seconds = 0.0
    if epoch_seconds > 0:
        return int(epoch_seconds * 1000)
    raw_timestamp = collapse_ws(str(payload.get("timestamp", "")))
    if not raw_timestamp:
        return 0
    try:
        return int(datetime.fromisoformat(raw_timestamp).timestamp() * 1000)
    except Exception:
        return 0


def _with_preview(text: str, preview: str, *, label: str) -> str:
    if not preview:
        return text
    return f"{text} [{label}: {preview}]"


def _skill_input_preview(arguments: dict[str, Any]) -> str:
    payload = arguments.get("invocation_payload")
    if not isinstance(payload, dict):
        payload = {}
    items: list[str] = []
    for key, value in payload.items():
        preview = _value_preview(value)
        if preview:
            items.append(f"{key}={preview}")
        if len(items) >= 2:
            break
    if items:
        return ", ".join(items)
    return _short_preview(collapse_ws(str(arguments.get("semantic_unit", ""))), limit=64)


def _skill_output_preview(result: dict[str, Any]) -> str:
    answer = _short_preview(str(result.get("answer", "")), limit=72)
    if answer:
        return answer
    parsed_output = result.get("parsed_output")
    if isinstance(parsed_output, dict):
        preview = _first_list_item_preview(parsed_output.get("matches", []))
        if preview:
            return preview
        preview = _short_preview(json.dumps(parsed_output, sort_keys=True), limit=72)
        if preview:
            return preview
    stdout = _short_preview(str(result.get("stdout", "")), limit=72)
    if stdout:
        return stdout
    return _first_list_item_preview(result.get("matches", []))


def _skill_compose_input_preview(arguments: dict[str, Any]) -> str:
    steps = arguments.get("steps", [])
    if not isinstance(steps, list):
        return ""
    titles = [
        _short_skill_title(str(item.get("skill_title", "")))
        for item in steps
        if isinstance(item, dict) and _short_skill_title(str(item.get("skill_title", "")))
    ]
    if not titles:
        return ""
    return " -> ".join(titles[:3]) + (" -> ..." if len(titles) > 3 else "")


def _skill_compose_output_preview(result: dict[str, Any]) -> str:
    final_output = result.get("final_output")
    if isinstance(final_output, dict):
        preview = _short_preview(json.dumps(final_output, sort_keys=True), limit=72)
        if preview:
            return preview
    answer = _short_preview(str(result.get("answer", "")), limit=72)
    if answer:
        return answer
    blocked = _short_skill_title(str(result.get("blocked_skill_title", "")))
    return blocked or ""


def _skill_error_preview(result: dict[str, Any]) -> str:
    for key in ("stderr", "error", "answer"):
        preview = _short_preview(str(result.get(key, "")), limit=72)
        if preview:
            return preview
    return ""


def _search_output_preview(result: dict[str, Any]) -> str:
    return _first_list_item_preview(result.get("matches", []))


def _process_output_preview(result: dict[str, Any]) -> str:
    stdout = _short_preview(str(result.get("stdout", "")), limit=72)
    if stdout:
        return stdout
    return _short_preview(str(result.get("stderr", "")), limit=72)


def _net_http_output_preview(result: dict[str, Any], *, fallback: str) -> str:
    http_status = collapse_ws(str(result.get("http_status", "")))
    text_preview = _short_preview(str(result.get("text", "")), limit=72)
    if http_status and text_preview:
        return f"{http_status} {text_preview}"
    if http_status:
        return http_status
    return text_preview or fallback


def _imported_skills_preview(result: dict[str, Any]) -> str:
    imported = result.get("imported", [])
    if not isinstance(imported, list):
        return ""
    for item in imported:
        if isinstance(item, dict):
            title = _short_skill_title(str(item.get("title", "")))
            if title:
                return title
    return ""


def _content_preview(text: str) -> str:
    for line in str(text or "").splitlines():
        preview = _short_preview(line, limit=72)
        if preview:
            return preview
    return ""


def _first_list_item_preview(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    for item in values:
        if isinstance(item, dict):
            for key in ("path", "file", "match", "text", "line"):
                preview = _short_preview(str(item.get(key, "")), limit=72)
                if preview:
                    return preview
            preview = _short_preview(json.dumps(item, sort_keys=True), limit=72)
            if preview:
                return preview
        else:
            preview = _short_preview(str(item), limit=72)
            if preview:
                return preview
    return ""


def _value_preview(value: Any) -> str:
    if isinstance(value, (str, int, float, bool)):
        return _short_preview(str(value), limit=36)
    if isinstance(value, list):
        parts = [_short_preview(str(item), limit=16) for item in value[:2] if _short_preview(str(item), limit=16)]
        return "[" + ", ".join(parts) + (", ..." if len(value) > 2 else "") + "]" if parts else ""
    if isinstance(value, dict):
        parts: list[str] = []
        for key, child in list(value.items())[:2]:
            child_preview = _value_preview(child)
            if child_preview:
                parts.append(f"{key}={child_preview}")
        return "{" + ", ".join(parts) + (" ..." if len(value) > 2 else "") + "}" if parts else ""
    return ""


def _short_preview(text: str, *, limit: int) -> str:
    normalized = collapse_ws(str(text))
    if not normalized:
        return ""
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)].rstrip() + "…"
