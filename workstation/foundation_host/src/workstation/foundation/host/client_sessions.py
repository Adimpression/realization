"""Compatibility alias for subject-service client session state."""

from __future__ import annotations

import sys

from workstation.subject.service import client_sessions as _implementation


sys.modules[__name__] = _implementation
