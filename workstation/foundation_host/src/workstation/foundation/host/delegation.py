# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_semantics.applied_model import Artifact
from realized_host_interaction.delegation import (
    artifact_with_delegated_virtual_mounts,
    build_host_interaction_delegated_mounts,
)
from workstation.foundation.host.host_interaction import workstation_host_interaction_attachments
from workstation.foundation.models import WorkstationSession


def build_workstation_delegated_mounts(
    session: WorkstationSession,
    *,
    granted_delegation: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """
    High Level Purpose:
        In circumstances like workstation-to-skill invocation, helps with translating granted workstation delegation entries into invocation-scoped governed virtual mounts for the nested skill runtime.

    Reference to Theory:
        Supports the workstation shell / pluggable-worker model by attenuating workstation rights into explicit attachment-scoped grants instead of ambient inheritance.

    Example Input Output:
        Input: `build_workstation_delegated_mounts(session=3, granted_delegation=[{'capability': 'ws.fs.read', 'target': 'main'}])`
        Output: ({'main': {'root': '/tmp/project', 'permissions': ['list', 'read'], 'data_class': 'public'}}, [{'capability': 'ws.fs.read', 'target': 'main', 'mount': 'main', 'permissions': ['list', 'read'], 'data_class': 'public'}], [])

    Args:
        session: Value for `session` used by `build_workstation_delegated_mounts`. Expected type: `WorkstationSession`.
        granted_delegation: Value for `granted_delegation` used by `build_workstation_delegated_mounts`. Expected type: `list[dict[str, Any]]`.

    Returns:
        tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]: Result produced by `build_workstation_delegated_mounts`.
    """
    return build_host_interaction_delegated_mounts(
        workstation_host_interaction_attachments(session),
        granted_delegation=granted_delegation,
    )


def artifact_with_delegated_workstation_mounts(
    artifact: Artifact,
    *,
    delegated_mounts: Mapping[str, Any],
) -> Artifact:
    """
    High Level Purpose:
        In circumstances like invoking one skill from a workstation session, helps with producing an invocation-scoped artifact view that includes delegated virtual mounts without persisting those grants back into the underlying skill store.

    Reference to Theory:
        Supports the workstation delegation model by keeping delegated rights ephemeral, explicit, and attachment-scoped.

    Example Input Output:
        Input: `artifact_with_delegated_workstation_mounts(artifact=3, delegated_mounts={'main': {'root': '/tmp/project', 'permissions': ['read', 'list'], 'data_class': 'public'}})`
        Output: Artifact(id='artifact-skill-...', title='Workstation Repo Search', artifact_type='ability', representation='python_script')

    Args:
        artifact: Value for `artifact` used by `artifact_with_delegated_workstation_mounts`. Expected type: `Artifact`.
        delegated_mounts: Value for `delegated_mounts` used by `artifact_with_delegated_workstation_mounts`. Expected type: `Mapping[str, Any]`.

    Returns:
        Artifact: Result produced by `artifact_with_delegated_workstation_mounts`.
    """
    return artifact_with_delegated_virtual_mounts(
        artifact,
        delegated_mounts=delegated_mounts,
        conflict_label="delegated workstation",
    )
