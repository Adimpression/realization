"""Compatibility alias for the migrated projection subscriber controller."""

from __future__ import annotations

import sys

from workstation.runtime.core import projection_subscriber_controller as _implementation


sys.modules[__name__] = _implementation
