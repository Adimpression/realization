from __future__ import annotations

import unittest

from realized_core_runtime.python_transport import (
    PYTHON_SKILL_HOST_ENDPOINT_ENV,
    PYTHON_SKILL_HOST_TOKEN_ENV,
    python_skill_host_bridge,
    request_parent_host_broker,
)
from realized_host_interaction import (
    HostBrokerBinding,
    HostRealizerDescriptor,
    StaticHostRealizerProvider,
)


class PythonSkillHostTransportTests(unittest.TestCase):
    def _provider(self, calls: list[str]) -> StaticHostRealizerProvider:
        return StaticHostRealizerProvider(
            brokers=(
                HostBrokerBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="broker",
                        identity="fs.read_text",
                    ),
                    callback=lambda invocation, active: calls.append(invocation.identity)
                    or {"status": "ok", "text": "parent result"},
                ),
            ),
        )

    def _context(
        self,
        *,
        declared: tuple[str, ...] = ("fs.read_text",),
        grants: tuple[dict[str, str], ...] = (
            {"id": "grant-read", "authority": "read"},
        ),
    ) -> dict[str, object]:
        return {
            "strict_realizer_declaration": True,
            "declared_host_brokers": list(declared),
            "admission": {"status": "admitted", "admitted": True},
            "grants": list(grants),
        }

    def test_authorized_child_request_uses_parent_provider(self) -> None:
        calls: list[str] = []
        with python_skill_host_bridge(
            self._provider(calls),
            governance_context=self._context(),
        ) as environment:
            result = request_parent_host_broker(
                endpoint=environment[PYTHON_SKILL_HOST_ENDPOINT_ENV],
                token=environment[PYTHON_SKILL_HOST_TOKEN_ENV],
                broker_name="fs.read_text",
                arguments={"path": "ignored"},
            )

        self.assertEqual(result, {"status": "ok", "text": "parent result"})
        self.assertEqual(calls, ["fs.read_text"])

    def test_direct_child_request_cannot_bypass_exact_declaration(self) -> None:
        calls: list[str] = []
        with python_skill_host_bridge(
            self._provider(calls),
            governance_context=self._context(declared=()),
        ) as environment:
            result = request_parent_host_broker(
                endpoint=environment[PYTHON_SKILL_HOST_ENDPOINT_ENV],
                token=environment[PYTHON_SKILL_HOST_TOKEN_ENV],
                broker_name="fs.read_text",
                arguments={"path": "ignored"},
            )

        self.assertEqual(result["status"], "error")
        self.assertIn("does not bind the exact host broker", result["error"])
        self.assertEqual(calls, [])

    def test_direct_child_request_cannot_bypass_parent_grants(self) -> None:
        calls: list[str] = []
        with python_skill_host_bridge(
            self._provider(calls),
            governance_context=self._context(grants=()),
        ) as environment:
            result = request_parent_host_broker(
                endpoint=environment[PYTHON_SKILL_HOST_ENDPOINT_ENV],
                token=environment[PYTHON_SKILL_HOST_TOKEN_ENV],
                broker_name="fs.read_text",
                arguments={"path": "ignored"},
            )

        self.assertEqual(result["status"], "error")
        self.assertIn("Runtime grants do not cover", result["error"])
        self.assertEqual(calls, [])

    def test_wrong_invocation_token_never_reaches_provider(self) -> None:
        calls: list[str] = []
        with python_skill_host_bridge(
            self._provider(calls),
            governance_context=self._context(),
        ) as environment:
            result = request_parent_host_broker(
                endpoint=environment[PYTHON_SKILL_HOST_ENDPOINT_ENV],
                token="wrong-token",
                broker_name="fs.read_text",
                arguments={"path": "ignored"},
            )

        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid invocation-scoped bridge token", result["error"])
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
