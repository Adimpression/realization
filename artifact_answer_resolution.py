"""Compatibility alias for canonical artifact answer resolution behavior."""

from __future__ import annotations

import sys

from realized_core_engine import artifact_answer_resolution as _canonical


sys.modules[__name__] = _canonical
