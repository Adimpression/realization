"""Compatibility alias for canonical normalization dependencies."""

from __future__ import annotations

import sys

from realized_core_engine import normalization_runtime_dependencies as _canonical


sys.modules[__name__] = _canonical
