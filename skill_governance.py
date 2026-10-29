"""Compatibility alias for canonical controller skill governance."""

from __future__ import annotations

import sys

from realized_core_engine import skill_governance as _canonical


sys.modules[__name__] = _canonical
