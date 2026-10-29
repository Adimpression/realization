"""Compatibility alias for canonical semantic-text helpers."""

from __future__ import annotations

import sys

from realized_core_semantics import semantic_text as _canonical


sys.modules[__name__] = _canonical
