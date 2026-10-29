"""Compatibility alias for canonical governed run-bundle exchange."""

from __future__ import annotations

import sys

from realized_exchange import run_bundle as _canonical


sys.modules[__name__] = _canonical
