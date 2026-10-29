"""Compatibility alias for canonical controller state."""

from __future__ import annotations

import sys

from realized_core_engine import state as _canonical


sys.modules[__name__] = _canonical
