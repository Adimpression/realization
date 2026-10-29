"""Compatibility alias for canonical deterministic Markdown semantics."""

from __future__ import annotations

import sys

from realized_core_semantics import markdown as _canonical


sys.modules[__name__] = _canonical
