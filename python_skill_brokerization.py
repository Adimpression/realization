"""Compatibility alias for canonical Python broker inspection."""

from __future__ import annotations

import sys

from realized_core_runtime import python_brokerization as _canonical


sys.modules[__name__] = _canonical
