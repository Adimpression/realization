"""Compatibility alias for canonical subject-core Gather source records."""

from __future__ import annotations

import sys

from workstation.subject.core import gather_sources as _implementation


sys.modules[__name__] = _implementation
