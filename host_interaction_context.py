# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from host_interaction_models import HostInteractionAttachment, HostInteractionDescriptor
from host_interaction_resolution import (
    normalize_host_interaction_attachment_relative_path,
    primary_workspace_attachment,
    resolve_host_interaction_attachment_reference,
)
from semantic_text import collapse_ws


_HOST_INTERACTION_ACCESS_PERMISSIONS = {
    "read": ("list", "read"),
    "read_write": ("list", "read", "write"),
    "write": ("list", "write"),
    "indirect": (),
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


@runtime_checkable
class HostInteractionContext(Protocol):
    def describe_host_interaction(self) -> HostInteractionDescriptor:
        """
        High Level Purpose:
            In circumstances like controller/runtime execution against a pluggable host backend, helps with returning the stable descriptor for the active host-interaction surface.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by making host-native and workstation-backed execution look like different implementations of one contract.

        Example Input Output:
            Input: `describe_host_interaction()`
            Output: HostInteractionDescriptor(backend_kind='host', attachments=(), allowed_capabilities=(), metadata={})

        Returns:
            HostInteractionDescriptor: Result produced by `describe_host_interaction`.
        """


@dataclass(frozen=True)
class StaticHostInteractionContext:
    descriptor: HostInteractionDescriptor

    def describe_host_interaction(self) -> HostInteractionDescriptor:
        """
        High Level Purpose:
            In circumstances like wiring one first shared-substrate backend, helps with exposing a prebuilt descriptor through the common host-interaction interface.

        Reference to Theory:
            Supports the six-layer shared-substrate rule by letting controller/runtime and workstation share one contract without forcing behavioral coupling.

        Example Input Output:
            Input: `StaticHostInteractionContext(descriptor=HostInteractionDescriptor(backend_kind='host')).describe_host_interaction()`
            Output: HostInteractionDescriptor(backend_kind='host', attachments=(), allowed_capabilities=(), metadata={})

        Args:
            self: Bound static host-interaction context instance.

        Returns:
            HostInteractionDescriptor: Result produced by `describe_host_interaction`.
        """
        return self.descriptor


def host_native_interaction_context(*, metadata: dict[str, Any] | None = None) -> StaticHostInteractionContext:
    """
    High Level Purpose:
        In circumstances like governed runtime execution outside any workstation session, helps with materializing the default host-native backend descriptor.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by making ordinary host execution an explicit backend rather than an unspoken default.

    Example Input Output:
        Input: `host_native_interaction_context(metadata={'owner': 'controller'})`
        Output: StaticHostInteractionContext(descriptor=HostInteractionDescriptor(backend_kind='host', attachments=(), allowed_capabilities=(), metadata={'owner': 'controller'}))

    Args:
        metadata: Value for `metadata` used by `host_native_interaction_context`. Expected type: `dict[str, Any] | None`. Defaults to `None`.

    Returns:
        StaticHostInteractionContext: Result produced by `host_native_interaction_context`.
    """
    return StaticHostInteractionContext(
        descriptor=HostInteractionDescriptor(
            backend_kind="host",
            attachments=(),
            allowed_capabilities=(),
            metadata=dict(metadata or {}),
        )
    )


def host_interaction_descriptor_payload(context: HostInteractionContext | None) -> dict[str, Any]:
    """
    High Level Purpose:
        In circumstances like supplement-profile shaping and runtime metadata recording, helps with projecting any host-interaction backend into one JSON-friendly payload.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by giving controller/runtime and workstation one common way to describe backend kind, attachment scope, and allowed capabilities.

    Example Input Output:
        Input: `host_interaction_descriptor_payload(context=None)`
        Output: {'backend_kind': 'host', 'attachments': [], 'allowed_capabilities': [], 'metadata': {}}

    Args:
        context: Value for `context` used by `host_interaction_descriptor_payload`. Expected type: `HostInteractionContext | None`.

    Returns:
        dict[str, Any]: Result produced by `host_interaction_descriptor_payload`.
    """
    active_context = context or host_native_interaction_context()
    return active_context.describe_host_interaction().to_dict()


def host_interaction_attachments(context: HostInteractionContext | None) -> tuple[HostInteractionAttachment, ...]:
    """
    High Level Purpose:
        In circumstances like controller/runtime execution over a pluggable host backend, helps with recovering the active attachment set from the shared host-interaction contract.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by making attachment scope explicit and backend-independent.

    Example Input Output:
        Input: `host_interaction_attachments(context=None)`
        Output: ()

    Args:
        context: Value for `context` used by `host_interaction_attachments`. Expected type: `HostInteractionContext | None`.

    Returns:
        tuple[HostInteractionAttachment, ...]: Result produced by `host_interaction_attachments`.
    """
    active_context = context or host_native_interaction_context()
    return tuple(active_context.describe_host_interaction().attachments)


def resolve_host_interaction_attachment(
    context: HostInteractionContext | None,
    name: str,
) -> tuple[HostInteractionAttachment, str]:
    """
    High Level Purpose:
        In circumstances like controller/runtime use of the shared host-interaction seam, helps with resolving an attachment reference through the common contract rather than through layer-specific path heuristics.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting host-native and workstation-backed backends share the same attachment-addressing behavior.

    Example Input Output:
        Input: `resolve_host_interaction_attachment(context=None, name='main')`
        Output: ValueError('Unknown host interaction attachment: main')

    Args:
        context: Value for `context` used by `resolve_host_interaction_attachment`. Expected type: `HostInteractionContext | None`.
        name: Value for `name` used by `resolve_host_interaction_attachment`. Expected type: `str`.

    Returns:
        tuple[HostInteractionAttachment, str]: Result produced by `resolve_host_interaction_attachment`.
    """
    return resolve_host_interaction_attachment_reference(host_interaction_attachments(context), name)


def normalize_host_interaction_attachment_path(
    context: HostInteractionContext | None,
    *,
    raw_target: str,
    explicit_relative_path: str,
) -> tuple[HostInteractionAttachment, str]:
    """
    High Level Purpose:
        In circumstances like controller/runtime capability planning over the shared host-interaction seam, helps with canonicalizing one attachment reference plus bounded relative path.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by giving all backends one shared attachment-path normalization behavior.

    Example Input Output:
        Input: `normalize_host_interaction_attachment_path(context=None, raw_target='main', explicit_relative_path='README.md')`
        Output: ValueError('Unknown host interaction attachment: main')

    Args:
        context: Value for `context` used by `normalize_host_interaction_attachment_path`. Expected type: `HostInteractionContext | None`.
        raw_target: Value for `raw_target` used by `normalize_host_interaction_attachment_path`. Expected type: `str`.
        explicit_relative_path: Value for `explicit_relative_path` used by `normalize_host_interaction_attachment_path`. Expected type: `str`.

    Returns:
        tuple[HostInteractionAttachment, str]: Result produced by `normalize_host_interaction_attachment_path`.
    """
    return normalize_host_interaction_attachment_relative_path(
        host_interaction_attachments(context),
        raw_target=raw_target,
        explicit_relative_path=explicit_relative_path,
    )


def primary_host_interaction_workspace(
    context: HostInteractionContext | None,
) -> HostInteractionAttachment | None:
    """
    High Level Purpose:
        In circumstances like shared host-interaction execution, helps with recovering the single primary workspace attachment when the current backend exposes exactly one.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting different backends agree on the same bounded default workspace semantics.

    Example Input Output:
        Input: `primary_host_interaction_workspace(context=None)`
        Output: None

    Args:
        context: Value for `context` used by `primary_host_interaction_workspace`. Expected type: `HostInteractionContext | None`.

    Returns:
        HostInteractionAttachment | None: Result produced by `primary_host_interaction_workspace`.
    """
    return primary_workspace_attachment(host_interaction_attachments(context))


def _host_interaction_directory_root(attachment: HostInteractionAttachment) -> str:
    source = collapse_ws(str(getattr(attachment, "source", "")))
    if not source or collapse_ws(str(getattr(attachment, "access_mode", ""))) == "indirect":
        return ""
    candidate = Path(source).expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate.absolute()
    if resolved.exists() and not resolved.is_dir():
        return ""
    return str(resolved)


def host_interaction_virtual_mounts(context: HostInteractionContext | None) -> dict[str, dict[str, Any]]:
    """
    High Level Purpose:
        In circumstances like governed child-runtime execution against a pluggable host backend, helps with projecting attachment-scoped host resources into broker-ready virtual mounts.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by turning host-native and workstation-backed attachment scope into one shared filesystem mediation surface instead of relying on ambient cwd assumptions.

    Example Input Output:
        Input: `host_interaction_virtual_mounts(context=None)`
        Output: {}

    Args:
        context: Value for `context` used by `host_interaction_virtual_mounts`. Expected type: `HostInteractionContext | None`.

    Returns:
        dict[str, dict[str, Any]]: Result produced by `host_interaction_virtual_mounts`.
    """
    mounts: dict[str, dict[str, Any]] = {}
    for attachment in host_interaction_attachments(context):
        mount_name = collapse_ws(str(getattr(attachment, "name", "")))
        if not mount_name:
            continue
        root = _host_interaction_directory_root(attachment)
        if not root:
            continue
        permissions = list(
            _HOST_INTERACTION_ACCESS_PERMISSIONS.get(
                collapse_ws(str(getattr(attachment, "access_mode", ""))),
                (),
            )
        )
        if not permissions:
            continue
        mounts[mount_name] = {
            "root": root,
            "permissions": permissions,
            "data_class": _HOST_INTERACTION_DATA_CLASSES.get(
                collapse_ws(str(getattr(attachment, "kind", ""))),
                "internal",
            ),
            "attachment_kind": collapse_ws(str(getattr(attachment, "kind", ""))),
            "mount_path": collapse_ws(str(getattr(attachment, "mount_path", ""))),
        }
    return mounts


def host_interaction_workspace_root(
    context: HostInteractionContext | None,
    *,
    fallback_root: str = "",
) -> str:
    """
    High Level Purpose:
        In circumstances like governed runtime mediation over a pluggable host backend, helps with recovering the effective workspace root from the shared attachment contract instead of from ambient process cwd.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by making worker filesystem roots derive from the injected host backend, allowing the same runtime to operate against host-native and workstation-backed environments.

    Example Input Output:
        Input: `host_interaction_workspace_root(context=None, fallback_root='/tmp/project')`
        Output: '/tmp/project'

    Args:
        context: Value for `context` used by `host_interaction_workspace_root`. Expected type: `HostInteractionContext | None`.
        fallback_root: Value for `fallback_root` used by `host_interaction_workspace_root`. Expected type: `str`. Defaults to `''`.

    Returns:
        str: Result produced by `host_interaction_workspace_root`.
    """
    primary_workspace = primary_host_interaction_workspace(context)
    if primary_workspace is not None:
        root = _host_interaction_directory_root(primary_workspace)
        if root:
            return root
    for attachment in host_interaction_attachments(context):
        root = _host_interaction_directory_root(attachment)
        if root:
            return root
    if collapse_ws(fallback_root):
        return str(Path(fallback_root).expanduser().resolve())
    return str(Path.cwd().resolve())
