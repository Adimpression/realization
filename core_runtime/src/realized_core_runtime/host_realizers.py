# See MODULES.md for the repository module map before editing.
"""Application-owned adapters from host-realizer contracts to concrete runtimes."""

from __future__ import annotations

import importlib.util
import platform
import shutil
from collections.abc import Mapping

from realized_core_runtime.execution import execute_cross_boundary
from realized_core_runtime.host_brokers import (
    HOST_BROKER_REGISTRY,
    invoke_host_broker,
)
from realized_host_interaction.realizers import (
    HostBrokerBinding,
    HostBrokerCallback,
    HostBrokerInvocation,
    HostExecutorBinding,
    HostExecutorInvocation,
    HostRealizerDescriptor,
    HostRealizerInspection,
    HostRealizerPrerequisite,
    HostRealizerPrerequisiteStatus,
    HostRealizerProvider,
    StaticHostRealizerProvider,
)


def _binary_inspector(binary: str):
    prerequisite = HostRealizerPrerequisite(identity=binary, kind="executable")

    def inspect(descriptor: HostRealizerDescriptor) -> HostRealizerInspection:
        resolved = shutil.which(binary)
        available = bool(resolved)
        rationale = (
            f"Required executable {binary!r} is available at {resolved}."
            if available
            else f"Required executable {binary!r} is not available on PATH."
        )
        return HostRealizerInspection(
            kind=descriptor.kind,
            identity=descriptor.identity,
            registered=True,
            available=available,
            rationale=rationale,
            prerequisites=(
                HostRealizerPrerequisiteStatus(
                    prerequisite=prerequisite,
                    available=available,
                    rationale=rationale,
                ),
            ),
        )

    return prerequisite, inspect


def _python_module_inspector(module_name: str):
    prerequisite = HostRealizerPrerequisite(identity=module_name, kind="python_module")

    def inspect(descriptor: HostRealizerDescriptor) -> HostRealizerInspection:
        available = importlib.util.find_spec(module_name) is not None
        rationale = (
            f"Required Python module {module_name!r} is importable."
            if available
            else f"Required Python module {module_name!r} is not importable."
        )
        return HostRealizerInspection(
            kind=descriptor.kind,
            identity=descriptor.identity,
            registered=True,
            available=available,
            rationale=rationale,
            prerequisites=(
                HostRealizerPrerequisiteStatus(
                    prerequisite=prerequisite,
                    available=available,
                    rationale=rationale,
                ),
            ),
        )

    return prerequisite, inspect


def _macos_inspector(descriptor: HostRealizerDescriptor) -> HostRealizerInspection:
    prerequisite = descriptor.prerequisites[0]
    available = platform.system() == "Darwin"
    rationale = (
        "The active host is macOS."
        if available
        else "This host realizer requires macOS."
    )
    return HostRealizerInspection(
        kind=descriptor.kind,
        identity=descriptor.identity,
        registered=True,
        available=available,
        rationale=rationale,
        prerequisites=(
            HostRealizerPrerequisiteStatus(
                prerequisite=prerequisite,
                available=available,
                rationale=rationale,
            ),
        ),
    )


def _execute(
    invocation: HostExecutorInvocation,
    provider: HostRealizerProvider,
):
    return execute_cross_boundary(
        framework=invocation.identity,
        executable_text=invocation.executable_text,
        stdin_payload=invocation.stdin_payload,
        timeout_seconds=invocation.timeout_seconds,
        host_runtime_context=invocation.host_runtime_context,
        realizer_provider=provider,
    )


def _invoke_broker(
    invocation: HostBrokerInvocation,
    provider: HostRealizerProvider,
):
    return invoke_host_broker(
        invocation.identity,
        arguments=invocation.arguments,
        governance_context=invocation.governance_context,
        realizer_provider=provider,
    )


def packaged_host_realizer_provider(
    *,
    broker_overrides: Mapping[str, HostBrokerCallback] | None = None,
) -> StaticHostRealizerProvider:
    """Build the immutable concrete provider supplied by the application host."""

    executor_bindings: list[HostExecutorBinding] = []
    for identity, prerequisite_name, inspector_factory in (
        ("python3", "uv", _binary_inspector),
        ("bash", "bash", _binary_inspector),
        ("ansible", "ansible-playbook", _binary_inspector),
        ("wasm_wasi", "wasmtime", _python_module_inspector),
    ):
        prerequisite, inspector = inspector_factory(prerequisite_name)
        executor_bindings.append(
            HostExecutorBinding(
                descriptor=HostRealizerDescriptor(
                    kind="executor",
                    identity=identity,
                    prerequisites=(prerequisite,),
                ),
                callback=_execute,
                inspector=inspector,
            )
        )

    override_map = dict(broker_overrides or {})
    broker_bindings: list[HostBrokerBinding] = []
    for identity in sorted(HOST_BROKER_REGISTRY):
        is_macos = identity.startswith("macos.")
        override = override_map.pop(identity, None)
        broker_bindings.append(
            HostBrokerBinding(
                descriptor=HostRealizerDescriptor(
                    kind="broker",
                    identity=identity,
                    prerequisites=(
                        HostRealizerPrerequisite(identity="macOS", kind="operating_system"),
                    ) if is_macos else (),
                ),
                callback=override or _invoke_broker,
                inspector=_macos_inspector if is_macos and override is None else None,
            )
        )
    for identity in sorted(override_map):
        broker_bindings.append(
            HostBrokerBinding(
                descriptor=HostRealizerDescriptor(kind="broker", identity=identity),
                callback=override_map[identity],
            )
        )
    return StaticHostRealizerProvider(
        executors=tuple(executor_bindings),
        brokers=tuple(broker_bindings),
    )


__all__ = ["packaged_host_realizer_provider"]
