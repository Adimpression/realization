"""Compatibility alias for canonical semantic-title helpers."""

from __future__ import annotations

import sys

from realized_core_semantics import title_semantics as _canonical


sys.modules[__name__] = _canonical
