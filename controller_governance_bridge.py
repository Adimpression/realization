"""Compatibility alias for canonical controller governance bridge."""

from __future__ import annotations

import sys

from realized_core_engine import controller_governance_bridge as _canonical


sys.modules[__name__] = _canonical
