from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from realized_core.chat import CoreConversationHost
from realized_core.planning import (
    AdvisoryJsonResult,
    ConversationIdentityDisposition,
    ConversationPlanProposal,
    ConversationPlanningError,
    ConversationPlanningResult,
    ConversationRenderResult,
    CorrectionProposal,
    JsonConversationPlanner,
    SemanticItemProposal,
)
from realized_core_engine import (
    EngineConfiguration,
    InspectionView,
    OperationKind,
)


class QueuePlanner:
    def __init__(self, *proposals: ConversationPlanProposal) -> None:
        self.proposals = list(proposals)
        self.contexts = []

    def propose(self, context):
        self.contexts.append(context)
        return ConversationPlanningResult(
            proposal=self.proposals.pop(0),
            receipt={"provider": "fake", "response_id": "proposal-1"},
        )


class StaticRenderer:
    def render(self, context):
        return ConversationRenderResult(
            text="Rendered from admitted state.",
            receipt={"provider": "fake", "response_id": "render-1"},
        )


class NaturalLanguagePlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "conversation"
        self.host = CoreConversationHost(
            root=self.root,
            configuration=EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )

    def test_json_planner_preserves_receipt_and_invalid_enum_is_unresolved(
        self,
    ) -> None:
        planner = JsonConversationPlanner(
            lambda _prompt, _schema: AdvisoryJsonResult(
                payload={
                    "operation": "not-an-operation",
                    "identity_disposition": "not-a-disposition",
                },
                receipt={"provider": "fake", "response_id": "response-1"},
            )
        )

        result = planner.propose(
            self._unbound_context("Do something ambiguous.")
        )

        self.assertIsNone(result.proposal.operation)
        self.assertIn(
            "unsupported operation: not-an-operation",
            result.proposal.unresolved_interpretation,
        )
        self.assertIn(
            "unsupported identity disposition: not-a-disposition",
            result.proposal.unresolved_interpretation,
        )
        self.assertEqual("response-1", result.receipt["response_id"])

    def test_text_turn_plans_then_executes_then_renders(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
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
                        text="Audience is undecided",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                corrections=(
                    CorrectionProposal(
                        target_selector="color",
                        replacement=SemanticItemProposal(
                            "color",
                            "fact",
                            "green",
                        ),
                        rationale="The user changed the color.",
                    ),
                ),
            ),
        )
        renderer = StaticRenderer()

        started = self.host.submit_text(
            "Create a Cedar brief.",
            planner=planner,
            renderer=renderer,
        )
        corrected = self.host.submit_text(
            "Change blue to green.",
            planner=planner,
            renderer=renderer,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(corrected["run_id"]))
        current = {
            item["payload"]["semantic_key"]: item["payload"].get(
                "value", item["payload"].get("text", "")
            )
            for item in state["achieved"]
        }
        self.assertEqual(
            {"project": "Cedar", "color": "green", "deadline": "Friday"},
            current,
        )
        self.assertEqual("Rendered from admitted state.", corrected["assistant_text"])
        self.assertEqual("correct", corrected["planning"]["proposal"]["operation"])
        self.assertEqual("rendered", corrected["rendering"]["status"])
        planning = self._jsonl("PLANNING_RECEIPTS.jsonl")
        rendering = self._jsonl("RENDERING_RECEIPTS.jsonl")
        self.assertEqual(2, len(planning))
        self.assertEqual(2, len(rendering))
        self.assertEqual("proposal-1", planning[-1]["provider_receipt"]["response_id"])
        self.assertEqual("render-1", rendering[-1]["provider_receipt"]["response_id"])

    def test_missing_binding_is_rejected_before_the_planner_can_choose_one(
        self,
    ) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(operation=OperationKind.START)
        )

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "exact causal binding is required",
        ):
            self.host.submit_text(
                "Continue the greenish project plan.",
                planner=planner,
                require_existing_binding=True,
            )

        self.assertEqual([], planner.contexts)
        self.assertEqual([], self._jsonl("RUN_BINDINGS.jsonl"))
        self.assertEqual(
            "unresolved",
            self._jsonl("PLANNING_RECEIPTS.jsonl")[-1]["status"],
        )

    def test_unresolved_interpretation_creates_no_semantic_revision(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.REVERSE,
                unresolved_interpretation=(
                    "The requested prior state is not identified.",
                ),
            )
        )

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "requested prior state is not identified",
        ):
            self.host.submit_text("Change it back.", planner=planner)

        self.assertEqual([], self._jsonl("RUN_BINDINGS.jsonl"))
        self.assertEqual([], self._jsonl("ENGINE_REQUESTS.jsonl"))

    def test_bound_identity_ambiguity_cannot_move_the_current_head(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            ),
            ConversationPlanProposal(
                operation=None,
                unresolved_interpretation=(
                    "The contribution could continue this objective or start "
                    "an independent objective.",
                ),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)
        state_before = self.host.inspect_binding(str(started["run_id"]))
        requests_before = self._jsonl("ENGINE_REQUESTS.jsonl")

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "could continue this objective or start an independent objective",
        ):
            self.host.submit_text(
                "Plan the next thing.",
                planner=planner,
                parent_run_id=str(started["run_id"]),
            )

        self.assertEqual(
            state_before,
            self.host.inspect_binding(str(started["run_id"])),
        )
        self.assertEqual(requests_before, self._jsonl("ENGINE_REQUESTS.jsonl"))

    def test_explicit_independent_start_inherits_no_bound_state(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Plan a weekend hiking trip",
                non_achieved_items=(
                    SemanticItemProposal(
                        "trail",
                        "requirement",
                        text="A trail remains to be selected.",
                    ),
                ),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)

        independent = self.host.submit_text(
            "Separately, start a new objective: plan a weekend hiking trip.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        self.assertNotEqual(
            started["binding"]["resumption_identity"]["objective_id"],
            independent["binding"]["resumption_identity"]["objective_id"],
        )
        independent_state = self.host.inspect_binding(
            str(independent["run_id"])
        )
        self.assertEqual([], independent_state["achieved"])
        self.assertEqual(
            ["trail"],
            [
                item["payload"].get("semantic_key")
                for item in independent_state["non_achievedness"]
                if item["payload"].get("semantic_key")
            ],
        )

    def test_public_selectors_normalize_spaces_hyphens_and_underscores(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                achieved_items=(
                    SemanticItemProposal(
                        "release_deadline",
                        "fact",
                        "Friday",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                corrections=(
                    CorrectionProposal(
                        target_selector="release deadline",
                        replacement=SemanticItemProposal(
                            "release-deadline",
                            "fact",
                            "Monday",
                        ),
                        rationale="The deadline changed.",
                    ),
                ),
            ),
        )

        started = self.host.submit_text("Set Friday.", planner=planner)
        corrected = self.host.submit_text(
            "Move the release deadline to Monday.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(corrected["run_id"]))
        current = {
            item["payload"]["semantic_key"]: item["payload"].get("value", "")
            for item in state["achieved"]
        }
        self.assertEqual({"release_deadline": "Monday"}, current)

    def test_empty_requirement_misfiled_as_achieved_is_not_duplicated(self) -> None:
        result = self.host.submit_text(
            "Add an unresolved budget requirement.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    achieved_items=(
                        SemanticItemProposal(
                            "budget",
                            "requirement",
                            text="Budget is unresolved.",
                        ),
                    ),
                    non_achieved_items=(
                        SemanticItemProposal(
                            "budget",
                            "requirement",
                            text="A budget is still required.",
                        ),
                    ),
                )
            ),
        )
        state = self.host.inspect_binding(str(result["run_id"]))

        self.assertNotIn(
            "budget",
            {
                item["payload"].get("semantic_key")
                for item in state["achieved"]
            },
        )
        self.assertEqual(
            ["budget"],
            [
                item["payload"].get("semantic_key")
                for item in state["non_achievedness"]
                if item["payload"].get("semantic_key")
            ],
        )

    def test_augment_ignores_exact_current_restatements(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "green"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience is unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.AUGMENT,
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "green"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience is unresolved.",
                    ),
                    SemanticItemProposal(
                        "budget",
                        "requirement",
                        text="A budget summary remains unresolved.",
                    ),
                ),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)

        augmented = self.host.submit_text(
            "Also require an unresolved budget summary.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(augmented["run_id"]))
        selectors = [
            item["payload"].get("semantic_key")
            for collection in ("achieved", "non_achievedness")
            for item in state[collection]
            if item["payload"].get("semantic_key")
        ]
        self.assertEqual(
            {"project", "color", "audience", "budget"},
            set(selectors),
        )
        self.assertEqual(len(selectors), len(set(selectors)))

    def test_augment_rejects_replacement_disguised_as_addition(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                achieved_items=(
                    SemanticItemProposal("color", "fact", "green"),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.AUGMENT,
                achieved_items=(
                    SemanticItemProposal("color", "fact", "blue"),
                ),
            ),
        )
        started = self.host.submit_text("Use green.", planner=planner)

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "must use correction",
        ):
            self.host.submit_text(
                "Change the color to blue.",
                planner=planner,
                parent_run_id=str(started["run_id"]),
            )

        state = self.host.inspect_binding(str(started["run_id"]))
        self.assertEqual(
            ["green"],
            [item["payload"]["value"] for item in state["achieved"]],
        )

    def test_augment_rejects_a_pure_restatement(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.AUGMENT,
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                ),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "requires new semantic material",
        ):
            self.host.submit_text(
                "Add a budget summary.",
                planner=planner,
                parent_run_id=str(started["run_id"]),
            )

    def test_correction_cannot_resolve_unmentioned_non_achievedness(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                achieved_items=(
                    SemanticItemProposal("color", "fact", "blue"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                corrections=(
                    CorrectionProposal(
                        target_selector="color",
                        replacement=SemanticItemProposal(
                            "color",
                            "fact",
                            "green",
                        ),
                        rationale="The user changed the color.",
                    ),
                ),
                resolved_selectors=("audience",),
            ),
        )
        started = self.host.submit_text("Use blue.", planner=planner)

        corrected = self.host.submit_text(
            "Change blue to green.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(corrected["run_id"]))
        self.assertEqual(
            ["audience"],
            [
                item["payload"].get("semantic_key")
                for item in state["non_achievedness"]
                if item["payload"].get("semantic_key")
            ],
        )
        self.assertEqual(
            ["audience"],
            corrected["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_unsupported_resolved_selectors"
            ],
        )

    def test_correction_deduplicates_replacement_and_promotion(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                non_achieved_items=(
                    SemanticItemProposal(
                        "audience",
                        "requirement",
                        text="Audience remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                corrections=(
                    CorrectionProposal(
                        target_selector="audience",
                        replacement=SemanticItemProposal(
                            "audience",
                            "fact",
                            "city officials",
                        ),
                        rationale="The audience was supplied.",
                    ),
                ),
                promote_selectors=("audience",),
            ),
        )
        started = self.host.submit_text(
            "The audience is unresolved.",
            planner=planner,
        )

        corrected = self.host.submit_text(
            "Set the audience to city officials.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(corrected["run_id"]))
        audience = [
            item
            for collection in ("achieved", "non_achievedness")
            for item in state[collection]
            if item["payload"].get("semantic_key") == "audience"
        ]
        self.assertEqual(1, len(audience))
        self.assertEqual("city officials", audience[0]["payload"]["value"])
        self.assertEqual(
            ["audience"],
            corrected["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_redundant_promote_selectors"
            ],
        )

    def test_realignment_defaults_omitted_current_selectors_to_unresolved(
        self,
    ) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create a Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "green"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "budget",
                        "requirement",
                        text="A budget summary remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.REDIRECT_AND_REALIGN,
                objective="Create a Cedar launch checklist",
                affected_selectors=("project", "color"),
                retained_selectors=("project", "color"),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)

        redirected = self.host.submit_text(
            "Instead create a launch checklist for Cedar.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        state = self.host.inspect_binding(str(redirected["run_id"]))
        unresolved_ids = set(state["unresolved_applicability_item_ids"])
        unresolved = {
            item["payload"].get("semantic_key")
            for item in state["non_achievedness"]
            if item["item_id"] in unresolved_ids
        }
        self.assertEqual({"color", "budget"}, unresolved)
        self.assertEqual(
            ["budget"],
            redirected["planning"]["normalized_plan"]["inlet_payload"][
                "defaulted_unresolved_realignment_selectors"
            ],
        )

    def test_applicability_clarification_preserves_unachieved_requirement(
        self,
    ) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create a Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("deadline", "fact", "Monday"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "budget",
                        "requirement",
                        text="A budget summary remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.REDIRECT_AND_REALIGN,
                objective="Create a Cedar launch checklist",
                affected_selectors=("project", "deadline", "budget"),
                retained_selectors=("project",),
                unresolved_selectors=("deadline", "budget"),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                promote_selectors=("deadline",),
                resolved_applicability_selectors=("budget",),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)
        redirected = self.host.submit_text(
            "Instead create a launch checklist for Cedar.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        clarified = self.host.submit_text(
            "Keep Monday and the budget summary.",
            planner=planner,
            parent_run_id=str(redirected["run_id"]),
        )

        state = self.host.inspect_binding(str(clarified["run_id"]))
        self.assertEqual(
            {"project", "deadline"},
            {
                item["payload"].get("semantic_key")
                for item in state["achieved"]
                if item["payload"].get("semantic_key")
            },
        )
        self.assertEqual(
            ["budget"],
            [
                item["payload"].get("semantic_key")
                for item in state["non_achievedness"]
                if item["payload"].get("semantic_key")
            ],
        )
        self.assertEqual([], state["unresolved_applicability_item_ids"])

    def test_unmentioned_applicability_cannot_be_resolved(self) -> None:
        redirected = self._redirect_with_uncertain_budget()

        clarified = self.host.submit_text(
            "Keep Monday.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.CORRECT,
                    promote_selectors=("deadline",),
                    resolved_applicability_selectors=("budget",),
                )
            ),
            parent_run_id=str(redirected["run_id"]),
        )

        state = self.host.inspect_binding(str(clarified["run_id"]))
        unresolved_ids = set(state["unresolved_applicability_item_ids"])
        self.assertEqual(
            ["budget"],
            [
                item["payload"].get("semantic_key")
                for item in state["non_achievedness"]
                if item["item_id"] in unresolved_ids
            ],
        )
        self.assertEqual(
            ["budget"],
            clarified["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_unsupported_resolved_applicability_selectors"
            ],
        )

    def test_full_resolution_dominates_applicability_only_resolution(
        self,
    ) -> None:
        redirected = self._redirect_with_uncertain_budget()

        resolved = self.host.submit_text(
            "The budget summary is no longer required.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.CORRECT,
                    resolved_selectors=("budget",),
                    resolved_applicability_selectors=("budget",),
                )
            ),
            parent_run_id=str(redirected["run_id"]),
        )

        state = self.host.inspect_binding(str(resolved["run_id"]))
        self.assertNotIn(
            "budget",
            {
                item["payload"].get("semantic_key")
                for collection in ("achieved", "non_achievedness")
                for item in state[collection]
            },
        )
        unresolved_ids = set(state["unresolved_applicability_item_ids"])
        self.assertEqual(
            ["deadline"],
            [
                item["payload"].get("semantic_key")
                for item in state["non_achievedness"]
                if item["item_id"] in unresolved_ids
            ],
        )
        self.assertEqual(
            ["budget"],
            resolved["planning"]["normalized_plan"]["inlet_payload"][
                "ignored_redundant_resolved_applicability_selectors"
            ],
        )

    def test_conflicting_achieved_and_non_achieved_selector_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ConversationPlanningError,
            "same semantic selector twice: budget",
        ):
            self.host.submit_text(
                "Set a budget while also leaving it unresolved.",
                planner=QueuePlanner(
                    ConversationPlanProposal(
                        operation=OperationKind.START,
                        achieved_items=(
                            SemanticItemProposal(
                                "budget",
                                "fact",
                                value="100",
                            ),
                        ),
                        non_achieved_items=(
                            SemanticItemProposal(
                                "budget",
                                "requirement",
                                text="A budget is still required.",
                            ),
                        ),
                    )
                ),
            )

    def test_reversal_selector_must_be_explicit_in_the_user_contribution(
        self,
    ) -> None:
        setup = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                achieved_items=(
                    SemanticItemProposal("color", "fact", "blue"),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.CORRECT,
                corrections=(
                    CorrectionProposal(
                        target_selector="color",
                        replacement=SemanticItemProposal(
                            "color",
                            "fact",
                            "green",
                        ),
                        rationale="The color changed.",
                    ),
                ),
            ),
        )
        started = self.host.submit_text("Use blue.", planner=setup)
        corrected = self.host.submit_text(
            "Change color to green.",
            planner=setup,
            parent_run_id=str(started["run_id"]),
        )

        with self.assertRaisesRegex(
            ConversationPlanningError,
            "generic reversal selector must be explicit",
        ):
            self.host.submit_text(
                "Change it back.",
                planner=QueuePlanner(
                    ConversationPlanProposal(
                        operation=OperationKind.REVERSE,
                        reversal_selector="last correction",
                    )
                ),
                parent_run_id=str(corrected["run_id"]),
            )

        reversed_result = self.host.submit_text(
            "Undo the last correction.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.REVERSE,
                    reversal_selector="latest correction",
                )
            ),
            parent_run_id=str(corrected["run_id"]),
        )
        state = self.host.inspect_binding(str(reversed_result["run_id"]))
        self.assertEqual(
            ["blue"],
            [
                item["payload"].get("value")
                for item in state["achieved"]
                if item["payload"].get("semantic_key") == "color"
            ],
        )

    def test_merge_mechanically_links_explicit_advertised_aliases(self) -> None:
        started = self.host.submit_text(
            "Create the Cedar brief.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                    ),
                )
            ),
        )
        executive = self.host.submit_text(
            "Prepare an executive version.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.BRANCH,
                    target_branch="executive",
                )
            ),
            parent_run_id=str(started["run_id"]),
        )
        technical = self.host.submit_text(
            "Prepare a technical version.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.BRANCH,
                    target_branch="technical",
                )
            ),
            parent_run_id=str(started["run_id"]),
        )

        merged = self.host.submit_text(
            "Merge the executive and technical branches.",
            planner=QueuePlanner(
                ConversationPlanProposal(operation=OperationKind.MERGE)
            ),
            parent_run_id=str(executive["run_id"]),
            binding_aliases={
                "executive": str(executive["run_id"]),
                "technical": str(technical["run_id"]),
            },
        )
        reconstruction = self.host.inspect_binding(
            str(merged["run_id"]),
            view=InspectionView.RECONSTRUCTION,
        )

        self.assertEqual(
            {
                str(executive["run_id"]),
                str(technical["run_id"]),
            },
            set(reconstruction["revision"]["parent_revision_ids"]),
        )

    def test_realignment_makes_unsupported_dispositions_unresolved(self) -> None:
        started = self.host.submit_text(
            "Create a Cedar brief using green, due Monday, with audience pending.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                        SemanticItemProposal("color", "fact", "green"),
                        SemanticItemProposal("deadline", "fact", "Monday"),
                    ),
                    non_achieved_items=(
                        SemanticItemProposal(
                            "audience",
                            "requirement",
                            text="Audience remains required.",
                        ),
                    ),
                )
            ),
        )
        redirected = self.host.submit_text(
            "Instead of a brief, create a launch checklist for Cedar.",
            planner=QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.REDIRECT_AND_REALIGN,
                    identity_disposition=(
                        ConversationIdentityDisposition.DERIVED_OBJECTIVE
                    ),
                    objective="Create a launch checklist for Cedar",
                    required_outcome="A Cedar launch checklist",
                    affected_selectors=(
                        "project",
                        "color",
                        "deadline",
                        "audience",
                    ),
                    retained_selectors=(
                        "project",
                        "color",
                        "deadline",
                        "audience",
                    ),
                )
            ),
            parent_run_id=str(started["run_id"]),
        )
        state = self.host.inspect_binding(str(redirected["run_id"]))
        self.assertEqual(
            started["binding"]["resumption_identity"]["objective_id"],
            redirected["binding"]["resumption_identity"]["objective_id"],
        )
        achieved = {
            item["payload"].get("semantic_key")
            for item in state["achieved"]
            if item["payload"].get("semantic_key")
        }
        unresolved_ids = set(state["unresolved_applicability_item_ids"])
        unresolved = {
            item["payload"].get("semantic_key")
            for item in state["non_achievedness"]
            if item["item_id"] in unresolved_ids
        }

        self.assertEqual({"project"}, achieved)
        self.assertEqual(
            {"color", "deadline", "audience"},
            unresolved,
        )

    def test_explicit_derived_objective_redirect_changes_identity(self) -> None:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("color", "fact", "green"),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.REDIRECT_AND_REALIGN,
                identity_disposition=(
                    ConversationIdentityDisposition.DERIVED_OBJECTIVE
                ),
                objective="Create the Cedar launch checklist",
                affected_selectors=("project", "color"),
                retained_selectors=("project",),
                unresolved_selectors=("color",),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)

        redirected = self.host.submit_text(
            "As a new objective, create a Cedar launch checklist.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

        self.assertNotEqual(
            started["binding"]["resumption_identity"]["objective_id"],
            redirected["binding"]["resumption_identity"]["objective_id"],
        )

    def _redirect_with_uncertain_budget(self) -> dict[str, object]:
        planner = QueuePlanner(
            ConversationPlanProposal(
                operation=OperationKind.START,
                objective="Create the Cedar brief",
                achieved_items=(
                    SemanticItemProposal("project", "fact", "Cedar"),
                    SemanticItemProposal("deadline", "fact", "Monday"),
                ),
                non_achieved_items=(
                    SemanticItemProposal(
                        "budget",
                        "requirement",
                        text="A budget summary remains unresolved.",
                    ),
                ),
            ),
            ConversationPlanProposal(
                operation=OperationKind.REDIRECT_AND_REALIGN,
                objective="Create the Cedar launch checklist",
                affected_selectors=("project", "deadline", "budget"),
                retained_selectors=("project",),
                unresolved_selectors=("deadline", "budget"),
            ),
        )
        started = self.host.submit_text("Create Cedar.", planner=planner)
        return self.host.submit_text(
            "Instead create a launch checklist for Cedar.",
            planner=planner,
            parent_run_id=str(started["run_id"]),
        )

    def _unbound_context(self, prompt: str):
        from realized_core.planning import ConversationPlanningContext

        return ConversationPlanningContext(
            prompt=prompt,
            scope_id=self.host.scope_id,
        )

    def _jsonl(self, name: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (self.root / name).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


if __name__ == "__main__":
    unittest.main()
