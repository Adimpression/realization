"""Compatibility alias for the canonical controller-runtime binding."""

from __future__ import annotations

import sys

from realized_core_engine import controller_runtime_binding as _canonical


sys.modules[__name__] = _canonical
