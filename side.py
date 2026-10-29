"""Compatibility alias for canonical artifact exchange adapters."""

from __future__ import annotations

import sys

from realized_exchange import artifact_yaml as _canonical


sys.modules[__name__] = _canonical
