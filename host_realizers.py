"""Compatibility alias for canonical concrete host realizers."""

from __future__ import annotations

import sys

from realized_core_runtime import host_realizers as _canonical


sys.modules[__name__] = _canonical
