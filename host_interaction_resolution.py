# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from semantic_text import collapse_ws

from host_interaction_models import HostInteractionAttachment


DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS = frozenset(
    {
        "",
        ".",
        "./",
        "/",
        "root",
        "workspace",
        "repo",
        "project",
        "/workspace",
        "/workspace/",
        "/workstation",
        "/workstation/mounts",
    }
)

DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS = frozenset(
    {
        "bash_skill_runtime",
        "python3_skill_runtime",
        "wasm_wasi_skill_runtime",
    }
)


def primary_workspace_attachment(
    attachments: Sequence[HostInteractionAttachment],
) -> HostInteractionAttachment | None:
    """
    High Level Purpose:
        In circumstances like attachment-scoped host interaction, helps with resolving the one primary workspace attachment when exactly one canonical workspace is present.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting host-native and workstation-backed backends derive the same bounded workspace default from the same attachment contract.

    Example Input Output:
        Input: `primary_workspace_attachment((HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),))`
        Output: HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main')

    Args:
        attachments: Value for `attachments` used by `primary_workspace_attachment`. Expected type: `Sequence[HostInteractionAttachment]`.

    Returns:
        HostInteractionAttachment | None: Result produced by `primary_workspace_attachment`.
    """
    workspace_attachments = tuple(
        attachment
        for attachment in attachments
        if attachment.kind == "workspace" and not str(attachment.metadata.get("alias_of", "")).strip()
    )
    if len(workspace_attachments) == 1:
        return workspace_attachments[0]
    return None


def resolve_host_interaction_attachment_reference(
    attachments: Sequence[HostInteractionAttachment],
    name: str,
    *,
    root_like_targets: Iterable[str] = DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS,
    runtime_alias_targets: Iterable[str] = DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS,
) -> tuple[HostInteractionAttachment, str]:
    """
    High Level Purpose:
        In circumstances like shared host-interaction attachment addressing, helps with resolving an attachment reference even when the caller supplies a name, mount path, host path, or one path nested beneath an attachment root.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by giving host-native and workstation-backed backends one common attachment-addressing behavior instead of re-implementing path heuristics in each layer.

    Example Input Output:
        Input: `resolve_host_interaction_attachment_reference((HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), '/workstation/mounts/main/src')`
        Output: (HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), 'src')

    Args:
        attachments: Value for `attachments` used by `resolve_host_interaction_attachment_reference`. Expected type: `Sequence[HostInteractionAttachment]`.
        name: Value for `name` used by `resolve_host_interaction_attachment_reference`. Expected type: `str`.
        root_like_targets: Value for `root_like_targets` used by `resolve_host_interaction_attachment_reference`. Expected type: `Iterable[str]`. Defaults to `DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS`.
        runtime_alias_targets: Value for `runtime_alias_targets` used by `resolve_host_interaction_attachment_reference`. Expected type: `Iterable[str]`. Defaults to `DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS`.

    Returns:
        tuple[HostInteractionAttachment, str]: Result produced by `resolve_host_interaction_attachment_reference`.
    """
    normalized_name = str(name or "").strip()
    for attachment in attachments:
        if attachment.name == normalized_name or attachment.mount_path == normalized_name:
            return attachment, ""
        resolved_source = str(Path(attachment.source).expanduser().resolve())
        if resolved_source == normalized_name:
            return attachment, ""
    workspace_attachment = primary_workspace_attachment(attachments)
    if workspace_attachment is not None:
        workspace_source_name = Path(workspace_attachment.source).expanduser().resolve().name
        if normalized_name == workspace_source_name:
            return workspace_attachment, ""
        if normalized_name in {str(item) for item in runtime_alias_targets}:
            return workspace_attachment, ""
    for attachment in attachments:
        prefixes = (
            attachment.mount_path.rstrip("/"),
            str(Path(attachment.source).expanduser().resolve()).rstrip("/"),
        )
        for prefix in prefixes:
            if prefix and normalized_name.startswith(prefix + "/"):
                return attachment, normalized_name[len(prefix) :].lstrip("/")
    if normalized_name in {str(item) for item in root_like_targets} and workspace_attachment is not None:
        return workspace_attachment, ""
    raise ValueError(f"Unknown host interaction attachment: {name}")


def normalize_host_interaction_attachment_relative_path(
    attachments: Sequence[HostInteractionAttachment],
    *,
    raw_target: str,
    explicit_relative_path: str,
    root_like_targets: Iterable[str] = DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS,
    runtime_alias_targets: Iterable[str] = DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS,
) -> tuple[HostInteractionAttachment, str]:
    """
    High Level Purpose:
        In circumstances like shared host-interaction capability normalization, helps with separating one attachment reference from its in-attachment relative path even when both were conflated into one string.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting host-native and workstation-backed backends canonicalize attachment target plus bounded relative path through one shared function.

    Example Input Output:
        Input: `normalize_host_interaction_attachment_relative_path((HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), raw_target='/workstation/mounts/main/src', explicit_relative_path='')`
        Output: (HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'), 'src')

    Args:
        attachments: Value for `attachments` used by `normalize_host_interaction_attachment_relative_path`. Expected type: `Sequence[HostInteractionAttachment]`.
        raw_target: Value for `raw_target` used by `normalize_host_interaction_attachment_relative_path`. Expected type: `str`.
        explicit_relative_path: Value for `explicit_relative_path` used by `normalize_host_interaction_attachment_relative_path`. Expected type: `str`.
        root_like_targets: Value for `root_like_targets` used by `normalize_host_interaction_attachment_relative_path`. Expected type: `Iterable[str]`. Defaults to `DEFAULT_HOST_INTERACTION_ROOT_LIKE_TARGETS`.
        runtime_alias_targets: Value for `runtime_alias_targets` used by `normalize_host_interaction_attachment_relative_path`. Expected type: `Iterable[str]`. Defaults to `DEFAULT_HOST_INTERACTION_RUNTIME_ALIAS_TARGETS`.

    Returns:
        tuple[HostInteractionAttachment, str]: Result produced by `normalize_host_interaction_attachment_relative_path`.
    """
    attachment, derived_relative_path = resolve_host_interaction_attachment_reference(
        attachments,
        raw_target,
        root_like_targets=root_like_targets,
        runtime_alias_targets=runtime_alias_targets,
    )
    normalized_explicit = collapse_ws(str(explicit_relative_path))
    if normalized_explicit:
        try:
            explicit_attachment, explicit_relative = resolve_host_interaction_attachment_reference(
                attachments,
                normalized_explicit,
                root_like_targets=root_like_targets,
                runtime_alias_targets=runtime_alias_targets,
            )
            if explicit_attachment.name == attachment.name:
                return attachment, explicit_relative
        except ValueError:
            pass
        return attachment, normalized_explicit
    return attachment, derived_relative_path


def normalize_host_interaction_delegation_targets(
    attachments: Sequence[HostInteractionAttachment],
    requested_delegation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like attachment-scoped delegated-rights planning, helps with normalizing requested delegation targets onto canonical attachment names.

    Reference to Theory:
        Supports the shared host-interaction contract by ensuring delegated rights can be compared and attenuated across backends using one attachment namespace.

    Example Input Output:
        Input: `normalize_host_interaction_delegation_targets((HostInteractionAttachment(name='main', kind='workspace', source='/tmp/project', access_mode='read_write', mount_path='/workstation/mounts/main'),), [{'capability': 'ws.fs.read', 'target': '/workstation/mounts/main'}])`
        Output: [{'capability': 'ws.fs.read', 'target': 'main'}]

    Args:
        attachments: Value for `attachments` used by `normalize_host_interaction_delegation_targets`. Expected type: `Sequence[HostInteractionAttachment]`.
        requested_delegation: Value for `requested_delegation` used by `normalize_host_interaction_delegation_targets`. Expected type: `list[dict[str, Any]]`.

    Returns:
        list[dict[str, Any]]: Result produced by `normalize_host_interaction_delegation_targets`.
    """
    normalized: list[dict[str, Any]] = []
    for item in requested_delegation:
        updated = dict(item)
        target = collapse_ws(str(item.get("target", "")))
        if target:
            try:
                attachment, _relative_path = resolve_host_interaction_attachment_reference(attachments, target)
                updated["target"] = attachment.name
            except ValueError:
                updated["target"] = target
        normalized.append(updated)
    return normalized


def safe_join_within_attachment_root(base: Path, relative_path: str) -> Path:
    """
    High Level Purpose:
        In circumstances like attachment-scoped file mediation, helps with resolving one relative path without allowing escape from the declared attachment root.

    Reference to Theory:
        Supports the shared host-interaction contract by enforcing bounded attachment access consistently across host-native and workstation-backed backends.

    Example Input Output:
        Input: `safe_join_within_attachment_root(base=Path('/tmp/project'), relative_path='src/app.py')`
        Output: Path('/tmp/project/src/app.py')

    Args:
        base: Value for `base` used by `safe_join_within_attachment_root`. Expected type: `Path`.
        relative_path: Value for `relative_path` used by `safe_join_within_attachment_root`. Expected type: `str`.

    Returns:
        Path: Result produced by `safe_join_within_attachment_root`.
    """
    candidate = (base / relative_path).resolve()
    base_resolved = base.resolve()
    if candidate != base_resolved and base_resolved not in candidate.parents:
        raise ValueError(f"Path escapes attachment root: {relative_path}. Attachment root: {base_resolved}")
    return candidate
