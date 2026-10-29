from __future__ import annotations

from dataclasses import replace
import unittest
from pathlib import Path
from typing import Any

from realized_blend.context import BlendContext
from realized_blend.execution import BlendResolvedWorkflowStep
from realized_blend.operators import BlendOperator
from realized_blend.workflows import (
    BlendWorkflowBinding,
    BlendWorkflowPlan,
    BlendWorkflowRun,
    BlendWorkflowStep,
)
from workstation.runtime.core.blend_adapters import (
    execute_workstation_blend_workflow,
)


def _canonical_skill() -> dict[str, Any]:
    return {
        "artifact_id": "artifact-emit-text",
        "kind": "ability",
        "title": "Emit Text",
        "schema": "bssc_skill.v2",
        "declaration": {"authorities_requested": ["execute"]},
        "normalization": {
            "regions": {
                "a": {
                    "boundary_term": "a*",
                    "leaves": [
                        {
                            "region": "a*",
                            "path": "/a/text",
                            "carrier_kind": "value",
                            "data_type": "String",
                            "semantic_label": "text",
                            "leaf_class": "scalar",
                        }
                    ],
                },
                "d": {
                    "boundary_term": "d*",
                    "leaves": [
                        {
                            "region": "d*",
                            "path": "/d/text",
                            "carrier_kind": "value",
                            "data_type": "String",
                            "semantic_label": "text",
                            "leaf_class": "scalar",
                        }
                    ],
                },
            }
        },
    }


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.plan: BlendWorkflowPlan | None = None
        self.run: BlendWorkflowRun | None = None

    def persist(
        self,
        *,
        plan: BlendWorkflowPlan,
        run: BlendWorkflowRun,
        session_id: str = "",
    ) -> tuple[BlendWorkflowPlan, BlendWorkflowRun, dict[str, Any]]:
        self.plan = replace(
            plan,
            workflow_id=plan.workflow_id or "workflow-memory",
            session_id=plan.session_id or session_id,
        )
        self.run = replace(
            run,
            workflow_run_id=run.workflow_run_id or "run-memory",
            workflow_id=run.workflow_id or self.plan.workflow_id,
            plan=self.plan,
            session_id=run.session_id or self.plan.session_id,
        )
        return self.plan, self.run, {"adapter": "memory"}


class WorkstationBlendAdapterTests(unittest.TestCase):
    def test_workstation_adapter_executes_through_canonical_blend_ports(self) -> None:
        context = BlendContext(
            attachments=(),
            visible_mounts=("skills",),
            writable_mounts=(),
            granted_capabilities=("ws.skill.invoke",),
            task_focus="Run a canonical Blend workflow",
        )
        workflow_step = BlendWorkflowStep(
            step_id="emit",
            operator_kind="skill",
            operator_name="Emit Text",
            bindings=(
                BlendWorkflowBinding(
                    {
                        "target_region": "a",
                        "target_path": "/a/text",
                        "source_root_name": "text",
                        "source_root_region": "a",
                    }
                ),
            ),
        )
        plan = BlendWorkflowPlan(
            workflow_id="workflow-direct-consumer",
            workflow_kind="skill_compose",
            session_id="session-direct-consumer",
            steps=(workflow_step,),
            root_inputs={"text": "direct canonical path"},
            final_output_step="emit",
        )
        descriptor = BlendOperator(
            operator_id="skill:emit_text",
            operator_kind="skill",
            display_name="Emit Text",
            execution_adapter="workstation.skill.invoke",
            input_shape={"text": "text input"},
            output_shape={"text": "text output"},
            policy_requirements=("execute",),
            actor_visibility=("ai_chat",),
            target_resolution={
                "default_target": "skills",
                "allowed_targets": ["skills"],
                "require_visible": True,
            },
        )
        resolved_step = BlendResolvedWorkflowStep(
            workflow_step=workflow_step,
            operator=_canonical_skill(),
            operator_descriptor=descriptor,
            operator_source={"source_kind": "test"},
            context_applicability={"status": "applicable"},
            resolved_target="skills",
        )
        repository = InMemoryWorkflowRepository()
        invocations: list[dict[str, Any]] = []
        events = []

        def invoke_step(step, invocation) -> dict[str, Any]:
            invocations.append(
                {
                    "step_id": step.step_id,
                    "inputs": dict(invocation.inputs),
                    "context": invocation.context,
                    "target": invocation.resolved_target,
                }
            )
            return {
                "status": "ok",
                "answer": str(invocation.inputs["text"]),
                "result_payload": {"text": str(invocation.inputs["text"])},
                "parsed_output": {"text": str(invocation.inputs["text"])},
            }

        result = execute_workstation_blend_workflow(
            root_path=Path("/unused-json-root"),
            session_id="session-direct-consumer",
            context=context,
            workflow_plan=plan,
            resolved_steps=(resolved_step,),
            capability_name="ws.workflow.run",
            target_name="skills",
            invoke_step=invoke_step,
            execution_observer=events.append,
            workflow_repository=repository,
        )

        self.assertEqual("ok", result["status"])
        self.assertEqual({"text": "direct canonical path"}, result["final_output"])
        self.assertEqual("workflow-direct-consumer", result["workflow_id"])
        self.assertEqual({"adapter": "memory"}, result["workflow_store"])
        self.assertEqual(
            {
                "step_id": "emit",
                "inputs": {"text": "direct canonical path"},
                "context": context,
                "target": "skills",
            },
            invocations[0],
        )
        self.assertEqual(result["workflow_run"], repository.run.to_dict())
        self.assertEqual(
            [
                "blend_workflow_started",
                "blend_step_started",
                "blend_step_completed",
                "blend_workflow_completed",
                "blend_workflow_persisted",
            ],
            [event.kind for event in events],
        )


if __name__ == "__main__":
    unittest.main()
