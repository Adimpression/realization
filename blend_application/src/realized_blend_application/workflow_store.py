# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from realized_core_semantics.applied_primitives import json_safe
from realized_blend.workflows import BlendWorkflowPlan, BlendWorkflowRun
from realized_core_semantics.semantic_text import collapse_ws


def _ensure_blend_workflow_store(root_path: Path) -> dict[str, Path]:
    root = Path(root_path).expanduser().resolve()
    workflows_root = root / "workflows"
    plans_path = workflows_root / "plans"
    runs_path = workflows_root / "runs"
    index_path = root / "BLEND_WORKFLOWS.json"
    plans_path.mkdir(parents=True, exist_ok=True)
    runs_path.mkdir(parents=True, exist_ok=True)
    if not index_path.exists():
        _write_json(
            index_path,
            {
                "latest_plan_id": "",
                "latest_run_id": "",
                "plans": [],
                "runs": [],
            },
        )
    return {
        "root": workflows_root,
        "plans": plans_path,
        "runs": runs_path,
        "index": index_path,
    }


def _load_blend_workflow_plan(root_path: Path, workflow_id: str) -> BlendWorkflowPlan:
    paths = _ensure_blend_workflow_store(root_path)
    payload = json.loads((paths["plans"] / f"{workflow_id}.json").read_text())
    return BlendWorkflowPlan.from_dict(payload)


def _load_blend_workflow_run(root_path: Path, workflow_run_id: str) -> BlendWorkflowRun:
    paths = _ensure_blend_workflow_store(root_path)
    payload = json.loads((paths["runs"] / f"{workflow_run_id}.json").read_text())
    return BlendWorkflowRun.from_dict(payload)


def _load_blend_workflow_index(root_path: Path) -> dict[str, Any]:
    paths = _ensure_blend_workflow_store(root_path)
    return json.loads(paths["index"].read_text())


def _list_blend_workflow_summaries(
    root_path: Path,
    *,
    kind: str = "runs",
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    index_payload = _load_blend_workflow_index(root_path)
    collection_name = "plans" if collapse_ws(kind).casefold() == "plans" else "runs"
    items = [dict(item) for item in index_payload.get(collection_name, []) if isinstance(item, dict)]
    normalized_status = collapse_ws(status).casefold()
    if normalized_status and collection_name == "runs":
        items = [
            item for item in items
            if collapse_ws(str(item.get("status", ""))).casefold() == normalized_status
        ]
    items.sort(
        key=lambda item: (
            collapse_ws(str(item.get("finished_at", "")))
            or collapse_ws(str(item.get("created_at", "")))
            or collapse_ws(str(item.get("started_at", "")))
        ),
        reverse=True,
    )
    bounded_limit = max(1, min(int(limit or 20), 200))
    return items[:bounded_limit]


def _list_blend_workflow_runs_for_plan(
    root_path: Path,
    workflow_id: str,
    *,
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    normalized_workflow_id = collapse_ws(workflow_id)
    if not normalized_workflow_id:
        return []
    related_runs = [
        dict(item)
        for item in _load_blend_workflow_index(root_path).get("runs", [])
        if isinstance(item, dict) and collapse_ws(str(item.get("workflow_id", ""))) == normalized_workflow_id
    ]
    normalized_status = collapse_ws(status).casefold()
    if normalized_status:
        related_runs = [
            item
            for item in related_runs
            if collapse_ws(str(item.get("status", ""))).casefold() == normalized_status
        ]
    related_runs.sort(
        key=lambda item: (
            collapse_ws(str(item.get("finished_at", "")))
            or collapse_ws(str(item.get("started_at", "")))
            or collapse_ws(str(item.get("created_at", "")))
        ),
        reverse=True,
    )
    bounded_limit = max(1, min(int(limit or 20), 200))
    return related_runs[:bounded_limit]


def _persist_blend_workflow_objects(
    *,
    root_path: Path,
    plan: BlendWorkflowPlan,
    run: BlendWorkflowRun,
    session_id: str = "",
) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
    paths = _ensure_blend_workflow_store(root_path)
    now = datetime.now(timezone.utc).isoformat()
    effective_session_id = collapse_ws(session_id) or plan.session_id or run.session_id
    effective_plan = replace(
        plan,
        workflow_id=plan.workflow_id or f"bwf_plan_{uuid.uuid4().hex[:12]}",
        session_id=plan.session_id or effective_session_id,
        created_at=plan.created_at or now,
        metadata={
            **dict(plan.metadata),
            "persisted": True,
        },
    )
    effective_run = replace(
        run,
        workflow_run_id=run.workflow_run_id or f"bwf_run_{uuid.uuid4().hex[:12]}",
        workflow_id=run.workflow_id or effective_plan.workflow_id,
        plan=effective_plan,
        session_id=run.session_id or effective_plan.session_id or effective_session_id,
        started_at=run.started_at or now,
        finished_at=run.finished_at or now,
        metadata={
            **dict(run.metadata),
            "persisted": True,
        },
    )
    plan_payload = json_safe(effective_plan.to_dict())
    run_payload = json_safe(effective_run.to_dict())
    plan_path = paths["plans"] / f"{effective_plan.workflow_id}.json"
    run_path = paths["runs"] / f"{effective_run.workflow_run_id}.json"
    _write_json(plan_path, plan_payload)
    _write_json(run_path, run_payload)
    index_payload = json.loads(paths["index"].read_text()) if paths["index"].exists() else {"plans": [], "runs": []}
    plan_summary = {
        "workflow_id": effective_plan.workflow_id,
        "session_id": effective_plan.session_id,
        "created_at": effective_plan.created_at,
        "workflow_kind": effective_plan.workflow_kind,
        "step_count": len(effective_plan.steps),
        "final_output_step": effective_plan.final_output_step,
        "path": str(plan_path),
    }
    run_summary = {
        "workflow_run_id": effective_run.workflow_run_id,
        "workflow_id": effective_run.workflow_id,
        "session_id": effective_run.session_id,
        "status": effective_run.status,
        "started_at": effective_run.started_at,
        "finished_at": effective_run.finished_at,
        "final_output_step": effective_run.final_output_step,
        "path": str(run_path),
    }
    index_payload["plans"] = _updated_summary_items(
        list(index_payload.get("plans", [])),
        identifier_key="workflow_id",
        item=plan_summary,
    )
    index_payload["runs"] = _updated_summary_items(
        list(index_payload.get("runs", [])),
        identifier_key="workflow_run_id",
        item=run_summary,
    )
    index_payload["latest_plan_id"] = effective_plan.workflow_id
    index_payload["latest_run_id"] = effective_run.workflow_run_id
    _write_json(paths["index"], index_payload)
    return effective_plan, effective_run, {
        "workflow_id": effective_plan.workflow_id,
        "workflow_run_id": effective_run.workflow_run_id,
        "plan_path": str(plan_path),
        "run_path": str(run_path),
        "index_path": str(paths["index"]),
    }


class JsonBlendWorkflowRepository:
    """JSON adapter for the authoritative Blend workflow repository port."""

    def __init__(self, root_path: Path) -> None:
        self.root_path = Path(root_path)

    def ensure(self) -> dict[str, Path]:
        return _ensure_blend_workflow_store(self.root_path)

    def load_plan(self, workflow_id: str) -> BlendWorkflowPlan:
        return _load_blend_workflow_plan(self.root_path, workflow_id)

    def load_run(self, workflow_run_id: str) -> BlendWorkflowRun:
        return _load_blend_workflow_run(self.root_path, workflow_run_id)

    def load_index(self) -> dict[str, Any]:
        return _load_blend_workflow_index(self.root_path)

    def list_summaries(
        self,
        *,
        kind: str = "runs",
        status: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return _list_blend_workflow_summaries(
            self.root_path,
            kind=kind,
            status=status,
            limit=limit,
        )

    def list_runs_for_plan(
        self,
        workflow_id: str,
        *,
        status: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return _list_blend_workflow_runs_for_plan(
            self.root_path,
            workflow_id,
            status=status,
            limit=limit,
        )

    def persist(
        self,
        *,
        plan: BlendWorkflowPlan,
        run: BlendWorkflowRun,
        session_id: str = "",
    ) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
        return _persist_blend_workflow_objects(
            root_path=self.root_path,
            plan=plan,
            run=run,
            session_id=session_id,
        )


def ensure_blend_workflow_store(root_path: Path) -> dict[str, Path]:
    return JsonBlendWorkflowRepository(root_path).ensure()


def load_blend_workflow_plan(root_path: Path, workflow_id: str) -> BlendWorkflowPlan:
    return JsonBlendWorkflowRepository(root_path).load_plan(workflow_id)


def load_blend_workflow_run(root_path: Path, workflow_run_id: str) -> BlendWorkflowRun:
    return JsonBlendWorkflowRepository(root_path).load_run(workflow_run_id)


def load_blend_workflow_index(root_path: Path) -> dict[str, Any]:
    return JsonBlendWorkflowRepository(root_path).load_index()


def list_blend_workflow_summaries(
    root_path: Path,
    *,
    kind: str = "runs",
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return JsonBlendWorkflowRepository(root_path).list_summaries(
        kind=kind,
        status=status,
        limit=limit,
    )


def list_blend_workflow_runs_for_plan(
    root_path: Path,
    workflow_id: str,
    *,
    status: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    return JsonBlendWorkflowRepository(root_path).list_runs_for_plan(
        workflow_id,
        status=status,
        limit=limit,
    )


def persist_blend_workflow_objects(
    *,
    root_path: Path,
    plan: BlendWorkflowPlan,
    run: BlendWorkflowRun,
    session_id: str = "",
) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
    return JsonBlendWorkflowRepository(root_path).persist(
        plan=plan,
        run=run,
        session_id=session_id,
    )


def _updated_summary_items(
    items: list[dict[str, Any]],
    *,
    identifier_key: str,
    item: dict[str, Any],
) -> list[dict[str, Any]]:
    identifier = collapse_ws(str(item.get(identifier_key, "")))
    updated: list[dict[str, Any]] = []
    replaced = False
    for existing in items:
        if not isinstance(existing, dict):
            continue
        if collapse_ws(str(existing.get(identifier_key, ""))) == identifier:
            updated.append(dict(item))
            replaced = True
        else:
            updated.append(dict(existing))
    if not replaced:
        updated.append(dict(item))
    return updated


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
