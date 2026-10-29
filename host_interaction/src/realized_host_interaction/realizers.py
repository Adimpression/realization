"""Immutable contracts for exact, inspectable host-realizer binding."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol, runtime_checkable


type HostRealizerKind = Literal["executor", "broker"]


class HostRealizerUnavailableError(RuntimeError):
    """Raised when an exact host realizer is absent or unavailable."""


@dataclass(frozen=True, slots=True)
class HostRealizerPrerequisite:
    """One prerequisite advertised by a concrete host realizer."""

    identity: str
    kind: str = "runtime"
    required: bool = True

    def __post_init__(self) -> None:
        identity = str(self.identity).strip()
        kind = str(self.kind).strip()
        if not identity:
            raise ValueError("Host-realizer prerequisite identity must not be empty.")
        if not kind:
            raise ValueError("Host-realizer prerequisite kind must not be empty.")
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "kind", kind)

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "kind": self.kind,
            "required": self.required,
        }


@dataclass(frozen=True, slots=True)
class HostRealizerPrerequisiteStatus:
    """Current availability of one advertised host prerequisite."""

    prerequisite: HostRealizerPrerequisite
    available: bool
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.prerequisite.to_dict(),
            "available": self.available,
            "rationale": str(self.rationale),
        }


@dataclass(frozen=True, slots=True)
class HostRealizerDescriptor:
    """Stable identity and prerequisites of one supplied host realizer."""

    kind: HostRealizerKind
    identity: str
    prerequisites: tuple[HostRealizerPrerequisite, ...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"executor", "broker"}:
            raise ValueError(f"Unsupported host-realizer kind: {self.kind!r}.")
        identity = str(self.identity).strip()
        if not identity:
            raise ValueError("Host-realizer identity must not be empty.")
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "prerequisites", tuple(self.prerequisites))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "identity": self.identity,
            "prerequisites": [item.to_dict() for item in self.prerequisites],
        }


@dataclass(frozen=True, slots=True)
class HostRealizerInspection:
    """Pre-invocation evidence for an exact host-realizer identity."""

    kind: HostRealizerKind
    identity: str
    registered: bool
    available: bool
    rationale: str
    prerequisites: tuple[HostRealizerPrerequisiteStatus, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "identity", str(self.identity).strip())
        object.__setattr__(self, "rationale", str(self.rationale).strip())
        object.__setattr__(self, "prerequisites", tuple(self.prerequisites))

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "identity": self.identity,
            "registered": self.registered,
            "available": self.available,
            "rationale": self.rationale,
            "prerequisites": [item.to_dict() for item in self.prerequisites],
        }


@dataclass(frozen=True, slots=True)
class HostExecutorInvocation:
    """One exact executor invocation after declaration binding."""

    identity: str
    executable_text: str
    stdin_payload: Any
    timeout_seconds: float | None = None
    host_runtime_context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        identity = str(self.identity).strip()
        if not identity:
            raise ValueError("Executor invocation identity must not be empty.")
        object.__setattr__(self, "identity", identity)
        object.__setattr__(
            self,
            "host_runtime_context",
            MappingProxyType(dict(self.host_runtime_context)),
        )


@dataclass(frozen=True, slots=True)
class HostBrokerInvocation:
    """One exact broker invocation after declaration binding."""

    identity: str
    arguments: Mapping[str, Any] = field(default_factory=dict)
    governance_context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        identity = str(self.identity).strip()
        if not identity:
            raise ValueError("Broker invocation identity must not be empty.")
        object.__setattr__(self, "identity", identity)
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
        object.__setattr__(
            self,
            "governance_context",
            MappingProxyType(dict(self.governance_context)),
        )


@runtime_checkable
class HostRealizerProvider(Protocol):
    """Dependency-inverted host surface used by governed runtime mediation."""

    def executor_bindings(self) -> tuple[HostExecutorBinding, ...]: ...

    def broker_bindings(self) -> tuple[HostBrokerBinding, ...]: ...

    def inspect_executor(self, identity: str) -> HostRealizerInspection: ...

    def inspect_broker(self, identity: str) -> HostRealizerInspection: ...

    def execute(self, invocation: HostExecutorInvocation) -> Any: ...

    def invoke_broker(self, invocation: HostBrokerInvocation) -> Any: ...


type HostRealizerInspector = Callable[[HostRealizerDescriptor], HostRealizerInspection]
type HostExecutorCallback = Callable[[HostExecutorInvocation, HostRealizerProvider], Any]
type HostBrokerCallback = Callable[[HostBrokerInvocation, HostRealizerProvider], Any]


@dataclass(frozen=True, slots=True)
class HostExecutorBinding:
    """One immutable executor descriptor, inspector, and callback binding."""

    descriptor: HostRealizerDescriptor
    callback: HostExecutorCallback = field(repr=False, compare=False)
    inspector: HostRealizerInspector | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.descriptor.kind != "executor":
            raise ValueError("HostExecutorBinding requires an executor descriptor.")


@dataclass(frozen=True, slots=True)
class HostBrokerBinding:
    """One immutable broker descriptor, inspector, and callback binding."""

    descriptor: HostRealizerDescriptor
    callback: HostBrokerCallback = field(repr=False, compare=False)
    inspector: HostRealizerInspector | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.descriptor.kind != "broker":
            raise ValueError("HostBrokerBinding requires a broker descriptor.")


def _missing_inspection(kind: HostRealizerKind, identity: str) -> HostRealizerInspection:
    normalized = str(identity).strip()
    return HostRealizerInspection(
        kind=kind,
        identity=normalized,
        registered=False,
        available=False,
        rationale=f"No {kind} realizer is registered for exact identity {normalized!r}.",
    )


def _default_inspection(descriptor: HostRealizerDescriptor) -> HostRealizerInspection:
    prerequisites = tuple(
        HostRealizerPrerequisiteStatus(
            prerequisite=item,
            available=True,
            rationale="No dynamic prerequisite check was declared.",
        )
        for item in descriptor.prerequisites
    )
    return HostRealizerInspection(
        kind=descriptor.kind,
        identity=descriptor.identity,
        registered=True,
        available=True,
        rationale="Exact host realizer is registered and available.",
        prerequisites=prerequisites,
    )


def _validated_inspection(
    descriptor: HostRealizerDescriptor,
    inspector: HostRealizerInspector | None,
) -> HostRealizerInspection:
    inspection = inspector(descriptor) if inspector is not None else _default_inspection(descriptor)
    if inspection.kind != descriptor.kind or inspection.identity != descriptor.identity:
        raise ValueError("Host-realizer inspector returned evidence for a different identity.")
    if not inspection.registered:
        raise ValueError("A registered host-realizer binding cannot inspect as unregistered.")
    return inspection


class StaticHostRealizerProvider:
    """Immutable exact-identity provider assembled at a composition boundary."""

    __slots__ = ("_broker_bindings", "_brokers", "_executor_bindings", "_executors")

    def __init__(
        self,
        *,
        executors: Sequence[HostExecutorBinding] = (),
        brokers: Sequence[HostBrokerBinding] = (),
    ) -> None:
        executor_bindings = tuple(executors)
        broker_bindings = tuple(brokers)
        executor_map = {item.descriptor.identity: item for item in executor_bindings}
        broker_map = {item.descriptor.identity: item for item in broker_bindings}
        if len(executor_map) != len(executor_bindings):
            raise ValueError("Duplicate exact executor realizer identity.")
        if len(broker_map) != len(broker_bindings):
            raise ValueError("Duplicate exact broker realizer identity.")
        self._executor_bindings = executor_bindings
        self._broker_bindings = broker_bindings
        self._executors = MappingProxyType(executor_map)
        self._brokers = MappingProxyType(broker_map)

    def executor_bindings(self) -> tuple[HostExecutorBinding, ...]:
        return self._executor_bindings

    def broker_bindings(self) -> tuple[HostBrokerBinding, ...]:
        return self._broker_bindings

    def inspect_executor(self, identity: str) -> HostRealizerInspection:
        normalized = str(identity).strip()
        binding = self._executors.get(normalized)
        if binding is None:
            return _missing_inspection("executor", normalized)
        return _validated_inspection(binding.descriptor, binding.inspector)

    def inspect_broker(self, identity: str) -> HostRealizerInspection:
        normalized = str(identity).strip()
        binding = self._brokers.get(normalized)
        if binding is None:
            return _missing_inspection("broker", normalized)
        return _validated_inspection(binding.descriptor, binding.inspector)

    def execute(self, invocation: HostExecutorInvocation) -> Any:
        inspection = self.inspect_executor(invocation.identity)
        if not inspection.available:
            raise HostRealizerUnavailableError(inspection.rationale)
        binding = self._executors[invocation.identity]
        return binding.callback(invocation, self)

    def invoke_broker(self, invocation: HostBrokerInvocation) -> Any:
        inspection = self.inspect_broker(invocation.identity)
        if not inspection.available:
            raise HostRealizerUnavailableError(inspection.rationale)
        binding = self._brokers[invocation.identity]
        return binding.callback(invocation, self)


def combine_host_realizer_providers(
    *providers: HostRealizerProvider | None,
) -> StaticHostRealizerProvider:
    """Compose supplied providers while rejecting ambiguous exact identities."""

    return StaticHostRealizerProvider(
        executors=tuple(
            binding
            for provider in providers
            if provider is not None
            for binding in provider.executor_bindings()
        ),
        brokers=tuple(
            binding
            for provider in providers
            if provider is not None
            for binding in provider.broker_bindings()
        ),
    )


EMPTY_HOST_REALIZER_PROVIDER = StaticHostRealizerProvider()


__all__ = [
    "EMPTY_HOST_REALIZER_PROVIDER",
    "HostBrokerBinding",
    "HostBrokerCallback",
    "HostBrokerInvocation",
    "HostExecutorBinding",
    "HostExecutorCallback",
    "HostExecutorInvocation",
    "HostRealizerDescriptor",
    "HostRealizerInspection",
    "HostRealizerInspector",
    "HostRealizerKind",
    "HostRealizerPrerequisite",
    "HostRealizerPrerequisiteStatus",
    "HostRealizerProvider",
    "HostRealizerUnavailableError",
    "StaticHostRealizerProvider",
    "combine_host_realizer_providers",
]
