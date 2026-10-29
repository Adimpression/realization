"""Compatibility alias for canonical governed closure and commitment behavior."""

from __future__ import annotations

import sys

from realized_core_engine import governed_closure_and_commitment as _canonical


sys.modules[__name__] = _canonical
