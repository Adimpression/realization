"""Compatibility alias for canonical controller trace projection."""

from __future__ import annotations

import sys

from realized_core_engine import constitutional_trace as _canonical


sys.modules[__name__] = _canonical
