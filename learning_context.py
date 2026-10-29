"""Compatibility alias for the outer learning-context persistence adapter."""

from __future__ import annotations

import sys

from realized_exchange import learning_context as _canonical


sys.modules[__name__] = _canonical
