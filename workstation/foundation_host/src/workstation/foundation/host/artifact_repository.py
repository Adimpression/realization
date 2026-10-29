"""Process-local binding for the application artifact repository provider."""

from __future__ import annotations

from threading import RLock

from workstation.contracts.runtime import ArtifactRepositoryProvider


_LOCK = RLock()
_provider: ArtifactRepositoryProvider | None = None


def register_artifact_repository_provider(
    provider: ArtifactRepositoryProvider,
) -> None:
    """Bind the persistence implementation at the application composition root."""
    if not isinstance(provider, ArtifactRepositoryProvider):
        raise TypeError("provider must implement ArtifactRepositoryProvider")
    global _provider
    with _LOCK:
        _provider = provider


def artifact_repository_provider() -> ArtifactRepositoryProvider:
    """Return the configured provider or fail at the missing composition seam."""
    with _LOCK:
        provider = _provider
    if provider is None:
        raise RuntimeError(
            "The artifact repository provider is not configured. "
            "Start the application through main.py or register a provider explicitly."
        )
    return provider


__all__ = [
    "artifact_repository_provider",
    "register_artifact_repository_provider",
]
