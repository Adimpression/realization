"""Compatibility alias for the canonical bounded Python host transport."""

from __future__ import annotations

import sys

from realized_core_runtime import python_transport as _canonical


sys.modules[__name__] = _canonical
