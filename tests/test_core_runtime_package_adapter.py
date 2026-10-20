from __future__ import annotations

import unittest
from unittest.mock import patch

import governed_semantic_reduction_runtime as legacy_runtime
from applied_theory_types import NodeStatus
from controller_runtime import BSSCController
from realized_core_runtime import RealizationResumePort, RealizationRunPort
from system_state import SystemState


class CoreRuntimePackageAdapterTests(unittest.TestCase):
    def test_controller_keeps_historical_run_and_resume_method_identities(self) -> None:
        self.assertIs(legacy_runtime.run, BSSCController.run)
        self.assertIs(legacy_runtime.resume, BSSCController.resume)

    def test_controller_satisfies_the_public_lifecycle_ports(self) -> None:
        controller = BSSCController(
            SystemState.bootstrap("Verify the core runtime port."),
            llm_policy="off",
        )

        self.assertIsInstance(controller, RealizationRunPort)
        self.assertIsInstance(controller, RealizationResumePort)

    def test_historical_run_delegates_to_extracted_lifecycle(self) -> None:
        runtime = object()
        result = object()

        with patch.object(
            legacy_runtime,
            "run_to_realization",
            return_value=result,
        ) as delegated:
            actual = legacy_runtime.run(runtime, max_steps=7)

        self.assertIs(result, actual)
        delegated.assert_called_once_with(runtime, max_steps=7)

    def test_historical_resume_delegates_with_the_existing_open_status(self) -> None:
        runtime = object()
        result = object()

        with patch.object(
            legacy_runtime,
            "resume_to_realization",
            return_value=result,
        ) as delegated:
            actual = legacy_runtime.resume(runtime, max_steps=11)

        self.assertIs(result, actual)
        delegated.assert_called_once_with(
            runtime,
            open_status=NodeStatus.OPEN,
            max_steps=11,
        )


if __name__ == "__main__":
    unittest.main()
