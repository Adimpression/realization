"""Installed compatibility alias for the canonical Python skill host API."""

from __future__ import annotations

import sys

from realized_core_runtime import python_host as _canonical


sys.modules[__name__] = _canonical
