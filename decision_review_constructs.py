"""Compatibility alias for canonical transformation-construct persistence."""

from __future__ import annotations

import sys

from workstation.subject.core import decision_review_constructs as _canonical


sys.modules[__name__] = _canonical
