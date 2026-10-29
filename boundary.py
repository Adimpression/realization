"""Compatibility alias for canonical boundary-shape semantic behavior."""

from __future__ import annotations

import sys

from realized_core_semantics import boundary as _canonical


sys.modules[__name__] = _canonical
