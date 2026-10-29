"""Compatibility alias for package-owned validation ladder infrastructure."""

from __future__ import annotations

import sys

from realized_validation import ladder as _canonical


sys.modules[__name__] = _canonical
