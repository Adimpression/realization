from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from realized_core_conversation import (
    ConversationActivityStatus,
    ConversationReceipt,
    ConversationRecordKind,
    CoreConversationHost,
    NormalizedRequestRecord,
    PlanningProposalRecord,
    RenderingRecord,
    SQLiteConversationActivityJournal,
    StructuredResultRecord,
)
from realized_core_engine import EngineConfiguration
from realized_core_llm import (
    ConversationIdentityDisposition,
    ConversationOperation,
    ConversationPlanProposal,
    ConversationPlanningError,
    ConversationPlanningResult,
    ConversationRenderResult,
    CorrectionProposal,
    SemanticItemProposal,
)


class StaticPlanner:
    def __init__(self):
        self.calls = 0

    def propose(self, _context):
        self.calls += 1
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            ),
            receipt={"provider": "fake", "response_id": "planning-1"},
        )


class StaticRenderer:
    def __init__(self):
        self.calls = 0

    def render(self, _context):
        self.calls += 1
        return ConversationRenderResult(
            text="The Cedar brief is represented.",
            receipt={"provider": "fake", "response_id": "rendering-1"},
        )


class FailingPlanner:
    def propose(self, _context):
        raise TimeoutError("injected provider timeout")


class AmbiguousPlanner:
    def propose(self, _context):
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal(
                operation=None,
                unresolved_interpretation=(
                    "The contribution could start or continue an objective.",
                ),
            ),
            receipt={"provider": "fake", "response_id": "ambiguous-1"},
        )


class InvalidSemanticPlanner:
    def propose(self, _context):
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact"),
                ),
            ),
            receipt={
                "provider": "fake",
                "response_id": "planning-invalid-1",
                "elapsed_seconds": 0.25,
            },
        )


class InvalidControlPlanner:
    def propose(self, _context):
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                introduced_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            ),
            receipt={"provider": "fake", "response_id": "invalid-control-1"},
        )


class SelectorOnlyNonAchievedPlanner:
    def propose(self, _context):
        return ConversationPlanningResult(
            proposal=ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
                non_achieved_items=(
                    SemanticItemProposal("audience", "requirement"),
                ),
            ),
        )


class DuplicateCorrectionPlanner:
    def propose(self, context):
        if not context.has_causal_binding:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "blue"),
                ),
            )
        else:
            replacement = SemanticItemProposal("color", "fact", "green")
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.CORRECT,
                achieved_items=(replacement,),
                corrections=(
                    CorrectionProposal(
                        target_selector="color",
                        replacement=replacement,
                        rationale="The user changed the color.",
                    ),
                ),
            )
        return ConversationPlanningResult(proposal=proposal)


class SuspendAndResumePlanner:
    def propose(self, context):
        if not context.has_causal_binding:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience is undecided.",
                    ),
                ),
            )
        else:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.RESUME_SUSPENDED,
                achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "fact",
                        "city officials",
                    ),
                ),
                resolved_selectors=("audience",),
            )
        return ConversationPlanningResult(proposal=proposal)


class PauseThenAugmentPlanner:
    def propose(self, context):
        if not context.has_causal_binding:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience is undecided.",
                    ),
                ),
            )
        else:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.AUGMENT,
                non_achieved_items=(
                    SemanticItemProposal(
                        "budget",
                        "requirement",
                        text="A budget summary is required.",
                    ),
                ),
            )
        return ConversationPlanningResult(proposal=proposal)


class PauseThenRedirectPlanner:
    def propose(self, context):
        if not context.has_causal_binding:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                required_outcome="A brief with an identified audience",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "blue"),
                    SemanticItemProposal("deadline", "fact", "Friday"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience is undecided.",
                    ),
                ),
            )
        else:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.REDIRECT_AND_REALIGN,
                objective="Create the Cedar launch checklist",
                required_outcome="A complete launch checklist",
                affected_selectors=(
                    "project",
                    "color",
                    "deadline",
                    "audience",
                ),
                retained_selectors=("project",),
                unresolved_selectors=("color", "deadline", "audience"),
                identity_disposition=(
                    ConversationIdentityDisposition.SAME_OBJECTIVE
                ),
                rationale="The requested product changed from a brief to a checklist.",
            )
        return ConversationPlanningResult(proposal=proposal)


class StartThenExplainPlanner:
    def __init__(self) -> None:
        self.calls = 0

    def propose(self, context):
        self.calls += 1
        if not context.has_causal_binding:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.START,
                objective="Prepare the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            )
        else:
            proposal = ConversationPlanProposal(
                operation=ConversationOperation.EXPLAIN,
            )
        return ConversationPlanningResult(proposal=proposal)


class FailingRenderer:
    def render(self, _context):
        raise RuntimeError("injected rendering failure")


class AlternateRenderer:
    def __init__(self) -> None:
        self.calls = 0

    def render(self, _context):
        self.calls += 1
        return ConversationRenderResult(
            text="The same admitted Cedar result, phrased differently.",
            receipt={"provider": "fake", "response_id": "rerendering-1"},
        )


class ConversationPipelineTests(unittest.TestCase):
    def test_planning_failure_is_durable_but_creates_no_semantic_state(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        with self.assertRaisesRegex(TimeoutError, "provider timeout"):
            host.submit_text(
                "Prepare the Cedar brief.",
                planner=FailingPlanner(),
                idempotency_key="delivery-planning-failure",
            )

        assert host.journal is not None
        contribution = host.journal.find_contribution(
            idempotency_key="delivery-planning-failure"
        )
        assert contribution is not None
        records = host.journal.list_for_contribution(
            contribution.contribution_id
        )
        proposal = next(
            record
            for record in records
            if isinstance(record, PlanningProposalRecord)
        )
        self.assertEqual(ConversationActivityStatus.UNRESOLVED, proposal.status)
        self.assertEqual("TimeoutError", proposal.error["error_type"])
        self.assertFalse(
            any(
                isinstance(
                    record,
                    (NormalizedRequestRecord, StructuredResultRecord),
                )
                for record in records
            )
        )
        self.assertEqual((0, 0), self._semantic_counts(host.sqlite_path))

    def test_ambiguous_planning_is_not_admitted_as_a_best_guess(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        with self.assertRaisesRegex(
            ValueError,
            "could start or continue",
        ):
            host.submit_text(
                "Do that next.",
                planner=AmbiguousPlanner(),
                idempotency_key="delivery-ambiguous",
            )

        self.assertEqual((0, 0), self._semantic_counts(host.sqlite_path))
        self.assertEqual([], self._jsonl(host.root / "ENGINE_REQUESTS.jsonl"))

    def test_post_response_planning_failure_exposes_its_durable_receipt(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        with self.assertRaises(ConversationPlanningError) as raised:
            host.submit_text(
                "Prepare the Cedar brief.",
                planner=InvalidSemanticPlanner(),
                idempotency_key="delivery-invalid-semantic-plan",
            )

        self.assertIn("no value or text", str(raised.exception))
        self.assertEqual(
            "planning-invalid-1",
            raised.exception.provider_receipt["response_id"],
        )
        assert host.journal is not None
        contribution = host.journal.find_contribution(
            idempotency_key="delivery-invalid-semantic-plan"
        )
        assert contribution is not None
        proposal = next(
            record
            for record in host.journal.list_for_contribution(
                contribution.contribution_id
            )
            if isinstance(record, PlanningProposalRecord)
        )
        self.assertEqual(
            "planning-invalid-1",
            proposal.provider_receipt["response_id"],
        )
        self.assertEqual((0, 0), self._semantic_counts(host.sqlite_path))

    def test_inapplicable_control_fields_cannot_leak_into_execution(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        result = host.submit_text(
            "Prepare the Cedar brief.",
            planner=InvalidControlPlanner(),
        )

        self.assertEqual(
            ["introduced_items"],
            result["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_inapplicable_control_fields"
            ],
        )
        state = host.inspect_binding(str(result["run_id"]))
        self.assertEqual([], state["achieved"])
        self.assertFalse(
            any(
                item.get("payload", {}).get("semantic_key") == "project"
                for item in state["non_achievedness"]
            )
        )

    def test_correction_ignores_duplicate_direct_semantic_items(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )
        planner = DuplicateCorrectionPlanner()
        started = host.submit_text("Prepare Cedar.", planner=planner)

        corrected = host.submit_text(
            "Change blue to green.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        self.assertEqual(
            ["achieved_items"],
            corrected["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_inapplicable_control_fields"
            ],
        )
        state = host.inspect_binding(str(corrected["run_id"]))
        values = {
            item["payload"]["semantic_key"]: item["payload"].get("value")
            for item in state["achieved"]
            if item.get("payload", {}).get("semantic_key")
        }
        self.assertEqual("green", values["color"])

    def test_resume_suspended_resolves_the_supplied_requirement(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=EngineConfiguration(
                max_steps=24,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )
        planner = SuspendAndResumePlanner()
        started = host.submit_text("Prepare Cedar.", planner=planner)
        self.assertEqual("paused", started["run_outcome"])

        resumed = host.submit_text(
            "The audience is city officials.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = host.inspect_binding(str(resumed["run_id"]))
        achieved = {
            item["payload"].get("semantic_key"): item["payload"].get("value")
            for item in state["achieved"]
        }
        unresolved = {
            item["payload"].get("semantic_key")
            for item in state["non_achievedness"]
        }
        self.assertEqual("city officials", achieved["audience"])
        self.assertNotIn("audience", unresolved)

    def test_augmentation_can_extend_a_paused_reduction(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=EngineConfiguration(
                max_steps=24,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )
        planner = PauseThenAugmentPlanner()
        started = host.submit_text("Prepare Cedar.", planner=planner)
        self.assertEqual("paused", started["run_outcome"])

        augmented = host.submit_text(
            "Also require a budget summary.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = host.inspect_binding(str(augmented["run_id"]))
        unresolved = {
            item["payload"].get("semantic_key")
            for item in state["non_achievedness"]
            if item.get("payload", {}).get("semantic_key")
        }
        self.assertEqual({"audience", "budget"}, unresolved)

    def test_realignment_classifies_only_public_items_on_a_paused_reduction(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=EngineConfiguration(
                max_steps=24,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )
        planner = PauseThenRedirectPlanner()
        started = host.submit_text("Prepare Cedar.", planner=planner)
        self.assertEqual("paused", started["run_outcome"])

        redirected = host.submit_text(
            "Instead create a Cedar launch checklist.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )
        self.assertNotEqual("rejected", redirected["run_outcome"])
        self.assertNotEqual(started["run_id"], redirected["run_id"])

        state = host.inspect_binding(str(redirected["run_id"]))
        achieved = {
            item["payload"].get("semantic_key"): item["payload"].get("value")
            for item in state["achieved"]
            if item.get("payload", {}).get("semantic_key")
        }
        unresolved = {
            item["payload"].get("semantic_key")
            for item in state["non_achievedness"]
            if item.get("payload", {}).get("semantic_key")
        }
        self.assertEqual({"project": "Cedar"}, achieved)
        self.assertEqual({"color", "deadline", "audience"}, unresolved)
        self.assertEqual(
            "Create the Cedar launch checklist",
            state["governing_direction"]["objective"],
        )

    def test_selector_only_non_achieved_item_gets_deterministic_text(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        result = host.submit_text(
            "Prepare Cedar and ask for the undecided audience.",
            planner=SelectorOnlyNonAchievedPlanner(),
        )

        state = host.inspect_binding(str(result["run_id"]))
        audience = next(
            item
            for item in state["non_achievedness"]
            if item.get("payload", {}).get("semantic_key") == "audience"
        )
        self.assertEqual("audience is unresolved.", audience["payload"]["text"])

    def test_rendering_failure_cannot_undo_or_mutate_the_semantic_result(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )

        report = host.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=FailingRenderer(),
            idempotency_key="delivery-rendering-failure",
        )

        self.assertEqual("failed", report["rendering"]["status"])
        self.assertNotIn("injected rendering failure", report["assistant_text"])
        self.assertEqual((1, 1), self._semantic_counts(host.sqlite_path))
        assert host.journal is not None
        records = host.journal.list_for_contribution(
            report["contribution_id"]
        )
        result = next(
            record
            for record in records
            if isinstance(record, StructuredResultRecord)
        )
        rendering = next(
            record
            for record in records
            if isinstance(record, RenderingRecord)
        )
        self.assertEqual(report["result_id"], result.result_id)
        self.assertEqual(ConversationActivityStatus.FAILED, rendering.status)
        self.assertEqual("RuntimeError", rendering.error["error_type"])

    def test_transcript_discard_and_rerender_do_not_resubmit_semantic_work(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )
        initial = host.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=StaticRenderer(),
            idempotency_key="delivery-rerender",
        )
        state_before = host.inspect_binding(initial["run_id"])
        semantic_counts_before = self._semantic_counts(host.sqlite_path)

        discarded = host.discard_transcript()
        alternate = AlternateRenderer()
        rerendered = host.rerender_result(
            initial["result_id"],
            renderer=alternate,
            rendering_attempt_key="alternate-presentation",
        )
        recovered = host.rerender_result(
            initial["result_id"],
            renderer=FailingRenderer(),
            rendering_attempt_key="alternate-presentation",
        )

        self.assertEqual(2, discarded["discarded_message_count"])
        self.assertEqual([], self._jsonl(host.root / "MESSAGES.jsonl"))
        self.assertEqual("rendered", rerendered["status"])
        self.assertEqual("recovered", recovered["status"])
        self.assertEqual(1, alternate.calls)
        self.assertEqual(rerendered["presentation"], recovered["presentation"])
        self.assertEqual(state_before, host.inspect_binding(initial["run_id"]))
        self.assertEqual(
            semantic_counts_before,
            self._semantic_counts(host.sqlite_path),
        )

    def test_natural_language_pipeline_persists_stages_in_strict_order(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )

        report = host.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=StaticRenderer(),
            idempotency_key="delivery-1",
        )

        assert host.journal is not None
        records = host.journal.list_for_contribution(
            report["contribution_id"]
        )
        self.assertEqual(
            (
                "contribution",
                "receipt:planning_request",
                "proposal",
                "normalized_request",
                "receipt:engine_submission",
                "structured_result",
                "receipt:rendering_request",
                "rendering",
                "receipt:presentation_delivery",
            ),
            tuple(
                (
                    f"receipt:{record.stage}"
                    if isinstance(record, ConversationReceipt)
                    else record.KIND.value
                )
                for record in records
            ),
        )
        proposal = next(
            record
            for record in records
            if isinstance(record, PlanningProposalRecord)
        )
        request = next(
            record
            for record in records
            if isinstance(record, NormalizedRequestRecord)
        )
        result = next(
            record
            for record in records
            if isinstance(record, StructuredResultRecord)
        )
        rendering = next(
            record
            for record in records
            if isinstance(record, RenderingRecord)
        )
        self.assertEqual(ConversationActivityStatus.SUCCEEDED, proposal.status)
        self.assertEqual(report["normalized_request_id"], request.record_id)
        self.assertEqual(report["result_id"], result.record_id)
        self.assertEqual(report["rendering_attempt_id"], rendering.record_id)
        self.assertEqual(
            "The Cedar brief is represented.",
            rendering.presentation,
        )
        self.assertEqual(
            ConversationActivityStatus.PENDING,
            rendering.delivery_status,
        )
        self.assertEqual(
            ConversationRecordKind.STRUCTURED_RESULT,
            result.KIND,
        )

    def test_repeated_delivery_after_restart_reuses_every_durable_stage(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        first_planner = StaticPlanner()
        first_renderer = StaticRenderer()
        first = CoreConversationHost(root=root, configuration=configuration)

        initial = first.submit_text(
            "Prepare the Cedar brief.",
            planner=first_planner,
            renderer=first_renderer,
            idempotency_key="delivery-restart-1",
        )
        replacement_planner = StaticPlanner()
        replacement_renderer = StaticRenderer()
        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=replacement_planner,
            renderer=replacement_renderer,
            idempotency_key="delivery-restart-1",
        )

        self.assertEqual(1, first_planner.calls)
        self.assertEqual(1, first_renderer.calls)
        self.assertEqual(0, replacement_planner.calls)
        self.assertEqual(0, replacement_renderer.calls)
        self.assertEqual(initial["run_id"], recovered["run_id"])
        self.assertEqual(
            initial["normalized_request_id"],
            recovered["normalized_request_id"],
        )
        self.assertEqual(initial["result_id"], recovered["result_id"])
        self.assertEqual(
            initial["rendering_attempt_id"],
            recovered["rendering_attempt_id"],
        )
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    def test_distinct_contributions_can_share_one_normalized_read_request(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        host = CoreConversationHost(
            root=Path(temporary.name) / "conversation",
            configuration=self._configuration(),
        )
        planner = StartThenExplainPlanner()
        started = host.submit_text("Prepare Cedar.", planner=planner)
        renderer = StaticRenderer()

        first = host.submit_text(
            "Explain what remains unresolved.",
            planner=planner,
            renderer=renderer,
            parent_run_id=str(started["run_id"]),
        )
        second = host.submit_text(
            "Explain the current constraints.",
            planner=planner,
            renderer=renderer,
            parent_run_id=str(started["run_id"]),
        )

        self.assertEqual(
            first["normalized_request_id"],
            second["normalized_request_id"],
        )
        self.assertEqual(first["result_id"], second["result_id"])
        self.assertNotEqual(
            first["rendering_attempt_id"],
            second["rendering_attempt_id"],
        )
        self.assertEqual(2, renderer.calls)

    def test_recorded_proposal_replays_after_failure_before_engine_submission(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        planner = StaticPlanner()
        failing = _FailOnceJournal(
            root / "artifacts.sqlite3",
            lambda record: isinstance(record, NormalizedRequestRecord),
        )
        first = CoreConversationHost(
            root=root,
            configuration=configuration,
            journal=failing,
        )

        with self.assertRaisesRegex(RuntimeError, "injected journal failure"):
            first.submit_text(
                "Prepare the Cedar brief.",
                planner=planner,
                renderer=StaticRenderer(),
                idempotency_key="delivery-plan-boundary",
            )

        retry_planner = StaticPlanner()
        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=retry_planner,
            renderer=StaticRenderer(),
            idempotency_key="delivery-plan-boundary",
        )

        self.assertEqual(1, planner.calls)
        self.assertEqual(0, retry_planner.calls)
        self.assertTrue(recovered["run_id"])
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    def test_contribution_only_recovery_starts_planning_once(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        first = CoreConversationHost(root=root, configuration=configuration)
        first._accept_contribution(
            "Prepare the Cedar brief.",
            idempotency_key="delivery-contribution-boundary",
            parent_run_id="",
        )

        planner = StaticPlanner()
        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=planner,
            renderer=StaticRenderer(),
            idempotency_key="delivery-contribution-boundary",
        )

        self.assertEqual(1, planner.calls)
        self.assertTrue(recovered["run_id"])
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    def test_recovery_queries_engine_after_commit_before_local_result(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        failing = _FailOnceJournal(
            root / "artifacts.sqlite3",
            lambda record: isinstance(record, StructuredResultRecord),
        )
        first = CoreConversationHost(
            root=root,
            configuration=configuration,
            journal=failing,
        )

        with self.assertRaisesRegex(RuntimeError, "injected journal failure"):
            first.submit_text(
                "Prepare the Cedar brief.",
                planner=StaticPlanner(),
                renderer=StaticRenderer(),
                idempotency_key="delivery-result-boundary",
            )

        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=StaticRenderer(),
            idempotency_key="delivery-result-boundary",
        )

        self.assertTrue(recovered["result_id"])
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    def test_recovery_does_not_rerender_after_delivery_failure(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        renderer = StaticRenderer()
        failing = _FailOnceJournal(
            root / "artifacts.sqlite3",
            lambda record: (
                isinstance(record, ConversationReceipt)
                and record.stage == "presentation_delivery"
            ),
        )
        first = CoreConversationHost(
            root=root,
            configuration=configuration,
            journal=failing,
        )

        with self.assertRaisesRegex(RuntimeError, "injected journal failure"):
            first.submit_text(
                "Prepare the Cedar brief.",
                planner=StaticPlanner(),
                renderer=renderer,
                idempotency_key="delivery-presentation-boundary",
            )

        retry_renderer = StaticRenderer()
        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=retry_renderer,
            idempotency_key="delivery-presentation-boundary",
        )

        self.assertEqual(1, renderer.calls)
        self.assertEqual(0, retry_renderer.calls)
        self.assertEqual(
            "The Cedar brief is represented.",
            recovered["assistant_text"],
        )
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    def test_recovery_rerenders_without_resubmission_when_render_record_was_lost(
        self,
    ) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "conversation"
        configuration = self._configuration()
        first_renderer = StaticRenderer()
        failing = _FailOnceJournal(
            root / "artifacts.sqlite3",
            lambda record: isinstance(record, RenderingRecord),
        )
        first = CoreConversationHost(
            root=root,
            configuration=configuration,
            journal=failing,
        )

        with self.assertRaisesRegex(RuntimeError, "injected journal failure"):
            first.submit_text(
                "Prepare the Cedar brief.",
                planner=StaticPlanner(),
                renderer=first_renderer,
                idempotency_key="delivery-render-boundary",
            )

        retry_renderer = StaticRenderer()
        replacement = CoreConversationHost(
            root=root,
            configuration=configuration,
        )
        recovered = replacement.submit_text(
            "Prepare the Cedar brief.",
            planner=StaticPlanner(),
            renderer=retry_renderer,
            idempotency_key="delivery-render-boundary",
        )

        self.assertEqual(1, first_renderer.calls)
        self.assertEqual(1, retry_renderer.calls)
        self.assertEqual(
            "The Cedar brief is represented.",
            recovered["assistant_text"],
        )
        self.assertEqual((1, 1), self._semantic_counts(replacement.sqlite_path))

    @staticmethod
    def _configuration() -> EngineConfiguration:
        return EngineConfiguration(
            max_steps=0,
            llm_policy="off",
            discovery="off",
            reflection="off",
            contemplation="off",
        )

    @staticmethod
    def _semantic_counts(sqlite_path: Path) -> tuple[int, int]:
        with closing(sqlite3.connect(sqlite_path)) as connection:
            attempts = connection.execute(
                "SELECT COUNT(*) FROM resumption_attempts"
            ).fetchone()[0]
            revisions = connection.execute(
                "SELECT COUNT(*) FROM resumption_revisions"
            ).fetchone()[0]
        return int(attempts), int(revisions)

    @staticmethod
    def _jsonl(path: Path) -> list[dict[str, object]]:
        if not path.is_file():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class _FailOnceJournal(SQLiteConversationActivityJournal):
    def __init__(self, sqlite_path: Path, predicate) -> None:
        super().__init__(sqlite_path)
        self._predicate = predicate
        self._failed = False

    def put(self, record):
        if not self._failed and self._predicate(record):
            self._failed = True
            raise RuntimeError("injected journal failure")
        return super().put(record)


if __name__ == "__main__":
    unittest.main()
