"""Compatibility alias for canonical macOS broker primitives."""

from __future__ import annotations

import sys

from realized_core_runtime import macos_brokers as _canonical


sys.modules[__name__] = _canonical
