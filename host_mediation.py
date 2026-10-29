"""Compatibility alias for canonical controller host mediation."""

from __future__ import annotations

import sys

from realized_core_engine import host_mediation as _canonical


sys.modules[__name__] = _canonical
