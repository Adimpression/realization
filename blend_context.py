"""Compatibility surface for canonical Blend context values and workstation adaptation."""

from __future__ import annotations

from realized_blend.context import BlendContext, BlendContextAttachment


def blend_context_from_workstation_session(session):
    """Preserve the historical workstation projection entrypoint."""
    from workstation.runtime.core.blend_adapters import (
        blend_context_from_workstation_session as _impl,
    )

    return _impl(session)


__all__ = [
    "BlendContext",
    "BlendContextAttachment",
    "blend_context_from_workstation_session",
]
