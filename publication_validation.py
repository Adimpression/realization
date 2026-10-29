"""Compatibility alias for the canonical subject publication validation module."""

from __future__ import annotations

import sys

from workstation.subject.core import publication_validation as _canonical

sys.modules[__name__] = _canonical
