"""Compatibility alias for canonical workstation skill composition."""

from __future__ import annotations

import sys

from realized_skill_application import composition as _canonical


sys.modules[__name__] = _canonical
