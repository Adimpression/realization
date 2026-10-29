"""Compatibility alias for canonical semantic normalization behavior."""

from __future__ import annotations

import sys

from realized_core_semantics import normalization as _canonical


sys.modules[__name__] = _canonical
