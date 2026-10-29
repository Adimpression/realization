"""Compatibility alias for the canonical controller model supplement."""

from __future__ import annotations

import sys

from realized_core_engine import supplement as _canonical


sys.modules[__name__] = _canonical
