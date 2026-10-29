"""Compatibility alias for canonical Blend application world materialization."""

from __future__ import annotations

import sys

from realized_blend_application import worlds as _canonical


sys.modules[__name__] = _canonical
