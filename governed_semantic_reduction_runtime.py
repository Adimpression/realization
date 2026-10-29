"""Compatibility alias for canonical governed reduction coordination."""

from __future__ import annotations

import sys

from realized_core_engine import reduction_runtime as _canonical


sys.modules[__name__] = _canonical
