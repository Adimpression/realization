"""Compatibility alias for the canonical runtime host ABI."""

from __future__ import annotations

import sys

from realized_core_runtime import host_abi as _canonical


sys.modules[__name__] = _canonical
