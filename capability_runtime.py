"""Compatibility alias for canonical runtime capability grants."""

from __future__ import annotations

import sys

from realized_core_runtime import capabilities as _canonical


sys.modules[__name__] = _canonical
