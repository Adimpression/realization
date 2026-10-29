"""Compatibility alias for the canonical subject publication renderer."""

from __future__ import annotations

import sys

from workstation.subject.core import publication_render as _canonical

sys.modules[__name__] = _canonical
