"""Compatibility alias for canonical controller prompt directives behavior."""

from __future__ import annotations

import sys

from realized_core_engine import prompt_directives as _canonical


sys.modules[__name__] = _canonical
