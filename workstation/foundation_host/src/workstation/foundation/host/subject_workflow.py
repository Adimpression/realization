"""Process-local binding for the subject-workflow client implementation."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from workstation.contracts.subject import SubjectWorkflowClient


SubjectWorkflowClientFactory = Callable[[], SubjectWorkflowClient]

_LOCK = RLock()
_client_factory: SubjectWorkflowClientFactory | None = None


def register_subject_workflow_client_factory(factory: SubjectWorkflowClientFactory) -> None:
    """Bind the subject client adapter at the application composition root."""
    if not callable(factory):
        raise TypeError("factory must be callable")
    global _client_factory
    with _LOCK:
        _client_factory = factory


def create_subject_workflow_client() -> SubjectWorkflowClient:
    """Create the configured client or fail at the missing composition seam."""
    with _LOCK:
        factory = _client_factory
    if factory is None:
        raise RuntimeError(
            "The subject workflow client factory is not configured. "
            "Start the application through main.py or register a factory explicitly."
        )
    client = factory()
    if not isinstance(client, SubjectWorkflowClient):
        raise TypeError("factory must return a SubjectWorkflowClient")
    return client


__all__ = [
    "SubjectWorkflowClientFactory",
    "create_subject_workflow_client",
    "register_subject_workflow_client_factory",
]
