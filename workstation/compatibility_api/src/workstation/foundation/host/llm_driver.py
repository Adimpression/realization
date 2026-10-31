"""Compatibility alias for the runtime-owned LLM provider adapter."""

from __future__ import annotations

import sys

from workstation.runtime.core import llm_driver as _implementation


sys.modules[__name__] = _implementation
