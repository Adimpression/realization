# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from realized_host_interaction.context import (
    host_interaction_descriptor_payload,
    host_interaction_virtual_mounts,
    host_native_interaction_context,
)
from realized_host_interaction.resolution import (
    normalize_host_interaction_attachment_relative_path,
    safe_join_within_attachment_root,
)
from realized_core_engine.controller_runtime import BSSCController
from realized_core_engine.state import SystemState
from workstation.foundation.host.host_interaction import workstation_host_interaction_attachments, workstation_host_interaction_context
from workstation.runtime.core.session import launch_workstation_session, load_workstation_session


class HostInteractionContextTests(unittest.TestCase):
    def test_host_native_context_defaults_to_host_backend(self) -> None:
        """
        High Level Purpose:
            In circumstances like first shared-substrate rollout, helps with verifying that the default host-native backend descriptor stays stable and explicit.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring ordinary controller/runtime execution is represented as an explicit `host` backend rather than an ambient assumption.

        Example Input Output:
            Input: `test_host_native_context_defaults_to_host_backend()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        payload = host_interaction_descriptor_payload(host_native_interaction_context(metadata={"owner": "test"}))
        self.assertEqual(payload["backend_kind"], "host")
        self.assertEqual(payload["attachments"], [])
        self.assertEqual(payload["metadata"]["owner"], "test")

    def test_workstation_context_projects_session_into_shared_descriptor(self) -> None:
        """
        High Level Purpose:
            In circumstances like first shared-substrate rollout, helps with verifying that a workstation session can be described through the shared host-interaction contract without importing workstation shell code into the runtime.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring the workstation is represented as a backend implementation of the common contract.

        Example Input Output:
            Input: `test_workstation_context_projects_session_into_shared_descriptor()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            launch_workstation_session(root_path=root, workspace_path=workspace, initial_task="Inspect the project.")
            session = load_workstation_session(root)
            payload = workstation_host_interaction_context(session).describe_host_interaction().to_dict()
            self.assertEqual(payload["backend_kind"], "workstation")
            self.assertIn("ws.fs.read", payload["allowed_capabilities"])
            self.assertTrue(any(item["name"] == "main" for item in payload["attachments"]))
            self.assertEqual(payload["metadata"]["session_id"], session.session_id)

    def test_controller_accepts_injected_host_interaction_context(self) -> None:
        """
        High Level Purpose:
            In circumstances like first shared-substrate rollout, helps with verifying that the governed controller/runtime can accept an injected host-interaction backend and surface it through runtime metadata.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring the governed runtime consumes the contract by injection rather than by importing workstation shell modules directly.

        Example Input Output:
            Input: `test_controller_accepts_injected_host_interaction_context()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            launch_workstation_session(root_path=root, workspace_path=workspace, initial_task="Inspect the project.")
            session = load_workstation_session(root)
            controller = BSSCController(
                SystemState.bootstrap("shared host interaction test"),
                llm_policy="off",
                host_interaction_context=workstation_host_interaction_context(session),
            )
            self.assertEqual(controller.host_interaction_backend_kind(), "workstation")
            self.assertEqual(controller.describe_host_interaction_context()["backend_kind"], "workstation")
            self.assertEqual(controller.runtime_host_interaction_context_payload()["backend_kind"], "workstation")
            attachment, relative_path = controller.resolve_host_interaction_attachment_reference("/workstation/mounts/main")
            self.assertEqual(attachment.name, "main")
            self.assertEqual(relative_path, "")
            normalized_attachment, normalized_relative_path = controller.normalize_host_interaction_attachment_path(
                raw_target="/workstation/mounts/main/src",
                explicit_relative_path="",
            )
            self.assertEqual(normalized_attachment.name, "main")
            self.assertEqual(normalized_relative_path, "src")
            controller.run(max_steps=0)
            self.assertEqual(controller.state.root().metadata["host_interaction_backend_kind"], "workstation")
            self.assertEqual(
                controller.state.root().metadata["host_interaction_primary_workspace"]["name"],
                "main",
            )

    def test_shared_attachment_resolution_helpers_match_workstation_mount_behavior(self) -> None:
        """
        High Level Purpose:
            In circumstances like extracting workstation attachment resolution into the shared substrate, helps with verifying that the shared helper layer preserves the workstation mount-path and root-alias semantics.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring attachment resolution is shared rather than re-implemented differently in workstation and runtime layers.

        Example Input Output:
            Input: `test_shared_attachment_resolution_helpers_match_workstation_mount_behavior()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            launch_workstation_session(root_path=root, workspace_path=workspace, initial_task="Inspect the project.")
            session = load_workstation_session(root)
            attachments = workstation_host_interaction_attachments(session)
            attachment, relative_path = normalize_host_interaction_attachment_relative_path(
                attachments,
                raw_target="/workstation/mounts/main/src",
                explicit_relative_path="",
            )
            self.assertEqual(attachment.name, "main")
            self.assertEqual(relative_path, "src")
            root_attachment, root_relative_path = normalize_host_interaction_attachment_relative_path(
                attachments,
                raw_target="/",
                explicit_relative_path="",
            )
            self.assertEqual(root_attachment.name, "main")
            self.assertEqual(root_relative_path, "")

    def test_workstation_context_derives_attachment_backed_virtual_mounts(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared child-runtime filesystem mediation, helps with verifying that workstation attachment scope becomes broker-ready virtual mounts through the common host-interaction substrate.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring runtime child workers can inherit workstation-backed filesystem scope without importing workstation session logic directly.

        Example Input Output:
            Input: `test_workstation_context_derives_attachment_backed_virtual_mounts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "ws"
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            launch_workstation_session(root_path=root, workspace_path=workspace, initial_task="Inspect the project.")
            session = load_workstation_session(root)
            mounts = host_interaction_virtual_mounts(workstation_host_interaction_context(session))
            self.assertEqual(mounts["main"]["root"], str(workspace.resolve()))
            self.assertEqual(mounts["main"]["permissions"], ["list", "read", "write"])
            self.assertEqual(mounts["skill_input"]["permissions"], ["list", "read"])
            self.assertEqual(mounts["skill_tmp"]["data_class"], "derived")

    def test_safe_join_within_attachment_root_rejects_escape(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared attachment-scoped file mediation, helps with verifying that the common safe-join helper rejects path escape attempts.

        Reference to Theory:
            Verifies the six-layer shared-substrate rule by ensuring bounded attachment access is enforced consistently in the shared substrate.

        Example Input Output:
            Input: `test_safe_join_within_attachment_root_rejects_escape()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            with self.assertRaises(ValueError):
                safe_join_within_attachment_root(base, "../escape.txt")
