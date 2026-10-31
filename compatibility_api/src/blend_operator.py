"""Compatibility alias for canonical Blend operator semantics."""

from __future__ import annotations

import sys

from realized_blend import operators as _canonical


sys.modules[__name__] = _canonical
