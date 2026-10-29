"""Compatibility alias for package-owned validation SQLite infrastructure."""

from __future__ import annotations

import sys

from realized_validation import sqlite_runtime as _canonical


sys.modules[__name__] = _canonical
