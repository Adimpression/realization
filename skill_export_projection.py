"""Compatibility alias for canonical portable-skill export projection."""

from __future__ import annotations

import sys

from realized_exchange import skill_export as _canonical


sys.modules[__name__] = _canonical
