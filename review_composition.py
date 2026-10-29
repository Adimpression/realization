"""Compatibility alias for canonical subject review composition."""

from __future__ import annotations

import sys

from workstation.subject.core import review_composition as _canonical


sys.modules[__name__] = _canonical
