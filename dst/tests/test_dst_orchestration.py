import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from realized_core_semantics.applied_model import ProposalType
from coordinated_transformation import executable_decisions, valid_decisions
from dst import (
    DstControllerBootstrapUnavailable,
    bootstrap_dst_discovery_controller,
    build_live_dst_fixture_for_itemized_item,
    build_reduce_not_discovery_prompt_packet,
    discovery_result_from_fixture,
    load_dst_normalized_cases,
    load_dst_use_cases,
    normalized_case_from_fixture,
    run_live_dst_construct_discovery_for_itemized_item,
    run_live_dst_pipeline_from_fixture,
    run_dst_pipeline_from_fixture,
    run_runtime_dst_discovery,
    run_runtime_dst_normalization,
)
from realized_core_semantics.itemization import ItemizedSubjectItem


class DstOrchestrationTests(unittest.TestCase):
    def _manual_item(self) -> ItemizedSubjectItem:
        return ItemizedSubjectItem(
            itemized_item_id="itm_bus_authority",
            subject_id="bus-demo",
            item_kind="decision_role_candidate",
            canonical_label="Transit Agency",
            summary="The transit agency decides how fare collection is modernized.",
            source_refs=("notes/bus.md",),
            confidence=0.84,
            status="candidate",
            metadata={"decision_role": "actor"},
        )

    def test_build_reduce_not_discovery_prompt_packet_carries_root_and_prompt(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        packet = build_reduce_not_discovery_prompt_packet(fixture)

        self.assertEqual(packet.fixture_id, fixture.fixture_id)
        self.assertEqual(packet.source_ref, fixture.source_ref)
        self.assertTrue(packet.root_non_achievedness.startswith("What are the materially distinct admissible transformation paths"))
        self.assertIn("DST sort-atom lexicon:", packet.prompt)
        self.assertIn("candidate_path_families", packet.prompt)

    def test_build_live_dst_fixture_for_itemized_item_centers_the_selected_item_and_seed_context(self) -> None:
        selected_item = self._manual_item()

        fixture = build_live_dst_fixture_for_itemized_item(
            selected_item,
            subject_title="Bus modernization note",
            subject_summary="A city bus operator needs to choose how to modernize fare collection.",
            subject_source_refs=("notes/bus.md",),
            supporting_items=(
                selected_item,
                ItemizedSubjectItem(
                    itemized_item_id="itm_dependency",
                    subject_id="bus-demo",
                    item_kind="decision_role_candidate",
                    canonical_label="Payment Processor",
                    summary="External payment connectivity must be available.",
                    source_refs=("notes/bus.md",),
                    confidence=0.78,
                    status="candidate",
                    metadata={"decision_role": "dependency"},
                ),
            ),
        )

        self.assertEqual(fixture.title, "Bus modernization note")
        self.assertEqual(fixture.source_ref, "notes/bus.md")
        self.assertIn("Selected item: Transit Agency", fixture.summary)
        self.assertIn("Nearby itemized inventory: Payment Processor", fixture.summary)
        self.assertIn("actors", [section.key for section in fixture.sections])
        self.assertIn("dependencies", [section.key for section in fixture.sections])

    def test_run_dst_pipeline_from_fixture_executes_discovery_then_normalization_and_builds_outputs(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        normalized_case = next(
            item for item in load_dst_normalized_cases()
            if item.fixture_id == fixture.fixture_id
        )
        calls: list[tuple[str, str]] = []

        def fake_discovery_runner(*, prompt: str, fixture, root_non_achievedness: str) -> dict[str, object]:
            calls.append(("discovery", fixture.fixture_id))
            self.assertIn("DST sort-atom lexicon:", prompt)
            self.assertIn(root_non_achievedness, prompt)
            return discovery_result_from_fixture(fixture).to_dict()

        def fake_normalization_runner(*, prompt_input: str, fixture, discovery) -> dict[str, object]:
            calls.append(("normalization", fixture.fixture_id))
            self.assertIn("Governed discovery candidate paths:", prompt_input)
            self.assertIn("Governed discovery sort atom context:", prompt_input)
            self.assertEqual(discovery.fixture_id, fixture.fixture_id)
            return normalized_case.to_dict()

        result = run_dst_pipeline_from_fixture(
            fixture,
            discovery_runner=fake_discovery_runner,
            normalization_runner=fake_normalization_runner,
            build_epoch_ms=7,
        )

        self.assertEqual(calls, [("discovery", fixture.fixture_id), ("normalization", fixture.fixture_id)])
        self.assertEqual(result.normalized_case.fixture_id, fixture.fixture_id)
        self.assertEqual(result.decision_projection.frame.subject_id, fixture.fixture_id)
        self.assertEqual(result.decision_projection.frame.question, normalized_case.context.decision_problem)
        self.assertEqual(result.decision_projection.candidate_transition_ids, ("t1", "t3"))
        current_state = next(iter(result.coordinated_model.current))
        self.assertEqual([decision.name for decision in valid_decisions(result.coordinated_model, current_state)], ["Start with closed-loop upgrade"])
        self.assertEqual([decision.name for decision in executable_decisions(result.coordinated_model, current_state)], ["Start with closed-loop upgrade"])

    def test_bootstrap_dst_discovery_controller_uses_root_non_achievedness_as_runtime_semantic_unit(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        state = SimpleNamespace(supplement_profile={})
        controller = object()
        captured: dict[str, object] = {}

        def _bootstrap(**kwargs):
            captured.update(kwargs)
            return state, controller

        result_state, result_controller, packet = bootstrap_dst_discovery_controller(
            fixture,
            llm_policy="off",
            subject_scope={"subject_id": "city-bus"},
            subject_scope_root_path=Path("/tmp/city-bus"),
            controller_bootstrap=_bootstrap,
        )

        self.assertIs(result_state, state)
        self.assertIs(result_controller, controller)
        self.assertEqual(captured["semantic_unit"], packet.root_non_achievedness)
        self.assertEqual(captured["llm_policy"], "off")
        self.assertEqual(captured["subject_scope"], {"subject_id": "city-bus"})
        self.assertEqual(captured["subject_scope_root_path"], Path("/tmp/city-bus"))
        self.assertEqual(
            state.supplement_profile["dst_discovery_root_non_achievedness"],
            packet.root_non_achievedness,
        )
        self.assertEqual(
            state.supplement_profile["dst_discovery_fixture_id"],
            fixture.fixture_id,
        )
        self.assertIn("candidate_path_families", packet.prompt)

    def test_bootstrap_dst_discovery_controller_fails_closed_without_runtime_realization(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )

        with self.assertRaisesRegex(
            DstControllerBootstrapUnavailable,
            "explicit controller bootstrap realization",
        ):
            bootstrap_dst_discovery_controller(fixture, llm_policy="off")

    def test_run_runtime_dst_discovery_uses_explicit_dst_discovery_proposal_type(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "city-bus-ticketing-modernization"
        )
        packet = build_reduce_not_discovery_prompt_packet(fixture)
        node = SimpleNamespace(metadata={})
        captured: dict[str, object] = {}

        class FakeController:
            def request_proposal(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(id="proposal-discovery", payload=discovery_result_from_fixture(fixture).to_dict())

            def admit_proposal(self, proposal, *, rationale: str):
                captured["admit_rationale"] = rationale
                return proposal

        result, proposal_id = run_runtime_dst_discovery(
            FakeController(),
            fixture,
            node=node,
            prompt_packet=packet,
        )

        self.assertEqual(proposal_id, "proposal-discovery")
        self.assertEqual(captured["proposal_type"], ProposalType.DST_DISCOVERY)
        self.assertEqual(captured["target_scope"], fixture.fixture_id)
        self.assertIn("DST sort-atom lexicon:", str(captured["instructions"]))
        self.assertIn("sort_atom_context", str(captured["schema_hint"]))
        self.assertEqual(node.metadata["dst_discovery_proposal_id"], "proposal-discovery")
        self.assertEqual(result.fixture_id, fixture.fixture_id)

    def test_run_runtime_dst_normalization_uses_explicit_dst_normalization_proposal_type(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "hospital-medication-system-upgrade"
        )
        discovery = discovery_result_from_fixture(fixture)
        node = SimpleNamespace(metadata={})
        captured: dict[str, object] = {}
        normalized = normalized_case_from_fixture(fixture, discovery)

        class FakeController:
            def request_proposal(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(id="proposal-normalization", payload=normalized.to_dict())

            def admit_proposal(self, proposal, *, rationale: str):
                captured["admit_rationale"] = rationale
                return proposal

        prompt_input, case, proposal_id = run_runtime_dst_normalization(
            FakeController(),
            fixture,
            discovery,
            node=node,
        )

        self.assertEqual(proposal_id, "proposal-normalization")
        self.assertEqual(captured["proposal_type"], ProposalType.DST_NORMALIZATION)
        self.assertIn("INPUT TO NORMALIZE", str(captured["instructions"]))
        self.assertIn("Governed discovery candidate paths:", prompt_input)
        self.assertIn("candidate_sets", str(captured["schema_hint"]))
        self.assertEqual(node.metadata["dst_normalization_proposal_id"], "proposal-normalization")
        self.assertEqual(case.fixture_id, fixture.fixture_id)

    def test_run_live_dst_pipeline_from_fixture_uses_runtime_proposal_surface_end_to_end(self) -> None:
        fixture = next(
            item for item in load_dst_use_cases()
            if item.fixture_id == "hospital-medication-system-upgrade"
        )
        discovery = discovery_result_from_fixture(fixture)
        normalized = normalized_case_from_fixture(fixture, discovery)
        node = SimpleNamespace(metadata={})
        call_types: list[ProposalType] = []

        class FakeState:
            def __init__(self) -> None:
                self.supplement_profile = {}

            def root(self):
                return node

        class FakeController:
            def request_proposal(self, **kwargs):
                call_types.append(kwargs["proposal_type"])
                if kwargs["proposal_type"] == ProposalType.DST_DISCOVERY:
                    return SimpleNamespace(id="proposal-discovery", payload=discovery.to_dict())
                if kwargs["proposal_type"] == ProposalType.DST_NORMALIZATION:
                    return SimpleNamespace(id="proposal-normalization", payload=normalized.to_dict())
                raise AssertionError(f"unexpected proposal type: {kwargs['proposal_type']}")

            def admit_proposal(self, proposal, *, rationale: str):
                return proposal

        fake_state = FakeState()
        bootstrap_calls: list[dict[str, object]] = []

        def _bootstrap(**kwargs):
            bootstrap_calls.append(dict(kwargs))
            return fake_state, FakeController()

        result = run_live_dst_pipeline_from_fixture(
            fixture,
            build_epoch_ms=11,
            controller_bootstrap=_bootstrap,
        )

        self.assertEqual(len(bootstrap_calls), 1)
        self.assertEqual(bootstrap_calls[0]["llm_policy"], "required")
        self.assertIn("transformation", str(bootstrap_calls[0]["semantic_unit"]).lower())
        self.assertEqual(call_types, [ProposalType.DST_DISCOVERY, ProposalType.DST_NORMALIZATION])
        self.assertEqual(result.discovery_proposal_id, "proposal-discovery")
        self.assertEqual(result.normalization_proposal_id, "proposal-normalization")
        self.assertEqual(result.normalized_case.fixture_id, fixture.fixture_id)
        self.assertEqual(result.decision_projection.frame.subject_id, fixture.fixture_id)
        self.assertEqual(node.metadata["dst_discovery_proposal_id"], "proposal-discovery")
        self.assertEqual(node.metadata["dst_normalization_proposal_id"], "proposal-normalization")

    def test_run_live_dst_construct_discovery_for_itemized_item_projects_normalized_case_into_construct_candidates(self) -> None:
        selected_item = self._manual_item()
        fixture = build_live_dst_fixture_for_itemized_item(
            selected_item,
            subject_title="Bus modernization note",
            subject_summary="A city bus operator needs to choose how to modernize fare collection.",
            subject_source_refs=("notes/bus.md",),
            supporting_items=(selected_item,),
        )
        orchestration_result = run_dst_pipeline_from_fixture(
            fixture,
            discovery_runner=lambda **runner_kwargs: discovery_result_from_fixture(
                runner_kwargs["fixture"]
            ).to_dict(),
            normalization_runner=lambda **runner_kwargs: normalized_case_from_fixture(
                runner_kwargs["fixture"],
                runner_kwargs["discovery"],
            ).to_dict(),
            subject_id=selected_item.subject_id,
            build_epoch_ms=17,
        )

        with patch(
            "dst.orchestration.run_live_dst_pipeline_from_fixture",
            return_value=orchestration_result,
        ):
            result = run_live_dst_construct_discovery_for_itemized_item(
                selected_item,
                subject_title="Bus modernization note",
                subject_summary="A city bus operator needs to choose how to modernize fare collection.",
                subject_source_refs=("notes/bus.md",),
                supporting_items=(selected_item,),
                build_epoch_ms=17,
            )

        self.assertEqual(result.fixture.source_ref, "notes/bus.md")
        self.assertEqual(result.orchestration_result.normalized_case.fixture_id, fixture.fixture_id)
        self.assertGreater(len(result.construct_candidates), 0)
        self.assertIn("actor", {candidate.sort_kind for candidate in result.construct_candidates})
        self.assertTrue(
            all(
                candidate.relation_hints.get("dst_construct_source") == "dst_runtime"
                for candidate in result.construct_candidates
            )
        )


if __name__ == "__main__":
    unittest.main()
