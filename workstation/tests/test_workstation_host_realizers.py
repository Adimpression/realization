from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from realized_host_interaction import (
    HostBrokerBinding,
    HostRealizerDescriptor,
    StaticHostRealizerProvider,
    host_realizer_provider,
)
from workstation.app.cli.composition import (
    ApplicationControllerRuntimeProvider as _ApplicationControllerRuntimeProvider,
)
from workstation.contracts import HostAwareControllerRuntimeProvider
from workstation.foundation.host.host_interaction import (
    workstation_host_interaction_context,
)
from workstation.foundation.models import WorkstationAttachment, WorkstationSession
from workstation.runtime.core.capabilities import (
    execute_workstation_capability,
    workstation_session_realizer_provider,
)


class WorkstationHostRealizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        self.session = WorkstationSession(
            session_id="ws-test",
            root_path=str(root),
            created_at="2026-10-27T00:00:00Z",
            attachments=(
                WorkstationAttachment(
                    name="main",
                    kind="workspace",
                    source=str(root),
                    access_mode="read_write",
                    mount_path="/workstation/mounts/main",
                ),
            ),
            allowed_capabilities=("ws.repo.tree", "ws.fs.read"),
            openai_profile=None,
            openai_env_var=None,
            initial_task="Inspect the project.",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_session_provider_advertises_only_allowed_shared_actions(self) -> None:
        provider = workstation_session_realizer_provider(self.session)

        self.assertTrue(provider.inspect_broker("ws.repo.tree").available)
        self.assertTrue(provider.inspect_broker("ws.fs.read").available)
        self.assertFalse(provider.inspect_broker("ws.process.run").registered)

    def test_shared_action_uses_explicit_injected_provider(self) -> None:
        invoked: list[str] = []
        provider = StaticHostRealizerProvider(
            brokers=(
                HostBrokerBinding(
                    descriptor=HostRealizerDescriptor(
                        kind="broker",
                        identity="ws.repo.tree",
                    ),
                    callback=lambda invocation, active: invoked.append(
                        invocation.identity
                    ) or {"status": "ok", "tree": ["injected"]},
                ),
            )
        )

        result = execute_workstation_capability(
            self.session,
            "ws.repo.tree",
            {"target": "main"},
            realizer_provider=provider,
        )

        self.assertEqual(result, {"status": "ok", "tree": ["injected"]})
        self.assertEqual(invoked, ["ws.repo.tree"])

    def test_workstation_context_carries_session_provider_explicitly(self) -> None:
        provider = workstation_session_realizer_provider(self.session)
        context = workstation_host_interaction_context(
            self.session,
            realizer_provider=provider,
        )

        self.assertIs(host_realizer_provider(context), provider)
        self.assertEqual(context.describe_host_interaction().backend_kind, "workstation")

    def test_application_composition_combines_packaged_and_session_providers(self) -> None:
        application_provider = _ApplicationControllerRuntimeProvider()
        session_provider = workstation_session_realizer_provider(self.session)
        context = workstation_host_interaction_context(
            self.session,
            realizer_provider=session_provider,
        )

        with patch.dict(
            "os.environ",
            {"STATE_SQLITE_PATH": str(Path(self.tempdir.name) / "state.sqlite3")},
            clear=False,
        ):
            _state, controller = (
                application_provider.bootstrap_controller_with_host_interaction(
                    semantic_unit="Use composed host realizers.",
                    llm_policy="off",
                    host_interaction_context=context,
                )
            )

        combined = host_realizer_provider(controller.host_interaction_context)
        self.assertIsInstance(application_provider, HostAwareControllerRuntimeProvider)
        self.assertIsNotNone(combined)
        self.assertTrue(combined.inspect_executor("python3").registered)
        self.assertTrue(combined.inspect_broker("ws.repo.tree").registered)
        self.assertTrue(combined.inspect_broker("fs.read_text").registered)


if __name__ == "__main__":
    unittest.main()
