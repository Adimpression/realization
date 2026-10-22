"""Conversation-host shell above the governed core engine."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, TextIO
import uuid

from realized_core_engine import (
    ContinuationInlet,
    EngineConfiguration,
    GoverningDirection,
    InletRelationship,
    InspectionRequest,
    InspectionTargetKind,
    InspectionView,
    OperationKind,
    ResumptionEngine,
    ResumptionIdentity,
    ResumptionRequest,
    ResumptionResult,
    SemanticDelta,
    SemanticItem,
    SemanticOutcome,
    StartRequest,
    Supersession,
    open_resumption_engine,
)


_TREATMENTS = {"independent", "human_contribution", "follow_up", "correction"}


@dataclass
class CoreConversationHost:
    """Own transcript and explicit turn/revision routing above the engine."""

    root: Path
    configuration: EngineConfiguration
    engine: ResumptionEngine | None = None

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("MESSAGES.jsonl", "RUN_BINDINGS.jsonl"):
            path = self.root / name
            if not path.exists():
                path.write_text("", encoding="utf-8")
        session_path = self.root / "SESSION.json"
        if not session_path.exists():
            _write_json(
                session_path,
                {
                    "session_id": f"session_{uuid.uuid4().hex}",
                    "scope_id": f"conversation_{uuid.uuid4().hex}",
                },
            )
        if self.engine is None:
            self.engine = open_resumption_engine(
                configuration=replace(
                    self.configuration,
                    sqlite_path=self.sqlite_path,
                    state_output_path=None,
                    inlets=(),
                )
            )

    @property
    def sqlite_path(self) -> Path:
        selected = self.configuration.sqlite_path or (self.root / "artifacts.sqlite3")
        return Path(selected).expanduser().resolve()

    @property
    def scope_id(self) -> str:
        return str(_read_json(self.root / "SESSION.json")["scope_id"])

    def submit(
        self,
        prompt: str,
        *,
        treatment: str = "independent",
        parent_run_id: str = "",
        target_hold_id: str = "",
        selected_item_ids: tuple[str, ...] = (),
        correction_target_item_id: str = "",
        inlet_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_prompt = str(prompt or "").strip()
        normalized_treatment = str(treatment or "independent").strip().casefold()
        if not normalized_prompt:
            raise ValueError("Prompt is required.")
        if normalized_treatment not in _TREATMENTS:
            raise ValueError(f"Unsupported governed turn treatment: {treatment}")

        turn_id = f"turn_{uuid.uuid4().hex}"
        user_message = self._append_message(
            role="user",
            content=normalized_prompt,
            turn_id=turn_id,
        )
        parent_binding = (
            self._resolve_binding(parent_run_id)
            if normalized_treatment != "independent"
            else None
        )
        resolved_parent_run_id = ""
        parent_identity: ResumptionIdentity | None = None
        parent_state: dict[str, Any] | None = None
        if parent_binding is not None:
            parent_identity = ResumptionIdentity.from_dict(
                dict(parent_binding["resumption_identity"])
            )
            resolved_parent_run_id = parent_identity.revision_id
            parent_state = self._inspect_state(parent_identity)

        assert self.engine is not None
        if normalized_treatment == "human_contribution":
            assert parent_identity is not None
            assert parent_state is not None
            active_holds = [
                hold
                for hold in parent_state.get("holds", ())
                if hold.get("disposition", "remain_held") == "remain_held"
            ]
            selected_hold = None
            normalized_hold_id = str(target_hold_id or "").strip()
            if normalized_hold_id:
                selected_hold = next(
                    (
                        hold
                        for hold in active_holds
                        if hold.get("hold_id") == normalized_hold_id
                    ),
                    None,
                )
                if selected_hold is None:
                    raise ValueError(
                        f"Unknown active HoldOn: {normalized_hold_id}"
                    )
            elif len(active_holds) == 1:
                selected_hold = active_holds[0]
            elif len(active_holds) > 1:
                raise ValueError(
                    "Multiple HoldOn continuations are active; select one explicitly."
                )
            relationship = (
                InletRelationship.HOLD_SATISFACTION
                if selected_hold is not None
                else InletRelationship.CONTINUATION
            )
            operation = (
                OperationKind.RESUME_SUSPENDED
                if selected_hold is not None
                else OperationKind.CONTINUE
            )
            hold_id = str((selected_hold or {}).get("hold_id", ""))
            target = hold_id or _single_non_achieved_target(parent_state)
            payload = {
                "content": normalized_prompt,
                "answer": normalized_prompt,
                "turn_id": turn_id,
                **dict(inlet_payload or {}),
            }
            if hold_id:
                payload["hold_id"] = hold_id
            result = self.engine.resume(
                ResumptionRequest(
                    anchor=parent_identity,
                    operation=operation,
                    expected_branch_head_revision_id=(
                        parent_identity.revision_id
                    ),
                    inlet=ContinuationInlet(
                        inlet_id=user_message["message_id"],
                        kind="human_contribution",
                        payload=payload,
                        target=target,
                        relationship=relationship,
                        source="human",
                        provenance=(turn_id, parent_identity.revision_id),
                        correlation=dict(
                            (selected_hold or {}).get("correlation", {})
                        ),
                        authority_context={"principal": "local-user"},
                    ),
                )
            )
        elif normalized_treatment == "follow_up":
            assert parent_identity is not None
            assert parent_state is not None
            if parent_binding.get("semantic_outcome") != SemanticOutcome.COMPLETED.value:
                raise ValueError(
                    "A follow-up requires a completed admitted parent revision."
                )
            achieved_ids = {
                str(item["item_id"])
                for item in parent_state.get("achieved", ())
            }
            selected = tuple(dict.fromkeys(selected_item_ids))
            if not selected and len(achieved_ids) == 1:
                selected = tuple(achieved_ids)
            if not selected or not set(selected).issubset(achieved_ids):
                raise ValueError(
                    "Select one or more admitted achieved items for the follow-up."
                )
            objective_id = f"objective_{uuid.uuid4().hex}"
            direction = GoverningDirection(
                objective=normalized_prompt,
                scope=self.scope_id,
                required_outcome="answer the represented follow-up",
            )
            result = self.engine.resume(
                ResumptionRequest(
                    anchor=parent_identity,
                    operation=OperationKind.DERIVE,
                    expected_branch_head_revision_id=(
                        parent_identity.revision_id
                    ),
                    inlet=ContinuationInlet(
                        inlet_id=user_message["message_id"],
                        kind="follow_up",
                        payload={
                            "content": normalized_prompt,
                            "selected_item_ids": list(selected),
                            "target_scope_id": self.scope_id,
                            "target_objective_id": objective_id,
                            "target_branch_id": "main",
                        },
                        target="root",
                        relationship=InletRelationship.CONTINUATION,
                        source="human",
                        provenance=(turn_id, parent_identity.revision_id),
                        correlation={},
                        authority_context={"principal": "local-user"},
                        delta=SemanticDelta(governing_direction=direction),
                    ),
                )
            )
        elif normalized_treatment == "correction":
            assert parent_identity is not None
            assert parent_state is not None
            target_item_id = str(correction_target_item_id or "").strip()
            current_items = {
                str(item["item_id"]): item
                for item in (
                    *parent_state.get("achieved", ()),
                    *parent_state.get("non_achievedness", ()),
                )
            }
            if not target_item_id:
                raise ValueError(
                    "Correction requires an explicit current semantic item identity."
                )
            target_item = current_items.get(target_item_id)
            if target_item is None:
                raise ValueError(
                    f"Correction target is not current: {target_item_id}"
                )
            replacement = SemanticItem(
                item_id=f"item_{uuid.uuid4().hex}",
                kind=str(target_item.get("kind", "corrected_item")),
                payload={
                    "text": normalized_prompt,
                    "source_message_id": user_message["message_id"],
                },
                evidence_references=(user_message["message_id"],),
                provenance_references=(
                    parent_identity.revision_id,
                    turn_id,
                ),
            )
            result = self.engine.resume(
                ResumptionRequest(
                    anchor=parent_identity,
                    operation=OperationKind.CORRECT,
                    expected_branch_head_revision_id=(
                        parent_identity.revision_id
                    ),
                    inlet=ContinuationInlet(
                        inlet_id=user_message["message_id"],
                        kind="correction",
                        payload={"content": normalized_prompt},
                        target=target_item_id,
                        relationship=InletRelationship.CORRECTION,
                        source="human",
                        provenance=(turn_id, parent_identity.revision_id),
                        correlation={},
                        authority_context={"principal": "local-user"},
                        delta=SemanticDelta(
                            supersessions=(
                                Supersession(
                                    target_item_id=target_item_id,
                                    replacement=replacement,
                                    evidence_references=(
                                        user_message["message_id"],
                                    ),
                                    rationale="Explicit user correction.",
                                ),
                            )
                        ),
                    ),
                )
            )
        else:
            result = self.engine.start(
                StartRequest(
                    scope_id=self.scope_id,
                    objective_id=f"objective_{uuid.uuid4().hex}",
                    branch_id="main",
                    initial_inlet=ContinuationInlet(
                        inlet_id=user_message["message_id"],
                        kind="user_request",
                        payload={"prompt": normalized_prompt},
                        target="root",
                        relationship=InletRelationship.CONTINUATION,
                        source="human",
                        provenance=(turn_id,),
                        correlation={},
                        authority_context={"principal": "local-user"},
                    ),
                    governing_direction=GoverningDirection(
                        objective=normalized_prompt,
                        scope=self.scope_id,
                        required_outcome="answer the represented request",
                    ),
                )
            )

        identity = result.resulting_revision_identity or result.source_revision_identity
        if identity is None:
            raise ValueError("The governed turn produced no causal revision identity.")
        summary = _result_summary(result)
        assistant_text = _assistant_text(result)
        assistant_message = self._append_message(
            role="assistant",
            content=assistant_text,
            turn_id=turn_id,
        )
        binding = {
            "binding_id": f"binding_{uuid.uuid4().hex}",
            "turn_id": turn_id,
            "user_message_id": user_message["message_id"],
            "assistant_message_id": assistant_message["message_id"],
            "treatment": normalized_treatment,
            "run_id": identity.revision_id,
            "parent_run_id": resolved_parent_run_id,
            "resumption_identity": identity.to_dict(),
            "execution_attempt_id": result.execution_attempt_id,
            "transition_artifact_reference": (
                result.transition_artifact_reference
            ),
            "sqlite_path": str(self.sqlite_path),
            "semantic_outcome": (
                result.semantic_outcome.value
                if result.semantic_outcome is not None
                else None
            ),
            "execution_outcome": result.execution_outcome.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(self.root / "RUN_BINDINGS.jsonl", binding)
        _write_json(
            self.root / "ACTIVE_BINDING.json",
            {"binding_id": binding["binding_id"]},
        )
        return {
            "assistant_text": assistant_text,
            "turn_id": turn_id,
            "run_id": binding["run_id"],
            "parent_run_id": resolved_parent_run_id,
            "run_outcome": binding["semantic_outcome"],
            "binding": binding,
            "summary": summary,
        }

    def _inspect_state(self, identity: ResumptionIdentity) -> dict[str, Any]:
        assert self.engine is not None
        return dict(
            self.engine.inspect(
                InspectionRequest(
                    target_kind=InspectionTargetKind.REVISION,
                    target_id=identity.revision_id,
                    view=InspectionView.CURRENT_STATE,
                    authority_context={
                        "allowed_scope_ids": [identity.scope_id]
                    },
                )
            ).payload
        )

    def _append_message(self, *, role: str, content: str, turn_id: str) -> dict[str, Any]:
        records = _read_jsonl(self.root / "MESSAGES.jsonl")
        payload = {
            "message_id": f"msg_{uuid.uuid4().hex}",
            "turn_id": turn_id,
            "sequence": len(records) + 1,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(self.root / "MESSAGES.jsonl", payload)
        return payload

    def _resolve_binding(self, run_id: str) -> dict[str, Any]:
        bindings = _read_jsonl(self.root / "RUN_BINDINGS.jsonl")
        normalized_run_id = str(run_id or "").strip()
        if normalized_run_id:
            bindings = [
                binding
                for binding in bindings
                if normalized_run_id
                in {
                    str(binding.get("run_id", "")),
                    str(binding.get("binding_id", "")),
                }
            ]
        else:
            active = _read_json(self.root / "ACTIVE_BINDING.json", default={})
            active_id = str(active.get("binding_id", ""))
            bindings = [
                binding
                for binding in bindings
                if str(binding.get("binding_id", "")) == active_id
            ]
        if not bindings:
            qualifier = f" for run {normalized_run_id}" if normalized_run_id else ""
            raise ValueError(f"No governed run binding is available{qualifier}.")
        return bindings[-1]

    def select_binding(self, run_id: str) -> dict[str, Any]:
        """Select an explicit causal binding for subsequent related turns."""

        binding = self._resolve_binding(run_id)
        _write_json(
            self.root / "ACTIVE_BINDING.json",
            {"binding_id": binding["binding_id"]},
        )
        return binding


def _assistant_text(result: ResumptionResult) -> str:
    final_answer = str(result.presentation.get("final_answer", "") or "").strip()
    if final_answer:
        return final_answer
    outcome = result.semantic_outcome.value if result.semantic_outcome else "ongoing"
    return {
        "paused": "The governed run paused for an explicit boundary contribution.",
        "incomplete": "The governed run is incomplete and remains available for explicit continuation.",
        "exhausted": "The governed run exhausted its current execution bound and remains available for continuation.",
        "ambiguous": "The governed turn requires an explicit disambiguation before state can change.",
        "rejected": "The governed turn was rejected without changing semantic state.",
    }.get(outcome, "The governed run completed without a projected answer.")


def _result_summary(result: ResumptionResult) -> dict[str, Any]:
    return {
        **dict(result.presentation),
        "semantic_outcome": (
            result.semantic_outcome.value
            if result.semantic_outcome is not None
            else None
        ),
        "execution_outcome": result.execution_outcome.value,
        "achieved_item_ids": list(result.achieved_state_summary),
        "non_achievedness_item_ids": list(
            result.non_achievedness_summary
        ),
        "active_hold_ids": list(result.active_hold_summary),
        "diagnostics": dict(result.diagnostics),
    }


def _single_non_achieved_target(state: dict[str, Any]) -> str:
    items = [
        str(item["item_id"])
        for item in state.get("non_achievedness", ())
    ]
    return items[0] if len(items) == 1 else "root"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(dict(payload))
    return records


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _read_json(
    path: Path,
    *,
    default: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not path.exists():
        return dict(default or {})
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return dict(payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_core_chat_loop(
    host: CoreConversationHost,
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    """Run an explicit-routing terminal conversation over the core engine."""

    output_stream.write(
        "Realized core chat. Plain input starts an independent run. "
        "Use /use to select a causal revision, then /continue, /follow-up, "
        "or /correct to relate a turn; /quit exits.\n"
    )
    while True:
        if getattr(input_stream, "isatty", lambda: False)():
            output_stream.write("realized> ")
            output_stream.flush()
        line = input_stream.readline()
        if not line:
            return 0
        text = line.strip()
        if not text:
            continue
        if text in {"/quit", "/exit"}:
            return 0
        if text.startswith("/use "):
            try:
                selected = host.select_binding(text.removeprefix("/use ").strip())
            except Exception as exc:
                output_stream.write(f"error: {exc}\n")
                continue
            output_stream.write(
                f"selected {selected['run_id']}\n"
            )
            continue
        treatment = "independent"
        prompt = text
        target_hold_id = ""
        correction_target_item_id = ""
        selected_item_ids: tuple[str, ...] = ()
        for command, candidate in (
            ("/continue", "human_contribution"),
            ("/follow-up", "follow_up"),
            ("/correct", "correction"),
            ("/new", "independent"),
        ):
            if text == command or text.startswith(command + " "):
                treatment = candidate
                prompt = text[len(command) :].strip()
                break
        if treatment != "independent" and " -- " in prompt:
            selector, prompt = prompt.split(" -- ", 1)
            selector = selector.strip()
            prompt = prompt.strip()
            if treatment == "human_contribution":
                target_hold_id = selector
            elif treatment == "follow_up":
                selected_item_ids = tuple(
                    item.strip()
                    for item in selector.split(",")
                    if item.strip()
                )
            elif treatment == "correction":
                correction_target_item_id = selector
        if not prompt:
            output_stream.write("A prompt must follow the routing command.\n")
            continue
        try:
            report = host.submit(
                prompt,
                treatment=treatment,
                target_hold_id=target_hold_id,
                selected_item_ids=selected_item_ids,
                correction_target_item_id=correction_target_item_id,
            )
        except Exception as exc:
            output_stream.write(f"error: {exc}\n")
            continue
        output_stream.write(str(report["assistant_text"]) + "\n")


__all__ = ["CoreConversationHost", "run_core_chat_loop"]
