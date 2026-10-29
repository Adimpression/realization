"""Compatibility alias for canonical artifact-exchange dependencies."""

from __future__ import annotations

import sys

from realized_exchange import dependencies as _canonical


sys.modules[__name__] = _canonical
