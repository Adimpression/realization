"""Stable application-facing surface for CLI and workstation UI adapters."""

from workstation.foundation.events.event_bus import append_workstation_receipt_and_publish
from workstation.foundation.models import (
    WorkstationDelegationEscalationDecision,
    WorkstationDelegationEscalationRequest,
)
from workstation.runtime.core.capabilities import (
    AVAILABLE_WORKSTATION_CAPABILITIES,
    DEFAULT_WORKSTATION_CAPABILITIES,
    execute_workstation_capability,
)
from workstation.runtime.core.chat_commands import (
    canonical_workstation_chat_slash_command_text,
    run_workstation_chat_slash_command,
    workstation_chat_slash_commands,
)
from workstation.runtime.core.projection_subscriber_controller import (
    WorkstationProjectionSubscriberController,
)
from workstation.runtime.core.session import (
    launch_workstation_session,
    load_workstation_session,
    prompt_workstation_session,
)
from workstation.runtime.core.workstation_core import (
    workstation_export_learned_skill_bundle_action,
)
from workstation.shell.core.chat_shell import (
    workstation_chat_context,
    workstation_chat_help_text,
    workstation_chat_prepare_last_assistant_resolution,
    workstation_chat_prepare_markdown_prompt,
    workstation_chat_prompt_target_plan,
    workstation_chat_resume_research_prompt,
    workstation_chat_routed_llm_prompt_text,
)
from workstation.shell.core.workstation_shell_client import InProcessWorkstationShellClient

__all__ = [
    "AVAILABLE_WORKSTATION_CAPABILITIES",
    "DEFAULT_WORKSTATION_CAPABILITIES",
    "InProcessWorkstationShellClient",
    "WorkstationDelegationEscalationDecision",
    "WorkstationDelegationEscalationRequest",
    "WorkstationProjectionSubscriberController",
    "append_workstation_receipt_and_publish",
    "canonical_workstation_chat_slash_command_text",
    "execute_workstation_capability",
    "launch_workstation_session",
    "load_workstation_session",
    "prompt_workstation_session",
    "run_workstation_chat_slash_command",
    "workstation_chat_context",
    "workstation_chat_help_text",
    "workstation_chat_prepare_last_assistant_resolution",
    "workstation_chat_prepare_markdown_prompt",
    "workstation_chat_prompt_target_plan",
    "workstation_chat_resume_research_prompt",
    "workstation_chat_routed_llm_prompt_text",
    "workstation_chat_slash_commands",
    "workstation_export_learned_skill_bundle_action",
]
