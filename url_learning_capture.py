"""Compatibility alias for canonical subject URL capture behavior."""

from __future__ import annotations

import sys

from workstation.subject.service import url_learning_capture as _canonical


sys.modules[__name__] = _canonical
