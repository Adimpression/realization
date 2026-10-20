from __future__ import annotations

import unittest

from design.controllers import DriftDetector
from design.examples import EXAMPLE_MODULES
from design.revision import AlignmentStatus


class DesignExampleTests(unittest.TestCase):
    def test_all_case_study_examples_build_reference_bundles(self) -> None:
        expected_names = {
            "material_case_study",
            "physical_service_case_study",
            "high_risk_operational_case_study",
            "collaborative_workflow_case_study",
        }
        self.assertEqual(set(EXAMPLE_MODULES), expected_names)

        for name, module in EXAMPLE_MODULES.items():
            with self.subTest(example=name):
                snapshot, reality = module.get_reference_bundle()
                self.assertEqual(snapshot.metadata["case_study"], name)
                self.assertEqual(reality.metadata["case_study"], name)
                self.assertTrue(snapshot.objectives)
                self.assertTrue(snapshot.obligations)
                self.assertTrue(snapshot.embodiments)
                self.assertTrue(snapshot.encodings)
                self.assertTrue(reality.evidence)

    def test_examples_round_trip_through_drift_detection(self) -> None:
        detector = DriftDetector()
        expected_statuses = {
            "material_case_study": AlignmentStatus.DRIFTED,
            "physical_service_case_study": AlignmentStatus.DRIFTED,
            "high_risk_operational_case_study": AlignmentStatus.DRIFTED,
            "collaborative_workflow_case_study": AlignmentStatus.INVALIDATED,
        }

        for name, module in EXAMPLE_MODULES.items():
            with self.subTest(example=name):
                snapshot, reality = module.get_reference_bundle()
                drift = detector.detect(snapshot, reality)
                self.assertEqual(len(drift.alignment_checks), 1)
                self.assertEqual(
                    drift.alignment_checks[0].status,
                    expected_statuses[name],
                )
                self.assertTrue(drift.recompilation.required)


if __name__ == "__main__":
    unittest.main()
