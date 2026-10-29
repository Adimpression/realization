"""Compatibility alias for package-owned learning-context Markdown helpers."""

from __future__ import annotations

import sys

from workstation.subject.core import learning_context_markdown as _canonical


sys.modules[__name__] = _canonical
