"""Compatibility alias for canonical runtime virtual mounts."""

from __future__ import annotations

import sys

from realized_core_runtime import virtual_mounts as _canonical


sys.modules[__name__] = _canonical
