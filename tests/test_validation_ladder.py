# See MODULES.md for the repository module map before editing.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from args import parse_args
from realized_validation import ladder as packaged_validation_ladder
import validation_ladder
from validation_ladder import run_validation_ladder


class ValidationLadderTests(unittest.TestCase):
    """
    High Level Purpose:
        In circumstances like stabilization-work validation infrastructure changes, helps with verifying that the layered validation ladder runs the expected stages in order and stops cleanly on failure.

    Reference to Theory:
        Verifies the implemented validation doctrine around layered acceptance and staged observability without changing controller semantics.

    Example Input Output:
        Input: `ValidationLadderTests().test_run_validation_ladder_stops_after_unit_failure()`
        Output: None

    Args:
        self: Bound test case instance.

    Returns:
        None: This function mutates state or performs side effects without returning a value.
    """

    def test_historical_module_is_exact_package_alias(self) -> None:
        self.assertIs(validation_ladder, packaged_validation_ladder)

    def test_run_validation_ladder_runs_all_stages_and_loads_nested_reports(self) -> None:
        """
        High Level Purpose:
            In circumstances like green layered acceptance execution, helps with proving that the ladder runs unit tests, workstation trials, and chemistry validation in order and captures nested stage reports.

        Reference to Theory:
            Verifies the implemented validation doctrine around layered acceptance and staged observability without changing controller semantics.

        Example Input Output:
            Input: `test_run_validation_ladder_runs_all_stages_and_loads_nested_reports()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            report_root = Path(tmp) / "validation_ladder"
            workstation_report_out = report_root / "workstation_trial_validation_report.json"
            chemistry_report_path = report_root / "chemistry_domain_validation" / "report.json"

            seen_vector_modes: list[str] = []

            def fake_runner(*, name, cmd, cwd, env):
                calls.append(name)
                seen_vector_modes.append(env.get("STATE_VECTOR_MODE", ""))
                if name == "workstation_trials":
                    workstation_report_out.write_text(json.dumps({"status": "ok", "kind": "workstation"}))
                if name == "chemistry_domain":
                    chemistry_report_path.parent.mkdir(parents=True, exist_ok=True)
                    chemistry_report_path.write_text(json.dumps({"status": "ok", "kind": "chemistry"}))
                return {
                    "name": name,
                    "cmd": cmd,
                    "cwd": str(cwd),
                    "status": "ok",
                    "returncode": 0,
                    "elapsed_seconds": 0.01,
                    "stdout_tail": "",
                    "stderr_tail": "",
                }

            report = run_validation_ladder(
                workspace=Path("/tmp/workspace"),
                report_root=report_root,
                runner=fake_runner,
            )

            self.assertEqual(calls, ["unit_tests", "workstation_trials", "chemistry_domain"])
            self.assertEqual(report["status"], "ok")
            self.assertEqual(len(report["stages"]), 3)
            self.assertEqual(report["stages"][1]["nested_report"], {"status": "ok", "kind": "workstation"})
            self.assertEqual(report["stages"][2]["nested_report"], {"status": "ok", "kind": "chemistry"})
            self.assertEqual(seen_vector_modes, ["off", "off", "off"])

    def test_run_validation_ladder_stops_after_unit_failure(self) -> None:
        """
        High Level Purpose:
            In circumstances like an early failure in the layered acceptance ladder, helps with proving that later layers do not run and the top-level report records the failed state.

        Reference to Theory:
            Verifies the implemented validation doctrine around layered acceptance and staged observability without changing controller semantics.

        Example Input Output:
            Input: `test_run_validation_ladder_stops_after_unit_failure()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        calls: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            report_root = Path(tmp) / "validation_ladder"

            def fake_runner(*, name, cmd, cwd, env):
                calls.append(name)
                return {
                    "name": name,
                    "cmd": cmd,
                    "cwd": str(cwd),
                    "status": "failed",
                    "returncode": 1,
                    "elapsed_seconds": 0.01,
                    "stdout_tail": "",
                    "stderr_tail": "boom",
                }

            report = run_validation_ladder(
                workspace=Path("/tmp/workspace"),
                report_root=report_root,
                runner=fake_runner,
            )

            self.assertEqual(calls, ["unit_tests"])
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["stage"], "unit_tests")
            self.assertEqual(len(report["stages"]), 1)
            persisted = json.loads((report_root / "report.json").read_text())
            self.assertEqual(persisted["status"], "failed")

    def test_parse_args_keeps_validation_ladder_as_explicit_subcommand(self) -> None:
        """
        High Level Purpose:
            In circumstances like CLI normalization for convenience run prompts, helps with proving that `validation-ladder` remains an explicit subcommand instead of being rewritten into `run --prompt`.

        Reference to Theory:
            Verifies the implemented validation doctrine around layered acceptance entry points without changing controller semantics.

        Example Input Output:
            Input: `test_parse_args_keeps_validation_ladder_as_explicit_subcommand()`
            Output: None

        Args:
            self: Bound instance that owns the runtime state used by this method.

        Returns:
            None: This function mutates state or performs side effects without returning a value.
        """
        args = parse_args(["validation-ladder", "--workspace", "/tmp/workspace"])
        self.assertEqual(args.command, "validation-ladder")
        self.assertEqual(Path(args.workspace), Path("/tmp/workspace"))
