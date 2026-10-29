"""Compatibility alias for learning-context skill exchange projection."""

from __future__ import annotations

import sys

from realized_exchange import learning_context_skills as _canonical


sys.modules[__name__] = _canonical
