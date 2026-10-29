"""Compatibility alias for canonical foreign skill export adapters."""

from __future__ import annotations

import sys

from realized_exchange import compatibility_export as _canonical


sys.modules[__name__] = _canonical
