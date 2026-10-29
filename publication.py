"""Compatibility alias for the canonical subject publication substrate."""

from __future__ import annotations

import sys

from workstation.subject.core import publication as _canonical

sys.modules[__name__] = _canonical
