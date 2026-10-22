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
    EngineConfiguration,
    EngineInlet,
    inspect as inspect_engine,
    resume as resume_engine,
    run as run_engine,
)


_TREATMENTS = {"independent", "human_contribution", "follow_up", "correction"}


@dataclass
class CoreConversationHost:
    """Own transcript and turn/run correlation while delegating reduction."""

    root: Path
    configuration: EngineConfiguration

    def __post_init__(self) -> None:
        self.root = Path(self.root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "states").mkdir(parents=True, exist_ok=True)
        for name in ("MESSAGES.jsonl", "RUN_BINDINGS.jsonl"):
            path = self.root / name
            if not path.exists():
                path.write_text("", encoding="utf-8")

    @property
    def sqlite_path(self) -> Path:
        selected = self.configuration.sqlite_path or (self.root / "artifacts.sqlite3")
        return Path(selected).expanduser().resolve()

    def submit(
        self,
        prompt: str,
        *,
        treatment: str = "independent",
        parent_run_id: str = "",
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
        parent_summary: dict[str, Any] | None = None
        resolved_parent_run_id = ""
        if parent_binding is not None:
            parent_checkpoint = Path(parent_binding["checkpoint_path"])
            parent_summary = dict(inspect_engine(parent_checkpoint).summary)
            resolved_parent_run_id = str(parent_summary.get("run_id", ""))
            if parent_run_id and resolved_parent_run_id != parent_run_id:
                raise ValueError("The selected parent run does not match its checkpoint.")

        inlets: tuple[EngineInlet, ...] = ()
        if normalized_treatment == "human_contribution":
            if str((parent_summary or {}).get("run_outcome", "")) not in {
                "paused",
                "incomplete",
            }:
                raise ValueError(
                    "A human contribution may resume only a paused or incomplete run."
                )
            checkpoint_path = Path(parent_binding["checkpoint_path"]).resolve()
            inlets = (
                EngineInlet(
                    kind="human_contribution",
                    content=normalized_prompt,
                    source_ref=user_message["message_id"],
                    provenance=(turn_id, resolved_parent_run_id),
                    context={"turn_id": turn_id, "parent_run_id": resolved_parent_run_id},
                ),
            )
            result = resume_engine(
                checkpoint_path,
                configuration=self._turn_configuration(
                    checkpoint_path=checkpoint_path,
                    inlets=inlets,
                ),
            )
        elif normalized_treatment in {"follow_up", "correction"}:
            prior_answer = str((parent_summary or {}).get("final_answer", "") or "").strip()
            if (
                str((parent_summary or {}).get("run_outcome", "")) != "completed"
                or not prior_answer
            ):
                raise ValueError(
                    f"A {normalized_treatment} requires a completed parent run with a committed result."
                )
            checkpoint_path = (self.root / "states" / f"{turn_id}.json").resolve()
            inlets = (
                EngineInlet(
                    kind="prior_result",
                    content=prior_answer,
                    source_ref=resolved_parent_run_id,
                    provenance=(turn_id,),
                    context={
                        "relationship": normalized_treatment,
                        "parent_run_id": resolved_parent_run_id,
                    },
                ),
            )
            result = run_engine(
                normalized_prompt,
                configuration=self._turn_configuration(
                    checkpoint_path=checkpoint_path,
                    inlets=inlets,
                ),
            )
        else:
            checkpoint_path = (self.root / "states" / f"{turn_id}.json").resolve()
            result = run_engine(
                normalized_prompt,
                configuration=self._turn_configuration(checkpoint_path=checkpoint_path),
            )

        summary = dict(result.summary)
        assistant_text = _assistant_text(summary)
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
            "run_id": str(summary.get("run_id", "")),
            "parent_run_id": resolved_parent_run_id,
            "checkpoint_path": str(checkpoint_path),
            "sqlite_path": str(self.sqlite_path),
            "run_outcome": str(summary.get("run_outcome", "ongoing")),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(self.root / "RUN_BINDINGS.jsonl", binding)
        return {
            "assistant_text": assistant_text,
            "turn_id": turn_id,
            "run_id": binding["run_id"],
            "parent_run_id": resolved_parent_run_id,
            "run_outcome": binding["run_outcome"],
            "checkpoint_path": str(checkpoint_path),
            "binding": binding,
            "summary": summary,
        }

    def _turn_configuration(
        self,
        *,
        checkpoint_path: Path,
        inlets: tuple[EngineInlet, ...] = (),
    ) -> EngineConfiguration:
        return replace(
            self.configuration,
            state_output_path=checkpoint_path,
            sqlite_path=self.sqlite_path,
            inlets=inlets,
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
                if str(binding.get("run_id", "")) == normalized_run_id
            ]
        if not bindings:
            qualifier = f" for run {normalized_run_id}" if normalized_run_id else ""
            raise ValueError(f"No governed run binding is available{qualifier}.")
        return bindings[-1]


def _assistant_text(summary: dict[str, Any]) -> str:
    final_answer = str(summary.get("final_answer", "") or "").strip()
    if final_answer:
        return final_answer
    outcome = str(summary.get("run_outcome", "ongoing"))
    return {
        "paused": "The governed run paused for an explicit boundary contribution.",
        "incomplete": "The governed run is incomplete and remains available for explicit continuation.",
        "ongoing": "The governed run remains in progress.",
    }.get(outcome, "The governed run completed without a projected answer.")


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


def run_core_chat_loop(
    host: CoreConversationHost,
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    """Run an explicit-routing terminal conversation over the core engine."""

    output_stream.write(
        "Realized core chat. Plain input starts an independent run. "
        "Use /continue, /follow-up, or /correct to relate a turn; /quit exits.\n"
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
        treatment = "independent"
        prompt = text
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
        if not prompt:
            output_stream.write("A prompt must follow the routing command.\n")
            continue
        try:
            report = host.submit(prompt, treatment=treatment)
        except Exception as exc:
            output_stream.write(f"error: {exc}\n")
            continue
        output_stream.write(str(report["assistant_text"]) + "\n")


__all__ = ["CoreConversationHost", "run_core_chat_loop"]
