from __future__ import annotations

import unittest

from realized_core_runtime import (
    PerformanceRecorder,
    measured_performance,
    merge_performance_measurements,
    performance_scope,
)


class PerformanceTelemetryTests(unittest.TestCase):
    def test_nested_measurements_are_context_local_and_additive(self) -> None:
        recorder = PerformanceRecorder()

        @measured_performance("proposal_latency_ns")
        def propose() -> int:
            return sum(range(100))

        self.assertEqual(4950, propose())
        self.assertEqual({}, recorder.snapshot())

        with performance_scope(recorder):
            self.assertEqual(4950, propose())
            self.assertEqual(4950, propose())

        self.assertGreater(recorder.snapshot()["proposal_latency_ns"], 0)

    def test_measurement_merge_adds_layers_without_overwriting(self) -> None:
        merged = merge_performance_measurements(
            {"reduction_latency_ns": 4},
            {"reduction_latency_ns": 6, "effect_latency_ns": 3},
        )

        self.assertEqual(
            {"effect_latency_ns": 3, "reduction_latency_ns": 10},
            merged,
        )


if __name__ == "__main__":
    unittest.main()
