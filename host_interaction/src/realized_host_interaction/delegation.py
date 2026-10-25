"""Delegated-rights narrowing for the shared host-interaction substrate."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any, TypeVar

from ._normalization import collapse_ws
from .models import HostInteractionAttachment


ArtifactT = TypeVar("ArtifactT")


_HOST_INTERACTION_DELEGATION_PERMISSIONS = {
    "ws.fs.read": ("read", "list"),
    "ws.fs.write": ("write", "list"),
}

_HOST_INTERACTION_ACCESS_PERMISSIONS = {
    "read": {"read", "list"},
    "read_write": {"read", "write", "list"},
    "write": {"write", "list"},
    "indirect": set(),
}

_HOST_INTERACTION_DATA_CLASSES = {
    "workspace": "public",
    "scratch": "derived",
    "output": "derived",
    "session_root": "internal",
    "skill_exports": "derived",
    "skill_imports": "internal",
    "skill_store": "internal",
}


def normalized_requested_delegation(requested_delegation: Any) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like host-backed delegated-rights planning, helps with normalizing one optional requested-delegation payload into a stable list form suitable for receipts and grant checks.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping invocation-time requested rights explicit and machine-readable independent of whether the caller is workstation-backed or host-native.

    Example Input Output:
        Input: `normalized_requested_delegation([{'capability': 'ws.fs.read', 'target': 'main'}])`
        Output: [{'capability': 'ws.fs.read', 'target': 'main', 'rationale': ''}]

    Args:
        requested_delegation: Value for `requested_delegation` used by `normalized_requested_delegation`. Expected type: `Any`.

    Returns:
        list[dict[str, Any]]: Result produced by `normalized_requested_delegation`.
    """
    if not isinstance(requested_delegation, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in requested_delegation:
        if not isinstance(item, Mapping):
            continue
        capability = collapse_ws(str(item.get("capability", "")))
        if not capability:
            continue
        normalized.append(
            {
                "capability": capability,
                "target": collapse_ws(str(item.get("target", ""))),
                "rationale": str(item.get("rationale", "")),
            }
        )
    return normalized


def host_interaction_delegation_requires_escalation(
    *,
    allowed_capabilities: Sequence[str],
    requested_delegation: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like host-backed delegated-rights planning, helps with separating the requested delegation entries that are already inside the current session grant from those that would require escalation.

    Reference to Theory:
        Supports the shared host-interaction substrate by distinguishing ordinary invocation-time attenuation from new authority acquisition independent of any workstation-specific shell logic.

    Example Input Output:
        Input: `host_interaction_delegation_requires_escalation(allowed_capabilities=('ws.fs.read',), requested_delegation=[{'capability': 'ws.fs.read'}, {'capability': 'ws.fs.write'}])`
        Output: ([{'capability': 'ws.fs.read', 'target': '', 'rationale': ''}], [{'capability': 'ws.fs.write', 'target': '', 'rationale': ''}])

    Args:
        allowed_capabilities: Value for `allowed_capabilities` used by `host_interaction_delegation_requires_escalation`. Expected type: `Sequence[str]`.
        requested_delegation: Value for `requested_delegation` used by `host_interaction_delegation_requires_escalation`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: Result produced by `host_interaction_delegation_requires_escalation`.
    """
    allowed = {collapse_ws(str(item)) for item in allowed_capabilities}
    granted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for item in normalized_requested_delegation(requested_delegation):
        capability = collapse_ws(str(item.get("capability", "")))
        if capability in allowed:
            granted.append(dict(item))
        else:
            missing.append(dict(item))
    return granted, missing


def build_host_interaction_delegated_mounts(
    attachments: Sequence[HostInteractionAttachment],
    *,
    granted_delegation: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like host-backed nested skill invocation, helps with translating granted host-interaction delegation entries into invocation-scoped governed virtual mounts for the child runtime.

    Reference to Theory:
        Supports the shared host-interaction substrate by attenuating backend attachment rights into explicit mount-scoped grants instead of ambient inheritance.

    Example Input Output:
        Input: `build_host_interaction_delegated_mounts((HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), granted_delegation=[{'capability': 'ws.fs.read', 'target': 'main'}])`
        Output: ({'main': {'root': '/tmp/project', 'permissions': ['list', 'read'], 'data_class': 'public', 'attachment_kind': 'workspace', 'mount_path': '/workstation/mounts/main'}}, [{'capability': 'ws.fs.read', 'target': 'main', 'rationale': '', 'mount': 'main', 'permissions': ['list', 'read'], 'data_class': 'public'}], [])

    Args:
        attachments: Value for `attachments` used by `build_host_interaction_delegated_mounts`. Expected type: `Sequence[HostInteractionAttachment]`.
        granted_delegation: Value for `granted_delegation` used by `build_host_interaction_delegated_mounts`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]: Result produced by `build_host_interaction_delegated_mounts`.
    """
    delegated_mounts: dict[str, dict[str, Any]] = {}
    effective_grants: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    attachments_by_name = {
        collapse_ws(str(getattr(attachment, "name", ""))): attachment
        for attachment in attachments
        if collapse_ws(str(getattr(attachment, "name", "")))
    }
    for item in normalized_requested_delegation(granted_delegation):
        capability = collapse_ws(str(item.get("capability", "")))
        target = collapse_ws(str(item.get("target", "")))
        rationale = str(item.get("rationale", ""))
        requested_permissions = set(_HOST_INTERACTION_DELEGATION_PERMISSIONS.get(capability, ()))
        if not requested_permissions:
            unsupported.append(
                {
                    "capability": capability,
                    "target": target,
                    "rationale": rationale,
                    "error": f"Delegation for host-interaction capability {capability!r} is not yet supported.",
                }
            )
            continue
        if not target:
            unsupported.append(
                {
                    "capability": capability,
                    "target": target,
                    "rationale": rationale,
                    "error": "Delegated host-interaction filesystem capabilities require a non-empty attachment target.",
                }
            )
            continue
        attachment = attachments_by_name.get(target)
        if attachment is None:
            unsupported.append(
                {
                    "capability": capability,
                    "target": target,
                    "rationale": rationale,
                    "error": f"Unknown host-interaction attachment {target!r}.",
                }
            )
            continue
        supported_permissions = set(
            _HOST_INTERACTION_ACCESS_PERMISSIONS.get(
                collapse_ws(str(getattr(attachment, "access_mode", ""))),
                set(),
            )
        )
        effective_permissions = sorted(requested_permissions & supported_permissions)
        if not effective_permissions:
            unsupported.append(
                {
                    "capability": capability,
                    "target": target,
                    "rationale": rationale,
                    "error": (
                        f"Attachment {target!r} with access mode {collapse_ws(str(getattr(attachment, 'access_mode', '')))!r} "
                        f"does not support delegation for {capability!r}."
                    ),
                }
            )
            continue
        mount_name = target
        mount_spec = delegated_mounts.get(mount_name, {})
        merged_permissions = sorted(
            {
                collapse_ws(str(current))
                for current in [*mount_spec.get("permissions", []), *effective_permissions]
                if collapse_ws(str(current))
            }
        )
        delegated_mounts[mount_name] = {
            "root": str(getattr(attachment, "source", "")),
            "permissions": merged_permissions,
            "data_class": _HOST_INTERACTION_DATA_CLASSES.get(
                collapse_ws(str(getattr(attachment, "kind", ""))),
                "public",
            ),
            "attachment_kind": collapse_ws(str(getattr(attachment, "kind", ""))),
            "mount_path": collapse_ws(str(getattr(attachment, "mount_path", ""))),
        }
        effective_grants.append(
            {
                "capability": capability,
                "target": target,
                "rationale": rationale,
                "mount": mount_name,
                "permissions": effective_permissions,
                "data_class": _HOST_INTERACTION_DATA_CLASSES.get(
                    collapse_ws(str(getattr(attachment, "kind", ""))),
                    "public",
                ),
            }
        )
    return delegated_mounts, effective_grants, unsupported


def artifact_with_delegated_virtual_mounts(
    artifact: ArtifactT,
    *,
    delegated_mounts: Mapping[str, Any],
    conflict_label: str = "delegated host-interaction",
) -> ArtifactT:
    """
    High Level Purpose:
        In circumstances like nested worker invocation against a host-backed substrate, helps with producing an invocation-scoped artifact view that includes delegated virtual mounts without persisting those grants back into the underlying skill store.

    Reference to Theory:
        Supports the shared host-interaction substrate by keeping delegated rights ephemeral, explicit, and mount-scoped.

    Example Input Output:
        Input: `artifact_with_delegated_virtual_mounts(artifact=3, delegated_mounts={'main': {'root': '/tmp/project', 'permissions': ['read', 'list'], 'data_class': 'public'}})`
        Output: Artifact(id='artifact-skill-...', title='Demo Skill', artifact_type='ability', representation='python_script')

    Args:
        artifact: Value for `artifact` used by `artifact_with_delegated_virtual_mounts`. Expected type: `Artifact`.
        delegated_mounts: Value for `delegated_mounts` used by `artifact_with_delegated_virtual_mounts`. Expected type: `Mapping[str, Any]`.
        conflict_label: Value for `conflict_label` used by `artifact_with_delegated_virtual_mounts`. Expected type: `str`. Defaults to `'delegated host-interaction'`.

    Returns:
        Artifact: Result produced by `artifact_with_delegated_virtual_mounts`.
    """
    if not isinstance(delegated_mounts, Mapping) or not delegated_mounts:
        return artifact
    content = dict(artifact.content) if isinstance(artifact.content, Mapping) else {}
    explicit_mounts = (
        dict(content.get("virtual_mounts", {}))
        if isinstance(content.get("virtual_mounts", {}), Mapping)
        else {}
    )
    merged_mounts = dict(explicit_mounts)
    for raw_name, raw_spec in delegated_mounts.items():
        mount_name = collapse_ws(str(raw_name))
        if not mount_name or not isinstance(raw_spec, Mapping):
            continue
        delegated_spec = dict(raw_spec)
        existing_spec = (
            dict(merged_mounts.get(mount_name, {}))
            if isinstance(merged_mounts.get(mount_name, {}), Mapping)
            else {}
        )
        existing_root = collapse_ws(str(existing_spec.get("root", "")))
        delegated_root = collapse_ws(str(delegated_spec.get("root", "")))
        if existing_root and delegated_root and existing_root != delegated_root:
            raise ValueError(
                f"{conflict_label.capitalize()} mount {mount_name!r} conflicts with the skill's existing mount root."
            )
        merged_permissions = sorted(
            {
                collapse_ws(str(current))
                for current in [*existing_spec.get("permissions", []), *delegated_spec.get("permissions", [])]
                if collapse_ws(str(current))
            }
        )
        merged_mounts[mount_name] = {
            **existing_spec,
            **delegated_spec,
            "permissions": merged_permissions,
        }
    updated_content = dict(content)
    updated_content["virtual_mounts"] = merged_mounts
    return replace(artifact, content=updated_content)
