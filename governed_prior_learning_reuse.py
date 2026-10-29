"""Compatibility alias for canonical governed prior-learning reuse behavior."""

from __future__ import annotations

import sys

from realized_core_engine import governed_prior_learning_reuse as _canonical


sys.modules[__name__] = _canonical
