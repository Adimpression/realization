"""Compatibility alias for canonical applied theory primitive behavior."""

from __future__ import annotations

import sys

from realized_core_semantics import applied_primitives as _canonical


sys.modules[__name__] = _canonical
