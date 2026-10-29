"""Process-local binding for the entry-layer skill exchange adapter."""

from __future__ import annotations

from threading import RLock

from workstation.contracts.runtime import SkillExchangeProvider


_LOCK = RLock()
_provider: SkillExchangeProvider | None = None


def register_skill_exchange_provider(provider: SkillExchangeProvider) -> None:
    """Bind representation translation at the application composition root."""
    if not isinstance(provider, SkillExchangeProvider):
        raise TypeError("provider must implement SkillExchangeProvider")
    global _provider
    with _LOCK:
        _provider = provider


def skill_exchange_provider() -> SkillExchangeProvider:
    """Return the configured adapter or fail at the missing composition seam."""
    with _LOCK:
        provider = _provider
    if provider is None:
        raise RuntimeError(
            "The skill exchange provider is not configured. "
            "Start the application through a supported entry surface or register a provider explicitly."
        )
    return provider


__all__ = ["register_skill_exchange_provider", "skill_exchange_provider"]
