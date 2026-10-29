"""Compatibility alias for canonical Blend workflow values."""

from __future__ import annotations

import sys

from realized_blend import workflows as _canonical


sys.modules[__name__] = _canonical
