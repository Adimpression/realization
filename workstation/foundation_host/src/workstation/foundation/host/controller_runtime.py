"""Process-local binding for the outer controller-runtime implementation."""

from __future__ import annotations

from threading import RLock

from workstation.contracts.runtime import ControllerRuntimeProvider


_LOCK = RLock()
_provider: ControllerRuntimeProvider | None = None


def register_controller_runtime_provider(provider: ControllerRuntimeProvider) -> None:
    """Bind the controller implementation at the application composition root."""
    if not isinstance(provider, ControllerRuntimeProvider):
        raise TypeError("provider must implement ControllerRuntimeProvider")
    global _provider
    with _LOCK:
        _provider = provider


def controller_runtime_provider() -> ControllerRuntimeProvider:
    """Return the configured provider or fail at the missing composition seam."""
    with _LOCK:
        provider = _provider
    if provider is None:
        raise RuntimeError(
            "The controller runtime provider is not configured. "
            "Start the application through realized-workstation or register a provider explicitly."
        )
    return provider


__all__ = [
    "controller_runtime_provider",
    "register_controller_runtime_provider",
]
