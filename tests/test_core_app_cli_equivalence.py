from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_APP_SRC = REPO_ROOT / "core_app" / "src"
if str(CORE_APP_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_APP_SRC))

from controller_entrypoints import main as application_main
from realized_core import cli as core_cli


def _normalized_runtime_projection(summary: dict[str, object]) -> dict[str, object]:
    node_keys = (
        "semantic_unit",
        "not",
        "role",
        "boundary_shape",
        "depth",
        "status",
        "certainty",
        "blockers",
    )
    return {
        "controller_features": summary["controller_features"],
        "counts": summary["counts"],
        "final_answer": summary["final_answer"],
        "frontier": [
            {
                "semantic_unit": row["semantic_unit"],
                "status": row["status"],
            }
            for row in summary["frontier"]
        ],
        "nodes": [
            {key: row[key] for key in node_keys}
            for row in summary["nodes"]
        ],
        "run_outcome": summary["run_outcome"],
        "theory_version": summary["theory_version"],
        "vector_enabled": summary["llm"]["artifact_store"]["vector_enabled"],
    }


class CoreApplicationCliEquivalenceTests(unittest.TestCase):
    def test_packaged_cli_matches_existing_run_behavior_on_fresh_sqlite(self) -> None:
        prompt = "Verify packaged behavior equivalence."
        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            application_sqlite = root / "application.sqlite3"
            application_state = root / "application.json"
            packaged_sqlite = root / "packaged.sqlite3"
            packaged_state = root / "packaged.json"
            with patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "", "STATE_VECTOR_MODE": "off"},
                clear=False,
            ):
                with patch.object(
                    sys,
                    "argv",
                    [
                        "main.py",
                        "run",
                        "--prompt",
                        prompt,
                        "--llm",
                        "off",
                        "--max-steps",
                        "0",
                        "--sqlite",
                        str(application_sqlite),
                        "--state-out",
                        str(application_state),
                    ],
                ), patch("builtins.print") as application_output:
                    self.assertEqual(0, application_main())

                with patch("builtins.print") as packaged_output:
                    self.assertEqual(
                        0,
                        core_cli.main(
                            [
                                "run",
                                "--prompt",
                                prompt,
                                "--llm",
                                "off",
                                "--max-steps",
                                "0",
                                "--sqlite",
                                str(packaged_sqlite),
                                "--state-out",
                                str(packaged_state),
                            ]
                        ),
                    )

            application_summary = json.loads(application_output.call_args.args[0])
            packaged_summary = json.loads(packaged_output.call_args.args[0])
            self.assertEqual(
                _normalized_runtime_projection(application_summary),
                _normalized_runtime_projection(packaged_summary),
            )
            self.assertTrue(application_sqlite.is_file())
            self.assertTrue(application_state.is_file())
            self.assertTrue(packaged_sqlite.is_file())
            self.assertTrue(packaged_state.is_file())


if __name__ == "__main__":
    unittest.main()
