from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_ENGINE_SRC = REPO_ROOT / "core_engine" / "src"
if str(CORE_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_ENGINE_SRC))

from realized_core_engine import (
    EngineConfiguration,
    EngineResult,
    inspect,
    resume,
    run,
)


class CoreEngineApiTests(unittest.TestCase):
    def test_run_applies_typed_configuration_and_plain_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            state_path = root / "run.json"
            evidence_path = root / "evidence.json"
            evidence_path.write_text(
                json.dumps(
                    [
                        {
                            "target": "root",
                            "observation": "A deterministic supporting observation.",
                            "source": "test",
                            "support_strength": "high",
                            "confidence": "high",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            configuration = EngineConfiguration(
                evidence_path=evidence_path,
                state_output_path=state_path,
                sqlite_path=sqlite_path,
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
                prolog_query_priming="force",
                supported_executors=("python3", "bash"),
            )

            with patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "",
                    "STATE_VECTOR_MODE": "on",
                },
                clear=False,
            ):
                result = run(
                    "Exercise the public engine ABI.",
                    configuration=configuration,
                )

                self.assertEqual("off", os.environ["STATE_VECTOR_MODE"])
                self.assertEqual(str(sqlite_path), os.environ["STATE_SQLITE_PATH"])
                self.assertEqual("force", os.environ["BSSC_PROLOG_QUERY_PRIMING"])

            self.assertIsInstance(result, EngineResult)
            self.assertTrue(sqlite_path.is_file())
            self.assertTrue(state_path.is_file())
            self.assertEqual(
                "Exercise the public engine ABI.",
                result.summary["root"]["semantic_unit"],
            )
            self.assertEqual(1, result.summary["counts"]["evidence"])
            self.assertEqual(
                {
                    "contemplation_enabled": False,
                    "discovery_enabled": False,
                    "reflection_enabled": False,
                    "supported_executors": ["python3", "bash"],
                },
                result.summary["controller_features"],
            )
            self.assertFalse(result.summary["llm"]["artifact_store"]["vector_enabled"])

    def test_resume_and_inspect_preserve_the_durable_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            sqlite_path = root / "state.sqlite3"
            initial_state_path = root / "initial.json"
            resumed_state_path = root / "resumed.json"
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                run(
                    "Resume through the public engine ABI.",
                    configuration=EngineConfiguration(
                        state_output_path=initial_state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                    ),
                )
                resumed = resume(
                    initial_state_path,
                    configuration=EngineConfiguration(
                        state_output_path=resumed_state_path,
                        sqlite_path=sqlite_path,
                        max_steps=0,
                        llm_policy="off",
                    ),
                )
                inspected = inspect(resumed_state_path)

            self.assertTrue(resumed_state_path.is_file())
            for stable_key in (
                "controller_features",
                "counts",
                "final_answer",
                "frontier",
                "nodes",
                "root",
                "run_id",
                "run_outcome",
                "theory_version",
            ):
                with self.subTest(stable_key=stable_key):
                    self.assertEqual(
                        resumed.summary[stable_key],
                        inspected.summary[stable_key],
                    )


if __name__ == "__main__":
    unittest.main()
