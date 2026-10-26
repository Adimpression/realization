"""Package-local deterministic text normalization."""

from __future__ import annotations

import re
from typing import Any


def collapse_ws(value: Any) -> str:
    """Remove controls and collapse whitespace exactly once."""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return re.sub(r"\s+", " ", text).strip()
