"""Compatibility alias for canonical runtime execution frameworks."""

from __future__ import annotations

import sys

from realized_core_runtime import execution as _canonical


sys.modules[__name__] = _canonical
