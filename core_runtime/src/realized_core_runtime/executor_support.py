# See MODULES.md for the repository module map before editing.
from __future__ import annotations

from realized_core_semantics.executors import (
    DEFAULT_SUPPORTED_EXECUTOR_FRAMEWORKS,
    normalize_supported_executor_frameworks,
)
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
