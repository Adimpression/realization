"""Compatibility alias for canonical controller artifact semantics."""

from __future__ import annotations

import sys

from realized_core_engine import artifact_semantics as _canonical


sys.modules[__name__] = _canonical
