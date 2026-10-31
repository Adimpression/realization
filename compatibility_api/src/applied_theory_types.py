"""Compatibility alias for canonical applied semantic model behavior."""

from __future__ import annotations

import sys

from realized_core_semantics import applied_model as _canonical


sys.modules[__name__] = _canonical
