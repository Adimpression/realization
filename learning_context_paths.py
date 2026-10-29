# See MODULES.md for the repository module map before editing.
"""Compatibility alias for canonical subject corpus path behavior."""

from __future__ import annotations

import sys

from workstation.subject.core import learning_context_paths as _canonical


sys.modules[__name__] = _canonical
