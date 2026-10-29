from __future__ import annotations

from dataclasses import replace
import unittest
from typing import Any

from realized_blend.context import BlendContext
from realized_blend.execution import (
    BlendResolvedWorkflowStep,
    execute_blend_workflow,
)
from realized_blend.operators import BlendOperator
from realized_blend.ports import (
    BlendCompositionExecutionEvent,
    BlendCompositionExecutionResult,
)
from realized_blend.workflows import (
    BlendWorkflowPlan,
    BlendWorkflowRun,
    BlendWorkflowStep,
)


class FixedClock:
    def __init__(self) -> None:
        self._index = 0

    def now(self) -> str:
        self._index += 1
        return f"2026-10-27T00:00:{self._index:02d}+00:00"


class FixedIdentifierFactory:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def new_identifier(self, prefix: str) -> str:
        self._counts[prefix] = self._counts.get(prefix, 0) + 1
        return f"{prefix}_{self._counts[prefix]:02d}"


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.plan: BlendWorkflowPlan | None = None
        self.run: BlendWorkflowRun | None = None

    def load_plan(self, workflow_id: str) -> BlendWorkflowPlan:
        if self.plan is None or self.plan.workflow_id != workflow_id:
            raise KeyError(workflow_id)
        return self.plan

    def load_run(self, workflow_run_id: str) -> BlendWorkflowRun:
        if self.run is None or self.run.workflow_run_id != workflow_run_id:
            raise KeyError(workflow_run_id)
        return self.run

    def load_index(self) -> dict[str, Any]:
        return {
            "latest_plan_id": self.plan.workflow_id if self.plan else "",
            "latest_run_id": self.run.workflow_run_id if self.run else "",
        }

    def list_summaries(
        self,
        *,
        kind: str = "runs",
        status: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        del kind, status, limit
        return []

    def list_runs_for_plan(
        self,
        workflow_id: str,
        *,
        status: str = "",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        del workflow_id, status, limit
        return []

    def persist(
        self,
        *,
        plan: BlendWorkflowPlan,
        run: BlendWorkflowRun,
        session_id: str = "",
    ) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
        self.plan = replace(
            plan,
            session_id=plan.session_id or session_id,
            metadata={**plan.metadata, "persisted": True},
        )
        self.run = replace(
            run,
            workflow_run_id=run.workflow_run_id or "bwf_run_01",
            workflow_id=run.workflow_id or self.plan.workflow_id,
            plan=self.plan,
            session_id=run.session_id or self.plan.session_id or session_id,
            metadata={**run.metadata, "persisted": True},
        )
        return self.plan, self.run, {
            "workflow_id": self.plan.workflow_id,
            "workflow_run_id": self.run.workflow_run_id,
            "adapter": "memory",
        }


class ScriptedInvocationPort:
    def __init__(self, results: dict[str, dict[str, Any]]) -> None:
        self.results = results
        self.invocations: list[dict[str, Any]] = []

    def invoke(self, *, operator, invocation, handle) -> dict[str, Any]:
        self.invocations.append(
            {
                "operator": operator.to_dict(),
                "invocation": invocation.to_dict(),
                "handle": handle,
            }
        )
        return dict(self.results[invocation.step_id])


class ScriptedCompositionPort:
    def __init__(
        self,
        *,
        final_outputs_by_step: dict[str, Any] | None = None,
        skipped_step_ids: tuple[str, ...] = (),
        iterations_by_step: dict[str, int] | None = None,
    ) -> None:
        self.final_outputs_by_step = final_outputs_by_step
        self.skipped_step_ids = set(skipped_step_ids)
        self.iterations_by_step = dict(iterations_by_step or {})

    def execute(
        self,
        *,
        steps,
        invoker,
        root_inputs,
        root_references,
        execution_observer=None,
    ) -> BlendCompositionExecutionResult:
        del root_inputs, root_references
        execution_steps: list[dict[str, Any]] = []
        outputs: dict[str, Any] = {}
        for step in steps:
            step_id = str(step["step_id"])
            branch_label = str(step.get("branch_label", ""))
            if step_id in self.skipped_step_ids:
                if execution_observer is not None:
                    execution_observer(
                        BlendCompositionExecutionEvent(
                            kind="step_skipped",
                            step_id=step_id,
                            title=step_id,
                            iteration=1,
                            branch_label=branch_label,
                            status="skipped",
                            skipped_reason="condition did not match",
                        )
                    )
                execution_steps.append(
                    {
                        "step_id": step_id,
                        "title": step_id,
                        "status": "skipped",
                        "iteration": 1,
                        "branch_label": branch_label,
                        "skipped_reason": "condition did not match",
                    }
                )
                continue
            iterations = self.iterations_by_step.get(step_id, 1)
            for iteration in range(1, iterations + 1):
                if execution_observer is not None:
                    execution_observer(
                        BlendCompositionExecutionEvent(
                            kind="step_started",
                            step_id=step_id,
                            title=step_id,
                            iteration=iteration,
                            branch_label=branch_label,
                            status="started",
                            input_payload={"iteration": iteration},
                        )
                    )
                output = invoker(
                    step_id,
                    dict(step["skill"]),
                    {"iteration": iteration},
                )
                outputs[step_id] = output
                if execution_observer is not None:
                    execution_observer(
                        BlendCompositionExecutionEvent(
                            kind="step_completed",
                            step_id=step_id,
                            title=step_id,
                            iteration=iteration,
                            branch_label=branch_label,
                            status="ok",
                            input_payload={"iteration": iteration},
                            output_payload=output,
                        )
                    )
                execution_steps.append(
                    {
                        "step_id": step_id,
                        "title": step_id,
                        "status": "ok",
                        "iteration": iteration,
                        "branch_label": branch_label,
                        "input_payload": {"iteration": iteration},
                        "output_payload": output,
                    }
                )
        return BlendCompositionExecutionResult(
            steps=execution_steps,
            plan_authorities=["compose"],
            final_outputs_by_step=(
                dict(self.final_outputs_by_step)
                if self.final_outputs_by_step is not None
                else outputs
            ),
        )


class BlendExecutionTests(unittest.TestCase):
    def _context(self) -> BlendContext:
        return BlendContext(
            attachments=(),
            visible_mounts=("main",),
            writable_mounts=("main",),
            granted_capabilities=("test.invoke",),
            task_focus="Execute deterministic workflow",
        )

    def _resolved_step(
        self,
        step_id: str,
        *,
        branch_label: str = "",
    ) -> BlendResolvedWorkflowStep:
        operator = BlendOperator(
            operator_id=f"operator:{step_id}",
            operator_kind="capability",
            display_name=f"operator.{step_id}",
            execution_adapter="test.invoke",
            input_shape={"iteration": "integer"},
            output_shape={"value": "text"},
            policy_requirements=("execute",),
            actor_visibility=("ai_chat",),
        )
        return BlendResolvedWorkflowStep(
            workflow_step=BlendWorkflowStep(
                step_id=step_id,
                operator_kind="capability",
                operator_name=operator.display_name,
                semantic_unit=f"unit.{step_id}",
                branch_label=branch_label,
            ),
            operator={"title": operator.display_name},
            operator_descriptor=operator,
            operator_source={"source_kind": "test"},
            context_applicability={"status": "applicable"},
            resolved_target="main",
        )

    def _execute(
        self,
        *,
        composition_port: ScriptedCompositionPort | None = None,
        results: dict[str, dict[str, Any]] | None = None,
        execution_observer=None,
    ) -> tuple[dict[str, Any], InMemoryWorkflowRepository, ScriptedInvocationPort]:
        resolved_steps = (
            self._resolved_step("first", branch_label="primary"),
            self._resolved_step("second", branch_label="fallback"),
        )
        plan = BlendWorkflowPlan(
            workflow_id="bwf_plan_01",
            workflow_kind="capability_compose",
            session_id="session-1",
            steps=tuple(item.workflow_step for item in resolved_steps),
            final_output_step="second",
        )
        repository = InMemoryWorkflowRepository()
        invocation_port = ScriptedInvocationPort(
            results
            or {
                "first": {
                    "status": "ok",
                    "answer": "first answer",
                    "result_payload": {"value": "first output"},
                },
                "second": {
                    "status": "ok",
                    "answer": "second answer",
                    "result_payload": {"value": "second output"},
                },
            }
        )
        result = execute_blend_workflow(
            session_id="session-1",
            context=self._context(),
            workflow_plan=plan,
            resolved_steps=resolved_steps,
            capability_name="blend.execute",
            target_name="main",
            composition_port=composition_port or ScriptedCompositionPort(),
            operator_invocation_port=invocation_port,
            workflow_repository=repository,
            clock=FixedClock(),
            identifier_factory=FixedIdentifierFactory(),
            execution_observer=execution_observer,
        )
        return result, repository, invocation_port

    def test_execution_preserves_iteration_branch_skip_and_final_output_fallback(self) -> None:
        result, repository, invocation_port = self._execute(
            composition_port=ScriptedCompositionPort(
                final_outputs_by_step={"first": {"value": "first output"}},
                skipped_step_ids=("second",),
                iterations_by_step={"first": 2},
            )
        )

        self.assertEqual("ok", result["status"])
        self.assertEqual("first", result["final_output_step"])
        self.assertEqual({"value": "first output"}, result["final_output"])
        self.assertEqual(
            ["ok", "ok", "skipped"],
            [step["status"] for step in result["steps"]],
        )
        self.assertEqual(
            ["primary", "primary", "fallback"],
            [step["branch_label"] for step in result["steps"]],
        )
        self.assertEqual(2, len(invocation_port.invocations))
        self.assertEqual(
            ["bop_inv_01", "bop_inv_02"],
            [
                item["invocation"]["invocation_id"]
                for item in invocation_port.invocations
            ],
        )
        self.assertEqual(result["workflow_run"], repository.run.to_dict())

    def test_non_ok_operator_result_halts_shapes_status_and_persists(self) -> None:
        result, repository, _invocation_port = self._execute(
            results={
                "first": {
                    "status": "approval_required",
                    "answer": "Approval required.",
                    "requested_delegation": [
                        {
                            "capability": "ws.process.run",
                            "target": "main",
                            "rationale": "Run a governed process.",
                        }
                    ],
                    "missing_delegation": [
                        {
                            "capability": "ws.process.run",
                            "target": "main",
                            "rationale": "Run a governed process.",
                        }
                    ],
                },
                "second": {"status": "ok", "answer": "unused"},
            }
        )

        self.assertEqual("approval_required", result["status"])
        self.assertEqual("first", result["blocked_step_id"])
        self.assertEqual("operator.first", result["blocked_operator_name"])
        self.assertEqual("Approval required.", result["answer"])
        self.assertEqual(1, len(result["requested_delegation"]))
        self.assertEqual(1, len(result["missing_delegation"]))
        self.assertEqual("approval_required", repository.run.status)
        self.assertEqual(result["workflow_run"], repository.run.to_dict())

    def test_observations_are_lossy_and_never_authoritative_for_stored_runs(self) -> None:
        authoritative_results: dict[str, dict[str, Any]] = {}
        authoritative_runs: dict[str, dict[str, Any]] = {}
        observed: dict[str, list[Any]] = {
            "duplicate": [],
            "delayed": [],
            "reject": [],
        }

        observer_modes = {
            "absent": None,
            "duplicate": lambda event: observed["duplicate"].extend([event, event]),
            "delayed": lambda event: observed["delayed"].append(event),
            "reject": lambda event: (
                observed["reject"].append(event),
                (_ for _ in ()).throw(RuntimeError("observer rejected event")),
            )[-1],
        }
        for mode, observer in observer_modes.items():
            with self.subTest(mode=mode):
                result, repository, _invocation_port = self._execute(
                    execution_observer=observer
                )
                authoritative_results[mode] = result
                authoritative_runs[mode] = repository.run.to_dict()

        baseline_result = authoritative_results["absent"]
        baseline_run = authoritative_runs["absent"]
        for mode in ("duplicate", "delayed", "reject"):
            with self.subTest(authoritative_equivalence=mode):
                self.assertEqual(baseline_result, authoritative_results[mode])
                self.assertEqual(baseline_run, authoritative_runs[mode])

        self.assertEqual([], observed.get("absent", []))
        self.assertGreater(len(observed["duplicate"]), len(observed["delayed"]))
        self.assertEqual(len(observed["delayed"]), len(observed["reject"]))
        self.assertEqual("ok", baseline_run["status"])
        self.assertEqual("second", baseline_run["final_output_step"])
        self.assertEqual("second output", baseline_run["final_output"])
        self.assertEqual(2, len(baseline_run["steps"]))
        self.assertEqual(
            [
                "blend_workflow_started",
                "blend_step_started",
                "blend_step_completed",
                "blend_step_started",
                "blend_step_completed",
                "blend_workflow_completed",
                "blend_workflow_persisted",
            ],
            [event.kind for event in observed["delayed"]],
        )


if __name__ == "__main__":
    unittest.main()
