"""Public module surface for Realized governance contracts and rules."""

from importlib import import_module
from types import ModuleType

__all__ = [
    "admission",
    "approval",
    "authority",
    "current_use",
    "data",
    "declarations",
    "inventory",
    "lifecycle",
    "persistence",
    "records",
    "safety",
    "trace",
    "vocabulary",
]


def __getattr__(name: str) -> ModuleType:
    """Load only explicitly published governance modules."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    return sorted((*globals(), *__all__))
