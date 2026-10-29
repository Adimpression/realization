"""Compatibility alias for canonical controller runtime-governance context."""

from __future__ import annotations

import sys

from realized_core_engine import runtime_governance_context as _canonical


sys.modules[__name__] = _canonical
