"""Compatibility alias for canonical direct knowledge reuse behavior."""

from __future__ import annotations

import sys

from realized_core_engine import direct_knowledge_reuse as _canonical


sys.modules[__name__] = _canonical
