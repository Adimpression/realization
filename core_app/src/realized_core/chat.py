"""Terminal adapter and compatibility surface for governed conversation."""

from __future__ import annotations

import sys
from typing import TextIO

from realized_core_conversation import CoreConversationHost
from realized_core_llm import ConversationPlanner, ConversationRenderer


def run_core_chat_loop(
    host: CoreConversationHost,
    *,
    planner: ConversationPlanner | None = None,
    renderer: ConversationRenderer | None = None,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
) -> int:
    """Run a terminal adapter over the governed conversation application."""

    output_stream.write(
        "Realized core chat. Plain input uses governed interpretation when "
        "configured, otherwise it starts an independent run. "
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
            output_stream.write(f"selected {selected['run_id']}\n")
            continue
        known_routing_commands = (
            "/continue",
            "/follow-up",
            "/correct",
            "/new",
        )
        if text.startswith("/") and not any(
            text == command or text.startswith(command + " ")
            for command in known_routing_commands
        ):
            output_stream.write(f"unknown command: {text.split(maxsplit=1)[0]}\n")
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
            if planner is not None and treatment == "independent" and not text.startswith("/new"):
                report = host.submit_text(
                    prompt,
                    planner=planner,
                    renderer=renderer,
                )
            else:
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
