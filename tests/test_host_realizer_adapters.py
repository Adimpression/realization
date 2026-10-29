from __future__ import annotations

import unittest
from types import MappingProxyType
from unittest.mock import patch

from realized_core_runtime.host_brokers import HOST_BROKER_REGISTRY
from realized_core_runtime.host_realizers import packaged_host_realizer_provider
from realized_host_interaction import HostBrokerInvocation


class HostRealizerAdapterTests(unittest.TestCase):
    def test_packaged_provider_advertises_existing_executor_and_broker_identities(self) -> None:
        provider = packaged_host_realizer_provider()

        self.assertTrue(provider.inspect_executor("bash").registered)
        self.assertTrue(provider.inspect_broker("fs.read_text").registered)
        self.assertFalse(provider.inspect_broker("FS.READ_TEXT").registered)

    def test_executor_prerequisite_is_inspectable_before_invocation(self) -> None:
        with patch("realized_core_runtime.host_realizers.shutil.which", return_value=None):
            inspection = packaged_host_realizer_provider().inspect_executor("python3")

        self.assertTrue(inspection.registered)
        self.assertFalse(inspection.available)
        self.assertEqual(inspection.prerequisites[0].prerequisite.identity, "uv")

    def test_broker_override_is_bound_without_mutating_global_registry(self) -> None:
        calls: list[str] = []
        provider = packaged_host_realizer_provider(
            broker_overrides={
                "fs.read_text": lambda invocation, active: calls.append(
                    invocation.identity
                ) or {"status": "ok", "text": "injected"},
            }
        )

        result = provider.invoke_broker(
            HostBrokerInvocation(identity="fs.read_text", arguments={"path": "ignored"})
        )

        self.assertEqual(result, {"status": "ok", "text": "injected"})
        self.assertEqual(calls, ["fs.read_text"])
        self.assertIsInstance(HOST_BROKER_REGISTRY, MappingProxyType)


if __name__ == "__main__":
    unittest.main()
