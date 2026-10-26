# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from realized_skill_semantics.execution import (
    EXECUTOR_FRAMEWORK_ALIASES,
    EXECUTOR_FRAMEWORK_CONTENT_KEYS,
    EXECUTOR_FRAMEWORK_REPRESENTATIONS,
    SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES,
    ability_executable_text,
    ability_executor_framework,
    executor_framework_content_key,
    normalize_executor_framework_name,
)


SUPPORTED_EXECUTOR_FRAMEWORKS_ENV = "BSSC_SUPPORTED_EXECUTORS"
DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS = ("python3",)


def normalize_supported_executor_frameworks(
    values: Iterable[Any] | str | None,
    *,
    default: Sequence[str] = DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS,
) -> list[str]:
    raw_values: list[Any] = []
    if values is None:
        raw_values = list(default)
    elif isinstance(values, str):
        raw_values = [item for item in re.split(r"[,\s]+", values) if item]
    else:
        for item in values:
            if isinstance(item, str):
                raw_values.extend(piece for piece in re.split(r"[,\s]+", item) if piece)
            elif item not in (None, ""):
                raw_values.append(item)

    normalized: list[str] = []
    for item in raw_values:
        framework = normalize_executor_framework_name(item)
        if framework in SUPPORTED_EXECUTOR_FRAMEWORK_CHOICES and framework not in normalized:
            normalized.append(framework)
    if normalized:
        return normalized
    return [
        normalize_executor_framework_name(item)
        for item in default
        if normalize_executor_framework_name(item)
    ]
