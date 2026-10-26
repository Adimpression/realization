# See MODULES.md for the repository module map before editing.
"""Compatibility facade for the canonical formal theory model."""

from realized_core_semantics import theory as _theory


__all__ = list(_theory.__all__)
globals().update((name, getattr(_theory, name)) for name in __all__)
