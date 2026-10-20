# See MODULES.md for the repository module map before editing.
"""Dependency-light binding for the executable controller entrypoint."""
from __future__ import annotations

from collections.abc import Callable

ControllerEntrypoint = Callable[[], int]

_controller_entrypoint: ControllerEntrypoint | None = None


def register_controller_entrypoint(entrypoint: ControllerEntrypoint) -> None:
    """Register the outer CLI composition entrypoint."""
    global _controller_entrypoint
    _controller_entrypoint = entrypoint


def run_registered_controller_entrypoint() -> int:
    """Run the registered CLI composition entrypoint."""
    if _controller_entrypoint is None:
        raise RuntimeError("The controller entrypoint has not been registered.")
    return int(_controller_entrypoint())


__all__ = [
    "ControllerEntrypoint",
    "register_controller_entrypoint",
    "run_registered_controller_entrypoint",
]
