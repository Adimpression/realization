"""Compatibility alias for canonical non-achievedness ranking."""

from __future__ import annotations

import sys

from realized_core_engine import not_elaboration_ranking as _canonical


sys.modules[__name__] = _canonical
