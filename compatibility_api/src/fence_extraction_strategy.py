"""Compatibility entry and alias for canonical fence extraction."""

from __future__ import annotations

import sys

from realized_core_runtime import fence_extraction as _canonical


if __name__ == "__main__":
    raise SystemExit(_canonical.main())

sys.modules[__name__] = _canonical
