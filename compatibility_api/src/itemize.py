"""Compatibility alias for canonical subject itemization."""

from __future__ import annotations

import sys

from workstation.subject.core import itemization as _canonical

sys.modules[__name__] = _canonical
