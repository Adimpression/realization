"""Compatibility alias for canonical runtime host brokers."""

from __future__ import annotations

import sys

from realized_core_runtime import host_brokers as _canonical


sys.modules[__name__] = _canonical
