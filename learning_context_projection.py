"""Compatibility alias for canonical learning-context document projection."""

from __future__ import annotations

import sys

from workstation.subject.core import learning_context_projection as _canonical


sys.modules[__name__] = _canonical
