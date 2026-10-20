# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from applied_theory_types import RuntimeDeterminismPolicy
from constitutional_trace import composition_chain_signature, controller_decision_flow_signature
from main import BSSCController
from system_state import SystemState


class ControllerDeterminismReplayPackTests(unittest.TestCase):
    def _run_deterministic_llm_off(
        self,
        prompt: str,
        *,
        max_steps: int,
        sqlite_path: Path,
    ) -> dict[str, object]:
        with patch.dict(
            os.environ,
            {
                "STATE_SQLITE_PATH": str(sqlite_path),
                "STATE_VECTOR_MODE": "off",
            },
            clear=False,
        ):
            state = SystemState.bootstrap(prompt)
            state.determinism_policy = RuntimeDeterminismPolicy(mode="deterministic", llm_strategy="off")
            controller = BSSCController(state, llm_policy="off")
            controller.run(max_steps=max_steps)
        return {
            "run_outcome": state.run_outcome.value,
            "final_answer": state.root_final_answer(),
            "composition_chain_signatures": composition_chain_signature(state),
            "decision_flow_signatures": controller_decision_flow_signature(state),
        }

    def test_deterministic_llm_off_is_stable_across_runs(self) -> None:
        cases = [
            {"prompt": "Say hi.", "max_steps": 32},
            {"prompt": "Compute force from mass and acceleration.", "max_steps": 64},
            {"prompt": "Explain why the sky is blue.", "max_steps": 64},
        ]

        with tempfile.TemporaryDirectory(prefix="controller_determinism_replay_") as tempdir:
            root = Path(tempdir)
            for index, case in enumerate(cases):
                prompt = str(case["prompt"])
                max_steps = int(case["max_steps"])
                with self.subTest(prompt=prompt):
                    first = self._run_deterministic_llm_off(
                        prompt,
                        max_steps=max_steps,
                        sqlite_path=root / f"case-{index}-first.sqlite3",
                    )
                    second = self._run_deterministic_llm_off(
                        prompt,
                        max_steps=max_steps,
                        sqlite_path=root / f"case-{index}-second.sqlite3",
                    )
                    self.assertEqual(first["run_outcome"], second["run_outcome"])
                    self.assertEqual(first["final_answer"], second["final_answer"])
                    self.assertEqual(first["composition_chain_signatures"], second["composition_chain_signatures"])
                    self.assertEqual(first["decision_flow_signatures"], second["decision_flow_signatures"])


if __name__ == "__main__":
    unittest.main()
