"""Compatibility alias for canonical controller semantic prompt posture behavior."""

from __future__ import annotations

import sys

from realized_core_engine import semantic_prompt_posture as _canonical


sys.modules[__name__] = _canonical
