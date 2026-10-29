"""Compatibility alias for canonical Prolog semantic helpers."""

from __future__ import annotations

import sys

from realized_core_semantics import prolog as _canonical


sys.modules[__name__] = _canonical
