"""Compatibility alias for canonical runtime Wasm execution."""

from __future__ import annotations

import sys

from realized_core_runtime import wasm as _canonical


sys.modules[__name__] = _canonical
