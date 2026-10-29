"""Compatibility alias for the canonical Blend world repository adapter."""

from __future__ import annotations

import sys

from realized_blend_application import world_store as _canonical


sys.modules[__name__] = _canonical
