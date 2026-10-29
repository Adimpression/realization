"""Compatibility alias for workstation entry-owned controller composition."""

from __future__ import annotations

import sys

from workstation.app.cli import runtime_controller as _canonical


sys.modules[__name__] = _canonical
