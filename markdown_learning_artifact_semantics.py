"""Compatibility alias for package-owned Markdown artifact semantics."""

from __future__ import annotations

import sys

from realized_core_engine import markdown_learning_artifact_semantics as _canonical


sys.modules[__name__] = _canonical
