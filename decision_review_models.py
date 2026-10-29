"""Compatibility alias for canonical decision-review semantic values."""

from __future__ import annotations

import sys

from realized_core_semantics import decision_review as _canonical


sys.modules[__name__] = _canonical
