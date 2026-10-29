"""Compatibility alias for canonical runtime temporary-path policy."""

from __future__ import annotations

import sys

from realized_core_runtime import temporary as _canonical


sys.modules[__name__] = _canonical
