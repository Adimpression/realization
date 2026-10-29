"""Compatibility alias for canonical runtime executor support."""

from __future__ import annotations

import sys

from realized_core_runtime import executor_support as _canonical


sys.modules[__name__] = _canonical
