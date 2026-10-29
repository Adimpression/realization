"""Compatibility alias for canonical portable-skill registry exchange."""

from __future__ import annotations

import sys

from realized_exchange import registry as _canonical


sys.modules[__name__] = _canonical
