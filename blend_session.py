"""Compatibility surface for canonical Blend sessions and workstation adaptation."""

from __future__ import annotations

from realized_blend.sessions import BlendSession


def blend_session_from_workstation_session(
    session,
    *,
    actor_kind: str = "ai_chat",
    projection_kind: str = "ai_chat",
):
    """Preserve the historical workstation projection entrypoint."""
    from workstation.runtime.core.blend_adapters import (
        blend_session_from_workstation_session as _impl,
    )

    return _impl(
        session,
        actor_kind=actor_kind,
        projection_kind=projection_kind,
    )


__all__ = ["BlendSession", "blend_session_from_workstation_session"]
