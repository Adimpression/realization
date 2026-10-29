"""Compatibility alias for canonical Blend world values."""

from __future__ import annotations

import sys

from realized_blend import worlds as _canonical


sys.modules[__name__] = _canonical
