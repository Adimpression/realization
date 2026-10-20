# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dst import load_dst_normalized_case
from dst.projection import project_normalized_case_to_decision_frame
from decision_review import (
    DecisionFrame,
    DecisionReviewItem,
    decision_review_item_from_review_item,
    list_decision_review_items,
    load_decision_frame,
    persist_decision_review,
    stable_decision_frame_id,
)
from decision_review_projection import (
    analyze_decision_frame,
    decision_review_model,
    list_decision_analysis_receipts,
    persist_decision_analysis_receipt,
)
from decision_review_policy import (
    default_decision_policy_profile,
    load_decision_policy_profile,
    next_decision_policy_profile_kind,
    persist_decision_policy_profile,
)
from learning_context import (
    LearningContext,
    LearningUnit,
    new_learning_delta,
    new_learning_source,
    persist_learning_context,
    persist_learning_delta,
    persist_learning_source,
    stable_learning_unit_id,
)
from itemize import materialize_itemization_session
from review_composition import review_composition_from_itemization


class DecisionReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _persist_demo_context(self) -> str:
        subject_id = "decision-review-demo"
        source = new_learning_source(
            subject_id=subject_id,
            title="Decision Review Notes",
            source_ref="notes/decision-review.md",
            source_kind="markdown",
        )
        persist_learning_source(
            self.root,
            source,
            source_text=(
                "# Decision Review Notes\n\n"
                "## Operations Team\nOperations team executes the workflow.\n\n"
                "## Reduce Approval Friction\nReduce approval friction across the release path.\n\n"
                "## Current Manual Review State\nManual review is the current state.\n\n"
                "## Target Assisted Review State\nAssisted review is the target state.\n\n"
                "## Add Guided Decision Aid\nAdd a guided decision aid as the option.\n"
            ),
        )
        delta = new_learning_delta(
            subject_id=subject_id,
            source_kind="markdown",
            rationale="Admit the decision review test subject.",
        )
        persist_learning_delta(self.root, delta)
        persist_learning_context(
            self.root,
            LearningContext(
                subject_id=subject_id,
                canonical_title="Decision Review Demo",
                aliases=("Decision Review Demo",),
                subject_family="Operations",
                summary="Decision review test subject.",
                units=(
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Operations Team"),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Operations Team",
                        statement="Operations team executes the workflow.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Reduce Approval Friction"),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Reduce Approval Friction",
                        statement="Reduce approval friction across the release path.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Current Manual Review State"),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Current Manual Review State",
                        statement="Manual review is the current state.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Target Assisted Review State"),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Target Assisted Review State",
                        statement="Assisted review is the target state.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                    LearningUnit(
                        unit_id=stable_learning_unit_id(subject_id=subject_id, unit_kind="definition", canonical_title="Add Guided Decision Aid"),
                        subject_id=subject_id,
                        unit_kind="definition",
                        canonical_title="Add Guided Decision Aid",
                        statement="Add a guided decision aid as the option.",
                        provenance_refs=(source.source_id,),
                        status="admitted",
                    ),
                ),
                linked_source_ids=(source.source_id,),
                applied_delta_ids=(delta.delta_id,),
                governance_status="active",
            ),
        )
        return subject_id

    def test_decision_review_round_trips_frame_items_and_receipt(self) -> None:
        subject_id = self._persist_demo_context()
        session, itemized_items = materialize_itemization_session(self.root, subject_id)

        # reload through the review path so the test uses real seeded review items
        from learning_context import load_learning_context

        loaded_context = load_learning_context(self.root, subject_id)
        _composition, review_items = review_composition_from_itemization(
            loaded_context,
            session,
            itemized_items,
            build_epoch_ms=100,
            status="draft",
        )
        role_map = {
            "Operations Team": "actor",
            "Reduce Approval Friction": "objective",
            "Current Manual Review State": "current_state",
            "Target Assisted Review State": "target_state",
            "Add Guided Decision Aid": "decision_candidate",
        }
        selected_review_items = tuple(
            item
            for item in review_items
            if item.metadata.get("canonical_label") in role_map
        )
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="What decision should the report support for guided review?",
            ),
            subject_id=subject_id,
            question="What decision should the report support for guided review?",
            decision_mode="decision_aid",
            status="draft",
            created_at_epoch_ms=100,
            updated_at_epoch_ms=100,
        )
        decision_items = tuple(
            decision_review_item_from_review_item(
                item,
                decision_frame_id=frame.decision_frame_id,
                decision_role=role_map[str(item.metadata.get("canonical_label"))],
                ordering=index,
                build_epoch_ms=101,
            )
            for index, item in enumerate(selected_review_items, start=1)
        )
        current_state_ids = tuple(
            item.decision_review_item_id
            for item in decision_items
            if item.decision_role == "current_state"
        )
        target_state_ids = tuple(
            item.decision_review_item_id
            for item in decision_items
            if item.decision_role == "target_state"
        )
        objective_ids = tuple(
            item.decision_review_item_id
            for item in decision_items
            if item.decision_role == "objective"
        )
        frame = DecisionFrame.from_dict(
            {
                **frame.to_dict(),
                "current_state_ids": list(current_state_ids),
                "target_state_ids": list(target_state_ids),
                "primary_objective_ids": list(objective_ids),
            }
        )

        persist_decision_review(self.root, frame, decision_items)
        receipt = analyze_decision_frame(frame, decision_items, build_epoch_ms=102)
        persist_decision_analysis_receipt(self.root, subject_id, receipt)

        loaded_frame = load_decision_frame(self.root, subject_id)
        loaded_items = list_decision_review_items(self.root, subject_id)
        loaded_receipts = list_decision_analysis_receipts(self.root, subject_id)

        self.assertEqual(loaded_frame.decision_frame_id, frame.decision_frame_id)
        self.assertEqual(len(loaded_items), len(decision_items))
        self.assertTrue(any(item.decision_role == "actor" for item in loaded_items))
        self.assertTrue(any(item.decision_role == "current_state" for item in loaded_items))
        self.assertEqual(len(loaded_receipts), 1)
        self.assertIn(loaded_receipts[0].recommendation_status, {"blocked", "decision_aid_ready", "recommendable", "valid_but_not_executable"})

    def test_decision_review_analysis_uses_bound_transition_and_selected_decision_relations(self) -> None:
        subject_id = self._persist_demo_context()
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="Which transition should be chosen?",
            ),
            subject_id=subject_id,
            question="Which transition should be chosen?",
            decision_mode="decision_aid",
            current_state_ids=("state-current",),
            target_state_ids=("state-target",),
            primary_objective_ids=("objective-1",),
            created_at_epoch_ms=200,
            updated_at_epoch_ms=200,
        )
        decision_items = (
            DecisionReviewItem(
                decision_review_item_id="state-current",
                review_item_id="review-current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                metadata={"canonical_label": "Current State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-target",
                review_item_id="review-target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                metadata={"canonical_label": "Target State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="objective-1",
                review_item_id="review-objective",
                decision_frame_id=frame.decision_frame_id,
                decision_role="objective",
                ordering=3,
                metadata={"canonical_label": "Reach Target"},
            ),
            DecisionReviewItem(
                decision_review_item_id="capability-1",
                review_item_id="review-capability",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=4,
                metadata={"canonical_label": "Guided Ticketing Capability"},
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-1",
                review_item_id="review-transition",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=5,
                metadata={
                    "canonical_label": "Move To Target",
                    "source_state_decision_review_item_id": "state-current",
                    "target_state_decision_review_item_id": "state-target",
                    "changed_capability_decision_review_item_id": "capability-1",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="actor-1",
                review_item_id="review-actor",
                decision_frame_id=frame.decision_frame_id,
                decision_role="actor",
                ordering=6,
                metadata={"canonical_label": "Operations Team"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decision-1",
                review_item_id="review-decision",
                decision_frame_id=frame.decision_frame_id,
                decision_role="decision_candidate",
                ordering=7,
                metadata={
                    "canonical_label": "Choose The Transition",
                    "selected_transition_decision_review_item_id": "transition-1",
                    "assigned_actor_decision_review_item_id": "actor-1",
                },
            ),
        )

        receipt = analyze_decision_frame(frame, decision_items, build_epoch_ms=201)

        self.assertEqual(receipt.admissible_transition_ids, ("Move To Target",))
        self.assertEqual(receipt.valid_decision_ids, ("Choose The Transition",))
        self.assertEqual(receipt.executable_decision_ids, ("Choose The Transition",))

    def test_decision_review_analysis_honors_dst_normalized_decision_status_when_present(self) -> None:
        national_case = load_dst_normalized_case("national-school-system-exam-digitization-rollout")
        self.assertIsNotNone(national_case)
        assert national_case is not None

        national_projection = project_normalized_case_to_decision_frame(national_case, build_epoch_ms=210)
        national_receipt = analyze_decision_frame(
            national_projection.frame,
            national_projection.items,
            build_epoch_ms=211,
        )

        self.assertEqual(
            set(national_receipt.valid_decision_ids),
            {
                "Conservative layered rollout",
                "Readiness-based regional rollout",
                "Resilience-first audited rollout",
            },
        )
        self.assertEqual(
            national_receipt.executable_decision_ids,
            ("Resilience-first audited rollout",),
        )
        self.assertEqual(
            national_receipt.metadata.get("recommended_option_ids"),
            ("Resilience-first audited rollout",),
        )

        regional_case = load_dst_normalized_case("regional-emergency-alerting-system")
        self.assertIsNotNone(regional_case)
        assert regional_case is not None

        regional_projection = project_normalized_case_to_decision_frame(regional_case, build_epoch_ms=212)
        regional_receipt = analyze_decision_frame(
            regional_projection.frame,
            regional_projection.items,
            build_epoch_ms=213,
        )

        self.assertEqual(
            set(regional_receipt.valid_decision_ids),
            {
                "Resilience-first configuration",
                "Inclusion-first configuration",
                "Balanced configuration",
            },
        )
        self.assertEqual(
            regional_receipt.executable_decision_ids,
            ("Balanced configuration",),
        )
        self.assertEqual(
            regional_receipt.metadata.get("recommended_option_ids"),
            ("Balanced configuration",),
        )

    def test_decision_review_analysis_reports_missing_capability_and_actor_bindings(self) -> None:
        subject_id = self._persist_demo_context()
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="Which transition should be chosen?",
            ),
            subject_id=subject_id,
            question="Which transition should be chosen?",
            decision_mode="decision_aid",
            current_state_ids=("state-current",),
            target_state_ids=("state-target",),
            primary_objective_ids=("objective-1",),
            created_at_epoch_ms=220,
            updated_at_epoch_ms=220,
        )
        decision_items = (
            DecisionReviewItem(
                decision_review_item_id="state-current",
                review_item_id="review-current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                metadata={"canonical_label": "Current State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-target",
                review_item_id="review-target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                metadata={"canonical_label": "Target State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="objective-1",
                review_item_id="review-objective",
                decision_frame_id=frame.decision_frame_id,
                decision_role="objective",
                ordering=3,
                metadata={"canonical_label": "Reach Target"},
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-1",
                review_item_id="review-transition",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=4,
                metadata={
                    "canonical_label": "Move To Target",
                    "source_state_decision_review_item_id": "state-current",
                    "target_state_decision_review_item_id": "state-target",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="decision-1",
                review_item_id="review-decision",
                decision_frame_id=frame.decision_frame_id,
                decision_role="decision_candidate",
                ordering=5,
                metadata={
                    "canonical_label": "Choose The Transition",
                    "selected_transition_decision_review_item_id": "transition-1",
                },
            ),
        )

        receipt = analyze_decision_frame(frame, decision_items, build_epoch_ms=221)

        self.assertEqual(receipt.admissible_transition_ids, ("Move To Target",))
        self.assertEqual(receipt.valid_decision_ids, ())
        self.assertEqual(receipt.executable_decision_ids, ())
        self.assertIn(
            "Transition candidate 'Move To Target' is missing its changed capability.",
            receipt.blocking_conditions,
        )
        self.assertIn(
            "Decision candidate 'Choose The Transition' is missing its assigned actor.",
            receipt.blocking_conditions,
        )

    def test_decision_review_model_projects_multiple_selected_transitions_for_one_decision(self) -> None:
        subject_id = self._persist_demo_context()
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="Which transitions should be chosen?",
            ),
            subject_id=subject_id,
            question="Which transitions should be chosen?",
            decision_mode="decision_aid",
            current_state_ids=("state-current",),
            target_state_ids=("state-target",),
            primary_objective_ids=("objective-1",),
            created_at_epoch_ms=230,
            updated_at_epoch_ms=230,
        )
        decision_items = (
            DecisionReviewItem(
                decision_review_item_id="state-current",
                review_item_id="review-current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                metadata={"canonical_label": "Current State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-target",
                review_item_id="review-target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                metadata={"canonical_label": "Target State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="objective-1",
                review_item_id="review-objective",
                decision_frame_id=frame.decision_frame_id,
                decision_role="objective",
                ordering=3,
                metadata={"canonical_label": "Reach Target"},
            ),
            DecisionReviewItem(
                decision_review_item_id="capability-1",
                review_item_id="review-capability-1",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=4,
                metadata={"canonical_label": "SMS Alerts"},
            ),
            DecisionReviewItem(
                decision_review_item_id="capability-2",
                review_item_id="review-capability-2",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=5,
                metadata={"canonical_label": "Cell Broadcast"},
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-1",
                review_item_id="review-transition-1",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=6,
                metadata={
                    "canonical_label": "Enable SMS Alerts",
                    "source_state_decision_review_item_id": "state-current",
                    "target_state_decision_review_item_id": "state-target",
                    "changed_capability_decision_review_item_id": "capability-1",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-2",
                review_item_id="review-transition-2",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=7,
                metadata={
                    "canonical_label": "Enable Cell Broadcast",
                    "source_state_decision_review_item_id": "state-current",
                    "target_state_decision_review_item_id": "state-target",
                    "changed_capability_decision_review_item_id": "capability-2",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="actor-1",
                review_item_id="review-actor",
                decision_frame_id=frame.decision_frame_id,
                decision_role="actor",
                ordering=8,
                metadata={"canonical_label": "Operations Team"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decision-1",
                review_item_id="review-decision",
                decision_frame_id=frame.decision_frame_id,
                decision_role="decision_candidate",
                ordering=9,
                metadata={
                    "canonical_label": "Run Both Channels",
                    "selected_transition_decision_review_item_ids": (
                        "transition-1",
                        "transition-2",
                    ),
                    "assigned_actor_decision_review_item_id": "actor-1",
                },
            ),
        )

        model = decision_review_model(frame, decision_items)
        self.assertEqual(
            {
                (decision.name, transition.name)
                for decision, transition in model.selects
            },
            {
                ("Run Both Channels", "Enable SMS Alerts"),
                ("Run Both Channels", "Enable Cell Broadcast"),
            },
        )
        self.assertEqual(
            {
                (decision.name, actor.name, capability.name)
                for decision, actor, capability in model.assigns
            },
            {
                ("Run Both Channels", "Operations Team", "SMS Alerts"),
                ("Run Both Channels", "Operations Team", "Cell Broadcast"),
            },
        )

    def test_decision_review_model_projects_capability_dependency_and_boundary_relations(self) -> None:
        subject_id = self._persist_demo_context()
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="What gating relations apply to this capability?",
            ),
            subject_id=subject_id,
            question="What gating relations apply to this capability?",
            decision_mode="decision_aid",
            current_state_ids=("state-current",),
            target_state_ids=("state-target",),
            primary_objective_ids=("objective-1",),
            created_at_epoch_ms=235,
            updated_at_epoch_ms=235,
        )
        decision_items = (
            DecisionReviewItem(
                decision_review_item_id="state-current",
                review_item_id="review-current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                metadata={"canonical_label": "Current State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-target",
                review_item_id="review-target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                metadata={"canonical_label": "Target State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="objective-1",
                review_item_id="review-objective",
                decision_frame_id=frame.decision_frame_id,
                decision_role="objective",
                ordering=3,
                metadata={"canonical_label": "Reach Target"},
            ),
            DecisionReviewItem(
                decision_review_item_id="capability-1",
                review_item_id="review-capability",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=4,
                metadata={
                    "canonical_label": "SMS Alerts",
                    "required_dependency_decision_review_item_ids": ("dependency-1",),
                    "crossed_boundary_decision_review_item_ids": ("boundary-1",),
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="dependency-1",
                review_item_id="review-dependency",
                decision_frame_id=frame.decision_frame_id,
                decision_role="dependency",
                ordering=5,
                metadata={"canonical_label": "Carrier Uptime"},
            ),
            DecisionReviewItem(
                decision_review_item_id="boundary-1",
                review_item_id="review-boundary",
                decision_frame_id=frame.decision_frame_id,
                decision_role="boundary",
                ordering=6,
                metadata={"canonical_label": "Carrier Boundary"},
            ),
        )

        model = decision_review_model(frame, decision_items)

        self.assertEqual(
            {(capability.name, dependency.name) for capability, dependency in model.requires},
            {("SMS Alerts", "Carrier Uptime")},
        )
        self.assertEqual(
            {(capability.name, boundary.name) for capability, boundary in model.crosses},
            {("SMS Alerts", "Carrier Boundary")},
        )

    def test_decision_review_analysis_records_multi_step_candidate_paths(self) -> None:
        subject_id = self._persist_demo_context()
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="How can the system reach the target state?",
            ),
            subject_id=subject_id,
            question="How can the system reach the target state?",
            decision_mode="decision_aid",
            current_state_ids=("state-current",),
            target_state_ids=("state-target",),
            primary_objective_ids=("objective-1",),
            created_at_epoch_ms=240,
            updated_at_epoch_ms=240,
        )
        decision_items = (
            DecisionReviewItem(
                decision_review_item_id="state-current",
                review_item_id="review-current",
                decision_frame_id=frame.decision_frame_id,
                decision_role="current_state",
                ordering=1,
                metadata={"canonical_label": "Current State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-middle",
                review_item_id="review-middle",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=2,
                metadata={"canonical_label": "Intermediate State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="state-target",
                review_item_id="review-target",
                decision_frame_id=frame.decision_frame_id,
                decision_role="target_state",
                ordering=3,
                metadata={"canonical_label": "Target State"},
            ),
            DecisionReviewItem(
                decision_review_item_id="objective-1",
                review_item_id="review-objective",
                decision_frame_id=frame.decision_frame_id,
                decision_role="objective",
                ordering=4,
                metadata={"canonical_label": "Reach Target"},
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-1",
                review_item_id="review-transition-1",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=5,
                metadata={
                    "canonical_label": "Move To Intermediate",
                    "source_state_decision_review_item_id": "state-current",
                    "target_state_decision_review_item_id": "state-middle",
                    "changed_capability_decision_review_item_id": "capability-1",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="transition-2",
                review_item_id="review-transition-2",
                decision_frame_id=frame.decision_frame_id,
                decision_role="transition_candidate",
                ordering=6,
                metadata={
                    "canonical_label": "Move To Target",
                    "source_state_decision_review_item_id": "state-middle",
                    "target_state_decision_review_item_id": "state-target",
                    "changed_capability_decision_review_item_id": "capability-1",
                },
            ),
            DecisionReviewItem(
                decision_review_item_id="capability-1",
                review_item_id="review-capability",
                decision_frame_id=frame.decision_frame_id,
                decision_role="capability",
                ordering=7,
                metadata={"canonical_label": "Guided Support"},
            ),
            DecisionReviewItem(
                decision_review_item_id="decision-1",
                review_item_id="review-decision",
                decision_frame_id=frame.decision_frame_id,
                decision_role="decision_candidate",
                ordering=8,
                metadata={"canonical_label": "Choose A Path"},
            ),
        )

        receipt = analyze_decision_frame(frame, decision_items, build_epoch_ms=241)

        self.assertEqual(receipt.metadata.get("candidate_path_count"), 1)
        self.assertEqual(
            tuple(receipt.metadata.get("candidate_path_signatures", ())),
            ("Current State --Move To Intermediate--> Intermediate State --Move To Target--> Target State",),
        )

    def test_decision_policy_profiles_persist_and_affect_blocking_conditions(self) -> None:
        subject_id = self._persist_demo_context()
        session, itemized_items = materialize_itemization_session(self.root, subject_id)

        from learning_context import load_learning_context

        loaded_context = load_learning_context(self.root, subject_id)
        _composition, review_items = review_composition_from_itemization(
            loaded_context,
            session,
            itemized_items,
            build_epoch_ms=200,
            status="draft",
        )
        role_map = {
            "Operations Team": "actor",
            "Reduce Approval Friction": "objective",
            "Current Manual Review State": "current_state",
            "Target Assisted Review State": "target_state",
            "Add Guided Decision Aid": "decision_candidate",
        }
        selected_review_items = tuple(
            item
            for item in review_items
            if item.metadata.get("canonical_label") in role_map
        )
        frame = DecisionFrame(
            decision_frame_id=stable_decision_frame_id(
                subject_id=subject_id,
                question="What decision should the report support for guided review?",
            ),
            subject_id=subject_id,
            question="What decision should the report support for guided review?",
            decision_mode="decision_aid",
            created_at_epoch_ms=200,
            updated_at_epoch_ms=200,
        )
        decision_items = tuple(
            decision_review_item_from_review_item(
                item,
                decision_frame_id=frame.decision_frame_id,
                decision_role=role_map[str(item.metadata.get("canonical_label"))],
                ordering=index,
                build_epoch_ms=201,
            )
            for index, item in enumerate(selected_review_items, start=1)
        )
        frame = DecisionFrame.from_dict(
            {
                **frame.to_dict(),
                "current_state_ids": [
                    item.decision_review_item_id
                    for item in decision_items
                    if item.decision_role == "current_state"
                ],
                "target_state_ids": [
                    item.decision_review_item_id
                    for item in decision_items
                    if item.decision_role == "target_state"
                ],
                "primary_objective_ids": [
                    item.decision_review_item_id
                    for item in decision_items
                    if item.decision_role == "objective"
                ],
            }
        )
        persist_decision_review(self.root, frame, decision_items)

        conservative_policy = default_decision_policy_profile(
            decision_frame_id=frame.decision_frame_id,
            build_epoch_ms=202,
            profile_kind="conservative",
        )
        persist_decision_policy_profile(self.root, subject_id, conservative_policy)
        loaded_policy = load_decision_policy_profile(self.root, subject_id)
        conservative_receipt = analyze_decision_frame(
            frame,
            decision_items,
            policy_profile=loaded_policy,
            build_epoch_ms=203,
        )

        permissive_policy = default_decision_policy_profile(
            decision_frame_id=frame.decision_frame_id,
            build_epoch_ms=204,
            profile_kind=next_decision_policy_profile_kind("balanced"),
        )
        permissive_receipt = analyze_decision_frame(
            frame,
            decision_items,
            policy_profile=permissive_policy,
            build_epoch_ms=205,
        )

        self.assertEqual(loaded_policy.profile_kind, "conservative")
        self.assertEqual(conservative_receipt.metadata.get("policy_profile_kind"), "conservative")
        self.assertIn(
            "Policy requires at least one supporting evidence item.",
            conservative_receipt.blocking_conditions,
        )
        self.assertEqual(permissive_policy.profile_kind, "permissive")
        self.assertNotIn(
            "Policy requires at least one supporting evidence item.",
            permissive_receipt.blocking_conditions,
        )
