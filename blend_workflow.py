"""Compatibility alias for canonical Blend application workflow adapters."""

from __future__ import annotations

import sys

from realized_blend_application import workflows as _canonical


sys.modules[__name__] = _canonical
