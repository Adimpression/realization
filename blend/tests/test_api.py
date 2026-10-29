from __future__ import annotations

import unittest

import realized_blend
from realized_blend import (
    actors,
    context,
    coordination,
    execution,
    history,
    observations,
    operators,
    ports,
    sessions,
    workflows,
    worlds,
)


class BlendApiTests(unittest.TestCase):
    def test_package_exports_only_the_cohesive_contract_modules(self) -> None:
        expected = [
            "actors",
            "context",
            "coordination",
            "execution",
            "history",
            "observations",
            "operators",
            "ports",
            "sessions",
            "workflows",
            "worlds",
        ]

        self.assertEqual(expected, realized_blend.__all__)
        for name in expected:
            with self.subTest(name=name):
                self.assertIs(getattr(realized_blend, name), globals()[name])

    def test_module_exports_are_explicit_unique_and_resolvable(self) -> None:
        for module in (
            actors,
            context,
            coordination,
            execution,
            history,
            observations,
            operators,
            ports,
            sessions,
            workflows,
            worlds,
        ):
            with self.subTest(module=module.__name__):
                self.assertEqual(len(module.__all__), len(set(module.__all__)))
                for name in module.__all__:
                    self.assertTrue(hasattr(module, name), name)

    def test_structural_actor_history_and_coordination_values_round_trip(self) -> None:
        values = (
            actors.BlendActor(
                actor_id="actor-1",
                actor_kind="person",
                display_name="Operator",
                capability_envelope=("review", "approve"),
                metadata={"team": "release"},
            ),
            history.BlendHistoryRecord(
                record_id="history-1",
                aggregate_kind="workflow",
                aggregate_id="workflow-1",
                transition="completed",
                sequence=3,
                recorded_at="2026-10-27T00:00:00+00:00",
                actor_id="actor-1",
                session_id="session-1",
                workflow_id="workflow-1",
                workflow_run_id="run-1",
                receipt_refs=("receipt-1",),
                provenance_refs=("source-1",),
                metadata={"verified": True},
            ),
            coordination.BlendCoordinationRecord(
                coordination_id="coordination-1",
                coordination_kind="review",
                status="open",
                subject_kind="workflow",
                subject_id="workflow-1",
                created_at="2026-10-27T00:00:00+00:00",
                updated_at="2026-10-27T00:01:00+00:00",
                participant_actor_ids=("actor-1", "actor-2"),
                authority_refs=("authority-1",),
                payload={"stage": "review"},
                metadata={"priority": 1},
            ),
        )

        for value in values:
            with self.subTest(value=type(value).__name__):
                self.assertEqual(value, type(value).from_dict(value.to_dict()))

    def test_execution_observation_alias_has_one_identity(self) -> None:
        self.assertIs(
            observations.BlendExecutionObservation,
            observations.BlendWorkflowExecutionEvent,
        )

    def test_operator_catalog_contract_is_public(self) -> None:
        for name in (
            "BlendOperatorProvider",
            "BlendOperatorRecord",
            "get_blend_operator_summary",
            "list_blend_operator_summaries",
            "new_blend_capability_operator_provider",
            "resolve_blend_operator_record",
            "resolve_blend_operator_record_for_workflow_step",
        ):
            with self.subTest(name=name):
                self.assertIn(name, operators.__all__)
                self.assertTrue(hasattr(operators, name))

    def test_workflow_execution_contract_is_public(self) -> None:
        for name in (
            "BlendResolvedWorkflowStep",
            "BlendWorkflowExecutionHalt",
            "execute_blend_workflow",
            "resolve_blend_workflow_steps",
            "resolve_blend_workflow_steps_from_providers",
        ):
            with self.subTest(name=name):
                self.assertIn(name, execution.__all__)
                self.assertTrue(hasattr(execution, name))


if __name__ == "__main__":
    unittest.main()
