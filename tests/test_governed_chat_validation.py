from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

from realized_core_conversation import CoreConversationHost
from realized_core_llm import (
    ConversationPlanProposal,
    ConversationPlanningResult,
    ConversationRenderResult,
    CorrectionProposal,
    SemanticItemProposal,
)
from realized_core_engine import EngineConfiguration, OperationKind


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


class QueuePlanner:
    def __init__(
        self,
        *proposals: ConversationPlanProposal | BaseException,
    ) -> None:
        self.proposals = list(proposals)

    def propose(self, _context):
        proposal = self.proposals.pop(0)
        if isinstance(proposal, BaseException):
            raise proposal
        return ConversationPlanningResult(
            proposal=proposal,
            receipt={"provider": "fake", "response_id": "planning-1"},
        )


class StaticRenderer:
    def render(self, _context):
        return ConversationRenderResult(
            text="Cedar remains governed and the audience is unresolved.",
            receipt={"provider": "fake", "response_id": "rendering-1"},
        )


class GovernedChatValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = VALIDATION.load_scenario(
            VALIDATION.LEGACY_FIVE_TURN_SCENARIO
        )

    def test_default_fixture_is_the_full_cedar_resumption_conversation(self) -> None:
        scenario = VALIDATION.load_scenario(VALIDATION.DEFAULT_SCENARIO)

        self.assertEqual("cedar_resumption_journey", scenario["scenario_id"])
        self.assertEqual(
            {f"3.{index}" for index in range(1, 22)},
            set(scenario["principle_coverage"]),
        )
        self.assertGreater(
            sum(len(flow["steps"]) for flow in scenario["flows"]),
            5,
        )
        self.assertTrue(
            {
                str(step["operation"])
                for flow in scenario["flows"]
                for step in flow["steps"]
            }.issubset(VALIDATION._CEDAR_SUPPORTED_OPERATIONS)
        )

    def test_full_scenario_rejects_an_unknown_harness_operation(self) -> None:
        scenario = VALIDATION.load_scenario(VALIDATION.DEFAULT_SCENARIO)
        scenario["flows"][0]["steps"][0]["operation"] = "private_state_repair"
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "scenario.json"
            path.write_text(
                json.dumps(scenario),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "Unsupported Cedar harness operation",
            ):
                VALIDATION.load_scenario(path)

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

    def test_provider_evidence_uses_product_receipts_without_prompt_text(self) -> None:
        requests = VALIDATION.TimedLlmRequests()
        requests.capture_result(
            {
                "planning": {
                    "provider_receipt": {
                        "provider": "openai",
                        "model": "small-model",
                        "response_id": "response-1",
                        "request_digest": "request-digest",
                        "response_digest": "response-digest",
                        "elapsed_seconds": 0.125,
                    }
                }
            },
            action="semantic_turn",
        )

        self.assertEqual(1, len(requests.records))
        self.assertNotIn("private prompt", str(requests.records[0]))
        self.assertEqual("small-model", requests.records[0]["response_model"])
        self.assertEqual(0.125, requests.records[0]["elapsed_seconds"])

    def test_rejected_provider_plan_retains_request_evidence(self) -> None:
        scenario = {
            "scenario_id": "cedar_rejected_plan_receipt",
            "principle_coverage": {"3.10": ["start_brief"]},
            "flows": [
                {
                    "flow_id": "baseline",
                    "steps": [
                        {
                            "step_id": "start_brief",
                            "operation": "start",
                            "prompt": "Create the Cedar brief.",
                            "expect": {},
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            conversation_root = root / "conversation"
            configuration = EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )
            requests = VALIDATION.TimedLlmRequests()
            planner = QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    achieved_items=(
                        SemanticItemProposal("project", "fact"),
                    ),
                )
            )
            outcome = VALIDATION.CedarTrialRunner(
                scenario=scenario,
                host=CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                host_factory=lambda: CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                advisor_factory=lambda: (planner, StaticRenderer()),
                llm_requests=requests,
            ).execute(
                report_path=root / "report.json",
                base_report={"status": "running"},
                max_median_turn_seconds=None,
                max_single_turn_seconds=None,
            )

        self.assertEqual(2, outcome.exit_code)
        self.assertEqual("operational_error", outcome.report["status"])
        self.assertEqual(
            1,
            outcome.report["performance"]["logical_llm_request_count"],
        )
        self.assertEqual(
            "planning-1",
            outcome.report["steps"][0]["llm_requests"][0]["response_id"],
        )

    def test_cedar_harness_owns_no_private_conversation_implementation(
        self,
    ) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        for forbidden in (
            "import supplement",
            "LLMSupplement",
            "JsonConversationPlanner",
            "JsonConversationRenderer",
            "ConversationTurnPlan",
            ".submit_plan(",
            '"MESSAGES.jsonl"',
            "SQLiteConversationActivityJournal",
            "_materialize_proposal",
            "_record_recovery",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn(
            "from realized_core_conversation import CoreConversationHost",
            source,
        )
        self.assertIn("build_environment_conversation_advisors", source)

    def test_cedar_runner_uses_real_host_planning_engine_and_rendering(self) -> None:
        scenario = {
            "scenario_id": "cedar_runner_smoke",
            "principle_coverage": {"3.10": ["start_brief"]},
            "flows": [
                {
                    "flow_id": "baseline",
                    "steps": [
                        {
                            "step_id": "start_brief",
                            "operation": "start",
                            "prompt": "Create a brief for Cedar and ask for its audience.",
                            "expect": {
                                "achieved": {"project": "Cedar"},
                                "non_achieved": ["audience"],
                                "objective_complete": False,
                                "turn_complete": True,
                            },
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            conversation_root = root / "conversation"
            configuration = EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )
            host = CoreConversationHost(
                root=conversation_root,
                configuration=configuration,
            )
            planner = QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    required_outcome="A brief with an identified audience",
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                    ),
                    non_achieved_items=(
                        SemanticItemProposal(
                            "audience",
                            "requirement",
                            text="Audience is unresolved",
                        ),
                    ),
                )
            )
            outcome = VALIDATION.CedarTrialRunner(
                scenario=scenario,
                host=host,
                host_factory=lambda: CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                advisor_factory=lambda: (planner, StaticRenderer()),
                llm_requests=VALIDATION.TimedLlmRequests(),
            ).execute(
                report_path=root / "report.json",
                base_report={"status": "running"},
                max_median_turn_seconds=None,
                max_single_turn_seconds=None,
            )

        self.assertEqual(0, outcome.exit_code, outcome.report)
        self.assertTrue(outcome.report["structural_passed"])
        self.assertTrue(outcome.report["structural"]["passed"])
        self.assertTrue(outcome.report["interpretation"]["passed"])
        self.assertTrue(outcome.report["rendering"]["passed"])
        self.assertEqual(1, outcome.report["semantic_turn_count"])
        self.assertEqual(0, outcome.report["operational_action_count"])
        self.assertEqual(
            "start",
            outcome.report["steps"][0]["planning"]["proposal"]["operation"],
        )

    def test_cedar_runner_verifies_correction_supersession_edges(self) -> None:
        scenario = {
            "scenario_id": "cedar_correction_supersession",
            "principle_coverage": {"3.4": ["correct_color"]},
            "flows": [
                {
                    "flow_id": "correction",
                    "steps": [
                        {
                            "step_id": "start_brief",
                            "operation": "start",
                            "prompt": "Create the blue Cedar brief.",
                            "expect": {"achieved": {"color": "blue"}},
                        },
                        {
                            "step_id": "correct_color",
                            "operation": "correct",
                            "prompt": "Change blue to green.",
                            "expect": {
                                "achieved": {"color": "green"},
                                "superseded": {"color": ["blue"]},
                            },
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            conversation_root = root / "conversation"
            configuration = EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )
            planner = QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                        SemanticItemProposal("color", "fact", "blue"),
                    ),
                ),
                ConversationPlanProposal(
                    operation=OperationKind.CORRECT,
                    corrections=(
                        CorrectionProposal(
                            target_selector="color",
                            replacement=SemanticItemProposal(
                                "color",
                                "fact",
                                "green",
                            ),
                            rationale="The user explicitly replaced blue.",
                        ),
                    ),
                ),
            )
            outcome = VALIDATION.CedarTrialRunner(
                scenario=scenario,
                host=CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                host_factory=lambda: CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                advisor_factory=lambda: (planner, StaticRenderer()),
                llm_requests=VALIDATION.TimedLlmRequests(),
            ).execute(
                report_path=root / "report.json",
                base_report={"status": "running"},
                max_median_turn_seconds=None,
                max_single_turn_seconds=None,
            )

        self.assertEqual(0, outcome.exit_code, outcome.report)
        correction_checks = {
            check["label"]: check
            for check in outcome.report["steps"][1]["checks"]
        }
        self.assertTrue(correction_checks["correction superseded color"]["passed"])

    def test_cedar_runner_isolates_flows_started_from_one_checkpoint(self) -> None:
        scenario = {
            "scenario_id": "cedar_independent_checkpoint_flows",
            "principle_coverage": {"3.13": ["green", "yellow"]},
            "flows": [
                {
                    "flow_id": "baseline",
                    "steps": [
                        {
                            "step_id": "start_brief",
                            "operation": "start",
                            "prompt": "Create the blue Cedar brief.",
                            "expect": {"achieved": {"color": "blue"}},
                        }
                    ],
                },
                {
                    "flow_id": "green_flow",
                    "starts_from": "start_brief",
                    "steps": [
                        {
                            "step_id": "green",
                            "operation": "correct",
                            "prompt": "Change blue to green.",
                            "expect": {"achieved": {"color": "green"}},
                        }
                    ],
                },
                {
                    "flow_id": "yellow_flow",
                    "starts_from": "start_brief",
                    "steps": [
                        {
                            "step_id": "yellow",
                            "operation": "correct",
                            "prompt": "Change blue to yellow.",
                            "expect": {"achieved": {"color": "yellow"}},
                        }
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            conversation_root = root / "conversation"
            configuration = EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )
            planner = QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                        SemanticItemProposal("color", "fact", "blue"),
                    ),
                ),
                ConversationPlanProposal(
                    operation=OperationKind.CORRECT,
                    corrections=(
                        CorrectionProposal(
                            "color",
                            SemanticItemProposal("color", "fact", "green"),
                            "Create the green alternate continuation.",
                        ),
                    ),
                ),
                ConversationPlanProposal(
                    operation=OperationKind.CORRECT,
                    corrections=(
                        CorrectionProposal(
                            "color",
                            SemanticItemProposal("color", "fact", "yellow"),
                            "Create the yellow alternate continuation.",
                        ),
                    ),
                ),
            )
            outcome = VALIDATION.CedarTrialRunner(
                scenario=scenario,
                host=CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                host_factory=lambda: CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                advisor_factory=lambda: (planner, StaticRenderer()),
                llm_requests=VALIDATION.TimedLlmRequests(),
            ).execute(
                report_path=root / "report.json",
                base_report={"status": "running"},
                max_median_turn_seconds=None,
                max_single_turn_seconds=None,
            )

        self.assertEqual(0, outcome.exit_code, outcome.report)
        self.assertEqual(
            ["blue", "green", "yellow"],
            [
                next(
                    check["actual"]
                    for check in step["checks"]
                    if check["label"] == "achieved color"
                )
                for step in outcome.report["steps"]
            ],
        )

    def test_old_frontier_planning_error_does_not_prove_staleness(self) -> None:
        scenario = {
            "scenario_id": "cedar_old_frontier_evidence",
            "principle_coverage": {"3.20": ["redirect_checklist"]},
            "flows": [
                {
                    "flow_id": "redirection",
                    "steps": [
                        {
                            "step_id": "start_brief",
                            "operation": "start",
                            "prompt": "Create a brief for Cedar.",
                            "expect": {},
                        },
                        {
                            "step_id": "redirect_checklist",
                            "operation": "redirect_and_realign",
                            "prompt": (
                                "Instead of a brief, create a launch checklist "
                                "for Cedar."
                            ),
                            "expect": {"old_frontier_executable": False},
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            conversation_root = root / "conversation"
            configuration = EngineConfiguration(
                max_steps=0,
                llm_policy="off",
                discovery="off",
                reflection="off",
                contemplation="off",
            )
            planner = QueuePlanner(
                ConversationPlanProposal(
                    operation=OperationKind.START,
                    objective="Create the Cedar brief",
                    achieved_items=(
                        SemanticItemProposal("project", "fact", "Cedar"),
                    ),
                ),
                ConversationPlanProposal(
                    operation=OperationKind.REDIRECT_AND_REALIGN,
                    objective="Create the Cedar launch checklist",
                    required_outcome="A Cedar launch checklist",
                    affected_selectors=("project",),
                    retained_selectors=("project",),
                ),
                VALIDATION.ConversationPlanningError(
                    "The probe could not be interpreted."
                ),
            )
            outcome = VALIDATION.CedarTrialRunner(
                scenario=scenario,
                host=CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                host_factory=lambda: CoreConversationHost(
                    root=conversation_root,
                    configuration=configuration,
                ),
                advisor_factory=lambda: (planner, StaticRenderer()),
                llm_requests=VALIDATION.TimedLlmRequests(),
            ).execute(
                report_path=root / "report.json",
                base_report={"status": "running"},
                max_median_turn_seconds=None,
                max_single_turn_seconds=None,
            )

        self.assertEqual(1, outcome.exit_code, outcome.report)
        stale_check = next(
            check
            for check in outcome.report["steps"][1]["checks"]
            if check["label"] == "old frontier was stale after redirection"
        )
        self.assertFalse(stale_check["passed"])

    def test_retained_realignment_material_may_remain_non_achieved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            runner = VALIDATION.CedarTrialRunner(
                scenario={"flows": []},
                host=FakeHost(root),
                host_factory=lambda: FakeHost(root),
                advisor_factory=lambda: (QueuePlanner(), StaticRenderer()),
                llm_requests=VALIDATION.TimedLlmRequests(),
            )
            checks = runner._evaluate_step(
                step={
                    "step_id": "clarify_realignment",
                    "operation": "continue_realignment",
                    "expect": {"retained": ["deadline", "budget"]},
                },
                result=None,
                metadata={},
                parent_run="run-1",
                pre=None,
                post={
                    "state": {
                        "achieved": [
                            {
                                "item_id": "deadline-1",
                                "payload": {
                                    "semantic_key": "deadline",
                                    "value": "Monday",
                                },
                            }
                        ],
                        "non_achievedness": [
                            {
                                "item_id": "budget-1",
                                "payload": {
                                    "semantic_key": "budget",
                                    "text": "A budget summary remains required.",
                                },
                            }
                        ],
                    }
                },
            )

        self.assertTrue(all(check["passed"] for check in checks), checks)

    def test_rejected_stale_attempt_is_not_an_overwrite(self) -> None:
        for outcome in ("stale", "rejected", "ambiguous"):
            with self.subTest(outcome=outcome):
                self.assertTrue(
                    VALIDATION._is_explicit_noncommit_outcome(
                        {"run_outcome": outcome}
                    )
                )
        self.assertFalse(
            VALIDATION._is_explicit_noncommit_outcome(
                {"run_outcome": "completed"}
            )
        )

    def test_stale_setup_must_advance_the_bound_branch(self) -> None:
        self.assertEqual(
            "run-2",
            VALIDATION._require_advanced_setup_result(
                {"run_id": "run-2", "run_outcome": "paused"},
                "run-1",
            ),
        )
        for result in (
            {"run_id": "run-1", "run_outcome": "paused"},
            {"run_id": "run-2", "run_outcome": "rejected"},
        ):
            with self.subTest(result=result):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "did not advance",
                ):
                    VALIDATION._require_advanced_setup_result(result, "run-1")


if __name__ == "__main__":
    unittest.main()
