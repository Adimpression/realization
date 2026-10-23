"""Workstation composition adapter for governed conversational resumption."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from realized_core_conversation import CoreConversationHost
from realized_core_llm import build_environment_conversation_advisors


def submit_governed_conversation_turn(
    *,
    root_path: Path,
    prompt_text: str,
    model: str | None = None,
    max_steps: int = 256,
    llm_policy: str = "auto",
    parent_run_id: str = "",
) -> dict[str, Any]:
    """Submit ordinary language through the shared conversation product path."""

    if llm_policy == "off":
        raise ValueError(
            "Governed conversation requires a planning provider. Use the "
            "governed_reduction route for explicit LLM-off treatments."
        )
    conversation_root = (
        Path(root_path).expanduser().resolve() / "governed_conversation"
    )
    host = CoreConversationHost.open(
        root=conversation_root,
        max_steps=max_steps,
        llm_policy=llm_policy,
    )
    planner, renderer = build_environment_conversation_advisors(model=model)
    return host.submit_text(
        prompt_text,
        planner=planner,
        renderer=renderer,
        parent_run_id=parent_run_id,
    )


__all__ = ["submit_governed_conversation_turn"]
