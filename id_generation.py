"""Compatibility alias for canonical semantic identifier helpers."""

from __future__ import annotations

import sys

from realized_core_semantics import identifiers as _canonical

sys.modules[__name__] = _canonical
