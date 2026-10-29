"""Compatibility alias for canonical foreign skill import adapters."""

from __future__ import annotations

import sys

from realized_exchange import compatibility_import as _canonical


sys.modules[__name__] = _canonical
