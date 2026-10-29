"""Public module surface for Realized exchange adapters."""

from importlib import import_module
from types import ModuleType

__all__ = [
    "artifact_yaml",
    "compatibility_export",
    "compatibility_import",
    "compiler",
    "dependencies",
    "learning_context",
    "learning_context_skills",
    "registry",
    "run_bundle",
    "skill_export",
    "skill_schema",
    "workstation",
]


def __getattr__(name: str) -> ModuleType:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
