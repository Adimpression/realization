# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from realized_host_interaction.context import StaticHostInteractionContext
from realized_host_interaction.models import HostInteractionAttachment, HostInteractionDescriptor
from workstation.foundation.models import WorkstationSession


def workstation_host_interaction_attachments(session: WorkstationSession) -> tuple[HostInteractionAttachment, ...]:
    """
    High Level Purpose:
        In circumstances like workstation-backed use of the shared host-interaction substrate, helps with projecting workstation session attachments into the shared attachment model.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by letting the workstation reuse shared attachment-resolution helpers instead of maintaining a private attachment model.

    Example Input Output:
        Input: `workstation_host_interaction_attachments(session=WorkstationSession(session_id='ws_123', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=('ws.fs.read',), openai_profile='openai_default', openai_env_var='OPENAI_API_KEY', initial_task='Inspect the project.'))`
        Output: ()

    Args:
        session: Value for `session` used by `workstation_host_interaction_attachments`. Expected type: `WorkstationSession`.

    Returns:
        tuple[HostInteractionAttachment, ...]: Result produced by `workstation_host_interaction_attachments`.
    """
    return tuple(
        HostInteractionAttachment(
            name=attachment.name,
            kind=attachment.kind,
            source=attachment.source,
            access_mode=attachment.access_mode,
            mount_path=attachment.mount_path,
            metadata=dict(attachment.metadata),
        )
        for attachment in session.attachments
    )


def workstation_host_interaction_context(session: WorkstationSession) -> StaticHostInteractionContext:
    """
    High Level Purpose:
        In circumstances like letting the governed runtime execute against workstation-style host interactions, helps with projecting one workstation session into the shared host-interaction contract.

    Reference to Theory:
        Supports the six-layer shared-substrate rule by making the workstation a backend implementation of the common host-interaction interface rather than a direct runtime dependency.

    Example Input Output:
        Input: `workstation_host_interaction_context(session=WorkstationSession(session_id='ws_123', root_path='/tmp/ws', created_at='2026-04-03T00:00:00+00:00', attachments=(), allowed_capabilities=('ws.fs.read',), openai_profile='openai_default', openai_env_var='OPENAI_API_KEY', initial_task='Inspect the project.'))`
        Output: StaticHostInteractionContext(descriptor=HostInteractionDescriptor(backend_kind='workstation', attachments=(), allowed_capabilities=('ws.fs.read',), metadata={'session_id': 'ws_123'}))

    Args:
        session: Value for `session` used by `workstation_host_interaction_context`. Expected type: `WorkstationSession`.

    Returns:
        StaticHostInteractionContext: Result produced by `workstation_host_interaction_context`.
    """
    attachments = workstation_host_interaction_attachments(session)
    descriptor = HostInteractionDescriptor(
        backend_kind="workstation",
        attachments=attachments,
        allowed_capabilities=tuple(session.allowed_capabilities),
        metadata={
            "session_id": session.session_id,
            "root_path": session.root_path,
            "openai_profile": session.openai_profile or "",
            "initial_task": session.initial_task,
        },
    )
    return StaticHostInteractionContext(descriptor=descriptor)
