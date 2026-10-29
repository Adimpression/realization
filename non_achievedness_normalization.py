"""Compatibility alias for canonical non-achievedness normalization."""

from __future__ import annotations

import sys

from realized_core_engine import non_achievedness_normalization as _canonical


sys.modules[__name__] = _canonical
