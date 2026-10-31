"""Compatibility alias for canonical Blend application operator adapters."""

from __future__ import annotations

import sys

from realized_blend_application import operators as _canonical


sys.modules[__name__] = _canonical
