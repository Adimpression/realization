"""Public ABI for Realization's shared host-interaction substrate."""

from .action_dispatch import (
    SHARED_HOST_INTERACTION_ACTION_CAPABILITIES,
    execute_shared_host_interaction_action,
    is_shared_host_interaction_action_capability,
)
from .actions import (
    host_interaction_fs_read,
    host_interaction_net_http,
    host_interaction_process_run,
    host_interaction_repo_search,
    host_interaction_repo_tree,
)
from .context import (
    HostInteractionContext,
    StaticHostInteractionContext,
    host_interaction_attachments,
    host_interaction_descriptor_payload,
    host_interaction_virtual_mounts,
    host_interaction_workspace_root,
    host_native_interaction_context,
    normalize_host_interaction_attachment_path,
    primary_host_interaction_workspace,
    resolve_host_interaction_attachment,
)
from .delegation import (
    artifact_with_delegated_virtual_mounts,
    build_host_interaction_delegated_mounts,
    host_interaction_delegation_requires_escalation,
    normalized_requested_delegation,
)
from .models import HostInteractionAttachment, HostInteractionDescriptor
from .receipts import (
    append_host_interaction_receipt,
    host_interaction_assistant_response_receipt,
    host_interaction_capability_call_receipt,
    host_interaction_delegation_approval_decision_receipt,
    host_interaction_delegation_approval_requested_receipt,
    host_interaction_receipts_path,
    host_interaction_user_prompt_receipt,
)
from .resolution import (
    DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS,
    DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS,
    normalize_host_interaction_attachment_relative_path,
    normalize_host_interaction_delegation_targets,
    primary_workspace_attachment,
    resolve_host_interaction_attachment_reference,
    safe_join_within_attachment_root,
)


__all__ = [
    "DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS",
    "DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS",
    "HostInteractionAttachment",
    "HostInteractionContext",
    "HostInteractionDescriptor",
    "SHARED_HOST_INTERACTION_ACTION_CAPABILITIES",
    "StaticHostInteractionContext",
    "append_host_interaction_receipt",
    "artifact_with_delegated_virtual_mounts",
    "build_host_interaction_delegated_mounts",
    "execute_shared_host_interaction_action",
    "host_interaction_assistant_response_receipt",
    "host_interaction_attachments",
    "host_interaction_capability_call_receipt",
    "host_interaction_delegation_approval_decision_receipt",
    "host_interaction_delegation_approval_requested_receipt",
    "host_interaction_delegation_requires_escalation",
    "host_interaction_descriptor_payload",
    "host_interaction_fs_read",
    "host_interaction_net_http",
    "host_interaction_process_run",
    "host_interaction_receipts_path",
    "host_interaction_repo_search",
    "host_interaction_repo_tree",
    "host_interaction_user_prompt_receipt",
    "host_interaction_virtual_mounts",
    "host_interaction_workspace_root",
    "host_native_interaction_context",
    "is_shared_host_interaction_action_capability",
    "normalize_host_interaction_attachment_path",
    "normalize_host_interaction_attachment_relative_path",
    "normalize_host_interaction_delegation_targets",
    "normalized_requested_delegation",
    "primary_host_interaction_workspace",
    "primary_workspace_attachment",
    "resolve_host_interaction_attachment",
    "resolve_host_interaction_attachment_reference",
    "safe_join_within_attachment_root",
]
