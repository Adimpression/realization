# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import unittest

from realized_host_interaction.delegation import (
    artifact_with_delegated_virtual_mounts,
    build_host_interaction_delegated_mounts,
    host_interaction_delegation_requires_escalation,
    normalized_requested_delegation,
)
from realized_host_interaction.models import HostInteractionAttachment
from realized_core_semantics.applied_model import Artifact, ArtifactType
from realized_core_semantics.applied_primitives import (
    ArtifactAdmission,
    ArtifactRepresentation,
    ArtifactReuse,
    LearningRelation,
)


class HostInteractionDelegationTests(unittest.TestCase):
    def test_normalized_requested_delegation_filters_invalid_items(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared delegated-rights planning, helps with verifying that malformed or capability-less delegation entries are removed while valid ones are normalized.

        Reference to Theory:
            Verifies the shared host-interaction substrate by ensuring requested rights become explicit, comparable records before any backend-specific grant logic runs.

        Example Input Output:
            Input: `test_normalized_requested_delegation_filters_invalid_items()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        normalized = normalized_requested_delegation(
            [
                {"capability": " ws.fs.read ", "target": " main "},
                {"target": "scratch"},
                "ignore",
                {"capability": ""},
            ]
        )

        self.assertEqual(
            normalized,
            [{"capability": "ws.fs.read", "target": "main", "rationale": ""}],
        )

    def test_delegation_requires_escalation_splits_allowed_from_missing(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared delegated-rights planning, helps with verifying that ordinary attenuation is separated from escalation-required rights.

        Reference to Theory:
            Verifies the shared host-interaction substrate by keeping current-session delegation distinct from new authority acquisition.

        Example Input Output:
            Input: `test_delegation_requires_escalation_splits_allowed_from_missing()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        granted, missing = host_interaction_delegation_requires_escalation(
            allowed_capabilities=("ws.fs.read",),
            requested_delegation=[
                {"capability": "ws.fs.read", "target": "main"},
                {"capability": "ws.fs.write", "target": "scratch"},
            ],
        )

        self.assertEqual(granted, [{"capability": "ws.fs.read", "target": "main", "rationale": ""}])
        self.assertEqual(missing, [{"capability": "ws.fs.write", "target": "scratch", "rationale": ""}])

    def test_build_host_interaction_delegated_mounts_projects_attachment_scope(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared nested-worker invocation, helps with verifying that granted attachment-scoped rights become ephemeral virtual mounts with bounded permissions.

        Reference to Theory:
            Verifies the shared host-interaction substrate by turning backend attachments into explicit child-runtime mount grants instead of ambient inheritance.

        Example Input Output:
            Input: `test_build_host_interaction_delegated_mounts_projects_attachment_scope()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        attachments = (
            HostInteractionAttachment(
                name="main",
                kind="workspace",
                source="/tmp/project",
                access_mode="read_write",
                mount_path="/workstation/mounts/main",
            ),
            HostInteractionAttachment(
                name="scratch",
                kind="scratch",
                source="/tmp/scratch",
                access_mode="read_write",
                mount_path="/workstation/scratch",
            ),
            HostInteractionAttachment(
                name="openai",
                kind="secret_ref",
                source="host:OPENAI_API_KEY",
                access_mode="indirect",
                mount_path="/workstation/secrets/openai",
            ),
        )

        delegated_mounts, granted, unsupported = build_host_interaction_delegated_mounts(
            attachments,
            granted_delegation=[
                {"capability": "ws.fs.read", "target": "main"},
                {"capability": "ws.fs.write", "target": "scratch"},
                {"capability": "ws.fs.read", "target": "openai"},
            ],
        )

        self.assertEqual(delegated_mounts["main"]["permissions"], ["list", "read"])
        self.assertEqual(delegated_mounts["scratch"]["permissions"], ["list", "write"])
        self.assertEqual(granted[0]["mount"], "main")
        self.assertEqual(granted[1]["mount"], "scratch")
        self.assertEqual(len(unsupported), 1)
        self.assertIn("does not support delegation", unsupported[0]["error"])

    def test_artifact_with_delegated_virtual_mounts_merges_permissions_and_rejects_conflicts(self) -> None:
        """
        High Level Purpose:
            In circumstances like shared nested-worker invocation, helps with verifying that delegated mounts merge into an invocation-scoped artifact view while conflicting roots are rejected.

        Reference to Theory:
            Verifies the shared host-interaction substrate by keeping delegated rights ephemeral and explicit without silently overriding the artifact's own mount declaration.

        Example Input Output:
            Input: `test_artifact_with_delegated_virtual_mounts_merges_permissions_and_rejects_conflicts()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        artifact = Artifact(
            id="artifact-demo",
            artifact_type=ArtifactType.ABILITY,
            title="Demo Artifact",
            representation=ArtifactRepresentation.PYTHON_SCRIPT,
            function_bit=1,
            scope="shared delegation test",
            provenance=["test"],
            reusability=ArtifactReuse.BROAD_REUSE,
            admissibility=ArtifactAdmission.ADMITTED,
            learning_relation=LearningRelation.NEW_FAMILY,
            related_artifact_ids=[],
            template_schema={},
            content={
                "virtual_mounts": {
                    "main": {
                        "root": "/tmp/project",
                        "permissions": ["read"],
                        "data_class": "public",
                    }
                }
            },
            justification="test",
            constraints=[],
        )

        merged = artifact_with_delegated_virtual_mounts(
            artifact,
            delegated_mounts={
                "main": {
                    "root": "/tmp/project",
                    "permissions": ["list"],
                    "data_class": "public",
                }
            },
        )
        self.assertEqual(
            merged.content["virtual_mounts"]["main"]["permissions"],
            ["list", "read"],
        )

        with self.assertRaises(ValueError):
            artifact_with_delegated_virtual_mounts(
                artifact,
                delegated_mounts={
                    "main": {
                        "root": "/tmp/other-project",
                        "permissions": ["list"],
                        "data_class": "public",
                    }
                },
            )
