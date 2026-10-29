"""Compatibility alias for the canonical SQLite artifact-store adapter."""

from __future__ import annotations

import sys

from realized_core_engine import store as _canonical


sys.modules[__name__] = _canonical
