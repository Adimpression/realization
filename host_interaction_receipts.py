"""Compatibility facade for shared host-interaction receipts."""

from realized_host_interaction.receipts import (
    append_host_interaction_receipt,
    host_interaction_assistant_response_receipt,
    host_interaction_capability_call_receipt,
    host_interaction_delegation_approval_decision_receipt,
    host_interaction_delegation_approval_requested_receipt,
    host_interaction_receipts_path,
    host_interaction_user_prompt_receipt,
)


__all__ = [
    "append_host_interaction_receipt",
    "host_interaction_assistant_response_receipt",
    "host_interaction_capability_call_receipt",
    "host_interaction_delegation_approval_decision_receipt",
    "host_interaction_delegation_approval_requested_receipt",
    "host_interaction_receipts_path",
    "host_interaction_user_prompt_receipt",
]
