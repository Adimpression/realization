# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from pathlib import Path

from blend_world_models import BlendWorld, BlendWorldMount


def ensure_blend_workstation_world(
    *,
    root_path: Path,
    workspace_path: Path,
    workspace_name: str = "main",
) -> BlendWorld:
    """
    High Level Purpose:
        In circumstances like shared workstation or trial execution, helps with materializing one persistent world root whose mutable mounts can be reused across multiple workstation sessions.

    Reference to Theory:
        Supports Blend sharing by making shared mutable world continuity explicit instead of relying on prompt-to-prompt payload transfer alone.

    Example Input Output:
        Input: `ensure_blend_workstation_world(root_path=Path('/tmp/ws-world'), workspace_path=Path('/tmp/project'))`
        Output: BlendWorld(world_id='bworld_123', root_path='/tmp/ws-world', mounts=(...))

    Args:
        root_path: Value for `root_path` used by `root_path`. Expected type: `Path`.
        workspace_path: Value for `workspace_path` used by `workspace_path`. Expected type: `Path`.
        workspace_name: Value for `workspace_name` used by `workspace_name`. Expected type: `str`. Defaults to `'main'`.

    Returns:
        BlendWorld: Result produced by `ensure_blend_workstation_world`.
    """
    from blend_world_store import ensure_persisted_blend_workstation_world

    return ensure_persisted_blend_workstation_world(
        root_path=root_path,
        workspace_path=workspace_path,
        workspace_name=workspace_name,
    )
