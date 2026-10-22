from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "trials" / "GOVERNED_CHAT_VALIDATION.py"
SPEC = importlib.util.spec_from_file_location("governed_chat_validation", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATION
SPEC.loader.exec_module(VALIDATION)


PASSING_ANSWERS = (
    "On the sunny 2m by 1m balcony, make basil the priority and spend no more than 20 minutes a week.",
    "Use two herbs: basil and thyme. The complete constraints remain a sunny 2m by 1m balcony and 20 minutes a week.",
    "The constraints are a sunny 2m by 1m balcony, a 20 minutes weekly budget, basil as the favorite, and a two-herb scope.",
    "For the 2m by 1m balcony with partial sun, keep two herbs led by basil and stay within 20 minutes a week.",
    "Keep two herbs led by basil on the 2m by 1m balcony within 20 minutes a week. Sunlight changed from sunny to partial sun.",
)


class FakeHost:
    def __init__(self, root: Path, answers: tuple[str, ...] = PASSING_ANSWERS) -> None:
        self.root = root
        self.answers = answers
        self.calls: list[dict[str, str]] = []

    def submit(
        self,
        prompt: str,
        *,
        treatment: str,
        parent_run_id: str,
    ) -> dict[str, object]:
        index = len(self.calls)
        run_id = f"run_{index + 1}"
        checkpoint_path = self.root / f"turn_{index + 1}.json"
        checkpoint_path.write_text("{}\n", encoding="utf-8")
        self.calls.append(
            {
                "prompt": prompt,
                "treatment": treatment,
                "parent_run_id": parent_run_id,
            }
        )
        return {
            "assistant_text": self.answers[index],
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "run_outcome": "completed",
            "checkpoint_path": str(checkpoint_path),
            "binding": {"treatment": treatment},
            "summary": {"root_status": "closed"},
        }


class FailingHost:
    def submit(self, *_args: object, **_kwargs: object) -> dict[str, object]:
        raise TimeoutError("provider did not answer")


class GovernedChatValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = VALIDATION.load_scenario(VALIDATION.DEFAULT_SCENARIO)

    def test_fixture_defines_five_explicitly_related_turns(self) -> None:
        self.assertEqual(5, len(self.scenario["turns"]))
        self.assertEqual(
            ["independent", "follow_up", "follow_up", "correction", "follow_up"],
            [turn["treatment"] for turn in self.scenario["turns"]],
        )

    def test_semantic_evaluator_rejects_superseded_values(self) -> None:
        result = VALIDATION.evaluate_answer(
            "Cedar remains blue and is due Friday.",
            {
                "required_concepts": [
                    {"label": "codename", "any_of": ["Cedar"]},
                ],
                "forbidden_concepts": [
                    {"label": "old color", "any_of": ["blue"]},
                ],
            },
        )

        self.assertFalse(result["passed"])
        self.assertEqual(1, result["checks_passed"])
        self.assertEqual(2, result["checks_total"])

    def test_execute_trial_separates_structure_semantics_and_timing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            report_path = root / "report.json"
            requests = VALIDATION.TimedLlmRequests()
            outcome = VALIDATION.execute_trial(
                scenario=self.scenario,
                host=FakeHost(root),
                report_path=report_path,
                base_report={"status": "running"},
                llm_requests=requests,
            )

        self.assertEqual(0, outcome.exit_code)
        self.assertEqual("passed", outcome.report["status"])
        self.assertTrue(outcome.report["structural_passed"])
        self.assertEqual(1.0, outcome.report["semantic"]["score"])
        self.assertIsNone(outcome.report["timing"]["passed"])
        self.assertEqual(
            0,
            outcome.report["performance"]["logical_llm_request_count"],
        )
        self.assertEqual("run_1", outcome.report["turns"][1]["parent_run_id"])
        self.assertEqual("run_4", outcome.report["turns"][4]["parent_run_id"])

    def test_semantic_omission_fails_without_becoming_an_operational_error(self) -> None:
        answers = (*PASSING_ANSWERS[:4], "Use basil and thyme.")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outcome = VALIDATION.execute_trial(
                scenario=self.scenario,
                host=FakeHost(root, answers=answers),
                report_path=root / "report.json",
                base_report={"status": "running"},
                llm_requests=VALIDATION.TimedLlmRequests(),
            )

        self.assertEqual(1, outcome.exit_code)
        self.assertEqual("failed", outcome.report["status"])
        self.assertTrue(outcome.report["structural_passed"])
        self.assertFalse(outcome.report["semantic"]["passed"])

    def test_provider_failure_is_classified_as_operational(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            outcome = VALIDATION.execute_trial(
                scenario=self.scenario,
                host=FailingHost(),
                report_path=root / "report.json",
                base_report={"status": "running"},
                llm_requests=VALIDATION.TimedLlmRequests(),
            )

        self.assertEqual(2, outcome.exit_code)
        self.assertEqual("operational_error", outcome.report["status"])
        self.assertEqual("establish_plan", outcome.report["failure_stage"])
        self.assertEqual("TimeoutError", outcome.report["turns"][0]["error_type"])

    def test_llm_timer_records_metadata_without_recording_prompt_text(self) -> None:
        original = VALIDATION.supplement.ask_llm
        VALIDATION.supplement.ask_llm = lambda prompt, **_kwargs: (
            "answer",
            {"model": "small-model", "response_id": "response-1"},
        )
        try:
            with VALIDATION.TimedLlmRequests() as requests:
                result = VALIDATION.supplement.ask_llm(
                    "private prompt",
                    model="small-model",
                    return_metadata=True,
                )
        finally:
            VALIDATION.supplement.ask_llm = original

        self.assertEqual("answer", result[0])
        self.assertEqual(1, len(requests.records))
        self.assertNotIn("private prompt", str(requests.records[0]))
        self.assertEqual("small-model", requests.records[0]["response_model"])


if __name__ == "__main__":
    unittest.main()
