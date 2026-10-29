"""Compatibility alias for subject-service learning capture."""

from __future__ import annotations

import sys

from workstation.subject.service import learning_capture as _implementation


sys.modules[__name__] = _implementation
