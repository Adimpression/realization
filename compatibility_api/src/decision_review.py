"""Compatibility alias for canonical subject decision-review persistence."""

from __future__ import annotations

import sys

from workstation.subject.core import decision_review as _canonical

sys.modules[__name__] = _canonical
