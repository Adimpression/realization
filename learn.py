"""Historical import facade for controller-owned learning semantics."""

from __future__ import annotations

import sys

from realized_core_engine import learning as _canonical


sys.modules[__name__] = _canonical
