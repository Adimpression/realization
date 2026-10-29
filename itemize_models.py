"""Compatibility alias for canonical itemization semantic values."""

from __future__ import annotations

import sys

from realized_core_semantics import itemization as _canonical


sys.modules[__name__] = _canonical
