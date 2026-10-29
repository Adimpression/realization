"""Compatibility alias for canonical run outcome harvest and reporting behavior."""

from __future__ import annotations

import sys

from realized_core_engine import run_outcome_harvest_and_reporting as _canonical


sys.modules[__name__] = _canonical
