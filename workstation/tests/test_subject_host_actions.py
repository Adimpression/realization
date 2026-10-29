# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from realized_core_semantics.proposals import ProposalType, SupplementMode
from controller_entrypoints import ensure_application_controller_runtime
from learning_context import new_learning_context, persist_learning_context
from workstation.foundation.host.subject_workflow import create_subject_workflow_client
from workstation.app.cli.composition import (
    ApplicationControllerRuntimeProvider as _ApplicationControllerRuntimeProvider,
)
from workstation.foundation.projections import WorkstationActionResultView
from workstation.runtime.core.subject_host_actions import RuntimeSubjectWorkflowHostActions
from workstation.subject.core.host_actions import (
    SubjectHostActionResult,
    SubjectItemizationProposal,
    SubjectWorkflowHostActionUnavailable,
    UnavailableSubjectWorkflowHostActions,
)
from workstation.subject.service.subject_workflow_api import SubjectWorkflowApiService


class SubjectHostActionBoundaryTests(unittest.TestCase):
    def test_unavailable_port_is_fail_closed(self) -> None:
        port = UnavailableSubjectWorkflowHostActions()

        self.assertFalse(port.allows_direct_llm_decomposition(root_path=Path(".")))
        self.assertEqual(
            port.import_staged_source(
                root_path=Path("."),
                subject_id="subject-a",
                staged_source_id="source-a",
            ).status,
            "unavailable",
        )
        with self.assertRaises(SubjectWorkflowHostActionUnavailable):
            port.preview_assistant_markdown(
                root_path=Path("."),
                markdown_text="# Subject",
                command_text="/start-research",
                subject_title_override="",
            )
        with self.assertRaisesRegex(
            SubjectWorkflowHostActionUnavailable,
            "request_itemization_proposal",
        ):
            port.request_itemization_proposal(
                semantic_unit="Itemize source prose",
                llm_policy="auto",
                target_scope="itemize:subject-a:source-a",
                instructions="Return candidates.",
                fallback_payload={"candidates": []},
                schema_hint={"candidates": []},
            )
        with self.assertRaisesRegex(
            SubjectWorkflowHostActionUnavailable,
            "bootstrap_decision_support_controller",
        ):
            port.bootstrap_decision_support_controller(
                semantic_unit="Decide the route",
                llm_policy="off",
                subject_scope=None,
                subject_scope_root_path=None,
            )

    def test_runtime_adapter_preserves_the_neutral_result_contract(self) -> None:
        runtime_result = WorkstationActionResultView(
            action_kind="stage_markdown_source",
            status="ok",
            title="Stage Markdown Source",
            message="Source staged.",
            details=("Subject id: subject-a",),
            payload={"subject_id": "subject-a", "staged_source_id": "source-a"},
        )
        adapter = RuntimeSubjectWorkflowHostActions()

        with mock.patch(
            "workstation.runtime.core.subject_host_actions.workstation_stage_markdown_source_action",
            return_value=runtime_result,
        ) as stage:
            result = adapter.stage_markdown_source(
                root_path=Path("/tmp/workstation-root"),
                markdown_path=Path("/tmp/source.md"),
                subject_id="subject-a",
                subject_title="Subject A",
            )

        self.assertEqual(
            result,
            SubjectHostActionResult(
                status="ok",
                message="Source staged.",
                details=("Subject id: subject-a",),
                payload={"subject_id": "subject-a", "staged_source_id": "source-a"},
            ),
        )
        stage.assert_called_once_with(
            root_path=Path("/tmp/workstation-root"),
            markdown_path=Path("/tmp/source.md"),
            subject_id="subject-a",
            subject_title="Subject A",
        )

    def test_runtime_adapter_reads_session_policy_without_exposing_session_to_subject_core(self) -> None:
        adapter = RuntimeSubjectWorkflowHostActions()

        with mock.patch(
            "workstation.runtime.core.subject_host_actions.load_workstation_session",
            return_value=SimpleNamespace(allow_direct_llm_decomposition=True),
        ):
            self.assertTrue(adapter.allows_direct_llm_decomposition(root_path=Path("/tmp/root")))

    def test_runtime_adapter_composes_skill_materialization_only_for_capture(self) -> None:
        adapter = RuntimeSubjectWorkflowHostActions()
        materialize = mock.Mock(return_value=())
        provider = SimpleNamespace(materialize_learning_context_skills=materialize)
        preview_payload = {"status": "preview"}
        capture_payload = {"status": "captured"}

        with (
            mock.patch(
                "workstation.runtime.core.subject_host_actions.preview_workstation_assistant_markdown_for_research",
                return_value=preview_payload,
            ) as preview,
            mock.patch(
                "workstation.runtime.core.subject_host_actions.capture_workstation_assistant_markdown_for_research",
                return_value=capture_payload,
            ) as capture,
            mock.patch(
                "workstation.runtime.core.subject_host_actions.skill_exchange_provider",
                return_value=provider,
            ) as exchange_provider,
        ):
            self.assertEqual(
                preview_payload,
                adapter.preview_assistant_markdown(
                    root_path=Path("/tmp/root"),
                    markdown_text="# Subject",
                    command_text="/start-research",
                    subject_title_override="",
                ),
            )
            self.assertEqual(
                capture_payload,
                adapter.capture_assistant_markdown(
                    root_path=Path("/tmp/root"),
                    markdown_text="# Subject",
                    command_text="/start-research",
                    subject_title_override="",
                ),
            )

        preview.assert_called_once_with(
            root_path=Path("/tmp/root"),
            markdown_text="# Subject",
            command_text="/start-research",
            subject_title_override="",
        )
        exchange_provider.assert_called_once_with()
        capture.assert_called_once_with(
            root_path=Path("/tmp/root"),
            markdown_text="# Subject",
            command_text="/start-research",
            subject_title_override="",
            skill_materializer=materialize,
        )

    def test_runtime_adapter_maps_itemization_proposal_without_exposing_controller(self) -> None:
        adapter = RuntimeSubjectWorkflowHostActions()
        proposal = SimpleNamespace(
            id="proposal-itemize-a",
            source="provider-a",
            payload={"candidates": [{"canonical_label": "Candidate A"}]},
        )
        controller = SimpleNamespace(request_proposal=mock.Mock(return_value=proposal))
        provider = SimpleNamespace(
            bootstrap_controller=mock.Mock(return_value=(object(), controller))
        )

        with mock.patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=provider,
        ):
            result = adapter.request_itemization_proposal(
                semantic_unit="Itemize source prose",
                llm_policy="auto",
                target_scope="itemize:subject-a:source-a",
                instructions="Return candidates.",
                fallback_payload={"candidates": []},
                schema_hint={"candidates": [{"canonical_label": "Candidate A"}]},
            )

        self.assertEqual(
            result,
            SubjectItemizationProposal(
                proposal_id="proposal-itemize-a",
                source="provider-a",
                payload={"candidates": [{"canonical_label": "Candidate A"}]},
            ),
        )
        provider.bootstrap_controller.assert_called_once_with(
            semantic_unit="Itemize source prose",
            llm_policy="auto",
        )
        controller.request_proposal.assert_called_once_with(
            proposal_type=ProposalType.NOT_DECOMPOSITION,
            node=None,
            target_scope="itemize:subject-a:source-a",
            instructions="Return candidates.",
            fallback_payload={"candidates": []},
            mode=SupplementMode.DEEP,
            schema_hint={"candidates": [{"canonical_label": "Candidate A"}]},
        )

    def test_runtime_adapter_realizes_decision_support_bootstrap_with_exact_inputs(self) -> None:
        adapter = RuntimeSubjectWorkflowHostActions()
        state = object()
        controller = object()
        provider = SimpleNamespace(
            bootstrap_controller=mock.Mock(return_value=(state, controller))
        )

        with mock.patch(
            "workstation.runtime.core.subject_host_actions.controller_runtime_provider",
            return_value=provider,
        ):
            result = adapter.bootstrap_decision_support_controller(
                semantic_unit="Choose a safe transition",
                llm_policy="off",
                subject_scope={"subject_id": "subject-a"},
                subject_scope_root_path=Path("/tmp/workstation-root"),
            )

        self.assertEqual(result, (state, controller))
        provider.bootstrap_controller.assert_called_once_with(
            semantic_unit="Choose a safe transition",
            llm_policy="off",
            subject_scope={"subject_id": "subject-a"},
            subject_scope_root_path=Path("/tmp/workstation-root"),
        )

    def test_subject_service_forwards_host_only_actions_through_the_injected_port(self) -> None:
        class UrlHostActions:
            def __init__(self) -> None:
                self.calls: list[dict[str, object]] = []

            def learn_url(self, **kwargs: object) -> SubjectHostActionResult:
                self.calls.append(dict(kwargs))
                return SubjectHostActionResult(status="error", message="Sentinel URL failure.")

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            context = new_learning_context(canonical_title="Subject A")
            persist_learning_context(root, context)
            host_actions = UrlHostActions()
            service = SubjectWorkflowApiService(host_actions=host_actions)  # type: ignore[arg-type]

            outcome = service.apply_action(
                root_path=root,
                subject_id=context.subject_id,
                phase="research",
                action_key="use_url_ingress",
                assistant_message_text="https://example.test/source",
            )

        self.assertEqual(outcome.status_text, "Sentinel URL failure.")
        self.assertEqual(len(host_actions.calls), 1)
        self.assertEqual(host_actions.calls[0]["source_url"], "https://example.test/source")
        self.assertEqual(host_actions.calls[0]["subject_id"], context.subject_id)

    def test_application_composition_injects_the_runtime_adapter(self) -> None:
        ensure_application_controller_runtime()

        client = create_subject_workflow_client()

        self.assertIsInstance(client.service.host_actions, RuntimeSubjectWorkflowHostActions)

    def test_application_controller_provider_forwards_subject_scope_to_root_bootstrap(self) -> None:
        provider = _ApplicationControllerRuntimeProvider()
        state = object()
        controller = object()

        with mock.patch(
            "workstation.app.cli.composition.bootstrap_runtime_controller",
            return_value=(state, controller),
        ) as bootstrap:
            result = provider.bootstrap_controller(
                semantic_unit="Choose a safe transition",
                llm_policy="off",
                subject_scope={"active_subject_id": "subject-a"},
                subject_scope_root_path=Path("/tmp/workstation-root"),
            )

        self.assertEqual(result, (state, controller))
        bootstrap.assert_called_once_with(
            semantic_unit="Choose a safe transition",
            llm_policy="off",
            subject_scope={"active_subject_id": "subject-a"},
            subject_scope_root_path=Path("/tmp/workstation-root"),
        )


if __name__ == "__main__":
    unittest.main()
