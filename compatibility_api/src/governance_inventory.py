"""Compatibility alias for the canonical controller governance inventory adapter."""

from __future__ import annotations

import sys

from realized_core_engine import governance_inventory as _canonical


sys.modules[__name__] = _canonical
