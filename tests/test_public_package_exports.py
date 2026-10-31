from __future__ import annotations

import importlib
import unittest


class PublicPackageExportTests(unittest.TestCase):
    def assert_exports_identical(
        self,
        *,
        package_name: str,
        expected_by_module: dict[str, tuple[str, ...]],
    ) -> None:
        package = importlib.import_module(package_name)
        expected = {
            name
            for names in expected_by_module.values()
            for name in names
        }
        self.assertEqual(expected, set(package.__all__))
        for module_name, names in expected_by_module.items():
            source = importlib.import_module(module_name)
            for name in names:
                self.assertIs(getattr(package, name), getattr(source, name), name)

    def test_data_governance_facade_exports_only_canonical_public_api(self) -> None:
        self.assert_exports_identical(
            package_name="data_governance",
            expected_by_module={
                "realized_core_governance.data": (
                    "DATA_CLASS_CHOICES",
                    "allowed_data_classes_from_governance_context",
                    "ensure_governed_data_access",
                    "normalize_data_class",
                    "normalize_data_class_list",
                    "normalize_named_query_registry",
                    "query_is_read_only",
                ),
            },
        )

    def test_workstation_compatibility_exports_only_its_supported_module_list(self) -> None:
        package = importlib.import_module("workstation.compatibility")

        self.assertEqual({"SUPPORTED_MODULES"}, set(package.__all__))
        self.assertEqual(
            (
                "workstation.foundation.events.subscriber_controllers",
                "workstation.foundation.host.client_sessions",
                "workstation.foundation.host.learning_capture",
                "workstation.foundation.host.llm_driver",
                "workstation.shell.core.shell_prompt_routing",
            ),
            package.SUPPORTED_MODULES,
        )

    def test_application_cli_exports_only_entry_api(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.app.cli",
            expected_by_module={
                "workstation.app.cli": ("cli",),
                "workstation.app.cli.cli": (
                    "handle_workstation_chat_command",
                    "handle_workstation_grpc_host_command",
                    "handle_workstation_launch_command",
                    "handle_workstation_prompt_command",
                    "handle_workstation_skill_catalog_command",
                    "handle_workstation_skill_export_command",
                    "handle_workstation_skill_import_command",
                    "handle_workstation_trial_validate_command",
                    "main",
                    "run_workstation_chat_loop",
                ),
            },
        )
        package = importlib.import_module("workstation.app.cli")
        runtime_controller = importlib.import_module(
            "workstation.app.cli.runtime_controller"
        )
        self.assertIs(package.runtime_controller, runtime_controller)
        self.assertNotIn("json", package.__all__)
        self.assertNotIn("Path", package.__all__)

    def test_foundation_models_export_only_owned_values(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.foundation.models",
            expected_by_module={
                "workstation.foundation.models.models": (
                    "TaskBoundaryContract",
                    "WorkstationAttachment",
                    "WorkstationDelegationEscalationDecision",
                    "WorkstationDelegationEscalationRequest",
                    "WorkstationSession",
                ),
            },
        )

    def test_foundation_projections_export_only_owned_views_and_renderers(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.foundation.projections",
            expected_by_module={
                "workstation.foundation.projections.projection_models": (
                    "WorkstationActionResultView",
                    "WorkstationActivityEventView",
                    "WorkstationActivityFeedView",
                    "WorkstationChatMessageView",
                    "WorkstationChatTranscriptView",
                    "WorkstationOperatorDetailView",
                    "WorkstationOperatorSummaryEntryView",
                    "WorkstationOperatorSummaryListView",
                    "WorkstationPermissionEntryView",
                    "WorkstationPermissionPanelView",
                    "WorkstationSkillCatalogEntryView",
                    "WorkstationSkillCatalogView",
                    "WorkstationSkillDescriptorView",
                    "WorkstationSkillFieldView",
                    "WorkstationSkillFormSectionView",
                    "WorkstationSkillInputFormView",
                    "WorkstationWorkflowEdgeView",
                    "WorkstationWorkflowGraphView",
                    "WorkstationWorkflowNodeView",
                    "WorkstationWorkflowSummaryEntryView",
                    "WorkstationWorkflowSummaryListView",
                    "WorkstationWorkflowTimelineEntryView",
                    "WorkstationWorkflowTimelineView",
                    "annotate_workstation_activity_events",
                    "render_workstation_activity_event",
                    "render_workstation_activity_feed",
                    "render_workstation_permission_panel",
                    "render_workstation_skill_catalog",
                    "render_workstation_skill_descriptor",
                    "split_rendered_workstation_activity_line",
                    "workstation_permission_panel_view",
                    "workstation_workflow_graph_view",
                ),
                "workstation.foundation.projections.activity_receipts": (
                    "render_workstation_activity_line",
                    "workstation_activity_event_view",
                ),
            },
        )

    def test_builtin_skills_export_only_builtin_catalog_api(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.skills.builtin",
            expected_by_module={
                "workstation.skills.builtin.builtin_skills": (
                    "builtin_workstation_skill_artifacts",
                    "builtin_workstation_skill_documents",
                    "resolve_builtin_workstation_skill",
                ),
            },
        )

    def test_subject_textual_exports_only_projection_backend(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.subject.textual",
            expected_by_module={
                "workstation.subject.textual.subject_workflow_textual_backend": (
                    "TextualSubjectWorkflowProjectionBackend",
                ),
            },
        )

    def test_textual_ui_exports_only_owned_application_api(self) -> None:
        self.assert_exports_identical(
            package_name="workstation.ui.textual",
            expected_by_module={
                "workstation.ui.textual.chat_ui": (
                    "TEXTUAL_CHAT_CSS",
                    "configure_textual_subject_workflow_client_factory",
                    "format_chat_timestamp_epoch_ms",
                    "prompt_for_workstation_escalation_enhanced",
                    "run_enhanced_workstation_chat_loop",
                    "workstation_chat_activity_strip_text",
                    "workstation_chat_apply_prompt_suggestion",
                    "workstation_chat_assistant_block_text",
                    "workstation_chat_banner",
                    "workstation_chat_completion_candidates",
                    "workstation_chat_context",
                    "workstation_chat_help_text",
                    "workstation_chat_history_path",
                    "workstation_chat_inline_completion",
                    "workstation_chat_live_suggestions",
                    "workstation_chat_named_block_text",
                    "workstation_chat_prepare_last_assistant_resolution",
                    "workstation_chat_prepare_last_assistant_routed_text",
                    "workstation_chat_prepare_markdown_prompt",
                    "workstation_chat_prompt_target_plan",
                    "workstation_chat_prompt_target_plan_via_shell",
                    "workstation_chat_research_capture_text",
                    "workstation_chat_research_preview_text",
                    "workstation_chat_resume_research_prompt",
                    "workstation_chat_routed_llm_prompt_text",
                    "workstation_chat_suggestions",
                    "workstation_chat_ui_supported",
                ),
            },
        )
        package = importlib.import_module("workstation.ui.textual")
        self.assertNotIn("TextualButton", package.__all__)
        self.assertNotIn("Application", package.__all__)


if __name__ == "__main__":
    unittest.main()
