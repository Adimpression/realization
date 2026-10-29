"""Compatibility alias for canonical portable-skill schema exchange."""

from __future__ import annotations

import sys

from realized_exchange import skill_schema as _canonical


sys.modules[__name__] = _canonical
