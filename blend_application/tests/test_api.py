from __future__ import annotations

import unittest

import realized_blend_application
from realized_blend_application import (
    execution,
    operators,
    workflow_store,
    workflows,
    world_store,
    worlds,
)


class BlendApplicationApiTests(unittest.TestCase):
    def test_public_surface_is_explicit(self) -> None:
        self.assertEqual(
            [
                "execution",
                "operators",
                "workflow_store",
                "workflows",
                "world_store",
                "worlds",
            ],
            realized_blend_application.__all__,
        )

    def test_public_modules_expose_adapter_operations(self) -> None:
        self.assertTrue(callable(operators.blend_skill_operator_record_from_artifact))
        self.assertTrue(callable(workflows.blend_workflow_plan_from_skill_compose_arguments))
        self.assertTrue(callable(execution.execute_blend_workflow))
        self.assertTrue(callable(workflow_store.persist_blend_workflow_objects))
        self.assertTrue(callable(world_store.ensure_persisted_blend_workstation_world))
        self.assertTrue(callable(worlds.ensure_blend_workstation_world))


if __name__ == "__main__":
    unittest.main()
