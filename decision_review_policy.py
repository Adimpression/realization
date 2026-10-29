"""Compatibility alias for canonical subject-core decision policy."""

from __future__ import annotations

import sys

from workstation.subject.core import decision_review_policy as _implementation


sys.modules[__name__] = _implementation
