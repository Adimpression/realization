"""Public module surface for the Realized Blend domain."""

from importlib import import_module
from types import ModuleType


__all__ = [
    "actors",
    "context",
    "coordination",
    "execution",
    "history",
    "observations",
    "operators",
    "ports",
    "sessions",
    "workflows",
    "worlds",
]


def __getattr__(name: str) -> ModuleType:
    """Load only explicitly published Blend modules."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
