"""Compatibility alias for canonical workstation skill IR projection."""

from __future__ import annotations

import sys

from realized_skill_application import ir as _canonical


sys.modules[__name__] = _canonical
