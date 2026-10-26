# See MODULES.md for the repository module map before editing.
"""Compatibility facade for package-owned data-governance rules."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from realized_core_governance import data as _data
from realized_core_governance.data import *  # noqa: F403


_string_list = _data._string_list
collapse_ws = _data.collapse_ws

__all__ = list(_data.__all__)
