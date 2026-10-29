"""Compatibility alias for canonical controller retrieval ranking behavior."""

from __future__ import annotations

import sys

from realized_core_engine import retrieval_ranking as _canonical


sys.modules[__name__] = _canonical
