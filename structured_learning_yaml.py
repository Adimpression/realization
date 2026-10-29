"""Compatibility alias for canonical structured-learning rendering."""

from __future__ import annotations

import sys

from realized_core_engine import structured_learning as _canonical


sys.modules[__name__] = _canonical
