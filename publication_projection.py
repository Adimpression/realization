"""Compatibility alias for canonical subject-core publication projection."""

from __future__ import annotations

import sys

from workstation.subject.core import publication_projection as _implementation


sys.modules[__name__] = _implementation
