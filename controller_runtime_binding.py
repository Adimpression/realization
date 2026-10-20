# See MODULES.md for the repository module map before editing.
"""Dependency-light binding for constructing the registered controller runtime."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from system_state import SystemState

ControllerFactory = Callable[..., Any]

_controller_factory: ControllerFactory | None = None


def register_controller_factory(factory: ControllerFactory) -> None:
    """Register the application-owned controller constructor."""
    global _controller_factory
    _controller_factory = factory


def new_registered_controller(state: SystemState, *, llm_policy: str = "off") -> Any:
    """Construct a controller through the application registration seam."""
    if _controller_factory is None:
        raise RuntimeError("The controller runtime has not been registered.")
    return _controller_factory(state=state, llm_policy=llm_policy)


def bootstrap_registered_controller(
    *,
    semantic_unit: str,
    llm_policy: str = "off",
) -> tuple[SystemState, Any]:
    """Bootstrap state and construct its registered controller."""
    state = SystemState.bootstrap(semantic_unit)
    return state, new_registered_controller(state, llm_policy=llm_policy)


__all__ = [
    "ControllerFactory",
    "bootstrap_registered_controller",
    "new_registered_controller",
    "register_controller_factory",
]
