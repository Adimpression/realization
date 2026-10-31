"""Compatibility alias for canonical workstation skill normalization."""

from __future__ import annotations

import sys

from realized_skill_application import normalization as _canonical


sys.modules[__name__] = _canonical
