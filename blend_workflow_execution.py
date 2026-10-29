"""Compatibility alias for canonical Blend application execution adapters."""

from __future__ import annotations

import sys

from realized_blend_application import execution as _canonical


sys.modules[__name__] = _canonical
