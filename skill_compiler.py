"""Compatibility alias for canonical portable-skill compilation."""

from __future__ import annotations

import sys

from realized_exchange import compiler as _canonical


sys.modules[__name__] = _canonical
