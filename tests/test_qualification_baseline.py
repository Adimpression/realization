from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "capture_qualification_baseline.py"
SPEC = importlib.util.spec_from_file_location("capture_qualification_baseline", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
qualification = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualification)


def _gate(
    status: str,
    *,
    errors: list[str] | None = None,
    failures: list[str] | None = None,
) -> dict[str, object]:
    gate: dict[str, object] = {
        "artifacts": [],
        "id": "unit",
        "performance": {"median_seconds": 1.0, "p95_seconds": 1.0, "runs": 1},
        "status": status,
    }
    if errors is not None or failures is not None:
        gate["unittest"] = {
            "errors": errors or [],
            "failures": failures or [],
            "tests_run": 2,
        }
    return gate


def _baseline(gate: dict[str, object]) -> dict[str, object]:
    return {
        "gates": [gate],
        "policy": {
            "max_median_regression_percent": 10.0,
            "max_p95_regression_percent": 10.0,
        },
    }


class QualificationLogTest(unittest.TestCase):
    def test_log_normalization_removes_only_line_ending_padding(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "progress.log"
            log_path.write_bytes(b"first  \n second value \t\r\nthird\t")

            qualification._normalize_log(log_path)

            self.assertEqual(
                b"first\n second value\r\nthird",
                log_path.read_bytes(),
            )

    def test_python_gate_uses_the_invoking_interpreter(self) -> None:
        self.assertEqual(
            [sys.executable, "-m", "unittest"],
            qualification._runtime_command(["python", "-m", "unittest"]),
        )
        self.assertEqual(
            ["flutter", "test"],
            qualification._runtime_command(["flutter", "test"]),
        )

    def test_source_roots_cover_top_level_and_workstation_projects(self) -> None:
        roots = qualification._source_roots(REPO_ROOT)

        self.assertEqual(REPO_ROOT, roots[0])
        self.assertEqual(len(roots), len(set(roots)))
        for expected in (
            REPO_ROOT / "core_governance" / "src",
            REPO_ROOT / "core_runtime" / "src",
            REPO_ROOT / "core_semantics" / "src",
            REPO_ROOT / "host_interaction" / "src",
            REPO_ROOT / "skill_semantics" / "src",
            REPO_ROOT / "workstation" / "skills_core" / "src",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, roots)

    def test_unittest_summary_preserves_failure_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "unittest.log"
            log_path.write_text(
                "ERROR: test_error (tests.Example)\n"
                "FAIL: test_failure (tests.Example)\n"
                "Ran 2 tests in 1.250s\n"
                "FAILED (failures=1, errors=1)\n",
                encoding="utf-8",
            )

            summary = qualification._unittest_summary(log_path)

        self.assertEqual(
            {
                "errors": ["test_error (tests.Example)"],
                "failures": ["test_failure (tests.Example)"],
                "tests_run": 2,
            },
            summary,
        )


class RepositoryQualificationEvidenceTest(unittest.TestCase):
    def test_baseline_covers_declared_gates_and_provider_runs(self) -> None:
        baseline = json.loads(
            (REPO_ROOT / "architecture" / "qualification-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        with (REPO_ROOT / "architecture" / "qualification-gates.toml").open(
            "rb"
        ) as handle:
            config = tomllib.load(handle)
        configured_gate_ids = {str(gate["id"]) for gate in config["gates"]}
        baseline_gate_ids = {str(gate["id"]) for gate in baseline["gates"]}
        self.assertEqual(configured_gate_ids, baseline_gate_ids)

        expected = {
            "incremental_publication_bdd_live",
            "validation_ladder",
            "workstation_trial_validation",
        }
        provider_gates = {
            gate["id"]: gate
            for gate in baseline["gates"]
            if gate["id"] in expected
        }
        self.assertEqual(expected, set(provider_gates))
        self.assertTrue(
            all(gate["status"] == "passed" for gate in provider_gates.values())
        )
        self.assertTrue(
            all(gate["runs"] for gate in provider_gates.values())
        )


class QualificationComparisonTest(unittest.TestCase):
    def test_nested_json_result_must_have_an_accepted_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            result_path = root / "result.json"
            result_path.write_text('{"status": "partial"}\n', encoding="utf-8")
            evidence = qualification._result_json_evidence(
                {
                    "result_json": "result.json",
                    "accepted_result_statuses": ["ok", "partial"],
                },
                root,
            )

        self.assertIsNotNone(evidence)
        assert evidence is not None
        self.assertTrue(evidence["accepted"])
        self.assertEqual("partial", evidence["observed_status"])

    def test_nested_ok_result_may_not_regress_to_partial(self) -> None:
        prior = _baseline(_gate("passed"))
        current = _baseline(_gate("passed"))
        prior["gates"][0]["result_evidence"] = {"observed_status": "ok"}
        current["gates"][0]["result_evidence"] = {
            "observed_status": "partial"
        }

        regressions = qualification.compare_baselines(current, prior)

        self.assertEqual(
            ["nested result no longer ok: unit (partial)"],
            regressions,
        )

    def test_passed_gate_may_not_regress(self) -> None:
        regressions = qualification.compare_baselines(
            _baseline(_gate("failed")),
            _baseline(_gate("passed")),
        )

        self.assertEqual(["gate no longer passes: unit (failed)"], regressions)

    def test_failed_gate_rejects_only_new_failure_identities(self) -> None:
        regressions = qualification.compare_baselines(
            _baseline(
                _gate(
                    "failed",
                    errors=["existing error", "new error"],
                    failures=["existing failure"],
                )
            ),
            _baseline(
                _gate(
                    "failed",
                    errors=["existing error"],
                    failures=["existing failure"],
                )
            ),
        )

        self.assertEqual(
            ["new unittest error: unit: new error"],
            regressions,
        )

    def test_failed_gate_cannot_be_hidden_by_not_running_it(self) -> None:
        regressions = qualification.compare_baselines(
            _baseline(_gate("not_run")),
            _baseline(_gate("failed", errors=["existing error"])),
        )

        self.assertEqual(
            ["failed gate is no longer observable: unit (not_run)"],
            regressions,
        )

    def test_failed_unittest_gate_must_keep_structured_results(self) -> None:
        regressions = qualification.compare_baselines(
            _baseline(_gate("failed")),
            _baseline(_gate("failed", errors=["existing error"])),
        )

        self.assertEqual(["unittest result missing: unit"], regressions)


if __name__ == "__main__":
    unittest.main()
