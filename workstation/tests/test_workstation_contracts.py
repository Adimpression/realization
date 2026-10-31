from __future__ import annotations

import importlib
import pickle
import unittest
from pathlib import Path
from unittest.mock import patch

import grpc

import workstation.contracts as contracts
from workstation.contracts.events import WorkstationEvent
from workstation.contracts.runtime import (
    ArtifactRepository,
    ArtifactRepositoryProvider,
    SkillExchangeProvider,
)
from workstation.contracts.shell import (
    WorkstationChatContext,
    WorkstationChatMessageView,
    WorkstationChatPromptTargetPlan,
    WorkstationShellClient,
    WorkstationShellTextView,
)
from workstation.contracts.shell_prompt_routing import (
    match_workstation_shell_utility_prompt,
)
from workstation.contracts.subject import (
    SubjectImportStaging,
    SubjectWorkflowClient,
    SubjectWorkflowOptionView,
)
from workstation.shell.core.workstation_shell_client import (
    GrpcWorkstationShellClient,
    InProcessWorkstationShellClient,
)
from workstation.subject.service.subject_workflow_client import (
    GrpcSubjectWorkflowClient,
    InProcessSubjectWorkflowClient,
)


class WorkstationContractSurfaceTest(unittest.TestCase):
    def test_root_contract_surface_is_explicit_and_importable(self) -> None:
        expected = {
            "ArtifactRepository",
            "ArtifactRepositoryProvider",
            "ControllerRuntimeProvider",
            "GovernedTurnRuntimeProvider",
            "HostAwareControllerRuntimeProvider",
            "SkillExchangeProvider",
            "GovernedTurnLlmPolicy",
            "GovernedTurnRequest",
            "GovernedTurnResult",
            "GovernedTurnTreatment",
            "SubjectImportStaging",
            "SubjectWorkflowActionOutcomeView",
            "SubjectWorkflowActionSpecView",
            "SubjectWorkflowClient",
            "SubjectWorkflowControlBundleView",
            "SubjectWorkflowCurrentStepView",
            "SubjectWorkflowGateActionView",
            "SubjectWorkflowKeyValueRowView",
            "SubjectWorkflowOptionView",
            "SubjectWorkflowPaneBundleView",
            "SubjectWorkflowPaneItemView",
            "SubjectWorkflowPaneView",
            "SubjectWorkflowPhaseView",
            "SubjectWorkflowScenarioView",
            "SubjectWorkflowSelectionListSpecView",
            "SubjectWorkflowSelectionOptionView",
            "SubjectWorkflowSelectSpecView",
            "SubjectWorkflowSnapshotView",
            "SubjectWorkflowStatusView",
            "SubjectWorkflowSwitchSpecView",
            "SubjectWorkflowTableSpecView",
            "SubjectWorkflowTextSectionView",
            "SubjectWorkflowWatchEventView",
            "WorkstationArtifactRefView",
            "WorkstationChatContext",
            "WorkstationChatMessageView",
            "WorkstationChatPromptTargetPlan",
            "WorkstationChatSnapshotView",
            "WorkstationEvent",
            "WorkstationPreparedChatPromptTargetView",
            "WorkstationShellClient",
            "WorkstationShellTextView",
            "WorkstationShellWatchEventView",
            "WorkstationSubmitChatInputResultView",
            "match_workstation_shell_utility_prompt",
        }

        self.assertEqual(expected, set(contracts.__all__))
        for name in contracts.__all__:
            self.assertTrue(hasattr(contracts, name), name)

    def test_artifact_repository_provider_is_an_explicit_composition_port(self) -> None:
        from workstation.foundation.host import artifact_repository as binding

        class Repository:
            def describe(self):
                return {}

            def persist(self, state):
                return {}

            def persist_artifact(self, artifact, *, run_id="artifact_import"):
                return {}

            def persist_artifacts(self, artifacts, *, run_id="artifact_import"):
                return {}

            def load_all_artifacts(self):
                return []

            def load_relevant_artifacts(self, query_text, *, limit=8):
                return []

            def load_recent_artifacts(self, *, limit=512):
                return []

        repository = Repository()

        class Provider:
            def open_artifact_repository(self, *, sqlite_path, vector_mode=None):
                return repository

        provider = Provider()
        self.assertIsInstance(repository, ArtifactRepository)
        self.assertIsInstance(provider, ArtifactRepositoryProvider)
        with patch.object(binding, "_provider", None):
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                binding.artifact_repository_provider()
            binding.register_artifact_repository_provider(provider)
            self.assertIs(binding.artifact_repository_provider(), provider)

    def test_skill_exchange_provider_is_an_explicit_composition_port(self) -> None:
        from workstation.foundation.host import skill_exchange as binding

        class Provider:
            def artifact_from_skill_document(self, document):
                return document

            def load_import_payload_documents(self, source_file):
                return []

            def export_skill_bundle_text(self, artifacts):
                return ""

            def normalized_skill_bundle_filename_for_source(self, path):
                return "skill.yaml"

            def batch_skill_export_filename(self, artifact):
                return "skill.yaml"

            def materialize_learning_context_skills(self, root_path, context):
                return ()

        provider = Provider()
        self.assertIsInstance(provider, SkillExchangeProvider)
        with patch.object(binding, "_provider", None):
            with self.assertRaisesRegex(RuntimeError, "not configured"):
                binding.skill_exchange_provider()
            binding.register_skill_exchange_provider(provider)
            self.assertIs(binding.skill_exchange_provider(), provider)

    def test_legacy_event_and_subject_symbols_are_identical(self) -> None:
        legacy_event = importlib.import_module(
            "workstation.foundation.events.event_bus"
        )
        legacy_subject_core = importlib.import_module(
            "workstation.subject.core.subject_workflow"
        )
        legacy_subject_api = importlib.import_module(
            "workstation.subject.service.subject_workflow_api"
        )
        legacy_subject_client = importlib.import_module(
            "workstation.subject.service.subject_workflow_client"
        )

        self.assertIs(WorkstationEvent, legacy_event.WorkstationEvent)
        self.assertIs(SubjectImportStaging, legacy_subject_core.SubjectImportStaging)
        self.assertIs(
            SubjectWorkflowOptionView,
            legacy_subject_api.SubjectWorkflowOptionView,
        )
        self.assertIs(
            SubjectWorkflowClient,
            legacy_subject_client.SubjectWorkflowClient,
        )

    def test_legacy_shell_symbols_are_identical(self) -> None:
        legacy_chat = importlib.import_module("workstation.shell.core.chat_shell")
        legacy_projection = importlib.import_module(
            "workstation.foundation.projections.projection_models"
        )
        legacy_shell_api = importlib.import_module(
            "workstation.shell.core.workstation_shell_api"
        )
        legacy_shell_client = importlib.import_module(
            "workstation.shell.core.workstation_shell_client"
        )

        self.assertIs(WorkstationChatContext, legacy_chat.WorkstationChatContext)
        self.assertIs(
            WorkstationChatPromptTargetPlan,
            legacy_chat.WorkstationChatPromptTargetPlan,
        )
        self.assertIs(
            WorkstationChatMessageView,
            legacy_projection.WorkstationChatMessageView,
        )
        self.assertIs(
            WorkstationShellTextView,
            legacy_shell_api.WorkstationShellTextView,
        )
        self.assertIs(
            WorkstationShellClient,
            legacy_shell_client.WorkstationShellClient,
        )

    def test_historical_module_names_remain_stable(self) -> None:
        self.assertEqual(
            "workstation.foundation.events.event_bus",
            WorkstationEvent.__module__,
        )
        self.assertEqual(
            "workstation.subject.core.subject_workflow",
            SubjectImportStaging.__module__,
        )
        self.assertEqual(
            "workstation.subject.service.subject_workflow_api",
            SubjectWorkflowOptionView.__module__,
        )
        self.assertEqual(
            "workstation.shell.core.chat_shell",
            WorkstationChatContext.__module__,
        )
        self.assertEqual(
            "workstation.foundation.projections.projection_models",
            WorkstationChatMessageView.__module__,
        )

    def test_representative_legacy_pickles_round_trip(self) -> None:
        values = (
            WorkstationEvent(
                kind="subject.changed",
                session_id="session-1",
                root_path="/tmp/workstation",
                timestamp="2026-10-06T00:00:00Z",
                payload={"subject_id": "subject-1"},
                trace_id="trace-1",
                parent_id="parent-1",
            ),
            SubjectImportStaging(
                source_subject_id="subject-1",
                source_subject_title="Subject One",
            ),
            SubjectWorkflowOptionView(label="Summary", value="summary"),
            WorkstationChatContext(
                root=Path("/tmp/workstation"),
                workspace_root=Path("/tmp/workstation/workspace"),
                skill_titles=("Research",),
                builtin_skill_titles=("Research",),
                imported_skill_titles=(),
                subject_titles=("Subject One",),
                workspace_paths=("report.md",),
                allowed_capabilities=("ws.subject.read",),
            ),
            WorkstationChatMessageView(
                role="assistant",
                content="Ready.",
                timestamp_epoch_ms=1,
            ),
            WorkstationShellTextView(
                text="Ready.",
                snapshot_version="snapshot-1",
                progress_fingerprint="fingerprint-1",
            ),
        )

        for value in values:
            with self.subTest(value_type=type(value).__name__):
                restored = pickle.loads(pickle.dumps(value))
                self.assertIs(type(value), type(restored))
                self.assertEqual(value, restored)


class WorkstationCompatibilityAdapterTest(unittest.TestCase):
    def test_moved_implementation_modules_are_true_aliases(self) -> None:
        module_pairs = (
            (
                "workstation.foundation.events.subscriber_controllers",
                "workstation.runtime.core.projection_subscriber_controller",
            ),
            (
                "workstation.foundation.host.client_sessions",
                "workstation.subject.service.client_sessions",
            ),
            (
                "workstation.foundation.host.learning_capture",
                "workstation.subject.service.learning_capture",
            ),
            (
                "workstation.foundation.host.llm_driver",
                "workstation.runtime.core.llm_driver",
            ),
            (
                "workstation.shell.core.shell_prompt_routing",
                "workstation.contracts.shell_prompt_routing",
            ),
        )

        for legacy_name, canonical_name in module_pairs:
            with self.subTest(legacy_name=legacy_name):
                self.assertIs(
                    importlib.import_module(legacy_name),
                    importlib.import_module(canonical_name),
                )

    def test_package_alias_qualified_name_obligations_are_explicit(self) -> None:
        subscriber = importlib.import_module(
            "workstation.runtime.core.projection_subscriber_controller"
        )
        sessions = importlib.import_module(
            "workstation.subject.service.client_sessions"
        )
        llm_driver = importlib.import_module("workstation.runtime.core.llm_driver")
        prompt_routing = importlib.import_module(
            "workstation.contracts.shell_prompt_routing"
        )
        learning_capture = importlib.import_module(
            "workstation.subject.service.learning_capture"
        )

        historical_identities = (
            (
                subscriber.WorkstationProjectionSubscriberController,
                "workstation.foundation.events.subscriber_controllers",
            ),
            (
                sessions.WorkstationClientSessionRegistry,
                "workstation.foundation.host.client_sessions",
            ),
            (
                llm_driver.run_workstation_openai_turn,
                "workstation.foundation.host.llm_driver",
            ),
            (
                prompt_routing.match_workstation_shell_utility_prompt,
                "workstation.shell.core.shell_prompt_routing",
            ),
        )
        for value, historical_module in historical_identities:
            with self.subTest(value=value):
                self.assertEqual(historical_module, value.__module__)
                self.assertIs(value, pickle.loads(pickle.dumps(value, protocol=0)))

        canonical_learning_module = "workstation.subject.service.learning_capture"
        for name in (
            "capture_workstation_assistant_markdown_for_research",
            "capture_workstation_chat_learning_from_tool_receipts",
            "preview_workstation_assistant_markdown_for_research",
        ):
            with self.subTest(name=name):
                value = getattr(learning_capture, name)
                self.assertEqual(canonical_learning_module, value.__module__)
                self.assertIs(value, pickle.loads(pickle.dumps(value, protocol=0)))

    def test_in_process_adapters_satisfy_contracts(self) -> None:
        self.assertIsInstance(InProcessSubjectWorkflowClient(), SubjectWorkflowClient)
        self.assertIsInstance(InProcessWorkstationShellClient(), WorkstationShellClient)

    def test_grpc_adapters_satisfy_contracts_without_connecting(self) -> None:
        subject_channel = grpc.insecure_channel("127.0.0.1:1")
        shell_channel = grpc.insecure_channel("127.0.0.1:1")
        self.addCleanup(subject_channel.close)
        self.addCleanup(shell_channel.close)

        self.assertIsInstance(
            GrpcSubjectWorkflowClient(subject_channel),
            SubjectWorkflowClient,
        )
        self.assertIsInstance(
            GrpcWorkstationShellClient(shell_channel),
            WorkstationShellClient,
        )

    def test_legacy_and_contract_prompt_routing_are_identical(self) -> None:
        legacy_routing = importlib.import_module(
            "workstation.shell.core.shell_prompt_routing"
        )
        prompt = "Import the skill file at /tmp/research.md into this workstation."

        self.assertIs(
            match_workstation_shell_utility_prompt,
            legacy_routing.match_workstation_shell_utility_prompt,
        )
        self.assertEqual(
            {
                "command_text": "/import-skill /tmp/research.md",
                "capability": "ws.skill.import",
            },
            match_workstation_shell_utility_prompt(prompt),
        )


if __name__ == "__main__":
    unittest.main()
