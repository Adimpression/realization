"""Compatibility alias for contract-owned deterministic prompt routing."""

from __future__ import annotations

import sys

from workstation.contracts import shell_prompt_routing as _implementation


sys.modules[__name__] = _implementation
