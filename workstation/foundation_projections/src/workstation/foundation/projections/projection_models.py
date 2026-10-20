# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any

from blend_workflow import BlendWorkflowPlan, BlendWorkflowRun
from semantic_text import collapse_ws
from workstation.contracts.shell import WorkstationChatMessageView
from workstation.foundation.models import WorkstationSession


_ACTIVITY_RENDERED_PREFIX_PATTERN = re.compile(r"^((?:│  )*├─ )")
_ACTIVITY_RENDERED_SECTION_PATTERN = re.compile(r"\[[^\[\]]+\]")
_ACTIVITY_RENDERED_TIMING_PATTERN = re.compile(r"^(.*?)(\s*\([^()]+\))$")


@dataclass(frozen=True)
class WorkstationPermissionEntryView:
    capability: str
    granted: bool
    protected: bool
    revocable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "granted": self.granted,
            "protected": self.protected,
            "revocable": self.revocable,
        }


@dataclass(frozen=True)
class WorkstationPermissionPanelView:
    granted_capabilities: tuple[str, ...]
    available_capabilities: tuple[str, ...]
    ungranted_capabilities: tuple[str, ...]
    protected_capabilities: tuple[str, ...]
    revocable_capabilities: tuple[str, ...]
    entries: tuple[WorkstationPermissionEntryView, ...]
    usage: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "granted_capabilities": list(self.granted_capabilities),
            "available_capabilities": list(self.available_capabilities),
            "ungranted_capabilities": list(self.ungranted_capabilities),
            "protected_capabilities": list(self.protected_capabilities),
            "revocable_capabilities": list(self.revocable_capabilities),
            "entries": [item.to_dict() for item in self.entries],
            "usage": list(self.usage),
        }


@dataclass(frozen=True)
class WorkstationWorkflowNodeView:
    node_id: str
    label: str
    node_kind: str
    operator_kind: str = ""
    operator_name: str = ""
    status: str = ""
    semantic_unit: str = ""
    branch_label: str = ""
    is_final_output: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_kind": self.node_kind,
            "operator_kind": self.operator_kind,
            "operator_name": self.operator_name,
            "status": self.status,
            "semantic_unit": self.semantic_unit,
            "branch_label": self.branch_label,
            "is_final_output": self.is_final_output,
        }


@dataclass(frozen=True)
class WorkstationWorkflowEdgeView:
    edge_id: str
    source_node_id: str
    target_node_id: str
    source_path: str = ""
    target_path: str = ""
    mapper_kind: str = ""
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "mapper_kind": self.mapper_kind,
            "label": self.label,
        }


@dataclass(frozen=True)
class WorkstationWorkflowGraphView:
    workflow_id: str
    workflow_run_id: str
    workflow_kind: str
    status: str
    final_output_step: str
    nodes: tuple[WorkstationWorkflowNodeView, ...]
    edges: tuple[WorkstationWorkflowEdgeView, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "workflow_kind": self.workflow_kind,
            "status": self.status,
            "final_output_step": self.final_output_step,
            "nodes": [item.to_dict() for item in self.nodes],
            "edges": [item.to_dict() for item in self.edges],
        }


@dataclass(frozen=True)
class WorkstationSkillFieldView:
    field_name: str
    label: str
    io_direction: str
    description: str = ""
    data_type: str = ""
    required: bool = True
    widget_hint: str = ""
    default_value: Any = None
    options: tuple[str, ...] = ()
    constraints: dict[str, Any] = field(default_factory=dict)
    section: str = ""
    placeholder: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "label": self.label,
            "io_direction": self.io_direction,
            "description": self.description,
            "data_type": self.data_type,
            "required": self.required,
            "widget_hint": self.widget_hint,
            "default_value": self.default_value,
            "options": list(self.options),
            "constraints": dict(self.constraints),
            "section": self.section,
            "placeholder": self.placeholder,
        }


@dataclass(frozen=True)
class WorkstationSkillFormSectionView:
    section_id: str
    title: str
    field_names: tuple[str, ...]
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "field_names": list(self.field_names),
            "description": self.description,
        }


@dataclass(frozen=True)
class WorkstationSkillInputFormView:
    skill_title: str
    executor_framework: str
    fields: tuple[WorkstationSkillFieldView, ...]
    sections: tuple[WorkstationSkillFormSectionView, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_title": self.skill_title,
            "executor_framework": self.executor_framework,
            "fields": [item.to_dict() for item in self.fields],
            "sections": [item.to_dict() for item in self.sections],
        }


@dataclass(frozen=True)
class WorkstationSkillDescriptorView:
    skill_title: str
    kind: str
    source_kind: str
    executor_framework: str
    risk_tier: str
    authorities_requested: tuple[str, ...]
    aliases: tuple[str, ...]
    family: dict[str, str]
    inputs: tuple[WorkstationSkillFieldView, ...]
    outputs: tuple[WorkstationSkillFieldView, ...]
    input_form: WorkstationSkillInputFormView

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_title": self.skill_title,
            "kind": self.kind,
            "source_kind": self.source_kind,
            "executor_framework": self.executor_framework,
            "risk_tier": self.risk_tier,
            "authorities_requested": list(self.authorities_requested),
            "aliases": list(self.aliases),
            "family": dict(self.family),
            "inputs": [item.to_dict() for item in self.inputs],
            "outputs": [item.to_dict() for item in self.outputs],
            "input_form": self.input_form.to_dict(),
        }


@dataclass(frozen=True)
class WorkstationSkillCatalogEntryView:
    skill_title: str
    kind: str
    source_kind: str
    executor_framework: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_title": self.skill_title,
            "kind": self.kind,
            "source_kind": self.source_kind,
            "executor_framework": self.executor_framework,
        }


@dataclass(frozen=True)
class WorkstationSkillCatalogView:
    query: str
    builtin: tuple[WorkstationSkillCatalogEntryView, ...]
    imported: tuple[WorkstationSkillCatalogEntryView, ...]
    total_visible: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "builtin": [item.to_dict() for item in self.builtin],
            "imported": [item.to_dict() for item in self.imported],
            "total_visible": self.total_visible,
        }


@dataclass(frozen=True)
class WorkstationActivityEventView:
    event_kind: str
    message: str
    capability: str = ""
    status: str = ""
    prompt_elapsed_seconds: float | None = None
    elapsed_seconds: float | None = None
    workflow_execution_id: str = ""
    workflow_id: str = ""
    workflow_run_id: str = ""
    step_id: str = ""
    branch_label: str = ""
    iteration: int = 0
    tree_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_kind": self.event_kind,
            "message": self.message,
            "rendered_message": render_workstation_activity_event(self),
            "capability": self.capability,
            "status": self.status,
            "prompt_elapsed_seconds": self.prompt_elapsed_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "workflow_execution_id": self.workflow_execution_id,
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "step_id": self.step_id,
            "branch_label": self.branch_label,
            "iteration": self.iteration,
            "tree_depth": self.tree_depth,
        }


@dataclass(frozen=True)
class WorkstationActivityFeedView:
    events: tuple[WorkstationActivityEventView, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [item.to_dict() for item in self.events],
        }


@dataclass(frozen=True)
class WorkstationChatTranscriptView:
    messages: tuple[WorkstationChatMessageView, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "messages": [item.to_dict() for item in self.messages],
        }


@dataclass(frozen=True)
class WorkstationWorkflowSummaryEntryView:
    workflow_id: str
    workflow_run_id: str = ""
    workflow_kind: str = ""
    status: str = ""
    session_id: str = ""
    step_count: int = 0
    final_output_step: str = ""
    created_at: str = ""
    started_at: str = ""
    finished_at: str = ""
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "workflow_kind": self.workflow_kind,
            "status": self.status,
            "session_id": self.session_id,
            "step_count": self.step_count,
            "final_output_step": self.final_output_step,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "path": self.path,
        }


@dataclass(frozen=True)
class WorkstationWorkflowSummaryListView:
    kind: str
    items: tuple[WorkstationWorkflowSummaryEntryView, ...]
    returned_count: int
    total_count: int
    latest_plan_id: str = ""
    latest_run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "items": [item.to_dict() for item in self.items],
            "returned_count": self.returned_count,
            "total_count": self.total_count,
            "latest_plan_id": self.latest_plan_id,
            "latest_run_id": self.latest_run_id,
        }


@dataclass(frozen=True)
class WorkstationWorkflowTimelineEntryView:
    sequence_index: int
    step_id: str
    title: str
    status: str = ""
    operator_kind: str = ""
    operator_name: str = ""
    branch_label: str = ""
    target: str = ""
    applicability: str = ""
    output_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence_index": self.sequence_index,
            "step_id": self.step_id,
            "title": self.title,
            "status": self.status,
            "operator_kind": self.operator_kind,
            "operator_name": self.operator_name,
            "branch_label": self.branch_label,
            "target": self.target,
            "applicability": self.applicability,
            "output_preview": self.output_preview,
        }


@dataclass(frozen=True)
class WorkstationWorkflowTimelineView:
    workflow_id: str
    workflow_run_id: str
    status: str
    started_at: str = ""
    finished_at: str = ""
    final_output_step: str = ""
    entries: tuple[WorkstationWorkflowTimelineEntryView, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "final_output_step": self.final_output_step,
            "entries": [item.to_dict() for item in self.entries],
        }


@dataclass(frozen=True)
class WorkstationOperatorSummaryEntryView:
    operator_id: str
    operator_name: str
    operator_kind: str
    source_kind: str = ""
    execution_adapter: str = ""
    semantic_description: str = ""
    provider_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "operator_kind": self.operator_kind,
            "source_kind": self.source_kind,
            "execution_adapter": self.execution_adapter,
            "semantic_description": self.semantic_description,
            "provider_id": self.provider_id,
        }


@dataclass(frozen=True)
class WorkstationOperatorSummaryListView:
    operator_kind: str
    query: str
    items: tuple[WorkstationOperatorSummaryEntryView, ...]
    returned_count: int
    provider_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator_kind": self.operator_kind,
            "query": self.query,
            "items": [item.to_dict() for item in self.items],
            "returned_count": self.returned_count,
            "provider_ids": list(self.provider_ids),
        }


@dataclass(frozen=True)
class WorkstationOperatorDetailView:
    operator: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "operator": dict(self.operator),
        }


@dataclass(frozen=True)
class WorkstationActionResultView:
    action_kind: str
    status: str
    title: str
    message: str = ""
    details: tuple[str, ...] = ()
    payload_preview: str = ""
    workflow_id: str = ""
    workflow_run_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_kind": self.action_kind,
            "status": self.status,
            "title": self.title,
            "message": self.message,
            "details": list(self.details),
            "payload_preview": self.payload_preview,
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
            "payload": dict(self.payload),
        }


def workstation_permission_panel_view(
    *,
    session: WorkstationSession,
    available_capabilities: list[str] | tuple[str, ...],
    protected_capabilities: list[str] | tuple[str, ...],
) -> WorkstationPermissionPanelView:
    granted_capabilities = tuple(str(item) for item in session.allowed_capabilities if collapse_ws(str(item)))
    available_ordered = tuple(
        str(item) for item in available_capabilities if collapse_ws(str(item))
    )
    protected_set = {
        str(item) for item in protected_capabilities if collapse_ws(str(item))
    }
    available_set = {item for item in available_ordered}
    ungranted_capabilities = tuple(
        item for item in available_ordered if item not in granted_capabilities
    )
    revocable_capabilities = tuple(
        item for item in granted_capabilities if item not in protected_set
    )
    entries = tuple(
        WorkstationPermissionEntryView(
            capability=item,
            granted=item in granted_capabilities,
            protected=item in protected_set,
            revocable=item in revocable_capabilities,
        )
        for item in available_ordered
    )
    return WorkstationPermissionPanelView(
        granted_capabilities=tuple(item for item in granted_capabilities if item in available_set or item),
        available_capabilities=available_ordered,
        ungranted_capabilities=ungranted_capabilities,
        protected_capabilities=tuple(item for item in protected_capabilities if collapse_ws(str(item))),
        revocable_capabilities=revocable_capabilities,
        entries=entries,
        usage=(
            "/grant-permission <capability>",
            "/revoke-permission <capability>",
            "/permissions <skill title>",
        ),
    )


def render_workstation_permission_panel(view: WorkstationPermissionPanelView) -> str:
    lines = [
        "Granted session capabilities:",
        *([f"- {item}" for item in view.granted_capabilities] or ["- <none>"]),
        "",
        "Available capabilities:",
        *([f"- {item}" for item in view.available_capabilities] or ["- <none>"]),
        "",
        "Not yet granted:",
        *([f"- {item}" for item in view.ungranted_capabilities] or ["- <none>"]),
        "",
        "Protected shell capabilities:",
        *([f"- {item}" for item in view.protected_capabilities] or ["- <none>"]),
        "",
        "Revocable now:",
        *([f"- {item}" for item in view.revocable_capabilities] or ["- <none>"]),
        "",
        "Usage:",
        *list(view.usage),
    ]
    return "\n".join(lines)


def render_workstation_skill_descriptor(view: WorkstationSkillDescriptorView) -> str:
    lines = [
        f"Title: {view.skill_title}",
        f"Kind: {view.kind}",
        f"Source: {view.source_kind or '<unknown>'}",
        f"Executor: {view.executor_framework or '<unknown>'}",
        f"Risk tier: {view.risk_tier or '<unspecified>'}",
        "Authorities requested: "
        + (", ".join(view.authorities_requested) if view.authorities_requested else "<none>"),
        "Inputs:",
        *_render_skill_field_lines(view.inputs),
        "Outputs:",
        *_render_skill_field_lines(view.outputs),
    ]
    if view.aliases:
        lines.extend(
            [
                "Aliases:",
                *[f"- {item}" for item in view.aliases],
            ]
        )
    if view.family:
        lines.append(
            "Family: "
            + ", ".join(
                f"{key}={value}"
                for key, value in view.family.items()
                if collapse_ws(str(value))
            )
        )
    lines.extend(
        [
            "Input form:",
            *_render_skill_field_lines(view.input_form.fields),
        ]
    )
    return "\n".join(lines)


def render_workstation_skill_catalog(view: WorkstationSkillCatalogView) -> str:
    lines: list[str] = []
    if view.query:
        lines.append(f"Skills matching: {view.query}")
        lines.append("")
    lines.extend(_render_skill_catalog_group_lines("Built-in skills", view.builtin))
    lines.append("")
    lines.extend(_render_skill_catalog_group_lines("Imported skills", view.imported))
    lines.append("")
    lines.append(f"Total visible: {view.total_visible}")
    return "\n".join(line for line in lines if line is not None).strip()


def render_workstation_activity_event(view: WorkstationActivityEventView) -> str:
    return _with_timing(
        _activity_tree_message(view),
        prompt_elapsed_seconds=view.prompt_elapsed_seconds,
        elapsed_seconds=view.elapsed_seconds,
    )


def render_workstation_activity_feed(view: WorkstationActivityFeedView) -> str:
    if not view.events:
        return "No activity yet."
    return "\n".join(render_workstation_activity_event(item) for item in view.events)


def split_rendered_workstation_activity_line(text: str) -> tuple[str, str, tuple[str, ...], str]:
    rendered = str(text or "")
    if not rendered:
        return "", "", (), ""
    timing_text = ""
    timing_match = _ACTIVITY_RENDERED_TIMING_PATTERN.match(rendered)
    if timing_match is not None:
        rendered = timing_match.group(1)
        timing_text = timing_match.group(2).strip()
    tree_prefix = ""
    prefix_match = _ACTIVITY_RENDERED_PREFIX_PATTERN.match(rendered)
    if prefix_match is not None:
        tree_prefix = prefix_match.group(1)
        rendered = rendered[prefix_match.end() :]
    sections: list[str] = []
    main_parts: list[str] = []
    cursor = 0
    for match in _ACTIVITY_RENDERED_SECTION_PATTERN.finditer(rendered):
        if match.start() > cursor:
            main_parts.append(rendered[cursor:match.start()])
        sections.append(match.group(0))
        cursor = match.end()
    if cursor < len(rendered):
        main_parts.append(rendered[cursor:])
    main_text = " ".join(part.strip() for part in main_parts if part.strip())
    return tree_prefix, main_text, tuple(sections), timing_text


def annotate_workstation_activity_events(
    events: tuple[WorkstationActivityEventView, ...] | list[WorkstationActivityEventView],
) -> tuple[WorkstationActivityEventView, ...]:
    active_workflow_stack: list[str] = []
    annotated: list[WorkstationActivityEventView] = []
    for item in events:
        depth = 0
        execution_id = collapse_ws(item.workflow_execution_id)
        kind = collapse_ws(item.event_kind)
        if execution_id and kind == "blend_workflow_started":
            depth = len(active_workflow_stack)
            active_workflow_stack.append(execution_id)
        elif execution_id and kind.startswith("blend_step_"):
            if execution_id in active_workflow_stack:
                depth = active_workflow_stack.index(execution_id) + 1
            else:
                depth = max(len(active_workflow_stack), 0) + 1
        elif execution_id and kind in {"blend_workflow_completed", "blend_workflow_failed", "blend_workflow_persisted"}:
            depth = active_workflow_stack.index(execution_id) if execution_id in active_workflow_stack else 0
            if kind in {"blend_workflow_completed", "blend_workflow_failed"} and execution_id in active_workflow_stack:
                active_workflow_stack.remove(execution_id)
        annotated.append(replace(item, tree_depth=depth))
    return tuple(annotated)


def _render_skill_field_lines(fields: tuple[WorkstationSkillFieldView, ...]) -> list[str]:
    if not fields:
        return ["- <none>"]
    rendered: list[str] = []
    for field in fields:
        suffix_parts = []
        if field.data_type:
            suffix_parts.append(field.data_type)
        suffix_parts.append("required" if field.required else "optional")
        if field.widget_hint:
            suffix_parts.append(f"widget={field.widget_hint}")
        if field.description:
            rendered.append(
                f"- {field.field_name}: {field.description} ({', '.join(suffix_parts)})"
            )
        else:
            rendered.append(f"- {field.field_name} ({', '.join(suffix_parts)})")
    return rendered


def _render_skill_catalog_group_lines(
    title: str,
    entries: tuple[WorkstationSkillCatalogEntryView, ...],
) -> list[str]:
    lines = [title]
    if not entries:
        lines.append("- <none>")
        return lines
    for item in entries:
        executor_suffix = f" [{item.executor_framework}]" if item.executor_framework else ""
        lines.append(f"- {item.skill_title}{executor_suffix}")
    return lines


def _with_timing(
    text: str,
    *,
    prompt_elapsed_seconds: float | None = None,
    elapsed_seconds: float | None = None,
) -> str:
    parts: list[str] = []
    if prompt_elapsed_seconds is not None:
        parts.append(f"t+{_elapsed_preview(prompt_elapsed_seconds).lstrip('~')}")
    if elapsed_seconds is not None:
        parts.append(f"op {_elapsed_preview(elapsed_seconds)}")
    if not parts:
        return text
    return f"{text} ({', '.join(parts)})"


def _activity_tree_message(view: WorkstationActivityEventView) -> str:
    prefix = _activity_tree_prefix(view.tree_depth)
    suffix_parts: list[str] = []
    branch_label = collapse_ws(view.branch_label)
    if branch_label:
        suffix_parts.append(branch_label)
    if int(view.iteration or 0) > 0:
        suffix_parts.append(f"iter {int(view.iteration) + 1}")
    if not suffix_parts:
        return f"{prefix}{view.message}" if prefix else view.message
    return f"{prefix}{view.message} [{' | '.join(suffix_parts)}]" if prefix else f"{view.message} [{' | '.join(suffix_parts)}]"


def _activity_tree_prefix(depth: int) -> str:
    normalized_depth = max(int(depth or 0), 0)
    if normalized_depth <= 0:
        return ""
    if normalized_depth == 1:
        return "├─ "
    return ("│  " * (normalized_depth - 1)) + "├─ "


def _elapsed_preview(elapsed_seconds: float) -> str:
    seconds = max(0.0, float(elapsed_seconds))
    if seconds < 0.1:
        return "~0.0s"
    if seconds < 10.0:
        return f"~{seconds:.1f}s"
    return f"~{seconds:.0f}s"


def workstation_workflow_graph_view(
    *,
    workflow_plan: BlendWorkflowPlan,
    workflow_run: BlendWorkflowRun | None = None,
) -> WorkstationWorkflowGraphView:
    run_step_status: dict[str, str] = {}
    if workflow_run is not None:
        for item in workflow_run.steps:
            if not isinstance(item, dict):
                continue
            step_id = collapse_ws(str(item.get("step_id", "")))
            if step_id:
                run_step_status[step_id] = collapse_ws(str(item.get("status", "")))
    final_output_step = (
        collapse_ws(workflow_run.final_output_step) if workflow_run is not None else ""
    ) or collapse_ws(workflow_plan.final_output_step)
    nodes: list[WorkstationWorkflowNodeView] = []
    edges: list[WorkstationWorkflowEdgeView] = []
    needs_root_node = bool(workflow_plan.root_inputs or workflow_plan.root_references)
    for step in workflow_plan.steps:
        for binding in step.bindings:
            payload = binding.to_dict()
            if not collapse_ws(str(payload.get("source_step_id", ""))):
                needs_root_node = True
    if needs_root_node:
        nodes.append(
            WorkstationWorkflowNodeView(
                node_id="__root__",
                label="Root Context",
                node_kind="root",
                status="available",
            )
        )
    seen_edges: set[tuple[str, str, str, str, str]] = set()
    for step in workflow_plan.steps:
        nodes.append(
            WorkstationWorkflowNodeView(
                node_id=step.step_id,
                label=step.operator_name or step.step_id,
                node_kind="step",
                operator_kind=step.operator_kind,
                operator_name=step.operator_name,
                status=run_step_status.get(step.step_id, ""),
                semantic_unit=step.semantic_unit,
                branch_label=step.branch_label,
                is_final_output=step.step_id == final_output_step,
            )
        )
        for index, binding in enumerate(step.bindings):
            payload = binding.to_dict()
            source_node_id = collapse_ws(str(payload.get("source_step_id", ""))) or "__root__"
            source_path = collapse_ws(str(payload.get("source_path", "")))
            target_path = collapse_ws(str(payload.get("target_path", "")))
            mapper_payload = payload.get("mapper", {})
            mapper_kind = ""
            if isinstance(mapper_payload, dict):
                mapper_kind = collapse_ws(str(mapper_payload.get("kind", "")))
            if not mapper_kind:
                mapper_kind = collapse_ws(str(payload.get("mapper_kind", "")))
            edge_signature = (
                source_node_id,
                step.step_id,
                source_path,
                target_path,
                mapper_kind,
            )
            if edge_signature in seen_edges:
                continue
            seen_edges.add(edge_signature)
            label_parts = [part for part in (source_path, target_path) if part]
            if mapper_kind:
                label_parts.append(f"mapper={mapper_kind}")
            edges.append(
                WorkstationWorkflowEdgeView(
                    edge_id=f"{step.step_id}_edge_{index}",
                    source_node_id=source_node_id,
                    target_node_id=step.step_id,
                    source_path=source_path,
                    target_path=target_path,
                    mapper_kind=mapper_kind,
                    label=" -> ".join(label_parts),
                )
            )
    return WorkstationWorkflowGraphView(
        workflow_id=collapse_ws(workflow_plan.workflow_id),
        workflow_run_id=collapse_ws(workflow_run.workflow_run_id) if workflow_run is not None else "",
        workflow_kind=collapse_ws(workflow_plan.workflow_kind),
        status=collapse_ws(workflow_run.status) if workflow_run is not None else "",
        final_output_step=final_output_step,
        nodes=tuple(nodes),
        edges=tuple(edges),
    )
