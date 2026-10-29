"""Compatibility alias for the canonical Blend workflow repository adapter."""

from __future__ import annotations

import sys

from realized_blend_application import workflow_store as _canonical


sys.modules[__name__] = _canonical
