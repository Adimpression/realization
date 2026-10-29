from __future__ import annotations

import unittest

from realized_host_interaction import (
    HostBrokerBinding,
    HostBrokerInvocation,
    HostExecutorBinding,
    HostExecutorInvocation,
    HostRealizerDescriptor,
    HostRealizerInspection,
    HostRealizerPrerequisite,
    HostRealizerPrerequisiteStatus,
    HostRealizerUnavailableError,
    StaticHostRealizerProvider,
    combine_host_realizer_providers,
    host_native_interaction_context,
    host_realizer_provider,
    with_host_realizer_provider,
)


class HostRealizerContractTests(unittest.TestCase):
    def test_exact_identity_lookup_does_not_case_fold(self) -> None:
        provider = StaticHostRealizerProvider(
            executors=(
                HostExecutorBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="executor",
                        identity="python3",
                    ),
                    callback=lambda invocation, active: invocation.identity,
                ),
            ),
        )

        self.assertTrue(provider.inspect_executor("python3").available)
        self.assertFalse(provider.inspect_executor("Python3").registered)

    def test_unavailable_prerequisite_blocks_callback(self) -> None:
        invoked: list[str] = []
        prerequisite = HostRealizerPrerequisite(identity="uv", kind="executable")

        def inspect(descriptor: HostRealizerDescriptor) -> HostRealizerInspection:
            return HostRealizerInspection(
                kind=descriptor.kind,
                identity=descriptor.identity,
                registered=True,
                available=False,
                rationale="uv is not available on PATH.",
                prerequisites=(
                    HostRealizerPrerequisiteStatus(
                        prerequisite=prerequisite,
                        available=False,
                        rationale="Executable was not found.",
                    ),
                ),
            )

        provider = StaticHostRealizerProvider(
            executors=(
                HostExecutorBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="executor",
                        identity="python3",
                        prerequisites=(prerequisite,),
                    ),
                    callback=lambda invocation, active: invoked.append(invocation.identity),
                    inspector=inspect,
                ),
            ),
        )

        with self.assertRaisesRegex(HostRealizerUnavailableError, "uv is not available"):
            provider.execute(
                HostExecutorInvocation(
                    identity="python3",
                    executable_text="print('ok')",
                    stdin_payload={},
                )
            )
        self.assertEqual(invoked, [])

    def test_composed_provider_is_propagated_to_nested_dispatch(self) -> None:
        broker_provider = StaticHostRealizerProvider(
            brokers=(
                HostBrokerBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="broker",
                        identity="test.echo",
                    ),
                    callback=lambda invocation, active: dict(invocation.arguments),
                ),
            ),
        )
        executor_provider = StaticHostRealizerProvider(
            executors=(
                HostExecutorBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="executor",
                        identity="test.executor",
                    ),
                    callback=lambda invocation, active: active.invoke_broker(
                        HostBrokerInvocation(
                            identity="test.echo",
                            arguments={"value": invocation.stdin_payload},
                        )
                    ),
                ),
            ),
        )
        provider = combine_host_realizer_providers(executor_provider, broker_provider)

        result = provider.execute(
            HostExecutorInvocation(
                identity="test.executor",
                executable_text="",
                stdin_payload="nested",
            )
        )

        self.assertEqual(result, {"value": "nested"})

    def test_duplicate_exact_identity_is_rejected(self) -> None:
        binding = HostBrokerBinding(
            descriptor=HostRealizerDescriptor(kind="broker", identity="test.echo"),
            callback=lambda invocation, active: {},
        )

        with self.assertRaisesRegex(ValueError, "Duplicate exact broker"):
            StaticHostRealizerProvider(brokers=(binding, binding))

    def test_context_attaches_provider_without_changing_descriptor_payload(self) -> None:
        provider = StaticHostRealizerProvider()
        original = host_native_interaction_context(metadata={"owner": "test"})
        attached = with_host_realizer_provider(original, provider)

        self.assertEqual(
            attached.describe_host_interaction(),
            original.describe_host_interaction(),
        )
        self.assertIs(host_realizer_provider(attached), provider)
        self.assertIsNone(host_realizer_provider(original))


if __name__ == "__main__":
    unittest.main()
