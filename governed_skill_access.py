"""Compatibility alias for canonical controller governed-skill access."""

from __future__ import annotations

import sys

from realized_core_engine import governed_skill_access as _canonical


sys.modules[__name__] = _canonical
