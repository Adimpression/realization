"""Public module surface for Realized formal semantic contracts."""

from importlib import import_module
from types import ModuleType

__all__ = [
    "applied_model",
    "applied_primitives",
    "artifacts",
    "boundary",
    "decision_review",
    "executors",
    "identifiers",
    "itemization",
    "markdown",
    "normalization",
    "prolog",
    "proposals",
    "semantic_text",
    "theory",
    "title_semantics",
    "transformation_constructs",
    "values",
]


def __getattr__(name: str) -> ModuleType:
    """Load public contract modules without coupling independent submodules."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
