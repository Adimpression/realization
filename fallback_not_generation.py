"""Compatibility alias for canonical fallback non-achievedness generation."""

from __future__ import annotations

import sys

from realized_core_engine import fallback_not_generation as _canonical


sys.modules[__name__] = _canonical
