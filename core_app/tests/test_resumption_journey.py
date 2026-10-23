from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


from realized_core.chat import CoreConversationHost
from realized_core.conversation import (
    ConversationTurnPlan,
    CorrectionPlan,
    RealignmentPlan,
    ReversalPlan,
)
from realized_core_engine import (
    EngineConfiguration,
    GoverningDirection,
    InspectionView,
    OperationKind,
    SemanticDelta,
    SemanticItem,
)


def _item(key: str, value: str, *, version: str = "v1") -> SemanticItem:
    return SemanticItem(
        item_id=f"item-{key}-{version}",
        kind="fact",
        payload={
            "semantic_key": key,
            "value": value,
            "text": f"{key}: {value}",
        },
        evidence_references=(f"fixture:{key}:{version}",),
    )


def _requirement(key: str, text: str) -> SemanticItem:
    return SemanticItem(
        item_id=f"requirement-{key}",
        kind="requirement",
        payload={"semantic_key": key, "text": text},
        evidence_references=(f"fixture:{key}",),
    )


def _values(state: dict[str, object], collection: str) -> dict[str, str]:
    return {
        str(item["payload"]["semantic_key"]): str(
            item["payload"].get("value", item["payload"].get("text", ""))
        )
        for item in state[collection]
        if item.get("payload", {}).get("semantic_key")
    }


def _semantic_item(state: dict[str, object], key: str) -> SemanticItem:
    matches = [
        SemanticItem.from_dict(item)
        for collection in ("achieved", "non_achievedness")
        for item in state[collection]
        if item.get("payload", {}).get("semantic_key") == key
    ]
    if len(matches) != 1:
        raise AssertionError(f"Expected one current semantic item for {key}: {matches}")
    return matches[0]


class ResumptionConversationJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "conversation"
        self.configuration = EngineConfiguration(
            max_steps=0,
            llm_policy="off",
            discovery="off",
            reflection="off",
            contemplation="off",
        )
        self.host = CoreConversationHost(
            root=self.root,
            configuration=self.configuration,
        )

    def _start_brief(self) -> dict[str, object]:
        return self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.START,
                prompt=(
                    "Create a brief for Cedar. Use blue, make it due Friday, "
                    "and ask for the undecided audience."
                ),
                governing_direction=GoverningDirection(
                    objective="Create the Cedar brief",
                    scope=self.host.scope_id,
                    required_outcome="A brief with an identified audience",
                ),
                semantic_delta=SemanticDelta(
                    achieved=(
                        _item("project", "Cedar"),
                        _item("color", "blue"),
                        _item("deadline", "Friday"),
                    ),
                    non_achievedness=(
                        _requirement("audience", "Audience is undecided"),
                    ),
                ),
                treatment_label="structured_start",
            )
        )

    def _correct(
        self,
        parent_run_id: str,
        *,
        key: str,
        value: str,
        version: str,
    ) -> dict[str, object]:
        return self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.CORRECT,
                prompt=f"Change {key} to {value}.",
                parent_run_id=parent_run_id,
                corrections=(
                    CorrectionPlan(
                        target_selector=key,
                        replacement=_item(key, value, version=version),
                        rationale=f"The user explicitly corrected {key}.",
                    ),
                ),
                treatment_label="structured_correction",
            )
        )

    def _corrected_brief(self) -> dict[str, object]:
        started = self._start_brief()
        color = self._correct(
            str(started["run_id"]),
            key="color",
            value="green",
            version="v2",
        )
        return self._correct(
            str(color["run_id"]),
            key="deadline",
            value="Monday",
            version="v2",
        )

    def test_corrections_restart_and_presentation_do_not_replace_state(self) -> None:
        deadline = self._corrected_brief()

        state = self.host.inspect_binding(str(deadline["run_id"]))
        self.assertEqual(
            {
                "project": "Cedar",
                "color": "green",
                "deadline": "Monday",
            },
            _values(state, "achieved"),
        )
        self.assertEqual(
            {"audience": "Audience is undecided"},
            _values(state, "non_achievedness"),
        )
        self.assertNotEqual("completed", deadline["run_outcome"])
        self.assertTrue(str(deadline["assistant_text"]).strip())

        reconstruction = self.host.inspect_binding(
            str(deadline["run_id"]),
            view=InspectionView.RECONSTRUCTION,
        )
        revision = reconstruction["revision"]
        self.assertEqual(
            str(deadline["binding"]["resumption_identity"]["state_digest"]),
            revision["identity"]["state_digest"],
        )
        self.assertEqual(2, len(revision["state"]["supersession_edges"]))
        provenance = self.host.inspect_binding(
            str(deadline["run_id"]),
            view=InspectionView.PROVENANCE,
        )
        self.assertEqual(2, len(provenance["supersession_edges"]))
        self.assertTrue(provenance["provenance_references"])

        messages_path = self.root / "MESSAGES.jsonl"
        messages = [
            json.loads(line)
            for line in messages_path.read_text(encoding="utf-8").splitlines()
        ]
        messages[-1]["content"] = "A completely different presentation."
        messages_path.write_text(
            "".join(json.dumps(message) + "\n" for message in messages),
            encoding="utf-8",
        )

        restarted = CoreConversationHost(
            root=self.root,
            configuration=self.configuration,
        )
        restarted_state = restarted.inspect_binding(str(deadline["run_id"]))
        self.assertEqual(state, restarted_state)
        self.assertEqual(
            revision["identity"]["state_digest"],
            restarted.inspect_binding(
                str(deadline["run_id"]),
                view=InspectionView.RECONSTRUCTION,
            )["revision"]["identity"]["state_digest"],
        )

        messages_path.unlink()
        replacement_configuration = EngineConfiguration(
            sqlite_path=self.host.sqlite_path,
            max_steps=0,
            llm_policy="off",
            discovery="off",
            reflection="off",
            contemplation="off",
        )
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "replacement-provider-must-not-be-used"},
        ):
            replacement_host = CoreConversationHost(
                root=self.root,
                configuration=replacement_configuration,
            )
            continued = replacement_host.submit_plan(
                ConversationTurnPlan(
                    operation=OperationKind.CONTINUE,
                    prompt="State what remains unresolved in the brief.",
                    parent_run_id=str(deadline["run_id"]),
                    treatment_label="provider_independent_continuation",
                )
            )
        continued_state = replacement_host.inspect_binding(
            str(continued["run_id"])
        )
        self.assertEqual(
            _values(state, "achieved"),
            _values(continued_state, "achieved"),
        )
        self.assertEqual(
            _values(state, "non_achievedness"),
            _values(continued_state, "non_achievedness"),
        )
        self.assertNotIn(
            "A completely different presentation.",
            messages_path.read_text(encoding="utf-8"),
        )

    def test_correction_can_update_a_paused_nonzero_step_reduction(self) -> None:
        host = CoreConversationHost(
            root=Path(self.temporary.name) / "nonzero-step-conversation",
            configuration=EngineConfiguration(
                max_steps=24,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            ),
        )
        started = host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.START,
                prompt="Create the Cedar brief.",
                governing_direction=GoverningDirection(
                    objective="Create the Cedar brief",
                    scope=host.scope_id,
                    required_outcome="A brief with an identified audience",
                ),
                semantic_delta=SemanticDelta(
                    achieved=(
                        _item("project", "Cedar"),
                        _item("color", "blue"),
                    ),
                    non_achievedness=(
                        _requirement("audience", "Audience is undecided"),
                    ),
                ),
            )
        )
        self.assertEqual("paused", started["run_outcome"])

        corrected = host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.CORRECT,
                prompt="Change blue to green.",
                parent_run_id=str(started["run_id"]),
                corrections=(
                    CorrectionPlan(
                        target_selector="color",
                        replacement=_item("color", "green", version="v2"),
                        rationale="The user explicitly corrected color.",
                    ),
                ),
            )
        )

        self.assertEqual("paused", corrected["run_outcome"])
        state = host.inspect_binding(str(corrected["run_id"]))
        self.assertEqual("green", _values(state, "achieved")["color"])

    def test_augmentation_redirection_and_clarification_preserve_uncertainty(
        self,
    ) -> None:
        baseline = self._corrected_brief()
        augmented = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.AUGMENT,
                prompt="Also include a budget summary.",
                parent_run_id=str(baseline["run_id"]),
                semantic_delta=SemanticDelta(
                    non_achievedness=(
                        _requirement(
                            "budget",
                            "A budget summary is still required",
                        ),
                    ),
                ),
                treatment_label="structured_augmentation",
            )
        )
        augmented_state = self.host.inspect_binding(str(augmented["run_id"]))
        self.assertEqual(
            {
                "project": "Cedar",
                "color": "green",
                "deadline": "Monday",
            },
            _values(augmented_state, "achieved"),
        )
        self.assertEqual(
            {"audience", "budget"},
            set(_values(augmented_state, "non_achievedness")),
        )
        self.assertEqual(
            2,
            len(augmented_state["supersession_edges"]),
            "augmentation must not supersede current material",
        )

        redirected = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.REDIRECT_AND_REALIGN,
                prompt=(
                    "Instead of a brief, create a launch checklist for "
                    "Cedar."
                ),
                parent_run_id=str(augmented["run_id"]),
                governing_direction=GoverningDirection(
                    objective="Create the Cedar launch checklist",
                    scope=self.host.scope_id,
                    required_outcome="A complete launch checklist",
                ),
                realignment=RealignmentPlan(
                    affected_selectors=(
                        "project",
                        "color",
                        "deadline",
                        "audience",
                        "budget",
                    ),
                    retained_selectors=("project",),
                    unresolved_selectors=(
                        "color",
                        "deadline",
                        "audience",
                        "budget",
                    ),
                    rationale="The requested product changed from a brief to a checklist.",
                    evidence_references=("fixture:redirect",),
                    governance_references=("policy:realignment",),
                    completeness_statement=(
                        "Every application semantic item was classified."
                    ),
                ),
                treatment_label="structured_redirection",
            )
        )
        self.assertNotEqual(
            "rejected",
            redirected["run_outcome"],
            redirected["summary"],
        )
        redirected_state = self.host.inspect_binding(str(redirected["run_id"]))
        self.assertEqual(
            {"project": "Cedar"},
            _values(redirected_state, "achieved"),
        )
        self.assertEqual(
            {"color", "deadline", "audience", "budget"},
            set(_values(redirected_state, "non_achievedness")),
            redirected_state,
        )
        self.assertEqual(
            {
                _semantic_item(redirected_state, key).item_id
                for key in ("color", "deadline", "audience", "budget")
            },
            set(redirected_state["unresolved_applicability_item_ids"]),
        )
        for key in ("color", "deadline", "audience", "budget"):
            with self.subTest(externalized_item=key):
                payload = _semantic_item(redirected_state, key).payload
                self.assertNotIn("resumption_projection", payload)
                self.assertNotIn("node", payload)
                self.assertNotIn("status", payload)
        self.assertEqual({}, redirected_state["engine_state"])
        self.assertEqual(
            "Create the Cedar launch checklist",
            redirected_state["governing_direction"]["objective"],
        )

        clarified = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.CORRECT,
                prompt=(
                    "Keep Monday and the budget summary, but drop the color "
                    "and audience requirements."
                ),
                parent_run_id=str(redirected["run_id"]),
                semantic_delta=SemanticDelta(
                    achieved=(
                        _semantic_item(redirected_state, "deadline"),
                    ),
                    resolved_applicability_item_ids=(
                        _semantic_item(redirected_state, "budget").item_id,
                    ),
                ),
                corrections=(
                    CorrectionPlan(
                        target_selector="color",
                        replacement=None,
                        rationale="Color no longer applies to the checklist.",
                    ),
                    CorrectionPlan(
                        target_selector="audience",
                        replacement=None,
                        rationale="Audience no longer applies to the checklist.",
                    ),
                ),
                treatment_label="structured_realignment_clarification",
            )
        )
        clarified_state = self.host.inspect_binding(str(clarified["run_id"]))
        self.assertEqual(
            {
                "project": "Cedar",
                "deadline": "Monday",
            },
            _values(clarified_state, "achieved"),
        )
        self.assertEqual(
            {"budget": "A budget summary is still required"},
            _values(clarified_state, "non_achievedness"),
        )
        self.assertEqual([], clarified_state["unresolved_applicability_item_ids"])
        self.assertEqual(
            str(redirected["run_id"]),
            clarified["parent_run_id"],
            "clarification must be a new anchored transition",
        )

    def test_explanation_and_reversal_use_persisted_path_artifacts(self) -> None:
        corrected = self._corrected_brief()
        corrected_run_id = str(corrected["run_id"])
        corrected_state = self.host.inspect_binding(corrected_run_id)
        corrected_digest = str(
            corrected["binding"]["resumption_identity"]["state_digest"]
        )

        explained = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.EXPLAIN,
                prompt="Why is the deadline Monday?",
                parent_run_id=corrected_run_id,
                treatment_label="structured_explanation",
            )
        )
        self.assertEqual(corrected_run_id, explained["run_id"])
        self.assertEqual(corrected_state, self.host.inspect_binding(corrected_run_id))
        self.assertFalse(
            explained["summary"]["diagnostics"]["semantic_state_changed"]
        )
        self.assertEqual(
            OperationKind.EXPLAIN.value,
            explained["summary"]["operation_result"]["operation"],
        )

        for operation in (OperationKind.VERIFY, OperationKind.RECONSTRUCT):
            with self.subTest(operation=operation.value):
                inspected = self.host.submit_plan(
                    ConversationTurnPlan(
                        operation=operation,
                        prompt=f"{operation.value} the admitted path.",
                        parent_run_id=corrected_run_id,
                        treatment_label=f"structured_{operation.value}",
                    )
                )
                self.assertEqual(corrected_run_id, inspected["run_id"])
                self.assertFalse(
                    inspected["summary"]["diagnostics"][
                        "semantic_state_changed"
                    ]
                )
                self.assertEqual(
                    operation.value,
                    inspected["summary"]["operation_result"]["operation"],
                )

        transition = self.host.inspect_binding(
            corrected_run_id,
            view=InspectionView.TRANSITION,
        )
        reconstruction = self.host.inspect_binding(
            corrected_run_id,
            view=InspectionView.RECONSTRUCTION,
        )
        parent_revision_id = reconstruction["revision"]["parent_revision_ids"][0]
        reversed_result = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.REVERSE,
                prompt="Undo the deadline correction.",
                parent_run_id=corrected_run_id,
                reversal=ReversalPlan(
                    target_transition_artifact_id=transition["artifact_id"],
                    restore_parent_revision_id=parent_revision_id,
                    rationale="The user explicitly selected the deadline transition.",
                    evidence_references=("fixture:reverse",),
                ),
                treatment_label="structured_reversal",
            )
        )
        reversed_state = self.host.inspect_binding(str(reversed_result["run_id"]))
        self.assertEqual(
            {
                "project": "Cedar",
                "color": "green",
                "deadline": "Friday",
            },
            _values(reversed_state, "achieved"),
        )
        self.assertEqual(
            corrected_run_id,
            reversed_result["parent_run_id"],
        )
        self.assertNotEqual(corrected_digest, reversed_result["binding"]["resumption_identity"]["state_digest"])

        head_before_ambiguous_request = str(reversed_result["run_id"])
        with self.assertRaisesRegex(ValueError, "explicit reversal proposal"):
            self.host.submit_plan(
                ConversationTurnPlan(
                    operation=OperationKind.REVERSE,
                    prompt="Change it back.",
                    parent_run_id=head_before_ambiguous_request,
                    treatment_label="ambiguous_reversal",
                )
            )
        self.assertEqual(
            reversed_state,
            self.host.inspect_binding(head_before_ambiguous_request),
        )

    def test_branches_stale_anchors_and_unbound_prose_preserve_identity(self) -> None:
        baseline = self._corrected_brief()
        baseline_run_id = str(baseline["run_id"])

        executive = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.BRANCH,
                prompt="Prepare an executive version of the Cedar brief.",
                parent_run_id=baseline_run_id,
                target_branch_id="executive",
                treatment_label="structured_branch",
            )
        )
        technical = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.BRANCH,
                prompt="Prepare a technical version of the Cedar brief.",
                parent_run_id=baseline_run_id,
                target_branch_id="technical",
                treatment_label="structured_branch",
            )
        )
        self.assertNotEqual(executive["run_id"], technical["run_id"])
        self.assertEqual(
            "executive",
            executive["binding"]["resumption_identity"]["branch_id"],
        )
        self.assertEqual(
            "technical",
            technical["binding"]["resumption_identity"]["branch_id"],
        )
        for branch in (executive, technical):
            with self.subTest(branch=branch["run_id"]):
                state = self.host.inspect_binding(str(branch["run_id"]))
                self.assertEqual(
                    {
                        "project": "Cedar",
                        "color": "green",
                        "deadline": "Monday",
                    },
                    _values(state, "achieved"),
                )
                self.assertIn("audience", _values(state, "non_achievedness"))

        merged = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.MERGE,
                prompt="Merge the executive and technical brief branches.",
                parent_run_id=str(executive["run_id"]),
                merge_parent_run_ids=(str(technical["run_id"]),),
                treatment_label="structured_merge",
            )
        )
        merged_reconstruction = self.host.inspect_binding(
            str(merged["run_id"]),
            view=InspectionView.RECONSTRUCTION,
        )
        self.assertEqual(
            {str(executive["run_id"]), str(technical["run_id"])},
            set(merged_reconstruction["revision"]["parent_revision_ids"]),
        )
        self.assertIn(
            "audience",
            _values(
                self.host.inspect_binding(str(merged["run_id"])),
                "non_achievedness",
            ),
        )

        advanced_technical = self._correct(
            str(technical["run_id"]),
            key="deadline",
            value="Wednesday",
            version="technical-v3",
        )
        stale = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.AUGMENT,
                prompt="Add one stale technical note.",
                parent_run_id=str(technical["run_id"]),
                semantic_delta=SemanticDelta(
                    achieved=(_item("stale_note", "must not commit"),),
                ),
                treatment_label="stale_augmentation",
            )
        )
        self.assertEqual("stale", stale["run_outcome"])
        advanced_state = self.host.inspect_binding(
            str(advanced_technical["run_id"])
        )
        self.assertEqual("Wednesday", _values(advanced_state, "achieved")["deadline"])
        self.assertNotIn("stale_note", _values(advanced_state, "achieved"))

        unrelated = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.START,
                prompt="Plan a weekend hiking trip.",
                governing_direction=GoverningDirection(
                    objective="Plan a weekend hiking trip",
                    scope=self.host.scope_id,
                    required_outcome="A hiking plan",
                ),
                semantic_delta=SemanticDelta(
                    non_achievedness=(
                        _requirement("trail", "A trail is not selected"),
                    ),
                ),
                treatment_label="independent",
            )
        )
        unrelated_state = self.host.inspect_binding(str(unrelated["run_id"]))
        self.assertEqual({}, _values(unrelated_state, "achieved"))
        self.assertEqual(
            {"trail": "A trail is not selected"},
            _values(unrelated_state, "non_achievedness"),
        )

        unbound_configuration = EngineConfiguration(
            sqlite_path=self.host.sqlite_path,
            max_steps=0,
            llm_policy="off",
            discovery="off",
            reflection="off",
            contemplation="off",
        )
        for name, prompt in (
            ("similarity", "Continue the greenish project plan."),
            (
                "prose",
                "Continue from this sentence alone: Cedar uses green.",
            ),
        ):
            with self.subTest(unbound_attempt=name):
                unbound = CoreConversationHost(
                    root=self.root.parent / f"unbound-{name}",
                    configuration=unbound_configuration,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "No governed run binding is available",
                ):
                    unbound.submit_plan(
                        ConversationTurnPlan(
                            operation=OperationKind.CONTINUE,
                            prompt=prompt,
                            treatment_label=f"unbound_{name}",
                        )
                    )

    def test_interruption_and_resume_exclude_unfinished_candidate_work(self) -> None:
        baseline = self._corrected_brief()
        baseline_run_id = str(baseline["run_id"])
        baseline_state = self.host.inspect_binding(baseline_run_id)
        attempt_running = threading.Event()
        attempt_ids: list[str] = []
        submitted: dict[str, object] = {}
        failures: list[BaseException] = []

        def observe_attempt(attempt_id: str) -> None:
            attempt_ids.append(attempt_id)
            attempt_running.set()

        plan = ConversationTurnPlan(
            operation=OperationKind.AUGMENT,
            prompt="Add an unfinished launch channel proposal.",
            parent_run_id=baseline_run_id,
            semantic_delta=SemanticDelta(
                achieved=(_item("audience", "city officials", version="candidate"),),
            ),
            treatment_label="interrupted_augmentation",
        )

        def submit() -> None:
            try:
                submitted["result"] = self.host.submit_plan(
                    plan,
                    on_attempt_running=observe_attempt,
                )
            except BaseException as exc:  # pragma: no cover - asserted below
                failures.append(exc)

        from realized_core_engine.canonical_reduction import (
            CanonicalReductionAdapter,
        )

        original_reduce = CanonicalReductionAdapter.reduce

        def blocked_reduce(adapter, context, *, should_stop):
            while not should_stop():
                threading.Event().wait(0.005)
            return original_reduce(
                adapter,
                context,
                should_stop=should_stop,
            )

        with patch.object(CanonicalReductionAdapter, "reduce", blocked_reduce):
            worker = threading.Thread(target=submit, daemon=True)
            worker.start()
            self.assertTrue(attempt_running.wait(timeout=2))
            self.assertEqual(1, len(attempt_ids))
            interruption = self.host.interrupt(
                attempt_ids[0],
                reason="The user stopped the in-flight turn.",
            )
            worker.join(timeout=2)

        self.assertFalse(worker.is_alive())
        self.assertEqual([], failures)
        self.assertEqual("accepted", interruption["disposition"])
        self.assertFalse(interruption["semantic_revision_created"])
        interrupted = submitted["result"]
        self.assertEqual(
            "interrupted",
            interrupted["binding"]["execution_outcome"],
        )
        self.assertEqual(
            baseline_state,
            self.host.inspect_binding(baseline_run_id),
        )
        self.assertNotIn(
            "city officials",
            _values(self.host.inspect_binding(baseline_run_id), "achieved").values(),
        )
        self.assertNotIn(
            "audience",
            _values(self.host.inspect_binding(baseline_run_id), "achieved"),
        )

        resumed = self.host.submit_plan(
            ConversationTurnPlan(
                operation=OperationKind.RESUME_AFTER_INTERRUPTION,
                prompt="Resume from the last admitted Cedar state.",
                parent_run_id=baseline_run_id,
                source_attempt_id=attempt_ids[0],
                treatment_label="resume_after_interruption",
            )
        )
        resumed_state = self.host.inspect_binding(str(resumed["run_id"]))
        self.assertNotIn("audience", _values(resumed_state, "achieved"))
        self.assertEqual(
            _values(baseline_state, "achieved"),
            _values(resumed_state, "achieved"),
        )


if __name__ == "__main__":
    unittest.main()
