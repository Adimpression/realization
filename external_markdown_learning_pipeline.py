"""Compatibility alias for package-owned external Markdown learning."""

from __future__ import annotations

import sys

from realized_exchange import markdown_learning_pipeline as _canonical


sys.modules[__name__] = _canonical
